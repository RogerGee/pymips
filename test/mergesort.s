    .text
    jal main
    move $a0, $v0
    li $v0, 10
    syscall
print_int:
    addiu   $sp,$sp,-8
    sw  $fp,4($sp)
    move    $fp,$sp
    li  $v0, 1
    syscall
    move    $sp,$fp
    lw  $fp,4($sp)
    addiu   $sp,$sp,8
    jr   $ra
print_character:
    addiu   $sp,$sp,-8
    sw  $fp,4($sp)
    move    $fp,$sp
    li  $v0, 11
    syscall
    move    $sp,$fp
    lw  $fp,4($sp)
    addiu   $sp,$sp,8
    jr   $ra
read_int:
    addiu   $sp,$sp,-8
    sw  $fp,4($sp)
    sw  $s0,0($sp)
    move    $fp,$sp
    li  $v0, 5
    syscall
    move    $s0, $v0
    move    $v0,$s0
    move    $sp,$fp
    lw  $fp,4($sp)
    lw  $s0,0($sp)
    addiu   $sp,$sp,8
    jr   $ra
main:
    addiu   $sp,$sp,-544
    sw  $ra,540($sp)
    sw  $fp,536($sp)
    sw  $s1,532($sp)
    sw  $s0,528($sp)
    move    $fp,$sp
    jal read_int
    move    $s1,$v0
    move    $s0,$0
    j   $L6
$L7:
    jal read_int
    move    $v1,$v0
    sll $v0,$s0,2
    addiu   $a0,$fp,16
    addu    $v0,$a0,$v0
    sw  $v1,0($v0)
    addiu   $s0,$s0,1
$L6:
    slt $v0,$s0,$s1
    bne $v0,$0,$L7
    addiu   $v0,$fp,16
    move    $a0,$v0
    move    $a1,$s1
    jal mergesort
    move    $s0,$0
    j   $L8
$L9:
    sll $v0,$s0,2
    addiu   $v1,$fp,16
    addu    $v0,$v1,$v0
    lw  $v0,0($v0)
    move    $a0,$v0
    jal print_int
    li  $a0,32
    jal print_character
    addiu   $s0,$s0,1
$L8:
    slt $v0,$s0,$s1
    bne $v0,$0,$L9
    li  $a0,10
    jal print_character
    move    $v0,$0
    move    $sp,$fp
    lw  $ra,540($sp)
    lw  $fp,536($sp)
    lw  $s1,532($sp)
    lw  $s0,528($sp)
    addiu   $sp,$sp,544
    jr   $ra
    .globl  merge
merge:
    addiu   $sp,$sp,-536
    sw  $fp,532($sp)
    sw  $s4,528($sp)
    sw  $s3,524($sp)
    sw  $s2,520($sp)
    sw  $s1,516($sp)
    sw  $s0,512($sp)
    move    $fp,$sp
    sw  $a0,536($fp)
    sw  $a1,540($fp)
    sw  $a2,544($fp)
    sw  $a3,548($fp)
    move    $s1,$0
    move    $s2,$s1
    move    $s0,$s2
$L17:
    lw  $v0,544($fp)
    slt $v0,$s0,$v0
    andi    $v0,$v0,255
    move    $s4,$v0
    lw  $v0,548($fp)
    slt $v0,$s2,$v0
    andi    $v0,$v0,255
    move    $s3,$v0
    bne $s4,$0,$L12
    beq $s3,$0,$L21
$L12:
    beq $s4,$0,$L14
    beq $s3,$0,$L15
    move    $v0,$s0
    sll $v0,$v0,2
    lw  $v1,536($fp)
    addu    $v0,$v1,$v0
    lw  $v1,0($v0)
    move    $v0,$s2
    sll $v0,$v0,2
    lw  $a0,540($fp)
    addu    $v0,$a0,$v0
    lw  $v0,0($v0)
    slt $v0,$v1,$v0
    beq $v0,$0,$L14
$L15:
    move    $v0,$s0
    sll $v0,$v0,2
    lw  $v1,536($fp)
    addu    $v0,$v1,$v0
    lw  $v1,0($v0)
    sll $v0,$s1,2
    addu    $v0,$fp,$v0
    sw  $v1,0($v0)
    addiu   $s0,$s0,1
    j   $L16
$L14:
    move    $v0,$s2
    sll $v0,$v0,2
    lw  $v1,540($fp)
    addu    $v0,$v1,$v0
    lw  $v1,0($v0)
    sll $v0,$s1,2
    addu    $v0,$fp,$v0
    sw  $v1,0($v0)
    addiu   $s2,$s2,1
$L16:
    addiu   $s1,$s1,1
    j   $L17
$L21:
    nop
$L20:
    move    $s0,$0
    j   $L18
$L19:
    move    $v0,$s0
    sll $v0,$v0,2
    lw  $v1,536($fp)
    addu    $v0,$v1,$v0
    sll $v1,$s0,2
    addu    $v1,$fp,$v1
    lw  $v1,0($v1)
    sw  $v1,0($v0)
    addiu   $s0,$s0,1
$L18:
    slt $v0,$s0,$s1
    bne $v0,$0,$L19
    move    $sp,$fp
    lw  $fp,532($sp)
    lw  $s4,528($sp)
    lw  $s3,524($sp)
    lw  $s2,520($sp)
    lw  $s1,516($sp)
    lw  $s0,512($sp)
    addiu   $sp,$sp,536
    jr   $ra
    .globl  mergesort
mergesort:
    addiu   $sp,$sp,-32
    sw  $ra,28($sp)
    sw  $fp,24($sp)
    sw  $s1,20($sp)
    sw  $s0,16($sp)
    move    $fp,$sp
    sw  $a0,32($fp)
    sw  $a1,36($fp)
    lw  $v1,36($fp)
    li  $v0,1
    beq $v1,$v0,$L25
$L23:
    lw  $v0,36($fp)
    srl $v1,$v0,31
    addu    $v0,$v1,$v0
    sra $v0,$v0,1
    move    $s0,$v0
    lw  $v0,36($fp)
    subu    $s1,$v0,$s0
    lw  $a0,32($fp)
    move    $a1,$s0
    jal mergesort
    move    $v0,$s0
    sll $v0,$v0,2
    lw  $v1,32($fp)
    addu    $v0,$v1,$v0
    move    $a0,$v0
    move    $a1,$s1
    jal mergesort
    move    $v0,$s0
    sll $v0,$v0,2
    lw  $v1,32($fp)
    addu    $v0,$v1,$v0
    lw  $a0,32($fp)
    move    $a1,$v0
    move    $a2,$s0
    move    $a3,$s1
    jal merge
    j   $L22
$L25:
    nop
$L22:
    move    $sp,$fp
    lw  $ra,28($sp)
    lw  $fp,24($sp)
    lw  $s1,20($sp)
    lw  $s0,16($sp)
    addiu   $sp,$sp,32
    jr   $ra
