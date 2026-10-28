"""'The November 1st pharmacy hero': a deadpan voxel short. The morning after Michael Crackson's Halloween party, a
man in a cape walks into the family planning aisle to meet the love of his life. From Austin's DM (a @nick2flyy__ reel,
Oct 27, with his note to mention "Michael Crackson's Halloween party") and his earlier $50 CVS charge idea; our own script.

python render_pharmacy.py out.mp4 out.wav     full render (Blender frames are cached in out/pharmacy/frames)
python render_pharmacy.py preview 1.0,12.5    render and composite stills into preview/
python render_pharmacy.py times               narrate and print the event times

Facts: the FDA approved Plan B One-Step for over-the-counter sale with no age limit or ID in June 2013
(https://www.npr.org/2013/06/11/190559971/feds-buckle-on-emergency-contraception-age-restrictions,
https://www.cbsnews.com/news/fda-approves-over-the-counter-sales-of-plan-b-one-step-for-all-ages/); it works best within
three days, and the brand costs about $40 to $50 (same CBS piece; https://uspharmacist.com/weekly_news_update/nl/41486).
The bank charge is a made-up notification; Michael Crackson's party is the meme Austin named, not a real event.
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
    ("A", "*November first.* A man puts on a *cape.*"),
    ("B", "Destination: the *pharmacy.* The *family planning* aisle."),
    ("C", "Last night was *Michael Crackson's* Halloween party."),
    ("D", "This morning, the line is *out the door.*"),
    ("E", "Plan B has been sold *over the counter* since *2013{twenty thirteen},* no ID needed."),
    ("F", "It works best within *three days,* and runs about *forty* to *fifty dollars.*"),
    ("G", "Somewhere, a *boyfriend* is staring at a *fifty-dollar* pharmacy charge. He thinks it was *snacks.*"),
    ("H", "But our hero isn't here to *buy* anything."),
    ("I", "He's here to meet the *love of his life.*"),
    ("J", "She's here to *undo* last night."),
    ("K", "Security is *on the way.*"),
]
EXTRA_GAP = {2: 0.1, 4: 0.1, 6: 0.15, 7: 0.2, 8: 0.1, 9: 0.2, 10: 0.25}
OUT = os.path.join(ROOT, "out", "pharmacy")
FRAMES = os.path.join(OUT, "frames")

def wn(sents, si, sub, nth=0):
    s = sents[si]
    hits = [i for i, w in enumerate(s["words"]) if sub.lower() in w["display"].lower()]
    return s["abs_starts"][hits[min(nth, len(hits) - 1)]] if hits else s["t0"]

def events(sents, speech_end):
    w = lambda si, sub, n=0: wn(sents, si, sub, n)
    s = lambda si: sents[si]["t0"]
    E = {k: s(i) for i, k in enumerate("ABCDEFGHIJK")}
    E.update({"cape": w(0, "cape"), "pharmacy": w(1, "pharmacy"), "family": w(1, "family"), "crackson": w(2, "Crackson"),
              "door": w(3, "door"), "counter": w(4, "counter"), "2013": w(4, "2013"), "id": w(4, "ID"),
              "three": w(5, "three"), "forty": w(5, "forty"), "fifty": w(5, "fifty"), "boyfriend": w(6, "boyfriend"),
              "charge": w(6, "fifty"), "snacks": w(6, "snacks"), "buy": w(7, "buy"), "love": w(8, "love"),
              "undo": w(9, "undo"), "way": w(10, "way"), "speech_end": speech_end})
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
    hit(0.0, "braam", 0.12, lp=2500)
    hit(E["cape"], "swoosh", 0.22)
    steps = sfx.onsets(F["steps"], 0.25, 10)
    t, k = 0.3, 0
    while t < E["D"] - 0.3:
        hit(t, "steps", 0.12, start=steps[k % len(steps)], dur=0.2, lp=2500, hp=90)
        t += 0.42
        k += 1
    hit(E["family"], "pop", 0.18)
    hit(E["crackson"], "perc", 0.2)
    hit(E["door"], "woosh", 0.16)
    hit(E["2013"], "pop", 0.16, rate=1.1)
    hit(E["three"], "pop", 0.16, rate=1.2)
    hit(E["forty"], "perc", 0.16, rate=1.1)
    hit(E["charge"] - 0.1, "kalimba", 0.18)
    hit(E["snacks"], "deny", 0.18, rate=1.1)
    hit(E["H"] - 0.1, "powerup", 0.24)
    hit(E["love"], "kalimba", 0.18, rate=0.9)
    hit(E["undo"], "bass", 0.2, lp=3000)
    hit(E["K"] - 0.2, "deny", 0.22, rate=0.7)
    hit(E["way"], "door", 0.24, lp=5000)
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
    for s, k in (("November 1st,", False), ("9 a.m.", True)):
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

def pill(c, text, cx, y, a, color=INK, bg=K.DARK_PILL, size=34):
    if a <= 0:
        return
    f = font("JetBrainsMono-700", size)
    w = f.measureText(text)
    c.drawRRect(tap.rrect(cx - w / 2 - 22, y - size - 10, cx + w / 2 + 22, y + 16, 14), paint(bg, a))
    c.drawString(text, cx - w / 2, y, f, paint(color, a))

GREEN = skia.Color(120, 220, 120)
PURPLE = skia.Color(150, 90, 220)

def draw_flyer(c, t, E):
    a = K.fade(t, E["crackson"] - 0.2, E["D"] - 0.1, 0.25)
    if a <= 0:
        return
    s = 0.92 + 0.08 * smooth01((t - E["crackson"] + 0.2) / 0.3)
    c.save()
    c.translate(W / 2, 1000)
    c.rotate(-4)
    c.scale(s, s)
    c.drawRRect(tap.rrect(-330, -260, 330, 260, 18), paint(skia.Color(18, 12, 24), a))
    c.drawRRect(tap.rrect(-330, -260, 330, 260, 18), tap.stroke(ORANGE, 6, a))
    text_center(c, "YOU'RE INVITED", 0, -170, font("JetBrainsMono-700", 34), paint(ORANGE, a))
    text_center(c, "MICHAEL", 0, -70, font("Bricolage-800", 92), paint(INK, a))
    text_center(c, "CRACKSON'S", 0, 30, font("Bricolage-800", 92), paint(INK, a))
    text_center(c, "HALLOWEEN PARTY", 0, 110, font("Bricolage-800", 56), paint(PURPLE, a))
    text_center(c, "OCT 31  .  TILL LATE  .  COSTUMES", 0, 190, font("JetBrainsMono-700", 30), paint(MUTED, a))
    c.restore()

def draw_facts(c, t, E):
    a = K.fade(t, E["E"] - 0.15, E["G"] - 0.15, 0.25)
    if a <= 0:
        return
    x0, y0 = 70, 1010
    rows = [("OVER THE COUNTER", "since 2013", E["counter"] - 0.1), ("ID NEEDED", "no", E["id"] - 0.1),
            ("WORKS BEST", "within 72 h", E["three"] - 0.1), ("PRICE", "about $40 to $50", E["forty"] - 0.1)]
    c.drawRRect(tap.rrect(x0, y0, 1010, y0 + 70 + 72 * len(rows), 18), paint(K.DARK_PILL, a))
    f1, f2 = font("JetBrainsMono-700", 30), font("Bricolage-800", 42)
    for k, (h, v, t0) in enumerate(rows):
        b = a * smooth01((t - t0) / 0.25)
        if b <= 0:
            continue
        y = y0 + 84 + 72 * k
        c.drawString(h, x0 + 26, y, f1, paint(MUTED, b))
        c.drawString(v, 990 - f2.measureText(v), y + 4, f2, paint(GOLD, b))
    text_center(c, "Sources: FDA approval June 2013 (NPR, CBS); Plan B label", W / 2, 1525,
                font("JetBrainsMono-500", 22), paint(MUTED, 0.9 * a))

def draw_bank(c, t, E):
    a = K.fade(t, E["boyfriend"] - 0.1, E["H"] - 0.1, 0.25)
    if a <= 0:
        return
    drop = 1 - smooth01((t - E["boyfriend"] + 0.1) / 0.35)
    x0, y0 = 90, 1010 - 120 * drop
    c.drawRRect(tap.rrect(x0, y0, 990, y0 + 250, 30), paint(skia.Color(236, 238, 242), a))
    c.drawRRect(tap.rrect(x0 + 30, y0 + 34, x0 + 110, y0 + 114, 18), paint(skia.Color(40, 120, 70), a))
    text_center(c, "$", x0 + 70, y0 + 98, font("Bricolage-800", 60), paint(INK, a))
    dk = skia.Color(20, 20, 24)
    c.drawString("YOUR BANK", x0 + 136, y0 + 66, font("JetBrainsMono-700", 30), paint(skia.Color(110, 110, 120), a))
    c.drawString("now", 990 - 30 - font("JetBrainsMono-700", 28).measureText("now"), y0 + 66, font("JetBrainsMono-700", 28),
                 paint(skia.Color(110, 110, 120), a))
    c.drawString("PHARMACY  -$49.99", x0 + 136, y0 + 124, font("Bricolage-800", 52), paint(dk, a))
    c.drawString("Nov 1, 9:04 AM  .  Pending", x0 + 136, y0 + 180, font("JetBrainsMono-700", 30), paint(skia.Color(80, 80, 90), a))
    sn = smooth01((t - E["snacks"]) / 0.25)
    if sn > 0:
        pill(c, "HIS GUESS: SNACKS", W / 2, y0 + 330, a * sn, GREEN)

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, K.fade(t, -1, E["B"] - 0.05, 0.2))
    tap.draw_captions(c, t, sents, cm)
    c.restore()
    lab = font("JetBrainsMono-700", 30)
    tags = [
        ("cape", "CAPE: EQUIPPED", E["cape"] - 0.05, E["B"] - 0.1, 200, -120, tap.RED),
        ("sign", "AISLE 7: FAMILY PLANNING", E["family"] - 0.1, E["C"] - 0.1, -60, 160, GOLD),
        ("line", "LINE: OUT THE DOOR", E["door"] - 0.1, E["E"] - 0.1, 120, -200, ORANGE),
        ("hero", "PURPOSE: ROMANCE", E["love"] - 0.1, E["J"] - 0.1, 160, -140, GOLD),
        ("line", "PURPOSE: DAMAGE CONTROL", E["undo"] - 0.1, E["K"] - 0.1, -60, -220, ORANGE),
        ("guard", "SECURITY", E["way"] - 0.2, speech_end + 1.0, 140, -160, tap.RED),
    ]
    for name, text, t0, t1, dx, dy, col in tags:
        a = K.fade(t, t0, t1, 0.2)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, col, lab)
    draw_flyer(c, t, E)
    draw_facts(c, t, E)
    draw_bank(c, t, E)
    pill(c, "MISSION: SAVE SOMEONE", W / 2, 1440, K.fade(t, E["H"] - 0.1, E["I"] - 0.1, 0.15), GOLD)
    pill(c, "HERO STATUS: REVOKED", W / 2, 1440, K.fade(t, E["way"] - 0.05, speech_end + 0.8, 0.15), tap.RED)
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
    K.run_blender("pharmacy_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0]
    if not preview_times:
        build_audio(sents, E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "pharmacy" if preview_times else None)

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
