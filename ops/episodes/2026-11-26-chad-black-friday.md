# Saw It On A Reel: Black Friday (2026-11-26-chad-black-friday)

**Why now:** Black Friday is Friday, Nov 27. Everyone repeats the "stores finally go in the black" story that day, and it isn't true. Timely reels are one of our two idea sources that work (`ops/make.md`), and the last one in this shape, "Saw It On A Reel" (tryptophan, Nov 25), is our best recent reel: 5.4K plays, 73% watched, 12 shares (`reports/daily/2026-11-25.md`). This is the third episode of the "reel educated" chad bit (`research_notes/2026-11-24_Series_And_Shirt_Concept.md`). No new DM this run: Chrome wasn't connected, so the DM check was skipped.

**Re-rendered the same evening with the low-poly cast** (`pipeline/render_ps2.py chad_black_friday`): Austin DMed the PS1/PS2 recipe, OK'd the chadlite test and said "Yes, rebuild them" for the friends. The script, voices, cards, timing and caption are unchanged; only the people and the look changed (`research_notes/2026-11-26_PS2_Look_With_Claude.md`). The MakeHuman render is kept as `videos/2026-11-26_Saw_It_On_A_Reel_Black_Friday.mp4`; the queue now points at the low-poly one. Later that night Austin asked for the chad to look like the actor who plays Matt Hagen in Clayface ("emphasis on the wavy hair"). The low-poly file was re-rendered with that chad under the same name: wavy dirty-blond hair, blue-grey eyes and a dark tee.

**Format:** game cutscene (`pipeline/render_cutscene.py`, episode `chad_black_friday`). The same four characters at the patio table, now a Black Friday morning set (`blackfriday_props` in `cutscene_scene.py`): coffee, leftover turkey sandwiches, shopping bags on the front corners of the table and a receipt. The post just before this one (The Turkey Is Still A Rock) was the pastel toy kit, so the set and the opening shot are new to the feed.

## Script

| Who | Line | Tag |
|---|---|---|
| Hook (frame 0) | "POV: Black Friday with the guy who learned everything from reels" | |
| Finance guy | "Black Friday. Stores finally go in the black." | MBA / $140K |
| Chad | "Philly cops named it." | EDUCATION / REELS |
| (the table laughs) | | |
| Finance guy | "Okay. Let me just check." | |
| Phone search | "why is it called black friday" → HISTORY.COM: "Philadelphia police named it in the 1950s" / "For the traffic chaos. The 'in the black' story came in the late 1980s." | |
| (tags flip) | | MBA → WRONG (red), REELS turns gold |
| Big tech guy | "Whatever. This TV's sixty percent off." | BIG TECH / $310K |
| Chad | "Same price in March." | |
| Plumber | "Where are you getting all this?" | |
| Chad | "Saw it on a reel." (orange punchline) | |

23.3 s. The chad's first line lands at 3.5 s.

## Facts and sources

| Claim on screen | Source |
|---|---|
| Philadelphia police named it in the 1950s, for the traffic chaos | History.com, Sarah Pruitt, "Black Friday's Origins and History" (updated Sept 9 2026): the police used the term in the 1950s for the chaos of the day after Thanksgiving; "By 1961, 'Black Friday' had caught on in Philadelphia", and merchants tried to rename it "Big Friday". https://www.history.com/articles/black-friday-thanksgiving-origins-history Also the Philadelphia Inquirer: https://www.inquirer.com/philly/news/breaking/20111125_Black_Friday_started_in_Philly.html |
| The "in the black" story came in the late 1980s | Same History.com article: calls it the officially sanctioned but inaccurate story behind the name, and says "Sometime in the late 1980s, however, retailers found a way to reinvent Black Friday". Snopes dates the earliest known use of the accounting explanation to 1981 (https://www.snopes.com/fact-check/black-friday-2, from search results; the page itself would not load). |
| "Same price in March" | The chad's joke version of Which?'s yearly finding that most Black Friday deals are the same price or cheaper at other times of the year (for example nine in 10: https://www.which.co.uk/policy-and-insight/article/nine-in-10-black-friday-deals-cheaper-or-same-price-at-other-times-of-the-year-which-finds-a4Z2J3u5lTI2). The TV is fictional; no real product or month is claimed. |

Assumptions: Which? is a UK consumer group and checks UK retailers; the line only claims something about the fictional TV. The salary tags are the characters' flexes, part of the joke, as in the earlier chad episodes. History.com says "1950s" in its text and "1961" in a photo caption; the card uses "1950s" with "1961" as the year it had clearly caught on, so either reading fits.

## Shot sheet

Look: golden-hour patio, warm sun and leaf shadows on a sandstone wall, blue sky fill; the one accent is gold on REELS when the tags flip.
Big moment: the tag flip after the search card ("WRONG" in red, REELS turns gold), at 12.7 s.

| t (s) | Shot | Eye | Beat |
|---|---|---|---|
| 0.0 | group of three behind the table, red bag front left | the hook text, then the finance guy's face | breath |
| 3.5 | close on the chad | his face, EDUCATION / REELS tag | hit |
| 5.2 | wide, all four laugh | the laughing faces | settle |
| 6.6 | single on the finance guy looking down at his phone | his face | breath |
| 9.5 | full-frame phone search | the answer card | hit |
| 12.7 | wide, tags tick (the big moment) | WRONG / REELS gold | hit |
| 14.2 | single on the big tech guy | his tag and face | breath |
| 17.3 | close on the chad | face | hit |
| 19.3 | single on the plumber | face | breath |
| 21.3 | close on the chad, orange punchline | caption | hit |

## Caption

"Send this to whoever's setting an alarm for the doorbusters. #blackfriday #funfacts #history"

## Slot

Fri Nov 27, 10:30 am ET (timely, so the morning slot on the day itself).
