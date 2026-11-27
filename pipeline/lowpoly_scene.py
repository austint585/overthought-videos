"""Blender side of the low-poly cutscene (Nov 26): the patio, table, props and golden-hour light from
cutscene_scene.py, with the low-poly cast (lowpoly_cast.py) seated in place of the MakeHuman people, driven by the
same timing.json, rendered at 270 x 480 for ps2look (render_ps2.py does the rest).

blender -b --factory-startup -P lowpoly_scene.py -- timing.json out_dir FRAMES   (FRAMES: 'all' or 1-based list)

timing.json adds "poses" to what render_cutscene.timing_json writes: {name: [[t, pose], ...]}, one pose per line
(the sixth low-poly rule), worked out by render_ps2.pose_events.
"""
import json, math, os, runpy, sys
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index("--") + 1:]
timing, out, frames_arg = argv[:3]
out = os.path.abspath(out)
# the set, props, lights and helpers come from the MakeHuman kit unchanged ("anchors" builds nothing by itself)
sys.argv = [sys.argv[0], "--", timing, out, "anchors"]
ns = runpy.run_path(os.path.join(HERE, "cutscene_scene.py"), run_name="cutscene_scene")
import lowpoly_cast as LC
import ps2look

T, NF, FPS, B = ns["T"], ns["NF"], ns["FPS"], ns["B"]
scene = bpy.context.scene
D = math.radians


def build():
    cast = T["cast"]
    xs = [c["x"] for c in cast]
    ns["patio"]()
    {"friendsgiving": ns["friendsgiving_props"], "blackfriday": ns["blackfriday_props"]}.get(
        T.get("props"), ns["props_on_table"])(xs)
    people = {}
    for c in cast:
        p = LC.build(c["name"], x=c["x"], y=c.get("y", 0.15), rot_z=D(c.get("rot", 0)))
        p.base = "sit_crossed" if c.get("arms") == "crossed" else "sit_table"
        p.pose(p.base)
        people[c["name"]] = p
    sun, to_sun = ns["golden_hour"]()
    ns["leaf_shadows"](to_sun, (0, 1.5, 1.4))
    cam = B.camera(lens=35, fstop=5.6)
    cam.data.dof.use_dof = False                              # console cutscenes have no depth of field
    B.area("fill", (1.6, -1.6, 1.4), (0, 0.15, 1.15), 1.4, 28, color=ns["hexc"]("dfe6ff"))
    B.area("rim", (-1.2, 1.6, 2.2), (0, 0.15, 1.3), 0.8, 60, color=ns["hexc"]("ffc890"))
    B.render_settings(FPS, samples=16, motion_blur=0, look="AgX - Medium High Contrast")
    scene.view_settings.view_transform = "Standard"           # painted colours stay as painted
    scene.view_settings.look = "None"
    ps2look.apply(cam)
    return people, cam


def _at(events, t):
    """Index of the last [t0, ...] event with t0 <= t, or -1."""
    i = -1
    for k, e in enumerate(events):
        if e[0] <= t:
            i = k
        else:
            break
    return i


def plan(people):
    """Per frame and person: pose blend, head turn, face. Heads and facing come from the seated base pose."""
    heads = {n: LC.head_world(p) for n, p in people.items()}
    fwds = {n: LC.forward(p) for n, p in people.items()}
    smooth = ns["_smooth"]
    noise = ns["_noise"]
    P = {}
    for ci, (n, p) in enumerate(people.items()):
        d = T["chars"][n]
        fwd = fwds[n]
        yaw_t, pitch_t = [], []
        for f in range(NF):
            t = f / FPS
            looks = d.get("look", [])
            i = _at(looks, t)
            target = looks[i][1] if i >= 0 else "cam"
            if target in heads and target != n:
                v = heads[target] - heads[n]
            elif target == "down":
                v = fwd * 0.5 + Vector((0, 0, -0.6))
            else:
                v = fwd.copy()
            a = math.atan2(fwd.x * v.y - fwd.y * v.x, fwd.x * v.x + fwd.y * v.y)
            a = max(-0.8, min(0.8, a))
            el = math.atan2(v.z, Vector((v.x, v.y)).length) if (target in heads or target == "down") else 0.0
            yaw_t.append(a * 0.8)
            pitch_t.append(-el * 0.75)
        yaw, pitch = smooth(yaw_t, 0.1, FPS), smooth(pitch_t, 0.12, FPS)
        mouth, shape = d.get("mouth", [0] * NF), d.get("shape", ["aa"] * NF)
        exprs, blinks = d.get("expr", []), d.get("blinks", [])
        poses = T.get("poses", {}).get(n, [[0.0, p.base]])
        rows = []
        for f in range(NF):
            t = f / FPS
            i = _at(poses, t)
            cur = poses[i][1] if i >= 0 else p.base
            prev = poses[i - 1][1] if i >= 1 else p.base
            w = LC.ease_back((t - poses[i][0]) / 0.22) if i >= 0 else 1.0
            ei = _at(exprs, t)
            expr = exprs[ei][1] if ei >= 0 else "neutral"
            laughing = expr == "laugh" and t - exprs[ei][0] < 1.8
            m = mouth[f] if f < len(mouth) else 0.0
            sh = shape[f] if f < len(shape) else "aa"
            if laughing:
                mo = "grin" if int(t * 11) % 2 == 0 else "open"
            elif m >= 0.15:
                mo = "half" if (m < 0.45 and sh == "aa") else LC.TALK[sh]
            else:
                mo = None
            blink = any(0 <= t - b0 < 0.12 for b0 in blinks)
            nod = 0.07 * m * math.sin(t * 2 * math.pi * 2.1 + ci)
            yw = yaw[f] + 0.05 * noise(ci * 7 + 1, t, 0.9)
            pt = pitch[f] + nod + 0.03 * noise(ci * 7 + 2, t, 0.7) + (-0.14 if laughing else 0)
            rl = 0.035 * noise(ci * 7 + 3, t, 0.5) + (0.06 * math.sin(t * 2 * math.pi * 5.5) if laughing else 0)
            breath = 0.015 * math.sin(t * 2 * math.pi / 4.2 + ci) + (0.03 * math.sin(t * 2 * math.pi * 5.5)
                                                                     if laughing else 0)
            rows.append({"pose": cur, "prev": prev, "w": w,
                         "add": {"neck": (pt * 0.4, rl * 0.4, yw * 0.4), "head": (pt * 0.6, rl * 0.6, yw * 0.6),
                                 "spine": (breath, 0, 0)},
                         "face": (expr, mo, "closed" if blink else None)})
        P[n] = rows
    return P, heads, fwds


def plan_camera(people, heads, fwds):
    """Per frame (location, aim target, lens): the MakeHuman kit's framing (cutscene_scene.plan_camera), with heads and
    facing from the low-poly cast."""
    cast = T["cast"]
    xs = [c["x"] for c in cast]
    shots = T["shots"]
    res = []
    for f in range(NF):
        t = f / FPS
        si = max([i for i, s in enumerate(shots) if s["t0"] <= t] or [0])
        sh = shots[si]
        t1 = shots[si + 1]["t0"] if si + 1 < len(shots) else T["duration"]
        u = (t - sh["t0"]) / max(0.5, t1 - sh["t0"])
        kind, who = sh["cam"], sh.get("who", [])
        push = 1 - 0.035 * u
        if kind == "wide" and max(xs) - min(xs) > 1.2:
            tgt = Vector((sum(xs) / len(xs), 0.15, 1.0))
            off, lens = Vector((0, -1.72, 0.72)) * push, 16
        elif kind == "wide":
            tgt = Vector((sum(xs) / len(xs), 0.15, 1.08))
            off, lens = Vector((0, -1.85, 0.12)) * push, 22
        elif kind in ("two", "group"):
            hs = [heads[w] for w in who]
            tgt = sum(hs, Vector()) / len(hs) + Vector((0, 0, -0.12))
            spread = max(h.x for h in hs) - min(h.x for h in hs)
            k = max(1.0, (spread + 1.1) / 1.3)
            off, lens = Vector((0.05, -1.45 * k, 0.05 + 0.08 * (k - 1))) * push, 32
        else:
            tgt = heads[who[0]] + Vector((0, 0, -0.16 if kind == "single" else -0.1))
            dist = 1.55 if kind == "single" else 1.3
            off = (fwds[who[0]] * dist + Vector((sh.get("side", 0.16), 0, 0.06))) * push
            lens = 50 if kind == "single" else 58
        res.append((tgt + off, tgt, lens))
    return res


def main():
    people, cam = build()
    P, heads, fwds = plan(people)
    C = plan_camera(people, heads, fwds)

    def apply(f):
        for n, p in people.items():
            r = P[n][f]
            LC.set_pose(p, r["pose"], r["w"], other=r["prev"], add=r["add"])
            p.face(*r["face"])
        loc, tgt, lens = C[f]
        cam.location = loc
        cam.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = lens

    # every face square exists, and every tag anchor is known, before any render starts (making or swapping images
    # while a render runs crashed Blender, Nov 26)
    from bpy_extras.object_utils import world_to_camera_view
    anchors = {n: [] for n in people}
    for f in range(NF):
        apply(f)
        bpy.context.view_layer.update()
        for n, p in people.items():
            v = world_to_camera_view(scene, cam, LC.head_world(p) + Vector((0, 0, 0.19)))
            anchors[n].append([round(v.x * 1080, 1), round((1 - v.y) * 1920, 1)] if v.z > 0 else None)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "anchors.json"), "w") as fh:
        json.dump(anchors, fh)
    want = range(1, NF + 1) if frames_arg == "all" else [int(x) for x in frames_arg.split(",")]
    for F in want:
        path = os.path.join(out, f"f_{F:05d}.png")
        if os.path.exists(path):
            continue
        apply(F - 1)
        scene.frame_set(F)
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)


main()
