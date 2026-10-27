"""Blender scene for "Schrodinger's situationship": a plank crate on a dark studio floor, sawn open at the front, with a
couch inside. The couple on it is drawn twice (dating / not dating) as see-through states that fade against each other,
the 1935 cat gets the same treatment, and a friend with a flashlight collapses it. Built in code and timed to the narration.

blender -b --factory-startup -P quantum_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Always writes out_dir/anchors.json: screen positions of label points for every frame.
"""
import json, math, os, random, sys
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bkit as B
import quantum_anim as QA

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

def shade(c, f):
    return tuple(min(1.0, x * f) for x in c)

MATS = {
    "floor": pixel_mat("floor", [(0.045, 0.048, 0.06), (0.055, 0.058, 0.07), (0.04, 0.042, 0.052), (0.06, 0.064, 0.077)], rough=0.6),
    "planks": pixel_mat("planks", [(0.42, 0.26, 0.12), (0.47, 0.30, 0.14), (0.38, 0.23, 0.10)], lines=((1, 1, 4), (0.20, 0.11, 0.05))),
    "log": pixel_mat("log", [(0.17, 0.11, 0.06), (0.21, 0.14, 0.07), (0.13, 0.08, 0.04)]),
    "inside": pixel_mat("inside", [(0.30, 0.19, 0.09), (0.34, 0.22, 0.10), (0.27, 0.17, 0.08)], lines=((1, 1, 4), (0.15, 0.09, 0.04))),
    "rug": pixel_mat("rug", [(0.35, 0.30, 0.24), (0.40, 0.34, 0.27), (0.31, 0.26, 0.21)]),
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

# ------------------------------------------------------------------ studio floor and the crate (front sawn off)

for i in range(-20, 20):
    for j in range(-18, 14):
        GRID[(i, j, -1)] = "floor"
fill(-4, 3, -3, 2, 0, 5, "planks")
fill(-3, 2, -2, 1, 1, 4, None)                 # hollow
fill(-3, 2, -3, -3, 1, 4, None)                # the cutaway front
for i in (-4, 3):
    fill(i, i, -3, -3, 0, 5, "log")
fill(-4, 3, -3, -3, 5, 5, "log")
fill(-4, 3, -3, -3, 0, 0, "log")
fill(-3, 2, -2, 1, 0, 0, "inside")
fill(-2, 1, -2, 0, 0, 0, "rug")
voxel_mesh("world", GRID)

# ------------------------------------------------------------------ see-through state materials

GHOST = {}                                     # state -> materials whose alpha is animated
_gcache = {}
def gmat(color, state, rough=0.55, emit=0.0):
    key = (color, state, rough, emit)
    if key not in _gcache:
        m = solid(f"g_{state}_{len(_gcache)}", color, rough, emit)    # default DITHERED: BLENDED failed to compile (magenta) on Oct 27
        _gcache[key] = m
        GHOST.setdefault(state, []).append(m)
    return _gcache[key]

def set_alpha(state, a):
    for m in GHOST.get(state, []):
        B.bsdf(m).inputs["Alpha"].default_value = max(0.0, min(1.0, a))

# ------------------------------------------------------------------ couch, Geiger counter, lamp

COUCH = colmat((0.55, 0.08, 0.07), 0.8)
COUCH_D = colmat((0.40, 0.05, 0.05), 0.8)
boxes("couch", [((-2.25, 2.25, 0.35, 1.65, 0.0, 0.45), COUCH), ((-2.25, 2.25, 1.45, 1.9, 0.0, 1.35), COUCH_D),
                ((-2.6, -2.2, 0.35, 1.9, 0.0, 0.8), COUCH_D), ((2.2, 2.6, 0.35, 1.9, 0.0, 0.8), COUCH_D)], (0, 0, 1.0))
GLOW_G = colmat((0.35, 1.0, 0.25), 0.3, emit=5.0)
geiger = boxes("geiger", [((-0.3, 0.3, -0.2, 0.2, 0.0, 0.42), colmat((0.75, 0.62, 0.10), 0.5)),
                          ((-0.2, 0.2, -0.21, -0.2, 0.12, 0.34), colmat((0.92, 0.92, 0.85), 0.4)),
                          ((-0.02, 0.02, -0.215, -0.205, 0.14, 0.32), colmat((0.05, 0.05, 0.05), 0.4)),
                          ((0.32, 0.42, -0.05, 0.05, 0.05, 0.6), colmat((0.15, 0.15, 0.16), 0.4)),
                          ((0.6, 0.78, -0.09, 0.09, 0.0, 0.38), GLOW_G),
                          ((0.58, 0.8, -0.11, 0.11, 0.38, 0.44), colmat((0.2, 0.2, 0.22), 0.4))], (1.85, -1.25, 1.0))
vial_ld = bpy.data.lights.new("vial", "POINT"); vial_ld.color = (0.4, 1.0, 0.3); vial_ld.energy = 15.0; vial_ld.shadow_soft_size = 0.2
B.link(bpy.data.objects.new("vial", vial_ld)).location = (2.55, -1.25, 1.6)
lamp_ld = bpy.data.lights.new("lamp", "POINT"); lamp_ld.color = (1.0, 0.75, 0.45); lamp_ld.energy = 120.0; lamp_ld.shadow_soft_size = 0.6
B.link(bpy.data.objects.new("lamp", lamp_ld)).location = (-1.8, -0.6, 4.4)

# ------------------------------------------------------------------ characters

def figure(name, hair, shirt, pants, skin, state=None, long_hair=False, phone=False):
    m = (lambda c, r=0.55, e=0.0: gmat(c, state, r, e)) if state else (lambda c, r=0.55, e=0.0: colmat(c, r, e))
    root = B.link(bpy.data.objects.new(name, None))
    S, H, Sh, P, D = m(skin), m(hair, 0.7), m(shirt), m(pants, 0.7), m((0.03, 0.02, 0.02), 0.4)
    Shoe = m((0.05, 0.05, 0.06), 0.5)
    f = {"root": root}
    for side, x in (("L", -0.125), ("R", 0.125)):
        f["leg" + side] = boxes(f"{name}_leg{side}", [((-0.125, 0.125, -0.125, 0.125, -0.75, 0.0), P),
                                                       ((-0.13, 0.13, -0.135, 0.13, -0.75, -0.62), Shoe)], (x, 0, 0.75), root)
    boxes(f"{name}_body", [((-0.25, 0.25, -0.125, 0.125, 0, 0.75), Sh)], (0, 0, 0.75), root)
    for side, x in (("L", -0.375), ("R", 0.375)):
        parts = [((-0.125, 0.125, -0.125, 0.125, -0.25, 0.0), Sh), ((-0.12, 0.12, -0.12, 0.12, -0.75, -0.25), S)]
        if phone and side == "R":
            parts += [((-0.08, 0.08, -0.03, 0.03, -0.92, -0.72), m((0.55, 0.75, 1.0), 0.3, 3.0))]
        f["arm" + side] = boxes(f"{name}_arm{side}", parts, (x, 0, 1.5), root)
    head = [((-0.25, 0.25, -0.25, 0.25, 0, 0.5), S), ((-0.27, 0.27, -0.27, 0.27, 0.38, 0.55), H),
            ((-0.16, -0.06, -0.265, -0.25, 0.2, 0.28), D), ((0.06, 0.16, -0.265, -0.25, 0.2, 0.28), D),
            ((-0.07, 0.07, -0.262, -0.25, 0.07, 0.1), m(shade(skin, 0.6)))]
    if long_hair:
        head += [((-0.27, 0.27, 0.1, 0.29, -0.5, 0.5), H), ((-0.29, -0.2, -0.2, 0.27, -0.35, 0.45), H),
                 ((0.2, 0.29, -0.2, 0.27, -0.35, 0.45), H)]
    else:
        head += [((-0.27, 0.27, 0.08, 0.28, 0.12, 0.5), H)]
    f["head"] = boxes(f"{name}_head", head, (0, 0, 1.5), root)
    return f

def hide(f):
    f["root"].location = AWAY

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

YOU = dict(hair=(0.12, 0.08, 0.05), shirt=(0.10, 0.22, 0.45), pants=(0.12, 0.12, 0.13), skin=(0.80, 0.55, 0.40))
THEM = dict(hair=(0.45, 0.25, 0.10), shirt=(0.85, 0.80, 0.70), pants=(0.25, 0.30, 0.45), skin=(0.62, 0.42, 0.28), long_hair=True)
SEAT_Z, SEAT_Y = 1.0 + 0.45 - 0.75, 1.0
D_YOU, D_THEM = figure("d_you", state="dating", **YOU), figure("d_them", state="dating", **THEM)
N_YOU, N_THEM = figure("n_you", state="not", phone=True, **YOU), figure("n_them", state="not", phone=True, **THEM)
PINKH = gmat((1.0, 0.25, 0.45), "dating", 0.4, 3.0)
heart = boxes("heart", [((-0.3, -0.05, -0.06, 0.06, 0.1, 0.35), PINKH), ((0.05, 0.3, -0.06, 0.06, 0.1, 0.35), PINKH),
                        ((-0.22, 0.22, -0.06, 0.06, -0.1, 0.12), PINKH), ((-0.1, 0.1, -0.06, 0.06, -0.25, -0.08), PINKH)], (0, SEAT_Y - 0.1, 3.75))
FRIEND = figure("friend", (0.05, 0.04, 0.04), (0.20, 0.45, 0.25), (0.15, 0.15, 0.18), (0.45, 0.30, 0.20))
torch = boxes("torch", [((-0.06, 0.06, -0.06, 0.06, -1.1, -0.7), colmat((0.15, 0.15, 0.16), 0.4)),
                        ((-0.08, 0.08, -0.08, 0.08, -1.18, -1.1), colmat((1.0, 0.95, 0.8), 0.3, emit=8.0))], (0, 0, 0), FRIEND["armR"])
spot_ld = bpy.data.lights.new("torch", "SPOT"); spot_ld.spot_size = math.radians(34); spot_ld.spot_blend = 0.4
spot_ld.color = (1.0, 0.95, 0.85); spot_ld.shadow_soft_size = 0.1
spot = B.link(bpy.data.objects.new("torch_light", spot_ld))
spot.parent = torch
spot.location = (0, 0, -1.2)                   # a spot light shines down its local -Z, which is along the arm

# the cat, alive (sitting) and dead (on its side, X eyes)
def cat(name, state, dead=False):
    O, Od, W = gmat((0.90, 0.48, 0.12), state, 0.7), gmat((0.65, 0.30, 0.06), state, 0.7), gmat((0.95, 0.93, 0.88), state, 0.7)
    K_ = gmat((0.03, 0.03, 0.03), state, 0.4)
    parts = [((-0.22, 0.22, -0.3, 0.3, 0.0, 0.42), O), ((-0.23, 0.23, -0.31, 0.31, 0.15, 0.2), Od),
             ((-0.2, 0.2, -0.42, -0.1, 0.42, 0.78), O), ((-0.2, -0.08, -0.36, -0.24, 0.78, 0.9), Od), ((0.08, 0.2, -0.36, -0.24, 0.78, 0.9), Od),
             ((-0.1, 0.1, -0.43, -0.42, 0.48, 0.56), W), ((-0.05, 0.05, 0.3, 0.42, 0.05, 0.12), O), ((-0.05, 0.05, 0.38, 0.45, 0.1, 0.55), O)]
    if dead:
        for cx in (-0.1, 0.1):
            parts += [((cx - 0.05, cx + 0.05, -0.425, -0.42, 0.62, 0.66), K_), ((cx - 0.015, cx + 0.015, -0.426, -0.421, 0.58, 0.70), K_)]
    else:
        parts += [((-0.14, -0.06, -0.425, -0.42, 0.6, 0.68), K_), ((0.06, 0.14, -0.425, -0.42, 0.6, 0.68), K_)]
    return boxes(name, parts, (0, 0, 0))
CAT_ALIVE = cat("cat_alive", "alive")
CAT_DEAD = cat("cat_dead", "dead", dead=True)
CAT_END = cat("cat_end", "cat_end")           # sits on the couch for the last line

# ------------------------------------------------------------------ lights, world, camera

world = bpy.data.worlds.new("bg")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.013, 0.017, 1)
B.area("key", Vector((-6, -9, 9)), Vector((0, 0, 2)), 6.0, 2600.0, (1.0, 0.95, 0.88))
B.area("fill", Vector((8, -6, 4)), Vector((0, 0, 2)), 6.0, 500.0, (0.75, 0.82, 1.0))
B.area("rim", Vector((3, 9, 8)), Vector((0, 0, 2)), 5.0, 1400.0, (1.0, 0.6, 0.35))
flash_ld = bpy.data.lights.new("flash", "POINT"); flash_ld.color = (1.0, 1.0, 1.0); flash_ld.shadow_soft_size = 1.0
flash = B.link(bpy.data.objects.new("flash", flash_ld)); flash.location = (0, -0.5, 3.0)

cam = B.camera(lens=35, fstop=2.8)
B.render_settings(FPS, samples=32, motion_blur=0.3)

# ------------------------------------------------------------------ timeline

T_FLASH = QA.flash_time(E)

def couple_state(t):
    a_d, a_n = QA.couple_alphas(t, E)
    set_alpha("dating", a_d)
    set_alpha("not", a_n)
    breathe = 0.03 * math.sin(t * 2.1)
    if a_d > 0.01:
        place(D_YOU, -0.32, SEAT_Y, z=SEAT_Z); place(D_THEM, 0.32, SEAT_Y, z=SEAT_Z)
        pose(D_YOU, sit=True, arms=(-0.25, (-0.15, 0, 0.25)), head_tilt=-0.18 + breathe)
        pose(D_THEM, sit=True, arms=((-0.15, 0, -0.25), -0.25), head_tilt=0.22 - breathe, head_turn=0.15)
        heart.location = (0, SEAT_Y - 0.1, 3.75 + 0.08 * math.sin(t * 3))
    else:
        hide(D_YOU); hide(D_THEM); heart.location = AWAY
    if a_n > 0.01:
        place(N_YOU, -1.55, SEAT_Y, z=SEAT_Z, face=(0.15, -1)); place(N_THEM, 1.55, SEAT_Y, z=SEAT_Z, face=(-0.15, -1))
        thumb = 0.06 * math.sin(t * 9)
        pose(N_YOU, sit=True, arms=(-0.35, -1.0 + thumb), head_nod=-0.38)
        pose(N_THEM, sit=True, arms=(-0.35, -1.0 - thumb), head_nod=-0.38)
    else:
        hide(N_YOU); hide(N_THEM)

def cat_state(t):
    a_alive, a_dead = QA.cat_alphas(t, E)
    c0, c1 = QA.cat_window(E)
    in_box = c0 <= t < c1
    set_alpha("alive", a_alive)
    set_alpha("dead", a_dead)
    if in_box:
        CAT_ALIVE.location = (0, -0.6, 1.0)
        CAT_DEAD.location = (0.1, -0.55, 1.0 + 0.22)
        CAT_DEAD.rotation_euler = (0, math.pi / 2, 0.1)
    else:
        CAT_ALIVE.location = AWAY
        CAT_DEAD.location = AWAY
    if t >= E["right"] - 0.25:
        pop = min(1.0, (t - (E["right"] - 0.25)) / 0.25)
        CAT_END.location = (0, SEAT_Y - 0.2, 1.45)
        CAT_END.scale = (pop + 0.001,) * 3
        CAT_END.rotation_euler = (0, 0, 0.1 * math.sin(t * 1.5))
    else:
        CAT_END.location = AWAY

def friend_state(t):
    t0, t1 = QA.friend_enter(E), QA.friend_arrive(E)
    on = t1 + 0.1 <= t < E["H"] - 0.3
    spot_ld.energy = 900.0 * ramp(t, t1 - 0.1, t1 + 0.2) if on else 0.0
    if t < t0 or t >= E["H"] - 0.3:
        hide(FRIEND)
        return
    (ax, ay), (bx, by) = QA.FRIEND_PATH
    L = math.hypot(bx - ax, by - ay)
    d = min(L, (t - t0) * QA.FRIEND_SPEED)
    x, y = ax + (bx - ax) * d / L, ay + (by - ay) * d / L
    walking = d < L
    face = ((bx - ax) / L, (by - ay) / L) if walking else (0.25, 1)
    place(FRIEND, x, y, face=face)
    raise_arm = ramp(t, t1 - 0.2, t1 + 0.25)
    pose(FRIEND, walk=1.0 if walking else 0.0, phase=(t - t0) * 10, arms=None)
    if not walking:
        FRIEND["armL"].rotation_euler = (-0.2, 0, 0)
        FRIEND["armR"].rotation_euler = (-1.45 * raise_arm, 0, 0)
    FRIEND["head"].rotation_euler = (0.05, 0, 0)

def apply_state(t):
    couple_state(t)
    cat_state(t)
    friend_state(t)
    u = t - T_FLASH
    flash_ld.energy = 8000.0 * math.exp(-u * 6) if u >= 0 else 0.0
    loc, target, fstop, lens = camera_at(t)
    B.aim(cam, loc, target)
    cam.data.lens = lens
    cam.data.dof.focus_distance = (target - loc).length
    cam.data.dof.aperture_fstop = fstop
    cam.data.clip_start = 0.05
    cam.data.clip_end = 200

# ------------------------------------------------------------------ camera: each shot returns (camera location, look target)

COUCH_C = Vector((0, SEAT_Y - 0.1, 2.35))
def shot_hook(t):
    u = min(1.0, t / max(1.0, E["B"]))
    return COUCH_C + Vector((-2.2 + 0.8 * u, -8.4 + 1.6 * u, 1.6 - 0.2 * u)), COUCH_C + Vector((0, 0, 0.2))
def shot_cat(t):
    tg = Vector((0, -0.6, 1.5))
    u = t - E["B"]
    return tg + Vector((1.5 - 0.12 * u, -4.4 + 0.15 * u, 1.3)), tg
def shot_couple(t):
    u = t - E["C"]
    return COUCH_C + Vector((1.9 - 0.25 * u, -6.0 + 0.1 * u, 1.0)), COUCH_C
def shot_side(t):
    u = t - E["E"]
    a = math.radians(-128 + 4.0 * u)
    return COUCH_C + 7.2 * Vector((math.cos(a), math.sin(a), 0.28)), COUCH_C
def shot_wide(t):
    u = t - E["F"]
    tg = Vector((0, 0, 2.6))
    return tg + Vector((3.2 - 0.3 * u, -12.0 + 0.4 * u, 3.6)), tg
def shot_friend(t):
    u = t - E["G"]
    tg = Vector((-1.0, -2.6, 2.2))
    return tg + Vector((6.5 - 0.3 * u, -9.0 + 0.3 * u, 2.4)), tg
def shot_end(t):
    u = t - E["H"]
    return COUCH_C + Vector((-1.4 + 0.2 * u, -5.6 + 0.25 * u, 0.9)), COUCH_C + Vector((0, 0, -0.1))

SHOTS = [(shot_hook, None), (shot_cat, (E["B"] - 0.3, E["B"] + 0.15)), (shot_couple, (E["C"] - 0.3, E["C"] + 0.15)),
         (shot_side, (E["E"] - 0.3, E["E"] + 0.15)), (shot_wide, (E["F"] - 0.3, E["F"] + 0.15)),
         (shot_friend, (E["G"] - 0.3, E["G"] + 0.15)), (shot_end, (E["H"] - 0.3, E["H"] + 0.15))]
LENS = {shot_wide: 32.0}

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
    fstop = 2.0 if d < 6 else (2.8 if d < 10 else 4.0)
    return loc, tg, fstop, lens

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    names = ("heart", "you", "them", "cat", "geiger", "friend", "box")
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        pts = {
            "heart": Vector((0, SEAT_Y - 0.1, 4.1)),
            "you": Vector((-1.55, SEAT_Y, 3.0)),
            "them": Vector((1.55, SEAT_Y, 3.0)),
            "cat": Vector((0, -0.6, 2.0)),
            "geiger": Vector((1.85, -1.4, 1.5)),
            "friend": FRIEND["root"].matrix_world @ Vector((0, 0, 2.15)),
            "box": Vector((0, -2.0, 6.1)),
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
