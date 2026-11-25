"""Game-cutscene UI layer (Nov 24, from the @zeromrrclub reel Austin DMed on Nov 22: "can you figure out how this
style is made"). The picture in that style is AI video (stylized mid-2000s console cutscene, made on Higgsfield); this
file is everything drawn on top of it, which is ours and in code:

  stat_tag      a black panel with a light border floating over a character: a label and a value in pixel type
                ("CONSULTING / $180K" in green, "GARAGE / $0 / AURA oo"); it pops in when the character speaks
  tick          a value that drops on a beat ($180K -> $0): one white flash frame, then red, with a short shake
  caption       the spoken line in Press Start 2P, white with a one-pixel black outline and a hard shadow;
                the punchline in orange
  hook_text     the frame-0 "POV: ..." line in a plain bold sans with a black stroke, like Instagram's own text
  lock_screen   a full-frame phone insert: pixel clock and a notification that drops in (the plot twist shot)
  end_card      black card, orange pixel title, white line, orange call to action

python cutscene_ui.py demo <out_dir> [plate1.png plate2.png ...]   -> stills of every element (plates optional)
"""
import math, os, sys
import skia
from common import W, H, font, typeface, ease_out

PIX = "PressStart2P-400"          # every pixel word: captions, tags, clock, phone card
SANS = "Inter-700"

WHITE = skia.Color(246, 246, 242)
BLACK = skia.Color(10, 10, 12)
PANEL = skia.ColorSetARGB(235, 24, 24, 26)
BORDER = skia.Color(214, 214, 210)
GREEN = skia.Color(72, 214, 92)
RED = skia.Color(232, 64, 56)
YELLOW = skia.Color(240, 196, 48)
ORANGE = skia.Color(255, 150, 36)


def pfont(name, size):
    """Pixel fonts render hard-edged: no anti-aliasing, no subpixel positioning."""
    f = skia.Font(typeface(name), size)
    f.setEdging(skia.Font.Edging.kAlias)
    f.setSubpixel(False)
    return f


def _p(color, alpha=1.0):
    p = skia.Paint(AntiAlias=False, Color=color)
    if alpha < 1.0:
        p.setAlphaf(alpha)
    return p


def outlined(c, s, x, y, f, fill, px, shadow=1, alpha=1.0):
    """Draw text with a one-font-pixel black outline (8 neighbours) and a hard drop shadow, the way game dialogue
    boxes did it. px is the size of one font pixel on screen (font size / 8 for Press Start 2P)."""
    ink = _p(BLACK, alpha)
    if shadow:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                c.drawString(s, x + (dx + shadow) * px, y + (dy + shadow) * px, f, ink)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx or dy:
                c.drawString(s, x + dx * px, y + dy * px, f, ink)
    c.drawString(s, x, y, f, _p(fill, alpha))


def pop_scale(t, t0, dur=0.14):
    """0 before t0, then 0.55 -> 1.12 -> 1.0 over dur: a blunt game-UI pop, not a smooth ease."""
    if t < t0:
        return 0.0
    u = (t - t0) / dur
    if u >= 1:
        return 1.0
    return 0.55 + 0.57 * min(1, u / 0.45) if u < 0.45 else 1.12 - 0.12 * (u - 0.45) / 0.55


def tick(t, t_drop, before, after, color_before=GREEN, color_after=RED):
    """(text, color, shake_px) for a value that drops at t_drop: one white flash frame, then the new value in red."""
    if t < t_drop:
        return before, color_before, 0.0
    d = t - t_drop
    if d < 1 / 30:
        return after, WHITE, 0.0
    shake = 6 * math.sin(d * 90) * max(0.0, 1 - d / 0.2)
    return after, color_after, shake


INFINITY = ["011000110",          # a 9x5 infinity sign drawn as pixels (the pixel fonts have no glyph for it)
            "100101001",
            "100010001",
            "100101001",
            "011000110"]


def draw_infinity(c, x, y_base, px, color):
    rows = INFINITY
    top = y_base - len(rows) * px
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == "1":
                c.drawRect(skia.Rect.MakeXYWH(x + i * px, top + j * px, px, px), _p(color))
    return len(rows[0]) * px


def stat_tag(c, cx, cy, lines, scale=1.0, t=1e9, t0=0.0, shake=0.0):
    """A floating stat panel centred at (cx, cy). lines: [(text, color, size), ...]; sizes are at scale 1 for a
    wide shot (label 24, value 40). A text ending in ' oo' gets a pixel infinity sign. Pops in at t0."""
    k = pop_scale(t, t0)
    if k <= 0:
        return
    rows = []
    for text, color, size in lines:
        size = max(8, round(size * scale / 4) * 4)
        f = pfont(PIX, size)
        inf = text.endswith(" oo")
        s = text[:-3] if inf else text
        w = f.measureText(s) + (size * 0.25 + 9 * size / 8 if inf else 0)
        rows.append((s, color, size, f, w, inf))
    pad_x, pad_y, gap = 22 * scale, 16 * scale, 10 * scale
    bw = max(r[4] for r in rows) + 2 * pad_x
    bh = sum(r[2] for r in rows) + gap * (len(rows) - 1) + 2 * pad_y
    c.save()
    c.translate(cx + shake, cy)
    c.scale(k, k)
    border = max(3, round(4 * scale))
    c.drawRect(skia.Rect.MakeXYWH(-bw / 2 - border, -bh / 2 - border, bw + 2 * border, bh + 2 * border), _p(BORDER))
    c.drawRect(skia.Rect.MakeXYWH(-bw / 2, -bh / 2, bw, bh), _p(PANEL))
    y = -bh / 2 + pad_y
    for s, color, size, f, w, inf in rows:
        y += size
        x = -w / 2
        outlined(c, s, x, y, f, color, size / 8, shadow=0)
        if inf:
            draw_infinity(c, x + f.measureText(s) + size * 0.25, y, size / 8, color)
        y += gap
    c.restore()


def wrap(text, max_chars):
    out, line = [], ""
    for w in text.split():
        if line and len(line) + 1 + len(w) > max_chars:
            out.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        out.append(line)
    return out


def caption(c, text, color=WHITE, size=48, bottom=1300, max_chars=17):
    """The spoken line, centred, last baseline at `bottom` (inside the Reels safe area). Instant on, like a
    dialogue line: the caller decides when it shows."""
    f = pfont(PIX, size)
    lines = wrap(text.upper(), max_chars)
    lh = size * 1.5
    y = bottom - lh * (len(lines) - 1)
    for ln in lines:
        outlined(c, ln, W / 2 - f.measureText(ln) / 2, y, f, color, size / 8)
        y += lh


def hook_text(c, text, y=300, size=58, max_w=900):
    """Frame-0 text in Instagram's own style: bold sans, white, black stroke."""
    f = font(SANS, size)
    words, lines, line = text.split(), [], ""
    for w in words:
        trial = (line + " " + w).strip()
        if line and f.measureText(trial) > max_w:
            lines.append(line)
            line = w
        else:
            line = trial
    lines.append(line)
    stroke = skia.Paint(AntiAlias=True, Color=BLACK, Style=skia.Paint.kStroke_Style, StrokeWidth=size * 0.16,
                        StrokeJoin=skia.Paint.kRound_Join)
    fill = skia.Paint(AntiAlias=True, Color=WHITE)
    for i, ln in enumerate(lines):
        x = W / 2 - f.measureText(ln) / 2
        c.drawString(ln, x, y + i * size * 1.15, f, stroke)
        c.drawString(ln, x, y + i * size * 1.15, f, fill)


def lock_screen(c, t, clock="4:12", day="WEDNESDAY", app="HR", sub="Important update", title="", body="",
                t_note=0.25):
    """Full-frame phone insert: navy gradient, pixel clock, and a notification card that drops in at t_note.
    Placeholder text only: every episode writes its own."""
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)],
                                        [skia.Color(20, 26, 44), skia.Color(36, 46, 74)])
    c.drawPaint(skia.Paint(Shader=sh))
    fc = pfont(PIX, 120)
    outlined(c, clock, W / 2 - fc.measureText(clock) / 2, 520, fc, WHITE, 0, shadow=0)
    fd = pfont(PIX, 24)
    c.drawString(day, W / 2 - fd.measureText(day) / 2, 590, fd, _p(skia.Color(190, 198, 220)))
    if t < t_note:
        return
    u = ease_out((t - t_note) / 0.25)
    x0, x1 = 70, W - 70
    y0 = 760 - (1 - u) * 140
    ft = pfont(PIX, 40)
    tl = wrap(title.upper(), 17)
    fb = pfont(PIX, 24)
    card_h = 130 + len(tl) * 58 + (60 if body else 0) + 30
    alpha = min(1.0, u * 1.5)
    card = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, y0, x1, y0 + card_h), 26, 26)
    c.drawRRect(card, skia.Paint(AntiAlias=True, Color=skia.Color(234, 234, 238), Alphaf=alpha))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x0 + 32, y0 + 30, 52, 52), 10, 10),
                skia.Paint(AntiAlias=True, Color=skia.Color(226, 76, 46), Alphaf=alpha))
    fi = pfont(PIX, 32)
    c.drawString("!", x0 + 58 - fi.measureText("!") / 2, y0 + 72, fi, _p(WHITE, alpha))
    fa = pfont(PIX, 32)
    dark = skia.Color(30, 30, 36)
    c.drawString(app, x0 + 104, y0 + 58, fa, _p(dark, alpha))
    c.drawString(sub, x0 + 104, y0 + 96, pfont(PIX, 20), _p(skia.Color(90, 90, 100), alpha))
    fn = pfont(PIX, 20)
    c.drawString("now", x1 - 36 - fn.measureText("now"), y0 + 58, fn, _p(skia.Color(110, 110, 120), alpha))
    y = y0 + 170
    for ln in tl:
        c.drawString(ln, x0 + 36, y, ft, _p(RED, alpha))
        y += 58
    if body:
        c.drawString(body, x0 + 36, y + 10, fb, _p(dark, alpha))


def search_screen(c, t, query="", source="", title="", body="", t_type=0.7, t_note=0.85):
    """Full-frame phone search: the query types itself into the bar, then an answer card with its source drops in.
    For the 'look it up' beat (Nov 24, the reel-educated chad): every fact on it must come from the episode pack."""
    c.drawPaint(skia.Paint(Color=skia.Color(244, 244, 247)))
    x0, x1 = 60, W - 60
    bar = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, 300, x1, 400), 50, 50)
    c.drawRRect(bar, skia.Paint(AntiAlias=True, Color=skia.Color(255, 255, 255)))
    c.drawRRect(bar, skia.Paint(AntiAlias=True, Color=skia.Color(200, 200, 210), Style=skia.Paint.kStroke_Style,
                                StrokeWidth=4))
    ring = skia.Paint(AntiAlias=True, Color=skia.Color(120, 120, 130), Style=skia.Paint.kStroke_Style, StrokeWidth=6)
    c.drawCircle(x0 + 62, 342, 17, ring)
    c.drawLine(x0 + 74, 354, x0 + 88, 368, ring)
    fq = pfont(PIX, 26)
    n = int(len(query) * min(1.0, max(0.0, t / t_type)))
    typed = query[:n] + ("_" if t < t_type + 0.3 and int(t * 6) % 2 == 0 else "")
    c.drawString(typed, x0 + 112, 362, fq, _p(skia.Color(30, 30, 36)))
    if t < t_note:
        return
    u = ease_out((t - t_note) / 0.25)
    alpha = min(1.0, u * 1.5)
    y0 = 470 + (1 - u) * 80
    ft = pfont(PIX, 38)
    tl = wrap(title, 18)
    fb = pfont(PIX, 26)
    bl = wrap(body, 26) if body else []
    card_h = 120 + len(tl) * 56 + len(bl) * 40 + 40
    card = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, y0, x1, y0 + card_h), 24, 24)
    c.drawRRect(card, skia.Paint(AntiAlias=True, Color=skia.Color(255, 255, 255), Alphaf=alpha))
    c.drawRRect(card, skia.Paint(AntiAlias=True, Color=skia.Color(215, 215, 222), Alphaf=alpha,
                                 Style=skia.Paint.kStroke_Style, StrokeWidth=3))
    c.drawString(source, x0 + 36, y0 + 64, pfont(PIX, 22), _p(skia.Color(40, 110, 60), alpha))
    y = y0 + 132
    for ln in tl:
        c.drawString(ln, x0 + 36, y, ft, _p(skia.Color(26, 26, 32), alpha))
        y += 56
    y += 10
    for ln in bl:
        c.drawString(ln, x0 + 36, y, fb, _p(skia.Color(80, 80, 92), alpha))
        y += 40


def end_card(c, title="PART 2", line="overthought.daily", cta="FOLLOW SO YOU SEE IT"):
    c.drawPaint(skia.Paint(Color=skia.Color(8, 8, 10)))
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H * 0.46), 900,
                                        [skia.Color(28, 26, 24), skia.Color(8, 8, 10)])
    c.drawPaint(skia.Paint(Shader=sh))
    f1 = pfont(PIX, 64)
    outlined(c, title, W / 2 - f1.measureText(title) / 2, 520, f1, ORANGE, 8, shadow=0)
    f2 = pfont(PIX, 36)
    c.drawString(line, W / 2 - f2.measureText(line) / 2, 1210, f2, _p(WHITE))
    f3 = pfont(PIX, 40)
    c.drawString(cta, W / 2 - f3.measureText(cta) / 2, 1300, f3, _p(ORANGE))


# ---------------------------------------------------------------- demo stills

def _plate(c, path):
    if path and os.path.exists(path):
        img = skia.Image.open(path)
        s = max(W / img.width(), H / img.height())
        w, h = img.width() * s, img.height() * s
        c.drawImageRect(img, skia.Rect.MakeXYWH((W - w) / 2, (H - h) / 2, w, h),
                        skia.SamplingOptions(skia.FilterMode.kLinear))
    else:
        sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, H)],
                                            [skia.Color(196, 158, 112), skia.Color(92, 62, 40)])
        c.drawPaint(skia.Paint(Shader=sh))


def demo(out_dir, plates):
    os.makedirs(out_dir, exist_ok=True)
    plates = plates + [None] * 5
    shots = []

    def wide(c, t):                                   # the three-shot: jobs pop in as each one talks
        _plate(c, plates[0])
        hook_text(c, "POV: the reunion goes around the table")
        stat_tag(c, 200, 560, [("DENTIST", WHITE, 24), ("$190K", GREEN, 40)], t=t, t0=0.0)
        stat_tag(c, 540, 520, [("SALES", WHITE, 24), ("$140K", GREEN, 40)], t=t, t0=0.0)
        stat_tag(c, 870, 560, [("REAL", WHITE, 24), ("ESTATE", WHITE, 24), ("$210K", GREEN, 40)], t=t, t0=0.0)
        caption(c, "Placeholder line. And you?")
    shots.append(("1_wide_tags", wide, 1.0))

    def single(c, t):                                 # the close single: bigger tag, punchline in orange
        _plate(c, plates[1])
        stat_tag(c, 760, 470, [("TIKTOK", WHITE, 40), ("$0", GREEN, 72), ("AURA oo", YELLOW, 48)], scale=1.0,
                 t=t, t0=0.0)
        caption(c, "Placeholder punchline.", color=ORANGE)
    shots.append(("2_single_punch", single, 1.0))

    def drop(c, t):                                   # after the twist: every salary ticks to $0
        _plate(c, plates[2])
        for i, (cx, cy, lab) in enumerate([(200, 560, ["DENTIST"]), (540, 520, ["SALES"]),
                                          (870, 560, ["REAL", "ESTATE"])]):
            s, col, shk = tick(t, 0.2 + 0.15 * i, ["$190K", "$140K", "$210K"][i], "$0")
            stat_tag(c, cx, cy, [(l, WHITE, 24) for l in lab] + [(s, col, 40)], shake=shk)
        caption(c, "...a reply line.")
    shots.append(("3_tick_to_zero", drop, 1.0))

    shots.append(("4_lock_screen", lambda c, t: lock_screen(
        c, t, app="BANK", sub="Account alert", title="Payment declined.", body="Tap to review."), 1.0))
    shots.append(("5_end_card", lambda c, t: end_card(c), 1.0))

    for name, fn, t in shots:
        surf = skia.Surface(W, H)
        fn(surf.getCanvas(), t)
        surf.makeImageSnapshot().save(os.path.join(out_dir, name + ".png"), skia.kPNG)
        print(os.path.join(out_dir, name + ".png"))


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "demo":
        demo(sys.argv[2], sys.argv[3:])
    else:
        print(__doc__)
