#!/usr/bin/env python3
"""Builds the animated SVGs used by the profile README.

    python3 assets/src/build.py <fonts-dir>

<fonts-dir> is assets/fonts from the KevinPratap.github.io repo (Geist and
Geist Mono, woff2). All type is converted to outlines, so the SVGs carry no
fonts and render the same everywhere. GitHub shows them through <img>, where
scripts are off: every animation here is CSS or SMIL.

Needs: fonttools, brotli, pillow.
"""
import math
import os
import random
import sys
import tempfile

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

BG, FG, ACID = "#07070b", "#f2efe9", "#d4ff3a"
DIM, MUTE = "#85827b", "#9a978f"
LINE = "rgba(242,239,233,.12)"
EASE = "cubic-bezier(.16,1,.3,1)"
W = 1200
OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

FONTS = {}


def load_fonts(d):
    for key, name in {
        "bold": "geist-latin-700-normal",
        "semi": "geist-latin-600-normal",
        "mono": "geist-mono-latin-500-normal",
    }.items():
        f = TTFont(os.path.join(d, name + ".woff2"))
        FONTS[key] = (f, f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm)


def n(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def advance(key, text, size, track=0.0):
    _, gs, cmap, upm = FONTS[key]
    return sum(gs[cmap[ord(c)]].width * size / upm + track for c in text) - track


def outline(key, text, size, x, y, track=0.0, anchor="start"):
    """Text as one SVG path. x,y is the baseline start (or middle / end)."""
    _, gs, cmap, upm = FONTS[key]
    w = advance(key, text, size, track)
    if anchor == "middle":
        x -= w / 2
    elif anchor == "end":
        x -= w
    pen = SVGPathPen(gs, ntos=lambda v: n(v))
    s = size / upm
    cx = x
    for c in text:
        g = gs[cmap[ord(c)]]
        g.draw(TransformPen(pen, (s, 0, 0, -s, cx, y)))
        cx += g.width * s + track
    return pen.getCommands(), x, w


def text(key, s, size, x, y, fill=FG, track=0.0, anchor="start", extra=""):
    d, _, _ = outline(key, s, size, x, y, track, anchor)
    return f'<path d="{d}" fill="{fill}"{extra}/>'


def arrow(x, y, size, fill=ACID, up=False):
    """A right arrow (or an up-right one) drawn as strokes; the fonts have none."""
    h = size * 0.34
    if up:
        return (f'<path d="M{n(x)},{n(y)} L{n(x+size*.62)},{n(y-size*.62)} M{n(x+size*.14)},{n(y-size*.62)} '
                f'H{n(x+size*.62)} V{n(y-size*.14)}" stroke="{fill}" stroke-width="{n(size*.11)}" fill="none" '
                f'stroke-linecap="square"/>')
    return (f'<path d="M{n(x)},{n(y-h)} H{n(x+size*.8)} M{n(x+size*.8-h)},{n(y-2*h)} L{n(x+size*.8)},{n(y-h)} '
            f'L{n(x+size*.8-h)},{n(y)}" stroke="{fill}" stroke-width="{n(size*.11)}" fill="none" stroke-linecap="square"/>')


def svg(h, css, body, title):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img">'
        f"<title>{title}</title>"
        f"<style>{css}@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>"
        f'<defs><clipPath id="frame"><rect width="{W}" height="{h}" rx="22"/></clipPath>'
        f'<pattern id="dots" width="28" height="28" patternUnits="userSpaceOnUse">'
        f'<circle cx="2" cy="2" r="1.1" fill="{FG}" opacity=".13"/></pattern></defs>'
        f'<g clip-path="url(#frame)"><rect width="{W}" height="{h}" fill="{BG}"/>{body}</g>'
        f'<rect x=".5" y=".5" width="{W-1}" height="{h-1}" rx="21.5" fill="none" stroke="{LINE}"/></svg>'
    )


def write(name, s):
    p = os.path.join(OUT, name)
    with open(p, "w") as f:
        f.write(s)
    print(f"{name}: {len(s)/1024:.0f} KB")


# ------------------------------------------------------------------ hero

TRACK = -3.5


def sample_points(lines, size, count, rng):
    """Random points inside the outlined glyphs of each (text, baseline-y) line."""
    font, _, _, upm = FONTS["bold"]
    with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as tmp:
        font.flavor = None
        font.save(tmp.name)
    pil = ImageFont.truetype(tmp.name, int(size))
    os.unlink(tmp.name)
    scale = size / int(size)
    H = 600
    im = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(im)
    for s, y in lines:
        _, x, _ = outline("bold", s, size, W / 2, y, TRACK, anchor="middle")
        cx = x
        _, gs, cmap, _ = FONTS["bold"]
        for c in s:
            dr.text((cx, y), c, font=pil, fill=255, anchor="ls")
            cx += gs[cmap[ord(c)]].width * size / upm + TRACK
    px = im.load()
    pts = []
    while len(pts) < count:
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        if px[int(x), int(y)] > 128:
            pts.append((x, y))
    return pts


def hero():
    rng = random.Random(7)
    H, T = 560, 14
    size = 152
    while advance("bold", "Kevin Pratap", size, TRACK) > 900:
        size -= 1
    y1, y2 = 268, 268 + size * 0.98
    name = outline("bold", "Kevin Pratap", size, W / 2, y1, TRACK, anchor="middle")[0] + \
        outline("bold", "Sidhu", size, W / 2, y2, TRACK, anchor="middle")[0]

    parts = []
    for x, y in sample_points([("Kevin Pratap", y1), ("Sidhu", y2)], size, 1800, rng):
        a, r = rng.uniform(0, math.tau), rng.uniform(160, 640)
        sx, sy = math.cos(a) * r, math.sin(a) * r * 0.7
        ex, ey = rng.uniform(260, 900), rng.uniform(-260, 90)
        delay = (x - 150) / 900 * 0.75 + rng.uniform(0, 0.25)
        fill = ACID if rng.random() < 0.04 else FG
        parts.append(
            f'<circle class="p" cx="{n(x)}" cy="{n(y)}" r="{n(rng.uniform(.8, 1.9))}" fill="{fill}" '
            f'style="--sx:{n(sx)}px;--sy:{n(sy)}px;--ex:{n(ex)}px;--ey:{n(ey)}px;animation-delay:{delay:.2f}s"/>'
        )

    dust = []
    for _ in range(150):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        dust.append(
            f'<circle class="d" cx="{n(x)}" cy="{n(y)}" r="{n(rng.uniform(.6, 1.5))}" fill="{FG}" '
            f'style="--dx:{n(rng.uniform(-60, 60))}px;--dy:{n(rng.uniform(-50, 50))}px;'
            f'animation-duration:{rng.uniform(7, 15):.1f}s;animation-delay:-{rng.uniform(0, 15):.1f}s"/>'
        )

    line = "interfaces for products that don't exist yet."
    ts, tx, ty = 21, 56, H - 50
    typed, _, tw = outline("mono", line, ts, tx, ty)
    step = advance("mono", "x", ts)

    css = f"""
.p{{opacity:0;animation:p {T}s linear infinite}}
@keyframes p{{
0%{{transform:translate(var(--sx),var(--sy));opacity:0}}
5%{{transform:translate(var(--sx),var(--sy));opacity:.85;animation-timing-function:{EASE}}}
30%{{transform:translate(0,0);opacity:1}}
35%{{transform:translate(0,0);opacity:1}}
40%{{transform:translate(0,0);opacity:0}}
74%{{transform:translate(0,0);opacity:0}}
78%{{transform:translate(0,0);opacity:1;animation-timing-function:cubic-bezier(.6,0,.9,.4)}}
94%,100%{{transform:translate(var(--ex),var(--ey));opacity:0}}}}
.d{{opacity:.22;animation:d 10s ease-in-out infinite alternate}}
@keyframes d{{to{{transform:translate(var(--dx),var(--dy));opacity:.05}}}}
.name{{animation:name {T}s linear infinite}}
@keyframes name{{0%,31%{{opacity:0}}39%,75%{{opacity:1}}80%,100%{{opacity:0}}}}
.sweep{{transform:translate(-400px,0) skewX(-18deg);animation:sweep {T}s linear infinite}}
@keyframes sweep{{0%,44%{{transform:translate(-400px,0) skewX(-18deg);animation-timing-function:cubic-bezier(.5,0,.2,1)}}
58%,100%{{transform:translate(1400px,0) skewX(-18deg)}}}}
.eyebrow{{animation:eyebrow {T}s linear infinite}}
@keyframes eyebrow{{0%,24%{{opacity:0;transform:translateY(8px);animation-timing-function:{EASE}}}36%,78%{{opacity:1;transform:none}}84%,100%{{opacity:0;transform:none}}}}
.typed{{animation:typed {T}s linear infinite}}
@keyframes typed{{0%,80%{{opacity:1}}84%,100%{{opacity:0}}}}
.cover{{transform:translate({n(tw+step)}px,0);animation:cover {T}s linear infinite}}
@keyframes cover{{0%,40%{{transform:translate(0,0);animation-timing-function:steps({len(line)+1},end)}}60%,100%{{transform:translate({n(tw+step)}px,0)}}}}
.caret{{animation:blink 1s steps(2,jump-none) infinite}}
@keyframes blink{{to{{opacity:0}}}}
.ring{{animation:ring 2.4s ease-in-out infinite}}
@keyframes ring{{50%{{r:19px;opacity:.45}}}}
"""
    body = (
        f'<defs><clipPath id="nm"><path d="{name}"/></clipPath></defs>'
        f'<rect width="{W}" height="{H}" fill="url(#dots)" opacity=".5"/>'
        + "".join(dust)
        + text("mono", "KP / PORTFOLIO 2026", 15, 56, 62, MUTE, track=2.2)
        + text("mono", "KEVINPRATAP.GITHUB.IO", 15, W - 84, 62, FG, track=2.2, anchor="end")
        + arrow(W - 72, 62, 16, ACID, up=True)
        + '<g class="eyebrow">'
        + text("mono", "MOTION DESIGNER  ·  AI ENGINEER  ·  MUMBAI", 17, W / 2, 138, MUTE, track=3.4, anchor="middle")
        + "</g>"
        + f'<g class="name"><path d="{name}" fill="{FG}"/>'
        f'<g clip-path="url(#nm)"><rect class="sweep" y="100" width="150" height="{H-200}" fill="{ACID}"/></g></g>'
        + "".join(parts)
        + f'<g class="typed"><path d="{typed}" fill="{FG}"/>'
        f'<g class="cover"><rect x="{tx-2}" y="{ty-24}" width="{n(tw+step+6)}" height="34" fill="{BG}"/>'
        f'<rect class="caret" x="{tx}" y="{ty-19}" width="{n(step*.9)}" height="24" fill="{ACID}"/></g></g>'
        + text("mono", "SCROLL", 14, W - 56, ty, MUTE, track=2.6, anchor="end")
        + f'<g><circle class="ring" r="14" fill="none" stroke="{FG}" stroke-width="1.4"/><circle r="3.2" fill="{FG}"/>'
        f'<animateMotion dur="{T}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.35;0.7;1" '
        f'keySplines=".4 0 .2 1;.4 0 .2 1;.4 0 .2 1" '
        f'path="M960,452 C1090,380 1110,210 930,150 C640,60 330,90 190,250 C120,380 620,520 960,452"/></g>'
    )
    write("hero.svg", svg(H, css, body, "Kevin Pratap Sidhu: a cloud of particles assembles into the name, then blows away"))


# ----------------------------------------------------------------- cards

def card_text(idx, kind, title_lines, cta):
    H = 340
    size = 78
    block = size * 1.02 * (len(title_lines) - 1)
    y = (H - block) / 2 + size * 0.36 + 4
    out = text("mono", idx, 16, 56, 62, ACID, track=2.4)
    out += text("mono", kind, 16, 56 + advance("mono", idx, 16, 2.4) + 22, 62, MUTE, track=2.4)
    for i, t in enumerate(title_lines):
        out += f'<g class="t" style="animation-delay:{i*.12:.2f}s">' + text("semi", t, size, 54, y + i * size * 1.02) + "</g>"
    cw = advance("mono", cta, 17, 1.6)
    out += text("mono", cta, 17, 56, H - 50, ACID, track=1.6)
    out += f'<g class="go">{arrow(56 + cw + 14, H - 50, 17)}</g>'
    return out


CARD_CSS = f"""
.go{{animation:go 1.8s {EASE} infinite}}
@keyframes go{{50%{{transform:translateX(9px)}}}}
"""


def trippin():
    H = 340
    route = "M660,262 C760,70 1010,40 1128,128"
    stops = [(660, 262, "BOM"), (1128, 128, "LIS")]
    css = CARD_CSS + f"""
.trail{{stroke-dasharray:1;stroke-dashoffset:1;animation:trail 6s linear infinite}}
@keyframes trail{{0%{{stroke-dashoffset:1;opacity:1;animation-timing-function:cubic-bezier(.45,0,.25,1)}}62%{{stroke-dashoffset:0;opacity:1}}86%{{stroke-dashoffset:0;opacity:1}}100%{{stroke-dashoffset:0;opacity:0}}}}
.ping{{transform-box:fill-box;transform-origin:center;animation:ping 6s ease-out infinite backwards}}
@keyframes ping{{0%{{transform:scale(.4);opacity:.9}}30%,100%{{transform:scale(3.2);opacity:0}}}}
.row{{transform-box:fill-box;transform-origin:left;transform:scaleX(1);animation:row 6s {EASE} infinite backwards}}
@keyframes row{{0%,8%{{transform:scaleX(0)}}30%,88%{{transform:scaleX(1)}}100%{{transform:scaleX(0)}}}}
.plane{{animation:plane 6s linear infinite}}
@keyframes plane{{0%,86%{{opacity:1}}94%,100%{{opacity:0}}}}
"""
    body = f'<rect x="600" width="600" height="{H}" fill="url(#dots)"/>'
    body += f'<path d="{route}" fill="none" stroke="{FG}" stroke-opacity=".28" stroke-width="1.6" stroke-dasharray="2 9" stroke-linecap="round"/>'
    body += f'<path class="trail" d="{route}" pathLength="1" fill="none" stroke="{ACID}" stroke-width="2.4" stroke-linecap="round"/>'
    for i, (x, y, code) in enumerate(stops):
        body += f'<circle class="ping" cx="{x}" cy="{y}" r="7" fill="none" stroke="{ACID}" stroke-width="1.2" style="animation-delay:{i*3.6:.1f}s"/>'
        body += f'<circle cx="{x}" cy="{y}" r="5" fill="{BG}" stroke="{FG}" stroke-width="1.8"/>'
        body += text("mono", code, 16, x - (34 if i == 0 else -2), y + (34 if i == 0 else -22), FG, track=2.4, anchor="start" if i == 0 else "middle")
    body += (f'<g class="plane"><path d="M-11,-7 L11,0 L-11,7 L-6,0 Z" fill="{ACID}"/>'
             f'<animateMotion dur="6s" repeatCount="indefinite" rotate="auto" calcMode="spline" keyTimes="0;0.62;1" '
             f'keySplines=".45 0 .25 1;0 0 1 1" keyPoints="0;1;1" path="{route}"/></g>')
    for i, wdt in enumerate([190, 150, 118]):
        yy = 214 + i * 26
        body += text("mono", f"DAY {i+1}", 13, 880, yy + 5, MUTE, track=2)
        body += f'<rect class="row" x="952" y="{yy-5}" width="{wdt}" height="9" rx="4.5" fill="{FG}" opacity="{.5 - i*.12:.2f}" style="animation-delay:{.9 + i*.5:.1f}s"/>'
    body += card_text("01", "TRAVEL PLANNER · 2026", ["Tripp’in AI"], "SEE THE REPO")
    write("work-trippin.svg", svg(H, css, body, "Tripp'in AI: a flight path draws itself between two airports while an itinerary fills in"))


def aitools():
    H = 340
    rng = random.Random(3)
    cols, rows, cell, gap = 14, 6, 30, 8
    x0, y0 = 1144 - cols * (cell + gap) + gap, 86
    dur = 5.0
    css = CARD_CSS + f"""
.c{{animation:c {dur}s linear infinite}}
@keyframes c{{0%{{fill-opacity:.07}}3%{{fill-opacity:.5}}22%,100%{{fill-opacity:.07}}}}
.hit{{animation:hit {dur}s linear infinite}}
@keyframes hit{{0%{{fill-opacity:.07;fill:{FG}}}3%,70%{{fill-opacity:1;fill:{ACID}}}86%,100%{{fill-opacity:.07;fill:{FG}}}}}
.scan{{animation:scan {dur}s linear infinite}}
@keyframes scan{{0%{{transform:translateX(0);opacity:1}}60%{{transform:translateX({cols*(cell+gap)}px);opacity:1}}64%,100%{{transform:translateX({cols*(cell+gap)}px);opacity:0}}}}
"""
    body = ""
    hits = set(rng.sample(range(cols * rows), 9))
    for r in range(rows):
        for c in range(cols):
            delay = c / cols * dur * 0.6
            cls = "hit" if r * cols + c in hits else "c"
            body += (f'<rect class="{cls}" x="{x0 + c*(cell+gap)}" y="{y0 + r*(cell+gap)}" width="{cell}" height="{cell}" rx="6" '
                     f'fill="{FG}" fill-opacity=".07" style="animation-delay:{delay:.2f}s"/>')
    body += f'<rect class="scan" x="{x0-5}" y="{y0-12}" width="2" height="{rows*(cell+gap)+16}" fill="{ACID}"/>'
    body += text("mono", "1,200+ TOOLS", 16, 1144, 62, FG, track=2.4, anchor="end")
    body += card_text("02", "DIRECTORY · 2026", ["AI Tools", "Directory"], "OPEN IT")
    write("work-aitools.svg", svg(H, css, body, "AI Tools Directory: a scan line crosses a grid of tiles and the matches light up"))


def cast():
    H = 340
    rng = random.Random(11)
    P = [(150, 290), (110, 265), (80, 235), (60, 205), (45, 178), (120, 190), (110, 140), (104, 105), (100, 75),
         (150, 182), (150, 125), (150, 88), (150, 55), (178, 190), (188, 140), (193, 105), (196, 78),
         (202, 205), (220, 168), (230, 140), (238, 115)]
    bones = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8), (5, 9), (9, 10), (10, 11), (11, 12),
             (9, 13), (13, 14), (14, 15), (15, 16), (13, 17), (0, 17), (17, 18), (18, 19), (19, 20)]
    tips = {4, 8, 12, 16, 20}
    css = CARD_CSS + """
.hand{transform-origin:150px 290px;animation:hand 5s ease-in-out infinite alternate}
@keyframes hand{from{transform:rotate(-5deg)}to{transform:rotate(6deg)}}
.tip{transform-box:fill-box;transform-origin:center;animation:tip 1.6s ease-in-out infinite}
@keyframes tip{50%{transform:scale(1.7)}}
.s{opacity:0;animation:s 2.6s cubic-bezier(.1,.7,.3,1) infinite}
@keyframes s{0%{transform:translate(0,0);opacity:1}65%{opacity:.85}100%{transform:translate(var(--x),var(--y));opacity:0}}
"""
    hand = ""
    for a, b in bones:
        hand += f'<path d="M{P[a][0]},{P[a][1]} L{P[b][0]},{P[b][1]}" stroke="{FG}" stroke-opacity=".55" stroke-width="2" stroke-linecap="round"/>'
    for i, (x, y) in enumerate(P):
        if i in tips:
            hand += f'<circle class="tip" cx="{x}" cy="{y}" r="5" fill="{ACID}" style="animation-delay:{i*.06:.2f}s"/>'
        else:
            hand += f'<circle cx="{x}" cy="{y}" r="4" fill="{BG}" stroke="{FG}" stroke-width="1.8"/>'
    sparks = ""
    for i in range(90):
        a = rng.uniform(-math.pi * 0.95, -math.pi * 0.05)
        r = rng.uniform(50, 170)
        tip = P[rng.choice([8, 12, 8, 16])]
        sparks += (f'<circle class="s" cx="{tip[0]}" cy="{tip[1]}" r="{n(rng.uniform(1.4, 3.2))}" fill="{ACID if rng.random()<.6 else FG}" '
                   f'style="--x:{n(math.cos(a)*r*1.25)}px;--y:{n(math.sin(a)*r*.6)}px;animation-delay:-{rng.uniform(0,2.6):.2f}s"/>')
    body = f'<rect x="600" width="600" height="{H}" fill="url(#dots)"/>'
    body += f'<g transform="translate(748,22) scale(.98)"><g class="hand">{sparks}{hand}</g></g>'
    body += text("mono", "21 LANDMARKS · ON DEVICE", 16, 1144, H - 50, MUTE, track=2.4, anchor="end")
    body += card_text("03", "HAND TRACKING · 2026", ["Cast"], "TRY THE DEMO")
    write("work-cast.svg", svg(H, css, body, "Cast: a tracked hand skeleton sways while particles stream from its fingertips"))


# --------------------------------------------------------------- systems

def systems():
    H = 250
    y = 128
    nodes = [(150, y, "SOURCE"), (390, y, "PLAN"), (640, y - 54, "AGENT"), (640, y, "AGENT"), (640, y + 54, "AGENT"),
             (890, y, "GATE"), (1090, y, "SHIP")]
    paths = [
        f"M150,{y} H390 C500,{y} 520,{y-54} 640,{y-54} C770,{y-54} 780,{y} 890,{y} H1090",
        f"M150,{y} H1090",
        f"M150,{y} H390 C500,{y} 520,{y+54} 640,{y+54} C770,{y+54} 780,{y} 890,{y} H1090",
    ]
    css = """
.gate{animation:gate 1.4s ease-in-out infinite}
@keyframes gate{50%{stroke-opacity:1;stroke-width:3}}
"""
    body = f'<rect width="{W}" height="{H}" fill="url(#dots)" opacity=".7"/>'
    for p in paths:
        body += f'<path d="{p}" fill="none" stroke="{FG}" stroke-opacity=".22" stroke-width="1.5"/>'
    for i, p in enumerate(paths):
        for k in range(3):
            body += (f'<circle r="4" fill="{ACID}"><animateMotion dur="4.2s" begin="-{(i*0.5 + k*1.4):.1f}s" '
                     f'repeatCount="indefinite" path="{p}"/></circle>')
    for x, yy, label in nodes:
        gate = label == "GATE"
        body += (f'<circle {"class=\"gate\" " if gate else ""}cx="{x}" cy="{yy}" r="{13 if gate else 9}" fill="{BG}" '
                 f'stroke="{ACID if gate else FG}" stroke-opacity="{.6 if gate else 1}" stroke-width="1.8"/>')
        if label != "AGENT":
            body += text("mono", label, 14, x, yy + 44, MUTE, track=2.4, anchor="middle")
    body += text("mono", "3 AGENTS", 14, 640, y + 96, MUTE, track=2.4, anchor="middle")
    body += text("mono", "SYSTEMS", 16, 56, 50, ACID, track=2.4)
    body += text("mono", "AGENTS, PIPELINES, QUALITY GATES", 16, 56 + advance("mono", "SYSTEMS", 16, 2.4) + 22, 50, MUTE, track=2.4)
    write("systems.svg", svg(H, css, body, "Systems: packets travel from a source through three agents and a quality gate"))


if __name__ == "__main__":
    load_fonts(sys.argv[1])
    hero()
    trippin()
    aitools()
    cast()
    systems()
