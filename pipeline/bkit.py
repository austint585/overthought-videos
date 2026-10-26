"""Blender-side kit for the 3D episodes: materials, mesh builders, booleans, lights, render settings, distance haze.
Imported by the *_scene.py scripts that run inside Blender (blender -b -P <scene>.py)."""
import math
import bpy, bmesh
from mathutils import Matrix, Vector

ORANGE = (1.0, 0.144, 0.024)       # brand orange (255,106,43) in linear
GLOW = (1.0, 0.16, 0.0)            # emission reads pink under AgX unless pushed past the brand hue
RED = (1.0, 0.02, 0.01)

scene = bpy.context.scene

def clear_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)

# ------------------------------------------------------------------ materials

def material(name, color, metallic=0.0, rough=0.4, rough_var=0.0, brushed=0.0, coat=0.0, noise_scale=3.0):
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
        n.inputs["Scale"].default_value = noise_scale
        n.inputs["Detail"].default_value = 6.0
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value = rough - rough_var
        mr.inputs["To Max"].default_value = rough + rough_var
        nt.links.new(n.outputs["Fac"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], p.inputs["Roughness"])
    if brushed:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (0.4, 40.0, 40.0)
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

def color_noise(m, c0, c1, scale=2.0, coords="Object", mapping_scale=(1, 1, 1), detail=8.0, distortion=0.0):
    """Base color from noise between two colors (wood grain, grass, rock)."""
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = mapping_scale
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Distortion"].default_value = distortion
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c0, 1)
    ramp.color_ramp.elements[1].color = (*c1, 1)
    nt.links.new(tc.outputs[coords], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
    nt.links.new(n.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf(m).inputs["Base Color"])
    return ramp

def set_emit(m, strength, color=GLOW):
    p = bsdf(m)
    p.inputs["Emission Strength"].default_value = 0.6 * strength
    p.inputs["Emission Color"].default_value = (*color, 1)

def add_haze(m, color, distance):
    """Fade the surface toward the horizon color with camera distance (aerial perspective)."""
    nt = m.node_tree
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    src = out.inputs["Surface"].links[0].from_socket
    cam = nt.nodes.new("ShaderNodeCameraData")
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = -1.0 / distance
    ex = nt.nodes.new("ShaderNodeMath"); ex.operation = "EXPONENT"
    inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*color, 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(cam.outputs["View Distance"], mul.inputs[0])
    nt.links.new(mul.outputs[0], ex.inputs[0])
    nt.links.new(ex.outputs[0], inv.inputs[1])
    nt.links.new(inv.outputs[0], mix.inputs["Fac"])
    nt.links.new(src, mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])

# ------------------------------------------------------------------ geometry

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

def cyl_z(r, z0, z1, x, y=0.0, seg=64, r2=None):
    def b(bm):
        M = Matrix.Translation((x, y, (z0 + z1) / 2))
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

def with_material(builder, index):
    """Run a builder and tag the faces it made with a material slot index."""
    def b(bm):
        before = set(bm.faces)
        builder(bm)
        for f in bm.faces:
            if f not in before:
                f.material_index = index
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

# ------------------------------------------------------------------ lights, camera, render

def aim(ob, loc, target):
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

def area(name, loc, target, size, power, color=(1, 1, 1), size_y=None):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = "RECTANGLE"
    ld.size = size
    ld.size_y = size_y or size
    ld.energy = power
    ld.color = color
    ob = link(bpy.data.objects.new(name, ld))
    aim(ob, loc, target)
    return ob

def sun(name, azimuth_deg, elevation_deg, strength, color=(1, 1, 1), angle_deg=1.5):
    ld = bpy.data.lights.new(name, "SUN")
    ld.energy = strength
    ld.color = color
    ld.angle = math.radians(angle_deg)
    ob = link(bpy.data.objects.new(name, ld))
    az, el = math.radians(azimuth_deg), math.radians(elevation_deg)
    to_sun = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
    ob.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()
    return ob

def camera(lens=50, fstop=4.0):
    cd = bpy.data.cameras.new("cam")
    cam = link(bpy.data.objects.new("cam", cd))
    scene.camera = cam
    cd.lens = lens
    cd.sensor_width = 36
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop
    return cam

def render_settings(fps, samples=48, motion_blur=0.4, look="AgX - Medium High Contrast"):
    r = scene.render
    r.engine = "BLENDER_EEVEE"
    r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
    r.fps = fps
    r.use_motion_blur = motion_blur > 0
    r.motion_blur_shutter = motion_blur
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGB"
    r.image_settings.compression = 15
    r.use_overwrite = False
    r.use_placeholder = True
    r.use_lock_interface = True
    ee = scene.eevee
    ee.taa_render_samples = samples
    for attr, val in (("use_raytracing", True), ("use_shadows", True), ("use_fast_gi", True), ("fast_gi_method", "GLOBAL_ILLUMINATION")):
        try:
            setattr(ee, attr, val)
        except Exception as ex:
            print("eevee setting skipped:", attr, ex)
    scene.view_settings.view_transform = "AgX"
    for name in (look, look.replace("AgX - ", "")):
        try:
            scene.view_settings.look = name
            break
        except Exception:
            pass

def render(out_dir, mode, n_frames):
    """mode 'all' renders every frame (skipping ones on disk), or a comma list of 1-based frames (re-rendered)."""
    import os
    scene.render.filepath = os.path.join(out_dir, "f_#####")
    if mode == "all":
        scene.frame_start, scene.frame_end = 1, n_frames
        bpy.ops.render.render(animation=True)
        return
    for n in [int(x) for x in mode.split(",")]:
        path = os.path.join(out_dir, f"f_{n:05d}.png")
        if os.path.exists(path):
            os.remove(path)
        scene.frame_start = scene.frame_end = n
        bpy.ops.render.render(animation=True)
