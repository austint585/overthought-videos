"""Product-studio kit, pen set: a clear stick ballpoint and its cap, modeled in code at 10x scale (1 unit = 10 cm of
real pen: 147 mm long, 8.3 mm across, 1 mm ball) on the walnut desk. Shots, listed with start times by the render script:

  cap, cap_out     the cap standing on the desk, close on the hole in its top (cap_out plays backwards, for the loop)
  throat           a windpipe cut in half with a cut-in-half cap stuck in it, air dots squeezing through the hole
  std              the cap lying down, slow orbit
  barrel           macro on the small hole in the barrel
  drop             the pen upright: ink level falling, air dots coming in through the barrel hole
  tip              macro on the tip and ball
  socket           the tip cut in half: ball, socket, ink behind it; a leak grows for 'too loose'
  roll             the pen writing a line on paper, low
  thin             the cut tip again, closer, ink dots speeding up as the ball spins
  chew             the cap on the desk with bite marks

blender -b --factory-startup -P pen_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Writes out_dir/anchors.json (screen points for labels, every frame).
"""
import json, math, os, random, sys
import bpy, bmesh
from mathutils import Matrix, Vector
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
rng = random.Random(5)
AWAY = Vector((0, 0, -1.0e4))
INK_BLUE = (0.015, 0.06, 0.55)
AIRC = (0.45, 0.85, 1.0)

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
    hdr = nt.nodes.new("ShaderNodeBackground"); hdr.inputs[1].default_value = 0.3
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

def see_through(name, color, alpha, rough=0.08):
    m = plain(name, color, rough=rough, coat=0.6)
    principled(m).inputs["Alpha"].default_value = alpha
    m.surface_render_method = "BLENDED"
    m.use_transparent_shadow = True
    m.show_transparent_back = False
    return m

def glowing(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = (*color, 1); e.inputs[1].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs[0])
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

# ------------------------------------------------------------------ builders

def lathe(profile, seg=72, span=2 * math.pi):
    """Spin a closed (r, z) outline around z. A span under a full turn gives a cut-in-half part with closed cut faces,
    on the +y side, so a camera on -y looks straight at the cut."""
    def build(bm):
        full = span >= 2 * math.pi - 1e-6
        n = seg if full else seg + 1
        rings = [[bm.verts.new((r * math.cos(span * i / seg), r * math.sin(span * i / seg), z)) for r, z in profile] for i in range(n)]
        m = len(profile)
        for i in range(seg):
            a, b = rings[i], rings[(i + 1) % n]
            for j in range(m):
                k = (j + 1) % m
                try:
                    bm.faces.new((a[j], b[j], b[k], a[k]))
                except ValueError:
                    pass
        if not full:
            bm.faces.new(rings[0])
            bm.faces.new(rings[-1])
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return build

def part(name, build, mat, parent=None, smooth=80, loc=(0, 0, 0)):
    ob = B.mesh_from(name, build, [mat])
    if smooth:
        B.smooth(ob, smooth)
    ob.parent = parent
    ob.location = loc
    return ob

def sphere(name, r, mat, parent=None, subdiv=3):
    def b(bm):
        bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    return part(name, b, mat, parent)

def hexrod(z0, z1, r):
    def b(bm):
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=r, radius2=r, depth=z1 - z0,
                              matrix=Matrix.Translation((0, 0, (z0 + z1) / 2)) @ Matrix.Rotation(math.radians(30), 4, "Z"))
    return b

def disc_x(r, h, x, z):
    def b(bm):
        bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=r, radius2=r, depth=h,
                              matrix=Matrix.Translation((x, 0, z)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    return b

# ------------------------------------------------------------------ desk

desk_m = pbr_texture("walnut", "black_walnut_veneer_01", 4.5)
B.mesh_from("desk", B.box(-5, 5, -4, 5, -0.1, 0.0), [desk_m])
for i in range(6):
    p = Vector((rng.uniform(-5, 5), rng.uniform(6, 9), rng.uniform(0.5, 4.0)))
    B.mesh_from(f"bokeh{i}", B.cyl_z(0.11, p.z - 0.005, p.z + 0.005, p.x, p.y, seg=24), [glowing(f"bk{i}", (1.0, 0.62, 0.32), rng.uniform(3, 9))])
B.area("key", (-1.8, -2.2, 2.4), (0.2, 0, 0.2), 1.6, 30.0, color=(1.0, 0.88, 0.74))
B.area("rim", (1.8, 1.8, 1.5), (0.2, 0, 0.2), 1.0, 28.0, color=(0.65, 0.75, 1.0))
B.area("top", (0, 0, 3.0), (0, 0, 0), 1.5, 14.0, color=(1, 0.95, 0.9))

CAP_BLUE = plain("capblue", (0.015, 0.06, 0.55), rough=0.22, coat=0.5)
CLEAR = see_through("clear", (0.82, 0.88, 0.92), 0.26)
TUBE = see_through("tube", (0.85, 0.88, 0.9), 0.10)
INK = plain("ink", INK_BLUE, rough=0.18, coat=0.3)
BRASS = plain("brass", (0.86, 0.68, 0.36), rough=0.22, metal=1.0)
CARB = plain("carbide", (0.42, 0.43, 0.46), rough=0.16, metal=1.0)
HOLE_M = plain("hole", (0.004, 0.004, 0.005), rough=0.8)

# ------------------------------------------------------------------ the cap (hole through the top, open at the bottom)

CAP_PROFILE = [(0.058, 0.0), (0.056, 0.42), (0.044, 0.50), (0.018, 0.515), (0.012, 0.50), (0.012, 0.47), (0.030, 0.45), (0.044, 0.40), (0.046, 0.0)]

def bite_marks(parent, r=0.056):
    for i, a in enumerate((0.3, 1.0, 1.7, 3.4, 4.1, 5.0)):
        dark = plain(f"bite{i}", (0.008, 0.03, 0.28), rough=0.5)
        ob = sphere(f"bite{i}", 0.013, dark, parent, 2)
        ob.location = (r * math.cos(a), r * math.sin(a), 0.03 + 0.05 * (i % 2))
        ob.scale = (0.6, 1.2, 1.6)
        ob.rotation_euler = (0, 0, a)

CAP = C_ROOT = B.link(bpy.data.objects.new("cap", None))
part("cap.body", lathe(CAP_PROFILE), CAP_BLUE, CAP)
part("cap.clip", B.box(-0.012, 0.012, -0.075, -0.056, 0.14, 0.46), CAP_BLUE, CAP, smooth=0)
part("cap.clipb", B.box(-0.012, 0.012, -0.086, -0.072, 0.14, 0.19), CAP_BLUE, CAP, smooth=0)
CAP_HOME = Vector((0.0, 0.0, 0.0))
bite_marks(CAP)
for ob in CAP.children:
    if ob.name.startswith("bite"):
        ob.hide_render = True
BITES = [o for o in CAP.children if o.name.startswith("bite")]

# ------------------------------------------------------------------ the pen, tip at local z 0, back end at 1.47

PEN = B.link(bpy.data.objects.new("pen", None))
part("pen.tip", lathe([(0.0, 0.0035), (0.0065, 0.0035), (0.018, 0.09), (0.018, 0.14), (0.0, 0.14)]), BRASS, PEN)
BALL = sphere("pen.ball", 0.005, CARB, PEN)
BALL.location = (0, 0, 0.0005)
part("pen.nose", lathe([(0.0, 0.08), (0.0185, 0.08), (0.0415, 0.25), (0.0, 0.25)]), CLEAR, PEN)
part("pen.barrel", hexrod(0.24, 1.40, 0.0415), CLEAR, PEN, smooth=20)
part("pen.tube", lathe([(0.017, 0.12), (0.017, 1.34), (0.015, 1.34), (0.015, 0.12)]), TUBE, PEN)
ink = part("pen.ink", lathe([(0.0, 0.0), (0.0145, 0.0), (0.0145, 1.0), (0.0, 1.0)]), INK, PEN)
ink.location = (0, 0, 0.13)
INK_TOP0 = 1.18
part("pen.plug", lathe([(0.0, 1.38), (0.03, 1.38), (0.03, 1.455), (0.024, 1.47), (0.0, 1.47)]), CAP_BLUE, PEN)
HOLE_Z = 0.78
FACE_X = -0.0415 * math.cos(math.radians(30))
part("pen.hole", disc_x(0.0075, 0.0012, FACE_X - 0.0002, HOLE_Z), HOLE_M, PEN, smooth=0)

# ------------------------------------------------------------------ windpipe and half cap (their own little set)

THROAT = B.link(bpy.data.objects.new("throat", None))
FLESH = plain("flesh", (0.72, 0.22, 0.20), rough=0.32, coat=0.5)
RING_M = plain("cartilage", (0.86, 0.68, 0.60), rough=0.45)
part("th.wall", lathe([(0.075, -0.75), (0.075, 0.75), (0.10, 0.75), (0.10, -0.75)], span=math.pi), FLESH, THROAT)
for i in range(11):
    z = -0.68 + i * 0.136
    part(f"th.ring{i}", lathe([(0.094, z - 0.03), (0.094, z + 0.03), (0.112, z + 0.03), (0.112, z - 0.03)], span=math.pi), RING_M, THROAT)
part("th.cap", lathe(CAP_PROFILE, span=math.pi), CAP_BLUE, THROAT, loc=(0, 0, -0.2))
part("th.fill", lathe([(0.058, -0.2), (0.058, 0.2), (0.076, 0.2), (0.076, -0.2)], span=math.pi), plain("thfold", (0.58, 0.16, 0.15), rough=0.4), THROAT)
air_m = glowing("air", AIRC, 6.0)
AIR = [sphere(f"air{i}", 0.0052, air_m, None, 2) for i in range(26)]
OUTAIR = [sphere(f"oair{i}", 0.0052, air_m, None, 2) for i in range(12)]

# ------------------------------------------------------------------ cut tip (socket), own set, ball at local origin, 4x larger than the pen's

SEC = B.link(bpy.data.objects.new("section", None))
HOUSE = plain("house", (0.86, 0.68, 0.36), rough=0.25, metal=1.0)
R_BALL = 0.04
part("sec.house", lathe([(0.030, -0.018), (0.075, 0.10), (0.15, 0.36), (0.15, 0.62), (0.03, 0.62), (0.03, 0.09), (0.042, 0.03), (0.0415, 0.0)], span=math.pi), HOUSE, SEC)
part("sec.ink", lathe([(0.0, 0.05), (0.028, 0.05), (0.028, 0.62), (0.0, 0.62)], span=math.pi), INK, SEC)
SECBALL = sphere("sec.ball", R_BALL, CARB, SEC, 4)
for i, (dx, dz) in enumerate(((0.024, 0.024), (-0.03, 0.005), (0.0, -0.034))):
    d = sphere(f"sec.mark{i}", 0.006, plain(f"mk{i}", (0.05, 0.05, 0.06), rough=0.4), SECBALL, 2)
    d.location = (dx, -0.018 if i else -0.022, dz)
LEAK = sphere("sec.leak", 0.022, INK, SEC, 3)
LEAK.location = (0.0, 0.0, -0.05)
INKD = [sphere(f"d{i}", 0.0042, glowing(f"dg{i}", (0.25, 0.5, 1.0), 4.0), SEC, 2) for i in range(18)]

# ------------------------------------------------------------------ paper and the line

PAPER = part("paper", B.box(-1.6, 1.6, -1.2, 1.2, 0.0, 0.006), plain("paperm", (0.86, 0.84, 0.79), rough=0.7), smooth=0)
LINE = part("line", B.box(0.0, 1.0, -0.006, 0.006, 0.0, 0.001), plain("linem", INK_BLUE, rough=0.3), smooth=0)

# ------------------------------------------------------------------ shots

cam = B.camera(lens=50, fstop=2.0)
cam.data.clip_start = 0.005

def lerp_cam(a, b, target, lens, fstop, u):
    return Vector(a).lerp(Vector(b), smooth01(u)), Vector(target), lens, fstop

PEN_LAID = (Vector((0.9, 0.05, 0.0365)), (0, math.pi / 2, 0))    # flat face with the hole up, tip toward +x
HOLE_W = PEN_LAID[0] + Vector((HOLE_Z, 0, 0.0))
PEN_UP = Vector((0.0, 0.0, 0.08))
THROAT_AT = Vector((0.0, 0.0, 0.9))
SEC_AT = Vector((0.0, 0.0, 0.8))
ROLL_AT = Vector((0.0, 0.0, 0.006))
CAP_TOP = Vector((0, 0, 0.515))

def s_cap(u):
    return lerp_cam((0.42, -0.70, 1.08), (0.27, -0.46, 0.92), CAP_TOP + Vector((0, 0, -0.03)), 62, 8.0, u)

CAMS = {
    "cap": s_cap,
    "cap_out": lambda u: s_cap(1.0 - u),
    "throat": lambda u: lerp_cam((0.03, -1.15, 0.98), (0.0, -0.95, 0.92), THROAT_AT + Vector((0, 0, 0.14)), 50, 18.0, u),
    "std": lambda u: lerp_cam((-0.65, -0.72, 0.55), (-0.50, -0.82, 0.48), Vector((0, 0, 0.26)), 55, 7.0, u),
    "barrel": lambda u: lerp_cam(HOLE_W + Vector((-0.20, -0.30, 0.20)), HOLE_W + Vector((-0.15, -0.23, 0.16)), HOLE_W, 62, 12.0, u),
    "drop": lambda u: lerp_cam((0.14, -2.45, 1.0), (0.10, -2.2, 0.95), Vector((0, 0, 0.86)), 44, 18.0, u),
    "tip": lambda u: lerp_cam(PEN_LAID[0] + Vector((0.21, -0.20, 0.09)), PEN_LAID[0] + Vector((0.14, -0.15, 0.07)), PEN_LAID[0] + Vector((0.03, 0, 0.0)), 70, 13.0, u),
    "socket": lambda u: lerp_cam(SEC_AT + Vector((0.08, -0.75, 0.22)), SEC_AT + Vector((0.05, -0.62, 0.19)), SEC_AT + Vector((0, 0, 0.13)), 55, 22.0, u),
    "roll": lambda u: lerp_cam((0.06, -0.48, 0.17), (0.2, -0.40, 0.14), Vector((0.1, 0.0, 0.05)), 42, 9.0, u),
    "thin": lambda u: lerp_cam(SEC_AT + Vector((0.03, -0.42, 0.08)), SEC_AT + Vector((0.02, -0.34, 0.07)), SEC_AT + Vector((0, 0, 0.05)), 55, 22.0, u),
    "chew": lambda u: lerp_cam((-0.32, -0.55, 0.30), (-0.25, -0.44, 0.24), Vector((0, 0, 0.13)), 55, 9.0, u),
}

def alt_cam(base, u):
    """The same action from a second angle: swung around the subject and closer."""
    loc, tg, lens, fstop = base(u)
    return tg + (Matrix.Rotation(-0.5, 3, "Z") @ (loc - tg)) * 0.75, tg, lens, fstop

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

def air_path_throat(p):
    """0..1 up the pipe from below, squeezing in through the open end of the cap and out of the hole."""
    az = -0.72 + 1.44 * p
    top = 0.31                                      # hole height in throat space (the cap sits 0.2 lower)
    if az < -0.25:
        r = 0.05
    elif az < top:
        r = 0.04 * (1 - (az + 0.25) / (top + 0.25)) + 0.004
    else:
        r = 0.006 + min(0.05, (az - top) * 0.5)
    return az, r

def set_state_air(t, name, u):
    th = name == "throat"
    for i, ob in enumerate(AIR):
        if th:
            p = ((t * 0.32 + i / len(AIR)) % 1.0)
            az, r = air_path_throat(p)
            a = i * 2.4
            ob.location = THROAT_AT + Vector((r * math.cos(a), 0.0035 + r * abs(math.sin(a)), az))
        else:
            ob.location = AWAY
    drop = name == "drop" and u < 0.55
    for i, ob in enumerate(OUTAIR):
        if drop:                                    # in through the barrel hole, up the gap, into the open tube
            p = (t * 0.33 + i / len(OUTAIR)) % 1.0
            x0 = FACE_X - 0.05
            if p < 0.18:
                loc = (x0 + (0.03 - x0) * p / 0.18 - 0.0, 0.0, HOLE_Z)
            elif p < 0.72:
                loc = (0.028, 0.0, HOLE_Z + (1.36 - HOLE_Z) * (p - 0.18) / 0.54)
            else:
                loc = (0.028 * (1 - p) / 0.28, 0.0, 1.36 - (1.36 - ink_top(t, u)) * (p - 0.72) / 0.28)
            ob.location = PEN_UP + Vector(loc)
        else:
            ob.location = AWAY

def ink_top(t, u):
    return INK_TOP0 - 0.3 * min(1.0, u / 0.55)

def apply_state(t):
    name, u, age, cut, second = shot_at(t)
    loc, tg, lens, fstop = alt_cam(CAMS[name], cut) if second else CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    cam.data.dof.focus_distance = (tg - loc).length
    cam.data.dof.aperture_fstop = fstop
    cam.data.clip_end = 60

    # the cap: upright, lying, or gone
    if name in ("cap", "cap_out", "chew", "std"):
        CAP.location = CAP_HOME
        CAP.rotation_euler = (0, 0, 0)
    else:
        CAP.location = PEN_LAID[0] + Vector((-1.45, -0.4, 0.0))
    for ob in BITES:
        ob.hide_render = name != "chew"
    # the pen
    if name == "drop":
        PEN.location, PEN.rotation_euler = PEN_UP, (0, 0, 0)
    elif name == "roll":
        x = 0.25 * u + 0.0
        PEN.location = ROLL_AT + Vector((x, 0, 0.0052))
        PEN.rotation_euler = (0, -0.75, 0.0)
    elif name in ("cap", "cap_out", "std", "chew", "barrel", "tip"):
        PEN.location, PEN.rotation_euler = PEN_LAID
    else:
        PEN.location = AWAY
    top = ink_top(t, u) if name == "drop" else INK_TOP0
    ink.scale = (1, 1, top - 0.13)
    BALL.rotation_euler = (0, age * 10.0 if name == "roll" else 0.0, 0)

    THROAT.location = THROAT_AT if name == "throat" else AWAY
    SEC.location = SEC_AT if name in ("socket", "thin") else AWAY
    set_state_air(t, name, u)

    # the leak in the second half of 'socket' (too loose)
    grow = smooth01((u - 0.55) / 0.3) if name == "socket" else 0.0
    LEAK.scale = (max(grow, 0.001),) * 3
    LEAK.location = (0.0, -0.002, -R_BALL - 0.01 - 0.035 * grow)
    SECBALL.rotation_euler = (0, (age * 3.0 if name == "socket" else age * (2.0 + 6.0 * u) if name == "thin" else 0.0), 0)
    for i, ob in enumerate(INKD):
        if name in ("socket", "thin"):
            speed = 0.12 if name == "socket" else 0.12 + 0.9 * smooth01(u)
            phase = (age * speed + i / len(INKD)) % 1.0
            a = (i * 1.7) % 1.0
            if phase < 0.5:                                # down the ink column
                ob.location = (-0.022 + 0.044 * a, -0.0035, 0.5 - 0.42 * phase * 2)
            else:                                          # around the ball, in the film under it
                ang = math.pi / 2 + (phase - 0.5) * 2 * math.pi * (1 if i % 2 else -1)
                ob.location = (0.046 * math.cos(ang), -0.0035, 0.046 * math.sin(ang))
        else:
            ob.location = AWAY

    # paper and the written line
    show = name == "roll"
    PAPER.location = Vector((0.1, 0, 0)) if show else AWAY
    LINE.location = Vector((-0.75, 0, 0.0065)) if show else AWAY
    LINE.scale = (0.75 + 0.25 * u + 0.0005, 1, 1)

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    pts = {
        "hole": lambda: CAP.location + Vector((0.0, 0.0, 0.517)),
        "airway": lambda: THROAT_AT + Vector((0.0, 0.0, 0.34)),
        "tcap": lambda: THROAT_AT + Vector((0.05, 0.0, 0.0)),
        "vent": lambda: HOLE_W + Vector((0.0, 0.0, 0.003)),
        "vent_up": lambda: PEN_UP + Vector((FACE_X, 0.0, HOLE_Z)),
        "inktop": lambda: PEN_UP + Vector((0.0, 0.0, 1.0)),
        "ball": lambda: PEN_LAID[0] + Vector((0.0, 0.0, 0.0)),
        "secball": lambda: SEC_AT + Vector((0.02, -0.01, -0.01)),
        "secink": lambda: SEC_AT + Vector((0.0, 0.0, 0.26)),
        "seat": lambda: SEC_AT + Vector((0.045, 0.0, 0.03)),
        "line": lambda: Vector((-0.25, 0.0, 0.007)),
        "bite": lambda: Vector((0.03, -0.05, 0.05)),
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

B.render_settings(FPS, samples=int(os.environ.get("PEN_SAMPLES", "40")), motion_blur=0.25, look="AgX - Medium High Contrast")

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1 + scn.frame_subframe) / FPS)

anchors()
apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
