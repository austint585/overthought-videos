"""Blender scene for 'Restaurant units': cel-shaded sets along x, 14 m apart, each with a floor, a colored back wall and hanging
signs. The cast is a wine glass with a face and stubby limbs (your friend). She moves in stop motion (12 steps a second, the camera
stays smooth). Shots, timed by render_wine.py: bar (two empty glasses on the counter, then RESTAURANT UNITS), lab (shelves of
480 drinks, a beaker scale), pour (a giant bottle pours past the ONE STANDARD DRINK line, +43%), row (ten glasses, all over the
line), martini (a martini glass on a pedestal, 1.6), math (two glasses on a scale, about 3 drinks), final (she wears shades).

blender -b --factory-startup -P wine_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
"""
import json, math, os, random, sys
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bkit as B
import toon as K

argv = sys.argv[sys.argv.index("--") + 1:]
TIMING, OUT, MODE = argv[0], argv[1], argv[2]
T = json.load(open(TIMING))
FPS, DUR, SHOTS = T["fps"], T["duration"], T["shots"]
NF = int(round(DUR * FPS))
os.makedirs(OUT, exist_ok=True)
B.clear_scene()
scene = B.scene
AWAY = Vector((0, 0, -1.0e4))
K.setup_world()

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

def setx(i):
    return Vector((i * 14.0, 0, 0))

def stage(i, wall, floor):
    o = setx(i)
    K.box(f"floor{i}", (13.5, 12, 0.3), floor, o + Vector((0, -2.5, -0.15)), bevel=0, line=0)
    K.box(f"wall{i}", (13.5, 0.3, 9), wall, o + Vector((0, 2.2, 4.5)), bevel=0, line=0)
    K.box(f"skirt{i}", (13.5, 0.06, 0.28), tuple(c * 0.7 for c in wall), o + Vector((0, 2.03, 0.14)), bevel=0, line=0)
    return o

NAVY, CREAM, RED, BLUE, TEAL, PINK, GOLD, GREEN = (0.08, 0.12, 0.30), (0.93, 0.90, 0.76), (0.82, 0.13, 0.11), (0.14, 0.50, 0.90), \
    (0.05, 0.62, 0.60), (0.93, 0.18, 0.48), (0.98, 0.72, 0.08), (0.20, 0.62, 0.20)
GREY, DARK, WOOD, ICE, WHITE = (0.55, 0.58, 0.64), (0.13, 0.14, 0.20), (0.62, 0.36, 0.16), (0.80, 0.93, 1.0), (0.97, 0.97, 0.95)
WATER, ORANGE, PLUM = (0.38, 0.72, 0.98), (0.95, 0.45, 0.15), (0.36, 0.14, 0.30)

def heart(name, color, r=0.2, parent=None, loc=(0, 0, 0), line=0.01):
    """Two balls and an upside-down cone, facing -y."""
    root = K.empty(name, loc, parent)
    for s in (-1, 1):
        K.ball(f"{name}l{s}", r, color, (s * r * 0.62, 0, r * 0.35), root, squash=(1, 0.5, 1), line=line)
    K.cyl(name + "c", r * 1.38, r * 1.7, color, (0, 0, -r * 0.62), root, rot=(math.pi, 0, 0), line=line, seg=32, r2=0.0).scale = (1, 0.5, 1)
    return root

def face(name, body, r, z, parts, eye=0.06, gap=0.09):
    """Eyes, brows and a mouth on a round body of radius r, facing -y."""
    y = -r - 0.012
    for s, k in ((-1, "L"), (1, "R")):
        K.ball(name + "eye" + k, eye, (0.99, 0.98, 0.94), (s * gap, y, z), body, squash=(1, 0.35, 1), line=0.006)
        K.ball(name + "pup" + k, eye * 0.47, K.INK, (s * gap * 0.92, y - 0.02, z - 0.01), body, squash=(1, 0.3, 1), line=0)
        brow = K.empty(name + "br" + k, (s * gap, y - 0.02, z + eye * 1.6), body)
        K.box(name + "brow" + k, (eye * 2.0, 0.02, 0.035), K.INK, (0, 0, 0), brow, bevel=0.005, line=0)
        parts["brow" + k] = brow
    mouth = K.empty(name + "m", (0, y, z - eye * 2.4), body)
    K.box(name + "mouth", (eye * 2.4, 0.016, 0.05), K.INK, (0, 0, 0), mouth, bevel=0.01, line=0)
    parts["mouth"] = mouth
    shades = K.empty(name + "sh", (0, y - 0.03, z), body)
    for s in (-1, 1):
        K.box(f"{name}lens{s}", (eye * 2.2, 0.03, eye * 1.4), DARK, (s * gap, 0, 0), shades, bevel=0.02, line=0.005)
    K.box(name + "bridge", (0.06, 0.02, 0.015), DARK, (0, 0, 0.02), shades, bevel=0, line=0)
    parts["shades"] = shades

def limbs(name, root, body, parts, color, arm_x, arm_z, hip_x):
    for s, k in ((-1, "L"), (1, "R")):
        arm = K.empty(name + "arm" + k, (s * arm_x, 0, arm_z), body)
        K.box(name + "armb" + k, (0.26, 0.09, 0.08), color, (s * 0.13, 0, 0), arm, bevel=0.03)
        parts["arm" + k] = arm
        leg = K.empty(name + "leg" + k, (s * hip_x, 0, 0.30), root)
        K.box(name + "legb" + k, (0.11, 0.13, 0.30), color, (0, 0, -0.15), leg, bevel=0.03)
        parts["leg" + k] = leg

WINE, GLASS, STEM = (0.55, 0.04, 0.16), (0.82, 0.92, 0.98), (0.90, 0.95, 0.99)
OLIVE, BOTTLE = (0.45, 0.62, 0.12), (0.10, 0.30, 0.16)

def glass_body(name, parent, s=1.0, wine=0.5, line=0.01):
    """A wine glass cup (open cone-ish bowl) on a stem and foot, z=0 at the foot. Returns the wine object (scaled in z)."""
    K.cyl(name + "foot", 0.22 * s, 0.03 * s, STEM, (0, 0, 0.015 * s), parent, line=line, seg=32)
    K.cyl(name + "stem", 0.035 * s, 0.4 * s, STEM, (0, 0, 0.23 * s), parent, line=line, seg=16)
    K.cyl(name + "bowl", 0.26 * s, 0.5 * s, GLASS, (0, 0, 0.68 * s), parent, r2=0.3 * s, line=line, seg=32)
    w = K.cyl(name + "wine", 0.27 * s, 0.4 * s, WINE, (0, 0, 0.45 * s), parent, r2=0.31 * s, line=0.006, seg=32)
    w.data.transform(Matrix.Translation((0, 0, 0.2 * s)))     # pivot at the bottom of the bowl
    w.scale = (1, 1, max(0.01, wine))
    return w

def friend(name):
    """Her: a big wine glass with eyes, brows, a mouth and stubby limbs. z=0 at the feet."""
    root = K.empty(name)
    body = K.empty(name + "b", (0, 0, 0.30), root)
    K.cyl(name + "foot", 0.3, 0.05, STEM, (0, 0, 0.025), body, seg=32)
    K.cyl(name + "stem", 0.06, 0.55, STEM, (0, 0, 0.3), body, seg=16)
    K.cyl(name + "bowl", 0.42, 0.8, GLASS, (0, 0, 0.98), body, r2=0.5, seg=48)
    K.cyl(name + "wine", 0.43, 0.4, WINE, (0, 0, 0.78), body, r2=0.475, line=0.008, seg=48)
    parts = {"root": root, "body": body}
    face(name, body, 0.46, 1.1, parts, eye=0.075, gap=0.14)
    limbs(name, root, body, parts, (0.65, 0.78, 0.86), 0.44, 0.95, 0.14)
    return parts

def scale_line(name, z, w, parent=None, loc=(0, 0, 0)):
    root = K.empty(name, loc, parent)
    K.box(name + "l", (w, 0.03, 0.035), (0.98, 0.96, 0.88), (0, 0, z), root, bevel=0, line=0.006)
    return root

# ------------------------------------------------------------------ 0 bar: the counter, two glasses

O0 = stage(0, PLUM, WOOD)
K.box("bar", (5.0, 1.0, 1.1), WOOD, O0 + Vector((0, 0.6, 0.55)), bevel=0.04)
K.box("bartop", (5.2, 1.2, 0.12), DARK, O0 + Vector((0, 0.6, 1.16)), bevel=0.03)
for x in (-2.0, -1.2, 1.4, 2.1):
    for k in range(2):
        K.cyl(f"bt{x}{k}", 0.13, 0.7, BOTTLE if (x + k) % 2 else (0.45, 0.10, 0.12), O0 + Vector((x + 0.3 * k, 2.0, 2.15)), seg=16)
        K.cyl(f"btn{x}{k}", 0.05, 0.25, BOTTLE, O0 + Vector((x + 0.3 * k, 2.0, 2.6)), seg=12)
K.box("shelf", (5.5, 0.4, 0.08), DARK, O0 + Vector((0, 2.0, 1.76)), bevel=0)
BAR_G = []
for k, x in enumerate((0.55, 1.05)):
    g = K.empty(f"bg{k}", O0 + Vector((x, 0.4, 1.22)))
    glass_body(f"bg{k}", g, s=0.8, wine=0.08)
    BAR_G.append(g)
S_TWO = K.sign("s_two", ["2 GLASSES"], AWAY, w=2.2, head="SHE HAD")
S_UNITS = K.sign("s_units", ["RESTAURANT UNITS"], AWAY, w=3.4, head="COUNTED IN")

# ------------------------------------------------------------------ 1 lab: shelves of 480 drinks

O1 = stage(1, (0.86, 0.90, 0.95), (0.35, 0.38, 0.45))
for r in range(3):
    K.box(f"lshelf{r}", (5.6, 0.6, 0.08), GREY, O1 + Vector((0, 1.5, 0.9 + r * 0.95)), bevel=0)
    for c in range(22):
        kind = (c + r) % 3
        x = -2.6 + c * 0.245
        col = WINE if kind == 0 else ((0.95, 0.75, 0.2) if kind == 1 else (0.95, 0.45, 0.55))
        K.cyl(f"lg{r}{c}", 0.08, 0.32, GLASS, O1 + Vector((x, 1.5, 0.94 + r * 0.95 + 0.16)), seg=12, line=0.006)
        K.cyl(f"lgw{r}{c}", 0.07, 0.2, col, O1 + Vector((x, 1.48, 0.94 + r * 0.95 + 0.11)), seg=12, line=0)
K.box("lbench", (3.0, 1.0, 0.95), WHITE, O1 + Vector((0, -0.4, 0.475)), bevel=0.03)
BEAKER = K.cyl("beaker", 0.25, 0.6, GLASS, O1 + Vector((-0.5, -0.4, 1.25)), seg=24)
K.cyl("beakerw", 0.22, 0.35, WINE, O1 + Vector((-0.5, -0.42, 1.13)), seg=24, line=0)
for k in range(4):
    K.box(f"tick{k}", (0.12, 0.02, 0.02), K.INK, O1 + Vector((-0.5, -0.67, 1.05 + k * 0.12)), bevel=0, line=0)
K.box("meter", (0.8, 0.5, 0.45), GOLD, O1 + Vector((0.7, -0.4, 1.18)), bevel=0.05)
K.box("meterscr", (0.6, 0.02, 0.25), DARK, O1 + Vector((0.7, -0.66, 1.2)), bevel=0.01, line=0)
METER = K.label("metert", "14.2%", 0.17, (0.4, 1.0, 0.5), O1 + Vector((0.7, -0.68, 1.2)))
S_480 = K.sign("s_480", ["480 DRINKS"], AWAY, w=2.4, head="BOUGHT AND MEASURED")

# ------------------------------------------------------------------ 2 pour: a giant bottle, the standard-drink line

O2 = stage(2, (0.98, 0.80, 0.30), (0.62, 0.38, 0.20))
K.box("ped2", (1.6, 1.2, 0.8), WHITE, O2 + Vector((0, 0, 0.4)), bevel=0.04)
BIGG = K.empty("bigg", O2 + Vector((0, 0, 0.8)))
BIG_WINE = glass_body("bigg", BIGG, s=2.2, wine=0.0, line=0.014)
STD_Z = 0.8 + (0.45 + 0.2 - 0.2) * 2.2       # the bowl bottom in world z; the line sits at 45% fill
LINE_STD = K.box("stdline", (1.25, 0.03, 0.04), (0.98, 0.96, 0.88), O2 + Vector((0, -0.6, 0.8 + 0.45 * 2.2 + 0.4 * 2.2 * 0.62)),
                 bevel=0, line=0.006)
K.label("stdt", "1 DRINK", 0.22, (0.98, 0.96, 0.88), O2 + Vector((1.2, -0.62, 0.8 + 0.45 * 2.2 + 0.4 * 2.2 * 0.62)))
BOT = K.empty("bot", AWAY)
K.cyl("botb", 0.38, 1.6, BOTTLE, (0, 0, 0), BOT, seg=32)
K.cyl("bots", 0.38, 0.35, BOTTLE, (0, 0, 0.97), BOT, r2=0.14, seg=32)
K.cyl("botn", 0.14, 0.5, BOTTLE, (0, 0, 1.39), BOT, seg=16)
K.cyl("botl", 0.39, 0.6, CREAM, (0, 0, -0.1), BOT, seg=32, line=0.006)
STREAM = K.cyl("stream", 0.05, 1.0, WINE, AWAY, seg=12, line=0)
S_43 = K.sign("s_43", ["+43%"], AWAY, w=1.7, head="AVERAGE POUR")

# ------------------------------------------------------------------ 3 row: ten glasses, every one over the line

O3 = stage(3, (0.55, 0.80, 0.95), (0.25, 0.30, 0.45))
K.box("shelf3", (6.0, 1.0, 0.9), WHITE, O3 + Vector((0, 0.2, 0.45)), bevel=0.03)
ROW = []
for k in range(10):
    g = K.empty(f"rg{k}", O3 + Vector((-2.48 + k * 0.55, 0.2, 0.9)))
    w = glass_body(f"rg{k}", g, s=0.85, wine=0.01)
    ROW.append((g, w))
K.box("rowline", (5.8, 0.03, 0.035), (0.98, 0.25, 0.2), O3 + Vector((0, -0.12, 0.9 + (0.45 + 0.4 * 0.62) * 0.85)), bevel=0, line=0)
S_98 = K.sign("s_98", ["98% OVER 1 DRINK"], AWAY, w=3.2, head="WINE GLASSES")

# ------------------------------------------------------------------ 4 martini: a martini glass on a pedestal

O4 = stage(4, (0.20, 0.55, 0.50), (0.10, 0.28, 0.26))
K.box("ped4", (1.4, 1.4, 1.0), GOLD, O4 + Vector((0, 0, 0.5)), bevel=0.05)
MART = K.empty("mart", O4 + Vector((0, 0, 1.0)))
K.cyl("mfoot", 0.4, 0.05, STEM, (0, 0, 0.025), MART, seg=32)
K.cyl("mstem", 0.05, 1.0, STEM, (0, 0, 0.5), MART, seg=16)
K.cyl("mcone", 0.08, 0.7, GLASS, (0, 0, 1.35), MART, r2=0.75, seg=48)
K.cyl("mgin", 0.06, 0.5, (0.92, 0.95, 0.80), (0, 0, 1.27), MART, r2=0.6, seg=48, line=0)
K.cyl("pick", 0.015, 0.9, WOOD, (0.25, 0, 1.6), MART, rot=(0, -0.6, 0), seg=8, line=0.004)
OLV = K.ball("olive", 0.1, OLIVE, (0.18, 0, 1.48), MART)
S_16 = K.sign("s_16", ["1.6 DRINKS"], AWAY, w=2.2, head="AVERAGE MARTINI")

# ------------------------------------------------------------------ 5 math: two glasses on a scale

O5 = stage(5, PINK, (0.40, 0.12, 0.25))
K.box("scale", (3.0, 1.0, 0.35), GREY, O5 + Vector((0, 0, 0.175)), bevel=0.05)
K.box("scaled", (1.2, 0.02, 0.22), DARK, O5 + Vector((0, -0.51, 0.18)), bevel=0.01, line=0)
SCALE_T = K.label("scalet", "0.0", 0.16, (0.4, 1.0, 0.5), O5 + Vector((0, -0.53, 0.18)))
MATH_G = []
for k, x in enumerate((-0.7, 0.7)):
    g = K.empty(f"mg{k}", O5 + Vector((x, 0, 0.35)))
    glass_body(f"mgl{k}", g, s=1.6, wine=0.72)
    MATH_G.append(g)
S_3 = K.sign("s_3", ["ABOUT 3 DRINKS"], AWAY, w=2.8, head="2 GLASSES =")

# ------------------------------------------------------------------ 6 final: she wears shades

O6 = stage(6, NAVY, (0.30, 0.32, 0.40))
K.box("ped6", (1.4, 1.0, 0.6), GOLD, O6 + Vector((0, 0.2, 0.3)), bevel=0.05)
K.label("ped6t", "2 GLASSES", 0.2, K.INK, O6 + Vector((0, -0.32, 0.3)))
S_FIN = K.sign("s_fin", ["THE GLASSES HAD 3"], AWAY, w=3.3, head="SHE HAD 2")
SPARK = [K.ball(f"spark{i}", 0.05, GOLD, AWAY, line=0) for i in range(8)]

# ------------------------------------------------------------------ the cast and the camera

FR = friend("fr")
FR["shades"]["home"] = FR["shades"].location.copy()
cam = B.camera(lens=40, fstop=16.0)
cam.data.dof.use_dof = False
cam.data.clip_start = 0.05
cam.data.clip_end = 80

def lc(a, b, tg, lens, u, o):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "bar": lambda u: lc((-0.4, -6.4, 2.1), (-0.2, -5.8, 2.1), (0, 0, 1.8), 40, u, O0),
    "lab": lambda u: lc((0.5, -7.0, 2.2), (0.2, -6.4, 2.2), (0, 0, 1.9), 40, u, O1),
    "pour": lambda u: lc((0.0, -9.2, 2.4), (0.1, -8.6, 2.4), (0, 0, 2.1), 40, u, O2),
    "row": lambda u: lc((-0.6, -6.6, 1.9), (-0.2, -6.0, 1.8), (0, 0, 1.6), 40, u, O3),
    "martini": lambda u: lc((0.3, -6.0, 2.4), (0.1, -5.4, 2.4), (0, 0, 2.3), 40, u, O4),
    "math": lambda u: lc((-0.3, -6.4, 2.0), (-0.1, -5.8, 2.0), (0, 0, 1.75), 40, u, O5),
    "final": lambda u: lc((0.4, -6.4, 2.1), (0.2, -5.8, 2.1), (0, 0, 2.1), 40, u, O6),
}

def base_of(i):
    return SHOTS[i][1].split("~")[0]

def shot_at(t):
    k = max([0] + [i for i, (s, _) in enumerate(SHOTS) if t >= s - 1e-6])
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    cut = max(0.0, min(1.0, (t - SHOTS[k][0]) / max(1e-6, t1 - SHOTS[k][0])))
    a = b = k
    while a > 0 and base_of(a - 1) == base_of(k):
        a -= 1
    while b + 1 < len(SHOTS) and base_of(b + 1) == base_of(k):
        b += 1
    t0 = SHOTS[a][0]
    t2 = SHOTS[b + 1][0] if b + 1 < len(SHOTS) else DUR
    return base_of(k), max(0.0, min(1.0, (t - t0) / max(1e-6, t2 - t0))), t - t0, cut, "~" in SHOTS[k][1], t2 - t0

def alt_cam(base, u):
    loc, tg, lens = base(u)
    return tg + (Matrix.Rotation(-0.5, 3, "Z") @ (loc - tg)) * 0.75 + Vector((0, 0, 0.3)), tg, lens

def drop(ob, at, age, delay=0.0):
    """A sign falling in on its cords with a little overshoot."""
    u = max(0.0, age - delay) / 0.4
    z = 4.5 * max(0.0, 1 - u) ** 2 - (0.12 * math.sin(min(u, 2.0) * 6) * max(0.0, 1 - u / 2) if u > 1 else 0)
    ob.location = at + Vector((0, 0, z))

def pop(ob, at, age, delay=0.0, s=1.0):
    u = max(0.0, age - delay) / 0.25
    k = 0.0 if u <= 0 else (1.0 + 0.25 * math.sin(min(u, 2.0) * math.pi) * max(0.0, 1 - u / 2) if u >= 1 else smooth01(u))
    ob.location = at if k > 0 else AWAY
    ob.scale = (k * s,) * 3

def pose(p, at, hop=0.0, sway=0.0, arm=(0.0, 0.0), scale=1.0, angry=0.0, yaw=0.0, gape=0.0, shades=False, frozen=None):
    p["root"].location = at + Vector((0, 0, hop))
    p["root"].rotation_euler = (0, sway, yaw)
    p["root"].scale = (scale, scale, scale)
    p["armL"].rotation_euler = (0, -arm[0], 0)
    p["armR"].rotation_euler = (0, arm[1], 0)
    p["legL"].rotation_euler = (0.5 * math.sin(hop * 12) if hop else 0, 0, 0)
    p["legR"].rotation_euler = (-0.5 * math.sin(hop * 12) if hop else 0, 0, 0)
    p["mouth"].scale = (1 - 0.4 * gape, 1, 1 + 3.0 * gape)
    p["shades"].location = p["shades"]["home"] if shades else AWAY
    K.mood(p, angry)
    if "ice" in p:
        f = 0.0 if frozen is None else frozen
        p["ice"].scale = (1, 1, max(0.001, f))
        p["ice"].location = Vector((0, 0, 1.56)) if f > 0.001 else AWAY
        for sp, home, z in p["spikes"]:
            k = smooth01((f - z) / 0.15) if f > 0 else 0.0
            sp.location = home if k > 0 else AWAY
            sp.scale = (k, k, k)


def start_of(n):
    return next(s for s, m in SHOTS if m == n)

def apply_state(t):
    name, u, age, cut, second, length = shot_at(t)
    q = math.floor(t * 12) / 12            # props step in stop motion
    aq = age - (t - q)
    loc, tg, lens = alt_cam(CAMS[name], cut) if second and name not in ("bar", "pour") else CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens

    for o in [FR["root"], S_TWO, S_UNITS, S_480, S_43, S_98, S_16, S_3, S_FIN, BOT, STREAM] + SPARK:
        o.location = AWAY
    FR["root"].scale = (1, 1, 1)

    if name == "bar":
        pose(FR, O0 + Vector((-0.8, -0.6, 0)), arm=(0.3, 1.1 + 0.2 * math.sin(q * 5)), sway=0.08 * math.sin(q * 4), yaw=0.15,
             angry=-0.3, gape=0.2 * abs(math.sin(q * 7)))
        drop(S_TWO, O0 + Vector((0.9, 0.0, 2.85)), aq, 0.2)
        if second:
            drop(S_UNITS, O0 + Vector((0.0, -0.6, 2.75)), t - start_of("bar~2"), 0.05)
            pose(FR, O0 + Vector((-0.8, -0.6, 0)), shades=True, arm=(0.3, 1.4), angry=0.4, yaw=0.15, hop=0.03 * abs(math.sin(q * 6)))
    elif name == "lab":
        METER.data.body = f"{11.0 + 3.5 * abs(math.sin(q * 3)):.1f}%"
        drop(S_480, O1 + Vector((0, 0.6, 3.6)), aq, 0.2)
        pose(FR, O1 + Vector((-1.1, -1.4, 0)), scale=0.8, arm=(0.2, 0.4), yaw=0.3, angry=-0.6, gape=0.3)
    elif name == "pour":
        f = smooth01((aq - 0.3) / 2.2)
        BIG_WINE.scale = (1, 1, max(0.01, 0.62 * 1.43 * f))
        tip = O2 + Vector((0.55, 0, 3.55))
        BOT.location = O2 + Vector((1.35, 0, 3.9))
        BOT.rotation_euler = (0, -2.1, 0)
        if f < 0.999:
            STREAM.location = O2 + Vector((0.3, 0, 2.9))
            STREAM.scale = (1, 1, 1.0)
        if second:
            drop(S_43, O2 + Vector((-1.15, -0.8, 3.2)), t - start_of("pour~2"), 0.1)
        pose(FR, O2 + Vector((-1.7, -1.0, 0)), scale=0.75, arm=(1.2, 1.2), angry=-1.0, gape=0.4 + 0.3 * f, yaw=0.3)
    elif name == "row":
        for k, (g, w) in enumerate(ROW):
            f = smooth01((aq - 0.15 * k) / 0.4)
            w.scale = (1, 1, max(0.01, 0.62 * (1.25 + 0.3 * ((k * 7) % 5) / 4) * f))
        drop(S_98, O3 + Vector((0, 0.3, 2.75)), aq, 0.4)
    elif name == "martini":
        MART.rotation_euler = (0, 0, 0.4 * math.sin(q * 1.5))
        drop(S_16, O4 + Vector((0, 0.3, 3.6)), aq, 0.3)
        pose(FR, O4 + Vector((-1.6, -0.9, 0)), scale=0.75, arm=(0.4, 1.5), angry=-0.8, gape=0.6, yaw=0.3)
    elif name == "math":
        v = 2.86 * smooth01((aq - 0.3) / 1.0)
        SCALE_T.data.body = f"{v:.1f} DRINKS"
        drop(S_3, O5 + Vector((0, 0.3, 3.4)), aq, 0.6)
    elif name == "final":
        pose(FR, O6 + Vector((0, 0.2, 0.6)), shades=True, angry=0.5, arm=(0.2, 1.4), hop=0.04 * abs(math.sin(q * 6)))
        drop(S_FIN, O6 + Vector((0, -0.2, 3.35)), aq, 0.3)
        for i, s in enumerate(SPARK):
            a = i / len(SPARK) * 2 * math.pi + q
            s.location = O6 + Vector((math.cos(a) * 1.1, -0.4, 1.9 + math.sin(a) * 1.0))

B.render_settings(FPS, samples=int(os.environ.get("WINE_SAMPLES", "12")), motion_blur=0.0)
K.flat_look()
try:
    scene.eevee.use_raytracing = False
    scene.eevee.use_fast_gi = False
except Exception as ex:
    print("skip", ex)

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1) / FPS)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
