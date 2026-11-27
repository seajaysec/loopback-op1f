.macro os_skip
    R0.H = 0x11a0
    R0.L = 0x5a3a
.endm
.macro os_usb_mode
    P1.H = 0x848c
    P1.L = 0xe514
.endm
.macro os_usb_send
    P1.H = 0x8d4e
    P1.L = 0x75c4
.endm
.macro os_speaker reg=P0
    \reg\().H = 0x8400
    \reg\().L = 0xdec9
.endm
