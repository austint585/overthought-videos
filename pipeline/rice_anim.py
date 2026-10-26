"""Shared numbers and motion for the rice-on-a-chessboard what-if (render_rice.py + rice_scene.py).

Units are meters. The board sits on a garden table; the rice pile is a heightfield whose volume always
equals the grains placed so far, so it sits on the board, spills off the table, then buries the town.
"""
import math
import numpy as np

GRAIN_KG = 25e-6                    # one grain of milled rice, 20 to 30 mg
BULK_KG_M3 = 800.0                  # loose rice
GRAIN_M3 = GRAIN_KG / BULK_KG_M3
TAN = math.tan(math.radians(32))    # angle of repose of a rice pile
SQ = 0.05                           # one chess square
BOARD = 8 * SQ + 0.05               # board with its border
BOARD_TOP = 0.77
TABLE_TOP = 0.75
TABLE_HALF = (0.8, 0.45)
DISCRETE = 9                        # squares 1..9 are drawn grain by grain (511 grains)


def square_xy(k):
    r, c = divmod(int(k) - 1, 8)
    return (-3.5 * SQ + c * SQ, -3.5 * SQ + r * SQ)


def n_keys(E):
    return [(0.0, 1.0), (E["double"] + 0.25, 1.0), (E["s10"], 10.0), (E["s20"], 20.0), (E["s30"], 30.0),
            (E["s40"], 40.0), (E["s50"], 50.0), (E["s64"], 64.0)]


def square_at(t, E):
    """Squares filled so far (float). Resets to 1 at the loop point so the last frame matches the first."""
    if t >= E["loop"]:
        return 1.0
    keys = n_keys(E)
    if t >= keys[-1][0]:
        return 64.0
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t0 <= t < t1:
            return a + (b - a) * (t - t0) / (t1 - t0)
    return 1.0


def grains_on(k):
    return 2 ** (int(k) - 1)


def total_grains(n):
    return 2.0 ** n - 1.0


def heap_volume(n):
    return max(0.0, total_grains(n) - (2 ** DISCRETE - 1)) * GRAIN_M3


def surface(x, y):
    s = np.zeros_like(x)
    s[(np.abs(x) <= TABLE_HALF[0]) & (np.abs(y) <= TABLE_HALF[1])] = TABLE_TOP
    s[(np.abs(x) <= BOARD / 2) & (np.abs(y) <= BOARD / 2)] = BOARD_TOP
    return s


K_RINGS, M_SEG = 220, 240
_U = (np.arange(1, K_RINGS + 1) / K_RINGS) ** 2      # ring radii as a fraction of the base radius, dense near the top
_TH = np.arange(M_SEG) * 2 * math.pi / M_SEG
_COS, _SIN = np.cos(_TH)[None, :], np.sin(_TH)[None, :]
UNDER_TABLE = TABLE_TOP - 0.045                     # rice under the table stops just below the tabletop
APEX_EDGE = TABLE_TOP + TAN * TABLE_HALF[1] + 0.003  # just past the apex where the table pile reaches the table's near edge


def _grid(R):
    rho = (R * _U)[:, None] * np.ones((1, M_SEG))
    x, y = rho * _COS, rho * _SIN
    r = rho[:, 0]
    edges = np.concatenate([[0.0], (r[:-1] + r[1:]) / 2, [r[-1]]])
    area = ((edges[1:] ** 2 - edges[:-1] ** 2) * math.pi / M_SEG)[:, None]
    return rho, x, y, area


def _table_pile(apex):
    """Cone on the board and tabletop; rice reaches a point only if the pile is unbroken from the top out to it."""
    rho, x, y, area = _grid(apex / TAN)
    s = surface(x, y)
    z = apex - TAN * rho
    thick = np.where(np.logical_and.accumulate((z > s) & (s > 0), axis=0), z - s, 0.0)
    return x, y, np.where(thick > 0, s + thick, s - 0.004), thick > 0, float((thick * area).sum())


def _ground_pile(top, under_cap):
    """Cone standing on the ground; under the table it is capped just below the tabletop while the table still shows."""
    rho, x, y, area = _grid(max(top, 1e-6) / TAN)
    z = np.clip(top - TAN * rho, 0.0, None)
    if under_cap:
        under = (np.abs(x) <= TABLE_HALF[0]) & (np.abs(y) <= TABLE_HALF[1])
        z = np.where(under, np.minimum(z, UNDER_TABLE), z)
    return x, y, np.where(z > 0, z, -0.004), z > 0, float((z * area).sum())


def _solve(f, target, lo, hi):
    while f(hi) < target:
        hi = hi * 2.0 + 1.0
    for _ in range(48):
        mid = (lo + hi) / 2
        if f(mid) < target:
            lo = mid
        else:
            hi = mid
    return hi


def heap_fields(volume):
    """-> {apex, table: (x, y, z, has) or None, ground: (x, y, z, has) or None}, rings x segments arrays.

    Three stages, continuous in volume: a cone on the board and tabletop; then, with that pile held at the
    table edge, the rice pouring off builds a mound on the ground (under the table too) whose top rises to
    meet it; then one cone on the ground that keeps growing and buries the table, the town and the hills."""
    if volume <= 0:
        return None
    table_full = _table_pile(APEX_EDGE)[4]
    mound_full = _ground_pile(APEX_EDGE, True)[4]
    if volume <= table_full:
        apex = _solve(lambda a: _table_pile(a)[4], volume, BOARD_TOP, APEX_EDGE)
        return {"apex": apex, "table": _table_pile(apex)[:4], "ground": None}
    if volume <= table_full + mound_full:
        top = _solve(lambda h: _ground_pile(h, True)[4], volume - table_full, 0.0, APEX_EDGE)
        return {"apex": APEX_EDGE, "table": _table_pile(APEX_EDGE)[:4], "ground": _ground_pile(top, True)[:4]}
    apex = _solve(lambda a: _ground_pile(a, False)[4], volume, APEX_EDGE, APEX_EDGE + 1.0)
    return {"apex": apex, "table": None, "ground": _ground_pile(apex, False)[:4]}


def fmt_mass(kg):
    if kg < 0.001:
        return f"{kg * 1e6:.0f} mg"
    if kg < 0.01:
        return f"{kg * 1000:.1f} g"
    if kg < 1:
        return f"{kg * 1000:.0f} g"
    if kg < 1000:
        return f"{kg:.0f} kg"
    t = kg / 1000
    if t < 1e6:
        return f"{t:,.0f} t" if t >= 100 else f"{t:.1f} t"
    if t < 1e9:
        return f"{t / 1e6:.0f} million t"
    return f"{t / 1e9:.0f} billion t"
