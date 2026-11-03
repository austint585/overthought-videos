"""Pastel toy kit, AI water episode (the @howyourhouseworks.au look in ops/style.md): smooth bevelled props in flat pastel
colors, bright soft daylight, numbers on signs in the scene. Everything is modeled here. Shots are named; the render
script lists them with start times in timing.json:

  hook, hook_out   a framed AI picture drinks from a 500 mL bottle through a straw; a red X lands on the sign on events.not / not2.
                   hook_out ends on hook's first frame, for the loop
  paper, nopic     the paper on a clipboard; then the same with a picture beside it and no number for it
  cups             little cups pop up in front of a bottle, 10 then 50
  measure          a picture in a measuring jug, nobody knows
  drops            an eyedropper fills a glass, the sign counts to 12 mL
  spoons           two tablespoons on a stand, 29 mL
  flush            a mitt presses the toilet handle on events.press; framed pictures go down from events.count0 to events.count1
  loop, micro, meter   a water loop around a server rack: crossed out on events.wrong, then the late 2027 sign, then a power gauge rising
  tower, dc, plant, town   outdoor diorama: steam off the data center roof, the building from the road, the power plant, the town at its feet
  nothing          one tiny picture beside the glass

blender -b --factory-startup -P water_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
"""
import json, math, os, random, sys
import bpy, bmesh
from mathutils import Vector, Euler, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bkit as B

argv = sys.argv[sys.argv.index("--") + 1:]
TIMING, OUT, MODE = argv[0], argv[1], argv[2]
T = json.load(open(TIMING))
FPS, DUR = T["fps"], T["duration"]
NF = int(round(DUR * FPS))
SHOTS, EV, TEX, FONT = T["shots"], T["events"], T["textures"], T["font"]
os.makedirs(OUT, exist_ok=True)
B.clear_scene()
scene = B.scene
rng = random.Random(5)
AWAY = Vector((0, 0, -1.0e4))
BATH = Vector((20, 0, 0))          # the bathroom set sits away from the kitchen counter at the origin
N_PICS = 209

def hexc(s):
    """sRGB hex to linear."""
    def lin(v):
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return tuple(lin(int(s[i:i + 2], 16) / 255) for i in (0, 2, 4))

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

def back_out(u):
    u = max(0.0, min(1.0, u)) - 1
    return 1 + 2.7 * u ** 3 + 1.7 * u ** 2

def mat(name, color, rough=0.55):
    return B.material(name, hexc(color), rough=rough)

def tex_mat(name, path, rough=0.4, rotating=False):
    m = B.material(name, (1, 1, 1), rough=rough)
    nt = m.node_tree
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(path)
    if rotating:
        uv = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.name = "spin"
        mp.inputs["Location"].default_value = (0.5, 0.5, 0)
        nt.links.new(uv.outputs["UV"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], tx.inputs["Vector"])
    nt.links.new(tx.outputs["Color"], B.bsdf(m).inputs["Base Color"])
    return m

def rbox(name, x0, x1, y0, y1, z0, z1, m, bev=0.012, off=Vector()):
    ob = B.mesh_from(name, B.box(x0 + off.x, x1 + off.x, y0 + off.y, y1 + off.y, z0 + off.z, z1 + off.z), [m])
    if bev:
        B.bevel(ob, bev)
        B.smooth(ob)
    return ob

def lathe(name, profile, m, seg=72, sy=1.0, at=Vector(), uv=None, closed=False):
    """Spin a (radius, z) profile around z. uv: 'wrap' for a label, 'planar' centered on the axis for the water."""
    def b(bm):
        layer = bm.loops.layers.uv.new("UVMap") if uv else None
        rings = [[bm.verts.new((max(r, 1e-4) * math.cos(2 * math.pi * j / seg), max(r, 1e-4) * sy * math.sin(2 * math.pi * j / seg), z))
                  for j in range(seg)] for r, z in profile]
        n = len(profile)
        rmax = max(r for r, _ in profile)
        for i in range(n if closed else n - 1):
            i1 = (i + 1) % n
            for j in range(seg):
                j1 = (j + 1) % seg
                f = bm.faces.new((rings[i][j], rings[i][j1], rings[i1][j1], rings[i1][j]))
                if uv == "wrap":
                    for l, (a, c) in zip(f.loops, ((j, i), (j + 1, i), (j + 1, i1), (j, i1))):
                        l[layer].uv = (a / seg, c / (n - 1))    # 0.75 faces -y, the middle of the label's second print
                elif uv == "planar":
                    for l in f.loops:
                        l[layer].uv = (l.vert.co.x / (2 * rmax), l.vert.co.y / (2 * rmax * sy))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = B.mesh_from(name, b, [m])
    ob.location = at
    ob.data.shade_smooth()
    return ob

def quad(name, w, h, m, at, parent=None):
    """A rectangle in the xz plane facing -y with a full UV."""
    def b(bm):
        layer = bm.loops.layers.uv.new("UVMap")
        vs = [bm.verts.new(p) for p in ((-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2))]
        f = bm.faces.new(vs)
        for l, u in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            l[layer].uv = u
    ob = B.mesh_from(name, b, [m])
    ob.location = at
    ob.parent = parent
    return ob

_font = bpy.data.fonts.load(FONT)

def text(name, body, size, color, at, parent=None, glow=1.0):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body, cu.font, cu.size = body, _font, size
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.resolution_u = 4
    ob = B.link(bpy.data.objects.new(name, cu))
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = (*hexc(color), 1)
    e.inputs[1].default_value = glow
    nt.links.new(e.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs[0])
    ob.data.materials.append(m)
    ob.parent = parent
    ob.location = at
    ob.rotation_euler = (math.pi / 2, 0, 0)
    return ob

def set_text_color(ob, color):
    ob.data.materials[0].node_tree.nodes["Emission"].inputs[0].default_value = (*hexc(color), 1)

def sign(name, at, w, h, head, big, foot, s=1.0):
    """A dark rounded board hung on the wall. Three lines of glowing text: a small head, a big number, a small foot."""
    root = B.link(bpy.data.objects.new(name, None))
    root.location = at
    plate = rbox(name + "p", -w / 2, w / 2, -0.012, 0.012, -h / 2, h / 2, mat(name + "pm", "2F3843", 0.5), bev=0.012)
    plate.parent = root
    rim = B.mesh_from(name + "r", B.many(B.box(-w / 2 + 0.01, w / 2 - 0.01, -0.0145, -0.0125, h / 2 - 0.017, h / 2 - 0.011),
                                         B.box(-w / 2 + 0.01, w / 2 - 0.01, -0.0145, -0.0125, -h / 2 + 0.011, -h / 2 + 0.017),
                                         B.box(-w / 2 + 0.011, -w / 2 + 0.017, -0.0145, -0.0125, -h / 2 + 0.011, h / 2 - 0.011),
                                         B.box(w / 2 - 0.017, w / 2 - 0.011, -0.0145, -0.0125, -h / 2 + 0.011, h / 2 - 0.011)),
                      [mat(name + "rm", "9FC3DD", 0.5)])
    rim.parent = root
    head_t = text(name + "h", head, 0.042 * s, "F4F1E8", (0, -0.016, h * 0.33), root)
    big_t = text(name + "b", big, 0.105 * s, "FFFFFF", (0, -0.016, -0.005 * s), root, glow=1.1)
    foot_t = text(name + "f", foot, 0.036 * s, "F4F1E8", (0, -0.016, -h * 0.34), root)
    return root, head_t, big_t, foot_t

# ------------------------------------------------------------------ materials

cream = mat("cream", "F4ECDD", 0.8)
brick_m = mat("brick", "FBF8F2", 0.6)
top_m = mat("top", "F1ECE5", 0.35)
sage = mat("sage", "83A392", 0.6)
sage_d = mat("saged", "6F8F7E", 0.6)
handle_m = B.material("handle", hexc("3F4650"), metallic=0.6, rough=0.35)
wood = mat("wood", "D79A5F", 0.5)
wood_d = mat("woodd", "B97F4A", 0.55)
coral = mat("coral", "EE6F52", 0.4)
water_m = mat("water", "8FCDEE", 0.12)
cap_m = mat("cap", "2F7FD0", 0.35)
shell_m = B.material("shell", hexc("DDF1FB"), rough=0.08)
shell_m.surface_render_method = "BLENDED"
B.bsdf(shell_m).inputs["Alpha"].default_value = 0.30
pic_m = tex_mat("pic", TEX["picture"], rough=0.45)
label_m = tex_mat("label", TEX["label"], rough=0.45)
red_x = B.material("redx", hexc("E5392F"), rough=0.4)
porcelain = mat("porcelain", "FAFAF6", 0.18)
seat_m = mat("seat", "F4EFE4", 0.3)
tile_m = mat("tile", "BFE4D7", 0.28)
grout_m = mat("grout", "EEF4EE", 0.8)
floor_m = mat("floor", "E9CBA9", 0.55)
mat_m = mat("mat", "F2A98C", 0.9)
chrome = B.material("chrome", (0.75, 0.77, 0.8), metallic=1.0, rough=0.2)
sleeve_m = mat("sleeve", "4F8A6B", 0.7)
mitt_m = mat("mitt", "D9743F", 0.6)
paper_m = mat("paper", "FFFFFF", 0.8)
swirl_m = tex_mat("swirl", TEX["swirl"], rough=0.1, rotating=True)
swirl_map = swirl_m.node_tree.nodes["spin"]

# ------------------------------------------------------------------ set 1: the counter

rbox("wall", -4.5, 4.5, 0.30, 0.42, 0, 3.2, cream, bev=0)
bricks = []
for row in range(6):
    z = 0.912 + row * 0.056
    for k in range(-32, 33):
        x = k * 0.136 + (0.068 if row % 2 else 0)
        bricks.append(B.box(x - 0.065, x + 0.065, 0.286, 0.306, z, z + 0.05))
bk = B.mesh_from("bricks", B.many(*bricks), [brick_m])
B.bevel(bk, 0.003, segments=2)
B.smooth(bk)
rbox("counter", -4.5, 4.5, -0.46, 0.296, 0.86, 0.905, top_m, bev=0.008)
rbox("cab", -4.5, 4.5, -0.40, 0.28, 0, 0.855, sage_d, bev=0)
for k in range(-9, 10):
    x = k * 0.46
    rbox(f"door{k}", x - 0.222, x + 0.222, -0.415, -0.395, 0.04, 0.84, sage, bev=0.008)
    hx = x + 0.17 if k % 2 else x - 0.17
    rbox(f"pull{k}", hx - 0.009, hx + 0.009, -0.435, -0.41, 0.62, 0.78, handle_m, bev=0.004)

# the picture on a little easel, tipped back; `frame` is what bounces
PIC_AT = Vector((0.105, -0.04, 0.905))
frame = B.link(bpy.data.objects.new("frame", None))
frame.location = PIC_AT
frame.rotation_euler = (math.radians(-9), 0, math.radians(-5))
FW, FH = 0.225, 0.272
fm = rbox("fr", -FW / 2, FW / 2, -0.016, 0.016, 0.0, FH, wood, bev=0.010)
fm.parent = frame
quad("picq", FW - 0.042, FH - 0.042, pic_m, Vector((0, -0.0175, FH / 2)), frame)
leg = rbox("leg", -0.018, 0.018, 0.0, 0.11, 0.0, 0.012, wood_d, bev=0.004, off=Vector((0, 0.03, 0.0)))
leg.parent = frame

# the bottle: a 500 mL bottle at 1.3x so it reads at phone size
BOT = Vector((-0.135, -0.075, 0.905))
PROF = [(0.0, 0.0), (0.036, 0.0), (0.044, 0.008), (0.044, 0.17), (0.041, 0.185), (0.044, 0.20), (0.043, 0.215),
        (0.036, 0.245), (0.018, 0.268), (0.016, 0.285), (0.016, 0.292)]
lathe("shell", PROF, shell_m, at=BOT)
W_PROF = [(0.0, 0.003), (0.034, 0.003), (0.0415, 0.01), (0.0415, 0.168), (0.0385, 0.185), (0.0415, 0.2), (0.0405, 0.214), (0.030, 0.235), (0.0, 0.2355)]
water = lathe("wat", W_PROF, water_m, at=BOT)
lathe("label", [(0.0448, 0.055), (0.0448, 0.15)], label_m, at=BOT, uv="wrap")
cap = lathe("cap", [(0.0, 0.0), (0.0175, 0.0), (0.0185, 0.002), (0.0185, 0.018), (0.015, 0.021), (0.0, 0.021)], cap_m,
            at=BOT + Vector((0.075, -0.075, 0.0)))
sc = bpy.data.curves.new("straw", "CURVE")
sc.dimensions = "3D"
sc.bevel_depth = 0.0055
sc.bevel_resolution = 3
sp = sc.splines.new("BEZIER")
top_pic = PIC_AT + Vector((-0.055, 0.044, FH - 0.006))
sp.bezier_points.add(3)
pts = [BOT + Vector((0.004, 0, 0.10)), BOT + Vector((0.004, 0, 0.285)), BOT + Vector((0.085, 0.03, 0.312)), top_pic + Vector((0, 0.002, 0.0))]
for bp, p in zip(sp.bezier_points, pts):
    bp.co = p
    bp.handle_left_type = bp.handle_right_type = "AUTO"
straw = B.link(bpy.data.objects.new("straw", sc))
sc.materials.append(coral)

SIGN1, s1h, s1b, s1f = sign("s1", Vector((-0.005, 0.27, 1.355)), 0.42, 0.26, "ONE AI PICTURE", "500 mL", "PEOPLE SAY")
x1 = rbox("x1", -0.165, 0.165, -0.008, 0.008, -0.012, 0.012, red_x, bev=0.005)
x2 = rbox("x2", -0.165, 0.165, -0.008, 0.008, -0.012, 0.012, red_x, bev=0.005)
XROOT = B.link(bpy.data.objects.new("xroot", None))
XROOT.location = SIGN1.location + Vector((0, -0.03, -0.005))
for ob, a in ((x1, 17), (x2, -17)):
    ob.parent = XROOT
    ob.rotation_euler = (0, math.radians(a), 0)

# ------------------------------------------------------------------ set 2: the bathroom

rbox("bwall", -2, 2, 0.40, 0.52, 0, 3.2, grout_m, bev=0, off=BATH)
tiles = []
for row in range(24):
    z = 0.11 + row * 0.122
    for k in range(-10, 11):
        x = k * 0.122
        tiles.append(B.box(x - 0.058, x + 0.058, 0.388, 0.408, z, z + 0.116))
tl = B.mesh_from("tiles", B.many(*tiles), [tile_m])
tl.location = BATH
B.bevel(tl, 0.004, segments=2)
B.smooth(tl)
rbox("base", -2, 2, 0.372, 0.41, 0.0, 0.10, porcelain, bev=0.006, off=BATH)
rbox("bfloor", -2, 2, -2, 0.42, -0.1, 0.0, floor_m, bev=0, off=BATH)
lathe("bmat", [(0.0, 0.004), (0.30, 0.004), (0.32, 0.012), (0.30, 0.022), (0.0, 0.022)], mat_m, sy=0.72, at=BATH + Vector((0, -0.54, 0)))

SY = 1.22
BOWL = [(0.0, 0.0), (0.115, 0.0), (0.12, 0.012), (0.105, 0.05), (0.102, 0.12), (0.14, 0.28), (0.188, 0.395), (0.2, 0.41), (0.196, 0.422),
        (0.172, 0.424), (0.158, 0.385), (0.112, 0.285), (0.075, 0.24), (0.0, 0.22)]
lathe("bowl", BOWL, porcelain, sy=SY, at=BATH + Vector((0, -0.03, 0)))
SEAT = [(0.203, 0.424), (0.208, 0.436), (0.198, 0.449), (0.172, 0.451), (0.152, 0.44), (0.150, 0.426)]
lathe("seat", SEAT, seat_m, sy=SY, at=BATH + Vector((0, -0.03, 0)), closed=True)
rbox("tank", -0.215, 0.215, 0.205, 0.385, 0.42, 0.80, porcelain, bev=0.022, off=BATH)
rbox("tanklid", -0.228, 0.228, 0.195, 0.392, 0.803, 0.84, porcelain, bev=0.014, off=BATH)
rbox("neck", -0.13, 0.13, 0.12, 0.30, 0.03, 0.43, porcelain, bev=0.02, off=BATH)
lid = lathe("blid", [(0.0, 0.0), (0.195, 0.0), (0.206, 0.012), (0.19, 0.024), (0.0, 0.028)], seat_m, sy=SY, at=BATH + Vector((0, 0.135, 0.665)))
lid.rotation_euler = (math.radians(85), 0, 0)
# the lever sticks out of the tank's left side
LEVER_AT = BATH + Vector((-0.218, 0.262, 0.73))
lever = B.link(bpy.data.objects.new("lever", None))
lever.location = LEVER_AT
lb = rbox("lb", -0.012, 0.0, -0.025, 0.025, -0.025, 0.025, chrome, bev=0.006)
lb.parent = lever
la = rbox("la", -0.105, -0.008, -0.011, 0.011, -0.007, 0.007, chrome, bev=0.004)
la.parent = lever
# water: a shallow funnel whose z scale sets how deep the whirlpool is
swirl = lathe("swirl", [(0.0, -0.105), (0.018, -0.082), (0.045, -0.05), (0.085, -0.02), (0.128, 0.0)], swirl_m, sy=SY,
              at=BATH + Vector((0, -0.03, 0.325)), uv="planar")
# toilet paper, for scale and a laugh
for nm, r, h, m_, x in (("tp", 0.056, 0.105, paper_m, 0.335), ("tpa", 0.009, 0.135, chrome, 0.335)):
    ob = B.mesh_from(nm, B.cyl_z(r, -h / 2, h / 2, 0, 0, 40), [m_])
    ob.location = BATH + Vector((x, 0.33, 0.72))
    ob.rotation_euler = (0, math.pi / 2, 0)
    B.smooth(ob)
SIGN2, s2h, s2b, s2f = sign("s2", BATH + Vector((0.0, 0.365, 1.115)), 0.56, 0.34, "ONE FLUSH", "6 L", "= 0 AI PICTURES", s=1.3)

# the mitt that presses the lever
mitt = B.link(bpy.data.objects.new("mitt", None))
sl = B.mesh_from("slv", B.cyl_x(0.042, -0.7, -0.075, 40), [sleeve_m])
sl.parent = mitt
B.smooth(sl)
cf = B.mesh_from("cuf", B.cyl_x(0.047, -0.085, -0.055, 40), [mitt_m])
cf.parent = mitt
B.smooth(cf)
hb = rbox("hnd", -0.06, 0.03, -0.042, 0.042, -0.03, 0.03, mitt_m, bev=0.024)
hb.parent = mitt
th = rbox("thm", -0.03, 0.012, -0.018, 0.018, -0.052, -0.01, mitt_m, bev=0.012)
th.parent = mitt

# the 209 little framed pictures share one mesh
def mini_build(bm):
    layer = bm.loops.layers.uv.new("UVMap")
    w, h, d = 0.095, 0.118, 0.006
    B.with_material(B.box(-w / 2, w / 2, -d, d, -h / 2, h / 2), 0)(bm)
    vs = [bm.verts.new(p) for p in ((-w / 2 + 0.009, -d - 0.001, -h / 2 + 0.009), (w / 2 - 0.009, -d - 0.001, -h / 2 + 0.009),
                                     (w / 2 - 0.009, -d - 0.001, h / 2 - 0.009), (-w / 2 + 0.009, -d - 0.001, h / 2 - 0.009))]
    f = bm.faces.new(vs)
    f.material_index = 1
    for l, u in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        l[layer].uv = u
mini0 = B.mesh_from("mini0", mini_build, [wood, pic_m])
MINIS = []
c0, c1 = EV["count0"], EV["count1"]
LIFE = 0.8
for i in range(N_PICS):
    ob = mini0 if i == 0 else B.link(bpy.data.objects.new(f"mini{i}", mini0.data))
    ob.location = AWAY
    u = (i + 0.5) / N_PICS
    t_i = c0 + (c1 - c0) * u ** 0.8     # a few first, then a flood
    MINIS.append((ob, t_i, rng.uniform(-0.2, 0.2), rng.uniform(0, math.tau), rng.choice((-1, 1)) * rng.uniform(3, 7),
                  Euler((rng.uniform(0, 6), rng.uniform(0, 6), rng.uniform(0, 6))), rng.uniform(0.9, 1.1)))

def count_at(t):
    return sum(1 for m in MINIS if t >= m[1])

# ------------------------------------------------------------------ the rest of the counter: each prop has its own stretch of it

PAPER_X, CUPS_X, JUG_X, DROP_X, SPOON_X = -1.0, -2.0, 1.0, 2.0, 3.0
paper_m = tex_mat("papertex", TEX["paper"], rough=0.7)
board_m = mat("board", "A9764B", 0.55)
clip_m = B.material("clip", (0.7, 0.72, 0.75), metallic=1.0, rough=0.25)

clipb = B.link(bpy.data.objects.new("clipb", None))
clipb.location = Vector((PAPER_X + 0.045, -0.03, 0.905))
clipb.scale = (0.82, 0.82, 0.82)
clipb.rotation_euler = (math.radians(-10), 0, math.radians(3))
b_ = rbox("cb", -0.135, 0.135, -0.008, 0.008, 0, 0.345, board_m, bev=0.006)
b_.parent = clipb
quad("cbp", 0.235, 0.31, paper_m, Vector((0, -0.0095, 0.158)), clipb)
c_ = rbox("cbc", -0.05, 0.05, -0.02, 0.0, 0.312, 0.35, clip_m, bev=0.005)
c_.parent = clipb
l_ = rbox("cbl", -0.018, 0.018, 0.0, 0.10, 0.0, 0.012, board_m, bev=0.004, off=Vector((0, 0.02, 0)))
l_.parent = clipb
# the picture on set for 'nopic'
mini_np = B.link(bpy.data.objects.new("minip", mini0.data))
MINI_NP_AT = Vector((PAPER_X - 0.165, -0.11, 0.905 + 0.075))

def bottle_at(at):
    lathe("shell2", PROF, shell_m, at=at)
    w_ = lathe("wat2", W_PROF, water_m, at=at)
    lathe("label2", [(0.0448, 0.055), (0.0448, 0.15)], label_m, at=at, uv="wrap")
    return w_

water2 = bottle_at(Vector((CUPS_X - 0.17, 0.03, 0.905)))
cup_m = mat("cup", "FDFDFB", 0.35)
def cup_build(bm):
    bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=0.019, radius2=0.025, depth=0.042, matrix=Matrix.Translation((0, 0, 0.021)))
cup0 = B.mesh_from("cup0", cup_build, [cup_m])
cup0.data.shade_smooth()
wat_top = lathe("wtop0", [(0.0, 0.0432), (0.0255, 0.0432)], water_m, seg=20)
wat_top.parent = cup0
CUPS = []
crng = random.Random(11)
for i in range(50):
    r_, c_i = i // 10, i % 10
    ob = cup0 if i == 0 else B.link(bpy.data.objects.new(f"cup{i}", cup0.data))
    wt_ = wat_top if i == 0 else B.link(bpy.data.objects.new(f"wtop{i}", wat_top.data))
    wt_.parent = ob
    # the back row is the first ten; cups fill toward the camera
    x = CUPS_X - 0.085 + c_i * 0.034 - (0.012 if r_ % 2 else 0)
    y = 0.03 - r_ * 0.04
    ob.location = Vector((x, y, 0.906))
    CUPS.append(ob)

SGN_Z = 1.355
jug_s = lathe("jug", [(0.0, 0.0), (0.073, 0.0), (0.078, 0.008), (0.082, 0.19), (0.092, 0.205), (0.083, 0.2)], shell_m, at=Vector((JUG_X - 0.015, -0.06, 0.905)))
jug_h = lathe("jugh", [(0.042, 0.0), (0.05, 0.008), (0.058, 0.0), (0.05, -0.008)], mat("jhm", "DDF1FB", 0.15), seg=32, closed=True)
jug_h.parent = jug_s
jug_h.location = (0.085, 0, 0.105)
jug_h.rotation_euler = (math.pi / 2, 0, 0)
mini_j = B.link(bpy.data.objects.new("minij", mini0.data))
mini_j.location = Vector((JUG_X - 0.015, -0.06, 0.905 + 0.075))
mini_j.rotation_euler = (math.radians(-8), 0, math.radians(-14))
mini_j.scale = (1.05, 1.05, 1.05)

GLASS = Vector((DROP_X, -0.08, 0.905))
lathe("glass", [(0.0, 0.0), (0.03, 0.0), (0.033, 0.006), (0.04, 0.095), (0.042, 0.095)], shell_m, at=GLASS)
drop_w = lathe("gwat", [(0.0, 0.0), (0.0295, 0.0), (0.0325, 0.006), (0.0375, 0.08), (0.0, 0.08)], water_m, at=GLASS + Vector((0, 0, 0.001)))
DROPPER = B.link(bpy.data.objects.new("dropper", None))
DROPPER.location = GLASS + Vector((0, 0, 0.13))
tube = lathe("dtube", [(0.0, 0.0), (0.0035, 0.0), (0.0085, 0.03), (0.0085, 0.12), (0.0, 0.12)], shell_m, seg=24)
tube.parent = DROPPER
bulb = lathe("dbulb", [(0.0, 0.0), (0.012, 0.0), (0.021, 0.022), (0.019, 0.05), (0.0, 0.058)], coral, seg=32)
bulb.parent = DROPPER
bulb.location = (0, 0, 0.118)
DRIPS = []
drip_mesh = lathe("drip0", [(0.0, -0.008), (0.005, -0.004), (0.0045, 0.002), (0.0, 0.009)], water_m, seg=16)
DRIPS.append(drip_mesh)
for i in range(2):
    DRIPS.append(B.link(bpy.data.objects.new(f"drip{i + 1}", drip_mesh.data)))
mini_n = B.link(bpy.data.objects.new("minin", mini0.data))
mini_n.location = GLASS + Vector((0.09, 0.0, 0.052))
mini_n.rotation_euler = (math.radians(-8), 0, math.radians(-10))
mini_n.scale = (0.72, 0.72, 0.72)

stand_m = mat("stand", "E7C9A1", 0.5)
rbox("spst", SPOON_X - 0.17, SPOON_X + 0.17, -0.14, 0.02, 0.905, 0.925, stand_m, bev=0.006)
steel = B.material("steel", (0.78, 0.8, 0.82), metallic=1.0, rough=0.28)
SPOON_WAT = []
for i, sx in enumerate((-0.078, 0.078)):
    root = B.link(bpy.data.objects.new(f"spoon{i}", None))
    root.location = Vector((SPOON_X + sx, -0.05, 0.99))
    root.rotation_euler = (math.radians(58), 0, 0)
    lathe(f"spb{i}", [(0.0, -0.016), (0.022, -0.012), (0.038, 0.0), (0.0405, 0.004), (0.0, 0.004)], steel).parent = root
    root.children[-1].scale = (1, 1.3, 1)
    wt_ = lathe(f"spw{i}", [(0.0, 0.0048), (0.031, 0.0048)], water_m, sy=1.3)
    wt_.parent = root
    h_ = rbox(f"sph{i}", -0.008, 0.008, 0.048, 0.20, -0.002, 0.006, steel, bev=0.003)
    h_.parent = root

# ------------------------------------------------------------------ the water loop set

LP = Vector((-20, 0, 0))
rbox("lwall", -2.5, 2.5, 0.42, 0.55, 0, 3.2, mat("lav", "D3CBEA", 0.75), bev=0, off=LP)
rbox("lfloor", -2.5, 2.5, -2, 0.44, -0.1, 0.0, mat("lfl", "ECE1D1", 0.6), bev=0, off=LP)
rack_m = mat("rack", "39424F", 0.45)
for k, x in enumerate((-0.17, 0.17)):
    rbox(f"rack{k}", x - 0.15, x + 0.15, 0.0, 0.34, 0.02, 0.98, rack_m, bev=0.014, off=LP)
    for r_ in range(10):
        z = 0.10 + r_ * 0.085
        rbox(f"bl{k}{r_}", x - 0.13, x + 0.13, -0.008, 0.01, z, z + 0.058, mat(f"bl{k}{r_}", "4B5664", 0.4), bev=0.004, off=LP)
led_m = B.material("led", (0.1, 0.9, 0.5), rough=0.3)
B.bsdf(led_m).inputs["Emission Color"].default_value = (0.1, 1.0, 0.55, 1)
B.bsdf(led_m).inputs["Emission Strength"].default_value = 4.0
leds = []
for k, x in enumerate((-0.17, 0.17)):
    for r_ in range(10):
        z = 0.129 + r_ * 0.085
        leds.append(B.box(LP.x + x + 0.09, LP.x + x + 0.11, -0.0115, -0.006, LP.z + z - 0.006, LP.z + z + 0.006))
B.mesh_from("leds", B.many(*leds), [led_m])
pipe_m = mat("pipe", "58AEE2", 0.25)
PX, PZ0, PZ1, PY = 0.40, 0.14, 1.09, -0.06
for nm, a, b in (("pl", (-PX, PZ0), (-PX, PZ1)), ("pr", (PX, PZ0), (PX, PZ1))):
    ob = B.mesh_from(nm, B.cyl_z(0.028, PZ0, PZ1, a[0], PY, 24), [pipe_m])
    ob.location = LP
    B.smooth(ob)
for nm, z in (("pb", PZ0), ("pt", PZ1)):
    ob = B.mesh_from(nm, B.cyl_x(0.028, -PX, PX, 24), [pipe_m])
    ob.location = LP + Vector((0, PY, z))
    B.smooth(ob)
ball_mesh = None
for sx in (-PX, PX):
    for z in (PZ0, PZ1):
        o_ = lathe(f"elb{sx}{z}", [(0.0, -0.037), (0.027, -0.027), (0.037, 0.0), (0.027, 0.027), (0.0, 0.037)], pipe_m, seg=24, at=LP + Vector((sx, PY, z)))
rbox("pump", -0.09 - PX, 0.09 - PX, PY - 0.06, PY + 0.06, 0.40, 0.62, mat("pump", "F2A98C", 0.4), bev=0.02, off=LP)
FLOW = []
flow_m = mat("flow", "E7F7FF", 0.2)
flow0 = lathe("flow0", [(0.0, -0.017), (0.015, -0.01), (0.017, 0.0), (0.015, 0.01), (0.0, 0.017)], flow_m, seg=16)
for i in range(22):
    FLOW.append((flow0 if i == 0 else B.link(bpy.data.objects.new(f"flow{i}", flow0.data)), i / 22))

SIGN3, s3h, s3b, s3f = sign("s3", LP + Vector((0.0, 0.40, 1.415)), 0.42, 0.26, "", "", "", s=1.0)
GAUGE_AT = LP + Vector((0.95, 0.39, 0.92))
gg = B.mesh_from("gg", B.cyl_x(0.145, 0.0, 0.03, 64), [mat("gg", "FBF8F1", 0.95)])
gg.location = GAUGE_AT
gg.rotation_euler = (0, 0, math.pi / 2)
B.smooth(gg)
rim2 = lathe("gr", [(0.14, 0.0), (0.158, 0.0), (0.158, 0.04), (0.14, 0.04)], mat("grm", "39424F", 0.4), seg=64, closed=True, at=GAUGE_AT + Vector((0, 0.02, 0)))
rim2.rotation_euler = (math.pi / 2, 0, 0)
needle = B.link(bpy.data.objects.new("needle", None))
needle.location = GAUGE_AT + Vector((0, -0.012, 0))
nd = rbox("nd", -0.007, 0.007, -0.002, 0.002, 0.0, 0.118, red_x, bev=0.0)
nd.parent = needle
gh = lathe("gh", [(0.0, -0.01), (0.015, -0.01), (0.015, 0.01), (0.0, 0.01)], rack_m, seg=20, at=GAUGE_AT + Vector((0, -0.016, 0)))
gh.rotation_euler = (math.pi / 2, 0, 0)
for k in range(9):
    a = math.radians(-120 + k * 30)
    t_ = rbox(f"gt{k}", -0.004, 0.004, -0.001, 0.001, 0.104, 0.128, red_x if k > 5 else rack_m, bev=0.0)
    t_.location = GAUGE_AT + Vector((0, -0.003, 0))
    t_.rotation_euler = (0, a, 0)
text("gtx", "POWER", 0.04, "39424F", GAUGE_AT + Vector((0, -0.003, -0.07)), glow=1.0)

# ------------------------------------------------------------------ the outdoor diorama

O = Vector((60, 0, 0))
rbox("gnd", -220, 220, -200, 220, -1, 0, mat("gnd", "A8CF92", 0.85), bev=0, off=O)
rbox("sky", -500, 500, 300, 310, -5, 400, mat("skym", "BEE3F3", 1.0), bev=0, off=O)
road = rbox("road", -220, 220, -19, -9, 0.0, 0.04, mat("rd", "8E939B", 0.8), bev=0, off=O)
DC_Z = 26.0
dc_m = mat("dc", "DDE1E6", 0.6)
rbox("dcb", -32, 32, 10, 54, 0, DC_Z, dc_m, bev=0.25, off=O)
louv = []
for z in range(3, 24, 4):
    louv.append(B.box(O.x - 30.5, O.x + 30.5, 9.7, 10.2, z, z + 1.7))
B.mesh_from("louv", B.many(*louv), [mat("louv", "9FA9B4", 0.55)])
rbox("door", -3, 3, 9.8, 10.3, 0, 3.4, rack_m, bev=0.05, off=O)
unit_m = mat("unit", "EDEFF2", 0.5)
fan_m = mat("fan", "3F4650", 0.4)
STEAM = []
puff_m = mat("puff", "FBFBFA", 0.9)
puff0 = lathe("puff0", [(0.0, -1.0), (0.5, -0.87), (0.87, -0.5), (1.0, 0.0), (0.87, 0.5), (0.5, 0.87), (0.0, 1.0)], puff_m, seg=20)
puff0.location = AWAY

def steam(at, n, rise, spread, size, life, shots):
    for i in range(n):
        ob = B.link(bpy.data.objects.new(f"st{len(STEAM)}", puff0.data))
        ob.location = AWAY
        STEAM.append((ob, Vector(at), rng.random(), rng.uniform(-1, 1), rng.uniform(-0.6, 0.6), rise, spread, size, life, shots))

for x in (-3.3, 3.3, -11, 11, -19, 19):
    y_ = 29.0
    rbox(f"unit{x}", x - 2.2, x + 2.2, y_ - 2.2, y_ + 2.2, DC_Z, DC_Z + 2.6, unit_m, bev=0.12, off=O)
    f_ = B.mesh_from(f"fanb{x}", B.cyl_z(1.7, DC_Z + 2.6, DC_Z + 2.72, x, y_, 32), [fan_m])
    f_.location = O
    steam(O + Vector((x, y_, DC_Z + 3.0)), 12, 12.0, 0.7, 0.8, 2.6, ("tower", "dc", "town"))

def cooling(x, y, R, h, shots):
    n = 18
    prof = [(0.0, 0.0)]
    for i in range(n + 1):
        u = i / n
        prof.append((R * (0.60 + 0.45 * (u - 0.72) ** 2 / 0.72 ** 2 + 0.0), h * u))
    lathe(f"ct{x}", prof, mat(f"ct{x}", "D8D5CC", 0.8), seg=48, at=O + Vector((x, y, 0)))
    lathe(f"ctr{x}", [(R * 0.665, h * 0.72), (R * 0.668, h * 0.74), (R * 0.675, h * 0.76)], mat(f"ctr{x}", "E88F73", 0.7), seg=48, at=O + Vector((x, y, 0.02)))
    steam(O + Vector((x, y, h + 2)), 26, 34.0, 8.0, 7.5, 3.4, shots)

cooling(77, 72, 11, 40, ("plant",))
cooling(103, 76, 11, 40, ("plant",))
rbox("hall", 82, 98, 44, 60, 0, 10, mat("hall", "CFC6BB", 0.7), bev=0.2, off=O)

SIGN4, s4h, s4b, s4f = sign("s4", O + Vector((0, 34, 33)), 0.42, 0.26, "", "", "", s=1.0)
post_m = mat("post", "5B6471", 0.5)
for x in (-0.14, 0.14):
    pb = rbox(f"p4{x}", x - 0.008, x + 0.008, 0.002, 0.018, -1.0, -0.12, post_m, bev=0.0)
    pb.parent = SIGN4

def house(x, y, w, d, h, col, roof):
    rbox(f"hw{x}{y}", x - w / 2, x + w / 2, y - d / 2, y + d / 2, 0, h, mat(f"hw{x}{y}", col, 0.7), bev=0.08, off=O)
    r_h = w * 0.42
    def wedge(bm):
        cx, cy = O.x + x, O.y + y
        ov = 0.3
        v = [bm.verts.new(p) for p in ((cx - w / 2 - ov, cy - d / 2 - ov, h), (cx + w / 2 + ov, cy - d / 2 - ov, h), (cx, cy - d / 2 - ov, h + r_h),
                                        (cx - w / 2 - ov, cy + d / 2 + ov, h), (cx + w / 2 + ov, cy + d / 2 + ov, h), (cx, cy + d / 2 + ov, h + r_h))]
        for f in ((0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)):
            bm.faces.new([v[i] for i in f])
    B.mesh_from(f"hr{x}{y}", wedge, [mat(f"hr{x}{y}", roof, 0.7)])
    rbox(f"hd{x}{y}", x - 0.6, x + 0.6, y - d / 2 - 0.1, y - d / 2 + 0.05, 0, 2.3, mat(f"hd{x}{y}", "7B5A3C", 0.6), bev=0.03, off=O)
    win = mat(f"hwn{x}{y}", "CDE9F6", 0.15)
    for sx in (-0.28, 0.28):
        rbox(f"hn{x}{y}{sx}", x + sx * w - 0.55, x + sx * w + 0.55, y - d / 2 - 0.08, y - d / 2 + 0.05, h * 0.45, h * 0.45 + 1.2, win, bev=0.03, off=O)

COLS = (("F5D9B8", "D9694F"), ("CFE4D2", "8C6E5A"), ("F3C8C0", "6F7F92"), ("FBEFC8", "C76A4A"), ("C9DCEF", "7A5F52"), ("EFD8EC", "5F7D6B"))
hr = random.Random(9)
spots = [(-15, -24), (-6, -26), (4, -24.5), (14, -26), (-20, -3), (-10.5, -2), (-29, -4), (-29, -24), (28, -25)]
for i, (x, y) in enumerate(spots):
    c1_, c2_ = COLS[i % len(COLS)]
    house(x, y, hr.uniform(6.4, 7.8), hr.uniform(6, 7), hr.uniform(3.6, 4.8), c1_, c2_)
trunk_m, leaf_m = mat("trk", "8A6A4B", 0.8), mat("leaf", "6FAE78", 0.8)
for i, (x, y) in enumerate(((-24.5, -28), (-11, -30), (9.5, -29), (23, -28), (-15, -7), (0, -29), (-33, -6), (33, -7))):
    lathe(f"trk{i}", [(0.0, 0.0), (0.35, 0.0), (0.3, 2.0), (0.0, 2.0)], trunk_m, seg=12, at=O + Vector((x, y, 0)))
    lathe(f"lf{i}", [(0.0, 1.6), (2.0, 1.8), (2.3, 3.2), (1.5, 5.0), (0.0, 6.3)], leaf_m, seg=20, at=O + Vector((x, y, 0)))
# the town's water tower, asking
TW = O + Vector((-3.0, -6.0, 0))
tower_m = mat("wt", "E9EEF2", 0.5)
lathe("wtt", [(0.0, 12.6), (3.6, 13.4), (4.4, 15.2), (4.4, 18.2), (3.2, 19.8), (0.0, 20.8)], tower_m, seg=48, at=TW)
for sx, sy in ((-2.6, -2.6), (2.6, -2.6), (-2.6, 2.6), (2.6, 2.6)):
    leg_ = B.mesh_from(f"wl{sx}{sy}", B.cyl_z(0.25, 0, 13.2, TW.x + sx, TW.y + sy, 12), [fan_m])
    B.smooth(leg_)
lathe("wtp", [(0.0, 0.0), (0.7, 0.0), (0.7, 13.0), (0.0, 13.0)], fan_m, seg=16, at=TW)
tq = text("wtq", "?", 4.4, "E5392F", TW + Vector((0, -4.42, 16.6)), glow=1.0)

SIGNS = {"s1": (SIGN1, s1h, s1b, s1f), "s3": (SIGN3, s3h, s3b, s3f), "s4": (SIGN4, s4h, s4b, s4f)}

def put_sign(key, at, head, big, foot, scale=None):
    root, h_, b_, f_ = SIGNS[key]
    root.location = at
    if scale:
        root.scale = (scale, scale, scale)
    for ob, s, size in ((h_, head, 0.042), (b_, big, 0.105), (f_, foot, 0.036)):
        if ob.data.body != s:
            ob.data.body = s
            ob.data.size = min(size, 0.37 / (max(1, len(s)) * 0.6))    # long lines shrink to fit the board

# ------------------------------------------------------------------ light, world, camera

w = bpy.data.worlds.new("w")
scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (*hexc("E8EEF2"), 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.72
B.sun("key", -62, 56, 2.1, color=hexc("FFF4E4"), angle_deg=14)
cam = B.camera(lens=35, fstop=14.0)
cam.data.clip_start, cam.data.clip_end = 0.02, 1500.0

# ------------------------------------------------------------------ state

def shot_at(t):
    k = max([0] + [i for i, (s, _) in enumerate(SHOTS) if t >= s])
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    return SHOTS[k][1], SHOTS[k][0], t1

def counter_cam(x, u, wig, y0=-0.93, push=0.07):
    """The same framing all along the counter: sign up top, props on the counter, the camera creeping in."""
    cam_at = Vector((x - 0.01, y0 + push * smooth01(u), 1.20)) + wig
    B.aim(cam, cam_at, (x, 0.1, 1.135))
    cam.data.dof.focus_distance = -cam_at.y - 0.05

def flow_at(k):
    """A point k (0 to 1) round the rectangular loop."""
    w_, h_ = 2 * PX, PZ1 - PZ0
    d = k * 2 * (w_ + h_)
    if d < w_:
        return LP + Vector((-PX + d, PY, PZ0))
    d -= w_
    if d < h_:
        return LP + Vector((PX, PY, PZ0 + d))
    d -= h_
    if d < w_:
        return LP + Vector((PX - d, PY, PZ1))
    return LP + Vector((-PX, PY, PZ1 - (d - w_)))

def apply_state(t):
    # motion blur asks for times between frames; a whole frame stays in one shot, or the cut smears into a white ghost frame
    name, s0, s1 = shot_at(round(t * FPS) / FPS)
    u = (t - s0) / max(0.01, s1 - s0)
    wig = Vector((math.sin(t * 1.3) * 0.004, 0, math.sin(t * 1.7) * 0.003))
    set_text_color(s1b, "FFFFFF")
    XROOT.scale = (0, 0, 0)
    SIGN1.rotation_euler = (0, 0, 0)
    if name in ("hook", "hook_out"):
        tn = EV["not"] if name == "hook" else EV["not2"]
        hit = t >= tn
        put_sign("s1", Vector((-0.005, 0.27, SGN_Z)), "ONE AI PICTURE", "500 mL", "PEOPLE SAY")
        counter_cam(0.0, 1 - u if name == "hook_out" else u, wig)
        # the level drops while the picture drinks, and jumps back when the sign is crossed out
        lvl = 1.0 - 0.34 * min(1.0, (t - s0) / max(0.1, tn - s0))
        if hit:
            lvl = lvl + (1.0 - lvl) * back_out((t - tn) / 0.28)
        water.scale = (1, 1, lvl)
        k = (t - tn) if hit else -1
        s = back_out(k / 0.16) if hit else 0.0
        if name == "hook_out":
            s *= 1 - smooth01((t - (s1 - 0.32)) / 0.3)     # gone by the last frame, so it loops into the first
        XROOT.location = SIGN1.location + Vector((0, -0.03, -0.005))
        XROOT.scale = (s, s, s)
        set_text_color(s1b, "FF8A7E" if hit and s > 0.5 else "FFFFFF")
        # the frame slurps until it's caught, then jumps
        frame.location = PIC_AT + Vector((0, 0, 0.02 * math.exp(-k * 7) * abs(math.sin(k * 15)) if hit else 0.0025 * abs(math.sin(t * 13))))
        SIGN1.rotation_euler = (0, 0.05 * math.exp(-k * 8) * math.sin(k * 30) if hit else 0.0, 0)
    elif name == "paper":
        counter_cam(PAPER_X, u, wig)
        put_sign("s1", Vector((PAPER_X - 0.005, 0.27, SGN_Z)), "THE PAPER", "2023", "ABOUT TEXT ANSWERS")
    elif name == "nopic":
        counter_cam(PAPER_X - 0.03, u, wig, y0=-0.85, push=0.04)
        put_sign("s1", Vector((PAPER_X - 0.035, 0.27, SGN_Z)), "NUMBER FOR PICTURES", "NONE", "IN THIS PAPER")
    elif name == "cups":
        counter_cam(CUPS_X, u, wig)
        c0_, c1_ = EV["cups0"], EV["cups1"]
        v = max(0.0, min(1.0, (t - c0_) / max(0.1, c1_ - c0_)))
        shown = 10 + int(round(40 * v)) if t >= c0_ else 0
        for i, ob in enumerate(CUPS):
            due = c0_ + i * 0.022 if i < 10 else c0_ + (c1_ - c0_) * (i - 10) / 40
            s = 0.72 * back_out((t - due) / 0.14) if t >= due else 0.0
            ob.scale = (s, s, s)
        water2.scale = (1, 1, 1.0 - 0.72 * v)
        put_sign("s1", Vector((CUPS_X - 0.005, 0.27, SGN_Z)), "ONE BOTTLE FOR", "10 TO 50" if v >= 1 else (str(shown) if shown else "..."), "ANSWERS")
    elif name == "measure":
        counter_cam(JUG_X, u, wig)
        put_sign("s1", Vector((JUG_X - 0.005, 0.27, SGN_Z)), "ONE AI PICTURE", "? mL", "NOBODY HAS MEASURED IT")
    elif name in ("drops", "nothing"):
        counter_cam(DROP_X, u, wig, y0=-0.86 if name == "drops" else -0.8, push=0.06)
        d0, d1 = EV["drops0"], EV["drops1"]
        v = max(0.0, min(1.0, (t - d0) / max(0.1, d1 - d0)))
        drop_w.scale = (1, 1, max(0.02, v))
        DROPPER.location = (GLASS + Vector((0, 0, 0.13))) if name == "drops" else AWAY
        bulb.scale = (1 - 0.14 * max(0, math.sin(t * 12)), 1 - 0.14 * max(0, math.sin(t * 12)), 1 + 0.08 * max(0, math.sin(t * 12)))
        for i, ob in enumerate(DRIPS):
            k = ((t * 2.4 + i / 3) % 1)
            ob.location = (GLASS + Vector((0, 0, 0.128 - 0.12 * k * k))) if name == "drops" and d0 <= t <= d1 else AWAY
        if name == "drops":
            mini_n.location = AWAY
            put_sign("s1", Vector((DROP_X - 0.005, 0.27, SGN_Z)), "OUR MATH", f"{int(round(12 * v))} mL", "POWER PLANT INCLUDED")
        else:
            mini_n.location = GLASS + Vector((0.09, 0.0, 0.052))
            put_sign("s1", Vector((DROP_X - 0.005, 0.27, SGN_Z)), "YOUR ONE PICTURE", "TINY", "ISN'T THE PROBLEM")
    elif name == "spoons":
        counter_cam(SPOON_X, u, wig)
        put_sign("s1", Vector((SPOON_X - 0.005, 0.27, SGN_Z)), "HIGHEST NUMBER WE FOUND", "29 mL", "TWO TABLESPOONS")
    elif name in ("loop", "micro", "meter"):
        for ob, ph in FLOW:
            ob.location = flow_at((ph + t * 0.14) % 1.0)
        if name == "loop":
            cam_at = LP + Vector((0.0, -2.02 + 0.13 * smooth01(u), 1.18)) + wig
            B.aim(cam, cam_at, LP + Vector((0, 0.1, 1.03)))
            cam.data.dof.focus_distance = -cam_at.y
            put_sign("s3", LP + Vector((0.0, 0.40, 1.49)), "YOUR FRIEND SAYS", "ALL OF IT", "CLOSED LOOP", scale=1.9)
            tw_ = EV["wrong"]
            if t >= tw_:
                k = t - tw_
                s = back_out(k / 0.16) * 1.9
                XROOT.location = SIGN3.location + Vector((0, -0.05, -0.01))
                XROOT.scale = (s, s, s)
        else:
            needle.rotation_euler = (0, math.radians(-120), 0)
            if name == "micro":
                cam_at = LP + Vector((0.32, -1.92 + 0.12 * smooth01(u), 1.18)) + wig
                B.aim(cam, cam_at, LP + Vector((0.32, 0.1, 1.03)))
                cam.data.dof.focus_distance = -cam_at.y
                put_sign("s3", LP + Vector((0.32, 0.40, 1.49)), "MICROSOFT'S NO-WATER SITES", "LATE 2027", "START COMING ONLINE", scale=1.9)
            else:
                cam_at = GAUGE_AT + Vector((0.0, -1.05 + 0.06 * smooth01(u), 0.16)) + wig
                B.aim(cam, cam_at, GAUGE_AT + Vector((0, 0, 0.12)))
                cam.data.dof.focus_distance = 1.0
                put_sign("s3", GAUGE_AT + Vector((0.0, 0.01, 0.31)), "THE TRADE", "MORE POWER", "FOR NO WATER", scale=1.0)
                te = EV["elec"]
                needle.rotation_euler = (0, math.radians(-105 + 150 * smooth01((t - s0) / max(0.1, te + 0.4 - s0)) + 2.0 * math.sin(t * 22)), 0)
    elif name == "tower":
        k_ = 16.0
        cam_at = O + Vector((0, 34 - 1.22 * k_ + 0.9 * smooth01(u), DC_Z + 0.295 * k_)) + wig * 8
        B.aim(cam, cam_at, O + Vector((0, 34 - 0.17 * k_, DC_Z + 0.23 * k_)))
        cam.data.dof.focus_distance = 16.0
        v = max(0.0, min(1.0, (t - EV["lose0"]) / max(0.1, EV["lose1"] - EV["lose0"])))
        put_sign("s4", O + Vector((0, 34, DC_Z + 0.45 * k_)), "GOOGLE LOSES" if t >= EV["lose0"] else "DATA CENTERS", f"{int(round(80 * v))}%" if t >= EV["lose0"] else "STEAM", "OF THE WATER IT TAKES IN" if t >= EV["lose0"] else "ON PURPOSE", scale=k_)
    elif name == "dc":
        cam_at = O + Vector((17, -22 + 2.0 * smooth01(u), 10.0)) + wig * 8
        B.aim(cam, cam_at, O + Vector((17, 10, 15.0)))
        cam.data.dof.focus_distance = 32.0
        put_sign("s4", O + Vector((17, 9.0, 13.0)), "AT THE DATA CENTER", "13%", "OF THE WATER", scale=22.0)
    elif name == "plant":
        cam_at = O + Vector((90, -30 + 4.0 * smooth01(u), 11.0)) + wig * 8
        B.aim(cam, cam_at, O + Vector((90, 60, 25.0)))
        cam.data.dof.focus_distance = 80.0
        put_sign("s4", O + Vector((90, 18, 10.0)), "AT THE POWER PLANT", "87%", "OF THE WATER", scale=28.0)
    elif name == "town":
        cam_at = O + Vector((2 - 4 * smooth01(u), -58 + 4.0 * smooth01(u), 7.0)) + wig * 8
        B.aim(cam, cam_at, O + Vector((0, 10, 15.0)))
        cam.data.dof.focus_distance = 62.0
        put_sign("s4", AWAY, "", "", "")
    elif name == "flush":
        shake = 0.0
        if t > EV["press"]:
            shake = 0.0035 * min(1.0, (t - EV["press"]) / 0.3)
        wob = Vector((math.sin(t * 37) * shake, 0, math.sin(t * 43) * shake))
        cam_at = BATH + Vector((0.0, -1.58 + 0.10 * smooth01(u), 1.28)) + wig + wob
        B.aim(cam, cam_at, BATH + Vector((0.0, 0.08, 0.80)))
        cam.data.dof.focus_distance = 1.6
        # the mitt comes in, presses, leaves
        press = EV["press"]
        into = smooth01((t - s0) / max(0.05, press - s0 - 0.04))
        away = smooth01((t - press - 0.45) / 0.4)
        down = smooth01((t - press + 0.05) / 0.1) * (1 - smooth01((t - press - 0.4) / 0.14))
        lever.rotation_euler = (0, math.radians(-26) * down, 0)
        tip = LEVER_AT + Vector((-0.085, 0, 0.042 - 0.046 * down))
        mitt.location = tip + Vector((-0.42 * (1 - into) - 0.5 * away, 0, 0.12 * (1 - into)))
        # whirlpool
        since = max(0.0, t - press - 0.15)
        swirl.scale = (1, 1, 0.12 + 0.88 * smooth01(since / 0.8))
        swirl_map.inputs["Rotation"].default_value = (0, 0, -(1.3 * since ** 2 if since < 1.5 else 2.9 + 3.9 * (since - 1.5)))
        s2f.data.body = f"= {count_at(t)} AI PICTURES"
    for ob, at, ph, jx, jy, rise, spread, size, life, shots_ in STEAM:
        if name not in shots_:
            ob.location = AWAY
            continue
        k = (t / life + ph) % 1.0
        ob.location = at + Vector((spread * jx * (0.4 + k * 1.6) + 0.9 * spread * k * k, spread * jy * k, rise * k))
        s = size * (0.45 + 1.1 * k) * min(1.0, k / 0.08) * min(1.0, (1 - k) / 0.14)
        ob.scale = (s, s, s)
    mini_np.location = MINI_NP_AT if name == "nopic" else AWAY
    mini_np.rotation_euler = (math.radians(-6), 0, math.radians(8 + 3 * math.sin(t * 2)))
    for ob, t_i, jit, a0, spin, rot0, sc_ in MINIS:
        k = (t - t_i) / LIFE
        if name != "flush" or not 0 <= k <= 1:
            ob.location = AWAY
            continue
        rim = BATH + Vector((0, -0.03, 0.47))
        # thrown in from just below the camera for the first 30%, then round the bowl and down the middle
        if k < 0.3:
            v = k / 0.3
            st = BATH + Vector((jit * 2.2, -0.62, 1.0))
            p = st.lerp(rim, v) + Vector((0, 0, 0.14 * math.sin(math.pi * v)))
            r, ang = 0.13 * v, a0 + spin * k
            p += Vector((r * math.cos(ang), r * SY * math.sin(ang), 0))
            s = sc_ * 0.72
        else:
            v = (k - 0.3) / 0.7
            r = 0.13 * (1 - v) ** 1.3
            ang = a0 + spin * 0.3 + 9.0 * v ** 0.75
            p = rim + Vector((r * math.cos(ang), r * SY * math.sin(ang), -0.30 * v ** 1.5))
            s = sc_ * (0.72 - 0.5 * v)
        ob.location = p
        ob.rotation_euler = (rot0.x + spin * k, rot0.y + spin * 0.7 * k, ang)
        ob.scale = (s, s, s)

B.render_settings(FPS, samples=int(os.environ.get("WATER_SAMPLES", "24")), motion_blur=0.3)
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1 + scn.frame_subframe) / FPS)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
