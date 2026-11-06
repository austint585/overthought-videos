"""Episode: The Hangry Friend (ops/episodes/2026-11-06-hangry-friend.md). A tag-a-friend joke on MacCormack and Lindquist
(Emotion, 2018): over 200 students fasted or ate, did a boring computer task rigged to crash, and got blamed by a
researcher; the hungry ones felt worse and judged him harsher, unless they had first written about their feelings.
Pastel toy kit, toy peg people (hangry_scene.py). Calm read. Built from render_barista.py.

python render_hangry.py narrate             voice the script (cached in out/hangry/voice), print the timing
python render_hangry.py preview 1.0,9.5     stills into preview/hangry_*.png
python render_hangry.py out.mp4 out.wav     full render (Blender frames cached in out/hangry/frames)
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
OUT = os.path.join(ROOT, "out", "hangry")
FRAMES = os.path.join(OUT, "frames")
TAIL = 0.8

SCRIPT = [
    ("Your friend who gets mean right before *dinner* has a study now.", [("couch", 0)], {"cloud": 3}),
    ("In 2018{twenty eighteen}, psychologists had over 200{two hundred} students skip food or *eat first.*", [("lab", 0)],
     {"students": 6, "skip": 7, "eat": 10}),
    ("Then a long, boring computer task, rigged to *crash* right before the end.", [("task", 0), ("crash", 6)],
     {"type": 2, "crash": 8}),
    ("A researcher walked in and *blamed them* for it.", [("blame", 0)], {"walk": 1, "blame": 5}),
    ("The hungry ones felt more stressed and hateful, and called the researcher *harsh.*", [("hungry", 0)],
     {"stressed": 5, "hateful": 7, "harsh": 12}),
    ("But hungry students who first wrote about their feelings were *fine.*", [("write", 0)], {"wrote": 5, "fine": 10}),
    ("So don't argue with them. Hand them a snack and ask how they *feel.*", [("snack", 0)], {"snack": 5, "feel": 13}),
    ("Tag the friend who gets mean right before *dinner.*", [("final", 0)], {"end": 0}),
]
HOOK = ["THE HANGRY FRIEND", "IT'S A STUDY NOW"]
_SRC = "MacCormack & Lindquist, Emotion, 2018"
NOTES = {"lab": _SRC, "task": _SRC, "crash": _SRC, "blame": _SRC, "hungry": _SRC, "write": _SRC}

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
    add(0.05, sfx.clip(HIT, 0.0, 0.2, lp=900), 0.12)                    # the stomach rumble on frame one
    add(ev["cloud"], sfx.clip(SNAP, 0.0, 0.3), 0.08)
    for k in ("students", "skip", "eat"):
        add(ev[k], sfx.clip(POP, 0.0, 0.3), 0.08)
    for k in range(10):
        add(ev["type"] + k * 0.13, sfx.clip(CLICK, 0.0, 0.12), 0.06)
    add(ev["crash"], sfx.clip(HIT, 0.0, 0.2), 0.14)
    add(ev["walk"], sfx.clip(CLOTH, 0.0, 0.6), 0.15)
    add(ev["blame"], sfx.clip(SNAP, 0.0, 0.3), 0.1)
    for k in ("stressed", "hateful", "harsh", "wrote", "fine", "feel"):
        add(ev[k], sfx.clip(POP, 0.0, 0.3), 0.09)
    add(ev["snack"], sfx.clip(CLOTH, 0.0, 0.5), 0.15)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "hangry_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, ev, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots), out_mp4, out_wav, "hangry" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    elif sys.argv[1] == "times":
        main()
    else:
        main(sys.argv[1], sys.argv[2])
