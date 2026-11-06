"""Episode: Caffeine Doesn't Affect Me (ops/episodes/2026-11-06-caffeine-immune.md). A tag-a-friend joke on a real study:
Drake et al. (J. Clin. Sleep Med., 2013) gave 400 mg of caffeine 0, 3 or 6 hours before bed; at 6 hours it still cut
measured sleep by more than an hour, and the sleepers' own reports suggested they didn't notice. Toon kit (toon.py,
caff_scene.py), the friend and a grumpy giant mug as the cast. Calm read, yellow outlined captions. Built from render_cold.py.

python render_caff.py narrate                voice the script (cached in out/caff/voice), print the timing
python render_caff.py preview 1.0,9.5        stills into preview/caff_*.png
python render_caff.py out.mp4 out.wav        full render (Blender frames cached in out/caff/frames)
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
OUT = os.path.join(ROOT, "out", "caff")
FRAMES = os.path.join(OUT, "frames")
TAIL = 1.2

# (line, [(shot, word index the shot starts on), ...]); *word* is colored in the caption
SCRIPT = [
    ("Your friend who drinks coffee at 9{nine} at night says caffeine doesn't *affect them.*", [("chug", 0)]),
    ("In 2013{twenty thirteen}, sleep scientists *tested that.*", [("lab", 0)]),
    ("People took 400{four hundred} milligrams of caffeine, about *four cups* of coffee, six hours before bed.",
     [("mugs", 0), ("clock", 10)]),
    ("A monitor tracked their sleep *at home.*", [("bed", 0)]),
    ("They lost more than *an hour* of sleep.", [("bar", 0)]),
    ("Then they wrote in their sleep diaries that they *slept fine.*", [("diary", 0)]),
    ("So your friend is right. They *can't feel it.*", [("right", 0)]),
    ("Tag the friend who says caffeine doesn't *affect them.*", [("final", 0)]),
]
HOOK = ["CAFFEINE DOESN'T AFFECT ME", "(THEY CAN'T TELL)"]

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

SOURCES = "Drake et al., J. Clin. Sleep Med., 2013 (12 adults)"

def make_overlay(lines, shots, duration):
    RH.HOOK = HOOK
    base = _height_overlay(lines, shots, duration)
    t_lab = next(t for t, n in shots if n == "lab")
    t_clock = next(t for t, n in shots if n == "right")
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
    for k in range(3):                                                   # gulps on frame one
        add(0.05 + 0.28 * k, sfx.clip(BUBBLE, 0.0, 0.15, lp=1800), 0.1)
    for n, d in (("chug", 0.8), ("lab", 0.4), ("clock", 0.3), ("bed", 0.4), ("bar", 0.6), ("diary", 0.6), ("right", 0.5)):
        add(start[n] + d + 0.4, sfx.clip(SNAP, 0.0, 0.2, lp=1500), 0.22)
    for k in range(4):                                                   # four mugs land
        add(start["mugs"] + 0.3 + 0.22 * k, sfx.clip(KNOCK, 0.0, 0.12), 0.12)
    for k in range(6):                                                   # the clock hands spin six hours
        add(start["clock"] + 0.2 + 0.12 * k, sfx.clip(TICK, 0.0, 0.1), 0.08)
    add(start["bar"] + 0.5, sfx.clip(POP, 0.0, 0.25), 0.12)
    add(start["diary"] + 0.2, sfx.clip(PAGE, 0.0, 0.6), 0.2)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "caff_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots, duration), out_mp4, out_wav, "caff" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "times":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
