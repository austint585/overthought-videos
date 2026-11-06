# Mercury Retrograde

- **id:** 2026-11-05-mercury-retrograde
- **Source idea:** ours. A friend joke people send to one person: the friend who texts the ex and blames Mercury retrograde. It is topical: Mercury is in retrograde right now (Oct 24 to Nov 13, 2026), so "Mercury is in retrograde" is all over feeds this week.
- **Why people care:** "blame it on Mercury retrograde" is a running dating meme every retrograde, and our only reels with real shares are dating and friend jokes with a clear "send this to" person (Cuffing Season 8.1K plays and 55 shares, Group Chat 65 shares, Nov 4 report).
- **Format:** toon joke explainer (toon.py), calm Chatterbox read, yellow outlined captions. Cast: objects only. Your friend is a smartphone with a face, Mercury is a small grey planet with a face. Sets: a purple bedroom at night (opening: the phone fires off a text bubble on frame one), a night sky with Mercury tracing its backwards loop, a space orbit diorama with the Sun, Mercury and Earth, a wall calendar with the three 2026 retrogrades shaded, a day counter, and a road with a FORWARD sign. Rotation: the episode before (Second Sleep) was a pastel toy second-person story; the last toon one (36 Questions) was diner condiments in a booth. No set, opening or cast repeats.
- **Files:** `pipeline/render_merc.py`, `pipeline/merc_scene.py`.

## Script: see `SCRIPT` in `pipeline/render_merc.py`

## Facts and sources

| Claim in the script | Source |
|---|---|
| Mercury is in retrograde right now | 2026 Mercury retrogrades: Feb 26 to Mar 20, Jun 29 to Jul 23, Oct 24 to Nov 13. Old Farmer's Almanac: https://www.almanac.com/content/mercury-retrograde-dates , CHANI 2026 key dates: https://chani.com/this-year/key-dates/2026-astrological-key-dates-mercury-retrogrades |
| It looks like it moves backwards across the sky, and it is an illusion | NASA Space Place, "What is retrograde motion?": https://spaceplace.nasa.gov/retrograde/en/ (planets only appear to move backward because of how Earth and the other planet pass each other). Almanac page above says the same. |
| When it laps us it looks like it goes back | NASA Space Place above: an inner planet looks like it backs up while it overtakes Earth on the inside track. |
| This year that is three times, 66 days in total | Dates above: Feb 26 to Mar 20 (22 days), Jun 29 to Jul 23 (24), Oct 24 to Nov 13 (20). 22 + 24 + 20 = 66. |
| The other 299 days | 365 minus 66. |

## Assumptions and jokes (not claims)

- The friend, the ex and the texts are fiction. "Your friend texted the ex anyway" is the joke, not a claim about anyone.
- We say nothing about astrology being true or false beyond the astronomy: the backwards motion is apparent, which NASA states.
- Day counts use the start and end dates as listed by the Almanac; sources round the length slightly differently (a day either way does not change the joke).

## Caption

"Tag the friend who blames Mercury for every text. #mercuryretrograde #relatable #funny"

## Scroll patrol

See `2026-11-05-mercury-retrograde-patrol.md` (6 of 10, re-test 9 of 10). Taken: line 3 cut to one short sentence (the 88 days dropped), two camera angles on the orbit so no shot runs past about 4 s, and a caption that no longer gives away the 299 punchline. Skipped: the new first lines that lead with 66 days, because they spoil the payoff; the original line 1 is short and readable on frame one.

## Status (Nov 5, 8 pm make run): rendered, QA passed, queued

- Narration: Chatterbox, calm (0.5), 27.5 s; Whisper matched every line (no drift warnings).
- Eevee, 825 frames. Blender crashed once at frame 704 (access violation); the cached frames resumed cleanly.
- Preview fixes: dropped the bed signs (the hook text covered them), made the second angles a push-in with the sign hidden, spaced the sets 40 m apart (shadows from the neighbouring sets fell on the walls), moved the 66 DAYS sign off Feb and Mar, pulled the cast in from the frame edges, and had Mercury roll toward the camera on the road instead of into the wall.
- QA: 27.5 s, no steady tones, 6.6 MB. The mix came out at -17.9 LUFS, so the final audio got +4.9 dB through a limiter (video stream copied): -13.8 LUFS, peak -0.7 dBFS.
