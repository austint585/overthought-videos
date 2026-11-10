"""Cadence fix for a narration made line by line (Austin, Nov 10: "your cadence in the voice is still messed up").

Chatterbox voices each line on its own, so one line comes out at 100 words a minute and the next at 210, and it
leaves 0.3 to 0.6 s pauses after small words ("to", "for", "Row"). This evens that out without new takes:
  1. pauses inside a line follow the punctuation: none after a plain word (cut to <= 0.07 s), a short one after a
     comma or colon (0.16 to 0.24 s), a full one after a sentence (0.32 to 0.42 s). Only quiet audio is ever cut.
  0. each line's quiet head and tail are trimmed from the audio first: a take keeps up to 0.4 s of its own silence,
     which turned a 0.42 s gap into 0.6 to 0.96 s of dead air between sentences.
  2. every line is time-stretched (rubberband, pitch kept) toward the median speaking rate measured from the audio,
     at most 12% either way, and never faster than HOUSE_PACE (about 200 wpm).
  3. gaps between lines follow how the line ends (0.36 s after a full stop, as heard, not a fixed 0.16 s).
  4. lines are levelled to the same loudness (within 3 dB).
Word times are carried through every cut and stretch, so captions stay in sync.

    python voice_fix.py out/<slug>            writes narration_fixed.wav/json next to the originals and prints the
                                              before/after numbers (rate spread, misplaced pauses)
    from voice_fix import fix; lines = fix(out_dir)   # same, returns the new lines
"""
import json, os, re, subprocess, sys, tempfile, wave
import numpy as np

SR_DEFAULT = 48000
QUIET_DB = -40.0                    # dBFS frame level counted as silence (the narration peaks at -1 dBFS)
HOP = 0.005
PLAIN_MAX = 0.07
COMMA = (0.16, 0.24)
STOP = (0.32, 0.42)
LINE_GAP = {".": 0.36, "?": 0.40, "!": 0.34, ",": 0.22, ":": 0.28, ";": 0.26}   # silence between lines, after trimming
TRIM_DB = -38.0                     # a line's head and tail quieter than this are cut (qa_voice's silence level)
HEAD_KEEP, TAIL_KEEP = 0.03, 0.07   # what stays of the quiet: the onset of the first sound, the decay of the last
MAX_STRETCH = 0.12
HOUSE_PACE = 4.8                    # syllables per second of sound, about 200 wpm: the fastest a reel should talk (Nov 10)

def read_wav(path):
    w = wave.open(path)
    sr = w.getframerate()
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return a, sr

def write_wav(path, a, sr):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())

def end_punct(text):
    t = re.sub(r"\{[^}]*\}", "", text).replace("*", "").strip()
    t = t.rstrip("\"')]")
    return t[-1] if t else ""

def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        d = re.sub(r"[^0-9]", "", word)
        return max(1, len(d)) if d else 1
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and n > 1 and not w.endswith(("le", "ee")):
        n -= 1
    return max(1, n)

def spoken_syllables(text):
    """Syllables as said, not as shown: "*0.14%*{zero point one four percent}" is 9, not 3 (Nov 10)."""
    said = re.sub(r"\S+\{([^}]*)\}", r"\1", text).replace("*", "")
    return sum(syllables(w) for w in said.split())

def frame_db(a, sr):
    h = max(1, int(HOP * sr))
    n = len(a) // h
    if n == 0:
        return np.array([-120.0])
    f = a[: n * h].reshape(n, h)
    return 20 * np.log10(np.sqrt((f ** 2).mean(1)) + 1e-9)

def quiet_run(a, sr, s0, s1, margin=0.02):
    """Longest run of quiet frames inside [s0, s1) (samples), with `margin` kept at each side. (start, end) or None."""
    if s1 - s0 <= 0:
        return None
    db = frame_db(a[s0:s1], sr)
    h = max(1, int(HOP * sr))
    best, cur = None, None
    for i, v in enumerate(db):
        if v < QUIET_DB:
            cur = (cur[0], i + 1) if cur else (i, i + 1)
            if not best or cur[1] - cur[0] > best[1] - best[0]:
                best = cur
        else:
            cur = None
    if not best:
        return None
    m = int(margin * sr)
    a0, a1 = s0 + best[0] * h + m, s0 + best[1] * h - m
    return (a0, a1) if a1 > a0 else None

class TimeMap:
    """Piecewise-linear old -> new time, built from (old, new) knots."""
    def __init__(self):
        self.k = [(0.0, 0.0)]
    def add(self, old, new):
        self.k.append((old, new))
    def __call__(self, t):
        ks = self.k
        for (o0, n0), (o1, n1) in zip(ks, ks[1:]):
            if t <= o1:
                return n0 + (t - o0) * ((n1 - n0) / (o1 - o0) if o1 > o0 else 0.0)
        o, n = ks[-1]
        return n + (t - o)

def shape_line(a, sr, words, t0):
    """Re-time the pauses inside one line. a: the line's audio (starting at t0 in the track). Returns (audio, timemap)."""
    tm = TimeMap()
    out = []
    pos = 0                                           # samples of `a` consumed
    newlen = 0
    for k in range(len(words) - 1):
        w, nxt = words[k], words[k + 1]
        g0, g1 = int((w["end"] - t0) * sr), int((nxt["start"] - t0) * sr)
        g0, g1 = max(g0, pos), min(max(g1, g0), len(a))
        p = w["w"].rstrip("\"')*")[-1:] if w["w"] else ""
        lo, hi = (0.0, PLAIN_MAX) if p not in ",:;.?!" else (COMMA if p in ",:;" else STOP)
        run = quiet_run(a, sr, max(pos, g0 - int(0.04 * sr)), min(len(a), g1 + int(0.04 * sr)))
        cur = (run[1] - run[0]) / sr if run else 0.0
        if run and cur > hi:                          # cut the middle of the quiet run down to `hi`
            keep = int(hi * sr)
            c0 = run[0] + keep // 2
            c1 = run[1] - (keep - keep // 2)
            out.append(a[pos:c0]); newlen += c0 - pos
            tm.add(c0 / sr, newlen / sr)
            tm.add(c1 / sr, newlen / sr)
            pos = c1
        elif lo > 0 and cur < lo and run:             # a sentence that runs straight into the next: give it air
            # only where the audio itself dips: Whisper's word times drift about 0.2 s, so a gap placed from them
            # alone can land inside a word (the Wish Window's "11/11" pause went from 0.47 to 0.72 s that way)
            add = int((lo - cur) * sr)
            mid = (run[0] + run[1]) // 2
            mid = max(pos, min(mid, len(a)))
            out.append(a[pos:mid]); newlen += mid - pos
            tm.add(mid / sr, newlen / sr)
            out.append(np.zeros(add, np.float32)); newlen += add
            tm.add(mid / sr + 1e-6, newlen / sr)
            pos = mid
    out.append(a[pos:]); newlen += len(a) - pos
    tm.add(len(a) / sr, newlen / sr)
    return np.concatenate(out) if out else a, tm

def stretch(a, sr, tempo):
    if abs(tempo - 1.0) < 0.01:
        return a
    with tempfile.TemporaryDirectory() as d:
        i, o = os.path.join(d, "i.wav"), os.path.join(d, "o.wav")
        write_wav(i, a, sr)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", i, "-af", f"rubberband=tempo={tempo:.4f}:transients=crisp:pitchq=quality",
                        "-ar", str(sr), "-ac", "1", o], check=True)
        b, _ = read_wav(o)
    return b

def sound_time(seg, sr, quiet=-38.0, min_pause=0.12):
    """Seconds of a line that are sound: its length minus inner pauses of min_pause or more (as qa_voice measures)."""
    db = frame_db(seg, sr)
    q = db < quiet
    pauses, n = 0.0, 0
    for k, v in enumerate(q):
        if v:
            n += 1
        else:
            if n * HOP >= min_pause and k - n > 0:
                pauses += n * HOP
            n = 0
    return max(1e-3, len(seg) / sr - pauses)

def speech_rate(words, t_of, text=None):
    """Syllables per second of speaking time (pauses longer than 0.1 s don't count)."""
    syl = spoken_syllables(text) if text else sum(syllables(w["w"]) for w in words)
    talk = 0.0
    for k, w in enumerate(words):
        talk += max(0.0, t_of(w["end"]) - t_of(w["start"]))
        if k + 1 < len(words):
            talk += min(0.1, max(0.0, t_of(words[k + 1]["start"]) - t_of(w["end"])))
    return syl / max(talk, 1e-3)

def metrics(lines):
    rates = [speech_rate(L["words"], lambda t: t, L["text"]) for L in lines]
    bad = []
    for L in lines:
        ws = L["words"]
        for k in range(len(ws) - 1):
            g = ws[k + 1]["start"] - ws[k]["end"]
            p = ws[k]["w"].rstrip("\"')*")[-1:]
            if p not in ",:;.?!" and g > 0.2:
                bad.append(f"{g:.2f}s after '{ws[k]['w']}'")
    return rates, bad

def fix(out_dir, src="narration", dst="narration_fixed", lead_in=None):
    lines = json.load(open(os.path.join(out_dir, src + ".json")))
    a, sr = read_wav(os.path.join(out_dir, src + ".wav"))
    lead = lines[0]["start"] if lead_in is None else lead_in
    # 1. pauses inside each line
    # 0. each take keeps up to 0.4 s of its own quiet at the head and tail (it is cut from Whisper's word times, which
    #    drift), so the 0.42 s gap measured 0.6 to 0.96 s of real silence between lines (Nov 10). Trim from the audio.
    shaped, starts = [], []
    h = max(1, int(HOP * sr))
    for L in lines:
        s0, s1 = int(L["start"] * sr), int(L["end"] * sr)
        seg = a[s0:s1].copy()
        on = np.where(frame_db(seg, sr) > TRIM_DB)[0]
        c0 = max(0, on[0] * h - int(HEAD_KEEP * sr)) if len(on) else 0
        c1 = min(len(seg), (on[-1] + 1) * h + int(TAIL_KEEP * sr)) if len(on) else len(seg)
        seg = seg[c0:c1]
        f = min(len(seg) // 2, int(0.005 * sr))
        if f:
            seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
        t0 = L["start"] + c0 / sr
        seg, tm = shape_line(seg, sr, L["words"], t0)
        shaped.append((seg, tm))
        starts.append(t0)
    # 2. speaking rate toward the median, measured from the audio the way qa_voice.py checks it
    rates = [spoken_syllables(L["text"]) / sound_time(seg, sr) for L, (seg, _) in zip(lines, shaped)]
    target = min(float(np.median(rates)), HOUSE_PACE)
    # 4. loudness: speech frames only
    def level(x):
        db = frame_db(x, sr)
        v = db[db > QUIET_DB + 10]
        return float(np.median(v)) if v.size else -30.0
    levels = [level(seg) for seg, _ in shaped]
    ref_level = float(np.median(levels))
    track = [np.zeros(int(lead * sr), np.float32)]
    t = lead
    out = []
    for i, (L, (seg, tm), r, lv, t0) in enumerate(zip(lines, shaped, rates, levels, starts)):
        tempo = float(np.clip(target / r, 1 - MAX_STRETCH, 1 + MAX_STRETCH))
        seg2 = stretch(seg, sr, tempo)
        gain = 10 ** (np.clip(ref_level - lv, -3, 3) / 20)
        seg2 = seg2 * gain
        scale = (len(seg2) / sr) / max(len(seg) / sr, 1e-6)
        words = []
        span = len(seg2) / sr
        for w in L["words"]:
            w2 = dict(w)
            w2["start"] = t + min(span, tm(max(0.0, w["start"] - t0)) * scale)
            w2["end"] = t + min(span, tm(max(0.0, w["end"] - t0)) * scale)
            words.append(w2)
        L2 = dict(L, start=t, end=t + len(seg2) / sr, words=words, tempo=round(tempo, 3))
        out.append(L2)
        track.append(seg2.astype(np.float32))
        t += len(seg2) / sr
        if i + 1 < len(lines):                       # 3. the gap follows how the line ends
            g = LINE_GAP.get(end_punct(L["text"]), 0.34)
            track.append(np.zeros(int(g * sr), np.float32))
            t += g
    pcm = np.concatenate(track)
    pcm *= 0.89 / (np.abs(pcm).max() + 1e-9)
    write_wav(os.path.join(out_dir, dst + ".wav"), pcm, sr)
    json.dump(out, open(os.path.join(out_dir, dst + ".json"), "w"), indent=1)
    return out

def fixed(out_dir):
    """The evened narration for a render: narration_fixed.json, rebuilt whenever narration.json is newer (a re-voice).
    The render then mixes narration_fixed.wav, and qa_voice.py out/<slug> narration_fixed must PASS."""
    src, dst = os.path.join(out_dir, "narration.json"), os.path.join(out_dir, "narration_fixed.json")
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
        return json.load(open(dst))
    return fix(out_dir)

def report(name, lines):
    rates, bad = metrics(lines)
    sp = 100 * (max(rates) - min(rates)) / np.median(rates)
    print(f"{name}: speaking rate {min(rates):.1f}-{max(rates):.1f} syllables/s (spread {sp:.0f}% of the median), "
          f"{len(bad)} pauses after plain words over 0.2 s{': ' + '; '.join(bad[:6]) if bad else ''}")
    return sp, len(bad)

if __name__ == "__main__":
    d = sys.argv[1]
    before = json.load(open(os.path.join(d, "narration.json")))
    report("before", before)
    after = fix(d)
    report("after ", after)
