"""Body-macro set: the inside of a stomach. Two places in one file:

  the wall (origin)       folded pink lining (rugae) half under a pool of yellow-green acid, bubbles, pepsin blobs
                          shots: wall_in, acid, pepsin, wall_low, wall_out (wall_out ends on wall_in's first frame)
  the section (at M)      a magnified slice of the lining: columnar cells with nuclei, the mucus gel on top, acid
                          drops falling onto it, bicarbonate rising to meet them
                          shots: section, neutral, cells (cells replaced), fail (mucus thins), ulcer (acid eats in)

blender -b --factory-startup -P stomach_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Writes out_dir/anchors.json (screen points for labels, every frame).
"""
import json, math, os, random, sys
import bpy, bmesh
from mathutils import Vector, noise
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bkit as B

argv = sys.argv[sys.argv.index("--") + 1:]
TIMING, OUT, MODE = argv[0], argv[1], argv[2]
T = json.load(open(TIMING))
FPS, DUR = T["fps"], T["duration"]
NF = int(round(DUR * FPS))
SHOTS = T["shots"]
os.makedirs(OUT, exist_ok=True)
B.clear_scene()
scene = B.scene
rng = random.Random(5)
AWAY = Vector((0, 0, -1.0e4))
ACID = (0.72, 0.86, 0.12)
BICARB = (0.02, 0.18, 1.0)

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

w = bpy.data.worlds.new("world")
scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.012, 0.002, 0.003, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0

# ------------------------------------------------------------------ materials

def principled(m):
    return m.node_tree.nodes["Principled BSDF"]

def plain(name, color, rough=0.4, metal=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = principled(m)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    return m

def emit(m, color, strength):
    b = principled(m)
    b.inputs["Emission Color"].default_value = (*color, 1)
    b.inputs["Emission Strength"].default_value = strength

def refractive(m):
    for attr in ("use_raytrace_refraction", "use_screen_refraction"):
        if hasattr(m, attr):
            setattr(m, attr, True)

def value(nt, key, v=0.0):
    n = nt.nodes.new("ShaderNodeValue"); n.name = key; n.outputs[0].default_value = v
    return n.outputs[0]

def setv(m, key, v):
    m.node_tree.nodes[key].outputs[0].default_value = v

def flesh(name, c0, c1, scale=6.0, bump=0.35, sss=0.35):
    """Wet tissue: blotchy two-tone color, subsurface, a clear wet coat, fine bump."""
    m = plain(name, c0, rough=0.42, coat=1.0)
    b = principled(m)
    b.inputs["Coat Roughness"].default_value = 0.04
    b.inputs["Subsurface Weight"].default_value = sss
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.25, 0.15)
    b.inputs["Subsurface Scale"].default_value = 0.02
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 8.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.35, 0.7
    ramp.color_ramp.elements[0].color, ramp.color_ramp.elements[1].color = (*c0, 1), (*c1, 1)
    nt.links.new(nz.outputs["Fac"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], b.inputs["Base Color"])
    fine = nt.nodes.new("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = scale * 18; fine.inputs["Detail"].default_value = 4.0
    nt.links.new(tc.outputs["Object"], fine.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.002
    nt.links.new(fine.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs[0], b.inputs["Normal"])
    return m

def liquid(name, tint, alpha_keep=0.0):
    """Clear tinted liquid with a moving ripple bump (Value node 't' drives it)."""
    m = plain(name, tint, rough=0.07)
    b = principled(m)
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.33
    refractive(m)
    emit(m, tint, 0.06)
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"
    nz.inputs["Scale"].default_value = 14.0; nz.inputs["Detail"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(value(nt, "t"), nz.inputs["W"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; bp.inputs["Distance"].default_value = 0.003
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs[0], b.inputs["Normal"])
    return m

def see_through(name, color, keep, rough=0.12, glow=0.0):
    """Mostly transparent tinted gel: `keep` of the surface is a glossy tinted shader, the rest lets light through."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = principled(m)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.05
    b.inputs["Emission Color"].default_value = (*color, 1)
    b.inputs["Emission Strength"].default_value = glow
    out = nt.nodes["Material Output"]
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = 1.0 - keep
    nt.links.new(b.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    m.use_transparent_shadow = True
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "BLENDED"     # dithered transparency came out blotchy
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

def sphere(name, r, mat, subdiv=3):
    def b(bm):
        bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
    ob = B.mesh_from(name, b, [mat])
    B.smooth(ob, 80)
    return ob

# ------------------------------------------------------------------ the wall: rugae under acid

ACID_Z = 0.017

def ridge(x, y):
    xw = x + 0.05 * math.sin(y * 5.0 + 1.3) + 0.03 * noise.noise(Vector((x * 3, y * 3, 0.5)))
    s = 0.5 + 0.5 * math.sin(2 * math.pi * xw / 0.17)
    h = 0.042 * s ** 0.9 * (0.75 + 0.25 * noise.noise(Vector((x * 2, y * 1.5, 2.0))))
    return h + 0.004 * noise.noise(Vector((x * 30, y * 30, 7.0)))

def wall_build(bm):
    nx, ny = 260, 300
    x0, x1, y0, y1 = -0.75, 0.75, -0.75, 1.1
    verts = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            y = y0 + (y1 - y0) * j / ny
            verts.append(bm.verts.new((x, y, ridge(x, y))))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            bm.faces.new((verts[a], verts[a + 1], verts[a + nx + 2], verts[a + nx + 1]))

wall_m = flesh("wall", (0.42, 0.04, 0.06), (0.78, 0.26, 0.26), scale=5.0)
wall = B.mesh_from("wall", wall_build, [wall_m])
B.smooth(wall, 80)
acid_m = liquid("acid", ACID)
B.mesh_from("acid", B.box(-0.75, 0.75, -0.75, 1.1, ACID_Z - 0.002, ACID_Z), [acid_m])

bubble_m = plain("bubble", (0.9, 0.95, 0.8), rough=0.02)
principled(bubble_m).inputs["Transmission Weight"].default_value = 1.0
refractive(bubble_m)
BUBBLES = []
for i in range(46):
    x, y = rng.uniform(-0.30, 0.30), rng.uniform(-0.25, 0.30)
    while ridge(x, y) > ACID_Z - 0.006:                    # start in a valley, under the acid
        x, y = rng.uniform(-0.30, 0.30), rng.uniform(-0.25, 0.30)
    r = rng.uniform(0.0015, 0.0045)
    BUBBLES.append((sphere(f"bub{i}", r, bubble_m, 2), Vector((x, y, ridge(x, y) + r)), rng.uniform(0, 1), rng.uniform(0.6, 1.4)))

drop = sphere("drop", 0.007, acid_m)
pepsin_m = flesh("pepsin", (0.30, 0.08, 0.55), (0.55, 0.20, 0.75), scale=40.0, bump=0.6, sss=0.2)
PEPSIN = []
for i in range(9):
    def b(bm):
        bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.010)
        for v in bm.verts:
            v.co *= 1.0 + 0.35 * noise.noise(v.co * 160 + Vector((i, 0, 0)))
    ob = B.mesh_from(f"pepsin{i}", b, [pepsin_m])
    B.smooth(ob, 80)
    x, y = -0.10 + rng.uniform(-0.06, 0.06), rng.uniform(-0.05, 0.10)
    PEPSIN.append((ob, Vector((x, y, ACID_Z - 0.006 - rng.uniform(0, 0.006))), rng.uniform(0, 6.28)))

key = B.area("key", (-0.5, -0.6, 0.6), (0, 0, 0), 1.0, 22.0, color=(1.0, 0.88, 0.78))
rim = B.area("rim", (0.5, 0.9, 0.3), (0, 0, 0), 0.5, 40.0, color=(1.0, 0.55, 0.45))
fill = B.area("fill", (0.6, -0.5, 0.25), (0, 0, 0), 0.6, 6.0, color=(0.6, 0.75, 1.0))
WALL_LIGHTS = [key, rim, fill]

# ------------------------------------------------------------------ the section: lining cells, mucus, acid

M = Vector((8.0, 0.0, 0.0))
CW, CH, MU = 0.05, 0.16, 0.08          # cell width, cell height, mucus thickness
COLS = list(range(-11, 12))            # cell columns, x = M.x + c * CW
ROWS = (0, 1, 2)
cell_m = flesh("cell", (0.78, 0.30, 0.36), (0.92, 0.48, 0.50), scale=30.0, bump=0.2, sss=0.5)
nuc_m = flesh("nucleus", (0.32, 0.08, 0.30), (0.45, 0.14, 0.42), scale=60.0, bump=0.3, sss=0.2)
raw_m = flesh("raw", (0.50, 0.03, 0.04), (0.75, 0.08, 0.06), scale=30.0, bump=0.4)
emit(raw_m, (1.0, 0.12, 0.04), 0.0)
B.mesh_from("base", B.box(M.x - 0.62, M.x + 0.62, M.y - 0.026, M.y + 0.30, -0.10, -0.002), [flesh("base", (0.55, 0.10, 0.14), (0.70, 0.20, 0.22), scale=8.0)])

def cell(name, mat, nucleus=True):
    def b(bm):
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector((v.co.x * (CW - 0.004), v.co.y * (CW - 0.004), (v.co.z + 0.5) * CH))
    ob = B.mesh_from(name, b, [mat])
    B.bevel(ob, 0.009, 3)
    B.smooth(ob, 60)
    if nucleus:
        n = sphere(name + "_n", 0.011, nuc_m, 2)
        n.parent = ob
        n.location = (0, -CW / 2 + 0.006, CH * 0.32)
        n.scale = (1, 0.6, 1.25)
    return ob

CELLS = {}
for c in COLS:
    for r in ROWS:
        home = M + Vector((c * CW, r * CW, 0.0))
        old = cell(f"cell_{c}_{r}", cell_m, r == 0)
        new = cell(f"cnew_{c}_{r}", cell_m, r == 0)
        CELLS[(c, r)] = (old, new, home, rng.uniform(0.05, 0.6))

mucus_m = see_through("mucus", (0.72, 0.84, 0.95), 0.45, rough=0.15)
GAP = 1                                   # columns -1..1 are where the mucus fails
mu_left = B.mesh_from("mu_left", B.box(M.x + COLS[0] * CW - CW / 2, M.x - (GAP + 0.5) * CW, M.y - CW / 2, M.y + 2.5 * CW, CH, CH + MU), [mucus_m])
mu_right = B.mesh_from("mu_right", B.box(M.x + (GAP + 0.5) * CW, M.x + COLS[-1] * CW + CW / 2, M.y - CW / 2, M.y + 2.5 * CW, CH, CH + MU), [mucus_m])
mu_mid = B.mesh_from("mu_mid", B.box(-(GAP + 0.5) * CW + 0.001, (GAP + 0.5) * CW - 0.001, M.y - CW / 2, M.y + 2.5 * CW, 0.0, MU), [mucus_m])
mu_mid.location = M + Vector((0, 0, CH))
acid_haze = see_through("acid_haze", ACID, 0.16, rough=0.3, glow=0.25)
B.mesh_from("acid_box", B.box(M.x - 0.62, M.x + 0.62, M.y - CW / 2 + 0.002, M.y + 2.5 * CW, CH + MU + 0.002, CH + MU + 0.40), [acid_haze])

acid_drop_m = glowing("acid_drop", ACID, 1.6)
bic_m = glowing("bicarb", BICARB, 4.0)
DROPS, BICS = [], []
for i in range(40):
    DROPS.append((sphere(f"ad{i}", 0.007, acid_drop_m, 2), rng.uniform(-0.55, 0.55), rng.uniform(-0.01, 0.10), rng.uniform(0, 1), rng.uniform(0.7, 1.3)))
for i in range(36):
    BICS.append((sphere(f"bc{i}", 0.0085, bic_m, 2), rng.uniform(-0.55, 0.55), rng.uniform(-0.01, 0.10), rng.uniform(0, 1)))
for i in range(8):                                          # a few drops always aimed at the gap, for 'fail' and 'ulcer'
    DROPS.append((sphere(f"adg{i}", 0.007, acid_drop_m, 2), rng.uniform(-0.06, 0.06), rng.uniform(-0.01, 0.04), rng.uniform(0, 1), rng.uniform(0.8, 1.2)))

key2 = B.area("key2", M + Vector((-0.6, -0.9, 0.8)), M + Vector((0, 0, 0.15)), 0.8, 45.0, color=(1.0, 0.9, 0.82))
rim2 = B.area("rim2", M + Vector((0.5, 0.8, 0.6)), M + Vector((0, 0, 0.15)), 0.6, 35.0, color=(1.0, 0.6, 0.5))
fill2 = B.area("fill2", M + Vector((0.7, -0.8, 0.2)), M + Vector((0, 0, 0.15)), 0.6, 10.0, color=(0.6, 0.75, 1.0))
SEC_LIGHTS = [key2, rim2, fill2]

# ------------------------------------------------------------------ shots

cam = B.camera(lens=35, fstop=2.8)
cam.data.clip_start = 0.002

def lerp_cam(a, b, target, lens, fstop, u):
    return a.lerp(b, smooth01(u)), target, lens, fstop

def wall_in(u):
    return lerp_cam(Vector((0.02, -0.52, 0.20)), Vector((0.0, -0.36, 0.12)), Vector((0.0, 0.05, 0.015)), 35, 3.2, u)

CAMS = {
    "wall_in": wall_in,
    "wall_out": lambda u: wall_in(1.0 - u),
    "acid": lambda u: lerp_cam(Vector((0.15, -0.22, 0.10)), Vector((0.12, -0.17, 0.085)), Vector((0.06, 0.01, 0.017)), 50, 2.8, u),
    "pepsin": lambda u: lerp_cam(Vector((-0.16, -0.17, 0.10)), Vector((-0.14, -0.13, 0.085)), Vector((-0.10, 0.02, 0.014)), 50, 3.2, u),
    "wall_low": lambda u: lerp_cam(Vector((0.36, -0.30, 0.16)), Vector((0.30, -0.25, 0.14)), Vector((0.0, 0.05, 0.02)), 28, 4.0, u),
    "section": lambda u: lerp_cam(M + Vector((0.02, -1.05, 0.34)), M + Vector((0.0, -0.88, 0.30)), M + Vector((0, 0, 0.17)), 50, 5.6, u),
    "neutral": lambda u: lerp_cam(M + Vector((0.16, -0.46, 0.30)), M + Vector((0.13, -0.40, 0.29)), M + Vector((0.06, 0, 0.23)), 50, 4.0, u),
    "cells": lambda u: lerp_cam(M + Vector((-0.06, -0.58, 0.14)), M + Vector((-0.05, -0.50, 0.14)), M + Vector((0, 0, 0.12)), 50, 4.0, u),
    "fail": lambda u: lerp_cam(M + Vector((0.0, -0.72, 0.32)), M + Vector((0.0, -0.62, 0.29)), M + Vector((0, 0, 0.19)), 50, 5.0, u),
    "ulcer": lambda u: lerp_cam(M + Vector((0.06, -0.42, 0.26)), M + Vector((0.04, -0.36, 0.23)), M + Vector((0, 0, 0.13)), 50, 4.0, u),
}
WALL_SHOTS = {"wall_in", "wall_out", "acid", "pepsin", "wall_low"}

def shot_at(t):
    k = max([0] + [i for i, (s, _) in enumerate(SHOTS) if t >= s - 1e-6])
    t0 = SHOTS[k][0]
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    return SHOTS[k][1], max(0.0, min(1.0, (t - t0) / max(1e-6, t1 - t0))), t - t0

def apply_state(t):
    name, u, age = shot_at(t)
    loc, tg, lens, fstop = CAMS[name](u)
    B.aim(cam, loc, tg)
    cam.data.lens = lens
    cam.data.dof.aperture_fstop = fstop
    cam.data.dof.focus_distance = (tg - loc).length
    wall_shot = name in WALL_SHOTS
    for ob in WALL_LIGHTS:
        ob.hide_render = not wall_shot
    for ob in SEC_LIGHTS:
        ob.hide_render = wall_shot
    setv(acid_m, "t", t * 0.35)
    # 'your stomach wall is meat': the wall wobbles like jelly when the line lands (the odd detail people comment on)
    wob = 0.35 * math.exp(-age * 3.5) * math.sin(age * 24) if name == "wall_low" else 0.0
    wall.scale = (1, 1, 1 + wob)
    # bubbles rise from the valleys to the acid surface, then start over (a time loop, the same at t and t + period)
    for ob, home, phase, speed in BUBBLES:
        a = (t * 0.35 * speed + phase) % 1.0
        ob.location = home + Vector((0.002 * math.sin(t * 3 + phase * 9), 0, (ACID_Z - home.z) * a))
        s = 1.0 if a < 0.92 else 0.01
        ob.scale = (s, s, s)
    # one drop of acid lands on frame 1 (and again at the very end, so the loop matches)
    tl = min(t, DUR - t + 0.0)
    fall = tl / 0.35
    drop.location = Vector((0.03, 0.04, ACID_Z + 0.09 * (1 - fall))) if (wall_shot and fall < 1.0 and name in ("wall_in", "wall_out")) else AWAY
    for ob, home, ph in PEPSIN:
        ob.location = home + Vector((0.004 * math.sin(t * 0.8 + ph), 0.003 * math.cos(t * 0.6 + ph), 0.0)) if name in ("pepsin", "acid") else AWAY
        ob.rotation_euler = (t * 0.5 + ph, t * 0.3, ph)
    # the section
    gap_open = smooth01(u / 0.7) if name == "fail" else (1.0 if name == "ulcer" else 0.0)
    mu_mid.scale = (1, 1, max(0.001, 1.0 - gap_open))
    eaten = smooth01((u - 0.1) / 0.8) if name == "ulcer" else 0.0
    emit(raw_m, (1.0, 0.12, 0.04), 2.0 * eaten)
    for (c, r), (old, new, home, ph) in CELLS.items():
        in_gap = abs(c) <= GAP
        if name == "cells":                                 # time-lapse: the old cell lifts off and shrinks, a new one grows
            k = smooth01((u - ph) / 0.35)
            old.location = home + Vector((0, 0, 0.08 * k))
            s = max(0.001, 1.0 - k)
            old.scale = (s, s, s)
            new.location = home
            new.scale = (1, 1, max(0.001, k))
        else:
            old.location = home
            old.scale = (1, 1, 1)
            new.location = AWAY
        if in_gap and name == "ulcer":
            depth = eaten * (1.0 - 0.35 * abs(c))
            old.scale = (1, 1, max(0.001, 1.0 - depth))
            old.data.materials[0] = raw_m
        else:
            old.data.materials[0] = cell_m
    for ob, x, y, ph, sp in DROPS:
        a = (t * 0.45 * sp + ph) % 1.0
        z = CH + MU + 0.38 * (1 - a)
        p = M + Vector((x, y, z))
        s = 1.0
        bottom = CH + MU
        gap_x = abs(x) < (GAP + 0.5) * CW
        if name in ("fail", "ulcer") and gap_x:
            bottom = CH * (1 - eaten) + 0.01 if name == "ulcer" else CH + MU * (1 - gap_open)
            p.z = bottom + (CH + MU + 0.38 - bottom) * (1 - a)
        elif z < bottom + 0.02:
            s = max(0.01, (z - bottom) / 0.02)
        if name in ("section", "neutral", "fail", "ulcer") and (name in ("fail", "ulcer") or ph < 0.85 or not gap_x):
            ob.location = p
            ob.scale = (s, s, s)
        else:
            ob.location = AWAY
    for ob, x, y, ph in BICS:
        a = (t * 0.5 + ph) % 1.0
        on = name in ("neutral", "section") and not (abs(x) < (GAP + 0.5) * CW and name == "fail")
        ob.location = M + Vector((x, y, CH + 0.005 + (MU + 0.012) * a)) if on else AWAY
        s = 1.0 if a < 0.85 else max(0.01, (1 - a) / 0.15)
        ob.scale = (s, s, s)

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    pts = {
        "acid": lambda: Vector((0.07, 0.03, ACID_Z)),
        "pepsin": lambda: PEPSIN[0][0].location.copy(),
        "wall": lambda: Vector((0.05, 0.05, ridge(0.05, 0.05))),
        "mucus": lambda: M + Vector((-0.24, -CW / 2, CH + MU * 0.6)),
        "cells": lambda: M + Vector((0.22, -CW / 2, CH * 0.6)),
        "bicarb": lambda: next((o.location.copy() for o, x, y, ph in BICS if o.location.z > -1 and x > 0.05 and y < 0.02), M),
        "ulcer": lambda: M + Vector((0.0, -CW / 2, CH * 0.5)),
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

B.render_settings(FPS, samples=int(os.environ.get("STOMACH_SAMPLES", "48")), motion_blur=0.35, look="AgX - Medium High Contrast")

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1 + scn.frame_subframe) / FPS)

anchors()
apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
