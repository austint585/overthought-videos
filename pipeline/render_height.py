"""Episode: Height inflation (ops/episodes/2026-11-02-height-inflation.md). Deadpan economics of dating-app height in the toon
kit (toon.py, height_scene.py), calm Chatterbox read, yellow outlined captions low in the frame, a hook label on frame 1.

python render_height.py narrate                voice the script (cached in out/height/voice), print the timing
python render_height.py preview 1.0,9.5        stills into preview/height_*.png
python render_height.py out.mp4 out.wav        full render (Blender frames cached in out/height/frames)
"""
import json, os, subprocess, sys, time
import numpy as np
import skia
import common
from common import *
import kit3d as K
import sfx
from narrate_cb import narrate
from render_led import chunks, common_load

FPS = 30
OUT = os.path.join(ROOT, "out", "height")
FRAMES = os.path.join(OUT, "frames")
TAIL = 1.2

# (line, [(shot, word index the shot starts on), ...]); *word* is colored in the caption
SCRIPT = [
    ("Every man on a dating app is *six feet* tall.", [("stamp", 0), ("stamp~2", 7)]),
    ("Economists call this *height inflation.*", [("press", 0)]),
    ("In twenty ten, OkCupid ran the numbers. Men were listing about *two inches* they don't have.", [("chart", 0), ("chart~2", 7)]),
    ("The real average American man is *five nine.*", [("door", 0)]),
    ("But at five eleven he's one inch from *six feet,* and nobody stops at five eleven.", [("stairs", 0), ("stairs~2", 8)]),
    ("So the market floods. Now six feet buys you *nothing.*", [("flood", 0), ("flood~2", 4)]),
    ("Actual six foot guys have to print *six one.* Six one prints *six two.*", [("stairs2", 0)]),
    ("And it's all backed by nothing. *Boots.* *Hair.* A *hill.*", [("vault", 0), ("boot", 6), ("hair", 7), ("hill", 8)]),
    ("You really are about a *centimeter* taller when you wake up, so he only measures at *seven a.m.*", [("bed", 0), ("clock", 10)]),
    ("One man still holds his value. He's five seven. He says *five seven.*", [("gold", 0), ("gold~2", 6)]),
    ("Economists call him the *gold standard.* Women call him *a great friend.*", [("final", 0)]),
]
HOOK = ["Every man on a dating app", "is 6 feet tall"]
YELLOW = skia.ColorSetARGB(255, 255, 226, 66)
ORANGE = skia.ColorSetARGB(255, 255, 126, 40)
OUTLINE = skia.ColorSetARGB(255, 12, 14, 26)

def timeline():
    lines = narrate([l for l, _ in SCRIPT], OUT, exaggeration=0.5, cfg=0.4, gap=0.22)
    shots = []
    for (line, plan), L in zip(SCRIPT, lines):
        for name, wi in plan:
            t = L["words"][wi]["start"] - 0.08 if wi else L["start"] - 0.08
            shots.append([0.0 if not shots else round(t, 3), name])
    return lines, shots, lines[-1]["end"] + TAIL

def text_outlined(c, s, x, y, f, color, width=11):
    c.drawString(s, x, y, f, skia.Paint(Color=OUTLINE, AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width, StrokeJoin=skia.Paint.kRound_Join))
    c.drawString(s, x, y, f, skia.Paint(Color=color, AntiAlias=True))

def make_overlay(lines, shots, duration):
    ch = chunks(lines)
    hook_end = lines[0]["end"] + 0.1
    def overlay(c, t, F):
        if t < hook_end:                                    # the premise, readable on frame 1
            f = font("Fredoka-700", 60)
            for i, s in enumerate(HOOK):
                wd = f.measureText(s)
                x, y = (W - wd) / 2, 262 + i * 84
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 26, y - 56, x + wd + 26, y + 20), 16, 16), skia.Paint(Color=skia.ColorWHITE, AntiAlias=True))
                c.drawString(s, x, y, f, skia.Paint(Color=OUTLINE, AntiAlias=True))
        f = font("Fredoka-700", 64)
        for i, cw in enumerate(ch):
            t0 = cw[0]["start"] - 0.03
            t1 = ch[i + 1][0]["start"] - 0.03 if i + 1 < len(ch) else cw[-1]["end"] + 0.5
            if not (t0 <= t < t1):
                continue
            s = [w["w"] for w in cw]
            x = (W - (sum(f.measureText(a + " ") for a in s) - f.measureText(" "))) / 2
            for w in cw:
                text_outlined(c, w["w"], x, 1400, f, ORANGE if w["key"] else YELLOW)
                x += f.measureText(w["w"] + " ")
    return overlay

# ------------------------------------------------------------------ sound

PERC = "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav"
PAPER = "Cinematic Sound Design - Paper Foley/A4 Printing Paper Rattle Page Turn Tail.wav"
PAGE = "Cinematic Sound Design - Paper Foley/Encyclopedia Glossy Page Turn Muted.wav"
CLOTH = "InMotionAudio - Foley T-Shirt/FOLYClth_ClothMovement24_InMotionAudio_FoleyT-Shirt.wav"
TICK = "344 Audio - Antique Clocks/CLOCKTick_Crooked Antique Clock_344 Audio_Antique Clocks.wav"
KALIMBA = "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Kalimba 3 Up_CB Sounddesign_APPlicable Sounds.wav"

def build_audio(lines, shots, duration, out_wav):
    track = np.zeros(int((duration + 1) * SR), np.float32)
    def add(t, x, gain):
        a = int(max(0.0, t) * SR)
        x = x[: len(track) - a]
        track[a:a + len(x)] += x * gain
    add(0.0, common_load(os.path.join(OUT, "narration.wav")), 1.0)
    start, end = {}, {}
    for i, (t, n) in enumerate(shots):
        start.setdefault(n, t)
        end[n] = shots[i + 1][0] if i + 1 < len(shots) else duration
    def thuds(t0, t1, step, gain=0.3, lp=1600):
        t = t0
        while t < t1 - 0.05:
            add(t, sfx.clip(PERC, 0.0, 0.2, lp=lp), gain)
            t += step
    thuds(0.0, start["press"], 0.6, 0.34)                   # the stamp, from the first frame
    thuds(start["press"], end["press"], 0.3, 0.2, 2400)
    add(start["chart"] + 0.2, sfx.clip(PAGE, 0.0, 0.6), 0.2)
    add(start["door"] + 0.2, sfx.clip(CLOTH, 0.0, 0.3, hp=1500), 0.2)
    for name in ("stairs", "stairs2"):                      # a hop on each step
        for k in range(4):
            add(start[name] + 0.15 + k * 0.62, sfx.clip(PERC, 0.0, 0.2, lp=2200), 0.22)
    t = start["flood"]
    while t < end["flood~2"]:
        add(t, sfx.clip(PAPER, 0.0, 0.5), 0.09)
        t += 0.4
    for name in ("boot", "hair", "hill"):
        add(start[name], sfx.clip(PERC, 0.0, 0.2, lp=1500), 0.3)
    add(start["bed"] + 0.25, sfx.clip(CLOTH, 0.0, 0.4), 0.22)
    t = start["clock"]
    while t < end["clock"]:
        add(t, sfx.clip(TICK, 0.2, 0.14), 0.28)
        t += 0.14
    add(start["gold"] + 0.1, sfx.clip(KALIMBA, 0.0, 1.5), 0.12)
    add(start["final"] + 0.1, sfx.clip(KALIMBA, 0.0, 1.5), 0.1)
    fw = next(w for w in lines[-1]["words"] if w["w"].lower().startswith("women"))
    add(fw["start"], sfx.clip(PERC, 0.0, 0.2, lp=900), 0.34)    # the sign flips
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
    women = next(w for w in lines[-1]["words"] if w["w"].lower().startswith("women"))["start"]
    json.dump({"fps": FPS, "duration": duration, "shots": shots, "flip": women}, open(tj, "w"))
    t0 = time.time()
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "height_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots, duration), out_mp4, out_wav, "height" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
