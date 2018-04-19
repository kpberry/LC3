.orig x20
.fill __GETC__
.fill __OUT__
.fill __PUTS__
.fill __IN__
.fill __PUTSP__
.fill __HALT__
.end

.orig x200
__GETC__
LDI R0, __KBSR__
BRzp __GETC__
LDI R0, __KBDR__
RET
__KBSR__ .fill xFE00
__KBDR__ .fill xFE02
.end

.orig x210
__OUT__
ST R1, __OUT_TEMP__
__OUT_LOOP__
LDI R1, __DSR__
BRzp __OUT_LOOP__
STI R0, __DDR__
LD R1, __OUT_TEMP__
RET
__DSR__ .fill xFE04
__DDR__ .fill xFE06
__OUT_TEMP__ .fill 0
.end

.orig x220
__PUTS__
ST R0, __PUTS_TEMP_0__
ST R1, __PUTS_TEMP_1__
ST R2, __PUTS_TEMP_2__
__PUTS_LOOP__
LDR R2, R0, 0
BRz __PUTS_END__

__PUTS_OUT_LOOP__
LDI R1, __DSR__
BRzp __PUTS_OUT_LOOP__
STI R2, __DDR__

ADD R0, R0, 1
BR __PUTS_LOOP__
__PUTS_END__
LD R0, __PUTS_TEMP_0__
LD R1, __PUTS_TEMP_1__
LD R2, __PUTS_TEMP_2__
RET
__PUTS_TEMP_0__ .fill 0
__PUTS_TEMP_1__ .fill 0
__PUTS_TEMP_2__ .fill 0
.end

.orig x240
__IN__
.end

.orig x230
__PUTSP__
.end

.orig x250
__HALT__
    LD R0, __MCR__
    AND R1, R1, 0
    STR R1, R0, 0
__MCR__ .fill xFFFE
.end

.orig x3000
LD R0, X
LD R2, Y
AND R1, R1, 0
LOOP
ADD R1, R1, R2
ADD R0, R0, -1
BRp LOOP
LEA R0, S
PUTS

GETC
OUT
GETC
OUT
GETC
OUT
GETC
OUT
GETC
OUT

BRp NOT_END
END
    HALT
NOT_END
    AND R2, R2, 0
HALT

ANS
    .fill 0
X
    .fill x3
Y
    .fill 60
S
    .stringz "Done."

.end