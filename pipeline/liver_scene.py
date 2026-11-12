"""The "larp" payoff of the raw liver parody (render_liver.py): a raw liver shot like a luxury car commercial, the way
the original ends on a grainy Porsche taillight and a Lamborghini in the dark. Three shots, all code-built:
  A 0.0 to 2.2 s  macro: a thin strip light sweeps across the wet surface (the taillight sweep)
  B 2.2 to 4.1 s  the "sill plate": RAW LIVER lit in a dark brushed-metal plate, camera slides along it
  C 4.1 to 6.4 s  hero: the liver on a black glossy plate, low three-quarter, rim light, slow push

blender -b --factory-startup -P liver_scene.py -- out_dir MODE      (MODE: 'all' or a 1-based frame list)
"""
import math, os, sys
import bpy, bmesh
from mathutils import Vector, noise

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bkit as B

argv = sys.argv[sys.argv.index("--") + 1:]
OUT, MODE = argv[0], argv[1]
FPS, DUR = 30, 6.4
NF = int(round(DUR * FPS))
SHOT_B, SHOT_C = 2.2, 4.1
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor", "fonts", "Inter-500.ttf")

B.clear_scene()
scene = B.scene
scene.world = bpy.data.worlds.new("w")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
B.render_settings(FPS, samples=64, motion_blur=0.5)

# ------------------------------------------------------------------ the liver (about 3.4 units wide)

def liver_mesh():
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=64, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co
        u = min(1.0, max(0.0, (x + 1) / 2))                  # 0 at the big right lobe, 1 at the thin left lobe tip
        thick = 0.5 * (1 - 0.55 * u ** 1.3)
        z = z * thick * (0.45 if z < 0 else 1.0)             # flat underside, domed top
        y = y * 1.25 * (1.0 - 0.3 * u)                       # the left lobe narrows to a wedge
        x = x * 1.5 + 0.2 * y * y
        groove = 0.11 * math.exp(-((x - 0.25 + 0.35 * y) / 0.16) ** 2) if z > 0 else 0.0   # the ligament notch
        n = noise.noise(Vector((x * 1.1, y * 1.1, z * 1.1))) * 0.06 + noise.noise(Vector((x * 4, y * 4, z * 4))) * 0.012
        v.co = Vector((x, y, z - groove + n))
    me = bpy.data.meshes.new("liver")
    bm.to_mesh(me)
    bm.free()
    ob = B.link(bpy.data.objects.new("liver", me))
    sub = ob.modifiers.new("sub", "SUBSURF")
    sub.levels = sub.render_levels = 1
    ob.data.shade_smooth()
    return ob

LIV = B.material("liver", (0.08, 0.008, 0.007), rough=0.28, rough_var=0.12, coat=0.55, noise_scale=7.0)
P = B.bsdf(LIV)
P.inputs["Coat Roughness"].default_value = 0.07
P.inputs["Subsurface Weight"].default_value = 0.12
P.inputs["Subsurface Radius"].default_value = (1.0, 0.12, 0.08)
P.inputs["Subsurface Scale"].default_value = 0.03
B.color_noise(LIV, (0.035, 0.004, 0.005), (0.13, 0.014, 0.011), scale=2.4, detail=7.0, distortion=0.4)
nt = LIV.node_tree
bump_n = nt.nodes.new("ShaderNodeTexNoise"); bump_n.inputs["Scale"].default_value = 22.0; bump_n.inputs["Detail"].default_value = 8.0
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.22; bump.inputs["Distance"].default_value = 0.01
nt.links.new(bump_n.outputs["Fac"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], P.inputs["Normal"])
nt.links.new(bump.outputs["Normal"], P.inputs["Coat Normal"])

liver = liver_mesh()
liver.data.materials.append(LIV)
liver.location = (0, 0, 0.36)
liver.rotation_euler = (0, 0, math.radians(-12))
BLOOD = B.material("blood", (0.05, 0.002, 0.002), rough=0.04, coat=1.0)
def puddle(bm):
    bmesh.ops.create_circle(bm, cap_ends=True, segments=96, radius=1.0)
    for v in bm.verts:
        a = math.atan2(v.co.y, v.co.x)
        r = v.co.length * (1 + 0.14 * math.sin(3 * a + 0.7) + 0.08 * math.sin(7 * a))
        v.co = Vector((r * 2.2 * math.cos(a), r * 1.55 * math.sin(a), 0.026))
pud = B.mesh_from("puddle", puddle, [BLOOD])
pud.rotation_euler = (0, 0, math.radians(-12))

# a black glossy plate and a black showroom floor
PLATE = B.material("plate", (0.008, 0.008, 0.009), rough=0.12, coat=1.0)
plate = B.mesh_from("plate", B.cyl_z(2.6, -0.06, 0.02, 0, 0, seg=160), [PLATE])
plate.data.shade_smooth()
FLOOR = B.material("floor", (0.004, 0.004, 0.005), rough=0.22, rough_var=0.08)
B.mesh_from("floor", B.box(-40, 40, -40, 40, -0.4, -0.06), [FLOOR])

# the sill plate (shot B): brushed dark metal, the words lit from inside, far away from the liver
SILL = B.material("sill", (0.05, 0.05, 0.055), metallic=1.0, rough=0.32, brushed=0.6)
sill = B.mesh_from("sill", B.box(-5.0, 5.0, -0.7, 0.7, -0.1, 0.0), [SILL])
sill.location = (0, 30, 0)
sill.rotation_euler = (0, 0, math.radians(28))
B.bevel(sill, 0.04, 3)
cu = bpy.data.curves.new("badge", "FONT")
cu.body = "RAW  LIVER"
cu.font = bpy.data.fonts.load(FONT)
cu.size = 0.54
cu.space_character = 1.35
cu.align_x, cu.align_y = "CENTER", "CENTER"
cu.extrude = 0.004
badge = B.link(bpy.data.objects.new("badge", cu))
badge.location = (0, 30, 0.006)
badge.rotation_euler = (0, 0, math.radians(28))
EMIT = B.material("badge", (1, 1, 1), rough=0.3)
B.set_emit(EMIT, 18.0, (1.0, 0.97, 0.93))
badge.data.materials.append(EMIT)

# ------------------------------------------------------------------ light: car-commercial strips and rims

strip = B.area("strip", (0, -3, 3), (0, 0, 0.3), 0.12, 900, size_y=9.0)            # the sweeping taillight strip
rim = B.area("rim", (0, 6, 2.2), (0, 0, 0.4), 4.0, 1600, (0.85, 0.9, 1.0), size_y=0.6)
kick = B.area("kick", (-6, -2, 1.6), (0, 0, 0.3), 1.5, 260, (1.0, 0.82, 0.75))
sill_l = B.area("sill_light", (0, 27.5, 2.0), (0, 30, 0), 0.15, 500, size_y=10.0)
for l in (strip, rim, kick, sill_l):
    l.data.volume_factor = 0.0

cam = B.camera(lens=85, fstop=2.0)

def smooth01(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

def apply_state(t):
    if t < SHOT_B:                                           # A: macro, grazing angle, a thin strip sweeps across
        u = t / SHOT_B
        cam.data.lens = 85
        cam.data.dof.aperture_fstop = 2.0
        p, tg = Vector((2.2 - 0.5 * u, -4.6, 1.25)), Vector((0.6 - 0.3 * u, 0, 0.45))
        B.aim(cam, tuple(p), tuple(tg))
        cam.data.dof.focus_distance = (p - tg).length
        sx = -4.5 + 9.0 * smooth01(u * 1.1)
        B.aim(strip, (sx, -2.6, 2.8), (sx * 0.35, 0, 0.4))
        strip.data.energy = 380
        rim.data.energy, kick.data.energy, sill_l.data.energy = 520, 30, 0
    elif t < SHOT_C:                                         # B: the sill plate on a diagonal, slow slide, light sweep
        u = (t - SHOT_B) / (SHOT_C - SHOT_B)
        cam.data.lens = 26                                   # wide enough that the whole word stays in frame
        cam.data.dof.aperture_fstop = 2.8
        p, tg = Vector((-0.9 + 0.4 * u, 30 - 5.2, 3.4)), Vector((-0.15 + 0.3 * u, 30.1, 0))
        B.aim(cam, tuple(p), tuple(tg))
        cam.data.dof.focus_distance = (p - tg).length
        lx = -6.0 + 12.0 * smooth01(u)
        B.aim(sill_l, (lx, 27.8, 2.2), (lx * 0.8, 30, 0))
        sill_l.data.energy = 420
        strip.data.energy, rim.data.energy, kick.data.energy = 0, 0, 0
    else:                                                    # C: hero, low three-quarter, slow push
        u = (t - SHOT_C) / (DUR - SHOT_C)
        cam.data.lens = 40
        cam.data.dof.aperture_fstop = 2.8
        d = 6.4 - 1.1 * smooth01(u)
        a = math.radians(-62 + 6 * u)
        p, tg = Vector((d * math.cos(a), d * math.sin(a), 1.55)), Vector((0.15, 0, 0.42))
        B.aim(cam, tuple(p), tuple(tg))
        cam.data.dof.focus_distance = (p - tg).length
        B.aim(strip, (3.0 - 1.0 * u, -3.5, 3.6), (0, 0, 0.4))
        strip.data.energy = 260
        rim.data.energy, kick.data.energy, sill_l.data.energy = 1400, 90, 0

def shot_of(t):
    return 0 if t < SHOT_B else (1 if t < SHOT_C else 2)

def on_frame(scn, depsgraph=None):
    # Motion blur samples a little before and after the frame. On a cut frame those samples must not reach back into
    # the previous shot (they smeared shot A across the first frame of shot B). bkit.render's frame-list mode renders
    # one frame at a time (frame_start == frame_end == that frame), so the frame being made is known: render the
    # cut frames (67 and 124) that way.
    t = (scn.frame_current - 1 + scn.frame_subframe) / FPS
    if scn.frame_start == scn.frame_end:
        tc = (scn.frame_start - 1) / FPS
        if shot_of(t) != shot_of(tc):
            t = tc
    apply_state(t)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
os.makedirs(OUT, exist_ok=True)
B.render(OUT, MODE, NF)
