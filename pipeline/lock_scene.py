"""Blender scene for the lock cutaway, built entirely in code and animated from lock_anim.

blender -b --factory-startup -P lock_scene.py -- timing.json out_dir MODE
MODE: 'all' renders every frame (skipping ones already on disk), or comma-separated 1-based frame numbers.
Always writes out_dir/anchors.json: screen positions of label points for every frame.
"""
import bpy, bmesh, json, math, os, sys
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lock_anim as LA

argv = sys.argv[sys.argv.index("--") + 1:]
TIMING, OUT, MODE = argv[0], argv[1], argv[2]
T = json.load(open(TIMING))
FPS, DUR, E = T["fps"], T["duration"], T["events"]
NF = int(round(DUR * FPS))
os.makedirs(OUT, exist_ok=True)

scene = bpy.context.scene
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob)

ORANGE = (1.0, 0.144, 0.024)       # brand orange (255,106,43) in linear
GLOW = (1.0, 0.16, 0.0)            # emission reads pink under AgX unless it is pushed past the brand hue
RED = (1.0, 0.02, 0.01)

# ------------------------------------------------------------------ materials

def material(name, color, metallic=0.0, rough=0.4, rough_var=0.0, brushed=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = rough
    p.inputs["Coat Weight"].default_value = coat
    p.inputs["Emission Color"].default_value = (*ORANGE, 1)
    p.inputs["Emission Strength"].default_value = 0.0
    if rough_var:
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = 3.0
        n.inputs["Detail"].default_value = 6.0
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value = rough - rough_var
        mr.inputs["To Max"].default_value = rough + rough_var
        nt.links.new(n.outputs["Fac"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], p.inputs["Roughness"])
    if brushed:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (0.4, 40.0, 40.0)    # streaks run along x (the saw direction)
        n2 = nt.nodes.new("ShaderNodeTexNoise")
        n2.inputs["Scale"].default_value = 6.0
        n2.inputs["Detail"].default_value = 3.0
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = brushed
        bump.inputs["Distance"].default_value = 0.004
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], n2.inputs["Vector"])
        nt.links.new(n2.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], p.inputs["Normal"])
    return m

def bsdf(m):
    return m.node_tree.nodes["Principled BSDF"]

BRASS = (0.80, 0.56, 0.26)
M_HOUSING = material("housing", BRASS, 1.0, 0.30, 0.08)
M_PLUG = material("plug", (0.86, 0.64, 0.32), 1.0, 0.24, 0.06)
M_CUT = material("cut", (0.80, 0.58, 0.30), 1.0, 0.2, 0.06, brushed=0.5)
M_KEY = material("key", (0.78, 0.76, 0.70), 1.0, 0.26, 0.06)
M_SPRING = [material(f"spring{i}", (0.62, 0.62, 0.64), 1.0, 0.32) for i in range(5)]
M_KEYPIN = [material(f"keypin{i}", BRASS, 1.0, 0.22) for i in range(5)]
M_DRIVER = [material(f"driver{i}", (0.72, 0.72, 0.74), 1.0, 0.22) for i in range(5)]
M_LINE = material("shearline", (0.0, 0.0, 0.0), 0.0, 0.5)
M_FLOOR = material("floor", (0.006, 0.0065, 0.008), 0.0, 0.8, 0.1)
bsdf(M_FLOOR).inputs["Specular IOR Level"].default_value = 0.25    # keeps the key light's reflection off the floor

def wood():
    m = material("wood", (0.3, 0.15, 0.07), 0.0, 0.45, 0.1, coat=0.25)
    nt = m.node_tree
    p = bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 0.9, 0.02)       # long grain running up the door
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 2.0
    n.inputs["Detail"].default_value = 12.0
    n.inputs["Distortion"].default_value = 3.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.10, 0.045, 0.02, 1)
    ramp.color_ramp.elements[1].color = (0.34, 0.16, 0.07, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
    nt.links.new(n.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    return m

M_WOOD = wood()

# ------------------------------------------------------------------ geometry helpers

def link(ob):
    scene.collection.objects.link(ob)
    return ob

def mesh_from(name, build, mats):
    bm = bmesh.new()
    build(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    return link(bpy.data.objects.new(name, me))

def cyl_x(r, x0, x1, seg=128):
    def b(bm):
        M = Matrix.Translation(((x0 + x1) / 2, 0, 0)) @ Matrix.Rotation(math.pi / 2, 4, "Y")
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=r, depth=x1 - x0, matrix=M)
    return b

def cyl_z(r, z0, z1, x, seg=64, r2=None):
    def b(bm):
        M = Matrix.Translation((x, 0, (z0 + z1) / 2))
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r,
                              radius2=r if r2 is None else r2, depth=z1 - z0, matrix=M)
    return b

def box(x0, x1, y0, y1, z0, z1):
    def b(bm):
        M = Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)) @ Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1))
        bmesh.ops.create_cube(bm, size=1.0, matrix=M)
    return b

def many(*builders):
    def b(bm):
        for f in builders:
            f(bm)
    return b

def apply_modifiers(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    ob.modifiers.clear()
    old = ob.data
    ob.data = me
    bpy.data.meshes.remove(old)

def boolean(ob, ops):
    cutters = []
    for build, op in ops:
        c = mesh_from("cutter", build, [])
        cutters.append(c)
        md = ob.modifiers.new("b", "BOOLEAN")
        md.operation = op
        md.object = c
        md.solver = "EXACT"
    apply_modifiers(ob)
    for c in cutters:
        bpy.data.objects.remove(c)

def bevel(ob, width, segments=3, angle=35):
    md = ob.modifiers.new("bevel", "BEVEL")
    md.width = width
    md.segments = segments
    md.limit_method = "ANGLE"
    md.angle_limit = math.radians(angle)
    apply_modifiers(ob)

def smooth(ob, angle=32):
    ob.data.shade_smooth()
    ob.data.set_sharp_from_angle(angle=math.radians(angle))

def split_half(ob, cut_mat):
    """Saw the object along y = 0: returns (front y<0, back y>0); sawn faces get cut_mat."""
    front = ob.copy()
    front.data = ob.data.copy()
    link(front)
    boolean(ob, [(box(-20, 20, 0, 20, -20, 20), "INTERSECT")])
    boolean(front, [(box(-20, 20, -20, 0, -20, 20), "INTERSECT")])
    for part in (ob, front):
        me = part.data
        if cut_mat.name not in me.materials:
            me.materials.append(cut_mat)
        idx = list(me.materials).index(cut_mat)
        for poly in me.polygons:
            if abs(poly.normal.y) > 0.999 and abs(poly.center.y) < 1e-4:
                poly.material_index = idx
        smooth(part)
    return front, ob

# ------------------------------------------------------------------ the lock

X = LA.PIN_X
housing = mesh_from("housing", cyl_x(1.45, 0.0, 4.6), [M_HOUSING])
boolean(housing, [(box(0.0, 4.6, -0.62, 0.62, 0.0, 3.3), "UNION")])
bevel(housing, 0.05)
boolean(housing, [(cyl_x(1.02, -1.0, 5.6), "DIFFERENCE"),
                  (many(*[cyl_z(0.2, 0.95, LA.SPRING_TOP, x) for x in X]), "DIFFERENCE")])
housing_f, housing_b = split_half(housing, M_CUT)

plug = mesh_from("plug", cyl_x(1.0, 0.0, 4.6), [M_PLUG])
boolean(plug, [(cyl_x(1.22, -0.2, 0.0), "UNION"), (box(4.55, 5.5, -0.12, 0.12, -0.55, 0.55), "UNION")])
bevel(plug, 0.03)
boolean(plug, [(box(-0.5, 4.45, -0.19, 0.19, -0.85, 0.5), "DIFFERENCE"),
               (many(*[cyl_z(0.2, -0.1, 1.15, x) for x in X]), "DIFFERENCE")])
plug_f, plug_b = split_half(plug, M_CUT)

keypins, drivers, springs = [], [], []
for i, x in enumerate(X):
    L = LA.key_pin_len(i)
    kp = mesh_from(f"keypin{i}", many(cyl_z(0.07, 0.0, 0.12, 0.0, r2=0.18), cyl_z(0.18, 0.12, L, 0.0)), [M_KEYPIN[i]])
    smooth(kp)
    keypins.append(kp)
    dp = mesh_from(f"driver{i}", cyl_z(0.18, 0.0, LA.DRIVER_LEN, 0.0), [M_DRIVER[i]])
    bevel(dp, 0.03, 3)
    smooth(dp)
    drivers.append(dp)
    cu = bpy.data.curves.new(f"spring{i}", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.026
    cu.bevel_resolution = 3
    sp = cu.splines.new("POLY")
    sp.points.add(299)
    cu.materials.append(M_SPRING[i])
    so = link(bpy.data.objects.new(f"spring{i}", cu))
    so.location = (x, 0, LA.SPRING_TOP)
    springs.append(so)

def set_spring(so, length, turns=9):
    pts = so.data.splines[0].points
    n = len(pts)
    for k in range(n):
        a = 2 * math.pi * turns * k / (n - 1)
        pts[k].co = (0.155 * math.cos(a), 0.155 * math.sin(a), -length * k / (n - 1), 1)

def build_key(name, cuts):
    """Key along -x from its tip at the origin, blade vertical, cuts on top."""
    def blade(bm):
        top = [(-u, LA.blade_top(u, cuts)) for u in [k * 0.01 for k in range(461)]]
        bottom = [(-u, -0.8 + max(0.0, 0.2 - u)) for u in [k * 0.01 for k in range(460, -1, -1)]]
        outline = top + bottom
        a = [bm.verts.new((x, -0.13, z)) for x, z in outline]
        b = [bm.verts.new((x, 0.13, z)) for x, z in outline]
        bm.faces.new(a)
        bm.faces.new(list(reversed(b)))
        n = len(outline)
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = mesh_from(name, blade, [M_KEY])
    boolean(ob, [(box(-4.85, -4.55, -0.15, 0.15, -0.95, 0.62), "UNION"),
                 (lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=96, radius1=1.32, radius2=1.32,
                                                   depth=0.32, matrix=Matrix.Translation((-6.15, 0, -0.15)) @ Matrix.Rotation(math.pi / 2, 4, "X") @ Matrix.Diagonal((1.05, 1.0, 1.0, 1))), "UNION"),
                 (lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=48, radius1=0.3, radius2=0.3,
                                                   depth=1.0, matrix=Matrix.Translation((-6.9, 0, -0.15)) @ Matrix.Rotation(math.pi / 2, 4, "X")), "DIFFERENCE"),
                 (box(-4.6, 0.3, 0.09, 0.3, -0.5, -0.32), "DIFFERENCE"),
                 (box(-4.6, 0.3, -0.3, -0.09, -0.12, 0.02), "DIFFERENCE")])
    bevel(ob, 0.015, 2, 40)
    smooth(ob, 40)
    return ob

key_good = build_key("key_good", LA.GOOD)
key_bad = build_key("key_bad", LA.BAD)

line = mesh_from("shearline", box(-0.02, 4.62, -0.025, -0.012, 0.985, 1.015), [M_LINE])

# ------------------------------------------------------------------ set: studio sweep and the door

def sweep_floor(bm):
    prof = [(y, -1.46) for y in (-60, -10, 0, 6)]
    for k in range(1, 13):
        a = k / 12 * math.pi / 2
        prof.append((6 + 10 * math.sin(a), -1.46 + 10 * (1 - math.cos(a))))
    prof += [(16, 30), (16, 60)]
    rows = []
    for x in (-60.0, 60.0):
        rows.append([bm.verts.new((x, y, z)) for y, z in prof])
    for k in range(len(prof) - 1):
        bm.faces.new((rows[0][k], rows[1][k], rows[1][k + 1], rows[0][k + 1]))

floor = mesh_from("floor", sweep_floor, [M_FLOOR])
floor.data.shade_smooth()

door = mesh_from("door", box(0.0, 7.0, -60, 60, -90, 60), [M_WOOD])
rose = mesh_from("rose", cyl_x(2.5, -0.18, 0.0), [M_HOUSING])
boolean(rose, [(cyl_x(1.24, -1, 1), "DIFFERENCE")])
bevel(rose, 0.08, 4, 30)
smooth(rose)
plug_face = mesh_from("plug_face", cyl_x(1.22, -0.2, 0.0), [M_PLUG])     # stands in for the lock seen from outside
boolean(plug_face, [(box(-0.5, 0.5, -0.19, 0.19, -0.85, 0.5), "DIFFERENCE")])
bevel(plug_face, 0.03)
smooth(plug_face)
door_set = [door, rose, plug_face]

# ------------------------------------------------------------------ lights, world, camera, render settings

def area(name, loc, target, size, power, color=(1, 1, 1), size_y=None):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = "RECTANGLE"
    ld.size = size
    ld.size_y = size_y or size
    ld.energy = power
    ld.color = color
    ob = link(bpy.data.objects.new(name, ld))
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob

L_KEY = area("key", (-6, -14, 12), (2, 0, 0.5), 12, 9000, (1.0, 0.97, 0.92), 8)
L_RIM = area("rim", (9, 12, 7), (2, 0, 1), 10, 6000, (0.85, 0.92, 1.0))
L_FILL = area("fill", (8, -16, -1), (2, 0, 1), 14, 1800)
L_ACCENT = area("accent", (-9, 8, 3), (1, 0, 1), 6, 2500, ORANGE)
L_WINDOW = area("window", (-30, 25, 25), (0, 0, 0), 30, 0, (1.0, 0.86, 0.68))
STUDIO = [(L_KEY, 9000), (L_RIM, 6000), (L_FILL, 1800), (L_ACCENT, 2500)]

world = bpy.data.worlds.new("world")
scene.world = world
world.use_nodes = True
wt = world.node_tree
bg = wt.nodes["Background"]
tc = wt.nodes.new("ShaderNodeTexCoord")
sep = wt.nodes.new("ShaderNodeSeparateXYZ")
wr = wt.nodes.new("ShaderNodeValToRGB")
wr.color_ramp.elements[0].position = 0.55
wr.color_ramp.elements[0].color = (0.02, 0.02, 0.024, 1)
wr.color_ramp.elements[1].position = 0.95
wr.color_ramp.elements[1].color = (0.4, 0.4, 0.42, 1)
mr = wt.nodes.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = -1
mr.inputs["From Max"].default_value = 1
lp = wt.nodes.new("ShaderNodeLightPath")
mix = wt.nodes.new("ShaderNodeMix")
mix.data_type = "RGBA"
mix.inputs[7].default_value = (0.006, 0.0065, 0.008, 1)     # B: what the camera sees directly
wt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
wt.links.new(sep.outputs["Z"], mr.inputs["Value"])
wt.links.new(mr.outputs["Result"], wr.inputs["Fac"])
wt.links.new(wr.outputs["Color"], mix.inputs[6])            # A: soft studio gradient seen in reflections
wt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
wt.links.new(mix.outputs[2], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0

cam_data = bpy.data.cameras.new("cam")
cam = link(bpy.data.objects.new("cam", cam_data))
scene.camera = cam
cam_data.sensor_width = 36
cam_data.dof.use_dof = True
cam_data.dof.aperture_fstop = 9.0
cam_data.clip_start = 0.1
cam_data.clip_end = 500
scene.unit_settings.scale_length = 0.00635      # one unit = 6.35 mm, so depth of field behaves like a macro lens

r = scene.render
r.engine = "BLENDER_EEVEE"
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps = FPS
r.use_motion_blur = True
r.motion_blur_shutter = 0.4
r.image_settings.file_format = "PNG"
r.image_settings.color_mode = "RGB"
r.image_settings.compression = 15
r.use_overwrite = False
r.use_placeholder = True
ee = scene.eevee
ee.taa_render_samples = 48
for attr, val in (("use_raytracing", True), ("use_shadows", True), ("use_fast_gi", True), ("fast_gi_method", "GLOBAL_ILLUMINATION")):
    try:
        setattr(ee, attr, val)
    except Exception as ex:
        print("eevee setting skipped:", attr, ex)
scene.view_settings.view_transform = "AgX"
for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
    try:
        scene.view_settings.look = look
        break
    except Exception:
        pass

# ------------------------------------------------------------------ camera path

def P(loc, target, lens=50):
    return (Vector(loc), Vector(target), lens)

DOOR0 = P((-10.5, -7.5, 3.6), (-0.4, 0, 0.0), 42)
DOOR1 = P((-8.0, -5.6, 2.6), (-0.6, 0, 0.0), 42)
WIDE0 = P((1.6, -24, 2.6), (1.5, 0, 0.5))
WIDE = P((1.7, -21, 2.4), (1.6, 0, 0.5))
MID = P((2.2, -15, 2.6), (2.2, 0, 0.9))
PINS = P((2.3, -11.5, 3.0), (2.2, 0, 1.25))
PINS2 = P((2.1, -11, 2.8), (2.2, 0, 1.15))
KEYV = P((1.1, -19, 2.3), (1.0, 0, 0.5))
KEYV2 = P((1.4, -17, 2.2), (1.4, 0, 0.6))
SHEAR = P((2.2, -13, 2.3), (2.2, 0, 0.9))
SHEAR2 = P((2.2, -12, 2.1), (2.2, 0, 0.9))
CLOSE0 = P((1.9, -10, 1.4), (2.0, 0, 0.55))
CLOSE = P((2.0, -8.5, 1.2), (2.1, 0, 0.45))
END = P((-10.5, -14, 7.0), (0.6, 0, 1.6))

sw = LA.swap_start(E)
KEYS = [(0.0, DOOR0), (E["cut"] - 1e-3, DOOR1), (E["cut"], WIDE0), (E["plug"], WIDE), (E["five"] - 0.2, MID),
        (E["spring"] - 0.3, PINS), (E["slide"] - 0.3, PINS2), (E["slide"] + 0.7, KEYV), (E["shear"] - 0.4, KEYV2),
        (E["shear"] + 0.3, SHEAR), (sw, SHEAR2), (sw + 0.7, MID), (E["some"] - 0.1, MID), (E["halfmm"] - 0.3, CLOSE0),
        (E["comment"] - 0.2, CLOSE), (E["comment"] + 1.3, END), (DUR + 1, END)]

def camera_at(t):
    for (t0, a), (t1, b) in zip(KEYS, KEYS[1:]):
        if t0 <= t <= t1:
            u = LA.ease((t - t0) / max(1e-6, t1 - t0))
            return a[0].lerp(b[0], u), a[1].lerp(b[1], u), a[2] + (b[2] - a[2]) * u
    return END

# ------------------------------------------------------------------ per-frame state

def rot_x(theta, v):
    return Matrix.Rotation(theta, 4, "X") @ Vector(v)

def set_emit(m, strength, color=GLOW):
    p = bsdf(m)
    p.inputs["Emission Strength"].default_value = 0.6 * strength
    p.inputs["Emission Color"].default_value = (*color, 1)

AWAY = Vector((0, 0, -500))

def apply_state(t):
    which, tip, theta = LA.key_state(t, E)
    door_on = t < E["cut"]
    for ob in door_set:
        ob.location = (0, 0, 0) if door_on else AWAY
    floor.location = AWAY if door_on else (0, 0, 0)
    for lt, power in STUDIO:
        lt.data.energy = power * (0.35 if door_on else 1.0)
    L_WINDOW.data.energy = 90000 if door_on else 0
    # inside parts are hidden behind the door shot anyway; keep them where they belong
    fo = Vector(LA.front_offset(t, E))
    for ob in (housing_f, plug_f):
        ob.location = fo
        ob.rotation_euler = (0, 0, 0)
    plug_f.rotation_euler.x = theta
    plug_b.rotation_euler.x = theta
    for name, ob in (("good", key_good), ("bad", key_bad)):
        if which == name:
            ob.location = (tip, 0, 0)
            ob.rotation_euler.x = theta
        else:
            ob.location = AWAY
    tips = LA.pin_tips(t, E)
    g = LA.glows(t, E)
    for i, x in enumerate(X):
        z = tips[i]
        keypins[i].location = rot_x(theta, (x, 0, z))
        keypins[i].rotation_euler.x = theta
        d0 = z + LA.key_pin_len(i)
        if which == "good" and abs(theta) > 0.1:
            d0 = LA.SHEAR
        drivers[i].location = (x, 0, d0)
        set_spring(springs[i], LA.SPRING_TOP - (d0 + LA.DRIVER_LEN))
        s = g["stack"][i]
        part = g["part"] if i == 2 else {"spring": 0, "top": 0, "bottom": 0}
        set_emit(M_SPRING[i], s + part["spring"])
        if g["driver_red"][i] > 0.05:
            set_emit(M_DRIVER[i], g["driver_red"][i], RED)
        else:
            set_emit(M_DRIVER[i], s + part["top"])
        if g["pin_red"][i] > 0.05:
            set_emit(M_KEYPIN[i], g["pin_red"][i], RED)
        else:
            set_emit(M_KEYPIN[i], s + part["bottom"])
    if g["line_red"] > g["line_orange"]:
        set_emit(M_LINE, g["line_red"], RED)
    else:
        set_emit(M_LINE, g["line_orange"])
    line.location = (0, 0, 0) if max(g["line_red"], g["line_orange"]) > 0.02 else AWAY
    set_emit(M_PLUG, g["plug"] + 0.0)
    loc, target, lens = camera_at(t)
    cam.location = loc
    cam.rotation_euler = (target - loc).to_track_quat("-Z", "Y").to_euler()
    cam_data.lens = lens
    cam_data.dof.focus_distance = (target - loc).length
    # tailpiece glow rides on the plug material; brief and subtle
    if g["tail"] > 0.05:
        set_emit(M_PLUG, g["tail"] * 0.5)
    return which, tip, theta

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1 + scn.frame_subframe) / FPS)

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    out = {k: [] for k in ("plug", "tail", "spring", "top", "bottom", "shear", "wrongpin", "depth_a", "depth_b")}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        which, tip, theta = apply_state(t)
        vl.update()
        tips = LA.pin_tips(t, E)
        i = LA.WRONG_PIN
        z_d = drivers[i].location.z
        cuts = LA.BAD if which == "bad" else LA.GOOD
        u = LA.FULL_TIP - LA.PIN_X[i]
        pts = {
            "plug": plug_b.matrix_world @ Vector((3.95, 0, 0.72)),
            "tail": plug_b.matrix_world @ Vector((5.25, 0, 0.3)),
            "spring": Vector((X[i], 0, (z_d + LA.DRIVER_LEN + LA.SPRING_TOP) / 2)),
            "top": Vector((X[i], 0, z_d + LA.DRIVER_LEN / 2)),
            "bottom": rot_x(theta, (X[i], 0, tips[i] + LA.key_pin_len(i) * 0.4)),
            "shear": Vector((4.1, 0, LA.SHEAR)),
            "wrongpin": rot_x(theta, (X[i], 0, tips[i] + LA.key_pin_len(i))),
            "depth_a": Vector((tip - u, 0, LA.GOOD[i])),
            "depth_b": Vector((tip - u, 0, LA.BAD[i])),
        }
        for k, p in pts.items():
            v = world_to_camera_view(scene, cam, p)
            out[k].append([round(v.x * 1080, 1), round((1 - v.y) * 1920, 1)] if v.z > 0 else None)
    with open(os.path.join(OUT, "anchors.json"), "w") as fh:
        json.dump(out, fh)

anchors()
bpy.app.handlers.frame_change_pre.append(on_frame)
r.use_lock_interface = True
r.filepath = os.path.join(OUT, "f_#####")
if MODE == "all":
    scene.frame_start, scene.frame_end = 1, NF
    bpy.ops.render.render(animation=True)
else:
    for n in [int(x) for x in MODE.split(",")]:
        path = os.path.join(OUT, f"f_{n:05d}.png")
        if os.path.exists(path):
            os.remove(path)
        scene.frame_start = scene.frame_end = n
        bpy.ops.render.render(animation=True)
