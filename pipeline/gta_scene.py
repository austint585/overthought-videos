"""Blender scene for 'Boyfriends vs GTA 6': a voxel living room at night. A wall calendar with November 19 circled,
a TV with a download bar, a console, a shelf of four game cases that vanish, a gaming chair with the boyfriend and a
couch with the girlfriend and her phone. On "gone" the boyfriend despawns into cubes. Timed to render_gta.py.

blender -b --factory-startup -P gta_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Always writes out_dir/anchors.json: screen positions of label points for every frame.
"""
import json, math, os, random, sys
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bkit as B

argv = sys.argv[sys.argv.index("--") + 1:]
TIMING, OUT, MODE = argv[0], argv[1], argv[2]
T = json.load(open(TIMING))
FPS, DUR, E = T["fps"], T["duration"], T["events"]
NF = int(round(DUR * FPS))
os.makedirs(OUT, exist_ok=True)
B.clear_scene()
scene = B.scene
rng = random.Random(19)
AWAY = Vector((0, 0, -1.0e5))

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

def ramp(t, t0, t1):
    return smooth01((t - t0) / (t1 - t0))

# ------------------------------------------------------------------ materials

def pixel_mat(name, pal, rough=0.85, emit=0.0):
    """16x16 pixel noise on every face: the position (nudged inside the block) snapped to 1/16 and hashed."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = rough
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    nudge = nt.nodes.new("ShaderNodeVectorMath"); nudge.operation = "MULTIPLY_ADD"
    nudge.inputs[1].default_value = (-0.01, -0.01, -0.01)
    nt.links.new(geo.outputs["Normal"], nudge.inputs[0])
    nt.links.new(geo.outputs["Position"], nudge.inputs[2])
    snap = nt.nodes.new("ShaderNodeVectorMath"); snap.operation = "SNAP"
    snap.inputs[1].default_value = (1 / 16, 1 / 16, 1 / 16)
    nt.links.new(nudge.outputs[0], snap.inputs[0])
    wn = nt.nodes.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = "3D"
    nt.links.new(snap.outputs[0], wn.inputs["Vector"])
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.color_ramp.interpolation = "CONSTANT"
    els = r.color_ramp.elements
    els[0].color = (*pal[0], 1)
    els[1].position = 1.0 / len(pal)
    els[1].color = (*pal[1 % len(pal)], 1)
    for k in range(2, len(pal)):
        e = els.new(k / len(pal)); e.color = (*pal[k], 1)
    nt.links.new(wn.outputs["Value"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], p.inputs["Base Color"])
    if emit:
        nt.links.new(r.outputs["Color"], p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = emit
    return m

def solid(name, color, rough=0.6, emit=0.0, metallic=0.0):
    m = B.material(name, color, metallic, rough)
    p = B.bsdf(m)
    p.inputs["Emission Color"].default_value = (*color, 1)
    p.inputs["Emission Strength"].default_value = emit
    return m

_mat_cache = {}
def colmat(color, rough=0.55, emit=0.0, metallic=0.0):
    key = (color, rough, emit, metallic)
    if key not in _mat_cache:
        _mat_cache[key] = solid(f"c{len(_mat_cache)}", color, rough, emit, metallic)
    return _mat_cache[key]

def shade(c, f):
    return tuple(min(1.0, x * f) for x in c)

MATS = {
    "roof": pixel_mat("roof", [(0.10, 0.10, 0.11), (0.12, 0.12, 0.13), (0.085, 0.085, 0.095), (0.14, 0.135, 0.14)], rough=0.9),
    "brick": pixel_mat("brick", [(0.36, 0.15, 0.10), (0.42, 0.18, 0.12), (0.30, 0.12, 0.08), (0.25, 0.22, 0.20)]),
    "cap": pixel_mat("cap", [(0.42, 0.42, 0.44), (0.48, 0.48, 0.50), (0.36, 0.36, 0.38)]),
}

GRID = {}
def fill(i0, i1, j0, j1, k0, k1, mat):
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            for k in range(k0, k1 + 1):
                if mat is None:
                    GRID.pop((i, j, k), None)
                else:
                    GRID[(i, j, k)] = mat

DIRS = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]),
        ((-1, 0, 0), [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]),
        ((0, 1, 0), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)]),
        ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
        ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]),
        ((0, 0, -1), [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)])]

def voxel_mesh(name, grid):
    keys = sorted(set(grid.values()))
    idx = {k: n for n, k in enumerate(keys)}
    verts, faces, mats = [], [], []
    for (i, j, k), mat in grid.items():
        for (di, dj, dk), quad in DIRS:
            if (i + di, j + dj, k + dk) in grid:
                continue
            base = len(verts)
            verts.extend((i + a, j + b, k + c) for a, b, c in quad)
            faces.append((base, base + 1, base + 2, base + 3))
            mats.append(idx[mat])
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    for k in keys:
        me.materials.append(MATS[k])
    me.polygons.foreach_set("material_index", mats)
    return B.link(bpy.data.objects.new(name, me))

def boxes(name, parts, origin, parent=None):
    """parts: list of ((x0, x1, y0, y1, z0, z1), material)."""
    mats, builders = [], []
    for bb, m in parts:
        if m not in mats:
            mats.append(m)
        builders.append(B.with_material(B.box(*bb), mats.index(m)))
    ob = B.mesh_from(name, B.many(*builders), mats)
    ob.parent = parent
    ob.location = origin
    return ob

# ------------------------------------------------------------------ set
METAL_D = colmat((0.30, 0.32, 0.35), 0.4, metallic=0.5)
# ------------------------------------------------------------------ the room: wood floor, plaster walls, a window

MATS["wood"] = pixel_mat("wood", [(0.32, 0.20, 0.11), (0.36, 0.23, 0.13), (0.28, 0.17, 0.09), (0.40, 0.26, 0.15)])
MATS["wall"] = pixel_mat("wall", [(0.36, 0.38, 0.46), (0.38, 0.40, 0.48), (0.34, 0.36, 0.44)], rough=0.95)
MATS["base"] = pixel_mat("base", [(0.85, 0.84, 0.80), (0.80, 0.79, 0.75)])
fill(-9, 8, -4, 9, -1, -1, "wood")
fill(-9, 8, 9, 9, 0, 7, "wall")                    # back wall, front face at y = 9
fill(-10, -10, -4, 9, 0, 7, "wall")                # left wall, face at x = -9
fill(-10, -10, 2, 4, 2, 4, None)                   # window hole
fill(-9, 8, 9, 9, 0, 0, "base")
voxel_mesh("room", GRID)
GLASS = colmat((0.25, 0.35, 0.6), 0.2, emit=1.2)
SILL = colmat((0.85, 0.84, 0.80), 0.6)
boxes("window", [((-0.2, 0.0, 2.0, 5.0, 2.0, 5.0), GLASS), ((-0.3, 0.1, 3.45, 3.55, 2.0, 5.0), SILL),
                 ((-0.3, 0.1, 2.0, 5.0, 3.45, 3.55), SILL), ((-0.1, 0.5, 1.9, 5.1, 1.85, 2.0), SILL)], (-9.6, 0, 0))

RUG = colmat((0.45, 0.12, 0.14), 0.95)
boxes("rug", [((-3.0, 3.0, -2.0, 2.0, 0.0, 0.03), RUG), ((-2.6, 2.6, -1.6, 1.6, 0.03, 0.04), colmat((0.55, 0.18, 0.18), 0.95))],
      (0.5, 3.5, 0))

# calendar on the back wall, November 2026 (the 1st is a Sunday), the 19th circled
CAL_C = Vector((-4.5, 9.0, 3.8))
PAPER = colmat((0.93, 0.92, 0.88), 0.8)
HEAD_R = colmat((0.80, 0.12, 0.10), 0.6)
CELL = colmat((0.80, 0.79, 0.76), 0.8)
MARK = colmat((0.25, 0.25, 0.28), 0.7)
RING = colmat((0.95, 0.08, 0.06), 0.5, emit=1.5)
cal = [((-1.3, 1.3, -0.06, 0.0, -1.5, 1.5), PAPER), ((-1.3, 1.3, -0.08, -0.06, 0.95, 1.5), HEAD_R),
       ((-0.05, 0.05, -0.1, 0.0, 1.5, 1.75), MARK)]
CW, CH = 0.32, 0.4
for r in range(5):
    for col in range(7):
        x0 = -1.18 + col * (CW + 0.035)
        z1 = 0.82 - r * (CH + 0.035)
        cal.append(((x0, x0 + CW, -0.07, -0.06, z1 - CH, z1), CELL))
        cal.append(((x0 + 0.04, x0 + 0.14, -0.075, -0.07, z1 - 0.14, z1 - 0.05), MARK))
x0 = -1.18 + 4 * (CW + 0.035); z1 = 0.82 - 2 * (CH + 0.035)
C19 = Vector((x0 + CW / 2, -0.08, z1 - CH / 2))
for bb in ((x0 - 0.07, x0 + CW + 0.07, z1 - 0.03, z1 + 0.04), (x0 - 0.07, x0 + CW + 0.07, z1 - CH - 0.04, z1 - CH + 0.03),
           (x0 - 0.07, x0, z1 - CH - 0.04, z1 + 0.04), (x0 + CW, x0 + CW + 0.07, z1 - CH - 0.04, z1 + 0.04)):
    cal.append(((bb[0], bb[1], -0.1, -0.075, bb[2], bb[3]), RING))
boxes("calendar", cal, CAL_C)
CAL19 = CAL_C + C19

# TV, stand, console, shelf with four game cases
TV_C = Vector((2.0, 8.75, 3.1))
BLACK = colmat((0.03, 0.03, 0.035), 0.4)
SCREEN = solid("screen", (0.25, 0.45, 1.0), 0.3, 0.4)
boxes("tv", [((-2.3, 2.3, -0.12, 0.12, -1.35, 1.35), BLACK)], TV_C)
boxes("screen", [((-2.18, 2.18, -0.14, -0.12, -1.23, 1.23), SCREEN)], TV_C)
BAR_BG = colmat((0.1, 0.12, 0.2), 0.4, emit=1.0)
BAR = colmat((0.3, 1.0, 0.45), 0.3, emit=5.0)
boxes("barbg", [((-1.6, 1.6, -0.17, -0.14, -0.15, 0.15), BAR_BG)], TV_C + Vector((0, 0, -0.5)))
bar = boxes("bar", [((0.0, 3.1, -0.19, -0.17, -0.1, 0.1), BAR)], TV_C + Vector((-1.55, 0, -0.5)))
STAND = colmat((0.20, 0.13, 0.08), 0.7)
boxes("stand", [((-2.6, 2.6, -0.6, 0.6, 0.0, 1.1), STAND), ((-2.5, 2.5, -0.62, -0.6, 0.15, 0.95), colmat((0.15, 0.10, 0.06), 0.7))],
      (2.0, 8.3, 0))
CONS = colmat((0.92, 0.92, 0.95), 0.4)
CLED = solid("cled", (0.3, 0.6, 1.0), 0.3, 0.0)
boxes("console", [((-0.25, 0.25, -0.45, 0.45, 0.0, 1.0), CONS), ((-0.27, 0.27, -0.47, -0.45, 0.05, 0.95), CLED)],
      (0.6, 8.3, 1.1))
boxes("shelf", [((-1.2, 1.2, -0.35, 0.35, 0.0, 0.08), STAND)], (5.6, 8.6, 2.3))
CASES = []
for k, col in enumerate(((0.1, 0.35, 0.9), (0.9, 0.2, 0.15), (0.15, 0.7, 0.3), (0.95, 0.75, 0.1))):
    CASES.append(boxes(f"case{k}", [((-0.07, 0.07, -0.3, 0.3, 0.0, 0.85), colmat(col, 0.5))], (5.0 + k * 0.38, 8.6, 2.38)))
CASE_HOME = [c.location.copy() for c in CASES]
boxes("controller", [((-0.25, 0.25, -0.12, 0.12, 0.0, 0.1), BLACK)], (1.0, 7.9, 1.1))

# gaming chair (him) and couch (her)
CHAIR = Vector((2.0, 4.6, 0))
RED_C = colmat((0.75, 0.08, 0.08), 0.5)
boxes("gchair", [((-0.6, 0.6, -0.55, 0.55, 0.55, 0.75), BLACK), ((-0.6, 0.6, -0.75, -0.55, 0.6, 2.3), BLACK),
                 ((-0.35, 0.35, -0.78, -0.74, 0.9, 2.1), RED_C), ((-0.08, 0.08, -0.08, 0.08, 0.1, 0.55), METAL_D),
                 ((-0.6, 0.6, -0.06, 0.06, 0.0, 0.1), METAL_D), ((-0.06, 0.06, -0.6, 0.6, 0.0, 0.1), METAL_D)], CHAIR)
COUCH = Vector((-3.6, 1.8, 0))
SOFA = colmat((0.22, 0.30, 0.42), 0.9)
SOFA_D = colmat((0.17, 0.24, 0.34), 0.9)
boxes("couch", [((-2.0, 2.0, -0.8, 0.8, 0.0, 0.6), SOFA_D), ((-1.9, 1.9, -0.7, 0.7, 0.6, 0.85), SOFA),
                ((-2.0, 2.0, -0.8, -0.4, 0.6, 1.9), SOFA_D), ((-2.3, -1.9, -0.8, 0.8, 0.0, 1.2), SOFA_D),
                ((1.9, 2.3, -0.8, 0.8, 0.0, 1.2), SOFA_D)], COUCH)
COUCH_ROT = math.radians(-35)
bpy.data.objects["couch"].rotation_euler = (0, 0, COUCH_ROT)
LAMP_C = colmat((1.0, 0.75, 0.4), 0.4, emit=6.0)
boxes("lamp", [((-0.08, 0.08, -0.08, 0.08, 0.0, 2.4), METAL_D), ((-0.4, 0.4, -0.4, 0.4, 2.4, 3.0), LAMP_C)], (-7.6, 7.6, 0))

# despawn cubes
BITS = []
BIT_M = colmat((0.6, 0.9, 1.0), 0.4, emit=6.0)
for n in range(18):
    BITS.append((boxes(f"bit{n}", [((-0.09, 0.09, -0.09, 0.09, -0.09, 0.09), BIT_M)], AWAY),
                 Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0.2, 1.6)))))

# ------------------------------------------------------------------ figures

def figure(name, hair, shirt, pants, skin, phone=False):
    m = colmat
    root = B.link(bpy.data.objects.new(name, None))
    S, Hh, Sh, P, D = m(skin), m(hair, 0.7), m(shirt), m(pants, 0.7), m((0.03, 0.02, 0.02), 0.4)
    Shoe = m((0.92, 0.92, 0.94), 0.5)
    f = {"root": root}
    for side, x in (("L", -0.125), ("R", 0.125)):
        f["leg" + side] = boxes(f"{name}_leg{side}", [((-0.125, 0.125, -0.125, 0.125, -0.75, 0.0), P),
                                                       ((-0.13, 0.13, -0.16, 0.13, -0.75, -0.62), Shoe)], (x, 0, 0.75), root)
    f["body"] = boxes(f"{name}_body", [((-0.25, 0.25, -0.125, 0.125, 0, 0.75), Sh),
                                        ((-0.26, 0.26, -0.135, 0.135, 0.55, 0.75), m(shade(shirt, 0.8)))], (0, 0, 0.75), root)
    for side, x in (("L", -0.375), ("R", 0.375)):
        parts = [((-0.125, 0.125, -0.125, 0.125, -0.25, 0.0), Sh), ((-0.12, 0.12, -0.12, 0.12, -0.75, -0.25), S)]
        if side == "R" and phone:
            parts += [((-0.08, 0.08, -0.03, 0.03, -0.92, -0.72), m((0.55, 0.75, 1.0), 0.3, 3.0))]
        f["arm" + side] = boxes(f"{name}_arm{side}", parts, (x, 0, 1.5), root)
    head = [((-0.25, 0.25, -0.25, 0.25, 0, 0.5), S), ((-0.27, 0.27, -0.27, 0.27, 0.38, 0.55), Hh),
            ((-0.27, 0.27, 0.08, 0.28, 0.12, 0.5), Hh),
            ((-0.16, -0.06, -0.265, -0.25, 0.2, 0.28), D), ((0.06, 0.16, -0.265, -0.25, 0.2, 0.28), D),
            ((-0.07, 0.07, -0.262, -0.25, 0.07, 0.1), m(shade(skin, 0.6)))]
    f["head"] = boxes(f"{name}_head", head, (0, 0, 1.5), root)
    return f

def place(f, x, y, face=(0, -1), z=0.0):
    f["root"].location = (x, y, z)
    f["root"].rotation_euler = (0, 0, math.atan2(face[0], -face[1]))

def pose(f, walk=0.0, phase=0.0, arms=None, sit=False, head_turn=0.0, head_nod=0.0, head_tilt=0.0):
    s = math.sin(phase) * walk
    f["legL"].rotation_euler = (-math.pi / 2 if sit else s * 0.8, 0, 0)
    f["legR"].rotation_euler = (-math.pi / 2 if sit else -s * 0.8, 0, 0)
    aL, aR = arms if arms else (-s * 0.7, s * 0.7)
    f["armL"].rotation_euler = aL if isinstance(aL, tuple) else (aL, 0, 0)
    f["armR"].rotation_euler = aR if isinstance(aR, tuple) else (aR, 0, 0)
    f["head"].rotation_euler = (head_nod, head_tilt, head_turn)

BF = figure("bf", hair=(0.08, 0.06, 0.05), shirt=(0.15, 0.17, 0.20), pants=(0.25, 0.27, 0.30), skin=(0.72, 0.50, 0.36))
GF = figure("gf", hair=(0.35, 0.18, 0.08), shirt=(0.85, 0.55, 0.65), pants=(0.20, 0.22, 0.40), skin=(0.85, 0.63, 0.50),
            phone=True)
boxes("gf_hair_long", [((-0.27, 0.27, 0.05, 0.3, -0.35, 0.5), colmat((0.35, 0.18, 0.08), 0.7))], (0, 0, 0), GF["head"])
CO = math.cos(COUCH_ROT); SI = math.sin(COUCH_ROT)
GF_FACE = Vector((-SI, CO, 0))                       # couch front direction
GF_POS = COUCH + Vector((0.6 * CO, 0.6 * SI, 0)) + GF_FACE * 0.15
BF_POS = CHAIR + Vector((0, 0.05, 0))
BF_HEAD = BF_POS + Vector((0, 0, 1.85))
GF_HEAD = GF_POS + Vector((0, 0, 1.95))
TO_GF = (GF_POS - BF_POS).normalized()

world = bpy.data.worlds.new("bg")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.008, 0.010, 0.025, 1)
B.area("moon", Vector((-15, 3.5, 5.5)), Vector((-3, 3.5, 0.5)), 3.0, 900.0, (0.55, 0.65, 1.0))
B.area("fill", Vector((0, -10, 7)), Vector((0, 4, 1)), 10.0, 420.0, (0.45, 0.5, 0.8))
B.area("calkey", CAL_C + Vector((1.5, -3.5, 2.5)), CAL_C, 2.0, 260.0, (1.0, 0.85, 0.65))
B.area("people", Vector((-1.0, -2.0, 4.5)), Vector((-0.5, 3.0, 1.5)), 4.0, 350.0, (0.7, 0.75, 1.0))
lamp_ld = bpy.data.lights.new("lamp", "POINT"); lamp_ld.color = (1.0, 0.72, 0.42); lamp_ld.energy = 260
lamp_ld.shadow_soft_size = 0.4
B.link(bpy.data.objects.new("lamp", lamp_ld)).location = (-7.6, 7.6, 2.6)
tv_ld = bpy.data.lights.new("tvglow", "AREA"); tv_ld.shape = "RECTANGLE"; tv_ld.size = 4.4; tv_ld.size_y = 2.5
tv_ld.color = (0.45, 0.6, 1.0)
tvl = B.link(bpy.data.objects.new("tvglow", tv_ld))
tvl.location = TV_C + Vector((0, -0.4, 0))
tvl.rotation_euler = (math.radians(-90), 0, 0)      # area light faces local -Z; turned to face -Y
phone_ld = bpy.data.lights.new("phone", "POINT"); phone_ld.color = (0.6, 0.75, 1.0); phone_ld.shadow_soft_size = 0.1
phone = B.link(bpy.data.objects.new("phone", phone_ld))
cam = B.camera(lens=35, fstop=2.8)
B.render_settings(FPS, samples=32, motion_blur=0.3)

def tv_state(t):
    on = ramp(t, E["console"] - 0.1, E["console"] + 0.1)
    flash = math.exp(-(t - E["console"]) * 3) if t >= E["console"] else 0.0
    B.bsdf(SCREEN).inputs["Emission Strength"].default_value = 1.2 + 2.5 * on + 10.0 * flash
    tv_ld.energy = 250 + 500 * on + 2500 * flash
    B.bsdf(CLED).inputs["Emission Strength"].default_value = 4.0 * on
    u = ramp(t, E["gb"] - 0.2, E["C"] + 1.5)
    bar.scale = (max(0.02, u), 1, 1)
    bar.location = TV_C + Vector((-1.55, 0, -0.5)) if t < E["console"] else AWAY
    bpy.data.objects["barbg"].location = TV_C + Vector((0, 0, -0.5)) if t < E["console"] else AWAY
    for k, c in enumerate(CASES):
        tk = E["four"] - 0.25 + 0.16 * k
        if t < tk:
            c.location = CASE_HOME[k]
            c.scale = (1, 1, 1)
        elif t < tk + 0.2:
            c.location = CASE_HOME[k] + Vector((0, 0, 0.6 * (t - tk) / 0.2))
            c.scale = (1, 1, 1 - (t - tk) / 0.2)
        else:
            c.location = AWAY

def people_state(t):
    # him: gaming chair, back to the room, controller up; turns to her to say it; despawns on "gone"
    turn = ramp(t, E["F"] - 0.2, E["F"] + 0.3) * (1 - ramp(t, E["console"] - 0.25, E["console"]))
    fwd = Vector((0, 1, 0)).lerp(TO_GF, turn).normalized()
    place(BF, BF_POS.x, BF_POS.y, face=(fwd.x, fwd.y), z=0.05)
    mash = 0.07 * math.sin(t * 13)
    if turn > 0.5:
        pose(BF, sit=True, arms=(-0.3, (-2.2, 0, 0.35) if t > E["love"] - 0.1 else -0.3), head_nod=0.05)
    else:
        pose(BF, sit=True, arms=(-1.2 + mash, -1.2 - mash), head_nod=0.08 + 0.03 * math.sin(t * 3))
    g = ramp(t, E["gone"] - 0.05, E["gone"] + 0.35)
    s = max(0.001, 1 - g)
    BF["root"].scale = (s, s, s)
    if g >= 1:
        BF["root"].location = AWAY
    for o, d in BITS:
        u = t - (E["gone"] - 0.05)
        if 0 <= u < 1.1:
            o.location = BF_POS + Vector((0, 0, 1.2)) + d * (u * 2.2) + Vector((0, 0, -1.2 * u * u))
            k = max(0.001, 1 - u / 1.1)
            o.scale = (k, k, k)
        else:
            o.location = AWAY
    # her: on the couch, phone up, looks over at him from "protocol" on
    place(GF, GF_POS.x, GF_POS.y, face=(GF_FACE.x, GF_FACE.y), z=0.15)
    look = ramp(t, E["E"] - 0.2, E["E"] + 0.2) * (1 - ramp(t, E["H"] - 0.2, E["H"] + 0.2))
    phone_up = 1 - look
    pose(GF, sit=True, arms=(-0.4, -1.1 * phone_up - 0.3 + 0.04 * math.sin(t * 8)),
         head_nod=-0.35 * phone_up + 0.05 * look, head_turn=-0.5 * look, head_tilt=0.1 * look)
    hand = GF["armR"].matrix_world @ Vector((0, -0.25, -0.85))
    phone.location = hand
    phone_ld.energy = 8.0 * phone_up

def apply_state(t):
    tv_state(t)
    people_state(t)
    loc, target, fstop, lens = camera_at(t)
    B.aim(cam, loc, target)
    cam.data.lens = lens
    cam.data.dof.focus_distance = (target - loc).length
    cam.data.dof.aperture_fstop = fstop
    cam.data.clip_start = 0.05
    cam.data.clip_end = 400

# ------------------------------------------------------------------ camera: each shot returns (camera location, look target)

def shot_hook(t):                                  # straight on the calendar, slow push to the circled 19
    u = min(1.0, t / max(1.0, E["B"]))
    tg = CAL_C.lerp(CAL19, 0.35 * u) + Vector((0, 0, -0.1))
    return tg + Vector((0.2 - 0.3 * u, -6.0 + 1.6 * u, -0.1)), tg
def shot_boys(t):                                 # from beside the TV: his face in screen light
    u = t - E["boys"]
    tg = BF_HEAD + Vector((0, 0, -0.15))
    return tg + Vector((1.1 - 0.15 * u, 3.0 - 0.2 * u, 0.2)), tg
def shot_wide(t):                                  # high wide from the back corner: room, him, TV with the bar
    u = t - E["B"]
    tg = Vector((1.2, 5.6, 1.9))
    return tg + Vector((-6.0 + 0.4 * u, -10.5 + 0.3 * u, 4.8 - 0.15 * u)), tg
def shot_shelf(t):                                 # low on the shelf of four games and the console
    u = t - E["C"]
    tg = Vector((5.6, 8.6, 2.8))
    return tg + Vector((0.3 - 0.15 * u, -3.6 + 0.1 * u, 0.6)), tg
def shot_her(t):                                   # her face in phone light
    u = t - E["D"]
    tg = GF_HEAD + Vector((0, 0, -0.15))
    side = Vector((GF_FACE.y, -GF_FACE.x, 0))
    return tg + GF_FACE * (3.0 - 0.15 * u) + side * 0.9 + Vector((0, 0, 0.3)), tg
def shot_over(t):                                  # two-shot from the front: her on the couch looking at him
    u = t - E["E"]
    tg = GF_HEAD + Vector((0, 0, -0.6))
    side = Vector((GF_FACE.y, -GF_FACE.x, 0))
    return tg + GF_FACE * (4.6 - 0.15 * u) - side * 1.4 + Vector((0, 0, 1.0)), tg
def shot_him(t):                                   # on him, turned to her
    u = t - E["F"]
    d = TO_GF
    tg = BF_HEAD + Vector((0, 0, -0.1))
    return tg + d * (3.0 - 0.15 * u) + Vector((d.y, -d.x, 0)) * 0.8 + Vector((0, 0, 0.35)), tg
def shot_gone(t):                                  # side wide: chair and TV, the flash and the despawn
    u = t - E["G"]
    tg = Vector((2.0, 6.4, 1.9))
    return tg + Vector((6.4 - 0.2 * u, -5.0 + 0.1 * u, 1.6)), tg
def shot_end(t):                                   # back to the calendar, the loop
    u = t - E["H"]
    tg = CAL_C + Vector((0.4, 0, -0.6))
    return tg + Vector((1.8 - 0.4 * u, -7.5 + 0.6 * u, 0.2)), tg

SHOTS = [(shot_hook, None), (shot_boys, (E["boys"] - 0.2, E["boys"])), (shot_wide, (E["B"] - 0.3, E["B"] + 0.15)), (shot_shelf, (E["C"] - 0.3, E["C"] + 0.15)),
         (shot_her, (E["D"] - 0.3, E["D"] + 0.15)), (shot_over, (E["E"] - 0.3, E["E"] + 0.15)),
         (shot_him, (E["F"] - 0.3, E["F"] + 0.15)), (shot_gone, (E["G"] - 0.3, E["G"] + 0.15)),
         (shot_end, (E["H"] - 0.3, E["H"] + 0.15))]
LENS = {shot_wide: 30.0, shot_gone: 30.0}

def camera_at(t):
    k = 0
    for n, (fn, win) in enumerate(SHOTS):
        if win and t >= win[0]:
            k = n
    fn, win = SHOTS[k]
    loc, tg = fn(t)
    lens = LENS.get(fn, 35.0)
    if win and t < win[1] and k > 0:
        fn0 = SHOTS[k - 1][0]
        loc0, tg0 = fn0(t)
        u = smooth01((t - win[0]) / (win[1] - win[0]))
        loc, tg = loc0.lerp(loc, u), tg0.lerp(tg, u)
        lens = LENS.get(fn0, 35.0) * (1 - u) + lens * u
    d = (tg - loc).length
    fstop = 2.0 if d < 6 else (2.8 if d < 12 else 4.5)
    return loc, tg, fstop, lens

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    names = ("cal19", "bf", "gf", "tv", "shelf")
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        pts = {"cal19": CAL19, "bf": BF["head"].matrix_world @ Vector((0, 0, 0.6)),
               "gf": GF["head"].matrix_world @ Vector((0, 0, 0.6)), "tv": TV_C + Vector((0, -0.2, 1.4)),
               "shelf": Vector((5.6, 8.3, 3.3))}
        for k, p in pts.items():
            v = world_to_camera_view(scene, cam, p)
            out[k].append([round(v.x * 1080, 1), round((1 - v.y) * 1920, 1)] if v.z > 0 and 0 <= v.x <= 1 and 0 <= v.y <= 1 else None)
    with open(os.path.join(OUT, "anchors.json"), "w") as fh:
        json.dump(out, fh)

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1 + scn.frame_subframe) / FPS)

anchors()
apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
