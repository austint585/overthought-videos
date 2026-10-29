"""Blender scene for 'The man who took down Crumbl': a voxel strip mall at dusk with a pink cookie shop, an empty
'for lease' unit and a donut shop next door, a paleo coach who walks up and hands cash to each customer heading for
the cookie shop, customers who hop and walk away, the cookie shop going dark, and the coach eyeing the donut shop.

blender -b --factory-startup -P crumbl_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Always writes out_dir/anchors.json: screen positions of label points for every frame.

No two surfaces of different materials share a plane (Austin saw texture flicker where they did): every add-on part
sits a few centimetres off the face behind it.
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
    "asphalt": pixel_mat("asphalt", [(0.10, 0.10, 0.11), (0.12, 0.12, 0.13), (0.09, 0.09, 0.10), (0.14, 0.14, 0.15)], rough=0.9),
    "walk": pixel_mat("walk", [(0.55, 0.55, 0.53), (0.60, 0.60, 0.58), (0.52, 0.52, 0.50)], lines=((1, 1, 1), (0.38, 0.38, 0.37))),
    "brick": pixel_mat("brick", [(0.45, 0.42, 0.40), (0.50, 0.47, 0.44), (0.42, 0.39, 0.37)]),
    "pink": pixel_mat("pink", [(0.95, 0.55, 0.68), (0.98, 0.62, 0.74), (0.92, 0.50, 0.64)]),
    "teal": pixel_mat("teal", [(0.15, 0.55, 0.58), (0.18, 0.60, 0.63), (0.13, 0.50, 0.53)]),
    "trim": pixel_mat("trim", [(0.88, 0.88, 0.86), (0.92, 0.92, 0.90)]),
    "cglass": solid("cglass", (1.0, 0.85, 0.80), rough=0.1, emit=3.0, emit_color=(1.0, 0.80, 0.78)),
    "dglass": solid("dglass", (0.6, 0.85, 1.0), rough=0.1, emit=0.05, emit_color=(1.0, 0.9, 0.7)),
    "lglass": solid("lglass", (0.10, 0.11, 0.13), rough=0.15, emit=0.0),
}

# ------------------------------------------------------------------ voxel strip mall (front face at y = 10)

GRID = {}

def fill(i0, i1, j0, j1, k0, k1, mat):
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            for k in range(k0, k1 + 1):
                GRID[(i, j, k)] = mat

fill(-16, 16, -6, 18, -1, -1, "asphalt")
fill(-16, 16, 8, 9, -1, -1, "walk")                 # sidewalk, flush with the lot (one surface, no overlap)
fill(-12, 11, 10, 13, 0, 4, "brick")
fill(-4, 3, 10, 10, 0, 4, "pink")                   # cookie shop
fill(4, 10, 10, 10, 0, 4, "teal")                   # donut shop
fill(-12, 11, 10, 13, 5, 5, "trim")                 # parapet
fill(-3, 2, 10, 10, 0, 2, "cglass")
fill(5, 9, 10, 10, 0, 2, "dglass")
fill(-11, -6, 10, 10, 0, 2, "lglass")

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

voxel_mesh("mall", GRID)

_mat_cache = {}
def colmat(color, rough=0.55, emit=0.0):
    key = (color, rough, emit)
    if key not in _mat_cache:
        _mat_cache[key] = solid(f"c{len(_mat_cache)}", color, rough, emit)
    return _mat_cache[key]

def boxes(name, parts, origin, parent=None):
    mats, builders = [], []
    for bb, m in parts:
        if m not in mats:
            mats.append(m)
        builders.append(B.with_material(B.box(*bb), mats.index(m)))
    ob = B.mesh_from(name, B.many(*builders), mats)
    ob.parent = parent
    ob.location = origin
    return ob

def text3d(name, body, loc, size, mat, extrude=0.04):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    ob = B.link(bpy.data.objects.new(name, cu))
    ob.data.materials.append(mat)
    ob.location = loc
    ob.rotation_euler = (math.pi / 2, 0, 0)        # stands up, reads toward -y
    return ob

# parking lines: thin boxes lifted 2 cm off the asphalt
LINE_M = colmat((0.85, 0.85, 0.80), 0.7)
boxes("lines", [((x - 0.06, x + 0.06, 1.0, 6.0, 0.02, 0.04), LINE_M) for x in (-9.0, -6.0, -3.0, 3.0, 6.0, 9.0)], (0, 0, 0))
# curb strip between the lot and the sidewalk
boxes("curb", [((-16, 17, 7.85, 8.0, 0.0, 0.12), colmat((0.62, 0.62, 0.60), 0.8))], (0, 0, 0))

# cookie shop: awning, sign board with a big cookie and the name
PINK_D = colmat((0.80, 0.25, 0.45), 0.6)
WHITE = colmat((0.97, 0.95, 0.93), 0.5)
boxes("awning", [((-3.0 + 0.5 * n, -2.5 + 0.5 * n, 9.0, 9.94, 2.62, 2.80), PINK_D if n % 2 == 0 else WHITE) for n in range(12)],
      (0, 0, 0))
boxes("csign", [((-3.6, 3.6, 9.80, 9.94, 3.05, 4.65), colmat((0.20, 0.06, 0.12), 0.5))], (0, 0, 0))
CSIGN_TXT = solid("csigntxt", (1.0, 0.70, 0.82), rough=0.4, emit=4.0)
text3d("ctext", "CRUMBL", (0.45, 9.70, 3.85), 1.05, CSIGN_TXT)
bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.62, depth=0.12, location=(-2.55, 9.70, 3.85),
                                    rotation=(math.pi / 2, 0, 0))
cookie = bpy.context.active_object
cookie.data.materials.append(colmat((0.80, 0.55, 0.30), 0.8))
for dx, dz in ((-0.25, 0.2), (0.18, 0.28), (0.05, -0.05), (-0.2, -0.25), (0.3, -0.18)):
    boxes("chip", [((-0.07, 0.07, -0.03, 0.03, -0.07, 0.07), colmat((0.18, 0.09, 0.05), 0.6))], (-2.55 + dx, 9.60, 3.85 + dz))

# donut shop: sign with a donut and the name, lights off until the end
boxes("dsign", [((4.4, 10.6, 9.80, 9.94, 3.05, 4.65), colmat((0.05, 0.12, 0.16), 0.5))], (0, 0, 0))
DSIGN_TXT = solid("dsigntxt", (0.6, 1.0, 0.95), rough=0.4, emit=0.0)
text3d("dtext", "DONUTS", (8.1, 9.70, 3.85), 0.9, DSIGN_TXT)
bpy.ops.mesh.primitive_torus_add(major_radius=0.48, minor_radius=0.2, location=(5.35, 9.62, 3.85), rotation=(math.pi / 2, 0, 0))
donut = bpy.context.active_object
DONUT_M = solid("donut", (0.95, 0.45, 0.70), rough=0.5, emit=0.0)
donut.data.materials.append(DONUT_M)

# empty unit: a paper sign in the dark window
boxes("lease", [((-9.6, -7.4, 9.90, 9.95, 1.0, 2.0), colmat((0.95, 0.95, 0.92), 0.7))], (0, 0, 0))
text3d("ltext", "FOR LEASE", (-8.5, 9.86, 1.5), 0.36, colmat((0.80, 0.10, 0.08), 0.6), extrude=0.01)

# street lamps
for x in (-7.5, 7.5):
    boxes(f"lamp{x}", [((-0.08, 0.08, -0.08, 0.08, 0.0, 4.25), colmat((0.2, 0.2, 0.22), 0.5)),
                       ((-0.25, 0.25, -0.25, 0.25, 4.2, 4.4), colmat((1.0, 0.85, 0.6), 0.3, emit=8.0))], (x, 7.5, 0.0))

# ------------------------------------------------------------------ figures

def person(name, shirt, pants, skin, hair, long_hair=False, tank=False, shorts=False, band=None):
    root = B.link(bpy.data.objects.new(name, None))
    S, P, Sk, H = colmat(shirt, 0.7), colmat(pants, 0.7), colmat(skin), colmat(hair, 0.8)
    D, Shoe = colmat((0.03, 0.02, 0.02), 0.4), colmat((0.15, 0.15, 0.17), 0.5)
    f = {"root": root}
    for side, x in (("L", -0.125), ("R", 0.125)):
        legs = [((-0.125, 0.125, -0.125, 0.125, -0.75, 0.0), P), ((-0.13, 0.13, -0.17, 0.13, -0.75, -0.66), Shoe)]
        if shorts:
            legs = [((-0.125, 0.125, -0.125, 0.125, -0.35, 0.0), P), ((-0.11, 0.11, -0.11, 0.11, -0.68, -0.34), Sk),
                    ((-0.13, 0.13, -0.17, 0.13, -0.75, -0.66), Shoe)]
        f["leg" + side] = boxes(f"{name}_leg{side}", legs, (x, 0, 0.75), root)
    f["body"] = boxes(f"{name}_body", [((-0.25, 0.25, -0.125, 0.125, 0, 0.75), S)], (0, 0, 0.75), root)
    for side, x in (("L", -0.375), ("R", 0.375)):
        top = Sk if tank else S
        f["arm" + side] = boxes(f"{name}_arm{side}", [((-0.12, 0.12, -0.12, 0.12, -0.35, 0.0), top),
                                                      ((-0.11, 0.11, -0.11, 0.11, -0.78, -0.34), Sk)], (x, 0, 1.5), root)
    hp = [((-0.25, 0.25, -0.25, 0.25, 0, 0.5), Sk), ((-0.27, 0.27, -0.27, 0.27, 0.43, 0.58), H),
          ((-0.268, 0.268, 0.05, 0.28, 0.15 if not long_hair else -0.35, 0.47), H),
          ((-0.16, -0.06, -0.265, -0.25, 0.22, 0.29), D), ((0.06, 0.16, -0.265, -0.25, 0.22, 0.29), D),
          ((-0.08, 0.08, -0.262, -0.25, 0.07, 0.1), colmat((0.55, 0.30, 0.22)))]
    if long_hair:
        hp += [((-0.29, -0.23, -0.2, 0.26, -0.35, 0.47), H), ((0.23, 0.29, -0.2, 0.26, -0.35, 0.47), H)]
    if band:
        hp += [((-0.285, 0.285, -0.285, 0.285, 0.34, 0.42), colmat(band, 0.6))]
    f["head"] = boxes(f"{name}_head", hp, (0, 0, 1.5), root)
    return f

CASH = colmat((0.35, 0.70, 0.35), 0.6)
BOX = colmat((0.98, 0.62, 0.74), 0.5)

COACH = person("coach", (0.25, 0.55, 0.30), (0.75, 0.65, 0.45), (0.80, 0.55, 0.38), (0.45, 0.30, 0.12),
               tank=True, shorts=True, band=(0.95, 0.95, 0.95))
COACH["cash"] = boxes("coachcash", [((-0.04, 0.04, -0.20, 0.0, -0.06, 0.06), CASH), ((-0.035, 0.035, -0.19, 0.005, -0.10, 0.10), CASH)],
                      (0.0, -0.06, -0.80), COACH["armR"])
COACH["fan"] = boxes("coachfan", [((-0.05, 0.05, -0.14, 0.0, -0.09, 0.09), CASH)], (0.0, -0.06, -0.80), COACH["armL"])
boxes("pack", [((-0.22, 0.22, -0.20, -0.13, 0.05, 0.22), colmat((0.10, 0.10, 0.12), 0.5))], (0, 0, 0), COACH["body"])
COACH["root"].scale = (1.12,) * 3

LOOKS = [((0.85, 0.25, 0.45), (0.15, 0.15, 0.2), (0.86, 0.64, 0.5), (0.85, 0.65, 0.25), True),
         ((0.15, 0.30, 0.65), (0.25, 0.3, 0.55), (0.55, 0.38, 0.26), (0.08, 0.05, 0.03), False),
         ((0.95, 0.6, 0.15), (0.12, 0.12, 0.14), (0.92, 0.72, 0.6), (0.45, 0.22, 0.08), True),
         ((0.55, 0.75, 0.95), (0.85, 0.85, 0.85), (0.70, 0.50, 0.36), (0.1, 0.07, 0.05), False),
         ((0.75, 0.2, 0.2), (0.1, 0.1, 0.15), (0.45, 0.30, 0.20), (0.04, 0.03, 0.03), True),
         ((0.3, 0.7, 0.4), (0.15, 0.15, 0.2), (0.86, 0.66, 0.52), (0.95, 0.85, 0.55), False)]
CUST = []
for n, (sh, pa, sk, ha, lh) in enumerate(LOOKS):
    p = person(f"c{n}", sh, pa, sk, ha, long_hair=lh)
    p["bill"] = boxes(f"c{n}bill", [((-0.04, 0.04, -0.18, 0.0, -0.06, 0.06), CASH)], (0.0, -0.05, -0.80), p["armR"])
    p["box"] = boxes(f"c{n}box", [((-0.20, 0.20, -0.32, 0.0, -0.06, 0.04), BOX)], (-0.37, -0.10, -0.72), p["armR"])
    p["root"].scale = (1.0 + 0.04 * (n % 3),) * 3
    CUST.append(p)

# ------------------------------------------------------------------ lights, world, camera

world = bpy.data.worlds.new("bg")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.10, 0.07, 0.20, 1)
bg.inputs["Strength"].default_value = 0.9
B.sun("dusk", -60, 9, 2.2, (1.0, 0.55, 0.30), angle_deg=3)
shop_l = B.area("shopl", Vector((-0.5, 8.6, 2.4)), Vector((-0.5, 5.0, 0.8)), 4.0, 400.0, (1.0, 0.72, 0.78))
donut_l = B.area("donutl", Vector((7.0, 8.6, 2.4)), Vector((7.0, 5.0, 0.8)), 4.0, 0.0, (0.7, 1.0, 0.95))
fill_l = B.area("fill", Vector((2.0, 1.0, 4.0)), Vector((0.0, 8.0, 1.0)), 5.0, 260.0, (0.6, 0.65, 1.0))
for x in (-7.5, 7.5):
    B.area(f"lampl{x}", Vector((x, 7.5, 4.15)), Vector((x, 7.5, 0)), 0.6, 300.0, (1.0, 0.82, 0.55))

cam = B.camera(lens=30, fstop=2.8)
B.render_settings(FPS, samples=32, motion_blur=0.3)

# ------------------------------------------------------------------ motion

def pose(f, walk=0.0, phase=0.0, arms=None, head_turn=0.0, head_nod=0.0, lean=0.0):
    s = math.sin(phase) * walk
    f["legL"].rotation_euler = (s * 0.7, 0, 0)
    f["legR"].rotation_euler = (-s * 0.7, 0, 0)
    aL, aR = arms if arms else ((-s * 0.45, 0, -0.08), (s * 0.45, 0, 0.08))
    f["armL"].rotation_euler = aL
    f["armR"].rotation_euler = aR
    f["head"].rotation_euler = (head_nod, 0, head_turn)
    f["body"].rotation_euler = (lean, 0, 0)

def face_dir(d):
    return math.atan2(d[0], -d[1])

COACH_SPOT = Vector((-1.2, 8.4, 0.0))
MEET = Vector((-0.25, 7.55, 0.0))

def coach_state(t):
    t_in = E["D"] - 1.6
    if t < t_in:
        COACH["root"].location = AWAY
        return
    u = ramp(t, t_in, E["D"] + 0.2)
    p = Vector((-5.0, 8.6, 0.0)).lerp(COACH_SPOT, u)
    walking = u < 0.98
    COACH["root"].location = p + Vector((0, 0, 0.03 * abs(math.sin(t * 8.0)) if walking else 0))
    # facing: toward the customer meeting point while handing out cash, the donut shop at the end, the camera between
    if walking:
        ang = face_dir((1, 0))
    else:
        ang = face_dir(MEET - COACH_SPOT)
    look_donut = ramp(t, E["next"] - 1.4, E["next"] - 0.6)
    ang = ang * (1 - look_donut) + face_dir((1, 0.3)) * look_donut
    COACH["root"].rotation_euler = (0, 0, ang)
    give = max(give_amount(t, tm) for tm in MEETS)
    fan = 0.5 + 0.5 * math.sin(t * 3.1)
    armL = (-0.5 - 0.2 * fan, 0, -0.35)          # left hand holds the fan of cash in front of his chest
    armR = (-1.45 * give - 0.15 * (1 - give), 0, 0.1 * (1 - give))
    nod = 0.12 * math.sin(t * 2.3) if not walking else 0.0
    if walking:
        pose(COACH, walk=1.0, phase=t * 8.0, head_turn=0.3)
    else:
        pose(COACH, arms=(armL, armR), head_nod=nod, lean=-0.08 * give)
    smug = ramp(t, E["wallet"] - 0.2, E["wallet"] + 0.3) * (1 - look_donut)
    if smug > 0:
        COACH["armL"].rotation_euler = (0.3 * smug + armL[0] * (1 - smug), 0, -0.9 * smug + armL[2] * (1 - smug))
        COACH["armR"].rotation_euler = (0.3 * smug, 0, 0.9 * smug)
        COACH["head"].rotation_euler = (-0.15 * smug, 0, 0)
    if look_donut > 0:
        COACH["head"].rotation_euler = (0.05, 0, 0.3 * look_donut)

def give_amount(t, tm):
    return ramp(t, tm - 0.45, tm - 0.05) * (1 - ramp(t, tm + 0.35, tm + 0.75))

# customer n walks in from the lot, meets him at MEETS[n], takes the cash, hops, and walks off the other way
MEETS = []

def setup_meets():
    keys = ("not", "delivery", "million", "720", "officially")
    for k in keys:
        MEETS.append(E[k])

setup_meets()
START = [Vector((3.0, 1.5, 0)), Vector((2.8, 1.0, 0)), Vector((2.5, 0.5, 0)), Vector((3.5, 1.5, 0)), Vector((-3.5, 1.0, 0))]
LEAVE = [Vector((4.5, 4.0, 0)), Vector((3.5, 8.9, 0)), Vector((5.0, 1.0, 0)), Vector((-4.0, 1.5, 0)), Vector((5.5, 2.5, 0))]
WALK_IN = 2.6

def customer_state(n, t):
    f = CUST[n]
    tm = MEETS[n]
    t0 = tm - WALK_IN - 0.3
    f["box"].scale = (0, 0, 0)
    if t < t0 or t > tm + 6.0:
        f["root"].location = AWAY
        return
    if t < tm - 0.3:                                   # walking in, a little bounce in the step
        u = (t - t0) / WALK_IN
        p = START[n].lerp(MEET, smooth01(u) * 0.3 + u * 0.7)
        d = MEET - START[n]
        f["root"].location = p + Vector((0, 0, 0.035 * abs(math.sin(t * 7.0 + n))))
        f["root"].rotation_euler = (0, 0, face_dir(d))
        pose(f, walk=1.0, phase=t * 7.0 + n, head_turn=0.15 * math.sin(t * 1.3 + n))
        f["bill"].scale = (0, 0, 0)
        return
    if t < tm + 0.9:                                   # stops, turns to him, takes the bill, hops with both arms up
        f["root"].rotation_euler = (0, 0, face_dir(COACH_SPOT - MEET))
        took = t > tm + 0.05
        f["bill"].scale = (1, 1, 1) if took else (0, 0, 0)
        hop = ramp(t, tm + 0.15, tm + 0.25)
        h = 0.0
        if tm + 0.15 < t < tm + 0.65:
            v = (t - tm - 0.15) / 0.5
            h = 0.45 * 4 * v * (1 - v)
        f["root"].location = MEET + Vector((0, 0, h))
        reach = ramp(t, tm - 0.3, tm) * (1 - hop)
        up = hop
        aR = (-1.3 * reach - 2.8 * up, 0, 0.3 * up)
        aL = (-2.8 * up, 0, -0.3 * up)
        pose(f, arms=(aL, aR), head_nod=-0.2 * up)
        f["legL"].rotation_euler = (-0.4 * up * (h > 0.05), 0, 0)
        f["legR"].rotation_euler = (0.2 * up * (h > 0.05), 0, 0)
        return
    u = (t - tm - 0.9) / 4.0                           # walks off, waving the bill
    d = LEAVE[n] - MEET
    p = MEET.lerp(LEAVE[n] + d * 0.6, min(1.0, u))
    f["root"].location = p + Vector((0, 0, 0.04 * abs(math.sin(t * 8.0 + n))))
    f["root"].rotation_euler = (0, 0, face_dir(d))
    f["bill"].scale = (1, 1, 1)
    s = math.sin(t * 8.0 + n)
    pose(f, walk=1.0, phase=t * 8.0 + n, arms=((-s * 0.45, 0, -0.08), (-2.6 + 0.3 * math.sin(t * 10), 0, 0.2)))

# before he shows up: two shoppers leave the cookie shop with pink boxes
SHOPPERS = [(4, Vector((0.6, 9.3, 0)), Vector((3.5, 2.0, 0)), 0.0), (5, Vector((-1.0, 9.3, 0)), Vector((-4.5, 3.0, 0)), 1.2)]

def shopper_state(n, a, b, t_start, t):
    f = CUST[n]
    u = (t - t_start) / 7.0
    if u < 0 or u > 1:
        return False
    d = b - a
    f["root"].location = a.lerp(b, u) + Vector((0, 0, 0.035 * abs(math.sin(t * 7.0 + n))))
    f["root"].rotation_euler = (0, 0, face_dir(d))
    s = math.sin(t * 7.0 + n)
    pose(f, walk=1.0, phase=t * 7.0 + n, arms=((-s * 0.45, 0, -0.08), (-0.9, 0, 0.35)))
    f["box"].scale = (1, 1, 1)
    f["bill"].scale = (0, 0, 0)
    return True

def lights_state(t):
    off = ramp(t, E["down"] - 0.1, E["down"] + 0.4)
    flick = 1.0 if off < 0.05 else (0.3 if math.sin(t * 40) > 0.3 else 1.0) * (1 - off)
    B.bsdf(MATS["cglass"]).inputs["Emission Strength"].default_value = 3.0 * flick + 0.02
    CSIGN_TXT.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 4.0 * flick
    shop_l.data.energy = 400.0 * flick + 20.0
    on = ramp(t, E["next"] - 0.8, E["next"] - 0.4)
    blink = 1.0 if on > 0.99 or math.sin(t * 35) > -0.2 else 0.2
    B.bsdf(MATS["dglass"]).inputs["Emission Strength"].default_value = 0.05 + 3.0 * on * blink
    DSIGN_TXT.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 4.0 * on * blink
    DONUT_M.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 1.5 * on * blink
    donut_l.data.energy = 380.0 * on * blink

def apply_state(t):
    coach_state(t)
    for n in range(len(CUST)):
        CUST[n]["root"].location = AWAY
    for n, a, b, ts in SHOPPERS:
        if t < E["D"] - 1.0:
            shopper_state(n, a, b, ts, t)
    for n in range(5):
        if MEETS[n] - WALK_IN - 0.3 <= t <= MEETS[n] + 6.0:
            customer_state(n, t)
    lights_state(t)
    loc, target, fstop, lens = camera_at(t)
    B.aim(cam, loc, target)
    cam.data.lens = lens
    cam.data.dof.focus_distance = (target - loc).length
    cam.data.dof.aperture_fstop = fstop
    cam.data.clip_start = 0.1
    cam.data.clip_end = 120

# ------------------------------------------------------------------ camera

def coach_at(z):
    p = COACH["root"].location
    if p.z < -1000:
        p = COACH_SPOT
    return p + Vector((0, 0, z))

def shot_hook(t):          # wide on the strip mall, slowly pushing toward the pink shop
    u = t
    return Vector((0.6, -1.5 + 0.25 * u, 2.2 + 0.03 * u)), Vector((-0.2, 10.0, 2.6))
def shot_lease(t):         # pan to the empty unit next door
    u = t - E["B"]
    return Vector((-9.6 + 0.1 * u, 4.6, 1.9)), Vector((-8.5, 10.0, 1.6))
def shot_econ(t):
    u = t - E["C"]
    return Vector((2.0 - 0.1 * u, 2.5, 3.0)), Vector((-0.5, 10.0, 2.2))
def shot_coach(t):         # he arrives: medium shot, low angle, shop glow behind
    u = t - E["D"]
    tg = Vector((-0.9, 8.2, 1.4))
    return Vector((-1.6 + 0.05 * u, 3.2 + 0.12 * u, 1.5)), tg
def shot_side(t):          # side view of the hand-off
    u = t - E["E"]
    return Vector((-2.5 + 0.05 * u, 4.4, 1.3)), Vector((-0.7, 8.0, 1.3))
def shot_low(t):
    u = t - E["F"]
    return Vector((-2.6 + 0.08 * u, 3.6, 0.8)), Vector((0.0, 9.0, 2.2))
def shot_close(t):         # close on him and the cash
    u = t - E["G"]
    tg = coach_at(1.75)
    return tg + Vector((-0.4, -2.7 + 0.08 * u, -0.1)), tg
def shot_wide2(t):
    u = t - E["H"]
    return Vector((0.5, 1.5 + 0.15 * u, 2.6)), Vector((-0.3, 8.0, 1.3))
def shot_push(t):          # slow push on his face
    u = t - E["I"]
    tg = coach_at(1.95)
    return tg + Vector((0.5, -2.6 + 0.25 * u, 0.0)), tg
def shot_end(t):           # the dark cookie shop, then a pan to the donut shop
    u = ramp(t, E["next"] - 1.6, E["next"] - 0.2)
    tg = Vector((-0.5, 10.0, 2.4)).lerp(Vector((6.5, 10.0, 2.4)), u)
    return Vector((1.2 + 2.0 * u, 2.2, 2.2)), tg

SHOTS = [(shot_hook, None), (shot_lease, (E["B"] - 0.25, E["B"] + 0.15)), (shot_econ, (E["C"] - 0.25, E["C"] + 0.15)),
         (shot_coach, (E["D"] - 0.25, E["D"] + 0.15)), (shot_side, (E["E"] - 0.25, E["E"] + 0.15)),
         (shot_low, (E["F"] - 0.25, E["F"] + 0.15)), (shot_close, (E["G"] - 0.25, E["G"] + 0.15)),
         (shot_wide2, (E["H"] - 0.25, E["H"] + 0.15)), (shot_push, (E["I"] - 0.25, E["I"] + 0.15)),
         (shot_end, (E["J"] - 0.25, E["J"] + 0.15))]
LENS = {shot_coach: 34.0, shot_side: 32.0, shot_hook: 26.0, shot_lease: 28.0, shot_close: 35.0, shot_push: 40.0, shot_end: 24.0, shot_wide2: 26.0}

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
    fstop = 2.0 if d < 3 else (2.8 if d < 6 else 5.6)
    return loc, tg, fstop, lens

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    names = ("coach", "shop", "lease", "donut", "cust")
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        active = [c for c in CUST[:5] if c["root"].location.z > -1000]
        pts = {
            "coach": COACH["head"].matrix_world @ Vector((0, 0, 0.7)) if COACH["root"].location.z > -1000 else None,
            "shop": Vector((0.0, 9.7, 4.7)),
            "lease": Vector((-8.5, 9.8, 2.1)),
            "donut": Vector((7.5, 9.7, 4.7)),
            "cust": active[0]["head"].matrix_world @ Vector((0, 0, 0.7)) if active else None,
        }
        for k, p in pts.items():
            v = world_to_camera_view(scene, cam, p) if p is not None else None
            out[k].append([round(v.x * 1080, 1), round((1 - v.y) * 1920, 1)]
                          if v is not None and v.z > 0 and 0 <= v.x <= 1 and 0 <= v.y <= 1 else None)
    with open(os.path.join(OUT, "anchors.json"), "w") as fh:
        json.dump(out, fh)

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1 + scn.frame_subframe) / FPS)

anchors()
apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
