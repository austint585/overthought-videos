"""Episode: Phantom Buzz (ops/episodes/2026-11-07-phantom-buzz.md). Built from render_yawn.py. Was: The Yawn Test. A tag-a-friend joke on Norscia and Palagi (PLoS ONE,
2011): 109 adults watched yawning in everyday life for a year; yawns spread most from family, then friends, then
acquaintances, then strangers, and family and friends caught them faster. Toon kit (toon.py, yawn_scene.py). Calm read,
yellow outlined captions. Built from render_nap.py.

python render_yawn.py narrate                voice the script (cached in out/yawn/voice), print the timing
python render_yawn.py preview 1.0,9.5        stills into preview/yawn_*.png
python render_yawn.py out.mp4 out.wav        full render (Blender frames cached in out/yawn/frames)
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
OUT = os.path.join(ROOT, "out", "buzz")
FRAMES = os.path.join(OUT, "frames")
TAIL = 1.2

# (line, [(shot, word index the shot starts on), ...], {event: word index}); *word* is colored in the caption
SCRIPT = [
    ("Your phone just buzzed in your pocket. Nobody *texted you.*", [("pocket", 0)], {}),
    ("Researchers asked 290{two hundred and ninety} college students about this *exact feeling.*", [("study", 0)], {}),
    ("89{Eighty-nine} percent had felt a buzz that *never happened.*", [("ninety", 0)], {"never": 7}),
    ("Most of them about once every *two weeks.*", [("often", 0)], {}),
    ("And almost nobody was *bothered by it.*", [("chill", 0)], {}),
    ("So your pocket lies to you, and you just *let it.*", [("lying", 0)], {}),
    ("Tag the friend who checks their phone every *five seconds.*", [("final", 0)], {}),
]
HOOK = ["YOUR PHONE", "DIDN'T BUZZ"]

def timeline():
    if os.environ.get("OT_VOICE") == "kokoro":            # Chatterbox needs ~4 GB free commit; Kokoro is the low-memory fallback
        from narrate_kk import narrate as kk
        lines = kk([l for l, _, _ in SCRIPT], OUT, gap=0.22)
    else:
        lines = narrate([l for l, _, _ in SCRIPT], OUT, exaggeration=0.5, cfg=0.4, gap=0.22)
    shots, ev = [], {}
    for (line, plan, evs), L in zip(SCRIPT, lines):
        for name, wi in plan:
            wi = min(wi, len(L["words"]) - 1)
            t = L["words"][wi]["start"] - 0.08 if wi else L["start"] - 0.08
            shots.append([0.0 if not shots else round(t, 3), name])
        for k, wi in evs.items():
            ev[k] = L["words"][min(wi, len(L["words"]) - 1)]["start"]
    return lines, shots, ev, lines[-1]["end"] + TAIL

SOURCES = "Drouin et al., Computers in Human Behavior, 2012"

def make_overlay(lines, shots, duration):
    RH.HOOK = HOOK
    base = _height_overlay(lines, shots, duration)
    t_lab = next(t for t, n in shots if n == "study")
    t_clock = next(t for t, n in shots if n == "lying")
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

BUZZ = "Epic Stock Media - HD Game Materials/WOODFric_Wood Shaker Microphone Head Roll Table Alternate Grainy 05_ESM_HDGM.wav"

def buzz(add, t, n=2, gain=0.10):
    for i in range(n):
        add(t + 0.32 * i, sfx.clip(BUZZ, 0.0, 0.22, lp=900, hp=80), gain)

def build_audio(lines, shots, ev, duration, out_wav):
    track = np.zeros(int((duration + 1) * SR), np.float32)
    def add(t, x, gain):
        a = int(max(0.0, t) * SR)
        x = x[: len(track) - a]
        track[a:a + len(x)] += x * gain
    add(0.0, common_load(os.path.join(OUT, "narration.wav")), 1.0)
    start = {}
    for t, n in shots:
        start.setdefault(n, t)
    for n in ("pocket", "final"):
        buzz(add, start[n] + 0.0)
        add(start[n] + 0.85, sfx.clip(CLOTH, 0.0, 0.35), 0.07)
        add(start[n] + 1.3, sfx.clip(SNAP, 0.0, 0.2, lp=1500), 0.2)
    add(start["study"] + 0.75, sfx.clip(SNAP, 0.0, 0.2, lp=1500), 0.22)
    for k in range(9):
        buzz(add, start["ninety"] + 0.25 + 0.08 * k + (0.08 if k >= 6 else 0), 1, 0.05)
    add(ev["never"] - 0.2, sfx.clip(SNAP, 0.0, 0.2, lp=1500), 0.22)
    add(start["often"] + 0.6, sfx.clip(SNAP, 0.0, 0.2, lp=1500), 0.2)
    for k in range(14):
        add(start["often"] + 0.4 + 0.09 * k, sfx.clip(POP, 0.0, 0.12), 0.03)
    add(start["chill"] + 0.4, sfx.clip(CLOTH, 0.0, 0.4), 0.07)
    add(start["chill"] + 0.9, sfx.clip(SNAP, 0.0, 0.2, lp=1500), 0.2)
    buzz(add, start["lying"] + 0.5)
    add(start["lying"] + 1.0, sfx.clip(SNAP, 0.0, 0.2, lp=1500), 0.2)
    add(start["final"] + 1.6, sfx.clip(KALIMBA, 0.0, 1.2), 0.05)
    save_wav(track, out_wav, duration)

# ------------------------------------------------------------------ main

def main(out_mp4=None, out_wav=None, preview_times=None):
    common.FPS = FPS
    lines, shots, ev, duration = timeline()
    if out_mp4 is None and preview_times is None:
        for t, n in shots:
            print(f"{t:6.2f} {n}")
        print(f"duration {duration:.2f} s")
        return
    os.makedirs(FRAMES, exist_ok=True)
    n = int(round(duration * FPS))
    frames = sorted({min(n - 1, int(round(x * FPS))) for x in preview_times}) if preview_times else list(range(n))
    tj = os.path.join(OUT, "timing.json")
    json.dump({"fps": FPS, "duration": duration, "shots": shots, "events": ev}, open(tj, "w"))
    t0 = time.time()
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "buzz_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, ev, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots, duration), out_mp4, out_wav, "buzz" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "times":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
