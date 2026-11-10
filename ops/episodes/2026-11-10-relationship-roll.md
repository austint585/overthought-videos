# Your Next Relationship, Randomized

- **id:** 2026-11-10-relationship-roll
- **Source idea:** a meme everyone is posting this week (make.md rule 2), lined up in `ops/ideas.md` on Nov 10 from a vidIQ outlier search: a filter that spins random traits for your next partner (https://www.instagram.com/reel/DfWEDrWPIJC 2.4M, https://www.instagram.com/reel/DfZODBpJIbv 954K, a TikTok at 1.4M). Also the interactive beat from the Nov 9 @science_in_8bit note: the viewer does something (pauses) in the first second.
- **Why people care:** the filter is everywhere this week and the pause mechanic gives every viewer a personal result to comment, which is what pushes comments and sends.
- **Format:** voxel, deadpan, calm Chatterbox read. Our own categories and our own results, nothing from the filter.
- **Set (new):** a voxel arcade at night: dark carpet, neon strips, four background cabinets, a pink and gold slot machine with a glowing header, four reel rows spinning the whole time, a lever, one player. The GTA 6 episode before it is a living room, so the set and the opening shot are new. Opening shot: straight on the machine, reels already spinning, "PAUSE NOW" on frame one.
- **Mechanic:** four result cards (how you meet, how they text, red flag, how it ends) are drawn on every frame and change every 3 frames (10 picks a second), so any paused frame is a complete, readable result. The order is a fixed shuffle (seed 1111), so it is the same each render.
- **Files:** `pipeline/render_roll.py`, `pipeline/roll_scene.py`.

## Script (see `SCRIPT` in `pipeline/render_roll.py`)

1. Pause the video now. Whatever you stopped on is your next relationship.
2. Row one: how you meet. Row two: how they text.
3. Row three: their red flag. Row four: how it ends.
4. No rerolls. The machine has spoken.
5. Comment what you got. Be honest.
6. Missed it? It never stops. Pause sooner.

The last line runs back into the first, so it loops.

## Facts and sources

No factual claims. Every pick is a joke about a made-up partner; none is presented as a statistic or a prediction.

## Assumptions spelled out

- "The machine has spoken" and the results are the joke. Nothing says the machine predicts anything.
- Picks are about habits (texting, ketchup on steak, a podcast), never about anyone's ethnicity, religion or sexuality. "Lost to GTA 6" is a nod to the episode before it.
- Picks are gender-neutral ("they"), so the reel works for everyone.

## Caption

Pause it and comment what you got. No rerolls. #relationships #dating #pausechallenge

## Scroll patrol

See `2026-11-10-relationship-roll-patrol.md`.

Patrol changes: "PAUSE NOW" as the big frame-one text (taken), cards always complete on any frame (taken). Skipped the suggestion to slow the picks to make them readable while playing: the whole point is that you can't, so you pause.
