"""'The entropy of the talking stage': a deadpan clay short in the Schrödinger's Situationship style. Clausius's second
law applied to texting: left alone, the replies shrink from paragraphs to a thumbs up. Same clay bedroom as 'The same
hour twice' and 'The Heisenberg situationship' (entropy_scene.py is that set with speech bubbles and a molecule cube).

python render_entropy.py out.mp4 out.wav     full render (Blender frames are cached in out/entropy/frames)
python render_entropy.py preview 1.0,12.5    render and composite stills into preview/
python render_entropy.py times               narrate and print the event times

Facts and links: ops/episodes/2026-10-29-entropy-talking-stage.md (Clausius 1865: coined 'entropy', 'the entropy of
the universe tends to a maximum').
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
    ("A", "Every *talking stage* obeys the *second law of thermodynamics.*"),
    ("B", "In *1865{eighteen sixty-five},* Rudolf *Clausius{/klˈaʊziəs/}* gave it a name: *entropy.*"),
    ("C", "Leave a system *alone,* and its disorder only goes *up.*"),
    ("D", "Day one: *paragraphs.* Follow-up *questions.* Good morning *texts.*"),
    ("E", "Day four: *haha.*"),
    ("F", "Day nine: *lol.*"),
    ("G", "Day twelve: *hbu{aitch bee you}.*"),
    ("H", "Day fifteen: a *thumbs up.* To a *question.*"),
    ("I", "Clausius{/klˈaʊziəs/} wrote that entropy tends to a *maximum.*"),
    ("J", "The only way to *reverse* it is to put *energy* in from *outside.*"),
    ("K", "And *nobody* is texting *first.*"),
    ("L", "Heat death of a conversation. *Seen,* *2:47{two forty-seven} a.m.{A M}*"),
]
EXTRA_GAP = {3: 0.1, 4: 0.25, 5: 0.25, 6: 0.25, 7: 0.25, 8: 0.2, 10: 0.15, 11: 0.35}
OUT = os.path.join(ROOT, "out", "entropy")
FRAMES = os.path.join(OUT, "frames")

def events(sents, speech_end):
    w = lambda si, sub, n=0: D.wn(sents, si, sub, n)
    s = lambda si: sents[si]["t0"]
    E = {k: s(i) for i, k in enumerate("ABCDEFGHIJKL")}
    E.update({"law": w(0, "second"), "1865": w(1, "1865"), "entropy": w(1, "entropy"), "alone": w(2, "alone"), "up": w(2, "up"),
              "para": w(3, "paragraphs"), "questions": w(3, "questions"), "texts": w(3, "texts"), "haha": w(4, "haha"),
              "lol": w(5, "lol"), "hbu": w(6, "hbu"), "thumbs": w(7, "thumbs"), "question": w(7, "question"),
              "maximum": w(8, "maximum"), "reverse": w(9, "reverse"), "energy": w(9, "energy"), "outside": w(9, "outside"),
              "nobody": w(10, "nobody"), "first": w(10, "first"), "seen": w(11, "Seen"), "speech_end": speech_end})
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
    hit(E["entropy"], "kalimba", 0.13)
    hit(E["up"], "woosh", 0.12)
    hit(E["D"], "pop", 0.16)
    for key, rate in (("haha", 0.95), ("lol", 1.05), ("hbu", 1.15)):
        hit(E[key] - 0.05, "pop", 0.15, rate=rate)
    hit(E["thumbs"] - 0.05, "deny", 0.18)
    hit(E["H"] + 0.2, "cloth", 0.22, dur=0.6, lp=6000)
    hit(E["maximum"], "swoosh", 0.12)
    for j in range(5):
        hit(E["energy"] + 0.12 * j, "perc", 0.09, rate=1.3)
    hit(E["nobody"], "deny", 0.14, rate=0.9)
    hit(E["seen"], "pop", 0.14, rate=0.8)
    hit(E["seen"] + 0.9, "bass", 0.15, lp=2500)
    save_wav(tr, path, duration)

# ------------------------------------------------------------------ overlay

GOLD, GREEN, BLUE = D.GOLD, D.GREEN, D.BLUE
ORANGE = skia.Color(255, 160, 40)

def draw_hook(c, t, E, a):
    if a <= 0:
        return
    y = 300
    for s, k in (("The entropy of the", False), ("talking stage", True)):
        ff = font("Bricolage-800", 100)
        wd = ff.measureText(s) + (40 if k else 0)
        x = W / 2 - wd / 2
        if k:
            c.drawRRect(tap.rrect(x, y - 86, x + wd, y + 28, 16), paint(tap.RED, a))
            c.drawString(s, x + 20, y, ff, paint(INK, a))
        else:
            c.drawString(s, x, y, ff, paint(INK, a))
        y += 122

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, t, E, K.fade(t, -1, E["B"] - 0.05, 0.2))
    tap.draw_captions(c, t, sents, cm)
    c.restore()
    lab = font("JetBrainsMono-700", 30)
    tags = [
        ("mol", "LOW ENTROPY", E["B"] + 0.5, E["alone"] - 0.1, 160, 170, BLUE),
        ("mol", "HIGHER ENTROPY", E["up"] - 0.05, E["D"] - 0.1, 160, 170, ORANGE),
        ("bub", "EFFORT: HIGH", E["questions"] - 0.1, E["E"] - 0.15, -200, 260, GREEN),
        ("guy", "SITTING UP", E["question"] - 0.05, E["I"] - 0.1, 200, 140, GOLD),
    ]
    for name, text, t0, t1, dx, dy, col in tags:
        a = K.fade(t, t0, t1, 0.2)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, col, lab)
    for key, nxt, label in (("D", "E", "DAY 1"), ("E", "F", "DAY 4"), ("F", "G", "DAY 9"), ("G", "H", "DAY 12"), ("H", "I", "DAY 15")):
        D.pill(c, label, W / 2, 1440, K.fade(t, E[key] - 0.1, E[nxt] - 0.15, 0.12), GOLD)
    D.card(c, t, [("DAY 1", "15 WORDS", GREEN, E["I"] - 0.1), ("DAY 15", "0 WORDS", tap.RED, E["I"] + 0.4),
                  ("ENTROPY", "MAXIMUM", ORANGE, E["maximum"] - 0.1)],
           E["I"] - 0.15, E["J"] - 0.1, "Clausius, Annalen der Physik, 1865", y0=1060)
    D.pill(c, "ENERGY FROM OUTSIDE: 0 J", W / 2, 1440, K.fade(t, E["nobody"] - 0.1, E["L"] - 0.1, 0.15), ORANGE)
    D.pill(c, "PEER REVIEWED BY THE GROUP CHAT", W / 2, 1440, K.fade(t, E["seen"] + 1.2, speech_end + 1.4, 0.15), BLUE)
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
    K.run_blender("entropy_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
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
                out_mp4, out_wav, "entropy" if preview_times else None)

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
