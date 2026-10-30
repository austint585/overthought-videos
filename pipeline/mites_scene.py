"""Body-macro set: human skin. Two places in one file, one unit = about a millimeter on the skin:

  the skin (origin)     skin with furrows and pores, a few hairs, face mites (drawn large). Warm by day, blue at night.
                        shots: skin_in, hero, field, dusk, emerge, crawl, meet, rear, found, skin_out (ends on skin_in's first frame)
  the follicle (at S)   a pore cut in half: skin layers, a hair, a grease gland, mites inside, grease blobs
                        shots: section, pore, feed

blender -b --factory-startup -P mites_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Writes out_dir/anchors.json (screen points for labels, every frame).
"""
import json, math, os, random, sys
import bpy, bmesh
from mathutils import Vector, noise
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bkit as B

argv = sys.argv[sys.argv.index("--") + 1:]
TIMING, OUT, MODE = argv[0], argv[1], argv[2]
T = json.load(open(TIMING))
FPS, DUR = T["fps"], T["duration"]
NF = int(round(DUR * FPS))
SHOTS = T["shots"]
os.makedirs(OUT, exist_ok=True)
B.clear_scene()
scene = B.scene
rng = random.Random(11)
AWAY = Vector((0, 0, -1.0e4))

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

w = bpy.data.worlds.new("world")
scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.006, 0.004, 0.005, 1)

# ------------------------------------------------------------------ materials

def principled(m):
    return m.node_tree.nodes["Principled BSDF"]

def flesh(name, c0, c1, scale=6.0, bump=0.3, sss=0.4, rough=0.45, coat=0.5, cell=False):
    """Skin-like: blotchy two-tone color, subsurface, a thin oily coat, fine bump (cell=True adds a scaly pattern)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = principled(m)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.15
    b.inputs["Subsurface Weight"].default_value = sss
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    b.inputs["Subsurface Scale"].default_value = 0.05
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 8.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.35, 0.7
    ramp.color_ramp.elements[0].color, ramp.color_ramp.elements[1].color = (*c0, 1), (*c1, 1)
    nt.links.new(nz.outputs["Fac"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], b.inputs["Base Color"])
    src = nt.nodes.new("ShaderNodeTexNoise"); src.inputs["Scale"].default_value = scale * 14; src.inputs["Detail"].default_value = 5.0
    nt.links.new(tc.outputs["Object"], src.inputs["Vector"])
    out = src.outputs["Fac"]
    if cell:
        vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = scale * 3.5
        nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
        mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MINIMUM"
        nt.links.new(vo.outputs["Distance"], mx.inputs[0]); mx.inputs[1].default_value = 0.08
        ad = nt.nodes.new("ShaderNodeMath"); ad.operation = "MULTIPLY_ADD"; ad.inputs[1].default_value = 4.0
        nt.links.new(mx.outputs[0], ad.inputs[0]); nt.links.new(src.outputs["Fac"], ad.inputs[2])
        out = ad.outputs[0]
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.02
    nt.links.new(out, bp.inputs["Height"])
    nt.links.new(bp.outputs[0], b.inputs["Normal"])
    return m

def plain(name, color, rough=0.4, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = principled(m)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    return m

skin_m = flesh("skin", (0.62, 0.34, 0.26), (0.78, 0.48, 0.38), scale=2.6, bump=0.55, coat=0.2, cell=True)
mite_m = flesh("mite", (0.70, 0.56, 0.36), (0.88, 0.78, 0.56), scale=24.0, bump=0.5, sss=0.5, rough=0.3, coat=0.9)
leg_m = plain("leg", (0.50, 0.36, 0.20), rough=0.35, coat=0.5)
hair_m = plain("hair", (0.035, 0.022, 0.016), rough=0.35, coat=0.6)
oil_m = plain("oil", (0.95, 0.72, 0.22), rough=0.08, coat=1.0)
principled(oil_m).inputs["Emission Color"].default_value = (1.0, 0.62, 0.12, 1)
principled(oil_m).inputs["Emission Strength"].default_value = 0.25
rear_m = plain("rear", (0.20, 0.07, 0.05), rough=0.3)
principled(rear_m).inputs["Emission Color"].default_value = (1.0, 0.18, 0.03, 1)

# ------------------------------------------------------------------ skin

PORES = []
for gx in range(-3, 4):
    for gy in range(-3, 4):
        PORES.append(Vector((gx * 0.46 + rng.uniform(-0.1, 0.1), gy * 0.46 + rng.uniform(-0.1, 0.1), 0.0)))
P0 = PORES[24]                 # the hero's pore, near the middle

def h(x, y):
    z = 0.016 * noise.noise(Vector((x * 2.2, y * 2.2, 1.0))) + 0.005 * noise.noise(Vector((x * 12, y * 12, 3.0)))
    a, b = x * 1.0 + y * 0.45, x * -0.5 + y * 1.0                       # crossing furrows
    z -= 0.012 * (math.exp(-(math.sin(a * 12) / 0.28) ** 2) + math.exp(-(math.sin(b * 12) / 0.28) ** 2))
    for p in PORES:
        d2 = (x - p.x) ** 2 + (y - p.y) ** 2
        if d2 < 0.06:
            z -= 0.16 * math.exp(-d2 / 0.0035)
            z += 0.012 * math.exp(-((math.sqrt(d2) - 0.11) / 0.05) ** 2)   # a soft rim
    return z

def skin_build(bm):
    n = 420
    a, b = -1.6, 1.6
    verts = []
    for j in range(n + 1):
        for i in range(n + 1):
            x, y = a + (b - a) * i / n, a + (b - a) * j / n
            verts.append(bm.verts.new((x, y, h(x, y))))
    for j in range(n):
        for i in range(n):
            k = j * (n + 1) + i
            bm.faces.new((verts[k], verts[k + 1], verts[k + n + 2], verts[k + n + 1]))
skin = B.mesh_from("skin", skin_build, [skin_m])
B.smooth(skin, 80)

def curve(name, pts, bevel, mat):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = bevel; cu.bevel_resolution = 3
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p; bp.handle_left_type = bp.handle_right_type = "AUTO"
    ob = B.link(bpy.data.objects.new(name, cu)); ob.data.materials.append(mat)
    return ob

for i in (3, 10, 12, 33, 38, 45):
    p = PORES[i]
    d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized()
    curve(f"hair{i}", [p + Vector((0, 0, -0.1)), p + d * 0.12 + Vector((0, 0, 0.35)), p + d * 0.45 + Vector((0, 0, 0.8)), p + d * 1.0 + Vector((0, 0, 1.25))], 0.018, hair_m)

# ------------------------------------------------------------------ the mite: long tapered body, ringed rear, four pairs of stub legs, mouthparts. +x is forward.

def mite_body(bm):
    prof = [(-0.5, 0.004), (-0.48, 0.022), (-0.42, 0.034)]
    prof += [(-0.42 + 0.60 * i / 40, (0.040 + 0.024 * (i / 40)) * (1 + 0.05 * math.sin(i * 1.3))) for i in range(1, 41)]   # the ringed rear
    prof += [(0.22, 0.066), (0.30, 0.060), (0.38, 0.042), (0.44, 0.030), (0.50, 0.012), (0.52, 0.002)]
    rings = []
    for x, r in prof:
        rings.append([bm.verts.new((x, r * math.cos(2 * math.pi * k / 20), r * 0.85 * math.sin(2 * math.pi * k / 20))) for k in range(20)])
    for a, b in zip(rings, rings[1:]):
        for k in range(20):
            bm.faces.new((a[k], a[(k + 1) % 20], b[(k + 1) % 20], b[k]))

def stub(bm, side):
    """One short jointed leg, sticking out to one side and down."""
    a = Vector((0.0, side * 0.055, -0.012))
    b = Vector((0.015, side * 0.105, -0.040))
    c = Vector((0.035, side * 0.135, -0.075))
    for p, q, ra, rb in ((a, b, 0.016, 0.012), (b, c, 0.012, 0.006)):
        ax = q - p
        u = ax.cross(Vector((0, 0, 1))).normalized()
        v = ax.cross(u).normalized()
        ang = [2 * math.pi * k / 8 for k in range(8)]
        va = [bm.verts.new(p + (u * math.cos(t) + v * math.sin(t)) * ra) for t in ang]
        vb = [bm.verts.new(q + (u * math.cos(t) + v * math.sin(t)) * rb) for t in ang]
        for k in range(8):
            bm.faces.new((va[k], va[(k + 1) % 8], vb[(k + 1) % 8], vb[k]))

proto = B.mesh_from("mite_proto", mite_body, [mite_m])
B.smooth(proto, 80)
proto.location = AWAY
LEG_MESH = []
for x in (0.30, 0.22, 0.14, 0.06):
    for side in (1, -1):
        def build_leg(bm, side=side):
            stub(bm, side)
        ob = B.mesh_from(f"leg_{x}_{side}", build_leg, [leg_m])
        B.smooth(ob, 60)
        ob.location = AWAY
        LEG_MESH.append((ob.data, x, side))

class Mite:
    def __init__(self, name, scale):
        self.root = B.link(bpy.data.objects.new(name, proto.data))
        self.root.rotation_mode = "QUATERNION"
        self.root.scale = (scale, scale, scale)
        self.legs = []
        for mesh, x, side in LEG_MESH:
            l = B.link(bpy.data.objects.new(f"{name}_l", mesh))
            l.parent = self.root
            l.location = (x, 0, 0)
            self.legs.append((l, x, side))
        self.pos = AWAY
    def place(self, pos, heading=None, step=0.0):
        """heading: the direction of +x. step: the walk cycle phase."""
        self.pos = pos
        self.root.location = pos
        d = heading if heading is not None else Vector((1, 0, 0))
        self.root.rotation_quaternion = d.to_track_quat("X", "Z")
        for i, (l, x, side) in enumerate(self.legs):
            p = step * 2 * math.pi + i * math.pi / 2 + (0 if side > 0 else math.pi)
            l.rotation_euler = (0.12 * side * math.sin(p), 0, 0.45 * math.cos(p))
    def hide(self):
        self.place(AWAY)

M0, M1 = Mite("m0", 0.55), Mite("m1", 0.55)
FIELD = []                                  # tails poking out of pores
for i, p in enumerate(PORES):
    if i != 24 and rng.random() < 0.72:
        FIELD.append((Mite(f"f{i}", 0.9), p, rng.uniform(0, 6.28), rng.uniform(0.18, 0.34)))

def pose_surface(m, x, y, heading, step, lift=0.045):
    m.place(Vector((x, y, h(x, y) + lift)), Vector((math.cos(heading), math.sin(heading), 0.0)), step)

# the odd spot on the hero's rear: a small dark dot that lights up when the study says they do
def rear_build(bm):
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.012)
rear_ob = B.mesh_from("rear", rear_build, [rear_m])
rear_ob.parent = M0.root
rear_ob.location = (-0.492, 0, 0.0)

# ------------------------------------------------------------------ the follicle: skin cut in half at S

S = Vector((12.0, 0.0, 0.0))
PW, DEPTH = 0.42, 4.2                       # half width of the pore, depth

def layered():
    m = flesh("cut", (0.80, 0.42, 0.36), (0.92, 0.55, 0.48), scale=2.0, bump=0.3, sss=0.5, coat=0.3)
    nt = m.node_tree
    b = principled(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    r = nt.nodes.new("ShaderNodeMapRange"); r.inputs["From Min"].default_value = -0.75; r.inputs["From Max"].default_value = -0.55
    nt.links.new(sep.outputs["Z"], r.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    old = b.inputs["Base Color"].links[0].from_socket
    nt.links.new(old, mix.inputs["A"])
    mix.inputs["B"].default_value = (0.86, 0.66, 0.52, 1)
    nt.links.new(r.outputs[0], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    return m
cut_m = layered()
for name, a, b_ in (("left", -5.0, -PW), ("right", PW, 5.0)):
    ob = B.mesh_from(f"cut_{name}", B.box(a, b_, 0, 3.0, -DEPTH - 2.0, 0.0), [cut_m])
    ob.location = S
ob = B.mesh_from("cut_below", B.box(-PW + 0.001, PW - 0.001, 0, 3.0, -DEPTH - 2.0, -DEPTH), [cut_m])
ob.location = S
pocket = B.mesh_from("cut_back", B.box(-PW + 0.001, PW - 0.001, 0.45, 3.0, -DEPTH + 0.001, 0.0), [plain("back", (0.42, 0.14, 0.13), rough=0.6, coat=0.5)])
pocket.location = S
curve("s_hair", [S + Vector((0.03, 0.3, -DEPTH + 0.1)), S + Vector((0.02, 0.3, -2.0)), S + Vector((-0.02, 0.3, 0.0)), S + Vector((-0.25, 0.3, 2.2))], 0.11, hair_m)
def gland_build(bm):
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=0.9)
gland = B.mesh_from("gland", gland_build, [plain("gland", (0.92, 0.68, 0.22), rough=0.25, coat=1.0)])
B.smooth(gland, 80)
gland.location = S + Vector((1.25, -0.25, -2.3))
gland.scale = (1.0, 0.35, 1.25)
SM = [Mite(f"s{i}", 2.2) for i in range(4)]
SM_HOME = [(Vector((-0.20, 0.10, -1.05)), 1.9), (Vector((0.22, 0.14, -1.85)), 1.4), (Vector((-0.14, 0.12, -2.75)), 1.75), (Vector((0.18, 0.08, -3.5)), 1.5)]
OIL = []
for i in range(16):
    def oil_build(bm, r=rng.uniform(0.05, 0.11)):
        bmesh.ops.create_icosphere(bm, subdivisions=3, radius=r)
    ob = B.mesh_from(f"oil{i}", oil_build, [oil_m])
    B.smooth(ob, 80)
    OIL.append((ob, S + Vector((rng.uniform(-0.32, 0.32), rng.uniform(-0.05, 0.25), rng.uniform(-3.9, -0.6))), rng.uniform(0, 6.28)))

# ------------------------------------------------------------------ lights

key = B.area("key", (-1.4, -1.5, 1.8), (0, 0, 0), 1.6, 26.0, color=(1.0, 0.86, 0.72))
rim = B.area("rim", (1.5, 1.6, 0.8), (0, 0, 0), 1.0, 24.0, color=(1.0, 0.72, 0.58))
moon = B.area("moon", (1.2, -1.6, 1.3), (0, 0, 0), 1.2, 0.0, color=(0.40, 0.58, 1.0))
moon2 = B.area("moon2", (-1.6, 1.2, 0.5), (0, 0, 0), 1.0, 0.0, color=(0.42, 0.50, 1.0))
key2 = B.area("key2", S + Vector((-2.5, -6.0, 3.0)), S + Vector((0, 0, -2)), 3.0, 170.0, color=(1.0, 0.9, 0.8))
rim2 = B.area("rim2", S + Vector((3.0, -3.0, 1.0)), S + Vector((0, 0, -2)), 2.0, 40.0, color=(1.0, 0.65, 0.55))
SKIN_LIGHTS, CUT_LIGHTS = [key, rim, moon, moon2], [key2, rim2]

# ------------------------------------------------------------------ shots

cam = B.camera(lens=35, fstop=3.2)
cam.data.clip_start = 0.005

def lerp_cam(a, b, target, lens, fstop, u):
    return a.lerp(b, smooth01(u)), target, lens, fstop

PATH0 = P0 + Vector((0.05, -0.28, 0.0))        # where the hero is on frame 1 (and the last frame)
MEET = P0 + Vector((0.42, 0.20, 0.0))

def hero_pt():
    return M0.pos + Vector((0, 0, 0.02))

def rear_pt():
    return M0.root.matrix_world @ Vector((-0.49, 0, 0))

def skin_in(u):
    return lerp_cam(PATH0 + Vector((0.34, -0.76, 0.46)), PATH0 + Vector((0.26, -0.60, 0.34)), PATH0 + Vector((0, 0.02, 0.02)), 50, 8.0, u)

CAMS = {
    "skin_in": skin_in,
    "skin_out": lambda u: skin_in(1.0 - u),
    "hero": lambda u: lerp_cam(PATH0 + Vector((-0.34, -0.38, 0.16)), PATH0 + Vector((-0.26, -0.30, 0.13)), PATH0 + Vector((0.02, 0, 0.03)), 60, 11.0, u),
    "field": lambda u: lerp_cam(Vector((0.1, -1.15, 1.25)), Vector((0.0, -1.55, 1.75)), Vector((0, 0.05, 0.0)), 35, 11.0, u),
    "section": lambda u: lerp_cam(S + Vector((0.0, -7.2, -1.6)), S + Vector((0.0, -6.0, -1.8)), S + Vector((0.0, 0, -1.85)), 50, 16.0, u),
    "pore": lambda u: lerp_cam(S + Vector((0.35, -3.2, -0.7)), S + Vector((0.2, -2.6, -0.9)), S + Vector((0.0, 0, -0.9)), 50, 16.0, u),
    "feed": lambda u: lerp_cam(S + Vector((-0.2, -2.0, -2.0)), S + Vector((-0.3, -1.6, -2.1)), S + Vector((0.1, 0, -1.9)), 50, 16.0, u),
    "dusk": lambda u: lerp_cam(Vector((0.1, -1.05, 1.10)), Vector((0.05, -0.85, 0.8)), P0 * 0.6, 35, 11.0, u),
    "emerge": lambda u: lerp_cam(P0 + Vector((-0.30, -0.66, 0.34)), P0 + Vector((-0.24, -0.56, 0.28)), P0 + Vector((0.06, 0, 0.04)), 55, 11.0, u),
    "crawl": lambda u: lerp_cam(hero_pt() + Vector((-0.30, -0.46, 0.13)), hero_pt() + Vector((-0.22, -0.40, 0.12)), hero_pt(), 50, 11.0, u),
    "meet": lambda u: lerp_cam(MEET + Vector((0.36, -0.62, 0.28)), MEET + Vector((0.20, -0.56, 0.20)), MEET + Vector((0, 0, 0.03)), 55, 11.0, u),
    "rear": lambda u: lerp_cam(rear_pt() + Vector((-0.30, -0.36, 0.20)), rear_pt() + Vector((-0.22, -0.28, 0.15)), rear_pt() + Vector((0.08, 0, 0.0)), 60, 16.0, u),
    "found": lambda u: lerp_cam(rear_pt() + Vector((-0.20, -0.18, 0.08)), rear_pt() + Vector((-0.14, -0.13, 0.06)), rear_pt(), 70, 22.0, u),
}
CUT_SHOTS = {"section", "pore", "feed"}
NIGHT = {"dusk", "emerge", "crawl", "meet", "rear", "found"}

def shot_at(t):
    k = max([0] + [i for i, (s, _) in enumerate(SHOTS) if t >= s - 1e-6])
    t0 = SHOTS[k][0]
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    return SHOTS[k][1], max(0.0, min(1.0, (t - t0) / max(1e-6, t1 - t0))), t - t0

def apply_state(t):
    name, u, age = shot_at(t)
    cut = name in CUT_SHOTS
    night = 0.0
    if name in NIGHT:
        night = smooth01(u / 0.7) if name == "dusk" else 1.0
    key.data.energy = 26.0 * (1 - night)
    rim.data.energy = 24.0 * (1 - night) + 2.0 * night
    moon.data.energy = 48.0 * night
    moon2.data.energy = 26.0 * night
    for ob in SKIN_LIGHTS:
        ob.hide_render = cut
    for ob in CUT_LIGHTS:
        ob.hide_render = not cut
    # the heroes
    if name in ("skin_in", "skin_out", "hero"):
        d = 0.22 * math.sin(t * 2 * math.pi / DUR)                 # back at the same spot on the last frame
        pose_surface(M0, PATH0.x + d, PATH0.y + 0.2 * d, 0.2 + 0.25 * math.sin(t * 2 * math.pi / DUR), 0.9 * t)
        M1.hide()
    elif name == "emerge":                                         # climbing up out of the pore, nose first
        k = smooth01(u / 0.8)
        d = Vector((0.45 * k, 0, 1.0 - 0.8 * k)).normalized()
        M0.place(P0 + Vector((0.08 * k, 0, -0.20 + 0.27 * k)), d, t * 2.6)
        M1.hide()
    elif name == "crawl":
        pose_surface(M0, P0.x + 0.08 + 0.10 * smooth01(u), P0.y + 0.14 * u, 0.3, t * 2.8)
        pose_surface(M1, MEET.x + 0.78 - 0.16 * u, MEET.y + 0.05, math.pi - 0.1, t * 2.6)
    elif name == "meet":                                           # they walk in and bump heads, tails wiggling
        k = smooth01(u / 0.45)
        wig = 0.12 * math.sin(age * 14) * smooth01((u - 0.45) / 0.15)
        pose_surface(M0, MEET.x - 0.62 + 0.335 * k, MEET.y - 0.02, wig, t * 2.8 if k < 1 else 0.0)
        pose_surface(M1, MEET.x + 0.62 - 0.335 * k, MEET.y + 0.02, math.pi - wig, t * 2.6 if k < 1 else 0.0)
    elif name in ("rear", "found"):
        pose_surface(M0, MEET.x - 0.285, MEET.y - 0.02, 0.0, 0.0)
        pose_surface(M1, MEET.x + 0.285, MEET.y + 0.02, math.pi, 0.0)
    else:
        M0.hide(); M1.hide()
    bpy.context.view_layer.update()
    principled(rear_m).inputs["Emission Strength"].default_value = 1.1 * smooth01((age - 0.45) / 0.15) if name == "found" else 0.0
    # tails in the pores, wiggling a little
    for m, p, ph, out in FIELD:
        if name in ("field", "dusk"):
            m.place(p + Vector((0.01 * math.sin(t * 3 + ph), 0.01 * math.cos(t * 2.7 + ph), -0.45 + out)), Vector((0.08 * math.sin(ph), 0.08 * math.cos(ph), -1.0)), 0.0)
        else:
            m.hide()
    # the follicle
    for i, (m, (home, sc)) in enumerate(zip(SM, SM_HOME)):
        if cut:
            m.place(S + home + Vector((0.015 * math.sin(t * 2.3 + i), 0, 0.03 * math.sin(t * 1.7 + i * 2))), Vector((0.08 * math.sin(i * 1.7 + t), 0.05, -1.0)).normalized(), t * 0.8 + i * 0.3)
            m.root.scale = (sc, sc, sc)
        else:
            m.hide()
    for ob, p, ph in OIL:
        if cut:
            ob.location = p + Vector((0.02 * math.sin(t + ph), 0, 0.03 * math.sin(t * 0.8 + ph)))
            sh = 1.0 - (0.75 * smooth01((u - 0.1) / 0.8) if name == "feed" and p.z < S.z - 1.2 else 0.0)
            ob.scale = (sh, sh, sh)
        else:
            ob.location = AWAY
    loc, tg, lens, fstop = CAMS[name](u)
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    cam.data.dof.aperture_fstop = fstop
    cam.data.dof.focus_distance = (tg - loc).length

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    pts = {
        "hero": lambda: M0.pos + Vector((0.1, 0, 0.04)),
        "smite": lambda: S + SM_HOME[1][0] + Vector((0, -0.08, 0.1)),
        "follicle": lambda: S + Vector((-PW, 0.05, -0.8)),
        "oil": lambda: OIL[0][0].location.copy(),
        "rear": lambda: rear_pt(),
    }
    out = {k: [] for k in pts}
    vl = bpy.context.view_layer
    for fr in range(NF):
        apply_state(fr / FPS)
        vl.update()
        for k, fn in pts.items():
            v = world_to_camera_view(scene, cam, fn())
            out[k].append([round(v.x * 1080, 1), round((1 - v.y) * 1920, 1)] if v.z > 0 and 0 <= v.x <= 1 and 0 <= v.y <= 1 else None)
    with open(os.path.join(OUT, "anchors.json"), "w") as fh:
        json.dump(out, fh)

B.render_settings(FPS, samples=int(os.environ.get("MITES_SAMPLES", "48")), motion_blur=0.25, look="AgX - Medium High Contrast")

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1 + scn.frame_subframe) / FPS)

anchors()
apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
