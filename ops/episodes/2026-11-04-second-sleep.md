# Second Sleep

- **id:** 2026-11-04-second-sleep
- **Source idea:** the story shape from Austin's Nov 3 @garden_reels1o reels ("more stupid ideas like this would be good") and the @design.pilot reel he sent Nov 4 (https://www.instagram.com/reel/DfSKMDkyIWA/, watched with watch.py): a second-person awkward moment, strangers walking in one at a time, nobody reacting, then a "what you don't know" turn to a real history fact that explains it, and a wide shot where the whole cast joins in. Premise, cast and history fact are ours: the 3 a.m. "u up?" text, a candle-carrying neighbour, a goose on the router, and pre-industrial segmented sleep.
- **Why people care:** "u up?" at 3 a.m. is a universal late-night-text joke, and our only reels with real shares are relatable dating jokes with one clear friend to send it to (Height 4.2K plays and 18 shares, Cuffing Forecast 3.6K and 21, Nov 3 report; Schrodinger 566K). Segmented sleep is a well-known history fact that comes back around online every year or two (the BBC piece below has been reprinted widely).
- **Format:** second-person story, pastel toy kit at night, toy peg people plus a goose. Calm read. The episode before it is a toon diner joke explainer (36 Questions), so the kit, set and format rotate. Sets: a moonlit bedroom (opening: the phone already glowing, the "u up?" bubble popping), the bedroom door, a timber medieval room with two people in nightcaps, a night lane between two cottages, an open book of records by candlelight, the bedroom again with everyone asleep.
- **Files:** `pipeline/render_sleep.py`, `pipeline/sleep_scene.py`.

## Script: see `SCRIPT` in `pipeline/render_sleep.py`

1. It's 3 a.m. You text your ex: u up?
2. No reply. Then somebody knocks.
3. It's your neighbor. Holding a candle.
4. He sits on your bed and asks how the harvest went.
5. Then his wife walks in with soup.
6. Then a priest. Then a man with a goose.
7. The goose sits on your router.
8. Your ex texts back. She's at the door, with her neighbors.
9. What you don't know: before electric light, people slept in two shifts.
10. They woke up for an hour or two in the middle of the night.
11. Some prayed. Some went over to visit the neighbors.
12. Old records call it first sleep, then second sleep.
13. The goose falls asleep first.
14. So the next time it's 3 a.m. and you text your ex, it's tradition.

## Facts and sources

| Claim in the script | Source |
|---|---|
| Before electric light, people slept in two shifts | A. Roger Ekirch, "Sleep We Have Lost: Pre-industrial Slumber in the British Isles", American Historical Review 106(2), 2001; book "At Day's Close: Night in Times Past" (2005). Summary: BBC News Magazine, Stephanie Hegarty, "The myth of the eight-hour sleep", 22 Feb 2012, https://www.bbc.com/news/magazine-16964783 (full text copy: https://people.uncw.edu/imperialm/uncw/PLS_506/BBC_Myth_of_8_hour_sleep_2_22_12.pdf) |
| They woke for an hour or two in the middle of the night | BBC piece above: a first sleep starting about two hours after dusk, then a waking period of one or two hours, then a second sleep. |
| Some prayed, some visited neighbours | BBC piece above: during the waking period people stayed in bed, read, wrote, often prayed; others went out and visited neighbours. |
| Old records call it "first sleep" and "second sleep" | Ekirch 2001 cites over 500 references (diaries, court records, medical books, literature); he later reported over 2,000 (Big Think summary: https://bigthink.com/robby-berman/for-1000s-of-years-we-went-to-bed-twice-a-night-2). The script names no count. |

## Assumptions and jokes (not claims)

- The neighbour, his wife, the priest, the goose man, the goose and the ex are fiction. The harvest question and the soup are period jokes, not claims.
- We do not say everyone everywhere slept this way. Scholars dispute how universal it was (Russell Foster and Sasha Handley, cited in the same coverage), so the script says "people" and "old records", nothing stronger.
- "Tradition" in the last line is the joke, not a historical claim about texting.
- Cut for length (first take ran 49.7 s): "Fully dressed.", "Some read.", the record count, and "Your phone buzzes. It's your ex." became "Your ex texts back."

## Caption

"Historians have a name for the 3 a.m. text. Tag the friend who keeps this tradition alive. #relatable #history #funny"

## Scroll patrol

See `2026-11-04-second-sleep-patrol.md`.

## Status (Nov 4, 6 pm make run): rendered, QA passed, queued

- Narration: Chatterbox ran out of Windows commit memory on the second take (DefaultCPUAllocator: not enough memory) with Austin's apps open, so this one uses the Kokoro fallback (`OT_VOICE=kokoro`, am_adam), as You Too did. 37.2 s. Kokoro reads "a.m." as "ay em".
- Eevee at about 0.85 s a frame (1,116 frames in 16 minutes).
- Preview fixes: the u up?, I'M OUTSIDE and HARVEST bubbles were cut at the right edge (moved over your head and the bed); the wake, lane and book shots were framed too tight (pulled back); the two history signs were enlarged.
- QA: 37.2 s, no steady tones, -12.9 LUFS, peak -0.9 dBFS, 8.4 MB. Last shot matches the first (loops).
