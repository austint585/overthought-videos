"""'Napoleon wakes up in 2026': a deadpan voxel short. Napoleon wakes up in a museum gallery next to one of his own hats,
looks himself up, and learns what happened to his height, his money and Waterloo. From Austin's DM (a @whatif.bros
"what if a dictator woke up in 2026" reel, Oct 27, "make your own take on this"); our own subject and script.

python render_napoleon.py out.mp4 out.wav     full render (Blender frames are cached in out/napoleon/frames)
python render_napoleon.py preview 1.0,12.5    render and composite stills into preview/
python render_napoleon.py times               narrate and print the event times

Facts (every one is in ops/episodes/2026-10-28-napoleon-2026.md with its link): died on Saint Helena in 1821; one of his
bicorne hats sold at Osenat, Fontainebleau, on Nov 19 2023 for about 1.93 million euros, and he owned about 120 of them;
he was about 1.69 m, average for a Frenchman then, and the "five foot two" was in French units; British cartoonists
(Gillray's "Little Boney") drew him tiny; the "Napoleon complex" is named after him; the franc germinal dates from 1803 and
euro cash replaced the franc in 2002; ABBA won Eurovision 1974 with "Waterloo".
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
    ("A", "*Napoleon* wakes up in *2026{twenty twenty-six}.*"),
    ("B", "Last thing he remembers: *Saint Helena,* *1821{eighteen twenty-one}.*"),
    ("C", "He's in a *museum,* next to one of his own *hats.*"),
    ("D", "One of them sold in *2023{twenty twenty-three}* for *1.9{one point nine} million euros.* He owned about *a hundred and twenty.*"),
    ("E", "He looks himself up. The internet says he was *short.*"),
    ("F", "He was about *one sixty-nine.* *Average* for a Frenchman back then."),
    ("G", "British cartoonists drew him *tiny,* and it *stuck.* There's a *complex* named after him."),
    ("H", "His *franc* got replaced by the *euro* in *2002{two thousand two}.*"),
    ("I", "He checks the weather in *Moscow.* He closes the app."),
    ("J", "He asks about *Waterloo.* It's an *ABBA* song now. It won *Eurovision.*"),
    ("K", "He has now lost Waterloo *twice.*"),
]
EXTRA_GAP = {2: 0.1, 4: 0.15, 7: 0.1, 8: 0.15, 9: 0.1, 10: 0.35}
OUT = os.path.join(ROOT, "out", "napoleon")
FRAMES = os.path.join(OUT, "frames")

def wn(sents, si, sub, nth=0):
    s = sents[si]
    hits = [i for i, w in enumerate(s["words"]) if sub.lower() in w["display"].lower()]
    return s["abs_starts"][hits[min(nth, len(hits) - 1)]] if hits else s["t0"]

def events(sents, speech_end):
    w = lambda si, sub, n=0: wn(sents, si, sub, n)
    s = lambda si: sents[si]["t0"]
    E = {k: s(i) for i, k in enumerate("ABCDEFGHIJK")}
    E.update({"wakes": w(0, "wakes"), "2026": w(0, "2026"), "helena": w(1, "Helena"), "1821": w(1, "1821"),
              "museum": w(2, "museum"), "hats": w(2, "hats"), "sold": w(3, "sold"), "million": w(3, "million"),
              "hundred": w(3, "hundred"), "looks": w(4, "looks"), "short": w(4, "short"), "169": w(5, "sixty"),
              "average": w(5, "Average"), "tiny": w(6, "tiny"), "stuck": w(6, "stuck"), "complex": w(6, "complex"),
              "franc": w(7, "franc"), "euro": w(7, "euro"), "moscow": w(8, "Moscow"), "closes": w(8, "closes"),
              "waterloo": w(9, "Waterloo"), "abba": w(9, "ABBA"), "eurovision": w(9, "Eurovision"),
              "twice": w(10, "twice"), "speech_end": speech_end})
    return E

# ------------------------------------------------------------------ sound (recorded effects from the Sonniss GDC 2026 bundle, see sfx.py)

F = {
    "bells": "Ivo Vicic - Church Bells/04 Church Bells, Near Distance, In Church Tower-3 Different Bell 02.wav",
    "clock": "344 Audio - Antique Clocks/CLOCKTick_Crooked Antique Clock_344 Audio_Antique Clocks.wav",
    "steps": "TheWorkRoom - Flip Flops/FFG002.wav",
    "swoosh": "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Pull Swoosh Readout.wav",
    "woosh": "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav",
    "pop": "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav",
    "perc": "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav",
    "kalimba": "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Kalimba 3 Up_CB Sounddesign_APPlicable Sounds.wav",
    "deny": "Cinematic Sound Design - System & UI Feedback Elements/Interface Deny Low Fat Dark.wav",
    "dizzy": "Cinematic Sound Design - Cartoon Bloopers/Cartoon Confused Dizzy.wav",
    "musicbox": "Sonic Bat - Music Boxes/SBmb_Music Box A 013.wav",
    "wind": "Jake Fielding - Interior Wind Rain and Storms/HAIL_Hail on Door Window, UVPC_JF_INT Storm.wav",
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
    hit(E["wakes"], "bells", 0.14, dur=2.0, lp=4000)
    ticks = sfx.onsets(F["clock"], 0.3, 8)
    t, k = E["B"], 0
    while t < E["C"] - 0.2:
        hit(t, "clock", 0.16, start=ticks[k % len(ticks)], dur=0.18)
        t += 0.5
        k += 1
    hit(E["hats"], "pop", 0.18)
    hit(E["million"], "kalimba", 0.18)
    hit(E["hundred"], "perc", 0.16, rate=1.1)
    hit(E["looks"], "swoosh", 0.16)
    hit(E["short"], "deny", 0.18, rate=1.1)
    hit(E["169"], "kalimba", 0.16, rate=1.1)
    hit(E["tiny"], "dizzy", 0.14, dur=1.2)
    hit(E["complex"], "perc", 0.16)
    hit(E["franc"], "woosh", 0.14)
    hit(E["euro"], "pop", 0.16, rate=1.2)
    hit(E["moscow"], "wind", 0.10, dur=1.6, lp=3000, hp=150)
    hit(E["closes"], "deny", 0.18, rate=0.9)
    hit(E["abba"], "musicbox", 0.14, dur=2.2)
    hit(E["twice"], "bass", 0.2, lp=3000)
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
    for s, k in (("Napoleon wakes up", False), ("in 2026", True)):
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

def card(c, x0, y0, x1, y1, a):
    c.drawRRect(tap.rrect(x0, y0, x1, y1, 20), paint(CARD, a))

def rows_card(c, t, rows, y0, a, source=None):
    """rows: (label, value, t_in, color). A dark card bottom-middle with values popping in on their words."""
    if a <= 0:
        return
    x0, x1 = 70, 1010
    card(c, x0, y0, x1, y0 + 60 + 74 * len(rows), a)
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

def draw_search(c, t, E):
    """A phone-style search result: 'napoleon height' -> short, then the real number with a strike on the myth."""
    a = K.fade(t, E["looks"] - 0.1, E["H"] - 0.15, 0.25)
    if a <= 0:
        return
    x0, y0, x1 = 110, 960, 970
    c.drawRRect(tap.rrect(x0, y0, x1, y0 + 430, 34), paint(skia.Color(240, 241, 244), a))
    c.drawRRect(tap.rrect(x0 + 30, y0 + 30, x1 - 30, y0 + 104, 37), paint(skia.Color(222, 224, 230), a))
    c.drawString("napoleon height", x0 + 66, y0 + 80, font("JetBrainsMono-700", 34), paint(skia.Color(40, 40, 48), a))
    dk = skia.Color(20, 20, 24)
    b = a * smooth01((t - E["short"] + 0.05) / 0.2)
    if b > 0:
        c.drawString("\"famously short\"", x0 + 40, y0 + 190, font("Bricolage-800", 54), paint(dk, b))
        c.drawString("5 pieds 2 pouces (French units)", x0 + 40, y0 + 240, font("JetBrainsMono-700", 26),
                     paint(skia.Color(100, 100, 110), b))
        st = smooth01((t - E["169"] + 0.1) / 0.25)
        if st > 0:
            p = tap.stroke(tap.RED, 7, b)
            c.drawLine(x0 + 34, y0 + 172, x0 + 34 + (480 * st), y0 + 172, p)
    g = a * smooth01((t - E["169"] + 0.05) / 0.25)
    if g > 0:
        c.drawString("about 1.69 m (5 ft 6 or 7)", x0 + 40, y0 + 320, font("Bricolage-800", 48), paint(skia.Color(30, 130, 60), g))
        av = smooth01((t - E["average"]) / 0.25)
        c.drawString("average for a Frenchman of his time", x0 + 40, y0 + 372, font("JetBrainsMono-700", 26),
                     paint(skia.Color(100, 100, 110), g * av))

def draw_cartoon(c, t, E):
    a = K.fade(t, E["tiny"] - 0.1, E["H"] - 0.15, 0.25)
    if a <= 0:
        return
    pill(c, "BRITISH CARTOONS: \"LITTLE BONEY\"", W / 2, 1440, a, GOLD)

def draw_franc(c, t, E):
    a = K.fade(t, E["H"] - 0.1, E["I"] - 0.15, 0.25)
    rows_card(c, t, [("FRANC", "1803 to 2002", E["franc"] - 0.05, GOLD),
                     ("NOW", "the euro", E["euro"] - 0.05, BLUE)], 1050, a,
              "Sources: franc germinal 1803; euro cash replaced it by March 2002")

def draw_weather(c, t, E):
    a = K.fade(t, E["moscow"] - 0.1, E["J"] - 0.15, 0.25)
    if a <= 0:
        return
    x0, y0, x1 = 170, 980, 910
    c.drawRRect(tap.rrect(x0, y0, x1, y0 + 300, 34), paint(skia.Color(60, 110, 190), a))
    c.drawString("WEATHER", x0 + 40, y0 + 70, font("JetBrainsMono-700", 30), paint(skia.Color(210, 225, 255), a))
    c.drawString("Moscow", x0 + 40, y0 + 160, font("Bricolage-800", 76), paint(INK, a))
    c.drawString("winter is coming", x0 + 40, y0 + 230, font("JetBrainsMono-700", 32), paint(skia.Color(220, 232, 255), a))
    for k in range(9):
        fx = x0 + 520 + 160 * ((k * 37) % 9) / 9
        fy = y0 + 60 + ((t * 120 + k * 61) % 220)
        c.drawCircle(fx, fy, 6, paint(INK, 0.8 * a))
    cl = smooth01((t - E["closes"]) / 0.3)
    if cl > 0:
        pill(c, "APP CLOSED", W / 2, 1440, a * cl, tap.RED)

def draw_waterloo(c, t, E):
    a = K.fade(t, E["abba"] - 0.3, E["K"] - 0.1, 0.25)
    rows_card(c, t, [("WATERLOO", "ABBA, 1974", E["abba"] - 0.05, GOLD),
                     ("RESULT", "won Eurovision", E["eurovision"] - 0.05, GREEN)], 1050, a,
              "Source: Eurovision Song Contest 1974, Brighton")

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, K.fade(t, -1, E["B"] - 0.05, 0.2))
    tap.draw_captions(c, t, sents, cm)
    c.restore()
    lab = font("JetBrainsMono-700", 30)
    tags = [
        ("hero", "LAST SAVE: 1821", E["helena"] - 0.1, E["C"] - 0.1, 170, -150, ORANGE),
        ("hat", "HIS HAT (ONE OF ~120)", E["hats"] - 0.1, E["E"] - 0.1, -60, -230, GOLD),
        ("hero", "COMPLEX: NAMED AFTER HIM", E["complex"] - 0.1, E["H"] - 0.1, 140, -170, tap.RED),
        ("hero", "WATERLOO RECORD: 0-2", E["twice"] - 0.05, speech_end + 1.0, 150, -160, tap.RED),
    ]
    for name, text, t0, t1, dx, dy, col in tags:
        a = K.fade(t, t0, t1, 0.2)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, col, lab)
    rows_card(c, t, [("SOLD", "Nov 2023", E["sold"] - 0.05, INK),
                     ("PRICE", "1.93 million euros", E["million"] - 0.05, GOLD),
                     ("HATS HE OWNED", "about 120", E["hundred"] - 0.05, INK)], 1010,
              K.fade(t, E["D"] - 0.1, E["E"] - 0.15, 0.25), "Source: Osenat auction, Fontainebleau, Nov 19 2023")
    draw_search(c, t, E)
    draw_cartoon(c, t, E)
    draw_franc(c, t, E)
    draw_weather(c, t, E)
    draw_waterloo(c, t, E)
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
    K.run_blender("napoleon_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0]
    if not preview_times:
        build_audio(sents, E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "napoleon" if preview_times else None)

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
