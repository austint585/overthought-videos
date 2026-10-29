"""Blender scene for 'The Heisenberg situationship': the clay bedroom from 'The same hour twice' (dst_scene.py), reused.
A guy in bed at 2:47 a.m. watches a location pin over his phone: the pin is sharp, the arrows around it point
everywhere. Originally: a clay bedroom (clay.py, the @petersindex look) at night, a guy in bed on his phone, a digital clock on the
nightstand that falls back from 1:59 to 1:00, moonlight through the window. Built in code and timed to the narration.

blender -b --factory-startup -P dst_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
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


# ------------------------------------------------------------------ props: the particle, the arrows of where it is going, the location pin

import bmesh
from mathutils import Matrix

def cone(name, r, h, mat, parent=None, loc=(0, 0, 0)):
    """A soft clay cone, tip up along +z, base at z 0."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r, radius2=0.0, depth=h,
                          matrix=Matrix.Translation((0, 0, h / 2)))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = B.link(bpy.data.objects.new(name, me))
    ob.parent = parent
    ob.location = loc
    sd = ob.modifiers.new("soft", "SUBSURF")
    sd.levels = sd.render_levels = 1
    me.shade_smooth()
    return ob

S = Vector((0.15, 1.75, 2.05))                         # the subject point over the bed: particle, then pin
PART = C.ball("particle", 0.12, C.glow("partglow", (0.55, 0.75, 1.0), 9.0), AWAY, wobble=0)
ARROW_M = C.clay("arrow", (1.0, 0.62, 0.12), 0.4, prints=0.0, emit=0.6, emit_color=(1.0, 0.55, 0.1))
arw = []
rng2 = random.Random(11)
for k in range(9):
    a = C.empty(f"arw{k}", AWAY)
    C.soft(f"arw{k}.shaft", (0.05, 0.05, 0.34), ARROW_M, (0, 0, 0.25), a, r=0.022, wobble=0)
    cone(f"arw{k}.tip", 0.075, 0.15, ARROW_M, a, (0, 0, 0.41))
    arw.append((a, rng2.uniform(0, 6.28), rng2.uniform(0, 6.28), rng2.uniform(0.6, 1.6)))
PIN_M = C.clay("pin", (0.92, 0.16, 0.12), 0.35, prints=0.0)
pin = C.empty("pin", AWAY)
C.ball("pin.head", 0.17, PIN_M, (0, 0, 0.3), pin, squash=(1, 0.8, 1))
tip = cone("pin.tip", 0.11, 0.26, PIN_M, pin, (0, 0, 0.27))
tip.rotation_euler = (math.pi, 0, 0)
C.ball("pin.dot", 0.065, C.glow("pindot", (1.0, 0.97, 0.92), 3.0), (0, -0.12, 0.31), pin, squash=(1, 0.5, 1), wobble=0)
pin_glow = B.area("pinl", S + Vector((0, -1.0, 0.6)), S, 0.5, 0.0, (1.0, 0.35, 0.25))

# ------------------------------------------------------------------ motion

def pop(t, t0, d=0.3):
    return ramp(t, t0, t0 + d)

def arrows_on(t):
    return pop(t, E["momentum"]) * (1 - pop(t, E["D"] - 0.2)) + pop(t, E["undefined"]) * (1 - pop(t, E["I"] - 0.2))

def guy_state(t):
    sit = ramp(t, E["G"] - 0.2, E["G"] + 0.5) * (1 - ramp(t, E["I"] - 0.1, E["I"] + 0.5))
    GUY["root"].location = GUY_ROOT
    GUY["root"].rotation_euler = (-math.pi / 2, 0, 0)        # lying on his back, head toward +y
    GUY["torso"].rotation_euler = (math.pi / 2 * 0.85 * sit, 0, 0)
    refresh = 0.0
    if t > E["refresh"] - 0.1:                               # hard thumb refreshes
        refresh = 0.12 * max(0.0, math.sin((t - E["refresh"]) * 18.0)) * (1 - ramp(t, E["worse"], E["worse"] + 0.4))
    idle = 0.02 * math.sin(t * 3.0)
    GUY["armR"].rotation_euler = (-1.45 - 0.1 * sit + idle + refresh, 0, 0.35)
    GUY["armL"].rotation_euler = (-1.30 + 0.9 * sit, 0, -0.30 + 0.5 * sit)     # left hand drops to the blanket when he sits
    look_up = ramp(t, E["D"], E["D"] + 0.4) * (1 - ramp(t, E["G"], E["G"] + 0.4))
    GUY["head"].rotation_euler = (-0.25 - 0.15 * look_up, 0, 0.12 * math.sin(t * 6) * sit)
    worry = ramp(t, E["G"], E["G"] + 0.3) * (1 - ramp(t, E["I"] + 0.4, E["I"] + 0.8)) + ramp(t, E["worse"], E["worse"] + 0.3)
    worry = min(1.0, worry)
    for k, b in enumerate(GUY["brows"]):
        sx = (-1, 1)[k]
        b.rotation_euler = (0, 0.45 * worry * sx, 0)
        b.location.z = 0.44 + 0.035 * worry
    GUY["mouth"].scale = (1.0 - 0.3 * worry, 1.0, 1.0 + 1.8 * worry)
    GUY["legL"].rotation_euler = (0, 0, 0)
    GUY["legR"].rotation_euler = (0.05, 0, 0)

def apply_state(t):
    guy_state(t)
    cur = "2:48" if t > E["hbar"] else "2:47"
    for s_, ob in CLOCK.items():
        ob.location = CLOCK_AT if s_ == cur else AWAY
    # the particle: B to D, then the pin takes its place over the phone
    pu = pop(t, E["B"] + 0.3) * (1 - pop(t, E["D"] - 0.2))
    if pu > 0.01:
        PART.location = S + Vector((0.03 * math.sin(t * 5), 0, 0.04 * math.sin(t * 3.3)))
        PART.scale = (pu,) * 3
    else:
        PART.location = AWAY
    pn = pop(t, E["location"], 0.35)
    if pn > 0.01:
        jit = 0.03 * math.sin(t * 23.0) if t > E["refresh"] else 0.0     # each refresh: still exactly here
        pin.location = S + Vector((jit, 0, 0.18 * math.sin(math.pi * pn) + 0.03 * math.sin(t * 2.4)))
        pin.scale = (pn,) * 3
        pin.rotation_euler = (0, 0, 0.4 * math.sin(t * 1.3))
    else:
        pin.location = AWAY
    pin_glow.data.energy = 25.0 * pn
    on = arrows_on(t)
    for k, (a, ph, ph2, sp) in enumerate(arw):
        if on <= 0.01:
            a.location = AWAY
            continue
        ang = ph + t * sp * (1.0 + 2.5 * ramp(t, E["refresh"], E["refresh"] + 0.4))
        el = 0.6 * math.sin(ph2 + t * sp * 0.7)
        d = Vector((math.cos(ang) * math.cos(el), math.sin(ang) * math.cos(el), math.sin(el)))
        a.location = S + d * 0.42
        a.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        a.scale = (on,) * 3
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
def shot_part(t):          # the particle hanging over the bed
    u = t - E["B"]
    return S + Vector((0.9 - 0.04 * u, -1.9 + 0.05 * u, -0.3)), S + Vector((0, 0, -0.35))
def shot_partc(t):         # close: the arrows around it
    u = t - E["momentum"]
    a = -0.6 + 0.12 * u
    return S + Vector((1.1 * math.sin(a), -1.1 * math.cos(a), 0.15)), S
def shot_orbit(t):
    u = t - E["C"]
    a = 0.5 + 0.1 * u
    return S + Vector((1.5 * math.sin(a), -1.5 * math.cos(a), 0.5)), S + Vector((0, 0, -0.2))
def shot_phone(t):         # over his face: phone up, the pin popping out of it
    u = t - E["D"]
    return S + Vector((-0.9, -1.1 + 0.05 * u, -0.25)), S + Vector((0, 0, -0.25))
def shot_pin(t):           # pin close-up
    u = t - E["E"]
    return S + Vector((0.25, -0.95 + 0.04 * u, 0.25)), S + Vector((0, 0, 0.28))
def shot_wide(t):          # arrows everywhere around a perfectly known pin
    u = t - E["F"]
    return S + Vector((1.2, -2.4 - 0.06 * u, 0.3)), S + Vector((0, 0, -0.3))
def shot_side(t):          # he sits up
    u = t - E["G"]
    return Vector((-2.2 + 0.04 * u, 0.4, 1.4)), Vector((0.3, 1.6, 1.15))
def shot_face(t):
    u = t - E["cant"]
    h = head()
    return h + Vector((-0.2, -1.3 + 0.05 * u, 0.1)), h + Vector((0, 0, -0.05))
def shot_clock(t):
    u = t - E["H"]
    return Vector((1.05 + 0.02 * u, 1.35 + 0.03 * u, 1.05)), Vector((1.45, 2.36, 0.42))
def shot_top(t):
    u = t - E["I"]
    a = -0.3 + 0.05 * u
    return Vector((1.5 * math.sin(a), 1.6 - 1.5 * math.cos(a), 2.85)), Vector((0.0, 1.6, 0.9))
def shot_end(t):
    u = t - E["J"]
    return Vector((0.4, -2.0 - 0.12 * u, 2.0 + 0.04 * u)), Vector((0.3, 1.7, 1.1))

SHOTS = [(shot_hook, None), (shot_part, (E["B"] - 0.25, E["B"] + 0.15)),
         (shot_partc, (E["momentum"] - 0.25, E["momentum"] + 0.15)), (shot_orbit, (E["C"] - 0.25, E["C"] + 0.15)),
         (shot_phone, (E["D"] - 0.25, E["D"] + 0.15)), (shot_pin, (E["E"] - 0.25, E["E"] + 0.15)),
         (shot_wide, (E["F"] - 0.25, E["F"] + 0.15)), (shot_side, (E["G"] - 0.25, E["G"] + 0.15)),
         (shot_face, (E["cant"] - 0.25, E["cant"] + 0.15)), (shot_clock, (E["H"] - 0.25, E["H"] + 0.15)),
         (shot_top, (E["I"] - 0.25, E["I"] + 0.15)), (shot_end, (E["J"] - 0.25, E["J"] + 0.15))]
LENS = {shot_hook: 26.0, shot_partc: 35.0, shot_pin: 40.0, shot_clock: 45.0, shot_top: 24.0, shot_end: 26.0,
        shot_face: 35.0}

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
    names = ("pin", "guy", "part")
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        pts = {"pin": S + Vector((0, 0, 0.55)), "guy": head() + Vector((0, 0, 0.3)), "part": S + Vector((0, 0, 0.15))}
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
