"""Shared timing for the Schrodinger's situationship episode, so the Blender picture and the sound effects agree.
Pure Python (no Blender); E is the event dict from render_quantum.events()."""
import math

FRIEND_PATH = [(-9.0, -7.5), (-2.6, -6.2)]     # walks in from the left to in front of the open box
FRIEND_SPEED = 3.2
STEP = 0.3

def smooth01(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)

def ramp(t, t0, t1):
    return smooth01((t - t0) / (t1 - t0))

def pulse(t, rate=0.9):
    """Superposition: two states trade opacity smoothly, never fully gone."""
    return 0.5 + 0.5 * math.sin(2 * math.pi * rate * t)

def cat_window(E):
    return E["B"] - 0.2, E["C"] - 0.1

def couple_alphas(t, E):
    """(dating, not_dating) opacity, 0..1."""
    c0, c1 = cat_window(E)
    if c0 <= t < c1:
        return 0.0, 0.0
    if t >= E["collapses"]:
        return 0.0, 1.0
    # the D sentence shows one state at a time on its word
    if E["dating_d"] - 0.1 <= t < E["not_d"] - 0.1:
        return 1.0, 0.08
    if E["not_d"] - 0.1 <= t < E["E"] - 0.2:
        return 0.08, 1.0
    p = pulse(t)
    return 0.28 + 0.5 * p, 0.78 - 0.5 * p

def cat_alphas(t, E):
    """(alive, dead) opacity; the cat returns alive on the last line."""
    c0, c1 = cat_window(E)
    if c0 <= t < c1:
        p = pulse(t, 1.1)
        return 0.25 + 0.6 * p, 0.85 - 0.6 * p
    if t >= E["right"] - 0.25:
        return 1.0, 0.0
    return 0.0, 0.0

def friend_enter(E):
    return E["G"] - 0.4

def friend_arrive(E):
    (ax, ay), (bx, by) = FRIEND_PATH
    return friend_enter(E) + math.hypot(bx - ax, by - ay) / FRIEND_SPEED

def flash_time(E):
    return E["collapses"]
