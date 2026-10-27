"""'Schrodinger's situationship': the 1935 cat-in-a-box thought experiment run straight on a situationship, in a voxel
crate on a dark studio floor. From Austin's DM idea (a famous physics idea applied to internet slang, explained deadpan);
our own script and subject.

python render_quantum.py out.mp4 out.wav     full render (Blender frames are cached in out/quantum/frames; delete them to re-render)
python render_quantum.py preview 1.0,12.5    render and composite stills into preview/
python render_quantum.py times               narrate and print the event times
python render_quantum.py audio out.mp4 out.wav  rebuild only the soundtrack and swap it into an existing render

Facts: Schrodinger described the cat in 1935, as a critique of the Copenhagen interpretation; in his setup an atom may decay
within the hour "with equal probability" as not, and he called it one of the "quite ridiculous cases"
(https://en.wikipedia.org/wiki/Schr%C3%B6dinger%27s_cat, https://www.britannica.com/science/Schrodingers-cat).
"Situationship" was a finalist for Oxford Word of the Year 2023 (https://languages.oup.com/word-of-the-year-2023/).
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
    ("A", "Every *situationship* is secretly a *quantum physics* problem."),
    ("B", "In *1935{nineteen thirty-five},* Erwin Schrödinger{Shrodinger} imagined a cat in a sealed box that's *alive and dead* at once, until somebody *looks.*"),
    ("C", "A situationship follows the same rules. Until someone asks *what are we,* you're *dating* and *not dating.*"),
    ("D", "You text every morning. *Dating.* You've never met their friends. *Not dating.*"),
    ("E", "Physicists call this *superposition.* The group chat calls it *delulu.*"),
    ("F", "And it stays stable as long as *nobody measures it.*"),
    ("G", "Then a friend asks, *so what are you two?* And the whole thing *collapses.*"),
    ("H", "In the original setup, the odds were *fifty-fifty.* Schrödinger{Shrodinger} called it a *ridiculous case.*"),
    ("I", "He was *right.*"),
]
EXTRA_GAP = {3: 0.1, 5: 0.15, 6: 0.15, 7: 0.25, 8: 0.2}
OUT = os.path.join(ROOT, "out", "quantum")
FRAMES = os.path.join(OUT, "frames")

def events(sents, speech_end):
    w = lambda si, sub: tap.word_time(sents, si, sub)
    s = lambda si: sents[si]["t0"]
    return {"A": s(0), "B": s(1), "C": s(2), "D": s(3), "E": s(4), "F": s(5), "G": s(6), "H": s(7), "I": s(8),
            "year": w(1, "1935"), "alive": w(1, "alive"), "looks": w(1, "looks"), "whatwe": w(2, "what"),
            "dating_c": w(2, "dating"), "not_c": w(2, "not"), "text": w(3, "text"), "dating_d": w(3, "Dating"),
            "friends": w(3, "friends"), "not_d": w(3, "Not"), "superposition": w(4, "superposition"), "delulu": w(4, "delulu"),
            "nobody": w(5, "nobody"), "friend": w(6, "friend"), "sowhat": w(6, "so"), "collapses": w(6, "collapses"),
            "fifty": w(7, "fifty"), "ridiculous": w(7, "ridiculous"), "right": w(8, "right"), "speech_end": speech_end}

# ------------------------------------------------------------------ sound (recorded effects from the Sonniss GDC 2026 bundle, see sfx.py)

F = {
    "room": "Cinematic Sound Design - Sci-Fi Drones/Roomtone Space Ship Interior Muted.wav",
    "shimmer": "Epic Stock Media - Strange Game Ambient Loops 3/MAGShim_Shimmer Loop Small Bell Metal Taps_ESM_SGA3.wav",
    "magic": "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/GAMEMisc_Magic Creation 23_CB Sounddesign_APPlicable Sounds.wav",
    "perc": "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav",
    "pop": "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav",
    "bubbles": "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Bubbles Short.wav",
    "swoosh": "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Pull Swoosh Readout.wav",
    "woosh": "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav",
    "snap": "Cinematic Sound Design - Interface & Infographics/Interface Accept Glassy Snap.wav",
    "denymuted": "Cinematic Sound Design - UI Interaction Elements/Deny Muted.wav",
    "steps": "TheWorkRoom - Flip Flops/FFG002.wav",
    "click": "InMotionAudio - USA Hotel/MECHClik_USALightSwitch_On05_InMotionAudio_USAHotel.wav",
    "bassdown": "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Transition Bass Down.wav",
    "shatter": "Epic Stock Media - Tower Defense Game/ICEBrk_Skill Freeze Whoosh Break Impact Layered Movement Shatter 03_ESM_TDG.wav",
    "bass": "344 Audio - Bass Drops & Downers Vol. 1/DSGNBass_Bass Drop & Downer Fast 16_344 Audio_Bass Drops & Downers.wav",
    "kalimba": "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Kalimba 3 Up_CB Sounddesign_APPlicable Sounds.wav",
}

def build_audio(sents, E, duration, path):
    import sfx
    import quantum_anim as QA
    n = int(duration * SR)
    tt = np.arange(n) / SR
    voice = K.voice_track(sents, duration)[:n]
    sup = np.array([0.0 if t >= E["collapses"] else (0.3 if E["dating_d"] - 0.1 <= t < E["E"] - 0.2 else 1.0) for t in tt[::480]])
    sup = np.convolve(np.interp(tt, tt[::480], sup), np.ones(4800) / 4800, "same")
    beds = sfx.bed(F["room"], duration, 0.03, hp=60) + sfx.bed(F["shimmer"], duration, 0.025, hp=300) * sup
    env = np.sqrt(np.convolve(voice ** 2, np.ones(2400) / 2400, "same"))
    beds *= 1 - 0.4 * np.clip(env / 0.08, 0, 1)
    tr = new_track(duration)
    tr[:n] += voice + beds
    hit = lambda t0, key, gain, **kw: add(tr, t0, sfx.clip(F[key], **kw), gain)
    hit(0.0, "magic", 0.16)
    hit(0.0, "bass", 0.08, lp=2500)
    # Geiger counter ticks, sparse and irregular while the box is a quantum system
    rng = np.random.default_rng(3)
    t = E["B"] + 0.3
    while t < E["collapses"]:
        hit(t, "perc", 0.05, rate=1.7, lp=6000)
        t += rng.exponential(0.55) + 0.08
    hit(E["B"] - 0.3, "swoosh", 0.18)
    hit(E["year"], "snap", 0.18)
    hit(E["alive"], "bubbles", 0.14)
    hit(E["looks"], "pop", 0.16)
    hit(E["C"] - 0.3, "swoosh", 0.16, rate=1.1)
    hit(E["dating_d"], "kalimba", 0.24)
    hit(E["not_d"], "denymuted", 0.3)
    hit(E["E"] - 0.25, "woosh", 0.18)
    hit(E["superposition"], "magic", 0.14)
    hit(E["delulu"], "pop", 0.18, rate=1.2)
    t, k = QA.friend_enter(E), 0
    steps = sfx.onsets(F["steps"], 0.25, 10)
    while t < QA.friend_arrive(E):
        hit(t, "steps", 0.16, start=steps[k % len(steps)], dur=0.2, lp=2500, hp=90)
        t += QA.STEP
        k += 1
    hit(QA.friend_arrive(E) + 0.05, "click", 0.35)
    hit(E["collapses"] - 0.35, "bassdown", 0.35)
    hit(E["collapses"], "shatter", 0.38)
    hit(E["fifty"], "snap", 0.16)
    hit(E["ridiculous"], "pop", 0.14, rate=0.9)
    hit(E["right"] - 0.25, "bubbles", 0.2)
    hit(E["right"] - 0.2, "pop", 0.2, rate=1.1)
    save_wav(tr, path, duration)

def remux(mp4, wav):
    import subprocess
    tmp = mp4 + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", tmp], check=True)
    os.replace(tmp, mp4)

# ------------------------------------------------------------------ overlay

PINK = skia.Color(255, 120, 170)
BLUE = skia.Color(130, 180, 255)

def draw_hook(c, a):
    if a <= 0:
        return
    y = 290
    for s, k in (("Schrödinger’s", False), ("situationship", True)):
        f = font("Bricolage-800", 96)
        wd = f.measureText(s) + (40 if k else 0)
        x = W / 2 - wd / 2
        if k:
            c.drawRRect(tap.rrect(x, y - 78, x + wd, y + 26, 16), paint(ORANGE, a))
            c.drawString(s, x + 20, y, f, paint(tap.PANEL2, a))
        else:
            c.drawString(s, x, y, f, paint(INK, a))
        y += 112

def pill(c, text, cx, y, a, color=INK, bg=K.DARK_PILL, size=34):
    if a <= 0:
        return
    f = font("JetBrainsMono-700", size)
    w = f.measureText(text)
    c.drawRRect(tap.rrect(cx - w / 2 - 22, y - size - 10, cx + w / 2 + 22, y + 16, 14), paint(bg, a))
    c.drawString(text, cx - w / 2, y, f, paint(color, a))


def smooth01(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

def bubble(c, text, x, y, a):
    """Speech bubble with its tail pointing down at (x, y)."""
    if a <= 0:
        return
    f = font("Bricolage-800", 46)
    w = f.measureText(text)
    x0 = max(60, min(x - w / 2 - 30, W - 120 - w))
    y1 = y - 40
    c.drawRRect(tap.rrect(x0, y1 - 96, x0 + w + 60, y1, 26), paint(INK, a))
    path = skia.Path()
    tx = max(x0 + 40, min(x, x0 + w + 20))
    path.moveTo(tx - 18, y1 - 2); path.lineTo(tx + 18, y1 - 2); path.lineTo(x, y); path.close()
    c.drawPath(path, paint(INK, a))
    c.drawString(text, x0 + 30, y1 - 32, f, paint(tap.PANEL2, a))

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    import quantum_anim as QA
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, K.fade(t, -1, E["B"] - 0.05, 0.2))
    tap.draw_captions(c, t, sents, cm)
    c.restore()
    lab = font("JetBrainsMono-700", 30)
    a_d, a_n = QA.couple_alphas(t, E)
    a_alive, a_dead = QA.cat_alphas(t, E)
    c0, c1 = QA.cat_window(E)
    # state readout: the kets and their weights
    if c0 <= t < c1:
        rows = (("|ALIVE>", a_alive, tap.GREEN), ("|DEAD>", a_dead, tap.RED))
    elif t < E["collapses"]:
        rows = (("|DATING>", a_d, PINK), ("|NOT DATING>", a_n, BLUE))
    else:
        rows = (("|NOT DATING>", 1.0, BLUE),)
    if t >= E["right"] - 0.25:
        rows = (("|NOT DATING>", 1.0, BLUE), ("|CAT: ALIVE>", 1.0, tap.GREEN))
    x0, y0 = 54, 452
    f_k = font("JetBrainsMono-800", 34)
    c.drawRRect(tap.rrect(x0, y0, x0 + 470, y0 + 40 + 58 * len(rows), 18), paint(K.DARK_PILL, 1.0))
    c.drawString("STATE", x0 + 26, y0 + 34, font("JetBrainsMono-700", 24), paint(MUTED))
    for k, (name, a, col) in enumerate(rows):
        yy = y0 + 84 + 58 * k
        c.drawString(name, x0 + 26, yy, f_k, paint(col, 0.35 + 0.65 * min(1.0, a)))
        bw = 130 * min(1.0, a)
        c.drawRRect(tap.rrect(x0 + 310, yy - 24, x0 + 440, yy - 4, 8), paint(skia.ColorSetARGB(255, 40, 42, 50)))
        if bw > 1:
            c.drawRRect(tap.rrect(x0 + 310, yy - 24, x0 + 310 + bw, yy - 4, 8), paint(col))
    tags = [
        ("geiger", "GEIGER COUNTER", E["year"] - 0.1, E["C"] - 0.2, 120, -220, tap.GREEN),
        ("heart", "TEXTS EVERY MORNING", E["text"] - 0.1, E["friends"] - 0.15, -60, -230, PINK),
        ("them", "NEVER MET THE FRIENDS", E["friends"] - 0.15, E["E"] - 0.2, -40, -260, BLUE),
    ]
    for name, text, t0, t1, dx, dy, col in tags:
        a = K.fade(t, t0, t1, 0.2)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, col, lab)
    pill(c, "MEASUREMENTS TAKEN: 0", W / 2, 1440, K.fade(t, E["nobody"] - 0.1, E["G"] - 0.2, 0.2), INK)
    a = K.fade(t, E["sowhat"] - 0.1, E["collapses"] + 0.6, 0.15)
    p = K.anchor(A, "friend", Fr) if a > 0 else None
    if p:
        bubble(c, "so what are you two?", p[0], p[1] - 10, a)
    pill(c, "WAVE FUNCTION: COLLAPSED", W / 2, 1440, K.fade(t, E["collapses"] + 0.05, E["H"] - 0.15, 0.2), tap.RED)
    pill(c, "ODDS IN 1935: 50 / 50", W / 2, 1440, K.fade(t, E["fifty"] - 0.1, E["I"] - 0.1, 0.2), ORANGE)
    u = t - E["collapses"]
    if 0 <= u < 0.35:
        c.drawRect(skia.Rect(0, 0, W, H), paint(INK, 0.55 * (1 - u / 0.35)))
    a = K.fade(t, E["year"] - 0.1, E["C"] - 0.2, 0.3)
    if a > 0:
        text_center(c, "Thought experiment: E. Schrödinger, 1935", W / 2, 1535, font("JetBrainsMono-500", 26), paint(MUTED, 0.9 * a))
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
    K.run_blender("quantum_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0]
    if not preview_times:
        build_audio(sents, E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "quantum" if preview_times else None)

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
