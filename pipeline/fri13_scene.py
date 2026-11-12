"""Blender scene for 'Friday the 13th, checked by science': a voxel suburban street at dusk. A black cat crosses the
believer's path under the streetlamp; a parked car's hazards blink; he goes inside and shuts the door; the bro walks
under the ladder and the paint can lands on his head on "don't believe in it". Directed with direct.py (shot sheet in
ops/episodes/2026-11-13-friday-13th.md). Timed to render_fri13.py.

blender -b --factory-startup -P fri13_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
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
rng = random.Random(1113)
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


import direct as D

# ------------------------------------------------------------------ the set: a suburban street at dusk
# The house front faces -Y (wall y = 3.0 to 3.3). Lawn y 1..3, sidewalk y -1..1, road below y -1. The believer stands
# on the sidewalk at (0.4, 0.9); the cat crosses at y 0.2. The ladder leans on the wall at x -2.0, the door is at
# x 3.2, the lit window at x 4.8, the streetlamp at (1.3, -0.6), a parked car at x 6.5 on the road.

MATS["walk"] = pixel_mat("walk", [(0.34, 0.35, 0.38), (0.38, 0.39, 0.42), (0.30, 0.31, 0.34), (0.41, 0.41, 0.43)], rough=0.9)
MATS["road"] = pixel_mat("road", [(0.06, 0.065, 0.075), (0.075, 0.08, 0.09), (0.05, 0.055, 0.065)], rough=0.9)
MATS["grass"] = pixel_mat("grass", [(0.07, 0.16, 0.07), (0.09, 0.19, 0.08), (0.06, 0.13, 0.06), (0.11, 0.21, 0.09)], rough=0.95)
MATS["siding"] = pixel_mat("siding", [(0.22, 0.27, 0.36), (0.24, 0.29, 0.38), (0.20, 0.25, 0.33)], rough=0.9)
MATS["roofm"] = pixel_mat("roofm", [(0.09, 0.07, 0.08), (0.11, 0.08, 0.09), (0.07, 0.06, 0.07)], rough=0.9)
MATS["room"] = pixel_mat("room", [(0.55, 0.40, 0.26), (0.60, 0.44, 0.29), (0.50, 0.36, 0.23)], rough=0.9)
for i in range(-24, 24):
    for j in range(-9, 8):
        if j < -1:
            fill(i, i, j, j, -1, -1, "road")
        elif j < 1:
            fill(i, i, j, j, -1, -1, "walk")
        else:
            fill(i, i, j, j, -1, -1, "grass")
voxel_mesh("ground", GRID)
ROAD_DROP = boxes("roaddrop", [((-24, 24, -9, -1.0, -0.001, 0.0), colmat((0.05, 0.055, 0.065), 0.9))], (0, 0, -0.14))
LINE_M = colmat((0.75, 0.62, 0.20), 0.7)
boxes("dashes", [((x, x + 1.4, -5.1, -4.95, 0.0, 0.012), LINE_M) for x in range(-24, 24, 3)], (0, 0, -0.14))
boxes("curb", [((-24, 24, -1.12, -0.98, -0.15, 0.03), MATS["walk"])], (0, 0, 0))

SID, ROOF = MATS["siding"], MATS["roofm"]
TRIM = colmat((0.80, 0.80, 0.78), 0.7)
wall = [((-9, 2.7, 3.0, 3.3, 0, 5.0), SID), ((3.7, 4.2, 3.0, 3.3, 0, 5.0), SID), ((5.4, 9, 3.0, 3.3, 0, 5.0), SID),
        ((2.7, 3.7, 3.0, 3.3, 2.2, 5.0), SID), ((4.2, 5.4, 3.0, 3.3, 0, 1.2), SID), ((4.2, 5.4, 3.0, 3.3, 2.6, 5.0), SID),
        ((-9.2, 9.2, 2.6, 3.6, 5.0, 5.35), ROOF),
        ((2.6, 2.7, 2.98, 3.02, 0, 2.3), TRIM), ((3.7, 3.8, 2.98, 3.02, 0, 2.3), TRIM), ((2.6, 3.8, 2.98, 3.02, 2.2, 2.3), TRIM),
        ((4.1, 5.5, 2.96, 3.02, 1.1, 1.2), TRIM), ((4.1, 4.2, 2.98, 3.02, 1.1, 2.7), TRIM), ((5.4, 5.5, 2.98, 3.02, 1.1, 2.7), TRIM),
        ((4.1, 5.5, 2.98, 3.02, 2.6, 2.7), TRIM), ((4.78, 4.82, 3.1, 3.12, 1.2, 2.6), TRIM),
        ((2.5, 3.9, 2.35, 3.0, 0, 0.2), MATS["walk"])]
boxes("house", wall, (0, 0, 0))
ROOM = MATS["room"]
boxes("room", [((1.5, 7.0, 6.0, 6.2, 0, 3.2), ROOM), ((1.5, 7.0, 3.3, 6.2, -0.01, 0.0), colmat((0.25, 0.15, 0.09), 0.8)),
               ((1.5, 1.7, 3.3, 6.2, 0, 3.2), ROOM), ((6.8, 7.0, 3.3, 6.2, 0, 3.2), ROOM),
               ((1.5, 7.0, 3.3, 6.2, 3.2, 3.3), ROOM),
               ((5.6, 6.6, 5.4, 6.0, 0, 1.6), colmat((0.18, 0.10, 0.06), 0.8)),                  # a bookshelf
               ((2.0, 2.8, 5.0, 5.8, 0, 0.9), colmat((0.45, 0.12, 0.10), 0.8))], (0, 0, 0))     # an armchair
# the door: hinged on its right edge (x 3.7), open into the house until "drove"
door_pivot = B.link(bpy.data.objects.new("door_pivot", None))
door_pivot.location = (3.68, 3.15, 0.0)
door = boxes("door", [((-0.98, 0.0, -0.05, 0.05, 0.0, 2.18), colmat((0.42, 0.10, 0.08), 0.6)),
                      ((-0.86, -0.8, -0.09, -0.05, 1.0, 1.1), colmat((0.8, 0.7, 0.3), 0.3, metallic=0.9))], (0, 0, 0), door_pivot)
CURTAIN = boxes("curtain", [((0.0, 0.62, 0.0, 0.04, 0.0, 1.45), colmat((0.62, 0.18, 0.14), 0.9))], (4.2, 3.36, 1.18))
CURTAIN2 = boxes("curtain2", [((-0.62, 0.0, 0.0, 0.04, 0.0, 1.45), colmat((0.62, 0.18, 0.14), 0.9))], (5.4, 3.36, 1.18))
# neighbours, set back and darker, each with one lit window (depth)
WARM = colmat((1.0, 0.72, 0.38), 0.4, emit=3.0)
for n, x0 in enumerate((-22, -14, 11, 19)):
    boxes(f"nb{n}", [((x0, x0 + 6.5, 6.0, 6.3, 0, 4.4), colmat((0.10, 0.12, 0.17), 0.9)),
                     ((x0 - 0.2, x0 + 6.7, 5.6, 6.6, 4.4, 4.7), ROOF),
                     ((x0 + 2.2, x0 + 3.4, 5.97, 6.0, 1.4, 2.5), WARM if n % 2 == 0 else colmat((0.04, 0.05, 0.07), 0.5))], (0, 0, 0))
# a hedge and a mailbox for foreground layers
boxes("hedge", [((-9, -4.0, 2.4, 3.0, 0, 0.9), colmat((0.04, 0.10, 0.05), 0.95))], (0, 0, 0))
boxes("mailbox", [((-0.06, 0.06, -0.06, 0.06, 0, 1.0), colmat((0.15, 0.15, 0.16), 0.6)),
                  ((-0.18, 0.18, -0.3, 0.3, 1.0, 1.32), colmat((0.10, 0.12, 0.30), 0.5))], (-4.6, 0.7, 0))

# the ladder: foot at y 1.2 on the lawn, top against the wall at z 4.0; the paint can on the top rung
LAD = colmat((0.70, 0.71, 0.73), 0.4, metallic=0.7)
lad_parts = []
for x in (-2.38, -1.62):
    lad_parts.append(((x - 0.04, x + 0.04, -0.04, 0.04, 0.0, 4.4), LAD))
for r in range(1, 14):
    z = r * 0.31
    lad_parts.append(((-2.38, -1.62, -0.03, 0.03, z, z + 0.05), LAD))
ladder = boxes("ladder", lad_parts, (0, 1.2, 0))
ladder.rotation_euler = (-math.atan2(1.8, 4.0), 0, 0)
LADDER_TOP = Vector((-2.0, 2.75, 3.75))
CAN_M = colmat((0.62, 0.63, 0.66), 0.35, metallic=0.8)
PAINT_M = colmat((1.0, 0.30, 0.04), 0.35)
can = boxes("can", [((-0.16, 0.16, -0.16, 0.16, -0.2, 0.2), CAN_M), ((-0.165, 0.165, -0.165, 0.165, 0.12, 0.2), PAINT_M)], LADDER_TOP)
DRIPS = boxes("drips", [((-0.27, 0.27, -0.27, 0.27, 0.44, 0.47), PAINT_M), ((-0.27, -0.2, -0.1, 0.0, 0.1, 0.47), PAINT_M),
                        ((0.18, 0.27, -0.27, -0.2, 0.2, 0.47), PAINT_M), ((-0.05, 0.05, -0.28, -0.26, 0.05, 0.4), PAINT_M)], AWAY)
SHARDS = []
for n in range(26):
    SHARDS.append((boxes(f"shard{n}", [((-0.07, 0.07, -0.07, 0.07, -0.07, 0.07), colmat((1.0, 0.36, 0.06), 0.3, emit=1.5))], AWAY),
                   Vector((rng.uniform(-1.6, 1.6), rng.uniform(-1.4, 0.4), rng.uniform(1.0, 3.2)))))

# the streetlamp: post near camera right, arm over the sidewalk
POST = colmat((0.05, 0.06, 0.07), 0.5, metallic=0.4)
LAMP_GLASS = colmat((1.0, 0.82, 0.55), 0.3, emit=12.0)
boxes("lamppost", [((-0.08, 0.08, -0.08, 0.08, 0, 4.3), POST), ((-0.85, 0.08, -0.06, 0.06, 4.25, 4.35), POST),
                   ((-0.95, -0.55, -0.2, 0.2, 4.05, 4.25), POST), ((-0.9, -0.6, -0.15, 0.15, 3.98, 4.05), LAMP_GLASS)], (1.3, -0.6, 0))

# the car, parked on the road, hazards on in the 1993 shot
CAR = colmat((0.55, 0.62, 0.70), 0.35, metallic=0.5)
GLASS = colmat((0.03, 0.04, 0.06), 0.15)
TYRE = colmat((0.02, 0.02, 0.02), 0.8)
car = boxes("car", [((-1.9, 1.9, -0.85, 0.85, 0.3, 1.0), CAR), ((-1.0, 0.9, -0.8, 0.8, 1.0, 1.55), CAR),
                    ((-0.95, 0.85, -0.82, 0.82, 1.05, 1.5), GLASS), ((0.9, 1.25, -0.75, 0.75, 1.0, 1.02), GLASS)] +
          [((x - 0.33, x + 0.33, s * 0.95 - 0.13, s * 0.95 + 0.13, 0.0, 0.66), TYRE) for x in (-1.25, 1.25) for s in (-1, 1)],
          (6.5, -2.9, -0.14))
HAZ_ON = colmat((1.0, 0.55, 0.08), 0.3, emit=25.0)
HAZ_OFF = colmat((0.35, 0.20, 0.06), 0.4)
hazards = []
for x in (-1.92, 1.92):
    for s in (-1, 1):
        for mat, nm in ((HAZ_ON, "on"), (HAZ_OFF, "off")):
            hazards.append((boxes(f"haz{nm}{x}{s}", [((-0.04, 0.04, -0.14, 0.14, -0.07, 0.07), mat)], (6.5 + x, -2.9 + s * 0.6, 0.71)), nm))

# ------------------------------------------------------------------ cast
HIM = figure("him", hair=(0.18, 0.12, 0.07), shirt=(0.36, 0.38, 0.42), pants=(0.12, 0.13, 0.20), skin=(0.70, 0.50, 0.38))
HELMET = colmat((0.85, 0.14, 0.10), 0.35)
boxes("helmet", [((-0.29, 0.29, -0.31, 0.29, 0.36, 0.62), HELMET), ((-0.29, 0.29, -0.36, -0.28, 0.4, 0.46), HELMET),
                 ((-0.27, -0.24, -0.1, 0.1, 0.0, 0.36), colmat((0.05, 0.05, 0.05), 0.6)),
                 ((0.24, 0.27, -0.1, 0.1, 0.0, 0.36), colmat((0.05, 0.05, 0.05), 0.6))], (0, 0, 0), HIM["head"])
BRO = figure("bro", hair=(0.55, 0.38, 0.18), shirt=(0.95, 0.95, 0.93), pants=(0.15, 0.30, 0.55), skin=(0.78, 0.55, 0.40))
boxes("shades", [((-0.22, 0.22, -0.29, -0.25, 0.18, 0.3), colmat((0.01, 0.01, 0.01), 0.1, metallic=0.6))], (0, 0, 0), BRO["head"])
for side in ("L", "R"):    # tank top: bare upper arms
    BRO["arm" + side].data.materials[0] = colmat((0.78, 0.55, 0.40))

CAT_M = colmat((0.012, 0.012, 0.016), 0.5)
EYE_M = colmat((1.0, 0.85, 0.15), 0.3, emit=6.0)
cat = B.link(bpy.data.objects.new("cat", None))
cat_body = boxes("cat_body", [((-0.28, 0.28, -0.1, 0.1, 0.18, 0.38), CAT_M)], (0, 0, 0), cat)
cat_head = boxes("cat_head", [((-0.12, 0.12, -0.11, 0.11, -0.09, 0.11), CAT_M),
                              ((-0.1, -0.03, -0.09, -0.02, 0.11, 0.18), CAT_M), ((0.03, 0.1, -0.09, -0.02, 0.11, 0.18), CAT_M),
                              ((-0.08, -0.03, -0.115, -0.105, 0.0, 0.04), EYE_M), ((0.03, 0.08, -0.115, -0.105, 0.0, 0.04), EYE_M)],
                 (0.3, 0, 0.44), cat)
cat_tail = boxes("cat_tail", [((-0.025, 0.025, -0.025, 0.025, 0.0, 0.34), CAT_M)], (-0.27, 0, 0.34), cat)
cat_legs = [boxes(f"cat_leg{n}", [((-0.035, 0.035, -0.035, 0.035, -0.2, 0.0), CAT_M)], (x, y, 0.2), cat)
            for n, (x, y) in enumerate(((0.2, -0.06), (0.2, 0.06), (-0.2, -0.06), (-0.2, 0.06)))]

HIM_X, HIM_Y = 0.4, 0.9
BRO_Y = 2.35
UNDER = Vector((-2.0, BRO_Y, 0))
HEAD_TOP = Vector((-2.0, BRO_Y, 2.05))

# ------------------------------------------------------------------ light: the streetlamp, the window, the hazards, the flash
world = bpy.data.worlds.new("bg")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.006, 0.010, 0.03, 1)
lamp_ld = bpy.data.lights.new("lamp", "SPOT")
lamp_ld.energy = 1300.0
lamp_ld.color = (1.0, 0.76, 0.48)
lamp_ld.spot_size = math.radians(85)
lamp_ld.spot_blend = 0.7
lamp_ld.shadow_soft_size = 0.25
lamp = B.link(bpy.data.objects.new("lamp", lamp_ld))
D.point_at(lamp, Vector((0.55, -0.6, 3.95)), Vector((0.3, 0.6, 0.0)))
win_ld = bpy.data.lights.new("win", "AREA")
win_ld.energy = 260.0
win_ld.color = (1.0, 0.70, 0.40)
win_ld.size = 2.2
win = B.link(bpy.data.objects.new("win", win_ld))
D.point_at(win, Vector((4.6, 5.2, 2.6)), Vector((4.6, 2.0, 0.6)))
room_ld = bpy.data.lights.new("roomfill", "POINT")
room_ld.energy = 120.0
room_ld.color = (1.0, 0.68, 0.38)
roomfill = B.link(bpy.data.objects.new("roomfill", room_ld))
roomfill.location = (4.2, 4.6, 2.6)
rim = B.area("rim", Vector((0, 2.5, 6.5)), Vector((0, 0.5, 1.2)), 6.0, 380.0, (0.45, 0.55, 0.95))
fill_l = B.area("fill", Vector((0, -10, 2.0)), Vector((0, 1, 1.2)), 7.0, 110.0, (0.40, 0.48, 0.85))
haz_ld = bpy.data.lights.new("haz", "POINT")
haz_ld.energy = 0.0
haz_ld.color = (1.0, 0.55, 0.1)
haz_ld.shadow_soft_size = 0.3
hazl = B.link(bpy.data.objects.new("hazl", haz_ld))
hazl.location = (6.5, -1.6, 0.9)
orange_ld = bpy.data.lights.new("orange", "POINT")
orange_ld.energy = 0.0
orange_ld.color = (1.0, 0.42, 0.10)
orange_ld.shadow_soft_size = 0.2
orange = B.link(bpy.data.objects.new("orange", orange_ld))
orange.location = HEAD_TOP + Vector((0, -0.8, 0.4))
porch_ld = bpy.data.lights.new("porch", "POINT")      # a porch light by the door: lights the door and the cat on the step
porch_ld.energy = 70.0
porch_ld.color = (1.0, 0.74, 0.45)
porch_ld.shadow_soft_size = 0.15
porch = B.link(bpy.data.objects.new("porch", porch_ld))
porch.location = (4.0, 2.75, 2.35)
boxes("porchlamp", [((-0.08, 0.08, -0.06, 0.0, -0.12, 0.12), colmat((1.0, 0.8, 0.5), 0.3, emit=10.0))], (4.0, 2.99, 2.45))
cam = B.camera(lens=35, fstop=2.8)
B.render_settings(FPS, samples=32, motion_blur=0.3, look="AgX - Punchy")
key_ld = bpy.data.lights.new("key", "SPOT")      # re-placed per shot: the lamp or the window, cheated onto the face
key_ld.energy = 520.0
key_ld.color = (1.0, 0.80, 0.55)
key_ld.spot_size = math.radians(34)
key_ld.spot_blend = 0.6
key_ld.shadow_soft_size = 0.3
key = B.link(bpy.data.objects.new("key", key_ld))
rig = D.Rig(cam, {"lamp": lamp, "win": win, "roomfill": roomfill, "rim": rim, "fill": fill_l, "key": key})

# ------------------------------------------------------------------ the shot sheet (ops/episodes/2026-11-13-friday-13th.md)
T_HIT = E["believe"]
HOOK_EYE = Vector((HIM_X, 0.5, 0.75))
SHOTS = D.ShotList([
    D.Shot("hook", 0.0, eye=HOOK_EYE, lens=35, dist=5.0, yaw=0, pitch=5, screen=(0.5, 0.58),
           key=(1, 35, 40, 4.0), light={"key": 0.8, "fill": 0.5, "win": 0.4},
           note="low and locked off: the cat mid-step in the lamp pool, the believer frozen behind it"),
    D.Shot("fear", E["B"] - 0.05, eye=Vector((0.8, 0.6, 1.6)), lens=24, dist=7.5, yaw=0, pitch=-3, screen=(0.5, 0.55),
           light={"key": 0.0, "fill": 0.35, "win": 0.6}, note="wide and symmetrical: him hugging the lamp post, the house beyond"),
    D.Shot("study93", E["C"] - 0.05, eye=Vector((6.5, -2.9, 0.8)), lens=35, dist=9.5, yaw=-30, pitch=-7, screen=(0.5, 0.6),
           key=(1, 40, 40, 5.5), light={"key": 1.2, "fill": 0.4, "lamp": 0.6}, note="the parked car, its hazards the only moving light"),
    D.Shot("dutch", E["D"] - 0.05, eye=Vector((3.2, 3.0, 1.2)), lens=35, dist=5.6, yaw=8, pitch=-3, screen=(0.5, 0.55),
           key=(1, 30, 35, 3.2), light={"key": 0.8, "fill": 0.08, "rim": 0.4, "lamp": 0.5}, note="the front door; he goes in and shuts it on 'drove'"),
    D.Shot("setup", E["E"] - 0.05, eye=Vector((-2.4, BRO_Y, 1.5)), lens=28, dist=7.5, yaw=0, pitch=3, screen=(0.5, 0.56),
           key=(-1, 40, 35, 4.5), light={"key": 0.9, "fill": 0.3}, note="low, locked off: the bro strolls under the ladder"),
    D.Shot("hit", E["dont"] - 0.05, eye=HEAD_TOP + Vector((0, 0, -0.15)), lens=35, dist=4.8, yaw=78, pitch=-4, screen=(0.5, 0.5),
           move=("punch", 1.3), hit=T_HIT, kick=0.05, key=(1, 40, 35, 3.5), light={"key": 1.0, "fill": 0.2, "lamp": 0.4},
           note="the big moment: the can lands on his head, the only orange, the only fast move"),
    D.Shot("three", E["F"] - 0.05, eye=Vector((4.8, 3.6, 1.9)), lens=50, dist=4.8, yaw=0, pitch=-2, screen=(0.5, 0.45),
           key=(1, 30, 20, 3.0), light={"key": 0.55, "fill": 0.15, "lamp": 0.3}, note="the lit window, him peeking out in his helmet"),
    D.Shot("house", E["G"] - 0.05, eye=Vector((4.0, 2.7, 1.0)), lens=35, dist=5.8, yaw=0, pitch=2, screen=(0.5, 0.56),
           key=(1, 35, 40, 3.2), light={"key": 0.5, "fill": 0.08, "rim": 0.4, "lamp": 0.5}, note="curtains shut, the cat sits on his step and turns its head on 'house'"),
    D.Shot("loop", E["H"] - 0.05, eye=HOOK_EYE, lens=35, dist=5.0, yaw=0, pitch=5, screen=(0.5, 0.58),
           key=(1, 35, 40, 4.0), light={"key": 0.8, "fill": 0.5, "win": 0.4}, note="the hook framing again, the cat crosses again"),
], end=DUR)
SHOTS.check()
SHOTS.dump(os.path.join(os.path.dirname(OUT.rstrip("/\\")), "shots.json"), big=T_HIT)

# ------------------------------------------------------------------ motion

def cat_state(t):
    tc = D.on_twos(t, FPS)
    if tc < E["B"] - 0.05:
        u = tc
        x, y, face, walking = -1.2 + 0.75 * u, 0.25, 0.0, True
    elif tc >= E["H"] - 0.05:
        u = tc - (E["H"] - 0.05)
        x, y, face, walking = -1.2 + 0.75 * u, 0.25, 0.0, True
    elif tc >= E["G"] - 0.05:
        x, y, face, walking = 3.2, 2.2, -math.pi / 2, False
    else:
        cat.location = AWAY
        return
    cat.location = (x, y, 0.0)
    cat.rotation_euler = (0, 0, face)
    ph = tc * 11
    for n, leg in enumerate(cat_legs):
        leg.rotation_euler = (0, (0.5 * math.sin(ph + (math.pi if n in (1, 2) else 0))) if walking else 0.0, 0)
    cat_tail.rotation_euler = (0, -0.5 + 0.15 * math.sin(tc * 3), 0)
    turn = 0.0
    if not walking:
        turn = -0.9 * D.ars(tc, E["house"], wind=0.2, back=0.05, release=0.15, settle=0.3, over=0.1, snap="out")
    cat_head.rotation_euler = (0, 0, turn)

def him_state(t):
    tc = D.on_twos(t, FPS)
    shiver = 0.03 * math.sin(t * 40)
    if tc < E["B"] - 0.05 or tc >= E["H"] - 0.05:
        place(HIM, HIM_X, HIM_Y, face=(0, -1))
        pose(HIM, arms=(0.1 + shiver, 0.1 - shiver), head_turn=-0.35 + 0.7 * min(1.0, max(0.0, ((tc if tc < E["B"] else tc - E["H"] + 0.05)) / 3.0)))
    elif tc < E["D"] - 0.05:
        place(HIM, 1.0, -0.55, face=(1, 0))            # clinging to the lamp post
        pose(HIM, arms=((-1.35 + shiver, 0, 0.25), (-1.35 - shiver, 0, -0.25)), head_turn=0.6, head_nod=0.1)
    elif tc < E["F"] - 0.05:
        u = D.smoother((tc - (E["D"] - 0.05)) / max(0.3, E["drove"] - 0.15 - E["D"]))
        if u >= 1.0:
            HIM["root"].location = AWAY
        else:
            place(HIM, 3.2, 2.0 + 1.6 * u, face=(0, 1))
            pose(HIM, walk=0.6, phase=tc * 9)
    else:
        place(HIM, 4.8, 3.85, face=(0, -1), z=-0.05)    # peeking through the window
        pose(HIM, arms=(0.0, 0.0), head_turn=0.25 * math.sin(tc * 1.3), head_nod=-0.05)

def bro_state(t):
    tc = D.on_twos(t, FPS)
    if not (E["E"] - 0.05 <= tc < E["F"] - 0.05):
        BRO["root"].location = AWAY
        return
    arrive = T_HIT - 0.45
    u = D.clamp01((tc - (E["E"] - 0.05)) / max(0.5, arrive - E["E"]))
    x = -6.0 + (UNDER.x + 6.0) * D.smoother(u)
    place(BRO, x, BRO_Y, face=(1, 0))
    if u < 1.0:
        pose(BRO, walk=0.55, phase=tc * 8, head_nod=-0.08)
    else:
        jolt = D.ars(tc, T_HIT, wind=0.1, back=0.0, release=0.04, settle=0.25, over=0.15)
        pose(BRO, arms=((0.1, 0, -0.15), (0.1, 0, 0.15)), head_nod=0.25 * jolt - 0.08, head_turn=-0.6 * D.smoother((tc - T_HIT - 0.6) / 0.4))

def can_state(t):
    if t < T_HIT - 0.32:
        can.location, can.rotation_euler = LADDER_TOP, (0, 0, 0)
        DRIPS.location = AWAY
    elif t < T_HIT:
        u = (t - (T_HIT - 0.32)) / 0.32
        can.location = LADDER_TOP.lerp(HEAD_TOP + Vector((0, 0, 0.6)), u * u) + Vector((0, 0, -0.6 * u * u))
        can.rotation_euler = (math.pi * u, 0, 0)
        DRIPS.location = AWAY
    elif t < E["F"] - 0.05:
        can.location = HEAD_TOP + Vector((0, 0, 0.32))
        can.rotation_euler = (math.pi, 0, 0)
        DRIPS.location = BRO["head"].matrix_world.translation
        DRIPS.rotation_euler = BRO["head"].matrix_world.to_euler()
    else:
        can.location = AWAY
        DRIPS.location = AWAY
    for ob, vel in SHARDS:
        u = t - T_HIT
        if 0 <= u < 1.1 and t < E["F"] - 0.05:
            p = HEAD_TOP + Vector((0, -0.1, 0.3)) + vel * u + Vector((0, 0, -4.9 * u * u))
            p.z = max(0.05, p.z)
            ob.location = p
            k = max(0.001, 1 - u / 1.1)
            ob.scale = (k, k, k)
        else:
            ob.location = AWAY
    orange.data.energy = 0.0 if t < T_HIT or t >= E["F"] - 0.05 else 380.0 * D.flash(t, T_HIT, decay=0.5)

def set_state(t):
    # the door: open (swung into the house) until he is inside, shuts on "drove"
    close = D.ars(t, E["drove"] + 0.05, wind=0.15, back=0.05, release=0.12, settle=0.25, over=0.06)
    door_pivot.rotation_euler = (0, 0, math.radians(-100) * (1 - close) if t < E["F"] else 0.0)
    if t >= E["H"] - 0.05:
        door_pivot.rotation_euler = (0, 0, 0)
    # curtains: open while he peeks, drawn shut on "survived"
    sh = D.smoother((t - E["survived"]) / 0.5) if t < E["H"] - 0.05 else 0.0
    CURTAIN.scale = (0.25 + 0.75 * sh, 1, 1)
    CURTAIN2.scale = (0.25 + 0.75 * sh, 1, 1)
    # hazards blink at about 1.4 Hz during the 1993 shot
    on = E["C"] - 0.1 <= t < E["D"] - 0.05 and ((t - E["C"]) * 1.45) % 1.0 < 0.5
    for ob, nm in hazards:
        ob.hide_render = (nm == "on") != on
    hazl.data.energy = 140.0 if on else 0.0

def apply_state(t):
    cat_state(t)
    him_state(t)
    bro_state(t)
    can_state(t)
    set_state(t)
    SHOTS.apply(rig, t)

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    names = ("him", "bro", "cat")
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        pts = {"him": HIM["head"].matrix_world @ Vector((0, 0, 0.7)),
               "bro": BRO["head"].matrix_world @ Vector((0, 0, 0.6)),
               "cat": cat_head.matrix_world @ Vector((0, 0, 0.2))}
        for k, p in pts.items():
            v = world_to_camera_view(scene, cam, p)
            out[k].append([round(v.x * 1080, 1), round((1 - v.y) * 1920, 1)] if v.z > 0 and 0 <= v.x <= 1 and 0 <= v.y <= 1 else None)
    with open(os.path.join(OUT, "anchors.json"), "w") as fh:
        json.dump(out, fh)

CUTS = [sh.t0 for sh in SHOTS.shots[1:]] + [E["B"] - 0.05, E["D"] - 0.05, E["F"] - 0.05, E["G"] - 0.05, E["H"] - 0.05]
CUT_FRAMES = {n for c in CUTS for n in (int(c * FPS), int(c * FPS) + 1, int(c * FPS) + 2)}   # 1-based frames whose shutter can touch a cut
BLUR = scene.render.use_motion_blur

def on_render_pre(scn, *a):
    # figures and the camera jump at a cut; a shutter that spans it smears both, so frames at a cut render sharp
    scn.render.use_motion_blur = BLUR and scn.frame_current not in CUT_FRAMES

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1 + scn.frame_subframe) / FPS)

anchors()
apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
bpy.app.handlers.render_pre.append(on_render_pre)
B.render(OUT, MODE, NF)
