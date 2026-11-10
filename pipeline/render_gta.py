"""'Boyfriends vs GTA 6': a deadpan voxel field report for the week before November 19, when boyfriends despawn.
Timely episode (ops/episodes/2026-11-10-gta-boyfriends.md), from the week's trend of girlfriends joking they lose
their boyfriends to the game. Voxel kit (gta_scene.py, a new night living-room set with a wall calendar), calm Chatterbox read.

python render_gta.py narrate             voice the script (cached in out/gta/voice), print the event times
python render_gta.py preview 1.0,12.5    render and composite stills into preview/
python render_gta.py out.mp4 out.wav     full render (Blender frames are cached in out/gta/frames)

Facts: GTA VI launches November 19, 2026 on PS5 and Xbox Series X|S; Rockstar confirmed it needs up to 212 GB
(https://gamesradar.com/games/grand-theft-auto/rockstar-confirms-gta-6-is-212gb-pre-loading-opens-earlier-than-previously-announced-for-digital-orders).
Name only: no Rockstar art, logos, characters or music.
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
OUT = os.path.join(ROOT, "out", "gta")
FRAMES = os.path.join(OUT, "frames")
SCRIPT = [
    "Field report. On *November 19,*{November nineteen,} boyfriends across the country begin to *despawn.*",
    "The cause is *GTA 6.*{GTA six.} A *212*{two hundred twelve} gigabyte download. Rockstar's own number.",
    "Early signs: he already *deleted four games* to make room. He never cleared that much space for you.",
    "Next, his replies shrink to *ya.* Last seen location: *Vice City.*",
    "Before he goes, protocol says she needs *reassurance.*",
    "So he says it out loud: *I love you more than GTA.*",
    "Then the console turns on, and he is *gone.*",
    "Send this to him now. You have *nine days.*",
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
    E.update({"nov": w(0, "November"), "despawn": w(0, "despawn"), "boys": w(0, "boyfriends"), "gta": w(1, "GTA"), "gb": w(1, "212"),
              "own": w(1, "Rockstar"), "deleted": w(2, "deleted"), "four": w(2, "four"), "space": w(2, "space"),
              "ya": w(3, "ya"), "seen": w(3, "seen"), "vice": w(3, "Vice"), "protocol": w(4, "protocol"),
              "reassure": w(4, "reassurance"), "out": w(5, "out"), "love": w(5, "love"), "more": w(5, "more"),
              "console": w(6, "console"), "gone": w(6, "gone"), "send": w(7, "Send"), "nine": w(7, "nine"),
              "speech_end": speech_end})
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
    hit(0.0, "perc", 0.18)
    hit(E["nov"], "pop", 0.16)
    hit(E["despawn"], "deny", 0.16, rate=1.1)
    hit(E["B"] - 0.25, "swoosh", 0.14)
    hit(E["gta"], "powerup", 0.16)
    hit(E["gb"], "perc", 0.16)
    for k in range(4):
        hit(E["four"] - 0.25 + 0.16 * k, "pop", 0.14, rate=1.0 + 0.08 * k)
    hit(E["space"], "bassdown", 0.2)
    hit(E["ya"], "denymuted", 0.22)
    hit(E["vice"], "woosh", 0.12)
    hit(E["protocol"], "snap", 0.14)
    hit(E["reassure"], "kalimba", 0.14)
    hit(E["love"], "magic", 0.14)
    hit(E["console"] - 0.05, "click", 0.3)
    hit(E["console"], "powerup", 0.18)
    hit(E["gone"], "bassdown", 0.22)
    hit(E["gone"] + 0.05, "swoosh", 0.12)
    hit(E["nine"], "perc", 0.18, rate=0.9)
    save_wav(tr, path, duration)

# ------------------------------------------------------------------ overlay

GOLD = skia.Color(255, 205, 60)
GREEN = skia.Color(90, 230, 120)

def smooth01(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

def draw_hook(c, a):
    if a <= 0:
        return
    y = 300
    for s, k in (("Nov 19:", False), ("boyfriends despawn", True)):
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

def draw_text_card(c, t, E):
    """His reply on her phone: a chat bubble that says 'ya'."""
    a = K.fade(t, E["ya"] - 0.1, E["E"] - 0.1, 0.15)
    if a <= 0:
        return
    drop = 1 - smooth01((t - E["ya"] + 0.1) / 0.25)
    x0, y0 = 150, 1060 - 80 * drop
    c.drawRRect(tap.rrect(x0, y0, W - 150, y0 + 250, 30), paint(skia.Color(236, 238, 242), a))
    c.drawString("him", x0 + 40, y0 + 58, font("JetBrainsMono-700", 30), paint(skia.Color(110, 110, 120), a))
    c.drawRRect(tap.rrect(x0 + 40, y0 + 88, x0 + 210, y0 + 200, 40), paint(skia.Color(205, 208, 215), a))
    c.drawString("ya", x0 + 82, y0 + 172, font("Bricolage-800", 70), paint(skia.Color(20, 20, 24), a))
    c.drawString("Read 2:14 AM", W - 150 - 260, y0 + 228, font("JetBrainsMono-500", 26), paint(skia.Color(120, 120, 130), a))

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, K.fade(t, -1, E["despawn"] + 0.6, 0.2))
    if t >= E["despawn"] + 0.4:
        tap.draw_captions(c, t, sents, cm)
    c.restore()
    lab = font("JetBrainsMono-700", 30)
    pill(c, "GTA 6 DOWNLOAD: 212 GB", W / 2, 1460, K.fade(t, E["gb"] - 0.1, E["C"] - 0.1, 0.2), GREEN)
    pill(c, "GAMES DELETED: 4", W / 2, 1460, K.fade(t, E["four"] - 0.1, E["space"] - 0.1, 0.2), INK)
    pill(c, "SPACE CLEARED FOR YOU: 0 GB", W / 2, 1460, K.fade(t, E["space"] - 0.1, E["D"] - 0.1, 0.2), tap.RED, size=32)
    draw_text_card(c, t, E)
    pill(c, "LAST SEEN: VICE CITY", W / 2, 1460, K.fade(t, E["seen"] - 0.1, E["E"] - 0.1, 0.2), GOLD)
    pill(c, "PROTOCOL: REASSURANCE", W / 2, 1460, K.fade(t, E["protocol"] - 0.1, E["F"] - 0.1, 0.2), INK)
    pill(c, "REASSURANCE: DELIVERED", W / 2, 1460, K.fade(t, E["love"] - 0.1, E["G"] - 0.1, 0.2), GREEN)
    pill(c, "BOYFRIEND DESPAWNED", W / 2, 1460, K.fade(t, E["gone"] - 0.05, E["H"] - 0.1, 0.2), tap.RED)
    pill(c, "NOV 19: 9 DAYS LEFT", W / 2, 1460, K.fade(t, E["nine"] - 0.1, speech_end + 0.6, 0.2), GOLD)
    for name, text, t0, t1, dx, dy, col in (("cal19", "NOV 19", 0.0, E["despawn"] + 0.6, 170, 150, tap.RED),
                                            ("bf", "SUBJECT", E["B"] + 0.2, E["gta"] + 1.2, 150, -150, INK),
                                            ("shelf", "4 GAMES", E["four"] - 0.4, E["space"] - 0.1, -180, -120, INK),
                                            ("gf", "HER", E["protocol"] - 0.1, E["F"] - 0.1, -150, -140, INK)):
        a = K.fade(t, t0, t1, 0.2)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, col, lab)
    u = t - E["console"]
    if 0 <= u < 0.35:
        c.drawRect(skia.Rect(0, 0, W, H), paint(skia.Color(150, 190, 255), 0.4 * (1 - u / 0.35)))
    u = t - E["gone"]
    if 0 <= u < 0.3:
        c.drawRect(skia.Rect(0, 0, W, H), paint(skia.Color(255, 255, 255), 0.25 * (1 - u / 0.3)))
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
    K.run_blender("gta_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0 or x[2] > E["despawn"] + 0.3]
    if not preview_times:
        build_audio(E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "gta" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
