"""Pastel toy kit, "The Turkey Drop": toy peg people. Sets: a hometown Thanksgiving table at dusk (a roast turkey drops
onto the platter on frame one, your friend and their high school sweetheart sit across from each other under a wall
sign), a corkboard of campus-paper clippings, and a giant breakup chart wall (a year of bars, the December spike, an
almost empty Christmas Day with a tiny tree). Shots, timed by render_turkey.py: table, name, pie, papers, chart, spike,
xmas, safe, final. Helpers copied from singles_scene.py.

blender -b --factory-startup -P turkey_scene.py -- timing.json out_dir MODE   (MODE: "all" or 1-based frame list)
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


def turkey(name, at, s=1.0):
    root = empty(name, at)
    b = ball(name + "b", 0.1 * s, "B8662E", (0, 0, 0.06 * s), (1.25, 1.0, 0.7))
    b.parent = root
    for k in (-1, 1):
        d = ball(f"{name}d{k}", 0.04 * s, "A9561F", (k * 0.07 * s, -0.08 * s, 0.07 * s), (0.8, 1.5, 0.8))
        d.parent = root
        bn = ball(f"{name}n{k}", 0.014 * s, "FFF6E6", (k * 0.08 * s, -0.135 * s, 0.075 * s))
        bn.parent = root
    hl = ball(name + "h", 0.05 * s, "D58B4A", (0, 0.02 * s, 0.1 * s), (1.5, 1.0, 0.5))
    hl.parent = root
    return root

# ------------------------------------------------------------------ 0 the hometown Thanksgiving table at dusk

O0 = Vector()
rbox("floor0", -3, 3, -4, 0.32, -0.05, 0, "C9A27E", bev=0)
rbox("wall0", -3, 3, 0.32, 0.4, 0, 3, "F2D3B3", bev=0)
rbox("skirt0", -3, 3, 0.305, 0.32, 0, 0.03, "FFFFFF", bev=0)
rbox("winf0", -0.82, -0.42, 0.305, 0.325, 0.42, 0.8, "FFFFFF", bev=0.006)
rbox("wing0", -0.8, -0.44, 0.298, 0.304, 0.44, 0.78, "F2A07B", bev=0).data.materials[0] = glow_mat("dusk", "F5A47E", 0.9)
ball("sun0", 0.05, "FFE29A", (-0.62, 0.294, 0.5), (1, 0.2, 1)).data.materials[0] = glow_mat("sunm", "FFE29A", 3.0)
rbox("winbar0", -0.626, -0.614, 0.292, 0.298, 0.44, 0.78, "FFFFFF", bev=0)
rbox("tablet", -0.5, 0.5, -0.32, 0.12, 0.3, 0.33, "D79A5F", bev=0.01)
for x in (-0.46, 0.46):
    for y in (-0.28, 0.08):
        rbox(f"tl{x}{y}", x - 0.015, x + 0.015, y - 0.015, y + 0.015, 0, 0.3, "B98A6A", bev=0)
rbox("cloth", -0.08, 0.08, -0.33, 0.13, 0.33, 0.3345, "EE6F52", bev=0)
PLAT = cyl("plat", 0.14, 0.336, 0.346, 0.0, -0.1, "FFFFFF", seg=64)
for x in (-0.33, 0.33):
    cyl(f"pl{x}", 0.07, 0.331, 0.34, x, -0.1, "FFFFFF", seg=48)
PIE = empty("pie", Vector((0.22, 0.04, 0.331)))
cyl("pied", 0.06, 0.0, 0.03, 0, 0, "E8A04B", seg=48).parent = PIE
torus("piec", 0.058, 0.01, (0, 0, 0.028), (0, 0, 0), "D9A86C").parent = PIE
for k in range(3):
    ball(f"cand{k}", 0.012, "FFE29A", (-0.25 + k * 0.05, 0.06, 0.392)).data.materials[0] = glow_mat(f"cm{k}", "FFE29A", 4.0)
    cyl(f"cs{k}", 0.008, 0.331, 0.38, -0.25 + k * 0.05, 0.06, "FFFFFF")
TURK = turkey("turk", AWAY)
for x in ():
    rbox(f"ch{x}", x - 0.09, x + 0.09, -0.19, -0.01, 0.16, 0.19, "7FA7D6", bev=0.01)
    for dx in (-0.07, 0.07):
        rbox(f"chl{x}{dx}", x + dx - 0.01, x + dx + 0.01, -0.12, -0.08, 0, 0.16, "5E86B5", bev=0)
FR, FR_A = peg("fr", "EE6F52", Vector((-0.3, 0.24, 0.12)), hair="6B4A3A")
SW, SW_A = peg("sw", "4FA36B", Vector((0.3, 0.24, 0.12)), hair="2F2A28", long_hair=True)
FR.scale = SW.scale = (1.5, 1.5, 1.5)
HL = ball("hl", 0.035, "F2A7B5", AWAY, (1, 0.5, 1))
HR = ball("hr", 0.035, "F2A7B5", AWAY, (1, 0.5, 1))
for h in (HL, HR):
    h.data.materials[0] = glow_mat("heartm" + h.name, "F28FA5", 2.0)
SIGN, STX = sign("sign", Vector((0.0, 0.3, 0.84)), "THANKSGIVING", "NOV 26", "HOME FOR THE BREAK", w=0.5, h=0.26)
BUB = bubble("bub", AWAY, "WE SHOULD TALK", w=0.32)

# ------------------------------------------------------------------ 1 the campus-paper corkboard

O1 = room(1, "CFE8C9", "C9A27E")
rbox("cork", -0.7, 0.7, 0.29, 0.31, 0.12, 0.98, "C9955E", bev=0.01, off=O1)
rbox("corkf", -0.73, 0.73, 0.31, 0.32, 0.09, 1.01, "8A5A3A", bev=0.005, off=O1)
HEADS = ["SURVIVING THE TURKEY DROP", "THE TURKEY DROP IS COMING", "HOME FOR THE BREAK, SINGLE BY SUNDAY",
         "LONG DISTANCE VS. THE TURKEY DROP", "HOW TO SURVIVE A HOLIDAY BREAKUP", "COLD TURKEY: FIRST-YEARS BRACE",
         "THE TURKEY DROP, EXPLAINED", "IS THE TURKEY DROP REAL?"]
PAPERS = []
prnd = random.Random(3)
for k, hd in enumerate(HEADS):
    x = -0.48 + (k % 4) * 0.32 + prnd.uniform(-0.03, 0.03)
    z = 0.74 - (k // 4) * 0.36 + prnd.uniform(-0.03, 0.03)
    root = empty(f"pp{k}", AWAY)
    rbox(f"ppb{k}", -0.13, 0.13, -0.004, 0.004, -0.15, 0.15, "FBF8F0", bev=0.002, parent=root, rough=0.8)
    words = hd.split()
    half = (len(words) + 1) // 2
    for j, part in enumerate((" ".join(words[:half]), " ".join(words[half:]))):
        ht = text(f"pph{k}{j}", part, 0.03, INKC, (0, -0.006, 0.1 - j * 0.04), root, glow=0.35)
        ht.data.size = min(0.032, 0.23 / (max(1, len(part)) * 0.6))
    for j in range(4):
        rbox(f"ppl{k}{j}", -0.1, 0.1 - (0.04 if j == 3 else 0), -0.0055, -0.0045, 0.0 - j * 0.035, 0.01 - j * 0.035,
             "B8B4AA", bev=0, parent=root)
    pin = ball(f"pin{k}", 0.012, ("EE6F52", "7FA7D6", "F6C945", "4FA36B")[k % 4], (0, -0.012, 0.135))
    pin.parent = root
    PAPERS.append((root, O1 + Vector((x, 0.28, z)), prnd.uniform(-0.12, 0.12), k * 0.16))

# ------------------------------------------------------------------ 2 the breakup chart wall

O2 = room(2, "D8DDF6", "E8D9C8")
rbox("chartb", -1.3, 1.3, 0.28, 0.31, 0.05, 1.25, "FFFFFF", bev=0.01, off=O2, rough=0.6)
rbox("axis", -1.2, 1.2, 0.268, 0.278, 0.14, 0.15, INKC, bev=0, off=O2)
text("ctitle", "BREAKUP POSTS ON FACEBOOK, BY WEEK", 0.08, INKC, O2 + Vector((0, 0.262, 1.14)), glow=0.4)
for i, m in enumerate("JFMAMJJASOND"):
    text(f"mo{i}", m, 0.07, INKC, O2 + Vector((-1.15 + (i + 0.5) * 2.3 / 12, 0.262, 0.095)), glow=0.4)

def breakups(w):
    """Stylized weekly shape of the 2008 chart (McCandless and Byron): Valentine's and spring break peaks, a summer
    hump, the pre-Christmas spike, an almost empty Christmas Day. Height 0..1."""
    g = lambda c, s, h: h * math.exp(-((w - c) / s) ** 2)
    base = 0.22 + g(7, 0.8, 0.35) + g(11.5, 1.2, 0.75) + g(28, 6, 0.12) + g(36, 3, 0.1) + g(49.5, 1.0, 0.55)
    if w >= 51:
        base = 0.05
    return min(1.0, base)

BARS = []
for wk in range(52):
    x = -1.15 + (wk + 0.5) * 2.3 / 52
    h = 0.92 * breakups(wk)
    col = "EE6F52" if 48 <= wk <= 50 else ("4FA36B" if wk == 51 else "7FA7D6")
    b = rbox(f"bar{wk}", -0.017, 0.017, -0.02, 0.02, 0, 1.0, col, bev=0.004)
    b.location = O2 + Vector((x, 0.245, 0.15))
    BARS.append((b, h, wk))
TREE = empty("tree", AWAY)
for k, (r, z) in enumerate(((0.05, 0.0), (0.04, 0.035), (0.028, 0.065))):
    cyl(f"tr{k}", r, z, z + 0.05, 0, 0, "4FA36B", r2=0.004).parent = TREE
ball("trs", 0.012, "F6C945", (0, 0, 0.12)).parent = TREE
DESIGNER, DES_A = peg("des", "F6C945", O2 + Vector((-1.45, -0.05, 0)), hair="2F2A28")
DCOUNT, DC_T = sign("dcount", O2 + Vector((1.62, 0.25, 0.8)), "STATUS UPDATES", "0", "SCRAPED, 2008", w=0.5, h=0.3)

# ------------------------------------------------------------------ light, world, camera

w = bpy.data.worlds.new("w")
scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (*hexc("F2D6C2"), 1)
w.node_tree.nodes["Background"].inputs[1].default_value = float(os.environ.get("TK_WORLD", "0.8"))
B.sun("sun", -130, 40, float(os.environ.get("TK_SUN", "2.4")), color=hexc("FFE7CC"), angle_deg=8)
for k, o in enumerate((O0, O1, O2)):
    B.area(f"fill{k}", o + Vector((0.3, -2.2, 1.5)), o + Vector((0.1, 0, 0.35)), 3.0, float(os.environ.get("TK_FILL", "45")),
           color=hexc("FFF0E0"))
B.area("candlek", O0 + Vector((-0.2, -0.2, 0.75)), O0 + Vector((0.0, -0.1, 0.35)), 0.4, 6, color=hexc("FFC98A"))
cam = B.camera(lens=35, fstop=14.0)
cam.data.clip_start, cam.data.clip_end = 0.01, 200.0

def lc(a, b, tg, u, o, lens=35):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "table": lambda u: lc((0.0, -1.35, 0.72), (0.0, -1.2, 0.68), (0.0, -0.05, 0.52), u, O0),
    "name": lambda u: lc((0.0, -1.0, 0.6), (0.05, -0.88, 0.58), (0.0, 0.0, 0.45), u, O0),
    "pie": lambda u: lc((-0.45, -1.0, 0.58), (-0.3, -0.95, 0.55), (0.1, -0.05, 0.45), u, O0),
    "papers": lambda u: lc((0.0, -1.9, 0.58), (0.0, -1.65, 0.56), (0.0, 0.2, 0.56), u, O1),
    "chart": lambda u: lc((0.0, -3.7, 0.7), (0.0, -3.45, 0.68), (0.0, 0.2, 0.62), u, O2),
    "spike": lambda u: lc((0.95, -1.0, 0.55), (0.88, -0.85, 0.55), (0.9, 0.24, 0.5), u, O2),
    "xmas": lambda u: lc((1.16, -0.6, 0.32), (1.14, -0.5, 0.3), (1.13, 0.24, 0.24), u, O2),
    "safe": lambda u: lc((0.35, -1.25, 0.66), (0.2, -1.25, 0.64), (0.0, 0.0, 0.5), u, O0),
    "final": lambda u: lc((0.0, -1.6, 0.85), (0.0, -1.45, 0.8), (0.0, -0.05, 0.52), u, O0),
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

    # ---- table: the turkey is already falling on frame one, lands on the platter, bounces once
    u = min(1.0, (t + 0.12) / 0.4)
    bounce = 0.03 * math.sin(min(1.0, (t - 0.28) / 0.3) * math.pi) if t > 0.28 else 0.0
    TURK.location = Vector((0.0, -0.1, 0.346 + 1.0 * (1 - u) ** 2 + max(0.0, bounce)))
    TURK.rotation_euler = (0, 0, 0.3 * (1 - u))
    dn = t - EV["drop"]
    if 0 <= dn < 0.6:
        TURK.location.z += 0.12 * math.sin(dn / 0.6 * math.pi)
        TURK.rotation_euler = (0, 0, dn * 4)
    # the two of them: hearts over the table, "we should talk", then the hearts split
    sp = t - EV["split"]
    FR.location = Vector((-0.3, 0.24, 0.12))
    SW.location = Vector((0.3, 0.24, 0.12))
    FR.rotation_euler = (0, 0, -0.5 + 0.05 * math.sin(t * 1.3))
    SW.rotation_euler = (0, 0, 0.5 + 0.05 * math.sin(t * 1.1))
    for i, pv in enumerate(FR_A + SW_A):
        pv.rotation_euler = (-0.9 + 0.05 * math.sin(t * 2 + i), 0, 0)
    safe = t >= start_of("safe")
    if safe:
        HL.location = Vector((-0.03, -0.1, 0.62 + 0.01 * math.sin(t * 3)))
        HR.location = Vector((0.03, -0.1, 0.62 + 0.01 * math.sin(t * 3)))
        HL.rotation_euler, HR.rotation_euler = (0, 0.5, 0), (0, -0.5, 0)
        pop(HL, t - start_of("safe"))
        pop(HR, t - start_of("safe"))
    elif t >= EV["hearts"] and sp < 0:
        HL.location = Vector((-0.03, -0.1, 0.62 + 0.01 * math.sin(t * 3)))
        HR.location = Vector((0.03, -0.1, 0.62 + 0.01 * math.sin(t * 3)))
        HL.rotation_euler, HR.rotation_euler = (0, 0.5, 0), (0, -0.5, 0)
        pop(HL, t - EV["hearts"])
        pop(HR, t - EV["hearts"])
    elif sp >= 0:
        v = smooth01(sp / 0.5)
        HL.location = Vector((-0.03 - 0.3 * v, -0.1, 0.62 - 0.22 * v))
        HR.location = Vector((0.03 + 0.3 * v, -0.1, 0.62 - 0.22 * v))
        HL.rotation_euler = (0, 0.5 + 1.2 * v, 0)
        HR.rotation_euler = (0, -0.5 - 1.2 * v, 0)
        k = max(0.001, 1 - smooth01((sp - 1.4) / 0.4))
        HL.scale = HR.scale = (k, k * 0.5, k)
    else:
        hide(HL, HR)
        HL.location = HR.location = AWAY
    if not safe and EV["talk"] <= t < EV["split"] + 1.0:
        BUB.location = Vector((0.2, 0.1, 0.72))
        pop(BUB, t - EV["talk"])
    else:
        hide(BUB)
        BUB.location = AWAY
    if sp >= 0 and not safe:
        SW.rotation_euler = (0, 0, 0.5 + 2.4 * smooth01(sp / 0.6))
    if t < start_of("safe"):
        set_sign(STX, "THANKSGIVING", "NOV 26", "HOME FOR THE BREAK", w=0.5)
    elif t < start_of("final"):
        set_sign(STX, "STILL TOGETHER", "DEC 25", "THE SAFE DAY", w=0.5)
    else:
        set_sign(STX, "THANKSGIVING", "NOV 26", "TURKEY DROP SEASON", w=0.5)

    # ---- corkboard: clippings pin up one after another
    for root, at, rz, delay in PAPERS:
        age = t - EV["papers"] - delay
        if age < 0:
            hide(root)
            root.location = AWAY
            continue
        root.location = at
        root.rotation_euler = (0, rz, 0)
        pop(root, age)

    # ---- chart: bars grow left to right while the counter climbs; a tiny tree on the empty Christmas bar
    ca = t - EV["chart"]
    for b, h, wk in BARS:
        g = smooth01((ca - wk * 0.025) / 0.3) if ca > 0 else 0.0
        b.scale = (1, 1, max(0.001, h * g))
    nn = count(t, EV["chart"], 1.5, 10000)
    set_sign(DC_T, big=f"{nn:,}", w=0.5)
    DESIGNER.rotation_euler = (0, 0, 0.3)
    DES_A[1].rotation_euler = (0, -2.2 + 0.15 * math.sin(t * 3), 0)
    if t >= EV["xmas"]:
        TREE.location = O2 + Vector((1.128, 0.22, 0.2))
        pop(TREE, t - EV["xmas"], 1.3)
    else:
        hide(TREE)
        TREE.location = AWAY

B.render_settings(FPS, samples=int(os.environ.get("YT_SAMPLES", "24")), motion_blur=0.0)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1) / FPS)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
