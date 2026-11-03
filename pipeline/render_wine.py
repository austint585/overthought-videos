"""Episode: Restaurant units (ops/episodes/2026-11-03-restaurant-units.md). The friend who "only had two glasses", run through the
2008 study that bought 480 bar and restaurant drinks and measured them, in the toon kit (toon.py, wine_scene.py). Calm
Chatterbox read, yellow outlined captions.

python render_wine.py narrate                voice the script (cached in out/wine/voice), print the timing
python render_wine.py preview 1.0,9.5        stills into preview/wine_*.png
python render_wine.py out.mp4 out.wav        full render (Blender frames cached in out/wine/frames)
"""
import json, os, subprocess, sys, time
import numpy as np
import skia
import common
from common import *
import kit3d as K
import sfx
from narrate_cb import narrate
from render_led import common_load
from render_height import make_overlay as _height_overlay
import render_height as RH

FPS = 30
OUT = os.path.join(ROOT, "out", "wine")
FRAMES = os.path.join(OUT, "frames")
TAIL = 1.2

# (line, [(shot, word index the shot starts on), ...]); *word* is colored in the caption
SCRIPT = [
    ("Your friend who says she only had *two glasses* is not lying. She's counting in *restaurant units.*",
     [("bar", 0), ("bar~2", 12)]),
    ("In two thousand eight, researchers bought *four hundred eighty* drinks at bars and restaurants in Northern California, "
     "and measured them.", [("lab", 0)]),
    ("The average glass of wine had *forty three percent* more alcohol than a standard drink.", [("pour", 0), ("pour~2", 6)]),
    ("*Ninety eight percent* of the glasses were over one drink.", [("row", 0)]),
    ("The average martini? *One point six.*", [("martini", 0)]),
    ("So her two glasses were really about *three* drinks.", [("math", 0)]),
    ("She had two glasses. The glasses had *three.*", [("final", 0)]),
]
HOOK = ["She only had", "two glasses"]

def timeline():
    lines = narrate([l for l, _ in SCRIPT], OUT, exaggeration=0.5, cfg=0.4, gap=0.22)
    shots = []
    for (line, plan), L in zip(SCRIPT, lines):
        for name, wi in plan:
            t = L["words"][wi]["start"] - 0.08 if wi else L["start"] - 0.08
            shots.append([0.0 if not shots else round(t, 3), name])
    return lines, shots, lines[-1]["end"] + TAIL

SOURCES = "Data: Kerr et al. 2008, Alcohol: Clinical & Experimental Research"

def make_overlay(lines, shots, duration):
    RH.HOOK = HOOK
    base = _height_overlay(lines, shots, duration)
    t_final = next(t for t, n in shots if n == "final")
    def overlay(c, t, F):
        base(c, t, F)
        if t >= t_final:                                    # honesty note, small, top of frame
            f = font("Fredoka-700", 30)
            wd = f.measureText(SOURCES)
            x = (W - wd) / 2
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 18, 150, x + wd + 18, 198), 14, 14),
                        skia.Paint(Color=skia.ColorSetARGB(200, 12, 14, 26), AntiAlias=True))
            c.drawString(SOURCES, x, 185, f, skia.Paint(Color=skia.ColorWHITE, AntiAlias=True))
    return overlay

# ------------------------------------------------------------------ sound

SNAP = "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav"
POP = "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav"
GLASSY = "Cinematic Sound Design - Interface & Infographics/Interface Accept Glassy Snap.wav"
PAGE = "Cinematic Sound Design - Paper Foley/Encyclopedia Glossy Page Turn Muted.wav"
BUBBLE = "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Bubbles Short.wav"
KALIMBA = "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Kalimba 3 Up_CB Sounddesign_APPlicable Sounds.wav"

def build_audio(lines, shots, duration, out_wav):
    track = np.zeros(int((duration + 1) * SR), np.float32)
    def add(t, x, gain):
        a = int(max(0.0, t) * SR)
        x = x[: len(track) - a]
        track[a:a + len(x)] += x * gain
    add(0.0, common_load(os.path.join(OUT, "narration.wav")), 1.0)
    start = {}
    for t, n in shots:
        start.setdefault(n, t)
    add(0.2, sfx.clip(GLASSY, 0.0, 0.4), 0.14)                         # two glasses clink on the counter
    add(0.45, sfx.clip(GLASSY, 0.0, 0.4), 0.12)
    for n in ("bar~2", "lab", "pour~2", "row", "martini", "math", "final"):   # the signs land
        add(start[n] + 0.45, sfx.clip(SNAP, 0.0, 0.2, lp=1500), 0.26)
    add(start["pour"] + 0.3, sfx.clip(BUBBLE, 0.0, 1.0), 0.14)          # the pour
    for k in range(10):                                                 # the row fills, one glass at a time
        add(start["row"] + 0.15 * k, sfx.clip(POP, 0.0, 0.12, lp=2400), 0.1)
    add(start["math"] + 0.3, sfx.clip(PAGE, 0.0, 0.4), 0.12)
    add(start["final"] + 0.3, sfx.clip(KALIMBA, 0.0, 1.2), 0.1)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "wine_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots, duration), out_mp4, out_wav, "wine" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
