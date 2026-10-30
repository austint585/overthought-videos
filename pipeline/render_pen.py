"""Episode: The hole in your pen cap (ops/episodes/2026-10-30-pen-cap-hole.md). Product-studio kit (pen_scene.py: a stick
ballpoint modeled in code on the walnut desk), yelled Chatterbox narration, @speedy_devv-style captions and labels.

python render_pen.py narrate                  voice the script (cached in out/pen/voice), print the timing
python render_pen.py preview 1.0,9.5          stills into preview/pen_*.png
python render_pen.py out.mp4 out.wav          full render (Blender frames cached in out/pen/frames)
"""
import json, math, os, subprocess, sys, time
import numpy as np
import skia
import common
from common import *
import kit3d as K
import sfx
from narrate_cb import narrate
from render_led import chunks, captions, leader, panel, shot_at, common_load

FPS = 30
OUT = os.path.join(ROOT, "out", "pen")
FRAMES = os.path.join(OUT, "frames")
TAIL = 0.45

# (line, [(shot, word index the shot starts on), ...]); *word* is boxed, 11540{eleven five forty} is shown / spoken
SCRIPT = [
    ("The hole in your pen cap has nothing to do with the *ink.*", [("cap", 0), ("cap~2", 6)]),
    ("It's there in case you *inhale* it.", [("throat", 0)]),
    ("If your cap ever gets stuck in your *windpipe,* that hole can let *air* get past it.", [("throat~2", 0)]),
    ("BIC makes its caps to a safety standard called *ISO 11540.*{eleven five forty}", [("std", 0), ("std~2", 5)]),
    ("Now the tiny hole on your *barrel?* That one really is for your *ink.*", [("barrel", 0), ("barrel~2", 7)]),
    ("Every word you write pulls ink out of your tube, and *air* has to come in behind it.", [("drop", 0)]),
    ("With nowhere for air to get in, your pen would just *stop.*", [("drop~2", 0)]),
    ("And your tip? That's a *tungsten carbide* ball, just *1*{one} millimeter wide.", [("tip", 0), ("tip~2", 6)]),
    ("It sits in a tiny socket. Too *tight,* no ink gets out. Too *loose,* your pen *leaks.*", [("socket", 0), ("socket~2", 5)]),
    ("When you write, that ball *rolls,* and drags a thin coat of ink onto your page.", [("roll", 0), ("roll~2", 8)]),
    ("Your ink is thick in the tube, but it gets *runnier* while that ball is spinning.", [("thin", 0), ("thin~2", 8)]),
    ("And that cap you keep chewing on? Someone saw *you* coming.", [("chew", 0)]),
    ("The hole in your pen cap has nothing to do with the *ink.*", [("cap_out", 0)]),
]
LABELS = {   # shot: [(anchor, text, delay after the shot starts, (dx, dy))]
    "cap~2": [("hole", "THE HOLE", 0.2, (-230, 220))],
    "throat": [("tcap", "PEN CAP", 0.3, (230, 200))],
    "throat~2": [("airway", "AIR GETS THROUGH", 0.5, (-190, -180))],
    "barrel": [("vent", "BARREL VENT", 0.4, (180, 260))],
    "drop": [("vent_up", "AIR IN", 0.5, (-200, -80)), ("inktop", "INK LEVEL", 0.9, (230, -60))],
    "tip": [("ball", "BALL", 0.4, (-220, -260))],
    "socket": [("secball", "BALL", 0.3, (260, 220)), ("secink", "INK", 0.6, (-280, 120))],
    "socket~2": [("seat", "SOCKET", 0.2, (260, -220))],
    "roll": [("line", "THE LINE YOU WROTE", 0.8, (60, 240))],
    "thin": [("secball", "SPINNING BALL", 0.3, (260, 220))],
    "chew": [("bite", "YOUR TEETH", 0.8, (240, 260))],
}
NOTES = {"throat": "Cutaway illustration, not to scale. It buys time. Still an emergency.",
         "drop": "Illustration, air shown in light blue", "tip": "Magnified illustration",
         "socket": "Cutaway illustration, not to scale", "thin": "Cutaway illustration, not to scale",
         "std": "BIC data sheet: Cristal cap, ISO 11540"}
SEL = skia.ColorSetARGB(255, 70, 140, 255)
GRAY = skia.ColorSetARGB(255, 150, 150, 150)
RED = skia.ColorSetARGB(255, 255, 90, 70)
GREEN = skia.ColorSetARGB(255, 120, 225, 130)

def timeline():
    lines = narrate([l for l, _ in SCRIPT], OUT, exaggeration=1.6, cfg=0.25)
    shots = []
    for (line, plan), L in zip(SCRIPT, lines):
        for name, wi in plan:
            t = L["words"][wi]["start"] - 0.08 if wi else L["start"] - 0.08
            shots.append([0.0 if not shots else round(t, 3), name])
    return lines, shots, lines[-1]["end"] + TAIL

def fade(t, t0, t1):
    return max(0.0, min(1.0, (t - t0) / 0.2)) * max(0.0, min(1.0, (t1 - t) / 0.15))

def big_card(c, t, t0, t1, small, big, color, y=1180):
    a = fade(t, t0, t1)
    if a <= 0:
        return
    f, fs = font("Inter-700", 76), font("Inter-700", 25)
    wd = max(f.measureText(big), fs.measureText(" ".join(small))) + 90
    panel(c, W / 2 - wd / 2, y - 80, W / 2 + wd / 2, y + 130, a)
    s = " ".join(small)
    c.drawString(s, W / 2 - fs.measureText(s) / 2, y - 26, fs, paint(GRAY, a))
    c.drawString(big, W / 2 - f.measureText(big) / 2, y + 72, f, paint(color, a))

def word_at(line, sub):
    for w in line["words"]:
        if sub in w["w"]:
            return w["start"]
    return line["start"]

def visc_card(c, t, t0, t1):
    a = fade(t, t0, t1)
    if a <= 0:
        return
    u = min(1.0, max(0.0, (t - t0) / (t1 - t0)))
    x0, x1, y = 170, W - 170, 1240
    panel(c, 120, y - 95, W - 120, y + 70, a)
    fs = font("Inter-700", 25)
    c.drawString(" ".join("HOW RUNNY YOUR INK IS"), x0, y - 42, fs, paint(GRAY, a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0, y - 14, x1, y + 16), 15, 15), paint(skia.ColorSetARGB(255, 60, 60, 66), a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0, y - 14, x0 + (x1 - x0) * (0.08 + 0.87 * u * u * (3 - 2 * u)), y + 16), 15, 15), paint(SEL, a))

def make_overlay(lines, shots, duration, A):
    ch = chunks(lines)
    t_tight = word_at(lines[8], "tight")
    t_loose = word_at(lines[8], "loose")
    t_stop = lines[6]["start"]
    def overlay(c, t, F):
        K.top_shade(c, 700, 120)
        name, s0, s1 = shot_at(shots, t, duration)
        for key, text, delay, (dx, dy) in LABELS.get(name, []):
            if t >= s0 + delay and A[key][F] is not None:
                a = min(1.0, (t - s0 - delay) / 0.2) * min(1.0, (s1 - t) / 0.1)
                x, y = A[key][F]
                leader(c, x, y, x + dx, y + dy, text, a)
        base = name.split("~")[0]
        if base in NOTES:
            c.drawString(NOTES[base], 60, 1500, font("Inter-500", 26), paint(skia.ColorSetARGB(255, 200, 200, 200), 0.75))
        if name == "std~2":
            big_card(c, t, s0, s1 + 0.3, "SAFETY STANDARD", "ISO 11540", skia.ColorWHITE)
        if name == "drop~2":
            big_card(c, t, s0, s1, "NO AIR IN", "NO INK OUT", RED)
        if name == "tip~2":
            big_card(c, t, s0, s1, "BALL WIDTH", "1 mm", skia.ColorWHITE)
        big_card(c, t, t_tight - 0.05, t_loose - 0.1, "TOO TIGHT", "NO INK", RED, 1250)
        big_card(c, t, t_loose - 0.05, s1 if name == "socket~2" else t_loose - 0.05, "TOO LOOSE", "LEAK", RED, 1250)
        if name == "thin~2" or name == "thin":
            t0 = next(s for s, n in shots if n == "thin")
            t1 = next(s for s, n in shots if n == "chew")
            visc_card(c, t, t0, t1)
        captions(c, t, ch)
    return overlay

# ------------------------------------------------------------------ sound

CLICK = "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav"
WOOSH = "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav"
SNAP = "Cinematic Sound Design - Interface & Infographics/Interface Accept Glassy Snap.wav"
DENY = "Cinematic Sound Design - System & UI Feedback Elements/Interface Deny Low Fat Dark.wav"
CLOTH = "InMotionAudio - Foley T-Shirt/FOLYClth_ClothMovement24_InMotionAudio_FoleyT-Shirt.wav"

def build_audio(lines, shots, duration, out_wav):
    track = np.zeros(int((duration + 1) * SR), np.float32)
    def add(t, x, gain):
        a = int(max(0.0, t) * SR)
        x = x[: len(track) - a]
        track[a:a + len(x)] += x * gain
    add(0.0, common_load(os.path.join(OUT, "narration.wav")), 1.0)
    start = dict((n, t) for t, n in shots)
    ends = {}
    for i, (t, n) in enumerate(shots):
        ends[n] = shots[i + 1][0] if i + 1 < len(shots) else duration
    add(0.0, sfx.clip(CLICK, 0.0, 0.3), 0.22)
    for t, name in shots[1:]:
        add(t - 0.12, sfx.clip(WOOSH, 0.0, 0.6, lp=6000), 0.09)
    for name, items in LABELS.items():
        for key, text, delay, _ in items:
            add(start[name] + delay, sfx.clip(SNAP, 0.0, 0.4), 0.11)
    add(start["drop~2"] + 0.1, sfx.clip(DENY, 0.0, 0.5), 0.12)
    add(word_at(lines[8], "tight"), sfx.clip(DENY, 0.0, 0.5), 0.10)
    add(word_at(lines[8], "loose"), sfx.clip(DENY, 0.0, 0.5, rate=0.8), 0.10)
    t = start["roll"]                                       # the pen scratching along
    while t < ends["roll~2"] - 0.2:
        add(t, sfx.clip(CLOTH, 0.0, 0.3, hp=2500, lp=9000), 0.12)
        t += 0.36
    save_wav(track, out_wav, duration)

# ------------------------------------------------------------------ main

def main(out_mp4=None, out_wav=None, preview_times=None):
    common.FPS = FPS
    lines, shots, duration = timeline()
    if out_mp4 is None and preview_times is None:
        for t, n in shots:
            print(f"{t:6.2f} {n}")
        print(f"duration {duration:.2f} s")
        return
    os.makedirs(FRAMES, exist_ok=True)
    n = int(round(duration * FPS))
    frames = sorted({min(n - 1, int(round(x * FPS))) for x in preview_times}) if preview_times else list(range(n))
    tj = os.path.join(OUT, "timing.json")
    json.dump({"fps": FPS, "duration": duration, "shots": shots}, open(tj, "w"))
    t0 = time.time()
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "pen_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    if not preview_times:
        build_audio(lines, shots, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots, duration, A), out_mp4, out_wav, "pen" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
