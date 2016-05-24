// simple-math.cpp
#include <iostream>
#include <sstream>
#include <vector>
#include <stack>
#include <deque>
#include <stdexcept>
#include <algorithm>
#include <cctype>
#include <cassert>
using namespace std;

static const int TERMINAL = 'S';

enum marker
{
    marker_id,
    marker_as,
    marker_md,
    marker_paren,
    marker_expand
};

enum token_kind
{
    token_operator,
    token_operand
};

struct token
{
    int kind;
    int value;

    token() {}
    token(int pkind,int pvalue)
        : kind(pkind),value(pvalue) {}
};

static ostream& operator <<(ostream& stream,const token& tok)
{
    if (tok.kind == token_operator)
        stream << char(tok.value);
    else
        stream << tok.value;
    return stream;
}

typedef deque<token> prefix_expr;

static void print_expr(const prefix_expr& ex)
{
    auto cpy(ex);
    while (!cpy.empty()) {
        cerr << cpy.front() << ' ';
        cpy.pop_front();
    }
    cerr.put('\n');
}

class parse_error : public exception
{
public:
    virtual const char* what() const throw()
    { return "Couldn't parse input string"; }
};

static prefix_expr& collapse(stack<prefix_expr>& exprs)
{
    if (exprs.size() > 1) {
        prefix_expr old = exprs.top();
        exprs.pop();
        exprs.top().insert(exprs.top().end(),old.begin(),old.end());
    }
    return exprs.top();
}

static prefix_expr& expand(stack<prefix_expr>& exprs)
{
    exprs.emplace();
    return exprs.top();
}

static prefix_expr parse(string input)
{
    int state = 0;
    stack<int> stk;
    stringstream ss;
    string::const_iterator it;
    stack<prefix_expr> exprs;

    // add terminal symbol to end of input string
    input += TERMINAL;
    it = input.begin();

    stk.push(marker_id);
    expand(exprs);
    while (it != input.end()) {
        int top = stk.top();
        prefix_expr& expr = exprs.top();

        // this state means we try to read the beginning of either a term or a
        // parenthesized expression
        if (state == 0) {
            if (top == marker_id || top == marker_as
                || top == marker_md)
            {
                if (*it == '(') {
                    stk.push(marker_paren);
                    stk.push(marker_id);
                    expand(exprs);
                }
                else if (isdigit(*it)) {
                    ss.put(*it);
                    state = 1;
                }
                else if (*it == '-') {
                    ss.put(*it);
                    state = 2;
                }
                else
                    throw parse_error();
            }
            else
                throw parse_error();
        }

        // this state reads a digit, then transitions to applying it in state 3
        else if (state == 1) {
            if (isdigit(*it)) {
                ss.put(*it);
            }
            else {
                --it; // don't consume input symbol
                state = 3;
            }
        }

        // this state ensures one digit is read before potentially reading
        // others in state 1
        else if (state == 2) {
            if (isdigit(*it)) {
                ss.put(*it);
                state = 1;
            }
            else
                throw parse_error();
        }

        // this state expects there to be a term inside the stringstream; we
        // convert it to an integer and expect an operator, close parentheses or
        // end of input
        else if (state == 3) {
            int n;
            ss >> n;
            ss.str("");
            ss.seekg(0);
            ss.seekp(0);
            stk.pop();
            if (*it == '+' || *it == '-') {
                if (top == marker_id || top == marker_as) {
                    // free to build prefix expression in the usual way
                    expr.emplace_front(token_operator,*it);
                    expr.emplace_back(token_operand,n);
                }
                else if (top == marker_md) {
                    // exit higher precedence scope (collapse subexpression down
                    // into the previous expression, if any); note the term is
                    // included with the previous expression
                    expr.emplace_back(token_operand,n);
                    if (!stk.empty() && stk.top() == marker_expand) {
                        collapse(exprs).emplace_front(token_operator,*it);
                        stk.pop();
                    }
                    else
                        expr.emplace_front(token_operator,*it);
                }
                else
                    throw parse_error();
                stk.push(marker_as);
                state = 0;
            }
            else if (*it == '*' || *it == '/') {
                if (top == marker_id || top == marker_md) {
                    // free to build prefix expression in the usual way
                    expr.emplace_front(token_operator,*it);
                    expr.emplace_back(token_operand,n);
                }
                else if (top == marker_as) {
                    // begin higher precedence scope by pushing on a new
                    // subexpression
                    auto& newexpr = expand(exprs);
                    newexpr.emplace_front(token_operator,*it);
                    newexpr.emplace_back(token_operand,n);
                    stk.push(marker_expand);
                }
                else
                    throw parse_error();
                stk.push(marker_md);
                state = 0;
            }
            else if (*it == TERMINAL) {
                // at end of input; include operand in current expression and
                // transition to accept state
                if (!stk.empty() && stk.top() == marker_expand) {
                    collapse(exprs).emplace_back(token_operand,n);
                    stk.pop();
                }
                else
                    expr.emplace_back(token_operand,n);
                if (stk.empty())
                    state = 5;
            }
            else if (*it == ')') {
                // transition to separate state to handle close parentheses
                // case; include operand with current expression
                if (stk.top() == marker_expand) { // stack should be non-empty
                    collapse(exprs).emplace_back(token_operand,n);
                    stk.pop();
                }
                else
                    expr.emplace_back(token_operand,n);
                state = 4;
            }
            else
                throw parse_error();
        }

        // this state handles matching parentheses and handling the start of any
        // expression that appears after a ')'
        else if (state == 4) {
            if (!stk.empty() && top == marker_paren) {
                stk.pop(); // marker_paren
                top = stk.top();
                stk.pop(); // context marker
                if (*it == '+' || *it == '-') {
                    if (top == marker_id || marker_as)
                        collapse(exprs).emplace_front(token_operator,*it);
                    else if (top == marker_md) {
                        // the parenthesized expression was part of a mult/div
                        // expression; collapse the parenthesized expression
                        // down first, then collapse the mult/div expression
                        collapse(exprs);
                        collapse(exprs).emplace_front(token_operator,*it);
                    }
                    stk.push(marker_as);
                    state = 0;
                }
                else if (*it == '*' || *it == '/') {
                    if (top == marker_id || top == marker_md)
                        collapse(exprs).emplace_front(token_operator,*it);
                    else if (top == marker_as) {
                        expr.emplace_front(token_operator,*it);
                        stk.push(marker_expand);
                    }
                    stk.push(marker_md);
                    state = 0;
                }
                else if (*it == ')') {
                    if (stk.top() == marker_expand) {
                        collapse(exprs);
                        stk.pop();
                    }
                    collapse(exprs);
                }
                else if (*it == TERMINAL)
                    state = 5;
                else
                    throw parse_error();
            }
            else
                throw parse_error();
        }

        ++it;
    }

    if (state != 5)
        throw parse_error();

    while (exprs.size() > 1)
        collapse(exprs);

    return exprs.top();
}

// static void code_gen_recursive(prefix_expr& expr,int state = 0)
// {
//     token tok;
//     static const char* const REGS[] = {
//         "$a0","$v0", "$v1", "$a1", "$a2", "$a3",
//         "$t0", "$t1", "$t2", "$t3", "$t4", "$t5",
//         "$t6", "$t7", "$t8", "$s0", "$s1", "$s2",
//         "$s3", "$s4", "$s5", "$s6", "$s7"
//     };
//
//     tok = expr.front();
//     expr.pop_front();
//
//     if (tok.kind == token_operator) {
//         int a, b;
//         token next = expr.front();
//         if (next.kind == token_operand) {
//             // try to search ahead for a deeper nested expression to evaluate;
//             // this is only a heuristic that on average decreases register usage
//             a = state+1, b = state;
//             expr.pop_front();
//             code_gen_recursive(expr,b);
//             expr.push_front(next);
//             code_gen_recursive(expr,a);
//         }
//         else {
//             a = state, b = state+1;
//             code_gen_recursive(expr,a);
//             code_gen_recursive(expr,b);
//         }
//         if (tok.value == '+') {
//             cout << "add " << REGS[state] << ", " << REGS[a]
//                  << ", " << REGS[b] << '\n';
//         }
//         else if (tok.value == '-') {
//             cout << "sub " << REGS[state] << ", " << REGS[a]
//                  << ", " << REGS[b] << '\n';
//         }
//         else if (tok.value == '*') {
//             cout << "mult " << REGS[a] << ", " << REGS[b]
//                  << "\nmflo " << REGS[state] << '\n';
//         }
//         else if (tok.value == '/') {
//             cout << "div " << REGS[a] << ", " << REGS[b]
//                  << "\nmflo " << REGS[state] << '\n';
//         }
//     }
//     else {
//         cout << "li " << REGS[state] << ", " << tok.value << '\n';
//     }
// }

/* note: the algorithm presented here (and the commented-out one above, which
   also works) is a little naive; depending on how nested the expression is, it
   will run out of registers to allocate; the solution would be to reuse
   registers via swapping to/from the stack but for simplicity we do not
   implement that functionality */

static void code_gen_iterative(prefix_expr& expr)
{
    int alloc = 0;
    stack<token> stk;
    static const char* const REGS[] = {
        "$a0","$v0", "$v1", "$a1", "$a2", "$a3",
        "$t0", "$t1", "$t2", "$t3", "$t4", "$t5",
        "$t6", "$t7", "$t8", "$s0", "$s1", "$s2",
        "$s3", "$s4", "$s5", "$s6", "$s7"
    };

    while (!expr.empty()) {
        token& tok = expr.back();
        if (tok.kind == token_operand) {
            // push operand onto the stack
            stk.push(tok);
        }
        else { // token_operator
            // pop off two operands from the stack and allocate registers for
            // them; the operands could be some combination of literal values or
            // pre-allocated registers
            int regs[2];
            for (int i = 0,j = 0;i < 2;++i) {
                token& operand = stk.top();
                if (operand.kind == token_operator/*i.e. register*/)
                    regs[i] = operand.value;
                else {
                    regs[i] = alloc + j++;
                    cout << "li " << REGS[regs[i]] << ", " << operand.value << '\n';
                }
                stk.pop();
            }

            // since we pop the values off, whatever registers that were in use
            // can be deallocated; since we allocate them contiguously, then the
            // next available register is the minimum one of the pair
            alloc = min(regs[0],regs[1]);

            if (tok.value == '+') {
                cout << "add " << REGS[alloc] << ", " << REGS[regs[0]]
                     << ", " << REGS[regs[1]];
            }
            else if (tok.value == '-') {
                cout << "sub " << REGS[alloc] << ", " << REGS[regs[0]]
                     << ", " << REGS[regs[1]];
            }
            else if (tok.value == '*') {
                cout << "mult " << REGS[regs[0]] << ", " << REGS[regs[1]]
                     << "\nmflo " << REGS[alloc];
            }
            else if (tok.value == '/') {
                cout << "div " << REGS[regs[0]] << ", " << REGS[regs[1]]
                     << "\nmflo " << REGS[alloc];
            }
            cout.put('\n');
            stk.push(token(token_operator/*register*/,alloc));
            alloc += 1;
        }
        expr.pop_back();
    }
}

static void code_gen(prefix_expr& expr)
{
    // print out the prefix expression on standard error so we can see it
    print_expr(expr);

    // now generate the assembly instructions and write them to standard output
    // so we can pass them to the assembler
    cout << ".text\n";
    code_gen_iterative(expr);

    // print out the answer and add runtime-related code to terminate the
    // process cleanly
    cout << "li $v0, 1\n"
        "syscall\n"
        "li $a0, 10\n"
        "li $v0, 11\n"
        "syscall\n"
        "li $v0, 10\n"
        "li $a0, 0\n"
        "syscall\n";
}

int main(int argc,const char* argv[])
{
    string input;
    prefix_expr expr;

    // read all input from stdin into the buffer
    while (true) {
        char buffer[128];
        cin.read(buffer,sizeof(buffer));
        if (cin.bad())
            break;
        for (streamsize i = 0;i < cin.gcount();++i)
            if (!isspace(buffer[i]))
                input += buffer[i];
        if (cin.eof())
            break;
    }

    // obtain a deque that represents the source code in its parsed form
    try {
        expr = parse(input);
    } catch (parse_error) {
        cerr << argv[0] << ": parse error: the expression was malformed\n";
        return 1;
    }

    // then generate the assembly code as output
    code_gen(expr);
}
