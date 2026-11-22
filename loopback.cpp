#include "build_m3_card.h"
#include "loopback_parts.h"

typedef unsigned u32;

#define INPUT_SOURCE (*(volatile u32*)0x11902e48u)
#define INPUT_ROUTE (*(volatile u32*)0x11902e44u)
#include "loopback_os.h"
#define PLAY_METER (*(volatile const int*)0x11902e14u)
#define PLAY_PEAK (*(volatile const int*)0x11902e04u)
#define INPUT_BLOCK ((volatile const int*)0x119025a0u)

enum { MODE_LOOP = 0, MODE_BREAK = 1, MODE_WET = 2, MODES = 3, INPUT_SCREEN = 43,
       KEY_BLUE_CLICK = 54, KEY_GRAY_CLICK = 56, FRAMES = 64,
       SAVE_FOLDER = 0, SAVE_QUIET_MS = 1000, SAVE_MAGIC = 0x4b4f4f4c, SAVE_VERSION = 2 };

extern "C" const Op1fCard op1f_card_loopback OP1F_NAMED("op1f_card_loopback");
static const char SAVE_NAME[] = "loopback.bin";

extern "C" volatile u32 op1f_loopback_mode OP1F_NAMED("op1f_loopback_mode");
extern "C" volatile u32 op1f_loopback_speaker OP1F_NAMED("op1f_loopback_speaker");
extern "C" volatile u32 op1f_loopback_held OP1F_NAMED("op1f_loopback_held");
extern "C" volatile u32 op1f_loopback_due OP1F_NAMED("op1f_loopback_due");
extern "C" volatile u32 op1f_loopback_fresh OP1F_NAMED("op1f_loopback_fresh");
extern "C" volatile int op1f_loopback_inpeak OP1F_NAMED("op1f_loopback_inpeak");
extern "C" volatile u32 op1f_loopback_amp OP1F_NAMED("op1f_loopback_amp");
extern "C" { volatile u32 op1f_loopback_mode = 0, op1f_loopback_speaker = 0, op1f_loopback_held = 0,
             op1f_loopback_due = 0, op1f_loopback_fresh = 0, op1f_loopback_amp = 0;
             volatile int op1f_loopback_inpeak = 0; }
extern "C" const int op1f_loopback_dry[128] OP1F_NAMED("op1f_loopback_dry");
extern "C" const int op1f_loopback_return[128] OP1F_NAMED("op1f_loopback_return");

static volatile u32 edits;

static inline int mul(int a, int b) { return __builtin_bfin_mult_fr1x32x32(a, b); }
static inline int add(int a, int b) { return __builtin_bfin_add_fr1x32(a, b); }

static void monitor(int* out) {
    const int* in = op1f_loopback_return;
    int left = INSTRUMENT_GAIN[0], right = INSTRUMENT_GAIN[1];
    for (int i = 0; i < FRAMES; ++i) {
        out[2 * i] = add(out[2 * i], mul(in[2 * i], left));
        out[2 * i + 1] = add(out[2 * i + 1], mul(in[2 * i + 1], right));
    }
}

extern "C" void op1f_loopback_send_dry(int* slot) OP1F_NAMED("op1f_loopback_send_dry");
extern "C" void op1f_loopback_send_dry(int* slot) {
    int left = INSTRUMENT_GAIN[0], right = INSTRUMENT_GAIN[1];
    for (int i = 0; i < FRAMES; ++i) {
        slot[i] = mul(op1f_loopback_dry[i], left);
        slot[FRAMES + i] = mul(op1f_loopback_dry[FRAMES + i], right);
    }
}

static volatile int level_send, level_return;

static int peak_of(const int* a, int n, int peak) {
    for (int i = 0; i < n; ++i) {
        int v = a[i] < 0 ? -(a[i] + 1) : a[i];
        if (v > peak) peak = v;
    }
    return peak;
}

extern "C" void op1f_loopback_after_send(int* out, u32 mark, const int* slot) OP1F_NAMED("op1f_loopback_after_send");
extern "C" void op1f_loopback_after_send(int* out, u32 mark, const int* slot) {
    level_send = peak_of(USB_MODE == 1u ? out : slot, 2 * FRAMES, level_send);
    if (op1f_loopback_fresh) {
        op1f_loopback_fresh = 0;
        level_return = peak_of(op1f_loopback_return, 2 * FRAMES, level_return);
    }
    if (mark) monitor(out);
}

static int taken_click(const Op1fInput* e, unsigned key) {
    if (e->key != key) return 0;
    if (e->what == (unsigned)OP1F_UP) return 1;
    if (e->what != (unsigned)OP1F_DOWN) return 0;
    return e->screen == (unsigned)INPUT_SCREEN ? 2 : 0;
}

extern "C" int loopback_input(const Op1fInput* e) OP1F_NAMED("loopback_input");
extern "C" int loopback_input(const Op1fInput* e) {
    if (e->bytes < 36u) return 0;
    int blue = taken_click(e, KEY_BLUE_CLICK);
    if (blue == 1) return 1;
    if (blue == 2) {
        u32 next = op1f_loopback_mode + 1u;
        op1f_loopback_mode = next >= (u32)MODES ? 0u : next;
        edits = edits + 1;
        return 1;
    }
    int gray = taken_click(e, KEY_GRAY_CLICK);
    if (gray == 1) return 1;
    if (gray == 2) {
        op1f_loopback_speaker = op1f_loopback_speaker ? 0u : 1u;
        edits = edits + 1;
        return 1;
    }
    return 0;
}

struct Saved { u32 magic, version, mode, speaker; };
static struct { u32 loaded, edits_seen, changed_ms; } disk;

static void load_settings() {
    Saved s;
    int got = op1f_read(&op1f_card_loopback, SAVE_FOLDER, SAVE_NAME, &s, sizeof s);
    if (got != (int)sizeof s || s.magic != (u32)SAVE_MAGIC || s.version != (u32)SAVE_VERSION) return;
    if (s.mode >= (u32)MODES || s.speaker > 1u) return;
    op1f_loopback_mode = s.mode;
    op1f_loopback_speaker = s.speaker;
}

static void keep_settings(const Op1fFrame* now) {
    if (!disk.loaded) { disk.loaded = 1; load_settings(); disk.edits_seen = edits; return; }
    if (edits != disk.edits_seen) { disk.edits_seen = edits; disk.changed_ms = now->ms ? now->ms : 1u; return; }
    if (!disk.changed_ms || now->ms - disk.changed_ms < (u32)SAVE_QUIET_MS || now->disk) return;
    Saved s = { (u32)SAVE_MAGIC, (u32)SAVE_VERSION, op1f_loopback_mode, op1f_loopback_speaker };
    op1f_write(&op1f_card_loopback, SAVE_FOLDER, SAVE_NAME, &s, sizeof s);
    disk.changed_ms = 0;
}

enum { Q = 1024, SAMP = 686, SAMP_TX = 80204, SAMP_TY = -599 };
enum { SOUND = 0x00400000,
       HOLD_MS = 300 };

static struct {
    void* document;
    void* part[LB_PARTS];
    signed char shown[LB_PARTS];
    int found, up, along[4];
    u32 send_ms, return_ms, in_ms, last_ms;
} strip;

static void make_strip(void* document) {
    strip.document = document;
    strip.found = 0;
    strip.up = 0;
    for (int p = 0; p < LB_PARTS; ++p) { strip.part[p] = 0; strip.shown[p] = -1; }
    if (!document) return;
    for (int p = 0; p < LB_PARTS; ++p) {
        strip.part[p] = op1f_node(document, LB_FIXED_NAME[p]);
        if (strip.part[p]) ++strip.found;
    }
}

static void show(int p, int on) {
    if (p < 0 || !strip.part[p] || strip.shown[p] == on) return;
    op1f_show(strip.part[p], on);
    strip.shown[p] = (signed char)on;
}

static const char* const ICON_PART[2] = { "inputs_texts", "input_icons" };

static int matrix_dy(void* node) { return ((const int*)((const char*)node + 4))[7]; }

static struct { void* doc; void* group; void* part[2]; } icons;

static void hold_icons(void* document) {
    if (document != icons.doc) {
        icons.doc = document;
        icons.group = document ? op1f_node(document, "inputs") : 0;
        for (int i = 0; i < 2; ++i) icons.part[i] = document ? op1f_node(document, ICON_PART[i]) : 0;
    }
    if (!icons.group) return;
    int back = -matrix_dy(icons.group);
    int m[9] = { Q, 0, 0, 0, Q, 0, 0, back, Q };
    for (int i = 0; i < 2; ++i)
        if (icons.part[i] && matrix_dy(icons.part[i]) != back) op1f_move(icons.part[i], m);
}

static int overlay_up(void* document) {
    static void* doc;
    static void* rec;
    static void* stand;
    if (document != doc) {
        doc = document;
        rec = document ? op1f_node(document, "recording") : 0;
        stand = document ? op1f_node(document, "standby") : 0;
    }
    if (rec && ((const unsigned char*)rec)[0x5c] != 0) return 1;
    if (stand && ((const unsigned char*)stand)[0x5c] != 0) return 1;
    return 0;
}

static signed char placed[LB_PARTS];

static void fit_sample(void* document) {
    if (!document) return;
    void* box = op1f_node(document, "keytorec");
    if (!box || ((const unsigned char*)box)[0x5c] == 0) return;
    int m[9] = { SAMP, 0, 0, 0, SAMP, 0, SAMP_TX, SAMP_TY, Q };
    op1f_move(box, m);
}

static void place(int p, int x, int y) {
    if (p < 0 || !strip.part[p]) return;
    int m[9] = { Q, 0, 0, 0, Q, 0, x, y, Q };
    op1f_move(strip.part[p], m);
    placed[p] = 1;
}

static const LbPt* const PATH_P[] = {
    LB_LN_OUT_P, LB_LN_OUTO_P, LB_LN_RISE_P, LB_LN_BACK_P, LB_LN_BACKO_P, LB_LN_BACKR_P, LB_LN_SPUR_P, LB_LN_SPURR_P,
    LB_US_OUT_P, LB_US_OUTO_P, LB_US_RISE_P, LB_US_BACK_P, LB_US_BACKO_P, LB_US_BACKR_P, LB_US_SPUR_P, LB_US_SPURR_P,
    LB_MIC_P, LB_RD_IN_P, LB_RD_SPUR_P, LB_EA_OUT_P, LB_EA_BACK_P, LB_EA_SPUR_P, LB_FIELD_OUT_P,
};
static const int PATH_N[] = {
    LB_LN_OUT_N, LB_LN_OUTO_N, LB_LN_RISE_N, LB_LN_BACK_N, LB_LN_BACKO_N, LB_LN_BACKR_N, LB_LN_SPUR_N, LB_LN_SPURR_N,
    LB_US_OUT_N, LB_US_OUTO_N, LB_US_RISE_N, LB_US_BACK_N, LB_US_BACKO_N, LB_US_BACKR_N, LB_US_SPUR_N, LB_US_SPURR_N,
    LB_MIC_N, LB_RD_IN_N, LB_RD_SPUR_N, LB_EA_OUT_N, LB_EA_BACK_N, LB_EA_SPUR_N, LB_FIELD_OUT_N,
};

static int wire_len(int path) {
    const LbPt* p = PATH_P[path - LB_LN_OUT];
    int n = PATH_N[path - LB_LN_OUT];
    int total = 0;
    for (int i = 1; i < n; ++i) {
        int dx = p[i].x - p[i - 1].x, dy = p[i].y - p[i - 1].y;
        if (dx < 0) dx = -dx;
        if (dy < 0) dy = -dy;
        total += dx + dy;
    }
    return total;
}

static void put_on(int part, int path, int left) {
    const LbPt* p = PATH_P[path - LB_LN_OUT];
    int n = PATH_N[path - LB_LN_OUT];
    for (int i = 1; i < n; ++i) {
        int dx = p[i].x - p[i - 1].x, dy = p[i].y - p[i - 1].y;
        int adx = dx < 0 ? -dx : dx, ady = dy < 0 ? -dy : dy;
        int seg = (adx + ady) * Q;
        if (left < seg || i + 1 == n) {
            int x = p[i - 1].x * Q, y = p[i - 1].y * Q;
            if (dx > 0) x += left;
            else if (dx < 0) x -= left;
            if (dy > 0) y += left;
            else if (dy < 0) y -= left;
            place(part, x, y);
            return;
        }
        left -= seg;
    }
}

static void walk(signed char* want, int part, int path, int path2, int on, u32 dt, int slot) {
    int total = wire_len(path);
    if (path2 >= 0) total += wire_len(path2);
    int len = total * Q;
    int at = strip.along[slot];
    if (on && len > 0) {
        at += (int)((u32)total * dt);
        while (at >= len) at -= len;
        strip.along[slot] = at;
    }
    if (!on || len <= 0) return;
    want[part] = 1;
    int first = wire_len(path) * Q;
    if (path2 < 0 || at < first) put_on(part, path, at);
    else put_on(part, path2, at - first);
}

static int magnitude(int v) { return v < 0 ? -(v + 1) : v; }

static int field_playing(int usb_peak) {
    int level = magnitude(PLAY_METER);
    int peak = magnitude(PLAY_PEAK);
    if (peak > level) level = peak;
    if (usb_peak > level) level = usb_peak;
    return level > SOUND;
}

static int input_arriving(void* document, int inn) {
    if (inn > SOUND) return 1;
    if ((INPUT_ROUTE == 0 || op1f_loopback_amp) && INPUT_BLOCK) {
        for (int i = 0; i < 128; ++i) {
            int v = magnitude(INPUT_BLOCK[i]);
            if (v > inn) inn = v;
        }
        if (inn > SOUND) return 1;
    }
    static void* level_doc;
    static void* level_node;
    if (document != level_doc) {
        level_doc = document;
        level_node = document ? op1f_node(document, "slowinputlevel") : 0;
    }
    if (level_node) {
        int dy = ((const int*)((const char*)level_node + 4))[7] >> 10;
        if (dy < -3) return 1;
    }
    return 0;
}

static void dress_strip(const Op1fFrame* now) {
    void* document = op1f_screen(INPUT_SCREEN);
    if (document != strip.document) make_strip(document);
    hold_icons(document);
    fit_sample(document);
    int send = level_send, back = level_return, inn = op1f_loopback_inpeak;
    level_send = 0;
    level_return = 0;
    op1f_loopback_inpeak = 0;
    if (strip.found != LB_PARTS) return;
    u32 ms = now->ms;
    int src = (int)INPUT_SOURCE;
    int mode = op1f_loopback_mode < (u32)MODES ? (int)op1f_loopback_mode : 0;
    int up = src >= 0 && src < LB_SRC && now->screen == (u32)INPUT_SCREEN;
    int open = INPUT_ROUTE == 0 || op1f_loopback_amp != 0;
    int playing = field_playing(send);
    int arriving = input_arriving(document, inn);
    if (!open) strip.send_ms = strip.return_ms = strip.in_ms = 0;
    else {
        if (playing) strip.send_ms = ms ? ms : 1u;
        if (back > SOUND) strip.return_ms = ms ? ms : 1u;
        if (arriving) strip.in_ms = ms ? ms : 1u;
    }
    if (!up) {
        if (strip.up || strip.shown[0] != 0) {
            for (int p = 0; p < LB_PARTS; ++p) show(p, 0);
            strip.up = 0;
        }
        return;
    }
    strip.up = 1;
    if (overlay_up(document)) {
        for (int p = 0; p < LB_PARTS; ++p) show(p, 0);
        return;
    }
    int kind = LB_KIND[src];
    int cable = SPEAKER_GATE == 0;
    int force = op1f_loopback_speaker != 0;
    int speaker_on = !cable || force;
    int line_on = cable;
    int both = speaker_on && line_on;
    int sending = open && strip.send_ms && ms - strip.send_ms < (u32)HOLD_MS;
    int returning = open && strip.return_ms && ms - strip.return_ms < (u32)HOLD_MS;
    int incoming = open && strip.in_ms && ms - strip.in_ms < (u32)HOLD_MS;
    signed char want[LB_PARTS];
    for (int p = 0; p < LB_PARTS; ++p) { want[p] = 0; placed[p] = 0; }
    want[LB_FIELD] = 1;
    want[LB_WORD0 + mode] = 1;
    if (kind == LB_LOOP && mode != MODE_LOOP) {
        want[LB_STOP] = 1;
        place(LB_STOP, (src == 1 ? LB_LINE_MID : LB_USB_MID) * Q, LB_STOP_Y * Q);
    }
    if (speaker_on) {
        want[LB_SPEAKER] = 1;
        place(LB_SPEAKER, LB_JOIN_X * Q, (both ? LB_SPK_Y : LB_SPK_ONLY_Y) * Q);
    }
    if (line_on) {
        want[LB_LINE] = 1;
        place(LB_LINE, LB_JOIN_X * Q, (both ? LB_PLUG_Y : LB_PLUG_ONLY_Y) * Q);
    }
    if (both) {
        want[LB_PLUS] = 1;
        place(LB_PLUS, LB_JOIN_X * Q, LB_PLUS_Y * Q);
    }
    int base = src == 1 ? LB_LN_OUT : LB_US_OUT;
    int outp = base, backp = base + 3, spurp = base + 6;
    if (kind == LB_LOOP) {
        int open_cable = mode != MODE_LOOP;
        outp = base + (open_cable ? 1 : 0);
        want[outp] = 1;
        want[base + 2] = 1;
        if (mode == MODE_WET) { backp = base + 5; spurp = base + 7; }
        else if (open_cable) { backp = base + 4; spurp = base + 6; }
        else { backp = base + 3; spurp = base + 6; }
        want[backp] = 1;
        want[spurp] = 1;
        if (mode == MODE_BREAK && open && (sending || returning)) {
            want[LB_MIX] = 1;
            place(LB_MIX, (src == 1 ? LB_LINE_MID : LB_USB_MID) * Q, LB_ROUTE_TOP * Q);
        }
    } else if (src == 0) {
        want[LB_MIC] = 1;
        want[LB_FIELD_OUT] = 1;
        outp = LB_MIC;
    } else if (src == 2) {
        want[LB_RD_IN] = 1;
        want[LB_RD_SPUR] = 1;
        want[LB_FIELD_OUT] = 1;
        outp = LB_RD_IN;
    } else {
        want[LB_EA_OUT] = 1;
        want[LB_EA_BACK] = 1;
        want[LB_EA_SPUR] = 1;
        outp = LB_EA_OUT;
        backp = LB_EA_BACK;
    }
    u32 dt = ms - strip.last_ms;
    strip.last_ms = ms;
    if (dt > 100u) dt = 100u;
    if (kind == LB_LOOP) {
        int ret = mode == MODE_WET ? LB_DOT_WET : LB_DOT_BACK;
        walk(want, LB_DOT_OUT, outp, -1, sending, dt, 0);
        walk(want, LB_DOT_RED, base + 2, -1, incoming, dt, 1);
        walk(want, ret, backp, spurp, returning, dt, 2);
    } else if (src == 4) {
        walk(want, LB_DOT_OUT, outp, -1, sending, dt, 0);
        walk(want, LB_DOT_BACK, backp, LB_EA_SPUR, returning || incoming, dt, 2);
    } else if (src == 2) {
        walk(want, LB_DOT_RED, LB_RD_IN, -1, incoming, dt, 1);
        walk(want, LB_DOT_WET, LB_RD_SPUR, -1, incoming, dt, 3);
        walk(want, LB_DOT_OUT, LB_FIELD_OUT, -1, sending, dt, 0);
    } else {
        walk(want, LB_DOT_RED, outp, -1, incoming, dt, 1);
        walk(want, LB_DOT_OUT, LB_FIELD_OUT, -1, sending, dt, 0);
    }
    for (int p = 0; p < LB_PARTS; ++p) {
        if (want[p] && !placed[p]) place(p, 0, 0);
        show(p, want[p]);
    }
}

extern "C" void loopback_frame(const Op1fFrame* now) OP1F_NAMED("loopback_frame");
extern "C" void loopback_frame(const Op1fFrame* now) {
    if (!now || now->bytes < 36u) return;
    keep_settings(now);
    dress_strip(now);
}
