# Hibernation Mode

- **id:** 2026-11-06-hibernation-mode
- **Source idea:** ours. A seasonal tag-a-friend joke (the Cuffing Season setup the Nov 5 report suggests): the clocks went back on Nov 1, the sun now sets before 5, and everybody has the friend who announces "hibernation mode" and then orders food every night. Real bear numbers make the joke land: bears really do eat nonstop in the fall, so the friend is technically in the right phase.
- **Why people care:** the early dark is the thing everyone in the US is complaining about this week, and "hibernation mode" is a phrase people already use about themselves and friends.
- **Format:** toon kit (toon.py), calm Chatterbox read, yellow outlined captions. Cast: your friend rolled up in a blue quilt (only the face shows) and a black bear. Sets: his living room at 4:48 pm (opening: the sun sliding behind a hill in the window while he waddles to the couch in the quilt), a cave with the bear asleep and one slow heartbeat, his front door with three delivery bags, the woods in fall with the bear eating berries.
- **Rotation:** the episode before it in the queue is Singles' Day (pastel toy kit, peg people, night apartment, dorm, wedding hall). The last toon one, No Shave November, was a potato in a bathroom mirror. New kit from the one before, new cast, new sets, new opening.
- **Odd physical detail (style.md, Oct 29):** his "GO AWAY" doormat, and the bags still piled in front of him while he sleeps.
- **Files:** `pipeline/render_hibern.py`, `pipeline/hibern_scene.py`.

## Script: see `SCRIPT` in `pipeline/render_hibern.py`

1. The sun now sets before 5. Your friend is already in a blanket.
2. He says he's in hibernation mode.
3. A hibernating black bear's heart slows to about 8 beats a minute.
4. It goes months without eating, drinking or using the bathroom.
5. Your friend has had food delivered three times since Sunday.
6. Bears do that part too. In the fall they eat up to 20,000 calories a day.
7. So technically, your friend is still in the eating part.
8. And the sun keeps setting earlier until December.
9. Tag your friend. It's 4:48. He's asleep.

Loops: the last line (4:48, asleep) runs into the first (sun sets before 5, blanket).

## Facts and sources

| Claim in the script | Source |
|---|---|
| The sun now sets before 5 (4:48 pm on the clock) | New York City, Nov 6 2026: sunset about 4:47 to 4:48 pm EST (surf-life.blue table: https://www.surf-life.blue/us/sunrisesunset/new-york-city-ny/202611/ ; Time Out NY on the clock change: https://www.timeout.com/newyork/news/this-is-the-last-day-the-sun-will-go-down-after-6pm-in-nyc-until-spring-2027-102326). Clocks went back Nov 1 2026 (timeanddate: https://www.timeanddate.com/time/change/usa/new-york-state?year=2026). True for most of the eastern US; not everywhere (assumption below). |
| A hibernating black bear's heart slows to about 8 beats a minute | North American Bear Center, "5 Stages of Activity and Hibernation": 8 to 21 beats a minute in hibernation (https://bear.org/5-stages-of-activity-and-hibernation/); Yellowstone NPS fact sheet: 40 to 50 in summer, 8 to 19 in hibernation (https://webarchive.library.unt.edu/web/20120927065533/http://www.nps.gov/yell/forkids/upload/YELL710.pdf). "About 8" is the low end; the on-screen note gives the range. |
| It goes months without eating, drinking or using the bathroom | Yellowstone NPS fact sheet above; Minnesota DNR, Conservation Volunteer, Jan-Feb 2020 (https://www-dev.dnr.state.mn.us/mcvmagazine/issues/2020/jan-feb/bears.html); EarthSky on the Alaska black bear study (https://earthsky.org/earth/what-we-didnt-know-about-hibernating-black-bears). |
| In the fall bears eat up to 20,000 calories a day | Yosemite NPS, "Eleven Pounds of Acorns": hyperphagia, up to 20,000 calories every day (https://www.nps.gov/yose/blogs/eleven-pounds-of-acorns-a-daily-feast-for-a-bear.htm); NC Wildlife: 15,000 to 20,000 (https://wlos.com/news/local/wildlife-officials-warn-black-bears-appetites-now-at-a-seasonal-high-during-fall-months-north-carolina-resources-commission-hyperphagia-phase-birdfeeders-avoid-encounters-safety-tips-gain-weight-hibernation). |
| The sun keeps setting earlier until December | timeanddate, "Earliest sunset": the earliest sunset in New York comes about Dec 7 and 8, two weeks before the solstice (https://www.timeanddate.com/astronomy/earliest-sunset.html); ABC7 NY (https://abc7ny.com/earliest-sunset-winter-solstice-latest-sunrise-solar-time/11310130/). |

## Assumptions and jokes

- "Before 5" uses New York. Many US cities have sunsets before 5 pm this week, but not every one (places on the western edge of a time zone set later). The clock says 4:48 pm, the NYC time.
- The friend, his three deliveries and the doormat are fiction.
- The bear in the cave and the one in the woods are generic black bears; no claim about one bear.

## Caption

"Tag the friend who went into hibernation mode at 4:48 pm. #relatable #hibernation #winter"

## Scroll patrol

6 of 10 (`2026-11-06-hibernation-mode-patrol.md`). Taken: frame one has motion (the sun sliding down while he waddles in the quilt), and the hook text says the joke ("SUNSET BEFORE 5 PM / HIBERNATION MODE"). Skipped: opening on the bear (the friend is who people tag).

## Status (Nov 6, 6 am make run): rendered, QA passed, queued

- Chatterbox read, every line checked by Whisper (line 9 heard as "448", the right words).
- QA: 33.5 s, no steady tones, 6.7 MB. The mix came out at -15.3 LUFS, so the audio got +2.2 dB through a limiter (video copied).
- Video: `videos/2026-11-6_Hibernation_Mode.mp4`.
