import sys
import threading
from random import randint

from assembler import Assembler


class LC3:
    mem_size = 0xFFFF
    word_size = 16
    num_registers = 8
    kbsr = 0xFE00
    kbdr = 0xFE02
    dsr = 0xFE04
    ddr = 0xFE06
    mcr = 0xFFFE

    def __init__(self):
        self.memory = []
        self.registers = []
        self.pc = 0
        self.psr = 0
        self.instr = None
        self.inputs = ''
        self.ssp = 0x3000
        self.zero_registers()
        self.isr_registers = []
        self.assembler = Assembler()
        self.instrs = [
            self.BR, self.ADD, self.LD, self.ST, self.JSR, self.AND,
            self.LDR, self.STR, self.RTI, self.NOT, self.LDI,
            self.STI, self.JMP, None, self.LEA, self.TRAP
        ]

    def reset_device_registers(self):
        self.memory[LC3.kbsr] = 0
        self.memory[LC3.dsr] = -1
        self.memory[LC3.kbdr] = 0
        self.memory[LC3.ddr] = 0
        self.memory[LC3.mcr] = 1

    def zero_memory(self):
        self.memory = [0] * LC3.mem_size

    def randomize_memory(self):
        self.memory = [randint(0, 1 << LC3.word_size)
                       for _ in range(LC3.mem_size)]

    def zero_registers(self):
        self.registers = [0] * LC3.num_registers

    def randomize_registers(self):
        self.registers = [
            randint(0, 1 << LC3.word_size) for _ in range(LC3.num_registers)
        ]

    def listen_for_input(self):
        def read_input():
            self.inputs += input()
            self.listen_for_input()
        t = threading.Thread(target=read_input)
        t.daemon = True
        t.start()

    def exec_file(self, filename):
        self.exec_memory(self.assembler.assemble_file(filename))

    def exec_lines(self, lines):
        self.exec_memory(self.assembler.assemble(lines))

    def exec_memory(self, memory, origin=0x3000):
        self.memory = memory
        self.reset_device_registers()
        self.pc = origin

        self.listen_for_input()

        key_delay = 0
        while self.memory[LC3.mcr] != 0:
            key_delay += 1
            if self.memory[LC3.dsr] < 0 and self.memory[LC3.ddr] != 0:
                sys.stdout.write(chr(self.memory[LC3.ddr]))
                sys.stdout.flush()
                self.memory[LC3.dsr] = 1
                self.memory[LC3.ddr] = 0
            else:
                self.memory[LC3.dsr] = -1

            self.instr = self.memory[self.pc]
            self.pc += 1

            opcode = (self.instr >> 12) & 0xF

            if self.instrs[opcode] is None:
                raise Exception('IllegalOpcodeException')
            else:
                self.instrs[opcode]()  # execute the current instruction

            if self.inputs:
                cur_input = ord(self.inputs[0])
                self.inputs = self.inputs[1:]
                self.memory[LC3.kbsr] |= 0x8000
                self.memory[LC3.kbdr] = cur_input
                key_delay = 0
            elif key_delay > 2:
                self.memory[LC3.kbsr] &= 0x7FFF

    def set_cc(self, v):
        self.psr &= 0xFFF8
        if v == 0:
            self.psr |= 0b010
        elif v & 0x8000 == 0:
            self.psr |= 0b001
        else:
            self.psr |= 0b100

    def ADD(self):
        mode = bit_range(self.instr, 5, 1)
        sr1 = bit_range(self.instr, 6, 3)
        dr = bit_range(self.instr, 9, 3)
        if not mode:
            sr2 = bit_range(self.instr, 0, 3)
            dr_val = self.registers[sr1] + self.registers[sr2]
        else:
            imm = sext_bit_range(self.instr, 0, 5)
            dr_val = self.registers[sr1] + imm
        self.registers[dr] = dr_val
        self.set_cc(dr_val)

    def AND(self):
        mode = bit_range(self.instr, 5, 1)
        sr1 = bit_range(self.instr, 6, 3)
        dr = bit_range(self.instr, 9, 3)
        if not mode:
            sr2 = bit_range(self.instr, 0, 3)
            dr_val = self.registers[sr1] & self.registers[sr2]
        else:
            imm = sext_bit_range(self.instr, 0, 5)
            dr_val = self.registers[sr1] & imm
        self.registers[dr] = dr_val
        self.set_cc(dr_val)

    def BR(self):
        if bit_range(self.instr, 9, 3) & self.psr != 0:
            pc_offset_9 = sext_bit_range(self.instr, 0, 9)
            self.pc += pc_offset_9

    def JMP(self):
        base_r = bit_range(self.instr, 6, 3)
        self.pc = self.registers[base_r]

    def JSR(self):
        self.registers[7] = self.pc
        mode = bit_range(self.instr, 11, 1)
        if not mode:
            base_r = bit_range(self.instr, 6, 3)
            self.pc = self.registers[base_r]
        else:
            pc_offset_11 = sext_bit_range(self.instr, 0, 11)
            self.pc += pc_offset_11

    def LD(self):
        dr = bit_range(self.instr, 9, 3)
        pc_offset_9 = sext_bit_range(self.instr, 0, 9)
        self.registers[dr] = self.memory[self.pc + pc_offset_9]
        self.set_cc(self.registers[dr])

    def LDI(self):
        dr = bit_range(self.instr, 9, 3)
        pc_offset_9 = sext_bit_range(self.instr, 0, 9)
        self.registers[dr] = self.memory[self.memory[self.pc + pc_offset_9]]
        self.set_cc(self.registers[dr])

    def LDR(self):
        dr = bit_range(self.instr, 9, 3)
        base_r = bit_range(self.instr, 6, 3)
        pc_offset_6 = sext_bit_range(self.instr, 0, 6)
        self.registers[dr] = self.memory[self.registers[base_r] + pc_offset_6]
        self.set_cc(self.registers[dr])

    def LEA(self):
        dr = bit_range(self.instr, 9, 3)
        pc_offset_9 = sext_bit_range(self.instr, 0, 9)
        self.registers[dr] = self.pc + pc_offset_9
        self.set_cc(self.registers[dr])

    def NOT(self):
        dr = bit_range(self.instr, 9, 3)
        sr = bit_range(self.instr, 6, 3)
        self.registers[dr] = ~self.registers[sr]
        self.set_cc(self.registers[dr])

    def RTI(self):
        if bit_range(self.psr, 15, 1) == 0:
            self.pc = self.memory[self.registers[6]]
            self.registers[6] += 1
            temp = self.memory[self.registers[6]]
            self.registers[6] += 1
            self.psr = temp
        else:
            raise Exception('Privilege Mode Exception')

    def ST(self):
        sr = bit_range(self.instr, 9, 3)
        pc_offset_9 = sext_bit_range(self.instr, 0, 9)
        self.memory[self.pc + pc_offset_9] = self.registers[sr]

    def STI(self):
        sr = bit_range(self.instr, 9, 3)
        pc_offset_9 = sext_bit_range(self.instr, 0, 9)
        self.memory[self.memory[self.pc + pc_offset_9]] = self.registers[sr]

    def STR(self):
        sr = bit_range(self.instr, 9, 3)
        base_r = bit_range(self.instr, 6, 3)
        pc_offset_6 = sext_bit_range(self.instr, 0, 6)
        self.memory[self.registers[base_r] + pc_offset_6] = self.registers[sr]

    def TRAP(self):
        self.registers[7] = self.pc
        trap_vect_8 = bit_range(self.instr, 0, 8)
        self.pc = self.memory[trap_vect_8]


def bit_range(num, start, bits):
    return (num >> start) & ~(~0 << bits)


def sext_bit_range(num, start, bits):
    if (num >> start) & 0x1 << (bits - 1) == 0:
        return (num >> start) & ~(~0 << (bits - 1))
    else:
        return -(-(num >> start) & ~(~0 << (bits - 1)))


if __name__ == '__main__':
    LC3().exec_file('../res/test.asm')
