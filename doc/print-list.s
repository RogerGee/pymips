        .data
list:   .word 859, 613, 31, 660, 200, 538
end:    .byte 0
        .text
start:  la      $t0, list       # load address of list
        la      $t1, end        # load end address of list (one past last elem)
top:    lw      $a0, ($t0)      # load value at current address
        li      $v0, 1          # load syscall number for print_int
        syscall                 # print_int()
        li      $v0, 11         # load syscall number for print_character
        li      $a0, 32         # load value of ASCII ' ' (space) character
        syscall                 # print_character
        addi    $t0, $t0, 4     # update address pointer to next element
        bne     $t0, $t1, top   # check if at end of list; if not loop
        li      $v0, 11         # print newline character
        li      $a0, 10
        syscall
        li      $v0, 10         # do exit
        li      $a0, 0          # process return code set to 0
        syscall
