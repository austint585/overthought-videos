"""Shared brand constants, fonts, audio synthesis and ffmpeg piping for Overthought videos."""
import math, subprocess, wave
import numpy as np
import skia

W, H = 1080, 1920
FPS = 60
SR = 48000
import os
ROOT = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(ROOT, "vendor", "fonts")

BG = skia.Color(12, 13, 17)
BG_LIGHT = skia.Color(26, 29, 37)
INK = skia.Color(243, 239, 230)
MUTED = skia.Color(150, 148, 142)
ORANGE = skia.Color(255, 106, 43)
ORANGE_RGB = (255, 106, 43)

_tf = {}
def typeface(name):
    if name not in _tf:
        _tf[name] = skia.Typeface.MakeFromFile(f"{FONT_DIR}/{name}.ttf")
    return _tf[name]

def font(name, size):
    f = skia.Font(typeface(name), size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    return f

def text_center(canvas, s, x, y, fnt, paint):
    w = fnt.measureText(s)
    canvas.drawString(s, x - w / 2, y, fnt, paint)
    return w

def fit_font(name, s, max_w, size):
    f = font(name, size)
    while f.measureText(s) > max_w and size > 10:
        size -= 2
        f = font(name, size)
    return f

def ease_io(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)

def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3

def paint(color, alpha=None, **kw):
    p = skia.Paint(AntiAlias=True, Color=color, **kw)
    if alpha is not None:
        p.setAlphaf(alpha)
    return p

def background(canvas, cx=W / 2, cy=H / 2, r=1100):
    shader = skia.GradientShader.MakeRadial(skia.Point(cx, cy), r, [BG_LIGHT, BG])
    canvas.drawPaint(skia.Paint(Shader=shader))

# ---------------------------------------------------------------- audio

def new_track(seconds):
    return np.zeros(int(seconds * SR) + SR, dtype=np.float64)

def add(track, t, sig, gain=1.0):
    i = int(t * SR)
    if i >= len(track):
        return
    j = min(len(track), i + len(sig))
    track[i:j] += sig[: j - i] * gain

def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))

def tone(freq, dur, tau=0.08, harmonics=(1.0,), attack=0.002):
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = sum(a * np.sin(2 * np.pi * freq * (k + 1) * t) for k, a in enumerate(harmonics))
    env = env_exp(n, tau)
    a = int(attack * SR)
    if a > 0:
        env[:a] *= np.linspace(0, 1, a)
    return sig * env

def sweep(f0, f1, dur, tau=0.12):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (t / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env_exp(n, tau)

def noise_burst(dur, tau=0.03, lp=0.35, seed=0):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    x = rng.standard_normal(n)
    # one-pole lowpass, coefficient lp in (0,1]
    y = np.empty_like(x)
    acc = 0.0
    for i in range(n):
        acc += lp * (x[i] - acc)
        y[i] = acc
    return y * env_exp(n, tau)

def kick(dur=0.35):
    return sweep(140, 42, dur, tau=0.09) * 0.9

def hat(seed=0):
    n = int(0.05 * SR)
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n)
    x = np.diff(np.concatenate([[0], x]))  # crude highpass
    return x * env_exp(n, 0.012) * 0.35

def beat_bed(track, start, end, bpm=124, gain=0.18, hat_gain=0.1, dense_from=None):
    spb = 60 / bpm
    t = start
    k = 0
    K = kick()
    while t < end:
        add(track, t, K, gain)
        add(track, t + spb / 2, hat(k), hat_gain)
        if dense_from is not None and t >= dense_from:
            add(track, t + spb / 4, hat(k + 1000), hat_gain * 0.6)
            add(track, t + 3 * spb / 4, hat(k + 2000), hat_gain * 0.6)
        t += spb
        k += 1

def save_wav(track, path, seconds):
    x = track[: int(seconds * SR)]
    peak = np.max(np.abs(x)) or 1.0
    x = x / peak
    # soft limiter: lifts average loudness without hard clipping
    drive = 2.2
    x = np.tanh(drive * x) / np.tanh(drive) * 0.9
    # gentle fade out
    fo = int(0.25 * SR)
    x[-fo:] *= np.linspace(1, 0, fo)
    pcm = (x * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())

# ---------------------------------------------------------------- video

def open_encoder(path, audio_path=None):
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if audio_path:
        cmd += ["-i", audio_path]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
            "-profile:v", "high", "-movflags", "+faststart"]
    if audio_path:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += [path]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)

def frame_bytes(surface):
    return surface.makeImageSnapshot().tobytes()
