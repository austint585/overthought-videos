"""Blender scene for 'The dots on your microwave door': a voxel kitchen, a microwave on the counter whose lid lifts off
to show the magnetron and cavity, 12.2 cm waves at true scale bouncing off the metal, water molecules shaking in the
soup, the perforated door (holes enlarged for the camera), the two door switches, and a guy watching his food.
Built in code and timed to the narration (voxel helpers as in pharmacy_scene.py).

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
rng = random.Random(9)
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
    "floor": pixel_mat("floor", [(0.80, 0.78, 0.74), (0.84, 0.82, 0.78), (0.76, 0.74, 0.70)], rough=0.35,
                       lines=((2, 2, 2), (0.5, 0.5, 0.5))),
    "wall": pixel_mat("wall", [(0.62, 0.78, 0.74), (0.66, 0.82, 0.78), (0.58, 0.74, 0.70)], rough=0.3,
                      lines=((4, 4, 4), (0.85, 0.88, 0.86))),
    "ceiling": pixel_mat("ceiling", [(0.92, 0.92, 0.90), (0.95, 0.95, 0.93)]),
}

# ------------------------------------------------------------------ voxel kitchen shell (half-meter voxels)

GRID = {}

def fill(i0, i1, j0, j1, k0, k1, mat):
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            for k in range(k0, k1 + 1):
                GRID[(i, j, k)] = mat

fill(-8, 7, -6, 4, -1, -1, "floor")
fill(-9, -9, -6, 4, 0, 5, "wall")
fill(8, 8, -6, 4, 0, 5, "wall")
fill(-9, 8, 4, 4, 0, 5, "wall")
fill(-9, 8, -6, 4, 6, 6, "ceiling")


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


shell = voxel_mesh("kitchen", GRID)
shell.scale = (0.5, 0.5, 0.5)

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

def mesh_mat(name, pitch=0.005, hole=0.36):
    """Black perforated metal: round holes on a square grid (object coordinates, x-z plane), cut out with alpha."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (0.02, 0.02, 0.025, 1)
    p.inputs["Metallic"].default_value = 0.6
    p.inputs["Roughness"].default_value = 0.4
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sc = nt.nodes.new("ShaderNodeVectorMath"); sc.operation = "SCALE"; sc.inputs["Scale"].default_value = 1.0 / pitch
    nt.links.new(tc.outputs["Object"], sc.inputs[0])
    fr = nt.nodes.new("ShaderNodeVectorMath"); fr.operation = "FRACTION"
    nt.links.new(sc.outputs[0], fr.inputs[0])
    sub = nt.nodes.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    nt.links.new(fr.outputs[0], sub.inputs[0])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sub.outputs[0], sep.inputs[0])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(sep.outputs["X"], comb.inputs["X"]); nt.links.new(sep.outputs["Z"], comb.inputs["Y"])
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; nt.links.new(comb.outputs[0], ln.inputs[0])
    gt = nt.nodes.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = hole / 2
    nt.links.new(ln.outputs["Value"], gt.inputs[0])
    nt.links.new(gt.outputs[0], p.inputs["Alpha"])
    try:
        m.surface_render_method = "DITHERED"
    except Exception:
        m.blend_method = "HASHED"
    return m

SHELLM = colmat((0.08, 0.08, 0.09), 0.35, metallic=0.8)
INNER = colmat((0.72, 0.72, 0.70), 0.35, metallic=0.9)
BLACK = colmat((0.02, 0.02, 0.025), 0.5)
COPPER = colmat((0.85, 0.42, 0.22), 0.3, metallic=1.0)
WHITE = colmat((0.95, 0.95, 0.93), 0.4)

# counter along the back wall: cabinets, a stone top, a backsplash shelf
boxes("counter", [((-3.0, 3.0, 1.0, 1.65, 0.0, 0.88), colmat((0.55, 0.36, 0.20), 0.6)),
                  ((-3.0, 3.0, 0.98, 1.67, 0.88, 0.92), colmat((0.15, 0.15, 0.17), 0.25)),
                  ((-3.0, 3.0, 0.99, 1.0, 0.05, 0.85), colmat((0.45, 0.28, 0.15), 0.6))] +
      [((x - 0.02, x + 0.02, 0.97, 0.99, 0.6, 0.75), colmat((0.8, 0.8, 0.8), 0.3, metallic=1.0)) for x in (-1.2, -0.6, 0.6, 1.2)],
      (0, 0, 0))
boxes("kettle", [((-0.09, 0.09, -0.09, 0.09, 0.0, 0.22), colmat((0.85, 0.2, 0.15), 0.3)),
                 ((-0.02, 0.02, -0.12, -0.09, 0.12, 0.18), BLACK)], (0.75, 1.3, 0.92))
boxes("jar", [((-0.06, 0.06, -0.06, 0.06, 0.0, 0.16), colmat((0.9, 0.85, 0.6), 0.5))], (-0.7, 1.4, 0.92))

# the microwave: 60 x 42 x 35 cm on the counter, door on the left, control panel on the right
MW = Vector((0.0, 1.05, 0.92))          # front-left-bottom corner reference: x center, front face y, counter z
X0, X1, XP = -0.30, 0.30, 0.12          # outer left/right, partition between cavity and controls
Y0, Y1 = 1.05, 1.47
Z0, Z1 = 0.92, 1.27
T = 0.012
CX0, CX1, CY0, CY1, CZ0, CZ1 = X0 + 0.03, XP - 0.01, Y0 + 0.03, Y1 - 0.03, Z0 + 0.03, Z1 - 0.03
boxes("mw_body", [((X0, X1, Y0 + 0.02, Y1, Z0, Z0 + 0.03), SHELLM),                         # floor
                  ((X0, X0 + 0.03, Y0 + 0.02, Y1, Z0, Z1), SHELLM),                         # left side
                  ((X0, X1, Y1 - 0.03, Y1, Z0, Z1), SHELLM),                                # back
                  ((X1 - 0.02, X1, Y0 + 0.02, Y1, Z0, Z1), SHELLM),                         # right side
                  ((CX0, CX1, CY0, CY1, CZ0, CZ0 + 0.002), INNER),                          # cavity lining
                  ((CX0, CX0 + 0.002, CY0, CY1, CZ0, CZ1), INNER),
                  ((CX0, CX1, CY1 - 0.002, CY1, CZ0, CZ1), INNER),
                  ((XP - 0.012, XP, Y0 + 0.02, Y1 - 0.03, Z0, Z1), INNER),                  # partition
                  ((XP, X1, Y0, Y0 + 0.025, Z0, Z1), colmat((0.12, 0.12, 0.13), 0.3)),     # control panel
                  ((XP + 0.03, X1 - 0.03, Y0 - 0.002, Y0, Z1 - 0.09, Z1 - 0.04), colmat((0.1, 0.9, 0.5), 0.3, emit=4.0)),
                  ] + [((XP + 0.035 + 0.04 * (k % 3), XP + 0.065 + 0.04 * (k % 3), Y0 - 0.004, Y0,
                         Z1 - 0.13 - 0.035 * (k // 3), Z1 - 0.105 - 0.035 * (k // 3)), colmat((0.7, 0.7, 0.72), 0.4))
                       for k in range(9)], (0, 0, 0))
LID = boxes("mw_lid", [((X0, X1, Y0 + 0.02, Y1, Z1 - 0.02, Z1), SHELLM),
                       ((CX0, CX1, CY0, CY1, CZ1 - 0.002, CZ1), INNER)], (0, 0, 0))
# magnetron in the control bay, with its waveguide feeding the cavity through the partition
MAG = boxes("magnetron", [((-0.05, 0.05, -0.06, 0.06, -0.05, 0.05), COPPER)] +
            [((-0.06, 0.06, -0.065, 0.065, z, z + 0.006), colmat((0.75, 0.75, 0.78), 0.3, metallic=1.0)) for z in (-0.04, -0.02, 0.0, 0.02, 0.04)] +
            [((-0.015, 0.015, -0.015, 0.015, 0.05, 0.08), colmat((0.9, 0.5, 0.2), 0.3, emit=0.0))],
            (0.20, 1.30, 1.08))
GUIDE = boxes("waveguide", [((XP - 0.01, 0.16, -0.04, 0.04, 1.17, 1.22), INNER)], (0, 1.30, 0))
MAG_GLOW = colmat((1.0, 0.35, 0.05), 0.3, emit=0.0)
MAG_CORE = boxes("magcore", [((-0.035, 0.035, -0.035, 0.035, 0.05, 0.053), MAG_GLOW)], (0.20, 1.30, 1.08))

# turntable, bowl of soup, water molecules
TT = Vector(((CX0 + CX1) / 2, (CY0 + CY1) / 2, CZ0 + 0.003))
TURN = B.link(bpy.data.objects.new("turn", None))
TURN.location = TT
plate = B.mesh_from("plate", B.cyl_z(0.13, 0.0, 0.008, 0, 0, seg=48), [colmat((0.85, 0.9, 0.9), 0.05)])
plate.parent = TURN
bowl = B.mesh_from("bowl", B.many(B.with_material(B.cyl_z(0.075, 0.008, 0.06, 0.03, 0, seg=40, r2=0.09), 0),
                                  B.with_material(B.cyl_z(0.078, 0.045, 0.05, 0.03, 0, seg=40), 1)),
                   [WHITE, colmat((0.9, 0.45, 0.1), 0.3)])
bowl.parent = TURN
SOUP_HEAT = bowl.data.materials[1]
MOLS = []
for k in range(7):
    a = k * 2 * math.pi / 7
    mol = boxes(f"mol{k}", [((-0.008, 0.008, -0.008, 0.008, -0.008, 0.008), colmat((0.9, 0.12, 0.1), 0.4, emit=0.5)),
                            ((0.008, 0.018, -0.005, 0.005, 0.0, 0.01), WHITE), ((-0.018, -0.008, -0.005, 0.005, 0.0, 0.01), WHITE)],
                AWAY)
    MOLS.append((mol, a))

# door: hinge on the left, perforated window, two latch hooks on the right edge
DOOR = B.link(bpy.data.objects.new("door", None))
DOOR.location = (X0, Y0, Z0)
DW, DH = XP - X0, Z1 - Z0
boxes("door_frame", [((0.0, DW, -0.03, 0.0, 0.0, 0.035), BLACK), ((0.0, DW, -0.03, 0.0, DH - 0.035, DH), BLACK),
                     ((0.0, 0.035, -0.03, 0.0, 0.0, DH), BLACK), ((DW - 0.05, DW, -0.03, 0.0, 0.0, DH), BLACK),
                     ((DW - 0.04, DW - 0.02, -0.045, -0.03, 0.06, DH - 0.06), colmat((0.6, 0.6, 0.62), 0.3, metallic=1.0)),
                     ((DW - 0.03, DW - 0.005, 0.0, 0.03, DH - 0.09, DH - 0.07), colmat((0.6, 0.6, 0.62), 0.3, metallic=1.0)),
                     ((DW - 0.03, DW - 0.005, 0.0, 0.03, 0.07, 0.09), colmat((0.6, 0.6, 0.62), 0.3, metallic=1.0))],
      (0, 0, 0), DOOR)
MESH = B.mesh_from("door_mesh", B.box(0.035, DW - 0.05, -0.016, -0.014, 0.035, DH - 0.035), [mesh_mat("mesh")])
MESH.parent = DOOR
# the two interlock switches on the partition face, where the latch hooks land
SW_OFF, SW_ON = colmat((0.25, 0.25, 0.27), 0.4), colmat((1.0, 0.08, 0.05), 0.3, emit=6.0)
SW = [boxes(f"sw{k}", [((-0.012, 0.012, 0.0, 0.02, -0.01, 0.01), SW_OFF)], (XP - 0.02, Y0 + 0.002, z))
      for k, z in enumerate((Z0 + DH - 0.08, Z0 + 0.08))]

# the waves: chains of small glowing cubes along a sine, true scale (wavelength 12.2 cm), bouncing off the metal
WAVEM = colmat((1.0, 0.3, 0.02), 0.4, emit=12.0)
LAM = 0.122
N_DOT = 34
def wave_chain(name):
    me = B.mesh_from(name, B.box(-0.0035, 0.0035, -0.0035, 0.0035, -0.0035, 0.0035), [WAVEM])
    obs = [me] + [bpy.data.objects.new(f"{name}_{k}", me.data) for k in range(1, N_DOT)]
    for ob in obs[1:]:
        B.link(ob)
    for ob in obs:
        ob.location = AWAY
    return obs
WAVES = [wave_chain(f"wave{k}") for k in range(3)]
LIGHTM = colmat((1.0, 0.95, 0.6), 0.4, emit=25.0)
PHOT = []
pm = B.mesh_from("phot", B.box(-0.003, 0.003, -0.003, 0.003, -0.003, 0.003), [LIGHTM])
PHOT.append(pm)
for k in range(1, 40):
    ob = bpy.data.objects.new(f"phot{k}", pm.data); B.link(ob); PHOT.append(ob)
for ob in PHOT:
    ob.location = AWAY

# ------------------------------------------------------------------ the guy

def person(name, shirt, pants, skin, hair):
    root = B.link(bpy.data.objects.new(name, None))
    S, P, Sk, H = colmat(shirt, 0.7), colmat(pants, 0.7), colmat(skin), colmat(hair, 0.8)
    D, Shoe = colmat((0.03, 0.02, 0.02), 0.4), colmat((0.15, 0.15, 0.17), 0.5)
    f = {"root": root}
    for side, x in (("L", -0.125), ("R", 0.125)):
        f["leg" + side] = boxes(f"{name}_leg{side}", [((-0.125, 0.125, -0.125, 0.125, -0.75, 0.0), P),
                                                      ((-0.13, 0.13, -0.17, 0.13, -0.75, -0.66), Shoe)], (x, 0, 0.75), root)
    f["body"] = boxes(f"{name}_body", [((-0.25, 0.25, -0.125, 0.125, 0, 0.75), S)], (0, 0, 0.75), root)
    for side, x in (("L", -0.375), ("R", 0.375)):
        f["arm" + side] = boxes(f"{name}_arm{side}", [((-0.125, 0.125, -0.125, 0.125, -0.35, 0.0), S),
                                                      ((-0.11, 0.11, -0.11, 0.11, -0.78, -0.35), Sk)], (x, 0, 1.5), root)
    hp = [((-0.25, 0.25, -0.25, 0.25, 0, 0.5), Sk), ((-0.27, 0.27, -0.27, 0.27, 0.42, 0.58), H),
          ((-0.27, 0.27, 0.05, 0.28, 0.15, 0.5), H),
          ((-0.16, -0.06, -0.265, -0.25, 0.22, 0.29), D), ((0.06, 0.16, -0.265, -0.25, 0.22, 0.29), D),
          ((-0.08, 0.08, -0.262, -0.25, 0.07, 0.1), colmat((0.55, 0.30, 0.22)))]
    f["head"] = boxes(f"{name}_head", hp, (0, 0, 1.5), root)
    return f

GUY = person("guy", (0.95, 0.55, 0.15), (0.2, 0.25, 0.45), (0.70, 0.50, 0.36), (0.08, 0.05, 0.03))
GS = 0.85
GUY["root"].scale = (GS,) * 3
GUY["root"].location = (-0.15, 0.32, 0.0)
GUY["root"].rotation_euler = (0, 0, math.pi)          # facing +y, toward the microwave
EYE = lambda: GUY["head"].matrix_world @ Vector((0, -0.26, 0.26))

# ------------------------------------------------------------------ lights, world, camera

world = bpy.data.worlds.new("bg")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.06, 0.06, 0.065, 1)
B.area("ceil", Vector((0.0, 0.2, 2.9)), Vector((0.0, 1.0, 0.9)), 2.5, 260.0, (1.0, 0.95, 0.88))
key = B.area("key", Vector((1.4, -0.4, 1.9)), Vector((0.0, 1.2, 1.1)), 1.2, 60.0, (1.0, 0.93, 0.85))
rim = B.area("rim", Vector((-1.3, 0.4, 1.6)), Vector((0.0, 1.2, 1.1)), 1.0, 25.0, (0.6, 0.75, 1.0))
inside = bpy.data.lights.new("inside", "POINT")
inside.shadow_soft_size = 0.05
inside.color = (1.0, 0.85, 0.55)
INSIDE = B.link(bpy.data.objects.new("inside", inside))
INSIDE.location = ((CX0 + CX1) / 2, (CY0 + CY1) / 2 + 0.05, CZ1 - 0.03)

cam = B.camera(lens=35, fstop=2.8)
B.render_settings(FPS, samples=32, motion_blur=0.2)

# ------------------------------------------------------------------ motion

def ramp_in(t, t0, d=0.35):
    return ramp(t, t0 - d / 2, t0 + d / 2)

def bounce(s, a, b):
    L = b - a
    u = s % (2 * L)
    return a + (u if u < L else 2 * L - u)

def oven_on(t):
    """1 while cooking; off from the moment the door opens until it closes again for the ending."""
    return 1.0 - ramp_in(t, E["open"] + 0.05, 0.15) * (1 - ramp_in(t, E["J"] + 0.1, 0.4))

def lid_off(t):
    return ramp(t, E["B"] + 0.1, E["B"] + 0.7) * (1 - ramp(t, E["I"] - 0.4, E["I"] + 0.1))

def apply_state(t):
    on = oven_on(t)
    TURN.rotation_euler = (0, 0, 0.6 * t)
    lo = lid_off(t)
    LID.location = (0.0, 0.0, 0.5 * lo) if lo < 0.999 else AWAY
    LID.rotation_euler = (0, 0, 0)
    # door swings open on "open", shuts again at the start of the last line
    sw = ramp_in(t, E["open"], 0.5) * (1 - ramp_in(t, E["J"], 0.5))
    DOOR.rotation_euler = (0, 0, -1.5 * sw)
    for k, s in enumerate(SW):
        s.data.materials[0] = SW_ON if (sw > 0.05 and t > E["switches"] - 0.1) else SW_OFF
    MAG_GLOW.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 30.0 * on
    INSIDE.data.energy = 6.0 * max(on, 0.4 * sw)
    heat = ramp(t, E["water"], E["heat"] + 0.5)
    SOUP_HEAT.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 1.5 * heat * on
    SOUP_HEAT.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.3, 0.05, 1)
    # water molecules shaking above the soup (shown only on the water line)
    mshow = ramp_in(t, E["water"] - 0.1, 0.3) * (1 - ramp_in(t, E["E"] - 0.1, 0.3))
    for mol, a in MOLS:
        if mshow < 0.02:
            mol.location = AWAY
            continue
        r = 0.045
        mol.location = TT + Vector((0.03 + r * math.cos(a + 0.6 * t), r * math.sin(a + 0.6 * t), 0.075 + 0.01 * math.sin(t * 3 + a)))
        jig = (on * ramp_in(t, E["shake"], 0.3))
        mol.rotation_euler = (0.6 * jig * math.sin(t * 47 + a), 0.6 * jig * math.sin(t * 53 + 2 * a), a + 0.8 * jig * math.sin(t * 41))
        mol.scale = (mshow,) * 3
    # waves: two bounce left-right across the cavity, one front-back against the door
    wshow = on * ramp_in(t, E["magnetron"] + 0.4, 0.4)
    speed = 0.22
    for k, chain in enumerate(WAVES):
        for n, ob in enumerate(chain):
            if wshow < 0.02:
                ob.location = AWAY
                continue
            s = speed * t + 0.11 * k - n * (LAM * 1.5 / N_DOT)
            ph = 2 * math.pi * s / LAM
            if k < 2:
                x = bounce(s, CX0 + 0.01, CX1 - 0.01)
                y = CY0 + 0.12 + 0.12 * k
                z = (CZ0 + CZ1) / 2 + 0.035 + 0.02 * math.sin(ph)
            else:
                x = (CX0 + CX1) / 2 - 0.06
                y = bounce(s, Y0 + 0.004, CY1 - 0.01)
                z = (CZ0 + CZ1) / 2 + 0.02 * math.sin(ph)
            ob.location = (x, y, z)
            ob.scale = (wshow,) * 3
    # light: photons leave the soup, pass through the mesh and reach the guy's eye
    pshow = ramp_in(t, E["light"], 0.3) * (1 - ramp_in(t, E["I"] - 0.1, 0.3))
    eye = EYE()
    src = TT + Vector((0.03, 0, 0.06))
    for n, ob in enumerate(PHOT):
        if pshow < 0.02:
            ob.location = AWAY
            continue
        u = (t * 0.9 + n / len(PHOT)) % 1.0
        off = Vector((0.02 * math.sin(n * 2.3), 0.0, 0.015 * math.cos(n * 1.7)))
        ob.location = src.lerp(eye, u) + off * (1 - u)
        ob.scale = (pshow,) * 3
    guy_state(t)
    loc, target, fstop, lens = camera_at(t)
    B.aim(cam, loc, target)
    cam.data.lens = lens
    cam.data.dof.focus_distance = (target - loc).length
    cam.data.dof.aperture_fstop = fstop
    cam.data.clip_start = 0.01
    cam.data.clip_end = 100

def guy_state(t):
    h = GUY["head"]
    look = 0.35 + 0.05 * math.sin(t * 0.8)                         # looking down at the microwave
    jump = ramp_in(t, E["open"] + 0.1, 0.3) * (1 - ramp_in(t, E["J"], 0.4))
    h.rotation_euler = (-look * (1 - 0.6 * jump), 0, 0.05 * math.sin(t * 0.6))
    GUY["armL"].rotation_euler = (-0.15, 0, 0)
    GUY["armR"].rotation_euler = (-0.15 - 0.6 * jump, 0, 0)
    GUY["root"].location = (-0.15, 0.32 - 0.12 * jump, 0.0)

# ------------------------------------------------------------------ camera

def shot_hook(t):          # face-on to the door, close enough that the mesh dots read
    return Vector((-0.09, 0.62 + 0.03 * t, 1.13)), Vector((-0.09, 1.05, 1.1))
def shot_top(t):           # three-quarter from above as the lid lifts: magnetron, waveguide, cavity
    u = t - E["B"]
    return Vector((0.5 - 0.01 * u, 0.62, 1.75)), Vector((0.0, 1.27, 1.03))
def shot_wave(t):          # looking down into the cavity at the waves
    u = t - E["C"]
    return Vector((-0.12, 0.92 + 0.01 * u, 1.62)), Vector((-0.09, 1.27, 1.05))
def shot_food(t):
    u = t - E["D"]
    return Vector((-0.14 + 0.01 * u, 1.0, 1.58)), TT + Vector((0.02, 0.0, 0.04))   # high, over the front wall
def shot_walls(t):
    u = t - E["E"]
    return Vector((0.38 - 0.01 * u, 0.55, 1.62)), Vector((-0.06, 1.27, 1.03))
def shot_door(t):          # front-left and above: the door mesh and the wave hitting it from inside
    u = t - E["F"]
    return Vector((-0.55 + 0.01 * u, 0.62, 1.48)), Vector((-0.08, 1.12, 0.99))
def shot_eye(t):           # from the side: the guy on the left, light from the soup to his eyes
    u = t - E["H"]
    return Vector((1.3 - 0.01 * u, -0.9, 1.75)), Vector((-0.12, 0.75, 1.15))
def shot_open(t):
    u = t - E["I"]
    return Vector((0.72 - 0.01 * u, 0.42, 1.42)), Vector((0.0, 1.05, 1.08))
def shot_inside(t):        # pulled back: the guy watching the closed door
    u = t - E["J"]
    return Vector((1.25 + 0.01 * u, -1.0 - 0.02 * u, 1.8)), Vector((-0.12, 0.75, 1.15))

SHOTS = [(shot_hook, None), (shot_top, (E["B"] - 0.25, E["B"] + 0.25)), (shot_wave, (E["C"] - 0.25, E["C"] + 0.15)),
         (shot_food, (E["D"] - 0.25, E["D"] + 0.15)), (shot_walls, (E["E"] - 0.25, E["E"] + 0.15)),
         (shot_door, (E["F"] - 0.25, E["F"] + 0.15)), (shot_eye, (E["H"] - 0.25, E["H"] + 0.15)),
         (shot_open, (E["I"] - 0.25, E["I"] + 0.15)), (shot_inside, (E["J"] + 0.3, E["J"] + 0.35))]
LENS = {shot_hook: 32.0, shot_top: 30.0, shot_wave: 32.0, shot_food: 36.0, shot_walls: 30.0, shot_door: 34.0,
        shot_eye: 40.0, shot_open: 30.0, shot_inside: 38.0}

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
    fstop = 4.0 if d < 0.8 else (5.6 if d < 1.5 else 8.0)      # small subject: keep more of it sharp
    return loc, tg, fstop, lens

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    names = ("door", "mag", "food", "wall", "sw1", "sw2", "guy")
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        pts = {
            "door": MESH.matrix_world @ Vector((DW / 2, -0.016, DH / 2)),
            "mag": MAG.matrix_world @ Vector((0, 0, 0.06)),
            "food": TT + Vector((0.03, 0, 0.09)),
            "wall": Vector((CX0, (CY0 + CY1) / 2, (CZ0 + CZ1) / 2 + 0.06)),
            "sw1": SW[0].matrix_world @ Vector((0, 0, 0)),
            "sw2": SW[1].matrix_world @ Vector((0, 0, 0)),
            "guy": GUY["head"].matrix_world @ Vector((0, 0, 0.65)),
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
