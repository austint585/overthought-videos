"""'Sir, this is a Wendy's' (ops/episodes/2026-11-15-sir-wendys.md). A boxing-glove corner coach gives a cash register
the speech of its life across a fast-food counter roped off like a boxing corner. The register answers with the line.
Toon kit (wendys_scene.py). Two voices: the coach in the designed hype voice (qwen_hype), the cashier calm (Chatterbox).

python render_wendys.py narrate             voice both parts (cached in out/wendys/coach and out/wendys/cash), merge, print times
python render_wendys.py preview 1.0,12.5    render and composite stills into preview/
python render_wendys.py out.mp4 out.wav     full render (Blender frames are cached in out/wendys/frames)

Sources: Know Your Meme and the Daily Dot on the line. No numbers are claimed.
"""
import json, math, os, sys, wave
import numpy as np
import skia
import common
from common import *
import render_tap as tap
import kit3d as K
from narrate_cb import narrate
from render_led import common_load

FPS = 30
TAIL = 1.0
OUT = os.path.join(ROOT, "out", "wendys")
FRAMES = os.path.join(OUT, "frames")
SCRIPT = [   # (who, line)
    ("coach", "Look at me. They said you'd never *make it.* Too small. Too slow. Too *soft.*"),
    ("coach", "Every time you went down, you got back up. Tonight, you take what's *yours.*"),
    ("cash", "Sir, this is a *Wendy's.*"),
    ("coach", "A number six. And the *heart of a champion.*"),
    ("cash", "Send this to the friend who gives speeches at the drive-through."),
]
GAPS = [0.40, 0.52, 0.44, 0.42]       # the held breath before "Sir" stays inside the 0.6 s gate (qa_voice)
KEYS = "ABCDE"

def voice_parts():
    parts = {}
    for who, eng, ex in (("coach", "qwen_hype", 0.5), ("cash", "cb", 0.5)):
        lines = [l for w, l in SCRIPT if w == who]
        parts[who] = (narrate(lines, os.path.join(OUT, who), exaggeration=ex, cfg=0.4, gap=0.3, engine=eng), who)
    return parts

def merge():
    """One narration.json/.wav in script order from the two voices' takes, so voice_fix and qa_voice see one read."""
    dst = os.path.join(OUT, "narration.json")
    srcs = [os.path.join(OUT, w, "narration.json") for w in ("coach", "cash")]
    if os.path.exists(dst) and all(os.path.getmtime(dst) >= os.path.getmtime(s) for s in srcs):
        return
    pcm = {}
    lines = {}
    for w in ("coach", "cash"):
        lines[w] = json.load(open(os.path.join(OUT, w, "narration.json")))
        with wave.open(os.path.join(OUT, w, "narration.wav")) as f:
            pcm[w] = np.frombuffer(f.readframes(f.getnframes()), np.int16).astype(np.float32) / 32767
    # level the two voices to the same RMS over their speech
    rms = {w: float(np.sqrt(np.mean(np.concatenate([pcm[w][int(L["start"] * SR):int(L["end"] * SR)] for L in lines[w]]) ** 2)))
           for w in pcm}
    ref = rms["coach"]
    idx = {"coach": 0, "cash": 0}
    t = 0.25
    track, out = [np.zeros(int(0.25 * SR), np.float32)], []
    for k, (who, text) in enumerate(SCRIPT):
        L = lines[who][idx[who]]
        idx[who] += 1
        seg = pcm[who][int(L["start"] * SR):int(L["end"] * SR)] * (ref / max(1e-6, rms[who]))
        off = t - L["start"]
        words = [dict(w, start=w["start"] + off, end=w["end"] + off) for w in L["words"]]
        out.append(dict(L, text=text, start=t, end=t + len(seg) / SR, words=words))
        g = GAPS[k] if k < len(GAPS) else 0.0
        track += [seg, np.zeros(int(g * SR), np.float32)]
        t += len(seg) / SR + g
    a = np.concatenate(track)
    a *= 0.89 / (np.abs(a).max() + 1e-9)
    with wave.open(os.path.join(OUT, "narration.wav"), "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((a * 32767).astype(np.int16).tobytes())
    json.dump(out, open(dst, "w"), indent=1)

def to_sents(lines):
    out = []
    for L in lines:
        words = [{"display": w["w"], "key": w["key"]} for w in L["words"]]
        out.append({"words": words, "abs_starts": [w["start"] for w in L["words"]], "t0": L["start"],
                    "dur": L["end"] - L["start"]})
    return out

def wn(sents, si, sub, nth=0):
    s = sents[si]
    hits = [i for i, w in enumerate(s["words"]) if sub.lower() in w["display"].lower()]
    return s["abs_starts"][hits[min(nth, len(hits) - 1)]] if hits else s["t0"]

def setup():
    voice_parts()
    merge()
    from voice_fix import fixed
    lines = fixed(OUT, keep_pauses=True, max_stretch=0.06, gaps=GAPS)
    sents = to_sents(lines)
    speech_end = lines[-1]["end"]
    w = lambda si, sub, n=0: wn(sents, si, sub, n)
    E = {k: sents[i]["t0"] for i, k in enumerate(KEYS)}
    E.update({"they": w(0, "They"), "make": w(0, "make"), "too1": w(0, "Too", 0), "too2": w(0, "Too", 1),
              "too3": w(0, "Too", 2), "soft": w(0, "soft"), "every": w(1, "Every"), "down": w(1, "down"),
              "tonight": w(1, "Tonight"), "yours": w(1, "yours"), "sir": w(2, "Sir"), "wendys": w(2, "Wendy"),
              "six": w(3, "six"), "heart": w(3, "heart"), "champion": w(3, "champion"), "send": w(4, "Send"),
              "speech_end": speech_end})
    E["coach_end"] = sents[1]["t0"] + sents[1]["dur"]
    E["coach_words"] = [x for i, (who, _) in enumerate(SCRIPT) if who == "coach" for x in sents[i]["abs_starts"]]
    E["cash_words"] = [x for i, (who, _) in enumerate(SCRIPT) if who == "cash" for x in sents[i]["abs_starts"]]
    return lines, sents, speech_end, speech_end + TAIL, E

# ------------------------------------------------------------------ sound (recorded effects from the Sonniss GDC 2026 bundle)

F = {
    "bell": "Ivo Vicic - Church Bells/04 Church Bells, Near Distance, In Church Tower-3 Different Bell 02.wav",
    "crowd": "Sonik Sound Library - Spanish Crowds/CRWDCheer_Small Club, 50 People, Crowd, Spanish, Cheering and Applause-Surround_KSL_KS015.wav",
    "punch": "Epic Stock Media - Anime Game/FGHTImpt_Combat Punch Impact Light Hit Delay Crunchy Vintage Quick Smack 05_ESM_AG.wav",
    "pop": "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav",
    "snap": "Cinematic Sound Design - Interface & Infographics/Interface Accept Glassy Snap.wav",
    "woosh": "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav",
}

def build_audio(E, duration, path):
    import sfx
    n = int(duration * SR)
    tr = new_track(duration)
    voice = common_load(os.path.join(OUT, "narration_fixed.wav"))[:n]
    tr[:len(voice)] += voice
    hit = lambda t0, key, gain, **kw: add(tr, t0, sfx.clip(F[key], **kw), gain)
    # the round bell: two short dings sliced from a tower bell, pitched up
    for k in range(2):
        hit(0.0 + 0.32 * k, "bell", 0.16, dur=0.6, rate=1.9)
    # the crowd: under the coach only, at least 6 dB under the voice, cut dead on "Sir"
    crowd = sfx.clip(F["crowd"], dur=max(1.0, E["sir"] - 0.05))
    m = len(crowd)
    env = np.ones(m, np.float32)
    ti = np.arange(m) / SR
    env *= np.clip(ti / 0.4, 0, 1)
    sw = (ti >= E["tonight"]) & (ti < E["yours"] + 0.6)
    env[sw] *= 1.0 + 0.8 * np.clip((ti[sw] - E["tonight"]) / max(0.3, E["yours"] - E["tonight"]), 0, 1)
    cut = int((E["sir"] - 0.08) * SR)
    env[cut:] = 0
    fade = int(0.03 * SR)
    if cut - fade > 0:
        env[cut - fade:cut] *= np.linspace(1, 0, fade)
    add(tr, 0.0, crowd * env, 0.05)
    for key_t in ("too1", "too2", "too3"):
        hit(E[key_t], "punch", 0.07)
    hit(E["soft"], "punch", 0.1, rate=0.85)
    hit(E["B"] - 0.08, "woosh", 0.06)
    hit(E["tonight"] - 0.05, "woosh", 0.06, rate=0.8)
    hit(E["wendys"], "snap", 0.16, rate=0.7)                 # the big moment: the lights come on
    hit(E["wendys"] + 0.02, "pop", 0.08, rate=0.6)
    hit(E["champion"], "pop", 0.07, rate=1.3)                 # the receipt
    hit(E["send"], "bell", 0.08, dur=0.5, rate=1.9)          # the loop: back to the corner
    save_wav(tr, path, duration)

# ------------------------------------------------------------------ overlay

YELLOW = skia.Color(247, 184, 21)

def smooth01(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

def spot_on(t, E):
    return t < E["wendys"] or t >= E["E"]

def vignette(c, t, E, A, Fr):
    """The boxing spotlight: a hard pool of light on the eye of the shot, black around it. Off from 'Wendy's'."""
    if not spot_on(t, E):
        u = t - E["wendys"]
        if u > 0.12:
            return
        k = 1 - u / 0.12
    else:
        k = 1.0
    p = K.anchor(A, "pool", Fr) or [W / 2, H * 0.52]
    r = 700
    sh = skia.GradientShader.MakeRadial(skia.Point(p[0], p[1]), r,
                                        [skia.ColorSetARGB(0, 0, 0, 0), skia.ColorSetARGB(0, 0, 0, 0),
                                         skia.ColorSetARGB(int(245 * k), 2, 3, 8)], [0.0, 0.42, 1.0])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))
    c.drawRect(skia.Rect(0, 0, W, H), paint(skia.Color(255, 214, 160), 0.08 * k))     # the spot's warm cast

def draw_round(c, a):
    if a <= 0:
        return
    f1, f2 = font("Bricolage-800", 150), font("JetBrainsMono-700", 44)
    text_center(c, "ROUND 12", W / 2, 400, f1, paint(INK, a))
    text_center(c, "0:59", W / 2, 470, f2, paint(YELLOW, a))

def pill(c, text, cx, y, a, color=INK, bg=K.DARK_PILL, size=36):
    if a <= 0:
        return
    f = font("JetBrainsMono-700", size)
    w = f.measureText(text)
    c.drawRRect(tap.rrect(cx - w / 2 - 22, y - size - 10, cx + w / 2 + 22, y + 16, 14), paint(bg, a))
    c.drawString(text, cx - w / 2, y, f, paint(color, a))

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    vignette(c, t, E, A, Fr)
    u = t - E["wendys"]
    if 0 <= u < 0.25:                                     # the lights come on: a short white flash
        c.drawRect(skia.Rect(0, 0, W, H), paint(skia.Color(255, 255, 250), 0.35 * (1 - u / 0.25)))
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_round(c, K.fade(t, -1, E["they"] - 0.05, 0.15))
    if t >= E["they"] - 0.1:
        tap.draw_captions(c, t, sents, cm)
    c.restore()
    if t > speech_end + 0.1:
        a = smooth01((t - speech_end - 0.1) / 0.4)
        text_center(c, "@overthought.daily", W / 2, 1530, font("JetBrainsMono-500", 32), paint(MUTED, a))

# ------------------------------------------------------------------ main

def main(out_mp4=None, out_wav=None, preview_times=None):
    common.FPS = FPS
    lines, sents, speech_end, duration, E = setup()
    if out_mp4 is None and preview_times is None:
        for L in lines:
            print(f"{L['start']:6.2f} {L['end']:6.2f} match {L['match']}  {L['text']}")
        print(json.dumps({k: round(v, 2) for k, v in E.items() if not isinstance(v, list)}))
        print(f"duration {duration:.2f} s")
        return
    n_frames = int(round(duration * FPS))
    frames = sorted({min(n_frames - 1, int(round(x * FPS))) for x in preview_times}) if preview_times else list(range(n_frames))
    K.run_blender("wendys_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = tap.build_chunk_map(sents)
    if not preview_times:
        build_audio(E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "wendys" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] in ("narrate", "times"):
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
