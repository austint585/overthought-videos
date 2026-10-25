"""Overthought profile picture: a stick-figure head with a tangled thought above it."""
import math, random
import skia

S = 1080
ORANGE = skia.Color(255, 106, 43)
INK = skia.Color(17, 17, 20)

def tangle_path(cx, cy, rx, ry, seed=7, turns=9, steps=2400):
    """One continuous looping line that wanders inside an ellipse, like a knot of yarn."""
    rnd = random.Random(seed)
    # sum of a few slow sinusoids per axis gives organic, overlapping loops
    comps = [(rnd.uniform(0.7, 1.3) * k, rnd.uniform(0, 6.283), 1.0 / k ** 0.9) for k in (1, 2.13, 3.71)]
    compy = [(rnd.uniform(0.7, 1.3) * k, rnd.uniform(0, 6.283), 1.0 / k ** 0.9) for k in (1, 1.87, 3.29)]
    sx = sum(a for _, _, a in comps); sy = sum(a for _, _, a in compy)
    p = skia.Path()
    for i in range(steps + 1):
        t = i / steps * turns * 2 * math.pi
        x = sum(a * math.cos(f * t + ph) for f, ph, a in comps) / sx
        y = sum(a * math.sin(f * t + ph) for f, ph, a in compy) / sy
        X, Y = cx + x * rx, cy + y * ry
        if i == 0:
            p.moveTo(X, Y)
        else:
            p.lineTo(X, Y)
    return p

def render(path, size=S):
    surf = skia.Surface(size, size)
    c = surf.getCanvas()
    c.scale(size / S, size / S)
    c.clear(ORANGE)

    stroke = skia.Paint(AntiAlias=True, Color=INK, Style=skia.Paint.kStroke_Style,
                        StrokeWidth=30, StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)
    fill = skia.Paint(AntiAlias=True, Color=INK)

    # stick figure in a "thinking" pose (hand on chin), cropped by the circle at the bottom
    hx, hy, hr = 450, 715, 102
    c.drawCircle(hx, hy, hr, stroke)
    neck = hy + hr
    sh = neck + 48
    c.drawLine(hx, neck, hx, 1140, stroke)          # body
    c.drawLine(hx, sh, hx - 100, sh + 135, stroke)  # left arm hanging
    arm = skia.Path()                                # right arm bent up to the chin
    arm.moveTo(hx, sh); arm.lineTo(hx + 118, sh + 92); arm.lineTo(hx + 52, neck - 6)
    c.drawPath(arm, stroke)

    # thought-bubble dots rising toward the tangle
    c.drawCircle(552, 570, 16, fill)
    c.drawCircle(603, 510, 24, fill)

    # the overthought: one long tangled line
    thin = skia.Paint(stroke); thin.setStrokeWidth(18)
    c.drawPath(tangle_path(645, 310, 235, 160, seed=11, turns=5), thin)

    surf.makeImageSnapshot().save(path, skia.kPNG)

if __name__ == "__main__":
    import sys
    render(sys.argv[1] if len(sys.argv) > 1 else "pfp.png")
