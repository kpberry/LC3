.orig x25
.fill __HALT__
.end

.orig x200
__HALT__
    LD R0, __MCR__
    AND R1, R1, 0
    STR R1, R0, 0
__MCR__ .fill xFFFE
.end

.orig x3000
AND R0, R0, 0
AND R2, R2, 0
ADD R2, R0, 12
AND R3, R3, 0
LOOP ADD R3, R2, R3
ADD R2, R2, -1
BRp LOOP
HALT
.end