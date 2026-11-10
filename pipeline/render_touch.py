"""'Breaking the touch barrier is quantum tunneling': a deadpan voxel explainer for this week's "when they break the
touch barrier first" trend (ops/episodes/2026-11-10-touch-tunnel.md). She touches first, he collapses. Voxel kit
(touch_scene.py, a new after-hours school hallway with a glowing barrier between them), calm Chatterbox read.

python render_touch.py narrate             voice the script (cached in out/touch/voice), print the event times
python render_touch.py preview 1.0,12.5    render and composite stills into preview/
python render_touch.py out.mp4 out.wav     full render (Blender frames are cached in out/touch/frames)

Facts: tunneling lets a particle cross a barrier it lacks the energy to climb, and the odds fall exponentially with
the barrier's width; in a scanning tunneling microscope the current drops about tenfold for every 0.1 nm of extra gap
(https://arxiv.org/pdf/1404.0961, https://www.liverpool.ac.uk/~sdb/ALTAIR/Images/STM.pdf). The Sun's protons fuse
only by tunneling through the barrier of their own repulsion (https://www.astro.princeton.edu/~gk/A403/fusion.pdf).
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
OUT = os.path.join(ROOT, "out", "touch")
FRAMES = os.path.join(OUT, "frames")
SCRIPT = [
    "Breaking the *touch barrier* first? That is *quantum tunneling.*",
    "Between you two sits a barrier. Neither of you has the *energy* to get over it.",
    "Classically, that means his hands stay in his *pockets.* Forever.",
    "But quantum particles don't climb. They go straight *through* walls they can't clear.",
    "The catch: each extra tenth of a nanometer cuts the odds about *ten times.*",
    "So she closes the gap. And she *tunnels.*",
    "He was not built for this. Total *collapse.*",
    "The Sun tunnels all day. He did it once and has to *lie down.*",
    "Send this to whoever breaks the barrier first.",
]
KEYS = "ABCDEFGHI"

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
    from voice_fix import fix                     # even the cadence (qa_voice.py must PASS on narration_fixed)
    fixed = os.path.join(OUT, "narration_fixed.json")
    lines = json.load(open(fixed)) if os.path.exists(fixed) else fix(OUT)
    sents = to_sents(lines)
    speech_end = lines[-1]["end"]
    w = lambda si, sub, n=0: wn(sents, si, sub, n)
    E = {k: sents[i]["t0"] for i, k in enumerate(KEYS)}
    E.update({"barrier": w(0, "barrier"), "quantum": w(0, "quantum"), "energy": w(1, "energy"),
              "pockets": w(2, "pockets"), "forever": w(2, "Forever"), "through": w(3, "through"),
              "catch": w(4, "catch"), "ten": w(4, "ten", 1), "closes": w(5, "closes"), "tunnels": w(5, "tunnels"),
              "built": w(6, "built"), "collapse": w(6, "collapse"), "sun": w(7, "Sun"), "lie": w(7, "lie"),
              "send": w(8, "Send"), "speech_end": speech_end})
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
    "deny": "Cinematic Sound Design - System & UI Feedback Elements/Interface Deny Low Fat Dark.wav",
    "denymuted": "Cinematic Sound Design - UI Interaction Elements/Deny Muted.wav",
    "bassdown": "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Transition Bass Down.wav",
    "kalimba": "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Kalimba 3 Up_CB Sounddesign_APPlicable Sounds.wav",
}

def build_audio(E, duration, path):
    import sfx
    n = int(duration * SR)
    tr = new_track(duration)
    voice = common_load(os.path.join(OUT, "narration_fixed.wav"))[:n]
    tr[:len(voice)] += voice                  # no ambience bed: no hum, buzz or drone (Austin, Oct 27)
    hit = lambda t0, key, gain, **kw: add(tr, t0, sfx.clip(F[key], **kw), gain)
    hit(0.0, "perc", 0.18)
    hit(E["quantum"], "snap", 0.14)
    hit(E["energy"], "deny", 0.14, rate=1.1)
    hit(E["pockets"], "denymuted", 0.2)
    hit(E["through"] - 0.15, "woosh", 0.12)
    for k in range(3):
        hit(E["ten"] + 0.12 * k, "pop", 0.13, rate=1.0 - 0.1 * k)
    hit(E["tunnels"] - 0.05, "magic", 0.2)    # the big moment: the loudest sound, after a breath of silence
    hit(E["tunnels"], "powerup", 0.22)
    hit(E["collapse"] + 0.25, "bassdown", 0.22)
    hit(E["lie"], "kalimba", 0.12)
    hit(E["send"], "perc", 0.16, rate=0.9)
    save_wav(tr, path, duration)

# ------------------------------------------------------------------ overlay

CYAN = skia.Color(95, 227, 255)
PINK = skia.Color(255, 61, 139)
GOLD = skia.Color(255, 205, 60)

def smooth01(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

def draw_hook(c, a):
    if a <= 0:
        return
    y = 300
    for s, k in (("The touch barrier", False), ("is quantum tunneling", True)):
        f = font("Bricolage-800", 84)
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
    draw_hook(c, K.fade(t, -1, E["quantum"] + 0.7, 0.2))
    if t >= E["quantum"] + 0.5:
        tap.draw_captions(c, t, sents, cm)
    c.restore()
    lab = font("JetBrainsMono-700", 30)
    pill(c, "ENERGY NEEDED: TOO MUCH", W / 2, 1460, K.fade(t, E["energy"] - 0.1, E["C"] - 0.1, 0.2), CYAN)
    pill(c, "CLASSICAL ODDS OF TOUCH: 0", W / 2, 1460, K.fade(t, E["pockets"] - 0.1, E["D"] - 0.1, 0.2), INK)
    pill(c, "+0.1 nm GAP = ~10x LESS LIKELY", W / 2, 1460, K.fade(t, E["ten"] - 0.2, E["F"] - 0.1, 0.2), GOLD, size=32)
    pill(c, "BARRIER: TUNNELED", W / 2, 1460, K.fade(t, E["tunnels"], E["G"] - 0.1, 0.15), PINK)
    pill(c, "HIM: COLLAPSED", W / 2, 1460, K.fade(t, E["collapse"] + 0.2, E["H"] - 0.1, 0.2), INK)
    pill(c, "THE SUN: DOES THIS 24/7", W / 2, 1460, K.fade(t, E["sun"] - 0.1, E["lie"] + 0.2, 0.2), GOLD)
    for name, text, t0, t1, dx, dy, col in (("wall", "THE BARRIER", E["B"] + 0.1, E["C"] - 0.1, 170, -160, CYAN),
                                            ("him", "HIM", E["C"] + 0.1, E["D"] - 0.1, 200, 60, INK),
                                            ("her", "HER", E["closes"] - 0.1, E["tunnels"] - 0.3, -150, -140, INK)):
        a = K.fade(t, t0, t1, 0.2)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, col, lab)
    u = t - E["tunnels"]
    if 0 <= u < 0.35:
        c.drawRect(skia.Rect(0, 0, W, H), paint(skia.Color(255, 120, 180), 0.35 * (1 - u / 0.35)))
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
    K.run_blender("touch_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0 or x[2] > E["quantum"] + 0.4]
    if not preview_times:
        build_audio(E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "touch" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "narrate":
        main()
    elif sys.argv[1] == "times":
        main()
    elif sys.argv[1] == "preview":
        main(preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
