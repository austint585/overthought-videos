"""Shared pieces for the 3D episodes: narration timing, the Blender hand-off, overlay helpers, sound effects and the encode loop."""
import glob, json, os, pickle, subprocess
import numpy as np
import skia
import common
from common import *
import render_tap as tap

BLENDER = os.environ.get("BLENDER") or next(iter(sorted(glob.glob(os.path.join(ROOT, "vendor", "blender_dl", "*", "blender.exe"))
                                                         + glob.glob(os.path.join(ROOT, "vendor", "blender_dl", "*", "blender")))), "blender")
TAIL = 2.6

# ------------------------------------------------------------------ narration and Blender

def narrate(script, out_dir, extra_gap=None, lead_in=0.2):
    """Kokoro narration with word timing (render_tap's), cached in out_dir. Returns (sentences, speech_end)."""
    extra_gap = extra_gap or {}
    os.makedirs(out_dir, exist_ok=True)
    cache = os.path.join(out_dir, "narration.pkl")
    key = repr((script, extra_gap, lead_in, tap.VOICE, tap.SPEED, sorted(tap.LEXICON.items())))
    if os.path.exists(cache):
        d = pickle.load(open(cache, "rb"))
        if d["key"] == key:
            return d["sents"], d["speech_end"]
    tap.SCRIPT = script
    sents = tap.synth_all()
    t = lead_in
    for i, s in enumerate(sents):
        t += extra_gap.get(i, 0.0)
        s["t0"] = t
        s["abs_starts"] = [t + x for x in s["starts"]]
        t += s["dur"] + tap.GAP
    speech_end = t - tap.GAP
    pickle.dump({"key": key, "sents": sents, "speech_end": speech_end}, open(cache, "wb"))
    return sents, speech_end

def run_blender(scene_py, out_dir, frames_dir, mode, events, duration, fps):
    tj = os.path.join(out_dir, "timing.json")
    with open(tj, "w") as fh:
        json.dump({"fps": fps, "duration": duration, "events": events}, fh, indent=1)
    subprocess.run([BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, scene_py),
                    "--", tj, frames_dir, mode], check=True)

# ------------------------------------------------------------------ overlay helpers

DARK_PILL = skia.ColorSetARGB(200, 10, 11, 14)

def fade(t, t0, t1, d=0.25):
    return max(0.0, min(1.0, (t - t0) / d, (t1 - t) / d))

def shadow_paint():
    return skia.Paint(ImageFilter=skia.ImageFilters.DropShadow(0, 4, 10, 10, skia.ColorSetARGB(200, 0, 0, 0)))

def top_shade(c, height=620, alpha=150):
    shade = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, height)],
                                           [skia.ColorSetARGB(alpha, 0, 0, 0), skia.ColorSetARGB(0, 0, 0, 0)])
    c.drawRect(skia.Rect(0, 0, W, height), skia.Paint(Shader=shade))

def tag(c, text, x, y, tx, ty, alpha, color, fnt):
    """Leader line from a point on the model to a caps label on a dark pill."""
    c.drawLine(x, y, tx, ty, tap.stroke(color, 3, 0.9 * alpha))
    c.drawCircle(x, y, 7, paint(color, alpha))
    w = fnt.measureText(text)
    lx = tx + 14 if tx >= x else tx - 14 - w
    lx = max(50, min(lx, W - 50 - w))
    c.drawRRect(tap.rrect(lx - 16, ty - 30, lx + w + 16, ty + 22, 12), paint(DARK_PILL, alpha))
    c.drawString(text, lx, ty + 10, fnt, paint(color, alpha))

def end_card(c, t, speech_end):
    if t <= speech_end + 0.2:
        return
    a = ease_out((t - speech_end - 0.2) / 0.5)
    c.saveLayer(None, shadow_paint())
    text_center(c, "Things you use every day,", W / 2, 330, font("Bricolage-800", 60), paint(INK, a))
    text_center(c, "explained.", W / 2, 405, font("Bricolage-800", 60), paint(ORANGE, a))
    c.restore()
    text_center(c, "@overthought.daily", W / 2, 1500, font("JetBrainsMono-500", 32), paint(MUTED, a))

def anchor(A, name, F):
    seq = A.get(name)
    if not seq or F >= len(seq) or seq[F] is None:
        return None
    return seq[F]

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

def whoosh(seed=0, dur=0.5):
    return noise_burst(dur, tau=dur * 0.35, lp=0.1, seed=seed)

def voice_track(sents, duration):
    tr = new_track(duration)
    for s in sents:
        x = s["audio"] / (np.abs(s["audio"]).max() + 1e-9)
        up = np.interp(np.arange(0, len(x) * 2) / 2.0, np.arange(len(x)), x)   # 24k -> 48k
        add(tr, s["t0"], up, 1.0)
    return tr

def pad_bed(duration, start, root=98.0, bpm=92):
    bed = new_track(duration)
    tt = np.arange(len(bed)) / SR
    bed += (np.sin(2 * np.pi * root * tt) + 0.5 * np.sin(2 * np.pi * root * (146.8 / 98) * tt)
            + 0.3 * np.sin(2 * np.pi * root * (196.2 / 98) * tt)) * 0.05 * (0.8 + 0.2 * np.sin(2 * np.pi * 0.15 * tt))
    beat_bed(bed, start, duration - 0.5, bpm=bpm, gain=0.1, hat_gain=0.03)
    return bed * 0.5

# ------------------------------------------------------------------ composite and encode

def composite(frames_dir, frames, fps, overlay, out_mp4=None, out_wav=None, preview_prefix=None):
    """Draw overlay(c, t, F) over each Blender frame and encode, or save previews when preview_prefix is set."""
    common.FPS = fps
    enc = None if preview_prefix else open_encoder(out_mp4, out_wav)
    surf = skia.Surface(W, H)
    for F in frames:
        c = surf.getCanvas()
        c.clear(skia.ColorBLACK)
        c.drawImage(skia.Image.open(os.path.join(frames_dir, f"f_{F + 1:05d}.png")), 0, 0)
        overlay(c, F / fps, F)
        if preview_prefix:
            os.makedirs("preview", exist_ok=True)
            surf.makeImageSnapshot().save(f"preview/{preview_prefix}_{F:05d}.png", skia.kPNG)
        else:
            enc.stdin.write(frame_bytes(surf))
    if enc:
        enc.stdin.close()
        enc.wait()
