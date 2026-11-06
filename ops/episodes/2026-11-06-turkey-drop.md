# The Turkey Drop

- **id:** 2026-11-06-turkey-drop
- **Source idea:** ours. A seasonal tag-a-friend dating joke, the Cuffing Season setup the Nov 5 daily report suggests. "The turkey drop" is real college slang for the Thanksgiving breakup: a first-year goes home for the break and ends it with the high school sweetheart. Thanksgiving 2026 is Thursday, Nov 26, about three weeks after this posts.
- **Why people care:** almost everyone knows one friend still in a long distance high school relationship, and the phrase gets a wave of campus-paper and magazine coverage every November. The turn (the safest day for that couple is Christmas, if they live through Thanksgiving) comes from a real chart.
- **Format:** pastel toy kit at dusk, toy peg people, calm Chatterbox read.
- **Rotation:** the episode before it in the queue is Hibernation Mode (toon kit, quilt friend and a bear). The pastel episode before that, Singles' Day, was a night apartment, a 1993 dorm and a wedding hall. This one is new on every count: a Thanksgiving table at dusk with a roast turkey, a corkboard of clippings, a giant breakup bar chart wall. Opening: a turkey drops onto the platter on frame one (the title, literally).
- **Odd physical detail:** the turkey hops on the platter when the narrator says "turkey drop", and a tiny Christmas tree pops up on the almost empty Christmas Day bar.
- **Files:** `pipeline/render_turkey.py`, `pipeline/turkey_scene.py`.

## Script: see `SCRIPT` in `pipeline/render_turkey.py`

1. Your friend who's still with their high school sweetheart has until Thanksgiving.
2. College kids have a name for it. The turkey drop.
3. A freshman goes home for the break, sits across from the hometown sweetheart, and ends it before the pie.
4. Campus papers run survival guides for it every November.
5. In 2008, two designers charted 10,000 Facebook breakup posts.
6. The second biggest spike of the year is the two weeks before Christmas.
7. And Christmas Day itself is almost empty.
8. So the relationship is safest on Christmas. It just has to survive Thanksgiving first.
9. Tag your friend still FaceTiming their high school sweetheart. Thanksgiving is the 26th.

The last line runs back into the first ("Your friend who's still with their high school sweetheart").

## Facts and sources

| Claim in the script | Source |
|---|---|
| "Turkey drop" is college slang for first-years breaking up with high school partners over Thanksgiving | Psychology Today, "Say Goodbye: It's Turkey Drop Time", Nov 2018: https://www.psychologytoday.com/us/blog/meet-catch-and-keep/201811/say-goodbye-its-turkey-drop-time ; Yahoo/Cosmopolitan explainer: https://ca.news.yahoo.com/why-everyone-feels-breaking-around-221500669.html |
| Campus papers run guides for it every November | Penn State Collegian, "The dreaded turkey drop: how to deal with a breakup over the holidays": https://www.psucollegian.com/news/campus/the-dreaded-turkey-drop-how-to-deal-with-a-breakup-over-the-holidays/article_cbfd7d8a-d4ac-11e7-878e-d7ceefe4eecd.html ; Daily Bruin, Nov 23 2016: https://dailybruin.com/2016/11/23/the-quad-long-distance-relationships-face-the-turkey-drop-this-thanksgiving ; Bucknellian, "Cold turkey: First-years prepare for their inevitable Thanksgiving break-ups": https://bucknellian.net/?p=80147 ; UMD Diamondback, Nov 10 2019: https://dbknews.com/2019/11/10/college-students-thanksgiving-break-break-up-relationship-freshmen ; Duke Chronicle, Nov 2016. "Every November" means the recurring yearly coverage across these papers, not that each paper runs one every year. |
| In 2008 two designers charted 10,000 Facebook breakup posts | David McCandless (Information is Beautiful) and Lee Byron searched about 10,000 Facebook status updates for "breakup" and "broken up" and plotted them by day of year: FlowingData, Nov 4 2010: https://flowingdata.com/2010/11/04/when-people-break-up-according-to-facebook-updates/ ; the data is from Facebook's 2008 Lexicon tool. |
| The second biggest spike is the two weeks before Christmas | ABC News, Dec 3 2010: the pre-Christmas period is the second highest breakup time, behind spring break: https://www.goodmorningamerica.com/news/story/christmas-breakups-romantic-relationships-end-holidays-12307305 ; Adweek: https://www.adweek.com/performance-marketing/when-is-the-best-time-to-break-up-with-someone-facebook-stats-say-spring-break/ |
| Christmas Day is almost empty | The same chart: Christmas Day is the lowest point (FlowingData and ABC above). |
| Thanksgiving is the 26th | Fourth Thursday of November 2026 (Nov 1 2026 is a Sunday). Hook "starts in 3 weeks" holds for a post Nov 6 to 8 (20 to 18 days). |

## Assumptions and jokes

- "Has until Thanksgiving" and "safest on Christmas" are the joke reading of the chart, not a prediction about any couple.
- The 2008 data is small and old (10,000 posts, Facebook Lexicon, not public now). The chart on screen is a simplified shape with the note "Shape simplified from McCandless and Byron, 2008". The real chart also has Valentine's, spring break and summer bumps; ours keeps those so it is not cherry-picked.
- I found no national number for how many freshmen break up at Thanksgiving (one Whitman College humor-page survey said over half, not used). So the script gives no percentage.
- The clipping headlines on the corkboard are paraphrased, with an on-screen note.
- The couple at the table is fiction. No real people on screen; Facebook is named but no logo is shown.

## Caption

"Tag your friend still FaceTiming their high school sweetheart. Thanksgiving is in three weeks. #turkeydrop #longdistance #relatable"

## Scroll patrol

See `2026-11-06-turkey-drop-patrol.md`. Taken: the turkey drops onto the platter on frame one so something moves at 0:00, the hook text puts the slang and the deadline on screen ("TURKEY DROP SEASON / STARTS IN 3 WEEKS"), and line 3 changes inside the shot (speech bubble, then the hearts split). Skipped: opening on "Christmas is the safest day" (spends the turn).

## Status (Nov 6, 10 am make run): rendered, QA passed, queued

- Chatterbox read, every line checked by Whisper (lowest match 0.92 on lines 5 and 9: the words are right).
- First preview had the couple outside the 9:16 frame, the hook text too wide and the speech bubble cut off; moved the two of them behind the table, shortened the hook to "TURKEY DROP / IN 3 WEEKS", lowered the sign under the captions.
- QA: 41.5 s, no steady tones, 9.5 MB. The mix came out at -15.4 LUFS, so the audio got +2.5 dB through a limiter (video copied): -13.2 LUFS, peak -0.4 dBFS.
- Video: `videos/2026-11-6_The_Turkey_Drop.mp4`.
