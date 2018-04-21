class Assembler:
    def __init__(self):
        self.orig = None

        self.instrs = {
            'add': self.assemble_add,
            'and': self.assemble_and,
            'br': self.assemble_br,
            'brn': self.assemble_br,
            'brz': self.assemble_br,
            'brp': self.assemble_br,
            'brnz': self.assemble_br,
            'brzp': self.assemble_br,
            'brnp': self.assemble_br,
            'brnzp': self.assemble_br,
            'jmp': self.assemble_jmp,
            'jsr': self.assemble_jsr,
            'jsrr': self.assemble_jsrr,
            'ld': self.assemble_ld,
            'ldi': self.assemble_ldi,
            'ldr': self.assemble_ldr,
            'lea': self.assemble_lea,
            'not': self.assemble_not,
            'ret': self.assemble_jmp,
            'rti': self.assemble_rti,
            'st': self.assemble_st,
            'sti': self.assemble_sti,
            'str': self.assemble_str,
            'trap': self.assemble_trap
        }

        self.ops = {
            '.orig': self.process_orig,
            '.end': self.process_end,
            '.fill': self.process_fill,
            '.blkw': self.process_blkw,
            '.stringz': self.process_stringz
        }

        self.traps = {
            'getc': 'trap x20',
            'out': 'trap x21',
            'puts': 'trap x22',
            'in': 'trap x23',
            'putsp': 'trap x24',
            'halt': 'trap x25'
        }

        self.labels = {}

    def assemble_file(self, filename):
        with open(filename, 'r') as f:
            return self.assemble([line for line in f])

    def assemble(self, lines):
        memory = [0] * (1 << 16)
        i = 0
        to_be_assembled = []
        self.orig = 0

        for i, line in enumerate(lines):
            line = line.split(';')[0].split()
            for j, tok in enumerate(line):
                ltok = tok.lower()
                if ltok in self.instrs or ltok in self.traps or ltok == '.fill':
                    to_be_assembled.append(' '.join(line[j:]))
                    self.orig += 1
                    break
                elif ltok in self.ops:
                    to_be_assembled.append(' '.join(line[j:]))
                    self.ops[ltok](' '.join(line[j:]), memory)
                    break
                else:
                    if tok in self.labels:
                        message = 'Duplicate Symbol Found on line ' + str(i) + \
                                  ': ' + tok + ' already defined'
                        raise Exception(message)
                    self.labels[tok] = self.orig

        self.orig = 0
        for i, line in enumerate(to_be_assembled):
            line = line.split(';')[0].split()
            for j, tok in enumerate(line):
                ltok = tok.lower()
                if ltok in self.instrs:
                    memory[self.orig] = self.instrs[ltok](' '.join(line[j:]))
                    self.orig += 1
                    break
                elif ltok in self.ops:
                    self.ops[ltok](' '.join(line[j:]), memory)
                    break
                elif ltok in self.traps:
                    memory[self.orig] = self.instrs['trap'](self.traps[ltok])
                    self.orig += 1
                    break
                else:
                    assert tok in self.labels
        
        return memory

    def process_orig(self, line, memory):
        digits = self.get_digits(line, '.orig NUM')
        self.orig = digits[0]

    def process_blkw(self, line, memory):
        digits = self.get_digits(line, '.blkw NUM')
        self.orig += digits[0]

    def process_end(self, line, memory):
        self.orig = None

    def process_stringz(self, line, memory):
        text = line.split('.stringz')[1].strip()
        text = bytes(text, 'utf-8').decode('unicode_escape')
        assert (text[0] == '"' and text[-1] == '"')
        text = text[1:-1]
        for char in text:
            memory[self.orig] = ord(char)
            self.orig += 1
        memory[self.orig] = 0
        self.orig += 1

    def process_fill(self, line, memory):
        try:
            digits = self.get_digits(line, '.fill NUM')
            memory[self.orig] = digits[0]
        except Exception:
            digits = self.get_digits(line, '.fill ID')
            memory[self.orig] = self.labels[digits[0]]
        self.orig += 1

    @staticmethod
    def assert_max_digit_lengths(digits, lengths):
        for i, cur in enumerate(digits):
            if cur < 0:
                cur = -cur
            if ~(~0x0 << lengths[i]) & cur != cur:
                raise Exception('FuckedUpDigitLengthException')

    def assemble_add(self, line):
        try:
            digits = self.get_digits(line, 'add REG, REG, REG')
            self.assert_max_digit_lengths(digits, [3, 3, 3])
            result = 0x1000 | digits[0] << 9 | digits[1] << 6 | digits[2]
        except Exception:
            digits = self.get_digits(line, 'add REG, REG, NUM')
            self.assert_max_digit_lengths(digits, [3, 3, 5])
            result = 0x1000 | digits[0] << 9 | digits[1] << 6 | 1 << 5 | digits[2] & 0x1F
        return result

    def assemble_and(self, line):
        try:
            digits = self.get_digits(line, 'and REG, REG, REG')
            self.assert_max_digit_lengths(digits, [3, 3, 3])
            result = 0x5000 | digits[0] << 9 | digits[1] << 6 | digits[2]
        except Exception:
            digits = self.get_digits(line, 'and REG, REG, NUM')
            self.assert_max_digit_lengths(digits, [3, 3, 5])
            result = 0x5000 | digits[0] << 9 | digits[1] << 6 | 1 << 5 | digits[2] & 0x1F
        return result

    def assemble_br(self, line):
        br, label = line.strip().split(' ')
        extensions = {'': 0b111, 'n': 0b100, 'z': 0b010, 'p': 0b001,
                      'nz': 0b110, 'np': 0b101, 'zp': 0b011, 'nzp': 0b111}
        offset = self.labels[label] - (self.orig + 1)
        self.assert_max_digit_lengths([offset], [9])
        return 0x0000 | extensions[br[2:]] << 9 | offset & 0x1FF

    def assemble_jmp(self, line):
        if line.lower() == 'ret':
            return 0xC000 | 0b111 << 6
        digits = self.get_digits(line, 'jmp REG')
        self.assert_max_digit_lengths(digits, [3])
        return 0xC000 | digits[0] << 6

    def assemble_jsr(self, line):
        digits = self.get_digits(line, 'jsr ID')
        digits[0] = (self.labels[digits[0]] - (self.orig + 1))
        self.assert_max_digit_lengths(digits, [11])
        return 0x4000 | 0x1 << 11 | digits[0]

    def assemble_jsrr(self, line):
        digits = self.get_digits(line, 'jsrr REG')
        self.assert_max_digit_lengths(digits, [3])
        return 0x4000 | digits[0] << 6

    def assemble_ld(self, line):
        digits = self.get_digits(line, 'ld REG, ID')
        digits[1] = (self.labels[digits[1]] - (self.orig + 1))
        self.assert_max_digit_lengths(digits, [3, 9])
        return 0x2000 | digits[0] << 9 | digits[1] & 0x1FF

    def assemble_ldi(self, line):
        digits = self.get_digits(line, 'ldi REG, ID')
        digits[1] = (self.labels[digits[1]] - (self.orig + 1))
        self.assert_max_digit_lengths(digits, [3, 9])
        return 0xA000 | digits[0] << 9 | digits[1] & 0x1FF

    def assemble_ldr(self, line):
        digits = self.get_digits(line, 'ldr REG, REG, NUM')
        self.assert_max_digit_lengths(digits, [3, 3, 6])
        return 0x6000 | digits[0] << 9 | digits[1] << 6 | digits[2]

    def assemble_lea(self, line):
        digits = self.get_digits(line, 'lea REG, ID')
        digits[1] = (self.labels[digits[1]] - (self.orig + 1))
        self.assert_max_digit_lengths(digits, [3, 9])
        return 0xE000 | digits[0] << 9 | digits[1] & 0x1FF

    def assemble_not(self, line):
        digits = self.get_digits(line, 'not REG, REG')
        self.assert_max_digit_lengths(digits, [3, 3])
        return 0x9000 | digits[0] << 9 | digits[1] << 6 | 0x003F

    def assemble_rti(self, line):
        return 0x8000

    def assemble_st(self, line):
        digits = self.get_digits(line, 'st REG, ID')
        digits[1] = (self.labels[digits[1]] - (self.orig + 1))
        self.assert_max_digit_lengths(digits, [3, 9])
        return 0x3000 | digits[0] << 9 | digits[1] & 0x1FF

    def assemble_sti(self, line):
        digits = self.get_digits(line, 'sti REG, ID')
        digits[1] = (self.labels[digits[1]] - (self.orig + 1))
        self.assert_max_digit_lengths(digits, [3, 9])
        return 0xB000 | digits[0] << 9 | digits[1] & 0x1FF

    def assemble_str(self, line):
        digits = self.get_digits(line, 'str REG, REG, NUM')
        self.assert_max_digit_lengths(digits, [3, 3, 6])
        return 0x7000 | digits[0] << 9 | digits[1] << 6 | digits[2]

    def assemble_trap(self, line):
        digits = self.get_digits(line, 'trap NUM')
        self.assert_max_digit_lengths(digits, [8])
        return 0xF000 | digits[0]

    def get_digits(self, raw_line, raw_pattern):
        line = ' , '.join(raw_line.split(',')).split()
        pattern = ' , '.join(raw_pattern.split(',')).split()
        assert len(line) == len(pattern)
        result = []
        for tok, lexeme in list(zip(line, pattern)):
            if lexeme == 'NUM':
                if tok[0] == 'x':
                    result.append(int(tok[1:], 16))
                else:
                    result.append(int(tok))
            elif lexeme == 'REG':
                assert tok[0].lower() == 'r'
                result.append(int(tok[1:]))
            elif lexeme == 'ID':
                result.append(tok)
            else:
                assert(tok.lower() == lexeme.lower())
        return result

if __name__ == '__main__':
    try:
        Assembler().assemble_file('../res/test.asm')
    except:
        Assembler().assemble_file('res/test.asm')