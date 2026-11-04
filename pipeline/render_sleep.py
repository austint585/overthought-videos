"""Episode: Second Sleep (ops/episodes/2026-11-04-second-sleep.md). A second-person story in the @garden_reels1o / @design.pilot
shape Austin sent (Nov 3 and Nov 4): you text your ex "u up?" at 3 a.m., the neighbours file in one by one, then the real history
turn (pre-industrial "first sleep" and "second sleep", A. Roger Ekirch). Pastel toy kit at night with toy peg people
(sleep_scene.py). Calm Chatterbox read.

python render_sleep.py narrate                voice the script (cached in out/sleep/voice), print the timing
python render_sleep.py preview 1.0,9.5        stills into preview/sleep_*.png
python render_sleep.py out.mp4 out.wav        full render (Blender frames cached in out/sleep/frames)
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
OUT = os.path.join(ROOT, "out", "sleep")
FRAMES = os.path.join(OUT, "frames")
TAIL = 0.8

SCRIPT = [
    ("It's 3{three} a.m. You text your ex: *u{you} up?*", [("phone", 0)], {"sent": 7}),
    ("No reply. Then somebody *knocks.*", [("door", 0)], {"knock": 4}),
    ("It's your neighbor. Holding a *candle.*", [("neighbor", 0)], {"open": 0}),
    ("He sits on your bed and asks how the *harvest* went.", [("bed", 0)], {"sit": 1, "harvest": 6}),
    ("Then his wife walks in with *soup.*", [("wife", 0)], {"wife": 2}),
    ("Then a priest. Then a man with a *goose.*", [("priest", 0), ("goose", 5)], {"priest": 0, "gooseman": 5}),
    ("The goose sits on your *router.*", [("router", 0)], {"perch": 2}),
    ("Your ex texts back. She's at the door, with *her neighbors.*", [("phone2", 0), ("exdoor", 4)],
     {"buzz": 2, "ex": 4}),
    ("What you don't know: before electric light, people slept in *two shifts.*", [("history", 0)], {"shifts": 10}),
    ("They woke up for an hour or two in the middle of the *night.*", [("wake", 0)], {"wake": 1}),
    ("Some prayed. Some went over to visit the *neighbors.*", [("visit", 0)], {"walk": 2, "knock2": 6}),
    ("Old records call it *first sleep*, then *second sleep.*", [("book", 0)], {"first": 4, "second": 7}),
    ("The goose falls asleep *first.*", [("pile", 0)], {"zzz": 2}),
    ("So the next time it's 3{three} a.m. and you text your ex, it's *tradition.*", [("phone3", 0)], {"sent2": 9}),
]
HOOK = ["It's 3 a.m.", "U UP?"]
NOTES = {}

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
PAGE = "Cinematic Sound Design - Paper Foley/Encyclopedia Glossy Page Turn Muted.wav"
HIT = "Cinematic Sound Design - Cartoon Impacts/Cartoon Pops Random Sequence Reverb.wav"
KNOCK = "344 Audio - Haunting Ambiences Vol. 3/WOODImpt_Wooden Hit, Dark, Heavy Hit, Vampire's Prison_344 Audio_Haunting Ambiences Vol 3.wav"
CREAK = "344 Audio - Cinema Experience Vol. 1/FOLYProp_Sitting Down, Creaky Seat, Squeaks 3_344 Audio_CInema Experience.wav"
RING = "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Xylophone Ringtone 2_CB Sounddesign_APPlicable Sounds.wav"

def build_audio(lines, shots, ev, duration, out_wav):
    track = np.zeros(int((duration + 1) * SR), np.float32)
    def add(t, x, gain):
        a = int(max(0.0, t) * SR)
        x = x[: len(track) - a]
        track[a:a + len(x)] += x * gain
    add(0.0, common_load(os.path.join(OUT, "narration.wav")), 1.0)
    for t, _ in shots[1:]:
        add(max(0.0, t - 0.12), sfx.clip(WOOSH, 0.0, 0.5, lp=6000), 0.06)
    for k in ("sent", "sent2"):
        add(ev[k], sfx.clip(SNAP, 0.0, 0.3), 0.14)
    knock = sfx.clip(KNOCK, 0.0, 0.22, lp=3000)
    for k in ("knock", "knock2"):
        for j in range(3):
            add(ev[k] + j * 0.2, knock, 0.2 if k == "knock" else 0.12)
    add(ev["sit"], sfx.clip(CREAK, 0.0, 0.8), 0.14)
    for k in ("harvest", "wife", "priest", "gooseman", "ex"):
        add(ev[k], sfx.clip(POP, 0.0, 0.3), 0.13)
    add(ev["perch"], sfx.clip(HIT, 0.0, 0.35), 0.13)
    add(ev["buzz"], sfx.clip(RING, 0.0, 0.7), 0.1)
    add(ev["wake"], sfx.clip(CREAK, 0.0, 0.6), 0.1)
    for k in ("first", "second"):
        add(ev[k], sfx.clip(PAGE, 0.0, 0.3, hp=900), 0.13)
    add(ev["zzz"], sfx.clip(HIT, 0.0, 0.35), 0.12)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "sleep_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, ev, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots), out_mp4, out_wav, "sleep" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    elif sys.argv[1] == "times":
        main()
    else:
        main(sys.argv[1], sys.argv[2])
