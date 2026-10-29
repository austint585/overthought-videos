"""'How does tap-to-pay actually work?' narrated explainer with word-by-word captions."""
import math, os, re, sys, tempfile
import numpy as np
import skia
from common import *

VOICE = "am_adam"
SPEED = 1.05
TTS_DIR = os.environ.get("OT_TTS_DIR", os.path.join(ROOT, "vendor", "tts"))

# Each sentence: display text with *keyword* marks and {spoken form} after tokens that read differently.
# {/IPA/} instead gives the exact phonemes, for words the voice gets wrong in context: Lives{/lˈɪvz/} (the verb).
SCRIPT = [
    ("A", "You tap your *phone,* and a *second* later, you've paid."),
    ("B", "But your phone doesn't need the *internet* for this."),
    ("B", "It talks to the reader *directly,* through a *magnetic* field."),
    ("C", "Inside the reader is a *coil* of wire."),
    ("C", "Current flips through it *13.56{thirteen point five six} million* times a second, making a field that reaches about *4{four} centimeters.*"),
    ("C", "That's why you have to get so *close.*"),
    ("D", "A plastic card has *no battery.*"),
    ("D", "A coil hidden around its *edge* catches the field, and that's enough power to wake up the *chip.*"),
    ("E", "Your phone has its own coil, but it doesn't send your *card number.*"),
    ("E", "It sends a *stand-in* number, called a *token,* plus a *code* that only works for this one purchase."),
    ("E", "Steal it, and it's *useless.* The next tap makes a *new* code."),
    ("F", "The card network swaps the token for your *real* card, and your bank says *yes.*"),
    ("G", "All of that happens in a *fraction* of a second."),
]
# Words the voice mispronounces everywhere, as Kokoro (espeak) phonemes. Add to this when QA hears a wrong word.
LEXICON = {
    "hypergamy": "haɪpˈɜːɡəmi",          # hy-PUR-guh-mee (espeak says hyper-GAY-mee); Austin, Oct 27
    "schrödinger": "ʃɹˈoʊdɪŋɚ",          # SHROH-ding-er, no hard g
    "schrodinger": "ʃɹˈoʊdɪŋɚ",
}
# Same spelling, two sounds: the run prints how each one came out so the script can be checked before rendering.
HETERONYMS = {"lives", "live", "read", "lead", "wind", "tear", "close", "use", "bass", "bow", "row", "wound", "minute",
              "object", "present", "record", "content", "desert", "produce", "refuse", "permit", "project", "subject",
              "does", "dove", "excuse", "separate", "estimate", "graduate", "alternate", "invalid", "conduct", "contract",
              "house", "polish", "moped", "sow", "resume", "attribute", "rebel", "console", "entrance", "wound"}
GAP = 0.22          # pause between sentences
LEAD_IN = 0.35      # silence before the first word
TAIL = 2.6          # end card after the last word

# ------------------------------------------------------------------ narration + word timing

def parse(sentence):
    """-> list of dicts: display, spoken, key"""
    sentence = re.sub(r"\{([^}]*)\}", lambda m: "{" + m.group(1).replace(" ", "_") + "}", sentence)
    words = []
    for tok in sentence.split():
        key = "*" in tok
        tok = tok.replace("*", "")
        m = re.match(r"^(.*?)\{(.*?)\}(.*)$", tok)
        ipa = None
        if m and m.group(2).startswith("/"):
            display = spoken = m.group(1) + m.group(3)
            ipa = m.group(2).strip("/")
        elif m:
            display = m.group(1) + m.group(3)
            spoken = m.group(2).replace("_", " ") + m.group(3)
        else:
            display = spoken = tok
        bare = re.sub(r"[^\w']", "", spoken).lower()
        if ipa is None and bare in LEXICON:
            ipa = LEXICON[bare]
        elif ipa is None and bare.endswith("'s") and bare[:-2] in LEXICON:
            ipa = LEXICON[bare[:-2]] + "z"
        words.append({"display": display, "spoken": spoken, "key": key, "ipa": ipa})
    # keyword runs: "*13.56 million*" marks both words
    inside = False
    for w, tok in zip(words, sentence.split()):
        starts, ends = tok.startswith("*"), tok.rstrip(",.?!").endswith("*")
        if starts:
            inside = True
        w["key"] = w["key"] or inside
        if ends:
            inside = False
    return words

def phonemes(words, tok):
    """Kokoro phonemes for a sentence: espeak for runs of ordinary words, the override for LEXICON and {/IPA/} words."""
    out, run = [], []
    def flush():
        if run:
            out.append(tok.phonemize(" ".join(run), "en-us"))
            run.clear()
    for w in words:
        if w.get("ipa"):
            flush()
            out.append(w["ipa"] + re.sub(r"^[\w'-]+", "", w["spoken"]))
        else:
            run.append(w["spoken"])
    flush()
    return " ".join(out)

def pronounce_report(words, tok):
    """Print the phonemes used for overridden words and heteronyms, so a wrong reading shows before the render."""
    for w in words:
        bare = re.sub(r"[^\w']", "", w["spoken"]).lower()
        if w.get("ipa") or bare in HETERONYMS:
            ph = w["ipa"] or tok.phonemize(re.sub(r"[^\w\s'-]", "", w["spoken"]), "en-us") + " (alone; check it in context)"
            print(f"PRONOUNCE {w['display']}: {ph}", flush=True)

def synth_all():
    from kokoro_onnx import Kokoro
    from kokoro_onnx.tokenizer import Tokenizer
    k = Kokoro(f"{TTS_DIR}/kokoro-v1.0.onnx", f"{TTS_DIR}/voices-v1.0.bin")
    tok = Tokenizer()
    sents = []
    for scene, s in SCRIPT:
        words = parse(s)
        pronounce_report(words, tok)
        audio, sr = k.create(phonemes(words, tok), voice=VOICE, speed=SPEED, lang="en-us", is_phonemes=True)
        audio = np.asarray(audio, dtype=np.float64)
        # trim silence
        env = np.abs(audio)
        thr = 0.02 * env.max()
        idx = np.where(env > thr)[0]
        a0, a1 = max(0, idx[0] - int(0.02 * sr)), min(len(audio), idx[-1] + int(0.06 * sr))
        audio = audio[a0:a1]
        # word weights from phoneme counts, with extra weight for punctuation pauses
        weights = []
        for w in words:
            ph = w.get("ipa") or tok.phonemize(re.sub(r"[^\w\s'-]", "", w["spoken"]), "en-us")
            n = len(re.sub(r"[ˈˌː\s]", "", ph)) or 1
            pause = 4.0 if w["spoken"][-1] in ".?!" else (2.6 if w["spoken"][-1] == "," else 0.0)
            weights.append((n, pause))
        total = sum(n + p for n, p in weights)
        dur = len(audio) / sr
        # predicted starts
        starts, acc = [], 0.0
        for n, p in weights:
            starts.append(acc / total * dur)
            acc += n + p
        # snap internal boundaries to nearby energy dips
        hop = int(0.01 * sr)
        rms = np.sqrt(np.convolve(audio ** 2, np.ones(hop) / hop, mode="same"))
        snapped = [starts[0]]
        for s0 in starts[1:]:
            c0 = int(s0 * sr)
            lo, hi = max(0, c0 - int(0.09 * sr)), min(len(rms) - 1, c0 + int(0.09 * sr))
            j = lo + int(np.argmin(rms[lo:hi])) if hi > lo else c0
            snapped.append(max(snapped[-1] + 0.06, j / sr))
        sents.append({"scene": scene, "words": words, "audio": audio, "sr": sr, "starts": snapped, "dur": dur})
    return sents

def layout_timeline(sents):
    t = LEAD_IN
    for s in sents:
        s["t0"] = t
        s["abs_starts"] = [t + x for x in s["starts"]]
        t += s["dur"] + GAP
    return t - GAP

def chunks_for(sent):
    """Split a sentence into caption chunks of up to 4 words, breaking after punctuation."""
    out, cur = [], []
    for i, w in enumerate(sent["words"]):
        cur.append(i)
        if len(cur) >= 4 or w["display"][-1] in ",.?!" or (len(cur) >= 3 and i + 1 < len(sent["words"]) and sent["words"][i + 1]["key"]):
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out

# ------------------------------------------------------------------ drawing kit

GREEN = skia.Color(96, 210, 130)
RED = skia.Color(240, 80, 70)
PANEL = skia.Color(30, 33, 41)
PANEL2 = skia.Color(22, 24, 30)

def rrect(x0, y0, x1, y1, r):
    return skia.RRect.MakeRectXY(skia.Rect(x0, y0, x1, y1), r, r)

def stroke(color, w, alpha=1.0, glow=0):
    p = paint(color, alpha, Style=skia.Paint.kStroke_Style, StrokeWidth=w, StrokeCap=skia.Paint.kRound_Cap,
              StrokeJoin=skia.Paint.kRound_Join)
    if glow:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, glow))
    return p

F_LABEL = None
def label(c, text, x, y, tx, ty, alpha=1.0, color=None):
    """Leader line from (x,y) on the object to a caps label at (tx,ty)."""
    color = color or INK
    c.drawLine(x, y, tx, ty, stroke(color, 2, 0.8 * alpha))
    c.drawCircle(x, y, 5, paint(color, alpha))
    w = F_LABEL.measureText(text)
    left = tx > x
    lx = tx + 10 if left else tx - 10 - w
    lx = max(40, min(lx, W - 40 - w))
    c.drawString(text, lx, ty + 9, F_LABEL, paint(color, alpha))

def contactless_symbol(c, cx, cy, s, alpha, color=INK):
    for k in range(4):
        r = s * (0.35 + 0.22 * k)
        c.drawArc(skia.Rect(cx - r, cy - r, cx + r, cy + r), -40, 80, False, stroke(color, s * 0.09, alpha))

def draw_reader(c, cx, cy, alpha=1.0, cut=0.0, glow=0.0, amount="$4.50"):
    w, h = 360, 470
    x0, y0 = cx - w / 2, cy - h / 2
    c.drawRRect(rrect(x0, y0, x0 + w, y0 + h, 40), paint(PANEL, alpha))
    c.drawRRect(rrect(x0, y0, x0 + w, y0 + h, 40), stroke(INK, 4, 0.8 * alpha))
    # screen
    c.drawRRect(rrect(x0 + 40, y0 + 40, x0 + w - 40, y0 + 175, 18), paint(PANEL2, alpha))
    text_center(c, amount, cx, y0 + 128, font("JetBrainsMono-700", 54), paint(INK, alpha))
    # tap zone
    if cut < 1:
        contactless_symbol(c, cx - 30, cy + 95, 150, alpha * (1 - cut))
    if cut > 0:
        # cutaway: coil spiral under the tap zone
        a = alpha * cut
        for k in range(5):
            m = 26 + k * 16
            c.drawRRect(rrect(x0 + m, cy - 10 + k * 8, x0 + w - m, y0 + h - 30 - k * 8, 20), stroke(ORANGE, 5, a))
        if glow > 0:
            c.drawRRect(rrect(x0 + 26, cy - 10, x0 + w - 26, y0 + h - 30, 20), stroke(ORANGE, 22, 0.5 * a * glow, glow=16))

def draw_phone(c, cx, cy, alpha=1.0, xray=0.0, coil_glow=0.0, scale=1.0, approved=0.0):
    w, h = 300 * scale, 610 * scale
    x0, y0 = cx - w / 2, cy - h / 2
    body_a = alpha * (1 - 0.6 * xray)
    c.drawRRect(rrect(x0, y0, x0 + w, y0 + h, 46 * scale), paint(skia.Color(36, 39, 48), body_a))
    c.drawRRect(rrect(x0, y0, x0 + w, y0 + h, 46 * scale), stroke(INK, 4, 0.85 * alpha))
    c.drawRRect(rrect(x0 + 14 * scale, y0 + 14 * scale, x0 + w - 14 * scale, y0 + h - 14 * scale, 34 * scale),
                paint(PANEL2, body_a))
    c.drawRRect(rrect(cx - 40 * scale, y0 + 30 * scale, cx + 40 * scale, y0 + 54 * scale, 12 * scale), paint(skia.Color(8, 8, 10), body_a))
    if approved > 0:
        a = alpha * approved
        c.drawCircle(cx, cy - 20 * scale, 70 * scale, paint(GREEN, a))
        chk = skia.Path(); chk.moveTo(cx - 32 * scale, cy - 20 * scale); chk.lineTo(cx - 8 * scale, cy + 4 * scale); chk.lineTo(cx + 36 * scale, cy - 44 * scale)
        c.drawPath(chk, stroke(PANEL2, 14 * scale, a))
        text_center(c, "Paid", cx, cy + 110 * scale, font("Bricolage-800", 52 * scale), paint(INK, a))
    if xray > 0:
        a = alpha * xray
        # NFC coil in the upper back, battery below
        for k in range(4):
            m = k * 14 * scale
            c.drawRRect(rrect(x0 + 50 * scale + m, y0 + 90 * scale + m, x0 + w - 50 * scale - m, y0 + 300 * scale - m, 18 * scale),
                        stroke(ORANGE, 4.5 * scale, a))
        if coil_glow > 0:
            c.drawRRect(rrect(x0 + 50 * scale, y0 + 90 * scale, x0 + w - 50 * scale, y0 + 300 * scale, 18 * scale),
                        stroke(ORANGE, 20 * scale, 0.5 * a * coil_glow, glow=14))
        c.drawRRect(rrect(x0 + 60 * scale, y0 + 330 * scale, x0 + w - 60 * scale, y0 + h - 60 * scale, 14 * scale), stroke(MUTED, 3, a))
        text_center(c, "BATTERY", cx, y0 + 470 * scale, font("JetBrainsMono-500", 22 * scale), paint(MUTED, a))
        c.drawRRect(rrect(cx - 34 * scale, y0 + 175 * scale, cx + 34 * scale, y0 + 215 * scale, 6 * scale), paint(skia.Color(200, 170, 90), a))

def card_loop_path(cx, cy, w, h, inset):
    p = skia.Path()
    p.addRRect(rrect(cx - w / 2 + inset, cy - h / 2 + inset, cx + w / 2 - inset, cy + h / 2 - inset, 26))
    return p

def draw_card(c, cx, cy, alpha=1.0, xray=0.0, flow=0.0, t=0.0, chip_on=0.0):
    w, h = 600, 378
    base = skia.GradientShader.MakeLinear([skia.Point(cx - w / 2, cy - h / 2), skia.Point(cx + w / 2, cy + h / 2)],
                                          [skia.Color(48, 58, 92), skia.Color(24, 28, 44)])
    pc = skia.Paint(AntiAlias=True, Shader=base); pc.setAlphaf(alpha * (1 - 0.65 * xray))
    c.drawRRect(rrect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 30), pc)
    c.drawRRect(rrect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 30), stroke(INK, 3, 0.7 * alpha))
    # chip
    chip = skia.Rect(cx - w / 2 + 70, cy - 50, cx - w / 2 + 160, cy + 20)
    if chip_on > 0:
        c.drawRRect(skia.RRect.MakeRectXY(chip.makeOutset(14, 14), 18, 18), paint(skia.Color(255, 210, 90), 0.6 * alpha * chip_on,
                    MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18)))
    c.drawRRect(skia.RRect.MakeRectXY(chip, 12, 12), paint(skia.Color(212, 178, 96), alpha))
    c.drawLine(chip.left(), chip.centerY(), chip.right(), chip.centerY(), stroke(skia.Color(150, 120, 60), 2, alpha))
    c.drawLine(chip.centerX(), chip.top(), chip.centerX(), chip.bottom(), stroke(skia.Color(150, 120, 60), 2, alpha))
    if xray > 0:
        a = alpha * xray
        for inset in (14, 26, 38):
            c.drawPath(card_loop_path(cx, cy, w, h, inset), stroke(ORANGE, 4, a))
        # lead from the antenna to the chip
        c.drawLine(cx - w / 2 + 38, cy - 15, chip.left(), cy - 15, stroke(ORANGE, 4, a))
        if flow > 0:
            path = card_loop_path(cx, cy, w, h, 26)
            pm = skia.PathMeasure(path, True)
            L = pm.getLength()
            for k in range(18):
                d = ((k / 18) + t * 0.35) % 1.0 * L
                pos, _ = pm.getPosTan(d)
                c.drawCircle(pos.x(), pos.y(), 6, paint(skia.Color(255, 220, 150), a * flow))

def field_arcs(c, cx, cy, t, reach, alpha, up=True, spread=70):
    """Expanding arcs of a magnetic field from (cx, cy)."""
    for k in range(6):
        ph = (t * 0.9 + k / 6) % 1.0
        r = 40 + ph * reach
        a = alpha * (1 - ph) * 0.9
        start = (-90 - spread) if up else (90 - spread)
        c.drawArc(skia.Rect(cx - r, cy - r, cx + r, cy + r), start, spread * 2, False, stroke(ORANGE, 5, a))

def pill(c, text, cx, cy, alpha=1.0, color=INK, fill=PANEL, strike=0.0, size=34):
    f = font("JetBrainsMono-700", size)
    w = f.measureText(text) + 56
    h = size + 34
    c.drawRRect(rrect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, h / 2), paint(fill, alpha))
    c.drawRRect(rrect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, h / 2), stroke(color, 3, alpha))
    text_center(c, text, cx, cy + size * 0.36, f, paint(color, alpha))
    if strike > 0:
        c.drawLine(cx - w / 2 - 10, cy, cx - w / 2 - 10 + (w + 20) * strike, cy, stroke(RED, 7, alpha))
    return w

def wifi_icon(c, cx, cy, s, alpha):
    for k in range(3):
        r = s * (0.35 + 0.3 * k)
        c.drawArc(skia.Rect(cx - r, cy - r, cx + r, cy + r), -135, 90, False, stroke(INK, s * 0.1, alpha))
    c.drawCircle(cx, cy, s * 0.08, paint(INK, alpha))

def node(c, cx, cy, title, alpha, hot=0.0):
    w, h = 300, 130
    c.drawRRect(rrect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 22), paint(PANEL, alpha))
    c.drawRRect(rrect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 22), stroke(ORANGE if hot > 0.5 else INK, 4, alpha))
    text_center(c, title, cx, cy + 14, font("JetBrainsMono-700", 34), paint(INK, alpha))

def check_badge(c, cx, cy, r, alpha):
    c.drawCircle(cx, cy, r, paint(GREEN, alpha))
    chk = skia.Path(); chk.moveTo(cx - r * 0.45, cy); chk.lineTo(cx - r * 0.12, cy + r * 0.32); chk.lineTo(cx + r * 0.48, cy - r * 0.35)
    c.drawPath(chk, stroke(PANEL2, r * 0.2, alpha))

# ------------------------------------------------------------------ scenes

def scene_window(sents, scene):
    idx = [i for i, s in enumerate(sents) if s["scene"] == scene]
    return sents[idx[0]]["t0"], sents[idx[-1]]["t0"] + sents[idx[-1]]["dur"] + GAP, idx

def word_time(sents, si, word_sub):
    s = sents[si]
    for i, w in enumerate(s["words"]):
        if word_sub.lower() in w["display"].lower():
            return s["abs_starts"][i]
    return s["t0"]

def draw_scene(c, scene, t, ts, te, sents, idx):
    lt = t - ts
    fade = min(1.0, (t - ts) / 0.3 if scene != "A" else 1.0, (te + 0.3 - t) / 0.3)
    a = max(0.0, fade)
    VC = 1000   # visual center y
    if scene == "A":
        # phone glides to the reader, taps, and pays
        u = ease_io(lt / 1.3)
        draw_reader(c, 540, VC + 160, a)
        px = 540 + 260 * (1 - u)
        py = VC - 250 + 160 * u
        tapped = lt > 1.3
        if tapped:
            field_arcs(c, 540, VC + 110, lt, 220, a * min(1, (lt - 1.3) / 0.2) * max(0, 1 - (lt - 1.9) / 0.6))
        draw_phone(c, px, py, a, approved=ease_out((lt - 1.65) / 0.3) if lt > 1.65 else 0, scale=0.85)
    elif scene == "B":
        t_mag = word_time(sents, idx[1], "talks")
        if t < t_mag:
            wifi_icon(c, 540, VC - 30, 260, a)
            s = ease_out((t - word_time(sents, idx[0], "internet")) / 0.35)
            if s > 0:
                c.drawLine(380, VC - 190, 700, VC + 130, stroke(RED, 14, a * s))
            text_center(c, "NOT NEEDED", 540, VC + 230, font("JetBrainsMono-800", 48), paint(RED, a * s))
        else:
            k = min(1.0, (t - t_mag) / 0.4)
            draw_reader(c, 540, VC + 260, a * k)
            draw_phone(c, 540, VC - 260, a * k, scale=0.7)
            field_arcs(c, 540, VC + 200, lt, 320, a * k)
            mg = word_time(sents, idx[1], "magnetic")
            if t > mg:
                label(c, "MAGNETIC FIELD", 640, VC + 10, 800, VC - 90, a * min(1, (t - mg) / 0.3), ORANGE)
    elif scene == "C":
        t_cur = sents[idx[1]]["t0"]
        t_close = sents[idx[2]]["t0"]
        cut = ease_io((t - word_time(sents, idx[0], "coil")) / 0.5)
        if t < t_cur:
            draw_reader(c, 540, VC + 40, a, cut=cut)
            if cut > 0.5:
                label(c, "COIL OF WIRE", 420, VC + 230, 250, VC + 340, a * min(1, (cut - 0.5) * 2), ORANGE)
        else:
            # pulsing coil and the 13.56 MHz field, then the 4 cm reach
            draw_reader(c, 540, VC + 260, a, cut=1.0, glow=0.6 + 0.4 * math.sin(lt * 10))
            field_arcs(c, 540, VC + 250, lt * 1.6, 330, a)
            tm = word_time(sents, idx[1], "13.56")
            if t > tm:
                aa = a * min(1, (t - tm) / 0.3) * max(0.0, 1 - (t - t_close) / 0.3) if t > t_close else a * min(1, (t - tm) / 0.3)
                text_center(c, "13,560,000", 540, VC - 260, font("JetBrainsMono-800", 92), paint(INK, aa))
                text_center(c, "FLIPS PER SECOND", 540, VC - 205, font("JetBrainsMono-700", 30), paint(MUTED, aa))
            t4 = word_time(sents, idx[1], "4")
            if t > t4:
                aa = a * min(1, (t - t4) / 0.3)
                # 4 cm bracket above the reader face
                y_face, y_reach = VC + 30, VC - 120
                c.drawLine(880, y_face, 880, y_reach, stroke(ORANGE, 4, aa))
                c.drawLine(860, y_face, 900, y_face, stroke(ORANGE, 4, aa))
                c.drawLine(860, y_reach, 900, y_reach, stroke(ORANGE, 4, aa))
                c.drawString("4 cm", 760, (y_face + y_reach) / 2 + 14, font("JetBrainsMono-800", 40), paint(ORANGE, aa))
            if t > t_close:
                u = ease_io((t - t_close) / 0.8)
                draw_phone(c, 540, VC - 380 + 170 * u, a, scale=0.55, coil_glow=u)
    elif scene == "D":
        t2 = sents[idx[1]]["t0"]
        xr = ease_io((t - t2) / 0.5) if t > t2 else 0.0
        flow = ease_io((t - word_time(sents, idx[1], "catches")) / 0.4)
        chip_on = ease_out((t - word_time(sents, idx[1], "chip")) / 0.3)
        draw_card(c, 540, VC, a, xray=xr, flow=flow, t=lt, chip_on=chip_on)
        if t < t2 + 0.2:
            # no battery
            bx, by = 540, VC - 330
            c.drawRRect(rrect(bx - 70, by - 36, bx + 60, by + 36, 10), stroke(INK, 5, a))
            c.drawRect(skia.Rect(bx + 60, by - 14, bx + 74, by + 14), paint(INK, a))
            s = ease_out((t - word_time(sents, idx[0], "battery")) / 0.3)
            if s > 0:
                c.drawLine(bx - 100, by + 60, bx + 100, by - 60, stroke(RED, 12, a * s))
        if xr > 0.6:
            label(c, "ANTENNA LOOP", 840, VC - 189 + 26, 900, VC - 330, a * (xr - 0.6) * 2.5, ORANGE)
        if chip_on > 0:
            label(c, "CHIP WAKES UP", 345, VC - 15, 250, VC + 290, a * chip_on, skia.Color(255, 210, 90))
    elif scene == "E":
        t_tok = sents[idx[1]]["t0"]
        t_steal = sents[idx[2]]["t0"]
        draw_phone(c, 300, VC + 60, a, xray=1.0, coil_glow=0.5 + 0.5 * math.sin(lt * 6), scale=0.75)
        label(c, "NFC COIL", 300, VC - 105, 420, VC - 270, a, ORANGE)
        draw_reader(c, 760, VC + 280, a * 0.9, amount="$4.50")
        if t < t_tok:
            s = ease_out((t - word_time(sents, idx[0], "card")) / 0.4)
            pill(c, "4815 •••• •••• 2716", 700, VC - 120, a * min(1, (t - sents[idx[0]]["t0"]) / 0.3), strike=s, size=30)
            if s > 0.6:
                text_center(c, "NEVER SENT", 700, VC - 30, font("JetBrainsMono-800", 38), paint(RED, a * s))
        elif t < t_steal:
            tt = word_time(sents, idx[1], "token")
            tc = word_time(sents, idx[1], "code")
            u1 = ease_io((t - tt) / 0.7)
            u2 = ease_io((t - tc) / 0.7)
            if t > tt - 0.4:
                pill(c, "TOKEN 9271…", 620 + 140 * u1, VC - 200 + 110 * u1, a, color=ORANGE, size=32)
            if t > tc - 0.4:
                pill(c, "CODE A7F3 · 1 USE", 620 + 140 * u2, VC - 60 + 50 * u2, a, color=INK, size=30)
        else:
            tn = word_time(sents, idx[2], "next")
            if t < tn:
                # a copied code gets rejected
                s = ease_out((t - word_time(sents, idx[2], "useless")) / 0.3)
                pill(c, "CODE A7F3 · COPIED", 700, VC - 120, a, color=RED if s > 0.5 else INK, strike=s, size=30)
                if s > 0.5:
                    text_center(c, "REJECTED", 700, VC - 30, font("JetBrainsMono-800", 44), paint(RED, a * s))
            else:
                u = ease_out((t - tn) / 0.4)
                pill(c, "CODE 3QK8 · 1 USE", 700, VC - 120, a * u, color=GREEN, size=30)
                text_center(c, "NEW EVERY TAP", 700, VC - 30, font("JetBrainsMono-800", 40), paint(GREEN, a * u))
    elif scene == "F":
        ys = [VC - 330, VC, VC + 330]
        names = ["READER", "CARD NETWORK", "YOUR BANK"]
        t_real = word_time(sents, idx[0], "real")
        t_yes = word_time(sents, idx[0], "yes")
        for k, (y, nm) in enumerate(zip(ys, names)):
            node(c, 540, y, nm, a * min(1, max(0, (lt - 0.15 * k) / 0.3)))
            if k < 2:
                c.drawLine(540, y + 70, 540, ys[k + 1] - 70, stroke(MUTED, 3, a))
        # token travels down, becomes the real card at the network, then approval comes back up
        u = ease_io((t - ts - 0.3) / max(0.5, t_real - ts - 0.3))
        if t < t_real:
            y = ys[0] + (ys[1] - ys[0]) * u
            pill(c, "TOKEN", 800, y, a, color=ORANGE, size=30)
        elif t < t_yes:
            v = ease_io((t - t_real) / max(0.4, t_yes - t_real - 0.1))
            pill(c, "REAL CARD", 820, ys[1] + (ys[2] - ys[1]) * v, a, color=INK, size=30)
        else:
            v = ease_out((t - t_yes) / 0.5)
            check_badge(c, 820, ys[2] - (ys[2] - ys[0]) * v, 48, a)
            text_center(c, "APPROVED", 820, ys[2] - (ys[2] - ys[0]) * v + 90, font("JetBrainsMono-800", 32), paint(GREEN, a))
    elif scene == "G":
        # the whole chain, sped up, ending on Paid
        draw_reader(c, 540, VC + 200, a)
        draw_phone(c, 540, VC - 220, a, scale=0.7, approved=ease_out((lt - 0.5) / 0.3))
        field_arcs(c, 540, VC + 150, lt * 2, 260, a * max(0, 1 - lt / 1.5))

# ------------------------------------------------------------------ captions

def draw_captions(c, t, sents, chunk_map):
    # find active chunk
    active = None
    for (si, ch, t0, t1) in chunk_map:
        if t0 <= t < t1:
            active = (si, ch, t0, t1)
            break
    if not active:
        return
    si, ch, t0, t1 = active
    s = sents[si]
    words = [s["words"][i] for i in ch]
    starts = [s["abs_starts"][i] for i in ch]
    size = 66
    f = font("Bricolage-800", size)
    space = f.measureText(" ")
    widths = [f.measureText(w["display"]) for w in words]
    total = sum(widths) + space * (len(words) - 1) + 24 * sum(1 for w in words if w["key"])
    while total > 960 and size > 40:
        size -= 4
        f = font("Bricolage-800", size)
        space = f.measureText(" ")
        widths = [f.measureText(w["display"]) for w in words]
        total = sum(widths) + space * (len(words) - 1) + 24 * sum(1 for w in words if w["key"])
    x = W / 2 - total / 2
    y = 330
    for w, wd, st in zip(words, widths, starts):
        pad = 12 if w["key"] else 0
        if t >= st - 0.03:
            age = t - st
            pop = 1.0 + 0.12 * max(0.0, 1 - age / 0.12)
            if w["key"]:
                c.save(); c.translate(x + pad + wd / 2, y - size * 0.35); c.scale(pop, pop); c.translate(-(x + pad + wd / 2), -(y - size * 0.35))
                c.drawRRect(rrect(x, y - size * 0.86, x + wd + 2 * pad, y + size * 0.24, 12), paint(ORANGE))
                c.drawString(w["display"], x + pad, y, f, paint(PANEL2))
                c.restore()
            else:
                c.drawString(w["display"], x, y, f, paint(INK))
        x += wd + 2 * pad + space

CREAM = skia.Color(246, 238, 220)
CAP_INK = skia.Color(28, 26, 30)
CAP_BLUE = skia.Color(38, 108, 235)

def draw_captions_clay(c, t, sents, chunk_map):
    """Captions for the clay look (Oct 28, after the @petersindex reel Austin sent): the current phrase on a cream
    rounded label, slightly tilted, in a rounded bold font, key words in blue."""
    active = next(((si, ch, t0, t1) for (si, ch, t0, t1) in chunk_map if t0 <= t < t1), None)
    if not active:
        return
    si, ch, t0, t1 = active
    s = sents[si]
    words = [s["words"][i] for i in ch]
    starts = [s["abs_starts"][i] for i in ch]
    size = 76
    while True:
        f = font("Fredoka-700", size)
        space = f.measureText(" ")
        widths = [f.measureText(w["display"]) for w in words]
        total = sum(widths) + space * (len(words) - 1)
        if total <= 880 or size <= 44:
            break
        size -= 4
    x = W / 2 - total / 2
    y = 330
    pop = 1.0 + 0.08 * max(0.0, 1 - (t - t0) / 0.15)
    cy = y - size * 0.3
    c.save()
    c.translate(W / 2, cy); c.scale(pop, pop); c.rotate(-1.5 if si % 2 else 1.2); c.translate(-W / 2, -cy)
    c.drawRRect(rrect(x - 34, y - size * 0.86 - 22, x + total + 34, y + size * 0.26 + 22, 28), paint(CREAM))
    for w, wd in zip(words, widths):                    # the whole phrase at once, like the reference
        c.drawString(w["display"], x, y, f, paint(CAP_BLUE if w["key"] else CAP_INK))
        x += wd + space
    c.restore()

def build_chunk_map(sents):
    cm = []
    for si, s in enumerate(sents):
        chs = chunks_for(s)
        for ci, ch in enumerate(chs):
            t0 = s["abs_starts"][ch[0]] - 0.05
            if ci + 1 < len(chs):
                t1 = s["abs_starts"][chs[ci + 1][0]] - 0.05
            else:
                t1 = s["t0"] + s["dur"] + GAP * 0.8
            cm.append((si, ch, t0, t1))
    return cm

# ------------------------------------------------------------------ main

def main(out_mp4, out_wav, preview_times=None):
    global F_LABEL
    F_LABEL = font("JetBrainsMono-700", 28)
    sents = synth_all()
    speech_end = layout_timeline(sents)
    duration = speech_end + TAIL
    chunk_map = build_chunk_map(sents)
    scenes = []
    for sc in "ABCDEFG":
        ts, te, idx = scene_window(sents, sc)
        scenes.append((sc, ts, te, idx))
    print(f"duration {duration:.1f}s", flush=True)

    # ---- audio: voice + bed + sound design
    tr = new_track(duration)
    for s in sents:
        x = s["audio"] / (np.abs(s["audio"]).max() + 1e-9)
        up = np.interp(np.arange(0, len(x) * 2) / 2.0, np.arange(len(x)), x)   # 24k -> 48k
        add(tr, s["t0"], up, 1.0)
    bed = new_track(duration)
    n = len(bed); tt = np.arange(n) / SR
    pad_sig = (np.sin(2 * np.pi * 110 * tt) + 0.5 * np.sin(2 * np.pi * 164.8 * tt) + 0.35 * np.sin(2 * np.pi * 220.5 * tt))
    bed += pad_sig * 0.05 * (0.8 + 0.2 * np.sin(2 * np.pi * 0.2 * tt))
    beat_bed(bed, 0.0, duration - 0.5, bpm=96, gain=0.12, hat_gain=0.04)
    tr += bed * 0.55
    whoosh = noise_burst(0.35, tau=0.12, lp=0.12, seed=21)
    for sc, ts, te, idx in scenes[1:]:
        add(tr, ts - 0.05, whoosh, 0.35)
    beep = tone(1760, 0.16, tau=0.06, harmonics=(1, 0.2))
    a_s = scenes[0][1]
    add(tr, a_s + 1.65, beep, 0.35)
    add(tr, scenes[-1][1] + 0.5, beep, 0.35)
    # data pills and rejections
    e_s = [s for s in scenes if s[0] == "E"][0]
    for word in ("token", "code"):
        add(tr, word_time(sents, e_s[3][1], word), tone(880, 0.12, tau=0.04), 0.25)
    add(tr, word_time(sents, e_s[3][2], "useless"), sweep(220, 110, 0.35, tau=0.15), 0.45)
    f_s = [s for s in scenes if s[0] == "F"][0]
    add(tr, word_time(sents, f_s[3][0], "yes"), beep, 0.35)
    save_wav(tr, out_wav, duration)

    # ---- video
    enc = None if preview_times else open_encoder(out_mp4, out_wav)
    surf = skia.Surface(W, H)
    frames = [int(x * FPS) for x in preview_times] if preview_times else range(int(duration * FPS))
    f_title = font("Bricolage-800", 44)
    for F in frames:
        t = F / FPS
        c = surf.getCanvas()
        background(c, W / 2, 1000, 1200)
        # persistent title so late joiners know the premise
        title_a = 1.0 if t < speech_end + 0.3 else max(0.0, 1 - (t - speech_end - 0.3) / 0.4)
        hook = max(0.0, min(1.0, (3.0 - t) / 0.6))
        col = skia.Color(int(150 + (243 - 150) * hook), int(148 + (239 - 148) * hook), int(142 + (230 - 142) * hook))
        ft = font("Bricolage-800", 44 + 10 * hook)
        text_center(c, "HOW TAP-TO-PAY ACTUALLY WORKS", W / 2, 192, ft, paint(col, title_a))
        for sc, ts, te, idx in scenes:
            if (ts - 0.05 <= t or sc == "A") and t <= te + 0.35:
                draw_scene(c, sc, t, ts, te, sents, idx)
        draw_captions(c, t, sents, chunk_map)
        if t > speech_end + 0.2:
            a = ease_out((t - speech_end - 0.2) / 0.5)
            text_center(c, "Things you use every day,", W / 2, 330, font("Bricolage-800", 60), paint(INK, a))
            text_center(c, "explained.", W / 2, 405, font("Bricolage-800", 60), paint(ORANGE, a))
            text_center(c, "@overthought.daily", W / 2, 1520, font("JetBrainsMono-500", 32), paint(MUTED, a))
        if preview_times:
            surf.makeImageSnapshot().save(f"preview/tap_{F:05d}.png", skia.kPNG)
        else:
            enc.stdin.write(frame_bytes(surf))
    if enc:
        enc.stdin.close(); enc.wait()
    # timing dump for QA
    with open(os.path.join(tempfile.gettempdir(), "tap_timing.txt"), "w") as fh:
        for s in sents:
            fh.write(f"{s['scene']} {s['t0']:.2f} " + " ".join(f"{w['display']}@{t0:.2f}" for w, t0 in zip(s["words"], s["abs_starts"])) + "\n")

if __name__ == "__main__":
    if sys.argv[1] == "preview":
        main(None, os.path.join(tempfile.gettempdir(), "tap_prev.wav"), preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
