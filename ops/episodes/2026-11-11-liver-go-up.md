# You Never Wanted Chocolate (raw liver "go up" parody)

- **Source idea:** Austin, Nov 11 (chat): remake the @cluberich TikTok below in its own look and a similar voice, with the raw liver meme line in place of its words, research the trend, and use the same instrumental.
- **The TikTok:** @cluberich, "Or we could go up.." (https://www.tiktok.com/@cluberich/video/7705057053185723670), Nov 6, 53.9 s, 16:9, 5.3M plays, 1.3M likes, 259K saves, 77K shares, "original sound - cluberich". Watched frame by frame and transcribed (Whisper): a man's hype speech ("We could stay here, or we could go up. Do you not understand that? ... You know what's okay? Failing. ... But you know what is not okay? Not trying."), 186 wpm, music at 107.7 BPM, white line-art motion graphics on black, ending on 6 s of dark grainy luxury-car B-roll (#larp).
- **That guy:** the meme line is "You never wanted chocolate, what you actually did want is raw liver", a soundboard clip of a raw-meat YouTuber (who he is, and why, is in the local research notes, kept out of this public repo). We never name or show him: the narrator delivers the line as generic hype-bro wisdom.
- **Research:** four agents, notes in research_notes/2026-11-11_*.md (trend, quote and facts, directed motion style, voice and instrumental).
- **Voice:** the original is almost certainly a real person's podcast clip (not identified). We do not clone a real person to say new words. A designed voice in the same register instead: Qwen3-TTS VoiceDesign made three "deep, chesty, close-mic podcast pep talk" candidates (Nov 11, voice shootout session); candidate 1 won on the numbers (median pitch 119 Hz against the source's ~101 Hz; the other two sat near 200 Hz). The lines were voiced by the Qwen3-TTS Base model cloning that designed clip (engine `qwen_hype`, added at runtime), 3+ takes a line, all 10 lines matched by Whisper (0.97 to 1.00), then voice_fix and qa_voice.
- **Cover:** frame 0 is the opening line art (small figure, empty stairs), weak as a grid cover, so the queue item sets `thumb_offset_ms` 27100: the red RAW LIVER slam. `ops/publish.py` passes it to Instagram as `thumb_offset` (added Nov 12).
- **Music:** unidentified track at 107.7 BPM. Austin decides: Shazam it (legit source or add it in the app), lift the instrumental from the TikTok (copyright risk: Instagram can mute or block), or a royalty-free bed at the same tempo.

## Facts (on screen at the end)

- Dark chocolate (70 to 85%), per 100 g: magnesium 228 mg, iron 11.9 mg (USDA FoodData Central 170273).
- Raw beef liver, per 100 g: magnesium 18 mg, iron 4.9 mg, vitamin A 4,970 ug RAE (USDA 169451).
- So chocolate has about 12x the magnesium and 2.4x the iron. No good evidence that cravings signal a deficiency (BBC Science Focus).

## Script (same beats as the original, line for line)

1. We could stay here. Or we could go up.
2. Do you not understand that?
3. Are you not tired of eating the same chocolate they're currently eating, and afraid to eat like that for the rest of your life?
4. So you might as well start now.
5. And it's not, "one more square." It's not, "it's dark chocolate, it's healthy." It's not, "I'll stop after Halloween."
6. You never wanted chocolate. What you actually wanted... is raw liver.
7. Why? Because there's always... There's always going to be cravings. There's always going to be leftover Halloween candy. There's always going to be the checkout aisle. So you might as well eat the liver now.
8. You know what's okay? Gagging. Gagging is okay. You should gag. Your goal should be to gag as much as possible, so in the end, you'll have iron.
9. But you know what is not okay? Chocolate.
10. (music only) the "larp" payoff: raw liver shot like a luxury car.

Caption: "Or we could eat liver.. #motivation #larp #carnivore"

## The look (white on black, one color kept back)

- Ground #050505 with a soft center lift to #141414 (vignette), ink #FFFFFF, dim ink 45%, the accent #B3122E (liver red) used ONLY from "raw liver" on.
- Type: Montserrat 800, caps, letter-spacing 0.12em; slam words 120 to 150 px with a white glow (text-shadow 0 0 18px and 0 0 46px at 55% and 25%); quiet lines 34 to 40 px; pills white with black 26 px caps, radius 999.
- Icons are thin white line art (stroke 5 px): a person, a chocolate bar, a staircase, a circle with an orbiting square, bars, crossed cards, a star, a liver outline.
- 1080x1920, 30 fps. All words inside x 90 to 990 and y 220 to 1330 (Reels UI).

## The one big moment

Line 6, "raw liver": the only cut to color in the film. "YOU NEVER WANTED / CHOCOLATE" lands white, everything holds for 0.4 s of silence, then a hard cut: "RAW LIVER" slams in liver red with a red glow and the liver outline beats once. Loudest hit in the mix.

## Shot sheet

| # | Cuts in on | Job | Eye (x, y) | Light | Depth | Move | Beat | Intensity |
|---|---|---|---|---|---|---|---|---|
| 1 | "We" (frame 0 is already drawn: person, chocolate bar, line, STAY HERE) | the choice | person at (0.25, 0.56) then the top of the stairs (0.78, 0.30) | glow only on the top of the stairs: a white mystery glow (the liver, not yet revealed) | ground line, stairs, glow | stairs draw on left to right on "go up", arrow rises | hold on STAY HERE, stairs on "go", glow on "up" | 2 |
| 2 | "Do" | the push | center (0.5, 0.42) | text glow | none | words blur in per word | hold 0.5 s | 2 |
| 3 | "Are" | the loop | circle (0.5, 0.40) | glow on the orbiting square | circle, orbit labels, people row | square orbits once a line; circle rises, people row enters on "they're" | AFRAID? lands alone | 3 |
| 4 | "So" | the call | (0.5, 0.42) | inverted pill | none | pill scales 0.92 to 1 | hold | 2 |
| 5 | "And" | the excuses | cards stacked (0.5, 0.30 to 0.62) | none | three cards | each card enters on "It's", its X draws on the quote's last word | X x3, each faster | 3 |
| 6 | "You never" | THE BIG MOMENT | (0.5, 0.42) | white, then the only red | none | hard cut, scale 1.25 to 1 slam with a 4-frame shake | 0.4 s silence before "raw liver" | 5 |
| 7 | "Why" | always obstacles | bars (0.35 to 0.8, 0.50) | none | ground line, person, bars | bars grow on each noun | ANYWAY | 3 |
| 8 | "You know" | gag is okay | (0.5, 0.42), then stairs | glow on the star | stairs with an X per step | GAGS counter ticks per step, star lands on "iron" | slam on "Gagging" | 4 |
| 9 | "But" | the verdict | (0.5, 0.42) | glow | none | slam CHOCOLATE, IS NOT OKAY fades in | hold 0.6 s | 4 |
| 10 | music | the larp payoff | the liver | car-commercial rim light sweep, grain | macro, sill plate, hero | slow push, light sweep | last frame: the USDA note | 3 |

## Status (Nov 12, 12:50 am)

- Rendered `pipeline/out/liver/liver.mp4`: 60.0 s, 1080x1920, 30 fps, -13.0 LUFS, peak -0.9 dBFS. `qa_voice` PASS (pace 4.81 syl/s, spread 8%, line gaps 0.40 to 0.51 s), `qa_audio` no steady tones, `hyperframes check` no errors.
- Watched: frame sheet once a second plus the cut frames. Fixed after the first stills: the orbiting bar flew off the ring (an SVG group needs `svgOrigin`), two bar labels ran into the next bar, the iron goal and CHOCOLATE sat past x 990, seven labels under 28 px, three lines on screen under their read time, and in the B-roll the first frame of shot B carried shot A's motion blur and the camera slide pushed the R of RAW LIVER out of frame.
- The payoff has its own sound (whoosh, a high-passed braam, a headlight-flash click on the sill plate) so it is not silent without music.
- Not queued: the music is Austin's call (see Music above). Rebuilding the sound with a bed is `python render_liver.py audio` with the bed at `out/liver/music.wav`, no new picture render.
- Queue item when it goes: video `videos/2026-11-12_You_Never_Wanted_Chocolate.mp4`, caption above, trial SS_PERFORMANCE, `thumb_offset_ms` 27100.
