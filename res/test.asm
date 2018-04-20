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
ST R7, __IN__TEMP
LEA R0, __IN__PROMPT
PUTS
GETC
LD R7, __IN__TEMP
RET
__IN__TEMP .fill 0
__IN__PROMPT .stringz "Enter a single character: "
.end

.orig x270
__PUTSP__ 
ST R0, __PUTSP_TEMP_0__
ST R1, __PUTSP_TEMP_1__
ST R2, __PUTSP_TEMP_2__
__PUTSP_LOOP__
LDR R2, R0, 0
BRz __PUTSP_END__

__PUTSP_OUT_LOOP__
LDI R1, __DSR__
BRzp __PUTSP_OUT_LOOP__
LD R1, __PUTSP_MASK__
AND R1, R1, R2
STI R1, __DDR__
AND R1, R1, 0
; TODO add loop to get higher order bits

ADD R0, R0, 1
BR __PUTSP_LOOP__
__PUTSP_END__
LD R0, __PUTSP_TEMP_0__
LD R1, __PUTSP_TEMP_1__
LD R2, __PUTSP_TEMP_2__
RET
__PUTSP_TEMP_0__ .fill 0
__PUTSP_TEMP_1__ .fill 0
__PUTSP_TEMP_2__ .fill 0
__PUTSP_MASK__   .fill x00FF
.end

.orig x300
__HALT__
    LD R0, __MCR__
    AND R1, R1, 0
    STR R1, R0, 0
__MCR__ .fill xFFFE
.end

.orig x3000

IN
ADD R1, R0, 0
LEA R0, CONFIRM
PUTS
ADD R0, R1, 0
OUT
LD R0, NEWLINE
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
CONFIRM
    .stringz "You entered: "
NEWLINE
    .stringz "\n"

.end