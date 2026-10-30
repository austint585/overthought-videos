"""Blender scene for 'Hypergamy, but backwards': a clay staircase going down through six sets at night. She starts at a
neurosurgeon's marble landing with a suitcase and walks down: regional manager's cubicle, podcast corner, mall vape
kiosk, a Honda Civic in a parking lot, and a raccoon by a dumpster at the bottom.

blender -b --factory-startup -P hypo_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Always writes out_dir/anchors.json: screen positions of label points for every frame.

Landing k sits at x = 7k, top at z = -2.2k; stairs run down the front (-y) side between landings. Add-on parts sit a few
centimetres off the face behind them so no two surfaces share a plane.
"""
import json, math, os, random, sys
import bpy, bmesh
from mathutils import Matrix, Vector
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
DX, DZ, HALF = 7.0, 2.2, 2.5

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

def ramp(t, t0, t1):
    return smooth01((t - t0) / (t1 - t0))

_mats = {}
def col(color, rough=0.6, emit=0.0):
    key = (color, rough, emit)
    if key not in _mats:
        n = f"c{len(_mats)}"
        _mats[key] = C.glow(n, color, emit) if emit else C.clay(n, color, rough, prints=0.3)
    return _mats[key]

def flat(name, color, rough=0.7):
    return C.clay(name, color, rough, prints=0.0, dents=0.4)

def slab(name, x0, x1, y0, y1, z0, z1, m, r=0.06, wobble=0.01, parent=None):
    return C.soft(name, (x1 - x0, y1 - y0, z1 - z0), m, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), parent, r=r, wobble=wobble)

def text3d(name, body, loc, size, mat, parent=None):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = 0.012
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    ob = B.link(bpy.data.objects.new(name, cu))
    ob.data.materials.append(mat)
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = (math.pi / 2, 0, 0)
    return ob

# ------------------------------------------------------------------ the staircase: six landings, each its own place

LANDS = [flat("marble", (0.86, 0.82, 0.74), 0.3), flat("carpet", (0.30, 0.32, 0.36)), flat("purplef", (0.20, 0.12, 0.30)),
         flat("tile", (0.55, 0.60, 0.58), 0.35), flat("asphalt", (0.12, 0.12, 0.13), 0.9), flat("grime", (0.10, 0.13, 0.08), 0.9)]
WALLS = [flat("wall0", (0.55, 0.42, 0.22)), flat("wall1", (0.46, 0.47, 0.50)), flat("wall2", (0.13, 0.08, 0.22)),
         flat("wall3", (0.28, 0.20, 0.42)), flat("wall4", (0.09, 0.10, 0.16)), flat("wall5", (0.14, 0.11, 0.08))]
def land_x(k): return k * DX
def land_z(k): return -k * DZ

for k in range(6):
    x, z = land_x(k), land_z(k)
    slab(f"land{k}", x - HALF, x + HALF, -2.2, 2.2, z - 1.2, z, LANDS[k], 0.06, 0.006)
    slab(f"back{k}", x - HALF - 0.02, x + HALF + 0.02, 2.25, 2.6, z - 1.3, z + 3.6, WALLS[k], 0.06, 0.012)
    if k < 5:
        n = 10
        run = DX - 2 * HALF
        for i in range(n):
            x0 = x + HALF + run * i / n
            x1 = x + HALF + run * (i + 1) / n + 0.02
            top = z - DZ * (i + 0.5) / n
            slab(f"step{k}_{i}", x0, x1, -1.9, -0.25, top - 0.5, top, LANDS[k], 0.03, 0.003)

rng = random.Random(11)
# far skyline
CITY, LITW = C.clay("city", (0.04, 0.05, 0.11), 0.8, prints=0.0), C.glow("lit", (1.0, 0.72, 0.35), 3.5)
for k in range(16):
    bx = -12 + k * 3.6 + rng.uniform(-0.5, 0.5)
    h = rng.uniform(6, 15)
    w = rng.uniform(1.8, 3.0)
    base = -16.0
    C.soft(f"bld{k}", (w, 1.5, h + 14), CITY, (bx, 17 + rng.uniform(0, 3), base + (h + 14) / 2), r=0.15, wobble=0.02)
    for j in range(9):
        wz = base + 4 + rng.uniform(0, h + 8)
        C.soft(f"bw{k}_{j}", (0.3, 0.1, 0.4), LITW, (bx + rng.uniform(-w / 3, w / 3), 15.9, wz), r=0.04, wobble=0)

# ------------------------------------------------------------------ set 0: the neurosurgeon's marble landing

GOLD = col((0.95, 0.68, 0.22), 0.3)
x, z = land_x(0), land_z(0)
for sx in (-1.9, 1.9):
    C.soft(f"col{sx}", (0.45, 0.45, 3.3), col((0.92, 0.88, 0.80), 0.35), (x + sx, 1.8, z + 1.65), r=0.12, wobble=0.006)
    C.soft(f"colcap{sx}", (0.65, 0.65, 0.18), GOLD, (x + sx, 1.8, z + 3.3), r=0.06, wobble=0.003)
C.soft("door0", (1.3, 0.1, 2.5), col((0.22, 0.11, 0.05), 0.4), (x, 2.2, z + 1.26), r=0.04, wobble=0.003)
C.ball("knob0", 0.07, GOLD, (x + 0.45, 2.1, z + 1.2), wobble=0)
for i, sx in enumerate((-0.9, -0.5, -0.1, 0.3, 0.7)):
    C.ball(f"chand{i}", 0.12, C.glow(f"chg{i}", (1.0, 0.82, 0.5), 7.0), (x + sx + 0.1, 0.8, z + 3.3 - 0.2 * abs(sx)), wobble=0)
C.soft("rug0", (2.6, 1.8, 0.04), col((0.45, 0.06, 0.08), 0.8), (x, -0.5, z + 0.03), r=0.015, wobble=0.002)

# ------------------------------------------------------------------ set 1: regional manager's cubicle

x, z = land_x(1), land_z(1)
PART = flat("partition", (0.42, 0.45, 0.52), 0.9)
slab("cubL", x + 0.05, x + 0.2, 0.2, 2.1, z + 0.02, z + 1.7, PART, 0.04, 0.004)
slab("cubB", x + 0.05, x + 2.4, 2.0, 2.15, z + 0.02, z + 1.7, PART, 0.04, 0.004)
slab("desk1", x + 0.3, x + 2.3, 0.7, 1.9, z + 0.8, z + 0.92, col((0.55, 0.40, 0.25), 0.5), 0.03, 0.003)
slab("deskleg", x + 2.0, x + 2.2, 0.8, 1.8, z + 0.02, z + 0.79, PART, 0.03, 0.002)
C.soft("monitor", (0.75, 0.06, 0.48), col((0.05, 0.05, 0.06), 0.3), (x + 1.3, 1.75, z + 1.3), r=0.02, wobble=0)
C.soft("mscreen", (0.66, 0.02, 0.39), C.glow("spread", (0.55, 0.85, 0.65), 2.5), (x + 1.3, 1.71, z + 1.3), r=0.008, wobble=0)
C.soft("mstand", (0.12, 0.1, 0.24), col((0.05, 0.05, 0.06), 0.3), (x + 1.3, 1.78, z + 1.03), r=0.03, wobble=0)
C.soft("mugd", (0.15, 0.15, 0.17), col((0.92, 0.92, 0.90), 0.3), (x + 0.75, 1.1, z + 1.01), r=0.05, wobble=0.002)
C.soft("plaque", (0.45, 0.03, 0.2), col((0.15, 0.25, 0.5), 0.4), (x - 1.2, 2.23, z + 1.9), r=0.01, wobble=0)
PIGGY = C.empty("piggy", (x + 1.75, 1.25, z + 1.14))                 # his 401(k): a fat little piggy bank on the desk
C.ball("pig.body", 0.2, col((0.92, 0.55, 0.60), 0.4), (0, 0, 0), PIGGY, squash=(1.2, 0.9, 0.9), wobble=0.004)
C.ball("pig.snout", 0.06, col((0.85, 0.42, 0.48), 0.4), (-0.24, -0.03, 0.02), PIGGY, squash=(0.6, 1, 0.9), wobble=0)
for sx in (-1, 1):
    C.ball(f"pig.ear{sx}", 0.05, col((0.85, 0.42, 0.48), 0.4), (-0.12, 0.09 * sx, 0.17), PIGGY, squash=(0.7, 1, 1), wobble=0)

# ------------------------------------------------------------------ set 2: the podcast corner, with the bed frame

x, z = land_x(2), land_z(2)
for i in range(5):
    for j in range(3):
        slab(f"foam{i}_{j}", x - 1.2 + i * 0.5, x - 0.74 + i * 0.5, 2.12, 2.24, z + 1.2 + j * 0.5, z + 1.66 + j * 0.5,
             col((0.08, 0.08, 0.10), 0.95), 0.05, 0.015)
BEDF = col((0.45, 0.28, 0.14), 0.5)
slab("bf.head", x - 2.2, x - 2.08, 0.1, 1.9, z + 0.02, z + 1.1, BEDF, 0.04, 0.004)
slab("bf.a", x - 2.18, x - 0.4, 0.1, 0.22, z + 0.25, z + 0.42, BEDF, 0.03, 0.003)
slab("bf.b", x - 2.18, x - 0.4, 1.78, 1.9, z + 0.25, z + 0.42, BEDF, 0.03, 0.003)
slab("bf.foot", x - 0.5, x - 0.38, 0.1, 1.9, z + 0.02, z + 0.55, BEDF, 0.03, 0.003)
for i in range(4):
    slab(f"bf.s{i}", x - 1.9 + i * 0.42, x - 1.72 + i * 0.42, 0.2, 1.8, z + 0.42, z + 0.47, BEDF, 0.015, 0.002)
C.soft("bf.pillow", (0.5, 0.6, 0.14), col((0.75, 0.73, 0.68), 0.8), (x - 1.8, 1.0, z + 0.56), r=0.06)
METAL = col((0.08, 0.08, 0.09), 0.35)
MIC = C.empty("mic", (x + 0.15, -0.35, z))
C.soft("mic.base", (0.4, 0.4, 0.05), METAL, (0, 0, 0.03), MIC, r=0.02, wobble=0)
C.soft("mic.pole", (0.05, 0.05, 1.45), METAL, (0, 0, 0.75), MIC, r=0.02, wobble=0)
C.soft("mic.head", (0.2, 0.2, 0.34), col((0.25, 0.25, 0.28), 0.5), (0, 0, 1.6), MIC, r=0.09, wobble=0)
C.soft("mic.band", (0.22, 0.22, 0.05), col((0.8, 0.45, 0.1), 0.3), (0, 0, 1.47), MIC, r=0.02, wobble=0)
RING = C.glow("ringl", (1.0, 0.92, 0.82), 5.0)
for i in range(16):
    a = i / 16 * 2 * math.pi
    C.ball(f"ring{i}", 0.05, RING, (x + 1.9 + 0.42 * math.cos(a), 0.6, z + 1.75 + 0.42 * math.sin(a)), wobble=0)
C.soft("ringpole", (0.04, 0.04, 1.4), METAL, (x + 1.9, 0.62, z + 0.7), r=0.015, wobble=0)
ONAIR = C.glow("onair", (1.0, 0.08, 0.05), 6.0)
C.soft("onairbox", (0.9, 0.05, 0.32), col((0.04, 0.03, 0.03), 0.4), (x + 1.1, 2.22, z + 2.9), r=0.02, wobble=0)
text3d("onairt", "ON AIR", (x + 1.1, 2.18, z + 2.9), 0.2, ONAIR)

# ------------------------------------------------------------------ set 3: the mall vape kiosk

x, z = land_x(3), land_z(3)
KIOSK = col((0.08, 0.08, 0.12), 0.3)
slab("kiosk", x + 0.6, x + 2.4, 0.2, 1.3, z + 0.02, z + 1.05, KIOSK, 0.04, 0.004)
slab("ktop", x + 0.5, x + 2.5, 0.12, 1.38, z + 1.05, z + 1.13, col((0.75, 0.75, 0.8), 0.25), 0.03, 0.003)
slab("kpost", x + 2.2, x + 2.35, 0.6, 0.8, z + 1.1, z + 3.2, KIOSK, 0.03, 0.003)
slab("kroof", x + 0.5, x + 2.5, 0.2, 1.2, z + 3.15, z + 3.3, KIOSK, 0.03, 0.003)
text3d("ksign", "VAPE WORLD", (x + 1.5, 0.15, z + 3.22), 0.2, C.glow("neon", (0.2, 1.0, 0.85), 7.0))
for i in range(8):
    c = ((1.0, 0.1, 0.6), (0.1, 0.8, 1.0), (0.6, 1.0, 0.1), (1.0, 0.6, 0.1))[i % 4]
    C.soft(f"vape{i}", (0.09, 0.05, 0.28), C.glow(f"vp{i}", c, 4.0), (x + 0.8 + i * 0.2, 0.13, z + 0.55 + 0.2 * (i % 2)), r=0.02, wobble=0)
    C.soft(f"vapet{i}", (0.09, 0.05, 0.2), C.glow(f"vt{i}", c, 3.0), (x + 0.8 + i * 0.2, 0.75, z + 1.25), r=0.02, wobble=0)
for i in range(3):
    slab(f"shop{i}", x - 2.3 + i * 1.5, x - 1.0 + i * 1.5, 2.18, 2.27, z + 0.5, z + 3.0, C.glow(f"shopg{i}", (0.85, 0.82, 0.70), 0.7), 0.01, 0)
PUFF = [C.ball(f"puff{i}", 0.2, C.clay(f"pf{i}", (0.9, 0.9, 0.95), 0.95, prints=0.0, dents=0.8), AWAY, wobble=0.02) for i in range(5)]

# ------------------------------------------------------------------ set 4: the Civic in a parking lot

x, z = land_x(4), land_z(4)
CAR = C.empty("car", (x + 1.25, 0.65, z))
SIL = col((0.48, 0.50, 0.52), 0.35)
slab("car.low", -1.25, 1.25, -0.6, 0.6, 0.25, 0.72, SIL, 0.12, 0.008, CAR)
slab("car.cab", -0.75, 0.7, -0.52, 0.52, 0.7, 1.15, SIL, 0.14, 0.006, CAR)
slab("car.win", -0.62, 0.58, -0.555, -0.5, 0.76, 1.08, col((0.05, 0.07, 0.12), 0.12), 0.03, 0, CAR)
slab("car.door", -0.05, 0.62, -0.635, -0.59, 0.3, 0.70, col((0.65, 0.12, 0.08), 0.5), 0.02, 0.002, CAR)   # the wrong color door
slab("car.hlight", -1.28, -1.24, -0.45, -0.2, 0.48, 0.62, C.glow("hl", (1.0, 0.9, 0.65), 3.0), 0.01, 0, CAR)
C.soft("car.tape", (0.42, 0.02, 0.12), col((0.75, 0.72, 0.65), 0.6), (-0.3, -0.585, 0.92), CAR, r=0.006, wobble=0)
C.soft("car.pillow", (0.4, 0.3, 0.14), col((0.82, 0.8, 0.74), 0.8), (0.1, -0.35, 1.0), CAR, r=0.06)
for wx, block in ((-0.82, False), (0.82, True)):
    if block:
        C.soft("car.block", (0.42, 0.28, 0.3), col((0.38, 0.38, 0.36), 0.95), (wx, -0.5, 0.16), CAR, r=0.03)
    else:
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.26, radius2=0.26, depth=0.2, matrix=Matrix.Rotation(math.pi / 2, 4, "X"))
        me = bpy.data.meshes.new("wheel")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(col((0.03, 0.03, 0.035), 0.75))
        wh = B.link(bpy.data.objects.new("wheel", me))
        wh.parent = CAR
        wh.location = (wx, -0.52, 0.26)
        me.shade_smooth()
LAMP = col((0.2, 0.2, 0.22), 0.4)
slab("lamp.p", x - 2.1, x - 1.95, 1.6, 1.75, z, z + 4.0, LAMP, 0.03, 0.002)
slab("lamp.a", x - 2.1, x - 0.9, 1.6, 1.75, z + 3.95, z + 4.08, LAMP, 0.03, 0.002)
C.soft("lamp.h", (0.5, 0.26, 0.1), C.glow("sodium", (1.0, 0.62, 0.22), 9.0), (x - 1.0, 1.67, z + 3.92), r=0.03, wobble=0)
for i in range(3):
    slab(f"pline{i}", x - 1.7 + i * 1.6, x - 1.58 + i * 1.6, -1.9, 1.4, z + 0.005, z + 0.02, col((0.8, 0.75, 0.45), 0.8), 0.003, 0)

# ------------------------------------------------------------------ set 5: the dumpster and the raccoon

x, z = land_x(5), land_z(5)
DG = col((0.09, 0.22, 0.13), 0.55)
slab("dump", x + 0.3, x + 2.3, 0.7, 1.9, z + 0.05, z + 1.2, DG, 0.05, 0.012)
slab("dumplid", x + 0.25, x + 2.35, 0.65, 1.95, z + 1.2, z + 1.32, col((0.04, 0.05, 0.05), 0.5), 0.04, 0.008)
for i, (bx, by) in enumerate(((x - 1.0, 1.5), (x - 0.3, 1.8), (x + 2.2, 0.1))):
    C.ball(f"bag{i}", 0.4, col((0.03, 0.03, 0.04), 0.25), (bx, by, z + 0.37), squash=(1, 1, 0.9), wobble=0.03)
C.soft("dumplight", (0.5, 0.2, 0.16), C.glow("flood", (0.75, 0.95, 0.75), 6.0), (x + 1.3, 2.18, z + 3.1), r=0.03, wobble=0)
RAC = C.empty("raccoon", (x + 0.35, -0.3, z))
FUR, DARKF, LIGHTF = col((0.32, 0.32, 0.34), 0.85), col((0.05, 0.05, 0.06), 0.8), col((0.8, 0.8, 0.8), 0.85)
C.ball("rac.body", 0.42, FUR, (0, 0, 0.42), RAC, squash=(1, 0.85, 1.1))
C.ball("rac.belly", 0.27, LIGHTF, (0, -0.2, 0.38), RAC, squash=(1, 0.6, 1.1))
RACH = C.empty("rac.head", (0, -0.05, 0.92), RAC)
C.ball("rac.skull", 0.3, FUR, (0, 0, 0), RACH, squash=(1.15, 0.95, 0.9))
C.ball("rac.snout", 0.11, LIGHTF, (0, -0.28, -0.07), RACH, squash=(1, 1.1, 0.8))
C.ball("rac.nose", 0.045, DARKF, (0, -0.39, -0.03), RACH, wobble=0)
for sx in (-1, 1):
    C.ball(f"rac.ear{sx}", 0.11, DARKF, (0.25 * sx, 0.0, 0.26), RACH, squash=(1, 0.5, 1.1), wobble=0)
    C.ball(f"rac.mask{sx}", 0.12, DARKF, (0.14 * sx, -0.235, 0.05), RACH, squash=(1.15, 0.45, 0.8), wobble=0)
    C.ball(f"rac.eye{sx}", 0.045, C.glossy(f"racg{sx}", (0.02, 0.02, 0.02)), (0.14 * sx, -0.285, 0.06), RACH, wobble=0)
    C.ball(f"rac.shine{sx}", 0.012, C.glow(f"racs{sx}", (1, 1, 1), 6.0), (0.155 * sx, -0.325, 0.08), RACH, wobble=0)
RACA = {}
for sx in (-1, 1):
    arm = C.empty(f"rac.arm{sx}", (0.36 * sx, -0.18, 0.62), RAC)
    C.ball(f"rac.upper{sx}", 0.11, DARKF, (0, -0.1, -0.05), arm, squash=(0.9, 1.6, 0.9))
    RACA[sx] = arm
C.soft("rac.sandw", (0.32, 0.12, 0.2), col((0.85, 0.65, 0.35), 0.75), (0, -0.28, -0.08), RACA[1], r=0.05)
C.soft("rac.lett", (0.34, 0.13, 0.03), col((0.3, 0.6, 0.2), 0.7), (0, -0.28, -0.08), RACA[1], r=0.012)
for k in range(5):
    C.ball(f"rac.tail{k}", 0.13 - k * 0.008, DARKF if k % 2 else LIGHTF, (0.42 + k * 0.11, 0.3, 0.14 + k * 0.07), RAC, squash=(1, 1, 0.8), wobble=0)
HEARTM = C.glow("heart", (1.0, 0.13, 0.25), 3.5)
def heart(name):
    h = C.empty(name, AWAY)
    C.ball(name + ".l", 0.11, HEARTM, (-0.08, 0, 0.05), h, wobble=0)
    C.ball(name + ".r", 0.11, HEARTM, (0.08, 0, 0.05), h, wobble=0)
    C.ball(name + ".b", 0.11, HEARTM, (0, 0, -0.08), h, squash=(1.05, 1, 1.1), wobble=0)
    return h
HEARTS = [heart(f"h{i}") for i in range(5)]

# ------------------------------------------------------------------ the people

def her_fig():
    f = C.figure("her", skin=(0.82, 0.58, 0.44), shirt=(0.85, 0.20, 0.28), pants=(0.85, 0.20, 0.28), shoes=(0.05, 0.05, 0.06),
                 hair=(0.20, 0.10, 0.04))
    HA = C.clay("herhair", (0.20, 0.10, 0.04), 0.7, prints=0.0)
    C.soft("her.long", (0.6, 0.26, 0.85), HA, (0, 0.2, 0.15), f["head"], r=0.12)
    return f
HER = her_fig()
HER["root"].scale = (0.85,) * 3
BAG = C.empty("suitcase", (0, 0, -0.78), HER["armR"])
C.soft("bag.body", (0.28, 0.72, 0.5), col((0.12, 0.45, 0.55), 0.4), (0, 0, -0.42), BAG, r=0.05)
C.soft("bag.handle", (0.1, 0.22, 0.05), col((0.05, 0.05, 0.05), 0.4), (0, 0, -0.14), BAG, r=0.02, wobble=0)

def man(name, k, shirt, pants, hair, skin=(0.78, 0.55, 0.40), cap=None, belly=1.0, shoes=(0.08, 0.06, 0.05)):
    f = C.figure(name, skin=skin, shirt=shirt, pants=pants, hair=hair, cap=cap, cap_back=False, belly=belly, shoes=shoes)
    f["root"].scale = (0.87,) * 3
    f["root"].location = (land_x(k) + 0.8, -0.3, land_z(k))
    f["root"].rotation_euler = (0, 0, -0.7)
    return f

SURG = man("surg", 0, (0.08, 0.42, 0.42), (0.08, 0.42, 0.42), (0.12, 0.07, 0.03))
C.soft("surg.mop", (0.66, 0.6, 0.3), C.clay("surgh", (0.12, 0.07, 0.03), 0.6, prints=0.0), (0, 0.02, 0.62), SURG["head"], r=0.14, wobble=0.03)
MGR = man("mgr", 1, (0.86, 0.88, 0.92), (0.14, 0.15, 0.20), (0.10, 0.07, 0.05), belly=1.25)
C.soft("mgr.tie", (0.11, 0.04, 0.48), col((0.5, 0.08, 0.1), 0.4), (0, -0.23, 0.45), MGR["body"], r=0.018, wobble=0)
MGRMUG = C.soft("mgr.mug", (0.15, 0.15, 0.17), col((0.92, 0.92, 0.90), 0.3), (0, -0.1, -0.84), MGR["armR"], r=0.05, wobble=0.002)
POD = man("pod", 2, (0.15, 0.17, 0.20), (0.22, 0.24, 0.28), (0.1, 0.07, 0.05), cap=(0.55, 0.28, 0.08))
for sx in (-1, 1):
    C.ball(f"pod.can{sx}", 0.13, METAL, (0.28 * sx, 0, 0.33), POD["head"], squash=(0.55, 1, 1.05), wobble=0)
VAPE = man("vp", 3, (0.10, 0.48, 0.38), (0.25, 0.20, 0.15), (0.05, 0.04, 0.03))
C.soft("vp.stick", (0.05, 0.05, 0.2), C.glow("vstick", (0.1, 0.8, 1.0), 4.0), (0, -0.07, -0.86), VAPE["armR"], r=0.02, wobble=0)
CIV = man("civ", 4, (0.50, 0.46, 0.34), (0.20, 0.22, 0.30), (0.16, 0.13, 0.10), belly=1.1)
C.soft("civ.beard", (0.42, 0.2, 0.22), C.clay("beard", (0.16, 0.13, 0.10), 0.85, prints=0.0), (0, -0.2, 0.13), CIV["head"], r=0.09, wobble=0.012)
CIV["root"].location = (land_x(4) + 0.1, -1.0, land_z(4))
MGR["root"].location = (land_x(1) + 0.9, -0.2, land_z(1))
POD["root"].location = (land_x(2) + 0.9, -0.35, land_z(2))
VAPE["root"].location = (land_x(3) + 1.5, 0.75, land_z(3))
VAPE["root"].rotation_euler = (0, 0, -0.25)
MEN = [SURG, MGR, POD, VAPE, CIV]

# ------------------------------------------------------------------ lights and camera

world = bpy.data.worlds.new("bg")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.008, 0.016, 0.055, 1)
LIGHT = [((1.0, 0.72, 0.42), 150.0), ((0.95, 1.0, 0.95), 110.0), ((0.8, 0.45, 1.0), 110.0), ((0.5, 1.0, 0.85), 120.0), ((1.0, 0.6, 0.25), 230.0), ((0.65, 0.95, 0.65), 170.0)]
for k, (c, p) in enumerate(LIGHT):
    x, z = land_x(k), land_z(k)
    B.area(f"key{k}", Vector((x - 0.6, -2.4, z + 3.6)), Vector((x + 0.4, 0.3, z + 0.8)), 2.6, p, c)
    B.area(f"rim{k}", Vector((x + 2.0, 1.8, z + 3.3)), Vector((x, -0.3, z + 1.2)), 1.5, p * 0.3, c)
B.area("bluefill", Vector((14, -12, 3)), Vector((16, 0, -5)), 14.0, 700.0, (0.25, 0.4, 1.0))
cam = B.camera(lens=30, fstop=2.0)
B.render_settings(FPS, samples=24, motion_blur=0.3, look="AgX - Punchy")
C.cpu_preview_quality(samples=48)

# ------------------------------------------------------------------ motion: her walk down the stairs

STOPS = [0.0, E["D"], E["E"], E["G"], E["H"], E["K"]]      # she has arrived at landing k by this time
WALK = 1.15

def stand(k):
    return Vector((land_x(k) - 0.75, -0.55, land_z(k)))

def ground_z(x):
    k = max(0, min(4, int(math.floor((x + HALF) / DX))))
    x1 = land_x(k) + HALF
    u = max(0.0, min(1.0, (x - x1) / (DX - 2 * HALF)))
    return land_z(k) - DZ * u

def her_state(t):
    """Position, heading and walk phase."""
    for k in range(1, 6):
        t1 = STOPS[k]
        if t1 - WALK <= t < t1:
            u = (t - (t1 - WALK)) / WALK
            u = u * u * (3 - 2 * u) * 0.25 + u * 0.75
            a, b = stand(k - 1), stand(k)
            x = a.x + (b.x - a.x) * u
            y = -0.9 - 0.25 * math.sin(math.pi * u)
            if u < 0.08:
                y = a.y + (-0.9 - a.y) * u / 0.08
            elif u > 0.92:
                y = b.y + (-0.9 - b.y) * (1 - u) / 0.08
            return Vector((x, y, ground_z(x))), math.pi / 2, (t - (t1 - WALK)) * 15.0, True
    k = max(i for i in range(6) if t >= STOPS[i])
    return stand(k), 0.75, 0.0, False

def apply_her(t):
    p, head, phase, walking = her_state(t)
    k = max(i for i in range(6) if t >= STOPS[i])
    HER["root"].location = p + Vector((0, 0, 0.03 * abs(math.sin(phase)) if walking else 0.0))
    HER["root"].rotation_euler = (0, 0, head)
    sw = math.sin(phase) * 0.8 if walking else 0.0
    HER["legL"].rotation_euler = (sw, 0, 0)
    HER["legR"].rotation_euler = (-sw, 0, 0)
    HER["armL"].rotation_euler = (-sw * 0.6, 0, -0.08)
    # the free hand: on her hip at the neurosurgeon, then more and more delighted further down
    delight = ramp(t, E["I"], E["I"] + 0.3)
    if not walking:
        wave = math.sin(t * 7) * 0.2 * delight
        HER["armL"].rotation_euler = (-0.15 - 2.5 * delight + wave, 0, -0.5 - 0.2 * delight)
    HER["armR"].rotation_euler = (0.0 if walking else 0.02 * math.sin(t * 2), 0, 0.08)
    disgust = ramp(t, E["C"], E["C"] + 0.2) * (1 - ramp(t, E["D"] - WALK, E["D"] - WALK + 0.2))
    sniff = ramp(t, E["smell"], E["smell"] + 0.2) * (1 - ramp(t, E["E"] - WALK, E["E"] - WALK + 0.2))
    joy = max(ramp(t, E["I"], E["I"] + 0.3), ramp(t, E["K"], E["K"] + 0.3))
    for j, b in enumerate(HER["brows"]):
        sx = (-1, 1)[j]
        b.rotation_euler = (0, (-0.45 * max(disgust, sniff) + 0.3 * joy) * sx, 0)
        b.location.z = 0.44 + 0.03 * joy
    HER["mouth"].scale = (1.0 - 0.4 * disgust + 0.7 * joy + 0.1 * k, 1.0, 1.0 + 1.5 * joy)
    HER["head"].rotation_euler = (-0.12 * disgust + 0.25 * sniff, 0, -0.3 * disgust + 0.05 * math.sin(t * 1.7))

def apply_men(t):
    # the neurosurgeon: arms out, pleading as she walks off
    plead = ramp(t, E["notice"], E["notice"] + 0.3)
    S = SURG
    S["armL"].rotation_euler = (-0.15 - 1.1 * plead + 0.08 * math.sin(t * 8) * plead, 0, -0.1 - 0.3 * plead)
    S["armR"].rotation_euler = (-0.15 - 1.1 * plead - 0.08 * math.sin(t * 8) * plead, 0, 0.1 + 0.3 * plead)
    for j, b in enumerate(S["brows"]):
        b.rotation_euler = (0, 0.4 * plead * (-1, 1)[j], 0)
    # the manager sips and shows the piggy bank
    M = MGR
    sip = 0.5 + 0.5 * math.sin((t - E["D"]) * 1.6)
    M["armR"].rotation_euler = (-1.3 - 1.0 * sip, 0, 0.45)
    M["armL"].rotation_euler = (-0.1, 0, -0.08)
    M["head"].rotation_euler = (0.05 * sip, 0, 0)
    pig = ramp(t, E["401"] - 0.1, E["401"] + 0.15) * (1 - ramp(t, E["401"] + 0.5, E["401"] + 0.8))
    PIGGY.scale = (1 + 0.5 * pig,) * 3
    # the podcast guy leans into the mic and gestures at nobody
    P = POD
    u = t - E["E"]
    P["body"].rotation_euler = (0.1, 0, 0)
    P["head"].rotation_euler = (0.1 + 0.08 * math.sin(u * 5), 0, 0.15 * math.sin(u * 2.3))
    P["armR"].rotation_euler = (-1.2 + 0.4 * math.sin(u * 4.3), 0, 0.3 + 0.15 * math.sin(u * 3.1))
    P["armL"].rotation_euler = (-1.0 - 0.3 * math.sin(u * 3.7), 0, -0.2)
    # the vape guy hits it and blows a cloud
    V = VAPE
    u = t - E["G"]
    hit = 0.5 + 0.5 * math.sin(u * 1.9 - 1.2)
    V["armR"].rotation_euler = (-1.1 - 1.3 * hit, 0, 0.55 * hit)
    V["armL"].rotation_euler = (-0.1, 0, -0.08)
    V["head"].rotation_euler = (-0.12 * hit, 0, 0)
    mouth = V["head"].matrix_world @ Vector((0, -0.3, 0.14)) if t > E["G"] else AWAY
    for i, ob in enumerate(PUFF):
        life = ((u - 1.0 - i * 0.25) % 2.5) / 2.5 if u > 1.0 + i * 0.25 else -1
        if life >= 0 and t < E["H"]:
            ob.location = mouth + Vector((-0.6 * life + 0.32 * math.sin(i * 2.4) * life, -0.25 * life, 0.55 * life + 0.3 * math.cos(i * 1.7) * life))
            ob.scale = (0.3 + 1.3 * life,) * 3
        else:
            ob.location = AWAY
    # the Civic guy: shrugging, hands up, broke and at peace
    H = CIV
    u = t - E["H"]
    shrug = 0.5 + 0.5 * math.sin(u * 2.4)
    H["armL"].rotation_euler = (-0.5 - 0.6 * shrug, 0, -0.5 - 0.3 * shrug)
    H["armR"].rotation_euler = (-0.5 - 0.6 * shrug, 0, 0.5 + 0.3 * shrug)
    H["head"].rotation_euler = (0, 0, 0.18 * math.sin(u * 1.7))
    # the raccoon eats, and looks up at the end
    bite = 0.5 + 0.5 * math.sin((t - E["K"]) * 6)
    RACA[1].rotation_euler = (-0.25 - 0.7 * bite, 0, 0)
    RACA[-1].rotation_euler = (0.3, 0, 0)
    RACH.rotation_euler = (-0.15 + 0.12 * bite, 0, -0.5 * ramp(t, E["K"] + 0.5, E["K"] + 0.9))
    for i, h in enumerate(HEARTS):
        ta = E["I"] + 0.1 + i * 0.2 if t < E["J"] else E["K"] + 0.4 + i * 0.2
        life = (t - ta) / 1.5
        if 0 <= life <= 1 and (t < E["J"] or t > E["K"]):
            hd = HER["head"].matrix_world @ Vector((0, 0, 0.5))
            h.location = hd + Vector((0.3 * math.sin(i * 2.1 + life * 3), -0.2, 0.2 + 0.8 * life))
            h.scale = (min(1.0, life * 5) * (1 - life * 0.3),) * 3
        else:
            h.location = AWAY

# ------------------------------------------------------------------ camera: a cut every 2 to 3 s

def at(k, dx, dy, dz):
    return Vector((land_x(k) + dx, dy, land_z(k) + dz))

def shot(k, start, target, push=(0, 0, 0), lens=30.0):
    def fn(t, t0):
        u = t - t0
        return at(k, *start) + Vector(push) * u, at(k, *target), lens
    return fn

def s_wide(t, t0):                     # the whole staircase, going down to the dumpster: the punchline on frame one
    u = t - t0
    return Vector((-5.2 + 0.1 * u, -6.0 + 0.06 * u, 8.2)), Vector((7.5, -0.4, -2.2 - 0.08 * u)), 23.0
def s_up(t, t0):                       # looking back up the stairs past her
    u = t - t0
    return at(4, 2.2 + 0.05 * u, -1.9, 0.6), at(2, 1.0, -0.5, 1.5), 20.0

SHOTS = [
    (0.0, s_wide),
    (E["B"], shot(0, (0.4, -4.9, 1.45), (-0.1, 0, 1.15), (0, 0.1, 0), 30.0)),
    (E["hair"], shot(0, (1.2, -2.2, 1.65), (0.75, -0.3, 1.75), (0, 0.08, 0), 34.0)),
    (E["C"], shot(0, (0.55, -2.3, 1.5), (-0.75, -0.55, 1.6), (0, 0.05, 0), 34.0)),
    (E["notice"], shot(0, (0.2, -5.2, 1.6), (0.3, 0, 1.2), (0, -0.1, 0), 28.0)),
    (E["D"], shot(1, (0.5, -5.0, 1.7), (0.5, 0.2, 1.2), (0, 0.1, 0), 28.0)),
    (E["401"] - 0.15, shot(1, (1.2, -1.2, 1.6), (1.75, 1.25, 1.15), (0, 0.06, 0), 32.0)),
    (E["smell"], shot(1, (0.55, -2.3, 1.5), (-0.75, -0.55, 1.6), (0, 0.05, 0), 34.0)),
    (E["E"], shot(2, (0.2, -4.4, 1.2), (0.25, 0, 1.1), (0, 0.1, 0), 28.0)),
    (E["listeners"], shot(2, (0.6, -1.9, 1.35), (0.45, -0.35, 1.5), (0.03, 0.05, 0), 32.0)),
    (E["F"], shot(2, (-2.1, -2.4, 1.35), (-1.3, 1.0, 0.5), (0.05, 0.05, 0), 28.0)),
    (E["G"], shot(3, (0.1, -5.0, 1.7), (0.5, 0.3, 1.5), (0, 0.1, 0), 26.0)),
    (E["office"], shot(3, (1.3, -2.8, 1.5), (1.5, 0.6, 1.35), (0, 0.07, 0), 28.0)),
    (E["H"], shot(4, (0.3, -5.6, 1.5), (0.6, 0.3, 0.95), (0, 0.12, 0), 28.0)),
    (E["forty"], shot(4, (-0.5, -3.0, 1.25), (-0.35, -0.8, 1.45), (0, 0.06, 0), 32.0)),
    (E["I"], shot(4, (0.55, -2.5, 1.5), (-0.75, -0.55, 1.75), (0, 0.06, 0), 30.0)),
    (E["J"], s_up),
    (E["K"] - 0.08, shot(5, (0.0, -4.5, 1.2), (-0.05, -0.3, 1.0), (0, 0.15, 0.02), 30.0)),
]

def camera_at(t):
    t0, fn = SHOTS[0]
    for a, b in SHOTS:
        if t >= a:
            t0, fn = a, b
    loc, tg, lens = fn(t, t0)
    p, _, _, walking = her_state(t)
    if walking:                        # follow her down the stairs
        loc, tg, lens = p + Vector((-1.2, -5.0, 1.5)), p + Vector((0.3, 0, 0.9)), 28.0
    d = (tg - loc).length * 30.0 / lens
    return loc, tg, (1.4 if d < 3 else (2.2 if d < 7 else 5.6)), lens

def apply_state(t):
    apply_her(t)
    apply_men(t)
    loc, target, fstop, lens = camera_at(t)
    B.aim(cam, loc, target)
    cam.data.lens = lens
    cam.data.dof.focus_distance = (target - loc).length
    cam.data.dof.aperture_fstop = fstop
    cam.data.clip_start = 0.05
    cam.data.clip_end = 120

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    names = ["her", "m0", "m1", "m2", "m3", "m4", "rac", "bed", "pig", "door"]
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        pts = {"her": HER["head"].matrix_world @ Vector((0, 0, 0.75)), "rac": RACH.matrix_world @ Vector((0, 0, 0.42)),
               "bed": at(2, -1.3, 1.0, 0.6), "pig": PIGGY.matrix_world @ Vector((0, 0, 0.25)),
               "door": CAR.matrix_world @ Vector((0.28, -0.64, 0.5))}
        for i, m in enumerate(MEN):
            pts[f"m{i}"] = m["head"].matrix_world @ Vector((0, 0, 0.8))
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
