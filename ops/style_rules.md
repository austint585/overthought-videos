# Style rule set (Austin, Nov 11: "you are still doing the minecraft style animation. do the animation styles i sent you where it is directed and not prompted")

Every make run reads this before step 5 of `ops/make.md`. The voxel kit is no longer the default. Pick the look in this order:

1. **A remake copies the source reel's own look.** If Austin sent a reel or TikTok to remake, the episode is built in that reel's visual language (watch it frame by frame first), with our own drawings, script and voice. Example: the @cluberich "go up" edit is white line-art motion graphics on black, so the raw liver parody is built that way in HyperFrames, not in voxels.
2. **Otherwise, one of the styles Austin sent** (`ops/style.md` has the links and notes). Rotate them; never the same style twice in a row.
3. **Voxel only when the source itself is Minecraft-styled** (the brainrot-as-Minecraft-science remakes of Oct 27 and 28).

## The styles and how we make each

| Style (his reference) | Use it for | Kit | The rules that make it |
|---|---|---|---|
| Minimal line motion graphics (@cluberich "go up", Nov 11) | hype speeches, life advice, "you" lists, parodies of them | HyperFrames (`pipeline/hf/<slug>`, generator `pipeline/render_liver.py`) | black field with a soft center lift; white line icons (stroke 5 px); Montserrat 800 caps, 0.12em tracking; one glow word per beat; white pills with black caps; one accent color kept for the big moment; a new graphic on each stressed word |
| Directed pixel art (@science_in_8bit, Nov 9 to 11) | science claims with a countdown or counter | HyperFrames canvas or skia at low resolution, scaled up with nearest-neighbor | one centered subject; warm glow on a cool field; big pixel type at the top; a counter on screen; one "go inside" move; a seamless loop |
| Clay (@petersindex) | character satire | `pipeline/clay.py`, `render_gymclay.py` | plasticine materials, tilt-shift depth of field, warm practicals against a blue night, cuts every 1 to 2 s |
| Pastel toy (@howyourhouseworks.au) | "you're doing this habit wrong" explainers | `render_water.py`, `water_scene.py` | flat pastel props, bright soft daylight, numbers on in-scene signs that count up |
| Product studio (@speedy_devv, @seethroughworks) | how an everyday object works | `render_led.py`, `led_scene.py`, Poly Haven assets | real CC0 models, dark studio, cutaways, a magnified section, leader-line labels, honesty notes |
| Toon (@aiwithmax) | absurd lists and rankings | `pipeline/toon.py`, `render_height.py` | cel shading with one hard shadow step, thick outlines, giant everyday objects as sets, a hanging sign per idea |

## Directed, not prompted (the checks every episode passes)

From `ops/direction.md` and research_notes/2026-11-11_Directed_Motion_Style.md. Write the shot sheet before any code, then check:

1. One focal point per beat; everything else dims to 35 to 55% or leaves.
2. One idea per beat, 1.2 to 3 s, beat lengths varying by 30% or more.
3. One big moment per video: the biggest change in light, scale and sound, after 0.3 to 0.5 s of stillness. The accent color appears there first.
4. Graphics land on the stressed word, 0 to 2 frames ahead of the sound.
5. A landed title is dead still; arrivals ease out on a long tail, exits are 40 to 50% shorter.
6. Slam words (the punchlines) drop from 1.25x to 1x in about 6 frames with a 4-frame shake; nothing else does.
7. Glow only on the focal element.
8. Hard cuts or blur swaps between beats, never default crossfades.
9. Frame 0 is a directed still that works as the thumbnail with the sound off.
10. All words inside x 90 to 990, y 220 to 1330 on 1080x1920 (the Reels buttons and caption cover the rest); nothing read under 28 px.
11. Before the full render: stills of every beat, compared with the shot sheet. After it: the frame sheet once a second and `qa_voice.py`, then `"watched": "passed"`.
