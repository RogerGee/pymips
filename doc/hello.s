    .data
message:    .asciiz "Hello, World!\n"

    .text
    la  $a0, message        # load address of string to print
    li  $v0, 4              # load syscall number for print_string
    syscall                 # perform system call
