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
SEEDS = (7, 11, 23, 41, 59, 73, 89, 97)
# Voice engines (Nov 11 shootout): every one takes the same job file and goes through the same take choice, voice_fix
# and qa_voice. "cb" is the regular Chatterbox read in use since Oct 29.
PYQ = os.path.join(ROOT, "vendor", "venv_qwen3tts", "Scripts", "python.exe")
ENGINES = {
    "cb": {"py": PY, "worker": "cb_worker.py", "ref": REF},
    "turbo": {"py": PY, "worker": "cbt_worker.py", "ref": REF},
    "qwen": {"py": PYQ, "worker": "qwen_worker.py", "ref": os.path.join(ROOT, "out", "voice_tests", "qwen_narrator_ref.wav"),
             "ref_text": os.path.join(ROOT, "out", "voice_tests", "qwen_narrator_ref.txt")},
}
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
    out = []
    for s in segs:
        for w in s.words:
            t = w.word.strip()
            if out and t.startswith("-") and len(t) > 1 and out[-1][0].isalpha() and len(out[-1][0]) <= 3:
                out[-1] = (out[-1][0] + t, out[-1][1], w.end)          # "re" + "-rolls" is one word: "rerolls"
            else:
                out.append((t, w.start, w.end))
    return out

def release_whisper():
    """Free Whisper before the voice worker starts: the two together run this laptop out of commit memory."""
    global _whisper
    if _whisper is not None:
        _whisper = None
        import gc
        gc.collect()

def digit_tokens(line):
    """The script as Whisper tends to write it: a marked-up number keeps its shown digits ("11:11{eleven eleven}" ->
    "1111", "0.14%{...}" -> "014"); everything else is spoken words."""
    out = []
    for tok in re.findall(r"\S+\{[^}]*\}|\S+", line):
        m = re.match(r"(\S+)\{([^}]*)\}", tok)
        if m and re.search(r"[0-9]", m.group(1)):
            out.append(re.sub(r"[^0-9]", "", m.group(1)))
        else:
            out += words_of((m.group(2) if m else tok).replace("*", ""))
    return out

def heard_digit_tokens(heard):
    """Whisper's words with numbers as bare digits, split numbers joined ("11", ".11" -> "1111"; "0", ".14", "%" ->
    "014"), and short lone numbers spoken out ("8 ones" -> "eight ones")."""
    out, prev_num = [], False
    for w, _, _ in heard:
        d = re.sub(r"[^0-9]", "", w)
        if d:
            if prev_num:
                out[-1] += d
            else:
                out.append(d)
            prev_num = not re.search(r"[,.!?;:]$", w)                    # "-2," then "8": two numbers
        else:
            n = norm(w)
            if n:
                out.append(n)
                prev_num = False
    res = []
    for t in out:
        res += say_number(int(t)).split() if t.isdigit() and len(t) <= 2 else [t]
    return res

def score(script_line, heard):
    """How closely Whisper's transcript matches the script, 0 to 1. Numbers are compared both ways (spoken words and
    digits) because Whisper writes "eleven eleven" as "11 .11" or "1111" (the Wish Window never matched, Nov 10)."""
    a = words_of(spoken(script_line))
    b = words_of(" ".join(w for w, _, _ in heard))
    words = difflib.SequenceMatcher(None, a, b).ratio()
    digits = difflib.SequenceMatcher(None, digit_tokens(script_line), heard_digit_tokens(heard)).ratio()
    return max(words, digits)

MIN_TAKES = 3          # Nov 10: always try at least 3 seeds per line and keep the one that matches the others' pace
PACE_TOL = 0.10        # after that, a line keeps getting new seeds while its best take is more than 10% off the median pace

def take_shape(path, line):
    """(pace in syllables per second of sound, pauses inside the line beyond what its punctuation allows)."""
    from voice_fix import frame_db, syllables, HOP
    a = load_pcm(path)
    a = a / (np.abs(a).max() + 1e-9) * 0.89
    db = frame_db(a, SR)
    on = np.where(db > -38.0)[0]
    if not len(on):
        return 0.0, 9
    db = db[on[0]:on[-1] + 1]
    quiet = db < -38.0
    runs, n = [], 0
    for q in quiet:
        if q:
            n += 1
        else:
            if n:
                runs.append(n * HOP)
            n = 0
    pauses = [r for r in runs if r >= 0.18]
    sound = (len(db) - quiet.sum()) * HOP + sum(r for r in runs if r < 0.12)
    text = spoken(line)
    syl = sum(syllables(w) for w in text.split())
    allowed = len(re.findall(r"[,;:.?!](?=\s)", text.strip()))
    return syl / max(sound, 1e-3), max(0, len(pauses) - allowed)

def voice(lines, vdir, exaggeration, cfg, engine="cb"):
    """Every line gets at least MIN_TAKES takes; among the ones Whisper hears right, the take closest to the median
    pace with no stray pauses wins (one line at 100 wpm next to one at 210 is what Austin heard as a broken cadence)."""
    os.makedirs(vdir, exist_ok=True)
    best = {}
    takes = {i: [] for i in range(len(lines))}
    todo = list(range(len(lines)))
    for n_seed, seed in enumerate(SEEDS):
        if not todo:
            break
        tag = f"e{exaggeration}" if engine == "cb" else engine
        items = [{"text": spoken(lines[i]), "out": os.path.join(vdir, f"l{i:02d}_s{seed}_{tag}.wav"),
                  "exaggeration": exaggeration, "cfg": cfg, "seed": seed} for i in todo]
        job = os.path.join(vdir, "job.json")
        eng = ENGINES[engine]
        jd = {"ref": eng["ref"], "items": items}
        if eng.get("ref_text"):
            jd["ref_text"] = open(eng["ref_text"], encoding="utf-8").read().strip()
        json.dump(jd, open(job, "w"))
        release_whisper()
        # OpenBLAS reserves a buffer per thread; on this laptop's tight commit limit that alone can sink the worker
        subprocess.run([eng["py"], os.path.join(ROOT, eng["worker"]), job], check=True,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8", "OPENBLAS_NUM_THREADS": "1"})
        for i, it in zip(todo, items):
            heard = transcribe(it["out"])
            s = score(lines[i], heard)
            pace, stray = take_shape(it["out"], lines[i])
            takes[i].append((s, it["out"], heard, pace, stray))
            if i not in best or s > best[i][0]:
                best[i] = (s, it["out"], heard)
        still = []
        if n_seed + 1 < MIN_TAKES:
            still = list(todo)
        else:
            ok = {i: [t for t in ts if t[0] >= min(0.97, max(x[0] for x in ts) - 0.02)] for i, ts in takes.items()}
            tgt = float(np.median([np.median([t[3] for t in (ok[i] or takes[i])]) for i in takes]))
            for i in todo:
                if best[i][0] < 0.97 or min(abs(t[3] - tgt) / tgt + 0.4 * t[4] for t in ok[i]) > PACE_TOL:
                    still.append(i)
        todo = still
    for i in [i for i in todo if best[i][0] < 0.97]:
        print(f"narration: line {i + 1} best match {best[i][0]:.2f}: heard '{' '.join(w for w, _, _ in best[i][2])}'")
    # takes as close to the script as the line's best (within 0.02) all qualify, so a line Whisper never hears
    # perfectly (a number it spells oddly) still gets its pace chosen from several takes, not just one
    good = {i: [t for t in ts if t[0] >= min(0.97, max(x[0] for x in ts) - 0.02)] for i, ts in takes.items()}
    target = float(np.median([np.median([t[3] for t in good[i]]) for i in good]))
    chosen = []
    for i in range(len(lines)):
        t = min(good[i], key=lambda t: abs(t[3] - target) / target + 0.4 * t[4])
        print(f"narration: line {i + 1} pace {t[3]:.2f} (target {target:.2f}), stray pauses {t[4]}, {os.path.basename(t[1])}")
        chosen.append((t[0], t[1], t[2]))
    return chosen

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

def narrate(lines, out_dir, exaggeration=1.6, cfg=0.25, gap=0.16, lead_in=0.25, engine="cb"):
    cached = os.path.join(out_dir, "narration.json")
    if os.path.exists(cached) and os.path.exists(os.path.join(out_dir, "narration.wav")):
        old = json.load(open(cached))
        if [o["text"] for o in old] == list(lines):
            print("narration: reusing", cached, "(delete it to re-voice)")    # frames were rendered to this timing
            return old
    takes = voice(lines, os.path.join(out_dir, "voice"), exaggeration, cfg, engine)
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
        from voice_fix import LINE_GAP, end_punct
        g = max(gap, LINE_GAP.get(end_punct(line), 0.34))        # a full stop gets a full stop's pause (Nov 10)
        track += [seg, np.zeros(int(g * SR), np.float32)]
        t += len(seg) / SR + g
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
