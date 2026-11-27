"""A cutscene episode with the low-poly cast in the PS2 look (Nov 26): same script, voices, cameras, overlay and sound
as render_cutscene.py, but the people are lowpoly_cast.py's (rendered through lowpoly_scene.py at 270 x 480), then
dithered and scaled up 4x (ps2look.post) before the overlay goes on.

python render_ps2.py <episode> preview t1,t2,...     stills into preview/<episode>_ps2_*.png
python render_ps2.py <episode> clip t0 t1            frames for that stretch, encoded with its sound to out/<ep>_ps2/
python render_ps2.py <episode>                       the whole episode to out/<ep>_ps2/<ep>_ps2.mp4
python render_ps2.py <episode> encode                redo overlay, sound and MP4 from the frames on disk
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit3d, ps2look
import render_cutscene as rc
from common import save_wav

AUTO = ("sit_hand", "sit_lean", "sit_point")       # lines with nothing more specific rotate through these
# where each episode is set (lowpoly_sets.SETS); missing = the patio table. Austin, Nov 27: "change up your
# scenery", so a new chad episode gets a place that fits its topic. PS2_SET=<name> (or "table") overrides.
SETS = {"chad_black_friday": "tv_aisle", "chad_rudolph": "living_room"}


def pose_events(ep, duration):
    """A new pose on every line (the sixth low-poly rule): {name: [[t, pose], ...]}. A beat can name one ("pose");
    otherwise a question opens the palms, the punchline leans back, a phone check looks down at the phone, the chad
    leans back (deadpan), and laughs and shocks react. Each pose holds through the next beat, then the person settles
    back to the base pose from the cast ("arms": table or crossed)."""
    base = {c["name"]: "sit_crossed" if c.get("arms") == "crossed" else "sit_table" for c in ep["cast"]}
    ev = {n: [[0.0, base[n]]] for n in base}
    beats = ep["beats"]
    k = 0

    def put(n, t0, pose, until):
        ev[n] = [e for e in ev[n] if e[0] < t0]               # a newer pose cuts an older one short
        ev[n].append([t0, pose])
        ev[n].append([until, base[n]])

    for i, b in enumerate(beats):
        t0 = b["_t0"]
        t_after = beats[i + 2]["_t0"] if i + 2 < len(beats) else duration
        looks = b.get("look", {})
        if "say" in b:
            who = b["who"]
            say = rc.strip_notes(b["say"])
            if b.get("pose"):
                pz = b["pose"]
            elif looks.get(who) == "down":
                pz = "sit_phone"
            elif b.get("punch") or who == "chad":
                pz = "sit_back"
            elif say.rstrip().endswith("?"):
                pz = "sit_palms"
            else:
                pz, k = AUTO[k % len(AUTO)], k + 1
            t1 = t0 + len(b["_audio"]) / rc.SR
            until = max(t1 + 0.4, t_after)
            if pz == "sit_phone":                              # hold the phone through the search insert
                j = next((m for m in range(i + 1, len(beats)) if beats[m].get("drops")), i + 2)
                until = beats[j]["_t0"] if j < len(beats) else duration
            put(who, t0 - 0.05, pz, until)
        for n, face in b.get("faces", {}).items():
            if n in base and b.get("who") != n and face in ("laugh", "shock"):
                t_next = beats[i + 1]["_t0"] if i + 1 < len(beats) else duration
                put(n, t0 + 0.1, "sit_laugh" if face == "laugh" else "sit_back", t_next + 0.5)
    for n in ev:
        ev[n].sort()
    return ev


def blender(tj, low, which, NF, tries=6):
    """Same resume-after-crash loop as render_cutscene.blender_frames, on lowpoly_scene.py."""
    want = list(range(1, NF + 1)) if which == "all" else list(which)
    for attempt in range(tries):
        for f in want:
            p = os.path.join(low, f"f_{f:05d}.png")
            if os.path.exists(p) and os.path.getsize(p) < 200:
                os.remove(p)
        todo = [f for f in want if not os.path.exists(os.path.join(low, f"f_{f:05d}.png"))]
        if not todo:
            return
        arg = "all" if which == "all" else ",".join(map(str, todo))
        r = subprocess.run([kit3d.BLENDER, "-b", "--factory-startup", "-noaudio", "-P",
                            os.path.join(HERE, "lowpoly_scene.py"), "--", tj, low, arg])
        if r.returncode != 0:
            print(f"Blender exited with {r.returncode} (attempt {attempt + 1}); resuming")
    missing = [f for f in want if not os.path.exists(os.path.join(low, f"f_{f:05d}.png"))]
    if missing:
        raise RuntimeError(f"frames still missing: {missing[:10]}")


def main():
    name = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "full"
    ep = rc.EPISODES[name]
    voice_dir = os.path.join(HERE, "out", name)              # reuse the episode's cached voices
    out_dir = os.path.join(HERE, "out", f"{name}_ps2")
    low, big = os.path.join(out_dir, "low"), os.path.join(out_dir, "frames")
    os.makedirs(low, exist_ok=True)
    rc.voice_lines(ep, voice_dir)
    duration = rc.timeline(ep)
    T = rc.timing_json(ep, duration)
    T["poses"] = pose_events(ep, duration)
    st = os.environ.get("PS2_SET", SETS.get(name))
    if st and st != "table":
        T["set"] = st
    tj = os.path.join(out_dir, "timing.json")
    json.dump(T, open(tj, "w"))
    NF = int(round(duration * rc.FPS))
    if mode == "preview":
        fl = [min(NF - 1, int(round(float(t) * rc.FPS))) for t in sys.argv[3].split(",")]
    elif mode == "clip":
        fl = list(range(int(float(sys.argv[3]) * rc.FPS), min(NF, int(float(sys.argv[4]) * rc.FPS))))
    else:
        fl = list(range(NF))
    if mode == "preview":                                    # stills are always rendered fresh
        for F in fl:
            p = os.path.join(low, f"f_{F + 1:05d}.png")
            if os.path.exists(p):
                os.remove(p)
    elif mode == "full":                                     # a full run starts clean
        for f in os.listdir(low):
            if f.startswith("f_") and f.endswith(".png"):
                os.remove(os.path.join(low, f))
    if mode != "encode":
        blender(tj, low, [F + 1 for F in fl] if mode != "full" else "all", NF)
    ps2look.post_dir(low, big, fl)
    A = json.load(open(os.path.join(low, "anchors.json")))
    over = rc.make_overlay(ep, T, A)
    if mode == "preview":
        kit3d.composite(big, fl, rc.FPS, over, preview_prefix=f"{name}_ps2")
        print("previews in preview/")
        return
    wav = os.path.join(out_dir, f"{name}_ps2.wav")
    save_wav(rc.mix(ep, duration), wav, duration)
    if mode == "clip":                                       # cut the sound to the clip
        import soundfile as sf
        a, sr = sf.read(wav)
        a = a[int(fl[0] / rc.FPS * sr):int((fl[-1] + 1) / rc.FPS * sr)]
        wav = os.path.join(out_dir, f"{name}_ps2_clip.wav")
        sf.write(wav, a, sr)
    mp4 = os.path.join(out_dir, f"{name}_ps2{'_clip' if mode == 'clip' else ''}.mp4")
    kit3d.composite(big, fl, rc.FPS, over, out_mp4=mp4, out_wav=wav)
    print(mp4)


if __name__ == "__main__":
    main()
