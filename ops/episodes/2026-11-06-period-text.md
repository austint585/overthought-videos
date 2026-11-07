# The Period Text

- **id:** 2026-11-06-period-text
- **Source idea:** ours. A tag-a-friend joke: everyone has the friend who answers "Okay." with a period and makes you wonder what you did. A 2015 Binghamton study (Gunraj, Klin and colleagues, Computers in Human Behavior) found one-word text replies ending in a period were rated less sincere than the same replies with no punctuation, and the period made no difference on handwritten notes.
- **Why people care:** the "ok." text is a universal small panic, and "tag the friend who texts okay with a period" names one person.
- **Format:** pastel toy kit, toy peg people, calm Chatterbox read.
- **Rotation:** the episode before it is The Yawn Test (toon kit, movie night, bleachers, a timing board). The pastel episode before that, The Friend Who Can't Pick A Restaurant, was a sidewalk and a grocery store. This one: a kitchen counter in the morning where you hold your phone under a giant floating chat, and a psychology test room with a big text screen and a handwritten note on an easel, students on stools and a SINCERE meter. No sidewalk, no store. Opening: a giant "Okay." bubble with its period glowing red lands over your head on frame one, and you flinch.
- **Odd physical detail:** the period is a heavy red ball that drops out of the bubble and rolls across the counter.
- **Files:** `pipeline/render_period.py`, `pipeline/period_scene.py`.

## Script: see `SCRIPT` in `pipeline/render_period.py`

1. Your friend replied okay, with a period. You felt that.
2. In 2015, psychologists showed 126 students short text exchanges.
3. Someone asks a question. The answer is one word: okay, sure, yeah, yup.
4. Half the replies ended with a period. Half had nothing.
5. Replies with a period were rated less sincere.
6. On handwritten notes, the period made no difference.
7. So you weren't imagining it. That dot meant something.
8. Tag the friend who texts okay with a period.

The last line runs back into the first.

## Facts and sources

| Claim in the script | Source |
|---|---|
| 2015 study, 126 undergraduates (Binghamton University) read short exchanges | Gunraj, D. N., Drumm-Hewitt, A. M., Dashow, E. M., Upadhyay, S. S. N. and Klin, C. M. (2016), "Texting insincerely: The role of the period in text messaging", Computers in Human Behavior 55, 1067 to 1075 (online December 2015). Press release: https://www.eurekalert.org/news-releases/570442 ; ScienceDaily: https://sciencedaily.com/releases/2015/12/151208094229.htm ; Phys.org: https://phys.org/news/2015-12-text-messages-period-sincere.html |
| A statement and a question, answered with one word: Okay, Sure, Yeah, Yup | Same release. |
| Two versions: the reply ended with a period, or with no punctuation | Same release. |
| Replies with a period were rated less sincere | Same release. |
| No such difference on handwritten notes | Same release. |

## Assumptions and jokes

- "Half the replies" means each exchange had two versions, one with and one without the period; the release does not say each student saw exactly half, so the line describes the replies, not the students.
- "That dot meant something" is the joke: the study measured how sincere readers rated the reply, not what the sender meant. The on-screen note reads "Gunraj et al., Computers in Human Behavior, 2016".
- The friend, the kitchen and the test room are fiction. No real people on screen. No real messaging app's look: plain rounded bubbles.

## Caption

"Tag the friend who texts okay with a period. In a 2015 study, one-word texts ending in a period were rated less sincere. On handwritten notes it made no difference. #texting #relatable #psychology"

## Scroll patrol

See `2026-11-06-period-text-patrol.md`. Taken: the red period dropping and you flinching on frame one, and hook text "OKAY. / WITH A PERIOD" so the joke reads with the sound off. Skipped: opening on the study result ("less sincere"), because the friend's text is what gets it sent.

## Status (Nov 6, 6 pm make run): rendered, QA passed, queued

- Chatterbox read, every line checked by Whisper (lowest match 0.67 on line 2, heard correctly: "In 2015, psychologists showed 126 students short text exchanges"; the score is low only because Whisper writes the numbers as digits). No PRONOUNCE flags.
- First preview: white text on the light blue question bubbles was unreadable, the split and meter shots cropped the screens, the handwritten "Okay" turned into the paper, the last kitchen shot missed the rolling dot, and the SAME sign hit the caption. Fixed: darker blue bubbles, screens moved together with closer cameras, a big "RATED LESS SINCERE" sign, the note text tilted in its own plane, a reframed last shot, and SAME as a stamp between the two notes.
- QA: 32.0 s, no steady tones, 5.2 MB. Mix came out at -16.5 LUFS; +3.3 dB through a limiter (video copied): -13.5 LUFS.
- Video: `videos/2026-11-6_The_Period_Text.mp4`.
