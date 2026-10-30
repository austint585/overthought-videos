# Why a fork sparks in the microwave

- **id:** 2026-10-28-fork-sparks
- **Source idea:** Austin's DM, Oct 27 (https://www.instagram.com/p/De_42nKxoyZ/, @how_it_secretly_works): more 3D "how the stuff you use daily works" episodes with a hook that grabs. Everyone has heard "don't put a fork in the microwave"; few know why.
- **Format:** everyday-object explainer on the product-studio kit (rebuilt Oct 29 from the Oct 28 voxel draft, which was never rendered: Austin retired the voxel look). Poly Haven's CC0 vintage microwave on the walnut desk for the outside shots, a cutaway oven cavity, plate and fork modeled in code for the inside, macro shots of the tines. Yelled Chatterbox narration (Austin's rule for straight educational reels). Hook: a surprising true claim about something you own; the last line repeats the first so the reel loops. Odd detail for comments (Austin's Oct 29 @kaleidoexplains note): the foil ball hops as it crackles.

## Script (render_tap markup)

1. Your fork doesn't spark because it's metal. It sparks because it's *pointy.*
2. Your microwave fills with waves that flip back and forth *2.45 billion* times a second.
3. Your food soaks them up. That's how your leftovers get *hot.*
4. But metal can't soak them up, so it *reflects* them off its surface.
5. Every flip shoves the *electrons* in your fork one way, then the other.
6. And they pile up wherever the metal comes to a *point,* like the *tips* of your tines.
7. Right at a sharp tip, the electric field gets strong enough to rip electrons off the *air.*
8. That air turns into *plasma.* That's the *spark* you see.
9. Your smooth *spoon* spreads the charge out, so it usually stays *calm.*
10. Crumpled *foil* is nothing but points. That's why it *crackles* like crazy.
11. Leave it running and those sparks can *scorch* your oven, or even start a *fire.*
12. So your fork doesn't spark because it's metal. It sparks because it's *pointy.*

## Facts and sources

| Claim | Source |
|---|---|
| Microwaves are absorbed by food (mostly its water) and reflected by metal | FDA, https://www.fda.gov/radiation-emitting-products/resources-you-radiation-emitting-products/microwave-ovens |
| Ovens run at 2,450 MHz, so the field flips direction 2.45 billion times a second | Health Physics Society, https://hps.org/hpspublications/articles/microwaveoven/ (2,450 MHz = 2.45 billion cycles per second) |
| The field moves electrons in the metal; charge concentrates at points and edges, where the field gets strong enough to ionize the air and arc | NPR, "Microwave Antics: Don't Stick a Fork in It" (Nov 3 2006), https://www.npr.org/6429308; https://www.scienceabc.com/eyeopeners/not-good-practise-put-metals-microwave-oven.html |
| Smooth metal without points (a spoon) often does not spark; crumpled foil, full of edges, does | ScienceABC article above; NPR piece above |
| Arcing can burn the cavity walls and set things on fire | ScienceABC article above; NPR piece above |

## Assumptions, written out

- "Tear electrons off the air" is the plain version of ionization (dielectric breakdown); "plasma" is the ionized air in the spark.
- "Often stays calm" is deliberately hedged: a smooth spoon can still arc, for example near the wall.
- Scale: the fork, spoon, foil and mug are life size; the microwave model is scaled to a normal countertop size. Electrons, air molecules, sparks and flame are illustrations, and the oven's inside is a cutaway with the front wall removed.
- "The waves flip 2.45 billion times a second": the field reverses direction at 2,450 MHz; the wave on screen is schematic.
- "Doesn't spark because it's metal": metal is necessary, but the hook is about why it sparks (sharp points concentrate the field). Smooth metal can still arc in some cases, which is why the spoon line says "usually".
- The scorch and flame are shown as what can happen, not a claim that one fork always does it.

## Caption

"Your fork sparks in the microwave because it's pointy, not just because it's metal. Send this to the friend who still tries it. #howitworks #science #physics"

## Production status (Oct 30, 2:45 am ET run)

Rebuilt on the product-studio kit (`pipeline/render_fork.py`, `pipeline/fork_scene.py`). Narration is voiced and cached in `pipeline/out/fork/voice` (56.4 s; three lines reworded after Chatterbox repeated "It reflects them" and "back and forth"). Not rendered yet: the run ran out of time (the stomach episode took 2.8 h at 8.6 s a frame, so this one needs about 3.5 h).

Before the full render, fix and re-preview:
- Listen to line 6: Whisper heard "mental" for "metal". Re-voice it (delete `out/fork/voice/l05_*`) if it really says that.
- `spark_tip`, `tips`, `spark`, `breakdown`: the macro shots are out of focus (the camera focuses on the target point, but the fork sits off it) and the arc reads as a white blob. Focus on `tip_world(k)`, use a thinner arc, cut the arc's emission.
- `scorch`: the burn is a flat black disc and the flames are plain cones. Soften the burn edge (a ramp, not LESS_THAN) and use a noise-displaced flame or a few small arcs.
- `front`: the window shows nothing of the lit inside (the model's door is opaque behind the glass). Either clip the door material behind the glass or accept a dark window.
