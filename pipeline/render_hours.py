"""Episode: We Should Hang Out Sometime (ops/episodes/2026-11-03-hang-out-sometime.md). The friend who keeps saying "we should
hang out sometime", run through the 2018 University of Kansas study of how many hours a friendship takes, in the pastel toy kit
(hours_scene.py). Two toy mugs are the cast. Calm Chatterbox read, dark caption pills with one boxed word.

python render_hours.py narrate                voice the script (cached in out/hours/voice), print the timing
python render_hours.py preview 1.0,9.5        stills into preview/hours_*.png
python render_hours.py out.mp4 out.wav        full render (Blender frames cached in out/hours/frames)
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
OUT = os.path.join(ROOT, "out", "hours")
FRAMES = os.path.join(OUT, "frames")
TAIL = 1.0

# (line, [(shot, word index the shot starts on), ...], {event: word index}); *word* is boxed in the caption
SCRIPT = [
    ("This is you and the friend who keeps saying we should hang out *sometime.*", [("cafe", 0)], {}),
    ("In twenty eighteen, a University of Kansas study counted how many *hours* a friendship actually takes.",
     [("study", 0)], {}),
    ("About *fifty hours* together to go from acquaintance to casual friend.", [("bar", 0)], {"m50": 1}),
    ("About *ninety* to become actual friends.", [("bar~2", 0)], {"m90": 1}),
    ("And over *two hundred* to be close friends.", [("bar200", 0)], {"m200": 2}),
    ("Now say you two really hang out twice a year, for two hours each.", [("calendar", 0)], {"circle1": 7, "circle2": 11}),
    ("That's *four hours* a year.", [("calendar~2", 0)], {}),
    ("At that rate, you become close friends in *fifty years.*", [("porch", 0)], {"years": 8}),
    ("Send this to them. It counts as *zero* hours.", [("final", 0)], {"sent": 0}),
]
HOOK = ["We should hang out", "sometime"]
NOTES = {"study": "Hall 2018, Journal of Social and Personal Relationships",
         "bar": "Hall 2018: about 50 hours to a casual friend",
         "bar~2": "Hall 2018: about 90 hours to a friend",
         "bar200": "Hall 2018: over 200 hours to a close friend",
         "calendar": "Twice a year is our example, not data",
         "porch": "200 hours at 4 hours a year",
         "final": "Data: Hall 2018, University of Kansas"}

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
CLINK = SNAP

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
    add(0.35, sfx.clip(CLINK, 0.0, 0.4), 0.14)                          # the two mugs slide up and stop short
    add(start["study"] + 0.4, sfx.clip(PAGE, 0.0, 0.3, hp=900), 0.12)
    for k in ("m50", "m90", "m200"):
        add(ev[k], sfx.clip(POP, 0.0, 0.3), 0.2)
    for k in ("circle1", "circle2"):
        add(ev[k], sfx.clip(SNAP, 0.0, 0.25), 0.12)
    add(start["calendar~2"] + 0.4, sfx.clip(HIT, 0.0, 0.35), 0.14)
    add(ev["years"], sfx.clip(HIT, 0.0, 0.35), 0.16)
    add(ev["sent"], sfx.clip(BUBBLE, 0.0, 0.5), 0.14)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "hours_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, ev, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots), out_mp4, out_wav, "hours" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
