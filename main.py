#!/usr/bin/env python3
"""THE WORLD TODAY - Friday, 20 November 2026, in one image.

A make.fun entry for the competition "news-image-20261120"
("Sum up 20 November's world news in one image").

The program draws a newspaper front page for Friday 20 November 2026
with pure Python standard library code: a small software rasteriser
renders the page at 2x supersampling, downsamples it, and writes a
deterministic PNG to /output/entry.png (or $MAKEFUN_OUTPUT_DIR).

The day's news, as the wires led with it on 20 November 2026:
  * Shenzhen: Trump, Xi Jinping and Putin hold the first-ever
    US-China-Russia trilateral summit at Kylin Villa and issue a
    joint "Declaration toward Peace" pledging dialogue on nuclear
    risk; Trump hails it in Washington as "momentous" (Reuters, CNN,
    AP, Fox News). No breakthrough on Ukraine.
  * Anthropic's record IPO: priced at $83, it raises about $81
    billion - the largest IPO on record - at a $1.5 trillion
    valuation; underwriters' extra shares lift the total to about
    $93.5 billion on Friday (Reuters).
  * Grand Theft Auto VI, released the day before after 13 years,
    draws rave reviews: a Metacritic score of 99, tying the all-time
    record, and about $2.4 billion of first-day sales (Reuters).
  * Spain: polls give the PP's Alberto Nunez Feijoo the win over
    Prime Minister Pedro Sanchez in their TV debate, 51-29, days
    before the election (Reuters, 20 Nov 2026).
  * Also Friday: the FTSE 100 slides in a global risk-off mood and
    India's foreign-exchange reserves dip to $705 billion (Reuters).
"""

import math
import os
import struct
import zlib

# ------------------------------------------------------------------
# Canvas: an RGB framebuffer rendered at SS x final size, then
# box-downsampled. All drawing coordinates are in final-image pixels.
# ------------------------------------------------------------------

FINAL_W = 1024
FINAL_H = 1024
SS = 2
W = FINAL_W * SS
H = FINAL_H * SS

FB = [bytearray(W * 3) for _ in range(H)]


def _clamp(v):
    return 0 if v < 0 else (255 if v > 255 else v)


def set_px(x, y, color, alpha=1.0):
    """Blend one supersampled pixel (integer supersample coords)."""
    if 0 <= x < W and 0 <= y < H:
        row = FB[y]
        i = x * 3
        if alpha >= 1.0:
            row[i] = color[0]
            row[i + 1] = color[1]
            row[i + 2] = color[2]
        else:
            ia = 1.0 - alpha
            row[i] = _clamp(int(row[i] * ia + color[0] * alpha + 0.5))
            row[i + 1] = _clamp(int(row[i + 1] * ia + color[1] * alpha + 0.5))
            row[i + 2] = _clamp(int(row[i + 2] * ia + color[2] * alpha + 0.5))


def fill_rect(x, y, w, h, color, alpha=1.0):
    x0 = int(round(x * SS))
    y0 = int(round(y * SS))
    x1 = int(round((x + w) * SS))
    y1 = int(round((y + h) * SS))
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W, x1)
    y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0:
        return
    if alpha >= 1.0:
        seg = bytes(color) * (x1 - x0)
        n = len(seg)
        for yy in range(y0, y1):
            FB[yy][x0 * 3:x0 * 3 + n] = seg
    else:
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                set_px(xx, yy, color, alpha)


def fill_circle(cx, cy, r, color, alpha=1.0):
    cx_s = cx * SS
    cy_s = cy * SS
    r_s = r * SS
    y0 = max(0, int(cy_s - r_s - 1))
    y1 = min(H - 1, int(cy_s + r_s + 1))
    for yy in range(y0, y1 + 1):
        dy = yy - cy_s
        rem = r_s * r_s - dy * dy
        if rem < 0:
            continue
        dx = math.sqrt(rem)
        x0 = max(0, int(cx_s - dx))
        x1 = min(W - 1, int(cx_s + dx))
        if alpha >= 1.0:
            seg = bytes(color) * (x1 - x0 + 1)
            FB[yy][x0 * 3:x0 * 3 + len(seg)] = seg
        else:
            for xx in range(x0, x1 + 1):
                set_px(xx, yy, color, alpha)


def fill_ellipse(cx, cy, rx, ry, color, alpha=1.0):
    cx_s = cx * SS
    cy_s = cy * SS
    rx_s = rx * SS
    ry_s = ry * SS
    y0 = max(0, int(cy_s - ry_s - 1))
    y1 = min(H - 1, int(cy_s + ry_s + 1))
    for yy in range(y0, y1 + 1):
        t = (yy - cy_s) / ry_s
        rem = 1.0 - t * t
        if rem < 0:
            continue
        dx = rx_s * math.sqrt(rem)
        x0 = max(0, int(cx_s - dx))
        x1 = min(W - 1, int(cx_s + dx))
        if alpha >= 1.0:
            seg = bytes(color) * (x1 - x0 + 1)
            FB[yy][x0 * 3:x0 * 3 + len(seg)] = seg
        else:
            for xx in range(x0, x1 + 1):
                set_px(xx, yy, color, alpha)


def fill_poly(points, color, alpha=1.0):
    """Scanline fill of a polygon given in final-image coordinates."""
    pts = [(px * SS, py * SS) for (px, py) in points]
    ys = [p[1] for p in pts]
    y0 = max(0, int(min(ys)))
    y1 = min(H - 1, int(max(ys)))
    n = len(pts)
    for yy in range(y0, y1 + 1):
        yc = yy + 0.5
        xs = []
        for i in range(n):
            xa, ya = pts[i]
            xb, yb = pts[(i + 1) % n]
            if (ya <= yc < yb) or (yb <= yc < ya):
                xs.append(xa + (yc - ya) * (xb - xa) / (yb - ya))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            x0 = max(0, int(xs[i]))
            x1 = min(W - 1, int(xs[i + 1]))
            if x1 < x0:
                continue
            if alpha >= 1.0:
                seg = bytes(color) * (x1 - x0 + 1)
                FB[yy][x0 * 3:x0 * 3 + len(seg)] = seg
            else:
                for xx in range(x0, x1 + 1):
                    set_px(xx, yy, color, alpha)


def draw_line(x0, y0, x1, y1, width, color, alpha=1.0):
    """A thick line, drawn as a quad with round caps."""
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)
    if length == 0:
        fill_circle(x0, y0, width / 2.0, color, alpha)
        return
    nx = -dy / length * width / 2.0
    ny = dx / length * width / 2.0
    fill_poly([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
               (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], color, alpha)
    fill_circle(x0, y0, width / 2.0, color, alpha)
    fill_circle(x1, y1, width / 2.0, color, alpha)


def stroke_rect(x, y, w, h, lw, color, alpha=1.0):
    fill_rect(x, y, w, lw, color, alpha)
    fill_rect(x, y + h - lw, w, lw, color, alpha)
    fill_rect(x, y, lw, h, color, alpha)
    fill_rect(x + w - lw, y, lw, h, color, alpha)


def star_points(cx, cy, r_out, r_in, rot=-math.pi / 2.0):
    pts = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        a = rot + i * math.pi / 5.0
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def fill_star(cx, cy, r_out, color, alpha=1.0):
    fill_poly(star_points(cx, cy, r_out, r_out * 0.382), color, alpha)


def v_gradient(x, y, w, h, top, bottom):
    """Vertical colour gradient over a rectangle."""
    y0 = max(0, int(round(y * SS)))
    y1 = min(H, int(round((y + h) * SS)))
    x0 = max(0, int(round(x * SS)))
    x1 = min(W, int(round((x + w) * SS)))
    span = max(1, (y + h) * SS - y * SS)
    for yy in range(y0, y1):
        t = (yy - y * SS) / span
        c = (_clamp(int(top[0] + (bottom[0] - top[0]) * t + 0.5)),
             _clamp(int(top[1] + (bottom[1] - top[1]) * t + 0.5)),
             _clamp(int(top[2] + (bottom[2] - top[2]) * t + 0.5)))
        seg = bytes(c) * (x1 - x0)
        FB[yy][x0 * 3:x0 * 3 + len(seg)] = seg


def grain(x, y, w, h, amp, base_seed=1234567):
    """Deterministic faint paper grain: a hash of the pixel position."""
    x0 = int(round(x * SS))
    y0 = int(round(y * SS))
    x1 = min(W, int(round((x + w) * SS)))
    y1 = min(H, int(round((y + h) * SS)))
    for yy in range(y0, y1):
        row = FB[yy]
        for xx in range(x0, x1):
            n = (xx * 374761393 + yy * 668265263 + base_seed) & 0xFFFFFFFF
            n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
            n = n ^ (n >> 16)
            d = (n % (2 * amp + 1)) - amp
            if d:
                i = xx * 3
                row[i] = _clamp(row[i] + d)
                row[i + 1] = _clamp(row[i + 1] + d)
                row[i + 2] = _clamp(row[i + 2] + d)


def downsample():
    """Box-downsample the supersampled framebuffer to FINAL_W x FINAL_H."""
    out = []
    for fy in range(FINAL_H):
        r0 = FB[fy * SS]
        r1 = FB[fy * SS + 1]
        row = bytearray(FINAL_W * 3)
        for fx in range(FINAL_W):
            i = fx * SS * 3
            o = fx * 3
            for ch in range(3):
                row[o + ch] = (r0[i + ch] + r0[i + 3 + ch] +
                               r1[i + ch] + r1[i + 3 + ch] + 2) // 4
        out.append(bytes(row))
    return out


def write_png(path, rows):
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    raw = b"".join(b"\x00" + r for r in rows)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", FINAL_W, FINAL_H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)

# ------------------------------------------------------------------
# A hand-drawn 7x10 bitmap font (capitals, digits, punctuation).
# Each glyph is 10 rows of 7 characters; '#' is ink.
# ------------------------------------------------------------------

FONT = {
    "A": (".#####.", "#.....#", "#.....#", "#.....#", "#######",
          "#.....#", "#.....#", "#.....#", "#.....#", "#.....#"),
    "B": ("######.", "#.....#", "#.....#", "#.....#", "######.",
          "#.....#", "#.....#", "#.....#", "#.....#", "######."),
    "C": (".#####.", "#.....#", "#......", "#......", "#......",
          "#......", "#......", "#......", "#.....#", ".#####."),
    "D": ("######.", "#.....#", "#.....#", "#.....#", "#.....#",
          "#.....#", "#.....#", "#.....#", "#.....#", "######."),
    "E": ("#######", "#......", "#......", "#......", "#####..",
          "#......", "#......", "#......", "#......", "#######"),
    "F": ("#######", "#......", "#......", "#......", "#####..",
          "#......", "#......", "#......", "#......", "#......"),
    "G": (".#####.", "#.....#", "#......", "#......", "#..####",
          "#.....#", "#.....#", "#.....#", "#.....#", ".#####."),
    "H": ("#.....#", "#.....#", "#.....#", "#.....#", "#######",
          "#.....#", "#.....#", "#.....#", "#.....#", "#.....#"),
    "I": ("#######", "...#...", "...#...", "...#...", "...#...",
          "...#...", "...#...", "...#...", "...#...", "#######"),
    "J": (".######", "......#", "......#", "......#", "......#",
          "......#", "......#", "......#", "#....#.", ".####.."),
    "K": ("#.....#", "#....#.", "#...#..", "#..#...", "###....",
          "#..#...", "#...#..", "#....#.", "#.....#", "#.....#"),
    "L": ("#......", "#......", "#......", "#......", "#......",
          "#......", "#......", "#......", "#......", "#######"),
    "M": ("#.....#", "##...##", "#.#.#.#", "#.#.#.#", "#..#..#",
          "#.....#", "#.....#", "#.....#", "#.....#", "#.....#"),
    "N": ("#.....#", "##....#", "##....#", "#.#...#", "#..#..#",
          "#...#.#", "#....##", "#....##", "#.....#", "#.....#"),
    "O": (".#####.", "#.....#", "#.....#", "#.....#", "#.....#",
          "#.....#", "#.....#", "#.....#", "#.....#", ".#####."),
    "P": ("######.", "#.....#", "#.....#", "#.....#", "######.",
          "#......", "#......", "#......", "#......", "#......"),
    "Q": (".#####.", "#.....#", "#.....#", "#.....#", "#.....#",
          "#.....#", "#.#...#", "#..#..#", ".#####.", ".....##"),
    "R": ("######.", "#.....#", "#.....#", "#.....#", "######.",
          "#..#...", "#...#..", "#....#.", "#.....#", "#.....#"),
    "S": (".######", "#......", "#......", "#......", ".#####.",
          "......#", "......#", "......#", "#.....#", ".#####."),
    "T": ("#######", "...#...", "...#...", "...#...", "...#...",
          "...#...", "...#...", "...#...", "...#...", "...#..."),
    "U": ("#.....#", "#.....#", "#.....#", "#.....#", "#.....#",
          "#.....#", "#.....#", "#.....#", "#.....#", ".#####."),
    "V": ("#.....#", "#.....#", "#.....#", "#.....#", "#.....#",
          "#.....#", "#.....#", ".#...#.", ".#...#.", "..#.#.."),
    "W": ("#.....#", "#.....#", "#.....#", "#.....#", "#..#..#",
          "#..#..#", "#.#.#.#", "#.#.#.#", "##...##", "#.....#"),
    "X": ("#.....#", "#.....#", ".#...#.", "..#.#..", "...#...",
          "...#...", "..#.#..", ".#...#.", "#.....#", "#.....#"),
    "Y": ("#.....#", "#.....#", ".#...#.", ".#...#.", "..#.#..",
          "...#...", "...#...", "...#...", "...#...", "...#..."),
    "Z": ("#######", "......#", ".....#.", "....#..", "...#...",
          "..#....", ".#.....", "#......", "#......", "#######"),
    "0": (".#####.", "#....##", "#...#.#", "#...#.#", "#..#..#",
          "#.#...#", "#.#...#", "##....#", "#.....#", ".#####."),
    "1": ("...#...", "..##...", "..#.#..", "...#...", "...#...",
          "...#...", "...#...", "...#...", "...#...", ".#####."),
    "2": (".#####.", "#.....#", "......#", ".....#.", "....#..",
          "...#...", "..#....", ".#.....", "#......", "#######"),
    "3": (".#####.", "#.....#", "......#", "......#", "..####.",
          "......#", "......#", "......#", "#.....#", ".#####."),
    "4": ("....#..", "...##..", "..#.#..", ".#..#..", "#....#.",
          "#######", ".....#.", ".....#.", ".....#.", ".....#."),
    "5": ("#######", "#......", "#......", "######.", "......#",
          "......#", "......#", "......#", "#.....#", ".#####."),
    "6": (".#####.", "#.....#", "#......", "#......", "######.",
          "#.....#", "#.....#", "#.....#", "#.....#", ".#####."),
    "7": ("#######", "......#", ".....#.", ".....#.", "....#..",
          "....#..", "...#...", "...#...", "...#...", "...#..."),
    "8": (".#####.", "#.....#", "#.....#", "#.....#", ".#####.",
          "#.....#", "#.....#", "#.....#", "#.....#", ".#####."),
    "9": (".#####.", "#.....#", "#.....#", "#.....#", "#.....#",
          ".######", "......#", "......#", "#.....#", ".#####."),
    ".": (".......", ".......", ".......", ".......", ".......",
          ".......", ".......", ".......", "..##...", "..##..."),
    ",": (".......", ".......", ".......", ".......", ".......",
          ".......", ".......", ".......", "..##...", ".##...."),
    "'": ("..##...", "..##...", ".#.....", ".......", ".......",
          ".......", ".......", ".......", ".......", "......."),
    "-": (".......", ".......", ".......", ".......", ".#####.",
          ".......", ".......", ".......", ".......", "......."),
    ":": (".......", ".......", "..##...", "..##...", ".......",
          ".......", ".......", "..##...", "..##...", "......."),
    "!": ("...#...", "...#...", "...#...", "...#...", "...#...",
          "...#...", "...#...", ".......", "...#...", "...#..."),
    "?": (".#####.", "#.....#", "......#", ".....#.", "....#..",
          "...#...", "...#...", ".......", "...#...", "...#..."),
    "$": ("...#...", ".######", "#.#....", "#.#....", ".#####.",
          "..#.#..", "..#.#..", ".#####.", "...#...", "...#..."),
    "/": ("......#", ".....#.", ".....#.", "....#..", "....#..",
          "...#...", "...#...", "..#....", "..#....", ".#....."),
    "(": ("....##.", "...#...", "..#....", "..#....", "..#....",
          "..#....", "..#....", "..#....", "...#...", "....##."),
    ")": (".##....", "...#...", "....#..", "....#..", "....#..",
          "....#..", "....#..", "....#..", "...#...", ".##...."),
    "·": (".......", ".......", ".......", ".......", "..##...",
          "..##...", ".......", ".......", ".......", "......."),
    "+": (".......", ".......", "...#...", "...#...", ".#####.",
          "...#...", "...#...", ".......", ".......", "......."),
    '"': (".#...#.", ".#...#.", ".#...#.", ".......", ".......",
          ".......", ".......", ".......", ".......", "......."),
}

GLYPH_W = 7
GLYPH_H = 10
ADVANCE = 8.6  # glyph advance in grid units, including letter spacing


def text_width(s, cap):
    """Width in final pixels of string s at cap height cap."""
    if not s:
        return 0.0
    unit = cap / GLYPH_H
    return (len(s) * ADVANCE - (ADVANCE - GLYPH_W)) * unit


def draw_text(x, y, s, cap, color, bold=False, align="left", alpha=1.0):
    """Draw string s with its top at y; cap = cap height in final px.

    align: 'left' (x is the left edge), 'center' (x is the centre) or
    'right' (x is the right edge). Returns the drawn width.
    """
    s = s.upper()
    unit = cap / GLYPH_H
    w = text_width(s, cap)
    if align == "center":
        x = x - w / 2.0
    elif align == "right":
        x = x - w
    cx = x
    for ch in s:
        glyph = FONT.get(ch)
        if glyph is not None:
            for gy, row in enumerate(glyph):
                for gx, cell in enumerate(row):
                    if cell == "#":
                        fill_rect(cx + gx * unit, y + gy * unit,
                                  unit + 0.35, unit + 0.35, color, alpha)
                        if bold:
                            fill_rect(cx + (gx + 0.55) * unit, y + gy * unit,
                                      unit + 0.35, unit + 0.35, color, alpha)
        cx += ADVANCE * unit
    return w

# ------------------------------------------------------------------
# Scene pieces: flags, a seated leader, the summit table, icons.
# ------------------------------------------------------------------

INK = (26, 24, 20)
PAPER = (246, 241, 227)
RED = (178, 34, 42)
GOLD = (176, 141, 62)
GREY = (96, 92, 84)


def flag_russia(x, y, w, h):
    band = h / 3.0
    fill_rect(x, y, w, band + 1, (238, 238, 240))
    fill_rect(x, y + band, w, band + 1, (28, 62, 152))
    fill_rect(x, y + 2 * band, w, band + 1, (204, 34, 46))


def flag_china(x, y, w, h):
    fill_rect(x, y, w, h, (222, 40, 44))
    gold = (250, 208, 60)
    fill_star(x + w * 0.20, y + h * 0.26, w * 0.085, gold)
    for dx, dy, r in ((0.335, 0.10, 0.032), (0.375, 0.22, 0.032),
                      (0.375, 0.36, 0.032), (0.335, 0.48, 0.032)):
        fill_star(x + w * dx, y + h * dy, w * r, gold)


def flag_usa(x, y, w, h):
    fill_rect(x, y, w, h, (240, 240, 240))
    stripe = h / 13.0
    for i in range(0, 13, 2):
        fill_rect(x, y + i * stripe, w, stripe + 0.6, (178, 34, 52))
    canton_w = w * 0.42
    canton_h = stripe * 7
    fill_rect(x, y, canton_w, canton_h, (40, 52, 110))
    for r in range(5):
        for c in range(6):
            fill_circle(x + canton_w * (c + 0.5) / 6.0,
                        y + canton_h * (r + 0.5) / 5.0,
                        stripe * 0.30, (245, 245, 245))


def draw_flag(kind, cx, top, w, h):
    """A flag hanging from a pole whose top is at (cx, top)."""
    pole_x = cx - w / 2.0
    fill_rect(pole_x - 3, top - 8, 6, h + 60, (58, 50, 40))
    fill_circle(pole_x, top - 12, 6, GOLD)
    x = pole_x + 3
    if kind == "russia":
        flag_russia(x, top, w, h)
    elif kind == "china":
        flag_china(x, top, w, h)
    else:
        flag_usa(x, top, w, h)
    # gentle hanging shading: two soft vertical bands
    fill_rect(x + w * 0.30, top, w * 0.16, h, (0, 0, 0), 0.07)
    fill_rect(x + w * 0.68, top, w * 0.14, h, (255, 255, 255), 0.08)
    stroke_rect(x, top, w, h, 1.6, (30, 28, 26), 0.55)


def draw_leader(cx, head_cy, skin, hair, hair_style, suit, tie):
    """A stylised seated leader: bust behind the table.

    hair_style: 'swept' (blond sweep), 'full' (black, neat) or
    'short' (pale, receding).
    """
    head_r = 41
    # shoulders / suit: a broad trapezoid from the neck down
    fill_poly([(cx - 86, head_cy + 148), (cx - 62, head_cy + 44),
               (cx - 26, head_cy + 26), (cx + 26, head_cy + 26),
               (cx + 62, head_cy + 44), (cx + 86, head_cy + 148)], suit)
    # shirt front and tie
    fill_poly([(cx - 17, head_cy + 28), (cx + 17, head_cy + 28),
               (cx, head_cy + 74)], (242, 240, 236))
    fill_poly([(cx - 6, head_cy + 34), (cx + 6, head_cy + 34),
               (cx + 8, head_cy + 96), (cx, head_cy + 110),
               (cx - 8, head_cy + 96)], tie)
    # lapels
    fill_poly([(cx - 44, head_cy + 34), (cx - 15, head_cy + 28),
               (cx - 2, head_cy + 70), (cx - 30, head_cy + 88)], suit)
    fill_poly([(cx + 44, head_cy + 34), (cx + 15, head_cy + 28),
               (cx + 2, head_cy + 70), (cx + 30, head_cy + 88)], suit)
    # neck and head
    fill_rect(cx - 13, head_cy + 14, 26, 26, skin)
    fill_circle(cx, head_cy, head_r, skin)
    # ears
    fill_circle(cx - head_r, head_cy + 4, 8, skin)
    fill_circle(cx + head_r, head_cy + 4, 8, skin)
    # hair
    if hair_style == "swept":
        fill_poly([(cx - 43, head_cy - 8), (cx - 44, head_cy - 30),
                   (cx - 30, head_cy - 44), (cx + 6, head_cy - 47),
                   (cx + 38, head_cy - 40), (cx + 45, head_cy - 24),
                   (cx + 30, head_cy - 26), (cx + 2, head_cy - 31),
                   (cx - 24, head_cy - 27), (cx - 34, head_cy - 16)], hair)
        fill_rect(cx - 44, head_cy - 26, 9, 30, hair)
    elif hair_style == "full":
        fill_poly([(cx - 43, head_cy - 6), (cx - 44, head_cy - 28),
                   (cx - 28, head_cy - 43), (cx + 24, head_cy - 44),
                   (cx + 42, head_cy - 32), (cx + 44, head_cy - 10),
                   (cx + 30, head_cy - 22), (cx - 6, head_cy - 27),
                   (cx - 30, head_cy - 20)], hair)
        fill_rect(cx - 44, head_cy - 24, 8, 24, hair)
        fill_rect(cx + 36, head_cy - 24, 8, 24, hair)
    else:  # short, receding
        fill_poly([(cx - 42, head_cy - 16), (cx - 36, head_cy - 36),
                   (cx - 14, head_cy - 44), (cx + 16, head_cy - 44),
                   (cx + 36, head_cy - 36), (cx + 42, head_cy - 16),
                   (cx + 26, head_cy - 27), (cx - 26, head_cy - 27)], hair)
        fill_rect(cx - 43, head_cy - 22, 7, 20, hair)
        fill_rect(cx + 36, head_cy - 22, 7, 20, hair)
    # face: calm, minimal, editorial
    eye = (38, 34, 32)
    fill_ellipse(cx - 16, head_cy + 1, 4.6, 3.0, eye)
    fill_ellipse(cx + 16, head_cy + 1, 4.6, 3.0, eye)
    draw_line(cx - 24, head_cy - 9, cx - 8, head_cy - 10, 2.6, eye, 0.75)
    draw_line(cx + 8, head_cy - 10, cx + 24, head_cy - 9, 2.6, eye, 0.75)
    draw_line(cx + 1, head_cy + 6, cx - 2, head_cy + 15, 2.2, (120, 84, 66), 0.8)
    draw_line(cx - 9, head_cy + 25, cx + 9, head_cy + 25, 2.8, (122, 78, 66), 0.9)


def draw_table(cx, cy):
    """The round summit table: top ellipse, rim and front apron."""
    fill_ellipse(cx, cy + 20, 452, 62, (74, 48, 30))
    fill_ellipse(cx, cy, 452, 62, (122, 82, 46))
    fill_ellipse(cx, cy - 4, 428, 54, (140, 96, 54))
    fill_ellipse(cx, cy - 6, 428, 52, (128, 86, 48))


def draw_paper(cx, cy, angle_deg):
    a = math.radians(angle_deg)
    w, h = 46.0, 32.0
    pts = []
    for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h)):
        pts.append((cx + dx * math.cos(a) - dy * math.sin(a),
                    cy + dx * math.sin(a) + dy * math.cos(a)))
    fill_poly(pts, (247, 245, 238))
    # faint ruled lines on the document
    for i in range(3):
        off = -14 + i * 11
        x0 = cx + (-34) * math.cos(a) - off * math.sin(a)
        y0 = cy + (-34) * math.sin(a) + off * math.cos(a)
        x1 = cx + 34 * math.cos(a) - off * math.sin(a)
        y1 = cy + 34 * math.sin(a) + off * math.cos(a)
        draw_line(x0, y0, x1, y1, 2.0, (150, 148, 140), 0.8)


def draw_microphone(x_base, y_base, x_top, y_top):
    draw_line(x_base, y_base, x_top, y_top, 4.5, (30, 30, 34))
    fill_ellipse(x_top, y_top - 4, 8, 11, (24, 24, 28))


def draw_name_plate(cx, cy, name):
    w = 176
    fill_rect(cx - w / 2, cy, w, 34, (240, 233, 214))
    stroke_rect(cx - w / 2, cy, w, 34, 2, (120, 104, 74))
    draw_text(cx, cy + 8, name, 17, (40, 36, 30), bold=True, align="center")


def icon_chart(x, y):
    """A rising market chart in a small box."""
    stroke_rect(x, y, 44, 34, 3, INK)
    draw_line(x + 6, y + 26, x + 16, y + 17, 3.4, RED)
    draw_line(x + 16, y + 17, x + 24, y + 21, 3.4, RED)
    draw_line(x + 24, y + 21, x + 36, y + 8, 3.4, RED)
    fill_poly([(x + 36, y + 8), (x + 29, y + 9), (x + 35, y + 15)], RED)


def icon_palm(x, y):
    """A palm tree over a sun: Vice City shorthand."""
    fill_circle(x + 33, y + 9, 8, GOLD)
    draw_line(x + 12, y + 34, x + 15, y + 12, 4.5, (90, 70, 44))
    for a_deg, ln in ((-168, 17), (-128, 19), (-88, 18), (-48, 19), (-12, 16)):
        a = math.radians(a_deg)
        draw_line(x + 15, y + 12, x + 15 + ln * math.cos(a),
                  y + 12 + ln * math.sin(a), 3.6, (46, 110, 62))


def icon_podiums(x, y):
    """Two debate podiums facing off."""
    for px, col in ((x + 4, RED), (x + 26, (36, 62, 120))):
        fill_rect(px, y + 12, 14, 22, col)
        fill_poly([(px - 2, y + 12), (px + 16, y + 12), (px + 13, y + 4),
                   (px + 1, y + 4)], col)
        fill_circle(px + 7, y - 1, 4.5, (238, 200, 168))

# ------------------------------------------------------------------
# The front page itself.
# ------------------------------------------------------------------

def ring(cx, cy, r, width, color, alpha):
    steps = 72
    for i in range(steps):
        a0 = 2 * math.pi * i / steps
        a1 = 2 * math.pi * (i + 1) / steps
        draw_line(cx + r * math.cos(a0), cy + r * math.sin(a0),
                  cx + r * math.cos(a1), cy + r * math.sin(a1),
                  width, color, alpha)


def story_column(x, kicker, head1, head2, body1, body2, icon):
    icon(x + 252, 838)
    draw_text(x, 842, kicker, 14, RED, bold=True)
    draw_text(x, 864, head1, 22, INK, bold=True)
    draw_text(x, 890, head2, 22, INK, bold=True)
    draw_text(x, 922, body1, 13.5, (52, 49, 44))
    draw_text(x, 939, body2, 13.5, (52, 49, 44))


def draw_front_page():
    # paper
    fill_rect(0, 0, FINAL_W, FINAL_H, PAPER)
    grain(0, 0, FINAL_W, FINAL_H, 3)

    # page borders: one heavy rule, one hairline
    stroke_rect(14, 14, FINAL_W - 28, FINAL_H - 28, 3, INK)
    stroke_rect(22, 22, FINAL_W - 44, FINAL_H - 44, 1.2, INK)

    # masthead
    draw_text(512, 40, "THE WORLD TODAY", 56, INK, bold=True, align="center")
    fill_rect(40, 114, 944, 5, INK)
    fill_rect(40, 125, 944, 1.6, INK)

    # dateline: the day, named in full
    draw_text(40, 138, "VOL. I - No. 324", 13, GREY)
    draw_text(512, 134, "FRIDAY · 20 NOVEMBER 2026", 21, INK,
              bold=True, align="center")
    draw_text(984, 138, "ONE IMAGE, ONE DAY", 13, GREY, align="right")
    fill_rect(40, 166, 944, 1.6, INK)

    # the day's main headline
    draw_text(512, 182, "THREE POWERS,", 80, INK, bold=True, align="center")
    draw_text(512, 270, "ONE TABLE", 80, INK, bold=True, align="center")

    # standfirst
    draw_text(512, 366, "TRUMP, XI AND PUTIN HOLD THE FIRST-EVER", 19,
              INK, align="center")
    draw_text(512, 394, "US-CHINA-RUSSIA SUMMIT AT SHENZHEN, CHINA", 19,
              INK, align="center")
    draw_text(512, 422, "'DECLARATION TOWARD PEACE' PLEDGES NUCLEAR-RISK TALKS",
              17, RED, bold=True, align="center")

    # ---- the picture: Kylin Villa, Shenzhen ----
    px, py, pw, ph = 40, 452, 944, 340
    v_gradient(px, py, pw, ph, (46, 60, 84), (22, 30, 48))
    ring(512, 600, 158, 3, GOLD, 0.45)
    ring(512, 600, 147, 1.6, GOLD, 0.35)

    draw_flag("russia", 250, 482, 190, 114)
    draw_flag("china", 512, 470, 212, 127)
    draw_flag("usa", 774, 482, 190, 114)

    # Putin (left), Xi Jinping (centre), Trump (right)
    draw_leader(250, 632, (233, 199, 176), (198, 180, 152), "short",
                (54, 56, 64), (30, 44, 88))
    draw_leader(512, 628, (238, 206, 172), (28, 26, 28), "full",
                (30, 34, 48), RED)
    draw_leader(774, 632, (241, 198, 158), (228, 188, 94), "swept",
                (34, 44, 76), RED)

    draw_table(512, 730)
    draw_paper(250, 712, -8)
    draw_paper(512, 706, 4)
    draw_paper(774, 712, 9)
    draw_microphone(214, 736, 244, 690)
    draw_microphone(480, 738, 504, 690)
    draw_microphone(744, 736, 760, 690)
    draw_name_plate(250, 748, "PUTIN")
    draw_name_plate(512, 748, "XI JINPING")
    draw_name_plate(774, 748, "TRUMP")

    # crop the scene at the frame: repaint the paper the table's
    # front apron spilled onto, so the picture ends at its border
    fill_rect(px, py + ph, pw, 42, PAPER)
    grain(px, py + ph, pw, 42, 3)

    stroke_rect(px, py, pw, ph, 3, INK)
    stroke_rect(px + 6, py + 6, pw - 12, ph - 12, 1.4, GOLD, 0.75)

    # photo caption
    draw_text(512, 802, "KYLIN VILLA, SHENZHEN - PUTIN, XI AND TRUMP AROUND ONE TABLE",
              15.5, (70, 66, 60), align="center")
    fill_rect(40, 830, 944, 1.6, INK, 0.55)

    # ---- three more of the day's stories ----
    fill_rect(346, 842, 1.6, 106, INK, 0.55)
    fill_rect(668, 842, 1.6, 106, INK, 0.55)
    story_column(40, "TECH - MARKETS", "BIGGEST IPO", "IN HISTORY",
                 "ANTHROPIC RAISES $81BN AT", "A $1.5 TRILLION VALUATION",
                 icon_chart)
    story_column(362, "CULTURE - GAMES", "GTA VI SCORES", "99 OUT OF 100",
                 "RAVE REVIEWS AND $2.4BN", "OF FIRST-DAY SALES",
                 icon_palm)
    story_column(684, "EUROPE - POLITICS", "FEIJOO WINS", "SPAIN TV DUEL",
                 "POLLS: 51-29 OVER PM", "SANCHEZ BEFORE ELECTION",
                 icon_podiums)

    # ---- ticker of the rest of the day ----
    fill_rect(40, 960, 944, 34, INK)
    draw_text(512, 970,
              "ALSO FRIDAY: FTSE 100 SLIDES IN GLOBAL RISK-OFF · INDIA FX RESERVES DIP TO $705BN",
              13, PAPER, bold=True, align="center")


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    draw_front_page()
    rows = downsample()
    path = os.path.join(out_dir, "entry.png")
    size = write_png(path, rows)
    print("wrote %s (%d bytes, %dx%d)" % (path, size, FINAL_W, FINAL_H))


if __name__ == "__main__":
    main()
