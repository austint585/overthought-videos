"""Blender scene for 'Your next relationship, randomized': a voxel arcade at night with a relationship slot machine.
Four reel rows spin the whole time (every frame is a different pick), a lever, a player, neon and background cabinets.
The picks themselves are drawn in 2D by render_roll.py, so any paused frame reads as a full result.

blender -b --factory-startup -P roll_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
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
# ------------------------------------------------------------------ the arcade: dark carpet, back wall, neon strips

MATS["carpet"] = pixel_mat("carpet", [(0.05, 0.03, 0.10), (0.10, 0.05, 0.18), (0.03, 0.08, 0.14), (0.16, 0.04, 0.12)])
MATS["wall"] = pixel_mat("wall", [(0.06, 0.06, 0.09), (0.07, 0.07, 0.10), (0.05, 0.05, 0.08)], rough=0.95)
fill(-10, 9, -6, 8, -1, -1, "carpet")
fill(-10, 9, 9, 9, 0, 8, "wall")
voxel_mesh("arcade", GRID)
NEON_P = colmat((1.0, 0.15, 0.7), 0.4, emit=8.0)
NEON_C = colmat((0.1, 0.9, 1.0), 0.4, emit=8.0)
boxes("neon1", [((-9.0, 9.0, -0.05, 0.05, 0.0, 0.12), NEON_P)], (0, 8.95, 6.6))
boxes("neon2", [((-9.0, 9.0, -0.05, 0.05, 0.0, 0.12), NEON_C)], (0, 8.95, 6.2))

# background cabinets
CAB = colmat((0.08, 0.08, 0.12), 0.5)
for n, (x, col) in enumerate(((-7.0, (1.0, 0.3, 0.1)), (-4.6, (0.2, 1.0, 0.4)), (4.8, (0.3, 0.5, 1.0)), (7.2, (1.0, 0.85, 0.1)))):
    scr = colmat(col, 0.3, emit=3.0)
    boxes(f"cab{n}", [((-0.9, 0.9, -0.8, 0.8, 0.0, 3.6), CAB), ((-0.7, 0.7, -0.82, -0.8, 2.0, 3.1), scr),
                      ((-0.9, 0.9, -0.82, -0.8, 3.3, 3.55), colmat(col, 0.3, emit=6.0))], (x, 7.8, 0))

# the machine: a tall cabinet, a glowing header, four reel rows (spinning square prisms), a lever
M = Vector((0.0, 4.0, 0.0))
BODY = colmat((0.75, 0.08, 0.30), 0.35, metallic=0.2)
TRIM = colmat((1.0, 0.82, 0.25), 0.3, metallic=0.8)
HEADER = colmat((1.0, 0.85, 0.3), 0.3, emit=7.0)
boxes("machine", [((-2.2, 2.2, -1.2, 1.2, 0.0, 1.6), BODY), ((-2.0, 2.0, -0.9, 1.2, 1.6, 6.2), BODY),
                  ((-2.3, 2.3, -1.3, 1.3, 1.5, 1.65), TRIM), ((-2.1, 2.1, -1.0, 1.2, 6.2, 6.35), TRIM),
                  ((-2.0, 2.0, -0.95, -0.9, 6.35, 7.3), HEADER), ((-2.0, 2.0, -0.9, 1.0, 6.35, 7.3), BODY)], M)
WIN_BG = colmat((0.02, 0.02, 0.03), 0.4)
ROWS = []
ROW_Z = [5.3, 4.25, 3.2, 2.15]
PRISM_COLS = [colmat((0.95, 0.95, 0.92), 0.4, emit=0.6), colmat((0.95, 0.35, 0.55), 0.4, emit=0.6),
              colmat((0.35, 0.8, 0.95), 0.4, emit=0.6), colmat((1.0, 0.85, 0.3), 0.4, emit=0.6)]
for r, z in enumerate(ROW_Z):
    boxes(f"win{r}", [((-1.85, 1.85, -0.97, -0.9, z + 0.42, z + 0.5), TRIM),
                      ((-1.85, 1.85, -0.97, -0.9, z - 0.5, z - 0.42), TRIM)], M)
    parts = []
    for k in range(4):                          # four faces of a square prism, each a different color
        a = k * math.pi / 2
        parts.append(((-1.6, 1.6, -0.36, 0.36, 0.33, 0.36), PRISM_COLS[(k + r) % 4]))
    ob = B.link(bpy.data.objects.new(f"reel{r}", None))
    ob.location = M + Vector((0, -0.55, z))
    for k in range(4):
        face = boxes(f"reel{r}f{k}", [((-1.6, 1.6, -0.36, 0.36, 0.30, 0.36), PRISM_COLS[(k + r) % 4])], (0, 0, 0), ob)
        face.rotation_euler = (k * math.pi / 2, 0, 0)
    ROWS.append(ob)
LEVER = B.link(bpy.data.objects.new("lever", None))
LEVER.location = M + Vector((2.3, -0.4, 1.4))
boxes("lever_base", [((-0.1, 0.35, -0.3, 0.3, -0.3, 0.3), TRIM)], M + Vector((2.0, -0.4, 1.4)))
boxes("lever_arm", [((0.1, 0.2, -0.05, 0.05, 0.0, 1.1), TRIM)], (0, 0, 0), LEVER)
boxes("lever_ball", [((0.0, 0.3, -0.15, 0.15, 1.1, 1.4), colmat((1.0, 0.1, 0.1), 0.3, emit=1.0))], (0, 0, 0), LEVER)

# coin-op stool in front
boxes("stool", [((-0.4, 0.4, -0.4, 0.4, 0.9, 1.05), colmat((0.1, 0.1, 0.1), 0.5)),
                ((-0.06, 0.06, -0.06, 0.06, 0.0, 0.9), METAL_D)], M + Vector((-3.3, -2.0, 0)))

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

YOU = figure("you", hair=(0.12, 0.08, 0.05), shirt=(0.15, 0.55, 0.45), pants=(0.12, 0.12, 0.18), skin=(0.80, 0.58, 0.44))
YOU_POS = M + Vector((3.0, -1.7, 0))
YOU_HEAD = YOU_POS + Vector((0, 0, 1.75))

world = bpy.data.worlds.new("bg")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.01, 0.006, 0.02, 1)
B.area("key", M + Vector((-5, -7, 8)), M + Vector((0, 0, 3)), 6.0, 900.0, (1.0, 0.8, 0.9))
B.area("rimP", M + Vector((6, 4, 5)), M + Vector((0, 0, 3)), 4.0, 700.0, (1.0, 0.3, 0.8))
B.area("rimC", M + Vector((-6, 4, 5)), M + Vector((0, 0, 3)), 4.0, 700.0, (0.2, 0.8, 1.0))
B.area("fill", M + Vector((0, -12, 4)), M + Vector((0, 0, 2)), 10.0, 250.0, (0.6, 0.6, 0.9))
hdr_ld = bpy.data.lights.new("hdr", "AREA"); hdr_ld.size = 4.0; hdr_ld.color = (1.0, 0.85, 0.4); hdr_ld.energy = 400
hdr = B.link(bpy.data.objects.new("hdr", hdr_ld))
hdr.location = M + Vector((0, -1.6, 6.8)); hdr.rotation_euler = (math.radians(-90), 0, 0)
cam = B.camera(lens=35, fstop=2.8)
B.render_settings(FPS, samples=32, motion_blur=0.15)

def pulls(t):
    """Lever pull amount 0..1: at the start and on 'Pause sooner'."""
    p = 0.0
    for t0 in (-0.15, E["F"] - 0.1):
        u = t - t0
        if 0 <= u < 0.7:
            p = max(p, smooth01(u / 0.15) * (1 - smooth01((u - 0.3) / 0.4)))
    return p

def apply_state(t):
    for r, ob in enumerate(ROWS):
        ob.rotation_euler = (t * (11.0 + 1.7 * r) + r, 0, 0)
    p = pulls(t)
    LEVER.rotation_euler = (-1.2 * p, 0, 0)
    look = ramp(t, E["E"] - 0.2, E["E"] + 0.2) * (1 - ramp(t, E["F"] - 0.3, E["F"]))
    ang = math.atan2(-0.35, 1) + (math.atan2(-0.25, -1) - math.atan2(-0.35, 1)) * look
    place(YOU, YOU_POS.x, YOU_POS.y, face=(math.sin(ang), math.cos(ang)))
    bob = 0.03 * math.sin(t * 4)
    arm = -1.9 - 0.8 * p
    pose(YOU, arms=(-0.1 + bob, (arm * (1 - look) - 0.3 * look, 0, 0.5 * (1 - look))), head_nod=0.15 * (1 - look) - 0.05 * look)
    if E["C"] < t < E["D"]:
        pose(YOU, arms=(-0.1, -0.2), head_nod=0.25, head_tilt=0.15 * math.sin(t * 2))
    loc, target, fstop, lens = camera_at(t)
    B.aim(cam, loc, target)
    cam.data.lens = lens
    cam.data.dof.focus_distance = (target - loc).length
    cam.data.dof.aperture_fstop = fstop
    cam.data.clip_start = 0.05
    cam.data.clip_end = 400

# ------------------------------------------------------------------ camera: each shot returns (camera location, look target)

REELS_C = M + Vector((0, -0.9, 3.7))
def shot_hook(t):                                  # straight on the machine, header to bottom row
    u = min(1.0, t / max(1.0, E["B"]))
    tg = REELS_C + Vector((0, 0, 0.6))
    return tg + Vector((0.3 - 0.4 * u, -9.0 + 1.0 * u, 0.3)), tg
def shot_lever(t):                                 # low side on the lever and the player
    u = t - E["B"]
    tg = M + Vector((2.6, -1.2, 2.2))
    return tg + Vector((4.5 - 0.3 * u, -7.5 + 0.3 * u, 1.6)), tg
def shot_low(t):                                   # low angle up the spinning rows
    u = t - E["C"]
    tg = REELS_C + Vector((0, 0, 0.3))
    return tg + Vector((-3.5 + 0.4 * u, -5.0, -2.6)), tg
def shot_wide(t):                                  # high wide over the arcade
    u = t - E["D"]
    tg = M + Vector((0, 0, 2.5))
    a = math.radians(-120 + 6 * u)
    return tg + Vector((11.0 * math.cos(a), 11.0 * math.sin(a), 7.0)), tg
def shot_face(t):                                  # the player turns to camera
    u = t - E["E"]
    tg = YOU_HEAD + Vector((0, 0, -0.1))
    return tg + Vector((-1.4 + 0.1 * u, -3.4 + 0.1 * u, 0.3)), tg
def shot_end(t):                                   # back to the front, the loop
    u = t - E["F"]
    tg = REELS_C + Vector((0, 0, 0.6))
    return tg + Vector((-0.4 + 0.3 * u, -9.5 + 0.4 * u, 0.3)), tg

SHOTS = [(shot_hook, None), (shot_lever, (E["B"] - 0.3, E["B"] + 0.15)), (shot_low, (E["C"] - 0.3, E["C"] + 0.15)),
         (shot_wide, (E["D"] - 0.3, E["D"] + 0.15)), (shot_face, (E["E"] - 0.3, E["E"] + 0.15)),
         (shot_end, (E["F"] - 0.3, E["F"] + 0.15))]
LENS = {shot_wide: 30.0, shot_hook: 32.0, shot_end: 32.0}

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
    names = ("lever", "you")
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        pts = {"lever": M + Vector((2.45, -0.4, 2.7)), "you": YOU["head"].matrix_world @ Vector((0, 0, 0.6))}
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
