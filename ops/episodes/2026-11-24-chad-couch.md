# Couch Pulls Out (2026-11-24-chad-couch)

**Source:** Austin's DM of the @zeromrrclub reel (https://www.instagram.com/p/Df5RJMCNUlO/, "can you figure out how this style is made"), plus his Nov 22 note to pick one big niche (the jobless joke or blue-collar guys) and make videos like it. Nov 24 in chat: "get something that looks better then post stuff with him" (the chad).

**Format:** game cutscene, built in code (`pipeline/render_cutscene.py`, episode `chad_couch`). Four MakeHuman characters at a patio table in golden-hour light, Drama 3 voices, pixel UI on top. First episode with the rebuilt chad (lean face, jaw and brow past MakeHuman's range, stubble, strand hair).

## Their beats, ours

| Their reel (21 s) | Ours (22.9 s) |
|---|---|
| Hook: "POV: meeting her friends' boyfriends" | "POV: her friends brought their boyfriends" |
| A friend teases the hero: "Oh, you're the startup guy" | Big tech guy: "So you're the one who's between things." |
| Three flexes with salary tags (consulting, private equity, big tech) | Finance $240K, big tech $310K, plumber $180K ("One-eighty. Cash.") |
| "You?" | Finance guy: "You?" (cut to the chad) |
| "I'm in a garage." Tag GARAGE / $0 / AURA ∞ | "I don't work." Tag UNEMPLOYED / $0 / AURA ∞ |
| They laugh | They laugh |
| Phones buzz, layoff notification, tags tick to $0 | Two phones ring, HR lock screen "Your role has been eliminated / Please return your laptop", finance and big tech tick to $0. **Our twist:** the plumber's phone stays quiet and his tag stays $180K. |
| "The garage has room." | "Couch pulls out." (orange punchline) |
| "Is there Wi-Fi?" | Big tech guy: "Is there room for a second monitor?" |
| Merch end card | none (nothing to sell yet) |

Every line is our own; no sentence, catchphrase or sign-off is lifted. The salaries are the characters' flexes, read as part of the joke, not claims.

## Sound

Voices: Fish Drama 3, each character cloned from a different Kokoro synthetic voice (no real person): jacket am_liam, suit am_onyx, chad am_michael, overalls am_eric. Music: the @zeromrrclub reel's own background bed (Austin, Nov 24: "we need that background audio they use"), split with Demucs and looped; its source is unidentified, so Instagram may match it (Austin was told). Effects from the Sonniss GDC 2026 bundle: a xylophone ringtone for the phones, a male laugh doubled at two pitches for the table laugh, UI coins on each tag, a muted deny on each drop to $0.

## Shots

Wide from just over the table's front edge (16 mm, so all four heads and tags fit 9:16 and the table fills the bottom), single on the chad for "You?", close-ups on the chad for both of his lines, a full-frame phone insert, a single on the big tech guy for the last line.

## Checks

- Preview stills: Nov 24, after reframing the four-person wide (first pass cut the outer two tags off and showed legs under the table).
- Full render, Nov 24: transcript matched the script, -12.9 LUFS, no steady tones. The frame check then caught the finance and big tech guys looking up at the sky when their phones ring (head pitch was inverted in `cutscene_scene.py`). Fixed and re-rendered the same night, before its slot.
- Checks on every render: frame sheet, Whisper transcript against the script, `qa_audio.py`, loudness. `qa_voice.py` measures a single narrator's pace and does not apply to a four-voice dialogue; the transcript and the sheet stand in for it.

## Caption

"Tag the friend who'd ask about the second monitor. #unemployed #layoffs #aura"
