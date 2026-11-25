"""Blender side, called by cutscene_build.py: strand hair and a stubble mask for a MakeHuman body.

Strand hair (spec "strand_hair"): a Curves object grown on the body's 'scalp' vertex group and parented to the head
bone. A few hundred guide strands follow the skull surface (BVH projection) in a combing direction, lifted off the
scalp by a volume profile (a big lift at the front hairline makes the swept-back quiff); thousands of child strands
copy the nearest guide and gather toward its tip (clumps read as locks), with waves along each lock.

Masks (spec "stubble"): float point attributes on the body, read by the skin shader in cutscene_scene.restyle:
  beard   the five-o'clock-shadow area (jaw, chin, upper lip, a little under the chin), soft edges, lips left out
  scalp   where hair grows, so the skin between strands reads dark instead of pink
All positions are in the rest pose with every shape key mixed in, and the landmarks come from the fitted rig, so the
masks follow whatever face the spec builds.
"""
import math
import random
import bpy
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree


def mixed_coords(body):
    """Vertex positions with all shape keys at their current values (rest pose, no armature)."""
    n = len(body.data.vertices)
    kb = body.data.shape_keys.key_blocks
    base = np.empty(n * 3)
    kb[0].data.foreach_get("co", base)
    co = base.copy()
    tmp = np.empty(n * 3)
    for k in kb[1:]:
        if k.value and not k.mute:
            k.data.foreach_get("co", tmp)
            co += k.value * (tmp - base)
    return co.reshape(-1, 3)


def group_weights(body, name):
    w = np.zeros(len(body.data.vertices))
    vg = body.vertex_groups.get(name)
    if vg is None:
        return w
    gi = vg.index
    for v in body.data.vertices:
        for g in v.groups:
            if g.group == gi:
                w[v.index] = g.weight
    return w


def _ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def landmarks(rig, co, body):
    bones = rig.data.bones
    ears = group_weights(body, "ears") > 0.5
    ear_pts = co[ears]
    lm = {
        "chin": Vector(bones["jaw"].tail_local),
        "mouth_z": 0.5 * (bones["oris07.L"].tail_local.z + bones["oris03.L"].tail_local.z),
        "mouth_y": bones["oris03.L"].tail_local.y,
        "nose_z": bones["levator06.L"].head_local.z,
        "eye": Vector(bones["eye.L"].head_local),
        "ear_front_y": float(ear_pts[:, 1].min()) if len(ear_pts) else bones["temporalis02.L"].head_local.y + 0.04,
        "ear_z": float(ear_pts[:, 2].mean()) if len(ear_pts) else bones["eye.L"].head_local.z - 0.01,
    }
    return lm


def hair_region(body, rig, co, spec=None):
    """0..1 per vertex: where hair grows. MakeHuman's 'scalp' group starts high on the forehead, so strand hair
    adds a lower front hairline (spec 'hairline': metres above the eyes, the temples a little higher) and keeps a
    gap around the ears so no strands wrap them."""
    real = group_weights(body, "body") > 0.5
    w = _ss(0.2, 0.8, group_weights(body, "scalp"))
    if spec is None:
        return w * real
    lm = landmarks(rig, co, body)
    x, y, z = np.abs(co[:, 0]), co[:, 1], co[:, 2]
    ze = lm["eye"].z
    zh = ze + spec.get("hairline", 0.06) + 0.014 * np.clip(x / 0.05, 0, 1.6) ** 2
    front = _ss(zh - 0.003, zh + 0.006, z) * (x < 0.085) * (y < lm["eye"].y + 0.07)
    w = np.maximum(w, front)
    # short back: the nape hairline sits about level with the ear lobes, not halfway down the neck
    nape = spec.get("nape", 0.035)
    w = w * np.where(y > lm["ear_front_y"], _ss(lm["ear_z"] - nape - 0.012, lm["ear_z"] - nape, z), 1.0)
    ears = co[group_weights(body, "ears") > 0.5]
    if len(ears):
        near = np.full(len(co), 1.0)
        for chunk in range(0, len(co), 4000):
            d = np.linalg.norm(co[chunk:chunk + 4000, None, :] - ears[None, ::3, :], axis=2).min(axis=1)
            near[chunk:chunk + 4000] = _ss(0.012, 0.024, d)
        w = w * near
    return w * real


def stubble_masks(body, rig, co, hair_spec=None):
    """Write the 'beard' and 'scalp' point attributes onto the body mesh."""
    lm = landmarks(rig, co, body)
    x, y, z = np.abs(co[:, 0]), co[:, 1], co[:, 2]
    zc, ze, zm, zn = lm["chin"].z, lm["eye"].z, lm["mouth_z"], lm["nose_z"]
    ym, year = lm["mouth_y"], lm["ear_front_y"]
    # the cheek line runs from just above the mouth corner back to the sideburn, a little under eye level
    t = np.clip((y - ym) / (year - ym), 0.0, 1.0)
    z_side = (zm + 0.010) + t * ((ze - 0.018) - (zm + 0.010))
    z_line = z_side + (1 - _ss(0.020, 0.032, x)) * ((zn - 0.004) - z_side) * (y < ym + 0.01)   # moustache in the middle
    up = 1 - _ss(z_line - 0.012, z_line + 0.010, z)
    up *= 1 - 0.35 * _ss(zm, ze - 0.02, z) * _ss(0.025, 0.04, x)   # thinner up the cheeks (not the moustache)
    low = _ss(zc - 0.050, zc - 0.022, z)                     # fades out on the throat under the jaw
    back = 1 - _ss(year - 0.018, year - 0.004, y)            # stops in front of the ear
    head = (x < 0.11) & (z > zc - 0.07) & (z < ze)
    lips = _ss(0.25, 0.6, group_weights(body, "lips"))
    real = group_weights(body, "body") > 0.5
    beard = up * low * back * (1 - lips) * head * real
    scalp = hair_region(body, rig, co, hair_spec)
    me = body.data
    for name, vals in (("beard", beard), ("scalp", scalp)):
        if name in me.attributes:
            me.attributes.remove(me.attributes[name])
        a = me.attributes.new(name, "FLOAT", "POINT")
        a.data.foreach_set("value", vals.astype(np.float32))
    return lm


# ------------------------------------------------------------------ strands

def _poly_arrays(body, co, keep):
    polys = [p for p in body.data.polygons if all(keep[i] for i in p.vertices)]
    return polys


def _tri_area(a, b, c):
    return 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=-1)


def _sample_surface(co, polys, weight, n, rng):
    """Area-weighted random points on the given polygons (quads split in two). Returns points, normals, weight."""
    tris = []
    for p in polys:
        v = list(p.vertices)
        for i in range(1, len(v) - 1):
            tris.append((v[0], v[i], v[i + 1]))
    tris = np.array(tris)
    A, Bv, C = co[tris[:, 0]], co[tris[:, 1]], co[tris[:, 2]]
    area = _tri_area(A, Bv, C) * weight[tris].mean(axis=1)
    pick = rng.choice(len(tris), size=n, p=area / area.sum())
    r1, r2 = rng.random(n), rng.random(n)
    s = np.sqrt(r1)
    pts = (1 - s)[:, None] * A[pick] + (s * (1 - r2))[:, None] * Bv[pick] + (s * r2)[:, None] * C[pick]
    nrm = np.cross(Bv[pick] - A[pick], C[pick] - A[pick])
    nrm /= np.linalg.norm(nrm, axis=1)[:, None]
    return pts, nrm


def grow_hair(body, rig, co, spec, name):
    """Build the strand-hair Curves object for a body; returns it (parented to the head bone)."""
    rng = np.random.default_rng(spec.get("seed", 7))
    random.seed(spec.get("seed", 7))
    real = group_weights(body, "body") > 0.5
    scalp_w = hair_region(body, rig, co, spec)
    head_keep = real & (co[:, 2] > rig.data.bones["jaw"].tail_local.z - 0.12)
    head_polys = _poly_arrays(body, co, head_keep)
    bvh = BVHTree.FromPolygons([tuple(v) for v in co], [tuple(p.vertices) for p in head_polys])
    scalp_polys = _poly_arrays(body, co, real & (scalp_w > 0.35))
    center = Vector(co[scalp_w > 0.5].mean(axis=0))
    center.z -= 0.05
    top_z = float(co[scalp_w > 0.5][:, 2].max())
    front_y = float(co[scalp_w > 0.5][:, 1].min())
    back_y = float(co[scalp_w > 0.5][:, 1].max())
    crown_y = center.y + 0.015

    n_guides = spec.get("guides", 700)
    n_child = spec.get("count", 30000)
    K = spec.get("points", 22)
    L_top, L_side, L_back = spec.get("length_top", 0.12), spec.get("length_side", 0.045), spec.get("length_back", 0.035)
    lift_front, lift_top, lift_side = spec.get("lift_front", 0.022), spec.get("lift_top", 0.010), spec.get("lift_side", 0.003)
    wave_amp, wave_len = spec.get("wave_amp", 0.004), spec.get("wave_len", 0.045)
    clump = spec.get("clump", 0.65)
    style = spec.get("comb", "back")             # back (the chad's sweep), side (a part at x = 'part'), crop
    part_x = spec.get("part", -0.03)

    groots, gnrm = _sample_surface(co, scalp_polys, np.clip(scalp_w, 0.05, 1), n_guides, rng)

    def outward(p, nr):
        nr = Vector(nr)
        return nr if nr.dot(p - center) >= 0 else -nr

    guides, gnorms = [], []
    for gi in range(n_guides):
        r = Vector(groots[gi])
        nr = outward(r, gnrm[gi])
        # where on the head: 1 at the front hairline on top, 0 at the back; 'top' 1 on the crown, 0 on the sides
        front = float(np.clip((back_y - r.y) / (back_y - front_y), 0, 1)) ** 1.6
        top = float(np.clip((r.z - (top_z - 0.085)) / 0.07, 0, 1))
        behind = float(np.clip((r.y - crown_y) / 0.05, 0, 1)) * (1 - top)      # the back of the head: short, flat
        # long at the front (the sweep), shorter from the crown back so the back lies flat
        L = (L_side + (L_top - L_side) * top * (0.5 + 0.5 * front)) * (1 - behind) + L_back * behind
        L *= 0.85 + 0.3 * rng.random()
        h_max = lift_side + (lift_top - lift_side) * top + lift_front * front * top
        h_max *= 0.6 + 0.6 * rng.random()
        phase = rng.random() * math.tau
        p_surf, n_cur = r.copy(), nr
        pts, nrms = [r.copy()], [nr.copy()]
        step = L / (K - 1)
        prev_t = None
        for k in range(1, K):
            s = k * step
            down = float(np.clip((p_surf.y - crown_y) / 0.06, 0, 1))
            side = p_surf.z < top_z - 0.08
            if style == "side" and not side:
                # side part at x = part: the big side sweeps across the top, the small side combs down to the ear
                sgn = 1.0 if r.x > part_x else -1.0
                comb = Vector((0.8 * sgn, 0.35 - 0.3 * down, -0.25 - 0.7 * down))
            elif style == "crop" and not side:
                # short crop: pushed forward and down on top, like a Caesar
                comb = Vector((0, -0.55 + 1.2 * down, -0.45 - 0.5 * down))
            else:
                # combed straight back over the top, horizontally back along the sides, down only at the very back
                comb = Vector((0, 1.0 - 0.6 * down, (-0.15 if not side else 0.05) - 0.9 * down))
            t = comb - n_cur * comb.dot(n_cur)
            if t.length < 1e-6:
                t = prev_t or Vector((0, 0, -1))
            t.normalize()
            prev_t = t
            loc, nn, _i, _d = bvh.find_nearest(p_surf + t * step)
            if loc is None:
                break
            p_surf = loc
            n_cur = outward(loc, nn)
            # up off the scalp fast (the quiff), easing down along the strand, lying flat once past the crown
            sag = 1 - 0.55 * min(1.0, max(0.0, (s - 0.03) / max(L - 0.03, 1e-3)))
            flat = 1 - 0.8 * float(np.clip((p_surf.y - crown_y) / 0.06, 0, 1))
            h = h_max * (1 - math.exp(-s / 0.012)) * sag * flat
            b = t.cross(n_cur)
            wave = wave_amp * math.sin(math.tau * s / wave_len + phase) * min(1.0, s / 0.03)
            pts.append(p_surf + n_cur * (h + 0.0015) + b * wave)
            nrms.append(n_cur.copy())
        while len(pts) < K:                                  # ran off the mesh: extend straight
            pts.append(pts[-1] + (pts[-1] - pts[-2]))
            nrms.append(nrms[-1])
        guides.append(np.array(pts))
        gnorms.append(np.array(nrms))
    guides = np.array(guides)
    gnorms = np.array(gnorms)

    kd = KDTree(n_guides)
    for i, p in enumerate(groots):
        kd.insert(Vector(p), i)
    kd.balance()

    croots, _cn = _sample_surface(co, scalp_polys, np.clip(scalp_w, 0.05, 1), n_child, rng)
    pos = np.empty((n_child, K, 3))
    u = (np.arange(K) / (K - 1))[None, :, None]
    for ci in range(n_child):
        r = croots[ci]
        _co, gi, _d = kd.find(Vector(r))
        off = r - groots[gi]
        lift = (rng.random() * 1.4 - 0.4) * 0.006
        pos[ci] = guides[gi] + off[None, :] * (1 - clump * u[0] ** 1.3) + gnorms[gi] * (lift * u[0])
    # a little frizz at the tips so the edges aren't perfect
    pos += rng.normal(0, spec.get("frizz", 0.0003), pos.shape) * (u ** 2)
    pos[:, 0] = croots

    curves = bpy.data.hair_curves.new(f"{name}.strands")
    curves.add_curves([K] * n_child)
    curves.position_data.foreach_set("vector", pos.reshape(-1).astype(np.float32))
    rad = spec.get("radius", 0.00028) * (1 - 0.7 * np.linspace(0, 1, K) ** 2)
    radius = np.tile(rad, n_child).astype(np.float32)
    if "radius" not in curves.attributes:
        curves.attributes.new("radius", "FLOAT", "POINT")
    curves.attributes["radius"].data.foreach_set("value", radius)
    ob = bpy.data.objects.new(f"{name}.strands", curves)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(hair_material(spec))

    # ride the head bone: rest-pose bone matrix to the bone tail, as Blender's bone parenting expects
    bone = rig.data.bones["head"]
    ob.parent = rig
    ob.parent_type = "BONE"
    ob.parent_bone = "head"
    ob.matrix_parent_inverse = (rig.matrix_world @ bone.matrix_local @ Matrix.Translation((0, bone.length, 0))).inverted()
    return ob


def _lin(hexs):
    def ch(v):
        v = v / 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return tuple(ch(int(hexs[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


def hair_material(spec):
    """Principled BSDF, not the Principled Hair BSDF: Eevee renders the hair BSDF nearly black with no highlights.
    Colour runs from dark roots to warm tips along each strand, with a little per-strand variation, and a glossy coat
    gives the shine."""
    m = bpy.data.materials.new("strand_hair")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    info = nt.nodes.new("ShaderNodeHairInfo")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cols = spec.get("colors", ["1a0f08", "3a2312", "6b4426", "9a6a3e"])
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, _lin(cols[0])
    els[1].position, els[1].color = 1.0, _lin(cols[-1])
    for i, c in enumerate(cols[1:-1]):
        els.new((i + 1) / (len(cols) - 1)).color = _lin(c)
    nt.links.new(info.outputs["Intercept"], ramp.inputs[0])
    var = nt.nodes.new("ShaderNodeMapRange")                 # per-strand brightness, 0.75 to 1.2
    var.inputs["To Min"].default_value, var.inputs["To Max"].default_value = 0.75, 1.2
    nt.links.new(info.outputs["Random"], var.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    nt.links.new(ramp.outputs[0], mul.inputs[6])
    comb = nt.nodes.new("ShaderNodeCombineColor")
    for k in ("Red", "Green", "Blue"):
        nt.links.new(var.outputs[0], comb.inputs[k])
    nt.links.new(comb.outputs[0], mul.inputs[7])
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mul.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = spec.get("roughness", 0.38)
    b.inputs["Specular IOR Level"].default_value = 0.6
    b.inputs["Specular Tint"].default_value = _lin(spec.get("spec_tint", "e8b88a"))
    b.inputs["Coat Weight"].default_value = 0.25
    b.inputs["Coat Roughness"].default_value = 0.3
    b.inputs["Sheen Weight"].default_value = spec.get("sheen", 0.35)
    b.inputs["Sheen Tint"].default_value = _lin(spec.get("sheen_tint", "c89a6a"))
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m
