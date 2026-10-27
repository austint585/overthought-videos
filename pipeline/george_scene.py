"""Blender scene for 'Curious George learns about hypergamy': a voxel city apartment at night (wood floor, rug, couch,
window onto lit towers, a height chart by the door), a blocky monkey with no tail, and his tall roommate in a yellow
suit who walks in and puts on a tall yellow hat. Built in code and timed to the narration.

blender -b --factory-startup -P george_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
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
rng = random.Random(4)
AWAY = Vector((0, 0, -1.0e5))

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

def ramp(t, t0, t1):
    return smooth01((t - t0) / (t1 - t0))

# ------------------------------------------------------------------ pixel-texture materials (same method as spawner_scene)

def pixel_mat(name, pal, rough=0.85, lines=None, emit=0.0):
    """16x16 pixel noise on every face: the position (nudged inside the block) snapped to 1/16 and hashed.
    lines: (axis_scale, dark) seams."""
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
    base = r.outputs["Color"]
    if lines:
        scale, dark = lines
        sc = nt.nodes.new("ShaderNodeVectorMath"); sc.operation = "MULTIPLY"; sc.inputs[1].default_value = scale
        nt.links.new(snap.outputs[0], sc.inputs[0])
        sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sc.outputs[0], sep.inputs[0])
        acc = None
        for ax in ("X", "Y", "Z"):
            fr = nt.nodes.new("ShaderNodeMath"); fr.operation = "FRACT"; nt.links.new(sep.outputs[ax], fr.inputs[0])
            lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.06
            nt.links.new(fr.outputs[0], lt.inputs[0])
            if acc is None:
                acc = lt.outputs[0]
            else:
                mxx = nt.nodes.new("ShaderNodeMath"); mxx.operation = "MAXIMUM"
                nt.links.new(acc, mxx.inputs[0]); nt.links.new(lt.outputs[0], mxx.inputs[1]); acc = mxx.outputs[0]
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
        mix.inputs[7].default_value = (*dark, 1)
        nt.links.new(acc, mix.inputs[0]); nt.links.new(base, mix.inputs[6])
        base = mix.outputs[2]
    nt.links.new(base, p.inputs["Base Color"])
    if emit:
        nt.links.new(base, p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = emit
    return m

def solid(name, color, rough=0.6, emit=0.0, emit_color=None, metallic=0.0):
    m = B.material(name, color, metallic, rough)
    p = B.bsdf(m)
    p.inputs["Emission Color"].default_value = (*(emit_color or color), 1)
    p.inputs["Emission Strength"].default_value = emit
    return m

NIGHT = (0.06, 0.08, 0.20)
MATS = {
    "floor": pixel_mat("floor", [(0.36, 0.22, 0.12), (0.40, 0.25, 0.13), (0.33, 0.20, 0.10), (0.43, 0.27, 0.15)],
                       lines=((1, 0.25, 1), (0.20, 0.12, 0.06))),
    "wall": pixel_mat("wall", [(0.50, 0.58, 0.46), (0.53, 0.61, 0.49), (0.47, 0.55, 0.43)]),
    "base": pixel_mat("base", [(0.30, 0.18, 0.09), (0.34, 0.21, 0.11)], lines=((1, 1, 1), (0.16, 0.09, 0.04))),
    "ceiling": pixel_mat("ceiling", [(0.62, 0.60, 0.55), (0.66, 0.64, 0.59)]),
    "window": pixel_mat("window", [NIGHT, NIGHT, NIGHT, (0.08, 0.10, 0.25), NIGHT, (1.0, 0.78, 0.40)], rough=0.3,
                        lines=((1, 1, 1), (0.02, 0.02, 0.03)), emit=1.6),
    "hall": solid("hall", (1.0, 0.92, 0.78), emit=3.0),
}

# ------------------------------------------------------------------ voxel apartment

GRID = {}

def fill(i0, i1, j0, j1, k0, k1, mat):
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            for k in range(k0, k1 + 1):
                if mat is None:
                    GRID.pop((i, j, k), None)
                else:
                    GRID[(i, j, k)] = mat

X0, X1, Y1, ZC = -6, 5, 7, 4          # inner room: x -6..6, y 0..8, ceiling at z 4
fill(X0, X1, -2, Y1 + 2, -1, -1, "floor")
fill(X0 - 1, X0 - 1, -2, Y1 + 1, 0, ZC - 1, "wall")
fill(X1 + 1, X1 + 1, -2, Y1 + 1, 0, ZC - 1, "wall")
fill(X0 - 1, X1 + 1, Y1 + 1, Y1 + 1, 0, ZC - 1, "wall")
fill(X0 - 1, X1 + 1, -2, Y1 + 2, ZC, ZC, "ceiling")
fill(X0, X1, Y1 + 1, Y1 + 1, 0, 0, "base")
fill(X0 - 1, X0 - 1, -2, Y1, 0, 0, "base")
fill(X1 + 1, X1 + 1, -2, Y1, 0, 0, "base")
fill(0, 1, Y1 + 1, Y1 + 1, 0, 2, None)            # doorway x 0..2, z 0..3
fill(-1, 2, Y1 + 3, Y1 + 3, 0, 3, "hall")         # lit hallway behind it
fill(-1, -1, Y1 + 2, Y1 + 2, 0, 3, "wall")
fill(2, 2, Y1 + 2, Y1 + 2, 0, 3, "wall")
fill(3, 4, Y1 + 1, Y1 + 1, 1, 2, "window")        # window over the couch, x 3..5, z 1..3

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

voxel_mesh("room", GRID)

# ------------------------------------------------------------------ boxes, furniture

_mat_cache = {}
def colmat(color, rough=0.55, emit=0.0):
    key = (color, rough, emit)
    if key not in _mat_cache:
        _mat_cache[key] = solid(f"c{len(_mat_cache)}", color, rough, emit)
    return _mat_cache[key]

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

WALL_Y = Y1 + 1.0
RUG = pixel_mat("rug", [(0.55, 0.12, 0.10), (0.60, 0.15, 0.12), (0.50, 0.10, 0.09)], lines=((0.5, 0.5, 1), (0.85, 0.70, 0.40)))
boxes("rug", [((-3.6, 0.4, 4.4, 7.7, 0.0, 0.03), RUG)], (0, 0, 0))
TEAL, TEAL2 = colmat((0.10, 0.32, 0.36), 0.8), colmat((0.13, 0.38, 0.42), 0.8)
boxes("couch", [((2.7, 5.9, 6.75, 7.95, 0.0, 0.42), TEAL), ((2.7, 5.9, 7.5, 7.95, 0.42, 1.15), TEAL),
                ((2.7, 3.0, 6.75, 7.95, 0.42, 0.75), TEAL), ((5.6, 5.9, 6.75, 7.95, 0.42, 0.75), TEAL),
                ((3.02, 4.28, 6.8, 7.5, 0.42, 0.55), TEAL2), ((4.32, 5.58, 6.8, 7.5, 0.42, 0.55), TEAL2)], (0, 0, 0))
LAMP_POS = Vector((-4.6, 7.3, 0.0))
boxes("lamp", [((-0.25, 0.25, -0.25, 0.25, 0.0, 0.06), colmat((0.1, 0.1, 0.1), 0.4)),
               ((-0.04, 0.04, -0.04, 0.04, 0.06, 1.65), colmat((0.1, 0.1, 0.1), 0.4)),
               ((-0.3, 0.3, -0.3, 0.3, 1.55, 2.0), colmat((1.0, 0.85, 0.6), 0.6, emit=4.0))], LAMP_POS)
boxes("plant", [((-0.22, 0.22, -0.22, 0.22, 0.0, 0.45), colmat((0.55, 0.30, 0.18), 0.7)),
                ((-0.3, 0.3, -0.3, 0.3, 0.45, 1.0), colmat((0.15, 0.40, 0.15), 0.8)),
                ((-0.18, 0.18, -0.18, 0.18, 1.0, 1.35), colmat((0.18, 0.46, 0.18), 0.8))], (-5.4, 6.2, 0.0))
door = boxes("door", [((-2.0, 0.0, -0.08, 0.0, 0.0, 3.0), colmat((0.42, 0.26, 0.12), 0.6)),
                      ((-1.82, -1.7, -0.2, -0.08, 1.3, 1.45), colmat((0.8, 0.7, 0.3), 0.3))], (2.0, WALL_Y, 0.0))
boxes("frame", [((-0.12, 0.0, -0.06, 0.0, 0.0, 3.1), colmat((0.95, 0.93, 0.88), 0.5)),
                ((2.0, 2.12, -0.06, 0.0, 0.0, 3.1), colmat((0.95, 0.93, 0.88), 0.5)),
                ((-0.12, 2.12, -0.06, 0.0, 3.0, 3.12), colmat((0.95, 0.93, 0.88), 0.5))], (0.0, WALL_Y, 0.0))

# the height chart on the wall, ticks every 0.25
CHART_X = -3.0
parts = [((CHART_X - 0.16, CHART_X + 0.16, WALL_Y - 0.05, WALL_Y, 0.0, 3.5), colmat((0.94, 0.92, 0.85), 0.6))]
for n in range(1, 15):
    z = 0.25 * n
    wid = 0.16 if n % 4 == 0 else 0.07
    parts.append(((CHART_X - 0.16, CHART_X - 0.16 + wid, WALL_Y - 0.07, WALL_Y - 0.05, z - 0.012, z + 0.012), colmat((0.05, 0.05, 0.05), 0.5)))
boxes("chart", parts, (0, 0, 0))

# ------------------------------------------------------------------ characters

def george_fig():
    """A blocky monkey: short legs, long arms, tan face and ears, no tail. Local units; the root is scaled."""
    root = B.link(bpy.data.objects.new("george", None))
    Br, Tn, Dk = colmat((0.33, 0.19, 0.09), 0.85), colmat((0.86, 0.68, 0.48), 0.75), colmat((0.03, 0.02, 0.02), 0.4)
    f = {"root": root}
    for side, x in (("L", -0.09), ("R", 0.09)):
        f["leg" + side] = boxes(f"g_leg{side}", [((-0.08, 0.08, -0.08, 0.08, -0.28, 0.0), Br),
                                                 ((-0.085, 0.085, -0.13, 0.085, -0.28, -0.22), Tn)], (x, 0, 0.28), root)
    f["body"] = boxes("g_body", [((-0.18, 0.18, -0.12, 0.12, 0.0, 0.36), Br),
                                 ((-0.12, 0.12, -0.13, -0.11, 0.04, 0.3), Tn)], (0, 0, 0.28), root)
    for side, x in (("L", -0.24), ("R", 0.24)):
        f["arm" + side] = boxes(f"g_arm{side}", [((-0.06, 0.06, -0.06, 0.06, -0.5, 0.0), Br),
                                                 ((-0.068, 0.068, -0.068, 0.068, -0.58, -0.47), Tn)], (x, 0, 0.6), root)
    f["head"] = boxes("g_head", [((-0.2, 0.2, -0.19, 0.19, 0.0, 0.38), Br),
                                 ((-0.15, 0.15, -0.205, -0.18, 0.02, 0.29), Tn),
                                 ((-0.1, 0.1, -0.26, -0.18, 0.02, 0.13), Tn),
                                 ((-0.11, -0.04, -0.215, -0.2, 0.19, 0.26), Dk), ((0.04, 0.11, -0.215, -0.2, 0.19, 0.26), Dk),
                                 ((-0.06, 0.06, -0.266, -0.255, 0.05, 0.07), colmat((0.45, 0.20, 0.12), 0.6)),
                                 ((-0.03, -0.01, -0.266, -0.258, 0.1, 0.12), Dk), ((0.01, 0.03, -0.266, -0.258, 0.1, 0.12), Dk),
                                 ((-0.28, -0.2, -0.04, 0.04, 0.11, 0.27), Tn), ((0.2, 0.28, -0.04, 0.04, 0.11, 0.27), Tn),
                                 ((-0.08, 0.08, -0.17, 0.02, 0.38, 0.43), Br)], (0, 0, 0.64), root)
    return f

def man_fig():
    """The roommate: the standard blocky figure in a yellow suit and tie."""
    root = B.link(bpy.data.objects.new("man", None))
    Y, Y2, S = colmat((0.95, 0.76, 0.10), 0.6), colmat((0.88, 0.68, 0.08), 0.6), colmat((0.88, 0.66, 0.50))
    H, D, Shoe = colmat((0.22, 0.12, 0.06), 0.7), colmat((0.03, 0.02, 0.02), 0.4), colmat((0.25, 0.14, 0.06), 0.5)
    f = {"root": root}
    for side, x in (("L", -0.125), ("R", 0.125)):
        f["leg" + side] = boxes(f"m_leg{side}", [((-0.125, 0.125, -0.125, 0.125, -0.75, 0.0), Y2),
                                                 ((-0.13, 0.13, -0.17, 0.13, -0.75, -0.66), Shoe)], (x, 0, 0.75), root)
    f["body"] = boxes("m_body", [((-0.25, 0.25, -0.125, 0.125, 0, 0.75), Y),
                                 ((-0.1, 0.1, -0.135, -0.125, 0.5, 0.75), colmat((0.97, 0.95, 0.9), 0.5)),
                                 ((-0.04, 0.04, -0.14, -0.13, 0.22, 0.72), colmat((0.80, 0.42, 0.06), 0.5)),
                                 ((-0.25, 0.25, -0.13, 0.13, 0.0, 0.05), colmat((0.35, 0.22, 0.08), 0.5))], (0, 0, 0.75), root)
    for side, x in (("L", -0.375), ("R", 0.375)):
        f["arm" + side] = boxes(f"m_arm{side}", [((-0.125, 0.125, -0.125, 0.125, -0.68, 0.0), Y),
                                                 ((-0.11, 0.11, -0.11, 0.11, -0.82, -0.68), S)], (x, 0, 1.5), root)
    f["head"] = boxes("m_head", [((-0.25, 0.25, -0.25, 0.25, 0, 0.5), S), ((-0.27, 0.27, -0.27, 0.27, 0.4, 0.55), H),
                                 ((-0.27, 0.27, 0.08, 0.28, 0.15, 0.5), H),
                                 ((-0.16, -0.06, -0.265, -0.25, 0.22, 0.29), D), ((0.06, 0.16, -0.265, -0.25, 0.22, 0.29), D),
                                 ((-0.08, 0.08, -0.262, -0.25, 0.07, 0.1), colmat((0.55, 0.30, 0.22))),
                                 ((-0.04, 0.04, -0.3, -0.25, 0.14, 0.24), colmat((0.80, 0.58, 0.44)))], (0, 0, 1.5), root)
    return f

G_SCALE, M_SCALE = 0.88, 1.15
GEO = george_fig()
MAN = man_fig()
GEO["root"].scale = (G_SCALE,) * 3
MAN["root"].scale = (M_SCALE,) * 3
G_POS = Vector((-1.9, 6.6, 0.0))
M_STAND = Vector((-0.75, 6.6, 0.0))
PATH = [Vector((1.0, 8.9, 0.0)), Vector((1.0, 6.6, 0.0)), M_STAND]
G_TOP, M_TOP = 1.07 * G_SCALE, 2.05 * M_SCALE
HAT_H = 0.62 * M_SCALE

HAT_Y, HAT_B = colmat((0.98, 0.80, 0.08), 0.55), colmat((0.80, 0.55, 0.05), 0.55)
hat = boxes("hat", [((-0.5, 0.5, -0.5, 0.5, 0.0, 0.06), HAT_Y), ((-0.27, 0.27, -0.27, 0.27, 0.06, 0.62), HAT_Y),
                    ((-0.28, 0.28, -0.28, 0.28, 0.08, 0.18), HAT_B)], AWAY)
hat.scale = (M_SCALE,) * 3
phone = boxes("phone", [((-0.06, 0.06, -0.02, 0.02, -0.75, -0.55), colmat((0.05, 0.05, 0.06), 0.3)),
                        ((-0.05, 0.05, 0.02, 0.025, -0.73, -0.57), colmat((0.6, 0.8, 1.0), 0.3, emit=3.0)),
                        ((-0.05, 0.05, -0.025, -0.02, -0.73, -0.57), colmat((0.6, 0.8, 1.0), 0.3, emit=3.0))], (0, 0, 0), GEO["armR"])
marks = {}
for name, h, col in (("g", G_TOP, (1.0, 0.42, 0.17)), ("m", M_TOP, (1.0, 0.80, 0.24)), ("h", M_TOP + HAT_H, (1.0, 0.80, 0.24))):
    marks[name] = boxes(f"mark_{name}", [((CHART_X - 0.22, CHART_X + 0.22, WALL_Y - 0.09, WALL_Y - 0.05, h - 0.025, h + 0.025),
                                          colmat(col, 0.4, emit=1.5))], AWAY)

GOLD_M = solid("gold_shell", (1.0, 0.75, 0.15), rough=0.5, emit=1.5)
B.bsdf(GOLD_M).inputs["Alpha"].default_value = 0.2
shell = boxes("shell", [((-0.33, 0.33, -0.2, 0.2, 0.0, 1.58), GOLD_M), ((-0.33, 0.33, -0.33, 0.33, 1.45, 2.2), GOLD_M),
                        ((-0.55, 0.55, -0.2, 0.2, 0.75, 1.55), GOLD_M)], AWAY)
shell.scale = (M_SCALE,) * 3
RAIN_M = colmat((0.55, 0.70, 1.0), 0.2, emit=1.2)
rain = [boxes(f"rain{k}", [((-0.012, 0.012, -0.01, 0.01, -0.12, 0.0), RAIN_M)], AWAY) for k in range(26)]
RAIN_X = [3.05 + rng.random() * 1.9 for _ in rain]
RAIN_P = [rng.random() for _ in rain]

# ------------------------------------------------------------------ lights, world, camera

world = bpy.data.worlds.new("bg")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.02, 0.03, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
ceil = B.area("ceil", Vector((-1.0, 4.5, ZC - 0.15)), Vector((-1.0, 4.5, 0)), 3.0, 200.0, (1.0, 0.86, 0.66), size_y=3.0)
key = B.area("key", Vector((-0.8, 2.2, 3.0)), Vector((-1.4, 6.6, 1.0)), 2.0, 110.0, (1.0, 0.95, 0.88))
win = B.area("win", Vector((4.0, 7.7, 2.0)), Vector((2.0, 3.0, 1.0)), 2.0, 60.0, (0.55, 0.65, 1.0))
blue = B.area("blue", Vector((1.0, 3.0, 3.5)), Vector((-1.5, 6.6, 0.3)), 3.0, 0.0, (0.35, 0.5, 1.0))
lamp_ld = bpy.data.lights.new("lamp", "POINT"); lamp_ld.color = (1.0, 0.75, 0.45); lamp_ld.shadow_soft_size = 0.3
lamp_l = B.link(bpy.data.objects.new("lamp_l", lamp_ld)); lamp_l.location = LAMP_POS + Vector((0, 0, 1.75))
ph_ld = bpy.data.lights.new("phone", "POINT"); ph_ld.color = (0.6, 0.8, 1.0); ph_ld.shadow_soft_size = 0.05
ph_l = B.link(bpy.data.objects.new("phone_l", ph_ld))
gold_ld = bpy.data.lights.new("gold", "POINT"); gold_ld.color = (1.0, 0.75, 0.3); gold_ld.shadow_soft_size = 0.5
gold_l = B.link(bpy.data.objects.new("gold_l", gold_ld))
hall_ld = bpy.data.lights.new("hall", "POINT"); hall_ld.color = (1.0, 0.85, 0.65); hall_ld.shadow_soft_size = 0.4
hall_l = B.link(bpy.data.objects.new("hall_l", hall_ld)); hall_l.location = (1.0, WALL_Y + 1.0, 2.2)

cam = B.camera(lens=30, fstop=2.8)
B.render_settings(FPS, samples=32, motion_blur=0.3)

# ------------------------------------------------------------------ posing

def place(f, p, face=(0, -1)):
    f["root"].location = p
    f["root"].rotation_euler = (0, 0, math.atan2(face[0], -face[1]))

def pose(f, walk=0.0, phase=0.0, arms=None, sit=False, head_turn=0.0, head_nod=0.0):
    s = math.sin(phase) * walk
    f["legL"].rotation_euler = (-math.pi / 2 if sit else s * 0.8, 0, 0)
    f["legR"].rotation_euler = (-math.pi / 2 if sit else -s * 0.8, 0, 0)
    aL, aR = arms if arms else (-s * 0.7, s * 0.7)
    f["armL"].rotation_euler = (aL, 0, 0) if not isinstance(aL, tuple) else aL
    f["armR"].rotation_euler = (aR, 0, 0) if not isinstance(aR, tuple) else aR
    f["head"].rotation_euler = (head_nod, 0, head_turn)

def path_point(d):
    for a, b in zip(PATH, PATH[1:]):
        seg = (b - a).length
        if d <= seg:
            return a.lerp(b, d / seg), (b - a).normalized()
        d -= seg
    return PATH[-1].copy(), (PATH[-1] - PATH[-2]).normalized()

PATH_LEN = sum((b - a).length for a, b in zip(PATH, PATH[1:]))
T_HAT = E["hat"]
T_SIT = E["over"] - 0.45

def george_state(t):
    turn = ramp(t, E["tail"] - 0.45, E["tail"] - 0.05) * (1 - ramp(t, E["D"] - 0.5, E["D"] - 0.1))
    look = ramp(t, E["belt"] - 0.6, E["belt"] - 0.2) * (1 - ramp(t, E["H"], E["H"] + 0.4))
    sit = ramp(t, T_SIT, T_SIT + 0.45)
    p = G_POS + Vector((0, 0, -0.25 * sit))
    GEO["root"].location = p
    GEO["root"].rotation_euler = (0, 0, math.pi * turn)
    read = (1 - turn) * (1 - sit)
    right = -1.3 * read - 0.15 * sit
    nod = 0.28 * read - 0.4 * look + 0.45 * sit + 0.03 * math.sin(t * 1.7)
    pose(GEO, sit=sit > 0.5, arms=(-0.1 - 0.15 * sit, right), head_nod=nod, head_turn=0.55 * look * (1 - sit))
    if 0 < sit < 1:
        for leg in ("legL", "legR"):
            GEO[leg].rotation_euler = (-math.pi / 2 * sit, 0, 0)
    ph_l.location = GEO["root"].matrix_world @ Vector((0, -0.38, 0.75)) if read > 0.3 else AWAY
    ph_ld.energy = 7.0 * read

def man_state(t):
    if t < E["walk0"] - 0.05:
        MAN["root"].location = AWAY
        return
    d = PATH_LEN * smooth01((t - E["walk0"]) / (E["walk1"] - E["walk0"])) if t < E["walk1"] else PATH_LEN
    p, dirv = path_point(d)
    walking = t < E["walk1"]
    rise = 0.3 * ramp(t, E["J"], E["ascending"] + 0.6)
    place(MAN, p + Vector((0, 0, rise)), face=(dirv.x, dirv.y) if walking else (0, -1))
    up = ramp(t, T_HAT - 0.5, T_HAT - 0.15) * (1 - ramp(t, T_HAT + 0.15, T_HAT + 0.55))
    look_down = ramp(t, E["mogged"] - 0.3, E["mogged"] + 0.1) * (1 - ramp(t, E["H"], E["H"] + 0.4))
    arms = None if walking else (0.04 * math.sin(t * 1.3), -2.75 * up + 0.04 * math.sin(t * 1.3 + 1))
    pose(MAN, walk=1.0 if walking else 0.0, phase=(t - E["walk0"]) * 8.0, arms=arms,
         head_nod=0.32 * look_down, head_turn=-0.45 * look_down)
    if walking:
        MAN["armR"].rotation_euler = (-0.15, 0, 0)

def hat_state(t):
    if MAN["root"].location.z < -100:
        hat.location = AWAY
        return
    bpy.context.view_layer.update()
    hand = MAN["armR"].matrix_world @ Vector((0, -0.05, -1.0))
    top = MAN["head"].matrix_world @ Vector((0, 0, 0.55))
    u = ramp(t, T_HAT - 0.45, T_HAT)
    hat.location = hand.lerp(top, u) + Vector((0, 0, 0.25 * math.sin(math.pi * u)))
    hat.rotation_euler = (0.35 * (1 - u), 0, 0)

def apply_state(t):
    door_open = ramp(t, E["walk0"] - 0.4, E["walk0"] + 0.1) * (1 - ramp(t, E["walk1"] + 0.2, E["walk1"] + 0.9))
    door.rotation_euler = (0, 0, 1.6 * door_open)
    george_state(t)
    man_state(t)
    hat_state(t)
    for name, t0 in (("g", E["belt"] - 0.15), ("m", E["chad"] - 0.1), ("h", T_HAT + 0.15)):
        marks[name].location = (0, 0, 0) if E["E"] - 0.5 < t and t >= t0 and t < E["H"] else AWAY
    over = ramp(t, T_SIT - 0.2, T_SIT + 0.6) * (1 - ramp(t, E["J"] - 0.2, E["J"] + 0.4))
    dim = 1 - 0.65 * over
    ceil.data.energy = 200.0 * dim
    key.data.energy = 110.0 * (1 - 0.5 * over)
    lamp_ld.energy = 45.0 * dim
    win.data.energy = 60.0 + 40.0 * over
    blue.data.energy = 220.0 * over
    B.bsdf(MATS["window"]).inputs["Emission Strength"].default_value = 1.6 - 0.9 * over
    hall_ld.energy = 90.0 * ramp(t, E["walk0"] - 0.4, E["walk0"]) * (1 - ramp(t, E["walk1"] + 0.2, E["walk1"] + 0.9))
    for k, ob in enumerate(rain):
        if over > 0.05:
            u = (t * 1.6 + RAIN_P[k]) % 1.0
            ob.location = (RAIN_X[k], WALL_Y - 0.03, 2.95 - 1.85 * u)
        else:
            ob.location = AWAY
    glow = ramp(t, E["J"] - 0.1, E["ascending"] + 0.3)
    if glow > 0:
        sc = M_SCALE * (1.0 + 0.04 * math.sin(t * 7) + 0.08 * glow)
        shell.location = MAN["root"].location + Vector((0, 0, (M_SCALE - sc) * 1.2))
        shell.scale = (sc, sc, sc)
        B.bsdf(GOLD_M).inputs["Alpha"].default_value = 0.08 * glow
        gold_l.location = MAN["root"].location + Vector((0.2, -0.9, 1.8))
        gold_ld.energy = 120.0 * glow + 250.0 * math.exp(-max(0.0, t - E["ascending"]) * 3) * (t >= E["ascending"])
    else:
        shell.location = AWAY
        gold_l.location = AWAY
        gold_ld.energy = 0.0
    loc, target, fstop, lens = camera_at(t)
    B.aim(cam, loc, target)
    cam.data.lens = lens
    cam.data.dof.focus_distance = (target - loc).length
    cam.data.dof.aperture_fstop = fstop
    cam.data.clip_start = 0.05
    cam.data.clip_end = 200

# ------------------------------------------------------------------ camera: each shot returns (camera location, look target)

GH = G_POS + Vector((0, 0, 0.75))
MH = M_STAND + Vector((0, 0, 2.1))

def shot_hook(t):
    u = t / max(1.0, E["B"])
    tg = GH + Vector((0.25, 0, 0.1))
    return tg + Vector((0.75 - 0.15 * u, -2.1 + 0.25 * u, 0.4)), tg
def shot_close(t):
    u = t - E["B"]
    return GH + Vector((0.4 - 0.05 * u, -1.3 + 0.05 * u, 0.12)), GH + Vector((0, 0, -0.02))
def shot_rear(t):
    tg = G_POS + Vector((-0.2, 0, 0.55))
    u = t - E["C"]
    return tg + Vector((0.9 - 0.08 * u, -2.2, 0.35)), tg
def shot_wide(t):
    u = t - E["D"]
    return Vector((0.6 - 0.08 * u, 1.4, 2.0)), Vector((-0.2, 7.0, 1.2))
def shot_height(t):
    tg = Vector((-1.6, 6.6, 1.95))
    u = t - E["E"]
    return tg + Vector((0.0 + 0.03 * u, -5.0, 0.0)), tg
def shot_low(t):
    u = t - E["mogged"]
    return Vector((-2.3 + 0.05 * u, 5.35, 0.45)), M_STAND + Vector((0, 0, 2.15))
def shot_study(t):
    u = t - E["H"]
    return Vector((-0.8 - 0.05 * u, 3.0, 1.6)), Vector((-1.4, 6.6, 1.2))
def shot_over(t):
    u = t - E["I"]
    tg = G_POS + Vector((0, 0, 0.42))
    return tg + Vector((0.05 - 0.04 * u, -1.9 + 0.06 * u, 0.3)), tg
def shot_ascend(t):
    u = t - E["J"]
    tg = MAN["root"].location + Vector((0, 0, 1.75)) if MAN["root"].location.z > -100 else MH
    return tg + Vector((0.5, -3.2 + 0.1 * u, -0.9)), tg
def shot_end(t):
    u = t - E["K"]
    tg = Vector((-1.35, 6.6, 1.35))
    return tg + Vector((0.3 + 0.05 * u, -3.4 - 0.2 * u, 0.3)), tg

SHOTS = [(shot_hook, None), (shot_close, (E["B"] - 0.25, E["B"] + 0.15)), (shot_rear, (E["C"] - 0.25, E["C"] + 0.15)),
         (shot_wide, (E["D"] - 0.3, E["D"] + 0.15)), (shot_height, (E["E"] - 0.3, E["E"] + 0.15)),
         (shot_low, (E["mogged"] - 0.45, E["mogged"] - 0.1)), (shot_study, (E["H"] - 0.3, E["H"] + 0.15)),
         (shot_over, (E["I"] - 0.3, E["I"] + 0.15)), (shot_ascend, (E["J"] - 0.3, E["J"] + 0.15)),
         (shot_end, (E["K"] - 0.3, E["K"] + 0.4))]

LENS = {shot_close: 35.0, shot_wide: 24.0, shot_height: 26.0, shot_low: 24.0, shot_over: 32.0}

def camera_at(t):
    k = 0
    for n, (fn, win_) in enumerate(SHOTS):
        if win_ and t >= win_[0]:
            k = n
    fn, win_ = SHOTS[k]
    loc, tg = fn(t)
    lens = LENS.get(fn, 30.0)
    if win_ and t < win_[1] and k > 0:
        fn0 = SHOTS[k - 1][0]
        loc0, tg0 = fn0(t)
        u = smooth01((t - win_[0]) / (win_[1] - win_[0]))
        loc, tg = loc0.lerp(loc, u), tg0.lerp(tg, u)
        lens = LENS.get(fn0, 30.0) * (1 - u) + lens * u
    d = (tg - loc).length * 30.0 / lens
    fstop = 2.0 if d < 3 else (2.8 if d < 6 else 4.0)
    return loc, tg, fstop, lens

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    names = ("george", "rear", "man", "mark_g", "mark_m", "mark_h")
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        pts = {
            "george": GEO["root"].matrix_world @ Vector((0, 0, 1.12)),
            "rear": GEO["root"].matrix_world @ Vector((0, 0.13, 0.36)),
            "man": MAN["root"].matrix_world @ Vector((0, 0, 2.2)),
            "mark_g": Vector((CHART_X + 0.2, WALL_Y - 0.08, G_TOP)),
            "mark_m": Vector((CHART_X + 0.2, WALL_Y - 0.08, M_TOP)),
            "mark_h": Vector((CHART_X + 0.2, WALL_Y - 0.08, M_TOP + HAT_H)),
        }
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
