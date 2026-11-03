"""Episode: Your AI picture did not drink a bottle of water (ops/episodes/2026-11-02-ai-water-bottle.md). Pastel toy kit
(water_scene.py), yelled Chatterbox narration, the look Austin OK'd on the Nov 2 test.

python render_water.py layout 1.0,5.5        stills with estimated timing and no voice
python render_water.py narrate               voice the script (out/water/voice, out/water/narration.json), print the timing
python render_water.py preview 1.0,5.5       stills with the real timing into preview/water_*.png
python render_water.py out.mp4 out.wav       full render (Blender frames cached in out/water/frames)
"""
import json, math, os, subprocess, sys, time
import numpy as np
import skia
import soundfile as sf
import common
from common import *
import kit3d as K
import sfx

FPS = 30
OUT = os.path.join(ROOT, "out", "water")
FRAMES = os.path.join(OUT, "frames")
TAIL = 0.45
# (line, [(shot, word index the shot starts on), ...]); *word* is boxed, a{b} is shown a / spoken b
SCRIPT = [
    ("That AI picture you just scrolled past did not drink a whole *bottle* of water!", [("hook", 0)]),
    # one sentence in the script, voiced in three: Chatterbox trailed off into nonsense at the end of the long take
    ("The bottle comes from a 2023{twenty twenty three} paper about text answers!", [("paper", 0)]),
    ("and it says one bottle for *10* *to* *50* answers.", [("cups", 0)]),
    ("It has no number for pictures!", [("nopic", 0)]),
    ("Nobody has measured one picture directly. Do the math, power plant included, and you get about *12* milliliters!", [("measure", 0), ("drops", 6)]),
    ("The highest number we could find is *29.* That's two tablespoons!", [("spoons", 0)]),
    ("One flush of your toilet is *6* *liters.* That's 200 AI pictures, gone!", [("flush", 0)]),
    ("But if your friend says it's all a *closed* *loop,* your friend is wrong too!", [("loop", 0)]),
    ("Lots of data centers *evaporate* water on purpose. Google loses about 80 percent of the water it takes in!", [("tower", 0)]),
    ("Microsoft's no-water{no water} sites start coming online in *late* *2027,* and they use more electricity!", [("micro", 0), ("meter", 9)]),
    ("And in one estimate, most of the water isn't at the data center. It's at the *power* *plant!*", [("dc", 0), ("plant", 13)]),
    ("Your one picture is nothing. The town next to a *giant* data center still has a real question!", [("nothing", 0), ("town", 5)]),
    ("But no, that picture did not drink a bottle of water!", [("hook_out", 0)]),
]
LINES = [l for l, _ in SCRIPT]
NOTES = {"cups": "The paper: GPT-3, medium-length answers",
         "drops": "Our math: 2.9 Wh a picture x 4.25 L per kWh",
         "spoons": "UN University report, June 2026",
         "flush": "Using the high estimate, 29 mL a picture",
         "meter": "Microsoft calls the increase nominal",
         "dc": "One estimate: GPT-3 in 2023, average US data center",
         "plant": "One estimate: GPT-3 in 2023, average US data center"}
NOTE_Y = {"flush": 788}
PILL = skia.ColorSetARGB(225, 28, 33, 41)
KEY = skia.ColorSetARGB(255, 255, 106, 43)

FLUSH = "InMotionAudio - USA Hotel/WATRPlmb_ToiletFlush01_InMotionAudio_USAHotel.wav"
CLICK = "InMotionAudio - USA Hotel/MECHClik_USALightSwitch_On05_InMotionAudio_USAHotel.wav"
SPLASH = "344 Audio - Elemental Palette Designed Vol. 1/WATRMisc_Water, Liquid Impact, Bubble, Sci Fi, Hit 04_344 Audio_Elemental Palette Designed Vol 1.wav"
WOOSH = "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav"
HIT = "Cinematic Sound Design - Cartoon Impacts/Cartoon Pops Random Sequence Reverb.wav"
SNAP = "Cinematic Sound Design - Interface & Infographics/Interface Accept Glassy Snap.wav"

# ------------------------------------------------------------------ textures

def rgba_save(arr, path):
    skia.Image.fromarray(arr, colorType=skia.ColorType.kRGBA_8888_ColorType).save(path, skia.kPNG)

def picture(path):
    """Our joke AI picture: a too-perfect sunset and a waving hand with six fingers."""
    s = skia.Surface(800, 1000)
    c = s.getCanvas()
    sky = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, 720)],
                                         [skia.ColorSetRGB(92, 92, 190), skia.ColorSetRGB(246, 120, 140), skia.ColorSetRGB(255, 205, 120)], [0, 0.6, 1])
    c.drawRect(skia.Rect(0, 0, 800, 1000), skia.Paint(Shader=sky))
    c.drawCircle(400, 640, 170, skia.Paint(Color=skia.ColorSetRGB(255, 236, 170), AntiAlias=True))
    for col, y0, amp, ph in ((skia.ColorSetRGB(112, 84, 160), 690, 60, 0.4), (skia.ColorSetRGB(74, 66, 130), 780, 45, 2.0)):
        p = skia.Path()
        p.moveTo(0, 1000)
        for x in range(0, 801, 10):
            p.lineTo(x, y0 + amp * math.sin(x / 140 + ph))
        p.lineTo(800, 1000)
        p.close()
        c.drawPath(p, skia.Paint(Color=col, AntiAlias=True))
    skin = skia.ColorSetRGB(245, 190, 150)
    for i in range(6):                 # six fingers
        a = math.radians(-70 + i * 28)
        x, y = 400 + 110 * math.sin(a), 640 - 110 * math.cos(a)
        c.drawLine(x, y, x + 150 * math.sin(a), y - 150 * math.cos(a), skia.Paint(Color=skin, StrokeWidth=58, StrokeCap=skia.Paint.kRound_Cap, AntiAlias=True))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(285, 590, 515, 830), 100, 100), skia.Paint(Color=skin, AntiAlias=True))
    c.drawRect(skia.Rect(345, 780, 455, 1000), skia.Paint(Color=skin, AntiAlias=True))
    s.makeImageSnapshot().save(path, skia.kPNG)

def label(path):
    s = skia.Surface(2048, 340)
    c = s.getCanvas()
    c.clear(skia.ColorSetRGB(46, 127, 208))
    c.drawRect(skia.Rect(0, 0, 2048, 40), skia.Paint(Color=skia.ColorSetRGB(240, 248, 255)))
    c.drawRect(skia.Rect(0, 300, 2048, 340), skia.Paint(Color=skia.ColorSetRGB(240, 248, 255)))
    for cx in (512, 1536):
        f = font("Inter-700", 118)
        t = "500 mL"
        c.drawString(t, cx - f.measureText(t) / 2, 214, f, paint(skia.ColorWHITE, 1.0))
    s.makeImageSnapshot().save(path, skia.kPNG)

def swirl(path):
    n = 1024
    yy, xx = np.mgrid[0:n, 0:n]
    x, y = (xx - n / 2) / (n / 2), (yy - n / 2) / (n / 2)
    r, th = np.sqrt(x * x + y * y), np.arctan2(y, x)
    arms = 0.5 + 0.5 * np.sin(5 * th + 11 * r)
    arms = np.clip((arms - 0.45) * 3.5, 0, 1)[..., None]
    dark = np.array([64, 165, 222], np.float32) * (0.72 + 0.28 * np.clip(r, 0, 1))[..., None]
    img = dark * (1 - arms) + np.array([196, 236, 250], np.float32) * arms
    rgba = np.dstack([img.astype(np.uint8), np.full((n, n), 255, np.uint8)])
    rgba_save(rgba, path)

def paper(path):
    """The sheet on the clipboard: the paper's real title and date, the rest just gray lines."""
    s = skia.Surface(800, 1040)
    c = s.getCanvas()
    c.clear(skia.ColorSetRGB(252, 251, 247))
    ink = skia.ColorSetRGB(40, 44, 52)
    c.drawString("Making AI", 70, 130, font("Inter-700", 84), paint(ink, 1.0))
    c.drawString("Less Thirsty", 70, 225, font("Inter-700", 84), paint(ink, 1.0))
    c.drawString("2023", 70, 300, font("Inter-500", 46), paint(skia.ColorSetRGB(110, 114, 122), 1.0))
    r = np.random.RandomState(4)
    y = 370
    while y < 980:
        w = 660 if r.rand() > 0.2 else 400
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(70, y, 70 + w, y + 20), 8, 8), skia.Paint(Color=skia.ColorSetRGB(198, 200, 204), AntiAlias=True))
        y += 50
    s.makeImageSnapshot().save(path, skia.kPNG)

def textures():
    d = os.path.join(OUT, "tex")
    os.makedirs(d, exist_ok=True)
    out = {k: os.path.join(d, k + ".png") for k in ("picture", "label", "swirl", "paper")}
    picture(out["picture"]); label(out["label"]); swirl(out["swirl"]); paper(out["paper"])
    return out

# ------------------------------------------------------------------ timing

def estimated():
    """Word times with no voice, for looking at the sets before the narration exists."""
    from narrate_cb import caption_words
    out, t = [], 0.25
    for line in LINES:
        L = {"text": line, "start": t, "words": []}
        for w in caption_words(line):
            w.pop("say")
            w["start"], w["end"] = t, t + 0.25
            t += 0.25
            L["words"].append(w)
        L["end"] = t
        t += 0.16
        out.append(L)
    return out

def timeline(lines):
    def wt(li, word):
        return next(w for w in lines[li]["words"] if w["w"].rstrip(".,!?") == word)
    shots = []
    for (_, plan), L in zip(SCRIPT, lines):
        for name, wi in plan:
            t = L["words"][wi]["start"] - 0.08 if wi else L["start"] - 0.08
            shots.append([0.0 if not shots else round(t, 3), name])
    ev = {"not": wt(0, "not")["start"], "press": wt(6, "flush")["start"], "count0": wt(6, "That's")["start"] - 0.1, "count1": wt(6, "gone")["end"] - 0.05,
          "cups0": wt(2, "one")["start"], "cups1": wt(2, "50")["end"], "drops0": wt(4, "Do")["start"], "drops1": wt(4, "12")["end"],
          "wrong": wt(7, "wrong")["start"], "lose0": wt(8, "Google")["start"], "lose1": wt(8, "80")["end"], "elec": wt(9, "electricity")["start"],
          "not2": wt(12, "not")["start"]}
    return shots, ev, lines[-1]["end"] + TAIL

def shot_at(shots, t):
    return max([0] + [i for i, (s, _) in enumerate(shots) if t >= s])

# ------------------------------------------------------------------ overlay

def chunks(lines):
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
    f = font("Inter-700", 64)
    for i, cw in enumerate(ch):
        t0 = cw[0]["start"] - 0.03
        t1 = ch[i + 1][0]["start"] - 0.03 if i + 1 < len(ch) else cw[-1]["end"] + 0.5
        if not (t0 <= t < t1):
            continue
        shown = [w for w in cw if w["start"] - 0.03 <= t]
        widths = [f.measureText(w["w"] + " ") for w in shown]
        total = sum(widths) - f.measureText(" ")
        x, y = (W - total) / 2, 280
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 30, y - 66, x + total + 30, y + 26), 26, 26), skia.Paint(Color=PILL, AntiAlias=True))
        for w, wd in zip(shown, widths):
            if w["key"]:
                tw = f.measureText(w["w"])
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 10, y - 56, x + tw + 10, y + 16), 12, 12), skia.Paint(Color=KEY, AntiAlias=True))
            c.drawString(w["w"], x, y, f, paint(skia.ColorWHITE, 1.0))
            x += wd

def make_overlay(lines, shots):
    ch = chunks(lines)
    def overlay(c, t, F):
        name = shots[shot_at(shots, t)][1]
        if name in NOTES:
            fn = font("Inter-700", 28)
            s, y = NOTES[name], NOTE_Y.get(name, 1532)
            w = fn.measureText(s)
            if name != "flush":
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect((W - w) / 2 - 18, y - 32, (W + w) / 2 + 18, y + 12), 14, 14), skia.Paint(Color=skia.ColorSetARGB(170, 255, 255, 255), AntiAlias=True))
            text_center(c, s, W / 2, y, fn, paint(skia.ColorSetARGB(255, 40, 62, 58), 0.95))
        captions(c, t, ch)
    return overlay

# ------------------------------------------------------------------ sound

def build_audio(lines, shots, ev, duration, out_wav):
    from narrate_cb import load_pcm
    track = np.zeros(int((duration + 1) * SR), np.float32)
    def add(t, x, gain):
        a = int(t * SR)
        x = x[: len(track) - a]
        track[a:a + len(x)] += x * gain
    add(0.0, load_pcm(os.path.join(OUT, "narration.wav")), 1.0)
    for t, _ in shots[1:]:
        add(max(0.0, t - 0.12), sfx.clip(WOOSH, 0.0, 0.5, lp=6000), 0.08)
    for k in ("not", "wrong", "not2"):
        add(ev[k] - 0.01, sfx.clip(HIT, 0.0, 0.35), 0.20)
    add(ev["not"] + 0.02, sfx.clip(SPLASH, 0.0, 0.6, lp=7000), 0.12)
    add(ev["not2"] + 0.02, sfx.clip(SPLASH, 0.0, 0.6, lp=7000), 0.12)
    start = {n: t for t, n in shots}
    i1 = shot_at(shots, ev["press"]) + 1
    flush_end = shots[i1][0] if i1 < len(shots) else duration
    add(ev["press"] - 0.02, sfx.clip(CLICK, 0.0, 0.4), 0.28)
    add(ev["press"] + 0.05, sfx.clip(FLUSH, 0.0, flush_end - ev["press"], fade=0.2), 0.18)
    n = 7
    for i in range(n):                                     # a plink per few cups, then the dropper
        add(ev["cups0"] + (ev["cups1"] - ev["cups0"]) * i / n, sfx.clip(SNAP, 0.0, 0.3), 0.07)
        add(ev["drops0"] + (ev["drops1"] - ev["drops0"]) * i / n, sfx.clip(SPLASH, 0.0, 0.25, lp=6000, rate=1.3), 0.07)
    add(start["spoons"] + 0.15, sfx.clip(SNAP, 0.0, 0.3), 0.1)
    add(start["town"] + 0.1, sfx.clip(WOOSH, 0.0, 0.5, lp=3000), 0.1)
    save_wav(track, out_wav, duration)
    x, sr = sf.read(out_wav)
    sf.write(out_wav, x * 0.74, sr, subtype="PCM_16")      # save_wav normalizes the peak, and the yelled voice lands near -10.5 LUFS; -13 is the target

# ------------------------------------------------------------------ main

def main(mode, a=None, b=None):
    common.FPS = FPS
    os.makedirs(FRAMES, exist_ok=True)
    if mode == "layout":
        lines = estimated()
    else:
        from narrate_cb import narrate
        cache = os.path.join(OUT, "narration.json")
        old = json.load(open(cache)) if os.path.exists(cache) else None
        lines = old if old and [L["text"] for L in old] == LINES else narrate(LINES, OUT, exaggeration=1.6, cfg=0.25)
    shots, ev, duration = timeline(lines)
    if mode == "narrate":
        print(shots, f"duration {duration:.2f} s")
        for L in lines:
            print(L.get("match"), L["text"])
        return
    n = int(round(duration * FPS))
    still = mode in ("layout", "preview")
    frames = sorted({min(n - 1, int(round(float(x) * FPS))) for x in a.split(",")}) if still else list(range(n))
    tj = os.path.join(OUT, "timing.json")
    json.dump({"fps": FPS, "duration": duration, "shots": shots, "events": {k: float(v) for k, v in ev.items()}, "textures": textures(),
               "font": os.path.join(ROOT, "vendor", "fonts", "Inter-700.ttf")}, open(tj, "w"))
    t0 = time.time()
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "water_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if still else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not still:
        build_audio(lines, shots, ev, duration, b)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots), None if still else a, None if still else b, "water" if still else None)

if __name__ == "__main__":
    if sys.argv[1] in ("layout", "preview", "narrate"):
        main(*sys.argv[1:])
    else:
        main("full", sys.argv[1], sys.argv[2])
