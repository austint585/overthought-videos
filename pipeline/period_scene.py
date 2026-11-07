"""Pastel toy kit, "The Period Text": toy peg people. Sets: a kitchen counter in the morning (you with your phone under a
giant chat; the reply "Okay" lands with a red period that drops and rolls across the counter) and a psychology test room
(two wall screens with the exchange, words cycling Okay, Sure, Yeah, Yup, a period on one side only, SINCERE meters, an
easel with two handwritten notes, students on stools). Shots, timed by render_period.py: kitchen, room, screen, split,
meter, note, back, final. Helpers copied from hangry_scene.py.

blender -b --factory-startup -P period_scene.py -- timing.json out_dir MODE   (MODE: "all" or 1-based frame list)
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





def chat(name, body, panel, ink, w, h, at, dot=False, size=0.07):
    """A rounded chat bubble facing -y; with dot=True a red ball sits after the text as the period."""
    root = empty(name, at)
    rbox(name + "p", -w / 2, w / 2, -0.012, 0.012, -h / 2, h / 2, panel, bev=0.03, parent=root, rough=0.4)
    tx = text(name + "x", body, size, ink, (-0.015 if dot else 0.0, -0.016, -0.004), root, glow=0.5)
    d = None
    if dot:
        d = ball(name + "d", size * 0.2, "E8584B", (0, 0, 0))
        d.data.materials[0] = glow_mat(name + "dm", "E8584B", 1.2)
        d.parent = root
        d.location = (-0.015 + len(body) * size * 0.3 + size * 0.22, -0.02, -0.004 - size * 0.28)
    return root, tx, d

def set_text(tx, body):
    if tx.data.body != body:
        tx.data.body = body

INK2, BLUEB, GREYB = "2F3843", "3566A8", "ECEAE6"

# ------------------------------------------------------------------ 0 the kitchen in the morning
O0 = Vector()
rbox("floor0", -3, 3, -4, 0.32, -0.05, 0, "C9A27E", bev=0)
rbox("wall0", -3, 3, 0.32, 0.4, 0, 3, "DFF0E6", bev=0)
for x in (-0.95, -0.55, 0.55, 0.95):
    rbox(f"cab{x}", x - 0.19, x + 0.19, 0.17, 0.32, 0.95, 1.3, "F4F1E8", bev=0.01)
    rbox(f"knob{x}", x - 0.012, x + 0.012, 0.155, 0.17, 0.98, 1.0, "B98A6A", bev=0.003)
rbox("win0f", -0.3, 0.3, 0.3, 0.32, 0.55, 0.95, "FFFFFF", bev=0.006)
rbox("win0g", -0.28, 0.28, 0.296, 0.302, 0.57, 0.93, "BFE3F5", bev=0).data.materials[0] = glow_mat("morning", "CFEAF7", 1.3)
rbox("ctr0", -0.8, 0.8, -0.22, 0.1, 0.0, 0.2, "7FB9A8", bev=0.01)
rbox("top0", -0.82, 0.82, -0.24, 0.11, 0.2, 0.225, "F4F1E8", bev=0.006, rough=0.35)
cyl("mug0", 0.035, 0.225, 0.3, -0.45, -0.1, "EE6F52", seg=32, bev=0.004)
cyl("cof0", 0.03, 0.29, 0.296, -0.45, -0.1, "6B4A3A", seg=32)
rbox("toast0", 0.38, 0.6, -0.12, 0.02, 0.225, 0.36, "C8CDD6", bev=0.02)
for dx in (0.44, 0.54):
    rbox(f"slot{dx}", dx - 0.03, dx + 0.03, -0.06, -0.04, 0.355, 0.362, "2F3843", bev=0)
YOU, YOU_A = peg("you", "7FA7D6", Vector((0.0, 0.18, 0.0)), hair="2F2A28")
YOU.scale = (1.5, 1.5, 1.5)
PHONE = rbox("ph", -0.022, 0.022, -0.004, 0.004, -0.04, 0.04, "2F3843", bev=0.004)
PHONE.parent = YOU_A[1]
PHONE.location = (0.0, -0.02, -0.115)
PHONE.rotation_euler = (1.25, 0, 0)
pscr = rbox("phs", -0.018, 0.018, -0.0055, -0.0045, -0.034, 0.034, "8FC3F0", bev=0)
pscr.parent = PHONE
pscr.data.materials[0] = glow_mat("phg", "8FC3F0", 2.0)
Q0, _, _ = chat("q0", "food later?", BLUEB, "FFFFFF", 0.4, 0.11, Vector((-0.12, -0.05, 0.9)), size=0.055)
R0, R0_T, R0_D = chat("r0", "Okay", GREYB, INK2, 0.3, 0.13, Vector((0.12, -0.05, 0.74)), dot=True, size=0.075)
ROLL = ball("roll", 0.015, "E8584B", AWAY)
ROLL.data.materials[0] = glow_mat("rollm", "E8584B", 1.2)

# ------------------------------------------------------------------ 1 the psychology test room
O1 = room(1, "E3DDF2", "C9CFDA")
SCR = {}
for key, x in (("L", -0.32), ("R", 0.32)):
    o = O1 + Vector((x, 0.28, 0.78))
    rbox(f"scr{key}", -0.29, 0.29, -0.015, 0.015, -0.24, 0.24, "2F3843", bev=0.012, off=o)
    rbox(f"scg{key}", -0.27, 0.27, -0.018, -0.016, -0.22, 0.22, "F4F1E8", bev=0, off=o).data.materials[0] = glow_mat(
        f"scgm{key}", "F7F5EF", 0.9)
    q, _, _ = chat(f"q{key}", "come tonight?", BLUEB, "FFFFFF", 0.32, 0.08, o + Vector((-0.08, -0.03, 0.11)), size=0.042)
    r, rt, rd = chat(f"r{key}", "Okay", GREYB, INK2, 0.24, 0.1, o + Vector((0.09, -0.03, -0.03)), dot=True, size=0.06)
    bar_bg = rbox(f"mbg{key}", -0.22, 0.22, -0.02, -0.018, -0.205, -0.175, "D8D4CC", bev=0, off=o)
    bar = rbox(f"mbar{key}", 0.0, 0.44, -0.024, -0.021, -0.205, -0.175, "4FA36B", bev=0)
    bar.location = o + Vector((-0.22, 0, 0))
    lab = text(f"mlab{key}", "SINCERE", 0.026, INK2, o + Vector((0, -0.026, -0.145)), glow=0.4)
    SCR[key] = {"o": o, "q": q, "r": r, "rt": rt, "rd": rd, "bar": bar, "lab": lab, "bg": bar_bg}
S_N, S_N_T = sign("sn", AWAY, "STUDENTS", "126", "", w=0.34, h=0.22)
S_TXT, _ = sign("stxt", AWAY, "", "TEXT", "", w=0.3, h=0.13)
EASEL = empty("easel", O1 + Vector((1.15, 0.05, 0.0)))
for dx in (-0.15, 0.15):
    leg = rbox(f"el{dx}", -0.01, 0.01, -0.01, 0.01, 0, 0.8, "B98A6A", bev=0, parent=EASEL)
    leg.location = (dx, 0, 0)
    leg.rotation_euler = (0, -0.12 if dx > 0 else 0.12, 0)
rbox("eboard", -0.2, 0.2, -0.03, -0.01, 0.3, 0.85, "E8B57A", bev=0.006, parent=EASEL)
NOTES2 = []
for k, (z, body, d) in enumerate(((0.69, "Okay", True), (0.46, "Okay", False))):
    p = rbox(f"np{k}", -0.17, 0.17, -0.034, -0.03, z - 0.09, z + 0.09, "FFFBEE", bev=0.003, parent=EASEL)
    t_ = text(f"nt{k}", body, 0.07, "3A4150", (-0.02 if d else 0.0, -0.045, z + 0.01), EASEL, glow=0.4)
    t_.rotation_euler = (math.pi / 2, -0.06, 0)
    if d:
        dd = ball(f"nd{k}", 0.011, "3A4150", (0.08, -0.04, z - 0.012))
        dd.parent = EASEL
    nb = rbox(f"nbar{k}", 0.0, 0.26, -0.036, -0.034, -0.012, 0.012, "4FA36B", bev=0, parent=EASEL)
    nb.location = (-0.13, 0, z - 0.06)
    NOTES2.append(nb)
S_SAME, _ = sign("ssame", AWAY, "", "SAME", "", w=0.24, h=0.12)
S_LESS, _ = sign("sless", AWAY, "RATED", "LESS SINCERE", "", w=0.5, h=0.2)
STU = []
srnd = random.Random(3)
for k, x in enumerate((-0.75, -0.42, -0.1, 0.22, 0.54)):
    st = cyl(f"stool{k}", 0.05, 0.0, 0.12, x, -0.42, "B98A6A", seg=24, off=O1)
    p, a = peg(f"stu{k}", ("F6C945", "9B7FD6", "EE6F52", "4FA36B", "F29C9C")[k], O1 + Vector((x, -0.42, 0.12)),
               hair=srnd.choice(("2F2A28", "6B4A3A", "C9955E")), long_hair=k % 2 == 1)
    p.rotation_euler = (0, 0, math.pi)
    STU.append((p, a))

# ------------------------------------------------------------------ light, world, camera
w = bpy.data.worlds.new("w")
scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (*hexc("F2E2D6"), 1)
w.node_tree.nodes["Background"].inputs[1].default_value = float(os.environ.get("TK_WORLD", "0.8"))
B.sun("sun", -130, 40, float(os.environ.get("TK_SUN", "2.4")), color=hexc("FFF1DD"), angle_deg=8)
for k, o in enumerate((O0, O1)):
    B.area(f"fill{k}", o + Vector((0.3, -2.4, 1.6)), o + Vector((0.1, 0.2, 0.4)), 3.0, float(os.environ.get("TK_FILL", "45")),
           color=hexc("FFF0E0"))
cam = B.camera(lens=26, fstop=14.0)
cam.data.clip_start, cam.data.clip_end = 0.01, 200.0

def lc(a, b, tg, u, o, lens=26):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "kitchen": lambda u: lc((0.03, -1.25, 0.62), (0.0, -1.12, 0.6), (0.0, 0.0, 0.58), u, O0),
    "room": lambda u: lc((0.0, -1.9, 0.75), (0.0, -1.75, 0.72), (0.0, 0.2, 0.6), u, O1, 22),
    "screen": lambda u: lc((-0.32, -0.85, 0.8), (-0.32, -0.75, 0.79), (-0.32, 0.28, 0.76), u, O1, 28),
    "split": lambda u: lc((0.0, -1.45, 0.92), (0.0, -1.38, 0.9), (0.0, 0.28, 0.8), u, O1, 22),
    "meter": lambda u: lc((0.03, -1.5, 0.95), (0.0, -1.42, 0.93), (0.0, 0.28, 0.85), u, O1, 22),
    "note": lambda u: lc((1.12, -0.85, 0.66), (1.12, -0.75, 0.64), (1.13, 0.05, 0.6), u, O1, 28),
    "back": lambda u: lc((-0.08, -0.82, 0.46), (-0.12, -0.75, 0.44), (-0.15, -0.05, 0.3), u, O0, 28),
    "final": lambda u: lc((0.03, -1.25, 0.62), (0.0, -1.12, 0.6), (0.0, 0.0, 0.58), u, O0),
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

    # ---- kitchen: the reply lands on frame one, the period drops on "period" and rolls; you flinch
    final = t >= start_of("final")
    loop_t = t - start_of("final") if final else t
    R0.location = Vector((0.12, -0.05, 0.74))
    pop(R0, loop_t + 0.12)
    drop_t = EV["period"] if not final else 1e9
    dt = t - drop_t
    if dt < 0:
        R0_D.scale = (1, 1, 1)
        ROLL.location = AWAY
    else:
        R0_D.scale = (0.001,) * 3
        sx, sy, sz = 0.12 + R0_D.location.x, -0.07, 0.74 + R0_D.location.z
        if dt < 0.45:
            u = dt / 0.45
            ROLL.location = Vector((sx, sy, sz - (sz - 0.24) * u * u))
        else:
            u = smooth01((dt - 0.45) / 2.2)
            bounce = 0.03 * abs(math.sin((dt - 0.45) * 9)) * max(0.0, 1 - (dt - 0.45) / 0.8)
            ROLL.location = Vector((sx - 0.55 * u, sy - 0.05 * u, 0.24 + bounce))
        ROLL.scale = (1.6, 1.6, 1.6)
    fl = 0.0
    for t0 in (0.0 if not final else -9, EV["felt"]):
        a = loop_t - t0 if t0 == 0.0 else t - t0
        if 0 <= a < 0.5:
            fl = math.sin(a / 0.5 * math.pi)
    YOU.location = Vector((0.0, 0.18 + 0.03 * fl, 0.0))
    YOU.rotation_euler = (-0.15 * fl, 0, 0.012 * math.sin(t * 40) * fl)
    YOU_A[1].rotation_euler = (-1.25, 0, 0)
    YOU_A[0].rotation_euler = (-0.3 - 0.8 * fl, 0, 0)
    look = t >= EV["roll"] and not final
    YOU.rotation_euler.x += 0.35 if look else 0.0

    # ---- test room: screens show the exchange, words cycle, then the split, the meters and the handwritten notes
    place(S_N, O1 + Vector((0.0, 0.22, 1.18)), t - EV["n126"] if t < start_of("screen") else -1)
    words = [("w1", "Okay"), ("w2", "Sure"), ("w3", "Yeah"), ("w4", "Yup")]
    cur = "Okay"
    for k, wd in words:
        if t >= EV[k]:
            cur = wd
    if t >= EV["dot"]:
        cur = "Okay"
    for key in ("L", "R"):
        s = SCR[key]
        set_text(s["rt"], cur)
        s["rd"].location.x = -0.015 + len(cur) * 0.06 * 0.3 + 0.06 * 0.22
        on = key == "L" or t >= EV["none"] - 0.3
        place(s["q"], s["o"] + Vector((-0.08, -0.03, 0.11)), (t - EV["ask"]) if on and t >= start_of("screen") else
              (t - EV["texts"] if on and t >= EV["texts"] else -1))
        rstart = EV["w1"] if t < start_of("split") else start_of("split")
        place(s["r"], s["o"] + Vector((0.09, -0.03, -0.03)), (t - rstart) if on and t >= rstart else
              (t - EV["texts"] - 0.3 if on and t >= EV["texts"] + 0.3 else -1))
        with_dot = key == "L" and t >= EV["dot"]
        s["rd"].scale = (1, 1, 1) if with_dot else (0.001,) * 3
        if key == "L" and EV["w1"] <= t < EV["dot"]:
            s["r"].scale = (1 + 0.15 * max(0.0, 1 - min(abs(t - EV[k]) for k, _ in words) / 0.15),) * 3
        mshow = t >= EV["rated"]
        lvl = 0.88 if key == "R" else (0.88 - 0.5 * smooth01((t - EV["less"]) / 0.7) if t >= EV["less"] else 0.88)
        for ob in (s["bg"], s["lab"]):
            ob.scale = (1, 1, 1) if mshow else (0.001,) * 3
        s["bar"].scale = (max(0.001, lvl), 1, 1) if mshow else (0.001,) * 3
        if key == "L":
            s["bar"].data.materials[0] = mat("E8584B" if t >= EV["less"] else "4FA36B")
    for k, nb in enumerate(NOTES2):
        nb.scale = (1, 1, 1) if t >= EV["same"] - 0.2 else (0.001, 1, 1)
    place(S_SAME, O1 + Vector((1.2, -0.02, 0.575)), t - EV["same"] if t < start_of("back") else -1)
    S_SAME.rotation_euler = (0, 0.18, 0)
    place(S_LESS, O1 + Vector((-0.32, 0.2, 1.17)), t - EV["less"] if t < start_of("note") else -1)
    for k, (p, a) in enumerate(STU):
        for j, pv in enumerate(a):
            pv.rotation_euler = (-0.25 + 0.08 * math.sin(t * 2 + k + j), 0, 0)
        p.location.z = 0.12 + (0.015 * abs(math.sin(t * 7 + k)) if EV["less"] <= t < EV["less"] + 0.6 else 0.0)

B.render_settings(FPS, samples=int(os.environ.get("YT_SAMPLES", "24")), motion_blur=0.0)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1) / FPS)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
