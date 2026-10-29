"""'The Heisenberg situationship': a deadpan clay short in the Schrödinger's Situationship style. She shares her
location, so his position data is perfect and his momentum data is zero. Same clay bedroom as 'The same hour twice'
(heis_scene.py is dst_scene.py's set with a particle, arrows and a location pin).

python render_heis.py out.mp4 out.wav     full render (Blender frames are cached in out/heis/frames)
python render_heis.py preview 1.0,12.5    render and composite stills into preview/
python render_heis.py times               narrate and print the event times

Facts and links: ops/episodes/2026-10-28-heisenberg-situationship.md (Heisenberg 1927, Zeitschrift fur Physik 43;
Kennard 1927 for the h-bar over two bound; NIST CODATA for h).
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
    ("A", "Every *situationship* runs on the *Heisenberg uncertainty principle.*"),
    ("B", "In *1927{nineteen twenty-seven},* Heisenberg showed you can't pin down a particle's *position* and its *momentum* at once."),
    ("C", "The better you know *where* it is, the less you know *where it's going.*"),
    ("D", "So she *shares her location.*"),
    ("E", "Position: *known.* Down to the *driveway.*"),
    ("F", "Momentum: *undefined.*"),
    ("G", "Exclusive? *Unknown.* Meeting the parents? *Unknown.* Is this going *anywhere?* Physics says you *can't know.*"),
    ("H", "The uncertainty never drops below *h-bar over two{h bar over two}.* That's a decimal point, *thirty-four zeros,* then a five."),
    ("I", "Which is also how much *clarity* you're getting."),
    ("J", "Stop *refreshing* the map. Measuring it makes it *worse.*"),
]
EXTRA_GAP = {2: 0.1, 4: 0.15, 5: 0.25, 7: 0.15, 8: 0.2, 9: 0.25}
OUT = os.path.join(ROOT, "out", "heis")
FRAMES = os.path.join(OUT, "frames")

def events(sents, speech_end):
    w = lambda si, sub, n=0: D.wn(sents, si, sub, n)
    s = lambda si: sents[si]["t0"]
    E = {k: s(i) for i, k in enumerate("ABCDEFGHIJ")}
    E.update({"heis": w(0, "Heisenberg"), "1927": w(1, "1927"), "position": w(1, "position"), "momentum": w(1, "momentum"),
              "where": w(2, "where"), "going": w(2, "going"), "location": w(3, "location"), "known": w(4, "known"),
              "driveway": w(4, "driveway"), "undefined": w(5, "undefined"), "exclusive": w(6, "Exclusive"),
              "parents": w(6, "parents"), "anywhere": w(6, "anywhere"), "cant": w(6, "can't"), "hbar": w(7, "h-bar"),
              "zeros": w(7, "zeros"), "clarity": w(8, "clarity"), "refresh": w(9, "refreshing"), "worse": w(9, "worse"),
              "speech_end": speech_end})
    return E

# ------------------------------------------------------------------ sound (recorded effects, see sfx.py; files listed in render_dst.F)

F = dict(D.F)
F["ping"] = "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav"

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
    hit(E["B"] + 0.3, "kalimba", 0.13)
    hit(E["position"], "pop", 0.14)
    hit(E["momentum"], "swoosh", 0.12)
    hit(E["going"], "woosh", 0.12)
    hit(E["location"], "pop", 0.18, rate=0.85)
    hit(E["known"], "perc", 0.16)
    hit(E["undefined"], "deny", 0.18)
    hit(E["G"] - 0.15, "cloth", 0.25, dur=0.6, lp=6000)
    for key in ("exclusive", "parents", "anywhere"):
        hit(E[key], "deny", 0.12, rate=1.1)
    hit(E["zeros"], "pop", 0.13, rate=1.15)
    hit(E["I"] - 0.1, "cloth", 0.22, dur=0.6, lp=6000)
    for j in range(3):
        hit(E["refresh"] + 0.35 * j, "perc", 0.12, rate=1.2)
    hit(E["worse"] + 0.3, "bass", 0.15, lp=2500)
    save_wav(tr, path, duration)

# ------------------------------------------------------------------ overlay

GOLD, GREEN, BLUE = D.GOLD, D.GREEN, D.BLUE
ORANGE = skia.Color(255, 160, 40)

def draw_hook(c, t, E, a):
    if a <= 0:
        return
    y = 300
    for s, k in (("The Heisenberg", False), ("situationship", True)):
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
        ("part", "PARTICLE", E["B"] + 0.5, E["momentum"] - 0.1, 200, 160, BLUE),
        ("pin", "POSITION: EXACT", E["known"] - 0.1, E["F"] - 0.1, 180, 320, GREEN),
        ("pin", "MOMENTUM: ???", E["undefined"] - 0.05, E["G"] - 0.1, 180, 320, ORANGE),
        ("guy", "MEASURING AGAIN", E["refresh"] - 0.05, speech_end + 0.2, 200, 140, GOLD),
    ]
    for name, text, t0, t1, dx, dy, col in tags:
        a = K.fade(t, t0, t1, 0.2)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, col, lab)
    D.card(c, t, [("POSITION  x", "KNOWN", GREEN, E["position"] - 0.1), ("MOMENTUM  p", "FUZZY", ORANGE, E["momentum"] - 0.1)],
           E["position"] - 0.15, E["D"] - 0.15, "Heisenberg, Zeitschrift fur Physik 43, 1927", y0=1080)
    D.card(c, t, [("EXCLUSIVE?", "UNKNOWN", ORANGE, E["exclusive"] - 0.1), ("MEET THE PARENTS?", "UNKNOWN", ORANGE, E["parents"] - 0.1),
                  ("GOING ANYWHERE?", "UNKNOWN", tap.RED, E["anywhere"] - 0.1)],
           E["exclusive"] - 0.15, E["H"] - 0.15, "Status as of 2:47 a.m.", y0=1060)
    D.card(c, t, [("dx * dp  >=", "h-bar / 2", BLUE, E["hbar"] - 0.1),
                  ("h-bar / 2  =", "5.27 x 10^-35", GOLD, E["zeros"] - 0.1)],
           E["hbar"] - 0.15, E["I"] + 0.6, "Kennard 1927; NIST CODATA, J s", y0=1060)
    D.pill(c, "CLARITY: 0.0000...0527", W / 2, 1440, K.fade(t, E["clarity"] - 0.1, E["J"] - 0.1, 0.15), GOLD)
    D.pill(c, "PEER REVIEWED BY THE GROUP CHAT", W / 2, 1440, K.fade(t, E["worse"] + 0.2, speech_end + 1.4, 0.15), BLUE)
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
    K.run_blender("heis_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
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
                out_mp4, out_wav, "heis" if preview_times else None)

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
