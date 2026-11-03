"""Pastel toy kit, 'Five minutes away': bevelled props in flat pastel colors, bright soft daylight, numbers on dark signs that count
up through text bodies set each frame. Sets sit along x, 10 m apart, each a counter or a wall at table height. Shots, timed by
render_late.py:

  phone, shower, phone2   a phone on the bathroom vanity says 5 min away; pull back to the shower running, steam rising
  label                   the living room wall: PLANNING FALLACY
  desk, desk~2, worst     a desk with a thesis stack and a calendar; the sign counts 34 to 56 days on events.took; the worst case sign
  clock, clock~2          the kitchen wall clock; the sign counts seconds from events.count0 to 77 at events.count1
  timer                   a kitchen timer at 5:00, the sign 6.4 MIN on events.timer
  plan                    the front door, coat on the hook, the sign PLAN FOR 20 MIN on events.twenty

blender -b --factory-startup -P late_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
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

# ------------------------------------------------------------------ 0 bathroom: phone on the vanity, the shower running

O0 = room(0, "BFE3EC", "E9E1D6", counter="F7F4EE")
for k in range(10):                                      # tile seams, a hair in front of the wall
    rbox(f"seam{k}", -3, 3, 0.317, 0.319, 1.0 + k * 0.15, 1.004 + k * 0.15, "A9D2DD", bev=0, off=O0)
rbox("mirror", -0.42, 0.12, 0.29, 0.31, 1.15, 1.75, "DDEFF5", bev=0.01, off=O0, rough=0.08)
cyl("basin", 0.16, 0.9, 0.95, -0.15, 0.0, "FFFFFF", off=O0, bev=0.01)
cyl("tap", 0.015, 0.9, 1.06, -0.15, 0.19, "B8C0C8", off=O0)
PHONE = B.link(bpy.data.objects.new("phone", None))
PHONE.location = O0 + Vector((-0.5, -0.08, 0.905))
PHONE.rotation_euler = (math.radians(-12), 0, math.radians(8))
rbox("stand", -0.04, 0.04, -0.03, 0.03, 0, 0.02, "EE6F52", parent=PHONE)
SCR = B.link(bpy.data.objects.new("scr", None))
SCR.parent = PHONE
SCR.location = (0, 0, 0.1)
rbox("ph", -0.042, 0.042, -0.005, 0.005, -0.085, 0.085, "2F3843", bev=0.008, parent=SCR, rough=0.3)
rbox("phs", -0.038, 0.038, -0.0062, -0.0052, -0.08, 0.08, "F7F8FA", bev=0.004, parent=SCR, rough=0.2)
text("phname", "him", 0.008, "2F3843", (0, -0.0066, 0.068), SCR)
BUB1 = rbox("bub1", -0.036, 0.026, -0.0075, -0.0065, 0.016, 0.044, "E3E6EA", bev=0.004, parent=SCR)
T1 = text("bub1t", "5 min away!", 0.0105, "2F3843", (-0.005, -0.0078, 0.03), SCR)
BUB2 = rbox("bub2", -0.026, 0.036, -0.0075, -0.0065, -0.016, 0.01, "2F7FD0", bev=0.004, parent=SCR)
T2 = text("bub2t", "where are u", 0.0095, "FFFFFF", (0.005, -0.0078, -0.003), SCR)
BUB3 = rbox("bub3", -0.036, 0.026, -0.0075, -0.0065, -0.05, -0.022, "E3E6EA", bev=0.004, parent=SCR)
T3 = text("bub3t", "5 min away!", 0.0105, "2F3843", (-0.005, -0.0078, -0.036), SCR)
# the shower, right of the vanity
SX = 1.25
rbox("trayb", SX - 0.45, SX + 0.45, -0.45, 0.32, 0, 0.08, "FFFFFF", off=O0)
GLASS = B.material("glass", hexc("E6F5FA"), rough=0.15)
GLASS.surface_render_method = "BLENDED"
B.bsdf(GLASS).inputs["Alpha"].default_value = 0.35
g = B.mesh_from("glassf", B.box(SX - 0.44, SX + 0.44, -0.46, -0.44, 0.08, 2.0), [GLASS])
g.location = O0
rbox("frame", SX - 0.46, SX - 0.43, -0.47, -0.43, 0.08, 2.0, "B8C0C8", bev=0.004, off=O0)
rbox("head", SX - 0.05, SX + 0.05, 0.0, 0.3, 1.85, 1.9, "B8C0C8", bev=0.01, off=O0)
cyl("rose", 0.07, 1.8, 1.85, SX, 0.05, "B8C0C8", off=O0)
rbox("towel", SX - 0.75, SX - 0.55, 0.26, 0.3, 1.0, 1.45, "F2A7B5", bev=0.02, off=O0)
DUCK = [ball("duck", 0.05, "F6C945", O0 + Vector((-0.66, 0.15, 0.94)), (1.2, 1, 0.8)),
        ball("duckh", 0.032, "F6C945", O0 + Vector((-0.62, 0.15, 1.0))),
        ball("duckb", 0.014, "EE6F52", O0 + Vector((-0.59, 0.13, 0.995)), (1.4, 1, 0.6))]
STEAM = [ball(f"steam{i}", 0.09, "FFFFFF", AWAY) for i in range(18)]
srng = random.Random(3)
STEAM_P = [(srng.uniform(-0.3, 0.3), srng.uniform(-0.3, 0.2), srng.random(), srng.uniform(0.7, 1.3)) for _ in STEAM]
DROPS = [rbox(f"drop{i}", -0.004, 0.004, -0.004, 0.004, -0.03, 0.03, "8FCDEE", bev=0, rough=0.1) for i in range(30)]
DROP_P = [(srng.uniform(-0.12, 0.12), srng.uniform(-0.1, 0.15), srng.random()) for _ in DROPS]

# ------------------------------------------------------------------ 1 living room: the label

O1 = room(1, "F6D8B8", "D79A5F")
rbox("couch", -0.75, 0.75, -0.2, 0.3, 0, 0.42, "83A392", bev=0.06, off=O1)
rbox("back", -0.75, 0.75, 0.12, 0.3, 0.42, 0.8, "83A392", bev=0.06, off=O1)
for x in (-0.82, 0.82):
    rbox(f"arm{x}", x - 0.08, x + 0.08, -0.2, 0.3, 0, 0.58, "6F8F7E", bev=0.05, off=O1)
for x in (-0.36, 0.36):
    rbox(f"cush{x}", x - 0.34, x + 0.34, -0.18, 0.12, 0.42, 0.52, "9DBAA9", bev=0.04, off=O1)
cyl("pot", 0.12, 0, 0.3, 1.15, 0.0, "EE6F52", off=O1, r2=0.09)
for k in range(5):
    ball(f"leaf{k}", 0.12, "6FAF6F", O1 + Vector((1.15 + 0.08 * math.cos(k * 1.3), 0.0, 0.42 + 0.09 * k)), (0.7, 0.7, 1.4))
S_LABEL, TX_LABEL = sign("s_label", O1 + Vector((0, 0.3, 1.25)), "PSYCHOLOGISTS CALL IT", "PLANNING", "FALLACY", w=0.7, h=0.42)
TX_LABEL["big"].location.z = 0.035
TX_LABEL["foot"].data.size = TX_LABEL["big"].data.size
TX_LABEL["foot"].location.z = -0.095
TX_LABEL["head"].location.z = 0.15

# ------------------------------------------------------------------ 2 desk: the thesis, the calendar, two signs

O2 = room(2, "D9E6F5", "C9A27A", counter="D79A5F", top="E6B47E")
for k in range(9):
    rbox(f"paper{k}", -0.14, 0.14, -0.19, 0.19, 0.9 + k * 0.012, 0.909 + k * 0.012, "FFFFFF" if k % 2 else "F4F1E8",
         bev=0.002, off=O2 + Vector((-0.25, -0.05, 0)))
rbox("cover", -0.14, 0.14, -0.19, 0.19, 1.008, 1.016, "2F7FD0", bev=0.002, off=O2 + Vector((-0.25, -0.05, 0)))
text("covert", "THESIS", 0.035, "FFFFFF", O2 + Vector((-0.25, -0.05, 1.018))).rotation_euler = (0, 0, 0)
cyl("mug", 0.04, 0.9, 1.0, 0.3, -0.05, "EE6F52", off=O2)
rbox("lamp", 0.45, 0.55, 0.0, 0.1, 0.9, 1.25, "F6C945", bev=0.02, off=O2)
CAL = Vector((-0.25, 0.3, 1.35))
rbox("calback", -0.15, 0.15, -0.006, 0.0, -0.18, 0.18, "2F3843", bev=0.004, off=O2 + CAL)
PAGES = []
for k in range(8):
    r = B.link(bpy.data.objects.new(f"page{k}", None))
    r.location = O2 + CAL + Vector((0, -0.008 - 0.001 * k, 0.16))
    rbox(f"pageb{k}", -0.14, 0.14, -0.0008, 0.0008, -0.32, 0, "FFFFFF", bev=0.002, parent=r)
    rbox(f"pageh{k}", -0.14, 0.14, -0.0012, -0.0009, -0.08, 0, "EE6F52", bev=0, parent=r)
    text(f"paget{k}", str(34 + 3 * k), 0.07, "2F3843", (0, -0.0014, -0.2), r).rotation_euler = (math.pi / 2, 0, 0)
    PAGES.append(r)
S_DAYS, TX_DAYS = sign("s_days", O2 + Vector((0.17, 0.3, 1.38)), "THEY GUESSED", "34 DAYS", "HONORS THESIS, 1994")
WORST_AT = O2 + Vector((0.17, 0.3, 1.72))
S_WORST, TX_WORST = sign("s_worst", WORST_AT, "WORST CASE GUESS", "49 DAYS", "STILL A WEEK SHORT")

# ------------------------------------------------------------------ 3 kitchen: the wall clock, the timer

O3 = room(3, "F2E3A6", "E9E1D6", counter="83A392")
CLK = O3 + Vector((-0.17, 0.3, 1.42))
cyl("clkrim", 0.2, 0, 0.04, 0, 0, "2F3843", seg=64).rotation_euler = (math.pi / 2, 0, 0)
bpy.data.objects["clkrim"].location = CLK
cyl("clkface", 0.18, 0, 0.012, 0, 0, "FFFFFF", seg=64).rotation_euler = (math.pi / 2, 0, 0)
bpy.data.objects["clkface"].location = CLK + Vector((0, -0.03, 0))
for k in range(12):
    a = k * math.pi / 6
    tk = rbox(f"tick{k}", -0.004, 0.004, -0.002, 0.0, -0.02, 0.02, "2F3843", bev=0)
    tk.location, tk.rotation_euler = CLK + Vector((0.15 * math.sin(a), -0.043, 0.15 * math.cos(a))), (0, a, 0)
def hand(name, ln, wd, color):
    r = B.link(bpy.data.objects.new(name, None))
    r.location = CLK + Vector((0, -0.046, 0))
    rbox(name + "b", -wd / 2, wd / 2, -0.002, 0.0, -0.02, ln, color, bev=0, parent=r)
    return r
HOUR, MINUTE, SECOND = hand("hour", 0.08, 0.012, "2F3843"), hand("minute", 0.13, 0.008, "2F3843"), hand("second", 0.15, 0.004, "EE6F52")
S_SEC, TX_SEC = sign("s_sec", O3 + Vector((0.21, 0.3, 1.42)), "ONE MINUTE", "60 S", "BY THE CLOCK", w=0.36)
TIMER = Vector((-0.1, -0.05, 0.9))
rbox("timerb", -0.08, 0.08, -0.05, 0.05, 0, 0.1, "F6C945", bev=0.02, off=O3 + TIMER)
rbox("timers", -0.06, 0.06, -0.052, -0.05, 0.03, 0.08, "2F3843", bev=0.004, off=O3 + TIMER)
TIMER_T = text("timert", "5:00", 0.035, "8FF0A4", O3 + TIMER + Vector((0, -0.054, 0.055)))
cyl("knob", 0.015, 0.1, 0.12, 0.05, 0, "EE6F52", off=O3 + TIMER)
rbox("board", 0.15, 0.45, -0.15, 0.1, 0.9, 0.92, "D79A5F", bev=0.006, off=O3)
for k, c in enumerate(("F6C945", "EE6F52", "6FAF6F")):
    ball(f"veg{k}", 0.035, c, O3 + Vector((0.22 + 0.08 * k, -0.03, 0.955)))
S_HIS, TX_HIS = sign("s_his", O3 + Vector((0.21, 0.3, 1.1)), "HIS 5 MINUTES", "6.4 MIN", "OF YOURS", w=0.36, h=0.24)

# ------------------------------------------------------------------ 4 front door: coat, keys, the plan

O4 = room(4, "C7D7EA", "D79A5F")
rbox("door", -0.45, 0.45, 0.26, 0.32, 0, 2.05, "EE6F52", bev=0.02, off=O4)
for z in (0.55, 1.35):
    rbox(f"panel{z}", -0.33, 0.33, 0.255, 0.26, z, z + 0.6, "F08A72", bev=0.01, off=O4)
ball("knobd", 0.035, "F6C945", O4 + Vector((0.34, 0.23, 1.0)))
rbox("mat", -0.5, 0.5, -0.4, 0.2, 0, 0.015, "83A392", bev=0.005, off=O4)
rbox("hook", 0.62, 0.95, 0.28, 0.32, 1.55, 1.6, "D79A5F", bev=0.008, off=O4)
rbox("coat", 0.68, 0.9, 0.2, 0.28, 0.95, 1.55, "2F7FD0", bev=0.05, off=O4)
rbox("bowl", -0.95, -0.6, -0.1, 0.2, 0.0, 0.85, "F7F4EE", bev=0.02, off=O4)
cyl("keys", 0.05, 0.85, 0.9, -0.78, 0.05, "B8C0C8", off=O4, r2=0.03)
S_PLAN, TX_PLAN = sign("s_plan", O4 + Vector((0, 0.24, 2.35)), "SO PLAN FOR", "20 MIN", "TO BE SAFE", w=0.5)

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
    "phone": lambda u: lc((-0.47, -0.36, 1.04), (-0.48, -0.31, 1.035), (-0.5, -0.08, 1.0), u, O0),
    "shower": lambda u: lc((0.5, -2.4, 1.35), (0.7, -2.7, 1.4), (0.85, 0.0, 1.15), u, O0),
    "phone2": lambda u: lc((-0.52, -0.36, 1.03), (-0.5, -0.31, 1.02), (-0.5, -0.08, 1.0), u, O0),
    "label": lambda u: lc((-0.15, -1.75, 1.15), (0.0, -1.55, 1.15), (0, 0, 1.08), u, O1),
    "desk": lambda u: lc((-0.05, -1.5, 1.42), (0.0, -1.35, 1.4), (0.0, 0, 1.3), u, O2),
    "worst": lambda u: lc((0.25, -0.95, 1.6), (0.18, -0.85, 1.62), (0.12, 0.3, 1.6), u, O2),
    "clock": lambda u: lc((-0.05, -1.2, 1.42), (0.0, -1.1, 1.42), (0.0, 0.3, 1.38), u, O3),
    "timer": lambda u: lc((0.05, -1.0, 1.2), (0.1, -0.9, 1.18), (0.1, 0, 1.1), u, O3),
    "plan": lambda u: lc((0.25, -2.7, 1.55), (0.1, -2.4, 1.6), (0, 0, 1.55), u, O4),
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

def apply_state(t):
    name, cut, age, second, length = shot_at(t)
    loc, tg, lens = alt_cam(name, cut) if second else CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    cam.data.dof.use_dof = False

    # phone: bubbles pop in
    p2 = name == "phone2"
    t0 = 0.0 if not p2 else [s for s, n in SHOTS if n == "phone2"][0]
    a = t - t0
    for ob, tx, d in ((BUB1, T1, 0.25), (BUB2, T2, 99 if not p2 else -9), (BUB3, T3, 99 if not p2 else 0.3)):
        k = 1.0 if p2 and ob is BUB1 else (0.0 if a < d else min(1.0, back_out((a - d) / 0.25)))
        if not p2 and ob is BUB1:
            k = 1.0 if a > 0.5 else (0.0 if a < 0.25 else back_out((a - 0.25) / 0.25))
        ob.scale = tx.scale = (max(0.001, k),) * 3
    if p2:
        T2.data.body = "sent you a reel"
    # shower: steam and water while the shower shot runs, steam lingers after
    on = name in ("shower",) or t > 0.5
    q = math.floor(t * 12) / 12
    for ob, (x, y, ph, sp) in zip(STEAM, STEAM_P):
        f = (ph + q * 0.18 * sp) % 1.0
        ob.location = O0 + Vector((SX + x * (1 + f), y - 0.1, 0.4 + 1.9 * f)) if on else AWAY
        s = 0.6 + 1.6 * f
        ob.scale = (s, s, s * 0.8)
    for ob, (x, y, ph) in zip(DROPS, DROP_P):
        f = (ph + t * 2.2) % 1.0
        ob.location = O0 + Vector((SX + x * (1 + f), 0.05 + y, 1.78 - 1.65 * f))

    # desk: the counter climbs 34 to 56 on 'took', calendar pages tear off
    took = EV["took"]
    if t < EV["guess"]:
        TX_DAYS["big"].data.body = "?"
    elif t < took:
        TX_DAYS["big"].data.body = "34 DAYS"
        TX_DAYS["head"].data.body = "THEY GUESSED"
    else:
        u = smooth01((t - took) / 1.3)
        TX_DAYS["head"].data.body = "IT TOOK"
        TX_DAYS["big"].data.body = f"{round(34 + 22 * u)} DAYS"
    for k, pg in enumerate(PAGES):
        tk = took + 0.15 * k
        f = max(0.0, (t - tk) / 0.6)
        base = O2 + CAL + Vector((0, -0.008 - 0.001 * (len(PAGES) - k), 0.16))
        pg.location = base + Vector((0.12 * f, -0.06 * f, -0.5 * f * f)) if f > 0 else base
        pg.rotation_euler = (-1.2 * min(f, 1.2), 0, 0.8 * f)
        if f > 1.4:
            pg.location = AWAY

    # clock: real time, then a minute that runs to 77
    c0, c1 = EV["count0"], EV["count1"]
    if t < c0:
        secs = t * 1.0
        TX_SEC["big"].data.body = "60 S"
        TX_SEC["head"].data.body, TX_SEC["foot"].data.body = "ONE MINUTE", "BY THE CLOCK"
    else:
        u = min(1.0, (t - c0) / max(0.5, c1 - c0))
        secs = 77 * u
        TX_SEC["head"].data.body, TX_SEC["foot"].data.body = "ONE MINUTE", "FELT BY TYPE B"
        TX_SEC["big"].data.body = f"{int(secs)} S"
    SECOND.rotation_euler = (0, math.floor(secs) * math.pi / 30, 0)
    MINUTE.rotation_euler = (0, 2.0 + secs * math.pi / 1800, 0)
    HOUR.rotation_euler = (0, 5.3, 0)

    S_WORST.location = WORST_AT if name == "worst" else AWAY

    # timer and its sign
    tm = EV["timer"]
    TIMER_T.data.body = "5:00"
    S_HIS.scale = (1, 1, 1) if t >= tm else (0.001,) * 3
    if t >= tm:
        pop(S_HIS, t - tm)
    tw = EV["twenty"]
    if t >= tw:
        pop(S_PLAN, t - tw)
    else:
        S_PLAN.scale = (0.001,) * 3

B.render_settings(FPS, samples=int(os.environ.get("LATE_SAMPLES", "24")), motion_blur=0.0)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1) / FPS)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
