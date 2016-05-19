        .text
main:   addiu   $sp, $sp, -16   # allocate stack space for arguments to callee
        
        ## read integer to pass to 'fib'
        li  $v0, 5
        syscall
        move    $a0, $v0

        ## invoke 'fib' to compute value; then print it out followed
	    ## by a newline character
        jal fib
        move    $a0, $v0
        li  $v0, 1
        syscall
        li  $a0, 10
        li  $v0, 11
        syscall
        
        ## do exit
        li  $v0, 10
        li  $a0, 0
        syscall

fib:    addiu   $sp, $sp, -24   # allocate stack frame
        sw  $s0, 16($sp)        # save the save register we use here
        sw  $ra, 20($sp)        # save return address
        slti    $v0, $a0, 2     # check for base case
        beq $v0, $0, l2         # go to recursive case if not set
        move    $v0, $a0        # set return value to argument
        j   l1                  # go to return instructions
l2:     sw  $a0, 24($sp)        # save argument to stack
        addiu   $a0, $a0, -1    # compute n-1
        jal fib                 # make first recursive call
        move    $s0, $v0        # save return value in save register
        lw  $a0, 24($sp)        # restore argument
        addiu   $a0, $a0, -2    # compute n-2
        jal fib                 # make second recursive call
        add $v0, $s0, $v0       # compute return value
l1:     lw  $ra, 20($sp)        # restore return address
        lw  $s0, 16($sp)        # restore save register
        addiu   $sp, $sp, 24    # deallocate stack frame
        jr  $ra                 # return from procedure
