"""Shared timing for the Stacy spawner episode, so the Blender picture and the sound effects agree.
Pure Python (no Blender); E is the event dict from render_spawner.events()."""
import math

SPAWNER_XY = (0.5, 0.5)
WALK_SPEED = 5.6                                   # blocks per second (sprinting)
PATH = [(-20.5, 12.2), (-19.4, 9.4), (-3.5, 0.5)]  # bed, front of the house, west edge of the plaza
STEP = 0.26                                        # seconds per footstep while sprinting

def _segs():
    return [math.dist(a, b) for a, b in zip(PATH, PATH[1:])]

WALK_LEN = sum(_segs())

def walk_point(dist):
    for (a, b), L in zip(zip(PATH, PATH[1:]), _segs()):
        if dist <= L:
            u = dist / L
            return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u), ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        dist -= L
    (a, b) = PATH[-2], PATH[-1]
    L = math.dist(a, b)
    return b, ((b[0] - a[0]) / L, (b[1] - a[1]) / L)

def cross_time(E):
    """When Chad comes within 16 blocks of the plaza spawner."""
    for k in range(4000):
        p, _ = walk_point(k * 0.01)
        if math.dist(p, SPAWNER_XY) <= 16.0:
            return E["D"] + k * 0.01 / WALK_SPEED
    return E["D"] + 2.0

def arrive_time(E):
    return E["D"] + WALK_LEN / WALK_SPEED

def plaza_spawns(E):
    return [E["four"] + 0.05 + 0.12 * k for k in range(4)]

def hits(E):
    return [E["home"] + 0.1, E["home"] + 0.55, E["silk"] - 0.25]

def break_time(E):
    return E["silk"] + 0.35
