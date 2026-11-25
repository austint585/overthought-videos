"""Episode: The Turkey Is Still A Rock (ops/episodes/2026-11-25-turkey-rock.md). The night before Thanksgiving, a frozen
20 lb bird, the USDA thaw rules and the 20 water changes they add up to. Pastel toy kit, directed (turkeyrock_scene.py with
direct.py): an evening kitchen lit by two pendants and a dusk window. Fish Drama 3 narration, evened by voice_fix.

python render_turkeyrock.py times                voice the script (cached in out/turkeyrock), print the timing and PRONOUNCE lines
python render_turkeyrock.py preview 1.0,9.5      stills into preview/turkeyrock_*.png
python render_turkeyrock.py out.mp4 out.wav      full render (Blender frames cached in out/turkeyrock/frames)
"""
import json, os, sys
import numpy as np
import skia
import common
from common import *
import kit3d as K
import sfx
from narrate_cb import narrate
from render_led import common_load
from render_water import captions, chunks, KEY

FPS = 30
OUT = os.path.join(ROOT, "out", "turkeyrock")
FRAMES = os.path.join(OUT, "frames")
TAIL = 1.0

SCRIPT = [
    "Thanksgiving is *tomorrow.* The turkey is still a *rock.*",
    "The fridge needs about a day for every *four to five pounds.*",
    "You don't have *four days.*",
    "So it goes in *cold water.*",
    "[calm, slow, deliberate] It takes about thirty minutes a pound.",
    "A *20*{twenty} pound bird takes about *ten hours.*",
    "[calm, slow, deliberate, deadpan] And you change the water every *thirty minutes.*",
    "That's *20*{twenty} water changes.",
    "Your friend is on number *one.*",
    "Send this to whoever's hosting tomorrow.",
]
LETTERS = "ABCDEFGHIJ"
HOOK = ["THANKSGIVING: TOMORROW", "TURKEY: STILL FROZEN"]
NOTES = {"fridge": "USDA: about 1 day per 4 to 5 lb in the fridge",
         "days": "20 lb / 4 to 5 lb a day = 4 to 5 days",
         "sink": "Cold tap water, bird in a sealed bag",
         "bag": "USDA: about 30 min per lb in cold water",
         "hours": "20 lb x 30 min = 10 hours",
         "change": "USDA: change the water every 30 minutes",
         "count": "Our math: 10 h / 30 min = 20"}

def word_at(L, sub, nth=0):
    hits = [w for w in L["words"] if sub.lower() in w["w"].lower()]
    return hits[min(nth, len(hits) - 1)]["start"] if hits else L["start"]

def setup():
    narrate(SCRIPT, OUT)
    from voice_fix import fixed
    lines = fixed(OUT, max_stretch=[0.12] * 6 + [0.2] + [0.12] * 3)   # line 7 reads fast every take
    E = {k: L["start"] for k, L in zip(LETTERS, lines)}
    E.update({"rock": word_at(lines[0], "rock"), "four": word_at(lines[2], "four"), "cold": word_at(lines[3], "cold"),
              "ten": word_at(lines[5], "ten"), "thirty": word_at(lines[6], "thirty"), "twenty": word_at(lines[7], "20")
              if any("20" in w["w"] for w in lines[7]["words"]) else word_at(lines[7], "twenty"),
              "one": word_at(lines[8], "one"), "speech_end": lines[-1]["end"]})
    duration = lines[-1]["end"] + TAIL
    return lines, E, duration

SHOT_ORDER = [("hook", "A"), ("rock", "rock"), ("fridge", "B"), ("days", "C"), ("sink", "D"), ("bag", "E"), ("hours", "F"),
              ("change", "G"), ("count", "H"), ("one", "I"), ("loop", "J")]

def shot_name(E, t):
    cur = "hook"
    for name, ev in SHOT_ORDER:
        if t >= E[ev] - 0.06:
            cur = name
    return cur

def make_overlay(lines, E):
    ch = chunks(lines)
    hook_end = E["B"] - 0.1
    dark = skia.ColorSetARGB(225, 28, 33, 41)
    def overlay(c, t, F):
        if t < hook_end:                                   # the premise, readable on frame 1 with the sound off
            f = font("Inter-700", 58)
            for i, s in enumerate(HOOK):
                wd = f.measureText(s)
                x, y = (W - wd) / 2, 470 + i * 84
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 20, y - 56, x + wd + 20, y + 18), 16, 16),
                            skia.Paint(Color=KEY if i == 1 else dark, AntiAlias=True))
                c.drawString(s, x, y, f, skia.Paint(Color=skia.ColorWHITE, AntiAlias=True))
        name = shot_name(E, t)
        if name in NOTES:
            fn = font("Inter-700", 28)
            s, y = NOTES[name], 1300
            w = fn.measureText(s)
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect((W - w) / 2 - 18, y - 32, (W + w) / 2 + 18, y + 12), 14, 14),
                        skia.Paint(Color=skia.ColorSetARGB(170, 255, 255, 255), AntiAlias=True))
            text_center(c, s, W / 2, y, fn, paint(skia.ColorSetARGB(255, 40, 62, 58), 0.95))
        u = t - E["twenty"]
        if 0 <= u < 0.35:                                  # the big moment: an orange flash on "20"
            c.drawRect(skia.Rect(0, 0, W, H), paint(KEY, 0.28 * (1 - u / 0.35)))
        captions(c, t, ch)
        if t > E["speech_end"] + 0.1:
            a = min(1.0, (t - E["speech_end"] - 0.1) / 0.4)
            text_center(c, "@overthought.daily", W / 2, 1300, font("JetBrainsMono-500", 32), paint(MUTED, a))
    return overlay

# ------------------------------------------------------------------ sound (Sonniss GDC 2026; no hum or drone beds)

S = {
    "clank": "Epic Stock Media - HD Game Materials/METLImpt_Metal Old File Impact Tap Against Tire Iron Metallic Hit 01_ESM_HDGM.wav",
    "ice": "Alexander Kopeikin - 100 kHz Designed Ice/ice, crack, ice block snapping-001.wav",
    "latch": "Epic Stock Media - HD Lock And Mechanism Sound Design Kit/MECHLtch_Click Deep Mechanism Latch Button Nearfield Thunk 02_ESM_HDLM.wav",
    "splash": "Epic Stock Media - Elemental Mutation Whooshes and Impacts/WATRImpt_Impact Water Deep Submerge Bubble Drown Ship Hit 05_ESM_EMWI.wav",
    "ding": "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Xylophone Ringtone 2_CB Sounddesign_APPlicable Sounds.wav",
    "snap": "Cinematic Sound Design - Interface & Infographics/Interface Accept Glassy Snap.wav",
    "pop": "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav",
    "hit": "Cinematic Sound Design - Cartoon Impacts/Cartoon Pops Random Sequence Reverb.wav",
    "kalimba": "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Kalimba 3 Up_CB Sounddesign_APPlicable Sounds.wav",
}
KNOCKS = [0.12, 0.42]          # seconds after the hook and the loop cut in (turkeyrock_scene.py uses the same)

def build_audio(E, duration, out_wav):
    tr = new_track(duration + 1)
    voice = common_load(os.path.join(OUT, "narration_fixed.wav"))
    tr[:len(voice)] += voice[:len(tr)]
    hit = lambda t, k, g, **kw: add(tr, max(0.0, t), sfx.clip(S[k], **kw), g)
    for t0 in (0.0, E["J"] - 0.06):
        for k in KNOCKS:
            hit(t0 + k, "clank", 0.16, dur=0.35, lp=5000)
    hit(E["rock"], "ice", 0.08, dur=0.5)
    hit(E["B"] - 0.06, "latch", 0.16, dur=0.4)
    hit(E["four"], "pop", 0.1)
    hit(E["cold"], "splash", 0.14, dur=1.0, lp=4000)
    hit(E["ten"], "snap", 0.1)
    hit(E["thirty"], "ding", 0.09, dur=0.9)
    hit(E["twenty"], "hit", 0.2, dur=0.5)                 # the big moment: the loudest hit
    hit(E["twenty"], "kalimba", 0.14, dur=1.4)
    hit(E["one"], "pop", 0.08, rate=0.8)
    tr = np.tanh(1.0 * tr / (np.abs(tr).max() + 1e-9))   # save_wav peak-normalizes: limit first to reach about -13 LUFS
    save_wav(tr, out_wav, duration)

# ------------------------------------------------------------------ main

def main(out_mp4=None, out_wav=None, preview_times=None):
    common.FPS = FPS
    lines, E, duration = setup()
    if out_mp4 is None and preview_times is None:
        for L in lines:
            print(f"{L['start']:6.2f} {L['end']:6.2f} match {L.get('match')}  {L['text']}")
        print(json.dumps({k: round(v, 2) for k, v in E.items()}))
        print(f"duration {duration:.2f} s")
        return
    os.makedirs(FRAMES, exist_ok=True)
    n = int(round(duration * FPS))
    frames = sorted({min(n - 1, int(round(x * FPS))) for x in preview_times}) if preview_times else list(range(n))
    E["font"] = os.path.join(ROOT, "vendor", "fonts", "Inter-700.ttf")
    E["knocks"] = KNOCKS
    K.run_blender("turkeyrock_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    if not preview_times:
        build_audio(E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, E), out_mp4, out_wav, "turkeyrock" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] in ("narrate", "times"):
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
