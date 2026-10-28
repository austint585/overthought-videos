# Curious George learns about hypergamy

- **id:** 2026-10-27-george-hypergamy
- **Source idea:** Austin's DM, Oct 27 evening (https://www.instagram.com/p/DfAT1F2AH6X/, @larpforlarp, 33 s), with "immediately make this". The creator talks over a picture of Curious George and the man with the yellow hat and asks what would happen if George learned about hypergamy. Austin asked in chat to animate it and post it right away.
- **Format:** 3D voxel brainrot explainer (the voxel kit, moved into the roommate's city apartment at night), with a tier list, a height chart on the wall and a real height study.
- **Length:** 38.3 s.

## Script (render_tap markup)

1. What happens when *Curious George* learns about *hypergamy?*
2. Hard case. George is a *monkey.*
3. Except he has *no tail,* so technically he's an *ape.* Mislabeled since *1941.*
4. By the books, he's a *mid-tier* primate. No job. No car. Lives with his *roommate.*
5. He also comes up to the roommate's *belt.* *Not ideal.*
6. Because the roommate is the *Chad in the yellow hat.* *Tall,* plus the *hat.*
7. George is getting *height-mogged* at *home.*
8. In a *1980* study of *720* couples, the woman was taller in *one.*
9. So once George learns about *hypergamy,* it's *over.*
10. The Chad in the yellow hat? *Ascending.*
11. Peer review is *pending.*

Same beats as the reference, in the same order (the question, "he's a monkey", mid-tier by the books, his height is not ideal, the yellow-hat guy is much taller, George would not last, the yellow-hat guy would do well, a fake-academic sign-off). Every line is ours. Left out: the reference's "foid" line (written while RULES.md still banned the word; Austin lifted that on Oct 27 after the script was locked), its "my research is ongoing" sign-off, and its "six hats tall" bit. Added: the no-tail fact, the tier list, the hat landing on screen and the 1980 study.

## Facts and sources

| Claim | Source |
|---|---|
| The first Curious George book came out in 1941 (by Margret and H. A. Rey) | https://en.wikipedia.org/wiki/Curious_George |
| George is drawn with no tail; apes have no tails and most monkeys do, so by that rule he reads as an ape | University anthropology course blog: https://www.poweredbyosteons.org/2013/06/is-curious-george-monkey-or-ape.html |
| In a 1980 study of 720 couples, the woman was taller in only one | Gillis, J. S. and Avis, W. E. (1980), "The male-taller norm in mate selection", Personality and Social Psychology Bulletin. Summarized with the 1-of-720 figure at https://statmodeling.stat.columbia.edu/2024/04/29/boris-and-natasha-in-america-how-often-is-the-wife-taller-than-the-husband/ and https://pmc.ncbi.nlm.nih.gov/articles/PMC3546926 |

## Assumptions, written out

- **"Technically an ape"** rests on the tail rule. It has exceptions (the Barbary macaque is a monkey with no tail), and the Reys always called George a monkey. The script says "technically" and the pill says "APE (TECHNICALLY)".
- **The 1980 study** used heights from 720 couples' bank account forms in the US and UK. A Columbia statistics blog questions its spread estimates; the 1-in-720 count itself is what the paper reports, and that is all the script claims.
- **Heights in the scene are the drawing, not measurements.** George is built to reach the roommate's belt, as he does in the book art. No height in feet is claimed (the reference's "two feet" came from a search snippet with no real source).
- **The tier list is the joke** (silverback, orangutan, George, lemur, sea monkeys). "No job, no car, roommate" describes the books' setup as a joke.
- "Hypergamy", "height-mogged", "Chad", "ascending" are internet slang used deadpan; the joke is on the slang and on George, not on women.

## Rights and content lines

- George and the roommate are our own blocky voxel figures (brown monkey with tan face, tall man in a yellow suit and hat). No book art, no frames or photos from the reference reel, no real people.
- Nothing sexual.

## Visuals

Voxel apartment at night: wood floor, red rug, teal couch, a window onto lit towers, a floor lamp, a plant, a door to a lit hallway, and a height chart with ticks on the wall. Shots: hook (George reading his phone), close on George, his back (no tail), wide room as the roommate walks in, the height chart with both of them (marks appear for George, the roommate, then the hat), a low shot up at the roommate for "height-mogged", the 720-couple chart, George slumped on the floor with rain on the window and the lights dimmed, the roommate rising in a gold glow, a wide end shot.

## Sound

Room hum, rain on the window from "it's over", a thunder rumble, the hallway door, flip-flop steps, a tape measure on the height line, swooshes and a pop for the hat, a bass hit on "height-mogged", denies on "no tail", "no job", "no car", "not ideal", a power-up on "ascending", a horn braam under the last lines. All from the Sonniss GDC 2026 bundle via `pipeline/sfx.py`.

## Caption

"Curious George has been getting height-mogged by his own roommate since 1941. Tag the friend who wears a hat for the extra inches. #curiousgeorge #brainrot #3danimation"

## Posting

Austin, in chat on Oct 27 at about 6:30 pm: animate it and "get it posted immediately". That is a fourth post on Oct 27, past the standing 3-a-day cap, on his direct instruction. The Meta app is still blocked, so it goes out through vidIQ as a Trial Reel.

## QA

Passed Oct 27 (evening, laptop). 38.3 s, 1080x1920 60 fps, 14.6 MB, -13.2 LUFS integrated, peak -0.8 dBFS. Frames checked at 0.3, 6.5, 12.2, 17.8, 21.95, 23.7, 29.3, 32.6, 34.8 and 37.8 s: title readable on frame 1, captions in the top third, tier list, chart marks and the 720 grid readable, pills above y=1540. The Blender pass took about 62 minutes (1.6 s a frame), slower than the steak hall.

## After posting

- Posted 8:15 pm Oct 27 as a regular Reel through vidIQ: https://www.instagram.com/reel/DfBHw6viI7z/ . At 30 minutes: 60 plays, 2 likes, 0% skip, 104% average watched (people rewatch it).
- Austin heard a buzz (the electric hum bed) and two misread words: "Lives" as the plural of life, "hypergamy" as hyper-GAY-mee. Fixed in the pipeline (LEXICON, `{/IPA/}`, qa_audio.py). Austin chose to keep the original up; a fixed render (`Lives{/lˈɪvz/}`, hy-PUR-guh-mee, no hum) is kept as a spare in case we need it.
