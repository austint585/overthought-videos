"""Clay kit (Blender side): the handmade plasticine look Austin picked on Oct 28 (the @petersindex reel, see ops/style.md),
replacing the voxel kit. Every part is a rounded block with a slight hand-made wobble, a mottled clay material with
soft thumb dents and patches of fingerprint ridges, and a little subsurface glow. Figures are built from the same parts
with the voxel figures' pivots (legs at the hips, arms at the shoulders, head at the neck), so posing code carries over.

    import clay as C
    m = C.clay("shirt", (0.4, 0.42, 0.46))
    C.soft("box", (0.5, 0.3, 0.2), m, center=(0, 0, 1))
    C.boxes("couch", [((x0, x1, y0, y1, z0, z1), m), ...], origin)    # same call as the voxel scenes' boxes()
    f = C.figure("bro", skin=..., shirt=...)                          # dict: root, legL, legR, body, armL, armR, head
"""
import math, os, random
import bpy, bmesh
from mathutils import Matrix, Vector
import bkit as B

scene = B.scene

# ------------------------------------------------------------------ material

def clay(name, color, rough=0.6, sss=0.1, prints=1.0, mottle=0.07, emit=0.0, emit_color=None, dents=1.0):
    """Plasticine: color mottled by hand mixing, rougher where untouched, a little subsurface glow, and a bump made of
    fine grain, soft thumb dents and patches of fingerprint ridges. Coordinates are object space in meters, so the
    marks stay on a part when it moves and keep the same size on every part."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes.new, nt.links.new
    p = nt.nodes["Principled BSDF"]
    tc = N("ShaderNodeTexCoord")
    obj = tc.outputs["Object"]

    mot = N("ShaderNodeTexNoise")
    mot.inputs["Scale"].default_value = 2.2
    mot.inputs["Detail"].default_value = 3.0
    L(obj, mot.inputs["Vector"])
    cr = N("ShaderNodeValToRGB")
    lo = tuple(max(0.0, c * (1 - mottle)) for c in color)
    hi = tuple(min(1.0, c * (1 + mottle)) for c in color)
    cr.color_ramp.elements[0].position, cr.color_ramp.elements[0].color = 0.3, (*lo, 1)
    cr.color_ramp.elements[1].position, cr.color_ramp.elements[1].color = 0.7, (*hi, 1)
    L(mot.outputs["Fac"], cr.inputs["Fac"])
    L(cr.outputs["Color"], p.inputs["Base Color"])

    mr = N("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = max(0.05, rough - 0.1)
    mr.inputs["To Max"].default_value = min(1.0, rough + 0.08)
    L(mot.outputs["Fac"], mr.inputs["Value"])
    L(mr.outputs["Result"], p.inputs["Roughness"])
    p.inputs["Subsurface Weight"].default_value = sss
    p.inputs["Subsurface Radius"].default_value = (1.0, 0.45, 0.3)
    p.inputs["Subsurface Scale"].default_value = 0.02
    p.inputs["Specular IOR Level"].default_value = 0.32
    if emit:
        p.inputs["Emission Color"].default_value = (*(emit_color or color), 1)
        p.inputs["Emission Strength"].default_value = emit

    grain = N("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 90.0
    grain.inputs["Detail"].default_value = 2.0
    dent = N("ShaderNodeTexVoronoi")
    dent.feature = "SMOOTH_F1"
    dent.inputs["Scale"].default_value = 6.0
    ring = N("ShaderNodeTexWave")
    ring.wave_type = "RINGS"
    ring.rings_direction = "SPHERICAL"
    ring.inputs["Scale"].default_value = 160.0
    ring.inputs["Distortion"].default_value = 3.0
    ring.inputs["Detail"].default_value = 1.0
    patch = N("ShaderNodeTexNoise")
    patch.inputs["Scale"].default_value = 4.0
    for n in (grain, dent, ring, patch):
        L(obj, n.inputs["Vector"])
    pm = N("ShaderNodeMapRange")                          # fingerprints only where a finger pressed
    pm.inputs["From Min"].default_value = 0.56
    pm.inputs["From Max"].default_value = 0.68
    L(patch.outputs["Fac"], pm.inputs["Value"])
    pr = N("ShaderNodeMath"); pr.operation = "MULTIPLY"
    L(ring.outputs["Fac"], pr.inputs[0]); L(pm.outputs["Result"], pr.inputs[1])
    h1 = N("ShaderNodeMath"); h1.operation = "MULTIPLY_ADD"
    L(grain.outputs["Fac"], h1.inputs[0]); h1.inputs[1].default_value = 0.3
    dm = N("ShaderNodeMath"); dm.operation = "MULTIPLY"; dm.inputs[1].default_value = dents
    L(dent.outputs["Distance"], dm.inputs[0]); L(dm.outputs[0], h1.inputs[2])
    h2 = N("ShaderNodeMath"); h2.operation = "MULTIPLY_ADD"
    L(pr.outputs[0], h2.inputs[0]); h2.inputs[1].default_value = 0.25 * prints; L(h1.outputs[0], h2.inputs[2])
    bump = N("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.75
    bump.inputs["Distance"].default_value = 0.01
    L(h2.outputs[0], bump.inputs["Height"])
    L(bump.outputs["Normal"], p.inputs["Normal"])
    return m

def glossy(name, color, rough=0.12):
    """Eyes and buttons: the same clay, polished."""
    return clay(name, color, rough=rough, sss=0.0, prints=0.0, mottle=0.02, dents=0.15)

def glow(name, color, strength):
    """Lit windows, lamp shades, screens: flat emission (no clay marks needed where it's too bright to see them)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Emission Color"].default_value = (*color, 1)
    p.inputs["Emission Strength"].default_value = strength
    p.inputs["Roughness"].default_value = 0.5
    return m

# ------------------------------------------------------------------ parts

_wobble = None

def _wobble_tex():
    global _wobble
    if _wobble is None:
        _wobble = bpy.data.textures.new("clay_wobble", "CLOUDS")
        _wobble.noise_scale = 0.3
        _wobble.noise_depth = 1
    return _wobble

def soft(name, size, mat, center=(0, 0, 0), parent=None, r=None, wobble=None, subdiv=2, rot=None):
    """A rounded clay block of size (x, y, z) centered at `center` (in the parent's space). r is the corner radius
    (default a third of the thinnest side, so small parts come out as pebbles and capsules); wobble is the hand-made
    unevenness in meters."""
    sx, sy, sz = size
    mn = min(size)
    r = min(0.33 * mn if r is None else r, 0.49 * mn)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Diagonal((sx, sy, sz, 1)))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = B.link(bpy.data.objects.new(name, me))
    ob.parent = parent
    ob.location = center
    if rot:
        ob.rotation_euler = rot
    bv = ob.modifiers.new("round", "BEVEL")
    bv.width = r
    bv.segments = 3
    bv.limit_method = "NONE"
    bv.use_clamp_overlap = True
    sd = ob.modifiers.new("soft", "SUBSURF")
    sd.levels = sd.render_levels = subdiv
    w = min(0.025, 0.05 * mn) if wobble is None else wobble
    if w > 0:
        dp = ob.modifiers.new("hand", "DISPLACE")
        dp.texture = _wobble_tex()
        dp.strength = w
        dp.mid_level = 0.5
    me.shade_smooth()
    return ob

def ball(name, radius, mat, center=(0, 0, 0), parent=None, squash=(1, 1, 1), wobble=None):
    return soft(name, tuple(2 * radius * s for s in squash), mat, center, parent, r=radius, wobble=wobble)

def empty(name, loc=(0, 0, 0), parent=None):
    ob = B.link(bpy.data.objects.new(name, None))
    ob.parent = parent
    ob.location = loc
    return ob

def boxes(name, parts, origin, parent=None, r=None):
    """Same call as the voxel scenes' boxes(): parts are ((x0, x1, y0, y1, z0, z1), material) around `origin`.
    Returns an empty that carries every part, so moving, scaling or parenting it moves the whole prop."""
    root = empty(name, origin, parent)
    for n, ((x0, x1, y0, y1, z0, z1), m) in enumerate(parts):
        soft(f"{name}.{n}", (x1 - x0, y1 - y0, z1 - z0), m, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), root, r)
    return root

# ------------------------------------------------------------------ figures

_mats = {}

def _m(color, rough=0.6, kind="clay"):
    key = (color, rough, kind)
    if key not in _mats:
        _mats[key] = (glossy if kind == "glossy" else clay)(f"fig{len(_mats)}", color, rough)
    return _mats[key]

def figure(name, skin=(0.80, 0.56, 0.40), shirt=(0.42, 0.43, 0.46), pants=(0.08, 0.08, 0.10), shoes=(0.92, 0.92, 0.90),
           hair=(0.10, 0.06, 0.03), cap=None, cap_back=True, tank=False, arms=1.0, belly=1.0, brows=0.0):
    """A clay person, about 2.1 m with the head, pivots matching the voxel figures: legs at (+-0.14, 0, 0.75), body at
    (0, 0, 0.75), arms at (+-0.47, 0, 1.5) hanging down to about z -0.8, head at (0, 0, 1.55). arms scales the arm
    thickness (gym bro 1.3), belly the waist depth, brows tilts the eyebrows (positive is angry, negative is worried).
    Returns a dict of the moving parts plus 'brows' and 'mouth' for expressions."""
    SK, SK2 = _m(skin), _m(tuple(c * 0.86 for c in skin))
    SH, PA, SO = _m(shirt), _m(pants), _m(shoes, 0.45)
    HA = _m(hair, 0.7)
    EYE, SHINE = _m((0.02, 0.02, 0.025), 0.1, "glossy"), glow("eye_shine", (1.0, 1.0, 1.0), 6.0)
    root = empty(name)
    f = {"root": root}
    for side, x in (("L", -0.15), ("R", 0.15)):
        leg = empty(f"{name}.leg{side}", (x, 0, 0.75), root)
        soft(f"{name}.thigh{side}", (0.27, 0.28, 0.46), PA, (0, 0, -0.2), leg, r=0.12)
        soft(f"{name}.shin{side}", (0.22, 0.23, 0.36), PA if not tank else SK, (0, 0, -0.5), leg, r=0.1)
        soft(f"{name}.shoe{side}", (0.27, 0.40, 0.15), SO, (0, -0.06, -0.69), leg, r=0.07)
        f["leg" + side] = leg
    body = empty(f"{name}.body", (0, 0, 0.75), root)
    soft(f"{name}.hips", (0.6, 0.33 * belly, 0.3), PA, (0, 0, 0.1), body, r=0.13)
    soft(f"{name}.torso", (0.66, 0.36 * belly, 0.66), SH, (0, 0, 0.45), body, r=0.17)
    if tank:                                                         # bare shoulders
        for sx in (-1, 1):
            soft(f"{name}.delt{sx}", (0.22, 0.3, 0.2), SK, (0.25 * sx, 0, 0.72), body, r=0.09)
    f["body"] = body
    aw = 0.22 * arms
    for side, x in (("L", -0.44 - 0.04 * arms), ("R", 0.44 + 0.04 * arms)):
        arm = empty(f"{name}.arm{side}", (x, 0, 1.5), root)
        soft(f"{name}.upper{side}", (aw * 1.08, aw * 1.08, 0.42), SK if tank else SH, (0, 0, -0.2), arm, r=aw * 0.5)
        soft(f"{name}.fore{side}", (aw, aw, 0.36), SK, (0, 0, -0.5), arm, r=aw * 0.48)
        ball(f"{name}.hand{side}", 0.1 + 0.015 * arms, SK, (0, -0.01, -0.74), arm, squash=(0.95, 0.85, 1.05))
        f["arm" + side] = arm
    head = empty(f"{name}.head", (0, 0, 1.55), root)
    soft(f"{name}.neck", (0.2, 0.2, 0.16), SK, (0, 0, 0.03), head, r=0.09)
    soft(f"{name}.skull", (0.54, 0.5, 0.56), SK, (0, 0, 0.31), head, r=0.22)
    for sx in (-1, 1):
        soft(f"{name}.ear{sx}", (0.07, 0.11, 0.15), SK2, (0.27 * sx, 0.02, 0.29), head, r=0.035)
        soft(f"{name}.eye{sx}", (0.085, 0.05, 0.12), EYE, (0.11 * sx, -0.235, 0.33), head, r=0.042, wobble=0.0)
        ball(f"{name}.shine{sx}", 0.012, SHINE, (0.11 * sx + 0.02, -0.262, 0.36), head, wobble=0.0)
    f["brows"] = []
    for sx in (-1, 1):
        b = soft(f"{name}.brow{sx}", (0.14, 0.045, 0.04), HA, (0.115 * sx, -0.245, 0.44), head, r=0.019,
                 rot=(0, -0.35 * brows * sx, 0))
        f["brows"].append(b)
    soft(f"{name}.nose", (0.085, 0.09, 0.1), SK2, (0, -0.26, 0.25), head, r=0.042)
    f["mouth"] = soft(f"{name}.mouth", (0.15, 0.04, 0.035), _m((0.30, 0.10, 0.08), 0.5), (0, -0.237, 0.14), head, r=0.016)
    if cap:
        CP = _m(cap, 0.55)
        soft(f"{name}.cap", (0.58, 0.54, 0.22), CP, (0, 0.01, 0.56), head, r=0.1)
        soft(f"{name}.brim", (0.42, 0.26, 0.045), CP, (0, 0.33 if cap_back else -0.33, 0.5), head, r=0.02)
    else:
        soft(f"{name}.hair", (0.57, 0.53, 0.2), HA, (0, 0.02, 0.56), head, r=0.09)
    f["head"] = head
    return f

# ------------------------------------------------------------------ render setup

def cpu_preview_quality(samples=24, percent=50):
    """When OVERTHOUGHT_CPU_PREVIEW=1 (look checks while the GPU is busy): half resolution, few samples and a CPU
    denoise, so a clay still takes minutes instead of the 15+ a full-size one took on Oct 28. The driver scales the
    frame back up before drawing the overlay."""
    if os.environ.get("OVERTHOUGHT_CPU_PREVIEW") != "1":
        return
    scene.render.resolution_percentage = percent
    c = scene.cycles
    c.samples = samples
    c.use_denoising = True
    try:
        c.denoiser = "OPENIMAGEDENOISE"
        c.denoising_use_gpu = False
    except Exception as ex:
        print("denoise setting skipped:", ex)
