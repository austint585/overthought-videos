"""Episode: You Too (ops/episodes/2026-11-03-you-too.md). A second-person story in the @garden_reels1o shape Austin sent on Nov 3:
you still say "you too" to waiters, a witness who writes it down, and the payoff at your own wedding. Pastel toy kit with toy peg
people (youtoo_scene.py). Calm Chatterbox read.

python render_youtoo.py narrate                voice the script (cached in out/youtoo/voice), print the timing
python render_youtoo.py preview 1.0,9.5        stills into preview/youtoo_*.png
python render_youtoo.py out.mp4 out.wav        full render (Blender frames cached in out/youtoo/frames)
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
OUT = os.path.join(ROOT, "out", "youtoo")
FRAMES = os.path.join(OUT, "frames")
TAIL = 1.2

SCRIPT = [
    ("You're twenty six, and you still say *you too* to waiters.", [("rest", 0)], {}),
    ("The waiter puts down your pasta and says, enjoy your *meal.*", [("waiter", 0)], {"plate": 3, "enjoy": 8}),
    ("You say: *you too.*", [("you", 0)], {"youtoo1": 2}),
    ("He is not eating. He is at *work.*", [("waiter~2", 0)], {"work": 7}),
    ("Your date doesn't laugh. She just writes something on a *napkin*, and puts it in her purse.", [("napkin", 0)],
     {"write": 6, "purse": 12}),
    ("At the movies, the ticket guy says, enjoy the *show.*", [("booth", 0)], {"enjoy2": 7}),
    ("*You too.* He is not coming in.", [("booth~2", 0)], {"youtoo2": 0}),
    ("A man across the street waves. You wave back. He was waving at his *Uber{/ˈuːbɚ/}.*", [("street", 0)],
     {"manwave": 5, "youwave": 7, "uber": 14}),
    ("Two years later. Your *wedding.*", [("wedding", 0)], {"later": 0}),
    ("The officiant says, you may now kiss the bride.", [("officiant", 0)], {"kiss": 3}),
    ("You look him in the eye and say: *you too.*", [("groom", 0)], {"youtoo3": 8}),
    ("Your wife pulls out the *napkin* from your first date.", [("bride", 0)], {"pull": 2}),
    ("It says: he'll do it at the *wedding.*", [("note", 0)], {"reveal": 2}),
]
HOOK = ["You still say", "YOU TOO"]
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
BUBBLE = "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Bubbles Short.wav"

def build_audio(lines, shots, ev, duration, out_wav):
    track = np.zeros(int((duration + 1) * SR), np.float32)
    def add(t, x, gain):
        a = int(max(0.0, t) * SR)
        x = x[: len(track) - a]
        track[a:a + len(x)] += x * gain
    add(0.0, common_load(os.path.join(OUT, "narration.wav")), 1.0)
    for t, _ in shots[1:]:
        add(max(0.0, t - 0.12), sfx.clip(WOOSH, 0.0, 0.5, lp=6000), 0.07)
    add(ev["plate"], sfx.clip(SNAP, 0.0, 0.3), 0.14)
    for k in ("enjoy", "enjoy2", "kiss"):
        add(ev[k], sfx.clip(POP, 0.0, 0.3), 0.16)
    for k in ("youtoo1", "youtoo2", "youtoo3"):
        add(ev[k], sfx.clip(HIT, 0.0, 0.35), 0.16)
    add(ev["write"], sfx.clip(PAGE, 0.0, 0.3, hp=900), 0.12)
    add(ev["purse"], sfx.clip(SNAP, 0.0, 0.25), 0.1)
    add(ev["uber"], sfx.clip(BUBBLE, 0.0, 0.4), 0.12)
    add(ev["pull"], sfx.clip(PAGE, 0.0, 0.3, hp=900), 0.14)
    add(ev["reveal"], sfx.clip(HIT, 0.0, 0.35), 0.18)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "youtoo_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, ev, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots), out_mp4, out_wav, "youtoo" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
