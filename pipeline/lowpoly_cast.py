"""Low-poly cast (Nov 26): the chad ("chadlite") and his three friends rebuilt under the six low-poly rules Austin
DMed (@visualizemy_, research_notes/2026-11-26_PS2_Look_With_Claude.md), in Blender instead of three.js.

- Low poly: every body part is one simple shape (chamfered boxes and prisms), flat shaded, about 450 to 500
  triangles a person. Joints are separate rigid parts hung on empties, like a PS1 game: no skinning, no shape keys.
- Tiny textures: everything is painted here in numpy at 64 px or less, nearest-neighbour. A face is one 64 x 64
  square on the front of the head; an expression is another square (eyes x brows x mouth), swapped per frame.
  Shirts, ties, lapels and overall bibs are one 32 x 64 square on the front of the torso.
- The look (270 x 480, wobble, dither, 4x) comes from ps2look.apply/post.
- Same people as the MakeHuman cast (cutscene_chars.py), except the chad: since the evening of Nov 26 he has the
  Matt Hagen (Clayface) look Austin asked for, chin-length wavy dirty-blond hair with curtain bangs, blue-grey eyes,
  light stubble, a dark tee. Then suit (finance: side part, navy suit, orange tie), jacket (big tech: black crop, olive jacket over a red
  plaid shirt) and overalls (the plumber: buzz cut, white tee, denim overalls, work boots).

In Blender:  import lowpoly_cast as LC; p = LC.build("chad"); p.pose("point"); p.face("smug", mouth="open")
Showcase:    blender -b --factory-startup -P lowpoly_cast.py -- out_dir lineup|turnaround|faces|clip [clip.json]
"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def shade(c, k, add=0):
    return tuple(int(max(0, min(255, v * k + add))) for v in c)


def mix(a, b, t):
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


SCLERA = (236, 232, 224)
PUPIL = (18, 20, 30)
MOUTH = (58, 22, 24)
TEETH = (238, 232, 220)

# ------------------------------------------------------------------ the cast (sRGB 0..255)
CAST = {
    # the chad, from Nov 26 evening: Austin asked for "the actor that play matt hagan in clayface" (Tom Rhys Harries),
    # "emphasis on the wavy hair". A look, not a portrait: chin-length wavy dirty-blond hair with curtain bangs off a
    # middle part, blue-grey hooded eyes, a leaner jaw, light stubble, a dark heather tee (his first-look photo).
    "chad": dict(
        skin=(222, 170, 134), lip=(176, 106, 92), stubble=0.16, iris=(92, 126, 150), brow=(96, 70, 44), brow_rows=2,
        eye_rows=2, chin=0.049, jaw=0.072, rest="smirk0",
        head_scale=(1.07, 1.02, 0.87),                   # "not a long face" (Austin): shorter and a bit wider
        hair="wavy", hair_cols=((62, 44, 26), (112, 82, 48), (158, 118, 70), (204, 166, 106)),
        top="tee", cloth=((56, 64, 82), (48, 55, 72), (66, 74, 94)), sleeve="short",
        legs=((42, 55, 86), (52, 67, 100), (34, 44, 70)), shoes=((228, 228, 222), (200, 200, 196), (150, 150, 150)),
        build=dict(shoulder=1.0, waist=1.0, arm=1.0, neck=1.0)),
    "suit": dict(
        skin=(232, 184, 154), lip=(184, 110, 98), stubble=0.12, iris=(96, 62, 38), brow=(58, 38, 24), brow_rows=2,
        eye_rows=3, chin=0.040, jaw=0.064, rest="flat",
        hair="side", hair_cols=((28, 18, 12), (50, 32, 20), (76, 50, 30), (102, 70, 44)),
        top="suit", cloth=((36, 42, 66), (30, 36, 58), (46, 54, 80)), shirt=(234, 234, 230),
        tie=((214, 110, 42), (176, 82, 28)), sleeve="long",
        legs=((36, 42, 66), (30, 36, 58), (46, 54, 80)), shoes=((34, 30, 30), (52, 48, 48), (20, 18, 18)),
        build=dict(shoulder=0.9, waist=0.98, arm=0.86, neck=0.86)),
    "jacket": dict(
        skin=(226, 186, 150), lip=(188, 118, 102), stubble=0.0, iris=(70, 46, 30), brow=(24, 20, 20), brow_rows=2,
        eye_rows=2, chin=0.040, jaw=0.063, rest="flat",
        hair="crop", hair_cols=((12, 10, 12), (24, 20, 22), (38, 34, 36), (56, 50, 52)),
        top="jacket", cloth=((84, 86, 66), (72, 74, 56), (98, 100, 78)),
        shirt=((160, 44, 46), (36, 28, 30), (198, 82, 72)), sleeve="long",
        legs=((74, 76, 82), (64, 66, 72), (88, 90, 96)), shoes=((198, 200, 204), (178, 180, 186), (120, 120, 124)),
        build=dict(shoulder=0.88, waist=0.95, arm=0.84, neck=0.84)),
    "overalls": dict(
        skin=(116, 74, 54), lip=(92, 52, 46), stubble=0.25, iris=(56, 36, 24), brow=(24, 18, 16), brow_rows=2,
        eye_rows=3, chin=0.046, jaw=0.070, rest="flat",
        hair="buzz", hair_cols=((12, 10, 10), (22, 17, 15), (34, 26, 22), (46, 36, 30)),
        top="overalls", cloth=((232, 230, 224), (216, 214, 208), (244, 242, 238)),
        denim=((62, 88, 134), (52, 76, 118), (76, 104, 152)), brass=(204, 170, 84), sleeve="short",
        legs=((62, 88, 134), (52, 76, 118), (76, 104, 152)), shoes=((104, 70, 44), (86, 56, 34), (50, 34, 22)),
        boots=True, build=dict(shoulder=1.04, waist=1.12, arm=1.02, neck=1.1)),
}


def palette(S):
    b = S["skin"]
    hc = S["hair_cols"]
    return dict(skin=b, lt=shade(b, 1.07, 10), sh=shade(b, 0.86), dk=shade(b, 0.7),
                g1=shade(b, 1.03, 2), g2=shade(b, 0.97), lip=S["lip"], lip_lt=mix(S["lip"], shade(b, 1.07, 10), 0.4),
                stub=mix(shade(b, 0.62), hc[1], 0.45), stub_dk=mix(shade(b, 0.5), hc[0], 0.5),
                lid=mix(shade(b, 0.42), S["brow"], 0.5), brow=S["brow"], iris=S["iris"])


# ------------------------------------------------------------------ painting (rows top to bottom)

def canvas(w, h, col):
    return np.tile(np.array(col, dtype=np.float32), (h, w, 1))


def speckle(a, cols, frac, seed, mask=None):
    """Scatter hand-placed-looking pixels of the given shades."""
    r = np.random.default_rng(seed)
    h, w = a.shape[:2]
    pick = r.random((h, w)) < frac
    if mask is not None:
        pick &= mask
    idx = r.integers(0, len(cols), (h, w))
    for i, c in enumerate(cols):
        a[pick & (idx == i)] = c
    return a


def rect(a, x0, y0, x1, y1, col):
    a[max(0, y0):y1 + 1, max(0, x0):x1 + 1] = col


def px(a, x, y, col):
    if 0 <= y < a.shape[0] and 0 <= x < a.shape[1]:
        a[y, x] = col


def hline(a, x0, x1, y, col):
    for x in range(x0, x1 + 1):
        px(a, x, y, col)


EYE_L, EYE_R, EYE_Y = 20, 44, 26       # eye centres on the 64 x 64 face (screen left / right), row of the iris
MOUTH_Y = 50


def _eye(a, P, S, cx, kind, outer):
    """outer = -1 when the outer corner is to the left (screen-left eye)."""
    lid = P["lid"]
    if kind == "closed":
        hline(a, cx - 5, cx + 5, EYE_Y + 1, lid)
        px(a, cx + 6 * outer, EYE_Y, lid)
        return
    if kind == "squint":                                     # laughing: a curved line, cheeks pushed up
        hline(a, cx - 4, cx + 4, EYE_Y, lid)
        px(a, cx - 5, EYE_Y + 1, lid)
        px(a, cx + 5, EYE_Y + 1, lid)
        hline(a, cx - 4, cx + 4, EYE_Y + 2, P["lt"])
        return
    if S["eye_rows"] == 2 and kind == "open":
        kind = "half"
    top = {"open": EYE_Y - 1, "half": EYE_Y, "wide": EYE_Y - 2}[kind]
    bot = EYE_Y + 1 if kind != "wide" else EYE_Y + 2
    rect(a, cx - 4, top, cx + 4, bot, SCLERA)
    px(a, cx + 4 * outer * -1, bot, P["skin"])                # trim the inner lower corner
    rect(a, cx - 1, top, cx + 1, bot, P["iris"])
    px(a, cx, EYE_Y, PUPIL)
    if kind != "half":
        px(a, cx, EYE_Y - 1, PUPIL)
    px(a, cx - 1, top, (250, 250, 250))                       # the highlight
    hline(a, cx - 5, cx + 5, top - 1, lid)                    # upper lid
    px(a, cx + 6 * outer, top - 2, lid)                       # outer corner lifted
    px(a, cx + 5 * outer, top - 2, lid)
    hline(a, cx - 4, cx + 4, bot + 1, P["sh"])                # lower lid shadow


def _brow(a, P, S, cx, kind, outer, side_raise=False):
    base = EYE_Y - 5
    lift = {"low": 0, "up": -3, "down": 0, "raise": -3 if side_raise else 0}[kind]
    for x in range(cx - 6, cx + 7):
        inner = (x - cx) * -outer                              # >0 toward the nose
        y = base + lift
        if kind == "down" and inner > 1:
            y += 2                                            # inner ends pulled down: serious
        if kind == "raise" and side_raise and -inner > 2:
            y -= 1                                            # an arch on the raised one
        if inner > 4 and kind == "low":
            y += 1                                            # heavy, low, straight
        px(a, x, y, P["brow"])
        px(a, x, y + 1, P["brow"])
        if S["brow_rows"] >= 3 and abs(inner) < 4:
            px(a, x, y - 1, P["brow"])


def _mouth(a, P, kind):
    y = MOUTH_Y
    lip, lip_lt = P["lip"], P["lip_lt"]
    if kind in ("smirk0", "smirk", "flat", "smile"):
        hline(a, 25, 39, y, lip)
        hline(a, 27, 37, y + 1, lip_lt)
        if kind in ("smirk0", "smirk"):
            px(a, 40, y - 1, lip)
            px(a, 39, y - 1, lip)
            if kind == "smirk":
                px(a, 41, y - 2, lip)
                px(a, 24, y + 1, lip)
        elif kind == "smile":
            for x in (23, 24, 40, 41):
                px(a, x, y - 1, lip)
        else:
            px(a, 24, y, lip)
            px(a, 40, y, lip)
        return
    if kind == "mbp":
        hline(a, 26, 38, y, lip)
        hline(a, 26, 38, y + 1, lip)
        return
    shapes = {"half": (26, 38, y, y + 1), "open": (26, 38, y - 1, y + 3), "grin": (23, 41, y - 1, y + 3),
              "o": (29, 35, y - 1, y + 4), "ee": (25, 39, y, y + 1)}
    x0, x1, y0, y1 = shapes[kind]
    rect(a, x0, y0, x1, y1, MOUTH)
    hline(a, x0, x1, y0 - 1, lip)
    hline(a, x0, x1, y1 + 1, lip_lt)
    if kind in ("open", "grin", "ee"):
        hline(a, x0 + 1, x1 - 1, y0, TEETH)                   # top teeth
    if kind == "grin":
        px(a, x0 - 1, y0 - 2, lip)
        px(a, x1 + 1, y0 - 2, lip)


def paint_face(S, eyes="open", brows="low", mouth=None, seed=1):
    P = palette(S)
    mouth = mouth or S["rest"]
    a = canvas(64, 64, P["skin"])
    speckle(a, [P["g1"], P["g2"]], 0.10, seed)                # barely-there grain, not freckles
    # shading at the sides and under the cheekbones
    rect(a, 0, 0, 3, 63, P["sh"])
    rect(a, 60, 0, 63, 63, P["sh"])
    for y in range(31, 44):
        for x in list(range(6, 11 - (y - 31) // 4)) + list(range(53 + (y - 31) // 4, 58)):
            px(a, x, y, P["sh"])
    yy, xx = np.mgrid[0:64, 0:64]
    if S["stubble"] > 0:                                      # jaw, chin and upper lip
        jaw = (yy >= 41) & ~((yy >= MOUTH_Y - 2) & (yy <= MOUTH_Y + 2) & (xx >= 24) & (xx <= 40))
        jaw &= ~((yy < 46) & (xx > 12) & (xx < 52) & ~((yy >= 45) & (xx >= 24) & (xx <= 40)))
        speckle(a, [P["stub"], P["stub_dk"], P["sh"]], S["stubble"], seed + 1, jaw)
        speckle(a, [P["stub_dk"]], 0.7 * S["stubble"], seed + 2, (yy >= 58))
    else:
        rect(a, 14, 60, 50, 63, P["sh"])                      # a soft shadow under the jaw line
    # nose: a light ridge, nostrils, a shadow under it
    for y in range(27, 41):
        px(a, 31, y, P["lt"])
        px(a, 33, y, P["sh"])
    hline(a, 28, 36, 42, P["sh"])
    for x in (28, 29, 35, 36):
        px(a, x, 41, P["dk"])
    for cx in (EYE_L, EYE_R):                                 # eye sockets a shade darker
        hline(a, cx - 5, cx + 5, EYE_Y - 3, P["sh"])
    _eye(a, P, S, EYE_L, eyes, -1)
    _eye(a, P, S, EYE_R, eyes, 1)
    _brow(a, P, S, EYE_L, brows, -1)
    _brow(a, P, S, EYE_R, brows, 1, side_raise=True)
    _mouth(a, P, mouth)
    return a


def paint_head_side(S):
    """Sides and back of the head (u: front to back, v: chin to crown), 16 x 16."""
    P = palette(S)
    a = canvas(16, 16, P["skin"])
    speckle(a, [P["sh"]], 0.1, 4)
    if S["stubble"] > 0:
        yy, xx = np.mgrid[0:16, 0:16]
        speckle(a, [P["stub"], P["stub_dk"]], min(0.6, S["stubble"] * 1.2), 5, (yy >= 11) & (xx <= 6))
    return a


def paint_hair(S):
    style, H = S["hair"], S["hair_cols"]
    r = np.random.default_rng(6)
    a = canvas(32, 32, H[1])
    if style == "quiff":                                      # locks run front to back (down the v axis)
        for x in range(32):
            c = H[r.choice([0, 1, 1, 2, 2, 3], p=[0.12, 0.22, 0.2, 0.22, 0.14, 0.1])]
            y0 = r.integers(0, 8)
            a[y0:, x] = c
            a[:y0, x] = H[0]
        speckle(a, [H[0]], 0.08, 7)
    elif style == "side":                                     # a part on his right, combed across to the left
        for y in range(32):
            a[y, 11:] = H[r.choice([0, 1, 1, 2, 3], p=[0.15, 0.3, 0.25, 0.2, 0.1])]
            a[y, :10] = H[r.choice([0, 1, 2], p=[0.3, 0.45, 0.25])]
        a[:, 10] = shade(S["skin"], 0.8)                      # the part line
        speckle(a, [H[0]], 0.1, 7)
    elif style == "wavy":                                     # locks snake along v; roots darker, ends sun-bleached
        for x0 in range(0, 32, 2):
            c = H[r.choice([0, 1, 2, 2, 3], p=[0.16, 0.24, 0.26, 0.2, 0.14])]
            ph = r.uniform(0, 2 * math.pi)
            for y in range(32):
                x = int(round(x0 + 2.2 * math.sin(2 * math.pi * y / 11 + ph)))
                px(a, x % 32, y, c)
                px(a, (x + 1) % 32, y, c)
        a[:6] = a[:6] * 0.8 + np.array(H[0], np.float32) * 0.2
        a[25:] = a[25:] * 0.6 + np.array(H[3], np.float32) * 0.4
        speckle(a, [H[0]], 0.05, 7)
        for y in range(21, 32):                               # the middle part (top projection: x = 0, the front)
            px(a, 16, y, H[0])
    elif style == "crop":                                     # short, textured, a little spiky
        speckle(a, [H[0], H[2], H[3]], 0.45, 7)
    else:                                                     # buzz: scalp showing through
        a = canvas(32, 32, H[0])
        speckle(a, [shade(S["skin"], 0.75), H[2]], 0.3, 7)
    return a


def paint_tile(cols, size, seed, frac=0.35, kind=None):
    a = canvas(size, size, cols[0])
    speckle(a, list(cols[1:]), frac, seed)
    if kind == "jeans":
        for i in range(size):
            px(a, i, (i * 2) % size, cols[1])                  # twill
        a[:, size // 2] = cols[2]                              # a seam
    if kind == "shoe":
        a[size - 4:, :] = cols[2]                              # the sole
        a[size - 5, :] = cols[1]
    return a


def paint_skin(S):
    P = palette(S)
    a = canvas(16, 16, P["skin"])
    return speckle(a, [P["g1"], P["sh"]], 0.15, 8)


TK = 1.12                              # torso length: 12% longer than the first chadlite (Nov 26), less leggy
TORSO_X, TORSO_Z = 0.25, 0.45 * TK     # the torso front square covers x -0.25..0.25, z 0..0.50 (spine space)


def paint_torso_front(S):
    """32 wide x 64 tall, front projection: col 15.5 is the middle of the chest, row 0 the collar line."""
    C = S["cloth"]
    a = canvas(32, 64, C[0])
    speckle(a, [C[1], C[2]], 0.3, 12)
    if S["top"] == "tee":
        hline(a, 11, 20, 3, C[1])                              # a crew neck
        hline(a, 12, 19, 4, C[1])
    elif S["top"] == "suit":
        for y in range(0, 36):                                 # the shirt V and the lapels
            hw = max(0, int(round(6 - y * 6 / 35)))
            if hw:
                a[y, 16 - hw:16 + hw] = S["shirt"]
                px(a, 15 - hw, y, C[2])
                px(a, 16 + hw, y, C[2])
        t0, t1 = S["tie"]
        rect(a, 14, 2, 17, 5, t0)                              # knot
        for y in range(6, 33):
            hw = 1 if y < 28 else (1 if y < 31 else 0)
            a[y, 15 - hw + 1:17 + hw - 1 + 1] = t0
            if y % 5 == 0:
                a[y, 15:17] = t1                               # stripes
        rect(a, 15, 33, 16, 33, t0)
        for y in (40, 50):
            rect(a, 15, y, 16, y, C[1])                        # buttons
        hline(a, 4, 9, 44, C[1])                               # pocket flaps
        hline(a, 22, 27, 44, C[1])
    elif S["top"] == "jacket":
        s0, s1, s2 = S["shirt"]
        sh = canvas(10, 64, s0)
        for y in range(64):
            for x in range(10):
                if y % 4 == 0 or x % 4 == 1:
                    sh[y, x] = s1                              # plaid
                elif (y % 4 == 2) and (x % 4 == 3):
                    sh[y, x] = s2
        a[:, 11:21] = sh
        a[:, 10] = C[1]                                        # zipper edges
        a[:, 21] = C[1]
        hline(a, 9, 22, 0, C[2])                               # collar
        hline(a, 9, 22, 1, C[2])
    elif S["top"] == "overalls":
        D, brass = S["denim"], S["brass"]
        rect(a, 8, 24, 23, 63, D[0])                           # the bib
        speckle(a, [D[1], D[2]], 0.3, 13, mask=(np.mgrid[0:64, 0:32][0] >= 24) & (np.mgrid[0:64, 0:32][1] >= 8)
                & (np.mgrid[0:64, 0:32][1] <= 23))
        for x0 in (8, 20):                                     # straps up to the shoulders
            rect(a, x0, 0, x0 + 3, 23, D[0])
            px(a, x0 + 1, 24, brass)
            px(a, x0 + 2, 24, brass)
        for x in range(12, 20):                                # bib pocket
            px(a, x, 30, D[1])
            px(a, x, 38, D[1])
        for y in range(30, 39):
            px(a, 12, y, D[1])
            px(a, 19, y, D[1])
        hline(a, 11, 20, 3, C[1])                              # the tee's crew neck
    return a


# ------------------------------------------------------------------ Blender side

def _bpy():
    import bpy
    return bpy


def image(name, arr):
    """numpy (rows top to bottom, 0..255 sRGB) -> a Blender image."""
    bpy = _bpy()
    h, w = arr.shape[:2]
    img = bpy.data.images.get(name) or bpy.data.images.new(name, w, h, alpha=False)
    if tuple(img.size) != (w, h):
        img.scale(w, h)
    rgba = np.concatenate([arr[::-1] / 255.0, np.ones((h, w, 1), np.float32)], axis=2)
    img.pixels.foreach_set(rgba.astype(np.float32).ravel())
    img.update()
    return img


def material(name, img, emit=0.0):
    bpy = _bpy()
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bs.inputs["Roughness"].default_value = 1.0
    for key in ("Specular IOR Level", "Specular"):
        if key in bs.inputs:
            bs.inputs[key].default_value = 0.0
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image, tex.interpolation, tex.extension = img, "Closest", "EXTEND"
    if emit:                                                  # a backdrop: its own light only, the sun ignores it
        bs.inputs["Base Color"].default_value = (0, 0, 0, 1)
        nt.links.new(tex.outputs["Color"], bs.inputs["Emission Color"])
        bs.inputs["Emission Strength"].default_value = emit
    else:
        nt.links.new(tex.outputs["Color"], bs.inputs["Base Color"])
    m["tex"] = tex.name
    return m


def ring(hx, hy, z, yoff=0.0, k=0.5, kf=None):
    """A chamfered rectangle (8 points) at height z: half-width hx, half-depth hy, front (-y) chamfer kf."""
    kf = k if kf is None else kf
    return [(-kf * hx, -hy + yoff, z), (kf * hx, -hy + yoff, z), (hx, -k * hy + yoff, z), (hx, k * hy + yoff, z),
            (k * hx, hy + yoff, z), (-k * hx, hy + yoff, z), (-hx, k * hy + yoff, z), (-hx, -k * hy + yoff, z)]


def loft(rings, cap_top=True, cap_bottom=True):
    """Join rings of equal point count with quads; returns a bmesh."""
    import bmesh
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in r] for r in rings]
    n = len(rings[0])
    for a, b in zip(vs, vs[1:]):
        for i in range(n):
            bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    if cap_bottom:
        bm.faces.new(list(reversed(vs[0])))
    if cap_top:
        bm.faces.new(vs[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def box(x0, x1, y0, y1, z0, z1, taper=1.0):
    """A box from z0 to z1; the z1 end is scaled by taper around its centre."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

    def r(z, s):
        return [(cx + (x - cx) * s, cy + (y - cy) * s, z) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    return loft([r(z0, 1.0), r(z1, taper)])


def uv_box(bm, scale):
    """Per face, project along its main axis; scale = texture repeats per metre."""
    uv = bm.loops.layers.uv.verify()
    bm.normal_update()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            co = l.vert.co
            u, v = [(co.y, co.z), (co.x, co.z), (co.x, co.y)][ax]
            l[uv].uv = (u * scale + 0.5, v * scale + 0.5)


def to_object(name, bm, mats, parent=None, loc=(0, 0, 0)):
    bpy = _bpy()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for m in mats:
        me.materials.append(m)
    if parent:
        ob.parent = parent
    ob.location = loc
    return ob


def joint(name, parent, loc):
    bpy = _bpy()
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.05
    bpy.context.scene.collection.objects.link(e)
    if parent:
        e.parent = parent
    e.location = loc
    e.rotation_mode = "XYZ"
    return e


def head_rings(S):
    """z from the chin (0) up, -y is the face: (z, half width, half depth, forward shift, chamfer, front chamfer)."""
    return [
        (0.000, S["chin"], 0.026, -0.064, 0.8, 0.85),     # chin, far forward
        (0.026, S["jaw"], 0.062, -0.028, 0.7, 0.8),       # the jaw angle
        (0.075, 0.074, 0.088, -0.004, 0.55, 0.72),
        (0.118, 0.075, 0.096, 0.000, 0.55, 0.70),         # eyes
        (0.150, 0.074, 0.100, 0.002, 0.55, 0.68),         # brow ridge
        (0.200, 0.068, 0.094, 0.006, 0.55, 0.62),
        (0.240, 0.044, 0.060, 0.010, 0.55, 0.55),         # crown
    ]


FACE_X, FACE_Z = 0.08, 0.20                     # the face square covers x -0.08..0.08 and z 0..0.20
HEAD_OFF = (0, 0.012, -0.035)                   # head mesh origin (the chin) relative to the head joint
# hair shells: (z at the front, z at the back, scale, lift at the front, push forward at the front) per ring
HAIR = {
    "quiff": [(0.180, 0.085, 1.10, 0, 0), (0.218, 0.165, 1.13, 0.018, 0.012), (0.250, 0.222, 0.98, 0.018, -0.004),
              (0.262, 0.240, 0.62, 0.006, -0.02)],
    "side": [(0.182, 0.088, 1.08, 0, 0), (0.220, 0.168, 1.10, 0.006, 0.006), (0.246, 0.222, 0.96, 0.004, 0),
             (0.256, 0.238, 0.6, 0, -0.01)],
    "crop": [(0.170, 0.088, 1.07, 0, 0.006), (0.214, 0.168, 1.08, 0.002, 0.004), (0.244, 0.224, 0.95, 0.004, 0),
             (0.254, 0.238, 0.6, 0.002, 0)],
    "buzz": [(0.186, 0.092, 1.03, 0, 0), (0.222, 0.170, 1.035, 0, 0), (0.242, 0.226, 0.86, 0, 0),
             (0.249, 0.238, 0.5, 0, 0)],
}
HAIR_RING = (0.074, 0.100, 0.002, 0.55, 0.68)   # the brow ring every hair shell is scaled from (hx, hy, yoff, k, kf)


def ring16(hx, hy, yoff, k, kf):
    """ring() with its edges split: 16 (x, y). 1 is the front centre, 5 and 13 the sides, 9 the back centre;
    i and (2 - i) % 16 are mirror pairs."""
    r = ring(hx, hy, 0, yoff, k, kf)
    out = []
    for i in range(8):
        a, b = r[i], r[(i + 1) % 8]
        out += [a[:2], ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)]
    return out


# wavy (the chad since Nov 26 evening): a cap whose front edge is curtain bangs (high at the middle part, down to the
# brows at the outer forehead, past the temples), plus an open skirt from one cheek round the back to the other that
# hangs to the jaw, kinks in and out (the waves) and flicks out at the ends.
WAVY_HEM = {1: 0.190, 2: 0.141, 3: 0.096, 4: 0.088, 5: 0.112, 6: 0.128, 7: 0.13, 8: 0.13, 9: 0.13}
WAVY_TOP = {1: 0.213, 2: 0.200, 3: 0.180, 4: 0.176, 5: 0.180, 6: 0.176, 7: 0.172, 8: 0.168, 9: 0.168}
WAVY_SKIRT = [(None, 1.07), (0.100, 1.16), (0.066, 1.11), (0.036, 1.22)]   # rows: (z, scale); None = under the cap


def wavy_hair():
    """bmesh of the wavy style, in head-mesh space (chin at z 0, face toward -y)."""
    import bmesh
    hx0, hy0, yo0, k0, kf0 = HAIR_RING

    def zmap(table, i):
        return table[i] if i in table else table[(2 - i) % 16]

    def cap_ring(s, z_of, lump=0.0):
        pts = ring16(hx0 * s, hy0 * s, yo0, k0, kf0)
        out = []
        for i, (x, y) in enumerate(pts):
            t = (y - yo0 + hy0 * s) / (2 * hy0 * s)
            m = 1.0 if i in (0, 1, 2) else 1 + lump * (1 if i % 2 else -1)    # lumps: tousled, not a helmet
            out.append((x * m, yo0 + (y - yo0) * m, z_of(i, t)))
        return out
    rings = [cap_ring(1.09, lambda i, t: zmap(WAVY_HEM, i)),
             cap_ring(1.14, lambda i, t: zmap(WAVY_TOP, i), 0.03),
             cap_ring(1.0, lambda i, t: 0.245 - 0.017 * t, 0.02),
             cap_ring(0.6, lambda i, t: 0.259 - 0.013 * t)]
    bm = loft(rings, cap_bottom=False)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for l in f.loops:
            co = l.vert.co
            l[uv].uv = ((co.x + 0.09) / 0.18, (co.y + 0.12) / 0.24)
    cols = list(range(3, 16))                                # temple (+x) round the back to temple (-x)
    grid = []
    for row, (z, s) in enumerate(WAVY_SKIRT):
        pts = ring16(hx0 * s, hy0 * s, yo0, k0, kf0)
        line = []
        for c, i in enumerate(cols):
            x, y = pts[i]
            wave = 0.0 if row == 0 else (0.035 if (c + row) % 2 else -0.025)
            x, y = x * (1 + wave), yo0 + (y - yo0) * (1 + wave)
            if y > yo0 and row >= 2:                         # the back falls onto the nape, not straight down
                y = yo0 + (y - yo0) * (0.86 if row == 2 else 0.8)
            zz = zmap(WAVY_HEM, i) + 0.02 if z is None else z
            if row == 3:
                zz += 0.016 if c % 2 else 0.0                 # uneven tips
                if c in (0, len(cols) - 1):
                    zz += 0.014                               # the front ends stop at the jaw corner
            line.append(bm.verts.new((x, y, zz)))
        grid.append(line)
    for r0, r1 in zip(grid, grid[1:]):
        for c in range(len(cols) - 1):
            f = bm.faces.new((r0[c], r0[c + 1], r1[c + 1], r1[c]))
            for l in f.loops:
                ci = c if l.vert in (r0[c], r1[c]) else c + 1
                l[uv].uv = (0.02 + 0.43 * ci / (len(cols) - 1), (l.vert.co.z - 0.02) / 0.2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


class Person:
    pass


def build(who, x=0.0, y=0.0, rot_z=0.0, name=None):
    """Builds one of CAST standing at (x, y), facing -y turned by rot_z."""
    import bmesh
    from mathutils import Vector
    S = CAST[who]
    name = name or who
    B = S["build"]
    p = Person()
    p.who, p.name, p.S, p.faces = who, name, S, {}
    shoe_kind = "shoe"
    M = {"face": material(f"{name}_face", image(f"{name}_face", paint_face(S))),
         "head": material(f"{name}_headside", image(f"{name}_headside", paint_head_side(S))),
         "hair": material(f"{name}_hair", image(f"{name}_hair", paint_hair(S))),
         "skin": material(f"{name}_skin", image(f"{name}_skin", paint_skin(S))),
         "top": material(f"{name}_top", image(f"{name}_top", paint_tile(S["cloth"], 32, 12))),
         "front": material(f"{name}_front", image(f"{name}_front", paint_torso_front(S))),
         "legs": material(f"{name}_legs", image(f"{name}_legs", paint_tile(S["legs"], 32, 13, 0.2, "jeans"))),
         "shoe": material(f"{name}_shoe", image(f"{name}_shoe", paint_tile(S["shoes"], 16, 14, 0.1, shoe_kind)))}
    p.mats = M
    p.face_tex = M["face"].node_tree.nodes[M["face"]["tex"]]

    J = {}
    J["root"] = joint(f"{name}.root", None, (x, y, 0))
    J["root"].rotation_euler = (0, 0, rot_z)
    J["pelvis"] = joint(f"{name}.pelvis", J["root"], (0, 0, 0.96))
    J["spine"] = joint(f"{name}.spine", J["pelvis"], (0, 0, 0.06))
    J["neck"] = joint(f"{name}.neck", J["spine"], (0, 0.01, 0.445 * TK))
    J["head"] = joint(f"{name}.head", J["neck"], (0, 0, 0.09))
    if S.get("head_scale"):                                  # head, ears and hair all hang on this joint
        J["head"].scale = S["head_scale"]
    sw = 0.205 * B["shoulder"]
    for s, sx in (("L", 1), ("R", -1)):
        J[f"shoulder{s}"] = joint(f"{name}.shoulder{s}", J["spine"], (sw * sx, 0.01, 0.39 * TK))
        J[f"elbow{s}"] = joint(f"{name}.elbow{s}", J[f"shoulder{s}"], (0, 0, -0.29))
        J[f"wrist{s}"] = joint(f"{name}.wrist{s}", J[f"elbow{s}"], (0, 0, -0.26))
        J[f"hip{s}"] = joint(f"{name}.hip{s}", J["pelvis"], (0.088 * sx * B["waist"], 0, -0.04))
        J[f"knee{s}"] = joint(f"{name}.knee{s}", J[f"hip{s}"], (0, 0, -0.43))
        J[f"ankle{s}"] = joint(f"{name}.ankle{s}", J[f"knee{s}"], (0, 0, -0.42))
    p.J = J
    p.rest = {k: (tuple(e.location), tuple(e.rotation_euler)) for k, e in J.items()}
    parts = []

    # head: front faces take the face square (front projection), the rest the side texture (side projection)
    bm = loft([ring(hx, hy, z, yo, k, kf) for z, hx, hy, yo, k, kf in head_rings(S)])
    nv = [bm.verts.new(q) for q in ((-0.011, -0.091, 0.072), (0.011, -0.091, 0.072), (0.0, -0.110, 0.077),
                                    (0.0, -0.095, 0.116))]
    nose = {bm.faces.new(t) for t in ((nv[0], nv[1], nv[2]), (nv[0], nv[2], nv[3]), (nv[2], nv[1], nv[3]))}
    bm.normal_update()
    base = Vector((0.0, -0.092, 0.09))
    for f in nose:                                           # point the nose's three faces outward
        if f.normal.dot(f.calc_center_median() - base) < 0:
            f.normal_flip()
    bm.normal_update()
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        front = f.normal.y < -0.42 or f in nose
        f.material_index = 0 if front else 1
        for l in f.loops:
            co = l.vert.co
            if front:
                l[uv].uv = ((co.x + FACE_X) / (2 * FACE_X), co.z / FACE_Z)
            else:
                l[uv].uv = ((co.y + 0.11) / 0.22, co.z / 0.25)
    parts.append(to_object(f"{name}.head_mesh", bm, [M["face"], M["head"]], J["head"], HEAD_OFF))
    for sx in (1, -1):                                       # ears
        bm = box(-0.008, 0.008, -0.02, 0.02, 0.07, 0.13, 0.9)
        uv_box(bm, 2.0)
        parts.append(to_object(f"{name}.ear", bm, [M["head"]], J["head"], (0.077 * sx, 0.03, -0.035)))
    # hair: a shell over the top of the head, low at the back, shaped per style at the front
    hx0, hy0, yo0, k0, kf0 = HAIR_RING

    def hair_ring(z_front, z_back, s, lift=0.0, fwd=0.0):
        pts = []
        for (px_, py_, _) in ring(hx0 * s, hy0 * s, 0, yo0, k0, kf0):
            t = (py_ - (-hy0 * s)) / (2 * hy0 * s)              # 0 front .. 1 back
            front = 1.0 - t
            pts.append((px_, py_ - fwd * front, z_front + (z_back - z_front) * t + lift * front ** 2))
        return pts
    if S["hair"] == "wavy":
        bm = wavy_hair()
    else:
        bm = loft([hair_ring(*r) for r in HAIR[S["hair"]]], cap_bottom=False)
        uv = bm.loops.layers.uv.verify()
        for f in bm.faces:
            for l in f.loops:
                co = l.vert.co
                l[uv].uv = ((co.x + 0.09) / 0.18, (co.y + 0.12) / 0.24)
    parts.append(to_object(f"{name}.hair", bm, [M["hair"]], J["head"], HEAD_OFF))

    nk = B["neck"]                                           # neck: six sides
    bm = loft([[(0.064 * nk * math.cos(a), 0.058 * nk * math.sin(a) + 0.005, z) for a in
                [i * math.pi / 3 + math.pi / 6 for i in range(6)]] for z in (-0.04, 0.10)], False, False)
    uv_box(bm, 4.0)
    parts.append(to_object(f"{name}.neck_mesh", bm, [M["skin"]], J["neck"]))
    # torso: V-taper; front faces take the front square (shirt, tie, bib), the rest the cloth tile
    sh, wa = B["shoulder"], B["waist"]
    bm = loft([ring(0.150 * wa, 0.098 * wa, 0.00, 0.0, 0.6), ring(0.168 * wa, 0.106 * wa, 0.14 * TK, 0.0, 0.6),
               ring(0.205 * sh, 0.118, 0.28 * TK, -0.004, 0.55), ring(0.228 * sh, 0.112, 0.38 * TK, 0.004, 0.5),
               ring(0.115 * nk, 0.075, 0.45 * TK, 0.01, 0.55)])
    uv_box(bm, 3.0)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        if f.normal.y < -0.45:
            f.material_index = 1
            for l in f.loops:
                co = l.vert.co
                l[uv].uv = ((co.x + TORSO_X) / (2 * TORSO_X), co.z / TORSO_Z)
    parts.append(to_object(f"{name}.torso", bm, [M["top"], M["front"]], J["spine"]))
    # pelvis: short, so the thighs read as two legs right below the belt
    bm = loft([ring(0.118 * wa, 0.084 * wa, -0.07, 0.0, 0.6), ring(0.150 * wa, 0.096 * wa, 0.07, 0.0, 0.6)])
    uv_box(bm, 3.0)
    parts.append(to_object(f"{name}.pelvis_mesh", bm, [M["legs"]], J["pelvis"]))
    ar = B["arm"]
    long_sleeve = S["sleeve"] == "long"
    for s, sx in (("L", 1), ("R", -1)):
        bm = box(-0.062 * ar, 0.062 * ar, -0.058 * ar, 0.058 * ar, -0.14, 0.03, 0.95)
        uv_box(bm, 3.0)
        parts.append(to_object(f"{name}.sleeve{s}", bm, [M["top"]], J[f"shoulder{s}"]))
        bm = box(-0.056 * ar, 0.056 * ar, -0.056 * ar, 0.056 * ar, -0.29, -0.13, 0.9)
        uv_box(bm, 4.0)
        parts.append(to_object(f"{name}.upperarm{s}", bm, [M["top"] if long_sleeve else M["skin"]],
                               J[f"shoulder{s}"]))
        bm = box(-0.047 * ar, 0.047 * ar, -0.048 * ar, 0.048 * ar, -0.26, 0.0)
        for v in bm.verts:                                     # forearm tapers to the wrist
            if v.co.z < -0.1:
                v.co.x *= 0.78
                v.co.y *= 0.82
        uv_box(bm, 4.0)
        parts.append(to_object(f"{name}.forearm{s}", bm, [M["top"] if long_sleeve else M["skin"]],
                               J[f"elbow{s}"]))
        bm = box(-0.024, 0.024, -0.046, 0.046, -0.10, 0.0, 0.85)
        uv_box(bm, 4.0)
        parts.append(to_object(f"{name}.hand{s}", bm, [M["skin"]], J[f"wrist{s}"]))
        bm = box(-0.054 * wa, 0.070 * wa, -0.078, 0.078, -0.44, 0.02, 0.74)   # less on the inside: a crotch gap
        if sx < 0:
            for v in bm.verts:
                v.co.x = -v.co.x
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
        uv_box(bm, 3.0)
        parts.append(to_object(f"{name}.thigh{s}", bm, [M["legs"]], J[f"hip{s}"]))
        bm = box(-0.056, 0.056, -0.06, 0.06, -0.42, 0.0, 0.86)
        uv_box(bm, 3.0)
        parts.append(to_object(f"{name}.shin{s}", bm, [M["legs"]], J[f"knee{s}"]))
        top = 0.04 if S.get("boots") else 0.0                  # boots come up over the ankle
        bm = box(-0.054, 0.054, -0.17, 0.07, -0.075, top, 1.0)
        for v in bm.verts:                                     # toe box lower than the heel
            if v.co.y < -0.08 and v.co.z > -0.02:
                v.co.z = min(v.co.z, 0.0) - 0.03
        uv = bm.loops.layers.uv.verify()
        bm.normal_update()
        for f in bm.faces:
            for l in f.loops:
                co = l.vert.co
                l[uv].uv = ((co.y + 0.17) / 0.24, (co.z + 0.075) / (0.075 + top))
        parts.append(to_object(f"{name}.shoe{s}", bm, [M["shoe"]], J[f"ankle{s}"]))
    p.parts = parts
    p.tris = sum(sum(len(q.vertices) - 2 for q in o.data.polygons) for o in parts)
    p.pose = lambda pose, w=1.0, **kw: set_pose(p, pose, w, **kw)
    p.face = lambda e, mouth=None, eyes=None: set_face(p, e, mouth, eyes)
    return p


def head_world(p):
    """The middle of the head (about eye height), in world space."""
    from mathutils import Vector
    _bpy().context.view_layer.update()
    return p.J["head"].matrix_world @ Vector((HEAD_OFF[0], HEAD_OFF[1], HEAD_OFF[2] + 0.12))


def forward(p):
    from mathutils import Vector
    _bpy().context.view_layer.update()
    return (p.J["root"].matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()


# ------------------------------------------------------------------ faces and poses

EXPR = {  # name: (eyes, brows, mouth); mouth None = the person's own resting mouth
    "neutral": ("open", "low", None),
    "chad": ("open", "low", "smirk0"),
    "smile": ("open", "low", "smile"),
    "smirk": ("open", "low", "smirk"),
    "smug": ("half", "raise", "smirk"),
    "laugh": ("squint", "up", "grin"),
    "shock": ("wide", "up", "o"),
    "serious": ("open", "down", "flat"),
}
TALK = {"aa": "open", "oh": "o", "ee": "ee", "mbp": "mbp"}


def face_key(p, expr, mouth=None, eyes=None):
    e, b, m = EXPR.get(expr, EXPR["neutral"])
    return eyes or e, b, mouth or m or p.S["rest"]


def set_face(p, expr, mouth=None, eyes=None):
    e, b, m = face_key(p, expr, mouth, eyes)
    key = f"{e}|{b}|{m}"
    if key not in p.faces:
        p.faces[key] = image(f"{p.name}_face_{e}_{b}_{m}", paint_face(p.S, e, b, m))
    p.face_tex.image = p.faces[key]


D = math.radians
SEAT_PELVIS = 0.54
# joint: Euler degrees (x, y, z) in the parent's space. Arm and leg joints are written as if for his LEFT side (+x):
# x swings the limb forward (negative) or back, y swings it out (negative) or in, z twists. Every "R" entry is
# mirrored (y and z flipped); with "sym" the right side copies the left where it isn't given. spine/neck x > 0 leans
# forward / nods down. "lift" raises both shoulders (m). "seated" bends the legs onto a seat. Missing joints rest.
POSES = {
    "stand": {"sym": 1, "shoulderL": (0, -6, 0), "elbowL": (-8, 0, 0)},
    "hips": {"sym": 1, "shoulderL": (8, -38, 0), "elbowL": (-30, 85, 0), "spine": (-3, 0, 0), "neck": (-4, 0, 0)},
    "crossed": {"shoulderL": (-28, -12, 0), "elbowL": (-100, 0, -68), "shoulderR": (-26, -10, 0),
                "elbowR": (-92, 0, -72), "spine": (-4, 0, 0), "neck": (-6, 0, 0)},
    "point": {"shoulderR": (-82, -4, 0), "elbowR": (-6, 0, 0), "shoulderL": (0, -6, 0), "elbowL": (-10, 0, 0),
              "spine": (4, 0, -6), "neck": (2, 0, 4)},
    "shrug": {"sym": 1, "shoulderL": (-10, -22, 0), "elbowL": (-75, 0, 35), "wristL": (0, 40, 0),
              "neck": (0, 10, 0), "lift": 0.025},
    "flex": {"sym": 1, "shoulderL": (0, -85, 0), "elbowL": (0, -100, 0), "spine": (-6, 0, 0), "neck": (-8, 0, 0)},
    # at the table
    "sit_table": {"seated": 1, "sym": 1, "shoulderL": (-25, -6, 0), "elbowL": (-65, 0, 14), "spine": (4, 0, 0)},
    "sit_crossed": {"seated": 1, "shoulderL": (-36, -12, 0), "elbowL": (-96, 0, -66), "shoulderR": (-34, -10, 0),
                    "elbowR": (-90, 0, -70), "spine": (-2, 0, 0)},
    "sit_back": {"seated": 1, "shoulderL": (-30, -14, 0), "elbowL": (-104, 0, -64), "shoulderR": (-28, -12, 0),
                 "elbowR": (-98, 0, -68), "spine": (-10, 0, 0), "neck": (-5, 0, 0)},
    "sit_palms": {"seated": 1, "sym": 1, "shoulderL": (-30, -16, 0), "elbowL": (-80, 0, 32), "wristL": (0, 40, 0),
                  "spine": (2, 0, 0), "lift": 0.02},
    "sit_hand": {"seated": 1, "shoulderL": (-25, -6, 0), "elbowL": (-65, 0, 14), "shoulderR": (-46, -14, 0),
                 "elbowR": (-100, 0, -10), "wristR": (0, 20, 0), "spine": (6, 0, 0)},
    "sit_point": {"seated": 1, "shoulderL": (-25, -6, 0), "elbowL": (-65, 0, 14), "shoulderR": (-78, -6, 0),
                  "elbowR": (-8, 0, 0), "spine": (8, 0, 0)},
    "sit_phone": {"seated": 1, "sym": 1, "shoulderL": (-36, -4, 0), "elbowL": (-82, 0, 26), "spine": (8, 0, 0)},
    "sit_laugh": {"seated": 1, "sym": 1, "shoulderL": (-20, -8, 0), "elbowL": (-66, 0, 14), "spine": (-12, 0, 0),
                  "neck": (-8, 0, 0)},
    "sit_lean": {"seated": 1, "sym": 1, "shoulderL": (-36, -4, 0), "elbowL": (-58, 0, 18), "spine": (14, 0, 0)},
}
SEATED_LEGS = {"hipL": (-88, -4, 0), "kneeL": (90, 0, 0), "ankleL": (-4, 0, 0)}


def _resolve(name):
    src = POSES[name]
    out = {}
    for j, v in src.items():
        if j in ("sym", "lift", "seated"):
            continue
        out[j] = (v[0], -v[1], -v[2]) if j.endswith("R") else v
    if src.get("seated"):
        for j, v in SEATED_LEGS.items():
            out[j] = v
            out[j[:-1] + "R"] = (v[0], -v[1], -v[2])
    if src.get("sym"):
        for j, v in list(out.items()):
            if j.endswith("L") and j[:-1] + "R" not in out:
                out[j[:-1] + "R"] = (v[0], -v[1], -v[2])
    return out, src.get("lift", 0.0), bool(src.get("seated"))


def pose_values(name):
    vals, lift, seated = _resolve(name)
    return {j: tuple(D(a) for a in v) for j, v in vals.items()}, lift, seated


def set_pose(p, name, w=1.0, other=None, add=None):
    """Blend from pose `other` (or rest) to pose `name` by w (w may overshoot past 1). add: {joint: (x, y, z) rad}
    added on top (head turns, breathing, laughs)."""
    a, la, sa = pose_values(other) if other else ({}, 0.0, False)
    b, lb, sb = pose_values(name)
    add = add or {}
    for j, e in p.J.items():
        if j == "root":
            continue
        r0 = a.get(j, (0, 0, 0))
        r1 = b.get(j, (0, 0, 0))
        d = add.get(j, (0, 0, 0))
        e.rotation_euler = tuple(x0 + (x1 - x0) * w + dd for x0, x1, dd in zip(r0, r1, d))
    lift = la + (lb - la) * w
    for s in ("L", "R"):
        loc = p.rest[f"shoulder{s}"][0]
        p.J[f"shoulder{s}"].location = (loc[0], loc[1], loc[2] + lift)
    z = SEAT_PELVIS if sb else 0.96
    p.J["pelvis"].location = (0, 0, z)


def ease_back(x, s=1.9):
    """0..1 with a small overshoot: fast in, settles."""
    x = max(0.0, min(1.0, x)) - 1
    return 1 + x * x * ((s + 1) * x + s)


# ------------------------------------------------------------------ showcase scene (a rooftop at golden hour)

def paint_sky():
    """64 x 128 backdrop: dusk gradient with a dithered band, and a skyline with lit windows."""
    h, w = 128, 64
    top, mid, low = np.array((74, 112, 190.0)), np.array((190, 140, 170.0)), np.array((252, 186, 120.0))
    a = np.zeros((h, w, 3), np.float32)
    bayer = np.array(((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))) / 16.0
    for y in range(h):
        t = y / (h - 1)
        c = top + (mid - top) * min(1, t / 0.55) if t < 0.55 else mid + (low - mid) * ((t - 0.55) / 0.45)
        a[y, :] = c
    a = np.floor(a / 12 + bayer[np.arange(h) % 4][:, np.arange(w) % 4][..., None]) * 12
    r = np.random.default_rng(9)
    x = 0
    while x < w:                                              # buildings
        bw, bh = int(r.integers(5, 11)), int(r.integers(18, 46))
        a[h - bh:, x:x + bw] = np.array((52, 46, 70.0)) + r.integers(-6, 7)
        for wy in range(h - bh + 3, h - 2, 4):
            for wx in range(x + 1, min(w, x + bw - 1), 2):
                if r.random() < 0.35:
                    a[wy, wx] = (255, 214, 120)
        x += bw + int(r.integers(0, 3))
    return a


def paint_floor():
    a = canvas(32, 32, (150, 120, 104))
    speckle(a, [(138, 108, 94), (160, 130, 112)], 0.3, 10)
    a[0, :] = a[:, 0] = (110, 88, 78)                         # grout, one tile per texture
    return a


def paint_wall():
    a = canvas(32, 32, (176, 92, 70))
    speckle(a, [(160, 82, 62), (188, 104, 80)], 0.3, 11)
    for y in range(0, 32, 4):                                 # bricks
        a[y, :] = (150, 132, 120)
        off = 0 if (y // 4) % 2 else 4
        for x in range(off, 32, 8):
            a[y:y + 4, x] = (150, 132, 120)
    return a


def rooftop():
    import bmesh
    bpy = _bpy()
    floor = material("floor", image("floor", paint_floor()))
    wall = material("wall", image("wall", paint_wall()))
    sky = material("sky", image("sky", paint_sky()), emit=1.0)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6)
    uv_box(bm, 1.6)
    to_object("floor", bm, [floor])
    for x0, x1, y0, y1 in ((-6, 6, 1.6, 1.9), (-6, -2.4, -2, 1.9), (2.4, 6, -2, 1.9)):   # the parapet
        bm = box(x0, x1, y0, y1, 0, 0.95)
        uv_box(bm, 1.4)
        to_object("parapet", bm, [wall])
    bm = bmesh.new()                                         # the skyline backdrop
    vs = [bm.verts.new(q) for q in ((-9, 9, -1), (9, 9, -1), (9, 9, 14), (-9, 9, 14))]
    f = bm.faces.new(vs)
    uv = bm.loops.layers.uv.verify()
    for l, c in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        l[uv].uv = c
    to_object("sky", bm, [sky]).visible_shadow = False
    world = bpy.data.worlds.new("w")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.32, 0.36, 0.52, 1)
    bg.inputs["Strength"].default_value = 0.55
    sun_d = bpy.data.lights.new("sun", "SUN")
    sun_d.energy, sun_d.color, sun_d.angle = 3.2, (1.0, 0.76, 0.52), math.radians(2)
    sun = bpy.data.objects.new("sun", sun_d)
    bpy.context.scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(62), 0, math.radians(-38))
    fill_d = bpy.data.lights.new("fill", "AREA")
    fill_d.energy, fill_d.size, fill_d.color = 60, 2.0, (0.7, 0.78, 1.0)
    fill = bpy.data.objects.new("fill", fill_d)
    bpy.context.scene.collection.objects.link(fill)
    fill.location = (-2.0, -2.5, 2.2)
    fill.rotation_euler = (math.radians(55), 0, math.radians(-40))


def camera(lens, loc, target):
    from mathutils import Vector
    bpy = _bpy()
    cam = bpy.context.scene.camera
    if cam is None:
        cd = bpy.data.cameras.new("cam")
        cd.sensor_width = 36
        cam = bpy.data.objects.new("cam", cd)
        bpy.context.scene.collection.objects.link(cam)
        bpy.context.scene.camera = cam
    cam.data.lens = lens
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return cam


def render_settings():
    bpy = _bpy()
    sc = bpy.context.scene
    r = sc.render
    r.engine = "BLENDER_EEVEE"
    if os.environ.get("OVERTHOUGHT_CPU_PREVIEW") == "1":
        r.engine = "CYCLES"
        sc.cycles.device = "CPU"
        sc.cycles.samples = 24
        sc.cycles.use_denoising = False                      # OIDN ran out of memory next to a GPU render
    r.fps = 30
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGB"
    sc.view_settings.view_transform = "Standard"           # painted colours stay as painted
    sc.view_settings.look = "None"
    try:
        sc.eevee.taa_render_samples = 16
        sc.eevee.use_shadows = True
    except Exception:
        pass


def _still(path):
    bpy = _bpy()
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def showcase(out, mode, clip_json=None):
    sys.path.insert(0, HERE)
    import ps2look
    from mathutils import Vector
    os.makedirs(out, exist_ok=True)
    bpy = _bpy()
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    rooftop()
    if mode == "lineup":                                      # all four side by side
        people = [build(w, x=x, rot_z=D(r)) for w, x, r in
                  (("jacket", -0.9, 8), ("suit", -0.3, 3), ("chad", 0.3, -3), ("overalls", 0.9, -8))]
        for q, (pz, ex) in zip(people, (("hips", "smug"), ("crossed", "neutral"), ("hips", "chad"),
                                        ("stand", "smile"))):
            q.pose(pz)
            q.face(ex)
        print("LOWPOLY triangles:", {q.who: q.tris for q in people})
        render_settings()
        cam = camera(30, (0, -3.6, 1.15), (0, 0, 1.0))
        ps2look.apply(cam)
        _still(os.path.join(out, "lineup.png"))
        camera(42, (0, -2.4, 1.62), (0, 0, 1.6))
        for q in people:
            q.face({"jacket": "smug", "suit": "smirk", "chad": "smug", "overalls": "laugh"}[q.who])
        _still(os.path.join(out, "lineup_faces.png"))
        return
    who = os.environ.get("LOWPOLY_WHO", "chad")
    ch = build(who)
    print("LOWPOLY triangles:", ch.tris)
    render_settings()
    cam = camera(35, (0, -3.0, 1.05), (0, 0, 0.95))
    ps2look.apply(cam)
    if mode == "turnaround":
        ch.pose("stand")
        ch.face("neutral")
        for tag, a in (("front", 0), ("34", -35), ("side", -90), ("back", 180)):
            ch.J["root"].rotation_euler = (0, 0, math.radians(a))
            _still(os.path.join(out, f"turn_{tag}.png"))
        for q in ("hips", "crossed", "point", "shrug", "flex"):
            ch.J["root"].rotation_euler = (0, 0, math.radians(-20 if q != "point" else 4))
            ch.pose(q)
            ch.face({"hips": "smug", "crossed": "serious", "point": "smug", "shrug": "neutral",
                     "flex": "laugh"}[q])
            _still(os.path.join(out, f"pose_{q}.png"))
    elif mode == "faces":
        ch.pose("stand")
        ch.J["root"].rotation_euler = (0, 0, math.radians(-12))
        camera(50, (0.05, -0.62, 1.67), (0, 0, 1.66))
        for e in ("neutral", "smug", "laugh", "shock", "serious"):
            ch.face(e)
            _still(os.path.join(out, f"face_{e}.png"))
        ch.face("neutral", mouth="open")
        _still(os.path.join(out, "face_talk.png"))
    elif mode == "clip":
        C = json.load(open(clip_json))
        sc = bpy.context.scene
        nf = len(C["mouth"])
        beats = C["poses"]                                    # [[t, pose, expr], ...]
        shots = C["shots"]                                    # [[t, lens, [loc], [target], push m], ...]
        dur = nf / 30.0

        def at(t):
            cur = max((b for b in beats if b[0] <= t), key=lambda b: b[0])
            i = beats.index(cur)
            prev = beats[i - 1][1] if i else "stand"
            return cur, prev, ease_back((t - cur[0]) / 0.22)

        def face_at(f):
            t = f / 30.0
            e = at(t)[0][2]
            m, shape = C["mouth"][min(f, nf - 1)], C["shape"][min(f, nf - 1)]
            blink = any(0 <= t - bt < 0.1 for bt in C.get("blinks", []))
            mouth = None if m < 0.15 else ("half" if m < 0.45 and shape == "aa" else TALK[shape])
            return e, mouth, "closed" if blink else None

        for f in range(nf):                                   # every face square exists before any render starts
            ch.face(*face_at(f))
        # one still per frame, everything set between renders (making or swapping images while an animation
        # render runs crashed Blender, Nov 26)
        for f in range(nf):
            t = f / 30.0
            (t0, q, e), prev, w = at(t)
            m = C["mouth"][min(f, nf - 1)]
            set_pose(ch, q, w, other=prev, add={"spine": (D(1.2) * math.sin(t * 2.4), 0, 0),
                                                "neck": (D(3.0) * m * math.sin(t * 9.0), 0, 0)})
            ch.face(*face_at(f))
            sh = max((s for s in shots if s[0] <= t), key=lambda s: s[0])
            t1 = next((s[0] for s in shots if s[0] > t), dur)
            k = sh[4] * (t - sh[0]) / max(1e-6, t1 - sh[0])     # a slow push toward the target over the shot
            loc = Vector(sh[2]) + (Vector(sh[3]) - Vector(sh[2])).normalized() * k
            camera(sh[1], loc, sh[3])
            path = os.path.join(out, f"f_{f + 1:05d}.png")
            if not os.path.exists(path):
                sc.frame_set(f + 1)
                _still(path)


if __name__ == "__main__" and "--" in sys.argv:
    args = sys.argv[sys.argv.index("--") + 1:]
    showcase(os.path.abspath(args[0]), args[1], args[2] if len(args) > 2 else None)
