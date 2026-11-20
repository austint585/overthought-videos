# Sir, This Is A Wendy's

- **id:** 2026-11-15-sir-wendys
- **Source idea:** make.md "Pick the idea", rule 3 (form x line), from the Nov 14 weekly plan (`ops/plan/2026-11-14.md`, episode 1) and idea 2 of the Nov 12 blind trend test. No new DM could be read this run: Claude in Chrome was not connected (Nov 14, 8:20 pm ET).
- **The form:** an earnest corner-coach motivational speech, the register of the cats-boxing reel at 1.5M views on Nov 10 (https://www.instagram.com/reel/DfjX_KStX9j, per `ops/research/2026-11-12-blind-trend-test.md`).
- **The line:** "Sir, this is a Wendy's", the reply people give to someone ranting where nobody asked.
- **Why people care:** everyone knows the line, and everyone knows the friend who gives a speech at the wrong moment. The payoff is the line itself, so the whole reel is a setup for a punchline the viewer can see coming and still wants to hear. Share target: "send this to the friend who gives speeches at the drive-through".
- **Look (style_rules.md):** toon (cel shading, thick outlines), and the cast are objects, not code-built people: the coach is a blue boxing glove with a towel and a headset, the cashier is a cash register in a visor. The episode before it in the queue (The Bicep Heart) is clay, and the one before that is white line art, so this is a new style, a new set (a fast-food counter roped off like a boxing corner, a menu board with a round timer) and a new opening.
- **Voices:** the coach is the designed hype voice (`qwen_hype`, Qwen3-TTS, designed from a text description), voiced in breath groups like We Could Go Up. The cashier and the last line are the calm Chatterbox narrator (exaggeration 0.5). Two voices because the joke is the gap between the speech and the flat reply.
- **Files:** `pipeline/render_wendys.py`, `pipeline/wendys_scene.py`.

## Script (`SCRIPT` in `pipeline/render_wendys.py`)

1. (coach) Look at me. They said you'd never *make it.* Too small. Too slow. Too *soft.*
2. (coach) Every time you went down, you got back up. Tonight, you take what's *yours.*
3. (cashier, flat) Sir, this is a *Wendy's.*
4. (coach, quieter) A number six. And the *heart of a champion.*
5. (cashier) Send this to the friend who gives speeches at the drive-through.

Loop: the last shot is the hook framing again (the glove gripping the register under the spotlight), and the speech starts over.

## Facts and sources

| Claim | Source |
|---|---|
| "Sir, this is a Wendy's" is the reply to someone delivering a strange monologue to a fast-food worker; an offshoot of "Sir, this is an Arby's" (Twitter, 2011 to 2012), likely from The Office (2008), spread on Reddit from 2019 | Know Your Meme, https://knowyourmeme.com/memes/sir-this-is-a-wendys ; Know Your Meme explainer, https://knowyourmeme.com/editorials/guides/what-does-sir-this-is-a-wendys-mean ; Daily Dot, https://www.dailydot.com/memes/sir-this-is-a-wendys-meme/ |
| The form: an earnest corner-coach speech, 1.5M views, Nov 10 | `ops/research/2026-11-12-blind-trend-test.md`, idea 2 |

No numbers are claimed. "ROUND 12", the 0:59 timer and "number six" are props and an order, not facts.

## Assumptions spelled out

- The restaurant is named only in the line. No logo, mascot, menu art, red-and-white colors or anything that copies the brand: the set is navy, cream and yellow, with a generic menu.
- The coach and cashier are objects, so nobody real is shown.

## Shot sheet (ops/direction.md)

**Look.** Navy field #0E1530 (walls), cream #EDE6C8 (counter, register), coach blue #2461D8, and white spotlight. **Accent kept back: warm yellow #F7B815**, the menu board's light strip, which switches on for the first time at the big moment along with the plain ceiling lights.

**Big moment:** "Wendy's" (E["wendys"]). The crowd bed cuts to silence on "Sir", 0.4 s still, and on "Wendy's" the boxing spotlight look (a hard 2D vignette over the frame) snaps off, the flat ceiling panels and the yellow menu strip come on, and the whole ordinary restaurant is visible. The biggest change in light and sound in the reel. Everything before it is one pool of light in the dark.

Intensity: 3, 4, 3, 4, 5, 2, 3.

| # | Starts | Eye on screen | Light | Depth (fg / subject / mid / bg) | Lens, height, move | Beat |
|---|---|---|---|---|---|---|
| 1 hook | 0 | the glove gripping the register over the counter (0.5, 0.52) | the spotlight pool on the two, the rest black | rope / glove and register / counter / menu board with ROUND 12 and 0:59 | 28 mm, chest height, side-on, symmetrical, locked off | the bell on frame 1; the glove already mid-shout (thumbnail) |
| 2 face | "They" | the glove's face, mouth wide (0.5, 0.48) | spot, from above | rope blur / glove face / register edge / black | 55 mm, close, locked, kick on "soft" | each "Too" a small push of the glove toward camera |
| 3 cashier | B | the register's flat face (0.5, 0.5) | spot | the glove's shoulder blur / register / counter / black | 40 mm over the glove's shoulder, still | blank stare; one slow blink |
| 4 hero | "Tonight" | the glove, low angle against the spot (0.5, 0.46) | spot as a halo from behind | rope / glove / spot flare / black ceiling | 24 mm, low, slow push | the crowd swells on "yours" |
| 5 Wendy's | C | the register, frontal (0.5, 0.5) | spot, then on "Wendy's" the flat ceiling lights and the yellow menu strip | counter / register / menu board / back wall | 35 mm, locked off, symmetrical | silence on "Sir", 0.4 s still, the lights on the hit |
| 6 order | D | wide two-shot, both small under flat light (0.5, 0.55) | flat fluorescent | tray / glove and register / tables / wall | 28 mm, still, deadpan | the glove lets go, quieter; a receipt prints on "champion" |
| 7 loop | E | back to the hook framing (0.5, 0.52) | the spotlight again | as shot 1 | as shot 1 | cuts back into frame 0 |

## Scroll patrol

See `2026-11-15-sir-wendys-patrol.md`.

## Status (finished Nov 20)

- **The Nov 14 make run died.** It rendered all 608 frames and `out/wendys/wendys.mp4` (9:05 pm ET) and then stopped before QA and queueing; the laptop restarted on Nov 19. Its `pipeline/out/MAKING` lock was left behind and blocked every make run from Nov 15 to Nov 20. The lock was removed on Nov 20 once no Python or Blender process was running.
- **Finished from the render:**
  - `qa_voice` PASS (spread 10%), and `qa_audio` reports no steady tones.
  - Whisper on the final mix matches the script word for word.
  - Watched on a 2 fps sheet against the shot sheet.
  - The render came out at -15.4 LUFS with a -0.1 dBFS peak, so it was normalized to -13 LUFS / -1 dBTP for `videos/2026-11-15_Sir_This_Is_A_Wendys.mp4`.
- **Queued** `ready` for Nov 20, 12:30 pm ET. Posting is paused (`ops/PAUSE`, Austin, Nov 14) until he says the photos are done, so it waits for that.
