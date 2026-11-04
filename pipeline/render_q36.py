"""Episode: 36 Questions (ops/episodes/2026-11-04-36-questions.md). The friend who brings Aron's 1997 closeness questions to a
first date, laminated, in the toon kit (toon.py, q36_scene.py) with diner condiments as the cast. Calm read, yellow outlined
captions. OT_VOICE=kokoro uses the low-memory Kokoro voice instead of Chatterbox.

python render_q36.py narrate                voice the script (cached in out/q36/voice), print the timing
python render_q36.py preview 1.0,9.5        stills into preview/q36_*.png
python render_q36.py out.mp4 out.wav        full render (Blender frames cached in out/q36/frames)
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
OUT = os.path.join(ROOT, "out", "q36")
FRAMES = os.path.join(OUT, "frames")
TAIL = 1.2

# (line, [(shot, word index the shot starts on), ...]); *word* is colored in the caption
SCRIPT = [
    ("Your friend brought *thirty six questions* to a first date. Laminated.", [("booth", 0), ("booth~2", 10)]),
    ("They're real. In nineteen ninety seven, a psychologist had strangers ask each other these, and they felt *closer* "
     "than pairs making small talk.", [("lab", 0)]),
    ("The full list takes about *forty five minutes.*", [("clock", 0)]),
    ("The viral version ends with *four minutes* of staring into each other's eyes.", [("stare", 0)]),
    ("So she asked all thirty six. Over one basket of *fries.*", [("fries", 0)]),
    ("Then she stared. Her date stared at the *exit.*", [("exit", 0)]),
    ("The waiter stared back. They're *engaged.*", [("final", 0)]),
]
HOOK = ["She brought", "36 QUESTIONS"]

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

SOURCES = "Aron et al. 1997, PSPB. Eye contact: Catron, NYT 2015"

def make_overlay(lines, shots, duration):
    RH.HOOK = HOOK
    base = _height_overlay(lines, shots, duration)
    t_lab = next(t for t, n in shots if n == "lab")
    t_clock = next(t for t, n in shots if n == "fries")
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
    add(0.12, sfx.clip(SNAP, 0.0, 0.25, lp=900), 0.34)                 # the card slaps the table
    add(start["booth~2"] + 0.1, sfx.clip(GLASSY, 0.0, 0.4), 0.12)       # the laminate glints
    for n in ("lab", "clock", "stare", "fries", "exit", "final"):        # the signs land
        add(start[n] + 0.45, sfx.clip(SNAP, 0.0, 0.2, lp=1500), 0.24)
    for k in range(int((start["stare"] - start["clock"]) / 0.5)):        # the clock ticks
        add(start["clock"] + 0.2 + 0.5 * k, sfx.clip(TICK, 0.0, 0.08, lp=3000), 0.06)
    add(start["lab"] + 0.3, sfx.clip(PAGE, 0.0, 0.4), 0.12)
    for k in range(8):                                                   # questions fly by
        add(start["fries"] + 0.2 + 0.18 * k, sfx.clip(POP, 0.0, 0.12, lp=2400), 0.09)
    add(start["exit"] + 0.3, sfx.clip(BUBBLE, 0.0, 0.8), 0.1)            # the date sweats
    add(start["final"] + 0.6, sfx.clip(KALIMBA, 0.0, 1.2), 0.11)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "q36_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots, duration), out_mp4, out_wav, "q36" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
