        .text
start:  la      $t0, stuff
        li      $v0, 5          # load syscall number for read_int
        syscall                 # read_int()
        sh      $v0, ($t0)      # store low half word in data segment
        li      $v0, 5
        syscall                 # read_int()
        sh      $v0, 2($t0)     # store high half word in data segment
        la      $a0, message    # load string to print
        li      $v0, 4          # load syscall number for print_string
        syscall                 # print_string()
        lw      $a0, ($t0)      # load resulting word value
        li      $v0, 1          # load syscall number for print_int
        syscall                 # print_int()
        li      $a0, 10         # load ASCII character '\n'
        li      $v0, 11         # load syscall number for print_character
        syscall                 # print_character()
        li      $v0, 10         # load syscall number for exit
        li      $a0, 0          # load argument (process return code)
        syscall                 # exit()

        .data
message:  .asciiz "The combined value is "
stuff:    .space 4
