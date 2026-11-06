"""Episode: Mercury Retrograde (ops/episodes/2026-11-05-mercury-retrograde.md). The friend who texts the ex and blames
Mercury retrograde, in the toon kit (toon.py, merc_scene.py) with a phone and a little planet as the cast. Calm read,
yellow outlined captions. Built from render_q36.py. OT_VOICE=kokoro uses the low-memory Kokoro voice.

python render_merc.py narrate                voice the script (cached in out/merc/voice), print the timing
python render_merc.py preview 1.0,9.5        stills into preview/merc_*.png
python render_merc.py out.mp4 out.wav        full render (Blender frames cached in out/merc/frames)
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
OUT = os.path.join(ROOT, "out", "merc")
FRAMES = os.path.join(OUT, "frames")
TAIL = 1.2

# (line, [(shot, word index the shot starts on), ...]); *word* is colored in the caption
SCRIPT = [
    ("Your friend texted their ex and blamed *Mercury.*", [("bed", 0), ("bed~2", 5)]),
    ("Right now, Mercury is in *retrograde.* It looks like it's moving backwards across the sky.", [("sky", 0), ("sky~2", 6)]),
    ("It's an illusion. Mercury *laps* us, so it looks like it's going back.", [("orbit", 0), ("orbit~2", 3)]),
    ("This year that's three times. Sixty six days in *total.*", [("cal", 0)]),
    ("The other two hundred ninety nine days, your friend texted the ex *anyway.*", [("count", 0)]),
    ("Mercury never actually goes backwards. Your friend could *try it.*", [("road", 0)]),
]
HOOK = ["Texted the ex.", "BLAMED MERCURY"]

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

SOURCES = "Dates: Old Farmer's Almanac 2026. Motion: NASA Space Place"

def make_overlay(lines, shots, duration):
    RH.HOOK = HOOK
    base = _height_overlay(lines, shots, duration)
    t_lab = next(t for t, n in shots if n == "sky")
    t_clock = next(t for t, n in shots if n == "count")
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
    add(0.05, sfx.clip(POP, 0.0, 0.25), 0.3)                            # the text fires off on frame one
    add(start["bed~2"] + 0.1, sfx.clip(GLASSY, 0.0, 0.4), 0.12)
    for n in ("sky", "orbit", "cal", "count", "road"):                    # the signs land
        add(start[n] + 0.45, sfx.clip(SNAP, 0.0, 0.2, lp=1500), 0.24)
    add(start["sky"] + 0.2, sfx.clip(KALIMBA, 0.0, 1.2), 0.07)
    add(start["cal"] + 0.3, sfx.clip(PAGE, 0.0, 0.4), 0.12)
    for k in range(12):                                                   # texts keep flying
        add(start["count"] + 0.2 + 0.25 * k, sfx.clip(POP, 0.0, 0.12, lp=2400), 0.08)
    add(start["road"] + 0.6, sfx.clip(BUBBLE, 0.0, 0.8), 0.08)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "merc_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots, duration), out_mp4, out_wav, "merc" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
