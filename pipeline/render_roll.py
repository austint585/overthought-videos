"""'Your next relationship, randomized': a pause-to-play voxel short. A slot machine in a night arcade rolls four rows
(how you meet, how they text, their red flag, how it ends) the whole time, so wherever the viewer pauses they get a full
result. Timely: the random next-partner filter trend this week (ops/episodes/2026-11-10-relationship-roll.md).
Voxel kit (roll_scene.py, a new arcade set), calm Chatterbox read. No facts: every pick is a joke, none is a claim.

python render_roll.py narrate             voice the script (cached in out/roll/voice), print the event times
python render_roll.py preview 1.0,12.5    render and composite stills into preview/
python render_roll.py out.mp4 out.wav     full render (Blender frames are cached in out/roll/frames)
"""
import json, math, os, sys, random
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
OUT = os.path.join(ROOT, "out", "roll")
FRAMES = os.path.join(OUT, "frames")
SCRIPT = [
    "Pause the video now. Whatever you stopped on is your *next relationship.*",
    "Row one: how you *meet.* Row two: how they *text.*",
    "Row three: their *red flag.* Row four: how it *ends.*",
    "No rerolls. The machine has *spoken.*",
    "Comment what you got. *Be honest.*",
    "Missed it? It never stops. *Pause sooner.*",
]
KEYS = "ABCDEF"

ROWS = [
    ("HOW YOU MEET", ["at the gym", "in a group chat", "at a wedding", "their ex introduces you", "at self checkout",
                      "on a delayed flight", "at jury duty", "they slide into your DMs", "at your cousin's BBQ",
                      "in the comments of this reel", "fighting over the last cart", "the dog park"]),
    ("HOW THEY TEXT", ["only voice memos", "replies in 3 days", "full paragraphs", "just \"ya\"", "ALL CAPS",
                       "reels, no words", "double texts every time", "perfect grammar. scary", "emoji only",
                       "good morning at 5 AM", "\"k.\"", "reads, never replies"]),
    ("RED FLAG", ["friends with every ex", "has a podcast", "claps when the plane lands", "calls their mom 6x a day",
                  "doesn't like dogs", "ketchup on steak", "4 identical hoodies", "\"I'm not like other people\"",
                  "reads your texts out loud", "still uses a Hotmail", "a crypto tattoo", "no red flag. suspicious"]),
    ("HOW IT ENDS", ["married in 2 years", "ghosts you in March", "you move in together", "they move to Denver",
                     "best friends forever", "still a situationship", "taco truck wedding", "lost to GTA 6",
                     "3 kids and a dog", "you ghost them", "it's complicated", "Vegas. it's legal"]),
]
PICK_EVERY = 3                                     # frames per pick: 10 picks a second, readable when paused

def to_sents(lines):
    """narrate_cb lines -> the sentence dicts render_tap's captions read."""
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
    from voice_fix import fixed                   # evened cadence (Nov 10); qa_voice.py must PASS on narration_fixed
    lines = fixed(OUT)
    sents = to_sents(lines)
    speech_end = lines[-1]["end"]
    w = lambda si, sub, n=0: wn(sents, si, sub, n)
    E = {k: sents[i]["t0"] for i, k in enumerate(KEYS)}
    E.update({"pause": w(0, "Pause"), "next": w(0, "next"), "meet": w(1, "meet"), "text": w(1, "text"),
              "flag": w(2, "red"), "ends": w(2, "ends"), "rerolls": w(3, "rerolls"), "spoken": w(3, "spoken"),
              "comment": w(4, "Comment"), "honest": w(4, "honest"), "missed": w(5, "Missed"), "sooner": w(5, "sooner"),
              "speech_end": speech_end})
    return lines, sents, speech_end, speech_end + TAIL, E

# ------------------------------------------------------------------ sound (recorded effects from the Sonniss GDC 2026 bundle)

F = {
    "powerup": "Epic Stock Media - Anime Game/DSGNStngr_Power Up Bright Positive Successful Light Saturation Crash Shimmer 05_ESM_AG.wav",
    "perc": "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav",
    "pop": "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav",
    "snap": "Cinematic Sound Design - Interface & Infographics/Interface Accept Glassy Snap.wav",
    "swoosh": "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Pull Swoosh Readout.wav",
    "kalimba": "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Kalimba 3 Up_CB Sounddesign_APPlicable Sounds.wav",
    "deny": "Cinematic Sound Design - System & UI Feedback Elements/Interface Deny Low Fat Dark.wav",
    "click": "InMotionAudio - USA Hotel/MECHClik_USALightSwitch_On05_InMotionAudio_USAHotel.wav",
    "bassdown": "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Transition Bass Down.wav",
}

def build_audio(E, duration, path):
    import sfx
    n = int(duration * SR)
    tr = new_track(duration)
    voice = common_load(os.path.join(OUT, "narration_fixed.wav"))[:n]
    tr[:len(voice)] += voice                  # no ambience bed: no hum, buzz or drone (Austin, Oct 27)
    hit = lambda t0, key, gain, **kw: add(tr, t0, sfx.clip(F[key], **kw), gain)
    tick = sfx.clip(F["click"])
    t = 0.0
    while t < duration - 0.3:                  # the reel ticking, quiet, the whole time
        add(tr, t, tick, 0.05 if t < 0.5 else 0.035)
        t += 0.2
    hit(0.0, "swoosh", 0.16)
    hit(E["pause"], "perc", 0.16)
    hit(E["next"], "powerup", 0.14)
    for k in ("meet", "text", "flag", "ends"):
        hit(E[k], "pop", 0.14)
    hit(E["rerolls"], "deny", 0.16)
    hit(E["spoken"], "bassdown", 0.18)
    hit(E["comment"], "snap", 0.14)
    hit(E["missed"] - 0.1, "swoosh", 0.14)
    hit(E["sooner"], "kalimba", 0.14)
    save_wav(tr, path, duration)

# ------------------------------------------------------------------ overlay

GOLD = skia.Color(255, 205, 60)
PINK = skia.Color(255, 90, 170)
_order = []
rnd = random.Random(1111)
for label, opts in ROWS:
    seq = []
    while len(seq) < 400:
        o = opts[:]
        rnd.shuffle(o)
        if seq and o[0] == seq[-1]:
            o = o[1:] + o[:1]
        seq += o
    _order.append(seq)

def picks(Fr):
    k = Fr // PICK_EVERY
    return [_order[r][(k * (3 + r) + 7 * r) % len(_order[r])] for r in range(4)]

def draw_cards(c, Fr, t, E):
    """Four result cards, always complete, so a paused frame is a full reading."""
    res = picks(Fr)
    x0, x1, y = 90, W - 90, 760
    hl = [("meet", "text"), ("text", "flag"), ("flag", "ends"), ("ends", "rerolls")]
    for r, (label, _) in enumerate(ROWS):
        lit = E[hl[r][0]] - 0.1 <= t < E[hl[r][1]] - 0.1
        c.drawRRect(tap.rrect(x0, y, x1, y + 130, 22), paint(K.DARK_PILL, 0.82))
        if lit:
            c.drawRRect(tap.rrect(x0, y, x1, y + 130, 22), tap.stroke(GOLD, 5, 1.0))
        c.drawString(label, x0 + 30, y + 40, font("JetBrainsMono-700", 26), paint(PINK if not lit else GOLD, 1.0))
        txt = res[r]
        f = font("Bricolage-800", 56)
        while f.measureText(txt) > x1 - x0 - 60 and f.getSize() > 30:
            f = font("Bricolage-800", f.getSize() - 2)
        c.drawString(txt, x0 + 30, y + 106, f, paint(INK, 1.0))
        y += 150

def draw_hook(c, a):
    if a <= 0:
        return
    y = 330
    for s, k in (("PAUSE NOW", True), ("= your next relationship", False)):
        f = font("Bricolage-800", 96 if k else 60)
        wd = f.measureText(s) + (40 if k else 0)
        x = W / 2 - wd / 2
        if k:
            c.drawRRect(tap.rrect(x, y - 84, x + wd, y + 26, 18), paint(ORANGE, a))
            c.drawString(s, x + 20, y, f, paint(tap.PANEL2, a))
        else:
            c.drawString(s, x, y, f, paint(INK, a))
        y += 100

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    K.top_shade(c, height=760, alpha=205)         # darker than the kit's: the close-ups put the pale pink machine behind the captions
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, K.fade(t, -1, E["B"] - 0.2, 0.2))
    if t >= E["B"] - 0.2:
        tap.draw_captions(c, t, sents, cm)
    c.restore()
    draw_cards(c, Fr, t, E)
    a = K.fade(t, E["rerolls"] - 0.1, E["E"] - 0.1, 0.2)
    if a > 0:
        f = font("JetBrainsMono-700", 36)
        wd = f.measureText("REROLLS LEFT: 0")
        c.drawRRect(tap.rrect(W / 2 - wd / 2 - 22, 1414, W / 2 + wd / 2 + 22, 1476, 14), paint(K.DARK_PILL, a))
        c.drawString("REROLLS LEFT: 0", W / 2 - wd / 2, 1460, f, paint(tap.RED, a))
    u = t - E["spoken"]
    if 0 <= u < 0.3:
        c.drawRect(skia.Rect(0, 0, W, H), paint(GOLD, 0.2 * (1 - u / 0.3)))
    if t > speech_end + 0.1:
        a = smooth01((t - speech_end - 0.1) / 0.4)
        text_center(c, "@overthought.daily", W / 2, 1530, font("JetBrainsMono-500", 32), paint(MUTED, a))

def smooth01(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

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
    K.run_blender("roll_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0 or x[2] > E["B"] - 0.3]
    if not preview_times:
        build_audio(E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "roll" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
