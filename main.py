#!/usr/bin/env python3
"""
THE WORLD DAILY -- front page of Thursday, 19 November 2026.

A make.fun bounty entry ("Sum up 19 November's world news in one image").

Pure Python 3 standard library. No fonts, no images, no network: every
glyph, rule and pictogram is plotted pixel by pixel into an RGB
framebuffer and encoded as a PNG with our own chunk writer.

Output: /output/entry.png  (override location with env var OUT).
Deterministic: same input, same bytes, every run.
"""

import math
import os
import struct
import zlib

W = H = 1024

# Fixed palette
PAPER = (244, 238, 218)   # cream newsprint
INK = (28, 26, 22)        # near-black ink
CRIMSON = (179, 43, 43)   # accent red
BLUE = (47, 74, 107)      # muted editorial blue

_buf = bytearray(W * H * 3)


# --------------------------------------------------------------------------
# Primitives
# --------------------------------------------------------------------------

def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        _buf[i] = c[0]
        _buf[i + 1] = c[1]
        _buf[i + 2] = c[2]


def rect(x, y, w, h, c):
    x0 = max(x, 0)
    y0 = max(y, 0)
    x1 = min(x + w, W)
    y1 = min(y + h, H)
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        for _ in range(x0, x1):
            _buf[i] = c[0]
            _buf[i + 1] = c[1]
            _buf[i + 2] = c[2]
            i += 3


def outline_rect(x, y, w, h, c, t=1):
    rect(x, y, w, t, c)
    rect(x, y + h - t, w, t, c)
    rect(x, y, t, h, c)
    rect(x + w - t, y, t, h, c)


def line(x0, y0, x1, y1, c, t=1):
    """Bresenham line with square-stamp thickness."""
    o = (t - 1) // 2
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        rect(x0 - o, y0 - o, t, t, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def disc(cx, cy, r, c):
    r2 = r * r
    for dy in range(-r, r + 1):
        hw = int(math.sqrt(r2 - dy * dy))
        rect(cx - hw, cy + dy, 2 * hw + 1, 1, c)


def half_disc_down(cx, cy, r, c):
    r2 = r * r
    for dy in range(0, r + 1):
        hw = int(math.sqrt(r2 - dy * dy))
        rect(cx - hw, cy + dy, 2 * hw + 1, 1, c)


def ring(cx, cy, r, c, t=1):
    n = max(48, int(6.3 * r))
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        x = int(round(cx + r * math.cos(a)))
        y = int(round(cy + r * math.sin(a)))
        rect(x - (t - 1) // 2, y - (t - 1) // 2, t, t, c)


def arc(cx, cy, r, a0, a1, c, t=1):
    n = max(24, int(abs(a1 - a0) * r * 1.5))
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        x = int(round(cx + r * math.cos(a)))
        y = int(round(cy + r * math.sin(a)))
        rect(x - (t - 1) // 2, y - (t - 1) // 2, t, t, c)


def ellipse_ring(cx, cy, rx, ry, rot, c, t=1):
    n = 240
    cr = math.cos(rot)
    sr = math.sin(rot)
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        ex = rx * math.cos(a)
        ey = ry * math.sin(a)
        x = int(round(cx + ex * cr - ey * sr))
        y = int(round(cy + ex * sr + ey * cr))
        rect(x, y, t, t, c)


# --------------------------------------------------------------------------
# Embedded 5x7 pixel font (hand-drawn glyph table)
# --------------------------------------------------------------------------

FONT = {
    " ": ["00000"] * 7,
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10011", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["01110", "10001", "00001", "00110", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    ",": ["00000", "00000", "00000", "00000", "00110", "00110", "00100"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    "'": ["01100", "01100", "00100", "00000", "00000", "00000", "00000"],
    '"': ["11011", "11011", "00000", "00000", "00000", "00000", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "&": ["01100", "10010", "10010", "01100", "10101", "10010", "01101"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "%": ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    ";": ["00000", "01100", "01100", "00000", "00110", "00110", "00100"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "?": ["01110", "10001", "00001", "00010", "00100", "00000", "00100"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "*": ["00000", "00100", "10101", "01110", "10101", "00100", "00000"],
    "$": ["00100", "01111", "10100", "01110", "00101", "11110", "00100"],
}


def draw_text(x, y, s, scale, c):
    for ch in s:
        g = FONT.get(ch, FONT[" "])
        for ry in range(7):
            row = g[ry]
            for rx in range(5):
                if row[rx] == "1":
                    rect(x + rx * scale, y + ry * scale, scale, scale, c)
        x += 6 * scale


def text_w(s, scale):
    return len(s) * 6 * scale - scale


def center_text(y, s, scale, c):
    draw_text((W - text_w(s, scale)) // 2, y, s, scale, c)


def right_text(x_right, y, s, scale, c):
    draw_text(x_right - text_w(s, scale), y, s, scale, c)


# --------------------------------------------------------------------------
# Pictograms (drawn from primitives)
# --------------------------------------------------------------------------

def star(cx, cy, r, c, t=2):
    line(cx - r, cy, cx + r, cy, c, t)
    line(cx, cy - r, cx, cy + r, c, t)
    d = int(r * 0.72)
    line(cx - d, cy - d, cx + d, cy + d, c, t)
    line(cx - d, cy + d, cx + d, cy - d, c, t)


def pico_scales(x, y):
    """Scales of justice (ICJ ruling)."""
    cx = x + 22
    rect(cx - 2, y + 8, 4, 32, INK)          # post
    rect(x + 4, y + 8, 36, 2, INK)           # beam
    disc(cx, y + 7, 3, INK)                  # finial
    rect(x + 12, y + 40, 20, 3, INK)         # base
    rect(x + 16, y + 36, 12, 4, INK)
    vline_from = y + 10
    for px_ in (x + 7, x + 37):
        rect(px_, vline_from, 1, 14, INK)    # strings
        half_disc_down(px_, y + 24, 6, INK)  # pans


def pico_tank(x, y):
    """Tanks crossing the Gaza 'yellow line'."""
    for i in range(0, 44, 8):
        rect(x + i, y + 33, 5, 2, CRIMSON)   # the line
    rect(x + 8, y + 23, 28, 7, INK)          # hull
    rect(x + 16, y + 15, 13, 8, INK)         # turret
    rect(x + 29, y + 17, 13, 2, INK)         # barrel
    for wx in (x + 12, x + 18, x + 24, x + 30, x + 36):
        disc(wx, y + 31, 2, INK)             # wheels


def pico_bridge(x, y):
    """Suspension bridge under attack (Kerch)."""
    rect(x + 2, y + 34, 40, 3, INK)          # deck
    rect(x + 9, y + 8, 3, 27, INK)           # tower L
    rect(x + 32, y + 8, 3, 27, INK)          # tower R
    rect(x + 7, y + 6, 7, 2, INK)
    rect(x + 30, y + 6, 7, 2, INK)
    x0, x1 = x + 11, x + 32
    sag = 18.0
    cable = {}
    for i in range(0, 22):
        t = i / 21
        xx = x0 + int(round(t * (x1 - x0)))
        yy = y + 10 + int(round(sag * 4 * t * (1 - t)))
        cable[xx] = yy
        rect(xx, yy, 1, 1, INK)
    line(x + 2, y + 34, x + 10, y + 9, INK, 1)   # side cables
    line(x + 42, y + 34, x + 33, y + 9, INK, 1)
    for xx in range(x + 13, x + 32, 4):
        if xx in cable:
            rect(xx, cable[xx], 1, y + 34 - cable[xx], INK)  # hangers


def pico_stock(x, y):
    """Rising market (Anthropic debut)."""
    rect(x + 6, y + 4, 2, 36, BLUE)          # y axis
    rect(x + 6, y + 38, 36, 2, BLUE)         # x axis
    pts = [(x + 10, y + 34), (x + 17, y + 26), (x + 22, y + 30), (x + 34, y + 12)]
    for i in range(len(pts) - 1):
        line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], CRIMSON, 2)
    line(x + 34, y + 12, x + 25, y + 11, CRIMSON, 2)
    line(x + 34, y + 12, x + 32, y + 21, CRIMSON, 2)


def pico_tower(x, y):
    """Skyscraper under attack (Riyadh)."""
    line(x + 14, y + 42, x + 21, y + 6, INK, 2)
    line(x + 30, y + 42, x + 23, y + 6, INK, 2)
    rect(x + 21, y + 3, 6, 3, INK)
    rect(x + 12, y + 41, 20, 3, INK)
    for wy in range(10, 40, 5):
        t = (42 - wy) / 36.0
        lx = x + 14 + int(round(t * 7))
        rx = x + 30 - int(round(t * 7))
        rect(lx, y + wy, rx - lx, 1, INK)
    bx, by = x + 27, y + 18
    disc(bx, by, 2, CRIMSON)
    line(bx, by, bx + 7, by - 4, CRIMSON, 1)
    line(bx, by, bx + 8, by + 1, CRIMSON, 1)
    line(bx, by, bx + 5, by + 6, CRIMSON, 1)
    line(bx, by, bx - 3, by + 8, CRIMSON, 1)


def pico_baseball(x, y):
    cx, cy = x + 22, y + 22
    ring(cx, cy, 15, INK, 2)
    arc(cx - 20, cy, 22, -0.55, 0.55, INK, 1)
    arc(cx + 20, cy, 22, math.pi - 0.55, math.pi + 0.55, INK, 1)


def pico_football(x, y):
    cx, cy = x + 22, y + 22
    ring(cx, cy, 15, INK, 2)
    verts = []
    for k in range(5):
        a = -math.pi / 2 + k * 2 * math.pi / 5
        verts.append((cx + 6 * math.cos(a), cy + 6 * math.sin(a)))
    for k in range(5):
        x0, y0 = verts[k]
        x1, y1 = verts[(k + 1) % 5]
        line(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)), INK, 1)
        a = -math.pi / 2 + k * 2 * math.pi / 5
        line(int(round(x0)), int(round(y0)),
             int(round(cx + 14 * math.cos(a))), int(round(cy + 14 * math.sin(a))), INK, 1)


def pico_chip(x, y):
    outline_rect(x + 8, y + 8, 28, 28, INK, 2)
    outline_rect(x + 17, y + 17, 10, 10, INK, 1)
    for i in range(4):
        p_ = x + 11 + i * 6
        rect(p_, y + 2, 2, 6, INK)
        rect(p_, y + 36, 2, 6, INK)
        rect(x + 2, p_, 6, 2, INK)
        rect(x + 36, p_, 6, 2, INK)
    disc(x + 22, y + 22, 2, CRIMSON)


def pico_atom(x, y):
    cx, cy = x + 22, y + 22
    disc(cx, cy, 3, CRIMSON)
    ellipse_ring(cx, cy, 16, 6, 0.0, INK, 1)
    ellipse_ring(cx, cy, 16, 6, 1.0472, INK, 1)
    ellipse_ring(cx, cy, 16, 6, -1.0472, INK, 1)
    disc(x + 28, y + 28, 2, CRIMSON)
    disc(x + 30, y + 36, 2, CRIMSON)
    disc(x + 14, y + 8, 2, CRIMSON)


def pico_summit(x, y):
    """Round-table summit: three stars over three leaders at a table."""
    cx = x + 66
    for sx in (cx - 38, cx, cx + 38):
        star(sx, y + 18, 10, CRIMSON, 2)
    for hx in (cx - 38, cx, cx + 38):
        disc(hx, y + 62, 6, INK)             # heads
        rect(hx - 10, y + 70, 20, 16, INK)   # shoulders
    ellipse_ring(cx, y + 100, 52, 13, 0.0, INK, 2)  # round table


def pico_hippo(x, y, c, bg):
    """Fiona the hippo, in silhouette, for the ticker strip."""
    rect(x + 2, y + 8, 26, 14, c)
    disc(x + 9, y + 15, 7, c)
    disc(x + 21, y + 15, 7, c)
    for lx in (x + 4, x + 11, x + 18, x + 24):
        rect(lx, y + 18, 5, 9, c)
    disc(x + 31, y + 12, 7, c)
    rect(x + 33, y + 8, 12, 10, c)
    disc(x + 44, y + 13, 5, c)
    rect(x + 27, y + 2, 4, 5, c)
    rect(x + 40, y + 10, 2, 2, bg)
    rect(x + 45, y + 10, 2, 2, bg)
    rect(x + 31, y + 6, 2, 2, bg)


# --------------------------------------------------------------------------
# Page layout
# --------------------------------------------------------------------------

def card(x, y, kicker, head_lines, dek_lines, pico):
    outline_rect(x, y, 320, 170, INK, 1)
    draw_text(x + 12, y + 12, kicker, 1, CRIMSON)
    rect(x + 12, y + 22, text_w(kicker, 1), 2, CRIMSON)
    pico(x + 12, y + 32)
    yy = y + 34
    for ln in head_lines:
        draw_text(x + 66, yy, ln, 2, INK)
        yy += 15
    yy = y + 94
    for ln in dek_lines:
        draw_text(x + 12, yy, ln, 1, BLUE)
        yy += 11


def build():
    rect(0, 0, W, H, PAPER)

    # ---- Masthead -------------------------------------------------------
    rect(24, 14, 976, 1, INK)
    draw_text(24, 22, "VOL. LXXXII - NO. 323", 1, INK)
    right_text(1000, 22, "( PRICE: ONE IMAGE )", 1, INK)
    center_text(40, "THE WORLD DAILY", 7, INK)
    center_text(100, "THURSDAY, 19 NOVEMBER 2026", 3, CRIMSON)
    rect(24, 132, 976, 2, INK)
    rect(24, 137, 976, 1, INK)

    # ---- Lead story -----------------------------------------------------
    draw_text(24, 148, "LEAD STORY: THE SHENZHEN SUMMIT", 2, CRIMSON)
    draw_text(24, 170, "TRUMP, XI & PUTIN HOLD FIRST-EVER", 3, INK)
    draw_text(24, 192, "TRILATERAL SUMMIT IN SHENZHEN", 3, INK)
    draw_text(24, 224, "THE THREE LEADERS SIGN A FOUR-POINT 'DECLARATION TOWARDS PEACE' -", 2, INK)
    draw_text(24, 240, "BERLIN WARNS A 'YALTA FORMAT' WILL NOT BRING PEACE.", 2, INK)
    draw_text(24, 266, "FOUR POINTS: UN REFORM + LOWER NUCLEAR RISK + MORE REFINED OIL + ICC LIMITS", 1, BLUE)
    rect(854, 148, 2, 130, INK)
    pico_summit(866, 148)
    rect(24, 290, 976, 2, INK)
    rect(24, 295, 976, 1, INK)

    # ---- Story cards (3 x 3) --------------------------------------------
    cards = [
        ("COURT",
         ["WORLD COURT: MYANMAR", "GUILTY OF GENOCIDE"],
         ["FIRST-EVER GENOCIDE RULING BY THE WORLD", "COURT, OVER THE ROHINGYA PEOPLE."],
         pico_scales),
        ("WORLD",
         ["ISRAEL PUSHES PAST", "GAZA 'YELLOW LINE'"],
         ["TANKS SEIZE TWO-THIRDS OF GAZA; THOUSANDS", "FLEE. DR. ABU SAFIYA HELD LONGER."],
         pico_tank),
        ("WORLD",
         ["KERCH BRIDGE HIT", "FOR A THIRD TIME"],
         ["RAIL TRAFFIC HALTED ON THE CRIMEA LINK;", "PUTIN VOWS A 'PAINFUL' RESPONSE."],
         pico_bridge),
        ("BUSINESS",
         ["ANTHROPIC SOARS 17%", "IN NASDAQ DEBUT"],
         ["CLOSES AT $97.17 ON A VALUE NEAR $2", "TRILLION, TOPPING SPACEX'S JUNE LISTING."],
         pico_stock),
        ("MIDEAST",
         ["DRONE HITS RIYADH'S", "TALLEST TOWER"],
         ["HOUTHI ATTACK HIT THE TOWER HOUSING", "SAUDI ARABIA'S SOVEREIGN-WEALTH FUND."],
         pico_tower),
        ("US",
         ["TRUMP PARDONS", "BASEBALL LEGEND", "PETE ROSE"],
         ["THE POSTHUMOUS PARDON LIFTS HIS", "LIFETIME BAN FOR BETTING."],
         pico_baseball),
        ("SPORT",
         ["LYON 2-0 ARSENAL", "IN THE WOMEN'S", "CHAMPIONS LEAGUE"],
         ["THE FRENCH SIDE WIN 2-0 IN THE WOMEN'S", "CHAMPIONS LEAGUE MEETING."],
         pico_football),
        ("TECH",
         ["CALIFORNIA PROBES", "NVIDIA OVER CHINA", "AI CHIPS"],
         ["STATE OFFICIALS OPEN AN INQUIRY INTO", "AI CHIPS SOLD INTO CHINA."],
         pico_chip),
        ("SCIENCE",
         ["GOOGLE'S 105-QUBIT", "GAME YOU CANNOT WIN"],
         ["RESEARCHERS SHOW QUANTUM CONTEXTUALITY", "ON A 105-QUBIT PROCESSOR."],
         pico_atom),
    ]
    xs = (24, 352, 680)
    ys = (306, 486, 666)
    for i, (k, hl, dl, p) in enumerate(cards):
        card(xs[i % 3], ys[i // 3], k, hl, dl, p)

    # ---- Footer ticker --------------------------------------------------
    rect(24, 848, 976, 2, INK)
    rect(24, 858, 976, 54, INK)
    pico_hippo(36, 870, PAPER, INK)
    draw_text(96, 881,
              "TAKAICHI MEETS PUTIN * ALBANESE TOLD PUTIN AT APEC TO END THE WAR "
              "* FIONA, THE SOCIAL-MEDIA HIPPO, DIES * HASINA'S RETURN DEEPENS BANGLADESH CRISIS",
              1, PAPER)

    # ---- Folio ----------------------------------------------------------
    center_text(924, "PAGE 01 - THE WORLD DAILY - THURSDAY, 19 NOVEMBER 2026", 1, INK)
    rect(24, 940, 976, 2, INK)
    rect(24, 945, 976, 1, INK)


# --------------------------------------------------------------------------
# PNG encoder (signature + IHDR + IDAT + IEND, CRC-32 per chunk)
# --------------------------------------------------------------------------

def write_png(path, w, h, buf):
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    stride = w * 3
    raw = bytearray()
    for y in range(h):
        raw.append(0)  # filter type 0 (None)
        raw += buf[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    png = sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    build()
    out = os.environ.get("OUT") or "/output/entry.png"
    d = os.path.dirname(out)
    if d:
        os.makedirs(d, exist_ok=True)
    n = write_png(out, W, H, _buf)
    print("wrote %s (%d bytes, %dx%d)" % (out, n, W, H))


if __name__ == "__main__":
    main()
