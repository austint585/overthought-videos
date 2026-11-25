"""The game-cutscene cast: one spec per character, built into vendor/cutscene_chars/<name>.blend by cutscene_build.py.

python cutscene_chars.py build <name> [<name> ...] | all     (skips characters already built; --force rebuilds)
python cutscene_chars.py list

Spec fields (MakeHuman/MPFB names; assets are folder/file inside the MPFB data folder):
  phenotype   gender 0 female .. 1 male; age 0.5 is 25 and 0.6 about 32; muscle, weight, height, proportions 0..1;
              race weights for the default skin blend
  targets     face and body sliders, e.g. {"target": "chin-width-incr", "value": 0.4}; the game look comes from a
              squarer jaw, stronger cheekbones and a heavier brow than MakeHuman's average face
  skin_mhmat, hair, eyebrows, eyelashes, eyes, teeth, tongue, clothes
"""
import json, os, subprocess, sys
from kit3d import BLENDER
from common import ROOT

OUT_DIR = os.path.join(ROOT, "vendor", "cutscene_chars")
USER_RES = os.path.join(ROOT, "vendor", "blender_user")       # MPFB and its CC0 packs live here, not in Austin's Blender

def T(name, value):
    return {"target": name, "value": value}

# stylized "game hero" face: square jaw, cheekbones, brow; applied to everyone, then each spec adds its own
GAME_FACE = [T("chin-width-incr", 0.8), T("chin-prominent-incr", 0.6), T("chin-bones-incr", 0.6),
             T("chin-height-incr", 0.25), T("l-cheek-bones-incr", 0.8), T("r-cheek-bones-incr", 0.8),
             T("l-cheek-volume-decr", 0.4), T("r-cheek-volume-decr", 0.4), T("head-square", 0.6),
             T("forehead-nubian-incr", 0.45), T("eyebrows-trans-down", 0.3), T("l-eye-height2-decr", 0.25),
             T("r-eye-height2-decr", 0.25), T("nose-point-width-decr", 0.2), T("neck-scale-horiz-incr", 0.4),
             T("mouth-scale-horiz-incr", 0.15)]

def bodyparts(brows="eyebrow001", lashes="eyelashes01", eyes="low-poly"):
    return {"eyes": f"{eyes}/{eyes}.mhclo", "eyebrows": f"{brows}/{brows}.mhclo",
            "eyelashes": f"{lashes}/{lashes}.mhclo", "teeth": "teeth_base/teeth_base.mhclo",
            "tongue": "tongue01/tongue01.mhclo"}

def merge_targets(*lists):
    """Later lists win: a character's own value replaces the shared game-face value for the same slider."""
    out = {}
    for lst in lists:
        for t in lst:
            out[t["target"]] = t["value"]
    return [T(k, v) for k, v in out.items()]


def male(name, age=0.55, muscle=0.75, weight=0.55, height=0.55, race=(0.05, 0.9, 0.05), hair="short02",
         skin="middleage_caucasian_male", clothes=("male_casualsuit03",), brows="eyebrow001", extra=(), style=None,
         proportions=0.7):
    asian, cauc, afr = race
    spec = {"name": name, "rig": "default",
            "phenotype": {"gender": 1.0, "age": age, "muscle": muscle, "weight": weight, "proportions": proportions,
                          "height": height, "cupsize": 0.5, "firmness": 0.5,
                          "race": {"asian": asian, "caucasian": cauc, "african": afr}},
            "targets": merge_targets(GAME_FACE, extra),
            "skin_mhmat": f"{skin}/{skin}.mhmat",
            "hair": f"{hair}/{hair}.mhclo" if hair else "",
            "clothes": [f"{c}/{c}.mhclo" for c in clothes]}
    spec.update(bodyparts(brows=brows))
    spec["style"] = style or {}          # skin_sat, skin_tint: read by cutscene_scene.restyle
    return spec

# the main character (Austin, Nov 24: "make him an absolute chad with gorgeous hair"). The first pass (every slider
# near 1, weight 0.6) came out puffy and round; Austin: "none of those look like a true chad". So: lean (low weight,
# no face fat, no double chin), a long rectangular head, the jaw, chin and brow pushed past MakeHuman's range
# (values over 1 are opened up in cutscene_build.py), hollow cheeks, low heavy brows over narrow eyes, a cleft chin,
# a neck as wide as the jaw, five-o'clock shadow and swept-back strand hair.
def LR(name, value):
    return [T(f"l-{name}", value), T(f"r-{name}", value)]

CHAD_FACE = [T("head-fat-decr", 1.0), T("head-square", 0.9), T("head-scale-vert-incr", 0.15),
             T("forehead-scale-vert-decr", 0.8), T("head-back-scale-depth-decr", 0.4), T("head-scale-horiz-decr", 0.2), T("chin-width-incr", 1.2), T("chin-bones-incr", 1.1),
             T("chin-prominent-incr", 1.2), T("chin-height-incr", 0.55), T("chin-cleft-incr", 0.8),
             T("chin-prognathism-incr", 0.25), *LR("cheek-bones-incr", 1.4), *LR("cheek-volume-decr", 0.9),
             T("forehead-nubian-incr", 1.5), T("forehead-trans-backward", 0.3),
             T("eyebrows-trans-down", 1.0), T("eyebrows-trans-forward", 0.9), T("eyebrows-angle-down", 0.15),
             *LR("eye-height2-decr", 0.6), *LR("eye-corner2-up", 0.35), *LR("eye-bag-decr", 1.0),
             *LR("eye-scale-decr", 0.2), T("nose-greek-incr", 0.5), T("nose-hump-decr", 0.5),
             T("nose-point-width-decr", 0.5), T("nose-scale-vert-incr", 0.3), T("nose-width1-decr", 0.3),
             T("mouth-scale-horiz-incr", 0.1), T("mouth-upperlip-volume-decr", 0.4),
             T("mouth-lowerlip-volume-decr", 0.2), T("neck-double-decr", 1.0), T("neck-scale-horiz-incr", 1.0),
             T("neck-scale-depth-incr", 0.5), T("measure-neck-circ-incr", 1.0), *LR("ear-scale-decr", 0.3),
             *LR("ear-flap-decr", 0.5)]
CHAD_BODY = [T("measure-shoulder-dist-incr", 0.7), T("torso-vshape-incr", 0.9), T("torso-muscle-pectoral-incr", 0.6),
             T("torso-muscle-dorsi-incr", 0.6), T("measure-waist-circ-decr", 0.4), T("l-upperarm-muscle-incr", 0.6),
             T("r-upperarm-muscle-incr", 0.6), T("l-upperarm-shoulder-muscle-incr", 0.7),
             T("r-upperarm-shoulder-muscle-incr", 0.7), T("measure-upperarm-circ-incr", 0.5)]
CHAD_STYLE = {"skin_tint": [1.0, 0.86, 0.74], "skin_sat": 1.1, "hair": "gloss", "stubble": 1.0, "scalp": 0.9,
              "rest": "chad", "eyes": "blue"}
# swept-back strand hair (cutscene_hair.grow_hair): a tall quiff at the front, the rest combed back, waves in each lock
CHAD_HAIR = {"count": 40000, "guides": 800, "hairline": 0.058, "length_top": 0.12, "length_side": 0.045,
             "length_back": 0.035, "lift_front": 0.03, "lift_top": 0.011, "lift_side": 0.003, "wave_amp": 0.003,
             "wave_len": 0.07, "clump": 0.8, "frizz": 0.0003, "roughness": 0.38, "radius": 0.00025,
             "colors": ["1a0f08", "3a2312", "6b4426", "9a6a3e"]}   # dark roots to warm brown tips


def chad(name, hair="", strand_hair=None):
    spec = male(name, age=0.55, muscle=1.0, weight=0.3, height=0.8, proportions=1.0, hair=hair, brows="eyebrow009",
                skin="middleage_caucasian_male", clothes=("toigo_basic_tucked_t-shirt", "shoes01"),   # casualsuit06's tee has a MakeHuman logo
                extra=CHAD_FACE + CHAD_BODY, style=CHAD_STYLE)
    spec["sculpt"] = {"cranium": 0.84}         # a shorter skull above the brows (no slider does just that)
    if strand_hair:
        spec["strand_hair"] = strand_hair
    return spec


def strands(spec, hair):
    """Swap a character's card hair for strand hair (cutscene_hair.grow_hair)."""
    spec["hair"] = ""
    spec["strand_hair"] = hair
    return spec


# the friends got strand hair and leaner faces on Nov 24 too: next to the rebuilt chad, the stock card hair and soft
# MakeHuman faces looked like a different, older game
LEAN = [T("head-fat-decr", 0.6), T("neck-double-decr", 0.8), *LR("cheek-volume-decr", 0.4)]
SIDE_PART = {"comb": "side", "part": -0.032, "count": 30000, "guides": 700, "hairline": 0.062, "length_top": 0.09,
             "length_side": 0.035, "length_back": 0.03, "lift_front": 0.008, "lift_top": 0.006, "lift_side": 0.002,
             "wave_amp": 0.0015, "wave_len": 0.08, "clump": 0.75, "frizz": 0.0002, "roughness": 0.32,
             "radius": 0.00025, "colors": ["2a1c10", "4e3620", "7a5a36", "a8865a"]}
CROP = {"comb": "crop", "count": 30000, "guides": 700, "hairline": 0.06, "length_top": 0.04, "length_side": 0.018,
        "length_back": 0.016, "lift_front": 0.004, "lift_top": 0.004, "lift_side": 0.001, "wave_amp": 0.001,
        "wave_len": 0.05, "clump": 0.55, "frizz": 0.0003, "roughness": 0.45, "radius": 0.00025,
        "colors": ["070605", "0e0b0a", "171311", "241e1a"], "sheen": 0.04, "spec_tint": "b8b0a8"}   # black hair: no warm sheen
BUZZ = dict(CROP, length_top=0.014, length_side=0.009, length_back=0.008, lift_top=0.002, clump=0.3,
            radius=0.0002, count=36000)

CAST = {
    "chad": chad("chad", strand_hair=CHAD_HAIR),

    # the look-test guy: a late-twenties office worker in a casual suit
    "test_guy": male("test_guy"),
    # the friends (Nov 24): a finance guy, a tech guy, a tradesman
    "suit": strands(male("suit", age=0.6, weight=0.45, brows="eyebrow008", race=(0.0, 1.0, 0.0), extra=LEAN,
                         skin="middleage_caucasian_male", clothes=("toigo_male_suit_tie_and_jacket", "shoes03"),
                         style={"eyes": "brown", "stubble": 0.15, "scalp": 0.8}), SIDE_PART),
    "jacket": strands(male("jacket", age=0.52, muscle=0.6, weight=0.42, brows="eyebrow009", race=(0.55, 0.45, 0.0),
                           extra=LEAN, skin="middleage_asian_male", clothes=("male_casualsuit05", "shoes06"),
                           style={"eyes": "brown", "scalp": 0.9}), CROP),
    "overalls": strands(male("overalls", age=0.58, muscle=0.9, weight=0.5, brows="eyebrow012",
                             race=(0.0, 0.25, 0.75), skin="middleage_african_male", clothes=("male_worksuit01", "shoes02"),
                             extra=LEAN + [T("neck-scale-horiz-incr", 0.4)],
                             style={"skin_sat": 0.82, "skin_tint": [1.0, 0.95, 0.92], "eyes": "brown", "scalp": 0.95}),
                        BUZZ),
}

def build(name, force=False):
    out = os.path.join(OUT_DIR, f"{name}.blend")
    if os.path.exists(out) and not force:
        print("already built:", out)
        return out
    os.makedirs(OUT_DIR, exist_ok=True)
    spec_path = os.path.join(OUT_DIR, f"{name}.json")
    json.dump(CAST[name], open(spec_path, "w"), indent=1)
    env = dict(os.environ, BLENDER_USER_RESOURCES=USER_RES)
    subprocess.run([BLENDER, "-b", "-noaudio", "-P", os.path.join(ROOT, "cutscene_build.py"), "--", spec_path, out],
                   check=True, env=env)
    return out

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "list":
        print("\n".join(sorted(CAST)))
    elif args[0] == "build":
        force = "--force" in args
        names = [a for a in args[1:] if not a.startswith("--")]
        for n in (sorted(CAST) if names == ["all"] else names):
            build(n, force)
