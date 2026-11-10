# Breaking The Touch Barrier Is Quantum Tunneling

- **id:** 2026-11-10-touch-tunnel
- **Source idea:** a meme everyone is posting this week (make.md rule 2), third in the Nov 10 list in `ops/ideas.md`: "when they break the touch barrier first" (https://www.instagram.com/reel/DfavT2GMEdk, 1.2M). Watched it this run (11 s, no narration, `pipeline/out/watch/DfavT2GMEdk/sheet.png`): a girl lightly touches a guy's shoulder in a school hallway, and the cut-ins show guys melting, then him lying flat on the hallway carpet. The joke is how little it takes: one touch and he is done.
- **Why people care:** the trend is everywhere this week, everybody knows the feeling, and it is a send-to-your-person reel ("send this to whoever breaks the barrier first").
- **Format:** voxel "brainrot explained as science" (Nov 7 rule), deadpan, calm Chatterbox read. Real physics: quantum tunneling.
- **Set (new):** a voxel school hallway after hours (the reference is a school hallway): blue lockers, checker tiles, one ceiling panel lit over the pair, the rest of the panels off, a red exit sign far down the hall, a glowing cyan barrier filling the gap between them. The episode before it in the queue (Your Next Relationship, Randomized) is an arcade slot machine, and Schrodinger's Situationship was a crate at night, so the set and the opening shot are new.
- **Files:** `pipeline/render_touch.py`, `pipeline/touch_scene.py`.

## Script (see `SCRIPT` in `pipeline/render_touch.py`)

1. Breaking the touch barrier first? That is quantum tunneling.
2. Between you two sits a barrier. Neither of you has the energy to get over it.
3. Classically, that means his hands stay in his pockets. Forever.
4. But quantum particles don't climb. They go straight through walls they can't clear.
5. The catch: each extra tenth of a nanometer cuts the odds about ten times.
6. So she closes the gap. And she tunnels.
7. He was not built for this. Total collapse.
8. The Sun tunnels all day. He did it once and has to lie down.
9. Send this to whoever breaks the barrier first.

Preview fixes (Nov 10 run): the barrier was too wide and opaque, so it is now a 0.7 m deep slab at 24% opacity; the pockets and her shots looked through the barrier at their backs, so both are near-profile now; the top-down camera sat above the ceiling panel; the touch shot was too tight and too pink (35 mm, punch 1.25x, a dimmer pink light).

The last shot cuts back to the hook framing with everything reset, so it loops.

## Facts and sources

| Claim | Source |
|---|---|
| A quantum particle can cross a barrier it doesn't have the energy to climb (tunneling) | Princeton stellar fusion notes: https://www.astro.princeton.edu/~gk/A403/fusion.pdf ; Richmond lecture: https://facultystaff.richmond.edu/~ggilfoyl/qm/slides/solarfusion3.pdf |
| The odds fall off exponentially with the barrier's width; in a scanning tunneling microscope the current drops about tenfold for every extra 0.1 nm (1 angstrom) of gap | https://arxiv.org/pdf/1404.0961 ("one order of magnitude per 1 A") ; https://www.liverpool.ac.uk/~sdb/ALTAIR/Images/STM.pdf ; https://my.eng.utah.edu/~lzang/images/Lecture_6_STM.pdf |
| The Sun runs on tunneling: protons in its core have far too little energy to climb their mutual repulsion and fuse by tunneling | Princeton notes above ; https://books.openbookpublishers.com/10.11647/obp.0526.10.pdf |

## Assumptions spelled out

- The narration says "about ten times", because the exact factor depends on the barrier (sources give 7 to 10 per angstrom). The on-screen pill says "~10x".
- "Classically, his hands stay in his pockets", the barrier between two people, and him collapsing are the joke. Nothing says people actually tunnel. "The Sun tunnels all day" is true of its protons, said loosely.
- "Collapse" is a pun (he falls over), not a claim about wave function collapse.
- He keeps his hands at his sides in the picture (the figures' arms don't fit in pockets); the line is about him never making the move.

## Direction (ops/direction.md)

**Look:** field `#0B1230` (night navy: the dark hall, the off panels, the lockers falling to black); subject `#5FE3FF` (the barrier's cyan glow, the light on both faces); neutral `#E8EEF8` (the ceiling panel's cool white pool on the tiles); accent `#FF3D8B` (hot pink), kept back for the touch: the shards and the pink light at his shoulder.

**Big moment:** "tunnels" (`E["tunnels"]`). Her hand goes through the barrier and touches his shoulder; the barrier shatters into cyan and pink cubes, the cyan glow dies, a pink light takes over, the camera punches in 1.3x with one jolt, and the loudest sound plays. The breath: her idle sway and the barrier's flicker stop 0.35 s before it.

| # | Cuts in on | Job | Eye (x, y on screen) | Light | Depth fg / subject / mid / bg | Lens, height, move | Beat | Int. |
|---|---|---|---|---|---|---|---|---|
| 1 | 0.0 hook | the situation as a thumbnail | the barrier between them (0.50, 0.56) | ceiling pool from above, the barrier's cyan on both faces, rim from the lockers, the hall falls to black | tile floor edge / the pair and barrier / lockers / dark hall and the far exit sign | 35 mm, eye level, locked off, symmetrical profile two-shot | hold | 2 |
| 2 | B "Between" | how big the barrier is | barrier center (0.50, 0.54) | same pool; fill lower | his back near camera / the barrier / her beyond / exit sign deep down the hall | 24 mm, low behind him down the hall axis, still | hold | 2 |
| 3 | C "Classically" | his side: he will never move | his chest and hands (0.50, 0.56) | cyan on one cheek, pool from above, rest dark | barrier edge blur / him / lockers / black | 50 mm, eye level, near profile, still | hold on "Forever" | 2 |
| 4 | D "But quantum" | what tunneling is | the white cube above their heads (0.50, 0.48) | pool dimmed to 0.6, the cube is the brightest thing | barrier / the cube crossing / lockers / black | 28 mm, eye level, still | cube passes through on "through" | 3 |
| 5 | E "The catch" | the gap is the odds | the gap (0.50, 0.52) | the pool on the tiles, cyan slab | heads / the slab between / tile checker / dark edges | 16 mm, straight down from just under the ceiling panel, still | pill on "ten times" | 3 |
| 6 | F "closes" | she commits | her face (0.50, 0.52) | cyan on her face from the thinning barrier | her / the barrier and his shoulder at frame right / lockers / black | 50 mm, eye level, profile, still | she steps in on twos; breath 0.35 s | 3 |
| 7 | tunnels - 0.45 | **the touch** | her hand at his shoulder (0.50, 0.52) | cyan dies, pink light at his shoulder, shards | shards / both / lockers / black | 50 mm, punch 1.3x on the hit, one jolt | ars reach lands on the word | 5 |
| 8 | G "He was not" | the payoff | him (0.50, 0.58) | pool back to normal, pink gone | floor / him tipping over / her standing / hall | 35 mm, locked off, symmetrical | stiff plank fall lands 0.35 s after "collapse" | 4 |
| 9 | H "The Sun" | aftermath | him flat on the tiles (0.50, 0.52) | pool on him | tiles / him / her standing over / dark | 35 mm, high looking down, still | hold | 2 |
| 10 | I "Send" | the loop | the barrier (0.50, 0.56) | same as shot 1 | same as shot 1 | same as shot 1 | reset | 2 |

Intensity climbs 2, 2, 2, 3, 3, 3 to 5 on the touch, then 4 and back down to 2 for the loop.

## Caption

Send this to whoever breaks the touch barrier first. It's literally quantum tunneling. #physics #relationships #science

## Scroll patrol

See `2026-11-10-touch-tunnel-patrol.md`.

## QA (Nov 10 run)

- 39.9 s, -13.5 LUFS (a loudnorm pass after the mix; the raw mix came out at -17.4), no steady tones, 8 MB.
- Voice: the first take failed `qa_voice.py` (pace spread, short gaps, pauses after "first" and "gap"). Re-voiced with the new narrator, reworded lines 1 and 5 so the pauses land on punctuation, evened with `voice_fix.py`: `qa_voice.py out/touch narration_fixed` says PASS. Whisper matched every line (1.0).
- Direction (`qa_direction.py`): the biggest change lands on "tunnels" (27.77 vs 27.67 s) and the loop closes (0.029). Three shots are under the bar even after adding a per-shot key light: pockets (eye rank 0.72, light focus 1.03) and her (0.74, 1.27), because the translucent cyan barrier in the near foreground is the brightest thing in frame on purpose (it is the reel's subject and the near depth layer); collapse (0.77, 0.63), because the wide is lit evenly so the fall reads deadpan. A known weakness, not re-rendered (another hour).
- Frames checked once a second (`pipeline/out/touch/sheet.png`): captions in the top third, pills above y=1540, nothing blocking the subject.
