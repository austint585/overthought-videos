"""Episode: The Christmas Music Friend (ops/episodes/2026-11-06-christmas-music-friend.md). A seasonal tag-a-friend joke:
your friend has played Christmas music since Nov 1, the jack-o'-lantern is still out, the turkey was not consulted, and the
back-to-back math (19,359 plays to Christmas). Pastel toy kit in daylight with toy peg people (xmas_scene.py). Calm Chatterbox read.

python render_xmas.py narrate                voice the script (cached in out/xmas/voice), print the timing
python render_xmas.py preview 1.0,9.5        stills into preview/xmas_*.png
python render_xmas.py out.mp4 out.wav        full render (Blender frames cached in out/xmas/frames)
"""
import json, os, subprocess, sys, time
import numpy as np
import common
from common import *
import kit3d as K
import sfx
from narrate_cb import narrate
from render_led import common_load
import render_late as RL

FPS = 30
OUT = os.path.join(ROOT, "out", "xmas")
FRAMES = os.path.join(OUT, "frames")
TAIL = 0.8

SCRIPT = [
    ("Your friend has been playing *Christmas music* since November 1st{first}.", [("living", 0)], {"notes": 0}),
    ("The jack-o'-lantern is still *on the table.*", [("pumpkin", 0)], {"hat": 4}),
    ("At midnight, Mariah Carey posted her yearly video: *It's time.*", [("phone", 0)], {"time": 8}),
    ("By the end of that day, her song had over 700,000{seven hundred thousand} *plays* on Spotify.", [("counter", 0)],
     {"count0": 3}),
    ("Your friend was a *lot of them.*", [("replay", 0)], {"press": 1}),
    ("Thanksgiving is November 26th{twenty-sixth}. Nobody asked the *turkey.*", [("turkey", 0)], {"bauble": 1, "turn": 4}),
    ("From November 1st{first} to Christmas is 54{fifty-four} *days.*", [("calendar", 0)], {"days": 5}),
    ("The song is 4{four} minutes long. Back to back, that's over 19,000{nineteen thousand} *plays.*", [("ears", 0), ("total", 5)],
     {"pillow": 2, "count1": 5}),
    ("Tag your friend. They're almost at play *1,800{eighteen hundred}.*", [("final", 0)], {"count2": 3}),
]
HOOK = ["SINCE NOV 1ST:", "CHRISTMAS MUSIC"]
NOTES = {"final": "A 4:01 song, back to back from Nov 1 to Nov 6"}

def timeline():
    if os.environ.get("OT_VOICE") == "kokoro":            # Chatterbox needs ~4 GB free commit; Kokoro is the low-memory fallback
        from narrate_kk import narrate as kk
        lines = kk([l for l, _, _ in SCRIPT], OUT, gap=0.28)
    else:
        lines = narrate([l for l, _, _ in SCRIPT], OUT, exaggeration=0.5, cfg=0.4, gap=0.28)
    shots, ev = [], {}
    for (line, plan, evs), L in zip(SCRIPT, lines):
        for name, wi in plan:
            t = L["words"][wi]["start"] - 0.08 if wi else L["start"] - 0.08
            shots.append([0.0 if not shots else round(t, 3), name])
        for k, wi in evs.items():
            ev[k] = L["words"][wi]["start"]
    return lines, shots, ev, lines[-1]["end"] + TAIL

def make_overlay(lines, shots):
    RL.HOOK, RL.NOTES = HOOK, NOTES
    return RL.make_overlay(lines, shots)

# ------------------------------------------------------------------ sound

WOOSH = "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav"
SNAP = "Cinematic Sound Design - Interface & Infographics/Interface Accept Glassy Snap.wav"
POP = "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav"
HIT = "Cinematic Sound Design - Cartoon Impacts/Cartoon Pops Random Sequence Reverb.wav"
BELLS = "344 Audio - Christmas Vol. 1/MAGMisc_Magic Christmas Bells 2_344 Audio_Christmas.wav"
MUSIC = "Sonic Bat - Music Boxes/SBmb_Music Box A 013.wav"
CLICK = "Epic Stock Media - Board Game - Sound Set Kit for Tabletop and Digital Games/UIClick_UI Button Analog Vintage Double Click Neutral Dry Press 11_ESM_BG.wav"
CLOTH = "InMotionAudio - Foley T-Shirt/FOLYClth_ClothMovement24_InMotionAudio_FoleyT-Shirt.wav"
RING = "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Xylophone Ringtone 2_CB Sounddesign_APPlicable Sounds.wav"

def build_audio(lines, shots, ev, duration, out_wav):
    track = np.zeros(int((duration + 1) * SR), np.float32)
    def add(t, x, gain):
        a = int(max(0.0, t) * SR)
        x = x[: len(track) - a]
        track[a:a + len(x)] += x * gain
    add(0.0, common_load(os.path.join(OUT, "narration.wav")), 1.0)
    # the friend's speaker: a music box tune, quiet under the voice, from frame one to the end
    mb = sfx.clip(MUSIC, 0.0, None, fade=0.2)
    t = 0.0
    while t < duration:
        add(t, mb, 0.035)
        t += len(mb) / SR - 0.2
    add(0.0, sfx.clip(BELLS, 0.0, 1.2), 0.08)
    for t, _ in shots[1:]:
        add(max(0.0, t - 0.12), sfx.clip(WOOSH, 0.0, 0.5, lp=6000), 0.06)
    add(ev["hat"], sfx.clip(POP, 0.0, 0.3), 0.14)
    add(ev["time"], sfx.clip(RING, 0.0, 0.7), 0.1)
    for k in ("count0", "count1", "count2", "days"):
        add(ev[k], sfx.clip(SNAP, 0.0, 0.3), 0.13)
    for j in range(4):
        add(ev["press"] + j * 0.32, sfx.clip(CLICK, 0.0, 0.2), 0.16)
    add(ev["bauble"], sfx.clip(BELLS, 0.0, 0.6, hp=2000), 0.08)
    add(ev["turn"], sfx.clip(HIT, 0.0, 0.35), 0.12)
    add(ev["pillow"], sfx.clip(CLOTH, 0.0, 0.6), 0.2)
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
    subprocess.run([K.BLENDER, "-b", "--factory-startup", "-noaudio", "-P", os.path.join(ROOT, "xmas_scene.py"),
                    "--", tj, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all"], check=True)
    print(f"blender: {time.time() - t0:.0f} s for {len(frames)} frames")
    if not preview_times:
        build_audio(lines, shots, ev, duration, out_wav)
    K.composite(FRAMES, frames, FPS, make_overlay(lines, shots), out_mp4, out_wav, "xmas" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    elif sys.argv[1] == "times":
        main()
    else:
        main(sys.argv[1], sys.argv[2])
