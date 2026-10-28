"""'Gym bro reads the label': a deadpan voxel explainer. A gym bro is fine with every strange ingredient (raw eggs,
raw liver, taurine and its rumor) and panics at 0.1 g of sugar. From Austin's DM (a @realriderjet reel, Oct 27); our own script.

python render_gym.py out.mp4 out.wav     full render (Blender frames are cached in out/gym/frames)
python render_gym.py preview 1.0,12.5    render and composite stills into preview/
python render_gym.py times               narrate and print the event times

Facts: taurine is named from Latin taurus (bull) because it was first isolated from ox bile, by Tiedemann and Gmelin in 1827;
energy-drink taurine is synthetic, not from bulls (https://www.chemistryworld.com/podcasts/taurine/1010038.article and https://www.etymonline.com/word/taurine).
Red Bull 8.4 fl oz: 27 g sugar (retailer nutrition listing: https://giantfoodstores.com/groceries/product/red-bull-energy-drink-8-4-oz-can/99550).
Rocky drinks raw eggs in Rocky (1976). The 0.1 g label is the reference reel's joke.
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
    ("A", "A *gym bro* reads the *ingredients.*"),
    ("B", "*Creatine.* Fine. Raw *eggs,* like *Rocky.* *Fine.*"),
    ("C", "*Beef liver,* uncooked. *Delicious.*"),
    ("D", "*Taurine.* Named after the Latin word for *bull.*"),
    ("E", "The internet says it comes from *bull sperm.* He read{/ɹˈɛd/} that. Still *drinking* it."),
    ("F", "It doesn't, for the record. It was first found in *ox bile* in *1827{eighteen twenty-seven},* and now it's made in a *lab.*"),
    ("G", "Then he sees it. *Point one grams* of *sugar.*"),
    ("H", "*Absolutely not.* That's *poison.*"),
    ("I", "Meanwhile a *Red Bull,* the *taurine* drink, has about *27{twenty-seven}* grams."),
    ("J", "The *gains* are *safe.*"),
]
EXTRA_GAP = {3: 0.1, 5: 0.15, 6: 0.25, 7: 0.15, 8: 0.25, 9: 0.2}
OUT = os.path.join(ROOT, "out", "gym")
FRAMES = os.path.join(OUT, "frames")

def wn(sents, si, sub, nth=0):
    s = sents[si]
    hits = [i for i, w in enumerate(s["words"]) if sub.lower() in w["display"].lower()]
    return s["abs_starts"][hits[min(nth, len(hits) - 1)]] if hits else s["t0"]

def events(sents, speech_end):
    w = lambda si, sub, n=0: wn(sents, si, sub, n)
    s = lambda si: sents[si]["t0"]
    E = {k: s(i) for i, k in enumerate("ABCDEFGHIJ")}
    E.update({"ingredients": w(0, "ingredients"), "creatine": w(1, "Creatine"), "fine1": w(1, "Fine"),
              "eggs": w(1, "eggs"), "rocky": w(1, "Rocky"), "fine2": w(1, "Fine", 1), "liver": w(2, "liver"),
              "delicious": w(2, "Delicious"), "taurine": w(3, "Taurine"), "bull": w(3, "bull"),
              "sperm": w(4, "sperm"), "drinking": w(4, "drinking"), "doesnt": w(5, "doesn't"), "bile": w(5, "bile"),
              "1827": w(5, "1827"), "lab": w(5, "lab"), "sees": w(6, "sees"), "point": w(6, "Point"),
              "sugar": w(6, "sugar"), "absolutely": w(7, "Absolutely"), "poison": w(7, "poison"),
              "redbull": w(8, "Red"), "27": w(8, "27"), "gains": w(9, "gains"), "safe": w(9, "safe"),
              "speech_end": speech_end})
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
    hit(0.05, "pop", 0.18)
    for k, key in enumerate(("creatine", "eggs", "liver")):
        hit(E[key] - 0.05, "pop", 0.2, rate=1.0 + 0.06 * k)
    for key in ("fine1", "fine2", "delicious", "drinking"):
        hit(E[key] + 0.05, "kalimba", 0.14, rate=1.2)
    hit(E["taurine"] - 0.2, "swoosh", 0.16)
    hit(E["sperm"], "perc", 0.2, rate=0.8)
    hit(E["doesnt"], "deny", 0.18)
    hit(E["lab"], "pop", 0.16, rate=1.3)
    hit(E["sugar"], "bass", 0.24, lp=3000)
    hit(E["sugar"] + 0.2, "thunder", 0.22, lp=4000)
    hit(E["absolutely"], "deny", 0.24, rate=0.8)
    hit(E["poison"], "deny", 0.24, rate=0.65)
    hit(E["redbull"] - 0.2, "woosh", 0.16, rate=1.1)
    hit(E["27"], "perc", 0.2)
    hit(E["gains"], "powerup", 0.32)
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
    for s, k in (("Gym bro reads", False), ("the label", True)):
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
LABEL = [("creatine", "CREATINE", "OK"), ("eggs", "RAW EGGS", "OK"), ("liver", "RAW BEEF LIVER", "OK"),
         ("taurine", "TAURINE", "OK"), ("point", "SUGAR 0.1 g", "NO")]

def draw_label(c, t, E):
    """The ingredients card, top-left under the captions; lines tick in as he reads."""
    a = K.fade(t, E["creatine"] - 0.15, E["sperm"] - 0.1, 0.25) + K.fade(t, E["sees"] - 0.1, E["redbull"] - 0.15, 0.25)
    a = min(1.0, a)
    if a <= 0:
        return
    x0, y0, w = 70, 1010, 560
    rows = [r for r in LABEL if t >= E[r[0]] - 0.1]
    h = 80 + 58 * len(LABEL)
    c.drawRRect(tap.rrect(x0, y0, x0 + w, y0 + h, 16), paint(skia.Color(245, 243, 236), a))
    c.drawString("INGREDIENTS", x0 + 24, y0 + 52, font("Bricolage-800", 40), paint(skia.Color(15, 15, 18), a))
    c.drawRect(skia.Rect(x0 + 24, y0 + 66, x0 + w - 24, y0 + 72), paint(skia.Color(15, 15, 18), a))
    f = font("JetBrainsMono-700", 32)
    for k, (key, name, verdict) in enumerate(rows):
        y = y0 + 118 + 58 * k
        bad = verdict == "NO"
        if bad:
            flash = 0.5 + 0.5 * math.sin((t - E["sugar"]) * 14)
            c.drawRect(skia.Rect(x0 + 12, y - 40, x0 + w - 12, y + 14), paint(tap.RED, a * (0.35 + 0.4 * flash)))
        c.drawString(name, x0 + 24, y, f, paint(skia.Color(15, 15, 18), a))
        col = tap.RED if bad else skia.Color(30, 140, 50)
        txt = "X" if bad else "OK"
        c.drawString(txt, x0 + w - 24 - f.measureText(txt), y, f, paint(col, a))

def draw_myth(c, t, E):
    a = K.fade(t, E["sperm"] - 0.1, E["G"] - 0.15, 0.25)
    if a <= 0:
        return
    x0, y0 = 70, 1060
    rows = [("THE INTERNET", "bull sperm", tap.RED, E["sperm"] - 0.1), ("FIRST FOUND", "ox bile, 1827", GOLD, E["bile"] - 0.1),
            ("MADE TODAY", "in a lab", GREEN, E["lab"] - 0.1)]
    c.drawRRect(tap.rrect(x0, y0, 1010, y0 + 60 + 70 * len(rows), 18), paint(K.DARK_PILL, a))
    f1, f2 = font("JetBrainsMono-700", 30), font("Bricolage-800", 44)
    for k, (h, v, col, t0) in enumerate(rows):
        b = a * smooth01((t - t0) / 0.25)
        if b <= 0:
            continue
        y = y0 + 80 + 70 * k
        c.drawString(h, x0 + 26, y, f1, paint(MUTED, b))
        c.drawString(v, x0 + 340, y + 4, f2, paint(col, b))
        if k == 0 and t > E["doesnt"]:
            c.drawRect(skia.Rect(x0 + 336, y - 14, x0 + 340 + f2.measureText(v), y - 8), paint(INK, b))

def draw_compare(c, t, E):
    a = K.fade(t, E["redbull"] - 0.15, E["J"] - 0.1, 0.25)
    if a <= 0:
        return
    x0, y0 = 70, 1000
    c.drawRRect(tap.rrect(x0, y0, 1010, y0 + 400, 20), paint(K.DARK_PILL, a))
    text_center(c, "SUGAR PER SERVING", W / 2, y0 + 56, font("JetBrainsMono-700", 32), paint(MUTED, a))
    grow = smooth01((t - E["27"] + 0.3) / 0.6)
    full = 700
    f = font("JetBrainsMono-700", 34)
    c.drawString("HIS DRINK", x0 + 30, y0 + 140, f, paint(INK, a))
    c.drawRect(skia.Rect(x0 + 30, y0 + 160, x0 + 30 + max(4, full * 0.1 / 27), y0 + 210), paint(GREEN, a))
    c.drawString("0.1 g", x0 + 60, y0 + 200, f, paint(GREEN, a))
    c.drawString("RED BULL (8.4 oz)", x0 + 30, y0 + 280, f, paint(INK, a))
    c.drawRect(skia.Rect(x0 + 30, y0 + 300, x0 + 30 + full * grow, y0 + 350), paint(tap.RED, a))
    if grow > 0.9:
        c.drawString("27 g", x0 + 30 + full + 20, y0 + 340, f, paint(tap.RED, a))
    text_center(c, "Source: Red Bull 8.4 oz can nutrition label (retailer listing)", W / 2, 1525,
                font("JetBrainsMono-500", 22), paint(MUTED, 0.9 * a))

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, K.fade(t, -1, E["B"] - 0.05, 0.2))
    tap.draw_captions(c, t, sents, cm)
    c.restore()
    lab = font("JetBrainsMono-700", 30)
    tags = [
        ("tub", "CREATINE", E["creatine"] + 0.1, E["C"] - 0.2, 150, -150, GREEN),
        ("eggs", "RAW", E["eggs"] + 0.1, E["C"] - 0.2, 60, -260, GREEN),
        ("liver", "UNCOOKED", E["liver"] + 0.1, E["D"] - 0.3, 170, -200, GREEN),
        ("can", "TAURINE", E["taurine"] + 0.05, E["sperm"] - 0.15, 180, -170, GOLD),
    ]
    for name, text, t0, t1, dx, dy, col in tags:
        a = K.fade(t, t0, t1, 0.2)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, col, lab)
    draw_label(c, t, E)
    draw_myth(c, t, E)
    draw_compare(c, t, E)
    pill(c, "TAURUS = BULL (LATIN)", W / 2, 1440, K.fade(t, E["bull"] - 0.1, E["E"] - 0.1, 0.15), GOLD)
    pill(c, "STILL DRINKING", W / 2, 1440, K.fade(t, E["drinking"] - 0.1, E["F"] - 0.1, 0.15), GREEN)
    pill(c, "THREAT LEVEL: MAXIMUM", W / 2, 1440, K.fade(t, E["absolutely"] - 0.1, E["I"] - 0.1, 0.15), tap.RED)
    pill(c, "GAINS: SAFE", W / 2, 1440, K.fade(t, E["gains"] - 0.1, speech_end + 0.8, 0.15), GOLD)
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
    K.run_blender("gym_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0]
    if not preview_times:
        build_audio(sents, E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "gym" if preview_times else None)

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
