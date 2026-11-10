# The 11:11 Wish Window

- **id:** 2026-11-09-wish-window
- **Source idea:** a timely moment (make.md "Pick the idea", rule 2). Wednesday, November 11, 2026 is the one day a year the date and the time both read 11:11, and "make a wish at 11:11" is a habit nearly everyone under 30 knows. No new trending reel from Austin was found this run: the Chrome profile was signed in to his personal account, not @overthought.daily, and the "austin thompson" thread there had nothing new after the Nov 5 entries in `ops/ideas.md`.
- **Why people care:** the 11:11 wish is shared folklore with no known origin (USC folklore archive: it "cannot be pinned down to a single origin"), and the post goes up on 11/11 itself, before 11:11 a.m., so the joke has a deadline the viewer can act on.
- **Format:** voxel "brainrot explained as science" (Nov 7 rule: remakes and timely jokes use the voxel kit). The wish is treated as a game event: windows that spawn, a drop rate, double XP, and the frequency illusion as the explanation. Calm Chatterbox read.
- **Set (new):** a voxel rooftop at night above a dark city, a giant amber digital clock billboard (7-segment digits, time row plus a date row), one blocky guy on a camping chair with his phone, stars, a moon, a shooting star on "Double XP". The episode before it in the queue (Secondhand Cringe) was the pastel toy kit in a karaoke bar, so set, kit and opening shot are all new. Opening shot: straight on the big digits reading 11:10, flipping to 11:11 on the first spoken "11:11".
- **Files:** `pipeline/render_wish.py`, `pipeline/wish_scene.py`.

## Script (see `SCRIPT` in `pipeline/render_wish.py`)

1. Today at 11:11, the wish server opens its rarest window of the year.
2. A normal day only spawns two wish windows. Two minutes out of 1,440.
3. That's a 0.14% drop rate.
4. But today the date is 11/11 too. Eight ones on one screen. Double XP.
5. If you always catch 11:11, a linguist named that in 2005. The frequency illusion.
6. Your brain saves the hits and forgets the other 1,438 minutes.
7. So the sign from the universe is mostly your screen time.
8. Set an alarm for 11:10. Lock in. The next one is a year away.

The last frame shows the clock back on 11:10, the first frame's reading, so the loop runs back into line 1.

## Facts and sources

| Claim | Source |
|---|---|
| 11:11 shows twice a day on a 12-hour clock: 2 of the day's 1,440 minutes (24 x 60), 2 / 1,440 = 0.139%, rounded to 0.14% | Arithmetic. |
| The other 1,438 minutes | 1,440 - 2. |
| On 11/11 at 11:11 a clock showing date and time has eight 1s | 11/11 plus 11:11 (the board shows exactly that). |
| "Frequency illusion" was named by a linguist in 2005 | Arnold Zwicky (Stanford) coined the term in a 2005 Language Log post; the OED cites it as the first use: https://en.wikipedia.org/wiki/Frequency_illusion , https://languagelog.ldc.upenn.edu/nll/?p=42180 |
| The brain saves the hits and forgets the misses | Zwicky describes the illusion as selective attention followed by confirmation bias (same Wikipedia article). The line is a plain-English version of that. |
| The 11:11 wish has no single known origin | USC Digital Folklore Archives, https://folklore.usc.edu/?p=60185 ; Dictionary.com, https://www.dictionary.com/browse/1111 (origin "murky", no evidence of any powers). Not claimed on screen; background for the framing. |

## Assumptions spelled out

- "Wish server", "spawns", "drop rate", "double XP" and "lock in" are the gaming joke, not claims. The only numbers on screen are the arithmetic above.
- "A year away" means the next time the date and the time are both 11:11 (November 11, 2027). The daily 11:11 still happens twice a day, which line 2 already says.
- The phone's "SCREEN TIME: yes." card is a gag about the character, with no number on it, so it presents no fake data.
- Posted on Nov 11 at 10:30 a.m. ET, before 11:11 a.m., so "Today" is true when it goes up.

## Caption

Today is 11/11. Send this to the friend who never misses an 11:11. #1111 #makeawish #11november

## Scroll patrol

See `2026-11-09-wish-window-patrol.md`.

Patrol changes: took the pull-back with a shooting star on "Double XP" (already in the shot list) and a send prompt in the caption. Skipped trimming the gaming slang for the Stranger: the slang density is what the voxel hits ran on.

## Re-voiced (Nov 10, desktop session)

Held after Austin said the cadence was off (pace swung 59% between lines, pauses mid-phrase). Re-voiced with up to 8 takes a line; Whisper writes the numbers as digits ("11 .11"), so the matcher now reads them both ways. Evened and re-timed by `voice_fix.py`: pace spread 3% at about 200 wpm (capped; it ran 219), gaps 0.40 to 0.51 s between sentences as heard. 40.9 s, -13.5 LUFS, no steady tones. Re-rendered; frames checked once a second (two captions brush the clock digits at 21 and 26 s, still readable).
