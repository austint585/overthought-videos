"""'You never wanted chocolate': a parody of the @cluberich "we could go up" motivational edit (ops/episodes/2026-11-11-
liver-go-up.md). White line-art motion graphics on black, built in HyperFrames (pipeline/hf/liver), timed to the
narration's words. The one color (liver red) is kept back for "raw liver".

python render_liver.py build                 write the HyperFrames project from out/liver/narration_fixed.json
                                             (or placeholder timings from the original when there is no narration yet)
python render_liver.py stills 1.0,9.5,...    build, then snapshot those times into out/liver/stills/
python render_liver.py render                build, render the picture, mix the sound, mux to out/liver/liver.mp4
python render_liver.py audio                 the same, but keep the last picture.mp4 and redo only the sound
"""
import json, os, re, shutil, subprocess, sys
from common import ROOT

HF = os.path.join(ROOT, "hf", "liver")
OUT = os.path.join(ROOT, "out", "liver")
W, H, FPS = 1080, 1920, 30
RED = "#C21A33"
TAIL = 6.4                                   # the music-only "larp" payoff after the last line

SCRIPT = [
    "We could stay here. Or we could go up.",
    "Do you not understand that?",
    "Are you not tired of eating the same chocolate they're currently eating, and afraid to eat like that for the rest of your life?",
    "So you might as well start now.",
    "And it's not, one more square. It's not, it's dark chocolate, it's healthy. It's not, I'll stop after Halloween.",
    "You never wanted chocolate.",
    "What you actually wanted... is raw liver.",
    "Why? Because there's always... There's always going to be cravings. There's always going to be leftover Halloween candy. There's always going to be the checkout aisle. So you might as well eat the liver now.",
    "You know what's okay? Gagging. Gagging is okay. You should gag. Your goal should be to gag as much as possible, so in the end, you'll have iron.",
    "But you know what is not okay? Chocolate.",
]
# where each line sat in the original (s), for placeholder timing before our narration exists
ORIG = [(0.0, 2.7), (3.1, 4.5), (4.9, 12.2), (12.4, 13.2), (13.6, 19.8), (20.2, 21.0), (21.1, 21.7), (22.2, 32.3),
        (32.9, 42.2), (42.8, 45.5)]

# ------------------------------------------------------------------ timing

def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())

def load_lines():
    p = os.path.join(OUT, "narration_fixed.json")
    if os.path.exists(p):
        return json.load(open(p)), True
    lines = []
    for text, (a, b) in zip(SCRIPT, ORIG):
        ws = text.split()
        step = (b - a) / len(ws)
        lines.append({"text": text, "start": a, "end": b,
                      "words": [{"w": w, "start": a + i * step, "end": a + (i + 0.9) * step} for i, w in enumerate(ws)]})
    return lines, False

class T:
    """Word times: T(i, 'word', n) is the start of the n-th occurrence of word in line i (absolute seconds)."""
    def __init__(self, lines):
        self.lines = lines
    def __call__(self, i, word, n=0, end=False):
        hits = [w for w in self.lines[i]["words"] if norm(w["w"]) == norm(word)]
        if not hits:
            raise KeyError(f"line {i + 1} has no word {word!r}: {[w['w'] for w in self.lines[i]['words']]}")
        w = hits[min(n, len(hits) - 1)]
        return w["end"] if end else w["start"]
    def start(self, i):
        return self.lines[i]["start"]
    def end(self, i):
        return self.lines[i]["end"]

# ------------------------------------------------------------------ shared look

CSS = """
#root { position: absolute; inset: 0; font-family: 'Montserrat', sans-serif; color: #fff; }
.t { position: absolute; left: 0; width: 1080px; text-align: center; font-weight: 800; letter-spacing: 0.12em;
     text-transform: uppercase; white-space: nowrap; }
.glow { text-shadow: 0 0 16px rgba(255,255,255,0.55), 0 0 44px rgba(255,255,255,0.22); }
.dim { color: rgba(255,255,255,0.55); }
.pillin { display: inline-block; background: #fff; color: #000; font-weight: 800; letter-spacing: 0.14em;
          border-radius: 999px; box-shadow: 0 0 26px rgba(255,255,255,0.25); }
.h { opacity: 0; }
.w { display: inline-block; }
svg { position: absolute; left: 0; top: 0; overflow: visible; }
"""

PERSON = '<g transform="translate({x},{y}) scale({s})"><circle cx="0" cy="-58" r="15" fill="#fff"/><rect x="-19" y="-38" width="38" height="38" rx="12" fill="#fff"/></g>'

def choc(x, y, w=56, h=88, sw=5, extra=""):
    """A chocolate bar in line art: outline, a 2x3 grid, a torn foil edge on top."""
    cells = "".join(f'<line x1="{x + w / 2}" y1="{y + 14}" x2="{x + w / 2}" y2="{y + h}" />' if i == 0 else "" for i in range(1))
    rows = "".join(f'<line x1="{x}" y1="{y + 14 + k * (h - 14) / 3}" x2="{x + w}" y2="{y + 14 + k * (h - 14) / 3}" />' for k in (1, 2))
    foil = f'<polyline points="{x},{y + 14} {x + w * 0.2},{y + 4} {x + w * 0.4},{y + 14} {x + w * 0.6},{y + 3} {x + w * 0.8},{y + 13} {x + w},{y + 5}" />'
    return (f'<g {extra} fill="none" stroke="#fff" stroke-width="{sw}" stroke-linejoin="round">'
            f'<rect x="{x}" y="{y + 14}" width="{w}" height="{h - 14}" rx="6" />{cells}{rows}{foil}</g>')

# a liver seen from the front: the big right lobe on the left, tapering to the thin left lobe, the ligament notch
LIVER_D = ("M -178 -34 C -164 -102 -40 -116 70 -96 C 150 -82 214 -64 204 -34 C 194 -6 128 14 66 34 "
           "C 4 56 -62 98 -126 88 C -184 78 -196 22 -178 -34 Z M 8 -100 C 0 -60 -6 -16 -30 34")

def liver(x, y, s, color="#fff", sw=6, extra=""):
    return (f'<g {extra} transform="translate({x},{y}) scale({s})"><path d="{LIVER_D}" fill="none" stroke="{color}" '
            f'stroke-width="{sw / s:.2f}" stroke-linecap="round" stroke-linejoin="round" pathLength="1"/></g>')

def words(id_, text, top, size, cls="glow", color=None):
    """A line of text split into word spans (#id-0, #id-1, ...) for per-word entrances."""
    style = f"top:{top}px;font-size:{size}px;" + (f"color:{color};" if color else "")
    spans = " ".join(f'<span class="w" id="{id_}-{k}">{w}</span>' for k, w in enumerate(text.split()))
    return f'<div class="t {cls}" id="{id_}" style="{style}">{spans}</div>', len(text.split())

def pill(id_, text, top, size, hidden=True):
    """A white pill, centered by a full-width row so GSAP can scale it without fighting a CSS transform."""
    return (f'<div class="t" id="{id_}" style="top:{top}px;{"opacity:0;" if hidden else ""}">'
            f'<span class="pillin" style="font-size:{size}px;padding:{size * 0.42:.0f}px {size * 1.05:.0f}px;">{text}</span></div>')

class TL:
    """GSAP lines for one scene, all times local to the scene (seconds)."""
    def __init__(self, t0, name=""):
        self.t0, self.js, self.name, self.hide, self.dash = t0, [], name, [], []
    def at(self, t):
        return max(0.0, t - self.t0)
    def set(self, sel, props, t=0.0):
        if t == 0.0 and props == "{opacity:0}":
            self.hide.append(sel)             # start hidden in CSS: a set at 0 does not render on the scene's first frame
        elif t == 0.0 and "strokeDasharray" in props:
            self.dash.append(sel)
        else:
            self.js.append(f'tl.set("{sel}", {props}, {t:.3f});')
    def to(self, sel, props, t):
        self.js.append(f'tl.to("{sel}", {props}, {t:.3f});')
    def fromto(self, sel, a, b, t):
        self.js.append(f'tl.fromTo("{sel}", {a}, {b}, {t:.3f});')
    # entrances and exits from ops/episodes/2026-11-11-liver-go-up.md and research_notes/2026-11-11_Directed_Motion_Style.md
    def draw_set(self, sel):
        pass                                   # draw-on lines start hidden in their markup (stroke-dashoffset="1")
    def blur_in(self, sel, t, d=0.16):
        self.fromto(sel, "{opacity:0, filter:'blur(8px)'}", f"{{opacity:1, filter:'blur(0px)', duration:{d}, ease:'power4.out'}}", t)
    def blur_out(self, sel, t, d=0.16):
        self.to(sel, f"{{opacity:0, filter:'blur(8px)', duration:{d}, ease:'power2.in'}}", t)
    def word_in(self, id_, times):
        for k, t in enumerate(times):
            self.blur_in(f"#{id_}-{k}", t, 0.13)
    def slam(self, sel, t, shake=True):
        self.fromto(sel, "{opacity:0, scale:1.25}", "{opacity:1, scale:1, duration:0.2, ease:'expo.out'}", t)
        if shake:
            for k, dx in enumerate((7, -6, 4, -2, 0)):
                self.to(sel, f"{{x:{dx}, duration:0.033, ease:'none'}}", t + 0.2 + k * 0.033)
    def pop(self, sel, t):
        self.fromto(sel, "{opacity:0, scale:0.92}", "{opacity:1, scale:1, duration:0.32, ease:'expo.out'}", t)
    def draw(self, sel, t, d=0.6, ease="power2.inOut"):
        self.fromto(sel, "{strokeDasharray:1, strokeDashoffset:1}", f"{{strokeDashoffset:0, duration:{d}, ease:'{ease}'}}", t)

def scene(name, t0, t1, body, tl):
    css = CSS + "".join(f"{s} {{ opacity: 0; }}\n" for s in tl.hide) + "".join(f"{s} {{ stroke-dasharray: 1; stroke-dashoffset: 1; }}\n" for s in tl.dash)
    return name, t0, t1, f"""<template>
  <style>{css}</style>
  <div id="root" data-composition-id="{name}" data-width="{W}" data-height="{H}">
   <div id="{name}-all" style="position:absolute;inset:0;">
{body}
   </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    {chr(10).join('    ' + j for j in tl.js)}
    window.__timelines["{name}"] = tl;
  </script>
</template>
"""

# ------------------------------------------------------------------ the scenes

def build_scenes(T_):
    sc = []
    cut = lambda i: T_.start(i) - 0.12                           # each scene cuts in just before its first word

    # 1. the choice: stay here, or go up (frame 0 is already drawn: the hook frame)
    t0, t1 = 0.0, cut(1)
    tl = TL(t0, "s1")
    sx, sy, stp = 430, 1120, 96
    steps = " ".join(f"{sx + k * stp},{sy - k * stp} {sx + (k + 1) * stp},{sy - k * stp}" for k in range(6))
    stairs = f"{sx},{sy} " + steps
    top = (sx + 6 * stp, sy - 6 * stp)
    body = f"""
    <svg width="{W}" height="{H}">
      <line id="s1-ground" x1="90" y1="{sy}" x2="{sx}" y2="{sy}" stroke="#fff" stroke-width="5" />
      {PERSON.format(x=190, y=sy, s=1.7)}
      {choc(268, sy - 118, 74, 118, 6, extra='id="s1-choc"')}
      <polyline id="s1-stairs" points="{stairs}" fill="none" stroke="#fff" stroke-width="5" pathLength="1" />
      <g id="s1-arrow"><line id="s1-arrow-l" x1="560" y1="1000" x2="560" y2="760" stroke="#fff" stroke-width="5" pathLength="1"/>
        <polyline id="s1-arrowhead" points="540,784 560,760 580,784" fill="none" stroke="#fff" stroke-width="5" /></g>
      <g id="s1-glow" style="filter: drop-shadow(0 0 18px rgba(255,255,255,0.9)) drop-shadow(0 0 50px rgba(255,255,255,0.5));">
        {liver(top[0] - 70, top[1] - 120, 0.5)}
      </g>
    </svg>
    <div class="t dim" id="s1-stay" style="top:{sy + 36}px;left:-310px;font-size:30px;">STAY HERE</div>
    <div class="t" id="s1-up" style="top:700px;left:20px;font-size:32px;">OR GO UP</div>
"""
    tl.set("#s1-stairs", "{strokeDasharray:1, strokeDashoffset:1}")
    tl.set("#s1-arrow-l", "{strokeDasharray:1, strokeDashoffset:1}")
    tl.set("#s1-arrowhead, #s1-up, #s1-glow", "{opacity:0}")
    tl.draw("#s1-stairs", tl.at(T_(0, "Or")), 0.75)
    tl.draw("#s1-arrow-l", tl.at(T_(0, "go")), 0.32, "power3.out")
    tl.to("#s1-arrowhead", "{opacity:1, duration:0.1}", tl.at(T_(0, "go")) + 0.28)
    tl.blur_in("#s1-up", tl.at(T_(0, "Or")))                 # on screen for the whole "or we could go up"
    tl.fromto("#s1-glow", "{opacity:0, scale:0.6, transformOrigin:'50% 50%'}", "{opacity:1, scale:1, duration:0.6, ease:'expo.out'}",
              tl.at(T_(0, "up")))
    tl.blur_out(f"#{tl.name}-all", tl.at(t1) - 0.16)
    sc.append(scene("s1", t0, t1, body, tl))

    # 2. do you not understand that?
    t0, t1 = cut(1), cut(2)
    tl = TL(t0, "s2")
    a, n1 = words("s2-a", "DO YOU NOT", 700, 64)
    b, n2 = words("s2-b", "UNDERSTAND THAT?", 790, 64)
    ws = [w["start"] for w in T_.lines[1]["words"]]
    tl.word_in("s2-a", [tl.at(x) for x in ws[:3]])
    tl.word_in("s2-b", [tl.at(x) for x in ws[3:5]])
    tl.blur_out("#s2-a, #s2-b", tl.at(t1) - 0.16)
    sc.append(scene("s2", t0, t1, f"    {a}\n    {b}", tl))

    # 3. the same chocolate life (a loop you keep orbiting)
    t0, t1 = cut(2), cut(3)
    tl = TL(t0, "s3")
    cx, cy, r = 540, 690, 205
    days = "".join(
        f'<text x="{cx + (r + 58) * __import__("math").cos(a_):.0f}" y="{cy + (r + 58) * __import__("math").sin(a_) + 11:.0f}" '
        f'font-size="33" font-weight="700" letter-spacing="2" text-anchor="middle" fill="rgba(255,255,255,0.45)">{d}</text>'
        for d, a_ in zip("MON TUE WED THU FRI SAT SUN".split(), [-1.5708 + k * 6.2832 / 7 for k in range(7)]))
    people = "".join(PERSON.format(x=330 + k * 140, y=1090, s=0.95) + choc(330 + k * 140 + 18, 1040, 24, 38, 3)
                     for k in range(4))
    body = f"""
    <div id="s3-loop">
      <svg width="{W}" height="{H}">
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#fff" stroke-width="4" />
        {days}
        <g id="s3-orbit">
          <g style="filter: drop-shadow(0 0 10px rgba(255,255,255,0.9));">{choc(cx - 14, cy - r - 22, 28, 44, 3)}</g>
        </g>
      </svg>
      <div class="t" style="top:{cy - 42}px;font-size:34px;">SAME</div>
      <div class="t" style="top:{cy + 2}px;font-size:34px;">CHOCOLATE LIFE</div>
    </div>
    {pill("s3-tired", "TIRED OF THE SAME CRAVING?", 206, 28)}
    <div id="s3-people"><svg width="{W}" height="{H}">{people}</svg></div>
    <div class="t dim" id="s3-eating" style="top:1112px;font-size:28px;">THEY'RE EATING IT</div>
    <div class="t glow" id="s3-afraid" style="top:1160px;font-size:44px;">AFRAID?</div>
    <svg width="{W}" height="{H}"><line id="s3-dash" x1="150" y1="1250" x2="930" y2="1250" stroke="#fff" stroke-width="3" stroke-dasharray="14 12" /></svg>
    <div class="t" id="s3-rest" style="top:1266px;font-size:28px;">FOR THE REST OF YOUR LIFE</div>
"""
    dur = t1 - t0
    tl.fromto("#s3-orbit", f"{{rotation:0, svgOrigin:'{cx} {cy}'}}", f"{{rotation:{360 * dur / 3.2:.1f}, svgOrigin:'{cx} {cy}', duration:{dur:.3f}, ease:'none'}}", 0)
    tl.blur_in("#s3-loop", 0.0, 0.2)
    tl.set("#s3-tired, #s3-people, #s3-eating, #s3-afraid, #s3-rest", "{opacity:0}")
    tl.set("#s3-dash", "{opacity:0}")
    tl.pop("#s3-tired", tl.at(T_(2, "tired")))
    tl.to("#s3-loop", "{y:-60, scale:0.86, transformOrigin:'50% 36%', duration:0.6, ease:'power2.inOut'}", tl.at(T_(2, "they're")) - 0.2)
    tl.fromto("#s3-people", "{opacity:0, y:20}", "{opacity:1, y:0, duration:0.4, ease:'expo.out'}", tl.at(T_(2, "they're")))
    tl.blur_in("#s3-eating", tl.at(T_(2, "eating", 1)))
    tl.slam("#s3-afraid", tl.at(T_(2, "afraid")), shake=False)
    tl.fromto("#s3-dash", "{opacity:0, scaleX:0, transformOrigin:'0% 50%'}", "{opacity:1, scaleX:1, duration:0.7, ease:'power2.inOut'}",
              tl.at(T_(2, "rest")))
    tl.blur_in("#s3-rest", tl.at(T_(2, "for")))
    tl.blur_out(f"#{tl.name}-all", tl.at(t1) - 0.16)
    sc.append(scene("s3", t0, t1, body, tl))

    # 4. so you might as well start now
    t0, t1 = cut(3), cut(4)
    tl = TL(t0, "s4")
    a, _ = words("s4-a", "SO YOU MIGHT AS WELL", 690, 30, cls="")
    ws = [w["start"] for w in T_.lines[3]["words"]]
    tl.word_in("s4-a", [tl.at(x) for x in ws[:5]])
    tl.pop("#s4-pill", tl.at(T_(3, "start")))
    tl.blur_out("#s4-a, #s4-pill", tl.at(t1) - 0.16)
    sc.append(scene("s4", t0, t1, f"    {a}\n    {pill('s4-pill', 'START NOW', 760, 58)}", tl))

    # 5. the excuses, crossed out one by one
    t0, t1 = cut(4), cut(5)
    tl = TL(t0, "s5")
    cards = [("ONE MORE SQUARE", "one", "square"), ("IT'S DARK, IT'S HEALTHY", "dark", "healthy"),
             ("AFTER HALLOWEEN", "stop", "Halloween")]
    body = pill("s5-not", "IT'S NOT...", 300, 30)
    for k, (txt, w_in, w_x) in enumerate(cards):
        y = 470 + k * 250
        body += f"""
    <div id="s5-c{k}" style="position:absolute;left:250px;top:{y}px;width:580px;height:200px;border:4px solid #fff;border-radius:18px;">
      <div style="position:absolute;left:0;right:0;top:0;height:52px;border-bottom:3px solid #fff;font:800 28px Montserrat;letter-spacing:0.16em;text-align:center;line-height:52px;">LET'S STOP</div>
      <div class="t" style="width:580px;top:96px;font-size:{30 if len(txt) > 16 else 36}px;">{txt}</div>
      <svg width="580" height="200"><line id="s5-x{k}a" x1="150" y1="58" x2="430" y2="194" stroke="#fff" stroke-width="7" stroke-linecap="round" pathLength="1"/>
        <line id="s5-x{k}b" x1="430" y1="58" x2="150" y2="194" stroke="#fff" stroke-width="7" stroke-linecap="round" pathLength="1"/></svg>
    </div>"""
        tl.set(f"#s5-x{k}a, #s5-x{k}b", "{strokeDasharray:1, strokeDashoffset:1}")
        tl.set(f"#s5-c{k}", "{opacity:0}")
        tl.fromto(f"#s5-c{k}", "{opacity:0, y:24}", "{opacity:1, y:0, duration:0.35, ease:'expo.out'}", tl.at(T_(4, w_in)) - 0.1)
        tx = tl.at(T_(4, w_x, end=True))
        tl.draw(f"#s5-x{k}a", tx - 0.05, 0.14, "power3.out")
        tl.draw(f"#s5-x{k}b", tx + 0.06, 0.14, "power3.out")
        tl.to(f"#s5-c{k}", "{opacity:0.45, duration:0.25}", tx + 0.3)
    tl.set("#s5-not", "{opacity:0}")
    tl.pop("#s5-not", tl.at(T_(4, "not")))
    tl.blur_out(f"#{tl.name}-all", tl.at(t1) - 0.16)
    sc.append(scene("s5", t0, t1, body, tl))

    # 6. THE BIG MOMENT: you never wanted chocolate ... raw liver (the only color in the film)
    t0, t1 = cut(5), cut(7)
    tl = TL(t0, "s6")
    a, _ = words("s6-a", "YOU NEVER WANTED", 660, 44)
    b, _ = words("s6-b", "WHAT YOU ACTUALLY WANTED", 600, 32, cls="dim")
    body = f"""
    {a}
    <div class="t glow" id="s6-choc" style="top:740px;font-size:118px;">CHOCOLATE</div>
    {b}
    <div id="s6-flash" style="position:absolute;inset:0;background:radial-gradient(ellipse at 50% 45%, rgba(194,26,51,0.38) 0%, rgba(194,26,51,0) 60%);"></div>
    <svg width="{W}" height="{H}" id="s6-liv" style="filter: drop-shadow(0 0 14px rgba(194,26,51,0.95)) drop-shadow(0 0 40px rgba(194,26,51,0.55));">
      {liver(540, 520, 0.95, RED, 7)}
    </svg>
    <div class="t" id="s6-raw" style="top:780px;font-size:124px;color:{RED};text-shadow:0 0 18px rgba(194,26,51,0.85),0 0 60px rgba(194,26,51,0.45);">RAW LIVER</div>
"""
    ws5 = [w["start"] for w in T_.lines[5]["words"]]
    tl.set("#s6-choc, #s6-flash, #s6-liv, #s6-raw", "{opacity:0}")
    tl.word_in("s6-a", [tl.at(x) for x in ws5[:3]])
    tl.slam("#s6-choc", tl.at(T_(5, "chocolate")), shake=False)
    tw = tl.at(T_(6, "What"))
    tl.set("#s6-a, #s6-choc", "{opacity:0}", tw - 0.04)                       # a hard cut, no fade
    ws6 = [w["start"] for w in T_.lines[6]["words"]]
    tl.word_in("s6-b", [tl.at(x) for x in ws6[:4]])
    tr = tl.at(T_(6, "raw"))
    tl.set("#s6-b", "{opacity:0}", tr - 0.04)
    tl.slam("#s6-raw", tr)
    tl.fromto("#s6-flash", "{opacity:0}", "{opacity:1, duration:0.06}", tr)
    tl.to("#s6-flash", "{opacity:0.35, duration:0.9, ease:'power2.out'}", tr + 0.1)
    tl.set("#s6-liv path", "{strokeDasharray:1, strokeDashoffset:1}")
    tl.to("#s6-liv", "{opacity:1, duration:0.01}", tr)
    tl.draw("#s6-liv path", tr, 0.45, "power3.out")
    tl.fromto("#s6-liv", "{scale:1, transformOrigin:'50% 27%'}", "{scale:1.07, duration:0.12, ease:'power2.out', yoyo:true, repeat:1}", tr + 0.5)
    tl.blur_out(f"#{tl.name}-all", tl.at(t1) - 0.16)
    sc.append(scene("s6", t0, t1, body, tl))

    # 7. there's always going to be... (bars)
    t0, t1 = cut(7), cut(8)
    tl = TL(t0, "s7")
    gy = 1120
    bars = [("CRAVINGS", "cravings", 230), ("HALLOWEEN<br>CANDY", "leftover", 330), ("CHECKOUT<br>AISLE", "checkout", 430)]
    body = f"""
    <div class="t glow" id="s7-why" style="top:720px;font-size:70px;">WHY?</div>
    <div id="s7-set">
      <svg width="{W}" height="{H}"><line x1="110" y1="{gy}" x2="970" y2="{gy}" stroke="#fff" stroke-width="4"/>{PERSON.format(x=190, y=gy, s=1.6)}</svg>
    </div>
    {pill("s7-pill", "THERE'S ALWAYS GOING TO BE", 330, 30)}
    {pill("s7-pill2", "SO YOU MIGHT AS WELL EAT IT NOW", 330, 30)}
    <div class="t dim" id="s7-always" style="top:{gy + 28}px;font-size:30px;">ALWAYS</div>
    <div class="t glow" id="s7-anyway" style="top:{gy + 70}px;font-size:40px;">ANYWAY</div>
"""
    for k, (lab, w_in, h) in enumerate(bars):
        x = 330 + k * 230
        body += f"""
    <div id="s7-b{k}" style="position:absolute;left:{x}px;top:{gy - h}px;width:150px;height:{h}px;background:#fff;border-radius:8px 8px 0 0;box-shadow:0 0 22px rgba(255,255,255,0.35);"></div>
    <div class="t" id="s7-l{k}" style="left:{x + 75 - 540}px;top:{gy - h - (50 if '<br>' not in lab else 86)}px;font-size:28px;line-height:1.2;">{lab}</div>"""
        tl.set(f"#s7-b{k}, #s7-l{k}", "{opacity:0}")
        tb = tl.at(T_(7, w_in))
        tl.fromto(f"#s7-b{k}", "{opacity:1, scaleY:0, transformOrigin:'50% 100%'}", "{opacity:1, scaleY:1, duration:0.45, ease:'expo.out'}", tb)
        tl.blur_in(f"#s7-l{k}", tb + 0.1)
    tl.set("#s7-set, #s7-pill, #s7-pill2, #s7-always, #s7-anyway", "{opacity:0}")
    tl.slam("#s7-why", tl.at(T_(7, "Why")), shake=False)
    tb0 = tl.at(T_(7, "because"))
    tl.blur_out("#s7-why", tb0 - 0.05)
    tl.fromto("#s7-set", "{opacity:0}", "{opacity:1, duration:0.25}", tb0)
    tl.pop("#s7-pill", tl.at(T_(7, "There's", 1)) - 0.1)
    tl.blur_in("#s7-always", tl.at(T_(7, "always", 2)))
    tso = tl.at(T_(7, "So"))
    tl.blur_out("#s7-pill", tso - 0.08, 0.1)
    tl.pop("#s7-pill2", tso)
    tl.slam("#s7-anyway", tl.at(T_(7, "now")), shake=False)
    tl.blur_out(f"#{tl.name}-all", tl.at(t1) - 0.16)
    sc.append(scene("s7", t0, t1, body, tl))

    # 8. gagging is okay; gag as much as possible; the star is iron
    t0, t1 = cut(8), cut(9)
    tl = TL(t0, "s8")
    q, _ = words("s8-q", "YOU KNOW WHAT'S OKAY?", 720, 40)
    sx, sy, st = 160, 1150, 8
    sw_, sh_ = (930 - sx) / st, (1150 - 470) / st
    pts = f"{sx},{sy} " + " ".join(f"{sx + k * sw_:.0f},{sy - k * sh_:.0f} {sx + (k + 1) * sw_:.0f},{sy - k * sh_:.0f}" for k in range(st))
    xs = "".join(f'<g id="s8-x{k}" style="opacity:0"><line x1="{sx + k * sw_ + sw_ / 2 - 12:.0f}" y1="{sy - k * sh_ - 34:.0f}" x2="{sx + k * sw_ + sw_ / 2 + 12:.0f}" y2="{sy - k * sh_ - 10:.0f}"/>'
                 f'<line x1="{sx + k * sw_ + sw_ / 2 + 12:.0f}" y1="{sy - k * sh_ - 34:.0f}" x2="{sx + k * sw_ + sw_ / 2 - 12:.0f}" y2="{sy - k * sh_ - 10:.0f}"/></g>'
                 for k in range(st))
    star = " ".join(f"{870 + (34 if k % 2 == 0 else 14) * __import__('math').cos(-1.5708 + k * 3.14159 / 5):.1f},"
                    f"{400 + (34 if k % 2 == 0 else 14) * __import__('math').sin(-1.5708 + k * 3.14159 / 5):.1f}" for k in range(10))
    body = f"""
    {q}
    <div class="t glow" id="s8-gag" style="top:700px;font-size:128px;">GAGGING</div>
    <div class="t" id="s8-ok" style="top:860px;font-size:30px;">&#10003;&nbsp; IS OKAY</div>
    {pill("s8-should", "YOU SHOULD GAG", 940, 30)}
    <div id="s8-stairs" style="opacity:0">
      <svg width="{W}" height="{H}">
        <polyline id="s8-steps" points="{pts}" fill="none" stroke="#fff" stroke-width="4" pathLength="1"/>
        <g stroke="#fff" stroke-width="5" stroke-linecap="round">{xs}</g>
        <polygon id="s8-star" points="{star}" fill="#fff" style="opacity:0;filter: drop-shadow(0 0 14px rgba(255,255,255,0.95)) drop-shadow(0 0 40px rgba(255,255,255,0.5));"/>
      </svg>
      <div class="t" id="s8-count" style="left:-300px;top:340px;font-size:34px;">GAGS: <span id="s8-n">0</span></div>
      <div class="t dim" id="s8-end" style="left:330px;top:318px;font-size:28px;opacity:0;">IN THE END</div>
      <div class="t glow" id="s8-iron" style="left:330px;top:446px;font-size:34px;opacity:0;">IRON</div>
    </div>
    {pill("s8-much", "GAG AS MUCH AS POSSIBLE", 230, 30)}
"""
    ws7 = [w["start"] for w in T_.lines[8]["words"]]
    tl.set("#s8-gag, #s8-ok, #s8-should, #s8-much", "{opacity:0}")
    tl.word_in("s8-q", [tl.at(x) for x in ws7[:4]])
    tg = tl.at(T_(8, "Gagging"))
    tl.set("#s8-q", "{opacity:0}", tg - 0.03)
    tl.slam("#s8-gag", tg)
    tl.blur_in("#s8-ok", tl.at(T_(8, "okay", 1)))
    tl.pop("#s8-should", tl.at(T_(8, "should")))
    tgo = tl.at(T_(8, "Your"))
    tl.blur_out("#s8-gag, #s8-ok, #s8-should", tgo - 0.12)
    tl.set("#s8-steps", "{strokeDasharray:1, strokeDashoffset:1}")
    tl.to("#s8-stairs", "{opacity:1, duration:0.05}", tgo)
    tl.draw("#s8-steps", tgo, 0.7)
    tend = tl.at(T_(8, "iron"))
    gap = (tend - 0.3 - (tgo + 0.5)) / st
    for k in range(st):
        tk = tgo + 0.5 + k * gap
        tl.fromto(f"#s8-x{k}", "{opacity:0, scale:1.4, transformOrigin:'50% 50%'}", "{opacity:1, scale:1, duration:0.12, ease:'expo.out'}", tk)
        tl.set("#s8-n", f"{{textContent:'{k + 1}'}}", tk)
    tl.pop("#s8-much", tl.at(T_(8, "much")))
    tl.blur_in("#s8-end", tl.at(T_(8, "end")))
    tl.fromto("#s8-star", "{opacity:0, scale:0.3, transformOrigin:'50% 50%'}", "{opacity:1, scale:1, duration:0.5, ease:'back.out(1.6)'}", tend)
    tl.blur_in("#s8-iron", tend + 0.1)
    tl.blur_out(f"#{tl.name}-all", tl.at(t1) - 0.16)
    sc.append(scene("s8", t0, t1, body, tl))

    # 9. but you know what is not okay? chocolate.
    t0 = cut(9)
    t1 = T_.end(9) + 1.5                                    # the punchline holds dead still before the payoff
    tl = TL(t0, "s9")
    a, _ = words("s9-a", "BUT YOU KNOW", 640, 32, cls="dim")
    b, _ = words("s9-b", "WHAT IS NOT OKAY?", 700, 46)
    ws9 = [w["start"] for w in T_.lines[9]["words"]]
    body = f"""
    {a}
    {b}
    <div class="t glow" id="s9-choc" style="top:708px;font-size:106px;">CHOCOLATE</div>
    <div class="t" id="s9-not" style="top:870px;font-size:30px;">IS NOT OKAY</div>
"""
    tl.set("#s9-choc, #s9-not", "{opacity:0}")
    tl.word_in("s9-a", [tl.at(x) for x in ws9[:3]])
    tl.word_in("s9-b", [tl.at(x) for x in ws9[3:7]])
    tc = tl.at(T_(9, "Chocolate"))
    tl.set("#s9-a, #s9-b", "{opacity:0}", tc - 0.03)
    tl.slam("#s9-choc", tc)
    tl.blur_in("#s9-not", tc + 0.22)
    tl.to("#s9-choc, #s9-not", "{opacity:0, duration:0.5, ease:'power2.in'}", tl.at(t1) - 0.5)
    sc.append(scene("s9", t0, t1, body, tl))
    return sc

# ------------------------------------------------------------------ the project

def build():
    lines, real = load_lines()
    T_ = T(lines)
    scenes = build_scenes(T_)
    end_speech = scenes[-1][2]
    total = end_speech + TAIL
    os.makedirs(os.path.join(HF, "compositions"), exist_ok=True)
    os.makedirs(os.path.join(HF, "assets"), exist_ok=True)
    hosts = []
    for k, (name, t0, t1, html) in enumerate(scenes):
        open(os.path.join(HF, "compositions", f"{name}.html"), "w", encoding="utf-8").write(html)
        hosts.append(f'      <div id="{name}" data-composition-id="{name}" data-composition-src="compositions/{name}.html" '
                     f'data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="{k + 1}" data-track-kind="graphics" '
                     f'data-width="{W}" data-height="{H}"></div>')
    broll = os.path.join(HF, "assets", "broll.mp4")
    payoff = (f'      <video id="broll" class="clip" src="assets/broll.mp4" muted playsinline data-start="{end_speech:.3f}" '
              f'data-duration="{TAIL:.3f}" data-track-index="20" style="position:absolute;left:0;top:0;width:{W}px;height:{H}px;object-fit:cover;z-index:20;"></video>'
              if os.path.exists(broll) else
              f'      <div id="broll" class="clip" data-start="{end_speech:.3f}" data-duration="{TAIL:.3f}" data-track-index="20" '
              f'style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#555;font:800 40px Montserrat;z-index:20;">LIVER B-ROLL HERE</div>')
    note_t = total - 4.6
    index = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; background: #000; }}
      #bg {{ position: absolute; inset: 0; background: radial-gradient(ellipse 70% 45% at 50% 40%, #1a1a1a 0%, #0a0a0a 55%, #000 100%); }}
      #note {{ position: absolute; left: 50%; top: 1150px; transform: translateX(-50%); width: 860px; text-align: center;
               font: 700 30px Montserrat; letter-spacing: 0.06em; color: #fff; background: rgba(0,0,0,0.62);
               border: 2px solid rgba(255,255,255,0.7); border-radius: 18px; padding: 16px 22px; z-index: 30; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-fps="{FPS}" data-width="{W}" data-height="{H}">
      <div id="bg"></div>
{chr(10).join(hosts)}
{payoff}
      <div id="note" class="clip" data-start="{note_t:.3f}" data-duration="{total - note_t:.3f}" data-track-index="21">
        <div id="note-in">FOR THE RECORD: DARK CHOCOLATE HAS 228 MG MAGNESIUM PER 100 G. RAW LIVER HAS 18. (USDA)</div>
      </div>
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo("#note-in", {{ opacity: 0, filter: 'blur(6px)' }}, {{ opacity: 1, filter: 'blur(0px)', duration: 0.2, ease: 'power4.out' }}, {note_t:.3f});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    open(os.path.join(HF, "index.html"), "w", encoding="utf-8").write(index)
    json.dump({"lines": lines, "real_narration": real, "end_speech": end_speech, "total": total,
               "scenes": [(n, round(a, 3), round(b, 3)) for n, a, b, _ in scenes]},
              open(os.path.join(OUT, "timing.json"), "w"), indent=1)
    print(f"built {HF}: {len(scenes)} scenes, speech ends {end_speech:.2f} s, total {total:.2f} s"
          + ("" if real else " (placeholder timing from the original)"))
    return total

def hf(*args, timeout=900):
    r = subprocess.run(["npx", "hyperframes", *args], cwd=HF, capture_output=True, text=True, timeout=timeout, shell=True)
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode, "\n".join(l for l in out.splitlines() if "npm notice" not in l)

# ------------------------------------------------------------------ sound (recorded effects from the Sonniss GDC 2026 bundle)

SFX = {
    "hit": "Cinematic Sound Design - Ultra Transitions & Impacts/Impact Hit Rapid Chord Reverb.wav",
    "splat": "344 Audio - Elemental Palette Designed Vol. 1/WATRMisc_Water, Liquid Impact, Bubble, Sci Fi, Hit 04_344 Audio_Elemental Palette Designed Vol 1.wav",
    "punch": "Epic Stock Media - Anime Game/FGHTImpt_Combat Punch Impact Light Hit Delay Crunchy Vintage Quick Smack 05_ESM_AG.wav",
    "woosh": "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav",
    "snap": "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav",
    "pop": "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav",
    "debris": "Cinematic Sound Design - Colossal Impacts/Woosh Debris.wav",
    "sweep": "Cinematic Sound Design - Colossal Impacts/Impact Cut Sweep.wav",
    "braam": "Cinematic Sound Design - Ultra Transitions & Impacts/Transition Braam Slow Dark Creepy.wav",
    "flash": "344 Audio - Car Foley Vol. 1/VEHInt_LIGHTING CONTROL, RELEASE, HEADLIGHT FLASH_344 Audio_Car Foley Vol 1.wav",
}
MUSIC = os.path.join(OUT, "music.wav")       # the bed Austin picks (see the episode file); none until then
MUSIC_GAIN = 0.32

def build_audio(lines, total, path):
    import numpy as np
    import sfx
    from common import new_track, add, save_wav, SR
    from render_led import common_load
    T_ = T(lines)
    tr = new_track(total)
    voice = common_load(os.path.join(OUT, "narration_fixed.wav"))[:len(tr)]
    tr[:len(voice)] += voice
    if os.path.exists(MUSIC):
        m = common_load(MUSIC)[:len(tr)] * MUSIC_GAIN
        tr[:len(m)] += m
    hit = lambda t, key, gain, **kw: add(tr, t, sfx.clip(SFX[key], **kw), gain)
    hit(T_(0, "Or") - 0.05, "woosh", 0.06)
    for w in ("square", "healthy", "Halloween"):
        hit(T_(4, w, end=True) - 0.03, "snap", 0.1)
    hit(T_(5, "chocolate") - 0.02, "punch", 0.1)
    hit(T_(6, "raw") - 0.03, "hit", 0.3)                       # the big moment: the loudest sound in the film
    hit(T_(6, "raw") + 0.02, "splat", 0.1)
    for w in ("cravings", "leftover", "checkout"):
        hit(T_(7, w), "pop", 0.08)
    hit(T_(8, "Gagging") - 0.02, "punch", 0.12)
    hit(T_(8, "iron"), "snap", 0.1)
    hit(T_(9, "Chocolate") - 0.02, "punch", 0.14)
    # the payoff (no voice): sound it like a car ad, quieter than the raw liver hit, so it is never 6 s of silence
    e = total - TAIL
    hit(e - 0.15, "debris", 0.12)
    hit(e + 0.05, "braam", 0.13, hp=70)                          # high-passed: no long sub-bass under the B-roll
    hit(e + 2.2 - 0.03, "flash", 0.16)                           # the sill plate lights up like a car's
    hit(e + 2.2 - 0.05, "sweep", 0.08, hp=60)
    hit(e + 4.1 - 0.25, "debris", 0.07, hp=120)
    save_wav(tr, path, total)

def render(picture=True):
    """picture=False ("python render_liver.py audio") rebuilds only the sound and muxes it onto the last picture.mp4."""
    total = build()
    lines, real = load_lines()
    if not real:
        raise SystemExit("no narration yet: voice it first (out/liver/narration_fixed.json)")
    pic = os.path.join(OUT, "picture.mp4")
    if picture or not os.path.exists(pic):
        code, out = hf("render", "-o", pic, "--quality", "delivery", timeout=3600)
        print(out[-2000:])
        if code:
            raise SystemExit("render failed")
    wav = os.path.join(OUT, "liver.wav")
    build_audio(lines, total, wav)
    mux = os.path.join(OUT, "liver_mux.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pic, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", mux], check=True)
    final = os.path.join(OUT, "liver.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mux, "-c:v", "copy", "-af", "loudnorm=I=-13:TP=-1:LRA=11", "-ar", "48000",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final], check=True)
    print("rendered", final)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else "build"
    if mode in ("render", "audio"):
        render(picture=mode == "render")
        raise SystemExit
    build()
    if mode == "stills":
        times = sys.argv[2]
        code, out = hf("snapshot", "--at", times, timeout=600)
        print(out[-3000:])
