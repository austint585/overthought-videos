"""Episode: No Shave November, Day 6 (ops/episodes/2026-11-06-no-shave-day-six.md). The friend on day 6 of his "beard", in
the toon kit (toon.py, shave_scene.py) with a potato as the cast. Calm read, yellow outlined captions. Built from
render_shave.py. OT_VOICE=kokoro uses the low-memory Kokoro voice.

python render_shave.py narrate                voice the script (cached in out/merc/voice), print the timing
python render_shave.py preview 1.0,9.5        stills into preview/merc_*.png
python render_shave.py out.mp4 out.wav        full render (Blender frames cached in out/merc/frames)
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
OUT = os.path.join(ROOT, "out", "shave")
FRAMES = os.path.join(OUT, "frames")
TAIL = 1.2

# (line, [(shot, word index the shot starts on), ...]); *word* is colored in the caption
SCRIPT = [
    ("Your friend is doing *No Shave November.*", [("mirror", 0)]),
    ("It's day 6{six}. He calls it a *beard.*", [("mirror~2", 0), ("stroke", 3)]),
    ("Beard hair grows about a third of a *millimeter* a day.", [("macro", 0)]),
    ("So he has about *2{two} millimeters.*", [("ruler", 0)]),
    ("He has posted 4{four} *progress pics.*", [("pics", 0)]),
    ("At that speed, by November 30th{thirtieth}, it's about *a centimeter.*", [("cal", 0), ("ruler~2", 5)]),
    ("No Shave November started in 2009{two_thousand_nine} to raise money for *cancer research.*", [("jar", 0), ("jar~2", 5)]),
    ("Tag your friend and ask how much he *donated.*", [("sweat", 0)]),
]
HOOK = ["Day 6 of", "NO SHAVE NOVEMBER"]

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

SOURCES = "Growth: about 0.27 to 0.5 mm a day (Int J Cosmet Sci 2016)"

def make_overlay(lines, shots, duration):
    RH.HOOK = HOOK
    base = _height_overlay(lines, shots, duration)
    t_lab = next(t for t, n in shots if n == "macro")
    t_clock = next(t for t, n in shots if n == "pics")
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
    rasp = sfx.clip(SCRATCH, 0.0, 0.5, hp=2500)                          # the stubble rasps when he strokes it
    for t0 in (0.15, start["stroke"] + 0.1):
        for k in range(3):
            add(t0 + k * 0.33, rasp, 0.12)
    for n in ("macro", "ruler", "pics", "cal", "jar"):                   # the signs land
        add(start[n] + 0.45, sfx.clip(SNAP, 0.0, 0.2, lp=1500), 0.24)
    add(start["macro"] + 0.2, sfx.clip(KALIMBA, 0.0, 1.2), 0.07)
    for k in range(4):                                                   # four progress pics
        add(start["pics"] + 0.35 + 0.3 * k, sfx.clip(GLASSY, 0.0, 0.3), 0.1)
    add(start["cal"] + 0.3, sfx.clip(PAGE, 0.0, 0.4), 0.12)
    add(start["ruler~2"] + 0.2, sfx.clip(POP, 0.0, 0.25), 0.14)
    add(start["sweat"] + 0.9, sfx.clip(BUBBLE, 0.0, 0.6), 0.1)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "shave_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots, duration), out_mp4, out_wav, "shave" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
