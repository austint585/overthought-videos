"""Episode: The Period Text (ops/episodes/2026-11-06-period-text.md). A tag-a-friend joke on Gunraj, Klin and colleagues
(Computers in Human Behavior, 2016; Binghamton release Dec 2015): 126 students read short exchanges answered with one word
(Okay, Sure, Yeah, Yup); replies ending in a period were rated less sincere, with no difference on handwritten notes.
Pastel toy kit (period_scene.py). Calm read. Built from render_picker.py.

python render_period.py narrate             voice the script (cached in out/period/voice), print the timing
python render_period.py preview 1.0,9.5     stills into preview/period_*.png
python render_period.py out.mp4 out.wav     full render (Blender frames cached in out/period/frames)
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
OUT = os.path.join(ROOT, "out", "period")
FRAMES = os.path.join(OUT, "frames")
TAIL = 0.8

SCRIPT = [
    ("Your friend replied okay, with a *period.* You felt that.", [("kitchen", 0)], {"period": 6, "felt": 8}),
    ("In 2015{twenty fifteen} psychologists showed 126{a hundred and twenty-six} students short *text exchanges.*",
     [("room", 0)], {"n126": 4, "texts": 7}),
    ("Someone asks a question. The answer is one word: okay, sure, yeah, *yup.*", [("screen", 0)],
     {"ask": 1, "w1": 9, "w2": 10, "w3": 11, "w4": 12}),
    ("Half the replies ended with a period. Half had *nothing.*", [("split", 0)], {"dot": 6, "none": 9}),
    ("Replies with a period were rated less *sincere.*", [("meter", 0)], {"rated": 5, "less": 6}),
    ("On handwritten notes, the period made *no difference.*", [("note", 0)], {"note": 1, "same": 6}),
    ("So you weren't imagining it. That dot *meant something.*", [("back", 0)], {"roll": 5}),
    ("Tag the friend who texts okay with a *period.*", [("final", 0)], {"end": 0}),
]
HOOK = ["OKAY.", "WITH A PERIOD"]
_SRC = "Gunraj et al., Computers in Human Behavior, 2016"
NOTES = {"room": _SRC, "screen": _SRC, "split": _SRC, "meter": _SRC, "note": _SRC}

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
    add(0.02, sfx.clip(SNAP, 0.0, 0.3), 0.1)                            # the reply lands on frame one
    add(ev["period"], sfx.clip(HIT, 0.0, 0.2, lp=900), 0.14)               # the dot drops
    add(ev["felt"], sfx.clip(CLOTH, 0.0, 0.5), 0.12)
    for k in ("n126", "texts", "ask", "w1", "w2", "w3", "w4", "dot", "none", "less", "note", "same"):
        add(ev[k], sfx.clip(POP, 0.0, 0.3), 0.08)
    add(ev["rated"], sfx.clip(SNAP, 0.0, 0.3), 0.08)
    for k in range(6):
        add(ev["roll"] + k * 0.16, sfx.clip(CLICK, 0.0, 0.12), 0.05 * (1 - k / 7))
    add(ev["end"] + 0.1, sfx.clip(SNAP, 0.0, 0.3), 0.08)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "period_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, ev, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots), out_mp4, out_wav, "period" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    elif sys.argv[1] == "times":
        main()
    else:
        main(sys.argv[1], sys.argv[2])
