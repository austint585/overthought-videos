"""Narration with Chatterbox (free, MIT): yelled or calm takes per line, checked by Whisper, timed word by word.

    from narrate_cb import narrate
    lines = narrate(["The light in your LED bulb starts out *blue.*", ...], out_dir, exaggeration=1.6)
    -> [{"text": "...", "start": s, "end": e, "words": [{"w": "blue.", "key": True, "start": .., "end": ..}, ...]}]
and out_dir/narration.wav (48 kHz mono, the lines back to back with `gap` seconds between).

Each line is voiced by cb_worker.py in vendor/venv_chatterbox_cpu. Whisper (small.en) transcribes every take; a take
whose words drift from the script (Chatterbox sometimes drops "n't" or adds a word when it shouts) is redone with the
next seed, up to len(SEEDS) tries, then the closest take wins and the miss is reported. Word times come from Whisper
and are mapped back onto the script's own words, so captions always show the script spelling.
"""
import difflib, json, os, re, subprocess, sys
import numpy as np
from common import ROOT, SR

PY = os.path.join(ROOT, "vendor", "venv_chatterbox_cpu", "Scripts", "python.exe")
REF = os.path.join(ROOT, "out", "voice_tests", "ref_am_michael.wav")     # Kokoro's synthetic am_michael
SEEDS = (7, 11, 23, 41, 59)
_whisper = None

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()

def say_number(n):
    """12345 -> 'twelve thousand three hundred forty five' (enough for scripts; Whisper writes numbers as digits)."""
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    if n < 1000:
        return ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + say_number(n % 100))
    if n < 1_000_000:
        return say_number(n // 1000) + " thousand" + ("" if n % 1000 == 0 else " " + say_number(n % 1000))
    return str(n)

def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())             # apostrophes too: Whisper hears "wall's" as "walls"

def words_of(text):
    out = []
    for w in text.split():
        d = re.sub(r"[^0-9]", "", w)
        out += say_number(int(d)).split() if d and re.fullmatch(r"[$]?[0-9][0-9,]*[.,!?]?", w) else [norm(w)]
    return [w for w in out if w]

def spoken(line):
    """Script markup to what is said: *key* marks a boxed keyword, 13.56{thirteen point five six} a spoken form."""
    return re.sub(r"\S+\{([^}]*)\}", r"\1", line).replace("*", "")

def caption_words(line):
    out = []
    for tok in re.findall(r"\S+\{[^}]*\}|\S+", line):            # 50,000{fifty thousand} is one token
        m = re.match(r"(\S+)\{([^}]*)\}", tok)
        shown = m.group(1) if m else tok
        out.append({"w": shown.replace("*", ""), "key": "*" in shown, "say": (m.group(2) if m else shown.replace("*", "")).split()})
    return out

def load_pcm(path):
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0

def transcribe(path):
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel
        _whisper = WhisperModel("small.en", device="cpu", compute_type="int8", download_root=os.path.join(ROOT, "vendor", "whisper"))
    a = load_pcm(path)[::3]                                                # 48 kHz -> 16 kHz for Whisper
    segs, _ = _whisper.transcribe(a, word_timestamps=True, vad_filter=False)
    return [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]

def release_whisper():
    """Free Whisper before the voice worker starts: the two together run this laptop out of commit memory."""
    global _whisper
    if _whisper is not None:
        _whisper = None
        import gc
        gc.collect()

def score(script_line, heard):
    a = words_of(spoken(script_line))
    b = words_of(" ".join(w for w, _, _ in heard))
    return difflib.SequenceMatcher(None, a, b).ratio()

def voice(lines, vdir, exaggeration, cfg):
    os.makedirs(vdir, exist_ok=True)
    best = {}
    todo = list(range(len(lines)))
    for seed in SEEDS:
        if not todo:
            break
        items = [{"text": spoken(lines[i]), "out": os.path.join(vdir, f"l{i:02d}_s{seed}_e{exaggeration}.wav"),
                  "exaggeration": exaggeration, "cfg": cfg, "seed": seed} for i in todo]
        job = os.path.join(vdir, "job.json")
        json.dump({"ref": REF, "items": items}, open(job, "w"))
        release_whisper()
        # OpenBLAS reserves a buffer per thread; on this laptop's tight commit limit that alone can sink the worker
        subprocess.run([PY, os.path.join(ROOT, "cb_worker.py"), job], check=True,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8", "OPENBLAS_NUM_THREADS": "1"})
        still = []
        for i, it in zip(todo, items):
            heard = transcribe(it["out"])
            s = score(lines[i], heard)
            if i not in best or s > best[i][0]:
                best[i] = (s, it["out"], heard)
            if s < 0.97:
                still.append(i)
        todo = still
    for i in todo:
        print(f"narration: line {i + 1} best match {best[i][0]:.2f}: heard '{' '.join(w for w, _, _ in best[i][2])}'")
    return [best[i] for i in range(len(lines))]

def align(line, heard, offset, trim0):
    """Script words with times: each spoken token is matched to a Whisper word in order; misses are interpolated."""
    words = caption_words(line)
    toks = [(wi, norm(t)) for wi, w in enumerate(words) for t in w["say"]]
    hn = [norm(w) for w, _, _ in heard]
    sm = difflib.SequenceMatcher(None, [t for _, t in toks], hn)
    tt = [None] * len(toks)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            _, s, e = heard[blk.b + k]
            tt[blk.a + k] = (s, e)
    known = [i for i, v in enumerate(tt) if v]
    t_first = heard[0][1] if heard else 0.0
    t_last = heard[-1][2] if heard else 0.5
    for i, v in enumerate(tt):
        if v:
            continue
        prev = max([k for k in known if k < i], default=None)
        nxt = min([k for k in known if k > i], default=None)
        a = tt[prev][1] if prev is not None else t_first
        b = tt[nxt][0] if nxt is not None else t_last
        n0 = prev if prev is not None else -1
        n1 = nxt if nxt is not None else len(tt)
        f0, f1 = (i - n0) / (n1 - n0), (i - n0 + 1) / (n1 - n0)
        tt[i] = (a + (b - a) * f0, a + (b - a) * f1)
    for w in words:
        w["start"], w["end"] = 1e9, -1e9
    for (wi, _), (s, e) in zip(toks, tt):
        words[wi]["start"] = min(words[wi]["start"], offset + s - trim0)
        words[wi]["end"] = max(words[wi]["end"], offset + e - trim0)
    for w in words:
        w.pop("say")
    return words

def narrate(lines, out_dir, exaggeration=1.6, cfg=0.25, gap=0.16, lead_in=0.25):
    takes = voice(lines, os.path.join(out_dir, "voice"), exaggeration, cfg)
    t = lead_in
    track, out = [np.zeros(int(lead_in * SR), np.float32)], []
    for line, (s, path, heard) in zip(lines, takes):
        a = load_pcm(path)
        t0 = max(0.0, (heard[0][1] if heard else 0.0) - 0.06)             # trim the silence Chatterbox leaves
        t1 = min(len(a) / SR, (heard[-1][2] if heard else len(a) / SR) + 0.14)
        seg = a[int(t0 * SR):int(t1 * SR)]
        fade = int(0.012 * SR)
        seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
        out.append({"text": line, "start": t, "end": t + len(seg) / SR, "match": round(s, 3),
                    "words": align(line, heard, t, t0)})
        track += [seg, np.zeros(int(gap * SR), np.float32)]
        t += len(seg) / SR + gap
    voice_pcm = np.concatenate(track)
    peak = np.abs(voice_pcm).max() + 1e-9
    voice_pcm *= 0.89 / peak                                               # -1 dBFS peak; the mix sets the level
    import wave
    with wave.open(os.path.join(out_dir, "narration.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((voice_pcm * 32767).astype(np.int16).tobytes())
    json.dump(out, open(os.path.join(out_dir, "narration.json"), "w"), indent=1)
    return out

if __name__ == "__main__":
    res = narrate([l for l in sys.argv[2:]], sys.argv[1])
    for r in res:
        print(round(r["start"], 2), round(r["end"], 2), r["match"], r["text"])
