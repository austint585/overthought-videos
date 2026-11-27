"""PS1/PS2 console look for the Blender kits (Nov 26), from the six lines in @visualizemy_'s "How to make low poly videos
with Claude" (https://www.instagram.com/p/DgLKy4hTAGZ/, full prompt at visualizemy.com/videos/low-poly), which
Austin DMed as the way to make "the p2 style". They build it in three.js; the same six steps map onto Blender:

1. Low poly: unsubdivide the MakeHuman meshes once (a quarter of the faces, stable from frame to frame because it
   follows the topology, unlike Collapse), thin out big props with Collapse (they don't move), flat shading.
2. Tiny textures: every image texture shrunk to TEX px on its longest side, nearest-neighbour filtering.
3. Big pixels: render at 270 x 480, then post() scales it up 4x with no smoothing.
4. The wobble: a Geometry Nodes pass snaps every vertex to the low-res pixel grid in camera space, so corners jump
   from pixel to pixel as things move; post() cuts colour to 23 levels with a 4x4 Bayer dither and adds light
   scanlines. (Their affine texture warp is left out: Blender has no switch for it.)
5. Slice it open and 6. a pose on every sentence are direction, not look: they belong in the episode script.

Blender side (inside a scene script, after the scene is built):   ps2look.apply(cam)
Python side (after the frames are rendered):                        ps2look.post_dir(src_dir, dst_dir, frames)
"""
import os

W, H = 270, 480          # low-res render; 4x gives 1080 x 1920
SCALE = 4
TEX = int(os.environ.get("PS2_TEX", "128"))       # their raccoon uses 64; faces of real-looking people need a bit more
LEVELS = 23
SCANLINE = 0.94          # one row in four, very light
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


# ------------------------------------------------------------------ Blender side

def _snap_group():
    import bpy
    ng = bpy.data.node_groups.get("ps2_snap")
    if ng:
        return ng
    ng = bpy.data.node_groups.new("ps2_snap", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Camera", in_out="INPUT", socket_type="NodeSocketObject")
    ng.interface.new_socket("Step", in_out="INPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gin, gout = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    oi = N.new("GeometryNodeObjectInfo")
    oi.transform_space = "RELATIVE"                  # the camera in this object's own space
    L.new(gin.outputs["Camera"], oi.inputs["Object"])
    inv = N.new("FunctionNodeInvertMatrix")
    L.new(oi.outputs["Transform"], inv.inputs["Matrix"])
    to_cam = N.new("FunctionNodeTransformPoint")
    L.new(N.new("GeometryNodeInputPosition").outputs["Position"], to_cam.inputs["Vector"])
    L.new(inv.outputs["Matrix"], to_cam.inputs["Transform"])
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(to_cam.outputs["Vector"], sep.inputs["Vector"])

    def math(op, a, b=None):
        m = N.new("ShaderNodeMath")
        m.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[i].default_value = v
            else:
                L.new(v, m.inputs[i])
        return m.outputs[0]

    depth = math("MAXIMUM", math("MULTIPLY", sep.outputs["Z"], -1.0), 0.02)    # the camera looks down -Z

    def snap(axis):                                  # x/depth onto the pixel grid, then back to camera space
        q = math("ROUND", math("DIVIDE", math("DIVIDE", axis, depth), gin.outputs["Step"]))
        return math("MULTIPLY", math("MULTIPLY", q, gin.outputs["Step"]), depth)

    comb = N.new("ShaderNodeCombineXYZ")
    L.new(snap(sep.outputs["X"]), comb.inputs["X"])
    L.new(snap(sep.outputs["Y"]), comb.inputs["Y"])
    L.new(sep.outputs["Z"], comb.inputs["Z"])
    back = N.new("FunctionNodeTransformPoint")
    L.new(comb.outputs["Vector"], back.inputs["Vector"])
    L.new(oi.outputs["Transform"], back.inputs["Transform"])
    sp = N.new("GeometryNodeSetPosition")
    L.new(gin.outputs["Geometry"], sp.inputs["Geometry"])
    L.new(back.outputs["Vector"], sp.inputs["Position"])
    L.new(sp.outputs["Geometry"], gout.inputs["Geometry"])
    return ng


def _add_snap(ob, cam):
    import bpy
    ng = _snap_group()
    mod = ob.modifiers.new("ps2_snap", "NODES")
    mod.node_group = ng
    ids = {it.name: it.identifier for it in ng.interface.items_tree if getattr(it, "in_out", "") == "INPUT"}
    # Blender 5.2 keeps node modifier inputs in mod.properties.inputs (older versions used mod["Socket_n"])
    getattr(mod.properties.inputs, ids["Camera"]).value = cam
    # one low-res pixel in tan units: the 36 mm sensor spans the frame's long side (480 px) for a portrait frame,
    # so the step follows the lens as the shots cut. A plain expression, so it runs without Python drivers.
    fc = ob.driver_add(f'modifiers["{mod.name}"].properties.inputs.{ids["Step"]}.value')
    drv = fc.driver
    drv.type = "SCRIPTED"
    v = drv.variables.new()
    v.name, v.type = "lens", "SINGLE_PROP"
    v.targets[0].id_type = "CAMERA"
    v.targets[0].id = cam.data
    v.targets[0].data_path = "lens"
    drv.expression = f"{36.0 / H:.6f} / lens"


def _shrink_textures():
    import bpy
    done = {}
    for m in bpy.data.materials:
        if not m.use_nodes or not m.node_tree:
            continue
        for n in m.node_tree.nodes:
            if n.type != "TEX_IMAGE" or not n.image:
                continue
            n.interpolation = "Closest"
            img = n.image
            if img.name not in done:
                w, h = img.size
                if max(w, h) > TEX:
                    small = img.copy()
                    k = TEX / max(w, h)
                    small.scale(max(1, round(w * k)), max(1, round(h * k)))
                    done[img.name] = small
                else:
                    done[img.name] = img
            n.image = done[img.name]


def apply(cam, lowpoly=True, wobble=True, hair_thicken=2.2):
    """Turn the built scene into the console look. Call after characters, props, lights and camera exist and
    after render_settings (this overrides the resolution)."""
    import bpy
    scene = bpy.context.scene
    r = scene.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
    r.filter_size = 0.6                             # crisper edges than the 1.5 px default at this size
    _shrink_textures()
    for ob in list(scene.objects):
        if ob.type == "MESH":
            me = ob.data
            rigged = any(md.type == "ARMATURE" for md in ob.modifiers)
            if lowpoly:
                if rigged and len(me.polygons) > 800:
                    d = ob.modifiers.new("ps2_lowpoly", "DECIMATE")
                    d.decimate_type, d.iterations = "UNSUBDIV", 1
                elif not rigged and len(me.polygons) > 3000:
                    d = ob.modifiers.new("ps2_lowpoly", "DECIMATE")
                    d.decimate_type, d.ratio = "COLLAPSE", 0.25
                me.polygons.foreach_set("use_smooth", [False] * len(me.polygons))
                me.update()
            if wobble and len(me.polygons) > 0:
                _add_snap(ob, cam)
        elif ob.type == "CURVES" and hair_thicken and "radius" in ob.data.attributes:
            att = ob.data.attributes["radius"]
            import numpy as np
            v = np.zeros(len(att.data), dtype=np.float32)
            att.data.foreach_get("value", v)
            att.data.foreach_set("value", v * hair_thicken)     # chunky locks, not fuzz, at 270 x 480


# ------------------------------------------------------------------ Python side

def post(src, dst):
    """270 x 480 frame -> 23 levels with a 4x4 Bayer dither -> 4x with no smoothing -> light scanlines."""
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(src).convert("RGB"), dtype=np.float32) / 255.0
    h, w = a.shape[:2]
    t = (np.tile(np.array(BAYER, dtype=np.float32), (h // 4 + 1, w // 4 + 1))[:h, :w] + 0.5) / 16.0
    q = np.floor(a * (LEVELS - 1) + t[..., None]) / (LEVELS - 1)
    big = np.repeat(np.repeat(q, SCALE, axis=0), SCALE, axis=1)
    big[SCALE - 1::SCALE] *= SCANLINE
    Image.fromarray(np.clip(big * 255.0 + 0.5, 0, 255).astype(np.uint8)).save(dst, compress_level=1)


def post_dir(src_dir, dst_dir, frames):
    """frames: 0-based frame numbers; files are f_00001.png style, as bkit.render writes them."""
    os.makedirs(dst_dir, exist_ok=True)
    for F in frames:
        name = f"f_{F + 1:05d}.png"
        post(os.path.join(src_dir, name), os.path.join(dst_dir, name))
