.text
.align 2
.include "loopback_os.inc"
.global op1f_loopback_in
.type op1f_loopback_in, STT_FUNC
op1f_loopback_in:
    [--SP] = ASTAT;
    [--SP] = R0;
    [--SP] = R1;
    [--SP] = R2;
    [--SP] = P0;
    [--SP] = P2;
    P1.H = 0x1190;
    P1.L = 0x2dfc;
    R2 = 0;
    R0 = [P1 + 0x48];
    R1 = 2;
    CC = R0 == R1;
    IF !CC JUMP .Lin_amp;
    P0.H = 0x1190;
    P0.L = 0x2da4;
    R0 = [P0];
    CC = R0 == 0;
    IF !CC JUMP .Lin_amp;
    P0.H = 0x84a0;
    P0.L = 0x1524;
    R0 = [P0];
    R1 = 8;
    CC = R0 < R1 (IU);
    IF !CC JUMP .Lin_amp;
    P2 = R0;
    P0.H = 0x1190;
    P0.L = 0x4714;
    P0 = P0 + (P2 << 2);
    R0 = [P0];
    R1 = 14;
    CC = R0 == R1;
    IF !CC JUMP .Lin_amp;
    R2 = 1;
.Lin_amp:
    P0.H = op1f_loopback_amp;
    P0.L = op1f_loopback_amp;
    [P0] = R2;
    R0 = [P1 + 0x48];
    CC = R0 == 0;
    IF CC JUMP .Lin_open;
    CC = R2 == 0;
    IF CC JUMP .Lin_shut;
.Lin_open:
    P0.H = 0x1190;
    P0.L = 0x25a0;
    R1 = 16;
    R2 = 0;
.Lin_pk:
    R0 = [P0++];
    CC = R0 < 0;
    IF !CC JUMP .Lin_abs;
    R0 = -R0;
.Lin_abs:
    CC = R2 < R0;
    IF !CC JUMP .Lin_max;
    R2 = R0;
.Lin_max:
    R1 += -1;
    CC = R1 == 0;
    IF !CC JUMP .Lin_pk;
    P0.H = op1f_loopback_inpeak;
    P0.L = op1f_loopback_inpeak;
    [P0] = R2;
    JUMP .Lin_mode;
.Lin_shut:
    P0.H = op1f_loopback_inpeak;
    P0.L = op1f_loopback_inpeak;
    R0 = 0;
    [P0] = R0;
.Lin_mode:
    P0.H = op1f_loopback_mode;
    P0.L = op1f_loopback_mode;
    R2 = [P0];
    R0 = [P1 + 0x4c];
    R1 = 3;
    CC = R0 == R1;
    IF CC JUMP .Lin_source;
    R1 = 1;
    CC = R0 == R1;
    IF !CC JUMP .Lin_done;
.Lin_source:
    R0 = [P1 + 0x48];
    CC = R0 == 0;
    IF CC JUMP .Lin_route0;
    P0.H = op1f_loopback_amp;
    P0.L = op1f_loopback_amp;
    R0 = [P0];
    CC = R0 == 0;
    IF CC JUMP .Lin_done;
    CC = R2 == 0;
    IF CC JUMP .Lin_done;
    P0.H = 0x1190;
    P0.L = 0x2ba0;
    P2.H = op1f_loopback_return;
    P2.L = op1f_loopback_return;
    R1 = 64;
.Lin_amp_keep:
    R0 = [P0];
    [P2++] = R0;
    R0 = [P0 + 0x100];
    [P2++] = R0;
    R0 = 0;
    [P0] = R0;
    [P0 + 0x100] = R0;
    P0 += 4;
    R1 += -1;
    CC = R1 == 0;
    IF !CC JUMP .Lin_amp_keep;
    P0.H = op1f_loopback_fresh;
    P0.L = op1f_loopback_fresh;
    R1 = 1;
    [P0] = R1;
    R1 = 2;
    CC = R2 == R1;
    IF !CC JUMP .Lin_mark;
    P0.H = op1f_loopback_return;
    P0.L = op1f_loopback_return;
    P2.H = op1f_loopback_dry;
    P2.L = op1f_loopback_dry;
    R1 = 64;
.Lin_amp_dry:
    R0 = [P0++];
    [P2] = R0;
    R0 = [P0++];
    [P2 + 0x100] = R0;
    P2 += 4;
    R1 += -1;
    CC = R1 == 0;
    IF !CC JUMP .Lin_amp_dry;
    JUMP .Lin_mark;
.Lin_route0:
    P0.H = 0x1190;
    P0.L = 0x25a0;
    P2.H = op1f_loopback_return;
    P2.L = op1f_loopback_return;
    R0 = 128;
.Lin_keep:
    R1 = [P0++];
    [P2++] = R1;
    R0 += -1;
    CC = R0 == 0;
    IF !CC JUMP .Lin_keep;
    P0.H = op1f_loopback_fresh;
    P0.L = op1f_loopback_fresh;
    R1 = 1;
    [P0] = R1;
    CC = R2 == 0;
    IF CC JUMP .Lin_done;
    R1 = 2;
    CC = R2 == R1;
    IF !CC JUMP .Lin_mark;
    P0.H = 0x1190;
    P0.L = 0x2ba0;
    P2.H = op1f_loopback_dry;
    P2.L = op1f_loopback_dry;
    R1 = 0;
    R0 = 128;
.Lin_take:
    R2 = [P0];
    [P0++] = R1;
    [P2++] = R2;
    R0 += -1;
    CC = R0 == 0;
    IF !CC JUMP .Lin_take;
    R2 = 2;
.Lin_mark:
    P0.H = op1f_loopback_held;
    P0.L = op1f_loopback_held;
    [P0] = R2;
    P1.H = op1f_loopback_shut;
    P1.L = op1f_loopback_shut;
.Lin_done:
    P2 = [SP++];
    P0 = [SP++];
    R2 = [SP++];
    R1 = [SP++];
    R0 = [SP++];
    ASTAT = [SP++];
    RTS;
.size op1f_loopback_in, .-op1f_loopback_in
.global op1f_loopback_mix
.type op1f_loopback_mix, STT_FUNC
op1f_loopback_mix:
    [--SP] = ASTAT;
    [--SP] = R0;
    [--SP] = R1;
    [--SP] = R2;
    [--SP] = P0;
    [--SP] = P2;
    P0.H = op1f_loopback_held;
    P0.L = op1f_loopback_held;
    R1 = [P0];
    R0 = 0;
    [P0] = R0;
    P0.H = op1f_loopback_due;
    P0.L = op1f_loopback_due;
    [P0] = R1;
    CC = R1 == 0;
    IF CC JUMP .Lmix_plain;
    P0.H = 0x1190;
    P0.L = 0x2ba0;
    P2.H = op1f_loopback_return;
    P2.L = op1f_loopback_return;
    R2 = 64;
.Lmix_add:
    R0 = [P0];
    R1 = [P2++];
    R0 = R0 + R1 (S);
    [P0] = R0;
    R0 = [P0 + 0x100];
    R1 = [P2++];
    R0 = R0 + R1 (S);
    [P0 + 0x100] = R0;
    P0 += 4;
    R2 += -1;
    CC = R2 == 0;
    IF !CC JUMP .Lmix_add;
    JUMP .Lmix_skip;
.Lmix_plain:
    CC = R7 == 0;
    IF CC JUMP .Lmix_skip;
    CC = R5 == 0;
    IF CC JUMP .Lmix_skip;
.Lmix_on:
    P2 = [SP++];
    P0 = [SP++];
    R2 = [SP++];
    R1 = [SP++];
    R0 = [SP++];
    ASTAT = [SP++];
    RTS;
.Lmix_skip:
    os_skip
    RETS = R0;
    P2 = [SP++];
    P0 = [SP++];
    R2 = [SP++];
    R1 = [SP++];
    R0 = [SP++];
    ASTAT = [SP++];
    RTS;
.size op1f_loopback_mix, .-op1f_loopback_mix
.global op1f_loopback_usb
.type op1f_loopback_usb, STT_FUNC
op1f_loopback_usb:
    [--SP] = RETS;
    [--SP] = R4;
    [--SP] = R2;
    [--SP] = R1;
    [--SP] = R0;
    SP += -12;
    P1.H = op1f_loopback_due;
    P1.L = op1f_loopback_due;
    R4 = [P1];
    R0 = 0;
    [P1] = R0;
    R0 = 2;
    CC = R4 == R0;
    IF !CC JUMP .Lsend;
    os_usb_mode
    R0 = [P1];
    CC = R0 == 1;
    IF CC JUMP .Lsend;
    R0 = [SP + 12];
    CALL op1f_loopback_send_dry;
.Lsend:
    R0 = [SP + 12];
    R1 = [SP + 16];
    R2 = [SP + 20];
    os_usb_send
    CALL (P1);
    R0 = P5;
    R1 = 0x600 (X);
    R0 = R0 - R1;
    R1 = R4;
    R2 = [SP + 12];
    CALL op1f_loopback_after_send;
.Lsend_done:
    SP += 24;
    R4 = [SP++];
    RETS = [SP++];
    RTS;
.size op1f_loopback_usb, .-op1f_loopback_usb
.global op1f_loopback_out
.type op1f_loopback_out, STT_FUNC
op1f_loopback_out:
    [--SP] = ASTAT;
    [--SP] = R0;
    [--SP] = R1;
    [--SP] = P0;
    [--SP] = P2;
    os_speaker
    R0 = B[P0] (Z);
    P2.H = op1f_loopback_speaker;
    P2.L = op1f_loopback_speaker;
    R1 = [P2];
    CC = R1 == 0;
    IF CC JUMP .Lout_keep;
    R0 = 1 (X);
.Lout_keep:
    P2.H = op1f_loopback_jack;
    P2.L = op1f_loopback_jack;
    B[P2] = R0;
    P1 = P2;
    P2 = [SP++];
    P0 = [SP++];
    R1 = [SP++];
    R0 = [SP++];
    ASTAT = [SP++];
    RTS;
.size op1f_loopback_out, .-op1f_loopback_out
.data
.balign 4
.global op1f_loopback_shut
.type op1f_loopback_shut, STT_OBJECT
op1f_loopback_shut:
    .space 0x48
    .long 1
.size op1f_loopback_shut, .-op1f_loopback_shut
.bss
.balign 4

.global op1f_loopback_return
.type op1f_loopback_return, STT_OBJECT
op1f_loopback_return:
    .space 512
.size op1f_loopback_return, .-op1f_loopback_return
.global op1f_loopback_dry
.type op1f_loopback_dry, STT_OBJECT
op1f_loopback_dry:
    .space 512
.size op1f_loopback_dry, .-op1f_loopback_dry
.global op1f_loopback_jack
.type op1f_loopback_jack, STT_OBJECT
op1f_loopback_jack:
    .space 4
.size op1f_loopback_jack, .-op1f_loopback_jack
