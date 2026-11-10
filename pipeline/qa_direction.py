"""Checks a rendered episode against its shot list (ops/direction.md): does the eye land where the shot says, is the
frame muddy or flat, does the biggest visual event land on the one big moment, does it loop.

python qa_direction.py <video.mp4> <shots.json> [out.png]

shots.json is what direct.ShotList.dump() writes. Prints a report and saves a contact sheet: one frame per shot with a
cyan ring where the shot puts the eye and a magenta square on the spot that pulls hardest (bright, contrasty, saturated).
These are measurements, not taste: a shot can fail one on purpose (a silhouette is meant to be dark), but say why.
"""
import json, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw

W, H = 270, 480          # analysis size (9:16)
GX, GY = 9, 16           # attention grid: 30 px blocks

def grab(video, t, w=W, h=H):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t):.3f}", "-i", video, "-frames:v", "1",
                          "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.uint8)[: w * h * 3].reshape(h, w, 3).astype(np.float32) / 255.0

def stream_gray(video, fps=30, w=90, h=160):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps={fps},scale={w}:{h}", "-f", "rawvideo",
                          "-pix_fmt", "gray", "-"], check=True, capture_output=True).stdout
    n = len(raw) // (w * h)
    return np.frombuffer(raw, np.uint8)[: n * w * h].reshape(n, h, w).astype(np.float32) / 255.0

def luma(rgb):
    return rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722

def sat(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    return np.where(mx > 1e-3, (mx - mn) / np.maximum(mx, 1e-3), 0.0)

def attention(rgb):
    """Per-block pull: brightness relative to the frame, local contrast and saturation (what eyes go to first)."""
    L, S = luma(rgb), sat(rgb)
    bh, bw = H // GY, W // GX
    Lb = L[: GY * bh, : GX * bw].reshape(GY, bh, GX, bw)
    Sb = S[: GY * bh, : GX * bw].reshape(GY, bh, GX, bw)
    mean = Lb.mean((1, 3))
    con = Lb.std((1, 3))
    sb = (Sb * (Lb > 0.08)).mean((1, 3))         # colour only counts where there is light to see it
    score = (mean - L.mean()) + 1.2 * con + 0.35 * sb
    score[: int(GY * 0.22)] = -1.0                # the caption band: captions pull by design, judge the picture
    return score

def light_focus(rgb, ex, ey):
    """Where the light goes: mean brightness near the eye over mean brightness far from it. An evenly lit frame is
    about 1; a directed frame (lit subject, falloff into shadow) is 1.6 and up."""
    L = luma(rgb)
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.hypot((xx - ex * W) / W, (yy - ey * H) / W)     # in frame widths
    keep = yy > H * 0.22
    near = L[(d < 0.16) & keep]
    far = L[(d > 0.42) & keep]
    return float(near.mean() / max(far.mean(), 1e-3)) if near.size and far.size else 0.0

def muddy(rgb):
    L, S = luma(rgb), sat(rgb)
    return float(((L > 0.18) & (L < 0.62) & (S < 0.22)).mean())

def spread(rgb):
    L = luma(rgb)
    return float(np.percentile(L, 97) - np.percentile(L, 3))

def main(video, shots_path, out_png=None):
    sj = json.load(open(shots_path))
    shots, big = sj["shots"], sj.get("big")
    rows, sheet = [], []
    print(f"{'shot':14s} {'len':>5s} {'eye rank':>8s} {'pull at':>11s} {'light':>6s} {'muddy':>6s} {'range':>6s}")
    for s in shots:
        t = s["hit"] + 0.15 if s.get("hit") is not None else (s["t0"] + s["t1"]) / 2
        t = min(t, s["t1"] - 0.05)
        rgb = grab(video, t)
        sc = attention(rgb)
        ex, ey = s["screen"]
        bx, by = min(GX - 1, int(ex * GX)), min(GY - 1, int(ey * GY))
        # the eye's block and its neighbours: a subject is bigger than one block
        local = sc[max(0, by - 1): by + 2, max(0, bx - 1): bx + 2].max()
        rank = float((sc < local).mean())
        lf = light_focus(rgb, ex, ey)
        py, px = np.unravel_index(np.argmax(sc), sc.shape)
        m, r = muddy(rgb), spread(rgb)
        flags = []
        if rank < 0.80:
            flags.append("the eye isn't the strongest spot")
        if lf < 1.4:
            flags.append("light is even, not on the subject")
        if m > 0.50:
            flags.append("muddy")
        if r < 0.45:
            flags.append("flat")
        rows.append({"shot": s["name"], "t": round(t, 2), "eye_rank": round(rank, 2), "light": round(lf, 2), "muddy": round(m, 2),
                     "range": round(r, 2), "pull": [round((px + 0.5) / GX, 2), round((py + 0.5) / GY, 2)], "flags": flags})
        print(f"{s['name'][:14]:14s} {s['t1'] - s['t0']:5.2f} {rank:8.2f}  ({(px + .5) / GX:.2f},{(py + .5) / GY:.2f})"
              f" {lf:6.2f} {m:6.2f} {r:6.2f}  {'; '.join(flags)}")
        im = Image.fromarray((rgb * 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        cx, cy = ex * W, ey * H
        d.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), outline=(0, 230, 255), width=3)
        qx, qy = px * (W // GX), py * (H // GY)
        d.rectangle((qx, qy, qx + W // GX, qy + H // GY), outline=(255, 0, 200), width=3)
        d.text((6, H - 16), f"{s['name'][:18]} {t:.1f}s", fill=(255, 255, 255))
        sheet.append(im)

    # rhythm
    lens_ = [s["t1"] - s["t0"] for s in shots]
    print(f"\nshot lengths: {', '.join(f'{x:.1f}' for x in lens_)}  (min {min(lens_):.1f}, max {max(lens_):.1f})")
    if len(lens_) > 3 and max(lens_) < 1.3 * min(lens_):
        print("RHYTHM: every shot is about the same length")

    # the one big moment: the largest change inside a shot (cuts masked out)
    fps = 30
    g = stream_gray(video, fps)
    diff = np.abs(np.diff(g, axis=0)).mean((1, 2))
    for s in shots[1:]:
        k = int(round(s["t0"] * fps))
        diff[max(0, k - 2): k + 2] = 0
    smoothd = np.convolve(diff, np.ones(5) / 5, mode="same")
    peak_t = (int(np.argmax(smoothd)) + 1) / fps
    print(f"biggest change inside a shot: {peak_t:.2f} s" + (f"; the one big moment is at {big:.2f} s" if big else ""))
    if big is not None and abs(peak_t - big) > 0.6:
        print("BIG MOMENT: something else moves more than the big moment. Quiet it, or make the moment bigger.")
    second = np.sort(smoothd)[-int(fps * 0.6)] if len(smoothd) > fps else 0
    if smoothd.max() < 1.6 * max(second, 1e-6):
        print("BIG MOMENT: no single moment stands out; the energy is spread evenly")

    # loop
    a, b = g[0], g[-1]
    loop = float(np.abs(a - b).mean())
    print(f"loop: first vs last frame differ by {loop:.3f}" + ("  (loops)" if loop < 0.04 else ""))

    if out_png and sheet:
        cols = min(6, len(sheet))
        rows_n = (len(sheet) + cols - 1) // cols
        big_im = Image.new("RGB", (cols * W, rows_n * H), (0, 0, 0))
        for i, im in enumerate(sheet):
            big_im.paste(im, ((i % cols) * W, (i // cols) * H))
        big_im.save(out_png)
        print("sheet:", out_png)
    return rows

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
