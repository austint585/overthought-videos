"""Product-studio kit, microwave set: Poly Haven's CC0 vintage microwave on the walnut desk in a dark studio (the
outside shots), and a cutaway oven cavity we model ourselves (no front wall) with a glass turntable, a plate and a
stainless fork, for everything inside. Shots are named; the render script lists them with start times:

  front, front_out     the microwave on the desk, lit inside, sparks flashing behind the glass (front_out ends on
                       front's first frame, for the loop)
  spark_tip            close on the tines, an arc jumping off a tip
  waves                the cavity, wide: plate and fork under the oven light
  food                 a mug of water warming up (glowing warm)
  reflect              the fork on the plate, low
  electrons, tips      macro of the tines: electrons slosh back and forth, then crowd at the tips
  breakdown            macro of one tip: air molecules beside it light up violet
  spark                the arc between a tine and the plate rim
  spoon                a smooth spoon on the plate, calm
  foil                 a crumpled foil ball crackling with small arcs (and hopping a little)
  scorch               the cavity wall, a scorch mark spreading and a small flame

blender -b --factory-startup -P fork_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Writes out_dir/anchors.json (screen points for labels, every frame).
"""
import json, math, os, random, sys
import bpy, bmesh
from mathutils import Euler, Matrix, Vector, noise
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bkit as B
import assets as A

argv = sys.argv[sys.argv.index("--") + 1:]
TIMING, OUT, MODE = argv[0], argv[1], argv[2]
T = json.load(open(TIMING))
FPS, DUR = T["fps"], T["duration"]
NF = int(round(DUR * FPS))
SHOTS = T["shots"]
os.makedirs(OUT, exist_ok=True)
B.clear_scene()
scene = B.scene
rng = random.Random(9)
AWAY = Vector((0, 0, -1.0e4))
WARM = (1.0, 0.72, 0.38)
ARC = (0.78, 0.62, 1.0)
EBLUE = (0.15, 0.45, 1.0)
HOT = (1.0, 0.35, 0.06)

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

# ------------------------------------------------------------------ world and materials (as led_scene.py)

def world():
    w = bpy.data.worlds.new("world")
    scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(A.hdri_path("brown_photostudio_02"))
    hdr = nt.nodes.new("ShaderNodeBackground"); hdr.inputs[1].default_value = 0.22
    dark = nt.nodes.new("ShaderNodeBackground"); dark.inputs[0].default_value = (0.004, 0.004, 0.006, 1)
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(env.outputs[0], hdr.inputs[0])
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(hdr.outputs[0], mix.inputs[1])
    nt.links.new(dark.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
world()

def principled(m):
    return m.node_tree.nodes["Principled BSDF"]

def plain(name, color, rough=0.4, metal=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = principled(m)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    return m

def emit(m, color, strength):
    b = principled(m)
    b.inputs["Emission Color"].default_value = (*color, 1)
    b.inputs["Emission Strength"].default_value = strength

def glowing(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (*color, 1); e.inputs[1].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs[0])
    return m

def object_color_glow(name, strength):
    """Emission colored by each object's own color (dots that change color per object)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs[1].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(oi.outputs["Color"], e.inputs[0]); nt.links.new(e.outputs[0], o.inputs[0])
    return m

def pbr_texture(name, asset, tile):
    maps = A.texture_maps(asset)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / tile, 1 / tile, 1 / tile)
    nt.links.new(tc.outputs["Object"], mp.inputs[0])
    def img(key, non_color=False):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(maps[key])
        if non_color:
            t.image.colorspace_settings.name = "Non-Color"
        nt.links.new(mp.outputs[0], t.inputs[0])
        return t
    nt.links.new(img("Diffuse").outputs[0], b.inputs["Base Color"])
    nt.links.new(img("Rough", True).outputs[0], b.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(img("nor_gl", True).outputs[0], nm.inputs["Color"])
    nt.links.new(nm.outputs[0], b.inputs["Normal"])
    b.inputs["Coat Weight"].default_value = 0.25
    b.inputs["Coat Roughness"].default_value = 0.18
    return m

def value(nt, key, v=0.0):
    n = nt.nodes.new("ShaderNodeValue"); n.name = key; n.outputs[0].default_value = v
    return n.outputs[0]

def setv(m, key, v):
    m.node_tree.nodes[key].outputs[0].default_value = v

def sphere(name, r, mat, subdiv=2):
    def b(bm):
        bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    ob = B.mesh_from(name, b, [mat])
    B.smooth(ob, 80)
    return ob

def arc_curve(name, n, mat, bevel):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = bevel
    sp = cu.splines.new("POLY"); sp.points.add(n - 1)
    ob = B.link(bpy.data.objects.new(name, cu)); ob.data.materials.append(mat)
    return ob

def set_arc(ob, a, b, seed, jag):
    """A jagged lightning path from a to b, a new shape for every seed."""
    r = random.Random(seed)
    pts = ob.data.splines[0].points
    n = len(pts)
    d = b - a
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-6:
        side = Vector((1, 0, 0))
    side.normalize()
    up = d.cross(side).normalized()
    for i, p in enumerate(pts):
        k = i / (n - 1)
        off = 0.0 if i in (0, n - 1) else jag * d.length * math.sin(math.pi * k)
        q = a + d * k + side * r.uniform(-off, off) + up * r.uniform(-off, off)
        p.co = (q.x, q.y, q.z, 1.0)

# ------------------------------------------------------------------ outside: the real microwave on the desk

def import_model(asset, loc, scale):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=A.model_path(asset))
    obs = [o for o in bpy.data.objects if o not in before]
    root = next(o for o in obs if o.parent is None)
    root.location = loc
    root.scale = (scale, scale, scale)
    return root, obs

MW_S = 0.5
mw, mw_obs = import_model("vintage_microwave", Vector((0, 0, 0)), MW_S)
for ob in mw_obs:
    for m in getattr(ob.data, "materials", []) or []:
        if m and "glass" in m.name:
            b = principled(m)
            b.inputs["Alpha"].default_value = 0.35
            b.inputs["Roughness"].default_value = 0.05
            m.surface_render_method = "BLENDED" if hasattr(m, "surface_render_method") else m.surface_render_method
            m.use_transparent_shadow = True
desk_m = pbr_texture("walnut", "black_walnut_veneer_01", 0.9)
B.mesh_from("desk", B.box(-1.4, 1.4, -1.0, 1.4, -0.04, 0.0), [desk_m])
for i in range(5):
    p = Vector((rng.uniform(-1.8, 1.8), rng.uniform(2.6, 4.0), rng.uniform(0.2, 1.2)))
    B.mesh_from(f"bokeh{i}", B.cyl_z(0.035, p.z - 0.002, p.z + 0.002, p.x, p.y, seg=24), [glowing(f"bk{i}", (1.0, 0.62, 0.32), rng.uniform(3, 9))])
# a warm-lit inside behind the window: a glowing back panel, a plate, and a little fork silhouette
inside_m = plain("inside", (0.85, 0.80, 0.70), rough=0.5)
emit(inside_m, WARM, 1.2)
B.mesh_from("inside_back", B.box(-0.17, 0.20, 0.10, 0.11, 0.04, 0.22), [inside_m])
B.mesh_from("inside_floor", B.box(-0.17, 0.20, -0.15, 0.11, 0.035, 0.04), [plain("inside_floor", (0.75, 0.72, 0.65), rough=0.5)])
in_light = bpy.data.lights.new("in_light", "POINT")
in_light.energy, in_light.color, in_light.shadow_soft_size = 4.0, WARM, 0.05
inl = B.link(bpy.data.objects.new("in_light", in_light)); inl.location = (0.0, -0.02, 0.18)
key1 = B.area("key1", (-0.9, -0.9, 0.9), (0, 0, 0.13), 0.7, 13.0, color=(1.0, 0.86, 0.70))
rim1 = B.area("rim1", (0.8, 0.7, 0.7), (0, 0, 0.13), 0.5, 22.0, color=(0.65, 0.75, 1.0))
WIN_Y = -0.1925
win_m = plain("win", (0.1, 0.08, 0.05), rough=0.6)
emit(win_m, (1.0, 0.5, 0.18), 0.16)
B.mesh_from("win_panel", B.box(-0.19, 0.13, WIN_Y, WIN_Y + 0.001, 0.056, 0.188), [win_m])
sil_m = plain("sil", (0.01, 0.01, 0.01), rough=0.6)
B.mesh_from("win_plate", B.box(-0.13, 0.07, WIN_Y - 0.0006, WIN_Y, 0.072, 0.079), [sil_m])
B.mesh_from("win_fork", B.box(-0.09, 0.03, WIN_Y - 0.0007, WIN_Y, 0.082, 0.086), [sil_m])
OUT_SET = mw_obs + [inl]
OUT_HOME = {o: o.location.copy() for o in OUT_SET}
front_arc_m = glowing("front_arc", ARC, 30.0)
front_arc = arc_curve("front_arc", 12, front_arc_m, 0.0009)
front_spark = bpy.data.lights.new("front_spark", "POINT")
front_spark.color, front_spark.shadow_soft_size = ARC, 0.01
fsl = B.link(bpy.data.objects.new("front_spark", front_spark)); fsl.location = (0.04, WIN_Y - 0.03, 0.10)

# ------------------------------------------------------------------ inside: the cutaway cavity at C

C = Vector((4.0, 0.0, 0.0))
CX, CY, CZ = 0.36, 0.32, 0.22                 # cavity inner width, depth, height
enamel_m = plain("enamel", (0.11, 0.11, 0.115), rough=0.38)
scorch_m = plain("enamel_scorch", (0.11, 0.11, 0.115), rough=0.38)
snt = scorch_m.node_tree
sb = principled(scorch_m)
tc = snt.nodes.new("ShaderNodeTexCoord")
dist = snt.nodes.new("ShaderNodeVectorMath"); dist.operation = "DISTANCE"
dist.inputs[1].default_value = (0.05, 0.0, 0.06)
snt.links.new(tc.outputs["Object"], dist.inputs[0])
nz = snt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 40.0
snt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
mul = snt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 0.035
snt.links.new(nz.outputs["Fac"], mul.inputs[0])
add = snt.nodes.new("ShaderNodeMath"); add.operation = "ADD"
snt.links.new(dist.outputs["Value"], add.inputs[0]); snt.links.new(mul.outputs[0], add.inputs[1])
burn = value(snt, "burn")
edge = snt.nodes.new("ShaderNodeMath"); edge.operation = "SUBTRACT"; edge.inputs[1].default_value = 0.022
snt.links.new(burn, edge.inputs[0])
lt = snt.nodes.new("ShaderNodeMapRange"); lt.interpolation_type = "SMOOTHSTEP"
lt.inputs["To Min"].default_value = 1.0; lt.inputs["To Max"].default_value = 0.0
snt.links.new(add.outputs[0], lt.inputs["Value"]); snt.links.new(edge.outputs[0], lt.inputs["From Min"]); snt.links.new(burn, lt.inputs["From Max"])
mixc = snt.nodes.new("ShaderNodeMix"); mixc.data_type = "RGBA"
mixc.inputs["A"].default_value = (0.11, 0.11, 0.115, 1); mixc.inputs["B"].default_value = (0.012, 0.010, 0.008, 1)
snt.links.new(lt.outputs[0], mixc.inputs["Factor"]); snt.links.new(mixc.outputs["Result"], sb.inputs["Base Color"])

x0, x1, y0, y1, z0, z1 = C.x - CX / 2, C.x + CX / 2, C.y - CY / 2, C.y + CY / 2, C.z, C.z + CZ
W_T = 0.008
B.mesh_from("cav_floor", B.box(x0 - W_T, x1 + W_T, y0, y1 + W_T, z0 - W_T, z0), [enamel_m])
B.mesh_from("cav_top", B.box(x0 - W_T, x1 + W_T, y0, y1 + W_T, z1, z1 + W_T), [enamel_m])
B.mesh_from("cav_left", B.box(x0 - W_T, x0, y0, y1 + W_T, z0, z1), [enamel_m])
cav_right = B.mesh_from("cav_right", B.box(x1, x1 + W_T, y0, y1 + W_T, z0, z1), [enamel_m])
cav_back = B.mesh_from("cav_back", B.box(-CX / 2, CX / 2, 0, W_T, 0, CZ), [scorch_m])
cav_back.location = Vector((C.x, y1, z0))
glass_m = plain("turntable", (0.9, 0.95, 0.9), rough=0.03)
principled(glass_m).inputs["Transmission Weight"].default_value = 1.0
for attr in ("use_raytrace_refraction", "use_screen_refraction"):
    if hasattr(glass_m, attr):
        setattr(glass_m, attr, True)
tt = B.mesh_from("turntable", B.cyl_z(0.14, z0 + 0.010, z0 + 0.016, C.x, C.y, seg=96), [glass_m])
plate_m = plain("plate", (0.09, 0.10, 0.115), rough=0.5, coat=0.0)
def plate_build(bm):
    prof = [(0.0, 0.0), (0.075, 0.0), (0.085, 0.004), (0.11, 0.016), (0.112, 0.018)]
    rings = []
    for r, z in prof:
        ring = [bm.verts.new((r * math.cos(2 * math.pi * k / 96), r * math.sin(2 * math.pi * k / 96), z)) for k in range(96)]
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(96):
            bm.faces.new((a[k], a[(k + 1) % 96], b[(k + 1) % 96], b[k]))
plate = B.mesh_from("plate", plate_build, [plate_m])
B.smooth(plate, 60)
plate.location = C + Vector((0, 0, 0.016))
PLATE_Z = C.z + 0.016

steel_m = plain("steel", (0.88, 0.88, 0.90), rough=0.28, metal=1.0)
emit(steel_m, (0.72, 0.76, 0.82), 0.14)
tipglow_m = plain("tipglow", (0.88, 0.88, 0.90), rough=0.16, metal=1.0)
emit(tipglow_m, (0.55, 0.65, 1.0), 0.0)

# the fork, lying on the plate along +x, tines toward +x, bowed so the tines lift a little
FORK = []
TINES = []
def fork_build(bm):
    def slab(xa, xb, wa, wb, z, th):
        v = [bm.verts.new((xa, -wa / 2, z)), bm.verts.new((xb, -wb / 2, z)), bm.verts.new((xb, wb / 2, z)), bm.verts.new((xa, wa / 2, z)),
             bm.verts.new((xa, -wa / 2, z + th)), bm.verts.new((xb, -wb / 2, z + th)), bm.verts.new((xb, wb / 2, z + th)), bm.verts.new((xa, wa / 2, z + th))]
        for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            bm.faces.new([v[i] for i in f])
    slab(-0.09, -0.02, 0.018, 0.010, 0.0, 0.0030)     # handle
    slab(-0.02, 0.025, 0.010, 0.024, 0.0, 0.0028)     # neck widening into the head
fork = B.mesh_from("fork", fork_build, [steel_m])
B.bevel(fork, 0.0009, 2)
B.smooth(fork, 40)
FORK_HOME = C + Vector((0.01, -0.01, PLATE_Z - C.z + 0.0035))
FORK_ROT = Euler((0, 0, 0.25))
fork.location = FORK_HOME
fork.rotation_euler = FORK_ROT
FORK_MAT = Matrix.Translation(FORK_HOME) @ FORK_ROT.to_matrix().to_4x4()      # fixed: never stale inside a frame handler
TINE_MAT = FORK_MAT @ Matrix.Translation((0.025, 0, 0))
for k in range(4):
    yk = -0.0090 + k * 0.0060
    def tine_build(bm, yk=yk):
        L, w, th = 0.045, 0.0032, 0.0026
        base = [bm.verts.new((0, yk - w / 2, 0)), bm.verts.new((0, yk + w / 2, 0)), bm.verts.new((0, yk + w / 2, th)), bm.verts.new((0, yk - w / 2, th))]
        tip = bm.verts.new((L, yk, th * 0.5))
        bm.faces.new(base[::-1])
        for i in range(4):
            bm.faces.new((base[i], base[(i + 1) % 4], tip))
    t = B.mesh_from(f"tine{k}", tine_build, [tipglow_m])
    t.parent = fork
    t.location = (0.025, 0, 0)
    TINES.append(t)
def tip_world(k):
    return TINE_MAT @ Vector((0.045, -0.0090 + k * 0.0060, 0.0013))

# the spoon (its own shot), the mug of water, the foil ball
spoon = B.mesh_from("spoon_handle", B.box(-0.10, 0.0, -0.005, 0.005, 0.0, 0.0028), [steel_m])
B.bevel(spoon, 0.0012, 3); B.smooth(spoon, 40)
bowl = sphere("spoon_bowl", 0.022, steel_m, 3)
bowl.scale = (1.3, 0.85, 0.22)
bowl.parent = spoon
bowl.location = (0.025, 0, 0.004)
mug_m = plain("mug", (0.12, 0.30, 0.55), rough=0.25, coat=0.6)
mug = B.mesh_from("mug", B.cyl_z(0.04, 0.0, 0.09, 0, 0, seg=64), [mug_m])
B.boolean(mug, [(B.cyl_z(0.035, 0.006, 0.10, 0, 0, seg=64), "DIFFERENCE")])
B.smooth(mug, 40)
water_m = plain("water", (0.6, 0.75, 0.85), rough=0.05)
emit(water_m, HOT, 0.0)
water = B.mesh_from("water", B.cyl_z(0.0349, 0.006, 0.075, 0, 0, seg=64), [water_m])
water.parent = mug
foil_m = plain("foil", (0.85, 0.85, 0.87), rough=0.22, metal=1.0)
def foil_build(bm):
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=0.03)
    for v in bm.verts:
        n = noise.noise(v.co * 90)
        v.co *= 1.0 + 0.30 * n + 0.12 * noise.noise(v.co * 260)
foil = B.mesh_from("foil", foil_build, [foil_m])
SPOON_HOME = C + Vector((-0.02, 0.0, PLATE_Z - C.z + 0.003))
MUG_HOME = C + Vector((0.0, 0.0, PLATE_Z - C.z + 0.002))
FOIL_HOME = C + Vector((0.0, 0.0, PLATE_Z - C.z + 0.025))

oven_light = bpy.data.lights.new("oven_light", "POINT")
oven_light.energy, oven_light.color, oven_light.shadow_soft_size = 1.5, WARM, 0.04
ovl = B.link(bpy.data.objects.new("oven_light", oven_light)); ovl.location = C + Vector((0.12, 0.10, CZ - 0.02))
key2 = B.area("key2", C + Vector((-0.4, -0.7, 0.35)), C + Vector((0, 0, 0.05)), 0.5, 3.5, color=(1.0, 0.88, 0.75))
top2 = B.area("top2", C + Vector((0.08, -0.12, 0.36)), C + Vector((0.03, 0, 0.02)), 0.28, 4.5, color=(1.0, 0.96, 0.90))
rim2 = B.area("rim2", C + Vector((0.4, -0.5, 0.30)), C + Vector((0, 0, 0.05)), 0.3, 2.0, color=(0.6, 0.72, 1.0))
arc_m = glowing("arc", ARC, 16.0)
ARCS = [arc_curve(f"arc{i}", 14, arc_m, 0.00022 if i else 0.00035) for i in range(4)]
spark_l = bpy.data.lights.new("spark_l", "POINT")
spark_l.color, spark_l.shadow_soft_size = ARC, 0.005
spl = B.link(bpy.data.objects.new("spark_l", spark_l))
flame_m = glowing("flame", (1.0, 0.16, 0.01), 1.1)
flame_core_m = glowing("flame_core", (1.0, 0.42, 0.05), 2.0)
FLAMES = []
for i in range(7):
    core = i >= 4
    def b(bm, seed=i * 3.7, r=0.0035 if core else 0.0062, h=0.016 if core else 0.028):
        bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
        for v in bm.verts:
            k = (v.co.z + 1) / 2
            w = (1 - k) ** 0.75 * (0.35 + 0.65 * min(1.0, k * 5))
            n = noise.noise(v.co * 2.2 + Vector((seed, 0, 0)))
            v.co = Vector((v.co.x * r * w * (1 + 0.5 * n), v.co.y * r * w, k * h * (1 + 0.35 * n)))
    ob = B.mesh_from(f"flame{i}", b, [flame_core_m if core else flame_m])
    B.smooth(ob, 80)
    FLAMES.append((ob, Vector((rng.uniform(-0.012, 0.012), rng.uniform(-0.005, 0.005) - (0.002 if core else 0.0), 0.0)), rng.uniform(0, 6.28)))

dot_m = object_color_glow("dot", 3.0)
ELECTRONS = []                                    # (object, tine, position 0..1 along it, side offset)
for k in range(4):
    for i in range(9):
        ELECTRONS.append((sphere(f"e{k}_{i}", 0.00042, dot_m, 2), k, rng.uniform(0.0, 1.0), rng.uniform(-0.0009, 0.0009)))
AIR = []
for i in range(40):
    d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-0.3, 1))).normalized() * rng.uniform(0.002, 0.012)
    AIR.append((sphere(f"air{i}", 0.00035, dot_m, 2), d, rng.uniform(0, 6.28)))

IN_SET = [ovl, key2, top2, rim2]

# ------------------------------------------------------------------ shots

cam = B.camera(lens=50, fstop=2.0)
cam.data.clip_start = 0.002

def lerp_cam(a, b, target, lens, fstop, u):
    return a.lerp(b, smooth01(u)), target, lens, fstop

def front(u):
    return lerp_cam(Vector((0.12, -1.55, 0.42)), Vector((0.07, -1.20, 0.34)), Vector((0.02, 0.0, 0.13)), 45, 2.8, u)

FORK_HEAD = lambda: FORK_MAT @ Vector((0.045, 0, 0.002))
CAMS = {
    "front": front,
    "front_out": lambda u: front(1.0 - u),
    "spark_tip": lambda u: lerp_cam(C + Vector((0.14, -0.14, 0.16)), C + Vector((0.12, -0.12, 0.14)), tip_world(1), 60, 45.0, u),
    "waves": lambda u: lerp_cam(C + Vector((0.0, -0.62, 0.17)), C + Vector((0.0, -0.52, 0.15)), C + Vector((0, 0.02, 0.07)), 35, 4.0, u),
    "food": lambda u: lerp_cam(C + Vector((0.04, -0.22, 0.24)), C + Vector((0.03, -0.19, 0.21)), MUG_HOME + Vector((0, 0, 0.06)), 50, 3.5, u),
    "reflect": lambda u: lerp_cam(C + Vector((-0.12, -0.21, 0.15)), C + Vector((-0.10, -0.18, 0.13)), C + Vector((0.01, -0.01, 0.02)), 50, 4.0, u),
    "electrons": lambda u: lerp_cam(C + Vector((0.06, -0.12, 0.09)), C + Vector((0.055, -0.10, 0.08)), TINE_MAT @ Vector((0.022, 0, 0.002)), 70, 60.0, u),
    "tips": lambda u: lerp_cam(C + Vector((0.14, -0.07, 0.06)), C + Vector((0.12, -0.06, 0.055)), tip_world(1), 80, 60.0, u),
    "breakdown": lambda u: lerp_cam(tip_world(1) + Vector((0.035, -0.06, 0.03)), tip_world(1) + Vector((0.03, -0.05, 0.025)), tip_world(1), 85, 70.0, u),
    "spark": lambda u: lerp_cam(C + Vector((0.16, -0.17, 0.17)), C + Vector((0.14, -0.15, 0.15)), tip_world(1), 55, 40.0, u),
    "spoon": lambda u: lerp_cam(C + Vector((0.08, -0.22, 0.20)), C + Vector((0.07, -0.19, 0.18)), SPOON_HOME + Vector((0.0, 0, 0.005)), 55, 14.0, u),
    "foil": lambda u: lerp_cam(C + Vector((0.06, -0.20, 0.09)), C + Vector((0.05, -0.17, 0.08)), FOIL_HOME, 55, 16.0, u),
    "scorch": lambda u: lerp_cam(C + Vector((0.02, -0.10, 0.08)), C + Vector((0.03, -0.02, 0.075)), C + Vector((0.05, CY / 2, 0.065)), 40, 13.0, u),
}
OUTSIDE = {"front", "front_out"}
FORK_SHOTS = {"spark_tip", "waves", "reflect", "electrons", "tips", "breakdown", "spark", "scorch"}

def alt_cam(base, u):
    """The same action from a second angle: swung around the subject and closer."""
    loc, tg, lens, fstop = base(u)
    return tg + (Matrix.Rotation(-0.55, 3, "Z") @ (loc - tg)) * 0.72, tg, lens, fstop

def base_of(i):
    return SHOTS[i][1].split("~")[0]

def shot_at(t):
    """(base name, 0..1 across all angles of the action, age in the action, 0..1 in this cut, second angle?)"""
    k = max([0] + [i for i, (s, _) in enumerate(SHOTS) if t >= s - 1e-6])
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    cut = max(0.0, min(1.0, (t - SHOTS[k][0]) / max(1e-6, t1 - SHOTS[k][0])))
    a = k
    while a > 0 and base_of(a - 1) == base_of(k):
        a -= 1
    b = k
    while b + 1 < len(SHOTS) and base_of(b + 1) == base_of(k):
        b += 1
    t0 = SHOTS[a][0]
    t2 = SHOTS[b + 1][0] if b + 1 < len(SHOTS) else DUR
    return base_of(k), max(0.0, min(1.0, (t - t0) / max(1e-6, t2 - t0))), t - t0, cut, "~" in SHOTS[k][1]

def flicker(t, seed):
    """1 or 0 in a ragged on/off pattern, new every frame."""
    return 1.0 if random.Random(int(t * FPS) * 7 + seed).random() < 0.6 else 0.0

def apply_state(t):
    name, u, age, cut, second = shot_at(t)
    loc, tg, lens, fstop = alt_cam(CAMS[name], cut) if second else CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    cam.data.dof.aperture_fstop = fstop
    cam.data.dof.use_dof = name not in ("spark_tip", "electrons", "tips", "breakdown", "spark")
    cam.data.dof.focus_distance = (tg - loc).length
    outside = name in OUTSIDE
    for ob in OUT_SET:
        ob.location = OUT_HOME[ob] if outside else AWAY
    for ob in (key1, rim1):
        ob.hide_render = not outside
    for ob in IN_SET:
        ob.hide_render = outside
    fr = int(t * FPS)
    # outside: a spark flashes behind the window now and then
    on = outside and flicker(t, 1) and (fr % 9 < 5)
    if on:
        set_arc(front_arc, Vector((0.03, WIN_Y - 0.0012, 0.084)), Vector((0.085, WIN_Y - 0.0012, 0.115 + 0.02 * math.sin(fr))), fr, 0.3)
        front_arc.location = (0, 0, 0)
    else:
        front_arc.location = AWAY
    front_spark.energy = 0.8 if on else 0.0
    # the props on the plate
    fork.location = FORK_HOME if name in FORK_SHOTS else AWAY
    spoon.location = SPOON_HOME if name == "spoon" else AWAY
    spoon.rotation_euler = (0, -0.05, -0.3)
    mug.location = MUG_HOME if name == "food" else AWAY
    emit(water_m, HOT, 2.0 * smooth01(u / 0.8) if name == "food" else 0.0)
    hop = 0.0
    if name == "foil":
        hop = 0.004 * abs(math.sin(age * 9.0)) * flicker(t, 5)          # it hops a little with the crackle
    foil.location = FOIL_HOME + Vector((0, 0, hop)) if name == "foil" else AWAY
    foil.rotation_euler = (0.3 * math.sin(age * 4), 0.2, age * 0.3)
    tt.rotation_euler = (0, 0, t * 0.6)
    # electrons: slosh back and forth (electrons), then crowd at the tips (tips, breakdown, spark_tip)
    crowd = smooth01(u / 0.6) if name == "tips" else (1.0 if name in ("breakdown", "spark", "spark_tip") else 0.0)
    show_e = name in ("electrons", "tips", "breakdown")
    for ob, k, p0, side in ELECTRONS:
        if not show_e:
            ob.location = AWAY
            continue
        p = p0 + 0.35 * math.sin(t * 2 * math.pi * 1.6) * (1 - crowd)
        p = max(0.0, min(1.0, p)) * (1 - crowd) + (0.88 + 0.1 * p0) * crowd
        local = Vector((0.045 * p, -0.0090 + k * 0.0060 + side * (1 - p), 0.0029))
        ob.location = TINE_MAT @ local
        ob.color = (*EBLUE, 1)
    emit(tipglow_m, (0.65, 0.72, 0.9), max(0.14, 0.8 * crowd) if name in ("tips", "breakdown") else 0.14)
    # air beside one tip turns violet as it breaks down
    for ob, d, ph in AIR:
        if name != "breakdown":
            ob.location = AWAY
            continue
        ob.location = tip_world(1) + d + Vector((0.0005 * math.sin(t * 5 + ph), 0, 0.0005 * math.cos(t * 4 + ph)))
        lit = d.length < 0.012 * smooth01((u - 0.2) / 0.6)
        ob.color = (*ARC, 1) if lit else (0.25, 0.25, 0.28, 1)
        s = 1.6 if lit else 1.0
        ob.scale = (s, s, s)
    # arcs
    arcs_on = []
    if name in ("spark", "spark_tip"):
        if flicker(t, 2):
            k = (fr // 3) % 4
            a = tip_world(k)
            b = a + Vector((0.012 + 0.006 * math.sin(fr), -0.004, -0.004))
            arcs_on.append((a, b, 0.4))
    if name == "foil":
        for i in range(3):
            if flicker(t, 10 + i):
                r = random.Random(fr * 3 + i)
                d = Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(0, 1))).normalized()
                a = FOIL_HOME + Vector((0, 0, hop)) + d * 0.031
                arcs_on.append((a, a + d * 0.008, 0.5))
    if name == "scorch" and u <= 0.45 and flicker(t, 3):
        a = C + Vector((0.05, CY / 2 - 0.01, 0.065))
        arcs_on.append((a, a + Vector((0.01, -0.02, -0.01)), 0.4))
    for i, ob in enumerate(ARCS):
        if i < len(arcs_on):
            a, b, jag = arcs_on[i]
            set_arc(ob, a, b, fr * 13 + i, jag)
            ob.location = (0, 0, 0)
        else:
            ob.location = AWAY
    if arcs_on:
        spl.location = arcs_on[0][0]
        spark_l.energy = 0.05 if name == "scorch" else 0.35
    else:
        spl.location = AWAY
        spark_l.energy = 0.0
    setv(scorch_m, "burn", 0.015 + 0.05 * smooth01(u / 0.8) if name == "scorch" else 0.0)
    for ob, off, ph in FLAMES:
        if name == "scorch" and u > 0.45:
            ob.location = C + Vector((0.05, CY / 2 - 0.012, 0.03)) + off
            s = 0.6 + 0.4 * abs(math.sin(t * 11 + ph))
            ob.scale = (s, s, s * 1.4 * smooth01((u - 0.45) / 0.2))
            ob.rotation_euler = (0, 0.25 * math.sin(t * 7 + ph), t * 5 + ph)
        else:
            ob.location = AWAY
    oven_light.energy = 1.5 + (0.8 if name == "scorch" and u > 0.45 else 0.0)

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    pts = {
        "fork": lambda: FORK_MAT @ Vector((-0.06, 0, 0.003)),
        "tips": lambda: tip_world(2),
        "electron": lambda: next((o.location.copy() for o, k, p, s in ELECTRONS if k == 0 and o.location.z > -1), C),
        "air": lambda: tip_world(1) + Vector((0.006, -0.002, 0.004)),
        "spoon": lambda: SPOON_HOME + Vector((0.02, 0, 0.006)),
        "foil": lambda: FOIL_HOME + Vector((0.02, -0.02, 0.02)),
        "mug": lambda: MUG_HOME + Vector((0.02, -0.03, 0.07)),
        "scorch": lambda: C + Vector((0.05, CY / 2, 0.07)),
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

B.render_settings(FPS, samples=int(os.environ.get("FORK_SAMPLES", "48")), motion_blur=0.25, look="AgX - Medium High Contrast")

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1 + scn.frame_subframe) / FPS)

anchors()
apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
