# The Bicep Heart, A Nature Documentary

- **id:** 2026-11-13-bicep-heart
- **Source idea:** make.md "Pick the idea", rule 3 (form x line). No new DM: the newest item in the "Overthought" thread (read in Chrome, Nov 13, 10:10 am) is Austin's Nov 12 "make your own version of we could go up", already made (cat-go-up). The Nov 12 blind trend test (`ops/research/2026-11-12-blind-trend-test.md`) ranked "Have you ever heard of a bicep heart?" first and said to make it first because it is timely, so this run uses that pairing instead of spending a new agent on the same question.
- **The trend:** the bicep heart. Flex one arm and curl the other hand over it to make a heart. It took off on TikTok and Instagram Reels from late October into early November 2026 (Know Your Meme explainer: https://trending.knowyourmeme.com/editorials/guides/what-is-the-bicep-heart-trend-how-to-do-the-viral-tiktok-and-instagram-reels-thirst-trap-trend-explained ; Box Life: https://boxlifemagazine.com/bicep-heart-trend-tiktok-viral/ ; the kavithageorge TikTok at 5.3M, https://www.tiktok.com/@kavithageorge/video/7703044626931895583). Pet and "anyone can do it" versions followed.
- **The form:** a hushed nature-documentary narrator (the calm narrator over nature footage format, 2.5M on Nov 7: https://www.instagram.com/reel/DfchdnwzPXi).
- **Why people care:** everyone has seen the pose this month, most of us know a guy who does it, and a real animal with a similar display (the fiddler crab, which courts by waving one giant claw) is true and funnier than anything we could invent. Share target: "send this to the guy who flexes in the gym mirror".
- **Look (style_rules.md):** clay, character satire (the @petersindex reference). The episode before it in the queue (We Could Go Up, 17:30) is white line art on black and the one before that (Friday the 13th) is voxel, so this is a new style, a new set (a night gym with a wall mirror, plus a mudflat at golden hour) and a new opening.
- **Files:** `pipeline/render_bicep.py`, `pipeline/bicep_scene.py`.

## Script (`SCRIPT` in `pipeline/render_bicep.py`)

1. At the gym mirror, the male performs the *bicep heart.*
2. One arm flexes. The other hand curls over the top. A *heart.*
3. Biologists have seen this before. On a *mudflat.*
4. The male fiddler crab grows one giant claw. It can weigh *half his body.*
5. He waves it at every female who walks past.
6. In *2018,* scientists used *robot crabs.* Females chose the waves that sped *up.*
7. So the male *speeds up.*
8. She walks right past him. And does *her own.*
9. Send this to the guy who flexes in the gym mirror.

Loop: the last shot is the hook framing again (the bro at the mirror, mid-heart).

## Facts and sources

| Claim | Source |
|---|---|
| The bicep heart: one arm flexed, the other hand curled over it to make a heart | Know Your Meme explainer (link above) |
| Male fiddler crabs grow one oversized claw that can weigh up to about half the body | National Geographic, https://www.nationalgeographic.com/science/article/youll-find-the-biggest-male-appendage-in-the-world-at-the-beach ("roughly half"); UT Marine Science Institute, https://utmsi.utexas.edu/science-and-the-sea/radio-program/crab-claws/ ("up to half"). The line says "can weigh", since many males carry less (Stony Brook gives a third for the sand fiddler). |
| They wave it to court females | Same UTMSI page; Stony Brook marine bio, https://you.stonybrook.edu/marinebio/?p=294 |
| They live on mudflats | Uca mjoebergi, the species in the robot studies, lives on intertidal mudflats in northern Australia (the studies below). |
| 2018: robot crabs; females preferred displays that sped up over constant or slowing ones | Mowles, Jennions and Backwell, "Robotic crabs reveal that female fiddler crabs are sensitive to changes in male display rate", Biology Letters 2018: https://researchportalplus.anu.edu.au/en/publications/robotic-crabs-reveal-that-female-fiddler-crabs-are-sensitive-to-c/ ; summary: https://www.expressandstar.com/news/science/robots-reveal-how-female-fiddler-crabs-prefer-fast-dancers-6236365 |

## Assumptions spelled out

- The gym bro and the woman are characters; the narrator treats the human pose "as" a courtship display. That is the joke, not a claim about people.
- "Biologists have seen this before" means the crab's claw-waving display, which is real; we do not say the pose came from crabs.
- Line 6 says "used" robot crabs (the lab had built them for earlier studies), not "built".
- No numbers on screen beyond "up to 1/2 body weight" and "2018".

## Shot sheet (ops/direction.md)

**Look.** Gym: night-blue field #0B1226, warm overhead spot amber #FFB06A on the bro, neutral cream (mirror frame, rack chrome). Mudflat: the same four slots, warm sun on the crab, the mud falling into blue shadow. **Accent kept back: hot pink #FF3F8A**, first seen on the neon heart sign at the big moment.

**Big moment:** "her own" (E["own"]). She stops at the mirror, does the heart, the pink neon heart above the mirror switches on, the camera pushes in on the hit, the loudest sound. Everything before it is amber and blue.

Intensity: 2, 2, 2, 3, 3, 3, 4, 5, 2.

| # | Starts | Eye on screen | Light | Depth (fg / subject / mid / bg) | Lens, height, move | Beat |
|---|---|---|---|---|---|---|
| 1 hook | 0 | the bro mid-heart, three-quarter front (0.5, 0.50) | one overhead spot on him, the gym falls to black | his flexed arm / bro / dark gym / dark neon on the back wall | 30 mm, chest height, from the mirror side, locked off | frame 0 already mid-pose with the heart outline drawn (thumbnail) |
| 2 heart | B | the arm and hand (0.5, 0.48) | same spot, rim from the mirror | fg blur of his shoulder / the arm / mirror / black | 55 mm, close, still | the heart outline draws on "heart" |
| 3 mudflat | C | a single crab, small (0.5, 0.56) | low gold sun from frame right, sky dusk blue | mud lump / crab / burrows and puddles / mangrove silhouettes | 24 mm, low, still (scale, comedy) | hold, then the claw rises |
| 4 claw | D | the big claw (0.5, 0.50) | the sun as a rim on the claw | mud blur / claw / body / sky | 55 mm, crab eye level, slow push | "half his body" |
| 5 wave | E | the crab, a female walking past (0.5, 0.54) | same sun | mud / crab and female / burrows / sky | 35 mm, low, still | each wave on twos |
| 6 robot | F | the robot crab on its rod (0.52, 0.52) | same sun | a lab clamp / robot / real crab / sky | 35 mm, still | the robot's wave speeds up, the female turns to it on "up" |
| 7 faster | G | the bro, frontal in the mirror (0.5, 0.50) | the spot, harder | rack / bro / mirror / black | 35 mm, locked off, symmetrical | the heart pumps faster each beat |
| 8 her own | H | she walks into frame, stops at the mirror (0.5, 0.50) | the spot; on "own" the pink neon switches on | bro (out of focus) / her / mirror / black | 35 mm, still, push on the hit | 0.3 s still before "own", then the push and the pink |
| 9 loop | I | back to the hook framing | as shot 1 | as shot 1 | as shot 1 | cuts back into frame 0 |

## Scroll patrol (`2026-11-13-bicep-heart-patrol.md`)

5 of 10, 6 of 10 with fixes. Took: the heart outline drawn on frame 0, an "ALSO A COURTSHIP DISPLAY" pill on the first crab shot so the gym-to-mudflat cut reads with the sound off, and the claw starts rising on "mudflat". Skipped the new first lines: they overclaim (crabs don't make hearts) or describe the format; the pose on frame 0 is the hook.

## Build notes (Nov 13 run)

- The first plan opened over his shoulder on his reflection. It didn't work: Eevee only reflects what is already on screen, and from any angle where both fit his reflection hides behind his own back. The opening is now three-quarter front from the mirror side (the mirror sits behind the camera), with the heart outline drawn on frame 0.
- The clay figure's arms are one piece, so the scene splits them at the elbow and stretches them (the stock arms were too short for one hand to reach the other bicep). The left hand is placed by a small IK search; it lands within 3 cm of the bicep.
- Line 4 was re-voiced as two sentences ("one giant claw. It can weigh half his body.") after qa_voice flagged a 0.2 s pause inside the phrase near "claw".
- QA (final MP4): 32.6 s, 8.2 MB, -13.8 LUFS after a loudnorm pass on the audio only (the mix came out at -16.3), no steady tones, qa_voice PASS, loop difference 0.017. qa_direction notes: the mudflat shots have even daylight (the sun scene, kept), and the frame at 26 s is mostly the empty spot-lit floor for a second before she walks in. The pink neon on "own" is the only accent change.
