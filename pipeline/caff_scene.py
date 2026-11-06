"""Blender scene for Caffeine Doesn't Affect Me (render_caff.py). Toon kit (toon.py). Cast: your friend (eyes wide open,
twitching) and a grumpy giant coffee mug. Sets along x, 40 m apart: a kitchen at night with a 9 o'clock wall clock, a
sleep lab (a 400 MG bottle, four mugs, a clock that spins six hours), and a bedroom with a sleep monitor, a stack of sleep
blocks that loses one, and a sleep diary page. Stop motion at 12 steps a second for props, smooth camera. Helpers from
cold_scene.py.

blender -b --factory-startup -P caff_scene.py -- timing.json out_dir MODE   (MODE: all or 1-based frame list)
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

# ------------------------------------------------------------------ 0 the kitchen at night

O0 = stage(0, (0.20, 0.24, 0.45), (0.42, 0.30, 0.22))
K.box("win0", (1.6, 0.08, 1.4), NIGHT, O0 + Vector((-2.2, 2.0, 3.1)), bevel=0.02).data.materials[0] = K.flat(NIGHT)
K.box("winf0", (1.75, 0.06, 1.55), WHITE, O0 + Vector((-2.2, 2.05, 3.1)), bevel=0.02, line=0.006)
K.ball("moon0", 0.22, MOON, O0 + Vector((-2.6, 1.95, 3.4)), squash=(1, 0.3, 1), line=0).data.materials[0] = K.flat(MOON)
K.box("ctr0", (3.2, 0.9, 1.0), (0.85, 0.80, 0.70), O0 + Vector((-0.6, 1.5, 0.5)), bevel=0.04)
K.box("ctrt0", (3.3, 1.0, 0.1), WOOD, O0 + Vector((-0.6, 1.5, 1.05)), bevel=0.02)
mug("cm0", 0.18, 0.4, WHITE, O0 + Vector((-1.5, 1.4, 1.1)))
CLK0, CLK0_H, CLK0_M = clock("clk0", O0 + Vector((1.1, 2.0, 3.6)))
BIG = {"root": K.empty("big", O0 + Vector((1.15, -0.3, 0)))}
BIGB = K.empty("bigb", (0, 0, 0), BIG["root"])
mug("bigm", 0.62, 1.35, MUGC, (0, 0, 0), BIGB)
face("big", K.empty("bigf", (0, 0, 0), BIGB), 0.62, 0.85, BIG, eye=0.11, gap=0.2)
SWEAT = (0.20, 0.55, 0.30)
FR = friend("fr")
CUP = mug("cup", 0.11, 0.24, WHITE)
S_NINE = K.sign("s_nine", ["COFFEE #3"], AWAY, w=1.6, head="9:00 PM")
S_RIGHT = K.sign("s_right", ["CAN'T FEEL IT"], AWAY, w=2.2, head="THEY'RE RIGHT")

# ------------------------------------------------------------------ 1 the sleep lab

O1 = stage(1, (0.86, 0.92, 0.95), (0.62, 0.66, 0.72))
K.box("bench1", (3.0, 1.0, 0.1), WHITE, O1 + Vector((-0.4, 0.2, 0.95)), bevel=0.02)
for x in (-1.8, 1.0):
    K.box(f"bl{x}", (0.1, 0.9, 0.9), GREY, O1 + Vector((x, 0.2, 0.45)), bevel=0, line=0.005)
BOT = K.empty("bot", O1 + Vector((-1.2, 0.2, 1.0)))
K.cyl("botb", 0.32, 0.8, (0.95, 0.55, 0.15), (0, 0, 0.4), BOT, seg=32)
K.cyl("botc", 0.34, 0.16, WHITE, (0, 0, 0.88), BOT, seg=32)
K.box("botl", (0.5, 0.02, 0.38), WHITE, (0, -0.32, 0.42), BOT, bevel=0.01, line=0.004)
K.label("botlt", "400 MG", 0.13, K.INK, (0, -0.34, 0.47), BOT)
K.label("botlt2", "CAFFEINE", 0.09, K.INK, (0, -0.34, 0.33), BOT)
MUGS = [mug(f"m{k}", 0.2, 0.42, (WHITE, (0.95, 0.75, 0.2), BLUE, PINK)[k], AWAY) for k in range(4)]
CLK1, CLK1_H, CLK1_M = clock("clk1", O1 + Vector((1.9, 2.0, 3.1)), r=0.8)
S_LAB = K.sign("s_lab", ["SLEEP STUDY"], AWAY, w=2.2, head="2013")
S_CUPS = K.sign("s_cups", ["4 CUPS"], AWAY, w=1.5, head="400 MG = ABOUT")
S_SIX = K.sign("s_six", ["BEFORE BED"], AWAY, w=1.9, head="6 HOURS")

# ------------------------------------------------------------------ 2 the bedroom with the sleep monitor

O2 = stage(2, (0.30, 0.26, 0.50), (0.35, 0.28, 0.40))
K.box("bedf", (1.5, 2.6, 0.4), WOOD, O2 + Vector((-0.9, 0.6, 0.2)), bevel=0.04)
K.box("bedm", (1.4, 2.5, 0.25), WHITE, O2 + Vector((-0.9, 0.6, 0.52)), bevel=0.06)
K.box("bedh", (1.6, 0.15, 1.2), WOOD, O2 + Vector((-0.9, 1.9, 0.6)), bevel=0.04)
K.box("pil", (0.9, 0.45, 0.2), WHITE, O2 + Vector((-0.9, 1.5, 0.75)), bevel=0.08)
K.box("blk", (1.45, 1.5, 0.12), SHEET, O2 + Vector((-0.9, 0.2, 0.72)), bevel=0.05)
K.box("ns", (0.6, 0.5, 0.7), WOOD, O2 + Vector((0.4, 1.4, 0.35)), bevel=0.03)
MON = K.empty("mon", O2 + Vector((0.4, 1.4, 0.7)))
K.box("monb", (0.5, 0.3, 0.4), DARK, (0, 0, 0.2), MON, bevel=0.03)
K.box("mons", (0.4, 0.02, 0.26), SCREEN, (0, -0.16, 0.22), MON, bevel=0, line=0).data.materials[0] = K.flat(SCREEN)
WAVE = [K.box(f"wv{k}", (0.03, 0.01, 0.1), WHITE, (-0.16 + k * 0.04, -0.175, 0.22), MON, bevel=0, line=0) for k in range(9)]
K.box("wire", (0.9, 0.03, 0.03), K.INK, O2 + Vector((-0.15, 1.35, 0.92)), bevel=0, line=0)
BLOCKS = []
for k in range(8):
    BLOCKS.append(K.box(f"blk{k}", (1.0, 0.2, 0.36), (0.30, 0.55, 0.95) if k < 7 else (0.95, 0.42, 0.13),
                        O2 + Vector((2.6, 1.8, 0.4 + k * 0.42)), bevel=0.04))
K.label("hrs", "SLEEP", 0.28, WHITE, O2 + Vector((2.6, 1.6, 3.95)))
DIARY = K.empty("diary", AWAY)
K.box("dpg", (2.2, 0.06, 2.6), (0.99, 0.97, 0.88), (0, 0, 0), DIARY, bevel=0.03)
K.box("dsp", (0.08, 0.08, 2.6), (0.95, 0.42, 0.13), (-1.1, 0, 0), DIARY, bevel=0.02, line=0.006)
K.label("dh", "SLEEP DIARY", 0.26, K.INK, (0, -0.05, 0.95), DIARY)
for j in range(5):
    K.box(f"dl{j}", (1.8, 0.01, 0.015), (0.55, 0.75, 0.95), (0, -0.04, 0.55 - j * 0.38), DIARY, bevel=0, line=0)
K.label("dq", "SLEPT OK?", 0.3, K.INK, (-0.25, -0.05, 0.2), DIARY)
YES = K.label("dy", "YES!", 0.42, RED, (0.55, -0.06, -0.45), DIARY)
S_LOST = K.sign("s_lost", ["1 HOUR +"], AWAY, w=1.6, head="LOST")

# ------------------------------------------------------------------ camera

cam = B.camera(lens=40, fstop=16.0)
cam.data.dof.use_dof = False
cam.data.clip_start = 0.05
cam.data.clip_end = 80

def lc(a, b, tg, lens, u, o):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "chug": lambda u: lc((0.4, -5.9, 2.2), (0.35, -5.4, 2.1), (0.35, 0, 1.8), 40, u, O0),
    "lab": lambda u: lc((-0.6, -5.4, 2.6), (-0.4, -4.9, 2.5), (-0.6, 0.2, 1.9), 40, u, O1),
    "mugs": lambda u: lc((0.35, -4.4, 2.2), (0.3, -4.1, 2.1), (0.3, 0.2, 1.7), 40, u, O1),
    "clock": lambda u: lc((1.2, -4.6, 2.8), (1.35, -4.2, 2.85), (1.4, 1.0, 2.8), 40, u, O1),
    "bed": lambda u: lc((0.2, -4.6, 3.0), (0.0, -4.1, 2.8), (-0.4, 0.8, 0.9), 40, u, O2),
    "bar": lambda u: lc((2.9, -5.4, 2.4), (3.0, -5.0, 2.4), (3.1, 1.0, 2.2), 40, u, O2),
    "diary": lambda u: lc((0.0, -4.6, 2.3), (0.0, -4.1, 2.2), (0.0, 0, 2.0), 40, u, O2 + Vector((-4.5, 0, 0))),
    "right": lambda u: lc((0.3, -5.2, 2.2), (0.3, -4.8, 2.1), (0.35, 0, 1.8), 40, u, O0),
    "final": lambda u: lc((0.4, -6.3, 2.3), (0.35, -5.8, 2.2), (0.35, 0, 1.8), 40, u, O0),
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

def wide_eyes(p, q, k=1.0):
    """Eyes stretched open with a nervous twitch (stop motion)."""
    tw = 1.0 + 0.25 * k * (1 if math.sin(q * 37) > 0.6 else 0)
    for e in ("L", "R"):
        ob = bpy.data.objects.get("freye" + e)
        if ob:
            ob.scale = (1.15 * tw, 1, 1.35 * tw)
    for e in ("L", "R"):
        ob = bpy.data.objects.get("frpup" + e)
        if ob:
            ob.scale = (0.7, 1, 0.7)

def pose(p, at, arm=(0.0, 0.0), angry=0.0, gape=0.0, yaw=0.0, hop=0.0, tilt=0.0):
    p["root"].location = at + Vector((0, 0, hop))
    p["root"].rotation_euler = (tilt, 0, yaw)
    p["armL"].rotation_euler = (0, -arm[0], 0)
    p["armR"].rotation_euler = (0, arm[1], 0)
    p["mouth"].scale = (1 - 0.4 * gape, 1, 1 + 3.0 * gape)
    p["shades"].location = AWAY
    K.mood(p, angry)

def apply_state(t):
    name, age, cut, length = shot_at(t)
    q = math.floor(t * 12) / 12
    aq = age - (t - q)
    loc, tg, lens = CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    for o in [FR["root"], CUP, S_NINE, S_RIGHT, S_LAB, S_CUPS, S_SIX, S_LOST, DIARY] + MUGS:
        o.location = AWAY
    FR["hood"].location = AWAY
    FR["body"].rotation_euler = (0, 0, 0)
    BIG["shades"].location = AWAY
    K.mood(BIG, 0.8)
    BIGB.location = (0, 0, 0.04 * abs(math.sin(q * 4)))
    set_time(CLK0_H, CLK0_M, 21.0 + max(0.0, t) / 3600 * 60)
    wide_eyes(FR, q)

    if name in ("chug", "final", "right"):
        at = O0 + Vector((-0.35, -0.6, 0))
        if name == "right":
            pose(FR, at, arm=(-0.2, 0.9), angry=-0.3, gape=0.15, hop=0.05 * abs(math.sin(q * 9)))
            FR["body"].rotation_euler = (0, 0.04 * math.sin(q * 31), 0)
            drop(S_RIGHT, O0 + Vector((0.35, -0.7, 3.0)), aq, 0.5)
            K.mood(BIG, -0.6)
        else:
            sip = 0.5 + 0.5 * math.sin(q * 6)
            pose(FR, at, arm=(-1.0, 2.2), angry=0.2, gape=0.0, tilt=-0.08 - 0.08 * sip)
            CUP.location = at + Vector((0.2, -0.38, 1.38 + 0.04 * sip))
            CUP.rotation_euler = (0, -1.2 - 0.4 * sip, 0)
            if name == "chug":
                drop(S_NINE, O0 + Vector((0.4, -0.7, 2.55)), aq, 0.8)
    elif name in ("lab", "mugs", "clock"):
        BOT.rotation_euler = (0, 0, 0.05 * math.sin(q * 5))
        if name == "lab":
            drop(S_LAB, O1 + Vector((-0.4, -0.3, 3.3)), aq, 0.4)
        ta = t - start_of("mugs")
        for k, m in enumerate(MUGS):
            if ta < 0:
                continue
            drop(m, O1 + Vector((-0.45 + k * 0.5, -0.05, 1.0)), ta, 0.3 + 0.22 * k)
        if name == "mugs":
            drop(S_CUPS, O1 + Vector((0.3, -0.3, 2.55)), aq, 0.8)
        h = 17.0
        if name == "clock":
            h = 17.0 + 6.0 * smooth01((aq - 0.2) / 0.9)
            drop(S_SIX, O1 + Vector((0.75, 0.6, 2.95)), aq, 0.3)
        set_time(CLK1_H, CLK1_M, h)
    elif name in ("bed", "bar"):
        FR["root"].location = O2 + Vector((-0.9, -0.4, 0.95))
        FR["root"].rotation_euler = (-math.pi / 2 + 0.25, 0, 0)
        for e in ("armL", "armR"):
            FR[e].rotation_euler = (0, 0, 0)
        K.mood(FR, -0.5)
        for k, wv in enumerate(WAVE):
            wv.scale = (1, 1, 0.4 + 1.6 * abs(math.sin(q * 7 + k * 0.9)))
        ba = t - start_of("bar")
        for k, b in enumerate(BLOCKS):
            base = O2 + Vector((2.6, 1.8, 0.4 + k * 0.42))
            if k == 7 and ba > 0.5:
                u = (ba - 0.5)
                b.location = base + Vector((0.9 * u, -0.6 * u, 1.2 * u - 4.0 * u * u))
                b.rotation_euler = (0, 2.5 * u, 0)
            else:
                b.location = base
                b.rotation_euler = (0, 0, 0)
        if name == "bar":
            drop(S_LOST, O2 + Vector((3.8, 0.9, 2.4)), aq, 0.7)
    elif name == "diary":
        DIARY.location = O2 + Vector((-4.5, 0.4, 2.0))
        DIARY.rotation_euler = (0, 0.03 * math.sin(q * 3), 0)
        u = (aq - 0.6) / 0.25
        YES.scale = (0.001,) * 3 if u <= 0 else (max(0.001, min(1.3, 1.6 * u) if u < 1 else 1.0),) * 3

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
