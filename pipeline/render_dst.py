"""'The same hour twice': a deadpan clay short for the end of daylight saving time (Sunday Nov 1 2026, 2 a.m.). A guy
in bed watches his clock fall back, Congress keeps half-passing the fix, and he spends the free hour on his phone.

python render_dst.py out.mp4 out.wav     full render (Blender frames are cached in out/dst/frames)
python render_dst.py preview 1.0,12.5    render and composite stills into preview/
python render_dst.py times               narrate and print the event times

Facts and links: ops/episodes/2026-10-28-same-hour-twice.md (Fox 29 for the date, the states that skip it and
March 14 2027; Wikipedia and Anadolu for the Senate's 2022 unanimous consent; States Newsroom and WWSB for the House's
308-117 vote on July 14 2026; Sandhu's Michigan hospital study via the ACC and AFP for the 21% and 25% figures).
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
    ("A", "This *Sunday* at *2{two} a.m.,* the clock goes back to *1{one} a.m.*"),
    ("B", "You get the same *hour* twice."),
    ("C", "In *2022{twenty twenty-two},* the *Senate* voted to make daylight time *permanent.* The *House* never voted."),
    ("D", "This *July,* the *House* passed it, *308{three oh eight} to 117{one seventeen}.* The *Senate* hasn't."),
    ("E", "Congress agrees on this. Just never in the *same year.*"),
    ("F", "*Hawaii* and most of *Arizona* don't change their clocks at all."),
    ("G", "A Michigan study found heart attacks drop about *21{twenty-one} percent* the Tuesday after the fall change."),
    ("H", "In spring, when we lose the hour, they jump about *25{twenty-five} percent* that Monday."),
    ("I", "You will spend your free hour *scrolling.*"),
    ("J", "See you in *March.*"),
]
EXTRA_GAP = {1: 0.1, 4: 0.1, 5: 0.15, 8: 0.2, 9: 0.25}
OUT = os.path.join(ROOT, "out", "dst")
FRAMES = os.path.join(OUT, "frames")
tap.draw_captions = tap.draw_captions_clay          # the clay look's cream caption label

def wn(sents, si, sub, nth=0):
    s = sents[si]
    hits = [i for i, w in enumerate(s["words"]) if sub.lower() in w["display"].lower()]
    return s["abs_starts"][hits[min(nth, len(hits) - 1)]] if hits else s["t0"]

def events(sents, speech_end):
    w = lambda si, sub, n=0: wn(sents, si, sub, n)
    s = lambda si: sents[si]["t0"]
    E = {k: s(i) for i, k in enumerate("ABCDEFGHIJ")}
    E.update({"2am": w(0, "2"), "1am": w(0, "1"), "hour": w(1, "hour"), "2022": w(2, "2022"), "senate": w(2, "Senate"),
              "permanent": w(2, "permanent"), "house": w(2, "House"), "july": w(3, "July"), "308": w(3, "308"),
              "senate2": w(3, "Senate"), "same": w(4, "same"), "hawaii": w(5, "Hawaii"), "arizona": w(5, "Arizona"),
              "21": w(6, "21"), "25": w(7, "25"), "scroll": w(8, "scrolling"), "march": w(9, "March"),
              "speech_end": speech_end})
    return E

# ------------------------------------------------------------------ sound (recorded effects from the Sonniss GDC 2026 bundle, see sfx.py)

F = {
    "tick": "344 Audio - Antique Clocks/CLOCKTick_Crooked Antique Clock_344 Audio_Antique Clocks.wav",
    "cloth": "InMotionAudio - Foley T-Shirt/FOLYClth_ClothMovement24_InMotionAudio_FoleyT-Shirt.wav",
    "swoosh": "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Pull Swoosh Readout.wav",
    "woosh": "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav",
    "pop": "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav",
    "perc": "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav",
    "kalimba": "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Kalimba 3 Up_CB Sounddesign_APPlicable Sounds.wav",
    "deny": "Cinematic Sound Design - System & UI Feedback Elements/Interface Deny Low Fat Dark.wav",
    "bass": "344 Audio - Bass Drops & Downers Vol. 1/DSGNBass_Bass Drop & Downer Fast 16_344 Audio_Bass Drops & Downers.wav",
    "braam": "Jake Fielding - Cinematic Horn Braams/DSGNBram____Cinematic Horn Braam, Epic, Cinematic, Dark, Instrument, Huge-32.wav",
}

def build_audio(sents, E, duration, path):
    import sfx
    n = int(duration * SR)
    voice = K.voice_track(sents, duration)[:n]
    tr = new_track(duration)
    tr[:n] += voice
    hit = lambda t0, key, gain, **kw: add(tr, t0, sfx.clip(F[key], **kw), gain)
    ticks = sfx.onsets(F["tick"], 0.25, 12)
    t, k = 0.0, 0
    while t < duration - 0.3:                              # a soft clock tick under everything
        if not (E["scroll"] - 0.1 < t < E["J"]):
            hit(t, "tick", 0.05, start=ticks[k % len(ticks)], dur=0.12, hp=300)
        t += 1.0
        k += 1
    t = E["scroll"]
    while t < E["J"] - 0.1:                                 # the clock racing while he scrolls
        hit(t, "tick", 0.07, start=ticks[k % len(ticks)], dur=0.1, hp=300, rate=1.2)
        t += 0.225
        k += 1
    hit(0.0, "braam", 0.12, lp=2500)
    hit(E["1am"], "deny", 0.18, rate=0.9)
    hit(E["hour"], "kalimba", 0.14)
    hit(E["senate"], "pop", 0.15)
    hit(E["house"], "deny", 0.15, rate=1.1)
    hit(E["308"], "pop", 0.15, rate=1.1)
    hit(E["senate2"], "deny", 0.15, rate=1.1)
    hit(E["same"], "perc", 0.18)
    hit(E["F"] - 0.15, "cloth", 0.25, dur=0.6, lp=6000)
    hit(E["21"], "pop", 0.15)
    hit(E["25"], "pop", 0.15, rate=0.85)
    hit(E["scroll"], "woosh", 0.14)
    hit(E["march"] - 0.1, "cloth", 0.22, dur=0.6, lp=6000)
    hit(E["march"] + 0.3, "bass", 0.16, lp=2500)
    save_wav(tr, path, duration)

def remux(mp4, wav):
    import subprocess
    tmp = mp4 + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", tmp], check=True)
    os.replace(tmp, mp4)

# ------------------------------------------------------------------ overlay

GOLD = skia.Color(255, 205, 60)
GREEN = skia.Color(120, 220, 120)
BLUE = skia.Color(130, 170, 255)

def smooth01(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

def draw_hook(c, t, E, a):
    if a <= 0:
        return
    y = 300
    late = t > E["1am"] - 0.05
    for s, k in (("Sunday, 2:00 a.m.", False), ("= 1:00 a.m." if late else "1:59 a.m.", True)):
        ff = font("Bricolage-800", 96)
        wd = ff.measureText(s) + (40 if k else 0)
        x = W / 2 - wd / 2
        if k:
            c.drawRRect(tap.rrect(x, y - 82, x + wd, y + 26, 16), paint(tap.RED, a))
            c.drawString(s, x + 20, y, ff, paint(INK, a))
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

def card(c, t, rows, t_in, t_out, source, y0=1060):
    a = K.fade(t, t_in, t_out, 0.25)
    if a <= 0:
        return
    x0 = 70
    c.drawRRect(tap.rrect(x0, y0, 1010, y0 + 70 + 72 * len(rows), 18), paint(K.DARK_PILL, a))
    f1, f2 = font("JetBrainsMono-700", 30), font("Bricolage-800", 42)
    for k, (h, v, col, t0) in enumerate(rows):
        b = a * smooth01((t - t0) / 0.25)
        if b <= 0:
            continue
        y = y0 + 84 + 72 * k
        c.drawString(h, x0 + 26, y, f1, paint(MUTED, b))
        c.drawString(v, 990 - f2.measureText(v), y + 4, f2, paint(col, b))
    text_center(c, source, W / 2, y0 + 110 + 72 * len(rows), font("JetBrainsMono-500", 22), paint(MUTED, 0.9 * a))

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, t, E, K.fade(t, -1, E["B"] - 0.05, 0.2))
    tap.draw_captions(c, t, sents, cm)
    c.restore()
    lab = font("JetBrainsMono-700", 30)
    tags = [
        ("clock", "FALLS BACK", E["1am"] - 0.05, E["B"] - 0.1, -120, 170, tap.RED),
        ("guy", "STILL AWAKE", E["F"] + 0.3, E["G"] - 0.1, 230, 120, GOLD),
        ("clock", "1:00 TO 2:00 AGAIN", E["scroll"] - 0.05, E["J"] - 0.1, -140, 200, tap.RED),
    ]
    for name, text, t0, t1, dx, dy, col in tags:
        a = K.fade(t, t0, t1, 0.2)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, col, lab)
    pill(c, "1:00 A.M., AGAIN", W / 2, 1440, K.fade(t, E["hour"] - 0.1, E["C"] - 0.1, 0.15), tap.RED)
    card(c, t, [("SENATE, MAR 2022", "PASSED", GREEN, E["senate"] - 0.1), ("HOUSE, 2022", "NO VOTE", tap.RED, E["house"] - 0.1),
                ("HOUSE, JUL 2026", "308-117", GREEN, E["308"] - 0.1), ("SENATE, 2026", "NOT YET", tap.RED, E["senate2"] - 0.1)],
         E["senate"] - 0.15, E["F"] - 0.15, "Sources: Congress.gov via Wikipedia; States Newsroom, Jul 14 2026", y0=980)
    pill(c, "SAME YEAR: NEVER", W / 2, 1520, K.fade(t, E["same"] - 0.1, E["F"] - 0.15, 0.15), GOLD)
    card(c, t, [("HAWAII", "NO CHANGE", BLUE, E["hawaii"] - 0.1), ("ARIZONA (MOST)", "NO CHANGE", BLUE, E["arizona"] - 0.1)],
         E["hawaii"] - 0.15, E["G"] - 0.15, "Source: Fox 29, Oct 2026")
    card(c, t, [("FALL BACK, TUESDAY", "-21%", GREEN, E["21"] - 0.1), ("SPRING AHEAD, MONDAY", "+25%", tap.RED, E["25"] - 0.1)],
         E["21"] - 0.15, E["I"] - 0.15, "Heart attacks, Michigan hospitals (Sandhu, ACC 2014)")
    pill(c, "FREE HOUR: SPENT", W / 2, 1440, K.fade(t, E["scroll"] - 0.1, E["J"] - 0.1, 0.15), GOLD)
    pill(c, "NEXT CHANGE: MARCH 14, 2027", W / 2, 1440, K.fade(t, E["march"] - 0.1, speech_end + 1.4, 0.15), BLUE)
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
    K.run_blender("dst_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    if preview_times:                                   # CPU previews come out at half size
        from PIL import Image
        for f in frames:
            path = os.path.join(FRAMES, f"f_{f + 1:05d}.png")
            im = Image.open(path)
            if im.size != (1080, 1920):
                im.resize((1080, 1920), Image.LANCZOS).save(path)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0]
    if not preview_times:
        build_audio(sents, E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "dst" if preview_times else None)

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
