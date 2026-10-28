"""'Halloween party loadout': a deadpan voxel explainer in the George apartment. One guy gears up item by item for a
Halloween party, stats on screen, then the polo logo gets inspected. From Austin's DM (a @brodyy.up reel, Oct 27); our own script.

python render_loadout.py out.mp4 out.wav     full render (Blender frames are cached in out/loadout/frames)
python render_loadout.py preview 1.0,12.5    render and composite stills into preview/
python render_loadout.py times               narrate and print the event times

Facts: average US man is about 5 ft 9 in (CDC NCHS, reported by NBC: https://www.nbcnewyork.com/news/health/American-Adults-Getting-Heavier-Height-CDC-503226801.html).
Height insoles add about 1 to 3 in (https://www.fashionbeans.com/article/best-height-increase-insoles/).
U.S. Polo Assn.'s logo has two riders, Ralph Lauren's one; they have been in court over it since 1984
(https://en.wikipedia.org/wiki/Polo_Ralph_Lauren_vs_U.S._Polo_Association). Aura and frame numbers are the joke.
"""
import json, math, os, sys
import numpy as np
import skia
from common import *
import render_tap as tap
import kit3d as K

FPS = 60
TAIL = 1.2
SCRIPT = [
    ("A", "*Halloween party* prep, *2026{twenty twenty-six}* edition."),
    ("B", "Base stats: *five nine,* the *average* American guy."),
    ("C", "Item one: a *size small* shirt. *Breathing* is optional."),
    ("D", "Item two: *three-inch* insoles. Six feet, *technically.*"),
    ("E", "Item three: *shoulder pads.* The frame is now *load-bearing.*"),
    ("F", "Item four: *concealer.* Item five: a *bulge enhancer.* We will not be *elaborating.*"),
    ("G", "Item six: a *Porsche* key. There is no *Porsche.*"),
    ("H", "Item seven: *colored contacts.* Eye color is now *negotiable.*"),
    ("I", "And the *polo.* Check the *horse.*"),
    ("J", "*Two* riders. *U.S. Polo Assn.{U S Polo Association}* *Too many people* on that horse."),
    ("K", "Ralph Lauren's has *one.* They've been in *court* over it since *1984{nineteen eighty-four}.*"),
    ("L", "Final stats: *six feet,* *broad,* *rich.* Until the *shoes* come off."),
]
EXTRA_GAP = {1: 0.1, 2: 0.1, 5: 0.1, 7: 0.1, 8: 0.15, 9: 0.1, 10: 0.2, 11: 0.3}
OUT = os.path.join(ROOT, "out", "loadout")
FRAMES = os.path.join(OUT, "frames")

def wn(sents, si, sub, nth=0):
    s = sents[si]
    hits = [i for i, w in enumerate(s["words"]) if sub.lower() in w["display"].lower()]
    return s["abs_starts"][hits[min(nth, len(hits) - 1)]] if hits else s["t0"]

def events(sents, speech_end):
    w = lambda si, sub, n=0: wn(sents, si, sub, n)
    s = lambda si: sents[si]["t0"]
    E = {k: s(i) for i, k in enumerate("ABCDEFGHIJKL")}
    E.update({"base": w(1, "five"), "average": w(1, "average"), "small": w(2, "small"), 
              "breathing": w(2, "Breathing"), "insoles": w(3, "three"), "three": w(3, "three"), "six": w(3, "Six"),
              "technically": w(3, "technically"), "pads": w(4, "pads"), "load": w(4, "load"),
              "concealer": w(5, "concealer"), "bulge": w(5, "bulge"), "elab": w(5, "elaborating"),
              "porsche": w(6, "Porsche"), "noporsche": w(6, "Porsche", 1), "contacts": w(7, "contacts"),
              "negotiable": w(7, "negotiable"), "polo": w(8, "polo"), "horse": w(8, "horse"), "two": w(9, "Two"),
              "assn": w(9, "U.S."), "many": w(9, "many"), "one": w(10, "one"), "court": w(10, "court"),
              "1984": w(10, "1984"), "final": w(11, "Final"), "feet": w(11, "feet"), "broad": w(11, "broad"),
              "rich": w(11, "rich"), "off": w(11, "shoes"), "speech_end": speech_end})
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
    tr = new_track(duration)
    tr[:n] += voice           # no ambience bed: no hum, buzz or drone (Austin, Oct 27)
    hit = lambda t0, key, gain, **kw: add(tr, t0, sfx.clip(F[key], **kw), gain)
    hit(0.0, "woosh", 0.2)
    hit(0.05, "pop", 0.2)
    hit(E["base"], "tape", 0.2, dur=1.0)
    for k, key in enumerate(("small", "insoles", "pads", "concealer", "bulge", "porsche", "contacts")):
        hit(E[key] - 0.05, "pop" if k % 2 == 0 else "perc", 0.2, rate=1.0 + 0.04 * k)
        hit(E[key] - 0.25, "swoosh", 0.12, rate=1.1)
    hit(E["breathing"], "deny", 0.18, rate=1.1)
    hit(E["six"], "kalimba", 0.18)
    hit(E["load"], "perc", 0.18, rate=0.8)
    hit(E["elab"], "deny", 0.2, rate=0.9)
    hit(E["noporsche"], "deny", 0.22, rate=0.8)
    hit(E["negotiable"], "kalimba", 0.16, rate=1.2)
    hit(E["horse"] - 0.2, "woosh", 0.16)
    hit(E["many"], "bass", 0.2, lp=3000)
    hit(E["court"], "perc", 0.2, rate=0.7)
    hit(E["final"], "powerup", 0.3)
    hit(E["off"] + 0.1, "deny", 0.3, rate=0.7)
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
    for s, k in (("Halloween party", False), ("loadout", True)):
        size = 96
        ff = font("Bricolage-800", size)
        wd = ff.measureText(s) + (40 if k else 0)
        x = W / 2 - wd / 2
        if k:
            c.drawRRect(tap.rrect(x, y - 82, x + wd, y + 26, 16), paint(ORANGE, a))
            c.drawString(s, x + 20, y, ff, paint(tap.PANEL2, a))
        else:
            c.drawString(s, x, y, ff, paint(INK, a))
        y += 116

def pill(c, text, cx, y, a, color=INK, bg=K.DARK_PILL, size=34, redact=None):
    if a <= 0:
        return
    f = font("JetBrainsMono-700", size)
    w = f.measureText(text)
    c.drawRRect(tap.rrect(cx - w / 2 - 22, y - size - 10, cx + w / 2 + 22, y + 16, 14), paint(bg, a))
    c.drawString(text, cx - w / 2, y, f, paint(color, a))
    if redact:
        x0 = cx - w / 2 + f.measureText(text[:redact[0]])
        x1 = cx - w / 2 + f.measureText(text[:redact[1]])
        c.drawRect(skia.Rect(x0 - 4, y - size + 2, x1 + 4, y + 8), paint(skia.Color(0, 0, 0), a))

def stat_panel(c, t, E):
    a = K.fade(t, E["B"] - 0.1, E["I"] - 0.15, 0.25) + K.fade(t, E["L"] - 0.1, 99, 0.25)
    a = min(1.0, a)
    if a <= 0:
        return
    ins = smooth01((t - E["insoles"]) / 0.3) * (1 - smooth01((t - E["off"]) / 0.3))
    inches = 69 + round(3 * ins)
    height = f"{inches // 12}'{inches % 12}\""
    frame = 100 + round(22 * smooth01((t - E["pads"]) / 0.3))
    items = sum(t >= E[k] for k in ("small", "insoles", "pads", "concealer", "bulge", "porsche", "contacts"))
    aura = 120 * items * (1 - smooth01((t - E["off"]) / 0.3))
    rows = [("HEIGHT", height, GOLD if ins > 0.5 else INK), ("FRAME", f"{frame}%", GOLD if frame > 100 else INK),
            ("ITEMS", f"{items}/7", INK), ("AURA", f"{int(aura)}", GOLD if aura > 0 else tap.RED)]
    x0, y0 = 70, 1050
    c.drawRRect(tap.rrect(x0, y0, x0 + 470, y0 + 66 + 58 * len(rows), 18), paint(K.DARK_PILL, a))
    c.drawString("STATS", x0 + 26, y0 + 50, font("JetBrainsMono-700", 30), paint(MUTED, a))
    f = font("JetBrainsMono-700", 38)
    for k, (name, val, col) in enumerate(rows):
        y = y0 + 106 + 58 * k
        c.drawString(name, x0 + 26, y, f, paint(INK, a))
        c.drawString(val, x0 + 444 - f.measureText(val), y, f, paint(col, a))

def horse(c, x, y, s, riders, a, col):
    """A crude polo-pony silhouette facing right with 1 or 2 stick riders; (x, y) is the hooves' baseline middle."""
    p = paint(col, a)
    c.drawRRect(tap.rrect(x - 0.9 * s, y - 1.5 * s, x + 0.7 * s, y - 0.85 * s, 0.3 * s), p)          # body
    for dx in (-0.75, -0.5, 0.35, 0.58):
        c.drawRect(skia.Rect(x + dx * s, y - 0.95 * s, x + (dx + 0.13) * s, y), p)                    # legs
    path = skia.Path()
    path.moveTo(x + 0.45 * s, y - 1.4 * s); path.lineTo(x + 0.95 * s, y - 2.2 * s)
    path.lineTo(x + 1.15 * s, y - 2.05 * s); path.lineTo(x + 0.8 * s, y - 1.1 * s); path.close()
    c.drawPath(path, p)                                                                              # neck
    c.drawRRect(tap.rrect(x + 0.85 * s, y - 2.3 * s, x + 1.45 * s, y - 1.95 * s, 0.1 * s), p)         # head
    c.drawRect(skia.Rect(x - 1.25 * s, y - 1.45 * s, x - 0.85 * s, y - 1.33 * s), p)                  # tail
    st = tap.stroke(col, 0.11 * s, a)
    for k in range(riders):
        rx = x - 0.15 * s - k * 0.55 * s
        c.drawCircle(rx, y - 2.5 * s, 0.17 * s, p)
        c.drawLine(rx, y - 2.33 * s, rx - 0.05 * s, y - 1.6 * s, st)
        c.drawLine(rx - 0.02 * s, y - 2.15 * s, rx + 0.45 * s, y - 2.7 * s - 0.15 * s * k, st)       # mallet arm
        c.drawLine(rx + 0.45 * s, y - 2.7 * s - 0.15 * s * k, rx + 0.3 * s, y - 3.4 * s, tap.stroke(col, 0.06 * s, a))

def draw_logos(c, t, E):
    a = K.fade(t, E["two"] - 0.15, E["L"] - 0.15, 0.25)
    if a <= 0:
        return
    show_r = smooth01((t - E["one"] + 0.1) / 0.3)
    y0 = 640
    c.drawRRect(tap.rrect(60, y0, 1020, y0 + 520, 24), paint(skia.ColorSetARGB(230, 10, 11, 14), a))
    horse(c, 300, y0 + 400, 80, 2, a, INK)
    text_center(c, "U.S. POLO ASSN.", 300, y0 + 470, font("JetBrainsMono-700", 34), paint(INK, a))
    many = smooth01((t - E["many"] + 0.05) / 0.25)
    if many > 0:
        c.drawCircle(265, y0 + 160, 120 + 10 * (1 - many), tap.stroke(tap.RED, 7, a * many))
        text_center(c, "TOO MANY PEOPLE", 300, y0 + 60, font("JetBrainsMono-700", 34), paint(tap.RED, a * many))
    if show_r > 0:
        horse(c, 760, y0 + 400, 80, 1, a * show_r, GOLD)
        text_center(c, "RALPH LAUREN", 780, y0 + 470, font("JetBrainsMono-700", 34), paint(GOLD, a * show_r))
        text_center(c, "1 RIDER", 780, y0 + 60, font("JetBrainsMono-700", 34), paint(GOLD, a * show_r))
    c.drawLine(540, y0 + 40, 540, y0 + 480, tap.stroke(MUTED, 3, a * 0.6))
    text_center(c, "Drawings ours. Court fight since 1984: Polo Ralph Lauren v. U.S. Polo Assn.", W / 2, 1525,
                font("JetBrainsMono-500", 22), paint(MUTED, 0.9 * a * smooth01((t - E["court"] + 0.2) / 0.3)))

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, K.fade(t, -1, E["B"] - 0.05, 0.2))
    tap.draw_captions(c, t, sents, cm)
    c.restore()
    lab = font("JetBrainsMono-700", 30)
    tags = [
        ("mark_b", "5'9\"", E["base"] - 0.1, E["C"] - 0.3, 70, 0, ORANGE),
        ("feet", "+3 IN", E["three"] - 0.1, E["E"] - 0.3, 190, 60, GOLD),
        ("mark_u", "6'0\"", E["six"] - 0.1, E["E"] - 0.3, 70, 0, GOLD),
        ("shoulder", "PADDED", E["pads"] + 0.1, E["F"] - 0.3, 170, -150, GOLD),
        ("hand", "KEY: PORSCHE", E["porsche"] + 0.1, E["noporsche"] - 0.1, 160, -170, GOLD),
        ("hand", "CAR: NONE", E["noporsche"] - 0.1, E["H"] - 0.2, 160, -170, tap.RED),
        ("chest", "2 RIDERS?", E["horse"] - 0.05, E["two"] - 0.15, 170, 170, ORANGE),
    ]
    for name, text, t0, t1, dx, dy, col in tags:
        a = K.fade(t, t0, t1, 0.2)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, col, lab)
    stat_panel(c, t, E)
    draw_logos(c, t, E)
    pill(c, "ITEM 1: SIZE S SHIRT", W / 2, 1440, K.fade(t, E["small"] - 0.1, E["breathing"] - 0.05, 0.15), INK)
    pill(c, "OXYGEN: OPTIONAL", W / 2, 1440, K.fade(t, E["breathing"] - 0.05, E["D"] - 0.1, 0.15), tap.RED)
    pill(c, "ITEM 2: HEIGHT INSOLES", W / 2, 1440, K.fade(t, E["insoles"] - 0.1, E["E"] - 0.1, 0.15), INK)
    pill(c, "ITEM 3: SHOULDER PADS", W / 2, 1440, K.fade(t, E["pads"] - 0.1, E["F"] - 0.1, 0.15), INK)
    pill(c, "ITEM 4: CONCEALER", W / 2, 1440, K.fade(t, E["concealer"] - 0.1, E["bulge"] - 0.1, 0.15), INK)
    pill(c, "ITEM 5: BULGE ENHANCER", W / 2, 1440, K.fade(t, E["bulge"] - 0.1, E["G"] - 0.1, 0.15), INK,
         redact=(8, 22) if t > E["elab"] - 0.05 else None)
    pill(c, "ITEM 6: PORSCHE KEY", W / 2, 1440, K.fade(t, E["porsche"] - 0.1, E["H"] - 0.1, 0.15), INK)
    pill(c, "ITEM 7: COLORED CONTACTS", W / 2, 1440, K.fade(t, E["contacts"] - 0.1, E["I"] - 0.1, 0.15), INK)
    pill(c, "LOGO CHECK", W / 2, 1440, K.fade(t, E["polo"] - 0.1, E["two"] - 0.15, 0.15), ORANGE)
    pill(c, "6'0\" / BROAD / RICH", W / 2, 1440, K.fade(t, E["feet"] - 0.1, E["off"] - 0.05, 0.15), GOLD)
    pill(c, "SHOES OFF: 5'9\"", W / 2, 1440, K.fade(t, E["off"] - 0.05, speech_end + 0.8, 0.15), tap.RED)
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
    K.run_blender("loadout_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0]
    if not preview_times:
        build_audio(sents, E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "loadout" if preview_times else None)

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
