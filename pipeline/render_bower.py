"""'Your friend is a bowerbird': a deadpan clay nature short. The satin bowerbird builds a stick hallway, decorates it
only in blue (much of it stolen), wrecks the neighbor's, dances too hard, and gets studied with a robot girlfriend.
Every behavior is real; the friend framing is the joke.

python render_bower.py out.mp4 out.wav     full render (Blender frames are cached in out/bower/frames)
python render_bower.py preview 1.0,12.5    render and composite stills into preview/
python render_bower.py times               narrate and print the event times

Facts and links: ops/episodes/2026-11-02-bowerbird-friend.md
"""
import json, math, os, sys
import skia
from common import *
import render_tap as tap
import kit3d as K
import render_dst as D                       # pill, sound files and remux; also switches captions to clay

tap.LEXICON["bowerbird"] = "bˈaʊɚbɜːɹd"

FPS = 30
TAIL = 1.6
SCRIPT = [
    ("A", "This is the *satin bowerbird.* He's your friend who *deep cleaned* his apartment for one date."),
    ("B", "He builds her a little *hallway* out of sticks. Then he *decorates.* Only in *blue.*"),
    ("C", "Bottle caps. *Straws.* A lot of it is *stolen* from the guy next door."),
    ("D", "If the guy next door's place looks *better,* he goes over and *wrecks it.*"),
    ("E", "She shows up. He *dances.* He *buzzes.* He does *impressions* of other birds."),
    ("F", "Come on too *strong,* and she *leaves.* Scientists tested this with a *robot* girlfriend."),
    ("G", "Most guys get *nobody.* A few guys get *everyone.*"),
    ("H", "And it takes him about *seven years* just to get the *fit.*"),
    ("I", "So he fixes his *straws,* and waits for *next season.*"),
]
EXTRA_GAP = {1: 0.15, 2: 0.2, 3: 0.3, 4: 0.3, 5: 0.45, 6: 0.45, 7: 0.4, 8: 0.5}
OUT = os.path.join(ROOT, "out", "bower")
FRAMES = os.path.join(OUT, "frames")
KEYS = "ABCDEFGHI"

def events(sents, speech_end):
    w = lambda si, sub, n=0: D.wn(sents, si, sub, n)
    E = {k: sents[i]["t0"] for i, k in enumerate(KEYS)}
    E.update({"deep": w(0, "deep"), "decor": w(1, "decorates"), "blue": w(1, "blue"), "straws": w(2, "Straws"),
              "stolen": w(2, "stolen"), "wreck": w(3, "wrecks"), "dance": w(4, "dances"), "buzz": w(4, "buzzes"),
              "imp": w(4, "impressions"), "strong": w(5, "strong"), "leaves": w(5, "leaves"), "robot": w(5, "Scientists"),
              "everyone": w(6, "few"), "fit": w(7, "fit"), "season": w(8, "waits"), "speech_end": speech_end})
    return E

# ------------------------------------------------------------------ sound (recorded effects, see sfx.py)

F = dict(D.F)

def build_audio(sents, E, duration, path):
    import sfx
    n = int(duration * SR)
    tr = new_track(duration)
    tr[:n] += K.voice_track(sents, duration)[:n]
    hit = lambda t0, key, gain, **kw: add(tr, t0, sfx.clip(F[key], **kw), gain)
    hit(0.0, "pop", 0.14, rate=0.8)
    for i in range(7):                                     # sticks going up, one tick each
        hit(E["B"] + 0.15 + i * 0.16, "perc", 0.09, rate=0.7 + 0.05 * (i % 3), dur=0.1, lp=3500)
    for i in range(4):                                     # blue things landing on the court
        hit(E["decor"] + 0.3 + i * 0.22, "pop", 0.10, rate=1.0 + 0.08 * i)
    hit(E["stolen"], "swoosh", 0.09)
    for i in range(5):
        hit(E["wreck"] + i * 0.11, "perc", 0.12, rate=0.6 + 0.07 * i, dur=0.12, lp=2500)
    hit(E["wreck"], "cloth", 0.12, dur=0.5, lp=5000)
    for i in range(6):                                     # the dance: wing flicks
        hit(E["dance"] + i * 0.25, "cloth", 0.08, dur=0.18, lp=6000)
    hit(E["strong"], "woosh", 0.09)
    hit(E["leaves"] + 0.1, "swoosh", 0.10)
    hit(E["robot"] + 0.2, "kalimba", 0.10, rate=0.8)
    hit(E["G"], "deny", 0.10)
    hit(E["everyone"] + 0.2, "kalimba", 0.12, rate=1.2)
    hit(E["fit"], "pop", 0.12, rate=1.2)
    hit(E["season"], "tick", 0.10)
    hit(E["season"] + 0.6, "tick", 0.10)
    save_wav(tr, path, duration)

# ------------------------------------------------------------------ overlay

def draw_hook(c, t, a):
    if a <= 0:
        return
    y = 300
    for s, k in (("Every guy you know", False), ("is this bird", True)):
        ff = font("Bricolage-800", 96)
        wd = ff.measureText(s) + (40 if k else 0)
        x = W / 2 - wd / 2
        if k:
            c.drawRRect(tap.rrect(x, y - 82, x + wd, y + 26, 16), paint(tap.RED, a))
            c.drawString(s, x + 20, y, ff, paint(INK, a))
        else:
            c.drawString(s, x, y, ff, paint(INK, a))
        y += 118

def overlay(c, t, Fr, sents, cm, E, A, speech_end):
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, t, K.fade(t, -1, E["A"] + 0.9, 0.2))
    if t > E["A"] + 0.9:
        tap.draw_captions(c, t, sents, cm)
    c.restore()
    lab = font("JetBrainsMono-700", 30)
    for name, text, t0, t1, dx, dy, colr in (
            ("hero", "SATIN BOWERBIRD (MALE)", E["A"] + 0.9, E["deep"] + 0.8, 60, -150, D.GOLD),
            ("bower", "THE BOWER", E["B"] + 0.3, E["decor"], -80, -170, D.GOLD),
            ("cap", "STOLEN", E["stolen"] + 0.1, E["D"] - 0.1, 40, -170, tap.RED),
            ("hen", "HER", E["E"] + 0.2, E["dance"], -60, -160, D.GOLD),
            ("robot", "ROBOT (REAL, 2002)", E["robot"] + 0.5, E["G"] - 0.1, 50, -160, tap.RED),
            ("champ", "THIS GUY", E["everyone"] + 0.1, E["H"] - 0.1, 50, -170, D.GOLD),
            ("young", "STILL GREEN AT 5", E["H"] + 0.2, E["fit"] - 0.05, -40, -160, D.GOLD)):
        a = K.fade(t, t0, t1, 0.15)
        p = K.anchor(A, name, Fr) if a > 0 else None
        if p:
            if p[1] + dy < 440:            # keep labels clear of the captions in the top third
                dy = 140
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, colr, lab)
    D.pill(c, "ALL REAL. SATIN BOWERBIRD, EASTERN AUSTRALIA.", W / 2, 1282, K.fade(t, E["season"] + 0.3, speech_end + 1.6, 0.15), MUTED, size=25)

# ------------------------------------------------------------------ main

def setup():
    sents, speech_end = K.narrate(SCRIPT, OUT, EXTRA_GAP)
    duration = speech_end + TAIL
    return sents, speech_end, duration, events(sents, speech_end)

def main(out_mp4, out_wav, preview_times=None):
    sents, speech_end, duration, E = setup()
    n_frames = int(round(duration * FPS))
    print(f"duration {duration:.1f}s, {n_frames} frames", flush=True)
    frames = sorted({min(n_frames - 1, int(round(x * FPS))) for x in preview_times}) if preview_times else range(n_frames)
    K.run_blender("bower_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0]
    if not preview_times:
        build_audio(sents, E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, Fr: overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "bower" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "times":
        sents, speech_end, duration, E = setup()
        print(json.dumps({k: round(v, 2) for k, v in E.items()}, indent=1))
        print("duration", round(duration, 2))
    elif sys.argv[1] == "audio":
        sents, speech_end, duration, E = setup()
        build_audio(sents, E, duration, sys.argv[3])
        D.remux(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "preview":
        main(None, None, preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
