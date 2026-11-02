"""Blender scene for 'The note in your lunch': a clay kitchen at night with no people in it, props moving on their own in
stop motion (12 steps a second, the camera stays smooth), plus a school cafeteria table. Shots, timed by render_lunch.py:

  open, write     the bag on the counter, a marker writing on it        wide, wide2     the whole kitchen (wide2 years later, your duffel out)
  clock           the wall clock at 10:04                               knife, crust    the board: the knife, then the crusts coming off
  fridge          a crayon drawing on the fridge                        note            the folded note going into the bag
  cafe            chips, apple sliding away, cookie sliding in          trash           the balled-up note dropping into a can
  clock2          the clock again, years later                          plate, crust2   a new sandwich on a plate
  final, ending   the kitchen with your duffel, then the note, read at last

blender -b --factory-startup -P lunch_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Add-on parts sit a few millimetres off the face behind them so no two surfaces share a plane.
"""
import json, math, os, random, sys
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bkit as B
import clay as C

argv = sys.argv[sys.argv.index("--") + 1:]
TIMING, OUT, MODE = argv[0], argv[1], argv[2]
T = json.load(open(TIMING))
FPS, DUR, SHOTS = T["fps"], T["duration"], T["shots"]
NF = int(round(DUR * FPS))
os.makedirs(OUT, exist_ok=True)
B.clear_scene()
scene = B.scene
AWAY = Vector((0, 0, -1.0e4))
TOP = 0.90          # counter height
HAND = bpy.data.fonts.load("C:/Windows/Fonts/segoesc.ttf")

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

w = bpy.data.worlds.new("w")
scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.012, 0.018, 0.045, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0

_m = {}
def col(color, rough=0.6, prints=0.0):
    key = (color, rough, prints)
    if key not in _m:
        _m[key] = C.clay(f"c{len(_m)}", color, rough, prints=prints, dents=0.5)
    return _m[key]

def slab(name, x0, x1, y0, y1, z0, z1, m, r=0.02, wobble=0.003, parent=None):
    return C.soft(name, (x1 - x0, y1 - y0, z1 - z0), m, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), parent, r=r, wobble=wobble)

def writing(name, body, loc, size, mat, parent=None):
    """Handwriting on a face looking at -y. Grows letter by letter through .data.body, so it is left aligned."""
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = HAND
    cu.size = size
    cu.extrude = 0.0006
    cu.align_x = "LEFT"
    ob = B.link(bpy.data.objects.new(name, cu))
    ob.data.materials.append(mat)
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = (math.pi / 2, 0, 0)
    return ob

def disc(name, r, h, mat, loc, parent=None, upright=True):
    """A true round disc (soft() can't round past its thinnest side), facing -y when upright."""
    ob = B.mesh_from(name, B.cyl_z(r, -h / 2, h / 2, 0, 0, seg=72), [mat])
    B.smooth(ob, 40)
    ob.parent = parent
    ob.location = loc
    if upright:
        ob.rotation_euler = (math.pi / 2, 0, 0)
    return ob

# ------------------------------------------------------------------ the kitchen

WALL = col((0.07, 0.11, 0.26))
CAB = col((0.20, 0.30, 0.34))
WOOD = col((0.42, 0.25, 0.12), 0.5)
slab("floor", -6, 6, -5, 1.0, -0.2, 0.0, col((0.22, 0.14, 0.09), 0.65), 0.02, 0.0)
slab("wall", -6, 6, 0.36, 0.6, 0, 3.2, WALL, 0.02, 0.003)
slab("base", -1.7, 1.9, -0.32, 0.34, 0.0, TOP - 0.05, CAB)
slab("counter", -1.75, 1.95, -0.38, 0.345, TOP - 0.05, TOP, WOOD, 0.012, 0.001)
for i in range(6):
    x = -1.68 + i * 0.6
    slab(f"door{i}", x + 0.02, x + 0.56, -0.345, -0.31, 0.08, TOP - 0.1, col((0.25, 0.37, 0.40)), 0.02, 0.002)
    C.ball(f"pull{i}", 0.018, col((0.85, 0.66, 0.3), 0.3), (x + 0.5, -0.36, TOP - 0.2), wobble=0)
for i in range(2):
    x = 1.0 + i * 0.5
    slab(f"up{i}", x, x + 0.47, 0.02, 0.34, 1.5, 2.3, col((0.25, 0.37, 0.40)), 0.02, 0.002)
# window with the night in it
slab("win_f", 0.12, 0.92, 0.325, 0.40, 1.22, 1.98, col((0.75, 0.70, 0.60)), 0.012, 0.001)
slab("win_g", 0.17, 0.87, 0.305, 0.33, 1.27, 1.93, C.glow("night", (0.05, 0.10, 0.34), 0.55), 0.004, 0)
C.ball("moon", 0.06, C.glow("moon", (1.0, 0.95, 0.75), 5.0), (0.68, 0.296, 1.74), wobble=0)
slab("win_x", 0.505, 0.535, 0.29, 0.30, 1.27, 1.93, col((0.75, 0.70, 0.60)), 0.004, 0)
slab("win_y", 0.17, 0.87, 0.29, 0.30, 1.585, 1.615, col((0.75, 0.70, 0.60)), 0.004, 0)
# pendant lamp, the only light on
LAMP_AT = Vector((-0.22, -0.03, 1.62))
C.soft("cord", (0.012, 0.012, 1.5), col((0.05, 0.05, 0.05)), LAMP_AT + Vector((0, 0, 0.82)), r=0.005, wobble=0)
C.soft("shade", (0.32, 0.32, 0.16), col((0.85, 0.55, 0.20), 0.45), LAMP_AT + Vector((0, 0, 0.03)), r=0.075, wobble=0.003)
C.ball("bulb", 0.05, C.glow("bulbg", (1.0, 0.8, 0.5), 18.0), LAMP_AT + Vector((0, 0, -0.06)), wobble=0)
sp = bpy.data.lights.new("lampkey", "SPOT")
sp.energy, sp.color, sp.spot_size, sp.spot_blend = 170.0, (1.0, 0.72, 0.42), 1.9, 0.75
sp.shadow_soft_size = 0.06
ob = B.link(bpy.data.objects.new("lampkey", sp))
ob.location = LAMP_AT - Vector((0, 0, 0.05))
B.area("fill", (1.2, -3.0, 2.2), (0, 0, 1.0), 2.0, 45.0, color=(0.35, 0.5, 1.0))
B.area("warm", (-0.3, -1.5, 2.3), (-0.3, 0, 1.0), 2.2, 60.0, color=(1.0, 0.72, 0.45))
B.area("winlight", (0.5, 0.2, 1.6), (0.3, -0.5, 0.9), 0.7, 5.0, color=(0.4, 0.55, 1.0))
# wall clock
CLOCK = Vector((-1.15, 0.345, 1.78))
disc("clk", 0.18, 0.04, col((0.85, 0.82, 0.72), 0.4), CLOCK)
disc("clkr", 0.2, 0.03, col((0.5, 0.12, 0.08)), CLOCK + Vector((0, 0.012, 0)))
BLK = col((0.02, 0.02, 0.03), 0.35)
for i in range(12):
    a = i * math.pi / 6
    C.ball(f"tick{i}", 0.007, BLK, CLOCK + Vector((0.135 * math.sin(a), -0.024, 0.135 * math.cos(a))), wobble=0)
def hand(name, ln, th):
    root = C.empty(name, CLOCK + Vector((0, -0.028, 0)))
    C.soft(name + "b", (th, 0.006, ln), BLK, (0, 0, ln / 2 - 0.01), root, r=0.002, wobble=0)
    return root
H_H, H_M = hand("hh", 0.08, 0.016), hand("hm", 0.125, 0.011)
# fridge with a first-grader's drawing
slab("fridge", -2.75, -1.82, -0.42, 0.33, 0, 2.0, col((0.72, 0.74, 0.72), 0.35), 0.05, 0.003)
slab("fridge_gap", -2.74, -1.83, -0.435, -0.41, 1.28, 1.30, col((0.15, 0.15, 0.17)), 0.004, 0)
FR = Vector((-2.28, -0.44, 1.60))
slab("paper", FR.x - 0.21, FR.x + 0.21, FR.y - 0.004, FR.y + 0.03, FR.z - 0.15, FR.z + 0.15, col((0.86, 0.80, 0.66), 0.8), 0.003, 0.0006)
def crayon(name, x, z, sx, sz, color, rot=0.0):
    C.soft(name, (sx, 0.004, sz), col(color, 0.8), FR + Vector((x, -0.008, z)), r=0.003, wobble=0.0005, rot=(0, rot, 0))
SUN, GRN, RD, BLU, BRN = (0.95, 0.68, 0.08), (0.14, 0.45, 0.12), (0.72, 0.08, 0.06), (0.05, 0.16, 0.6), (0.08, 0.05, 0.03)
crayon("grass", 0, -0.115, 0.38, 0.03, GRN)
C.ball("csun", 0.035, col(SUN, 0.8), FR + Vector((0.14, -0.01, 0.09)), squash=(1, 0.1, 1), wobble=0)
for i in range(6):
    a = i * math.pi / 3
    crayon(f"ray{i}", 0.14 + 0.055 * math.cos(a), 0.09 + 0.055 * math.sin(a), 0.03, 0.007, SUN, -a)
for name, x, h, shirt in (("big", -0.10, 0.17, RD), ("kid", 0.03, 0.11, BLU)):
    base = -0.095
    crayon(name + "b", x, base + h * 0.42, 0.012, h * 0.55, shirt)
    C.ball(name + "h", 0.022, col(BRN, 0.8), FR + Vector((x, -0.01, base + h * 0.85)), squash=(1, 0.1, 1), wobble=0)
    crayon(name + "a1", x - 0.022, base + h * 0.55, 0.045, 0.008, shirt, 0.5)
    crayon(name + "a2", x + 0.022, base + h * 0.55, 0.045, 0.008, shirt, -0.5)
for i, (x, z) in enumerate(((-0.17, 0.12), (0.17, 0.12))):
    C.ball(f"mag{i}", 0.02, col((0.8, 0.2, 0.15) if i else (0.15, 0.5, 0.75), 0.3), FR + Vector((x, -0.016, z)), squash=(1, 0.6, 1), wobble=0)

# ------------------------------------------------------------------ props, built once and moved per shot

BREAD = col((0.85, 0.70, 0.46), 0.75, 0.3)
CRUST = col((0.40, 0.20, 0.07), 0.6, 0.3)
JAM = col((0.34, 0.03, 0.14), 0.3)
PB = col((0.60, 0.34, 0.12), 0.5)
PAPERB = col((0.56, 0.38, 0.20), 0.85, 0.2)
INK = col((0.01, 0.01, 0.015), 0.5)
KRAFT = col((0.66, 0.46, 0.26), 0.8, 0.2)
NAP = col((0.90, 0.88, 0.82), 0.85)

BOARD = slab("board", -0.20, 0.20, -0.15, 0.15, 0.0, 0.025, col((0.55, 0.36, 0.16), 0.55), 0.008, 0.001, C.empty("boardroot"))
BOARD_R = BOARD.parent
def sandwich(name):
    root = C.empty(name)
    S = 0.085
    for z, h, m in ((0.0, 0.022, BREAD), (0.022, 0.006, PB), (0.0285, 0.006, JAM), (0.035, 0.022, BREAD)):
        slab(f"{name}{z}", -S, S, -S, S, z, z + h, m, 0.006, 0.0012, root)
    crusts = []
    for i, (dx, dy, sx, sy) in enumerate(((0, -1, 2, 0), (1, 0, 0, 2), (0, 1, 2, 0), (-1, 0, 0, 2))):
        c = C.empty(f"{name}c{i}", (dx * (S + 0.006), dy * (S + 0.006), 0.0), root)
        for j, z in enumerate((0.0, 0.035)):
            slab(f"{name}c{i}{j}", -S - 0.008 if sx else -0.008, S + 0.008 if sx else 0.008, -S - 0.008 if sy else -0.008, S + 0.008 if sy else 0.008,
                 z - 0.001, z + 0.023, CRUST, 0.006, 0.0008, c)
        crusts.append(c)
    return root, crusts
SAND, CRUSTS = sandwich("sand")
SAND2, CRUSTS2 = sandwich("sandb")

KNIFE = C.empty("knife")
C.soft("blade", (0.22, 0.004, 0.036), C.glossy("steel", (0.62, 0.64, 0.66), 0.22), (0.11, 0, 0.018), KNIFE, r=0.0015, wobble=0)
C.soft("khandle", (0.13, 0.022, 0.03), col((0.08, 0.06, 0.05), 0.4), (-0.06, 0, 0.022), KNIFE, r=0.01, wobble=0.0005)

BAG = C.empty("bag")
slab("bagb", -0.11, 0.11, -0.07, 0.07, 0, 0.30, PAPERB, 0.012, 0.002, BAG)
BAGFOLD = C.empty("bagfold", (0, 0.07, 0.30), BAG)
slab("bagf", -0.112, 0.112, -0.145, 0.0, -0.005, 0.009, col((0.50, 0.33, 0.17), 0.85, 0.2), 0.004, 0.001, BAGFOLD)
BAGTX = writing("bagtx", "your name", (-0.092, -0.0755, 0.13), 0.040, INK, BAG)

MARK = C.empty("marker")
C.soft("mbody", (0.022, 0.022, 0.13), col((0.04, 0.04, 0.05), 0.35), (0, 0, 0.085), MARK, r=0.01, wobble=0)
C.soft("mband", (0.0235, 0.0235, 0.012), col((0.85, 0.82, 0.74), 0.5), (0, 0, 0.11), MARK, r=0.005, wobble=0)
C.soft("mtip", (0.009, 0.009, 0.022), BLK, (0, 0, 0.012), MARK, r=0.004, wobble=0)

NOTEF = slab("notef", -0.05, 0.05, -0.035, 0.035, 0.0, 0.006, NAP, 0.002, 0.0006)        # folded, face hidden
NOTE_R = C.empty("noteflat")
slab("noteb", -0.21, 0.21, -0.29, 0.29, -0.006, 0.0, NAP, 0.003, 0.0012, NOTE_R)
for i in range(3):
    slab(f"nw{i}", -0.20, 0.20, -0.14 + i * 0.145, -0.138 + i * 0.145, 0.0001, 0.0009, col((0.72, 0.70, 0.64)), 0.0004, 0, NOTE_R)
NOTE_TX = []
for i, (s, y, sz) in enumerate((("eat the apple.", 0.10, 0.056), ("love, mom", -0.05, 0.056))):
    tx = writing(f"ntx{i}", s, (-0.18, y, 0.0012), sz, col((0.02, 0.05, 0.28), 0.5), NOTE_R)
    tx.rotation_euler = (0, 0, 0)
    NOTE_TX.append(tx)
BALLN = C.ball("balled", 0.04, NAP, (0, 0, 0), wobble=0.012)

DUFFEL = C.empty("duffel")
C.soft("dufb", (0.62, 0.30, 0.30), col((0.05, 0.10, 0.24), 0.7, 0.2), (0, 0, 0.15), DUFFEL, r=0.12, wobble=0.012)
C.soft("dufs", (0.34, 0.03, 0.10), col((0.70, 0.62, 0.46), 0.6), (0, -0.15, 0.31), DUFFEL, r=0.012, wobble=0.002)

PLATE = C.empty("plate")
slab("plateb", -0.15, 0.15, -0.15, 0.15, 0.0, 0.016, col((0.82, 0.84, 0.86), 0.25), 0.007, 0.0005, PLATE)

# ------------------------------------------------------------------ the cafeteria, its own set, x = 12

CAFE = Vector((12.0, 0.0, 0.0))
slab("cfloor", 9, 15, -4, 2.5, -0.2, 0, col((0.55, 0.53, 0.46), 0.35), 0.01, 0.0)
slab("cwall", 9, 15, 1.5, 1.7, 0, 3.2, col((0.62, 0.72, 0.62)), 0.02, 0.002)
slab("cwall2", 9, 15, 1.48, 1.5, 0.0, 1.05, col((0.28, 0.42, 0.50)), 0.006, 0.001)
slab("ctable", 10.8, 13.2, -0.42, 0.42, 0.72, TOP - 0.03, col((0.34, 0.50, 0.44), 0.3), 0.012, 0.001)
for x in (11.0, 13.0):
    slab(f"cleg{x}", x - 0.03, x + 0.03, -0.3, 0.3, 0, 0.72, col((0.4, 0.4, 0.42), 0.3), 0.012, 0)
B.area("csun", (11.0, -2.2, 3.0), (12.0, 0.0, 0.9), 2.5, 55.0, color=(1.0, 0.96, 0.88))
B.area("cfill", (13.6, -2.0, 1.5), (12.0, 0, 0.9), 2.0, 12.0, color=(0.75, 0.85, 1.0))
CT = TOP - 0.03
CHIPS = C.soft("chips", (0.20, 0.05, 0.27), col((0.80, 0.14, 0.06), 0.22), CAFE + Vector((-0.20, 0.05, CT + 0.135)), r=0.022, wobble=0.006)
BAG2 = C.soft("bag2", (0.20, 0.11, 0.22), PAPERB, CAFE + Vector((0.20, 0.22, CT + 0.11)), r=0.012, wobble=0.004)
APPLE = C.empty("apple")
C.ball("appleb", 0.062, col((0.62, 0.05, 0.04), 0.22), (0, 0, 0.058), APPLE, squash=(1, 1, 0.92), wobble=0.002)
C.soft("stem", (0.007, 0.007, 0.03), col((0.15, 0.09, 0.04)), (0, 0, 0.125), APPLE, r=0.003, wobble=0)
COOKIE = C.empty("cookie")
slab("cookb", -0.062, 0.062, -0.062, 0.062, 0, 0.022, col((0.62, 0.40, 0.18), 0.7, 0.3), 0.011, 0.002, COOKIE)
crng = random.Random(4)
for i in range(9):
    a, d = crng.uniform(0, 6.28), crng.uniform(0, 0.05)
    C.ball(f"chip{i}", 0.009, col((0.06, 0.03, 0.02), 0.5), (d * math.cos(a), d * math.sin(a), 0.023), COOKIE, squash=(1, 1, 0.55), wobble=0)
CAN_AT = CAFE + Vector((0.92, -0.95, 0))
TR = C.empty("trashcan", CAN_AT)
for i in range(16):
    a = i * math.pi / 8
    C.soft(f"tr{i}", (0.15, 0.04, 0.72), col((0.20, 0.27, 0.30), 0.45), (0.3 * math.cos(a), 0.3 * math.sin(a), 0.36), TR, r=0.015, wobble=0.002, rot=(0, 0, a + math.pi / 2))
disc("trin", 0.27, 0.02, col((0.02, 0.02, 0.025)), (0, 0, 0.56), TR, upright=False)
for i, (x, y) in enumerate(((-0.1, 0.05), (0.09, -0.08), (0.03, 0.11))):
    C.ball(f"tb{i}", 0.05, col((0.75, 0.72, 0.66), 0.8), (x, y, 0.58), TR, wobble=0.012)

# ------------------------------------------------------------------ shots

cam = B.camera(lens=50, fstop=2.0)
cam.data.clip_start = 0.01
cam.data.clip_end = 60
BAG_AT = Vector((-0.02, -0.08, TOP))
BOARD_AT = Vector((-0.40, -0.10, TOP))
DUFFEL_AT = Vector((-0.75, -0.02, TOP))
PLATE_AT = Vector((0.55, -0.12, TOP))
TX0 = BAG_AT + Vector((0.0, -0.075, 0.15))

def lc(a, b, tg, lens, fstop, u):
    return Vector(a).lerp(Vector(b), smooth01(u)), Vector(tg), lens, fstop

def rel(p, *a):
    return p + Vector(a)

BC = BOARD_AT + Vector((0, 0, 0.05))
PC = PLATE_AT + Vector((0, 0, 0.05))
CAMS = {
    "open": lambda u: lc(rel(TX0, -0.24, -0.66, 0.07), rel(TX0, -0.14, -0.52, 0.03), TX0, 58, 2.4, u),
    "write": lambda u: lc(rel(TX0, 0.30, -0.62, 0.12), rel(TX0, 0.20, -0.50, 0.08), TX0, 58, 2.4, u),
    "wide": lambda u: lc((0.25, -5.0, 1.45), (0.1, -4.4, 1.40), (-0.25, 0, 1.28), 34, 4.0, u),
    "wide2": lambda u: lc((0.25, -5.0, 1.45), (0.1, -4.4, 1.40), (-0.25, 0, 1.28), 34, 4.0, u),
    "clock": lambda u: lc(rel(CLOCK, 0.2, -1.0, -0.06), rel(CLOCK, 0.1, -0.8, -0.03), CLOCK, 55, 2.8, u),
    "knife": lambda u: lc(rel(BC, -0.42, -0.52, 0.30), rel(BC, -0.30, -0.44, 0.24), BC, 55, 2.2, u),
    "crust": lambda u: lc(rel(BC, 0.30, -0.42, 0.11), rel(BC, 0.22, -0.32, 0.09), BC, 58, 2.0, u),
    "fridge": lambda u: lc(rel(FR, 0.28, -1.15, -0.06), rel(FR, 0.1, -0.80, -0.02), rel(FR, 0, 0, 0), 55, 2.6, u),
    "note": lambda u: lc(rel(BAG_AT, 0.24, -0.62, 0.46), rel(BAG_AT, 0.16, -0.50, 0.42), rel(BAG_AT, 0, 0, 0.28), 52, 2.8, u),
    "cafe": lambda u: lc(rel(CAFE, -0.42, -1.10, CT + 0.34), rel(CAFE, -0.2, -0.9, CT + 0.28), rel(CAFE, 0, 0, CT + 0.07), 50, 3.2, u),
    "trash": lambda u: lc(rel(CAN_AT, -0.5, -1.45, 1.05), rel(CAN_AT, -0.34, -1.25, 0.95), rel(CAN_AT, 0, 0, 0.56), 42, 4.0, u),
    "clock2": lambda u: lc(rel(CLOCK, -0.2, -1.0, -0.06), rel(CLOCK, -0.1, -0.8, -0.03), CLOCK, 55, 2.8, u),
    "plate": lambda u: lc(rel(PC, 0.40, -0.60, 0.34), rel(PC, 0.30, -0.50, 0.28), PC, 52, 2.4, u),
    "crust2": lambda u: lc(rel(PC, -0.30, -0.40, 0.12), rel(PC, -0.20, -0.30, 0.09), PC, 58, 2.0, u),
    "final": lambda u: lc(rel(PC, -0.05, -1.25, 0.52), rel(PC, -0.05, -0.95, 0.40), rel(PC, -0.1, 0, 0.07), 42, 2.6, u),
    "ending": lambda u: lc(rel(PC, 0.0, -0.16, 1.02), rel(PC, 0.0, -0.13, 0.90), rel(PC, 0.0, -0.02, -0.03), 42, 7.0, u),
}

ZOOM = {"open": 1.6, "write": 1.6, "knife": 1.5, "crust": 1.5, "fridge": 1.5, "note": 1.5, "clock": 1.7, "clock2": 1.7,
        "plate": 1.5, "crust2": 1.4, "cafe": 1.5}

def alt_cam(base, u):
    loc, tg, lens, fstop = base(u)
    return tg + (Matrix.Rotation(-0.55, 3, "Z") @ (loc - tg)) * 0.72, tg, lens, fstop

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
    return base_of(k), max(0.0, min(1.0, (t - t0) / max(1e-6, t2 - t0))), t - t0, cut, "~" in SHOTS[k][1]

def place(ob, p, rot=(0, 0, 0)):
    ob.location = p
    ob.rotation_euler = rot

def write_progress(tx, full, u, marker_at, size):
    """Show the first letters of `full` and put the marker's tip at the end of them, with a little scribble."""
    n = int(round(len(full) * max(0.0, min(1.0, u))))
    tx.data.body = full[:n] if n else " "
    x = marker_at + Vector((size * 0.56 * n, -0.012, size * 0.2 + size * 0.22 * math.sin(n * 2.1)))
    place(MARK, x, (math.radians(62), 0, math.radians(-14)))

def apply_state(t):
    name, u, age, cut, second = shot_at(t)
    q = math.floor(t * 12) / 12            # props step in stop motion
    uq = max(0.0, min(1.0, u - (t - q) / max(0.5, DUR)))
    loc, tg, lens, fstop = alt_cam(CAMS[name], cut) if second else CAMS[name](cut)
    loc = tg + (loc - tg) * ZOOM.get(name, 1.0) * (1.5 if second and name == "cafe" else 1.0)
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    cam.data.dof.focus_distance = (tg - loc).length
    cam.data.dof.aperture_fstop = fstop

    later = name in ("wide2", "clock2", "plate", "crust2", "final", "ending")
    # clock: 10:04, and in wide2 thirteen years rush through first
    spin = max(0.0, 1.0 - age / 1.1) ** 2 * 60.0 if name == "wide2" else 0.0
    H_M.rotation_euler = (0, math.radians(24) + spin * 2, 0)
    H_H.rotation_euler = (0, math.radians(302) + spin * 0.16, 0)

    # everything starts out of frame
    for o in (BOARD_R, SAND, SAND2, KNIFE, BAG, MARK, NOTEF, NOTE_R, BALLN, DUFFEL, PLATE, APPLE, COOKIE):
        o.location = AWAY

    if not later and name not in ("cafe", "trash"):
        place(BOARD_R, BOARD_AT)
        place(SAND, BOARD_AT + Vector((0, 0, 0.026)))
        place(BAG, BAG_AT)
        BAGFOLD.rotation_euler = (math.radians(2), 0, 0)
        BAGTX.data.body = "your name" if name in ("open", "note") else " "
        if name == "knife":
            for c in CRUSTS:
                c.location = c.location.normalized() * 0.091
            # the knife runs along one side, then the next, four strokes
            k = min(3, int(uq * 4))
            f = (uq * 4 - k)
            ang = k * math.pi / 2
            saw = 0.022 * math.sin(q * 26)
            p = Vector((-0.11 + saw + 0.22 * f * 0.3, -0.091, 0.06))
            place(KNIFE, BOARD_AT + Vector((0, 0, 0.026)) + Matrix.Rotation(ang, 3, "Z") @ p, (0, 0, ang))
        elif name == "crust":
            for i, c in enumerate(CRUSTS):
                f = smooth01((uq - 0.1 - i * 0.2) / 0.2)
                d = Vector(((0, -1), (1, 0), (0, 1), (-1, 0))[i] + (0,))
                c.location = d * (0.091 + f * 0.07)
                c.rotation_euler = (0, 0, f * 0.35 * (1 if i % 2 else -1))
            place(KNIFE, BOARD_AT + Vector((-0.11, 0.24, 0.026)), (0, 0, 0.3))
        else:
            for i, c in enumerate(CRUSTS):
                d = Vector(((0, -1), (1, 0), (0, 1), (-1, 0))[i] + (0,))
                c.location = d * (0.161 if name in ("write", "note") else 0.091)
            place(KNIFE, BOARD_AT + Vector((-0.11, -0.2, 0.026)), (0, 0, 0.3))
        if name == "open":
            write_progress(BAGTX, "your name", uq * 1.25, BAG_AT + Vector((-0.092, -0.09, 0.13)), 0.040)
        if name == "write":
            write_progress(BAGTX, "your name", uq * 1.15, BAG_AT + Vector((-0.092, -0.09, 0.13)), 0.040)
        if name == "note":
            f = smooth01(uq / 0.65)
            BAGFOLD.rotation_euler = (math.radians(-120), 0, 0)      # folded open
            place(NOTEF, BAG_AT + Vector((0.0, 0.0, 0.56 - 0.34 * f)), (math.pi / 2, 0, 0))
    if name in ("cafe",):
        place(APPLE, CAFE + Vector((0.02 + 0.46 * smooth01((uq - 0.55) / 0.3), -0.1, CT)))
        slide = smooth01((uq - 0.62) / 0.28)
        place(COOKIE, CAFE + Vector((0.48 - 0.46 * slide, -0.22, CT)))
    if name == "trash":
        z = 1.42 - 0.95 * min(1.0, (uq / 0.5)) ** 2
        place(BALLN, CAN_AT + Vector((0, 0, max(0.62, z))), (uq * 6, uq * 4, 0))
    if later:
        place(DUFFEL, DUFFEL_AT)
        if name in ("plate", "crust2", "final"):
            place(PLATE, PLATE_AT)
            place(SAND2, PLATE_AT + Vector((0.0, 0.0, 0.017)))
            for i, c in enumerate(CRUSTS2):
                d = Vector(((0, -1), (1, 0), (0, 1), (-1, 0))[i] + (0,))
                c.location = d * 0.122
                c.rotation_euler = (0, 0, 0.25 * (1 if i % 2 else -1))
        if name == "ending":
            place(NOTE_R, PLATE_AT + Vector((0, -0.02, 0.008)), (0, 0, -0.04))

B.render_settings(FPS, samples=int(os.environ.get("LUNCH_SAMPLES", "20")), motion_blur=0.0, look="AgX - Punchy")
C.cpu_preview_quality()

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1) / FPS)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
