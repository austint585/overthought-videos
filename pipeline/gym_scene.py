"""Blender scene for 'Gym bro reads the label': the voxel apartment from the George episode with a kitchen counter,
a gym bro in a tank top and a backwards cap reading an energy drink can, creatine, raw eggs and raw liver popping onto
the counter, a red alarm when he finds the sugar, and a flex at the end. Built in code and timed to the narration.

blender -b --factory-startup -P gym_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
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

# ------------------------------------------------------------------ the gym bro and the counter

GREY, GREY2 = colmat((0.42, 0.43, 0.46), 0.8), colmat((0.32, 0.33, 0.36), 0.8)
SKIN, HAIR = colmat((0.80, 0.56, 0.40)), colmat((0.10, 0.06, 0.03), 0.8)
SHORTS, SHOE = colmat((0.05, 0.05, 0.06), 0.7), colmat((0.92, 0.92, 0.90), 0.5)
CAP = colmat((0.75, 0.10, 0.10), 0.6)
DK = colmat((0.03, 0.02, 0.02), 0.4)

def bro_fig():
    root = B.link(bpy.data.objects.new("bro", None))
    f = {"root": root}
    for side, x in (("L", -0.14), ("R", 0.14)):
        f["leg" + side] = boxes(f"leg{side}", [((-0.14, 0.14, -0.14, 0.14, -0.3, 0.0), SHORTS),
                                               ((-0.13, 0.13, -0.13, 0.13, -0.75, -0.3), SKIN),
                                               ((-0.14, 0.14, -0.18, 0.14, -0.75, -0.64), SHOE)], (x, 0, 0.75), root)
    f["body"] = boxes("body", [((-0.33, 0.33, -0.16, 0.16, 0, 0.8), GREY),
                               ((-0.2, 0.2, -0.17, -0.16, 0.45, 0.8), SKIN),            # deep tank-top scoop
                               ((-0.33, -0.2, -0.165, 0.165, 0.55, 0.8), SKIN), ((0.2, 0.33, -0.165, 0.165, 0.55, 0.8), SKIN)],
                    (0, 0, 0.75), root)
    for side, x in (("L", -0.49), ("R", 0.49)):
        f["arm" + side] = boxes(f"arm{side}", [((-0.16, 0.16, -0.16, 0.16, -0.75, 0.0), SKIN),
                                               ((-0.17, 0.17, -0.17, 0.12, -0.42, -0.12), colmat((0.76, 0.52, 0.37)))],
                                (x, 0, 1.5), root)
    f["head"] = boxes("head", [((-0.25, 0.25, -0.25, 0.25, 0, 0.5), SKIN),
                               ((-0.27, 0.27, -0.27, 0.27, 0.4, 0.58), CAP), ((-0.2, 0.2, 0.27, 0.5, 0.4, 0.46), CAP),
                               ((-0.16, -0.06, -0.265, -0.25, 0.22, 0.29), DK), ((0.06, 0.16, -0.265, -0.25, 0.22, 0.29), DK),
                               ((-0.17, -0.05, -0.27, -0.25, 0.3, 0.33), HAIR), ((0.05, 0.17, -0.27, -0.25, 0.3, 0.33), HAIR),
                               ((-0.08, 0.08, -0.262, -0.25, 0.07, 0.1), colmat((0.55, 0.30, 0.22))),
                               ((-0.04, 0.04, -0.3, -0.25, 0.14, 0.24), colmat((0.74, 0.50, 0.36)))], (0, 0, 1.55), root)
    return f

SCALE = 1.15
BRO = bro_fig()
BRO["root"].scale = (SCALE,) * 3
G_POS = Vector((-1.6, 6.9, 0.0))
BRO["root"].location = G_POS
CTR = Vector((-1.6, 6.0, 0.0))            # counter in front of him
CT = 1.05                                 # counter top height
boxes("counter", [((-1.3, 1.3, -0.35, 0.35, 0.0, CT - 0.08), colmat((0.20, 0.22, 0.26), 0.6)),
                  ((-1.35, 1.35, -0.4, 0.4, CT - 0.08, CT), colmat((0.82, 0.80, 0.76), 0.35))], CTR)

def on_counter(x):
    return CTR + Vector((x, -0.05, CT))

tub = boxes("tub", [((-0.17, 0.17, -0.17, 0.17, 0.0, 0.42), colmat((0.95, 0.95, 0.95), 0.4)),
                    ((-0.175, 0.175, -0.175, 0.175, 0.12, 0.3), colmat((0.10, 0.30, 0.85), 0.5)),
                    ((-0.18, 0.18, -0.18, 0.18, 0.42, 0.48), colmat((0.08, 0.08, 0.1), 0.5))], AWAY)
EGG = colmat((0.96, 0.92, 0.84), 0.5)
eggs = boxes("eggs", [((-0.24, 0.24, -0.1, 0.1, 0.0, 0.05), colmat((0.75, 0.62, 0.45), 0.9))]
             + [(((k - 1.5) * 0.12 - 0.045, (k - 1.5) * 0.12 + 0.045, -0.04, 0.04, 0.05, 0.16), EGG) for k in range(4)], AWAY)
liver = boxes("liver", [((-0.24, 0.24, -0.16, 0.16, 0.0, 0.025), colmat((0.95, 0.95, 0.95), 0.4)),
                        ((-0.2, 0.18, -0.12, 0.12, 0.025, 0.08), colmat((0.35, 0.04, 0.05), 0.25)),
                        ((-0.12, 0.2, -0.1, 0.08, 0.08, 0.11), colmat((0.42, 0.06, 0.07), 0.25))], AWAY)
CAN_S, CAN_B = colmat((0.78, 0.80, 0.84), 0.25), colmat((0.10, 0.18, 0.55), 0.4)
can = boxes("can", [((-0.065, 0.065, -0.065, 0.065, -0.15, 0.15), CAN_S),
                    ((-0.068, 0.068, -0.068, 0.068, -0.08, 0.08), CAN_B)], AWAY)
alarm = B.area("alarm", Vector((-1.6, 4.0, 3.2)), Vector((-1.6, 6.9, 1.4)), 3.0, 0.0, (1.0, 0.1, 0.08))

# ------------------------------------------------------------------ lights, world, camera

world = bpy.data.worlds.new("bg")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.02, 0.03, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
ceil = B.area("ceil", Vector((-1.0, 4.5, ZC - 0.15)), Vector((-1.0, 4.5, 0)), 3.0, 200.0, (1.0, 0.86, 0.66), size_y=3.0)
key = B.area("key", Vector((-0.6, 3.0, 3.0)), Vector((-1.6, 6.6, 1.3)), 2.0, 120.0, (1.0, 0.95, 0.88))
win = B.area("win", Vector((4.0, 7.7, 2.0)), Vector((2.0, 3.0, 1.0)), 2.0, 60.0, (0.55, 0.65, 1.0))
gold = B.area("gold", Vector((0.5, 4.0, 3.2)), Vector((-1.6, 6.9, 1.5)), 2.5, 0.0, (1.0, 0.72, 0.3))
lamp_ld = bpy.data.lights.new("lamp", "POINT"); lamp_ld.color = (1.0, 0.75, 0.45); lamp_ld.shadow_soft_size = 0.3
lamp_l = B.link(bpy.data.objects.new("lamp_l", lamp_ld)); lamp_l.location = LAMP_POS + Vector((0, 0, 1.75))

cam = B.camera(lens=30, fstop=2.8)
B.render_settings(FPS, samples=32, motion_blur=0.3)

# ------------------------------------------------------------------ posing

def ramp_in(t, t0, d=0.35):
    return ramp(t, t0 - d / 2, t0 + d / 2)

def pop_in(ob, t, t0, where):
    u = ramp_in(t, t0, 0.3)
    if u <= 0.01:
        ob.location = AWAY
        return
    ob.location = where + Vector((0, 0, 0.12 * math.sin(math.pi * u)))
    ob.scale = (u,) * 3

def apply_state(t):
    door.rotation_euler = (0, 0, 0)
    shock = ramp_in(t, E["sees"], 0.25) * (1 - ramp_in(t, E["I"], 0.4))
    flex = ramp_in(t, E["J"], 0.4)
    hold = 1 - ramp_in(t, E["sugar"], 0.2) * (1 - ramp_in(t, E["I"] + 0.3, 0.4))   # can drops at "sugar", picked up again
    BRO["root"].location = G_POS + Vector((0, 0.12 * shock, 0))
    BRO["root"].rotation_euler = (0, 0, 0)
    breathe = 0.02 * math.sin(t * 1.8)
    BRO["body"].scale = (1.0 + breathe, 1.0, 1.0)
    # right arm holds the can up to read; both arms up for the flex
    read = hold * (1 - flex)
    BRO["armR"].rotation_euler = (-1.25 * read - 2.9 * flex, 0, 0.25 * read - 0.6 * flex)
    BRO["armL"].rotation_euler = (-0.2 * shock - 2.9 * flex + 0.03 * math.sin(t * 1.3), 0, 0.6 * flex)
    BRO["head"].rotation_euler = (0.32 * read - 0.25 * shock, 0, 0.12 * math.sin(t * 7) * shock)
    bpy.context.view_layer.update()
    if read > 0.5 or flex > 0.5:
        can.parent = BRO["armR"]
        can.location = (0, -0.1, -0.8)
        can.rotation_euler = (math.pi / 2 * (1 - flex), 0, 0)
        can.scale = (1, 1, 1)
    else:
        can.parent = None
        u = ramp_in(t, E["sugar"] + 0.15, 0.3)
        can.location = on_counter(0.55) + Vector((0, -0.1, 0.07 + 0.5 * (1 - u)))
        can.rotation_euler = (math.pi / 2, 0, 0.6)
        can.scale = (1, 1, 1)
    pop_in(tub, t, E["creatine"], on_counter(-0.75))
    pop_in(eggs, t, E["eggs"], on_counter(-0.2))
    pop_in(liver, t, E["liver"], on_counter(0.25))
    alarm.data.energy = (120.0 + 70.0 * math.sin(t * 14)) * shock
    gold.data.energy = 260.0 * flex
    dim = 1 - 0.5 * shock
    ceil.data.energy = 200.0 * dim
    lamp_ld.energy = 45.0 * dim
    loc, target, fstop, lens = camera_at(t)
    B.aim(cam, loc, target)
    cam.data.lens = lens
    cam.data.dof.focus_distance = (target - loc).length
    cam.data.dof.aperture_fstop = fstop
    cam.data.clip_start = 0.05
    cam.data.clip_end = 200

# ------------------------------------------------------------------ camera: each shot returns (camera location, look target)

def gp(z):
    return G_POS + Vector((0, 0, z))

def shot_hook(t):
    u = t / max(1.0, E["B"])
    tg = gp(1.5)
    return tg + Vector((0.8 - 0.2 * u, -4.6 + 0.4 * u, 0.3)), tg
def shot_counter(t):
    u = t - E["B"]
    tg = on_counter(-0.2) + Vector((0, 0, 0.2))
    return tg + Vector((0.6 - 0.04 * u, -2.4, 0.8)), tg
def shot_can(t):
    u = t - E["D"]
    tg = gp(1.85) + Vector((0.3, -0.4, 0))
    return tg + Vector((0.9 - 0.05 * u, -2.2 + 0.05 * u, 0.1)), tg
def shot_wide(t):
    u = t - E["F"]
    return Vector((0.8 - 0.06 * u, 2.6, 1.9)), gp(1.3)
def shot_face(t):
    u = t - E["G"]
    tg = gp(2.0)
    return tg + Vector((0.2, -1.8 + 0.12 * u, 0.0)), tg
def shot_shock(t):
    u = t - E["H"]
    tg = gp(1.6)
    return tg + Vector((-0.3, -3.2 + 0.05 * u, 0.2)), tg
def shot_flex(t):
    u = t - E["J"]
    tg = gp(1.7)
    return tg + Vector((0.4 + 0.05 * u, -3.9 - 0.15 * u, -0.6)), tg

SHOTS = [(shot_hook, None), (shot_counter, (E["B"] - 0.25, E["B"] + 0.15)), (shot_can, (E["D"] - 0.25, E["D"] + 0.15)),
         (shot_wide, (E["F"] - 0.25, E["F"] + 0.15)), (shot_face, (E["G"] - 0.2, E["G"] + 0.1)),
         (shot_shock, (E["H"] - 0.2, E["H"] + 0.1)), (shot_wide, (E["I"] - 0.25, E["I"] + 0.15)),
         (shot_flex, (E["J"] - 0.25, E["J"] + 0.15))]

LENS = {shot_wide: 26.0, shot_face: 35.0, shot_counter: 32.0}

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
    names = ("head", "can", "tub", "eggs", "liver")
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        pts = {
            "head": BRO["head"].matrix_world @ Vector((0, 0, 0.62)),
            "can": can.matrix_world @ Vector((0, 0, 0)),
            "tub": on_counter(-0.75) + Vector((0, 0, 0.5)),
            "eggs": on_counter(-0.2) + Vector((0, 0, 0.18)),
            "liver": on_counter(0.25) + Vector((0, 0, 0.12)),
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
