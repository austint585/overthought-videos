"""Directed version of the Schrodinger's Situationship collapse (G to H), for the 'directed vs described' test (Nov 10).
Same set, figures, narration and animation as quantum_scene.py; only the direction changes (ops/direction.md).
quantum_scene.py calls install(globals()) when OVERTHOUGHT_DIRECT=1 is set and uses the apply_state it returns.

The shot sheet
  Look: night-blue field #0A1022, warm lamp amber #FFB46B on the couple, neutral crate wood falling into shadow,
        and one accent kept back for the big moment: the flashlight's cold white #E8F0FF.
  Big moment: "collapses" (E['collapses']). The flashlight clicks on, the warm lamp dies, the dating ghosts vanish,
        the camera cuts in on the same axis with one jolt. The only cold light, the only fast move.
  1 couple    G-0.3   two-shot, locked off, symmetrical; eye: the heart between them (0.5, 0.50); light: the lamp
                      above them only, rim from behind; depth: the glowing vial in the near corner, couple, crate
                      back wall, black. 35 mm at eye level. Intensity 2.
  2 friend    friend  low over-the-shoulder from outside the crate: the friend walks in as a silhouette (rim from
                      the moon), the warm box glows beyond him; eye: the lit box (0.58, 0.52). 28 mm, low, still. 3.
  3 target    friend+1.9  the friend's view: the couple, tight, 50 mm, he raises the torch (anticipation, release,
                      settle) but it stays off; the breath: the superposition pulse stops 0.45 s before the hit.
                      On the hit: punch-in 1.3x, one jolt, the torch on, the lamp off. Holds on the result. 3 then 5.
"""
import math
import bpy
from mathutils import Vector
import direct as D

def install(g):
    E, B, QA = g["E"], g["B"], g["QA"]
    T_HIT = E["collapses"]
    FPS = g["FPS"]
    scene = g["scene"]

    # ---------------------------------------------------------------- the look: night, haze, practicals
    world = scene.world
    nt = world.node_tree
    nt.nodes["Background"].inputs["Color"].default_value = (0.004, 0.006, 0.016, 1)
    vol = nt.nodes.new("ShaderNodeVolumeScatter")
    vol.inputs["Density"].default_value = 0.018
    vol.inputs["Anisotropy"].default_value = 0.35
    vol.inputs["Color"].default_value = (0.75, 0.82, 1.0, 1)
    nt.links.new(vol.outputs[0], nt.nodes["World Output"].inputs["Volume"])
    ee = scene.eevee
    for attr, val in (("volumetric_tile_size", "8"), ("volumetric_samples", 48), ("volumetric_end", 40.0),
                      ("use_volumetric_shadows", True), ("volumetric_shadow_samples", 8)):
        try:
            setattr(ee, attr, val)
        except Exception as ex:
            print("volumetric setting skipped:", attr, ex)

    obs = bpy.data.objects
    key, fill, rim = obs["key"], obs["fill"], obs["rim"]
    lamp, flash, torch, vial = obs["lamp"], obs["flash"], obs["torch_light"], obs["vial"]
    lamp.data.energy = 260.0
    lamp.data.color = (1.0, 0.70, 0.42)
    lamp.data.shadow_soft_size = 0.35
    torch.data.energy = 2600.0
    torch.data.color = (0.91, 0.94, 1.0)
    torch.data.spot_size = math.radians(30)
    torch.data.spot_blend = 0.25
    torch.data.shadow_soft_size = 0.05
    moon = B.sun("moon", 75, 22, 0.9, (0.55, 0.65, 1.0), angle_deg=2.0)     # from behind the crate, rims the friend
    flash.data.color = (0.9, 0.94, 1.0)
    rim.data.color = (1.0, 0.55, 0.30)
    rig = D.Rig(g["cam"], {"key": key, "fill": fill, "rim": rim, "lamp": lamp, "torch": torch, "moon": moon,
                           "flash": flash, "vial": vial})

    COUCH_C = g["COUCH_C"]
    HEART = Vector((0, g["SEAT_Y"] - 0.1, 2.75))
    t_friend = E["friend"]
    t_target = E["friend"] + 1.9
    SHOTS = D.ShotList([
        D.Shot("couple", E["G"] - 0.3, eye=HEART, lens=35, dist=7.6, yaw=0, pitch=-3, screen=(0.5, 0.50),
               light={"key": 0.0, "fill": 0.05, "rim": 0.55, "lamp": 1.0, "torch": 0.0, "moon": 0.6, "flash": 0.0},
               note="lamp only; the green vial is the near layer"),
        D.Shot("friend", t_friend, eye=Vector((-0.6, -1.2, 2.1)), lens=28, dist=10.5, yaw=-31, pitch=4,
               screen=(0.58, 0.52),
               light={"key": 0.0, "fill": 0.04, "rim": 0.8, "lamp": 1.0, "torch": 0.0, "moon": 1.0, "flash": 0.0},
               note="silhouette on purpose: the friend is the dark foreground, the box is the light"),
        D.Shot("target", t_target, eye=Vector((0, g["SEAT_Y"], 2.45)), lens=50, dist=5.6, yaw=-14, pitch=-1,
               screen=(0.5, 0.52), hit=T_HIT, move=("punch", 1.3), kick=0.035,
               light={"key": 0.0, "fill": 0.05, "rim": 0.6, "lamp": 1.0, "torch": 0.0, "moon": 0.5, "flash": 0.0},
               note="the big moment: punch-in and the only cold light"),
    ], end=g["DUR"])
    SHOTS.check()
    import os
    SHOTS.dump(os.path.join(g["OUT"], "shots.json"), big=T_HIT)

    BREATH = 0.45
    couple_state, cat_state = g["couple_state"], g["cat_state"]
    FRIEND, place, pose, hide = g["FRIEND"], g["place"], g["pose"], g["hide"]

    def couple_clock(t):
        """The superposition pulse stops for the breath before the hit."""
        a = T_HIT - BREATH
        return a if a <= t < T_HIT else t

    def friend_state(t):
        tc = D.on_twos(t, FPS)                       # the figure steps on twos; camera and light stay smooth
        t0, t1 = QA.friend_enter(E), QA.friend_arrive(E)
        if tc < t0 or tc >= E["H"] + 1.5:
            hide(FRIEND)
            return
        (ax, ay), (bx, by) = QA.FRIEND_PATH
        L = math.hypot(bx - ax, by - ay)
        d = min(L, (tc - t0) * QA.FRIEND_SPEED)
        x, y = ax + (bx - ax) * d / L, ay + (by - ay) * d / L
        walking = d < L
        face = ((bx - ax) / L, (by - ay) / L) if walking else (0.25, 1)
        place(FRIEND, x, y, face=face)
        pose(FRIEND, walk=1.0 if walking else 0.0, phase=(tc - t0) * 10, arms=None)
        if not walking:
            # raise the torch: dips first, snaps up, overshoots, settles; it lands well before the hit
            up = D.ars(tc, t1 + 0.55, wind=0.3, back=0.15, release=0.12, settle=0.4, over=0.1, snap="out")
            FRIEND["armL"].rotation_euler = (-0.2, 0, 0)
            FRIEND["armR"].rotation_euler = (-1.45 * up, 0, 0)
        FRIEND["head"].rotation_euler = (0.05, 0, 0)

    def apply_state(t):
        couple_state(couple_clock(t))
        cat_state(t)
        friend_state(t)
        SHOTS.apply(rig, t)
        if t >= T_HIT:                                # the hit: cold light in, warm light out
            u = t - T_HIT
            torch.data.energy = rig.base["torch"] * (1.0 + 1.5 * D.flash(t, T_HIT, decay=0.3))
            flash.data.energy = 9000.0 * D.flash(t, T_HIT, decay=0.25)
            lamp.data.energy = rig.base["lamp"] * max(0.06, 1.0 - u / 0.06)
            rim.data.energy = rig.base["rim"] * 0.25
        g["cam"].data.clip_start = 0.05

    return apply_state
