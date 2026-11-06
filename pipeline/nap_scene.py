"""Blender scene for The NASA Nap (render_nap.py). Toon kit (toon.py). Cast: your friend (face down on a textbook, Z's
rising, a little drool) and toy airline pilots. Sets along x, 40 m apart: a library study table with a flashing phone
alarm and a nap timer, a cockpit at night over the ocean (one pilot flies, one sleeps), no-nap and nap stat bars, and a
movie screen with a toy ship. Stop motion at 12 steps a second for props, smooth camera. Helpers from caff_scene.py.

blender -b --factory-startup -P nap_scene.py -- timing.json out_dir MODE   (MODE: all or 1-based frame list)
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


MUGC, COFFEE, NIGHT, MOON = (0.85, 0.20, 0.18), (0.30, 0.17, 0.08), (0.10, 0.12, 0.30), (1.0, 0.92, 0.55)
SHEET, BLANK = (0.55, 0.75, 0.98), (0.95, 0.85, 0.40)

def mug(name, r, h, color, loc=(0, 0, 0), parent=None, line=0.01):
    """A coffee mug, z=0 at its base, handle on +x."""
    root = K.empty(name, loc, parent)
    K.cyl(name + "b", r, h, color, (0, 0, h / 2), root, seg=40, line=line)
    K.cyl(name + "c", r * 0.88, 0.02, COFFEE, (0, 0, h - 0.015), root, seg=40, line=0)
    K.box(name + "h", (r * 0.22, r * 0.25, h * 0.55), color, (r * 1.12, 0, h * 0.5), root, bevel=r * 0.08, line=line)
    return root

def clock(name, loc, r=0.55):
    """A wall clock facing -y with an hour and a minute hand on pivots."""
    root = K.empty(name, loc)
    K.cyl(name + "f", r, 0.08, WHITE, (0, 0, 0), root, rot=(math.pi / 2, 0, 0), seg=48)
    for j in range(12):
        a = j / 12 * 2 * math.pi
        K.box(f"{name}tk{j}", (0.035, 0.02, 0.09), K.INK, (r * 0.8 * math.sin(a), -0.05, r * 0.8 * math.cos(a)), root,
              rot=(0, a, 0), bevel=0, line=0)
    hp = K.empty(name + "hp", (0, -0.07, 0), root)
    K.box(name + "hh", (0.06, 0.02, r * 0.5), K.INK, (0, 0, r * 0.22), hp, bevel=0.01, line=0)
    mp = K.empty(name + "mp", (0, -0.09, 0), root)
    K.box(name + "mh", (0.04, 0.02, r * 0.72), RED, (0, 0, r * 0.33), mp, bevel=0.01, line=0)
    return root, hp, mp

def set_time(hp, mp, hours):
    """Clock hands for a time in hours (21.0 = 9:00)."""
    hp.rotation_euler = (0, (hours % 12) / 12 * 2 * math.pi, 0)
    mp.rotation_euler = (0, (hours % 1) * 2 * math.pi, 0)


NIGHT, MOON = (0.06, 0.08, 0.22), (1.0, 0.92, 0.55)
NAVYH, SHIRT, BOOKR = (0.10, 0.12, 0.25), (0.92, 0.93, 0.96), (0.80, 0.25, 0.22)

def tlabel(ob, body):
    if ob.data.body != body:
        ob.data.body = body

def sign_text(sg, i=0):
    return bpy.data.objects[f"{sg.name}t{i}"]

def pilot(name, shirt):
    global SWEAT
    SWEAT = shirt
    p = friend(name)
    hat = K.empty(name + "hat", (0, 0, 1.68), p["body"])
    K.cyl(name + "hatc", 0.3, 0.14, NAVYH, (0, 0.02, 0.0), hat, seg=32)
    K.box(name + "hatb", (0.5, 0.22, 0.03), K.INK, (0, -0.22, -0.06), hat, bevel=0.01, line=0.005)
    K.box(name + "hatg", (0.14, 0.02, 0.06), GOLD, (0, -0.3, 0.03), hat, bevel=0.005, line=0)
    for k in ("scarf",):
        ob = bpy.data.objects.get(name + k)
        if ob:
            ob.scale = (0.001,) * 3
    return p

def zs(name, n=3):
    return [K.label(f"{name}{k}", "Z", 0.28 - 0.04 * k, WHITE, AWAY) for k in range(n)]

def float_zs(lst, at, t):
    for k, z in enumerate(lst):
        ph = (t * 0.45 + k / len(lst)) % 1.0
        z.location = at + Vector((0.15 + 0.35 * ph, -0.1, 0.7 * ph))
        s = 0.5 + 0.8 * math.sin(ph * math.pi)
        z.scale = (s, s, s)

# ------------------------------------------------------------------ 0 the library study table
O0 = stage(0, (0.45, 0.30, 0.24), (0.55, 0.40, 0.28))
for c in range(4):
    x = -3.0 + c * 2.0
    K.box(f"shelf{c}", (1.8, 0.4, 3.6), WOOD, O0 + Vector((x, 1.9, 1.8)), bevel=0.02)
    for r in range(4):
        for b in range(7):
            col = (BOOKR, BLUE, GREEN, GOLD, PLUM, TEAL, ORANGE)[(b + r + c) % 7]
            K.box(f"bk{c}{r}{b}", (0.18, 0.3, 0.55 + 0.1 * ((b * 3 + r) % 3)), col,
                  O0 + Vector((x - 0.62 + b * 0.21, 1.7, 0.45 + r * 0.85 + 0.3)), bevel=0.01, line=0.006)
K.box("tbl", (2.6, 1.1, 0.08), WOOD, O0 + Vector((0.2, -0.3, 0.8)), bevel=0.02)
K.box("tblf", (2.5, 0.06, 0.4), (0.50, 0.28, 0.12), O0 + Vector((0.2, -0.82, 0.58)), bevel=0.01)
K.box("book", (0.8, 0.55, 0.06), BOOKR, O0 + Vector((0.0, -0.55, 0.87)), bevel=0.01)
K.box("pages", (0.74, 0.5, 0.04), WHITE, O0 + Vector((0.0, -0.55, 0.91)), bevel=0.005, line=0.005)
PHONE = K.empty("phone", O0 + Vector((0.75, -0.55, 0.85)))
K.box("phb", (0.22, 0.4, 0.04), DARK, (0, 0, 0), PHONE, bevel=0.02)
ALARM = K.label("alarm", "20 MIN", 0.07, WHITE, (0, -0.05, 0.03), PHONE)
ALARM.rotation_euler = (0, 0, 0)
ALSCR = K.box("phs", (0.19, 0.36, 0.01), RED, (0, 0, 0.022), PHONE, bevel=0, line=0)
ALSCR.data.materials[0] = K.flat(RED)
DROOL = K.box("drool", (0.025, 0.025, 0.12), (0.7, 0.88, 1.0), AWAY, bevel=0.01, line=0)
CLK0, CLK0_H, CLK0_M = clock("clk0", O0 + Vector((1.6, 1.6, 3.3)), r=0.45)
FR = friend("fr")
Z0 = zs("z0")
S_TIMER = K.sign("s_timer", ["2 HRS 58 MIN"], AWAY, w=2.0, head="NAP TIMER")

# ------------------------------------------------------------------ 1 the cockpit at night
O1 = stage(1, (0.12, 0.14, 0.26), (0.18, 0.18, 0.24))
K.box("win1", (4.6, 0.08, 2.0), NIGHT, O1 + Vector((0, 2.0, 2.6)), bevel=0.02).data.materials[0] = K.flat(NIGHT)
for x in (-0.8, 0.8):
    K.box(f"wbar{x}", (0.12, 0.1, 2.1), GREY, O1 + Vector((x, 1.95, 2.6)), bevel=0.01, line=0.006)
K.ball("moon1", 0.25, MOON, O1 + Vector((1.5, 1.94, 3.1)), squash=(1, 0.3, 1), line=0).data.materials[0] = K.flat(MOON)
srnd = random.Random(4)
for k in range(18):
    st = K.ball(f"star{k}", 0.025, WHITE, O1 + Vector((srnd.uniform(-2.2, 2.2), 1.94, srnd.uniform(1.8, 3.5))), line=0)
    st.data.materials[0] = K.flat(WHITE)
K.box("sea1", (4.6, 0.06, 0.25), (0.10, 0.20, 0.42), O1 + Vector((0, 1.93, 1.72)), bevel=0, line=0)
for x in (-0.8, 0.8):
    K.box(f"seat{x}", (0.8, 0.25, 1.5), (0.35, 0.30, 0.28), O1 + Vector((x, 1.0, 0.75)), bevel=0.08)
PIL1 = pilot("p1", SHIRT)
PIL2 = pilot("p2", (0.55, 0.75, 0.95))
K.box("panel", (3.4, 0.5, 0.8), (0.25, 0.27, 0.33), O1 + Vector((0, -0.4, 0.4)), bevel=0.04)
for k, x in enumerate((-1.3, -0.5, 0.3, 1.1)):
    sc = K.box(f"pscr{k}", (0.45, 0.02, 0.3), (0.2, 0.9, 0.5) if k % 2 else SCREEN, O1 + Vector((x, -0.66, 0.5)), bevel=0, line=0)
    sc.data.materials[0] = K.flat((0.2, 0.9, 0.5) if k % 2 else SCREEN)
for x in (-0.8, 0.8):
    K.box(f"yoke{x}", (0.4, 0.06, 0.06), DARK, O1 + Vector((x, -0.25, 0.95)), bevel=0.02, line=0.006)
Z1 = zs("z1")
S_PAC = K.sign("s_pac", ["ACROSS THE PACIFIC"], AWAY, w=2.6, head="NASA, OVERNIGHT FLIGHTS")
S_REST = K.sign("s_rest", ["40 MIN"], AWAY, w=1.3, head="REST WINDOW")
S_SLEPT = K.sign("s_slept", ["26 MIN"], AWAY, w=1.3, head="ACTUAL SLEEP")

# ------------------------------------------------------------------ 2 the stat bars
O2 = stage(2, (0.30, 0.22, 0.45), (0.22, 0.20, 0.30))
BARS = []
for k, (x, h, c, lab) in enumerate(((-1.25, 1.5, GREY, "NO NAP"), (-0.5, 2.01, GOLD, "NAP"),
                                     (0.5, 1.5, GREY, "NO NAP"), (1.25, 2.31, TEAL, "NAP"))):
    root = K.empty(f"bar{k}", O2 + Vector((x, 0.6, 0)))
    K.box(f"barb{k}", (0.6, 0.6, 1.0), c, (0, 0, 0.5), root, bevel=0.04)
    K.label(f"barl{k}", lab, 0.16, WHITE, O2 + Vector((x, 0.2, 0.15)))
    BARS.append((root, h))
PIL3 = pilot("p3", SHIRT)
S_PERF = K.sign("s_perf", ["+34%"], AWAY, w=1.3, head="PERFORMANCE")
S_ALERT = K.sign("s_alert", ["+54%"], AWAY, w=1.3, head="ALERTNESS")
S_NASA = K.sign("s_nasa", ["26 MIN"], AWAY, w=1.6, head="THE NASA NAP")

# ------------------------------------------------------------------ 3 the movie screen
O3 = stage(3, (0.10, 0.08, 0.14), (0.22, 0.10, 0.12))
SCR = K.box("screen3", (4.0, 0.08, 2.2), (0.85, 0.9, 1.0), O3 + Vector((0, 2.0, 2.6)), bevel=0, line=0.01)
SCR.data.materials[0] = K.flat((0.55, 0.75, 0.95))
K.box("sea3", (4.0, 0.06, 0.6), (0.15, 0.35, 0.65), O3 + Vector((0, 1.94, 1.8)), bevel=0, line=0).data.materials[0] = K.flat((0.15, 0.35, 0.65))
SHIP = K.empty("ship", O3 + Vector((0, 1.9, 2.05)))
K.box("hull", (1.8, 0.08, 0.32), K.INK, (0, 0, 0), SHIP, bevel=0.06, line=0.008)
K.box("deck", (1.5, 0.07, 0.16), WHITE, (0.05, 0, 0.24), SHIP, bevel=0.02, line=0.006)
for k in range(4):
    K.cyl(f"fun{k}", 0.08, 0.36, (0.95, 0.70, 0.20), (-0.45 + k * 0.3, 0, 0.5), SHIP, seg=16, line=0.006)
for r in range(2):
    for c in range(5):
        K.box(f"cs{r}{c}", (0.7, 0.3, 0.7 + 0.15 * r), (0.70, 0.12, 0.14), O3 + Vector((-1.6 + c * 0.8, -0.6 - r * 0.9, 0.35)), bevel=0.08)
S_RUN = K.sign("s_run", ["3 HRS 14 MIN"], AWAY, w=2.1, head="TITANIC RUNTIME")

# ------------------------------------------------------------------ camera

cam = B.camera(lens=40, fstop=16.0)
cam.data.dof.use_dof = False
cam.data.clip_start = 0.05
cam.data.clip_end = 80

def lc(a, b, tg, lens, u, o):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "desk": lambda u: lc((0.4, -5.0, 2.4), (0.3, -4.5, 2.3), (0.25, 0, 1.6), 40, u, O0),
    "cockpit": lambda u: lc((0.0, -5.6, 2.2), (0.0, -5.1, 2.15), (0.0, 0.3, 1.8), 40, u, O1),
    "rest": lambda u: lc((1.3, -3.8, 1.9), (1.2, -3.4, 1.9), (0.8, 0.3, 1.6), 40, u, O1),
    "slept": lambda u: lc((-0.3, -3.6, 2.4), (-0.1, -3.3, 2.3), (0.6, 0.3, 1.7), 40, u, O1),
    "perf": lambda u: lc((-0.7, -5.4, 2.3), (-0.6, -5.0, 2.3), (-0.6, 0.5, 1.9), 40, u, O2),
    "alert": lambda u: lc((0.8, -5.4, 2.4), (0.7, -5.0, 2.4), (0.7, 0.5, 2.0), 40, u, O2),
    "nasa": lambda u: lc((0.0, -5.8, 2.4), (0.0, -5.3, 2.3), (0.0, 0.3, 2.0), 40, u, O2),
    "movie": lambda u: lc((0.0, -6.6, 2.2), (0.0, -6.0, 2.2), (0.0, 1.0, 2.2), 40, u, O3),
    "final": lambda u: lc((0.4, -5.6, 2.5), (0.3, -5.1, 2.4), (0.25, 0, 1.6), 40, u, O0),
}

def shot_at(t):
    k = max([0] + [i for i, (s, _) in enumerate(SHOTS) if t >= s - 1e-6])
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    cut = max(0.0, min(1.0, (t - SHOTS[k][0]) / max(1e-6, t1 - SHOTS[k][0])))
    return SHOTS[k][1], t - SHOTS[k][0], cut, t1 - SHOTS[k][0]

def start_of(n):
    return next(s for s, m in SHOTS if m == n)

def drop(ob, at, age, delay=0.0):
    u = max(0.0, age - delay) / 0.4
    z = 4.5 * max(0.0, 1 - u) ** 2 - (0.12 * math.sin(min(u, 2.0) * 6) * max(0.0, 1 - u / 2) if u > 1 else 0)
    ob.location = at + Vector((0, 0, z))

def eyes(name, open_=1.0):
    for e in ("L", "R"):
        ob = bpy.data.objects.get(name + "eye" + e)
        if ob:
            ob.scale = (1, 1, max(0.12, open_))
        ob = bpy.data.objects.get(name + "pup" + e)
        if ob:
            ob.scale = (1, 1, 1) if open_ > 0.5 else (0.001,) * 3

def seat(p, at, lean=0.0, tilt=0.0):
    p["root"].location = at
    p["root"].rotation_euler = (0, 0, 0)
    p["body"].rotation_euler = (lean, tilt, 0)
    p["shades"].location = AWAY
    p["hood"].location = AWAY

def apply_state(t):
    name, age, cut, length = shot_at(t)
    q = math.floor(t * 12) / 12
    aq = age - (t - q)
    loc, tg, lens = CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    for o in [S_TIMER, S_PAC, S_REST, S_SLEPT, S_PERF, S_ALERT, S_NASA, S_RUN] + Z1:
        o.location = AWAY

    # ---- library: face down on the textbook, Z's rising, the alarm flashing, the timer creeping up
    seat(FR, O0 + Vector((0.0, 0.42, 0.05)), lean=0.75 + 0.02 * math.sin(t * 1.6))
    eyes("fr", 0.12)
    for k in ("armL", "armR"):
        FR[k].rotation_euler = (0, (-1 if k == "armL" else 1) * 0.3, 0)
    K.mood(FR, -0.4)
    head = O0 + Vector((0.0, -0.6, 1.1))
    float_zs(Z0, head + Vector((0.2, 0, 0.2)), t)
    DROOL.location = O0 + Vector((-0.12, -0.92, 0.93))
    DROOL.scale = (1, 1, 0.7 + 0.3 * math.sin(t * 2.2))
    blink = math.sin(q * 9) > 0
    ALSCR.scale = (1, 1, 1) if blink else (0.001,) * 3
    PHONE.location = O0 + Vector((0.75 + (0.01 * math.sin(q * 60) if blink else 0), -0.55, 0.85))
    mins = 178 + int(10 * smooth01(t / DUR))
    set_time(CLK0_H, CLK0_M, 14.0 + mins / 60)
    if name in ("desk", "final"):
        tlabel(sign_text(S_TIMER), f"{mins // 60} HRS {mins % 60} MIN")
        drop(S_TIMER, O0 + Vector((0.3, -0.2, 2.75)), aq, 0.6)

    # ---- cockpit: the left pilot flies, the right one sleeps
    seat(PIL1, O1 + Vector((-0.8, 0.55, -0.35)), lean=-0.05)
    PIL1["armL"].rotation_euler = (0, 0.9, 0)
    PIL1["armR"].rotation_euler = (0, -0.9 + 0.05 * math.sin(t * 2), 0)
    eyes("p1", 1.0)
    K.mood(PIL1, 0.2)
    seat(PIL2, O1 + Vector((0.8, 0.55, -0.35)), tilt=0.22 + 0.03 * math.sin(t * 1.2), lean=-0.1)
    PIL2["armL"].rotation_euler = (0, 0.2, 0)
    PIL2["armR"].rotation_euler = (0, -0.2, 0)
    eyes("p2", 0.12)
    K.mood(PIL2, -0.3)
    if name in ("cockpit", "rest", "slept"):
        float_zs(Z1, O1 + Vector((1.0, 0.4, 1.4)), t)
    if name == "cockpit":
        drop(S_PAC, O1 + Vector((0.0, 0.2, 3.25)), aq, 0.5)
    elif name == "rest":
        drop(S_REST, O1 + Vector((0.75, 0.0, 2.4)), aq, 0.4)
    elif name == "slept":
        drop(S_SLEPT, O1 + Vector((0.55, 0.0, 2.45)), aq, 0.3)

    # ---- stat bars: no-nap bars stand, the nap bars climb; the pilot hops
    seat(PIL3, O2 + Vector((0.0, -0.7, 0.0)) if t >= start_of("nasa") else AWAY)
    eyes("p3", 1.0)
    K.mood(PIL3, -0.2)
    PIL3["armR"].rotation_euler = (0, 2.2 if t >= start_of("nasa") else 0.4, 0)
    PIL3["armL"].rotation_euler = (0, 0.4, 0)
    if t >= start_of("nasa"):
        PIL3["root"].location.z = 0.08 * abs(math.sin(q * 6))
    for k, (root, h) in enumerate(BARS):
        if k % 2 == 0:
            root.scale = (1, 1, h)
        else:
            t0 = start_of("perf") if k == 1 else start_of("alert")
            g = smooth01((t - t0 - 0.4) / 1.0) if t >= t0 else 0.0
            root.scale = (1, 1, max(0.02, 1.5 + (h - 1.5) * g) if t >= t0 else 1.5)
    if name in ("perf", "alert"):
        if t >= start_of("perf"):
            S_PERF.location = O2 + Vector((-0.85, 0.3, 3.15))
            if name == "perf":
                drop(S_PERF, O2 + Vector((-0.85, 0.3, 3.15)), aq, 0.8)
        if t >= start_of("alert"):
            S_ALERT.location = O2 + Vector((0.9, 0.3, 3.45))
            if name == "alert":
                drop(S_ALERT, O2 + Vector((0.9, 0.3, 3.45)), aq, 0.8)
    if name == "nasa":
        drop(S_NASA, O2 + Vector((0.0, -0.9, 2.55)), aq, 0.4)

    # ---- movie: the toy ship bobs on the screen, the runtime sign lands
    SHIP.location = O3 + Vector((-0.3 + 0.15 * t % 1.0 * 0, 1.9, 2.05 + 0.03 * math.sin(q * 3)))
    SHIP.rotation_euler = (0, 0.03 * math.sin(q * 2.5), 0)
    if name == "movie":
        drop(S_RUN, O3 + Vector((0.0, 0.6, 3.75)), aq, 0.5)

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
