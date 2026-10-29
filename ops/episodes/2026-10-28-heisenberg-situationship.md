# The Heisenberg situationship

- **id:** 2026-10-28-heisenberg-situationship
- **Source idea:** the daily report of Oct 28. Schrödinger's Situationship is the account's breakout (274K plays, 10.7K shares), and the report suggests a second episode in that style: a real physics rule applied to a dating situation, deadpan, with a tag-a-friend caption. Not from a DM.
- **Format:** clay deadpan short, 40 s, on the clay bedroom built for "The same hour twice" (`pipeline/heis_scene.py` reuses `dst_scene.py`'s set). A guy in bed at 2:47 a.m. on his phone. A glowing particle hangs over the bed with arrows spinning around it; then a red location pin pops out of his phone, perfectly still, while the arrows of "where this is going" spin everywhere. He sits up worried, flops back, refreshes the map. Cuts every 2 to 3 s, after the @seethroughworks reel Austin sent tonight (see `ops/style.md`).
- **Files:** `pipeline/render_heis.py`, `pipeline/heis_scene.py`.

## Script (render_tap markup)

1. Every *situationship* runs on the *Heisenberg uncertainty principle.*
2. In *1927,* Heisenberg showed you can't pin down a particle's *position* and its *momentum* at once.
3. The better you know *where* it is, the less you know *where it's going.*
4. So she *shares her location.*
5. Position: *known.* Down to the *driveway.*
6. Momentum: *undefined.*
7. Exclusive? *Unknown.* Meeting the parents? *Unknown.* Is this going *anywhere?* Physics says you *can't know.*
8. The uncertainty never drops below *h-bar over two.* That's a decimal point, *thirty-four zeros,* then a five.
9. Which is also how much *clarity* you're getting.
10. Stop *refreshing* the map. Measuring it makes it *worse.*

## Facts and sources

| Claim | Source |
|---|---|
| Heisenberg published the uncertainty principle in 1927 (Zeitschrift fur Physik vol. 43, pp. 172-198, received March 23 1927): position and momentum can't both be known precisely | AIP history exhibit, https://history.aip.org/exhibits/heisenberg/uncertainty-relations.html |
| The bound is (spread in x) times (spread in p) >= h-bar / 2; the standard-deviation form is Kennard's, 1927 (Z. Physik 44) | https://en.wikipedia.org/wiki/Earle_Hesse_Kennard, https://arxiv.org/pdf/1904.06139 |
| h = 6.62607015 x 10^-34 J s exactly (2019 SI), so h-bar = h / 2 pi = 1.054571817 x 10^-34 J s and h-bar / 2 = 5.27 x 10^-35 J s | NIST, https://pml.nist.gov/cgi-bin/cuu/Value?h and https://www.physics.nist.gov/cuu/pdf/wall_2022.pdf |
| 5.27 x 10^-35 written out: a decimal point, 34 zeros, then 527 | arithmetic from the line above |

## Assumptions, written out

- "Momentum" as "where it's going" is the joke's analogy for a relationship, said with a straight face; the script never claims physics applies to dating. Same device as Schrödinger's Situationship.
- "Pin down position and momentum at once" is the plain version of the inequality; the on-screen card shows the actual bound and cites Kennard.
- "Measuring it makes it worse" plays on the measurement disturbance in Heisenberg's original microscope argument; as physics it is a loose paraphrase and is the punchline, not a claim.
- h-bar / 2 has units (J s); "how much clarity you're getting" is the joke. The card shows the units.
- The particle and arrows are illustrations, not to scale. The location pin is a generic map pin, no app's branding.
- No real people. Heisenberg is a historical figure cited for his published work; he is not shown.

## Caption

In 1927 Heisenberg proved you can know where something is or where it's going, never both. Shared locations prove it nightly. Tag the friend who checks the map at 2 a.m. #physics #situationship #3danimation

## QA

Rendered Oct 29 on the laptop (Eevee, 2,387 frames). 39.8 s, 14.6 MB, -13.3 LUFS, peak -0.6 dBFS, qa_audio says no steady tones. Preview pass moved the two pin tags below the pin, off the captions. Final frames checked at 1, 9.5, 16, 19, 22, 30, 34.5 and 38 s: hook readable, cards clear of the subject, captions in the top third, end pill and handle present. Queued ready for Oct 29 11:30 am ET.
