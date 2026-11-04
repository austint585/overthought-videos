"""Pastel toy kit at night, "Second Sleep": toy peg people (from youtoo_scene.py) in a moonlit bedroom, a timber medieval room,
a night lane between two cottages and an open book of records. Shots, timed by render_sleep.py: phone (you in bed, the phone
glowing, u up? popping from frame one), door (it shakes on events.knock), neighbor (door open, a neighbour with a candle),
bed (he sits on your bed: HOW WAS THE HARVEST?), wife (soup), priest, goose (a man and a goose at the door), router (the goose
hops onto it), phone2 (I'M OUTSIDE), exdoor (your ex in the doorway with two neighbours), history (nightcaps, BEFORE ELECTRIC
LIGHT sign), wake (they sit up, AWAKE sign), visit (a lantern walks to the next cottage), book (FIRST SLEEP, SECOND SLEEP),
pile (everyone asleep, the goose first), phone3 (you, awake again, u up?).

blender -b --factory-startup -P sleep_scene.py -- timing.json out_dir MODE   (MODE: "all" or 1-based frame list)
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


def point(name, at, power, color, r=0.04, parent=None):
    ld = bpy.data.lights.new(name, "POINT")
    ld.energy, ld.color, ld.shadow_soft_size = power, hexc(color), r
    ob = B.link(bpy.data.objects.new(name, ld))
    ob.parent = parent
    ob.location = at
    return ob

def nightcap(root, color):
    ball(root.name + "nc", 0.069, color, (0, 0.01, 0.3), (1.02, 1.02, 0.85)).parent = root
    ball(root.name + "nt", 0.018, "FFFFFF", (0.05, 0.03, 0.37)).parent = root

FLAME = glow_mat("flame", "FFC24A", 6.0)

def candle(name, at, parent=None, light=1.5):
    c = cyl(name, 0.012, 0, 0.06, 0, 0, "FBFAF6")
    c.parent = parent
    c.location = at
    fl = ball(name + "f", 0.01, "FFC24A", Vector(at) + Vector((0, 0, 0.072)), (1, 1, 1.7))
    fl.data.materials[0] = FLAME
    fl.parent = parent
    point(name + "L", Vector(at) + Vector((0, -0.02, 0.1)), light, "FFB25A", parent=parent)
    return fl

def lie(root, at):
    root.location = at
    root.rotation_euler = (-math.pi / 2, 0, 0)

def stand(root, at, sway=0.0):
    root.location = at
    root.rotation_euler = (0, 0, sway)

# ------------------------------------------------------------------ 0 bedroom at night (door in the back wall, a lit hallway behind)

WALL0, FLOOR0 = "3D4A78", "8A6A55"
rbox("floor0", -3, 3, -4, 0.32, -0.05, 0, FLOOR0, bev=0)
rbox("wallL0", -3, 0.41, 0.32, 0.4, 0, 3, WALL0, bev=0)
rbox("wallR0", 0.69, 3, 0.32, 0.4, 0, 3, WALL0, bev=0)
rbox("wallT0", 0.41, 0.69, 0.32, 0.4, 0.46, 3, WALL0, bev=0)
rbox("hallf", 0.3, 0.8, 0.32, 1.0, -0.05, -0.001, "B98A6A", bev=0)
rbox("hallb", 0.3, 0.8, 1.0, 1.05, 0, 0.8, "F2C6C2", bev=0)
for x in (0.37, 0.73):
    rbox(f"halls{x}", x - 0.03, x + 0.03, 0.41, 1.0, 0, 0.8, "E8B9B3", bev=0)
point("hallL", Vector((0.55, 0.75, 0.42)), 3.0, "FFC98A", r=0.1)
for k, (x0, x1, z0, z1) in enumerate(((0.38, 0.41, 0, 0.49), (0.69, 0.72, 0, 0.49), (0.41, 0.69, 0.46, 0.49))):
    rbox(f"dframe{k}", x0, x1, 0.305, 0.325, z0, z1, "E9E1D6", bev=0.004)
DOOR = empty("door", Vector((0.415, 0.3, 0)))
rbox("doorp", 0, 0.27, -0.012, 0.012, 0.002, 0.455, "C98B5E", bev=0.006, parent=DOOR)
ball("knob", 0.012, "F6C945", (0.24, -0.02, 0.22)).parent = DOOR
# window with the moon
rbox("winf", -0.75, -0.35, 0.305, 0.325, 0.5, 0.86, "E9E1D6", bev=0.006)
WGL = rbox("wing", -0.73, -0.37, 0.298, 0.304, 0.52, 0.84, "26304F", bev=0)
WGL.data.materials[0] = glow_mat("night", "2A3766", 0.6)
MOON = wall_disc("moon", 0.05, "FFF3C4", Vector((-0.47, 0.297, 0.75)), depth=0.003)
MOON.data.materials[0] = glow_mat("moonm", "FFF3C4", 4.0)
STARM = glow_mat("starm", "FFFFFF", 4.0)
for k, (x, z) in enumerate(((-0.66, 0.8), (-0.6, 0.6), (-0.42, 0.58), (-0.68, 0.66))):
    ball(f"star{k}", 0.005, "FFFFFF", (x, 0.294, z)).data.materials[0] = STARM
rbox("winbar", -0.556, -0.544, 0.292, 0.298, 0.52, 0.84, "E9E1D6", bev=0)
# bed
rbox("bedf", -0.78, -0.12, -0.26, 0.3, 0, 0.08, "C98B5E", bev=0.01)
rbox("bedh", -0.78, -0.12, 0.25, 0.302, 0.08, 0.32, "C98B5E", bev=0.012)
rbox("matt", -0.77, -0.13, -0.25, 0.245, 0.08, 0.12, "F4EFE6", bev=0.012)
ball("pillow", 0.09, "FFFFFF", (-0.45, 0.19, 0.14), (1.5, 0.6, 0.35))
rbox("blank", -0.79, -0.11, -0.27, 0.06, 0.121, 0.145, "7FA7D6", bev=0.012)
rbox("nst", -0.09, 0.07, 0.1, 0.28, 0, 0.16, "D79A5F", bev=0.01)
LAMP = ball("lamp", 0.035, "FFE1A8", (-0.01, 0.2, 0.2))
LAMP.data.materials[0] = glow_mat("lampm", "FFD58A", 2.5)
point("lampL", Vector((-0.02, 0.1, 0.28)), 2.0, "FFC98A", r=0.06)
rbox("rug", -0.1, 0.9, -0.95, -0.25, 0.0005, 0.004, "E7D5F0", bev=0)
# router on a wall shelf
rbox("shelf", 0.82, 1.12, 0.18, 0.32, 0.2, 0.215, "D79A5F", bev=0.004)
rbox("router", 0.88, 1.06, 0.2, 0.3, 0.2155, 0.245, "F4F1E8", bev=0.006)
for x in (0.9, 1.04):
    cyl(f"ant{x}", 0.004, 0.245, 0.33, x, 0.29, "F4F1E8")
LEDM = glow_mat("ledm", "57E08A", 5.0)
for k in range(4):
    ball(f"led{k}", 0.004, "57E08A", (0.92 + k * 0.03, 0.199, 0.232)).data.materials[0] = LEDM

YOU, YOU_ARMS = peg("you", "EE6F52", Vector((-0.45, 0.06, 0.1)), hair="6B4A3A")
PHONE = empty("phone")
rbox("phb", -0.02, 0.02, -0.004, 0.004, -0.035, 0.035, "1E1E24", bev=0.003, parent=PHONE)
scr = rbox("phs", -0.017, 0.017, 0.0042, 0.0048, -0.031, 0.031, "BFE6FF", bev=0, parent=PHONE)
scr.data.materials[0] = glow_mat("scrm", "BFE6FF", 3.0)
PHL = point("phoneL", Vector((0, 0.03, 0.01)), 0.4, "BFE6FF", r=0.02, parent=PHONE)

NEI, NEI_A = peg("nei", "83A392", AWAY, hair="B8C0C8")
candle("ncand", Vector((0.06, -0.1, 0.16)), NEI, light=1.2)
WIFE, WIFE_A = peg("wife", "F2A7B5", AWAY, hair="6B4A3A", long_hair=True)
cyl("bowl", 0.04, 0.17, 0.2, 0, -0.1, "FFFFFF", r2=0.03).parent = WIFE
ball("soup", 0.036, "E58A3A", (0, -0.1, 0.198), (1, 1, 0.15)).parent = WIFE
PRIEST, PRIEST_A = peg("priest", "26262E", AWAY, hair="B8C0C8")
rbox("collar", -0.015, 0.015, -0.074, -0.068, 0.17, 0.19, "FFFFFF", bev=0, parent=PRIEST)
GMAN, GMAN_A = peg("gman", "C98B5E", AWAY, hair="3A2A22")
EX, EX_A = peg("ex", "7FA7D6", AWAY, hair="3A2A22", long_hair=True)
EXN1, _ = peg("exn1", "F6C945", AWAY, hair="1E1E24")
EXN2, _ = peg("exn2", "E7D5F0", AWAY, hair="F6C945", long_hair=True)
for pv in NEI_A[1:] + WIFE_A:
    pv.rotation_euler = (-1.4, 0, 0)
PRIEST_A[0].rotation_euler = (-1.2, 0, 0.3)

GOOSE = empty("goose", AWAY)
ball("gbody", 0.045, "FFFFFF", (0, 0, 0.045), (1.0, 1.35, 0.85)).parent = GOOSE
ball("gtail", 0.02, "F1ECE5", (0, 0.06, 0.06)).parent = GOOSE
GNECK = empty("gneck", Vector((0, -0.04, 0.06)), GOOSE)
cyl("gn", 0.011, 0, 0.07, 0, 0, "FFFFFF").parent = GNECK
ball("gh", 0.02, "FFFFFF", (0, -0.005, 0.078)).parent = GNECK
rbox("gbeak", -0.008, 0.008, -0.045, -0.018, 0.07, 0.08, "F59A3A", bev=0.003, parent=GNECK)
for s in (-1, 1):
    ball(f"geye{s}", 0.004, INKC, (s * 0.012, -0.018, 0.085)).parent = GNECK
    rbox(f"gleg{s}", s * 0.02 - 0.004, s * 0.02 + 0.004, -0.004, 0.004, 0.0, 0.012, "F59A3A", bev=0, parent=GOOSE)

B_UP = bubble("b_up", Vector((-0.45, -0.02, 0.5)), "u up?", w=0.17)
B_HARV = bubble("b_harv", Vector((-0.3, -0.16, 0.48)), "HOW WAS THE HARVEST?", w=0.42)
B_OUT = bubble("b_out", Vector((-0.45, -0.02, 0.5)), "I'M OUTSIDE", w=0.38, h=0.1)
B_UP2 = bubble("b_up2", Vector((-0.45, -0.02, 0.5)), "u up?", w=0.17)

# ------------------------------------------------------------------ 1 medieval room

O1 = room(1, "D9B98F", "8A6A55")
for k, x in enumerate((-1.1, -0.55, 0.55, 1.1)):
    rbox(f"beam{k}", x - 0.03, x + 0.03, 0.29, 0.318, 0, 1.4, "6B4A3A", bev=0.004, off=O1)
rbox("beamh", -3, 3, 0.29, 0.318, 0.98, 1.04, "6B4A3A", bev=0.004, off=O1)
rbox("straw", -0.45, 0.45, -0.2, 0.28, 0, 0.09, "E3C77A", bev=0.02, off=O1)
rbox("quilt", -0.46, 0.46, -0.21, 0.04, 0.091, 0.11, "B8574A", bev=0.012, off=O1)
rbox("stool", 0.55, 0.75, -0.05, 0.12, 0, 0.12, "8A5A3A", bev=0.01, off=O1)
candle("mcand", O1 + Vector((0.65, 0.03, 0.12)), light=2.5)
rbox("mwin", -0.9, -0.66, 0.296, 0.306, 0.45, 0.72, "2A3766", bev=0, off=O1).data.materials[0] = glow_mat("night2", "2A3766", 0.6)
MM = wall_disc("mmoon", 0.04, "FFF3C4", O1 + Vector((-0.78, 0.294, 0.62)), depth=0.002)
MM.data.materials[0] = glow_mat("moonm2", "FFF3C4", 4.0)
MAN1, _ = peg("man1", "8E7CC3", AWAY)
WOM1, _ = peg("wom1", "83A392", AWAY, hair="6B4A3A", long_hair=True)
nightcap(MAN1, "F4F1E8")
nightcap(WOM1, "F2A7B5")
S_SHIFT, _ = sign("s_shift", O1 + Vector((0.0, 0.28, 0.62)), "BEFORE ELECTRIC LIGHT", "2 SHIFTS", "OF SLEEP", w=0.7, h=0.36)
S_AWAKE, _ = sign("s_awake", O1 + Vector((0.0, 0.27, 0.62)), "AWAKE FOR", "1 TO 2 HRS", "IN THE NIGHT", w=0.7, h=0.36)

# ------------------------------------------------------------------ 2 night lane between two cottages

O2 = Vector((20.0, 0, 0))
rbox("grass2", -3, 3, -3, 2, -0.05, 0, "4F6B55", bev=0, off=O2)
rbox("lane2", -1.2, 1.2, 0.02, 0.24, 0.0005, 0.004, "B8A58A", bev=0, off=O2)
rbox("sky2", -4, 4, 2.0, 2.05, 0, 4, "1C2440", bev=0, off=O2).data.materials[0] = glow_mat("skym", "222C52", 0.5)
wall_disc("moon2", 0.12, "FFF3C4", O2 + Vector((0.9, 1.995, 1.25)), depth=0.003).data.materials[0] = glow_mat("moonm3", "FFF3C4", 4.0)
rnd = random.Random(4)
for k in range(30):
    ball(f"st2{k}", 0.008, "FFFFFF", O2 + Vector((rnd.uniform(-2, 2), 1.99, rnd.uniform(0.7, 2.0)))).data.materials[0] = STARM
WINB = []
for k, x in enumerate((-0.6, 0.6)):
    rbox(f"cot{k}", x - 0.25, x + 0.25, 0.3, 0.7, 0, 0.35, ("E9E1D6", "F6D8B8")[k], bev=0.01, off=O2)
    roof = rbox(f"roof{k}", -0.2, 0.2, -0.22, 0.22, -0.2, 0.2, "8A4B3A", bev=0.01)
    roof.location = O2 + Vector((x, 0.5, 0.35))
    roof.rotation_euler = (0, math.pi / 4, 0)
    rbox(f"cdoor{k}", x - 0.06, x + 0.06, 0.286, 0.3, 0, 0.2, "6B4A3A", bev=0.004, off=O2)
    wm = glow_mat(f"cwinm{k}", "FFD58A", 2.0 if k == 0 else 0.15)
    rbox(f"cwin{k}", x + 0.1, x + 0.2, 0.286, 0.3, 0.17, 0.27, "FFD58A", bev=0, off=O2).data.materials[0] = wm
    WINB.append(wm)
for k, x in enumerate((-1.4, 1.5, -1.9)):
    cyl(f"tree{k}", 0.16, 0.12, 0.6, x, 0.9, "3E5A48", off=O2, r2=0.0, seg=10)
    cyl(f"trk{k}", 0.03, 0, 0.12, x, 0.9, "6B4A3A", off=O2)
VIS, VIS_A = peg("vis", "D2483A", AWAY)
nightcap(VIS, "F4F1E8")
VIS_A[1].rotation_euler = (-0.6, 0, 0)
lan = ball("lantern", 0.018, "FFD58A", (0.08, -0.06, 0.09))
lan.data.materials[0] = glow_mat("lanm", "FFD58A", 5.0)
lan.parent = VIS
point("lanL", Vector((0.08, -0.1, 0.14)), 1.5, "FFB25A", parent=VIS)

# ------------------------------------------------------------------ 3 the book of records by candlelight

O3 = Vector((30.0, 0, 0))
rbox("tbl3", -1, 1, -1, 1, -0.05, 0, "8A5A3A", bev=0, off=O3)
rbox("cover3", -0.34, 0.34, -0.23, 0.23, 0, 0.012, "6B3A2E", bev=0.004, off=O3)
for s in (-1, 1):
    pg = rbox(f"page{s}", -0.155, 0.155, -0.21, 0.21, 0, 0.01, "F4EBD6", bev=0.004)
    pg.location = O3 + Vector((s * 0.163, 0, 0.012))
    for r in range(9):
        if r in (1, 2, 3):
            continue
        ln = rbox(f"ln{s}{r}", -0.12, 0.12 - 0.05 * (r % 3 == 2), -0.003, 0.003, 0, 0.0015, "B9A88A", bev=0)
        ln.location = O3 + Vector((s * 0.163, 0.17 - r * 0.042, 0.0225))
BOOK_T = {}
for s, key, body in ((-1, "first", "FIRST SLEEP"), (1, "second", "SECOND SLEEP")):
    tx = text(f"bk{key}", body, 0.04, "6B3A2E", O3 + Vector((s * 0.163, 0.085, 0.0235)), glow=0.5)
    tx.rotation_euler = (0, 0, 0)
    tx.data.size = min(0.04, 0.27 / (len(body) * 0.6))
    BOOK_T[key] = tx
candle("bcand", O3 + Vector((0.45, 0.2, 0.0)), light=2.0)
rbox("quill", -0.004, 0.004, -0.12, 0.0, 0, 0.004, "F4F1E8", bev=0, off=O3 + Vector((0.42, -0.12, 0.0)))

ZZZ_AT = [("goose", Vector((0.97, 0.22, 0.4)))]
for k in range(6):
    ZZZ_AT.append((f"r{k}", Vector((-0.12 + k * 0.17, -0.62, 0.2))))
ZZZ_AT.append(("nei", Vector((-0.3, 0.0, 0.32))))
ZZZ_AT.append(("you", Vector((-0.5, 0.05, 0.36))))
ZZZ = {key: text("zzz" + key, "z z Z", 0.05, "FFFFFF", at, glow=1.5) for key, at in ZZZ_AT}

# ------------------------------------------------------------------ light, world, camera

w = bpy.data.worlds.new("w")
scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (*hexc("2A355C"), 1)
w.node_tree.nodes["Background"].inputs[1].default_value = float(os.environ.get("SL_WORLD", "0.55"))
B.sun("moonsun", -120, 40, float(os.environ.get("SL_MOON", "1.1")), color=hexc("C9D6FF"), angle_deg=10)
for k, o in enumerate((Vector(), O1, O2, O3)):
    B.area(f"fill{k}", o + Vector((0.3, -2.0, 1.4)), o + Vector((0.1, 0, 0.25)), 2.5, float(os.environ.get("SL_FILL", "30")),
           color=hexc("D6DEFF"))
cam = B.camera(lens=35, fstop=14.0)
cam.data.clip_start, cam.data.clip_end = 0.01, 200.0
O0 = Vector()

def lc(a, b, tg, u, o, lens=35):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

PHONE_CAM = lambda u: lc((-0.42, -0.6, 0.4), (-0.43, -0.5, 0.38), (-0.44, 0.05, 0.33), u, O0)
CAMS = {
    "phone": PHONE_CAM, "phone2": PHONE_CAM, "phone3": PHONE_CAM,
    "door": lambda u: lc((0.5, -0.8, 0.34), (0.52, -0.7, 0.33), (0.55, 0.3, 0.24), u, O0),
    "neighbor": lambda u: lc((0.5, -0.62, 0.34), (0.52, -0.54, 0.33), (0.55, 0.3, 0.26), u, O0),
    "bed": lambda u: lc((-0.2, -0.95, 0.45), (-0.22, -0.85, 0.43), (-0.3, 0.0, 0.26), u, O0),
    "wife": lambda u: lc((0.15, -1.15, 0.5), (0.18, -1.05, 0.48), (0.15, 0.05, 0.25), u, O0),
    "priest": lambda u: lc((0.35, -0.95, 0.45), (0.37, -0.85, 0.44), (0.4, 0.1, 0.25), u, O0),
    "goose": lambda u: lc((0.58, -0.75, 0.32), (0.6, -0.65, 0.31), (0.62, 0.25, 0.2), u, O0),
    "router": lambda u: lc((0.9, -0.3, 0.32), (0.92, -0.24, 0.31), (0.96, 0.23, 0.25), u, O0),
    "exdoor": lambda u: lc((0.55, -0.62, 0.36), (0.56, -0.54, 0.35), (0.56, 0.45, 0.27), u, O0),
    "pile": lambda u: lc((0.05, -1.75, 1.0), (0.08, -1.6, 0.92), (0.12, -0.25, 0.1), u, O0),
    "history": lambda u: lc((0.0, -1.3, 0.6), (0.0, -1.15, 0.56), (0.0, 0.1, 0.38), u, O1),
    "wake": lambda u: lc((0.05, -1.25, 0.5), (0.04, -1.12, 0.48), (0.0, 0.1, 0.36), u, O1),
    "visit": lambda u: lc((-0.1, -2.9, 0.75), (0.1, -2.75, 0.72), (0.0, 0.3, 0.3), u, O2),
    "book": lambda u: lc((0.0, -0.5, 1.3), (0.0, -0.44, 1.18), (0.0, 0.0, 0.0), u, O3),
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

DOORWAY = Vector((0.55, 0.42, 0))

def walk(root, t, t0, a, b, dur=0.8, appear=None, phase=0.0):
    """Hidden before `appear` (default t0), standing at a until t0, then a hop-walk to b."""
    if t < (t0 if appear is None else appear):
        root.location = AWAY
        return
    u = max(0.0, min(1.0, (t - t0) / dur))
    p = Vector(a).lerp(Vector(b), smooth01(u))
    if 0 < u < 1:
        p.z += 0.025 * abs(math.sin(u * math.pi * 4))
    root.location = p
    root.rotation_euler = (0, 0, 0.05 * math.sin(t * 2.3 + phase))

def apply_state(t):
    name, cut = shot_at(t)
    loc, tg, lens = CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    cam.data.dof.use_dof = False
    T_PILE, T_P3 = start_of("pile"), start_of("phone3")

    # door: shakes on the knock, swings open into the room on events.open
    if t < EV["open"]:
        k = t - EV["knock"]
        DOOR.rotation_euler = (0, 0, -0.05 * abs(math.sin(k * 15.7)) if 0 <= k < 0.65 else 0)
    else:
        DOOR.rotation_euler = (0, 0, -1.75 * smooth01((t - EV["open"] + 0.1) / 0.45))

    # you, in bed with the phone (asleep in the pile shot, back up for phone3)
    if T_PILE <= t < T_P3:
        lie(YOU, Vector((-0.5, -0.12, 0.14)))
        for pv in YOU_ARMS:
            pv.rotation_euler = (0, 0, 0)
        PHONE.location = Vector((-0.22, 0.15, 0.125))
        PHONE.rotation_euler = (math.pi / 2, 0, 0)
        PHL.data.energy = 0.0
    else:
        stand(YOU, Vector((-0.45, 0.06, 0.1)))
        for pv in YOU_ARMS:
            pv.rotation_euler = (-1.98, 0, 0)
        buzz = 0.006 * math.sin(t * 90) if 0 <= t - EV["buzz"] < 0.6 else 0.0
        PHONE.location = Vector((-0.45 + buzz, -0.045, 0.31))
        PHONE.rotation_euler = (0.25, 0, 0)
        PHL.data.energy = 0.4
    show_between(B_UP, t, -0.2, start_of("door"))
    show_between(B_OUT, t, EV["buzz"] + 0.15, start_of("exdoor"))
    show_between(B_UP2, t, EV["sent2"])

    # the visitors
    bedge = Vector((-0.2, -0.15, 0.08))
    if t < T_PILE:
        t_bed = start_of("bed") - 0.2
        walk(NEI, t, t_bed, DOORWAY, bedge, dur=max(0.4, EV["sit"] - t_bed), appear=EV["open"], phase=1)
        walk(WIFE, t, EV["wife"] - 0.5, DOORWAY, Vector((0.12, -0.04, 0)), phase=2)
        walk(PRIEST, t, EV["priest"] - 0.3, DOORWAY, Vector((0.33, -0.14, 0)), phase=3)
        walk(GMAN, t, EV["gooseman"] - 0.25, DOORWAY, Vector((0.72, -0.02, 0)), dur=1.6, phase=4)
        # the goose follows him in, then hops up onto the router
        if t < EV["gooseman"] - 0.25:
            GOOSE.location = AWAY
        elif t < EV["perch"] - 0.35:
            u = smooth01((t - EV["gooseman"] + 0.25) / 1.6)
            GOOSE.location = Vector((0.62, 0.36, 0)).lerp(Vector((0.92, -0.02, 0)), u)
            GOOSE.location.z += 0.012 * abs(math.sin(t * 14))
        else:
            u = smooth01((t - EV["perch"] + 0.35) / 0.45)
            p = Vector((0.92, -0.02, 0)).lerp(Vector((0.97, 0.25, 0.245)), u)
            p.z += 0.12 * math.sin(math.pi * u)
            GOOSE.location = p
        GNECK.rotation_euler = (0.15 * math.sin(t * 3), 0, 0)
        walk(EX, t, EV["ex"] - 0.25, DOORWAY + Vector((0, 0.12, 0)), DOORWAY, dur=0.5, phase=5)
        walk(EXN1, t, EV["ex"] - 0.25, Vector((0.47, 0.64, 0)), Vector((0.47, 0.57, 0)), dur=0.5, phase=6)
        walk(EXN2, t, EV["ex"] - 0.25, Vector((0.64, 0.66, 0)), Vector((0.64, 0.6, 0)), dur=0.5, phase=7)
    else:
        # everyone asleep: you and the neighbour on the bed, the rest in a row on the rug
        lie(NEI, Vector((-0.27, -0.12, 0.14)))
        for k, r in enumerate((EXN2, WIFE, PRIEST, EX, GMAN, EXN1)):
            lie(r, Vector((-0.12 + k * 0.17, -0.8, 0.07)))
        GOOSE.location = Vector((0.97, 0.25, 0.245))
        GNECK.rotation_euler = (1.25, 0, 0)
    show_between(B_HARV, t, EV["harvest"], start_of("wife"))

    # z z Z: the goose first, then everyone else (you wake back up for phone3)
    for i, (key, at) in enumerate(ZZZ_AT):
        t0 = EV["zzz"] + (0.0 if i == 0 else 0.55 + 0.12 * i)
        ob = ZZZ[key]
        if t >= t0 and t >= T_PILE and not (key == "you" and t >= T_P3):
            pop(ob, t - t0)
            ob.location = at + Vector((0, 0, 0.015 * math.sin((t - t0) * 3 + i)))
        else:
            hide(ob)

    # medieval room: lying in bed, they sit up on events.wake
    su = smooth01((t - EV["wake"]) / 0.6) if t >= EV["wake"] else 0.0
    for r, x in ((MAN1, -0.18), (WOM1, 0.18)):
        r.location = O1 + Vector((x, -0.1, 0.09))
        r.rotation_euler = (-math.pi / 2 * (1 - su), 0, 0)
    show_between(S_SHIFT, t, EV["shifts"] - 0.2, start_of("wake"))
    show_between(S_AWAKE, t, EV["wake"] + 0.3, start_of("visit"))

    # lane: a lantern walks to the next cottage; its window lights up after the knock
    walk(VIS, t, EV["walk"], O2 + Vector((-0.6, 0.15, 0)), O2 + Vector((0.6, 0.15, 0)),
         dur=max(0.6, EV["knock2"] - EV["walk"]), appear=start_of("visit") - 0.1)
    B.bsdf(WINB[1]).inputs["Emission Strength"].default_value = 1.2 if t >= EV["knock2"] + 0.4 else 0.09

    # book: the two names appear as they are read
    show_between(BOOK_T["first"], t, EV["first"] - 0.05)
    show_between(BOOK_T["second"], t, EV["second"] - 0.05)

B.render_settings(FPS, samples=int(os.environ.get("YT_SAMPLES", "24")), motion_blur=0.0)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1) / FPS)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
