        .text
        jal     main
        li      $v0, 10
        syscall
print_string:
        addiu   $sp,$sp,-8
        sw      $fp,4($sp)
        move    $fp,$sp
        li      $v0, 4
        syscall
        move    $sp,$fp
        lw      $fp,4($sp)
        addiu   $sp,$sp,8
        jr      $ra
        .data
$LC0:
        .asciiz "Hello, World!\012"
        .text
        .globl  main
main:
        addiu   $sp,$sp,-24
        sw      $ra,20($sp)
        sw      $fp,16($sp)
        move    $fp,$sp
        la      $a0,$LC0
        jal     print_string
        move    $v0,$0
        move    $sp,$fp
        lw      $ra,20($sp)
        lw      $fp,16($sp)
        addiu   $sp,$sp,24
        jr      $ra
