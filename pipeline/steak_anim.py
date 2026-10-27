"""Shared timing for the back-row steak guy episode, so the Blender picture and the sound effects agree.
Pure Python (no Blender); E is the event dict from render_steak.events()."""
import math

ROW_DEPTH = 2.0                      # each tier is 2 blocks deep and 1 block higher than the one in front
N_ROWS = 7
SEAT_X = [-8.45 + 1.3 * k for k in range(14)]
GUY_SEAT = 12                        # back row, next to the right aisle
WALK_SPEED = 2.6                     # blocks per second (walking in late, no hurry)
DOOR = (10.0, 17.3)
PATH = [DOOR, (10.0, 13.35), (SEAT_X[GUY_SEAT], 13.35)]
STEP = 0.36

def floor_z(y):
    if y < 0:
        return 0.0
    if y < ROW_DEPTH * N_ROWS:
        return float(int(y // ROW_DEPTH) + 1)
    return float(N_ROWS + 1)

def seat_y(r):
    return ROW_DEPTH * r + 1.35

def _segs():
    return [math.dist(a, b) for a, b in zip(PATH, PATH[1:])]

WALK_LEN = sum(_segs())

def walk_point(dist):
    for (a, b), L in zip(zip(PATH, PATH[1:]), _segs()):
        if dist <= L:
            u = dist / L
            return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u), ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        dist -= L
    a, b = PATH[-2], PATH[-1]
    L = math.dist(a, b)
    return b, ((b[0] - a[0]) / L, (b[1] - a[1]) / L)

def enter_time(E):
    return E["B"] + 0.15

def arrive_time(E):
    return enter_time(E) + WALK_LEN / WALK_SPEED

def seated(t, E):
    return t < E["B"] or t >= arrive_time(E) + 0.3

def bites(E, duration):
    """Times the steak reaches his mouth. None while he walks in or pours ranch."""
    out = []
    t = 0.7
    while t < duration - 0.3:
        if seated(t - 0.5, E) and seated(t, E) and not (E["ranch"] - 0.4 <= t < E["ranch"] + 1.6):
            out.append(t)
        t += 1.55
    return out

def turn_start(E):
    return E["buffering"] - 0.75

def aura_awards(E):
    """(time, points) for the counter; the total is the payoff."""
    return [(E["tomahawk"], 500), (E["C_end"], 1000), (E["handle"], 1500), (E["ranch"], 2000),
            (E["attendance"], 2500), (E["chewing"], 10000)]
