"""Recorded sound effects from the Sonniss #GameAudioGDC 2026 bundle (royalty-free, commercial use, no attribution;
its license forbids using the sounds to train AI). The bundle sits in Inputs/sonniss_gdc2026, outside git.

clip(rel, start, dur, gain, rate, lp) loads one file as mono at common.SR, peak-normalized, then scaled by gain.
"""
import functools, os
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly, butter, sosfilt
from common import ROOT, SR

LIB = os.path.join(os.path.dirname(ROOT), "Inputs", "sonniss_gdc2026")

@functools.lru_cache(maxsize=64)
def _load(rel):
    x, sr = sf.read(os.path.join(LIB, rel), always_2d=True)
    x = x.mean(axis=1)
    if sr != SR:
        g = np.gcd(int(sr), SR)
        x = resample_poly(x, SR // g, int(sr) // g)
    return x

def lowpass(x, hz):
    return sosfilt(butter(4, hz, btype="low", fs=SR, output="sos"), x)

def highpass(x, hz):
    return sosfilt(butter(2, hz, btype="high", fs=SR, output="sos"), x)

def clip(rel, start=0.0, dur=None, gain=1.0, rate=1.0, lp=None, hp=None, fade=0.01, norm=True):
    x = _load(rel)
    a = int(start * SR)
    b = len(x) if dur is None else min(len(x), a + int(dur * rate * SR))
    x = x[a:b].copy()
    if rate != 1.0:
        x = np.interp(np.arange(0, len(x), rate), np.arange(len(x)), x)
    if lp:
        x = lowpass(x, lp)
    if hp:
        x = highpass(x, hp)
    n = max(1, int(fade * SR))
    if len(x) > 2 * n:
        x[:n] *= np.linspace(0, 1, n)
        x[-n:] *= np.linspace(1, 0, n)
    if norm:
        x = x / (np.abs(x).max() + 1e-9)
    return x * gain

def bed(rel, duration, gain, start=0.0, lp=None, hp=None):
    """A long ambience, RMS-normalized to `gain`, cut or looped to `duration` seconds."""
    x = clip(rel, start, None, 1.0, lp=lp, hp=hp, norm=False)
    need = int(duration * SR)
    while len(x) < need:
        x = np.concatenate([x, x])
    x = x[:need]
    return x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * gain

def onsets(rel, min_gap=0.3, top=8, win=0.12):
    """Start times of the loudest isolated hits in a file (for slicing single footsteps out of a take)."""
    x = _load(rel)
    hop = int(SR * 0.005)
    e = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, "same"))[::hop]
    peaks = [i for i in range(1, len(e) - 1) if e[i] >= e[i - 1] and e[i] > e[i + 1] and e[i] > 0.2 * e.max()]
    gap = int(min_gap / 0.005)
    iso = [i for i in peaks if all(abs(i - j) > gap or j == i for j in peaks)]
    if not iso:                     # dense takes (clock ticks, arcs): keep the loudest peaks at least min_gap apart
        for i in sorted(peaks, key=lambda i: -e[i]):
            if all(abs(i - j) > gap for j in iso):
                iso.append(i)
    iso.sort(key=lambda i: -e[i])
    return sorted(max(0.0, i * 0.005 - 0.01) for i in iso[:top])
