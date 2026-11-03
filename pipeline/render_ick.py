"""Episode: The ick is supercooling (ops/episodes/2026-11-03-ick-supercooled.md). Deadpan physics of getting the ick in the toon
kit (toon.py, ick_scene.py): a water bottle crush that freezes all at once, calm Chatterbox read, yellow outlined captions.

python render_ick.py narrate                voice the script (cached in out/ick/voice), print the timing
python render_ick.py preview 1.0,9.5        stills into preview/ick_*.png
python render_ick.py out.mp4 out.wav        full render (Blender frames cached in out/ick/frames)
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
OUT = os.path.join(ROOT, "out", "ick")
FRAMES = os.path.join(OUT, "frames")
TAIL = 1.2

# (line, [(shot, word index the shot starts on), ...]); *word* is colored in the caption
SCRIPT = [
    ("Your friend did not lose feelings for him overnight. Her crush was *supercooled.*",
     [("date", 0), ("date~2", 8)]),
    ("Pure water can stay liquid way below freezing, down to about *minus forty,* as long as nothing disturbs it.",
     [("freezer", 0), ("freezer~2", 13)]),
    ("Then one tiny bump, one speck of dust, and it starts turning to ice *all at once.*",
     [("tap", 0), ("tap~2", 9)]),
    ("Physicists call that bump a *nucleation site.*", [("site", 0)]),
    ("Your friend calls it: he clapped when the plane *landed.*", [("plane", 0), ("plane~2", 5)]),
    ("In a twenty twenty five study, *seventy five percent* of single women had gotten the ick, and fifty seven percent of men.",
     [("chart", 0), ("chart~2", 13)]),
    ("Twenty six percent ended it *on the spot.*", [("door", 0)]),
    ("So she's not picky. That's just *physics.*", [("final", 0)]),
]
HOOK = ["Your friend got the ick", "in one second"]

def timeline():
    lines = narrate([l for l, _ in SCRIPT], OUT, exaggeration=0.5, cfg=0.4, gap=0.22)
    shots = []
    for (line, plan), L in zip(SCRIPT, lines):
        for name, wi in plan:
            t = L["words"][wi]["start"] - 0.08 if wi else L["start"] - 0.08
            shots.append([0.0 if not shots else round(t, 3), name])
    return lines, shots, lines[-1]["end"] + TAIL

SOURCES = "Data: Collisson, Saunders & Yin 2025; AMS Glossary of Meteorology"

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
SHARDS = "Epic Stock Media - Elemental Mutation Whooshes and Impacts/GLASMvmt_Whoosh Glass Crystal Fragments Sharp Shards Dry 05_ESM_EMWI.wav"
CRACK = "Alexander Kopeikin - 100 kHz Designed Ice/ice, surface cracking, fissure, fast, hard-003.wav"
SNAPICE = "Alexander Kopeikin - 100 kHz Designed Ice/ice, crack, ice block snapping-001.wav"
CRUSH = "Alexander Kopeikin - 100 kHz Designed Ice/ice, block of ice crushed, heavy-015.wav"
DOOR = "344 Audio - Haunting Ambiences Vol. 3/METLImpt_Metal Bangs, Metal Hits, Banging On Doors_344 Audio_Haunting Ambiences Vol 3.wav"
KALIMBA = "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Kalimba 3 Up_CB Sounddesign_APPlicable Sounds.wav"
PAGE = "Cinematic Sound Design - Paper Foley/Encyclopedia Glossy Page Turn Muted.wav"

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
    add(0.05, sfx.clip(KALIMBA, 0.0, 1.2), 0.1)                       # hearts over the table
    add(start["date~2"] + 0.2, sfx.clip(GLASSY, 0.0, 0.5), 0.18)
    add(start["freezer"] + 0.1, sfx.clip(DOOR, 0.0, 0.25, lp=1200), 0.14)   # the freezer door
    for k in range(10):                                                 # the display ticks down
        add(start["freezer"] + 0.4 + k * 0.25, sfx.clip(POP, 0.0, 0.12, lp=2400), 0.1)
    add(start["tap"] + 0.55, sfx.clip(SNAP, 0.0, 0.2, lp=2000), 0.32)  # the speck lands
    add(start["tap~2"], sfx.clip(CRACK, 0.0, 1.4), 0.22)                # the freeze runs up the bottle
    add(start["tap~2"] + 0.1, sfx.clip(SHARDS, 0.0, 0.8), 0.14)
    add(start["site"] + 0.25, sfx.clip(SNAP, 0.0, 0.2, lp=1500), 0.3)  # the sign lands
    for k in range(6):                                                  # claps
        add(start["plane~2"] + 0.1 + k * 0.17, sfx.clip(SNAP, 0.0, 0.12, hp=900), 0.22)
    add(start["plane~2"] + 0.25, sfx.clip(SNAPICE, 0.0, 0.8), 0.2)     # the bottle freezes solid
    for k in range(2):                                                  # one tick per bar
        add(start["chart"] + 0.3 + k * 0.4, sfx.clip(POP, 0.0, 0.2), 0.16)
    add(start["chart~2"] + 0.2, sfx.clip(PAGE, 0.0, 0.5), 0.15)
    add(start["door"] + 0.35, sfx.clip(CRUSH, 0.0, 0.6, lp=2500), 0.16)  # the ice bottle slides out
    add(start["door"] + 0.9, sfx.clip(DOOR, 0.0, 0.35, lp=900), 0.2)      # the door slams
    add(start["final"] + 0.35, sfx.clip(SNAP, 0.0, 0.2, lp=900), 0.3)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "ick_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots, duration), out_mp4, out_wav, "ick" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
