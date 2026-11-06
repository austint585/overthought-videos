"""Blender scene for Always Cold (render_cold.py). Toon kit (toon.py). Cast: your always cold friend (thin sweater, scarf,
later a borrowed orange hoodie) and a grumpy wall thermostat. Sets along x, 40 m apart: an office with ceiling vents and snow
drifting down, the 2019 Berlin test room (six desks, a giant thermometer), and two giant pencils as a bar chart (women and men).
Stop motion at 12 steps a second for props, smooth camera. Helpers from hibern_scene.py.

blender -b --factory-startup -P cold_scene.py -- timing.json out_dir MODE   (MODE: all or 1-based frame list)
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
    return Vector((i * 40.0, 0, 0))

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

SCREEN, PHONE, ROCK, CRATER, EARTH, LAND, SUN, ROAD = (0.30, 0.75, 1.0), (0.12, 0.12, 0.16), (0.62, 0.60, 0.58), (0.45, 0.43, 0.42), \
    (0.20, 0.48, 0.92), (0.30, 0.72, 0.30), (1.0, 0.80, 0.22), (0.30, 0.30, 0.34)
SKY, GRASS, LILAC = (0.45, 0.72, 0.95), (0.35, 0.68, 0.28), (0.42, 0.24, 0.62)


SKIN, SWEAT, HOOD, FROST, BEIGE = (0.93, 0.72, 0.55), (0.42, 0.30, 0.70), (0.95, 0.45, 0.15), (0.80, 0.93, 1.0), (0.90, 0.86, 0.74)
PENW, PENM, LEAD = (0.95, 0.35, 0.55), (0.25, 0.55, 0.95), (0.20, 0.20, 0.22)

def friend(name):
    """Your always cold friend: a person in a thin purple sweater, a scarf, and a hoodie that can appear over it. z=0 at feet."""
    root = K.empty(name)
    body = K.empty(name + "b", (0, 0, 0), root)
    K.cyl(name + "t", 0.34, 0.8, SWEAT, (0, 0, 0.75), body, seg=40)
    K.ball(name + "head", 0.3, SKIN, (0, 0, 1.42), body)
    K.ball(name + "hair", 0.31, (0.30, 0.18, 0.10), (0, 0.06, 1.5), body, squash=(1.02, 1.0, 0.8))
    K.cyl(name + "scarf", 0.27, 0.12, RED, (0, 0, 1.16), body, seg=32, line=0.006)
    hood = K.empty(name + "hood", AWAY, body)
    K.cyl(name + "hb", 0.39, 0.82, HOOD, (0, 0, 0.75), hood, seg=40)
    K.ball(name + "hh", 0.36, HOOD, (0, 0.08, 1.45), hood, squash=(1.0, 0.95, 1.05))
    K.box(name + "pocket", (0.4, 0.05, 0.16), (0.85, 0.38, 0.1), (0, -0.39, 0.6), hood, bevel=0.03, line=0.006)
    parts = {"root": root, "body": body, "hood": hood}
    face(name, K.empty(name + "fc", (0, 0, 0), body), 0.3, 1.42, parts, eye=0.065, gap=0.1)
    for s, k in ((-1, "L"), (1, "R")):
        arm = K.empty(name + "arm" + k, (s * 0.34, 0, 1.0), body)
        K.box(name + "armb" + k, (0.3, 0.13, 0.12), SWEAT, (s * 0.14, 0, 0), arm, bevel=0.04)
        K.ball(name + "hand" + k, 0.07, SKIN, (s * 0.3, 0, 0), arm)
        parts["arm" + k] = arm
        leg = K.empty(name + "leg" + k, (s * 0.15, 0, 0.36), root)
        K.box(name + "legb" + k, (0.14, 0.16, 0.36), DARK, (0, 0, -0.18), leg, bevel=0.03)
        parts["leg" + k] = leg
    return parts

def thermostat(name):
    """The wall thermostat: a beige box with a round dial, a number on it and a face. Faces -y."""
    root = K.empty(name)
    K.box(name + "c", (1.3, 0.25, 1.5), BEIGE, (0, 0, 0), root, bevel=0.12)
    K.cyl(name + "d", 0.42, 0.06, WHITE, (0, -0.15, -0.1), root, rot=(math.pi / 2, 0, 0), seg=48)
    num = K.label(name + "n", "68°", 0.32, K.INK, (0, -0.2, -0.12), root)
    parts = {"root": root, "num": num}
    for s, k in ((-1, "L"), (1, "R")):
        K.ball(name + "eye" + k, 0.09, (0.99, 0.98, 0.94), (s * 0.26, -0.13, 0.45), root, squash=(1, 0.35, 1), line=0.006)
        K.ball(name + "pup" + k, 0.04, K.INK, (s * 0.25, -0.16, 0.44), root, squash=(1, 0.3, 1), line=0)
        brow = K.empty(name + "br" + k, (s * 0.26, -0.15, 0.6), root)
        K.box(name + "brow" + k, (0.22, 0.02, 0.05), K.INK, (0, 0, 0), brow, bevel=0.005, line=0)
        parts["brow" + k] = brow
    knob = K.empty(name + "kn", (0, -0.2, -0.1), root)
    K.box(name + "kp", (0.05, 0.03, 0.3), RED, (0, 0, 0.22), knob, bevel=0.01, line=0.005)
    parts["knob"] = knob
    return parts

def desk(name, at, paper=True):
    root = K.empty(name, at)
    K.box(name + "t", (1.0, 0.7, 0.08), WOOD, (0, 0, 0.75), root, bevel=0.02)
    for x in (-0.44, 0.44):
        K.box(f"{name}l{x}", (0.06, 0.6, 0.72), DARK, (x, 0, 0.36), root, bevel=0, line=0.005)
    if paper:
        K.box(name + "p", (0.42, 0.55, 0.012), WHITE, (0, -0.02, 0.8), root, bevel=0, line=0.004).rotation_euler = (0, 0, 0.08)
        for j in range(3):
            K.box(f"{name}pl{j}", (0.3, 0.02, 0.005), GREY, (0, 0.12 - j * 0.12, 0.81), root, bevel=0, line=0)
    return root

def pencil(name, color):
    """A giant pencil standing on its eraser end, point up; scale z to grow. z=0 at the floor."""
    root = K.empty(name)
    shaft = K.empty(name + "s", (0, 0, 0), root)
    K.cyl(name + "e", 0.32, 0.3, PINK if color != PINK else (0.98, 0.6, 0.7), (0, 0, 0.15), shaft, seg=6)
    K.cyl(name + "f", 0.33, 0.14, GREY, (0, 0, 0.37), shaft, seg=6, line=0.006)
    K.cyl(name + "b", 0.32, 1.0, color, (0, 0, 0.94), shaft, seg=6)
    tip = K.empty(name + "tip", (0, 0, 1.44), root)
    K.cyl(name + "w", 0.32, 0.45, (0.95, 0.80, 0.55), (0, 0, 0.225), tip, seg=6, r2=0.08)
    K.cyl(name + "l", 0.08, 0.12, LEAD, (0, 0, 0.5), tip, seg=6, r2=0.0, line=0.004)
    return {"root": root, "shaft": shaft, "tip": tip}

def thermometer(name, at):
    root = K.empty(name, at)
    K.box(name + "bd", (0.7, 0.12, 3.4), WHITE, (0, 0, 1.7), root, bevel=0.1)
    K.box(name + "tube", (0.16, 0.06, 2.8), (0.85, 0.88, 0.9), (0, -0.07, 1.85), root, bevel=0.06, line=0.005)
    K.ball(name + "bulb", 0.2, RED, (0, -0.07, 0.35), root, squash=(1, 0.5, 1))
    col = K.empty(name + "col", (0, -0.09, 0.45), root)
    K.box(name + "cb", (0.1, 0.05, 1.0), RED, (0, 0, 0.5), col, bevel=0.03, line=0)
    for j in range(7):
        K.box(f"{name}tk{j}", (0.12, 0.02, 0.02), K.INK, (0.22, -0.07, 0.6 + j * 0.38), root, bevel=0, line=0)
    return root, col

# ------------------------------------------------------------------ 0 the office, cold

O0 = stage(0, (0.62, 0.78, 0.90), (0.50, 0.52, 0.58))
DESK0 = desk("desk0", O0 + Vector((1.3, -0.2, 0)), paper=False)
K.box("mon", (0.7, 0.08, 0.5), DARK, O0 + Vector((1.3, 0.0, 1.13)), bevel=0.03)
K.box("mons", (0.6, 0.02, 0.4), SCREEN, O0 + Vector((1.3, -0.045, 1.13)), bevel=0, line=0).data.materials[0] = K.flat(SCREEN)
K.box("monst", (0.08, 0.08, 0.2), DARK, O0 + Vector((1.3, 0.0, 0.88)), bevel=0, line=0.004)
MUG = K.cyl("mug", 0.09, 0.2, WHITE, O0 + Vector((1.0, -0.35, 0.9)), seg=24)
for k in range(3):
    K.box(f"vent{k}", (1.6, 0.06, 0.05), GREY, O0 + Vector((-1.3, 2.0, 4.6 - k * 0.12)), bevel=0, line=0.004)
TH = thermostat("th")
TH["root"].location = O0 + Vector((-1.6, 1.95, 3.0))
SNOW = [K.ball(f"sn{k}", 0.05, FROST, AWAY, line=0) for k in range(14)]
for s in SNOW:
    s.data.materials[0] = K.flat(FROST)
S_SCI = K.sign("s_sci", ["SCIENCE"], AWAY, w=1.4, head="SHE HAS")
S_GRADE = K.sign("s_grade", ["MATH GRADE"], AWAY, w=2.0, head="PROTECTING HER")
S_HEAT = K.sign("s_heat", ["FOR SCIENCE"], AWAY, w=2.0, head="TURN IT UP")
HOODIE = K.empty("hoodie", AWAY)
K.box("hdb", (0.7, 0.2, 0.8), HOOD, (0, 0, 0), HOODIE, bevel=0.1)
K.ball("hdh", 0.25, HOOD, (0, 0.05, 0.5), HOODIE, squash=(1, 0.7, 0.8))

# ------------------------------------------------------------------ 1 the Berlin test room

O1 = stage(1, (0.98, 0.93, 0.80), (0.62, 0.48, 0.32))
DESKS = []
for r in range(2):
    for c in range(3):
        DESKS.append(desk(f"dk{r}{c}", O1 + Vector((-1.4 + c * 1.4, -0.4 - r * 1.3, 0))))
STUDS = []
for k, d in enumerate(DESKS):
    p = K.empty(f"st{k}", d.location + Vector((0, 0.45, 0)))
    K.cyl(f"stb{k}", 0.22, 0.6, (BLUE, PINK, GREEN, ORANGE, TEAL, LILAC)[k], (0, 0, 0.75), p, seg=24)
    K.ball(f"sth{k}", 0.2, SKIN, (0, 0, 1.22), p)
    K.ball(f"sthr{k}", 0.205, ((0.3, 0.18, 0.1), K.INK, (0.85, 0.6, 0.25))[k % 3], (0, 0.05, 1.3), p, squash=(1, 1, 0.75))
    STUDS.append(p)
TM, TM_COL = thermometer("tm", O1 + Vector((2.9, 1.9, 0.3)))
S_STUD = K.sign("s_stud", ["543 STUDENTS"], AWAY, w=2.4, head="BERLIN, 2019")
S_RANGE = K.sign("s_range", ["61°F", "TO 91°F"], AWAY, w=1.3, head="ROOMS")
S_MATH = K.sign("s_math", ["MATH TESTS"], AWAY, w=1.7, head="THEN")

# ------------------------------------------------------------------ 2 the pencils

O2 = stage(2, (0.30, 0.22, 0.45), (0.22, 0.20, 0.30))
for k in range(9):
    K.box(f"grid{k}", (8.0, 0.02, 0.02), (0.45, 0.40, 0.62), O2 + Vector((0, 2.0, 0.6 + k * 0.5)), bevel=0, line=0)
PW = pencil("pw", PENW)
PM = pencil("pm", PENM)
PW["root"].location = O2 + Vector((-0.9, 0.2, 0))
PM["root"].location = O2 + Vector((0.9, 0.2, 0))
K.label("lw", "WOMEN", 0.3, WHITE, O2 + Vector((-0.9, -0.5, 0.25)))
K.label("lm", "MEN", 0.3, WHITE, O2 + Vector((0.9, -0.5, 0.25)))
S_PCT = K.sign("s_pct", ["+1.76%", "PER °C"], AWAY, w=1.4, head="WOMEN")
S_SMALL = K.sign("s_small", ["TOO SMALL", "TO COUNT"], AWAY, w=1.9, head="MEN")

# ------------------------------------------------------------------ cast and camera

FR = friend("fr")
cam = B.camera(lens=40, fstop=16.0)
cam.data.dof.use_dof = False
cam.data.clip_start = 0.05
cam.data.clip_end = 80

def lc(a, b, tg, lens, u, o):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "cold": lambda u: lc((-0.2, -5.4, 2.3), (-0.1, -4.8, 2.2), (-0.4, 0, 2.0), 40, u, O0),
    "lab": lambda u: lc((0.0, -7.6, 3.2), (0.3, -7.0, 3.0), (0.3, 0, 1.6), 40, u, O1),
    "range": lambda u: lc((1.9, -4.8, 2.6), (2.1, -4.4, 2.5), (2.3, 0.5, 2.1), 40, u, O1),
    "math": lambda u: lc((-1.0, -3.6, 2.3), (-1.2, -3.2, 2.1), (-1.4, -0.4, 1.0), 40, u, O1),
    "women": lambda u: lc((-0.6, -6.2, 2.3), (-0.4, -5.6, 2.3), (-0.2, 0, 2.1), 40, u, O2),
    "men": lambda u: lc((0.8, -5.4, 2.1), (0.7, -5.0, 2.1), (0.6, 0, 1.9), 40, u, O2),
    "hoodie": lambda u: lc((0.4, -5.2, 2.3), (0.2, -4.7, 2.2), (0.0, 0, 2.0), 40, u, O0),
    "heat": lambda u: lc((-1.0, -4.2, 2.8), (-1.2, -3.8, 2.85), (-1.5, 1.5, 2.8), 40, u, O0),
    "final": lambda u: lc((0.2, -6.4, 2.6), (0.1, -5.8, 2.5), (0.0, 0, 1.9), 40, u, O0),
}

def shot_at(t):
    k = max([0] + [i for i, (s, _) in enumerate(SHOTS) if t >= s - 1e-6])
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    cut = max(0.0, min(1.0, (t - SHOTS[k][0]) / max(1e-6, t1 - SHOTS[k][0])))
    return SHOTS[k][1], t - SHOTS[k][0], cut, t1 - SHOTS[k][0]

def drop(ob, at, age, delay=0.0):
    u = max(0.0, age - delay) / 0.4
    z = 4.5 * max(0.0, 1 - u) ** 2 - (0.12 * math.sin(min(u, 2.0) * 6) * max(0.0, 1 - u / 2) if u > 1 else 0)
    ob.location = at + Vector((0, 0, z))

def pose(p, at, shiver=0.0, arm=(0.0, 0.0), angry=0.0, gape=0.0, yaw=0.0, hop=0.0):
    p["root"].location = at + Vector((shiver, 0, hop))
    p["root"].rotation_euler = (0, 0, yaw)
    p["armL"].rotation_euler = (0, -arm[0], 0)
    p["armR"].rotation_euler = (0, arm[1], 0)
    p["mouth"].scale = (1 - 0.4 * gape, 1, 1 + 3.0 * gape)
    p["shades"].location = AWAY
    K.mood(p, angry)

def th_mood(v):
    TH["browL"].rotation_euler = (0, 0.42 * v, 0)
    TH["browR"].rotation_euler = (0, -0.42 * v, 0)

def apply_state(t):
    name, age, cut, length = shot_at(t)
    q = math.floor(t * 12) / 12
    aq = age - (t - q)
    loc, tg, lens = CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    for o in [FR["root"], S_SCI, S_GRADE, S_HEAT, HOODIE, S_STUD, S_RANGE, S_MATH, S_PCT, S_SMALL] + SNOW:
        o.location = AWAY
    FR["hood"].location = AWAY
    th_mood(0.6)
    TH["knob"].rotation_euler = (0, -0.6, 0)
    if TH["num"].data.body != "68°":
        TH["num"].data.body = "68°"

    if name == "cold":                         # she shivers in the office, snow drifts down, the sign lands
        pose(FR, O0 + Vector((-0.2, -0.5, 0)), shiver=0.035 * math.sin(q * 40), arm=(-1.0, -1.0), angry=-0.8, gape=0.25)
        for k, s in enumerate(SNOW):
            ph = (t * 0.35 + k / len(SNOW)) % 1.0
            s.location = O0 + Vector((-2.4 + (k * 0.37) % 4.0, -0.8 + (k % 3) * 0.5, 4.2 - 4.0 * ph))
        drop(S_SCI, O0 + Vector((-0.25, -0.6, 2.75)), aq, 0.6)
    elif name in ("lab", "range", "math"):
        for k, p in enumerate(STUDS):
            p.rotation_euler = (0.12 * abs(math.sin(q * 5 + k)) if name == "math" else 0, 0, 0)
        rise = smooth01((t - start_of("range") - 0.3) / 1.6) if name != "lab" else 0.0
        TM_COL.scale = (1, 1, max(0.05, 0.25 + 2.3 * rise))
        if name == "lab":
            drop(S_STUD, O1 + Vector((0.0, 0.6, 3.6)), aq, 0.4)
        elif name == "range":
            drop(S_RANGE, O1 + Vector((1.75, 0.2, 2.9)), aq, 0.3)
        else:
            drop(S_MATH, O1 + Vector((-1.3, -0.6, 1.98)), aq, 0.2)
    elif name in ("women", "men"):
        tw = start_of("women")
        steps = min(8, int(max(0.0, t - tw - 0.4) / 0.25)) if t >= tw else 0
        PW["root"].scale = (1, 1, 1.0 + 0.11 * steps)
        if name == "women":
            PM["root"].scale = (1, 1, 1.0)
            drop(S_PCT, O2 + Vector((0.45, -0.2, 3.0)), aq, 0.5)
        else:
            PW["root"].scale = (1, 1, 1.88)
            PM["root"].scale = (1, 1, 1.0 - 0.03 * smooth01(aq / 0.6))
            PM["root"].rotation_euler = (0, 0.05 * math.sin(q * 9) * max(0.0, 1 - aq), 0)
            drop(S_SMALL, O2 + Vector((0.6, -0.2, 3.25)), aq, 0.3)
    elif name in ("hoodie", "heat", "final"):
        warm = name != "hoodie" or aq > 0.5
        if name == "hoodie":
            u = smooth01(aq / 0.5)
            if u < 1:
                HOODIE.location = O0 + Vector((-2.5 + 2.3 * u, -0.5, 2.8 + 1.2 * math.sin(u * math.pi)))
                HOODIE.rotation_euler = (0, 6.0 * u, 0)
            drop(S_GRADE, O0 + Vector((0.0, -0.6, 3.4)), aq, 0.7)
        if warm:
            FR["hood"].location = (0, 0, 0)
        pose(FR, O0 + Vector((-0.2, -0.5, 0)), shiver=0.0 if warm else 0.03 * math.sin(q * 40),
             arm=(0.6, 0.6) if warm else (-1.0, -1.0), angry=0.0 if warm else -0.8, gape=0.0,
             hop=0.06 * abs(math.sin(q * 6)) if name == "final" else 0.0)
        if name in ("heat", "final"):
            kk = smooth01((t - start_of("heat") - 0.3) / 0.8)
            TH["knob"].rotation_euler = (0, -0.6 + 1.4 * kk, 0)
            deg = int(round(68 + 9 * kk))
            if TH["num"].data.body != f"{deg}°":
                TH["num"].data.body = f"{deg}°"
            th_mood(-0.6 * kk + 0.6 * (1 - kk))
            if name == "heat":
                drop(S_HEAT, O0 + Vector((-1.5, 0.8, 4.3)), aq, 0.5)

def start_of(n):
    return next(s for s, m in SHOTS if m == n)

B.render_settings(FPS, samples=int(os.environ.get("CO_SAMPLES", "12")), motion_blur=0.0)
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
