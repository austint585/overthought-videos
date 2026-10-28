"""Sound QA for a finished video: integrated loudness, per-second levels, and any steady tone (hum or buzz) under the mix.

python qa_audio.py video.mp4

A steady tone is a frequency that stays well above its neighbours for most of the video. Voices and music move in pitch,
rain and room noise are broadband, so neither trips it; an electrical hum bed does (Austin heard one in the Curious George
video, Oct 27). Exit 1 when one is found.
"""
import re, subprocess, sys
import numpy as np

SR = 48000

def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)

def loudness(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)
    p = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)
    return (float(i[-1]) if i else None), (float(p[-1]) if p else None)

def steady_tones(x, lo=70.0, hi=6000.0):
    n = SR // 2                                    # 0.5 s frames, 2 Hz bins
    frames = [x[k:k + n] for k in range(0, len(x) - n, n)]
    win = np.hanning(n)
    spec = np.array([20 * np.log10(np.abs(np.fft.rfft(f * win)) + 1e-9) for f in frames])
    freqs = np.fft.rfftfreq(n, 1 / SR)
    loud = spec.max(axis=1) > spec.max() - 60       # skip silent frames
    spec = spec[loud]
    found = []
    for b in np.where((freqs >= lo) & (freqs <= hi))[0]:
        prom = spec[:, b] - np.median(np.c_[spec[:, max(0, b - 25):b - 3], spec[:, b + 4:b + 26]], axis=1)
        if np.mean(prom > 10) > 0.6:
            found.append((freqs[b], float(np.median(prom))))
    merged = []
    for f, p in found:                              # one line per tone, not per bin
        if merged and f - merged[-1][0] <= 6:
            if p > merged[-1][1]:
                merged[-1] = (f, p)
        else:
            merged.append((f, p))
    return merged

def main(path):
    x = load(path)
    i, p = loudness(path)
    print(f"{len(x) / SR:.1f} s, {i} LUFS integrated, peak {p} dBFS")
    sec = [20 * np.log10(np.sqrt(np.mean(x[k:k + SR] ** 2)) + 1e-9) for k in range(0, len(x) - SR // 2, SR)]
    print("per-second dBFS:", " ".join(f"{v:.0f}" for v in sec))
    tones = steady_tones(x)
    if len(tones) > 3:
        gap = np.median(np.diff([f for f, _ in tones]))
        print(f"STEADY TONE: {len(tones)} harmonics about {gap:.0f} Hz apart, {tones[0][0]:.0f} to {tones[-1][0]:.0f} Hz "
              f"(a buzz: find the bed or effect and remove it)")
    else:
        for f, prom in tones:
            print(f"STEADY TONE {f:.0f} Hz, {prom:.0f} dB above its neighbours (hum or buzz: find the bed and remove it)")
    if not tones:
        print("no steady tones")
    return 1 if tones else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
