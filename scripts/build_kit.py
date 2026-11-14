#!/usr/bin/env python3
"""Generate the terminal-styled SVG kit (badges, headers, tagline).

Run from anywhere:  python3 scripts/build_kit.py
Deterministic; rewrites every file under assets/badges, assets/headers and
assets/tagline.svg.
"""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BG, BORDER, SURFACE = "#0b0b0c", "#2a2a2e", "#151517"
CREAM, TAN, DIM = "#eee0ba", "#98846b", "#5e5548"
RED, RED_TXT = "#f00009", "#ff3b44"
MONO = ('ui-monospace, SFMono-Regular, &quot;SF Mono&quot;, Menlo, Consolas, '
        '&quot;Liberation Mono&quot;, &quot;DejaVu Sans Mono&quot;, monospace')
CW = 0.6  # advance per character, in em, used for every textLength


def num(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return s or "0"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def write(rel, text):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def svg(w, h, title, body, css):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {num(w)} {num(h)}" '
        f'role="img" aria-label="{esc(title)}">\n'
        f'<title>{esc(title)}</title>\n<style>\n{css}</style>\n{body}</svg>\n'
    )


# ---------------------------------------------------------------- badges
ICONS = {  # drawn in a 14x14 box, stroke only
    "portfolio": '<path d="M3 11 L11 3 M4.5 3 H11 V9.5"/>',
    "linkedin": '<circle cx="7" cy="4.6" r="2.4"/><path d="M2.2 12.6 A4.8 4.4 0 0 1 11.8 12.6"/>',
    "email": '<rect x="1" y="2.5" width="12" height="9" rx="1.6"/><path d="M1.6 3.7 L7 8 L12.4 3.7"/>',
    "leetcode": '<path d="M4.8 3 L1.4 7 L4.8 11 M9.2 3 L12.6 7 L9.2 11 M7.8 2.4 L6.2 11.6"/>',
    "huggingface": '<circle cx="7" cy="7" r="6"/><path d="M4.4 8.2 Q7 11 9.6 8.2"/>'
                   '<circle cx="5" cy="5.5" r="0.5"/><circle cx="9" cy="5.5" r="0.5"/>',
    "resume": '<path d="M2.8 1.2 H8.6 L11.6 4.2 V12.8 H2.8 Z M8.6 1.2 V4.2 H11.6 M5 7.4 H9.4 M5 10 H9.4"/>',
}
LABELS = [("portfolio", "portfolio"), ("linkedin", "linkedin"), ("email", "email"),
          ("leetcode", "leetcode"), ("huggingface", "hugging face"), ("resume", "resume")]


def badge(key, label):
    primary = key == "portfolio"
    fs, pad, icon, gap = 13, 14, 14, 8
    tl = len(label) * fs * CW
    extra = 13 if primary else 0  # gap + dot
    w = math.ceil(pad + icon + gap + tl + extra + pad)
    tx = pad + icon + gap
    stroke = RED if primary else BORDER
    icol = RED_TXT if primary else TAN
    dot = ""
    if primary:
        cx = tx + tl + 10
        dot = (f'<circle class="halo" cx="{num(cx)}" cy="18" r="3" fill="{RED}"/>'
               f'<circle cx="{num(cx)}" cy="18" r="3" fill="{RED}"/>')
    css = (f'text{{font-family:{MONO};font-size:{fs}px;font-variant-ligatures:none}}\n'
           '.halo{transform-box:fill-box;transform-origin:center;animation:pulse 2.4s ease-in-out infinite}\n'
           '@keyframes pulse{0%,100%{transform:scale(1);opacity:.55}50%{transform:scale(2.3);opacity:0}}\n'
           '@media (prefers-reduced-motion: reduce){.halo{animation:none;opacity:0}}\n')
    body = (f'<rect x="0.5" y="0.5" width="{w-1}" height="35" rx="9.5" fill="{BG}" stroke="{stroke}"/>\n'
            f'<g transform="translate({pad} 11)" fill="none" stroke="{icol}" stroke-width="1.5" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICONS[key]}</g>\n'
            f'<text x="{tx}" y="22.5" fill="{CREAM}" textLength="{num(tl)}" lengthAdjust="spacing">{esc(label)}</text>\n'
            f'{dot}\n')
    write(f"assets/badges/{key}.svg", svg(w, 36, f"{label} link", body, css))
    return w


# --------------------------------------------------------------- headers
HEADERS = [("about", "cat about.md", "# who"),
           ("projects", "ls ~/projects", "# six things I built"),
           ("contact", "open --contact", "# say hello"),
           ("activity", "git log --graph", "# lately")]


def header(key, cmd, comment):
    fs, cfs = 15, 13
    x0 = 44
    tl = len(cmd) * fs * CW
    ctl = len(comment) * cfs * CW
    css = (f'text{{font-family:{MONO};font-variant-ligatures:none}}\n'
           '.cur{animation:blink 1.1s step-end infinite}\n'
           '@keyframes blink{0%,50%{opacity:1}50.01%,100%{opacity:0}}\n'
           '@media (prefers-reduced-motion: reduce){.cur{animation:none;opacity:1}}\n')
    body = (f'<rect x="0.5" y="0.5" width="839" height="47" rx="9.5" fill="{BG}" stroke="{BORDER}"/>\n'
            f'<path d="M22 17 L30 24 L22 31" fill="none" stroke="{RED}" stroke-width="2.2" '
            f'stroke-linecap="round" stroke-linejoin="round"/>\n'
            f'<text x="{x0}" y="29.2" font-size="{fs}" fill="{CREAM}" textLength="{num(tl)}" '
            f'lengthAdjust="spacing">{esc(cmd)}</text>\n'
            f'<rect class="cur" x="{num(x0+tl+2)}" y="15" width="{num(fs*CW)}" height="19" fill="{CREAM}"/>\n'
            f'<text x="{num(820-ctl)}" y="28.6" font-size="{cfs}" fill="{TAN}" textLength="{num(ctl)}" '
            f'lengthAdjust="spacing">{esc(comment)}</text>\n')
    write(f"assets/headers/{key}.svg", svg(840, 48, f"{cmd} {comment}", body, css))


# --------------------------------------------------------------- tagline
PHRASES = ["I build AI agents.", "And the backends they run on.",
           "And the checks that prove they did the work."]


def tagline():
    fs, x0 = 19, 52
    cw = fs * CW
    TYPE, DEL, HOLD, PAUSE, LEAD = 0.07, 0.035, (1.8, 1.8, 2.6), 0.4, 0.6
    t = LEAD
    segs = []  # (type_start, type_end, del_start, del_end, n)
    for p, hold in zip(PHRASES, HOLD):
        n = len(p)
        a = t; b = a + n * TYPE; c = b + hold; d = c + n * DEL
        segs.append((a, b, c, d, n))
        t = d + PAUSE
    total = round(t, 3)
    pc = lambda s: f"{s / total * 100:.4f}%"
    css = [f'text{{font-family:{MONO};font-size:{fs}px;font-variant-ligatures:none}}',
           '.cur{animation:blink 1s step-end infinite}',
           '@keyframes blink{0%,50%{opacity:1}50.01%,100%{opacity:0}}']
    body_clips, body_text = [], []
    for i, (p, (a, b, c, d, n)) in enumerate(zip(PHRASES, segs), 1):
        W = n * cw
        last = i == len(PHRASES)
        body_clips.append(f'<clipPath id="c{i}"><rect class="w{i}" x="{x0}" y="10" '
                          f'width="{num(W if last else 0)}" height="40"/></clipPath>')
        body_text.append(f'<text clip-path="url(#c{i})" x="{x0}" y="36.2" fill="{CREAM}" '
                         f'textLength="{num(W)}" lengthAdjust="spacing">{esc(p)}</text>')
        css.append(f'.w{i}{{animation:k{i} {num(total)}s infinite}}')
        css.append(f'@keyframes k{i}{{0%{{width:0}}'
                   f'{pc(a)}{{width:0;animation-timing-function:steps({n})}}'
                   f'{pc(b)}{{width:{num(W)}px}}'
                   f'{pc(c)}{{width:{num(W)}px;animation-timing-function:steps({n})}}'
                   f'{pc(d)}{{width:0}}100%{{width:0}}}}')
    # cursor travels with the same steps
    kf = ['0%{transform:translateX(0)}']
    for (a, b, c, d, n) in segs:
        W = n * cw
        kf.append(f'{pc(a)}{{transform:translateX(0);animation-timing-function:steps({n})}}')
        kf.append(f'{pc(b)}{{transform:translateX({num(W)}px)}}')
        kf.append(f'{pc(c)}{{transform:translateX({num(W)}px);animation-timing-function:steps({n})}}')
        kf.append(f'{pc(d)}{{transform:translateX(0)}}')
    kf.append('100%{transform:translateX(0)}')
    css.append(f'.mv{{animation:kc {num(total)}s infinite}}')
    css.append('@keyframes kc{' + ''.join(kf) + '}')
    still_w = len(PHRASES[-1]) * cw
    css.append('@media (prefers-reduced-motion: reduce){'
               '.w1,.w2,.w3,.mv,.cur{animation:none}.cur{opacity:1}}')
    body = ('<defs>' + ''.join(body_clips) + '</defs>\n'
            f'<rect x="0.5" y="0.5" width="839" height="59" rx="9.5" fill="{BG}" stroke="{BORDER}"/>\n'
            f'<path d="M24 21 L32 30 L24 39" fill="none" stroke="{RED}" stroke-width="2.4" '
            f'stroke-linecap="round" stroke-linejoin="round"/>\n'
            + '\n'.join(body_text) + '\n'
            # still state: cursor sits after the full third phrase
            f'<g class="mv" style="transform:translateX({num(still_w)}px)">'
            f'<rect class="cur" x="{num(x0+1)}" y="15" width="{num(cw-1)}" height="30" fill="{RED}"/></g>\n')
    write("assets/tagline.svg", svg(840, 60, " ".join(PHRASES), body, "\n".join(css) + "\n"))
    return total


def main():
    widths = {k: badge(k, l) for k, l in LABELS}
    for h in HEADERS:
        header(*h)
    total = tagline()
    print("badge widths:", widths, "row(8px gaps):", sum(widths.values()) + 8 * (len(widths) - 1))
    print("tagline loop:", total, "s")


if __name__ == "__main__":
    main()
