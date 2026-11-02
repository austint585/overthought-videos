"""Episode: The note in your lunch (ops/episodes/2026-11-02-lunch-note.md). A nostalgic "you" story in the clay kit with
objects as the whole cast (lunch_scene.py), a calm Chatterbox read, cream clay captions, foley on every action.

python render_lunch.py narrate                voice the script (cached in out/lunch/voice), print the timing
python render_lunch.py preview 1.0,9.5        stills into preview/lunch_*.png
python render_lunch.py out.mp4 out.wav        full render (Blender frames cached in out/lunch/frames)
"""
import json, os, subprocess, sys, time
import numpy as np
import skia
import common
from common import *
import render_tap as tap
import kit3d as K
import sfx
from narrate_cb import narrate
from render_led import chunks, shot_at, common_load

FPS = 30
OUT = os.path.join(ROOT, "out", "lunch")
FRAMES = os.path.join(OUT, "frames")
TAIL = 2.4      # the note holds on screen after the last line

# (line, [(shot, word index the shot starts on), ...]); *word* is colored in the caption
SCRIPT = [
    ("Your mom wrote you a *note* once. You threw it out without *reading* it.", [("open", 0), ("open~2", 6)]),
    ("It's ten at night. You've been asleep for *two hours.*", [("wide", 0), ("clock", 4)]),
    ("She's still up, cutting the *crusts* off your sandwich,", [("knife", 0), ("knife~2", 5)]),
    ("because in first grade you told her they taste *weird.*", [("crust", 0)]),
    ("You don't remember saying that. She *does.*", [("fridge", 0)]),
    ("She writes your *name* on the bag, even though you're the only one taking a lunch.", [("write", 0), ("write~2", 7)]),
    ("Then she tucks in a *note.*", [("note", 0)]),
    ("At noon, you eat the chips, and trade the *apple* for a cookie.", [("cafe", 0), ("cafe~2", 6)]),
    ("The note goes in the *trash.*", [("trash", 0)]),
    ("Now you're home for one *weekend.* Same kitchen. Same *lamp.*", [("wide2", 0)]),
    ("It's ten at night. You leave in the *morning.*", [("clock2", 0)]),
    ("She's making you a sandwich for the *drive.*", [("plate", 0)]),
    ("*Crusts off.*", [("crust2", 0)]),
    ("You're *twenty-six.* You'd eat the crusts now.", [("crust2~2", 0)]),
    ("She doesn't know that. Don't tell her.", [("final", 0)]),
]
CREAM = skia.ColorSetARGB(255, 246, 236, 214)
DARKT = skia.ColorSetARGB(255, 42, 36, 44)
BLUE = skia.ColorSetARGB(255, 42, 96, 214)

def timeline():
    lines = narrate([l for l, _ in SCRIPT], OUT, exaggeration=0.5, cfg=0.4, gap=0.3)
    shots = []
    for (line, plan), L in zip(SCRIPT, lines):
        for name, wi in plan:
            t = L["words"][wi]["start"] - 0.08 if wi else L["start"] - 0.08
            shots.append([0.0 if not shots else round(t, 3), name])
    shots.append([round(lines[-1]["end"] + 0.35, 3), "ending"])
    return lines, shots, lines[-1]["end"] + TAIL

def cream_captions(c, t, ch):
    f = font("Fredoka-700", 62)
    for i, cw in enumerate(ch):
        t0 = cw[0]["start"] - 0.03
        t1 = ch[i + 1][0]["start"] - 0.03 if i + 1 < len(ch) else cw[-1]["end"] + 0.4
        if not (t0 <= t < t1):
            continue
        s = [w["w"] for w in cw]
        wd = sum(f.measureText(x + " ") for x in s) - f.measureText(" ")
        x, y = (W - wd) / 2, 380
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 30, y - 62, x + wd + 30, y + 24), 26, 26), skia.Paint(Color=CREAM, AntiAlias=True))
        for w in cw:
            c.drawString(w["w"], x, y, f, skia.Paint(Color=BLUE if w["key"] else DARKT, AntiAlias=True))
            x += f.measureText(w["w"] + " ")

def make_overlay(lines, shots, duration):
    ch = chunks(lines)
    def overlay(c, t, F):
        K.top_shade(c, 620, 70)
        cream_captions(c, t, ch)
    return overlay

# ------------------------------------------------------------------ sound

MARKER = "Cinematic Sound Design - Paper Foley/Newspaper Static Foley Rummage.wav"
PAPER = "Cinematic Sound Design - Paper Foley/A4 Printing Paper Rattle Page Turn Tail.wav"
PAGE = "Cinematic Sound Design - Paper Foley/Encyclopedia Glossy Page Turn Muted.wav"
CLOTH = "InMotionAudio - Foley T-Shirt/FOLYClth_ClothMovement24_InMotionAudio_FoleyT-Shirt.wav"
TICK = "344 Audio - Antique Clocks/CLOCKTick_Crooked Antique Clock_344 Audio_Antique Clocks.wav"
PERC = "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav"
KIDS = "Epic Stock Media - Public Spaces - Crowds Walla and Everyday Ambiences/CRWDChld_Walla Children Kids Daytime School Playing Laughing Playground 01_ESM_CPS.wav"
CRICK = "344 Audio - East Coast America Vol. 1/AMBSubn_Ambience, Forest Crickets, Birds, Connecticut 02_344 Audio_East Coast America.wav"
KALIMBA = "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Kalimba 3 Up_CB Sounddesign_APPlicable Sounds.wav"

def build_audio(lines, shots, duration, out_wav):
    track = np.zeros(int((duration + 1) * SR), np.float32)
    def add(t, x, gain):
        a = int(max(0.0, t) * SR)
        x = x[: len(track) - a]
        track[a:a + len(x)] += x * gain
    add(0.0, common_load(os.path.join(OUT, "narration.wav")), 1.0)
    start = {}
    end = {}
    for i, (t, n) in enumerate(shots):
        start.setdefault(n, t)
        end[n] = shots[i + 1][0] if i + 1 < len(shots) else duration
    def scribble(t0, t1):                                   # felt marker on paper: short strokes
        t = t0
        while t < t1 - 0.1:
            add(t, sfx.clip(CLOTH, 0.0, 0.16, hp=2500, lp=9000), 0.2)
            t += 0.22
    def bed(path, t0, t1, gain, **kw):
        x = sfx.clip(path, 2.0, t1 - t0, **kw)
        f = min(len(x) // 4, int(0.25 * SR))
        x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
        add(t0, x, gain)
    bed(CRICK, 0.0, start["cafe"], 0.05, lp=7000)
    bed(CRICK, start["wide2"], duration, 0.05, lp=7000)
    bed(KIDS, start["cafe"], start["wide2"], 0.05, lp=5000)
    scribble(0.05, start["open~2"] - 0.1)
    t = start["clock"]
    while t < end["clock"]:
        add(t, sfx.clip(TICK, 0.2, 0.14), 0.2)
        t += 0.5
    t = start["knife"]
    while t < end["knife~2"] - 0.1:                         # the knife through bread
        add(t, sfx.clip(CLOTH, 0.0, 0.2, lp=3000), 0.2)
        t += 0.5
    for k in range(4):
        add(start["crust"] + 0.25 + k * 0.5, sfx.clip(PERC, 0.0, 0.2, lp=1800), 0.12)
    scribble(start["write"] + 0.15, end["write~2"] - 0.8)
    add(start["note"] + 0.3, sfx.clip(PAGE, 0.0, 0.7), 0.2)
    add(start["cafe~2"] + 0.1, sfx.clip(CLOTH, 0.0, 0.3), 0.2)
    add(start["trash"] + 0.1, sfx.clip(PAPER, 0.0, 0.6), 0.2)
    add(start["trash"] + 1.0, sfx.clip(PERC, 0.0, 0.2, lp=1400), 0.2)
    t = start["wide2"]
    for k in range(8):                                      # the clock running through the years
        add(t + k * 0.08, sfx.clip(TICK, 0.2, 0.08), 0.13)
    t = start["clock2"]
    while t < end["clock2"]:
        add(t, sfx.clip(TICK, 0.2, 0.14), 0.2)
        t += 0.5
    add(start["plate"] + 0.2, sfx.clip(PERC, 0.0, 0.2, lp=2500), 0.15)
    add(start["ending"], sfx.clip(KALIMBA, 0.0, 1.5), 0.12)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "lunch_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots, duration), out_mp4, out_wav, "lunch" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
