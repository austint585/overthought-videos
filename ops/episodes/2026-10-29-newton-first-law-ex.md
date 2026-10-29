# Newton's first law of the ex

- **id:** 2026-10-29-newton-first-law-ex
- **Source idea:** the daily report of Oct 28. Schrödinger's Situationship is the breakout (274K plays, 10.7K shares) and the report suggests more of that style: a real physics rule applied to a dating situation, deadpan, with a tag-a-friend caption. Not from a DM. Satire, so the deadpan voice is right.
- **Format:** clay deadpan short, about 30 s, on the clay bedroom from "The same hour twice" (`pipeline/newton_scene.py` reuses that set). The ex is a heavy purple clay ball at rest on the floor among dust bunnies. He posts someone new (a clay photo pops out of his phone), a red clay arrow (the outside force) knocks the ball rolling to the foot of his bed, the clock goes 2:47 to 2:58 and "hey stranger" pops over his phone. Then a bright orange "you" ball rolls across the floor and never stops. He sits up and tosses the phone onto the blanket.
- **Files:** `pipeline/render_newton.py`, `pipeline/newton_scene.py`.

## Script (render_tap markup)

1. Your *ex* runs on *Newton's first law.*
2. In *1687,* Newton wrote that a body at *rest* stays at *rest,*
3. unless an *outside force* makes it *change.*
4. Your ex has been at rest for *seven months.* No texts. No likes. *Nothing.*
5. Then you post someone *new.*
6. *Outside force:* applied.
7. Eleven minutes later. *Hey stranger.*
8. But the law works both ways. A body in *motion* stays in *motion.*
9. So if you're *moving on,* keep *moving.*
10. Do not *reply.* Newton would not *reply.*

## Facts and sources

| Claim | Source |
|---|---|
| Newton's first law is Law I of the Principia, published 1687: every body perseveres in its state of rest or of uniform straight motion except insofar as it is compelled to change its state by impressed forces | Cohen and Whitman translation (1999), quoted in https://www.scientificamerican.com/article/mistranslation-of-newtons-first-law-discovered-after-nearly-300-years/ and https://arxiv.org/pdf/2112.02339 |
| The same law covers a body in uniform motion: it keeps moving unless a force changes that | same sources |

## Assumptions, written out

- "Unless an outside force makes it change" is the plain version of Law I. The Scientific American piece notes that "unless" comes from Motte's 1729 translation and that "except insofar as" is closer to Newton's Latin; for a body that starts at rest the two read the same, so the short version stays.
- The ex as a body at rest is the joke's analogy, said with a straight face; the script never claims physics governs people. Same device as Schrödinger's Situationship.
- "Seven months", "eleven minutes" and the 2:47 post / 2:58 text are a made-up example, not data. The card's zeros count the example (no texts, no likes); its source line cites Law I.
- "Velocity: 0 m/s" on the card is the joke's reading of "at rest".
- "Newton would not reply" is the punchline, not a historical claim.
- The photo in the post is two generic clay figures, no real people. No app's branding on the post or the text bubble. Newton is a historical figure cited for his published work; he is not shown.

## Caption

Newton, 1687: a body at rest stays at rest until an outside force acts on it. Post someone new and watch it work. Tag the friend who just got a hey stranger text. #physics #newton #3danimation

## QA (Oct 29)

- `videos/2026-10-29_Newtons_First_Law_Of_The_Ex.mp4`: 29.5 s, 1080x1920, 60 fps, 11 MB.
- Audio: -12.9 LUFS integrated, peak -0.9 dBFS, `qa_audio.py` finds no steady tones.
- First preview fixed: the "you" ball rolled 10 m in a 6 m room and took the tracking camera through the wall (now 0.5 m/s, stays inside), the ex close-ups were too tight and pushed the tag into the captions, the face shot sat inside the bed, the orange ball read dark (now a little self-lit), and the force arrow was too small (1.8x).
- Frames checked at the hook, the ex at rest, the force hit, "hey stranger", the rolling "you" ball and the end card: captions in the top third, nothing important below y 1540.
