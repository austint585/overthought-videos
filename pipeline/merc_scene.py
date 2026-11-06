"""Blender scene for Mercury Retrograde (render_merc.py). Cast: a smartphone with a face (your friend) and a little grey
Mercury with a face. Sets along x, 14 m apart: bed, sky, orbit, cal, count, road. Stop motion at 12 steps a second,
smooth camera. Built from q36_scene.py.

blender -b --factory-startup -P merc_scene.py -- timing.json out_dir MODE   (MODE: all or 1-based frame list)
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

def phone(name):
    """Your friend: a dark phone slab with a glowing screen, the face on the screen, stubby limbs. z=0 at the feet."""
    root = K.empty(name)
    body = K.empty(name + "b", (0, 0, 0.30), root)
    K.box(name + "slab", (0.72, 0.14, 1.3), PHONE, (0, 0, 0.65), body, bevel=0.1)
    scr = K.box(name + "scr", (0.6, 0.02, 1.1), SCREEN, (0, -0.07, 0.67), body, bevel=0.06, line=0)
    scr.data.materials[0] = K.flat(SCREEN)
    K.box(name + "notch", (0.16, 0.02, 0.04), PHONE, (0, -0.085, 1.15), body, bevel=0.01, line=0)
    parts = {"root": root, "body": body}
    face(name, body, 0.075, 0.8, parts, eye=0.08, gap=0.14)
    limbs(name, root, body, parts, (0.22, 0.22, 0.28), 0.36, 0.6, 0.15)
    return parts

def planet(name, r=0.45):
    """Mercury: a grey ball with craters and a face. Its origin is its centre."""
    root = K.empty(name)
    body = K.empty(name + "b", (0, 0, 0), root)
    K.ball(name + "ball", r, ROCK, (0, 0, 0), body)
    for i, (a, z, cr) in enumerate(((0.9, 0.25, 0.09), (2.2, -0.3, 0.12), (2.9, 0.4, 0.07), (-0.6, -0.15, 0.1), (1.6, 0.6, 0.06))):
        K.ball(f"{name}cr{i}", cr * r / 0.45, CRATER, (math.cos(a) * r * 0.93, math.sin(a) * r * 0.93, z * r), body, squash=(1, 1, 0.5), line=0)
    parts = {"root": root, "body": body}
    face(name, root, r, 0.05 * r, parts, eye=0.09 * r / 0.45, gap=0.15 * r / 0.45)
    return parts

def bubble(name, text, color=(0.2, 0.55, 1.0)):
    root = K.empty(name, AWAY)
    K.box(name + "b", (1.0, 0.06, 0.45), color, (0, 0, 0), root, bevel=0.12)
    K.label(name + "t", text, 0.2, WHITE, (0, -0.05, -0.02), root)
    return root

# ------------------------------------------------------------------ 0 bed: night, the text goes out

O0 = stage(0, LILAC, WOOD)
K.box("bedf", (3.4, 2.2, 0.5), (0.45, 0.25, 0.12), O0 + Vector((0, 0.8, 0.25)), bevel=0.05)
K.box("matt", (3.3, 2.1, 0.3), WHITE, O0 + Vector((0, 0.8, 0.62)), bevel=0.08)
K.box("blanket", (3.32, 1.3, 0.12), PINK, O0 + Vector((0, 0.35, 0.83)), bevel=0.05)
K.box("pillow", (1.1, 0.5, 0.3), CREAM, O0 + Vector((-0.9, 1.6, 0.92)), bevel=0.12)
K.box("headb", (3.4, 0.2, 1.6), (0.45, 0.25, 0.12), O0 + Vector((0, 1.95, 0.8)), bevel=0.05)
K.box("winf", (1.6, 0.1, 1.4), CREAM, O0 + Vector((1.8, 2.0, 3.0)), bevel=0.03)
K.box("winp", (1.4, 0.05, 1.2), NAVY, O0 + Vector((1.8, 1.93, 3.0)), bevel=0, line=0)
for k in range(5):
    random.seed(k + 7)
    K.ball(f"wst{k}", 0.025, CREAM, O0 + Vector((1.8 + random.uniform(-0.6, 0.6), 1.88, 3.0 + random.uniform(-0.5, 0.5))), line=0)
WINMERC = K.ball("winmerc", 0.09, ROCK, O0 + Vector((2.2, 1.87, 3.3)), line=0.006)
K.cyl("lampn", 0.18, 0.5, GOLD, O0 + Vector((-2.4, 1.2, 0.95)), seg=20, r2=0.1)
TEXTS0 = [bubble("tx0", "u up?"), bubble("tx1", "miss u")]
S_SENT = K.sign("s_sent", ["SENT"], AWAY, w=1.5, head="11:58 PM")
S_BLAME = K.sign("s_blame", ["MERCURY"], AWAY, w=2.1, head="WHOSE FAULT")

# ------------------------------------------------------------------ 1 sky: the backwards loop

O1 = stage(1, NAVY, (0.10, 0.22, 0.14))
for k, (x, r) in enumerate(((-4.0, 3.0), (0.5, 2.4), (4.5, 3.2))):
    K.ball(f"hill{k}", r, (0.12, 0.30, 0.18), O1 + Vector((x, 1.2 - k * 0.1, -r * 0.55)), squash=(1, 0.4, 1), line=0.01)
for k in range(26):
    random.seed(200 + k)
    K.ball(f"sst{k}", random.uniform(0.02, 0.045), CREAM, O1 + Vector((random.uniform(-5, 5), 2.0, random.uniform(1.5, 8.5))), line=0)
TRAIL = [K.ball(f"trail{k}", 0.05, GOLD, AWAY, line=0) for k in range(40)]
S_RETRO = K.sign("s_retro", ["RETROGRADE"], AWAY, w=2.5, head="RIGHT NOW")

def loop_xz(s):
    """Mercury's path across the sky: forward, a small loop backwards, forward again."""
    return Vector((-2.0 + 4.0 * s + 0.75 * math.sin(2 * math.pi * s), 0.6, 2.1 + 0.45 * math.sin(2 * math.pi * s - 0.4) + 0.4 * s))

# ------------------------------------------------------------------ 2 orbit: the Sun, Mercury lapping Earth

O2 = stage(2, (0.05, 0.06, 0.14), (0.08, 0.09, 0.18))
SUNB = K.ball("sunb", 0.6, SUN, O2 + Vector((0, 0.4, 1.6)), line=0.01)
SUNB.data.materials[0] = K.flat(SUN)
RM, RE = 1.25, 2.3
for k in range(36):
    a = k / 36 * 2 * math.pi
    K.ball(f"om{k}", 0.02, GREY, O2 + Vector((math.cos(a) * RM, 0.4 + math.sin(a) * RM, 1.6)), line=0)
for k in range(56):
    a = k / 56 * 2 * math.pi
    K.ball(f"oe{k}", 0.02, GREY, O2 + Vector((math.cos(a) * RE, 0.4 + math.sin(a) * RE, 1.6)), line=0)
EARTHO = K.empty("earth", AWAY)
K.ball("earthb", 0.28, EARTH, (0, 0, 0), EARTHO)
for k, (a, z) in enumerate(((0.5, 0.1), (2.4, -0.1), (4.0, 0.15))):
    K.ball(f"land{k}", 0.12, LAND, (math.cos(a) * 0.2, math.sin(a) * 0.2, z), EARTHO, squash=(1, 1, 0.5), line=0)
SIGHT = [K.ball(f"sight{k}", 0.025, (1.0, 0.4, 0.4), AWAY, line=0) for k in range(10)]
S_LAPS = K.sign("s_laps", ["IT LAPS US"], AWAY, w=2.3, head="ILLUSION")
for k in range(20):
    random.seed(300 + k)
    K.ball(f"ost{k}", 0.025, CREAM, O2 + Vector((random.uniform(-5, 5), 2.0, random.uniform(1.0, 8.0))), line=0)

# ------------------------------------------------------------------ 3 cal: the three retrogrades of 2026

O3 = stage(3, GOLD, (0.55, 0.36, 0.12))
K.box("calb", (3.4, 0.08, 2.5), WHITE, O3 + Vector((0, 2.0, 3.0)), bevel=0.04)
K.box("calh", (3.4, 0.09, 0.35), RED, O3 + Vector((0, 1.94, 4.1)), bevel=0.03, line=0)
K.label("calt", "2026", 0.24, WHITE, O3 + Vector((0, 1.88, 4.1)))
MONTHS = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()
MARKS = []
for i, m in enumerate(MONTHS):
    cx, cz = -1.2 + (i % 4) * 0.8, 3.55 - (i // 4) * 0.7
    K.box(f"cell{i}", (0.72, 0.03, 0.6), CREAM, O3 + Vector((cx, 1.94, cz)), bevel=0.02, line=0.006)
    K.label(f"cellt{i}", m, 0.14, K.INK, O3 + Vector((cx, 1.91, cz + 0.17)))
    if m in ("FEB", "MAR", "JUN", "JUL", "OCT", "NOV"):
        MARKS.append(K.box(f"mark{i}", (0.6, 0.02, 0.18), RED, AWAY, bevel=0.02, line=0))
        MARKS[-1]["home"] = O3 + Vector((cx, 1.90, cz - 0.1))
S_66 = K.sign("s_66", ["66 DAYS"], AWAY, w=1.6, head="THIS YEAR")

# ------------------------------------------------------------------ 4 count: the other 299

O4 = stage(4, TEAL, (0.06, 0.30, 0.30))
K.box("cntb", (2.6, 0.08, 0.9), DARK, O4 + Vector((0, 2.0, 3.4)), bevel=0.04)
CNT = K.label("cnt", "DAY 0", 0.42, (0.4, 1.0, 0.5), O4 + Vector((0, 1.94, 3.4)))
TEXTS4 = [bubble(f"tf{k}", ["u up?", "hey", "miss u", "wyd", "hi", "??"][k % 6]) for k in range(6)]
S_ANY = K.sign("s_any", ["ANYWAY"], AWAY, w=2.0, head="TEXTED THE EX")

# ------------------------------------------------------------------ 5 road: Mercury goes forward

O5 = stage(5, SKY, GRASS)
K.box("road", (2.2, 12, 0.04), ROAD, O5 + Vector((0, -2.5, 0.02)), bevel=0, line=0)
for k in range(6):
    K.box(f"dash{k}", (0.12, 0.7, 0.02), WHITE, O5 + Vector((0, -6.5 + k * 1.6, 0.05)), bevel=0, line=0)
K.box("fpost", (0.1, 0.1, 2.6), GREY, O5 + Vector((-1.9, 1.0, 1.3)), bevel=0, line=0.006)
K.box("farrow", (1.4, 0.08, 0.5), GREEN, O5 + Vector((-1.5, 0.95, 2.4)), bevel=0.03)
K.label("farrowt", "FORWARD", 0.2, WHITE, O5 + Vector((-1.5, 0.88, 2.4)))
for k, x in enumerate((-4.5, 3.6, 5.0)):
    K.cyl(f"trunk{k}", 0.12, 1.0, WOOD, O5 + Vector((x, 1.4, 0.5)), seg=12)
    K.ball(f"tree{k}", 0.7, (0.2, 0.55, 0.22), O5 + Vector((x, 1.4, 1.5)))
S_TRY = K.sign("s_try", ["TRY IT"], AWAY, w=1.8, head="YOUR FRIEND")

# ------------------------------------------------------------------ the cast and the camera

PH = phone("ph")
ME = planet("me")
PH["shades"]["home"] = PH["shades"].location.copy()
ME["shades"].location = AWAY
cam = B.camera(lens=40, fstop=16.0)
cam.data.dof.use_dof = False
cam.data.clip_start = 0.05
cam.data.clip_end = 80

def lc(a, b, tg, lens, u, o):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "bed": lambda u: lc((-0.3, -6.8, 2.4), (0.0, -6.0, 2.3), (0, 0.4, 1.9), 40, u, O0),
    "sky": lambda u: lc((0.4, -7.4, 2.0), (0.1, -6.6, 2.1), (0, 0, 2.4), 40, u, O1),
    "orbit": lambda u: lc((0.0, -6.0, 5.2), (0.2, -5.4, 4.8), (0, 0.4, 1.9), 40, u, O2),
    "cal": lambda u: lc((-0.3, -7.6, 2.4), (0.0, -6.8, 2.5), (0, 0, 2.3), 40, u, O3),
    "count": lambda u: lc((0.3, -7.0, 2.6), (0.0, -6.3, 2.6), (0, 0, 2.6), 40, u, O4),
    "road": lambda u: lc((0.8, -7.4, 1.6), (0.3, -6.6, 1.9), (0, 0, 1.6), 40, u, O5),
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


def pose(p, at, hop=0.0, sway=0.0, arm=(0.0, 0.0), scale=1.0, angry=0.0, yaw=0.0, gape=0.0, shades=False):
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

def start_of(n):
    return next(s for s, m in SHOTS if m == n)


def pose_me(at, scale=1.0, spin=0.0, angry=0.0, gape=0.0, yaw=0.0):
    ME["root"].location = at
    ME["root"].scale = (scale,) * 3
    ME["root"].rotation_euler = (0, 0, yaw)
    ME["body"].rotation_euler = (0, spin, 0)
    ME["mouth"].scale = (1 - 0.4 * gape, 1, 1 + 3.0 * gape)
    K.mood(ME, angry)

def fly(ob, a, b, u, arc=0.6):
    ob.location = a.lerp(b, u) + Vector((0, 0, arc * 4 * u * (1 - u)))

def apply_state(t):
    name, u, age, cut, second, length = shot_at(t)
    q = math.floor(t * 12) / 12            # props step in stop motion
    aq = age - (t - q)
    loc, tg, lens = CAMS[name](cut)
    if second and name != "bed":          # the second angle is a push in on the same set
        lens = 48
        tg = tg + Vector((0, 0, -0.3))
    B.aim(cam, loc, tg)
    cam.data.lens = lens

    for o in [PH["root"], ME["root"], S_SENT, S_BLAME, S_RETRO, S_LAPS, S_66, S_ANY, S_TRY, EARTHO] \
            + TEXTS0 + TEXTS4 + TRAIL + SIGHT + MARKS:
        o.location = AWAY
    WINMERC.scale = (1, 1, 1)

    if name == "bed":
        throw = smooth01(aq / 0.2)
        pose(PH, O0 + Vector((-0.4, 0.2, 0.89)), scale=0.85, arm=(0.3, 2.2 * (1 - throw) + 0.6), yaw=0.2, angry=0.5, gape=0.3,
             hop=0.04 * abs(math.sin(q * 6)))
        for k, b in enumerate(TEXTS0):
            v = (aq - k * 0.9) / 1.2
            if 0 <= v <= 1:
                fly(b, O0 + Vector((-0.1, 0.0, 2.2)), O0 + Vector((1.6, 1.4, 3.3)), v)
                b.scale = (1 - 0.6 * v,) * 3
        if second:
            a2 = t - start_of("bed~2")
            S_SENT.location = AWAY
            pose(PH, O0 + Vector((-0.4, 0.2, 0.89)), scale=0.85, arm=(0.2, 1.9 * smooth01(a2 / 0.3)), yaw=-0.5, angry=0.9, gape=0.4)
            WINMERC.scale = (1 + 0.4 * abs(math.sin(q * 6)),) * 3
    elif name == "sky":
        s = min(1.0, aq / max(1.0, length - 0.3))
        for k, d in enumerate(TRAIL):
            sk = k / len(TRAIL)
            if sk < s:
                d.location = O1 + loop_xz(sk)
        p = O1 + loop_xz(s)
        back = math.cos(2 * math.pi * s) < -0.5
        pose_me(p, scale=0.75, spin=-aq * 2, angry=-0.6 if back else 0.2, gape=0.3 if back else 0.0)
        if not second:
            drop(S_RETRO, O1 + Vector((0, 0.2, 4.4)), aq, 0.3)
    elif name == "orbit":
        wm, we = 1.6, 0.4                       # Mercury laps the slow Earth
        am, ae = -1.9 + aq * wm, -1.6 + aq * we
        pm = O2 + Vector((math.cos(am) * RM, 0.4 + math.sin(am) * RM, 1.6))
        pe = O2 + Vector((math.cos(ae) * RE, 0.4 + math.sin(ae) * RE, 1.6))
        pose_me(pm, scale=0.55, gape=0.2)
        EARTHO.location = pe
        EARTHO.rotation_euler = (0, 0, aq * 2)
        for k, d in enumerate(SIGHT):
            d.location = pe.lerp(pm, (k + 1) / (len(SIGHT) + 1))
        if not second:
            drop(S_LAPS, O2 + Vector((0, 1.6, 3.5)), aq, 0.3)
    elif name == "cal":
        for k, m in enumerate(MARKS):
            pop(m, m["home"], aq, 0.4 + 0.3 * k)
        pose(PH, O3 + Vector((-0.8, -1.2, 0)), scale=0.75, yaw=0.4, arm=(0.3, 1.5), gape=0.25 * abs(math.sin(q * 7)), angry=0.4)
        pose_me(O3 + Vector((0.8, -1.2, 0.5)), scale=0.85, yaw=-0.3, angry=-0.8, gape=0.1)
        drop(S_66, O3 + Vector((0, -0.5, 1.15)), aq, 2.0)
    elif name == "count":
        n = min(299, int(299 * smooth01(aq / max(0.5, length - 1.0))))
        CNT.data.body = f"DAY {n}"
        pose(PH, O4 + Vector((0, -0.8, 0)), scale=0.85, arm=(1.0 + 0.5 * math.sin(q * 20), 1.0 + 0.5 * math.cos(q * 20)), angry=0.8,
             gape=0.3 * abs(math.sin(q * 9)), hop=0.04 * abs(math.sin(q * 8)))
        for k, b in enumerate(TEXTS4):
            v = (aq * 1.1 + k / len(TEXTS4)) % 1.0
            side = -1 if k % 2 else 1
            fly(b, O4 + Vector((0, -0.8, 1.8)), O4 + Vector((side * 2.0, 0.5, 3.0 + 0.3 * (k % 3))), v, arc=0.8)
            b.scale = (0.8 - 0.4 * v,) * 3
        drop(S_ANY, O4 + Vector((0, 0.4, 4.6)), aq, 0.8)
    elif name == "road":
        go = min(aq * 0.55, 2.6)               # rolls forward down the road toward us
        pose_me(O5 + Vector((-0.2, 1.0 - go, 0.45)), scale=0.9, spin=go * 2.2, angry=-0.2)
        look = smooth01((aq - 0.5) / 0.5)
        pose(PH, O5 + Vector((1.0, -1.0, 0)), scale=0.8, yaw=-0.4 + 0.3 * look, arm=(0.2, 1.4 * look), angry=-0.5 * look, gape=0.4 * look)
        drop(S_TRY, O5 + Vector((0.3, 0.6, 3.6)), aq, 1.0)

B.render_settings(FPS, samples=int(os.environ.get("MERC_SAMPLES", "12")), motion_blur=0.0)
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
