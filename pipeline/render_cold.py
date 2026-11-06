"""Episode: Always Cold (ops/episodes/2026-11-06-always-cold.md). A tag-a-friend joke on a real study: Chang and Kajackaite
(PLOS ONE, 2019) tested 543 students in Berlin in rooms from 61 to 91 F; each degree Celsius warmer raised women's math
scores 1.76%, and the men's change was small and not significant. Toon kit (toon.py, cold_scene.py), the friend and a
thermostat as the cast. Calm read, yellow outlined captions. Built from render_hibern.py.

python render_cold.py narrate                voice the script (cached in out/cold/voice), print the timing
python render_cold.py preview 1.0,9.5        stills into preview/cold_*.png
python render_cold.py out.mp4 out.wav        full render (Blender frames cached in out/cold/frames)
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
OUT = os.path.join(ROOT, "out", "cold")
FRAMES = os.path.join(OUT, "frames")
TAIL = 1.2

# (line, [(shot, word index the shot starts on), ...]); *word* is colored in the caption
SCRIPT = [
    ("Your friend who's cold in every single room now has *science.*", [("cold", 0)]),
    ("In 2019{twenty nineteen}, researchers in Berlin put 543{five hundred forty-three} students in rooms from 61{sixty-one} to 91{ninety-one} *degrees.*",
     [("lab", 0), ("range", 11)]),
    ("Then they gave them *math tests.*", [("math", 0)]),
    ("For the women, every degree Celsius warmer meant almost 2{two} percent more *right answers.*", [("women", 0)]),
    ("For the men, it barely moved. A small drop, too small to *count.*", [("men", 0)]),
    ("So when she steals your hoodie, she's protecting her *math grade.*", [("hoodie", 0)]),
    ("Turn the heat up. It's for *science.*", [("heat", 0)]),
    ("Tag the friend who's always cold, and give them your *hoodie.*", [("final", 0)]),
]
HOOK = ["THE ALWAYS COLD FRIEND", "HAS SCIENCE NOW"]

def timeline():
    if os.environ.get("OT_VOICE") == "kokoro":            # Chatterbox needs ~4 GB free commit; Kokoro is the low-memory fallback
        from narrate_kk import narrate as kk
        lines = kk([l for l, _ in SCRIPT], OUT, gap=0.22)
    else:
        lines = narrate([l for l, _ in SCRIPT], OUT, exaggeration=0.5, cfg=0.4, gap=0.22)
    shots = []
    for (line, plan), L in zip(SCRIPT, lines):
        for name, wi in plan:
            wi = min(wi, len(L["words"]) - 1)
            t = L["words"][wi]["start"] - 0.08 if wi else L["start"] - 0.08
            shots.append([0.0 if not shots else round(t, 3), name])
    return lines, shots, lines[-1]["end"] + TAIL

SOURCES = "Chang & Kajackaite, PLOS ONE, 2019"

def make_overlay(lines, shots, duration):
    RH.HOOK = HOOK
    base = _height_overlay(lines, shots, duration)
    t_lab = next(t for t, n in shots if n == "lab")
    t_clock = next(t for t, n in shots if n == "hoodie")
    def overlay(c, t, F):
        base(c, t, F)
        if t_lab <= t < t_clock:                            # honesty note while the facts are on screen
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

TICK = "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav"

WHOOSH = "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Bubbles Short.wav"

SCRATCH = "InMotionAudio - Scratch Card/OBJMisc_ScratchCard_SurfaceWipe_04_InMotionAudio_ScratchCard.wav"

CLOTH = "InMotionAudio - Foley T-Shirt/FOLYClth_ClothMovement24_InMotionAudio_FoleyT-Shirt.wav"
HEARTB = "Cinematic Sound Design - Cartoon Impacts/Cartoon Pops Random Sequence Reverb.wav"
KNOCK = "Epic Stock Media - Board Game - Sound Set Kit for Tabletop and Digital Games/UIClick_UI Button Analog Vintage Double Click Neutral Dry Press 11_ESM_BG.wav"

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
    for k in range(5):                                                   # teeth chattering on frame one
        add(0.05 + 0.09 * k, sfx.clip(KNOCK, 0.0, 0.08), 0.08)
    for n in ("cold", "lab", "range", "math", "women", "men", "hoodie", "heat"):   # the signs land
        d = {"cold": 0.6, "lab": 0.4, "range": 0.3, "math": 0.2, "women": 0.5, "men": 0.3, "hoodie": 0.7, "heat": 0.5}[n]
        add(start[n] + d + 0.4, sfx.clip(SNAP, 0.0, 0.2, lp=1500), 0.22)
    for k in range(8):                                                   # the women's pencil grows a step at a time
        add(start["women"] + 0.4 + 0.25 * k, sfx.clip(POP, 0.0, 0.25), 0.08)
    add(start["men"] + 0.1, sfx.clip(BUBBLE, 0.0, 0.15, lp=2500), 0.06)
    add(start["hoodie"], sfx.clip(CLOTH, 0.0, 0.8), 0.25)
    for k in range(4):                                                   # the thermostat dial clicks up
        add(start["heat"] + 0.3 + 0.2 * k, sfx.clip(TICK, 0.0, 0.1), 0.1)
    add(start["final"] + 0.4, sfx.clip(KALIMBA, 0.0, 1.2), 0.06)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "cold_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots, duration), out_mp4, out_wav, "cold" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "times":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
