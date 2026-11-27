# The PS2 look, the way Claude makes it (Nov 26)

Austin's DMs (Nov 25 to 26), oldest first:

- @retirdclub reel ("pov: you're 20 but it's 6pm and you're done"). Austin: "i feel like these do not look ai generated and look more like blender are something are you sure". He was right: these accounts render code-built or hand-built 3D, not AI video.
- @visualizemy_ "How to make low poly videos with Claude" (https://www.instagram.com/p/DgLKy4hTAGZ/, 43 s, 5.7K likes). Austin: "here is your prompting", and in chat on Nov 26: "it [shows] how to actually make the p2 style with claude".
- Today, 3:40 to 4:03 pm, not yet broken down: @mihad.builds "Your sound effects" (Claude Code), @withian.t "Why your Claude edits feel AI", and @science_in_8bit "Same rocket. Same drawing." (directed vs no direction, the same point as `ops/direction.md`). Austin also put a reel in a collection called SLOP IDEAS.

## Their recipe

The full prompt is free at visualizemy.com/videos/low-poly. It's a promo for their $9.99 "Studio Kit". We didn't download their raccoon file or skill; the prompt text was enough. They build it in three.js, one HTML file, and render it frame by frame:

0. "Make a [subject] explainer: [costume], [place]. three.js, one HTML file." Then 1080 x 1920 at 30 fps, every frame drawn from drawFrame(t), seeded random, the character facing camera with the mouth following the voice.
1. **Low poly:** about 300 triangles for the whole character, flat shading, one simple shape per body part, joints as separate rigid parts.
2. **Tiny textures:** painted in code at 64 px or less, nearest-neighbour, no mipmaps. The face is one 64 x 64 square, and expressions are swapped squares.
3. **Big pixels:** render at 270 x 480 and scale it up 4x with smoothing off. Captions get the same chunky edges.
4. **The wobble:** snap vertices to a grid one low-res pixel wide, use affine texture mapping, then cut colour to about 23 levels per channel with a 4x4 Bayer dither and very light scanlines.
5. **Slice it open:** a clipping plane, the halves opened toward camera, the inside a dark shell with triangle edges drawn, and one yellow label.
6. **A pose on every sentence:** fast in, small overshoot, hold, change, hitting on the stressed word. Captions are one word at a time, white with a dark outline.

Strictly, that is the PS1 look (their hashtag is #ps1graphics). The PS2-era accounts Austin means (retirdclub, zeromrrclub) have more polygons and smoother shading, but the same low resolution, point-sampled textures and dithered colour.

## Ours

`pipeline/ps2look.py` maps steps 1 to 4 onto the Blender cutscene kit. `pipeline/ps2_scene.py` builds an episode exactly as `cutscene_scene.py` does, then applies the look. `pipeline/render_ps2.py <episode> preview|clip|full` renders it at 270 x 480, dithers it, scales it up 4x and puts the usual overlay on top.

- **Low poly:** MakeHuman meshes are unsubdivided once, which gives a quarter of the faces. Unsubdivide follows the topology, so it stays the same on every frame (Collapse would flicker as the body moves). Big static props use Collapse. Everything gets flat shading.
- **Textures:** shrunk to 128 px with Closest filtering (`PS2_TEX=64` matches theirs exactly).
- **Wobble:** a Geometry Nodes pass snaps every vertex to the 270 x 480 grid in camera space, and a driver keeps the grid matched to the lens as shots cut. This was tested: every vertex lands exactly on the grid.
- **Hair:** strand radius x2.2, so it reads as chunky locks instead of fuzz at this size.
- **Left out:** affine texture warp (Blender has no switch for it). Steps 5 and 6 are direction, so they go in the episode script. For a chad episode: hit a pose on each line, and slice open the thing being argued about (the turkey, the TV).

## Same evening: Austin asked for new characters built this way

Austin: "give me my new chadlite character with these new rules", then "Yes, rebuild them" for the three friends.

Filtering the MakeHuman people (`ps2_scene.py`, since deleted) wasn't enough. Austin asked for the characters themselves to follow the rules, so they are rebuilt from scratch in `pipeline/lowpoly_cast.py`, using the recipe the way it's written:

- **Bodies:** about 470 triangles each, chamfered boxes and prisms hung on empties. The chad keeps his square jaw (a wide chin ring), quiff, blue hunter eyes and stubble.
- **Faces:** a face is 64 x 64 pixels, painted in numpy. An expression (eyes x brows x mouth) is another square, swapped per frame. Talking swaps between the open, half, o, ee and closed-lips mouths, driven by the voice.
- **Clothes:** the suit's V, tie and buttons, the jacket's plaid and the overall bib are painted on one 32 x 64 square on the front of the torso.
- **Table scene:** `lowpoly_scene.py` borrows the patio, props and golden-hour light from `cutscene_scene.py`, and the PS2 filter shrinks their textures to 128 px. Shots, look-at and the tag anchors follow the same timing.json as the MakeHuman kit. `render_ps2.pose_events` gives every line a pose:
  - a question opens the palms
  - a phone check holds the phone through the search card
  - the chad leans back with his arms crossed
  - laughs lean back, shocks recoil
  - other lines rotate through a raised hand, leaning in, and pointing
- **Bugs we hit:**
  - Blender crashes if images are made or swapped during an animation render, so every face square is made first and each frame is rendered as its own still.
  - On CPU previews, OIDN ran out of memory beside a GPU render, so denoising is off there.
  - Blender 5.2 moved node-modifier inputs to `mod.properties.inputs.<id>.value`.

First episode: "Saw It On A Reel: Black Friday", re-rendered with this cast the night it was made.

## Later that night: the chad gets the Matt Hagen look

Austin: "no kinda make him look like the actor that play matt hagan in clayface", then "emphasis on the wavy hair". That's Tom Rhys Harries. The reference is DC's first-look photo of him as Hagen on a magazine cover (/Film, Apr 21 2026: https://www.slashfilm.com/2153514/clayface-dc-studios-movie-tom-rhys-harries-matt-hagen-first-look/). In it he has chin-length, wavy dirty-blond hair, darker at the roots, with curtain bangs off a middle part. He also has hooded blue-grey eyes, a long straight nose, a lean face, light stubble and a dark heather tee.

- **Hair** (`wavy_hair()` in `lowpoly_cast.py`, 601 triangles in all):
  - a cap of 16-point rings, whose front edge is the curtain bangs: high at the middle part, down to the brows at the outer forehead, then past the temples to the cheekbones
  - an open skirt from one temple round the back to the other, hanging to the jaw
  - alternate columns kink in and out (the waves), and the tips are uneven and flick out
  - a few lumps in the cap so it reads tousled, not a helmet
  - the texture is wavy locks, darker roots and sun-bleached ends
- **Face:** blue-grey hooded eyes (two rows), lighter brows, a narrower chin and jaw, stubble cut to a third.
- It's a look, not a portrait, and we never name the actor or the film in a post.

Then Austin said "not a long face". The chad's head joint now has a scale (`head_scale` in his spec: 1.07 wide, 0.87 tall) that the face, ears and hair all follow, and his jaw is back to nearly its old width. Black Friday was rendered again with him before its Nov 27 slot.

## Nov 27: iterating against the photo, and a new set

Austin asked "why did you stop iterating", so the chad went through three more rounds, each compared side by side with the photo (`pipeline/out/chadlite/2026-11-27_Chad_vs_Reference.png`):

- The hair top was lowered and rounded, so it no longer reads as a box.
- The bangs now part off-centre and sweep diagonally to the outer brows. Low, even bangs had read as a bowl cut.
- The hair colour is more even.
- The stubble was cut to a trace.
- The nose is shallower and the jaw tapered a little.
- He has smile lines.

Austin also said "change up your scenery" (the finance bro at a table every time), so the cast can now stand in sets from `pipeline/lowpoly_sets.py`:

- **Painted textures:** the signs use a 5 x 7 pixel font, and the TVs play pictures painted at 32 x 18.
- **Poses:** the seated poses have standing versions (`lowpoly_sets.STAND`).
- **Cameras:** the wide frames full bodies and the set behind them.

The first set, `tv_aisle`, is a store's TV wall on Black Friday. It has a BLACK FRIDAY banner, pallets of boxed TVs with 60% OFF and DOORBUSTER signs, grey tile, fluorescent light and the screens' blue glow. `render_ps2.SETS` picks the set per episode, and `PS2_SET` overrides it.

`ops/questions.md` came out of the same morning.
