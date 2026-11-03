"""Pastel toy kit, "She is not unphotogenic": bevelled pastel props, bright soft daylight, numbers on dark signs. Our cast is a toy
wig-stand head (egg face, a hair swoop on one side, a mole on one cheek) so the mirror flip shows. Sets sit along x, 10 m apart.
Shots, timed by render_selfie.py: bin (polaroids dropping into a bin), mirror (her head and its flipped reflection), prints (true
and mirror prints, the votes pop on events.pick1 / pick2), label (MERE EXPOSURE EFFECT), selfie (phone 12 in away, the nose swells
on events.nose), portrait (tripod at 5 ft, +0%), final (her polaroid on the fridge, TO YOU).

blender -b --factory-startup -P selfie_scene.py -- timing.json out_dir MODE   (MODE: "all" or 1-based frame list)
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

SKIN, HAIR, BLUSH, INKC = "F3C7A6", "6B4A3A", "F29C9C", "2F3843"

def head(name, at, flip=1, parent=None):
    """The toy head on a little stand. flip=-1 mirrors it (the hair swoop and the mole change sides). Returns root, nose."""
    root = B.link(bpy.data.objects.new(name, None))
    root.location = at
    root.parent = parent
    def p(ob):
        ob.parent = root
        return ob
    p(cyl(name + "base", 0.07, 0, 0.02, 0, 0, "F7F4EE", bev=0.006))
    p(cyl(name + "neck", 0.028, 0.02, 0.12, 0, 0, SKIN))
    p(ball(name + "face", 0.085, SKIN, (0, 0, 0.2), (0.9, 0.9, 1.15)))
    p(ball(name + "hair", 0.088, HAIR, (0, 0.008, 0.232), (0.95, 0.95, 0.9)))
    p(ball(name + "swoop", 0.05, HAIR, (flip * 0.05, -0.05, 0.27), (1.3, 0.8, 0.6)))
    for s in (-1, 1):
        p(ball(f"{name}eye{s}", 0.009, INKC, (s * 0.028, -0.074, 0.205)))
        p(ball(f"{name}blush{s}", 0.014, BLUSH, (s * 0.048, -0.064, 0.178), (1, 0.4, 0.7)))
    p(ball(name + "mole", 0.005, "5A3A2E", (-flip * 0.036, -0.071, 0.165)))
    p(rbox(name + "smile", -0.016, 0.016, -0.08, -0.074, 0.152, 0.158, "C0566A", bev=0.002))
    nose = p(ball(name + "nose", 0.013, "EBB08F", (0, -0.082, 0.185), (1.0, 0.9, 1.2)))
    return root, nose

def polaroid(name, parent=None):
    r = B.link(bpy.data.objects.new(name, None))
    r.parent = parent
    rbox(name + "c", -0.045, 0.045, -0.002, 0.002, -0.055, 0.055, "FFFFFF", bev=0.002, parent=r)
    rbox(name + "p", -0.038, 0.038, -0.0032, -0.0021, -0.032, 0.046, "F2A7B5", bev=0, parent=r)
    b = ball(name + "f", 0.016, SKIN, (0, -0.004, 0.01), (1, 0.3, 1.15))
    b.parent = r
    h = ball(name + "h", 0.017, HAIR, (0, -0.0035, 0.018), (1, 0.3, 0.8))
    h.parent = r
    return r

def wall_disc(name, r, color, at, depth=0.025):
    ob = cyl(name, r, 0, depth, 0, 0, color, seg=64)
    ob.rotation_euler = (math.pi / 2, 0, 0)
    ob.location = at
    return ob

# ------------------------------------------------------------------ 0 bedroom dresser: the trash bin, deleted polaroids

O0 = room(0, "E7D5F0", "D79A5F", counter="F7F4EE", top="F2A7B5")
for x in (-0.35, 0.35):
    rbox(f"drawer{x}", x - 0.3, x + 0.3, -0.302, -0.3, 0.45, 0.8, "EFE9F5", bev=0.006, off=O0)
    ball(f"knob{x}", 0.018, "F6C945", O0 + Vector((x, -0.31, 0.62)))
BIN = Vector((0.18, -0.02, 0.9))
cyl("bin", 0.11, 0.0, 0.22, 0, 0, "83A392", off=O0 + BIN, r2=0.13, bev=0.005)
cyl("binin", 0.115, 0.205, 0.215, 0, 0, "4F6F5E", off=O0 + BIN)
cyl("lampb", 0.07, 0.9, 0.93, -0.45, 0.1, "F6C945", off=O0)
cyl("lamps", 0.012, 0.93, 1.2, -0.45, 0.1, "F6C945", off=O0)
cyl("lampsh", 0.12, 1.2, 1.36, -0.45, 0.1, "FFF4E4", off=O0, r2=0.07)
rbox("book", -0.25, -0.07, -0.1, 0.05, 0.9, 0.94, "2F7FD0", bev=0.006, off=O0)
POLS = [polaroid(f"pol{i}") for i in range(7)]
S_DEL, TX_DEL = sign("s_del", O0 + Vector((-0.12, 0.3, 1.5)), "PHOTOS OF HER", "0 KEPT", "THIS WEEK", w=0.42, h=0.25)

# ------------------------------------------------------------------ 1 hallway: her head and its mirror image

O1 = room(1, "BFE3EC", "E9E1D6", counter="F7F4EE", top="EE6F52")
HEAD1, NOSE1 = head("h1", O1 + Vector((-0.3, -0.05, 0.9)))
MIR = O1 + Vector((0.28, 0.25, 1.22))
wall_disc("mirframe", 0.26, "F6C945", MIR, 0.04)
wall_disc("mirglass", 0.23, "DDEFF5", MIR + Vector((0, -0.03, 0)), 0.012)
HEADM, NOSEM = head("hm", MIR + Vector((0, -0.035, -0.16)), flip=-1)
HEADM.scale = (1.15, 0.3, 1.15)
S_SEE, TX_SEE = sign("s_see", O1 + Vector((-0.3, 0.3, 1.5)), "WHAT YOU SEE", "HER", "THE REAL FACE", w=0.36, h=0.22)
S_SHE, TX_SHE = sign("s_she", MIR + Vector((0, -0.05, 0.38)), "WHAT SHE SEES", "FLIPPED", "EVERY MORNING", w=0.36, h=0.22)

# ------------------------------------------------------------------ 2 photo lab: two prints, two votes

O2 = room(2, "F6D8B8", "C9A27A")
for k, (x, fl, tag) in enumerate(((-0.42, 1, "TRUE PRINT"), (0.42, -1, "MIRROR PRINT"))):
    for s in (-1, 1):
        rbox(f"easel{k}{s}", x + s * 0.2 - 0.015, x + s * 0.2 + 0.015, -0.02, 0.02, 0, 1.25, "D79A5F", bev=0.006, off=O2)
    rbox(f"ledge{k}", x - 0.28, x + 0.28, -0.06, 0.03, 0.62, 0.65, "D79A5F", bev=0.006, off=O2)
    rbox(f"print{k}", x - 0.25, x + 0.25, -0.03, -0.02, 0.65, 1.3, "FFFFFF", bev=0.004, off=O2)
    rbox(f"printbg{k}", x - 0.22, x + 0.22, -0.034, -0.03, 0.75, 1.27, "BFE3EC", bev=0, off=O2)
    hd, _ = head(f"hp{k}", O2 + Vector((x, -0.035, 0.76)), flip=fl)
    hd.scale = (2.0, 0.25, 2.0)
    text(f"tag{k}", tag, 0.035, INKC, O2 + Vector((x, -0.036, 0.69)))
S_PICK1, TX_PICK1 = sign("s_pick1", O2 + Vector((0.42, -0.08, 1.5)), "SHE PICKED", "THIS ONE", "MITA ET AL. 1977", w=0.42, h=0.24)
S_PICK2, TX_PICK2 = sign("s_pick2", O2 + Vector((-0.42, -0.08, 1.5)), "HER FRIENDS PICKED", "THIS ONE", "SAME STUDY", w=0.42, h=0.24)

# ------------------------------------------------------------------ 3 living room: the label, a wall of mirrors

O3 = room(3, "F2E3A6", "D79A5F")
for i in range(10):
    if i in (2, 7):
        continue
    x, z = -0.9 + (i % 5) * 0.45, 1.75 if i < 5 else 0.85
    wall_disc(f"wm{i}", 0.11, "F6C945" if i % 2 else "EE6F52", O3 + Vector((x, 0.3, z)))
    wall_disc(f"wmg{i}", 0.09, "DDEFF5", O3 + Vector((x, 0.275, z)), 0.01)
rbox("sofa", -0.75, 0.75, -0.2, 0.3, 0, 0.42, "83A392", bev=0.06, off=O3)
rbox("sofab", -0.75, 0.75, 0.12, 0.3, 0.42, 0.62, "83A392", bev=0.06, off=O3)
S_LABEL, TX_LABEL = sign("s_label", O3 + Vector((0, 0.27, 1.3)), "PSYCHOLOGISTS CALL IT", "MERE EXPOSURE", "EFFECT", w=0.7, h=0.42)
TX_LABEL["big"].location.z = 0.035
TX_LABEL["foot"].data.size = TX_LABEL["big"].data.size
TX_LABEL["foot"].location.z = -0.095
TX_LABEL["head"].location.z = 0.15

# ------------------------------------------------------------------ 4 studio: selfie stick at 12 in, then a tripod at 5 ft

O4 = room(4, "C7D7EA", "E9E1D6")
rbox("ped4", -0.15, 0.15, -0.15, 0.15, 0, 1.0, "F7F4EE", bev=0.01, off=O4)
HEAD4, NOSE4 = head("h4", O4 + Vector((0, 0, 1.0)))
HEAD4.scale = (1.6, 1.6, 1.6)
STICK = B.link(bpy.data.objects.new("stick", None))
rbox("stickp", -0.035, 0.035, -0.005, 0.005, -0.07, 0.07, INKC, bev=0.006, parent=STICK, rough=0.3)
rbox("sticks", -0.032, 0.032, 0.005, 0.0062, -0.065, 0.065, "F7F8FA", bev=0.003, parent=STICK)
rbox("stickr", -0.006, 0.006, -0.006, 0.006, -0.6, -0.07, "B8C0C8", bev=0, parent=STICK)
rbox("tape4", -0.004, 0.004, -0.305, -0.13, 1.001, 1.004, "F6C945", bev=0, off=O4)
TRIPOD = B.link(bpy.data.objects.new("tripod", None))
rbox("camb", -0.06, 0.06, -0.04, 0.04, 1.25, 1.33, INKC, bev=0.01, parent=TRIPOD)
lens_ob = cyl("camlens", 0.025, 0, 0.05, 0, 0, "B8C0C8")
lens_ob.parent, lens_ob.location, lens_ob.rotation_euler = TRIPOD, (0, 0.09, 1.29), (math.pi / 2, 0, 0)
for a in (0, 2.1, 4.2):
    lg = rbox(f"leg{a}", -0.008, 0.008, -0.008, 0.008, 0, 1.27, "B8C0C8", bev=0, parent=TRIPOD)
    lg.location, lg.rotation_euler = (0.18 * math.sin(a), 0.18 * math.cos(a), 0), (-0.14 * math.cos(a), 0.14 * math.sin(a), 0)
rbox("floortape", -0.02, 0.02, -1.52, -0.15, 0.0, 0.004, "F6C945", bev=0, off=O4)
S_NOSE, TX_NOSE = sign("s_nose", O4 + Vector((0.42, 0.3, 1.55)), "SELFIE AT 12 IN", "NOSE +30%", "WIDER", w=0.42, h=0.25)
S_FIVE, TX_FIVE = sign("s_five", O4 + Vector((-0.42, 0.3, 1.55)), "PHOTO AT 5 FT", "+0%", "NO DIFFERENCE", w=0.42, h=0.25)

# ------------------------------------------------------------------ 5 kitchen: the fridge door, her polaroid

O5 = room(5, "D9E6F5", "E9E1D6")
rbox("fridge", -0.42, 0.42, -0.35, 0.3, 0, 1.85, "F7F4EE", bev=0.04, off=O5)
rbox("fgap", -0.42, 0.42, -0.356, -0.35, 1.2, 1.21, "B8C0C8", bev=0, off=O5)
rbox("fhandle", 0.3, 0.34, -0.4, -0.356, 1.25, 1.6, "B8C0C8", bev=0.008, off=O5)
FPOL = polaroid("fpol")
FPOL.location = O5 + Vector((-0.25, -0.356, 1.3))
FPOL.scale = (1.6, 1.6, 1.6)
FPOL.rotation_euler = (0, 0.12, 0)
ball("magnet", 0.022, "EE6F52", O5 + Vector((-0.25, -0.366, 1.38)), (1, 0.5, 1))
for k, (x, z, c) in enumerate(((0.2, 1.05, "F6C945"), (-0.2, 0.95, "6FAF6F"), (0.15, 0.75, "2F7FD0"))):
    rbox(f"fnote{k}", x - 0.06, x + 0.06, -0.359, -0.354, z - 0.06, z + 0.06, c, bev=0.002, off=O5)
S_YOU, TX_YOU = sign("s_you", O5 + Vector((0.13, -0.37, 1.6)), "WHAT SHE LOOKS LIKE", "TO YOU", "THE REAL FACE", w=0.46, h=0.26)

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
    "bin": lambda u: lc((0.0, -1.35, 1.42), (0.02, -1.2, 1.4), (0.0, 0.0, 1.17), u, O0),
    "mirror": lambda u: lc((-0.05, -1.9, 1.32), (0.0, -1.75, 1.32), (0.0, 0.0, 1.25), u, O1),
    "prints": lambda u: lc((-0.05, -2.3, 1.15), (0.0, -2.1, 1.15), (0.0, 0.0, 1.1), u, O2),
    "label": lambda u: lc((-0.15, -1.85, 1.25), (0.0, -1.65, 1.25), (0, 0, 1.2), u, O3),
    "selfie": lambda u: lc((0.8, -1.05, 1.45), (0.7, -0.95, 1.45), (0.1, -0.1, 1.35), u, O4),
    "portrait": lambda u: lc((-0.55, -2.4, 1.5), (-0.45, -2.2, 1.5), (-0.12, 0.0, 1.35), u, O4),
    "final": lambda u: lc((0.25, -2.0, 1.5), (0.15, -1.8, 1.5), (0, -0.3, 1.45), u, O5),
}

def base_of(i):
    return SHOTS[i][1].split("~")[0]

def shot_at(t):
    k = max([0] + [i for i, (s, _) in enumerate(SHOTS) if t >= s - 1e-6])
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    cut = max(0.0, min(1.0, (t - SHOTS[k][0]) / max(1e-6, t1 - SHOTS[k][0])))
    return base_of(k), cut, t - SHOTS[k][0], "~" in SHOTS[k][1], t1 - SHOTS[k][0]

def alt_cam(name, u):
    loc, tg, lens = CAMS[name](u)
    d = loc - tg
    return tg + Vector((d.x * 0.6 + 0.35 * d.length * 0.35, d.y * 0.85, d.z)), tg, lens

def pop(ob, age, s=1.0):
    k = 0.0 if age <= 0 else back_out(age / 0.25)
    ob.scale = (max(0.001, k * s),) * 3

def start_of(n):
    return next(s for s, m in SHOTS if m == n)

def apply_state(t):
    name, cut, age, second, length = shot_at(t)
    loc, tg, lens = alt_cam(name, cut) if second else CAMS[name](cut)
    if name == "selfie" and second:                       # her face and the +30% sign, past the phone
        loc, tg, lens = O4 + Vector((-0.35 + 0.05 * cut, -0.95, 1.42)), O4 + Vector((0.15, 0.0, 1.38)), 35
    elif name == "mirror" and second:
        loc, tg, lens = O4 * 0 + O1 + Vector((0.2 + 0.05 * cut, -1.6, 1.38)), O1 + Vector((0.05, 0.0, 1.32)), 35
    elif name == "prints" and second:
        loc, tg, lens = O2 + Vector((0.05 * cut, -2.7, 1.2)), O2 + Vector((0.0, 0.0, 1.18)), 35
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    cam.data.dof.use_dof = False

    # bin: polaroids fall one after another into the bin
    for k, pl in enumerate(POLS):
        f = t * 1.6 - k * 0.55
        if f < 0 or f > 1.0 or name != "bin":
            pl.location = AWAY
            continue
        pl.location = O0 + BIN + Vector((0.03 * math.sin(k * 2.1), 0.02 * math.cos(k), 0.75 * (1 - f) ** 1.6 + 0.12))
        pl.rotation_euler = (0.3 * f, 0.8 * math.sin(k * 1.7) + 2.0 * f, 0.4 * k)

    # mirror: the two signs pop on mirror~2
    m2 = start_of("mirror~2")
    if name == "mirror" and t >= m2:
        pop(S_SHE, t - m2 - 0.1)
        pop(S_SEE, t - m2 - 0.35)
    else:
        S_SHE.scale = S_SEE.scale = (0.001,) * 3

    # prints: the two votes
    for s, e in ((S_PICK1, "pick1"), (S_PICK2, "pick2")):
        if t >= EV[e]:
            pop(s, t - EV[e])
        else:
            s.scale = (0.001,) * 3

    # selfie: the nose swells on events.nose; the portrait puts it back
    nose = smooth01((t - EV["nose"]) / 0.5) if name == "selfie" else 0.0
    NOSE4.scale = (1.0 + 0.3 * nose, 0.9 * (1 + 0.15 * nose), 1.2)
    STICK.location = O4 + Vector((0, -0.305, 1.3)) if name == "selfie" else AWAY
    TRIPOD.location = O4 + Vector((0, -1.52, 0)) if name == "portrait" else AWAY
    if name == "selfie" and t >= EV["nose"]:
        pop(S_NOSE, t - EV["nose"])
    else:
        S_NOSE.scale = (0.001,) * 3
    if name == "portrait":
        pop(S_FIVE, age - 0.3)
    else:
        S_FIVE.scale = (0.001,) * 3
    if name == "final":
        pop(S_YOU, age - 0.5)
    else:
        S_YOU.scale = (0.001,) * 3

B.render_settings(FPS, samples=int(os.environ.get("SELFIE_SAMPLES", "24")), motion_blur=0.0)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1) / FPS)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
