# The Christmas Music Friend

- **id:** 2026-11-06-christmas-music-friend
- **Source idea:** ours. The seasonal "tag the friend" joke, following the Nov 5 daily report (Cuffing Season, our only breakout since Nov 2, was a seasonal joke with one friend to tag). Every year the internet jokes about the friend who starts Christmas music on November 1st, and this week it is in every feed: Mariah Carey posted her yearly "It's time" video at midnight on Nov 1 and the song re-entered the charts that day.
- **Why people care:** everybody has one friend who starts on Nov 1, and the post lands five days into it. Our reels with real shares are friend and dating jokes with a clear "send this to" person (Cuffing Season 64 shares, Group Chat 65, Nov 5 report).
- **Format:** pastel toy kit in bright daytime (new: every pastel episode so far was a kitchen, a bathroom or a night bedroom), toy peg people, calm Chatterbox read. Rotation: the episode before (Mercury Retrograde) was a toon joke explainer with an object cast; this one is a pastel daytime living room with peg people. No set, opening or cast repeats.
- **Cast and sets:** your friend (peg person in a Santa hat), you (on the couch), a jack-o'-lantern, a toy turkey, a smart speaker. Sets: a pastel living room (couch, coffee table, half-decorated tree, speaker on a shelf, a wall sign that counts plays), a coffee-table close-up, a dining corner with the turkey and a wall calendar.
- **Odd physical detail (style.md, Oct 29):** the friend hangs a bauble on the turkey's tail feathers, and the turkey turns its head slowly to the camera.
- **Files:** `pipeline/render_xmas.py`, `pipeline/xmas_scene.py`.

## Script: see `SCRIPT` in `pipeline/render_xmas.py`

1. Your friend has been playing Christmas music since November 1st.
2. The jack-o'-lantern is still on the table.
3. At midnight, Mariah Carey posted her yearly video: It's time.
4. By the end of that day, her song had over 700,000 plays on Spotify.
5. Your friend was a lot of them.
6. Thanksgiving is November 26th. Nobody asked the turkey.
7. From November 1st to Christmas is 54 days.
8. The song is 4 minutes long. Back to back, that's over 19,000 plays.
9. Tag your friend. They're almost at play 1,800.

## Facts and sources

| Claim in the script | Source |
|---|---|
| Mariah Carey posts a yearly video at midnight on Nov 1 ("It's time") | Star News Korea, Nov 3 2026 (AI-translated English edition): https://www.starnewskorea.com/en/music/2026/11/03/2026110301145595979 ; the yearly "It's time" post is also covered every year, e.g. Spotify newsroom: https://newsroom.spotify.com/tag/christmas-time |
| Over 700,000 plays on Spotify on Nov 1 2026 | Star News Korea above: No. 9 on Spotify's global chart with 713,000 streams on Nov 1, its best Nov 1 ever. We round down to "over 700,000". |
| Thanksgiving is November 26 | Fourth Thursday of November 2026 (Nov 1 2026 is a Sunday: Thursdays 5, 12, 19, 26). |
| Nov 1 to Christmas is 54 days | 30 days of November plus Dec 1 to Dec 25 (24) = 54. |
| The song is 4 minutes long | 4:01 on the original 1994 release: https://en.wikipedia.org/wiki/All_I_Want_for_Christmas_Is_You |
| Back to back, over 19,000 plays | 54 days x 1,440 min = 77,760 min, divided by 4.017 min = 19,359. |
| Almost at play 1,800 | Nov 1 to Nov 6 (the post day) is 5 days: 7,200 min / 4.017 = 1,792. |

## Assumptions and jokes (not claims)

- The friend, the turkey and "your friend was a lot of them" are the joke; nobody really plays one song for five days straight. The 19,359 and 1,792 are the math for that joke and read as such.
- We say nothing about Mariah Carey beyond the post and the chart number. She is not shown on screen.
- The 713,000 comes from a translated Korean report; we say "over 700,000" so a small translation error can't make the line false.

## Caption

"Tag the friend who put the tree up on November 1st. #christmasmusic #relatable #funny"

## Scroll patrol

See `2026-11-06-christmas-music-friend-patrol.md` (6 of 10, re-test 8 of 10). Taken: frame one shows the friend dancing in a Santa hat right next to the jack-o'-lantern, so the joke reads with the sound off before line 2; the hook card reads "SINCE NOV 1ST: / CHRISTMAS MUSIC"; line 4 cut from "By the end of that day, according to the charts" to the short version. Skipped: leading with the 19,000 (it is the payoff) and a question opener (nobody asks this as a question).

## Status (Nov 6, 2 am make run): rendered, QA passed, queued for Nov 6 11:30 am ET

- Narration: Chatterbox, calm (0.5), 37.7 s; Whisper matched every line.
- Eevee, 1,131 frames in 813 s.
- Preview fixes: dropped the source notes on the two counter shots (they covered the friend's face; the sign names Spotify and Nov 1), lowered the Thanksgiving sign out of the captions, centred the turkey, pressed the pillow down onto your head.
- QA: 37.7 s, no steady tones, 9.1 MB. The mix came out at -15.4 LUFS, so the audio got +2.4 dB through a limiter (video copied): -13.4 LUFS, peak -0.5 dBFS.
