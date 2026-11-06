"""Blender scene for No Shave November, Day 6 (render_shave.py). Cast: a potato with a face and stubble (your friend). Sets
along x, 40 m apart: bathroom mirror, macro of three hairs, giant ruler, four progress pics, November calendar, donation jar,
his own jar. Stop motion at 12 steps a second, smooth camera. Built from merc_scene.py.

blender -b --factory-startup -P shave_scene.py -- timing.json out_dir MODE   (MODE: all or 1-based frame list)
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

SKIN, SPOT, HAIR, TILE, PORCE, RULER = (0.80, 0.60, 0.36), (0.62, 0.43, 0.24), (0.10, 0.07, 0.06), (0.55, 0.82, 0.80), \
    (0.95, 0.95, 0.93), (0.98, 0.80, 0.15)

def potato(name):
    """Your friend: a lumpy potato with a face, stubble on the chin and stubby limbs. z=0 at the feet."""
    root = K.empty(name)
    body = K.empty(name + "b", (0, 0, 0.30), root)
    K.ball(name + "ball", 0.5, SKIN, (0, 0, 0.6), body, squash=(0.82, 0.72, 1.18))
    for i, (x, z, r) in enumerate(((0.25, 0.95, 0.05), (-0.3, 0.45, 0.06), (0.32, 0.3, 0.04), (-0.18, 1.1, 0.04))):
        K.ball(f"{name}sp{i}", r, SPOT, (x, -0.33, z), body, squash=(1, 0.4, 1), line=0)
    parts = {"root": root, "body": body}
    face(name, body, 0.345, 0.78, parts, eye=0.08, gap=0.13)
    limbs(name, root, body, parts, (0.66, 0.47, 0.26), 0.36, 0.55, 0.16)
    random.seed(11)
    stub = K.empty(name + "stub", (0, 0, 0), body)
    for k in range(34):                                   # the "beard": dots on the lower front of the body
        x = random.uniform(-0.26, 0.26)
        z = random.uniform(0.32, 0.56)
        if abs(x) < 0.1 and z > 0.5:
            continue
        e = 1 - (x / 0.41) ** 2 - ((z - 0.6) / 0.59) ** 2
        y = -0.36 * math.sqrt(max(0.05, e)) - 0.004
        K.ball(f"{name}h{k}", 0.012, HAIR, (x, y, z), stub, squash=(1, 0.5, 1.6), line=0)
    parts["stub"] = stub
    return parts

# ------------------------------------------------------------------ 0 bathroom: in the mirror

O0 = stage(0, TILE, (0.85, 0.85, 0.82))
for k in range(9):                                        # tile grout lines
    K.box(f"gx{k}", (13.5, 0.02, 0.03), (0.42, 0.66, 0.64), O0 + Vector((0, 2.04, 0.5 + k * 0.8)), bevel=0, line=0)
K.box("sinkc", (3.2, 1.2, 0.9), PORCE, O0 + Vector((0, 1.3, 0.45)), bevel=0.06)
K.cyl("tap", 0.06, 0.4, (0.75, 0.77, 0.8), O0 + Vector((0.0, 1.6, 1.1)), seg=16)
K.cyl("cup", 0.14, 0.32, PINK, O0 + Vector((-1.1, 1.2, 1.06)), seg=20)
for k, c in enumerate((BLUE, GREEN)):
    K.box(f"tb{k}", (0.04, 0.04, 0.5), c, O0 + Vector((-1.14 + k * 0.08, 1.2, 1.35)), rot=(0, 0.15 - 0.3 * k, 0), bevel=0.01, line=0.006)
K.box("razor", (0.5, 0.08, 0.06), GREY, O0 + Vector((1.0, 1.2, 0.94)), rot=(0, 0, 0.3), bevel=0.02)
K.box("razorh", (0.08, 0.2, 0.08), (0.2, 0.4, 0.85), O0 + Vector((1.22, 1.26, 0.95)), rot=(0, 0, 0.3), bevel=0.02)
K.box("dust", (0.3, 0.3, 0.02), (0.6, 0.6, 0.62), O0 + Vector((1.05, 1.2, 0.91)), bevel=0, line=0)   # dust on the razor shelf
S_BEARD = K.sign("s_beard", ["BEARD"], AWAY, w=1.7, head="HE CALLS IT")

# ------------------------------------------------------------------ 1 macro: three hairs growing out of skin

O1 = stage(1, (0.95, 0.80, 0.62), SKIN)
for k in range(20):
    random.seed(100 + k)
    K.ball(f"pore{k}", random.uniform(0.06, 0.12), SPOT, O1 + Vector((random.uniform(-4, 4), random.uniform(-4, 1.5), 0.0)),
           squash=(1, 1, 0.2), line=0)
HAIRS = []
for k, x in enumerate((-0.9, 0.0, 0.9)):
    K.ball(f"fol{k}", 0.16, SPOT, O1 + Vector((x, -0.5, 0.0)), squash=(1, 1, 0.25), line=0.006)
    h = K.empty(f"hair{k}", O1 + Vector((x, -0.5, 0.0)))
    K.cyl(f"hairc{k}", 0.07, 1.0, HAIR, (0, 0, 0.5), h, rot=(0, 0.1 * (k - 1), 0), seg=12, line=0.008)
    HAIRS.append(h)
S_RATE = K.sign("s_rate", ["1/3 MM"], AWAY, w=1.7, head="A DAY")

# ------------------------------------------------------------------ 2 ruler: two millimetres, then a centimetre

O2 = stage(2, PLUM, (0.30, 0.12, 0.26))
RUL = K.empty("rul", O2 + Vector((-1.5, 0.2, 0.0)))
K.box("rulb", (0.7, 0.12, 4.6), RULER, (0, 0, 2.3), RUL, bevel=0.03)
for k in range(12):                                       # one big tick per millimetre (the ruler is magnified)
    big = k % 5 == 0
    K.box(f"tick{k}", (0.32 if big else 0.18, 0.02, 0.035), K.INK, (0.35 - (0.16 if big else 0.09), -0.07, 0.25 + k * 0.36), RUL,
          bevel=0, line=0)
    if big:
        K.label(f"tl{k}", f"{k} MM", 0.14, K.INK, (-0.12, -0.075, 0.25 + k * 0.36), RUL)
ARROW = K.box("arrow", (0.9, 0.06, 0.08), RED, AWAY, bevel=0.02)
S_2MM = K.sign("s_2mm", ["2 MM"], AWAY, w=1.5, head="RIGHT NOW")
S_1CM = K.sign("s_1cm", ["1 CM"], AWAY, w=1.5, head="BY NOV 30")

# ------------------------------------------------------------------ 3 pics: four identical progress pics

O3 = stage(3, (0.98, 0.58, 0.52), (0.55, 0.30, 0.28))
K.box("bigph", (2.6, 0.16, 4.2), PHONE, O3 + Vector((0, 1.6, 2.5)), bevel=0.15)
K.box("bigsc", (2.3, 0.04, 3.8), WHITE, O3 + Vector((0, 1.5, 2.5)), bevel=0.06, line=0)
TILES = []
for k in range(4):
    cx, cz = -0.55 + (k % 2) * 1.1, 3.3 - (k // 2) * 1.5
    t = K.empty(f"tile{k}", AWAY)
    K.box(f"tileb{k}", (1.0, 0.03, 1.3), TILE, (0, 0, 0), t, bevel=0.03, line=0.006)
    K.ball(f"tilep{k}", 0.38, SKIN, (0, -0.03, -0.05), t, squash=(0.8, 0.2, 1.1), line=0.006)
    for s in (-1, 1):
        K.ball(f"tilee{k}{s}", 0.05, K.INK, (s * 0.1, -0.07, 0.12), t, squash=(1, 0.3, 1), line=0)
    K.label(f"tilel{k}", f"DAY {k + 3}", 0.12, K.INK, (0, -0.05, -0.52), t)
    t["home"] = O3 + Vector((cx, 1.47, cz))
    TILES.append(t)
S_PICS = K.sign("s_pics", ["4 PICS"], AWAY, w=1.6, head="PROGRESS")

# ------------------------------------------------------------------ 4 cal: November, day 30 circled

O4 = stage(4, GOLD, (0.55, 0.36, 0.12))
K.box("calb", (3.4, 0.08, 2.9), WHITE, O4 + Vector((0, 2.0, 3.0)), bevel=0.04)
K.box("calh", (3.4, 0.09, 0.35), RED, O4 + Vector((0, 1.94, 4.3)), bevel=0.03, line=0)
K.label("calt", "NOVEMBER", 0.22, WHITE, O4 + Vector((0, 1.88, 4.3)))
CELL = {}
for d in range(1, 31):
    i = d - 1                                             # Nov 1 2026 is a Sunday
    cx, cz = -1.38 + (i % 7) * 0.46, 3.8 - (i // 7) * 0.5
    K.box(f"cell{d}", (0.4, 0.03, 0.42), CREAM, O4 + Vector((cx, 1.94, cz)), bevel=0.02, line=0.005)
    K.label(f"cellt{d}", str(d), 0.15, K.INK, O4 + Vector((cx, 1.9, cz)))
    CELL[d] = O4 + Vector((cx, 1.86, cz))
TODAY = K.box("today", (0.4, 0.02, 0.42), GREEN, AWAY, bevel=0.02, line=0)
RING = K.empty("ring", AWAY)
for k in range(24):
    a = k / 24 * 2 * math.pi
    K.ball(f"ringd{k}", 0.035, RED, (math.cos(a) * 0.27, 0, math.sin(a) * 0.27), RING, line=0)

# ------------------------------------------------------------------ 5 jar: the real point, since 2009

O5 = stage(5, (0.30, 0.45, 0.75), (0.15, 0.22, 0.45))
K.box("table5", (3.0, 1.6, 0.9), WOOD, O5 + Vector((0, 0, 0.45)), bevel=0.05)
K.cyl("jar", 0.55, 1.1, (0.75, 0.90, 0.96), O5 + Vector((0, 0, 1.45)), seg=32)
K.cyl("jarlid", 0.58, 0.12, GREY, O5 + Vector((0, 0, 2.06)), seg=32)
K.box("jarlab", (0.9, 0.05, 0.4), CREAM, O5 + Vector((0, -0.55, 1.45)), bevel=0.02, line=0.005)
K.label("jarlabt", "CANCER RESEARCH", 0.09, K.INK, O5 + Vector((0, -0.59, 1.45)))
COINS = [K.cyl(f"coin{k}", 0.13, 0.03, GOLD, AWAY, rot=(math.pi / 2, 0, 0), seg=20, line=0.006) for k in range(6)]
S_2009 = K.sign("s_2009", ["SINCE 2009"], AWAY, w=2.1, head="NO SHAVE NOVEMBER")

# ------------------------------------------------------------------ 6 sweat: his own jar

O6 = stage(6, (0.82, 0.86, 0.90), (0.55, 0.58, 0.62))
K.cyl("jar6", 0.3, 0.6, (0.75, 0.90, 0.96), O6 + Vector((1.0, -0.6, 0.3)), seg=32)
K.box("jar6l", (0.5, 0.04, 0.22), CREAM, O6 + Vector((1.0, -0.91, 0.32)), bevel=0.02, line=0.005)
K.label("jar6lt", "HIS JAR", 0.08, K.INK, O6 + Vector((1.0, -0.94, 0.32)))
K.cyl("button6", 0.07, 0.02, RED, O6 + Vector((1.0, -0.6, 0.04)), seg=16, line=0.004)
DROP = K.ball("drop", 0.07, WATER, AWAY, squash=(1, 0.6, 1.5), line=0.006)

# ------------------------------------------------------------------ the cast and the camera

PO = potato("po")
PO["shades"]["home"] = PO["shades"].location.copy()
cam = B.camera(lens=40, fstop=16.0)
cam.data.dof.use_dof = False
cam.data.clip_start = 0.05
cam.data.clip_end = 80

def lc(a, b, tg, lens, u, o):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "mirror": lambda u: lc((0.3, -6.2, 2.2), (0.0, -5.4, 2.1), (0, 0, 1.4), 40, u, O0),
    "stroke": lambda u: lc((0.25, -3.0, 1.35), (0.1, -2.7, 1.3), (0, 0, 1.15), 40, u, O0),
    "macro": lambda u: lc((0.4, -5.2, 1.6), (0.1, -4.6, 1.4), (0, 0, 1.1), 40, u, O1),
    "ruler": lambda u: lc((0.2, -5.6, 2.0), (0.0, -5.0, 1.9), (-0.3, 0, 1.75), 40, u, O2),
    "pics": lambda u: lc((0.3, -6.4, 2.4), (0.0, -5.8, 2.4), (0, 0, 2.2), 40, u, O3),
    "cal": lambda u: lc((-0.3, -6.6, 2.6), (0.0, -5.9, 2.7), (0, 0, 2.6), 40, u, O4),
    "jar": lambda u: lc((0.4, -6.0, 2.4), (0.1, -5.3, 2.3), (0, 0, 1.9), 40, u, O5),
    "sweat": lambda u: lc((0.3, -3.6, 1.5), (0.1, -3.1, 1.45), (0.3, 0, 1.15), 40, u, O6),
}

def base_of(i):
    return SHOTS[i][1].split("~")[0]

def shot_at(t):
    k = max([0] + [i for i, (s, _) in enumerate(SHOTS) if t >= s - 1e-6])
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    cut = max(0.0, min(1.0, (t - SHOTS[k][0]) / max(1e-6, t1 - SHOTS[k][0])))
    return base_of(k), t - SHOTS[k][0], cut, "~" in SHOTS[k][1], t1 - SHOTS[k][0]

def drop(ob, at, age, delay=0.0):
    """A sign falling in on its cords with a little overshoot."""
    u = max(0.0, age - delay) / 0.4
    z = 4.5 * max(0.0, 1 - u) ** 2 - (0.12 * math.sin(min(u, 2.0) * 6) * max(0.0, 1 - u / 2) if u > 1 else 0)
    ob.location = at + Vector((0, 0, z))

def pop(ob, at, age, delay=0.0, s=1.0):
    u = max(0.0, age - delay) / 0.25
    k = 0.0 if u <= 0 else (1.0 + 0.25 * math.sin(min(u, 2.0) * math.pi) * max(0.0, 1 - u / 2) if u >= 1 else smooth01(u))
    ob.location = at if k > 0 else AWAY
    ob.scale = (max(0.001, k * s),) * 3

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

def apply_state(t):
    name, age, cut, second, length = shot_at(t)
    q = math.floor(t * 12) / 12            # props step in stop motion
    aq = age - (t - q)
    loc, tg, lens = CAMS[name](cut)
    if second and name == "ruler":         # pull up the ruler to the centimetre
        loc, tg = loc + Vector((0, -0.6, 1.1)), tg + Vector((0, 0, 1.1))
    elif second:                           # the second angle is a push in on the same set
        lens = 50
    B.aim(cam, loc, tg)
    cam.data.lens = lens

    for o in [PO["root"], S_BEARD, S_RATE, S_2MM, S_1CM, S_PICS, S_2009, ARROW, TODAY, RING, DROP] + TILES + COINS:
        o.location = AWAY
    PO["stub"].scale = (1, 1, 1)

    if name in ("mirror", "stroke"):
        rub = math.sin(q * 18)
        if name == "stroke":               # rubbing the stubble (it rasps)
            pose(PO, O0 + Vector((0, -0.1, 0)), arm=(0.2, 2.3 + 0.25 * rub), yaw=0.15 * rub, angry=-0.6, gape=0.0)
            drop(S_BEARD, O0 + Vector((-0.75, -0.3, 2.5)), aq, 0.5)
        else:                              # admiring himself, turning side to side
            pose(PO, O0 + Vector((0, -0.1, 0)), arm=(0.3, 1.2 + 0.9 * smooth01(aq / 0.4)), yaw=0.35 * math.sin(q * 3), angry=-0.8,
                 gape=0.15, hop=0.03 * abs(math.sin(q * 5)))
    elif name == "macro":
        g = smooth01(aq / max(0.5, length))
        for k, h in enumerate(HAIRS):
            h.scale = (1, 1, 0.3 + 1.2 * g + 0.08 * k)
        drop(S_RATE, O1 + Vector((0, 0.6, 2.55)), aq, 0.3)
    elif name == "ruler":
        mm = 10 if second else 2
        pose(PO, O2 + Vector((0.4, -0.4, 0)), scale=0.9, arm=(0.4, 1.0), yaw=-0.3, angry=-0.7 if not second else 0.6,
             gape=0.1 if not second else 0.35)
        ARROW.location = O2 + Vector((-1.5 + 0.75, 0.1, 0.25 + mm * 0.36 * smooth01(aq / 0.6)))
        drop(S_1CM if second else S_2MM, O2 + Vector((0.5, 0.2, 3.3 if second else 2.9)), aq, 0.4)
    elif name == "pics":
        for k, tl in enumerate(TILES):
            pop(tl, tl["home"], aq, 0.35 + 0.3 * k)
        pose(PO, O3 + Vector((0.9, -1.4, 0)), scale=0.8, arm=(0.3, 2.4), yaw=-0.4, angry=-0.9, gape=0.2 * abs(math.sin(q * 6)))
        drop(S_PICS, O3 + Vector((-0.9, -0.6, 1.2)), aq, 1.3)
    elif name == "cal":
        TODAY.location = CELL[6] + Vector((0, 0.03, 0))
        pop(RING, CELL[30] + Vector((0, -0.04, 0)), aq, 0.5)
        RING.rotation_euler = (0, 0, 0)
        pose(PO, O4 + Vector((1.2, -1.2, 0)), scale=0.75, yaw=0.4, arm=(0.3, 1.6), angry=0.2, gape=0.2)
    elif name == "jar":
        for k, c in enumerate(COINS):      # other people's coins drop in
            v = (aq - 0.6 - 0.35 * k) / 0.5
            if 0 <= v:
                c.location = O5 + Vector((-0.25 + 0.1 * k, -0.2, 2.9 - 1.85 * min(1.0, v) + 0.03 * k))
        drop(S_2009, O5 + Vector((0, 0.6, 3.6)), aq, 0.3)
    elif name == "sweat":
        side = math.sin(q * 4)
        pose(PO, O6 + Vector((0, 0, 0)), arm=(0.2, 0.3), yaw=0.25 * side, angry=-1.0, gape=0.1)
        for k in ("pupL", "pupR"):
            ob = bpy.data.objects["po" + k]
            ob.location.x = (-1 if k == "pupL" else 1) * 0.13 * 0.92 + 0.03 * side
        v = max(0.0, aq - 0.8) / 1.6
        if 0 < v < 1:
            DROP.location = O6 + Vector((0.36, -0.3, 1.75 - 0.6 * v))
    if name != "sweat":
        for k in ("pupL", "pupR"):
            bpy.data.objects["po" + k].location.x = (-1 if k == "pupL" else 1) * 0.13 * 0.92

B.render_settings(FPS, samples=int(os.environ.get("SHAVE_SAMPLES", "12")), motion_blur=0.0)
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
