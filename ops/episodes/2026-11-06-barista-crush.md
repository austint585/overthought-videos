# The Barista Crush

- **id:** 2026-11-06-barista-crush
- **Source idea:** ours. A tag-a-friend dating joke: everyone has the friend in love with a barista (or gym regular, or bus stranger) they have never spoken to. A real 1992 classroom study explains it: four women sat in a big lecture 0, 5, 10 or 15 times without talking to anyone, and the class liked the one who came most. The mere exposure effect, as a roast.
- **Why people care:** "my barista crush" is a running joke in every coffee order and every group chat, and the payoff ("their great love story is mostly attendance") is a send-to-one-person line.
- **Format:** pastel toy kit, toy peg people, calm Chatterbox read.
- **Rotation:** the episode before it in the queue is Always Cold (toon kit, cold office, indoor snow). The pastel episode before that, The Turkey Drop, used a Thanksgiving table, a corkboard and a bar chart wall. This one: a coffee shop counter with a growing tower of paper cups, a tiered lecture hall full of peg students, and a rating board. Opening: a latte slides across the counter while hearts pop over the friend's head on frame one.
- **Odd physical detail:** a tower of the friend's empty cups grows beside them all video, and the woman who came 15 times gets a little "PERFECT ATTENDANCE" ribbon.
- **Files:** `pipeline/render_barista.py`, `pipeline/barista_scene.py`.

## Script: see `SCRIPT` in `pipeline/render_barista.py`

1. Your friend who's in love with the barista has never talked to them.
2. Science says that's the whole point.
3. In 1992, psychologists sent four women into a lecture of over 100 students.
4. One came zero times. One came five. One came ten. One came fifteen.
5. They just sat there. They never spoke to anyone.
6. At the end, the class rated the one who came fifteen times the most attractive.
7. Barely anyone remembered seeing her. They just liked her more.
8. So your friend's great love story is mostly attendance.
9. Tag your friend who's in love with the barista.

The last line runs back into the first.

## Facts and sources

| Claim in the script | Source |
|---|---|
| 1992 study, four women posing as students attended a large lecture 0, 5, 10 or 15 times and did not interact with anyone | Moreland, R. L. and Beach, S. R. (1992), "Exposure effects in the classroom: The development of affinity among students", Journal of Experimental Social Psychology 28, 255 to 276. Summaries: Simply Psychology, "Mere Exposure Effect": https://www.simplypsychology.org/mere-exposure-effect.html ; Stangor, Principles of Social Psychology (open textbook): https://www.opentextbooks.org.hk/node/16741 |
| The lecture had over 100 students (about 130 took part in the ratings) | Same summaries ("a large lecture class of over 100 students"; 130 undergraduates). |
| The class rated the women who came more often as more attractive; 15 visits rated highest | Same summaries; mean attractiveness about 3.62 (0 visits), 3.88 (5), 4.25 (10), 4.38 (15) on a 1 to 7 scale: Save My Exams IB revision note: https://www.savemyexams.com/dp/psychology/ib/17/sl/revision-notes/human-relationships/formation-of-personal-relationships/three-key-studies-of-sociocultural-theories-of-attraction- |
| Barely anyone remembered seeing her | Same summaries: attendance did not change how well students recognized the women, but it did change how much they liked them. Recognition was low overall. |

## Assumptions and jokes

- The rating board bars use the reported means on a 1 to 7 scale, drawn from the bottom of the scale (1), so the differences look as big as they are and no bigger. The note on screen reads "Ratings from Moreland & Beach, 1992". The means come from secondary summaries, not the paper itself.
- "Barely anyone remembered seeing her" is the plain reading of "low recognition that did not rise with visits"; the script does not give a number.
- The barista, the friend, the visit counter (214) and the cup tower are fiction and clearly a joke. No real people on screen.
- "Mostly attendance" is the joke reading of a lab result about liking strangers, not a claim about any real relationship.
- Avoided "that's not love, that's X" (Austin's banned construction).

## Caption

"Tag your friend who's in love with the barista. A 1992 study found people liked a stranger more just for showing up to class more. #crush #barista #relatable"

## Scroll patrol

See `2026-11-06-barista-crush-patrol.md`. Taken: motion on frame one (latte sliding, hearts popping), hook text naming the friend ("IN LOVE WITH THE BARISTA / NEVER SPOKE ONCE"), the "WORDS SAID: 0" sign visible from frame one, a cut inside line 4 for each number. Skipped: opening on the study (no friend to tag).

## Status (Nov 6, 2 pm make run): rendered, QA passed, queued

- Chatterbox read, every line checked by Whisper (lowest match 0.76 on line 3, heard correctly: the score drops on digits). No PRONOUNCE flags.
- First preview: the hook text ran off the frame ("IN LOVE WITH THE BARISTA"), so it became "THE BARISTA CRUSH / NEVER SPOKE ONCE"; the cup close-up was too tight, the lectern blocked the four-women shot and a front-row head blocked the "sit" shot. All fixed and re-previewed.
- QA: 35.9 s, no steady tones, 7.2 MB. Mix came out at -14.2 LUFS; +1.3 dB through a limiter (video copied): -13.0 LUFS, peak -0.4 dBFS.
- Video: `videos/2026-11-6_Barista_Crush.mp4`.
