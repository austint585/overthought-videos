"""Blender scene for 'Your friend is a bowerbird': a clay forest floor in daylight with three satin bowerbird bowers. Our
guy's bower in the middle, the neighbor's on the left (he robs it, then wrecks it), the popular guy's on the right (he
gets everyone). A green female visits, leaves, and a robot female on a pole stands in for her, like the 2002 study.

blender -b --factory-startup -P bower_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Always writes out_dir/anchors.json: screen positions of label points for every frame.

Real scale: a bird is about 0.33 m long, a bower about 0.3 m tall. Ground top is z = 0; parts lying on it sit a few
millimetres up so no two surfaces share a plane.
"""
import json, math, os, random, sys
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bkit as B
import clay as C

argv = sys.argv[sys.argv.index("--") + 1:]
TIMING, OUT, MODE = argv[0], argv[1], argv[2]
T = json.load(open(TIMING))
FPS, DUR, E = T["fps"], T["duration"], T["events"]
NF = int(round(DUR * FPS))
os.makedirs(OUT, exist_ok=True)
B.clear_scene()
scene = B.scene
AWAY = Vector((0, 0, -1.0e5))

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

def ramp(t, t0, t1):
    return smooth01((t - t0) / (t1 - t0))

def lerp(a, b, u):
    return a + (b - a) * u

_mats = {}
def col(color, rough=0.6, prints=0.2):
    key = (color, rough, prints)
    if key not in _mats:
        _mats[key] = C.clay(f"c{len(_mats)}", color, rough, prints=prints)
    return _mats[key]

rng = random.Random(7)

# ------------------------------------------------------------------ the forest floor

GROUND = C.clay("soil", (0.22, 0.15, 0.09), 0.9, prints=0.0, dents=0.5)
C.soft("ground", (9.0, 9.0, 0.3), GROUND, (0.5, 1.5, -0.15), r=0.05, wobble=0.01)
LEAFC = [(0.55, 0.30, 0.10), (0.42, 0.22, 0.08), (0.62, 0.42, 0.16), (0.35, 0.28, 0.12), (0.50, 0.36, 0.14)]
CLEAR = [(0.0, -0.25, 0.45), (-1.25, 0.35, 0.45), (1.5, 0.7, 0.55)]          # leaf-free courts in front of each bower
n = 0
while n < 170:
    x, y = rng.uniform(-2.8, 3.2), rng.uniform(-1.6, 3.0)
    if any((x - cx) ** 2 + (y - cy) ** 2 < r * r for cx, cy, r in CLEAR):
        continue
    C.ball(f"leaf{n}", rng.uniform(0.025, 0.045), col(rng.choice(LEAFC), 0.8, 0.0), (x, y, 0.005 + 0.002 * (n % 3)),
           squash=(1.0, 0.55, 0.12), wobble=0.002).rotation_euler = (0, 0, rng.uniform(0, math.pi))
    n += 1
BARK = col((0.18, 0.12, 0.07), 0.85, 0.0)
for k in range(9):                                                        # tree trunks behind, out of focus
    x, y = -3.0 + k * 0.85 + rng.uniform(-0.25, 0.25), rng.uniform(2.4, 4.0)
    C.soft(f"trunk{k}", (0.35, 0.35, 7.0), BARK, (x, y, 3.4), r=0.15, wobble=0.03)
FERN = [col((0.18, 0.38, 0.12), 0.7, 0.0), col((0.24, 0.45, 0.14), 0.7, 0.0), col((0.14, 0.30, 0.10), 0.7, 0.0)]
for k in range(26):                                                       # ferns and bushes along the back
    x, y = rng.uniform(-2.8, 3.2), rng.uniform(1.6, 2.6)
    C.ball(f"bush{k}", rng.uniform(0.18, 0.35), FERN[k % 3], (x, y, 0.1), squash=(1.4, 1.0, 0.75), wobble=0.03)
LOG = C.soft("log", (0.75, 0.2, 0.2), col((0.30, 0.20, 0.11), 0.85, 0.0), (1.05, 0.05, 0.1), r=0.09, wobble=0.012,
             rot=(0, 0, 0.35))

# ------------------------------------------------------------------ bowers: two walls of sticks, a straw mat, blue things

STICK = [col((0.42, 0.31, 0.17), 0.85, 0.0), col((0.50, 0.38, 0.22), 0.85, 0.0), col((0.36, 0.26, 0.15), 0.85, 0.0)]
STRAW = col((0.80, 0.66, 0.36), 0.85, 0.0)
BLUE = [C.glossy("blue0", (0.04, 0.22, 0.85), 0.25), C.glossy("blue1", (0.10, 0.40, 0.95), 0.2), C.glossy("blue2", (0.02, 0.10, 0.55), 0.3)]

def bower(name, bx, by, height=0.3, rich=1.0):
    sticks = []
    for side in (-1, 1):
        for i in range(17):
            y = by - 0.16 + i * 0.02 + rng.uniform(-0.006, 0.006)
            L = height * rng.uniform(0.85, 1.12)
            tilt = -side * rng.uniform(0.18, 0.32)
            p = Vector((bx + side * 0.075 + rng.uniform(-0.01, 0.01), y, L / 2 * math.cos(tilt) + 0.004))
            r = (rng.uniform(-0.06, 0.06), tilt, rng.uniform(0, math.pi))
            ob = C.soft(f"{name}.st{side}_{i}", (0.011, 0.011, L), STICK[i % 3], p, r=0.005, wobble=0.0015, rot=r)
            sticks.append((ob, p.copy(), r))
    C.soft(f"{name}.mat", (0.42, 0.34, 0.012), STRAW, (bx, by - 0.36, 0.008), r=0.005, wobble=0.003)
    items = []
    for k in range(int(5 * rich)):                                        # bottle caps
        p = (bx + rng.uniform(-0.17, 0.17), by - 0.36 + rng.uniform(-0.13, 0.13), 0.021)
        items.append(C.soft(f"{name}.cap{k}", (0.03, 0.03, 0.012), BLUE[k % 3], p, r=0.004, wobble=0))
    for k in range(int(5 * rich)):                                        # straws, lying flat
        p = (bx + rng.uniform(-0.15, 0.15), by - 0.36 + rng.uniform(-0.12, 0.12), 0.019 + 0.009 * (k % 2))
        items.append(C.soft(f"{name}.straw{k}", (0.17, 0.008, 0.008), BLUE[(k + 1) % 3], p, r=0.0039, wobble=0,
                            rot=(0, 0, rng.uniform(0, math.pi))))
    for k in range(int(3 * rich)):                                        # clothes pegs and feathers
        p = (bx + rng.uniform(-0.16, 0.16), by - 0.36 + rng.uniform(-0.12, 0.12), 0.022)
        items.append(C.soft(f"{name}.peg{k}", (0.07, 0.014, 0.016), BLUE[(k + 2) % 3], p, r=0.005, wobble=0,
                            rot=(0, 0, rng.uniform(0, math.pi))))
    return sticks

HERO_B = bower("hb", 0.0, 0.0)
NEIGH_B = bower("nb", -1.25, 0.6, 0.33, 1.6)
CHAMP_B = bower("cb", 1.5, 1.05, 0.34, 2.0)
STOLEN = C.soft("stolen", (0.03, 0.03, 0.012), BLUE[1], (0, 0, 0), r=0.004, wobble=0)

# ------------------------------------------------------------------ birds

MALE = C.clay("male", (0.025, 0.028, 0.075), 0.22, prints=0.15)
MALE2 = C.clay("male_wing", (0.035, 0.04, 0.11), 0.2, prints=0.15)
HEN = C.clay("hen", (0.33, 0.40, 0.17), 0.6, prints=0.15)
HEN2 = C.clay("hen_wing", (0.40, 0.31, 0.13), 0.6, prints=0.15)
BEAK = C.clay("beak", (0.80, 0.84, 0.86), 0.4, prints=0.0)
HBEAK = C.clay("hbeak", (0.25, 0.22, 0.17), 0.5, prints=0.0)
LEG = col((0.55, 0.45, 0.35), 0.6, 0.0)
IRIS = C.glossy("iris", (0.30, 0.25, 0.95), 0.1)
PUPIL = C.glossy("pupil", (0.01, 0.01, 0.015), 0.1)

def bird(name, male=True):
    body_m, wing_m, beak_m = (MALE, MALE2, BEAK) if male else (HEN, HEN2, HBEAK)
    root = C.empty(name)
    f = {"root": root}
    body = C.empty(f"{name}.body", (0, 0, 0.0), root)
    C.ball(f"{name}.torso", 0.075, body_m, (0, 0.01, 0.13), body, squash=(0.85, 1.3, 0.9), wobble=0.003)
    for sx in (-1, 1):
        C.soft(f"{name}.leg{sx}", (0.012, 0.012, 0.085), LEG, (0.025 * sx, 0.0, 0.045), root, r=0.005, wobble=0)
        C.soft(f"{name}.foot{sx}", (0.03, 0.04, 0.01), LEG, (0.025 * sx, -0.012, 0.006), root, r=0.004, wobble=0)
        w = C.empty(f"{name}.wing{sx}", (0.062 * sx, 0.0, 0.155), body)
        C.ball(f"{name}.wingb{sx}", 0.052, wing_m, (0.004 * sx, 0.03, -0.01), w, squash=(0.42, 1.45, 0.75), wobble=0.002)
        f["wing" + ("L" if sx < 0 else "R")] = w
    tail = C.empty(f"{name}.tailp", (0, 0.1, 0.125), body)
    C.soft(f"{name}.tail", (0.055, 0.13, 0.016), wing_m, (0, 0.06, 0), tail, r=0.007, wobble=0.002)
    tail.rotation_euler = (-0.35, 0, 0)
    f["tail"] = tail
    head = C.empty(f"{name}.head", (0, -0.075, 0.185), body)
    C.ball(f"{name}.skull", 0.047, body_m, (0, 0, 0.012), head, squash=(0.95, 1.05, 1.0), wobble=0.002)
    C.soft(f"{name}.beak", (0.024, 0.048, 0.015), beak_m, (0, -0.06, 0.008), head, r=0.0065, wobble=0)
    jaw = C.empty(f"{name}.jawp", (0, -0.035, 0.0), head)
    C.soft(f"{name}.jaw", (0.02, 0.036, 0.009), beak_m, (0, -0.018, -0.002), jaw, r=0.004, wobble=0)
    f["jaw"] = jaw
    for sx in (-1, 1):
        C.ball(f"{name}.eye{sx}", 0.011, IRIS, (0.034 * sx, -0.026, 0.024), head, wobble=0)
        C.ball(f"{name}.pupil{sx}", 0.0055, PUPIL, (0.041 * sx, -0.032, 0.026), head, wobble=0)
    f["head"] = head
    f["body"] = body
    return f

HERO = bird("hero")
NEIGH = bird("neigh")
CHAMP = bird("champ")
HENB = bird("hen", male=False)
YOUNG = bird("young", male=False)
HAREM = [bird(f"harem{i}", male=False) for i in range(4)]
# the robot: a hen skin on a metal pole with a servo box and a cable, like the study's remote-controlled female
ROBOT = bird("robot", male=False)
METAL = C.glossy("metal", (0.55, 0.56, 0.58), 0.25)
ROBO_BASE = C.empty("robobase")
C.soft("robo.pole", (0.012, 0.012, 0.09), METAL, (0, 0, 0.045), ROBO_BASE, r=0.005, wobble=0)
C.soft("robo.box", (0.07, 0.05, 0.025), col((0.12, 0.12, 0.13), 0.4, 0.0), (0, 0.02, 0.014), ROBO_BASE, r=0.006, wobble=0)
C.soft("robo.led", (0.008, 0.004, 0.008), C.glow("led", (1.0, 0.1, 0.05), 6.0), (0.022, -0.006, 0.02), ROBO_BASE, r=0.003, wobble=0)
C.soft("robo.cable", (0.006, 0.6, 0.006), col((0.05, 0.05, 0.05), 0.5, 0.0), (0.03, 0.33, 0.006), ROBO_BASE, r=0.0029, wobble=0)

def place(f, p, heading=0.0, scale=1.0):
    f["root"].location = p
    f["root"].rotation_euler = (0, 0, heading)
    f["root"].scale = (scale,) * 3

def pose(f, t, bob=0.0, flick=0.0, beak=0.0, head_dip=0.0, head_turn=0.0, puff=1.0, tail_up=0.0, buzz=0.0):
    f["body"].location = (0, 0, bob + buzz * 0.004 * math.sin(t * 90))
    f["body"].scale = (puff, puff, puff)
    f["wingL"].rotation_euler = (0, -flick, 0)
    f["wingR"].rotation_euler = (0, flick, 0)
    f["jaw"].rotation_euler = (beak, 0, 0)
    f["head"].rotation_euler = (head_dip, 0, head_turn)
    f["tail"].rotation_euler = (-0.35 + tail_up, 0, 0)

def hide(f):
    f["root"].location = AWAY

def face(a, b):
    """Heading that points the bird's beak (-y) from a toward b."""
    return math.atan2(b[0] - a[0], -(b[1] - a[1]))

# ------------------------------------------------------------------ lights and camera

world = bpy.data.worlds.new("bg")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.42, 0.55, 0.62, 1)
bg.inputs["Strength"].default_value = 0.55
B.sun("sun", 225, 40, 3.2, (1.0, 0.88, 0.70), 2.5)
B.area("fill", Vector((-1.5, -2.5, 1.6)), Vector((0, 0, 0.1)), 3.0, 120.0, (0.7, 0.8, 1.0))
B.area("rim", Vector((1.0, 2.0, 1.2)), Vector((0, 0, 0.15)), 1.5, 60.0, (1.0, 0.85, 0.65))
cam = B.camera(lens=32, fstop=2.8)
B.render_settings(FPS, samples=24, motion_blur=0.3, look="AgX - Punchy")
C.cpu_preview_quality(samples=48)

# ------------------------------------------------------------------ motion

H0 = Vector((0.13, -0.3, 0))        # his spot on the court
D0 = Vector((0.0, -0.3, 0))         # where he dances, facing the bower
N0 = Vector((-1.15, 0.2, 0))        # the neighbor's court
AVE = Vector((0.0, -0.11, 0))       # in the front of his bower avenue
T_GO, T_THERE = E["stolen"] - 0.35, E["stolen"] + 0.45
T_BACK0, T_BACK1 = E["wreck"] + 0.7, E["wreck"] + 1.35

def hop(a, b, t, t0, t1, height=0.07, hops=4):
    u = smooth01((t - t0) / (t1 - t0))
    p = a.lerp(b, u)
    p.z = height * abs(math.sin(math.pi * hops * u))
    return p

def hero_state(t):
    """Location, heading, and whether he is carrying the stolen cap."""
    if t < T_GO:
        return H0, -0.35 + 0.25 * math.sin(t * 0.9), False
    if t < T_THERE:
        return hop(H0, N0, t, T_GO, T_THERE), face(H0, N0), False
    if t < E["wreck"]:
        return N0, face(N0, (-1.25, 0.6)), t > E["stolen"] + 0.75
    if t < T_BACK0:                    # lunges into the bower, back out
        u = math.sin(math.pi * ramp(t, E["wreck"] - 0.1, T_BACK0 - 0.1))
        return N0.lerp(Vector((-1.25, 0.42, 0)), u), face(N0, (-1.25, 0.6)), True
    if t < T_BACK1:
        return hop(N0, D0, t, T_BACK0, T_BACK1), face(N0, D0), True
    if t < E["G"]:
        return D0, math.pi, t < T_BACK1 + 0.3
    return H0, -0.3 + 0.2 * math.sin(t * 0.7), False

def apply_hero(t):
    p, h, carry = hero_state(t)
    place(HERO, p, h)
    moving = T_GO <= t < T_THERE or T_BACK0 <= t < T_BACK1
    bob = 0.006 * math.sin(t * 7) if not moving else 0.0
    if t < E["B"]:                     # tidying: quick head dips
        pose(HERO, t, bob, head_dip=0.5 * max(0, math.sin(t * 4.5)) if t > E["deep"] - 0.3 else 0.0,
             head_turn=0.3 * math.sin(t * 1.3))
    elif t < T_GO:                     # placing a cap, then looking proud
        dip = 0.7 * math.sin(math.pi * ramp(t, E["decor"] + 0.2, E["decor"] + 0.9))
        pose(HERO, t, bob, head_dip=dip, head_turn=0.25 * math.sin(t * 1.1), flick=0.15 * max(0, math.sin(t * 3)))
    elif t < E["wreck"]:
        sneak = 0.0 if moving else 0.25 * math.sin(t * 2.0)
        pose(HERO, t, bob - 0.01, head_turn=sneak, head_dip=0.2 if t > E["D"] else 0.0)
    elif t < T_BACK0:                  # kicking it apart
        pose(HERO, t, bob, flick=0.9 * abs(math.sin(t * 14)), head_dip=0.6 * abs(math.sin(t * 11)), tail_up=0.3)
    elif t < E["G"]:
        u = t - T_BACK1
        dance = t > E["dance"] - 0.2
        flick = (0.6 + 0.6 * abs(math.sin(u * 6.5))) if dance else 0.1
        buzz = 1.0 if E["buzz"] <= t < E["imp"] + 0.4 else 0.0
        beak = 0.55 * abs(math.sin(u * 9)) if E["imp"] <= t < E["strong"] else 0.0
        puff = 1.0
        if E["strong"] <= t < E["robot"]:  # comes on too strong
            puff = 1.0 + 0.4 * ramp(t, E["strong"], E["strong"] + 0.3)
            flick, buzz, beak = 1.35 + 0.15 * math.sin(u * 20), 1.0, 0.6
        elif t >= E["robot"]:            # tones it down for the robot
            flick = 0.4 + 0.35 * abs(math.sin(u * 4))
        pose(HERO, t, 0.012 * abs(math.sin(u * 6.5)) if dance else bob, flick=flick, beak=beak, puff=puff,
             tail_up=0.35 if dance else 0.0, buzz=buzz, head_dip=-0.25 if t >= E["strong"] and t < E["robot"] else 0.0)
    else:
        if t >= E["I"]:                  # fixing his straws, then waiting
            dip = 0.6 * max(0, math.sin((t - E["I"]) * 5)) if t < E["season"] else 0.0
            pose(HERO, t, bob, head_dip=dip, head_turn=0.0 if t < E["season"] else 0.4 * ramp(t, E["season"], E["season"] + 0.6))
        else:                            # showing off the outfit
            pose(HERO, t, bob, head_turn=0.3 * math.sin(t * 1.4), flick=0.2, tail_up=0.15)
    beak_tip = HERO["head"].matrix_world @ Vector((0, -0.085, 0.0))
    if carry:
        STOLEN.location = beak_tip
    elif t < E["stolen"]:
        STOLEN.location = (-1.17, 0.27, 0.021)
    else:
        STOLEN.location = (0.09, -0.4, 0.021)

def apply_others(t):
    # the neighbor's sticks fly when he wrecks it
    for i, (ob, p0, r0) in enumerate(NEIGH_B):
        t0 = E["wreck"] + 0.05 + (i % 7) * 0.05
        if t < t0:
            ob.location, ob.rotation_euler = p0, r0
            continue
        rr = random.Random(i)
        v = Vector((rr.uniform(-0.9, 0.9), rr.uniform(0.2, 1.1), rr.uniform(0.8, 1.6)))
        tl = 2 * v.z / 9.8 + 0.02
        u = min(t - t0, tl)
        q = p0 + v * u
        q.z = max(0.01, p0.z + v.z * u - 4.9 * u * u)
        landed = t - t0 >= tl or q.z <= 0.011
        if landed:
            q.z = 0.01
        ob.location = q
        spin = rr.uniform(6, 14) * u
        ob.rotation_euler = (math.pi / 2, 0, r0[2] + spin) if landed else (r0[0] + spin, r0[1] + spin * 0.6, r0[2])
    # the hen: hops in, watches, then flies off when he comes on too strong
    if E["E"] - 0.1 <= t < E["leaves"] + 1.4:
        if t < E["leaves"]:
            p = hop(Vector((0.55, 0.45, 0)), AVE, t, E["E"] - 0.1, E["E"] + 0.6, 0.06, 4)
            place(HENB, p, face(p, D0) if t > E["E"] + 0.6 else face((0.55, 0.45), AVE))
            startle = ramp(t, E["strong"] + 0.1, E["strong"] + 0.3)
            pose(HENB, t, 0.004 * math.sin(t * 5), head_turn=0.2 * math.sin(t * 1.6) * (1 - startle), head_dip=-0.3 * startle,
                 flick=0.5 * startle)
        else:
            u = (t - E["leaves"]) / 1.2
            p = AVE + Vector((0.9 * u, 1.3 * u, 0.15 + 1.1 * u * u))
            place(HENB, p, face(AVE, (0.9, 1.3)))
            pose(HENB, t, flick=0.9 + 0.8 * math.sin(t * 40), tail_up=0.2)
    else:
        hide(HENB)
    # the robot female, from the study, in his bower
    if E["robot"] <= t < E["G"]:
        crouch = 0.5 + 0.5 * math.sin((t - E["robot"]) * 2.2)
        place(ROBOT, AVE + Vector((0, 0, 0.09)), face(AVE, D0))
        pose(ROBOT, t, -0.025 * crouch, head_turn=0.5 * math.sin((t - E["robot"]) * 1.3) if crouch < 0.5 else 0.0,
             flick=0.25 * crouch)
        ROBO_BASE.location = AVE
    else:
        hide(ROBOT)
        ROBO_BASE.location = AWAY
    # the neighbor comes home to his wrecked bower
    if t >= E["G"] - 0.1:
        place(NEIGH, Vector((-1.2, 0.25, 0)), face((-1.2, 0.25), (-1.25, 0.6)) + 0.3)
        pose(NEIGH, t, -0.015, head_dip=0.45, head_turn=0.15 * math.sin(t * 0.8))
    else:
        hide(NEIGH)
    # the popular guy and everyone
    cp = Vector((1.5, 0.62, 0))
    place(CHAMP, cp, 0.1 * math.sin(t * 0.8))
    pose(CHAMP, t, 0.01 * abs(math.sin(t * 5)), flick=0.5 + 0.4 * abs(math.sin(t * 5)), tail_up=0.3, head_turn=0.3 * math.sin(t * 1.7))
    for i, f in enumerate(HAREM):
        if t >= E["G"] - 0.1:
            p = cp + Vector(((-0.28, 0.28, -0.13, 0.15)[i], (-0.18, -0.2, -0.33, -0.36)[i], 0))
            place(f, p, face(p, cp))
            pose(f, t, 0.004 * math.sin(t * 4 + i), head_turn=0.15 * math.sin(t * 1.3 + i * 2))
        else:
            hide(f)
    # the young male, still green, on the log
    if t >= E["H"] - 0.1:
        place(YOUNG, Vector((1.0, 0.03, 0.185)), face((1.0, 0.03), cp))
        pose(YOUNG, t, 0.0, head_turn=0.25 * math.sin(t * 1.1), head_dip=-0.15)
    else:
        hide(YOUNG)

# ------------------------------------------------------------------ camera: a cut every 2 to 3 s

def shot(loc, target, push=(0, 0, 0), lens=32.0):
    def fn(t, t0):
        u = t - t0
        return Vector(loc) + Vector(push) * u, Vector(target), lens
    return fn

SHOTS = [
    (0.0, shot((0.55, -1.3, 0.42), (0.05, -0.12, 0.12), (-0.03, 0.05, -0.01), 30.0)),
    (E["deep"], shot((0.4, -0.85, 0.2), (0.12, -0.3, 0.15), (-0.01, 0.02, 0), 42.0)),
    (E["B"], shot((-0.02, -0.8, 0.12), (0.0, 0.0, 0.13), (0, 0.04, 0), 28.0)),
    (E["decor"], shot((0.08, -0.82, 0.55), (0.02, -0.32, 0.02), (0, 0.03, -0.02), 34.0)),
    (E["straws"], shot((-0.42, -0.62, 0.24), (-0.08, -0.42, 0.0), (0.02, 0.01, 0), 44.0)),
    (E["stolen"] - 0.4, shot((-0.55, -1.75, 0.5), (-0.6, 0.1, 0.1), (-0.04, 0, 0), 27.0)),
    (E["D"], shot((-0.98, -0.45, 0.18), (-1.25, 0.55, 0.13), (0, 0.03, 0), 32.0)),
    (E["wreck"] - 0.1, shot((-0.75, -0.55, 0.32), (-1.25, 0.45, 0.1), (0.03, -0.03, 0), 25.0)),
    (E["E"], shot((0.65, -0.95, 0.26), (0.05, -0.1, 0.12), (-0.02, 0.03, 0), 30.0)),
    (E["dance"], shot((0.78, -0.22, 0.17), (0.0, -0.18, 0.13), (-0.02, 0, 0), 32.0)),
    (E["imp"], shot((0.36, -0.33, 0.25), (0.0, -0.24, 0.19), (0.0, 0.0, 0), 38.0)),
    (E["strong"], shot((0.75, -0.75, 0.3), (0.05, -0.05, 0.2), (0.0, -0.03, 0.02), 26.0)),
    (E["robot"], shot((0.45, -0.72, 0.2), (0.0, -0.05, 0.13), (-0.01, 0.02, 0), 32.0)),
    (E["G"], shot((-0.95, -0.35, 0.2), (-1.3, 0.38, 0.1), (0, 0.02, 0), 32.0)),
    (E["everyone"], shot((1.55, -0.35, 0.36), (1.5, 0.65, 0.1), (0, 0.03, 0), 28.0)),
    (E["H"], shot((0.62, -0.72, 0.32), (1.0, 0.1, 0.22), (0, 0.02, 0), 32.0)),
    (E["fit"] - 0.1, shot((0.32, -0.78, 0.2), (0.13, -0.3, 0.17), (-0.01, 0.02, 0), 50.0)),
    (E["I"], shot((-0.2, -0.85, 0.26), (0.08, -0.32, 0.05), (0.01, 0.02, 0), 38.0)),
    (E["season"], shot((0.45, -1.05, 0.3), (0.05, -0.12, 0.12), (0.02, -0.06, 0.03), 30.0)),
]

def camera_at(t):
    t0, fn = SHOTS[0]
    for a, b in SHOTS:
        if t >= a:
            t0, fn = a, b
    loc, tg, lens = fn(t, t0)
    d = (tg - loc).length * 32.0 / lens
    return loc, tg, (2.8 if d < 0.8 else (4.0 if d < 1.6 else 5.6)), lens

def apply_state(t):
    apply_hero(t)
    apply_others(t)
    loc, target, fstop, lens = camera_at(t)
    B.aim(cam, loc, target)
    cam.data.lens = lens
    cam.data.dof.focus_distance = (target - loc).length
    cam.data.dof.aperture_fstop = fstop
    cam.data.clip_start = 0.01
    cam.data.clip_end = 60

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    names = ["hero", "bower", "cap", "hen", "robot", "champ", "young"]
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        top = lambda b: b["head"].matrix_world @ Vector((0, 0, 0.07))
        pts = {"hero": top(HERO), "bower": Vector((0, 0.05, 0.33)), "cap": STOLEN.matrix_world @ Vector((0, 0, 0.02)),
               "hen": top(HENB), "robot": top(ROBOT), "champ": top(CHAMP), "young": top(YOUNG)}
        for k, q in pts.items():
            v = world_to_camera_view(scene, cam, q)
            out[k].append([round(v.x * 1080, 1), round((1 - v.y) * 1920, 1)] if v.z > 0 and 0 <= v.x <= 1 and 0 <= v.y <= 1 else None)
    with open(os.path.join(OUT, "anchors.json"), "w") as fh:
        json.dump(out, fh)

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1 + scn.frame_subframe) / FPS)

anchors()
apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
