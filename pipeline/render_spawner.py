"""'How Stacy spawners work': dating slang run on real Minecraft spawner rules, explained deadpan, in a voxel diorama.

python render_spawner.py out.mp4 out.wav     full render (Blender frames are cached in out/spawner/frames; delete them to re-render)
python render_spawner.py preview 1.0,12.5    render and composite stills into preview/
python render_spawner.py times               narrate and print the event times
python render_spawner.py audio out.mp4 out.wav  rebuild only the soundtrack and swap it into an existing render

Spawner rules (Minecraft Java Edition, https://minecraft.wiki/w/Monster_Spawner): a player within 16 blocks switches it on;
up to 4 spawn per attempt in a 9x9 area; 10 to 39.95 s between attempts; it skips the spawn if 6 of its mob are already
nearby; it can't be picked up in Survival, even with Silk Touch (a pickaxe drops 15 to 43 XP and nothing else).
"""
import json, math, os, sys
import numpy as np
import skia
from common import *
import render_tap as tap
import kit3d as K

FPS = 60
TAIL = 1.4
SCRIPT = [
    ("A", "Stacy spawners are real, and most Chads farm them completely *wrong.*"),
    ("B", "Like every spawner, it only turns on when a player is within *16{sixteen} blocks.*"),
    ("C", "So watching her stories from your *room* does nothing."),
    ("D", "Once you're in range, it spawns up to *four* at a time, every *10{ten} to 40{forty} seconds.*"),
    ("E", "But if *six* are already standing around it, the spawn *fails.*"),
    ("F", "Which is why the club at *1{one} a.m.{A M}* is a dead spawner."),
    ("G", "The real ones run in *daylight.* Coffee shops. Libraries. The *farmers market.*"),
    ("H", "And no, you can't take one home. Not even with *Silk Touch.*"),
]
EXTRA_GAP = {1: 0.15, 4: 0.2, 6: 0.25, 7: 0.3}
OUT = os.path.join(ROOT, "out", "spawner")
FRAMES = os.path.join(OUT, "frames")

def events(sents, speech_end):
    w = lambda si, sub: tap.word_time(sents, si, sub)
    s = lambda si: sents[si]["t0"]
    end = lambda si: sents[si]["t0"] + sents[si]["dur"]
    return {"A": s(0), "B": s(1), "C": s(2), "D": s(3), "E": s(4), "F": s(5), "G": s(6), "H": s(7),
            "wrong": w(0, "wrong"), "sixteen": w(1, "16"), "room": w(2, "room"), "range": w(3, "range"),
            "four": w(3, "four"), "ten": w(3, "10"), "D_end": end(3), "six": w(4, "six"), "fails": w(4, "fails"),
            "club": w(5, "club"), "one": w(5, "1"), "dead": w(5, "dead"), "daylight": w(6, "daylight"),
            "coffee": w(6, "Coffee"), "libraries": w(6, "Libraries"), "farmers": w(6, "farmers"),
            "home": w(7, "home"), "silk": w(7, "Silk"), "speech_end": speech_end}

# ------------------------------------------------------------------ sound (recorded effects from the Sonniss GDC 2026 bundle, see sfx.py)

F = {
    "bass": "344 Audio - Bass Drops & Downers Vol. 1/DSGNBass_Bass Drop & Downer Fast 16_344 Audio_Bass Drops & Downers.wav",
    "fire": "Epic Stock Media - Synthesized Nature Loops and Sounds/FIREBurn_Loop Elements Fire Crackling Crunchy Flame Burn 03_ESM_SNLS.wav",
    "meadow": "Just Sound Effects - Highlands of Norway/AMBSwmp_Meadow Pipits calling many Insects humming Wind blowing through Grass_JSE_HoN_Stereo.wav",
    "crickets": "344 Audio - East Coast America Vol. 1/AMBSubn_Ambience, Forest Crickets, Birds, Connecticut 02_344 Audio_East Coast America.wav",
    "bar": "Sonic Bat - Bars & Restaurants Ambience/SBbra_Bar E 001.wav",
    "swoosh": "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Pull Swoosh Readout.wav",
    "woosh": "Cinematic Sound Design - Ultra Transitions & Impacts/Woosh Sweep Slide Infographics Basic.wav",
    "pingdown": "Cinematic Sound Design - System & UI Feedback Elements/Interface Sci-Fi Ping Down.wav",
    "steps": "TheWorkRoom - Flip Flops/FFG002.wav",
    "powerup": "Epic Stock Media - Anime Game/DSGNStngr_Power Up Bright Positive Successful Light Saturation Crash Shimmer 05_ESM_AG.wav",
    "pop": "Cinematic Sound Design - Interface & Infographics/Interface Pop High Short.wav",
    "bubbles": "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Bubbles Short.wav",
    "snap": "Cinematic Sound Design - Interface & Infographics/Interface Accept Glassy Snap.wav",
    "perc": "Cinematic Sound Design - Interface & Infographics/Interface Percussion Snap.wav",
    "bassdown": "Cinematic Sound Design - Cartoon & Animation Vol 2/Cartoon Transition Bass Down.wav",
    "deny": "Cinematic Sound Design - System & UI Feedback Elements/Interface Deny Low Fat Dark.wav",
    "birdflute": "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/TOONMisc_Bird Flutes 3_CB Sounddesign_APPlicable Sounds.wav",
    "kalimba": "CB_Sounddesign - Applicable Sounds - Organic UI and Building Games SFX/UIMisc_Kalimba 3 Up_CB Sounddesign_APPlicable Sounds.wav",
    "metal1": "Epic Stock Media - HD Game Materials/METLImpt_Metal Old File Impact Tap Against Tire Iron Metallic Hit 01_ESM_HDGM.wav",
    "metal2": "David Dumais Audio - Melee Weapons Sound Effects Pack 2/METLImpt_METAL SWING HIT Weapon Swing To Metallic Body Impact And Resonant Tail 01_DDUMAIS_MWP2.wav",
    "shatter": "Epic Stock Media - Tower Defense Game/ICEBrk_Skill Freeze Whoosh Break Impact Layered Movement Shatter 03_ESM_TDG.wav",
    "coins": "Cinematic Sound Design - UI Interaction Elements/Ting Coins.wav",
    "denymuted": "Cinematic Sound Design - UI Interaction Elements/Deny Muted.wav",
}

def smooth01(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)

def build_audio(sents, E, duration, path):
    import sfx
    import spawner_anim as SA
    n = int(duration * SR)
    tt = np.arange(n) / SR
    voice = K.voice_track(sents, duration)[:n]
    # beds: day meadow, night crickets and a muffled club, the spawner's fire up close; all duck under the voice
    day = np.array([1 - smooth01((t - E["E"] + 0.4) / 0.9) + smooth01((t - E["G"] + 0.4) / 0.9) for t in tt[::480]])
    day = np.interp(tt, tt[::480], day)
    t_cross, t_break = SA.cross_time(E), SA.break_time(E)
    def fire_level(t):
        on = 1.0 if t < E["sixteen"] + 0.25 or t >= t_cross else 0.0
        near = 1.0 if t < E["B"] + 0.6 or E["H"] - 0.4 <= t < t_break else 0.2
        return 0.0 if t >= t_break else on * near
    fire = np.interp(tt, tt[::480], np.array([fire_level(t) for t in tt[::480]]))
    fire = np.convolve(fire, np.ones(4800) / 4800, "same")
    beds = (sfx.bed(F["meadow"], duration, 0.035, hp=120) * day
            + sfx.bed(F["crickets"], duration, 0.022, hp=200) * (1 - day)
            + sfx.bed(F["bar"], duration, 0.035, start=30.0, lp=650) * (1 - day)
            + sfx.bed(F["fire"], duration, 0.06) * fire)
    thump = new_track(duration)
    t = E["E"] - 0.4
    while t < E["G"]:
        add(thump, t, kick(0.3), 1.0)
        t += 60 / 124
    beds += sfx.lowpass(thump[:n], 160) * 0.22 * (1 - day)
    env = np.sqrt(np.convolve(voice ** 2, np.ones(2400) / 2400, "same"))
    beds *= 1 - 0.45 * np.clip(env / 0.08, 0, 1)
    tr = new_track(duration)
    tr[:n] += voice + beds
    hit = lambda t0, key, gain, **kw: add(tr, t0, sfx.clip(F[key], **kw), gain)
    hit(0.0, "bass", 0.12, lp=3000)
    hit(E["B"] - 0.35, "swoosh", 0.3)
    hit(E["sixteen"], "woosh", 0.28)
    hit(E["sixteen"] + 0.3, "pingdown", 0.3)
    hit(E["C"] - 0.45, "swoosh", 0.18, rate=1.2)
    steps = sfx.onsets(F["steps"], 0.25, 10)
    t, k = E["D"] + 0.1, 0
    while t < SA.arrive_time(E):
        hit(t, "steps", 0.26, start=steps[k % len(steps)], dur=0.2, lp=2800, hp=90)
        t += SA.STEP
        k += 1
    hit(t_cross, "powerup", 0.38)
    for k, ts in enumerate(SA.plaza_spawns(E)):
        hit(ts, "pop", 0.34, rate=(1.0, 1.12, 0.94, 1.06)[k])
        hit(ts + 0.02, "bubbles", 0.12)
    hit(E["ten"], "snap", 0.22)
    hit(E["E"] - 0.45, "bassdown", 0.4)
    hit(E["fails"] - 0.05, "deny", 0.45)
    hit(E["fails"], "pop", 0.2, rate=0.8)
    hit(E["one"], "perc", 0.25)
    hit(E["G"] - 0.4, "birdflute", 0.33)
    hit(E["G"] - 0.35, "woosh", 0.22)
    for key, r in (("coffee", 1.0), ("libraries", 1.12), ("farmers", 1.26)):
        hit(E[key], "kalimba", 0.24, rate=r)
    hit(E["H"] - 0.45, "swoosh", 0.18, rate=1.1)
    for k, h in enumerate(SA.hits(E)):
        if k < 2:
            hit(h - 0.01, "metal1", 0.45, rate=(0.92, 1.0)[k])
        else:
            hit(h - 0.01, "metal2", 0.5)
    hit(t_break, "shatter", 0.45)
    for k in range(3):
        hit(t_break + 0.6 + 0.25 * k, "coins", 0.2, rate=1.0 + 0.1 * k)
    hit(E["silk"] + 0.6, "denymuted", 0.35)
    save_wav(tr, path, duration)

def remux(mp4, wav):
    import subprocess
    tmp = mp4 + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", tmp], check=True)
    os.replace(tmp, mp4)

# ------------------------------------------------------------------ overlay

def draw_hook(c, a):
    if a <= 0:
        return
    f = font("Bricolage-800", 92)
    y = 290
    for s, k in (("How Stacy", False), ("spawners work", True)):
        wd = f.measureText(s) + (40 if k else 0)
        x = W / 2 - wd / 2
        if k:
            c.drawRRect(tap.rrect(x, y - 76, x + wd, y + 24, 16), paint(ORANGE, a))
            c.drawString(s, x + 20, y, f, paint(tap.PANEL2, a))
        else:
            c.drawString(s, x, y, f, paint(INK, a))
        y += 108

def pill(c, text, cx, y, a, color=INK, bg=K.DARK_PILL, size=34):
    if a <= 0:
        return
    f = font("JetBrainsMono-700", size)
    w = f.measureText(text)
    c.drawRRect(tap.rrect(cx - w / 2 - 22, y - size - 10, cx + w / 2 + 22, y + 16, 14), paint(bg, a))
    c.drawString(text, cx - w / 2, y, f, paint(color, a))

def overlay(c, t, F, sents, cm, E, A, speech_end):
    K.top_shade(c)
    c.saveLayer(None, K.shadow_paint())
    draw_hook(c, K.fade(t, -1, E["B"] - 0.05, 0.2))
    tap.draw_captions(c, t, sents, cm)
    c.restore()
    lab = font("JetBrainsMono-700", 30)
    # (anchor, text, start, end, dx, dy, color)
    tags = [
        ("ring", "16 BLOCKS", E["sixteen"] + 0.3, E["C"] + 0.2, 0, -150, tap.GREEN),
        ("chad", "PLAYER: OUT OF RANGE", E["room"] - 0.2, E["D"] + 0.1, 120, -230, tap.RED),
        ("plaza", "SPAWN AREA 9 x 9", E["four"] - 0.1, E["E"] - 0.1, 140, -260, ORANGE),
        ("club_spawner", "6 NEARBY: SPAWN FAILED", E["fails"] - 0.1, E["F"] + 0.2, -120, -300, tap.RED),
        ("cafe", "COFFEE SHOP", E["coffee"] - 0.05, E["H"] - 0.1, 0, -170, ORANGE),
        ("library", "LIBRARY", E["libraries"] - 0.05, E["H"] - 0.1, 0, -170, ORANGE),
        ("market", "FARMERS MARKET", E["farmers"] - 0.05, E["H"] - 0.1, 0, -170, ORANGE),
        ("pickaxe", "SILK TOUCH", E["silk"] - 0.05, E["silk"] + 0.5, -140, -200, skia.Color(190, 140, 255)),
    ]
    for name, text, t0, t1, dx, dy, col in tags:
        a = K.fade(t, t0, t1, 0.2)
        p = K.anchor(A, name, F) if a > 0 else None
        if p:
            K.tag(c, text, p[0], p[1], p[0] + dx, p[1] + dy, a, col, lab)
    pill(c, "NEXT SPAWN IN 10-40 s", W / 2, 1440, K.fade(t, E["ten"] - 0.1, E["E"] - 0.15, 0.2), INK)
    pill(c, "1:00 AM", W / 2, 1440, K.fade(t, E["one"] - 0.1, E["G"] - 0.2, 0.2), skia.Color(200, 120, 255))
    pill(c, "DROPS: NOTHING", W / 2, 1440, K.fade(t, E["silk"] + 0.6, 99, 0.25), tap.RED)
    a = K.fade(t, E["B"], E["G"] - 0.1, 0.3)
    if a > 0:
        text_center(c, "Spawner rules: Minecraft, Java Edition", W / 2, 1535, font("JetBrainsMono-500", 26), paint(MUTED, 0.9 * a))

# ------------------------------------------------------------------ main

def setup():
    sents, speech_end = K.narrate(SCRIPT, OUT, EXTRA_GAP)
    duration = speech_end + TAIL
    return sents, speech_end, duration, events(sents, speech_end)

def main(out_mp4, out_wav, preview_times=None):
    sents, speech_end, duration, E = setup()
    n_frames = int(round(duration * FPS))
    print(f"duration {duration:.1f}s, {n_frames} frames", flush=True)
    frames = sorted({min(n_frames - 1, int(round(x * FPS))) for x in preview_times}) if preview_times else range(n_frames)
    K.run_blender("spawner_scene.py", OUT, FRAMES, ",".join(str(f + 1) for f in frames) if preview_times else "all",
                  E, duration, FPS)
    A = json.load(open(os.path.join(FRAMES, "anchors.json")))
    cm = [x for x in tap.build_chunk_map(sents) if x[0] > 0]
    if not preview_times:
        build_audio(sents, E, duration, out_wav)
    K.composite(FRAMES, frames, FPS, lambda c, t, F: overlay(c, t, F, sents, cm, E, A, speech_end),
                out_mp4, out_wav, "spawner" if preview_times else None)

if __name__ == "__main__":
    if sys.argv[1] == "times":
        sents, speech_end, duration, E = setup()
        print(json.dumps({k: round(v, 2) for k, v in E.items()}, indent=1))
        print("duration", round(duration, 2))
    elif sys.argv[1] == "audio":
        sents, speech_end, duration, E = setup()
        build_audio(sents, E, duration, sys.argv[3])
        remux(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "preview":
        main(None, None, preview_times=[float(x) for x in sys.argv[2].split(",")])
    else:
        main(sys.argv[1], sys.argv[2])
