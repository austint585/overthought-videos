"""Blender scene for 'Height inflation': cel-shaded sets along x, 14 m apart, each with a floor, a colored back wall and a hanging
sign. Our tape measure mascot moves between them in stop motion (12 steps a second, the camera stays smooth). Shots, timed by
render_height.py: stamp, press, chart, door, stairs, flood, stairs2, vault, boot, hair, hill, bed, clock, gold, final.

blender -b --factory-startup -P height_scene.py -- timing.json out_dir MODE   (MODE: 'all' or 1-based frame list)
"""
import json, math, os, random, sys
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bkit as B
import toon as K

argv = sys.argv[sys.argv.index("--") + 1:]
TIMING, OUT, MODE = argv[0], argv[1], argv[2]
T = json.load(open(TIMING))
FPS, DUR, SHOTS, FLIP = T["fps"], T["duration"], T["shots"], T["flip"]
NF = int(round(DUR * FPS))
os.makedirs(OUT, exist_ok=True)
B.clear_scene()
scene = B.scene
AWAY = Vector((0, 0, -1.0e4))
K.setup_world()

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

def setx(i):
    return Vector((i * 14.0, 0, 0))

def stage(i, wall, floor):
    o = setx(i)
    K.box(f"floor{i}", (13.5, 12, 0.3), floor, o + Vector((0, -2.5, -0.15)), bevel=0, line=0)
    K.box(f"wall{i}", (13.5, 0.3, 9), wall, o + Vector((0, 2.2, 4.5)), bevel=0, line=0)
    K.box(f"skirt{i}", (13.5, 0.06, 0.28), tuple(c * 0.7 for c in wall), o + Vector((0, 2.03, 0.14)), bevel=0, line=0)
    return o

NAVY, CREAM, RED, BLUE, TEAL, PINK, GOLD, GREEN = (0.08, 0.12, 0.30), (0.93, 0.90, 0.76), (0.82, 0.13, 0.11), (0.14, 0.50, 0.90), \
    (0.05, 0.62, 0.60), (0.93, 0.18, 0.48), (0.98, 0.72, 0.08), (0.20, 0.62, 0.20)
GREY, DARK, WOOD, SKY = (0.55, 0.58, 0.64), (0.13, 0.14, 0.20), (0.62, 0.36, 0.16), (0.32, 0.66, 0.96)

# ------------------------------------------------------------------ 0 stamp: profile cards on a belt under a giant stamp

O0 = stage(0, NAVY, CREAM)
K.box("belt", (4.4, 1.0, 0.22), DARK, O0 + Vector((0, 0, 0.62)), bevel=0.05)
for x in (-1.8, 1.8):
    K.box(f"beltleg{x}", (0.2, 0.7, 0.52), GREY, O0 + Vector((x, 0, 0.26)), bevel=0.03)
CARDS = []
for i in range(6):
    r = K.empty(f"card{i}")
    K.box(f"cardb{i}", (0.62, 0.84, 0.03), (0.98, 0.96, 0.9), (0, 0, 0), r, bevel=0.01, line=0.008)
    K.ball(f"cardh{i}", 0.09, (0.3 + 0.1 * i % 0.5, 0.5, 0.7), (0, 0.2, 0.025), r, squash=(1, 1, 0.15), line=0)
    t = K.label(f"cardt{i}", "6'0\"", 0.24, RED, (0, -0.16, 0.022), r)
    t.rotation_euler = (0, 0, 0)
    CARDS.append(r)
STAMP = K.empty("stamp")
K.box("stampb", (0.82, 1.0, 0.16), RED, (0, 0, 0.08), STAMP, bevel=0.03)
K.box("stampn", (0.26, 0.26, 0.5), WOOD, (0, 0, 0.38), STAMP, bevel=0.04)
K.ball("stamph", 0.23, (0.55, 0.3, 0.12), (0, 0, 0.74), STAMP)
K.box("stampshaft", (0.09, 0.09, 6.0), GREY, (0, 0, 3.8), STAMP, bevel=0.01, line=0.008)

# ------------------------------------------------------------------ 1 press: the machine, money coming out, the sign drops

O1 = stage(1, RED, CREAM)
K.box("press", (2.5, 1.5, 2.1), GREY, O1 + Vector((0, 0.5, 1.05)), bevel=0.08)
K.box("pressmouth", (1.8, 0.1, 0.3), DARK, O1 + Vector((0, -0.28, 0.72)), bevel=0.02, line=0)
K.box("pressband", (2.54, 1.54, 0.18), GOLD, O1 + Vector((0, 0.5, 1.72)), bevel=0.02, line=0.008)
ROLLS = []
for x in (-0.75, 0.75):
    r = K.cyl(f"roll{x}", 0.42, 0.16, (0.7, 0.72, 0.76), O1 + Vector((x, -0.3, 1.32)), rot=(0, math.pi / 2, 0))
    K.box(f"spoke{x}", (0.05, 0.72, 0.05), DARK, (0, 0, 0), r, bevel=0, line=0)
    ROLLS.append(r)
K.label("presst", "U.S. MINT OF INCHES", 0.22, K.INK, O1 + Vector((0, -0.29, 1.72)))
def bill(name, parent=None):
    r = K.empty(name, parent=parent)
    K.box(name + "b", (0.62, 0.34, 0.012), (0.38, 0.72, 0.36), (0, 0, 0), r, bevel=0.003, line=0.007)
    t = K.label(name + "t", "6'0\"", 0.17, (0.05, 0.25, 0.08), (0, -0.01, 0.01), r)
    t.rotation_euler = (0, 0, 0)
    return r
MONEY = [bill(f"m{i}") for i in range(14)]
S_INFL = K.sign("s_infl", ["HEIGHT", "INFLATION"], AWAY, w=2.3)

# ------------------------------------------------------------------ 2 chart: two bars and the gap

O2 = stage(2, TEAL, CREAM)
K.box("chartbase", (3.0, 0.8, 0.14), DARK, O2 + Vector((0, 0, 0.07)), bevel=0.02)
BAR_REAL = K.box("barreal", (0.95, 0.6, 1.0), BLUE, AWAY, bevel=0.03)
BAR_LIST = K.box("barlist", (0.95, 0.6, 1.0), PINK, AWAY, bevel=0.03)
K.label("lreal", "ACTUAL", 0.2, (1, 1, 1), O2 + Vector((-0.75, -0.42, 0.075)))
K.label("llist", "LISTED", 0.2, (1, 1, 1), O2 + Vector((0.75, -0.42, 0.075)))
GAP = K.box("gap", (0.97, 0.62, 0.45), (0.98, 0.45, 0.1), AWAY, bevel=0.02)
S_2 = K.sign("s_2in", ["2 INCHES"], O2 + Vector((0, 0.7, 3.0)), w=2.1, head="OKCUPID, 2010")

# ------------------------------------------------------------------ 3 door: a doorframe with pencil marks

O3 = stage(3, (0.92, 0.60, 0.20), (0.56, 0.33, 0.16))
K.box("doorl", (0.26, 0.3, 3.0), CREAM, O3 + Vector((-1.0, 0.8, 1.5)), bevel=0.02)
K.box("doorr", (0.26, 0.3, 3.0), CREAM, O3 + Vector((1.0, 0.8, 1.5)), bevel=0.02)
K.box("doort", (2.26, 0.3, 0.26), CREAM, O3 + Vector((0, 0.8, 3.1)), bevel=0.02)
K.box("doorin", (1.74, 0.1, 2.98), (0.25, 0.14, 0.08), O3 + Vector((0, 1.0, 1.49)), bevel=0, line=0)
for i, s in enumerate(("5'7\"", "5'8\"", "5'9\"", "5'10\"", "5'11\"", "6'0\"")):
    z = 1.05 + i * 0.25
    K.box(f"mark{i}", (0.2, 0.01, 0.018), K.INK, O3 + Vector((-1.0, 0.645, z)), bevel=0, line=0)
    K.label(f"markt{i}", s, 0.13, RED if s == "5'9\"" else K.INK, O3 + Vector((-1.0, 0.64, z + 0.085)))
S_59 = K.sign("s_59", ["5'9\""], O3 + Vector((0.3, -0.3, 3.45)), w=1.7, head="THE REAL AVERAGE")

# ------------------------------------------------------------------ 4 stairs: each step a height, used twice (the 2nd higher up)

O4 = stage(4, PINK, CREAM)
STEPS = ["5'9\"", "5'10\"", "5'11\"", "6'0\"", "6'1\"", "6'2\""]
STEP_C = [BLUE, TEAL, GREEN, GOLD, (0.95, 0.45, 0.1), RED]
def step_at(i):
    return O4 + Vector((-2.2 + i * 1.05, 0.0, 0.0)), 0.42 * (i + 1)
for i, s in enumerate(STEPS):
    p, h = step_at(i)
    K.box(f"step{i}", (1.05, 1.6, h), STEP_C[i], p + Vector((0, 0, h / 2)), bevel=0.02)
    K.label(f"stept{i}", s, 0.3, (1, 1, 1), p + Vector((0, -0.82, h - 0.21)))
S_NOPE = K.sign("s_nope", ["NOBODY STOPS", "AT 5'11\""], AWAY, w=2.7)
S_PRINT = K.sign("s_print", ["KEEP PRINTING"], AWAY, w=2.7)

# ------------------------------------------------------------------ 5 flood: bills piling up around a price tag

O5 = stage(5, (0.28, 0.42, 0.20), CREAM)
PILE = []
prng = random.Random(7)
for i in range(70):
    b = bill(f"p{i}")
    a, d = prng.uniform(0, 6.283), prng.uniform(0, 1.0) ** 0.6 * 2.5
    PILE.append((b, Vector((d * math.cos(a), d * math.sin(a) * 0.7 - 0.4, 0.02 + 0.5 * max(0.0, 1 - d / 2.5) ** 1.3 * prng.random())),
                 (prng.uniform(-0.25, 0.25), prng.uniform(-0.25, 0.25), prng.uniform(0, 6.28)), prng.uniform(0, 0.7)))
S_FLOOD = K.sign("s_flood", ["6'0\" = $0"], O5 + Vector((0, 0.6, 3.25)), w=2.2, head="TODAY'S RATE")

# ------------------------------------------------------------------ 6 vault: three exhibits on pedestals

O6 = stage(6, (0.24, 0.26, 0.34), (0.42, 0.43, 0.48))
K.cyl("vaultring", 2.9, 0.3, (0.62, 0.64, 0.68), O6 + Vector((0, 1.9, 2.9)), rot=(math.pi / 2, 0, 0), line=0.02, seg=64)
K.cyl("vaultin", 2.45, 0.31, (0.06, 0.07, 0.10), O6 + Vector((0, 1.88, 2.9)), rot=(math.pi / 2, 0, 0), line=0, seg=64)
S_V = K.sign("s_vault", ["THE RESERVES"], O6 + Vector((0, 0.4, 3.9)), w=2.5)
EX = {n: O6 + Vector((x, 0.0, 0)) for n, x in (("boot", -1.6), ("hair", 0.0), ("hill", 1.6))}
for n, p in EX.items():
    K.box("ped" + n, (1.2, 1.2, 0.8), (0.72, 0.74, 0.78), p + Vector((0, 0, 0.4)), bevel=0.03)
BT = EX["boot"] + Vector((0, 0, 0.8))
K.box("lift", (0.74, 0.34, 0.24), (0.96, 0.82, 0.3), BT + Vector((0.02, 0, 0.12)), bevel=0.03)
K.box("sole", (0.76, 0.36, 0.08), DARK, BT + Vector((0.02, 0, 0.28)), bevel=0.02)
K.box("foot", (0.70, 0.32, 0.22), (0.45, 0.24, 0.1), BT + Vector((0.03, 0, 0.42)), bevel=0.08)
K.box("shin", (0.32, 0.30, 0.56), (0.45, 0.24, 0.1), BT + Vector((-0.16, 0, 0.78)), bevel=0.04)
HR = EX["hair"] + Vector((0, 0, 0.8))
K.ball("skull", 0.3, (0.96, 0.74, 0.58), HR + Vector((0, 0, 0.26)))
for i in range(9):
    a = -1.25 + i * 2.5 / 8
    K.ball(f"tuft{i}", 0.15, (0.2, 0.11, 0.05), HR + Vector((0.3 * math.sin(a), 0, 0.56 + 0.34 * math.cos(a) + 0.3 * (1 - abs(a) / 1.3))), squash=(1, 1, 1.5), line=0.01)
HL = EX["hill"] + Vector((0, 0, 0.8))
K.ball("hillb", 0.56, GREEN, HL, squash=(1, 1, 0.75))
K.box("flag", (0.02, 0.02, 0.36), DARK, HL + Vector((0, 0, 0.56)), bevel=0, line=0)
K.box("flagc", (0.2, 0.012, 0.12), RED, HL + Vector((0.1, 0, 0.68)), bevel=0, line=0.005)

# ------------------------------------------------------------------ 7 bed and alarm clock

O7 = stage(7, (0.44, 0.34, 0.74), (0.60, 0.35, 0.17))
K.box("bedf", (2.6, 1.5, 0.38), (0.45, 0.25, 0.12), O7 + Vector((-0.2, 0.3, 0.3)), bevel=0.04)
K.box("matt", (2.5, 1.42, 0.24), CREAM, O7 + Vector((-0.2, 0.3, 0.6)), bevel=0.08)
K.box("pillow", (0.6, 0.9, 0.18), (1, 1, 1), O7 + Vector((-1.1, 0.3, 0.8)), bevel=0.08)
K.box("blanket", (1.5, 1.46, 0.1), BLUE, O7 + Vector((0.28, 0.3, 0.74)), bevel=0.04)
K.box("night", (0.7, 0.7, 0.72), WOOD, O7 + Vector((1.55, 0.3, 0.36)), bevel=0.03)
CLK = K.empty("clk", O7 + Vector((1.55, 0.3, 0.72)))
K.box("clkb", (0.62, 0.34, 0.38), RED, (0, 0, 0.19), CLK, bevel=0.05)
K.box("clks", (0.5, 0.02, 0.24), (0.03, 0.05, 0.05), (0, -0.17, 0.19), CLK, bevel=0.01, line=0)
K.label("clkt", "7:00", 0.19, (0.3, 1.0, 0.45), (0, -0.19, 0.19), CLK)
for x in (-0.18, 0.18):
    K.ball(f"bell{x}", 0.12, GOLD, (x, 0, 0.47), CLK)
S_CM = K.sign("s_cm", ["+1 CM"], O7 + Vector((-0.2, 0.6, 3.1)), w=1.5, head="BEST BEFORE 8 A.M.")

# ------------------------------------------------------------------ 8 gold: the last honest man on a gold bar

O8 = stage(8, (0.10, 0.09, 0.14), (0.20, 0.18, 0.26))
K.box("goldbar", (1.8, 0.95, 0.5), GOLD, O8 + Vector((0, 0, 0.25)), bevel=0.05)
K.box("goldtop", (1.4, 0.65, 0.2), (1.0, 0.82, 0.2), O8 + Vector((0, 0, 0.6)), bevel=0.05)
K.label("goldt", "5'7\"", 0.32, (0.4, 0.2, 0.02), O8 + Vector((0, -0.48, 0.25)))
GLOW = K.cyl("pool", 1.5, 0.01, (0.98, 0.86, 0.42), O8 + Vector((0, 0, 0.012)), line=0, seg=64)
CROWN = K.empty("crown")
K.cyl("crownb", 0.15, 0.08, GOLD, (0, 0, 0.04), CROWN, line=0.006)
for i in range(5):
    a = i * 2 * math.pi / 5
    K.ball(f"crownp{i}", 0.04, GOLD, (0.13 * math.cos(a), 0.13 * math.sin(a), 0.11), CROWN, line=0.006)
S_GOLD = K.sign("s_gold", ["GOLD STANDARD"], AWAY, w=2.5)
S_FRIEND = K.sign("s_friend", ["GREAT FRIEND"], AWAY, w=2.3)
S_HE = K.sign("s_he", ["SAYS 5'7\"", "IS 5'7\""], O8 + Vector((0, 0.3, 2.65)), w=1.9)

# ------------------------------------------------------------------ the cast and the camera

TAPE = K.mascot("tape")
cam = B.camera(lens=42, fstop=16.0)
cam.data.dof.use_dof = False
cam.data.clip_start = 0.05
cam.data.clip_end = 80

def lc(a, b, tg, lens, u, o):
    return o + Vector(a).lerp(Vector(b), smooth01(u)), o + Vector(tg), lens

CAMS = {
    "stamp": lambda u: lc((-1.6, -5.3, 1.8), (-1.2, -4.6, 1.75), (0, 0, 1.55), 40, u, O0),
    "press": lambda u: lc((1.0, -6.2, 1.5), (0.5, -5.4, 1.6), (0, 0, 2.0), 40, u, O1),
    "chart": lambda u: lc((-1.0, -7.6, 1.7), (-0.6, -6.9, 1.7), (0, 0, 1.75), 40, u, O2),
    "door": lambda u: lc((0.7, -7.2, 1.5), (0.4, -6.4, 1.5), (0, 0, 1.9), 40, u, O3),
    "stairs": lambda u: lc((-2.0, -6.0, 1.6), (-0.4, -5.8, 1.7), (-0.5, 0, 1.75), 40, u, O4),
    "stairs2": lambda u: lc((0.4, -5.6, 2.2), (1.7, -5.8, 2.6), (1.0, 0, 2.4), 40, u, O4),
    "flood": lambda u: lc((-0.8, -6.0, 2.1), (-0.2, -5.2, 1.9), (0, 0, 1.75), 40, u, O5),
    "vault": lambda u: lc((0.0, -7.6, 2.0), (0.0, -6.6, 2.0), (0, 0, 2.2), 40, u, O6),
    "boot": lambda u: lc((-1.9, -2.5, 1.5), (-1.8, -2.1, 1.45), (-1.6, 0, 1.45), 42, u, O6),
    "hair": lambda u: lc((0.3, -2.5, 1.5), (0.2, -2.1, 1.5), (0, 0, 1.5), 42, u, O6),
    "hill": lambda u: lc((1.3, -2.5, 1.5), (1.4, -2.1, 1.45), (1.6, 0, 1.35), 42, u, O6),
    "bed": lambda u: lc((-0.8, -5.0, 1.6), (-0.3, -4.4, 1.6), (0, 0, 1.6), 40, u, O7),
    "clock": lambda u: lc((1.85, -1.5, 1.15), (1.75, -1.15, 1.1), (1.55, 0.3, 1.05), 42, u, O7),
    "gold": lambda u: lc((-0.7, -6.4, 1.5), (-0.3, -5.4, 1.5), (0, 0, 1.6), 40, u, O8),
    "final": lambda u: lc((0.5, -5.4, 1.4), (0.2, -4.6, 1.4), (0, 0, 1.7), 40, u, O8),
}

def base_of(i):
    return SHOTS[i][1].split("~")[0]

def shot_at(t):
    k = max([0] + [i for i, (s, _) in enumerate(SHOTS) if t >= s - 1e-6])
    t1 = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    cut = max(0.0, min(1.0, (t - SHOTS[k][0]) / max(1e-6, t1 - SHOTS[k][0])))
    a = b = k
    while a > 0 and base_of(a - 1) == base_of(k):
        a -= 1
    while b + 1 < len(SHOTS) and base_of(b + 1) == base_of(k):
        b += 1
    t0 = SHOTS[a][0]
    t2 = SHOTS[b + 1][0] if b + 1 < len(SHOTS) else DUR
    return base_of(k), max(0.0, min(1.0, (t - t0) / max(1e-6, t2 - t0))), t - t0, cut, "~" in SHOTS[k][1], t2 - t0

def alt_cam(base, u):
    loc, tg, lens = base(u)
    return tg + (Matrix.Rotation(-0.5, 3, "Z") @ (loc - tg)) * 0.85 + Vector((0, 0, 0.3)), tg, lens

def drop(ob, at, age, delay=0.0):
    """A sign falling in on its cords with a little overshoot."""
    u = max(0.0, age - delay) / 0.4
    z = 4.5 * max(0.0, 1 - u) ** 2 - (0.12 * math.sin(min(u, 2.0) * 6) * max(0.0, 1 - u / 2) if u > 1 else 0)
    ob.location = at + Vector((0, 0, z))

def pose(p, at, hop=0.0, sway=0.0, arm=0.0, scale=1.0, angry=1.0, yaw=0.0):
    p["root"].location = at + Vector((0, 0, hop))
    p["root"].rotation_euler = (0, sway, yaw)
    p["root"].scale = (scale, scale, scale)
    p["armL"].rotation_euler = (0, -arm, 0)
    p["armR"].rotation_euler = (0, arm, 0)
    p["legL"].rotation_euler = (0.5 * math.sin(hop * 12) if hop else 0, 0, 0)
    p["legR"].rotation_euler = (-0.5 * math.sin(hop * 12) if hop else 0, 0, 0)
    K.mood(p, angry)

def apply_state(t):
    name, u, age, cut, second, length = shot_at(t)
    q = math.floor(t * 12) / 12            # props step in stop motion
    aq = age - (t - q)
    loc, tg, lens = alt_cam(CAMS[name], cut) if second else CAMS[name](cut)
    B.aim(cam, loc, tg)
    cam.data.lens = lens

    for o in [TAPE["root"], STAMP, BAR_REAL, BAR_LIST, GAP, S_INFL, S_NOPE, S_PRINT, S_GOLD, S_FRIEND, CROWN] + CARDS + MONEY:
        o.location = AWAY
    for b, *_ in PILE:
        b.location = AWAY
    TAPE["root"].scale = (1, 1, 1)
    CROWN.scale = (1, 1, 1)

    if name == "stamp":
        beat = (q % 0.6) / 0.6
        press = 0.0 if beat < 0.22 else smooth01((beat - 0.22) / 0.78)
        STAMP.location = O0 + Vector((0.0, 0, 0.75 + 1.25 * press))
        for i, c in enumerate(CARDS):
            x = -2.5 + ((math.floor(q / 0.6) + smooth01((beat - 0.3) / 0.6)) * 0.85 + i * 0.85) % 5.1
            c.location = O0 + Vector((x, 0, 0.75))
        pose(TAPE, O0 + Vector((-0.72, -1.2, 0)), hop=0.1 * abs(math.sin(q * 5.2)), arm=0.8 * math.sin(q * 10.4))
    elif name == "press":
        for r, s in zip(ROLLS, (1, -1)):
            r.rotation_euler = (q * 8 * s, math.pi / 2, 0)
        rng = random.Random(3)
        for i, m in enumerate(MONEY):
            ph = (q * 0.9 + i / 14) % 1.0
            x0 = rng.uniform(-0.7, 0.7)
            m.location = O1 + Vector((x0 + (x0 * 1.8) * ph, -0.4 - 2.4 * ph, 0.72 + 1.2 * ph - 2.6 * ph * ph))
            m.rotation_euler = (ph * 5 + i, ph * 3, i)
            if m.location.z < O1.z + 0.02:
                m.location = AWAY
        drop(S_INFL, O1 + Vector((0, -0.4, 3.75)), aq, 0.2)
        pose(TAPE, O1 + Vector((1.6, -1.3, 0)), sway=-0.1 * math.sin(q * 6), arm=0.5, yaw=0.3)
    elif name == "chart":
        real = 1.55 * smooth01(aq / 0.5)
        lst = 1.55 * smooth01((aq - 0.2) / 0.5)
        BAR_REAL.location, BAR_REAL.scale = O2 + Vector((-0.75, 0, 0.14 + real / 2)), (1, 1, max(0.01, real))
        BAR_LIST.location, BAR_LIST.scale = O2 + Vector((0.75, 0, 0.14 + lst / 2)), (1, 1, max(0.01, lst))
        g = smooth01((aq - 2.0) / 0.5)
        if g > 0:
            GAP.location = O2 + Vector((0.75, 0, 0.14 + lst + 0.225 * g))
            GAP.scale = (1, 1, max(0.02, g))
        pose(TAPE, O2 + Vector((-0.75, -0.0, 0.14 + real)), hop=0.04 * abs(math.sin(q * 6)), arm=0.6, yaw=-0.5)
    elif name == "door":
        pose(TAPE, O3 + Vector((0, 0.15, 0)), arm=-0.3 + 0.2 * math.sin(q * 5), sway=0.03 * math.sin(q * 3), scale=2.1 / 0.82 * 0.62)
    elif name in ("stairs", "stairs2"):
        n0 = 0 if name == "stairs" else 3
        n = n0 + min(2 if name == "stairs2" else 3, int(aq / 0.62))
        f = (aq / 0.62) % 1.0 if n < (n0 + (2 if name == "stairs2" else 3)) else 1.0
        p, h = step_at(n)
        pn, hn = step_at(min(5, n + 1))
        ff = smooth01(f * 2.4) if n < (n0 + (2 if name == "stairs2" else 3)) else 0.0
        at = p.lerp(pn, ff) + Vector((0, -0.05, h + (hn - h) * ff + 0.55 * math.sin(ff * math.pi)))
        pose(TAPE, at, arm=0.9 * math.sin(ff * math.pi), sway=-0.2 * math.sin(ff * math.pi))
        follow = Vector((p.x * (1 - ff) + pn.x * ff, 0, h + (hn - h) * ff))
        tg = follow + Vector((0, 0, 0.4))
        loc = tg + Vector((-0.7 + 0.5 * cut, -6.0 if not second else -5.0, 0.2))
        B.aim(cam, loc, tg)
        at_sign = Vector((follow.x, O4.y + 0.9, follow.z + 2.35))
        if name == "stairs":
            drop(S_NOPE, at_sign, aq, length * 0.4)
        else:
            drop(S_PRINT, at_sign, aq, 0.3)
    elif name == "flood":
        for b, p, r, delay in PILE:
            f = min(1.0, max(0.0, (aq - delay * length * 0.5) / 0.5))
            b.location = O5 + p + Vector((0, 0, 4.5 * (1 - f) ** 2))
            b.rotation_euler = (r[0] + (1 - f) * 3, r[1], r[2] + (1 - f) * 2)
        pose(TAPE, O5 + Vector((0.2, -1.2, 0.35)), angry=smooth01(1 - aq / max(0.1, length)) * 2 - 1, arm=-0.6)
    elif name == "vault":
        pose(TAPE, O6 + Vector((-0.1, -1.4, 0)), arm=0.5 + 0.3 * math.sin(q * 6), yaw=0.2)
    elif name == "bed":
        wake = smooth01((aq - 0.25) / 0.3)
        pose(TAPE, O7 + Vector((-0.5, 0.25, 0.72 + 0.1 * wake)), arm=1.1 * wake, angry=wake * 2 - 1 if wake < 1 else 1)
    elif name == "clock":
        CLK.rotation_euler = (0, 0.09 * math.sin(q * 60), 0)
    elif name == "gold":
        pose(TAPE, O8 + Vector((0, -0.02, 0.7)), scale=0.74, sway=0.03 * math.sin(q * 3), arm=0.25)
        CROWN.location = O8 + Vector((0, -0.02, 0.7 + 0.74 * 0.8))
    elif name == "final":
        flip = t >= FLIP
        S = S_FRIEND if flip else S_GOLD
        S.location = O8 + Vector((0, 0.3, 2.65))
        S.rotation_euler = (0, 0, 0)
        S_HE.location = AWAY
        drop_u = smooth01((t - FLIP) / 0.35) if flip else 1.0
        if flip:
            S.rotation_euler = (0, 0, (1 - drop_u) * math.pi)
        pose(TAPE, O8 + Vector((0, -0.02, 0.7)), scale=0.74, arm=-0.4 if flip else 0.5, angry=-1.0 if flip else 1.0, sway=0.05 if flip else 0.0)
        CROWN.location = O8 + (Vector((0.42, -0.25, 0.72)) if flip else Vector((0, -0.02, 0.7 + 0.74 * 0.8)))
        CROWN.rotation_euler = (0, 1.3, 0) if flip else (0, 0, 0)
    if name != "final":
        S_HE.location = O8 + Vector((0, 0.3, 2.65))

B.render_settings(FPS, samples=int(os.environ.get("HEIGHT_SAMPLES", "12")), motion_blur=0.0)
K.flat_look()
try:
    scene.eevee.use_raytracing = False
    scene.eevee.use_fast_gi = False
except Exception as ex:
    print("skip", ex)

def on_frame(scn, depsgraph=None):
    apply_state((scn.frame_current - 1) / FPS)

apply_state(0.0)
bpy.app.handlers.frame_change_pre.append(on_frame)
B.render(OUT, MODE, NF)
