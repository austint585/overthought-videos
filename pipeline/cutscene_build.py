"""Builds one game-cutscene character with MPFB (MakeHuman for Blender) and saves it as its own .blend, so episode
scenes can append it without the add-on. Runs in the pipeline's own Blender user folder (vendor/blender_user, where
MPFB 2.0.18 and the CC0 MakeHuman packs are installed); never with --factory-startup, which turns add-ons off.

python cutscene_chars.py build <name>|all      (the usual way: writes vendor/cutscene_chars/<name>.blend)
blender -b -P cutscene_build.py -- spec.json out.blend

What the saved file holds: the body (default MakeHuman rig with jaw and eye bones, no subdivision for the game
look), the face shape keys (22 Microsoft visemes and the 52 ARKit face units, all at 0), eyes, brows, lashes, teeth,
tongue, hair and clothes. Brows and lashes get a Surface Deform onto the body, so they follow the face shape keys.
"""
import json, os, sys
import bpy
import addon_utils

argv = sys.argv[sys.argv.index("--") + 1:]
SPEC = json.load(open(argv[0]))
OUT = argv[1]

MOD = "bl_ext.user_default.mpfb"
if MOD not in bpy.context.preferences.addons:
    addon_utils.enable(MOD, default_set=True)
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.faceservice import FaceService

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

info = HumanService._create_default_human_info_dict()
for k in ("phenotype", "targets", "eyes", "eyebrows", "eyelashes", "teeth", "tongue", "hair", "clothes", "skin_mhmat",
          "rig"):
    if k in SPEC:
        info[k] = SPEC[k]
info["name"] = SPEC["name"]
info["skin_material_type"] = "MAKESKIN"          # a plain textured skin; the scene restyles it for the game look
info["clothes_material_type"] = "MAKESKIN"
info["eyes_material_type"] = "MAKESKIN"

settings = HumanService.get_default_deserialization_settings()
settings["subdiv_levels"] = 0                    # no subdivision: the slightly faceted silhouette is the look
settings["material_instances"] = "NEVER"
body = HumanService.deserialize_from_dict(info, settings)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cutscene_hair

# sliders pushed past MakeHuman's range (the chad's jaw and brow): Blender clamps a shape key at its slider_max, so
# open that up, then refit the clothes, eyes, brows and rig to the new face
kb = body.data.shape_keys.key_blocks
boosted = [t for t in SPEC.get("targets", []) if t["value"] > 1.0 and t["target"] in kb]
for t in boosted:
    kb[t["target"]].slider_max = max(2.0, t["value"])
    kb[t["target"]].value = t["value"]

# sculpt (spec "sculpt"), for what no slider does: "cranium" < 1 squashes everything above the brows toward eye
# level, so a long jaw doesn't come with a conehead. Saved as one more shape key on top of the sliders.
sculpt = SPEC.get("sculpt", {})
if sculpt.get("cranium"):
    import numpy as np
    co0 = cutscene_hair.mixed_coords(body)
    eye = co0[cutscene_hair.group_weights(body, "joint-l-eye") > 0.5]
    z0 = float(eye[:, 2].mean()) + 0.03
    z = co0[:, 2]
    w = np.clip((z - z0) / 0.03, 0, 1)
    w = w * w * (3 - 2 * w)
    new = co0.copy()
    new[:, 2] = z - w * (1 - sculpt["cranium"]) * (z - z0)
    key = body.shape_key_add(name="cutscene-sculpt", from_mix=False)
    base = np.empty(len(co0) * 3)
    kb[0].data.foreach_get("co", base)
    key.data.foreach_set("co", base + (new - co0).reshape(-1))
    key.value = 1.0
if boosted or sculpt:
    HumanService.refit(body)
FaceService.load_targets(body, load_microsoft_visemes=True, load_meta_visemes=False, load_arkit_faceunits=True)

rig = body.parent
co = cutscene_hair.mixed_coords(body)
cutscene_hair.stubble_masks(body, rig, co, SPEC.get("strand_hair"))   # 'beard' and 'scalp' attributes for the skin
if SPEC.get("strand_hair"):
    cutscene_hair.grow_hair(body, rig, co, SPEC["strand_hair"], SPEC["name"])

# brows and lashes ride the face: bind them to the body surface so visemes, smiles and blinks move them too
bpy.context.view_layer.update()
for ob in bpy.data.objects:
    if ob.type != "MESH" or ob is body:
        continue
    low = ob.name.lower()
    if "eyebrow" in low or "eyelash" in low:
        m = ob.modifiers.new("follow_face", "SURFACE_DEFORM")
        m.target = body
        bpy.context.view_layer.objects.active = ob
        for o in bpy.context.selected_objects:
            o.select_set(False)
        ob.select_set(True)
        with bpy.context.temp_override(object=ob, active_object=ob):
            bpy.ops.object.surfacedeform_bind(modifier=m.name)
        # Surface Deform follows the body's final shape (shape keys and armature), so the part's own armature
        # modifier would move it twice: drop it
        for other in [x for x in ob.modifiers if x.type == "ARMATURE"]:
            ob.modifiers.remove(other)

body["cutscene_name"] = SPEC["name"]
body["cutscene_style"] = json.dumps(SPEC.get("style", {}))      # per-character look hints for the scene
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("saved", OUT, "objects:", [o.name for o in bpy.data.objects])
