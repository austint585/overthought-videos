"""Physics for 'Last Flag Standing': balls bounce inside a rotating ring with a gap.
A ball that escapes through the gap is out. Last ball inside wins.

simulate(seed, ...) returns per-frame states plus an event log for sound."""
import math, random
import numpy as np
import pymunk

W, H = 1080, 1920
CX, CY = 540, 1010
R = 400               # ring radius (inner surface)
BALL_R = 31
FPS = 60
SUBSTEPS = 4
GRAVITY = 1150

COUNTRIES = [
    ("us", "USA"), ("ca", "Canada"), ("mx", "Mexico"), ("br", "Brazil"), ("ar", "Argentina"),
    ("co", "Colombia"), ("cl", "Chile"), ("pe", "Peru"), ("jm", "Jamaica"), ("do", "Dominican Rep."),
    ("gb", "UK"), ("ie", "Ireland"), ("fr", "France"), ("de", "Germany"), ("es", "Spain"),
    ("pt", "Portugal"), ("it", "Italy"), ("nl", "Netherlands"), ("be", "Belgium"), ("ch", "Switzerland"),
    ("pl", "Poland"), ("se", "Sweden"), ("no", "Norway"), ("dk", "Denmark"), ("gr", "Greece"),
    ("tr", "Turkey"), ("cn", "China"), ("jp", "Japan"), ("kr", "South Korea"), ("in", "India"),
    ("pk", "Pakistan"), ("bd", "Bangladesh"), ("ph", "Philippines"), ("id", "Indonesia"), ("vn", "Vietnam"),
    ("th", "Thailand"), ("my", "Malaysia"), ("sa", "Saudi Arabia"), ("ae", "UAE"), ("eg", "Egypt"),
    ("ng", "Nigeria"), ("za", "South Africa"), ("ma", "Morocco"), ("ke", "Kenya"), ("gh", "Ghana"),
    ("et", "Ethiopia"), ("au", "Australia"), ("nz", "New Zealand"),
]

CAT_BALL, CAT_RING, CAT_GONE = 0b001, 0b010, 0b100


def build_ring(space, body, gap_center, gap_width, segs=160):
    """Approximate the ring with short segments, leaving out an arc for the gap.
    Angles are in the ring body's local frame."""
    shapes = []
    rr = R + 6  # segment centerline sits just outside the visual inner radius
    for i in range(segs):
        a0 = 2 * math.pi * i / segs
        a1 = 2 * math.pi * (i + 1) / segs
        mid = (a0 + a1) / 2
        d = (mid - gap_center + math.pi) % (2 * math.pi) - math.pi
        if abs(d) < gap_width / 2:
            continue
        p0 = (rr * math.cos(a0), rr * math.sin(a0))
        p1 = (rr * math.cos(a1), rr * math.sin(a1))
        s = pymunk.Segment(body, p0, p1, 6)
        s.elasticity = 1.0
        s.friction = 0.0
        s.collision_type = 2
        s.filter = pymunk.ShapeFilter(categories=CAT_RING, mask=CAT_BALL)
        shapes.append(s)
    space.add(*shapes)
    return shapes


def simulate(seed=1, n=48, gap0=0.62, gap_growth=0.55, omega=1.05, max_seconds=90,
             spin_up=0.0, tail_boost=True):
    rnd = random.Random(seed)
    space = pymunk.Space()
    space.gravity = (0, GRAVITY)
    space.iterations = 20

    ring = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
    ring.position = (CX, CY)
    ring.angular_velocity = omega
    space.add(ring)
    gap_local = -math.pi / 2  # gap starts at the top
    gap_w = gap0
    ring_shapes = build_ring(space, ring, gap_local, gap_w)

    countries = COUNTRIES[:n]
    order = list(range(n))
    rnd.shuffle(order)
    balls = []
    # pack balls on a jittered grid in the middle of the ring
    placed = []
    for idx in order:
        for _ in range(500):
            a = rnd.uniform(0, 2 * math.pi)
            rad = math.sqrt(rnd.uniform(0, 1)) * (R - BALL_R - 30)
            x, y = CX + rad * math.cos(a), CY + rad * math.sin(a)
            if all((x - px) ** 2 + (y - py) ** 2 > (2 * BALL_R + 4) ** 2 for px, py in placed):
                break
        placed.append((x, y))
        b = pymunk.Body(1.0, pymunk.moment_for_circle(1.0, 0, BALL_R))
        b.position = (x, y)
        sp = rnd.uniform(380, 720)
        th = rnd.uniform(0, 2 * math.pi)
        b.velocity = (sp * math.cos(th), sp * math.sin(th))
        s = pymunk.Circle(b, BALL_R)
        s.elasticity = 1.0
        s.friction = 0.0
        s.collision_type = 1
        s.filter = pymunk.ShapeFilter(categories=CAT_BALL, mask=CAT_BALL | CAT_RING)
        space.add(b, s)
        balls.append({"i": idx, "code": countries[idx][0], "name": countries[idx][1],
                      "body": b, "shape": s, "alive": True, "out_frame": None})

    events = []  # (time_seconds, kind, strength, extra)
    frame_ref = {"f": 0}

    def on_wall(arbiter, space_, data):
        if arbiter.is_first_contact:
            imp = arbiter.total_impulse.length
            if imp > 150:
                events.append((frame_ref["f"] / FPS, "wall", min(imp / 1600.0, 1.0), None))

    def on_ball(arbiter, space_, data):
        if arbiter.is_first_contact:
            imp = arbiter.total_impulse.length
            if imp > 250:
                events.append((frame_ref["f"] / FPS, "ball", min(imp / 1600.0, 1.0), None))

    space.on_collision(1, 2, post_solve=on_wall)
    space.on_collision(1, 1, post_solve=on_ball)

    frames = []
    alive = n
    dt = 1.0 / FPS / SUBSTEPS
    winner_frame = None
    f = 0
    while f < max_seconds * FPS:
        frame_ref["f"] = f
        for _ in range(SUBSTEPS):
            space.step(dt)
        # keep things lively: clamp speeds into a band
        for bl in balls:
            if not bl["alive"]:
                continue
            v = bl["body"].velocity
            sp = v.length
            if sp > 1500:
                bl["body"].velocity = v * (1500 / sp)
            elif sp < 260 and f > 30:
                th = rnd.uniform(0, 2 * math.pi)
                bl["body"].velocity = v + (220 * math.cos(th), -260 - 120 * rnd.random())
        # eliminations
        for bl in balls:
            if not bl["alive"]:
                continue
            p = bl["body"].position
            d = math.hypot(p.x - CX, p.y - CY)
            if d > R + BALL_R + 10:
                bl["alive"] = False
                bl["out_frame"] = f
                bl["shape"].filter = pymunk.ShapeFilter(categories=CAT_GONE, mask=0)
                alive -= 1
                events.append((f / FPS, "out", 1.0, bl["name"]))
                # widen the gap as the field thins so the end doesn't drag
                frac = 1 - alive / n
                new_w = gap0 + gap_growth * frac ** 1.6
                if alive <= 6 and tail_boost:
                    new_w += 0.10 * (7 - alive)
                if abs(new_w - gap_w) > 0.01:
                    space.remove(*ring_shapes)
                    gap_w = new_w
                    ring_shapes = build_ring(space, ring, gap_local, gap_w)
        # record state
        st = {
            "ring_angle": ring.angle,
            "gap_local": gap_local,
            "gap_w": gap_w,
            "balls": [(bl["i"], bl["body"].position.x, bl["body"].position.y, bl["body"].angle, bl["alive"]) for bl in balls],
            "alive": alive,
        }
        frames.append(st)
        f += 1
        if alive == 1 and winner_frame is None:
            winner_frame = f
            events.append((f / FPS, "win", 1.0, [bl["name"] for bl in balls if bl["alive"]][0]))
            break
    out_frames = {bl["i"]: bl["out_frame"] for bl in balls}
    winner = [bl for bl in balls if bl["alive"]]
    return {
        "frames": frames, "events": events, "out_frames": out_frames,
        "winner": (winner[0]["i"], winner[0]["code"], winner[0]["name"]) if len(winner) == 1 else None,
        "countries": countries, "n": n, "end_frame": f,
    }


if __name__ == "__main__":
    import sys
    rows = []
    for seed in range(1, 25):
        r = simulate(seed=seed)
        outs = sorted(t for t, k, *_ in r["events"] if k == "out")
        dur = r["end_frame"] / FPS
        last_gap = outs[-1] - outs[-2] if len(outs) >= 2 else 0
        half = sum(1 for t in outs if t < dur / 2)
        print(f"seed {seed:2d}  dur {dur:5.1f}s  winner {r['winner'][2] if r['winner'] else None:14s}  outs_in_first_half {half:2d}  final_duel {last_gap:4.1f}s")
