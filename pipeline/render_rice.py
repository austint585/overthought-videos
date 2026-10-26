"""'Would you take this deal?' Rice on a chessboard, doubled every square, in 3D: Kokoro voice, Blender frames, Skia overlay.

python render_rice.py out.mp4 out.wav    full render (Blender frames are cached in out/rice/frames; delete them to re-render)
python render_rice.py preview 1.0,12.5   render and composite stills into preview/
"""
import json, math, os, sys
import numpy as np
import skia
from common import *
import render_tap as tap
import kit3d as K
import rice_anim as RA

FPS = 60
TAIL = 0.6          # the last frame cuts back to the opening shot, so the Reel loops
SCRIPT = [
    ("A", "Would you take this deal? One grain of rice on the first square, then *double* it on every square after."),
    ("B", "Square ten: about a *tablespoon.*"),
    ("C", "Square twenty: a *13{thirteen} kilo* sack."),
    ("D", "Square thirty: a full *dump truck.*"),
    ("E", "Square forty: *heavier* than the Eiffel Tower."),
    ("F", "Square fifty: more than a *week* of all the rice the world grows."),
    ("G", "And square sixty-four? The board holds *18{eighteen} quintillion* grains."),
    ("H", "A pile more than *four kilometers* tall. Over *700{seven hundred} years* of every rice farm on Earth."),
    ("I", "So, would you take the deal?"),
]
EXTRA_GAP = {6: 0.25, 7: 0.2, 8: 0.6}
OUT = os.path.join(ROOT, "out", "rice")
FRAMES = os.path.join(OUT, "frames")

def events(sents, speech_end):
    w = lambda si, sub: tap.word_time(sents, si, sub)
    return {"double": w(0, "double"), "s10": w(1, "ten"), "s20": w(2, "twenty"), "s30": w(3, "thirty"),
            "s40": w(4, "forty"), "s50": w(5, "fifty"), "s64": w(6, "sixty"), "four": w(7, "four"),
            "loop": sents[8]["t0"] - 0.15, "speech_end": speech_end}

# ------------------------------------------------------------------ sound

def build_audio(sents, E, duration, path):
    tr = K.voice_track(sents, duration) + K.pad_bed(duration, 0.0, root=110.0, bpm=100)
    # grains landing on the first squares, then a tok for every new square, lower as the pile grows
    for k in range(2, 65):
        tk = RA.n_keys(E)
        t_k = next((t0 + (k - a) / (b - a) * (t1 - t0) for (t0, a), (t1, b) in zip(tk, tk[1:]) if a <= k <= b and b > a), None)
        if t_k is None or t_k >= E["loop"]:
            continue
        if k <= RA.DISCRETE:
            for j in range(min(RA.grains_on(k), 8)):
                add(tr, t_k + 0.12 + j * 0.018, K.tick(k * 13 + j, 0.5), 0.3 * (0.85 ** j))
        else:
            f = 900 * (0.965 ** (k - 10))
            add(tr, t_k, tone(f, 0.09, tau=0.03, harmonics=(1, 0.4, 0.2)), 0.22)
    # pour: a hiss that turns into a rumble as the pile grows
    ts = np.arange(0, duration, 0.01)
    vols = np.array([RA.heap_volume(RA.square_at(t, E)) for t in ts])
    a = np.clip((np.log10(np.maximum(vols, 1e-9)) + 5) / 16.5, 0, 1)
    a[vols <= 0] = 0
    env = np.interp(np.arange(int(duration * SR)) / SR, ts, a)
    hiss = noise_burst(duration, tau=1e9, lp=0.35, seed=31)[:len(env)]
    rumble = noise_burst(duration, tau=1e9, lp=0.02, seed=32)[:len(env)]
    add(tr, 0.0, hiss * env * (1 - env) * 0.35 + rumble * env ** 2 * 0.8)     # rumble sits 6 dB under the voice
    add(tr, E["s64"], K.layer(K.clunk(5), sweep(80, 28, 1.6, tau=0.6) * 1.2), 0.5)
    add(tr, E["loop"] - 0.05, K.whoosh(41, 0.4), 0.35)
    save_wav(tr, path, duration)

# ------------------------------------------------------------------ overlay

def draw_hook(c, a):
    if a <= 0:
        return
    f = font("Bricolage-800", 84)
    parts = [("Would you take", False), ("this deal?", True)]
    y = 300
    for s, k in parts:
        wd = f.measureText(s) + (36 if k else 0)
        x = W / 2 - wd / 2
        if k:
            c.drawRRect(tap.rrect(x, y - 70, x + wd, y + 22, 14), paint(ORANGE, a))
            c.drawString(s, x + 18, y, f, paint(tap.PANEL2, a))
        else:
            c.drawString(s, x, y, f, paint(INK, a))
        y += 100
    text_center(c, "1 grain of rice, doubled on every square", W / 2, y + 10, font("Bricolage-700", 48), paint(INK, a))

def draw_hud(c, n, a):
    k = max(1, min(64, int(math.floor(n + 1e-6))))
    grains = RA.grains_on(k)
    total = 2 ** k - 1
    x, y = 60, 1240
    gtxt = f"{grains:,}"
    gf = font("JetBrainsMono-700", 30 if len(gtxt) < 20 else 26)
    w = max(300, gf.measureText(gtxt) + 40)
    c.drawRRect(tap.rrect(x - 22, y - 44, x + w, y + 250, 20), paint(skia.ColorSetARGB(140, 10, 11, 14), a))
    lab = font("JetBrainsMono-700", 22)
    c.drawString("SQUARE", x, y, lab, paint(MUTED, a))
    big = font("JetBrainsMono-800", 72)
    c.drawString(f"{k}", x, y + 72, big, paint(INK, a))
    c.drawString("/ 64", x + big.measureText(f"{k}") + 14, y + 72, font("JetBrainsMono-700", 32), paint(MUTED, a))
    c.drawString("GRAINS ON THIS SQUARE", x, y + 118, lab, paint(MUTED, a))
    c.drawString(gtxt, x, y + 156, gf, paint(INK, a))
    c.drawString("WHOLE BOARD SO FAR", x, y + 198, lab, paint(MUTED, a))
    c.drawString(RA.fmt_mass(total * RA.GRAIN_KG), x, y + 238, font("JetBrainsMono-800", 36), paint(ORANGE, a))

def overlay(c, t, F, sents, cm, E, speech_end):
    K.top_shade(c)
    n = RA.square_at(t, E)
    c.saveLayer(None, K.shadow_paint())
    hook = 1.0 if t >= E["loop"] else K.fade(t, -1, sents[1]["t0"] - 0.05, 0.2)
    draw_hook(c, hook)
    if t < E["loop"]:
        tap.draw_captions(c, t, sents, cm)
    c.restore()
    draw_hud(c, n, 1.0)
    text_center(c, "Assumes 25 mg per grain", W / 2, 1530, font("JetBrainsMono-500", 26), paint(MUTED, 0.9))

# ------------------------------------------------------------------ main

def main(out_mp4, out_wav, preview_times=None):
    sents, speech_end = K.narrate(SCRIPT, OUT, EXTRA_GAP)
    duration = speech_end + TAIL
    E = events(sents, speech_end)
    n_frames = int(round(duration * FPS))
    print(f"duration {duration:.1f}s, {n_frames} frames", flush=True)
    frames = sorted({min(n_frames - 1, int(round(x * FPS))) for x in preview_times}) if preview_times else range(n_frames)
    K.run_blender("rice_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    cm = [x for x in tap.build_chunk_map(sents) if 0 < x[0] < 8]
    if not preview_times:
        build_audio(sents, E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, F: overlay(c, t, F, sents, cm, E, speech_end),
                out_mp4, out_wav, "rice" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        main(None, None, preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
