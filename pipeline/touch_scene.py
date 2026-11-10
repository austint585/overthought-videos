"""Blender scene for 'Breaking the touch barrier is quantum tunneling': a voxel school hallway after hours. Lockers,
one ceiling panel lit over the pair, a glowing cyan barrier filling the gap between him and her. She steps in, her
hand goes through the barrier on "tunnels" (it shatters, pink light), and he tips over flat on "collapse".
Directed with direct.py (shot sheet in ops/episodes/2026-11-10-touch-tunnel.md). Timed to render_touch.py.

blender -b --factory-startup -P touch_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
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
rng = random.Random(1110)
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

# ------------------------------------------------------------------ the set: a school hallway after hours
# The hallway runs along X. Lockers line the back wall (front face y = 2.5). He stands at x = +0.6 facing -X,
# she starts at x = -1.8 facing +X, and a glowing cyan barrier fills the gap between them.

MATS["tile"] = pixel_mat("tile", [(0.30, 0.31, 0.34), (0.33, 0.34, 0.37), (0.27, 0.28, 0.31), (0.36, 0.36, 0.39)], rough=0.35)
MATS["tile2"] = pixel_mat("tile2", [(0.12, 0.16, 0.26), (0.14, 0.18, 0.29), (0.11, 0.14, 0.23)], rough=0.35)
MATS["wall"] = pixel_mat("wall", [(0.20, 0.22, 0.28), (0.22, 0.24, 0.30), (0.18, 0.20, 0.26)], rough=0.95)
for i in range(-16, 16):
    for j in range(-6, 3):
        fill(i, i, j, j, -1, -1, "tile" if (i + j) % 2 == 0 else "tile2")
fill(-16, 15, 3, 3, 0, 5, "wall")
voxel_mesh("hall", GRID)

LOCK_A = colmat((0.10, 0.19, 0.38), 0.45, metallic=0.3)
LOCK_B = colmat((0.09, 0.16, 0.33), 0.45, metallic=0.3)
VENT = colmat((0.03, 0.04, 0.07), 0.6)
HANDLE = colmat((0.55, 0.57, 0.60), 0.3, metallic=0.8)
parts = []
for n in range(-15, 15):
    x0 = n * 0.95
    m = LOCK_A if n % 2 else LOCK_B
    parts.append(((x0, x0 + 0.92, 2.5, 3.0, 0.15, 3.4), m))
    for v in range(3):
        parts.append(((x0 + 0.2, x0 + 0.72, 2.48, 2.5, 3.0 - 0.12 * v, 3.05 - 0.12 * v), VENT))
    parts.append(((x0 + 0.72, x0 + 0.8, 2.47, 2.5, 1.6, 1.95), HANDLE))
parts.append(((-15 * 0.95, 15 * 0.95, 2.5, 3.0, 0.0, 0.15), colmat((0.04, 0.05, 0.08), 0.6)))
boxes("lockers", parts, (0, 0, 0))
# a poster and a club flyer taped between lockers, the red exit sign far down the hall
boxes("poster", [((-0.45, 0.45, -0.02, 0.0, -0.6, 0.6), colmat((0.80, 0.55, 0.18), 0.8)),
                 ((-0.35, 0.35, -0.03, -0.02, 0.2, 0.45), colmat((0.95, 0.92, 0.85), 0.8))], (-4.3, 2.47, 2.4))
boxes("flyer", [((-0.3, 0.3, -0.02, 0.0, -0.4, 0.4), colmat((0.30, 0.65, 0.45), 0.8))], (4.6, 2.47, 2.2))
EXIT_M = colmat((1.0, 0.12, 0.08), 0.4, emit=8.0)
boxes("exit", [((-0.45, 0.45, -0.15, 0.0, -0.18, 0.18), EXIT_M)], (-11.5, 2.4, 3.9))
# ceiling light panels: only the one over them is on
PANEL_ON = colmat((0.92, 0.95, 1.0), 0.3, emit=6.0)
PANEL_OFF = colmat((0.08, 0.09, 0.11), 0.5)
for n, x in enumerate((-9.0, -4.5, -0.6, 3.9, 8.4)):
    boxes(f"panel{n}", [((-0.9, 0.9, -0.5, 0.5, 0.0, 0.08), PANEL_ON if n == 2 else PANEL_OFF)], (x, 0.6, 4.6))

# the barrier: a slab of glowing cyan voxels, rebuilt each frame to fill the gap between them
BAR_M = pixel_mat("barrier", [(0.25, 0.85, 1.0), (0.35, 0.9, 1.0), (0.18, 0.7, 0.95)], rough=0.3, emit=2.2)
BP = B.bsdf(BAR_M)
BP.inputs["Alpha"].default_value = 0.24
try:
    BAR_M.surface_render_method = "DITHERED"
except Exception as ex:
    print("render method skipped:", ex)
barrier = boxes("barrier", [((-0.5, 0.5, -0.35, 0.35, 0.0, 2.6), BAR_M)], (0, 0, 0.02))
# the particle that tunnels (shot D), and the shards when she breaks it
PART_M = colmat((0.9, 0.97, 1.0), 0.3, emit=12.0)
particle = boxes("particle", [((-0.09, 0.09, -0.09, 0.09, -0.09, 0.09), PART_M)], AWAY)
SHARDS = []
for n in range(28):
    col = (1.0, 0.24, 0.55) if n % 3 == 0 else (0.35, 0.88, 1.0)
    SHARDS.append((boxes(f"shard{n}", [((-0.1, 0.1, -0.1, 0.1, -0.1, 0.1), colmat(col, 0.3, emit=7.0))], AWAY),
                   Vector((rng.uniform(-0.15, 0.15), rng.uniform(-0.9, 0.9), rng.uniform(0.2, 2.8))),
                   Vector((rng.uniform(-1.5, 1.5), rng.uniform(-1.8, 1.8), rng.uniform(0.5, 2.5)))))

HIM = figure("him", hair=(0.05, 0.04, 0.04), shirt=(0.62, 0.13, 0.12), pants=(0.12, 0.13, 0.16), skin=(0.48, 0.32, 0.22))
HER = figure("her", hair=(0.07, 0.05, 0.04), shirt=(0.93, 0.88, 0.82), pants=(0.10, 0.10, 0.12), skin=(0.62, 0.42, 0.30))
boxes("her_hair_long", [((-0.27, 0.27, 0.05, 0.3, -0.45, 0.5), colmat((0.07, 0.05, 0.04), 0.7))], (0, 0, 0), HER["head"])
HIM_X, HER_X0, HER_X1 = 0.6, -1.4, -0.25
HIM_HEAD = Vector((HIM_X, 0, 1.75))
TOUCH = Vector((HIM_X, -0.375, 1.5))

# ------------------------------------------------------------------ light: one pool from the ceiling panel, the barrier's own glow
world = bpy.data.worlds.new("bg")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.004, 0.006, 0.018, 1)
pool_ld = bpy.data.lights.new("pool", "SPOT")
pool_ld.energy = 1500.0
pool_ld.color = (0.88, 0.92, 1.0)
pool_ld.spot_size = math.radians(70)
pool_ld.spot_blend = 0.6
pool_ld.shadow_soft_size = 0.6
pool = B.link(bpy.data.objects.new("pool", pool_ld))
D.point_at(pool, Vector((0.0, 0.4, 4.5)), Vector((0.0, 0.0, 0.0)))
glow_ld = bpy.data.lights.new("glow", "POINT")
glow_ld.energy = 220.0
glow_ld.color = (0.35, 0.85, 1.0)
glow_ld.shadow_soft_size = 0.8
glow = B.link(bpy.data.objects.new("glow", glow_ld))
glow.location = (-0.6, -0.4, 1.6)
rim = B.area("rim", Vector((0, 2.2, 4.2)), Vector((0, -0.5, 1.4)), 5.0, 500.0, (0.55, 0.65, 1.0))
fill_l = B.area("fill", Vector((0, -9, 2.5)), Vector((0, 0, 1.4)), 6.0, 120.0, (0.45, 0.5, 0.8))
exit_ld = bpy.data.lights.new("exitl", "POINT")
exit_ld.energy = 120.0
exit_ld.color = (1.0, 0.15, 0.1)
exitl = B.link(bpy.data.objects.new("exitl", exit_ld))
exitl.location = (-11.5, 1.8, 3.6)
pink_ld = bpy.data.lights.new("pink", "POINT")
pink_ld.energy = 0.0
pink_ld.color = (1.0, 0.24, 0.55)
pink_ld.shadow_soft_size = 0.2
pink = B.link(bpy.data.objects.new("pink", pink_ld))
pink.location = TOUCH + Vector((0, -0.4, 0.1))
cam = B.camera(lens=35, fstop=2.8)
B.render_settings(FPS, samples=32, motion_blur=0.3, look="AgX - Punchy")
key_ld = bpy.data.lights.new("key", "SPOT")      # re-placed per shot (Shot.key): the barrier's glow or the panel, cheated onto the face
key_ld.energy = 700.0
key_ld.color = (0.72, 0.9, 1.0)
key_ld.spot_size = math.radians(34)
key_ld.spot_blend = 0.6
key_ld.shadow_soft_size = 0.3
key = B.link(bpy.data.objects.new("key", key_ld))
rig = D.Rig(cam, {"pool": pool, "glow": glow, "rim": rim, "fill": fill_l, "exitl": exitl, "key": key})

# ------------------------------------------------------------------ the shot sheet (ops/episodes/2026-11-10-touch-tunnel.md)
T_HIT = E["tunnels"]
GAP0 = Vector(((HIM_X + HER_X0) / 2, 0, 1.55))
SHOTS = D.ShotList([
    D.Shot("hook", 0.0, eye=GAP0, lens=35, dist=6.0, yaw=0, pitch=-2, screen=(0.5, 0.56),
           light={"key": 0.0, "fill": 0.6}, note="symmetrical two-shot in profile, the barrier glowing between them, hall falls to black"),
    D.Shot("axis", E["B"] - 0.05, eye=GAP0 + Vector((0, 0, 0.2)), lens=24, dist=8.5, yaw=72, pitch=6, screen=(0.5, 0.54),
           light={"key": 0.0, "fill": 0.3}, note="low wide behind him down the hall: the barrier between, her beyond, the exit sign deep"),
    D.Shot("pockets", E["C"] - 0.05, eye=Vector((HIM_X, 0, 1.25)), lens=50, dist=3.6, yaw=-12, pitch=-4,
           screen=(0.5, 0.56), key=(-1, 40, 30, 3.2), light={"key": 1.0, "fill": 0.15, "glow": 0.6}, note="him alone, hands down at his sides, cyan on one cheek"),
    D.Shot("through", E["D"] - 0.05, eye=Vector((GAP0.x, 0, 2.0)), lens=28, dist=6.0, yaw=0, pitch=0, screen=(0.5, 0.48),
           light={"key": 0.0, "fill": 0.3, "pool": 0.6}, note="the particle crosses the barrier above their heads"),
    D.Shot("gap", E["E"] - 0.05, eye=Vector((GAP0.x, 0, 0.6)), lens=16, dist=3.9, yaw=0, pitch=-80, screen=(0.5, 0.52),
           light={"key": 0.0, "fill": 0.2}, note="straight down: the width of the gap is the whole story"),
    D.Shot("her", E["closes"] - 0.1, eye=Vector((HER_X1, 0, 1.75)), lens=50, dist=3.8, yaw=-6, pitch=-2,
           screen=(0.5, 0.52), key=(1, 40, 30, 3.2), light={"key": 1.0, "fill": 0.15, "glow": 0.6}, note="she steps in; the breath before the hit"),
    D.Shot("touch", T_HIT - 0.45, eye=Vector((0.15, -0.3, 1.55)), lens=35, dist=4.6, yaw=0, pitch=-2, screen=(0.5, 0.52),
           move=("punch", 1.25), hit=T_HIT, kick=0.04, light={"key": 0.0, "fill": 0.15},
           note="the big moment: her hand through the barrier, shards, the only pink light, the only fast move"),
    D.Shot("collapse", E["G"] - 0.05, eye=Vector((0.3, 0, 0.9)), lens=35, dist=5.8, yaw=0, pitch=-4, screen=(0.5, 0.58),
           key=(1, 35, 45, 4.5), light={"key": 1.3, "fill": 0.3, "exitl": 0.3}, note="wide and locked off: he tips over like a plank, deadpan"),
    D.Shot("floor", E["H"] - 0.05, eye=Vector((0.9, 0, 0.4)), lens=35, dist=6.4, yaw=-25, pitch=-58, screen=(0.5, 0.52),
           key=(1, 30, 55, 4.0), light={"key": 1.0, "fill": 0.15}, note="high and small: him flat on the tiles, her standing over him"),
    D.Shot("loop", E["I"] - 0.05, eye=GAP0, lens=35, dist=6.0, yaw=0, pitch=-2, screen=(0.5, 0.56),
           light={"key": 0.0, "fill": 0.6}, note="the hook framing again, reset, so it loops"),
], end=DUR)
SHOTS.check()
SHOTS.dump(os.path.join(os.path.dirname(OUT.rstrip("/\\")), "shots.json"), big=T_HIT)

# ------------------------------------------------------------------ motion

def her_x(t):
    if t >= E["I"] - 0.05:
        return HER_X0
    u = D.smoother((t - E["closes"] + 0.1) / 0.6)
    return HER_X0 + (HER_X1 - HER_X0) * u

def people_state(t):
    tc = D.on_twos(t, FPS)
    reset = t >= E["I"] - 0.05
    hx = her_x(tc)
    walking = 0.0 < (tc - E["closes"] + 0.1) < 0.6 and not reset
    place(HER, hx, 0, face=(1, 0))
    idle = 0.03 * math.sin(t * 2.2) * D.hold(t, T_HIT, breath=0.35)
    reach = 0.0 if reset else D.ars(tc, T_HIT, wind=0.25, back=0.1, release=0.1, settle=0.4, over=0.08)
    if walking:
        pose(HER, walk=0.6, phase=tc * 9, head_nod=0.05)
    else:
        pose(HER, arms=((-0.05 + idle - 1.45 * reach, 0, 0), -0.05 - idle), head_nod=0.05)
    # him: stiff, hands at his sides; tips over backwards on "collapse"
    fall = 0.0 if reset else D.ars(tc, E["collapse"] + 0.35, wind=0.3, back=0.06, release=0.32, settle=0.3, over=0.0)
    place(HIM, HIM_X, 0, face=(-1, 0), z=0.13 * min(1.0, max(0.0, fall)))
    yaw = HIM["root"].rotation_euler.z
    HIM["root"].rotation_euler = (-math.pi / 2 * max(0.0, fall), 0, yaw)
    shake = 0.0
    if not reset and T_HIT <= tc < E["collapse"] + 0.1:
        shake = 0.04 * math.sin(tc * 70)           # short-circuit jitter between the touch and the fall
    pose(HIM, arms=(0.02 + shake, 0.02 - shake), head_nod=0.05 + shake, head_turn=shake * 2)

def barrier_state(t):
    hx = her_x(t)
    if T_HIT <= t < E["I"] - 0.05:
        barrier.location = AWAY
    else:
        x0, x1 = hx + 0.3, HIM_X - 0.3
        barrier.location = Vector(((x0 + x1) / 2, 0, 0.02))
        barrier.scale = (max(0.05, x1 - x0), 1, 1)
    flick = 1.0 + 0.06 * math.sin(t * 5.3) * D.hold(t, T_HIT, breath=0.35)
    BP.inputs["Emission Strength"].default_value = 2.2 * flick
    glow.location = (hx * 0.5 + HIM_X * 0.5, -0.4, 1.6)
    for ob, home, vel in SHARDS:
        u = t - T_HIT
        if 0 <= u < 1.3 and t < E["I"] - 0.05:
            p = Vector(((hx + HIM_X) / 2, 0, 0)) + home + vel * u * 1.6 + Vector((0, 0, -4.9 * u * u))
            p.z = max(0.1, p.z)
            ob.location = p
            k = max(0.001, 1 - u / 1.3)
            ob.scale = (k, k, k)
        else:
            ob.location = AWAY
    # the particle: flies at the barrier, slows, appears on the far side
    u = t - (E["through"] - 1.6)
    if 0 <= u < 3.2 and t < E["E"] - 0.1:
        x = (HER_X0 + HIM_X) / 2 - 1.6 * 1.6 + 1.6 * u
        particle.location = (x, -0.1, 2.3)
        particle.rotation_euler = (u * 3, u * 2, 0)
    else:
        particle.location = AWAY
    pe = D.flash(t, T_HIT, decay=0.6)
    pink.data.energy = 0.0 if t < T_HIT or t >= E["G"] else 320.0 * (0.4 + pe)

def apply_state(t):
    people_state(t)
    barrier_state(t)
    SHOTS.apply(rig, t)
    if t >= T_HIT and t < E["G"]:
        glow.data.energy = 0.0                     # the barrier's light dies with it; pink takes over

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    names = ("wall", "him", "her")
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        pts = {"wall": barrier.location + Vector((0, 0, 3.0)),
               "him": HIM["head"].matrix_world @ Vector((0, 0, 0.6)),
               "her": HER["head"].matrix_world @ Vector((0, 0, 0.6))}
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
