"""'Why does only your key open your door?' 3D cutaway: Kokoro voice, Blender (Eevee) frames, Skia captions on top.

python render_lock.py out.mp4 out.wav    full render (Blender frames are cached in out/lock/frames; delete them to re-render)
python render_lock.py preview 1.0,12.5   render and composite stills into preview/
"""
import glob, json, os, pickle, subprocess, sys
import numpy as np
import skia
import common
from common import *
import render_tap as tap
import lock_anim as LA

FPS = 60
common.FPS = FPS
SCRIPT = [
    ("A", "Why does only *your* key open your door?"),
    ("B", "Cut a lock in *half.*"),
    ("B", "The part your key slides into is called the *plug.* Turning it pulls the *bolt* back."),
    ("C", "But *five* stacks of pins block it."),
    ("C", "Each stack is a *spring,* a top pin, and a bottom pin."),
    ("C", "With no key, the springs push the top pins *down* across the gap, so the plug *can't* turn."),
    ("D", "Now slide the key in."),
    ("D", "Each *cut* lifts its pin to an exact height."),
    ("D", "When every gap lines up with the *shear line,* where the plug meets the housing, nothing blocks it, and it *turns.*"),
    ("E", "Wrong key? Even *one* pin too high, and it stays *locked.*"),
    ("E", "On some locks, the cut depths are less than *half a millimeter* apart."),
    ("F", "Comment what we should cut open *next.*"),
]
tap.SCRIPT = SCRIPT
EXTRA_GAP = {1: 0.15, 6: 0.35, 9: 1.4, 11: 0.5}   # room for the cut, the key, the key swap, the reassembly
LEAD_IN = 0.2
TAIL = 2.6
OUT = os.path.join(ROOT, "out", "lock")
FRAMES = os.path.join(OUT, "frames")
BLENDER = os.environ.get("BLENDER") or next(iter(sorted(glob.glob(os.path.join(ROOT, "vendor", "blender_dl", "*", "blender.exe"))
                                                         + glob.glob(os.path.join(ROOT, "vendor", "blender_dl", "*", "blender")))), "blender")

# ------------------------------------------------------------------ narration and events

def narration():
    os.makedirs(OUT, exist_ok=True)
    cache = os.path.join(OUT, "narration.pkl")
    key = repr((SCRIPT, EXTRA_GAP, LEAD_IN, tap.VOICE, tap.SPEED))
    if os.path.exists(cache):
        d = pickle.load(open(cache, "rb"))
        if d["key"] == key:
            return d["sents"], d["speech_end"]
    sents = tap.synth_all()
    t = LEAD_IN
    for i, s in enumerate(sents):
        t += EXTRA_GAP.get(i, 0.0)
        s["t0"] = t
        s["abs_starts"] = [t + x for x in s["starts"]]
        t += s["dur"] + tap.GAP
    speech_end = t - tap.GAP
    pickle.dump({"key": key, "sents": sents, "speech_end": speech_end}, open(cache, "wb"))
    return sents, speech_end

def events(sents, speech_end):
    w = lambda si, sub: tap.word_time(sents, si, sub)
    return {"cut": sents[1]["t0"] - 0.08, "half": w(1, "half"), "plug": w(2, "plug"), "bolt": w(2, "bolt"),
            "C0": sents[3]["t0"], "five": w(3, "five"), "spring": w(4, "spring"), "top": w(4, "top"),
            "bottom": w(4, "bottom"), "down": w(5, "down"), "cant": w(5, "can't"), "slide": sents[6]["t0"],
            "cutw": w(7, "cut"), "shear": w(8, "shear"), "turns": w(8, "turns"), "wrong": sents[9]["t0"],
            "one": w(9, "one"), "locked": w(9, "locked"), "some": sents[10]["t0"], "halfmm": w(10, "half"),
            "comment": sents[11]["t0"], "next": w(11, "next"), "speech_end": speech_end}

def run_blender(mode, E, duration):
    tj = os.path.join(OUT, "timing.json")
    with open(tj, "w") as fh:
        json.dump({"fps": FPS, "duration": duration, "events": E}, fh, indent=1)
    subprocess.run([BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "lock_scene.py"),
                    "--", tj, FRAMES, mode], check=True)

# ------------------------------------------------------------------ sound

def layer(*sigs):
    out = np.zeros(max(len(s) for s in sigs))
    for s in sigs:
        out[:len(s)] += s
    return out

def tick(seed, gain=1.0):
    return layer(tone(3400 + 300 * (seed % 3), 0.05, tau=0.008, harmonics=(1, 0.5, 0.25)) * 0.6,
                 noise_burst(0.03, tau=0.004, lp=0.9, seed=seed) * 0.5) * gain

def clunk(seed=0):
    return layer(sweep(190, 70, 0.3, tau=0.07) * 0.9, noise_burst(0.12, tau=0.02, lp=0.25, seed=seed) * 0.6,
                 tone(880, 0.4, tau=0.12, harmonics=(1, 0.4)) * 0.15)

def build_audio(sents, E, duration, path):
    tr = new_track(duration)
    for s in sents:
        x = s["audio"] / (np.abs(s["audio"]).max() + 1e-9)
        up = np.interp(np.arange(0, len(x) * 2) / 2.0, np.arange(len(x)), x)   # 24k -> 48k
        add(tr, s["t0"], up, 1.0)
    bed = new_track(duration)
    tt = np.arange(len(bed)) / SR
    bed += (np.sin(2 * np.pi * 98 * tt) + 0.5 * np.sin(2 * np.pi * 146.8 * tt) + 0.3 * np.sin(2 * np.pi * 196.2 * tt)) \
        * 0.05 * (0.8 + 0.2 * np.sin(2 * np.pi * 0.15 * tt))
    beat_bed(bed, E["cut"], duration - 0.5, bpm=92, gain=0.1, hat_gain=0.03)
    tr += bed * 0.5

    # key scrape follows key speed; pin ticks where a pin tops out and drops into a cut
    dt = 0.002
    ts = np.arange(0, duration, dt)
    tips = np.array([LA.key_state(t, E)[1] for t in ts])
    speed = np.abs(np.gradient(tips, dt))
    speed[tips < -15] = 0
    scrape = noise_burst(duration, tau=1e9, lp=0.5, seed=5)
    env = np.interp(np.arange(len(scrape)) / SR, ts, np.clip(speed / 8.0, 0, 1))
    add(tr, 0.0, scrape * env * 0.12)
    pins = np.array([LA.pin_tips(t, E) for t in ts])
    for i in range(5):
        z = pins[:, i]
        dz = np.diff(z)
        for k in range(1, len(dz)):
            if dz[k - 1] > 1e-4 and dz[k] < -1e-4:
                add(tr, ts[k], tick(k + i), 0.35)
    add(tr, E["cut"] - 0.05, noise_burst(0.35, tau=0.12, lp=0.12, seed=21), 0.4)
    add(tr, E["half"] + 0.05, noise_burst(0.6, tau=0.2, lp=0.08, seed=22), 0.5)
    add(tr, E["half"] + 0.02, clunk(3), 0.35)
    for base in (E["cant"], E["locked"]):
        for k in range(4):
            add(tr, base + k / 7, layer(tick(40 + k, 0.5), clunk(k) * 0.25), 0.45 * (0.7 ** k))
    add(tr, E["shear"] + 0.05, tone(1320, 0.5, tau=0.18, harmonics=(1, 0.3)), 0.12)
    add(tr, E["turns"] + 0.05, tick(77), 0.4)
    add(tr, E["turns"] + 0.62, clunk(9), 0.6)
    add(tr, E["one"] + 0.05, sweep(330, 165, 0.35, tau=0.15), 0.3)
    add(tr, E["comment"] + 0.05, noise_burst(0.6, tau=0.2, lp=0.08, seed=23), 0.4)
    add(tr, E["comment"] + 1.1, clunk(11), 0.45)
    save_wav(tr, path, duration)

# ------------------------------------------------------------------ overlay

def anchor(A, name, F):
    seq = A.get(name)
    if not seq or F >= len(seq) or seq[F] is None:
        return None
    return seq[F]

def fade(t, t0, t1, d=0.25):
    return max(0.0, min(1.0, (t - t0) / d, (t1 - t) / d))

F_TAG = None
def tag(c, text, x, y, tx, ty, alpha, color):
    """Leader line from a point on the model to a caps label on a dark pill."""
    c.drawLine(x, y, tx, ty, tap.stroke(color, 3, 0.9 * alpha))
    c.drawCircle(x, y, 7, paint(color, alpha))
    w = F_TAG.measureText(text)
    lx = tx + 14 if tx >= x else tx - 14 - w
    lx = max(50, min(lx, W - 50 - w))
    c.drawRRect(tap.rrect(lx - 16, ty - 30, lx + w + 16, ty + 22, 12), paint(skia.ColorSetARGB(200, 10, 11, 14), alpha))
    c.drawString(text, lx, ty + 10, F_TAG, paint(color, alpha))

def labels_for(E):
    # (anchor, text, start, end, dx, dy, color)
    return [
        ("plug", "PLUG", E["plug"], E["five"] - 0.3, -120, 330, ORANGE),
        ("spring", "SPRING", E["spring"], E["down"], -300, -120, INK),
        ("top", "TOP PIN", E["top"], E["down"], 330, -40, INK),
        ("bottom", "BOTTOM PIN", E["bottom"], E["down"], -320, 200, INK),
        ("shear", "SHEAR LINE", E["shear"], E["turns"] + 1.0, -80, 420, ORANGE),
        ("wrongpin", "TOO HIGH", E["one"] + 0.2, E["some"], 300, -160, tap.RED),
    ]

def draw_dimension(c, a, b, alpha):
    """Depth bracket between two key-cut anchors, label to the right."""
    x = max(a[0], b[0]) + 70
    p = tap.stroke(ORANGE, 4, alpha)
    c.drawLine(a[0] + 20, a[1], x + 16, a[1], tap.stroke(ORANGE, 2, 0.7 * alpha))
    c.drawLine(b[0] + 20, b[1], x + 16, b[1], tap.stroke(ORANGE, 2, 0.7 * alpha))
    c.drawLine(x, a[1], x, b[1], p)
    f = font("JetBrainsMono-800", 46)
    y = (a[1] + b[1]) / 2 + 16
    w = f.measureText("< 0.5 mm")
    c.drawRRect(tap.rrect(x + 14, y - 40, x + 46 + w, y + 16, 12), paint(skia.ColorSetARGB(200, 10, 11, 14), alpha))
    c.drawString("< 0.5 mm", x + 30, y, f, paint(ORANGE, alpha))

def draw_hook(c, t, end):
    a = fade(t, -1, end, 0.2)
    if a <= 0:
        return
    f = font("Bricolage-800", 84)
    lines = [[("Why does only", False)], [("your key", True), ("open", False)], [("your door?", False)]]
    y = 300
    for line in lines:
        widths = [f.measureText(s) + (36 if k else 0) for s, k in line]
        x = W / 2 - (sum(widths) + f.measureText(" ") * (len(line) - 1)) / 2
        for (s, k), wd in zip(line, widths):
            if k:
                c.drawRRect(tap.rrect(x, y - 70, x + wd, y + 22, 14), paint(ORANGE, a))
                c.drawString(s, x + 18, y, f, paint(tap.PANEL2, a))
            else:
                c.drawString(s, x, y, f, paint(INK, a))
            x += wd + f.measureText(" ")
        y += 100

def overlay(c, t, F, sents, cm, E, A, speech_end):
    shade = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, 620)],
                                           [skia.ColorSetARGB(150, 0, 0, 0), skia.ColorSetARGB(0, 0, 0, 0)])
    c.drawRect(skia.Rect(0, 0, W, 620), skia.Paint(Shader=shade))
    shadow = skia.Paint(ImageFilter=skia.ImageFilters.DropShadow(0, 4, 10, 10, skia.ColorSetARGB(200, 0, 0, 0)))
    c.saveLayer(None, shadow)
    draw_hook(c, t, sents[1]["t0"] - 0.05)
    tap.draw_captions(c, t, sents, cm)
    for name, text, t0, t1, dx, dy, col in labels_for(E):
        al = fade(t, t0, t1)
        p = anchor(A, name, F)
        if al > 0 and p:
            tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, al, col)
    al = fade(t, E["halfmm"], E["comment"] - 0.1)
    pa, pb = anchor(A, "depth_a", F), anchor(A, "depth_b", F)
    if al > 0 and pa and pb:
        draw_dimension(c, pa, pb, al)
    c.restore()
    note = fade(t, E["half"] + 0.6, E["comment"])
    if note > 0:
        text_center(c, "Cutaway illustration, proportions simplified", W / 2, 1530, font("JetBrainsMono-500", 26),
                    paint(MUTED, 0.9 * note))
    if t > speech_end + 0.2:
        a = ease_out((t - speech_end - 0.2) / 0.5)
        c.saveLayer(None, shadow)
        text_center(c, "Things you use every day,", W / 2, 330, font("Bricolage-800", 60), paint(INK, a))
        text_center(c, "explained.", W / 2, 405, font("Bricolage-800", 60), paint(ORANGE, a))
        c.restore()
        text_center(c, "@overthought.daily", W / 2, 1500, font("JetBrainsMono-500", 32), paint(MUTED, a))

# ------------------------------------------------------------------ main

def main(out_mp4, out_wav, preview_times=None):
    global F_TAG
    F_TAG = font("JetBrainsMono-800", 38)
    sents, speech_end = narration()
    duration = speech_end + TAIL
    E = events(sents, speech_end)
    n_frames = int(round(duration * FPS))
    print(f"duration {duration:.1f}s, {n_frames} frames", flush=True)
    frames = sorted({min(n_frames - 1, int(round(x * FPS))) for x in preview_times}) if preview_times else range(n_frames)
    run_blender(",".join(str(f + 1) for f in frames) if preview_times else "all", E, duration)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0]
    if not preview_times:
        build_audio(sents, E, duration, out_wav)
    enc = None if preview_times else open_encoder(out_mp4, out_wav)
    surf = skia.Surface(W, H)
    for F in frames:
        t = F / FPS
        c = surf.getCanvas()
        c.clear(skia.ColorBLACK)
        img = skia.Image.open(os.path.join(FRAMES, f"f_{F + 1:05d}.png"))
        c.drawImage(img, 0, 0)
        overlay(c, t, F, sents, cm, E, A, speech_end)
        if preview_times:
            os.makedirs("preview", exist_ok=True)
            surf.makeImageSnapshot().save(f"preview/lock_{F:05d}.png", skia.kPNG)
        else:
            enc.stdin.write(frame_bytes(surf))
    if enc:
        enc.stdin.close()
        enc.wait()

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        main(None, None, preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
