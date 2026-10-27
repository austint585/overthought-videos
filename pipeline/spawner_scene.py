"""Blender scene for 'How Stacy spawners work': a floating voxel island with a plaza spawner, Chad's house, a cafe,
a library, a farmers market and a club, built in code and timed to the narration.

blender -b --factory-startup -P spawner_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Always writes out_dir/anchors.json: screen positions of label points for every frame.
"""
import json, math, os, random, sys
import bpy, bmesh
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import bkit as B
import spawner_anim as SA

argv = sys.argv[sys.argv.index("--") + 1:]
TIMING, OUT, MODE = argv[0], argv[1], argv[2]
T = json.load(open(TIMING))
FPS, DUR, E = T["fps"], T["duration"], T["events"]
NF = int(round(DUR * FPS))
os.makedirs(OUT, exist_ok=True)
B.clear_scene()
scene = B.scene
rng = random.Random(11)
AWAY = Vector((0, 0, -1.0e5))
SP = Vector((0.5, 0.5, 0.5))           # the plaza spawner, block (0, 0, 0)
CLUB_SP = Vector((13.5, 0.5, 0.5))

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

def ramp(t, t0, t1):
    return smooth01((t - t0) / (t1 - t0))

# ------------------------------------------------------------------ pixel-texture materials

def pixel_mat(name, pal, rough=0.85, fringe=None, lines=None, emit=0.0, metallic=0.0):
    """Minecraft-style 16x16 pixel noise on every face: the position (nudged inside the block) is snapped to 1/16
    and hashed. fringe: palette for the grass top and the top 3 pixels of the sides. lines: (axis_scale, dark) mortar or plank seams."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metallic
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

    def palette(cols):
        r = nt.nodes.new("ShaderNodeValToRGB")
        r.color_ramp.interpolation = "CONSTANT"
        els = r.color_ramp.elements
        els[0].color = (*cols[0], 1)
        els[1].position = 1.0 / len(cols)
        els[1].color = (*cols[1 % len(cols)], 1)
        for k in range(2, len(cols)):
            e = els.new(k / len(cols)); e.color = (*cols[k], 1)
        nt.links.new(wn.outputs["Value"], r.inputs["Fac"])
        return r

    base = palette(pal).outputs["Color"]
    if fringe:
        top = palette(fringe).outputs["Color"]
        sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(snap.outputs[0], sep.inputs[0])
        fr = nt.nodes.new("ShaderNodeMath"); fr.operation = "FRACT"; nt.links.new(sep.outputs["Z"], fr.inputs[0])
        hi = nt.nodes.new("ShaderNodeMath"); hi.operation = "GREATER_THAN"; hi.inputs[1].default_value = 0.76
        nt.links.new(fr.outputs[0], hi.inputs[0])
        nsep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Normal"], nsep.inputs[0])
        up = nt.nodes.new("ShaderNodeMath"); up.operation = "GREATER_THAN"; up.inputs[1].default_value = 0.5
        nt.links.new(nsep.outputs["Z"], up.inputs[0])
        mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
        nt.links.new(hi.outputs[0], mx.inputs[0]); nt.links.new(up.outputs[0], mx.inputs[1])
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
        nt.links.new(mx.outputs[0], mix.inputs[0]); nt.links.new(base, mix.inputs[6]); nt.links.new(top, mix.inputs[7])
        base = mix.outputs[2]
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

GRASS = [(0.10, 0.30, 0.05), (0.13, 0.36, 0.06), (0.08, 0.25, 0.04), (0.16, 0.40, 0.08)]
DIRT = [(0.20, 0.11, 0.05), (0.25, 0.14, 0.07), (0.16, 0.09, 0.04), (0.28, 0.17, 0.09)]
STONE = [(0.22, 0.22, 0.23), (0.27, 0.27, 0.28), (0.19, 0.19, 0.20), (0.31, 0.31, 0.32)]
MATS = {
    "grass": pixel_mat("grass", DIRT, fringe=GRASS),
    "dirt": pixel_mat("dirt", DIRT),
    "stone": pixel_mat("stone", STONE + [(0.05, 0.05, 0.05)]),
    "bricks": pixel_mat("bricks", [(0.30, 0.30, 0.31), (0.34, 0.34, 0.35), (0.27, 0.27, 0.28)], lines=((2, 4, 2), (0.10, 0.10, 0.11))),
    "path": pixel_mat("path", [(0.36, 0.26, 0.13), (0.42, 0.31, 0.16), (0.32, 0.22, 0.11)]),
    "planks": pixel_mat("planks", [(0.42, 0.26, 0.12), (0.47, 0.30, 0.14), (0.38, 0.23, 0.10)], lines=((1, 1, 4), (0.20, 0.11, 0.05))),
    "birch": pixel_mat("birch", [(0.75, 0.66, 0.45), (0.80, 0.71, 0.50), (0.70, 0.61, 0.41)], lines=((1, 1, 4), (0.45, 0.38, 0.24))),
    "log": pixel_mat("log", [(0.17, 0.11, 0.06), (0.21, 0.14, 0.07), (0.13, 0.08, 0.04)]),
    "leaves": pixel_mat("leaves", [(0.05, 0.20, 0.03), (0.07, 0.26, 0.04), (0.03, 0.15, 0.02), (0.09, 0.30, 0.05)]),
    "roof": pixel_mat("roof", [(0.18, 0.08, 0.05), (0.22, 0.10, 0.06), (0.15, 0.06, 0.04)], lines=((1, 1, 2), (0.08, 0.03, 0.02))),
    "glass": pixel_mat("glass", [(0.55, 0.75, 0.85), (0.65, 0.82, 0.90)], rough=0.08),
    "books": pixel_mat("books", [(0.45, 0.08, 0.05), (0.08, 0.20, 0.45), (0.12, 0.35, 0.10), (0.50, 0.38, 0.10), (0.30, 0.12, 0.30)],
                       lines=((1, 1, 2), (0.12, 0.07, 0.03))),
    "black": pixel_mat("black", [(0.015, 0.015, 0.02), (0.025, 0.025, 0.03)], rough=0.4),
    "neon": solid("neon", (1.0, 0.05, 0.6), emit=4.0),
    "red": pixel_mat("red_wool", [(0.55, 0.04, 0.03), (0.62, 0.06, 0.04)]),
    "white": pixel_mat("white_wool", [(0.80, 0.80, 0.78), (0.86, 0.86, 0.84)]),
    "yellow": pixel_mat("yellow_wool", [(0.85, 0.60, 0.04), (0.90, 0.66, 0.06)]),
    "blue": pixel_mat("blue_wool", [(0.05, 0.15, 0.55), (0.07, 0.18, 0.62)]),
    "green": pixel_mat("green_wool", [(0.15, 0.40, 0.05), (0.18, 0.46, 0.06)]),
    "lantern": solid("lantern", (1.0, 0.65, 0.25), emit=0.5),
    "water": pixel_mat("water", [(0.05, 0.20, 0.55), (0.06, 0.24, 0.62)], rough=0.05),
    "cloud": solid("cloud", (0.95, 0.95, 0.97), rough=0.9),
}
for k in ("glass", "water"):
    B.bsdf(MATS[k]).inputs["Alpha"].default_value = 0.55

# ------------------------------------------------------------------ voxel world

GRID = {}

def fill(i0, i1, j0, j1, k0, k1, mat):
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            for k in range(k0, k1 + 1):
                if mat is None:
                    GRID.pop((i, j, k), None)
                else:
                    GRID[(i, j, k)] = mat

R_ISLAND = 25.5
nrng = np.random.default_rng(5)
edge_noise = nrng.normal(0, 1.0, 64)
for i in range(-27, 28):
    for j in range(-27, 28):
        r = math.hypot(i + 0.5, j + 0.5)
        ang = math.atan2(j + 0.5, i + 0.5)
        rr = R_ISLAND + 1.2 * edge_noise[int((ang + math.pi) / (2 * math.pi) * 63)]
        if r > rr:
            continue
        depth = int(3 + (rr - r) * 0.55 + nrng.integers(0, 3))
        GRID[(i, j, -1)] = "grass"
        for k in range(-3, -1):
            GRID[(i, j, k)] = "dirt"
        for k in range(-3 - depth, -3):
            GRID[(i, j, k)] = "stone"

def top(i, j, mat):
    if (i, j, -1) in GRID:
        GRID[(i, j, -1)] = mat

# plaza: the spawner's 9x9 spawn area
for i in range(-4, 5):
    for j in range(-4, 5):
        top(i, j, "bricks")
# path from Chad's door to the plaza
DOOR = Vector((-19.0, 9.5))
PLAZA_W = Vector((-4.0, 0.5))
for s in np.linspace(0, 1, 120):
    p = DOOR.lerp(PLAZA_W, s)
    for di in (-1, 0):
        for dj in (-1, 0):
            top(int(math.floor(p.x + di + 0.5)), int(math.floor(p.y + dj + 0.5)), "path")

# Chad's house (front wall left open: a cutaway)
fill(-22, -17, 10, 14, -1, -1, "planks")
fill(-22, -17, 14, 14, 0, 3, "planks")
fill(-22, -22, 10, 14, 0, 3, "planks")
fill(-17, -17, 10, 14, 0, 3, "planks")
for (i, j) in ((-22, 10), (-17, 10), (-22, 14), (-17, 14)):
    fill(i, i, j, j, 0, 3, "log")
fill(-22, -22, 12, 12, 1, 2, "glass")
fill(-17, -17, 12, 12, 1, 2, "glass")
fill(-20, -19, 14, 14, 1, 2, "glass")
fill(-23, -16, 9, 15, 4, 4, "roof")
fill(-22, -17, 10, 14, 5, 5, "roof")
fill(-21, -18, 11, 13, 6, 6, "roof")

# cafe (awning facing the plaza)
fill(7, 11, -12, -9, -1, -1, "birch")
fill(7, 11, -12, -9, 0, 2, "birch")
fill(8, 10, -9, -9, 0, 1, None)
fill(8, 10, -9, -9, 1, 1, "glass")
fill(7, 11, -12, -9, 3, 3, "roof")
for i in range(6, 13):
    GRID[(i, -8, 3)] = "red" if i % 2 == 0 else "white"

# library
fill(-13, -7, -13, -9, 0, 3, "bricks")
fill(-12, -8, -9, -9, 1, 2, "books")
fill(-10, -10, -9, -9, 0, 1, None)
fill(-14, -6, -14, -8, 4, 4, "roof")
fill(-13, -7, -13, -9, 5, 5, "roof")

# farmers market stalls
for n, (i0, col) in enumerate(((5, "yellow"), (8, "blue"), (11, "green"))):
    fill(i0, i0 + 1, 7, 7, 0, 0, "planks")              # counter
    fill(i0, i0, 9, 9, 0, 1, "log"); fill(i0 + 1, i0 + 1, 9, 9, 0, 1, "log")
    fill(i0, i0 + 1, 7, 9, 2, 2, col)                    # awning

# club
fill(17, 23, -4, 4, 0, 4, "black")
fill(17, 17, 0, 1, 0, 2, None)                           # door
fill(16, 24, -5, 5, 5, 5, "black")
for j in range(-5, 6):
    GRID[(16, j, 5)] = "neon"
for k in range(0, 5):
    GRID[(16, -5, k)] = "neon"; GRID[(16, 5, k)] = "neon"

# pond by the library
fill(-15, -12, -4, -2, -1, -1, "water")

# trees
def tree(i, j, h=4):
    fill(i - 2, i + 2, j - 2, j + 2, h - 1, h, "leaves")
    fill(i - 1, i + 1, j - 1, j + 1, h + 1, h + 2, "leaves")
    fill(i, i, j, j, 0, h, "log")
for (i, j) in ((-8, 15), (3, 18), (-23, -3), (-3, -19), (18, 13), (20, -15)):
    tree(i, j, 4 + (i + j) % 2)

# lanterns on posts around the plaza

DIRS = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]),
        ((-1, 0, 0), [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]),
        ((0, 1, 0), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)]),
        ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
        ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]),
        ((0, 0, -1), [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)])]
SEE_THROUGH = {"glass", "water", "leaves"}

def voxel_mesh(name, grid):
    keys = sorted(set(grid.values()))
    idx = {k: n for n, k in enumerate(keys)}
    verts, faces, mats = [], [], []
    for (i, j, k), mat in grid.items():
        for (di, dj, dk), quad in DIRS:
            nb = grid.get((i + di, j + dj, k + dk))
            if nb is not None and (nb not in SEE_THROUGH or nb == mat):
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

world_ob = voxel_mesh("world", GRID)
clouds = {}
for (ci, cj, ck, w, d) in ((-30, 10, 22, 9, 5), (12, 30, 24, 11, 6), (25, -20, 20, 8, 5), (-44, -8, 24, 10, 4), (40, 8, 26, 12, 6)):
    for i in range(w):
        for j in range(d):
            if (i in (0, w - 1)) and (j in (0, d - 1)):
                continue
            clouds[(ci + i, cj + j, ck)] = "cloud"
voxel_mesh("clouds", clouds)

# ------------------------------------------------------------------ characters

_mat_cache = {}
def colmat(color, rough=0.55, emit=0.0):
    key = (color, rough, emit)
    if key not in _mat_cache:
        _mat_cache[key] = solid(f"c{len(_mat_cache)}", color, rough, emit)
    return _mat_cache[key]

def boxes(name, parts, origin, parent):
    """parts: list of ((x0, x1, y0, y1, z0, z1), material)."""
    mats = []
    builders = []
    for bb, m in parts:
        if m not in mats:
            mats.append(m)
        builders.append(B.with_material(B.box(*bb), mats.index(m)))
    ob = B.mesh_from(name, B.many(*builders), mats)
    ob.parent = parent
    ob.location = origin
    return ob

SKIN = (0.80, 0.52, 0.36)
def figure(name, hair, shirt, pants, long_hair=False, shades=False, skin=SKIN, shoes=(0.05, 0.05, 0.06)):
    root = B.link(bpy.data.objects.new(name, None))
    S, H, Sh, P, D = colmat(skin), colmat(hair, 0.7), colmat(shirt), colmat(pants, 0.7), colmat((0.03, 0.02, 0.02), 0.4)
    Shoe = colmat(shoes, 0.5)
    f = {"root": root}
    for side, x in (("L", -0.125), ("R", 0.125)):
        f["leg" + side] = boxes(f"{name}_leg{side}", [((-0.125, 0.125, -0.125, 0.125, -0.75, 0.0), P),
                                                       ((-0.13, 0.13, -0.135, 0.13, -0.75, -0.62), Shoe)], (x, 0, 0.75), root)
    boxes(f"{name}_body", [((-0.25, 0.25, -0.125, 0.125, 0, 0.75), Sh)], (0, 0, 0.75), root)
    for side, x in (("L", -0.375), ("R", 0.375)):
        f["arm" + side] = boxes(f"{name}_arm{side}", [((-0.125, 0.125, -0.125, 0.125, -0.25, 0.0), Sh),
                                                       ((-0.12, 0.12, -0.12, 0.12, -0.75, -0.25), S)], (x, 0, 1.5), root)
    head = [((-0.25, 0.25, -0.25, 0.25, 0, 0.5), S), ((-0.27, 0.27, -0.27, 0.27, 0.38, 0.55), H),
            ((-0.16, -0.06, -0.265, -0.25, 0.2, 0.28), D), ((0.06, 0.16, -0.265, -0.25, 0.2, 0.28), D),
            ((-0.07, 0.07, -0.262, -0.25, 0.07, 0.1), colmat(shade(skin, 0.6)))]
    if long_hair:
        head += [((-0.27, 0.27, 0.1, 0.29, -0.5, 0.5), H), ((-0.29, -0.2, -0.2, 0.27, -0.35, 0.45), H),
                 ((0.2, 0.29, -0.2, 0.27, -0.35, 0.45), H)]
    else:
        head += [((-0.27, 0.27, 0.08, 0.28, 0.12, 0.5), H)]
    if shades:
        head += [((-0.21, 0.21, -0.28, -0.25, 0.19, 0.3), colmat((0.01, 0.01, 0.012), 0.15))]
    f["head"] = boxes(f"{name}_head", head, (0, 0, 1.5), root)
    return f

def hide(f):
    f["root"].location = AWAY

def place(f, x, y, face=(0, -1), z=0.0, scale=1.0):
    f["root"].location = (x, y, z)
    f["root"].rotation_euler = (0, 0, math.atan2(face[0], -face[1]))
    f["root"].scale = (scale, scale, scale)

def pose(f, walk=0.0, phase=0.0, arms=None, sit=False):
    s = math.sin(phase) * walk
    f["legL"].rotation_euler = (-math.pi / 2 if sit else s * 0.8, 0, 0)
    f["legR"].rotation_euler = (-math.pi / 2 if sit else -s * 0.8, 0, 0)
    aL, aR = arms if arms else (-s * 0.7, s * 0.7)
    f["armL"].rotation_euler = (aL, 0, 0)
    f["armR"].rotation_euler = (aR, 0, 0)

STACY_LOOKS = [((0.85, 0.65, 0.25), (0.95, 0.45, 0.65), (0.20, 0.30, 0.65)),
               ((0.25, 0.12, 0.05), (0.95, 0.95, 0.92), (0.10, 0.10, 0.12)),
               ((0.05, 0.04, 0.04), (0.55, 0.20, 0.75), (0.85, 0.82, 0.75)),
               ((0.55, 0.15, 0.05), (0.25, 0.60, 0.55), (0.20, 0.25, 0.55)),
               ((0.80, 0.60, 0.30), (0.90, 0.75, 0.20), (0.15, 0.15, 0.18)),
               ((0.30, 0.15, 0.07), (0.85, 0.30, 0.25), (0.25, 0.35, 0.60))]
def stacy(name, n):
    hair, shirt, pants = STACY_LOOKS[n % len(STACY_LOOKS)]
    return figure(name, hair, shirt, pants, long_hair=True, skin=(0.85, 0.58, 0.42))

def chad(name):
    return figure(name, (0.06, 0.04, 0.03), (0.92, 0.92, 0.90), (0.10, 0.18, 0.40), shades=True)

CHAD = chad("chad")
PLAZA_POS = [(-2.2, 2.6), (3.2, 3.0), (3.4, -2.4), (-2.0, -2.8)]
PLAZA_STACIES = [stacy(f"ps{k}", k) for k in range(4)]
SPOT_POS = {"cafe": [(8.3, -6.3), (10.3, -6.6)], "library": [(-10.6, -7.0), (-8.6, -7.3)], "market": [(6.0, 5.8), (9.6, 6.0)]}
SPOT_STACIES = [(stacy(f"ss{k}", k + 2), pos) for k, pos in enumerate([p for v in SPOT_POS.values() for p in v])]
CLUB_STACIES = [stacy(f"cs{k}", k) for k in range(6)]
CLUB_CHADS = [chad(f"cc{k}") for k in range(8)]
MINI = stacy("mini", 0)

# phone and pickaxe
phone = boxes("phone", [((-0.07, 0.07, -0.02, 0.02, -0.12, 0.12), colmat((0.6, 0.8, 1.0), 0.3, emit=3.0))], (0, -0.45, 0.95), CHAD["root"])
pick_parts = [((-0.035, 0.035, -0.035, 0.035, -1.30, -0.62), colmat((0.30, 0.18, 0.08), 0.7))]
DIAMOND = solid("diamond", (0.10, 0.65, 0.62), rough=0.25, emit=0.25, emit_color=(0.55, 0.25, 1.0))
pick_parts += [((-0.045, 0.045, -0.34, 0.34, -1.36, -1.26), DIAMOND), ((-0.045, 0.045, -0.42, -0.30, -1.30, -1.20), DIAMOND),
               ((-0.045, 0.045, 0.30, 0.42, -1.30, -1.20), DIAMOND)]
pickaxe = boxes("pickaxe", pick_parts, (0, 0, 0), CHAD["armR"])

# ------------------------------------------------------------------ spawners, flames, poofs, ring, debris, XP

IRON = solid("iron", (0.05, 0.06, 0.08), rough=0.35, metallic=0.85)
FLAME_Y = solid("flame_y", (1.0, 0.55, 0.05), emit=4.0)
FLAME_O = solid("flame_o", (1.0, 0.22, 0.02), emit=3.5)
SMOKE = solid("smoke", (0.80, 0.80, 0.82), rough=0.9)

def cage_builder():
    s, th, g = 0.5, 0.07, 0.045
    bs = []
    for a in (-s, s):
        for b in (-s, s):
            bs += [B.box(-s, s, a - th / 2, a + th / 2, b - th / 2, b + th / 2),
                   B.box(a - th / 2, a + th / 2, -s, s, b - th / 2, b + th / 2),
                   B.box(a - th / 2, a + th / 2, b - th / 2, b + th / 2, -s, s)]
    for face in (-s + g / 2, s - g / 2):
        for o in (-0.25, 0.0, 0.25):
            bs += [B.box(face - g / 2, face + g / 2, o - g / 2, o + g / 2, -s, s), B.box(face - g / 2, face + g / 2, -s, s, o - g / 2, o + g / 2),
                   B.box(o - g / 2, o + g / 2, face - g / 2, face + g / 2, -s, s), B.box(-s, s, face - g / 2, face + g / 2, o - g / 2, o + g / 2),
                   B.box(o - g / 2, o + g / 2, -s, s, face - g / 2, face + g / 2), B.box(-s, s, o - g / 2, o + g / 2, face - g / 2, face + g / 2)]
    return B.many(*bs)

def make_spawner(name, c, mini=None):
    cage = B.mesh_from(name, cage_builder(), [IRON])
    cage.location = c
    flames = []
    for k in range(22):
        fl = B.mesh_from(f"{name}_fl{k}", B.box(-0.5, 0.5, -0.5, 0.5, -0.5, 0.5), [FLAME_Y if k % 2 else FLAME_O])
        flames.append((fl, rng.uniform(-0.36, 0.36), rng.uniform(-0.36, 0.36), rng.random(), rng.uniform(0.08, 0.15)))
    ld = bpy.data.lights.new(name + "_light", "POINT")
    ld.color = (1.0, 0.55, 0.2)
    ld.shadow_soft_size = 0.3
    light = B.link(bpy.data.objects.new(name + "_light", ld))
    light.location = c + Vector((0, 0, 0.1))
    return {"cage": cage, "flames": flames, "light": light, "c": Vector(c), "mini": mini}

SPAWNER = make_spawner("spawner", SP, MINI)
CLUB_SPAWNER = make_spawner("club_spawner", CLUB_SP)

def spawner_state(S, t, level, alive=True, shake=0.0):
    c = S["c"] + Vector((shake * math.sin(t * 90), shake * math.cos(t * 77), 0))
    S["cage"].location = c if alive else AWAY
    for fl, x, y, ph, size in S["flames"]:
        u = (t * 0.9 + ph) % 1.0
        if not alive or level <= 0.01:
            fl.location = AWAY
            continue
        rise = -0.42 + 1.25 * u
        fl.location = c + Vector((x * (1 - 0.3 * u), y * (1 - 0.3 * u), rise))
        fl.scale = (size * level * (1 - u) + 0.001,) * 3
    S["light"].data.energy = 160.0 * level if alive else 0.0
    if S["mini"]:
        if alive:
            place(S["mini"], c.x, c.y, z=c.z - 0.3, scale=0.3)
            S["mini"]["root"].rotation_euler = (0, 0, t * (0.4 + 3.0 * level))
            pose(S["mini"])
        else:
            hide(S["mini"])

POOF_N = 9
def make_poofs(n_sets):
    sets = []
    for s in range(n_sets):
        parts = []
        for k in range(POOF_N):
            ob = B.mesh_from(f"poof{s}_{k}", B.box(-0.5, 0.5, -0.5, 0.5, -0.5, 0.5), [SMOKE])
            a = 2 * math.pi * k / POOF_N + rng.uniform(-0.3, 0.3)
            parts.append((ob, Vector((math.cos(a), math.sin(a), rng.uniform(0.2, 1.0))).normalized()))
        sets.append(parts)
    return sets

def poof_state(parts, t, t0, origin):
    u = (t - t0) / 0.6
    for ob, d in parts:
        if u < 0 or u > 1:
            ob.location = AWAY
            continue
        ob.location = origin + d * (0.25 + 0.9 * (1 - (1 - u) ** 2))
        ob.scale = (0.22 * math.sin(math.pi * min(1.0, u * 1.3)) + 0.001,) * 3

def torus_builder(R, r, seg=192, ring=8):
    def b(bm):
        rows = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            row = []
            for j in range(ring):
                q = 2 * math.pi * j / ring
                row.append(bm.verts.new(((R + r * math.cos(q)) * math.cos(a), (R + r * math.cos(q)) * math.sin(a), r * math.sin(q))))
            rows.append(row)
        for i in range(seg):
            for j in range(ring):
                bm.faces.new((rows[i][j], rows[(i + 1) % seg][j], rows[(i + 1) % seg][(j + 1) % ring], rows[i][(j + 1) % ring]))
    return b

RING_M = solid("ring", (0.05, 1.0, 0.25), emit=2.5)
ring = B.mesh_from("ring", torus_builder(16.0, 0.12), [RING_M])
d_house = (Vector((-19.5, 12.5)) - SP.xy).normalized()
radius = B.mesh_from("radius", B.box(0, 16, -0.06, 0.06, -0.06, 0.06), [RING_M])

DEBRIS = [(B.mesh_from(f"deb{k}", B.box(-0.5, 0.5, -0.5, 0.5, -0.5, 0.5), [IRON]),
           Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(1.2, 3.0))), rng.uniform(0.08, 0.16)) for k in range(18)]
XP_M = solid("xp", (0.35, 1.0, 0.03), emit=2.5)
def sphere_builder(r):
    def b(bm):
        bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=r)
    return b
XP = [(B.mesh_from(f"xp{k}", sphere_builder(0.07), [XP_M]),
       Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0.6, 1.6)))) for k in range(8)]
POOFS = make_poofs(5)

# ------------------------------------------------------------------ sky, sun, lights, camera, render settings

world = bpy.data.worlds.new("sky")
scene.world = world
world.use_nodes = True
wt = world.node_tree
bg = wt.nodes["Background"]
tc = wt.nodes.new("ShaderNodeTexCoord")
sep = wt.nodes.new("ShaderNodeSeparateXYZ")
mr = wt.nodes.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = -0.1
mr.inputs["From Max"].default_value = 0.7
sky_ramp = wt.nodes.new("ShaderNodeValToRGB")
mid_el = sky_ramp.color_ramp.elements.new(0.35)
wt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
wt.links.new(sep.outputs["Z"], mr.inputs["Value"])
wt.links.new(mr.outputs["Result"], sky_ramp.inputs["Fac"])
wt.links.new(sky_ramp.outputs["Color"], bg.inputs["Color"])
SKY_DAY = [(0.80, 0.86, 0.95), (0.42, 0.62, 0.92), (0.16, 0.36, 0.80)]
SKY_NIGHT = [(0.05, 0.03, 0.10), (0.02, 0.02, 0.06), (0.005, 0.006, 0.02)]

sun = B.sun("sun", -55, 40, 3.6, (1.0, 0.93, 0.82), 2.0)
moon = B.sun("moon", 130, 35, 0.0, (0.55, 0.65, 1.0), 3.0)
LANTERN_M = MATS["lantern"]
NEON_M = MATS["neon"]

def daylight(t):
    """1 = day, 0 = night (the club scene)."""
    return 1.0 - ramp(t, E["E"] - 0.4, E["E"] + 0.5) + ramp(t, E["G"] - 0.4, E["G"] + 0.5)

def sky_state(t):
    d = daylight(t)
    cols = [tuple(n + (dd - n) * d for dd, n in zip(day, night)) for day, night in zip(SKY_DAY, SKY_NIGHT)]
    els = sky_ramp.color_ramp.elements
    els[0].color = (*cols[0], 1); mid_el.color = (*cols[1], 1); els[-1].color = (*cols[2], 1)
    sun.data.energy = 3.6 * d
    moon.data.energy = 0.45 * (1 - d)
    B.bsdf(NEON_M).inputs["Emission Strength"].default_value = 2.0 + 10.0 * (1 - d)

cam = B.camera(lens=35, fstop=2.8)
B.render_settings(FPS, samples=32, motion_blur=0.3)

# ------------------------------------------------------------------ Chad's walk

WALK_SPEED, WALK_LEN = SA.WALK_SPEED, SA.WALK_LEN
BED = Vector(SA.PATH[0])

def chad_walk(dist):
    p, d = SA.walk_point(dist)
    return Vector(p), Vector(d)

T_CROSS = SA.cross_time(E)
HITS = SA.hits(E)
T_BREAK = SA.break_time(E)
MINE_POS = Vector((-0.95, 0.5))

def arm_swing(t):
    a = -1.25
    for h in HITS:
        if h - 0.32 <= t < h - 0.08:
            a = -1.25 - 1.55 * smooth01((t - (h - 0.32)) / 0.24)
        elif h - 0.08 <= t < h:
            a = -2.8 + 1.55 * ((t - (h - 0.08)) / 0.08)
    return a

def chad_state(t):
    pickaxe.location = (0, 0, 0) if t >= E["H"] - 0.5 else AWAY
    phone.location = (0, -0.62, 1.12) if t < E["D"] + 0.2 else AWAY
    if t < E["D"]:
        place(CHAD, BED.x, BED.y, face=(0, -1), z=-0.15)
        pose(CHAD, sit=True, arms=(-1.1, -1.1))
        return
    if t >= E["H"] - 0.5:
        place(CHAD, MINE_POS.x, MINE_POS.y, face=(1, 0))
        pose(CHAD, arms=(-0.3, arm_swing(t)))
        return
    dist = min(WALK_LEN, (t - E["D"]) * WALK_SPEED)
    p, d = chad_walk(dist)
    place(CHAD, p.x, p.y, face=(d.x, d.y) if dist < WALK_LEN else (1, 0))
    walking = dist < WALK_LEN
    pose(CHAD, walk=1.0 if walking else 0.0, phase=(t - E["D"]) * 13.0)

room_ld = bpy.data.lights.new("room", "POINT"); room_ld.energy = 120.0; room_ld.color = (1.0, 0.75, 0.45); room_ld.shadow_soft_size = 0.5
B.link(bpy.data.objects.new("room", room_ld)).location = (-19.0, 13.2, 3.2)
phone_ld = bpy.data.lights.new("phone_glow", "POINT"); phone_ld.energy = 6.0; phone_ld.color = (0.6, 0.8, 1.0); phone_ld.shadow_soft_size = 0.1
phone_light = B.link(bpy.data.objects.new("phone_glow", phone_ld)); phone_light.parent = phone; phone_light.location = (0, -0.12, 0.1)
BED_OB = boxes("bed", [((-0.5, 0.5, -1.0, 1.0, 0, 0.56), colmat((0.6, 0.05, 0.04), 0.8)),
                       ((-0.5, 0.5, 0.55, 1.0, 0.56, 0.62), colmat((0.9, 0.9, 0.88), 0.8))], (-20.5, 12.5, 0), None)

# ------------------------------------------------------------------ the timeline

PLAZA_SPAWNS = SA.plaza_spawns(E)

def plaza_level(t):
    if t < E["sixteen"] + 0.25:
        return 1.0
    if t < T_CROSS:
        return 1.0 - ramp(t, E["sixteen"] + 0.25, E["sixteen"] + 0.55)
    return ramp(t, T_CROSS, T_CROSS + 0.3)

def club_level(t):
    if t < E["fails"]:
        return 0.7 + 0.3 * math.sin(t * 23.0)
    if t < E["dead"]:
        return 0.35 * (1 - ramp(t, E["fails"], E["dead"]))
    return 0.0

def apply_state(t):
    sky_state(t)
    alive = t < T_BREAK
    shake = 0.04 if any(0 <= t - h < 0.12 for h in HITS) else 0.0
    spawner_state(SPAWNER, t, plaza_level(t), alive, shake)
    spawner_state(CLUB_SPAWNER, t, club_level(t), True)
    chad_state(t)
    for k, f in enumerate(PLAZA_STACIES):
        if t >= PLAZA_SPAWNS[k] + 0.1:
            x, y = PLAZA_POS[k]
            place(f, x, y, face=(-x, -y))
            pose(f)
        else:
            hide(f)
    for f, (x, y) in SPOT_STACIES:
        if t >= E["G"] - 0.3:
            place(f, x, y, face=(0, -1))
            pose(f)
        else:
            hide(f)
    club_on = E["E"] - 0.6 <= t < E["G"] - 0.1
    for k, f in enumerate(CLUB_STACIES):
        if club_on:
            a = 2 * math.pi * k / 6 + 0.3
            x, y = CLUB_SP.x + 1.7 * math.cos(a), CLUB_SP.y + 1.7 * math.sin(a)
            place(f, x, y, face=(CLUB_SP.x - x, CLUB_SP.y - y))
            pose(f)
        else:
            hide(f)
    for k, f in enumerate(CLUB_CHADS):
        if club_on:
            a = math.pi * (0.12 + 0.76 * k / 7)
            x, y = CLUB_SP.x + 3.3 * math.cos(a), CLUB_SP.y + 3.3 * math.sin(a)
            place(f, x, y, face=(CLUB_SP.x - x, CLUB_SP.y - y))
            pose(f, arms=(-0.2 - 0.15 * math.sin(t * 3 + k), -0.2))
        else:
            hide(f)
    # poofs: four spawns in the plaza, the failed spawn at the club
    events = [(PLAZA_SPAWNS[k], Vector((PLAZA_POS[k][0], PLAZA_POS[k][1], 1.0))) for k in range(4)]
    events.append((E["fails"], CLUB_SP + Vector((0, 0, 0.6))))
    for parts, (t0, origin) in zip(POOFS, events):
        poof_state(parts, t, t0, origin)
    # the 16-block ring and radius line
    g = ramp(t, E["sixteen"], E["sixteen"] + 0.7)
    vis = E["sixteen"] <= t < E["D_end"]
    s = max(0.001, g)
    ring.location = (SP.x, SP.y, 0.08) if vis else AWAY
    ring.scale = (s, s, 1)
    radius.location = (SP.x, SP.y, 0.08) if vis else AWAY
    radius.scale = (s, 1, 1)
    radius.rotation_euler = (0, 0, math.atan2(d_house.y, d_house.x))
    flash = math.exp(-max(0.0, t - T_CROSS) * 4) if t >= T_CROSS else 0.0
    B.bsdf(RING_M).inputs["Emission Strength"].default_value = 2.5 + 10.0 * flash
    # the break: debris and XP orbs
    for ob, v, size in DEBRIS:
        u = t - T_BREAK
        if 0 <= u < 1.6:
            p = SP + v * u * 1.3 + Vector((0, 0, -4.9 * u * u))
            p.z = max(0.08, p.z)
            ob.location = p
            ob.scale = (size,) * 3
            ob.rotation_euler = (u * 7 * v.x, u * 6 * v.y, 0)
        else:
            ob.location = AWAY
    chad_body = Vector((MINE_POS.x, MINE_POS.y, 1.1))
    for k, (ob, v) in enumerate(XP):
        u = t - T_BREAK - 0.15
        if 0 <= u < 1.4:
            burst = SP + v * min(u, 0.35) * 2.2
            home = smooth01((u - 0.45) / 0.8)
            ob.location = burst.lerp(chad_body, home) + Vector((0, 0, 0.15 * math.sin(u * 9 + k)))
            sc = 1.0 - smooth01((u - 1.15) / 0.25)
            ob.scale = (sc + 0.001,) * 3
        else:
            ob.location = AWAY
    pickaxe_glint = 0.25 + 0.2 * math.sin(t * 9)
    B.bsdf(DIAMOND).inputs["Emission Strength"].default_value = pickaxe_glint
    loc, target, fstop = camera_at(t)
    B.aim(cam, loc, target)
    cam.data.dof.focus_distance = (target - loc).length
    cam.data.dof.aperture_fstop = fstop
    cam.data.clip_start = 0.05
    cam.data.clip_end = 400

# ------------------------------------------------------------------ camera

def shot_hook(t):
    return SP + Vector((0, 0, 0.0)), 2.9 - 0.25 * min(1, t / 4), -100 + 5 * t, 13
def shot_wide(t):
    return Vector((-3.0, 1.5, 0.0)), 84.0, -100 + 1.2 * (t - E["B"]), 50
def shot_room(t):
    return Vector((-19.8, 12.3, 1.1)), 7.0, -86 + 1.0 * (t - E["C"]), 16
def shot_walk(t):
    p = CHAD["root"].location
    plaza = Vector((0.0, 0.5, 0.8))
    chad = Vector((p.x, p.y, 1.0))
    return chad.lerp(plaza, 0.5), max(17.0, 1.6 * (chad - plaza).length + 8.0), -112, 55
def shot_club(t):
    return Vector((14.6, 0.6, 1.2)), 12.5 - 0.15 * (t - E["E"]), 205 + 1.5 * (t - E["E"]), 17
TOUR = [("G", Vector((1.0, -2.0, 1.0))), ("coffee", Vector((9.5, -8.0, 1.5))), ("libraries", Vector((-9.8, -8.5, 1.8))),
        ("farmers", Vector((8.6, 7.0, 1.2)))]
def shot_tour(t):
    target = TOUR[0][1]
    for (k0, p0), (k1, p1) in zip(TOUR, TOUR[1:]):
        target = target.lerp(p1, ramp(t, E[k1] - 0.45, E[k1] + 0.1)) if t >= E[k1] - 0.45 else target
    return target, 19.0, -95 + 2.0 * (t - E["G"]), 30
def shot_mine(t):
    return Vector((-0.45, 0.5, 1.0)), 5.6 - 0.25 * min(1, (t - E["H"]) / 3), -70 + 2.0 * (t - E["H"]), 10

SHOTS = [(shot_hook, None), (shot_wide, (E["B"] - 0.3, E["B"] + 1.1)), (shot_room, (E["C"] - 0.5, E["C"] + 0.5)),
         (shot_walk, (E["D"] - 0.1, E["D"] + 1.0)), (shot_club, (E["E"] - 0.45, E["E"] + 0.55)),
         (shot_tour, (E["G"] - 0.45, E["G"] + 0.55)), (shot_mine, (E["H"] - 0.45, E["H"] + 0.4))]

def orbit(target, dist, az, el):
    az, el = math.radians(az), math.radians(el)
    return target + dist * Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))

def camera_at(t):
    k = 0
    for n, (fn, win) in enumerate(SHOTS):
        if win and t >= win[0]:
            k = n
    fn, win = SHOTS[k]
    tg, d, az, el = fn(t)
    if win and t < win[1] and k > 0:
        tg0, d0, az0, el0 = SHOTS[k - 1][0](t)
        u = smooth01((t - win[0]) / (win[1] - win[0]))
        while az - az0 > 180:
            az -= 360
        while az - az0 < -180:
            az += 360
        tg = tg0.lerp(tg, u)
        d = math.exp(math.log(d0) * (1 - u) + math.log(d) * u)
        az = az0 + (az - az0) * u
        el = el0 + (el - el0) * u
    fstop = 2.2 if d < 10 else (1.4 if d < 40 else 1.0)
    return orbit(tg, d, az, el), tg, fstop

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    names = ("ring", "chad", "plaza", "club_spawner", "cafe", "library", "market", "pickaxe")
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        loc, _, _ = camera_at(t)
        az = math.atan2(loc.y - SP.y, loc.x - SP.x)
        head = CHAD["root"].matrix_world @ Vector((0, 0, 2.05))
        pts = {
            "ring": Vector((SP.x + 16 * math.cos(az), SP.y + 16 * math.sin(az), 0.1)),
            "chad": head,
            "plaza": Vector((4.9, -3.9, 0.05)),
            "club_spawner": CLUB_SP + Vector((0, 0, 0.55)),
            "cafe": Vector((9.5, -10.0, 4.1)),
            "library": Vector((-10.0, -11.0, 6.1)),
            "market": Vector((9.0, 8.0, 3.1)),
            "pickaxe": pickaxe.matrix_world @ Vector((0, 0, -1.3)),
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
