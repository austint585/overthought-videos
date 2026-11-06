# Always Cold

- **id:** 2026-11-06-always-cold
- **Source idea:** ours. A tag-a-friend joke for the week the heating fights start: everyone has the friend who is cold in every room and steals hoodies. A real 2019 study gives her a better excuse than "I'm just cold": warmer rooms raised women's math scores and barely changed men's.
- **Why people care:** the thermostat argument is in every shared apartment, office and car this month, and "give them your hoodie" is a send-to-one-person ending.
- **Format:** toon kit (toon.py), calm Chatterbox read, yellow outlined captions.
- **Rotation:** the episode before it in the queue is The Turkey Drop (pastel toy kit, peg people, Thanksgiving table, corkboard, bar chart wall). The toon episode before that, Hibernation Mode, used a quilt-wrapped friend, a bear and a living room at sunset. This one: a cold office with ceiling vents and snow falling indoors, a grumpy wall thermostat with a face, a Berlin test room with six desks and a giant thermometer, and two giant pencils as the bar chart. Opening: she is shivering under indoor snow on frame one.
- **Odd physical detail:** it snows inside the office, and the thermostat is grumpy until someone turns it up.
- **Files:** `pipeline/render_cold.py`, `pipeline/cold_scene.py`.

## Script: see `SCRIPT` in `pipeline/render_cold.py`

1. Your friend who's cold in every single room now has science.
2. In 2019, researchers in Berlin put 543 students in rooms from 61 to 91 degrees.
3. Then they gave them math tests.
4. For the women, every degree Celsius warmer meant almost 2 percent more right answers.
5. For the men, it barely moved. A small drop, too small to count.
6. So when she steals your hoodie, she's protecting her math grade.
7. Turn the heat up. It's for science.
8. Tag the friend who's always cold, and give them your hoodie.

The last line runs back into the first ("Your friend who's cold in every single room").

## Facts and sources

| Claim in the script | Source |
|---|---|
| 2019 study, Berlin, 543 students, rooms from about 61 to 91 F, math tests | Chang, T. Y. and Kajackaite, A. (2019), "Battle for the thermostat: Gender and the effect of temperature on cognitive performance", PLOS ONE 14(5): e0216362. Coverage: PBS NOVA: https://www.pbs.org/wgbh/nova/article/cold-offices-womens-productivity/ ; CNN via WTVR, May 23 2019: https://www.wtvr.com/2019/05/23/turn-up-office-thermostats-to-improve-womens-productivity-study-suggest |
| For women, each 1 C warmer meant about 1.76% more correct math answers ("almost 2 percent") | Same paper and coverage (1.76% per degree Celsius). |
| For men the change was a small drop and not statistically significant ("too small to count") | Same coverage: the men's effect ran the other way, small and not significant. |

## Assumptions and jokes

- "Protecting her math grade" and "it's for science" are the joke reading of a lab result on test answers, not a claim about anyone's grades. The study tested students in a lab, not offices or homes.
- The study also found a similar pattern on verbal tasks and none on a cognitive reflection test; the script only uses math.
- Deliberately left out: the 2015 Kingma and van Marken Lichtenbelt claim that office temperature standards were built around a middle-aged man. ASHRAE disputes it, so it is not in the script.
- The friend, the office and the snow are fiction. No real people on screen. The on-screen note during the study shots reads "Chang & Kajackaite, PLOS ONE, 2019".

## Caption

"Tag the friend who's always cold. Warmer rooms really did raise women's math scores in a 2019 study. #alwayscold #thermostat #relatable"

## Scroll patrol

See `2026-11-06-always-cold-patrol.md`. Taken: snow falling inside the office and her shivering on frame one, and the hook text names the friend ("THE ALWAYS COLD FRIEND / HAS SCIENCE NOW"). Skipped: opening on the 1.76% number (a number with no person in it).

## Status (Nov 6, 10 am make run): rendered, QA passed, queued

- Chatterbox read, every line checked by Whisper (lowest match 0.70 on line 2, which it heard as "In 2019 ... 543 students ... 61 to 91 degrees": the words are right, the score drops on digits).
- First preview had five signs outside the 9:16 frame; moved and narrowed them, and put the women's 1.76% sign beside the tall pencil instead of over its tip.
- QA: 33.9 s, no steady tones, 7.8 MB. The mix came out at -15.9 LUFS, so the audio got +2.9 dB through a limiter (video copied): -13.3 LUFS, peak -0.5 dBFS.
- Video: `videos/2026-11-6_Always_Cold.mp4`.
