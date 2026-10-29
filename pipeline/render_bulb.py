"""Five-second look test of the product-studio kit (bulb_scene.py): three shots of an LED bulb, captions and labels
in the @speedy_devv manner (small top captions with one boxed keyword, thin leader-line labels, honesty notes).

python render_bulb.py preview 0.8,2.4,4.2     stills into preview/bulb_*.png
python render_bulb.py out.mp4                 the 5 s test clip (silent), Blender frames cached in out/bulb/frames
"""
import json, os, sys, time
import numpy as np
import skia
import common
from common import *
import kit3d as K

FPS = 30
DUR = 5.0
SHOTS = [0.0, 1.65, 3.3]
OUT = os.path.join(ROOT, "out", "bulb")
FRAMES = os.path.join(OUT, "frames")
# (start, end, words); a word in *stars* gets the selection box
CAPTIONS = [(0.05, 0.85, "The light in"), (0.85, 1.62, "your LED bulb"), (1.68, 3.25, "starts out *blue.*"),
            (3.32, 4.15, "A yellow coating"), (4.15, 4.98, "turns it *white.*")]
LABELS = [("chips", "LED CHIPS", 1, 1.85, 3.25, (250, 330)), ("driver", "DRIVER", 1, 2.15, 3.25, (-200, -160)),
          ("die", "BLUE CHIP", 2, 3.45, 5.0, (-250, 230)), ("phosphor", "YELLOW PHOSPHOR", 2, 3.7, 5.0, (-120, -260))]
NOTES = [(1.65, 3.3, "Cutaway illustration"), (3.3, 5.0, "Magnified illustration, not to scale")]
SEL = skia.ColorSetARGB(255, 70, 140, 255)

def txt(c, s, x, y, f, color, alpha):
    c.drawString(s, x, y, f, paint(color, alpha))

def captions(c, t):
    f = font("Inter-700", 64)
    for t0, t1, line in CAPTIONS:
        if not (t0 <= t < t1):
            continue
        a = min(1.0, (t - t0) / 0.08)
        words = line.split(" ")
        widths = [f.measureText(w.strip("*") + " ") for w in words]
        x = (W - sum(widths) + f.measureText(" ")) / 2
        y = 360
        for w, wd in zip(words, widths):
            key = w.startswith("*")
            s = w.strip("*")
            c.drawString(s, x + 3, y + 4, f, paint(skia.ColorSetARGB(255, 0, 0, 0), 0.45 * a))
            c.drawString(s, x, y, f, paint(skia.ColorWHITE, a))
            if key:
                tw = f.measureText(s)
                r = skia.Rect(x - 12, y - 58, x + tw + 12, y + 16)
                c.drawRect(r, skia.Paint(Color=SEL, Style=skia.Paint.kStroke_Style, StrokeWidth=3, AntiAlias=True, Alphaf=a))
                for cx, cy in ((r.left(), r.top()), (r.right(), r.top()), (r.left(), r.bottom()), (r.right(), r.bottom())):
                    c.drawRect(skia.Rect(cx - 6, cy - 6, cx + 6, cy + 6), skia.Paint(Color=skia.ColorWHITE, Alphaf=a))
                    c.drawRect(skia.Rect(cx - 6, cy - 6, cx + 6, cy + 6), skia.Paint(Color=SEL, Style=skia.Paint.kStroke_Style, StrokeWidth=2.5, Alphaf=a))
            x += wd

def labels(c, t, F, A):
    f = font("Inter-700", 30)
    for key, text, shot, t0, t1, (dx, dy) in LABELS:
        if not (t0 <= t < t1) or A[key][F] is None:
            continue
        a = min(1.0, (t - t0) / 0.2) * min(1.0, (t1 - t) / 0.1)
        x, y = A[key][F]
        tx, ty = x + dx, y + dy
        line = skia.Paint(Color=skia.ColorWHITE, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2, AntiAlias=True, Alphaf=0.9 * a)
        c.drawLine(x, y, tx, ty, line)
        c.drawCircle(x, y, 6, skia.Paint(Color=skia.ColorWHITE, AntiAlias=True, Alphaf=a))
        w = f.measureText(text)
        lx = tx - w - 14 if dx < 0 else tx + 14
        lx = max(40, min(lx, W - 40 - w))
        c.drawLine(tx, ty, lx + (w if dx < 0 else 0) + (14 if dx < 0 else -14), ty, line)
        spaced = " ".join(text)                                       # letter-spaced caps
        sf = font("Inter-700", 24)
        sw = sf.measureText(spaced)
        sx = tx - sw - 18 if dx < 0 else tx + 18
        sx = max(40, min(sx, W - 40 - sw))
        c.drawString(spaced, sx + 2, ty - 10, sf, paint(skia.ColorSetARGB(255, 0, 0, 0), 0.55 * a))
        c.drawString(spaced, sx, ty - 12, sf, paint(skia.ColorWHITE, a))

def notes(c, t):
    f = font("Inter-500", 26)
    for t0, t1, s in NOTES:
        if t0 <= t < t1:
            c.drawString(s, 60, H - 330, f, paint(skia.ColorSetARGB(255, 200, 200, 200), 0.75))

def main(out_mp4, preview_times=None):
    os.makedirs(FRAMES, exist_ok=True)
    n = int(round(DUR * FPS))
    frames = sorted({min(n - 1, int(round(x * FPS))) for x in preview_times}) if preview_times else list(range(n))
    tj = os.path.join(OUT, "timing.json")
    with open(tj, "w") as fh:
        json.dump({"fps": FPS, "duration": DUR, "shots": SHOTS, "events": []}, fh)
    t0 = time.time()
    import subprocess
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "bulb_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames ({(time.time() - t0) / len(frames):.2f} s a frame)")
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    def overlay(c, t, F):
        K.top_shade(c, 700, 120)
        captions(c, t)
        labels(c, t, F, A)
        notes(c, t)
    K.composite(FRAMES, frames, FPS, overlay, out_mp4, None, "bulb" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        main(None, [float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1])
