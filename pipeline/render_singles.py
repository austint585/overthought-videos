"""Episode: Singles' Day (ops/episodes/2026-11-06-singles-day.md). A seasonal tag-a-friend joke: Nov 11 is the holiday for
single people (Nanjing University dorms, 1993), Alibaba turned it into the biggest sale ($84.5B in 2021), and in 2011 over
4,000 Beijing couples took it as their wedding day. Pastel toy kit at night with toy peg people (singles_scene.py). Calm read.

python render_singles.py narrate             voice the script (cached in out/singles/voice), print the timing
python render_singles.py preview 1.0,9.5     stills into preview/singles_*.png
python render_singles.py out.mp4 out.wav     full render (Blender frames cached in out/singles/frames)
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
OUT = os.path.join(ROOT, "out", "singles")
FRAMES = os.path.join(OUT, "frames")
TAIL = 0.8

SCRIPT = [
    ("Your single friend has a holiday coming up. *November 11th{eleventh}.*", [("apart", 0)], {"phone": 0}),
    ("Four ones in a row. One for each *single person.*", [("ones", 0)], {"ones": 0}),
    ("It started in 1993{nineteen ninety-three}, in a dorm at Nanjing University, to celebrate *being single.*", [("dorm", 0)],
     {"cheer": 11}),
    ("In 2009{two thousand nine}, Alibaba turned it into a *sale.*", [("sale", 0)], {"sale": 7}),
    ("By 2021{twenty twenty-one}, Alibaba sold 84{eighty-four} billion *dollars* of stuff in it.", [("counter", 0)], {"count": 3}),
    ("So the one day for single people became the day they *buy themselves presents.*", [("presents", 0)], {"hug": 11}),
    ("And in 2011{twenty eleven}, over 4,000{four thousand} couples in Beijing picked it as their *wedding day.*", [("wedding", 0)],
     {"wed": 4}),
    ("Even the holiday for single people got *taken.*", [("taken", 0)], {"droop": 7}),
    ("Tag your single friend. Their holiday is *Wednesday.*", [("final", 0)], {"end": 0}),
]
HOOK = ["YOUR SINGLE", "FRIEND'S HOLIDAY"]
NOTES = {"wedding": "Reported by The Economist, 2011",
         "counter": "Alibaba's 11-day festival, 540.3 billion yuan"}

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
            ev[k] = L["words"][wi]["start"]
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
    for j in range(3):
        add(ev["phone"] + 0.2 + j * 0.35, sfx.clip(CLICK, 0.0, 0.15), 0.08)
    for k in range(4):
        add(ev["ones"] + k * 0.3, sfx.clip(POP, 0.0, 0.3), 0.12)
    add(ev["cheer"], sfx.clip(CHEER, 1.0, 2.6, fade=0.4), 0.08)
    add(0.25, sfx.clip(HIT, 0.0, 0.2), 0.07)
    for k in range(1, 14):
        add(ev["sale"] + k * 0.16 + 0.33, sfx.clip(HIT, 0.0, 0.2), 0.07)
    add(ev["count"], sfx.clip(SNAP, 0.0, 0.3), 0.13)
    add(ev["hug"], sfx.clip(CLOTH, 0.0, 0.6), 0.2)
    add(ev["hug"] + 0.3, sfx.clip(POP, 0.0, 0.3), 0.1)
    add(ev["wed"], sfx.clip(CHEER, 3.0, 5.5, fade=0.5), 0.08)
    add(ev["wed"] + 0.2, sfx.clip(SNAP, 0.0, 0.3), 0.12)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "singles_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, ev, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots), out_mp4, out_wav, "singles" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    elif sys.argv[1] == "times":
        main()
    else:
        main(sys.argv[1], sys.argv[2])
