"""Episode: The Yawn Test (ops/episodes/2026-11-06-yawn-test.md). A tag-a-friend joke on Norscia and Palagi (PLoS ONE,
2011): 109 adults watched yawning in everyday life for a year; yawns spread most from family, then friends, then
acquaintances, then strangers, and family and friends caught them faster. Toon kit (toon.py, yawn_scene.py). Calm read,
yellow outlined captions. Built from render_nap.py.

python render_yawn.py narrate                voice the script (cached in out/yawn/voice), print the timing
python render_yawn.py preview 1.0,9.5        stills into preview/yawn_*.png
python render_yawn.py out.mp4 out.wav        full render (Blender frames cached in out/yawn/frames)
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
OUT = os.path.join(ROOT, "out", "yawn")
FRAMES = os.path.join(OUT, "frames")
TAIL = 1.2

# (line, [(shot, word index the shot starts on), ...], {event: word index}); *word* is colored in the caption
SCRIPT = [
    ("You just yawned because your friend yawned. That's a *friendship test.*", [("couch", 0)], {}),
    ("Researchers in Italy watched 109{a hundred and nine} adults yawn in real life for a *whole year.*", [("study", 0)], {}),
    ("Yawns spread the most between family. Then *friends.*", [("family", 0)], {"family": 5, "friends": 7}),
    ("Then people you barely know. Strangers came *last.*", [("strangers", 0)], {"barely": 3, "last": 7}),
    ("Most family yawned back within a minute. About half of friends *did too.*", [("timing", 0)], {"half": 7}),
    ("Strangers mostly took two or three *minutes.*", [], {"strangers": 0}),
    ("So if your friend yawns and you don't, *think about that.*", [("think", 0)], {}),
    ("Tag the friend who just made you *yawn.*", [("final", 0)], {}),
]
HOOK = ["THE YAWN TEST", "DID YOU PASS?"]

def timeline():
    if os.environ.get("OT_VOICE") == "kokoro":            # Chatterbox needs ~4 GB free commit; Kokoro is the low-memory fallback
        from narrate_kk import narrate as kk
        lines = kk([l for l, _, _ in SCRIPT], OUT, gap=0.22)
    else:
        lines = narrate([l for l, _, _ in SCRIPT], OUT, exaggeration=0.5, cfg=0.4, gap=0.22)
    shots, ev = [], {}
    for (line, plan, evs), L in zip(SCRIPT, lines):
        for name, wi in plan:
            wi = min(wi, len(L["words"]) - 1)
            t = L["words"][wi]["start"] - 0.08 if wi else L["start"] - 0.08
            shots.append([0.0 if not shots else round(t, 3), name])
        for k, wi in evs.items():
            ev[k] = L["words"][min(wi, len(L["words"]) - 1)]["start"]
    return lines, shots, ev, lines[-1]["end"] + TAIL

SOURCES = "Norscia & Palagi, PLoS ONE, 2011"

def make_overlay(lines, shots, duration):
    RH.HOOK = HOOK
    base = _height_overlay(lines, shots, duration)
    t_lab = next(t for t, n in shots if n == "study")
    t_clock = next(t for t, n in shots if n == "think")
    def overlay(c, t, F):
        base(c, t, F)
        if t_lab <= t < t_clock:                            # honesty note while the facts are on screen
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
PAGE = "Cinematic Sound Design - Paper Foley/Encyclopedia Glossy Page Turn Muted.wav"
BUBBLE = "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Bubbles Short.wav"
KALIMBA = "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Kalimba 3 Up_CB Sounddesign_APPlicable Sounds.wav"

TICK = "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav"

WHOOSH = "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Bubbles Short.wav"

SCRATCH = "InMotionAudio - Scratch Card/OBJMisc_ScratchCard_SurfaceWipe_04_InMotionAudio_ScratchCard.wav"

CLOTH = "InMotionAudio - Foley T-Shirt/FOLYClth_ClothMovement24_InMotionAudio_FoleyT-Shirt.wav"
HEARTB = "Cinematic Sound Design - Cartoon Impacts/Cartoon Pops Random Sequence Reverb.wav"
KNOCK = "Epic Stock Media - Board Game - Sound Set Kit for Tabletop and Digital Games/UIClick_UI Button Analog Vintage Double Click Neutral Dry Press 11_ESM_BG.wav"

def build_audio(lines, shots, ev, duration, out_wav):
    track = np.zeros(int((duration + 1) * SR), np.float32)
    def add(t, x, gain):
        a = int(max(0.0, t) * SR)
        x = x[: len(track) - a]
        track[a:a + len(x)] += x * gain
    add(0.0, common_load(os.path.join(OUT, "narration.wav")), 1.0)
    start = {}
    for t, n in shots:
        start.setdefault(n, t)
    add(0.02, sfx.clip(BUBBLE, 0.0, 0.5), 0.08)                          # the puff on frame one
    for n, d in (("study", 0.4), ("timing", 0.1), ("timing", 0.5)):
        add(start[n] + d + 0.4, sfx.clip(SNAP, 0.0, 0.2, lp=1500), 0.22)
    for k in ("family", "friends", "barely", "last"):
        add(ev[k] - 0.1, sfx.clip(BUBBLE, 0.0, 0.4), 0.07)
        add(ev[k], sfx.clip(POP, 0.0, 0.25), 0.07)
    add(ev["strangers"], sfx.clip(SNAP, 0.0, 0.2, lp=1500), 0.2)
    add(start["think"] + 1.4 + 0.4, sfx.clip(SNAP, 0.0, 0.2, lp=1500), 0.2)
    add(start["final"] + 0.1, sfx.clip(BUBBLE, 0.0, 0.5), 0.08)
    add(start["final"] + 0.4, sfx.clip(KALIMBA, 0.0, 1.2), 0.06)
    save_wav(track, out_wav, duration)

# ------------------------------------------------------------------ main

def main(out_mp4=None, out_wav=None, preview_times=None):
    common.FPS = FPS
    lines, shots, ev, duration = timeline()
    if out_mp4 is None and preview_times is None:
        for t, n in shots:
            print(f"{t:6.2f} {n}")
        print(f"duration {duration:.2f} s")
        return
    os.makedirs(FRAMES, exist_ok=True)
    n = int(round(duration * FPS))
    frames = sorted({min(n - 1, int(round(x * FPS))) for x in preview_times}) if preview_times else list(range(n))
    tj = os.path.join(OUT, "timing.json")
    json.dump({"fps": FPS, "duration": duration, "shots": shots, "events": ev}, open(tj, "w"))
    t0 = time.time()
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "yawn_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, ev, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots, duration), out_mp4, out_wav, "yawn" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "times":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
