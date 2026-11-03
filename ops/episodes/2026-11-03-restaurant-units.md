# Restaurant units

- **id:** 2026-11-03-restaurant-units
- **Source idea:** ours. A relatable joke people send to one friend: the one who "only had two glasses". A real 2008 study bought bar and restaurant drinks and measured the alcohol in them; restaurant pours run well over a standard drink.
- **Format:** toon joke explainer, calm Chatterbox read (exaggeration 0.5), yellow outlined captions. Cast: a wine glass with a face and stubby limbs (your friend). New sets: a bar counter with two glasses (opening), a lab with shelves of drinks and a meter, a giant bottle pouring past a ONE STANDARD DRINK line, a row of ten glasses all over the line, a martini on a pedestal, two glasses on a scale that reads 2.9, a gold pedestal with shades. Rotation: the episode before is the pastel toy friendship one (two mugs at a cafe); the last toon one (Nobody Answered) was phones in a group chat, and nothing here repeats those sets or openings.
- **Files:** `pipeline/render_wine.py`, `pipeline/wine_scene.py`.

## Script: see `SCRIPT` in `pipeline/render_wine.py`

## Facts and sources

All from Kerr, Patterson, Koenen and Greenfield, "Alcohol content variation of bar and restaurant drinks in Northern California", Alcoholism: Clinical and Experimental Research 32(9):1623-1629 (2008). Full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC2574782

| Claim in the script | Where in the paper |
|---|---|
| Researchers bought 480 drinks at bars and restaurants in Northern California and measured the alcohol | "A total of 480 drinks were purchased and measured" (10 counties). 337 samples were lab-analyzed for strength; the rest were measured for volume. |
| The average glass of wine had 43% more alcohol than a standard drink | Wine mean 0.86 oz ethanol, "43.3% larger than the standard drink" (US standard 0.6 oz, 14 g). |
| 98% of the glasses (of wine) were over one drink | Results (Figure 1 paragraph): wine alcohol content was "almost always (98%) larger than the standard drink". |
| The average martini was 1.6 drinks | Martinis contain "160% of the alcohol in a standard drink on average". |
| Her two glasses were about three drinks | Arithmetic: 2 x 1.43 = 2.87. |

## Assumptions and jokes (not claims)

- "Two glasses" is the friend's claim; we assume both are average restaurant wine pours from the study.
- "Restaurant units" and "The glasses had three" are jokes.
- The scale reading "2.9 DRINKS" is the arithmetic above; the lab meter's numbers are decoration, not data.
- The study is from one region (Northern California, 2008); the source note on screen names it.

## Caption

"Send this to the friend who only had two glasses. #wine #science #relatable"

## Render and QA (Nov 3, evening run)

- Video: `videos/2026-11-3_She_Only_Had_Two_Glasses.mp4`, 31.0 s, 1080x1920 at 30 fps, 8.3 MB.
- Audio: -13.7 LUFS after loudnorm (the mix came out at -15.1), peak -0.9 dBFS, `qa_audio.py`: no steady tones.
- Moved the friend into frame in the lab shot (she stood off the left edge).
- Blender crashed out of commit memory on frame 2 of a single full render (other apps held most of the 30 GB commit limit), so frames were rendered in 60-frame chunks, each in a fresh Blender, then encoded. One earlier preview batch came out with four all-black frames that rendered fine on a rerun; the full render was scanned and has no black or broken frames.
