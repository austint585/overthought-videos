"""Blender scene for 36 Questions (render_q36.py). Diner condiments as the cast: salt shaker (your friend), pepper
shaker (the date), ketchup bottle with a bow tie (the waiter). Sets along x, 14 m apart: booth, lab, clock, stare (night
bridge), fries, exit, final. Stop motion at 12 steps a second, smooth camera.

blender -b --factory-startup -P q36_scene.py -- timing.json out_dir MODE   (MODE: all or 1-based frame list)
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


SALT, PEPPER, KETCH, SILVER = (0.96, 0.96, 0.93), (0.22, 0.22, 0.26), (0.80, 0.08, 0.06), (0.75, 0.78, 0.82)
FRY, BASKET, CHECK, BOOTH, TABLE = (0.98, 0.80, 0.25), (0.85, 0.12, 0.12), (0.92, 0.92, 0.88), (0.78, 0.10, 0.12), (0.95, 0.95, 0.92)
LAMP, EXITG = (1.0, 0.85, 0.45), (0.15, 0.95, 0.35)

def shaker(name, color, cap=SILVER):
    """A shaker: rounded body, a domed cap with holes, face, stubby limbs. z=0 at the feet."""
    root = K.empty(name)
    body = K.empty(name + "b", (0, 0, 0.30), root)
    K.cyl(name + "body", 0.40, 1.0, color, (0, 0, 0.5), body, seg=48, r2=0.34)
    K.cyl(name + "cap", 0.36, 0.22, cap, (0, 0, 1.1), body, seg=48)
    K.ball(name + "dome", 0.36, cap, (0, 0, 1.2), body, squash=(1, 1, 0.45))
    for i in range(5):
        a = i / 5 * 2 * math.pi
        K.ball(f"{name}hole{i}", 0.035, K.INK, (math.cos(a) * 0.15, math.sin(a) * 0.15 - 0.02, 1.36), body, line=0)
    parts = {"root": root, "body": body}
    face(name, body, 0.37, 0.7, parts, eye=0.075, gap=0.14)
    limbs(name, root, body, parts, tuple(c * 0.85 for c in color), 0.38, 0.55, 0.14)
    return parts

def waiter(name):
    """The ketchup bottle: tall red body, white cap, a black bow tie."""
    root = K.empty(name)
    body = K.empty(name + "b", (0, 0, 0.30), root)
    K.cyl(name + "body", 0.40, 1.3, KETCH, (0, 0, 0.65), body, seg=48, r2=0.30)
    K.cyl(name + "neck", 0.22, 0.25, KETCH, (0, 0, 1.42), body, seg=32, r2=0.16)
    K.cyl(name + "cap", 0.17, 0.25, WHITE, (0, 0, 1.65), body, seg=32, r2=0.10)
    K.box(name + "lbl", (0.5, 0.02, 0.32), CREAM, (0, -0.39, 0.42), body, bevel=0.02, line=0.006)
    K.label(name + "lblt", "WAITER", 0.13, KETCH, (0, -0.41, 0.42), body)
    for sx in (-1, 1):
        K.cyl(f"{name}bow{sx}", 0.12, 0.05, DARK, (sx * 0.12, -0.34, 1.12), body, rot=(math.pi / 2, 0, 0), seg=3, line=0.006)
    K.ball(name + "knot", 0.05, DARK, (0, -0.37, 1.12), body, line=0.006)
    parts = {"root": root, "body": body}
    face(name, body, 0.35, 0.85, parts, eye=0.07, gap=0.13)
    limbs(name, root, body, parts, (0.65, 0.06, 0.05), 0.36, 0.75, 0.14)
    return parts

def heart(name, color, r=0.2, loc=(0, 0, 0), line=0.01):
    root = K.empty(name, loc)
    for s in (-1, 1):
        K.ball(f"{name}l{s}", r, color, (s * r * 0.62, 0, r * 0.35), root, squash=(1, 0.5, 1), line=line)
    K.cyl(name + "c", r * 1.38, r * 1.7, color, (0, 0, -r * 0.62), root, rot=(math.pi, 0, 0), line=line, seg=32, r2=0.0).scale = (1, 0.5, 1)
    return root

# ------------------------------------------------------------------ 0 booth: the diner, the laminated card

O0 = stage(0, TEAL, CHECK)
for k in range(9):
    K.box(f"chk{k}", (0.7, 0.7, 0.02), DARK, O0 + Vector((-5.6 + k * 1.4, -1.0, 0.01)), bevel=0, line=0)
K.box("boothback", (5.6, 0.7, 1.9), BOOTH, O0 + Vector((0, 1.6, 0.95)), bevel=0.12)
K.box("boothseat", (5.6, 1.0, 0.55), BOOTH, O0 + Vector((0, 1.1, 0.28)), bevel=0.1)
K.box("table0", (3.0, 1.2, 0.1), TABLE, O0 + Vector((0, 0.2, 1.1)), bevel=0.03)
K.cyl("tleg0", 0.12, 1.05, SILVER, O0 + Vector((0, 0.2, 0.53)), seg=16)
CARD = K.empty("card", O0 + Vector((0, -0.05, 1.16)))
K.box("cardb", (1.3, 0.04, 0.9), CREAM, (0, 0, 0.45), CARD, bevel=0.03)
K.label("cardt", "36 QUESTIONS", 0.2, K.INK, (0, -0.03, 0.70), CARD)
for k in range(4):
    K.box(f"cardl{k}", (0.95, 0.01, 0.03), GREY, (0, -0.03, 0.50 - k * 0.1), CARD, bevel=0, line=0)
GLINT = K.box("glint", (0.08, 0.01, 1.0), WHITE, AWAY, rot=(0, 0.5, 0), bevel=0, line=0)
K.cyl("mug0", 0.13, 0.25, CREAM, O0 + Vector((1.2, 0.35, 1.28)), seg=20)
S_FIRST = K.sign("s_first", ["FIRST DATE"], AWAY, w=2.3)
S_LAM = K.sign("s_lam", ["LAMINATED"], AWAY, w=2.2, head="SHE")

# ------------------------------------------------------------------ 1 lab: the 1997 study

O1 = stage(1, (0.86, 0.90, 0.95), (0.40, 0.43, 0.50))
for k, x in enumerate((-1.2, 1.2)):
    ch = K.empty(f"chair{k}", O1 + Vector((x, 0.2, 0)))
    K.box(f"chs{k}", (0.8, 0.8, 0.1), BLUE, (0, 0, 0.55), ch, bevel=0.02)
    K.box(f"chb{k}", (0.1, 0.8, 0.9), BLUE, ((-0.4 if k == 0 else 0.4), 0, 1.0), ch, bevel=0.02)
    for lx in (-0.32, 0.32):
        for ly in (-0.32, 0.32):
            K.box(f"chl{k}{lx}{ly}", (0.06, 0.06, 0.55), GREY, (lx, ly, 0.27), ch, bevel=0, line=0.006)
K.box("board1", (3.4, 0.06, 1.0), WHITE, O1 + Vector((0, 2.0, 3.0)), bevel=0.03)
K.label("board1t", "Q1: WHO WOULD YOU WANT AS A DINNER GUEST?", 0.12, BLUE, O1 + Vector((0, 1.95, 3.15)))
K.label("board1u", "Q2: WOULD YOU LIKE TO BE FAMOUS?", 0.12, BLUE, O1 + Vector((0, 1.95, 2.85)))
S_1997 = K.sign("s_1997", ["1997 STUDY"], AWAY, w=2.3, head="PSYCHOLOGY LAB")
S_CLOSE = K.sign("s_close", ["CLOSER THAN", "SMALL TALK"], AWAY, w=2.4, head="RESULT")

# ------------------------------------------------------------------ 2 clock: 45 minutes

O2 = stage(2, GOLD, (0.55, 0.36, 0.12))
CLK = K.empty("clk", O2 + Vector((0, 1.9, 3.6)))
K.cyl("clkr", 1.35, 0.15, DARK, (0, 0, 0), CLK, rot=(math.pi / 2, 0, 0), seg=64)
K.cyl("clkf", 1.2, 0.05, WHITE, (0, -0.1, 0), CLK, rot=(math.pi / 2, 0, 0), seg=64, line=0)
for k in range(12):
    a = k / 12 * 2 * math.pi
    K.box(f"clkt{k}", (0.06, 0.02, 0.18), K.INK, (math.sin(a) * 1.0, -0.14, math.cos(a) * 1.0), CLK, rot=(0, a, 0), bevel=0, line=0)
HAND_M = K.empty("handm", (0, -0.16, 0), CLK)
K.box("handmb", (0.06, 0.02, 0.9), K.INK, (0, 0, 0.42), HAND_M, bevel=0, line=0)
HAND_H = K.empty("handh", (0, -0.17, 0), CLK)
K.box("handhb", (0.09, 0.02, 0.55), RED, (0, 0, 0.25), HAND_H, bevel=0, line=0)
S_45 = K.sign("s_45", ["45 MINUTES"], AWAY, w=2.3, head="THE FULL LIST")

# ------------------------------------------------------------------ 3 stare: a night bridge, a stopwatch

O3 = stage(3, NAVY, (0.18, 0.20, 0.30))
K.box("deck", (13.0, 3.0, 0.3), (0.42, 0.40, 0.45), O3 + Vector((0, -0.2, 0.15)), bevel=0.02)
for side in (-1.6, 1.25):
    K.box(f"rail{side}", (13.0, 0.08, 0.08), SILVER, O3 + Vector((0, side, 1.25)), bevel=0, line=0.006)
    for k in range(9):
        K.box(f"post{side}{k}", (0.08, 0.08, 1.0), SILVER, O3 + Vector((-6 + k * 1.5, side, 0.8)), bevel=0, line=0.006)
for x in (-3.5, 3.5):
    K.cyl(f"lamp{x}", 0.05, 2.6, DARK, O3 + Vector((x, 1.3, 1.6)), seg=12)
    lb = K.ball(f"lampb{x}", 0.22, LAMP, O3 + Vector((x, 1.3, 3.0)), line=0.006)
    lb.data.materials[0] = K.flat(LAMP)
for k in range(14):
    random.seed(k)
    K.ball(f"star{k}", 0.035, CREAM, O3 + Vector((random.uniform(-6, 6), 2.0, random.uniform(3.5, 8.5))), line=0)
K.ball("moon", 0.5, CREAM, O3 + Vector((4.2, 2.0, 6.0)), line=0.006)
WATCH = K.empty("watch", O3 + Vector((0, 0.9, 2.75)))
K.cyl("watchr", 0.75, 0.15, SILVER, (0, 0, 0), WATCH, rot=(math.pi / 2, 0, 0), seg=48)
K.cyl("watchf", 0.65, 0.05, DARK, (0, -0.1, 0), WATCH, rot=(math.pi / 2, 0, 0), seg=48, line=0)
K.cyl("watchk", 0.1, 0.25, SILVER, (0, 0, 0.85), WATCH, seg=16)
WATCH_T = K.label("watcht", "4:00", 0.42, (0.4, 1.0, 0.5), (0, -0.14, -0.05), WATCH)
S_4 = K.sign("s_4", ["4 MINUTES"], AWAY, w=2.2, head="EYE CONTACT")

# ------------------------------------------------------------------ 4 fries: all 36, one basket

O4 = stage(4, PINK, (0.40, 0.12, 0.25))
K.box("table4", (3.6, 1.4, 0.1), TABLE, O4 + Vector((0, 0.3, 1.1)), bevel=0.03)
K.cyl("tleg4", 0.12, 1.05, SILVER, O4 + Vector((0, 0.3, 0.53)), seg=16)
K.cyl("basket", 0.42, 0.4, BASKET, O4 + Vector((0, 0.3, 1.35)), seg=32, r2=0.55)
for k in range(11):
    random.seed(100 + k)
    K.box(f"fry{k}", (0.08, 0.08, 0.6), FRY, O4 + Vector((random.uniform(-0.3, 0.3), 0.3 + random.uniform(-0.2, 0.2), 1.75)),
          rot=(random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), 0), bevel=0.01, line=0.006)
K.box("qboard", (2.0, 0.06, 0.7), CREAM, O4 + Vector((0, 2.0, 3.0)), bevel=0.03)
QCOUNT = K.label("qcount", "1 / 36", 0.3, K.INK, O4 + Vector((0, 1.94, 3.0)))
CARDS = [K.box(f"fc{k}", (0.5, 0.02, 0.35), CREAM, AWAY, bevel=0.01, line=0.006) for k in range(8)]
S_36 = K.sign("s_36", ["ALL 36"], AWAY, w=1.9, head="SHE ASKED")

# ------------------------------------------------------------------ 5 exit: the glowing EXIT sign

O5 = stage(5, (0.12, 0.30, 0.32), CHECK)
K.box("door", (1.3, 0.1, 2.8), (0.55, 0.35, 0.2), O5 + Vector((1.2, 2.0, 1.4)), bevel=0.03)
K.ball("knob", 0.07, GOLD, O5 + Vector((0.75, 1.92, 1.4)), line=0.006)
K.box("exitb", (1.2, 0.1, 0.45), DARK, O5 + Vector((1.2, 1.95, 3.2)), bevel=0.03)
EXIT_T = K.label("exitt", "EXIT", 0.32, EXITG, O5 + Vector((1.2, 1.88, 3.2)))
K.box("table5", (2.2, 1.0, 0.1), TABLE, O5 + Vector((-0.7, 0.9, 1.1)), bevel=0.03)
K.cyl("tleg5", 0.12, 1.05, SILVER, O5 + Vector((-0.7, 0.9, 0.53)), seg=16)
SWEAT = [K.ball(f"sw{k}", 0.05, (0.55, 0.85, 1.0), AWAY, squash=(0.7, 0.7, 1.2), line=0.004) for k in range(3)]

# ------------------------------------------------------------------ 6 final: the waiter, the ring

O6 = stage(6, PLUM, (0.30, 0.32, 0.40))
RING = K.empty("ring", AWAY)
K.box("ringbox", (0.4, 0.4, 0.3), RED, (0, 0, 0), RING, bevel=0.05)
K.box("ringlid", (0.4, 0.1, 0.35), RED, (0, 0.2, 0.3), RING, rot=(-0.4, 0, 0), bevel=0.05)
K.cyl("ringg", 0.12, 0.04, GOLD, (0, -0.02, 0.28), RING, rot=(math.pi / 2, 0, 0), seg=32)
K.ball("gem", 0.06, (0.75, 0.95, 1.0), (0, -0.02, 0.42), RING, line=0.004)
HEARTS = [heart(f"h{k}", PINK if k % 2 else RED, r=0.14, loc=AWAY) for k in range(6)]
S_ENG = K.sign("s_eng", ["ENGAGED"], AWAY, w=2.1, head="THEY ARE")

# ------------------------------------------------------------------ the cast and the camera

SA = shaker("sa", SALT)
PE = shaker("pe", PEPPER)
WA = waiter("wa")
for p in (SA, PE, WA):
    p["shades"]["home"] = p["shades"].location.copy()
cam = B.camera(lens=40, fstop=16.0)
cam.data.dof.use_dof = False
cam.data.clip_start = 0.05
cam.data.clip_end = 80

def lc(a, b, tg, lens, u, o):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "booth": lambda u: lc((0.0, -7.0, 2.3), (0.0, -6.2, 2.2), (0, 0, 1.8), 40, u, O0),
    "lab": lambda u: lc((0.4, -7.2, 2.3), (0.1, -6.6, 2.3), (0, 0, 1.9), 40, u, O1),
    "clock": lambda u: lc((-0.3, -7.6, 2.4), (0.0, -6.8, 2.5), (0, 0, 2.2), 40, u, O2),
    "stare": lambda u: lc((0.6, -7.4, 2.2), (0.2, -6.6, 2.2), (0, 0, 2.0), 40, u, O3),
    "fries": lambda u: lc((-0.4, -6.8, 2.3), (-0.1, -6.2, 2.3), (0, 0, 1.9), 40, u, O4),
    "exit": lambda u: lc((0.3, -7.2, 2.3), (0.1, -6.6, 2.3), (0.1, 0, 2.0), 40, u, O5),
    "final": lambda u: lc((0.2, -6.6, 2.2), (0.0, -6.0, 2.2), (0, 0, 1.9), 40, u, O6),
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

def apply_state(t):
    name, u, age, cut, second, length = shot_at(t)
    q = math.floor(t * 12) / 12            # props step in stop motion
    aq = age - (t - q)
    loc, tg, lens = alt_cam(CAMS[name], cut) if second and name != "booth" else CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens

    for o in [SA["root"], PE["root"], WA["root"], S_FIRST, S_LAM, S_1997, S_CLOSE, S_45, S_4, S_36, S_ENG, GLINT, RING] \
            + SWEAT + CARDS + HEARTS:
        o.location = AWAY

    if name == "booth":
        k = smooth01(aq / 0.14)                                     # the card slams upright on frame one
        wob = 0.08 * math.sin(aq * 30) * max(0.0, 1 - aq / 0.6) if aq > 0.14 else 0.0
        CARD.rotation_euler = (-1.3 * (1 - k) + wob, 0, 0)
        pose(SA, O0 + Vector((-1.05, -1.0, 0)), scale=0.8, arm=(0.2, 1.6 - 1.4 * k), sway=-0.1 * k, yaw=0.35, angry=0.6, gape=0.25)
        pose(PE, O0 + Vector((1.05, -1.0, 0)), scale=0.8, arm=(0.5, 0.2), sway=0.12 + 0.03 * math.sin(q * 3), yaw=-0.35, angry=-0.7, gape=0.5)
        drop(S_FIRST, O0 + Vector((0, 0.4, 3.0)), aq, 0.3)
        if second:
            a2 = t - start_of("booth~2")
            g = smooth01(a2 / 0.6)
            GLINT.location = O0 + Vector((-0.6 + 1.2 * g, -0.12, 1.6))
            drop(S_LAM, O0 + Vector((0.0, 0.4, 2.8)), a2, 0.05)
            S_FIRST.location = AWAY
            pose(SA, O0 + Vector((-1.05, -1.0, 0)), scale=0.8, arm=(0.2, 1.3), yaw=0.35, angry=0.8, hop=0.03 * abs(math.sin(q * 6)))
    elif name == "lab":
        pose(SA, O1 + Vector((-0.9, -0.8, 0)), scale=0.8, yaw=-1.0, arm=(0.3, 0.8 + 0.3 * math.sin(q * 4)), gape=0.2 * abs(math.sin(q * 7)))
        pose(PE, O1 + Vector((0.9, -0.8, 0)), scale=0.8, yaw=1.0, arm=(0.5, 0.2), gape=0.15, angry=-0.2)
        if aq < 2.6:
            drop(S_1997, O1 + Vector((0, 0.0, 3.4)), aq, 0.2)
        else:
            drop(S_CLOSE, O1 + Vector((0, 0.0, 3.4)), aq, 2.6)
    elif name == "clock":
        HAND_M.rotation_euler = (0, aq * 6.0, 0)
        HAND_H.rotation_euler = (0, aq * 0.5, 0)
        pose(SA, O2 + Vector((-1.0, -0.8, 0)), scale=0.75, yaw=0.3, arm=(0.4, 1.2), gape=0.25 * abs(math.sin(q * 7)), angry=0.3)
        pose(PE, O2 + Vector((1.0, -0.8, 0)), scale=0.75, yaw=-0.3, sway=0.2, arm=(1.6, 0.1), gape=0.8 * smooth01(aq / 1.5), angry=-0.9)
        drop(S_45, O2 + Vector((0, -0.6, 1.9)), aq, 0.4)
    elif name == "stare":
        sec = max(0.0, 240 - aq * 9)
        WATCH_T.data.body = f"{int(sec) // 60}:{int(sec) % 60:02d}"
        pose(SA, O3 + Vector((-1.0, -0.6, 0.3)), scale=0.8, yaw=-1.05, angry=0.9)
        pose(PE, O3 + Vector((1.0, -0.6, 0.3)), scale=0.8, yaw=1.05, angry=-0.6, sway=0.04 * math.sin(q * 5))
        drop(S_4, O3 + Vector((0, 0.6, 4.25)), aq, 0.3)
    elif name == "fries":
        n = min(36, 1 + int(aq * 14))
        QCOUNT.data.body = f"{n} / 36"
        for k, c in enumerate(CARDS):
            a = (aq * 2.2 + k / len(CARDS)) % 1.0
            c.location = O4 + Vector((-0.8 + a * 1.4, -0.3, 1.6 + a * 2.0 - a * a * 1.6))
            c.rotation_euler = (0.3, a * 4, a * 3)
        pose(SA, O4 + Vector((-1.1, -0.8, 0)), scale=0.8, yaw=0.3, arm=(0.4, 1.4 + 0.2 * math.sin(q * 8)), gape=0.3 * abs(math.sin(q * 9)), angry=0.5)
        pose(PE, O4 + Vector((1.1, -0.8, 0)), scale=0.8, yaw=-0.3, sway=0.25, arm=(0.1, 0.1), angry=-1.0, gape=0.1)
        drop(S_36, O4 + Vector((0, 0.6, 4.1)), aq, 0.8)
    elif name == "exit":
        g = 1.0 if int(q * 4) % 2 else 0.8
        EXIT_T.scale = (g, g, g)
        pose(SA, O5 + Vector((-1.0, -0.8, 0)), scale=0.8, yaw=-0.5, angry=1.0)
        look = smooth01((aq - 0.3) / 0.4)
        pose(PE, O5 + Vector((0.6, -0.8, 0)), scale=0.8, yaw=-0.2 + 1.2 * look, arm=(0.2, 0.9 * look), angry=-1.0, gape=0.3)
        for k, d in enumerate(SWEAT):
            a = (aq * 1.5 + k / 3) % 1.0
            d.location = O5 + Vector((0.95, -1.05, 1.8 - a * 0.8))
    elif name == "final":
        pose(SA, O6 + Vector((-0.75, -0.3, 0)), scale=0.85, yaw=-0.7, angry=-0.4, gape=0.4, hop=0.03 * abs(math.sin(q * 5)))
        kneel = smooth01((aq - 0.8) / 0.5)
        pose(WA, O6 + Vector((0.8, -0.3, -0.25 * kneel)), scale=0.85, yaw=0.7, arm=(0.3, 1.2 * kneel), angry=-0.3, gape=0.15)
        if kneel > 0.01:
            RING.location = O6 + Vector((0.2, -0.75, 0.9))
            RING.scale = (kneel,) * 3
        if aq > 0.5:
            for k, h in enumerate(HEARTS):
                a = (aq * 0.6 + k / len(HEARTS)) % 1.0
                h.location = O6 + Vector(((-1.5 if k % 2 else 1.5) + 0.25 * (k % 3), -0.6, 1.4 + a * 1.3))
                h.scale = (1 - a * 0.5,) * 3
        drop(S_ENG, O6 + Vector((0, 0.3, 3.4)), aq, 1.3)

B.render_settings(FPS, samples=int(os.environ.get("Q36_SAMPLES", "12")), motion_blur=0.0)
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
