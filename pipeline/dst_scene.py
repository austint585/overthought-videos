"""Blender scene for 'The same hour twice': a voxel bedroom at night, a guy in bed on his phone, a digital clock on the
nightstand that falls back from 1:59 to 1:00, moonlight through the window. Built in code and timed to the narration.

blender -b --factory-startup -P dst_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Always writes out_dir/anchors.json: screen positions of label points for every frame.

No two surfaces of different materials share a plane (Austin saw texture flicker where they did): add-on parts sit a
few centimetres off the face behind them. The figure bends at the hip (a torso pivot), so he can sit up in bed.
"""
import json, math, os, random, sys
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bkit as B

argv = sys.argv[sys.argv.index("--") + 1:]
TIMING, OUT, MODE = argv[0], argv[1], argv[2]
T = json.load(open(TIMING))
FPS, DUR, E = T["fps"], T["duration"], T["events"]
NF = int(round(DUR * FPS))
os.makedirs(OUT, exist_ok=True)
B.clear_scene()
scene = B.scene
AWAY = Vector((0, 0, -1.0e5))

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

def ramp(t, t0, t1):
    return smooth01((t - t0) / (t1 - t0))

# ------------------------------------------------------------------ pixel-texture materials (same method as spawner_scene)

def pixel_mat(name, pal, rough=0.85, lines=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = rough
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    nudge = nt.nodes.new("ShaderNodeVectorMath"); nudge.operation = "MULTIPLY_ADD"
    nudge.inputs[1].default_value = (-0.01, -0.01, -0.01)
    nt.links.new(geo.outputs["Normal"], nudge.inputs[0])
    nt.links.new(geo.outputs["Position"], nudge.inputs[2])
    snap = nt.nodes.new("ShaderNodeVectorMath"); snap.operation = "SNAP"
    snap.inputs[1].default_value = (1 / 16, 1 / 16, 1 / 16)
    nt.links.new(nudge.outputs[0], snap.inputs[0])
    wn = nt.nodes.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = "3D"
    nt.links.new(snap.outputs[0], wn.inputs["Vector"])
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.color_ramp.interpolation = "CONSTANT"
    els = r.color_ramp.elements
    els[0].color = (*pal[0], 1)
    els[1].position = 1.0 / len(pal)
    els[1].color = (*pal[1 % len(pal)], 1)
    for k in range(2, len(pal)):
        e = els.new(k / len(pal)); e.color = (*pal[k], 1)
    nt.links.new(wn.outputs["Value"], r.inputs["Fac"])
    base = r.outputs["Color"]
    if lines:
        scale, dark = lines
        sc = nt.nodes.new("ShaderNodeVectorMath"); sc.operation = "MULTIPLY"; sc.inputs[1].default_value = scale
        nt.links.new(snap.outputs[0], sc.inputs[0])
        sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sc.outputs[0], sep.inputs[0])
        acc = None
        for ax in ("X", "Y", "Z"):
            fr = nt.nodes.new("ShaderNodeMath"); fr.operation = "FRACT"; nt.links.new(sep.outputs[ax], fr.inputs[0])
            lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.06
            nt.links.new(fr.outputs[0], lt.inputs[0])
            if acc is None:
                acc = lt.outputs[0]
            else:
                mxx = nt.nodes.new("ShaderNodeMath"); mxx.operation = "MAXIMUM"
                nt.links.new(acc, mxx.inputs[0]); nt.links.new(lt.outputs[0], mxx.inputs[1]); acc = mxx.outputs[0]
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
        mix.inputs[7].default_value = (*dark, 1)
        nt.links.new(acc, mix.inputs[0]); nt.links.new(base, mix.inputs[6])
        base = mix.outputs[2]
    nt.links.new(base, p.inputs["Base Color"])
    return m

def solid(name, color, rough=0.6, emit=0.0, emit_color=None):
    m = B.material(name, color, 0.0, rough)
    p = B.bsdf(m)
    p.inputs["Emission Color"].default_value = (*(emit_color or color), 1)
    p.inputs["Emission Strength"].default_value = emit
    return m

MATS = {
    "wood": pixel_mat("wood", [(0.36, 0.22, 0.12), (0.40, 0.25, 0.14), (0.33, 0.20, 0.11)], rough=0.6,
                      lines=((1, 0.25, 1), (0.22, 0.13, 0.07))),
    "wall": pixel_mat("wall", [(0.38, 0.42, 0.55), (0.40, 0.44, 0.58), (0.36, 0.40, 0.52)]),
    "ceil": pixel_mat("ceil", [(0.50, 0.50, 0.52), (0.53, 0.53, 0.55)]),
    "moon": solid("moonglass", (0.55, 0.65, 1.0), rough=0.1, emit=2.2),
}

# ------------------------------------------------------------------ voxel room (inside: x -3..3, y -4..3, z 0..3)

GRID = {}

def fill(i0, i1, j0, j1, k0, k1, mat):
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            for k in range(k0, k1 + 1):
                GRID[(i, j, k)] = mat

fill(-4, 3, -5, 3, -1, -1, "wood")
fill(-4, -4, -5, 3, 0, 2, "wall")
fill(3, 3, -5, 3, 0, 2, "wall")
fill(-4, 3, 3, 3, 0, 2, "wall")
fill(-4, 3, -5, 3, 3, 3, "ceil")
fill(-4, -4, 0, 1, 1, 1, "moon")                     # window in the left wall

DIRS = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]),
        ((-1, 0, 0), [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]),
        ((0, 1, 0), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)]),
        ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
        ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]),
        ((0, 0, -1), [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)])]

def voxel_mesh(name, grid):
    keys = sorted(set(grid.values()))
    idx = {k: n for n, k in enumerate(keys)}
    verts, faces, mats = [], [], []
    for (i, j, k), mat in grid.items():
        for (di, dj, dk), quad in DIRS:
            if (i + di, j + dj, k + dk) in grid:
                continue
            base = len(verts)
            verts.extend((i + a, j + b, k + c) for a, b, c in quad)
            faces.append((base, base + 1, base + 2, base + 3))
            mats.append(idx[mat])
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    for k in keys:
        me.materials.append(MATS[k])
    me.polygons.foreach_set("material_index", mats)
    return B.link(bpy.data.objects.new(name, me))

voxel_mesh("room", GRID)

_mat_cache = {}
def colmat(color, rough=0.55, emit=0.0):
    key = (color, rough, emit)
    if key not in _mat_cache:
        _mat_cache[key] = solid(f"c{len(_mat_cache)}", color, rough, emit)
    return _mat_cache[key]

def boxes(name, parts, origin, parent=None):
    mats, builders = [], []
    for bb, m in parts:
        if m not in mats:
            mats.append(m)
        builders.append(B.with_material(B.box(*bb), mats.index(m)))
    ob = B.mesh_from(name, B.many(*builders), mats)
    ob.parent = parent
    ob.location = origin
    return ob

def text3d(name, body, loc, size, mat, extrude=0.005):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    ob = B.link(bpy.data.objects.new(name, cu))
    ob.data.materials.append(mat)
    ob.location = loc
    ob.rotation_euler = (math.pi / 2, 0, 0)
    return ob

# bed along y, headboard against the back wall
FRAME = colmat((0.25, 0.15, 0.09), 0.6)
boxes("bed", [((-1.0, 1.0, 0.0, 2.2, 0.0, 0.32), FRAME),
              ((-0.96, 0.96, 0.03, 2.17, 0.32, 0.55), colmat((0.92, 0.92, 0.95), 0.8)),
              ((-1.0, 1.0, 2.2, 2.32, 0.0, 1.15), FRAME),
              ((-0.55, 0.55, 1.62, 2.12, 0.551, 0.70), colmat((0.95, 0.95, 0.97), 0.8))], (0, 0.62, 0))
BLANKET = colmat((0.20, 0.30, 0.55), 0.85)
blanket = boxes("blanket", [((-1.02, 1.02, -0.02, 1.25, 0.56, 0.85), BLANKET),
                            ((-1.02, 1.02, -0.02, 0.02, 0.10, 0.56), BLANKET),
                            ((-1.04, -0.98, 0.02, 1.25, 0.15, 0.85), BLANKET),
                            ((0.98, 1.04, 0.02, 1.25, 0.15, 0.85), BLANKET)], (0, 0.62, 0))
# nightstand and clock
boxes("stand", [((-0.3, 0.3, -0.25, 0.25, 0.0, 0.55), FRAME),
                ((-0.26, 0.26, -0.255, -0.25, 0.30, 0.50), colmat((0.18, 0.10, 0.06), 0.6))], (1.45, 2.45, 0.0))
boxes("clock", [((-0.17, 0.17, -0.06, 0.06, 0.0, 0.14), colmat((0.04, 0.04, 0.05), 0.4))], (1.45, 2.40, 0.55))
DIGIT = solid("digit", (1.0, 0.05, 0.02), rough=0.4, emit=12.0)
TIMES = ["1:59", "1:00", "1:15", "1:30", "1:45", "2:00"]
CLOCK = {s: text3d(f"t{s}", s, (1.45, 2.325, 0.62), 0.105, DIGIT) for s in TIMES}
# a lamp, a poster and a rug so the room is lived in
boxes("rug", [((-1.4, 1.4, -1.2, 0.5, 0.0, 0.015), colmat((0.55, 0.20, 0.18), 0.9))], (0, -0.4, 0))
boxes("poster", [((-0.45, 0.45, -0.02, 0.0, 0.0, 0.62), colmat((0.95, 0.65, 0.20), 0.7)),
                 ((-0.30, 0.30, -0.035, -0.02, 0.15, 0.45), colmat((0.15, 0.18, 0.30), 0.7))], (-1.9, 3.0, 1.55))
boxes("desk", [((-0.5, 0.5, -0.3, 0.3, 0.70, 0.76), FRAME), ((-0.46, -0.40, -0.26, 0.26, 0.0, 0.70), FRAME),
               ((0.40, 0.46, -0.26, 0.26, 0.0, 0.70), FRAME)], (2.4, -1.2, 0.0))

# ------------------------------------------------------------------ the guy (bends at the hip)

def figure(name, shirt, pants, skin, hair):
    S, P, Sk, H = colmat(shirt, 0.7), colmat(pants, 0.7), colmat(skin), colmat(hair, 0.8)
    D = colmat((0.03, 0.02, 0.02), 0.4)
    root = B.link(bpy.data.objects.new(name, None))
    f = {"root": root}
    for side, x in (("L", -0.125), ("R", 0.125)):
        f["leg" + side] = boxes(f"{name}_leg{side}", [((-0.125, 0.125, -0.125, 0.125, -0.75, 0.0), P),
                                                      ((-0.11, 0.11, -0.11, 0.11, -0.78, -0.70), Sk)], (x, 0, 0.75), root)
    torso = B.link(bpy.data.objects.new(f"{name}_torso", None))
    torso.parent = root
    torso.location = (0, 0, 0.75)
    f["torso"] = torso
    f["body"] = boxes(f"{name}_body", [((-0.25, 0.25, -0.125, 0.125, 0.0, 0.75), S)], (0, 0, 0), torso)
    for side, x in (("L", -0.375), ("R", 0.375)):
        f["arm" + side] = boxes(f"{name}_arm{side}", [((-0.12, 0.12, -0.12, 0.12, -0.35, 0.0), S),
                                                      ((-0.11, 0.11, -0.11, 0.11, -0.78, -0.34), Sk)], (x, 0, 0.75), torso)
    f["head"] = boxes(f"{name}_head", [((-0.25, 0.25, -0.25, 0.25, 0, 0.5), Sk), ((-0.27, 0.27, -0.27, 0.27, 0.43, 0.58), H),
                                       ((-0.268, 0.268, 0.05, 0.28, 0.12, 0.47), H),
                                       ((-0.16, -0.06, -0.265, -0.25, 0.22, 0.29), D), ((0.06, 0.16, -0.265, -0.25, 0.22, 0.29), D),
                                       ((-0.08, 0.08, -0.262, -0.25, 0.07, 0.1), colmat((0.55, 0.30, 0.22)))], (0, 0, 0.75), torso)
    return f

GUY = figure("guy", (0.55, 0.55, 0.58), (0.12, 0.14, 0.25), (0.78, 0.55, 0.40), (0.10, 0.07, 0.05))
GUY["root"].scale = (0.85,) * 3
# a flat slab past the fist, screen toward his face (the arm's +z once the arm points up)
SCREEN = solid("screen", (0.75, 0.85, 1.0), rough=0.3, emit=4.0)
PHONE = boxes("phone", [((-0.05, 0.05, -0.10, 0.10, -0.012, 0.0), colmat((0.05, 0.05, 0.06), 0.3)),
                        ((-0.044, 0.044, -0.09, 0.09, 0.0, 0.006), SCREEN)],
              (0.0, 0.0, -0.86), GUY["armR"])
# lying on his back, feet toward the foot of the bed, head on the pillow
GUY_ROOT = Vector((0.0, 0.70, 0.70))

# ------------------------------------------------------------------ lights, world, camera

world = bpy.data.worlds.new("bg")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.01, 0.012, 0.025, 1)
moon = B.area("moon", Vector((-3.6, 1.0, 1.5)), Vector((0.0, 1.5, 0.6)), 1.2, 260.0, (0.55, 0.65, 1.0))
fill = B.area("fill", Vector((1.5, -3.5, 2.8)), Vector((0.0, 1.0, 0.6)), 3.0, 70.0, (0.45, 0.5, 0.9))
glow = B.area("glow", Vector((0.0, 2.0, 1.2)), Vector((0.0, 2.0, 0.7)), 0.25, 0.0, (0.75, 0.85, 1.0))
glow.parent = PHONE
glow.location = (0.0, 0.0, 0.08)
glow.rotation_euler = (math.pi, 0, 0)            # shines along the phone's +z, onto his face
clock_l = B.area("clockl", Vector((1.45, 2.15, 0.75)), Vector((1.45, 1.5, 0.6)), 0.3, 6.0, (1.0, 0.1, 0.05))
cam = B.camera(lens=30, fstop=2.8)
B.render_settings(FPS, samples=32, motion_blur=0.3)

# ------------------------------------------------------------------ motion

def clock_text(t):
    if t < E["1am"] - 0.05:
        return "1:59"
    if t < E["scroll"]:
        return "1:00"
    seq = ["1:00", "1:15", "1:30", "1:45", "1:59", "2:00"]
    k = int(min(len(seq) - 1, (t - E["scroll"]) / 0.2))
    return seq[k]

def guy_state(t):
    sit = ramp(t, E["F"] - 0.2, E["F"] + 0.5) * (1 - ramp(t, E["G"] + 0.4, E["G"] + 1.1))
    flop = ramp(t, E["march"] - 0.3, E["march"] + 0.3)
    GUY["root"].location = GUY_ROOT
    GUY["root"].rotation_euler = (-math.pi / 2, 0, 0)        # lying on his back, head toward +y
    GUY["torso"].rotation_euler = (math.pi / 2 * 0.85 * sit, 0, 0)
    # arms hold the phone above his face; thumb flicks while scrolling; the phone drops at the end
    scroll = 0.06 * math.sin(t * 14.0) if E["scroll"] - 0.2 < t < E["J"] else 0.02 * math.sin(t * 3.0)
    up = 1 - flop
    GUY["armR"].rotation_euler = (-1.45 * up - 0.1 * sit + scroll, 0, 0.35 * up)
    GUY["armL"].rotation_euler = (-1.30 * up, 0, -0.30 * up)
    look_clock = ramp(t, E["F"] + 0.2, E["F"] + 0.7) * (1 - ramp(t, E["G"] + 0.2, E["G"] + 0.8))
    GUY["head"].rotation_euler = (-0.25 * up, 0, -0.9 * look_clock)
    GUY["legL"].rotation_euler = (0, 0, 0)
    GUY["legR"].rotation_euler = (0.05, 0, 0)

def apply_state(t):
    guy_state(t)
    cur = clock_text(t)
    for s, ob in CLOCK.items():
        ob.location = Vector((1.45, 2.325, 0.62)) if s == cur else AWAY
    flick = 0.0 if E["march"] + 0.2 < t else 1.0
    B.bsdf(SCREEN).inputs["Emission Strength"].default_value = 4.0 * flick
    glow.data.energy = 6.0 * flick
    loc, target, fstop, lens = camera_at(t)
    B.aim(cam, loc, target)
    cam.data.lens = lens
    cam.data.dof.focus_distance = (target - loc).length
    cam.data.dof.aperture_fstop = fstop
    cam.data.clip_start = 0.05
    cam.data.clip_end = 60

# ------------------------------------------------------------------ camera

def head():
    return GUY["head"].matrix_world @ Vector((0, 0, 0.25))

def shot_hook(t):          # from the foot of the bed, the clock glowing on the nightstand
    u = t
    return Vector((0.9 + 0.02 * u, -1.9 + 0.06 * u, 1.75)), Vector((0.6, 1.9, 0.75))
def shot_clock(t):         # close on the clock
    u = t - E["B"]
    return Vector((1.25 - 0.03 * u, 1.55 + 0.05 * u, 0.85)), Vector((1.45, 2.36, 0.66))
def shot_top(t):           # overhead, slowly turning
    u = t - E["C"]
    a = -0.4 + 0.05 * u
    return Vector((1.4 * math.sin(a), 1.5 - 1.4 * math.cos(a), 2.85)), Vector((0.0, 1.5, 0.7))
def shot_side(t):          # he sits up and checks the clock
    u = t - E["F"]
    return Vector((-2.2 + 0.04 * u, 0.2, 1.3)), Vector((0.4, 1.6, 0.95))
def shot_window(t):
    u = t - E["G"]
    return Vector((2.4 - 0.05 * u, -2.6, 1.9)), Vector((-0.6, 1.4, 0.8))
def shot_face(t):          # phone glow on his face while the clock races
    u = t - E["I"]
    h = head()
    return h + Vector((0.75, -0.55, 0.65 - 0.02 * u)), h + Vector((0.2, 0.0, 0.0))
def shot_end(t):
    u = t - E["J"]
    return Vector((0.3, -2.4 - 0.12 * u, 1.9 + 0.05 * u)), Vector((0.5, 1.6, 0.7))

SHOTS = [(shot_hook, None), (shot_clock, (E["B"] - 0.25, E["B"] + 0.15)), (shot_top, (E["C"] - 0.25, E["C"] + 0.15)),
         (shot_side, (E["F"] - 0.25, E["F"] + 0.15)), (shot_window, (E["G"] - 0.25, E["G"] + 0.15)),
         (shot_face, (E["I"] - 0.25, E["I"] + 0.15)), (shot_end, (E["J"] - 0.25, E["J"] + 0.15))]
LENS = {shot_hook: 26.0, shot_clock: 40.0, shot_top: 24.0, shot_face: 32.0, shot_end: 24.0}

def camera_at(t):
    k = 0
    for n, (fn, win_) in enumerate(SHOTS):
        if win_ and t >= win_[0]:
            k = n
    fn, win_ = SHOTS[k]
    loc, tg = fn(t)
    lens = LENS.get(fn, 30.0)
    if win_ and t < win_[1] and k > 0:
        fn0 = SHOTS[k - 1][0]
        loc0, tg0 = fn0(t)
        u = smooth01((t - win_[0]) / (win_[1] - win_[0]))
        loc, tg = loc0.lerp(loc, u), tg0.lerp(tg, u)
        lens = LENS.get(fn0, 30.0) * (1 - u) + lens * u
    d = (tg - loc).length * 30.0 / lens
    fstop = 2.0 if d < 2 else (2.8 if d < 4 else 4.0)
    return loc, tg, fstop, lens

# ------------------------------------------------------------------ anchors for 2D labels

def anchors():
    names = ("clock", "guy", "window")
    out = {k: [] for k in names}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        pts = {"clock": Vector((1.45, 2.34, 0.72)), "guy": head() + Vector((0, 0, 0.3)), "window": Vector((-3.0, 1.0, 2.0))}
        for k, p in pts.items():
            v = world_to_camera_view(scene, cam, p)
            out[k].append([round(v.x * 1080, 1), round((1 - v.y) * 1920, 1)] if v.z > 0 and 0 <= v.x <= 1 and 0 <= v.y <= 1 else None)
    with open(os.path.join(OUT, "anchors.json"), "w") as fh:
        json.dump(out, fh)

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1 + scn.frame_subframe) / FPS)

anchors()
apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
