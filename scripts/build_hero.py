#!/usr/bin/env python3
"""Build the README hero: an ASCII portrait of the avatar inside a neofetch-style
terminal panel.

    python3 scripts/build_hero.py          # needs Pillow only

Reads   assets/source/avatar.png
Writes  assets/hero.svg            (animated SVG, embedded in README via <img>)
        assets/ascii-portrait.txt  (the same character grid as plain text)

The output is deterministic for a given avatar.png and Pillow version.

How the portrait is made
------------------------
The avatar is a flat-coloured cartoon with dark outlines, so each character
cell is classified instead of being pushed through a single brightness ramp:

  background  mostly black source pixels             -> space
  feature     dark outline / eye / mouth pixels       -> a stroke glyph ( - _ / \\ | ( ) )
              (darker than their surroundings)           from the local orientation of the
                                                          dark map (structure tensor over a
                                                          1.5-cell window), '#' for solid dark
                                                          blobs, drawn in a dim tone of the
                                                          line's own colour
  edge        cell on the silhouette, partly covered -> the glyph whose rendered
                                                          shape best matches the
                                                          covered part of the cell
  fill        solid flat colour                       -> '@' in that colour

Glyph shapes come from rasterising the candidate characters with a real
monospace font (Menlo if present, else Pillow's bundled DejaVu Sans Mono) and
comparing them with the upscaled source cell by least squares (silhouette
cells). LINE_MODE = "match" swaps the stroke picker for per-cell shape matching
against the dark map; it was tried and rejected as noisy. A plain luminance
ramp was also tried and rejected: the face turned into uniform noise and the
eyes and muzzle outline disappeared. Cell colours
are the mean of the cell's bright pixels (or dark pixels for features),
quantised to a small shared palette.

In the SVG every character is placed at an explicit cell centre with
text-anchor="middle", so the portrait keeps its geometry in any monospace font
regardless of the font's natural advance.
"""
from __future__ import annotations

import colorsys
import math
import operator
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "source" / "avatar.png"
OUT_SVG = ROOT / "assets" / "hero.svg"
OUT_TXT = ROOT / "assets" / "ascii-portrait.txt"

# ---------------------------------------------------------------- design system
BG = "#0b0b0c"
BORDER = "#2a2a2e"
SURFACE = "#151517"
CREAM = "#eee0ba"
TAN = "#98846b"
DIM = "#5e5548"
RED = "#f00009"
RED_TEXT = "#ff3b44"
FONT = ('ui-monospace, SFMono-Regular, &quot;SF Mono&quot;, Menlo, Consolas, '
        '&quot;Liberation Mono&quot;, &quot;DejaVu Sans Mono&quot;, monospace')

# ---------------------------------------------------------------- portrait grid
ROWS = 56                  # character rows of the portrait
CELL_ASPECT = 0.6          # cell width / cell height (a monospace cell)
CROP_Y = (15, 125)         # source rows covered (pompom top .. into the shirt)
CENTRE_X = 58.0            # source column the grid is centred on
SRC_WIDTH = 76             # approx. source columns covered
BASELINE = 0.77            # baseline position inside a cell (fraction of height)
PALETTE_SIZE = 20

GW, GH = 6, 10             # matching raster per cell
FILL_CHAR = "@"
LINE_CHARS = "/\\|_-()'`,.<>^~=:;\"!"
EDGE_CHARS = list(".,:;'`\"-_~=+*^<>!|/\\()#%&@")
COV_MIN = 0.15             # less figure than this in a cell -> space
EDGE_COV = 0.85            # less than this -> silhouette (shape-matched) cell
DARK_V = 0.5               # HSV value below which a figure pixel is "dark line"
DARK_TAU = 0.3             # dark-feature share above which a cell is a line cell
LINE_V = 0.42              # brightness of line glyphs (lifted so they show on the panel)
SAT = 1.25                 # saturation boost (thin glyph strokes read paler)
LINE_MODE = "orient"       # "orient": stroke from local orientation; "match": per-cell shape match
BLOB_MASS = 0.8            # dark mass above which a feature cell is a solid dark blob
TOPHAT = 3                 # closing size for "darker than surroundings" line detection
TOPHAT_LO, TOPHAT_HI = 0.10, 0.30   # top-hat ramp (value units) -> line strength 0..1


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in ("/System/Library/Fonts/Menlo.ttc",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def glyph_masks(chars, blur=0.6):
    """Coverage maps (GW x GH, 0..1) of each glyph as drawn in one cell."""
    s = 8
    font = _font(GH * s)
    out = {}
    for ch in chars:
        im = Image.new("L", (GW * s, GH * s), 0)
        ImageDraw.Draw(im).text((GW * s / 2, BASELINE * GH * s), ch, font=font,
                                fill=255, anchor="ms")
        sm = im.resize((GW, GH), Image.BOX).filter(ImageFilter.GaussianBlur(blur))
        out[ch] = [v / 255 for v in sm.get_flattened_data()]
    return out


def _colour(px, line=False):
    n = len(px)
    r, g, b = (sum(p[i] for p in px) / n / 255 for i in range(3))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    s = min(1.0, s * SAT)
    if line:
        v = LINE_V
        if h > 0.05:            # keep brown lines muted; red lines stay red
            s = min(s, 0.45)
    elif v < 0.6:               # lift dark tones so shading survives on #0b0b0c
        v = max(v, 0.3 + 0.35 * v)
    return tuple(int(round(x * 255)) for x in colorsys.hsv_to_rgb(h, s, v))


def build_grid():
    """Return (grid, cols) where grid[r][c] = (char, (r,g,b) | None)."""
    y0, y1 = CROP_Y
    sh = (y1 - y0) / ROWS
    sw = sh * CELL_ASPECT
    cols = int(round(SRC_WIDTH / sw))
    cols += cols % 2
    x0 = CENTRE_X - cols * sw / 2
    box = (x0, y0, x0 + cols * sw, y1)

    src = Image.open(SRC).convert("RGB")
    val = src.convert("HSV").split()[2]
    # figure mask: everything that is not the black backdrop (small gaps closed)
    fig = (val.point(lambda x: 255 if x > 60 else 0)
           .filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3)))
    # relative darkness: how much darker a pixel is than its closed neighbourhood
    closed = val.filter(ImageFilter.MaxFilter(TOPHAT)).filter(ImageFilter.MinFilter(TOPHAT))
    th = Image.new("L", src.size)
    th.putdata([c - v for c, v in zip(closed.get_flattened_data(), val.get_flattened_data())])
    W, H = cols * GW, ROWS * GH
    C = list(src.resize((W, H), Image.BICUBIC, box=box).get_flattened_data())
    V = [x / 255 for x in val.resize((W, H), Image.BICUBIC, box=box).get_flattened_data()]
    F = [x / 255 for x in fig.resize((W, H), Image.BILINEAR, box=box).get_flattened_data()]
    T = [x / 255 for x in th.resize((W, H), Image.BICUBIC, box=box).get_flattened_data()]

    em = glyph_masks(EDGE_CHARS)
    dense = max(sum(m) / len(m) for m in em.values())
    em = {c: [v / dense for v in m] for c, m in em.items()}
    ess = {c: sum(v * v for v in m) for c, m in em.items()}
    lm = glyph_masks(LINE_CHARS)
    lnorm = {c: math.sqrt(sum(v * v for v in m)) for c, m in lm.items()}

    # dark-feature strength over the whole canvas (absolute darkness or darker-than-surroundings)
    DK = [f * max(0.0, min(1.0, (DARK_V - v) / DARK_V * 2),
                  min(1.0, max(0.0, (t - TOPHAT_LO) / (TOPHAT_HI - TOPHAT_LO))))
          for v, f, t in zip(V, F, T)]

    def stroke(r, c):
        """Pick a stroke glyph from the local orientation of the dark map."""
        xa, xb = max(1, c * GW - GW // 2), min(W - 1, (c + 1) * GW + GW // 2)
        ya, yb = max(1, r * GH - GH // 2), min(H - 1, (r + 1) * GH + GH // 2)
        jxx = jyy = jxy = 0.0
        for y in range(ya, yb):
            for x in range(xa, xb):
                gx = DK[y * W + x + 1] - DK[y * W + x - 1]
                gy = DK[(y + 1) * W + x] - DK[(y - 1) * W + x]
                jxx += gx * gx; jyy += gy * gy; jxy += gx * gy
        tr = jxx + jyy
        # centroid of darkness inside the cell (for _ vs - and ( vs ))
        m = sy = sx = 0.0
        for j in range(GH):
            for i in range(GW):
                d = DK[(r * GH + j) * W + c * GW + i]
                m += d; sy += d * j; sx += d * i
        cy = sy / m / (GH - 1) if m else 0.5
        cx = sx / m / (GW - 1) if m else 0.5
        mass = m / (GW * GH)
        if tr < 1e-6:
            return "#" if mass > 0.55 else ":"
        coh = math.sqrt((jxx - jyy) ** 2 + 4 * jxy * jxy) / tr
        if mass > BLOB_MASS or coh < 0.25:
            return "#" if mass > BLOB_MASS else ("*" if mass > 0.3 else ":")
        # gradient direction; the stroke runs perpendicular to it
        ang = 0.5 * math.atan2(2 * jxy, jxx - jyy)          # gradient angle, image coords (y down)
        la = math.degrees(ang + math.pi / 2) % 180            # stroke angle, 0 = horizontal
        if la < 22.5 or la >= 157.5:
            return "_" if cy > 0.62 else ("-" if cy > 0.3 else ("~" if cy > 0.2 else "`"))
        if la < 67.5:
            return "\\"   # y down: 45 deg in image coords goes down-right
        if la < 112.5:
            return "(" if cx < 0.3 else (")" if cx > 0.7 else "|")
        return "/"

    n = GW * GH
    grid = []
    for r in range(ROWS):
        row = []
        for c in range(cols):
            idx = [(r * GH + j) * W + c * GW + i for j in range(GH) for i in range(GW)]
            v = [V[k] for k in idx]
            f = [F[k] for k in idx]
            cov = sum(f) / n
            if cov < COV_MIN:
                row.append((" ", None))
                continue
            t = [T[k] for k in idx]
            dark = [fi * max(0.0, min(1.0, (DARK_V - vi) / DARK_V * 2),
                              min(1.0, max(0.0, (ti - TOPHAT_LO) / (TOPHAT_HI - TOPHAT_LO))))
                    for vi, fi, ti in zip(v, f, t)]
            mx = max(v)
            bright = [C[k] for k, x, d in zip(idx, v, dark) if x > max(DARK_V, 0.75 * mx) and d < 0.5]
            if sum(dark) / n > DARK_TAU or not bright:
                if LINE_MODE == "orient":
                    ch = stroke(r, c)
                else:
                    norm = math.sqrt(sum(x * x for x in dark)) or 1.0
                    ch = max(LINE_CHARS, key=lambda g: sum(map(operator.mul, dark, lm[g])) / (norm * lnorm[g]))
                dpx = [C[k] for k, x in zip(idx, dark) if x > 0.5] or [C[k] for k in idx]
                row.append((ch, _colour(dpx, line=True)))
                continue
            col = _colour(bright)
            if cov < EDGE_COV:
                tt = [fi * (1.0 - 0.7 * d) for d, fi in zip(dark, f)]
                ch = min(EDGE_CHARS, key=lambda g: ess[g] - 2 * sum(map(operator.mul, tt, em[g])))
            else:
                ch = FILL_CHAR
            row.append((ch, col))
        grid.append(row)
    return grid, cols


def quantise(grid, k=PALETTE_SIZE):
    """Map every cell colour onto a shared palette of at most k colours."""
    cells = [col for row in grid for _, col in row if col]
    im = Image.new("RGB", (len(cells), 1))
    im.putdata(cells)
    q = im.quantize(colors=k, method=Image.Quantize.MEDIANCUT, kmeans=4)
    pal = q.getpalette()[: k * 3]
    used = sorted(set(q.get_flattened_data()))
    remap = {old: new for new, old in enumerate(used)}
    hexes = ["#%02x%02x%02x" % tuple(pal[i * 3:i * 3 + 3]) for i in used]
    it = iter(q.get_flattened_data())
    out = [[(ch, remap[next(it)] if col else None) for ch, col in row] for row in grid]
    return out, hexes


# ---------------------------------------------------------------- SVG layout
W_VIEW, H_VIEW = 840, 440
TITLE_H = 30
PORTRAIT_X, PORTRAIT_TOP, PORTRAIT_H = 26, 70, 356
INFO_X = 304
FS = 14                    # terminal text size
ADV = 8.5                  # terminal text cell (explicit, font independent)

PROMPT_Y = 54
INFO_TOP = 102
INFO_LH = 24

COMMAND = "neofetch --ascii ~/avatar.png"

INFO = [
    ("title", "tohin@island"),
    ("rule", "-" * 12),
    ("kv", "role", "AI Backend Engineer"),
    ("kv", "based", "Gurugram, India"),
    ("kv", "builds", "AI agents, the backends they run on,"),
    ("cont", "and the checks that prove they did the work"),
    ("kv", "stack", "Python · Swift · TypeScript · Rust"),
    ("kv", "study", "B.Tech CSE (AI & ML), Sharda University, 2026"),
    ("kv", "paper", "IEEE ISAECT 2025 · WalkGuardian"),
    ("kv", "open to", "AI engineering · AI backend · distributed systems"),
    ("gap",),
    ("swatch",),
]
KEY_W = 10                 # key column width in cells

# animation timeline (seconds)
T_TYPE0, T_TYPE_STEP = 0.35, 0.045
T_ROWS0, T_ROWS_SPAN = 1.95, 2.4
T_INFO0, T_INFO_STEP = 3.9, 0.12


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def fmt(x: float) -> str:
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return s if s else "0"


def xs(x0: float, n: int, adv: float) -> str:
    """Centre x of n consecutive cells starting at x0."""
    return " ".join(fmt(x0 + (i + 0.5) * adv) for i in range(n))


def text_cells(x0, y, s, cls, extra=""):
    """A run of terminal text pinned to the ADV grid (cell centres)."""
    return (f'<text x="{xs(x0, len(s), ADV)}" y="{fmt(y)}" text-anchor="middle" class="{cls}"{extra}>'
            f"{esc(s)}</text>")


def build_svg(grid, palette, cols):
    rows = len(grid)
    ch = PORTRAIT_H / rows
    cw = ch * CELL_ASPECT
    pfs = ch  # portrait font size == cell height

    o = []
    a = o.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W_VIEW} {H_VIEW}" '
      f'role="img" aria-label="Terminal window: an ASCII-art portrait of Tohin Majumder\'s '
      f'avatar, a cartoon ape in a red beanie, next to neofetch-style info. AI Backend '
      f'Engineer in Gurugram, India, building AI agents, their backends, and the checks '
      f'that prove they did the work.">')
    a("<title>tohin@island: neofetch</title>")
    css = [
        f"text{{font-family:{FONT};font-variant-ligatures:none;}}",
        f".t{{font-size:{FS}px;fill:{CREAM};}}",
        f".k{{fill:{RED_TEXT};}}.n{{fill:{TAN};}}.d{{fill:{DIM};}}.c{{fill:{CREAM};}}",
        f".tt{{font-size:12px;fill:{TAN};}}",
        f".pt{{font-size:{fmt(pfs)}px;font-weight:700;}}",
    ]
    css += [f".p{i}{{fill:{h};}}" for i, h in enumerate(palette)]
    css += [
        "@keyframes on{from{opacity:0}to{opacity:1}}",
        "@keyframes type{from{transform:translateX(-%spx)}to{transform:translateX(0)}}" % fmt(len(COMMAND) * ADV),
        "@keyframes tcur{0%,99.9%{opacity:1}100%{opacity:0}}",
        "@keyframes blink{0%,49.9%{opacity:1}50%,100%{opacity:0}}",
        f".r{{animation:on .06s linear both;}}",
        f".i{{animation:on .18s ease-out both;}}",
        f".cover{{animation:type {fmt(len(COMMAND) * T_TYPE_STEP)}s steps({len(COMMAND)}) {fmt(T_TYPE0)}s both;}}",
        f".tcur{{opacity:0;animation:tcur {fmt(len(COMMAND) * T_TYPE_STEP + 0.6)}s linear {fmt(T_TYPE0 - 0.3)}s both,"
        f"type {fmt(len(COMMAND) * T_TYPE_STEP)}s steps({len(COMMAND)}) {fmt(T_TYPE0)}s both;}}",
        f".cur{{animation:on .01s linear {{END}}s both,blink 1.1s steps(1) {{END}}s infinite;}}",
        "@media (prefers-reduced-motion:reduce){.r,.i,.cover,.tcur,.cur{animation:none;}}",
    ]
    t_end = T_INFO0 + (len(INFO) + 1) * T_INFO_STEP + 0.15
    a("<style>" + "".join(css).replace("{END}", fmt(t_end)) + "</style>")

    # panel + title bar
    a('<defs><clipPath id="panel"><rect x="0.5" y="0.5" width="839" height="439" rx="14"/></clipPath></defs>')
    a(f'<rect x="0.5" y="0.5" width="839" height="439" rx="14" fill="{BG}"/>')
    a(f'<g clip-path="url(#panel)"><rect width="{W_VIEW}" height="{TITLE_H}" fill="{SURFACE}"/>'
      f'<rect y="{TITLE_H}" width="{W_VIEW}" height="1" fill="{BORDER}"/></g>')
    a(f'<rect x="0.5" y="0.5" width="839" height="439" rx="14" fill="none" stroke="{BORDER}"/>')
    for i, colr in enumerate((RED, CREAM, TAN)):
        a(f'<circle cx="{20 + i * 17}" cy="15.5" r="5" fill="{colr}"/>')
    a(f'<text x="420" y="19.5" text-anchor="middle" class="tt">tohin@island: ~</text>')

    # prompt + typed command
    px0 = PORTRAIT_X - 4
    pr_user = "tohin@island"
    a(f'<g class="t">{text_cells(px0, PROMPT_Y, pr_user, "n")}'
      f'{text_cells(px0 + len(pr_user) * ADV, PROMPT_Y, ":~", "d")}'
      f'{text_cells(px0 + (len(pr_user) + 2) * ADV, PROMPT_Y, "$", "k")}')
    cmd_x = px0 + (len(pr_user) + 4) * ADV
    a(text_cells(cmd_x, PROMPT_Y, COMMAND, "c") + "</g>")
    cover_x = cmd_x + len(COMMAND) * ADV
    # the cover sits after the command at rest; while typing it slides in from the left
    a(f'<rect class="cover" x="{fmt(cover_x)}" y="{PROMPT_Y - 13}" width="{fmt(W_VIEW - cover_x - 10)}" '
      f'height="18" fill="{BG}"/>')
    a(f'<rect class="tcur" x="{fmt(cover_x + 0.5)}" y="{PROMPT_Y - 11}" width="{fmt(ADV - 1)}" height="15" fill="{CREAM}"/>')

    # portrait
    a(f'<g class="pt" aria-hidden="true">')
    for r, row in enumerate(grid):
        y = PORTRAIT_TOP + (r + BASELINE) * ch
        delay = T_ROWS0 + T_ROWS_SPAN * r / rows
        spans = []
        c = 0
        while c < cols:
            chh, pi = row[c]
            if chh == " ":
                c += 1
                continue
            start = c
            run = []
            while c < cols and row[c][0] != " " and row[c][1] == pi:
                run.append(row[c][0])
                c += 1
            spans.append(f'<tspan x="{xs(PORTRAIT_X + start * cw, len(run), cw)}" class="p{pi}">'
                         f'{esc("".join(run))}</tspan>')
        if spans:
            a(f'<text y="{fmt(y)}" text-anchor="middle" class="r" style="animation-delay:{fmt(delay)}s">'
              + "".join(spans) + "</text>")
    a("</g>")

    # info block
    a('<g class="t">')
    y = INFO_TOP
    for i, item in enumerate(INFO):
        st = f' style="animation-delay:{fmt(T_INFO0 + i * T_INFO_STEP)}s"'
        kind = item[0]
        if kind == "title":
            a(f'<g class="i"{st}>{text_cells(INFO_X, y, "tohin", "k")}'
              f'{text_cells(INFO_X + 5 * ADV, y, "@", "n")}'
              f'{text_cells(INFO_X + 6 * ADV, y, "island", "k")}</g>')
        elif kind == "rule":
            a(f'<g class="i"{st}>{text_cells(INFO_X, y, item[1], "d")}</g>')
        elif kind == "kv":
            a(f'<g class="i"{st}>{text_cells(INFO_X, y, item[1], "k")}'
              f'{text_cells(INFO_X + KEY_W * ADV, y, item[2], "c")}</g>')
        elif kind == "cont":
            a(f'<g class="i"{st}>{text_cells(INFO_X + KEY_W * ADV, y, item[1], "c")}</g>')
        elif kind == "gap":
            y += INFO_LH * 0.4
            continue
        elif kind == "swatch":
            sw = [SURFACE, BORDER, DIM, TAN, CREAM, RED, RED_TEXT, "#7a0005"]
            cells = "".join(
                f'<rect x="{fmt(INFO_X + j * 3 * ADV)}" y="{fmt(y - 12)}" width="{fmt(3 * ADV)}" height="15" fill="{colr}"/>'
                for j, colr in enumerate(sw))
            a(f'<g class="i"{st}>{cells}</g>')
        y += INFO_LH
    a("</g>")

    # final prompt with blinking cursor
    fy = PORTRAIT_TOP + PORTRAIT_H - 6
    st = f' style="animation-delay:{fmt(t_end - 0.15)}s"'
    a(f'<g class="t i"{st}>{text_cells(INFO_X, fy, pr_user, "n")}'
      f'{text_cells(INFO_X + len(pr_user) * ADV, fy, ":~", "d")}'
      f'{text_cells(INFO_X + (len(pr_user) + 2) * ADV, fy, "$", "k")}</g>')
    a(f'<rect class="cur" x="{fmt(INFO_X + (len(pr_user) + 4) * ADV + 0.5)}" y="{fmt(fy - 11)}" '
      f'width="{fmt(ADV - 1)}" height="15" fill="{CREAM}"/>')
    a("</svg>")
    return "\n".join(o) + "\n"


def main():
    grid, cols = build_grid()
    qgrid, palette = quantise(grid)
    OUT_TXT.write_text("\n".join("".join(ch for ch, _ in row).rstrip() for row in qgrid) + "\n")
    svg = build_svg(qgrid, palette, cols)
    OUT_SVG.write_text(svg)
    print(f"portrait {cols}x{len(qgrid)}, {len(palette)} colours, svg {len(svg.encode()) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
