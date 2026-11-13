"""Blender scene for 'The bicep heart, a nature documentary' (render_bicep.py). Clay kit.

Two sets far apart in one file:
  the gym (origin): a night gym corner, a wall mirror at y = MIR_Y, a dumbbell rack under it, a back wall behind the
      lifters with a neon heart that stays dark until the big moment ("her own"), one warm overhead spot.
  the mudflat (x = MX): wet clay mud at golden hour, burrows and puddles, a mangrove line, a sky backdrop, a male
      fiddler crab with one giant yellow claw, a female, and a grey robot crab on a rod (Biology Letters 2018).

blender -b --factory-startup -P bicep_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Always writes out_dir/anchors.json: screen positions of label points for every frame, and shots.json.

The shot sheet is in ops/episodes/2026-11-13-bicep-heart.md.
"""
import json, math, os, random, sys
import bpy
from mathutils import Vector, Euler, Matrix
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bkit as B
import clay as C
import direct as D

argv = sys.argv[sys.argv.index("--") + 1:]
TIMING, OUT, MODE = argv[0], argv[1], argv[2]
T = json.load(open(TIMING))
FPS, DUR, E = T["fps"], T["duration"], T["events"]
NF = int(round(DUR * FPS))
os.makedirs(OUT, exist_ok=True)
B.clear_scene()
scene = B.scene
rng = random.Random(13)
AWAY = Vector((0, 0, -1.0e5))

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

def ramp(t, t0, t1):
    return smooth01((t - t0) / max(1e-3, t1 - t0))

_mc = {}
def cm(color, rough=0.6, prints=0.3):
    key = (color, rough, prints)
    if key not in _mc:
        _mc[key] = C.clay(f"m{len(_mc)}", color, rough, prints=prints)
    return _mc[key]

def slab(name, x0, x1, y0, y1, z0, z1, m, r=0.06, wobble=0.01):
    return C.soft(name, (x1 - x0, y1 - y0, z1 - z0), m, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), r=r, wobble=wobble)

# ================================================================== the gym

MIR_Y = 4.6
BACK_Y = -3.0
WALL = C.clay("gwall", (0.05, 0.08, 0.18), 0.8, prints=0.0, dents=0.3)
FLOOR = [C.clay(f"tile{k}", c, 0.85, prints=0.0, dents=0.4) for k, c in enumerate([(0.05, 0.05, 0.06), (0.07, 0.07, 0.08)])]
CREAM = cm((0.90, 0.86, 0.76), 0.5, 0.0)
for i in range(-4, 4):                                        # rubber tiles, 1 m, alternating shade
    for j in range(-3, 5):
        slab(f"tile{i}_{j}", i + 0.01, i + 0.99, j + 0.01, j + 0.99, -0.12, rng.uniform(-0.004, 0.004), FLOOR[(i + j) % 2], 0.03, 0.002)
slab("under", -4.5, 4.5, -3.5, 5.2, -0.5, -0.1, cm((0.02, 0.02, 0.03), 0.9, 0.0), 0.05, 0)
slab("wallL", -4.6, -4.0, -3.4, 5.4, -0.1, 4.4, WALL)
slab("wallR", 4.0, 4.6, -3.4, 5.4, -0.1, 4.4, WALL)
slab("wallM", -4.6, 4.6, MIR_Y + 0.08, MIR_Y + 0.6, -0.1, 4.4, WALL)
slab("wallB", -4.6, 4.6, BACK_Y - 0.6, BACK_Y, -0.1, 4.4, WALL)
slab("ceil", -4.7, 4.7, -3.6, 5.4, 4.0, 4.4, cm((0.03, 0.04, 0.09), 0.9, 0.0), 0.05, 0)

mir = bpy.data.materials.new("mirror")                       # a real mirror: Eevee ray-traced reflections
mir.use_nodes = True
mp = mir.node_tree.nodes["Principled BSDF"]
mp.inputs["Base Color"].default_value = (0.92, 0.94, 0.96, 1)
mp.inputs["Metallic"].default_value = 1.0
mp.inputs["Roughness"].default_value = 0.015
C.soft("mirror", (6.4, 0.04, 2.9), mir, (0, MIR_Y + 0.02, 1.85), r=0.005, wobble=0)
for name, bb in (("mt", (-3.3, 3.3, MIR_Y - 0.06, MIR_Y + 0.1, 3.28, 3.42)), ("mb", (-3.3, 3.3, MIR_Y - 0.06, MIR_Y + 0.1, 0.28, 0.42)),
                 ("ml", (-3.3, -3.16, MIR_Y - 0.06, MIR_Y + 0.1, 0.3, 3.4)), ("mr", (3.16, 3.3, MIR_Y - 0.06, MIR_Y + 0.1, 0.3, 3.4))):
    slab(name, *bb, CREAM, 0.03, 0.003)

# dumbbell rack along the mirror (foreground depth in the hook shot), chrome-ish handles, dark heads
RACK = cm((0.12, 0.12, 0.14), 0.5)
HEAD = cm((0.08, 0.08, 0.09), 0.55)
CHROME = C.glossy("chrome", (0.72, 0.74, 0.78), 0.2)
slab("rackA", -3.0, 3.0, MIR_Y - 0.75, MIR_Y - 0.15, 0.35, 0.45, RACK, 0.03)
for x in (-2.9, 0.0, 2.9):
    slab(f"rleg{x}", x - 0.06, x + 0.06, MIR_Y - 0.7, MIR_Y - 0.2, 0.0, 0.36, RACK, 0.03)
for k in range(9):
    x = -2.6 + 0.65 * k
    s = 0.09 + 0.012 * k
    for dx in (-0.16, 0.16):
        C.ball(f"db{k}{dx}", s, HEAD, (x + dx, MIR_Y - 0.45, 0.45 + s), squash=(0.7, 1, 1), wobble=0.004)
    C.soft(f"dh{k}", (0.3, 0.05, 0.05), CHROME, (x, MIR_Y - 0.45, 0.45 + s), r=0.02, wobble=0)
boxes = C.boxes
boxes("bench", [((-0.9, 0.9, -0.22, 0.22, 0.42, 0.56), cm((0.10, 0.10, 0.12), 0.45)),
                ((-0.7, -0.58, -0.08, 0.08, 0.0, 0.44), RACK), ((0.58, 0.7, -0.08, 0.08, 0.0, 0.44), RACK)],
      (2.6, -1.4, 0.0), r=0.04)

# the neon heart on the back wall: dark tube until "her own", then the accent pink
NEON_C = (0, BACK_Y + 0.08, 2.95)
neon = C.clay("neon", (0.09, 0.03, 0.06), 0.35, prints=0.0)
nb = neon.node_tree.nodes["Principled BSDF"]
nb.inputs["Emission Color"].default_value = (1.0, 0.18, 0.52, 1)
nb.inputs["Emission Strength"].default_value = 0.0
for k in range(56):
    a = 2 * math.pi * k / 56
    hx = 16 * math.sin(a) ** 3
    hz = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
    C.ball(f"neon{k}", 0.045, neon, (NEON_C[0] + 0.034 * hx, NEON_C[1], NEON_C[2] + 0.034 * hz), wobble=0)
neon_ld = bpy.data.lights.new("neon_l", "POINT"); neon_ld.color = (1.0, 0.25, 0.55); neon_ld.shadow_soft_size = 0.5
neon_l = B.link(bpy.data.objects.new("neon_l", neon_ld)); neon_l.location = (NEON_C[0], NEON_C[1] + 0.5, NEON_C[2])

# ------------------------------------------------------------------ figures with an elbow

def add_elbow(f, name, side, k=1.0):
    """The clay figure's arm is one piece; split it at the elbow so forearm and hand can bend. k stretches the arm."""
    arm = f["arm" + side]
    up = bpy.data.objects[f"{name}.upper{side}"]
    fo = bpy.data.objects[f"{name}.fore{side}"]
    ha = bpy.data.objects[f"{name}.hand{side}"]
    up.location = (0, 0, -0.2 * k); up.scale = (1, 1, k)
    el = C.empty(f"{name}.elbow{side}", (0, 0, -0.38 * k), arm)
    fo.parent = el; fo.location = (0, 0, -0.12 * k); fo.scale = (1, 1, k)
    ha.parent = el; ha.location = (0, -0.01, -0.36 * k)
    f["elbow" + side] = el
    f["k" + side] = k
    return el

KR = 1.3

def make_person(name, scale, k_left, **kw):
    f = C.figure(name, **kw)
    add_elbow(f, name, "L", k_left)
    add_elbow(f, name, "R", KR)
    f["root"].scale = (scale,) * 3
    f["shL0"] = f["armL"].location.copy()
    return f

BRO = make_person("bro", 1.15, 1.45, skin=(0.80, 0.56, 0.40), shirt=(0.30, 0.34, 0.30), pants=(0.05, 0.05, 0.06),
                  shoes=(0.92, 0.92, 0.90), hair=(0.12, 0.07, 0.03), tank=True, arms=1.15)
HER = make_person("her", 1.02, 1.45, skin=(0.86, 0.64, 0.50), shirt=(0.88, 0.86, 0.80), pants=(0.10, 0.11, 0.14),
                  shoes=(0.95, 0.95, 0.93), hair=(0.20, 0.11, 0.05), tank=True, arms=0.95)
C.ball("her.pony", 0.13, cm((0.20, 0.11, 0.05), 0.7), (0, 0.3, 0.6), HER["head"], squash=(0.8, 1.0, 1.5))
C.ball("her.pony2", 0.09, cm((0.20, 0.11, 0.05), 0.7), (0, 0.36, 0.38), HER["head"], squash=(0.8, 1.0, 1.6))

SH_L, SH_R = Vector((-0.32, -0.12, 1.5)), Vector((0.5, 0, 1.5))     # SH_L: the left shoulder rolled in for the curl

def arm_hand(sh, eul, elb, k):
    Ra = Euler(eul, "XYZ").to_matrix()
    Re = Euler(elb, "XYZ").to_matrix()
    return sh + Ra @ (Vector((0, 0, -0.38 * k)) + Re @ Vector((0, -0.01, -0.36 * k)))

# the flexing (right) arm: upper arm forward and across at shoulder height, forearm straight up
FLEX_R = (0.0, -math.pi / 2, -0.15)
FLEX_RE = (0.0, -math.pi / 2, 0.0)
def flex_points():
    Ra = Euler(FLEX_R, "XYZ").to_matrix()
    elbow = SH_R + Ra @ Vector((0, 0, -0.38 * KR))
    bicep = SH_R + Ra @ Vector((0, 0, -0.2 * KR)) + Vector((0, 0, 0.15))
    fist = arm_hand(SH_R, FLEX_R, FLEX_RE, KR)
    return elbow, bicep, fist

def solve_left(target, k):
    """Coarse IK: the left arm's euler and elbow bend that bring the hand nearest `target` (root-local)."""
    best, bd = None, 1e9
    r = random.Random(7)
    for _ in range(4000):
        cand = ((r.uniform(-2.8, 0.3), r.uniform(-0.6, 1.2), r.uniform(-1.6, 1.6)), (r.uniform(-2.6, 0.0), 0.0, 0.0))
        d = (arm_hand(SH_L, cand[0], cand[1], k) - target).length
        if d < bd:
            best, bd = cand, d
    step = 0.2
    for _ in range(300):
        improved = False
        for i in range(4):
            for s in (-step, step):
                a = list(best[0]); e = list(best[1])
                if i < 3:
                    a[i] += s
                else:
                    e[0] = min(0.0, max(-2.7, e[0] + s))
                d = (arm_hand(SH_L, a, e, k) - target).length
                if d < bd:
                    best, bd, improved = (tuple(a), tuple(e)), d, True
        if not improved:
            step *= 0.6
            if step < 0.002:
                break
    print(f"IK: hand misses its target by {bd:.3f} m")
    return best

_, BICEP, FIST = flex_points()
LEFT_TGT = BICEP + Vector((0.0, -0.06, 0.08))
POSE_L = solve_left(LEFT_TGT, 1.45)
REST = {"L": ((0, 0, 0.08), (0, 0, 0)), "R": ((0, 0, -0.08), (0, 0, 0))}

def lerp3(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))

def pose(f, flex, curl, pump=0.0):
    """flex 0..1 raises the right arm into the flex; curl 0..1 brings the left hand over the bicep."""
    ra = lerp3(REST["R"][0], FLEX_R, flex)
    re = lerp3(REST["R"][1], FLEX_RE, flex)
    ra = (ra[0], ra[1] + 0.18 * pump, ra[2])
    f["armR"].rotation_euler = ra
    f["elbowR"].rotation_euler = (re[0], re[1] + 0.35 * pump, re[2])
    f["armL"].location = f["shL0"].lerp(Vector((f["shL0"].x + 0.18, -0.12, 1.5)), curl)
    f["armL"].rotation_euler = lerp3(REST["L"][0], POSE_L[0], curl)
    f["elbowL"].rotation_euler = lerp3(REST["L"][1], POSE_L[1], curl)

def heart_local():
    """The middle of the heart the two arms make, root-local."""
    hand = arm_hand(SH_L, POSE_L[0], POSE_L[1], 1.45)
    return (hand + BICEP + FIST) / 3 + Vector((0, -0.12, -0.02))

BRO_POS = Vector((0.15, 1.3, 0.0))
HER_STOP = Vector((-1.3, 1.75, 0.0))

# ================================================================== the mudflat

MX = 80.0
MUD = C.clay("mud", (0.30, 0.22, 0.16), 0.32, prints=0.0, mottle=0.12, dents=0.8)
MUD2 = C.clay("mud2", (0.24, 0.17, 0.12), 0.4, prints=0.0, dents=0.6)
slab("flat", MX - 14, MX + 14, -6, 18, -0.4, 0.0, MUD, 0.1, 0.03)
HOLE = cm((0.02, 0.015, 0.01), 0.9, 0.0)
for k in range(26):
    x, y = MX + rng.uniform(-6, 6), rng.uniform(-1, 9)
    if abs(x - MX) < 1.6 and y < 2.5:
        continue
    r_ = rng.uniform(0.07, 0.12)
    C.ball(f"hole{k}", r_, HOLE, (x, y, 0.0), squash=(1, 1, 0.12), wobble=0)
    C.ball(f"rim{k}", r_ * 1.6, MUD2, (x, y, -0.01), squash=(1, 1, 0.2), wobble=0.004)
WET = C.glossy("puddle", (0.10, 0.12, 0.16), 0.04)
for k, (x, y, s) in enumerate(((MX - 2.8, 3.5, 1.1), (MX + 3.1, 5.5, 1.5), (MX - 0.6, 7.5, 1.8), (MX + 1.9, 1.8, 0.6))):
    C.ball(f"pud{k}", s, WET, (x, y, 0.004), squash=(1.4, 0.7, 0.01), wobble=0)
MANG = [cm((0.04, 0.08, 0.05), 0.8, 0.0), cm((0.05, 0.10, 0.06), 0.8, 0.0)]
for k in range(30):
    x = MX - 16 + 1.1 * k + rng.uniform(-0.3, 0.3)
    C.ball(f"mang{k}", rng.uniform(0.7, 1.4), MANG[k % 2], (x, 14 + rng.uniform(-0.6, 0.6), rng.uniform(0.5, 1.0)),
           squash=(1.3, 0.8, 0.9), wobble=0.05)

sky = bpy.data.materials.new("sky")                          # dusk gradient: gold at the horizon, blue above
sky.use_nodes = True
nt = sky.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
ramp_n = nt.nodes.new("ShaderNodeValToRGB"); em = nt.nodes.new("ShaderNodeEmission"); out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp_n.inputs["Fac"])
els = ramp_n.color_ramp.elements
els[0].position, els[0].color = 0.0, (1.0, 0.55, 0.22, 1)
els[1].position, els[1].color = 0.45, (0.10, 0.16, 0.38, 1)
nt.links.new(ramp_n.outputs["Color"], em.inputs["Color"]); em.inputs["Strength"].default_value = 1.6
nt.links.new(em.outputs[0], out.inputs["Surface"])
C.soft("skyback", (60, 0.2, 24), sky, (MX, 20, 10), r=0.01, wobble=0)

# ------------------------------------------------------------------ crabs (faces -Y, origin on the mud)

SHELL = C.clay("shell", (0.16, 0.20, 0.27), 0.45, prints=0.4, mottle=0.18)
SHELL_F = C.clay("shellf", (0.38, 0.30, 0.22), 0.5, prints=0.4, mottle=0.18)
YEL = C.clay("claw", (0.98, 0.78, 0.22), 0.4, prints=0.4)
LEG = cm((0.30, 0.24, 0.20), 0.55)
METAL = C.glossy("metal", (0.55, 0.57, 0.62), 0.25)
EYEB = C.glossy("eyeb", (0.02, 0.02, 0.02), 0.08)

def crab(name, shell, big_claw_mat=None, legs=True, scale=1.0):
    root = C.empty(name)
    body = C.empty(f"{name}.body", (0, 0, 0.0), root)
    C.soft(f"{name}.shell", (0.56, 0.38, 0.18), shell, (0, 0, 0.27), body, r=0.08)
    for sx in (-1, 1):
        stalk = C.soft(f"{name}.stalk{sx}", (0.035, 0.035, 0.2), LEG, (0.08 * sx, -0.15, 0.42), body, r=0.015)
        C.ball(f"{name}.eye{sx}", 0.04, EYEB, (0.08 * sx, -0.15, 0.53), body, wobble=0)
    lg = []
    if legs:
        for sx in (-1, 1):
            for k in range(4):
                pv = C.empty(f"{name}.legp{sx}{k}", (0.24 * sx, -0.08 + 0.09 * k, 0.24), body)
                C.soft(f"{name}.leg{sx}{k}", (0.32, 0.05, 0.05), LEG, (0.16 * sx, 0, 0), pv, r=0.022)
                C.soft(f"{name}.foot{sx}{k}", (0.05, 0.05, 0.22), LEG, (0.3 * sx, 0, -0.1), pv, r=0.022)
                lg.append((pv, sx, k))
    small = C.empty(f"{name}.smallp", (-0.2, -0.2, 0.25), body)
    C.ball(f"{name}.small", 0.07, shell, (0, -0.06, 0), small, squash=(0.8, 1.2, 0.8))
    big = None
    if big_claw_mat:
        big = C.empty(f"{name}.bigp", (0.26, -0.16, 0.26), body)       # the waving claw's shoulder
        C.soft(f"{name}.bigarm", (0.12, 0.12, 0.3), big_claw_mat, (0.06, -0.05, 0.12), big, r=0.05, rot=(0, -0.4, 0))
        C.soft(f"{name}.bigpal", (0.32, 0.18, 0.46), big_claw_mat, (0.16, -0.08, 0.42), big, r=0.07, rot=(0, -0.15, 0))
        C.soft(f"{name}.bigfing", (0.1, 0.1, 0.36), big_claw_mat, (0.02, -0.08, 0.8), big, r=0.045, rot=(0, 0.3, 0))
        C.soft(f"{name}.bigthumb", (0.09, 0.09, 0.3), big_claw_mat, (0.25, -0.08, 0.76), big, r=0.04, rot=(0, -0.3, 0))
    else:
        s2 = C.empty(f"{name}.smallp2", (0.2, -0.2, 0.25), body)
        C.ball(f"{name}.small2", 0.07, shell, (0, -0.06, 0), s2, squash=(0.8, 1.2, 0.8))
    if big is not None:
        big.scale = (0.85,) * 3
    root.scale = (scale,) * 3
    return {"root": root, "body": body, "big": big, "legs": lg}

MALE = crab("male", SHELL, YEL)
FEM = crab("fem", SHELL_F, None, scale=0.82)
ROBO = crab("robo", METAL, METAL, legs=False)
boxes("robobox", [((-0.22, 0.22, -0.18, 0.18, -0.1, 0.12), cm((0.15, 0.15, 0.17), 0.4)),
                  ((-0.025, 0.025, -0.025, 0.025, 0.1, 0.22), METAL)], (0, 0.05, 0), ROBO["root"], r=0.03)
for sx in (-1, 1):
    C.soft(f"robo.cable{sx}", (0.03, 0.9, 0.03), cm((0.05, 0.05, 0.05), 0.6), (0.12 * sx, 0.6, 0.03), ROBO["root"], r=0.014)

MALE_POS = Vector((MX, 0.0, 0.0))
ROBO_POS = Vector((MX + 1.3, 0.6, 0.0))
FEM_PATH = (Vector((MX - 3.0, 0.8, 0)), Vector((MX + 3.0, 0.7, 0)))

def wave_angle(t, t0, freq0, accel=0.0, amp=1.0):
    """The claw's raise: 0 down, 1 up. Frequency grows by `accel` per second (the 2018 robots sped up)."""
    if t < t0:
        return 0.0
    u = t - t0
    ph = 2 * math.pi * (freq0 * u + 0.5 * accel * u * u)
    return amp * 0.5 * (1 - math.cos(ph))

def set_claw(c, up):
    if c["big"] is not None:
        c["big"].rotation_euler = (0.0, 1.3 - 1.1 * up, 0.0)

def walk_legs(c, t, speed):
    for pv, sx, k in c["legs"]:
        pv.rotation_euler = (0.0, 0.25 * sx + 0.18 * math.sin(t * 14 * speed + k * 1.6) * speed, 0.0)

# ================================================================== lights, world, camera

world = bpy.data.worlds.new("bg")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.004, 0.007, 0.02, 1)
spot_ld = bpy.data.lights.new("spot", "SPOT")                 # the gym's motivated key: one warm overhead spot
spot_ld.energy = 1500.0; spot_ld.color = (1.0, 0.70, 0.42)
spot_ld.spot_size = math.radians(58); spot_ld.spot_blend = 0.6; spot_ld.shadow_soft_size = 0.4
spot = B.link(bpy.data.objects.new("spot", spot_ld))
D.point_at(spot, Vector((-0.4, 1.4, 3.9)), Vector((-0.4, 1.9, 0.6)))
grim = B.area("grim", Vector((1.5, MIR_Y - 0.4, 3.0)), Vector((0, 1.3, 1.8)), 1.5, 90.0, (0.45, 0.6, 1.0))
gfill = B.area("gfill", Vector((-3.0, -1.5, 2.2)), Vector((0, 1.5, 1.5)), 3.0, 40.0, (0.25, 0.40, 1.0))
sun_l = B.area("sunl", Vector((MX + 7.0, -1.5, 2.2)), Vector((MX, 0.3, 0.3)), 3.0, 2600.0, (1.0, 0.68, 0.35))
mfill = B.area("mfill", Vector((MX - 5, -3, 3)), Vector((MX, 0.5, 0.3)), 5.0, 260.0, (0.35, 0.5, 1.0))

cam = B.camera(lens=35, fstop=2.0)
B.render_settings(FPS, samples=32, motion_blur=0.3, look="AgX - Punchy")
C.cpu_preview_quality(samples=48)
if os.environ.get("BICEP_CYCLES") == "1":
    # the mirror shots: Eevee only reflects what is already on screen, and his front is not, so they ray trace
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            for d in prefs.devices:
                d.use = d.type == kind
            break
        except Exception as ex:
            print("cycles device skipped:", kind, ex)
    scene.cycles.device = "GPU"
    scene.cycles.samples = 64
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.cycles.glossy_bounces = 3
rig = D.Rig(cam, {"spot": spot, "grim": grim, "gfill": gfill, "sun": sun_l, "mfill": mfill})

# ------------------------------------------------------------------ shots

def wpt(f, local):
    return f["root"].location + Matrix.Rotation(f["root"].rotation_euler.z, 3, "Z") @ (local * f["root"].scale.x)

BRO_ROT = math.pi                                              # faces the mirror (+Y)
def bro_world(local):
    return BRO_POS + Matrix.Rotation(BRO_ROT, 3, "Z") @ (local * 1.15)

def mirror(p):
    return Vector((p.x, 2 * MIR_Y - p.y, p.z))

HEART_W = bro_world(heart_local())
REFL = mirror(HEART_W)
CHEST = bro_world(Vector((0, 0, 1.45)))
G_ON = dict(spot=1.0, grim=1.0, gfill=1.0, sun=0.0, mfill=0.0)
M_ON = dict(spot=0.0, grim=0.0, gfill=0.0, sun=1.0, mfill=1.0)
HER_CHEST = HER_STOP + Vector((0, 0, 1.6))

SH = [
    D.Shot("hook", 0.0, CHEST + Vector((-0.25, 0, 0.3)), lens=30, dist=2.9, yaw=196, pitch=-4, screen=(0.5, 0.5),
           light=G_ON, fstop=2.8, note="frame 0 mid-heart, three-quarter front from the mirror side; the spot on him, neon dark behind"),
    D.Shot("heart", E["B"], HEART_W + Vector((0, 0, -0.1)), lens=36, dist=2.5, yaw=172, pitch=-4, screen=(0.5, 0.48), light=G_ON, fstop=2.0,
           note="from the mirror side: the arms make the heart"),
    D.Shot("mudwide", E["C"], MALE_POS + Vector((0, 0, 0.35)), lens=24, dist=3.4, yaw=8, pitch=-7, screen=(0.5, 0.58),
           light=M_ON, fstop=4.0, note="the crab small on the flat, gold sun from the right"),
    D.Shot("claw", E["D"], MALE_POS + Vector((0.32, -0.25, 0.75)), lens=50, dist=3.0, yaw=-18, pitch=4, screen=(0.5, 0.5),
           move=("push", 0.12), light=M_ON, fstop=2.2, note="crab eye level, the claw against the sky"),
    D.Shot("wave", E["E"], MALE_POS + Vector((0, 0, 0.45)), lens=35, dist=3.2, yaw=6, pitch=-5, screen=(0.5, 0.55),
           light=M_ON, fstop=2.8, note="the female walks past; each wave on twos"),
    D.Shot("robot", E["F"], MX * Vector((1, 0, 0)) + Vector((0.65, 0.3, 0.45)), lens=32, dist=3.6, yaw=0, pitch=-6,
           screen=(0.5, 0.55), light=M_ON, fstop=2.8, note="robot right, real crab left, the female turns to the robot"),
    D.Shot("faster", E["G"], CHEST + Vector((0, 0, 0.25)), lens=32, dist=2.9, yaw=180, pitch=-3, screen=(0.5, 0.5),
           light=dict(G_ON, spot=1.3), fstop=2.4, note="frontal, symmetrical, locked off: the heart pumps faster"),
    D.Shot("herown", E["H"], HER_CHEST + Vector((-0.45, 0, 0.2)), lens=22, dist=2.5, yaw=180, pitch=-3,
           screen=(0.5, 0.5), move=("push_on_hit", 0.15), hit=E["own"], light=G_ON, fstop=2.4,
           note="she walks past him, 0.3 s still, then the push and the pink neon on 'own'"),
    D.Shot("loop", E["I"], CHEST + Vector((-0.25, 0, 0.3)), lens=30, dist=2.9, yaw=196, pitch=-4, screen=(0.5, 0.5),
           light=G_ON, fstop=2.8, note="back to the hook framing so the reel loops"),
]
SHOTS = D.ShotList(SH, DUR)
SHOTS.check()
SHOTS.dump(os.path.join(os.path.dirname(OUT.rstrip("/\\")), "shots.json"), big=E["own"])

# ------------------------------------------------------------------ the timeline

def apply_state(t):
    # bro: heart from frame 0; at B he drops it and rebuilds it on the words; pumps from "speeds"
    redo = E["B"] <= t < E["C"]
    if redo:
        flex = ramp(t, E["flexes"] - 0.25, E["flexes"] + 0.15) if t > E["B"] + 0.25 else 1 - ramp(t, E["B"], E["B"] + 0.25)
        curl = ramp(t, E["curls"] - 0.2, E["curls"] + 0.3) if t > E["B"] + 0.25 else 1 - ramp(t, E["B"], E["B"] + 0.25)
    else:
        flex = curl = 1.0
    pump = 0.0
    if E["speeds"] - 0.1 <= t < E["H"] + 0.6:
        u = t - (E["speeds"] - 0.1)
        pump = 0.5 * (1 - math.cos(2 * math.pi * (1.4 * u + 0.9 * u * u)))
    tq = D.on_twos(t, FPS)
    BRO["root"].location = BRO_POS
    BRO["root"].rotation_euler = (0, 0, BRO_ROT)
    pose(BRO, flex, curl, pump * (1 if t < E["H"] + 0.3 else 0))
    BRO["body"].scale = (1.0 + 0.015 * math.sin(t * 1.7), 1, 1)
    look = ramp(t, E["past"] - 0.4, E["past"] + 0.2) * (1 - ramp(t, E["I"] - 0.1, E["I"]))
    BRO["head"].rotation_euler = (0, 0, 0.55 * look)
    for k, b in enumerate(BRO["brows"]):
        b.rotation_euler = (0, 0.25 * (-1, 1)[k] * (1 - look) - 0.3 * (-1, 1)[k] * look, 0)
    BRO["mouth"].scale = (1.0 + 0.3 * (1 - look), 1, 1 + 1.6 * ramp(t, E["own"], E["own"] + 0.2) * (1 - ramp(t, E["I"] - 0.1, E["I"])))

    # her: in from the right at H, past him (between him and the camera), stops, does her own heart on "own"
    if E["H"] - 0.1 <= t < E["I"]:
        wu = ramp(t, E["H"], E["does"] - 0.15)
        start = Vector((0.9, 0.45, 0.0))
        mid = Vector((-0.5, 0.55, 0.0))
        p = start.lerp(mid, min(1, 2 * wu)) if wu < 0.5 else mid.lerp(HER_STOP, 2 * wu - 1)
        HER["root"].location = p
        walking = 1 - ramp(t, E["does"] - 0.25, E["does"] - 0.05)
        HER["root"].rotation_euler = (0, 0, -math.pi * (1 - walking) - (math.pi / 2) * walking)
        sw = math.sin(tq * 9.0) * walking
        HER["legL"].rotation_euler = (0.45 * sw, 0, 0); HER["legR"].rotation_euler = (-0.45 * sw, 0, 0)
        hf = D.ars(t, E["own"] - 0.05, wind=0.2, back=0.05, release=0.12, settle=0.4, over=0.06, snap="out")
        pose(HER, hf, hf)
        if hf < 0.05:
            HER["armL"].rotation_euler = (0.35 * sw, 0, 0.08); HER["armR"].rotation_euler = (-0.35 * sw, 0, -0.08)
        HER["root"].location.z = 0.03 * abs(math.sin(tq * 9.0)) * walking
    else:
        HER["root"].location = AWAY

    # the neon: dark until "own", then the accent pink with a short flicker
    on = 0.0 if t < E["own"] else (0.35 if 0.06 < t - E["own"] < 0.12 else 1.0)
    if t >= E["I"]:
        on = 0.0
    nb.inputs["Emission Strength"].default_value = 18.0 * on
    neon_ld.energy = 260.0 * on

    # the crabs
    MALE["root"].location = MALE_POS
    MALE["root"].rotation_euler = (0, 0, 0.15)
    if t < E["E"]:
        up = ramp(t, E["mudflat"] - 0.1, E["mudflat"] + 0.6) * (1 if t < E["D"] else 1.0)
        if E["D"] <= t:
            up = 0.85 + 0.05 * math.sin(t * 2)
    elif t < E["F"]:
        up = wave_angle(D.on_twos(t, FPS), E["E"], 1.1)
    else:
        up = wave_angle(D.on_twos(t, FPS), E["F"], 0.9)
    set_claw(MALE, up)
    walk_legs(MALE, t, 0.15)
    if E["E"] - 0.2 <= t < E["G"]:
        if t < E["F"]:
            u = ramp(t, E["E"], E["F"] + 0.2)
            FEM["root"].location = FEM_PATH[0].lerp(FEM_PATH[1], u)
            FEM["root"].rotation_euler = (0, 0, 0.1)
            walk_legs(FEM, D.on_twos(t, FPS), 1.0)
        else:
            turn = ramp(t, E["up"] - 0.3, E["up"] + 0.1)
            go = ramp(t, E["up"], E["G"])
            a = Vector((MX + 0.6, -0.3, 0))
            b = ROBO_POS + Vector((-0.45, -0.35, 0))
            FEM["root"].location = a.lerp(b, go)
            FEM["root"].rotation_euler = (0, 0, -0.4 * (1 - turn) + 0.9 * turn)
            walk_legs(FEM, D.on_twos(t, FPS), 0.3 + 0.7 * go)
    else:
        FEM["root"].location = AWAY
    if E["F"] - 0.1 <= t < E["G"]:
        ROBO["root"].location = ROBO_POS
        ROBO["root"].rotation_euler = (0, 0, -0.25)
        set_claw(ROBO, wave_angle(D.on_twos(t, FPS), E["F"] + 0.2, 0.7, accel=0.55))
    else:
        ROBO["root"].location = AWAY
    if E["F"] <= t < E["G"]:
        MALE["root"].location = MALE_POS + Vector((-0.4, 0.2, 0))

    SHOTS.apply(rig, t)

# ------------------------------------------------------------------ anchors for 2D labels

def proj(p):
    v = world_to_camera_view(scene, cam, p)
    return [round(v.x * 1080, 1), round((1 - v.y) * 1920, 1)] if v.z > 0 and 0 <= v.x <= 1 and 0 <= v.y <= 1 else None

def anchors():
    names = ("heart", "sheart", "crab", "fem", "robot")
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        behind = cam.location.y < BRO_POS.y and abs(cam.location.x) < 20
        hp = bro_world(heart_local())
        sp = HER["root"].location + Matrix.Rotation(HER["root"].rotation_euler.z, 3, "Z") @ (heart_local() * 1.02)
        pts = {"heart": mirror(hp) if behind else hp, "sheart": sp,
               "crab": MALE["root"].matrix_world @ Vector((0, 0, 0.4)),
               "fem": FEM["root"].matrix_world @ Vector((0, 0, 0.4)),
               "robot": ROBO["root"].matrix_world @ Vector((0, 0, 0.5))}
        for k, p in pts.items():
            out[k].append(proj(p))
    with open(os.path.join(OUT, "anchors.json"), "w") as fh:
        json.dump(out, fh)

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1 + scn.frame_subframe) / FPS)

anchors()
apply_state(0.0)
bpy.context.view_layer.update()
print("DEBUG cam", tuple(round(v, 2) for v in cam.location), "bro", tuple(BRO["root"].location), "refl", tuple(round(v, 2) for v in REFL))
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
