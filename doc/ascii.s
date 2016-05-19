        .text
start:
        ## call 'foo' and then exit
        jal foo
        li  $v0, 10
        li  $a0, 0
        syscall

foo:    addiu     $sp, $sp, -128 # allocate stack frame
        la  $a0, 0($sp)          # load address of buffer
        li  $a1, 128             # load size of buffer
        li  $v0, 8               # load syscall no. for read_string
        syscall                  # read_string()
        move $t0, $v0            # save number of characters read (n)
        li  $t1, 0               # load iterator (i)
l2:     slt $v0, $t1, $t0        # do comparison
        beq $v0, $0, l1          # branch if comparison was false
        addu    $v0, $sp, $t1    # compute offset
        lb  $a0, ($v0)           # load character from memory
        li  $v0, 1               # load syscall no. for print_int
        syscall                  # print_int()
        li  $a0, 32              # load space character value (' ')
        li  $v0, 11              # load syscall no. for print_character
        syscall                  # print_character()
        addiu $t1, $t1, 1        # increment iterator
        j   l2                   # loop
l1:     li  $a0, 10              # load newline character value ('\n')
        li  $v0, 11              # load syscall no. for print_character
        syscall                  # print_character()
        addiu   $sp, $sp, 128    # deallocate stack frame
        jr $ra                   # return
