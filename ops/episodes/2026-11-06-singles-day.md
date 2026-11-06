# Singles' Day

- **id:** 2026-11-06-singles-day
- **Source idea:** ours. A seasonal tag-a-friend dating joke, following the Nov 5 daily report (Cuffing Season, our only breakout since Nov 2, was a seasonal joke with one friend to tag; the report suggests that setup for the next episodes). Singles' Day is Wednesday, November 11: the holiday for single people that turned into the world's biggest shopping day and, in Beijing, a popular wedding date.
- **Why people care:** everyone has a single friend to tag, and the date is five days out. The turn (even the singles' holiday got taken by couples) is a true fact that lands as the punchline.
- **Format:** pastel toy kit at night, toy peg people, calm Chatterbox read. Rotation: the episode before it in the queue is No Shave November, Day 6 (toon kit, object cast, bathroom mirror); the pastel one before that was a daylight living room. This one is new on every count: a night apartment with a beanbag, a 1993 dorm with a bunk bed and a CRT, a pink wedding hall.
- **Odd physical detail (style.md, Oct 29):** delivery boxes keep falling from above and piling up around the beanbag, and he hugs a gift he bought himself while a heart pops over his head.
- **Files:** `pipeline/render_singles.py`, `pipeline/singles_scene.py`.

## Script: see `SCRIPT` in `pipeline/render_singles.py`

1. Your single friend has a holiday coming up. November 11th.
2. Four ones in a row. One for each single person.
3. It started in 1993, in a dorm at Nanjing University, to celebrate being single.
4. In 2009, Alibaba turned it into a sale.
5. By 2021, Alibaba sold 84 billion dollars of stuff in it.
6. So the one day for single people became the day they buy themselves presents.
7. And in 2011, over 4,000 couples in Beijing picked it as their wedding day.
8. Even the holiday for single people got taken.
9. Tag your single friend. Their holiday is Wednesday.

The last line runs back into the first ("Your single friend has a holiday coming up").

## Facts and sources

| Claim in the script | Source |
|---|---|
| Singles' Day is November 11; the four 1s stand for single people | Wikipedia, "Singles' Day" (the date chosen because 1 looks like a "bare stick", slang for a single man; the four 1s represent four singles, citing Keyu Jin, The New China Playbook, 2023, p. 53): https://en.wikipedia.org/wiki/Singles%27_Day |
| Started in 1993 in a Nanjing University dorm to celebrate being single | Wikipedia above (originated at Nanjing University in 1993; the most widely accepted story is a dorm of four single men), citing Time, "How China's Singles' Day Holiday Sold Out", Nov 11 2014: https://time.com/3576381/china-singles-day-history/ . The LA Review of Books calls the exact dorm story an origin myth (https://lareviewofbooks.org/blog/chinablog/selling-singles-day-origin-story/), so the script says only "started in 1993, in a dorm at Nanjing University", not the four-students detail. |
| In 2009 Alibaba turned it into a sale | Wikipedia above (in 2009 Alibaba's Daniel Zhang began using the day for online shopping discounts), citing the South China Morning Post: https://www.scmp.com/tech/big-tech/article/3155762/sales-growth-alibabas-singles-day-drops-amid-chinas-crackdown-big |
| By 2021 Alibaba sold 84 billion dollars of stuff in it | Reuters via FX Empire, Nov 2021: 540.3 billion yuan ($84.54 billion) over Alibaba's 11-day Singles' Day festival: https://fxempire.com/news/article/chinas-alibaba-records-singles-day-gmv-of-84-54-billion-over-11-day-sales-period-805915 ; Benzinga: https://www.benzinga.com/news/21/11/24047621/how-did-alibaba-fare-with-its-2021-singles-day-shopping-event . On-screen note says it is the 11-day festival. |
| In 2011 over 4,000 couples in Beijing married on that date | Wikipedia above ("more than 4,000 couples got married in Beijing on this date in 2011, far greater than the daily average of 700"), citing The Economist, "Asian demography: The flight from marriage", Aug 20 2011. |
| Their holiday is Wednesday | Nov 1 2026 is a Sunday, so Nov 11 2026 is a Wednesday. The queued slot is before Nov 11. |

## Assumptions and jokes

- "Buy themselves presents" is the joke framing of a shopping day; the sales figure is real, who bought what is not claimed.
- "Even the holiday for single people got taken" is the punchline drawn from the 2011 wedding fact, not a claim that couples own the day now.
- The friend, his cart count and the boxes are fiction.
- No real people on screen; Alibaba is named but no logo is shown.

## Caption

"Tag your single friend before somebody takes their holiday too. #singlesday #single #relatable"

## Scroll patrol

6 of 10 (`2026-11-06-singles-day-patrol.md`). Taken: a delivery box drops next to the friend on frame one so something moves at 0:00, and the hook text says the premise ("YOUR SINGLE FRIEND'S / HOLIDAY IS COMING"). Skipped: opening on the 4,000 weddings (it spends the punchline in the first second).

## Status (Nov 6, 6 am make run): rendered, QA passed, queued

- Chatterbox read, every line checked by Whisper (lowest match 0.69 on line 5, which it heard as "$84 billion": the words are right).
- QA: 40.7 s, no steady tones, 10.6 MB. The mix came out at -16.1 LUFS, so the audio got +3.1 dB through a limiter (video copied): -13.4 LUFS, peak -0.7 dBFS.
- Video: `videos/2026-11-6_Singles_Day.mp4`.
