#!/usr/bin/env python3
"""Sum up Tuesday 17 November 2026's world news in one image.

A front-page style picture: masthead with the date, a lead story on
Ukraine striking the Crimean Bridge again, a tanker hit by mines near
the Strait of Hormuz, Trump landing in Manila ahead of a three-way
Xi-Trump-Putin meeting, Japan scrambling jets, and Depardieu pleading
guilty in Paris, plus a ticker of the day's other stories.

Everything is drawn from scratch with the standard library only:
a tiny rasterizer, a 5x7 bitmap font, and a hand-rolled PNG encoder.
No network, no randomness, no clock: two runs write identical bytes.
"""

import math
import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font
# 5x7 bitmap font: each glyph is 7 rows of 5 bits, top row first.
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ",": (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    "-": (0, 0, 0, 0x0E, 0, 0, 0),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    ":": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0, 0x04),
    "/": (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "%": (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    "+": (0, 0x04, 0x04, 0x0E, 0x04, 0x04, 0),
    "\u2022": (0, 0x04, 0x0E, 0x0E, 0x0E, 0x04, 0),
}


def text_width(s, scale):
    return len(s) * 6 * scale


def wrap_text(s, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
PAPER = (247, 243, 234)
INK = (17, 17, 17)
GREY = (90, 86, 78)
NAVY = (22, 35, 63)
RED = (192, 57, 43)
GOLD = (214, 178, 80)


class Canvas:
    def __init__(self, w, h, color):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.rect(0, 0, w, h, color)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, int(x)), max(0, int(y))
        x1, y1 = min(self.w, int(x + w)), min(self.h, int(y + h))
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                self.px[i], self.px[i + 1], self.px[i + 2] = c
                i += 3

    def outline(self, x, y, w, h, c, t=2):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, w=1):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = x1 - x0, y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        r = max(0, w // 2)
        for i in range(steps + 1):
            t = i / steps
            cx, cy = int(round(x0 + dx * t)), int(round(y0 + dy * t))
            for yy in range(cy - r, cy + r + 1):
                for xx in range(cx - r, cx + r + 1):
                    if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r + (1 if r else 0):
                        self.set(xx, yy, c)

    def disc(self, cx, cy, r, c):
        r = int(r)
        for yy in range(cy - r, cy + r + 1):
            span = int(math.sqrt(max(0, r * r - (yy - cy) ** 2)))
            for xx in range(cx - span, cx + span + 1):
                self.set(xx, yy, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(int(cy - ry), int(cy + ry) + 1):
            t = (yy - cy) / ry if ry else 0
            span = int(rx * math.sqrt(max(0.0, 1 - t * t)))
            for xx in range(int(cx - span), int(cx + span) + 1):
                self.set(xx, yy, c)

    def poly(self, pts, c):
        """Scanline-filled polygon; pts is a list of (x, y)."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        y0, y1 = int(min(ys)), int(max(ys))
        n = len(pts)
        for yy in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                x0, ya = pts[i]
                x1, yb = pts[(i + 1) % n]
                if ya == yb:
                    continue
                if (ya <= yy < yb) or (yb <= yy < ya):
                    xs.append(x0 + (yy - ya) * (x1 - x0) / (yb - ya))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for xx in range(int(math.ceil(xs[k])), int(xs[k + 1]) + 1):
                    self.set(xx, yy, c)

    def vgrad(self, x, y, w, h, c0, c1):
        for yy in range(int(y), int(y + h)):
            t = (yy - y) / max(1, h - 1)
            c = tuple(int(round(c0[i] + (c1[i] - c0[i]) * t)) for i in range(3))
            self.rect(x, yy, w, 1, c)

    def text(self, s, x, y, scale, c, align="left"):
        s = s.upper()  # the bitmap font is capitals only
        if align == "center":
            x = x - text_width(s, scale) / 2
        elif align == "right":
            x = x - text_width(s, scale)
        x = int(round(x))
        y = int(round(y))
        cell = max(1, int(math.ceil(scale)))
        for ch in s:
            rows = FONT.get(ch, FONT["?"])
            for r in range(7):
                bits = rows[r]
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.rect(x + int(col * scale), y + int(r * scale),
                                  cell, cell, c)
            x += int(round(6 * scale))

    def wrapped(self, s, x, y, scale, c, max_width, gap=4):
        lines = wrap_text(s, scale, max_width)
        for ln in lines:
            self.text(ln, x, y, scale, c)
            y += int(round(7 * scale)) + gap
        return y

    def chip(self, s, x, y, scale, fg=(255, 255, 255), bg=NAVY):
        pad = 6
        w = int(text_width(s, scale)) + 2 * pad
        h = int(round(7 * scale)) + 2 * pad
        self.rect(x, y, w, h, bg)
        self.text(s, x + pad, y + pad, scale, fg)
        return w, h


# ---------------------------------------------------------------- scenes
def draw_bridge(cv, x, y, w, h):
    """Kerch Bridge: sea, two towers, deck with a collapsed middle span."""
    cv.vgrad(x, y, w, int(h * 0.55), (178, 210, 232), (235, 242, 247))
    sea_y = y + int(h * 0.55)
    cv.rect(x, sea_y, w, y + h - sea_y, (46, 111, 158))
    for wy, ww in ((sea_y + 18, 90), (sea_y + 42, 140), (sea_y + 66, 70)):
        cv.line(x + 40, wy, x + 40 + ww, wy, (140, 190, 220), 2)
        cv.line(x + w - 200, wy + 12, x + w - 60, wy + 12, (140, 190, 220), 2)
    deck_y = y + int(h * 0.52)
    steel = (58, 64, 72)
    # towers
    for tx in (x + int(w * 0.16), x + int(w * 0.84)):
        cv.rect(tx - 7, deck_y - 92, 14, 92, steel)
        cv.rect(tx - 34, deck_y - 92, 68, 10, steel)
        cv.line(tx, deck_y - 92, x + int(w * 0.42), deck_y, (120, 128, 138), 2)
        cv.line(tx, deck_y - 92, x + int(w * 0.58), deck_y, (120, 128, 138), 2)
    # deck: left and right spans, middle span collapsed into the water
    cv.rect(x, deck_y, int(w * 0.40), 10, steel)
    cv.rect(x + int(w * 0.60), deck_y, int(w * 0.40), 10, steel)
    cv.poly([(x + int(w * 0.40), deck_y + 10),
             (x + int(w * 0.47), deck_y + 10),
             (x + int(w * 0.55), deck_y + 58),
             (x + int(w * 0.48), deck_y + 62)], (44, 50, 58))
    cv.poly([(x + int(w * 0.60), deck_y + 10),
             (x + int(w * 0.55), deck_y + 10),
             (x + int(w * 0.55), deck_y + 58)], (44, 50, 58))
    # explosion burst at the break
    bx, by = x + int(w * 0.50), deck_y - 6
    for ang in range(0, 360, 30):
        a = math.radians(ang)
        tip = (bx + int(34 * math.cos(a)), by + int(34 * math.sin(a)))
        base1 = (bx + int(10 * math.cos(a + 0.45)), by + int(10 * math.sin(a + 0.45)))
        base2 = (bx + int(10 * math.cos(a - 0.45)), by + int(10 * math.sin(a - 0.45)))
        cv.poly([tip, base1, base2], (255, 140, 0))
    cv.disc(bx, by, 13, (255, 210, 60))
    # smoke plume
    for sx, sy, sr, sc in ((bx - 26, by - 52, 22, (120, 120, 120)),
                           (bx + 8, by - 78, 26, (140, 140, 140)),
                           (bx + 34, by - 58, 18, (100, 100, 100)),
                           (bx - 6, by - 104, 20, (160, 160, 160))):
        cv.disc(sx, sy, sr, sc)
    cv.chip("KERCH BRIDGE", x + 10, y + h - 34, 2)


def draw_tanker(cv, x, y, w, h):
    """LPG tanker ablaze near the Strait of Hormuz, with a sea mine."""
    cv.vgrad(x, y, w, int(h * 0.5), (185, 214, 233), (238, 243, 247))
    sea_y = y + int(h * 0.5)
    cv.rect(x, sea_y, w, y + h - sea_y, (38, 96, 142))
    hull_y = sea_y + int(h * 0.14)
    cv.poly([(x + int(w * 0.06), hull_y), (x + int(w * 0.94), hull_y),
             (x + int(w * 0.88), hull_y + 34), (x + int(w * 0.12), hull_y + 34)],
            (35, 42, 52))
    cv.rect(x + int(w * 0.06), hull_y + 26, int(w * 0.88), 6, (160, 40, 30))
    # spherical LPG tanks on deck
    for cx in (x + int(w * 0.22), x + int(w * 0.40), x + int(w * 0.58)):
        cv.disc(cx, hull_y - 16, 17, (235, 235, 230))
        cv.disc(cx, hull_y - 16, 17, (235, 235, 230))
    # superstructure and funnel
    cv.rect(x + int(w * 0.74), hull_y - 46, 44, 46, (240, 240, 235))
    cv.rect(x + int(w * 0.78), hull_y - 62, 20, 18, (40, 40, 40))
    cv.rect(x + int(w * 0.78), hull_y - 62, 20, 5, (192, 57, 43))
    cv.disc(x + int(w * 0.88), hull_y - 74, 10, (130, 130, 130))
    cv.disc(x + int(w * 0.80), hull_y - 88, 13, (150, 150, 150))
    # flames on deck
    for fx in (x + int(w * 0.30), x + int(w * 0.48), x + int(w * 0.64)):
        cv.poly([(fx, hull_y - 34), (fx - 12, hull_y), (fx + 12, hull_y)],
                (255, 140, 0))
        cv.poly([(fx, hull_y - 20), (fx - 6, hull_y), (fx + 6, hull_y)],
                (255, 210, 60))
    # sea mine in the foreground
    mx, my = x + int(w * 0.16), sea_y + int(h * 0.38)
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        cv.line(mx, my, mx + int(20 * math.cos(a)), my + int(20 * math.sin(a)),
                (20, 20, 20), 3)
    cv.disc(mx, my, 12, (25, 25, 25))
    cv.disc(mx - 4, my - 4, 3, (120, 120, 120))
    cv.chip("STRAIT OF HORMUZ", x + 10, y + h - 34, 2)


def draw_summit(cv, x, y, w, h):
    """Three flags over a table: Trump lands in Manila; Xi-Trump-Putin meet Thursday."""
    cv.rect(x, y, w, h, (233, 220, 196))
    cv.rect(x, y + int(h * 0.78), w, h - int(h * 0.78), (150, 120, 80))
    # table
    cv.rect(x + int(w * 0.08), y + int(h * 0.66), int(w * 0.84), int(h * 0.30),
            (96, 64, 38))
    # flags: China, USA, Russia
    flags = [
        (0.20, "china"),
        (0.50, "usa"),
        (0.80, "russia"),
    ]
    for fx, kind in flags:
        px = x + int(w * fx)
        cv.rect(px - 2, y + 8, 4, int(h * 0.58), (90, 80, 70))
        fw, fh = 52, 34
        fx0, fy0 = px - fw // 2, y + 10
        if kind == "china":
            cv.rect(fx0, fy0, fw, fh, (222, 41, 16))
            cv.disc(fx0 + 11, fy0 + 10, 4, (255, 222, 0))
            for sx, sy in ((30, 6), (38, 12), (38, 20), (30, 25)):
                cv.disc(fx0 + sx, fy0 + sy, 2, (255, 222, 0))
        elif kind == "usa":
            for i in range(7):
                cv.rect(fx0, fy0 + i * 5, fw, 5,
                        (178, 34, 52) if i % 2 == 0 else (240, 240, 240))
            cv.rect(fx0, fy0, 22, 20, (60, 60, 160))
            for sx in (5, 12, 19):
                for sy in (5, 12, 18):
                    cv.disc(fx0 + sx, fy0 + sy, 1, (255, 255, 255))
        else:
            cv.rect(fx0, fy0, fw, 12, (240, 240, 240))
            cv.rect(fx0, fy0 + 12, fw, 11, (0, 57, 166))
            cv.rect(fx0, fy0 + 23, fw, 11, (213, 0, 50))
    # three suited figures behind the table
    for fx, suit in ((0.20, (30, 40, 60)), (0.50, (60, 60, 60)),
                     (0.80, (70, 45, 30))):
        px = x + int(w * fx)
        cv.disc(px, y + int(h * 0.52), 12, (222, 184, 150))
        cv.poly([(px - 20, y + int(h * 0.66)), (px + 20, y + int(h * 0.66)),
                 (px + 13, y + int(h * 0.56)), (px - 13, y + int(h * 0.56))],
                suit)
        cv.poly([(px - 4, y + int(h * 0.57)), (px + 4, y + int(h * 0.57)),
                 (px, y + int(h * 0.66))], (192, 57, 43))
    cv.chip("MANILA", x + 10, y + h - 34, 2)


def draw_jets(cv, x, y, w, h):
    """Two jets over a rising sun: Japan scrambles fighters."""
    cv.vgrad(x, y, w, h, (168, 205, 230), (238, 244, 248))
    cv.disc(x + int(w * 0.76), y + int(h * 0.30), 32, (200, 40, 40))
    cv.ellipse(x + int(w * 0.22), y + int(h * 0.20), 46, 10, (255, 255, 255))
    cv.ellipse(x + int(w * 0.55), y + int(h * 0.72), 52, 11, (255, 255, 255))

    def jet(jx, jy, s):
        cv.poly([(jx, jy), (jx - 34 * s, jy - 6 * s), (jx - 30 * s, jy + 4 * s),
                 (jx - 12 * s, jy + 6 * s), (jx - 8 * s, jy + 16 * s),
                 (jx - 2 * s, jy + 6 * s), (jx + 26 * s, jy + 8 * s),
                 (jx + 34 * s, jy + 2 * s)], (52, 58, 66))
        cv.line(jx - 34 * s, jy, jx - 74 * s, jy - 6 * s, (255, 255, 255), 2)

    jet(x + int(w * 0.42), y + int(h * 0.42), 1.0)
    jet(x + int(w * 0.62), y + int(h * 0.62), 0.8)
    cv.chip("JAPAN", x + 10, y + h - 34, 2)


def draw_court(cv, x, y, w, h):
    """Courthouse in Paris: Depardieu pleads guilty."""
    cv.rect(x, y, w, h, (214, 208, 194))
    bx, by, bw = x + int(w * 0.14), y + int(h * 0.18), int(w * 0.72)
    cv.poly([(bx - 8, by), (bx + bw + 8, by), (bx + bw // 2, by - 22)],
            (120, 110, 96))
    cv.rect(bx, by, bw, int(h * 0.52), (238, 234, 224))
    for i in range(4):
        cx = bx + 14 + i * (bw - 28) // 3
        cv.rect(cx - 7, by + 6, 14, int(h * 0.52) - 6, (255, 255, 250))
    cv.rect(bx - 6, by + int(h * 0.52), bw + 12, 8, (120, 110, 96))
    for i in range(3):
        cv.rect(bx - 16 + i * 8, by + int(h * 0.52) + 8 + i * 7,
                bw + 32 - i * 16, 7, (150, 142, 128))
    # gavel resting at the foot of the steps
    gx, gy = x + int(w * 0.74), y + int(h * 0.86)
    cv.line(gx - 26, gy + 12, gx + 26, gy - 12, (110, 70, 35), 6)
    cv.rect(gx - 2, gy - 22, 26, 12, (140, 90, 45))
    cv.chip("PARIS", x + 10, y + h - 34, 2)


# ---------------------------------------------------------------- layout
def build():
    cv = Canvas(W, H, PAPER)
    # masthead
    cv.rect(20, 20, 984, 98, NAVY)
    cv.rect(20, 116, 984, 4, RED)
    cv.text("TUESDAY 17 NOVEMBER 2026", W // 2, 40, 6, (255, 255, 255),
            align="center")
    cv.text("THE WORLD IN ONE PICTURE", W // 2, 90, 3, GOLD, align="center")

    def panel(px, py, pw, ph):
        cv.rect(px, py, pw, ph, (255, 255, 255))
        cv.outline(px, py, pw, ph, (150, 140, 120), 2)

    # lead story: Crimea bridge
    panel(20, 138, 624, 422)
    draw_bridge(cv, 28, 146, 608, 246)
    cv.text("UKRAINE HITS CRIMEA", 36, 402, 5, INK)
    cv.text("BRIDGE AGAIN", 36, 440, 5, INK)
    cv.wrapped("Second strike in two days; road arch damaged, "
               "traffic halted. Russia hits two bridges in Kyiv.",
               36, 484, 3, GREY, 592)

    # tanker near Hormuz
    panel(664, 138, 340, 422)
    draw_tanker(cv, 672, 146, 324, 184)
    cv.text("TANKER HIT", 680, 340, 3.5, INK)
    cv.text("TWICE OFF OMAN", 680, 372, 3.5, INK)
    cv.wrapped("Crew abandons ship near Hormuz; 1 sailor "
               "missing. A third U.S. carrier reaches the region.",
               680, 406, 3, GREY, 308)

    # row two: summit, jets, court
    panel(20, 580, 320, 320)
    draw_summit(cv, 28, 588, 304, 142)
    cv.text("TRUMP LANDS", 36, 742, 3.5, INK)
    cv.text("IN MANILA", 36, 770, 3.5, INK)
    cv.wrapped("Xi, Trump and Putin to meet Thursday in Shenzhen.",
               36, 802, 3, GREY, 296)

    panel(352, 580, 320, 320)
    draw_jets(cv, 360, 588, 304, 142)
    cv.text("JETS SCRAMBLED", 368, 742, 3.5, INK)
    cv.text("OVER JAPAN", 368, 770, 3.5, INK)
    cv.wrapped("Russian planes enter airspace; Tokyo protests.",
               368, 802, 3, GREY, 296)

    panel(684, 580, 320, 320)
    draw_court(cv, 692, 588, 304, 142)
    cv.text("DEPARDIEU", 700, 742, 3.5, INK)
    cv.text("PLEADS GUILTY", 700, 770, 3.5, INK)
    cv.wrapped("French actor admits sexual assault charge in Paris.",
               700, 802, 3, GREY, 296)

    # ticker
    cv.rect(20, 920, 984, 72, NAVY)
    cv.text("ALSO TODAY:", 36, 930, 3, GOLD)
    cv.wrapped("Estonia to shut Russia border crossings. UK sanctions "
               "West Bank settlement builders. Pentagon fails audit, "
               "9th year.",
               36, 952, 2.5, (255, 255, 255), 952)
    cv.text("COMPILED FROM WORLD NEWS WIRES", W // 2, 998, 2, GREY,
            align="center")
    return cv


# ---------------------------------------------------------------- PNG
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    for yy in range(cv.h):
        raw.append(0)
        raw.extend(cv.px[yy * cv.w * 3:(yy + 1) * cv.w * 3])
    blob = b"\x89PNG\r\n\x1a\n"
    blob += _chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    blob += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    blob += _chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(blob)
    return len(blob)


def main(argv):
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(build(), path)
    print("wrote %s (%d bytes)" % (path, size))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
