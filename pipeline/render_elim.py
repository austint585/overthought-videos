"""Render 'Last Flag Standing' from the elimination sim."""
import math, random, sys, io, os, tempfile
import numpy as np
import skia, cairosvg
from common import *
import sim_elim as S

SEED, GAP0, GROWTH = 6, 0.28, 0.18
DY = -30                      # shift the sim upward on screen to clear Instagram's caption area
CX, CY, R, BR = S.CX, S.CY + DY, S.R, S.BALL_R
FLAG_DIR = os.path.join(ROOT, "vendor", "node_modules", "flag-icons", "flags", "1x1")
END_HOLD = 4.2                # seconds of winner screen
TRAY_Y0, TRAY_PITCH, TRAY_COLS, TRAY_D = 1432, 43, 16, 36

def load_flags(countries):
    imgs = {}
    for code, _ in countries:
        png = cairosvg.svg2png(url=f"{FLAG_DIR}/{code}.svg", output_width=160, output_height=160)
        imgs[code] = skia.Image.MakeFromEncoded(skia.Data.MakeWithCopy(png))
    return imgs

def gray_image(img):
    surf = skia.Surface(img.width(), img.height())
    c = surf.getCanvas()
    m = [0.33, 0.33, 0.33, 0, 0,  0.33, 0.33, 0.33, 0, 0,  0.33, 0.33, 0.33, 0, 0,  0, 0, 0, 1, 0]
    c.drawImage(img, 0, 0, skia.SamplingOptions(), skia.Paint(ColorFilter=skia.ColorFilters.Matrix(m)))
    return surf.makeImageSnapshot()

def draw_flag_ball(c, img, x, y, r, alpha=1.0, outline=INK, ow=3.0):
    path = skia.Path(); path.addCircle(x, y, r)
    c.save(); c.clipPath(path, doAntiAlias=True)
    p = skia.Paint(AntiAlias=True); p.setAlphaf(alpha)
    c.drawImageRect(img, skia.Rect(x - r, y - r, x + r, y + r), skia.SamplingOptions(skia.FilterMode.kLinear), p)
    c.restore()
    c.drawCircle(x, y, r, paint(outline, alpha, Style=skia.Paint.kStroke_Style, StrokeWidth=ow))

def tray_slot(k):
    row, col = divmod(k, TRAY_COLS)
    x0 = W / 2 - (TRAY_COLS - 1) * TRAY_PITCH / 2
    return x0 + col * TRAY_PITCH, TRAY_Y0 + row * TRAY_PITCH

def main(out_mp4, out_wav, preview_frames=None):
    sim = S.simulate(seed=SEED, gap0=GAP0, gap_growth=GROWTH, max_seconds=120)
    frames, events, n = sim["frames"], sim["events"], sim["n"]
    countries = sim["countries"]
    names = {i: countries[i][1] for i in range(n)}
    codes = {i: countries[i][0] for i in range(n)}
    flags = load_flags(countries)
    grays = {k: gray_image(v) for k, v in flags.items()}

    out_order = sorted([(f, i) for i, f in sim["out_frames"].items() if f is not None])
    slot_of = {i: k for k, (f, i) in enumerate(out_order)}
    exit_pos = {}
    for f, i in out_order:
        st = frames[f]
        for (bi, x, y, a, alive) in st["balls"]:
            if bi == i:
                exit_pos[i] = (x, y + DY)
    win_i, win_code, win_name = sim["winner"]
    wf = len(frames) - 1                      # last sim frame
    total_frames = len(frames) + int(END_HOLD * FPS)
    duration = total_frames / FPS
    print(f"sim {len(frames)/FPS:.1f}s, total {duration:.1f}s, winner {win_name}", flush=True)

    # ---------------- audio
    tr = new_track(duration)
    beat_bed(tr, 0.0, len(frames) / FPS, bpm=124, gain=0.16, hat_gain=0.07,
             dense_from=next(t for t, k, s, e in events if k == "out" and
                             sum(1 for tt, kk, *_ in events if kk == "out" and tt <= t) == n - 5))
    scale = [261.63, 293.66, 329.63, 392.0, 440.0]  # C major pentatonic
    notes = [f * m for m in (1, 2, 4) for f in scale]
    last_t = -1
    rnd = random.Random(3)
    for t, kind, s, extra in events:
        if kind == "wall" and t - last_t > 0.075:
            f = rnd.choice(notes[3:12])
            add(tr, t, tone(f, 0.25, tau=0.06, harmonics=(1, 0.3, 0.12)), 0.10 + 0.12 * s)
            last_t = t
    pop = noise_burst(0.12, tau=0.025, lp=0.5, seed=5)
    for t, kind, s, extra in events:
        if kind == "out":
            add(tr, t, sweep(900, 180, 0.28, tau=0.1), 0.32)
            add(tr, t, pop, 0.5)
    t_win = len(frames) / FPS
    add(tr, t_win, kick(0.6), 0.8)
    for k, f in enumerate([523.25, 659.25, 783.99, 1046.5]):
        add(tr, t_win + 0.09 * k, tone(f, 1.6, tau=0.5, harmonics=(1, 0.5, 0.25, 0.12)), 0.22)
    for f in (261.63, 329.63, 392.0):
        add(tr, t_win + 0.4, tone(f, 3.5, tau=1.4, harmonics=(1, 0.4, 0.2), attack=0.25), 0.12)
    save_wav(tr, out_wav, duration)

    # ---------------- video
    f_title = font("Bricolage-800", 84)
    f_sub = font("JetBrainsMono-500", 29)
    f_count = font("JetBrainsMono-800", 128)
    f_label = font("JetBrainsMono-700", 30)
    f_out = font("Bricolage-700", 40)
    f_tag = font("Bricolage-700", 24)

    enc = None if preview_frames else open_encoder(out_mp4, out_wav)
    surf = skia.Surface(W, H)
    trails = {}
    confetti = []
    crnd = random.Random(9)
    pal = [ORANGE, INK, skia.Color(255, 209, 64), skia.Color(90, 170, 255), skia.Color(120, 220, 140)]

    frame_iter = preview_frames if preview_frames else range(total_frames)
    for F in frame_iter:
        c = surf.getCanvas()
        background(c, CX, CY, 1150)
        simF = min(F, wf)
        st = frames[simF]
        alive_n = st["alive"]
        ending = F > wf
        te = (F - wf) / FPS if ending else 0.0

        # ---- HUD
        text_center(c, "LAST FLAG STANDING", W / 2, 205, f_title, paint(INK))
        sub_a = 1.0 if not ending else max(0.0, 1 - te * 3)
        if sub_a > 0:
            text_center(c, "comment your country before it starts", W / 2, 258, f_sub, paint(MUTED, sub_a))
        if not ending:
            col = ORANGE if alive_n <= 5 else INK
            pulse = 1.0
            if alive_n <= 3:
                pulse = 1 + 0.06 * math.sin(F / FPS * 2 * math.pi * 2)
            c.save(); c.translate(W / 2, 420); c.scale(pulse, pulse)
            text_center(c, str(alive_n), 0, 0, f_count, paint(col))
            c.restore()
            text_center(c, "LEFT", W / 2, 466, f_label, paint(MUTED))
            # latest elimination ticker
            last = [(f, i) for f, i in out_order if f <= F]
            if last:
                f0, i0 = last[-1]
                age = (F - f0) / FPS
                if age < 1.4:
                    a = 1.0 if age < 0.9 else 1 - (age - 0.9) / 0.5
                    text_center(c, f"{names[i0]} is out", W / 2, 528, f_out, paint(ORANGE, a))

        # ---- ring
        ga = st["ring_angle"] + st["gap_local"]
        gw = st["gap_w"]
        oval = skia.Rect(CX - R - 6, CY - R - 6, CX + R + 6, CY + R + 6)
        start = math.degrees(ga + gw / 2)
        sweep_deg = 360 - math.degrees(gw)
        ring_alpha = 1.0 if not ending else max(0.0, 1 - te * 1.4)
        glow = paint(ORANGE, 0.55 * ring_alpha, Style=skia.Paint.kStroke_Style, StrokeWidth=26,
                     StrokeCap=skia.Paint.kRound_Cap, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
        if ring_alpha > 0:
            c.drawArc(oval, start, sweep_deg, False, glow)
            c.drawArc(oval, start, sweep_deg, False,
                      paint(INK, ring_alpha, Style=skia.Paint.kStroke_Style, StrokeWidth=12, StrokeCap=skia.Paint.kRound_Cap))

        # ---- tray of eliminated flags
        for f0, i0 in out_order:
            k = slot_of[i0]
            sx, sy = tray_slot(k)
            if F >= f0 + 32:
                draw_flag_ball(c, grays[codes[i0]], sx, sy, TRAY_D / 2, 0.55, outline=MUTED, ow=2)
        # empty slot outlines for the ones still alive (a faint grid hints at what's to come)
        for k in range(len(out_order), n - 1):
            pass

        # ---- balls
        show_names = alive_n <= 8 and not ending
        for (bi, x, y, a, alive) in st["balls"]:
            y += DY
            if alive:
                if alive_n <= 8 and not ending:
                    tl = trails.setdefault(bi, [])
                    tl.append((x, y))
                    if len(tl) > 14:
                        tl.pop(0)
                    for k, (tx, ty) in enumerate(tl[:-1]):
                        aa = (k + 1) / len(tl) * 0.22
                        c.drawCircle(tx, ty, BR * (0.4 + 0.6 * (k + 1) / len(tl)), paint(ORANGE, aa))
                if ending and bi == win_i:
                    continue
                draw_flag_ball(c, flags[codes[bi]], x, y, BR)
                if show_names:
                    text_center(c, names[bi], x, y + BR + 30, f_tag, paint(INK, 0.9))
            else:
                f0 = sim["out_frames"][bi]
                age = F - f0
                if age < 32:
                    ex, ey = exit_pos[bi]
                    tx, ty = tray_slot(slot_of[bi])
                    u = ease_io(age / 32)
                    # arc downward-then-into-slot
                    x2 = ex + (tx - ex) * u
                    y2 = ey + (ty - ey) * u - math.sin(u * math.pi) * 60
                    r2 = BR + (TRAY_D / 2 - BR) * u
                    draw_flag_ball(c, flags[codes[bi]], x2, y2, r2, 1.0 - 0.3 * u)

        # ---- winner sequence
        if ending:
            wx, wy = [(x, y + DY) for (bi, x, y, a, al) in frames[wf]["balls"] if bi == win_i][0]
            u = ease_out(te / 0.9)
            x2 = wx + (CX - wx) * u
            y2 = wy + (CY - 30 - wy) * u
            r2 = BR + (170 - BR) * u
            # halo
            c.drawCircle(x2, y2, r2 + 20 + 8 * math.sin(te * 6), paint(ORANGE, 0.35 * u,
                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 30)))
            draw_flag_ball(c, flags[win_code], x2, y2, r2, ow=6)
            if te > 0.35:
                a = ease_out((te - 0.35) / 0.4)
                c.save(); c.translate(W / 2, 430); c.scale(0.8 + 0.2 * a, 0.8 + 0.2 * a)
                fw = fit_font("Bricolage-800", win_name.upper(), 900, 120)
                text_center(c, win_name.upper(), 0, 0, fw, paint(ORANGE, a))
                c.restore()
                text_center(c, "WINS", W / 2, 500, f_label, paint(INK, a))
            if te > 1.2:
                a = ease_out((te - 1.2) / 0.5)
                text_center(c, "Not your country?", W / 2, CY + 270, font("Bricolage-700", 46), paint(INK, a))
                text_center(c, "Comment it. You're in the next round.", W / 2, CY + 325, font("Bricolage-700", 38), paint(MUTED, a))
            # confetti
            if F == wf + 1:
                for _ in range(170):
                    ang = crnd.uniform(-math.pi, 0)
                    sp = crnd.uniform(500, 1500)
                    confetti.append([CX, CY - 30, sp * math.cos(ang) * 0.9, sp * math.sin(ang), crnd.uniform(0, 6.28),
                                     crnd.uniform(-10, 10), crnd.choice(pal), crnd.uniform(9, 16)])
            for p in confetti:
                p[0] += p[2] / FPS; p[1] += p[3] / FPS; p[3] += 1400 / FPS; p[2] *= 0.992; p[4] += p[5] / FPS
                c.save(); c.translate(p[0], p[1]); c.rotate(math.degrees(p[4]))
                c.drawRect(skia.Rect(-p[7] / 2, -p[7] / 4, p[7] / 2, p[7] / 4), paint(p[6]))
                c.restore()

        if preview_frames:
            surf.makeImageSnapshot().save(f"preview/elim_{F:05d}.png", skia.kPNG)
        else:
            enc.stdin.write(frame_bytes(surf))
            if F % 600 == 0:
                print(f"frame {F}/{total_frames}", flush=True)
    if enc:
        enc.stdin.close(); enc.wait()
    return sim

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        frames = [int(x) for x in sys.argv[2].split(",")]
        main(None, os.path.join(tempfile.gettempdir(), "elim_preview.wav"), preview_frames=frames)
    else:
        main(sys.argv[1], sys.argv[2])
