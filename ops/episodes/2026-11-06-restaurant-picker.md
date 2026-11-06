# The Friend Who Can't Pick A Restaurant

- **id:** 2026-11-06-restaurant-picker
- **Source idea:** ours. A tag-a-friend joke: everyone has the friend who scrolls restaurants for forty minutes and picks nothing. The famous jam study (Iyengar and Lepper, 2000) is the excuse: at a grocery store tasting booth, 24 jams pulled more people in, but six jams sold far more. Honest twist: later studies found the effect is often small, so the joke is that your friend is the case where it shows up.
- **Why people care:** "where do you want to eat?" "I don't care, you pick" is a universal fight; "send them two" is a usable fix and a send-to-one-person line.
- **Format:** pastel toy kit, toy peg people, calm Chatterbox read.
- **Rotation:** the episode before it is The NASA Nap (toon kit, library, cockpit, movie screen). The pastel episode before that, The Hangry Friend, was a living room couch and a computer lab. This one: a sidewalk at dusk outside a row of three toy restaurants with striped awnings, and a grocery store with two jam tables (24 jars and 6 jars). No couch, no lab. Opening: the friend on the sidewalk, phone in hand, with a ring of tiny menu cards spinning around their head and a sign counting "DECIDING 41 MIN" on frame one.
- **Odd physical detail:** the ring of menu cards around the friend's head spins faster the longer they decide, and collapses to two cards at the end.
- **Files:** `pipeline/render_picker.py`, `pipeline/picker_scene.py`.

## Script: see `SCRIPT` in `pipeline/render_picker.py`

1. Your friend who can't pick a restaurant has a jam study.
2. In 2000, researchers set up a jam tasting booth in a California grocery store.
3. Sometimes the table had 24 jams. Other times, only six.
4. The big table pulled more people in. 60 percent stopped, versus 40.
5. But only 3 percent of those shoppers bought a jar. With six jams, 30 percent did.
6. Later studies say it doesn't always happen. Your friend is the case where it does.
7. So don't send them twenty-four places. Send them two.
8. Tag the friend who can't pick a restaurant.

The last line runs back into the first.

## Facts and sources

| Claim in the script | Source |
|---|---|
| 2000 study, a jam tasting booth in an upscale California grocery store (Draeger's, Menlo Park) | Iyengar, S. S. and Lepper, M. R. (2000), "When choice is demotivating: Can one desire too much of a good thing?", Journal of Personality and Social Psychology 79(6), 995 to 1006. Copy: https://www.scribd.com/document/452274609/Iyengar-Lepper-2000-pdf ; Stanford Daily summary: https://stanforddaily.com/2020/02/03/choice-paralysis-and-the-fear-of-growing-up/ |
| The display alternated between 24 jams and 6 jams | Same paper. |
| 60% of passing shoppers stopped at the 24-jam table, 40% at the 6-jam table | Same paper; summary: https://medium.com/@FlorentGeerts/the-jam-experiment-how-choice-overloads-makes-consumers-buy-less-d610f8c37b9b ; https://econsultancy.com/want-more-sales-give-consumers-fewer-options/ |
| 3% of those who stopped bought a jar at 24 jams, 30% at 6 jams | Same paper and summaries. |
| Later studies: the effect is often small or absent | Scheibehenne, Greifeneder and Todd (2010), "Can there ever be too many options? A meta-analytic review of choice overload", Journal of Consumer Research 37(3), 409 to 425: 50 experiments, mean effect near zero with large variation. https://ideas.repec.org/a/oup/jconrs/v37y2010i3p409-425.html ; Psychology Today: https://www.psychologytoday.com/us/blog/pop-psych/201602/is-choice-overload-real-thing |

## Assumptions and jokes

- "Sometimes / other times": the paper alternated the two displays over the day; the script gives no hours.
- "Those shoppers" means shoppers who stopped at the booth (the 3% and 30% are of people who stopped), which the line says.
- "Send them two" is our joke and everyday advice, not something the study tested. The "41 MIN" counter, the friend and the restaurants are fiction. No real people or brands on screen; jam labels are plain colors.
- On-screen note during the study shots: "Iyengar & Lepper, 2000". During line 6: "Scheibehenne et al., 2010: effect often small".

## Caption

"Tag the friend who can't pick a restaurant. In the famous jam study, 30% bought a jar when there were 6 jams and 3% when there were 24. #relatable #psychology #food"

## Scroll patrol

See `2026-11-06-restaurant-picker-patrol.md`. Taken: the menu-card ring spinning and the counter running on frame one (a still sidewalk would lose the Thumb), and the hook text naming the friend. Skipped: a payoff-first opening ("3% vs 30%"), because without the friend it reads as a marketing tip, and the friend is what gets it sent.

## Status (Nov 6, 6 pm make run): rendered, QA passed, queued

- Chatterbox read, every line checked by Whisper (lowest match 0.84 on line 7, heard correctly: "24 places, send them 2"). No PRONOUNCE flags.
- First preview: the street and store shots were framed too wide (the friend and the jars were tiny), the DECIDING sign sat at the frame edge, and the 24 JAMS sign sat under the caption in the close-up. Fixed by moving the cameras in, the tables closer together and the sign. The two-card payoff only showed for half a second, so it now holds into the last line before the loop.
- QA: 36.8 s, no steady tones, 9.9 MB. Mix came out at -16.3 LUFS; +3.3 dB through a limiter (video copied): -13.5 LUFS.
- Video: `videos/2026-11-6_The_Friend_Who_Cant_Pick_A_Restaurant.mp4`.
