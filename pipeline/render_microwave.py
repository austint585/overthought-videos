"""'The dots on your microwave door': a voxel explainer. A kitchen microwave opened up: the magnetron, 12 cm waves bouncing
off the metal walls, water in the food shaking, the metal mesh in the door that bounces the waves back but lets light
through, and the two door switches. From Austin's DMs asking for more "how stuff people use daily works" episodes with a
strong hook (a @how_it_secretly_works reel, Oct 27); microwave door mesh was on the explainer backlog.

python render_microwave.py out.mp4 out.wav     full render (Blender frames are cached in out/microwave/frames)
python render_microwave.py preview 1.0,12.5    render and composite stills into preview/
python render_microwave.py times               narrate and print the event times

Facts (links in ops/episodes/2026-10-28-microwave-door.md): ovens run at 2,450 MHz (Health Physics Society), so a wave is
about 12 cm long (c / f); microwaves make the water in food vibrate, which is the heat (FDA); the door window has a metal
grid with small holes that light passes through but the microwaves don't (Health Physics Society), holes about 1 to 2 mm;
federal law requires two independent interlocks that stop the microwaves the moment the latch is released (FDA, 21 CFR
1030.10).
"""
import json, math, os, sys
import numpy as np
import skia
from common import *
import render_tap as tap
import kit3d as K

FPS = 60
TAIL = 1.4
SCRIPT = [
    ("A", "Those *dots* on your microwave door have *one job.*"),
    ("B", "Inside, a *magnetron* makes microwaves at *2,450{twenty-four fifty} megahertz.*"),
    ("C", "That makes each wave about *12{twelve} centimeters* long."),
    ("D", "They make the *water* in your food *shake,* and that's the *heat.*"),
    ("E", "The metal walls bounce them *back in.* But you want a *window.*"),
    ("F", "So the glass has a *metal sheet* with holes a *millimeter* or two wide."),
    ("G", "A *12{twelve}-centimeter* wave can't get through. It *bounces back.*"),
    ("H", "*Light* waves are *thousands* of times smaller than the holes, so they go *right through.*"),
    ("I", "And by law, *two* separate *switches* cut the power the second you open the door."),
    ("J", "So you get to *watch* your food cook, without *cooking* with it."),
]
EXTRA_GAP = {3: 0.1, 4: 0.1, 6: 0.1, 8: 0.15, 9: 0.25}
OUT = os.path.join(ROOT, "out", "microwave")
FRAMES = os.path.join(OUT, "frames")

def wn(sents, si, sub, nth=0):
    s = sents[si]
    hits = [i for i, w in enumerate(s["words"]) if sub.lower() in w["display"].lower()]
    return s["abs_starts"][hits[min(nth, len(hits) - 1)]] if hits else s["t0"]

def events(sents, speech_end):
    w = lambda si, sub, n=0: wn(sents, si, sub, n)
    s = lambda si: sents[si]["t0"]
    E = {k: s(i) for i, k in enumerate("ABCDEFGHIJ")}
    E.update({"dots": w(0, "dots"), "job": w(0, "job"), "magnetron": w(1, "magnetron"), "mhz": w(1, "megahertz"),
              "cm": w(2, "centimeters"), "water": w(3, "water"), "shake": w(3, "shake"), "heat": w(3, "heat"),
              "back": w(4, "back"), "window": w(4, "window"), "sheet": w(5, "sheet"), "mm": w(5, "millimeter"),
              "wave12": w(6, "12"), "bounces": w(6, "bounces"), "light": w(7, "Light"), "through": w(7, "through"),
              "two": w(8, "two"), "switches": w(8, "switches"), "open": w(8, "open"), "watch": w(9, "watch"),
              "cooking": w(9, "cooking"), "speech_end": speech_end})
    return E

# ------------------------------------------------------------------ sound (recorded effects from the Sonniss GDC 2026 bundle, see sfx.py)

F = {
    "beep": "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav",
    "pop": "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav",
    "perc": "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav",
    "swoosh": "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Pull Swoosh Readout.wav",
    "woosh": "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav",
    "kalimba": "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Kalimba 3 Up_CB Sounddesign_APPlicable Sounds.wav",
    "deny": "Cinematic Sound Design - System & UI Feedback Elements/Interface Deny Low Fat Dark.wav",
    "latch": "Epic Stock Media - HD Lock And Mechanism Sound Design Kit/MECHMisc_Tool Tape Measure Pull Retract Spring Slide Spin Long 07_ESM_HDLM.wav",
    "door": "InMotionAudio - USA Hotel/DOORMetl_StairWellDoor01_InMotionAudio_USAHotel.wav",
    "braam": "Jake Fielding - Cinematic Horn Braams/DSGNBram____Cinematic Horn Braam, Epic, Cinematic, Dark, Instrument, Huge-32.wav",
}

def build_audio(sents, E, duration, path):
    import sfx
    n = int(duration * SR)
    voice = K.voice_track(sents, duration)[:n]
    tr = new_track(duration)
    tr[:n] += voice           # no ambience bed and no oven hum: no steady tones (Austin, Oct 27)
    hit = lambda t0, key, gain, **kw: add(tr, t0, sfx.clip(F[key], **kw), gain)
    hit(0.0, "braam", 0.10, lp=2500)
    hit(E["dots"], "pop", 0.18)
    hit(E["magnetron"], "woosh", 0.14)
    hit(E["cm"], "perc", 0.16)
    hit(E["shake"], "kalimba", 0.14, rate=1.2)
    hit(E["back"], "perc", 0.14, rate=0.9)
    hit(E["sheet"], "swoosh", 0.14)
    hit(E["bounces"], "deny", 0.16, rate=1.1)
    hit(E["through"], "kalimba", 0.16)
    hit(E["open"] - 0.05, "latch", 0.14, dur=0.6, hp=200)
    hit(E["open"] + 0.15, "deny", 0.16, rate=0.8)
    for k in range(3):                          # the end-of-cook beeps
        hit(E["J"] - 0.6 + 0.22 * k, "beep", 0.16, rate=1.4)
    save_wav(tr, path, duration)

def remux(mp4, wav):
    import subprocess
    tmp = mp4 + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", tmp], check=True)
    os.replace(tmp, mp4)

# ------------------------------------------------------------------ overlay

GOLD = skia.Color(255, 205, 60)
BLUE = skia.Color(110, 170, 255)
GREEN = skia.Color(120, 220, 120)
CARD = skia.ColorSetARGB(215, 12, 13, 18)

def smooth01(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

def draw_hook(c, a):
    if a <= 0:
        return
    y = 290
    for s, k in (("The dots on your", False), ("microwave door", True)):
        ff = font("Bricolage-800", 92)
        wd = ff.measureText(s) + (40 if k else 0)
        x = W / 2 - wd / 2
        if k:
            c.drawRRect(tap.rrect(x, y - 80, x + wd, y + 26, 16), paint(ORANGE, a))
            c.drawString(s, x + 20, y, ff, paint(tap.PANEL2, a))
        else:
            c.drawString(s, x, y, ff, paint(INK, a))
        y += 116

def pill(c, text, cx, y, a, color=INK, bg=K.DARK_PILL, size=34):
    if a <= 0:
        return
    f = font("JetBrainsMono-700", size)
    w = f.measureText(text)
    c.drawRRect(tap.rrect(cx - w / 2 - 22, y - size - 10, cx + w / 2 + 22, y + 16, 14), paint(bg, a))
    c.drawString(text, cx - w / 2, y, f, paint(color, a))

def rows_card(c, t, rows, y0, a, source=None):
    if a <= 0:
        return
    x0, x1 = 60, 920                 # clear of the Reels buttons on the right edge
    c.drawRRect(tap.rrect(x0, y0, x1, y0 + 60 + 74 * len(rows), 20), paint(CARD, a))
    f1, f2 = font("JetBrainsMono-700", 30), font("Bricolage-800", 44)
    for k, (h, v, t0, col) in enumerate(rows):
        b = a * smooth01((t - t0) / 0.25)
        if b <= 0:
            continue
        y = y0 + 80 + 74 * k
        c.drawString(h, x0 + 28, y, f1, paint(MUTED, b))
        c.drawString(v, x1 - 24 - f2.measureText(v), y + 4, f2, paint(col, b))
    if source:
        text_center(c, source, W / 2, 1525, font("JetBrainsMono-500", 22), paint(MUTED, 0.9 * a))

def draw_ruler(c, t, E):
    """The 12 cm wavelength drawn as a sine with a bracket, next to a 1 mm hole for scale."""
    a = K.fade(t, E["C"] - 0.1, E["D"] - 0.1, 0.25)
    if a <= 0:
        return
    x0, x1, y = 120, 960, 1130
    c.drawRRect(tap.rrect(70, 980, 1010, 1330, 20), paint(CARD, a))
    path = skia.Path()
    for k in range(121):
        u = k / 120
        px = x0 + (x1 - x0) * u
        py = y - 70 * math.sin(2 * math.pi * u + t * 4)
        path.moveTo(px, py) if k == 0 else path.lineTo(px, py)
    c.drawPath(path, tap.stroke(ORANGE, 8, a))
    b = a * smooth01((t - E["cm"] + 0.1) / 0.25)
    c.drawLine(x0, y + 110, x1, y + 110, tap.stroke(INK, 4, b))
    c.drawLine(x0, y + 95, x0, y + 125, tap.stroke(INK, 4, b))
    c.drawLine(x1, y + 95, x1, y + 125, tap.stroke(INK, 4, b))
    text_center(c, "one wave: about 12 cm", W / 2, y + 170, font("Bricolage-800", 44), paint(GOLD, b))
    text_center(c, "2,450 MHz  .  speed of light / 2.45 GHz = 12.2 cm", W / 2, 1525, font("JetBrainsMono-500", 22),
                paint(MUTED, 0.9 * a))

def draw_holes(c, t, E):
    a = K.fade(t, E["mm"] - 0.1, E["H"] - 0.1, 0.25)
    rows_card(c, t, [("HOLE", "1 to 2 mm", E["mm"] - 0.05, INK), ("MICROWAVE", "about 120 mm", E["wave12"] - 0.05, ORANGE),
                     ("RESULT", "bounces back", E["bounces"] - 0.05, tap.RED)], 1210, a)

def draw_light(c, t, E):
    a = K.fade(t, E["H"] - 0.1, E["I"] - 0.1, 0.25)
    rows_card(c, t, [("HOLE", "1 to 2 mm", E["light"] - 0.1, INK), ("LIGHT WAVE", "0.0004 to 0.0007 mm", E["light"] + 0.2, GOLD),
                     ("RESULT", "goes through", E["through"] - 0.05, GREEN)], 1210, a,
              "Sources: Health Physics Society; FDA microwave oven page")

def draw_law(c, t, E):
    a = K.fade(t, E["I"] - 0.1, E["J"] - 0.1, 0.25)
    rows_card(c, t, [("DOOR SWITCHES", "2, independent", E["two"] - 0.05, GOLD),
                     ("DOOR OPENS", "microwaves stop", E["open"] - 0.05, GREEN)], 1300, a,
              "Source: FDA, federal standard 21 CFR 1030.10")

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, K.fade(t, -1, E["B"] - 0.05, 0.2))
    tap.draw_captions(c, t, sents, cm)
    c.restore()
    lab = font("JetBrainsMono-700", 30)
    tags = [
        ("door", "METAL MESH", E["job"] - 0.05, E["B"] - 0.1, 120, 230, GOLD),
        ("mag", "MAGNETRON", E["magnetron"] - 0.05, E["C"] - 0.1, 60, -200, ORANGE),
        ("food", "WATER: SHAKING", E["shake"] - 0.05, E["E"] - 0.1, -120, -200, ORANGE),
        ("wall", "METAL WALL", E["back"] - 0.1, E["F"] - 0.1, -60, -180, GOLD),
        ("door", "MESH (HOLES ENLARGED)", E["sheet"] - 0.05, E["I"] - 0.1, 120, -230, GOLD),
        ("sw1", "SWITCH 1", E["switches"] - 0.1, E["J"] - 0.1, -170, -150, tap.RED),
        ("sw2", "SWITCH 2", E["switches"] + 0.1, E["J"] - 0.1, -170, 120, tap.RED),
        ("guy", "WATCHING, NOT COOKING", E["watch"] - 0.05, speech_end + 1.0, 120, -150, GREEN),
    ]
    for name, text, t0, t1, dx, dy, col in tags:
        a = K.fade(t, t0, t1, 0.2)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, col, lab)
    pill(c, "2,450 MHz", W / 2, 1440, K.fade(t, E["mhz"] - 0.05, E["C"] - 0.1, 0.15), ORANGE)
    draw_ruler(c, t, E)
    pill(c, "WAVES: BOUNCING", W / 2, 1440, K.fade(t, E["back"] - 0.05, E["F"] - 0.1, 0.15), ORANGE)
    draw_holes(c, t, E)
    draw_light(c, t, E)
    draw_law(c, t, E)
    if t > speech_end + 0.1:
        a = smooth01((t - speech_end - 0.1) / 0.4)
        text_center(c, "@overthought.daily", W / 2, 1530, font("JetBrainsMono-500", 32), paint(MUTED, a))

# ------------------------------------------------------------------ main

def setup():
    sents, speech_end = K.narrate(SCRIPT, OUT, EXTRA_GAP)
    duration = speech_end + TAIL
    return sents, speech_end, duration, events(sents, speech_end)

def main(out_mp4, out_wav, preview_times=None):
    sents, speech_end, duration, E = setup()
    n_frames = int(round(duration * FPS))
    print(f"duration {duration:.1f}s, {n_frames} frames", flush=True)
    frames = sorted({min(n_frames - 1, int(round(x * FPS))) for x in preview_times}) if preview_times else range(n_frames)
    K.run_blender("microwave_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0]
    if not preview_times:
        build_audio(sents, E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "microwave" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "times":
        sents, speech_end, duration, E = setup()
        print(json.dumps({k: round(v, 2) for k, v in E.items()}, indent=1))
        print("duration", round(duration, 2))
    elif sys.argv[1] == "audio":
        sents, speech_end, duration, E = setup()
        build_audio(sents, E, duration, sys.argv[3])
        remux(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "preview":
        main(None, None, preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
