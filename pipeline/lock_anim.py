"""Shared geometry and motion for the lock cutaway (render_lock.py + lock_scene.py).

Units: plug radius = 1.0 (about 6.35 mm on a real lock). Key axis is +x, pins point +z,
the cut plane is y = 0 and the camera looks at it from -y. Pure Python so Blender can import it.
"""
import math

SHEAR = 1.0                              # top of the plug = shear line
PIN_X = [0.8, 1.5, 2.2, 2.9, 3.6]        # pin stacks, front of the lock first
FULL_TIP = 4.4                           # key tip x when fully inserted
UNCUT = 0.45                             # top of the uncut blade
GOOD = [0.30, -0.15, 0.15, 0.45, 0.0]    # blade height under each pin with the right key
BAD = list(GOOD)
WRONG_PIN = 2
BAD[WRONG_PIN] = 0.30                    # one cut a step too shallow: that pin rides too high
REST = -0.30                             # key pin tip height with no key in
DRIVER_LEN = 0.85
SPRING_TOP = 3.0
KEY_OUT = -6.5                           # tip x with the key just out of frame
TURN = -math.radians(75)


def key_pin_len(i):
    return SHEAR - GOOD[i]


def clamp01(u):
    return max(0.0, min(1.0, u))


def ease(u):
    u = clamp01(u)
    return u * u * (3 - 2 * u)


def ease_out(u):
    return 1 - (1 - clamp01(u)) ** 3


def ease_in(u):
    return clamp01(u) ** 2


def ramp(t, t0, dur, f=ease):
    return f((t - t0) / dur)


def blade_top(u, cuts):
    """Height of the key's top edge at distance u back from the tip."""
    if u < 0:
        return -9.0
    v = UNCUT
    for i, b in enumerate(cuts):
        ui = FULL_TIP - PIN_X[i]
        v = min(v, b + max(0.0, abs(u - ui) - 0.1))   # flat-bottomed cut with 45 degree flanks
    return min(v, -0.45 + 2.2 * u)                   # sloped nose


def bounce(dt, amp):
    if dt < 0 or dt > 0.7:
        return 0.0
    return amp * abs(math.sin(math.pi * dt / 0.16)) * math.exp(-dt * 8)


def pulse(dt, width=0.18):
    return math.exp(-((dt - width) / width) ** 2)


def jiggle(dt):
    if dt < 0 or dt > 0.8:
        return 0.0
    return 0.05 * math.sin(2 * math.pi * 7 * dt) * math.exp(-dt * 5)


def swap_start(E):
    return max(E["turns"] + 0.8, E["wrong"] - 1.6)


def key_state(t, E):
    """-> (which key or None, tip x, plug rotation in radians)."""
    theta = 0.0
    if t < E["cut"]:
        return "good", -3.0 + 2.75 * ramp(t, 0.15, E["cut"] - 0.35), 0.0
    if t < E["slide"]:
        theta = jiggle(t - E["cant"])
        return None, KEY_OUT - 20, theta
    sw = swap_start(E)
    if t < sw + 0.25:
        ins = max(1.6, min(2.6, E["shear"] - 0.35 - E["slide"]))
        tip = KEY_OUT + (FULL_TIP - KEY_OUT) * ramp(t, E["slide"], ins)
        theta = TURN * ramp(t, E["turns"], 0.7, ease_out) * (1 - ramp(t, sw, 0.25))
        return "good", tip, theta
    if t < sw + 0.65:
        return "good", FULL_TIP + (KEY_OUT - FULL_TIP) * ramp(t, sw + 0.25, 0.4, ease_in), 0.0
    tip = KEY_OUT + (FULL_TIP - KEY_OUT) * ramp(t, sw + 0.65, 1.0)
    return "bad", tip, jiggle(t - E["locked"])


def pin_tips(t, E):
    """Key pin tip heights (unrotated) for each stack."""
    which, tip, _ = key_state(t, E)
    cuts = GOOD if which == "good" else BAD
    tips = []
    for i, x in enumerate(PIN_X):
        z = REST
        if which is not None:
            z = max(z, blade_top(tip - x, cuts))
        if z <= REST + 1e-6:
            z += bounce(t - (E["five"] + 0.13 * i), 0.18) + bounce(t - E["down"], 0.22)
        tips.append(z)
    return tips


def front_offset(t, E):
    """Translation of the sawn-off front half: slides away at 'half', comes back for the end."""
    if t < E["half"]:
        return (0.0, 0.0, 0.0)
    if t < E["comment"]:
        u = ramp(t, E["half"], 0.85, ease_in)
        return (8.0 * u, -9.0 * u, 0.0) if u < 1 else (0.0, -400.0, 0.0)
    u = 1 - ramp(t, E["comment"], 1.1)
    return (8.0 * u, -9.0 * u, 0.0)


def glows(t, E):
    """Emission strengths: per-stack orange, drivers red, key pins red, shear line, plug, tailpiece."""
    stack = [0.0] * 5
    for i in range(5):
        stack[i] = 3.0 * pulse(t - (E["five"] + 0.13 * i))
    part = {"spring": 3.0 * pulse(t - E["spring"], 0.3),
            "top": 3.0 * pulse(t - E["top"], 0.3),
            "bottom": 3.0 * pulse(t - E["bottom"], 0.3)}
    blocked = ramp(t, E["down"] + 0.3, 0.4) * (1 - ramp(t, E["slide"] - 0.2, 0.4))
    driver_red = [2.0 * blocked] * 5
    pin_red = [0.0] * 5
    wrong = ramp(t, E["one"], 0.3) * (1 - ramp(t, E["comment"] - 0.3, 0.4))
    pin_red[WRONG_PIN] = 2.5 * wrong
    line_orange = 4.0 * ramp(t, E["shear"], 0.3) * (1 - ramp(t, E["turns"] + 0.9, 0.5))
    line_red = 4.0 * max(blocked, wrong)
    return {"stack": stack, "part": part, "driver_red": driver_red, "pin_red": pin_red,
            "line_orange": line_orange, "line_red": line_red,
            "plug": 1.2 * pulse(t - E["plug"], 0.35), "tail": 2.5 * pulse(t - E["bolt"], 0.35)}
