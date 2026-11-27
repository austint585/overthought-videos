"""Low-poly sets for the chad bit (Nov 27), so every episode isn't the same patio table (Austin: "change up your
scenery"). Each set is built the low-poly way: simple boxes, flat shading, every texture painted here in numpy at 64 px
or less with nearest filtering, signs lettered with a 5 x 7 pixel font. The cast stands in them.

SETS[name]() builds the set and its lights; STAND maps the seated pose names pose_events writes to standing ones.
"""
import math
import numpy as np
import bpy
import bmesh
import lowpoly_cast as LC

# ------------------------------------------------------------------ a 5 x 7 pixel font for signs
FONT = {
    "A": ".###.#...##...#######...##...##...#", "B": "####.#...##...#####.#...##...#####.",
    "C": ".###.#...##....#....#....#...#.###.", "D": "####.#...##...##...##...##...#####.",
    "E": "######....#....####.#....#....#####", "F": "######....#....####.#....#....#....",
    "I": "#####..#....#....#....#....#..#####", "K": "#...##..#.#.#..##...#.#..#..#.#...#",
    "L": "#....#....#....#....#....#....#####", "O": ".###.#...##...##...##...##...#.###.",
    "R": "####.#...##...#####.#.#..#..#.#...#", "S": ".#####....#.....###.....#....#####.",
    "T": "#####..#....#....#....#....#....#..", "U": "#...##...##...##...##...##...#.###.",
    "Y": "#...##...#.#.#...#....#....#....#..", "0": ".###.#...##..###.#.###..##...#.###.",
    "6": ".###.#....#....####.#...##...#.###.", "%": "##..###..#...#...#...#...#..###..##",
    " ": "." * 35,
}


def text_width(s, scale=1):
    return (len(s) * 6 - 1) * scale


def paint_text(a, s, x, y, col, scale=1):
    for k, ch in enumerate(s):
        g = FONT[ch]
        for r in range(7):
            for c in range(5):
                if g[r * 5 + c] == "#":
                    LC.rect(a, x + (k * 6 + c) * scale, y + r * scale, x + (k * 6 + c + 1) * scale - 1,
                            y + (r + 1) * scale - 1, col)


def sign(text, bg, fg, border=None, pad=3):
    w, h = text_width(text) + 2 * pad, 7 + 2 * pad
    a = LC.canvas(w, h, bg)
    if border:
        a[0, :] = a[-1, :] = border
        a[:, 0] = a[:, -1] = border
    paint_text(a, text, pad, pad, fg)
    return a


# ------------------------------------------------------------------ pictures on the demo TVs (32 x 18)
def screen_sunset():
    a = np.zeros((18, 32, 3), np.float32)
    for y in range(10):
        a[y, :] = np.array((255, 120, 70)) + (np.array((120, 60, 140)) - np.array((255, 120, 70))) * (1 - y / 9)
    yy, xx = np.mgrid[0:18, 0:32]
    a[((xx - 21) ** 2 + (yy - 9) ** 2) < 10] = (255, 224, 120)                    # the sun on the horizon
    a[10:] = (24, 60, 120)
    for y in range(11, 18, 2):
        LC.hline(a, 14 + (y % 4), 27 - (y % 3), y, (250, 170, 90))                # its glitter on the sea
    return a


def screen_field():
    a = LC.canvas(32, 18, (52, 150, 64))
    a[:5] = (110, 170, 240)
    a[5] = (30, 34, 40)                                                           # the stands
    for y in range(6, 18, 3):
        a[y, :] = (62, 166, 74)
    LC.hline(a, 0, 31, 12, (240, 240, 240))
    a[6:, 16] = (240, 240, 240)
    LC.rect(a, 9, 9, 10, 10, (250, 250, 250))                                     # the ball
    return a


def screen_mountains():
    a = LC.canvas(32, 18, (90, 160, 236))
    for x in range(32):
        top = int(6 + 5 * abs(math.sin(x * 0.35)) + 2 * abs(math.sin(x * 0.9)))
        a[top:, x] = (92, 96, 112)
        a[top:top + 2, x] = (244, 246, 250)                                       # snow caps
        a[14:, x] = (60, 130, 66)
    return a


# ------------------------------------------------------------------ helpers
def quad(name, corners, mat, emit_shadow=True):
    """A single face with the whole image on it: corners bottom-left, bottom-right, top-right, top-left."""
    bm = bmesh.new()
    vs = [bm.verts.new(c) for c in corners]
    f = bm.faces.new(vs)
    uv = bm.loops.layers.uv.verify()
    for l, c in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        l[uv].uv = c
    ob = LC.to_object(name, bm, [mat])
    ob.visible_shadow = emit_shadow
    return ob


def boxob(name, x0, x1, y0, y1, z0, z1, mat, scale=3.0):
    bm = LC.box(x0, x1, y0, y1, z0, z1)
    LC.uv_box(bm, scale)
    return LC.to_object(name, bm, [mat])


def tile_floor():
    a = LC.canvas(32, 32, (168, 170, 168))
    LC.speckle(a, [(160, 162, 160), (176, 178, 176)], 0.25, 21)
    a[0, :] = a[:, 0] = (132, 134, 134)
    return a


def slatwall():
    a = LC.canvas(32, 32, (64, 66, 74))
    for y in range(0, 32, 4):
        a[y, :] = (44, 46, 52)
    return a


def tv_box_art():
    """Side of a boxed TV: dark box, a blue band, a picture of a TV, a white text stripe (no brand)."""
    a = LC.canvas(32, 32, (28, 34, 52))
    a[22:27, :] = (40, 110, 200)
    LC.rect(a, 5, 5, 26, 18, (12, 12, 14))
    a[6:18, 6:26] = screen_mountains()[3:15, 6:26]
    LC.rect(a, 5, 29, 19, 30, (230, 230, 230))
    return a


def pallet_wood():
    a = LC.canvas(16, 16, (150, 112, 70))
    for y in (0, 5, 10, 15):
        a[y, :] = (96, 70, 44)
    return a


# ------------------------------------------------------------------ the TV aisle on Black Friday morning
def tv_aisle():
    """A big box store's TV wall at opening time: rows of demo TVs on a slatwall, a BLACK FRIDAY banner, pallet
    stacks of boxed TVs with a 60% OFF and a DOORBUSTER sign, grey tile, cold fluorescent light, and the screens'
    blue glow behind the group. The cast stands across the middle of it facing the camera."""
    M = LC.material
    floor = M("st_floor", LC.image("st_floor", tile_floor()))
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=8)
    LC.uv_box(bm, 1.6)
    LC.to_object("st_floor", bm, [floor])
    wall = M("st_wall", LC.image("st_wall", LC.speckle(LC.canvas(16, 16, (186, 190, 198)), [(176, 180, 188)], 0.3,
                                                       22)))
    slat = M("st_slat", LC.image("st_slat", slatwall()))
    boxob("st_backwall", -8, 8, 2.6, 2.8, 0, 4.2, wall, 1.0)
    boxob("st_tvwall", -3.4, 3.4, 2.4, 2.6, 0, 3.2, slat, 2.0)
    for side in (-1, 1):                                                          # side walls of the bay
        boxob("st_side", side * 3.4 - 0.15, side * 3.4 + 0.15, -3.0, 2.6, 0, 4.2, wall, 1.0)
    ceil = M("st_ceil", LC.image("st_ceil", LC.canvas(8, 8, (206, 206, 210))))
    boxob("st_ceiling", -8, 8, -6, 3, 4.2, 4.3, ceil, 1.0)
    lamp = M("st_lamp", LC.image("st_lamp", LC.canvas(4, 4, (255, 255, 250))), emit=4.0)
    for y in (-2.0, 0.0, 2.0):
        for x in (-1.6, 1.6):
            boxob("st_tube", x - 0.9, x + 0.9, y - 0.12, y + 0.12, 4.12, 4.2, lamp, 1.0).visible_shadow = False

    # the demo TVs: black bezels, a picture on each, the same three loops repeating like a real store
    bezel = M("st_bezel", LC.image("st_bezel", LC.canvas(4, 4, (16, 16, 18))))
    pics = [M(f"st_screen{i}", LC.image(f"st_screen{i}", f() * 0.85), emit=1.0)
            for i, f in enumerate((screen_sunset, screen_field, screen_mountains))]   # emit below
    k = 0
    for row, zc in enumerate((1.05, 1.74, 2.43)):
        for col in range(-3, 3):
            xc = (col + 0.5) * 1.06
            w, h = 0.48, 0.28
            boxob("st_tv", xc - w - 0.03, xc + w + 0.03, 2.30, 2.40, zc - h - 0.03, zc + h + 0.03, bezel, 1.0)
            quad("st_screen", [(xc - w, 2.295, zc - h), (xc + w, 2.295, zc - h), (xc + w, 2.295, zc + h),
                               (xc - w, 2.295, zc + h)], pics[(k + row) % 3], emit_shadow=False)
            k += 1
    # the banner over the wall
    ban = sign("BLACK FRIDAY", (22, 22, 26), (250, 250, 250), border=(206, 32, 40), pad=3)
    bmat = M("st_banner", LC.image("st_banner", ban), emit=0.25)
    bw, bx = 1.9, -0.31                                   # whole in the opening group shot and in the wides
    bh = bw * ban.shape[0] / ban.shape[1]
    quad("st_banner", [(bx - bw / 2, 2.25, 3.62), (bx + bw / 2, 2.25, 3.62), (bx + bw / 2, 2.25, 3.62 + bh),
                       (bx - bw / 2, 2.25, 3.62 + bh)], bmat)
    # pallet stacks of boxed TVs either side of the group, each with its sign on a pole
    wood = M("st_pallet", LC.image("st_pallet", pallet_wood()))
    art = M("st_tvbox", LC.image("st_tvbox", tv_box_art()))
    pole = M("st_pole", LC.image("st_pole", LC.canvas(4, 4, (150, 150, 156))))
    for sx, y0, txt, bg, fg in ((-1.2, 0.95, "60% OFF", (250, 208, 40), (200, 20, 30)),
                                (1.22, 1.05, "DOORBUSTER", (200, 24, 32), (255, 255, 255))):
        boxob("st_pallet", sx - 0.55, sx + 0.55, y0 - 0.45, y0 + 0.45, 0, 0.14, wood, 2.0)
        for i in range(5):                                                        # boxes standing on edge, nudged
            bx = sx - 0.42 + i * 0.21
            ob = boxob("st_box", -0.09, 0.09, -0.4, 0.4, 0.14, 0.14 + 0.62 - 0.04 * (i % 2), art, 1.25)
            ob.location = (bx, y0, 0)
            ob.rotation_euler = (0, 0, math.radians(90 + (i % 3 - 1) * 3))
        boxob("st_pole", sx - 0.015, sx + 0.015, y0 - 0.015, y0 + 0.015, 0.14, 1.95, pole, 1.0)
        a = sign(txt, bg, fg, border=fg, pad=2)
        sw = 0.62 if len(txt) < 8 else 0.86
        sh = sw * a.shape[0] / a.shape[1]
        smat = M(f"st_sign_{txt}", LC.image(f"st_sign_{txt}", a), emit=0.15)
        quad("st_sign", [(sx - sw / 2, y0 - 0.02, 1.9), (sx + sw / 2, y0 - 0.02, 1.9), (sx + sw / 2, y0 - 0.02, 1.9 + sh),
                         (sx - sw / 2, y0 - 0.02, 1.9 + sh)], smat)

    # light: a cool store, flat overhead fluorescents, a key for faces, the screens' blue glow behind them
    sc = bpy.context.scene
    w = bpy.data.worlds.new("st_world")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.62, 0.66, 0.72, 1)
    bg.inputs[1].default_value = 0.38

    def area(name, loc, target, size, power, color):
        ld = bpy.data.lights.new(name, "AREA")
        ld.size, ld.energy, ld.color = size, power, color
        ob = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(ob)
        ob.location = loc
        from mathutils import Vector
        ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        return ob
    area("st_overhead", (0, -0.5, 4.0), (0, -0.3, 0), 5.0, 420, (0.92, 0.96, 1.0))
    area("st_key", (-1.6, -2.4, 2.3), (0, 0.15, 1.5), 1.6, 55, (1.0, 0.95, 0.88))
    area("st_glow", (0, 2.1, 1.7), (0, 0.15, 1.5), 3.0, 120, (0.55, 0.7, 1.0))


# ------------------------------------------------------------------ a living room at night, tree going up (Nov 27)
def wood_floor():
    a = LC.canvas(32, 32, (128, 86, 52))
    r = np.random.default_rng(31)
    for y0 in range(0, 32, 8):
        a[y0:y0 + 8] = np.array((128, 86, 52), np.float32) * r.uniform(0.86, 1.1)
        a[y0, :] = (92, 60, 36)
        a[y0:y0 + 8, int(r.integers(0, 32))] = (100, 66, 40)                    # plank ends
    LC.speckle(a, [(116, 78, 46), (140, 96, 60)], 0.12, 32)
    return a


def wallpaper():
    a = LC.canvas(16, 16, (186, 160, 120))
    for x in (0, 8):
        a[:, x] = (170, 144, 106)
    for y in range(2, 16, 6):
        LC.px(a, 4, y, (204, 180, 140))
        LC.px(a, 12, y + 3, (204, 180, 140))
    return a


def window_night():
    a = np.zeros((32, 20, 3), np.float32)
    for y in range(32):
        a[y, :] = np.array((18, 26, 58)) + np.array((24, 30, 40)) * (y / 31)
    a[26:, :] = (210, 220, 236)                                                    # snow on the ground outside
    for x in (2, 9, 14):                                                          # a neighbour's lit windows
        LC.rect(a, x, 21, x + 2, 23, (250, 200, 110))
    r = np.random.default_rng(33)
    for _ in range(26):
        LC.px(a, int(r.integers(0, 20)), int(r.integers(0, 26)), (236, 240, 250))   # falling snow
    return a


def needles():
    a = LC.canvas(16, 16, (30, 82, 46))
    LC.speckle(a, [(22, 64, 36), (42, 104, 58), (18, 54, 30)], 0.5, 34)
    return a


def present(col, ribbon):
    a = LC.canvas(16, 16, col)
    a[:, 7:9] = ribbon
    a[7:9, :] = ribbon
    return a


def cone(r0, z0, r1, z1, n=8, x=0.0, y=0.0, tilt=0.0):
    rings = [[(x + r * math.cos(2 * math.pi * k / n + tilt), y + r * math.sin(2 * math.pi * k / n + tilt), z)
              for k in range(n)] for r, z in ((r0, z0), (r1, z1))]
    return LC.loft(rings)


def living_room():
    """The chad's living room the weekend after Thanksgiving, at night: a lit tree going up between the two of them,
    presents and a box of decorations, a snowy window, a couch and a warm floor lamp. Cozy and dark, so the tree and
    the faces carry the light (the TV aisle was cold and bright)."""
    M = LC.material
    floor = M("lr_floor", LC.image("lr_floor", wood_floor()))
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6)
    LC.uv_box(bm, 1.2)
    LC.to_object("lr_floor", bm, [floor])
    wall = M("lr_wall", LC.image("lr_wall", wallpaper()))
    boxob("lr_back", -4, 4, 2.0, 2.15, 0, 2.8, wall, 2.4)
    for side in (-1, 1):
        boxob("lr_side", side * 2.7 - 0.08, side * 2.7 + 0.08, -4, 2.15, 0, 2.8, wall, 2.4)
    trim = M("lr_trim", LC.image("lr_trim", LC.canvas(4, 4, (236, 230, 218))))
    boxob("lr_base", -4, 4, 1.96, 2.0, 0, 0.12, trim, 1.0)
    dark = M("lr_ceil", LC.image("lr_ceil", LC.canvas(4, 4, (60, 52, 46))))
    boxob("lr_ceiling", -4, 4, -4, 2.2, 2.8, 2.9, dark, 1.0)
    # the window, back left, with its frame and curtains
    win = M("lr_window", LC.image("lr_window", window_night()), emit=0.9)
    wx, wz = -1.35, 0.9
    quad("lr_window", [(wx - 0.5, 1.99, wz), (wx + 0.5, 1.99, wz), (wx + 0.5, 1.99, wz + 1.5),
                       (wx - 0.5, 1.99, wz + 1.5)], win, emit_shadow=False)
    for x0, x1, z0, z1 in ((wx - 0.56, wx + 0.56, wz - 0.06, wz), (wx - 0.56, wx + 0.56, wz + 1.5, wz + 1.56),
                           (wx - 0.56, wx - 0.5, wz, wz + 1.5), (wx + 0.5, wx + 0.56, wz, wz + 1.5),
                           (wx - 0.02, wx + 0.02, wz, wz + 1.5), (wx - 0.5, wx + 0.5, wz + 0.73, wz + 0.77)):
        boxob("lr_frame", x0, x1, 1.94, 1.99, z0, z1, trim, 1.0)
    curtain = M("lr_curtain", LC.image("lr_curtain", LC.speckle(LC.canvas(8, 8, (120, 34, 40)), [(100, 26, 32)],
                                                                 0.3, 35)))
    for cx in (wx - 0.72, wx + 0.72):
        boxob("lr_curtain", cx - 0.16, cx + 0.16, 1.86, 1.94, 0.3, 2.62, curtain, 2.0)
    # the tree between them: four tiers of eight-sided cones, a trunk, a star, bulbs and baubles
    tree_x, tree_y = 0.0, 0.95
    nmat = M("lr_needles", LC.image("lr_needles", needles()))
    trunk = M("lr_trunk", LC.image("lr_trunk", LC.canvas(4, 4, (86, 56, 34))))
    boxob("lr_trunk", tree_x - 0.06, tree_x + 0.06, tree_y - 0.06, tree_y + 0.06, 0, 0.22, trunk, 1.0)
    tiers = [(0.66, 0.18, 0.12, 0.9), (0.54, 0.62, 0.1, 1.38), (0.41, 1.04, 0.07, 1.78), (0.28, 1.42, 0.0, 2.1)]
    for k, (r0, z0, r1, z1) in enumerate(tiers):
        bm = cone(r0, z0, r1, z1, 8, tree_x, tree_y, tilt=0.39 * k)
        LC.uv_box(bm, 3.0)
        LC.to_object("lr_tier", bm, [nmat])
    star = M("lr_star", LC.image("lr_star", LC.canvas(4, 4, (255, 222, 110))), emit=3.0)
    for rz in (0, 45):
        ob = boxob("lr_star", -0.07, 0.07, -0.018, 0.018, -0.07, 0.07, star, 1.0)
        ob.location = (tree_x, tree_y - 0.02, 2.17)
        ob.rotation_euler = (0, math.radians(rz), 0)
        ob.visible_shadow = False
    bulb_cols = [(255, 214, 140), (255, 70, 60), (90, 220, 110), (90, 150, 255), (255, 200, 60)]
    bulbs = [M(f"lr_bulb{i}", LC.image(f"lr_bulb{i}", LC.canvas(2, 2, c)), emit=5.0) for i, c in enumerate(bulb_cols)]
    baub_cols = [(196, 30, 40), (214, 170, 60), (220, 220, 230)]
    baubs = [M(f"lr_baub{i}", LC.image(f"lr_baub{i}", LC.canvas(2, 2, c))) for i, c in enumerate(baub_cols)]
    rng = np.random.default_rng(36)
    for i in range(72):                                       # a spiral of bulbs up the tree, baubles between
        u = i / 72
        z = 0.3 + u * 1.65
        tier_r = max(0.08, 0.62 * (1 - (z - 0.18) / 2.0))
        ang = u * 2 * math.pi * 5.3 + rng.uniform(-0.2, 0.2)
        x, y = tree_x + tier_r * 0.92 * math.cos(ang), tree_y + tier_r * 0.92 * math.sin(ang)
        if i % 3 == 2:
            sz, mat = 0.04, baubs[i % len(baubs)]
        else:
            sz, mat = 0.03, bulbs[i % len(bulbs)]
        ob = boxob("lr_bulb", -sz, sz, -sz, sz, -sz, sz, mat, 1.0)
        ob.location = (x, y, z - 0.05)
        ob.visible_shadow = False
    # a rug, presents under the tree, a box of decorations by the chad
    rug = M("lr_rug", LC.image("lr_rug", LC.speckle(LC.canvas(8, 8, (130, 40, 44)), [(110, 30, 36), (150, 120, 70)],
                                                     0.3, 37)))
    bm = cone(0.95, 0.002, 0.95, 0.008, 8, tree_x, tree_y + 0.05)
    LC.uv_box(bm, 2.0)
    LC.to_object("lr_rug", bm, [rug])
    gifts = [((176, 30, 40), (236, 200, 90), -0.42, 0.62, 0.26, 0.2),
             ((40, 110, 60), (230, 230, 230), 0.38, 0.6, 0.22, 0.16),
             ((214, 172, 70), (176, 30, 40), 0.05, 0.42, 0.18, 0.14),
             ((60, 90, 170), (236, 236, 236), -0.22, 0.4, 0.16, 0.24)]
    for k, (c, rb, gx, gy, w, h) in enumerate(gifts):
        g = M(f"lr_gift{k}", LC.image(f"lr_gift{k}", present(c, rb)))
        ob = boxob("lr_gift", -w / 2, w / 2, -w / 2, w / 2, 0, h, g, 1.0 / w)
        ob.location = (tree_x + gx, tree_y + gy - 0.5, 0)
        ob.rotation_euler = (0, 0, math.radians(17 * k - 20))
    card = M("lr_card", LC.image("lr_card", LC.speckle(LC.canvas(8, 8, (168, 128, 82)), [(150, 112, 70)], 0.3, 38)))
    ob = boxob("lr_box", -0.24, 0.24, -0.18, 0.18, 0, 0.3, card, 2.0)
    ob.location = (1.05, 0.55, 0)
    ob.rotation_euler = (0, 0, math.radians(-12))
    # couch back right, floor lamp back left
    fab = M("lr_couch", LC.image("lr_couch", LC.speckle(LC.canvas(8, 8, (74, 84, 96)), [(64, 74, 86), (84, 94, 106)],
                                                         0.3, 39)))
    cx, cy = 1.75, 1.45
    for x0, x1, y0, y1, z0, z1 in ((-0.85, 0.85, -0.4, 0.35, 0.12, 0.45), (-0.85, 0.85, 0.2, 0.42, 0.12, 0.95),
                                   (-0.95, -0.8, -0.4, 0.42, 0.12, 0.68), (0.8, 0.95, -0.4, 0.42, 0.12, 0.68)):
        boxob("lr_couch", cx + x0, cx + x1, cy + y0, cy + y1, z0, z1, fab, 2.0)
    pole = M("lr_pole", LC.image("lr_pole", LC.canvas(4, 4, (40, 36, 34))))
    shade = M("lr_shade", LC.image("lr_shade", LC.canvas(4, 4, (255, 220, 160))), emit=2.2)
    lx, ly = -2.1, 1.55
    boxob("lr_lamp", lx - 0.015, lx + 0.015, ly - 0.015, ly + 0.015, 0, 1.55, pole, 1.0)
    bm = cone(0.2, 1.5, 0.13, 1.78, 8, lx, ly)
    LC.uv_box(bm, 1.0)
    LC.to_object("lr_shade", bm, [shade]).visible_shadow = False

    # light: a dark, warm room. The tree glows, the lamp warms the back, a soft key finds the faces, the window
    # gives a cold edge.
    from mathutils import Vector
    sc = bpy.context.scene
    wd = bpy.data.worlds.new("lr_world")
    sc.world = wd
    wd.use_nodes = True
    bg = wd.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.10, 0.11, 0.18, 1)
    bg.inputs[1].default_value = 0.35

    def light(kind, name, loc, power, color, size=0.5, target=None):
        ld = bpy.data.lights.new(name, kind)
        ld.energy, ld.color = power, color
        if kind == "AREA":
            ld.size = size
        else:
            ld.shadow_soft_size = size
        ob = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(ob)
        ob.location = loc
        if target:
            ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        return ob
    light("POINT", "lr_treeglow", (tree_x, tree_y - 0.1, 1.1), 90, (1.0, 0.78, 0.55), 0.4)
    light("POINT", "lr_lampglow", (lx, ly, 1.62), 70, (1.0, 0.72, 0.45), 0.2)
    light("AREA", "lr_key", (-0.9, -2.0, 2.0), 70, (1.0, 0.86, 0.72), 1.2, (0, 0.25, 1.45))
    light("AREA", "lr_moon", (wx, 1.7, 1.8), 40, (0.55, 0.65, 1.0), 1.0, (0, 0.25, 1.4))


SETS = {"tv_aisle": tv_aisle, "living_room": living_room}
STANDING = {"tv_aisle", "living_room"}                       # sets where the cast stands instead of sitting at the patio table

# the seated pose names render_ps2.pose_events writes, as standing poses
STAND = {"sit_table": "stand", "sit_crossed": "crossed", "sit_back": "stand_back", "sit_palms": "stand_palms",
         "sit_hand": "stand_hand", "sit_point": "point", "sit_phone": "stand_phone", "sit_laugh": "stand_laugh",
         "sit_lean": "stand_lean"}
