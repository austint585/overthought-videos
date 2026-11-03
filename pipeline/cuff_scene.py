"""Blender scene for 'Cuffing season forecast': cel-shaded sets along x, 14 m apart, each with a floor, a colored back wall and
hanging signs. A thermometer weatherman (our cast) moves in stop motion (12 steps a second, the camera stays smooth). Shots, timed
by render_cuff.py: studio, pair, front, cuff (weather studio), lab, winter, photo, chart, tree, phone, cakes, thaw, final.

blender -b --factory-startup -P cuff_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
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
GREY, DARK, WOOD, ICE, WHITE = (0.55, 0.58, 0.64), (0.13, 0.14, 0.20), (0.62, 0.36, 0.16), (0.70, 0.88, 1.0), (0.97, 0.97, 0.95)

def heart(name, color, r=0.2, parent=None, loc=(0, 0, 0), line=0.01):
    """Two balls and an upside-down cone, facing -y."""
    root = K.empty(name, loc, parent)
    for s in (-1, 1):
        K.ball(f"{name}l{s}", r, color, (s * r * 0.62, 0, r * 0.35), root, squash=(1, 0.5, 1), line=line)
    K.cyl(name + "c", r * 1.38, r * 1.7, color, (0, 0, -r * 0.62), root, rot=(math.pi, 0, 0), line=line, seg=32, r2=0.0).scale = (1, 0.5, 1)
    return root

def half_heart(name, color, side, r=0.32, parent=None):
    root = K.empty(name, parent=parent)
    K.ball(f"{name}l", r, color, (side * r * 0.62, 0, r * 0.35), root, squash=(1, 0.5, 1))
    K.box(name + "w", (r * 0.9, r * 0.9, r * 1.5), color, (side * r * 0.45, 0, -r * 0.55), root,
          rot=(0, side * 0.62, 0), bevel=0.04).scale = (1, 0.55, 1)
    return root

def pin(name, color):
    root = K.empty(name)
    K.cyl(name + "s", 0.02, 0.3, DARK, (0, 0, 0.15), root, line=0)
    heart(name + "h", color, 0.13, root, (0, -0.02, 0.42), line=0.008)
    return root

def thermo(name):
    """Our cast: a thermometer with a red bulb, a red column that rises and falls, brows, a mouth with teeth, stubby limbs.
    z=0 at the feet."""
    root = K.empty(name)
    body = K.empty(name + "b", (0, 0, 0.30), root)
    K.cyl(name + "tube", 0.19, 1.0, WHITE, (0, 0, 0.78), body)
    K.ball(name + "cap", 0.19, WHITE, (0, 0, 1.28), body)
    K.ball(name + "bulb", 0.27, RED, (0, 0, 0.2), body)
    col = K.empty(name + "colp", (0, -0.2, 0.35), body)
    K.box(name + "col", (0.08, 0.03, 0.5), RED, (0, 0, 0.25), col, bevel=0.012, line=0)
    for i in range(6):
        K.box(f"{name}tk{i}", (0.06, 0.01, 0.012), DARK, (0.1, -0.19, 0.4 + i * 0.08), body, bevel=0, line=0)
    parts = {"root": root, "body": body, "col": col}
    for s, k in ((-1, "L"), (1, "R")):
        K.ball(name + "eye" + k, 0.06, (0.99, 0.98, 0.94), (s * 0.085, -0.205, 1.1), body, squash=(1, 0.35, 1), line=0.006)
        K.ball(name + "pup" + k, 0.028, K.INK, (s * 0.078, -0.226, 1.09), body, squash=(1, 0.3, 1), line=0)
        brow = K.empty(name + "br" + k, (s * 0.085, -0.228, 1.19), body)
        K.box(name + "brow" + k, (0.12, 0.02, 0.035), K.INK, (0, 0, 0), brow, bevel=0.005, line=0)
        parts["brow" + k] = brow
        arm = K.empty(name + "arm" + k, (s * 0.2, 0, 0.72), body)
        K.box(name + "armb" + k, (0.26, 0.09, 0.08), (0.85, 0.2, 0.15), (s * 0.13, 0, 0), arm, bevel=0.03)
        parts["arm" + k] = arm
        leg = K.empty(name + "leg" + k, (s * 0.12, 0, 0.30), root)
        K.box(name + "legb" + k, (0.11, 0.13, 0.30), (0.85, 0.2, 0.15), (0, 0, -0.15), leg, bevel=0.03)
        parts["leg" + k] = leg
    mouth = K.empty(name + "m", (0, -0.215, 0.95), body)
    K.box(name + "mouth", (0.15, 0.016, 0.06), K.INK, (0, 0, 0), mouth, bevel=0.01, line=0)
    for i in range(3):
        K.box(f"{name}tooth{i}", (0.026, 0.006, 0.04), (0.97, 0.96, 0.9), (-0.045 + i * 0.045, -0.01, 0), mouth, bevel=0.002, line=0)
    parts["mouth"] = mouth
    shades = K.empty(name + "sh", (0, -0.25, 1.1), body)
    for s in (-1, 1):
        K.box(f"{name}lens{s}", (0.13, 0.03, 0.08), DARK, (s * 0.085, 0, 0), shades, bevel=0.02, line=0.005)
    K.box(name + "bridge", (0.06, 0.02, 0.015), DARK, (0, 0, 0.02), shades, bevel=0, line=0)
    parts["shades"] = shades
    return parts

# ------------------------------------------------------------------ 0 studio: weather map, anchor desk, pins, the cold front

O0 = stage(0, NAVY, (0.30, 0.32, 0.40))
K.box("mapb", (3.1, 0.1, 2.6), (0.18, 0.46, 0.80), O0 + Vector((-0.3, 1.7, 2.15)), bevel=0.04)
K.box("land", (2.3, 0.06, 1.5), GREEN, O0 + Vector((-0.45, 1.62, 2.1)), bevel=0.25, line=0.01)
K.box("land2", (0.9, 0.06, 0.7), GREEN, O0 + Vector((0.55, 1.62, 1.5)), bevel=0.2, line=0.01)
K.label("mapt", "TONIGHT", 0.26, (1, 1, 1), O0 + Vector((-1.15, 1.6, 3.2)))
K.box("desk", (1.7, 0.8, 0.95), (0.85, 0.85, 0.88), O0 + Vector((1.0, -0.75, 0.475)), bevel=0.05)
K.box("deskband", (1.72, 0.05, 0.22), RED, O0 + Vector((1.0, -1.17, 0.7)), bevel=0.02, line=0)
K.label("deskt", "OVERTHOUGHT WEATHER", 0.12, (1, 1, 1), O0 + Vector((1.0, -1.21, 0.69)))
PIN_A = pin("pinA", PINK)
PIN_B = pin("pinB", BLUE)
PINS_A_AT = O0 + Vector((-0.6, 1.55, 1.85))
PINS_B_AT = O0 + Vector((-0.3, 1.55, 1.85))
FRONT = K.empty("front")
K.box("frontbar", (0.06, 0.04, 2.3), (0.15, 0.35, 0.95), (0, 0, 0), FRONT, bevel=0, line=0.008)
for i in range(6):
    K.cyl(f"tri{i}", 0.13, 0.04, (0.15, 0.35, 0.95), (0.1, 0, -0.95 + i * 0.38), FRONT, rot=(math.pi / 2, 0, 0), seg=3, line=0.008)
SNOW = [K.ball(f"snow{i}", 0.035, WHITE, AWAY, line=0.004) for i in range(40)]
srng = random.Random(4)
SNOW_P = [(srng.uniform(-2.1, 2.1), srng.uniform(0, 1), srng.uniform(0.5, 1.1)) for _ in SNOW]
S_CUFF = K.sign("s_cuff", ["CUFFING", "SEASON"], AWAY, w=2.2, head="WEATHER WARNING")

# ------------------------------------------------------------------ 1 lab: the photo on an easel, the dial, a window

O1 = stage(1, TEAL, CREAM)
K.box("win", (1.3, 0.12, 1.1), WHITE, O1 + Vector((-0.8, 2.0, 3.55)), bevel=0.03)
K.box("pane", (1.1, 0.05, 0.9), (0.45, 0.75, 0.98), O1 + Vector((-0.8, 1.92, 3.55)), bevel=0, line=0)
PANE = bpy.data.objects["pane"]
NIGHT = K.box("panen", (1.1, 0.05, 0.9), (0.12, 0.18, 0.40), AWAY, bevel=0, line=0)
SUN = K.ball("sun", 0.22, GOLD, AWAY, squash=(1, 0.3, 1))
FLAKES = [K.ball(f"flake{i}", 0.03, WHITE, AWAY, line=0.004) for i in range(16)]
frng = random.Random(9)
FLAKE_P = [(frng.uniform(-0.6, 0.6), frng.uniform(0, 1)) for _ in FLAKES]
for x in (-0.35, 0.35):
    K.box(f"easel{x}", (0.06, 0.06, 2.0), WOOD, O1 + Vector((-0.8 + x, 0.2, 1.0)), rot=(0, -x * 0.25, 0), bevel=0.01)
K.box("frame", (1.1, 0.08, 1.35), WOOD, O1 + Vector((-0.8, 0.12, 1.75)), bevel=0.03)
K.box("photo", (0.9, 0.03, 1.15), CREAM, O1 + Vector((-0.8, 0.065, 1.75)), bevel=0, line=0)
for s in (1, -1):                                       # an hourglass silhouette: the "body photo", kept abstract
    K.cyl(f"glass{s}", 0.26, 0.42, PINK, O1 + Vector((-0.8, 0.04, 1.75 + s * 0.22)), rot=(0 if s > 0 else math.pi, 0, 0),
          seg=32, r2=0.08, line=0.006).scale = (1, 0.15, 1)
K.label("photot", "SAME PHOTO", 0.14, K.INK, O1 + Vector((-0.8, 0.03, 1.25)))
K.box("dialpost", (0.1, 0.1, 1.5), GREY, O1 + Vector((0.95, 0.4, 0.75)), bevel=0.02)
K.cyl("dial", 0.7, 0.08, (0.98, 0.96, 0.88), O1 + Vector((0.95, 0.35, 2.1)), rot=(math.pi / 2, 0, 0), seg=64, line=0.015)
K.label("dlo", "MEH", 0.16, BLUE, O1 + Vector((0.55, 0.29, 2.3)))
K.label("dhi", "HOTTER", 0.16, RED, O1 + Vector((1.35, 0.29, 2.3)))
K.label("dname", "HOT-O-METER", 0.13, K.INK, O1 + Vector((0.95, 0.29, 1.68)))
NEEDLE = K.empty("needle", O1 + Vector((0.95, 0.28, 1.9)))
K.box("needleb", (0.05, 0.02, 0.55), RED, (0, 0, 0.27), NEEDLE, bevel=0.01, line=0.006)
K.ball("needlehub", 0.07, DARK, (0, 0, 0), NEEDLE, line=0)
CLIP = K.box("clip", (0.3, 0.04, 0.4), WOOD, AWAY, bevel=0.02)

# ------------------------------------------------------------------ 2 chart: breakups by week, Nov 1 to Christmas

O2 = stage(2, (0.86, 0.42, 0.52), CREAM)
WEEKS = [0.35, 0.5, 0.65, 0.85, 1.1, 1.6, 0.9, 0.15]     # the shape of the 2010 chart, an illustration, not data points
BARS = [K.box(f"bar{i}", (0.32, 0.5, 1.0), RED if i == 5 else BLUE, AWAY, bevel=0.03) for i in range(8)]
K.box("chartbase", (3.3, 0.7, 0.12), DARK, O2 + Vector((0, 0, 0.06)), bevel=0.02)
K.label("lnov", "NOV 1", 0.17, (1, 1, 1), O2 + Vector((-1.4, -0.37, 0.06)))
K.label("lpk", "DEC 11", 0.17, (1, 1, 1), O2 + Vector((0.6, -0.37, 0.06)))
K.label("lxm", "DEC 25", 0.17, (1, 1, 1), O2 + Vector((1.4, -0.37, 0.06)))
HL = half_heart("hl", RED, -1)
HR = half_heart("hr", RED, 1)
S_BRK = K.sign("s_brk", ["BREAKUPS"], O2 + Vector((-0.6, 0.8, 3.5)), w=2.2, head="FACEBOOK, 2010")

def bar_at(i):
    return O2 + Vector((-1.4 + i * 0.4, 0, 0.12))

# ------------------------------------------------------------------ 3 tree: Christmas Day, ceasefire

O3 = stage(3, (0.10, 0.22, 0.20), (0.56, 0.33, 0.16))
for i, (r, z) in enumerate(((1.0, 0.9), (0.8, 1.6), (0.55, 2.2))):
    K.cyl(f"tree{i}", r, 1.0, (0.12, 0.52, 0.22), O3 + Vector((-0.7, 0.5, z)), seg=32, r2=0.05)
K.box("trunk", (0.25, 0.25, 0.45), WOOD, O3 + Vector((-0.7, 0.5, 0.22)), bevel=0.02)
K.ball("star", 0.15, GOLD, O3 + Vector((-0.7, 0.5, 2.8)))
for i, (x, c) in enumerate(((-1.45, RED), (-0.05, BLUE), (0.2, GOLD))):
    K.box(f"gift{i}", (0.5, 0.5, 0.42), c, O3 + Vector((x, -0.1, 0.21)), bevel=0.03)
    K.box(f"ribbon{i}", (0.08, 0.52, 0.44), WHITE, O3 + Vector((x, -0.1, 0.21)), bevel=0.01, line=0)
MIT = []
for s, c in ((-1, RED), (1, BLUE)):
    m = K.empty(f"mit{s}", O3 + Vector((0.5 + s * 0.24, -0.5, 0.0)))
    K.box(f"mitb{s}", (0.36, 0.22, 0.5), c, (0, 0, 0.45), m, bevel=0.1)
    K.box(f"mitc{s}", (0.4, 0.26, 0.14), WHITE, (0, 0, 0.17), m, bevel=0.05)
    K.box(f"mitt{s}", (0.14, 0.2, 0.22), c, (-s * 0.22, 0, 0.5), m, rot=(0, s * 0.5, 0), bevel=0.06)
    MIT.append(m)
heart("mitheart", PINK, 0.12, None, O3 + Vector((0.5, -0.5, 1.05)))
S_CEASE = K.sign("s_cease", ["FEWEST", "BREAKUPS"], O3 + Vector((0.7, 0.7, 3.5)), w=2.2, head="DEC 25")

# ------------------------------------------------------------------ 4 phone: Dating Sunday

O4 = stage(4, (0.44, 0.30, 0.72), CREAM)
K.box("phone", (1.7, 0.2, 3.1), DARK, O4 + Vector((0, 0.6, 1.75)), bevel=0.18)
K.box("screen", (1.45, 0.05, 2.7), (0.96, 0.95, 1.0), O4 + Vector((0, 0.48, 1.78)), bevel=0.08, line=0)
CARDS = []
for i in range(8):
    r = K.empty(f"card{i}")
    K.box(f"cardb{i}", (0.9, 0.04, 1.2), WHITE, (0, 0, 0), r, bevel=0.03, line=0.008)
    K.box(f"cardp{i}", (0.78, 0.02, 0.8), (0.3 + 0.08 * (i % 5), 0.55, 0.85 - 0.06 * (i % 4)), (0, -0.025, 0.12), r, bevel=0.01, line=0)
    K.ball(f"cardh{i}", 0.17, (0.95, 0.75, 0.6), (0, -0.04, 0.2), r, squash=(1, 0.3, 1), line=0.005)
    CARDS.append(r)
X_BTN = K.cyl("xbtn", 0.16, 0.04, RED, O4 + Vector((-0.4, 0.44, 0.75)), rot=(math.pi / 2, 0, 0), seg=32, line=0.006)
H_BTN = K.cyl("hbtn", 0.16, 0.04, GREEN, O4 + Vector((0.4, 0.44, 0.75)), rot=(math.pi / 2, 0, 0), seg=32, line=0.006)
S_SUN = K.sign("s_sun", ["DATING SUNDAY"], O4 + Vector((-0.2, 0.2, 3.9)), w=2.7, head="1ST SUNDAY IN JANUARY")

# ------------------------------------------------------------------ 5 cakes: the ten most common U.S. birthdays

O5 = stage(5, (0.95, 0.60, 0.22), (0.60, 0.35, 0.17))
K.box("shelf", (3.3, 0.9, 0.7), WHITE, O5 + Vector((0, 0.2, 0.35)), bevel=0.04)
K.box("shelf2", (3.3, 0.7, 0.08), WHITE, O5 + Vector((0, 0.3, 1.5)), bevel=0.02)
for x in (-1.6, 1.6):
    K.box(f"shelfp{x}", (0.1, 0.1, 0.8), WHITE, O5 + Vector((x, 0.55, 1.1)), bevel=0.02)
DATES = ["SEP 9", "SEP 19", "SEP 12", "SEP 17", "SEP 10", "JUL 7", "SEP 20", "SEP 15", "SEP 16", "SEP 18"]
CAKES = []
for i, d in enumerate(DATES):
    r = K.empty(f"cake{i}")
    c = (0.55, 0.75, 0.95) if d.startswith("JUL") else PINK
    K.cyl(f"cakeb{i}", 0.24, 0.32, c, (0, 0, 0.16), r, seg=32)
    K.cyl(f"cakei{i}", 0.25, 0.06, WHITE, (0, 0, 0.33), r, seg=32, line=0.006)
    K.box(f"cakec{i}", (0.04, 0.04, 0.2), CREAM, (0, 0, 0.46), r, bevel=0.01, line=0.004)
    K.ball(f"cakef{i}", 0.04, GOLD, (0, 0, 0.6), r, squash=(1, 1, 1.5), line=0)
    K.label(f"caket{i}", d, 0.1, K.INK if d.startswith("JUL") else (1, 1, 1), (0, -0.25, 0.16), r)
    CAKES.append(r)
S_BDAY = K.sign("s_bday", ["9 IN SEPTEMBER"], O5 + Vector((0, 0.6, 3.25)), w=2.9, head="TOP 10 U.S. BIRTHDAYS")

def cake_at(i):
    return O5 + Vector((-1.2 + (i % 5) * 0.6, 0.1 if i < 5 else 0.0, 1.54 if i < 5 else 0.7))

# ------------------------------------------------------------------ 6 thaw: the sun comes back, the snowman goes, the pin pops

O6 = stage(6, (0.45, 0.75, 0.98), (0.40, 0.70, 0.30))
SUN6 = K.ball("sun6", 0.55, GOLD, AWAY, squash=(1, 0.4, 1))
SNOWMAN = K.empty("snowman", O6 + Vector((-1.4, -0.2, 0)))
for i, (r, z) in enumerate(((0.42, 0.4), (0.3, 1.05), (0.22, 1.5))):
    K.ball(f"sm{i}", r, WHITE, (0, 0, z), SNOWMAN)
K.cyl("nose", 0.05, 0.25, (0.95, 0.5, 0.1), (0, -0.3, 1.5), SNOWMAN, rot=(math.pi / 2, 0, 0), r2=0.0, seg=16, line=0.004)
PUDDLE = K.cyl("puddle", 0.7, 0.01, ICE, AWAY, line=0, seg=48)
K.box("map6", (1.8, 0.1, 1.3), (0.18, 0.46, 0.80), O6 + Vector((0.9, 1.7, 2.3)), bevel=0.04)
K.box("land6", (1.3, 0.06, 0.8), GREEN, O6 + Vector((0.9, 1.62, 2.3)), bevel=0.2, line=0.01)
PIN6A = pin("pin6A", PINK)
PIN6B = pin("pin6B", BLUE)
S_VDAY = K.sign("s_vday", ["VALENTINE'S DAY"], AWAY, w=2.8, head="CLEARING BY")
S_FINAL = K.sign("s_final", ["SINGLE"], AWAY, w=2.0, head="FORECAST FOR SUMMER")

# ------------------------------------------------------------------ the cast and the camera

TH = thermo("th")
cam = B.camera(lens=40, fstop=16.0)
cam.data.dof.use_dof = False
cam.data.clip_start = 0.05
cam.data.clip_end = 80

def lc(a, b, tg, lens, u, o):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "studio": lambda u: lc((-0.4, -7.6, 2.0), (-0.2, -7.0, 2.0), (-0.1, 0, 2.0), 40, u, O0),
    "pair": lambda u: lc((-0.6, -1.5, 2.1), (-0.5, -1.1, 2.05), (-0.45, 1.5, 2.15), 42, u, O0),
    "front": lambda u: lc((0.3, -7.4, 2.2), (0.0, -6.8, 2.2), (-0.1, 1.0, 2.1), 40, u, O0),
    "cuff": lambda u: lc((0.6, -5.6, 2.4), (0.4, -5.0, 2.6), (0.3, 0, 2.6), 40, u, O0),
    "lab": lambda u: lc((-0.6, -7.8, 2.1), (-0.3, -7.2, 2.1), (0, 0, 2.1), 40, u, O1),
    "winter": lambda u: lc((1.0, -6.2, 2.3), (0.8, -5.6, 2.3), (0.5, 0, 2.2), 40, u, O1),
    "photo": lambda u: lc((-0.95, -2.6, 1.75), (-0.85, -2.2, 1.75), (-0.8, 0, 1.45), 42, u, O1),
    "chart": lambda u: lc((-0.4, -8.6, 1.8), (-0.1, -8.0, 1.8), (0, 0, 1.8), 40, u, O2),
    "tree": lambda u: lc((0.5, -7.6, 1.7), (0.2, -7.0, 1.7), (0, 0, 1.8), 40, u, O3),
    "phone": lambda u: lc((-0.6, -7.6, 2.1), (-0.2, -7.0, 2.1), (0, 0, 2.2), 40, u, O4),
    "cakes": lambda u: lc((-0.8, -8.4, 1.9), (-0.3, -7.8, 1.9), (0, 0, 2.0), 40, u, O5),
    "thaw": lambda u: lc((-0.6, -7.6, 1.9), (-0.3, -7.0, 1.9), (0, 0, 2.0), 40, u, O6),
    "final": lambda u: lc((1.0, -5.4, 2.1), (0.8, -4.8, 2.1), (0.5, 0.5, 2.1), 40, u, O6),
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
    return tg + (Matrix.Rotation(-0.5, 3, "Z") @ (loc - tg)) * 0.85 + Vector((0, 0, 0.3)), tg, lens

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

def pose(p, at, hop=0.0, sway=0.0, arm=(0.0, 0.0), scale=1.0, angry=1.0, yaw=0.0, level=0.6, chatter=0.0, shades=False):
    p["root"].location = at + Vector((0, 0, hop))
    p["root"].rotation_euler = (0, sway, yaw)
    p["root"].scale = (scale, scale, scale)
    p["armL"].rotation_euler = (0, -arm[0], 0)
    p["armR"].rotation_euler = (0, arm[1], 0)
    p["legL"].rotation_euler = (0.5 * math.sin(hop * 12) if hop else 0, 0, 0)
    p["legR"].rotation_euler = (-0.5 * math.sin(hop * 12) if hop else 0, 0, 0)
    p["col"].scale = (1, 1, max(0.02, level))
    p["mouth"].scale = (1, 1, 1 + chatter)
    p["shades"].location = Vector((0, -0.25, 1.1)) if shades else AWAY
    K.mood(p, angry)

def snowfall(q, center, w, h, z0, objs, params):
    for o, (x, ph, sp) in zip(objs, params):
        f = (ph + q * sp * 0.4) % 1.0
        o.location = center + Vector((x * w / 4.2, -0.2, z0 + h * (1 - f)))

CHART2 = next(s for s, n in SHOTS if n == "chart~2")

def apply_state(t):
    name, u, age, cut, second, length = shot_at(t)
    q = math.floor(t * 12) / 12            # props step in stop motion
    aq = age - (t - q)
    loc, tg, lens = alt_cam(CAMS[name], cut) if second else CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens

    for o in [TH["root"], PIN_A, PIN_B, FRONT, S_CUFF, NIGHT, SUN, CLIP, HL, HR, SUN6, PUDDLE, PIN6A, PIN6B, S_VDAY, S_FINAL] \
            + SNOW + FLAKES + BARS + CARDS + CAKES:
        o.location = AWAY
    for o in [TH["root"], PIN_A, PIN_B, SNOWMAN] + CAKES:
        o.scale = (1, 1, 1)
    PANE.location = O1 + Vector((-0.8, 1.92, 3.55))
    SNOWMAN.location = O6 + Vector((-1.4, -0.2, 0))

    if name in ("studio", "pair", "front", "cuff"):
        PIN_A.location = PINS_A_AT
        if name == "pair":
            pop(PIN_B, PINS_B_AT, aq, 0.3)
        else:
            PIN_B.location = PINS_B_AT if name != "studio" or second else AWAY
        cold = name in ("front", "cuff")
        if name == "front":
            FRONT.location = O0 + Vector((-1.7 + 2.6 * smooth01(aq / max(0.5, length * 0.8)), 1.56, 2.15))
        elif name == "cuff":
            FRONT.location = O0 + Vector((0.9, 1.56, 2.15))
        if cold:
            snowfall(q, O0 + Vector((-0.3, 1.3, 0)), 3.0, 2.4, 0.95, SNOW, SNOW_P)
        if name == "cuff":
            drop(S_CUFF, O0 + Vector((0.3, 0.6, 3.0)), aq, 0.25)
        chill = smooth01(aq / 1.2) if name == "front" else (1.0 if name == "cuff" else 0.0)
        pose(TH, O0 + Vector((1.0, 0.05, 0)), arm=(1.2 + 0.2 * math.sin(q * 5), 0.2) if not cold else (0.4, 0.4),
             sway=0.04 * math.sin(q * 30) * chill, level=0.75 - 0.55 * chill, chatter=0.6 * chill * abs(math.sin(q * 40)),
             angry=1.0 - 2.0 * chill, yaw=-0.25)
    elif name in ("lab", "winter", "photo"):
        win = O1 + Vector((-0.8, 1.86, 3.55))
        wint = name != "lab"
        if wint:
            NIGHT.location, PANE.location = O1 + Vector((-0.8, 1.92, 3.55)), AWAY
            snowfall(q, win + Vector((0, 0.15, 0)), 0.9, 0.8, -0.4, FLAKES, [(x, ph, 0.8) for x, ph in FLAKE_P])
        else:
            SUN.location = win + Vector((0.3, 0, 0.2))
        g = smooth01((aq - 0.3) / 0.5) if name == "winter" else (1.0 if name == "photo" else 0.0)
        NEEDLE.rotation_euler = (0, -1.0 + 1.9 * g + 0.04 * math.sin(q * 20) * g, 0)
        pose(TH, O1 + Vector((0.05, -1.0, 0)), arm=(0.3, 1.0 + 0.3 * math.sin(q * 4)), yaw=-0.3, angry=-0.6 + 1.6 * g,
             level=0.4 + 0.5 * g)
        CLIP.location = TH["root"].location + Vector((-0.38, -0.12, 1.15))
    elif name == "chart":
        for i, b in enumerate(BARS):
            h = WEEKS[i] * smooth01((aq - 0.12 - i * 0.22) / 0.3)
            b.location = bar_at(i) + Vector((0, 0, h / 2))
            b.scale = (1, 1, max(0.01, h))
        split = smooth01((t - CHART2 - 0.3) / 0.35)
        top = bar_at(5) + Vector((0, -0.1, WEEKS[5] + 0.55))
        HL.location = top + Vector((-0.04 - 0.3 * split, 0, -0.1 * split))
        HR.location = top + Vector((0.04 + 0.3 * split, 0, -0.1 * split))
        HL.rotation_euler = (0, 0.4 * split, 0)
        HR.rotation_euler = (0, -0.4 * split, 0)
        pose(TH, O2 + Vector((-1.6, -1.3, 0)), arm=(0.2, 0.9), yaw=0.35, angry=-1.0, level=0.5 - 0.2 * split)
    elif name == "tree":
        for m, s in zip(MIT, (-1, 1)):
            m.rotation_euler = (0, s * 0.06 * math.sin(q * 4), 0)
        pose(TH, O3 + Vector((1.25, -0.6, 0)), arm=(0.6, 0.6), angry=-0.2, level=0.6, hop=0.05 * abs(math.sin(q * 5)), yaw=-0.3)
    elif name == "phone":
        for i, c in enumerate(CARDS):
            f = (aq * 1.4 - i * 0.45)
            if f < 0:
                continue
            k = i % 2 * 2 - 1
            f = min(f, 1.6)
            c.location = O4 + Vector((k * 2.6 * smooth01(f) ** 1.5, 0.3 - 0.4 * f, 1.85 + 0.6 * math.sin(min(f, 1.0) * math.pi) - 0.4 * f))
            c.rotation_euler = (0, k * 0.9 * f, 0)
            if f >= 1.6:
                c.location = AWAY
        pose(TH, O4 + Vector((1.2, -0.9, 0)), arm=(0.3, 0.6 + 0.9 * abs(math.sin(q * 6))), yaw=-0.4, level=0.7)
    elif name == "cakes":
        for i, c in enumerate(CAKES):
            if second:
                pop(c, cake_at(i), aq - (length * 0.25), 0.12 * i)
            else:
                c.location = AWAY
        pose(TH, O5 + Vector((1.25, -1.6, 0)), scale=0.85, arm=(0.2, 1.1), angry=0.3, level=0.8, yaw=-0.4)
    elif name in ("thaw", "final"):
        warm = smooth01(aq / 1.5) if name == "thaw" else 1.0
        SUN6.location = O6 + Vector((-1.1, 1.9, 1.6 + 2.6 * warm))
        SNOWMAN.scale = (1, 1, max(0.05, 1 - 0.85 * warm))
        PUDDLE.location = O6 + Vector((-1.4, -0.2, 0.01))
        PUDDLE.scale = (0.3 + 0.9 * warm,) * 3
        PIN6A.location = O6 + Vector((0.75, 1.55, 2.1))
        if name == "thaw":
            PIN6B.location = O6 + Vector((1.05, 1.55, 2.1))
            drop(S_VDAY, O6 + Vector((-0.5, 0.6, 3.75)), aq, 0.3)
            pose(TH, O6 + Vector((0.2, -0.8, 0)), arm=(0.8, 0.8), level=0.4 + 0.5 * warm, angry=-1.0 + 2.0 * warm, yaw=-0.2)
        else:
            f = max(0.0, aq - 0.45) / 0.5
            if f < 1.6:
                PIN6B.location = O6 + Vector((1.05 + 1.1 * f, 1.4 - 0.8 * f, 2.1 + 1.2 * f - 1.6 * f * f))
                PIN6B.rotation_euler = (0, 4 * f, 0)
            drop(S_FINAL, O6 + Vector((0.6, 0.7, 3.7)), aq, 0.9)
            pose(TH, O6 + Vector((0.0, -0.8, 0)), arm=(0.1, 1.3), level=0.95, shades=True, angry=0.4,
                 hop=0.06 * abs(math.sin(q * 6)), yaw=-0.2)

B.render_settings(FPS, samples=int(os.environ.get("CUFF_SAMPLES", "12")), motion_blur=0.0)
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
