"""Episode: Cuffing season forecast (ops/episodes/2026-11-03-cuffing-forecast.md). Deadpan TV weather forecast for cuffing
season in the toon kit (toon.py, cuff_scene.py), a thermometer weatherman, calm Chatterbox read, yellow outlined captions.

python render_cuff.py narrate                voice the script (cached in out/cuff/voice), print the timing
python render_cuff.py preview 1.0,9.5        stills into preview/cuff_*.png
python render_cuff.py out.mp4 out.wav        full render (Blender frames cached in out/cuff/frames)
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
OUT = os.path.join(ROOT, "out", "cuff")
FRAMES = os.path.join(OUT, "frames")
TAIL = 1.2

# (line, [(shot, word index the shot starts on), ...]); *word* is colored in the caption
SCRIPT = [
    ("Your friend who was single all summer just got a girlfriend. That's not love. That's *weather.*",
     [("studio", 0), ("pair", 7), ("studio~2", 11)]),
    ("A cold front is moving in, and with it, *cuffing season.*", [("front", 0), ("cuff", 9)]),
    ("Researchers had the same men rate the same body photos all year. In winter, they rated them *hotter.*",
     [("lab", 0), ("winter", 12)]),
    ("The photos did not *change.*", [("photo", 0)]),
    ("On Facebook, breakups climb all November and peak *two weeks before Christmas.*", [("chart", 0), ("chart~2", 6)]),
    ("Christmas Day has the *fewest.*", [("tree", 0)]),
    ("The first Sunday in January is the *busiest day* of the year on dating apps.", [("phone", 0), ("phone~2", 7)]),
    ("Nine months after the holidays, nine of the ten most common American birthdays are in *September.*",
     [("cakes", 0), ("cakes~2", 5)]),
    ("It all clears up around *Valentine's Day.* Then your friend is single again, right on time for *summer.*",
     [("thaw", 0), ("final", 7)]),
]
HOOK = ["Your single friend", "just got a girlfriend"]

def timeline():
    lines = narrate([l for l, _ in SCRIPT], OUT, exaggeration=0.5, cfg=0.4, gap=0.22)
    shots = []
    for (line, plan), L in zip(SCRIPT, lines):
        for name, wi in plan:
            t = L["words"][wi]["start"] - 0.08 if wi else L["start"] - 0.08
            shots.append([0.0 if not shots else round(t, 3), name])
    return lines, shots, lines[-1]["end"] + TAIL

SOURCES = "Data: Pawlowski 2008, McCandless 2010, Hinge, SSA 1994-2014"

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
WIND = "344 Audio - Elemental Palette Designed Vol. 1/WINDDsgn_Wind, Rush, Whoosh, Long x5 01_344 Audio_Elemental Palette Designed Vol 1.wav"
SHARDS = "Epic Stock Media - Elemental Mutation Whooshes and Impacts/GLASMvmt_Whoosh Glass Crystal Fragments Sharp Shards Dry 05_ESM_EMWI.wav"
BELLS = "344 Audio - Christmas Vol. 1/MAGMisc_Magic Christmas Bells 2_344 Audio_Christmas.wav"
PAGE = "Cinematic Sound Design - Paper Foley/Encyclopedia Glossy Page Turn Muted.wav"
CLOTH = "InMotionAudio - Foley T-Shirt/FOLYClth_ClothMovement24_InMotionAudio_FoleyT-Shirt.wav"
KALIMBA = "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Kalimba 3 Up_CB Sounddesign_APPlicable Sounds.wav"

def build_audio(lines, shots, duration, out_wav):
    track = np.zeros(int((duration + 1) * SR), np.float32)
    def add(t, x, gain):
        a = int(max(0.0, t) * SR)
        x = x[: len(track) - a]
        track[a:a + len(x)] += x * gain
    add(0.0, common_load(os.path.join(OUT, "narration.wav")), 1.0)
    start, end = {}, {}
    for i, (t, n) in enumerate(shots):
        start.setdefault(n, t)
        end[n] = shots[i + 1][0] if i + 1 < len(shots) else duration
    add(0.05, sfx.clip(SNAP, 0.0, 0.2, lp=1800), 0.3)                  # the first pin lands on the map
    add(start["pair"] + 0.25, sfx.clip(POP, 0.0, 0.3), 0.3)             # the second pin snaps next to it
    add(start["front"], sfx.clip(WIND, 0.0, 2.2, lp=3000), 0.14)
    add(start["cuff"] + 0.35, sfx.clip(SNAP, 0.0, 0.2, lp=1500), 0.32)  # the sign lands
    add(start["lab"] + 0.2, sfx.clip(PAGE, 0.0, 0.6), 0.2)
    add(start["winter"], sfx.clip(WIND, 0.5, 1.5, lp=2200), 0.1)
    add(start["winter"] + 0.6, sfx.clip(GLASSY, 0.0, 0.5), 0.2)        # needle hits HOTTER
    add(start["photo"] + 0.1, sfx.clip(CLOTH, 0.0, 0.3, hp=1500), 0.2)
    for k in range(8):                                                  # one tick per bar
        add(start["chart"] + 0.15 + k * 0.22, sfx.clip(POP, 0.0, 0.15, lp=2600), 0.14)
    add(start["chart~2"] + 0.3, sfx.clip(SHARDS, 0.0, 0.8), 0.2)        # the heart splits
    add(start["tree"] + 0.1, sfx.clip(BELLS, 0.0, 1.6), 0.12)
    t = start["phone"]
    while t < end["phone~2"] - 0.1:
        add(t, sfx.clip(PAGE, 0.0, 0.25, hp=1200), 0.1)
        t += 0.3
    for k in range(10):                                                 # one pop per cake candle
        add(start["cakes~2"] + 0.1 + k * 0.12, sfx.clip(POP, 0.0, 0.15), 0.12)
    add(start["thaw"] + 0.1, sfx.clip(KALIMBA, 0.0, 1.5), 0.12)
    add(start["final"] + 0.4, sfx.clip(SNAP, 0.0, 0.2, lp=900), 0.32)   # the pin pops off
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "cuff_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots, duration), out_mp4, out_wav, "cuff" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
