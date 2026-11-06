# Caffeine Doesn't Affect Me

- **id:** 2026-11-06-caffeine-immune
- **Source idea:** ours. A tag-a-friend identity joke: everyone has the friend who drinks coffee or an energy drink at 9 p.m. and swears it does nothing. A real 2013 sleep study backs them up in the worst way: caffeine six hours before bed cost people more than an hour of sleep, and their own sleep diaries said they were fine. So the friend is right that they can't feel it.
- **Why people care:** "caffeine doesn't affect me" is a stock line in every dorm, office and group chat, and the payoff ("they can't feel it") is a send-to-one-person line.
- **Format:** toon kit (toon.py), calm Chatterbox read, yellow outlined captions.
- **Rotation:** the episode before it is The Barista Crush (pastel toy kit, coffee shop, lecture hall, rating board). The toon episode before that, Always Cold, was a cold office, a Berlin test room and giant pencils. This one: a night kitchen with a grumpy giant coffee mug mascot and a wall clock at 9 p.m., a sleep lab bed hooked to a monitor box, a stack of four mugs as "400 mg", a sleep bar that loses a chunk, and a sleep diary page. Opening: the friend chugging from the giant mug under the 9 p.m. clock on frame one. The coffee shop of the episode before is not reused (different kit, kitchen at night, no barista).
- **Odd physical detail:** the friend's eyes stay wide open and twitch the whole time, even in the bed.
- **Files:** `pipeline/render_caff.py`, `pipeline/caff_scene.py`.

## Script: see `SCRIPT` in `pipeline/render_caff.py`

1. Your friend who drinks coffee at 9 at night says caffeine doesn't affect them.
2. In 2013, sleep scientists tested that.
3. People took 400 milligrams of caffeine, about four cups of coffee, six hours before bed.
4. A monitor tracked their sleep at home.
5. They lost more than an hour of sleep.
6. Then they wrote in their sleep diaries that they slept fine.
7. So your friend is right. They can't feel it.
8. Tag the friend who says caffeine doesn't affect them.

The last line runs back into the first.

## Facts and sources

| Claim in the script | Source |
|---|---|
| 2013 study: 400 mg caffeine taken 0, 3 or 6 hours before bed, sleep tracked with an in-home monitor and a sleep diary | Drake, C., Roehrs, T., Shambroom, J. and Roth, T. (2013), "Caffeine effects on sleep taken 0, 3, or 6 hours before going to bed", Journal of Clinical Sleep Medicine 9(11): 1195 to 1200: https://pmc.ncbi.nlm.nih.gov/articles/PMC3805807/ ; AASM press release, Nov 14 2013: https://aasm.org/late-afternoon-and-early-evening-caffeine-can-disrupt-sleep-at-night/ |
| Six hours before bed, objectively measured sleep dropped by more than an hour | Same paper and press release ("reduced total sleep time by more than one hour"). |
| Their own reports suggested they did not notice | Same press release: "subjective reports suggest that participants were unaware of this sleep disturbance." The paper found the diary measures changed less than the monitor did at 6 hours. |
| 400 mg is about four cups of coffee | FDA, "Spilling the Beans: How Much Caffeine Is Too Much?": https://www.fda.gov/consumers/consumer-updates/spilling-beans-how-much-caffeine-too-much ("400 milligrams a day, about four or five cups of coffee"). |

## Assumptions and jokes

- The study had 12 healthy adults, a small sample. The script says "people", not a number, and the on-screen note reads "Drake et al., J. Clin. Sleep Med., 2013 (12 adults)".
- "Wrote in their sleep diaries that they slept fine" is the joke reading of "subjective reports suggest participants were unaware of the disturbance"; the diaries did not literally say "fine". On screen the diary reads "SLEPT OK?" with a check, a cartoon.
- The 9 p.m. coffee is the friend's habit, not the study's timing (the study's 6-hour dose was about 5 p.m. for an 11 p.m. bedtime).
- The friend, kitchen and mug mascot are fiction. No real people on screen.

## Caption

"Tag the friend who says caffeine doesn't affect them. In a 2013 study, coffee six hours before bed cost people an hour of sleep and they didn't notice. #caffeine #coffee #relatable"

## Scroll patrol

See `2026-11-06-caffeine-immune-patrol.md`.

## Status (Nov 6, 2 pm make run): rendered, QA passed, queued

- Chatterbox read, every line checked by Whisper (lowest match 0.80 on line 2, heard correctly). No PRONOUNCE flags. Line 1 says "9 at night" instead of "9 p.m." so the voice can't misread the abbreviation.
- On-screen, the sleep diary reads "SLEPT OK? YES!" (a cartoon of the participants' own reports).
- First preview: the friend's cup was missing, the giant mug, the 4th mug and three signs were cut off at the frame edges, and two signs sat under the hook or captions. All fixed and re-previewed.
- QA: 30.4 s, no steady tones, 7.4 MB. Mix came out at -15.3 LUFS; +2.4 dB through a limiter (video copied).
- Video: `videos/2026-11-6_Caffeine_Doesnt_Affect_Me.mp4`.
