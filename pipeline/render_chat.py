"""Episode: Nobody answered (ops/episodes/2026-11-03-group-chat-bystander.md). The group chat that leaves you on read, explained
with the 1968 Darley and Latane intercom study, in the toon kit (toon.py, chat_scene.py): phones as the cast, calm Chatterbox
read, yellow outlined captions.

python render_chat.py narrate                voice the script (cached in out/chat/voice), print the timing
python render_chat.py preview 1.0,9.5        stills into preview/chat_*.png
python render_chat.py out.mp4 out.wav        full render (Blender frames cached in out/chat/frames)
"""
import json, os, subprocess, sys, time
import numpy as np
import skia
import common
from common import *
import kit3d as K
import sfx
from narrate_cb import narrate
from render_led import common_load
from render_height import make_overlay as _height_overlay
import render_height as RH

FPS = 30
OUT = os.path.join(ROOT, "out", "chat")
FRAMES = os.path.join(OUT, "frames")
TAIL = 1.2

# (line, [(shot, word index the shot starts on), ...]); *word* is colored in the caption
SCRIPT = [
    ("You asked the group chat a question. Fourteen people saw it. Nobody *answered.*", [("couch", 0), ("chat", 7)]),
    ("That's not rude. Psychologists call it the *bystander effect.*", [("label", 0)]),
    ("In nineteen sixty eight, students heard what sounded like another student having a *seizure* over an intercom.",
     [("booth", 0), ("booth~2", 9)]),
    ("When they thought they were the only one listening, *eighty five percent* reported it.", [("alone", 0)]),
    ("When they thought four other people could hear it, only *thirty one percent* did.", [("group", 0)]),
    ("Everyone assumes somebody else will *handle it.*", [("assume", 0)]),
    ("So don't ask the group. Ask one person, *by name.*", [("name", 0)]),
    ("Or send this to the group chat, and watch *nobody* reply.", [("final", 0)]),
]
HOOK = ["14 people saw it", "Nobody answered"]

def timeline():
    lines = narrate([l for l, _ in SCRIPT], OUT, exaggeration=0.5, cfg=0.4, gap=0.22)
    shots = []
    for (line, plan), L in zip(SCRIPT, lines):
        for name, wi in plan:
            t = L["words"][wi]["start"] - 0.08 if wi else L["start"] - 0.08
            shots.append([0.0 if not shots else round(t, 3), name])
    return lines, shots, lines[-1]["end"] + TAIL

SOURCES = "Data: Darley & Latane 1968, J. of Personality and Social Psychology"

def make_overlay(lines, shots, duration):
    RH.HOOK = HOOK
    base = _height_overlay(lines, shots, duration)
    t_final = next(t for t, n in shots if n == "final")
    def overlay(c, t, F):
        base(c, t, F)
        if t >= t_final:                                    # honesty note, small, top of frame
            f = font("Fredoka-700", 30)
            wd = f.measureText(SOURCES)
            x = (W - wd) / 2
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 18, 150, x + wd + 18, 198), 14, 14),
                        skia.Paint(Color=skia.ColorSetARGB(200, 12, 14, 26), AntiAlias=True))
            c.drawString(SOURCES, x, 185, f, skia.Paint(Color=skia.ColorWHITE, AntiAlias=True))
    return overlay

# ------------------------------------------------------------------ sound

SNAP = "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav"
POP = "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav"
GLASSY = "Cinematic Sound Design - Interface & Infographics/Interface Accept Glassy Snap.wav"
BUBBLES = "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Bubbles Short.wav"
DOWN = "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Transition Bass Down.wav"
WIND = "344 Audio - Elemental Palette Designed Vol. 1/WINDDsgn_Wind, Rush, Whoosh, Long x5 01_344 Audio_Elemental Palette Designed Vol 1.wav"
KALIMBA = "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Kalimba 3 Up_CB Sounddesign_APPlicable Sounds.wav"
SWOOSH = "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Pull Swoosh Readout.wav"

def build_audio(lines, shots, duration, out_wav):
    track = np.zeros(int((duration + 1) * SR), np.float32)
    def add(t, x, gain):
        a = int(max(0.0, t) * SR)
        x = x[: len(track) - a]
        track[a:a + len(x)] += x * gain
    add(0.0, common_load(os.path.join(OUT, "narration.wav")), 1.0)
    start, end = {}, {}
    for i, (t, n) in enumerate(shots):
        start.setdefault(n, t)
        end[n] = shots[i + 1][0] if i + 1 < len(shots) else duration
    add(0.3, sfx.clip(GLASSY, 0.0, 0.4), 0.2)                         # the message sends
    for k in range(3):                                                  # typing dots come and go
        add(start["chat"] + 0.5 + k * 0.9, sfx.clip(POP, 0.0, 0.15, lp=2600), 0.12)
    add(start["label"] + 0.25, sfx.clip(SNAP, 0.0, 0.2, lp=1500), 0.3)  # the sign lands
    add(start["booth~2"] + 0.1, sfx.clip(BUBBLES, 0.0, 0.6, lp=2000), 0.12)   # the intercom crackles
    add(start["alone"] + 0.4, sfx.clip(SWOOSH, 0.0, 0.6), 0.14)         # he runs for the door
    add(start["alone"] + 0.6, sfx.clip(POP, 0.0, 0.3), 0.16)
    add(start["group"] + 0.6, sfx.clip(POP, 0.0, 0.3, lp=1500), 0.14)
    for k in range(5):                                                  # each phone points at the next
        add(start["assume"] + 0.3 + k * 0.18, sfx.clip(SNAP, 0.0, 0.12, hp=900), 0.16)
    add(start["name"] + 0.2, sfx.clip(KALIMBA, 0.0, 1.2), 0.12)         # the spotlight
    add(start["final"] + 0.3, sfx.clip(GLASSY, 0.0, 0.4), 0.18)
    add(start["final"] + 0.9, sfx.clip(WIND, 0.0, 2.2, lp=2500), 0.08)  # tumbleweed
    save_wav(track, out_wav, duration)

# ------------------------------------------------------------------ main

def main(out_mp4=None, out_wav=None, preview_times=None):
    common.FPS = FPS
    lines, shots, duration = timeline()
    if out_mp4 is None and preview_times is None:
        for t, n in shots:
            print(f"{t:6.2f} {n}")
        print(f"duration {duration:.2f} s")
        return
    os.makedirs(FRAMES, exist_ok=True)
    n = int(round(duration * FPS))
    frames = sorted({min(n - 1, int(round(x * FPS))) for x in preview_times}) if preview_times else list(range(n))
    tj = os.path.join(OUT, "timing.json")
    json.dump({"fps": FPS, "duration": duration, "shots": shots}, open(tj, "w"))
    t0 = time.time()
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "chat_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots, duration), out_mp4, out_wav, "chat" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
