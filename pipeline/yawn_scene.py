"""Blender scene for The Yawn Test (render_yawn.py). Toon kit (toon.py). Cast: your friend and you on beanbags at movie
night (a yawn puff drifts from them to you), and a yawner in front of four people on bleacher tiers (family, friend,
barely know, stranger), each catching the yawn later as the puff takes longer to reach them. Signs for the study and the
timing. Helpers from nap_scene.py.

blender -b --factory-startup -P yawn_scene.py -- timing.json out_dir MODE   (MODE: all or 1-based frame list)
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
FPS, DUR, SHOTS, EV = T["fps"], T["duration"], T["shots"], T["events"]
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



def tlabel(ob, body):
    if ob.data.body != body:
        ob.data.body = body

def sign_text(sg, i=0):
    return bpy.data.objects[f"{sg.name}t{i}"]

def person(name, shirt, hair=(0.30, 0.18, 0.10)):
    global SWEAT
    SWEAT = shirt
    p = friend(name)
    bpy.data.objects[name + "hair"].data.materials[0] = K.toon(hair)
    ob = bpy.data.objects.get(name + "scarf")
    if ob:
        ob.scale = (0.001,) * 3
    p["hood"].location = AWAY
    p["shades"].location = AWAY
    return p

def eyes(name, open_=1.0):
    for e in ("L", "R"):
        ob = bpy.data.objects.get(name + "eye" + e)
        if ob:
            ob.scale = (1, 1, max(0.12, open_))
        ob = bpy.data.objects.get(name + "pup" + e)
        if ob:
            ob.scale = (1, 1, 1) if open_ > 0.5 else (0.001,) * 3

def yawn(p, name, u):
    """u in 0..1 is how far into a 1.6 s yawn; 0 is a resting face."""
    k = math.sin(max(0.0, min(1.0, u)) * math.pi) if 0 < u < 1 else 0.0
    p["mouth"].scale = (1.0 - 0.3 * k, 1, 1 + 6.0 * k)
    p["mouth"].location.z = 1.42 - 0.065 * 2.4 - 0.08 * k
    eyes(name, 1.0 - 0.88 * k)
    p["armL"].rotation_euler = (0, -1.15 + 2.6 * k, 0)
    p["armR"].rotation_euler = (0, 1.15 - 2.6 * k, 0)
    p["body"].rotation_euler = (-0.12 * k, 0, 0)
    return k

def yawn_at(t, t0):
    return (t - t0) / 1.6 if t >= t0 else -1.0

def puff(name):
    root = K.empty(name, AWAY)
    for k, (x, z, r) in enumerate(((-0.08, 0, 0.09), (0.0, 0.05, 0.11), (0.09, 0.0, 0.08))):
        b = K.ball(f"{name}{k}", r, WHITE, (x, 0, z), root, squash=(1, 0.6, 1), line=0.006)
    return root

def drift(ob, a, b, t, t0, dur):
    if t < t0 or t > t0 + dur + 0.3:
        ob.location = AWAY
        return
    u = smooth01((t - t0) / dur)
    ob.location = a.lerp(b, u) + Vector((0, 0, 0.25 * math.sin(u * math.pi)))
    s = 0.6 + 0.6 * math.sin(min(1.0, (t - t0) / 0.3) * math.pi / 2) * (1 - max(0.0, (t - t0 - dur) / 0.3))
    ob.scale = (s, s, s)

def drop(ob, at, age, delay=0.0):
    if age < delay:
        ob.location = AWAY
        return
    u = (age - delay) / 0.4
    z = 4.5 * max(0.0, 1 - u) ** 2 - (0.12 * math.sin(min(u, 2.0) * 6) * max(0.0, 1 - u / 2) if u > 1 else 0)
    ob.location = at + Vector((0, 0, z))

# ------------------------------------------------------------------ 0 movie night
O0 = stage(0, (0.16, 0.18, 0.36), (0.45, 0.30, 0.22))
K.box("rug0", (3.6, 2.4, 0.03), (0.75, 0.35, 0.30), O0 + Vector((0, -0.6, 0.015)), bevel=0.01, line=0)
for k, x in enumerate((-0.55, 0.55)):
    K.ball(f"bean{k}", 0.62, (ORANGE, TEAL)[k], O0 + Vector((x, -0.2, 0.35)), squash=(1.0, 0.95, 0.6))
K.box("lamp0", (0.08, 0.08, 1.8), DARK, O0 + Vector((-1.7, 0.6, 0.9)), bevel=0, line=0.006)
K.cyl("shade0", 0.3, 0.35, (0.98, 0.85, 0.55), O0 + Vector((-1.7, 0.6, 1.9)), r2=0.2).data.materials[0] = K.flat((0.98, 0.85, 0.55))
K.box("frame0", (1.2, 0.06, 0.8), WOOD, O0 + Vector((0.9, 2.02, 2.6)), bevel=0.02)
K.box("pic0", (1.05, 0.05, 0.65), (0.55, 0.75, 0.95), O0 + Vector((0.9, 1.99, 2.6)), bevel=0, line=0)
K.ball("bowl0", 0.22, RED, O0 + Vector((0.0, -1.0, 0.1)), squash=(1, 1, 0.45))
for k in range(9):
    K.ball(f"pop{k}", 0.05, (0.99, 0.95, 0.75), O0 + Vector((-0.12 + (k % 3) * 0.12, -1.0 + (k // 3 - 1) * 0.1, 0.2)), line=0.004)
FR = person("fr", PLUM)
YOU = person("you", TEAL, hair=(0.12, 0.10, 0.10))
P0 = puff("p0")
S_TV = K.box("tvglow", (0.05, 2.0, 2.4), (0.55, 0.75, 1.0), O0 + Vector((2.3, -0.8, 1.4)), bevel=0, line=0)
S_TV.data.materials[0] = K.flat((0.55, 0.75, 1.0))
S_THINK = K.sign("s_think", ["...HUH"], AWAY, w=1.2)

# ------------------------------------------------------------------ 1 the bleachers
O1 = stage(1, (0.45, 0.72, 0.95), (0.35, 0.68, 0.28))
TIERS = []
for k in range(4):
    K.box(f"step{k}", (5.0, 0.9, 0.7 * (k + 1)), (0.80, 0.80, 0.84) if k % 2 else (0.70, 0.72, 0.78),
          O1 + Vector((0, 0.1 + 0.9 * k, 0.35 * (k + 1))), bevel=0.02)
    TIERS.append(O1 + Vector(((-0.85, -0.35, -0.85, -0.35)[k], -0.1 + 0.9 * k, 0.7 * (k + 1))))
RIDERS = []
for k, (shirt, hair) in enumerate(((RED, (0.30, 0.18, 0.10)), (GOLD, (0.12, 0.10, 0.10)),
                                    (BLUE, (0.55, 0.35, 0.15)), (GREEN, (0.20, 0.20, 0.22)))):
    RIDERS.append(person(f"r{k}", shirt, hair))
YAWNER = person("yw", PINK)
TAGS = [K.sign(f"tag{k}", [s], AWAY, w=1.55, cords=0.0) for k, s in
        enumerate(("FAMILY", "FRIEND", "BARELY KNOW", "STRANGER"))]
PUFFS = [puff(f"pf{k}") for k in range(4)]
S_STUDY = K.sign("s_study", ["109 ADULTS", "1 YEAR"], AWAY, w=1.9, head="ITALY, REAL LIFE")
S_FAM = K.sign("s_fam", ["MOST: UNDER 1 MIN"], AWAY, w=2.6, head="FAMILY")
S_FRI = K.sign("s_fri", ["HALF: UNDER 1 MIN"], AWAY, w=2.6, head="FRIENDS")
S_STR = K.sign("s_str", ["MOSTLY 2 TO 3 MIN"], AWAY, w=2.6, head="STRANGERS")
BOARD = O1 + Vector((4.6, 0.0, 0.0))
RES = person("res", WHITE, hair=(0.55, 0.55, 0.58))
CLIP = K.box("clip", (0.3, 0.04, 0.4), WOOD, AWAY, bevel=0.02)

# ------------------------------------------------------------------ camera
cam = B.camera(lens=40, fstop=16.0)
cam.data.dof.use_dof = False
cam.data.clip_start = 0.05
cam.data.clip_end = 80

def lc(a, b, tg, lens, u, o):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "couch": lambda u: lc((0.0, -5.6, 1.75), (0.0, -5.2, 1.72), (0.0, 0, 1.45), 40, u, O0),
    "study": lambda u: lc((0.0, -8.6, 3.4), (0.0, -8.1, 3.35), (0.0, 1.0, 2.9), 40, u, O1),
    "family": lambda u: lc((0.4, -5.6, 2.5), (0.35, -5.2, 2.45), (0.35, 0.4, 2.15), 40, u, O1),
    "strangers": lambda u: lc((0.1, -6.0, 4.2), (0.05, -5.6, 4.1), (0.05, 1.8, 3.5), 40, u, O1),
    "timing": lambda u: lc((4.6, -6.6, 3.3), (4.6, -6.1, 3.3), (4.6, 0.0, 3.2), 40, u, O1),
    "think": lambda u: lc((0.5, -3.4, 1.7), (0.45, -3.1, 1.7), (0.3, 0, 1.4), 40, u, O0),
    "final": lambda u: lc((0.0, -5.6, 1.75), (0.0, -5.2, 1.72), (0.0, 0, 1.45), 40, u, O0),
}

def shot_at(t):
    k = max([0] + [i for i, (s, _) in enumerate(SHOTS) if t >= s - 1e-6])
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    cut = max(0.0, min(1.0, (t - SHOTS[k][0]) / max(1e-6, t1 - SHOTS[k][0])))
    return SHOTS[k][1], t - SHOTS[k][0], cut

def start_of(n):
    return next(s for s, m in SHOTS if m == n)

def stand(p, at, rz=0.0):
    p["root"].location = at
    p["root"].rotation_euler = (0, 0, rz)

def apply_state(t):
    name, age, cut = shot_at(t)
    loc, tg, lens = CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    for o in [S_STUDY, S_FAM, S_FRI, S_STR, S_THINK] + TAGS:
        o.location = AWAY

    # ---- movie night: your friend yawns, the puff drifts over, you yawn back (on a loop for frame one and the end)
    stand(FR, O0 + Vector((-0.55, -0.35, 0.35)), 0.25)
    stand(YOU, O0 + Vector((0.55, -0.35, 0.35)), -0.25)
    for p in (FR, YOU):
        for k in ("legL", "legR"):
            p[k].rotation_euler = (1.3, 0, 0)
    think = start_of("think") <= t < start_of("final")
    if think:
        tf = t - start_of("think")
        yawn(FR, "fr", (tf - 0.2) / 1.6)
        yawn(YOU, "you", -1)
        eyes("you", 1.0)
        K.mood(YOU, 0.6 if tf > 1.2 else 0.0)
        P0.location = AWAY
    else:
        loop_t = t - start_of("final") if t >= start_of("final") else t
        u_fr = (loop_t + 0.75) / 1.6                  # frame one: your friend is at the widest point of the yawn
        u_you = (loop_t - 0.35) / 1.6 if loop_t > 0.35 else 0.0
        yawn(FR, "fr", u_fr if u_fr < 1 else -1)
        yawn(YOU, "you", u_you if u_you < 1 else -1)
        K.mood(FR, 0.0)
        K.mood(YOU, 0.0)
        drift(P0, O0 + Vector((-0.45, -0.75, 1.65)), O0 + Vector((0.45, -0.75, 1.65)), loop_t, 0.0, 0.7)

    # ---- bleachers: a yawner down front, four people up the tiers; puffs travel up, slower the farther the bond
    stand(YAWNER, O1 + Vector((-1.25, -1.35, 0.0)), -0.35)
    yt = EV["family"] - 1.0
    yawn(YAWNER, "yw", (t - yt) / 1.6 if yt <= t < yt + 1.6 else -1)
    K.mood(YAWNER, 0.0)
    eyes("yw", 1.0) if not (yt <= t < yt + 1.6) else None
    catch = [EV["family"], EV["friends"], EV["barely"], EV["last"]]
    for k, p in enumerate(RIDERS):
        stand(p, TIERS[k] + Vector((0, 0, 0)))
        K.mood(p, 0.0)
        yawn(p, f"r{k}", yawn_at(t, catch[k]) if yawn_at(t, catch[k]) < 1 else -1)
        if t >= catch[k] - 0.2 and start_of("family") <= t:
            TAGS[k].location = O1 + Vector((0.75, TIERS[k].y - O1.y - 0.35, TIERS[k].z + 1.45))
        travel = 0.5 + 0.35 * k
        drift(PUFFS[k], O1 + Vector((-1.2, -1.75, 1.65)), TIERS[k] + Vector((0, -0.35, 1.6)), t, catch[k] - travel, travel)
    if name == "study":
        stand(RES, O1 + Vector((-1.4, -1.6, 0.0)), -0.3)
        RES["armR"].rotation_euler = (0, -1.0, 0)
        CLIP.location = O1 + Vector((-1.05, -1.95, 1.05))
        drop(S_STUDY, O1 + Vector((0.0, -1.0, 4.2)), age, 0.4)
    else:
        RES["root"].location = AWAY
        CLIP.location = AWAY
    if name == "timing":
        drop(S_FAM, BOARD + Vector((0, 0.3, 4.6)), age, 0.1)
        drop(S_FRI, BOARD + Vector((0, 0.3, 3.5)), t - EV["half"], 0.0)
        if t >= EV["strangers"] - 0.4:
            drop(S_STR, BOARD + Vector((0, 0.3, 2.4)), t - EV["strangers"] + 0.4, 0.0)
        for k, p in enumerate(RIDERS):
            yawn(p, f"r{k}", -1)
            eyes(f"r{k}", 1.0)

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
