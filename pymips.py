#!/usr/bin/env python

# pymips.py

import re
import io
import os
import ctypes
import struct
import pickle
import argparse
from sys import exit
from sys import stdin
from sys import stdout
from sys import stderr

# MIPS Simulator: this program implements a simple MIPS simulator that
# both assembles and executes MIPS instructions. The simulator
# implements only a small subset of the MIPS architecture, documented
# here:
#
# Directives: the following directives serve as meta-instructions for
# the assembler
#
#  .text - begin code section
#  .data - begin data section
#  .globl <symbol> - define global symbol at location
#  .byte <value> [, <value>, ...]   - define byte in data section
#  .half <value> [, <value>, ...]   - define half-word in data section
#  .word <value> [, <value>, ...]   - define word in data section
#  .ascii <value>                   - define ascii string in data section
#  .asciiz <value>                  - define zero-terminated ascii
#                                     string in data section
#  .space <amount>                  - allocate bytes in data section
#
# Labels: labels are resolved to runtime addresses in the program's
# text/data segments; they have the following form:
#
#  <label>:
#   where label is any combination of [a-zA-Z0-9_$]
#
# Instructions: the simulator implements a subset of the complete MIPS
# instruction set (mainly arithmetic, logic and load/store);
# the simulator doesn't conceptualize puesdo-instructions, instead
# making them the same as normal instructions
#
#  add   $d, $s, $t  | $d = $s + $t               | add registers, signed
#  addu  $d, $s, $t  | $d = $s + $t               | add registers, unsigned
#  addi  $d, $s, i   | $d = $s + SE(i)            | add immediate, signed
#  addiu $d, $s, i   | $d = $s + SE(i)            | add immediate, unsigned
#  and   $d, $s, $t  | $d = $s & $t               | bit-and
#  andi  $d, $s, i   | $d = $s & ZE(i)            | bit-and immediate
#  div   $s, $t      | hi = $s % $t, lo = $s / $t | division, signed
#  divu  $s, $t      | hi = $s % $t, lo = $s / $t | division, unsigned
#  mul   $d, $s, $t  | $d = $s * $t               | multiplication, signed
#  mulu  $d, $s, $t  | $d = $s * $t               | multiplication, unsigned
#  mult  $s, $t      | hi:lo = $s*$t              | multiplication, signed
#  multu $s, $t      | hi:lo = $s*$t              | multiplication, unsigned
#  nor   $d, $s, $t  | $d = ~($s | $t)            | bit-not-or
#  or    $d, $s, $t  | $d = $s | $t               | bit-or
#  ori   $d, $s, i   | $d = $s | ZE(i)            | bit-or, immediate
#  rem   $d, $s, a   | $d = $s % $t               | remainder (by variable or constant)
#  sll   $d, $s, a   | $d = $s << a               | left-shift (by variable or constant)
#  sllv  $d, $s, $t  | $d = $s << $t              | same as 'sll'
#  sra   $d, $s, a   | $d = $s >> a  with sign-ex | arithmetic right-shift (by variable or constant)
#  srav  $d, $s, $t  | $d = $s >> $t with sign-ex | same as sra
#  srl   $d, $s, a   | $d = $s >> a               | logical right-shift (by variable or constant)
#  srlv  $d, $s, $t  | $d = $s >> $t              | same as srl
#  sub   $d, $s, $t  | $d = $s - $t               | subtraction, signed
#  subu  $d, $s, $t  | $d = $s - $t               | subtraction, unsigned
#  xor   $d, $s, $t  | $d = $s ^ $t               | bit-xor
#  xori  $d, $s, i   | $d = $s ^ ZE(i)            | bit-xor immediate
#
#  slt   $d, $s, $t  | $d = $s < $t               | set if less than signed
#  sltu  $d, $s, $t  | $d = $s < $t               | set if less than unsigned
#  slti  $d, $s, i   | $d = $s < SE(i)            | set if less than signed immediate
#  sltiu $d, $s, i   | $d = $s < SE(i)            | set if less than signed immediate
#
#  beq   $s, $t, lbl | if $s==$t goto lbl         | branch equal
#  bgez  $s, lbl     | if $s >= 0 goto lbl        | branch greater-than-or-equal-to zero
#  bgtz  $s, lbl     | if $s > 0 goto lbl         | branch greater-than zero
#  blez  $s, lbl     | if $s <= 0 goto lbl        | branch less-than-or-equal-to zero
#  bne   $s, $t, lbl | if $s!=$t goto lbl         | branch not-equal
#  blt   $s, $t, lbl | if $s < $t goto lbl        | branch less-than
#  bgt   $s, $t, lbl | if $s > $t goto lbl        | branch greater-than
#
#  j     lbl         | goto lbl                   | unconditional jump
#  jal   lbl         | $ra = addr and jump        | jump-and-link
#  jalr  $s          | $ra = addr and jump to $s  | jump-and-link (address in register)
#  jr    $s          | jump to $s                 | jump to address in register
#
#  la    $t, addr    | $t = addr                  | load literal, direct address (also supports indirect addressing)
#  lhi   $t, i       | HI($t) = i                 | load high half-word immediate
#  li    $t, i       | $t = i                     | load word immediate
#  llo   $t, i       | LO($t) = i                 | load low half-word immediate
#  lb    $t, i($s)   | $t = SE(MEM[$s+i]:1)       | load byte signed (also supports direct addressing)
#  lbu   $t, i($s)   | $t = ZE(MEM[$s+i]:1)       | load byte unsigned (also supports direct addressing)
#  lh    $t, i($s)   | $t = SE(MEM[$s+i]:2)       | load half-word signed (also supports direct addressing)
#  lhu   $t, i($s)   | $t = ZE(MEM[$s+i]:2)       | load half-word unsigned (also supports direct addressing)
#  lw    $t, i($s)   | $t = MEM[$s+i]:4           | load word (also supports direct addressing)
#  mfhi  $d          | $d = hi                    | move hi-register value
#  mflo  $d          | $d = lo                    | move lo-register value
#  move  $d, $t      | $d = $t                    | copy register to another
#  mthi  $d          | hi = $d                    | set hi-register value
#  mtlo  $d          | lo = $d                    | set lo-register value
#  sb    $t, i($s)   | MEM[$s+i]:1 = LB($t)       | store byte (also supports direct addressing)
#  sh    $t, i($s)   | MEM[$s+i]:2 = LB($t)       | store half-word (also supports direct addressing)
#  sw    $t, i($s)   | MEM[$s+i]:4 = LB($t)       | store word (also supports direct addressing)
#
#  nop               |                            | do absolutely nothing (waste a cycle)
#  syscall           |                            | initiate system routine
#

# error reporting helper function
def runtime_error(msg):
    stdout.flush()
    stderr.write("pymips: error: {}\n".format(msg))
    exit(1)
def error_on_line(msg,line):
    stdout.flush()
    stderr.write("pymips: error: line {0}: {1}\n".format(line,msg))
    exit(1)

# instruction functions: each function performs the operations of its
# corresponding instruction; if 'sim' is None, then the function
# checks to make sure 'parts' is formatted correctly

def check_register_instr(parts):
    # <REG> <REG> <REG>
    if len(parts) != 3 or not parts[0] in MIPS_REGISTERS or not parts[1] in MIPS_REGISTERS \
       or not parts[2] in MIPS_REGISTERS:
        return False
    return True

def check_register_instr2(parts):
    # <REG> <REG>
    if len(parts) != 2 or not parts[0] in MIPS_REGISTERS or not parts[1] in MIPS_REGISTERS:
        return False
    return True

REGEX_IMMED = re.compile('^-?[0-9]+$') # immediate must be an integer
def check_immed_instr(parts):
    # <REG> <REG> <IMMED>
    if len(parts) != 3 or not parts[0] in MIPS_REGISTERS or not parts[1] in MIPS_REGISTERS \
       or not REGEX_IMMED.match(parts[2]):
        return False
    # convert immediate string to integer
    parts[2] = int(parts[2])
    return True

def check_direct_instr(parts,**kwargs):
    # check direct addressing instruction
    # <REG> <LITERAL>
    # literal may already be converted
    if len(parts) != 2 or not parts[0] in MIPS_REGISTERS:
        return False
    # if we cannot convert the literal, then assume we have a
    # non-resolved label
    if not isinstance(parts[1],(int,long)) \
       and not REGEX_IMMED.match(parts[1]):
        runtime_error("line {1}: cannot resolve label '{0}'".format(parts[1],kwargs['line']))
    # convert immediate string to integer
    parts[1] = int(parts[1])
    return True

def check_direct_instr2(parts,**kwargs):
    # <REG> <REG> <LITERAL>
    # the literal may already be converted
    if len(parts) != 3 or not parts[0] in MIPS_REGISTERS or \
       not parts[1] in MIPS_REGISTERS:
        return False
    # if we cannot convert the literal, then assume we have a
    # non-resolved label
    if not isinstance(parts[2],(int,long)) \
       and not REGEX_IMMED.match(parts[2]):
        runtime_error("line {1}: cannot resolve label '{0}'".format(parts[2],kwargs['line']))
    # convert immediate string to integer
    parts[2] = int(parts[2])
    return True

def check_jump_instr(parts,**kwargs):
    # <IMMED>
    # the immediate may already be converted
    if len(parts) != 1:
        return False
    # if we cannot convert the literal, then assume we have a
    # non-resolved label
    if not isinstance(parts[0],(int,long)) \
       and not REGEX_IMMED.match(parts[0]):
        runtime_error("line {1}: cannot resolve label '{0}'".format(parts[0],kwargs['line']))
    # convert immediate string to integer
    parts[0] = int(parts[0])
    return True

def check_jumpreg_instr(parts):
    # <REG>
    return not (len(parts) != 1 or not parts[0] in MIPS_REGISTERS)

REGEX_INDIR = re.compile('(-?[0-9]+)?\((.+)\)')
def check_indirect_instr(parts):
    # check indirect addressing instruction format
    # <REG> <[offset](REG)>
    if not isinstance(parts[1],str):
        return False
    if len(parts) != 2 or not parts[0] in MIPS_REGISTERS:
        return False
    m = REGEX_INDIR.match(parts[1])
    if not m or not m.group(2) in MIPS_REGISTERS:
        return False
    # convert last part to offset; add new part for source register
    parts[1] = 0 if m.group(1) is None else int(m.group(1))
    parts.append(m.group(2))
    return True

def instr_add(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr(parts)
    t = sim.read_register(parts[1])
    u = sim.read_register(parts[2])
    sim.write_register(parts[0],ctypes.c_int32(t+u).value)

def instr_addu(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr(parts)
    t = sim.read_register(parts[1])
    u = sim.read_register(parts[2])
    sim.write_register(parts[0],ctypes.c_uint32(t+u).value)

def instr_addi(sim,parts,**kwargs):
    if sim is None:
        return check_immed_instr(parts)
    t = sim.read_register(parts[1])
    sim.write_register(parts[0],ctypes.c_int32(t+parts[2]).value)

def instr_addiu(sim,parts,**kwargs):
    if sim is None:
        return check_immed_instr(parts)
    t = sim.read_register(parts[1])
    sim.write_register(parts[0],ctypes.c_uint32(t + parts[2]).value)

def instr_and(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr(parts)
    t = sim.read_register(parts[1])
    u = sim.read_register(parts[2])
    sim.write_register(parts[0],t & u)

def instr_andi(sim,parts,**kwargs):
    if sim is None:
        return check_immed_instr(parts)
    t = sim.read_register(parts[1])
    sim.write_register(parts[0],ctypes.c_uint32(t & parts[2]).value)

def instr_div(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr2(parts)
    t = sim.read_register(parts[0])
    u = sim.read_register(parts[1])
    sim.write_register('HI',ctypes.c_int32(t % u).value)
    sim.write_register('LO',ctypes.c_int32(t // u).value)

def instr_divu(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr2(parts)
    t = sim.read_register(parts[0])
    u = sim.read_register(parts[1])
    sim.write_register('HI',ctypes.c_uint32(t % u).value)
    sim.write_register('LO',ctypes.c_uint32(t // u).value)

def instr_mul(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr(parts)
    t = sim.read_register(parts[1])
    u = sim.read_register(parts[2])
    sim.write_register(parts[0],ctypes.c_int32(t * u).value)

def instr_mulu(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr(parts)
    t = sim.read_register(parts[1])
    u = sim.read_register(parts[2])
    sim.write_register(parts[0],ctypes.c_uint32(t * u).value)

def instr_mult(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr2(parts)
    t = sim.read_register(parts[0]) * sim.read_register(parts[1])
    sim.write_register('HI',ctypes.c_int32(t >> 32).value)
    sim.write_register('LO',ctypes.c_int32(t).value)

def instr_multu(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr2(parts)
    t = sim.read_register(parts[0]) * sim.read_register(parts[1])
    sim.write_register('HI',ctypes.c_uint32(t >> 32).value)
    sim.write_register('LO',ctypes.c_uint32(t).value)

def instr_nor(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr(parts)
    t = sim.read_register(parts[1])
    u = sim.read_register(parts[2])
    sim.write_register(parts[0],ctypes.c_uint32(~(t | u)).value)

def instr_or(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr(parts)
    t = sim.read_register(parts[1])
    u = sim.read_register(parts[2])
    sim.write_register(parts[0],ctypes.c_uint32(t | u).value)

def instr_ori(sim,parts,**kwargs):
    if sim is None:
        return check_immed_instr(parts)
    t = sim.read_register(parts[1])
    sim.write_register(parts[0],ctypes.c_uint32(t | parts[2]).value)

def instr_rem(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr(parts) or check_immed_instr(parts)
    # Read operands: the right operand may be a register or an immediate.
    t = sim.read_register(parts[1])
    u = sim.read_register(parts[2]) if parts[2] in MIPS_REGISTERS else parts[2]
    sim.write_register(parts[0],ctypes.c_uint32(t % u).value)

def instr_sll(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr(parts) or check_immed_instr(parts)
    # the second argument is a source register and the second could be
    # either a register or an immediate (I handle both just to make
    # sure)
    t = sim.read_register(parts[1])
    u = sim.read_register(parts[2]) if parts[2] in MIPS_REGISTERS else parts[2]
    sim.write_register(parts[0],ctypes.c_uint32(t << u).value)

def instr_sllv(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr(parts)
    t = sim.read_register(parts[1])
    u = sim.read_register(parts[2])
    sim.write_register(parts[0],ctypes.c_uint32(t << u).value)

def instr_sra(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr(parts) or check_immed_instr(parts)
    # the second argument is a source register and the second could be
    # either a register or an immediate (I handle both just to make
    # sure)
    t = sim.read_register(parts[1])
    u = sim.read_register(parts[2]) if parts[2] in MIPS_REGISTERS else parts[2]
    # this is an arithmetic shift; this means we must preserve the
    # sign bit; we do this by bit-and'ing the complement of either all
    # ones or all zeros having been shifted by the same amount
    b = -1 if t & 0x80000000 else 0
    sim.write_register(parts[0],ctypes.c_uint32((t >> u) & ~(b >> u)).value)

def instr_srav(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr(parts)
    t = sim.read_register(parts[1])
    u = sim.read_register(parts[2])
    b = -1 if t & 0x80000000 else 0
    sim.write_register(parts[0],ctypes.c_uint32((t >> u) & ~(b >> u)).value)

def instr_srl(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr(parts) or check_immed_instr(parts)
    # the second argument is a source register and the second could be
    # either a register or an immediate (I handle both just to make
    # sure)
    t = sim.read_register(parts[1])
    u = sim.read_register(parts[2]) if parts[2] in MIPS_REGISTERS else parts[2]
    sim.write_register(parts[0],ctypes.c_uint32(t >> u).value)

def instr_srlv(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr(parts)
    t = sim.read_register(parts[1])
    u = sim.read_register(parts[2])
    sim.write_register(parts[0],ctypes.c_uint32(t >> u).value)

def instr_sub(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr(parts)
    t = sim.read_register(parts[1])
    u = sim.read_register(parts[2])
    sim.write_register(parts[0],ctypes.c_int32(t - u).value)

def instr_subu(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr(parts)
    t = sim.read_register(parts[1])
    u = sim.read_register(parts[2])
    sim.write_register(parts[0],ctypes.c_uint32(t - u).value)

def instr_xor(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr(parts)
    t = sim.read_register(parts[1])
    u = sim.read_register(parts[2])
    sim.write_register(parts[0],ctypes.c_uint32(t ^ u).value)

def instr_xori(sim,parts,**kwargs):
    if sim is None:
        return check_immed_instr(parts)
    t = sim.read_register(parts[1])
    u = ctypes.c_uint32(parts[2]).value
    sim.write_register(parts[0],ctypes.c_uint32(t ^ u).value)

def instr_slt(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr(parts)
    t = ctypes.c_int32(sim.read_register(parts[1])).value
    u = ctypes.c_int32(sim.read_register(parts[2])).value
    sim.write_register(parts[0],int(t < u))

def instr_sltu(sim,parts,**kwargs):
    if sim is None:
        return check_register_instr(parts)
    t = ctypes.c_uint32(sim.read_register(parts[1])).value
    u = ctypes.c_uint32(sim.read_register(parts[2])).value
    sim.write_register(parts[0],int(t < u))

def instr_slti(sim,parts,**kwargs):
    if sim is None:
        return check_immed_instr(parts)
    t = ctypes.c_int32(sim.read_register(parts[1])).value
    u = ctypes.c_int32(parts[2]).value
    sim.write_register(parts[0],int(t < u))

def instr_sltiu(sim,parts,**kwargs):
    if sim is None:
        return check_immed_instr(parts)
    t = ctypes.c_uint32(sim.read_register(parts[1])).value
    u = ctypes.c_uint32(parts[2]).value
    sim.write_register(parts[0],int(t < u))

def instr_beq(sim,parts,**kwargs):
    if sim is None:
        return check_direct_instr2(parts,**kwargs)
    t = ctypes.c_int32(sim.read_register(parts[0])).value
    u = ctypes.c_int32(sim.read_register(parts[1])).value
    if t == u:
        sim.progCounter = parts[2]

def instr_bgez(sim,parts,**kwargs):
    if sim is None:
        return check_direct_instr(parts,**kwargs)
    t = ctypes.c_int32(sim.read_register(parts[0])).value
    if t >= 0:
        sim.progCounter = parts[1]

def instr_bgtz(sim,parts,**kwargs):
    if sim is None:
        return check_direct_instr(parts,**kwargs)
    t = ctypes.c_int32(sim.read_register(parts[0])).value
    if t > 0:
        sim.progCounter = parts[1]

def instr_blez(sim,parts,**kwargs):
    if sim is None:
        return check_direct_instr(parts,**kwargs)
    t = ctypes.c_int32(sim.read_register(parts[0])).value
    if t <= 0:
        sim.progCounter = parts[1]

def instr_bne(sim,parts,**kwargs):
    if sim is None:
        return check_direct_instr2(parts,**kwargs)
    t = ctypes.c_int32(sim.read_register(parts[0])).value
    u = ctypes.c_int32(sim.read_register(parts[1])).value
    if t != u:
        sim.progCounter = parts[2]

def instr_blt(sim,parts,**kwargs):
    if sim is None:
        return check_direct_instr2(parts,**kwargs)
    t = ctypes.c_int32(sim.read_register(parts[0])).value
    u = ctypes.c_int32(sim.read_register(parts[1])).value
    if t < u:
        sim.progCounter = parts[2]

def instr_bgt(sim,parts,**kwargs):
    if sim is None:
        return check_direct_instr2(parts,**kwargs)
    t = ctypes.c_int32(sim.read_register(parts[0])).value
    u = ctypes.c_int32(sim.read_register(parts[1])).value
    if t > u:
        sim.progCounter = parts[2]

def instr_j(sim,parts,**kwargs):
    if sim is None:
        return check_jump_instr(parts,**kwargs)
    sim.progCounter = parts[0]

def instr_jal(sim,parts,**kwargs):
    if sim is None:
        return check_jump_instr(parts,**kwargs)
    sim.write_register('$ra',sim.progCounter) # link
    sim.progCounter = parts[0]

def instr_jalr(sim,parts,**kwargs):
    if sim is None:
        return check_jumpreg_instr(parts)
    sim.write_register('$ra',sim.progCounter) # link
    sim.progCounter = sim.read_register(parts[0])

def instr_jr(sim,parts,**kwargs):
    if sim is None:
        return check_jumpreg_instr(parts)
    sim.progCounter = sim.read_register(parts[0])

def instr_la(sim,parts,**kwargs):
    if sim is None:
        return check_direct_instr(parts,**kwargs) or check_indirect_instr(parts)
    if len(parts) == 2:
        addr = parts[1]
    else:
        addr = parts[1] + sim.read_register(parts[2])
    sim.write_register(parts[0],addr)

def instr_lhi(sim,parts,**kwargs):
    if sim is None:
        return check_direct_instr(parts,**kwargs)
    # grab current register value and place in upper word
    t = (sim.read_register(parts[0]) & 0xffff) | (parts[1] << 16)
    sim.write_register(parts[0],t)

def instr_li(sim,parts,**kwargs):
    return instr_la(sim,parts)

def instr_llo(sim,parts,**kwargs):
    if sim is None:
        return check_direct_instr(parts,**kwargs)
    # grab current register value and place in upper word
    t = (sim.read_register(parts[0]) & 0xffff0000) | (parts[1] << 16)
    sim.write_register(parts[0],t)

def instr_lb(sim,parts,**kwargs):
    if sim is None:
        return check_indirect_instr(parts) or check_direct_instr(parts,**kwargs)
    if len(parts) == 2:
        # direct
        addr = parts[1]
    else:
        # indirect (i.e. from register)
        addr = parts[1] + sim.read_register(parts[2])
    sim.write_register(parts[0],sim.read_byte(addr))

def instr_lbu(sim,parts,**kwargs):
    if sim is None:
        return check_indirect_instr(parts) or check_direct_instr(parts,**kwargs)
    if len(parts) == 2:
        # direct
        addr = parts[1]
    else:
        # indirect (i.e. from register)
        addr = parts[1] + sim.read_register(parts[2])
    sim.write_register(parts[0],ctypes.c_uint32(sim.read_byte(addr)).value)

def instr_lh(sim,parts,**kwargs):
    if sim is None:
        return check_indirect_instr(parts) or check_direct_instr(parts,**kwargs)
    if len(parts) == 2:
        # direct
        addr = parts[1]
    else:
        # indirect (i.e. from register)
        addr = parts[1] + sim.read_register(parts[2])
    sim.write_register(parts[0],sim.read_halfword(addr))

def instr_lhu(sim,parts,**kwargs):
    if sim is None:
        return check_indirect_instr(parts) or check_direct_instr(parts,**kwargs)
    if len(parts) == 2:
        # direct
        addr = parts[1]
    else:
        # indirect (i.e. from register)
        addr = parts[1] + sim.read_register(parts[2])
    sim.write_register(parts[0],ctypes.c_uint32(sim.read_halfword(addr)).value)

def instr_lw(sim,parts,**kwargs):
    if sim is None:
        return check_indirect_instr(parts) or check_direct_instr(parts,**kwargs)
    if len(parts) == 2:
        # direct
        addr = parts[1]
    else:
        # indirect (i.e. from register)
        addr = parts[1] + sim.read_register(parts[2])
    sim.write_register(parts[0],sim.read_word(addr))

def instr_mfhi(sim,parts,**kwargs):
    if sim is None:
        return check_jumpreg_instr(parts)
    t = sim.read_register('HI')
    sim.write_register(parts[0],t)

def instr_mflo(sim,parts,**kwargs):
    if sim is None:
        return check_jumpreg_instr(parts)
    t = sim.read_register('LO')
    sim.write_register(parts[0],t)

def instr_move(sim,parts,**kwargs):
    if sim is None:
        return len(parts) == 2 and parts[0] in MIPS_REGISTERS \
            and parts[1] in MIPS_REGISTERS
    t = sim.read_register(parts[1])
    sim.write_register(parts[0],t)

def instr_mthi(sim,parts,**kwargs):
    if sim is None:
        return check_jumpreg_instr(parts)
    t = sim.read_register(parts[0])
    sim.write_register('HI',t)

def instr_mtlo(sim,parts,**kwargs):
    if sim is None:
        return check_jumpreg_instr(parts)
    t = sim.read_register(parts[0])
    sim.write_register('LO',t)

def instr_sb(sim,parts,**kwargs):
    if sim is None:
        return check_indirect_instr(parts) or check_direct_instr(parts,**kwargs)
    if len(parts) == 2:
        # direct
        addr = parts[1]
    else:
        # indirect (i.e. from register)
        addr = parts[1] + sim.read_register(parts[2])
    sim.write_byte(addr,sim.read_register(parts[0]))

def instr_sh(sim,parts,**kwargs):
    if sim is None:
        return check_indirect_instr(parts) or check_direct_instr(parts,**kwargs)
    if len(parts) == 2:
        # direct
        addr = parts[1]
    else:
        # indirect (i.e. from register)
        addr = parts[1] + sim.read_register(parts[2])
    sim.write_halfword(addr,sim.read_register(parts[0]))

def instr_sw(sim,parts,**kwargs):
    if sim is None:
        return check_indirect_instr(parts) or check_direct_instr(parts,**kwargs)
    if len(parts) == 2:
        # direct
        addr = parts[1]
    else:
        # indirect (i.e. from register)
        addr = parts[1] + sim.read_register(parts[2])
    sim.write_word(addr,sim.read_register(parts[0]))

def instr_syscall(sim,parts,**kwargs):
    if sim is None:
        return len(parts) == 0
    # simulate the SPIM system calls
    v = sim.read_register('$v0')
    if v == 1:
        # print_int ($a0 = word to print)

        system.print_int(sim.read_register('$a0'))
    elif v == 4:
        # print_string ($a0 = pointer to null-terminated buffer)

        system.print_string(sim.read_string(sim.read_register('$a0')))
    elif v == 5:
        # read_int

        i = system.read_int()
        sim.write_register('$v0',i)
    elif v == 8:
        # read_string ($a0 = pointer to buffer, $a1 = amount); returns
        # number of bytes read

        n = system.read_string(sim,sim.read_register('$a0'),sim.read_register('$a1'))
        sim.write_register('$v0',n)
    elif v == 10:
        # exit ($a0 = process return code)

        system.exit(sim.read_register('$a0'))
    elif v == 11:
        # print_character ($a0 = char)

        system.print_character(sim.read_register('$a0'))
    elif v == 12:
        # read_character

        sim.write_register('$v0',system.read_character())
    else:
        runtime_error("could not execute system call {0}: no such service".format(v))

# define useful constant information for the program
STACK_SPACE = 1048576
MIPS_INSTRUCTIONS = {'add':instr_add,'addu':instr_addu,'addi':instr_addi,'addiu':instr_addiu,
                     'and':instr_and,'andi':instr_andi,'div':instr_div,'divu':instr_divu,
                     'mul':instr_mul,'mulu':instr_mulu,'mult':instr_mult,'multu':instr_multu,
                     'nor':instr_nor,'or':instr_or,'ori':instr_ori,'sll':instr_sll,'sllv':instr_sllv,
                     'sra':instr_sra,'srav':instr_srav,'srl':instr_srl,'srlv':instr_srlv,'sub':instr_sub,
                     'subu':instr_subu,'xor':instr_xor,'xori':instr_xori,'slt':instr_slt,
                     'sltu':instr_sltu,'slti':instr_slti,'sltiu':instr_sltiu,'beq':instr_beq,'bgez':instr_bgez,
                     'bgtz':instr_bgtz,'blez':instr_blez,'bne':instr_bne,'blt':instr_blt,'bgt':instr_bgt,
                     'j':instr_j,'jal':instr_jal,'jalr':instr_jalr,'jr':instr_jr,'la':instr_la,'lhi':instr_lhi,
                     'li':instr_li,'llo':instr_llo,'lb':instr_lb,'lbu':instr_lbu,'lh':instr_lh,'lhu':instr_lhu,
                     'lw':instr_lw,'mfhi':instr_mfhi,'mflo':instr_mflo,'move':instr_move,'mthi':instr_mthi,
                     'mtlo':instr_mtlo,'sb':instr_sb,'sh':instr_sh,'sw':instr_sw,'syscall':instr_syscall,
                     'rem':instr_rem,'nop':lambda _,__,**___: True}
MIPS_REGISTERS = {'$0' : 0, '$zero' : 0, '$r0' : 0,
                  '$1' : 4,'$at' : 4, '$2' : 8, '$v0' : 8,
                  '$3' : 12,'$v1' : 12, '$4' : 16, '$a0' : 16,
                  '$5' : 20,'$a1' : 20, '$6' : 24, '$a2' : 24,
                  '$7' : 28,'$a3' : 28, '$8' : 32, '$t0' : 32,
                  '$9' : 36,'$t1' : 36, '$10' : 40, '$t2' : 40,
                  '$11' : 44,'$t3' : 44, '$12' : 48, '$t4' : 48,
                  '$13' : 52,'$t5' : 52, '$14' : 56, '$t6' : 56,
                  '$15' : 60,'$t7' : 60, '$16' : 64, '$s0' : 64,
                  '$17' : 68, '$s1' : 68, '$18' : 72, '$s2' : 72,
                  '$19' : 76, '$s3' : 76, '$20' : 80, '$s4' : 80,
                  '$21' : 84, '$s5' : 84, '$22' : 88, '$s6' : 88,
                  '$23' : 92, '$s7' : 92, '$24' : 96, '$t8' : 96,
                  '$25' : 100, '$t9' : 100, '$26' : 104, '$k0' : 104,
                  '$27' : 108, '$k1' : 108, '$28' : 112, '$gp' : 112,
                  '$29' : 116, '$sp' : 116, '$30' : 120, '$fp' : 120, '$s8' : 120,
                  '$31' : 124, '$ra' : 124, 'HI' : 128, 'LO' : 132}
STRING_ESCAPES = ((r'\\a','\x07'),(r'\\b','\x08'),(r'\\f','\x0c'),(r'\\n','\x0a'),
                  (r'\\r','\x0d'),(r'\\t','\x09'),(r'\\v','\x0b'),(r'\\\\',r'\x5c'),
                  (r'\\\'','\x27'),(r'\\"','\x22'),(r'\\([0-7]{3})',lambda x:chr(int(x.group(1),8))),
                  (r'\\([0-9a-f]{2})',lambda x:chr(int(x.group(1),16))))
LABEL_INSTRS = ['beq','bgez','bgtz','blez','bne','blt','bgt','j','jal','jalr','jr','la','lb','lbu','lh','lhu',
                'lw','sw','sh','sw'] # only these instructions can resolve labels
SHEBANG = "#!/usr/bin/env pymips\n"

class MIPSSystem:
    REGEX_TOKEN = re.compile('\s*([^\s]+)')
    def __init__(self):
        self.buf = ""
        self.fdtable = {}

    def exit(self,v):
        exit(v)
    def print_int(self,i):
        stdout.write("{0}".format(i))
    def print_string(self,s):
        stdout.write(s)
    def print_character(self,v):
        stdout.write(chr(v))

    def read_int(self):
        tok = self.read_token()
        return int(tok)
    def read_character(self):
        # return the character as an integer (its ordinal value)
        c = self.buf[:1]
        if len(c) == 0:
            self.buf = stdin.readline()
            if len(self.buf) == 0:
                runtime_error("unexpected EOF on read operation")
            c = self.buf[:1]
            self.buf = self.buf[1:]
        return ord(c)
    def read_string(self,sim,addr,amount):
        # this works similarly to 'fgets'
        s = ""

        # pop off anything from the buffer within the amount of bytes
        # requested or until a newline has been read; if the buffer
        # becomes empty before we have read the requisite number of
        # bytes, read another line into the buffer
        while amount > 0:
            # check for newlines in the input stream
            p = self.buf.find("\n")
            if p != -1:
                p += 1 # include newline in buffer (potentially)
                if p > amount:
                    p = amount
                s += self.buf[:p]
                self.buf = self.buf[p:]
                break
            amount -= len(self.buf)
            s += self.buf[:amount]
            self.buf = self.buf[amount:]
            if len(self.buf) == 0:
                self.buf = stdin.readline()
                if len(self.buf) == 0:
                    break

        # write the string into simulator's memory at the specified
        # address and return the number of bytes written
        sim.write_memory(addr,s)
        return len(s)

    def read_token(self):
        # if we cannot read a token from the buffer, then the buffer
        # needs to be updated
        while True:
            m = MIPSSystem.REGEX_TOKEN.match(self.buf)
            if m:
                break
            # if we didn't match then only whitespaces were in the
            # buffer; so replace the buffer with a new line
            self.buf = stdin.readline()
            if len(self.buf) == 0:
                runtime_error("unexpected EOF on read operation")
        tok = m.group(1)
        self.buf = self.buf[m.end(1):]
        return tok

class MIPSSimulator:
    def __init__(self,f):
        # load information from pickle file; this consists of the
        # program's text instructions and its data segment memory; we
        # first must read off the shebang that lets the file be
        # executable; then the file stream is ready to be unpickled
        f.read(len(SHEBANG))
        t = pickle.load(f)
        self.instr = t[0]
        self.memory = io.BytesIO(t[1]) # main memory
        datalen = self.memory.seek(0,2) # calculate number of bytes in data segment
        self.memory.seek(0)

        # allocate registers as a memory stream; each register has a
        # constant offset into this memory
        self.regmem = io.BytesIO()
        self.regmem.seek(200)
        self.regmem.write("\x00")
        self.regmem.seek(0)

        # position the stack pointer register at the top of the main
        # memory stream
        self.maxaddr = STACK_SPACE + datalen
        self.write_register('$sp',self.maxaddr)

        # create the program counter (this is the offset within the
        # list of instructions of the next instruction to execute)
        self.progCounter = 0

    def write_register(self,reg,value):
        # each register is a 4-byte word; value should be a Python
        # 'long/int' that we wrap into a word and write to the memory
        # stream
        self.regmem.seek(MIPS_REGISTERS[reg])
        self.regmem.write(struct.pack('<i',ctypes.c_int32(value).value))

    def read_register(self,reg):
        # read a 4-byte value from the register memory stream; the
        # result should be a Python 'long/int'
        self.regmem.seek(MIPS_REGISTERS[reg])
        mem = self.regmem.read(4)
        return struct.unpack('<i',mem)[0]

    def write_memory(self,addr,data):
        # write some data to the main memory stream
        if addr+len(data) > self.maxaddr or addr < 0:
            raise Exception('segmentation fault: attempted to write outside of allocated memory segment')
        self.memory.seek(addr)
        return self.memory.write(data)

    def read_memory(self,addr,length):
        # read some data from main memory
        if addr+length > self.maxaddr or addr < 0:
            raise Exception('segmentation fault: attempted to read outside of allocated memory segment')
        self.memory.seek(addr)
        return self.memory.read(length)

    def write_word(self,addr,value):
        # write a word to main memory
        self.write_memory(addr,struct.pack('<i',ctypes.c_int32(value).value))

    def read_word(self,addr):
        # read a word from main memory
        mem = self.read_memory(addr,4)
        return struct.unpack('<i',mem)[0]

    def write_halfword(self,addr,value):
        self.write_memory(addr,struct.pack('<h',ctypes.c_int16(value).value))

    def read_halfword(self,addr):
        mem = self.read_memory(addr,2)
        return struct.unpack('<h',mem)[0]

    def write_byte(self,addr,value):
        self.write_memory(addr,struct.pack('<b',ctypes.c_int8(value).value))

    def read_byte(self,addr):
        mem = self.read_memory(addr,1)
        return struct.unpack('<b',mem)[0]

    def read_string(self,addr):
        s = ""
        while True:
            bu = self.read_byte(addr)
            if bu == 0:
                break
            s += chr(bu)
            addr += 1
        return s

    def simulation(self):
        # run the simulation
        while True:
            if self.progCounter >= len(self.instr):
                runtime_error("attempted to execute non-instruction: bad offset in program")

            # fetch current instruction; update program counter next
            # in case a jump happens during execution of the
            # instruction
            i = self.instr[self.progCounter]
            self.progCounter += 1
            try:
                MIPS_INSTRUCTIONS[i[0]](self,i[1:])
            except Exception as e:
                runtime_error(str(e))

class MIPSParser:
    REGEX_DIRECTIVE = re.compile('(?:\s*#.*\n)*\s*\.([a-z]+)')
    REGEX_LABEL = re.compile('(?:\s*#.*\n)*\s*([a-zA-Z0-9_$]+):')
    REGEX_ANY = re.compile('(?:\s*#.*\n)*\s*([^#\n]*[^#\s])?\s*')
    REGEXES = [(REGEX_DIRECTIVE,'directive'),(REGEX_LABEL,'label'),(REGEX_ANY,'any')]

    def __init__(self,f):
        self.content = f.read().replace("\r","")
        self.globl = []   # store global symbol details
        self.data = []    # store data segment details
        self.instr = []   # store instruction details

        # try to split the assembly code into directives, labels and
        # everything else
        pos = 0
        line = 1
        things = []
        while pos < len(self.content):
            for regex, kind in MIPSParser.REGEXES:
                m = regex.match(self.content,pos)
                if m:
                    break
            if m is None:
                error_on_line("bad input: '{0}'".format(self.content[pos:]),
                              line)
            lno = -1
            while pos < m.end(0):
                if self.content[pos] == "\n":
                    line += 1
                if pos == m.start(1):
                    lno = line
                pos += 1
            if m.group(1) is not None:
                things.append((m.group(1),kind,lno))
        self.preprocess(things)

    def preprocess(self,things):
        # go through the things we just parsed; assign them meaning
        # within the context of the program; labels are resolved to
        # addresses at a later stage
        mode = state = label = ''
        for content, kind, line in things:
            if kind == 'directive':
                if content == 'text':
                    mode = 'text'
                elif content == 'data':
                    mode = 'data'
                    state = ''
                elif content == 'globl':
                    state = 'globl'
                elif content in ['byte','half','word','ascii','asciiz','space']:
                    state = content
                else:
                    error_on_line("directive '{0}' is not recognized".format(content),line)
            elif kind == 'label':
                label = content
            elif kind == 'any':
                if mode == 'data':
                    if state in ['byte','half','word']:
                        # parse a list of comma separated integers and
                        # assign a data entry
                        try:
                            self.data.append((state,map(int,re.split('[,\s]+',content)),label,line))
                        except ValueError:
                            error_on_line("'{0}' directive requires integer argument".format(state),line)
                    elif state in ['ascii','asciiz']:
                        # this data directive only allows a single entry
                        # to be specified (unlike byte and word); we do
                        # have to unpack the double-quoted string
                        if len(content) < 2 or content[0] != '"' or content[len(content)-1] != '"':
                            error_on_line("'{0}' directive requires character string argument".format(state),line)
                        self.data.append((state,(content[1:len(content)-1],),label,line))
                    elif state == 'space':
                        try:
                            self.data.append((state,(int(content),),label,line))
                        except ValueError:
                            error_on_line("'space' directive requires integer allocation amount argument",line)
                    else:
                        if state == 'globl':
                            error_on_line("globl symbol '{0}' must be in text segment".format(content),line)
                        error_on_line("cannot understand '{0}'".format(content),line)
                elif mode == 'text':
                    if state != '':
                        if state == 'globl':
                            # add the content entry to the list of global
                            # symbols to mark a label as global
                            self.globl.append((content,line))
                        else:
                            error_on_line("directive '{0}' must be found in data segment".format(state),line)
                    else:
                        # then 'content' is an instruction; instructions
                        # are split by whitespace and commas
                        self.instr.append((re.split('[,\s]+',content),label,line))
                else:
                    error_on_line("cannot understand '{0}'".format(content),line)

                # reset label and state
                label = state = ''

    def __repr__(self):
        return "{0}\n{1}\n{2}\n".format(str(self.globl),
                                        str(self.data),
                                        str(self.instr))

    def build_program(self,outfile):
        # build the program based on the information the parser has
        # gathered; we pretty much leave instructions as they are
        # (performing no processing on them); we do however resolve
        # symbol labels into addresses (i.e. offsets) within the
        # different data sections

        # define a table of symbols that maps to their final address
        # within the program
        labels = {}

        # represent the memory segments of the program (data and
        # stack) using a binary stream; we don't use an actual text
        # segment since we emulate the machine at a very high level
        memory = io.BytesIO()

        # create list of tuples of instructions
        instructions = []

        # write all data entries to the memorystream; add labels to
        # the 'labels' table; the stack will be allocated at runtime
        # after the data segment
        addr = 0
        for kind, things, label, line in self.data:
            if label != '':
                if label in labels:
                    error_on_line("label '{0}' is already in use".format(label),line)
                labels[label] = addr

            for thing in things:
                if kind == 'byte':
                    bs = struct.pack("<b",thing)
                elif kind == 'half':
                    bs = struct.pack("<h",thing)
                elif kind == 'word':
                    bs = struct.pack("<i",thing)
                elif kind == 'ascii':
                    # this kind has no zero byte terminator
                    s = MIPSParser.eval_string_literal(thing)
                    bs = struct.pack("{0}s".format(len(s)),s)
                elif kind == 'asciiz':
                    # 'struct.pack' will pad a zero when size exceeds
                    # length of string
                    s = MIPSParser.eval_string_literal(thing)
                    bs = struct.pack("{0}s".format(len(s)+1),s)
                elif kind == 'space':
                    # fill in space with zero bytes
                    bs = struct.pack("{0}b".format(thing),*([0]*thing))
                addr += memory.write(bs)

        # make sure the data segment size is some multiple of eight
        memory.write('\x00'*(8 - addr%8))
        memory.seek(0)

        # go through all instructions and add the appropriate label to
        # the 'labels' table which should map to the index of the
        # instruction; if the label already exists then fail
        offset = 0
        for _, label, line in self.instr:
            if label != '':
                if label in labels:
                    error_on_line("label '{0}' is already in use".format(label),line)
                labels[label] = offset
            offset += 1

        # for each instruction, convert to a tuple and resolve any
        # labels to a numeric address value; also check to make sure
        # the instruction is real and having the correct number and
        # type of arguments; check_instr will perform any other
        # instruction-specific processing
        for instrs, _, line in self.instr:
            # a label can only be used by a select few instructions;
            # it only appears as the last argument also
            if instrs[0] in LABEL_INSTRS:
                if instrs[-1] in labels:
                    instrs[-1] = labels[instrs[-1]]
            instructions.append(MIPSParser.check_instr(instrs,line))
        instructions = tuple(instructions)

        # save tuple of the program information to a pickle file;
        # place a shebang in the pickle file so we can execute the
        # program file using the simulator; also mark the file as
        # executable (this will have no effect on some platforms)
        if isinstance(outfile,str):
            outfile = open(outfile,'wb')
        if isinstance(outfile,file):
            mode = os.stat(outfile.name).st_mode
            os.chmod(outfile.name,mode | 0111)
        outfile.write(SHEBANG)
        pickle.dump((instructions,memory.read()),outfile,pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def check_instr(parts,line):
        # check that the instruction exists and is well-formed; we
        # will return a new list containing any conversions/additions
        # that are needed for processing the instruction
        if not parts[0] in MIPS_INSTRUCTIONS:
            error_on_line("'{0}' is not a valid instruction".format(parts[0]),line)
        t = parts[1:]
        iname = parts[0]
        if not MIPS_INSTRUCTIONS[iname](None,t,line=line):
            error_on_line("'{0}' instruction is not formatted correctly".format(parts[0]),line)
        t.insert(0,iname)
        return t

    @staticmethod
    def eval_string_literal(literal):
        # replace string literals with their escape sequences
        # evaluated; we use C-style escape sequences
        for pat, rep in STRING_ESCAPES:
            literal = re.sub(pat,rep,literal)
        return literal

def execmips(exefile):
    # load the program from the specified 'executable' file and run
    # the simulation
    sim = MIPSSimulator(exefile)
    sim.simulation()

def assemblemips(asmfile):
    # assemble the mips instructions from the specified file stream
    # and write them to the specified output file
    global args
    parser = MIPSParser(asmfile)
    parser.build_program(args.outputFile)

def onestep(asmfile):
    # assemble the mips instructions from the specified file stream
    # and immediately execute the result
    parser = MIPSParser(asmfile)
    with io.BytesIO() as exefile: # write program to in-memory file
        parser.build_program(exefile)
        exefile.seek(0)
        execmips(exefile)

# create a MIPSSystem object to handle system interactions
system = MIPSSystem()

# create argument parser for simulator and parse command-line
# arguments
argp = argparse.ArgumentParser(description="A simple MIPS simulator")
argp.add_argument('filename',default=None,nargs='?',metavar='file',
                  help="input file for process (defaults to stdin if omitted)")
argp.add_argument('-a','--assemble',dest='action',action="store_const",default=execmips,
                  const=assemblemips,help="assemble the specified assembly code")
argp.add_argument('--one-step',dest='action',action='store_const',const=onestep,
                  help="assemble and execute in one step")
argp.add_argument('-o','--output-file',dest='outputFile',default='a.mips',nargs='?',
                  help="output file to write assembled program")
args = argp.parse_args()

if args.filename is None and args.action == execmips:
    runtime_error("no input program file")

with stdin if args.filename is None else open(args.filename,'rb') as f:
    args.action(f)
