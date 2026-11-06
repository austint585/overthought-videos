"""Pastel toy kit in daylight, "The Christmas Music Friend": toy peg people in a peach living room (couch, coffee table with a
jack-o'-lantern and a phone, a smart speaker on a sideboard, a half-decorated tree, a wall sign that counts plays) and a lilac
dining corner (a toy turkey, a THANKSGIVING sign, a 54-square calendar). Shots, timed by render_xmas.py: living, pumpkin (a
Santa hat lands on it), phone (IT'S TIME!!! at 12:00), counter (713,000), replay (the friend presses the speaker button),
turkey (bauble on the tail, the head turns to camera), calendar (54 DAYS), ears (pillow over your ears), total (19,359),
final (PLAY 1,792 OF 19,359). Helpers copied from sleep_scene.py.

blender -b --factory-startup -P xmas_scene.py -- timing.json out_dir MODE   (MODE: "all" or 1-based frame list)
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

# ------------------------------------------------------------------ 0 living room in daylight

WALL0, FLOOR0 = "F6D2C4", "E2C29A"
rbox("floor0", -3, 3, -4, 0.32, -0.05, 0, FLOOR0, bev=0)
rbox("wall0", -3, 3, 0.32, 0.4, 0, 3, WALL0, bev=0)
rbox("skirt0", -3, 3, 0.305, 0.32, 0, 0.03, "FFFFFF", bev=0)
rbox("rug0", -0.55, 0.55, -0.6, 0.05, 0.0005, 0.004, "BFE3D6", bev=0)
# window with sky and a cloud
rbox("winf0", -0.42, 0.02, 0.305, 0.325, 0.42, 0.8, "FFFFFF", bev=0.006)
rbox("wing0", -0.4, 0.0, 0.298, 0.304, 0.44, 0.78, "A9D8F5", bev=0).data.materials[0] = glow_mat("sky0", "A9D8F5", 1.2)
for k, (x, z, r) in enumerate(((-0.28, 0.68, 0.04), (-0.23, 0.69, 0.05), (-0.18, 0.675, 0.035))):
    ball(f"cloud{k}", r, "FFFFFF", (x, 0.296, z), (1.3, 0.2, 0.8)).data.materials[0] = glow_mat(f"cl{k}", "FFFFFF", 1.5)
rbox("winbar0", -0.206, -0.194, 0.292, 0.298, 0.44, 0.78, "FFFFFF", bev=0)
# couch on the left
rbox("cbase", -0.9, -0.36, -0.12, 0.2, 0, 0.09, "8FB6D9", bev=0.02)
rbox("cback", -0.9, -0.36, 0.12, 0.24, 0.09, 0.22, "8FB6D9", bev=0.025)
for s, x in ((-1, -0.9), (1, -0.36)):
    rbox(f"carm{s}", x - 0.035, x + 0.035, -0.12, 0.22, 0, 0.15, "7FA7D6", bev=0.02)
for k, x in enumerate((-0.76, -0.5)):
    rbox(f"cush{k}", x - 0.12, x + 0.12, -0.11, 0.12, 0.09, 0.115, "A9C8E6", bev=0.02)
PILLOW = ball("pillow", 0.06, "F6C945", (-0.82, 0.09, 0.17), (1.0, 0.45, 0.85))
# coffee table: jack-o'-lantern and a phone
rbox("ctop", -0.22, 0.2, -0.42, -0.18, 0.09, 0.11, "D79A5F", bev=0.008)
for x in (-0.2, 0.18):
    for y in (-0.4, -0.2):
        rbox(f"cleg{x}{y}", x - 0.01, x + 0.01, y - 0.01, y + 0.01, 0, 0.09, "B98A6A", bev=0)
PUMP = empty("pump", Vector((-0.1, -0.3, 0.11)))
ball("pumpb", 0.045, "F08A2C", (0, 0, 0.04), (1.15, 1.0, 0.85)).parent = PUMP
cyl("pumps", 0.008, 0.07, 0.09, 0, 0, "5E8A4A").parent = PUMP
FACEM = glow_mat("pface", "FFC24A", 3.0)
for s in (-1, 1):
    e = rbox(f"peye{s}", -0.009, 0.009, -0.004, 0.004, -0.007, 0.007, "FFC24A", bev=0.002)
    e.data.materials[0] = FACEM
    e.parent = PUMP
    e.location = (s * 0.018, -0.039, 0.05)
    e.rotation_euler = (0, math.pi / 4, 0)
pm = rbox("pmouth", -0.022, 0.022, -0.004, 0.004, -0.004, 0.004, "FFC24A", bev=0.002, parent=PUMP)
pm.data.materials[0] = FACEM
pm.location = (0, -0.041, 0.027)
PHAT = santa_hat("phat", PUMP, z=0.068, r=0.035, h=0.06)
PHONE = empty("phone", Vector((0.08, -0.29, 0.111)))
rbox("phb", -0.02, 0.02, -0.035, 0.035, 0, 0.005, "1E1E24", bev=0.003, parent=PHONE)
rbox("phs", -0.017, 0.017, -0.031, 0.031, 0.005, 0.0056, "BFE6FF", bev=0, parent=PHONE).data.materials[0] = glow_mat("scrm", "DCEFFF", 1.6)
PTIME = text("ptime", "12:00", 0.012, "1E1E24", (0, 0.016, 0.0062), PHONE, glow=0.6)
PTIME.rotation_euler = (0, 0, 0)
PBUB = empty("pbub", Vector((0, -0.006, 0.0063)), PHONE)
rbox("pbubp", -0.015, 0.015, -0.008, 0.008, 0, 0.0008, "EE6F52", bev=0, parent=PBUB).data.materials[0] = glow_mat("bubm", "EE6F52", 1.2)
pbt = text("pbubt", "IT'S TIME!!!", 0.0045, "FFFFFF", (0, 0, 0.0012), PBUB, glow=1.5)
pbt.rotation_euler = (0, 0, 0)
# sideboard with the smart speaker
rbox("sideb", 0.12, 0.46, 0.12, 0.3, 0, 0.08, "FFFFFF", bev=0.01)
SPK = empty("spk", Vector((0.31, 0.21, 0.08)))
cyl("spkb", 0.035, 0, 0.06, 0, 0, "3A3F4B", bev=0.01).parent = SPK
RING_M = glow_mat("spkring", "7FD4FF", 3.0)
rg = torus("spkr", 0.026, 0.004, (0, 0, 0.061), (0, 0, 0), "7FD4FF")
rg.data.materials[0] = RING_M
rg.parent = SPK
BTN = cyl("spkbtn", 0.01, 0.06, 0.066, 0, 0, "F4F1E8")
BTN.parent = SPK
NOTES_OB = []
NOTE_M = glow_mat("notem", "EE6F52", 1.2)
for k in range(7):
    n = empty(f"note{k}", AWAY)
    hd = ball(f"nh{k}", 0.013, "2F3843", (0, 0, 0), (1.2, 0.6, 0.9))
    hd.parent = n
    st = rbox(f"ns{k}", 0.009, 0.014, -0.003, 0.003, 0, 0.045, "2F3843", bev=0)
    st.parent = n
    if k % 2:
        hd.data.materials[0] = NOTE_M
        st.data.materials[0] = NOTE_M
    NOTES_OB.append(n)
# tree on the right
TREE = Vector((0.72, 0.05, 0))
cyl("trk", 0.025, 0, 0.06, TREE.x, TREE.y, "8A5A3A")
for k, (r, z0, z1) in enumerate(((0.2, 0.05, 0.26), (0.16, 0.2, 0.4), (0.11, 0.34, 0.54))):
    cyl(f"tr{k}", r, z0, z1, TREE.x, TREE.y, "4FA36B", r2=0.0, seg=24)
STAR = ball("star", 0.025, "F6C945", TREE + Vector((0, 0, 0.56)), (1, 0.5, 1))
STAR.data.materials[0] = glow_mat("starm", "F6C945", 4.0)
rnd = random.Random(7)
for k in range(16):
    z = rnd.uniform(0.1, 0.45)
    rr = 0.2 * (1 - (z - 0.05) / 0.55) + 0.012
    a = rnd.uniform(-2.6, -0.5)
    ball(f"bau{k}", 0.014, ("EE6F52", "F6C945", "7FA7D6", "F2A7B5", "FFFFFF")[k % 5],
         TREE + Vector((rr * math.cos(a), rr * math.sin(a), z)))
# you, on the couch; your friend in a Santa hat
YOU, YOU_A = peg("you", YOU_C, Vector((-0.55, 0.0, 0.115)), hair="6B4A3A")
FR, FR_A = peg("fr", "D9433B", Vector((0.2, -0.02, 0)), hair="F6C945", long_hair=True)
santa_hat("frhat", FR)
# wall counter sign
COUNT, CTX = sign("count", Vector((0.33, 0.3, 0.62)), "NOV 1 ON SPOTIFY", "0", "PLAYS IN ONE DAY", w=0.62, h=0.34)

# ------------------------------------------------------------------ 1 dining corner: the turkey and the calendar

O1 = room(1, "E7D5F0", "E2C29A")
rbox("dtop", -0.35, 0.35, -0.25, 0.15, 0.12, 0.14, "D79A5F", bev=0.008, off=O1)
rbox("cloth", -0.3, 0.3, -0.22, 0.12, 0.1405, 0.143, "FFFFFF", bev=0, off=O1)
for x in (-0.32, 0.32):
    for y in (-0.22, 0.12):
        rbox(f"dleg{x}{y}", x - 0.012, x + 0.012, y - 0.012, y + 0.012, 0, 0.12, "B98A6A", bev=0, off=O1)
TURK = empty("turk", O1 + Vector((0.0, -0.05, 0.143)))
ball("tbody", 0.06, "8A5A3A", (0, 0, 0.055), (1.0, 0.9, 0.9)).parent = TURK
for k in range(7):
    a = -0.9 + k * 0.3
    f = ball(f"tf{k}", 0.05, ("EE6F52", "F6C945", "D79A5F", "B8574A")[k % 4],
             (0.09 * math.sin(a), 0.06, 0.07 + 0.08 * math.cos(a)), (0.35, 0.12, 1.0))
    f.rotation_euler = (0, a, 0)
    f.parent = TURK
TNECK = empty("tneck", Vector((0, -0.04, 0.09)), TURK)
cyl("tn", 0.014, 0, 0.06, 0, 0, "8A5A3A").parent = TNECK
ball("th", 0.022, "8A5A3A", (0, -0.004, 0.068)).parent = TNECK
rbox("tbk", -0.006, 0.006, -0.04, -0.018, 0.064, 0.074, "F6C945", bev=0.002, parent=TNECK)
ball("twat", 0.008, "D2483A", (0, -0.026, 0.05), (1, 1, 1.8)).parent = TNECK
for s in (-1, 1):
    ball(f"teye{s}", 0.005, INKC, (s * 0.013, -0.018, 0.076)).parent = TNECK
    rbox(f"tleg{s}", s * 0.022 - 0.004, s * 0.022 + 0.004, -0.004, 0.004, 0.0, 0.012, "F6C945", bev=0, parent=TURK)
TBAU = ball("tbau", 0.016, "D9433B", TURK.location + Vector((0.075, 0.07, 0.15)))
FR2, FR2_A = peg("fr2", "D9433B", O1 + Vector((0.27, -0.2, 0)), hair="F6C945", long_hair=True)
santa_hat("fr2hat", FR2)
CAL, CALTX = sign("cal", O1 + Vector((-0.05, 0.3, 0.46)), "THANKSGIVING", "NOV 26", "NOBODY ASKED ME", w=0.5, h=0.3)
DAYS, DAYTX = sign("days", O1 + Vector((1.2, 0.3, 0.42)), "NOV 1 TO DEC 25", "0", "DAYS", w=0.6, h=0.3)
CALSQ = []
for k in range(56):
    c = rbox(f"cal{k}", -0.016, 0.016, -0.004, 0.004, -0.016, 0.016, "FFFFFF", bev=0.003)
    c.location = O1 + Vector((1.2 - 0.126 + (k % 7) * 0.042, 0.31, 0.9 - (k // 7) * 0.042))
    CALSQ.append(c)
XM, WM = mat("EE6F52"), mat("FFFFFF")

# ------------------------------------------------------------------ light, world, camera

w = bpy.data.worlds.new("w")
scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (*hexc("CFE6F5"), 1)
w.node_tree.nodes["Background"].inputs[1].default_value = float(os.environ.get("XM_WORLD", "0.9"))
B.sun("sun", -140, 50, float(os.environ.get("XM_SUN", "3.0")), color=hexc("FFF1DC"), angle_deg=8)
for k, o in enumerate((Vector(), O1)):
    B.area(f"fill{k}", o + Vector((0.3, -2.0, 1.4)), o + Vector((0.1, 0, 0.25)), 2.5, float(os.environ.get("XM_FILL", "40")),
           color=hexc("FFF6EE"))
cam = B.camera(lens=35, fstop=14.0)
cam.data.clip_start, cam.data.clip_end = 0.01, 200.0
O0 = Vector()

def lc(a, b, tg, u, o, lens=35):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "living": lambda u: lc((0.0, -2.0, 0.75), (0.02, -1.85, 0.72), (0.0, 0.0, 0.3), u, O0),
    "pumpkin": lambda u: lc((-0.08, -0.62, 0.22), (-0.09, -0.55, 0.21), (-0.1, -0.3, 0.16), u, O0),
    "phone": lambda u: lc((0.08, -0.36, 0.3), (0.08, -0.34, 0.25), (0.08, -0.29, 0.11), u, O0),
    "counter": lambda u: lc((0.3, -0.85, 0.5), (0.31, -0.78, 0.5), (0.31, 0.2, 0.5), u, O0),
    "replay": lambda u: lc((0.36, -0.42, 0.3), (0.35, -0.37, 0.28), (0.28, 0.15, 0.16), u, O0),
    "turkey": lambda u: lc((0.0, -0.75, 0.3), (-0.01, -0.66, 0.29), (0.0, 0.0, 0.25), u, O1),
    "calendar": lambda u: lc((1.2, -0.7, 0.62), (1.2, -0.62, 0.6), (1.2, 0.3, 0.62), u, O1),
    "ears": lambda u: lc((-0.45, -0.72, 0.3), (-0.48, -0.64, 0.29), (-0.55, 0.0, 0.2), u, O0),
    "total": lambda u: lc((0.2, -0.95, 0.35), (0.25, -0.85, 0.38), (0.32, 0.2, 0.55), u, O0),
    "final": lambda u: lc((0.4, -2.0, 1.2), (0.3, -1.85, 1.1), (0.05, 0.0, 0.3), u, O0),
}

def shot_at(t):
    k = max([0] + [i for i, (s, _) in enumerate(SHOTS) if t >= s - 1e-6])
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    cut = max(0.0, min(1.0, (t - SHOTS[k][0]) / max(1e-6, t1 - SHOTS[k][0])))
    return SHOTS[k][1], cut

def start_of(n):
    return next(s for s, m in SHOTS if m == n)

def dance(root, arms, t, at, phase=0.0):
    root.location = at + Vector((0, 0, 0.02 * abs(math.sin(t * 6.0 + phase))))
    root.rotation_euler = (0, 0.12 * math.sin(t * 3.0 + phase), 0.25 * math.sin(t * 1.5 + phase))
    for i, pv in enumerate(arms):
        pv.rotation_euler = (0, (-1) ** i * (2.4 + 0.35 * math.sin(t * 6.0 + i * math.pi)), 0)

def apply_state(t):
    name, cut = shot_at(t)
    loc, tg, lens = CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    cam.data.dof.use_dof = False

    # the friend dances all the time, except while pressing replay
    pr = t - EV["press"]
    if name == "replay":
        FR.location = Vector((0.2, 0.17, 0))
        FR.rotation_euler = (0, 0, -0.5)
        FR_A[0].rotation_euler = (0, 0.3, 0)
        k = (pr % 0.32) / 0.32 if 0 <= pr < 1.28 else 0.5
        FR_A[1].rotation_euler = (0, -2.0 + 0.25 * math.sin(k * math.pi), 0)
        down = 0 <= pr < 1.28 and k < 0.35
        BTN.location.z = -0.004 if down else 0.0
        SPK.scale = (1, 1, 0.94 if down else 1.0)
    else:
        dance(FR, FR_A, t, Vector((0.2, -0.02, 0)))
        BTN.location.z = 0.0
        SPK.scale = (1, 1, 1 + 0.03 * abs(math.sin(t * 6.0)))
    B.bsdf(RING_M).inputs["Emission Strength"].default_value = 2.0 + 1.5 * abs(math.sin(t * 6.0))
    for k, n in enumerate(NOTES_OB):
        age = (t + k * 0.45) % 3.15
        n.location = SPK.location + Vector((0.02 * math.sin(age * 3 + k) + (k % 3 - 1) * 0.03, -0.02, 0.09 + age * 0.12))
        n.rotation_euler = (math.pi / 2, 0, 0.3 * math.sin(age * 2 + k))
        s = min(1.0, age / 0.3) * max(0.0, min(1.0, (3.15 - age) / 0.4))
        n.scale = (max(0.001, s),) * 3

    # the hat lands on the jack-o'-lantern
    if t < EV["hat"]:
        hide(PHAT)
    else:
        u = smooth01((t - EV["hat"]) / 0.3)
        PHAT.scale = (1, 1, 1)
        PHAT.location = Vector((0, 0.005, 0.068 + 0.12 * (1 - u)))
    show_between(PBUB, t, EV["time"] - 0.1)

    # counter sign: three counts
    if t < start_of("total"):
        set_sign(CTX, "NOV 1 ON SPOTIFY", f"{count(t, EV['count0'], 2.2, 713000):,}", "PLAYS IN ONE DAY", w=0.62)
    elif t < start_of("final"):
        set_sign(CTX, "BACK TO BACK", f"{count(t, EV['count1'], 1.4, 19359):,}", "PLAYS TO CHRISTMAS", w=0.62)
    else:
        set_sign(CTX, "YOUR FRIEND IS ON", "PLAY " + f"{count(t, EV['count2'] - 0.4, 1.0, 1792):,}", "OF 19,359", w=0.62)

    # you, on the couch: the pillow goes over your ears
    YOU.rotation_euler = (0, 0, 0.05 * math.sin(t * 1.3))
    if t >= EV["pillow"]:
        u = smooth01((t - EV["pillow"]) / 0.4)
        PILLOW.location = Vector((-0.82, 0.09, 0.17)).lerp(Vector((-0.55, 0.0, 0.425)), u)
        PILLOW.scale = Vector((1.0, 0.45, 0.85)).lerp(Vector((1.35, 0.95, 0.6)), u)
        for i, pv in enumerate(YOU_A):
            pv.rotation_euler = (0, (-1) ** i * 2.7 * u, 0)
    else:
        PILLOW.location = Vector((-0.82, 0.09, 0.17))
        PILLOW.scale = (1.0, 0.45, 0.85)
        for pv in YOU_A:
            pv.rotation_euler = (0, 0, 0)

    # turkey: a bauble on the tail, then the head turns to camera
    dance(FR2, FR2_A, t, O1 + Vector((0.27, -0.2, 0)), phase=1.0)
    if t >= EV["bauble"] - 0.3:
        FR2_A[1].rotation_euler = (0, -2.3, 0)
    show_between(TBAU, t, EV["bauble"])
    tu = smooth01((t - EV["turn"]) / 0.9) if t >= EV["turn"] else 0.0
    TNECK.rotation_euler = (0, 0, 0.9 - 0.9 * tu + 0.05 * math.sin(t * 2))
    # 54 days: squares fill in as the count climbs
    nd = count(t, EV["days"] - 0.5, 1.0, 54)
    set_sign(DAYTX, big=str(nd), w=0.6)
    for k, c in enumerate(CALSQ):
        c.data.materials[0] = XM if k < nd else WM
        c.scale = (1, 1, 1) if k < 54 else (0.001,) * 3

B.render_settings(FPS, samples=int(os.environ.get("YT_SAMPLES", "24")), motion_blur=0.0)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1) / FPS)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
