"""Blender scene for Hibernation Mode (render_hibern.py). Toon kit (toon.py). Cast: your friend rolled up in a quilt, and a
black bear. Sets along x, 40 m apart: his living room at 4:48 pm (window with the sun sliding behind a hill, a couch, a clock),
a cave (the bear asleep, one slow heartbeat), his front door (three delivery bags), the woods in fall (the bear eating
berries). Stop motion at 12 steps a second for props, smooth camera. Built from shave_scene.py.

blender -b --factory-startup -P hibern_scene.py -- timing.json out_dir MODE   (MODE: all or 1-based frame list)
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


SKIN, QUILT, QUILT2, FUR, FUR2, SNOUT, BERRY = (0.93, 0.72, 0.55), (0.30, 0.42, 0.85), (0.98, 0.72, 0.08), (0.45, 0.27, 0.14), \
    (0.36, 0.21, 0.10), (0.78, 0.60, 0.42), (0.75, 0.10, 0.35)
DUSK, DUSK2, NIGHT = (0.98, 0.55, 0.25), (0.95, 0.35, 0.40), (0.10, 0.12, 0.30)

def burrito(name):
    """Your friend: a person rolled up in a blue quilt, only the face showing. z=0 at the floor."""
    root = K.empty(name)
    body = K.empty(name + "b", (0, 0, 0), root)
    K.cyl(name + "q", 0.45, 1.25, QUILT, (0, 0, 0.625), body, seg=40)
    for k, z in enumerate((0.3, 0.75)):
        K.cyl(f"{name}band{k}", 0.455, 0.12, QUILT2, (0, 0, z), body, seg=40, line=0.006)
    K.ball(name + "hood", 0.44, QUILT, (0, 0.06, 1.38), body, squash=(1.0, 0.95, 1.0))
    K.ball(name + "head", 0.3, SKIN, (0, -0.14, 1.36), body, squash=(1, 0.6, 1))
    parts = {"root": root, "body": body}
    face(name, K.empty(name + "fc", (0, -0.0, 0), body), 0.33, 1.38, parts, eye=0.07, gap=0.11)
    for s, k in ((-1, "L"), (1, "R")):
        arm = K.empty(name + "arm" + k, (s * 0.42, -0.05, 0.95), body)
        K.box(name + "armb" + k, (0.26, 0.16, 0.14), QUILT, (s * 0.12, 0, 0), arm, bevel=0.05)
        K.ball(name + "hand" + k, 0.07, SKIN, (s * 0.27, 0, 0), arm)
        parts["arm" + k] = arm
    return parts

def bear(name):
    """A brown bear lying on its belly, head on its paws. z=0 at the floor; faces -y."""
    root = K.empty(name)
    body = K.empty(name + "b", (0, 0, 0), root)
    K.ball(name + "torso", 0.8, FUR, (0, 0.5, 0.55), body, squash=(1.0, 1.3, 0.7))
    head = K.empty(name + "hd", (0, -0.55, 0.55), body)
    K.ball(name + "skull", 0.42, FUR, (0, 0, 0), head)
    K.ball(name + "snout", 0.19, SNOUT, (0, -0.36, -0.08), head, squash=(1.1, 0.9, 0.8))
    K.ball(name + "nose", 0.07, K.INK, (0, -0.52, -0.02), head, squash=(1.2, 0.8, 0.8), line=0)
    for s in (-1, 1):
        K.ball(f"{name}ear{s}", 0.13, FUR2, (s * 0.3, 0.05, 0.33), head, squash=(1, 0.6, 1))
        K.ball(f"{name}paw{s}", 0.2, FUR2, (s * 0.3, -0.75, 0.12), body, squash=(1, 1.3, 0.6))
    shut = K.empty(name + "shut", (0, 0, 0), head)
    opened = K.empty(name + "open", AWAY, head)
    for s in (-1, 1):
        K.box(f"{name}lid{s}", (0.12, 0.02, 0.025), K.INK, (s * 0.15, -0.38, 0.1), shut, bevel=0.008, line=0)
        K.ball(f"{name}eye{s}", 0.055, K.INK, (s * 0.15, -0.36, 0.1), opened, squash=(1, 0.4, 1), line=0)
    return {"root": root, "body": body, "head": head, "shut": shut, "open": opened}

def bag(name, color, loc):
    root = K.empty(name, AWAY)
    K.box(name + "b", (0.42, 0.3, 0.5), color, (0, 0, 0.25), root, bevel=0.03)
    for s in (-1, 1):
        K.box(f"{name}h{s}", (0.03, 0.03, 0.2), K.INK, (s * 0.1, 0, 0.58), root, bevel=0, line=0)
    K.box(name + "t", (0.24, 0.03, 0.03), K.INK, (0, 0, 0.68), root, bevel=0, line=0)
    root["home"] = loc
    return root

# ------------------------------------------------------------------ 0 your friend's living room at 4:48 pm

O0 = stage(0, (0.38, 0.32, 0.58), (0.55, 0.36, 0.20))
K.box("winf", (2.4, 0.2, 2.2), CREAM, O0 + Vector((-1.6, 2.0, 3.0)), bevel=0.05)
SKYD = K.box("skyd", (2.1, 0.05, 1.9), DUSK, O0 + Vector((-1.6, 1.88, 3.0)), bevel=0, line=0)
SKYD.data.materials[0] = K.flat(DUSK)
SKYN = K.box("skyn", (2.1, 0.05, 1.9), NIGHT, AWAY, bevel=0, line=0)
SKYN.data.materials[0] = K.flat(NIGHT)
SUNB = K.ball("sunb", 0.32, SUN, AWAY, squash=(1, 0.2, 1), line=0)
SUNB.data.materials[0] = K.flat(SUN)
K.box("hill", (2.1, 0.06, 0.55), (0.25, 0.35, 0.30), O0 + Vector((-1.6, 1.84, 2.18)), bevel=0, line=0)
K.box("sill", (2.6, 0.4, 0.12), CREAM, O0 + Vector((-1.6, 1.85, 1.86)), bevel=0.03)
K.box("winbar", (0.08, 0.06, 1.9), CREAM, O0 + Vector((-1.6, 1.84, 3.0)), bevel=0, line=0)
K.box("clockb", (0.95, 0.12, 0.5), K.INK, O0 + Vector((1.8, 2.0, 3.7)), bevel=0.05)
K.label("clockt", "4:48 PM", 0.26, (0.4, 1.0, 0.5), O0 + Vector((1.8, 1.93, 3.7)))
K.box("couch", (3.0, 1.0, 0.55), RED, O0 + Vector((1.2, 1.2, 0.28)), bevel=0.08)
K.box("couchb", (3.0, 0.35, 0.9), RED, O0 + Vector((1.2, 1.65, 0.75)), bevel=0.08)
for s in (-1, 1):
    K.box(f"carm{s}", (0.3, 1.0, 0.75), (0.65, 0.10, 0.09), O0 + Vector((1.2 + s * 1.5, 1.2, 0.38)), bevel=0.07)
K.box("lamp", (0.06, 0.06, 2.2), DARK, O0 + Vector((3.2, 1.6, 1.1)), bevel=0, line=0.004)
SHADE = K.cyl("shade", 0.35, 0.4, GOLD, O0 + Vector((3.2, 1.6, 2.3)), seg=24, r2=0.22)
ZZZ = [K.label(f"z{k}", "Z", 0.3 + 0.1 * k, CREAM, AWAY) for k in range(3)]
BAGS0 = [bag(f"bg0{k}", c, O0 + Vector((-0.7 + 0.5 * k, -0.6, 0))) for k, c in enumerate((RED, GREEN, ORANGE))]
S_MODE = K.sign("s_mode", ["HIBERNATION", "MODE"], AWAY, w=2.3, head="HE CALLS IT")
S_EAT = K.sign("s_eat", ["EATING PART"], AWAY, w=2.2, head="TECHNICALLY")
S_SUN = K.sign("s_sun", ["EARLY DEC"], AWAY, w=2.0, head="EARLIER UNTIL")

# ------------------------------------------------------------------ 1 the cave: a black bear hibernating

O1 = stage(1, (0.20, 0.17, 0.24), (0.32, 0.28, 0.30))
for k in range(16):
    a = math.pi * k / 15
    random.seed(200 + k)
    K.ball(f"rock{k}", random.uniform(0.5, 0.8), ROCK, O1 + Vector((3.0 * math.cos(a), 0.9, 0.3 + 3.2 * math.sin(a))))
BEAR = bear("bear")
HEART = heart("heart", RED, r=0.28)
S_BPM = K.sign("s_bpm", ["8 BPM"], AWAY, w=1.6, head="HEART RATE")
S_MONTHS = K.sign("s_months", ["NO FOOD", "NO WATER", "NO TOILET"], AWAY, w=1.9, head="FOR MONTHS")

# ------------------------------------------------------------------ 2 the front door: deliveries

O2 = stage(2, CREAM, (0.45, 0.45, 0.48))
K.box("door", (1.5, 0.15, 3.0), WOOD, O2 + Vector((0, 2.0, 1.5)), bevel=0.04)
K.ball("knob", 0.08, GOLD, O2 + Vector((0.5, 1.88, 1.45)))
K.box("mat", (1.8, 1.0, 0.04), (0.55, 0.25, 0.15), O2 + Vector((0, 1.2, 0.02)), bevel=0.01, line=0)
K.label("matt", "GO AWAY", 0.2, CREAM, O2 + Vector((0, 1.2, 0.05))).rotation_euler = (0, 0, 0)
BAGS2 = [bag(f"bg2{k}", c, O2 + Vector((-0.75 + 0.75 * k, 0.9, 0))) for k, c in enumerate((RED, GREEN, ORANGE))]
S_DEL = K.sign("s_del", ["3 SINCE", "SUNDAY"], AWAY, w=1.8, head="DELIVERIES")

# ------------------------------------------------------------------ 3 the woods in fall: the bear eats

O3 = stage(3, (0.98, 0.70, 0.40), (0.55, 0.42, 0.18))
for k, x in enumerate((-2.6, -1.4, 2.0, 3.0)):
    K.ball(f"bush{k}", 0.7, (0.80, 0.42, 0.10) if k % 2 else (0.70, 0.28, 0.12), O3 + Vector((x, 1.2, 0.5)))
    for j in range(5):
        random.seed(300 + 10 * k + j)
        K.ball(f"ber{k}{j}", 0.08, BERRY, O3 + Vector((x + random.uniform(-0.5, 0.5), 0.55, 0.4 + random.uniform(0, 0.6))), line=0.004)
PILE = K.empty("pile", O3 + Vector((0.9, -0.1, 0)))
for j in range(14):
    random.seed(400 + j)
    K.ball(f"pb{j}", 0.1, BERRY, (random.uniform(-0.3, 0.3), random.uniform(-0.2, 0.2), 0.08 + 0.1 * (j // 5)), PILE, line=0.004)
BEAR2 = bear("bear2")
S_CAL = K.sign("s_cal", ["20,000"], AWAY, w=1.8, head="CALORIES A DAY")

# ------------------------------------------------------------------ cast and camera

FR = burrito("fr")
FR["shades"]["home"] = FR["shades"].location.copy()
cam = B.camera(lens=40, fstop=16.0)
cam.data.dof.use_dof = False
cam.data.clip_start = 0.05
cam.data.clip_end = 80

def lc(a, b, tg, lens, u, o):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "room": lambda u: lc((-0.6, -5.6, 2.4), (-0.4, -5.0, 2.3), (-0.3, 0, 1.9), 40, u, O0),
    "mode": lambda u: lc((0.3, -6.6, 2.5), (0.2, -6.1, 2.45), (0.1, 0, 2.75), 40, u, O0),
    "cave": lambda u: lc((0.5, -6.8, 2.2), (0.3, -6.2, 2.1), (0, 0, 2.05), 40, u, O1),
    "months": lambda u: lc((-0.5, -6.6, 2.2), (-0.3, -6.1, 2.1), (0, 0, 2.05), 40, u, O1),
    "door": lambda u: lc((0.3, -6.8, 2.2), (0.1, -6.2, 2.1), (0, 0, 1.8), 40, u, O2),
    "berry": lambda u: lc((-0.3, -6.8, 2.2), (0.0, -6.2, 2.1), (0.0, 0, 2.05), 40, u, O3),
    "eat": lambda u: lc((0.4, -6.4, 2.4), (0.3, -5.9, 2.35), (0.1, 0, 2.6), 40, u, O0),
    "sunset": lambda u: lc((-1.6, -3.6, 2.9), (-1.6, -3.2, 2.9), (-1.6, 2.0, 2.9), 40, u, O0),
    "final": lambda u: lc((0.4, -6.4, 2.8), (0.2, -5.8, 2.6), (0.6, 0, 1.6), 40, u, O0),
}

def shot_at(t):
    k = max([0] + [i for i, (s, _) in enumerate(SHOTS) if t >= s - 1e-6])
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    cut = max(0.0, min(1.0, (t - SHOTS[k][0]) / max(1e-6, t1 - SHOTS[k][0])))
    return SHOTS[k][1], t - SHOTS[k][0], cut, t1 - SHOTS[k][0]

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

def pose(p, at, hop=0.0, sway=0.0, arm=(0.0, 0.0), angry=0.0, yaw=0.0, gape=0.0, lie=0.0):
    p["root"].location = at + Vector((0, 0, hop))
    p["root"].rotation_euler = (0, sway + lie, yaw)
    p["armL"].rotation_euler = (0, -arm[0], 0)
    p["armR"].rotation_euler = (0, arm[1], 0)
    p["mouth"].scale = (1 - 0.4 * gape, 1, 1 + 3.0 * gape)
    p["shades"].location = AWAY
    K.mood(p, angry)

def sky(dark, sun_z):
    SKYD.location = AWAY if dark else O0 + Vector((-1.6, 1.88, 3.0))
    SKYN.location = O0 + Vector((-1.6, 1.88, 3.0)) if dark else AWAY
    SUNB.location = O0 + Vector((-1.2, 1.86, sun_z)) if not dark else AWAY

def apply_state(t):
    name, age, cut, length = shot_at(t)
    q = math.floor(t * 12) / 12            # props step in stop motion
    aq = age - (t - q)
    loc, tg, lens = CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens

    for o in [FR["root"], BEAR["root"], BEAR2["root"], HEART, S_MODE, S_EAT, S_SUN, S_BPM, S_MONTHS, S_DEL, S_CAL] + ZZZ + BAGS0 + BAGS2:
        o.location = AWAY
    sky(False, 2.6)

    if name in ("room", "mode"):
        if name == "room":                 # the sun slides behind the hill; he wraps himself up and waddles to the couch
            sky(False, 2.75 - 0.6 * smooth01(aq / max(0.8, length)))
            pose(FR, O0 + Vector((-0.2 + 0.25 * smooth01(aq / 1.6), -0.3, 0)), hop=0.05 * abs(math.sin(q * 7)),
                 sway=0.08 * math.sin(q * 7), arm=(-0.3, -0.3), angry=-0.6, gape=0.1)
        else:
            sky(False, 2.1)
            pose(FR, O0 + Vector((0.1, -0.3, 0)), arm=(0.2, 1.2), angry=-0.9, gape=0.25, yaw=0.15 * math.sin(q * 3))
            drop(S_MODE, O0 + Vector((0.1, -0.5, 3.35)), aq, 0.35)
    elif name in ("cave", "months"):
        BEAR["root"].location = O1 + Vector((0, 0, 0))
        BEAR["shut"].location = (0, 0, 0)
        BEAR["open"].location = AWAY
        breath = 1 + 0.03 * math.sin(t * 1.4)
        BEAR["body"].scale = (1, 1, breath)
        if name == "cave":                 # one slow heartbeat
            v = max(0.0, aq - 0.6)
            beat = 1 + 0.25 * math.exp(-((v - 0.2) / 0.12) ** 2) + 0.15 * math.exp(-((v - 0.55) / 0.12) ** 2)
            pop(HEART, O1 + Vector((-0.9, -1.2, 1.9)), aq, 0.2, s=beat)
            drop(S_BPM, O1 + Vector((0.5, -0.6, 3.0)), aq, 0.5)
        else:
            drop(S_MONTHS, O1 + Vector((0.0, -0.6, 3.0)), aq, 0.3)
    elif name == "door":
        for k, b in enumerate(BAGS2):
            pop(b, b["home"], aq, 0.3 + 0.45 * k)
        drop(S_DEL, O2 + Vector((0, 0.6, 2.75)), aq, 1.0)
    elif name == "berry":
        BEAR2["root"].location = O3 + Vector((-0.4, 0.4, 0))
        BEAR2["root"].rotation_euler = (0, 0, 0.3)
        BEAR2["open"].location = (0, 0, 0)
        BEAR2["shut"].location = AWAY
        BEAR2["head"].rotation_euler = (0.25 + 0.2 * abs(math.sin(q * 6)), 0, 0.3)
        drop(S_CAL, O3 + Vector((0.5, 0.0, 3.0)), aq, 0.4)
    elif name == "eat":
        for b in BAGS0:
            b.location = b["home"]
        chew = abs(math.sin(q * 8))
        pose(FR, O0 + Vector((0.1, -0.3, 0)), arm=(0.3, 2.3 + 0.3 * chew), angry=-0.4, gape=0.3 * chew)
        drop(S_EAT, O0 + Vector((0.1, -0.5, 3.35)), aq, 0.4)
    elif name == "sunset":
        sky(False, 2.35 - 0.5 * smooth01(aq / max(0.8, length)))
        drop(S_SUN, O0 + Vector((-1.6, 1.0, 3.25)), aq, 0.4)
    elif name == "final":                  # dark outside, asleep on the couch, Zzz
        sky(True, 0)
        for b in BAGS0:
            b.location = b["home"]
        pose(FR, O0 + Vector((0.0, 1.1, 1.0)), lie=math.pi / 2, arm=(0.0, 0.0), angry=-0.3)
        FR["root"].location += Vector((0, 0, 0.02 * math.sin(t * 2)))
        for k, z in enumerate(ZZZ):
            ph = (aq * 0.8 + k / 3) % 1.0
            z.location = O0 + Vector((-0.6 + 0.3 * k + 0.2 * ph, 0.8, 1.6 + 0.9 * ph))
            z.scale = (max(0.001, min(1.0, 4 * (1 - ph))),) * 3
    if name not in ("room", "mode", "eat", "final"):
        FR["root"].location = AWAY

B.render_settings(FPS, samples=int(os.environ.get("HB_SAMPLES", "12")), motion_blur=0.0)
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
