"""Episode: Tiny animals are living on your face (ops/episodes/2026-10-30-face-mites.md). Body-macro short: skin at macro
scale and a cut follicle (mites_scene.py), day to night. Yelled Chatterbox narration, @speedy_devv-style captions and
labels (shared with render_led.py).

python render_mites.py narrate               voice the script (cached in out/mites/voice), print the timing
python render_mites.py preview 1.0,9.5       stills into preview/mites_*.png
python render_mites.py out.mp4 out.wav       full render (Blender frames cached in out/mites/frames)
"""
import json, os, subprocess, sys, time
import numpy as np
import skia
import common
from common import *
import kit3d as K
import sfx
from narrate_cb import narrate
from render_led import chunks, captions, leader, panel, shot_at, common_load, word_time

FPS = 30
OUT = os.path.join(ROOT, "out", "mites")
FRAMES = os.path.join(OUT, "frames")
TAIL = 0.45

# (line, [(shot, word index the shot starts on), ...])
SCRIPT = [
    ("Right now, tiny animals are living on your *face.*", [("skin_in", 0)]),
    ("They're called *face mites.* More than *90*{ninety} *percent* of people have them.", [("hero", 0), ("field", 4)]),
    ("Each one is under a *third of a millimeter* long, living in your *pores,* sucking up your skin *grease.*", [("section", 0), ("pore", 10), ("feed", 14)]),
    ("And at *night,* while you're asleep, they crawl *out.*", [("dusk", 0), ("emerge", 5)]),
    ("They walk across your face, find each other, and *mate* on your *skin.*", [("crawl", 0), ("meet", 7)]),
    ("People even said they had no *anus,* and held it in their whole *lives.*", [("rear", 0)]),
    ("A 2022{twenty twenty two} study looked. They *do.*", [("found", 0)]),
    ("So yeah. Right now, tiny animals are living on your *face.*", [("skin_out", 0)]),
]
LABELS = {   # shot: [(anchor, text, delay after the shot starts, (dx, dy))]
    "hero": [("hero", "FACE MITE", 0.3, (-240, -260))],
    "section": [("smite", "UNDER 0.3 MM", 0.4, (240, -240))],
    "pore": [("follicle", "HAIR FOLLICLE", 0.2, (-260, -230))],
    "feed": [("oil", "SKIN GREASE", 0.3, (240, 240))],
    "found": [("rear", "CONFIRMED", 0.5, (-240, -240))],
}
NOTES = {"skin_in": "Illustration, mite enlarged", "hero": "Illustration, mite enlarged", "field": "Illustration, mites enlarged",
         "section": "Cutaway illustration, not to scale", "pore": "Cutaway illustration, not to scale",
         "feed": "Cutaway illustration, not to scale", "dusk": "Illustration", "emerge": "Illustration, mites enlarged",
         "crawl": "Illustration, mites enlarged", "meet": "Illustration, mites enlarged", "rear": "Illustration, mite enlarged",
         "found": "Illustration, mite enlarged", "skin_out": "Illustration, mite enlarged"}

def timeline():
    lines = narrate([l for l, _ in SCRIPT], OUT, exaggeration=1.6, cfg=0.25)
    shots = []
    for (line, plan), L in zip(SCRIPT, lines):
        for name, wi in plan:
            t = L["words"][wi]["start"] - 0.08 if wi else L["start"] - 0.08
            shots.append([0.0 if not shots else round(t, 3), name])
    duration = lines[-1]["end"] + TAIL
    return lines, shots, duration

def percent_card(c, t, t0, t1):
    a = min(1.0, (t - t0) / 0.2) * min(1.0, (t1 - t) / 0.15)
    if a <= 0:
        return
    u = max(0.0, min(1.0, (t - t0 - 0.1) / 0.8))
    panel(c, 290, 1200, W - 290, 1400, a)
    f, fs = font("Inter-700", 78), font("Inter-700", 24)
    s = f"{int(90 * u * u * (3 - 2 * u))}%+"
    c.drawString(s, W / 2 - f.measureText(s) / 2, 1310, f, paint(skia.ColorWHITE, a))
    s = " ".join("OF PEOPLE")
    c.drawString(s, W / 2 - fs.measureText(s) / 2, 1365, fs, paint(skia.ColorSetARGB(255, 150, 150, 150), a))

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
        if name in NOTES:
            c.drawString(NOTES[name], 60, 1500, font("Inter-500", 26), paint(skia.ColorSetARGB(255, 200, 200, 200), 0.75))
        if name == "field":
            percent_card(c, t, s0, s1)
        captions(c, t, ch)
    return overlay

# ------------------------------------------------------------------ sound

BUB = "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Bubbles Short.wav"
SQUELCH = "Epic Stock Media - Tower Defense Game/WOODImpt_Hit Blood Spill Splat Wood Impact Light Hit Squelch Small Thump 03_ESM_TDG.wav"
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
    add(0.05, sfx.clip(SQUELCH, 0.0, 0.5, lp=5000), 0.20)
    for t, name in shots[1:]:
        add(t - 0.12, sfx.clip(WOOSH, 0.0, 0.6, lp=6000), 0.09)
    for name, items in LABELS.items():
        for key, text, delay, _ in items:
            add(start[name] + delay, sfx.clip(SNAP, 0.0, 0.4), 0.11)
    add(start["feed"] + 0.2, sfx.clip(BUB, 0.0, 1.2, lp=6000), 0.14)
    for name in ("emerge", "crawl", "meet"):                 # a soft wet step now and then
        for k in range(3):
            add(start[name] + 0.2 + k * 0.5, sfx.clip(SQUELCH, 0.0, 0.25, lp=4000), 0.07)
    add(start["found"] + 0.5, sfx.clip(SQUELCH, 0.0, 0.5, lp=5000), 0.22)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "mites_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    if not preview_times:
        build_audio(lines, shots, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots, duration, A), out_mp4, out_wav, "mites" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
