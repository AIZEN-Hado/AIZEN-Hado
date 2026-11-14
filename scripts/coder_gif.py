#!/usr/bin/env python3
"""Render assets/coder.gif: a pixel-art coder at a desk, floating in space. Needs Pillow.

    python3 scripts/coder_gif.py assets/coder.gif

Everything is drawn procedurally on a small grid, then scaled up with hard edges. The loop is
48 frames; every moving part (typing, code, steam, tail, particles) repeats exactly within it.
"""
import math
import random
import sys

from PIL import Image, ImageDraw

LW, LH, SCALE, FRAMES = 250, 92, 4, 48
BG = (3, 4, 5)

# palette
WHITE, GREY, DIM = (232, 236, 245), (92, 98, 116), (40, 44, 56)
YELLOW, PINK, SKY, AQUA, VIOLET, LIME, ORANGE = ((254, 228, 64), (241, 91, 181), (0, 187, 249), (0, 245, 212),
                                                 (155, 93, 229), (184, 243, 90), (255, 123, 57))
DEEP_V, DARK_V = (44, 24, 78), (86, 48, 140)
DESK, DESK_HI = (30, 33, 46), (58, 63, 84)
CHAIR, CHAIR_HI = (22, 24, 34), (44, 48, 66)
HOOD, HOOD_SH = (40, 32, 74), (26, 21, 48)
SKIN, SKIN_SH, HAIR = (232, 182, 150), (186, 136, 112), (18, 14, 22)
PANTS, SHOE = (24, 26, 38), (226, 228, 236)
BEZEL, SCREEN = (52, 56, 74), (8, 12, 22)
GLOW1, GLOW2 = (0, 34, 42), (0, 58, 66)
STEAM = (118, 124, 142)
CAT, CAT_HI, CAT_ST = (255, 123, 57), (255, 190, 120), (196, 82, 36)
POT, LEAF, LEAF_D = VIOLET, LIME, (88, 140, 40)
WARM = (70, 60, 18)
CODE_COLORS = [YELLOW, PINK, SKY, AQUA, VIOLET, WHITE, WHITE, GREY, GREY]


def frame(t):
    im = Image.new("RGB", (LW, LH), BG)
    d = ImageDraw.Draw(im)
    px = im.putpixel

    def rect(x0, y0, x1, y1, c):
        d.rectangle([x0, y0, x1, y1], fill=c)

    def put(x, y, c):
        if 0 <= x < LW and 0 <= y < LH:
            px((x, y), c)

    # ------------------------------------------------------------- space
    rng = random.Random(3)
    for i in range(70):
        x, y = rng.randrange(LW), rng.randrange(LH - 10)
        phase = rng.randrange(FRAMES)
        lit = (t + phase) % 24 < 18
        put(x, y, WHITE if (lit and i % 5 == 0) else (GREY if lit else DIM))
    # shooting star, crosses once per loop
    if 6 <= t < 20:
        k = t - 6
        for j in range(7):
            put(150 + k * 6 - j, 4 + k * 2 - j // 3, WHITE if j < 2 else GREY)

    # planet with a ring, far left
    pcx, pcy, pr = 46, 38, 19
    for y in range(pcy - pr, pcy + pr + 1):
        for x in range(pcx - pr, pcx + pr + 1):
            dx, dy = x - pcx, y - pcy
            if dx * dx + dy * dy > pr * pr:
                continue
            light = (-dx * .6 - dy * .5) / pr                    # light from upper left
            band = math.sin((dy + dx * .25) * .55)
            v = light + band * .25
            c = PINK if v > .45 else VIOLET if v > .05 else DARK_V if v > -.35 else DEEP_V
            if v > .45 and (x + y) % 2 and v < .55:
                c = VIOLET
            put(x, y, c)

    def ring(front):
        for a in range(0, 360, 2):
            r = math.radians(a)
            x = pcx + math.cos(r) * 31
            y = pcy + math.sin(r) * 7 - math.cos(r) * 3
            is_front = math.sin(r) > 0
            if is_front != front:
                continue
            inside = (x - pcx) ** 2 + (y - pcy) ** 2 < pr * pr
            if not front and inside:
                continue
            spark = (a // 2 + t * 2) % 45 == 0
            put(round(x), round(y), WHITE if spark else (AQUA if a % 6 else SKY))
    ring(False)
    ring(True)
    put(78, 18, WHITE); put(77, 18, GREY); put(79, 18, GREY)   # small moon
    put(78, 17, GREY); put(78, 19, GREY)

    # ------------------------------------------------------------- glow around the monitor
    sx0, sy0, sx1, sy1 = 152, 26, 197, 53
    for y in range(sy0 - 14, sy1 + 16):
        for x in range(sx0 - 16, sx1 + 18):
            dx = max(sx0 - x, 0, x - sx1)
            dy = max(sy0 - y, 0, y - sy1)
            dist = math.hypot(dx, dy)
            if 0 < dist < 15 and im.getpixel((x, y)) == BG:
                if dist < 4 and (x + y) % 2 == 0:
                    put(x, y, GLOW2)
                elif dist < 11 and (x * 3 + y) % 6 == 0:
                    put(x, y, GLOW1)

    # ------------------------------------------------------------- floor and desk
    for x in range(96, 246):
        if x % 2 == 0:
            put(x, 84, DIM)
    rect(138, 60, 246, 61, DESK_HI)
    rect(138, 62, 246, 62, DESK)
    rect(141, 63, 142, 83, DESK)
    rect(242, 63, 243, 83, DESK)
    for x in range(146, 200):                                   # screen light on the desk
        if (x + t // 4) % 3 == 0:
            put(x, 60, (60, 96, 110))

    # monitor
    rect(sx0 - 1, sy0 - 1, sx1 + 1, sy1 + 1, BEZEL)
    rect(sx0, sy0, sx1, sy1, SCREEN)
    rect(173, sy1 + 2, 176, 58, BEZEL)
    rect(166, 59, 183, 59, BEZEL)
    # code: a new line every 12 frames, the last line types itself
    crng = random.Random(11)
    lines = []
    for _ in range(64):
        indent = crng.choice([0, 0, 3, 3, 6, 9])
        toks, x = [], indent
        for _ in range(crng.randint(1, 5)):
            w = crng.choice([2, 3, 4, 5, 6, 8])
            if x + w > 40:
                break
            toks.append((x, w, crng.choice(CODE_COLORS)))
            x += w + 1
        lines.append(toks)
    step = t // 12
    typed = (t % 12) / 11
    rows = 8
    for r in range(rows):
        idx = step + r
        toks = lines[idx % len(lines)]
        y = sy0 + 2 + r * 3
        last = r == rows - 1
        limit = None
        if last:
            span = max((a + w for a, w, _ in toks), default=0)
            limit = round(span * typed)
        for a, w, c in toks:
            for k in range(w):
                if limit is not None and a + k >= limit:
                    break
                put(sx0 + 2 + a + k, y, c)
        if last and (t // 3) % 2 == 0:
            put(sx0 + 2 + (limit or 0), y, YELLOW)
            put(sx0 + 2 + (limit or 0), y - 1, YELLOW)

    # particles of light rising off the screen
    prng = random.Random(5)
    for i in range(14):
        x = prng.randrange(sx0 + 2, sx1 - 1)
        off = prng.randrange(FRAMES)
        y = sy0 - 2 - ((t + off) % FRAMES) // 2
        c = prng.choice([AQUA, SKY, PINK, YELLOW, VIOLET])
        if y > 2:
            put(x, y, c)

    # keyboard
    rect(147, 58, 166, 59, BEZEL)
    for x in range(148, 166, 2):
        put(x, 58, GREY)

    # mug + steam
    rect(221, 53, 226, 59, PINK)
    rect(222, 53, 225, 53, (255, 140, 205))
    put(227, 55, PINK); put(228, 56, PINK); put(227, 57, PINK)
    for k in range(2):
        for j in range(5):
            yy = 51 - ((t // 2 + j * 3 + k * 7) % 14)
            xx = 223 + k * 2 + round(math.sin((yy + t * .5) * .7))
            if yy > 38:
                put(xx, yy, STEAM if j % 2 else GREY)

    # plant
    rect(235, 54, 240, 59, POT)
    rect(235, 54, 240, 54, (190, 140, 245))
    for (x, y, c) in [(237, 53, LEAF), (237, 52, LEAF), (236, 51, LEAF), (235, 50, LEAF_D), (238, 51, LEAF),
                      (239, 50, LEAF), (240, 49, LEAF_D), (237, 50, LEAF), (237, 49, LEAF_D), (234, 52, LEAF_D),
                      (241, 51, LEAF), (233, 51, LEAF)]:
        put(x, y, c)

    # ------------------------------------------------------------- cat asleep on the desk, tail swaying
    rect(202, 55, 213, 59, CAT)
    rect(201, 56, 214, 59, CAT)
    rect(210, 52, 215, 56, CAT)
    put(210, 51, CAT); put(211, 50, CAT); put(214, 51, CAT); put(215, 50, CAT)   # ears
    for x in range(202, 210):                                     # light along the back
        put(x, 54, CAT_HI)
    for x in (204, 207):                                          # stripes
        put(x, 56, CAT_ST); put(x, 57, CAT_ST); put(x + 1, 58, CAT_ST)
    put(201, 55, CAT_HI); put(210, 51, CAT_HI); put(211, 50, CAT_HI)
    put(212, 54, CAT_ST); put(213, 54, CAT_ST)                    # closed eye
    put(215, 55, (255, 170, 190))                                 # nose
    sway = math.sin(2 * math.pi * t / FRAMES)
    for j in range(10):                                           # tail hanging off the desk edge
        tx = 214 + round(sway * (j / 9) ** 1.5 * 4)
        ty = 59 + j
        put(tx, ty, CAT)
        put(tx + 1, ty, CAT_ST if j % 3 == 1 else CAT)
    rect(214, 58, 216, 59, CAT)

    # ------------------------------------------------------------- the coder
    bob = 1 if (t // 4) % 2 else 0                               # nodding to the music
    # chair
    rect(110, 32, 117, 66, CHAIR)
    rect(110, 32, 110, 66, CHAIR_HI)
    rect(110, 66, 140, 69, CHAIR)
    rect(124, 70, 126, 79, CHAIR)
    rect(116, 80, 134, 80, CHAIR_HI)
    put(116, 81, GREY); put(134, 81, GREY); put(125, 81, GREY)
    # legs
    rect(124, 63, 145, 66, PANTS)
    rect(142, 66, 146, 80, PANTS)
    rect(143, 81, 151, 82, SHOE)
    # torso (hoodie)
    d.polygon([(119, 46 + bob), (121, 67), (139, 67), (137, 49 + bob), (131, 42 + bob), (123, 42 + bob)], fill=HOOD)
    d.polygon([(119, 46 + bob), (121, 67), (125, 67), (124, 46 + bob)], fill=HOOD_SH)
    for y in range(49 + bob, 67):                                # screen light on the chest
        put(138 if y < 60 else 139, y, AQUA if y % 3 else SKY)
    rect(120, 40 + bob, 126, 46 + bob, HOOD_SH)                  # hood behind the neck
    # arm reaching to the keyboard (typing: hands alternate)
    tap = (t // 2) % 2
    d.line([(131, 47 + bob), (135, 57)], fill=HOOD_SH, width=3)
    d.line([(135, 57), (147, 57)], fill=HOOD, width=2)
    put(148, 56 + tap, SKIN); put(149, 56 + tap, SKIN)
    put(151, 57 - tap, SKIN); put(152, 57 - tap, SKIN)
    # head
    hy = 34 + bob
    d.ellipse([125, hy - 7, 137, hy + 6], fill=SKIN)
    d.ellipse([124, hy - 8, 135, hy], fill=HAIR)
    rect(124, hy - 4, 127, hy + 3, HAIR)
    put(138, hy, SKIN); put(138, hy + 1, SKIN_SH)                # nose
    put(136, hy - 2, HAIR)                                       # eye
    for y in range(hy - 4, hy + 5):                              # screen light on the face
        put(137, y, (170, 240, 230)) if y % 2 else None
    rect(129, hy + 6, 132, 42 + bob, SKIN_SH)                    # neck
    # headphones
    d.arc([124, hy - 11, 136, hy + 3], 200, 340, fill=PINK, width=2)
    rect(128, hy - 3, 131, hy + 3, PINK)
    rect(129, hy - 2, 130, hy + 2, (255, 150, 210))
    return im


def main():
    out = sys.argv[1]
    frames = [frame(t) for t in range(FRAMES)]
    big = [f.resize((LW * SCALE, LH * SCALE), Image.NEAREST) for f in frames]
    # one shared palette so colours never flicker between frames
    strip = Image.new("RGB", (LW, LH * FRAMES))
    for i, f in enumerate(frames):
        strip.paste(f, (0, i * LH))
    pal = strip.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = [b.quantize(palette=pal, dither=Image.Dither.NONE) for b in big]
    q[0].save(out, save_all=True, append_images=q[1:], duration=80, loop=0, optimize=False, disposal=1)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
