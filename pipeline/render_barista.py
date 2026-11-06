"""Episode: The Barista Crush (ops/episodes/2026-11-06-barista-crush.md). A tag-a-friend dating joke: the friend in love
with a barista they never talked to, explained by Moreland and Beach's 1992 classroom study (four women sat in a big
lecture 0, 5, 10 or 15 times without speaking, and the class liked the one who came most). Pastel toy kit, toy peg
people (barista_scene.py). Calm read.

python render_barista.py narrate             voice the script (cached in out/barista/voice), print the timing
python render_barista.py preview 1.0,9.5     stills into preview/barista_*.png
python render_barista.py out.mp4 out.wav     full render (Blender frames cached in out/barista/frames)
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
OUT = os.path.join(ROOT, "out", "barista")
FRAMES = os.path.join(OUT, "frames")
TAIL = 0.8

SCRIPT = [
    ("Your friend who's in love with the barista has never *talked* to them.", [("cafe", 0)], {"hearts": 2, "zero": 9}),
    ("Science says that's the whole *point.*", [("cups", 0)], {"cups": 0}),
    ("In 1992{nineteen ninety-two}, psychologists sent four women into a lecture of over 100{a hundred} *students.*",
     [("hall", 0)], {"women": 5}),
    ("One came zero times. One came five. One came ten. One came *fifteen.*", [("four", 0)],
     {"w0": 2, "w5": 6, "w10": 9, "w15": 12}),
    ("They just sat there. They never spoke to *anyone.*", [("sit", 0)], {"ribbon": 4}),
    ("At the end, the class rated the one who came fifteen times the most *attractive.*", [("rate", 0)], {"rate": 0}),
    ("Barely anyone remembered seeing her. They just *liked* her more.", [("who", 0)], {"who": 2}),
    ("So your friend's great love story is mostly *attendance.*", [("love", 0)], {"love": 7}),
    ("Tag your friend who's in love with the *barista.*", [("final", 0)], {"end": 0}),
]
HOOK = ["THE BARISTA CRUSH", "NEVER SPOKE ONCE"]
NOTES = {"hall": "Moreland & Beach, J. Exp. Social Psych., 1992",
         "rate": "Ratings from Moreland & Beach, 1992 (1 to 7 scale)"}

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
    add(0.05, sfx.clip(CLOTH, 0.0, 0.4), 0.12)
    add(ev["hearts"], sfx.clip(POP, 0.0, 0.3), 0.1)
    add(ev["zero"], sfx.clip(SNAP, 0.0, 0.3), 0.08)
    for k in range(8):
        add(ev["cups"] + k * 0.12, sfx.clip(CLICK, 0.0, 0.15), 0.07)
    add(ev["women"], sfx.clip(POP, 0.0, 0.3), 0.08)
    for k in ("w0", "w5", "w10", "w15"):
        add(ev[k], sfx.clip(POP, 0.0, 0.3), 0.1)
    add(ev["ribbon"], sfx.clip(HIT, 0.0, 0.2), 0.1)
    for k in range(4):
        add(ev["rate"] + 0.2 + k * 0.25, sfx.clip(POP, 0.0, 0.3), 0.07)
    add(ev["who"], sfx.clip(CLICK, 0.0, 0.15), 0.1)
    add(ev["love"], sfx.clip(SNAP, 0.0, 0.3), 0.1)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "barista_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, ev, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots), out_mp4, out_wav, "barista" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    elif sys.argv[1] == "times":
        main()
    else:
        main(sys.argv[1], sys.argv[2])
