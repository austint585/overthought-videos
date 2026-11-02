# Crime is legal for 24 hours (your friend still returns the cart)

- **id:** 2026-11-02-crime-legal-cart
- **Status:** dropped by Austin, Nov 2, never made. I pitched this without watching the reference: he says the reel was funny because it subtly referenced an interview where a rapper (he thinks Lil Yachty) said what he would do if crime were legal for a day. Lesson: watch a reference and find what the joke is before writing from it.
- **Source idea:** Austin's DM, Oct 29: an @what.if.da1ly "what if crime was legal for a day" reel, with his note to bait with a big what-if and turn it into something funny. Our own script; nothing lifted from that reel.
- **Why this one:** our own numbers say sends decide it (every reel over 30K has 5 to 10% of plays as shares). This premise makes viewers think of one specific friend. The big what-if is the hook; the rule follower is the joke.
- **Format:** deadpan joke, about 30 to 40 s, flat Kokoro voice (the voice on all four hits). No yelling: it is satire, and nothing here is presented as real fact.
- **Look:** the smooth low-poly toy look of @howyourhouseworks.au (`ops/style.md`, Nov 2), not pixel voxel, not clay, not the dark studio. Plain flat colors, soft pastels, bright even light at dusk, bevelled chunky character, big condensed title with one colored word. Numbers on in-scene signs ("HOURS LEFT 23").

## Build order

1. New kit, `pipeline/toy.py`, on `bkit.py`. Time 10 fixed frames with raytracing off, then 8 to 16 samples, then motion blur off, and keep whatever survives a look check. Target under 1.5 s a frame.
2. Five-second look test of one shot. Put it next to the frames in `pipeline/out/watch/DfOIcgPiWAO/sheet.png` and send it to Austin. Don't render the full episode if it looks worse than the reference.
3. Full episode with a new set per beat. Reuse nothing from the bedroom or the bulb studio. Camera on the near-plane fix (`clip_start = 0.002` on close-ups).

## Script (draft, tighten for rhythm)

1. Crime is legal for twenty four hours. Here is what your friend does.
2. Hour one. The city is on fire. He returns his shopping cart.
3. Pushes it all the way into the corral.
4. Hour six. A man walks out of the jewelry store carrying the jewelry store. Your friend holds the door.
5. Hour twelve. Someone steals a city bus. He gets on and pays the fare.
6. Three a.m. No cops exist. Empty road. He stops at the stop sign. Full stop. Uses his blinker.
7. Hour twenty three. He finally snaps. He tears the tag off a mattress.
8. At midnight crime comes back. He turns himself in.
9. The officer asks why. He says he wants to get ahead of this.

Add one current slang or internet reference only if a trend check finds one that fits; Austin wanted a niche reference, and don't force it.

## Caption

Draft: "Crime is legal for one day and he's still pushing the cart into the corral. Tag the friend who would. #whatif #brainrot #3danimation"

## Facts

None presented as real: this is an obvious joke. No real people.
