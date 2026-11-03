"""Episode: Five minutes away (ops/episodes/2026-11-03-five-minutes-away.md). The friend who is always five minutes away, explained
with the planning fallacy and the 77-second minute, in the pastel toy kit (late_scene.py): bevelled pastel props, bright daylight,
numbers on dark signs in the scene. Calm Chatterbox read, dark caption pills with one boxed word (the water episode's captions).

python render_late.py narrate                voice the script (cached in out/late/voice), print the timing
python render_late.py preview 1.0,9.5        stills into preview/late_*.png
python render_late.py out.mp4 out.wav        full render (Blender frames cached in out/late/frames)
"""
import json, os, subprocess, sys, time
import numpy as np
import skia
import common
from common import *
import kit3d as K
import sfx
from narrate_cb import narrate
from render_led import chunks, common_load
from render_water import captions

FPS = 30
OUT = os.path.join(ROOT, "out", "late")
FRAMES = os.path.join(OUT, "frames")
TAIL = 1.0

# (line, [(shot, word index the shot starts on), ...], {event: word index}); *word* is boxed in the caption
SCRIPT = [
    ("Your friend who's always *five minutes away* is not lying. He *believes* it.", [("phone", 0), ("shower", 7)], {}),
    ("Psychologists call it the *planning fallacy.*", [("label", 0)], {}),
    ("Students were asked how long their thesis would take. They guessed *thirty four days.* It took *fifty six.*",
     [("desk", 0), ("desk~2", 9)], {"guess": 11, "took": 15}),
    ("Even their *worst case* guess was a week short.", [("worst", 0)], {}),
    ("And some people's minutes are just *longer.*", [("clock", 0)], {}),
    ("Asked to feel when one minute had passed, laid back Type B people called it at *seventy seven seconds.*",
     [("clock~2", 0)], {"count0": 0, "count1": 15}),
    ("So his five minutes is about *six and a half* of yours.", [("timer", 0)], {"timer": 6}),
    ("Add the planning fallacy, and plan for *twenty.*", [("plan", 0)], {"twenty": 7}),
    ("Send him this. He'll see it in *five minutes.*", [("phone2", 0)], {}),
]
HOOK = ["He is not", "5 minutes away"]
NOTES = {"desk": "Buehler, Griffin & Ross 1994: 37 students' honors theses",
         "desk~2": "Buehler, Griffin & Ross 1994: 37 students' honors theses",
         "worst": "Average worst case guess 49 days, actual 56",
         "clock~2": "Conte et al., San Diego State: Type B said 77 s, Type A 58 s",
         "timer": "Our math: 5 min x 77/60",
         "plan": "A joke, not a study"}
KEY = skia.ColorSetARGB(255, 255, 106, 43)

def timeline():
    lines = narrate([l for l, _, _ in SCRIPT], OUT, exaggeration=0.5, cfg=0.4, gap=0.22)
    shots, ev = [], {}
    for (line, plan, evs), L in zip(SCRIPT, lines):
        for name, wi in plan:
            t = L["words"][wi]["start"] - 0.08 if wi else L["start"] - 0.08
            shots.append([0.0 if not shots else round(t, 3), name])
        for k, wi in evs.items():
            ev[k] = L["words"][wi]["start"]
    ev["count1"] = lines[5]["words"][-1]["end"]
    return lines, shots, ev, lines[-1]["end"] + TAIL

def shot_name(shots, t):
    return [n for s, n in shots if t >= s - 1e-6][-1]

def make_overlay(lines, shots):
    ch = chunks(lines)
    hook_end = lines[0]["end"] + 0.1
    def overlay(c, t, F):
        if t < hook_end:                                   # the big title, readable on frame 1
            f = font("Inter-700", 104)
            y = 1520
            for i, s in enumerate(HOOK):
                wd = f.measureText(s)
                x = (W - wd) / 2
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 22, y + i * 120 - 92, x + wd + 22, y + i * 120 + 26), 20, 20),
                            skia.Paint(Color=KEY if i == 1 else skia.ColorSetARGB(225, 28, 33, 41), AntiAlias=True))
                c.drawString(s, x + 4, y + i * 120 + 5, f, skia.Paint(Color=skia.ColorSetARGB(120, 0, 0, 0), AntiAlias=True))
                c.drawString(s, x, y + i * 120, f, skia.Paint(Color=skia.ColorWHITE, AntiAlias=True))
        name = shot_name(shots, t)
        if name in NOTES:
            fn = font("Inter-700", 28)
            s, y = NOTES[name], 1532
            w = fn.measureText(s)
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect((W - w) / 2 - 18, y - 32, (W + w) / 2 + 18, y + 12), 14, 14),
                        skia.Paint(Color=skia.ColorSetARGB(170, 255, 255, 255), AntiAlias=True))
            text_center(c, s, W / 2, y, fn, paint(skia.ColorSetARGB(255, 40, 62, 58), 0.95))
        captions(c, t, ch)
    return overlay

# ------------------------------------------------------------------ sound

WOOSH = "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav"
SNAP = "Cinematic Sound Design - Interface & Infographics/Interface Accept Glassy Snap.wav"
POP = "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav"
TICK = "344 Audio - Antique Clocks/CLOCKTick_Crooked Antique Clock_344 Audio_Antique Clocks.wav"
PAGE = "Cinematic Sound Design - Paper Foley/Encyclopedia Glossy Page Turn Muted.wav"
SHOWER = "InMotionAudio - Back Garden Storm/STORM_StormAmbience11_InMotionAudio_BackGardenStorm.wav"   # rain on the patio, high-passed into a shower hiss
HIT = "Cinematic Sound Design - Cartoon Impacts/Cartoon Pops Random Sequence Reverb.wav"

def build_audio(lines, shots, ev, duration, out_wav):
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
    for t, _ in shots[1:]:
        add(max(0.0, t - 0.12), sfx.clip(WOOSH, 0.0, 0.5, lp=6000), 0.07)
    add(0.3, sfx.clip(POP, 0.0, 0.3), 0.22)                             # the message bubble
    add(start["shower"], sfx.clip(SHOWER, 2.0, end["shower"] - start["shower"], hp=900, fade=0.2), 0.1)
    add(start["label"] + 0.3, sfx.clip(HIT, 0.0, 0.35), 0.16)
    for k in range(6):                                                  # pages tearing off the calendar
        add(ev["took"] - 0.1 + k * 0.18, sfx.clip(PAGE, 0.0, 0.25, hp=1200), 0.12)
    add(ev["guess"], sfx.clip(SNAP, 0.0, 0.3), 0.12)
    t = start["clock"]
    while t < end["clock~2"] - 0.1:
        add(t, sfx.clip(TICK, 0.2, 0.14), 0.22)
        t += 1.0 if t < ev["count0"] else 0.5
    add(ev["count1"] + 0.05, sfx.clip(SNAP, 0.0, 0.3), 0.14)
    add(ev["timer"], sfx.clip(SNAP, 0.0, 0.3), 0.12)
    add(ev["twenty"], sfx.clip(HIT, 0.0, 0.35), 0.16)
    add(start["phone2"] + 0.3, sfx.clip(POP, 0.0, 0.3), 0.22)
    save_wav(track, out_wav, duration)

# ------------------------------------------------------------------ main

def main(out_mp4=None, out_wav=None, preview_times=None):
    common.FPS = FPS
    lines, shots, ev, duration = timeline()
    if out_mp4 is None and preview_times is None:
        for t, n in shots:
            print(f"{t:6.2f} {n}")
        print({k: round(v, 2) for k, v in ev.items()})
        print(f"duration {duration:.2f} s")
        return
    os.makedirs(FRAMES, exist_ok=True)
    n = int(round(duration * FPS))
    frames = sorted({min(n - 1, int(round(x * FPS))) for x in preview_times}) if preview_times else list(range(n))
    tj = os.path.join(OUT, "timing.json")
    json.dump({"fps": FPS, "duration": duration, "shots": shots, "events": ev,
               "font": os.path.join(ROOT, "vendor", "fonts", "Inter-700.ttf")}, open(tj, "w"))
    t0 = time.time()
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "late_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, ev, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots), out_mp4, out_wav, "late" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
