def sext(value, digits):
    if value & (0x1 << (digits - 1)) == 0:
        return value & ~(~0 << (digits - 1))
    else:
        return -(-value & ~(~0 << (digits - 1)))


class Disassembler:
    def __init__(self):
        self.instrs = {
            0: Disassembler.disassemble_br,
            1: Disassembler.disassemble_add,
            2: Disassembler.disassemble_ld,
            3: Disassembler.disassemble_st,
            4: Disassembler.disassemble_jsr,
            5: Disassembler.disassemble_and,
            6: Disassembler.disassemble_ldr,
            7: Disassembler.disassemble_str,
            8: Disassembler.disassemble_rti,
            9: Disassembler.disassemble_not,
            10: Disassembler.disassemble_ldi,
            11: Disassembler.disassemble_sti,
            12: Disassembler.disassemble_jmp,
            13: lambda _: 'Reserved',
            14: Disassembler.disassemble_lea,
            15: Disassembler.disassemble_trap
        }

    def disassemble(self, lines):
        return [self.disassemble_line(line) for line in lines if line != 0]

    def disassemble_line(self, line):
        return self.instrs[(line >> 12) & 0xF](line)

    @staticmethod
    def disassemble_add(line):
        if (line >> 5) & 0x1 == 0:
            return 'ADD R{}, R{}, R{}' \
                .format((line >> 9) & 0x7, (line >> 6) & 0x7, line & 0x7)
        else:
            return 'ADD R{}, R{}, #{}' \
                .format((line >> 9) & 0x7, (line >> 6) & 0x7, sext(line, 5))

    @staticmethod
    def disassemble_and(line):
        if (line >> 5) & 0x1 == 0:
            return 'AND R{}, R{}, R{}' \
                .format((line >> 9) & 0x7, (line >> 6) & 0x7, line & 0x7)
        else:
            return 'AND R{}, R{}, #{}' \
                .format((line >> 9) & 0x7, (line >> 6) & 0x7, sext(line, 5))

    @staticmethod
    def disassemble_br(line):
        return 'BR{}{}{} #{}'.format(
            'n' if line & 0x0800 != 0 else '',
            'z' if line & 0x0400 != 0 else '',
            'p' if line & 0x0200 != 0 else '',
            sext(line, 9)
        )

    @staticmethod
    def disassemble_jmp(line):
        return 'JMP R{}'.format((line >> 6) & 0x7) if (line >> 6) & 0x7 != 0x7 else 'RET'

    @staticmethod
    def disassemble_jsr(line):
        if line >> 11 & 0x1 == 0:
            return 'JSRR R{}'.format((line >> 6) & 0x7)
        else:
            return 'JSR #{}'.format(sext(line, 11))

    @staticmethod
    def disassemble_ld(line):
        return 'LD R{}, #{}'.format((line >> 9) & 0x7, sext(line, 9))

    @staticmethod
    def disassemble_ldi(line):
        return 'LDI R{}, #{}'.format((line >> 9) & 0x7, sext(line, 9))

    @staticmethod
    def disassemble_ldr(line):
        return 'LDR R{}, R{}, #{}'.format(
            (line >> 9) & 0x7, (line >> 6) & 0x7, sext(line, 6)
        )

    @staticmethod
    def disassemble_lea(line):
        return 'LEA R{}, #{}'.format((line >> 9) & 0x7, sext(line, 9))

    @staticmethod
    def disassemble_not(line):
        return 'NOT R{}, R{}'.format((line >> 9) & 0x7, (line >> 6) & 0x7)

    @staticmethod
    def disassemble_rti(line):
        return 'RTI'

    @staticmethod
    def disassemble_st(line):
        return 'ST R{}, #{}'.format((line >> 9) & 0x7, sext(line, 9))

    @staticmethod
    def disassemble_sti(line):
        return 'STI R{}, #{}'.format((line >> 9) & 0x7, sext(line, 9))

    @staticmethod
    def disassemble_str(line):
        return 'STR R{}, R{}, #{}'.format(
            (line >> 9) & 0x7, (line >> 6) & 0x7, sext(line, 6)
        )

    @staticmethod
    def disassemble_trap(line):
        traps = {0x20: 'GETC', 0x21: 'OUT', 0x22: 'PUTS',
                 0x23: 'IN', 0x24: 'PUTSP', 0x25: 'HALT'}
        index = line & 0xFF
        if index in traps.keys():
            return traps[index]
        else:
            return 'TRAP {}'.format(index)

print('imported')