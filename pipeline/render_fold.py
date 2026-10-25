"""'Folding paper 103 times': a zoom-out what-if with a fold counter and true-scale height lines."""
import math, random, sys, os, tempfile
import numpy as np
import skia
from common import *

T0 = 1e-4                    # sheet thickness, meters
LY = 9.4607e15               # meters per light-year
GROUND_Y, TOP_Y, VIEW_TOP = 1450, 820, 610
STACK_X, STACK_W = 250, 120

def h(f):
    return T0 * 2.0 ** f

def fmt_thickness(m):
    mm = m * 1000
    if mm < 10:
        return f"{mm:.1f} mm"
    if mm < 100:
        return f"{mm:.1f} mm"
    if m < 1:
        return f"{m*100:.1f} cm"
    if m < 10:
        return f"{m:.2f} m"
    if m < 1000:
        return f"{m:,.0f} m" if m >= 100 else f"{m:.1f} m"
    km = m / 1000
    if km < 10:
        return f"{km:.2f} km"
    if km < 1e6:
        return f"{km:,.0f} km"
    if km < 1e9:
        return f"{km/1e6:,.0f} million km" if km >= 1e7 else f"{km/1e6:.1f} million km"
    if m < LY:
        if km < 1e12:
            return f"{km/1e9:,.0f} billion km" if km >= 1e10 else f"{km/1e9:.1f} billion km"
        return f"{km/1e12:.1f} trillion km"
    ly = m / LY
    if ly < 10:
        return f"{ly:.1f} light-years"
    if ly < 1e6:
        return f"{ly:,.0f} light-years"
    if ly < 1e9:
        return f"{ly/1e6:,.0f} million light-years"
    return f"{ly/1e9:,.0f} billion light-years"

# reference heights drawn as dashed lines (name, meters, value label)
LANDMARKS = [
    ("Credit card", 0.00076, "0.76 mm"),
    ("Phone", 0.008, "8 mm"),
    ("Coffee mug", 0.095, "9.5 cm"),
    ("You", 1.75, "1.75 m"),
    ("4-story building", 13.0, "13 m"),
    ("Statue of Liberty", 93.0, "93 m"),
    ("Burj Khalifa", 828.0, "828 m"),
    ("Mount Everest", 8849.0, "8,849 m"),
    ("Jets cruise here", 11000.0, "11 km"),
    ("Edge of space", 100_000.0, "100 km"),
    ("Space Station", 400_000.0, "400 km"),
    ("The Moon", 384_400e3, "384,400 km"),
    ("The Sun", 149.6e9, "150 million km"),
    ("Milky Way", 100_000 * LY, "100,000 light-years across"),
    ("Observable universe", 93e9 * LY, "93 billion light-years"),
]

# stops: (fold, hold seconds, callout, emphasis landmark name or None, big moment?)
STOPS = [
    (0, 2.6, "What if you folded paper 103 times?|One sheet is 0.1 mm thick", None, False),
    (3, 1.6, "As thick as a credit card", "Credit card", False),
    (7, 1.6, "Thicker than your phone", "Phone", False),
    (10, 1.6, "Taller than a coffee mug", "Coffee mug", False),
    (14, 1.8, "Almost as tall as you", "You", False),
    (17, 1.6, "As tall as a 4-story building", "4-story building", False),
    (20, 1.8, "Taller than the Statue of Liberty", "Statue of Liberty", False),
    (23, 1.9, "Taller than the Burj Khalifa", "Burj Khalifa", False),
    (27, 2.2, "Higher than Everest. Higher than planes fly.", "Mount Everest", False),
    (30, 2.0, "Fold 30: you're in space", "Edge of space", True),
    (32, 1.9, "Higher than the Space Station", "Space Station", False),
    (42, 2.4, "Fold 42: it reaches the Moon", "The Moon", True),
    (51, 2.3, "Fold 51: past the Sun", "The Sun", True),
    (83, 2.3, "Fold 83: as long as the Milky Way is wide", "Milky Way", True),
    (103, 2.8, "Fold 103: longer than the observable universe is wide", "Observable universe", True),
]
OUTRO = 3.4

def build_timeline():
    """List of segments: ('hold', fold, t0, t1, stop_idx) or ('move', f0, f1, t0, t1)."""
    segs, t = [], 0.0
    for k, (fold, hold, *_rest) in enumerate(STOPS):
        if k > 0:
            f0 = STOPS[k - 1][0]
            d = fold - f0
            dur = max(0.5, min(2.6, 0.32 + 0.11 * d))
            segs.append(("move", f0, fold, t, t + dur, k))
            t += dur
        segs.append(("hold", fold, fold, t, t + hold, k))
        t += hold
    segs.append(("outro", STOPS[-1][0], STOPS[-1][0], t, t + OUTRO, len(STOPS)))
    return segs, t + OUTRO

def state_at(segs, t):
    for s in segs:
        kind, f0, f1, a, b, k = s
        if a <= t < b or s is segs[-1]:
            u = (t - a) / (b - a) if b > a else 1
            if kind == "move":
                # ease in-out on the exponent so the growth feels like a rush
                f = f0 + (f1 - f0) * ease_io(u)
                return kind, f, k, u, t - a
            return kind, f0, k, u, t - a
    return "outro", STOPS[-1][0], len(STOPS), 1.0, 0

def main(out_mp4, out_wav, preview_times=None):
    segs, duration = build_timeline()
    total_frames = int(duration * FPS)
    print(f"duration {duration:.1f}s", flush=True)

    # ---------------- audio
    tr = new_track(duration)
    beat_bed(tr, 2.0, duration - OUTRO, bpm=108, gain=0.12, hat_gain=0.05)
    # warm drone underneath
    n = len(tr); tt = np.arange(n) / SR
    drone = (np.sin(2 * np.pi * 55 * tt) + 0.6 * np.sin(2 * np.pi * 82.4 * tt) + 0.3 * np.sin(2 * np.pi * 110.3 * tt))
    drone *= 0.035 * (0.75 + 0.25 * np.sin(2 * np.pi * 0.11 * tt))
    fade = np.clip(tt / 1.5, 0, 1) * np.clip((duration - tt) / 1.0, 0, 1)
    tr += drone * fade
    fwip = noise_burst(0.07, tau=0.018, lp=0.6, seed=11)
    last_tick = -1.0
    prev_int = 0
    for F in range(total_frames):
        t = F / FPS
        kind, f, k, u, _ = state_at(segs, t)
        fi = int(math.floor(f + 1e-9))
        if fi > prev_int:
            for _ in range(fi - prev_int):
                if t - last_tick >= 0.05:
                    semis = min(fi, 103) * 0.35
                    add(tr, t, tone(330 * 2 ** (semis / 12), 0.09, tau=0.03, harmonics=(1, 0.4)), 0.13)
                    add(tr, t, fwip, 0.22)
                    last_tick = t
            prev_int = fi
    for k, (fold, hold, text, lm, big) in enumerate(STOPS):
        t = [s for s in segs if s[0] == "hold" and s[5] == k][0][3]
        if k == 0:
            continue
        bell = tone(1046.5, 1.2, tau=0.35, harmonics=(1, 0.0, 0.35, 0.0, 0.15))
        b2 = tone(1568, 0.9, tau=0.25)
        bell[: len(b2)] += 0.5 * b2
        add(tr, t, bell, 0.16)
        if big:
            add(tr, t, kick(0.7), 0.55)
            add(tr, t, sweep(80, 40, 1.2, tau=0.5), 0.35)
    t_out = segs[-1][3]
    for kf, fq in enumerate([392.0, 493.88, 587.33]):
        add(tr, t_out + 0.15 * kf, tone(fq, 2.4, tau=0.9, harmonics=(1, 0.4, 0.15), attack=0.01), 0.15)
    save_wav(tr, out_wav, duration)

    # ---------------- video
    f_head = font("Bricolage-800", 46)
    f_foldlbl = font("JetBrainsMono-700", 28)
    f_count = font("JetBrainsMono-800", 176)
    f_thick = font("Bricolage-800", 70)
    f_lm = font("Bricolage-700", 36)
    f_lmv = font("JetBrainsMono-500", 26)

    srnd = random.Random(4)
    stars = [(srnd.uniform(0, W), srnd.uniform(0, H), srnd.uniform(0.6, 2.2), srnd.uniform(0.3, 1.0)) for _ in range(260)]

    enc = None if preview_times else open_encoder(out_mp4, out_wav)
    surf = skia.Surface(W, H)
    frames = [int(t * FPS) for t in preview_times] if preview_times else range(total_frames)
    prev_fi = 0
    flash_t = -10.0
    for F in frames:
        t = F / FPS
        kind, f, k, u, tin = state_at(segs, t)
        fi = int(math.floor(f + 1e-9))
        if fi != prev_fi:
            flash_t = t
            prev_fi = fi
        c = surf.getCanvas()
        background(c, W / 2, 1000, 1200)

        # stars fade in once we're past the atmosphere
        sa = max(0.0, min(1.0, (f - 27.5) / 3))
        if sa > 0:
            drift = min(f, 103) * 3.0
            for (x, y, r, a) in stars:
                yy = (y + drift * r) % H
                c.drawCircle(x, yy, r, paint(INK, sa * a * 0.7))

        outro_a = 1.0
        if kind == "outro":
            outro_a = max(0.0, 1 - tin / 0.5)

        # ---- header + counter
        text_center(c, "FOLDING PAPER 103 TIMES", W / 2, 180, f_head, paint(INK, outro_a))
        if outro_a > 0:
            text_center(c, "FOLD", W / 2, 240, f_foldlbl, paint(MUTED, outro_a))
            pop = 1.0 + 0.07 * max(0.0, 1 - (t - flash_t) / 0.12)
            c.save(); c.translate(W / 2, 395); c.scale(pop, pop)
            text_center(c, str(fi), 0, 0, f_count, paint(INK, outro_a))
            c.restore()
            text_center(c, fmt_thickness(h(fi)), W / 2, 482, f_thick, paint(ORANGE, outro_a))
            # callout during holds
            if kind == "hold":
                text = STOPS[k][2]
                a = ease_out(tin / 0.25) * outro_a
                if "|" in text:
                    first, second = text.split("|")
                    if tin < 1.3:
                        text = first
                    else:
                        text = second
                        a = ease_out((tin - 1.3) / 0.25) * outro_a
                ff = fit_font("Bricolage-700", text, 940, 44)
                text_center(c, text, W / 2, 556, ff, paint(INK, a))

        # ---- visual: true-scale view where the stack top always sits at TOP_Y
        hh = h(f)
        ppm = (GROUND_Y - TOP_Y) / hh          # pixels per meter
        vis_a = outro_a
        c.save()
        c.clipRect(skia.Rect(0, VIEW_TOP, W, H))
        # landmark lines
        emph = STOPS[k][3] if kind == "hold" else None
        for name, L, val in LANDMARKS:
            y = GROUND_Y - L * ppm
            if y < VIEW_TOP - 40 or y > GROUND_Y - 4:
                continue
            a = vis_a
            a *= min(1.0, (y - VIEW_TOP + 40) / 90)           # fade in from the top
            a *= max(0.0, min(1.0, (GROUND_Y - 120 - y) / 110))  # fade out before the ground
            if a <= 0.01:
                continue
            reached = L <= hh
            is_emph = (name == emph)
            col = ORANGE if is_emph else (INK if not reached else MUTED)
            lw = 3.5 if is_emph else 2
            dash = skia.DashPathEffect.Make([14, 10], 0)
            c.drawLine(110, y, 940, y, paint(col, a * (1.0 if is_emph else 0.75), Style=skia.Paint.kStroke_Style,
                                             StrokeWidth=lw, PathEffect=dash))
            c.drawString(name, 420, y - 14, f_lm, paint(col, a))
            wname = f_lm.measureText(name)
            if 420 + wname + 16 + f_lmv.measureText(val) <= 930:
                c.drawString(val, 420 + wname + 16, y - 14, f_lmv, paint(MUTED, a))
            else:
                c.drawString(val, 420, y + 34, f_lmv, paint(MUTED, a))

        # true-scale Earth under the stack (flat ground until the curve shows)
        Re = 6.371e6 * ppm
        mix = max(0.0, min(1.0, (f - 24) / 6))
        gcol = skia.Color(int(20 + (34 - 20) * mix), int(22 + (70 - 22) * mix), int(28 + (138 - 28) * mix))
        if Re > 50000:
            c.drawRect(skia.Rect(0, GROUND_Y, W, H), paint(gcol, vis_a))
            c.drawLine(60, GROUND_Y, W - 60, GROUND_Y, paint(INK, 0.6 * vis_a * (1 - mix), StrokeWidth=3))
        else:
            rr = max(Re, 4.0)
            ecx, ecy = STACK_X, GROUND_Y + rr
            c.drawCircle(ecx, ecy, rr + 6, paint(skia.Color(90, 160, 255), 0.35 * vis_a,
                         MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, max(3, min(18, rr * 0.08)))))
            sh = skia.GradientShader.MakeRadial(skia.Point(ecx - rr * 0.3, ecy - rr * 0.4), rr * 1.3,
                                                [skia.Color(58, 116, 205), skia.Color(16, 38, 84)])
            c.drawCircle(ecx, ecy, rr, skia.Paint(AntiAlias=True, Shader=sh, Alphaf=vis_a))
            if rr < 140:
                c.drawString("Earth", ecx + rr + 18, ecy + 12, f_lm, paint(skia.Color(120, 175, 255), vis_a))
        # Moon and Sun as true-scale dots on their lines
        for nm, dist, rad, colr in (("The Moon", 384_400e3, 1_737e3, skia.Color(200, 200, 205)),
                                    ("The Sun", 149.6e9, 696e6, skia.Color(255, 196, 60))):
            yy = GROUND_Y - dist * ppm
            if VIEW_TOP < yy < GROUND_Y - 130:
                rpx = max(rad * ppm, 6.0)
                c.drawCircle(360, yy, rpx + 8, paint(colr, 0.5 * vis_a, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8)))
                c.drawCircle(360, yy, rpx, paint(colr, vis_a))

        # the stack (thins to a line once Earth is smaller than it)
        sw = STACK_W if Re > 200 else max(8.0, min(STACK_W, Re * 0.6))
        sx0, sx1 = STACK_X - sw / 2, STACK_X + sw / 2
        top = TOP_Y
        body = skia.Rect(sx0, top, sx1, GROUND_Y)
        shader = skia.GradientShader.MakeLinear([skia.Point(sx0, 0), skia.Point(sx1, 0)],
                                                [skia.Color(250, 247, 240), skia.Color(205, 200, 190)])
        glow_a = 0.5 * max(0.0, 1 - (t - flash_t) / 0.25) * vis_a
        if glow_a > 0:
            c.drawRect(body.makeOutset(10, 10), paint(ORANGE, glow_a, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16)))
        c.drawRect(body, skia.Paint(AntiAlias=True, Shader=shader, Alphaf=vis_a))
        layers = 2 ** fi
        if layers <= 128:
            sp = (GROUND_Y - top) / layers
            lp = paint(skia.Color(150, 145, 135), 0.55 * vis_a, StrokeWidth=1.2)
            for i in range(1, layers):
                yy = top + i * sp
                c.drawLine(sx0, yy, sx1, yy, lp)
        c.restore()

        # ---- outro
        if kind == "outro":
            a = ease_out((tin - 0.4) / 0.5)
            if a > 0:
                text_center(c, "In real life,", W / 2, 820, font("Bricolage-700", 54), paint(MUTED, a))
                text_center(c, "the record is 12 folds.", W / 2, 900, font("Bricolage-800", 72), paint(INK, a))
            a2 = ease_out((tin - 1.3) / 0.5)
            if a2 > 0:
                text_center(c, "And that took a strip of paper 1.2 km long.", W / 2, 985, font("Bricolage-700", 38), paint(ORANGE, a2))
            a3 = ease_out((tin - 2.1) / 0.5)
            if a3 > 0:
                text_center(c, "@overthought.daily", W / 2, 1120, font("JetBrainsMono-500", 30), paint(MUTED, a3))

        if preview_times:
            surf.makeImageSnapshot().save(f"preview/fold_{F:05d}.png", skia.kPNG)
        else:
            enc.stdin.write(frame_bytes(surf))
            if F % 600 == 0:
                print(f"frame {F}/{total_frames}", flush=True)
    if enc:
        enc.stdin.close(); enc.wait()

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        main(None, os.path.join(tempfile.gettempdir(), "fold_prev.wav"),
             preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
