"""Clay-look test: the Gym Bro episode (render_gym.py) re-shot on the clay set (gymclay_scene.py, clay.py). Same
narration, timing, overlay and sound; only the 3D picture changes, so the two looks can be compared shot for shot.

python render_gymclay.py preview 1.2,22.0     stills into preview/gymclay_*.png
python render_gymclay.py out.mp4 out.wav       full render (Blender frames cached in out/gymclay/frames)
Set OVERTHOUGHT_CPU_PREVIEW=1 to render stills with Cycles on the CPU while the GPU is busy.
"""
import json, os, sys
import render_gym as G
import render_tap as tap
import kit3d as K

FRAMES = os.path.join(G.ROOT, "out", "gymclay", "frames")
tap.draw_captions = tap.draw_captions_clay          # the clay look's cream caption label

def main(out_mp4, out_wav, preview_times=None):
    sents, speech_end, duration, E = G.setup()
    n_frames = int(round(duration * G.FPS))
    frames = sorted({min(n_frames - 1, int(round(x * G.FPS))) for x in preview_times}) if preview_times else range(n_frames)
    K.run_blender("gymclay_scene.py", G.OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, G.FPS)
    if preview_times:                                   # CPU previews come out at half size
        from PIL import Image
        for f in frames:
            path = os.path.join(FRAMES, f"f_{f + 1:05d}.png")
            im = Image.open(path)
            if im.size != (1080, 1920):
                im.resize((1080, 1920), Image.LANCZOS).save(path)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0]
    if not preview_times:
        G.build_audio(sents, E, duration, out_wav)
    K.composite(FRAMES, frames, G.FPS, lambda c, t, Fr: G.overlay(c, t, Fr, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "gymclay" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        main(None, None, preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
