"""Pastel toy kit at night, "Singles' Day": toy peg people. Sets: your single friend's apartment at night (lilac walls, a
beanbag, a glowing phone, a wall sign, a pile of delivery boxes that grows), a 1993 dorm (bunk bed, four peg students
lining up under an 11.11 banner) and a pink wedding hall in Beijing (an arch, rows of couples). Shots, timed by
render_singles.py: apart, ones, dorm, sale, counter, presents, wedding, taken, final. Helpers copied from xmas_scene.py.

blender -b --factory-startup -P singles_scene.py -- timing.json out_dir MODE   (MODE: "all" or 1-based frame list)
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

def santa_hat(name, parent, z=0.3, r=0.066, h=0.11):
    hat = empty(name, Vector((0, 0.005, z)), parent)
    c = cyl(name + "c", r, 0, h, 0, 0, "D9433B", r2=0.012)
    c.parent = hat
    c.rotation_euler = (0.25, 0, 0)
    b = torus(name + "b", r, r * 0.28, (0, 0, 0.005), (0, 0, 0), "FFFFFF")
    b.parent = hat
    tip = ball(name + "t", r * 0.3, "FFFFFF", (0, 0.03, h - 0.005))
    tip.parent = hat
    return hat

def set_sign(tx, head=None, big=None, foot=None, w=0.7):
    for key, body, size in (("head", head, 0.04), ("big", big, 0.11), ("foot", foot, 0.035)):
        if body is not None and tx[key].data.body != body:
            tx[key].data.body = body
            tx[key].data.size = min(size, (w - 0.06) / (max(1, len(body)) * 0.58))

def count(t, t0, dur, n):
    return int(round(n * smooth01((t - t0) / dur))) if t >= t0 else 0

def show_between(ob, t, t0, t1=1e9):
    if t0 <= t < t1:
        pop(ob, t - t0)
    else:
        hide(ob)

# ------------------------------------------------------------------ 0 your friend's apartment at night

O0 = Vector()
rbox("floor0", -3, 3, -4, 0.32, -0.05, 0, "C9A27E", bev=0)
rbox("wall0", -3, 3, 0.32, 0.4, 0, 3, "B9B7E6", bev=0)
rbox("skirt0", -3, 3, 0.305, 0.32, 0, 0.03, "FFFFFF", bev=0)
rbox("rug0", -0.5, 0.5, -0.55, 0.05, 0.0005, 0.004, "F2A7B5", bev=0)
# night window with a moon
rbox("winf0", -0.75, -0.35, 0.305, 0.325, 0.42, 0.8, "FFFFFF", bev=0.006)
rbox("wing0", -0.73, -0.37, 0.298, 0.304, 0.44, 0.78, "2B3566", bev=0).data.materials[0] = glow_mat("nsky", "2B3566", 0.6)
ball("moon", 0.04, "FFF3C4", (-0.47, 0.294, 0.7), (1, 0.2, 1)).data.materials[0] = glow_mat("moonm", "FFF3C4", 3.0)
for k, (x, z) in enumerate(((-0.66, 0.72), (-0.6, 0.55), (-0.42, 0.5), (-0.55, 0.66))):
    ball(f"st{k}", 0.006, "FFFFFF", (x, 0.295, z)).data.materials[0] = glow_mat(f"stm{k}", "FFFFFF", 4.0)
rbox("winbar0", -0.556, -0.544, 0.292, 0.298, 0.44, 0.78, "FFFFFF", bev=0)
# lamp (the warm practical)
cyl("lampb", 0.012, 0, 0.42, 0.62, 0.15, "F4F1E8")
LAMPS = cyl("lamps", 0.07, 0.4, 0.5, 0.62, 0.15, "FFD9A0", r2=0.045)
LAMPS.data.materials[0] = glow_mat("lampm", "FFD9A0", 3.0)
# beanbag and your friend on it
ball("bean", 0.2, "7FA7D6", (0.0, -0.05, 0.1), (1.0, 0.95, 0.55))
FR, FR_A = peg("fr", "EE6F52", Vector((0.0, -0.08, 0.13)), hair="6B4A3A")
PHONE = empty("phone", Vector((0, -0.12, 0.08)), FR)
rbox("phb", -0.022, 0.022, -0.004, 0.004, -0.038, 0.038, "1E1E24", bev=0.003, parent=PHONE)
ph = rbox("phs", -0.019, 0.019, -0.0055, -0.004, -0.034, 0.034, "BFE6FF", bev=0, parent=PHONE)
ph.data.materials[0] = glow_mat("scrm", "DCEFFF", 2.0)
CART = text("cart", "CART: 0", 0.008, "1E1E24", (0, -0.006, 0.0), PHONE, glow=0.6)
# wall sign above
SIGN, STX = sign("sign", Vector((0.0, 0.3, 0.68)), "NOVEMBER", "11.11", "SINGLES' DAY", w=0.62, h=0.32)
# delivery boxes that pile up around the beanbag
rnd = random.Random(11)
BOXES = []
for k in range(14):
    s = rnd.uniform(0.05, 0.09)
    b = empty(f"bx{k}", AWAY)
    rbox(f"bxb{k}", -s, s, -s * 0.8, s * 0.8, 0, s * 1.2, ("D9A86C", "C99559", "E3B97F")[k % 3], bev=0.006, parent=b)
    rbox(f"bxt{k}", -s * 0.18, s * 0.18, -s * 0.81, s * 0.81, s * 1.2 - 0.001, s * 1.2 + 0.002, "F4F1E8", bev=0, parent=b)
    side = -1 if k % 2 else 1
    x = side * rnd.uniform(0.28, 0.6)
    y = rnd.uniform(-0.35, 0.15)
    z = 0.0 if k < 8 else 0.1
    BOXES.append((b, Vector((x, y, z)), rnd.uniform(-0.4, 0.4), k * 0.16))
GIFT = empty("gift", AWAY)
rbox("gb", -0.045, 0.045, -0.045, 0.045, 0, 0.08, "F6C945", bev=0.006, parent=GIFT)
rbox("gr1", -0.008, 0.008, -0.0465, 0.0465, -0.001, 0.0815, "EE6F52", bev=0, parent=GIFT)
rbox("gr2", -0.0465, 0.0465, -0.008, 0.008, -0.001, 0.0815, "EE6F52", bev=0, parent=GIFT)
for s in (-1, 1):
    bw = ball(f"gbow{s}", 0.02, "EE6F52", (s * 0.018, 0, 0.09), (1, 0.5, 0.6))
    bw.parent = GIFT
HEART = ball("heart", 0.03, "F2A7B5", AWAY, (1, 0.5, 1))
HEART.data.materials[0] = glow_mat("heartm", "F28FA5", 2.0)

# ------------------------------------------------------------------ 1 the 1993 dorm

O1 = room(1, "CFE8C9", "C9A27E")
for x in (-0.9, -0.5):
    for y in (-0.12, 0.2):
        rbox(f"bkp{x}{y}", x - 0.015, x + 0.015, y - 0.015, y + 0.015, 0, 0.62, "B98A6A", bev=0, off=O1)
for z in (0.12, 0.42):
    rbox(f"bkm{z}", -0.9, -0.5, -0.12, 0.2, z, z + 0.05, "FFFFFF", bev=0.015, off=O1)
    rbox(f"bkb{z}", -0.88, -0.52, -0.1, 0.18, z + 0.05, z + 0.08, "7FA7D6", bev=0.02, off=O1)
rbox("dsk", 0.5, 0.95, -0.05, 0.25, 0.22, 0.25, "D79A5F", bev=0.008, off=O1)
for x in (0.52, 0.93):
    rbox(f"dskl{x}", x - 0.01, x + 0.01, -0.03, 0.23, 0, 0.22, "B98A6A", bev=0, off=O1)
rbox("crt", 0.6, 0.8, 0.03, 0.22, 0.25, 0.43, "E8E1D0", bev=0.02, off=O1)
rbox("crts", 0.62, 0.78, 0.02, 0.028, 0.27, 0.41, "4FA36B", bev=0, off=O1).data.materials[0] = glow_mat("crtm", "6BC48A", 1.5)
BANNER, BTX = sign("ban", O1 + Vector((0.0, 0.3, 0.72)), "NANJING UNIVERSITY", "11.11", "1993", w=0.66, h=0.34)
STUD = []
for k in range(4):
    x = -0.27 + k * 0.18
    p, a = peg(f"s{k}", ("7FA7D6", "EE6F52", "F6C945", "4FA36B")[k], O1 + Vector((x, -0.05, 0)),
               hair=("2F2A28", "6B4A3A", "2F2A28", "8A5A3A")[k])
    STUD.append((p, a, O1 + Vector((x, -0.05, 0))))

# ------------------------------------------------------------------ 2 the Beijing wedding hall

O2 = room(2, "F6D2DA", "E8D9C8")
rbox("aisle", -0.12, 0.12, -1.2, 0.3, 0.0005, 0.004, "FFFFFF", bev=0, off=O2)
for k in range(15):
    a = math.pi * k / 14
    ball(f"arch{k}", 0.05, ("FFFFFF", "F2A7B5", "F6C945")[k % 3], O2 + Vector((0.32 * math.cos(a), 0.15, 0.05 + 0.5 * math.sin(a))))
WSIGN, WTX = sign("wsign", O2 + Vector((0.0, 0.3, 0.86)), "BEIJING, 11.11.2011", "0", "WEDDINGS IN ONE DAY", w=0.66, h=0.3)
COUPLES = []
crnd = random.Random(5)
for row in range(3):
    for col in range(4):
        x = (-0.75 + col * 0.18) if col < 2 else (0.39 + (col - 2) * 0.18)
        y = -0.15 - row * 0.28
        g, ga = peg(f"g{row}{col}", "2F3843", O2 + Vector((x - 0.045, y, 0)), hair="2F2A28")
        b, ba = peg(f"b{row}{col}", "FFFFFF", O2 + Vector((x + 0.045, y, 0)), hair="6B4A3A", long_hair=True, veil=True)
        COUPLES.append((g, ga, b, ba, O2 + Vector((x, y, 0)), crnd.uniform(0, 6)))
FR2, FR2_A = peg("fr2", "EE6F52", O2 + Vector((0.0, -0.55, 0)), hair="6B4A3A")
GIFT2 = empty("gift2", Vector((0, -0.08, 0.1)), FR2)
rbox("g2b", -0.04, 0.04, -0.04, 0.04, 0, 0.07, "F6C945", bev=0.006, parent=GIFT2)
rbox("g2r", -0.008, 0.008, -0.0415, 0.0415, -0.001, 0.0715, "EE6F52", bev=0, parent=GIFT2)

# ------------------------------------------------------------------ light, world, camera

w = bpy.data.worlds.new("w")
scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (*hexc("8E9BD6"), 1)
w.node_tree.nodes["Background"].inputs[1].default_value = float(os.environ.get("SG_WORLD", "0.7"))
B.sun("sun", -140, 50, float(os.environ.get("SG_SUN", "2.0")), color=hexc("DCE4FF"), angle_deg=8)
for k, o in enumerate((O0, O1, O2)):
    B.area(f"fill{k}", o + Vector((0.3, -2.0, 1.4)), o + Vector((0.1, 0, 0.25)), 2.5, float(os.environ.get("SG_FILL", "38")),
           color=hexc("FFF0E0"))
B.area("lampk", O0 + Vector((0.55, -0.2, 0.7)), O0 + Vector((0.0, -0.05, 0.2)), 0.4, float(os.environ.get("SG_LAMP", "10")),
       color=hexc("FFC98A"))
cam = B.camera(lens=35, fstop=14.0)
cam.data.clip_start, cam.data.clip_end = 0.01, 200.0

def lc(a, b, tg, u, o, lens=35):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "apart": lambda u: lc((0.08, -1.15, 0.5), (0.05, -1.0, 0.48), (0.03, -0.1, 0.4), u, O0),
    "ones": lambda u: lc((0.0, -1.35, 0.5), (0.0, -1.2, 0.48), (0.0, 0.0, 0.38), u, O1),
    "dorm": lambda u: lc((-0.35, -1.25, 0.55), (-0.2, -1.2, 0.5), (-0.1, 0.0, 0.3), u, O1),
    "sale": lambda u: lc((0.0, -1.2, 0.62), (0.0, -1.1, 0.6), (0.0, 0.1, 0.5), u, O0),
    "counter": lambda u: lc((0.0, -0.95, 0.68), (0.0, -0.85, 0.68), (0.0, 0.3, 0.68), u, O0),
    "presents": lambda u: lc((0.4, -1.3, 0.55), (0.2, -1.25, 0.5), (0.0, -0.05, 0.2), u, O0),
    "wedding": lambda u: lc((0.0, -2.0, 0.9), (0.0, -1.85, 0.85), (0.0, 0.0, 0.42), u, O2),
    "taken": lambda u: lc((0.12, -1.0, 0.25), (0.08, -0.92, 0.26), (0.0, -0.5, 0.22), u, O2),
    "final": lambda u: lc((0.5, -2.0, 1.0), (0.4, -1.85, 0.95), (0.0, 0.0, 0.3), u, O0),
}

def shot_at(t):
    k = max([0] + [i for i, (s, _) in enumerate(SHOTS) if t >= s - 1e-6])
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    cut = max(0.0, min(1.0, (t - SHOTS[k][0]) / max(1e-6, t1 - SHOTS[k][0])))
    return SHOTS[k][1], cut

def start_of(n):
    return next(s for s, m in SHOTS if m == n)

def dance(root, arms, t, at, phase=0.0, amp=1.0):
    root.location = at + Vector((0, 0, 0.02 * amp * abs(math.sin(t * 6.0 + phase))))
    root.rotation_euler = (0, 0.12 * amp * math.sin(t * 3.0 + phase), 0.25 * amp * math.sin(t * 1.5 + phase))
    for i, pv in enumerate(arms):
        pv.rotation_euler = (0, (-1) ** i * (2.4 + 0.35 * math.sin(t * 6.0 + i * math.pi)), 0)

def apply_state(t):
    name, cut = shot_at(t)
    loc, tg, lens = CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    cam.data.dof.use_dof = False

    # ---- apartment: your friend scrolls, then hugs a gift he bought himself
    hug = t - EV["hug"]
    FR.location = Vector((0.0, -0.08, 0.13))
    FR.rotation_euler = (0.15, 0, 0.04 * math.sin(t * 1.1))
    if hug < 0:
        PHONE.scale = (1, 1, 1)
        PHONE.location = Vector((0, -0.12, 0.08 + 0.004 * math.sin(t * 9)))
        FR_A[0].rotation_euler = (-1.2, 0, 0.3)
        FR_A[1].rotation_euler = (-1.2 + 0.08 * math.sin(t * 9), 0, -0.3)
        hide(GIFT)
        GIFT.location = AWAY
    else:
        u = smooth01(hug / 0.5)
        hide(PHONE)
        GIFT.location = Vector((0, -0.2, 0.12)).lerp(Vector((0, -0.16, 0.18)), u)
        GIFT.scale = (1, 1, 1)
        GIFT.rotation_euler = (0, 0, 0.1 * math.sin(t * 2))
        for i, pv in enumerate(FR_A):
            pv.rotation_euler = (-1.5 * u, 0, (-1) ** i * -0.6 * u)
        FR.location = Vector((0.0, -0.08, 0.13 + 0.01 * abs(math.sin(t * 4))))
    if hug >= 0.3:
        HEART.location = Vector((0.0, -0.1, 0.5 + 0.03 * math.sin(t * 3)))
        pop(HEART, hug - 0.3)
    else:
        hide(HEART)
        HEART.location = AWAY
    ncart = 0 if t < EV["sale"] else min(6, 1 + int((t - EV["sale"]) / 0.9))
    CART.data.body = f"CART: {ncart}"
    if t < start_of("sale"):
        set_sign(STX, "NOVEMBER", "11.11", "SINGLES' DAY", w=0.62)
    elif t < start_of("counter"):
        set_sign(STX, "ALIBABA, 2009", "SALE", "SINGLES' DAY", w=0.62)
    elif t < start_of("final"):
        v = 84.5 * smooth01((t - EV["count"]) / 1.6) if t >= EV["count"] else 0.0
        set_sign(STX, "ALIBABA, 2021", f"${v:.1f}B", "SOLD ON SINGLES' DAY", w=0.62)
    else:
        set_sign(STX, "SINGLES' DAY", "WED NOV 11", "STILL SINGLE", w=0.62)
    for k, (b, at, rz, delay) in enumerate(BOXES):
        age = t + 0.1 if k == 0 else t - EV["sale"] - delay   # box 0 is already falling on frame one
        if age < 0:
            hide(b)
            b.location = AWAY
            continue
        u = min(1.0, age / 0.35)
        b.scale = (1, 1, 1)
        if k == 0:
            at = Vector((0.3, -0.2, 0.0))
        b.location = at + Vector((0, 0, 0.9 * (1 - u) ** 2))
        b.rotation_euler = (0, 0, rz)

    # ---- dorm: four students pop in one by one under 11.11, then cheer
    for k, (p, a, at) in enumerate(STUD):
        age = t - EV["ones"] - k * 0.3
        if age < 0:
            hide(p)
            continue
        if t >= EV["cheer"]:
            dance(p, a, t, at, phase=k * 1.3)
        else:
            p.location = at
            p.rotation_euler = (0, 0, 0)
            for pv in a:
                pv.rotation_euler = (0, 0, 0)
        p.scale = (1, 1, 1) if age > 0.25 else (max(0.001, back_out(age / 0.25)),) * 3

    # ---- wedding: couples dance, the counter climbs; your friend stands in front with his gift
    for g, ga, b, ba, at, ph in COUPLES:
        dance(g, ga, t, at - Vector((0.045, 0, 0)), phase=ph, amp=0.7)
        dance(b, ba, t, at + Vector((0.045, 0, 0)), phase=ph + 0.5, amp=0.7)
    nw = count(t, EV["wed"] - 0.2, 1.6, 4000)
    set_sign(WTX, big=(f"{nw:,}+" if nw >= 4000 else f"{nw:,}"), w=0.66)
    dr = smooth01((t - EV["droop"]) / 0.6) if t >= EV["droop"] else 0.0
    FR2.rotation_euler = (0.25 * dr, 0, 0)
    for i, pv in enumerate(FR2_A):
        pv.rotation_euler = (-1.3 + 0.5 * dr, 0, (-1) ** i * -0.5)

B.render_settings(FPS, samples=int(os.environ.get("YT_SAMPLES", "24")), motion_blur=0.0)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1) / FPS)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
