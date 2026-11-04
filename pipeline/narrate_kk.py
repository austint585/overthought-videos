"""Kokoro stand-in for narrate_cb.narrate: same return format (lines with word times) and the same narration.wav, for when the
laptop's commit memory is too low for Chatterbox (it needs about 4 GB free; on Nov 3 only 1.9 GB was). Calm read only.

    from narrate_kk import narrate
    lines = narrate(["Line one.", "Line *two.*"], out_dir, gap=0.28)
"""
import json, os, wave
import numpy as np
import render_tap as tap
from common import SR

def narrate(lines, out_dir, gap=0.22, lead_in=0.25, **_):
    os.makedirs(out_dir, exist_ok=True)
    tap.SCRIPT = [("", l) for l in lines]
    sents = tap.synth_all()
    t = lead_in
    track, out = [np.zeros(int(lead_in * SR), np.float32)], []
    for line, s in zip(lines, sents):
        a = s["audio"]
        n = int(round(len(a) * SR / s["sr"]))
        seg = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)
        dur = len(seg) / SR
        starts = s["starts"] + [s["dur"]]
        words = [{"w": w["display"], "key": w["key"], "start": t + starts[i], "end": t + starts[i + 1] - 0.02}
                 for i, w in enumerate(s["words"])]
        out.append({"text": line, "start": t, "end": t + dur, "match": 1.0, "words": words})
        track += [seg, np.zeros(int(gap * SR), np.float32)]
        t += dur + gap
    pcm = np.concatenate(track)
    pcm *= 0.89 / (np.abs(pcm).max() + 1e-9)
    with wave.open(os.path.join(out_dir, "narration.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((pcm * 32767).astype(np.int16).tobytes())
    json.dump(out, open(os.path.join(out_dir, "narration.json"), "w"), indent=1)
    return out
