"""Watch a reel for free: transcribe it with Whisper on this laptop and tile frames into a contact sheet.

python watch.py <video file> [name]     -> out/watch/<name>/transcript.txt, transcript.json, sheet.png

Getting the file: open the reel in the Chrome tab signed in as @overthought.daily and record it from the page
(the video element's captureStream into MediaRecorder, then a download link); it lands in ~/Downloads as a .webm.
The Whisper model (small.en) is in vendor/whisper; it runs on the CPU in int8, about real time or faster.
"""
import json, os, subprocess, sys
from common import ROOT

def transcribe(path):
    from faster_whisper import WhisperModel
    m = WhisperModel("small.en", device="cpu", compute_type="int8", download_root=os.path.join(ROOT, "vendor", "whisper"))
    import numpy as np
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         check=True, capture_output=True).stdout       # ffmpeg decodes; faster-whisper's own loader trips on this PyAV
    audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
    segs, info = m.transcribe(audio, vad_filter=True, word_timestamps=False)
    return [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs], info.duration

def sheet(path, out_png, every=3.0, cols=6, width=270):
    tmp = os.path.join(os.path.dirname(out_png), "f_%03d.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vf", f"fps=1/{every},scale={width}:-2", tmp], check=True)
    from PIL import Image
    d = os.path.dirname(out_png)
    fs = sorted(f for f in os.listdir(d) if f.startswith("f_") and f.endswith(".png"))
    ims = [Image.open(os.path.join(d, f)).convert("RGB") for f in fs]
    if not ims:
        return 0
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    s = Image.new("RGB", (w * cols, h * rows))
    for i, im in enumerate(ims):
        s.paste(im, ((i % cols) * w, (i // cols) * h))
    s.save(out_png)
    for f in fs:
        os.remove(os.path.join(d, f))
    return len(ims)

def main(path, name=None):
    name = name or os.path.splitext(os.path.basename(path))[0]
    out = os.path.join(ROOT, "out", "watch", name)
    os.makedirs(out, exist_ok=True)
    segs, dur = transcribe(path)
    n = sheet(path, os.path.join(out, "sheet.png"))
    with open(os.path.join(out, "transcript.json"), "w", encoding="utf-8") as fh:
        json.dump({"source": path, "duration": dur, "segments": segs}, fh, indent=1)
    text = "\n".join(f"[{s['start']:5.1f}] {s['text']}" for s in segs)
    open(os.path.join(out, "transcript.txt"), "w", encoding="utf-8").write(text + "\n")
    print(f"{name}: {dur:.1f} s, {len(segs)} segments, {n} frames -> {out}")
    print(text)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
