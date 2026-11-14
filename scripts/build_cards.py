#!/usr/bin/env python3
"""Generate the six animated project cards in assets/cards/*.svg.

Edit CARDS below (tagline, chips, name) and re-run:  python3 scripts/build_cards.py

Standard library only; output is deterministic.  Each SVG is a self-contained
dark panel (412x190), CSS-animated only (no JS, no external resources), with a
prefers-reduced-motion fallback that is a complete still.
"""
from pathlib import Path

# --------------------------------------------------------------------------
# Content: edit here.
# --------------------------------------------------------------------------
CARDS = [
    dict(slug="pebble", index="01", name="Pebble",
         url="https://github.com/tohin003/Pebble",
         tagline="An open-source AI agent that lives on your Mac.",
         chips=["Python", "Tauri", "MCP"]),
    dict(slug="truthstone", index="02", name="Truthstone",
         url="https://github.com/tohin003/Truthstone",
         tagline="A local, deterministic reliability guard for coding agents.",
         chips=["Python", "Claude Code", "Codex"]),
    dict(slug="agentguard", index="03", name="AgentGuard",
         url="https://github.com/tohin003/AgentGuard",
         tagline="A reliability layer for AI coding agents. Its core runs no LLM.",
         chips=["Python", "FastAPI", "QLoRA"]),
    dict(slug="boomboom", index="04", name="BoomBoom",
         url="https://github.com/tohin003/BoomBoom",
         tagline="A yellow music player for iPhone and Android with a real equaliser and amplifier.",
         chips=["Swift", "Kotlin", "Rust"]),   # iPhone app in Swift; Android app (release android-v1.0) in Kotlin with a Rust engine core
    dict(slug="agent-hub", index="05", name="Agent Hub",
         url="https://github.com/tohin003/agent-hub",
         tagline="Every AI coding agent on your Mac, in your pocket.",
         chips=["Swift", "SwiftUI", "Tailscale"]),
    dict(slug="ginie", index="06", name="Ginie",
         url="https://github.com/tohin003/ginie-releases",
         tagline="A compact, private AI workspace for macOS and Windows.",
         chips=["Electron", "TypeScript", "Next.js"]),
]

# --------------------------------------------------------------------------
# Design tokens
# --------------------------------------------------------------------------
BG, SURFACE, BORDER = "#0b0b0c", "#151517", "#2a2a2e"
CREAM, TAN, DIM = "#eee0ba", "#98846b", "#5e5548"
RED, RED_TEXT = "#f00009", "#ff3b44"
MONO = ('ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, '
        '"Liberation Mono", "DejaVu Sans Mono", monospace')
ADV = 0.62                      # width budget, em per character
W, H = 412, 190
PAD = 22
MOTIF_CX, MOTIF_CY = 354, 84    # motif centre; drawn in a +-36 box
STROKE = 1.6

TAGLINE_SIZE, TAGLINE_LINE = 12.5, 16
TAGLINE_MAX_CHARS = 34          # 34 * 0.62 * 12.5 = 263 px -> ends x=285, disc starts x=308
CHIP_SIZE, CHIP_H, CHIP_GAP, CHIP_PADX = 10.5, 22, 8, 9
CHIP_Y = 144


def wrap_balanced(text, max_chars):
    """Greedy wrap, then shrink the width while the line count stays the same."""
    def greedy(width):
        lines, cur = [], ""
        for word in text.split():
            trial = (cur + " " + word).strip()
            if len(trial) <= width or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
        return lines
    lines = greedy(max_chars)
    n = len(lines)
    width = max_chars
    while width > 10 and len(greedy(width - 1)) == n:
        width -= 1
    lines = greedy(width)
    assert len(lines) <= 3 and max(map(len, lines)) <= max_chars, (text, lines)
    return lines


def chip_width(label):
    return round(len(label) * ADV * CHIP_SIZE + 2 * CHIP_PADX)


# --------------------------------------------------------------------------
# Motifs.  Each returns (svg_fragment, css, defs).  Drawn around (0,0).
# Base styles are the reduced-motion still; animations only override them.
# --------------------------------------------------------------------------
def motif_pebble():
    css = """
.rg{transform-box:fill-box;transform-origin:center;vector-effect:non-scaling-stroke;animation:ripple 3.6s linear infinite}
.rg1{transform:scale(.42);opacity:.95;stroke:%(red)s;animation-delay:-.6s}
.rg2{transform:scale(.7);opacity:.55;animation-delay:-2.05s}
.rg3{transform:scale(1);opacity:.28;animation-delay:-3.25s}
@keyframes ripple{0%%{transform:scale(.3);opacity:0}12%%{opacity:.95}100%%{transform:scale(1);opacity:0}}
""" % dict(red=RED)
    svg = """
<ellipse class="s rg rg1" cx="0" cy="20" rx="34" ry="10"/>
<ellipse class="s rg rg2" cx="0" cy="20" rx="34" ry="10"/>
<ellipse class="s rg rg3" cx="0" cy="20" rx="34" ry="10"/>
<g transform="translate(0,-6)">
<path class="s" d="M-23,5 C-25,-6 -11,-14 4,-13 C19,-12 27,-3 23,6 C19,15 -4,17 -14,15 C-20,13 -22,10 -23,5Z"/>
<path class="s d2" d="M-14,-3 C-10,-7 -3,-8 3,-8"/>
</g>"""
    return svg, css, ""


def motif_truthstone():
    css = """
.ck{stroke-dasharray:44;stroke-dashoffset:0;animation:draw 4.4s ease-in-out infinite;animation-delay:-2.4s}
@keyframes draw{0%{stroke-dashoffset:44;opacity:1}30%{stroke-dashoffset:0;opacity:1}82%{stroke-dashoffset:0;opacity:1}94%{stroke-dashoffset:0;opacity:0}100%{stroke-dashoffset:44;opacity:0}}
"""
    svg = """
<path class="s" d="M-25,-5 L-11,-26 L12,-26 L26,-8 L18,21 L-14,23Z"/>
<path class="s d" d="M-11,-26 L-2,-8 M12,-26 L-2,-8 M-25,-5 L-2,-8 M26,-8 L-2,-8 M-2,-8 L-14,23 M-2,-8 L18,21"/>
<path class="ck" d="M-12,-1 L-3,8 L13,-13" stroke="%(bg)s" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<path class="s r ck" d="M-12,-1 L-3,8 L13,-13" stroke-width="2.2"/>""" % dict(bg=SURFACE)
    return svg, css, ""


def motif_agentguard():
    css = """
.scan{transform:translateY(2px);animation:sweep 3.4s ease-in-out infinite;animation-delay:-1.9s}
@keyframes sweep{0%{transform:translateY(-32px);opacity:0}12%{opacity:1}84%{opacity:1}100%{transform:translateY(34px);opacity:0}}
"""
    shield = "M0,-29 L22,-21 V2 C22,16 10,25 0,31 C-10,25 -22,16 -22,2 V-21Z"
    defs = '<clipPath id="shc"><path d="%s"/></clipPath>' % shield
    svg = """
<path class="s" d="%(sh)s"/>
<path class="s d" d="%(sh)s" transform="scale(.7)" vector-effect="non-scaling-stroke"/>
<g clip-path="url(#shc)"><g class="scan">
<rect x="-24" y="-12" width="48" height="12" fill="%(red)s" opacity=".16"/>
<line class="s r" x1="-24" y1="0" x2="24" y2="0"/>
</g></g>""" % dict(sh=shield, red=RED)
    return svg, css, defs


def motif_boomboom():
    base_y, full_h, bw, pitch = 27, 50, 6, 10
    # (still/from scale, to scale, duration s)
    bars = [(.36, .85, 1.15), (.64, .28, .85), (.92, .42, 1.45), (.5, .96, .95),
            (.78, .34, 1.3), (.4, .88, .8), (.58, .26, 1.05)]
    red_bar = 2
    css = ".bar{transform-box:fill-box;transform-origin:50% 100%;vector-effect:non-scaling-stroke}\n"
    svg = '<line class="s d" x1="-36" y1="%d" x2="36" y2="%d"/>\n' % (base_y + 4, base_y + 4)
    x0 = -(len(bars) - 1) * pitch / 2
    for i, (a, b, dur) in enumerate(bars):
        x = x0 + i * pitch - bw / 2
        top = base_y - full_h
        mk_y = base_y - full_h * a - 5
        css += (".b%(i)d{transform:scaleY(%(a)s);animation:bb%(i)d %(d)ss ease-in-out infinite alternate}"
                ".m%(i)d{animation:mm%(i)d %(d)ss ease-in-out infinite alternate}"
                "@keyframes bb%(i)d{from{transform:scaleY(%(a)s)}to{transform:scaleY(%(b)s)}}"
                "@keyframes mm%(i)d{from{transform:translateY(0)}to{transform:translateY(%(t).1fpx)}}\n"
                % dict(i=i, a=a, b=b, d=dur, t=full_h * (a - b)))
        svg += ('<rect class="s bar b%d" x="%.1f" y="%d" width="%d" height="%d"/>\n'
                % (i, x, top, bw, full_h))
        svg += ('<line class="s m%d %s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>\n'
                % (i, "r" if i == red_bar else "tn", x, mk_y, x + bw, mk_y))
    return svg, css, ""


def motif_agenthub():
    nodes = [(23, -26), (34, -8), (34, 12), (22, 29)]
    start = (-8, 0)
    D = 2.6
    css = ""
    svg = """
<rect class="s" x="-31" y="-21" width="23" height="42" rx="4.5"/>
<line class="s d" x1="-23" y1="-16" x2="-16" y2="-16"/>
<line class="s d" x1="-23" y1="16" x2="-16" y2="16"/>
<circle class="f r2" cx="-19.5" cy="0" r="2.2"/>
"""
    # links first (under the nodes)
    links = pulses = ""
    for i, (nx, ny) in enumerate(nodes):
        d = "M%d,%d L%d,%d" % (start[0], start[1], nx, ny)
        links += '<path class="s d" d="%s"/>\n' % d
        off = [-30, -62, -18, -78][i]          # still pulse position (pathLength 100)
        delay = -(6 - off) / 106 * D
        css += (".pl%(i)d{stroke-dashoffset:%(o)d;animation:pulse %(D)ss linear infinite;"
                "animation-delay:%(dl).2fs}\n" % dict(i=i, o=off, D=D, dl=delay))
        pulses += ('<path class="pl pl%d" d="%s" pathLength="100"/>\n' % (i, d))
    css += (".pl{fill:none;stroke:%s;stroke-width:2.4;stroke-linecap:round;stroke-dasharray:6 200}\n"
            "@keyframes pulse{from{stroke-dashoffset:6}to{stroke-dashoffset:-100}}\n" % RED)
    nds = "".join('<circle class="s nd" cx="%d" cy="%d" r="4.2"/>\n' % n for n in nodes)
    svg += links + pulses + nds
    return svg, css, ""


def motif_ginie():
    css = """
.sol{animation:solid 5.2s ease-in-out infinite;animation-delay:-.4s}
.gh{opacity:0;animation:ghost 5.2s ease-in-out infinite;animation-delay:-.4s}
@keyframes solid{0%,36%{opacity:1}50%,86%{opacity:.04}100%{opacity:1}}
@keyframes ghost{0%,36%{opacity:0}50%,86%{opacity:1}100%{opacity:0}}
"""
    svg = """
<g class="sol">
<rect class="s" x="-33" y="-25" width="60" height="44" rx="5"/>
<line class="s" x1="-33" y1="-14" x2="27" y2="-14"/>
<circle class="f" cx="-26.5" cy="-19.5" r="1.5"/><circle class="f" cx="-20.5" cy="-19.5" r="1.5"/><circle class="f" cx="-14.5" cy="-19.5" r="1.5"/>
<line class="s d" x1="-25" y1="-5" x2="2" y2="-5"/>
<line class="s d" x1="-25" y1="3" x2="-5" y2="3"/>
<line class="s d" x1="-25" y1="11" x2="9" y2="11"/>
</g>
<rect class="s gh" x="-33" y="-25" width="60" height="44" rx="5" stroke-dasharray="3.5 4.5"/>
<g transform="translate(22,17)">
<circle r="12.5" fill="%(sf)s"/>
<path class="s" d="M-9,0 Q0,-8 9,0 Q0,8 -9,0Z"/>
<circle class="f" r="2.2"/>
<line class="s r" x1="-8" y1="9" x2="8" y2="-9" stroke-width="2"/>
</g>""" % dict(sf=SURFACE)
    return svg, css, ""


MOTIFS = dict(pebble=motif_pebble, truthstone=motif_truthstone, agentguard=motif_agentguard,
              boomboom=motif_boomboom, **{"agent-hub": motif_agenthub}, ginie=motif_ginie)


# --------------------------------------------------------------------------
# Card assembly
# --------------------------------------------------------------------------
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build(card):
    motif_svg, motif_css, defs = MOTIFS[card["slug"]]()
    label = "%s: %s" % (card["name"], card["tagline"])

    lines = wrap_balanced(card["tagline"], TAGLINE_MAX_CHARS)
    tag = "".join('<text class="tg" x="%d" y="%d">%s</text>\n'
                  % (PAD, 89 + i * TAGLINE_LINE, esc(l)) for i, l in enumerate(lines))

    chips, x = "", PAD
    for c in card["chips"]:
        w = chip_width(c)
        chips += ('<rect class="chip" x="%d.5" y="%d.5" width="%d" height="%d" rx="%d"/>'
                  '<text class="ct" x="%.1f" y="%d">%s</text>\n'
                  % (x, CHIP_Y, w - 1, CHIP_H - 1, CHIP_H // 2, x + w / 2, CHIP_Y + 15, esc(c)))
        x += w + CHIP_GAP
    assert x - CHIP_GAP < 300, card["slug"]

    css = """
text{font-family:%(mono)s;font-variant-ligatures:none}
.s{fill:none;stroke:%(cream)s;stroke-width:%(sw)s;stroke-linecap:round;stroke-linejoin:round}
.d{stroke:%(dim)s}.d2{stroke:%(tan)s}.tn{stroke:%(tan)s}.r{stroke:%(red)s}
.f{fill:%(cream)s;stroke:none}.f.r2{fill:%(red)s}
.nd{fill:%(sf)s}
.ix{font-size:11px;font-weight:700;fill:%(redt)s}
.nm{font-size:22px;font-weight:700;fill:%(cream)s}
.tg{font-size:%(ts)spx;fill:%(tan)s}
.chip{fill:none;stroke:%(border)s;stroke-width:1}
.ct{font-size:%(cs)spx;fill:%(tan)s;text-anchor:middle}
%(mcss)s
@media (prefers-reduced-motion:reduce){*{animation:none !important}}
""" % dict(mono=MONO, cream=CREAM, sw=STROKE, dim=DIM, tan=TAN, red=RED, sf=SURFACE, redt=RED_TEXT,
           ts=TAGLINE_SIZE, cs=CHIP_SIZE, border=BORDER, mcss=motif_css.strip())
    css = "\n".join(l for l in css.splitlines() if l.strip())

    out = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %(W)d %(H)d" role="img" aria-label="%(al)s">
<title>%(al)s</title>
<defs>%(defs)s</defs>
<style>
%(css)s
</style>
<rect x=".5" y=".5" width="%(w1)d" height="%(h1)d" rx="13.5" fill="%(bg)s" stroke="%(border)s"/>
<text class="ix" x="%(pad)d" y="34">%(idx)s</text>
<line x1="%(rx)d" y1="30.5" x2="%(rx2)d" y2="30.5" stroke="%(dim)s" stroke-width="1"/>
<text class="nm" x="%(pad)d" y="64">%(name)s</text>
%(tag)s%(chips)s<circle cx="%(mx)d" cy="%(my)d" r="46" fill="%(sf)s"/>
<g transform="translate(%(mx)d,%(my)d)">%(motif)s</g>
<path d="M381,160 L391,150 M384,150 H391 V157" fill="none" stroke="%(dim)s" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
""" % dict(W=W, H=H, w1=W - 1, h1=H - 1, al=esc(label), defs=defs, css=css, bg=BG, border=BORDER,
           pad=PAD, idx=card["index"], rx=PAD + 22, rx2=PAD + 56, dim=DIM, name=esc(card["name"]),
           tag=tag, chips=chips, mx=MOTIF_CX, my=MOTIF_CY, sf=SURFACE, motif=motif_svg.strip())
    return out


def main():
    root = Path(__file__).resolve().parent.parent
    outdir = root / "assets" / "cards"
    outdir.mkdir(parents=True, exist_ok=True)
    for card in CARDS:
        svg = build(card)
        path = outdir / ("%s.svg" % card["slug"])
        path.write_text(svg, encoding="utf-8")
        print("%-24s %5d bytes" % (path.relative_to(root), len(svg.encode())))


if __name__ == "__main__":
    main()
