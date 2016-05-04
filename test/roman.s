	.text
    jal main
    li $v0,10
    syscall
print_int:
	addiu	$sp,$sp,-8
	sw	$fp,4($sp)
	move	$fp,$sp
	li	$v0, 1
	syscall
	move	$sp,$fp
	lw	$fp,4($sp)
	addiu	$sp,$sp,8
	jr	$ra
print_string:
	addiu	$sp,$sp,-8
	sw	$fp,4($sp)
	move	$fp,$sp
	li	$v0, 4
	syscall
	move	$sp,$fp
	lw	$fp,4($sp)
	addiu	$sp,$sp,8
	jr	$ra
read_string:
	addiu	$sp,$sp,-8
	sw	$fp,4($sp)
	move	$fp,$sp
	li	$v0, 8
	syscall
	move	$sp,$fp
	lw	$fp,4($sp)
	addiu	$sp,$sp,8
	jr	$ra
	.data
NUMERALS:
	.byte	73
	.byte	86
	.byte	88
	.byte	76
	.byte	67
	.byte	68
	.byte	77
	.data
VALUES:
	.word	1
	.word	5
	.word	10
	.word	50
	.word	100
	.word	500
	.word	1000
$LC0:
	.asciiz	"As Roman numeral: \000"
$LC1:
	.asciiz	"As decimal: \000"
$LC2:
	.asciiz	"\012\000"
	.text
	.globl	main
main:
	addiu	$sp,$sp,-160
	sw	$ra,156($sp)
	sw	$fp,152($sp)
	move	$fp,$sp
	addiu	$v0,$fp,20
	move	$a0,$v0
	li	$a1,128			# 0x80
	jal	read_string
	lb	$v0,20($fp)
	slti	$v0,$v0,48
	bne	$v0,$0,$L5
	lb	$v0,20($fp)
	slti	$v0,$v0,58
	beq	$v0,$0,$L5
	addiu	$v0,$fp,20
	move	$a0,$v0
	jal	atoi
	move	$v1,$v0
	addiu	$v0,$fp,20
	move	$a0,$v1
	move	$a1,$v0
	jal	convert_decimal_to_numeral
	la	$a0,$LC0
	jal	print_string
	addiu	$v0,$fp,20
	move	$a0,$v0
	jal	print_string
	j	$L6
$L5:
	addiu	$v0,$fp,20
	move	$a0,$v0
	jal	convert_numeral_to_decimal
	sw	$v0,16($fp)
	la	$a0,$LC1
	jal	print_string
	lw	$a0,16($fp)
	jal	print_int
$L6:
	la	$a0,$LC2
	jal	print_string
	move	$v0,$0
	move	$sp,$fp
	lw	$ra,156($sp)
	lw	$fp,152($sp)
	addiu	$sp,$sp,160
	jr	$ra
atoi:
	addiu	$sp,$sp,-16
	sw	$fp,12($sp)
	move	$fp,$sp
	sw	$a0,16($fp)
	sw	$0,0($fp)
	sw	$0,4($fp)
	j	$L9
$L11:
	lw	$v0,0($fp)
	sll	$v0,$v0,1
	sll	$v1,$v0,2
	addu	$v0,$v0,$v1
	sw	$v0,0($fp)
	lw	$v0,4($fp)
	lw	$v1,16($fp)
	addu	$v0,$v1,$v0
	lb	$v0,0($v0)
	addiu	$v0,$v0,-48
	lw	$v1,0($fp)
	addu	$v0,$v1,$v0
	sw	$v0,0($fp)
	lw	$v0,4($fp)
	addiu	$v0,$v0,1
	sw	$v0,4($fp)
$L9:
	lw	$v0,4($fp)
	lw	$v1,16($fp)
	addu	$v0,$v1,$v0
	lb	$v0,0($v0)
	beq	$v0,$0,$L10
	lw	$v0,4($fp)
	lw	$v1,16($fp)
	addu	$v0,$v1,$v0
	lb	$v1,0($v0)
	li	$v0,10			# 0xa
	bne	$v1,$v0,$L11
$L10:
	lw	$v0,0($fp)
	move	$sp,$fp
	lw	$fp,12($sp)
	addiu	$sp,$sp,16
	jr	$ra
convert_numeral_to_decimal:
	addiu	$sp,$sp,-24
	sw	$fp,20($sp)
	move	$fp,$sp
	sw	$a0,24($fp)
	sw	$0,0($fp)
	j	$L14
$L22:
	sw	$0,4($fp)
	j	$L15
$L21:
	lw	$v0,24($fp)
	lb	$v1,0($v0)
	lw	$a0,4($fp)
	la	$v0,NUMERALS
	addu	$v0,$a0,$v0
	lb	$v0,0($v0)
	bne	$v1,$v0,$L16
	lw	$v0,4($fp)
	addiu	$v0,$v0,1
	sw	$v0,8($fp)
	lw	$v0,24($fp)
	addiu	$v0,$v0,1
	sw	$v0,12($fp)
	lw	$v0,4($fp)
	andi	$v0,$v0,1
	bne	$v0,$0,$L17
	lw	$v1,4($fp)
	li	$v0,6			# 0x6
	beq	$v1,$v0,$L17
	lw	$v0,12($fp)
	lb	$v0,0($v0)
	beq	$v0,$0,$L17
	lw	$v0,12($fp)
	lb	$v1,0($v0)
	lw	$a0,8($fp)
	la	$v0,NUMERALS
	addu	$v0,$a0,$v0
	lb	$v0,0($v0)
	beq	$v1,$v0,$L18
	lw	$v0,12($fp)
	lb	$v1,0($v0)
	lw	$v0,8($fp)
	addiu	$v0,$v0,1
	sw	$v0,8($fp)
	lw	$a0,8($fp)
	la	$v0,NUMERALS
	addu	$v0,$a0,$v0
	lb	$v0,0($v0)
	bne	$v1,$v0,$L17
$L18:
	lw	$v0,12($fp)
	sw	$v0,24($fp)
	lw	$v0,8($fp)
	sll	$v1,$v0,2
	la	$v0,VALUES
	addu	$v0,$v1,$v0
	lw	$v1,0($v0)
	lw	$v0,4($fp)
	sll	$a0,$v0,2
	la	$v0,VALUES
	addu	$v0,$a0,$v0
	lw	$v0,0($v0)
	subu	$v0,$v1,$v0
	lw	$v1,0($fp)
	addu	$v0,$v1,$v0
	sw	$v0,0($fp)
	j	$L20
$L17:
	lw	$v0,4($fp)
	sll	$v1,$v0,2
	la	$v0,VALUES
	addu	$v0,$v1,$v0
	lw	$v0,0($v0)
	lw	$v1,0($fp)
	addu	$v0,$v1,$v0
	sw	$v0,0($fp)
	j	$L20
$L16:
	lw	$v0,4($fp)
	addiu	$v0,$v0,1
	sw	$v0,4($fp)
$L15:
	lw	$v0,4($fp)
	slti	$v0,$v0,7
	bne	$v0,$0,$L21
$L20:
	lw	$v0,24($fp)
	addiu	$v0,$v0,1
	sw	$v0,24($fp)
$L14:
	lw	$v0,24($fp)
	lb	$v0,0($v0)
	bne	$v0,$0,$L22
	lw	$v0,0($fp)
	move	$sp,$fp
	lw	$fp,20($sp)
	addiu	$sp,$sp,24
	jr	$ra
convert_decimal_to_numeral:
	addiu	$sp,$sp,-24
	sw	$fp,20($sp)
	move	$fp,$sp
	sw	$a0,24($fp)
	sw	$a1,28($fp)
	sw	$0,0($fp)
	j	$L25
$L33:
	li	$v0,6			# 0x6
	sw	$v0,4($fp)
	j	$L26
$L32:
	lw	$v0,4($fp)
	sll	$v1,$v0,2
	la	$v0,VALUES
	addu	$v0,$v1,$v0
	lw	$v1,0($v0)
	lw	$v0,24($fp)
	slt	$v0,$v0,$v1
	bne	$v0,$0,$L27
	lw	$v0,0($fp)
	lw	$v1,28($fp)
	addu	$v0,$v1,$v0
	lw	$a0,4($fp)
	la	$v1,NUMERALS
	addu	$v1,$a0,$v1
	lb	$v1,0($v1)
	sb	$v1,0($v0)
	lw	$v0,0($fp)
	addiu	$v0,$v0,1
	sw	$v0,0($fp)
	lw	$v0,4($fp)
	sll	$v1,$v0,2
	la	$v0,VALUES
	addu	$v0,$v1,$v0
	lw	$v0,0($v0)
	lw	$v1,24($fp)
	subu	$v0,$v1,$v0
	sw	$v0,24($fp)
	j	$L26
$L27:
	lw	$v0,4($fp)
	blez	$v0,$L28
	lw	$v0,4($fp)
	andi	$v0,$v0,1
	bne	$v0,$0,$L29
	li	$v0,2			# 0x2
	j	$L30
$L29:
	li	$v0,1			# 0x1
$L30:
	lw	$v1,4($fp)
	subu	$v0,$v1,$v0
	sw	$v0,8($fp)
	lw	$v0,4($fp)
	sll	$v1,$v0,2
	la	$v0,VALUES
	addu	$v0,$v1,$v0
	lw	$v1,0($v0)
	lw	$v0,8($fp)
	sll	$a0,$v0,2
	la	$v0,VALUES
	addu	$v0,$a0,$v0
	lw	$v0,0($v0)
	subu	$v0,$v1,$v0
	sw	$v0,12($fp)
	lw	$v1,12($fp)
	lw	$v0,24($fp)
	slt	$v0,$v0,$v1
	bne	$v0,$0,$L31
	lw	$v0,0($fp)
	lw	$v1,28($fp)
	addu	$v0,$v1,$v0
	lw	$a0,8($fp)
	la	$v1,NUMERALS
	addu	$v1,$a0,$v1
	lb	$v1,0($v1)
	sb	$v1,0($v0)
	lw	$v0,0($fp)
	addiu	$v0,$v0,1
	sw	$v0,0($fp)
	lw	$v0,0($fp)
	lw	$v1,28($fp)
	addu	$v0,$v1,$v0
	lw	$a0,4($fp)
	la	$v1,NUMERALS
	addu	$v1,$a0,$v1
	lb	$v1,0($v1)
	sb	$v1,0($v0)
	lw	$v0,0($fp)
	addiu	$v0,$v0,1
	sw	$v0,0($fp)
	lw	$v1,24($fp)
	lw	$v0,12($fp)
	subu	$v0,$v1,$v0
	sw	$v0,24($fp)
	j	$L26
$L31:
	lw	$v0,4($fp)
	addiu	$v0,$v0,-1
	sw	$v0,4($fp)
	j	$L26
$L28:
	lw	$v0,4($fp)
	addiu	$v0,$v0,-1
	sw	$v0,4($fp)
$L26:
	lw	$v0,4($fp)
	bgez	$v0,$L32
$L25:
	lw	$v0,24($fp)
	bgtz	$v0,$L33
	lw	$v0,0($fp)
	lw	$v1,28($fp)
	addu	$v0,$v1,$v0
	sb	$0,0($v0)
	lw	$v0,0($fp)
	addiu	$v0,$v0,1
	sw	$v0,0($fp)
	move	$sp,$fp
	lw	$fp,20($sp)
	addiu	$sp,$sp,24
	jr	$ra
