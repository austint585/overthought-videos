"""Blender scene for 'The ick is supercooling': cel-shaded sets along x, 14 m apart, each with a floor, a colored back wall and
hanging signs. Our cast are objects: a water bottle (the crush, it freezes from the top down) and a coffee mug (him). Both move in
stop motion (12 steps a second, the camera stays smooth). Shots, timed by render_ick.py: date, freezer, tap, site, plane, chart,
door, final.

blender -b --factory-startup -P ick_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
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

def bottle(name):
    """The crush: a water bottle with a blue cap and a label band. An ice shell grows from the cap down when it freezes.
    z=0 at the feet."""
    root = K.empty(name)
    body = K.empty(name + "b", (0, 0, 0.30), root)
    K.cyl(name + "tube", 0.28, 1.0, WATER, (0, 0, 0.5), body)
    K.cyl(name + "shoulder", 0.28, 0.25, WATER, (0, 0, 1.125), body, r2=0.12)
    K.cyl(name + "neck", 0.12, 0.16, WATER, (0, 0, 1.33), body)
    K.cyl(name + "cap", 0.135, 0.14, BLUE, (0, 0, 1.46), body)
    K.cyl(name + "band", 0.287, 0.26, WHITE, (0, 0, 0.3), body, line=0.006)
    K.label(name + "bandt", "H2O", 0.14, BLUE, (0, -0.3, 0.3), body)
    parts = {"root": root, "body": body}
    face(name, body, 0.30, 0.78, parts)
    limbs(name, root, body, parts, (0.25, 0.55, 0.85), 0.28, 0.6, 0.12)
    ice = K.empty(name + "ice", (0, 0, 1.56), body)      # scaled in z from the cap down
    for k, (r, z0, z1, r2) in enumerate(((0.305, 0.0, 1.0, None), (0.305, 1.0, 1.255, 0.135), (0.14, 1.25, 1.41, None),
                                          (0.155, 1.39, 1.545, None))):
        K.cyl(f"{name}ice{k}", r, z1 - z0, ICE, (0, 0, (z0 + z1) / 2 - 1.56), ice, r2=r2, line=0.01)
    parts["ice"] = ice
    spikes = []
    rng = random.Random(len(name))
    for i in range(7):
        a = rng.uniform(-1.4, 1.4) + (math.pi if i % 3 == 2 else 0)
        z = rng.uniform(0.15, 1.2)
        sp = K.cyl(f"{name}sp{i}", 0.06, 0.24, WHITE, (math.sin(a) * 0.3, -math.cos(a) * 0.3, z), body,
                   rot=(math.pi / 2 + 0.3, 0, a), r2=0.0, seg=6, line=0.006)
        spikes.append((sp, Vector(sp.location), 1.0 - z / 1.3))
    parts["spikes"] = spikes
    return parts

def mug(name):
    """Him: an orange coffee mug with a handle and stubby limbs. z=0 at the feet."""
    root = K.empty(name)
    body = K.empty(name + "b", (0, 0, 0.30), root)
    K.cyl(name + "cup", 0.42, 0.9, ORANGE, (0, 0, 0.45), body, bevel=0.03)
    K.cyl(name + "coffee", 0.37, 0.02, (0.30, 0.17, 0.08), (0, 0, 0.9), body, line=0)
    K.box(name + "handle", (0.12, 0.12, 0.5), ORANGE, (0.5, 0, 0.47), body, bevel=0.05)
    K.box(name + "handle2", (0.16, 0.12, 0.1), ORANGE, (0.44, 0, 0.7), body, bevel=0.04)
    K.box(name + "handle3", (0.16, 0.12, 0.1), ORANGE, (0.44, 0, 0.24), body, bevel=0.04)
    parts = {"root": root, "body": body}
    face(name, body, 0.43, 0.6, parts, eye=0.07, gap=0.13)
    limbs(name, root, body, parts, (0.75, 0.33, 0.1), 0.4, 0.42, 0.18)
    return parts

# ------------------------------------------------------------------ 0 date: a candlelit table for two

O0 = stage(0, PLUM, WOOD)
K.cyl("table", 1.0, 0.1, WHITE, O0 + Vector((0, 0, 1.05)), seg=48)
K.cyl("cloth", 1.02, 0.4, (0.95, 0.94, 0.9), O0 + Vector((0, 0, 0.85)), seg=48, r2=1.1, line=0.008)
K.cyl("post", 0.1, 0.9, DARK, O0 + Vector((0, 0, 0.45)), seg=16)
for x in (-0.25, 0.25):
    K.cyl(f"candle{x}", 0.05, 0.35, CREAM, O0 + Vector((x, 0.3, 1.27)), seg=16, line=0.005)
    K.ball(f"flame{x}", 0.045, GOLD, O0 + Vector((x, 0.3, 1.5)), squash=(1, 1, 1.6), line=0)
K.box("pic", (1.2, 0.08, 0.9), GOLD, O0 + Vector((0, 2.0, 3.3)), bevel=0.03)
K.box("picin", (1.0, 0.04, 0.7), (0.95, 0.55, 0.65), O0 + Vector((0, 1.95, 3.3)), bevel=0, line=0)
HEARTS = [heart(f"hrt{i}", PINK, 0.12) for i in range(5)]
S_SUPER = K.sign("s_super", ["SUPERCOOLED"], AWAY, w=2.5, head="CRUSH STATUS")

# ------------------------------------------------------------------ 1 freezer: open chest of drawers, the display counts down

O1 = stage(1, (0.55, 0.80, 0.95), (0.70, 0.72, 0.78))
FZ = O1 + Vector((0, 0.6, 0))
K.box("fzback", (2.6, 0.12, 3.4), WHITE, FZ + Vector((0, 0.55, 1.7)), bevel=0.04)
K.box("fzin", (2.3, 0.05, 3.0), (0.20, 0.30, 0.48), FZ + Vector((0, 0.48, 1.7)), bevel=0, line=0)
for s in (-1, 1):
    K.box(f"fzside{s}", (0.15, 1.2, 3.4), WHITE, FZ + Vector((s * 1.22, 0, 1.7)), bevel=0.04)
K.box("fztop", (2.6, 1.2, 0.15), WHITE, FZ + Vector((0, 0, 3.33)), bevel=0.04)
K.box("fzbot", (2.6, 1.2, 0.3), WHITE, FZ + Vector((0, 0, 0.15)), bevel=0.04)
K.box("fzshelf", (2.3, 1.0, 0.06), (0.75, 0.85, 0.95), FZ + Vector((0, 0.05, 2.55)), bevel=0.01, line=0.006)
DOORP = K.empty("doorp", FZ + Vector((-1.3, -0.6, 0)))
K.box("fzdoor", (2.6, 0.15, 3.4), WHITE, (1.3, 0, 1.7), DOORP, bevel=0.04)
K.box("fzhandle", (0.08, 0.1, 1.0), GREY, (2.4, -0.1, 1.9), DOORP, bevel=0.03)
DOORP.rotation_euler = (0, 0, -2.2)
for i, (x, z) in enumerate(((-1.05, 3.1), (1.05, 3.1), (-1.05, 0.4), (1.05, 0.4), (0.6, 2.6), (-0.7, 2.6))):
    K.ball(f"frost{i}", 0.13, WHITE, FZ + Vector((x, 0.2, z)), squash=(1, 0.6, 0.7), line=0.006)
K.box("disp", (1.1, 0.1, 0.5), DARK, FZ + Vector((0, -0.65, 3.0)), bevel=0.04)
DISP = K.label("dispt", "0°C", 0.34, (0.4, 1.0, 0.55), FZ + Vector((0, -0.71, 2.98)))
FLAKES = [K.ball(f"flake{i}", 0.03, WHITE, AWAY, line=0.004) for i in range(18)]
frng = random.Random(9)
FLAKE_P = [(frng.uniform(-1, 1), frng.uniform(0, 1), frng.uniform(0.5, 1.0)) for _ in FLAKES]
S_LIQ = K.sign("s_liq", ["STILL LIQUID"], AWAY, w=2.5, head="-40°C")

# ------------------------------------------------------------------ 2 lab: the bench, a speck of dust, a magnifier

O2 = stage(2, TEAL, CREAM)
K.box("bench", (3.6, 1.4, 0.15), (0.90, 0.92, 0.95), O2 + Vector((0, 0.2, 0.95)), bevel=0.02)
for x in (-1.6, 1.6):
    K.box(f"benchleg{x}", (0.12, 1.2, 0.9), GREY, O2 + Vector((x, 0.2, 0.45)), bevel=0.02)
for i, (x, c) in enumerate(((-1.3, (0.98, 0.5, 0.2)), (1.35, (0.5, 0.9, 0.4)))):
    K.cyl(f"flask{i}", 0.22, 0.35, c, O2 + Vector((x, 0.5, 1.2)), seg=32, r2=0.08)
    K.cyl(f"flaskn{i}", 0.07, 0.25, WHITE, O2 + Vector((x, 0.5, 1.5)), seg=16, line=0.005)
K.box("board", (2.6, 0.08, 1.4), (0.12, 0.26, 0.20), O2 + Vector((0, 2.0, 3.4)), bevel=0.03)
K.label("chalk", "0°C = FREEZING?", 0.22, WHITE, O2 + Vector((0, 1.94, 3.5)))
K.label("chalk2", "NOT ALWAYS", 0.18, GOLD, O2 + Vector((0, 1.94, 3.1)))
SPECK = K.ball("speck", 0.045, (0.35, 0.30, 0.28), AWAY, line=0.005)
LENS = K.empty("lens")
K.cyl("lensring", 0.75, 0.08, DARK, (0, 0, 0), LENS, rot=(math.pi / 2, 0, 0), seg=64, line=0)
K.cyl("lensglass", 0.66, 0.09, (0.85, 0.95, 1.0), (0, -0.01, 0), LENS, rot=(math.pi / 2, 0, 0), seg=64, line=0)
K.box("lenshandle", (0.14, 0.1, 0.8), WOOD, (0.55, 0, -0.85), LENS, rot=(0, 0.6, 0), bevel=0.03)
BIGSPECK = K.ball("bigspeck", 0.22, (0.35, 0.30, 0.28), AWAY, squash=(1, 0.7, 0.85), line=0.008)
S_SITE = K.sign("s_site", ["NUCLEATION", "SITE"], AWAY, w=2.4, head="PHYSICS")

# ------------------------------------------------------------------ 3 plane: two seats, windows, the runway outside

O3 = stage(3, CREAM, (0.30, 0.34, 0.48))
for i, x in enumerate((-2.2, 0.0, 2.2)):
    K.box(f"winf{i}", (0.8, 0.1, 1.0), (0.85, 0.83, 0.75), O3 + Vector((x, 2.0, 2.4)), bevel=0.3)
    K.box(f"wing{i}", (0.6, 0.05, 0.42), (0.55, 0.80, 1.0), O3 + Vector((x, 1.94, 2.6)), bevel=0.15, line=0)
    K.box(f"winr{i}", (0.6, 0.05, 0.36), (0.35, 0.62, 0.30), O3 + Vector((x, 1.94, 2.2)), bevel=0.15, line=0)
    K.box(f"winrw{i}", (0.6, 0.04, 0.08), DARK, O3 + Vector((x, 1.92, 2.15)), bevel=0, line=0)
for i, x in enumerate((-0.6, 0.6)):
    K.box(f"seat{i}", (1.0, 0.9, 0.35), BLUE, O3 + Vector((x, 0.4, 0.55)), bevel=0.06)
    K.box(f"seatb{i}", (1.0, 0.25, 1.6), BLUE, O3 + Vector((x, 0.9, 1.3)), bevel=0.08)
    K.box(f"head{i}", (0.7, 0.27, 0.25), WHITE, O3 + Vector((x, 0.86, 2.0)), bevel=0.05)
    K.box(f"seatleg{i}", (0.7, 0.6, 0.38), DARK, O3 + Vector((x, 0.4, 0.19)), bevel=0.02)
K.box("arm", (0.12, 0.8, 0.12), GREY, O3 + Vector((0, 0.35, 0.95)), bevel=0.03)
K.box("bin", (5.0, 0.8, 0.5), WHITE, O3 + Vector((0, 1.6, 3.6)), bevel=0.08)
S_ICK = K.sign("s_ick", ["THE ICK"], AWAY, w=2.0, head="NUCLEATION SITE")

# ------------------------------------------------------------------ 4 chart: 75% of women, 57% of men

O4 = stage(4, (0.86, 0.42, 0.52), CREAM)
K.box("chartbase", (2.6, 0.9, 0.12), DARK, O4 + Vector((0, 0, 0.06)), bevel=0.02)
BARS = [K.box(f"bar{i}", (0.8, 0.7, 1.0), c, AWAY, bevel=0.04) for i, c in enumerate((PINK, BLUE))]
PCT = [0.75, 0.57]
BAR_X = [-0.6, 0.6]
BARL = [K.label(f"barl{i}", s, 0.3, (1, 1, 1), O4 + Vector((BAR_X[i], -0.47, 0.06))) for i, s in enumerate(("WOMEN", "MEN"))]
BARP = [K.label(f"barp{i}", s, 0.36, K.INK, AWAY) for i, s in enumerate(("75%", "57%"))]
S_STUDY = K.sign("s_study", ["GOT THE ICK"], O4 + Vector((0, 0.8, 4.2)), w=2.4, head="125 SINGLE ADULTS, 2025")

# ------------------------------------------------------------------ 5 door: she leaves, on the spot

O5 = stage(5, (0.44, 0.30, 0.72), (0.60, 0.35, 0.17))
K.box("doorframe", (1.5, 0.2, 2.9), WHITE, O5 + Vector((0.9, 2.0, 1.45)), bevel=0.04)
K.box("doorway", (1.2, 0.1, 2.6), (0.98, 0.85, 0.45), O5 + Vector((0.9, 1.92, 1.3)), bevel=0, line=0)
DOOR5 = K.empty("door5", O5 + Vector((0.3, 1.85, 0)))
K.box("door5b", (1.2, 0.1, 2.6), (0.85, 0.30, 0.20), (0.6, 0, 1.3), DOOR5, bevel=0.03)
K.ball("door5k", 0.07, GOLD, (1.05, -0.08, 1.25), DOOR5, line=0.005)
K.label("exit", "EXIT", 0.25, (1, 1, 1), O5 + Vector((0.9, 1.88, 3.1)))
K.box("exitbox", (0.8, 0.05, 0.35), GREEN, O5 + Vector((0.9, 1.9, 3.1)), bevel=0.03, line=0)
S_SPOT = K.sign("s_spot", ["26% ENDED IT", "ON THE SPOT"], AWAY, w=2.6, head="SAME STUDY")

# ------------------------------------------------------------------ 6 final: a trophy pedestal, sunglasses

O6 = stage(6, NAVY, (0.30, 0.32, 0.40))
K.box("ped", (1.2, 1.0, 0.7), GOLD, O6 + Vector((0, 0.2, 0.35)), bevel=0.05)
K.label("pedt", "NOT PICKY", 0.2, K.INK, O6 + Vector((0, -0.32, 0.38)))
S_PHYS = K.sign("s_phys", ["JUST PHYSICS"], AWAY, w=2.6, head="DIAGNOSIS")
SPARK = [K.ball(f"spark{i}", 0.05, GOLD, AWAY, line=0) for i in range(8)]

# ------------------------------------------------------------------ the cast and the camera

BT = bottle("bt")
MG = mug("mg")
cam = B.camera(lens=40, fstop=16.0)
cam.data.dof.use_dof = False
cam.data.clip_start = 0.05
cam.data.clip_end = 80

def lc(a, b, tg, lens, u, o):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "date": lambda u: lc((-0.4, -7.2, 2.0), (-0.2, -6.6, 2.0), (0, 0, 1.6), 40, u, O0),
    "freezer": lambda u: lc((0.5, -7.4, 2.0), (0.2, -6.6, 2.1), (0, 0, 1.9), 40, u, O1),
    "tap": lambda u: lc((0.0, -4.6, 2.0), (0.2, -4.0, 2.0), (0.3, 0, 1.9), 40, u, O2),
    "site": lambda u: lc((0.2, -4.6, 2.7), (0.1, -4.2, 2.7), (0.1, 0, 2.6), 40, u, O2),
    "plane": lambda u: lc((-0.5, -6.6, 1.8), (-0.2, -6.0, 1.8), (0, 0, 1.7), 40, u, O3),
    "chart": lambda u: lc((-0.4, -7.6, 2.1), (-0.1, -7.0, 2.1), (0, 0, 2.0), 40, u, O4),
    "door": lambda u: lc((-0.5, -7.4, 1.9), (-0.2, -6.8, 1.9), (0, 0, 1.8), 40, u, O5),
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

for p in (BT, MG):
    p["shades"]["home"] = p["shades"].location.copy()

def flakes(q, center, w, h, objs, params):
    for o, (x, ph, sp) in zip(objs, params):
        f = (ph + q * sp * 0.4) % 1.0
        o.location = center + Vector((x * w / 2, -0.4, h * (1 - f)))

def apply_state(t):
    name, u, age, cut, second, length = shot_at(t)
    q = math.floor(t * 12) / 12            # props step in stop motion
    aq = age - (t - q)
    loc, tg, lens = alt_cam(CAMS[name], cut) if second else CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens

    for o in [BT["root"], MG["root"], S_SUPER, S_LIQ, SPECK, LENS, BIGSPECK, S_SITE, S_ICK, S_SPOT, S_PHYS] \
            + HEARTS + FLAKES + BARS + BARP + SPARK:
        o.location = AWAY
    for o in [BT["root"], MG["root"]] + HEARTS:
        o.scale = (1, 1, 1)
    DOOR5.rotation_euler = (0, 0, -1.2)

    if name == "date":
        for i, h in enumerate(HEARTS):
            f = (aq * 0.6 + i * 0.2) % 1.0
            h.location = O0 + Vector((-0.9 + 0.12 * math.sin(i * 2 + q * 4), -0.5, 2.0 + 0.9 * f))
            h.scale = (0.6 + 0.6 * math.sin(f * math.pi),) * 3
        pose(BT, O0 + Vector((-1.35, -0.5, 0)), arm=(0.4 + 0.3 * math.sin(q * 4), 0.9), sway=0.06 * math.sin(q * 5), yaw=0.3,
             angry=-0.8)
        pose(MG, O0 + Vector((1.35, -0.5, 0)), arm=(0.9 + 0.5 * math.sin(q * 6), 0.2), yaw=-0.3, angry=0.2,
             gape=0.3 * abs(math.sin(q * 9)))
        if second:
            drop(S_SUPER, O0 + Vector((0.5, 0.3, 2.75)), t - next(s for s, n in SHOTS if n == "date~2"), 0.15)
    elif name == "freezer":
        temp = -round(40 * smooth01(aq / 2.6))
        DISP.data.body = f"{temp}°C"
        flakes(q, FZ + Vector((0, 0, 0.35)), 2.0, 2.0, FLAKES, FLAKE_P)
        pose(BT, FZ + Vector((0, -0.1, 0.3)), arm=(0.5, 0.5), sway=0.035 * math.sin(q * 40) * smooth01(aq / 1.5),
             angry=-0.6, gape=0.2 * abs(math.sin(q * 35)))
        if second:
            drop(S_LIQ, O1 + Vector((-0.5, -1.2, 2.95)), t - next(s for s, n in SHOTS if n == "freezer~2"), 0.1)
    elif name in ("tap", "site"):
        top = O2 + Vector((0.6, 0.1, 1.03))
        cap = top + Vector((0.06, -0.03, 1.83))
        if name == "tap":
            fall = smooth01(aq / 0.55) ** 2
            SPECK.location = cap + Vector((0, 0, 2.6 * (1 - fall))) if aq < 0.55 else cap
            t2 = next(s for s, n in SHOTS if n == "tap~2")
            f = smooth01((t - t2) / 1.0) if second else 0.0
            pose(BT, top, arm=(0.3 + 1.2 * f, 0.3 + 1.2 * f), angry=-0.4 - 0.6 * f, gape=f,
                 sway=0.08 * math.sin(q * 30) * (1 - f) if aq > 0.55 and not second else 0.0, frozen=f)
        else:
            SPECK.location = cap
            pop(LENS, cap + Vector((-0.55, -0.45, 0.0)), aq, 0.0, 0.5)
            pop(BIGSPECK, cap + Vector((-0.55, -0.5, 0.0)), aq, 0.1, 0.5)
            drop(S_SITE, O2 + Vector((-0.4, 0.2, 3.35)), aq, 0.2)
            pose(BT, top, arm=(1.5, 1.5), angry=-1.0, gape=1.0, frozen=1.0)
    elif name == "plane":
        t2 = next(s for s, n in SHOTS if n == "plane~2")
        clap = second
        f = smooth01((t - t2 - 0.25) / 0.3) if clap else 0.0
        pose(BT, O3 + Vector((-0.6, 0.3, 0.73)), scale=0.75, arm=(0.3, 0.4 + 1.0 * f), yaw=0.2, angry=-0.8 if not clap else -1.0,
             gape=f, frozen=f)
        c = abs(math.sin(q * 18)) if clap else 0.0
        pose(MG, O3 + Vector((0.6, 0.3, 0.73)), scale=0.85, arm=(1.0 + 0.5 * c, 1.0 + 0.5 * c), yaw=-0.25, angry=0.5,
             gape=0.6 if clap else 0.1, hop=0.04 * c)
        if clap:
            drop(S_ICK, O3 + Vector((0, -0.4, 3.05)), t - t2, 0.4)
    elif name == "chart":
        for i, b in enumerate(BARS):
            h = 3.0 * PCT[i] * smooth01((aq - 0.3 - i * 0.4) / 0.35)
            b.location = O4 + Vector((BAR_X[i], 0, 0.12 + h / 2))
            b.scale = (1, 1, max(0.01, h))
            if h > 0.05:
                BARP[i].location = O4 + Vector((BAR_X[i], -0.4, 0.12 + h + 0.25))
        pose(BT, O4 + Vector((-1.75, -1.0, 0)), scale=0.8, frozen=1.0, angry=-0.6, yaw=0.3, arm=(0.2, 0.2))
        pose(MG, O4 + Vector((1.75, -1.0, 0)), scale=0.8, angry=-0.5, yaw=-0.3, arm=(0.3, 0.3), gape=0.4)
    elif name == "door":
        slide = smooth01((aq - 0.3) / 0.6)
        shut = smooth01((aq - 0.9) / 0.2)
        DOOR5.rotation_euler = (0, 0, -1.2 * (1 - shut))
        if slide < 1:
            pose(BT, O5 + Vector((-0.5 + 1.4 * slide, -0.3 + 1.9 * slide, 0)), frozen=1.0, angry=0.6, yaw=0.0, arm=(0.1, 0.1))
        pose(MG, O5 + Vector((-1.3, -0.9, 0)), angry=-1.0, yaw=0.25, arm=(0.2, 0.8 + 0.3 * math.sin(q * 6)), gape=0.5)
        if aq > 1.0:
            drop(S_SPOT, O5 + Vector((-0.6, 0.3, 2.95)), aq, 1.0)
    elif name == "final":
        pose(BT, O6 + Vector((0, 0.2, 0.7)), frozen=1.0, shades=True, angry=0.5, arm=(0.2, 1.4), hop=0.04 * abs(math.sin(q * 6)))
        drop(S_PHYS, O6 + Vector((0, -0.2, 3.55)), aq, 0.3)
        for i, s in enumerate(SPARK):
            a = i / len(SPARK) * 2 * math.pi + q
            s.location = O6 + Vector((math.cos(a) * 1.0, -0.3, 1.6 + math.sin(a) * 0.9))

B.render_settings(FPS, samples=int(os.environ.get("ICK_SAMPLES", "12")), motion_blur=0.0)
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
