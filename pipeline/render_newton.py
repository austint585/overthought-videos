"""'Newton's first law of the ex': a deadpan clay short in the Schrödinger's Situationship style. Lex I of the Principia
(1687) applied to an ex who goes quiet for months and then texts 'hey stranger' eleven minutes after you post someone
new. Same clay bedroom as 'The same hour twice' (newton_scene.py is that set with the ex as a ball at rest).

python render_newton.py out.mp4 out.wav     full render (Blender frames are cached in out/newton/frames)
python render_newton.py preview 1.0,12.5    render and composite stills into preview/
python render_newton.py times               narrate and print the event times

Facts and links: ops/episodes/2026-10-29-newton-first-law-ex.md (Newton, Principia, 1687, Law I).
"""
import json, math, os, sys
import skia
from common import *
import render_tap as tap
import kit3d as K
import render_dst as D                       # pill, card, sound files and remux; also switches captions to clay

FPS = 60
TAIL = 1.4
SCRIPT = [
    ("A", "Your *ex* runs on *Newton's first law.*"),
    ("B", "In *1687{sixteen eighty-seven},* Newton wrote that a body at *rest* stays at *rest,*"),
    ("C", "unless an *outside force* makes it *change.*"),
    ("D", "Your ex has been at rest for *seven months.* No texts. No likes. *Nothing.*"),
    ("E", "Then you post someone *new.*"),
    ("F", "*Outside force:* applied."),
    ("G", "Eleven minutes later. *Hey stranger.*"),
    ("H", "But the law works both ways. A body in *motion* stays in *motion.*"),
    ("I", "So if you're *moving on,* keep *moving.*"),
    ("J", "Do not *reply.* Newton would not *reply.*"),
]
EXTRA_GAP = {3: 0.1, 4: 0.2, 5: 0.3, 6: 0.3, 7: 0.35, 9: 0.25}
OUT = os.path.join(ROOT, "out", "newton")
FRAMES = os.path.join(OUT, "frames")

def events(sents, speech_end):
    w = lambda si, sub, n=0: D.wn(sents, si, sub, n)
    s = lambda si: sents[si]["t0"]
    E = {k: s(i) for i, k in enumerate("ABCDEFGHIJ")}
    E.update({"law": w(0, "first"), "1687": w(1, "1687"), "rest": w(1, "rest", 1), "force": w(2, "force"),
              "months": w(3, "months"), "nothing": w(3, "Nothing"), "new": w(4, "new"), "applied": w(5, "applied"),
              "stranger": w(6, "stranger"), "motion": w(7, "motion", 1), "moving": w(8, "moving", 1),
              "reply": w(9, "reply"), "toss": w(9, "reply", 1), "speech_end": speech_end})
    return E

# ------------------------------------------------------------------ sound (recorded effects, see sfx.py; files listed in render_dst.F)

F = dict(D.F)

def build_audio(sents, E, duration, path):
    import sfx
    n = int(duration * SR)
    voice = K.voice_track(sents, duration)[:n]
    tr = new_track(duration)
    tr[:n] += voice
    hit = lambda t0, key, gain, **kw: add(tr, t0, sfx.clip(F[key], **kw), gain)
    ticks = sfx.onsets(F["tick"], 0.25, 12)
    t, k = 0.0, 0
    while t < duration - 0.3:                              # the bedside clock, quietly
        hit(t, "tick", 0.04, start=ticks[k % len(ticks)], dur=0.12, hp=300)
        t += 1.0
        k += 1
    hit(0.0, "braam", 0.12, lp=2500)
    hit(E["1687"], "kalimba", 0.13)
    hit(E["months"], "deny", 0.12, rate=0.9)
    hit(E["new"], "pop", 0.16)
    hit(E["F"] - 0.15, "woosh", 0.14)
    hit(E["F"] + 0.35, "perc", 0.2, rate=0.8)
    hit(E["F"] + 0.4, "swoosh", 0.12)
    hit(E["stranger"] - 0.15, "pop", 0.18, rate=0.85)
    hit(E["H"] - 0.2, "woosh", 0.1)
    hit(E["toss"] + 0.2, "cloth", 0.25, dur=0.6, lp=6000)
    hit(E["toss"] + 0.6, "bass", 0.15, lp=2500)
    save_wav(tr, path, duration)

# ------------------------------------------------------------------ overlay

GOLD, GREEN, BLUE = D.GOLD, D.GREEN, D.BLUE
ORANGE = skia.Color(255, 160, 40)

def draw_hook(c, t, E, a):
    if a <= 0:
        return
    y = 300
    for s, k in (("Newton's first", False), ("law of the ex", True)):
        ff = font("Bricolage-800", 104)
        wd = ff.measureText(s) + (40 if k else 0)
        x = W / 2 - wd / 2
        if k:
            c.drawRRect(tap.rrect(x, y - 88, x + wd, y + 28, 16), paint(tap.RED, a))
            c.drawString(s, x + 20, y, ff, paint(INK, a))
        else:
            c.drawString(s, x, y, ff, paint(INK, a))
        y += 124

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, t, E, K.fade(t, -1, E["B"] - 0.05, 0.2))
    tap.draw_captions(c, t, sents, cm)
    c.restore()
    lab = font("JetBrainsMono-700", 30)
    tags = [
        ("ex", "THE EX (AT REST)", E["B"] + 0.3, E["D"] - 0.1, 160, -170, BLUE),
        ("force", "OUTSIDE FORCE", E["F"] - 0.05, E["F"] + 1.2, -60, -200, tap.RED),
        ("ex", "BACK IN MOTION", E["G"] + 0.1, E["H"] - 0.1, 150, -170, ORANGE),
        ("you", "YOU (IN MOTION)", E["motion"] - 0.1, E["J"] - 0.1, 120, -200, GREEN),
    ]
    for name, text, t0, t1, dx, dy, col in tags:
        a = K.fade(t, t0, t1, 0.2)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, col, lab)
    D.card(c, t, [("TEXTS", "0", GOLD, E["D"] + 1.2), ("LIKES", "0", GOLD, E["D"] + 1.7),
                  ("VELOCITY", "0 m/s", BLUE, E["nothing"] - 0.1)],
           E["months"] - 0.15, E["E"] - 0.1, "Newton, Principia, Law I, 1687", y0=1080)
    D.pill(c, "POSTED 2:47  /  TEXTED 2:58", W / 2, 1440, K.fade(t, E["G"] - 0.1, E["H"] - 0.15, 0.15), GOLD)
    D.pill(c, "STAY IN MOTION", W / 2, 1440, K.fade(t, E["toss"] + 0.3, speech_end + 1.4, 0.15), GREEN)
    if t > speech_end + 0.1:
        a = D.smooth01((t - speech_end - 0.1) / 0.4)
        text_center(c, "@overthought.daily", W / 2, 1530, font("JetBrainsMono-500", 32), paint(MUTED, a))

# ------------------------------------------------------------------ main

def setup():
    sents, speech_end = K.narrate(SCRIPT, OUT, EXTRA_GAP)
    duration = speech_end + TAIL
    return sents, speech_end, duration, events(sents, speech_end)

def main(out_mp4, out_wav, preview_times=None):
    sents, speech_end, duration, E = setup()
    n_frames = int(round(duration * FPS))
    print(f"duration {duration:.1f}s, {n_frames} frames", flush=True)
    frames = sorted({min(n_frames - 1, int(round(x * FPS))) for x in preview_times}) if preview_times else range(n_frames)
    K.run_blender("newton_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    if preview_times:                                   # CPU previews come out at half size
        from PIL import Image
        for f in frames:
            path = os.path.join(FRAMES, f"f_{f + 1:05d}.png")
            im = Image.open(path)
            if im.size != (1080, 1920):
                im.resize((1080, 1920), Image.LANCZOS).save(path)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0]
    if not preview_times:
        build_audio(sents, E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "newton" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "times":
        sents, speech_end, duration, E = setup()
        print(json.dumps({k: round(v, 2) for k, v in E.items()}, indent=1))
        print("duration", round(duration, 2))
    elif sys.argv[1] == "audio":
        sents, speech_end, duration, E = setup()
        build_audio(sents, E, duration, sys.argv[3])
        D.remux(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "preview":
        main(None, None, preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
