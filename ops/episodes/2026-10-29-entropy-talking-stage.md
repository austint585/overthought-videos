# The entropy of the talking stage

- **id:** 2026-10-29-entropy-talking-stage
- **Source idea:** the daily report of Oct 28. Schrödinger's Situationship is the account's breakout (274K plays, 10.7K shares) and the report suggests more episodes in that style: a real physics rule applied to a dating situation, deadpan, with a tag-a-friend caption. Not from a DM. Satire, so the deadpan voice is right (straight educational episodes wait for a shouting voice, see `ops/style.md`).
- **Format:** clay deadpan short, about 36 s, on the clay bedroom from "The same hour twice" and "The Heisenberg situationship" (`pipeline/entropy_scene.py` reuses that set). A guy in bed at 2:47 a.m. A clay speech bubble over his phone shrinks day by day: a paragraph, "haha", "lol", "hbu", a thumbs up, then "Seen 2:47 AM". Beside it a tidy cube of 27 clay molecules drifts apart into disorder. He smiles, scratches his head, sits up at the thumbs up, almost texts first, then lets the phone sink to his chest.
- **Files:** `pipeline/render_entropy.py`, `pipeline/entropy_scene.py`.

## Script (render_tap markup)

1. Every *talking stage* obeys the *second law of thermodynamics.*
2. In *1865,* Rudolf *Clausius* gave it a name: *entropy.*
3. Leave a system *alone,* and its disorder only goes *up.*
4. Day one: *paragraphs.* Follow-up *questions.* Good morning *texts.*
5. Day four: *haha.*
6. Day nine: *lol.*
7. Day twelve: *hbu.*
8. Day fifteen: a *thumbs up.* To a *question.*
9. Clausius wrote that entropy tends to a *maximum.*
10. The only way to *reverse* it is to put *energy* in from *outside.*
11. And *nobody* is texting *first.*
12. Heat death of a conversation. *Seen,* *2:47 a.m.*

## Facts and sources

| Claim | Source |
|---|---|
| Rudolf Clausius coined the word "entropy" in 1865 | https://en.wikipedia.org/wiki/History_of_entropy, https://www.etymonline.com/word/entropy |
| His 1865 paper ends with two laws: the energy of the universe is constant, the entropy of the universe tends to a maximum | https://en.wikipedia.org/wiki/Rudolf_Clausius (Annalen der Physik, 1865) |
| Second law: in an isolated system entropy never decreases; lowering it locally takes energy or work from outside (Clausius statement: heat does not flow from cold to hot on its own) | https://en.wikipedia.org/wiki/Second_law_of_thermodynamics |
| "Heat death" is the name for the end state of maximum entropy | https://en.wikipedia.org/wiki/Heat_death_of_the_universe |

## Assumptions, written out

- The talking stage as an isolated system is the joke's analogy, said with a straight face; the script never claims physics applies to texting. Same device as Schrödinger's Situationship.
- "Its disorder only goes up" is the plain version of "entropy never decreases in an isolated system" (it can stay constant in an ideal reversible process; left out for length).
- Days 1, 4, 9, 12, 15 and the replies are a made-up example, not data. The card's "15 words" and "0 words" count the example texts on screen (the day-one bubble has 15 words; the thumbs up has none). The card's source line is for the "maximum" row.
- The molecules are an illustration of disorder, not to scale. Message bubbles carry no app's branding.
- No real people. Clausius is a historical figure cited for his published work; he is not shown.

## Caption

In 1865 Clausius named it entropy: leave a system alone and the disorder only goes up. Every talking stage since has confirmed it. Tag the friend who replies hbu. #physics #talkingstage #3danimation

## QA (Oct 29)

- `videos/2026-10-29_Entropy_Of_The_Talking_Stage.mp4`: 36.3 s, 1080x1920, 60 fps, 14 MB.
- Audio: -13.3 LUFS integrated, peak -0.9 dBFS, `qa_audio.py` finds no steady tones. Clausius said /klˈaʊziəs/ (forced), "hbu" spelled out.
- Frames checked at the hook, the molecule cube, the thumbs-up sit-up, the face shot and the end card: captions in the top third, nothing important below y 1540, card reads DAY 1 15 WORDS / DAY 15 0 WORDS / ENTROPY MAXIMUM.
