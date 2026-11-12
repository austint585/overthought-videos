"""'You never wanted chocolate': the raw liver meme guy's own words, in the look, voice register and instrumental of the
@cluberich "we could go up" motivational edit (ops/episodes/2026-11-11-liver-go-up.md). White line-art motion graphics
on black, built in HyperFrames (pipeline/hf/liver), timed to the narration's words. The one color (liver red) is kept
back for "raw liver". The music is the TikTok's own bed, split from its voice with Demucs (out/ref/cluberich/split,
never committed), placed so its drop lands on the payoff cut.

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
BEAT = 60 / 107.7                            # the TikTok's instrumental
DROP, SONG_END = 47.83, 53.82                # its drop (a downbeat, where the original cuts to the car B-roll) and its end
TAIL = SONG_END - DROP                       # the music-only "larp" payoff after the last line, to the song's end
MUSIC = os.path.join(OUT, "..", "ref", "cluberich", "split", "htdemucs", "go_up_audio", "no_vocals.wav")

# The meme guy's own words, verbatim (Austin, Nov 12: quote what he said, don't rewrite the TikTok). Whisper on the
# 14 s soundboard clip: "You never wanted chocolate. What you actually did want is raw liver. Why do you play video
# games? Because you want to hunt. Why do you play football? Because you want to hunt with your team."
SCRIPT = [
    "You never wanted chocolate.",
    "What you actually did want is... raw liver.",
    "Why do you play video games?",
    "Because you want to hunt.",
    "Why do you play football?",
    "Because you want to hunt with your team.",
]
# where each line sat in the meme clip (s), for placeholder timing before our narration exists
ORIG = [(0.64, 2.3), (3.86, 6.46), (7.88, 9.1), (9.28, 9.9), (10.04, 10.9), (11.32, 12.9)]

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

def controller(x, y, s=1.0):
    """A game controller in line art: body with two grips, a d-pad, four buttons, two sticks."""
    body = ("M -170 -60 C -120 -95 120 -95 170 -60 C 215 -28 250 70 225 110 C 200 150 150 130 120 85 "
            "C 100 55 -100 55 -120 85 C -150 130 -200 150 -225 110 C -250 70 -215 -28 -170 -60 Z")
    btn = "".join(f'<circle cx="{bx}" cy="{by}" r="11" />' for bx, by in ((125, -40), (155, -12), (125, 16), (95, -12)))
    return (f'<g transform="translate({x},{y}) scale({s})" fill="none" stroke="#fff" stroke-width="{6 / s:.2f}" '
            f'stroke-linejoin="round" stroke-linecap="round"><path d="{body}" />'
            f'<path d="M -142 -12 h 56 M -114 -40 v 56" stroke-width="{12 / s:.2f}" />{btn}'
            f'<circle cx="-55" cy="30" r="22" /><circle cx="55" cy="30" r="22" /></g>')

def football(x, y, s=1.0, rot=-24):
    """An American football in line art: pointed oval, a seam, laces."""
    laces = "".join(f'<line x1="{lx}" y1="-14" x2="{lx}" y2="14" />' for lx in (-36, -12, 12, 36))
    return (f'<g transform="translate({x},{y}) rotate({rot}) scale({s})" fill="none" stroke="#fff" stroke-width="{6 / s:.2f}" '
            f'stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="M -190 0 C -120 -112 120 -112 190 0 C 120 112 -120 112 -190 0 Z" />'
            f'<path d="M -150 -38 C -140 -10 -140 10 -150 38 M 150 -38 C 140 -10 140 10 150 38" />'
            f'<line x1="-60" y1="0" x2="60" y2="0" />{laces}</g>')

def reticle(id_, x, y, r, color="#fff", sw=5):
    """Crosshairs: a ring, four ticks crossing it, a center dot. Drawn on with pathLength."""
    ticks = "".join(f'<line x1="{x + dx * (r - 34)}" y1="{y + dy * (r - 34)}" x2="{x + dx * (r + 34)}" y2="{y + dy * (r + 34)}" pathLength="1" />'
                    for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)))
    return (f'<g id="{id_}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round">'
            f'<circle cx="{x}" cy="{y}" r="{r}" pathLength="1" />{ticks}'
            f'<circle cx="{x}" cy="{y}" r="6" fill="{color}" stroke="none" /></g>')

def build_scenes(T_):
    sc = []
    cut = lambda i: T_.start(i) - 0.12                           # each scene cuts in just before its first word
    red_glow = "text-shadow:0 0 18px rgba(194,26,51,0.85),0 0 60px rgba(194,26,51,0.45);"

    # 1. you never wanted chocolate (frame 0 is already drawn: the bar, glowing, alone on black)
    t0, t1 = 0.0, cut(1)
    tl = TL(t0, "s1")
    a, _ = words("s1-a", "YOU NEVER WANTED", 770, 44)
    body = f"""
    <svg width="{W}" height="{H}" id="s1-bar" style="filter: drop-shadow(0 0 16px rgba(255,255,255,0.7)) drop-shadow(0 0 46px rgba(255,255,255,0.3));">
      {choc(420, 300, 240, 400, 9)}
      <line id="s1-xa" x1="380" y1="330" x2="700" y2="720" stroke="#fff" stroke-width="12" stroke-linecap="round" pathLength="1"/>
      <line id="s1-xb" x1="700" y1="330" x2="380" y2="720" stroke="#fff" stroke-width="12" stroke-linecap="round" pathLength="1"/>
    </svg>
    {a}
    <div class="t glow" id="s1-choc" style="top:840px;font-size:118px;">CHOCOLATE</div>
"""
    ws = [w["start"] for w in T_.lines[0]["words"]]
    tl.set("#s1-choc", "{opacity:0}")
    tl.set("#s1-xa", "{strokeDasharray:1, strokeDashoffset:1}")
    tl.set("#s1-xb", "{strokeDasharray:1, strokeDashoffset:1}")
    tl.word_in("s1-a", [tl.at(x) for x in ws[:3]])
    tc = tl.at(T_(0, "chocolate"))
    tl.slam("#s1-choc", tc, shake=False)
    tx = tc + 0.14                                   # the X lands right after the slam, so it holds long enough to read
    tl.draw("#s1-xa", tx, 0.14, "power3.out")
    tl.draw("#s1-xb", tx + 0.12, 0.14, "power3.out")
    tl.to("#s1-bar", "{opacity:0.4, duration:0.3}", tx + 0.35)
    tl.blur_out(f"#{tl.name}-all", tl.at(t1) - 0.16)
    sc.append(scene("s1", t0, t1, body, tl))

    # 2. THE BIG MOMENT: what you actually did want is... raw liver (the only color in the film, from here on)
    t0, t1 = cut(1), cut(2)
    tl = TL(t0, "s2")
    a, _ = words("s2-a", "WHAT YOU ACTUALLY", 690, 36, cls="dim")
    b, _ = words("s2-b", "DID WANT IS...", 752, 60)
    body = f"""
    {a}
    {b}
    <div id="s2-flash" style="position:absolute;inset:0;background:radial-gradient(ellipse at 50% 45%, rgba(194,26,51,0.38) 0%, rgba(194,26,51,0) 60%);"></div>
    <svg width="{W}" height="{H}" id="s2-liv" style="filter: drop-shadow(0 0 14px rgba(194,26,51,0.95)) drop-shadow(0 0 40px rgba(194,26,51,0.55));">
      {liver(540, 520, 0.95, RED, 7)}
    </svg>
    <div class="t" id="s2-raw" style="top:780px;font-size:124px;color:{RED};{red_glow}">RAW LIVER</div>
"""
    ws = [w["start"] for w in T_.lines[1]["words"]]
    tl.set("#s2-flash, #s2-liv, #s2-raw", "{opacity:0}")
    tl.word_in("s2-a", [tl.at(x) for x in ws[:3]])
    tl.word_in("s2-b", [tl.at(x) for x in ws[3:6]])
    tr = tl.at(T_(1, "raw"))
    tl.set("#s2-a, #s2-b", "{opacity:0}", tr - 0.04)                       # a hard cut, no fade
    tl.slam("#s2-raw", tr)
    tl.fromto("#s2-flash", "{opacity:0}", "{opacity:1, duration:0.06}", tr)
    tl.to("#s2-flash", "{opacity:0.35, duration:0.9, ease:'power2.out'}", tr + 0.1)
    tl.set("#s2-liv path", "{strokeDasharray:1, strokeDashoffset:1}")
    tl.to("#s2-liv", "{opacity:1, duration:0.01}", tr)
    tl.draw("#s2-liv path", tr, 0.45, "power3.out")
    tl.fromto("#s2-liv", "{scale:1, transformOrigin:'50% 27%'}", "{scale:1.07, duration:0.12, ease:'power2.out', yoyo:true, repeat:1}", tr + 0.5)
    tl.blur_out(f"#{tl.name}-all", tl.at(t1) - 0.16)
    sc.append(scene("s2", t0, t1, body, tl))

    # 3. why do you play video games? because you want to hunt (the controller turns into a scope)
    t0, t1 = cut(2), cut(4)
    tl = TL(t0, "s3")
    q, _ = words("s3-q", "WHY DO YOU PLAY", 820, 34, cls="dim")
    b, _ = words("s3-b", "BECAUSE YOU WANT TO", 820, 34, cls="dim")
    body = f"""
    <svg width="{W}" height="{H}" id="s3-pad" style="filter: drop-shadow(0 0 12px rgba(255,255,255,0.6));">{controller(540, 560, 1.2)}</svg>
    <svg width="{W}" height="{H}" id="s3-scope" style="filter: drop-shadow(0 0 12px rgba(255,255,255,0.8));">{reticle("s3-ret", 540, 560, 200, sw=6)}</svg>
    {q}
    <div class="t glow" id="s3-games" style="top:870px;font-size:78px;">VIDEO GAMES?</div>
    {b}
    <div class="t glow" id="s3-hunt" style="top:870px;font-size:140px;">HUNT</div>
"""
    ws2 = [w["start"] for w in T_.lines[2]["words"]]
    ws3 = [w["start"] for w in T_.lines[3]["words"]]
    tl.set("#s3-games, #s3-hunt", "{opacity:0}")
    tl.blur_in("#s3-pad", 0.0, 0.2)
    tl.word_in("s3-q", [tl.at(x) for x in ws2[:4]])
    tl.slam("#s3-games", tl.at(T_(2, "video")), shake=False)
    tb = tl.at(T_(3, "Because"))
    tl.set("#s3-q, #s3-games", "{opacity:0}", tb - 0.04)
    tl.to("#s3-pad", "{opacity:0.22, duration:0.25}", tb - 0.04)
    for sel in ("#s3-ret circle", "#s3-ret line"):
        tl.set(sel, "{strokeDasharray:1, strokeDashoffset:1}")
        tl.draw(sel, tb, 0.4, "power3.out")
    tl.word_in("s3-b", [tl.at(x) for x in ws3[:4]])
    th = tl.at(T_(3, "hunt"))
    tl.fromto("#s3-scope", "{scale:1, transformOrigin:'50% 29.2%'}", "{scale:0.82, duration:0.18, ease:'expo.out'}", th - 0.02)
    tl.set("#s3-b", "{opacity:0}", th - 0.03)
    tl.slam("#s3-hunt", th)
    tl.blur_out(f"#{tl.name}-all", tl.at(t1) - 0.16)
    sc.append(scene("s3", t0, t1, body, tl))

    # 4. why do you play football? because you want to hunt with your team (the team closes on the liver)
    # the hold after the last word is set so "raw" lands on a beat once the music's drop meets the payoff cut
    d = T_.end(5) - T_(1, "raw")
    hold = (-d) % BEAT
    while hold < 0.9:
        hold += BEAT
    t0, t1 = cut(4), T_.end(5) + hold
    tl = TL(t0, "s4")
    q, _ = words("s4-q", "WHY DO YOU PLAY", 820, 34, cls="dim")
    b, _ = words("s4-b", "BECAUSE YOU WANT TO", 470, 34, cls="dim")
    gy = 1170
    team = "".join(f'<g id="s4-p{k}">{PERSON.format(x=150 + k * 92, y=gy, s=1.25)}</g>' for k in range(5))
    body = f"""
    <svg width="{W}" height="{H}" id="s4-ball" style="filter: drop-shadow(0 0 12px rgba(255,255,255,0.6));">{football(540, 560, 1.3)}</svg>
    {q}
    <div class="t glow" id="s4-fb" style="top:870px;font-size:96px;">FOOTBALL?</div>
    <div id="s4-field">
      <svg width="{W}" height="{H}">
        <line x1="90" y1="{gy}" x2="990" y2="{gy}" stroke="#fff" stroke-width="4" />
        {team}
      </svg>
      <svg width="{W}" height="{H}" id="s4-prey" style="filter: drop-shadow(0 0 10px rgba(194,26,51,0.9)) drop-shadow(0 0 30px rgba(194,26,51,0.5));">
        {liver(840, gy - 110, 0.42, RED, 6)}
        {reticle("s4-ret", 840, gy - 110, 118, RED, 5)}
      </svg>
    </div>
    {b}
    <div class="t glow" id="s4-hunt" style="top:520px;font-size:140px;">HUNT</div>
    {pill("s4-team", "WITH YOUR TEAM", 730, 44)}
"""
    ws4 = [w["start"] for w in T_.lines[4]["words"]]
    ws5 = [w["start"] for w in T_.lines[5]["words"]]
    tl.set("#s4-fb, #s4-field, #s4-hunt", "{opacity:0}")
    tl.blur_in("#s4-ball", 0.0, 0.2)
    tl.word_in("s4-q", [tl.at(x) for x in ws4[:4]])
    tl.slam("#s4-fb", tl.at(T_(4, "football")), shake=False)
    tb = tl.at(T_(5, "Because"))
    tl.set("#s4-ball, #s4-q, #s4-fb", "{opacity:0}", tb - 0.04)               # a hard cut to the field
    tl.to("#s4-field", "{opacity:1, duration:0.01}", tb - 0.04)
    for sel in ("#s4-ret circle", "#s4-ret line"):
        tl.set(sel, "{strokeDasharray:1, strokeDashoffset:1}")
        tl.draw(sel, tb + 0.1, 0.4, "power3.out")
    tl.word_in("s4-b", [tl.at(x) for x in ws5[:4]])
    th = tl.at(T_(5, "hunt"))
    tl.set("#s4-b", "{opacity:0}", th - 0.03)
    tl.slam("#s4-hunt", th)
    tl.pop("#s4-team", tl.at(T_(5, "with")))
    tt = tl.at(T_(5, "team"))
    for k in range(5):                                           # the team charges, back to front
        tl.to(f"#s4-p{k}", "{x:150, duration:0.55, ease:'power3.out'}", tt + (4 - k) * 0.05)
    tl.fromto("#s4-prey", "{scale:1, transformOrigin:'77.8% 55.2%'}", "{scale:0.86, duration:0.2, ease:'expo.out'}", tt + 0.3)
    tl.blur_out(f"#{tl.name}-all", tl.at(t1) - 0.16)
    sc.append(scene("s4", t0, t1, body, tl))
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
    for f in os.listdir(os.path.join(HF, "compositions")):      # scenes from an older script
        if f.endswith(".html") and f[:-5] not in [s[0] for s in scenes]:
            os.remove(os.path.join(HF, "compositions", f))
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
MUSIC_UNDER = -7.0                           # dB of the bed against the voice while he talks (the TikTok sat about -2)
MUSIC_PAYOFF = -1.0                          # and in the music-only payoff, against the same voice level

def music_bed(total, end_speech, last_word, voice):
    """The TikTok's own bed, placed so its drop lands on the payoff cut, ducked under the voice, up for the payoff."""
    import numpy as np, soundfile as sf
    from scipy.signal import resample_poly
    from common import SR
    m, sr = sf.read(MUSIC, dtype="float64")
    m = resample_poly(m.mean(1) if m.ndim > 1 else m, SR, sr)
    off = DROP - end_speech                                     # where in the song our t=0 sits
    if off < 0:
        raise SystemExit("speech runs longer than the song before its drop")
    seg = m[int(off * SR):int((off + total) * SR)]
    t = np.arange(len(seg)) / SR
    rms = lambda x: np.sqrt(np.mean(x ** 2)) + 1e-9
    v = voice[np.abs(voice) > 0.02]
    ref = 20 * np.log10(rms(v) / rms(m[int(off * SR):int(DROP * SR)]))  # dB that brings the bed to the voice level
    lo, hi = 10 ** ((ref + MUSIC_UNDER) / 20), 10 ** ((ref + MUSIC_PAYOFF) / 20)
    g = np.interp(t, [0, last_word + 0.1, end_speech, total], [lo, lo, hi, hi])
    g *= np.clip(t / 0.12, 0, 1) * np.clip((total - t) / 0.25, 0, 1)   # no click at the start, a short tail at the end
    print(f"music: song {off:.2f} to {off + total:.2f} s, drop at our {end_speech:.2f} s, bed {ref + MUSIC_UNDER:+.1f} dB")
    return seg * g

def build_audio(lines, total, path):
    import numpy as np
    import sfx
    from common import new_track, add, save_wav, SR
    from render_led import common_load
    T_ = T(lines)
    tr = new_track(total)
    voice = common_load(os.path.join(OUT, "narration_fixed.wav"))[:len(tr)]
    tr[:len(voice)] += voice
    e = total - TAIL                                             # the payoff cut
    bed = music_bed(total, e, T_.end(len(lines) - 1), voice)
    tr[:len(bed)] += bed
    hit = lambda t, key, gain, **kw: add(tr, t, sfx.clip(SFX[key], **kw), gain)
    hit(T_(0, "chocolate") - 0.02, "punch", 0.1)
    hit(T_(0, "chocolate") + 0.14, "snap", 0.1)                  # the X across the bar
    hit(T_(1, "raw") - 0.03, "hit", 0.3)                         # the big moment: the loudest sound in the film
    hit(T_(1, "raw") + 0.02, "splat", 0.1)
    hit(T_(2, "video"), "pop", 0.08)
    hit(T_(3, "hunt") - 0.02, "punch", 0.12)
    hit(T_(4, "football"), "pop", 0.08)
    hit(T_(5, "hunt") - 0.02, "punch", 0.12)
    hit(T_(5, "team"), "woosh", 0.07)                            # the team charges
    hit(e - 0.15, "debris", 0.08)                                # into the payoff, under the song's drop
    hit(e + 2.2 - 0.03, "flash", 0.16)                           # the sill plate lights up like a car's
    hit(e + 2.2 - 0.05, "sweep", 0.06, hp=60)
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
