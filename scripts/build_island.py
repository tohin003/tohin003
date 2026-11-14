#!/usr/bin/env python3
"""Generate assets/island.svg: animated low-poly night island banner.

Deterministic (fixed seed). Run from anywhere:
    python3 scripts/build_island.py
"""
import math
import random
from pathlib import Path

W, H = 840, 260
HORIZON = 172
OUT = Path(__file__).resolve().parent.parent / "assets" / "island.svg"

rnd = random.Random(7)

CREAM, TAN, DIM, RED, RED_TXT = "#eee0ba", "#98846b", "#5e5548", "#f00009", "#ff3b44"
BG, SURFACE, BORDER = "#0b0b0c", "#151517", "#2a2a2e"


def f(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def pts(p):
    return " ".join(f"{f(x)},{f(y)}" for x, y in p)


def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    t = max(0.0, min(1.0, t))
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


out = []
add = out.append

# ---------------------------------------------------------------- terrain
LIGHT = (-0.75, 0.55, 0.36)  # moon up-left, slightly toward viewer
ln = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / ln for c in LIGHT)
LAND_DARK, LAND_LIGHT = "#0f0d0b", "#5a4c3a"
DEPTH_K = 7.0  # screen px per depth unit


def shade_tri(a, b, c, dark=LAND_DARK, light=LAND_LIGHT, jitter=0.06):
    # a,b,c are (x, h, z): x right, h up, z toward viewer
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    nl = math.sqrt(sum(x * x for x in n)) or 1
    n = tuple(x / nl for x in n)
    if n[1] < 0:
        n = tuple(-x for x in n)
    d = sum(n[i] * LIGHT[i] for i in range(3))
    t = max(0.0, d) ** 1.25 + rnd.uniform(-jitter, jitter)
    return mix(dark, light, t)


def proj(p, base=HORIZON):
    x, h, z = p
    return (x, base - h + z * DEPTH_K)


def interp(profile, x):
    for (x0, h0), (x1, h1) in zip(profile, profile[1:]):
        if x0 <= x <= x1:
            return h0 + (h1 - h0) * (x - x0) / (x1 - x0)
    return 0.0


def terrain(profile, rows, base=HORIZON, dark=LAND_DARK, light=LAND_LIGHT):
    """rows: list of (z, height_factor, xjitter). Back row first."""
    grid = []
    for ri, (z, hf, xj) in enumerate(rows):
        row = []
        for i, (x, h) in enumerate(profile):
            jx = 0 if i in (0, len(profile) - 1) else rnd.uniform(-xj, xj)
            hh = h * hf + (rnd.uniform(-2.5, 2.5) if 0 < i < len(profile) - 1 and hf > 0 else 0)
            if ri > 0 and (i == 0 or i == len(profile) - 1):
                hh = 0
            zz = z + (rnd.uniform(-0.35, 0.45) if ri > 0 and 0 < i < len(profile) - 1 else 0)
            row.append((x + jx, max(0.0, hh), zz))
        grid.append(row)
    polys = []
    for r in range(len(grid) - 1):
        A, B = grid[r], grid[r + 1]
        for i in range(len(A) - 1):
            a0, a1, b0, b1 = A[i], A[i + 1], B[i], B[i + 1]
            if (i + r) % 2:
                tris = [(a0, a1, b1), (a0, b1, b0)]
            else:
                tris = [(a0, a1, b0), (a1, b1, b0)]
            for t in tris:
                col = shade_tri(*t, dark=dark, light=light)
                polys.append((col, [proj(p, base) for p in t]))
    return polys, grid


MAIN = [(412, 0), (432, 9), (452, 24), (470, 33), (490, 35), (512, 48), (534, 60),
        (556, 64), (576, 66), (598, 80), (616, 77), (636, 61), (656, 58), (676, 50),
        (698, 37), (718, 28), (738, 33), (756, 52), (774, 56), (792, 44), (812, 24),
        (830, 8), (846, 0)]
main_polys, main_grid = terrain(MAIN, [(0, 1.0, 0), (0.7, 0.72, 5), (1.5, 0.32, 6), (2.2, 0.0, 6)])


def ground_y(x):
    return HORIZON - interp(MAIN, x)


SMALL = [(150, 0), (166, 6), (182, 12), (198, 15), (214, 11), (230, 6), (246, 0)]
small_polys, _ = terrain(SMALL, [(0, 1.0, 0), (0.6, 0.0, 4)],
                         dark="#15130f", light="#4a3f31")
TINY = [(296, 0), (306, 4), (318, 6), (330, 3), (340, 0)]
tiny_polys, _ = terrain(TINY, [(0, 1.0, 0), (0.4, 0.0, 2)], dark="#13110e", light="#3a3229")

# ---------------------------------------------------------------- water
SEA_A, SEA_B = "#0a0c10", "#161b22"
MOON = (404, 46)
water = []
ys = [HORIZON, 177, 184, 193, 204, 218, 236, 262]
cols_per_row = [44, 36, 28, 22, 17, 13, 10, 8]
grid_w = []
for ri, y in enumerate(ys):
    n = cols_per_row[ri]
    step = (W + 40) / n
    row = []
    for i in range(n + 1):
        x = -20 + i * step + (rnd.uniform(-step * 0.3, step * 0.3) if 0 < i < n else 0)
        yy = y + (rnd.uniform(-1.2, 1.2) * (ri / 3 + 0.3) if 0 < ri < len(ys) - 1 else 0)
        row.append((x, yy))
    grid_w.append(row)
for r in range(len(grid_w) - 1):
    A, B = grid_w[r], grid_w[r + 1]
    i = j = 0
    while i < len(A) - 1 or j < len(B) - 1:
        if j >= len(B) - 1 or (i < len(A) - 1 and A[i + 1][0] < B[j + 1][0]):
            tri = [A[i], A[i + 1], B[j]]
            i += 1
        else:
            tri = [A[i], B[j + 1], B[j]]
            j += 1
        cx = sum(p[0] for p in tri) / 3
        cy = sum(p[1] for p in tri) / 3
        near_moon = math.exp(-((cx - MOON[0]) / 70) ** 2)
        depth = (cy - HORIZON) / (H - HORIZON)
        t = 0.25 + 0.35 * rnd.random() + 0.45 * near_moon - 0.15 * depth
        water.append((mix(SEA_A, SEA_B, t), tri, near_moon))

# ---------------------------------------------------------------- stars
stars = []
caption_box = (30, 64, 392, 150)
lamp_zone = (700, 40, 840, 100)
while len(stars) < 30:
    x, y = rnd.uniform(16, 824), rnd.uniform(12, 120)
    if caption_box[0] < x < caption_box[2] and caption_box[1] < y < caption_box[3]:
        continue
    if math.hypot(x - MOON[0], y - MOON[1]) < 34:
        continue
    if y > HORIZON - interp(MAIN, x) - (48 if 430 < x < 800 else 18):
        continue
    if any(math.hypot(x - sx, y - sy) < 32 for sx, sy, *_ in stars):
        continue
    r = rnd.choice([0.7, 0.8, 0.9, 1.0, 1.2, 1.5])
    stars.append((x, y, r, rnd.randrange(4)))

# ---------------------------------------------------------------- svg
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" '
    f'aria-label="A low-poly island at night with a lighthouse sweeping its beam over the sea. '
    f'Explore the island at tohinisland.vercel.app">')
add('<title>Explore the island: tohinisland.vercel.app</title>')
add(f'''<defs>
<clipPath id="panel"><rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14"/></clipPath>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="#08080a"/><stop offset="0.75" stop-color="#101114"/><stop offset="1" stop-color="#16171a"/>
</linearGradient>
<radialGradient id="halo"><stop offset="0" stop-color="{CREAM}" stop-opacity="0.16"/><stop offset="1" stop-color="{CREAM}" stop-opacity="0"/></radialGradient>
<linearGradient id="beamL" x1="1" y1="0" x2="0" y2="0">
<stop offset="0" stop-color="{CREAM}" stop-opacity="0.42"/><stop offset="0.35" stop-color="{CREAM}" stop-opacity="0.12"/><stop offset="1" stop-color="{CREAM}" stop-opacity="0"/>
</linearGradient>
<linearGradient id="beamR" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="{CREAM}" stop-opacity="0.3"/><stop offset="1" stop-color="{CREAM}" stop-opacity="0"/>
</linearGradient>
<radialGradient id="lampglow"><stop offset="0" stop-color="{CREAM}" stop-opacity="0.5"/><stop offset="1" stop-color="{CREAM}" stop-opacity="0"/></radialGradient>
<linearGradient id="reflfade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.9"/></linearGradient>
</defs>''')

add('''<style>
.tw{animation:tw 5s ease-in-out infinite}
.tw1{animation-duration:3.7s;animation-delay:-1.2s}
.tw2{animation-duration:6.3s;animation-delay:-2.9s}
.tw3{animation-duration:8.1s;animation-delay:-0.6s}
@keyframes tw{0%,100%{opacity:1}50%{opacity:.3}}
.beam{transform-box:view-box;transform-origin:LXpx LYpx;transform:rotate(-7deg);animation:sweep 14s ease-in-out infinite}
@keyframes sweep{0%,100%{transform:rotate(-19deg)}50%{transform:rotate(11deg)}}
.lampg{animation:lamp 7s ease-in-out infinite}
@keyframes lamp{0%,100%{opacity:.75}50%{opacity:1}}
.win{animation:win 6s steps(1,end) infinite}
.win2{animation-duration:9s;animation-delay:-4s}
@keyframes win{0%,100%{opacity:1}46%{opacity:.82}48%{opacity:1}71%{opacity:.9}73%{opacity:1}}
.shim{animation:shim 4.5s ease-in-out infinite}
.sh1{animation-duration:3.4s;animation-delay:-1.1s}
.sh2{animation-duration:5.8s;animation-delay:-2.4s}
@keyframes shim{0%,100%{opacity:.9}50%{opacity:.25}}
.refl{animation:refl 6s ease-in-out infinite alternate}
@keyframes refl{from{transform:translateX(-3px)}to{transform:translateX(3px)}}
.drift{animation:drift 11s ease-in-out infinite alternate}
@keyframes drift{from{transform:translateX(0)}to{transform:translateX(-14px)}}
.boat{transform-box:view-box;transform-origin:BXpx BYpx;animation:bob 5s ease-in-out infinite}
@keyframes bob{0%,100%{transform:translateY(0) rotate(-2deg)}50%{transform:translateY(1.6px) rotate(2deg)}}
.cloud{animation:cloud 60s ease-in-out infinite alternate}
@keyframes cloud{from{transform:translateX(0)}to{transform:translateX(70px)}}
.flag{transform-box:view-box;transform-origin:FXpx FYpx;animation:flag 3s ease-in-out infinite}
@keyframes flag{0%,100%{transform:scaleX(1)}50%{transform:scaleX(.8)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
</style>''')

add(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="{BG}"/>')
add('<g clip-path="url(#panel)">')
add(f'<rect width="{W}" height="{HORIZON+1}" fill="url(#sky)"/>')

# stars
for x, y, r, k in stars:
    cls = f"tw tw{k}" if k else "tw"
    col = CREAM if r >= 1 else "#c9bc9a"
    if r >= 1.4:
        s = r * 2.6
        add(f'<path class="{cls}" fill="{col}" d="M{f(x)} {f(y-s)}L{f(x+r*0.55)} {f(y)}L{f(x)} {f(y+s)}L{f(x-r*0.55)} {f(y)}Z'
            f'M{f(x-s)} {f(y)}L{f(x)} {f(y+r*0.55)}L{f(x+s)} {f(y)}L{f(x)} {f(y-r*0.55)}Z"/>')
    else:
        add(f'<circle class="{cls}" cx="{f(x)}" cy="{f(y)}" r="{r}" fill="{col}"/>')

# moon: faceted disc
mx, my = MOON
add(f'<circle cx="{mx}" cy="{my}" r="46" fill="url(#halo)"/>')
mr = 17
n = 10
mpts = [(mx + mr * math.cos(2 * math.pi * i / n - 0.3), my + mr * math.sin(2 * math.pi * i / n - 0.3)) for i in range(n)]
for i in range(n):
    a, b = mpts[i], mpts[(i + 1) % n]
    ang = math.atan2((a[1] + b[1]) / 2 - my, (a[0] + b[0]) / 2 - mx)
    t = 0.5 + 0.5 * math.cos(ang - math.radians(200))
    col = mix("#ddd0ac", "#f4e9cb", t * 0.9 + rnd.uniform(0, 0.1))
    add(f'<polygon points="{pts([(mx + 2, my - 1), a, b])}" fill="{col}"/>')

# cloud (drifts slowly, sits below moon so never hides it fully)
cl = [(330, 74), (346, 66), (362, 68), (372, 62), (390, 64), (402, 70), (414, 72), (400, 78), (350, 79)]
add('<g class="cloud" opacity="0.9">')
add(f'<polygon points="{pts(cl)}" fill="#1b1b1e"/>')
add(f'<polygon points="{pts([(346, 66), (362, 68), (372, 62), (390, 64), (402, 70), (360, 72)])}" fill="#232326"/>')
add('</g>')

# lighthouse geometry (needed for beam before terrain)
LX = 770
LBASE = ground_y(LX) + 4
LTOP = 72
LY = LTOP - 7  # lamp centre

# distant islands
for col, tri in tiny_polys + small_polys:
    add(f'<polygon points="{pts(tri)}" fill="{col}" stroke="{col}" stroke-width="0.4"/>')
# tiny light on the small island + palm silhouette
add(f'<rect class="win win2" x="199" y="{HORIZON-17}" width="2" height="2" fill="{CREAM}" opacity="0.9"/>')
add(f'<path d="M193 {HORIZON-14}L194 {HORIZON-24}" stroke="#1a1714" stroke-width="1.2"/>')
add(f'<path d="M194 {HORIZON-24}l-6 3l6-1.5l5 3.5l-4-4.5l6-1l-7 0.5z" fill="#1a1714"/>')

# water
add('<g>')
for col, tri, _ in water:
    add(f'<polygon points="{pts(tri)}" fill="{col}" stroke="{col}" stroke-width="0.4"/>')
add('</g>')

# reflection of main island: mirrored silhouette, squashed, faded
SHORE_Y = HORIZON + 2.2 * DEPTH_K
sil = [(x, HORIZON - h) for x, h in MAIN]
add(f'<g opacity="0.32" transform="translate(0 {f(SHORE_Y)}) scale(1 -0.55) translate(0 {f(-SHORE_Y)})">')
add(f'<polygon points="{pts(sil + [(846, SHORE_Y), (412, SHORE_Y)])}" fill="#050505"/>')
add('</g>')
for x0 in (566, 594, 652, 480):
    add(f'<rect class="shim sh{x0%3}" x="{x0-2}" y="{f(SHORE_Y+8+rnd.uniform(0,6))}" width="5" height="1.2" fill="{CREAM}" opacity="0.35"/>')
add(f'<rect class="shim sh1" x="{LX-2}" y="{f(SHORE_Y+30)}" width="5" height="1.4" fill="{CREAM}" opacity="0.45"/>')

# moon reflection
add('<g class="refl">')
for k, (dy, w) in enumerate([(4, 22), (10, 30), (17, 20), (25, 36), (34, 24), (45, 30), (57, 18), (70, 26)]):
    y = HORIZON + 14 + dy
    if y > H - 4:
        break
    x = mx - w / 2 + rnd.uniform(-6, 6)
    op = 0.75 - k * 0.07
    add(f'<polygon class="shim sh{k%3}" points="{pts([(x, y), (x + w, y - 0.6), (x + w * 0.8, y + 1.6), (x + w * 0.15, y + 1.8)])}" fill="{CREAM}" opacity="{f(op)}"/>')
add('</g>')

# drifting wave highlights
add('<g class="drift">')
for _ in range(14):
    x = rnd.uniform(10, 820)
    y = rnd.uniform(HORIZON + 22, H - 8)
    if abs(x - mx) < 50:
        continue
    w = 6 + (y - HORIZON) * 0.12
    add(f'<path class="shim sh{rnd.randrange(3)}" d="M{f(x)} {f(y)}l{f(w)} -1.2l{f(w*0.6)} 1.4" fill="none" stroke="#2a2e35" stroke-width="1"/>')
add('</g>')

# beam (behind terrain, over sky & sea)
add('<g class="beam">')
add(f'<polygon points="{pts([(LX, LY - 2), (LX - 600, LY - 44), (LX - 600, LY + 44), (LX, LY + 2)])}" fill="url(#beamL)"/>')
add(f'<polygon points="{pts([(LX, LY - 2), (LX + 160, LY - 22), (LX + 160, LY + 22), (LX, LY + 2)])}" fill="url(#beamR)"/>')
add('</g>')

# main terrain
add('<g>')
for col, tri in main_polys:
    add(f'<polygon points="{pts(tri)}" fill="{col}" stroke="{col}" stroke-width="0.5" stroke-linejoin="round"/>')
add('</g>')
# shoreline foam
shore = [proj(p) for p in main_grid[-1]]
add(f'<polyline points="{pts(shore)}" fill="none" stroke="#3a3b3f" stroke-width="0.8" opacity="0.7"/>')

# ---------------- props
DARKW = "#1d1915"
MIDW = "#2e2720"
LITW = "#4a3f31"


def palm(x, lean=1, h=22, s=1.0):
    y = ground_y(x) + 2
    tx, ty = x + lean * 5 * s, y - h * s
    g = [f'<path d="M{f(x)} {f(y)}Q{f(x+lean*1*s)} {f(y-h*0.5*s)} {f(tx)} {f(ty)}" fill="none" stroke="{MIDW}" stroke-width="{f(1.8*s)}"/>']
    fronds = [(-11, 4), (-8, -3), (0, -6), (9, -3), (12, 5), (5, 6)]
    for dx, dy in fronds:
        ex, ey = tx + dx * s, ty + dy * s
        mx_, my_ = tx + dx * 0.5 * s, ty + (dy - 4) * 0.5 * s
        col = "#3b4232" if dx < 0 else "#252a21"
        g.append(f'<polygon points="{pts([(tx, ty), (mx_, my_ - 1.5*s), (ex, ey), (mx_, my_ + 1*s)])}" fill="{col}"/>')
    return "".join(g)


def pine(x, h=18):
    y = ground_y(x) + 3
    return (f'<polygon points="{pts([(x, y - h), (x - 6, y), (x, y - 2)])}" fill="#3b4232"/>'
            f'<polygon points="{pts([(x, y - h), (x + 6, y), (x, y - 2)])}" fill="#22261e"/>')


add(pine(520, 16))
add(pine(530, 20))
add(pine(690, 15))
add(palm(446, -1, 22, 0.9))
add(palm(728, 1, 24, 1.0))
add(palm(610, 1, 18, 0.8))

# watchtower with shield + red flag (x ~ 478)
wx = 480
wy = ground_y(wx) + 2
wtop = wy - 38
add(f'<path d="M{wx-9} {f(wy)}L{wx-6} {f(wtop+6)}M{wx+9} {f(wy)}L{wx+6} {f(wtop+6)}M{wx-8} {f(wy-10)}L{wx+7} {f(wy-22)}M{wx+8} {f(wy-10)}L{wx-7} {f(wy-22)}" stroke="{MIDW}" stroke-width="1.6" fill="none"/>')
add(f'<polygon points="{pts([(wx-10, wtop+6), (wx+10, wtop+6), (wx+9, wtop+12), (wx-9, wtop+12)])}" fill="{MIDW}"/>')
add(f'<rect x="{wx-8}" y="{f(wtop-2)}" width="16" height="8" fill="{DARKW}"/>')
add(f'<rect class="win" x="{wx-5}" y="{f(wtop)}" width="10" height="4" fill="{CREAM}" opacity="0.85"/>')
add(f'<polygon points="{pts([(wx-11, wtop-2), (wx, wtop-11), (wx+11, wtop-2)])}" fill="{LITW}"/>')
add(f'<polygon points="{pts([(wx, wtop-11), (wx+11, wtop-2), (wx+1, wtop-2)])}" fill="{MIDW}"/>')
# shield on platform
add(f'<path d="M{wx-3.5} {f(wtop+7)}h7v2.5q0 3 -3.5 4.5q-3.5 -1.5 -3.5 -4.5z" fill="{TAN}"/>')
add(f'<path d="M{wx} {f(wtop+7)}h3.5v2.5q0 3 -3.5 4.5z" fill="{DIM}"/>')
# flag
FX, FY = wx, wtop - 11
add(f'<path d="M{FX} {f(FY)}V{f(FY-10)}" stroke="{TAN}" stroke-width="0.9"/>')
add(f'<polygon class="flag" points="{pts([(FX, FY-10), (FX+9, FY-7.5), (FX, FY-5)])}" fill="{RED}"/>')

# big hut (x ~ 566): wide thatched roof, lit door + window
hx = 566
hy = ground_y(hx) + 3
add(f'<polygon points="{pts([(hx-17, hy), (hx-16, hy-14), (hx+17, hy-14), (hx+18, hy)])}" fill="{MIDW}"/>')
add(f'<polygon points="{pts([(hx+4, hy), (hx+4, hy-14), (hx+17, hy-14), (hx+18, hy)])}" fill="{DARKW}"/>')
add(f'<polygon points="{pts([(hx-24, hy-12), (hx-2, hy-34), (hx+3, hy-34), (hx+25, hy-12)])}" fill="{TAN}" opacity="0.55"/>')
add(f'<polygon points="{pts([(hx-24, hy-12), (hx-2, hy-34), (hx-1, hy-12)])}" fill="#6e5f4c"/>')
add(f'<polygon points="{pts([(hx-1, hy-12), (hx-2, hy-34), (hx+3, hy-34), (hx+25, hy-12)])}" fill="#3a3128"/>')
add(f'<rect class="win" x="{hx-12}" y="{f(hy-10)}" width="6" height="5" fill="{CREAM}"/>')
add(f'<rect class="win win2" x="{hx-2}" y="{f(hy-10)}" width="5" height="10" fill="#d9c79c"/>')
add(f'<rect class="win" x="{hx+8}" y="{f(hy-10)}" width="5" height="5" fill="#c9b78e"/>')

# small hut (x ~ 600)
sx = 594
sy = ground_y(sx) + 3
add(f'<rect x="{sx-7}" y="{f(sy-9)}" width="14" height="9" fill="{DARKW}"/>')
add(f'<polygon points="{pts([(sx-10, sy-8), (sx, sy-19), (sx+10, sy-8)])}" fill="#4a3f31"/>')
add(f'<polygon points="{pts([(sx, sy-19), (sx+10, sy-8), (sx, sy-8)])}" fill="#2e2720"/>')
add(f'<rect class="win win2" x="{sx-3}" y="{f(sy-6)}" width="4" height="4" fill="{CREAM}"/>')

# round stone cottage with eyes (x ~ 652)
cx = 652
cy = ground_y(cx) + 3
r = 11
add(f'<path d="M{cx-r} {f(cy)}A{r} {r} 0 0 1 {cx+r} {f(cy)}Z" fill="#3a352e"/>')
add(f'<path d="M{cx+1} {f(cy)}V{f(cy-r)}A{r} {r} 0 0 1 {cx+r} {f(cy)}Z" fill="#26231f"/>')
for ang in (200, 235, 270, 305, 340):
    a = math.radians(ang)
    add(f'<path d="M{f(cx+r*0.55*math.cos(a))} {f(cy+r*0.55*math.sin(a))}L{f(cx+r*math.cos(a))} {f(cy+r*math.sin(a))}" stroke="#1a1815" stroke-width="0.7"/>')
add(f'<polygon points="{pts([(cx-r-2, cy-r+3), (cx, cy-r-7), (cx+r+2, cy-r+3)])}" fill="#4f4436"/>')
add(f'<polygon points="{pts([(cx, cy-r-7), (cx+r+2, cy-r+3), (cx+1, cy-r+3)])}" fill="#2e2720"/>')
for ex in (-4, 4):
    add(f'<ellipse class="win" cx="{cx+ex}" cy="{f(cy-5)}" rx="2.4" ry="2.8" fill="{CREAM}"/>')
    add(f'<circle cx="{cx+ex+0.6}" cy="{f(cy-4.6)}" r="1.1" fill="{BG}"/>')

# lighthouse
bw, tw_ = 9, 6
add(f'<polygon points="{pts([(LX-bw, LBASE), (LX-tw_, LTOP), (LX+tw_, LTOP), (LX+bw, LBASE)])}" fill="#cfc2a0"/>')
add(f'<polygon points="{pts([(LX+1, LBASE), (LX+1, LTOP), (LX+tw_, LTOP), (LX+bw, LBASE)])}" fill="#8d806a"/>')
# dark bands
for t0, t1 in ((0.22, 0.34), (0.56, 0.68)):
    y0 = LBASE + (LTOP - LBASE) * t0
    y1 = LBASE + (LTOP - LBASE) * t1
    w0 = bw + (tw_ - bw) * t0
    w1 = bw + (tw_ - bw) * t1
    add(f'<polygon points="{pts([(LX-w0, y0), (LX-w1, y1), (LX+w1, y1), (LX+w0, y0)])}" fill="#2c2620"/>')
add(f'<rect x="{LX-1.5}" y="{f(LBASE-8)}" width="3" height="6" fill="#1a1714"/>')
# gallery + lamp room
add(f'<rect x="{LX-9}" y="{LTOP-1}" width="18" height="3" fill="#2c2620"/>')
add(f'<circle class="lampg" cx="{LX}" cy="{LY}" r="16" fill="url(#lampglow)"/>')
add(f'<rect x="{LX-5}" y="{LTOP-11}" width="10" height="10" fill="#17140f"/>')
add(f'<rect x="{LX-3.5}" y="{LTOP-10}" width="7" height="8" fill="{CREAM}"/>')
add(f'<polygon points="{pts([(LX-7, LTOP-11), (LX, LTOP-19), (LX+7, LTOP-11)])}" fill="{RED}"/>')
add(f'<polygon points="{pts([(LX, LTOP-19), (LX+7, LTOP-11), (LX+0.5, LTOP-11)])}" fill="#a30006"/>')
add(f'<path d="M{LX} {LTOP-19}v-3" stroke="{TAN}" stroke-width="0.9"/>')

# boat (bobs), between the islands
BX, BY = 300, 214
add('<g class="boat">')
add(f'<polygon points="{pts([(BX-13, BY-4), (BX+14, BY-4), (BX+9, BY+1.5), (BX-9, BY+1.5)])}" fill="#2e2720"/>')
add(f'<polygon points="{pts([(BX-13, BY-4), (BX+14, BY-4), (BX+12, BY-2.5), (BX-11, BY-2.5)])}" fill="#4a3f31"/>')
add(f'<path d="M{BX} {BY-4}V{BY-25}" stroke="{TAN}" stroke-width="0.9"/>')
add(f'<polygon points="{pts([(BX+1, BY-24), (BX+1, BY-6), (BX+13, BY-6)])}" fill="#cfc2a0"/>')
add(f'<polygon points="{pts([(BX-1, BY-21), (BX-1, BY-6), (BX-9, BY-6)])}" fill="#8d806a"/>')
add(f'<path d="M{BX-12} {BY+3.5}h24" stroke="#2a2e35" stroke-width="1"/>')
add('</g>')

# ---------------- caption
FONT = 'ui-monospace,SFMono-Regular,&quot;SF Mono&quot;,Menlo,Consolas,&quot;Liberation Mono&quot;,&quot;DejaVu Sans Mono&quot;,monospace'
add(f'<g font-family="{FONT}">')
add(f'<text x="40" y="104" font-size="31" font-weight="700" fill="{CREAM}" letter-spacing="-0.5">explore the island</text>')
ay = 133
add(f'<path d="M40 {ay}h15M49 {ay-6}l6 6l-6 6" fill="none" stroke="{RED_TXT}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>')
add(f'<text x="66" y="{ay+6}" font-size="19" fill="{TAN}">tohinisland.vercel.app</text>')
add('</g>')

add('</g>')
add(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="none" stroke="{BORDER}"/>')
add('</svg>')

svg = "\n".join(out)
svg = (svg.replace("LXpx", f"{LX}px").replace("LYpx", f"{LY}px")
          .replace("BXpx", f"{BX}px").replace("BYpx", f"{BY}px")
          .replace("FXpx", f"{FX}px").replace("FYpx", f"{f(FY-7.5)}px"))
OUT.write_text(svg + "\n")
print(OUT, len(svg.encode()), "bytes")
