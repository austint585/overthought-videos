"""Low-poly cast look tests (Nov 26): lineup, turnaround, expressions and a short talking clip in the PS2 look.

python render_chadlite.py clip     about 4.5 s: two of the chad's cached lines, a pose on each, out/chadlite/
python render_chadlite.py sheet    turnaround, poses and faces (LOWPOLY_WHO=chad|suit|jacket|overalls) in out/chadlite/
python render_chadlite.py lineup   all four side by side, full body and faces, in out/chadlite/
Set OVERTHOUGHT_CPU_PREVIEW=1 to render on the CPU while a GPU render is running.
"""
import json, os, shutil, subprocess, sys
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit3d, ps2look
import render_cutscene as rc

OUT = os.path.join(HERE, "out", "chadlite")


def blender(mode, out, extra=(), tries=6):
    """Blender 5.2 crashes now and then mid-run (EXCEPTION_ACCESS_VIOLATION); the clip skips frames already on
    disk, so each retry carries on where the last one stopped."""
    for attempt in range(tries):
        r = subprocess.run([kit3d.BLENDER, "-b", "--factory-startup", "-noaudio", "-P",
                            os.path.join(HERE, "lowpoly_cast.py"), "--", out, mode, *extra])
        if r.returncode == 0:
            return
        print(f"Blender exited with {r.returncode} (attempt {attempt + 1}); resuming")
    raise RuntimeError("Blender kept crashing")


def clip():
    ep = rc.EPISODES["chad_tryptophan"]
    rc.voice_lines(ep, os.path.join(HERE, "out", "chad_tryptophan"))        # cached takes, no new voice calls
    chad = [b for b in ep["beats"] if b.get("who") == "chad"]
    myth = next(b for b in chad if "myth" in b["say"])
    reel = next(b for b in chad if "reel" in b["say"].lower())
    fps, sr = rc.FPS, rc.SR
    t_myth, t_reel = 0.6, 2.55
    dur = t_reel + len(reel["_audio"]) / sr + 1.0
    nf = int(round(dur * fps))
    audio = np.zeros(int(dur * sr) + sr)
    mouth, shape = [0.0] * nf, ["aa"] * nf
    for t0, b in ((t_myth, myth), (t_reel, reel)):
        a = b["_audio"]
        i0 = int(t0 * sr)
        audio[i0:i0 + len(a)] += a
        m, sh = rc.mouth_curves(a)
        f0 = int(round(t0 * fps))
        for i, (v, s) in enumerate(zip(m, sh)):
            if f0 + i < nf:
                mouth[f0 + i], shape[f0 + i] = v, s
    C = {"mouth": mouth, "shape": shape, "blinks": [1.75, 4.05],
         # a pose on every sentence, hitting on it: hands on hips, point on "myth", arms crossed, shrug on "reel"
         "poses": [[0.0, "hips", "smug"], [t_myth - 0.05, "point", "smug"], [1.9, "crossed", "neutral"],
                   [t_reel - 0.05, "shrug", "smug"]],
         "shots": [[0.0, 35, [0.0, -2.5, 1.2], [0.0, 0.0, 1.15], 0.35],
                   [2.4, 45, [0.1, -1.25, 1.68], [0.0, 0.0, 1.6], 0.12]]}
    os.makedirs(OUT, exist_ok=True)
    cj = os.path.join(OUT, "clip.json")
    json.dump(C, open(cj, "w"))
    low, big = os.path.join(OUT, "low"), os.path.join(OUT, "frames")
    if "--keep" not in sys.argv:                              # --keep: reuse frames already rendered
        shutil.rmtree(low, ignore_errors=True)
    blender("clip", low, [cj])
    ps2look.post_dir(low, big, range(nf))
    wav = os.path.join(OUT, "clip.wav")
    sf.write(wav, audio[:int(nf / fps * sr)], sr)
    mp4 = os.path.join(OUT, "2026-11-26_Chadlite_Test.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-i", os.path.join(big, "f_%05d.png"),
                    "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", mp4], check=True)
    print(mp4)


def sheet(modes=("turnaround", "faces")):
    low = os.path.join(OUT, "stills_low")
    for m in modes:
        blender(m, low)
    for f in sorted(os.listdir(low)):
        if f.endswith(".png"):
            ps2look.post(os.path.join(low, f), os.path.join(OUT, f))
    print(OUT)


if __name__ == "__main__":
    {"clip": clip, "sheet": sheet, "lineup": lambda: sheet(("lineup",))}[sys.argv[1]]()
