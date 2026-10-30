"""'Hypergamy, but backwards': Austin's Oct 29 role-reversal idea as a deadpan clay short. She walks down a staircase of
worse and worse men while a net worth counter falls and her interest climbs. Hypogamy is the real word; the rest is a joke.

python render_hypo.py out.mp4 out.wav     full render (Blender frames are cached in out/hypo/frames)
python render_hypo.py preview 1.0,12.5    render and composite stills into preview/
python render_hypo.py times               narrate and print the event times

Facts and links: ops/episodes/2026-10-30-hypergamy-backwards.md
"""
import json, math, os, sys
import skia
from common import *
import render_tap as tap
import kit3d as K
import render_dst as D                       # pill, sound files and remux; also switches captions to clay

tap.LEXICON["hypogamy"] = "haɪpˈɑːɡəmi"     # hy-POG-uh-mee

FPS = 30
TAIL = 1.6
SCRIPT = [
    ("A", "Hypergamy has an *opposite.* It's called *hypogamy.* Dating *down.*"),
    ("B", "She starts at the top. A *neurosurgeon.* Full head of hair. Owns his *house.*"),
    ("C", "*Disgusting.* She gives him two weeks' *notice.*"),
    ("D", "Step two. A *regional manager.* He still has a *401(k){four oh one kay}.* She can smell it on him."),
    ("E", "Step three. A guy with a *podcast.* Four listeners. One is his *mom.*"),
    ("F", "Better. But he owns a *bed frame.*"),
    ("G", "Step four. He sells *vapes* at the mall. He calls the kiosk his *office.*"),
    ("H", "Step five. He lives{/lˈɪvz/} in a *Honda Civic.* He owes her *forty dollars.*"),
    ("I", "She has never felt more *alive.*"),
    ("J", "Her friends all tell her the same thing. *You could do so much worse.*"),
    ("K", "So she *does.*"),
]
EXTRA_GAP = {1: 0.1, 2: 0.15, 3: 0.55, 4: 0.55, 5: 0.15, 6: 0.55, 7: 0.55, 8: 0.2, 9: 0.2, 10: 0.7}
OUT = os.path.join(ROOT, "out", "hypo")
FRAMES = os.path.join(OUT, "frames")

def events(sents, speech_end):
    w = lambda si, sub, n=0: D.wn(sents, si, sub, n)
    E = {k: sents[i]["t0"] for i, k in enumerate("ABCDEFGHIJK")}
    E.update({"hair": w(1, "Full"), "notice": w(2, "She"), "401": w(3, "401"), "smell": w(3, "She"), "listeners": w(4, "Four"),
              "bed": w(5, "bed"), "office": w(6, "calls"), "forty": w(7, "owes"), "worse": w(9, "You"), "does": w(10, "does"),
              "speech_end": speech_end})
    return E

# ------------------------------------------------------------------ sound (recorded effects, see sfx.py)

F = dict(D.F)
F.update({"marimba": F["kalimba"]})

def build_audio(sents, E, duration, path):
    import sfx
    n = int(duration * SR)
    tr = new_track(duration)
    tr[:n] += K.voice_track(sents, duration)[:n]
    hit = lambda t0, key, gain, **kw: add(tr, t0, sfx.clip(F[key], **kw), gain)
    hit(0.0, "braam", 0.10, lp=2200)
    hit(0.0, "pop", 0.14, rate=0.8)
    stops = [E["D"], E["E"], E["G"], E["H"], E["K"]]
    for k, t1 in enumerate(stops):                         # her heels down each staircase, then the counter drops
        for i in range(8):
            hit(t1 - 1.15 + i * 0.14, "perc", 0.10, rate=0.65 + 0.03 * (i % 3), dur=0.1, lp=3000)
        hit(t1 - 1.15, "cloth", 0.12, dur=0.5, lp=5000)
        hit(t1, "deny", 0.10, rate=1.0 - 0.06 * k)
        hit(t1 + 0.05, "pop", 0.13, rate=1.1 - 0.08 * k)
    hit(E["C"], "deny", 0.12, rate=0.8)
    hit(E["401"], "kalimba", 0.11)
    hit(E["bed"] - 0.05, "perc", 0.14, rate=0.8)
    hit(E["G"] + 1.0, "swoosh", 0.08)
    hit(E["G"] + 2.6, "swoosh", 0.08)
    hit(E["I"], "kalimba", 0.13, rate=1.2)
    hit(E["K"] - 0.2, "woosh", 0.1)
    hit(E["does"] + 0.25, "bass", 0.12, lp=2500)
    hit(E["does"] + 0.5, "kalimba", 0.13, rate=1.3)
    save_wav(tr, path, duration)

# ------------------------------------------------------------------ overlay

WORTH = ["$6,200,000", "$184,000", "$312", "$212", "-$40", "1/2 SANDWICH"]
LOVE = [3, 11, 38, 64, 97, 100]
TITLES = [("m0", "NEUROSURGEON"), ("m1", "REGIONAL MANAGER"), ("m2", "PODCASTER"), ("m3", "VAPE ENTREPRENEUR"), ("m4", "LIVES IN CAR"), ("rac", "RACCOON")]

def draw_hook(c, t, a):
    if a <= 0:
        return
    y = 300
    for s, k in (("Hypergamy,", False), ("but backwards", True)):
        ff = font("Bricolage-800", 104)
        wd = ff.measureText(s) + (40 if k else 0)
        x = W / 2 - wd / 2
        if k:
            c.drawRRect(tap.rrect(x, y - 88, x + wd, y + 28, 16), paint(tap.RED, a))
            c.drawString(s, x + 20, y, ff, paint(INK, a))
        else:
            c.drawString(s, x, y, ff, paint(INK, a))
        y += 124

def counter(c, t, E, stops):
    a = K.fade(t, E["B"] + 0.5, E["speech_end"] + 1.3, 0.25)
    if a <= 0:
        return
    k = max(i for i in range(6) if t >= stops[i])
    pulse = 1 - D.smooth01((t - stops[k]) / 0.35)
    x0, y0 = 60, 1320
    c.drawRRect(tap.rrect(x0, y0, 770, y0 + 196, 18), paint(K.DARK_PILL, a))
    f1, f2 = font("JetBrainsMono-700", 28), font("Bricolage-800", 52)
    red = skia.Color(255, 110, 90)
    c.drawString("HIS NET WORTH", x0 + 26, y0 + 44, f1, paint(MUTED, a))
    s = WORTH[k]
    c.drawString(s, x0 + 26, y0 + 102, f2, paint(red if pulse > 0 else INK, a))
    c.drawString("HER INTEREST", x0 + 26, y0 + 146, f1, paint(MUTED, a))
    bx0, bx1, by = x0 + 270, 744, y0 + 124
    c.drawRRect(tap.rrect(bx0, by, bx1, by + 22, 11), paint(skia.Color(70, 70, 76), a))
    prev = LOVE[k - 1] if k else LOVE[0]
    v = prev + (LOVE[k] - prev) * D.smooth01((t - stops[k]) / 0.5)
    c.drawRRect(tap.rrect(bx0, by, bx0 + (bx1 - bx0) * v / 100, by + 22, 11), paint(D.GREEN, a))
    pc = f"{int(round(v))}%"
    c.drawString(pc, x0 + 26, y0 + 182, f1, paint(D.GREEN, a))

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, t, K.fade(t, -1, E["B"] - 0.05, 0.2))
    tap.draw_captions(c, t, sents, cm)
    c.restore()
    stops = [0.0, E["D"], E["E"], E["G"], E["H"], E["K"]]
    lab = font("JetBrainsMono-700", 30)
    windows = [(E["B"] + 0.1, E["hair"]), (E["D"], E["401"] - 0.2), (E["E"], E["listeners"]), (E["G"], E["office"]), (E["H"], E["forty"]), (E["does"] + 0.2, speech_end + 1.5)]
    for (name, text), (t0, t1) in zip(TITLES, windows):
        a = K.fade(t, t0, t1, 0.15)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + (-90 if p[0] > 700 else 70), p[1] - 110, a, D.GOLD, lab)
    for name, text, t0, t1, dx, dy in (("pig", "401(K)", E["401"], E["smell"] - 0.05, -120, -150), ("bed", "BED FRAME", E["bed"] - 0.2, E["G"] - 1.3, 90, -210),
                                       ("door", "WRONG COLOR DOOR", E["H"] + 1.2, E["forty"], -40, 140)):
        a = K.fade(t, t0, t1, 0.15)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, tap.RED, lab)
    counter(c, t, E, stops)
    D.pill(c, "HYPOGAMY IS A REAL WORD. THE REST IS A JOKE.", W / 2, 1282, K.fade(t, E["does"] + 0.3, speech_end + 1.6, 0.15), MUTED, size=25)

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
    K.run_blender("hypo_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0]
    if not preview_times:
        build_audio(sents, E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "hypo" if preview_times else None)

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
