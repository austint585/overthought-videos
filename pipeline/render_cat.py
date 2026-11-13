"""'We could go up', our own version: a cat's pep talk before the kitchen counter, in the look, voice register and
instrumental of the @cluberich "we could go up" edit (ops/episodes/2026-11-13-cat-go-up.md). White line art on black,
built in HyperFrames (pipeline/hf/cat) on the raw liver kit (render_liver.py), timed to the narration's words. The one
color (amber, the cat's eyes) is kept back for the last line and the payoff.

python render_cat.py build                 write the HyperFrames project from out/cat/narration_fixed.json
python render_cat.py stills 1.0,9.5,...    build, then snapshot those times
python render_cat.py render                build, render the picture, mix the sound, mux to out/cat/cat.mp4
python render_cat.py audio                 the same, but keep the last picture.mp4 and redo only the sound
"""
import json, math, os, random, subprocess, sys
from common import ROOT
from render_liver import T, TL, words, pill, scene, BEAT, DROP, MUSIC, W, H, FPS

HF = os.path.join(ROOT, "hf", "cat")
OUT = os.path.join(ROOT, "out", "cat")
AMBER = "#F2B33D"
TAIL = 4.2                                   # the music-only payoff after the hold (scroll patrol: 6 s was a long beat)

# Voiced in breath groups, one take a passage (Nov 12: per-sentence takes made the raw liver cut sound choppy).
SCRIPT = [
    "We could stay down here... or we could go up.",
    "Do you not see that counter?",
    "Are you not tired of staring at the bottom of the table, while they eat chicken up there?",
    "So you jump. Not when they leave for work. Not when they fall asleep. Now.",
    "Why? Because there's always going to be a glass in the way. A plant in the way. Somebody yelling your full name.",
    "You know what's okay? Missing. Missing is okay. You land on your feet anyway.",
    "But you know what's not okay?",
    "Leaving that glass on the counter.",
]
# silence after each passage, set by hand from the original speech's rhythm (it runs 0.34 to 0.56 s between sentences)
GAPS = [0.40, 0.40, 0.36, 0.46, 0.50, 0.55, 0.50]
# every take of passage 3 came out rushed (+24% against the median, Nov 12), so that one line may slow down to the
# median; the rest keep their own pace within 4%
VOICE_FIX = dict(max_stretch=[0.04, 0.04, 0.2, 0.04, 0.04, 0.04, 0.04, 0.04], keep_pauses=True, gaps=GAPS)

def load_lines():
    return json.load(open(os.path.join(OUT, "narration_fixed.json")))

def org(x, y):
    """A canvas point as a GSAP transformOrigin for a full-canvas element."""
    return f"'{100 * x / W:.2f}% {100 * y / H:.2f}%'"

GLOW = "filter: drop-shadow(0 0 12px rgba(255,255,255,0.65)) drop-shadow(0 0 36px rgba(255,255,255,0.25));"
AGLOW = "filter: drop-shadow(0 0 12px rgba(242,179,61,0.95)) drop-shadow(0 0 40px rgba(242,179,61,0.5));"

# ------------------------------------------------------------------ line art (local origin at the bottom center)

CAT_D = ("M -92 0 C -112 -72 -98 -148 -52 -180 C -70 -192 -72 -222 -62 -240 L -46 -322 L -18 -286 "
         "C -6 -290 6 -290 18 -286 L 46 -322 L 62 -240 C 72 -222 70 -192 52 -180 C 98 -148 112 -72 92 0 "
         "C 40 8 -40 8 -92 0 Z")
FILL = "#0c0c0c"                              # the cat hides the lines behind it
TAIL_D = "M 86 -8 C 150 -12 182 -64 160 -116 C 150 -140 124 -136 128 -114"

def g(x, y, s, inner, sw=6, color="#fff", extra=""):
    return (f'<g {extra} transform="translate({x},{y}) scale({s})" fill="none" stroke="{color}" stroke-width="{sw / s:.2f}" '
            f'stroke-linecap="round" stroke-linejoin="round">{inner}</g>')

def cat(x, y, s, face=False, tail=True, sw=6):
    """The cat seen from behind (or, with face=True, from the front: amber eyes with slit pupils, nose, whiskers)."""
    inner = f'<path d="{CAT_D}" fill="{FILL}" />' + (f'<path d="{TAIL_D}" />' if tail else "")
    if face:
        for cx in (-27, 27):
            inner += (f'<path d="M {cx - 18} -240 Q {cx} -258 {cx + 18} -240 Q {cx} -222 {cx - 18} -240 Z" fill="{AMBER}" stroke="{AMBER}" />'
                      f'<line x1="{cx}" y1="-251" x2="{cx}" y2="-229" stroke="#000" stroke-width="{5 / s:.2f}" />')
        inner += '<path d="M -7 -220 L 7 -220 L 0 -212 Z" />'
        inner += "".join(f'<line x1="{d * 14}" y1="{yy}" x2="{d * 62}" y2="{yy + dy}" />'
                         for d in (-1, 1) for yy, dy in ((-214, -8), (-207, 8)))
    return g(x, y, s, inner, sw)

def tail_only(x, y, s, sw=6):
    return g(x, y, s, f'<path d="{TAIL_D}" />', sw)

def cat_body(x, y, s, sw=6):
    return g(x, y, s, f'<path d="{CAT_D}" fill="{FILL}" />', sw)

def glass(x, y, s, sw=6):
    return g(x, y, s, '<path d="M -40 -128 L 40 -128 L 32 0 L -32 0 Z" /><path d="M -37 -84 Q -18 -90 0 -84 T 37 -84" />'
                      '<line x1="-22" y1="-112" x2="-18" y2="-24" stroke-opacity="0.5" />', sw)

def counter(x0, x1, y, d=28, sw=6):
    return (f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="{d}" rx="4" fill="none" stroke="#fff" stroke-width="{sw}" />')

def cabinets(x0, x1, y0, y1, sw=4):
    mid = (x0 + x1) / 2
    return (f'<g fill="none" stroke="#fff" stroke-width="{sw}">'
            f'<rect x="{x0}" y="{y0}" width="{mid - x0 - 10}" height="{y1 - y0}" rx="6" />'
            f'<rect x="{mid + 10}" y="{y0}" width="{x1 - mid - 10}" height="{y1 - y0}" rx="6" />'
            f'<circle cx="{mid - 34}" cy="{(y0 + y1) / 2}" r="9" /><circle cx="{mid + 34}" cy="{(y0 + y1) / 2}" r="9" /></g>')

def drumstick(x, y, s, sw=6):
    return g(x, y, s, '<path d="M -78 10 C -100 -40 -40 -78 10 -52 C 40 -36 40 0 14 22 C -14 46 -64 50 -78 10 Z" />'
                      '<path d="M 22 -30 L 68 -70" /><circle cx="64" cy="-84" r="13" /><circle cx="82" cy="-66" r="13" />', sw)

def door(x, y, s, sw=6):
    return g(x, y, s, '<rect x="-70" y="-260" width="140" height="260" rx="4" /><rect x="-44" y="-232" width="88" height="60" rx="3" />'
                      '<circle cx="46" cy="-128" r="8" />', sw)

def bed(x, y, s, sw=6):
    return g(x, y, s, '<path d="M -160 0 L -160 -150 M -160 -70 L 160 -70 L 160 0 M -160 -30 L 160 -30" />'
                      '<ellipse cx="-112" cy="-86" rx="34" ry="15" />'
                      '<text x="40" y="-112" font-family="Montserrat" font-weight="800" font-size="44" fill="#fff" stroke="none">Z</text>'
                      '<text x="90" y="-162" font-family="Montserrat" font-weight="800" font-size="36" fill="#fff" stroke="none">Z</text>', sw)

def plant(x, y, s, sw=6):
    return g(x, y, s, '<path d="M -42 -70 L 42 -70 L 32 0 L -32 0 Z" /><line x1="-48" y1="-70" x2="48" y2="-70" />'
                      '<path d="M 0 -70 C -10 -128 -58 -156 -72 -150 C -62 -116 -30 -88 0 -70" />'
                      '<path d="M 0 -70 C 10 -128 58 -156 72 -150 C 62 -116 30 -88 0 -70" />'
                      '<path d="M 0 -70 C -16 -140 0 -190 6 -198 C 18 -160 14 -110 0 -70" />', sw)

def bubble(x, y, text, w=320, h=104, sw=6, size=34):
    return (f'<g fill="none" stroke="#fff" stroke-width="{sw}" stroke-linejoin="round">'
            f'<path d="M {x - w / 2 + 20} {y - h / 2} L {x + w / 2 - 20} {y - h / 2} Q {x + w / 2} {y - h / 2} {x + w / 2} {y - h / 2 + 20} '
            f'L {x + w / 2} {y + h / 2 - 20} Q {x + w / 2} {y + h / 2} {x + w / 2 - 20} {y + h / 2} L {x + 70} {y + h / 2} '
            f'L {x + 120} {y + h / 2 + 46} L {x + 30} {y + h / 2} L {x - w / 2 + 20} {y + h / 2} Q {x - w / 2} {y + h / 2} {x - w / 2} {y + h / 2 - 20} '
            f'L {x - w / 2} {y - h / 2 + 20} Q {x - w / 2} {y - h / 2} {x - w / 2 + 20} {y - h / 2} Z" />'
            f'<text x="{x}" y="{y + size * 0.36:.0f}" text-anchor="middle" font-family="Montserrat" font-weight="800" '
            f'font-size="{size}" letter-spacing="3" fill="#fff" stroke="none">{text}</text></g>')

def paw(x, y, s, sw=6, arm=True):
    """A paw from the side, toes to the right, the leg running back off the left edge."""
    beans = "".join(f'<circle cx="{cx}" cy="{cy}" r="9" />' for cx, cy in ((34, -30), (44, -6), (36, 18)))
    leg = '<path d="M -10 -34 L -700 -60 M -10 30 L -700 40" />' if arm else ""
    return g(x, y, s, f'<path d="M -14 -36 C 30 -44 62 -20 60 0 C 58 26 28 42 -14 34" />{beans}{leg}', sw)

def grip_paw(x, y, s, sw=6):
    """A paw hooked over an edge, seen from the front: the pad and three claws."""
    return g(x, y, s, '<path d="M -40 0 C -44 -36 44 -36 40 0 C 36 24 -36 24 -40 0 Z" />'
                      '<path d="M -22 18 L -24 34 M 0 22 L 0 40 M 22 18 L 24 34" />', sw)

def fridge(x0, y0, x1, y1, split, sw=6):
    return (f'<g fill="none" stroke="#fff" stroke-width="{sw}" stroke-linecap="round">'
            f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" rx="18" />'
            f'<line x1="{x0}" y1="{split}" x2="{x1}" y2="{split}" />'
            f'<line x1="{x0 + 40}" y1="{y0 + 70}" x2="{x0 + 40}" y2="{split - 60}" stroke-width="{sw * 1.6}" />'
            f'<line x1="{x0 + 40}" y1="{split + 60}" x2="{x0 + 40}" y2="{split + 300}" stroke-width="{sw * 1.6}" /></g>')

def almond_eyes(cx, cy, gap=150, w=104, h=50):
    out = ""
    for x in (cx - gap / 2, cx + gap / 2):
        out += (f'<path d="M {x - w / 2} {cy} Q {x} {cy - h} {x + w / 2} {cy} Q {x} {cy + h} {x - w / 2} {cy} Z" fill="{AMBER}" />'
                f'<path d="M {x} {cy - h * 0.62} Q {x + 8} {cy} {x} {cy + h * 0.62} Q {x - 8} {cy} {x} {cy - h * 0.62} Z" fill="#000" />')
    return out

# ------------------------------------------------------------------ the scenes

def build_scenes(T_):
    sc = []
    cut = lambda i: T_.start(i) - 0.12
    ws = lambda i: [w["start"] for w in T_.lines[i]["words"]]

    # 1. we could stay down here... or we could go up. / do you not see that counter?
    #    Frame 0 already moves and reads (scroll patrol): the tail swishes, the frame drifts up, the first words are on.
    t0, t1 = 0.0, cut(2)
    tl = TL(t0, "s1")
    a, _ = words("s1-a", "WE COULD STAY", 600, 46)
    b, _ = words("s1-b", "DOWN HERE...", 662, 46, cls="dim")
    c, _ = words("s1-c", "OR WE COULD", 1000, 42, cls="dim")
    q, _ = words("s1-q", "DO YOU NOT SEE", 990, 36, cls="dim")
    tx, ty = 540 + 86 * 1.0, 1500 - 8
    body = f"""
    <div id="s1-world" style="position:absolute;inset:0;">
      <svg width="{W}" height="{H}" id="s1-cab" style="opacity:0.28;">{cabinets(160, 920, 372, 1262)}
        <line x1="90" y1="1290" x2="990" y2="1290" stroke="#fff" stroke-width="4" /></svg>
      <svg width="{W}" height="{H}" id="s1-counter" style="{GLOW}opacity:0.8;">{counter(130, 950, 330)}</svg>
      <svg width="{W}" height="{H}" id="s1-glass" style="{GLOW}">{glass(720, 330, 1.0)}</svg>
      <svg width="{W}" height="{H}" id="s1-cat" style="{GLOW}">{cat_body(540, 1500, 1.0)}</svg>
      <svg width="{W}" height="{H}" id="s1-tail" style="{GLOW}">{tail_only(540, 1500, 1.0)}</svg>
    </div>
    {a}
    {b}
    {c}
    <div class="t glow" id="s1-up" style="top:980px;font-size:150px;">GO UP</div>
    {q}
    <div class="t glow" id="s1-ctr" style="top:1040px;font-size:86px;">THAT COUNTER?</div>
"""
    w0 = ws(0)
    tl.set("#s1-b-0, #s1-b-1, #s1-c, #s1-up, #s1-ctr", "{opacity:0}")
    tl.word_in("s1-b", [tl.at(x) for x in w0[3:5]])
    t_or, t_up = tl.at(T_(0, "or")), tl.at(T_(0, "up"))
    n = int((t1 - t0) / 0.45) + 1
    for k in range(n):                                    # the tail swishes from frame 0 (no endless repeat)
        tl.to("#s1-tail", f"{{rotation:{9 if k % 2 == 0 else -7}, transformOrigin:{org(tx, ty)}, duration:0.45, ease:'sine.inOut'}}", k * 0.45)
    tl.to("#s1-world", f"{{y:36, duration:{max(0.5, t_or):.3f}, ease:'none'}}", 0.0)        # a slow drift up from frame 0
    tl.blur_out("#s1-a, #s1-b", t_or - 0.02, 0.12)
    tl.word_in("s1-c", [tl.at(x) for x in w0[5:8]])
    tl.set("#s1-c", "{opacity:1}", t_or - 0.03)
    tl.to("#s1-world", f"{{y:470, duration:{max(0.4, t_up - t_or + 0.2):.3f}, ease:'power3.inOut'}}", t_or + 0.02)
    tl.to("#s1-cab", "{opacity:0.14, duration:0.4}", t_or + 0.2)
    tl.set("#s1-c", "{opacity:0}", t_up - 0.03)
    tl.slam("#s1-up", t_up)
    t_do = tl.at(T_(1, "Do"))
    tl.set("#s1-up", "{opacity:0}", t_do - 0.03)
    tl.word_in("s1-q", [tl.at(x) for x in ws(1)[:4]])
    tc = tl.at(T_(1, "counter"))
    tl.slam("#s1-ctr", tl.at(T_(1, "that")), shake=False)
    tl.to("#s1-counter", "{opacity:1, duration:0.12}", tc)
    tl.fromto("#s1-counter", f"{{scale:1, transformOrigin:{org(540, 344)}}}", "{scale:1.04, duration:0.12, ease:'power2.out', yoyo:true, repeat:1}", tc)
    tl.blur_out("#s1-all", tl.at(t1) - 0.16)
    sc.append(scene("s1", t0, t1, body, tl))

    # 2. are you not tired of staring at the bottom of the table, while they eat chicken up there?
    t0, t1 = cut(2), cut(3)
    tl = TL(t0, "s2")
    a, _ = words("s2-a", "ARE YOU NOT TIRED OF", 640, 34, cls="dim")
    b, _ = words("s2-b", "STARING AT THE BOTTOM", 690, 46)
    c, _ = words("s2-c", "OF THE TABLE", 752, 46)
    d, _ = words("s2-d", "WHILE THEY EAT", 660, 36, cls="dim")
    body = f"""
    <svg width="{W}" height="{H}" id="s2-table" style="{GLOW}">
      <rect x="90" y="470" width="900" height="40" rx="5" fill="none" stroke="#fff" stroke-width="6" />
      <rect x="110" y="510" width="26" height="890" fill="none" stroke="#fff" stroke-width="5" />
      <rect x="944" y="510" width="26" height="890" fill="none" stroke="#fff" stroke-width="5" />
      <ellipse cx="640" cy="464" rx="96" ry="9" fill="none" stroke="#fff" stroke-width="5" />
      <line x1="60" y1="1400" x2="1020" y2="1400" stroke="#fff" stroke-width="3" stroke-opacity="0.4" />
    </svg>
    <svg width="{W}" height="{H}" id="s2-cat" style="{GLOW}">{cat(540, 1400, 0.55)}</svg>
    <svg width="{W}" height="{H}" id="s2-food" style="{GLOW}">{drumstick(630, 440, 0.85)}</svg>
    {a}{b}{c}{d}
    <div class="t glow" id="s2-chk" style="top:712px;font-size:128px;">CHICKEN</div>
    {pill("s2-up", "UP THERE", 890, 44)}
"""
    w2 = ws(2)
    tl.set("#s2-food, #s2-d, #s2-chk", "{opacity:0}")
    tl.blur_in("#s2-table", 0.0, 0.18)
    tl.word_in("s2-a", [tl.at(x) for x in w2[0:5]])
    tl.word_in("s2-b", [tl.at(x) for x in w2[5:9]])
    tl.word_in("s2-c", [tl.at(x) for x in w2[9:12]])
    tw = tl.at(T_(2, "while"))
    tl.set("#s2-a, #s2-b, #s2-c", "{opacity:0}", tw - 0.03)
    tl.set("#s2-d", "{opacity:1}", tw - 0.03)
    tl.word_in("s2-d", [tl.at(x) for x in w2[12:15]])
    tk = tl.at(T_(2, "chicken"))
    tl.slam("#s2-chk", tk)
    tl.pop("#s2-food", tk)
    tu = tl.at(T_(2, "up"))
    tl.pop("#s2-up", tu)
    tl.fromto("#s2-food", "{y:0}", "{y:-14, duration:0.18, ease:'power2.out', yoyo:true, repeat:1}", tu)
    tl.blur_out("#s2-all", tl.at(t1) - 0.16)
    sc.append(scene("s2", t0, t1, body, tl))

    # 3. so you jump. not when they leave for work. not when they fall asleep. now.
    t0, t1 = cut(3), cut(4)
    tl = TL(t0, "s3")
    a, _ = words("s3-a", "SO YOU", 560, 38, cls="dim")
    n1, _ = words("s3-n1", "NOT WHEN THEY", 900, 34, cls="dim")
    n2, _ = words("s3-n2", "NOT WHEN THEY", 900, 34, cls="dim")
    springs = "".join(f'<path d="M {540 + dx - 26} {1272 + k * 16} q 13 -10 26 0 t 26 0" fill="none" stroke="#fff" stroke-width="4" />'
                      for dx in (-60, 60) for k in range(2))
    body = f"""
    <svg width="{W}" height="{H}" id="s3-cat" style="{GLOW}">{cat(540, 1250, 0.95)}</svg>
    <svg width="{W}" height="{H}" id="s3-spring" style="{GLOW}">{springs}</svg>
    {a}
    <div class="t glow" id="s3-jump" style="top:612px;font-size:160px;">JUMP</div>
    <svg width="{W}" height="{H}" id="s3-door" style="{GLOW}">{door(330, 780, 1.0)}
      <line id="s3-xd1" x1="240" y1="500" x2="420" y2="800" stroke="#fff" stroke-width="12" stroke-linecap="round" pathLength="1"/>
      <line id="s3-xd2" x1="420" y1="500" x2="240" y2="800" stroke="#fff" stroke-width="12" stroke-linecap="round" pathLength="1"/></svg>
    <svg width="{W}" height="{H}" id="s3-bed" style="{GLOW}">{bed(760, 780, 0.9)}
      <line id="s3-xb1" x1="600" y1="560" x2="920" y2="810" stroke="#fff" stroke-width="12" stroke-linecap="round" pathLength="1"/>
      <line id="s3-xb2" x1="920" y1="560" x2="600" y2="810" stroke="#fff" stroke-width="12" stroke-linecap="round" pathLength="1"/></svg>
    {n1}
    <div class="t glow" id="s3-work" style="top:950px;font-size:68px;">LEAVE FOR WORK</div>
    {n2}
    <div class="t glow" id="s3-sleep" style="top:950px;font-size:68px;">FALL ASLEEP</div>
    <div class="t glow" id="s3-now" style="top:880px;font-size:200px;">NOW.</div>
"""
    w3 = ws(3)
    tl.set("#s3-spring, #s3-jump, #s3-door, #s3-bed, #s3-n1, #s3-n2, #s3-work, #s3-sleep, #s3-now", "{opacity:0}")
    for sel in ("#s3-xd1", "#s3-xd2", "#s3-xb1", "#s3-xb2"):
        tl.set(sel, "{strokeDasharray:1, strokeDashoffset:1}")
    tl.blur_in("#s3-cat", 0.0, 0.16)
    tl.word_in("s3-a", [tl.at(x) for x in w3[0:2]])
    tl.to("#s3-cat", f"{{scaleY:0.86, transformOrigin:{org(540, 1250)}, duration:0.3, ease:'power2.out'}}", tl.at(w3[0]))
    tl.to("#s3-spring", "{opacity:1, duration:0.1}", tl.at(w3[1]))
    tj = tl.at(T_(3, "jump"))
    tl.slam("#s3-jump", tj)
    tl.set("#s3-spring", "{opacity:0}", tj)
    tl.to("#s3-cat", "{scaleY:1.18, y:-1500, duration:0.42, ease:'power3.in'}", tj)
    tn1 = tl.at(T_(3, "Not", 0))
    tl.set("#s3-a, #s3-jump", "{opacity:0}", tn1 - 0.03)
    tl.pop("#s3-door", tn1)
    tl.set("#s3-n1", "{opacity:1}", tn1 - 0.03)
    tl.word_in("s3-n1", [tl.at(x) for x in w3[3:6]])
    tl.slam("#s3-work", tl.at(T_(3, "leave", 0)), shake=False)
    tw = tl.at(T_(3, "work", end=True))
    tl.draw("#s3-xd1", tw - 0.08, 0.14, "power3.out")
    tl.draw("#s3-xd2", tw + 0.04, 0.14, "power3.out")
    tl.to("#s3-door", "{opacity:0.3, duration:0.25}", tw + 0.25)
    tn2 = tl.at(T_(3, "Not", 1))
    tl.set("#s3-n1, #s3-work", "{opacity:0}", tn2 - 0.03)
    tl.pop("#s3-bed", tn2)
    tl.set("#s3-n2", "{opacity:1}", tn2 - 0.03)
    tl.word_in("s3-n2", [tl.at(x) for x in w3[9:12]])
    tl.slam("#s3-sleep", tl.at(T_(3, "fall")), shake=False)
    ta = tl.at(T_(3, "asleep", end=True))
    tl.draw("#s3-xb1", ta - 0.08, 0.14, "power3.out")
    tl.draw("#s3-xb2", ta + 0.04, 0.14, "power3.out")
    tnow = tl.at(T_(3, "Now"))
    tl.set("#s3-n2, #s3-sleep", "{opacity:0}", tnow - 0.03)
    tl.to("#s3-door, #s3-bed", "{opacity:0.15, duration:0.15}", tnow - 0.03)
    tl.slam("#s3-now", tnow)
    tl.blur_out("#s3-all", tl.at(t1) - 0.16)
    sc.append(scene("s3", t0, t1, body, tl))

    # 4. why? because there's always going to be a glass in the way. a plant in the way. somebody yelling your full name.
    t0, t1 = cut(4), cut(5)
    tl = TL(t0, "s4")
    a, _ = words("s4-a", "BECAUSE THERE'S ALWAYS", 680, 46, cls="dim")
    a2, _ = words("s4-a2", "GOING TO BE", 738, 46, cls="dim")
    s1_, _ = words("s4-s", "SOMEBODY YELLING", 820, 44)
    body = f"""
    <div class="t glow" id="s4-why" style="top:700px;font-size:180px;">WHY?</div>
    <svg width="{W}" height="{H}" id="s4-counter" style="{GLOW}">{counter(130, 950, 560)}</svg>
    <svg width="{W}" height="{H}" id="s4-glass" style="{GLOW}">{glass(300, 560, 1.0)}</svg>
    <svg width="{W}" height="{H}" id="s4-plant" style="{GLOW}">{plant(540, 560, 1.0)}</svg>
    <svg width="{W}" height="{H}" id="s4-bub" style="{GLOW}">{bubble(780, 400, "MILO JAMES!")}</svg>
    {a}{a2}
    <div class="t glow" id="s4-g" style="top:810px;font-size:100px;">A GLASS</div>
    <div class="t glow" id="s4-p" style="top:810px;font-size:100px;">A PLANT</div>
    {s1_}
    <div class="t glow" id="s4-name" style="top:874px;font-size:84px;">YOUR FULL NAME</div>
"""
    w4 = ws(4)
    tl.set("#s4-counter, #s4-glass, #s4-plant, #s4-bub, #s4-a, #s4-a2, #s4-g, #s4-p, #s4-s, #s4-name", "{opacity:0}")
    tl.slam("#s4-why", tl.at(T_(4, "Why")))
    tb = tl.at(T_(4, "Because"))
    tl.set("#s4-why", "{opacity:0}", tb - 0.03)
    tl.blur_in("#s4-counter", tb - 0.03, 0.14)
    tl.set("#s4-a, #s4-a2", "{opacity:1}", tb - 0.03)
    tl.word_in("s4-a", [tl.at(x) for x in w4[1:4]])
    tl.word_in("s4-a2", [tl.at(x) for x in w4[4:7]])
    tg = tl.at(T_(4, "glass"))
    tl.slam("#s4-g", tl.at(T_(4, "a", 0)), shake=False)
    tl.pop("#s4-glass", tg)
    tp = tl.at(T_(4, "plant"))
    tl.set("#s4-g", "{opacity:0}", tl.at(T_(4, "a", 1)) - 0.03)
    tl.slam("#s4-p", tl.at(T_(4, "a", 1)), shake=False)
    tl.pop("#s4-plant", tp)
    tsb = tl.at(T_(4, "Somebody"))
    tl.set("#s4-p", "{opacity:0}", tsb - 0.03)
    tl.set("#s4-s", "{opacity:1}", tsb - 0.03)
    tl.word_in("s4-s", [tl.at(x) for x in w4[-5:-3]])
    tl.slam("#s4-name", tl.at(T_(4, "full")))
    tl.pop("#s4-bub", tl.at(T_(4, "full")))
    tl.fromto("#s4-bub", f"{{x:0}}", "{x:6, duration:0.04, ease:'none', yoyo:true, repeat:5}", tl.at(T_(4, "name")))
    tl.blur_out("#s4-all", tl.at(t1) - 0.16)
    sc.append(scene("s4", t0, t1, body, tl))

    # 5. you know what's okay? missing. missing is okay. you land on your feet anyway.
    #    The cat hangs from the counter by its front paws, slides down the cabinet leaving claw marks, then drops to the
    #    floor and sits.
    t0, t1 = cut(5), cut(6)
    tl = TL(t0, "s5")
    a, _ = words("s5-a", "YOU KNOW WHAT'S OKAY?", 1160, 38, cls="dim")
    b, _ = words("s5-b", "MISSING IS OKAY.", 1200, 64)
    cy, fy, sl = 700, 1080, 200                                  # hanging cat's bottom, the floor, the slide
    claws = "".join(f'<line id="s5-c{k}" x1="{x}" y1="282" x2="{x + 3}" y2="{282 + sl + 40}" stroke="#fff" stroke-width="5" stroke-linecap="round" pathLength="1" />'
                    for k, x in enumerate((458, 480, 502, 578, 600, 622)))
    arms = (f'<path d="M {540 - 46} {cy - 160} L 480 268 M {540 + 46} {cy - 160} L 600 268" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" />')
    dust = "".join(f'<line x1="{540 + d * 110}" y1="{fy - 8 - k * 16}" x2="{540 + d * 165}" y2="{fy - 14 - k * 34}" stroke="#fff" stroke-width="5" stroke-linecap="round" />'
                   for d in (-1, 1) for k in range(2))
    body = f"""
    <svg width="{W}" height="{H}" id="s5-set" style="opacity:0.22;">{cabinets(160, 920, 280, 1060)}
      <line x1="90" y1="{fy}" x2="990" y2="{fy}" stroke="#fff" stroke-width="4" /></svg>
    <svg width="{W}" height="{H}" id="s5-counter" style="{GLOW}">{counter(130, 950, 240)}</svg>
    <svg width="{W}" height="{H}" id="s5-claws" style="{GLOW}">{claws}</svg>
    <svg width="{W}" height="{H}" id="s5-hang" style="{GLOW}">{arms}{cat_body(540, cy, 0.9)}{grip_paw(480, 262, 0.9)}{grip_paw(600, 262, 0.9)}</svg>
    <svg width="{W}" height="{H}" id="s5-cat" style="{GLOW}">{cat(540, fy, 0.9)}</svg>
    <svg width="{W}" height="{H}" id="s5-dust" style="{GLOW}">{dust}</svg>
    {a}
    <div class="t glow" id="s5-miss" style="top:1180px;font-size:140px;">MISSING.</div>
    {b}
    {pill("s5-feet", "YOU LAND ON YOUR FEET", 1180, 46)}
    <div class="t dim" id="s5-any" style="top:1290px;font-size:40px;">ANYWAY.</div>
"""
    w5 = ws(5)
    tl.set("#s5-cat, #s5-dust, #s5-miss, #s5-b, #s5-any", "{opacity:0}")
    for k in range(6):
        tl.set(f"#s5-c{k}", "{strokeDasharray:1, strokeDashoffset:1}")
    tl.blur_in("#s5-counter, #s5-hang", 0.0, 0.16)
    tl.fromto("#s5-set", "{opacity:0}", "{opacity:0.22, duration:0.16}", 0.0)
    tl.fromto("#s5-hang", "{y:0}", "{y:6, duration:0.35, ease:'sine.inOut', yoyo:true, repeat:3}", 0.1)   # dangling
    tl.word_in("s5-a", [tl.at(x) for x in w5[0:4]])
    tm = tl.at(T_(5, "Missing", 0))
    tl.set("#s5-a", "{opacity:0}", tm - 0.03)
    tl.slam("#s5-miss", tm)
    slide = 0.55
    tl.to("#s5-hang", f"{{y:{sl}, duration:{slide}, ease:'power2.in'}}", tm + 0.02)
    for k in range(6):
        tl.draw(f"#s5-c{k}", tm + 0.02 + 0.02 * (k % 3), slide, "power2.in")
    tm2 = tl.at(T_(5, "Missing", 1))
    tl.set("#s5-miss", "{opacity:0}", tm2 - 0.03)
    tl.set("#s5-b", "{opacity:1}", tm2 - 0.03)
    tl.word_in("s5-b", [tl.at(x) for x in w5[5:8]])
    tland = tl.at(T_(5, "land"))
    tl.to("#s5-hang", f"{{y:{fy - cy}, duration:0.24, ease:'power2.in'}}", tland - 0.26)
    tl.set("#s5-hang", "{opacity:0}", tland - 0.02)
    tl.set("#s5-cat", "{opacity:1}", tland - 0.02)
    tl.fromto("#s5-cat", f"{{scaleY:0.86, transformOrigin:{org(540, fy)}}}", "{scaleY:1, duration:0.22, ease:'back.out(3)'}", tland - 0.02)
    tl.fromto("#s5-dust", "{opacity:0}", "{opacity:1, duration:0.05}", tland - 0.02)
    tl.to("#s5-dust", "{opacity:0, duration:0.4}", tland + 0.25)
    tl.set("#s5-b", "{opacity:0}", tland - 0.06)
    tl.pop("#s5-feet", tland - 0.03)
    tl.blur_in("#s5-any", tl.at(T_(5, "anyway")), 0.14)
    tl.blur_out("#s5-all", tl.at(t1) - 0.16)
    sc.append(scene("s5", t0, t1, body, tl))

    # 6. THE BIG MOMENT. but you know what's not okay? / leaving that glass on the counter. The hold after it is set so
    #    "counter" (the tip) lands on a beat once the song's drop meets the payoff cut; the glass falls through the hold.
    d = T_.end(7) - T_(7, "counter")
    hold = (-d) % BEAT
    while hold < 1.1:
        hold += BEAT
    t0, t1 = cut(6), T_.end(7) + hold
    tl = TL(t0, "s6")
    a, _ = words("s6-a", "BUT YOU KNOW", 760, 38, cls="dim")
    b, _ = words("s6-b", "WHAT'S NOT OKAY?", 812, 66)
    c, _ = words("s6-c", "LEAVING THAT", 250, 40, cls="dim")
    gx, gy, gs = 690, 1040, 2.0
    body = f"""
    {a}{b}
    <div id="s6-close" style="position:absolute;inset:0;">
      <svg width="{W}" height="{H}" id="s6-eyes" style="{AGLOW}">{almond_eyes(330, 600)}</svg>
      <svg width="{W}" height="{H}" id="s6-counter" style="{GLOW}">
        <rect x="-20" y="{gy}" width="820" height="44" rx="6" fill="none" stroke="#fff" stroke-width="7" />
        <line x1="800" y1="{gy + 44}" x2="800" y2="1920" stroke="#fff" stroke-width="5" stroke-opacity="0.35" /></svg>
      <svg width="{W}" height="{H}" id="s6-paw" style="{GLOW}">{paw(470, gy - 52, 1.3)}</svg>
      <svg width="{W}" height="{H}" id="s6-glass" style="{GLOW}">{glass(gx, gy, gs)}</svg>
      {c}
      <div class="t glow" id="s6-gl" style="top:300px;font-size:130px;">GLASS</div>
      {pill("s6-on", "ON THE COUNTER", 1190, 48)}
    </div>
"""
    w6, w7 = ws(6), ws(7)
    tl.set("#s6-close, #s6-gl", "{opacity:0}")
    tl.word_in("s6-a", [tl.at(x) for x in w6[0:3]])
    tl.word_in("s6-b", [tl.at(x) for x in w6[3:6]])
    tlv = tl.at(T_(7, "Leaving"))
    tl.set("#s6-a, #s6-b", "{opacity:0}", tlv - 0.04)                       # a hard cut, no fade
    tl.set("#s6-close", "{opacity:1}", tlv - 0.04)
    tl.fromto("#s6-eyes", f"{{scaleY:0.05, transformOrigin:{org(330, 600)}}}", "{scaleY:1, duration:0.16, ease:'power3.out'}", tlv)
    tl.word_in("s6-c", [tl.at(x) for x in w7[0:2]])
    tl.slam("#s6-gl", tl.at(T_(7, "glass")), shake=False)
    tl.fromto("#s6-paw", "{x:-260}", f"{{x:0, duration:{max(0.3, tl.at(T_(7, 'counter')) - tlv - 0.1):.3f}, ease:'power1.inOut'}}", tlv + 0.05)
    tl.pop("#s6-on", tl.at(T_(7, "on")))
    tc = tl.at(T_(7, "counter"))
    pivot = org(gx + 32 * gs, gy)                                             # the glass's bottom right corner, at the edge
    tl.to("#s6-paw", "{x:60, duration:0.12, ease:'power2.out'}", tc - 0.02)
    tl.to("#s6-glass", f"{{rotation:24, transformOrigin:{pivot}, duration:0.22, ease:'power2.out'}}", tc)
    fall = tl.at(t1) - (tc + 0.32)
    tl.to("#s6-glass", f"{{rotation:110, x:170, y:1050, duration:{fall:.3f}, ease:'power2.in'}}", tc + 0.32)
    sc.append(scene("s6", t0, t1, body, tl))
    return sc, t1

def payoff(e):
    """7. On the song's drop: the glass bursts on the floor, then the cat on top of the fridge, shot like a car ad."""
    t0, t1 = e, e + TAIL
    tl = TL(t0, "s7")
    rnd = random.Random(7)
    shards, moves = "", []
    for k in range(20):
        a = -3.14 * (0.04 + 0.92 * k / 19)
        r = rnd.uniform(260, 600)
        sx, sy = 540 + rnd.uniform(-20, 20), 1330
        pts = " ".join(f"{sx + rnd.uniform(-44, 44):.0f},{sy + rnd.uniform(-44, 14):.0f}" for _ in range(3))
        shards += f'<polygon id="s7-sh{k}" points="{pts}" fill="none" stroke="#fff" stroke-width="5" stroke-linejoin="round" />'
        moves.append((k, r * math.cos(a), r * math.sin(a) * 0.9, rnd.uniform(-220, 220)))
    hero = 0.9
    body = f"""
    <div id="s7-hit" style="position:absolute;inset:0;">
      <svg width="{W}" height="{H}" style="{GLOW}"><line x1="60" y1="1340" x2="1020" y2="1340" stroke="#fff" stroke-width="5" />{shards}</svg>
    </div>
    <div id="s7-flash" style="position:absolute;inset:0;background:#fff;"></div>
    <div id="s7-hero" style="position:absolute;inset:0;">
      <div style="position:absolute;inset:0;background:radial-gradient(ellipse 60% 40% at 50% 38%, rgba(242,179,61,0.22) 0%, rgba(242,179,61,0) 70%);"></div>
      <svg width="{W}" height="{H}" id="s7-set" style="{GLOW}">{fridge(330, 770, 750, 1720, 1010)}
        <line x1="40" y1="1720" x2="1040" y2="1720" stroke="#fff" stroke-width="4" stroke-opacity="0.5" /></svg>
      <svg width="{W}" height="{H}" id="s7-cat" style="{GLOW}">{cat(540, 770, 1.05, face=True)}</svg>
      <div id="s7-sweep" style="position:absolute;left:-1100px;top:-200px;width:800px;height:2400px;
           background:linear-gradient(105deg, rgba(242,179,61,0) 0%, rgba(255,226,160,0.10) 30%, rgba(255,226,160,0.26) 50%, rgba(255,226,160,0.10) 70%, rgba(242,179,61,0) 100%);mix-blend-mode:screen;"></div>
    </div>
    <svg width="{W}" height="{H}" id="s7-grain" style="opacity:0.11;mix-blend-mode:screen;">
      <filter id="s7-n"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3" /></filter>
      <rect x="-60" y="-60" width="{W + 120}" height="{H + 120}" filter="url(#s7-n)" />
    </svg>
"""
    tl.set("#s7-hero, #s7-flash", "{opacity:0}")
    tl.fromto("#s7-flash", "{opacity:0.85}", "{opacity:0, duration:0.14, ease:'power2.out'}", 0.0)
    for k, dx, dy, rot in moves:
        tl.to(f"#s7-sh{k}", f"{{x:{dx:.0f}, y:{dy:.0f}, rotation:{rot:.0f}, transformOrigin:'50% 50%', duration:0.7, ease:'expo.out'}}", 0.0)
    tl.set("#s7-hit", "{opacity:0}", hero - 0.02)
    tl.set("#s7-hero", "{opacity:1}", hero - 0.02)
    tl.fromto("#s7-hero", f"{{scale:1, transformOrigin:{org(540, 900)}}}", f"{{scale:1.07, duration:{TAIL - hero:.3f}, ease:'none'}}", hero - 0.02)
    tl.fromto("#s7-sweep", "{x:0}", "{x:2400, duration:1.7, ease:'power1.inOut'}", hero + 0.5)
    for k in range(int(TAIL * 15)):                                   # grain jitters on twos
        tl.set("#s7-grain", f"{{x:{(k * 37) % 60 - 30}, y:{(k * 53) % 60 - 30}}}", k / 15)
    tl.to("#s7-all", "{opacity:0, duration:0.3}", TAIL - 0.32)
    return scene("s7", t0, t1, body, tl)

# ------------------------------------------------------------------ the project

def build():
    lines = load_lines()
    T_ = T(lines)
    scenes, e = build_scenes(T_)
    scenes.append(payoff(e))
    total = e + TAIL
    os.makedirs(os.path.join(HF, "compositions"), exist_ok=True)
    for f in os.listdir(os.path.join(HF, "compositions")):
        if f.endswith(".html") and f[:-5] not in [s[0] for s in scenes]:
            os.remove(os.path.join(HF, "compositions", f))
    hosts = []
    for k, (name, t0, t1, html) in enumerate(scenes):
        open(os.path.join(HF, "compositions", f"{name}.html"), "w", encoding="utf-8").write(html)
        hosts.append(f'      <div id="{name}" data-composition-id="{name}" data-composition-src="compositions/{name}.html" '
                     f'data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="{k + 1}" data-track-kind="graphics" '
                     f'data-width="{W}" data-height="{H}"></div>')
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
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-fps="{FPS}" data-width="{W}" data-height="{H}">
      <div id="bg"></div>
{chr(10).join(hosts)}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    open(os.path.join(HF, "index.html"), "w", encoding="utf-8").write(index)
    json.dump({"lines": lines, "end_speech": e, "total": total,
               "scenes": [(n, round(a, 3), round(b, 3)) for n, a, b, _ in scenes]},
              open(os.path.join(OUT, "timing.json"), "w"), indent=1)
    print(f"built {HF}: {len(scenes)} scenes, payoff cut {e:.2f} s, total {total:.2f} s")
    return total, e

def hf(*args, timeout=900):
    r = subprocess.run(["npx", "hyperframes", *args], cwd=HF, capture_output=True, text=True, timeout=timeout, shell=True)
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode, "\n".join(l for l in out.splitlines() if "npm notice" not in l)

# ------------------------------------------------------------------ sound (recorded effects from the Sonniss GDC 2026 bundle)

SFX = {
    "hit": "Cinematic Sound Design - Ultra Transitions & Impacts/Impact Hit Rapid Chord Reverb.wav",
    "punch": "Epic Stock Media - Anime Game/FGHTImpt_Combat Punch Impact Light Hit Delay Crunchy Vintage Quick Smack 05_ESM_AG.wav",
    "woosh": "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav",
    "snap": "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav",
    "pop": "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav",
    "clink": "Cinematic Sound Design - Interface & Infographics/Interface Accept Glassy Snap.wav",
    "shatter": "Epic Stock Media - Tower Defense Game/ICEBrk_Skill Freeze Whoosh Break Impact Layered Movement Shatter 03_ESM_TDG.wav",
    "shards": "Epic Stock Media - Elemental Mutation Whooshes and Impacts/GLASMvmt_Whoosh Glass Crystal Fragments Sharp Shards Dry 05_ESM_EMWI.wav",
    "scratch": "InMotionAudio - Scratch Card/OBJMisc_ScratchCard_SurfaceWipe_04_InMotionAudio_ScratchCard.wav",
    "sweep": "Cinematic Sound Design - Colossal Impacts/Impact Cut Sweep.wav",
    "flash": "344 Audio - Car Foley Vol. 1/VEHInt_LIGHTING CONTROL, RELEASE, HEADLIGHT FLASH_344 Audio_Car Foley Vol 1.wav",
}
MUSIC_UNDER = -7.0
MUSIC_PAYOFF = -1.0

def music_bed(total, e, last_word, voice):
    """The TikTok's own bed, its drop on the payoff cut, ducked under the voice, up for the payoff, faded at the end."""
    import numpy as np, soundfile as sf
    from scipy.signal import resample_poly
    from common import SR
    m, sr = sf.read(MUSIC, dtype="float64")
    m = resample_poly(m.mean(1) if m.ndim > 1 else m, SR, sr)
    off = DROP - e
    if off < 0:
        raise SystemExit("speech runs longer than the song before its drop")
    seg = m[int(off * SR):int((off + total) * SR)]
    t = np.arange(len(seg)) / SR
    rms = lambda x: np.sqrt(np.mean(x ** 2)) + 1e-9
    v = voice[np.abs(voice) > 0.02]
    ref = 20 * np.log10(rms(v) / rms(m[int(off * SR):int(DROP * SR)]))
    lo, hi = 10 ** ((ref + MUSIC_UNDER) / 20), 10 ** ((ref + MUSIC_PAYOFF) / 20)
    g = np.interp(t, [0, last_word + 0.1, e, total], [lo, lo, hi, hi])
    g *= np.clip(t / 0.12, 0, 1) * np.clip((total - t) / 0.8, 0, 1)
    print(f"music: song {off:.2f} to {off + total:.2f} s, drop at our {e:.2f} s, bed {ref + MUSIC_UNDER:+.1f} dB")
    return seg * g

def build_audio(lines, total, e, path):
    import sfx
    from common import new_track, add, save_wav
    from render_led import common_load
    T_ = T(lines)
    tr = new_track(total)
    voice = common_load(os.path.join(OUT, "narration_fixed.wav"))[:len(tr)]
    tr[:len(voice)] += voice
    bed = music_bed(total, e, T_.end(len(lines) - 1), voice)
    tr[:len(bed)] += bed
    hit = lambda t, key, gain, **kw: add(tr, t, sfx.clip(SFX[key], **kw), gain)
    hit(T_(0, "or"), "woosh", 0.06)                          # the frame goes up
    hit(T_(0, "up") - 0.02, "punch", 0.11)
    hit(T_(1, "counter"), "snap", 0.08)
    hit(T_(2, "chicken") - 0.02, "pop", 0.08)
    hit(T_(3, "jump") - 0.02, "woosh", 0.07)
    hit(T_(3, "work", end=True) - 0.08, "snap", 0.08)
    hit(T_(3, "asleep", end=True) - 0.08, "snap", 0.08)
    hit(T_(3, "Now") - 0.02, "punch", 0.13)
    hit(T_(4, "Why") - 0.02, "punch", 0.09)
    hit(T_(4, "glass"), "clink", 0.07)
    hit(T_(4, "plant"), "pop", 0.07)
    hit(T_(4, "full"), "pop", 0.07)
    hit(T_(5, "Missing", 0), "scratch", 0.06)
    hit(T_(5, "land") - 0.02, "punch", 0.08)
    hit(T_(7, "counter"), "clink", 0.1)                     # the tap that tips it
    hit(e - 0.02, "hit", 0.28)                               # the drop: the loudest sound in the film
    hit(e - 0.01, "shatter", 0.16)
    hit(e + 0.05, "shards", 0.1)
    hit(e + 0.9 + 0.5 - 0.03, "flash", 0.14)                 # the light sweep across the hero shot
    hit(e + 0.9 + 0.5 - 0.05, "sweep", 0.05, hp=60)
    save_wav(tr, path, total)

def render(picture=True):
    total, e = build()
    lines = load_lines()
    pic = os.path.join(OUT, "picture.mp4")
    if picture or not os.path.exists(pic):
        code, out = hf("render", "-o", pic, "--quality", "delivery", timeout=3600)
        print(out[-2000:])
        if code:
            raise SystemExit("render failed")
    wav = os.path.join(OUT, "cat.wav")
    build_audio(lines, total, e, wav)
    mux = os.path.join(OUT, "cat_mux.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pic, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", mux], check=True)
    final = os.path.join(OUT, "cat.mp4")
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
        code, out = hf("snapshot", "--at", sys.argv[2], timeout=600)
        print(out[-3000:])
