"""Game-cutscene kit, Blender side (the @zeromrrclub look Austin asked for on Nov 22, built in code from Nov 24):
MakeHuman characters from vendor/cutscene_chars (cutscene_chars.py builds them), restyled as mid-2000s console
cutscene people, seated at a table on a patio in golden-hour light with leaf shadows.

blender -b --factory-startup -P cutscene_scene.py -- timing.json out_dir MODE   (MODE: 'all', 1-based frames, 'look')

timing.json (written by the render script): fps, duration, "cast" [{name, seat}], "shots" [{t0, cam}], and per
character "acts" (talk spans with mouth curves, looks, expressions).
"""
import json, math, os, random, sys
import bpy
from mathutils import Vector, Matrix, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bkit as B
import assets as A

CHAR_DIR = os.path.join(HERE, "vendor", "cutscene_chars")
EYE_DIR = os.path.join(HERE, "vendor", "blender_user", "extensions", ".user", "user_default", "mpfb", "data", "eyes",
                       "materials")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TIMING, OUT, MODE = (argv + [None, None, None])[:3]
OUT = os.path.abspath(OUT) if OUT else OUT        # Blender resolves a relative path against the drive root
T = json.load(open(TIMING)) if TIMING else {"fps": 30, "duration": 1.0}
FPS = T["fps"]
NF = max(1, int(round(T["duration"] * FPS)))
B.clear_scene()
scene = B.scene

TABLE_H = 0.76            # table top height (m)
SEAT_HIP = 0.54           # hip joint height when seated
TABLE_GAP = 0.20          # from a seated character's spine to the table's near edge


def hexc(s):
    def lin(v):
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return tuple(lin(int(s[i:i + 2], 16) / 255) for i in (0, 2, 4))


# ------------------------------------------------------------------ materials

def pbr_texture(name, asset, tile, rough_mul=1.0, tint=None):
    """Poly Haven texture set on a Principled BSDF, tiled every `tile` metres (object coordinates)."""
    maps = A.texture_maps(asset)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / tile, 1 / tile, 1 / tile)
    nt.links.new(tc.outputs["Object"], mp.inputs[0])

    def img(key, non_color=False):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(maps[key], check_existing=True)
        t.projection = "BOX"
        t.projection_blend = 0.2
        if non_color:
            t.image.colorspace_settings.name = "Non-Color"
        nt.links.new(mp.outputs[0], t.inputs[0])
        return t
    col = img("Diffuse").outputs[0]
    if tint:
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        mix.inputs[7].default_value = (*tint, 1)
        nt.links.new(col, mix.inputs[6])
        col = mix.outputs[2]
    nt.links.new(col, b.inputs["Base Color"])
    r = img("Rough", True).outputs[0]
    if rough_mul != 1.0:
        mm = nt.nodes.new("ShaderNodeMath")
        mm.operation = "MULTIPLY"
        mm.inputs[1].default_value = rough_mul
        nt.links.new(r, mm.inputs[0])
        r = mm.outputs[0]
    nt.links.new(r, b.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(img("nor_gl", True).outputs[0], nm.inputs["Color"])
    nt.links.new(nm.outputs[0], b.inputs["Normal"])
    return m


def plain(name, color, rough=0.45, metal=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    return m


def _bsdf(m):
    return next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)


def _grade_texture(m, sat=1.0, val=1.0, tint=None):
    """Put a hue/saturation and a multiply between a MakeHuman material's diffuse texture and its BSDF."""
    nt = m.node_tree
    b = _bsdf(m)
    link = next((l for l in nt.links if l.to_node == b and l.to_socket.name == "Base Color"), None)
    if link is None:
        return
    src = link.from_socket
    hs = nt.nodes.new("ShaderNodeHueSaturation")
    hs.inputs["Saturation"].default_value = sat
    hs.inputs["Value"].default_value = val
    nt.links.new(src, hs.inputs["Color"])
    out = hs.outputs[0]
    if tint:
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        mix.inputs[7].default_value = (*tint, 1)
        nt.links.new(out, mix.inputs[6])
        out = mix.outputs[2]
    nt.links.new(out, b.inputs["Base Color"])


def _soften(m, size=256):
    """Shrink a material's diffuse image in memory: pores and blotches go, the console-era smooth skin stays."""
    for n in m.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image and n.name == "diffuseTexture" and n.image.size[0] > size:
            img = n.image.copy()
            img.scale(size, size)
            n.image = img
            n.interpolation = "Cubic"


def _chestnut(m, colors=None):
    """Recolour hair from its texture's brightness: dark roots, warm mid-browns, golden highlights. Works on any
    stock colour (the layered cut ships hot pink)."""
    nt = m.node_tree
    bsdf = _bsdf(m)
    link = next((l for l in nt.links if l.to_node == bsdf and l.to_socket.name == "Base Color"), None)
    if link is None:
        return
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    nt.links.new(link.from_socket, bw.inputs[0])
    gam = nt.nodes.new("ShaderNodeMath")                       # spread the texture's narrow value range
    gam.operation = "MULTIPLY_ADD"
    gam.inputs[1].default_value = 3.4
    gam.inputs[2].default_value = 0.02
    gam.use_clamp = True
    nt.links.new(bw.outputs[0], gam.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cols = colors or ["120a05", "3b1d0d", "7a4422", "c08a55"]
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (*hexc(cols[0]), 1)
    els[1].position, els[1].color = 1.0, (*hexc(cols[-1]), 1)
    for i, c in enumerate(cols[1:-1]):
        e = els.new((i + 1) / (len(cols) - 1))
        e.color = (*hexc(c), 1)
    nt.links.new(gam.outputs[0], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], bsdf.inputs["Base Color"])


def _stubble(m, density, scalp, hair_col="1c120c"):
    """Five-o'clock shadow and a dark scalp from the 'beard' and 'scalp' attributes cutscene_hair.py writes: the skin
    goes greyer and darker under a fine grain stuck to the UVs, and the scalp takes the hair colour so gaps between
    strands don't show pink."""
    nt = m.node_tree
    b = _bsdf(m)
    link = next((l for l in nt.links if l.to_node == b and l.to_socket.name == "Base Color"), None)
    if link is None:
        return
    src = link.from_socket

    def attr(name):
        a = nt.nodes.new("ShaderNodeAttribute")
        a.attribute_type = "GEOMETRY"
        a.attribute_name = name
        return a.outputs["Fac"]

    def math_node(op, a, bval):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        nt.links.new(a, n.inputs[0])
        if isinstance(bval, float):
            n.inputs[1].default_value = bval
        else:
            nt.links.new(bval, n.inputs[1])
        return n.outputs[0]

    uv = nt.nodes.new("ShaderNodeTexCoord")
    grain = nt.nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 4000.0                  # about 0.7 mm: a grain, not sandpaper
    grain.inputs["Detail"].default_value = 1.0
    nt.links.new(uv.outputs["UV"], grain.inputs["Vector"])
    rng = nt.nodes.new("ShaderNodeMapRange")
    rng.inputs["From Min"].default_value, rng.inputs["From Max"].default_value = 0.4, 0.6
    rng.inputs["To Min"].default_value, rng.inputs["To Max"].default_value = 0.6, 1.0
    nt.links.new(grain.outputs["Fac"], rng.inputs["Value"])
    amt = math_node("MULTIPLY", math_node("MULTIPLY", attr("beard"), rng.outputs[0]), float(density) * 0.75)
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[7].default_value = (*hexc("2f2c31"), 1)            # blue-grey: shaved dark hair under the skin
    nt.links.new(amt, mix.inputs["Factor"])
    nt.links.new(src, mix.inputs[6])
    out = mix.outputs[2]
    if scalp:
        mix2 = nt.nodes.new("ShaderNodeMix")
        mix2.data_type = "RGBA"
        mix2.inputs[7].default_value = (*hexc(hair_col), 1)
        nt.links.new(math_node("MULTIPLY", attr("scalp"), float(scalp)), mix2.inputs["Factor"])
        nt.links.new(out, mix2.inputs[6])
        out = mix2.outputs[2]
    nt.links.new(out, b.inputs["Base Color"])


def restyle(ch, skin_tint=(1.0, 0.93, 0.86), brow=0.28):
    """The game look: warm, slightly glossy 'plastic' skin, heavy dark brows, clean saturated clothes."""
    st = ch["style"]
    skin_tint = tuple(st.get("skin_tint", skin_tint))
    skin_sat = st.get("skin_sat", 1.05)
    for ob in [ch["body"]] + ch["parts"]:
        for slot in ob.material_slots:
            m = slot.material
            if not m or not m.node_tree:
                continue
            b = _bsdf(m)
            low = ob.name.lower()
            if ob is ch["body"]:
                _soften(m)
                _grade_texture(m, sat=skin_sat, val=1.0, tint=skin_tint)
                if st.get("stubble") or st.get("scalp"):
                    _stubble(m, st.get("stubble", 0.0), st.get("scalp", 0.0))
                b.inputs["Roughness"].default_value = 0.42
                b.inputs["Specular IOR Level"].default_value = 0.55
                b.inputs["Coat Weight"].default_value = 0.12
                b.inputs["Coat Roughness"].default_value = 0.35
                b.inputs["Subsurface Weight"].default_value = 0.06
                b.inputs["Subsurface Scale"].default_value = 0.004
            elif "eyebrow" in low:
                _grade_texture(m, sat=0.8, val=brow)
            elif "eyelash" in low:
                _grade_texture(m, val=0.3)
            elif "low-poly" in low or "high-poly" in low:
                if st.get("eyes"):                                   # another stock iris (blue, lightblue, ice, green...)
                    path = os.path.join(EYE_DIR, f"{st['eyes']}_eye.png")
                    tex = next((n for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image), None)
                    if tex and os.path.exists(path):
                        tex.image = bpy.data.images.load(path, check_existing=True)
                _grade_texture(m, val=1.35)                          # brighter whites: dark eyes read as dead
                b.inputs["Roughness"].default_value = 0.15           # wet eyes catch the sun
                b.inputs["Coat Weight"].default_value = 0.6
            elif "teeth" in low or "tongue" in low:
                _grade_texture(m, val=0.85)
            else:                                                     # hair and clothes
                tee = os.environ.get("CUTSCENE_TEE")                 # a printed tee (merch.py texture), Nov 24
                if tee and "t-shirt" in (low + m.name.lower()):
                    for n in m.node_tree.nodes:
                        if n.type == "TEX_IMAGE" and n.image and                                 os.path.basename(n.image.filepath).lower() == "t-shirt_basic.png":
                            n.image = bpy.data.images.load(os.path.abspath(tee), check_existing=True)
                is_hair = "hair" in low or "short0" in low or low.endswith(("bob01", "bob02", "afro01", "long01",
                                                                             "ponytail01", "braid01"))
                if is_hair and st.get("hair") == "gloss":            # hero hair: rich colour and a sheen
                    _chestnut(m, st.get("hair_colors"))
                    b.inputs["Roughness"].default_value = 0.4
                    b.inputs["Specular IOR Level"].default_value = 0.45
                    b.inputs["Specular Tint"].default_value = (*hexc("e0a060"), 1)   # warm highlights, not sky blue
                    b.inputs["Coat Weight"].default_value = 0.0
                    b.inputs["Sheen Weight"].default_value = 0.4
                    b.inputs["Sheen Tint"].default_value = (*hexc("d9a26a"), 1)
                else:
                    _grade_texture(m, sat=1.15, val=0.95)
                    if is_hair:
                        b.inputs["Roughness"].default_value = 0.55


# ------------------------------------------------------------------ characters

def load_char(name):
    """Append every object of a built character; returns {'rig', 'body', 'parts', 'name'}."""
    path = os.path.join(CHAR_DIR, f"{name}.blend")
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = list(src.objects)
    ch = {"rig": None, "body": None, "parts": [], "extras": [], "name": name}
    for ob in dst.objects:
        scene.collection.objects.link(ob)
        if ob.type == "ARMATURE":
            ch["rig"] = ob
        elif ".body" in ob.name:
            ch["body"] = ob
        elif ob.type == "MESH":
            ch["parts"].append(ob)
        else:                                       # strand hair (Curves, parented to the head bone)
            ch["extras"].append(ob)
            if os.environ.get("CUTSCENE_NO_STRANDS") == "1":
                ob.hide_render = True
    for pb in ch["rig"].pose.bones:
        pb.rotation_mode = "QUATERNION"
    ch["style"] = json.loads(ch["body"].get("cutscene_style", "{}") or "{}")
    if ch["extras"]:
        scene.render.hair_type = "STRIP"            # strands get their real width instead of 1-pixel lines
        scene.render.hair_subdiv = 1
    return ch


def point_bone(rig, name, direction):
    """Rotate a pose bone so it points along a world direction (parents must already be posed)."""
    bpy.context.view_layer.update()
    pb = rig.pose.bones[name]
    mw = rig.matrix_world.to_3x3()
    cur = (mw @ (pb.tail - pb.head)).normalized()
    q = cur.rotation_difference(Vector(direction).normalized())
    M = mw @ pb.matrix.to_3x3()
    local = M.inverted() @ q.to_matrix() @ M
    pb.rotation_quaternion = (pb.rotation_quaternion.to_matrix() @ local).to_quaternion()


def seat(ch, x, y, rot_z=0.0, arms="table", lean=0.12, spread=1.0):
    """Sit a character with the hips at (x, y), facing -Y turned by rot_z. arms: 'table' (forearms on the table),
    'crossed' (folded on the table edge) or 'lap'."""
    rig = ch["rig"]
    rest_hip = rig.data.bones["upperleg01.L"].head_local.z
    rig.location = (x, y, SEAT_HIP - rest_hip)
    rig.rotation_euler = (0, 0, rot_z)
    R = Matrix.Rotation(rot_z, 3, "Z")

    def d(v):
        return R @ Vector(v)
    for s in ("L", "R"):
        sx = 1 if s == "L" else -1
        point_bone(rig, f"upperleg01.{s}", d((0.08 * sx, -1, -0.12)))
        point_bone(rig, f"upperleg02.{s}", d((0.06 * sx, -1, -0.04)))
        point_bone(rig, f"lowerleg01.{s}", d((0.02 * sx, -0.08, -1)))
        point_bone(rig, f"lowerleg02.{s}", d((0.02 * sx, -0.08, -1)))
        point_bone(rig, f"foot.{s}", d((0, -1, -0.3)))
    point_bone(rig, "spine05", d((0, -0.1, 1)))
    point_bone(rig, "spine04", d((0, -lean * 0.5, 1)))
    point_bone(rig, "spine03", d((0, -lean, 1)))
    point_bone(rig, "spine02", d((0, -lean, 1)))
    point_bone(rig, "spine01", d((0, -lean * 0.6, 1)))
    point_bone(rig, "neck01", d((0, -0.15, 1)))
    point_bone(rig, "neck02", d((0, -0.1, 1)))
    point_bone(rig, "neck03", d((0, -0.05, 1)))
    point_bone(rig, "head", d((0, 0.02, 1)))
    for s in ("L", "R"):
        sx = 1 if s == "L" else -1
        if arms == "table":
            up = (0.18 * sx * spread, -0.62, -0.76)
            fore = (-0.42 * sx, -0.9, -0.03)
        elif arms == "crossed":
            up = (0.10 * sx, -0.55, -0.83)
            fore = (-0.97 * sx, -0.22, 0.02)
        else:
            up = (0.12 * sx, -0.1, -1)
            fore = (-0.1 * sx, -1, -0.2)
        point_bone(rig, f"upperarm01.{s}", d(up))
        point_bone(rig, f"upperarm02.{s}", d(up))
        point_bone(rig, f"lowerarm01.{s}", d(fore))
        point_bone(rig, f"lowerarm02.{s}", d(fore))
        point_bone(rig, f"wrist.{s}", d((fore[0] * 0.6, fore[1], -0.25)))
    relax_hands(rig)
    bpy.context.view_layer.update()


HAND_CURL = float(os.environ.get("CUTSCENE_CURL", "1.0"))     # sign and size of the finger curl, set by eye


def relax_hands(rig, amount=0.45):
    """Resting hands: each finger joint bends a little more than the one before; the thumb barely."""
    for s in ("L", "R"):
        for fi in range(1, 6):
            for seg, k in ((1, 0.6), (2, 1.0), (3, 0.8)):
                name = f"finger{fi}-{seg}.{s}"
                if name not in rig.pose.bones:
                    continue
                ang = amount * k * HAND_CURL * (0.35 if fi == 1 else 1.0)
                pb = rig.pose.bones[name]
                pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion((1, 0, 0), ang)


EXPRESSIONS = {
    "neutral": {},
    "smile": {"mouthSmileLeft": 0.75, "mouthSmileRight": 0.75, "cheekSquintLeft": 0.35, "cheekSquintRight": 0.35,
              "eyeSquintLeft": 0.2, "eyeSquintRight": 0.2},
    # one corner up, lips pressed, eyes narrowed: the old one (full smile on one side, mouth pulled sideways) read goofy
    "smirk": {"mouthSmileLeft": 0.55, "mouthDimpleLeft": 0.3, "mouthPressLeft": 0.3, "mouthPressRight": 0.3,
              "browDownRight": 0.35, "eyeSquintLeft": 0.3, "eyeSquintRight": 0.4, "cheekSquintLeft": 0.25},
    # the chad's resting face (style "rest"): hooded eyes, low brows, lips set, the faintest corner lift
    "chad": {"eyeSquintLeft": 0.45, "eyeSquintRight": 0.45, "browDownLeft": 0.35, "browDownRight": 0.35,
             "mouthPressLeft": 0.35, "mouthPressRight": 0.35, "mouthSmileLeft": 0.15, "jawForward": 0.12},
    "laugh": {"jawOpen": 0.45, "mouthSmileLeft": 1.0, "mouthSmileRight": 1.0, "cheekSquintLeft": 0.7,
              "cheekSquintRight": 0.7, "eyeSquintLeft": 0.6, "eyeSquintRight": 0.6, "browInnerUp": 0.2},
    "smug": {"mouthSmileLeft": 0.6, "mouthSmileRight": 0.6, "mouthPressLeft": 0.6, "mouthPressRight": 0.6,
             "eyeSquintLeft": 0.55, "eyeSquintRight": 0.55, "browDownLeft": 0.35, "browDownRight": 0.35,
             "eyeLookDownLeft": 0.2, "eyeLookDownRight": 0.2},
    "shock": {"jawOpen": 0.35, "eyeWideLeft": 0.8, "eyeWideRight": 0.8, "browInnerUp": 0.8, "browOuterUpLeft": 0.6,
              "browOuterUpRight": 0.6, "mouthFunnel": 0.2},
    "talk_aa": {"aa_02": 0.8, "jawOpen": 0.25},
    "talk_oh": {"ao_03": 0.8, "jawOpen": 0.15},
}


def face(ch, weights, frame=None, clear=True):
    """Set face shape keys (ARKit units and visemes by name); keyframe them at `frame` if given."""
    kb = ch["body"].data.shape_keys.key_blocks
    names = set(weights)
    if clear:
        names |= {k for e in EXPRESSIONS.values() for k in e}
    for n in names:
        if n in kb:
            kb[n].value = weights.get(n, 0.0)
            if frame is not None:
                kb[n].keyframe_insert("value", frame=frame)


def head_pos(ch):
    rig = ch["rig"]
    bpy.context.view_layer.update()
    pb = rig.pose.bones["head"]
    return rig.matrix_world @ (pb.head + (pb.tail - pb.head) * 0.35)


# ------------------------------------------------------------------ set

def world(color, strength):
    w = bpy.data.worlds.new("world")
    scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*color, 1)
    bg.inputs[1].default_value = strength


def leaf_shadows(sun_dir, center, dist=3.5, size=7.0, seed=3):
    """A big leaf-pattern card between the sun and the set: casts dappled shadows, never seen by the camera."""
    m = bpy.data.materials.new("leaves")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.05, 0.08, 0.03, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 3.0
    vor.inputs["Randomness"].default_value = 1.0
    noi = nt.nodes.new("ShaderNodeTexNoise")
    noi.inputs["Scale"].default_value = 0.7
    noi.inputs["Detail"].default_value = 2.0
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], noi.inputs["Vector"])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    vs = nt.nodes.new("ShaderNodeMath")
    vs.operation = "MULTIPLY"
    vs.inputs[1].default_value = 0.35
    nt.links.new(vor.outputs["Distance"], vs.inputs[0])
    nt.links.new(vs.outputs[0], add.inputs[0])
    nt.links.new(noi.outputs["Fac"], add.inputs[1])
    thr = nt.nodes.new("ShaderNodeMath")
    thr.operation = "GREATER_THAN"
    thr.inputs[1].default_value = 0.76                   # where leaves are: alpha 1 (blocks the sun)
    nt.links.new(add.outputs[0], thr.inputs[0])
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(thr.outputs[0], inv.inputs[1])
    nt.links.new(inv.outputs[0], b.inputs["Alpha"])
    m.surface_render_method = "DITHERED"
    sd = Vector(sun_dir).normalized()
    card = B.mesh_from("leaf_card", B.box(-size / 2, size / 2, -size / 2, size / 2, 0, 0.001), [m])
    card.location = Vector(center) + sd * dist
    card.rotation_euler = sd.to_track_quat("Z", "Y").to_euler()
    card.visible_camera = False
    card.visible_glossy = False
    card.visible_diffuse = False
    return card


def patio(width=8.0):
    """Ground, a stone back wall with dark windows, and a long worn wooden table (front edge toward the camera)."""
    ground = B.mesh_from("ground", B.box(-width, width, -6, 8, -0.02, 0),
                         [pbr_texture("cobble", "cobblestone_floor_04", 1.6, tint=(0.95, 0.88, 0.8))])
    wall_m = pbr_texture("wall", "sandstone_blocks_08", 2.4, tint=(1.0, 0.94, 0.84))
    wall = B.mesh_from("wall", B.box(-width, width, 3.2, 3.5, 0, 6), [wall_m])
    glass = plain("window", hexc("1b2230"), rough=0.08, coat=0.5)
    frame = plain("frame", hexc("2d2620"), rough=0.5)
    for wx in (-2.6, 0.0, 2.6):
        B.mesh_from("win", B.box(wx - 0.55, wx + 0.55, 3.17, 3.2, 1.55, 3.05), [glass])
        B.mesh_from("winframe", B.many(B.box(wx - 0.62, wx + 0.62, 3.15, 3.21, 1.48, 1.55),
                                       B.box(wx - 0.62, wx + 0.62, 3.15, 3.21, 3.05, 3.12),
                                       B.box(wx - 0.62, wx - 0.55, 3.15, 3.21, 1.48, 3.12),
                                       B.box(wx + 0.55, wx + 0.62, 3.15, 3.21, 1.48, 3.12),
                                       B.box(wx - 0.02, wx + 0.02, 3.15, 3.21, 1.55, 3.05)), [frame])
    wood = pbr_texture("tablewood", "wood_table_worn", 0.55, rough_mul=0.8, tint=(1.0, 0.82, 0.64))
    top = B.mesh_from("tabletop", B.box(-1.35, 1.35, -1.25, -0.05, TABLE_H - 0.045, TABLE_H), [wood])
    B.bevel(top, 0.01, segments=2)
    legs = plain("tableleg", hexc("2a221c"), rough=0.6)
    for lx in (-1.25, 1.25):
        for ly in (-1.15, -0.15):
            B.mesh_from("leg", B.box(lx - 0.035, lx + 0.035, ly - 0.035, ly + 0.035, 0, TABLE_H - 0.045), [legs])
    return top


def props_on_table(seat_xs):
    """Cups, a plate, phones and keys in front of the seats (code-built, low-poly, game-like)."""
    cer = plain("ceramic", hexc("efe9e0"), rough=0.25, coat=0.3)
    coffee = plain("coffee", hexc("2a160b"), rough=0.1)
    paper = plain("papercup", hexc("c9a57a"), rough=0.6)
    lid = plain("lid", hexc("f2efe8"), rough=0.4)
    phone_m = plain("phone", hexc("15161a"), rough=0.2, coat=0.6)
    orange = plain("phone2", hexc("e0662a"), rough=0.35, coat=0.4)
    z = TABLE_H
    for i, sx in enumerate(seat_xs):
        if i % 2 == 0:
            B.mesh_from("saucer", B.cyl_z(0.075, z, z + 0.012, sx - 0.22, -0.42, seg=24, r2=0.06), [cer])
            B.mesh_from("cup", B.cyl_z(0.04, z + 0.012, z + 0.085, sx - 0.22, -0.42, seg=20, r2=0.035), [cer])
            B.mesh_from("coffee", B.cyl_z(0.036, z + 0.075, z + 0.078, sx - 0.22, -0.42, seg=20), [coffee])
        else:
            B.mesh_from("papercup", B.cyl_z(0.042, z, z + 0.15, sx + 0.24, -0.38, seg=20, r2=0.05), [paper])
            B.mesh_from("lid", B.cyl_z(0.052, z + 0.15, z + 0.165, sx + 0.24, -0.38, seg=20), [lid])
        ph = B.mesh_from("phone", B.box(-0.037, 0.037, -0.077, 0.077, 0, 0.009), [orange if i == 1 else phone_m])
        B.bevel(ph, 0.006, segments=2)
        ph.location = (sx + (0.18 if i % 2 == 0 else -0.2), -0.68, z)
        ph.rotation_euler = (0, 0, 0.35 * (1 if i % 2 else -1))
    plate = B.mesh_from("plate", B.cyl_z(0.12, z, z + 0.014, 0.05, -0.75, seg=28, r2=0.1), [cer])
    crumbs = plain("crumbs", hexc("8a5a2e"), rough=0.8)
    rng = random.Random(4)
    for _ in range(14):
        a, r = rng.uniform(0, 6.28), rng.uniform(0.0, 0.08)
        cx, cy = 0.05 + r * math.cos(a), -0.75 + r * math.sin(a)
        B.mesh_from("crumb", B.box(cx - 0.003, cx + 0.003, cy - 0.003, cy + 0.003, z + 0.014, z + 0.017), [crumbs])
    napkin = plain("napkin", hexc("f4f1ea"), rough=0.9)
    nap = B.mesh_from("napkin", B.cyl_z(0.05, z, z + 0.05, -0.28, -0.98, seg=7, r2=0.02), [napkin])
    nap.rotation_euler = (0.2, 0.1, 0.4)
    keyring = plain("keys", hexc("b9b9b9"), metal=1.0, rough=0.25)
    fob = plain("fob", hexc("141414"), rough=0.4)
    B.mesh_from("fob", B.box(0.34, 0.40, -1.02, -0.97, z, z + 0.018), [fob])
    B.mesh_from("key", B.box(0.40, 0.47, -1.005, -0.99, z, z + 0.004), [keyring])
    ice = plain("icedcoffee", hexc("b07a4a"), rough=0.1, coat=0.6)
    B.mesh_from("iced", B.cyl_z(0.04, z, z + 0.13, -0.42, -0.55, seg=20, r2=0.048), [ice])
    straw = plain("straw", hexc("1d1d1d"), rough=0.4)
    B.mesh_from("straw", B.cyl_z(0.004, z + 0.1, z + 0.24, -0.41, -0.55, seg=8), [straw])


def blob(name, center, radii, mat, seg=24, rot=(0, 0, 0)):
    """A squashed sphere (turkey, food, pie filling): code-built, smooth-shaded."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=seg, ring_count=seg // 2, location=center, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = radii
    ob.data.materials.append(mat)
    for poly in ob.data.polygons:
        poly.use_smooth = True
    return ob


def friendsgiving_props(seat_xs):
    """Friendsgiving on the patio (Nov 24): a roast turkey on a platter in the middle, a pumpkin pie, a plate of food in
    front of every seat, and phones (the 'look it up' beat needs one in reach)."""
    z = TABLE_H
    cx = sum(seat_xs) / len(seat_xs)
    cer = plain("ceramic", hexc("efe9e0"), rough=0.25, coat=0.3)
    roast = plain("roast", hexc("8e4a1a"), rough=0.32, coat=0.55)
    bone = plain("bone", hexc("efe6d2"), rough=0.5)
    crust = plain("crust", hexc("c98f4c"), rough=0.6)
    pumpkin = plain("pumpkin", hexc("b85a1c"), rough=0.4, coat=0.2)
    mash = plain("mash", hexc("f1e6c8"), rough=0.7)
    stuffing = plain("stuffing", hexc("9a6a34"), rough=0.85)
    cran = plain("cranberry", hexc("8a1424"), rough=0.2, coat=0.5)
    slice_m = plain("turkeyslice", hexc("d9b48a"), rough=0.6)
    phone_m = plain("phone", hexc("15161a"), rough=0.2, coat=0.6)
    ty = -0.62
    B.mesh_from("platter", B.cyl_z(0.21, z, z + 0.016, cx, ty, seg=40, r2=0.19), [cer])
    blob("turkey", (cx, ty, z + 0.09), (0.16, 0.12, 0.085), roast)
    for sx in (-1, 1):
        blob("drum", (cx + 0.1 * sx, ty - 0.1, z + 0.07), (0.075, 0.04, 0.038), roast, rot=(0, 0, 0.7 * sx))
        blob("knob", (cx + 0.15 * sx, ty - 0.155, z + 0.075), (0.016, 0.016, 0.016), bone, seg=12)
    px = cx + 0.62
    B.mesh_from("pie", B.cyl_z(0.12, z, z + 0.036, px, -0.5, seg=36, r2=0.1), [crust])
    B.mesh_from("piefill", B.cyl_z(0.105, z + 0.03, z + 0.038, px, -0.5, seg=36), [pumpkin])
    for i, sx in enumerate(seat_xs):
        y = -0.36
        B.mesh_from("plate", B.cyl_z(0.12, z, z + 0.014, sx, y, seg=32, r2=0.1), [cer])
        blob("mash", (sx - 0.035, y + 0.01, z + 0.025), (0.04, 0.035, 0.022), mash, seg=16)
        blob("stuffing", (sx + 0.04, y + 0.02, z + 0.022), (0.04, 0.03, 0.02), stuffing, seg=12)
        blob("cran", (sx + 0.005, y - 0.05, z + 0.017), (0.022, 0.018, 0.01), cran, seg=12)
        B.mesh_from("slice", B.box(sx - 0.06, sx + 0.0, y - 0.03, y + 0.0, z + 0.014, z + 0.022), [slice_m])
        if i % 2 == 0:
            ph = B.mesh_from("phone", B.box(-0.037, 0.037, -0.077, 0.077, 0, 0.009), [phone_m])
            B.bevel(ph, 0.006, segments=2)
            ph.location = (sx + 0.2, -0.62, z)
            ph.rotation_euler = (0, 0, -0.35)


def golden_hour(az=232, el=19, strength=3.8):
    world(hexc("9fb2cc"), 1.0)                        # blue sky fill from everywhere
    s = B.sun("sun", azimuth_deg=az, elevation_deg=el, strength=strength, color=hexc("ffc690"), angle_deg=2.2)
    az_r, el_r = math.radians(az), math.radians(el)
    to_sun = Vector((math.cos(el_r) * math.cos(az_r), math.cos(el_r) * math.sin(az_r), math.sin(el_r)))
    return s, to_sun


def cam_on(cam, target, offset, lens, fstop=5.6):
    cam.data.lens = lens
    cam.data.dof.aperture_fstop = fstop
    loc = Vector(target) + Vector(offset)
    B.aim(cam, loc, target)
    cam.data.dof.focus_distance = (Vector(target) - loc).length


# ------------------------------------------------------------------ look test

def look_test():
    names = T.get("cast", ["suit", "jacket", "overalls"])
    seat_xs = [-0.6, 0.0, 0.6][:len(names)]
    patio()
    props_on_table(seat_xs)
    chars = []
    for i, (n, sx) in enumerate(zip(names, seat_xs)):
        ch = load_char(n)
        restyle(ch)
        seat(ch, sx, 0.15, rot_z=math.radians([-12, 0, 12][i]), arms=["crossed", "table", "table"][i])
        chars.append(ch)
    sun, to_sun = golden_hour()
    leaf_shadows(to_sun, (0, 1.5, 1.4))
    cam = B.camera(lens=35, fstop=5.6)
    B.area("fill", (1.6, -1.6, 1.4), (0, 0.15, 1.15), 1.4, 28, color=hexc("dfe6ff"))       # cool sky bounce, side-on
    B.area("rim", (-1.2, 1.6, 2.2), (0, 0.15, 1.3), 0.8, 60, color=hexc("ffc890"))      # warm edge on hair and shoulders
    B.render_settings(FPS, samples=32, motion_blur=0, look="AgX - Medium High Contrast")
    shots = {
        "wide": (Vector((0, 0.15, 1.08)), (0, -1.85, 0.12), 22),
        "single": (head_pos(chars[1]) + Vector((0, 0, -0.1)), (0.14, -1.2, 0.04), 55),
    }
    for name, (tgt, off, lens) in shots.items():
        cam_on(cam, tgt, off, lens)
        scene.render.filepath = os.path.join(OUT, f"look_{name}.png")
        bpy.ops.render.render(write_still=True)
    if os.environ.get("CUTSCENE_FACES") == "1":                 # expression sheet of the middle character
        tgt, off, lens = shots["single"]
        cam_on(cam, tgt + Vector((0, 0, 0.06)), (0.1, -0.85, 0.02), 70)
        for e in EXPRESSIONS:
            face(chars[1], EXPRESSIONS[e])
            scene.render.filepath = os.path.join(OUT, f"face_{e}.png")
            bpy.ops.render.render(write_still=True)


# ------------------------------------------------------------------ episode: motion from timing.json

HEAD_BONES = ("neck02", "head")
BODY_BONES = ("spine02", "spine01")
MOUTH_KEYS = ("jawOpen", "aa_02", "ow_08", "y_iy_ih_ix_06", "p_b_m_21", "mouthClose")
SHAPE_KEYS = {"aa": "aa_02", "oh": "ow_08", "ee": "y_iy_ih_ix_06"}


def _smooth(vals, tau, fps):
    """One-pole smoothing run both ways and averaged, so heads ease instead of snapping."""
    k = 1 - math.exp(-1 / (tau * fps))
    fwd, v = [], vals[0]
    for x in vals:
        v += (x - v) * k
        fwd.append(v)
    back, v = [], fwd[-1]
    for x in reversed(fwd):
        v += (x - v) * k
        back.append(v)
    return [(a + b) / 2 for a, b in zip(fwd, reversed(back))]


def _noise(seed, t, rate):
    r = random.Random(seed)
    ph = [r.uniform(0, 6.28) for _ in range(3)]
    return (math.sin(t * rate + ph[0]) + 0.6 * math.sin(t * rate * 2.3 + ph[1])
            + 0.3 * math.sin(t * rate * 4.1 + ph[2])) / 1.9


def _at(events, t):
    """The last [t0, value, ...] event whose t0 <= t, or None."""
    cur = None
    for e in events:
        if e[0] <= t:
            cur = e
        else:
            break
    return cur


def plan_motion(chars, cast):
    """Per frame and per character: head yaw/pitch/roll, body lean and every face key, worked out up front."""
    CH = T["chars"]
    heads = {n: head_pos(chars[n]) for n in chars}
    plan = {}
    for ci, c in enumerate(cast):
        n = c["name"]
        d = CH[n]
        fwd = chars[n]["fwd"]
        yaw_t, pitch_t, eye_t = [], [], []
        for f in range(NF):
            t = f / FPS
            look = _at(d.get("look", []), t)
            target = look[1] if look else "cam"
            if target in heads and target != n:
                v = heads[target] - heads[n]
            elif target == "down":
                v = fwd * 0.5 + Vector((0, 0, -0.6))
            else:                                              # toward the camera side, straight ahead
                v = fwd.copy()
            a = math.atan2(fwd.x * v.y - fwd.y * v.x, fwd.x * v.x + fwd.y * v.y)
            a = max(-0.75, min(0.75, a))
            el = math.atan2(v.z, Vector((v.x, v.y)).length) if (target in heads or target == "down") else 0.0
            yaw_t.append(a * 0.75)
            pitch_t.append(-el * 0.7)
            eye_t.append(a)
        yaw = _smooth(yaw_t, 0.12, FPS)
        pitch = _smooth(pitch_t, 0.15, FPS)
        eyes = _smooth(eye_t, 0.04, FPS)
        mouth, shape = d.get("mouth", [0] * NF), d.get("shape", ["aa"] * NF)
        blinks = d.get("blinks", [])
        exprs = d.get("expr", [])
        frames = []
        rest = chars[n]["style"].get("rest", "neutral")              # the chad's neutral is his chad face
        prev_w, cur_w, t_switch, cur_name = dict(EXPRESSIONS[rest]), dict(EXPRESSIONS[rest]), -10.0, ""
        ei = 0
        for f in range(NF):
            t = f / FPS
            while ei < len(exprs) and exprs[ei][0] <= t:
                u0 = min(1.0, (t - t_switch) / 0.22)
                prev_w = {k: prev_w.get(k, 0) * (1 - u0) + cur_w.get(k, 0) * u0 for k in set(prev_w) | set(cur_w)}
                e = exprs[ei]
                name_e = rest if e[1] == "neutral" else e[1]
                cur_w = {k: v * e[2] for k, v in EXPRESSIONS.get(name_e, {}).items()}
                t_switch, cur_name = e[0], e[1]
                ei += 1
            u = min(1.0, (t - t_switch) / 0.22)
            u = u * u * (3 - 2 * u)
            w = {k: prev_w.get(k, 0) * (1 - u) + cur_w.get(k, 0) * u for k in set(prev_w) | set(cur_w)}
            laughing = cur_name == "laugh" and t - t_switch < 1.8
            m = mouth[f] if f < len(mouth) else 0.0
            if m > 0.02:                                       # talking: the mouth wins over the expression's lips
                for k in ("jawOpen", "mouthPressLeft", "mouthPressRight"):
                    w[k] = w.get(k, 0) * 0.3
                for k in ("mouthSmileLeft", "mouthSmileRight"):
                    w[k] = w.get(k, 0) * 0.6
                sh = shape[f] if f < len(shape) else "aa"
                if sh == "mbp":
                    w["p_b_m_21"] = 0.8
                else:
                    w["jawOpen"] = w.get("jawOpen", 0) + m * 0.38
                    w[SHAPE_KEYS.get(sh, "aa_02")] = 0.35 + 0.55 * m
            if laughing:                                       # a laugh shakes the jaw and the shoulders
                w["jawOpen"] = w.get("jawOpen", 0) + 0.12 * (0.5 + 0.5 * math.sin(t * 2 * math.pi * 5.5))
            bl = 0.0
            for b0 in blinks:
                dt = t - b0
                if 0 <= dt < 0.2:
                    bl = max(bl, 1 - abs(dt - 0.07) / 0.13)
            w["eyeBlinkLeft"] = max(w.get("eyeBlinkLeft", 0), bl)
            w["eyeBlinkRight"] = max(w.get("eyeBlinkRight", 0), bl)
            ey = max(-1.0, min(1.0, (eyes[f] - yaw[f]) * 2.2))
            if ey > 0:      # toward the character's own left: left eye looks out, right eye looks in
                w["eyeLookOutLeft"], w["eyeLookInRight"] = ey * 0.7, ey * 0.7
            else:
                w["eyeLookInLeft"], w["eyeLookOutRight"] = -ey * 0.7, -ey * 0.7
            nod = 0.06 * m * math.sin(t * 2 * math.pi * 2.1 + ci)
            frames.append({
                "keys": w,
                "yaw": yaw[f] + 0.04 * _noise(ci * 7 + 1, t, 0.9),
                "pitch": pitch[f] + nod + 0.025 * _noise(ci * 7 + 2, t, 0.7) + (-0.12 if laughing else 0),
                "roll": 0.03 * _noise(ci * 7 + 3, t, 0.5) + (0.05 * math.sin(t * 2 * math.pi * 5.5) if laughing else 0),
                "lean": 0.015 * math.sin(t * 2 * math.pi / 4.2 + ci) + (-0.08 if laughing else 0)})
        plan[n] = frames
    return plan


def _base(ch):
    rig = ch["rig"]
    bpy.context.view_layer.update()
    mw = rig.matrix_world.to_3x3()
    ch["base_q"] = {b: rig.pose.bones[b].rotation_quaternion.copy() for b in HEAD_BONES + BODY_BONES}
    ch["base_M"] = {b: mw @ rig.pose.bones[b].matrix.to_3x3() for b in HEAD_BONES + BODY_BONES}
    ch["fwd"] = (mw @ Vector((0, -1, 0))).normalized()
    ch["right"] = (mw @ Vector((-1, 0, 0))).normalized()
    ch["pivot"] = {b: rig.matrix_world @ rig.pose.bones[b].head for b in HEAD_BONES + BODY_BONES}
    # strand hair parented to the head bone crashes Blender 5.2 when the pose changes between rendered frames
    # (EXCEPTION_ACCESS_VIOLATION, Nov 24), so in episodes it is unparented at the seated pose and apply_frame moves
    # it with the head itself
    ch["strands"] = []
    for ob in ch.get("extras", []):
        m = ob.matrix_world.copy()
        ob.parent = None
        ob.matrix_world = m
        ch["strands"].append((ob, m))


def _turn(ch, bone, R):
    """Rotate a bone by a world-space rotation R on top of its seated pose."""
    M = ch["base_M"][bone]
    local = M.inverted() @ R @ M
    ch["rig"].pose.bones[bone].rotation_quaternion = (ch["base_q"][bone].to_matrix() @ local).to_quaternion()


def apply_frame(chars, plan, f):
    f = max(0, min(NF - 1, f))
    for n, ch in chars.items():
        p = plan[n][f]
        kb = ch["body"].data.shape_keys.key_blocks
        for k in ch["face_keys"]:
            kb[k].value = 0.0
        for k, v in p["keys"].items():
            if k in kb:
                kb[k].value = max(0.0, min(1.0, v))
        # pitch > 0 tips the head down (a turn about "right" by +a lifts the face, hence the minus; fixed Nov 24
        # after "look down" turned faces to the sky)
        R = (Matrix.Rotation(p["yaw"], 3, "Z") @ Matrix.Rotation(-p["pitch"], 3, ch["right"])
             @ Matrix.Rotation(p["roll"], 3, ch["fwd"])).to_quaternion()
        _turn(ch, "neck02", Quaternion().slerp(R, 0.4).to_matrix())
        _turn(ch, "head", Quaternion().slerp(R, 0.6).to_matrix())
        L = Matrix.Rotation(p["lean"], 3, ch["right"]).to_quaternion()
        _turn(ch, "spine02", L.to_matrix())
        _turn(ch, "spine01", Quaternion().slerp(L, 0.5).to_matrix())
        if ch.get("strands"):
            # the same world rotations the bones just got, each about its seated pivot, parent first
            def G(b, q):
                pv = ch["pivot"][b]
                return Matrix.Translation(pv) @ q.to_matrix().to_4x4() @ Matrix.Translation(-pv)
            Tm = (G("spine02", L) @ G("spine01", Quaternion().slerp(L, 0.5)) @ G("neck02", Quaternion().slerp(R, 0.4))
                  @ G("head", Quaternion().slerp(R, 0.6)))
            for ob, m in ch["strands"]:
                ob.matrix_world = Tm @ m


def plan_camera(chars, cast):
    """Per frame camera (location, aim target, lens) from the shot list, with a slow push inside each shot."""
    heads = {n: head_pos(chars[n]) for n in chars}
    xs = [c["x"] for c in cast]
    shots = T["shots"]
    out = []
    for f in range(NF):
        t = f / FPS
        si = max([i for i, s in enumerate(shots) if s["t0"] <= t] or [0])
        sh = shots[si]
        t1 = shots[si + 1]["t0"] if si + 1 < len(shots) else T["duration"]
        u = (t - sh["t0"]) / max(0.5, t1 - sh["t0"])
        kind, who = sh["cam"], sh.get("who", [])
        push = 1 - 0.035 * u
        if kind == "wide" and max(xs) - min(xs) > 1.2:
            # four across: from just over the table's front edge, looking down a little, 16 mm, so the table fills
            # the bottom of the frame (no legs or cobbles under it) and every head and tag fits the width
            tgt = Vector((sum(xs) / len(xs), 0.15, 1.0))
            off, lens = Vector((0, -1.72, 0.72)) * push, 16
        elif kind == "wide":
            tgt = Vector((sum(xs) / len(xs), 0.15, 1.08))
            off, lens = Vector((0, -1.85, 0.12)) * push, 22
        elif kind in ("two", "group"):
            hs = [heads[w] for w in who]
            tgt = sum(hs, Vector()) / len(hs) + Vector((0, 0, -0.12))
            spread = max(h.x for h in hs) - min(h.x for h in hs)
            k = max(1.0, (spread + 1.1) / 1.3)               # room for shoulders past the outer heads
            off, lens = Vector((0.05, -1.45 * k, 0.05 + 0.08 * (k - 1))) * push, 32
        else:                                             # single / close on one character
            ch = chars[who[0]]
            tgt = heads[who[0]] + Vector((0, 0, -0.16 if kind == "single" else -0.1))
            dist = 1.55 if kind == "single" else 1.3
            off = (ch["fwd"] * dist + Vector((sh.get("side", 0.16), 0, 0.06))) * push
            lens = 50 if kind == "single" else 58
        out.append((tgt + off, tgt, lens))
    return out


def episode():
    cast = T["cast"]
    patio()
    (friendsgiving_props if T.get("props") == "friendsgiving" else props_on_table)([c["x"] for c in cast])
    chars = {}
    for c in cast:
        ch = load_char(c["name"])
        restyle(ch)
        seat(ch, c["x"], c.get("y", 0.15), rot_z=math.radians(c.get("rot", 0)), arms=c.get("arms", "table"))
        _base(ch)
        kb = ch["body"].data.shape_keys.key_blocks
        wanted = set(MOUTH_KEYS) | {k for e in EXPRESSIONS.values() for k in e} | {
            "eyeBlinkLeft", "eyeBlinkRight", "eyeLookOutLeft", "eyeLookInRight", "eyeLookInLeft", "eyeLookOutRight"}
        ch["face_keys"] = [k for k in wanted if k in kb]
        chars[c["name"]] = ch
    sun, to_sun = golden_hour()
    leaf_shadows(to_sun, (0, 1.5, 1.4))
    cam = B.camera(lens=35, fstop=5.6)
    B.area("fill", (1.6, -1.6, 1.4), (0, 0.15, 1.15), 1.4, 28, color=hexc("dfe6ff"))
    B.area("rim", (-1.2, 1.6, 2.2), (0, 0.15, 1.3), 0.8, 60, color=hexc("ffc890"))
    B.render_settings(FPS, samples=int(T.get("samples", 24)), motion_blur=0, look="AgX - Medium High Contrast")
    plan = plan_motion(chars, cast)
    cams = plan_camera(chars, cast)

    def apply_all(f):
        apply_frame(chars, plan, f)
        loc, tgt, lens = cams[max(0, min(NF - 1, f))]
        cam_on(cam, tgt, loc - tgt, lens)

    # 2D anchors for the stat tags: a point above each head, in screen pixels, every frame
    from bpy_extras.object_utils import world_to_camera_view
    anchors = {n: [] for n in chars}
    for f in range(NF):
        apply_all(f)
        bpy.context.view_layer.update()
        for n, ch in chars.items():
            v = world_to_camera_view(scene, cam, head_pos(ch) + Vector((0, 0, 0.19)))
            anchors[n].append([round(v.x * 1080, 1), round((1 - v.y) * 1920, 1)] if v.z > 0 else None)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "anchors.json"), "w") as fh:
        json.dump(anchors, fh)

    def on_frame(scn, depsgraph=None):
        apply_all(scn.frame_current - 1)
    bpy.app.handlers.frame_change_pre.append(on_frame)
    apply_all(0)
    if MODE != "anchors":
        B.render(OUT, MODE, NF)


def portraits():
    """Seated close-ups per character in the patio light, for picking looks. CUTSCENE_PORTRAITS=name,name,...
    CUTSCENE_PORTRAIT_FACES=rest,smirk (expressions; 'rest' is the character's own neutral) and
    CUTSCENE_PORTRAIT_ANGLES=front,34,profile."""
    names = os.environ.get("CUTSCENE_PORTRAITS", "chad").split(",")
    faces = os.environ.get("CUTSCENE_PORTRAIT_FACES", "smirk").split(",")
    angles = os.environ.get("CUTSCENE_PORTRAIT_ANGLES", "front,34").split(",")
    offsets = {"front": (0.05, -1.05, 0.0), "34": (0.6, -0.9, 0.02), "profile": (1.0, -0.12, 0.02),
               "low": (0.25, -0.95, -0.22)}
    patio()
    props_on_table([0.0])
    sun, to_sun = golden_hour()
    leaf_shadows(to_sun, (0, 1.5, 1.4))
    cam = B.camera(lens=60, fstop=4.0)
    B.area("fill", (1.6, -1.6, 1.4), (0, 0.15, 1.15), 1.4, 28, color=hexc("dfe6ff"))
    B.area("rim", (-1.2, 1.6, 2.2), (0, 0.15, 1.3), 0.8, 60, color=hexc("ffc890"))
    B.render_settings(FPS, samples=32, motion_blur=0, look="AgX - Medium High Contrast")
    for n in names:
        ch = load_char(n)
        restyle(ch)
        seat(ch, 0.0, 0.15, arms="table")
        h = head_pos(ch)
        for fe in faces:
            face(ch, EXPRESSIONS[ch["style"].get("rest", "neutral") if fe == "rest" else fe])
            for tag in angles:
                cam_on(cam, h + Vector((0, 0, -0.06)), offsets[tag], 60)
                scene.render.filepath = os.path.join(OUT, f"portrait_{n}_{fe}_{tag}.png")
                bpy.ops.render.render(write_still=True)
        for ob in [ch["rig"], ch["body"]] + ch["parts"] + ch["extras"]:
            bpy.data.objects.remove(ob, do_unlink=True)


def merch_shot():
    """Chad at the table in his printed tee (CUTSCENE_TEE=<texture from merch.py>), framed like the reference's
    single shot where the hero's shirt reads under his caption."""
    patio()
    props_on_table([0.0])
    sun, to_sun = golden_hour()
    leaf_shadows(to_sun, (0, 1.5, 1.4))
    cam = B.camera(lens=50, fstop=4.0)
    B.area("fill", (1.6, -1.6, 1.4), (0, 0.15, 1.15), 1.4, 28, color=hexc("dfe6ff"))
    B.area("rim", (-1.2, 1.6, 2.2), (0, 0.15, 1.3), 0.8, 60, color=hexc("ffc890"))
    B.render_settings(FPS, samples=32, motion_blur=0, look="AgX - Medium High Contrast")
    ch = load_char(os.environ.get("CUTSCENE_MERCH_CHAR", "chad"))
    restyle(ch)
    seat(ch, 0.0, 0.15, arms="table")
    face(ch, EXPRESSIONS[ch["style"].get("rest", "neutral")])
    h = head_pos(ch)
    shots = {"single": (-0.34, (0.1, -1.75, -0.04), 42), "close": (-0.24, (0.06, -1.25, 0.0), 48)}
    for tag, (dz, off, lens) in shots.items():
        cam_on(cam, h + Vector((0, 0, dz)), off, lens, fstop=4.0)
        scene.render.filepath = os.path.join(OUT, f"merch_{tag}.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    if MODE == "merch":
        merch_shot()
    elif MODE == "look":
        look_test()
    elif MODE == "portraits":
        portraits()
    else:
        episode()
