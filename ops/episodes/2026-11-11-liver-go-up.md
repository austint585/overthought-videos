# You Never Wanted Chocolate (raw liver meme, in the "go up" edit's style)

- **Source idea:** Austin, Nov 11 (chat): the @cluberich TikTok below, same look, same kind of voice, same instrumental, but saying what the raw liver meme guy says.
- **Cut 2 (Nov 12):** cut 1 rewrote the TikTok's speech line for line with chocolate swapped in and left the music for later. Austin: it should quote what the guy actually said, and the TikTok's music belongs under it. Cut 2 does both.
- **The TikTok:** @cluberich, "Or we could go up.." (https://www.tiktok.com/@cluberich/video/7705057053185723670), Nov 6, 53.9 s, 5.3M plays, 1.3M likes, 259K saves, 77K shares, "original sound - cluberich". A man's hype speech over a slow dark bed at 107.7 BPM, white line-art motion graphics on black, ending on 6 s of dark grainy luxury-car B-roll (#larp).
- **The words:** a 14 s meme soundboard clip of a raw-meat YouTuber (who he is, and why we keep him unnamed, is in the local research notes, not in this public repo). Whisper transcript, used verbatim: "You never wanted chocolate. What you actually did want is raw liver. Why do you play video games? Because you want to hunt. Why do you play football? Because you want to hunt with your team." We never name or show him.
- **Voice:** not a clone of anyone. A designed voice in the TikTok's register (Qwen3-TTS VoiceDesign, "deep, chesty, close-mic podcast pep talk", candidate 1 of 3, median pitch 119 Hz against the source's ~101 Hz), voiced with the Qwen3-TTS Base model from that designed clip (engine `qwen_hype`), 3+ takes a line, Whisper-checked, then voice_fix and qa_voice.
- **Music:** the TikTok's own bed. Its voice was removed with Demucs (htdemucs, two stems; Whisper hears no words left in the music stem). Placed so the song's drop (47.83 s, where the original cuts to the car B-roll) lands on our payoff cut, and the video ends where the song ends. The hold after the last word is set so "raw liver" lands on a beat. Ducked 7 dB under the voice, up for the payoff. The split audio lives in `pipeline/out/ref/cluberich/split/` and is never committed. Risk, said once: Instagram may match it and mute the audio or limit the Reel. Austin's call (Nov 12).
- **Cover:** frame 0 is the chocolate bar alone, so the queue item sets `thumb_offset_ms` on the red RAW LIVER slam. `ops/publish.py` passes it to Instagram as `thumb_offset`.

## Facts (on screen at the end)

- Dark chocolate (70 to 85%), per 100 g: magnesium 228 mg, iron 11.9 mg (USDA FoodData Central 170273).
- Raw beef liver, per 100 g: magnesium 18 mg, iron 4.9 mg, vitamin A 4,970 ug RAE (USDA 169451).
- End card: "For the record: dark chocolate has 228 mg magnesium per 100 g. Raw liver has 18. (USDA)"

## Script (his words, verbatim)

1. You never wanted chocolate.
2. What you actually did want is... raw liver.
3. Why do you play video games?
4. Because you want to hunt.
5. Why do you play football?
6. Because you want to hunt with your team.
7. (music only) the "larp" payoff: raw liver shot like a luxury car, on the song's drop.

Caption: "You never wanted chocolate.. #larp #rawliver #carnivore"

## The look (white on black, one color kept back)

- Ground #050505 with a soft center lift (vignette), ink #FFFFFF, dim ink 55%, the accent #C21A33 (liver red) used ONLY from "raw liver" on.
- Type: Montserrat 800, caps, letter-spacing 0.12em; slam words 78 to 140 px with a white glow; quiet lines 34 to 44 px; white pills with black caps.
- Icons are thin white line art: a chocolate bar, a liver outline, a game controller, crosshairs, an American football, a team of figures.
- 1080x1920, 30 fps. All words inside x 90 to 990 and y 220 to 1330 (Reels UI).

## The one big moment

Line 2, "raw liver": the only cut to color in the film. "WHAT YOU ACTUALLY / DID WANT IS..." builds in white, then a hard cut on "raw": RAW LIVER slams in liver red, the liver outline draws and beats once, on a beat of the song. Loudest hit in the mix.

## Shot sheet

| # | Cuts in on | Job | Eye (x, y) | Light | Move | Beat | Intensity |
|---|---|---|---|---|---|---|---|
| 1 | frame 0 (bar already drawn) | the claim | bar (0.5, 0.26), then CHOCOLATE (0.5, 0.47) | glow on the bar | words blur in, CHOCOLATE slams, an X draws across the bar | X on "chocolate" | 3 |
| 2 | "What" | THE BIG MOMENT | (0.5, 0.40) | white, then the only red | hard cut, RAW LIVER slams with a 4-frame shake, liver draws and beats | "raw" on a beat | 5 |
| 3 | "Why" | games are hunting | controller (0.5, 0.29) | glow on the scope | controller dims, crosshairs draw over it, tighten on "hunt" | HUNT slam | 3 |
| 4 | "Why" | football is team hunting | football (0.5, 0.29), then the field | red glow on the target | hard cut to a field: a team on the left, a red liver in red crosshairs on the right; the team charges on "team" | HUNT slam, WITH YOUR TEAM pill | 4 |
| 5 | the song's drop | the larp payoff | the liver | car-commercial rim light sweep, grain | macro, sill plate, hero, slow push | the USDA note | 3 |

## Status (Nov 12)

- Cut 1 (Nov 12, 12:50 am, 60 s, the rewritten speech) is kept in `pipeline/out/liver/v1/` and was never queued.
- Cut 2 rendered Nov 12, 11:41 am: `videos/2026-11-12_You_Never_Wanted_Chocolate.mp4`, 19.8 s, 1080x1920, 30 fps, -12.5 LUFS, peak -1.0 dBFS. `qa_voice` PASS (all six lines heard word for word, pace 4.72 syl/s, spread 0%), `qa_audio` no steady tones, `hyperframes check` no errors. Whisper on the final mix hears every word over the music.
- The pause before "raw liver" was 0.25 s after voice_fix; it was lengthened to 0.55 s by hand (silence added in `narration_fixed.wav`, later words shifted) and "raw" pinned to its real onset, since Whisper had it 0.24 s early. The song sits at 34.03 to 53.82 s, so "raw" lands 20 ms after a beat.
- Watched: stills at every word cue plus a 1 fps sheet of the final file. Fixed after the first stills: the X across the chocolate bar landed 0.2 s before the cut, too short to read; it now draws right after the CHOCOLATE slam.
- Queued `ready` for Nov 12, 12:30 pm ET, `thumb_offset_ms` 4700 (the RAW LIVER slam).
