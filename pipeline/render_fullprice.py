"""'He Wanna Pay Full Price' (ops/episodes/2026-11-26-full-price.md): the week's rising SNL sound ("He wanna pay full
price", from the Druski-hosted episode) carried by the calm "there's a quote I think about often" voiceover form, on
Black Friday. White line art on black, built in HyperFrames (pipeline/hf/fullprice) on the raw liver kit
(render_liver.py), timed to the narration's words. The one color (gold) is kept back for FULL PRICE.

python render_fullprice.py voice                voice the script (Fish Drama 3), even it out, print the timing
python render_fullprice.py build                write the HyperFrames project from out/fullprice/narration_fixed.json
python render_fullprice.py stills 1.0,9.5,...   build, then snapshot those times
python render_fullprice.py render               build, render the picture, mix the sound, mux to out/fullprice/fullprice.mp4
python render_fullprice.py audio                the same, but keep the last picture.mp4 and redo only the sound
"""
import json, os, subprocess, sys
from common import ROOT
from render_liver import T, TL, words, pill, scene, PERSON, W, H, FPS, CSS

HF = os.path.join(ROOT, "hf", "fullprice")
OUT = os.path.join(ROOT, "out", "fullprice")
GOLD = "#F2B33D"
TAIL = 1.4

SCRIPT = [
    "[calm, soft, reflective, like a quiet late-night thought] There's a quote I think about often.",
    "[calm, reflective] Every Black Friday, the whole world lines up for a discount.",
    "[calm, slow, listing] Doorbusters. Seventy percent off. Buy one, get one free.",
    "[calm, a little in awe] And one man walks right past all of it.",
    "[calm, quiet] Straight to the register. Because...",
    "[suddenly shouting with huge, silly, joyful excitement] He wanna pay full price!",
]
GAPS = [0.45, 0.35, 0.4, 0.35, 0.55]

def load_lines():
    return json.load(open(os.path.join(OUT, "narration_fixed.json")))

GLOW = "filter: drop-shadow(0 0 12px rgba(255,255,255,0.65)) drop-shadow(0 0 36px rgba(255,255,255,0.25));"
GGLOW = "filter: drop-shadow(0 0 14px rgba(242,179,61,0.95)) drop-shadow(0 0 44px rgba(242,179,61,0.5));"

def quotes(x, y, s=1.0, color="#fff"):
    """Two big opening quote marks in line art."""
    one = "M 0 0 C -40 0 -58 -30 -58 -60 C -58 -96 -30 -118 0 -118 M -58 -60 C -58 -20 -30 30 20 46"
    return (f'<g transform="translate({x},{y}) scale({s})" fill="none" stroke="{color}" stroke-width="{9 / s:.2f}" '
            f'stroke-linecap="round" stroke-linejoin="round"><path d="{one}" pathLength="1"/>'
            f'<path d="{one}" transform="translate(110,0)" pathLength="1"/></g>')

def register(x, y, s=1.0, color="#fff"):
    """A cash register: body, a raised display, a key grid, a drawer."""
    keys = "".join(f'<rect x="{-70 + 40 * c}" y="{-70 + 30 * r}" width="26" height="18" rx="4"/>'
                   for r in range(3) for c in range(4))
    return (f'<g transform="translate({x},{y}) scale({s})" fill="none" stroke="{color}" stroke-width="{6 / s:.2f}" '
            f'stroke-linejoin="round"><path d="M -110 -100 L 110 -100 L 130 40 L -130 40 Z"/>'
            f'<rect x="-50" y="-170" width="100" height="56" rx="8"/><line x1="0" y1="-114" x2="0" y2="-100"/>{keys}'
            f'<rect x="-140" y="40" width="280" height="56" rx="6"/><line x1="-30" y1="68" x2="30" y2="68"/></g>')

def tag(x, y, s=1.0, color="#fff", sw=6):
    """A price tag with its hole and string."""
    return (f'<g transform="translate({x},{y}) scale({s})" fill="none" stroke="{color}" stroke-width="{sw / s:.2f}" '
            f'stroke-linejoin="round" stroke-linecap="round"><path d="M -150 -70 L 110 -70 L 170 0 L 110 70 L -150 70 Z" pathLength="1"/>'
            f'<circle cx="112" cy="0" r="14"/><path d="M 126 0 C 170 -40 200 -60 240 -40"/></g>')

def build_scenes(T_):
    sc = []
    cut = lambda i: T_.start(i) - 0.12

    # 1. there's a quote I think about often (frame 0: the quote marks drawn, BLACK FRIDAY above, glowing)
    t0, t1 = 0.0, cut(1)
    tl = TL(t0, "s1")
    a, _ = words("s1-a", "THERE'S A QUOTE", 900, 46)
    b, _ = words("s1-b", "I THINK ABOUT OFTEN", 972, 46, cls="dim")
    body = f"""
    <div class="t glow" style="top:330px;font-size:64px;">BLACK FRIDAY</div>
    <svg width="{W}" height="{H}" id="s1-q" style="{GLOW}">{quotes(490, 700, 1.4)}</svg>
    {a}
    {b}
"""
    ws = [w["start"] for w in T_.lines[0]["words"]]
    tl.word_in("s1-a", [tl.at(x) for x in ws[:3]])
    tl.word_in("s1-b", [tl.at(x) for x in ws[3:7]])
    tl.blur_out(f"#{tl.name}-all", tl.at(t1) - 0.16)
    sc.append(scene("s1", t0, t1, body, tl))

    # 2. the whole world lines up for a discount (a long queue walks toward a tag)
    t0, t1 = cut(1), cut(2)
    tl = TL(t0, "s2")
    a, _ = words("s2-a", "EVERY BLACK FRIDAY", 520, 40, cls="dim")
    gy = 1120
    queue = "".join(f'<g id="s2-p{k}">{PERSON.format(x=170 + k * 82, y=gy, s=1.1)}</g>' for k in range(8))
    body = f"""
    {a}
    <div class="t glow" id="s2-d" style="top:600px;font-size:84px;">A DISCOUNT</div>
    <svg width="{W}" height="{H}" style="{GLOW}"><line x1="90" y1="{gy}" x2="990" y2="{gy}" stroke="#fff" stroke-width="4"/>{queue}</svg>
"""
    ws = [w["start"] for w in T_.lines[1]["words"]]
    tl.set("#s2-d", "{opacity:0}")
    tl.word_in("s2-a", [tl.at(x) for x in ws[:3]])
    for k in range(8):
        tl.fromto(f"#s2-p{k}", "{opacity:0, x:-60}", f"{{opacity:1, x:0, duration:0.4, ease:'power3.out'}}", 0.05 + 0.08 * k)
    tl.slam("#s2-d", tl.at(T_(1, "discount")), shake=False)
    tl.blur_out(f"#{tl.name}-all", tl.at(t1) - 0.16)
    sc.append(scene("s2", t0, t1, body, tl))

    # 3. doorbusters, seventy percent off, buy one get one free (three pills slam on their words)
    t0, t1 = cut(2), cut(3)
    tl = TL(t0, "s3")
    body = f"""
    <svg width="{W}" height="{H}" id="s3-tag" style="{GLOW}">{tag(520, 560, 1.3)}</svg>
    {pill("s3-a", "DOORBUSTERS", 820, 48)}
    {pill("s3-b", "70% OFF", 940, 64)}
    {pill("s3-c", "BUY ONE GET ONE", 1080, 48)}
"""
    tl.set("#s3-tag path", "{strokeDasharray:1, strokeDashoffset:1}")
    tl.draw("#s3-tag path", 0.05, 0.4, "power3.out")
    tl.slam("#s3-a", tl.at(T_(2, "Doorbusters")), shake=False)
    tl.slam("#s3-b", tl.at(T_(2, "Seventy")), shake=False)
    tl.slam("#s3-c", tl.at(T_(2, "Buy")), shake=False)
    tl.blur_out(f"#{tl.name}-all", tl.at(t1) - 0.16)
    sc.append(scene("s3", t0, t1, body, tl))

    # 4. one man walks right past all of it (the queue dims, one figure glows and walks right past the tags)
    t0, t1 = cut(3), cut(5)
    tl = TL(t0, "s4")
    gy = 1120
    crowd = "".join(PERSON.format(x=150 + k * 82, y=gy, s=1.1) for k in range(8))
    a, _ = words("s4-a", "ONE MAN", 520, 84)
    b, _ = words("s4-b", "STRAIGHT TO THE REGISTER", 520, 46)
    body = f"""
    <svg width="{W}" height="{H}" id="s4-crowd" style="opacity:0.3;"><line x1="90" y1="{gy}" x2="990" y2="{gy}" stroke="#fff" stroke-width="4"/>{crowd}</svg>
    <div id="s4-tags" style="position:absolute;inset:0;opacity:0.3;">{pill("s4-t1", "70% OFF", 760, 40, hidden=False)}</div>
    <svg width="{W}" height="{H}" id="s4-reg" style="{GLOW}">{register(800, 900, 1.1)}</svg>
    <svg width="{W}" height="{H}" id="s4-man" style="{GLOW}">{PERSON.format(x=120, y=gy + 160, s=1.6)}</svg>
    {a}
    {b}
"""
    ws3 = [w["start"] for w in T_.lines[3]["words"]]
    ws4 = [w["start"] for w in T_.lines[4]["words"]]
    tl.set("#s4-reg", "{opacity:0}")
    tl.word_in("s4-a", [tl.at(x) for x in ws3[1:3]])
    tl.fromto("#s4-man", "{x:0}", f"{{x:560, duration:{max(1.0, tl.at(T_(4, 'register')) - 0.1):.2f}, ease:'none'}}", 0.0)
    ts = tl.at(T_(4, "Straight"))
    tl.set("#s4-a", "{opacity:0}", ts - 0.04)
    tl.to("#s4-crowd, #s4-tags", "{opacity:0.08, duration:0.3}", ts - 0.04)
    tl.word_in("s4-b", [tl.at(x) for x in ws4[:4]])
    tl.pop("#s4-reg", tl.at(T_(4, "register")))
    tl.to("#s4-b", "{opacity:0.25, duration:0.4}", tl.at(T_(4, "Because")))     # a held breath before the shout
    tl.blur_out(f"#{tl.name}-all", tl.at(t1) - 0.06, 0.06)
    sc.append(scene("s4", t0, t1, body, tl))

    # 5. THE BIG MOMENT: he wanna pay FULL PRICE (gold, the only color in the film)
    t0, t1 = cut(5), T_.end(5) + TAIL
    tl = TL(t0, "s5")
    a, _ = words("s5-a", "HE WANNA PAY", 560, 60)
    body = f"""
    {a}
    <div id="s5-flash" style="position:absolute;inset:0;background:radial-gradient(ellipse at 50% 45%, rgba(242,179,61,0.4) 0%, rgba(242,179,61,0) 60%);"></div>
    <svg width="{W}" height="{H}" id="s5-tag" style="{GGLOW}">{tag(560, 1250, 1.5, GOLD, 8)}</svg>
    <div class="t" id="s5-fp" style="top:680px;font-size:150px;color:{GOLD};text-shadow:0 0 18px rgba(242,179,61,0.85),0 0 60px rgba(242,179,61,0.45);">FULL<br>PRICE</div>
    <div class="t" id="s5-pct" style="top:1212px;font-size:60px;color:{GOLD};">0% OFF</div>
"""
    ws = [w["start"] for w in T_.lines[5]["words"]]
    tl.set("#s5-flash, #s5-fp, #s5-pct, #s5-tag", "{opacity:0}")
    tl.set("#s5-tag path", "{strokeDasharray:1, strokeDashoffset:1}")
    tl.word_in("s5-a", [tl.at(x) for x in ws[:3]])
    tf = tl.at(T_(5, "full"))
    tl.slam("#s5-fp", tf)
    tl.fromto("#s5-flash", "{opacity:0}", "{opacity:1, duration:0.06}", tf)
    tl.to("#s5-flash", "{opacity:0.35, duration:0.9, ease:'power2.out'}", tf + 0.1)
    tl.to("#s5-tag", "{opacity:1, duration:0.01}", tf + 0.05)
    tl.draw("#s5-tag path", tf + 0.05, 0.4, "power3.out")
    tl.pop("#s5-pct", tf + 0.45)
    sc.append(scene("s5", t0, t1, body, tl))
    return sc, T_.end(5)

def build():
    lines = load_lines()
    T_ = T(lines)
    scenes, e = build_scenes(T_)
    total = scenes[-1][2]
    os.makedirs(os.path.join(HF, "compositions"), exist_ok=True)
    os.makedirs(os.path.join(HF, "assets"), exist_ok=True)
    for f in ("hyperframes.json", "package.json", "meta.json", "AGENTS.md", "CLAUDE.md"):
        dst = os.path.join(HF, f)
        if not os.path.exists(dst):
            s = open(os.path.join(ROOT, "hf", "cat", f), encoding="utf-8").read().replace('"cat"', '"fullprice"')
            open(dst, "w", encoding="utf-8").write(s)
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
    print(f"built {HF}: {len(scenes)} scenes, speech ends {e:.2f} s, total {total:.2f} s")
    return total, e

def hf(*args, timeout=900):
    r = subprocess.run(["npx", "hyperframes", *args], cwd=HF, capture_output=True, text=True, timeout=timeout, shell=True)
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode, "\n".join(l for l in out.splitlines() if "npm notice" not in l)

# ------------------------------------------------------------------ sound (recorded, Sonniss GDC 2026)

BOX = "Sonic Bat - Music Boxes/"
SFX = {
    "boxA": BOX + "SBmb_Music Box A 013.wav", "boxB": BOX + "SBmb_Music Box B 028.wav",
    "boxC": BOX + "SBmb_Music Box C 059.wav",
    "hit": "Cinematic Sound Design - Ultra Transitions & Impacts/Impact Hit Rapid Chord Reverb.wav",
    "pop": "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav",
    "snap": "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav",
    "woosh": "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav",
}

def build_audio(lines, total, path):
    import sfx
    from common import new_track, add, save_wav
    from render_led import common_load
    T_ = T(lines)
    tr = new_track(total)
    voice = common_load(os.path.join(OUT, "narration_fixed.wav"))[:len(tr)]
    tr[:len(voice)] += voice
    hit = lambda t, key, gain, **kw: add(tr, t, sfx.clip(SFX[key], **kw), gain)
    t, k, stop = 0.05, 0, T_(4, "Because") - 0.1          # a soft music box under the calm part, gone before the shout
    while t + 2.6 < stop:
        hit(t, ("boxA", "boxB", "boxC")[k % 3], 0.05)
        t += 2.6
        k += 1
    hit(T_(1, "discount") - 0.02, "pop", 0.05)
    for w in ("Doorbusters", "Seventy", "Buy"):
        hit(T_(2, w) - 0.02, "snap", 0.06)
    hit(T_(4, "register"), "pop", 0.05)
    hit(T_(5, "full") - 0.03, "hit", 0.22)                 # the big moment: the loudest sound in the film
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
    wav = os.path.join(OUT, "fullprice.wav")
    build_audio(lines, total, wav)
    mux = os.path.join(OUT, "fullprice_mux.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pic, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", mux], check=True)
    final = os.path.join(OUT, "fullprice.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mux, "-c:v", "copy", "-af", "loudnorm=I=-13:TP=-1:LRA=11", "-ar", "48000",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final], check=True)
    print("rendered", final)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else "build"
    if mode == "voice":
        from narrate_cb import narrate
        from voice_fix import fixed
        narrate(SCRIPT, OUT, gap=0.35)
        lines = fixed(OUT, keep_pauses=True, gaps=GAPS)
        for i, l in enumerate(lines):
            print(f"{l['start']:6.2f} {l['end']:6.2f}  {l['text']}")
        raise SystemExit
    if mode in ("render", "audio"):
        render(picture=mode == "render")
        raise SystemExit
    build()
    if mode == "stills":
        code, out = hf("snapshot", "--at", sys.argv[2], timeout=600)
        print(out[-3000:])
