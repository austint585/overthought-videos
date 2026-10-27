"""Blender scene for 'The 8 a.m. steak guy': a voxel lecture hall (tiered rows, projector screen, fluorescent strips),
a class of blocky students, a professor, and the guy in the back row with a tomahawk ribeye and a bottle of ranch.
Built in code and timed to the narration.

blender -b --factory-startup -P steak_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Always writes out_dir/anchors.json: screen positions of label points for every frame.
"""
import json, math, os, random, sys
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import bkit as B
import steak_anim as SA

argv = sys.argv[sys.argv.index("--") + 1:]
TIMING, OUT, MODE = argv[0], argv[1], argv[2]
T = json.load(open(TIMING))
FPS, DUR, E = T["fps"], T["duration"], T["events"]
NF = int(round(DUR * FPS))
os.makedirs(OUT, exist_ok=True)
B.clear_scene()
scene = B.scene
rng = random.Random(8)
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

def shade(c, f):
    return tuple(min(1.0, x * f) for x in c)

MATS = {
    "carpet": pixel_mat("carpet", [(0.07, 0.08, 0.11), (0.09, 0.10, 0.13), (0.06, 0.06, 0.09), (0.10, 0.11, 0.15)]),
    "riser": pixel_mat("riser", [(0.16, 0.16, 0.17), (0.19, 0.19, 0.20), (0.14, 0.14, 0.15)]),
    "stage": pixel_mat("stage", [(0.30, 0.20, 0.11), (0.35, 0.24, 0.13), (0.27, 0.18, 0.10)], lines=((1, 0.5, 1), (0.16, 0.10, 0.05))),
    "wall": pixel_mat("wall", [(0.52, 0.53, 0.55), (0.56, 0.57, 0.59), (0.49, 0.50, 0.52)], lines=((0.5, 1, 1), (0.40, 0.41, 0.43))),
    "panel": pixel_mat("panel", [(0.28, 0.20, 0.13), (0.32, 0.23, 0.15), (0.25, 0.18, 0.11)], lines=((1, 1, 0.5), (0.15, 0.10, 0.06))),
    "ceiling": pixel_mat("ceiling", [(0.30, 0.31, 0.33), (0.33, 0.34, 0.36)], lines=((0.5, 0.5, 1), (0.20, 0.20, 0.22))),
    "strip": solid("strip", (1.0, 0.97, 0.90), emit=9.0),
    "screen": pixel_mat("screen", [(0.80, 0.86, 0.95), (0.84, 0.89, 0.97)], rough=0.4, lines=((0, 0, 1.2), (0.25, 0.30, 0.45)), emit=1.6),
    "door": pixel_mat("door", [(0.36, 0.22, 0.10), (0.40, 0.25, 0.12)], lines=((1, 1, 2), (0.20, 0.11, 0.05))),
    "hall": solid("hall", (1.0, 0.92, 0.78), emit=4.0),
}

# ------------------------------------------------------------------ voxel hall

GRID = {}

def fill(i0, i1, j0, j1, k0, k1, mat):
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            for k in range(k0, k1 + 1):
                if mat is None:
                    GRID.pop((i, j, k), None)
                else:
                    GRID[(i, j, k)] = mat

X0, X1, Y0, Y1, ZC = -12, 11, -10, 17, 13       # inner hall: x -12..11, y -10..17, ceiling at z 13
for i in range(X0, X1 + 1):
    for j in range(Y0, Y1 + 1):
        top = int(SA.floor_z(j + 0.5))
        mat = "stage" if j < 0 else "carpet"
        GRID[(i, j, top - 1)] = mat
        for k in range(-2, top - 1):
            GRID[(i, j, k)] = "riser"
# side walls, front wall, back wall, ceiling
fill(X0 - 1, X0 - 1, Y0, Y1 + 1, -1, ZC - 1, "wall")
fill(X1 + 1, X1 + 1, Y0, Y1 + 1, -1, ZC - 1, "wall")
fill(X0 - 1, X1 + 1, Y0 - 1, Y0 - 1, -1, ZC - 1, "panel")
fill(X0 - 1, X1 + 1, Y1 + 1, Y1 + 1, -1, ZC - 1, "wall")
fill(X0 - 1, X1 + 1, Y0 - 1, Y1 + 1, ZC, ZC, "ceiling")
# wood wainscot along the side walls
for j in range(Y0, Y1 + 1):
    z = int(SA.floor_z(j + 0.5))
    for i in (X0 - 1, X1 + 1):
        GRID[(i, j, z)] = "panel"
# doorway in the back wall, right side (the hall light behind it)
fill(9, 10, Y1 + 1, Y1 + 1, 8, 10, None)
fill(9, 10, Y1 + 2, Y1 + 2, 8, 10, "hall")
fill(8, 11, Y1 + 2, Y1 + 2, 7, 7, "riser")

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

voxel_mesh("hall", GRID)

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

DESK = colmat((0.62, 0.48, 0.30), 0.5)
DESK_EDGE = colmat((0.20, 0.13, 0.07), 0.6)
SEAT = colmat((0.06, 0.06, 0.07), 0.6)
SEAT_TRIM = colmat((0.55, 0.05, 0.04), 0.6)
for r in range(SA.N_ROWS):
    y0 = SA.ROW_DEPTH * r
    z = r + 1.0
    parts = [((-9.3, 9.3, 0.15, 0.62, 0.74, 0.80), DESK), ((-9.3, 9.3, 0.15, 0.22, 0.0, 0.74), DESK_EDGE)]
    for x in SA.SEAT_X:
        parts += [((x - 0.5, x + 0.5, 1.05, 1.65, 0.38, 0.46), SEAT), ((x - 0.5, x + 0.5, 1.6, 1.72, 0.46, 1.15), SEAT),
                  ((x - 0.5, x + 0.5, 1.6, 1.74, 1.05, 1.15), SEAT_TRIM), ((x - 0.06, x + 0.06, 1.2, 1.5, 0.0, 0.38), SEAT)]
    boxes(f"row{r}", parts, (0, y0, z))

# projector screen, podium, ceiling light strips, projector
boxes("screen", [((-7.5, 7.5, 0.0, 0.08, 3.0, 9.5), MATS["screen"])], (0, Y0 + 0.02, 0))
boxes("screen_frame", [((-7.7, 7.7, -0.02, 0.04, 2.8, 9.7), colmat((0.03, 0.03, 0.035), 0.5))], (0, Y0 + 0.02, 0))
boxes("podium", [((-0.6, 0.6, -0.4, 0.4, 0.0, 1.15), colmat((0.30, 0.20, 0.11), 0.5)),
                 ((-0.7, 0.7, -0.5, 0.45, 1.15, 1.22), colmat((0.22, 0.14, 0.07), 0.5)),
                 ((-0.25, 0.25, -0.3, 0.05, 1.22, 1.26), colmat((0.5, 0.7, 1.0), 0.3, emit=2.0))], (-3.2, -4.0, 0))
strips = []
for x in (-7.5, -2.5, 2.5, 7.5):
    strips.append(((x - 0.25, x + 0.25, Y0 + 1, Y1 - 0.5, ZC - 0.08, ZC), MATS["strip"]))
boxes("strips", strips, (0, 0, 0))
boxes("projector", [((-0.6, 0.6, -0.5, 0.5, -0.45, 0.0), colmat((0.08, 0.08, 0.09), 0.4)),
                    ((-0.18, 0.18, -0.56, -0.5, -0.36, -0.1), colmat((0.8, 0.9, 1.0), 0.2, emit=6.0))], (0, 4.0, ZC))
door = boxes("door", [((0.0, 2.0, -0.08, 0.0, 0.0, 3.0), MATS["door"]),
                      ((1.7, 1.82, -0.2, -0.08, 1.3, 1.45), colmat((0.7, 0.7, 0.72), 0.3))], (9.0, Y1 + 1.0, 8.0))

# ------------------------------------------------------------------ characters

SKIN_TONES = [(0.80, 0.52, 0.36), (0.55, 0.36, 0.24), (0.88, 0.66, 0.50), (0.38, 0.24, 0.15), (0.72, 0.50, 0.33)]
def figure(name, hair, shirt, pants, skin, long_hair=False, cap=None, hood=False, glasses=False):
    root = B.link(bpy.data.objects.new(name, None))
    S, H, Sh, P, D = colmat(skin), colmat(hair, 0.7), colmat(shirt), colmat(pants, 0.7), colmat((0.03, 0.02, 0.02), 0.4)
    Shoe = colmat((0.05, 0.05, 0.06), 0.5)
    f = {"root": root}
    for side, x in (("L", -0.125), ("R", 0.125)):
        f["leg" + side] = boxes(f"{name}_leg{side}", [((-0.125, 0.125, -0.125, 0.125, -0.75, 0.0), P),
                                                       ((-0.13, 0.13, -0.135, 0.13, -0.75, -0.62), Shoe)], (x, 0, 0.75), root)
    body = [((-0.25, 0.25, -0.125, 0.125, 0, 0.75), Sh)]
    if hood:
        body += [((-0.22, 0.22, 0.12, 0.2, 0.45, 0.75), Sh)]
    f["body"] = boxes(f"{name}_body", body, (0, 0, 0.75), root)
    for side, x in (("L", -0.375), ("R", 0.375)):
        f["arm" + side] = boxes(f"{name}_arm{side}", [((-0.125, 0.125, -0.125, 0.125, -0.25, 0.0), Sh),
                                                       ((-0.12, 0.12, -0.12, 0.12, -0.75, -0.25), Sh if hood else S),
                                                       ((-0.11, 0.11, -0.11, 0.11, -0.82, -0.68), S)], (x, 0, 1.5), root)
    head = [((-0.25, 0.25, -0.25, 0.25, 0, 0.5), S), ((-0.27, 0.27, -0.27, 0.27, 0.38, 0.55), H),
            ((-0.16, -0.06, -0.265, -0.25, 0.2, 0.28), D), ((0.06, 0.16, -0.265, -0.25, 0.2, 0.28), D),
            ((-0.07, 0.07, -0.262, -0.25, 0.07, 0.1), colmat(shade(skin, 0.6)))]
    if long_hair:
        head += [((-0.27, 0.27, 0.1, 0.29, -0.5, 0.5), H), ((-0.29, -0.2, -0.2, 0.27, -0.35, 0.45), H),
                 ((0.2, 0.29, -0.2, 0.27, -0.35, 0.45), H)]
    else:
        head += [((-0.27, 0.27, 0.08, 0.28, 0.12, 0.5), H)]
    if cap:
        C = colmat(cap, 0.6)
        head += [((-0.28, 0.28, -0.28, 0.28, 0.48, 0.62), C), ((-0.22, 0.22, 0.27, 0.55, 0.48, 0.52), C)]   # worn backwards
    if glasses:
        head += [((-0.2, 0.2, -0.28, -0.25, 0.22, 0.25), colmat((0.02, 0.02, 0.02), 0.3))]
    f["head"] = boxes(f"{name}_head", head, (0, 0, 1.5), root)
    return f

def hide(f):
    f["root"].location = AWAY

def place(f, x, y, face=(0, -1), z=0.0):
    f["root"].location = (x, y, z)
    f["root"].rotation_euler = (0, 0, math.atan2(face[0], -face[1]))

def pose(f, walk=0.0, phase=0.0, arms=None, sit=False, head_turn=0.0, head_nod=0.0):
    s = math.sin(phase) * walk
    f["legL"].rotation_euler = (-math.pi / 2 if sit else s * 0.8, 0, 0)
    f["legR"].rotation_euler = (-math.pi / 2 if sit else -s * 0.8, 0, 0)
    aL, aR = arms if arms else (-s * 0.7, s * 0.7)
    f["armL"].rotation_euler = (aL, 0, 0) if not isinstance(aL, tuple) else aL
    f["armR"].rotation_euler = (aR, 0, 0) if not isinstance(aR, tuple) else aR
    f["head"].rotation_euler = (head_nod, 0, head_turn)

SHIRTS = [(0.10, 0.20, 0.45), (0.45, 0.45, 0.47), (0.08, 0.08, 0.09), (0.50, 0.12, 0.10), (0.15, 0.35, 0.25),
          (0.75, 0.72, 0.65), (0.35, 0.22, 0.45), (0.60, 0.45, 0.20), (0.20, 0.30, 0.40)]
HAIRS = [(0.05, 0.04, 0.04), (0.25, 0.14, 0.06), (0.55, 0.38, 0.18), (0.12, 0.08, 0.05), (0.75, 0.60, 0.35)]
PANTS = [(0.10, 0.15, 0.30), (0.12, 0.12, 0.13), (0.40, 0.38, 0.34), (0.20, 0.25, 0.35)]
LAPTOP = colmat((0.55, 0.56, 0.58), 0.3)
LAPTOP_SCREEN = colmat((0.55, 0.70, 1.0), 0.3, emit=1.6)

GUY_X, GUY_ROW = SA.SEAT_X[SA.GUY_SEAT], SA.N_ROWS - 1
students = []          # (figure, x, y, z, row, seat, phase)
TURNERS = []           # the ones in front of him who turn around
for r in range(SA.N_ROWS):
    for s_i, x in enumerate(SA.SEAT_X):
        if r == GUY_ROW and s_i == SA.GUY_SEAT:
            continue
        near = (r == GUY_ROW - 1 and s_i in (10, 11, 12, 13)) or (r == GUY_ROW - 2 and s_i in (11, 12))
        if not near and rng.random() > (0.55 if r < GUY_ROW else 0.2):
            continue
        k = len(students)
        f = figure(f"st{k}", rng.choice(HAIRS), rng.choice(SHIRTS), rng.choice(PANTS), rng.choice(SKIN_TONES),
                   long_hair=rng.random() < 0.45, cap=(rng.choice(SHIRTS) if rng.random() < 0.12 else None),
                   hood=rng.random() < 0.35, glasses=rng.random() < 0.2)
        y, z = SA.ROW_DEPTH * r + 1.35, r + 1.0 + 0.46 - 0.75
        students.append((f, x, y, z, r, s_i, rng.random() * 6.28))
        if near:
            TURNERS.append(len(students) - 1)
        if rng.random() < 0.45:
            boxes(f"lap{k}", [((-0.3, 0.3, -0.2, 0.22, 0.0, 0.03), LAPTOP), ((-0.3, 0.3, -0.24, -0.2, 0.03, 0.42), LAPTOP),
                              ((-0.27, 0.27, -0.2, -0.195, 0.06, 0.39), LAPTOP_SCREEN)], (x, SA.ROW_DEPTH * r + 0.38, r + 1.8))

GUY = figure("guy", (0.10, 0.07, 0.05), (0.38, 0.40, 0.44), (0.10, 0.11, 0.13), (0.78, 0.53, 0.38), cap=(0.85, 0.36, 0.10), hood=True)
PROF = figure("prof", (0.55, 0.55, 0.55), (0.62, 0.62, 0.66), (0.15, 0.15, 0.18), (0.82, 0.60, 0.45), glasses=True)
GUY_SEAT_Z = GUY_ROW + 1.0 + 0.46 - 0.75
GUY_SEAT_Y = SA.seat_y(GUY_ROW)
PROF_POS = Vector((-1.8, -4.3, 0.0))

# the steak (in the right hand, held by the bone) and the ranch (left hand)
SEAR = colmat((0.22, 0.09, 0.04), 0.55)
CRUST = colmat((0.32, 0.14, 0.06), 0.6)
PINK = colmat((0.50, 0.10, 0.09), 0.45)
FAT = colmat((0.90, 0.82, 0.62), 0.6)
BONE = colmat((0.92, 0.88, 0.78), 0.45)
steak = boxes("steak", [((-0.035, 0.035, -0.035, 0.035, -1.12, -0.62), BONE),
                        ((-0.05, 0.05, -0.05, 0.05, -1.16, -1.10), BONE),
                        ((-0.22, 0.22, -0.12, 0.12, -1.56, -1.12), SEAR),
                        ((-0.18, 0.18, -0.125, 0.125, -1.52, -1.16), CRUST),
                        ((-0.13, 0.09, -0.128, 0.128, -1.46, -1.22), PINK),
                        ((0.16, 0.23, -0.1, 0.1, -1.54, -1.14), FAT)], (0, 0, 0), GUY["armR"])
GREEN_L = colmat((0.10, 0.45, 0.15), 0.5)
ranch = boxes("ranch", [((-0.09, 0.09, -0.06, 0.06, -1.05, -0.65), colmat((0.95, 0.95, 0.92), 0.35)),
                        ((-0.095, 0.095, -0.065, 0.065, -0.95, -0.78), GREEN_L),
                        ((-0.04, 0.04, -0.04, 0.04, -1.15, -1.05), GREEN_L)], (0, 0, 0), GUY["armL"])
drip_m = colmat((0.95, 0.94, 0.88), 0.3)
drips = [boxes(f"drip{k}", [((-0.025, 0.025, -0.025, 0.025, -0.05, 0.05), drip_m)], AWAY) for k in range(10)]

AURA_M = solid("aura_shell", (0.45, 0.10, 1.0), rough=0.5, emit=3.5)
B.bsdf(AURA_M).inputs["Alpha"].default_value = 0.22
try:
    AURA_M.surface_render_method = "BLENDED"
except Exception:
    pass
shell = boxes("shell", [((-0.33, 0.33, -0.2, 0.2, 0.7, 1.58), AURA_M), ((-0.33, 0.33, -0.33, 0.33, 1.45, 2.2), AURA_M),
                        ((-0.55, 0.55, -0.2, 0.2, 1.0, 1.55), AURA_M)], AWAY)

# ------------------------------------------------------------------ lights, world, camera

world = bpy.data.worlds.new("bg")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.02, 0.025, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
for n, x in enumerate((-7.5, -2.5, 2.5, 7.5)):
    B.area(f"ceil{n}", Vector((x, 3.5, ZC - 0.3)), Vector((x, 3.5, 0)), 1.0, 1400.0, (1.0, 0.96, 0.88), size_y=26.0)
B.area("screen_glow", Vector((0, Y0 + 0.5, 6.0)), Vector((0, 10, 5)), 14.0, 900.0, (0.75, 0.85, 1.0), size_y=6.0)
aura_ld = bpy.data.lights.new("aura", "POINT"); aura_ld.color = (0.75, 0.35, 1.0); aura_ld.shadow_soft_size = 0.6
aura = B.link(bpy.data.objects.new("aura", aura_ld))
aura.location = (GUY_X + 0.3, GUY_SEAT_Y + 0.9, GUY_SEAT_Z + 2.4)
rim_ld = bpy.data.lights.new("rim", "POINT"); rim_ld.color = (1.0, 0.55, 0.25); rim_ld.shadow_soft_size = 0.4
rim = B.link(bpy.data.objects.new("rim", rim_ld))
rim.location = (GUY_X - 1.2, GUY_SEAT_Y + 1.6, GUY_SEAT_Z + 2.0)

cam = B.camera(lens=30, fstop=2.8)
B.render_settings(FPS, samples=32, motion_blur=0.3)

# ------------------------------------------------------------------ the guy

T_ENTER, T_ARRIVE = SA.enter_time(E), SA.arrive_time(E)
BITES = SA.bites(E, DUR)

def bite_amount(t):
    """0 = steak held in front, 1 = at his mouth."""
    a = 0.0
    for b in BITES:
        if b - 0.45 <= t < b + 0.35:
            a = max(a, smooth01((t - (b - 0.45)) / 0.4) * (1 - smooth01((t - (b + 0.05)) / 0.3)))
    return a

def pour_amount(t):
    return ramp(t, E["ranch"] - 0.5, E["ranch"] - 0.1) * (1 - ramp(t, E["ranch"] + 1.2, E["ranch"] + 1.6))

def guy_state(t):
    ranch.location = (0, 0, 0) if t >= E["ranch"] - 0.55 else AWAY
    if SA.seated(t, E):
        place(GUY, GUY_X, GUY_SEAT_Y, face=(0, -1), z=GUY_SEAT_Z)
        b, p = bite_amount(t), pour_amount(t)
        # right arm: forward and down (steak over the desk) to up at the mouth, bent inward
        right = (-1.15 - 0.85 * b, 0, 0.35 * b)
        left = (-1.2 - 0.35 * p, -0.5 * p, -0.25 * p) if t >= E["ranch"] - 0.55 else (-0.3, 0, 0)
        chew = 0.06 * math.sin(t * 14) if (b > 0.6 or any(0 < t - x < 1.0 for x in BITES)) else 0.0
        stare = 0.0
        pose(GUY, sit=True, arms=(left, right), head_nod=chew + 0.1 * b, head_turn=stare)
        return
    dist = min(SA.WALK_LEN, (t - T_ENTER) * SA.WALK_SPEED) if t >= T_ENTER else -1
    if dist < 0:
        hide(GUY)
        return
    p, d = SA.walk_point(dist)
    place(GUY, p[0], p[1], face=d, z=SA.floor_z(p[1]))
    pose(GUY, walk=1.0 if dist < SA.WALK_LEN else 0.0, phase=(t - T_ENTER) * 9.0, arms=None)
    GUY["armR"].rotation_euler = (-1.15, 0, 0)

def drip_state(t):
    p = pour_amount(t)
    tip = ranch.matrix_world @ Vector((0, 0, -1.15))
    for k, ob in enumerate(drips):
        u = ((t * 2.2 + k / len(drips)) % 1.0)
        if p > 0.7:
            ob.location = tip + Vector((0, 0, -0.45 * u))
            ob.scale = (1.0,) * 3
        else:
            ob.location = AWAY

# ------------------------------------------------------------------ timeline

def turn_amount(t, k):
    """Row in front turns around in stutters (buffering): 0 = facing the board, 1 = facing him."""
    t0 = SA.turn_start(E) + 0.18 * k
    u = max(0.0, min(1.0, (t - t0) / 0.8))
    return math.floor(u * 4) / 4

def apply_state(t):
    door_open = ramp(t, E["B"] - 0.25, E["B"] + 0.2) * (1 - ramp(t, T_ARRIVE - 0.4, T_ARRIVE + 0.3))
    door.rotation_euler = (0, 0, -1.7 * door_open)
    guy_state(t)
    drip_state(t)
    for n, (f, x, y, z, r, s_i, ph) in enumerate(students):
        place(f, x, y, face=(0, -1), z=z)
        turn = 0.0
        if n in TURNERS:
            k = TURNERS.index(n)
            dx = GUY_X - x
            full = math.pi - 0.35 * math.copysign(1, dx) * min(1.0, abs(dx) / 2) if abs(dx) > 0.2 else math.pi
            turn = full * turn_amount(t, k) * (1 if dx >= 0 else -1)
        typing = 0.08 * math.sin(t * 11 + ph) if (n % 3 == 0) else 0.0
        pose(f, sit=True, arms=(-1.05 + typing, -1.05 - typing), head_turn=turn, head_nod=0.05 * math.sin(t * 0.7 + ph))
    place(PROF, PROF_POS.x, PROF_POS.y, face=(0.25, 1))
    look = ramp(t, E["G"] - 0.2, E["G"] + 0.3)
    pose(PROF, arms=(-0.2 - 0.3 * math.sin(t * 1.3) * (1 - look), -0.25), head_nod=-0.18 * look, head_turn=0.25 * look)
    glow = ramp(t, E["H"] - 0.3, E["H"] + 0.8)
    if glow > 0:
        sc = 1.0 + 0.04 * math.sin(t * 7) + 0.1 * glow
        shell.location = (GUY_X, GUY_SEAT_Y, GUY_SEAT_Z + (1 - sc) * 1.4)
        shell.scale = (sc, sc, sc)
        B.bsdf(AURA_M).inputs["Alpha"].default_value = 0.16 * glow
    else:
        shell.location = AWAY
    aura.data.energy = 30.0 + 900.0 * glow + 700.0 * math.exp(-max(0.0, t - E["chewing"]) * 3) * (t >= E["chewing"])
    rim.data.energy = 60.0 + 120.0 * glow
    loc, target, fstop, lens = camera_at(t)
    B.aim(cam, loc, target)
    cam.data.lens = lens
    cam.data.dof.focus_distance = (target - loc).length
    cam.data.dof.aperture_fstop = fstop
    cam.data.clip_start = 0.05
    cam.data.clip_end = 200

# ------------------------------------------------------------------ camera: each shot returns (camera location, look target)

def guy_head():
    return GUY["root"].matrix_world @ Vector((0, 0, 1.8))

def steak_pt():
    return steak.matrix_world @ Vector((0, 0, -1.2))

GH = Vector((GUY_X, GUY_SEAT_Y, GUY_SEAT_Z + 1.8))        # where his head is when seated

def shot_hook(t):
    u = t / max(1.0, E["B"])
    tg = GH + Vector((-0.1, -0.8, -0.5))
    return tg + Vector((-2.2 + 0.5 * u, -4.6 + 0.9 * u, 2.3 - 0.3 * u)), tg
def shot_door(t):
    p = GUY["root"].location if GUY["root"].location.z > -100 else Vector((10.0, 17.3, 8.0))
    tg = Vector((p.x, p.y, max(p.z, 7.0) + 1.3))
    return Vector((5.2, 9.0, 11.2)) + Vector((0.3 * (t - E["B"]), 0, 0)), tg
STEAK_REST = Vector((GUY_X + 0.375, GUY_SEAT_Y - 1.25, GUY_SEAT_Z + 0.95))

def shot_close(t):
    tg = GH.lerp(STEAK_REST, 0.5)
    a = math.radians(-118 + 3.0 * (t - E["C"]))
    return tg + 3.7 * Vector((math.cos(a), math.sin(a), 0.3)), tg
def shot_ranch(t):
    tg = Vector((GUY_X - 0.3, GUY_SEAT_Y - 1.3, GUY_SEAT_Z + 1.35))
    return Vector((GUY_X - 1.3 + 0.15 * (t - E["E"]), GUY_SEAT_Y - 5.6, GUY_SEAT_Z + 1.7)), tg
def shot_usda(t):
    tg = GH.lerp(STEAK_REST, 0.6)
    a = math.radians(-62 - 4.0 * (t - E["F"]))
    return tg + 3.2 * Vector((math.cos(a), math.sin(a), 0.32)), tg
def shot_prof(t):
    head = PROF_POS + Vector((0, 0, 1.75))
    return head + Vector((1.0 - 0.1 * (t - E["G"]), 3.2, 0.25)), head + Vector((0, 0, -0.1))
def shot_face(t):
    tg = GH + Vector((0, -0.2, -0.1))
    return tg + Vector((-1.0 + 0.1 * (t - E["chewing"]), -2.9 + 0.2 * (t - E["chewing"]), 0.35)), tg
def shot_end(t):
    tg = GH + Vector((0, -0.4, -0.35))
    u = t - E["H"]
    a = math.radians(-105 + 3.5 * u)
    d = 4.2 - 0.25 * u
    return tg + d * Vector((math.cos(a), math.sin(a), 0.62)), tg

SHOTS = [(shot_hook, None), (shot_door, (E["B"] - 0.25, E["B"] + 0.15)), (shot_close, (E["C"] - 0.3, E["C"] + 0.15)),
         (shot_ranch, (E["E"] - 0.3, E["E"] + 0.15)), (shot_usda, (E["F"] - 0.3, E["F"] + 0.15)),
         (shot_prof, (E["G"] - 0.25, E["G"] + 0.1)), (shot_face, (E["chewing"] - 0.25, E["chewing"] + 0.1)),
         (shot_end, (E["H"] - 0.3, E["H"] + 0.5))]

LENS = {shot_prof: 45.0, shot_door: 35.0}

def camera_at(t):
    k = 0
    for n, (fn, win) in enumerate(SHOTS):
        if win and t >= win[0]:
            k = n
    fn, win = SHOTS[k]
    loc, tg = fn(t)
    lens = LENS.get(fn, 30.0)
    if win and t < win[1] and k > 0:
        fn0 = SHOTS[k - 1][0]
        loc0, tg0 = fn0(t)
        u = smooth01((t - win[0]) / (win[1] - win[0]))
        loc, tg = loc0.lerp(loc, u), tg0.lerp(tg, u)
        lens = LENS.get(fn0, 30.0) * (1 - u) + lens * u
    d = (tg - loc).length * 30.0 / lens
    fstop = 2.0 if d < 5 else (2.8 if d < 10 else 4.0)
    return loc, tg, fstop, lens

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    names = ("steak", "bone", "ranch", "guy", "prof", "door") + tuple(f"turn{k}" for k in range(len(TURNERS)))
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        pts = {
            "steak": steak.matrix_world @ Vector((0.0, 0, -1.25)),
            "bone": steak.matrix_world @ Vector((0, 0, -0.85)),
            "ranch": ranch.matrix_world @ Vector((0, 0, -0.85)),
            "guy": GUY["root"].matrix_world @ Vector((0, 0, 2.15)),
            "prof": PROF["root"].matrix_world @ Vector((0, 0, 1.75)),
            "door": Vector((10.0, 17.5, 10.6)),
        }
        for k, n in enumerate(TURNERS):
            pts[f"turn{k}"] = students[n][0]["root"].matrix_world @ Vector((0, 0, 2.25))
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
