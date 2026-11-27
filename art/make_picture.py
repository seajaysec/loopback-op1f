#!/usr/bin/env python3
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_BYTES, BASE_CRC = 48711, "27d5c7b5"

LIT, DIM = "#CDD0C2", "#545E69"
BLUE, PURPLE, RED = "#6CB4F0", "#C43BFF", "#E52817"
NAVY = "#245580"
KNOBS = ("#3C6087", "#8A653C", "#CDD0C2", "#E52817")

PLACES = {
    "sample": (105.0, 15.8, 370.0, 86.0),
    "mic": (80.8, 109.6, 98.2, 154.6),
    "line": (84.4, 109.5, 94.4, 167.1),
    "headset": (74.4, 110.8, 104.1, 151.2),
    "radio": (162.0, 102.7, 215.5, 155.3),
    "usb": (262.1, 110.9, 279.6, 167.1),
    "ear": (338.1, 112.5, 373.4, 152.5),
    "lab0": (73.0, 182.8, 107.2, 192.8),
    "lab1": (152.1, 182.8, 201.2, 193.5),
    "lab2": (257.2, 182.7, 286.5, 192.8),
    "lab3": (328.6, 182.5, 383.3, 192.5),
}

FIELD = (8, 194, 44, 208)
LABEL0_LEFT, LABEL0_RIGHT, LABEL0_BOTTOM = 51.2, 127.6, 193.5
ARCH, IN_Y, FX = 61, 208, 54
LIFT = 34
JOIN = (409, 150)
BEND, GAP = 8, 0
FIELD_END = FIELD[2] + 2
ROUTE_TOP = 95
RISE_FROM = 108
SPK_Y, PLUS_Y, PLUG_Y = 96, 122, 140
SPK_ONLY_Y, PLUG_ONLY_Y = 128, 140
NUM = r"[-+]?(?:\d+\.\d+|\d+|\.\d+)(?:[eE][-+]?\d+)?"
TOK = re.compile(r"[MmLlHhVvCcSsZz]|" + NUM)

def f(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")

def path(colour, d, width=1.0, fill="none", cap="round"):
    return '<path fill="%s" stroke="%s" stroke-width="%s" stroke-linecap="%s" d="%s"/>' % (
        fill, colour, f(width), cap, d)

def line(colour, x0, y0, x1, y1, width=1.0, cap="round"):
    return path(colour, "M%s,%sL%s,%s" % tuple(map(f, (x0, y0, x1, y1))), width, cap=cap)

def rounded(x0, y0, x1, y1, r):
    if x1 - x0 <= 0 or y1 - y0 <= 0:
        raise SystemExit("a box with no inside: %s" % ((x0, y0, x1, y1),))
    r = min(r, (x1 - x0) / 2.0, (y1 - y0) / 2.0)
    k = r * 0.45
    def L(x, y, px, py):
        return "" if (x, y) == (px, py) else "L%s,%s" % (f(x), f(y))
    def C(c1x, c1y, c2x, c2y, x, y):
        return "C%s,%s %s,%s %s,%s" % tuple(map(f, (c1x, c1y, c2x, c2y, x, y)))
    d = "M%s,%s" % (f(x0 + r), f(y0))
    d += L(x1 - r, y0, x0 + r, y0) + C(x1 - k, y0, x1, y0 + k, x1, y0 + r)
    d += L(x1, y1 - r, x1, y0 + r) + C(x1, y1 - k, x1 - k, y1, x1 - r, y1)
    d += L(x0 + r, y1, x1 - r, y1) + C(x0 + k, y1, x0, y1 - k, x0, y1 - r)
    d += L(x0, y0 + r, x0, y1 - r) + C(x0, y0 + k, x0 + k, y0, x0 + r, y0)
    return d + "z"

def arrow(colour, x, y, dx, dy, size=2.4):
    px, py = -dy, dx
    pts = (x, y, x - dx * size + px * size * 0.7, y - dy * size + py * size * 0.7,
           x - dx * size - px * size * 0.7, y - dy * size - py * size * 0.7)
    return '<path fill="%s" stroke="%s" stroke-width="0.5" d="M%s,%sL%s,%sL%s,%sz"/>' % (
        (colour, colour) + tuple(map(f, pts)))

def circle(colour, cx, cy, r):
    return '<circle fill="%s" stroke="%s" stroke-width="0.5" cx="%s" cy="%s" r="%s"/>' % (
        colour, colour, f(cx), f(cy), f(r))

def field_art():
    x0, y0, x1, y1 = FIELD
    w, h = x1 - x0, y1 - y0
    body = path(LIT, rounded(x0, y0, x1, y1, 3.2), 2.2)
    screen = path(LIT, rounded(x0 + 4, y0 + 4, x0 + w * 0.46, y0 + h * 0.40, 1.4), 1.6)
    knobs = "".join(circle(c, x0 + w * 0.56 + i * (w * 0.10), y0 + h * 0.20, 2.3) for i, c in enumerate(KNOBS))
    keys = ""
    for i in range(8):
        kx = x0 + w * 0.07 + i * (w * 0.112)
        keys += path(LIT, "M%s,%sH%sV%sH%sz" % tuple(map(f, (kx, y1 - h * 0.40, kx + w * 0.07, y1 - h * 0.08, kx))), 0.9, fill=LIT)
    return body + screen + knobs + keys

def orth(points):
    d = "M%s,%s" % (f(points[0][0]), f(points[0][1]))
    px, py = points[0]
    for x, y in points[1:]:
        if y == py:
            d += "H%s" % f(x)
        elif x == px:
            d += "V%s" % f(y)
        else:
            raise SystemExit("a wire that is not orthogonal: %s" % (points,))
        px, py = x, y
    return d

def wire(colour, points, width=3.6):
    return path(colour, orth(points), width)

def bead(colour):
    return circle("#07080a", 0, 0, 9.6) + circle(colour, 0, 0, 7.2)

def glyph(ch, x, y, s, colour=NAVY, stroke=1.55):
    u = s
    def P(*pairs):
        pts = []
        for i in range(0, len(pairs), 2):
            pts.append((x + pairs[i] * u, y + pairs[i + 1] * u))
        return path(colour, "M%s,%s" % (f(pts[0][0]), f(pts[0][1])) + "".join(
            "L%s,%s" % (f(a), f(b)) for a, b in pts[1:]), stroke)
    if ch == "L":
        return P(0, 0, 0, 6, 3.6, 6)
    if ch == "O":
        return path(colour, rounded(x + 0.3 * u, y + 0.3 * u, x + 3.6 * u, y + 5.7 * u, 0.7 * u), stroke)
    if ch == "P":
        return P(0, 6, 0, 0, 2.6, 0) + path(colour, "M%s,%sC%s,%s %s,%s %s,%sL%s,%s" % tuple(map(f, (
            x + 2.6 * u, y, x + 3.7 * u, y, x + 3.7 * u, y + 2.7 * u, x + 2.6 * u, y + 2.7 * u, x, y + 2.7 * u))), stroke)
    if ch == "D":
        return P(0, 0, 0, 6, 2.2, 6) + path(colour, "M%s,%sC%s,%s %s,%s %s,%sL%s,%s" % tuple(map(f, (
            x + 2.2 * u, y + 6 * u, x + 3.8 * u, y + 6 * u, x + 3.8 * u, y, x + 2.2 * u, y, x, y))), stroke)
    if ch == "R":
        return glyph("P", x, y, s, colour, stroke) + P(1.4, 2.7, 3.6, 6)
    if ch == "S":
        return P(3.6, 0.4, 0.3, 0.4, 0.2, 2.8, 3.4, 3.2, 3.4, 5.6, 0, 5.6)
    if ch == "Y":
        return P(0, 0, 1.8, 2.8, 3.6, 0) + P(1.8, 2.8, 1.8, 6)
    if ch == "+":
        return P(0.2, 3, 3.4, 3) + P(1.8, 1.2, 1.8, 4.8)
    if ch == "W":
        return P(0, 0, 0.2, 6, 1.8, 2.4, 3.4, 6, 3.6, 0)
    if ch == "E":
        return P(3.6, 0, 0, 0, 0, 6, 3.6, 6) + P(0, 3, 2.8, 3)
    if ch == "F":
        return P(3.6, 0, 0, 0, 0, 6) + P(0, 3, 2.8, 3)
    if ch == "T":
        return P(0, 0, 3.6, 0) + P(1.8, 0, 1.8, 6)
    raise SystemExit("no letter %s" % ch)

def word_art(lines):
    s = 1.55
    letter_gap = 3.6
    line_gap = 4.2
    advance = 3.6 * s + letter_gap
    pitch = 6 * s + line_gap
    x0, y0, x1, _ = FIELD
    room = x1 - x0
    widths = []
    for text in lines:
        width = advance * len(text) - letter_gap
        if width > room:
            raise SystemExit("the word %s is wider than the Field: %.1f > %d" % (text, width, room))
        widths.append(width)
    top = y0 - 8 - 6 * s - (len(lines) - 1) * pitch
    art = ""
    for i, text in enumerate(lines):
        x = x0 + (room - widths[i]) / 2.0
        y = top + i * pitch
        art += "".join(glyph(ch, x + n * advance, y, s) for n, ch in enumerate(text))
    return art

def speaker_art():
    half = 13.0
    art = path(LIT, "M%s,%sH%sV%sH%sz" % tuple(map(f, (-half, -half, half, half, -half))), 1.8)
    n, cut = 7, (2, 1, 0, 0, 0, 1, 2)
    inset = 3.1
    step = (half * 2 - inset * 2) / (n - 1)
    first = -half + inset
    for row in range(n):
        for col in range(cut[row], n - cut[row]):
            art += circle(LIT, first + col * step, first + row * step, 0.72)
    return art

def plug_art():
    s = 1.6
    def z(v):
        return v * s
    body = path(LIT, rounded(z(-11.1), z(-3.05), z(-1.1), z(3.05), z(0.9)), 1.7)
    bar = line(RED, z(-6.1), z(-3.55), z(-6.1), z(3.55), 2.1)
    shaft = line(LIT, z(-1.1), z(-2.05), z(6.9), z(-2.05), 1.7) + line(LIT, z(-1.1), z(2.05), z(6.9), z(2.05), 1.7)
    rings = line(LIT, z(1.9), z(-2.05), z(1.9), z(2.05), 1.7) + line(LIT, z(4.9), z(-2.05), z(4.9), z(2.05), 1.7)
    tip = path(LIT, "M%s,%sL%s,%sL%s,%sL%s,%sL%s,%sL%s,%s" % tuple(map(f, (
        z(6.9), z(-2.05), z(9.1), z(-1.05), z(11.1), z(-1.45), z(11.1), z(1.45), z(9.1), z(1.05), z(6.9), z(2.05)))), 1.7)
    return body + bar + shaft + rings + tip

def plus_art():
    return line(LIT, -7.2, 0, 7.2, 0, 1.8, "square") + line(LIT, 0, -7.2, 0, 7.2, 1.8, "square")

STOP_R = 11.0
STOP_GAP = 8
STOP_Y = 95 - 11 - 3

def stop_art():
    import math
    def octagon(r):
        pts = [(r * math.cos(math.pi / 8 + i * math.pi / 4), r * math.sin(math.pi / 8 + i * math.pi / 4)) for i in range(8)]
        return "M%s,%s" % (f(pts[0][0]), f(pts[0][1])) + "".join("L%s,%s" % (f(x), f(y)) for x, y in pts[1:]) + "z"
    art = path(RED, octagon(STOP_R), 0.8, fill=RED)
    art += path(LIT, octagon(STOP_R - 1.6), 1.1)
    s = 0.62
    advance = 3.6 * s + 1.5
    width = advance * 4 - 1.5
    x0, y0 = -width / 2.0, -3 * s
    return art + "".join(glyph(ch, x0 + i * advance, y0, s, LIT, 0.95) for i, ch in enumerate("STOP"))

def bracket(outer_l, pillar_l, pillar_r, outer_r, top, jog, mid):
    stop = outer_l + GAP
    closed_out = [(FIELD_END, IN_Y), (outer_l, IN_Y), (outer_l, jog), (pillar_l, jog), (pillar_l, top), (mid, top)]
    open_out = [(FIELD_END, IN_Y), (outer_l, IN_Y), (outer_l, jog), (pillar_l, jog), (pillar_l, top), (mid - STOP_GAP, top)]
    closed_back = [(mid, top), (pillar_r, top), (pillar_r, jog), (outer_r, jog), (outer_r, IN_Y), (stop, IN_Y)]
    open_back = [(mid + STOP_GAP, top), (pillar_r, top), (pillar_r, jog), (outer_r, jog), (outer_r, IN_Y), (stop, IN_Y)]
    spur = [(outer_r, IN_Y), (JOIN[0], IN_Y), (JOIN[0], JOIN[1])]
    return closed_out, open_out, closed_back, open_back, spur

def rise(mid):
    return [(mid, RISE_FROM), (mid, ROUTE_TOP)]

LINE = bracket(64, 80, 98, 114, ROUTE_TOP, 158, 89)
USB = bracket(232, 248, 294, 310, ROUTE_TOP, 158, 271)
EAR_TOP = ROUTE_TOP
EAR_OUT = [(FIELD_END, IN_Y), (316, IN_Y), (316, 160), (332, 160), (332, EAR_TOP), (355, EAR_TOP)]
EAR_BACK = [(355, EAR_TOP), (378, EAR_TOP), (378, 160), (396, 160), (396, IN_Y), (316 + GAP, IN_Y)]
EAR_SPUR = [(396, IN_Y), (JOIN[0], IN_Y), (JOIN[0], JOIN[1])]
KAPPA = 0.5523

def bresenham(pts, x1, y1):
    x0, y0 = pts[-1]
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx - dy
    while (x0, y0) != (x1, y1):
        e2 = 2 * err
        stepped = False
        if e2 > -dy:
            err -= dy
            x0 += sx
            stepped = True
        if e2 < dx:
            if stepped and (x0, y0) != (x1, y1):
                pts.append((x0, y0))
            err += dx
            y0 += sy
        pts.append((x0, y0))

def sample_curve(pts, p0, c1, c2, p3):
    prev = pts[-1]
    for i in range(1, 13):
        t = i / 12.0
        u = 1.0 - t
        x = u*u*u*p0[0] + 3*u*u*t*c1[0] + 3*u*t*t*c2[0] + t*t*t*p3[0]
        y = u*u*u*p0[1] + 3*u*u*t*c1[1] + 3*u*t*t*c2[1] + t*t*t*p3[1]
        ip = (int(round(x)), int(round(y)))
        if ip != prev:
            bresenham(pts, ip[0], ip[1])
            prev = pts[-1]

def build_wire(points, radius=BEND):
    if len(points) < 2:
        raise SystemExit("a wire needs two ends")
    for a, b in zip(points, points[1:]):
        if a[0] != b[0] and a[1] != b[1]:
            raise SystemExit("a wire that is not orthogonal: %s" % (points,))
    cuts = []
    n = len(points)
    for i, p in enumerate(points):
        if i == 0 or i + 1 == n:
            cuts.append(None)
            continue
        prev, nxt = points[i - 1], points[i + 1]
        lin = abs(p[0] - prev[0]) + abs(p[1] - prev[1])
        lout = abs(nxt[0] - p[0]) + abs(nxt[1] - p[1])
        r = min(radius, lin / 2.0, lout / 2.0)
        if r < 1:
            cuts.append(None)
            continue
        def cut(a, b, dist):
            length = abs(b[0] - a[0]) + abs(b[1] - a[1])
            t = dist / length
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        cuts.append((cut(p, prev, r), cut(p, nxt, r)))
    walker = [(int(round(points[0][0])), int(round(points[0][1])))]
    d = "M%s,%s" % (f(points[0][0]), f(points[0][1]))
    cursor = points[0]
    for i in range(1, n):
        p = points[i]
        incoming = cuts[i][0] if cuts[i] else p
        if incoming != cursor:
            if incoming[1] == cursor[1]:
                d += "H%s" % f(incoming[0])
            elif incoming[0] == cursor[0]:
                d += "V%s" % f(incoming[1])
            else:
                raise SystemExit("a fillet left a diagonal")
            end = (int(round(incoming[0])), int(round(incoming[1])))
            if end != walker[-1]:
                walker.append(end)
        if cuts[i]:
            c_in, c_out = cuts[i]
            c1 = (c_in[0] + (p[0] - c_in[0]) * KAPPA, c_in[1] + (p[1] - c_in[1]) * KAPPA)
            c2 = (c_out[0] + (p[0] - c_out[0]) * KAPPA, c_out[1] + (p[1] - c_out[1]) * KAPPA)
            d += "C%s,%s %s,%s %s,%s" % tuple(map(f, (c1[0], c1[1], c2[0], c2[1], c_out[0], c_out[1])))
            sample_curve(walker, c_in, c1, c2, c_out)
            cursor = c_out
        else:
            cursor = incoming
    return d, walker

def slant_points(x, y, side, home):
    land = max(y + 24, 178)
    p0, p1, p2, p3 = (x, y), (x, y + 12), (side, y + 18), (side, land)
    raw = []
    for i in range(33):
        t = i / 32.0
        u = 1.0 - t
        px = u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0]
        py = u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1]
        ip = (int(round(px)), int(round(py)))
        if not raw or raw[-1] != ip:
            raw.append(ip)
    raw.append((side, IN_Y))
    raw.append((home, IN_Y))
    pts = [raw[0]]
    for a, b in zip(raw, raw[1:]):
        x0, y0 = pts[-1]
        x1, y1 = b
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx - dy
        while (x0, y0) != (x1, y1):
            e2 = 2 * err
            stepped = False
            if e2 > -dy:
                err -= dy
                x0 += sx
                stepped = True
            if e2 < dx:
                if stepped and (x0, y0) != (x1, y1):
                    pts.append((x0, y0))
                err += dx
                y0 += sy
            pts.append((x0, y0))
    return pts

def slant_draw(x, y, side, home):
    land = max(y + 24, 178)
    return "M%s,%sC%s,%s %s,%s %s,%sV%sH%s" % tuple(map(f, (
        x, y, x, y + 12, side, y + 18, side, land, IN_Y, home)))

MIC_X = 134
MIC_Y = 201
MIC_IN = [(90, 157), (90, 166), (MIC_X, 166), (MIC_X, MIC_Y), (FIELD_END, MIC_Y)]
RADIO_FROM = (212, 156, 226, FIELD_END)
RADIO_IN = slant_points(*RADIO_FROM)
RADIO_SPUR = [(226, IN_Y), (JOIN[0], IN_Y), (JOIN[0], JOIN[1])]
FIELD_OUT = [(FIELD_END, IN_Y), (JOIN[0], IN_Y), (JOIN[0], JOIN[1])]
DRAW = {}

def drawn(points):
    d, walk = build_wire(points)
    return d, walk

def wrap(name, body):
    return '<g id="%s">%s</g>' % (name, body)

def c_points(pts):
    return ", ".join("{%d, %d}" % p for p in pts)

def route_row(enum, points, slant=None, home=False):
    if slant:
        DRAW[enum] = slant_draw(*slant)
        return (enum, points)
    d, walk = drawn(points)
    DRAW[enum] = d
    if home and walk[-1] != (FIELD_END, IN_Y):
        walk = walk + [(FIELD_END, IN_Y)]
    return (enum, walk)

ROUTES = [
    route_row("LB_LN_OUT", LINE[0]), route_row("LB_LN_OUTO", LINE[1]), route_row("LB_LN_RISE", rise(89)),
    route_row("LB_LN_BACK", LINE[2], home=True), route_row("LB_LN_BACKO", LINE[3], home=True), route_row("LB_LN_BACKR", LINE[3], home=True),
    route_row("LB_LN_SPUR", LINE[4]), route_row("LB_LN_SPURR", LINE[4]),
    route_row("LB_US_OUT", USB[0]), route_row("LB_US_OUTO", USB[1]), route_row("LB_US_RISE", rise(271)),
    route_row("LB_US_BACK", USB[2], home=True), route_row("LB_US_BACKO", USB[3], home=True), route_row("LB_US_BACKR", USB[3], home=True),
    route_row("LB_US_SPUR", USB[4]), route_row("LB_US_SPURR", USB[4]),
    route_row("LB_MIC", MIC_IN), route_row("LB_RD_IN", RADIO_IN, RADIO_FROM),
    route_row("LB_RD_SPUR", RADIO_SPUR),
    route_row("LB_EA_OUT", EAR_OUT), route_row("LB_EA_BACK", EAR_BACK, home=True), route_row("LB_EA_SPUR", EAR_SPUR),
    route_row("LB_FIELD_OUT", FIELD_OUT),
]
def route_colour(enum):
    key = enum[3:]
    if key in ("MIC", "RD_IN", "RD_SPUR") or key.endswith("RISE") or key.endswith("BACKR") or key.endswith("SPURR"):
        return RED
    if key.endswith("OUT") or key.endswith("OUTO"):
        return BLUE
    return PURPLE

PARTS = [
    ("lbfd", "LB_FIELD"),
    ("lbw0", "LB_WORD0"), ("lbw1", "LB_WORD1"), ("lbw2", "LB_WORD2"), ("lbw3", "LB_WORD3"),
    ("lbst", "LB_STOP"),
    ("lbsp", "LB_SPEAKER"), ("lbhp", "LB_LINE"), ("lbpl", "LB_PLUS"),
    ("lbmx", "LB_MIX"),
] + [("r%02d" % i, enum) for i, (enum, _) in enumerate(ROUTES)] + [
    ("lbd0", "LB_DOT_OUT"), ("lbd1", "LB_DOT_RED"), ("lbd2", "LB_DOT_BACK"), ("lbd3", "LB_DOT_WET"),
]

def art_of(enum):
    if enum == "LB_FIELD":
        return field_art()
    if enum == "LB_WORD0":
        return word_art(["OFF"])
    if enum == "LB_WORD1":
        return word_art(["LOOP"])
    if enum == "LB_WORD2":
        return word_art(["DRY", "+", "WET"])
    if enum == "LB_WORD3":
        return word_art(["WET"])
    if enum == "LB_STOP":
        return stop_art()
    if enum == "LB_SPEAKER":
        return speaker_art()
    if enum == "LB_LINE":
        return plug_art()
    if enum == "LB_PLUS":
        return plus_art()
    if enum == "LB_MIX":
        return circle(PURPLE, 0, 0, 5.2)
    if enum.startswith("LB_DOT_OUT"):
        return bead(BLUE)
    if enum == "LB_DOT_RED" or enum == "LB_DOT_WET":
        return bead(RED)
    if enum == "LB_DOT_BACK":
        return bead(PURPLE)
    if enum in DRAW:
        return path(route_colour(enum), DRAW[enum], 5.0 if enum.endswith("RISE") else 3.6)
    raise SystemExit("no art for %s" % enum)

def header():
    rows = [
        "#pragma once",
        "enum { LB_SRC = 5, LB_IN = 0, LB_LOOP = 1, LB_EAR = 2 };",
        "enum {",
    ]
    rows.append("    " + ", ".join(enum for _, enum in PARTS) + ",")
    rows += [
        "    LB_FIXED",
        "};",
        "enum { LB_PARTS = LB_FIXED };",
        "static const char *const LB_FIXED_NAME[LB_FIXED] = { %s };" % ", ".join('"%s"' % n for n, _ in PARTS),
        "static const int LB_KIND[LB_SRC] = { LB_IN, LB_LOOP, LB_IN, LB_LOOP, LB_EAR };",
        "struct LbPt { int x, y; };",
        "enum { LB_JOIN_X = %d, LB_JOIN_Y = %d, LB_ARCH = %d," % (JOIN[0], JOIN[1], ARCH),
        "       LB_SPK_Y = %d, LB_PLUS_Y = %d, LB_PLUG_Y = %d," % (SPK_Y, PLUS_Y, PLUG_Y),
        "       LB_SPK_ONLY_Y = %d, LB_PLUG_ONLY_Y = %d, LB_LIFT = %d," % (SPK_ONLY_Y, PLUG_ONLY_Y, LIFT),
        "       LB_LINE_MID = 89, LB_USB_MID = 271, LB_ROUTE_TOP = %d, LB_STOP_Y = %d };" % (ROUTE_TOP, STOP_Y),
    ]
    for enum, pts in ROUTES:
        rows.append("static const LbPt %s_P[] = { %s };" % (enum, c_points(pts)))
        rows.append("enum { %s_N = %d };" % (enum, len(pts)))
    rows.append("")
    return "\n".join(rows)

def check_strokes(d, where):
    tokens, i = TOK.findall(d), 0
    cx = cy = 0.0
    cmd, last = None, None
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
        if cmd in ("Z", "z"):
            last = None
            continue
        if cmd == "M":
            cx, cy = float(tokens[i]), float(tokens[i + 1])
            i += 2
            last, cmd = None, "L"
            continue
        if cmd == "C":
            c2x, c2y = float(tokens[i + 2]), float(tokens[i + 3])
            cx, cy = float(tokens[i + 4]), float(tokens[i + 5])
            i += 6
            last = (cx - c2x, cy - c2y)
            if last == (0.0, 0.0):
                last = None
            continue
        if cmd == "L":
            nx, ny = float(tokens[i]), float(tokens[i + 1])
            i += 2
        elif cmd == "H":
            nx, ny = float(tokens[i]), cy
            i += 1
        elif cmd == "V":
            nx, ny = cx, float(tokens[i])
            i += 1
        else:
            raise SystemExit("a path command the check does not know: %s in %s" % (cmd, where))
        v = (nx - cx, ny - cy)
        if v == (0.0, 0.0):
            raise SystemExit("a straight piece of zero length in %s: %s" % (where, d[:80]))
        if last and last[0] * v[1] - last[1] * v[0] == 0 and last[0] * v[0] + last[1] * v[1] < 0:
            raise SystemExit("a stroke that turns straight back in %s: %s" % (where, d[:80]))
        last, cx, cy = v, nx, ny

def build():
    if FIELD[2] + 1.1 > LABEL0_LEFT - 4:
        raise SystemExit("the Field meets the first column's label")
    if MIC_X - 1.8 < LABEL0_RIGHT + 4 or MIC_Y - 1.8 < LABEL0_BOTTOM + 4:
        raise SystemExit("the microphone's wire meets its label")
    if FIELD[3] > 216 or JOIN[0] + 14 > 436:
        raise SystemExit("the picture meets TRIG or leaves the screen")
    if STOP_Y - STOP_R < 60:
        raise SystemExit("the stop sign meets To Sample (its bottom is at y=57)")
    if ARCH < 58 or ARCH > 64:
        raise SystemExit("the arch left the measured band")
    parts = [wrap(name, art_of(enum)) for name, enum in PARTS]
    for part in parts:
        for d in re.findall(r'\bd="([^"]*)"', part):
            check_strokes(d, part[:20])
    print("route: %d parts" % len(parts))
    return parts

def main():
    parts = build()
    ours = "".join(parts) + "\n"
    added = ours.encode()
    text = (b"op1f picture 1\nsize %d\nfrom micline.svg %d %s\nadd end %d\n"
            % (BASE_BYTES + len(added), BASE_BYTES, BASE_CRC.encode(), len(added))) + added + b"\n"
    with open(os.path.join(ROOT, "micline.svg.make"), "wb") as out:
        out.write(text)
    with open(os.path.join(ROOT, "loopback_parts.h"), "w") as out:
        out.write(header())

if __name__ == "__main__":
    main()
