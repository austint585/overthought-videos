"""'The bicep heart, a nature documentary' (ops/episodes/2026-11-13-bicep-heart.md). A hushed narrator treats the
bicep heart trend as a courtship display: the gym bro at the mirror, the fiddler crab that waves one giant claw, the
2018 robot-crab study (females prefer waves that speed up), and the payoff: she walks past him and does her own.
Clay kit (bicep_scene.py), calm Chatterbox read.

python render_bicep.py narrate             voice the script (cached in out/bicep/voice), print the event times
python render_bicep.py preview 1.0,12.5    render and composite stills into preview/
python render_bicep.py out.mp4 out.wav     full render (Blender frames are cached in out/bicep/frames)

Sources: Know Your Meme on the trend; National Geographic and UTMSI on the claw (up to half the body);
Mowles, Jennions and Backwell, Biology Letters 2018 (robot crabs, females prefer accelerating waves).
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
TAIL = 1.0
OUT = os.path.join(ROOT, "out", "bicep")
FRAMES = os.path.join(OUT, "frames")
SCRIPT = [
    "At the gym mirror, the male performs the *bicep heart.*",
    "One arm flexes. The other hand curls over the top. A *heart.*",
    "Biologists have seen this before. On a *mudflat.*",
    "The male fiddler crab grows one giant claw. It can weigh *half his body.*",
    "He waves it at every female who walks past.",
    "In *2018,*{twenty eighteen,} scientists used *robot crabs.* Females chose the waves that sped *up.*",
    "So the male *speeds up.*",
    "She walks right past him. And does *her own.*",
    "Send this to the guy who flexes in the gym mirror.",
]
KEYS = "ABCDEFGHI"

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
    E.update({"bicep": w(0, "bicep"), "flexes": w(1, "flexes"), "curls": w(1, "curls"), "heart": w(1, "heart"),
              "mudflat": w(2, "mudflat"), "claw": w(3, "claw"), "half": w(3, "half"), "waves": w(4, "waves"),
              "female": w(4, "female"), "robot": w(5, "robot"), "chose": w(5, "chose"), "up": w(5, "up", 0),
              "speeds": w(6, "speeds"), "past": w(7, "past"), "does": w(7, "does"), "own": w(7, "own"),
              "send": w(8, "Send"), "speech_end": speech_end})
    s5 = sents[5]
    E["up"] = s5["abs_starts"][-1]                  # the last word, "up."
    return lines, sents, speech_end, speech_end + TAIL, E

# ------------------------------------------------------------------ sound (recorded effects from the Sonniss GDC 2026 bundle)

F = {
    "perc": "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav",
    "pop": "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav",
    "snap": "Cinematic Sound Design - Interface & Infographics/Interface Accept Glassy Snap.wav",
    "woosh": "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav",
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
    hit(0.0, "perc", 0.14)
    hit(E["heart"], "pop", 0.12)
    hit(E["C"] - 0.05, "woosh", 0.08)
    hit(E["half"], "pop", 0.1, rate=0.8)
    for k in range(4):                                       # claw waves
        hit(E["waves"] + 0.45 * k, "pop", 0.05, rate=1.2)
    for k in range(5):                                       # the robot speeds up
        hit(E["robot"] + 0.6 * k * (1 - 0.12 * k), "pop", 0.05, rate=1.4)
    hit(E["up"], "snap", 0.1)
    for k in range(4):
        hit(E["speeds"] + 0.32 * k * (1 - 0.15 * k), "perc", 0.06, rate=1.2)
    hit(E["own"] - 0.2, "swoosh", 0.12, rate=1.2)
    hit(E["own"], "kalimba", 0.22)                           # the big moment: the loudest hit
    hit(E["own"], "snap", 0.16, rate=0.8)
    hit(E["send"], "perc", 0.12, rate=0.9)
    save_wav(tr, path, duration)

# ------------------------------------------------------------------ overlay

AMBER = skia.Color(255, 194, 122)
PINK = skia.Color(255, 63, 138)

def smooth01(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

def draw_hook(c, a):
    if a <= 0:
        return
    f1, f2 = font("Bricolage-800", 92), font("Bricolage-700", 54)
    text_center(c, "THE BICEP HEART", W / 2, 320, f1, paint(INK, a))
    text_center(c, "a nature documentary", W / 2, 400, f2, paint(AMBER, a))

def pill(c, text, cx, y, a, color=INK, bg=K.DARK_PILL, size=36):
    if a <= 0:
        return
    f = font("JetBrainsMono-700", size)
    w = f.measureText(text)
    c.drawRRect(tap.rrect(cx - w / 2 - 22, y - size - 10, cx + w / 2 + 22, y + 16, 14), paint(bg, a))
    c.drawString(text, cx - w / 2, y, f, paint(color, a))

def heart_path(cx, cy, s):
    p = skia.Path()
    p.moveTo(cx, cy + 0.9 * s)
    p.cubicTo(cx - 1.3 * s, cy + 0.1 * s, cx - 1.0 * s, cy - 1.0 * s, cx, cy - 0.45 * s)
    p.cubicTo(cx + 1.0 * s, cy - 1.0 * s, cx + 1.3 * s, cy + 0.1 * s, cx, cy + 0.9 * s)
    return p

def draw_heart(c, p, s, a, color, draw=1.0, width=7):
    """A thin hand-drawn heart over the pose, like a documentary annotation; `draw` traces it on (0..1)."""
    if a <= 0 or p is None:
        return
    path = heart_path(p[0], p[1], s)
    pt = skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width, Color=color,
                    StrokeCap=skia.Paint.kRound_Cap)
    pt.setAlphaf(a)
    if draw < 1.0:
        meas = skia.PathMeasure(path, False)
        seg = skia.Path()
        meas.getSegment(0, meas.getLength() * max(0.0, draw), seg, True)
        path = seg
    c.drawPath(path, pt)

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, K.fade(t, -1, E["B"] - 0.1, 0.2))
    if t >= E["B"] - 0.15:
        tap.draw_captions(c, t, sents, cm)
    c.restore()
    lab = font("JetBrainsMono-700", 30)
    # the heart annotation: already drawn on frame 0 (the thumbnail), retraced on "heart", gone in the mudflat
    a_h = K.fade(t, -1, E["C"] - 0.1, 0.15) + K.fade(t, E["speeds"] - 0.1, E["H"] - 0.1, 0.15)
    a_h += K.fade(t, E["I"] - 0.05, 99, 0.1)
    if a_h > 0:
        dr = 1.0 if t < E["curls"] or t > E["C"] else smooth01((t - E["curls"]) / max(0.3, E["heart"] - E["curls"] + 0.1))
        beat = 1.0
        if E["speeds"] <= t < E["H"]:
            beat = 1.0 + 0.08 * max(0.0, math.sin((t - E["speeds"]) * (9 + 6 * (t - E["speeds"]))))
        draw_heart(c, K.anchor(A, "heart", Fr), 92 * beat, min(1.0, a_h), INK, dr)
    a_s = K.fade(t, E["own"], 99, 0.08) * (1 - K.fade(t, E["I"] - 0.05, 99, 0.05))
    if a_s > 0:
        draw_heart(c, K.anchor(A, "sheart", Fr), 92, a_s, PINK, smooth01((t - E["own"]) / 0.3), 9)
    pill(c, "ALSO A COURTSHIP DISPLAY", W / 2, 1460, K.fade(t, E["mudflat"] - 0.1, E["D"] - 0.1, 0.2), AMBER, size=32)
    pill(c, "CLAW: UP TO 1/2 HIS BODY WEIGHT", W / 2, 1460, K.fade(t, E["half"] - 0.1, E["E"] - 0.1, 0.2), AMBER, size=32)
    pill(c, "BIOLOGY LETTERS, 2018", W / 2, 1420, K.fade(t, E["robot"] - 0.1, E["G"] - 0.1, 0.2), INK, size=30)
    pill(c, "FASTER WAVE > STEADY WAVE", W / 2, 1490, K.fade(t, E["up"] - 0.05, E["G"] - 0.1, 0.15), AMBER, size=30)
    for name, text, t0, t1, dx, dy, col in (("crab", "MALE", E["claw"] - 0.1, E["half"] - 0.1, -170, -150, INK),
                                            ("fem", "FEMALE", E["female"] - 0.1, E["F"] - 0.1, 170, -140, INK),
                                            ("robot", "ROBOT", E["robot"], E["chose"], 180, -150, INK)):
        a = K.fade(t, t0, t1, 0.2)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, col, lab)
    u = t - E["own"]
    if 0 <= u < 0.3:
        c.drawRect(skia.Rect(0, 0, W, H), paint(PINK, 0.18 * (1 - u / 0.3)))
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
    mirror = []          # (Cycles mirror shots dropped: his reflection hid behind his own back; all Eevee now)
    if mirror:
        os.environ["BICEP_CYCLES"] = "1"
        todo = mirror if preview_times else [f for f in mirror if not os.path.exists(os.path.join(FRAMES, f"f_{f + 1:05d}.png"))]
        if todo:
            K.run_blender("bicep_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in todo), E, duration, FPS)
        os.environ.pop("BICEP_CYCLES")
    rest = [f for f in frames if f not in mirror]
    if rest:
        K.run_blender("bicep_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in rest) if preview_times else "all",
                      E, duration, FPS)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = tap.build_chunk_map(sents)
    if not preview_times:
        build_audio(E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "bicep" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] in ("narrate", "times"):
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
