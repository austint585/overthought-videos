"""Episode: Why a fork sparks in your microwave (ops/episodes/2026-10-28-fork-sparks.md). Product-studio kit
(fork_scene.py: Poly Haven's CC0 microwave on the walnut desk, a cutaway oven cavity), yelled Chatterbox narration,
@speedy_devv-style captions and labels (shared with render_led.py). Replaces the Oct 28 voxel draft.

python render_fork.py narrate                  voice the script (cached in out/fork/voice), print the timing
python render_fork.py preview 1.0,9.5          stills into preview/fork_*.png
python render_fork.py out.mp4 out.wav          full render (Blender frames cached in out/fork/frames)
"""
import json, math, os, subprocess, sys, time
import numpy as np
import skia
import common
from common import *
import kit3d as K
import sfx
from narrate_cb import narrate
from render_led import chunks, captions, leader, panel, shot_at, common_load, word_time

FPS = 30
OUT = os.path.join(ROOT, "out", "fork")
FRAMES = os.path.join(OUT, "frames")
TAIL = 0.45

# (line, [(shot, word index the shot starts on), ...])
SCRIPT = [
    ("Your fork doesn't spark because it's metal. It sparks because it's *pointy.*", [("front", 0), ("spark_tip", 7)]),
    ("Your microwave fills with waves that flip back and forth *2.45*{two point four five} *billion* times a second.", [("waves", 0), ("waves~2", 6)]),
    ("Your food soaks them up. That's how your leftovers get *hot.*", [("food", 0), ("food~2", 5)]),
    ("But metal can't soak them up, so it *reflects* them off its surface.", [("reflect", 0), ("reflect~2", 6)]),
    ("Every flip shoves the *electrons* in your fork one way, then the other.", [("electrons", 0), ("electrons~2", 7)]),
    ("They pile up at the sharpest parts of your fork, the *tips* of your tines.", [("tips", 0), ("tips~2", 8)]),
    ("Right at a sharp tip, the electric field gets strong enough to rip electrons off the *air.*", [("breakdown", 0), ("breakdown~2", 9)]),
    ("That air turns into *plasma.* That's the *spark* you see.", [("spark", 0), ("spark~2", 5)]),
    ("Your smooth *spoon* spreads the charge out, so it usually stays *calm.*", [("spoon", 0), ("spoon~2", 6)]),
    ("Crumpled *foil* is nothing but points. That's why it *crackles* like crazy.", [("foil", 0), ("foil~2", 6)]),
    ("Leave it running and those sparks can *scorch* your oven, or even start a *fire.*", [("scorch", 0), ("scorch~2", 8)]),
    ("So your fork doesn't spark because it's metal. It sparks because it's *pointy.*", [("front_out", 0)]),
]
LABELS = {   # shot: [(anchor, text, delay after the shot starts, (dx, dy))]
    "food": [("mug", "WATER ABSORBS", 0.4, (230, -220))],
    "reflect": [("fork", "STAINLESS FORK", 0.3, (180, -240))],
    "electrons": [("electron", "ELECTRONS", 0.4, (-230, -230))],
    "tips": [("tips", "CHARGE PILES UP", 0.6, (-260, -230))],
    "breakdown": [("air", "AIR MOLECULES", 0.4, (-250, -240))],
    "spark": [("tips", "PLASMA", 0.3, (-230, -240))],
    "spoon": [("spoon", "SMOOTH EDGES", 0.4, (200, -240))],
    "foil": [("foil", "ALL EDGES", 0.4, (220, -240))],
    "scorch": [("scorch", "SCORCH MARK", 0.8, (-240, 240))],
}
NOTES = {"spark_tip": "Illustration", "waves": "Cutaway illustration", "food": "Cutaway illustration, heat shown in orange",
         "reflect": "Cutaway illustration", "electrons": "Magnified illustration, not to scale",
         "tips": "Magnified illustration, not to scale", "breakdown": "Magnified illustration, not to scale",
         "spark": "Illustration", "spoon": "Cutaway illustration", "foil": "Illustration",
         "scorch": "Illustration of what can happen. Do not try this"}

def timeline():
    lines = narrate([l for l, _ in SCRIPT], OUT, exaggeration=1.6, cfg=0.25)
    shots = []
    for (line, plan), L in zip(SCRIPT, lines):
        for name, wi in plan:
            t = L["words"][wi]["start"] - 0.08 if wi else L["start"] - 0.08
            shots.append([0.0 if not shots else round(t, 3), name])
    duration = lines[-1]["end"] + TAIL
    return lines, shots, duration

def wave_card(c, t, t0, t1):
    a = min(1.0, (t - t0) / 0.2) * min(1.0, (t1 - t) / 0.15)
    if a <= 0:
        return
    y, h = 1230, 90
    panel(c, 110, y - h - 70, W - 110, y + h + 110, a)
    path = skia.Path()
    for i in range(301):
        x = 160 + i * (W - 320) / 300
        yy = y - math.sin(i / 300 * 10 * math.pi - t * 14) * h * 0.8
        path.moveTo(x, yy) if i == 0 else path.lineTo(x, yy)
    c.drawPath(path, skia.Paint(Color=skia.ColorSetARGB(255, 120, 170, 255), Style=skia.Paint.kStroke_Style, StrokeWidth=5, AntiAlias=True, Alphaf=a))
    u = max(0.0, min(1.0, (t - t0 - 0.2) / 1.4))
    n = int(2_450_000_000 * u * u * (3 - 2 * u) / 1_000_000) * 1_000_000
    f, fs = font("Inter-700", 58), font("Inter-700", 24)
    s = f"{n:,}"
    c.drawString(s, W / 2 - f.measureText(s) / 2, y + h + 55, f, paint(skia.ColorWHITE, a))
    s = " ".join("FLIPS EVERY SECOND")
    c.drawString(s, W / 2 - fs.measureText(s) / 2, y - h - 25, fs, paint(skia.ColorSetARGB(255, 150, 150, 150), a))

def make_overlay(lines, shots, duration, A):
    ch = chunks(lines)
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
        if name == "waves~2":
            wave_card(c, t, s0, s1)
        captions(c, t, ch)
    return overlay

# ------------------------------------------------------------------ sound

BEEP = "InMotionAudio - Medical Thermometer/BEEPMed_Thermometer_Beep11_InMotionAudio_MedicalThermometer.wav"
ARCS = "InMotionAudio - Arc/ELECArc_ArcDesign15_InMotionAudio_Arc.wav"
FIRE = "Epic Stock Media - Synthesized Nature Loops and Sounds/FIREBurn_Loop Elements Fire Crackling Crunchy Flame Burn 03_ESM_SNLS.wav"
WOOSH = "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav"
SNAP = "Cinematic Sound Design - Interface & Infographics/Interface Accept Glassy Snap.wav"

def build_audio(lines, shots, duration, out_wav):
    track = np.zeros(int((duration + 1) * SR), np.float32)
    def add(t, x, gain):
        a = int(max(0.0, t) * SR)
        x = x[: len(track) - a]
        track[a:a + len(x)] += x * gain
    add(0.0, common_load(os.path.join(OUT, "narration.wav")), 1.0)
    start = dict((n, t) for t, n in shots)
    ends = {}
    for i, (t, n) in enumerate(shots):                       # an action ends when its last angle does
        ends[n.split("~")[0]] = shots[i + 1][0] if i + 1 < len(shots) else duration
    add(0.0, sfx.clip(BEEP, 0.0, 0.35), 0.20)
    for t, name in shots[1:]:
        add(t - 0.12, sfx.clip(WOOSH, 0.0, 0.6, lp=6000), 0.09)
    for name, items in LABELS.items():
        for key, text, delay, _ in items:
            add(start[name] + delay, sfx.clip(SNAP, 0.0, 0.4), 0.11)
    for name, g in (("front", 0.06), ("spark_tip", 0.12), ("spark", 0.14), ("foil", 0.12), ("front_out", 0.06)):
        t, k = start[name], 0
        while t < ends[name] - 0.2:
            add(t, sfx.clip(ARCS, (0.37 * k) % max(0.01, len(sfx._load(ARCS)) / SR - 0.3), 0.25, lp=7000), g)
            t += 0.45 + 0.2 * ((k * 7) % 3)
            k += 1
    add(start["scorch"] + 0.4 * (ends["scorch"] - start["scorch"]), sfx.clip(FIRE, 0.0, 2.0, lp=6000), 0.10)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "fork_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    if not preview_times:
        build_audio(lines, shots, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots, duration, A), out_mp4, out_wav, "fork" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
