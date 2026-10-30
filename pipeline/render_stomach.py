"""Episode: Your stomach is trying to digest you (ops/episodes/2026-10-30-stomach-digests-you.md). Body-macro short:
the stomach wall at macro scale (stomach_scene.py), then a magnified cross-section of the lining. Yelled Chatterbox
narration, @speedy_devv-style captions and labels (shared with render_led.py).

python render_stomach.py narrate               voice the script (cached in out/stomach/voice), print the timing
python render_stomach.py preview 1.0,9.5       stills into preview/stomach_*.png
python render_stomach.py out.mp4 out.wav       full render (Blender frames cached in out/stomach/frames)
"""
import json, os, subprocess, sys, time
import numpy as np
import skia
import common
from common import *
import kit3d as K
import sfx
from narrate_cb import narrate
from render_led import chunks, captions, leader, panel, shot_at, common_load, word_time

FPS = 30
OUT = os.path.join(ROOT, "out", "stomach")
FRAMES = os.path.join(OUT, "frames")
TAIL = 0.45

# (line, [(shot, word index the shot starts on), ...])
SCRIPT = [
    ("Right now, your stomach is trying to *digest* you.", [("wall_in", 0)]),
    ("It's full of *acid,* around pH{pee aitch} *two,* and an enzyme called *pepsin* that breaks down meat.", [("acid", 0), ("pepsin", 7)]),
    ("And your stomach wall is *meat.*", [("wall_low", 0)]),
    ("The only thing saving you is a layer of *mucus,* packed with *bicarbonate* that kills the acid before it touches you.", [("section", 0), ("neutral", 10)]),
    ("And the cells under it wear out so fast, your stomach replaces its lining every *three to five days.*", [("cells", 0)]),
    ("When that slime fails, from *bacteria* or too many *painkillers,* the acid eats right into you.", [("fail", 0)]),
    ("That's called an *ulcer.*", [("ulcer", 0)]),
    ("So yeah. Right now, your stomach is trying to *digest* you.", [("wall_out", 0)]),
]
LABELS = {   # shot: [(anchor, text, delay after the shot starts, (dx, dy))]
    "acid": [("acid", "STOMACH ACID", 0.3, (-230, -240))],
    "pepsin": [("pepsin", "PEPSIN", 0.3, (220, -220))],
    "wall_low": [("wall", "STOMACH WALL", 0.4, (200, -260))],
    "section": [("mucus", "MUCUS", 0.5, (-260, -200)), ("cells", "LINING CELLS", 1.2, (240, 230))],
    "neutral": [("bicarb", "BICARBONATE", 0.3, (230, -230))],
    "ulcer": [("ulcer", "ULCER", 0.4, (-240, 240))],
}
NOTES = {"wall_in": "Illustration", "acid": "Illustration", "pepsin": "Enzyme shown as a blob, not to scale",
         "wall_low": "Illustration", "section": "Magnified illustration, not to scale",
         "neutral": "Magnified illustration, not to scale", "cells": "Time-lapse illustration",
         "fail": "Magnified illustration, not to scale", "ulcer": "Magnified illustration, not to scale",
         "wall_out": "Illustration"}

def timeline():
    lines = narrate([l for l, _ in SCRIPT], OUT, exaggeration=1.6, cfg=0.25)
    shots = []
    for (line, plan), L in zip(SCRIPT, lines):
        for name, wi in plan:
            t = L["words"][wi]["start"] - 0.08 if wi else L["start"] - 0.08
            shots.append([0.0 if not shots else round(t, 3), name])
    duration = lines[-1]["end"] + TAIL
    return lines, shots, duration

def day_counter(c, t, t0, t1):
    a = min(1.0, (t - t0) / 0.2) * min(1.0, (t1 - t) / 0.15)
    if a <= 0:
        return
    u = max(0.0, min(1.0, (t - t0 - 0.2) / max(0.1, t1 - t0 - 0.6)))
    day = 1 + int(u * 4.999)
    panel(c, 300, 1200, W - 300, 1400, a)
    f, fs = font("Inter-700", 78), font("Inter-700", 24)
    s = f"DAY {day}"
    c.drawString(s, W / 2 - f.measureText(s) / 2, 1310, f, paint(skia.ColorWHITE, a))
    s = " ".join("NEW LINING")
    c.drawString(s, W / 2 - fs.measureText(s) / 2, 1365, fs, paint(skia.ColorSetARGB(255, 150, 150, 150), a))

def make_overlay(lines, shots, duration, A):
    ch = chunks(lines)
    def overlay(c, t, F):
        K.top_shade(c, 700, 120)
        name, s0, s1 = shot_at(shots, t, duration)
        for key, text, delay, (dx, dy) in LABELS.get(name, []):
            if t >= s0 + delay and A[key][F] is not None:
                a = min(1.0, (t - s0 - delay) / 0.2) * min(1.0, (s1 - t) / 0.1)
                x, y = A[key][F]
                leader(c, x, y, x + dx, y + dy, text, a)
        if name in NOTES:
            c.drawString(NOTES[name], 60, 1500, font("Inter-500", 26), paint(skia.ColorSetARGB(255, 200, 200, 200), 0.75))
        if name == "cells":
            day_counter(c, t, s0, s1)
        captions(c, t, ch)
    return overlay

# ------------------------------------------------------------------ sound

BUB = "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Bubbles Short.wav"
DROP = "344 Audio - Elemental Palette Designed Vol. 1/WATRMisc_Water, Liquid Impact, Bubble, Sci Fi, Hit 04_344 Audio_Elemental Palette Designed Vol 1.wav"
HISS = "Ivo Vicic - Campfire - Bonfire FX/42 Campfire, Putting Out Fire, Water from Bottle, Variation, Close.wav"
SQUELCH = "Epic Stock Media - Tower Defense Game/WOODImpt_Hit Blood Spill Splat Wood Impact Light Hit Squelch Small Thump 03_ESM_TDG.wav"
WOOSH = "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav"
SNAP = "Cinematic Sound Design - Interface & Infographics/Interface Accept Glassy Snap.wav"

def build_audio(lines, shots, duration, out_wav):
    track = np.zeros(int((duration + 1) * SR), np.float32)
    def add(t, x, gain):
        a = int(max(0.0, t) * SR)
        x = x[: len(track) - a]
        track[a:a + len(x)] += x * gain
    add(0.0, common_load(os.path.join(OUT, "narration.wav")), 1.0)
    start = dict((n, t) for t, n in shots)
    add(0.05, sfx.clip(DROP, 0.0, 0.8, lp=7000), 0.30)                        # the first drop lands on frame 1
    for name in ("wall_in", "acid", "pepsin", "wall_out"):
        add(start[name] + 0.3, sfx.clip(BUB, 0.0, 1.2, lp=6000), 0.10)
    for t, name in shots[1:]:
        add(t - 0.12, sfx.clip(WOOSH, 0.0, 0.6, lp=6000), 0.09)
    for name, items in LABELS.items():
        for key, text, delay, _ in items:
            add(start[name] + delay, sfx.clip(SNAP, 0.0, 0.4), 0.11)
    add(start["wall_low"] + 0.1, sfx.clip(SQUELCH, 0.0, 0.6, lp=5000), 0.22)
    add(start["neutral"] + 0.4, sfx.clip(HISS, 0.5, 1.6, lp=5000), 0.10)
    add(start["ulcer"] + 0.05, sfx.clip(HISS, 0.5, 1.8, lp=6000), 0.16)
    save_wav(track, out_wav, duration)

# ------------------------------------------------------------------ main

def main(out_mp4=None, out_wav=None, preview_times=None):
    common.FPS = FPS
    lines, shots, duration = timeline()
    if out_mp4 is None and preview_times is None:
        for t, n in shots:
            print(f"{t:6.2f} {n}")
        print(f"duration {duration:.2f} s")
        return
    os.makedirs(FRAMES, exist_ok=True)
    n = int(round(duration * FPS))
    frames = sorted({min(n - 1, int(round(x * FPS))) for x in preview_times}) if preview_times else list(range(n))
    tj = os.path.join(OUT, "timing.json")
    json.dump({"fps": FPS, "duration": duration, "shots": shots}, open(tj, "w"))
    t0 = time.time()
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "stomach_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    if not preview_times:
        build_audio(lines, shots, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots, duration, A), out_mp4, out_wav, "stomach" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
