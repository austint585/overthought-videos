"""Blender scene for 'The Turkey Is Still A Rock' (render_turkeyrock.py). Pastel toy kit, directed with direct.py.

The set: an evening kitchen. A cream counter along the back wall (dusky blue), a cutting board on its left end under
pendant A, a stainless sink under pendant B with a dusk window above it, a mint fridge on the right with its door open,
dark signs on the wall that change their text through the reel. The cast: a frozen 20 lb turkey in its sealed bag and a
peg-person friend. Shot sheet: ops/episodes/2026-11-25-turkey-rock.md.

blender -b --factory-startup -P turkeyrock_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Writes ../shots.json for qa_direction.py.
"""
import json, math, os, random, sys
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bkit as B
import direct as D

argv = sys.argv[sys.argv.index("--") + 1:]
TIMING, OUT, MODE = argv[0], argv[1], argv[2]
T = json.load(open(TIMING))
FPS, DUR, E = T["fps"], T["duration"], T["events"]
NF = int(round(DUR * FPS))
os.makedirs(OUT, exist_ok=True)
B.clear_scene()
scene = B.scene
AWAY = Vector((0, 0, -1.0e4))
rng = random.Random(11)

def hexc(s):
    def lin(v):
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return tuple(lin(int(s[i:i + 2], 16) / 255) for i in (0, 2, 4))

_mats = {}
def mat(color, rough=0.55, alpha=None):
    k = (color, rough, alpha)
    if k not in _mats:
        m = B.material("m" + color + str(alpha), hexc(color), rough=rough)
        if alpha is not None:
            m.surface_render_method = "BLENDED"
            B.bsdf(m).inputs["Alpha"].default_value = alpha
        _mats[k] = m
    return _mats[k]

def emit_mat(color, strength=1.0):
    m = bpy.data.materials.new("e" + color)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = (*hexc(color), 1)
    e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs[0])
    return m

def rbox(name, x0, x1, y0, y1, z0, z1, color, bev=0.012, parent=None, rough=0.55, m=None):
    ob = B.mesh_from(name, B.box(x0, x1, y0, y1, z0, z1), [m or mat(color, rough)])
    if bev:
        B.bevel(ob, bev)
        B.smooth(ob)
    ob.parent = parent
    return ob

def cyl(name, r, z0, z1, x, y, color, r2=None, seg=48, bev=0.0, parent=None, m=None):
    ob = B.mesh_from(name, B.cyl_z(r, z0, z1, x, y, seg=seg, r2=r2), [m or mat(color)])
    if bev:
        B.bevel(ob, bev)
    B.smooth(ob)
    ob.parent = parent
    return ob

def ball(name, r, color, at, squash=(1, 1, 1), parent=None, m=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(0, 0, 0), segments=32, ring_count=16)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = squash
    ob.rotation_euler = rot
    ob.data.materials.append(m or mat(color))
    ob.data.shade_smooth()
    ob.parent = parent
    ob.location = at
    return ob

def empty(name, at=(0, 0, 0), parent=None):
    ob = B.link(bpy.data.objects.new(name, None))
    ob.parent = parent
    ob.location = at
    return ob

_font = bpy.data.fonts.load(E["font"])

def text(name, body, size, color, at, parent=None, glow=1.0):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body, cu.font, cu.size = body, _font, size
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.resolution_u = 4
    ob = B.link(bpy.data.objects.new(name, cu))
    ob.data.materials.append(emit_mat(color, glow).copy())
    ob.parent = parent
    ob.location = at
    ob.rotation_euler = (math.pi / 2, 0, 0)
    return ob

def set_color(ob, color):
    ob.data.materials[0].node_tree.nodes["Emission"].inputs[0].default_value = (*hexc(color), 1)

class Sign:
    """A dark rounded board on the wall: a small head, a big line, a small foot. Text changes through the reel."""
    def __init__(self, name, at, w=0.46, h=0.27, big=0.085):
        self.w, self.h, self.bigmax = w, h, big
        self.root = empty(name, at)
        rbox(name + "p", -w / 2, w / 2, -0.012, 0.012, -h / 2, h / 2, "232C38", parent=self.root, rough=0.5)
        rbox(name + "r", -w / 2 + 0.012, w / 2 - 0.012, -0.0145, -0.0125, h / 2 - 0.018, h / 2 - 0.012, "9FC3DD", bev=0,
             parent=self.root)
        self.head = text(name + "h", "", 0.032, "F4F1E8", (0, -0.016, h * 0.3), self.root)
        self.big = text(name + "b", "", big, "FFFFFF", (0, -0.016, -0.012), self.root, glow=1.1)
        self.foot = text(name + "f", "", 0.028, "F4F1E8", (0, -0.016, -h * 0.34), self.root)

    def fit(self, ob, s, cap):
        ob.data.body = s
        ob.data.size = min(cap, (self.w - 0.06) / (max(1, len(s)) * 0.6))

    def set(self, head, big, foot, color="FFFFFF"):
        self.fit(self.head, head, 0.032)
        self.fit(self.big, big, self.bigmax)
        self.fit(self.foot, foot, 0.028)
        set_color(self.big, color)

# ------------------------------------------------------------------ the kitchen

WALL, FLOOR, CREAM, TOP = "4A607C", "7E5E4A", "F4ECDD", "E6E0D6"
STEEL, MINT, SAGE, WOOD, ORANGE = "B8C0C8", "BFE3D5", "83A392", "D79A5F", "EE6F52"

rbox("floor", -4, 4, -5, 0.32, -0.05, 0, FLOOR, bev=0, rough=0.7)
rbox("wall", -4, 4, 0.32, 0.4, 0, 3.2, WALL, bev=0, rough=0.9)
rbox("skirt", -4, 4, 0.30, 0.32, 0, 0.1, "26323F", bev=0)
# counter, with a hole for the sink (x 0.05..0.65, y -0.22..0.18)
rbox("cabL", -1.05, 0.04, -0.28, 0.30, 0.1, 0.86, CREAM, bev=0.01)
rbox("cabM", 0.04, 0.66, -0.28, 0.30, 0.1, 0.56, CREAM, bev=0.0)
rbox("cabMF", 0.04, 0.66, -0.28, -0.232, 0.1, 0.86, CREAM, bev=0.0)
rbox("cabR", 0.66, 1.25, -0.28, 0.30, 0.1, 0.86, CREAM, bev=0.01)
rbox("kick", -1.02, 1.22, -0.24, 0.30, 0, 0.1, "26323F", bev=0)
for k, (x0, x1) in enumerate(((-1.05, -0.5), (-0.5, 0.05), (0.65, 1.25))):
    for j, (y0, y1) in enumerate(((-0.29, -0.15),)):
        pass
for k in range(5):                                           # cabinet door seams
    x = -1.05 + 0.46 * k
    rbox(f"seam{k}", x + 0.44, x + 0.455, -0.285, -0.281, 0.14, 0.82, "D9D0BF", bev=0)
for k, x in enumerate((-0.83, -0.37, 0.09, 0.55, 1.01)):
    rbox(f"knob{k}", x + 0.15, x + 0.19, -0.3, -0.282, 0.74, 0.76, STEEL, bev=0.004)
TOPM = mat(TOP, 0.35)
rbox("topL", -1.07, 0.05, -0.31, 0.31, 0.86, 0.9, TOP, m=TOPM, bev=0.006)
rbox("topR", 0.65, 1.27, -0.31, 0.31, 0.86, 0.9, TOP, m=TOPM, bev=0.006)
rbox("topF", 0.05, 0.65, -0.31, -0.22, 0.86, 0.9, TOP, m=TOPM, bev=0)
rbox("topB", 0.05, 0.65, 0.18, 0.31, 0.86, 0.9, TOP, m=TOPM, bev=0)
SM = B.material("steel", hexc("56606B"), metallic=0.3, rough=0.5)
rbox("basinB", 0.05, 0.65, -0.22, 0.18, 0.58, 0.6, STEEL, m=SM, bev=0)
rbox("basinF", 0.05, 0.65, -0.225, -0.215, 0.58, 0.88, STEEL, m=SM, bev=0)
rbox("basinK", 0.05, 0.65, 0.175, 0.185, 0.58, 0.88, STEEL, m=SM, bev=0)
rbox("basinL", 0.045, 0.055, -0.22, 0.18, 0.58, 0.88, STEEL, m=SM, bev=0)
rbox("basinR", 0.645, 0.655, -0.22, 0.18, 0.58, 0.88, STEEL, m=SM, bev=0)
WATER = rbox("water", 0.056, 0.644, -0.214, 0.174, 0.745, 0.75, "7FC4E8", m=mat("3F7FB0", 0.25, alpha=0.3), bev=0)
WATER_HOME = WATER.location.copy()
cyl("fbase", 0.035, 0.9, 0.93, 0.35, 0.25, STEEL, m=SM)
cyl("fneck", 0.02, 0.9, 1.3, 0.35, 0.25, STEEL, m=SM)
rbox("farm", 0.33, 0.37, 0.02, 0.27, 1.27, 1.31, STEEL, m=SM, bev=0.008)
cyl("fnoz", 0.022, 1.22, 1.28, 0.35, 0.03, STEEL, m=SM)
DRIP = ball("drip", 0.008, "9FD6F2", AWAY)
# the board on the left end
rbox("board", -0.98, -0.52, -0.21, 0.15, 0.9, 0.93, WOOD, bev=0.008)
# the window over the sink: dusk outside
WIN = Vector((0.35, 0.318, 1.42))
win_m = bpy.data.materials.new("dusk")
win_m.use_nodes = True
nt = win_m.node_tree
nt.nodes.clear()
tc, sep, ramp = nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeSeparateXYZ"), nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.25, (*hexc("C99BB5"), 1)
ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.85, (*hexc("3E5487"), 1)
em = nt.nodes.new("ShaderNodeEmission")
em.inputs[1].default_value = 0.9
nt.links.new(tc.outputs["Generated"], sep.inputs[0])
nt.links.new(sep.outputs["Z"], ramp.inputs[0])
nt.links.new(ramp.outputs[0], em.inputs[0])
nt.links.new(em.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs[0])
B.mesh_from("glass", B.box(0.03, 0.67, 0.314, 0.318, 1.1, 1.74), [win_m])
for k, (x0, x1, z0, z1) in enumerate(((0.0, 0.7, 1.07, 1.11), (0.0, 0.7, 1.73, 1.77), (0.0, 0.04, 1.07, 1.77),
                                       (0.66, 0.7, 1.07, 1.77), (0.335, 0.365, 1.1, 1.74), (0.03, 0.67, 1.405, 1.425))):
    rbox(f"wf{k}", x0, x1, 0.28, 0.318, z0, z1, CREAM, bev=0.004)
rbox("sill", -0.03, 0.73, 0.24, 0.32, 1.04, 1.075, CREAM, bev=0.006)
# pendants
def pendant(name, x, y):
    cyl(name + "cord", 0.005, 1.95, 3.2, x, y, "26323F")
    cyl(name + "shade", 0.15, 1.82, 1.95, x, y, SAGE, r2=0.03, seg=48)
    ball(name + "bulb", 0.04, "FFF3D6", (x, y, 1.82), m=emit_mat("FFF3D6", 3.0))
    ld = bpy.data.lights.new(name, "SPOT")
    ld.energy, ld.spot_size, ld.spot_blend, ld.color, ld.shadow_soft_size = 1100.0, math.radians(95), 0.5, hexc("FFE2BE"), 0.06
    ob = B.link(bpy.data.objects.new(name + "L", ld))
    ob.location = (x, y, 1.8)
    ob.rotation_euler = (0, 0, 0)                            # straight down
    return ob
LAMP_A = pendant("pa", -0.75, -0.08)
LAMP_B = pendant("pb", 0.35, -0.12)
WINL = B.area("winL", Vector((0.35, 0.22, 1.42)), Vector((0.35, -1.0, 1.0)), 0.6, 70.0, color=hexc("8FA0E0"), size_y=0.6)
WINL.data.use_shadow = False
# the fridge, door open, on the right
FX = 1.71
FRM = mat(MINT, 0.4)
INM = mat("F7F8F6", 0.5)
rbox("fback", FX - 0.38, FX + 0.38, 0.22, 0.3, 0, 1.8, MINT, m=FRM, bev=0.01)
rbox("fsideL", FX - 0.38, FX - 0.34, -0.36, 0.3, 0, 1.8, MINT, m=FRM, bev=0.01)
rbox("fsideR", FX + 0.34, FX + 0.38, -0.36, 0.3, 0, 1.8, MINT, m=FRM, bev=0.01)
rbox("ftop", FX - 0.38, FX + 0.38, -0.36, 0.3, 1.74, 1.8, MINT, m=FRM, bev=0.01)
rbox("fbot", FX - 0.38, FX + 0.38, -0.36, 0.3, 0, 0.12, MINT, m=FRM, bev=0.01)
rbox("fin", FX - 0.34, FX + 0.34, 0.2, 0.22, 0.12, 1.74, "F7F8F6", m=INM, bev=0)
for z in (0.52, 0.95):
    rbox(f"fshelf{z}", FX - 0.34, FX + 0.34, -0.32, 0.2, z - 0.015, z, "EAF2F4", bev=0)
rbox("fdiv", FX - 0.34, FX + 0.34, -0.34, 0.2, 1.34, 1.38, MINT, m=FRM, bev=0.004)
for k, (x, c) in enumerate(((FX - 0.22, "F6C945"), (FX - 0.12, "EE6F52"), (FX + 0.2, "6FAF6F"))):
    cyl(f"jar{k}", 0.04, 0.52, 0.64, x, 0.05, c if k != 1 else "F2A7B5")
cyl("milk", 0.05, 0.52, 0.74, FX + 0.1, 0.0, "FFFFFF")
rbox("light", FX - 0.1, FX + 0.1, 0.0, 0.18, 1.33, 1.34, "FFFFFF", m=emit_mat("F4FBFF", 2.0), bev=0)
DOOR = empty("door", (FX + 0.38, -0.36, 0))
rbox("door1", -0.76, 0, -0.06, 0, 0.0, 1.32, MINT, m=FRM, bev=0.02, parent=DOOR)
rbox("door2", -0.76, 0, -0.06, 0, 1.36, 1.8, MINT, m=FRM, bev=0.02, parent=DOOR)
rbox("dinner", -0.72, -0.04, 0.0, 0.02, 0.06, 1.28, "F7F8F6", m=INM, bev=0.004, parent=DOOR)
for z in (0.4, 0.8):
    rbox(f"dbin{z}", -0.7, -0.06, 0.0, 0.09, z, z + 0.08, "EAF2F4", bev=0.004, parent=DOOR)
DOOR.rotation_euler = (0, 0, math.radians(118))
ld = bpy.data.lights.new("fridgeL", "POINT")
ld.energy, ld.color, ld.shadow_soft_size = 160.0, hexc("E8F6FF"), 0.15
ld.use_shadow = False
FRIDGE_L = B.link(bpy.data.objects.new("fridgeL", ld))
FRIDGE_L.location = (FX, -0.12, 1.25)
# the timer on the counter
TM = empty("timer", (0.95, -0.12, 0.9))
cyl("tbody", 0.07, 0.0, 0.1, 0, 0, "F6C945", parent=TM, bev=0.01)
cyl("ttop", 0.05, 0.1, 0.13, 0, 0, "F4ECDD", parent=TM)
rbox("tmark", -0.004, 0.004, -0.072, -0.066, 0.06, 0.095, "232C38", bev=0, parent=TM)

SIGN_DAY = Sign("sday", (-0.75, 0.30, 1.47))
SIGN_DAY.set("THANKSGIVING", "TOMORROW", "THURSDAY, NOV 26")
SIGN_COUNT = Sign("scount", (0.98, 0.30, 1.47), w=0.44, h=0.3, big=0.1)
SIGN_FRIDGE = Sign("sfridge", (FX, 0.30, 2.06), w=0.52, h=0.3)

# ------------------------------------------------------------------ the cast

def turkey():
    root = empty("turkey")
    body = mat("D99A72", 0.45)
    ball("tbody", 0.16, "", (0, 0, 0.12), squash=(1.0, 1.32, 0.78), parent=root, m=body)
    for s in (-1, 1):
        ball(f"tdrum{s}", 0.05, "", (s * 0.1, -0.2, 0.17), squash=(1, 1, 2.0), parent=root, m=body, rot=(-1.0, 0, s * 0.25))
        ball(f"tknob{s}", 0.022, "F7F3EC", (s * 0.11, -0.27, 0.23), parent=root)
        ball(f"twing{s}", 0.06, "", (s * 0.15, 0.03, 0.12), squash=(0.5, 1.4, 0.7), parent=root, m=body)
    for k in range(28):                                       # frost crystals on the top
        a, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 0.13)
        ball(f"tice{k}", rng.uniform(0.006, 0.012), "F4FAFF", (r * math.cos(a), r * math.sin(a) * 1.3, 0.24 - 0.5 * r * r),
             parent=root, m=mat("F4FAFF", 0.1))
    bag = mat("EEF6FA", 0.05, alpha=0.12)
    ball("tbag", 0.185, "", (0, 0.0, 0.13), squash=(1.05, 1.42, 0.85), parent=root, m=bag)
    ball("tknot", 0.03, "", (0, 0.27, 0.15), parent=root, m=mat("EEF6FA", 0.05, alpha=0.5))
    for s in (-1, 1):
        ball(f"tear{s}", 0.022, "", (s * 0.03, 0.3, 0.19), squash=(1, 1, 1.6), parent=root, m=mat("EEF6FA", 0.05, alpha=0.5),
             rot=(0.5, s * 0.5, 0))
    return root

def friend():
    root = empty("friend")
    p = {"root": root}
    cyl("fbody", 0.16, 0.0, 1.22, 0, 0, SAGE, bev=0.05, parent=root)
    rbox("fapron", -0.12, 0.12, -0.17, -0.15, 0.35, 1.05, CREAM, bev=0.01, parent=root)
    head = empty("fhead", (0, 0, 1.4), root)
    p["head"] = head
    ball("fface", 0.15, "F0C8A0", (0, 0, 0), parent=head)
    ball("fhair", 0.16, "4A3426", (0, 0.03, 0.09), squash=(1.03, 1.03, 0.5), parent=head)
    for s in (-1, 1):
        ball(f"feye{s}", 0.017, "232C38", (s * 0.05, -0.14, 0.0), squash=(1, 0.5, 1.2), parent=head)
        rbox(f"fbrow{s}", s * 0.05 - 0.025, s * 0.05 + 0.025, -0.152, -0.142, 0.035, 0.045, "4A3426", bev=0, parent=head)
    rbox("fmouth", -0.03, 0.03, -0.146, -0.14, -0.065, -0.057, "8A4B3A", bev=0, parent=head)
    for s, k in ((-1, "L"), (1, "R")):
        arm = empty("farm" + k, (s * 0.19, 0, 1.12), root)
        cyl("farmc" + k, 0.045, -0.5, 0.0, 0, 0, SAGE, parent=arm)
        ball("fhand" + k, 0.055, "F0C8A0", (0, 0, -0.53), parent=arm)
        p["arm" + k] = arm
    hand = empty("fpit", (0, 0, -0.55), p["armR"])
    pit = empty("pitcher", (0, -0.02, 0), hand)
    cyl("pbody", 0.07, -0.18, 0.0, 0, 0, "9FC3DD", r2=0.06, parent=pit, m=mat("9FC3DD", 0.2, alpha=0.7))
    rbox("phandle", 0.06, 0.09, -0.01, 0.01, -0.15, -0.03, "9FC3DD", bev=0.005, parent=pit)
    p["pitcher"] = pit
    return p

TK = turkey()
FR = friend()
BIRD_BOARD = Vector((-0.75, -0.03, 0.93))
BIRD_FRIDGE = Vector((FX, -0.08, 0.95))
BIRD_SINK = Vector((0.35, -0.02, 0.62))
F_HOOK = Vector((-1.27, 0.14, 0.0))          # left of the board, facing +x, knocking with the camera-side arm
F_SINK = Vector((-0.12, -0.5, 0.0))          # left of the sink, three-quarters to camera
for o in TK.children_recursive:
    pass

# ------------------------------------------------------------------ world, camera, shots

w = bpy.data.worlds.new("w")
scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (*hexc("1C2533"), 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
cam = B.camera(lens=35, fstop=8.0)
rig = D.Rig(cam, {"lampA": LAMP_A, "lampB": LAMP_B, "win": WINL, "fridge": FRIDGE_L})

BOARD_EYE = Vector((-0.8, -0.04, 1.1))
COUNT_EYE = SIGN_COUNT.root.location + Vector((0, -0.02, 0))
SH = [
    D.Shot("hook", 0.0, BOARD_EYE, lens=35, dist=1.9, yaw=10, pitch=-12, screen=(0.5, 0.56),
           light={"lampA": 1, "lampB": 0.25, "win": 0.6, "fridge": 0}, note="frame 0: the friend's fist on the frozen bird; the sound-off title over it is meant to pull first"),
    D.Shot("rock", E["rock"] - 0.06, BIRD_BOARD + Vector((0, 0, 0.13)), lens=45, dist=1.1, yaw=28, pitch=-64,
           screen=(0.5, 0.52), move=("push", 0.08), light={"lampA": 1, "lampB": 0.2, "win": 0.6, "fridge": 0},
           note="0.7 s punch on rock; the hook title is still up and pulls first"),
    D.Shot("fridge", E["B"] - 0.06, Vector((FX, -0.1, 1.15)), lens=28, dist=2.4, yaw=-6, pitch=-5, screen=(0.5, 0.52),
           light={"lampA": 0.1, "lampB": 0.15, "win": 0.4, "fridge": 1}, note="lit by the fridge only"),
    D.Shot("days", E["C"] - 0.06, SIGN_FRIDGE.root.location + Vector((0, -0.02, -0.12)), lens=60, dist=1.7, yaw=-10,
           pitch=-6, screen=(0.5, 0.46), light={"lampA": 0.05, "lampB": 0.05, "win": 0.2, "fridge": 0.35},
           note="a self-lit sign in a dark kitchen, the bird on the lit shelf under it shares the eye"),
    D.Shot("sink", E["D"] - 0.06, Vector((0.35, -0.02, 0.86)), lens=32, dist=1.5, yaw=6, pitch=-40, screen=(0.5, 0.56),
           light={"lampA": 0.2, "lampB": 0.4, "win": 0.8, "fridge": 0}),
    D.Shot("bag", E["E"] - 0.06, BIRD_SINK + Vector((0, 0, 0.14)), lens=40, dist=1.2, yaw=-12, pitch=-38,
           screen=(0.5, 0.52), move=("push", 0.06), light={"lampA": 0.15, "lampB": 0.4, "win": 0.8, "fridge": 0}),
    D.Shot("hours", E["F"] - 0.06, Vector((0.68, 0.05, 1.18)), lens=32, dist=1.9, yaw=-14, pitch=-8, screen=(0.5, 0.5),
           light={"lampA": 0.1, "lampB": 0.35, "win": 0.5, "fridge": 0},
           note="the sign is self-lit; the pendant keeps the bird in the sink readable below it"),
    D.Shot("change", E["G"] - 0.06, Vector((0.12, -0.3, 1.1)), lens=30, dist=2.1, yaw=16, pitch=-8, screen=(0.5, 0.53),
           light={"lampA": 0.2, "lampB": 1, "win": 0.8, "fridge": 0}),
    D.Shot("count", E["H"] - 0.06, COUNT_EYE, lens=45, dist=1.45, yaw=0, pitch=-2, screen=(0.5, 0.46), hit=E["twenty"],
           move=("punch", 1.35), kick=0.012, light={"lampA": 0.05, "lampB": 0.7, "win": 0.4, "fridge": 0},
           note="big moment: the 20 flips orange on the word"),
    D.Shot("one", E["I"] - 0.06, Vector((0.3, -0.25, 1.12)), lens=26, dist=3.4, yaw=0, pitch=-6, screen=(0.5, 0.55),
           light={"lampA": 0.1, "lampB": 0.75, "win": 0.6, "fridge": 0}, note="wide and locked: deadpan"),
    D.Shot("loop", E["J"] - 0.06, BOARD_EYE, lens=35, dist=1.9, yaw=10, pitch=-12, screen=(0.5, 0.56),
           light={"lampA": 1, "lampB": 0.25, "win": 0.6, "fridge": 0}, note="the hook again, for the loop"),
]
SHOTS = D.ShotList(SH, DUR)
SHOTS.check()
SHOTS.dump(os.path.join(os.path.dirname(OUT.rstrip("/\\")), "shots.json"), big=E["twenty"])

# ------------------------------------------------------------------ the timeline

SPL = [ball(f"spl{i}", rng.uniform(0.01, 0.018), "9FD6F2", AWAY, m=mat("9FD6F2", 0.1, alpha=0.8)) for i in range(16)]
SPL_V = [(rng.uniform(-0.6, 0.6), rng.uniform(-0.5, 0.4), rng.uniform(1.4, 2.4)) for _ in SPL]

def knock_angle(t, t0):
    """Arm raised forward (degrees): rests at 104, drops to 90 on each knock."""
    a = 104.0
    for k in E["knocks"]:
        u = t - (t0 + k)
        if -0.08 <= u < 0:
            a = min(a, 104 - 14 * (u + 0.08) / 0.08)
        elif 0 <= u < 0.18:
            a = min(a, 90 + 14 * D.smooth(u / 0.18))
    return a

def apply_state(t):
    q = D.on_twos(t, FPS)                                     # the cast moves on twos, camera and light stay smooth
    name = SHOTS.at(t).name
    # the bird
    if t < E["B"] - 0.06 or t >= E["J"] - 0.06:
        TK.location = BIRD_BOARD
    elif t < E["D"] - 0.06:
        TK.location = BIRD_FRIDGE
    else:
        c = E["cold"]
        drop = D.ease_in((q - (c - 0.3)) / 0.3) if q < c else 1.0
        bob = 0.012 * math.exp(-(q - c) * 3) * math.sin((q - c) * 12) if q >= c else 0.0
        TK.location = BIRD_SINK + Vector((0, 0, 0.42 * (1 - drop) + bob))
    TK.rotation_euler = (0, 0, math.radians(90) if (E["D"] - 0.06 <= t < E["J"] - 0.06) else 0)
    # splash on 'cold water'
    for ob, (vx, vy, vz) in zip(SPL, SPL_V):
        u = t - E["cold"]
        if 0 <= u < 0.7 and E["D"] - 0.06 <= t < E["E"]:
            ob.location = BIRD_SINK + Vector((vx * 0.25 * u * 2, vy * 0.2 * u * 2, 0.2 + vz * u - 4.9 * u * u))
        else:
            ob.location = AWAY
    # the drip from the faucet, every 0.9 s; it stops for the breath before the big moment
    dd = (q % 0.9) / 0.9
    if D.hold(t, E["twenty"], breath=0.3) < 1 or t >= E["twenty"]:
        DRIP.location = AWAY
    else:
        DRIP.location = Vector((0.35, 0.03, 1.21 - 0.42 * dd * dd)) if dd < 0.9 else AWAY
    # the friend
    FR["pitcher"].location = AWAY if (t < E["G"] - 0.06 or t >= E["J"] - 0.06) else Vector((0, -0.02, 0))
    FR["root"].rotation_euler = (0, 0, 0)
    FR["head"].rotation_euler = (0, 0, 0)
    FR["armL"].rotation_euler = (0, 0, 0)
    FR["armR"].rotation_euler = (0, 0, 0)
    if name in ("hook", "rock", "loop"):
        FR["root"].location = F_HOOK
        FR["root"].rotation_euler = (0, 0, math.radians(90))
        t0 = 0.0 if name != "loop" else E["J"] - 0.06
        FR["armL"].rotation_euler = (-math.radians(knock_angle(q, t0)), 0, 0)
        FR["head"].rotation_euler = (0.25, 0, 0)
    elif name in ("fridge", "days", "sink", "bag", "hours", "count"):
        FR["root"].location = AWAY
    else:
        FR["root"].location = F_SINK
        FR["root"].rotation_euler = (0, 0, math.radians(40))
        FR["head"].rotation_euler = (0.2, 0, -0.2)
        if name == "change":
            pour = D.ars(q, E["thirty"], wind=0.3, back=0.1, release=0.15, settle=0.5, over=0.1, snap="out")
            FR["armR"].rotation_euler = (-math.radians(55 + 20 * pour), 0, 0)
            FR["pitcher"].rotation_euler = (math.radians(-60 * max(0.0, pour)), 0, 0)
        elif name == "one":
            FR["armR"].rotation_euler = (-math.radians(12), 0, 0)
            FR["root"].rotation_euler = (-0.06, 0, math.radians(40))
            FR["head"].rotation_euler = (0.45, 0, -0.1)
        else:
            FR["armR"].rotation_euler = (-math.radians(10), 0, 0)
    # the timer rings on 'thirty minutes'
    u = t - E["thirty"]
    TM.rotation_euler = (0, 0, 0.12 * math.sin(u * 60) * math.exp(-u * 4) if u >= 0 else 0.0)
    # the fridge sign
    if t < E["four"] - 0.03:
        SIGN_FRIDGE.set("FRIDGE THAW", "1 DAY", "PER 4 TO 5 LB")
    else:
        SIGN_FRIDGE.set("A 20 LB BIRD", "4 TO 5 DAYS", "THANKSGIVING: TOMORROW")
    # the count sign
    if t < E["F"] - 0.06:
        SIGN_COUNT.set("COLD WATER", "30 MIN", "PER POUND")
    elif t < E["G"] - 0.06:
        u = D.smooth((t - E["ten"]) / 0.6)
        SIGN_COUNT.set("A 20 LB BIRD", "? HOURS" if t < E["ten"] else f"{round(10 * u)} HOURS", "IN COLD WATER")
    elif t < E["H"] - 0.06:
        SIGN_COUNT.set("CHANGE THE WATER", "EVERY 30 MIN", "IN A SEALED BAG")
    elif t < E["I"] - 0.06:
        if t < E["twenty"]:
            SIGN_COUNT.set("WATER CHANGES", "?", "IN 10 HOURS")
        else:
            SIGN_COUNT.set("WATER CHANGES", "20", "IN 10 HOURS", color=ORANGE)
    else:
        SIGN_COUNT.set("WATER CHANGE", "1 OF 20", "19 TO GO")
    SHOTS.apply(rig, t)
    cam.data.dof.use_dof = False
    LAMP_B.data.energy *= 1.0 + 1.6 * D.flash(t, E["twenty"], decay=0.5) if name == "count" else 1.0

B.render_settings(FPS, samples=int(os.environ.get("TR_SAMPLES", "24")), motion_blur=0.0)
try:
    scene.eevee.use_fast_gi = False
    scene.eevee.use_raytracing = False
except Exception:
    pass

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1) / FPS)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
