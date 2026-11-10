"""Direction for the Blender scenes: the method in ops/direction.md as code. A scene declares decisions (where the eye
goes, which light carries the shot, the lens, the one move, the hit) and this module turns them into a camera and light
levels on every frame. Runs inside Blender; import it from a *_scene.py next to bkit.

    import direct as D
    rig = D.Rig(cam, {"key": key_ob, "fill": fill_ob, "rim": rim_ob, "lamp": lamp_ob})
    SHOTS = D.ShotList([
        D.Shot("hook", 0.0, eye=(0, 0, 1.6), lens=28, dist=7, yaw=-25, pitch=-6, screen=(0.5, 0.52),
               light={"lamp": 1.0, "key": 0.15}, move=("push", 0.10)),
        D.Shot("hit", E["punch"] - 0.05, eye=(0, 0.2, 1.7), lens=50, dist=3.2, yaw=10, pitch=-4,
               hit=E["punch"], move=("punch", 1.35), light={"lamp": 1.0, "rim": 1.4}),
    ], end=DUR)
    SHOTS.check()                       # prints warnings for rhythm, eye trace and hits into the render log
    SHOTS.dump(os.path.join(OUT, "shots.json"))   # qa_direction.py reads this
    ...
    def apply_state(t):
        SHOTS.apply(rig, t)

Screen positions are fractions of the 9:16 frame from the left and from the TOP, so (0.5, 0.5) is dead center and
anything above y = 0.28 sits under the captions. The focal point is framed with lens shift, so verticals stay straight.

Timing helpers for anything that moves:
    ars(t, hit)      anticipation, release, settle: 0 before, a small move the other way, a fast move into the hit,
                     an overshoot that settles. Use it for every action that matters.
    hold(t, hit)     1 normally, 0 for the breath before a hit: multiply idle motion (breathing, drift, flicker) by it.
    flash(t, hit)    a light or glow envelope: two-frame rise, exponential decay.
    kick(t, hit)     one camera jolt on an impact, decays in a quarter second.
    on_twos(t, fps)  stepped time for figures (a stop-motion feel) while the camera and light stay smooth.
"""
import json, math
from mathutils import Vector

# ------------------------------------------------------------------ timing curves

def clamp01(u):
    return max(0.0, min(1.0, u))

def smooth(u):
    u = clamp01(u)
    return u * u * (3 - 2 * u)

def smoother(u):
    u = clamp01(u)
    return u * u * u * (u * (u * 6 - 15) + 10)

def ease_in(u, p=2.0):
    return clamp01(u) ** p

def ease_out(u, p=3.0):
    return 1 - (1 - clamp01(u)) ** p

def ars(t, hit, wind=0.25, back=0.12, release=0.08, settle=0.5, over=0.12, snap="in"):
    """Anticipation, release, settle for an action going 0 -> 1 that lands exactly at `hit` (seconds).
    wind: how long the wind-up takes; back: how far it goes the wrong way first (fraction of the move);
    release: the fast part, ending at the hit; over: overshoot past 1; settle: seconds to come to rest.
    snap='in' accelerates into the hit (an impact); snap='out' leaves fast and slows (a pop or a reveal)."""
    t1 = hit - release
    t0 = t1 - wind
    if t < t0:
        return 0.0
    if t < t1:
        return -back * smooth((t - t0) / wind) if wind > 0 else 0.0
    if t < hit:
        u = (t - t1) / release
        e = ease_in(u, 2.0) if snap == "in" else ease_out(u, 3.0)
        return -back + (1.0 + over + back) * e
    u = t - hit
    k = 4.6 / max(settle, 1e-3)                       # down to 1% by `settle`
    return 1.0 + over * math.exp(-k * u) * math.cos(2 * math.pi * 1.2 * u / max(settle, 1e-3))

def hold(t, hit, breath=0.25, ease=0.1):
    """The breath before the hit: 1 until hit - breath - ease, eases to 0, stays still until the hit, then 1."""
    a = hit - breath - ease
    if t < a or t >= hit:
        return 1.0
    return 1.0 - smooth((t - a) / ease) if t < hit - breath else 0.0

def flash(t, hit, rise=0.035, decay=0.35):
    if t < hit - rise:
        return 0.0
    if t < hit:
        return smooth((t - (hit - rise)) / rise)
    return math.exp(-(t - hit) * 4.6 / decay)

def kick(t, hit, amp=0.05, decay=0.25, freq=17.0):
    """A camera jolt on an impact: an offset vector (world units) that dies out in `decay` seconds."""
    if t < hit:
        return Vector((0, 0, 0))
    u = t - hit
    a = amp * math.exp(-u * 4.6 / decay)
    return Vector((a * math.sin(2 * math.pi * freq * u), 0.0, a * 0.6 * math.sin(2 * math.pi * freq * 1.3 * u + 1.1)))

def on_twos(t, fps, n=2):
    return math.floor(t * fps / n + 1e-6) * n / fps

# ------------------------------------------------------------------ camera and light

def orbit_pos(eye, dist, yaw, pitch):
    """Camera position for a look at `eye`. yaw 0 = camera on the -Y side looking +Y (our sets face -Y);
    positive yaw swings the camera toward +X. pitch is the look angle: negative looks down, so the camera sits higher."""
    y, p = math.radians(yaw), math.radians(pitch)
    off = Vector((math.sin(y) * math.cos(p), -math.cos(y) * math.cos(p), -math.sin(p)))
    return Vector(eye) + dist * off

def side_light_pos(eye, cam_loc, side=1, h_deg=50.0, v_deg=35.0, dist=5.0):
    """Where a key light goes for this camera: h_deg off the camera-to-subject line toward `side` (+1 camera right),
    v_deg above. 30-50 deg is a classic key; 90 is a hard side light; 120-160 is a rim from behind."""
    eye = Vector(eye)
    to_cam = Vector(cam_loc) - eye
    to_cam.z = 0
    if to_cam.length < 1e-6:
        to_cam = Vector((0, -1, 0))
    to_cam.normalize()
    a = math.radians(h_deg) * (-side)
    d = Vector((to_cam.x * math.cos(a) - to_cam.y * math.sin(a), to_cam.x * math.sin(a) + to_cam.y * math.cos(a), 0))
    v = math.radians(v_deg)
    return eye + dist * Vector((d.x * math.cos(v), d.y * math.cos(v), math.sin(v)))

def point_at(ob, loc, target):
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

class Rig:
    """The camera plus the named lights a scene can direct. Each light's energy when the Rig is made is its level 1.0."""
    def __init__(self, cam, lights=None):
        self.cam = cam
        self.lights = dict(lights or {})
        self.base = {k: ob.data.energy for k, ob in self.lights.items()}
        cam.data.sensor_fit = "VERTICAL"
        cam.data.sensor_height = 36.0     # a full-frame camera held upright: '50 mm' frames like a 50 mm, as in bkit.camera
        cam.data.dof.use_dof = True

class Shot:
    """One setup. t0 is when it cuts in (it runs until the next shot's t0). Every field is a decision:
    eye      the one point the viewer should look at (world coords)
    screen   where that point sits in the frame, (x from left, y from top), fractions
    lens     mm on the 9:16 frame: 24-28 wide (space, comedy, scale), 35 neutral, 50-85 faces and tension
    dist     metres from the eye; yaw/pitch as in orbit_pos
    move     ('still',) ('push', frac) ('pull', frac) ('orbit', deg) ('crane', deg of pitch) ('punch', lens factor)
             ('push_on_hit', frac): a push that waits, winds back a touch and lands on the hit (ars)
    hit      the shot's beat in seconds (punch, push_on_hit and kick use it)
    light    {rig light name: level}; lights not named keep level 1.0 unless dark=True (then 0)
    key      optional (side, h_deg, v_deg, dist): re-place the rig's 'key' light for this camera, as film crews do
    fstop    depth of field; default opens up as the camera gets closer
    kick     camera jolt amplitude on the hit (0 = locked off)
    roll     dutch angle in degrees (rarely: unease)"""
    def __init__(self, name, t0, eye, lens=35.0, dist=6.0, yaw=0.0, pitch=-6.0, screen=(0.5, 0.52), move=("still",),
                 hit=None, light=None, dark=False, key=None, fstop=None, kick=0.0, roll=0.0, note=""):
        self.name, self.t0, self.eye = name, float(t0), Vector(eye)
        self.lens, self.dist, self.yaw, self.pitch = lens, dist, yaw, pitch
        self.screen, self.move, self.hit = screen, move, hit
        self.light, self.dark, self.key = dict(light or {}), dark, key
        self.fstop, self.kick, self.roll, self.note = fstop, kick, roll, note
        self.t1 = None

    def frame(self, t):
        """(camera location, look target, lens) at time t."""
        d = (t - self.t0) / max(1e-3, self.t1 - self.t0)
        dist, yaw, pitch, lens = self.dist, self.yaw, self.pitch, self.lens
        kind = self.move[0]
        amt = self.move[1] if len(self.move) > 1 else 0.0
        if kind == "push":
            dist *= 1 - amt * smoother(d)
        elif kind == "pull":
            dist *= 1 + amt * smoother(d)
        elif kind == "orbit":
            yaw += amt * smoother(d)
        elif kind == "crane":
            pitch += amt * smoother(d)
        elif kind == "punch" and self.hit is not None and t >= self.hit:
            lens *= amt
        elif kind == "push_on_hit" and self.hit is not None:
            dist *= 1 - amt * ars(t, self.hit, wind=0.3, back=0.06, release=0.12, settle=0.6, over=0.08, snap="out")
        loc = orbit_pos(self.eye, dist, yaw, pitch)
        if self.kick and self.hit is not None:
            loc = loc + kick(t, self.hit, amp=self.kick)
        return loc, self.eye, lens

class ShotList:
    def __init__(self, shots, end):
        self.shots = sorted(shots, key=lambda s: s.t0)
        for a, b in zip(self.shots, self.shots[1:]):
            a.t1 = b.t0
        self.shots[-1].t1 = end
        self.end = end

    def at(self, t):
        cur = self.shots[0]
        for s in self.shots:
            if t >= s.t0:
                cur = s
        return cur

    def apply(self, rig, t):
        s = self.at(t)
        loc, tg, lens = s.frame(t)
        cam = rig.cam
        point_at(cam, loc, tg)
        if s.roll:
            cam.rotation_euler.rotate_axis("Z", math.radians(s.roll))
        cd = cam.data
        cd.lens = lens
        sx, sy = s.screen
        cd.shift_y = (sy - 0.5)                      # vertical fit: 1.0 = one frame height; subject lower = shift up
        cd.shift_x = (0.5 - sx) * 9 / 16
        cd.dof.focus_distance = (Vector(tg) - Vector(loc)).length
        cd.dof.aperture_fstop = s.fstop or (1.8 if s.dist < 4 else 2.8 if s.dist < 9 else 4.0)
        cd.clip_start, cd.clip_end = 0.05, 400
        for name, ob in rig.lights.items():
            lvl = s.light.get(name, 0.0 if s.dark else 1.0)
            ob.data.energy = rig.base[name] * lvl
        if s.key and "key" in rig.lights:
            side, h, v, dd = s.key
            point_at(rig.lights["key"], side_light_pos(s.eye, loc, side, h, v, dd), s.eye)
        return s

    def check(self):
        """Warnings for the render log: things a director would catch on the shot list."""
        out = []
        for a, b in zip(self.shots, self.shots[1:]):
            if b.t0 - a.t0 < 0.6:
                out.append(f"{a.name}: {b.t0 - a.t0:.2f} s is too short to read")
            if abs(a.screen[0] - b.screen[0]) > 0.25:
                out.append(f"{a.name} -> {b.name}: the eye jumps across the frame on the cut")
        lens_set = {round(s.lens) for s in self.shots}
        if len(self.shots) > 3 and len(lens_set) == 1:
            out.append("every shot uses the same lens: vary it with the shot's job")
        lengths = [s.t1 - s.t0 for s in self.shots]
        if len(lengths) > 3 and max(lengths) < 1.3 * min(lengths):
            out.append("every shot is about the same length: let the narration set a rhythm")
        moving = [s for s in self.shots if s.move[0] != "still"]
        if len(self.shots) > 3 and len(moving) == len(self.shots):
            out.append("every shot moves: hold some still (deadpan reads best on a locked-off camera)")
        for s in self.shots:
            if s.hit is not None and not (s.t0 <= s.hit < s.t1):
                out.append(f"{s.name}: its hit {s.hit:.2f} falls outside the shot")
            if not (0.28 <= s.screen[1] <= 0.75):
                out.append(f"{s.name}: the eye at y={s.screen[1]:.2f} sits under the captions or the app's buttons")
        for w in out:
            print("DIRECTION:", w)
        return out

    def dump(self, path, big=None):
        """shots.json for qa_direction.py. big = the time of the one big moment."""
        json.dump({"end": self.end, "big": big,
                   "shots": [{"name": s.name, "t0": s.t0, "t1": s.t1, "screen": list(s.screen), "hit": s.hit,
                              "lens": s.lens, "move": list(s.move), "note": s.note} for s in self.shots]},
                  open(path, "w"), indent=1)
