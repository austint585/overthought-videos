"""Pastel toy kit, "The Hangry Friend": toy peg people. Sets: a living room at sunset (your friend on the couch under a
rain cloud with a tiny lightning bolt, shaking and rumbling; a snack flies in and the cloud becomes a sun) and a computer
lab (six students in three pairs: ate first, skipped food, skipped food and wrote about feelings; progress bars crawl, every
screen crashes, a researcher walks in and blames them). Shots, timed by render_hangry.py: couch, lab, task, crash, blame,
hungry, write, snack, final. Helpers copied from barista_scene.py.

blender -b --factory-startup -P hangry_scene.py -- timing.json out_dir MODE   (MODE: "all" or 1-based frame list)
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






def cloud(name, s=1.0, dark="8E97A6"):
    root = empty(name, AWAY)
    for k, (x, z, r) in enumerate(((-0.06, 0, 0.05), (0.0, 0.025, 0.065), (0.07, 0.005, 0.05), (0.03, -0.015, 0.045))):
        ball(f"{name}{k}", r * s, dark, (x * s, 0, z * s), (1, 0.7, 1)).parent = root
    return root

def sun(name, s=1.0):
    root = empty(name, AWAY)
    b = ball(name + "b", 0.05 * s, "FFD24A", (0, 0, 0), (1, 0.5, 1))
    b.data.materials[0] = glow_mat(name + "m", "FFD24A", 2.5)
    b.parent = root
    for k in range(8):
        a = k / 8 * 2 * math.pi
        r = rbox(f"{name}r{k}", -0.008 * s, 0.008 * s, -0.004, 0.004, 0.065 * s, 0.095 * s, "FFD24A", bev=0, parent=root)
        r.rotation_euler = (0, a, 0)
        r.data.materials[0] = b.data.materials[0]
    return root

def bolt(name):
    root = empty(name, AWAY)
    m = glow_mat(name + "m", "FFE066", 4.0)
    for k, (x, z, rz) in enumerate(((0.0, 0.0, 0.5), (0.02, -0.04, -0.5), (0.0, -0.08, 0.5))):
        b = rbox(f"{name}{k}", -0.006, 0.006, -0.004, 0.004, -0.025, 0.025, "FFE066", bev=0, parent=root)
        b.location = (x, 0, z)
        b.rotation_euler = (0, rz, 0)
        b.data.materials[0] = m
    return root

# ------------------------------------------------------------------ 0 the living room at sunset
O0 = Vector()
rbox("floor0", -3, 3, -4, 0.32, -0.05, 0, "C9A27E", bev=0)
rbox("wall0", -3, 3, 0.32, 0.4, 0, 3, "F7D9C4", bev=0)
rbox("skirt0", -3, 3, 0.305, 0.32, 0, 0.03, "FFFFFF", bev=0)
rbox("winf0", -0.75, -0.35, 0.305, 0.325, 0.55, 0.95, "FFFFFF", bev=0.006)
rbox("wing0", -0.73, -0.37, 0.298, 0.304, 0.57, 0.93, "F2A07B", bev=0).data.materials[0] = glow_mat("dusk", "F5A47E", 0.9)
rbox("seat", -0.42, 0.42, -0.14, 0.16, 0.06, 0.19, "7FA7D6", bev=0.02)
rbox("back", -0.42, 0.42, 0.13, 0.27, 0.06, 0.46, "7FA7D6", bev=0.025)
for x in (-0.48, 0.42):
    rbox(f"arm{x}", x, x + 0.06, -0.14, 0.27, 0.06, 0.3, "6A93C4", bev=0.02)
rbox("base0", -0.48, 0.48, -0.12, 0.25, 0.0, 0.06, "5E86B5", bev=0.01)
rbox("ctab", -0.28, 0.28, -0.52, -0.32, 0.12, 0.15, "D79A5F", bev=0.008)
for x in (-0.25, 0.25):
    rbox(f"ctl{x}", x - 0.012, x + 0.012, -0.44, -0.4, 0, 0.12, "B98A6A", bev=0)
cyl("bowl", 0.06, 0.15, 0.18, 0.1, -0.42, "FFFFFF", r2=0.045, seg=40)
FRI, FRI_A = peg("fri", YOU_C, Vector((0.0, 0.0, 0.19)), hair="6B4A3A")
FRI.scale = (1.5, 1.5, 1.5)
DIN, DIN_T = sign("din", Vector((0.36, 0.3, 0.88)), "DINNER IN", "47 MIN", "", w=0.36, h=0.22)
CLOUD = cloud("cl", 1.6)
DROPS = [ball(f"dr{k}", 0.008, "7FB3E6", AWAY, (1, 1, 1.8)) for k in range(7)]
BOLT = bolt("bolt")
SUN = sun("sun0", 1.4)
SAND = empty("sand", AWAY)
rbox("sb1", -0.05, 0.05, -0.035, 0.035, 0.0, 0.015, "F1D29A", bev=0.006, parent=SAND)
rbox("sb2", -0.052, 0.052, -0.037, 0.037, 0.015, 0.024, "7CC36B", bev=0.003, parent=SAND)
rbox("sb3", -0.05, 0.05, -0.035, 0.035, 0.024, 0.04, "F1D29A", bev=0.006, parent=SAND)

# ------------------------------------------------------------------ 1 the computer lab
O1 = room(1, "DDE6F2", "BFC6D1")
XS = [-1.05, -0.63, -0.21, 0.21, 0.63, 1.05]
STU, SCREENS, ERRS, BARS = [], [], [], []
srnd = random.Random(8)
blue = glow_mat("scr", "8FC3F0", 1.2)
red = glow_mat("err", "E8584B", 1.6)
for k, x in enumerate(XS):
    o = O1 + Vector((x, 0, 0))
    rbox(f"dk{k}", -0.17, 0.17, -0.1, 0.1, 0.18, 0.205, "E8B57A", bev=0.004, off=o)
    for dx in (-0.15, 0.15):
        rbox(f"dkl{k}{dx}", dx - 0.01, dx + 0.01, -0.08, 0.08, 0, 0.18, "B98A6A", bev=0, off=o)
    mon = empty(f"mon{k}", o + Vector((0.08, -0.02, 0.205)))
    mon.rotation_euler = (0, 0, 0.35)
    rbox(f"mb{k}", -0.075, 0.075, -0.008, 0.008, 0.03, 0.135, "3A4150", bev=0.006, parent=mon)
    rbox(f"mst{k}", -0.012, 0.012, -0.01, 0.01, 0.0, 0.03, "3A4150", bev=0, parent=mon)
    sc = rbox(f"ms{k}", -0.066, 0.066, -0.0095, -0.0085, 0.038, 0.127, "8FC3F0", bev=0, parent=mon)
    sc.data.materials[0] = blue
    er = rbox(f"me{k}", -0.066, 0.066, -0.0105, -0.0095, 0.038, 0.127, "E8584B", bev=0, parent=mon)
    er.data.materials[0] = red
    et = text(f"met{k}", "ERROR", 0.022, "FFFFFF", (0, -0.0115, 0.083), mon, glow=1.5)
    br = rbox(f"mbar{k}", 0.0, 0.11, -0.0102, -0.0098, 0.05, 0.06, "FFFFFF", bev=0, parent=mon)
    br.location = (-0.055, 0, 0)
    SCREENS.append(sc)
    ERRS.append((er, et))
    BARS.append(br)
    p, a = peg(f"stu{k}", ("F6C945", "9B7FD6", "EE6F52", "4FA36B", "F29C9C", "7FB9A8")[k], o + Vector((-0.03, 0.17, 0.0)),
               hair=srnd.choice(("2F2A28", "6B4A3A", "C9955E")), long_hair=k % 2 == 0)
    for pv in a:
        pv.rotation_euler = (-1.1, 0, 0)
    STU.append((p, a))
LAB, LAB_T = sign("lab", O1 + Vector((0, 0.3, 1.05)), "2018 STUDY", "200+", "STUDENTS", w=0.5, h=0.3)
S_ATE, _ = sign("sate", AWAY, "", "ATE FIRST", "", w=0.62, h=0.16)
S_SKIP, _ = sign("sskip", AWAY, "", "SKIPPED FOOD", "", w=1.2, h=0.16)
S_WROTE, _ = sign("swrote", AWAY, "", "WROTE FEELINGS", "FIRST", w=0.62, h=0.18)
RES, RES_A = peg("res", "F4F1E8", AWAY, hair="8A8A8A")
RES.scale = (1.15,) * 3
CLIP = rbox("clip", -0.02, 0.02, -0.004, 0.004, -0.03, 0.03, "B98A6A", bev=0.003)
B_BLAME = bubble("bbl", AWAY, "YOU BROKE IT", w=0.32)
B_STR = bubble("bstr", AWAY, "STRESSED", w=0.24)
B_HAT = bubble("bhat", AWAY, "HATEFUL", w=0.22)
S_HARSH, _ = sign("sharsh", AWAY, "RATED", "HARSH", "", w=0.3, h=0.18)
MCLOUDS = [cloud(f"mc{k}", 0.8) for k in range(2)]
NOTES_B = [rbox(f"nb{k}", -0.03, 0.03, -0.004, 0.004, -0.04, 0.04, "F6C945", bev=0.004) for k in range(2)]
SUNS = [sun(f"su{k}", 0.6) for k in range(2)]
B_FINE = bubble("bfine", AWAY, "FINE", w=0.16)

# ------------------------------------------------------------------ light, world, camera
w = bpy.data.worlds.new("w")
scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (*hexc("F2E2D6"), 1)
w.node_tree.nodes["Background"].inputs[1].default_value = float(os.environ.get("TK_WORLD", "0.8"))
B.sun("sun", -130, 40, float(os.environ.get("TK_SUN", "2.4")), color=hexc("FFE7CC"), angle_deg=8)
for k, o in enumerate((O0, O1)):
    B.area(f"fill{k}", o + Vector((0.3, -2.4, 1.6)), o + Vector((0.1, 0.2, 0.4)), 3.0, float(os.environ.get("TK_FILL", "45")),
           color=hexc("FFF0E0"))
cam = B.camera(lens=26, fstop=14.0)
cam.data.clip_start, cam.data.clip_end = 0.01, 200.0

def lc(a, b, tg, u, o, lens=26):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "couch": lambda u: lc((0.05, -1.45, 0.72), (0.0, -1.32, 0.68), (0.0, 0.0, 0.56), u, O0),
    "lab": lambda u: lc((0.0, -2.25, 0.85), (0.0, -2.05, 0.8), (0.0, 0.0, 0.4), u, O1, 24),
    "task": lambda u: lc((-0.25, -1.05, 0.5), (-0.15, -0.95, 0.48), (-0.1, 0.0, 0.3), u, O1, 28),
    "crash": lambda u: lc((0.02, -0.5, 0.36), (0.0, -0.44, 0.35), (-0.13, 0.0, 0.29), u, O1, 30),
    "blame": lambda u: lc((0.3, -1.6, 0.62), (0.25, -1.45, 0.6), (0.22, 0.0, 0.36), u, O1),
    "hungry": lambda u: lc((0.22, -1.2, 0.6), (0.15, -1.1, 0.58), (0.15, 0.0, 0.4), u, O1, 25),
    "write": lambda u: lc((0.9, -1.15, 0.58), (0.84, -1.05, 0.56), (0.84, 0.0, 0.38), u, O1, 28),
    "snack": lambda u: lc((0.3, -1.0, 0.62), (0.22, -0.92, 0.62), (0.05, 0.0, 0.6), u, O0, 28),
    "final": lambda u: lc((0.0, -1.55, 0.74), (0.0, -1.42, 0.7), (0.0, 0.0, 0.56), u, O0),
}

def shot_at(t):
    k = max([0] + [i for i, (s, _) in enumerate(SHOTS) if t >= s - 1e-6])
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    cut = max(0.0, min(1.0, (t - SHOTS[k][0]) / max(1e-6, t1 - SHOTS[k][0])))
    return SHOTS[k][1], cut

def start_of(n):
    return next(s for s, m in SHOTS if m == n)

def place(ob, at, age, s=1.0):
    if age < 0:
        hide(ob)
        ob.location = AWAY
    else:
        ob.location = at
        pop(ob, age, s)

def apply_state(t):
    name, cut = shot_at(t)
    loc, tg, lens = CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    cam.data.dof.use_dof = False

    # ---- couch: a rain cloud over your friend, shaking and rumbling; the snack turns it into a sun
    happy = EV["feel"] <= t < start_of("final")
    head = Vector((0.0, 0.0, 0.19 + 0.52))
    shake = 0.0 if happy else 0.006 * math.sin(t * 55)
    FRI.location = Vector((shake, 0.0, 0.19))
    rum = 1 + (0.0 if happy else 0.05 * max(0.0, math.sin(t * 9)) ** 4)
    FRI.scale = (1.5 * rum, 1.5 * rum, 1.5)
    FRI_A[0].rotation_euler = (-0.5 + 0.1 * math.sin(t * 3), 0, 0)
    sa = t - EV["snack"]
    FRI_A[1].rotation_euler = (-1.3 if 0 <= sa and t < start_of("final") else -0.5, 0, 0)
    mins = 47 - int(2 * smooth01(t / DUR))
    set_sign(DIN_T, big=f"{mins} MIN", w=0.36)
    if happy:
        hide(CLOUD, BOLT)
        CLOUD.location = BOLT.location = AWAY
        for d in DROPS:
            hide(d)
            d.location = AWAY
        place(SUN, head + Vector((0.0, -0.05, 0.22)), t - EV["feel"])
        SUN.rotation_euler = (0, t * 0.8, 0)
    else:
        hide(SUN)
        SUN.location = AWAY
        CLOUD.location = head + Vector((0.0, -0.03, 0.22 + 0.01 * math.sin(t * 2)))
        CLOUD.scale = (1.0 + (0.25 if t >= EV["cloud"] else 0.0),) * 3
        for k, d in enumerate(DROPS):
            ph = (t * 1.3 + k / len(DROPS)) % 1.0
            d.location = head + Vector((-0.09 + k * 0.03, -0.03, 0.17 - 0.2 * ph))
            d.scale = (1, 1, 1)
        if math.sin(t * 4.3) > 0.85 or EV["cloud"] <= t < EV["cloud"] + 0.25:
            BOLT.location = head + Vector((0.02, -0.06, 0.15))
            BOLT.scale = (1.4,) * 3
        else:
            hide(BOLT)
            BOLT.location = AWAY
    if 0 <= sa and t < start_of("final"):
        u = smooth01(sa / 0.5)
        SAND.location = Vector((-0.8 + 0.92 * u, -0.15, 0.42 + 0.25 * math.sin(u * math.pi)))
        SAND.rotation_euler = (0, 6.0 * (1 - u), 0)
        SAND.scale = (1.4,) * 3
    else:
        hide(SAND)
        SAND.location = AWAY

    # ---- lab: groups get signs, progress bars crawl, every screen crashes, the researcher walks in and blames them
    place(S_ATE, O1 + Vector((-0.84, 0.25, 0.62)), t - EV["eat"] if t < start_of("task") else -1)
    place(S_SKIP, O1 + Vector((0.42, 0.25, 0.62)), t - EV["skip"] if t < start_of("task") else -1)
    place(S_WROTE, O1 + Vector((0.84, 0.22, 0.56)), t - EV["wrote"] if t < start_of("snack") else -1)
    prog = smooth01((t - EV["type"]) / 2.0) if t >= EV["type"] else 0.0
    crashed = t >= EV["crash"]
    for k, br in enumerate(BARS):
        br.scale = (max(0.001, min(0.97, prog * (0.9 + 0.07 * k / 5))) if not crashed else 0.001, 1, 1)
    for er, et in ERRS:
        if crashed:
            er.scale = et.scale = (1, 1, 1)
        else:
            hide(er, et)
    for k, (p, a) in enumerate(STU):
        typing = EV["type"] <= t < EV["crash"]
        for j, pv in enumerate(a):
            pv.rotation_euler = (-1.1 + (0.12 * math.sin(t * 22 + j * 2 + k) if typing else 0.0), 0, 0)
        p.rotation_euler = (0, 0, 0.12 if crashed and k in (2, 3) else 0.0)
    wa = t - EV["walk"]
    if wa >= 0:
        u = smooth01(wa / 0.9)
        RES.location = O1 + Vector((1.7 - 1.25 * u, -0.33, 0.012 * abs(math.sin(wa * 10)) * (1 - u)))
        RES.rotation_euler = (0, 0, 2.6)
        RES_A[0].rotation_euler = (-1.7 if t >= EV["blame"] else -0.3, 0, 0)
        RES_A[1].rotation_euler = (-0.9, 0, 0)
        CLIP.location = RES.location + Vector((-0.06, 0.05, 0.17))
        CLIP.rotation_euler = (0, 0, 2.6)
    else:
        RES.location = CLIP.location = AWAY
    place(B_BLAME, O1 + Vector((0.5, -0.38, 0.62)), t - EV["blame"] if t < start_of("hungry") else -1)
    place(B_STR, O1 + Vector((-0.15, 0.05, 0.58)), t - EV["stressed"] if t < start_of("write") else -1)
    place(B_HAT, O1 + Vector((0.03, 0.05, 0.72)), t - EV["hateful"] if t < start_of("write") else -1)
    place(S_HARSH, O1 + Vector((0.3, 0.0, 0.55)), t - EV["harsh"] if t < start_of("write") else -1)
    for k, mc in enumerate(MCLOUDS):
        place(mc, O1 + Vector((XS[2 + k] - 0.03, 0.15, 0.48)), t - EV["stressed"], 1.0)
    for k, (nb, su) in enumerate(zip(NOTES_B, SUNS)):
        place(nb, O1 + Vector((XS[4 + k] - 0.15, 0.08, 0.25)), t - EV["wrote"])
        place(su, O1 + Vector((XS[4 + k] + 0.12, 0.1, 0.4)), t - EV["fine"])
        su.rotation_euler = (0, t, 0)
    place(B_FINE, O1 + Vector((0.84, -0.05, 0.62)), t - EV["fine"])

B.render_settings(FPS, samples=int(os.environ.get("YT_SAMPLES", "24")), motion_blur=0.0)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1) / FPS)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
