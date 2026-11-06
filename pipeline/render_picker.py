"""Episode: The Friend Who Can't Pick A Restaurant (ops/episodes/2026-11-06-restaurant-picker.md). A tag-a-friend joke on
Iyengar and Lepper (2000): a grocery store jam booth with 24 or 6 jams; 60% vs 40% stopped, 3% vs 30% bought. Line 6 admits
later studies often find no effect (Scheibehenne et al., 2010). Pastel toy kit (picker_scene.py). Calm read.
Built from render_hangry.py.

python render_picker.py narrate             voice the script (cached in out/picker/voice), print the timing
python render_picker.py preview 1.0,9.5     stills into preview/picker_*.png
python render_picker.py out.mp4 out.wav     full render (Blender frames cached in out/picker/frames)
"""
import json, os, subprocess, sys, time
import numpy as np
import common
from common import *
import kit3d as K
import sfx
from narrate_cb import narrate
from render_led import common_load
import render_late as RL

FPS = 30
OUT = os.path.join(ROOT, "out", "picker")
FRAMES = os.path.join(OUT, "frames")
TAIL = 0.8

SCRIPT = [
    ("Your friend who can't pick a restaurant has a *jam* study.", [("street", 0)], {"jam": 9}),
    ("In 2000{two thousand}, researchers set up a jam tasting booth in a California *grocery store.*", [("store", 0)],
     {"booth": 8}),
    ("Sometimes the table had 24{twenty-four} jams. Other times, only *six.*", [("big", 0), ("small", 8)],
     {"jars24": 4, "jars6": 9}),
    ("The big table pulled more people in. *60{sixty} percent* stopped, versus 40{forty}.", [("stopped", 0)],
     {"crowd": 3, "p60": 7, "p40": 11}),
    ("But only 3{three} percent of those shoppers bought a jar. With six jams, 30{thirty} percent *did.*", [("bought", 0)],
     {"b3": 2, "b30": 13}),
    ("Later studies say it doesn't always happen. Your friend is the case where it *does.*", [("later", 0), ("phone", 7)],
     {"later": 2, "does": 14}),
    ("So don't send them twenty-four places. Send them *two.*", [("two", 0)], {"many": 5, "two": 8}),
    ("Tag the friend who can't pick a *restaurant.*", [("final", 0)], {"end": 0}),
]
HOOK = ["THE FRIEND WHO", "CAN'T PICK A PLACE"]
_SRC = "Iyengar & Lepper, 2000"
NOTES = {"store": _SRC, "big": _SRC, "small": _SRC, "stopped": _SRC, "bought": _SRC,
         "later": "Scheibehenne et al., 2010: effect often small"}

def timeline():
    if os.environ.get("OT_VOICE") == "kokoro":            # Chatterbox needs ~4 GB free commit; Kokoro is the low-memory fallback
        from narrate_kk import narrate as kk
        lines = kk([l for l, _, _ in SCRIPT], OUT, gap=0.28)
    else:
        lines = narrate([l for l, _, _ in SCRIPT], OUT, exaggeration=0.5, cfg=0.4, gap=0.28)
    shots, ev = [], {}
    for (line, plan, evs), L in zip(SCRIPT, lines):
        for name, wi in plan:
            t = L["words"][wi]["start"] - 0.08 if wi else L["start"] - 0.08
            shots.append([0.0 if not shots else round(t, 3), name])
        for k, wi in evs.items():
            ev[k] = L["words"][min(wi, len(L["words"]) - 1)]["start"]
    return lines, shots, ev, lines[-1]["end"] + TAIL

def make_overlay(lines, shots):
    RL.HOOK, RL.NOTES = HOOK, NOTES
    return RL.make_overlay(lines, shots)

# ------------------------------------------------------------------ sound

WOOSH = "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav"
SNAP = "Cinematic Sound Design - Interface & Infographics/Interface Accept Glassy Snap.wav"
POP = "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav"
HIT = "Cinematic Sound Design - Cartoon Impacts/Cartoon Pops Random Sequence Reverb.wav"
MUSIC = "Sonic Bat - Music Boxes/SBmb_Music Box B 028.wav"
CHEER = "Sonik Sound Library - Spanish Crowds/CRWDCheer_Small Club, 50 People, Crowd, Spanish, Cheering and Applause-Surround_KSL_KS015.wav"
CLOTH = "InMotionAudio - Foley T-Shirt/FOLYClth_ClothMovement24_InMotionAudio_FoleyT-Shirt.wav"
CLICK = "Epic Stock Media - Board Game - Sound Set Kit for Tabletop and Digital Games/UIClick_UI Button Analog Vintage Double Click Neutral Dry Press 11_ESM_BG.wav"

def build_audio(lines, shots, ev, duration, out_wav):
    track = np.zeros(int((duration + 1) * SR), np.float32)
    def add(t, x, gain):
        a = int(max(0.0, t) * SR)
        x = x[: len(track) - a]
        track[a:a + len(x)] += x * gain
    add(0.0, common_load(os.path.join(OUT, "narration.wav")), 1.0)
    mb = sfx.clip(MUSIC, 0.0, None, fade=0.2)
    t = 0.0
    while t < duration:
        add(t, mb, 0.03)
        t += len(mb) / SR - 0.2
    for t, _ in shots[1:]:
        add(max(0.0, t - 0.12), sfx.clip(WOOSH, 0.0, 0.5, lp=6000), 0.06)
    for k in range(6):                                                  # phone taps on frame one
        add(0.05 + k * 0.35, sfx.clip(CLICK, 0.0, 0.12), 0.05)
    add(ev["jam"], sfx.clip(POP, 0.0, 0.3), 0.08)
    add(ev["booth"], sfx.clip(SNAP, 0.0, 0.3), 0.08)
    for k in range(8):
        add(ev["jars24"] + k * 0.06, sfx.clip(POP, 0.0, 0.2), 0.04)
    add(ev["jars6"], sfx.clip(HIT, 0.0, 0.2), 0.1)
    add(ev["crowd"], sfx.clip(CLOTH, 0.0, 0.6), 0.15)
    for k in ("p60", "p40", "b3", "b30", "later", "does"):
        add(ev[k], sfx.clip(POP, 0.0, 0.3), 0.09)
    add(ev["many"], sfx.clip(WOOSH, 0.0, 0.5, lp=6000), 0.07)
    add(ev["two"], sfx.clip(SNAP, 0.0, 0.3), 0.1)
    save_wav(track, out_wav, duration)

# ------------------------------------------------------------------ main

def main(out_mp4=None, out_wav=None, preview_times=None):
    common.FPS = FPS
    lines, shots, ev, duration = timeline()
    if out_mp4 is None and preview_times is None:
        for t, n in shots:
            print(f"{t:6.2f} {n}")
        print({k: round(v, 2) for k, v in ev.items()})
        print(f"duration {duration:.2f} s")
        return
    os.makedirs(FRAMES, exist_ok=True)
    n = int(round(duration * FPS))
    frames = sorted({min(n - 1, int(round(x * FPS))) for x in preview_times}) if preview_times else list(range(n))
    tj = os.path.join(OUT, "timing.json")
    json.dump({"fps": FPS, "duration": duration, "shots": shots, "events": ev,
               "font": os.path.join(ROOT, "vendor", "fonts", "Inter-700.ttf")}, open(tj, "w"))
    t0 = time.time()
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "picker_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, ev, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots), out_mp4, out_wav, "picker" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    elif sys.argv[1] == "times":
        main()
    else:
        main(sys.argv[1], sys.argv[2])
