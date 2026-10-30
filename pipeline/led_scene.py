"""Product-studio kit, LED bulb set: Poly Haven's CC0 LED bulb (and its incandescent bulb) hanging over a walnut desk
in a dark studio, an inside we model ourselves (spreader, LED ring, driver), and a magnified LED package. Shots are
named; the render script lists them with start times in timing.json:

  hang, hang_out       the lit bulb, pushing in / pulling back (hang_out ends on hang's first frame, for the loop)
  hang_white, hang_warm, hang_blue   quick cuts, dome glowing cool white, warm, then blue
  ring_lit, ring_blue  cutaway from below: the LED ring lit warm / glowing bare blue
  hot_board            same cutaway, the board glowing hot and the LEDs dimming
  fins                 outside close-up: heat flowing out along the heat-sink fins
  driver               cutaway of the neck: the power-supply board
  macro_fill, macro_photons, macro_top   the LED package magnified 100x and sectioned: phosphor filling the cup,
                       blue light in and yellow out, then from above with the light coming at the camera
  spectrum             the bulb far out of focus, a backdrop for the spectrum card
  versus               the incandescent bulb beside the LED bulb; the old one dies at timing["events"]["old_dies"]

blender -b --factory-startup -P led_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Writes out_dir/anchors.json (screen points for labels, every frame).
"""
import json, math, os, random, sys
import bpy
from mathutils import Vector
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
SHOTS = T["shots"]                                         # [[start_seconds, name], ...]
EV = T.get("events", {})
os.makedirs(OUT, exist_ok=True)
B.clear_scene()
scene = B.scene
rng = random.Random(3)
AWAY = Vector((0, 0, -1.0e4))
WARM = (1.0, 0.80, 0.58)
COOL = (0.86, 0.92, 1.0)
BLUE = (0.03, 0.12, 1.0)
YELLOW = (1.0, 0.78, 0.06)
HOT = (1.0, 0.22, 0.02)
TUNG = (1.0, 0.55, 0.22)

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

# ------------------------------------------------------------------ material helpers

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

def principled(m):
    return m.node_tree.nodes["Principled BSDF"]

def emit(m, color, strength):
    b = principled(m)
    b.inputs["Emission Color"].default_value = (*color, 1)
    b.inputs["Emission Strength"].default_value = strength

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
    b.inputs["Coat Weight"].default_value = 0.25
    b.inputs["Coat Roughness"].default_value = 0.18
    return m

def math_node(nt, op, a, b=None):
    """Math node fed by sockets or numbers; returns its output socket."""
    n = nt.nodes.new("ShaderNodeMath"); n.operation = op
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]

def value(nt, key, v=0.0):
    n = nt.nodes.new("ShaderNodeValue"); n.name = key; n.outputs[0].default_value = v
    return n.outputs[0]

def add_clip(m, axis="X", above=0.0, key="cut"):
    """Transparent where the object coordinate on `axis` is above `above`, scaled by Value node `key` (0 whole,
    1 cut): the cutaway without a boolean on the scanned mesh."""
    nt = m.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    src = out.inputs[0].links[0].from_socket
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    fac = math_node(nt, "MULTIPLY", math_node(nt, "GREATER_THAN", sep.outputs[{"X": 0, "Y": 1, "Z": 2}[axis]], above), value(nt, key))
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fac, mix.inputs[0])
    nt.links.new(src, mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    m.use_transparent_shadow = True

def setv(m, key, v):
    m.node_tree.nodes[key].outputs[0].default_value = v

def import_bulb(asset, loc):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=A.model_path(asset))
    ob = next(o for o in bpy.data.objects if o not in before)
    ob.location = loc
    ob.rotation_mode = "XYZ"                                # the glTF importer leaves objects in quaternion mode
    ob.rotation_euler = (math.pi, 0, 0)                     # base up, dome down
    return ob

def hang_hardware(name, top, brass_m, cloth_m):
    """Brass socket and cloth cord above a hanging bulb whose screw top sits at z = top."""
    s = B.mesh_from(name + "_socket", B.many(B.cyl_z(0.0175, top - 0.012, top + 0.036, 0, 0, seg=96),
                                             B.cyl_z(0.0110, top + 0.036, top + 0.050, 0, 0, seg=64)), [brass_m])
    B.bevel(s, 0.0012, 3)
    B.smooth(s)
    c = B.mesh_from(name + "_cord", B.cyl_z(0.0032, top + 0.050, 2.4, 0, 0, seg=24), [cloth_m])
    return [s, c]

# ------------------------------------------------------------------ the LED bulb, its inside, the desk

HANG = Vector((0.0, 0.0, 0.46))
bulb = import_bulb("lightbulb_led", HANG)
BULB_M = bulb.data.materials[0]
nt = BULB_M.node_tree
bs = nt.nodes["Principled BSDF"]
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Object"], sep.inputs[0])
z = sep.outputs[2]
dome = math_node(nt, "GREATER_THAN", z, 0.0485)                          # the frosted dome, above the seam
sink = math_node(nt, "MULTIPLY", math_node(nt, "GREATER_THAN", z, 0.013), math_node(nt, "SUBTRACT", 1.0, dome))
f = math_node(nt, "DIVIDE", math_node(nt, "SUBTRACT", 0.0485, z), 0.036)   # 0 at the board, 1 at the neck
wave = math_node(nt, "SINE", math_node(nt, "MULTIPLY", math_node(nt, "SUBTRACT", math_node(nt, "MULTIPLY", f, 2.5), value(nt, "phase")), 2 * math.pi))
band = math_node(nt, "ADD", 0.25, math_node(nt, "MULTIPLY", math_node(nt, "ADD", wave, 1.0), 0.375))
heat_e = math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", sink, band),
                   math_node(nt, "MULTIPLY", value(nt, "heat"), math_node(nt, "SUBTRACT", 1.0, math_node(nt, "MULTIPLY", f, 0.7))))
nt.links.new(math_node(nt, "ADD", math_node(nt, "MULTIPLY", dome, value(nt, "glow")), heat_e), bs.inputs["Emission Strength"])
dome_rgb = nt.nodes.new("ShaderNodeRGB"); dome_rgb.name = "dome_rgb"; dome_rgb.outputs[0].default_value = (*WARM, 1)
hot_rgb = nt.nodes.new("ShaderNodeRGB"); hot_rgb.outputs[0].default_value = (*HOT, 1)
mixc = nt.nodes.new("ShaderNodeMix"); mixc.data_type = "RGBA"
nt.links.new(sink, mixc.inputs["Factor"]); nt.links.new(dome_rgb.outputs[0], mixc.inputs["A"]); nt.links.new(hot_rgb.outputs[0], mixc.inputs["B"])
nt.links.new(mixc.outputs["Result"], bs.inputs["Emission Color"])
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

alu_m = plain("aluminium", (0.80, 0.80, 0.82), rough=0.28, metal=1.0)
pcb_m = plain("pcb_white", (0.86, 0.86, 0.84), rough=0.32, coat=0.4)
led_body_m = plain("led_body", (0.93, 0.93, 0.92), rough=0.22)
phos_m = plain("phosphor", YELLOW, rough=0.35)
green_m = plain("driver_pcb", (0.03, 0.22, 0.11), rough=0.35, coat=0.5)
cap_m = plain("cap_sleeve", (0.04, 0.07, 0.20), rough=0.3, coat=0.6)
cap_top_m = plain("cap_top", (0.75, 0.76, 0.78), rough=0.25, metal=1.0)
ic_m = plain("ic_black", (0.02, 0.02, 0.022), rough=0.45)
coil_m = plain("copper", (0.95, 0.52, 0.30), rough=0.25, metal=1.0)

part("spreader", cyl(0.0268, 0.0470, 0.0488, seg=96), alu_m)
part("pcb", cyl(0.0255, 0.0488, 0.0500, seg=96), pcb_m)
LEDS = []
for i, (r, n) in enumerate(((0.0175, 10), (0.0075, 4))):
    for k in range(n):
        a = 2 * math.pi * (k + 0.5 * i) / n
        x, y = r * math.cos(a), r * math.sin(a)
        part(f"led_{i}_{k}", B.box(-0.00175, 0.00175, -0.0014, 0.0014, 0.0500, 0.0508), led_body_m, loc=(x, y, 0)).rotation_euler = (0, 0, a)
        ph = part(f"ph_{i}_{k}", B.box(-0.0014, 0.0014, -0.0011, 0.0011, 0.05065, 0.05085), phos_m, loc=(x, y, 0))
        ph.rotation_euler = (0, 0, a)
        LEDS.append(ph)
part("driver", B.box(-0.0045, -0.0031, -0.0095, 0.0095, 0.0120, 0.0440), green_m)
part("cap", cyl(0.0042, 0.0230, 0.0400, x=0.0012, y=0.0035), cap_m, smooth=True)
part("cap_top", cyl(0.0042, 0.0400, 0.0404, x=0.0012, y=0.0035), cap_top_m)
part("ic", B.box(-0.0031, -0.0012, -0.0070, -0.0020, 0.0300, 0.0355), ic_m)
part("coil", cyl(0.0030, 0.0150, 0.0205, x=-0.0005, y=-0.0040), coil_m, smooth=True)
part("res", B.box(-0.0031, -0.0016, 0.0010, 0.0060, 0.0165, 0.0185), plain("resistor", (0.55, 0.42, 0.30), 0.5))
part("w_red", cyl(0.0006, 0.0440, 0.0475, x=-0.0040, y=0.0040, seg=12), plain("wire_red", (0.55, 0.03, 0.02), 0.4))
part("w_blk", cyl(0.0006, 0.0440, 0.0475, x=-0.0040, y=-0.0040, seg=12), plain("wire_black", (0.02, 0.02, 0.02), 0.4))

brass_m = plain("brass", (0.86, 0.62, 0.32), rough=0.28, metal=1.0)
cloth_m = plain("cloth", (0.015, 0.014, 0.013), 0.85)
hang_hardware("led", HANG.z + 0.0157, brass_m, cloth_m)
B.mesh_from("desk", B.box(-1.2, 1.2, -1.2, 1.2, -0.04, 0.0), [pbr_texture("walnut", "black_walnut_veneer_01", 0.9)])
for i in range(5):
    p = Vector((rng.uniform(-1.6, 1.6), rng.uniform(2.6, 4.0), rng.uniform(0.25, 1.4)))
    B.mesh_from(f"bokeh{i}", B.cyl_z(0.035, p.z - 0.002, p.z + 0.002, p.x, p.y, seg=24), [glowing(f"bk{i}", (1.0, 0.62, 0.32), rng.uniform(3, 9))])

bulb_light = bpy.data.lights.new("bulb_light", "POINT")
bulb_light.shadow_soft_size = 0.028
bl = B.link(bpy.data.objects.new("bulb_light", bulb_light)); bl.location = HANG + Vector((0, 0, -0.065))
key1 = B.area("key1", (-0.55, -0.45, 0.75), HANG, 0.35, 6.0, color=(1.0, 0.86, 0.70))
rim1 = B.area("rim1", (0.45, 0.55, 0.65), HANG, 0.25, 9.0, color=(0.65, 0.75, 1.0))

# ------------------------------------------------------------------ the incandescent bulb, only in 'versus'

OLD_AT = HANG + Vector((-0.135, 0.0, 0.0))
old = import_bulb("lightbulb_01", OLD_AT)
OLD_PARTS = [old] + hang_hardware("old", OLD_AT.z + 0.0157, brass_m, cloth_m)
OLD_HOME = {o: o.location.copy() for o in OLD_PARTS}
for m in old.data.materials:
    b = principled(m)
    if "glass" in m.name:
        b.inputs["Transmission Weight"].default_value = 1.0
        b.inputs["Roughness"].default_value = 0.04
        b.inputs["IOR"].default_value = 1.5
        for attr in ("use_raytrace_refraction", "use_screen_refraction"):
            if hasattr(m, attr):
                setattr(m, attr, True)
    else:                                                  # the filament and its wires, above the screw, glow
        ont = m.node_tree
        otc = ont.nodes.new("ShaderNodeTexCoord"); osep = ont.nodes.new("ShaderNodeSeparateXYZ")
        ont.links.new(otc.outputs["Object"], osep.inputs[0])
        ont.links.new(math_node(ont, "MULTIPLY", math_node(ont, "GREATER_THAN", osep.outputs[2], 0.038), value(ont, "glow")), b.inputs["Emission Strength"])
        b.inputs["Emission Color"].default_value = (*TUNG, 1)
        OLD_M = m
old_light = bpy.data.lights.new("old_light", "POINT")
old_light.color, old_light.shadow_soft_size = TUNG, 0.01
ola = B.link(bpy.data.objects.new("old_light", old_light)); ola.location = OLD_AT + Vector((0, 0, -0.06))
OLD_PARTS.append(ola)
OLD_HOME[ola] = ola.location.copy()

# ------------------------------------------------------------------ one LED package, magnified 100x, sectioned

M = Vector((6.0, 0.0, 0.0))
B.mesh_from("macro_pcb", B.box(M.x - 2.0, M.x + 2.0, -2.0, 2.0, -0.012, 0.0), [plain("macro_pcb", (0.035, 0.036, 0.04), 0.78)])
pkg_m = plain("pkg", (0.94, 0.94, 0.93), rough=0.2)
add_clip(pkg_m, "X", 0.0, "cut")
mph_m = plain("macro_phosphor", (1.0, 0.70, 0.05), rough=0.4)
mb = principled(mph_m)
mb.inputs["Subsurface Weight"].default_value = 0.6
mb.inputs["Subsurface Radius"].default_value = (1.0, 0.8, 0.3)
mb.inputs["Subsurface Scale"].default_value = 0.05
emit(mph_m, (1.0, 0.70, 0.12), 0.35)
add_clip(mph_m, "X", 0.0, "cut")
pkg = B.mesh_from("pkg", B.box(-0.175, 0.175, -0.14, 0.14, 0.0, 0.08), [pkg_m])
B.boolean(pkg, [(B.box(-0.14, 0.14, -0.105, 0.105, 0.012, 0.10), "DIFFERENCE")])
B.bevel(pkg, 0.004, 2)
pkg.location = M
phos = B.mesh_from("phos", B.box(-0.1395, 0.1395, -0.1045, 0.1045, 0.0, 0.0615), [mph_m])
phos.location = M + Vector((0, 0, 0.0125))
die = B.mesh_from("die", B.box(-0.032, 0.032, -0.026, 0.026, 0.0125, 0.024), [glowing("die", BLUE, 18.0)])
die.location = M
pad_m = plain("pad", (0.82, 0.83, 0.85), rough=0.2, metal=1.0)
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

# photons: thin streaks that leave the chip blue; outside the phosphor some stay blue and some come out yellow
ph_mat = bpy.data.materials.new("photon")
ph_mat.use_nodes = True
pn = ph_mat.node_tree
pn.nodes.clear()
oi = pn.nodes.new("ShaderNodeObjectInfo")
em = pn.nodes.new("ShaderNodeEmission"); em.inputs[1].default_value = 7.0
po = pn.nodes.new("ShaderNodeOutputMaterial")
pn.links.new(oi.outputs["Color"], em.inputs[0]); pn.links.new(em.outputs[0], po.inputs[0])
PHOTONS = []
for i in range(34):
    ob = B.mesh_from(f"photon{i}", B.cyl_z(0.0011, -0.014, 0.014, 0, 0, seg=8), [ph_mat])
    ang, tilt = rng.uniform(0, 2 * math.pi), rng.uniform(0.05, 0.6)
    d = Vector((math.sin(tilt) * math.cos(ang), math.sin(tilt) * math.sin(ang), math.cos(tilt)))
    PHOTONS.append((ob, d, rng.uniform(0, 1.0), i % 5 < 3))        # 3 in 5 come out converted to yellow

# ------------------------------------------------------------------ shots

cam = B.camera(lens=50, fstop=2.0)
cam.data.clip_start = 0.002                               # the default 10 cm slices into close-ups of a 6 cm bulb
HANG_LIGHTS = [bl, key1, rim1]
MACRO_LIGHTS = [dl, ol, key3, rim3]
ALL_LIGHTS = HANG_LIGHTS + MACRO_LIGHTS + [ola]
CUT_BELOW = (Vector((0.21, -0.10, 0.335)), Vector((0.175, -0.08, 0.35)), HANG + Vector((0, 0, -0.045)), 60, 4.0)

def lerp_cam(a, b, target, lens, fstop, u):
    return a.lerp(b, smooth01(u)), target, lens, fstop

def hang_cam(u):
    return lerp_cam(Vector((0.07, -0.44, 0.40)), Vector((0.04, -0.30, 0.425)), HANG + Vector((0, 0, -0.03)), 50, 2.2, u)

CAMS = {
    "hang": hang_cam,
    "hang_out": lambda u: hang_cam(1.0 - u),
    "hang_white": lambda u: lerp_cam(Vector((0.0, -0.17, 0.40)), Vector((0.0, -0.155, 0.402)), HANG + Vector((0, 0, -0.065)), 60, 2.4, u),
    "hang_warm": lambda u: lerp_cam(Vector((-0.20, -0.12, 0.47)), Vector((-0.19, -0.11, 0.465)), HANG + Vector((0, 0, -0.05)), 60, 2.4, u),
    "hang_blue": lambda u: lerp_cam(Vector((0.05, -0.26, 0.36)), Vector((0.04, -0.22, 0.37)), HANG + Vector((0, 0, -0.06)), 55, 2.4, u),
    "ring_lit": lambda u: lerp_cam(*CUT_BELOW, u),
    "ring_blue": lambda u: lerp_cam(*CUT_BELOW, u),
    "hot_board": lambda u: lerp_cam(Vector((0.19, -0.09, 0.34)), Vector((0.16, -0.075, 0.355)), HANG + Vector((0, 0, -0.047)), 60, 4.0, u),
    "fins": lambda u: lerp_cam(Vector((0.075, -0.125, 0.452)), Vector((0.06, -0.11, 0.445)), HANG + Vector((0.008, -0.024, -0.030)), 70, 4.5, u),
    "driver": lambda u: lerp_cam(Vector((0.13, -0.035, 0.445)), Vector((0.11, -0.03, 0.437)), HANG + Vector((0, 0, -0.028)), 70, 5.0, u),
    "macro_fill": lambda u: lerp_cam(M + Vector((0.70, -0.46, 0.34)), M + Vector((0.60, -0.40, 0.30)), M + Vector((0, 0, 0.04)), 50, 3.2, u),
    "macro_photons": lambda u: lerp_cam(M + Vector((0.78, -0.50, 0.36)), M + Vector((0.58, -0.36, 0.26)), M + Vector((0, 0, 0.05)), 50, 3.2, u),
    "macro_top": lambda u: lerp_cam(M + Vector((0.10, -0.25, 0.95)), M + Vector((0.08, -0.20, 0.80)), M + Vector((0, 0, 0.05)), 45, 3.5, u),
    "spectrum": lambda u: (Vector((0.10, -0.60, 0.42)).lerp(Vector((0.08, -0.56, 0.42)), u), HANG + Vector((0, 0, -0.03)), 85, 1.4),
    "versus": lambda u: lerp_cam(Vector((-0.06, -0.50, 0.40)), Vector((-0.066, -0.42, 0.41)), HANG + Vector((-0.0675, 0, -0.035)), 50, 2.4, u),
}

def shot_at(t):
    k = max([0] + [i for i, (s, _) in enumerate(SHOTS) if t >= s - 1e-6])   # motion blur samples before frame 1
    t0 = SHOTS[k][0]
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    return SHOTS[k][1], max(0.0, min(1.0, (t - t0) / max(1e-6, t1 - t0))), t - t0

def apply_state(t):
    name, u, age = shot_at(t)
    loc, tg, lens, fstop = CAMS[name](u)
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    cam.data.dof.aperture_fstop = fstop
    cam.data.dof.focus_distance = (tg - loc).length if name != "spectrum" else 0.12   # spectrum: everything soft
    macro = name.startswith("macro")
    on = set(MACRO_LIGHTS if macro else HANG_LIGHTS)
    # the bulb's own light: warm when lit, blue for the blue flash, off in the cutaways
    lit = name in ("hang", "hang_out", "hang_white", "hang_warm", "hang_blue", "spectrum", "versus")
    if not lit:
        on.discard(bl)
    if name == "versus":
        on.add(ola)
    for ob in ALL_LIGHTS:
        ob.hide_render = ob not in on
    dome_color = {"hang_white": COOL, "hang_blue": BLUE}.get(name, WARM)
    BULB_M.node_tree.nodes["dome_rgb"].outputs[0].default_value = (*dome_color, 1)
    bulb_light.color = dome_color
    bulb_light.energy = 12.0 if name == "hang_blue" else 7.0
    setv(BULB_M, "glow", {"hang_blue": 2.6, "hang_white": 14.0}.get(name, 28.0) if lit else 0.0)   # bright blue reads white under AGX
    setv(BULB_M, "cut", 1.0 if name in ("ring_lit", "ring_blue", "hot_board", "driver") else 0.0)
    heat = 0.0
    if name == "fins":
        heat = 5.0 * smooth01(age / 0.5)
    setv(BULB_M, "heat", heat)
    setv(BULB_M, "phase", t * 1.4)
    # the LED chips: warm when lit, bare blue in ring_blue, dimming as the board heats up
    pb = principled(phos_m)
    if name == "ring_blue":
        pb.inputs["Base Color"].default_value = (0.05, 0.12, 1.0, 1)
        emit(phos_m, BLUE, 12.0)
    else:
        pb.inputs["Base Color"].default_value = (*YELLOW, 1)
        dim = 1.0 - 0.8 * smooth01((u - 0.35) / 0.5) if name == "hot_board" else 1.0
        emit(phos_m, (1.0, 0.86, 0.62), (14.0 if lit else 1.6) * dim)
    hot = 0.0
    if name == "hot_board":
        hot = 25.0 * smooth01(u / 0.4)
    emit(pcb_m, HOT, hot * 0.6)
    emit(alu_m, HOT, hot)
    # the old bulb is only on set for 'versus'; it dies at events.old_dies
    for ob in OLD_PARTS:
        ob.location = OLD_HOME[ob] if name == "versus" else AWAY
    alive = t < EV.get("old_dies", 1e9)
    flicker = 1.0
    if name == "versus" and alive and EV.get("old_dies", 1e9) - t < 0.35:
        flicker = 0.35 + 0.65 * (int(t * 30) % 3 != 0)
    setv(OLD_M, "glow", 22.0 * flicker if alive else 0.0)
    old_light.energy = 6.0 * flicker if alive else 0.0
    # the macro package
    setv(pkg_m, "cut", 1.0)
    setv(mph_m, "cut", 1.0)
    fill = smooth01(u / 0.6) if name == "macro_fill" else 1.0
    phos.scale = (1, 1, max(0.001, fill))
    for ob, d, phase, converts in PHOTONS:
        if name not in ("macro_photons", "macro_top"):
            ob.location = AWAY
            continue
        a = (age * 1.3 + phase) % 1.0
        p = M + Vector((0, 0, 0.022)) + d * (a * 0.30)
        ob.location = p
        ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        inside = p.z < M.z + 0.074
        ob.color = (*BLUE, 1) if inside or not converts else (*YELLOW, 1)
        ob.scale = (1, 1, 1) if a < 0.9 else (0.01, 0.01, 0.01)

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    pts = {
        "chips": lambda: LEDS[2].matrix_world @ Vector((0, 0, 0.0508)),
        "driver": lambda: bulb.matrix_world @ Vector((-0.002, 0.0035, 0.030)),
        "fins": lambda: bulb.matrix_world @ Vector((0.006, 0.026, 0.032)),     # object +y faces the camera once flipped
        "die": lambda: M + Vector((0.0, -0.02, 0.018)),
        "phosphor": lambda: M + Vector((0.0, -0.09, 0.066)),
        "led": lambda: HANG + Vector((0, 0, -0.07)),
        "old": lambda: OLD_AT + Vector((0, 0, -0.07)),
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

B.render_settings(FPS, samples=int(os.environ.get("BULB_SAMPLES", "64")), motion_blur=0.35, look="AgX - Medium High Contrast")

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1 + scn.frame_subframe) / FPS)

anchors()
apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
