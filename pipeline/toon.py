"""Cel-shaded cartoon kit for Blender (the @aiwithmax look in ops/style.md): flat colors with one hard shadow step, thick dark
outlines from an inverted hull, chunky bevelled parts, hanging signs. Eevee, no textures, so it renders fast.
"""
import math
import bmesh
import bpy
from mathutils import Vector
import bkit as B

INK = (0.015, 0.018, 0.035)
LINE = 0.012        # outline width in metres, at the kit's human-sized scale
_mats = {}

def _linear(color):
    """Palette values are written as they should look on screen (sRGB)."""
    return tuple(x ** 2.2 for x in color)

def toon(color, shade=0.62):
    """Lit color above the ramp's step, the same color darkened and cooled below it."""
    key = (tuple(color), shade)
    if key in _mats:
        return _mats[key]
    color = _linear(color)
    m = bpy.data.materials.new(f"toon{len(_mats)}")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    d = n.new("ShaderNodeBsdfDiffuse")
    d.inputs[0].default_value = (1, 1, 1, 1)        # the ramp reads the light alone, not the object's color
    s2r = n.new("ShaderNodeShaderToRGB")
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (color[0] * shade, color[1] * shade, min(1.0, color[2] * shade * 1.15), 1)
    ramp.color_ramp.elements[1].position = 0.28
    ramp.color_ramp.elements[1].color = (*color, 1)
    e = n.new("ShaderNodeEmission")
    o = n.new("ShaderNodeOutputMaterial")
    l.new(d.outputs[0], s2r.inputs[0])
    l.new(s2r.outputs[0], ramp.inputs[0])
    l.new(ramp.outputs[0], e.inputs[0])
    l.new(e.outputs[0], o.inputs[0])
    _mats[key] = m
    return m

def flat(color):
    key = ("flat", tuple(color))
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(f"flat{len(_mats)}")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    e = n.new("ShaderNodeEmission")
    e.inputs[0].default_value = (*_linear(color), 1)
    l.new(e.outputs[0], n.new("ShaderNodeOutputMaterial").inputs[0])
    _mats[key] = m
    return m

def _outline_mat():
    if "line" not in _mats:
        m = flat(INK).copy()
        m.use_backface_culling = True
        _mats["line"] = m
    return _mats["line"]

def _finish(ob, color, parent, loc, rot, bevel, line):
    ob.data.materials.append(toon(color))
    ob.data.materials.append(_outline_mat())
    B.link(ob)
    if bevel:
        b = ob.modifiers.new("b", "BEVEL")
        b.width, b.segments, b.limit_method = bevel, 3, "ANGLE"
        ob.data.polygons.foreach_set("use_smooth", [True] * len(ob.data.polygons))
        ob.data.update()
    if line:
        s = ob.modifiers.new("line", "SOLIDIFY")
        s.thickness, s.offset, s.use_flip_normals, s.use_rim, s.material_offset = line, 1.0, True, False, 1
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = rot
    return ob

def _mesh(name, make):
    bm = bmesh.new()
    make(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new(name, me)

def box(name, size, color, loc=(0, 0, 0), parent=None, rot=(0, 0, 0), bevel=0.02, line=LINE):
    def make(bm):
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    return _finish(_mesh(name, make), color, parent, loc, rot, min(bevel, min(size) * 0.45), line)

def cyl(name, r, h, color, loc=(0, 0, 0), parent=None, rot=(0, 0, 0), bevel=0.0, line=LINE, seg=48, r2=None):
    def make(bm):
        bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
    ob = _mesh(name, make)
    ob = _finish(ob, color, parent, loc, rot, bevel, line)
    return ob

def ball(name, r, color, loc=(0, 0, 0), parent=None, squash=(1, 1, 1), line=LINE):
    def make(bm):
        bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=20, radius=r)
        for v in bm.verts:
            v.co = Vector((v.co.x * squash[0], v.co.y * squash[1], v.co.z * squash[2]))
    ob = _finish(_mesh(name, make), color, parent, loc, (0, 0, 0), 0, line)
    ob.data.polygons.foreach_set("use_smooth", [True] * len(ob.data.polygons))
    ob.data.update()
    return ob

def empty(name, loc=(0, 0, 0), parent=None):
    ob = B.link(bpy.data.objects.new(name, None))
    ob.parent = parent
    ob.location = loc
    return ob

FONT = None
def label(name, text, size, color=INK, loc=(0, 0, 0), parent=None, font="C:/Windows/Fonts/impact.ttf"):
    """Flat text facing -y, centred on loc."""
    global FONT
    if FONT is None:
        FONT = bpy.data.fonts.load(font)
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = text
    cu.font = FONT
    cu.size = size
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    ob = B.link(bpy.data.objects.new(name, cu))
    ob.data.materials.append(flat(color))
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = (math.pi / 2, 0, 0)
    return ob

def sign(name, lines, loc, w=1.5, h=None, head=None, parent=None, cords=2.5):
    """A hanging card: an optional orange header strip, then big lines of text. Returns its root, placed at its centre."""
    h = h or 0.34 * len(lines) + 0.22 + (0.22 if head else 0)
    root = empty(name, loc, parent)
    box(name + "c", (w, 0.05, h), (0.98, 0.96, 0.88), (0, 0, 0), root, bevel=0.03).data.materials[0] = flat((0.98, 0.96, 0.88))
    top = h / 2 - 0.08
    if head:
        box(name + "h", (w - 0.02, 0.06, 0.22), (0.95, 0.42, 0.13), (0, -0.006, h / 2 - 0.125), root, bevel=0.02, line=0)
        label(name + "ht", head, 0.15, (0.99, 0.97, 0.9), (0, -0.05, h / 2 - 0.13), root)
        top = h / 2 - 0.26
    for i, s in enumerate(lines):
        label(f"{name}t{i}", s, 0.27, INK, (0, -0.04, top - 0.17 - i * 0.33), root)
    for x in (-w * 0.32, w * 0.32):
        box(name + f"cord{x}", (0.018, 0.018, cords), (0.1, 0.1, 0.12), (x, 0, h / 2 + cords / 2), root, bevel=0, line=0)
    return root

def mascot(name, color=(0.97, 0.74, 0.12)):
    """Our cast: a square tape measure with a metal tongue, angry brows, a teeth grille and stubby limbs. z=0 at the feet."""
    root = empty(name)
    body = empty(name + "b", (0, 0, 0.30), root)
    box(name + "case", (0.56, 0.42, 0.50), color, (0, 0, 0.25), body, bevel=0.06)
    cyl(name + "dial", 0.14, 0.02, (0.13, 0.14, 0.17), (0.31 * 0, 0.215, 0.27), body, rot=(math.pi / 2, 0, 0), line=0)
    box(name + "tongue", (0.13, 0.26, 0.012), (0.82, 0.84, 0.86), (-0.34, -0.10, 0.08), body, bevel=0.002, line=0.006)
    box(name + "tip", (0.135, 0.02, 0.05), (0.92, 0.25, 0.14), (-0.34, -0.235, 0.075), body, bevel=0.004, line=0.006)
    parts = {"root": root, "body": body}
    for s, k in ((-1, "L"), (1, "R")):
        ball(name + "eye" + k, 0.062, (0.99, 0.98, 0.94), (s * 0.13, -0.215, 0.33), body, squash=(1, 0.35, 1), line=0.006)
        ball(name + "pup" + k, 0.03, INK, (s * 0.12, -0.236, 0.32), body, squash=(1, 0.3, 1), line=0)
        brow = empty(name + "br" + k, (s * 0.13, -0.235, 0.41), body)
        box(name + "brow" + k, (0.17, 0.02, 0.04), INK, (0, 0, 0), brow, bevel=0.005, line=0)
        parts["brow" + k] = brow
        arm = empty(name + "arm" + k, (s * 0.30, 0, 0.30), body)
        box(name + "armb" + k, (0.14, 0.11, 0.09), (0.85, 0.5, 0.1), (s * 0.08, 0, 0), arm, bevel=0.03)
        parts["arm" + k] = arm
        leg = empty(name + "leg" + k, (s * 0.14, 0, 0.30), root)
        box(name + "legb" + k, (0.13, 0.15, 0.30), (0.85, 0.5, 0.1), (0, 0, -0.15), leg, bevel=0.03)
        parts["leg" + k] = leg
    box(name + "mouth", (0.20, 0.016, 0.075), INK, (0, -0.214, 0.17), body, bevel=0.01, line=0)
    for i in range(3):
        box(f"{name}tooth{i}", (0.03, 0.006, 0.05), (0.97, 0.96, 0.9), (-0.06 + i * 0.06, -0.224, 0.17), body, bevel=0.002, line=0)
    return parts

def mood(p, angry=1.0):
    """1 = angry brows, -1 = sad ones."""
    p["browL"].rotation_euler = (0, 0.42 * angry, 0)
    p["browR"].rotation_euler = (0, -0.42 * angry, 0)

def setup_world(color=(0.3, 0.3, 0.33)):
    w = bpy.data.worlds.new("w")
    B.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (*color, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.35
    B.sun("key", 245, 42, 6.0, angle_deg=1.0)

def flat_look():
    B.scene.view_settings.view_transform = "Standard"
    B.scene.view_settings.look = "None"
