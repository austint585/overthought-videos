"""'Friday the 13th, checked by science': a deadpan voxel explainer for Friday, November 13, 2026, the year's third
Friday the 13th (ops/episodes/2026-11-13-friday-13th.md). A black cat crosses a believer's path on a dusk street; two
real studies disagree; the bro who doesn't believe walks under the ladder and the paint can lands on his head.
Voxel kit (fri13_scene.py), calm Chatterbox read.

python render_fri13.py narrate             voice the script (cached in out/fri13/voice), print the event times
python render_fri13.py preview 1.0,12.5    render and composite stills into preview/
python render_fri13.py out.mp4 out.wav     full render (Blender frames are cached in out/fri13/frames)

Sources: Dossey's 17 to 21 million estimate (NPR 2008, https://www.npr.org/2008/06/13/91461325/friday-the-13th-the-fear-that-will-not-die);
Scanlon et al., BMJ 1993 (https://pmc.ncbi.nlm.nih.gov/articles/PMC1697765); Dutch Centre for Insurance Statistics 2008
(https://www.dutchnews.nl/2008/06/fewer_accidents_on_friday_13/); three in 2026 (https://earthsky.org/human-world/years-that-have-3-friday-the-13ths/).
"""
import json, math, os, sys
import numpy as np
import skia
import common
from common import *
import render_tap as tap
import kit3d as K
from narrate_cb import narrate
from render_led import common_load

FPS = 30
TAIL = 1.2
OUT = os.path.join(ROOT, "out", "fri13")
FRAMES = os.path.join(OUT, "frames")
SCRIPT = [
    "It's *Friday the 13th,*{thirteenth,} and a black cat just crossed his *path.*",
    "Up to *21{twenty-one} million* Americans fear this day. There's a word for it, and nobody can *say* it.",
    "In *1993,*{nineteen ninety-three,} British doctors checked. Hospital admissions from car crashes went *up.*",
    "Dutch insurers checked too. *Fewer* crashes. Probably because fewer people *drove.*",
    "So the day is only dangerous if you *don't believe in it.*",
    "And *2026*{twenty twenty-six} has *three* of them. The most a year can get.",
    "He survived the first two. He is not leaving the *house.*",
    "Send this to the friend who walks under ladders.",
]
KEYS = "ABCDEFGH"

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
    lines = narrate(SCRIPT, OUT, exaggeration=0.5, cfg=0.4, gap=0.26)
    from voice_fix import fixed                   # even the cadence (qa_voice.py must PASS on narration_fixed)
    lines = fixed(OUT)
    sents = to_sents(lines)
    speech_end = lines[-1]["end"]
    w = lambda si, sub, n=0: wn(sents, si, sub, n)
    E = {k: sents[i]["t0"] for i, k in enumerate(KEYS)}
    E.update({"friday": w(0, "Friday"), "cat": w(0, "cat"), "path": w(0, "path"), "million": w(1, "million"),
              "word": w(1, "word"), "say": w(1, "say"), "y1993": w(2, "1993"), "up": w(2, "up"),
              "fewer": w(3, "Fewer"), "drove": w(3, "drove"), "dont": w(4, "don't"), "believe": w(4, "believe"),
              "three": w(5, "three"), "most": w(5, "most"), "survived": w(6, "survived"), "house": w(6, "house"),
              "send": w(7, "Send"), "speech_end": speech_end})
    return lines, sents, speech_end, speech_end + TAIL, E

# ------------------------------------------------------------------ sound (recorded effects from the Sonniss GDC 2026 bundle)

F = {
    "perc": "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav",
    "pop": "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav",
    "snap": "Cinematic Sound Design - Interface & Infographics/Interface Accept Glassy Snap.wav",
    "woosh": "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav",
    "deny": "Cinematic Sound Design - System & UI Feedback Elements/Interface Deny Low Fat Dark.wav",
    "denymuted": "Cinematic Sound Design - UI Interaction Elements/Deny Muted.wav",
    "bassdown": "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Transition Bass Down.wav",
    "swoosh": "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Pull Swoosh Readout.wav",
    "kalimba": "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Kalimba 3 Up_CB Sounddesign_APPlicable Sounds.wav",
}

def build_audio(E, duration, path):
    import sfx
    n = int(duration * SR)
    tr = new_track(duration)
    voice = common_load(os.path.join(OUT, "narration_fixed.wav"))[:n]
    tr[:len(voice)] += voice                  # no ambience bed: no hum, buzz or drone (Austin, Oct 27)
    hit = lambda t0, key, gain, **kw: add(tr, t0, sfx.clip(F[key], **kw), gain)
    hit(0.0, "perc", 0.16)
    hit(E["say"], "denymuted", 0.18)
    for k in range(3):
        hit(E["up"] + 0.35 * k, "pop", 0.10, rate=1.1)           # hazard blinks
    hit(E["drove"] + 0.1, "perc", 0.2, rate=0.7)                  # the door shuts
    hit(E["believe"] - 0.25, "swoosh", 0.12, rate=1.3)            # the can starts to fall
    hit(E["believe"] + 0.05, "deny", 0.26, rate=0.8)              # the big moment: the loudest hit
    hit(E["believe"] + 0.1, "bassdown", 0.2)
    for k in range(3):
        hit(E["three"] + 0.25 * k, "snap", 0.12)
    hit(E["house"], "kalimba", 0.1)
    hit(E["send"], "perc", 0.14, rate=0.9)
    save_wav(tr, path, duration)

# ------------------------------------------------------------------ overlay

AMBER = skia.Color(255, 194, 122)
PAINT = skia.Color(255, 106, 26)

def smooth01(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

def draw_hook(c, a):
    if a <= 0:
        return
    y = 300
    for s, k in (("Is Friday the 13th unlucky?", False), ("Science checked", True)):
        f = font("Bricolage-800", 78 if not k else 84)
        wd = f.measureText(s) + (40 if k else 0)
        x = W / 2 - wd / 2
        if k:
            c.drawRRect(tap.rrect(x, y - 74, x + wd, y + 24, 16), paint(ORANGE, a))
            c.drawString(s, x + 20, y, f, paint(tap.PANEL2, a))
        else:
            c.drawString(s, x, y, f, paint(INK, a))
        y += 106

def pill(c, text, cx, y, a, color=INK, bg=K.DARK_PILL, size=36):
    if a <= 0:
        return
    f = font("JetBrainsMono-700", size)
    w = f.measureText(text)
    c.drawRRect(tap.rrect(cx - w / 2 - 22, y - size - 10, cx + w / 2 + 22, y + 16, 14), paint(bg, a))
    c.drawString(text, cx - w / 2, y, f, paint(color, a))

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, K.fade(t, -1, E["path"] + 0.6, 0.2))
    if t >= E["path"] + 0.4:
        tap.draw_captions(c, t, sents, cm)
    c.restore()
    lab = font("JetBrainsMono-700", 30)
    pill(c, "UP TO 21 MILLION AMERICANS", W / 2, 1460, K.fade(t, E["million"] - 0.1, E["say"] - 0.1, 0.2), AMBER)
    pill(c, "PARASKEVIDEKATRIAPHOBIA", W / 2, 1460, K.fade(t, E["say"] - 0.1, E["C"] - 0.1, 0.15), INK, size=40)
    pill(c, "BMJ 1993: 65 VS 45 ADMISSIONS", W / 2, 1420, K.fade(t, E["up"] - 0.1, E["D"] - 0.1, 0.2), AMBER, size=32)
    pill(c, "(ONE SMALL STUDY)", W / 2, 1490, K.fade(t, E["up"] - 0.1, E["D"] - 0.1, 0.2), MUTED, size=28)
    pill(c, "NL INSURERS: ~7,500 VS ~7,800 CLAIMS", W / 2, 1460, K.fade(t, E["fewer"] - 0.1, E["E"] - 0.1, 0.2), AMBER, size=30)
    pill(c, "BELIEF: NONE", W / 2, 1460, K.fade(t, E["E"] + 0.1, E["believe"] - 0.05, 0.15), INK)
    pill(c, "LADDER: WALKED UNDER", W / 2, 1460, K.fade(t, E["believe"] + 0.05, E["F"] - 0.1, 0.1), PAINT)
    for k, (txt, key) in enumerate((("FEB 13  SURVIVED", "three"), ("MAR 13  SURVIVED", "three"), ("NOV 13  TODAY", "most"))):
        t0 = E[key] + (0.25 * k if key == "three" else 0.0)
        pill(c, txt, W / 2, 1330 + 76 * k, K.fade(t, t0, E["G"] - 0.1, 0.12), PAINT if k == 2 else INK, size=34)
    for name, text, t0, t1, dx, dy, col in (("him", "BELIEVER", E["B"] + 0.1, E["C"] - 0.1, 190, -150, AMBER),
                                            ("bro", "NON-BELIEVER", E["E"] + 0.1, E["believe"] - 0.2, -190, -150, INK),
                                            ("cat", "THE CAT", E["survived"], E["H"] - 0.1, 170, -140, INK)):
        a = K.fade(t, t0, t1, 0.2)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, col, lab)
    u = t - E["believe"]
    if 0 <= u < 0.35:
        c.drawRect(skia.Rect(0, 0, W, H), paint(PAINT, 0.32 * (1 - u / 0.35)))
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
        print(json.dumps({k: round(v, 2) for k, v in E.items()}))
        print(f"duration {duration:.2f} s")
        return
    n_frames = int(round(duration * FPS))
    frames = sorted({min(n_frames - 1, int(round(x * FPS))) for x in preview_times}) if preview_times else list(range(n_frames))
    K.run_blender("fri13_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0 or x[2] > E["path"] + 0.3]
    if not preview_times:
        build_audio(E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "fri13" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] in ("narrate", "times"):
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
