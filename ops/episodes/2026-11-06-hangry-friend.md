# The Hangry Friend

- **id:** 2026-11-06-hangry-friend
- **Source idea:** ours. A tag-a-friend joke: everyone has the friend who turns on you twenty minutes before dinner. A 2018 lab study (MacCormack and Lindquist, Emotion) made it official, with a rigged computer crash and a researcher who blamed the students for it. The twist that makes it useful: hungry students who first wrote about their feelings were fine.
- **Why people care:** "hangry" is in the dictionary and in every couple's and roommate's life; the ending ("hand them a snack and ask how they feel") is a send-to-one-person line.
- **Format:** pastel toy kit, toy peg people, calm Chatterbox read.
- **Rotation:** the episode before it is Caffeine Doesn't Affect Me (toon kit, night kitchen, sleep lab, bedroom). The pastel episode before that, The Barista Crush, used a coffee shop, a lecture hall and a rating board. This one: a living room couch at sunset with a storm cloud over the friend, a computer lab with a rigged monitor that throws an error, a researcher in a lab coat, and a split stage of hungry and full students. Opening: the friend on the couch with a little storm cloud raining on them and their stomach visibly rumbling on frame one.
- **Odd physical detail:** the storm cloud over the friend grows a tiny lightning bolt, and turns into a sun when the snack lands.
- **Files:** `pipeline/render_hangry.py`, `pipeline/hangry_scene.py`.

## Script: see `SCRIPT` in `pipeline/render_hangry.py`

1. Your friend who gets mean right before dinner has a study now.
2. In 2018, psychologists had over 200 students skip food or eat first.
3. Then a long, boring computer task, rigged to crash right before the end.
4. A researcher walked in and blamed them for it.
5. The hungry ones felt more stressed and hateful, and called the researcher harsh.
6. But hungry students who first wrote about their feelings were fine.
7. So don't argue with them. Hand them a snack and ask how they feel.
8. Tag the friend who gets mean right before dinner.

The last line runs back into the first.

## Facts and sources

| Claim in the script | Source |
|---|---|
| 2018 study, over 200 university students, asked to fast or eat beforehand | MacCormack, J. K. and Lindquist, K. A. (2018), "Feeling hangry? When hunger is conceptualized as emotion", Emotion 19(2). APA press release, June 2018: https://www.apa.org/news/press/releases/2018/06/hungry ; reprint: https://neurosciencenews.com/hunger-angry-hangry-9308/ ; UNC: https://collegearchive.unc.edu/?p=25108 |
| A tedious computer task programmed to crash just before it could be completed; a researcher came in and blamed the student | Same release. |
| Hungry students (not focused on their emotions) reported more unpleasant emotions, "stressed and hateful", and thought the researcher was "more judgmental or harsh" | Same release. |
| Students who first did a writing exercise focusing on their emotions did not show these shifts, even when hungry | Same release ("Participants who spent time thinking about their emotions, even when hungry, did not report these shifts"). |

## Assumptions and jokes

- "Skip food" stands for "asked to fast"; the release gives no number of hours, so the script gives none.
- "Ask how they feel" is the everyday version of the study's writing exercise about emotions, not a tested intervention. The snack is the joke; the study did not feed anyone.
- The friend, the couch and the storm cloud are fiction. No real people on screen. On-screen note during the study: "MacCormack & Lindquist, Emotion, 2018".

## Caption

"Tag the friend who gets mean right before dinner. In a 2018 study, hungry students judged people more harshly, unless they'd stopped to think about how they felt. #hangry #relatable #food"

## Scroll patrol

See `2026-11-06-hangry-friend-patrol.md`.

## Status (Nov 6, 2 pm make run): rendered, QA passed, queued

- Chatterbox read, every line checked by Whisper (lowest match 0.90 on line 2, heard correctly). No PRONOUNCE flags.
- First preview: the lab wide was too far away, the group signs blocked the close-ups, the researcher blocked the "hungry" shot and the notebooks covered faces. Fixed. After the full render the "hungry" shot still cut off the STRESSED bubble and the HARSH sign at the frame edges; those 157 frames were re-rendered twice until both sat inside the frame.
- QA: 33.0 s, no steady tones, 6.8 MB. Mix came out at -16.9 LUFS; +4 dB through a limiter (video copied): -13.4 LUFS, peak -0.4 dBFS.
- Video: `videos/2026-11-6_The_Hangry_Friend.mp4`.
