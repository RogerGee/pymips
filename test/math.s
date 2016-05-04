        .data
stuff:  .space  32
msg:    .asciiz "The result is "
newl:   .asciiz "\n"

        .text
        la      $t4, stuff
        li      $t0, 33
        li      $t1, 12

        ## addition
        add     $t2, $t0, $t1
        sw      $t2, ($t4)

        ## subtraction
        sub     $t2, $t0, $t1
        sw      $t2, 4($t4)

        ## multiplication
        mul     $t2, $t0, $t1
        sw      $t2, 8($t4)

        ## division (and mod)
        div     $t0, $t1
        mflo    $t2
        sw      $t2, 12($t4)
        mfhi    $t2
        sw      $t2, 16($t4)

        li      $t0, 8
top:    
        lw      $a0, ($t4)
        li      $v0, 1
        syscall
        li      $v0, 11
        li      $a0, 32
        syscall
        addi    $t4, $t4, 4
        addi    $t0, $t0, -1
        bne     $0, $t0, top

        li      $v0, 4
        la      $a0, newl
        syscall
        li      $v0, 10
        syscall
