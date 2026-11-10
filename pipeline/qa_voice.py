"""Listen to a narration the way a viewer does, from the audio itself (Whisper word times drift by 0.2 s, so pauses
and pace are measured from the waveform): real pauses (quiet for 120 ms or more) and where they fall, speaking pace per
line (syllables per second of actual sound), loudness per line, clipping. Fails the things Austin hears as a messed-up
cadence (Nov 10): pace that swings between lines, pauses inside a phrase, cramped or dragging gaps between lines.

python qa_voice.py out/<slug> [narration.json name]      -> report, exit 1 if it fails
"""
import json, os, re, sys
import numpy as np
from voice_fix import read_wav, frame_db, spoken_syllables, end_punct, HOP

QUIET = -38.0
MIN_PAUSE = 0.12

def silences(a, sr, t0, t1):
    db = frame_db(a[int(t0 * sr):int(t1 * sr)], sr)
    out, cur = [], None
    for i, v in enumerate(db):
        if v < QUIET:
            cur = (cur[0], i + 1) if cur else (i, i + 1)
        else:
            if cur and (cur[1] - cur[0]) * HOP >= MIN_PAUSE:
                out.append((t0 + cur[0] * HOP, t0 + cur[1] * HOP))
            cur = None
    if cur and (cur[1] - cur[0]) * HOP >= MIN_PAUSE:
        out.append((t0 + cur[0] * HOP, t0 + cur[1] * HOP))
    merged = []                                   # a breath inside a pause splits it in two; it is still one pause
    for s, e in out:
        if merged and s - merged[-1][1] < 0.06:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    return merged

def check(d, name="narration"):
    lines = json.load(open(os.path.join(d, name + ".json")))
    a, sr = read_wav(os.path.join(d, name + ".wav"))
    paces, louds, fails, rows = [], [], [], []
    for i, L in enumerate(lines):
        sil = [s for s in silences(a, sr, L["start"], L["end"]) if s[0] > L["start"] + 0.03 and s[1] < L["end"] - 0.03]
        dur = L["end"] - L["start"] - sum(e - s for s, e in sil)
        syl = spoken_syllables(L["text"])          # as said: "0.14%" is "zero point one four percent"
        pace = syl / max(dur, 1e-3)
        db = frame_db(a[int(L["start"] * sr):int(L["end"] * sr)], sr)
        loud = float(np.median(db[db > QUIET + 10])) if (db > QUIET + 10).any() else -60
        paces.append(pace); louds.append(loud)
        # punctuated words may pause, plain ones not. Whisper's word ends drift by up to 0.2 s, so a pause is allowed
        # when an unused punctuated word ends within [start - 0.3, end + 0.1] of it; each one excuses one pause
        # (nearest-word matching blamed "you" for the pause after "got." in the Relationship Roll, Nov 10)
        odd = []
        free = [j for j, w in enumerate(L["words"][:-1]) if w["w"].rstrip("\"')*")[-1:] in ",:;.?!-"]
        for s, e in sil:
            if e - s <= 0.18:
                continue
            ok = [j for j in free if s - 0.3 <= L["words"][j]["end"] <= e + 0.1]
            if ok:
                free.remove(min(ok, key=lambda j: abs(L["words"][j]["end"] - s)))
                continue
            if free:                              # word times of a number Whisper spelled as digits are guessed,
                free.pop(0)                       # so a spare punctuation break still excuses one pause
                continue
            k = min(range(len(L["words"])), key=lambda j: abs(L["words"][j]["end"] - s))
            odd.append(f"{e - s:.2f}s near '{L['words'][k]['w']}'")
        rows.append((i + 1, pace, loud, odd))
    med = float(np.median(paces))
    print(f"{'line':>4} {'pace':>6} {'vs med':>7} {'loud':>6}  pauses inside a phrase")
    for (n, p, l, odd) in rows:
        dev = 100 * (p - med) / med
        flag = " <" if abs(dev) > 15 else ""
        print(f"{n:4d} {p:6.2f} {dev:+6.0f}% {l:6.1f}  {'; '.join(odd)}{flag}")
        if abs(dev) > 15:
            fails.append(f"line {n} pace {dev:+.0f}% off the median")
        if odd:
            fails.append(f"line {n} pauses mid-phrase ({'; '.join(odd)})")
    gaps = [(lines[i + 1]["start"] - lines[i]["end"], end_punct(lines[i]["text"])) for i in range(len(lines) - 1)]
    for g, p in gaps:
        if p in ".?!" and not (0.28 <= g <= 0.6):
            fails.append(f"gap {g:.2f}s after a sentence (want 0.3 to 0.6)")
    if max(louds) - min(louds) > 4:
        fails.append(f"loudness swings {max(louds) - min(louds):.1f} dB between lines")
    if (np.abs(a) > 0.995).mean() > 1e-4:
        fails.append("clipping")
    print(f"pace median {med:.2f} syllables/s ({med * 60 / 1.45:.0f} wpm approx), spread "
          f"{100 * (max(paces) - min(paces)) / med:.0f}%; gaps between lines {', '.join(f'{g:.2f}' for g, _ in gaps)}")
    print("FAIL: " + " | ".join(fails) if fails else "PASS")
    return not fails

if __name__ == "__main__":
    ok = check(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "narration")
    sys.exit(0 if ok else 1)
