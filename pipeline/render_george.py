"""'Curious George learns about hypergamy': a deadpan voxel explainer in the roommate's apartment, with a height chart,
a tier list and a real height study. From Austin's DM (a @larpforlarp reel, Oct 27); our own script.

python render_george.py out.mp4 out.wav     full render (Blender frames are cached in out/george/frames; delete them to re-render)
python render_george.py preview 1.0,12.5    render and composite stills into preview/
python render_george.py times               narrate and print the event times
python render_george.py audio out.mp4 out.wav  rebuild only the soundtrack and swap it into an existing render

Facts: the first Curious George book came out in 1941 (https://en.wikipedia.org/wiki/Curious_George). George is drawn with
no tail; apes have none and most monkeys do (https://www.poweredbyosteons.org/2013/06/is-curious-george-monkey-or-ape.html).
Gillis and Avis (1980), "The male-taller norm in mate selection": the woman was taller in 1 of 720 couples.
Tier ranks and the heights in the scene are the joke and the drawing, not measurements.
"""
import json, math, os, sys
import numpy as np
import skia
from common import *
import render_tap as tap
import kit3d as K

FPS = 60
TAIL = 1.6
SCRIPT = [
    ("A", "What happens when *Curious George* learns about *hypergamy?*"),
    ("B", "Hard case. George is a *monkey.*"),
    ("C", "Except he has *no tail,* so technically he's an *ape.* Mislabeled since *1941{nineteen forty-one}.*"),
    ("D", "By the books, he's a *mid-tier* primate. No job. No car. Lives with his *roommate.*"),
    ("E", "He also comes up to the roommate's *belt.* *Not ideal.*"),
    ("F", "Because the roommate is the *Chad in the yellow hat.* *Tall,* plus the *hat.*"),
    ("G", "George is getting *height-mogged* at *home.*"),
    ("H", "In a *1980{nineteen eighty}* study of *720{seven hundred twenty}* couples, the woman was taller in *one.*"),
    ("I", "So once George learns about *hypergamy,* it's *over.*"),
    ("J", "The Chad in the yellow hat? *Ascending.*"),
    ("K", "Peer review is *pending.*"),
]
EXTRA_GAP = {1: 0.1, 4: 0.1, 6: 0.1, 7: 0.15, 8: 0.2, 9: 0.15, 10: 0.3}
OUT = os.path.join(ROOT, "out", "george")
FRAMES = os.path.join(OUT, "frames")
WALK_LEN = 3.5          # door -> beside George (scene units)

def wn(sents, si, sub, nth=0):
    s = sents[si]
    hits = [i for i, w in enumerate(s["words"]) if sub.lower() in w["display"].lower()]
    return s["abs_starts"][hits[min(nth, len(hits) - 1)]] if hits else s["t0"]

def events(sents, speech_end):
    w = lambda si, sub, n=0: wn(sents, si, sub, n)
    s = lambda si: sents[si]["t0"]
    E = {k: s(i) for i, k in enumerate("ABCDEFGHIJK")}
    E.update({"monkey": w(1, "monkey"), "tail": w(2, "tail"), "ape": w(2, "ape"), "1941": w(2, "1941"),
              "mid": w(3, "mid"), "job": w(3, "job"), "car": w(3, "car"), "roommate": w(3, "roommate"),
              "belt": w(4, "belt"), "ideal": w(4, "ideal"), "chad": w(5, "Chad"), "tall": w(5, "Tall"),
              "hat": w(5, "hat", 1), "mogged": w(6, "mogged"), "home": w(6, "home"), "1980": w(7, "1980"),
              "720": w(7, "720"), "one": w(7, "one"), "hyper2": w(8, "hypergamy"), "over": w(8, "over"),
              "ascending": w(9, "Ascending"), "pending": w(10, "pending"), "speech_end": speech_end})
    E["walk0"] = E["D"] + 0.8
    E["walk1"] = max(E["walk0"] + 1.8, E["E"] - 0.25)
    return E

# ------------------------------------------------------------------ sound (recorded effects from the Sonniss GDC 2026 bundle, see sfx.py)

F = {
    "rain": "Jake Fielding - Interior Wind Rain and Storms/RAINInt_Heavy Rain on Window,  Constant _JF_INT Storm.wav",
    "thunder": "Jake Fielding - Interior Wind Rain and Storms/THUN_Interior Thunder Rumble_JF_INT Storm_01.wav",
    "tape": "Epic Stock Media - HD Lock And Mechanism Sound Design Kit/MECHMisc_Tool Tape Measure Pull Retract Spring Slide Spin Long 07_ESM_HDLM.wav",
    "door": "InMotionAudio - USA Hotel/DOORMetl_StairWellDoor01_InMotionAudio_USAHotel.wav",
    "steps": "TheWorkRoom - Flip Flops/FFG002.wav",
    "swoosh": "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Pull Swoosh Readout.wav",
    "woosh": "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav",
    "pop": "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav",
    "perc": "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav",
    "kalimba": "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Kalimba 3 Up_CB Sounddesign_APPlicable Sounds.wav",
    "deny": "Cinematic Sound Design - System & UI Feedback Elements/Interface Deny Low Fat Dark.wav",
    "powerup": "Epic Stock Media - Anime Game/DSGNStngr_Power Up Bright Positive Successful Light Saturation Crash Shimmer 05_ESM_AG.wav",
    "bass": "344 Audio - Bass Drops & Downers Vol. 1/DSGNBass_Bass Drop & Downer Fast 16_344 Audio_Bass Drops & Downers.wav",
    "braam": "Jake Fielding - Cinematic Horn Braams/DSGNBram____Cinematic Horn Braam, Epic, Cinematic, Dark, Instrument, Huge-32.wav",
}

def build_audio(sents, E, duration, path):
    import sfx
    n = int(duration * SR)
    voice = K.voice_track(sents, duration)[:n]
    tt = np.arange(n) / SR
    rain_on = np.clip((tt - (E["I"] - 0.3)) / 0.8, 0, 1)
    beds = sfx.bed(F["rain"], duration, 0.05, lp=5000) * rain_on    # no electric hum bed: it read as a buzz (Austin, Oct 27)
    env = np.sqrt(np.convolve(voice ** 2, np.ones(2400) / 2400, "same"))
    beds *= 1 - 0.4 * np.clip(env / 0.08, 0, 1)
    tr = new_track(duration)
    tr[:n] += voice + beds
    hit = lambda t0, key, gain, **kw: add(tr, t0, sfx.clip(F[key], **kw), gain)
    hit(0.0, "bass", 0.1, lp=2500)
    hit(E["monkey"], "pop", 0.18)
    hit(E["tail"], "deny", 0.26)
    hit(E["ape"], "perc", 0.2)
    hit(E["1941"], "kalimba", 0.18, rate=0.9)
    hit(E["D"] - 0.2, "woosh", 0.18)
    hit(E["mid"] + 0.15, "swoosh", 0.16, rate=1.1)
    hit(E["job"], "deny", 0.2, rate=1.1)
    hit(E["car"], "deny", 0.2, rate=0.95)
    hit(E["walk0"] - 0.35, "door", 0.28, lp=5000)
    steps = sfx.onsets(F["steps"], 0.25, 10)
    t, k = E["walk0"], 0
    while t < E["walk1"]:
        hit(t, "steps", 0.15, start=steps[k % len(steps)], dur=0.2, lp=2500, hp=90)
        t += 0.36
        k += 1
    hit(E["E"] - 0.1, "tape", 0.22, dur=1.2)
    hit(E["ideal"], "deny", 0.22, rate=0.8)
    hit(E["chad"], "kalimba", 0.2)
    hit(E["hat"] - 0.25, "swoosh", 0.2)
    hit(E["hat"] + 0.1, "pop", 0.2, rate=0.85)
    hit(E["mogged"], "bass", 0.24, lp=3000)
    hit(E["H"] - 0.25, "woosh", 0.16, rate=1.1)
    hit(E["one"] + 0.1, "pop", 0.2, rate=1.2)
    hit(E["over"] - 0.05, "thunder", 0.3, lp=4000)
    hit(E["ascending"], "powerup", 0.36)
    hit(E["J"] - 0.2, "braam", 0.12, lp=2500)
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

def smooth01(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

def draw_hook(c, a):
    if a <= 0:
        return
    y = 290
    for s, k in (("Curious George learns", False), ("about hypergamy", True)):
        size = 88
        ff = font("Bricolage-800", size)
        wd = ff.measureText(s) + (40 if k else 0)
        while wd > 980:
            size -= 4
            ff = font("Bricolage-800", size)
            wd = ff.measureText(s) + (40 if k else 0)
        x = W / 2 - wd / 2
        if k:
            c.drawRRect(tap.rrect(x, y - 76, x + wd, y + 24, 16), paint(ORANGE, a))
            c.drawString(s, x + 20, y, ff, paint(tap.PANEL2, a))
        else:
            c.drawString(s, x, y, ff, paint(INK, a))
        y += 108

def pill(c, text, cx, y, a, color=INK, bg=K.DARK_PILL, size=34):
    if a <= 0:
        return
    f = font("JetBrainsMono-700", size)
    w = f.measureText(text)
    c.drawRRect(tap.rrect(cx - w / 2 - 22, y - size - 10, cx + w / 2 + 22, y + 16, 14), paint(bg, a))
    c.drawString(text, cx - w / 2, y, f, paint(color, a))

TIERS = [("S", skia.Color(240, 90, 90), "SILVERBACK"), ("A", skia.Color(250, 160, 80), "ORANGUTAN"),
         ("B", skia.Color(250, 215, 90), None), ("C", skia.Color(150, 220, 110), "LEMUR"),
         ("D", skia.Color(110, 170, 255), "SEA MONKEYS")]

def george_chip(c, x, y, s, a):
    """A tiny George face: brown square, tan face, ears."""
    c.drawRect(skia.Rect(x - 0.62 * s, y - 0.2 * s, x - 0.42 * s, y + 0.12 * s), paint(skia.Color(222, 180, 130), a))
    c.drawRect(skia.Rect(x + 0.42 * s, y - 0.2 * s, x + 0.62 * s, y + 0.12 * s), paint(skia.Color(222, 180, 130), a))
    c.drawRRect(tap.rrect(x - 0.45 * s, y - 0.5 * s, x + 0.45 * s, y + 0.45 * s, 0.08 * s), paint(skia.Color(110, 66, 34), a))
    c.drawRRect(tap.rrect(x - 0.32 * s, y - 0.25 * s, x + 0.32 * s, y + 0.38 * s, 0.1 * s), paint(skia.Color(232, 192, 142), a))
    for dx in (-0.14, 0.14):
        c.drawRect(skia.Rect(x + dx * s - 0.05 * s, y - 0.12 * s, x + dx * s + 0.05 * s, y - 0.02 * s), paint(skia.Color(20, 14, 10), a))
    c.drawRect(skia.Rect(x - 0.12 * s, y + 0.18 * s, x + 0.12 * s, y + 0.23 * s), paint(skia.Color(120, 60, 40), a))

def draw_tiers(c, t, E):
    a = K.fade(t, E["D"] - 0.1, E["job"] - 0.05, 0.25)
    if a <= 0:
        return
    x0, x1, y0, rh = 90, 990, 640, 104
    c.drawRRect(tap.rrect(x0 - 16, y0 - 80, x1 + 16, y0 + 5 * rh + 18, 22), paint(K.DARK_PILL, a))
    text_center(c, "PRIMATE TIER LIST (BY THE BOOKS)", W / 2, y0 - 28, font("JetBrainsMono-700", 30), paint(INK, a))
    lab = font("Bricolage-800", 64)
    chip_f = font("JetBrainsMono-700", 30)
    slide = smooth01((t - E["mid"] - 0.05) / 0.45)
    for k, (name, col, item) in enumerate(TIERS):
        y = y0 + k * rh
        c.drawRect(skia.Rect(x0, y + 6, x0 + 120, y + rh - 4), paint(col, a))
        text_center(c, name, x0 + 60, y + rh / 2 + 24, lab, paint(tap.PANEL2, a))
        c.drawRect(skia.Rect(x0 + 124, y + 6, x1, y + rh - 4), paint(skia.ColorSetARGB(255, 34, 36, 44), a))
        if item:
            w = chip_f.measureText(item)
            c.drawRRect(tap.rrect(x0 + 150, y + 22, x0 + 182 + w, y + rh - 20, 10), paint(skia.ColorSetARGB(255, 60, 63, 74), a))
            c.drawString(item, x0 + 166, y + rh / 2 + 11, chip_f, paint(INK, a))
    # George slides in from the right into B
    yb = y0 + 2 * rh + rh / 2
    gx = x1 + 120 - slide * (x1 + 120 - (x0 + 210))
    if slide > 0:
        george_chip(c, gx, yb, 64, a)
        c.drawString("GEORGE", gx + 56, yb + 11, chip_f, paint(INK, a * slide))
    st = smooth01((t - E["mid"] - 0.5) / 0.2)
    if st > 0:
        c.save()
        c.rotate(-8, x1 - 130, yb)
        c.drawRRect(tap.rrect(x1 - 225, yb - 42, x1 - 35, yb + 36, 10), tap.stroke(tap.RED, 6, a * st))
        text_center(c, "MID", x1 - 130, yb + 20, font("Bricolage-800", 58), paint(tap.RED, a * st))
        c.restore()

def draw_study(c, t, E):
    a = K.fade(t, E["H"] - 0.15, E["I"] - 0.1, 0.25)
    if a <= 0:
        return
    cols, rows = 24, 30
    x0, y0, cw, ch = 112, 600, 36, 28
    c.drawRRect(tap.rrect(x0 - 40, y0 - 90, x0 + cols * cw + 40, y0 + rows * ch + 30, 22), paint(skia.ColorSetARGB(225, 10, 11, 14), a))
    shown = int(720 * smooth01((t - E["720"] + 0.3) / 1.0))
    special = 14 * cols + 15
    hi = smooth01((t - E["one"] - 0.05) / 0.3)
    man = paint(skia.Color(150, 155, 170), a)
    wom = paint(skia.Color(105, 110, 125), a)
    for n in range(shown):
        r, k = divmod(n, cols)
        x, yb = x0 + k * cw + 8, y0 + r * ch + ch - 4
        if n == special:
            continue
        c.drawRect(skia.Rect(x, yb - 20, x + 8, yb), man)
        c.drawRect(skia.Rect(x + 11, yb - 14, x + 19, yb), wom)
    if shown > special:
        r, k = divmod(special, cols)
        x, yb = x0 + k * cw + 8, y0 + r * ch + ch - 4
        col = paint(GOLD if hi > 0 else skia.Color(150, 155, 170), a)
        c.drawRect(skia.Rect(x, yb - 14, x + 8, yb), col)
        c.drawRect(skia.Rect(x + 11, yb - 22, x + 19, yb), col)
        if hi > 0:
            c.drawCircle(x + 10, yb - 10, 30 + 6 * (1 - hi), tap.stroke(GOLD, 5, a * hi))
    if hi > 0:
        text_center(c, "WOMAN TALLER: 1 OF 720", W / 2, y0 - 34, font("JetBrainsMono-700", 34), paint(GOLD, a * hi))
    else:
        text_center(c, "720 COUPLES", W / 2, y0 - 34, font("JetBrainsMono-700", 34), paint(INK, a))
    text_center(c, "Source: Gillis & Avis (1980), The male-taller norm in mate selection", W / 2, 1525,
                font("JetBrainsMono-500", 24), paint(MUTED, 0.9 * a))

def draw_mog(c, t, E):
    a = K.fade(t, E["mogged"] - 0.05, E["H"] - 0.2, 0.15)
    if a <= 0:
        return
    s = 1.0 + 0.25 * math.exp(-max(0.0, t - E["mogged"]) * 9)
    c.save()
    c.translate(W / 2, 1200)
    c.rotate(-6)
    c.scale(s, s)
    f = font("Bricolage-800", 120)
    w = f.measureText("HEIGHT-MOGGED")
    while w > 940:
        f = font("Bricolage-800", f.getSize() - 6)
        w = f.measureText("HEIGHT-MOGGED")
    c.drawRRect(tap.rrect(-w / 2 - 30, -110, w / 2 + 30, 40, 18), paint(tap.RED, a))
    c.drawString("HEIGHT-MOGGED", -w / 2, 0, f, paint(INK, a))
    c.restore()

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, K.fade(t, -1, E["B"] - 0.05, 0.2))
    tap.draw_captions(c, t, sents, cm)
    c.restore()
    lab = font("JetBrainsMono-700", 30)
    # (anchor, text, start, end, dx, dy, color)
    tags = [
        ("george", "SUBJECT: GEORGE", E["B"] - 0.05, E["tail"] - 0.2, 200, -200, ORANGE),
        ("rear", "TAIL: NONE", E["tail"] - 0.05, E["D"] - 0.3, 220, -160, tap.RED),
        ("mark_g", "GEORGE", E["belt"] - 0.15, E["mogged"] - 0.4, 70, 0, ORANGE),
        ("mark_m", "ROOMMATE", E["chad"] - 0.1, E["mogged"] - 0.4, 70, 0, GOLD),
        ("mark_h", "+1 HAT", E["hat"] + 0.15, E["mogged"] - 0.4, 70, 0, GOLD),
    ]
    for name, text, t0, t1, dx, dy, col in tags:
        a = K.fade(t, t0, t1, 0.2)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, col, lab)
    draw_tiers(c, t, E)
    draw_mog(c, t, E)
    draw_study(c, t, E)
    pill(c, "SPECIES: MONKEY", W / 2, 1440, K.fade(t, E["monkey"] - 0.1, E["ape"] - 0.1, 0.2), INK)
    pill(c, "SPECIES: APE (TECHNICALLY)", W / 2, 1440, K.fade(t, E["ape"] - 0.1, E["1941"] - 0.1, 0.2), ORANGE)
    pill(c, "MISLABELED SINCE 1941", W / 2, 1440, K.fade(t, E["1941"] - 0.1, E["D"] - 0.15, 0.2), tap.RED)
    pill(c, "JOB: NONE", W / 2, 1440, K.fade(t, E["job"] - 0.1, E["car"] - 0.1, 0.15), tap.RED)
    pill(c, "CAR: NONE", W / 2, 1440, K.fade(t, E["car"] - 0.1, E["roommate"] - 0.1, 0.15), tap.RED)
    pill(c, "LIVES WITH: ROOMMATE", W / 2, 1440, K.fade(t, E["roommate"] - 0.1, E["E"] - 0.1, 0.15), INK)
    pill(c, "HEIGHT: BELT LEVEL", W / 2, 1440, K.fade(t, E["belt"] - 0.1, E["ideal"] - 0.1, 0.15), INK)
    pill(c, "NOT IDEAL", W / 2, 1440, K.fade(t, E["ideal"] - 0.1, E["F"] - 0.1, 0.15), tap.RED)
    pill(c, "ROOMMATE: CHAD IN THE YELLOW HAT", W / 2, 1440, K.fade(t, E["chad"] - 0.1, E["mogged"] - 0.1, 0.2), GOLD, size=30)
    pill(c, "STATUS: IT'S OVER", W / 2, 1440, K.fade(t, E["over"] - 0.1, E["J"] - 0.1, 0.15), tap.RED)
    pill(c, "STATUS: ASCENDING", W / 2, 1440, K.fade(t, E["ascending"] - 0.1, E["K"] - 0.1, 0.15), GOLD)
    pill(c, "PEER REVIEW: PENDING", W / 2, 1440, K.fade(t, E["pending"] - 0.1, speech_end + 0.6, 0.2), MUTED)
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
    K.run_blender("george_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0]
    if not preview_times:
        build_audio(sents, E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "george" if preview_times else None)

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
