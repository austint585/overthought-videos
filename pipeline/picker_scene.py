"""Pastel toy kit, "The Friend Who Can't Pick A Restaurant": toy peg people. Sets: a sidewalk at dusk outside three toy
restaurants with striped awnings (your friend with a phone, a ring of menu cards spinning around their head, a DECIDING
counter) and a grocery store with two jam tables (24 jars and 6 jars) where shoppers stop and one buys. Shots, timed by
render_picker.py: street, store, big, small, stopped, bought, later, phone, two, final. Helpers copied from hangry_scene.py.

blender -b --factory-startup -P picker_scene.py -- timing.json out_dir MODE   (MODE: "all" or 1-based frame list)
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





def sun(name, s=1.0):
    root = empty(name, AWAY)
    b = ball(name + "b", 0.05 * s, "FFD24A", (0, 0, 0), (1, 0.5, 1))
    b.data.materials[0] = glow_mat(name + "m", "FFD24A", 2.5)
    b.parent = root
    return root

def jar(name, at, lid, fill, s=1.0):
    root = empty(name, at)
    g = cyl(name + "g", 0.024 * s, 0.0, 0.055 * s, 0, 0, fill, seg=24, bev=0.004)
    g.parent = root
    l = cyl(name + "l", 0.026 * s, 0.055 * s, 0.068 * s, 0, 0, lid, seg=24, bev=0.003)
    l.parent = root
    rbox(name + "w", -0.018 * s, 0.018 * s, -0.0255 * s, -0.0235 * s, 0.015 * s, 0.04 * s, "FFF6E6", bev=0, parent=root)
    return root

def card(name, color, s=1.0, label=None):
    root = empty(name, AWAY)
    rbox(name + "p", -0.03 * s, 0.03 * s, -0.003, 0.003, -0.042 * s, 0.042 * s, "FFFFFF", bev=0.004, parent=root, rough=0.4)
    rbox(name + "s", -0.026 * s, 0.026 * s, -0.0045, -0.0035, 0.018 * s, 0.034 * s, color, bev=0, parent=root)
    for k in range(3):
        rbox(f"{name}l{k}", -0.022 * s, 0.012 * s, -0.0045, -0.0035, (-0.003 - k * 0.014) * s, (0.003 - k * 0.014) * s,
             "C8C2BA", bev=0, parent=root)
    if label:
        text(name + "t", label, 0.016 * s, INKC, (0, -0.006, 0.026 * s), root, glow=0.4)
    return root

JAMC = ("C2304A", "7A2E6B", "E8833A", "F2C14E", "5B8C3A", "D9536F", "4A2A6B", "B34A2E")
LIDC = ("E8B57A", "F4F1E8", "D9433B", "7FA7D6")

# ------------------------------------------------------------------ 0 the sidewalk at dusk
O0 = Vector()
rbox("street0", -3, 3, -4, -0.9, -0.08, -0.03, "5A6070", bev=0)
rbox("walk0", -3, 3, -0.9, 0.32, -0.05, 0, "D8D2CA", bev=0)
for k in range(-6, 7):
    rbox(f"seam{k}", k * 0.45 - 0.004, k * 0.45 + 0.004, -0.9, 0.3, 0.0, 0.002, "BDB6AD", bev=0)
rbox("curb0", -3, 3, -0.95, -0.88, -0.05, 0.02, "C4BDB3", bev=0.004)
FRONTS = (("PIZZA", "F7C9B0", ("E8584B", "FFFFFF"), -0.74), ("TACOS", "F6E3A8", ("4FA36B", "FFFFFF"), 0.0),
          ("SUSHI", "CFE3F0", ("2F3843", "F29C9C"), 0.74))
win = glow_mat("win", "FFD9A0", 1.6)
for k, (nm, wc, aw, x) in enumerate(FRONTS):
    rbox(f"fac{k}", x - 0.36, x + 0.36, 0.32, 0.42, 0, 1.25, wc, bev=0.006)
    rbox(f"door{k}", x + 0.12, x + 0.27, 0.3, 0.33, 0, 0.36, "8A6248", bev=0.006)
    rbox(f"win{k}", x - 0.28, x + 0.06, 0.305, 0.325, 0.12, 0.42, "FFD9A0", bev=0.004).data.materials[0] = win
    rbox(f"sb{k}", x - 0.24, x + 0.24, 0.29, 0.318, 0.72, 0.84, "2F3843", bev=0.008)
    text(f"st{k}", nm, 0.075, "FFF6E6", Vector((x, 0.284, 0.78)), glow=1.4)
    pv = empty(f"awp{k}", Vector((x, 0.3, 0.62)))
    pv.rotation_euler = (0.55, 0, 0)
    for j in range(7):
        rbox(f"aw{k}{j}", -0.33 + j * 0.0943, -0.33 + (j + 1) * 0.0943, -0.2, 0.0, -0.008, 0.008, aw[j % 2], bev=0.002,
             parent=pv)
lampg = glow_mat("lampg", "FFE7B0", 3.0)
for x in (-1.3, 1.3):
    cyl(f"lamp{x}", 0.012, 0, 1.0, x, -0.75, "3A4150")
    ball(f"lampb{x}", 0.05, "FFE7B0", (x, -0.75, 1.02)).data.materials[0] = lampg
FRI, FRI_A = peg("fri", YOU_C, Vector((0.0, -0.25, 0.0)), hair="6B4A3A")
FRI.scale = (1.5, 1.5, 1.5)
PHONE = rbox("ph", -0.022, 0.022, -0.004, 0.004, -0.04, 0.04, "2F3843", bev=0.004)
PHONE.parent = FRI_A[1]
PHONE.location = (0.0, -0.02, -0.115)
PHONE.rotation_euler = (1.25, 0, 0)
pscr = rbox("phs", -0.018, 0.018, -0.0055, -0.0045, -0.034, 0.034, "8FC3F0", bev=0)
pscr.parent = PHONE
pscr.data.materials[0] = glow_mat("phg", "8FC3F0", 2.0)
DEC, DEC_T = sign("dec", Vector((0.21, -0.12, 0.8)), "DECIDING", "41 MIN", "", w=0.26, h=0.17)
CARDS = [card(f"cd{k}", JAMC[k % len(JAMC)]) for k in range(12)]
BIGC = [card("cbA", "E8584B", 2.2, "PIZZA"), card("cbB", "4FA36B", 2.2, "TACOS")]
B_PICK = bubble("bpick", AWAY, "OK. TACOS.", w=0.28)

# ------------------------------------------------------------------ 1 the grocery store
O1 = room(1, "DCEBDF", "E9E2D6")
srnd = random.Random(5)
for r, z in enumerate((0.55, 0.85, 1.15)):
    rbox(f"shelf{r}", -2.4, 2.4, 0.2, 0.32, z - 0.02, z, "F4F1E8", bev=0.004, off=O1)
    x = -2.35
    while x < 2.3:
        wdt = srnd.uniform(0.05, 0.11)
        hgt = srnd.uniform(0.08, 0.17)
        rbox(f"g{r}_{x:.2f}", x, x + wdt, 0.22, 0.3, z, z + hgt,
             srnd.choice(("F2A07B", "7FA7D6", "F6C945", "9B7FD6", "7FB9A8", "EE6F52", "F4F1E8")), bev=0.004, off=O1)
        x += wdt + 0.012
TABLES = {}
for key, x, n, cols in (("big", -0.43, 24, 8), ("small", 0.43, 6, 3)):
    o = O1 + Vector((x, -0.05, 0))
    rbox(f"tt{key}", -0.36, 0.36, -0.17, 0.17, 0.28, 0.3, "FFFFFF", bev=0.004, off=o)
    rbox(f"tc{key}", -0.37, 0.37, -0.178, -0.168, 0.12, 0.29, "F29C9C", bev=0.003, off=o)
    for dx in (-0.32, 0.32):
        rbox(f"tl{key}{dx}", dx - 0.012, dx + 0.012, -0.12, 0.12, 0, 0.28, "B98A6A", bev=0, off=o)
    jars = []
    rows = n // cols
    for k in range(n):
        c, r = k % cols, k // cols
        jx = (c - (cols - 1) / 2) * (0.078 if cols == 8 else 0.12)
        jy = (r - (rows - 1) / 2) * 0.085
        jars.append(jar(f"j{key}{k}", o + Vector((jx, jy, 0.3)), LIDC[k % 4], JAMC[(k * 3) % len(JAMC)],
                        1.0 if cols == 8 else 1.25))
    sg, st = sign(f"s{key}", o + Vector((0, 0.15, 0.68)), "", f"{n} JAMS", "", w=0.46, h=0.24)
    TABLES[key] = (o, jars, sg, st)
S_LATER, _ = sign("slater", AWAY, "LATER STUDIES", "OFTEN SMALL", "50 EXPERIMENTS", w=0.62, h=0.3)
SHOP = []
cols6 = ("F6C945", "9B7FD6", "4FA36B", "F29C9C", "7FB9A8", "EE6F52", "7FA7D6", "D79A5F", "C0566A", "8FC3F0")
for k in range(10):
    p, a = peg(f"sh{k}", cols6[k], AWAY, hair=srnd.choice(("2F2A28", "6B4A3A", "C9955E", "8A8A8A")), long_hair=k % 3 == 0)
    p.scale = (1.1,) * 3
    SHOP.append((p, a))
HELD = jar("held", AWAY, "D9433B", "C2304A", 1.0)
BAG = rbox("bag", -0.035, 0.035, -0.022, 0.022, 0, 0.07, "D8B98A", bev=0.006)

# ------------------------------------------------------------------ light, world, camera
w = bpy.data.worlds.new("w")
scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (*hexc("F2E2D6"), 1)
w.node_tree.nodes["Background"].inputs[1].default_value = float(os.environ.get("TK_WORLD", "0.8"))
B.sun("sun", -130, 40, float(os.environ.get("TK_SUN", "2.2")), color=hexc("FFDDBB"), angle_deg=8)
for k, o in enumerate((O0, O1)):
    B.area(f"fill{k}", o + Vector((0.3, -2.4, 1.6)), o + Vector((0.1, 0.2, 0.4)), 3.0, float(os.environ.get("TK_FILL", "45")),
           color=hexc("FFF0E0"))
cam = B.camera(lens=26, fstop=14.0)
cam.data.clip_start, cam.data.clip_end = 0.01, 200.0

def lc(a, b, tg, u, o, lens=26):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "street": lambda u: lc((0.04, -1.2, 0.6), (0.0, -1.1, 0.58), (0.02, -0.2, 0.5), u, O0),
    "store": lambda u: lc((0.0, -1.75, 0.75), (0.0, -1.62, 0.72), (0.0, 0.0, 0.42), u, O1, 22),
    "big": lambda u: lc((-0.45, -0.9, 0.52), (-0.43, -0.82, 0.5), (-0.43, 0.0, 0.46), u, O1, 28),
    "small": lambda u: lc((0.45, -0.9, 0.52), (0.43, -0.82, 0.5), (0.43, 0.0, 0.46), u, O1, 28),
    "stopped": lambda u: lc((0.0, -1.85, 0.95), (0.0, -1.72, 0.92), (0.0, 0.0, 0.4), u, O1, 22),
    "bought": lambda u: lc((0.0, -1.8, 0.95), (0.04, -1.68, 0.92), (0.0, 0.0, 0.4), u, O1, 22),
    "later": lambda u: lc((0.0, -1.8, 0.95), (0.0, -1.68, 0.92), (0.0, 0.0, 0.6), u, O1, 22),
    "phone": lambda u: lc((0.12, -0.95, 0.62), (0.08, -0.85, 0.6), (0.0, -0.25, 0.48), u, O0, 28),
    "two": lambda u: lc((0.15, -1.4, 0.62), (0.08, -1.3, 0.6), (0.0, -0.25, 0.5), u, O0),
    "final": lambda u: lc((0.04, -1.2, 0.6), (0.0, -1.1, 0.58), (0.02, -0.2, 0.5), u, O0),
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

BIG_SPOTS = [(-0.75, -0.5), (-0.6, -0.64), (-0.45, -0.5), (-0.3, -0.64), (-0.15, -0.5), (-0.5, -0.8)]
SMALL_SPOTS = [(0.3, -0.55), (0.45, -0.68), (0.6, -0.55), (0.72, -0.7)]

def apply_state(t):
    name, cut = shot_at(t)
    loc, tg, lens = CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    cam.data.dof.use_dof = False

    # ---- street: the friend taps the phone, menu cards whirl around their head, the counter climbs; at "two" it collapses
    final = t >= start_of("final")
    done = EV["two"] <= t < start_of("final") + 1.3
    head = Vector((0.0, -0.25, 0.42))
    FRI_A[1].rotation_euler = (-1.25 + 0.04 * math.sin(t * 14), 0, 0)
    FRI_A[0].rotation_euler = ((-2.6 if done and t - EV["two"] > 0.5 else -0.4), 0, 0)
    hop = 0.0
    if done:
        da = t - EV["two"] - 0.5
        hop = 0.06 * max(0.0, math.sin(da * 9)) if 0 <= da < 0.35 else 0.0
    FRI.location = Vector((0.0, -0.25, hop))
    if t < start_of("store") or (final and not done):
        mins = 41
    else:
        mins = 41 + int(17 * smooth01((t - start_of("store")) / max(1e-6, start_of("two") - start_of("store"))))
    set_sign(DEC_T, head="DECIDING" if not done else "DECIDED", big=f"{mins} MIN", w=0.26)
    speed = 1.6 if t < start_of("store") or (final and not done) else (4.5 if t >= start_of("phone") else 2.5)
    many = EV["many"] <= t < EV["two"]
    for k, cd in enumerate(CARDS):
        if done:
            hide(cd)
            cd.location = AWAY
            continue
        a = t * speed + k / len(CARDS) * 2 * math.pi
        r = 0.17 + (0.06 if many else 0.0) + 0.01 * math.sin(t * 3 + k)
        cd.location = head + Vector((r * math.cos(a), r * math.sin(a) * 0.6, 0.1 + 0.03 * math.sin(a * 2)))
        cd.rotation_euler = (0, 0, -a * 0.3)
        cd.scale = (1, 1, 1)
    for k, cd in enumerate(BIGC):
        place(cd, head + Vector((-0.16 + 0.32 * k, -0.12, 0.12)), t - EV["two"] if done else -1)
        cd.rotation_euler = (0, 0, 0.15 * (1 - 2 * k))
    place(B_PICK, head + Vector((-0.13, -0.1, 0.3)), t - EV["two"] - 0.3 if done else -1)

    # ---- store: jars pop in, shoppers arrive (6 at 24 jams, 4 at 6 jams), signs swap to stopped, then bought
    for key in ("big", "small"):
        o, jars, sg, st = TABLES[key]
        t0 = EV["jars24"] if key == "big" else EV["jars6"]
        for k, j in enumerate(jars):
            if t < start_of("big") or t >= start_of("stopped"):
                j.scale = (1, 1, 1)
            else:
                pop(j, t - t0 - k * 0.02)
        if t >= EV["b3"]:
            big = "BOUGHT 3%" if key == "big" else ("BOUGHT 30%" if t >= EV["b30"] else "6 JAMS")
        elif t >= EV["p60"]:
            big = "STOPPED 60%" if key == "big" else ("STOPPED 40%" if t >= EV["p40"] else "6 JAMS")
        else:
            big = f"{len(jars)} JAMS"
        set_sign(st, big=big, w=0.46)
    for k, (p, a) in enumerate(SHOP):
        sx, sy = (BIG_SPOTS + SMALL_SPOTS)[k]
        ca = t - EV["crowd"] - 0.08 * k
        if ca < 0 or t >= start_of("phone"):
            p.location = AWAY
            continue
        u = smooth01(ca / 0.8)
        side = -1 if sx < 0 else 1
        p.location = O1 + Vector((sx + side * 1.6 * (1 - u), sy, 0.012 * abs(math.sin(ca * 10)) * (1 - u)))
        for j, pv in enumerate(a):
            pv.rotation_euler = (-0.3 + 0.15 * math.sin(t * 2 + k + j), 0, 0)
    buyer = SHOP[7][0]
    if t >= EV["b30"] and t < start_of("phone"):
        SHOP[7][1][1].rotation_euler = (-1.4, 0, 0)
        place(HELD, buyer.location + Vector((0.09, -0.12, 0.2)), t - EV["b30"], 1.3)
        place(BAG, buyer.location + Vector((-0.1, -0.03, 0.0)), t - EV["b30"] - 0.15, 1.2)
    else:
        place(HELD, AWAY, -1)
        place(BAG, AWAY, -1)
    place(S_LATER, O1 + Vector((0.0, 0.0, 0.98)), t - EV["later"] if t < start_of("phone") else -1)

B.render_settings(FPS, samples=int(os.environ.get("YT_SAMPLES", "24")), motion_blur=0.0)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1) / FPS)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
