// simple-math.cpp
#include <iostream>
#include <sstream>
#include <vector>
#include <stack>
#include <deque>
#include <stdexcept>
#include <cctype>
#include <cassert>
using namespace std;

static const int TERMINAL = 'S';

enum marker
{
    marker_id,
    marker_as,
    marker_md,
    marker_paren
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

class parse_error : public exception
{
public:
    virtual const char* what() const throw()
    { return "Couldn't parse input string"; }
};

prefix_expr& collapse(stack<prefix_expr>& exprs)
{
    if (exprs.size() > 1) {
        prefix_expr old = exprs.top();
        exprs.pop();
        exprs.top().insert(exprs.top().end(),old.begin(),old.end());
    }
    return exprs.top();
}

prefix_expr& expand(stack<prefix_expr>& exprs)
{
    exprs.emplace();
    return exprs.top();
}

prefix_expr parse(string input)
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
                    collapse(exprs).emplace_front(token_operator,*it);
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
                }
                else
                    throw parse_error();
                stk.push(marker_md);
                state = 0;
            }
            else if (*it == TERMINAL) {
                // at end of input; include operand in current expression and
                // transition to accept state
                expr.emplace_back(token_operand,n);
                if (stk.empty())
                    state = 5;
            }
            else if (*it == ')') {
                // transition to separate state to handle close parentheses
                // case; include operand with current expression
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
                    else if (top == marker_as)
                        expr.emplace_front(token_operator,*it);
                    stk.push(marker_md);
                    state = 0;
                }
                else if (*it == ')')
                    collapse(exprs);
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

void code_gen_recursive(prefix_expr& expr,int state = 0)
{
    token tok = expr.front();
    expr.pop_front();
    if (state == 0) {
        code_gen_recursive(expr,1);
        code_gen_recursive(expr,2);
        if (tok.value == '+')
            cout << "add $a0, $v0, $v1\n";
        else if (tok.value == '-')
            cout << "sub $a0, $v0, $v1\n";
        else if (tok.value == '*') {
            cout << "mult $v0, $v1\n"
                 << "mflo $a0\n";
        }
        else if (tok.value == '/') {
            cout << "div $v0, $v1\n"
                 << "mflo $a0\n";
        }
    }
    else if (state == 1) {
        if (tok.kind == token_operator) {
            code_gen_recursive(expr,1);
            code_gen_recursive(expr,2);
            if (tok.value == '+')
                cout << "add $v0, $v0, $v1\n";
            else if (tok.value == '-')
                cout << "sub $v0, $v0, $v1\n";
            else if (tok.value == '*') {
                cout << "mult $v0, $v1\n"
                     << "mflo $v0\n";
            }
            else if (tok.value == '/') {
                cout << "div $v0, $v1\n"
                     << "mflo $v0\n";
            }
        }
        else
            cout << "li $v0, " << tok.value << '\n';
    }
    else if (state == 2) {
        if (tok.kind == token_operator) {
            code_gen_recursive(expr,2);
            code_gen_recursive(expr,3);
            if (tok.value == '+')
                cout << "add $v1, $v1, $t0\n";
            else if (tok.value == '-')
                cout << "sub $v1, $v1, $t0\n";
            else if (tok.value == '*') {
                cout << "mult $v1, $t0\n"
                     << "mflo $v1\n";
            }
            else if (tok.value == '/') {
                cout << "div $v1, $t0\n"
                     << "mflo $v1\n";
            }
        }
        else
            cout << "li $v1, " << tok.value << '\n';
    }
    else if (state == 3) {
        assert(tok.kind == token_operand);
        cout << "li $t0, " << tok.value << '\n';
    }
}

void code_gen(prefix_expr& expr)
{
    // print out the prefix expression on standard error so we can see it
    auto copy = expr;
    while (!copy.empty()) {
        cerr << copy.front() << ' ';
        copy.pop_front();
    }
    cerr.put('\n');

    // now generate the assembly instructions and write them to standard output
    // so we can pass them to the assembler
    cout << ".text\n";

    if (expr.size() == 1) // special case of no operator
        cout << "li $a0, " << expr.front() << endl;
    else
        code_gen_recursive(expr);

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
