"""Episode: Your LED bulb starts out blue (ops/episodes/2026-10-30-led-bulb-blue.md). Product-studio kit
(led_scene.py), yelled Chatterbox narration (narrate_cb.py), @speedy_devv-style captions, labels and cards.

python render_led.py narrate                  voice the script (cached in out/led/voice), print the timing
python render_led.py preview 1.0,9.5,30.2     stills into preview/led_*.png
python render_led.py out.mp4 out.wav          full render (Blender frames cached in out/led/frames)
"""
import json, math, os, subprocess, sys, time
import numpy as np
import skia
import common
from common import *
import kit3d as K
import sfx
from narrate_cb import narrate

FPS = 30
OUT = os.path.join(ROOT, "out", "led")
FRAMES = os.path.join(OUT, "frames")
TAIL = 0.45

# (line, [(shot, word index the shot starts on), ...]); *word* is boxed, 1,000.{a thousand} is shown / spoken
SCRIPT = [
    ("The light in your LED bulb starts out *blue.*", [("hang", 0)]),
    ("Not white. Not warm. *Blue.*", [("hang_white", 0), ("hang_warm", 2), ("hang_blue", 4)]),
    ("Inside, a ring of tiny chips is glowing pure *blue.*", [("ring_blue", 0)]),
    ("Every chip sits in a little cup of yellow powder called *phosphor.*", [("macro_fill", 0)]),
    ("The phosphor eats some of that blue and spits it back out as *yellow.*", [("macro_photons", 0)]),
    ("Blue plus yellow hits your eyes, and your brain just calls it *white.*", [("macro_top", 0)]),
    ("That's why cheap LED light looks a little cold. There's barely any *red* in it.", [("spectrum", 0)]),
    ("And heat makes the phosphor dimmer, and it kills the *chips.*", [("hot_board", 0)]),
    ("Those fins? Not decoration. They're a *heat* *sink,* pulling heat off the chips.", [("fins", 0)]),
    ("The base isn't empty either. A tiny power supply turns your wall's *AC* into the low *DC* the chips need.", [("driver", 0)]),
    ("Keep it cool and it can last *30,000*{thirty} to *50,000*{fifty thousand} hours. An old bulb? About *1,000.*{a thousand}", [("versus", 0)]),
    ("All of that, just so your LED bulb can start out *blue.*", [("hang_out", 0)]),
]
LABELS = {   # shot: [(anchor, text, delay after the shot starts, (dx, dy))]
    "ring_blue": [("chips", "LED CHIPS", 0.4, (250, 330))],
    "macro_fill": [("die", "BLUE CHIP", 0.3, (-250, 230)), ("phosphor", "YELLOW PHOSPHOR", 1.6, (-120, -260))],
    "hot_board": [("chips", "LED CHIPS", 0.5, (250, 330))],
    "fins": [("fins", "HEAT SINK", 1.6, (-260, 300))],
    "driver": [("driver", "DRIVER", 0.4, (-200, -160))],
}
NOTES = {"ring_blue": "Cutaway illustration", "hot_board": "Cutaway illustration, heat shown in orange",
         "driver": "Cutaway illustration", "macro_fill": "Magnified illustration, not to scale",
         "macro_photons": "Magnified illustration, not to scale", "macro_top": "Magnified illustration, not to scale",
         "spectrum": "Schematic spectrum of a phosphor-white LED", "fins": "Heat shown in orange",
         "versus": "Lifetimes: US Department of Energy, LED Basics"}
SEL = skia.ColorSetARGB(255, 70, 140, 255)
GRAY = skia.ColorSetARGB(255, 150, 150, 150)

# ------------------------------------------------------------------ timing

def timeline():
    lines = narrate([l for l, _ in SCRIPT], OUT, exaggeration=1.6, cfg=0.25)
    shots = []
    for (line, plan), L in zip(SCRIPT, lines):
        for name, wi in plan:
            t = L["words"][wi]["start"] - 0.08 if wi else L["start"] - 0.08
            shots.append([0.0 if not shots else round(t, 3), name])
    duration = lines[-1]["end"] + TAIL
    L11 = lines[10]
    w = {x["w"]: x for x in L11["words"]}
    ramp = (w["last"]["start"], w["hours."]["end"])
    old_dies = ramp[0] + (ramp[1] - ramp[0]) * math.log(1000) / math.log(50000)
    return lines, shots, duration, {"old_dies": old_dies, "ramp": ramp}

def shot_at(shots, t, duration):
    k = max([0] + [i for i, (s, _) in enumerate(shots) if t >= s])
    t1 = shots[k + 1][0] if k + 1 < len(shots) else duration
    return shots[k][1], shots[k][0], t1

# ------------------------------------------------------------------ overlay

def chunks(lines):
    """Caption chunks of up to 3 words, broken after punctuation; each shows from its first word to the next chunk."""
    out = []
    for L in lines:
        cur = []
        for w in L["words"]:
            cur.append(w)
            if len(cur) == 3 or w["w"][-1] in ".,?!":
                out.append(cur); cur = []
        if cur:
            out.append(cur)
    return out

def captions(c, t, ch):
    f = font("Inter-700", 66)
    for i, cw in enumerate(ch):
        t0 = cw[0]["start"] - 0.03
        t1 = ch[i + 1][0]["start"] - 0.03 if i + 1 < len(ch) else cw[-1]["end"] + 0.5
        if not (t0 <= t < t1):
            continue
        shown = [w for w in cw if w["start"] - 0.03 <= t]
        widths = [f.measureText(w["w"] + " ") for w in cw]
        x = (W - sum(widths) + f.measureText(" ")) / 2
        y = 360
        for j, (w, wd) in enumerate(zip(cw, widths)):
            if w not in shown:
                break
            current = j == len(shown) - 1
            col = skia.ColorWHITE if current or w["key"] else GRAY
            c.drawString(w["w"], x + 3, y + 4, f, paint(skia.ColorSetARGB(255, 0, 0, 0), 0.45))
            c.drawString(w["w"], x, y, f, paint(col, 1.0))
            if w["key"]:
                tw = f.measureText(w["w"])
                r = skia.Rect(x - 12, y - 58, x + tw + 12, y + 16)
                c.drawRect(r, skia.Paint(Color=SEL, Style=skia.Paint.kStroke_Style, StrokeWidth=3, AntiAlias=True))
                for cx, cy in ((r.left(), r.top()), (r.right(), r.top()), (r.left(), r.bottom()), (r.right(), r.bottom())):
                    c.drawRect(skia.Rect(cx - 6, cy - 6, cx + 6, cy + 6), skia.Paint(Color=skia.ColorWHITE))
                    c.drawRect(skia.Rect(cx - 6, cy - 6, cx + 6, cy + 6), skia.Paint(Color=SEL, Style=skia.Paint.kStroke_Style, StrokeWidth=2.5))
            x += wd

def leader(c, x, y, tx, ty, text, a):
    line = skia.Paint(Color=skia.ColorWHITE, Style=skia.Paint.kStroke_Style, StrokeWidth=2.2, AntiAlias=True, Alphaf=0.9 * a)
    c.drawLine(x, y, tx, ty, line)
    c.drawCircle(x, y, 6, skia.Paint(Color=skia.ColorWHITE, AntiAlias=True, Alphaf=a))
    sf = font("Inter-700", 24)
    spaced = " ".join(text)
    sw = sf.measureText(spaced)
    left = tx < x
    sx = max(40, min(tx - sw - 18 if left else tx + 18, W - 40 - sw))
    c.drawLine(tx, ty, sx + (sw + 4 if left else -4), ty, line)
    c.drawString(spaced, sx + 2, ty - 10, sf, paint(skia.ColorSetARGB(255, 0, 0, 0), 0.55 * a))
    c.drawString(spaced, sx, ty - 12, sf, paint(skia.ColorWHITE, a))

def panel(c, x0, y0, x1, y1, a):
    a = max(0.0, min(1.0, a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0, y0, x1, y1), 28, 28), skia.Paint(Color=skia.ColorSetARGB(int(215 * a), 12, 12, 16), AntiAlias=True))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0, y0, x1, y1), 28, 28), skia.Paint(Color=skia.ColorSetARGB(int(60 * a), 255, 255, 255), Style=skia.Paint.kStroke_Style, StrokeWidth=2, AntiAlias=True))

def mix_card(c, t, t0, t1):
    a = min(1.0, (t - t0) / 0.2) * min(1.0, (t1 - t) / 0.15)
    u = min(1.0, max(0.0, (t - t0 - 0.3) / 1.2))
    u = u * u * (3 - 2 * u)
    cy, r = 1300, 120
    panel(c, 140, cy - 210, W - 140, cy + 210, a)
    sep = 150 * (1 - u)
    for col, cx in ((skia.ColorSetARGB(255, 40, 95, 255), W / 2 - 60 - sep), (skia.ColorSetARGB(255, 255, 205, 30), W / 2 + 60 + sep)):
        p = skia.Paint(Color=col, AntiAlias=True, Alphaf=a)
        p.setBlendMode(skia.BlendMode.kPlus)
        c.drawCircle(cx, cy, r, p)
    f = font("Inter-700", 30)
    for s, x in (("BLUE", W / 2 - 60 - sep), ("YELLOW", W / 2 + 60 + sep)):
        c.drawString(s, x - f.measureText(s) / 2, cy + r + 50, f, paint(skia.ColorWHITE, a * (1 - u)))
    if u > 0.85:
        s = "WHITE"
        c.drawString(s, W / 2 - f.measureText(s) / 2, cy + r + 50, f, paint(skia.ColorWHITE, a * (u - 0.85) / 0.15))

def spectrum_card(c, t, t0, t1, t_red):
    a = min(1.0, (t - t0) / 0.2) * min(1.0, (t1 - t) / 0.15)
    x0, x1, y0, y1 = 120, W - 120, 1000, 1500
    panel(c, x0 - 30, y0 - 90, x1 + 30, y1 + 110, a)
    f, fs = font("Inter-700", 28), font("Inter-500", 24)
    c.drawString("LIGHT FROM A WHITE LED", x0, y0 - 40, f, paint(skia.ColorWHITE, a))
    def wl_color(nm):
        stops = [(400, (120, 60, 255)), (450, (40, 90, 255)), (490, (0, 200, 255)), (520, (40, 255, 90)),
                 (570, (240, 240, 40)), (600, (255, 170, 20)), (640, (255, 50, 20)), (700, (180, 0, 0))]
        for (n0, c0), (n1, c1) in zip(stops, stops[1:]):
            if nm <= n1:
                k = (nm - n0) / (n1 - n0)
                return tuple(int(c0[i] + (c1[i] - c0[i]) * k) for i in range(3))
        return stops[-1][1]
    def power(nm):   # schematic: a narrow blue spike from the chip and the broad yellow hump from the phosphor
        return math.exp(-((nm - 450) / 11) ** 2) + 0.62 * math.exp(-((nm - 565) / 48) ** 2)
    reveal = min(1.0, (t - t0 - 0.2) / 1.1)
    nm_max = 400 + 300 * max(0.0, reveal)
    for nm in range(400, int(nm_max)):
        x = x0 + (nm - 400) / 300 * (x1 - x0)
        h = power(nm) * (y1 - y0) * 0.92
        col = wl_color(nm)
        c.drawRect(skia.Rect(x, y1 - h, x + (x1 - x0) / 300 + 0.6, y1), skia.Paint(Color=skia.ColorSetARGB(255, *col), Alphaf=a))
    c.drawLine(x0, y1, x1, y1, skia.Paint(Color=skia.ColorWHITE, StrokeWidth=2, Alphaf=a))
    for nm in (400, 500, 600, 700):
        x = x0 + (nm - 400) / 300 * (x1 - x0)
        s = f"{nm} nm"
        c.drawString(s, min(x1 - fs.measureText(s), max(x0, x - fs.measureText(s) / 2)), y1 + 40, fs, paint(GRAY, a))
    if t >= t_red - 0.05:
        b = min(1.0, (t - t_red + 0.05) / 0.2) * a
        rx0 = x0 + (620 - 400) / 300 * (x1 - x0)
        c.drawRect(skia.Rect(rx0, y0, x1, y1), skia.Paint(Color=skia.ColorSetARGB(255, 255, 60, 40), Style=skia.Paint.kStroke_Style, StrokeWidth=3, Alphaf=b))
        s = "BARELY ANY RED"
        c.drawString(s, rx0 + ((x1 - rx0) - f.measureText(s)) / 2, y0 + 50, f, paint(skia.ColorSetARGB(255, 255, 90, 70), b))

def acdc_card(c, t, t_ac, t_dc, t1):
    a = min(1.0, (t - t_ac + 0.1) / 0.2) * min(1.0, (t1 - t) / 0.15)
    if a <= 0:
        return
    y, h = 1400, 150
    panel(c, 120, y - h - 60, W - 120, y + h + 90, a)
    f = font("Inter-700", 30)
    path = skia.Path()
    for i in range(201):
        x = 170 + i * 1.6
        yy = y - math.sin(i / 200 * 4 * math.pi + t * 6) * h * 0.7
        path.moveTo(x, yy) if i == 0 else path.lineTo(x, yy)
    c.drawPath(path, skia.Paint(Color=skia.ColorSetARGB(255, 255, 190, 60), Style=skia.Paint.kStroke_Style, StrokeWidth=5, AntiAlias=True, Alphaf=a))
    c.drawString("AC", 170 + 160 - f.measureText("AC") / 2, y + h + 50, f, paint(skia.ColorWHITE, a))
    c.drawString("→", W / 2 - 18, y + 12, font("Inter-700", 56), paint(skia.ColorWHITE, a))
    if t >= t_dc - 0.05:
        b = a * min(1.0, (t - t_dc + 0.05) / 0.2)
        c.drawLine(W - 170 - 320, y - h * 0.4, W - 170, y - h * 0.4, skia.Paint(Color=skia.ColorSetARGB(255, 90, 170, 255), StrokeWidth=6, AntiAlias=True, Alphaf=b))
        c.drawString("DC", W - 170 - 160 - f.measureText("DC") / 2, y + h + 50, f, paint(skia.ColorWHITE, b))

def counter(c, t, A, F, ramp, old_dies, t_thousand, t1):
    a = min(1.0, (t - ramp[0] + 0.1) / 0.2) * min(1.0, (t1 - t) / 0.15)
    if a <= 0:
        return
    u = min(1.0, max(0.0, (t - ramp[0]) / (ramp[1] - ramp[0])))
    hours = int(round(math.exp(u * math.log(50000)) / 10) * 10) if u > 0 else 0
    f, fm, fs = font("Inter-700", 64), font("Inter-700", 46), font("Inter-700", 24)
    def centered(s, x, y, fnt, col, al):
        w = fnt.measureText(s)
        c.drawString(s, max(40, min(x - w / 2, W - 40 - w)), y, fnt, paint(col, al))
    if A["led"][F]:
        x, y = A["led"][F]
        centered(" ".join("LED"), x, y + 120, fs, skia.ColorWHITE, a)
        centered(f"{hours:,} h", x, y + 200, f, skia.ColorWHITE, a)
    if A["old"][F]:
        x, y = A["old"][F]
        centered(" ".join("INCANDESCENT"), x, y + 120, fs, skia.ColorWHITE, a)
        if t >= old_dies:
            b = a * min(1.0, (t - old_dies) / 0.2)
            centered("1,000 h", x, y + 195, fm, skia.ColorSetARGB(255, 255, 120, 90), b)
            centered("burned out", x, y + 240, font("Inter-500", 26), GRAY, b)

def word_time(lines, li, word):
    return next(w["start"] for w in lines[li]["words"] if w["w"] == word)

def make_overlay(lines, shots, duration, ev, A):
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
            c.drawString(NOTES[name], 60, H - 330, font("Inter-500", 26), paint(skia.ColorSetARGB(255, 200, 200, 200), 0.75))
        if name == "macro_top":
            mix_card(c, t, s0 + 0.1, s1)
        if name == "spectrum":
            spectrum_card(c, t, s0, s1, word_time(lines, 6, "red"))
        if name == "driver":
            acdc_card(c, t, word_time(lines, 9, "AC"), word_time(lines, 9, "DC"), s1)
        if name == "versus":
            counter(c, t, A, F, ev["ramp"], ev["old_dies"], word_time(lines, 10, "1,000."), s1)
        captions(c, t, ch)
    return overlay

# ------------------------------------------------------------------ sound

SW = "InMotionAudio - USA Hotel/MECHClik_USALightSwitch_On05_InMotionAudio_USAHotel.wav"
WOOSH = "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav"
SNAP = "Cinematic Sound Design - Interface & Infographics/Interface Accept Glassy Snap.wav"
ZAP = "Epic Stock Media - Elemental Mutation Whooshes and Impacts/ELECMisc_Impact Electric Tonal Deep Movement Motion Hiss Glitch 01_ESM_EMWI.wav"

def build_audio(lines, shots, duration, ev, out_wav):
    track = np.zeros(int((duration + 1) * SR), np.float32)
    def add(t, x, gain):
        a = int(t * SR)
        x = x[: len(track) - a]
        track[a:a + len(x)] += x * gain
    v = narr = common_load(os.path.join(OUT, "narration.wav"))
    add(0.0, narr, 1.0)
    add(0.02, sfx.clip(SW, 0.0, 0.5), 0.35)
    for t, name in shots[1:]:
        add(max(0.0, t - 0.12), sfx.clip(WOOSH, 0.0, 0.6, lp=6000), 0.10)
    for name, wi in (("ring_blue", 0), ("macro_fill", 0), ("fins", 0), ("driver", 0), ("versus", 0)):
        s0 = next(t for t, n in shots if n == name)
        for key, text, delay, _ in LABELS.get(name, []):
            add(s0 + delay, sfx.clip(SNAP, 0.0, 0.4), 0.12)
    add(word_time(lines, 9, "AC") - 0.05, sfx.clip(ZAP, 0.0, 0.9, lp=7000), 0.14)
    add(ev["old_dies"], sfx.clip(SW, 0.0, 0.5, rate=0.8), 0.25)
    save_wav(track, out_wav, duration)

def common_load(path):
    import wave
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0

# ------------------------------------------------------------------ main

def main(out_mp4=None, out_wav=None, preview_times=None):
    common.FPS = FPS
    lines, shots, duration, ev = timeline()
    if out_mp4 is None and preview_times is None:
        for t, n in shots:
            print(f"{t:6.2f} {n}")
        print(f"duration {duration:.2f} s; old bulb dies at {ev['old_dies']:.2f}")
        return
    os.makedirs(FRAMES, exist_ok=True)
    n = int(round(duration * FPS))
    frames = sorted({min(n - 1, int(round(x * FPS))) for x in preview_times}) if preview_times else list(range(n))
    tj = os.path.join(OUT, "timing.json")
    json.dump({"fps": FPS, "duration": duration, "shots": shots, "events": {"old_dies": ev["old_dies"]}}, open(tj, "w"))
    t0 = time.time()
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "led_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    if not preview_times:
        build_audio(lines, shots, duration, ev, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots, duration, ev, A), out_mp4, out_wav, "led" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
