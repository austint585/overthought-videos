"""Pastel toy kit, "We should hang out sometime": bevelled pastel props, bright soft daylight, numbers on dark signs. The cast is two
toy mugs with faces (you and the friend). Sets sit along x, 10 m apart. Shots, timed by render_hours.py: cafe (the mugs slide up and
stop short, NEXT HANGOUT: SOMETIME), study (a big stopwatch, HALL 2018), bar / bar~2 / bar200 (a wall progress bar fills to 50, 90
and 200 hours, milestone flags pop on events m50 / m90 / m200, the mugs ride the tip), calendar (two days circled on circle1 /
circle2, then 4 HOURS A YEAR), porch (the mugs old on rocking chairs, the year counts up to 2076 from events.years), final (back at
the cafe, a phone between them, HOURS ADDED 0 on events.sent).

blender -b --factory-startup -P hours_scene.py -- timing.json out_dir MODE   (MODE: "all" or 1-based frame list)
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

INKC, BLUSH = "2F3843", "F29C9C"
A_COL, B_COL = "EE6F52", "9FC3DD"

def torus(name, R, r, at, rot, color):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=at, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(mat(color))
    ob.data.shade_smooth()
    return ob

def mug(name, color, at, parent=None, old=False):
    """A toy mug with a face on its -y side; old=True adds a white hair tuft and round glasses."""
    root = B.link(bpy.data.objects.new(name, None))
    root.location = at
    root.parent = parent
    def p(ob):
        ob.parent = root
        return ob
    p(cyl(name + "b", 0.07, 0, 0.14, 0, 0, color, bev=0.01))
    p(cyl(name + "c", 0.062, 0.12, 0.133, 0, 0, "6B4A3A"))
    p(torus(name + "h", 0.038, 0.011, (0.075, 0, 0.075), (math.pi / 2, 0, 0), color))
    for s in (-1, 1):
        p(ball(f"{name}e{s}", 0.009, INKC, (s * 0.024, -0.066, 0.085)))
        p(ball(f"{name}k{s}", 0.012, BLUSH, (s * 0.04, -0.058, 0.064), (1, 0.4, 0.7)))
    p(rbox(name + "m", -0.012, 0.012, -0.072, -0.066, 0.056, 0.061, "C0566A", bev=0.002))
    if old:
        for k, x in enumerate((-0.035, 0.0, 0.035)):
            p(ball(f"{name}t{k}", 0.028, "FBFAF6", (x, 0.0, 0.15 + 0.012 * (k == 1)), (1, 1, 0.7)))
        for s in (-1, 1):
            p(torus(f"{name}g{s}", 0.017, 0.003, (s * 0.024, -0.071, 0.086), (math.pi / 2, 0, 0), INKC))
    return root

def table(name, o, r=0.42, z=0.74, top="F7F4EE"):
    cyl(name + "l", 0.035, 0, z, 0, 0, "B8C0C8", off=o)
    cyl(name + "f", 0.18, 0, 0.03, 0, 0, "B8C0C8", off=o, bev=0.006)
    cyl(name + "t", r, z, z + 0.035, 0, 0, top, off=o, bev=0.008)

def hide(*obs):
    for ob in obs:
        ob.scale = (0.001,) * 3

# ------------------------------------------------------------------ 0 cafe: the two mugs, NEXT HANGOUT SOMETIME

O0 = room(0, "F6D8B8", "C9A27A")
table("t0", O0)
TOP0 = 0.775
MUG_A0 = mug("ma0", A_COL, O0 + Vector((-0.2, 0, TOP0)))
MUG_B0 = mug("mb0", B_COL, O0 + Vector((0.2, 0, TOP0)))
for x in (-0.62, 0.62):
    rbox(f"chair{x}", x - 0.18, x + 0.18, -0.18, 0.18, 0.42, 0.47, "83A392", bev=0.02, off=O0)
    rbox(f"chairb{x}", x - 0.18, x + 0.18, 0.14, 0.18, 0.47, 0.95, "83A392", bev=0.02, off=O0)
    for sx in (-1, 1):
        rbox(f"chl{x}{sx}", x + sx * 0.15 - 0.015, x + sx * 0.15 + 0.015, -0.015, 0.015, 0, 0.42, "D79A5F", bev=0, off=O0)
cyl("plant", 0.12, 0, 0.3, -1.1, 0.1, "F2A7B5", off=O0, bev=0.01)
ball("plantl", 0.22, "6FAF6F", O0 + Vector((-1.1, 0.1, 0.5)), (1, 1, 1.3))
for k, x in enumerate((-0.9, 0.9)):
    wall_disc(f"lamp0{k}", 0.09, "F6C945", O0 + Vector((x, 0.3, 1.9)))
S_NEXT, TX_NEXT = sign("s_next", O0 + Vector((0, 0.3, 1.45)), "NEXT HANGOUT", "SOMETIME", "DATE: TBD", w=0.52, h=0.3)
PHONE = B.link(bpy.data.objects.new("phone", None))
rbox("phb", -0.04, 0.04, -0.08, 0.08, 0, 0.012, INKC, bev=0.008, parent=PHONE, rough=0.3)
rbox("phs", -0.035, 0.035, -0.072, 0.072, 0.012, 0.0135, "9FC3DD", bev=0, parent=PHONE)
S_ZERO, TX_ZERO = sign("s_zero", O0 + Vector((0.0, 0.29, 1.08)), "HOURS ADDED", "0", "BY SENDING THIS", w=0.36, h=0.24)

# ------------------------------------------------------------------ 1 lab: a big stopwatch, HALL 2018

O1 = room(1, "D9E6F5", "E9E1D6", counter="F7F4EE", top="F6C945")
SW = O1 + Vector((-0.3, 0.25, 1.5))
wall_disc("swr", 0.3, "EE6F52", SW, 0.05)
wall_disc("swf", 0.26, "FFFFFF", SW + Vector((0, -0.03, 0)), 0.012)
cyl("swk", 0.05, 0.3, 0.38, 0, 0, "EE6F52", off=SW + Vector((0, -0.02, 0)), bev=0.006)
for k in range(12):
    tk = B.link(bpy.data.objects.new(f"tick{k}", None))
    tk.location = SW + Vector((0, -0.045, 0))
    tk.rotation_euler = (0, k * math.pi / 6, 0)
    rbox(f"tickb{k}", -0.006, 0.006, -0.002, 0.002, 0.2, 0.235, INKC, bev=0, parent=tk)
HAND = B.link(bpy.data.objects.new("hand", None))
HAND.location = SW + Vector((0, -0.05, 0))
rbox("handb", -0.008, 0.008, -0.003, 0.003, -0.02, 0.21, INKC, bev=0, parent=HAND)
ball("handc", 0.02, INKC, SW + Vector((0, -0.055, 0)))
CLIP = O1 + Vector((-0.3, -0.05, 0.9))
rbox("clipb", -0.14, 0.14, -0.1, 0.1, 0, 0.012, "D79A5F", bev=0.004, off=CLIP)
rbox("clipp", -0.12, 0.12, -0.085, 0.085, 0.012, 0.015, "FFFFFF", bev=0, off=CLIP)
for k in range(5):
    rbox(f"clipl{k}", -0.09, 0.09 - 0.03 * (k % 2), 0.05 - 0.03 * k - 0.003, 0.05 - 0.03 * k + 0.003, 0.015, 0.017, "B8C0C8",
         bev=0, off=CLIP)
mug("ma1", A_COL, O1 + Vector((0.18, 0.0, 0.9)))
mug("mb1", B_COL, O1 + Vector((0.45, 0.05, 0.9)))
S_STUDY, TX_STUDY = sign("s_study", O1 + Vector((0.33, 0.3, 1.55)), "HOURS TO MAKE A FRIEND", "HALL 2018", "UNIVERSITY OF KANSAS",
                         w=0.56, h=0.3)

# ------------------------------------------------------------------ 2 long wall: the friendship progress bar

O2 = room(2, "E7D5F0", "D79A5F")
BAR_X0, BAR_X1, BAR_Z, HMAX = -2.2, 2.2, 1.15, 220.0

def bar_x(h):
    return BAR_X0 + (BAR_X1 - BAR_X0) * h / HMAX

rbox("barbg", BAR_X0 - 0.04, BAR_X1 + 0.04, 0.27, 0.32, BAR_Z - 0.09, BAR_Z + 0.09, INKC, bev=0.02, off=O2)
FILL = rbox("barfill", 0, 1, 0.255, 0.27, BAR_Z - 0.065, BAR_Z + 0.065, "F6C945", bev=0)
FILL.location = O2 + Vector((BAR_X0, 0, 0))
FLAGS = {}
for key, h, big, foot in (("m50", 50, "50 HOURS", "CASUAL FRIEND"), ("m90", 90, "90 HOURS", "FRIEND"),
                          ("m200", 200, "200+ HOURS", "CLOSE FRIEND")):
    x = bar_x(h)
    rbox(f"pole{key}", x - 0.01, x + 0.01, 0.24, 0.255, BAR_Z + 0.09, BAR_Z + 0.32, "F7F4EE", bev=0, off=O2)
    FLAGS[key] = sign(f"s{key}", O2 + Vector((x, 0.23, BAR_Z + 0.44)), "STAGE", big, foot, w=0.4, h=0.24)[0]
for h in range(0, 221, 10):
    x = bar_x(h)
    rbox(f"bt{h}", x - 0.004, x + 0.004, 0.25, 0.27, BAR_Z - 0.13, BAR_Z - 0.09, "F7F4EE", bev=0, off=O2)
rbox("track", BAR_X0 - 0.3, BAR_X1 + 0.3, -0.25, 0.05, 0.0, 0.5, "F7F4EE", bev=0.01, off=O2)
MUG_A2 = mug("ma2", A_COL, O2)
MUG_B2 = mug("mb2", B_COL, O2)

# ------------------------------------------------------------------ 3 kitchen: the calendar, two days a year

O3 = room(3, "BFE3EC", "E9E1D6", counter="F7F4EE", top="EE6F52")
CAL = O3 + Vector((-0.33, 0.3, 1.45))
rbox("calb", -0.36, 0.36, -0.02, 0.0, -0.3, 0.3, "FFFFFF", bev=0.006, off=CAL)
rbox("calh", -0.36, 0.36, -0.024, -0.02, 0.2, 0.3, "EE6F52", bev=0, off=CAL)
text("calt", "2026", 0.06, "FFFFFF", CAL + Vector((0, -0.026, 0.25)))
CELLS = []
for r in range(3):
    for c in range(4):
        x, z = -0.255 + c * 0.17, 0.11 - r * 0.15
        rbox(f"cell{r}{c}", x - 0.07, x + 0.07, -0.024, -0.02, z - 0.06, z + 0.06, "F1ECE5", bev=0, off=CAL)
        CELLS.append(CAL + Vector((x, -0.03, z)))
RINGS = [torus(f"ring{k}", 0.058, 0.009, CELLS[ci], (math.pi / 2, 0, 0), "EE6F52") for k, ci in enumerate((3, 8))]
mug("ma3", A_COL, O3 + Vector((0.2, 0.0, 0.9)))
mug("mb3", B_COL, O3 + Vector((0.48, 0.05, 0.9)))
S_TWICE, TX_TWICE = sign("s_twice", O3 + Vector((0.4, 0.3, 1.62)), "HANGOUTS", "2 A YEAR", "2 HOURS EACH", w=0.4, h=0.25)
S_FOUR, TX_FOUR = sign("s_four", O3 + Vector((0.4, 0.3, 1.3)), "PER YEAR", "4 HOURS", "TOGETHER", w=0.4, h=0.25)

# ------------------------------------------------------------------ 4 porch: old mugs in rocking chairs, the year counts up

O4 = room(4, "F2E3A6", "C9A27A")
ROCK = []
for k, (x, col) in enumerate(((-0.32, A_COL), (0.32, B_COL))):
    rk = B.link(bpy.data.objects.new(f"rock{k}", None))
    rk.location = O4 + Vector((x, 0, 0))
    rbox(f"rs{k}", -0.2, 0.2, -0.18, 0.18, 0.4, 0.45, "D79A5F", bev=0.015, parent=rk)
    rbox(f"rb{k}", -0.2, 0.2, 0.14, 0.18, 0.45, 1.0, "D79A5F", bev=0.015, parent=rk)
    for s in (-1, 1):
        for yy in (-1, 1):
            rbox(f"rl{k}{s}{yy}", s * 0.17 - 0.015, s * 0.17 + 0.015, yy * 0.14 - 0.015, yy * 0.14 + 0.015, 0.05, 0.4, "D79A5F",
                 bev=0, parent=rk)
        rbox(f"rr{k}{s}", s * 0.17 - 0.018, s * 0.17 + 0.018, -0.3, 0.3, 0.02, 0.055, "B07A4A", bev=0.014, parent=rk)
    m = mug(f"mo{k}", col, Vector((0, -0.02, 0.45)), parent=rk, old=True)
    m.scale = (1.7, 1.7, 1.7)
    ROCK.append(rk)
rbox("cane", 0.58, 0.61, -0.14, -0.11, 0.0, 0.52, "6B4A3A", bev=0.008, off=O4)
rbox("caneh", 0.58, 0.7, -0.14, -0.11, 0.49, 0.52, "6B4A3A", bev=0.008, off=O4)
S_YEAR, TX_YEAR = sign("s_year", O4 + Vector((0, 0.3, 1.55)), "CLOSE FRIENDS BY", "2026", "AT 4 HOURS A YEAR", w=0.5, h=0.3)

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
    "cafe": lambda u: lc((0.0, -1.55, 1.3), (0.0, -1.35, 1.27), (0.0, 0.0, 1.12), u, O0),
    "study": lambda u: lc((0.05, -2.15, 1.3), (0.0, -1.95, 1.3), (0.0, 0.0, 1.22), u, O1),
    "calendar": lambda u: lc((-0.05, -1.7, 1.35), (0.0, -1.5, 1.35), (0.02, 0.0, 1.27), u, O3),
    "porch": lambda u: lc((0.0, -2.2, 1.15), (0.0, -1.95, 1.12), (0.0, 0.0, 1.0), u, O4),
    "final": lambda u: lc((-0.05, -1.4, 1.22), (0.0, -1.25, 1.2), (0.02, 0.0, 1.13), u, O0),
}

def base_of(i):
    return SHOTS[i][1].split("~")[0]

def shot_at(t):
    k = max([0] + [i for i, (s, _) in enumerate(SHOTS) if t >= s - 1e-6])
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    cut = max(0.0, min(1.0, (t - SHOTS[k][0]) / max(1e-6, t1 - SHOTS[k][0])))
    return base_of(k), cut, t - SHOTS[k][0], "~" in SHOTS[k][1], t1 - SHOTS[k][0]

def pop(ob, age, s=1.0):
    k = 0.0 if age <= 0 else back_out(age / 0.25)
    ob.scale = (max(0.001, k * s),) * 3

def start_of(n):
    return next(s for s, m in SHOTS if m == n)

def bar_hours(t):
    """Hours on the progress bar: fills to 50 by m50, to 90 by m90, to 205 by m200."""
    pts = [(start_of("bar"), 0.0), (EV["m50"], 50.0), (start_of("bar~2"), 50.0), (EV["m90"], 90.0),
           (start_of("bar200"), 90.0), (EV["m200"] + 0.3, 205.0)]
    if t <= pts[0][0]:
        return 0.0
    for (t0, h0), (t1, h1) in zip(pts, pts[1:]):
        if t <= t1:
            return h0 + (h1 - h0) * smooth01((t - t0) / max(1e-6, t1 - t0))
    return pts[-1][1]

def apply_state(t):
    name, cut, age, second, length = shot_at(t)
    hours = bar_hours(t)
    if name == "bar":
        tip = bar_x(hours)
        loc, tg, lens = O2 + Vector((tip + 0.25, -1.75, 1.15)), O2 + Vector((tip + 0.2, 0.0, 1.05)), 35
    elif name == "bar200":
        tip = bar_x(hours)
        loc, tg, lens = O2 + Vector((tip - 0.1, -2.1, 1.2)), O2 + Vector((tip - 0.15, 0.0, 1.1)), 35
    elif name == "calendar" and second:
        loc, tg, lens = O3 + Vector((0.45 + 0.05 * cut, -1.25, 1.42)), O3 + Vector((0.4, 0.0, 1.38)), 35
    elif name == "cafe" and second:
        loc, tg, lens = CAMS["cafe"](cut)
    else:
        loc, tg, lens = CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    cam.data.dof.use_dof = False

    # cafe: the two mugs slide toward each other and stop short; in the final shot they sit closer, the phone between them
    if name == "final":
        MUG_A0.location = O0 + Vector((-0.15, 0, TOP0))
        MUG_B0.location = O0 + Vector((0.2, 0, TOP0))
        PHONE.location = O0 + Vector((0.03, -0.18, TOP0))
        PHONE.rotation_euler = (0, 0, 0.3)
        pop(PHONE, t - EV["sent"] + 0.3)
        pop(S_ZERO, t - EV["sent"] - 0.6)
    else:
        u = smooth01(t / 0.6)
        MUG_A0.location = O0 + Vector((-0.3 + 0.1 * u, 0, TOP0))
        MUG_B0.location = O0 + Vector((0.3 - 0.1 * u, 0, TOP0))
        MUG_A0.rotation_euler = (0, 0, 0.25 * u)
        MUG_B0.rotation_euler = (0, 0, -0.25 * u)
        PHONE.location = AWAY
        hide(S_ZERO)

    # lab: the stopwatch hand sweeps
    HAND.rotation_euler = (0, t * 1.6, 0)

    # bar: the fill and the two mugs ride the tip
    FILL.scale = (max(0.001, bar_x(hours) - BAR_X0), 1, 1)
    tip = bar_x(hours)
    bob = 0.01 * abs(math.sin(t * 9))
    MUG_A2.location = O2 + Vector((tip - 0.1, -0.1, 0.5 + bob))
    MUG_B2.location = O2 + Vector((tip + 0.1, -0.1, 0.5 + 0.01 * abs(math.cos(t * 9))))
    for key, root in FLAGS.items():
        if t >= EV[key]:
            pop(root, t - EV[key])
        else:
            hide(root)

    # calendar: two circled days, then 4 HOURS A YEAR
    for rg, e in zip(RINGS, ("circle1", "circle2")):
        if t >= EV[e]:
            pop(rg, t - EV[e])
        else:
            hide(rg)
    if name == "calendar":
        pop(S_TWICE, age - 0.3)
    else:
        hide(S_TWICE)
    c2 = start_of("calendar~2")
    if t >= c2 and name == "calendar":
        pop(S_FOUR, t - c2 - 0.2)
    else:
        hide(S_FOUR)

    # porch: rocking chairs, the year counts up from 2026 to 2076
    for k, rk in enumerate(ROCK):
        rk.rotation_euler = (0.07 * math.sin(t * 2.4 + k * 1.3), 0, 0)
    y0 = start_of("porch") + 0.4
    yr = 2026 + int(round(50 * smooth01((t - y0) / max(0.5, EV["years"] + 0.3 - y0))))
    TX_YEAR["big"].data.body = str(yr)

B.render_settings(FPS, samples=int(os.environ.get("HOURS_SAMPLES", "24")), motion_blur=0.0)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1) / FPS)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
