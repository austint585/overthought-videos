"""Clay-look test of 'Gym bro reads the label': the same apartment, gym bro, props, camera moves and timing as
gym_scene.py, rebuilt with the clay kit (clay.py) instead of voxels, so Austin can compare the two looks on one set.
Plank floor, plaster walls pressed together from slabs, a night window with a moon and a lit skyline, warm lamp light
against blue night, shallow depth of field.

blender -b --factory-startup -P gymclay_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Always writes out_dir/anchors.json: screen positions of label points for every frame.
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
rng = random.Random(4)
AWAY = Vector((0, 0, -1.0e5))

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

def ramp(t, t0, t1):
    return smooth01((t - t0) / (t1 - t0))

# ------------------------------------------------------------------ materials

WOOD = [C.clay(f"wood{k}", c, 0.62, prints=0.0) for k, c in enumerate([(0.40, 0.24, 0.12), (0.46, 0.28, 0.14), (0.35, 0.20, 0.10)])]
WALL = C.clay("wall", (0.08, 0.15, 0.32), 0.75, prints=0.0, dents=0.35)
TRIM = C.clay("trim", (0.93, 0.90, 0.82), 0.55, prints=0.0)
BASEB = C.clay("baseboard", (0.30, 0.18, 0.09), 0.6)
CEIL = C.clay("ceiling", (0.10, 0.13, 0.24), 0.8, prints=0.0, dents=0.3)
UNDER = C.clay("under", (0.05, 0.03, 0.02), 0.9)

_mat_cache = {}
def colmat(color, rough=0.55, emit=0.0):
    key = (color, rough, emit)
    if key not in _mat_cache:
        n = f"c{len(_mat_cache)}"
        _mat_cache[key] = C.glow(n, color, emit) if emit else C.clay(n, color, rough, prints=0.3)
    return _mat_cache[key]

boxes = C.boxes

def slab(name, x0, x1, y0, y1, z0, z1, m=WALL, r=0.09, wobble=0.02):
    return C.soft(name, (x1 - x0, y1 - y0, z1 - z0), m, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), r=r, wobble=wobble)

# ------------------------------------------------------------------ the room: inner floor x -6..6, back wall at y 8, ceiling at z 4

WALL_Y = 8.0
for row in range(25):                                        # planks along x, staggered seams, tops near z 0
    y0 = -2.5 + 0.5 * row
    x = -6.3 + rng.uniform(0, 1.2)
    slab(f"plank{row}s", -6.3, x, y0 + 0.015, y0 + 0.485, -0.16, 0.0, rng.choice(WOOD), 0.05, 0.006)
    while x < 6.3:
        x1 = min(6.3, x + rng.uniform(1.8, 3.6))
        dz = rng.uniform(-0.008, 0.008)
        slab(f"plank{row}_{x:.1f}", x + 0.015, x1 - 0.015, y0 + 0.015, y0 + 0.485, -0.16 + dz, dz, rng.choice(WOOD), 0.05, 0.006)
        x = x1
slab("underfloor", -6.8, 6.8, -2.6, 10.0, -0.5, -0.12, UNDER, 0.05, 0)

slab("wallL", -6.7, -6.0, -2.5, 8.7, -0.1, 4.3)
slab("wallR", 6.0, 6.7, -2.5, 8.7, -0.1, 4.3)
slab("backA", -6.7, 0.0, 8.0, 8.7, -0.1, 4.3)                 # back wall pressed together around the door and window
slab("backB", 2.0, 3.0, 8.0, 8.7, -0.1, 4.3)
slab("backC", 5.0, 6.7, 8.0, 8.7, -0.1, 4.3)
slab("backD", -0.05, 2.05, 8.0, 8.7, 3.0, 4.3)
slab("backE", 2.95, 5.05, 8.0, 8.7, -0.1, 1.0)
slab("backF", 2.95, 5.05, 8.0, 8.7, 3.0, 4.3)
slab("ceiling", -6.8, 6.8, -2.6, 8.8, 4.0, 4.5, CEIL)
for name, bb in (("bbA", (-6.0, 0.0, 7.84, 8.04)), ("bbB", (2.0, 3.0, 7.84, 8.04)), ("bbC", (5.0, 6.0, 7.84, 8.04)),
                 ("bbL", (-6.04, -5.84, -2.5, 7.9)), ("bbR", (5.84, 6.04, -2.5, 7.9))):
    slab(name, *bb, 0.0, 0.24, BASEB, 0.06, 0.004)

# lit hallway through the doorway
slab("hallL", -0.7, 0.0, 8.6, 10.2, -0.1, 4.0)
slab("hallR", 2.0, 2.7, 8.6, 10.2, -0.1, 4.0)
C.soft("hall", (2.4, 0.2, 3.6), colmat((1.0, 0.92, 0.78), emit=3.0), (1.0, 10.0, 1.7), r=0.02, wobble=0)

# night window: a deep blue sky, a moon, a clay skyline with lit windows
C.soft("sky", (2.2, 0.08, 2.2), C.glow("sky", (0.04, 0.07, 0.20), 1.2), (4.0, 8.62, 2.0), r=0.01, wobble=0)
C.ball("moon", 0.17, C.glow("moon", (1.0, 0.93, 0.72), 5.0), (4.55, 8.52, 2.55), squash=(1, 0.3, 1), wobble=0)
CITY, LIT = C.clay("city", (0.05, 0.06, 0.12), 0.8), C.glow("lit", (1.0, 0.72, 0.35), 4.0)
for k, (cx, w, h) in enumerate(((3.25, 0.45, 0.75), (3.75, 0.5, 0.5), (4.25, 0.4, 0.95), (4.7, 0.5, 0.6))):
    C.soft(f"bldg{k}", (w, 0.1, h), CITY, (cx, 8.5, 1.0 + h / 2), r=0.04, wobble=0.004)
    for wy in range(int(h / 0.18)):
        for wx in (-1, 1):
            if rng.random() < 0.55:
                C.soft(f"win{k}_{wy}_{wx}", (0.07, 0.03, 0.07), LIT, (cx + wx * w * 0.22, 8.44, 1.12 + wy * 0.18), r=0.02, wobble=0)
for name, bb in (("wtop", (2.9, 5.1, 7.9, 8.12, 2.9, 3.08)), ("wsill", (2.82, 5.18, 7.78, 8.12, 0.88, 1.06)),
                 ("wl", (2.9, 3.08, 7.9, 8.12, 1.0, 3.0)), ("wr", (4.92, 5.1, 7.9, 8.12, 1.0, 3.0)),
                 ("mullv", (3.96, 4.04, 7.98, 8.06, 1.0, 3.0)), ("mullh", (3.0, 5.0, 7.98, 8.06, 1.96, 2.04))):
    slab(name, *bb, TRIM, 0.03, 0.003)

# ------------------------------------------------------------------ furniture (same layout as the voxel apartment)

RUG, RUGB = C.clay("rug", (0.55, 0.12, 0.10), 0.85, prints=0.0, dents=0.5), C.clay("rugb", (0.85, 0.70, 0.40), 0.8, prints=0.0)
boxes("rug", [((-3.6, 0.4, 4.4, 7.7, -0.01, 0.05), RUG), ((-3.6, 0.4, 4.4, 4.56, 0.0, 0.07), RUGB),
              ((-3.6, 0.4, 7.54, 7.7, 0.0, 0.07), RUGB), ((-3.6, -3.44, 4.4, 7.7, 0.0, 0.07), RUGB),
              ((0.24, 0.4, 4.4, 7.7, 0.0, 0.07), RUGB)], (0, 0, 0), r=0.025)
TEAL, TEAL2 = colmat((0.10, 0.32, 0.36), 0.8), colmat((0.13, 0.38, 0.42), 0.8)
boxes("couch", [((2.7, 5.9, 6.75, 7.85, 0.05, 0.45), TEAL), ((2.7, 5.9, 7.45, 7.85, 0.4, 1.2), TEAL),
                ((2.6, 3.05, 6.75, 7.85, 0.4, 0.8), TEAL), ((5.55, 6.0, 6.75, 7.85, 0.4, 0.8), TEAL),
                ((3.05, 4.3, 6.8, 7.45, 0.42, 0.62), TEAL2), ((4.3, 5.55, 6.8, 7.45, 0.42, 0.62), TEAL2),
                ((3.2, 4.1, 7.2, 7.5, 0.6, 1.1), colmat((0.85, 0.62, 0.20), 0.8)),
                ((4.9, 5.5, 7.25, 7.5, 0.6, 1.0), colmat((0.90, 0.88, 0.80), 0.8))], (0, 0, 0))
LAMP_POS = Vector((-4.6, 7.3, 0.0))
boxes("lamp", [((-0.27, 0.27, -0.27, 0.27, 0.0, 0.1), colmat((0.12, 0.10, 0.09), 0.4)),
               ((-0.045, 0.045, -0.045, 0.045, 0.08, 1.6), colmat((0.12, 0.10, 0.09), 0.4)),
               ((-0.32, 0.32, -0.32, 0.32, 1.5, 2.0), colmat((1.0, 0.82, 0.55), 0.6, emit=4.0))], LAMP_POS)
plant = boxes("plant", [((-0.24, 0.24, -0.24, 0.24, 0.0, 0.5), colmat((0.62, 0.30, 0.16), 0.7)),
                        ((-0.27, 0.27, -0.27, 0.27, 0.42, 0.52), colmat((0.55, 0.26, 0.14), 0.7))], (-5.4, 6.2, 0.0))
LEAF = [colmat((0.15, 0.42, 0.15), 0.7), colmat((0.20, 0.50, 0.18), 0.7)]
for k in range(9):
    a = k * 2.4
    C.ball(f"leaf{k}", rng.uniform(0.13, 0.19), LEAF[k % 2], (0.2 * math.cos(a), 0.2 * math.sin(a), 0.65 + 0.09 * k),
           plant, squash=(1.0, 0.55, 1.4))
door = boxes("door", [((-2.0, 0.0, -0.1, 0.0, 0.0, 3.0), colmat((0.42, 0.26, 0.12), 0.6)),
                      ((-1.8, -1.68, -0.24, -0.08, 1.32, 1.46), colmat((0.85, 0.72, 0.30), 0.3))], (2.0, WALL_Y, 0.0), r=0.04)
boxes("frame", [((-0.14, 0.04, -0.12, 0.02, 0.0, 3.12), TRIM), ((1.96, 2.14, -0.12, 0.02, 0.0, 3.12), TRIM),
                ((-0.14, 2.14, -0.12, 0.02, 2.98, 3.16), TRIM)], (0.0, WALL_Y, 0.0), r=0.03)

CHART_X = -3.0
parts = [((CHART_X - 0.17, CHART_X + 0.17, WALL_Y - 0.07, WALL_Y + 0.01, 0.05, 3.5), colmat((0.94, 0.92, 0.85), 0.6))]
for n in range(1, 14):
    z = 0.25 * n
    wid = 0.17 if n % 4 == 0 else 0.08
    parts.append(((CHART_X - 0.16, CHART_X - 0.16 + wid, WALL_Y - 0.1, WALL_Y - 0.06, z - 0.016, z + 0.016), colmat((0.05, 0.05, 0.05), 0.5)))
boxes("chart", parts, (0, 0, 0), r=0.012)

# ------------------------------------------------------------------ the gym bro and the counter

BRO = C.figure("bro", skin=(0.80, 0.56, 0.40), shirt=(0.42, 0.43, 0.46), pants=(0.05, 0.05, 0.06),
               shoes=(0.92, 0.92, 0.90), cap=(0.75, 0.10, 0.10), cap_back=True, tank=True, arms=1.35)
SCALE = 1.15
BRO["root"].scale = (SCALE,) * 3
G_POS = Vector((-1.6, 6.9, 0.0))
BRO["root"].location = G_POS
CTR = Vector((-1.6, 6.0, 0.0))
CT = 1.05
boxes("counter", [((-1.3, 1.3, -0.35, 0.35, 0.0, CT - 0.06), colmat((0.20, 0.22, 0.26), 0.6)),
                  ((-1.38, 1.38, -0.42, 0.42, CT - 0.1, CT), colmat((0.82, 0.80, 0.76), 0.35))], CTR)

def on_counter(x):
    return CTR + Vector((x, -0.05, CT))

tub = boxes("tub", [((-0.17, 0.17, -0.17, 0.17, 0.0, 0.42), colmat((0.95, 0.95, 0.95), 0.4)),
                    ((-0.178, 0.178, -0.178, 0.178, 0.12, 0.3), colmat((0.10, 0.30, 0.85), 0.5)),
                    ((-0.185, 0.185, -0.185, 0.185, 0.4, 0.5), colmat((0.08, 0.08, 0.1), 0.5))], AWAY, r=0.06)
eggs = boxes("eggs", [((-0.26, 0.26, -0.11, 0.11, 0.0, 0.07), colmat((0.75, 0.62, 0.45), 0.9))], AWAY, r=0.03)
for k in range(4):
    C.ball(f"egg{k}", 0.05, colmat((0.96, 0.92, 0.84), 0.5), ((k - 1.5) * 0.125, 0, 0.12), eggs, squash=(1, 1, 1.3))
liver = boxes("liver", [((-0.25, 0.25, -0.17, 0.17, 0.0, 0.03), colmat((0.95, 0.95, 0.95), 0.4))], AWAY, r=0.015)
for k, (x, y, s) in enumerate(((-0.08, 0.0, 0.13), (0.09, 0.02, 0.11), (0.0, -0.05, 0.09))):
    C.ball(f"liv{k}", s, colmat((0.38, 0.05, 0.06), 0.25), (x, y, 0.06), liver, squash=(1.2, 0.9, 0.4))
can = boxes("can", [((-0.065, 0.065, -0.065, 0.065, -0.15, 0.15), colmat((0.78, 0.80, 0.84), 0.25)),
                    ((-0.069, 0.069, -0.069, 0.069, -0.08, 0.08), colmat((0.10, 0.18, 0.55), 0.4))], AWAY, r=0.05)
alarm = B.area("alarm", Vector((-1.6, 4.0, 3.2)), Vector((-1.6, 6.9, 1.4)), 3.0, 0.0, (1.0, 0.1, 0.08))

# ------------------------------------------------------------------ lights, world, camera: warm lamps against a blue night

world = bpy.data.worlds.new("bg")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.006, 0.012, 0.045, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
ceil = B.area("ceil", Vector((-1.0, 4.5, 3.85)), Vector((-1.0, 4.5, 0)), 3.0, 200.0, (1.0, 0.84, 0.62), size_y=3.0)
key = B.area("key", Vector((-4.2, 3.8, 3.2)), Vector((-1.6, 6.6, 1.5)), 1.6, 260.0, (1.0, 0.74, 0.48))
win = B.area("win", Vector((4.0, 7.7, 2.0)), Vector((2.0, 3.0, 1.0)), 2.0, 90.0, (0.45, 0.6, 1.0))
fill = B.area("fill", Vector((3.5, 1.5, 2.5)), Vector((-1.6, 6.9, 1.5)), 4.0, 90.0, (0.22, 0.38, 1.0))
rim = B.area("rim", Vector((0.6, 7.7, 3.4)), Vector((-1.6, 6.9, 1.9)), 1.2, 160.0, (1.0, 0.7, 0.4))
gold = B.area("gold", Vector((0.5, 4.0, 3.2)), Vector((-1.6, 6.9, 1.5)), 2.5, 0.0, (1.0, 0.72, 0.3))
lamp_ld = bpy.data.lights.new("lamp", "POINT"); lamp_ld.color = (1.0, 0.72, 0.42); lamp_ld.shadow_soft_size = 0.3
lamp_l = B.link(bpy.data.objects.new("lamp_l", lamp_ld)); lamp_l.location = LAMP_POS + Vector((0, 0, 1.75))

cam = B.camera(lens=30, fstop=1.6)
B.render_settings(FPS, samples=32, motion_blur=0.3, look="AgX - Punchy")
C.cpu_preview_quality(samples=56)

# ------------------------------------------------------------------ posing

def ramp_in(t, t0, d=0.35):
    return ramp(t, t0 - d / 2, t0 + d / 2)

def pop_in(ob, t, t0, where):
    u = ramp_in(t, t0, 0.3)
    if u <= 0.01:
        ob.location = AWAY
        return
    ob.location = where + Vector((0, 0, 0.12 * math.sin(math.pi * u)))
    ob.scale = (u,) * 3

def apply_state(t):
    door.rotation_euler = (0, 0, 0)
    shock = ramp_in(t, E["sees"], 0.25) * (1 - ramp_in(t, E["I"], 0.4))
    flex = ramp_in(t, E["J"], 0.4)
    hold = 1 - ramp_in(t, E["sugar"], 0.2) * (1 - ramp_in(t, E["I"] + 0.3, 0.4))   # can drops at "sugar", picked up again
    BRO["root"].location = G_POS + Vector((0, 0.12 * shock, 0))
    BRO["root"].rotation_euler = (0, 0, 0)
    breathe = 0.02 * math.sin(t * 1.8)
    BRO["body"].scale = (1.0 + breathe, 1.0, 1.0)
    # right arm holds the can up to read; both arms up for the flex
    read = hold * (1 - flex)
    BRO["armR"].rotation_euler = (-1.25 * read - 2.9 * flex, 0, 0.25 * read - 0.6 * flex)
    BRO["armL"].rotation_euler = (-0.2 * shock - 2.9 * flex + 0.03 * math.sin(t * 1.3), 0, 0.6 * flex)
    BRO["head"].rotation_euler = (0.32 * read - 0.25 * shock, 0, 0.12 * math.sin(t * 7) * shock)
    for k, b in enumerate(BRO["brows"]):                    # worried brows and an open mouth at the sugar, a grin at the flex
        sx = (-1, 1)[k]
        b.rotation_euler = (0, 0.45 * shock * sx - 0.25 * flex * sx, 0)
        b.location.z = 0.44 + 0.035 * shock
    BRO["mouth"].scale = (1.0 - 0.35 * shock + 0.45 * flex, 1.0, 1.0 + 2.6 * shock)
    bpy.context.view_layer.update()
    if read > 0.5 or flex > 0.5:
        can.parent = BRO["armR"]
        can.location = (0, -0.1, -0.8)
        can.rotation_euler = (math.pi / 2 * (1 - flex), 0, 0)
        can.scale = (1, 1, 1)
    else:
        can.parent = None
        u = ramp_in(t, E["sugar"] + 0.15, 0.3)
        can.location = on_counter(0.55) + Vector((0, -0.1, 0.07 + 0.5 * (1 - u)))
        can.rotation_euler = (math.pi / 2, 0, 0.6)
        can.scale = (1, 1, 1)
    pop_in(tub, t, E["creatine"], on_counter(-0.75))
    pop_in(eggs, t, E["eggs"], on_counter(-0.2))
    pop_in(liver, t, E["liver"], on_counter(0.25))
    alarm.data.energy = (120.0 + 70.0 * math.sin(t * 14)) * shock
    gold.data.energy = 260.0 * flex
    dim = 1 - 0.5 * shock
    ceil.data.energy = 40.0 * dim
    lamp_ld.energy = 45.0 * dim
    loc, target, fstop, lens = camera_at(t)
    B.aim(cam, loc, target)
    cam.data.lens = lens
    cam.data.dof.focus_distance = (target - loc).length
    cam.data.dof.aperture_fstop = fstop
    cam.data.clip_start = 0.05
    cam.data.clip_end = 200

# ------------------------------------------------------------------ camera: each shot returns (camera location, look target)

def gp(z):
    return G_POS + Vector((0, 0, z))

def shot_hook(t):
    u = t / max(1.0, E["B"])
    tg = gp(1.5)
    return tg + Vector((0.8 - 0.2 * u, -4.6 + 0.4 * u, 0.3)), tg
def shot_counter(t):
    u = t - E["B"]
    tg = on_counter(-0.2) + Vector((0, 0, 0.2))
    return tg + Vector((0.6 - 0.04 * u, -2.4, 0.8)), tg
def shot_can(t):
    u = t - E["D"]
    tg = gp(1.85) + Vector((0.3, -0.4, 0))
    return tg + Vector((0.9 - 0.05 * u, -2.2 + 0.05 * u, 0.1)), tg
def shot_wide(t):
    u = t - E["F"]
    return Vector((0.8 - 0.06 * u, 2.6, 1.9)), gp(1.3)
def shot_face(t):
    u = t - E["G"]
    tg = gp(2.0)
    return tg + Vector((0.2, -1.8 + 0.12 * u, 0.0)), tg
def shot_shock(t):
    u = t - E["H"]
    tg = gp(1.6)
    return tg + Vector((-0.3, -3.2 + 0.05 * u, 0.2)), tg
def shot_flex(t):
    u = t - E["J"]
    tg = gp(1.7)
    return tg + Vector((0.4 + 0.05 * u, -3.9 - 0.15 * u, -0.6)), tg

SHOTS = [(shot_hook, None), (shot_counter, (E["B"] - 0.25, E["B"] + 0.15)), (shot_can, (E["D"] - 0.25, E["D"] + 0.15)),
         (shot_wide, (E["F"] - 0.25, E["F"] + 0.15)), (shot_face, (E["G"] - 0.2, E["G"] + 0.1)),
         (shot_shock, (E["H"] - 0.2, E["H"] + 0.1)), (shot_wide, (E["I"] - 0.25, E["I"] + 0.15)),
         (shot_flex, (E["J"] - 0.25, E["J"] + 0.15))]

LENS = {shot_wide: 26.0, shot_face: 35.0, shot_counter: 32.0}

def camera_at(t):
    k = 0
    for n, (fn, win_) in enumerate(SHOTS):
        if win_ and t >= win_[0]:
            k = n
    fn, win_ = SHOTS[k]
    loc, tg = fn(t)
    lens = LENS.get(fn, 30.0)
    if win_ and t < win_[1] and k > 0:
        fn0 = SHOTS[k - 1][0]
        loc0, tg0 = fn0(t)
        u = smooth01((t - win_[0]) / (win_[1] - win_[0]))
        loc, tg = loc0.lerp(loc, u), tg0.lerp(tg, u)
        lens = LENS.get(fn0, 30.0) * (1 - u) + lens * u
    d = (tg - loc).length * 30.0 / lens
    fstop = 1.2 if d < 3 else (1.6 if d < 6 else 2.2)          # shallower than the voxel set: the miniature look
    return loc, tg, fstop, lens

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    names = ("head", "can", "tub", "eggs", "liver")
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        pts = {
            "head": BRO["head"].matrix_world @ Vector((0, 0, 0.62)),
            "can": can.matrix_world @ Vector((0, 0, 0)),
            "tub": on_counter(-0.75) + Vector((0, 0, 0.5)),
            "eggs": on_counter(-0.2) + Vector((0, 0, 0.18)),
            "liver": on_counter(0.25) + Vector((0, 0, 0.12)),
        }
        for k, p in pts.items():
            v = world_to_camera_view(scene, cam, p)
            out[k].append([round(v.x * 1080, 1), round((1 - v.y) * 1920, 1)] if v.z > 0 and 0 <= v.x <= 1 and 0 <= v.y <= 1 else None)
    with open(os.path.join(OUT, "anchors.json"), "w") as fh:
        json.dump(out, fh)

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1 + scn.frame_subframe) / FPS)

anchors()
apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
