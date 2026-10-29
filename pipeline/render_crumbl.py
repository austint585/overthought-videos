"""'The man who took down Crumbl': a deadpan voxel short. Crumbl's sales and closures are real; the culprit is the joke:
the Santa Cruz paleo coach who paid people outside Crumbl not to buy cookies. From Austin's DM (a @millionaire.mindset_club
reel, Oct 28, with his note to blame the paleo guy "for the sake of the joke"); our own script.

python render_crumbl.py out.mp4 out.wav     full render (Blender frames are cached in out/crumbl/frames)
python render_crumbl.py preview 1.0,12.5    render and composite stills into preview/
python render_crumbl.py times               narrate and print the event times

Facts and links: ops/episodes/2026-10-28-crumbl-paleo.md (KUTV/Restaurant Business Oct 2026 for the 70% drop, 57 closed
and 55 for sale; Daily Dot Mar 2025 for the $100 offer, the CEO's reply and 5.8M + 1.3M views; CSPI for 720 calories
per cookie against a 590-calorie Big Mac).
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
    ("A", "*Crumbl's* sales this August were down *70{seventy} percent* from two years earlier."),
    ("B", "At least *57{fifty-seven}* stores have closed this year. *55{fifty-five}* more are *for sale.*"),
    ("C", "Economists blame *the economy.*"),
    ("D", "But in *2025{twenty twenty-five},* a paleo coach from *Santa Cruz* stood outside Crumbl and paid people *not* to buy cookies."),
    ("E", "Up to *a hundred dollars* a person."),
    ("F", "Crumbl's *CEO* told everyone to take the money and order *delivery.*"),
    ("G", "He *doubled down.* His videos got over *seven million* views."),
    ("H", "Every cookie he stopped was about *720{seven hundred twenty} calories.* A *Big Mac* is *590{five ninety}.*"),
    ("I", "Officially, it's *the economy.* Unofficially, it was *one man* with a *wallet.*"),
    ("J", "Crumbl is *down.* Who does he take out *next?*"),
]
EXTRA_GAP = {2: 0.1, 3: 0.15, 6: 0.1, 7: 0.1, 8: 0.2, 9: 0.25}
OUT = os.path.join(ROOT, "out", "crumbl")
FRAMES = os.path.join(OUT, "frames")

def wn(sents, si, sub, nth=0):
    s = sents[si]
    hits = [i for i, w in enumerate(s["words"]) if sub.lower() in w["display"].lower()]
    return s["abs_starts"][hits[min(nth, len(hits) - 1)]] if hits else s["t0"]

def events(sents, speech_end):
    w = lambda si, sub, n=0: wn(sents, si, sub, n)
    s = lambda si: sents[si]["t0"]
    E = {k: s(i) for i, k in enumerate("ABCDEFGHIJ")}
    E.update({"70": w(0, "70"), "57": w(1, "57"), "55": w(1, "55"), "sale": w(1, "sale"), "economy": w(2, "economy"),
              "2025": w(3, "2025"), "santa": w(3, "Santa"), "not": w(3, "not"), "hundred": w(4, "hundred"),
              "ceo": w(5, "CEO"), "delivery": w(5, "delivery"), "doubled": w(6, "doubled"), "million": w(6, "million"),
              "720": w(7, "720"), "bigmac": w(7, "Big"), "590": w(7, "590"), "officially": w(8, "Officially"),
              "unofficially": w(8, "Unofficially"), "Unofficially": w(8, "Unofficially"), "wallet": w(8, "wallet"),
              "down": w(9, "down"), "next": w(9, "next"), "speech_end": speech_end})
    return E

# ------------------------------------------------------------------ sound (recorded effects from the Sonniss GDC 2026 bundle, see sfx.py)

F = {
    "street": "Epic Stock Media - Public Spaces - Urban Life Exteriors/AMBTown_City Courtyard Calm Street Distant Traffic Children Playing 03_ESM_CPS.wav",
    "steps": "TheWorkRoom - Flip Flops/FFG002.wav",
    "cash": "344 Audio - Casino Cards Vol. 1/GAMECas_Dealing 3_344 Audio_Casino Cards Vol 1.wav",
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
    tr[:n] += voice
    street = sfx.clip(F["street"], dur=duration, lp=6000, hp=150) * 0.05     # quiet street air, no hum or drone
    add(tr, 0.0, street[:n], 1.0)
    hit = lambda t0, key, gain, **kw: add(tr, t0, sfx.clip(F[key], **kw), gain)
    hit(0.0, "braam", 0.12, lp=2500)
    hit(E["70"], "deny", 0.18)
    hit(E["57"], "pop", 0.15)
    hit(E["55"], "pop", 0.15, rate=1.15)
    hit(E["economy"], "perc", 0.16)
    hit(E["santa"], "swoosh", 0.18)
    for tm in (E["not"], E["delivery"], E["million"], E["720"], E["officially"]):
        hit(tm - 0.05, "cash", 0.22, dur=0.5)
        hit(tm + 0.2, "kalimba", 0.12, rate=1.1)
    hit(E["hundred"], "pop", 0.16, rate=0.9)
    hit(E["ceo"], "woosh", 0.15)
    hit(E["million"], "powerup", 0.18)
    hit(E["720"] + 0.6, "pop", 0.14)
    hit(E["590"], "pop", 0.14, rate=1.2)
    hit(E["wallet"], "perc", 0.2, rate=0.9)
    hit(E["down"], "bass", 0.2, lp=3000)
    hit(E["next"] - 0.5, "kalimba", 0.16, rate=0.8)
    save_wav(tr, path, duration)

def remux(mp4, wav):
    import subprocess
    tmp = mp4 + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", tmp], check=True)
    os.replace(tmp, mp4)

# ------------------------------------------------------------------ overlay

GOLD = skia.Color(255, 205, 60)
PINK = skia.Color(255, 140, 180)
GREEN = skia.Color(120, 220, 120)

def smooth01(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

def draw_hook(c, a):
    if a <= 0:
        return
    y = 300
    for s, k in (("Crumbl sales:", False), ("-70%", True)):
        ff = font("Bricolage-800", 104)
        wd = ff.measureText(s) + (40 if k else 0)
        x = W / 2 - wd / 2
        if k:
            c.drawRRect(tap.rrect(x, y - 88, x + wd, y + 28, 16), paint(tap.RED, a))
            c.drawString(s, x + 20, y, ff, paint(INK, a))
        else:
            c.drawString(s, x, y, ff, paint(INK, a))
        y += 124

def pill(c, text, cx, y, a, color=INK, bg=K.DARK_PILL, size=34):
    if a <= 0:
        return
    f = font("JetBrainsMono-700", size)
    w = f.measureText(text)
    c.drawRRect(tap.rrect(cx - w / 2 - 22, y - size - 10, cx + w / 2 + 22, y + 16, 14), paint(bg, a))
    c.drawString(text, cx - w / 2, y, f, paint(color, a))

def draw_facts(c, t, E):
    a = K.fade(t, E["70"] - 0.1, E["C"] - 0.15, 0.25)
    if a <= 0:
        return
    x0, y0 = 70, 1060
    rows = [("SALES, AUG VS 2024", "-70%", E["70"] - 0.1), ("CLOSED IN 2026", "57+", E["57"] - 0.1),
            ("FOR SALE", "55", E["55"] - 0.1)]
    c.drawRRect(tap.rrect(x0, y0, 1010, y0 + 70 + 72 * len(rows), 18), paint(K.DARK_PILL, a))
    f1, f2 = font("JetBrainsMono-700", 30), font("Bricolage-800", 46)
    for k, (h, v, t0) in enumerate(rows):
        b = a * smooth01((t - t0) / 0.25)
        if b <= 0:
            continue
        y = y0 + 84 + 72 * k
        c.drawString(h, x0 + 26, y, f1, paint(MUTED, b))
        c.drawString(v, 990 - f2.measureText(v), y + 4, f2, paint(PINK, b))
    text_center(c, "Source: Restaurant Business via KUTV, Oct 2026", W / 2, 1385,
                font("JetBrainsMono-500", 22), paint(MUTED, 0.9 * a))

def draw_phone(c, t, E):
    a = K.fade(t, E["ceo"] - 0.15, E["G"] - 0.1, 0.25)
    if a <= 0:
        return
    rise = 1 - smooth01((t - E["ceo"] + 0.15) / 0.35)
    x0, y0 = 150, 980 + 140 * rise
    c.drawRRect(tap.rrect(x0, y0, W - x0, y0 + 300, 30), paint(skia.Color(236, 238, 242), a))
    dk, md = skia.Color(20, 20, 24), skia.Color(100, 100, 110)
    c.drawCircle(x0 + 70, y0 + 70, 34, paint(skia.Color(240, 120, 160), a))
    c.drawString("CRUMBL CEO", x0 + 120, y0 + 64, font("JetBrainsMono-700", 30), paint(md, a))
    c.drawString("Jan 2025", x0 + 120, y0 + 100, font("JetBrainsMono-700", 26), paint(md, a))
    c.drawString("\"just take the money", x0 + 40, y0 + 180, font("Bricolage-800", 46), paint(dk, a))
    c.drawString("and order delivery\"", x0 + 40, y0 + 240, font("Bricolage-800", 46), paint(dk, a))
    text_center(c, "Source: Daily Dot, Mar 2025", W / 2, y0 + 345, font("JetBrainsMono-500", 22), paint(MUTED, 0.9 * a))

def draw_views(c, t, E):
    a = K.fade(t, E["million"] - 0.4, E["H"] - 0.1, 0.25)
    if a <= 0:
        return
    u = smooth01((t - E["million"] + 0.4) / 1.0)
    v = 7.1 * u
    c.drawRRect(tap.rrect(250, 1080, 830, 1230, 24), paint(K.DARK_PILL, a))
    text_center(c, "HIS VIDEOS", W / 2, 1130, font("JetBrainsMono-700", 30), paint(MUTED, a))
    text_center(c, f"{v:.1f}M views", W / 2, 1205, font("Bricolage-800", 64), paint(GREEN, a))
    text_center(c, "5.8M on X + 1.3M on TikTok (Daily Dot)", W / 2, 1270, font("JetBrainsMono-500", 22), paint(MUTED, 0.9 * a))

def draw_cal(c, t, E):
    a = K.fade(t, E["720"] - 0.15, E["I"] - 0.1, 0.25)
    if a <= 0:
        return
    x0, y0 = 90, 1040
    c.drawRRect(tap.rrect(x0 - 20, y0 - 20, W - x0 + 20, y0 + 290, 22), paint(K.DARK_PILL, a))
    f1, f2 = font("JetBrainsMono-700", 30), font("Bricolage-800", 44)
    full = W - 2 * x0 - 40
    for k, (name, cal, col, t0) in enumerate((("1 CRUMBL COOKIE", 720, PINK, E["720"] - 0.1),
                                              ("1 BIG MAC", 590, GOLD, E["bigmac"] - 0.1))):
        b = a * smooth01((t - t0) / 0.25)
        if b <= 0:
            continue
        y = y0 + 40 + 120 * k
        c.drawString(name, x0 + 20, y, f1, paint(MUTED, b))
        wbar = full * (cal / 720) * smooth01((t - t0) / 0.6)
        c.drawRRect(tap.rrect(x0 + 20, y + 18, x0 + 20 + wbar, y + 70, 10), paint(col, b))
        lab = f"{cal} cal"
        c.drawString(lab, x0 + 36, y + 60, f2, paint(skia.Color(20, 20, 24), b))
    text_center(c, "Source: CSPI (menu lists 180 cal per quarter cookie)", W / 2, y0 + 315,
                font("JetBrainsMono-500", 22), paint(MUTED, 0.9 * a))

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, K.fade(t, -1, E["B"] - 0.05, 0.2))
    tap.draw_captions(c, t, sents, cm)
    c.restore()
    lab = font("JetBrainsMono-700", 30)
    tags = [
        ("lease", "FORMER CUSTOMER", E["B"] + 0.6, E["C"] - 0.1, 120, -160, MUTED),
        ("coach", "PALEO COACH, SANTA CRUZ", E["santa"] - 0.1, E["E"] - 0.1, 140, -150, GREEN),
        ("cust", "OFFER: $100", E["hundred"] - 0.1, E["F"] - 0.1, 120, -140, GOLD),
        ("coach", "STATUS: DOUBLED DOWN", E["doubled"] - 0.1, E["million"] - 0.4, 180, 140, GREEN),
        ("shop", "LIGHTS: OUT", E["down"] - 0.05, E["next"] - 0.9, -60, 150, tap.RED),
        ("donut", "NEXT?", E["next"] - 0.4, speech_end + 1.4, -60, 380, GOLD),
    ]
    for name, text, t0, t1, dx, dy, col in tags:
        a = K.fade(t, t0, t1, 0.2)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, col, lab)
    draw_facts(c, t, E)
    draw_phone(c, t, E)
    draw_views(c, t, E)
    draw_cal(c, t, E)
    pill(c, "OFFICIAL CAUSE: THE ECONOMY", W / 2, 1440, K.fade(t, E["economy"] - 0.1, E["D"] - 0.1, 0.15), MUTED)
    pill(c, "OFFICIAL: THE ECONOMY", W / 2, 1440, K.fade(t, E["officially"] - 0.05, E["unofficially"] - 0.05, 0.15), MUTED)
    pill(c, "UNOFFICIAL: ONE MAN, ONE WALLET", W / 2, 1440, K.fade(t, E["unofficially"] - 0.05, E["J"] - 0.1, 0.15), GOLD)
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
    K.run_blender("crumbl_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0]
    if not preview_times:
        build_audio(sents, E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "crumbl" if preview_times else None)

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
