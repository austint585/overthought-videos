"""Pastel toy kit, "The Barista Crush": toy peg people. Sets: a coffee shop counter (a latte slides to your friend on
frame one, hearts pop over their head, a tower of their empty cups grows, wall signs count visits and words said), a
tiered lecture hall of peg students with four women who came 0, 5, 10 and 15 times, and a rating board. Shots, timed by
render_barista.py: cafe, cups, hall, four, sit, rate, who, love, final. Helpers copied from turkey_scene.py.

blender -b --factory-startup -P barista_scene.py -- timing.json out_dir MODE   (MODE: "all" or 1-based frame list)
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




def cup(name, at, parent=None):
    root = empty(name, at, parent)
    cyl(name + "c", 0.042, 0.0, 0.075, 0, 0, "FBF8F0", r2=0.05, seg=32).parent = root
    cyl(name + "s", 0.0475, 0.025, 0.05, 0, 0, "B98A6A", r2=0.049, seg=32).parent = root
    cyl(name + "l", 0.052, 0.075, 0.085, 0, 0, "FFFFFF", seg=32).parent = root
    return root

def heart(name):
    root = empty(name, AWAY)
    m = glow_mat("hm" + name, "F28FA5", 2.0)
    for s in (-1, 1):
        b = ball(f"{name}{s}", 0.022, "F28FA5", (s * 0.015, 0, 0.008))
        b.data.materials[0] = m
        b.parent = root
    tip = rbox(name + "t", -0.024, 0.024, -0.01, 0.01, -0.024, 0.024, "F28FA5", bev=0.006, parent=root)
    tip.data.materials[0] = m
    tip.rotation_euler = (0, math.pi / 4, 0)
    tip.location = (0, 0, -0.012)
    return root

# ------------------------------------------------------------------ 0 the coffee shop
O0 = Vector()
rbox("floor0", -3, 3, -4, 0.5, -0.05, 0, "D9B48F", bev=0)
rbox("wall0", -3, 3, 0.5, 0.58, 0, 3, "F6D6D0", bev=0)
rbox("skirt0", -3, 3, 0.485, 0.5, 0, 0.04, "FFFFFF", bev=0)
rbox("ctr0", -0.45, 0.22, -0.1, 0.14, 0, 0.34, "7FB9A8")
rbox("top0", -0.47, 0.24, -0.12, 0.16, 0.34, 0.37, "F4EDE2", bev=0.008, rough=0.35)
rbox("esp0", -0.4, -0.27, 0.0, 0.13, 0.371, 0.53, "C0C6CC", rough=0.3)
rbox("espg", -0.38, -0.29, -0.003, 0.0, 0.47, 0.51, "2F3843", bev=0).data.materials[0] = glow_mat("espgm", "9FC3DD", 1.5)
cup("espcup", Vector((-0.335, 0.03, 0.371)))
rbox("plat0", -0.3, 0.05, 0.2, 0.42, 0, 0.06, "D9B48F", bev=0)
for k, (x, z, c) in enumerate(((-0.6, 1.5, "F6C945"), (0.95, 1.4, "7FA7D6"))):
    wall_disc(f"lamp{k}", 0.08, c, Vector((x, 0.49, z)))
BAR, BAR_A = peg("bar", "4FA36B", Vector((-0.12, 0.3, 0.06)), hair="2F2A28", long_hair=True)
FRI, FRI_A = peg("fri", YOU_C, Vector((0.45, -0.15, 0.0)), hair="6B4A3A")
BAR.scale = FRI.scale = (1.5, 1.5, 1.5)
LATTE = cup("latte", AWAY)
HEARTS = [heart(f"h{k}") for k in range(3)]
TOWER = [cup(f"tw{k}", AWAY) for k in range(16)]
VIS, VIS_T = sign("vis", Vector((0.55, 0.47, 1.05)), "VISITS THIS YEAR", "187", "ONE LATTE EACH", w=0.42, h=0.25)
WRD, WRD_T = sign("wrd", Vector((-0.12, 0.47, 1.05)), "WORDS SAID", "0", "TO THE BARISTA", w=0.42, h=0.25)

# ------------------------------------------------------------------ 1 the lecture hall
O1 = Vector((10.0, 0, 0))
rbox("floor1", -3, 3, -4, 1.2, -0.05, 0, "C9A27E", bev=0, off=O1)
rbox("wall1", -3, 3, 1.2, 1.28, 0, 3, "D8DDF6", bev=0, off=O1)
rbox("lect", 1.2, 1.44, -0.75, -0.6, 0, 0.32, "8A5A3A", bev=0.01, off=O1)
STUD_C = ["A7B4C2", "C2B8A3", "B9C9B0", "C7AFC2", "B4A7C2", "C9BBA0"]
HAIR_C = ["2F2A28", "6B4A3A", "C9955E", "3A2E2A"]
srnd = random.Random(5)
STUDENTS = []

def row_yz(k):
    return 0.4 * k, 0.16 * k

for k in range(3):
    y, z = row_yz(k)
    if k:
        rbox(f"tier{k}", -1.25, 1.25, y - 0.2, 1.2, 0, z, "B98A6A", bev=0, off=O1)
    rbox(f"desk{k}", -1.2, 1.2, y - 0.17, y - 0.11, z, z + 0.17, "D79A5F", bev=0.006, off=O1)
    rbox(f"deskt{k}", -1.22, 1.22, y - 0.2, y - 0.08, z + 0.17, z + 0.185, "E8B57A", bev=0.004, off=O1)
    xs = [-1.0 + 0.25 * i for i in range(9)] if k != 1 else [-1.05, -0.8, 0.8, 1.05]
    for x in xs:
        p, a = peg(f"st{k}{x}", srnd.choice(STUD_C), O1 + Vector((x, y, z)), hair=srnd.choice(HAIR_C),
                   long_hair=srnd.random() < 0.4)
        p.rotation_euler = (0, 0, srnd.uniform(-0.15, 0.15))
        for pv in a:
            pv.rotation_euler = (-0.9, 0, 0)
        STUDENTS.append(p)
WOMEN = []
for i, (n, x, c) in enumerate(((0, -0.45, "F6C945"), (5, -0.15, "9B7FD6"), (10, 0.15, "4FA36B"), (15, 0.45, "EE6F52"))):
    y, z = row_yz(1)
    p, a = peg(f"wo{n}", c, AWAY, hair=("2F2A28", "C9955E", "6B4A3A", "3A2E2A")[i], long_hair=True)
    for pv in a:
        pv.rotation_euler = (-0.9, 0, 0)
    sg, tx = sign(f"ws{n}", AWAY, "VISITS", "0", "", w=0.26, h=0.17)
    WOMEN.append((n, p, O1 + Vector((x, y, z)), sg, tx))
RIB = empty("rib", AWAY)
torus("ribt", 0.022, 0.008, (0, 0, 0), (math.pi / 2, 0, 0), "F6C945").parent = RIB
ball("ribc", 0.016, "F6C945", (0, 0, 0), (1, 0.5, 1)).parent = RIB
for s in (-1, 1):
    tl = rbox(f"ribl{s}", -0.006, 0.006, -0.003, 0.003, -0.04, 0.0, "D9433B", bev=0, parent=RIB)
    tl.location = (s * 0.008, 0, -0.012)
    tl.rotation_euler = (0, s * 0.3, 0)
PERF = text("perf", "PERFECT ATTENDANCE", 0.03, "F6C945", AWAY, glow=1.2)
DOTS = bubble("dots", AWAY, "...", w=0.12, h=0.07)
HALL, HALL_T = sign("hall", O1 + Vector((0, 1.17, 1.15)), "1992 LECTURE", "100+", "STUDENTS", w=0.5, h=0.3)

# ------------------------------------------------------------------ 2 the rating board
O2 = room(2, "CFE8C9", "E8D9C8")
rbox("board", -0.8, 0.8, 0.28, 0.31, 0.05, 1.32, "FFFFFF", bev=0.01, off=O2, rough=0.6)
text("btitle", "HOW ATTRACTIVE? (1 TO 7)", 0.075, INKC, O2 + Vector((0, 0.262, 1.24)), glow=0.4)
BASE, SPAN = 0.22, 0.85
rbox("base2", -0.72, 0.72, 0.266, 0.276, BASE - 0.01, BASE, INKC, bev=0, off=O2)
rbox("top2", -0.72, 0.72, 0.27, 0.274, BASE + SPAN - 0.003, BASE + SPAN, "B8B4AA", bev=0, off=O2)
text("ax7", "7", 0.05, INKC, O2 + Vector((-0.76, 0.262, BASE + SPAN)), glow=0.4)
text("ax1", "1", 0.05, INKC, O2 + Vector((-0.76, 0.262, BASE)), glow=0.4)
RATE = []
for i, (n, r, c) in enumerate(((0, 3.62, "F6C945"), (5, 3.88, "9B7FD6"), (10, 4.25, "4FA36B"), (15, 4.38, "EE6F52"))):
    x = -0.48 + i * 0.32
    b = rbox(f"rb{n}", -0.1, 0.1, -0.02, 0.02, 0, 1.0, c, bev=0.006)
    b.location = O2 + Vector((x, 0.245, BASE))
    h = (r - 1) / 6 * SPAN
    text(f"rl{n}", f"{n} VISITS", 0.045, INKC, O2 + Vector((x, 0.262, 0.15)), glow=0.4)
    v = text(f"rv{n}", f"{r:.2f}", 0.05, "FFFFFF", AWAY, glow=1.0)
    mini, _ = peg(f"mini{n}", c, AWAY, hair=("2F2A28", "C9955E", "6B4A3A", "3A2E2A")[i], long_hair=True)
    mini.scale = (0.55,) * 3
    RATE.append((b, h, x, v, mini, i))
CROWN = empty("crown", AWAY)
cyl("crc", 0.03, 0, 0.025, 0, 0, "F6C945", seg=10).parent = CROWN
WHO, WHO_A = peg("who", "A7B4C2", O2 + Vector((0.95, -0.25, 0)), hair="6B4A3A")
WHO.scale = (1.4,) * 3
WHOB = bubble("whob", AWAY, "WHO?", w=0.18, h=0.08)

# ------------------------------------------------------------------ light, world, camera
w = bpy.data.worlds.new("w")
scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (*hexc("F2E2D6"), 1)
w.node_tree.nodes["Background"].inputs[1].default_value = float(os.environ.get("TK_WORLD", "0.8"))
B.sun("sun", -130, 40, float(os.environ.get("TK_SUN", "2.4")), color=hexc("FFF1DE"), angle_deg=8)
for k, o in enumerate((O0, O1, O2)):
    B.area(f"fill{k}", o + Vector((0.3, -2.4, 1.6)), o + Vector((0.1, 0.2, 0.4)), 3.0, float(os.environ.get("TK_FILL", "45")),
           color=hexc("FFF0E0"))
B.area("cafek", O0 + Vector((0.1, -0.4, 1.3)), O0 + Vector((0.1, 0.0, 0.4)), 0.8, 12, color=hexc("FFD9A8"))
cam = B.camera(lens=28, fstop=14.0)
cam.data.clip_start, cam.data.clip_end = 0.01, 200.0

def lc(a, b, tg, u, o, lens=28):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "cafe": lambda u: lc((0.18, -1.45, 0.72), (0.18, -1.32, 0.7), (0.18, 0.0, 0.6), u, O0, 24),
    "cups": lambda u: lc((0.78, -1.35, 0.62), (0.74, -1.22, 0.66), (0.66, 0.0, 0.66), u, O0, 30),
    "hall": lambda u: lc((0.0, -2.7, 1.25), (0.0, -2.45, 1.15), (0.0, 0.45, 0.5), u, O1),
    "four": lambda u: lc((-0.05, -1.25, 0.85), (0.05, -1.15, 0.82), (0.0, 0.4, 0.5), u, O1),
    "sit": lambda u: lc((0.52, -0.25, 0.78), (0.5, -0.18, 0.74), (0.45, 0.4, 0.52), u, O1, 32),
    "rate": lambda u: lc((0.0, -2.0, 0.74), (0.0, -1.85, 0.72), (0.0, 0.2, 0.68), u, O2),
    "who": lambda u: lc((0.6, -1.4, 0.62), (0.66, -1.3, 0.6), (0.62, 0.1, 0.58), u, O2),
    "love": lambda u: lc((0.5, -1.05, 0.62), (0.52, -0.95, 0.72), (0.52, 0.0, 0.78), u, O0),
    "final": lambda u: lc((0.15, -1.85, 0.8), (0.15, -1.7, 0.76), (0.15, 0.0, 0.62), u, O0, 26),
}

def shot_at(t):
    k = max([0] + [i for i, (s, _) in enumerate(SHOTS) if t >= s - 1e-6])
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    cut = max(0.0, min(1.0, (t - SHOTS[k][0]) / max(1e-6, t1 - SHOTS[k][0])))
    return SHOTS[k][1], cut

def start_of(n):
    return next(s for s, m in SHOTS if m == n)

def apply_state(t):
    name, cut = shot_at(t)
    loc, tg, lens = CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    cam.data.dof.use_dof = False

    # ---- cafe: the latte slides across on frame one, hearts float over your friend, the cup tower grows
    u = smooth01((t + 0.15) / 0.6)
    LATTE.location = Vector((-0.08 + 0.26 * u, -0.02, 0.371))
    BAR_A[0].rotation_euler = (-0.9 - 0.6 * (1 - u), 0, 0)
    BAR_A[1].rotation_euler = (-0.9 + 0.05 * math.sin(t * 2), 0, 0)
    BAR.rotation_euler = (0, 0, 0.05 * math.sin(t * 0.9))
    FRI.rotation_euler = (0, 0, -0.6 + 0.04 * math.sin(t * 1.4))
    FRI.location.z = 0.012 * abs(math.sin(t * 3.0))
    FRI_A[0].rotation_euler = (-0.9, 0, 0)
    FRI_A[1].rotation_euler = (-0.6 - 1.2 * (0.5 + 0.5 * math.sin(t * 5)) * (1 if t < 2.0 else 0.3), 0, 0)
    for k, hr in enumerate(HEARTS):
        a = t * 1.6 + k * 2.1
        hr.location = Vector((0.45 + 0.12 * math.cos(a), -0.2 + 0.05 * math.sin(a), 0.68 + 0.04 * math.sin(t * 3 + k)))
        hr.rotation_euler = (0, 0.25 * math.sin(t * 2 + k), 0)
        age = t - (0.05 + k * 0.12)
        if age < 0:
            hide(hr)
        else:
            pk = back_out(age / 0.25)
            beat = 1 + 0.12 * max(0.0, math.sin(t * 7))
            if t >= start_of("love"):
                beat *= 1.5
            hr.scale = (max(0.001, 1.6 * pk * beat),) * 3
    if t < EV["cups"]:
        n = 5
    elif t < start_of("love"):
        n = 5 + int(7 * smooth01((t - EV["cups"]) / 1.0))
    else:
        n = 12 + int(4 * smooth01((t - start_of("love")) / 0.8))
    for k, c in enumerate(TOWER):
        if k < n:
            c.location = Vector((0.72 + 0.006 * math.sin(k * 1.7 + t * 2) * (k / 8), -0.05, 0.07 * k))
            c.scale = (1, 1, 1)
        else:
            hide(c)
            c.location = AWAY
    visits = 187 + int(27 * smooth01((t - EV["cups"]) / 1.0)) if t >= EV["cups"] else 187
    set_sign(VIS_T, big=str(visits), w=0.42)
    if t >= start_of("love"):
        set_sign(WRD_T, "WORDS SAID", "0", "STILL", w=0.42)
    else:
        set_sign(WRD_T, "WORDS SAID", "0", "TO THE BARISTA", w=0.42)
    WRD.scale = (1,) * 3 if t < EV["zero"] else (1 + 0.15 * max(0.0, 1 - (t - EV["zero"]) / 0.3),) * 3

    # ---- lecture hall: the four women take their seats one number at a time
    for n, p, at, sg, tx in WOMEN:
        te = EV[f"w{n}"]
        sg.location = at + Vector((0, -0.05, 0.47))
        if t < te:
            hide(sg)
        else:
            pop(sg, t - te)
        cnt = count(t, te, 0.45, n)
        set_sign(tx, "VISITS", str(cnt), "", w=0.26)
        if n == 0 or t < te:
            hide(p)
            p.location = AWAY
        else:
            p.location = at
            pop(p, t - te)
            p.rotation_euler = (0, 0, 0.04 * math.sin(t + n))
    w15 = WOMEN[3][2]
    if t >= EV["ribbon"]:
        RIB.location = w15 + Vector((0.035, -0.072, 0.15))
        pop(RIB, t - EV["ribbon"], 1.4)
        PERF.location = Vector((w15.x, w15.y - 0.177, w15.z + 0.09))
        pop(PERF, t - EV["ribbon"])
    else:
        hide(RIB, PERF)
        RIB.location = PERF.location = AWAY
    if start_of("sit") <= t < start_of("rate"):
        DOTS.location = w15 + Vector((-0.12, -0.02, 0.42))
        pop(DOTS, t - start_of("sit") - 0.3)
    else:
        hide(DOTS)
        DOTS.location = AWAY

    # ---- rating board: four bars rise, the 15-visit one wins a tiny crown
    ra = t - EV["rate"]
    for b, h, x, v, mini, i in RATE:
        g = smooth01((ra - 0.2 - i * 0.25) / 0.4) if ra > 0 else 0.0
        b.scale = (1, 1, max(0.001, h * g))
        if g <= 0:
            hide(mini, v)
            mini.location = v.location = AWAY
        else:
            mini.location = O2 + Vector((x, 0.24, BASE + h * g))
            pop(mini, ra - 0.2 - i * 0.25, 0.55)
            v.location = O2 + Vector((x, 0.22, BASE + h * g - 0.05))
            pop(v, ra - 0.2 - i * 0.25)
    b, h, x, v, mini, i = RATE[3]
    if ra > 1.6:
        CROWN.location = O2 + Vector((x, 0.24, BASE + h + 0.205))
        pop(CROWN, ra - 1.6)
    else:
        hide(CROWN)
        CROWN.location = AWAY
    WHO.rotation_euler = (0, 0, 0.5)
    sh = 0.5 + 0.5 * math.sin(t * 6)
    WHO_A[0].rotation_euler = (0, 0.6 + 0.4 * sh, 0) if t >= EV["who"] else (-0.9, 0, 0)
    WHO_A[1].rotation_euler = (0, -0.6 - 0.4 * sh, 0) if t >= EV["who"] else (-0.9, 0, 0)
    if t >= EV["who"]:
        WHOB.location = O2 + Vector((0.82, -0.3, 0.68))
        pop(WHOB, t - EV["who"])
    else:
        hide(WHOB)
        WHOB.location = AWAY

B.render_settings(FPS, samples=int(os.environ.get("YT_SAMPLES", "24")), motion_blur=0.0)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1) / FPS)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
