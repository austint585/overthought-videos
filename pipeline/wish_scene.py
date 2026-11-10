"""Blender scene for 'The 11:11 wish window': a voxel rooftop at night above a dark city, a giant amber digital clock
billboard that flips 11:10 -> 11:11 and lights a matching 11/11 date row, and one blocky guy on a camping chair with his
phone. Built in code and timed to the narration (render_wish.py). Pixel materials and voxel helpers as in quantum_scene.

blender -b --factory-startup -P wish_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
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
rng = random.Random(11)
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

# ------------------------------------------------------------------ rooftop: tar roof, brick parapet with a stone cap

fill(-7, 6, -6, 6, -1, -1, "roof")
fill(-8, 7, 7, 7, -1, 0, "brick")                  # back parapet
fill(-8, -8, -6, 7, -1, 0, "brick")                # sides
fill(7, 7, -6, 7, -1, 0, "brick")
fill(-8, 7, 7, 7, 1, 1, "cap")
fill(-8, -8, -6, 7, 1, 1, "cap")
fill(7, 7, -6, 7, 1, 1, "cap")
fill(-8, 7, -7, -7, -1, -1, "brick")               # front lip, low so the camera sees over it
fill(-8, 7, -6, 6, -4, -2, "brick")                # building below the roof
voxel_mesh("roof", GRID)

METAL = colmat((0.55, 0.57, 0.60), 0.35, metallic=0.6)
METAL_D = colmat((0.30, 0.32, 0.35), 0.4, metallic=0.5)
boxes("ac", [((-1.0, 1.0, -0.8, 0.8, 0.0, 1.3), METAL), ((-0.8, 0.8, -0.82, -0.8, 0.2, 1.1), METAL_D),
             ((-0.5, 0.5, -0.5, 0.5, 1.3, 1.45), METAL_D)], (-5.0, 3.5, 0.0))
boxes("pipe", [((-0.15, 0.15, -0.15, 0.15, 0.0, 2.2), METAL_D), ((-0.25, 0.25, -0.25, 0.25, 2.2, 2.4), METAL_D)], (5.5, -3.5, 0.0))
boxes("antenna", [((-0.05, 0.05, -0.05, 0.05, 0.0, 5.0), METAL_D), ((-1.0, 1.0, -0.04, 0.04, 4.0, 4.08), METAL_D),
                  ((-0.7, 0.7, -0.04, 0.04, 4.6, 4.68), METAL_D)], (-6.3, 6.0, 1.0))
RED_L = colmat((1.0, 0.1, 0.05), 0.4, emit=6.0)
boxes("antenna_tip", [((-0.09, 0.09, -0.09, 0.09, 0.0, 0.18), RED_L)], (-6.3, 6.0, 6.0))

# ------------------------------------------------------------------ the city below: dark towers with lit windows

TOWER = colmat((0.05, 0.055, 0.07), 0.8)
WIN_W = colmat((1.0, 0.78, 0.45), 0.4, emit=4.0)
WIN_C = colmat((0.6, 0.75, 1.0), 0.4, emit=3.0)
for n in range(26):
    ang = rng.uniform(-math.pi * 0.95, math.pi * 0.95)
    r = rng.uniform(18, 46)
    x, y = r * math.sin(ang), r * math.cos(ang) + 4
    if abs(x) < 12 and -10 < y < 12:
        continue
    w, d = rng.choice((3, 4, 5)), rng.choice((3, 4, 5))
    top = rng.uniform(-14, 9)
    parts = [((-w / 2, w / 2, -d / 2, d / 2, -40, top), TOWER)]
    for k in range(rng.randint(8, 22)):           # windows on the side facing the roof
        face = rng.choice(("x", "y"))
        zz = rng.uniform(-30, top - 1.0)
        mat = WIN_W if rng.random() < 0.75 else WIN_C
        if face == "y":
            u = rng.uniform(-w / 2 + 0.5, w / 2 - 0.9)
            side = -d / 2 - 0.02 if y > 4 else d / 2 + 0.02
            parts.append(((u, u + 0.4, side - 0.02, side + 0.02, zz, zz + 0.55), mat))
        else:
            u = rng.uniform(-d / 2 + 0.5, d / 2 - 0.9)
            side = -w / 2 - 0.02 if x > 0 else w / 2 + 0.02
            parts.append(((side - 0.02, side + 0.02, u, u + 0.4, zz, zz + 0.55), mat))
    boxes(f"tower{n}", parts, (x, y, 0.0))

# stars and the moon
STAR = colmat((1.0, 1.0, 1.0), 0.4, emit=12.0)
star_parts = []
for n in range(260):
    a = rng.uniform(0, 2 * math.pi)
    el = rng.uniform(0.12, 1.35)
    R = 150
    p = Vector((R * math.cos(el) * math.sin(a), R * math.cos(el) * math.cos(a) + 4, R * math.sin(el)))
    s = rng.uniform(0.15, 0.4)
    star_parts.append(((p.x - s, p.x + s, p.y - s, p.y + s, p.z - s, p.z + s), STAR))
boxes("stars", star_parts, (0, 0, 0))
MOON = colmat((0.95, 0.93, 0.82), 0.6, emit=3.0)
boxes("moon", [((-4, 4, -1, 1, -4, 4), MOON), ((-4.6, 4.6, -1, 1, -2.8, 2.8), MOON), ((-2.8, 2.8, -1, 1, -4.6, 4.6), MOON)],
      (-38, 110, 46))

# ------------------------------------------------------------------ the clock billboard

BOARD_Y = 9.0
BOARD_C = Vector((1.5, BOARD_Y, 8.2))
FRAME = colmat((0.06, 0.06, 0.07), 0.5)
boxes("board", [((-6.2, 6.2, -0.4, 0.4, -3.6, 3.6), FRAME), ((-6.4, 6.4, -0.45, -0.38, 3.4, 3.7), METAL_D),
                ((-6.4, 6.4, -0.45, -0.38, -3.7, -3.4), METAL_D),
                ((-4.2, -3.8, -0.2, 0.2, -10.0, -3.6), METAL_D), ((3.8, 4.2, -0.2, 0.2, -10.0, -3.6), METAL_D),
                ((-4.2, 4.2, -0.15, 0.15, -7.0, -6.7), METAL_D)], BOARD_C)
AMBER = (1.0, 0.33, 0.02)
LIT = solid("lit", AMBER, 0.4, 6.0)
DIM = solid("dim", (0.07, 0.03, 0.015), 0.5, 0.25)
FRONT = BOARD_Y - 0.42

SEGS = {"a": (0, 1, 1), "b": (1, 1, 0), "c": (1, 0, 0), "d": (0, 0, 1), "e": (-1, 0, 0), "f": (-1, 1, 0), "g": (0, 0.5, 1)}
DIGITS = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc",
          "8": "abcdefg", "9": "abcdfg"}
SEG_OBJ = []                                       # (slot, segment, lit object, home)

def seg_box(seg, cx, cz, w, h, th):
    if seg == "a": return (cx - w / 2, cx + w / 2, cz + h / 2 - th, cz + h / 2)
    if seg == "d": return (cx - w / 2, cx + w / 2, cz - h / 2, cz - h / 2 + th)
    if seg == "g": return (cx - w / 2, cx + w / 2, cz - th / 2, cz + th / 2)
    x0 = cx + w / 2 - th if seg in "bc" else cx - w / 2
    z0, z1 = (cz, cz + h / 2) if seg in "bf" else (cz - h / 2, cz)
    return (x0, x0 + th, z0 + th * 0.3, z1 - th * 0.3)

def build_digit(slot, cx, cz, w, h, th):
    for seg in "abcdefg":
        x0, x1, z0, z1 = seg_box(seg, cx, cz, w, h, th)
        gap = th * 0.12
        if seg in "adg":
            x0, x1 = x0 + gap, x1 - gap
        boxes(f"dim_{slot}{seg}", [((x0, x1, -0.03, 0.0, z0, z1), DIM)], (0, FRONT, 0))
        ob = boxes(f"lit_{slot}{seg}", [((x0, x1, -0.06, 0.0, z0, z1), LIT)], (0, FRONT, 0))
        SEG_OBJ.append((slot, seg, ob))

# time row: big digits, then the date row above
TW, TH, TT = 1.55, 2.9, 0.34
tz = BOARD_C.z - 1.2
txs = [BOARD_C.x + dx for dx in (-4.1, -2.1, 1.0, 3.0)]
for n, x in enumerate(txs):
    build_digit(f"t{n}", x, tz, TW, TH, TT)
COLON = []
for dz in (-0.55, 0.55):
    x = BOARD_C.x - 0.55
    boxes(f"dimc{dz}", [((x - 0.18, x + 0.18, -0.03, 0.0, tz + dz - 0.18, tz + dz + 0.18), DIM)], (0, FRONT, 0))
    COLON.append(boxes(f"litc{dz}", [((x - 0.18, x + 0.18, -0.06, 0.0, tz + dz - 0.18, tz + dz + 0.18), LIT)], (0, FRONT, 0)))
DW, DH, DT = 0.75, 1.3, 0.2
dz_ = BOARD_C.z + 1.9
dxs = [BOARD_C.x + dx for dx in (-2.4, -1.4, 1.0, 2.0)]
for n, x in enumerate(dxs):
    build_digit(f"d{n}", x, dz_, DW, DH, DT)
def slash(name, mat, depth):
    ob = boxes(name, [((-0.11, 0.11, depth, 0.0, -0.75, 0.75), mat)], (BOARD_C.x - 0.2, FRONT, dz_))
    ob.rotation_euler = (0, math.radians(25), 0)
    return ob
slash("dim_slash", DIM, -0.03)
SLASH = slash("lit_slash", LIT, -0.06)
SLASH_HOME = SLASH.location.copy()
HOME = {ob.name: ob.location.copy() for _, _, ob in SEG_OBJ}
COLON_HOME = [o.location.copy() for o in COLON]
for small, x in (("DATE", -5.2), ("TIME", -5.2)):
    pass
clock_ld = bpy.data.lights.new("clockglow", "AREA"); clock_ld.shape = "RECTANGLE"; clock_ld.size = 11.0; clock_ld.size_y = 6.0
clock_ld.color = AMBER
clock = B.link(bpy.data.objects.new("clockglow", clock_ld))
clock.location = (BOARD_C.x, BOARD_Y - 1.2, BOARD_C.z)
clock.rotation_euler = (math.radians(90), 0, math.radians(180))   # area light faces local -Z; turned to face -Y

def show(text_time, date_on):
    for slot, seg, ob in SEG_OBJ:
        if slot[0] == "t":
            ch = text_time.replace(":", "")[int(slot[1])]
        else:
            ch = "1" if date_on else None
        on = ch is not None and seg in DIGITS[ch]
        ob.location = HOME[ob.name] if on else AWAY
    SLASH.location = SLASH_HOME if date_on else AWAY

# ------------------------------------------------------------------ the guy and his camping chair

def figure(name, hair, shirt, pants, skin):
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
        if side == "R":
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

YOU = figure("you", hair=(0.10, 0.07, 0.05), shirt=(0.30, 0.32, 0.36), pants=(0.10, 0.14, 0.26), skin=(0.78, 0.55, 0.40))
GUY = Vector((-1.2, -1.2, 0.0))
CHAIR_C = colmat((0.10, 0.35, 0.30), 0.8)
boxes("chair", [((-0.55, 0.55, -0.45, 0.45, 0.55, 0.65), CHAIR_C), ((-0.55, 0.55, 0.35, 0.45, 0.6, 1.55), CHAIR_C),
                ((-0.6, -0.52, -0.45, 0.45, 0.0, 0.62), METAL_D), ((0.52, 0.6, -0.45, 0.45, 0.0, 0.62), METAL_D),
                ((-0.65, -0.5, -0.4, 0.3, 0.85, 0.92), METAL_D), ((0.5, 0.65, -0.4, 0.3, 0.85, 0.92), METAL_D)], GUY)
phone_ld = bpy.data.lights.new("phone", "POINT"); phone_ld.color = (0.6, 0.75, 1.0); phone_ld.shadow_soft_size = 0.1
phone = B.link(bpy.data.objects.new("phone", phone_ld))
SEAT_Z = 0.65 - 0.75 + 0.05

# shooting star
TRAIL = colmat((1.0, 0.95, 0.8), 0.4, emit=20.0)
comet = boxes("comet", [((-0.25, 0.25, -0.25, 0.25, -0.25, 0.25), TRAIL), ((0.25, 4.0, -0.1, 0.1, -0.1, 0.1), TRAIL)], (0, 0, 0))

# ------------------------------------------------------------------ lights, world, camera

world = bpy.data.worlds.new("bg")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.010, 0.014, 0.035, 1)
B.area("moonkey", Vector((-14, -6, 14)), Vector((0, 2, 1)), 8.0, 1500.0, (0.62, 0.72, 1.0))
B.area("rim", Vector((8, 14, 6)), Vector((0, 0, 1)), 6.0, 600.0, (0.55, 0.65, 1.0))
B.area("fill", Vector((4, -12, 5)), Vector((0, 0, 1)), 8.0, 160.0, (0.5, 0.55, 0.8))
cam = B.camera(lens=35, fstop=2.8)
B.render_settings(FPS, samples=32, motion_blur=0.3)

# ------------------------------------------------------------------ timeline

def time_text(t):
    if t < E["flip"]:
        return "1110"
    if t < E["alarm"]:
        return "1111"
    return "1110"

def guy_state(t):
    place(YOU, GUY.x, GUY.y - 0.1, face=(0.25, -1), z=SEAT_Z)
    bob = 0.03 * math.sin(t * 2.0)
    thumb = 0.06 * math.sin(t * 9)
    look_up = ramp(t, E["flip"], E["flip"] + 0.35) * (1 - ramp(t, E["B"] - 0.2, E["B"] + 0.2))
    look_up = max(look_up, ramp(t, E["catch"] - 0.2, E["catch"] + 0.2) * (1 - ramp(t, E["2005"], E["2005"] + 0.4)))
    standing = ramp(t, E["D"] - 0.1, E["D"] + 0.25) * (1 - ramp(t, E["E"] - 0.3, E["E"]))
    stand2 = ramp(t, E["lock"] - 0.3, E["lock"])
    st = max(standing, stand2)
    if st > 0.5:
        hop = 0.0
        if E["xp"] - 0.1 <= t < E["E"] - 0.3:
            hop = abs(math.sin((t - E["xp"]) * 9.0)) * 0.35
        place(YOU, GUY.x, GUY.y - 0.8, face=(0.25, -1), z=hop)
        if stand2 > 0.5:
            pose(YOU, arms=((-0.15, 0, -0.15), (-1.1, 0, 0.2)), head_nod=0.12)       # lock in: phone down, eyes front
        else:
            up = ramp(t, E["eight"], E["eight"] + 0.25)
            pose(YOU, arms=((-0.6 - 2.3 * up, 0, -0.3), (-0.6 - 2.3 * up, 0, 0.3)), head_nod=0.25 * up, head_turn=0.0)
    else:
        nod = -0.38 if t < E["G"] else -0.5
        nod = nod * (1 - look_up) + 0.45 * look_up
        pose(YOU, sit=True, arms=(-0.35, -1.0 + thumb), head_nod=nod + bob * 0.3, head_turn=-0.9 * look_up)
    hand = YOU["armR"].matrix_world @ Vector((0, -0.25, -0.85))
    phone.location = hand
    phone_ld.energy = (6.0 if t < E["G"] else 14.0) * (0 if stand2 > 0.5 and st > 0.5 else 1)

def clock_state(t):
    show(time_text(t), t >= E["date"])
    flip = max(math.exp(-(t - E["flip"]) * 5) if t >= E["flip"] else 0.0,
               0.7 * math.exp(-(t - E["date"]) * 5) if t >= E["date"] else 0.0)
    B.bsdf(LIT).inputs["Emission Strength"].default_value = 6.0 + 14.0 * flip
    clock_ld.energy = 900.0 + 6000.0 * flip
    blink = (t % 1.0) < 0.5 or E["flip"] - 0.1 < t < E["B"]
    for o, h in zip(COLON, COLON_HOME):
        o.location = h if blink else AWAY

def comet_state(t):
    u = (t - (E["xp"] - 0.2)) / 1.0
    if 0 <= u <= 1:
        comet.location = Vector((22 - 44 * u, 40, 30 - 9 * u))
        comet.rotation_euler = (0, math.radians(-12), 0)
    else:
        comet.location = AWAY

def apply_state(t):
    guy_state(t)
    clock_state(t)
    comet_state(t)
    loc, target, fstop, lens = camera_at(t)
    B.aim(cam, loc, target)
    cam.data.lens = lens
    cam.data.dof.focus_distance = (target - loc).length
    cam.data.dof.aperture_fstop = fstop
    cam.data.clip_start = 0.05
    cam.data.clip_end = 400

# ------------------------------------------------------------------ camera: each shot returns (camera location, look target)

TIME_C = Vector((BOARD_C.x - 0.6, BOARD_Y, tz))
HEAD = GUY + Vector((0, -0.1, 1.6))
def shot_hook(t):                                  # straight on the big digits, slow push
    u = min(1.0, t / max(1.0, E["B"]))
    return TIME_C + Vector((0.3 - 0.4 * u, -19.5 + 2.0 * u, -0.4)), TIME_C + Vector((0, 0, 0.6))
def shot_wide(t):                                  # high front-left wide: roof, guy, clock, city
    u = t - E["B"]
    tg = Vector((0.5, 3.0, 3.2))
    return tg + Vector((-9.5 + 0.5 * u, -15.0 + 0.4 * u, 7.5 - 0.2 * u)), tg
def shot_low(t):                                   # low on the guy and his phone, clock glowing behind
    u = t - E["C"]
    tg = HEAD + Vector((0.2, 0, -0.2))
    return tg + Vector((2.6 - 0.2 * u, -3.6 + 0.1 * u, -0.6)), tg + Vector((0, 0, 0.5))
def shot_date(t):                                  # both rows of the clock, pulls back for double XP
    u = t - E["D"]
    back = smooth01((t - E["xp"] + 0.2) / 0.8)
    tg = BOARD_C + Vector((-0.4, 0, 0.2 + 2.0 * back))
    return tg + Vector((-1.5 + 0.2 * u, -16.0 - 9.0 * back, -1.5 - 0.5 * back)), tg
def shot_over(t):                                  # behind the guy, looking up at the clock
    u = t - E["E"]
    tg = HEAD.lerp(BOARD_C, 0.18)
    return HEAD + Vector((3.2 - 0.15 * u, -5.8 + 0.1 * u, -0.2)), tg
def shot_top(t):                                   # high orbit over the guy
    u = t - E["F"]
    a = math.radians(-60 + 7 * u)
    tg = GUY + Vector((0, 0, 1.0))
    return tg + Vector((7.5 * math.cos(a), 7.5 * math.sin(a), 8.5)), tg
def shot_face(t):                                  # close on the face in phone light
    u = t - E["G"]
    tg = HEAD + Vector((0, -0.15, 0.1))
    return tg + Vector((1.0 - 0.1 * u, -3.6 + 0.15 * u, 0.5)), tg
def shot_end(t):                                   # front wide, slow pull back, the clock back on 11:10
    u = t - E["H"]
    tg = Vector((0.3, 3.0, 4.6))
    return tg + Vector((1.0 - 0.15 * u, -17.0 - 0.5 * u, 0.6 + 0.1 * u)), tg

SHOTS = [(shot_hook, None), (shot_wide, (E["B"] - 0.3, E["B"] + 0.15)), (shot_low, (E["C"] - 0.3, E["C"] + 0.15)),
         (shot_date, (E["D"] - 0.3, E["D"] + 0.15)), (shot_over, (E["E"] - 0.3, E["E"] + 0.15)),
         (shot_top, (E["F"] - 0.3, E["F"] + 0.15)), (shot_face, (E["G"] - 0.3, E["G"] + 0.15)),
         (shot_end, (E["H"] - 0.3, E["H"] + 0.15))]
LENS = {shot_wide: 30.0, shot_end: 32.0}

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
    names = ("ones", "you", "clock")
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        pts = {"ones": Vector((BOARD_C.x + 1.5, FRONT, dz_ + 0.9)),
               "you": YOU["head"].matrix_world @ Vector((0, 0, 0.6)),
               "clock": Vector((BOARD_C.x, FRONT, BOARD_C.z + 3.7))}
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
