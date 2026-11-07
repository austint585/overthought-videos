# Secondhand Cringe

- **id:** 2026-11-07-secondhand-cringe
- **Source idea:** ours. A tag-a-friend joke on vicarious embarrassment: Krach, Paulus and colleagues (Marburg and Lubeck, PLoS ONE, 2011) scanned people watching others in embarrassing situations. The anterior cingulate cortex and the left anterior insula, regions tied to feeling others' pain, lit up; it happened whether or not the person on screen knew they were embarrassing, and activity rose with the viewer's trait empathy.
- **Why people care:** everyone has a friend whose karaoke makes them watch through their fingers. The share target is that friend.
- **Format:** pastel toy kit, calm Chatterbox read.
- **Rotation:** the episode before it is Phantom Buzz (toon kit, sidewalk and classroom). The pastel episode before that, The Period Text, was a kitchen and a test room with screens. This one: a karaoke stage with a lyrics screen and a brain-scan lab with a ring scanner. Opening: your friend mid-song on stage, you at a table with your hands flying up to your face on frame one.
- **Odd physical detail:** a happy stranger walks past with toilet paper stuck to their shoe for the "no idea" line.
- **Files:** `pipeline/render_cringe.py`, `pipeline/cringe_scene.py`.

## Script: see `SCRIPT` in `pipeline/render_cringe.py`

1. Your friend is about to sing karaoke, and your brain already hurts.
2. German researchers scanned 32 people watching others embarrass themselves.
3. Two areas lit up that also fire when you watch someone get hurt.
4. It even worked when the person had no idea.
5. And the more empathy you have, the harder it hits.
6. So covering your eyes during their song is basically first aid.
7. Tag the friend who makes you watch through your fingers.

The last line runs back into the first.

## Facts and sources

| Claim in the script | Source |
|---|---|
| German researchers (Universities of Marburg and Lubeck) used fMRI on 32 participants viewing embarrassing situations | Krach, S. et al. (2011), "Your Flaws Are My Pain: Linking Empathy To Vicarious Embarrassment", PLoS ONE 6(4): e18675, https://pmc.ncbi.nlm.nih.gov/articles/PMC3076433 ; Marburg release: https://www.uni-marburg.de/archive/news/2011-4-13-du-bist-ja-so-peinlich.html ; ScienceDaily: https://www.sciencedaily.com/releases/2011/04/110413171321.htm |
| Anterior cingulate cortex and left anterior insula, regions linked to vicarious pain, were involved | Same paper (abstract). |
| Happened whether or not the protagonist was aware of the predicament | Same paper (abstract). |
| Activity in those regions correlated with trait empathy | Same paper (abstract). |

## Assumptions and jokes

- "Two areas lit up that also fire when you watch someone get hurt": the paper says these regions are known from studies of empathy for others' pain; this study did not scan people watching injuries itself.
- "Your brain already hurts" and "first aid" are jokes. The study shows overlapping brain regions, not literal pain.
- "32 people" is the fMRI group from the university release; the paper also ran larger questionnaire studies.
- The friend, the karaoke bar, the lab and the walker are fiction. The brains on screen are toys, not scan images.

## Caption

"What's the most secondhand cringe you've ever felt? Tag the friend who makes you watch through your fingers. A 2011 brain scan study found it lights up the same areas as watching someone get hurt. #cringe #friends #relatable"

## Scroll patrol

See `2026-11-07-secondhand-cringe-patrol.md`. Taken: hook "YOUR FRIEND IS / ABOUT TO SING" over a frame-one face-cover. Skipped: a real off-key singing sound (no clean recorded clip, and a synthesized one would be a steady tone).

## Status (Nov 7, 10 am make run): rendered, QA passed, queued

- Chatterbox read, every line checked by Whisper (lowest match 0.84 on line 2, heard correctly: "scanned 32 people"). No PRONOUNCE flags.
- First preview: you cropped at the left edge in the opening, the OUCH sign off frame, the scanner shot too wide for portrait, and the peek shot lost the hands. Fixed: you and the table moved in, the sign above your head, a tighter scanner shot, hands at your face in the peek.
- QA: 27.5 s, no steady tones, 4.9 MB. Mix came out at -15.0 LUFS; +2 dB through a limiter (video copied): -13.3 LUFS.
- Video: `videos/2026-11-7_Secondhand_Cringe.mp4`.
