"""Blender scene for 'The November 1st pharmacy hero': a voxel drugstore aisle with stocked shelves, ceiling light
panels and a pharmacy counter at the far end, a line of customers, a man in a red cape who walks up the aisle and
strikes a hero pose, and a security guard at the end. Built in code and timed to the narration.

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

MATS = {
    "floor": pixel_mat("floor", [(0.78, 0.78, 0.76), (0.82, 0.82, 0.80), (0.74, 0.74, 0.73)], rough=0.35,
                       lines=((1, 1, 1), (0.55, 0.55, 0.55))),
    "wall": pixel_mat("wall", [(0.80, 0.84, 0.86), (0.83, 0.87, 0.89), (0.77, 0.81, 0.83)]),
    "ceiling": pixel_mat("ceiling", [(0.88, 0.88, 0.86), (0.91, 0.91, 0.89)], lines=((1, 1, 1), (0.6, 0.6, 0.6))),
    "panel": solid("panel", (1.0, 1.0, 0.97), emit=6.0),
    "red": pixel_mat("red", [(0.75, 0.06, 0.06), (0.80, 0.08, 0.08), (0.70, 0.05, 0.05)]),
    "glass": solid("glass", (0.75, 0.85, 1.0), rough=0.1, emit=1.2),
}

# ------------------------------------------------------------------ voxel pharmacy: one long aisle toward the counter

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
fill(-6, 5, -4, 16, -1, -1, "floor")
fill(-7, -7, -4, 16, 0, ZC - 1, "wall")
fill(6, 6, -4, 16, 0, ZC - 1, "wall")
fill(-7, 6, 16, 16, 0, ZC - 1, "wall")
fill(-7, 6, -4, 16, ZC, ZC, "ceiling")
fill(-7, 6, 16, 16, 3, 3, "red")                  # red band on the back wall
for j in (0, 4, 8, 12):
    fill(-1, 0, j, j + 1, ZC, ZC, "panel")         # ceiling light panels
fill(-6, -4, 16, 16, 0, 2, "glass")               # front doors (left) seen down the aisle
fill(4, 5, 16, 16, 0, 2, "glass")

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

# shelves: two runs facing the aisle (x from -1.5 to 1.5 is the aisle), stocked with little boxes
PROD = [colmat(c, 0.5) for c in ((0.85, 0.25, 0.55), (0.25, 0.55, 0.85), (0.95, 0.75, 0.2), (0.3, 0.75, 0.45),
                                 (0.95, 0.95, 0.95), (0.55, 0.35, 0.8), (0.95, 0.5, 0.2))]
SHELF = colmat((0.92, 0.92, 0.94), 0.4)
for side, x0 in (("L", -3.4), ("R", 1.6)):
    parts = [((x0, x0 + 1.8, 0.0, 12.0, 0.0, 0.25), colmat((0.25, 0.27, 0.32), 0.5)),
             ((x0 + (0.0 if side == "R" else 1.6), x0 + (0.2 if side == "R" else 1.8), 0.0, 12.0, 0.0, 2.6), SHELF)]
    for lvl in range(4):
        z = 0.25 + 0.6 * lvl
        parts.append(((x0, x0 + 1.8, 0.0, 12.0, z, z + 0.05), SHELF))
        y = 0.1
        while y < 11.8:
            wdt = 0.18 + rng.random() * 0.2
            hgt = 0.2 + rng.random() * 0.25
            dep = 0.5 + rng.random() * 0.4
            xa = x0 + 1.75 - dep if side == "L" else x0 + 0.25
            parts.append(((xa, xa + dep, y, y + wdt, z + 0.05, z + 0.05 + hgt), PROD[rng.randrange(len(PROD))]))
            y += wdt + 0.02
    boxes(f"shelf{side}", parts, (0, 0, 0))
# aisle sign hanging over the aisle
boxes("sign", [((-1.0, 1.0, -0.03, 0.03, 0.0, 0.45), colmat((0.10, 0.35, 0.75), 0.4, emit=0.6)),
               ((-0.02, 0.02, -0.02, 0.02, 0.45, 1.3), colmat((0.6, 0.6, 0.6), 0.4))], (0.0, 3.0, 3.5))
# pharmacy counter across the far end
boxes("counter", [((-2.8, 2.8, -0.4, 0.4, 0.0, 1.05), colmat((0.95, 0.95, 0.95), 0.4)),
                  ((-2.8, 2.8, -0.42, -0.38, 0.6, 0.9), colmat((0.80, 0.08, 0.08), 0.5)),
                  ((-2.9, 2.9, -0.45, 0.45, 1.05, 1.12), colmat((0.35, 0.36, 0.40), 0.4))], (0.0, 14.2, 0.0))

# ------------------------------------------------------------------ figures

def person(name, shirt, pants, skin, hair, long_hair=False, cape=None):
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
          ((-0.27, 0.27, 0.05, 0.28, 0.15 if not long_hair else -0.35, 0.5), H),
          ((-0.16, -0.06, -0.265, -0.25, 0.22, 0.29), D), ((0.06, 0.16, -0.265, -0.25, 0.22, 0.29), D),
          ((-0.08, 0.08, -0.262, -0.25, 0.07, 0.1), colmat((0.55, 0.30, 0.22)))]
    if long_hair:
        hp += [((-0.28, -0.22, -0.2, 0.28, -0.35, 0.5), H), ((0.22, 0.28, -0.2, 0.28, -0.35, 0.5), H)]
    f["head"] = boxes(f"{name}_head", hp, (0, 0, 1.5), root)
    if cape:
        f["cape"] = boxes(f"{name}_cape", [((-0.3, 0.3, 0.0, 0.05, -1.25, 0.0), colmat(cape, 0.7))], (0, 0.14, 0.73), f["body"])
    return f

SCALE = 1.1
HERO = person("hero", (0.95, 0.95, 0.95), (0.08, 0.08, 0.10), (0.45, 0.30, 0.20), (0.05, 0.04, 0.03), cape=(0.80, 0.06, 0.06))
boxes("logo", [((-0.14, 0.14, -0.135, -0.125, 0.4, 0.64), colmat((0.85, 0.08, 0.08), 0.5)),
               ((-0.09, 0.09, -0.14, -0.13, 0.46, 0.58), colmat((1.0, 0.8, 0.1), 0.5))], (0, 0, 0), HERO["body"])
HERO["root"].scale = (SCALE,) * 3
LINE = []
LOOKS = [((0.85, 0.25, 0.45), (0.15, 0.15, 0.2), (0.86, 0.64, 0.5), (0.85, 0.65, 0.25)),
         ((0.15, 0.15, 0.17), (0.25, 0.3, 0.55), (0.55, 0.38, 0.26), (0.08, 0.05, 0.03)),
         ((0.95, 0.6, 0.15), (0.12, 0.12, 0.14), (0.92, 0.72, 0.6), (0.45, 0.22, 0.08)),
         ((0.55, 0.75, 0.95), (0.85, 0.85, 0.85), (0.70, 0.50, 0.36), (0.1, 0.07, 0.05)),
         ((0.3, 0.7, 0.4), (0.15, 0.15, 0.2), (0.86, 0.66, 0.52), (0.95, 0.85, 0.55)),
         ((0.75, 0.2, 0.2), (0.1, 0.1, 0.15), (0.45, 0.30, 0.20), (0.04, 0.03, 0.03))]
for n, (sh, pa, sk, ha) in enumerate(LOOKS):
    p = person(f"q{n}", sh, pa, sk, ha, long_hair=True)
    p["root"].scale = (1.02,) * 3
    LINE.append(p)
CLERK = person("clerk", (0.95, 0.95, 0.97), (0.2, 0.2, 0.25), (0.86, 0.66, 0.52), (0.3, 0.2, 0.1))
CLERK["root"].location = (0.6, 15.0, 0.0)
CLERK["root"].rotation_euler = (0, 0, 0)
GUARD = person("guard", (0.08, 0.08, 0.10), (0.08, 0.08, 0.10), (0.70, 0.50, 0.36), (0.05, 0.04, 0.03))
boxes("badge", [((0.08, 0.18, -0.135, -0.125, 0.5, 0.62), colmat((0.95, 0.8, 0.2), 0.3, emit=0.5))], (0, 0, 0), GUARD["body"])
GUARD["root"].scale = (1.15,) * 3

# ------------------------------------------------------------------ lights, world, camera

world = bpy.data.worlds.new("bg")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.05, 0.06, 1)
for k, j in enumerate((1.0, 5.0, 9.0, 13.0)):
    B.area(f"panel{k}", Vector((0.0, j, ZC - 0.05)), Vector((0.0, j, 0)), 1.8, 260.0, (0.95, 0.97, 1.0))
key = B.area("key", Vector((1.5, -2.0, 3.0)), Vector((0.0, 4.0, 1.2)), 2.5, 140.0, (1.0, 0.96, 0.9))
hero_l = B.area("herol", Vector((0.6, 2.5, 2.6)), Vector((0.0, 6.0, 1.2)), 2.0, 0.0, (1.0, 0.75, 0.4))
siren = B.area("siren", Vector((0.0, 8.0, 4.6)), Vector((0.0, 8.0, 0)), 3.0, 0.0, (0.2, 0.3, 1.0))

cam = B.camera(lens=30, fstop=2.8)
B.render_settings(FPS, samples=32, motion_blur=0.3)

# ------------------------------------------------------------------ motion

def place(f, p, face=(0, -1)):
    f["root"].location = p
    f["root"].rotation_euler = (0, 0, math.atan2(face[0], -face[1]))

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

HERO_A, HERO_B = Vector((0.0, 0.6, 0.0)), Vector((0.0, 6.0, 0.0))     # walks away from camera up the aisle
QUEUE0 = Vector((0.5, 13.3, 0.0))

def hero_state(t):
    walk_u = ramp(t, 0.0, E["D"] - 0.2)
    pose_u = ramp_in(t, E["H"], 0.5)                       # hands on hips, chest out
    p = HERO_A.lerp(HERO_B, walk_u)
    walking = 0.02 < walk_u < 0.98
    face = (0, 1) if walking else (0, -1) if t > E["D"] else (0, 1)
    turn = ramp_in(t, E["D"] - 0.1, 0.5)
    ang = math.pi * (1 - turn) if t < E["D"] + 0.3 else 0.0
    HERO["root"].location = p
    HERO["root"].rotation_euler = (0, 0, ang)
    hips = ((0.3, 0, -0.9 * pose_u), (0.3, 0, 0.9 * pose_u))
    pose(HERO, walk=1.0 if walking else 0.0, phase=t * 7.5, arms=hips if pose_u > 0.05 else None,
         head_nod=-0.15 * pose_u)
    flap = 0.35 + 0.15 * math.sin(t * 9) if walking else 0.08 + 0.05 * math.sin(t * 2)
    HERO["cape"].rotation_euler = (flap, 0, 0)

def line_state(t):
    for n, p in enumerate(LINE):
        q = QUEUE0 + Vector((0.0 if n % 2 == 0 else -0.15, -0.85 * n, 0))
        p["root"].location = q
        p["root"].rotation_euler = (0, 0, math.pi)          # facing the counter
        pose(p, arms=((0.05 * math.sin(t + n), 0, 0), (0.05 * math.sin(t * 1.3 + n), 0, 0)),
             head_nod=0.05 * math.sin(t * 0.7 + n))
    CLERK["root"].location = (0.6, 15.0, 0.0)
    pose(CLERK, head_turn=0.1 * math.sin(t * 0.5))

def guard_state(t):
    if t < E["K"] - 0.4:
        GUARD["root"].location = AWAY
        return
    u = ramp(t, E["K"] - 0.4, E["K"] + 1.4)
    p = Vector((-1.0, -1.5, 0.0)).lerp(Vector((-0.6, 6.4, 0.0)), u)
    GUARD["root"].location = p
    GUARD["root"].rotation_euler = (0, 0, math.pi)
    pose(GUARD, walk=1.0 if u < 0.99 else 0.0, phase=t * 8.0)

def apply_state(t):
    hero_state(t)
    line_state(t)
    guard_state(t)
    hero_l.data.energy = 25.0 * ramp_in(t, E["H"], 0.5) * (1 - ramp_in(t, E["J"], 0.4))
    s = ramp_in(t, E["K"], 0.3)
    siren.data.energy = 500.0 * s * (0.5 + 0.5 * math.sin(t * 12))
    siren.data.color = (0.2, 0.3, 1.0) if math.sin(t * 6) > 0 else (1.0, 0.15, 0.15)
    loc, target, fstop, lens = camera_at(t)
    B.aim(cam, loc, target)
    cam.data.lens = lens
    cam.data.dof.focus_distance = (target - loc).length
    cam.data.dof.aperture_fstop = fstop
    cam.data.clip_start = 0.05
    cam.data.clip_end = 200

# ------------------------------------------------------------------ camera

def hero_at(z):
    return HERO["root"].location + Vector((0, 0, z))

def shot_hook(t):          # low and behind, the hero walking off up the aisle with his cape
    tg = hero_at(1.3)
    return tg + Vector((0.5, -3.2, -0.6)), tg
def shot_sign(t):          # over the hero's shoulder, up to the aisle sign
    u = t - E["B"]
    return Vector((0.8 - 0.05 * u, -1.6, 1.9)), Vector((0.0, 3.0, 2.9))
def shot_line(t):
    u = t - E["C"]
    return Vector((-1.25 + 0.05 * u, 7.3 - 0.08 * u, 2.5)), Vector((0.4, 11.5, 1.1))
def shot_front(t):         # in front of the hero (he faces -y after turning), the line behind him
    u = t - E["H"]
    tg = hero_at(1.5)
    return tg + Vector((0.6, -3.0 + 0.1 * u, -0.3)), tg
def shot_close(t):
    u = t - E["I"]
    tg = hero_at(1.85)
    return tg + Vector((0.3, -2.3 + 0.08 * u, -0.05)), tg
def shot_queue(t):
    u = t - E["J"]
    return Vector((-1.3, 13.55 - 0.08 * u, 1.9)), Vector((0.4, 11.0, 1.4))
def shot_end(t):
    u = t - E["K"]
    return Vector((1.0, 1.2 - 0.15 * u, 2.3)), Vector((-0.2, 7.2, 1.2))

SHOTS = [(shot_hook, None), (shot_sign, (E["B"] - 0.25, E["B"] + 0.15)), (shot_line, (E["C"] - 0.25, E["C"] + 0.15)),
         (shot_front, (E["G"] - 0.3, E["G"] + 0.2)), (shot_line, (E["E"] - 0.25, E["E"] + 0.15)),
         (shot_front, (E["H"] - 0.25, E["H"] + 0.15)), (shot_close, (E["I"] - 0.2, E["I"] + 0.1)),
         (shot_queue, (E["J"] - 0.2, E["J"] + 0.1)), (shot_end, (E["K"] - 0.25, E["K"] + 0.15))]
SHOTS = sorted(SHOTS, key=lambda s: s[1][0] if s[1] else -1)
LENS = {shot_line: 28.0, shot_close: 35.0, shot_end: 24.0, shot_queue: 26.0}

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
    names = ("hero", "cape", "sign", "line", "guard")
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        pts = {
            "hero": HERO["head"].matrix_world @ Vector((0, 0, 0.65)),
            "cape": HERO["cape"].matrix_world @ Vector((0, 0.05, -0.6)),
            "sign": Vector((0.0, 2.97, 3.72)),
            "line": LINE[-1]["head"].matrix_world @ Vector((0, 0, 0.65)),
            "guard": GUARD["head"].matrix_world @ Vector((0, 0, 0.65)),
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
