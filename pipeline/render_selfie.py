"""Episode: She is not unphotogenic (ops/episodes/2026-11-03-mirror-face.md). The friend who hates every photo of herself, explained
with the 1977 mirror-print study and the 2018 selfie-distance study, in the pastel toy kit (selfie_scene.py). Calm Chatterbox read,
dark caption pills with one boxed word (the water episode's captions).

python render_selfie.py narrate                voice the script (cached in out/selfie/voice), print the timing
python render_selfie.py preview 1.0,9.5        stills into preview/selfie_*.png
python render_selfie.py out.mp4 out.wav        full render (Blender frames cached in out/selfie/frames)
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
OUT = os.path.join(ROOT, "out", "selfie")
FRAMES = os.path.join(OUT, "frames")
TAIL = 1.0

# (line, [(shot, word index the shot starts on), ...], {event: word index}); *word* is boxed in the caption
SCRIPT = [
    ("Your friend who hates every photo of herself is not unphotogenic. She has just never seen her *real face.*",
     [("bin", 0), ("mirror", 11)], {}),
    ("Every morning, the mirror shows it to her *flipped.*", [("mirror~2", 0)], {}),
    ("In nineteen seventy seven, psychologists showed people two prints of their own face: the real one, and the *mirror* one.",
     [("prints", 0)], {}),
    ("People picked the *mirror* one. Their friends picked the *real* one.", [("prints~2", 0)], {"pick1": 3, "pick2": 8}),
    ("Psychologists call it the *mere exposure effect.* You like the face you see the most.", [("label", 0)], {}),
    ("And the front camera makes it worse. At twelve inches, a selfie makes your nose look about *thirty percent* wider.",
     [("selfie", 0), ("selfie~2", 7)], {"nose": 17}),
    ("From five feet, there's *no difference.*", [("portrait", 0)], {}),
    ("So when she says that's not what she looks like, she's right. It's what she looks like to *you.*", [("final", 0)], {}),
]
HOOK = ["She is not", "unphotogenic"]
NOTES = {"prints": "Mita, Dermer & Knight 1977, J. of Personality and Social Psychology",
         "prints~2": "Mita, Dermer & Knight 1977, J. of Personality and Social Psychology",
         "selfie~2": "Ward et al. 2018, JAMA Facial Plastic Surgery (a modeled face)",
         "portrait": "Ward et al. 2018: no difference at 5 ft",
         "final": "Data: Mita et al. 1977, Ward et al. 2018"}

def timeline():
    lines = narrate([l for l, _, _ in SCRIPT], OUT, exaggeration=0.5, cfg=0.4, gap=0.22)
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
PAGE = "Cinematic Sound Design - Paper Foley/Encyclopedia Glossy Page Turn Muted.wav"
HIT = "Cinematic Sound Design - Cartoon Impacts/Cartoon Pops Random Sequence Reverb.wav"
BUBBLE = "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Bubbles Short.wav"

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
    for t, _ in shots[1:]:
        add(max(0.0, t - 0.12), sfx.clip(WOOSH, 0.0, 0.5, lp=6000), 0.07)
    for k in range(7):                                                  # each polaroid lands in the bin
        tk = (k * 0.55 + 1.0) / 1.6
        if tk < start["mirror"]:
            add(tk, sfx.clip(PAGE, 0.0, 0.22, hp=1200), 0.14)
    add(start["mirror~2"] + 0.1, sfx.clip(SNAP, 0.0, 0.3), 0.12)
    add(start["mirror~2"] + 0.35, sfx.clip(SNAP, 0.0, 0.3), 0.1)
    add(ev["pick1"], sfx.clip(POP, 0.0, 0.3), 0.2)
    add(ev["pick2"], sfx.clip(POP, 0.0, 0.3), 0.2)
    add(start["label"] + 0.3, sfx.clip(HIT, 0.0, 0.35), 0.16)
    add(start["selfie"] + 0.2, sfx.clip(SNAP, 0.0, 0.2, hp=1500), 0.12)   # the shutter
    add(ev["nose"], sfx.clip(BUBBLE, 0.0, 0.6), 0.16)                   # the nose swells
    add(start["portrait"] + 0.3, sfx.clip(SNAP, 0.0, 0.3), 0.12)
    add(start["final"] + 0.5, sfx.clip(HIT, 0.0, 0.35), 0.14)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "selfie_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, ev, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots), out_mp4, out_wav, "selfie" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
