"""Game-cutscene episodes (the @zeromrrclub look, built in code from Nov 24): MakeHuman characters at a patio table,
each with their own Drama 3 voice, talking mouths from the audio, heads that follow whoever speaks, camera cuts on
lines, and the pixel UI from cutscene_ui.py on top (stat tags over heads, outlined captions, hook text).

python render_cutscene.py <episode> times          voice the lines, print the timeline (no Blender)
python render_cutscene.py <episode> preview t1,t2  render those moments with the overlay into preview/
python render_cutscene.py <episode>                full render -> out/<slug>/<slug>.mp4
python render_cutscene.py <episode> encode         redo the overlay, sound and MP4 from the frames on disk

An episode is a dict in EPISODES: cast (who sits where, which voice), a frame-0 hook, and beats. A beat is a line
({"who", "say", "cam", "tag", "punch", "faces", "to"}) or a pause ({"pause": seconds, "cam", "faces"}).
"say" keeps Drama 3's [acting notes]; captions drop them. cam: "wide", "single", "close" (on the speaker unless
"on" names someone), "two" or "group" with "on": [a, b, ...]. tag: [label, value, color] or [label, value, color,
[extra, color]] pops over the speaker as the line starts. Any beat can also carry:
  look    {"name": "down" | "cam" | other name}: who looks where from this beat on (phones: "down")
  drops   [[name, "$0"], ...]: those tags tick to the new value one after another, 0.45 s apart
  insert  "lock" with "lock": {...cutscene_ui.lock_screen args}: a full-frame phone screen over the whole beat
  sfx     [[path under the Sonniss folder, offset s, gain], ...]
"""
import json, math, os, random, re, subprocess, sys
import numpy as np
import skia
import common
from common import ROOT, W, H, SR, new_track, add, save_wav
import kit3d
import cutscene_ui as UI
import sfx

FPS = 30
VOICE_DIR = os.path.join(ROOT, "out", "voice_tests")
REF_TEXT = ("Okay, so here's the thing nobody tells you about the stuff in your kitchen. "
            "Every single appliance is quietly doing something wild, and I'm going to show you exactly what.")
COLORS = {"green": UI.GREEN, "red": UI.RED, "yellow": UI.YELLOW, "white": UI.WHITE, "orange": UI.ORANGE}
# Music beds. "zeromrr" is the @zeromrrclub reel's own background track (Austin, Nov 24: "we need that background
# audio they use"), split from its dialogue with Demucs and cut to a seamless 4.67 s loop (1.02 to 5.69 s of their
# mix, before any of their sound effects). Source unidentified ("Original audio - zeromrrclub"), so assume it is
# copyrighted: it lives in out/ (gitignored) and is never committed to this public repo.
MUSIC = {"zeromrr": os.path.join(ROOT, "out", "ref", "zeromrr", "bed_loop.wav")}

EPISODES = {
    # 7 s look test (Nov 24): our own lines, never posted. The chad is the main character.
    "cutscene_test": {
        "cast": [{"name": "suit", "x": -0.6, "rot": -12, "arms": "crossed", "voice": "am_onyx"},
                 {"name": "chad", "x": 0.0, "rot": 0, "arms": "table", "voice": "am_michael"},
                 {"name": "overalls", "x": 0.6, "rot": 12, "arms": "table", "voice": "am_eric"}],
        "hook": "POV: the group chat finally meets up",
        "music": "zeromrr",
        "beats": [
            {"who": "suit", "say": "[smug, slow, pleased with himself] Finance. Two-forty.", "cam": "wide",
             "tag": ["FINANCE", "$240K", "green"], "faces": {"suit": "smug"}, "to": "chad"},
            {"who": "overalls", "say": "[calm, unbothered] Plumber. I'm off at two.", "cam": "single",
             "tag": ["PLUMBER", "OFF AT 2", "green"], "faces": {"overalls": "smug"}, "to": "chad"},
            {"who": "chad", "say": "[relaxed, warm, completely sure of himself] I don't work. Look at my hair.",
             "cam": "close", "tag": ["UNEMPLOYED", "AURA oo", "yellow"], "punch": True,
             "faces": {"chad": "smirk"}, "to": "suit"},
            {"pause": 1.3, "cam": "wide", "faces": {"suit": "shock", "overalls": "laugh", "chad": "smirk"}},
        ],
    },
}


RING = ["CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/"
        "UIMisc_Xylophone Ringtone 2_CB Sounddesign_APPlicable Sounds.wav"]
LAUGH = "Epic Stock Media - AAA Game Character Police Officer/VOXLaff_Police Officer Laugh Vocal Male 1.wav"

# Episode 1 with the chad (Nov 24, Austin: "get something that looks better then post stuff with him"). A remake of
# the @zeromrrclub reel he DMed (https://www.instagram.com/p/Df5RJMCNUlO/): same beats in the same order (a tease,
# three job-and-salary flexes, "you?", the hero's zero, a laugh, the phones, every tag to $0, the hero's offer, one
# friend's follow-up that shows he's in), our own words. Our twist: the plumber's phone stays quiet and his tag stays.
EPISODES["chad_couch"] = {
    "cast": [{"name": "jacket", "x": -0.75, "rot": -14, "arms": "table", "voice": "am_liam"},
             {"name": "suit", "x": -0.25, "rot": -5, "arms": "crossed", "voice": "am_onyx"},
             {"name": "chad", "x": 0.25, "rot": 5, "arms": "table", "voice": "am_michael"},
             {"name": "overalls", "x": 0.75, "rot": 14, "arms": "table", "voice": "am_eric"}],
    "hook": "POV: her friends brought their boyfriends",
    "music": "zeromrr",
    "beats": [
        {"who": "jacket", "say": "[friendly but condescending, a little smirk] So you're the one who's between things.",
         "cam": "group", "on": ["jacket", "suit", "chad"], "to": "chad", "faces": {"jacket": "smug"}},   # faces big at frame 0 (patrol)
        {"who": "suit", "say": "[smug, slow, pleased with himself] Finance. Two-forty.", "cam": "wide",
         "tag": ["FINANCE", "$240K", "green"], "faces": {"suit": "smug"}, "to": "chad"},
        {"who": "jacket", "say": "[casual, proud] Big tech. Three-ten.", "cam": "wide",
         "tag": ["BIG TECH", "$310K", "green"], "to": "chad"},
        {"who": "overalls", "say": "[calm, unbothered] Plumber. One-eighty. Cash.", "cam": "wide",
         "tag": ["PLUMBER", "$180K", "green"], "faces": {"overalls": "smug"}, "to": "chad"},
        {"who": "suit", "say": "[leaning in, smug] You?", "cam": "single", "on": "chad", "to": "chad"},
        {"who": "chad", "say": "[relaxed, warm, completely sure of himself] I don't work.", "cam": "close",
         "tag": ["UNEMPLOYED", "$0", "green", ["HAIR S+", "yellow"]], "to": "suit"},   # not their AURA bit
        {"pause": 1.5, "cam": "wide", "faces": {"jacket": "laugh", "suit": "laugh", "overalls": "laugh"},
         "sfx": [[LAUGH, 0.05, 0.5, 0.0, 1.6, 0.94], [LAUGH, 0.2, 0.4, 0.0, 1.4, 1.08]]},
        {"pause": 0.8, "cam": "wide", "look": {"jacket": "down", "suit": "down"},
         "faces": {"jacket": "neutral", "suit": "neutral"}, "sfx": [[RING[0], 0.0, 0.45, 0.0, 1.2]]},
        {"pause": 2.0, "insert": "lock",
         "lock": {"clock": "4:12", "day": "TUESDAY", "app": "HR", "sub": "Human Resources",
                  "title": "Your role has been eliminated", "body": "Please return your laptop"}},
        {"pause": 1.6, "cam": "wide", "drops": [["suit", "$0"], ["jacket", "$0"]],
         "faces": {"suit": "shock", "jacket": "shock", "overalls": "smug", "chad": "smirk"},
         "look": {"suit": "chad", "jacket": "chad", "overalls": "chad"}},
        {"who": "chad", "say": "[warm, generous, completely calm] Couch pulls out.", "cam": "close", "punch": True,
         "to": "suit"},
        {"who": "jacket", "say": "[quiet, dead serious] Is there room for a second monitor?", "cam": "single",
         "to": "chad", "faces": {"jacket": "neutral"}},
    ],
}


# Episode 2 with the chad (Nov 24, for Thanksgiving week): the "reel educated" bit from Austin's idea ("Instagram
# educated", see research_notes/2026-11-24_Series_And_Shirt_Concept.md). The fact is true and sourced in
# ops/episodes/2026-11-24-chad-tryptophan.md: turkey's tryptophan is about the same as chicken or beef (Harvard Health),
# and the after-dinner drowsiness comes from the big meal, the carbs and the alcohol (Harvard Health, Scientific
# American, Texas A&M).
EPISODES["chad_tryptophan"] = {
    "cast": EPISODES["chad_couch"]["cast"],
    "props": "friendsgiving",
    "hook": "POV: Friendsgiving with the guy who learned everything from reels",
    "music": "zeromrr",
    "beats": [
        {"who": "suit", "say": "[stuffed, tired, quick] Turkey's kicking in. I'm done.",
         "cam": "group", "on": ["jacket", "suit", "chad"], "tag": ["MBA", "$140K", "green"], "to": "jacket"},
        {"who": "jacket", "say": "[smug know-it-all, explaining slowly] Tryptophan. Turkey's loaded with it.",
         "cam": "wide", "tag": ["PRE-MED", "YEAR 3", "green"], "faces": {"jacket": "smug"}, "to": "suit"},
        {"who": "chad", "say": "[calm, casual, barely interested] That's a myth.", "cam": "close",
         "tag": ["EDUCATION", "REELS", "white"], "to": "jacket"},
        {"pause": 1.4, "cam": "wide", "faces": {"jacket": "laugh", "suit": "laugh", "overalls": "laugh"},
         "sfx": [[LAUGH, 0.05, 0.5, 0.0, 1.5, 0.94], [LAUGH, 0.2, 0.4, 0.0, 1.3, 1.08]]},
        {"who": "jacket", "say": "[still laughing, condescending] Okay. Let me just check.", "cam": "single",
         "look": {"jacket": "down"}, "faces": {"jacket": "smug"}},
        {"pause": 3.0, "insert": "search",
         "search": {"query": "does turkey make you sleepy", "source": "HARVARD HEALTH",
                    "title": "Turkey's tryptophan is about the same as chicken or beef",
                    "body": "The nap? Digesting a big meal."}},
        {"pause": 1.5, "cam": "wide", "drops": [["jacket", "WRONG"], ["chad", "REELS", "yellow"]],
         "faces": {"jacket": "shock", "suit": "shock", "overalls": "laugh", "chad": "smirk"},
         "look": {"jacket": "chad", "suit": "chad", "overalls": "chad"}},
        {"who": "suit", "say": "[sleepy, confused] Then why am I so tired?", "cam": "single", "to": "chad"},
        {"who": "chad", "say": "[deadpan] Four plates of stuffing.", "cam": "close", "to": "suit"},
        {"who": "jacket", "say": "[defeated, quiet] Where'd you even learn that?", "cam": "single", "to": "chad",
         "faces": {"jacket": "neutral"}},
        {"who": "chad", "say": "[warm, completely sure of himself] Saw it on a reel.", "cam": "close", "punch": True,
         "to": "jacket"},
    ],
}


def strip_notes(s):
    return re.sub(r"\[[^\]]*\]", "", s).strip()


# ------------------------------------------------------------------ voices

def ref_clip(voice):
    """A synthetic reference clip from one of Kokoro's own voices: Drama 3 clones it, so no real person is cloned."""
    path = os.path.join(VOICE_DIR, f"ref_{voice}.wav")
    if not os.path.exists(path):
        import soundfile as sf
        from kokoro_onnx import Kokoro
        k = Kokoro(os.path.join(ROOT, "vendor", "tts", "kokoro-v1.0.onnx"), os.path.join(ROOT, "vendor", "tts", "voices-v1.0.bin"))
        audio, sr = k.create(REF_TEXT, voice=voice, speed=1.0, lang="en-us")
        os.makedirs(VOICE_DIR, exist_ok=True)
        sf.write(path, audio, sr)
    return path


def voice_lines(ep, out_dir):
    """One Drama 3 take per line, in the speaker's voice; trimmed and resampled to 48 kHz mono."""
    vdir = os.path.join(out_dir, "voice")
    os.makedirs(vdir, exist_ok=True)
    voices = {c["name"]: c["voice"] for c in ep["cast"]}
    jobs = {}
    for i, b in enumerate(ep["beats"]):
        if "say" not in b:
            continue
        import hashlib
        key = hashlib.sha1(f'{b["who"]}|{voices[b["who"]]}|{b["say"]}'.encode()).hexdigest()[:8]   # new text, new take
        raw = os.path.join(vdir, f"line{i:02d}_{key}_raw.wav")
        b["_raw"], b["_wav"] = raw, os.path.join(vdir, f"line{i:02d}_{key}.wav")
        jobs.setdefault(b["who"], []).append({"text": b["say"], "out": raw, "seed": i})
    for who, items in jobs.items():
        if all(os.path.exists(it["out"]) for it in items):
            continue
        job = os.path.join(vdir, f"job_{who}.json")
        json.dump({"ref": ref_clip(voices[who]), "ref_text": REF_TEXT, "model": "drama-3", "direction": "",
                   "items": items}, open(job, "w"), indent=1)
        subprocess.run([sys.executable, os.path.join(ROOT, "fish_worker.py"), job], check=True)
    for b in ep["beats"]:
        if "say" in b and not os.path.exists(b["_wav"]):
            trim = ("silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.03,areverse,"
                    "silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.06,areverse")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", b["_raw"], "-af", trim, "-ar", str(SR), "-ac", "1",
                            b["_wav"]], check=True)
        if "say" in b:
            import soundfile as sf
            b["_audio"], _ = sf.read(b["_wav"])


def mouth_curves(x):
    """Per video frame: how open the mouth is (0..1, from loudness) and its shape ('aa', 'oh', 'ee', 'mbp')."""
    hop = SR // FPS
    n = int(math.ceil(len(x) / hop))
    rms, shape = np.zeros(n), []
    freqs = np.fft.rfftfreq(hop * 2, 1 / SR)
    for i in range(n):
        seg = x[i * hop: i * hop + hop * 2]
        if len(seg) < hop * 2:
            seg = np.pad(seg, (0, hop * 2 - len(seg)))
        rms[i] = np.sqrt(np.mean(seg ** 2))
        sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2
        lo = sp[(freqs > 120) & (freqs < 900)].sum()
        mid = sp[(freqs >= 900) & (freqs < 2500)].sum()
        hi = sp[(freqs >= 2500) & (freqs < 8000)].sum()
        tot = lo + mid + hi + 1e-12
        if hi / tot > 0.42:
            shape.append("ee")
        elif lo / tot > 0.72:
            shape.append("oh")
        else:
            shape.append("aa")
    ref = np.percentile(rms[rms > 0], 92) if np.any(rms > 0) else 1.0
    op = np.clip((rms / (ref + 1e-9)) ** 0.8, 0, 1)
    op[op < 0.12] = 0.0
    for i in range(1, n - 1):                         # a sharp dip inside speech reads as lips closing (m, b, p)
        if op[i] < 0.35 * min(op[i - 1], op[i + 1]) and min(op[i - 1], op[i + 1]) > 0.4:
            shape[i] = "mbp"
    sm = op.copy()
    for i in range(1, n):                             # fast open, slower close
        sm[i] = op[i] if op[i] > sm[i - 1] else sm[i - 1] * 0.55 + op[i] * 0.45
    return sm.tolist(), shape


# ------------------------------------------------------------------ timeline

def timeline(ep, lead_in=0.45, gap=0.28, tail=0.6):
    t = lead_in
    for b in ep["beats"]:
        b["_t0"] = t
        if "say" in b:
            b["_dur"] = len(b["_audio"]) / SR
            t += b["_dur"] + b.get("gap", gap)
        else:
            b["_dur"] = b["pause"]
            t += b["pause"]
    for b in ep["beats"]:                              # tags that tick to a new value, one after another
        for i, d in enumerate(b.get("drops", [])):     # [who, new value] or [who, new value, color]
            tb = next(x for x in ep["beats"] if x.get("who") == d[0] and "tag" in x)
            tb["tick"] = [b["_t0"] + b.get("drop_delay", 0.3) + 0.45 * i, d[1]] + list(d[2:3])
    return t + tail


def timing_json(ep, duration):
    names = [c["name"] for c in ep["cast"]]
    NF = int(round(duration * FPS))
    chars = {n: {"mouth": [0.0] * NF, "shape": ["aa"] * NF, "look": [], "expr": [[0.0, "neutral", 1.0]],
                 "blinks": []} for n in names}
    shots, last_speaker = [], None
    for b in ep["beats"]:
        t0 = b["_t0"]
        speaker = b.get("who")
        cam = b.get("cam", "wide")
        on = b.get("on", speaker or last_speaker)
        shot = {"t0": max(0.0, t0 - 0.06), "cam": cam}
        if cam in ("single", "close"):
            shot["who"] = [on if isinstance(on, str) else on[0]]
        elif cam in ("two", "group"):
            shot["who"] = list(on)
        if not shots or shots[-1]["cam"] != shot["cam"] or shots[-1].get("who") != shot.get("who"):
            shots.append(shot)
        focus = speaker or last_speaker
        for n in names:                               # listeners watch the speaker; the speaker addresses `to`
            if n == focus:
                to = b.get("to") or next((m for m in names if m != n), "cam")
                chars[n]["look"].append([t0 - 0.1, to])
            else:
                chars[n]["look"].append([t0 + 0.05 + 0.08 * names.index(n), focus])
        for n, e in b.get("faces", {}).items():
            chars[n]["expr"].append([t0 + (0.15 if n == speaker else 0.35), e, 1.0])
        for i, (n, target) in enumerate(b.get("look", {}).items()):
            chars[n]["look"].append([t0 + 0.12 + 0.1 * i, target])
        if speaker:
            m, sh = mouth_curves(b["_audio"])
            f0 = int(round(t0 * FPS))
            for i, (v, s) in enumerate(zip(m, sh)):
                if f0 + i < NF:
                    chars[speaker]["mouth"][f0 + i] = v
                    chars[speaker]["shape"][f0 + i] = s
            last_speaker = speaker
    for n in names:
        chars[n]["look"].sort()
        chars[n]["expr"].sort()
        r = random.Random(names.index(n) + 11)
        t = r.uniform(0.6, 2.0)
        while t < duration:
            chars[n]["blinks"].append(round(t, 3))
            t += r.uniform(2.2, 4.8)
    cast = [{k: c[k] for k in ("name", "x", "rot", "arms") if k in c} for c in ep["cast"]]
    return {"fps": FPS, "duration": duration, "cast": cast, "shots": shots, "chars": chars, "samples": 24,
            "props": ep.get("props", "cafe")}


# ------------------------------------------------------------------ overlay and sound

def make_overlay(ep, T, A):
    tags = []
    for b in ep["beats"]:
        if "tag" in b:
            label, value, color = b["tag"][:3]
            extra = b["tag"][3] if len(b["tag"]) > 3 else None
            tags.append({"who": b["who"], "t": b["_t0"] + 0.12, "label": label, "value": value,
                         "color": COLORS[color], "tick": b.get("tick"), "extra": extra})
    inserts = [b for b in ep["beats"] if b.get("insert")]
    lines = [b for b in ep["beats"] if "say" in b]
    first_end = lines[0]["_t0"] + lines[0]["_dur"] if lines else 2.0
    first_cut = T["shots"][1]["t0"] if len(T["shots"]) > 1 else 1e9
    hook_end = min(first_end + 0.4, first_cut)          # the hook leaves at the first cut, never over a close-up

    def shot_at(t):
        return max((s for s in T["shots"] if s["t0"] <= t), key=lambda s: s["t0"], default=T["shots"][0])

    def overlay(c, t, F):
        for b in inserts:                                  # a full-frame phone screen covers everything
            if b["_t0"] <= t < b["_t0"] + b["_dur"]:
                if b["insert"] == "search":
                    UI.search_screen(c, t - b["_t0"], **b.get("search", {}))
                else:
                    UI.lock_screen(c, t - b["_t0"], **b.get("lock", {}))
                return
        if t < hook_end:
            UI.hook_text(c, ep["hook"], y=300)
        sh = shot_at(t)
        close = sh["cam"] in ("single", "close")
        placed = []                                        # boxes already drawn this frame, to keep tags apart
        for tg in tags:
            if t < tg["t"] or (close and tg["who"] not in sh.get("who", [])):
                continue
            a = kit3d.anchor(A, tg["who"], F)
            if not a or not (60 < a[0] < W - 60) or a[1] < 260:
                continue
            scale = 1.55 if close else 1.2
            value, color, shake = tg["value"], tg["color"], 0.0
            if tg["tick"]:
                value, color, shake = UI.tick(t, tg["tick"][0], tg["value"], tg["tick"][1], color_before=tg["color"],
                                              color_after=COLORS[tg["tick"][2]] if len(tg["tick"]) > 2 else UI.RED)
            half = (max(len(tg["label"]) * 24, len(value) * 40, len(tg["extra"][0]) * 28 if tg["extra"] else 0)
                    + 50) * scale / 2                      # keep the panel on screen
            hh = (62 + (34 if tg["extra"] else 0)) * scale
            x = min(max(a[0], half + 24), W - half - 24)
            y = max(330, a[1]) - 40 * scale

            def hit(x, y):
                return next((p for p in placed if abs(x - p[0]) < half + p[2] + 12 and abs(y - p[1]) < hh + p[3] + 8),
                            None)
            for _ in range(6):                             # overlapping an earlier tag: slide away, else stack above
                p = hit(x, y)
                if p is None:
                    break
                nx = min(max(p[0] + (half + p[2] + 12) * (1 if x >= p[0] else -1), half + 24), W - half - 24)
                if hit(nx, y) is None and abs(nx - p[0]) >= half + p[2] + 12:
                    x = nx
                else:
                    y = p[1] - (hh + p[3] + 10)
            placed.append((x, y, half, hh))
            rows = [(tg["label"], UI.WHITE, 24), (value, color, 40)]
            if tg["extra"]:
                rows.append((tg["extra"][0], COLORS[tg["extra"][1]], 28))
            UI.stat_tag(c, x, y, rows, scale=scale, t=t, t0=tg["t"], shake=shake)
        for b in lines:
            if b["_t0"] <= t < b["_t0"] + b["_dur"] + 0.18:
                UI.caption(c, strip_notes(b["say"]), color=UI.ORANGE if b.get("punch") else UI.WHITE, bottom=1300)
    return overlay


def music_bed(path, duration, voices, gain=0.42, duck=0.55):
    """The music loop tiled to length, ducked under the voices (fast down, slow back up), faded at both ends."""
    import soundfile as sf
    from scipy.signal import resample_poly
    from scipy.ndimage import maximum_filter1d
    x, sr = sf.read(path)
    x = x.mean(axis=1) if x.ndim > 1 else x
    if sr != SR:
        g = np.gcd(int(sr), SR)
        x = resample_poly(x, SR // g, int(sr) // g)
    n = len(voices)
    bed = np.tile(x, int(np.ceil(n / len(x))))[:n]
    bed = bed / (np.abs(bed).max() + 1e-9)
    env = maximum_filter1d(np.abs(voices), int(0.3 * SR))
    k = int(0.15 * SR)
    env = np.convolve(env, np.ones(k) / k, "same")
    ref = np.percentile(env[env > 1e-4], 80) if np.any(env > 1e-4) else 1.0
    g = 1 - duck * np.clip(env / ref, 0, 1)
    fi, fo, end = int(0.2 * SR), int(0.6 * SR), int(duration * SR)
    g[:fi] *= np.linspace(0, 1, fi)
    g[end - fo:end] *= np.linspace(1, 0, fo)
    g[end:] = 0
    return bed * g * gain


def mix(ep, duration):
    tr = new_track(duration)
    for b in ep["beats"]:
        if "say" in b:
            add(tr, b["_t0"], b["_audio"] / (np.abs(b["_audio"]).max() + 1e-9), 1.0)
    music = MUSIC.get(ep.get("music", ""))
    if music and os.path.exists(music):
        tr = tr + music_bed(music, duration, tr.copy())
    else:
        if music:
            print("music bed missing, using walla:", music)
        bed = sfx.bed("Jake Fielding - British Walla and Crowd/CRWDWalla_Pub Walla Atmos, Restaurant, Liverpool, Scouse,_Jake Fielding_11.wav",
                      duration, 0.06, lp=3500)
        add(tr, 0.0, bed, 1.0)
    for b in ep["beats"]:
        for e in b.get("sfx", []):                     # [path, offset, gain] or [path, offset, gain, start, dur]
            kw = {"start": e[3], "dur": e[4]} if len(e) > 4 else {}
            if len(e) > 5:
                kw["rate"] = e[5]
            add(tr, b["_t0"] + e[1], sfx.clip(e[0], gain=e[2], **kw), 1.0)
        if "tag" in b:
            add(tr, b["_t0"] + 0.12, sfx.clip("Cinematic Sound Design - UI Interaction Elements/Ting Coins.wav", gain=0.22), 1.0)
        if b.get("tick"):
            add(tr, b["tick"][0], sfx.clip("Cinematic Sound Design - UI Interaction Elements/Deny Muted.wav", gain=0.3), 1.0)
    return tr


# ------------------------------------------------------------------ main

def blender_frames(tj, frames, which, NF, tries=6):
    """Run the scene script until every asked-for frame is on disk. Blender 5.2 crashes now and then between frames
    once strand hair is in the scene (EXCEPTION_ACCESS_VIOLATION inside the renderer, about one run in four on
    Nov 24), so a crash just clears the half-written frame and the next run carries on from there."""
    want = list(range(1, NF + 1)) if which == "all" else list(which)
    for attempt in range(tries):
        for f in want:                                  # placeholders and partial writes from a crash
            p = os.path.join(frames, f"f_{f:05d}.png")
            if os.path.exists(p) and os.path.getsize(p) < 1000:
                os.remove(p)
        todo = [f for f in want if not os.path.exists(os.path.join(frames, f"f_{f:05d}.png"))]
        if not todo:
            return
        arg = "all" if which == "all" else ",".join(map(str, todo))
        r = subprocess.run([kit3d.BLENDER, "-b", "--factory-startup", "-noaudio", "-P",
                            os.path.join(ROOT, "cutscene_scene.py"), "--", tj, frames, arg])
        if r.returncode != 0:
            print(f"Blender exited with {r.returncode} (attempt {attempt + 1}); resuming")
    missing = [f for f in want if not os.path.exists(os.path.join(frames, f"f_{f:05d}.png"))]
    if missing:
        raise RuntimeError(f"frames still missing after {tries} runs: {missing[:10]}")


def rerender_black(tj, frames, NF, tries=2):
    """Eevee sometimes writes an all-black frame (Nov 24: the first frame of a session, before its shaders were
    ready). Find any and render them again."""
    from PIL import Image
    for _ in range(tries):
        bad = []
        for f in range(1, NF + 1):
            p = os.path.join(frames, f"f_{f:05d}.png")
            im = Image.open(p).convert("L").resize((54, 96))
            if np.asarray(im).mean() < 4:
                bad.append(f)
        if not bad:
            return
        print("re-rendering black frames:", bad)
        for f in bad:
            os.remove(os.path.join(frames, f"f_{f:05d}.png"))
        blender_frames(tj, frames, bad, NF)


def main():
    name = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "full"
    ep = EPISODES[name]
    out_dir = os.path.join(ROOT, "out", name)
    frames = os.path.join(out_dir, "frames")
    os.makedirs(frames, exist_ok=True)
    voice_lines(ep, out_dir)
    duration = timeline(ep)
    for b in ep["beats"]:
        print(f"{b['_t0']:6.2f}  {b.get('who', '-'):9s} {b.get('cam', ''):7s} {strip_notes(b.get('say', '(pause)'))}")
    print(f"duration {duration:.2f} s")
    if mode == "times":
        return
    T = timing_json(ep, duration)
    tj = os.path.join(out_dir, "timing.json")
    json.dump(T, open(tj, "w"))
    NF = int(round(duration * FPS))
    if mode == "preview":
        ts = [float(x) for x in sys.argv[3].split(",")]
        fl = [min(NF - 1, int(round(t * FPS))) for t in ts]
        for f in fl:
            p = os.path.join(frames, f"f_{f + 1:05d}.png")
            if os.path.exists(p):
                os.remove(p)
        blender_frames(tj, frames, [f + 1 for f in fl], NF)
        A = json.load(open(os.path.join(frames, "anchors.json")))
        kit3d.composite(frames, fl, FPS, make_overlay(ep, T, A), preview_prefix=name)
        print("previews in preview/")
        return
    if mode != "encode":                             # "encode": overlay or sound changed, frames on disk are fine
        for f in os.listdir(frames):                 # Blender skips frames already on disk: start clean
            if f.startswith("f_") and f.endswith(".png"):
                os.remove(os.path.join(frames, f))
        blender_frames(tj, frames, "all", NF)
        rerender_black(tj, frames, NF)
    A = json.load(open(os.path.join(frames, "anchors.json")))
    wav = os.path.join(out_dir, f"{name}.wav")
    save_wav(mix(ep, duration), wav, duration)
    mp4 = os.path.join(out_dir, f"{name}.mp4")
    kit3d.composite(frames, range(NF), FPS, make_overlay(ep, T, A), out_mp4=mp4, out_wav=wav)
    print(mp4)


if __name__ == "__main__":
    main()
