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
            '.fill': None,
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

    def assemble_file(self, file):
        with open(file, 'r') as f:
            return self.assemble([line for line in f])

    def assemble(self, lines):
        result = [0] * (1 << 16)
        i = 0
        j = 0
        to_be_assembled = []
        while i < len(lines):
            line = lines[i][j:].lower().strip()
            if len(line) == 0:
                i += 1
                j = 0
                continue
            first = line.split()[0]
            same_line = False
            if first in self.instrs.keys() or first == '.fill':
                to_be_assembled.append((self.orig, first, line))
                self.orig += 1
            elif first in self.ops.keys():
                self.ops[first](line, lines, result, i)
            elif first in self.traps.keys():
                line = self.traps[first] + ' ' + line[len(first):]
                result[self.orig] = self.instrs['trap'](line)
                self.orig += 1
            elif first in self.labels.keys():
                raise Exception('Duplicate Symbol Found')
            else:
                self.labels[first] = self.orig
                j += len(first) + 1
                same_line = True

            if not same_line:
                i += 1
                j = 0
        for line_data in to_be_assembled:
            self.orig = line_data[0]
            first = line_data[1]
            if first == '.fill':
                self.process_fill(line_data[2], lines, result, line_data[0])
            else:
                result[self.orig] = self.instrs[line_data[1]](line_data[2])
        return result

    def process_orig(self, line, lines, result, i):
        digits = self.get_digits(line, '.orig ##')
        self.orig = digits[0]

    def process_blkw(self, line, lines, result, i):
        digits = self.get_digits(line, '.blkw ##')
        self.orig += digits[0]

    def process_end(self, line, lines, result, i):
        self.orig = None

    def process_stringz(self, line, lines, result, i):
        text = lines[i].strip()[len('.stringz'):].strip()
        assert (text[0] == '"' and text[-1] == '"')
        text = text[1:-1]
        for char in text:
            result[self.orig] = ord(char)
            self.orig += 1
        result[self.orig] = 0
        self.orig += 1

    def process_fill(self, line, lines, result, i):
        try:
            digits = self.get_digits(line, '.fill ##')
            result[i] = digits[0]
        except Exception:
            digits = self.get_digits(line, '.fill &')
            result[i] = self.labels[digits[0]]

    @staticmethod
    def assert_max_digit_lengths(digits, lengths):
        for i in range(len(digits)):
            cur = digits[i]
            if cur < 0:
                cur = -cur
            if ~(~0x0 << lengths[i]) & cur != cur:
                raise Exception('FuckedUpDigitLengthException')

    def assemble_add(self, line):
        try:
            digits = self.get_digits(line, 'add r#, r#, r#')
            self.assert_max_digit_lengths(digits, [3, 3, 3])
            result = 0x1000 | digits[0] << 9 | digits[1] << 6 | digits[2]
        except Exception:
            digits = self.get_digits(line, 'add r#, r#, ##')
            self.assert_max_digit_lengths(digits, [3, 3, 5])
            result = 0x1000 | digits[0] << 9 | digits[1] << 6 | 1 << 5 | digits[2] & 0x1F
        return result

    def assemble_and(self, line):
        try:
            digits = self.get_digits(line, 'and r#, r#, r#')
            self.assert_max_digit_lengths(digits, [3, 3, 3])
            result = 0x5000 | digits[0] << 9 | digits[1] << 6 | digits[2]
        except Exception:
            digits = self.get_digits(line, 'and r#, r#, ##')
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
        if line == 'ret':
            return 0xC000 | 0b111 << 6
        digits = self.get_digits(line, 'jmp r#')
        self.assert_max_digit_lengths(digits, [3])
        return 0xC000 | digits[0] << 6

    def assemble_jsr(self, line):
        digits = self.get_digits(line, 'jsr &')
        digits[0] = (self.labels[digits[0]] - (self.orig + 1))
        self.assert_max_digit_lengths(digits, [11])
        return 0x4000 | 0x1 << 11 | digits[0]

    def assemble_jsrr(self, line):
        digits = self.get_digits(line, 'jsrr r#')
        self.assert_max_digit_lengths(digits, [3])
        return 0x4000 | digits[0] << 6

    def assemble_ld(self, line):
        digits = self.get_digits(line, 'ld r#, &')
        digits[1] = (self.labels[digits[1]] - (self.orig + 1))
        self.assert_max_digit_lengths(digits, [3, 9])
        return 0x2000 | digits[0] << 9 | digits[1] & 0x1FF

    def assemble_ldi(self, line):
        digits = self.get_digits(line, 'ldi r#, &')
        digits[1] = (self.labels[digits[1]] - (self.orig + 1))
        self.assert_max_digit_lengths(digits, [3, 9])
        return 0xA000 | digits[0] << 9 | digits[1] & 0x1FF

    def assemble_ldr(self, line):
        digits = self.get_digits(line, 'ldr r#, r#, ##')
        self.assert_max_digit_lengths(digits, [3, 3, 6])
        return 0x6000 | digits[0] << 9 | digits[1] << 6 | digits[2]

    def assemble_lea(self, line):
        digits = self.get_digits(line, 'lea r#, &')
        digits[1] = (self.labels[digits[1]] - (self.orig + 1))
        self.assert_max_digit_lengths(digits, [3, 9])
        return 0xE000 | digits[0] << 9 | digits[1] & 0x1FF

    def assemble_not(self, line):
        digits = self.get_digits(line, 'not r#, r#')
        self.assert_max_digit_lengths(digits, [3, 3])
        return 0x9000 | digits[0] << 9 | digits[1] << 6 | 0x003F

    def assemble_rti(self, line):
        return 0x8000

    def assemble_st(self, line):
        digits = self.get_digits(line, 'st r#, &')
        digits[1] = (self.labels[digits[1]] - (self.orig + 1))
        self.assert_max_digit_lengths(digits, [3, 9])
        return 0x3000 | digits[0] << 9 | digits[1] & 0x1FF

    def assemble_sti(self, line):
        digits = self.get_digits(line, 'sti r#, &')
        digits[1] = (self.labels[digits[1]] - (self.orig + 1))
        self.assert_max_digit_lengths(digits, [3, 9])
        return 0xB000 | digits[0] << 9 | digits[1] & 0x1FF

    def assemble_str(self, line):
        digits = self.get_digits(line, 'str r#, r#, ##')
        self.assert_max_digit_lengths(digits, [3, 3, 6])
        return 0x7000 | digits[0] << 9 | digits[1] << 6 | digits[2]

    def assemble_trap(self, line):
        digits = self.get_digits(line, 'trap ##')
        self.assert_max_digit_lengths(digits, [8])
        return 0xF000 | digits[0]

    def get_digits(self, line, digit_pattern):
        line = ' '.join(line.split()).lower()
        digit_pattern = ' '.join(digit_pattern.split()).lower()
        digits = []
        i = 0
        j = 0
        while i < len(digit_pattern):
            if j > len(line):
                raise Exception('YouFuckedUpException')
            if digit_pattern[i] == '&':
                cur = ''
                while j < len(line) and not line[j] in [' ', '\n', '\r', '\t']:
                    cur += line[j]
                    j += 1
                i += 1
                digits.append(cur)
            elif digit_pattern[i] == '#':
                if i < len(digit_pattern) - 1 and digit_pattern[i + 1] == '#':
                    cur = ''
                    digit_is_hex = False
                    if line[j] == '-':
                        cur += '-'
                        j += 1
                    if line[j] == 'x':
                        digit_is_hex = True
                        j += 1
                    if line[j] == '#':
                        if digit_is_hex:
                            raise Exception('YouFuckedUpTheNumberFormatException')
                        j += 1
                    if line[j] == '-':
                        if cur[0] == '-':
                            cur = ''
                        else:
                            cur += '-'
                        j += 1
                    if line[j].isdigit() or line[j] in ['a', 'b', 'c', 'd', 'e', 'f']:
                        cur += line[j]
                        j += 1
                    else:
                        raise Exception('YouFuckedUpWithTheStartException')

                    while j < len(line) \
                            and (line[j].isdigit() or line[j] in ['a', 'b', 'c', 'd', 'e', 'f']):
                        cur += line[j]
                        j += 1
                    if digit_is_hex:
                        digits.append(int(cur, 16))
                    else:
                        digits.append(int(cur))
                    i += 1
                else:
                    digits.append(int(line[j]))
                    j += 1
            elif digit_pattern[j] != line[i]:
                raise Exception('YouFuckedUpException')
            else:
                j += 1
            i += 1
        if j != len(line):
            raise Exception('You\'veGotExtraShitException')
        return digits