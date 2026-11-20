"""Blender scene for 'Sir, this is a Wendy's' (render_wendys.py). Toon kit, objects as the cast.

The set: a fast-food counter running away from camera along +Y, roped off like a boxing corner (three ropes and two
corner posts along its customer side), a cash register on the counter (the cashier, in a visor), a blue boxing glove
on the customer side (the coach, towel and headset), a navy back wall with a generic menu board whose timer counts
down from 0:59 under "ROUND 12", tables, and ceiling panels that are dark until the big moment ("Wendy's").

blender -b --factory-startup -P wendys_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
Writes out_dir/anchors.json (the spotlight pool's screen point per frame) and ../shots.json.
The shot sheet is in ops/episodes/2026-11-15-sir-wendys.md.
"""
import json, math, os, sys
import bpy
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bkit as B
import toon as K
import direct as D

argv = sys.argv[sys.argv.index("--") + 1:]
TIMING, OUT, MODE = argv[0], argv[1], argv[2]
T = json.load(open(TIMING))
FPS, DUR, E = T["fps"], T["duration"], T["events"]
NF = int(round(DUR * FPS))
os.makedirs(OUT, exist_ok=True)
B.clear_scene()
scene = B.scene
AWAY = Vector((0, 0, -1.0e4))
K.setup_world((0.22, 0.24, 0.32))

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

def ramp(t, t0, t1):
    return smooth01((t - t0) / max(1e-3, t1 - t0))

NAVY, NAVY2, CREAM, BLUE = (0.09, 0.13, 0.30), (0.13, 0.18, 0.38), (0.93, 0.90, 0.78), (0.14, 0.38, 0.85)
WHITE, DARK, GREY, YELLOW = (0.97, 0.97, 0.95), (0.12, 0.13, 0.18), (0.55, 0.58, 0.64), (0.97, 0.72, 0.08)
TEAL, ROPE, STEEL, WOOD = (0.05, 0.55, 0.55), (0.88, 0.86, 0.80), (0.62, 0.66, 0.72), (0.60, 0.38, 0.20)

# ------------------------------------------------------------------ the room

for i in range(-6, 6):                                       # floor tiles, 0.8 m checker
    for j in range(-5, 6):
        K.box(f"tile{i}_{j}", (0.8, 0.8, 0.1), CREAM if (i + j) % 2 else NAVY2,
              ((i + 0.5) * 0.8, (j + 0.5) * 0.8 - 1.0, -0.05), bevel=0, line=0)
K.box("backwall", (10, 0.3, 4.2), NAVY, (0, 3.6, 2.1), bevel=0, line=0)
K.box("sidewall", (0.3, 9, 4.2), NAVY, (3.4, -0.5, 2.1), bevel=0, line=0)
LITWALLS = [(K.box("backlit", (10, 0.3, 4.2), (0.30, 0.42, 0.70), (0, 3.58, 2.1), bevel=0, line=0), Vector((0, 3.58, 2.1))),
            (K.box("sidelit", (0.3, 9, 4.2), (0.30, 0.42, 0.70), (3.38, -0.5, 2.1), bevel=0, line=0), Vector((3.38, -0.5, 2.1)))]
K.box("ceiling", (10, 9, 0.2), DARK, (0, -0.5, 3.6), bevel=0, line=0)
K.box("skirt", (10, 0.06, 0.25), (0.05, 0.07, 0.16), (0, 3.43, 0.13), bevel=0, line=0)

# the counter: along +Y, its customer face at x = CX
CX = -0.05
TOP = 1.05
K.box("counter", (1.0, 5.6, TOP - 0.06), CREAM, (CX + 0.5, 0.4, (TOP - 0.06) / 2), bevel=0.03)
K.box("countertop", (1.12, 5.7, 0.08), STEEL, (CX + 0.5, 0.4, TOP - 0.02), bevel=0.02)
K.box("kick", (0.04, 5.6, 0.14), DARK, (CX - 0.01, 0.4, 0.07), bevel=0, line=0)
for y in (3.1,):                                             # a ring corner post with a padded top (the front one blocked the hook)
    K.cyl(f"post{y}", 0.07, 1.85, STEEL, (CX - 0.22, y, 0.92), seg=24)
    K.box(f"pad{y}", (0.2, 0.2, 0.32), BLUE, (CX - 0.22, y, 1.45), bevel=0.05)
for k, z in enumerate((0.30, 0.52, 0.74)):                   # three ring ropes along the counter, under the coach's face
    K.cyl(f"rope{k}", 0.035, 5.4, ROPE if k != 1 else BLUE, (CX - 0.22, 0.4, z), rot=(math.pi / 2, 0, 0), seg=20, line=0.008)

# the menu board on the back wall: generic, navy and yellow, no brand art
MB = Vector((0.55, 3.42, 2.55))
K.box("menu", (2.6, 0.08, 1.15), DARK, MB, bevel=0.03)
K.label("menuR", "ROUND 12", 0.32, WHITE, MB + Vector((0, -0.06, 0.28)))
TIMER = K.label("menuT", "0:59", 0.36, YELLOW, MB + Vector((0, -0.06, -0.15)))
for k, x in enumerate((-0.95, 0.95)):                         # two generic food tiles: a burger and a cup
    o = MB + Vector((x, -0.07, -0.05))
    K.cyl(f"bun{k}", 0.17, 0.08, (0.85, 0.55, 0.22), o + Vector((0, 0, 0.1)), rot=(math.pi / 2, 0, 0), line=0.006) if k == 0 else \
        K.box(f"cup{k}", (0.22, 0.04, 0.34), WHITE, o + Vector((0, 0, 0.02)), bevel=0.02, line=0.006)
STRIP_OFF = K.box("strip_off", (2.6, 0.06, 0.07), (0.25, 0.22, 0.14), MB + Vector((0, -0.05, -0.62)), bevel=0, line=0)
STRIP_ON = K.box("strip_on", (2.6, 0.06, 0.07), YELLOW, MB + Vector((0, -0.05, -0.62)), bevel=0, line=0)
STRIP_ON.data.materials[0] = K.flat(YELLOW)
STRIP_HOME = STRIP_ON.location.copy()

# ceiling panels: dark until the lights come on
PANELS = []
for k, (x, y) in enumerate(((-1.4, -1.2), (0.6, -1.2), (-1.4, 1.4), (0.6, 1.4))):
    off = K.box(f"pan_off{k}", (1.2, 0.6, 0.04), (0.18, 0.19, 0.24), (x, y, 3.48), bevel=0, line=0)
    on = K.box(f"pan_on{k}", (1.2, 0.6, 0.04), WHITE, (x, y, 3.47), bevel=0, line=0)
    on.data.materials[0] = K.flat((1.0, 1.0, 0.97))
    PANELS.append((on, on.location.copy()))

# tables behind the coach, for the wide shot
for k, (x, y) in enumerate(((-2.2, 1.6), (-2.2, -0.6))):
    K.cyl(f"tbl{k}", 0.45, 0.06, WOOD, (x, y, 0.76), seg=32)
    K.cyl(f"tleg{k}", 0.05, 0.74, DARK, (x, y, 0.37), seg=12, line=0)
    for s in (-1, 1):
        K.cyl(f"stool{k}{s}", 0.2, 0.06, TEAL, (x + s * 0.7, y, 0.48), seg=24)
        K.cyl(f"sleg{k}{s}", 0.04, 0.46, DARK, (x + s * 0.7, y, 0.23), seg=12, line=0)

# ------------------------------------------------------------------ the cast

def face(name, body, y, z, parts, eye=0.07, gap=0.13):
    for s, k in ((-1, "L"), (1, "R")):
        lid = K.empty(name + "lid" + k, (s * gap, y, z), body)
        K.ball(name + "eye" + k, eye, (0.99, 0.98, 0.94), (0, 0, 0), lid, squash=(1, 0.35, 1), line=0.006)
        K.ball(name + "pup" + k, eye * 0.47, K.INK, (-s * eye * 0.1, -0.02, -0.01), lid, squash=(1, 0.3, 1), line=0)
        parts["eye" + k] = lid
        brow = K.empty(name + "br" + k, (s * gap, y - 0.02, z + eye * 1.6), body)
        K.box(name + "brow" + k, (eye * 2.1, 0.02, 0.04), K.INK, (0, 0, 0), brow, bevel=0.005, line=0)
        parts["brow" + k] = brow
    mouth = K.empty(name + "m", (0, y, z - eye * 2.5), body)
    K.box(name + "mouth", (eye * 2.6, 0.016, 0.06), K.INK, (0, 0, 0), mouth, bevel=0.01, line=0)
    parts["mouth"] = mouth

def glove(name):
    """The coach: a blue boxing glove with a white cuff, a towel around the cuff and a headset. z=0 at the feet."""
    root = K.empty(name)
    body = K.empty(name + "b", (0, 0, 0.30), root)
    K.ball(name + "mitt", 0.45, BLUE, (0, 0, 0.78), body, squash=(0.92, 0.82, 1.08))
    K.ball(name + "thumb", 0.16, BLUE, (0.40, -0.12, 0.62), body, squash=(0.8, 0.9, 1.4))
    K.cyl(name + "cuff", 0.31, 0.36, WHITE, (0, 0, 0.2), body, seg=40)
    K.box(name + "lace", (0.03, 0.02, 0.3), DARK, (0, -0.31, 0.2), body, bevel=0, line=0)
    K.cyl(name + "towel", 0.36, 0.1, (0.96, 0.95, 0.9), (0, 0, 0.42), body, rot=(0.08, 0.05, 0), seg=40, line=0.008)
    K.box(name + "towelend", (0.16, 0.05, 0.34), (0.96, 0.95, 0.9), (-0.22, -0.31, 0.28), body, rot=(0, 0.12, 0), bevel=0.02,
          line=0.008)
    K.box(name + "band", (0.86, 0.06, 0.05), DARK, (0, 0.02, 1.26), body, bevel=0.02, line=0.006)
    for s in (-1, 1):
        K.box(f"{name}bands{s}", (0.05, 0.06, 0.32), DARK, (s * 0.42, 0.02, 1.1), body, bevel=0.02, line=0.006)
        K.ball(f"{name}cup{s}", 0.09, DARK, (s * 0.43, 0.0, 0.92), body, squash=(0.6, 1, 1), line=0.006)
    K.box(name + "boom", (0.32, 0.03, 0.03), DARK, (-0.27, -0.25, 0.66), body, rot=(0, 0, -0.75), bevel=0, line=0.005)
    K.ball(name + "mic", 0.04, DARK, (-0.13, -0.37, 0.62), body, line=0.005)
    parts = {"root": root, "body": body}
    face(name, body, -0.385, 0.86, parts)
    for s, k in ((-1, "L"), (1, "R")):
        arm = K.empty(name + "arm" + k, (s * 0.38, 0, 0.62), body)
        K.box(name + "armb" + k, (0.48, 0.10, 0.09), (0.10, 0.28, 0.66), (s * 0.24, 0, 0), arm, bevel=0.03)
        K.ball(name + "fist" + k, 0.07, (0.10, 0.28, 0.66), (s * 0.5, 0, 0), arm)
        parts["arm" + k] = arm
        leg = K.empty(name + "leg" + k, (s * 0.15, 0, 0.30), root)
        K.box(name + "legb" + k, (0.11, 0.13, 0.30), (0.10, 0.28, 0.66), (0, 0, -0.15), leg, bevel=0.03)
        parts["leg" + k] = leg
    return parts

def register(name):
    """The cashier: a cream cash register in a teal visor. Its face is on the display. z=0 at its base."""
    root = K.empty(name)
    body = K.empty(name + "b", (0, 0, 0), root)
    K.box(name + "base", (0.62, 0.48, 0.16), CREAM, (0, 0, 0.08), body, bevel=0.03)
    K.box(name + "drawer", (0.5, 0.03, 0.08), GREY, (0, -0.245, 0.08), body, bevel=0.01, line=0.006)
    K.box(name + "keys", (0.58, 0.30, 0.10), CREAM, (0, -0.06, 0.2), body, rot=(-0.35, 0, 0), bevel=0.03)
    for i in range(4):
        for j in range(3):
            K.box(f"{name}k{i}{j}", (0.08, 0.06, 0.03), (0.86, 0.82, 0.70) if (i + j) % 3 else YELLOW,
                  (-0.18 + i * 0.12, -0.16 + j * 0.08, 0.255 + j * 0.03), body, rot=(-0.35, 0, 0), bevel=0.01, line=0.004)
    head = K.empty(name + "head", (0, 0.08, 0.30), body)
    K.box(name + "disp", (0.5, 0.26, 0.4), CREAM, (0, 0, 0.2), head, bevel=0.04)
    K.box(name + "screen", (0.42, 0.02, 0.3), (0.84, 0.92, 0.86), (0, -0.13, 0.2), head, bevel=0.01, line=0.006)
    K.box(name + "visor", (0.52, 0.3, 0.05), TEAL, (0, 0.0, 0.43), head, bevel=0.02)
    K.box(name + "brim", (0.5, 0.2, 0.025), TEAL, (0, -0.2, 0.42), head, rot=(0.15, 0, 0), bevel=0.01)
    K.box(name + "slot", (0.2, 0.06, 0.02), DARK, (0.12, 0.05, 0.405), head, bevel=0, line=0)
    rec = K.empty(name + "rec", (0.12, 0.05, 0.40), head)
    K.box(name + "paper", (0.16, 0.01, 0.4), WHITE, (0, 0, 0.2), rec, bevel=0, line=0.004)
    for k in range(4):
        K.box(f"{name}pl{k}", (0.1, 0.004, 0.012), GREY, (0, -0.007, 0.32 - k * 0.07), rec, bevel=0, line=0)
    parts = {"root": root, "body": body, "head": head, "rec": rec}
    face(name, head, -0.145, 0.22, parts, eye=0.055, gap=0.1)
    for s, k in ((-1, "L"), (1, "R")):
        arm = K.empty(name + "arm" + k, (s * 0.31, 0, 0.12), body)
        K.box(name + "armb" + k, (0.18, 0.08, 0.07), (0.78, 0.74, 0.62), (s * 0.09, 0, 0), arm, bevel=0.025)
        parts["arm" + k] = arm
    return parts

GL = glove("gl")
RG = register("rg")
GL_POS = Vector((-0.55, -0.10, 0.0))
RG_POS = Vector((0.30, 0.10, TOP + 0.02))
GL_ROT = math.radians(58)              # faces the register, cheated toward camera
RG_ROT = math.radians(-58)
for p in (GL, RG):
    for k in ("eyeL", "eyeR"):
        p[k]["home"] = list(p[k].scale)

def wpt(p, local, rot, pos):
    return pos + Matrix.Rotation(rot, 3, "Z") @ Vector(local)

GL_FACE = wpt(GL, (0, -0.3, 0.30 + 0.86), GL_ROT, GL_POS)
RG_FACE = wpt(RG, (0, -0.1, 0.30 + 0.22 + 0.08), RG_ROT, RG_POS)
MID = (GL_FACE + RG_FACE) / 2 + Vector((0, 0, -0.1))

# ------------------------------------------------------------------ camera and shots

cam = B.camera(lens=35, fstop=16.0)
rig = D.Rig(cam, {})
cam.data.dof.use_dof = False

SH = [
    D.Shot("hook", 0.0, MID, lens=30, dist=2.7, yaw=4, pitch=-4, screen=(0.5, 0.52),
           note="frame 0: the glove mid-shout gripping the register over the roped counter; ROUND 12 behind"),
    D.Shot("face", E["they"], GL_FACE + Vector((0, 0, -0.05)), lens=50, dist=1.5, yaw=22, pitch=-6, screen=(0.5, 0.48),
           move=("push", 0.06), note="close on the coach; each 'Too' pushes the glove at camera"),
    D.Shot("cashier", E["B"], RG_FACE, lens=40, dist=2.0, yaw=-40, pitch=-4, screen=(0.5, 0.5),
           note="over the glove's shoulder: the register's blank face"),
    D.Shot("hero", E["tonight"], GL_FACE + Vector((0, 0, -0.1)), lens=24, dist=1.7, yaw=-6, pitch=18, screen=(0.5, 0.46),
           move=("push", 0.1), note="low angle, the glove's fist up"),
    D.Shot("wendys", E["C"], RG_FACE + Vector((0, 0, -0.08)), lens=35, dist=1.7, yaw=-58, pitch=-2, screen=(0.5, 0.5),
           hit=E["wendys"], note="frontal, locked: silence on 'Sir', the lights come on with 'Wendy's'"),
    D.Shot("order", E["D"], MID + Vector((-0.1, 0.2, 0.1)), lens=26, dist=4.0, yaw=6, pitch=-7, screen=(0.5, 0.55),
           note="wide two-shot under flat light; the receipt prints on 'champion'"),
    D.Shot("loop", E["E"], MID, lens=30, dist=2.7, yaw=4, pitch=-4, screen=(0.5, 0.52),
           note="back to the hook framing so the reel loops"),
]
SHOTS = D.ShotList(SH, DUR)
SHOTS.check()
SHOTS.dump(os.path.join(os.path.dirname(OUT.rstrip("/\\")), "shots.json"), big=E["wendys"])

# ------------------------------------------------------------------ the timeline

COACH_W = E.get("coach_words", [])
CASH_W = E.get("cash_words", [])

def talk(t, starts):
    """Mouth open 0..1 from the word onsets: open fast on each word, close over 0.18 s."""
    v = 0.0
    for s in starts:
        if s - 0.03 <= t < s + 0.25:
            v = max(v, min(1.0, (t - s + 0.03) / 0.05) * max(0.0, 1 - (t - s) / 0.25))
    return v

def lights_on(t):
    return E["wendys"] - 0.01 <= t < E["E"]

def apply_state(t):
    q = math.floor(t * 12) / 12                              # the cast moves in stop motion, 12 steps a second
    coach_talking = t < E["C"] or (E["D"] <= t < E["E"]) or t >= E["E"]
    calm = E["D"] <= t < E["E"]
    hero = E["tonight"] - 0.1 <= t < E["C"]
    loop = t >= E["E"]
    # coach
    gape = talk(q, COACH_W) if coach_talking else 0.0
    if t < 0.4 or loop:
        gape = max(gape, 0.85)                                # frame 0 already mid-shout (the thumbnail)
    shove = 0.0
    for k in ("too1", "too2", "too3", "soft"):
        u = q - E[k]
        if 0 <= u < 0.3:
            shove = max(shove, (1 - u / 0.3))
    GL["root"].location = GL_POS + Matrix.Rotation(GL_ROT, 3, "Z") @ Vector((0, -0.06 * shove, 0.02 * abs(math.sin(q * 9))))
    turn = ramp(t, E["tonight"] - 0.15, E["tonight"] + 0.1) if hero else 0.0   # turns to the crowd for 'Tonight'
    GL["root"].rotation_euler = (0.08 * shove, 0, GL_ROT + (math.radians(8) - GL_ROT) * turn)
    GL["mouth"].scale = (1 - 0.3 * gape * (0.5 if calm else 1), 1, 1 + 3.2 * gape * (0.5 if calm else 1))
    K.mood(GL, 1.0 if not calm else 0.35)
    if hero:
        GL["armL"].rotation_euler = (0, 0, 1.15)
        GL["armR"].rotation_euler = (0, -1.3 * ramp(t, E["tonight"] - 0.1, E["tonight"] + 0.15), -0.3)
    elif calm:
        let = ramp(t, E["D"], E["D"] + 0.3)
        GL["armL"].rotation_euler = (0, -1.1 * let, 1.15 * (1 - let))
        GL["armR"].rotation_euler = (0, 1.1 * let, -1.15 * (1 - let))
    else:
        GL["armL"].rotation_euler = (0, 0, 1.15)               # both fists forward on the register's sides
        GL["armR"].rotation_euler = (0, 0, -1.15)
    # cashier: jolts with each shove, blank, one blink on 'Sir', talks on its lines
    jolt = 0.025 * shove * math.sin(q * 40)
    RG["root"].location = RG_POS + Vector((jolt, 0, 0))
    RG["root"].rotation_euler = (0, 0, RG_ROT)
    rg_gape = talk(q, CASH_W) * 0.45
    RG["mouth"].scale = (1, 1, 1 + 2.0 * rg_gape)
    K.mood(RG, -0.15)
    blink = 0.1 if (E["sir"] - 0.25 <= q < E["sir"] - 0.12) or (E["B"] + 1.2 <= q < E["B"] + 1.32) else 1.0
    for k in ("eyeL", "eyeR"):
        h = RG[k]["home"]
        RG[k].scale = (h[0], h[1], h[2] * blink)
    RG["armL"].rotation_euler = (0, -0.9, 0)
    RG["armR"].rotation_euler = (0, 0.9, 0)
    # the receipt prints on 'champion'
    pr = ramp(t, E["champion"] - 0.05, E["champion"] + 0.5) if E["D"] <= t < E["E"] else 0.0
    RG["rec"].location = Vector((0.12, 0.05, 0.40)) if pr > 0.01 else AWAY
    RG["rec"].scale = (1, 1, max(0.01, pr))
    # the room: lights and the menu strip come on with 'Wendy's'; the timer counts down from 0:59
    on = lights_on(t)
    for ob, home in PANELS:
        ob.location = home if on else AWAY
    STRIP_ON.location = STRIP_HOME if on else AWAY
    for ob, home in LITWALLS:
        ob.location = home if on else AWAY
    sec = max(0, 59 - int(t))
    TIMER.data.body = f"0:{sec:02d}"
    SHOTS.apply(rig, t)

# ------------------------------------------------------------------ anchors for the 2D spotlight

def proj(p):
    v = world_to_camera_view(scene, cam, p)
    return [round(v.x * 1080, 1), round((1 - v.y) * 1920, 1)] if v.z > 0 else None

def anchors():
    out = {"pool": []}
    vl = bpy.context.view_layer
    for f in range(NF):
        t = f / FPS
        apply_state(t)
        vl.update()
        out["pool"].append(proj(SHOTS.at(t).eye))
    with open(os.path.join(OUT, "anchors.json"), "w") as fh:
        json.dump(out, fh)

B.render_settings(FPS, samples=12, motion_blur=0.0)
K.flat_look()
try:
    scene.eevee.use_raytracing = False
    scene.eevee.use_fast_gi = False
except Exception as ex:
    print("skip", ex)

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1) / FPS)

anchors()
apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
