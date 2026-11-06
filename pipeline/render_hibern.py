"""Episode: Hibernation Mode (ops/episodes/2026-11-06-hibernation-mode.md). The sun sets before 5 now and your friend says
he is hibernating; a real black bear's numbers, and the catch (bears eat up to 20,000 calories a day in the fall). Toon kit
(toon.py, hibern_scene.py), a quilt-wrapped friend and a bear as the cast. Calm read, yellow outlined captions. Built from
render_shave.py. OT_VOICE=kokoro uses the low-memory Kokoro voice.

python render_hibern.py narrate                voice the script (cached in out/hibern/voice), print the timing
python render_hibern.py preview 1.0,9.5        stills into preview/hibern_*.png
python render_hibern.py out.mp4 out.wav        full render (Blender frames cached in out/hibern/frames)
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
OUT = os.path.join(ROOT, "out", "hibern")
FRAMES = os.path.join(OUT, "frames")
TAIL = 1.2

# (line, [(shot, word index the shot starts on), ...]); *word* is colored in the caption
SCRIPT = [
    ("The sun now sets before 5{five}. Your friend is already in a *blanket.*", [("room", 0)]),
    ("He says he's in *hibernation mode.*", [("mode", 0)]),
    ("A hibernating black bear's heart slows to about 8{eight} beats a *minute.*", [("cave", 0)]),
    ("It goes months without eating, drinking or using the *bathroom.*", [("months", 0)]),
    ("Your friend has had food *delivered* three times since Sunday.", [("door", 0)]),
    ("Bears do that part too. In the fall they eat up to 20,000{twenty thousand} *calories* a day.", [("berry", 0)]),
    ("So technically, your friend is still in the *eating part.*", [("eat", 0)]),
    ("And the sun keeps setting earlier until *December.*", [("sunset", 0)]),
    ("Tag your friend. It's 4:48{four forty-eight}. He's *asleep.*", [("final", 0)]),
]
HOOK = ["SUNSET BEFORE 5 PM", "HIBERNATION MODE"]

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

SOURCES = "Black bears: about 8 to 21 beats a minute (North American Bear Center)"

def make_overlay(lines, shots, duration):
    RH.HOOK = HOOK
    base = _height_overlay(lines, shots, duration)
    t_lab = next(t for t, n in shots if n == "cave")
    t_clock = next(t for t, n in shots if n == "door")
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
    add(0.1, sfx.clip(CLOTH, 0.0, 0.8), 0.2)                              # wrapping up in the quilt
    for n in ("mode", "cave", "months", "door", "berry", "eat", "sunset"):   # the signs land
        add(start[n] + 0.45, sfx.clip(SNAP, 0.0, 0.2, lp=1500), 0.22)
    hb = sfx.clip(HEARTB, 0.0, 0.12, lp=400)                             # one slow heartbeat
    add(start["cave"] + 0.8, hb, 0.3)
    add(start["cave"] + 1.15, hb, 0.22)
    for k in range(3):                                                   # three deliveries
        add(start["door"] + 0.3 + 0.45 * k, sfx.clip(POP, 0.0, 0.25), 0.13)
    add(start["door"] + 0.2, sfx.clip(KNOCK, 0.0, 0.2), 0.15)
    for k in range(4):                                                   # munching berries
        add(start["berry"] + 0.3 + 0.25 * k, sfx.clip(BUBBLE, 0.0, 0.15, lp=2500), 0.06)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "hibern_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots, duration), out_mp4, out_wav, "hibern" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "times":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
