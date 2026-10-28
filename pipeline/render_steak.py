"""'The 8 a.m. steak guy': the guy eating a tomahawk steak in the back of a lecture, scored in aura, explained deadpan,
in a voxel lecture hall. From Austin's DM (a lecture-hall steak video, Oct 27); our own script.

python render_steak.py out.mp4 out.wav     full render (Blender frames are cached in out/steak/frames; delete them to re-render)
python render_steak.py preview 1.0,12.5    render and composite stills into preview/
python render_steak.py times               narrate and print the event times
python render_steak.py audio out.mp4 out.wav  rebuild only the soundtrack and swap it into an existing render

Facts: USDA FSIS safe minimum for beef steaks is 145 F with a 3 minute rest
(https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/safe-temperature-chart).
Omaha Steaks sells a 36 oz tomahawk ribeye, bone about seven inches, as a steak for sharing
(https://www.omahasteaks.com/blog/what-is-tomahawk-steak/). Aura points are the joke, not a measurement.
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
    ("A", "The guy eating a *steak* in the back of your *8{eight} a.m.* has the most *aura* on campus."),
    ("B", "He walks in late holding a *tomahawk ribeye.* *36{thirty-six} ounces,* sold as a steak for *sharing.*"),
    ("C", "He is not *sharing.*"),
    ("D", "No plate. No fork. The *7{seven} inch bone* is the *handle.*"),
    ("E", "Then he opens a full bottle of *ranch,* and the row in front of him starts *buffering.*"),
    ("F", "The USDA says steak is safe at *145{one forty-five} degrees* after a *3{three} minute* rest. He rested it during *attendance.*"),
    ("G", "The professor makes eye contact. He keeps *chewing.*"),
    ("H", "Scientists call this *main character energy.* He calls it *breakfast.*"),
]
EXTRA_GAP = {2: 0.1, 3: 0.15, 6: 0.15, 7: 0.35}
OUT = os.path.join(ROOT, "out", "steak")
FRAMES = os.path.join(OUT, "frames")

def events(sents, speech_end):
    w = lambda si, sub: tap.word_time(sents, si, sub)
    s = lambda si: sents[si]["t0"]
    end = lambda si: sents[si]["t0"] + sents[si]["dur"]
    return {"A": s(0), "B": s(1), "C": s(2), "D": s(3), "E": s(4), "F": s(5), "G": s(6), "H": s(7),
            "tomahawk": w(1, "tomahawk"), "ounces": w(1, "36"), "sold": w(1, "sold"), "sharing1": w(1, "sharing"),
            "C_end": end(2), "plate": w(3, "plate"), "fork": w(3, "fork"), "bone": w(3, "bone"), "handle": w(3, "handle"),
            "ranch": w(4, "ranch"), "buffering": w(4, "buffering"), "usda": w(5, "USDA"), "deg": w(5, "145"),
            "rest": w(5, "rest"), "rested": w(5, "rested"), "attendance": w(5, "attendance"),
            "eye": w(6, "eye"), "chewing": w(6, "chewing"), "main": w(7, "main"), "breakfast": w(7, "breakfast"),
            "speech_end": speech_end}

# ------------------------------------------------------------------ sound (recorded effects from the Sonniss GDC 2026 bundle, see sfx.py)

F = {
    "walla": "Sonik Sound Library - Spanish Wallas/CRWDWalla_Crowd, Walla, Dense Immersive Group of Adults, After or Befor a Show, Exterior, Spanish-Stereo_KSL_KS014.wav",
    "door": "InMotionAudio - USA Hotel/DOORMetl_StairWellDoor01_InMotionAudio_USAHotel.wav",
    "steps": "TheWorkRoom - Flip Flops/FFG002.wav",
    "seat": "344 Audio - Cinema Experience Vol. 1/FOLYProp_Sitting Down, Creaky Seat, Squeaks 3_344 Audio_CInema Experience.wav",
    "chew": "344 Audio - Dinosaurs Vol. 2/ANMLRept_Dinosaur Eating Meat 01_344 Audio_Dinosaurs Vol 2.wav",
    "squelch": "Epic Stock Media - Tower Defense Game/WOODImpt_Hit Blood Spill Splat Wood Impact Light Hit Squelch Small Thump 03_ESM_TDG.wav",
    "cough": "Epic Stock Media - AAA Game Character Police Officer/HMNCough_Police Officer Cough Vocal Male 11.wav",
    "swoosh": "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Pull Swoosh Readout.wav",
    "woosh": "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav",
    "pop": "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav",
    "perc": "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav",
    "kalimba": "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Kalimba 3 Up_CB Sounddesign_APPlicable Sounds.wav",
    "coins": "Cinematic Sound Design - UI Interaction Elements/Ting Coins.wav",
    "deny": "Cinematic Sound Design - System & UI Feedback Elements/Interface Deny Low Fat Dark.wav",
    "powerup": "Epic Stock Media - Anime Game/DSGNStngr_Power Up Bright Positive Successful Light Saturation Crash Shimmer 05_ESM_AG.wav",
    "bass": "344 Audio - Bass Drops & Downers Vol. 1/DSGNBass_Bass Drop & Downer Fast 16_344 Audio_Bass Drops & Downers.wav",
    "braam": "Jake Fielding - Cinematic Horn Braams/DSGNBram____Cinematic Horn Braam, Epic, Cinematic, Dark, Instrument, Huge-32.wav",
}

def build_audio(sents, E, duration, path):
    import sfx
    import steak_anim as SA
    n = int(duration * SR)
    voice = K.voice_track(sents, duration)[:n]
    beds = sfx.bed(F["walla"], duration, 0.012, start=20.0, lp=900)    # the electric hum bed read as a buzz (Austin, Oct 27)
    env = np.sqrt(np.convolve(voice ** 2, np.ones(2400) / 2400, "same"))
    beds *= 1 - 0.4 * np.clip(env / 0.08, 0, 1)
    tr = new_track(duration)
    tr[:n] += voice + beds
    hit = lambda t0, key, gain, **kw: add(tr, t0, sfx.clip(F[key], **kw), gain)
    hit(0.0, "bass", 0.1, lp=2500)
    chew = sfx.onsets(F["chew"], 0.25, 8)
    for k, b in enumerate(SA.bites(E, duration)):
        hit(b - 0.05, "chew", 0.16, start=chew[k % len(chew)], dur=0.45, lp=4000, hp=150)
    hit(E["B"] - 0.3, "door", 0.32, lp=5000)
    steps = sfx.onsets(F["steps"], 0.25, 10)
    t, k = SA.enter_time(E), 0
    while t < SA.arrive_time(E):
        hit(t, "steps", 0.16, start=steps[k % len(steps)], dur=0.2, lp=2500, hp=90)
        t += SA.STEP
        k += 1
    hit(SA.arrive_time(E) + 0.1, "seat", 0.28)
    for j, key in enumerate(("tomahawk", "C_end", "handle", "ranch", "attendance")):
        hit(E[key] + 0.05, "kalimba", 0.22, rate=1.0 + 0.06 * j)
        hit(E[key] + 0.08, "coins", 0.14)
    hit(E["sold"], "perc", 0.2)
    hit(E["C"] - 0.05, "deny", 0.3)
    hit(E["plate"], "pop", 0.18, rate=0.9)
    hit(E["fork"], "pop", 0.18, rate=1.0)
    hit(E["ranch"] - 0.1, "squelch", 0.3)
    hit(E["ranch"] + 0.6, "squelch", 0.22, rate=1.15)
    for j in range(6):
        hit(SA.turn_start(E) + 0.28 * j, "perc", 0.12, rate=1.3)
    hit(E["F"] - 0.3, "swoosh", 0.16, rate=1.1)
    hit(E["deg"], "pop", 0.16)
    hit(E["attendance"] + 0.4, "cough", 0.12, lp=3000)
    hit(E["G"] - 0.3, "woosh", 0.2)
    hit(E["eye"], "deny", 0.22, rate=0.8)
    hit(E["chewing"], "powerup", 0.38)
    hit(E["chewing"], "bass", 0.22, lp=3000)
    hit(E["H"] - 0.2, "braam", 0.14, lp=2500)
    save_wav(tr, path, duration)

def remux(mp4, wav):
    import subprocess
    tmp = mp4 + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", tmp], check=True)
    os.replace(tmp, mp4)

# ------------------------------------------------------------------ overlay

PURPLE = skia.Color(190, 130, 255)

def draw_hook(c, a):
    if a <= 0:
        return
    f = font("Bricolage-800", 92)
    y = 290
    for s, k in (("The 8 a.m. steak guy", False), ("has the most aura", True)):
        size = 92
        ff = f
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

def aura_total(t, E):
    import steak_anim as SA
    total = 0.0
    for t0, pts in SA.aura_awards(E):
        total += pts * smooth01((t - t0) / 0.5)
    return total

def smooth01(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

def draw_counter(c, t, E):
    import steak_anim as SA
    x0, y0 = 54, 452
    total = aura_total(t, E)
    big = t >= E["H"]
    f_lab = font("JetBrainsMono-700", 28)
    f_num = font("JetBrainsMono-800", 64)
    num = f"{int(round(total)):,}"
    w = max(300, f_num.measureText(num) + 60)
    c.drawRRect(tap.rrect(x0, y0, x0 + w, y0 + 128, 18), paint(K.DARK_PILL, 1.0))
    c.drawString("AURA", x0 + 28, y0 + 40, f_lab, paint(PURPLE))
    c.drawString(num, x0 + 28, y0 + 106, f_num, paint(INK))
    # "+N" pops
    for t0, pts in SA.aura_awards(E):
        u = (t - t0) / 1.1
        if 0 <= u < 1:
            a = min(1.0, (1 - u) * 2.5)
            size = 92 if pts >= 10000 else 50
            ff = font("JetBrainsMono-800", size)
            s = f"+{pts:,} AURA"
            yy = y0 + 200 - 60 * u + (620 if pts >= 10000 else 0)
            xx = x0 + 20 if pts < 10000 else W / 2 - ff.measureText(s) / 2
            c.drawString(s, xx, yy, ff, paint(PURPLE, a))

def spinner(c, x, y, t, a):
    if a <= 0:
        return
    c.drawCircle(x, y, 30, paint(K.DARK_PILL, a))
    for k in range(8):
        ang = 2 * math.pi * k / 8 + math.floor(t * 10) * 2 * math.pi / 8
        al = a * (0.25 + 0.75 * k / 7)
        c.drawCircle(x + 17 * math.cos(ang), y + 17 * math.sin(ang), 5, paint(INK, al))

def dashed(c, p, q, a, color):
    n = 24
    for k in range(0, n, 2):
        u0, u1 = k / n, (k + 1) / n
        c.drawLine(p[0] + (q[0] - p[0]) * u0, p[1] + (q[1] - p[1]) * u0, p[0] + (q[0] - p[0]) * u1,
                   p[1] + (q[1] - p[1]) * u1, tap.stroke(color, 5, a))

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    import steak_anim as SA
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, K.fade(t, -1, E["B"] - 0.05, 0.2))
    tap.draw_captions(c, t, sents, cm)
    c.restore()
    draw_counter(c, t, E)
    lab = font("JetBrainsMono-700", 30)
    # (anchor, text, start, end, dx, dy, color)
    tags = [
        ("steak", "TOMAHAWK RIBEYE: 36 OZ", E["tomahawk"] - 0.1, E["C"] - 0.1, -160, -260, ORANGE),
        ("bone", "7 IN BONE = HANDLE", E["bone"] - 0.1, E["E"] - 0.2, -150, -240, ORANGE),
        ("ranch", "RANCH: FULL BOTTLE", E["ranch"] - 0.1, E["buffering"] - 0.1, -170, -230, skia.Color(120, 220, 140)),
    ]
    for name, text, t0, t1, dx, dy, col in tags:
        a = K.fade(t, t0, t1, 0.2)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, col, lab)
    # the row in front buffering
    a = K.fade(t, SA.turn_start(E) + 0.2, E["F"] - 0.1, 0.2)
    if a > 0:
        for k in range(len([n for n in A if n.startswith("turn")])):
            p = K.anchor(A, f"turn{k}", Fr)
            if p and 60 < p[0] < 1020 and 560 < p[1] < 1500:
                spinner(c, p[0], p[1], t + 0.13 * k, a)
    pill(c, "SOLD AS: SERVES 2", W / 2, 1440, K.fade(t, E["sold"] - 0.1, E["C"] - 0.05, 0.2), INK)
    pill(c, "SERVING: 1", W / 2, 1440, K.fade(t, E["C"] - 0.05, E["D"] - 0.1, 0.2), tap.RED)
    pill(c, "PLATE: NO   FORK: NO", W / 2, 1440, K.fade(t, E["fork"] - 0.1, E["E"] - 0.2, 0.2), tap.RED)
    pill(c, "USDA: 145°F + 3 MIN REST", W / 2, 1440, K.fade(t, E["deg"] - 0.1, E["rested"] - 0.05, 0.2), tap.GREEN)
    pill(c, "RESTED DURING: ATTENDANCE", W / 2, 1440, K.fade(t, E["rested"] - 0.05, E["G"] - 0.15, 0.2), ORANGE)
    pill(c, "EYE CONTACT: MADE", W / 2, 1440, K.fade(t, E["eye"] - 0.15, E["chewing"] - 0.1, 0.15), tap.RED)
    pill(c, "CHEWING: CONTINUED", W / 2, 1440, K.fade(t, E["chewing"] - 0.1, E["H"] - 0.15, 0.15), tap.GREEN)
    a = K.fade(t, E["deg"] - 0.1, E["G"] - 0.15, 0.3)
    if a > 0:
        text_center(c, "Source: USDA FSIS safe minimum temperature chart", W / 2, 1535, font("JetBrainsMono-500", 26), paint(MUTED, 0.9 * a))
    if t > speech_end + 0.1:
        a = smooth01((t - speech_end - 0.1) / 0.4)
        text_center(c, "@overthought.daily", W / 2, 1500, font("JetBrainsMono-500", 32), paint(MUTED, a))

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
    K.run_blender("steak_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0]
    if not preview_times:
        build_audio(sents, E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "steak" if preview_times else None)

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
