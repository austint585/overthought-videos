"""Pastel toy kit, "Secondhand Cringe" (render_cringe.py): karaoke night and a brain-scan lab. Helpers copied from period_scene.py. Was: "The Period Text": toy peg people. Sets: a kitchen counter in the morning (you with your phone under a
giant chat; the reply "Okay" lands with a red period that drops and rolls across the counter) and a psychology test room
(two wall screens with the exchange, words cycling Okay, Sure, Yeah, Yup, a period on one side only, SINCERE meters, an
easel with two handwritten notes, students on stools). Shots, timed by render_period.py: kitchen, room, screen, split,
meter, note, back, final. Helpers copied from hangry_scene.py.

blender -b --factory-startup -P cringe_scene.py -- timing.json out_dir MODE   (MODE: "all" or 1-based frame list)
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

INK2 = "2F3843"

def note(name):
    """A music note: a dark ball and a stem, facing -y."""
    root = empty(name, AWAY)
    b = ball(name + "b", 0.018, INKC, (0, 0, 0), (1.2, 0.6, 0.9))
    b.parent = root
    s = rbox(name + "s", 0.012, 0.018, -0.004, 0.004, 0.0, 0.07, INKC, bev=0, parent=root)
    return root

def brain(name, at, label):
    """A pink toy brain on the wall screen with two hidden glow spots (cingulate on top, insula at the side)."""
    root = empty(name, at)
    for s in (-1, 1):
        h = ball(f"{name}h{s}", 0.1, "F2A7B5", (s * 0.052, 0, 0), (0.55, 0.25, 0.8))
        h.parent = root
    st = cyl(name + "st", 0.025, -0.13, -0.06, 0, 0.0, "E89AA8", seg=24)
    st.parent = root
    spots = []
    for k, (x, z, r) in enumerate(((0.0, 0.03, 0.03), (-0.055, -0.02, 0.026))):
        sp = ball(f"{name}g{k}", r, "E8584B", (x, -0.03, z))
        sp.data.materials[0] = glow_mat(f"{name}gm{k}", "FF5A4A", 3.0)
        sp.parent = root
        spots.append(sp)
    tx = text(name + "l", label, 0.032, INKC, (0, -0.02, -0.17), root, glow=0.4)
    return root, spots

# ------------------------------------------------------------------ 0 karaoke night
O0 = room(0, "F6D6E0", "B9A3D6")
rbox("stage0", 0.0, 0.8, -0.1, 0.32, 0.0, 0.1, "F4F1E8", bev=0.01)
rbox("lip0", 0.0, 0.8, -0.115, -0.1, 0.03, 0.07, "F6C945", bev=0.004)
rbox("kscr0", 0.08, 0.72, 0.29, 0.31, 0.62, 1.0, "2F3843", bev=0.01)
rbox("kgl0", 0.1, 0.7, 0.286, 0.29, 0.64, 0.98, "8FC3F0", bev=0).data.materials[0] = glow_mat("kgl", "9FC9F2", 1.2)
LYR = []
for k, z in enumerate((0.88, 0.8, 0.72)):
    rbox(f"ly{k}", 0.16, 0.64, 0.282, 0.286, z - 0.015, z + 0.015, "F4F1E8", bev=0)
    bar = rbox(f"lyf{k}", 0.0, 0.48, 0.278, 0.282, z - 0.015, z + 0.015, "EE6F52", bev=0)
    bar.location = Vector((0.16, 0, 0))
    LYR.append(bar)
for k, x in enumerate((0.05, 0.75)):
    cyl(f"spk{k}", 0.06, 0.1, 0.36, x, 0.2, "2F3843", seg=24, bev=0.01)
FR, FR_A = peg("fr", "F6C945", Vector((0.42, 0.12, 0.1)), hair="C9955E", long_hair=True)
FR.scale = (1.4, 1.4, 1.4)
MIC = cyl("mic", 0.006, -0.16, -0.08, 0, 0, "2F3843", seg=16)
MIC.parent = FR_A[1]
mh = ball("mich", 0.016, "9AA3B0", (0, 0, -0.17))
mh.parent = FR_A[1]
NOTES = [note(f"nt{k}") for k in range(5)]
cyl("tbl0", 0.13, 0.0, 0.2, -0.36, -0.2, "EE6F52", seg=40, bev=0.01)
cyl("tblt0", 0.16, 0.2, 0.22, -0.36, -0.2, "F4F1E8", seg=40, bev=0.006)
cyl("cup0", 0.025, 0.22, 0.3, -0.42, -0.26, "7FA7D6", seg=24, bev=0.003)
YOU, YOU_A = peg("you", "7FA7D6", Vector((-0.12, -0.45, 0.0)), hair="2F2A28")
YOU.scale = (1.5, 1.5, 1.5)
YOU.rotation_euler = (0, 0, 0.75)
S_OUCH, _ = sign("souch", AWAY, "YOUR BRAIN", "OUCH", "", w=0.34, h=0.2)

# ------------------------------------------------------------------ 1 the brain lab
O1 = room(1, "DCEBF2", "C9CFDA")
rbox("bed1", -0.95, -0.25, -0.2, 0.05, 0.1, 0.15, "F4F1E8", bev=0.01, off=O1)
rbox("bedl1", -0.9, -0.3, -0.15, 0.0, 0.0, 0.1, "9AA3B0", bev=0.005, off=O1)
torus("ring1", 0.21, 0.075, O1 + Vector((-0.78, -0.07, 0.3)), (0, math.pi / 2, 0), "F4F1E8")
cyl("ringc1", 0.09, 0, 0.02, 0, 0, "7FA7D6", seg=48).location = O1 + Vector((-0.78, -0.16, 0.3))
bpy.data.objects["ringc1"].rotation_euler = (math.pi / 2, 0, 0)
LIE, LIE_A = peg("lie", "4FA36B", O1 + Vector((-0.42, -0.07, 0.2)), hair="6B4A3A")
LIE.rotation_euler = (0, -math.pi / 2, 0)
SCRO = O1 + Vector((0.45, 0.3, 0.78))
rbox("bscr1", -0.5, 0.5, -0.015, 0.015, -0.3, 0.3, "2F3843", bev=0.012, off=SCRO)
rbox("bscg1", -0.48, 0.48, -0.019, -0.016, -0.28, 0.28, "F4F1E8", bev=0, off=SCRO).data.materials[0] = glow_mat("bscg", "F7F5EF", 0.9)
BR_A, SP_A = brain("brA", SCRO + Vector((-0.24, -0.04, 0.05)), "SOMEONE GETS HURT")
BR_B, SP_B = brain("brB", SCRO + Vector((0.24, -0.04, 0.05)), "SOMEONE EMBARRASSING")
MBG = rbox("mbg1", -0.18, 0.18, -0.026, -0.022, -0.012, 0.012, "D8D4CC", bev=0, off=SCRO + Vector((0.24, 0, -0.21)))
MBAR = rbox("mbar1", 0.0, 0.36, -0.03, -0.027, -0.012, 0.012, "E8584B", bev=0)
MBAR.location = SCRO + Vector((0.06, 0, -0.21))
MLAB = text("mlab1", "EMPATHY", 0.026, INKC, SCRO + Vector((0.24, -0.03, -0.25)), glow=0.4)
S_N, _ = sign("sn1", AWAY, "BRAIN SCANS", "32 PEOPLE", "", w=0.42, h=0.2)
S_SAME, _ = sign("ssame1", AWAY, "", "SAME AREAS", "", w=0.42, h=0.13)
S_IDEA, _ = sign("sidea1", AWAY, "THEY HAD", "NO IDEA", "", w=0.38, h=0.2)
WALK, WALK_A = peg("walk", "9B7FD6", O1 + Vector((1.5, -0.3, 0.0)), hair="2F2A28")
WALK.scale = (1.3, 1.3, 1.3)
TP = rbox("tp", 0.0, 0.16, -0.012, 0.012, 0.0, 0.004, "FFFFFF", bev=0, parent=WALK)
TP.location = (0.04, 0.0, 0.002)

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
    "bar": lambda u: lc((-0.02, -1.5, 0.62), (0.0, -1.38, 0.6), (0.04, 0.0, 0.52), u, O0),
    "scan": lambda u: lc((-0.5, -1.45, 0.62), (-0.46, -1.35, 0.6), (-0.5, 0.0, 0.45), u, O1),
    "pain": lambda u: lc((0.45, -1.0, 0.85), (0.45, -0.92, 0.84), (0.45, 0.3, 0.8), u, O1, 24),
    "unaware": lambda u: lc((1.25, -1.15, 0.5), (1.35, -1.05, 0.48), (1.35, 0.0, 0.38), u, O1),
    "empathy": lambda u: lc((0.69, -0.75, 0.8), (0.69, -0.68, 0.79), (0.69, 0.3, 0.74), u, O1, 28),
    "back": lambda u: lc((0.0, -1.2, 0.55), (-0.03, -1.12, 0.54), (-0.08, -0.3, 0.45), u, O0, 28),
    "final": lambda u: lc((-0.02, -1.5, 0.62), (0.0, -1.38, 0.6), (0.04, 0.0, 0.52), u, O0),
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

    # ---- karaoke: your friend belts it out, notes float up, you cover your face (and peek on "back")
    final = t >= start_of("final")
    loop_t = t - start_of("final") if final else t
    FR.location = Vector((0.42, 0.12, 0.1 + 0.012 * abs(math.sin(t * 6))))
    FR.rotation_euler = (0.12 * math.sin(t * 3), 0, 0.15 * math.sin(t * 1.7))
    FR_A[1].rotation_euler = (-2.35, 0, 0)
    FR_A[0].rotation_euler = (-2.7 + 0.25 * math.sin(t * 4), 0, 0)
    for k, nt in enumerate(NOTES):
        ph = ((t * 0.7 + k / len(NOTES)) % 1.0)
        nt.location = Vector((0.42 + 0.12 * math.sin(k * 2.1 + ph * 3), 0.0, 0.62 + 0.4 * ph))
        nt.scale = (max(0.001, math.sin(ph * math.pi)) * 1.3,) * 3
        nt.rotation_euler = (0, 0.4 * math.sin(ph * 6 + k), 0)
    for k, bar in enumerate(LYR):
        u = max(0.0, min(1.0, (t * 0.35 - k) % 3 if True else 0))
        bar.scale = (max(0.001, min(1.0, u)), 1, 1)
    peek = name == "back"
    up = 1.0 if (name in ("bar", "final") and loop_t > -1) else 0.0
    if name in ("bar", "final"):
        up = smooth01((loop_t + 0.4) / 0.3)
    if peek:
        up = 0.85
    cover = -0.3 - 2.3 * up
    YOU_A[0].rotation_euler = (cover, 0.35 * up, 0)
    YOU_A[1].rotation_euler = (cover, -0.35 * up, 0)
    YOU.location = Vector((-0.12, -0.45, 0.012 * abs(math.sin(t * 9)) * up))
    YOU.rotation_euler = (-0.12 * up, 0, 0.75)
    place(S_OUCH, O0 + Vector((-0.12, -0.25, 0.9)), t - EV["hurts"] if name == "bar" else -1)

    # ---- the lab: one person in the scanner, the screen shows the brains
    LIE_A[0].rotation_euler = (0, 0, 0)
    LIE_A[1].rotation_euler = (0, 0, 0)
    place(S_N, O1 + Vector((-0.55, 0.2, 0.75)), t - EV["n32"] if name == "scan" else -1)
    pain_on = t >= start_of("pain")
    place(BR_A, SCRO + Vector((-0.24, -0.04, 0.05)), t - start_of("pain") if pain_on else -1)
    BR_B.location = SCRO + Vector((0.24 if pain_on else 0.0, -0.04, 0.05))
    glow_b = t >= EV["n32"] + 0.8
    glow_a = t >= EV["hurt"]
    for k, sp in enumerate(SP_B):
        sp.scale = ((1.0 + 0.12 * math.sin(t * 8 + k)) if glow_b else 0.001,) * 3
    for k, sp in enumerate(SP_A):
        sp.scale = ((1.0 + 0.12 * math.sin(t * 8 + k)) if glow_a else 0.001,) * 3
    place(S_SAME, SCRO + Vector((0.0, -0.05, 0.38)), t - EV["hurt"] if name == "pain" else -1)
    emp = t >= start_of("empathy")
    for ob in (MBG, MLAB):
        ob.scale = (1, 1, 1) if emp else (0.001,) * 3
    lvl = 0.25 + 0.75 * smooth01((t - EV["harder"] + 0.6) / 0.9) if emp else 0.001
    MBAR.scale = (max(0.001, lvl), 1, 1) if emp else (0.001,) * 3
    if emp:
        for k, sp in enumerate(SP_B):
            sp.scale = ((0.6 + 1.0 * lvl) * (1.0 + 0.1 * math.sin(t * 8 + k)),) * 3
    if name == "empathy":
        BR_A.location = AWAY

    # ---- the walk: a happy person with toilet paper on their shoe
    st = start_of("unaware")
    a = max(0.0, t - st)
    WALK.location = O1 + Vector((1.75 - 0.22 * a, -0.25, 0.008 * abs(math.sin(a * 10))))
    WALK.rotation_euler = (0, 0, -0.5)
    WALK_A[0].rotation_euler = (0.5 * math.sin(a * 10), 0, 0)
    WALK_A[1].rotation_euler = (-0.5 * math.sin(a * 10), 0, 0)
    TP.rotation_euler = (0, 0, 0.5 + 0.1 * math.sin(a * 10))
    place(S_IDEA, O1 + Vector((1.35, 0.25, 0.7)), t - EV["idea"] + 0.3 if name == "unaware" else -1)

B.render_settings(FPS, samples=int(os.environ.get("YT_SAMPLES", "24")), motion_blur=0.0)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1) / FPS)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
