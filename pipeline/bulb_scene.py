"""Product-studio look test: Poly Haven's CC0 LED bulb in three shots, built to compare against @speedy_devv's frames.

1. The bulb hangs lit from a brass socket over a black walnut desk in a dark room, camera pushing in.
2. Cutaway: the near half of the shell is clipped away, showing the LED board and the driver inside the heatsink.
3. Magnified LED package, sectioned: the blue chip at the bottom of a cup of yellow phosphor; blue photons leave the
   chip and come out of the phosphor warm white.

blender -b --factory-startup -P bulb_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Writes out_dir/anchors.json (screen points for labels, every frame).
"""
import json, math, os, random, sys
import bpy
from mathutils import Vector, Euler
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
SHOTS = T.get("shots", [0.0, 1.65, 3.3])                 # start time of each shot
os.makedirs(OUT, exist_ok=True)
B.clear_scene()
scene = B.scene
rng = random.Random(3)
AWAY = Vector((0, 0, -1.0e4))
WARM = (1.0, 0.80, 0.58)
BLUE = (0.03, 0.12, 1.0)

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

# ------------------------------------------------------------------ world: studio HDRI for reflections, dark to camera

def world():
    w = bpy.data.worlds.new("world")
    scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(A.hdri_path("brown_photostudio_02"))
    hdr = nt.nodes.new("ShaderNodeBackground"); hdr.inputs[1].default_value = 0.22
    dark = nt.nodes.new("ShaderNodeBackground"); dark.inputs[0].default_value = (0.004, 0.004, 0.006, 1); dark.inputs[1].default_value = 1.0
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(env.outputs[0], hdr.inputs[0])
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(hdr.outputs[0], mix.inputs[1])
    nt.links.new(dark.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
world()

# ------------------------------------------------------------------ materials

def pbr_texture(name, asset, tile):
    """Poly Haven texture set on a Principled BSDF, tiled every `tile` metres in object XY."""
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
    b.inputs["Coat Weight"].default_value = 0.25          # a satin lacquer on the desk top
    b.inputs["Coat Roughness"].default_value = 0.18
    return m

def plain(name, color, rough=0.4, metal=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
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

def add_clip(m, axis="X", above=0.0, key="cut"):
    """Make the material transparent where its object coordinate on `axis` is above `above`, scaled by a Value node
    named `key` (0 = whole, 1 = cut). The cutaway trick: no boolean on the scanned mesh, so nothing tears."""
    nt = m.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    src = out.inputs[0].links[0].from_socket
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    gt = nt.nodes.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = above
    val = nt.nodes.new("ShaderNodeValue"); val.name = key; val.outputs[0].default_value = 0.0
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs[{"X": 0, "Y": 1, "Z": 2}[axis]], gt.inputs[0])
    nt.links.new(gt.outputs[0], mul.inputs[0])
    nt.links.new(val.outputs[0], mul.inputs[1])
    nt.links.new(mul.outputs[0], mix.inputs[0])
    nt.links.new(src, mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    m.use_transparent_shadow = True
    return val

def setv(m, key, v):
    m.node_tree.nodes[key].outputs[0].default_value = v

# ------------------------------------------------------------------ shot 1 and 2 set: hanging bulb over a walnut desk

HANG = Vector((0.0, 0.0, 0.46))
bpy.ops.import_scene.gltf(filepath=A.model_path("lightbulb_led"))
bulb = bpy.data.objects["lightbulb_led"]
bulb.location = HANG
bulb.rotation_mode = "XYZ"                                # the glTF importer leaves objects in quaternion mode
bulb.rotation_euler = (math.pi, 0, 0)                     # base up, dome down
BULB_M = bulb.data.materials[0]
# the dome (object z above the seam at 0.0485) glows; the value node 'glow' sets how much
nt = BULB_M.node_tree
bs = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
gt = nt.nodes.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = 0.0485
gv = nt.nodes.new("ShaderNodeValue"); gv.name = "glow"
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
nt.links.new(tc.outputs["Object"], sep.inputs[0]); nt.links.new(sep.outputs[2], gt.inputs[0])
nt.links.new(gt.outputs[0], mul.inputs[0]); nt.links.new(gv.outputs[0], mul.inputs[1])
bs.inputs["Emission Color"].default_value = (*WARM, 1)
nt.links.new(mul.outputs[0], bs.inputs["Emission Strength"])
add_clip(BULB_M, "X", 0.0, "cut")

def part(name, build, mat, parent=bulb, loc=(0, 0, 0), smooth=False):
    ob = B.mesh_from(name, build, [mat])
    if smooth:
        B.smooth(ob)
    ob.parent = parent
    ob.location = loc
    return ob

def cyl(r, z0, z1, x=0.0, y=0.0, seg=48):
    return B.cyl_z(r, z0, z1, x, y, seg=seg)

# inside the bulb, in the bulb's own coordinates (z up from the screw tip at -0.0157 to the dome top at 0.0846)
pcb_m = plain("pcb_white", (0.86, 0.86, 0.84), rough=0.32, coat=0.4)
led_body_m = plain("led_body", (0.93, 0.93, 0.92), rough=0.22)
phos_m = bpy.data.materials.new("phosphor")
phos_m.use_nodes = True
pb = phos_m.node_tree.nodes["Principled BSDF"]
pb.inputs["Base Color"].default_value = (1.0, 0.72, 0.06, 1)
pb.inputs["Roughness"].default_value = 0.35
pb.inputs["Emission Color"].default_value = (1.0, 0.86, 0.62, 1)
pb.inputs["Emission Strength"].default_value = 0.0
alu_m = plain("aluminium", (0.80, 0.80, 0.82), rough=0.28, metal=1.0)
green_m = plain("driver_pcb", (0.03, 0.22, 0.11), rough=0.35, coat=0.5)
cap_m = plain("cap_sleeve", (0.04, 0.07, 0.20), rough=0.3, coat=0.6)
cap_top_m = plain("cap_top", (0.75, 0.76, 0.78), rough=0.25, metal=1.0)
ic_m = plain("ic_black", (0.02, 0.02, 0.022), rough=0.45)
coil_m = plain("copper", (0.95, 0.52, 0.30), rough=0.25, metal=1.0)
wire_r = plain("wire_red", (0.55, 0.03, 0.02), rough=0.4)
wire_k = plain("wire_black", (0.02, 0.02, 0.02), rough=0.4)

part("spreader", cyl(0.0268, 0.0470, 0.0488, seg=96), alu_m)
part("pcb", cyl(0.0255, 0.0488, 0.0500, seg=96), pcb_m)
LEDS = []
for i, (r, n) in enumerate(((0.0175, 10), (0.0075, 4))):
    for k in range(n):
        a = 2 * math.pi * (k + 0.5 * i) / n
        x, y = r * math.cos(a), r * math.sin(a)
        body = part(f"led_{i}_{k}", B.box(-0.00175, 0.00175, -0.0014, 0.0014, 0.0500, 0.0508), led_body_m, loc=(x, y, 0))
        body.rotation_euler = (0, 0, a)
        ph = part(f"ph_{i}_{k}", B.box(-0.0014, 0.0014, -0.0011, 0.0011, 0.05065, 0.05085), phos_m, loc=(x, y, 0))
        ph.rotation_euler = (0, 0, a)
        LEDS.append(ph)
# driver: a small board standing up in the heatsink neck, parts facing the cut
part("driver", B.box(-0.0045, -0.0031, -0.0095, 0.0095, 0.0120, 0.0440), green_m)
part("cap", cyl(0.0042, 0.0230, 0.0400, x=0.0012, y=0.0035), cap_m, smooth=True)
part("cap_top", cyl(0.0042, 0.0400, 0.0404, x=0.0012, y=0.0035), cap_top_m)
part("ic", B.box(-0.0031, -0.0012, -0.0070, -0.0020, 0.0300, 0.0355), ic_m)
part("coil", cyl(0.0030, 0.0150, 0.0205, x=-0.0005, y=-0.0040), coil_m, smooth=True)
part("res", B.box(-0.0031, -0.0016, 0.0010, 0.0060, 0.0165, 0.0185), plain("resistor", (0.55, 0.42, 0.30), 0.5))
part("w_red", cyl(0.0006, 0.0440, 0.0475, x=-0.0040, y=0.0040, seg=12), wire_r)
part("w_blk", cyl(0.0006, 0.0440, 0.0475, x=-0.0040, y=-0.0040, seg=12), wire_k)
INSIDE = [o for o in bulb.children]

# brass socket, cloth cord, desk
brass_m = plain("brass", (0.86, 0.62, 0.32), rough=0.28, metal=1.0)
socket = B.mesh_from("socket", B.many(B.cyl_z(0.0175, HANG.z + 0.004, HANG.z + 0.052, 0, 0, seg=96),
                                     B.cyl_z(0.0110, HANG.z + 0.052, HANG.z + 0.066, 0, 0, seg=64)), [brass_m])
B.bevel(socket, 0.0012, 3)
B.smooth(socket)
cord = B.mesh_from("cord", B.cyl_z(0.0032, HANG.z + 0.066, 2.4, 0, 0, seg=24), [plain("cloth", (0.015, 0.014, 0.013), 0.85)])
desk = B.mesh_from("desk", B.box(-1.2, 1.2, -1.2, 1.2, -0.04, 0.0), [pbr_texture("walnut", "black_walnut_veneer_01", 0.9)])
# a few far-off warm practicals for bokeh behind the bulb
for i in range(5):
    p = Vector((rng.uniform(-1.6, 1.6), rng.uniform(2.6, 4.0), rng.uniform(0.25, 1.4)))
    B.mesh_from(f"bokeh{i}", B.cyl_z(0.035, p.z - 0.002, p.z + 0.002, p.x, p.y, seg=24),
                [glowing(f"bk{i}", (1.0, 0.62, 0.32), rng.uniform(3, 9))])

bulb_light = bpy.data.lights.new("bulb_light", "POINT")
bulb_light.energy, bulb_light.color, bulb_light.shadow_soft_size = 7.0, WARM, 0.028
bl = B.link(bpy.data.objects.new("bulb_light", bulb_light)); bl.location = HANG + Vector((0, 0, -0.065))
key1 = B.area("key1", (-0.55, -0.45, 0.75), HANG, 0.35, 6.0, color=(1.0, 0.86, 0.70))
rim1 = B.area("rim1", (0.45, 0.55, 0.65), HANG, 0.25, 9.0, color=(0.65, 0.75, 1.0))

# ------------------------------------------------------------------ shot 3 set: one LED package, magnified 100x

M = Vector((6.0, 0.0, 0.0))
macro_floor = B.mesh_from("macro_pcb", B.box(M.x - 2.0, M.x + 2.0, -2.0, 2.0, -0.012, 0.0), [plain("macro_pcb", (0.035, 0.036, 0.04), 0.78, coat=0.0)])
pkg_m = plain("pkg", (0.94, 0.94, 0.93), rough=0.2)
pad_m = plain("pad", (0.82, 0.83, 0.85), rough=0.2, metal=1.0)
add_clip(pkg_m, "X", 0.0, "cut")
mph_m = bpy.data.materials.new("macro_phosphor")
mph_m.use_nodes = True
mb = mph_m.node_tree.nodes["Principled BSDF"]
mb.inputs["Base Color"].default_value = (1.0, 0.70, 0.05, 1)
mb.inputs["Roughness"].default_value = 0.4
mb.inputs["Subsurface Weight"].default_value = 0.6
mb.inputs["Subsurface Radius"].default_value = (1.0, 0.8, 0.3)
mb.inputs["Subsurface Scale"].default_value = 0.05
mb.inputs["Emission Color"].default_value = (1.0, 0.70, 0.12, 1)
mb.inputs["Emission Strength"].default_value = 0.35
add_clip(mph_m, "X", 0.0, "cut")

pkg = B.mesh_from("pkg", B.box(-0.175, 0.175, -0.14, 0.14, 0.0, 0.08), [pkg_m])
B.boolean(pkg, [(B.box(-0.14, 0.14, -0.105, 0.105, 0.012, 0.10), "DIFFERENCE")])
B.bevel(pkg, 0.004, 2)
pkg.location = M
phos = B.mesh_from("phos", B.box(-0.1395, 0.1395, -0.1045, 0.1045, 0.0125, 0.074), [mph_m])
phos.location = M
die = B.mesh_from("die", B.box(-0.032, 0.032, -0.026, 0.026, 0.0125, 0.024), [glowing("die", BLUE, 18.0)])
die.location = M
for sx in (-1, 1):
    B.mesh_from(f"pad{sx}", B.box(sx * 0.06 - 0.05, sx * 0.06 + 0.05, -0.12, 0.12, 0.0, 0.004), [pad_m]).location = M + Vector((0, 0, -0.004))
gold_m = plain("gold", (1.0, 0.76, 0.35), rough=0.18, metal=1.0)
for sy, x1 in ((-1, -0.10), (1, 0.10)):
    pts = [Vector((0.0, sy * 0.012, 0.024)), Vector((x1 * 0.4, sy * 0.02, 0.055)), Vector((x1, sy * 0.03, 0.013))]
    cu = bpy.data.curves.new(f"bond{sy}", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.0018
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p; bp.handle_left_type = bp.handle_right_type = "AUTO"
    ob = B.link(bpy.data.objects.new(f"bond{sy}", cu)); ob.data.materials.append(gold_m); ob.location = M
die_light = bpy.data.lights.new("die_light", "POINT")
die_light.energy, die_light.color, die_light.shadow_soft_size = 5.0, BLUE, 0.03
dl = B.link(bpy.data.objects.new("die_light", die_light)); dl.location = M + Vector((0, 0, 0.03))
out_light = bpy.data.lights.new("out_light", "POINT")
out_light.energy, out_light.color, out_light.shadow_soft_size = 4.0, WARM, 0.1
ol = B.link(bpy.data.objects.new("out_light", out_light)); ol.location = M + Vector((0, 0, 0.16))
key3 = B.area("key3", M + Vector((-0.9, -0.7, 0.9)), M, 0.8, 9.0, color=(1.0, 0.88, 0.74))
rim3 = B.area("rim3", M + Vector((0.6, 0.9, 0.5)), M, 0.6, 10.0, color=(0.6, 0.72, 1.0))

# photons: small streaks that leave the chip blue and come out of the phosphor warm white
ph_mat = bpy.data.materials.new("photon")
ph_mat.use_nodes = True
pn = ph_mat.node_tree
pn.nodes.clear()
oi = pn.nodes.new("ShaderNodeObjectInfo")
em = pn.nodes.new("ShaderNodeEmission"); em.inputs[1].default_value = 8.0
po = pn.nodes.new("ShaderNodeOutputMaterial")
pn.links.new(oi.outputs["Color"], em.inputs[0]); pn.links.new(em.outputs[0], po.inputs[0])
PHOTONS = []
for i in range(30):
    ob = B.mesh_from(f"photon{i}", B.cyl_z(0.0016, -0.016, 0.016, 0, 0, seg=8), [ph_mat])
    ang, tilt = rng.uniform(0, 2 * math.pi), rng.uniform(0.05, 0.6)
    d = Vector((math.sin(tilt) * math.cos(ang), math.sin(tilt) * math.sin(ang), math.cos(tilt)))
    PHOTONS.append((ob, d, rng.uniform(0, 1.0)))

# ------------------------------------------------------------------ camera and lighting per shot

cam = B.camera(lens=50, fstop=2.0)
LIGHTS = {0: [bl, key1, rim1], 1: [key1, rim1], 2: [dl, ol, key3, rim3]}

def shot_of(t):
    return max([0] + [i for i, s in enumerate(SHOTS) if t >= s - 1e-6])    # motion blur samples before frame 1

def camera_for(k, u):
    """Camera position, target, lens and f-stop for shot k at progress u (0..1)."""
    if k == 0:
        loc = Vector((0.07, -0.44, 0.40)).lerp(Vector((0.04, -0.30, 0.425)), smooth01(u))
        return loc, HANG + Vector((0, 0, -0.03)), 50, 2.2
    if k == 1:
        loc = Vector((0.21, -0.10, 0.335)).lerp(Vector((0.175, -0.08, 0.35)), smooth01(u))      # from below: into the dome
        return loc, HANG + Vector((0, 0, -0.045)), 60, 4.0
    loc = M + Vector((0.78, -0.50, 0.36)).lerp(Vector((0.58, -0.36, 0.26)), smooth01(u))
    return loc, M + Vector((0, 0, 0.05)), 50, 3.2

def apply_state(t):
    k = shot_of(t)
    t0 = SHOTS[k]
    t1 = SHOTS[k + 1] if k + 1 < len(SHOTS) else DUR
    u = (t - t0) / max(1e-6, t1 - t0)
    loc, tg, lens, fstop = camera_for(k, u)
    cam.location = loc
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    cam.data.dof.aperture_fstop = fstop
    cam.data.dof.focus_distance = (tg - loc).length
    on = set(LIGHTS[k])
    for ob in (bl, key1, rim1, dl, ol, key3, rim3):
        ob.hide_render = ob not in on
    cut = 1.0 if k == 1 else 0.0
    setv(BULB_M, "cut", cut)
    setv(BULB_M, "glow", 28.0 if k == 0 else 0.0)
    pb.inputs["Emission Strength"].default_value = 14.0 if k == 0 else 1.6
    setv(pkg_m, "cut", 1.0)
    setv(mph_m, "cut", 1.0)
    for ob, d, phase in PHOTONS:
        if k != 2:
            ob.location = AWAY
            continue
        age = ((t - t0) * 1.3 + phase) % 1.0                     # each photon loops every ~0.77 s
        p = M + Vector((0, 0, 0.022)) + d * (age * 0.30)
        ob.location = p
        ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        inside = p.z < M.z + 0.074
        ob.color = (*BLUE, 1) if inside else (*WARM, 1)
        ob.scale = (1, 1, 1) if age < 0.9 else (0.01, 0.01, 0.01)

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    pts = {
        "chips": lambda: LEDS[2].matrix_world @ Vector((0, 0, 0.0508)),
        "driver": lambda: bulb.matrix_world @ Vector((-0.002, 0.0035, 0.030)),
        "die": lambda: M + Vector((0.0, -0.02, 0.018)),
        "phosphor": lambda: M + Vector((0.0, -0.09, 0.066)),
    }
    out = {k: [] for k in pts}
    vl = bpy.context.view_layer
    for f in range(NF):
        apply_state(f / FPS)
        vl.update()
        for k, fn in pts.items():
            v = world_to_camera_view(scene, cam, fn())
            out[k].append([round(v.x * 1080, 1), round((1 - v.y) * 1920, 1)] if v.z > 0 and 0 <= v.x <= 1 and 0 <= v.y <= 1 else None)
    with open(os.path.join(OUT, "anchors.json"), "w") as fh:
        json.dump(out, fh)

B.render_settings(FPS, samples=int(os.environ.get("BULB_SAMPLES", "64")), motion_blur=0.35, look="AgX - Medium High Contrast")
scene.eevee.use_shadows = True

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1 + scn.frame_subframe) / FPS)

anchors()
apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
