"""Pastel toy kit, "You Too": toy peg people (a rounded body, a ball head with a face, stubby arms) in bright pastel sets 10 m apart
along x. Shots, timed by render_youtoo.py: rest (a candlelit table, you and your date, the waiter's arm already lowering the pasta),
waiter (ENJOY YOUR MEAL bubble on events.enjoy), you (YOU TOO bubble on youtoo1), waiter~2 (he freezes, ON SHIFT sign on work),
napkin (the date writes, then the napkin drops into her purse), booth / booth~2 (cinema ticket booth, ENJOY THE SHOW, YOU TOO),
street (a man across the road waves, you wave back, a car pulls up behind him on uber), wedding (an arch, 2 YEARS LATER), officiant,
groom (YOU TOO again), bride (she pulls out the napkin), note (the napkin close up: HE'LL DO IT AT THE WEDDING).

blender -b --factory-startup -P youtoo_scene.py -- timing.json out_dir MODE   (MODE: "all" or 1-based frame list)
"""
import json, math, os, random, sys
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bkit as B

argv = sys.argv[sys.argv.index("--") + 1:]
TIMING, OUT, MODE = argv[0], argv[1], argv[2]
T = json.load(open(TIMING))
FPS, DUR, SHOTS, EV, FONT = T["fps"], T["duration"], T["shots"], T["events"], T["font"]
NF = int(round(DUR * FPS))
os.makedirs(OUT, exist_ok=True)
B.clear_scene()
scene = B.scene
AWAY = Vector((0, 0, -1.0e4))

def hexc(s):
    """sRGB hex to linear."""
    def lin(v):
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return tuple(lin(int(s[i:i + 2], 16) / 255) for i in (0, 2, 4))

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

def back_out(u):
    u = max(0.0, min(1.0, u)) - 1
    return 1 + 2.7 * u ** 3 + 1.7 * u ** 2

_mats = {}
def mat(color, rough=0.55):
    if (color, rough) not in _mats:
        _mats[(color, rough)] = B.material("m" + color, hexc(color), rough=rough)
    return _mats[(color, rough)]

def rbox(name, x0, x1, y0, y1, z0, z1, color, bev=0.012, off=Vector(), parent=None, rough=0.55):
    ob = B.mesh_from(name, B.box(x0 + off.x, x1 + off.x, y0 + off.y, y1 + off.y, z0 + off.z, z1 + off.z), [mat(color, rough)])
    if bev:
        B.bevel(ob, bev)
        B.smooth(ob)
    ob.parent = parent
    return ob

def cyl(name, r, z0, z1, x, y, color, off=Vector(), r2=None, seg=48, bev=0.0):
    ob = B.mesh_from(name, B.cyl_z(r, z0 + off.z, z1 + off.z, x + off.x, y + off.y, seg=seg, r2=r2), [mat(color)])
    if bev:
        B.bevel(ob, bev)
    B.smooth(ob)
    return ob

def ball(name, r, color, at, squash=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=at, segments=32, ring_count=16)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = squash
    ob.data.materials.append(mat(color))
    ob.data.shade_smooth()
    return ob

_font = bpy.data.fonts.load(FONT)

def text(name, body, size, color, at, parent=None, glow=1.0):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body, cu.font, cu.size = body, _font, size
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.resolution_u = 4
    ob = B.link(bpy.data.objects.new(name, cu))
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = (*hexc(color), 1)
    e.inputs[1].default_value = glow
    nt.links.new(e.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs[0])
    ob.data.materials.append(m)
    ob.parent = parent
    ob.location = at
    ob.rotation_euler = (math.pi / 2, 0, 0)
    return ob

def sign(name, at, head, big, foot, w=0.46, h=0.27):
    """A dark rounded board on the wall: a small head, a big number, a small foot."""
    root = B.link(bpy.data.objects.new(name, None))
    root.location = at
    rbox(name + "p", -w / 2, w / 2, -0.012, 0.012, -h / 2, h / 2, "2F3843", parent=root, rough=0.5)
    rbox(name + "r", -w / 2 + 0.012, w / 2 - 0.012, -0.0145, -0.0125, h / 2 - 0.018, h / 2 - 0.012, "9FC3DD", bev=0, parent=root)
    tx = {"head": text(name + "h", head, 0.032, "F4F1E8", (0, -0.016, h * 0.3), root),
          "big": text(name + "b", big, 0.085, "FFFFFF", (0, -0.016, -0.012), root, glow=1.1),
          "foot": text(name + "f", foot, 0.028, "F4F1E8", (0, -0.016, -h * 0.34), root)}
    for ob in tx.values():
        ob.data.size = min(ob.data.size, (w - 0.05) / (max(1, len(ob.data.body)) * 0.58))
    return root, tx

def room(i, wall, floor, counter=None, top="F1ECE5"):
    """Floor, back wall at y=0.32, and an optional counter (front at y=-0.3, top at z=0.9)."""
    o = Vector((i * 10.0, 0, 0))
    rbox(f"floor{i}", -3, 3, -4, 0.32, -0.05, 0, floor, bev=0, off=o)
    rbox(f"wall{i}", -3, 3, 0.32, 0.4, 0, 3, wall, bev=0, off=o)
    if counter:
        rbox(f"ctr{i}", -0.7, 0.7, -0.3, 0.3, 0, 0.86, counter, off=o)
        rbox(f"top{i}", -0.72, 0.72, -0.32, 0.31, 0.86, 0.9, top, bev=0.008, off=o, rough=0.35)
    return o

def wall_disc(name, r, color, at, depth=0.025):
    ob = cyl(name, r, 0, depth, 0, 0, color, seg=64)
    ob.rotation_euler = (math.pi / 2, 0, 0)
    ob.location = at
    return ob


INKC, BLUSH, SKIN = "2F3843", "F29C9C", "F3C9A5"
YOU_C, DATE_C = "EE6F52", "7FA7D6"

def torus(name, R, r, at, rot, color):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=at, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(mat(color))
    ob.data.shade_smooth()
    return ob

def empty(name, at=Vector(), parent=None):
    e = B.link(bpy.data.objects.new(name, None))
    e.location = at
    e.parent = parent
    return e

def peg(name, color, at, hair=None, long_hair=False, bow=None, veil=False):
    """A toy peg person standing at `at`, facing -y: rounded body, ball head with a face, two arms on shoulder pivots."""
    root = empty(name, at)
    def p(ob):
        ob.parent = root
        return ob
    p(cyl(name + "b", 0.07, 0, 0.2, 0, 0, color, bev=0.03))
    p(ball(name + "h", 0.065, SKIN, (0, 0, 0.268)))
    for s in (-1, 1):
        p(ball(f"{name}e{s}", 0.0085, INKC, (s * 0.022, -0.06, 0.278)))
        p(ball(f"{name}k{s}", 0.011, BLUSH, (s * 0.037, -0.052, 0.258), (1, 0.4, 0.7)))
    p(rbox(name + "m", -0.011, 0.011, -0.066, -0.06, 0.244, 0.249, "C0566A", bev=0.002))
    if hair:
        p(ball(name + "hr", 0.068, hair, (0, 0.012, 0.29), (1.02, 1.0, 0.72)))
        if long_hair:
            p(ball(name + "hl", 0.064, hair, (0, 0.03, 0.22), (1.05, 0.8, 1.3)))
    if bow:
        for s in (-1, 1):
            p(ball(f"{name}w{s}", 0.014, bow, (s * 0.014, -0.068, 0.19), (1, 0.5, 0.75)))
    if veil:
        p(ball(name + "v", 0.075, "FFFFFF", (0, 0.03, 0.27), (1.05, 0.9, 1.35)))
        p(ball(name + "fl", 0.016, "F2A7B5", (0.04, -0.01, 0.33)))
    arms = []
    for s in (-1, 1):
        pv = empty(f"{name}a{s}", Vector((s * 0.072, 0, 0.17)), root)
        rbox(f"{name}ab{s}", -0.014, 0.014, -0.014, 0.014, -0.09, 0.0, color, bev=0.008, parent=pv)
        h = ball(f"{name}ah{s}", 0.017, SKIN, (0, 0, -0.095))
        h.parent = pv
        arms.append(pv)
    return root, arms

def bubble(name, at, body, w=0.3, h=0.09):
    """A white speech bubble with dark text, facing -y."""
    root = empty(name, at)
    rbox(name + "p", -w / 2, w / 2, -0.01, 0.01, -h / 2, h / 2, "FFFFFF", bev=0.02, parent=root, rough=0.4)
    tail = rbox(name + "t", -0.018, 0.018, -0.008, 0.008, -0.018, 0.018, "FFFFFF", bev=0.004, parent=root)
    tail.location = (-w * 0.2, 0, -h / 2 - 0.006)
    tail.rotation_euler = (0, math.pi / 4, 0)
    tx = text(name + "x", body, 0.05, INKC, (0, -0.013, -0.002), root, glow=0.4)
    tx.data.size = min(0.05, (w - 0.04) / (max(1, len(body)) * 0.6))
    return root

def glow_mat(name, color, strength):
    m = B.material(name, hexc(color), rough=0.5)
    B.set_emit(m, strength, hexc(color))
    return m

def pop(ob, age, s=1.0):
    k = 0.0 if age <= 0 else back_out(age / 0.25)
    ob.scale = (max(0.001, k * s),) * 3

def hide(*obs):
    for ob in obs:
        ob.scale = (0.001,) * 3

# ------------------------------------------------------------------ 0 restaurant

O0 = room(0, "F2C6C2", "B98A6A")
rbox("tcloth", -0.3, 0.3, -0.18, 0.18, 0.135, 0.16, "F7F4EE", bev=0.01, off=O0)
for sx in (-1, 1):
    for sy in (-1, 1):
        rbox(f"tleg{sx}{sy}", sx * 0.25 - 0.015, sx * 0.25 + 0.015, sy * 0.13 - 0.015, sy * 0.13 + 0.015, 0, 0.135, "D79A5F",
             bev=0, off=O0)
FLAME = glow_mat("flame", "FFC24A", 6.0)
for k, x in enumerate((-0.06, 0.06)):
    cyl(f"cand{k}", 0.012, 0.16, 0.22, x, 0.08, "FBFAF6", off=O0)
    fl = ball(f"flame{k}", 0.009, "FFC24A", O0 + Vector((x, 0.08, 0.232)), (1, 1, 1.7))
    fl.data.materials[0] = FLAME
cyl("dplate", 0.05, 0.16, 0.168, 0.18, -0.05, "FFFFFF", off=O0, bev=0.003)
YOU0, YOU0_ARMS = peg("you0", YOU_C, O0 + Vector((-0.38, -0.02, 0)), hair="6B4A3A")
DATE0, DATE0_ARMS = peg("date0", DATE_C, O0 + Vector((0.38, -0.02, 0)), hair="3A2A22", long_hair=True)
WAIT0, WAIT0_ARMS = peg("wait0", INKC, O0 + Vector((0.0, 0.22, 0)), hair="1E1E24", bow="FFFFFF")
PLATE = empty("plate")
cyl("pl", 0.055, 0, 0.008, 0, 0, "FFFFFF", bev=0.003).parent = PLATE
for nm, r, col, z, sq in (("pasta", 0.035, "F6C945", 0.015, (1, 1, 0.5)), ("sauce", 0.016, "D2483A", 0.032, (1, 1, 0.5))):
    ball(nm, r, col, (0, 0, z), sq).parent = PLATE
NAPKIN = rbox("napkin", -0.035, 0.035, -0.035, 0.035, 0, 0.004, "FFFFFF", bev=0.002)
PEN = cyl("pen", 0.004, 0, 0.07, 0, 0, INKC)
PURSE = empty("purse", O0 + Vector((0.56, -0.08, 0)))
rbox("pursb", -0.06, 0.06, -0.03, 0.03, 0, 0.08, "F2A7B5", bev=0.015, parent=PURSE)
torus("pursh", 0.035, 0.006, PURSE.location + Vector((0, 0, 0.085)), (math.pi / 2, 0, 0), "D2483A")
wall_disc("pic", 0.16, "F6C945", O0 + Vector((-0.45, 0.31, 0.75)))
wall_disc("pic2", 0.12, "83A392", O0 + Vector((-0.45, 0.29, 0.75)))
for k, x in enumerate((-0.9, 0.9)):
    wall_disc(f"lamp0{k}", 0.07, "F6C945", O0 + Vector((x, 0.3, 0.9)))
B_ENJOY = bubble("b_enjoy", O0 + Vector((0.05, 0.15, 0.47)), "ENJOY YOUR MEAL", w=0.34)
B_YT1 = bubble("b_yt1", O0 + Vector((-0.32, -0.03, 0.44)), "YOU TOO", w=0.22)
S_SHIFT, _ = sign("s_shift", O0 + Vector((0.42, 0.3, 0.62)), "WAITER", "ON SHIFT", "NOT EATING", w=0.34, h=0.2)

# ------------------------------------------------------------------ 1 cinema ticket booth

O1 = room(1, "BFE3EC", "E9E1D6")
rbox("booth", -0.3, 0.3, -0.12, 0.15, 0, 0.22, "EE6F52", bev=0.015, off=O1)
for x in (-0.29, 0.29):
    rbox(f"bpost{x}", x - 0.018, x + 0.018, -0.12, -0.09, 0.22, 0.5, "F6C945", bev=0.006, off=O1)
rbox("broof", -0.34, 0.34, -0.16, 0.17, 0.5, 0.56, "F6C945", bev=0.015, off=O1)
rbox("bslot", -0.08, 0.08, -0.127, -0.12, 0.17, 0.2, INKC, bev=0, off=O1)
TICK, TICK_ARMS = peg("tick", "D2483A", O1 + Vector((0.0, 0.02, 0.08)), hair="F6C945")
YOU1, YOU1_ARMS = peg("you1", YOU_C, O1 + Vector((-0.4, -0.35, 0)), hair="6B4A3A")
sign("s_movie", O1 + Vector((0.0, 0.3, 0.73)), "NOW SHOWING", "THE MOVIE", "7:30 PM", w=0.46, h=0.24)
for k, x in enumerate((-0.75, 0.75)):
    rbox(f"poster{k}", x - 0.15, x + 0.15, 0.29, 0.31, 0.35, 0.8, ("F6C945", "E7D5F0")[k], bev=0.01, off=O1)
B_SHOW = bubble("b_show", O1 + Vector((0.0, -0.08, 0.6)), "ENJOY THE SHOW", w=0.34)
B_YT2 = bubble("b_yt2", O1 + Vector((-0.3, -0.36, 0.46)), "YOU TOO", w=0.22)
S_WORKS, _ = sign("s_works", O1 + Vector((0.55, 0.28, 0.45)), "TICKET GUY", "WORKS HERE", "NOT COMING IN", w=0.36, h=0.22)

# ------------------------------------------------------------------ 2 street

O2 = room(2, "D9E6F5", "8E959D")
rbox("walkf", -3, 3, -1.0, -0.48, 0, 0.025, "E9E1D6", bev=0, off=O2)
rbox("walkb", -3, 3, -0.02, 0.32, 0, 0.025, "E9E1D6", bev=0, off=O2)
for k in range(-6, 7):
    rbox(f"dash{k}", k * 0.4 - 0.1, k * 0.4 + 0.1, -0.27, -0.23, 0, 0.004, "FFFFFF", bev=0, off=O2)
for k, (x, wd, ht, col) in enumerate(((-1.0, 0.5, 1.3, "F2A7B5"), (-0.4, 0.55, 1.0, "F6D8B8"), (0.25, 0.55, 1.45, "BFE3EC"),
                                      (0.9, 0.5, 1.15, "E7D5F0"))):
    rbox(f"bld{k}", x - wd / 2, x + wd / 2, 0.25, 0.3, 0, ht, col, bev=0.01, off=O2)
    for r in range(3):
        for c in range(2):
            rbox(f"win{k}{r}{c}", x - 0.12 + c * 0.16, x - 0.04 + c * 0.16, 0.24, 0.25, ht - 0.3 - r * 0.3, ht - 0.18 - r * 0.3,
                 "FFFFFF", bev=0, off=O2)
YOU2, YOU2_ARMS = peg("you2", YOU_C, O2 + Vector((-0.3, -0.68, 0.025)), hair="6B4A3A")
MAN2, MAN2_ARMS = peg("man2", "83A392", O2 + Vector((0.3, 0.08, 0.025)), hair="F6C945")
CAR = empty("car")
rbox("carb", -0.2, 0.2, -0.09, 0.09, 0.04, 0.14, INKC, bev=0.03, parent=CAR, rough=0.3)
rbox("carc", -0.11, 0.1, -0.08, 0.08, 0.14, 0.22, INKC, bev=0.03, parent=CAR, rough=0.3)
rbox("carw", -0.1, 0.09, -0.083, 0.083, 0.15, 0.205, "9FC3DD", bev=0.02, parent=CAR, rough=0.2)
for sx in (-1, 1):
    for sy in (-1, 1):
        wh = cyl(f"wheel{sx}{sy}", 0.045, -0.02, 0.02, 0, 0, "1E1E24", seg=32)
        wh.rotation_euler = (math.pi / 2, 0, 0)
        wh.location = (sx * 0.13, sy * 0.085, 0.045)
        wh.parent = CAR
S_RIDE = bubble("s_ride", Vector(), "HIS RIDE", w=0.2)
S_RIDE.parent = CAR
S_RIDE.location = (0, 0, 0.32)

# ------------------------------------------------------------------ 3 wedding

O3 = room(3, "F7E1EA", "E9E1D6")
for x in (-0.36, 0.36):
    cyl(f"apost{x}", 0.025, 0, 0.55, x, 0.15, "FFFFFF", off=O3)
torus("arch", 0.36, 0.025, O3 + Vector((0, 0.15, 0.55)), (math.pi / 2, 0, 0), "FFFFFF")
FLOWER = ("F2A7B5", "F6C945", "FFFFFF", "EE6F52")
for k in range(13):
    a = math.pi * k / 12
    ball(f"fl{k}", 0.03, FLOWER[k % 4], O3 + Vector((0.36 * math.cos(a), 0.12, 0.55 + 0.36 * math.sin(a))))
OFF3, _ = peg("off3", "8E7CC3", O3 + Vector((0.0, 0.18, 0)), hair="B8C0C8")
rbox("lect", -0.07, 0.07, 0.03, 0.1, 0, 0.16, "D79A5F", bev=0.01, off=O3)
YOU3, YOU3_ARMS = peg("you3", YOU_C, O3 + Vector((-0.2, -0.04, 0)), hair="6B4A3A", bow=INKC)
BRIDE3, BRIDE3_ARMS = peg("bride3", "FBFAF6", O3 + Vector((0.2, -0.04, 0)), hair="3A2A22", long_hair=True, veil=True)
for k, (x, y, col, hr) in enumerate(((-0.8, -0.2, "F6C945", "6B4A3A"), (-1.0, -0.4, "83A392", "1E1E24"),
                                     (0.8, -0.2, "9FC3DD", "F6C945"), (1.0, -0.4, "F2A7B5", "3A2A22"))):
    peg(f"guest{k}", col, O3 + Vector((x, y, 0)), hair=hr)
S_LATER, _ = sign("s_later", O3 + Vector((-0.75, 0.3, 0.75)), "TWO YEARS", "LATER", "YOUR WEDDING", w=0.36, h=0.22)
B_KISS = bubble("b_kiss", O3 + Vector((0.04, 0.06, 0.47)), "YOU MAY KISS THE BRIDE", w=0.42)
B_YT3 = bubble("b_yt3", O3 + Vector((-0.15, -0.07, 0.44)), "YOU TOO", w=0.22)
HNAP = rbox("hnap", -0.03, 0.03, -0.004, 0.004, -0.03, 0.03, "FFFFFF", bev=0.002)
HNAP.parent = BRIDE3_ARMS[0]
HNAP.location = (0, -0.03, -0.12)

# ------------------------------------------------------------------ 4 the napkin, close up

O4 = Vector((40.0, 0, 0))
rbox("tbl4", -1, 1, -1, 1, -0.05, 0, "F7F4EE", bev=0, off=O4)
rbox("nap4", -0.2, 0.2, -0.2, 0.2, 0, 0.004, "FFFFFF", bev=0.003, off=O4)
rbox("fold4", -0.001, 0.001, -0.2, 0.2, 0.004, 0.0045, "E8E4DC", bev=0, off=O4)
NOTE = empty("note", O4 + Vector((0, 0, 0.006)))
for k, s in enumerate(("HE'LL DO IT", "AT THE", "WEDDING")):
    tx = text(f"note{k}", s, 0.06, "3B5BA5", (0, 0.07 - k * 0.075, 0), NOTE, glow=0.6)
    tx.rotation_euler = (0, 0, 0.04 * (k - 1))
torus("heart", 0.02, 0.004, O4 + Vector((0.13, -0.14, 0.006)), (0, 0, 0), "D2483A")
pen4 = cyl("pen4", 0.006, 0, 0.14, 0, 0, INKC)
pen4.location = O4 + Vector((0.24, -0.1, 0.008))
pen4.rotation_euler = (math.pi / 2, 0, 0.6)

# ------------------------------------------------------------------ light, world, camera

w = bpy.data.worlds.new("w")
scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (*hexc("E8EEF2"), 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.72
B.sun("key", -62, 56, 2.1, color=hexc("FFF4E4"), angle_deg=14)
cam = B.camera(lens=35, fstop=14.0)
cam.data.clip_start, cam.data.clip_end = 0.01, 200.0

def lc(a, b, tg, u, o, lens=35):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "rest": lambda u: lc((0.0, -1.35, 0.6), (0.0, -1.15, 0.55), (0.0, 0.0, 0.26), u, O0),
    "waiter": lambda u: lc((0.08, -0.85, 0.45), (0.04, -0.72, 0.43), (0.02, 0.15, 0.32), u, O0),
    "you": lambda u: lc((-0.42, -0.72, 0.38), (-0.4, -0.62, 0.37), (-0.36, 0.0, 0.32), u, O0),
    "waiter~2": lambda u: lc((0.12, -0.7, 0.42), (0.1, -0.62, 0.42), (0.1, 0.2, 0.38), u, O0),
    "napkin": lambda u: lc((0.42, -0.62, 0.42), (0.4, -0.55, 0.4), (0.38, -0.04, 0.22), u, O0),
    "booth": lambda u: lc((0.0, -1.45, 0.55), (-0.05, -1.3, 0.52), (-0.05, -0.1, 0.36), u, O1),
    "booth~2": lambda u: lc((-0.34, -1.3, 0.5), (-0.32, -1.2, 0.49), (-0.24, -0.1, 0.33), u, O1),
    "street": lambda u: lc((-0.05, -2.0, 0.62), (0.0, -1.85, 0.58), (0.05, -0.2, 0.27), u, O2),
    "wedding": lambda u: lc((0.0, -1.75, 0.62), (0.0, -1.55, 0.58), (0.0, 0.0, 0.4), u, O3),
    "officiant": lambda u: lc((0.03, -0.78, 0.44), (0.02, -0.68, 0.43), (0.0, 0.15, 0.37), u, O3),
    "groom": lambda u: lc((-0.2, -0.72, 0.38), (-0.2, -0.62, 0.37), (-0.18, 0.0, 0.33), u, O3),
    "bride": lambda u: lc((0.26, -0.7, 0.36), (0.24, -0.6, 0.35), (0.2, 0.0, 0.27), u, O3),
    "note": lambda u: lc((0.0, -0.32, 0.72), (0.0, -0.26, 0.62), (0.0, 0.0, 0.0), u, O4),
}

def shot_at(t):
    k = max([0] + [i for i, (s, _) in enumerate(SHOTS) if t >= s - 1e-6])
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    cut = max(0.0, min(1.0, (t - SHOTS[k][0]) / max(1e-6, t1 - SHOTS[k][0])))
    return SHOTS[k][1], cut

def start_of(n):
    return next(s for s, m in SHOTS if m == n)

def show_between(ob, t, t0, t1=1e9):
    if t0 <= t < t1:
        pop(ob, t - t0)
    else:
        hide(ob)

def wave(pv, t, t0, side):
    """Raise an arm from t0 and wave it."""
    u = smooth01((t - t0) / 0.3)
    pv.rotation_euler = (0, side * u * (2.5 + 0.35 * math.sin((t - t0) * 12)), 0)

def apply_state(t):
    name, cut = shot_at(t)
    loc, tg, lens = CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    cam.data.dof.use_dof = False

    # restaurant: the waiter's arm lowers the pasta from frame one and lands on events.plate
    u = smooth01((t + 0.3) / max(0.5, EV["plate"] + 0.3))
    WAIT0_ARMS[0].rotation_euler = (0, 1.3 + 0.8 * (1 - u), 0)
    PLATE.location = O0 + Vector((-0.17, 0.17, 0.27)).lerp(Vector((-0.18, -0.05, 0.168)), u)
    show_between(B_ENJOY, t, EV["enjoy"], start_of("you"))
    show_between(B_YT1, t, EV["youtoo1"], start_of("napkin"))
    show_between(S_SHIFT, t, EV["work"], start_of("booth"))
    WAIT0.rotation_euler = (0, 0, 0.0 if t >= start_of("waiter~2") else 0.04 * math.sin(t * 3))
    # the date writes on the napkin, then it drops into her purse
    nap0 = O0 + Vector((0.27, -0.09, 0.161))
    writing = EV["write"] < t < EV["purse"]
    if t < EV["purse"]:
        NAPKIN.location = nap0
        NAPKIN.scale = (1, 1, 1)
        DATE0_ARMS[0].rotation_euler = (0, 1.0 + (0.08 * math.sin(t * 18) if writing else 0), 0)
    else:
        v = smooth01((t - EV["purse"]) / 0.5)
        NAPKIN.location = nap0.lerp(PURSE.location + Vector((0, 0, 0.08)), v)
        NAPKIN.scale = (max(0.001, 1 - v),) * 3
        DATE0_ARMS[0].rotation_euler = (0, 1.0 * (1 - v), 0)
    PEN.location = O0 + Vector((0.3 + (0.01 * math.sin(t * 18) if writing else 0), -0.12, 0.165))
    PEN.rotation_euler = (0.9, 0, 0.5)

    # booth
    show_between(B_SHOW, t, EV["enjoy2"], start_of("street"))
    show_between(B_YT2, t, EV["youtoo2"], start_of("street"))
    show_between(S_WORKS, t, EV["youtoo2"] + 0.8, start_of("street"))
    TICK_ARMS[0].rotation_euler = (0, 0.5 if t >= EV["enjoy2"] else 0.0, 0)

    # street: he waves, you wave back, his car pulls up
    if t >= EV["manwave"]:
        wave(MAN2_ARMS[1], t, EV["manwave"], -1)
    if t >= EV["youwave"]:
        wave(YOU2_ARMS[1], t, EV["youwave"], -1)
    cu = smooth01((t - EV["uber"] + 0.9) / 0.9)
    CAR.location = O2 + Vector((2.2 - 1.6 * cu, -0.3, 0.0))
    show_between(S_RIDE, t, EV["uber"] + 0.1)

    # wedding
    show_between(S_LATER, t, start_of("wedding") + 0.15, start_of("officiant"))
    show_between(B_KISS, t, EV["kiss"], start_of("groom"))
    show_between(B_YT3, t, EV["youtoo3"], start_of("bride"))
    if t >= EV["pull"]:
        BRIDE3_ARMS[0].rotation_euler = (0, 1.4 * smooth01((t - EV["pull"]) / 0.4), 0)
        pop(HNAP, t - EV["pull"])
    else:
        BRIDE3_ARMS[0].rotation_euler = (0, 0, 0)
        hide(HNAP)

    # note: the writing appears as the narrator reads it
    show_between(NOTE, t, EV["reveal"] - 0.1)

B.render_settings(FPS, samples=int(os.environ.get("YT_SAMPLES", "24")), motion_blur=0.0)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1) / FPS)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
