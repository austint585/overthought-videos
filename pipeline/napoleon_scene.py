"""Blender scene for 'Napoleon wakes up in 2026': a voxel museum gallery (parquet floor, framed paintings, ceiling light
panels), a red display plinth where Napoleon lies as an exhibit and gets up, a glass case with his bicorne hat, a height
chart on the wall, and disco lights for the ABBA beat. Built in code and timed to the narration (same voxel method as
pharmacy_scene.py).

blender -b --factory-startup -P pharmacy_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
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
rng = random.Random(7)
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

MATS = {
    "floor": pixel_mat("floor", [(0.42, 0.24, 0.12), (0.48, 0.28, 0.14), (0.38, 0.21, 0.10), (0.45, 0.26, 0.13)], rough=0.4,
                       lines=((1, 2, 1), (0.22, 0.12, 0.06))),
    "wall": pixel_mat("wall", [(0.86, 0.80, 0.68), (0.89, 0.83, 0.71), (0.83, 0.77, 0.65)]),
    "trim": pixel_mat("trim", [(0.55, 0.12, 0.12), (0.60, 0.14, 0.13), (0.50, 0.10, 0.10)]),
    "ceiling": pixel_mat("ceiling", [(0.92, 0.90, 0.86), (0.95, 0.93, 0.89)], lines=((1, 1, 1), (0.6, 0.6, 0.6))),
    "panel": solid("panel", (1.0, 0.97, 0.9), emit=5.0),
}

# ------------------------------------------------------------------ voxel gallery: one long room

GRID = {}

def fill(i0, i1, j0, j1, k0, k1, mat):
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            for k in range(k0, k1 + 1):
                if mat is None:
                    GRID.pop((i, j, k), None)
                else:
                    GRID[(i, j, k)] = mat

ZC = 5
fill(-6, 5, -6, 13, -1, -1, "floor")
fill(-7, -7, -6, 13, 0, ZC - 1, "wall")
fill(6, 6, -6, 13, 0, ZC - 1, "wall")
fill(-7, 6, 13, 13, 0, ZC - 1, "wall")
fill(-7, 6, -6, 13, ZC, ZC, "ceiling")
fill(-7, -7, -6, 13, 0, 0, "trim")                 # dark red skirting along the walls
fill(6, 6, -6, 13, 0, 0, "trim")
fill(-7, 6, 13, 13, 0, 0, "trim")
for j in (-2, 2, 6, 10):
    fill(-1, 0, j, j + 1, ZC, ZC, "panel")

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

voxel_mesh("store", GRID)

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

voxel_mesh("gallery", GRID)

_mat_cache = {}
def colmat(color, rough=0.55, emit=0.0, metallic=0.0):
    key = (color, rough, emit, metallic)
    if key not in _mat_cache:
        _mat_cache[key] = solid(f"c{len(_mat_cache)}", color, rough, emit, metallic=metallic)
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

GOLDM = colmat((0.95, 0.65, 0.18), 0.3, metallic=1.0)
VELVET = colmat((0.45, 0.03, 0.05), 0.9)
BLACK = colmat((0.02, 0.02, 0.025), 0.5)

# paintings: gold frames with blocky canvases (landscapes and portraits in voxel strokes)
def painting(name, x, y, z, w, h, face, palette):
    """face +1: hangs on the left wall facing +x; -1: right wall facing -x; 0: back wall facing -y."""
    parts = [((-w / 2 - 0.1, w / 2 + 0.1, -0.06, 0.0, -h / 2 - 0.1, h / 2 + 0.1), GOLDM)]
    n = 6
    for a in range(n):
        for b in range(n):
            col = palette[rng.randrange(len(palette))] if b < n - 2 or a % 2 else palette[0]
            parts.append(((-w / 2 + w * a / n, -w / 2 + w * (a + 1) / n, -0.08, -0.06,
                           -h / 2 + h * b / n, -h / 2 + h * (b + 1) / n), colmat(col, 0.8)))
    ob = boxes(name, parts, (x, y, z))
    ob.rotation_euler = (0, 0, {1: -math.pi / 2, -1: math.pi / 2, 0: 0.0}[face])
    return ob

LAND = [(0.25, 0.45, 0.65), (0.35, 0.55, 0.75), (0.25, 0.45, 0.2), (0.35, 0.55, 0.25), (0.6, 0.5, 0.3)]
DARKP = [(0.12, 0.10, 0.08), (0.20, 0.15, 0.10), (0.35, 0.22, 0.12), (0.15, 0.2, 0.35)]
painting("p1", -5.98, 1.0, 2.3, 1.6, 1.1, 1, LAND)
painting("p2", -5.98, 4.6, 2.4, 1.0, 1.4, 1, DARKP)
painting("p3", 5.98, 0.5, 2.3, 1.4, 1.0, -1, LAND)
painting("p4", 5.98, 4.0, 2.4, 1.2, 1.5, -1, DARKP)
painting("p5", 5.98, 10.0, 2.3, 1.8, 1.2, -1, LAND)
painting("p6", 0.0, 12.98, 2.6, 3.0, 2.0, 0, DARKP + [(0.1, 0.15, 0.45), (0.8, 0.8, 0.8)])

# the exhibit plinth Napoleon wakes up on, with rope posts
PL = Vector((0.0, 4.0, 0.0))
boxes("plinth", [((-0.9, 0.9, -1.4, 1.4, 0.0, 0.55), VELVET), ((-0.95, 0.95, -1.45, 1.45, 0.0, 0.08), GOLDM),
                 ((-0.92, 0.92, -1.42, 1.42, 0.55, 0.6), GOLDM)], PL)
for dx, dy in ((-1.5, -2.0), (1.5, -2.0), (-1.5, 2.0), (1.5, 2.0)):
    boxes(f"post{dx}{dy}", [((-0.05, 0.05, -0.05, 0.05, 0.0, 0.9), GOLDM), ((-0.12, 0.12, -0.12, 0.12, 0.0, 0.05), GOLDM)],
          PL + Vector((dx, dy, 0)))
boxes("ropes", [((-1.5, 1.5, -2.03, -1.97, 0.78, 0.84), VELVET), ((-1.53, -1.47, -2.0, 2.0, 0.78, 0.84), VELVET),
                ((1.47, 1.53, -2.0, 2.0, 0.78, 0.84), VELVET)], PL)

def bicorne(name, origin, parent=None, s=1.0):
    q = lambda a, b, c, d, e, f: (a * s, b * s, c * s, d * s, e * s, f * s)
    return boxes(name, [(q(-0.42, 0.42, -0.1, 0.1, 0.0, 0.16), BLACK), (q(-0.32, 0.32, -0.09, 0.09, 0.16, 0.26), BLACK),
                        (q(-0.18, 0.18, -0.08, 0.08, 0.26, 0.33), BLACK), (q(-0.44, 0.44, -0.11, 0.11, 0.0, 0.03), GOLDM),
                        (q(0.14, 0.24, -0.115, -0.1, 0.1, 0.2), colmat((0.1, 0.2, 0.7), 0.6)),
                        (q(0.165, 0.215, -0.12, -0.115, 0.125, 0.175), colmat((0.95, 0.95, 0.95), 0.6)),
                        (q(0.18, 0.2, -0.125, -0.12, 0.14, 0.16), colmat((0.8, 0.05, 0.05), 0.6))], origin, parent)

# the hat case: white pedestal, brass edges, the hat on a cushion, a small placard
CASE = Vector((2.7, 7.5, 0.0))
boxes("pedestal", [((-0.45, 0.45, -0.45, 0.45, 0.0, 1.1), colmat((0.93, 0.92, 0.9), 0.5)),
                   ((-0.32, 0.32, -0.32, 0.32, 1.1, 1.18), VELVET)] +
      [((x - 0.02, x + 0.02, y - 0.02, y + 0.02, 1.1, 1.85), GOLDM) for x in (-0.45, 0.45) for y in (-0.45, 0.45)] +
      [((-0.47, 0.47, -0.47, 0.47, 1.85, 1.9), GOLDM)], CASE)
HAT = bicorne("hat", CASE + Vector((0, 0, 1.18)), s=1.15)
HAT.rotation_euler = (0, 0, 0.5)
boxes("placard", [((-0.25, 0.25, -0.02, 0.02, 0.0, 0.18), colmat((0.95, 0.9, 0.75), 0.6))], CASE + Vector((0, -0.47, 0.8)))

# height chart on the left wall: white strip, ticks every 10 cm, red line at 1.57 m (5 ft 2 in) and green at 1.69 m
CH = Vector((-5.97, 9.6, 0.0))
chart = [((0.0, 0.03, -0.35, 0.35, 0.0, 2.2), colmat((0.95, 0.95, 0.93), 0.7))]
for k in range(22):
    z = 0.1 * (k + 1)
    ln = 0.3 if k % 5 == 4 else 0.15
    chart.append(((0.03, 0.04, -0.35, -0.35 + ln, z - 0.008, z + 0.008), BLACK))
chart.append(((0.03, 0.045, -0.35, 0.35, 1.565, 1.585), colmat((0.9, 0.05, 0.05), 0.5, emit=0.6)))
chart.append(((0.03, 0.045, -0.35, 0.35, 1.685, 1.705), colmat((0.1, 0.8, 0.2), 0.5, emit=0.6)))
boxes("chart", chart, CH)

# disco ball for the ABBA beat (hidden until then)
DISCO = boxes("disco", [((-0.25, 0.25, -0.25, 0.25, -0.25, 0.25), colmat((0.8, 0.8, 0.85), 0.05, metallic=1.0)),
                        ((-0.18, 0.18, -0.3, 0.3, -0.18, 0.18), colmat((0.9, 0.9, 0.95), 0.05, metallic=1.0)),
                        ((-0.3, 0.3, -0.18, 0.18, -0.18, 0.18), colmat((0.9, 0.9, 0.95), 0.05, metallic=1.0)),
                        ((-0.02, 0.02, -0.02, 0.02, 0.25, 1.0), colmat((0.5, 0.5, 0.5), 0.4))], AWAY)

# ------------------------------------------------------------------ Napoleon

def person(name, coat, pants, skin, hair):
    root = B.link(bpy.data.objects.new(name, None))
    S, P, Sk, H = colmat(coat, 0.7), colmat(pants, 0.7), colmat(skin), colmat(hair, 0.8)
    D = colmat((0.03, 0.02, 0.02), 0.4)
    f = {"root": root}
    for side, x in (("L", -0.125), ("R", 0.125)):
        f["leg" + side] = boxes(f"{name}_leg{side}", [((-0.125, 0.125, -0.125, 0.125, -0.75, 0.0), P),
                                                      ((-0.135, 0.135, -0.135, 0.135, -0.75, -0.35), BLACK),
                                                      ((-0.14, 0.14, -0.19, 0.135, -0.75, -0.68), BLACK)], (x, 0, 0.75), root)
    f["body"] = boxes(f"{name}_body", [((-0.25, 0.25, -0.125, 0.125, 0, 0.75), S),
                                       ((-0.11, 0.11, -0.13, -0.125, 0.05, 0.62), colmat((0.95, 0.95, 0.92), 0.7)),   # white vest
                                       ((-0.25, 0.25, -0.13, 0.13, 0.0, 0.07), colmat((0.95, 0.95, 0.92), 0.7)),
                                       ((-0.16, 0.16, -0.135, 0.135, 0.66, 0.75), colmat((0.7, 0.05, 0.05), 0.6)),  # red collar
                                       ((-0.36, -0.2, -0.13, 0.13, 0.72, 0.8), GOLDM), ((0.2, 0.36, -0.13, 0.13, 0.72, 0.8), GOLDM)],
                       (0, 0, 0.75), root)
    for side, x in (("L", -0.375), ("R", 0.375)):
        f["arm" + side] = boxes(f"{name}_arm{side}", [((-0.125, 0.125, -0.125, 0.125, -0.55, 0.0), S),
                                                      ((-0.13, 0.13, -0.13, 0.13, -0.58, -0.5), colmat((0.95, 0.95, 0.92), 0.7)),
                                                      ((-0.11, 0.11, -0.11, 0.11, -0.76, -0.58), Sk)], (x, 0, 1.5), root)
    hp = [((-0.25, 0.25, -0.25, 0.25, 0, 0.5), Sk), ((-0.27, 0.27, -0.27, 0.27, 0.42, 0.52), H),
          ((-0.27, 0.27, 0.05, 0.28, 0.15, 0.5), H), ((-0.12, 0.0, -0.27, -0.25, 0.4, 0.48), H),
          ((-0.16, -0.06, -0.265, -0.25, 0.22, 0.29), D), ((0.06, 0.16, -0.265, -0.25, 0.22, 0.29), D),
          ((-0.17, -0.05, -0.266, -0.25, 0.31, 0.33), H), ((0.05, 0.17, -0.266, -0.25, 0.31, 0.33), H),
          ((-0.08, 0.08, -0.262, -0.25, 0.07, 0.1), colmat((0.55, 0.30, 0.22)))]
    f["head"] = boxes(f"{name}_head", hp, (0, 0, 1.5), root)
    f["hat"] = bicorne(f"{name}_hat", (0, 0, 0.44), f["head"])
    f["phone"] = boxes(f"{name}_phone", [((-0.07, 0.07, -0.015, 0.015, -0.12, 0.12), BLACK),
                                         ((-0.06, 0.06, -0.02, -0.015, -0.11, 0.11), colmat((0.6, 0.8, 1.0), 0.3, emit=3.0))],
                       (0, -0.12, -0.8), f["armR"])
    return f

NAP = person("nap", (0.06, 0.10, 0.32), (0.93, 0.92, 0.88), (0.90, 0.72, 0.60), (0.12, 0.08, 0.05))

# ------------------------------------------------------------------ lights, world, camera

world = bpy.data.worlds.new("bg")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.045, 0.04, 1)
for k, j in enumerate((-1.5, 2.5, 6.5, 10.5)):
    B.area(f"panel{k}", Vector((0.0, j, ZC - 0.05)), Vector((0.0, j, 0)), 1.8, 200.0, (1.0, 0.95, 0.85))
key = B.area("key", Vector((2.5, -1.0, 3.2)), Vector((0.0, 5.0, 1.0)), 2.5, 160.0, (1.0, 0.92, 0.8))
spot_pl = B.area("spotpl", Vector((0.0, 3.0, 4.6)), PL + Vector((0, 0, 0.8)), 1.0, 120.0, (1.0, 0.85, 0.6))
spot_hat = B.area("spothat", CASE + Vector((-0.8, -0.6, 3.6)), CASE + Vector((0, 0, 1.3)), 0.6, 60.0, (1.0, 0.9, 0.7))
spot_chart = B.area("spotch", Vector((-3.5, 8.5, 4.2)), CH + Vector((0, 0, 1.2)), 1.2, 90.0, (1.0, 0.95, 0.85))
DISCO_L = [B.area(f"dl{k}", Vector((3.0 * math.cos(k * 2.1), 7.0 + 3.0 * math.sin(k * 2.1), 4.5)), Vector((0, 7.5, 0)),
                  1.5, 0.0, c) for k, c in enumerate(((1.0, 0.1, 0.6), (0.1, 0.4, 1.0), (1.0, 0.8, 0.1)))]

cam = B.camera(lens=30, fstop=2.8)
B.render_settings(FPS, samples=32, motion_blur=0.3)

# ------------------------------------------------------------------ motion

def pose(f, walk=0.0, phase=0.0, arms=None, head_turn=0.0, head_nod=0.0):
    s = math.sin(phase) * walk
    f["legL"].rotation_euler = (s * 0.8, 0, 0)
    f["legR"].rotation_euler = (-s * 0.8, 0, 0)
    aL, aR = arms if arms else ((-s * 0.7, 0, 0), (s * 0.7, 0, 0))
    f["armL"].rotation_euler = aL
    f["armR"].rotation_euler = aR
    f["head"].rotation_euler = (head_nod, 0, head_turn)

def ramp_in(t, t0, d=0.35):
    return ramp(t, t0 - d / 2, t0 + d / 2)

def face_angle(dx, dy):
    """Rotation about z so the figure (built facing -y) faces (dx, dy)."""
    return math.atan2(dx, -dy)

P_LIE = PL + Vector((0.0, -0.9, 0.6))
P_FLOOR = Vector((0.9, 2.2, 0.0))
P_CASE = CASE + Vector((-0.95, 0.0, 0.0))
P_CHART = CH + Vector((0.45, -0.7, 0.0))
P_CENTER = Vector((0.0, 7.6, 0.0))

def path(t, keys):
    """keys: list of (t, Vector). Linear between keys with smoothed ends; returns (pos, moving, heading)."""
    if t <= keys[0][0]:
        return keys[0][1], False, None
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t < t1:
            u = smooth01((t - t0) / (t1 - t0))
            d = b - a
            moving = d.length > 0.05
            return a.lerp(b, u), moving, (d.x, d.y) if moving else None
    return keys[-1][1], False, None

def nap_state(t):
    keys = [(E["C"] - 0.1, P_LIE), (E["C"] + 0.5, P_FLOOR), (E["C"] + 2.0, P_CASE), (E["looks"] - 0.2, P_CASE),
            (E["looks"] + 1.6, P_CHART), (E["J"] - 0.2, P_CHART), (E["J"] + 1.3, P_CENTER)]
    p, moving, head = path(t, keys)
    if E["C"] - 0.1 < t < E["C"] + 0.5:                         # hop down off the plinth
        u = (t - E["C"] + 0.1) / 0.6
        p = p + Vector((0, 0, 0.35 * math.sin(math.pi * u)))
    rise = ramp(t, E["wakes"] + 0.1, E["wakes"] + 1.0)
    lying = t < E["C"] - 0.1
    R = NAP["root"]
    R.location = p
    if lying:
        R.rotation_euler = (-math.pi / 2 * (1 - rise), 0, 0)
    elif moving:
        R.rotation_euler = (0, 0, face_angle(*head))
    elif t < E["looks"] - 0.2:
        R.rotation_euler = (0, 0, face_angle(1, 0.15))          # looking at the hat case
    elif t < E["J"] - 0.2:
        R.rotation_euler = (0, 0, face_angle(1, -0.6))          # back to the chart, half toward the room
    else:
        R.rotation_euler = (0, 0, face_angle(0.2, -1))          # toward the camera
    walk = 1.0 if moving else 0.0
    head_turn = 0.0
    if E["B"] < t < E["C"] - 0.1:
        head_turn = 0.6 * math.sin((t - E["B"]) * 2.2)          # looks around the gallery
    phone_u = ramp_in(t, E["looks"] + 1.7, 0.4) * (1 - ramp_in(t, E["closes"] + 0.15, 0.3))
    hand_in_coat = ((0.0, 0, 0), (-1.0, 0, 0.9))               # the portrait pose
    if phone_u > 0.02:
        arms = ((0.0, 0, 0), (-1.3 * phone_u, 0, 0.35 * phone_u))
    elif not moving and t > E["C"] + 2.0:
        arms = hand_in_coat
    else:
        arms = None
    nod = 0.0
    if E["looks"] + 1.7 < t < E["closes"]:
        nod = 0.35 * phone_u                                    # reading the phone
    if E["tiny"] < t < E["H"]:
        nod = 0.35 + 0.15 * ramp_in(t, E["complex"], 0.4)
    if E["moscow"] < t < E["closes"] + 0.4:                       # shiver
        R.rotation_euler.z += 0.05 * math.sin(t * 60)
    if t > E["abba"] and t < E["K"]:                             # reluctant head bob
        nod = 0.12 * math.sin(t * 10)
        arms = ((0.0, 0, -0.3 - 0.2 * math.sin(t * 5)), (0.0, 0, 0.3 + 0.2 * math.sin(t * 5)))
    slump = ramp_in(t, E["twice"] - 0.1, 0.5)
    if slump > 0:
        nod = 0.55 * slump
        arms = ((0.15 * slump, 0, -0.1 * slump), (0.15 * slump, 0, 0.1 * slump))
    pose(NAP, walk=walk, phase=t * 7.5, arms=arms, head_turn=head_turn, head_nod=nod)
    if slump > 0:
        R.location = p - Vector((0, 0, 0.06 * slump))
    NAP["phone"].scale = (1, 1, 1) if phone_u > 0.02 else (0, 0, 0)

def apply_state(t):
    nap_state(t)
    d = ramp_in(t, E["abba"], 0.3) * (1 - ramp_in(t, E["K"], 0.3))
    DISCO.location = Vector((0.3, 9.4, 3.0)) if d > 0.01 else AWAY
    DISCO.rotation_euler = (0, 0, t * 1.5)
    for k, L in enumerate(DISCO_L):
        L.data.energy = 1500.0 * d * (0.6 + 0.4 * math.sin(t * 8 + k * 2.1))
    dim = 1.0 - 0.6 * d - 0.4 * ramp_in(t, E["K"], 0.4)
    for ob in bpy.data.objects:
        if ob.name.startswith("panel"):
            ob.data.energy = 200.0 * dim
    key.data.energy = 160.0 * dim
    loc, target, fstop, lens = camera_at(t)
    B.aim(cam, loc, target)
    cam.data.lens = lens
    cam.data.dof.focus_distance = (target - loc).length
    cam.data.dof.aperture_fstop = fstop
    cam.data.clip_start = 0.05
    cam.data.clip_end = 200

# ------------------------------------------------------------------ camera

def nap_at(z):
    return NAP["root"].location + Vector((0, 0, z))

def shot_hook(t):          # low three-quarter view of the exhibit, Napoleon lying on the plinth, then rising
    rise = ramp(t, E["wakes"] + 0.1, E["wakes"] + 1.0)
    return Vector((2.3 - 0.05 * t, 0.7, 1.5 + 0.2 * rise)), PL + Vector((0, -0.6, 0.8 + 1.0 * rise))
def shot_look(t):          # closer on him standing on the plinth, the gallery behind
    u = t - E["B"]
    tg = nap_at(1.2)
    return tg + Vector((1.2 - 0.05 * u, -2.6, 0.2)), tg
def shot_follow(t):        # wide, following him to the hat case
    tg = nap_at(0.9)
    return tg + Vector((-1.6, -3.6, 1.2)), tg
def shot_hat(t):           # the hat case, Napoleon at its side
    u = t - E["D"]
    return CASE + Vector((-0.7 + 0.04 * u, -3.3 + 0.06 * u, 2.0)), CASE + Vector((-0.45, 0.0, 1.25))
def shot_chart(t):         # side-on to the wall: him next to the height chart
    u = t - E["looks"]
    tg = P_CHART + Vector((-0.2, 0.3, 1.0))
    return tg + Vector((3.4 - 0.03 * u, -2.4, 0.6)), tg
def shot_close(t):         # close on his face for the cartoon and complex beats
    u = t - E["G"]
    tg = nap_at(1.3)
    return tg + Vector((1.6 - 0.03 * u, -1.6, 0.3)), tg
def shot_disco(t):
    u = t - E["J"]
    tg = P_CENTER + Vector((0, 0, 1.0))
    return tg + Vector((0.5, -3.4 + 0.1 * u, 0.4)), tg
def shot_end(t):           # high angle, slumped in the dark gallery
    u = t - E["K"]
    tg = P_CENTER + Vector((0, 0, 1.1))
    return tg + Vector((0.8, -2.4 - 0.15 * u, 2.2)), tg

SHOTS = [(shot_hook, None), (shot_look, (E["B"] - 0.25, E["B"] + 0.15)), (shot_follow, (E["C"] - 0.25, E["C"] + 0.15)),
         (shot_hat, (E["D"] - 0.25, E["D"] + 0.15)), (shot_chart, (E["looks"] + 0.6, E["looks"] + 1.2)),
         (shot_close, (E["G"] - 0.25, E["G"] + 0.15)), (shot_chart, (E["H"] - 0.25, E["H"] + 0.15)),
         (shot_disco, (E["J"] + 0.9, E["J"] + 1.4)), (shot_end, (E["K"] - 0.2, E["K"] + 0.2))]
LENS = {shot_follow: 26.0, shot_close: 32.0, shot_end: 28.0, shot_disco: 28.0, shot_chart: 26.0}

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
    names = ("hero", "hat")
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        pts = {
            "hero": NAP["head"].matrix_world @ Vector((0, 0, 0.8)),
            "hat": CASE + Vector((0, 0, 1.6)),
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
