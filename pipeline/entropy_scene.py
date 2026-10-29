"""Blender scene for 'The entropy of the talking stage': the clay bedroom from 'The same hour twice' (dst_scene.py), reused
again after 'The Heisenberg situationship'. A guy in bed at 2:47 a.m. watches his texts shrink day by day (a clay speech
bubble over his phone goes from a paragraph to 'haha', 'lol', 'hbu', a thumbs up, 'Seen') while a neat cube of 27 clay
molecules beside it drifts apart into disorder.

blender -b --factory-startup -P entropy_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Always writes out_dir/anchors.json: screen positions of label points for every frame.

No two surfaces of different materials share a plane (Austin saw texture flicker where they did): add-on parts sit a
few centimetres off the face behind them. The figure bends at the hip (a torso pivot), so he can sit up in bed.
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

# ------------------------------------------------------------------ materials (clay kit, night palette)

WOOD = [C.clay(f"wood{k}", c, 0.62, prints=0.0) for k, c in enumerate([(0.40, 0.24, 0.12), (0.46, 0.28, 0.14), (0.35, 0.20, 0.10)])]
WALL = C.clay("wall", (0.08, 0.15, 0.32), 0.75, prints=0.0, dents=0.35)
CEIL = C.clay("ceiling", (0.10, 0.13, 0.24), 0.8, prints=0.0, dents=0.3)
TRIM = C.clay("trim", (0.93, 0.90, 0.82), 0.55, prints=0.0)
UNDER = C.clay("under", (0.05, 0.03, 0.02), 0.9)

_mat_cache = {}
def colmat(color, rough=0.55, emit=0.0):
    key = (color, rough, emit)
    if key not in _mat_cache:
        n = f"c{len(_mat_cache)}"
        _mat_cache[key] = C.glow(n, color, emit) if emit else C.clay(n, color, rough, prints=0.3)
    return _mat_cache[key]

boxes = C.boxes

def slab(name, x0, x1, y0, y1, z0, z1, m=WALL, r=0.07, wobble=0.015):
    return C.soft(name, (x1 - x0, y1 - y0, z1 - z0), m, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), r=r, wobble=wobble)

def text3d(name, body, loc, size, mat, extrude=0.005):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    ob = B.link(bpy.data.objects.new(name, cu))
    ob.data.materials.append(mat)
    ob.location = loc
    ob.rotation_euler = (math.pi / 2, 0, 0)
    return ob

# ------------------------------------------------------------------ the room: inner floor x -3..3, y -4..3, ceiling at z 3

rng = random.Random(7)
for row in range(15):                                        # planks along x, staggered seams
    y0 = -4.3 + 0.5 * row
    x = -3.3 + rng.uniform(0, 1.0)
    slab(f"plank{row}s", -3.3, x, y0 + 0.015, y0 + 0.485, -0.16, 0.0, rng.choice(WOOD), 0.05, 0.006)
    while x < 3.3:
        x1 = min(3.3, x + rng.uniform(1.4, 2.8))
        dz = rng.uniform(-0.008, 0.008)
        slab(f"plank{row}_{x:.1f}", x + 0.015, x1 - 0.015, y0 + 0.015, y0 + 0.485, -0.16 + dz, dz, rng.choice(WOOD), 0.05, 0.006)
        x = x1
slab("underfloor", -3.8, 3.8, -4.6, 3.6, -0.5, -0.12, UNDER, 0.05, 0)
# left wall pressed together around the window (opening y 0..2, z 1..2)
slab("wallLa", -3.7, -3.0, -4.5, 0.0, -0.1, 3.3)
slab("wallLb", -3.7, -3.0, 2.0, 3.7, -0.1, 3.3)
slab("wallLc", -3.7, -3.0, -0.05, 2.05, -0.1, 1.0)
slab("wallLd", -3.7, -3.0, -0.05, 2.05, 2.0, 3.3)
slab("wallR", 3.0, 3.7, -4.5, 3.7, -0.1, 3.3)
slab("wallB", -3.7, 3.7, 3.0, 3.7, -0.1, 3.3)
slab("ceiling", -3.8, 3.8, -4.6, 3.8, 3.0, 3.5, CEIL)
BASEB = colmat((0.30, 0.18, 0.09), 0.6)
slab("bbB", -2.98, 2.98, 2.84, 3.02, 0.0, 0.22, BASEB, 0.05, 0.004)
slab("bbL", -3.02, -2.84, -4.0, 2.82, 0.0, 0.22, BASEB, 0.05, 0.004)
slab("bbR", 2.84, 3.02, -4.0, 2.82, 0.0, 0.22, BASEB, 0.05, 0.004)

# night window: deep blue sky, a moon, a clay skyline with a few lit windows
C.soft("sky", (0.08, 2.4, 1.4), C.glow("sky", (0.04, 0.07, 0.20), 1.2), (-3.62, 1.0, 1.5), r=0.01, wobble=0)
C.ball("moon", 0.13, C.glow("moon", (1.0, 0.93, 0.72), 5.0), (-3.52, 1.55, 1.72), squash=(0.3, 1, 1), wobble=0)
CITY, LIT = C.clay("city", (0.05, 0.06, 0.12), 0.8), C.glow("lit", (1.0, 0.72, 0.35), 4.0)
for k, (cy, w, h) in enumerate(((0.25, 0.4, 0.55), (0.75, 0.45, 0.35), (1.2, 0.35, 0.7))):
    C.soft(f"bldg{k}", (0.1, w, h), CITY, (-3.45, cy, 1.0 + h / 2), r=0.04, wobble=0.004)
    for wy in range(int(h / 0.16)):
        if rng.random() < 0.5:
            C.soft(f"win{k}_{wy}", (0.03, 0.06, 0.06), LIT, (-3.39, cy + rng.choice((-1, 1)) * w * 0.2, 1.1 + wy * 0.16), r=0.02, wobble=0)
for name, bb in (("wtop", (-3.12, -2.9, -0.1, 2.1, 1.98, 2.12)), ("wsill", (-3.18, -2.82, -0.18, 2.18, 0.88, 1.04)),
                 ("wl", (-3.12, -2.9, -0.1, 0.06, 1.0, 2.0)), ("wr", (-3.12, -2.9, 1.94, 2.1, 1.0, 2.0)),
                 ("mull", (-3.06, -2.98, 0.96, 1.04, 1.0, 2.0))):
    slab(name, *bb, TRIM, 0.03, 0.003)

# ------------------------------------------------------------------ furniture: bed along y, headboard against the back wall

FRAME = colmat((0.34, 0.20, 0.10), 0.6)
boxes("bed", [((-1.0, 1.0, 0.0, 2.2, 0.0, 0.32), FRAME),
              ((-0.96, 0.96, 0.03, 2.17, 0.30, 0.55), colmat((0.92, 0.90, 0.86), 0.8)),
              ((-1.0, 1.0, 2.24, 2.36, 0.0, 1.15), FRAME)], (0, 0.62, 0))
C.soft("pillow", (1.0, 0.5, 0.2), colmat((0.95, 0.94, 0.90), 0.8), (0, 2.5, 0.63), r=0.09)
BLANKET = C.clay("blanket", (0.55, 0.13, 0.10), 0.85, prints=0.0, dents=0.6)
blanket = boxes("blanket", [((-1.04, 1.04, -0.04, 1.25, 0.50, 0.80), BLANKET)], (0, 0.62, 0), r=0.12)
# nightstand with a warm little lamp and the clock
boxes("stand", [((-0.3, 0.3, -0.25, 0.25, 0.0, 0.55), FRAME),
                ((-0.24, 0.24, -0.28, -0.24, 0.30, 0.48), colmat((0.22, 0.12, 0.06), 0.6))], (1.45, 2.45, 0.0))
boxes("clock", [((-0.18, 0.18, -0.07, 0.07, 0.0, 0.16), colmat((0.05, 0.05, 0.06), 0.4))], (1.45, 2.40, 0.56), r=0.03)
DIGIT = C.glow("digit", (1.0, 0.06, 0.03), 14.0)
TIMES = ["2:47", "2:48"]
CLOCK_AT = Vector((1.45, 2.318, 0.64))
CLOCK = {s: text3d(f"t{s}", s, CLOCK_AT, 0.105, DIGIT) for s in TIMES}
boxes("nlamp", [((-0.08, 0.08, -0.08, 0.08, 0.0, 0.04), colmat((0.12, 0.10, 0.09), 0.4)),
                ((-0.02, 0.02, -0.02, 0.02, 0.03, 0.30), colmat((0.12, 0.10, 0.09), 0.4)),
                ((-0.14, 0.14, -0.14, 0.14, 0.26, 0.48), colmat((1.0, 0.80, 0.52), 0.6, emit=3.0))], (1.6, 2.62, 0.56))
# a rug, a poster, a desk with a mug, a plant: lived in
RUG, RUGB = C.clay("rug", (0.85, 0.70, 0.40), 0.85, prints=0.0, dents=0.5), C.clay("rugb", (0.30, 0.42, 0.65), 0.8, prints=0.0)
boxes("rug", [((-1.4, 1.4, -1.2, 0.5, 0.0, 0.05), RUG), ((-1.25, 1.25, -1.05, 0.35, 0.03, 0.065), RUGB)], (0, -0.4, 0), r=0.02)
boxes("poster", [((-0.45, 0.45, -0.04, 0.0, 0.0, 0.62), colmat((0.95, 0.65, 0.20), 0.7)),
                 ((-0.30, 0.30, -0.07, -0.03, 0.15, 0.45), colmat((0.15, 0.18, 0.30), 0.7))], (-1.6, 2.98, 1.55), r=0.015)
boxes("desk", [((-0.6, 0.6, -0.35, 0.35, 0.70, 0.78), FRAME), ((-0.55, -0.47, -0.3, 0.3, 0.0, 0.71), FRAME),
               ((0.47, 0.55, -0.3, 0.3, 0.0, 0.71), FRAME)], (2.3, -1.4, 0.0), r=0.03)
C.soft("mug", (0.12, 0.12, 0.13), colmat((0.95, 0.85, 0.30), 0.4), (2.1, -1.4, 0.85), r=0.05)
C.soft("laptop", (0.45, 0.32, 0.03), colmat((0.6, 0.62, 0.66), 0.3), (2.45, -1.35, 0.8), r=0.012)
plant = boxes("plant", [((-0.2, 0.2, -0.2, 0.2, 0.0, 0.42), colmat((0.62, 0.30, 0.16), 0.7))], (-2.5, 2.4, 0.0))
for k in range(8):
    a = k * 2.4
    C.ball(f"leaf{k}", rng.uniform(0.11, 0.16), colmat((0.15, 0.42, 0.15), 0.7) if k % 2 else colmat((0.20, 0.50, 0.18), 0.7),
           (0.17 * math.cos(a), 0.17 * math.sin(a), 0.55 + 0.08 * k), plant, squash=(1.0, 0.55, 1.4))

# ------------------------------------------------------------------ the guy: clay figure with a torso pivot so he can sit up

GUY = C.figure("guy", skin=(0.78, 0.55, 0.40), shirt=(0.55, 0.55, 0.58), pants=(0.12, 0.14, 0.25),
               shoes=(0.78, 0.55, 0.40), hair=(0.10, 0.07, 0.05))
torso = C.empty("guy.torso", (0, 0, 0.75), GUY["root"])
for k in ("body", "armL", "armR", "head"):                    # hang the upper body on the hip pivot
    ob = GUY[k]
    ob.parent = torso
    ob.location = ob.location - Vector((0, 0, 0.75))
GUY["torso"] = torso
GUY["root"].scale = (0.85,) * 3
SCREEN = C.glow("screen", (0.75, 0.85, 1.0), 4.0)
PHONE = boxes("phone", [((-0.06, 0.06, -0.11, 0.11, -0.016, 0.0), colmat((0.05, 0.05, 0.06), 0.3)),
                        ((-0.052, 0.052, -0.1, 0.1, 0.002, 0.01), SCREEN)],
              (0.0, 0.0, -0.9), GUY["armR"], r=0.006)
GUY_ROOT = Vector((0.0, 0.70, 0.72))

# ------------------------------------------------------------------ lights, world, camera: moonlight blue, warm practicals

world = bpy.data.worlds.new("bg")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.006, 0.012, 0.045, 1)
moon = B.area("moonl", Vector((-3.4, 1.0, 1.6)), Vector((0.0, 1.5, 0.6)), 1.2, 200.0, (0.45, 0.6, 1.0))
fill = B.area("fill", Vector((1.5, -3.5, 2.6)), Vector((0.0, 1.0, 0.6)), 3.0, 60.0, (0.22, 0.38, 1.0))
warm = B.area("warm", Vector((1.6, 2.2, 1.6)), Vector((0.0, 1.6, 0.6)), 0.6, 45.0, (1.0, 0.72, 0.42))
rim = B.area("rim", Vector((-1.5, 2.8, 2.6)), Vector((0.0, 1.8, 0.9)), 1.0, 70.0, (1.0, 0.7, 0.4))
glow = B.area("glow", Vector((0.0, 2.0, 1.2)), Vector((0.0, 2.0, 0.7)), 0.25, 0.0, (0.75, 0.85, 1.0))
glow.parent = PHONE
glow.location = (0.0, 0.0, 0.08)
glow.rotation_euler = (math.pi, 0, 0)            # shines along the phone's +z, onto his face
clock_l = B.area("clockl", Vector((1.45, 2.15, 0.75)), Vector((1.45, 1.5, 0.6)), 0.3, 6.0, (1.0, 0.1, 0.05))
cam = B.camera(lens=30, fstop=1.6)
B.render_settings(FPS, samples=32, motion_blur=0.3, look="AgX - Punchy")
C.cpu_preview_quality(samples=56)


# ------------------------------------------------------------------ props: the speech bubbles and the molecule cube

import bmesh
from mathutils import Matrix

S = Vector((0.15, 1.75, 2.05))                         # the subject point over the bed
BUB_AT = S + Vector((-0.2, 0, 0))                      # the speech bubble
MOL_AT = S + Vector((0.75, 0.1, -0.05))                # centre of the ordered molecule cube

# speech bubbles: one per day, swapped in and out. (key, lines, width, height, text colour, bubble colour)
CREAM = C.clay("bubble", (0.95, 0.92, 0.84), 0.5, prints=0.0)
GREYB = C.clay("bubgrey", (0.74, 0.77, 0.84), 0.55, prints=0.0)
INKM = C.clay("ink", (0.05, 0.06, 0.10), 0.6, prints=0.0)
GREYT = C.clay("greytext", (0.85, 0.87, 0.92), 0.6, prints=0.0)
SKIN = colmat((0.78, 0.55, 0.40), 0.6)
BUBS = {}
for key, lines, w, h, tm, bm_ in (("para", "good morning!! how did\nthe exam go?? also i saw\nthis and thought of you", 1.05, 0.40, INKM, CREAM),
                                  ("haha", "haha", 0.42, 0.18, INKM, CREAM), ("lol", "lol", 0.34, 0.18, INKM, CREAM),
                                  ("hbu", "hbu", 0.36, 0.18, INKM, CREAM), ("thumb", "", 0.30, 0.24, INKM, CREAM),
                                  ("seen", "Seen 2:47 AM", 0.74, 0.18, INKM, GREYB)):
    e = C.empty(f"bub_{key}", AWAY)
    C.soft(f"bub_{key}.body", (w, 0.07, h), bm_, (0, 0, 0), e, r=min(0.07, h * 0.45), wobble=0.004)
    C.ball(f"bub_{key}.tail", 0.05, bm_, (-w / 2 + 0.06, 0.0, -h / 2 - 0.02), e, squash=(1, 0.6, 1), wobble=0)
    if lines:
        sz = 0.075 if key == "para" else (0.08 if key == "seen" else 0.11)
        cu = bpy.data.curves.new(f"bub_{key}.txt", "FONT")
        cu.body = lines
        cu.size = sz
        cu.extrude = 0.004
        cu.align_x = "CENTER"
        cu.align_y = "CENTER"
        cu.space_line = 1.05
        ob = B.link(bpy.data.objects.new(f"bub_{key}.txt", cu))
        ob.data.materials.append(tm)
        ob.parent = e
        ob.location = (0, -0.05, 0)
        ob.rotation_euler = (math.pi / 2, 0, 0)
    else:                                                # a clay thumbs up
        C.soft(f"bub_{key}.fist", (0.11, 0.06, 0.09), SKIN, (0.0, -0.06, -0.025), e, r=0.03, wobble=0)
        C.soft(f"bub_{key}.thumb", (0.035, 0.05, 0.085), SKIN, (-0.025, -0.07, 0.06), e, r=0.016, wobble=0)
    BUBS[key] = e

# 27 molecules in a tidy cube that wander off as the days pass
MOLC = [colmat(c, 0.45) for c in ((0.35, 0.65, 1.0), (1.0, 0.62, 0.15), (0.95, 0.35, 0.45), (0.45, 0.85, 0.45))]
rng3 = random.Random(5)
MOLS = []
for i in range(3):
    for j in range(3):
        for k in range(3):
            home = MOL_AT + Vector(((i - 1) * 0.13, (j - 1) * 0.13, (k - 1) * 0.13))
            far = Vector((rng3.uniform(-1.4, 1.7), rng3.uniform(0.6, 2.5), rng3.uniform(1.45, 2.75)))
            ob = C.ball(f"mol{i}{j}{k}", 0.045, MOLC[(i + j + k) % 4], AWAY, wobble=0)
            MOLS.append((ob, home, far, rng3.uniform(0, 6.28), rng3.uniform(0.7, 1.4)))
mol_l = B.area("moll", MOL_AT + Vector((0, -1.0, 0.6)), MOL_AT, 0.6, 0.0, (0.6, 0.75, 1.0))

# ------------------------------------------------------------------ motion

def pop(t, t0, d=0.3):
    return ramp(t, t0, t0 + d)

def disorder(t):
    d = 0.25 * ramp(t, E["alone"], E["up"] + 0.4)
    for key, lvl in (("E", 0.42), ("F", 0.58), ("G", 0.72), ("H", 0.86), ("maximum", 1.0)):
        d = max(d, lvl * ramp(t, E[key], E[key] + 0.6))
    d -= 0.3 * ramp(t, E["energy"], E["energy"] + 0.4) * (1 - ramp(t, E["K"], E["K"] + 0.5))    # a flicker of hope
    return d

BUB_START = {"haha": "E", "lol": "F", "hbu": "G", "thumb": "H", "seen": "L"}

def bubble_key(t):
    if t < E["D"]:
        return None
    for key, k in (("L", "seen"), ("H", "thumb"), ("G", "hbu"), ("F", "lol"), ("E", "haha")):
        if t >= E[key] - 0.1:
            return k
    return "para"

def guy_state(t):
    sit = ramp(t, E["H"], E["H"] + 0.5) * (1 - ramp(t, E["I"] + 0.3, E["I"] + 0.9))
    GUY["root"].location = GUY_ROOT
    GUY["root"].rotation_euler = (-math.pi / 2, 0, 0)        # lying on his back, head toward +y
    GUY["torso"].rotation_euler = (math.pi / 2 * 0.8 * sit, 0, 0)
    typing = 0.0
    if E["energy"] - 0.2 < t < E["K"]:                       # thumbs going: he almost texts first
        typing = 0.07 * math.sin((t - E["energy"]) * 22.0)
    drop = ramp(t, E["nobody"], E["nobody"] + 0.5)           # ...then the phone sinks to his chest
    idle = 0.02 * math.sin(t * 3.0)
    GUY["armR"].rotation_euler = (-1.45 - 0.1 * sit + idle + typing + 0.9 * drop, 0, 0.35 - 0.2 * drop)
    scratch = ramp(t, E["G"] - 0.1, E["G"] + 0.3) * (1 - ramp(t, E["H"] - 0.3, E["H"]))
    armL = -1.30 + 0.9 * sit - 1.2 * scratch + 0.15 * scratch * math.sin(t * 14)
    GUY["armL"].rotation_euler = (armL, 0, -0.30 + 0.5 * sit + 0.4 * scratch)
    happy = 1 - ramp(t, E["E"], E["F"])
    tilt = 0.12 * math.sin(t * 5) * happy * ramp(t, E["D"], E["D"] + 0.3)
    GUY["head"].rotation_euler = (-0.25 - 0.1 * scratch, 0, tilt + 0.25 * ramp(t, E["L"], E["L"] + 0.6))
    worry = max(ramp(t, E["F"], E["G"]) * (1 - ramp(t, E["energy"], E["energy"] + 0.3)), ramp(t, E["nobody"], E["nobody"] + 0.4))
    for k, b in enumerate(GUY["brows"]):
        sx = (-1, 1)[k]
        b.rotation_euler = (0, 0.45 * worry * sx, 0)
        b.location.z = 0.44 + 0.035 * worry
    smile = happy * ramp(t, E["D"], E["D"] + 0.3)
    GUY["mouth"].scale = (1.0 + 0.5 * smile - 0.3 * worry, 1.0, 1.0 + 1.2 * worry - 0.4 * smile)
    GUY["legL"].rotation_euler = (0.1 * scratch * math.sin(t * 7), 0, 0)
    GUY["legR"].rotation_euler = (0.05, 0, 0)

def apply_state(t):
    guy_state(t)
    for s_, ob in CLOCK.items():
        ob.location = CLOCK_AT if s_ == "2:47" else AWAY
    cur = bubble_key(t)
    for k, e in BUBS.items():
        if k != cur:
            e.location = AWAY
            continue
        start = E["D"] if k == "para" else E[BUB_START[k]] - 0.1
        p = pop(t, start, 0.3)
        e.location = BUB_AT + Vector((0, 0, 0.1 * math.sin(math.pi * p) + 0.02 * math.sin(t * 2.2)))
        e.scale = (0.6 + 0.4 * p,) * 3
        e.rotation_euler = (0, 0.05 * math.sin(t * 1.4), 0)
    d = disorder(t)
    show = pop(t, E["B"] + 0.2)
    for ob, home, far, ph, sp in MOLS:
        if show < 0.01:
            ob.location = AWAY
            continue
        jig = Vector((math.sin(ph + t * 2.1 * sp), math.sin(ph * 1.7 + t * 1.6 * sp), math.sin(ph * 2.3 + t * 1.9 * sp)))
        ob.location = home.lerp(far, smooth01(d)) + jig * (0.006 + 0.09 * d)
        ob.scale = (show,) * 3
    mol_l.data.energy = 12.0 * show
    loc, target, fstop, lens = camera_at(t)
    B.aim(cam, loc, target)
    cam.data.lens = lens
    cam.data.dof.focus_distance = (target - loc).length
    cam.data.dof.aperture_fstop = fstop
    cam.data.clip_start = 0.05
    cam.data.clip_end = 60

# ------------------------------------------------------------------ camera: a cut every 2 to 3 s

def head():
    return GUY["head"].matrix_world @ Vector((0, 0, 0.25))

def shot_hook(t):          # from the foot of the bed: him, the phone, the 2:47 clock
    return Vector((0.9 + 0.02 * t, -1.6 + 0.08 * t, 1.9)), Vector((0.5, 1.9, 0.9))
def shot_mol(t):           # the tidy cube of molecules
    u = t - E["B"]
    return MOL_AT + Vector((0.5 - 0.03 * u, -1.2 + 0.04 * u, 0.2)), MOL_AT
def shot_orbit(t):         # left alone, it spreads
    u = t - E["C"]
    a = 0.3 + 0.1 * u
    return S + Vector((2.2 * math.sin(a), -2.2 * math.cos(a), 0.4)), S + Vector((0.3, 0.3, -0.1))
def shot_bub(t):           # over his face: the paragraph bubble
    u = t - E["D"]
    return BUB_AT + Vector((-0.35, -1.6 + 0.05 * u, -0.1)), BUB_AT
def shot_bubL(t):
    u = t - E["E"]
    return BUB_AT + Vector((-0.45 + 0.03 * u, -1.0, 0.05)), BUB_AT
def shot_bubR(t):
    u = t - E["F"]
    return BUB_AT + Vector((0.45 - 0.03 * u, -1.0, -0.05)), BUB_AT
def shot_wide(t):          # molecules everywhere, his hand in his hair
    u = t - E["G"]
    return S + Vector((1.2, -2.6 - 0.06 * u, 0.2)), S + Vector((0, 0.2, -0.4))
def shot_side(t):          # he sits up at the thumbs up
    u = t - E["H"]
    return Vector((-2.2 + 0.04 * u, 0.4, 1.4)), Vector((0.1, 1.7, 1.3))
def shot_max(t):           # maximum disorder: the whole room
    u = t - E["I"]
    a = -0.2 + 0.05 * u
    return Vector((2.6 * math.sin(a), -0.6 - 2.0 * math.cos(a), 2.6)), Vector((0.2, 1.6, 1.5))
def shot_face(t):          # thumbs going, almost texting first
    u = t - E["J"]
    h = head()
    return h + Vector((-0.35, -0.75 + 0.03 * u, 0.95)), h + Vector((0, 0.1, -0.05))
def shot_top(t):
    u = t - E["K"]
    a = -0.3 + 0.05 * u
    return Vector((1.5 * math.sin(a), 1.6 - 1.5 * math.cos(a), 2.85)), Vector((0.0, 1.6, 0.9))
def shot_end(t):           # 'Seen' close, then pull back over the bed
    u = t - E["L"]
    return BUB_AT + Vector((0.25 + 0.05 * u, -1.15 - 0.3 * u, 0.05 + 0.08 * u)), BUB_AT + Vector((0, 0, -0.12 * min(u, 4.0)))

SHOTS = [(shot_hook, None), (shot_mol, (E["B"] - 0.25, E["B"] + 0.15)), (shot_orbit, (E["C"] - 0.25, E["C"] + 0.15)),
         (shot_bub, (E["D"] - 0.25, E["D"] + 0.15)), (shot_bubL, (E["E"] - 0.25, E["E"] + 0.15)),
         (shot_bubR, (E["F"] - 0.25, E["F"] + 0.15)), (shot_wide, (E["G"] - 0.25, E["G"] + 0.15)),
         (shot_side, (E["H"] - 0.25, E["H"] + 0.15)), (shot_max, (E["I"] - 0.25, E["I"] + 0.15)),
         (shot_face, (E["J"] - 0.25, E["J"] + 0.15)), (shot_top, (E["K"] - 0.25, E["K"] + 0.15)),
         (shot_end, (E["L"] - 0.25, E["L"] + 0.15))]
LENS = {shot_hook: 26.0, shot_mol: 38.0, shot_bubL: 40.0, shot_bubR: 40.0, shot_max: 24.0, shot_top: 24.0,
        shot_end: 28.0, shot_face: 35.0}

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
    fstop = 1.2 if d < 2 else (1.6 if d < 4 else 2.2)          # the miniature look
    return loc, tg, fstop, lens

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    names = ("bub", "mol", "guy")
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        pts = {"bub": BUB_AT + Vector((0, 0, 0.3)), "mol": MOL_AT + Vector((0, 0, 0.25)), "guy": head() + Vector((0, 0, 0.3))}
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
