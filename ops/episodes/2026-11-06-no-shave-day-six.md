# No Shave November, Day 6

- **id:** 2026-11-06-no-shave-day-six
- **Source idea:** ours. A looks joke with one friend to tag, which is the kind of reel that gets our shares (every reel over 30K is a looks, dating or identity joke, benchmark file, Nov 2). Seasonal like Cuffing Season (our only breakout since Nov 2, Nov 5 report): it is the first week of No Shave November, and everybody knows the friend who stops shaving on Nov 1 and calls six days of stubble a beard.
- **Why people care:** No Shave November is a yearly campaign millions of people joke about in the first week; the "how much did you donate" beat is the honest twist.
- **Format:** toon kit (toon.py), calm Chatterbox read, yellow outlined captions. Cast: objects only. Your friend is a potato with a face and a few dark hairs on his chin. Sets: a bathroom mirror (opening: the potato strokes his chin in the mirror on frame one), a macro of skin with three hairs growing, a giant ruler, a phone with four identical progress pics, a calendar with Nov 30 circled, a donation jar.
- **Rotation:** the episode before this one in the queue is The Christmas Music Friend (pastel toy, peg people, daylight living room). The last toon one, Mercury Retrograde, was a bedroom, a sky and a space orbit with a phone and a planet. No set, opening or cast repeats.
- **Odd physical detail (style.md, Oct 29):** when he strokes the stubble it squeaks like sandpaper, and in the last shot he sweats one big drop.
- **Files:** `pipeline/render_shave.py`, `pipeline/shave_scene.py`.

## Script: see `SCRIPT` in `pipeline/render_shave.py`

1. Your friend is doing No Shave November.
2. It's day 6. He calls it a beard.
3. Beard hair grows about a third of a millimeter a day.
4. So he has about 2 millimeters.
5. He has posted 4 progress pics.
6. At that speed, by November 30th, it's about a centimeter.
7. No Shave November started in 2009 to raise money for cancer research.
8. Tag your friend and ask how much he donated.

## Facts and sources

| Claim in the script | Source |
|---|---|
| Beard hair grows about a third of a millimeter a day | Reported averages run 0.27 to 0.5 mm a day; a 2016 International Journal of Cosmetic Science study is cited for a mean of 0.27 mm a day. Summaries: https://keratin.com/hair-biology/beard-hair-biology-structure-density-growth-rate , https://toolsofmen.com/beard-care/beard-growth-stages . "About a third" (0.33) sits inside that range. |
| Day 6: about 2 mm | 6 x 0.33 = 2.0 mm (1.6 to 3 mm across the reported range). |
| By Nov 30: about a centimeter | 30 x 0.33 = 10 mm "at that speed" (the line says so). |
| No Shave November started in 2009 to raise money for cancer research | Started by the Hill family of Chicago in 2009 as a Facebook campaign for cancer research after Matthew Hill died of colon cancer: https://www.kshb.com/news/local-news/siblings-turn-no-shave-november-into-millions-for-cancer-research , https://kykernel.com/?p=36569 . Since 2024 the campaign is run by Fight Colorectal Cancer: https://fightcolorectalcancer.org/zh/blog/a-new-era-for-no-shave-november |

## Assumptions and jokes (not claims)

- The friend, his "beard", the four progress pics and the empty jar are the joke, not a claim about anyone.
- The joke is on the friend who skips the donating part, never on the cause. The real purpose of the campaign is stated plainly.
- Growth varies a lot between people; "about" covers that, and the honesty note on screen gives the source.

## Caption

"Tag the friend on day 6 of his beard. #noshavenovember #relatable #funny"

## Scroll patrol

See `2026-11-06-no-shave-day-six-patrol.md`.

## Status (Nov 6, 2 am make run): rendered, QA passed, queued for Nov 6 12:30 pm ET

- Narration: Chatterbox, calm (0.5), 27.1 s; Whisper matched every line.
- Eevee, 812 frames in 311 s.
- Preview fixes: moved the sink behind the potato (it hid him and the tap covered his face), grew the hairs up out of the skin instead of both ways, brought the 1/3 MM, 2 MM and 1 CM signs into frame, pulled the camera up the ruler for the centimetre shot, set both jars on their tables, and split the 6 s jar shot into two angles.
- QA: 27.1 s, no steady tones, 7.8 MB. The mix came out at -15.7 LUFS, so the audio got +2.7 dB through a limiter (video copied): -13.3 LUFS, peak -0.5 dBFS.
