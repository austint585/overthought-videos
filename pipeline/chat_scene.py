"""Blender scene for 'Nobody answered': cel-shaded sets along x, 14 m apart, each with a floor, a colored back wall and hanging
signs. Our cast are phones with their faces on the screen (you in blue, the group chat in every other color). They move in
stop motion (12 steps a second, the camera stays smooth). Shots, timed by render_chat.py: couch, chat, label, booth, alone,
group, assume, name, final (back on the chat).

blender -b --factory-startup -P chat_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
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

def phone(name, case=BLUE, screen=(0.86, 0.93, 1.0)):
    """Our cast: a phone in a colored case, the face on its screen, stubby limbs. z=0 at the feet, about 1.75 m."""
    root = K.empty(name)
    body = K.empty(name + "b", (0, 0, 0.30), root)
    K.box(name + "case", (0.82, 0.16, 1.42), case, (0, 0, 0.72), body, bevel=0.12)
    K.box(name + "scr", (0.7, 0.03, 1.24), screen, (0, -0.075, 0.72), body, bevel=0.08, line=0)
    K.box(name + "cam", (0.16, 0.02, 0.04), DARK, (0, -0.092, 1.33), body, bevel=0.015, line=0)
    parts = {"root": root, "body": body}
    face(name, body, 0.085, 0.95, parts, eye=0.085, gap=0.15)
    limbs(name, root, body, parts, tuple(c * 0.75 for c in case), 0.4, 0.62, 0.17)
    return parts

def bubble(name, text, color, txt_color, w, h=0.42, parent=None, loc=(0, 0, 0), size=0.2):
    root = K.empty(name, loc, parent)
    K.box(name + "b", (w, 0.08, h), color, (0, 0, 0), root, bevel=0.15, line=0.01)
    lab = K.label(name + "t", text, size, txt_color, (0, -0.05, 0), root)
    return root, lab

CASES = [BLUE, PINK, GOLD, GREEN, ORANGE, TEAL, RED, (0.55, 0.35, 0.85), (0.35, 0.35, 0.4), (0.95, 0.6, 0.7),
         (0.4, 0.7, 0.95), (0.7, 0.85, 0.3), (0.9, 0.4, 0.3), (0.3, 0.55, 0.5)]

# ------------------------------------------------------------------ 0 couch: night living room, you on the couch

O0 = stage(0, NAVY, WOOD)
K.box("couchb", (3.4, 1.1, 0.5), TEAL, O0 + Vector((0, 0.3, 0.45)), bevel=0.12)
K.box("couchk", (3.4, 0.35, 1.1), TEAL, O0 + Vector((0, 0.95, 0.85)), bevel=0.12)
for x in (-1.8, 1.8):
    K.box(f"couchar{x}", (0.35, 1.1, 0.85), (0.04, 0.5, 0.48), O0 + Vector((x, 0.3, 0.55)), bevel=0.12)
K.box("cush", (0.6, 0.25, 0.55), PINK, O0 + Vector((1.2, 0.65, 0.95)), rot=(0, 0.2, 0), bevel=0.15)
K.cyl("lampp", 0.05, 2.0, GREY, O0 + Vector((-2.5, 0.9, 1.0)), seg=16)
K.cyl("lamps", 0.4, 0.55, (1.0, 0.85, 0.5), O0 + Vector((-2.5, 0.9, 2.15)), seg=32, r2=0.25)
K.box("win0", (1.4, 0.1, 1.2), (0.12, 0.18, 0.40), O0 + Vector((1.6, 2.0, 3.0)), bevel=0.03)
K.ball("moon", 0.2, CREAM, O0 + Vector((1.9, 1.93, 3.25)), squash=(1, 0.3, 1), line=0.006)
B0, B0T = bubble("b0", "ANYONE FREE TONIGHT?", BLUE, (1, 1, 1), 2.0, loc=AWAY, size=0.15)
SEEN0 = K.label("seen0", "SEEN BY 14", 0.16, CREAM, AWAY)

# ------------------------------------------------------------------ 1 chat: a giant phone screen, typing dots that give up

O1 = stage(1, (0.95, 0.80, 0.35), (0.40, 0.42, 0.50))
K.box("gphone", (4.2, 0.3, 7.6), DARK, O1 + Vector((0.4, 1.4, 3.9)), bevel=0.4)
K.box("gscreen", (3.8, 0.05, 7.0), (0.97, 0.97, 0.99), O1 + Vector((0.4, 1.23, 3.9)), bevel=0.25, line=0)
K.box("gbar", (3.8, 0.06, 0.7), (0.92, 0.93, 0.96), O1 + Vector((0.4, 1.2, 6.9)), bevel=0.1, line=0)
K.label("gname", "THE GROUP CHAT (15)", 0.2, K.INK, O1 + Vector((0.4, 1.16, 6.9)))
B1, B1T = bubble("b1", "ANYONE FREE TONIGHT?", BLUE, (1, 1, 1), 3.2, 0.6, loc=O1 + Vector((0.6, 1.12, 4.6)), size=0.24)
SEEN1 = K.label("seen1", "SEEN BY 14", 0.2, DARK, O1 + Vector((1.5, 1.16, 4.08)))
DOTS = []
for i in range(3):
    r = K.empty(f"dots{i}")
    K.box(f"dotsb{i}", (1.0, 0.08, 0.5), (0.88, 0.89, 0.92), (0, 0, 0), r, bevel=0.15, line=0.008)
    for k in range(3):
        K.ball(f"dot{i}{k}", 0.06, GREY, (-0.2 + k * 0.2, -0.06, 0), r, squash=(1, 0.4, 1), line=0)
    DOTS.append(r)
DOT_AT = [O1 + Vector((-0.6, 1.1, 3.5)), O1 + Vector((-0.6, 1.1, 2.9)), O1 + Vector((-0.6, 1.1, 2.3))]
B7, B7T = bubble("b7", "SEND THIS TO THE CHAT", BLUE, (1, 1, 1), 3.2, 0.6, loc=AWAY, size=0.24)
SEEN7 = K.label("seen7", "SEEN BY 14", 0.2, DARK, AWAY)
WEED = K.empty("weed")
for i in range(9):
    a, b = i * 0.7, i * 1.3
    K.cyl(f"weedr{i}", 0.32, 0.04, (0.62, 0.45, 0.22), (0, 0, 0), WEED, rot=(a, b, 0), seg=24, r2=0.32, line=0.006)

# ------------------------------------------------------------------ 2 bleachers: the fourteen, looking anywhere else

O2 = stage(2, (0.86, 0.42, 0.52), CREAM)
for i in range(3):
    K.box(f"step{i}", (5.4, 0.9, 0.45 * (i + 1)), (0.85, 0.85, 0.88), O2 + Vector((0, 0.1 + i * 0.9, 0.225 * (i + 1))), bevel=0.03)
CROWD = []
for i in range(14):
    row, col = i // 5, i % 5
    p = phone(f"c{i}", CASES[i % len(CASES)])
    at = O2 + Vector((-2.0 + col * 1.0 + (0.5 if row == 1 else 0), 0.1 + row * 0.9 - 0.15, 0.45 * (row + 1)))
    CROWD.append((p, at))
S_BYST = K.sign("s_byst", ["BYSTANDER", "EFFECT"], AWAY, w=2.4, head="PSYCHOLOGISTS CALL IT")

# ------------------------------------------------------------------ 3 booth: 1968, a booth, a desk, an intercom

O3 = stage(3, (0.55, 0.75, 0.65), (0.45, 0.45, 0.50))
for s in (-1, 1):
    K.box(f"bwall{s}", (0.12, 2.2, 2.6), CREAM, O3 + Vector((s * 1.4, 0.6, 1.3)), bevel=0.03)
K.box("bdesk", (2.4, 0.9, 0.12), WOOD, O3 + Vector((0, 1.0, 0.95)), bevel=0.03)
K.box("bdeskl", (2.2, 0.8, 0.9), (0.5, 0.29, 0.13), O3 + Vector((0, 1.05, 0.45)), bevel=0.03)
K.box("icom", (0.7, 0.4, 0.5), GREY, O3 + Vector((0.55, 1.05, 1.26)), bevel=0.05)
K.box("icomg", (0.5, 0.03, 0.3), DARK, O3 + Vector((0.55, 0.84, 1.28)), bevel=0.03, line=0)
K.ball("icoml", 0.05, RED, O3 + Vector((0.8, 0.83, 1.46)), line=0)
WAVES = []
for i in range(0):
    w = K.cyl(f"wave{i}", 0.25 + i * 0.18, 0.02, GOLD, AWAY, rot=(math.pi / 2, 0, 0), seg=48, r2=0.25 + i * 0.18, line=0.01)
    w.scale = (1, 1, 1)
    WAVES.append(w)
S_1968 = K.sign("s_1968", ["1968"], O3 + Vector((-0.2, 0.8, 3.4)), w=1.8, head="DARLEY & LATANE")
S_REC = K.sign("s_rec", ["A RECORDING"], AWAY, w=2.2, head="IT WAS")
B3, B3T = bubble("b3", "(SEIZURE SOUNDS)", WHITE, K.INK, 1.7, 0.4, loc=AWAY, size=0.16)

# ------------------------------------------------------------------ 4 results: two bars, a door

O4 = stage(4, (0.44, 0.30, 0.72), CREAM)
K.box("rbase", (3.4, 0.9, 0.12), DARK, O4 + Vector((0.2, 0.3, 0.06)), bevel=0.02)
BARS = [K.box(f"bar{i}", (0.9, 0.7, 1.0), c, AWAY, bevel=0.04) for i, c in enumerate((GREEN, RED))]
PCT = [0.85, 0.31]
BAR_X = [-0.6, 1.0]
for i, s in enumerate(("ALONE", "+4 OTHERS")):
    K.label(f"barl{i}", s, 0.22, (1, 1, 1), O4 + Vector((BAR_X[i], -0.17, 0.06)))
BARP = [K.label(f"barp{i}", s, 0.36, (1, 1, 1), AWAY) for i, s in enumerate(("85%", "31%"))]
S_REP = K.sign("s_rep", ["REPORTED IT"], O4 + Vector((-0.3, 0.9, 3.75)), w=2.4, head="WHEN THEY HEARD IT")
K.box("rdoor", (1.0, 0.1, 2.2), (0.98, 0.85, 0.45), O4 + Vector((-2.3, 1.95, 1.1)), bevel=0.03)
K.label("rexit", "HELP", 0.2, K.INK, O4 + Vector((-2.3, 1.88, 2.4)))
RUNNER = phone("run", BLUE)
SITTERS = [phone(f"sit{i}", CASES[i + 1]) for i in range(5)]

# ------------------------------------------------------------------ 5 assume: five phones, each pointing at the next

O5 = stage(5, (0.30, 0.62, 0.85), (0.93, 0.92, 0.88))
POINTERS = [phone(f"pt{i}", CASES[(i * 3) % len(CASES)]) for i in range(5)]
S_ELSE = K.sign("s_else", ["SOMEONE ELSE", "WILL DO IT"], AWAY, w=2.6, head="EVERYONE THINKS")

# ------------------------------------------------------------------ 6 name: a spotlight on one phone

O6 = stage(6, (0.10, 0.10, 0.16), (0.20, 0.20, 0.26))
K.cyl("spotfloor", 1.0, 0.02, (0.98, 0.92, 0.6), O6 + Vector((0, -0.5, 0.01)), seg=64, line=0)
DIMS = [phone(f"dim{i}", (0.25, 0.25, 0.3), screen=(0.35, 0.37, 0.45)) for i in range(4)]
S_NAME = K.sign("s_name", ["BY NAME"], AWAY, w=2.0, head="ASK ONE PERSON")
TAG = K.empty("tag")
K.box("tagb", (1.1, 0.06, 0.32), (0.98, 0.96, 0.88), (0, 0, 0), TAG, bevel=0.05, line=0.008)
K.label("tagt", "HEY JORDAN", 0.15, BLUE, (0, -0.04, 0), TAG)

# ------------------------------------------------------------------ the cast and the camera

YOU = phone("you", BLUE)
cam = B.camera(lens=40, fstop=16.0)
cam.data.dof.use_dof = False
cam.data.clip_start = 0.05
cam.data.clip_end = 80

def lc(a, b, tg, lens, u, o):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "couch": lambda u: lc((-0.3, -6.6, 2.1), (-0.1, -6.0, 2.1), (0, 0, 1.8), 40, u, O0),
    "chat": lambda u: lc((0.4, -7.4, 3.7), (0.5, -6.9, 3.7), (0.55, 0, 3.6), 40, u, O1),
    "final": lambda u: lc((0.5, -6.8, 2.9), (0.4, -6.2, 2.9), (0.4, 0, 3.1), 40, u, O1),
    "label": lambda u: lc((-0.4, -8.4, 2.6), (-0.1, -7.8, 2.6), (0, 0, 2.4), 40, u, O2),
    "booth": lambda u: lc((-0.3, -6.4, 1.9), (-0.1, -5.8, 1.9), (0, 0, 1.8), 40, u, O3),
    "alone": lambda u: lc((-1.6, -6.4, 2.0), (-1.3, -5.8, 2.0), (-1.1, 0, 1.8), 40, u, O4),
    "group": lambda u: lc((0.6, -8.6, 2.2), (0.4, -8.0, 2.2), (0.5, 0, 2.0), 40, u, O4),
    "assume": lambda u: lc((-0.3, -8.0, 2.0), (0.1, -7.4, 2.0), (0, 0, 1.9), 40, u, O5),
    "name": lambda u: lc((0.3, -6.4, 2.1), (0.1, -5.6, 2.1), (0, 0, 1.9), 40, u, O6),
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

ALL = [YOU] + [p for p, _ in CROWD] + [RUNNER] + SITTERS + POINTERS + DIMS
for p in ALL:
    p["shades"]["home"] = p["shades"].location.copy()

def apply_state(t):
    name, u, age, cut, second, length = shot_at(t)
    q = math.floor(t * 12) / 12            # props step in stop motion
    aq = age - (t - q)
    loc, tg, lens = alt_cam(CAMS[name], cut) if second else CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens

    for o in [p["root"] for p in ALL] + [B0, SEEN0, B7, SEEN7, WEED, B3, S_BYST, S_REC, S_ELSE, S_NAME, TAG] + DOTS + WAVES + BARS + BARP:
        o.location = AWAY
    for p in ALL:
        p["root"].scale = (1, 1, 1)
    B1.location = O1 + Vector((0.6, 1.12, 4.6))
    SEEN1.location = O1 + Vector((1.5, 1.16, 4.08))

    if name == "couch":
        pop(B0, O0 + Vector((-0.3, -0.3, 2.85)), aq, 0.25)
        if aq > 1.6:
            SEEN0.location = O0 + Vector((0.3, -0.36, 2.5))
        pose(YOU, O0 + Vector((-0.4, 0.15, 0.72)), arm=(0.4, 1.2 + 0.25 * math.sin(q * 8)), yaw=0.1, angry=-0.2,
             gape=0.2 * abs(math.sin(q * 7)))
    elif name in ("chat", "final"):
        if name == "chat":
            for i, d in enumerate(DOTS):           # each friend starts typing, then gives up
                ph = aq - 0.4 - i * 0.9
                if 0 < ph < 0.75:
                    pop(d, DOT_AT[i], ph, 0.0)
            pose(YOU, O1 + Vector((-1.6, -1.2, 0)), yaw=0.35, angry=-0.6 + 0.4 * math.sin(q * 2), arm=(0.2, 0.3),
                 gape=0.1)
        else:
            B1.location = O1 + Vector((0.6, 1.12, 5.4))
            SEEN1.location = O1 + Vector((1.5, 1.16, 4.88))
            pop(B7, O1 + Vector((0.6, 1.12, 3.9)), aq, 0.3)
            if aq > 0.8:
                SEEN7.location = O1 + Vector((1.5, 1.16, 3.38))
            f = max(0.0, aq - 1.0) / 3.0
            WEED.location = O1 + Vector((-3.5 + 6.5 * f, -1.0, 0.33 + 0.25 * abs(math.sin(f * 14))))
            WEED.rotation_euler = (0, 9 * f, 0)
            pose(YOU, O1 + Vector((-1.6, -1.2, 0)), yaw=0.35, angry=0.8, arm=(0.1, 0.1), shades=True)
    elif name == "label":
        for i, (p, at) in enumerate(CROWD):
            look = 0.9 * math.sin(i * 2.3 + 1)          # anywhere but the chat
            pose(p, at, scale=0.55, yaw=look + 0.15 * math.sin(q * 3 + i), arm=(0.2, 0.2 + 0.6 * (i % 3 == 0)),
                 angry=-0.3 if i % 2 else 0.2, gape=0.0)
        drop(S_BYST, O2 + Vector((0, -0.8, 3.7)), aq, 0.25)
    elif name == "booth":
        pose(YOU, O3 + Vector((-0.4, 0.2, 0)), yaw=-0.2, arm=(0.3, 0.3), angry=-0.2)
        if second:
            a2 = t - start_of("booth~2")
            for i, w in enumerate(WAVES):
                f = (a2 * 1.2 - i * 0.25) % 1.0
                w.location = O3 + Vector((0.55, 0.78 - f * 0.4, 1.28))
                w.scale = (0.5 + f, 1, 0.5 + f)
            pose(YOU, O3 + Vector((-0.4, 0.2, 0)), yaw=0.4, arm=(1.2, 1.2), angry=-1.0, gape=0.9,
                 sway=0.05 * math.sin(q * 30))
            S_1968.location = AWAY
            pop(B3, O3 + Vector((0.9, 0.6, 1.95)), a2, 0.1)
            drop(S_REC, O3 + Vector((-0.35, -0.9, 2.75)), a2, 0.6)
    elif name in ("alone", "group"):
        a0 = t - start_of("alone")
        for i, b in enumerate(BARS):
            ti = start_of("alone") if i == 0 else start_of("group")
            h = 3.0 * PCT[i] * smooth01((t - ti - 0.3) / 0.5)
            if h > 0.01:
                b.location = O4 + Vector((BAR_X[i], 0.3, 0.12 + h / 2))
                b.scale = (1, 1, max(0.01, h))
                BARP[i].location = O4 + Vector((BAR_X[i], -0.06, 0.12 + h - 0.3))
        f = smooth01((a0 - 0.3) / 1.0)
        if f < 1:
            pose(RUNNER, O4 + Vector((-1.2 - 1.1 * f, -0.9 + 2.2 * f, 0)), scale=0.7, hop=0.12 * abs(math.sin(q * 12)),
                 yaw=-0.6, arm=(1.3 * math.sin(q * 12), -1.3 * math.sin(q * 12)), angry=-1.0, gape=0.8)
        for i, p in enumerate(SITTERS):
            pose(p, O4 + Vector((1.85 + i * 0.36, -0.7 - 0.2 * (i % 2), 0)), scale=0.42, yaw=0.2 * math.sin(i * 3),
                 angry=-0.1, arm=(0.1, 0.1))
    elif name == "assume":
        for i, p in enumerate(POINTERS):
            k = smooth01((aq - 0.3 - i * 0.18) / 0.2)
            pose(p, O5 + Vector((-2.2 + i * 1.1, -0.5, 0)), scale=0.8, yaw=-0.5 if i < 4 else 0.5,
                 arm=(0.0, 1.5 * k) if i < 4 else (1.5 * k, 0.0), angry=0.4, gape=0.3)
        drop(S_ELSE, O5 + Vector((0, 0.3, 3.4)), aq, 0.9)
    elif name == "name":
        for i, p in enumerate(DIMS):
            pose(p, O6 + Vector((-2.4 + i * 1.6 + (1.6 if i > 1 else 0), 0.6, 0)), scale=0.75, yaw=0.0, angry=0.0)
        k = smooth01((aq - 0.6) / 0.3)
        pose(YOU, O6 + Vector((0, -0.5, 0)), hop=0.25 * k * abs(math.sin(q * 6)), arm=(0.2, 2.6 * k), angry=0.6 * k - 0.3,
             gape=0.4 * k)
        pop(TAG, O6 + Vector((0, -0.6, 2.35)), aq, 0.2)
        drop(S_NAME, O6 + Vector((0, 0.3, 3.5)), aq, 0.5)

B.render_settings(FPS, samples=int(os.environ.get("CHAT_SAMPLES", "12")), motion_blur=0.0)
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
