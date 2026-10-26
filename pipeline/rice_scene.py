"""Blender scene for the rice-on-a-chessboard what-if, built in code and animated from rice_anim.

blender -b --factory-startup -P rice_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
A garden table with a chessboard; single grains land on the first nine squares; then one rice pile whose
volume always matches the grains so far grows over the board, the table, a low-poly town and the hills.
"""
import json, math, os, random, sys
import bpy, bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import bkit as B
import rice_anim as RA

argv = sys.argv[sys.argv.index("--") + 1:]
TIMING, OUT, MODE = argv[0], argv[1], argv[2]
T = json.load(open(TIMING))
FPS, DUR, E = T["fps"], T["duration"], T["events"]
NF = int(round(DUR * FPS))
os.makedirs(OUT, exist_ok=True)
B.clear_scene()
scene = B.scene
rng = random.Random(7)
AWAY = Vector((0, 0, -1.0e6))     # far below the ground: a hidden 6 km pile must not shade anything
HORIZON = (0.9, 0.84, 0.76)
HAZE = (0.68, 0.76, 0.88)          # distant land fades toward a clear-day blue, not gray

# ------------------------------------------------------------------ materials

M_GRASS = B.material("grass", (0.1, 0.2, 0.05), 0.0, 0.9)

def land(m):
    """Grass up close, and from the air a patchwork of fields and forest at kilometer scale."""
    nt = m.node_tree
    near = B.color_noise(m, (0.055, 0.12, 0.03), (0.16, 0.24, 0.07), scale=0.004, detail=10)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 0.0013
    vor.inputs["Randomness"].default_value = 0.85
    patch = nt.nodes.new("ShaderNodeValToRGB")
    cr = patch.color_ramp
    cr.interpolation = "CONSTANT"
    cr.elements[0].position, cr.elements[0].color = 0.0, (0.05, 0.1, 0.03, 1)        # forest
    cr.elements[1].position, cr.elements[1].color = 0.35, (0.15, 0.19, 0.07, 1)      # dry field
    cr.elements.new(0.6).color = (0.1, 0.17, 0.05, 1)                                # pasture
    cr.elements.new(0.85).color = (0.18, 0.17, 0.09, 1)                              # plowed
    cam = nt.nodes.new("ShaderNodeCameraData")
    far = nt.nodes.new("ShaderNodeMapRange")
    far.inputs["From Min"].default_value = 300.0
    far.inputs["From Max"].default_value = 3000.0
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    nt.links.new(vor.outputs["Color"], patch.inputs["Fac"])
    nt.links.new(cam.outputs["View Distance"], far.inputs["Value"])
    nt.links.new(far.outputs["Result"], mix.inputs[0])
    nt.links.new(near.outputs["Color"], mix.inputs[6])
    nt.links.new(patch.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], B.bsdf(m).inputs["Base Color"])

land(M_GRASS)
M_WOOD = B.material("table", (0.3, 0.15, 0.07), 0.0, 0.5, 0.1, coat=0.15)
B.color_noise(M_WOOD, (0.17, 0.08, 0.035), (0.36, 0.19, 0.09), scale=3.0, mapping_scale=(0.05, 2.5, 2.5), distortion=3.0)
M_MAPLE = B.material("maple", (0.72, 0.5, 0.27), 0.0, 0.3, coat=0.5)
B.color_noise(M_MAPLE, (0.62, 0.42, 0.22), (0.8, 0.58, 0.33), scale=40.0, mapping_scale=(0.1, 3, 3), distortion=2.0)
M_WALNUT = B.material("walnut", (0.2, 0.1, 0.05), 0.0, 0.3, coat=0.5)
B.color_noise(M_WALNUT, (0.11, 0.05, 0.025), (0.24, 0.12, 0.06), scale=40.0, mapping_scale=(0.1, 3, 3), distortion=2.0)
M_RICE = B.material("rice", (0.93, 0.9, 0.82), 0.0, 0.5, 0.08, noise_scale=0.6)
B.bsdf(M_RICE).inputs["Subsurface Weight"].default_value = 0.15

def rice_bump(m):
    """Grain-sized cells in world space, fading out with camera distance so far shots don't shimmer."""
    nt = m.node_tree
    p = B.bsdf(m)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 160.0
    cam = nt.nodes.new("ShaderNodeCameraData")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.5
    mr.inputs["From Max"].default_value = 25.0
    mr.inputs["To Min"].default_value = 0.6
    mr.inputs["To Max"].default_value = 0.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.0007
    nt.links.new(geo.outputs["Position"], vor.inputs["Vector"])
    nt.links.new(cam.outputs["View Distance"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], bump.inputs["Strength"])
    nt.links.new(vor.outputs["Distance"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], p.inputs["Normal"])

rice_bump(M_RICE)
M_PILE = M_RICE.copy()
M_PILE.name = "pile"
M_PILE.use_transparent_shadow = True

def pile_relief(m):
    """Ripples and slumps sized relative to the pile (scale set per frame), so it reads as rice at every size."""
    nt = m.node_tree
    p = B.bsdf(m)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    scale = nt.nodes.new("ShaderNodeValue"); scale.name = "pscale"; scale.outputs[0].default_value = 1.0
    mul = nt.nodes.new("ShaderNodeVectorMath"); mul.operation = "SCALE"
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 7.0
    noise.inputs["Detail"].default_value = 10.0
    noise.inputs["Roughness"].default_value = 0.6
    bump = nt.nodes.new("ShaderNodeBump"); bump.name = "pbump"
    bump.inputs["Strength"].default_value = 0.35
    tint = nt.nodes.new("ShaderNodeMix"); tint.data_type = "RGBA"
    tint.inputs[6].default_value = (0.95, 0.92, 0.85, 1)
    tint.inputs[7].default_value = (0.8, 0.76, 0.66, 1)
    nt.links.new(geo.outputs["Position"], mul.inputs[0])
    nt.links.new(scale.outputs[0], mul.inputs["Scale"])
    nt.links.new(mul.outputs[0], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(noise.outputs["Fac"], tint.inputs[0])
    nt.links.new(tint.outputs[2], p.inputs["Base Color"])
    grain_bump = p.inputs["Normal"].links[0].from_socket
    nt.links.new(grain_bump, bump.inputs["Normal"])
    nt.links.new(bump.outputs["Normal"], p.inputs["Normal"])

pile_relief(M_PILE)
M_WINDOW = B.material("window", (0.03, 0.04, 0.05), 0.0, 0.15)
M_WALLS = [B.material(f"wall{i}", c, 0.0, 0.8) for i, c in enumerate([(0.8, 0.78, 0.72), (0.62, 0.66, 0.7), (0.75, 0.66, 0.52), (0.55, 0.42, 0.33)])]
M_ROOFS = [B.material(f"roof{i}", c, 0.0, 0.7) for i, c in enumerate([(0.12, 0.12, 0.13), (0.32, 0.12, 0.08), (0.22, 0.2, 0.18)])]
M_TRUNK = B.material("trunk", (0.16, 0.1, 0.06), 0.0, 0.9)
M_LEAVES = [B.material(f"leaves{i}", c, 0.0, 0.8) for i, c in enumerate([(0.07, 0.17, 0.04), (0.1, 0.22, 0.05), (0.13, 0.19, 0.06)])]
M_BLOCK = [B.material(f"block{i}", c, 0.0, 0.7) for i, c in enumerate([(0.7, 0.68, 0.64), (0.5, 0.5, 0.52), (0.62, 0.55, 0.48)])]
M_GLASS = B.material("glass", (0.08, 0.12, 0.18), 0.7, 0.12)
M_ROAD = B.material("road", (0.05, 0.05, 0.055), 0.0, 0.85)
M_ROCK = B.material("rock", (0.3, 0.28, 0.26), 0.0, 0.9)

def snow_line(m, height):
    nt = m.node_tree
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.22, 0.21, 0.2, 1)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0.9, 0.92, 0.95, 1)
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = height * 0.85
    mr.inputs["From Max"].default_value = height
    nt.links.new(geo.outputs["Position"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], B.bsdf(m).inputs["Base Color"])

snow_line(M_ROCK, 2400.0)

# ------------------------------------------------------------------ ground, table, board

ground = B.mesh_from("ground", B.box(-150000, 150000, -150000, 150000, -1.0, 0.0), [M_GRASS])

table = B.mesh_from("table", B.many(
    B.box(-0.8, 0.8, -0.45, 0.45, 0.71, 0.75),
    *[B.box(sx * 0.74 - 0.025, sx * 0.74 + 0.025, sy * 0.39 - 0.025, sy * 0.39 + 0.025, 0.0, 0.71)
      for sx in (-1, 1) for sy in (-1, 1)]), [M_WOOD])
B.bevel(table, 0.006, 2)
B.smooth(table)

half = RA.BOARD / 2
board_build = [B.with_material(B.box(-half, half, -half, half, 0.75, RA.BOARD_TOP), 1)]
for k in range(1, 65):
    x, y = RA.square_xy(k)
    r, c = divmod(k - 1, 8)
    board_build.append(B.with_material(B.box(x - RA.SQ / 2, x + RA.SQ / 2, y - RA.SQ / 2, y + RA.SQ / 2,
                                             RA.BOARD_TOP - 0.0005, RA.BOARD_TOP + 0.0005), 0 if (r + c) % 2 else 1))
board = B.mesh_from("board", B.many(*board_build), [M_MAPLE, M_WALNUT])

GRAIN_Z = RA.BOARD_TOP + 0.0005
grain_objs = []
for k in range(1, RA.DISCRETE + 1):
    cx, cy = RA.square_xy(k)
    def build(bm, k=k, cx=cx, cy=cy):
        for j in range(RA.grains_on(k)):
            layer = 0 if RA.grains_on(k) < 64 else rng.random() * (k - 6) * 0.0022
            M = (Matrix.Translation((cx + rng.uniform(-0.019, 0.019), cy + rng.uniform(-0.019, 0.019), GRAIN_Z + 0.0011 + layer))
                 @ Matrix.Rotation(rng.uniform(0, math.pi), 4, "Z") @ Matrix.Rotation(rng.uniform(-0.25, 0.25), 4, "X")
                 @ Matrix.Diagonal((0.0035, 0.0011, 0.0011, 1)))
            bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1.0, matrix=M)
    ob = B.mesh_from(f"grains{k}", build, [M_RICE])
    ob.data.shade_smooth()
    grain_objs.append(ob)

# ------------------------------------------------------------------ the pile (heightfield, updated every frame)

K_R, M_S = RA.K_RINGS, RA.M_SEG
def pile_build(bm):
    verts = [bm.verts.new((0, 0, 0))] + [bm.verts.new((0, 0, 0)) for _ in range(K_R * M_S)]
    idx = lambda ring, seg: 1 + ring * M_S + (seg % M_S)
    for s in range(M_S):
        bm.faces.new((verts[0], verts[idx(0, s)], verts[idx(0, s + 1)]))
    for ring in range(K_R - 1):
        for s in range(M_S):
            bm.faces.new((verts[idx(ring, s)], verts[idx(ring + 1, s)], verts[idx(ring + 1, s + 1)], verts[idx(ring, s + 1)]))
def make_pile(name):
    ob = B.mesh_from(name, pile_build, [M_PILE])
    ob.data.shade_smooth()
    ob.data.attributes.new("rice", "FLOAT", "POINT")
    return ob

piles = {"table": make_pile("pile_table"), "ground": make_pile("pile_ground")}
pile_co = np.zeros((1 + K_R * M_S) * 3, dtype=np.float32)
pile_mask = np.zeros(1 + K_R * M_S, dtype=np.float32)

def set_field(ob, field, apex):
    if field is None:
        ob.location = AWAY
        return
    x, y, z, has = field
    co = pile_co.reshape(-1, 3)
    co[0] = (0.0, 0.0, max(float(z.max()), 0.0) if ob is piles["ground"] else apex)
    co[1:, 0], co[1:, 1], co[1:, 2] = x.ravel(), y.ravel(), z.ravel()
    pile_mask[0] = 1.0
    pile_mask[1:] = has.ravel()
    ob.data.vertices.foreach_set("co", pile_co)
    ob.data.attributes["rice"].data.foreach_set("value", pile_mask)
    ob.data.update()
    ob.location = (0, 0, 0)

def set_pile(volume):
    fields = RA.heap_fields(volume)
    if fields is None:
        for ob in piles.values():
            ob.location = AWAY
        return None
    apex = fields["apex"]
    set_field(piles["table"], fields["table"], apex)
    set_field(piles["ground"], fields["ground"], apex)
    size = max(apex - RA.BOARD_TOP * math.exp(-apex), 0.02)
    M_PILE.node_tree.nodes["pscale"].outputs[0].default_value = 6.0 / size
    M_PILE.node_tree.nodes["pbump"].inputs["Distance"].default_value = 0.01 * size
    return apex

# ------------------------------------------------------------------ the town, hills and mountains

def gable_house(cx, cy, w, d, h, yaw, wall_i, roof_i):
    """Box walls plus a gable roof, as bmesh builders tagged with material slots."""
    R = Matrix.Translation((cx, cy, 0)) @ Matrix.Rotation(yaw, 4, "Z")
    def walls(bm):
        bmesh.ops.create_cube(bm, size=1.0, matrix=R @ Matrix.Translation((0, 0, h / 2)) @ Matrix.Diagonal((w, d, h, 1)))
    def roof(bm):
        rh = 0.45 * min(w, d)
        o = 0.4
        pts = [(-w / 2 - o, -d / 2 - o, h), (w / 2 + o, -d / 2 - o, h), (w / 2 + o, d / 2 + o, h), (-w / 2 - o, d / 2 + o, h),
               (-w / 2 - o, 0, h + rh), (w / 2 + o, 0, h + rh)]
        v = [bm.verts.new(R @ Vector(p)) for p in pts]
        for f in ((v[0], v[1], v[5], v[4]), (v[2], v[3], v[4], v[5]), (v[0], v[4], v[3]), (v[1], v[2], v[5]), (v[0], v[3], v[2], v[1])):
            bm.faces.new(f)
    def windows(bm):
        for side in (-1, 1):
            for fx in (-0.28, 0.28):
                M = R @ Matrix.Translation((fx * w, side * (d / 2 + 0.03), h * 0.55)) @ Matrix.Diagonal((1.3, 0.08, 1.2, 1))
                bmesh.ops.create_cube(bm, size=1.0, matrix=M)
        M = R @ Matrix.Translation((0, -(d / 2 + 0.03), 1.05)) @ Matrix.Diagonal((1.0, 0.08, 2.1, 1))
        bmesh.ops.create_cube(bm, size=1.0, matrix=M)
    return [B.with_material(walls, wall_i), B.with_material(roof, len(M_WALLS) + roof_i),
            B.with_material(windows, len(M_WALLS) + len(M_ROOFS))]

def ring_points(n, r0, r1, center=(0.0, 0.0), clear=None):
    pts = []
    while len(pts) < n:
        a = rng.uniform(0, 2 * math.pi)
        r = math.sqrt(rng.uniform(r0 ** 2, r1 ** 2))
        p = (center[0] + r * math.cos(a), center[1] + r * math.sin(a))
        if clear and any(math.hypot(p[0] - q[0], p[1] - q[1]) < clear for q in pts):
            continue
        pts.append(p)
    return pts

AZ0 = math.radians(225)                     # camera starts southwest of the board, looking northeast
look = Vector((-math.cos(AZ0), -math.sin(AZ0), 0))
home = look * 13.0
houses = gable_house(home.x, home.y, 11, 9, 6.0, AZ0 + math.pi / 2, 0, 1)
for p in ring_points(170, 22, 420, clear=17):
    houses += gable_house(p[0], p[1], rng.uniform(8, 13), rng.uniform(8, 11), rng.uniform(3.2, 6.5), rng.uniform(0, math.pi),
                          rng.randrange(len(M_WALLS)), rng.randrange(len(M_ROOFS)))
B.mesh_from("houses", B.many(*houses), M_WALLS + M_ROOFS + [M_WINDOW])

trees = []
for p in ring_points(420, 5.0, 520):
    h = rng.uniform(4, 11)
    trees.append(B.with_material(B.cyl_z(0.18, 0, h * 0.4, p[0], p[1], seg=6), 0))
    trees.append(B.with_material(B.cyl_z(h * 0.28, h * 0.3, h, p[0], p[1], seg=7, r2=0.0), 1 + rng.randrange(3)))
B.mesh_from("trees", B.many(*trees), [M_TRUNK] + M_LEAVES)

blocks = []
for p in ring_points(70, 480, 1500, clear=60):
    w, d, h = rng.uniform(18, 40), rng.uniform(15, 30), rng.uniform(12, 45)
    blocks.append(B.with_material(B.box(p[0] - w / 2, p[0] + w / 2, p[1] - d / 2, p[1] + d / 2, 0, h), rng.randrange(3)))
B.mesh_from("blocks", B.many(*blocks), M_BLOCK)

downtown = look * 2600.0
towers = []
for p in ring_points(34, 0, 520, center=(downtown.x, downtown.y), clear=70):
    s, h = rng.uniform(25, 45), rng.uniform(70, 330)
    towers.append(B.box(p[0] - s / 2, p[0] + s / 2, p[1] - s / 2, p[1] + s / 2, 0, h))
B.mesh_from("towers", B.many(*towers), [M_GLASS])

roads = []
for i in range(-6, 6):
    c = i * 160 + 80                     # the table sits mid-block, not on a crossing
    roads.append(B.box(c - 4, c + 4, -1600, 1600, 0.0, 0.03))
    roads.append(B.box(-1600, 1600, c - 4, c + 4, 0.0, 0.03))
roads_ob = B.mesh_from("roads", B.many(*roads), [M_ROAD])
roads_ob.location.z = 0.01

def mountain(bm, cx, cy, radius, height, seed):
    """Polar heightfield cone with ridged noise."""
    r2 = random.Random(seed)
    rings, segs = 14, 40
    ph = [r2.uniform(0, 6.28) for _ in range(4)]
    rows = []
    for i in range(rings + 1):
        u = i / rings
        row = []
        for s in range(segs):
            a = 2 * math.pi * s / segs
            wob = 1 + 0.18 * math.sin(3 * a + ph[0]) + 0.1 * math.sin(7 * a + ph[1])
            z = height * (1 - u) ** 1.4 * (1 + 0.12 * math.sin(5 * a + ph[2]) * u)
            rr = radius * u * wob
            row.append(bm.verts.new((cx + rr * math.cos(a), cy + rr * math.sin(a), z)))
        rows.append(row)
    for i in range(rings):
        for s in range(segs):
            bm.faces.new((rows[i][s], rows[i + 1][s], rows[i + 1][(s + 1) % segs], rows[i][(s + 1) % segs]))

mts = []
for j in range(18):
    a = 2 * math.pi * j / 18 + rng.uniform(-0.12, 0.12)
    r = rng.uniform(26000, 52000)
    mts.append(lambda bm, a=a, r=r, j=j: mountain(bm, r * math.cos(a), r * math.sin(a), rng.uniform(5000, 9000), rng.uniform(1600, 3400), j))
mt_ob = B.mesh_from("mountains", B.many(*mts), [M_ROCK])
mt_ob.data.shade_smooth()

# ------------------------------------------------------------------ sky, sun, haze, camera, render settings

world = bpy.data.worlds.new("sky")
scene.world = world
world.use_nodes = True
wt = world.node_tree
bg = wt.nodes["Background"]
tc = wt.nodes.new("ShaderNodeTexCoord")
sep = wt.nodes.new("ShaderNodeSeparateXYZ")
mr = wt.nodes.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = -0.02
mr.inputs["From Max"].default_value = 0.55
ramp = wt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (*HORIZON, 1)
ramp.color_ramp.elements[1].color = (0.17, 0.33, 0.68, 1)
mid = ramp.color_ramp.elements.new(0.25)
mid.color = (0.55, 0.65, 0.82, 1)
wt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
wt.links.new(sep.outputs["Z"], mr.inputs["Value"])
wt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
wt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0

B.sun("sun", math.degrees(AZ0) - 95, 16, 4.2, (1.0, 0.86, 0.7), 1.2)     # from the camera's right, low: long shadows
for m in bpy.data.materials:
    if m.use_nodes and m.node_tree.nodes.get("Principled BSDF"):
        B.add_haze(m, HAZE, 140000.0)

def pile_mask_mix(m):
    """Hide the parts of the pile mesh that hold no rice (the 'rice' point attribute is 0 there)."""
    nt = m.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    src = out.inputs["Surface"].links[0].from_socket
    attr = nt.nodes.new("ShaderNodeAttribute"); attr.attribute_name = "rice"
    hard = nt.nodes.new("ShaderNodeMath"); hard.operation = "GREATER_THAN"; hard.inputs[1].default_value = 0.995
    clear = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(attr.outputs["Fac"], hard.inputs[0])       # faces that touch an empty vertex vanish, no half-clear walls
    nt.links.new(hard.outputs[0], mix.inputs["Fac"])
    nt.links.new(clear.outputs[0], mix.inputs[1])
    nt.links.new(src, mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])

pile_mask_mix(M_PILE)

cam = B.camera(lens=40, fstop=2.8)
B.render_settings(FPS, samples=32, motion_blur=0.35)

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

def camera_at(t, n, volume, apex):
    # board phase: hover over the squares being filled
    k = max(1, min(RA.DISCRETE, math.ceil(n)))
    pts = [RA.square_xy(i) for i in range(1, k + 1)]
    bx = sum(p[0] for p in pts) / k
    by = sum(p[1] for p in pts) / k
    board_target = Vector((bx, by, RA.BOARD_TOP))
    board_dist = 0.17 + 0.022 * n
    # pile phase: frame the whole pile, pulling back as it grows
    heap_dist = max(0.45, 4.2 * volume ** (1 / 3)) if volume > 0 else 0.45
    if t >= E["s64"] and t < E["loop"]:
        heap_dist *= 1 + 0.25 * smooth01((t - E["s64"]) / (E["loop"] - E["s64"]))
    heap_target = Vector((0, 0, max(RA.BOARD_TOP, 0.36 * (apex or 0))))
    w = smooth01((n - 9.0) / 3.0)
    target = board_target.lerp(heap_target, w)
    dist = math.exp(math.log(board_dist) * (1 - w) + math.log(heap_dist) * w)
    elev = math.radians(max(13.0, min(40.0, 40 - 6.5 * math.log10(max(dist, 0.3) / 0.3))))
    orbit = 0.0 if t >= E["loop"] else math.radians(0.6) * t
    az = AZ0 + orbit
    loc = target + dist * Vector((math.cos(elev) * math.cos(az), math.cos(elev) * math.sin(az), math.sin(elev)))
    return loc, target

def apply_state(t):
    n = RA.square_at(t, E)
    for k, ob in enumerate(grain_objs, start=1):
        p = (n - (k - 1)) / 0.5
        if p <= 0:
            ob.location = AWAY
        else:
            u = 1 - (1 - min(1.0, p)) ** 3
            ob.location = (0, 0, 0.03 * (1 - u))
    volume = RA.heap_volume(n) if n > RA.DISCRETE else 0.0
    apex = set_pile(volume)
    loc, target = camera_at(t, n, volume, apex)
    B.aim(cam, loc, target)
    dist = (target - loc).length
    cam.data.dof.focus_distance = dist
    cam.data.clip_start = max(0.005, dist * 0.002)
    cam.data.clip_end = max(500.0, dist * 30 + 120000)

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1 + scn.frame_subframe) / FPS)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
