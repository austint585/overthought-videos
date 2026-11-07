# Phantom Buzz

- **id:** 2026-11-07-phantom-buzz
- **Source idea:** ours. A tag-a-friend joke on phantom phone vibrations: you feel your phone buzz, nobody texted you. Drouin, Kaiser and Miller (Computers in Human Behavior, 2012) asked 290 undergraduates: 89% had felt phantom vibrations, usually about once every two weeks, and few found them bothersome.
- **Why people care:** almost everyone has slapped their pocket for a text that never came, and "the friend who checks their phone every five seconds" is one specific person in most group chats. The daily report (Nov 6) says shorter reels (27 to 35 s) hold more of the audience, so this one is about 25 s.
- **Format:** toon kit (toon.py), calm Chatterbox read, yellow outlined captions.
- **Rotation:** the episode before it is The Period Text (pastel toy kit). The toon episode before that, The Yawn Test, was a living room and bleachers. This one: a brick sidewalk at dusk and a tiered classroom with a calendar board. Opening: you with your hand on a buzzing pocket on frame one, buzz lines already flickering.
- **Odd physical detail:** in the classroom nine of ten students jiggle with buzz lines and one sits still (an illustration of "nine in ten"; the real figure, 89%, is on the sign).
- **Files:** `pipeline/render_buzz.py`, `pipeline/buzz_scene.py`.

## Script: see `SCRIPT` in `pipeline/render_buzz.py`

1. Your phone just buzzed in your pocket. Nobody texted you.
2. Researchers asked 290 college students about this exact feeling.
3. 89 percent had felt a buzz that never happened.
4. Most of them about once every two weeks.
5. And almost nobody was bothered by it.
6. So your pocket lies to you, and you just let it.
7. Tag the friend who checks their phone every five seconds.

The last line runs back into the first.

## Facts and sources

| Claim in the script | Source |
|---|---|
| 290 undergraduates surveyed; 89% had experienced phantom vibrations | Drouin, M., Kaiser, D. H. and Miller, D. A. (2012), "Phantom vibrations among undergraduates: Prevalence and associated psychological characteristics", Computers in Human Behavior 28(4): 1490-1496. Abstract summarised in https://en.wikipedia.org/wiki/Phantom_vibration_syndrome and https://www.psychologytoday.com/us/blog/rewired-the-psychology-technology/201305/phantom-pocket-vibration-syndrome |
| Typically about once every two weeks | Same abstract. |
| Few found them bothersome | Same abstract ("few found them bothersome"); over 90% rated them not or only a little bothersome per the critical review at https://www.flowjournal.org/2013/01/banishing-phantoms-from-the-skin/ |

## Assumptions and jokes

- "Most of them about once every two weeks" stands for the abstract's "typically". "Almost nobody was bothered" stands for "few found them bothersome".
- The sample is one university, so 89% describes those students, not everyone (other studies report 30 to 89%). The script says "college students" and the source note stays on screen through the facts.
- "Your pocket lies to you" is a joke: the feeling is a false alarm from your own nervous system, not the phone.
- The person, the street and the classroom are fiction. Nine of ten students buzzing is an illustration.

## Caption

"Be honest, how many times today? Tag the friend who checks their phone every five seconds. 89% of 290 college students had felt a buzz that never happened. #phone #relatable #friends"

The first line is a question people can answer in the comments (the Nov 6 report: comments are still at zero).

## Scroll patrol

See `2026-11-07-phantom-buzz-patrol.md`. Taken: hook text "YOUR PHONE / DIDN'T BUZZ" and the buzz already on frame one. Skipped: a louder vibration sound on frame one (kept under the voice, and long buzzes read as a steady tone in qa_audio).

## Status (Nov 7, 10 am make run): rendered, QA passed, queued

- Chatterbox read, every line checked by Whisper (lowest match 0.78 on line 3, heard correctly as "89 % had felt a buzz that never happened"). No PRONOUNCE flags.
- First preview: the "0 NEW MESSAGES" sign cropped at the frame edge, the 89% shot too tight to show its sign, the close shot too close. Fixed: "0 NEW TEXTS" on a smaller sign, wider shots, a bigger 89% sign, buzz lines around the students' heads.
- QA: 24.3 s, no steady tones, 7 MB. Mix came out at -15.6 LUFS; +2.6 dB through a limiter (video copied): -13.5 LUFS.
- Video: `videos/2026-11-7_Phantom_Buzz.mp4`.
