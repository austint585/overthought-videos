"""'The 11:11 wish window': a deadpan voxel short for November 11. The 11:11 wish treated as a game event: two windows a
day, a 0.14 percent drop rate, double XP when the date matches, and the frequency illusion as the patch notes.
Timely episode (ops/episodes/2026-11-09-wish-window.md); voxel kit (wish_scene.py, a new night rooftop set with a
giant digital clock), calm Chatterbox read.

python render_wish.py narrate             voice the script (cached in out/wish/voice), print the event times
python render_wish.py preview 1.0,12.5    render and composite stills into preview/
python render_wish.py out.mp4 out.wav     full render (Blender frames are cached in out/wish/frames)

Facts: 11:11 shows twice a day on a 12-hour clock, 2 of 1,440 minutes (arithmetic). "Frequency illusion" was coined by
Stanford linguist Arnold Zwicky in a 2005 Language Log post (https://en.wikipedia.org/wiki/Frequency_illusion,
https://languagelog.ldc.upenn.edu/nll/?p=42180): selective attention plus confirmation bias.
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
TAIL = 1.4
OUT = os.path.join(ROOT, "out", "wish")
FRAMES = os.path.join(OUT, "frames")
SCRIPT = [
    "Today at *11:11,*{eleven eleven,} the wish server opens its *rarest window* of the year.",
    "A normal day only spawns *two* wish windows. Two minutes out of *1,440.*{fourteen forty.}",
    "That's a *0.14%*{zero point one four percent} drop rate.",
    "But today the date is *11/11*{eleven eleven} too. *Eight ones* on one screen. *Double XP.*",
    "If you always catch *11:11,*{eleven eleven,} a linguist named that in *2005.*{two thousand five.} The *frequency illusion.*",
    "Your brain *saves the hits* and *forgets* the other *1,438*{fourteen thirty-eight} minutes.",
    "So the sign from the universe is mostly your *screen time.*",
    "Set an alarm for *11:10.*{eleven ten.} *Lock in.* The next one is *a year away.*",
]
KEYS = "ABCDEFGH"

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
    sents = to_sents(lines)
    speech_end = lines[-1]["end"]
    w = lambda si, sub, n=0: wn(sents, si, sub, n)
    E = {k: sents[i]["t0"] for i, k in enumerate(KEYS)}
    E.update({"flip": w(0, "11:11"), "rarest": w(0, "rarest"), "two": w(1, "two"), "1440": w(1, "1,440"),
              "drop": w(2, "0.14"), "date": w(3, "11/11"), "eight": w(3, "Eight"), "xp": w(3, "Double"),
              "catch": w(4, "11:11"), "2005": w(4, "2005"), "illusion": w(4, "frequency"), "hits": w(5, "saves"),
              "forgets": w(5, "forgets"), "1438": w(5, "1,438"), "universe": w(6, "universe"), "screen": w(6, "screen"),
              "alarm": w(7, "alarm"), "lock": w(7, "Lock"), "year": w(7, "year"), "speech_end": speech_end})
    return lines, sents, speech_end, speech_end + TAIL, E

# ------------------------------------------------------------------ sound (recorded effects from the Sonniss GDC 2026 bundle)

F = {
    "magic": "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/GAMEMisc_Magic Creation 23_CB Sounddesign_APPlicable Sounds.wav",
    "powerup": "Epic Stock Media - Anime Game/DSGNStngr_Power Up Bright Positive Successful Light Saturation Crash Shimmer 05_ESM_AG.wav",
    "perc": "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav",
    "pop": "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav",
    "snap": "Cinematic Sound Design - Interface & Infographics/Interface Accept Glassy Snap.wav",
    "swoosh": "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Pull Swoosh Readout.wav",
    "woosh": "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav",
    "kalimba": "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Kalimba 3 Up_CB Sounddesign_APPlicable Sounds.wav",
    "deny": "Cinematic Sound Design - System & UI Feedback Elements/Interface Deny Low Fat Dark.wav",
    "denymuted": "Cinematic Sound Design - UI Interaction Elements/Deny Muted.wav",
    "click": "InMotionAudio - USA Hotel/MECHClik_USALightSwitch_On05_InMotionAudio_USAHotel.wav",
    "bassdown": "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Transition Bass Down.wav",
    "wind": "344 Audio - Elemental Palette Designed Vol. 1/WINDDsgn_Wind, Rush, Whoosh, Long x5 01_344 Audio_Elemental Palette Designed Vol 1.wav",
}

def build_audio(E, duration, path):
    import sfx
    n = int(duration * SR)
    tr = new_track(duration)
    voice = common_load(os.path.join(OUT, "narration.wav"))[:n]
    tr[:len(voice)] += voice                  # no ambience bed: no hum, buzz or drone (Austin, Oct 27)
    hit = lambda t0, key, gain, **kw: add(tr, t0, sfx.clip(F[key], **kw), gain)
    hit(0.0, "wind", 0.06, lp=1800, dur=2.5)
    hit(E["flip"] - 0.05, "click", 0.3)
    hit(E["flip"], "magic", 0.16)
    hit(E["two"], "pop", 0.16)
    hit(E["1440"], "perc", 0.16)
    hit(E["drop"], "deny", 0.16, rate=1.1)
    hit(E["date"] - 0.05, "click", 0.28)
    hit(E["eight"], "snap", 0.16)
    hit(E["xp"] - 0.1, "powerup", 0.2)
    hit(E["E"] - 0.25, "swoosh", 0.16)
    hit(E["2005"], "perc", 0.14)
    hit(E["illusion"], "kalimba", 0.14)
    hit(E["hits"], "snap", 0.14, rate=1.1)
    hit(E["forgets"], "denymuted", 0.22)
    hit(E["universe"] - 0.2, "woosh", 0.14)
    hit(E["screen"], "bassdown", 0.22)
    hit(E["alarm"], "pop", 0.16, rate=1.2)
    hit(E["lock"], "perc", 0.2, rate=0.9)
    hit(E["year"] + 0.3, "click", 0.26)
    save_wav(tr, path, duration)

# ------------------------------------------------------------------ overlay

GOLD = skia.Color(255, 205, 60)

def smooth01(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

def draw_hook(c, a):
    if a <= 0:
        return
    y = 300
    for s, k in (("11/11 at 11:11", False), ("rarest wish window", True)):
        f = font("Bricolage-800", 88)
        wd = f.measureText(s) + (40 if k else 0)
        x = W / 2 - wd / 2
        if k:
            c.drawRRect(tap.rrect(x, y - 76, x + wd, y + 24, 16), paint(ORANGE, a))
            c.drawString(s, x + 20, y, f, paint(tap.PANEL2, a))
        else:
            c.drawString(s, x, y, f, paint(INK, a))
        y += 108

def pill(c, text, cx, y, a, color=INK, bg=K.DARK_PILL, size=36):
    if a <= 0:
        return
    f = font("JetBrainsMono-700", size)
    w = f.measureText(text)
    c.drawRRect(tap.rrect(cx - w / 2 - 22, y - size - 10, cx + w / 2 + 22, y + 16, 14), paint(bg, a))
    c.drawString(text, cx - w / 2, y, f, paint(color, a))

def draw_hits(c, t, E):
    """Saved hits vs forgotten misses: little clock cards, 11:11 stays, the rest fade out."""
    a = K.fade(t, E["F"] - 0.15, E["G"] - 0.1, 0.25)
    if a <= 0:
        return
    cards = [("11:11", 160, 1080, True), ("3:47", 420, 1010, False), ("11:11", 700, 1120, True), ("9:02", 900, 1000, False),
             ("6:28", 250, 1260, False), ("11:11", 560, 1300, True), ("1:13", 850, 1250, False), ("4:56", 420, 1430, False),
             ("11:11", 780, 1420, True), ("10:39", 160, 1430, False)]
    f = font("JetBrainsMono-800", 44)
    for k, (s, x, y, hit) in enumerate(cards):
        b = a * smooth01((t - E["F"] - 0.08 * k) / 0.2)
        if not hit:
            b *= 1 - 0.85 * smooth01((t - E["forgets"]) / 0.4)
        if b <= 0.01:
            continue
        w = f.measureText(s)
        col = GOLD if hit else MUTED
        c.drawRRect(tap.rrect(x - w / 2 - 20, y - 52, x + w / 2 + 20, y + 16, 14), paint(K.DARK_PILL, b))
        if hit:
            c.drawRRect(tap.rrect(x - w / 2 - 20, y - 52, x + w / 2 + 20, y + 16, 14), tap.stroke(GOLD, 4, b))
        c.drawString(s, x - w / 2, y, f, paint(col, b))
    pill(c, "SAVED: 2   FORGOTTEN: 1,438", W / 2, 1530, K.fade(t, E["1438"] - 0.1, E["G"] - 0.1, 0.2), GOLD, size=32)

def draw_screen(c, t, E):
    a = K.fade(t, E["screen"] - 0.1, E["H"] - 0.1, 0.2)
    if a <= 0:
        return
    drop = 1 - smooth01((t - E["screen"] + 0.1) / 0.3)
    x0, y0 = 120, 1040 - 100 * drop
    c.drawRRect(tap.rrect(x0, y0, W - 120, y0 + 230, 30), paint(skia.Color(236, 238, 242), a))
    dk = skia.Color(20, 20, 24)
    c.drawString("SCREEN TIME", x0 + 40, y0 + 64, font("JetBrainsMono-700", 30), paint(skia.Color(110, 110, 120), a))
    c.drawString("yes.", x0 + 40, y0 + 150, font("Bricolage-800", 84), paint(dk, a))
    c.drawString("Daily average: up again", x0 + 40, y0 + 200, font("JetBrainsMono-700", 28), paint(skia.Color(80, 80, 90), a))

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, K.fade(t, -1, E["flip"] + 0.9, 0.2))
    if t >= E["flip"] + 0.7:
        tap.draw_captions(c, t, sents, cm)
    c.restore()
    lab = font("JetBrainsMono-700", 30)
    pill(c, "WINDOWS PER DAY: 2 / 1,440 MIN", W / 2, 1460, K.fade(t, E["two"] - 0.1, E["C"] - 0.1, 0.2), INK, size=32)
    pill(c, "DROP RATE: 0.14%", W / 2, 1460, K.fade(t, E["drop"] - 0.1, E["D"] - 0.1, 0.2), tap.RED)
    a = K.fade(t, E["xp"] - 0.1, E["E"] - 0.15, 0.15)
    if a > 0:
        s = 1.0 + 0.25 * max(0.0, 1 - (t - E["xp"] + 0.1) / 0.2)
        c.save(); c.translate(W / 2, 1440); c.scale(s, s)
        f = font("Bricolage-800", 110)
        wd = f.measureText("DOUBLE XP")
        c.drawRRect(tap.rrect(-wd / 2 - 30, -100, wd / 2 + 30, 30, 22), paint(GOLD, a))
        c.drawString("DOUBLE XP", -wd / 2, 0, f, paint(tap.PANEL2, a))
        c.restore()
    for name, text, t0, t1, dx, dy, col in (("ones", "8 ONES", E["eight"] - 0.1, E["xp"] - 0.1, 150, -120, GOLD),
                                            ("you", "YOU, CHECKING", E["catch"] - 0.1, E["2005"] - 0.1, 120, -160, INK)):
        a = K.fade(t, t0, t1, 0.2)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, col, lab)
    pill(c, "FREQUENCY ILLUSION (ZWICKY, 2005)", W / 2, 1460, K.fade(t, E["illusion"] - 0.1, E["F"] - 0.1, 0.2), GOLD, size=30)
    draw_hits(c, t, E)
    draw_screen(c, t, E)
    pill(c, "ALARM  11:10 AM", W / 2, 1460, K.fade(t, E["alarm"] - 0.1, E["year"] - 0.1, 0.2), INK)
    pill(c, "NEXT 11/11: ONE YEAR", W / 2, 1460, K.fade(t, E["year"] - 0.05, speech_end + 0.6, 0.2), GOLD)
    u = t - E["flip"]
    if 0 <= u < 0.3:
        c.drawRect(skia.Rect(0, 0, W, H), paint(GOLD, 0.35 * (1 - u / 0.3)))
    u = t - E["date"]
    if 0 <= u < 0.3:
        c.drawRect(skia.Rect(0, 0, W, H), paint(GOLD, 0.25 * (1 - u / 0.3)))
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
    K.run_blender("wish_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0 or x[2] > E["flip"] + 0.6]
    if not preview_times:
        build_audio(E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "wish" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
