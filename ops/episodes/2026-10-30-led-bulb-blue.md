# Your LED bulb starts out blue

- **id:** 2026-10-30-led-bulb-blue
- **Format:** everyday-object explainer on the product-studio kit (`pipeline/render_bulb.py`, `pipeline/bulb_scene.py`), about 60 to 70 s, 30 fps. Straight educational, so per Austin's tone rule the narrator yells the whole way through (Chatterbox at high exaggeration, our own synthetic reference voice).
- **Why people care:** everyone has one overhead right now. The surprise (white light made from blue) is checkable and shareable, and the payoffs explain things viewers have noticed: cheap LED light looks cold, the bulb has fins, the base gets warm. The format follows @speedy_devv's steady ~300K reels (see `ops/research/2026-10-29_Benchmark_200K_Accounts.md`), on an object he has not covered.
- **Not from a DM.** Picked after Austin's Oct 29 call to go back to research and benchmark against steady ~200K accounts.

## Facts and sources

1. Most white LEDs are a blue indium gallium nitride (InGaN) chip under a yellow phosphor, cerium-doped yttrium aluminum garnet (YAG:Ce). The phosphor turns part of the blue into yellow, and blue plus yellow reads as white. Chen, Lin, Yeh and Liu, "Light Converting Inorganic Phosphors for White Light-Emitting Diodes", *Materials* 3(3), 2172-2195 (2010), section 2: https://pmc.ncbi.nlm.nih.gov/articles/PMC5445896
2. The blue-plus-yellow mix renders colors poorly, and heat dims the phosphor ("thermal quenching"). Same paper, section 2. The DOE describes the same method as phosphor conversion of colored LED light to white: https://www.energy.gov/eere/ssl/led-basics
3. Heat sinks pull heat off LEDs to prevent LED failure. US patent 9,206,972 (compact LED device), background: https://patents.justia.com/patent/9206972
4. The driver sits inside the heat sink and turns mains AC into low-voltage DC for the LEDs. US patent application 2010/0277067 (dimmable LED luminaire): https://patents.justia.com/patent/20100277067. AC-to-DC through a diode bridge and filter: https://circuitdigest.com/comment/35525
5. Good white LED products are expected to last 30,000 to 50,000 hours, against about 1,000 hours for a typical incandescent. DOE, LED Basics: https://www.energy.gov/eere/ssl/led-basics

## Assumptions, written out

- The bulb shown is Poly Haven's CC0 "Lightbulb Led" model. Its inside (spreader, LED ring, driver parts) is modeled by us as a generic layout, labeled "Cutaway illustration". Real bulbs vary.
- The LED package is drawn as a generic 2835-size SMD LED (2.8 x 3.5 mm), magnified about 100x, labeled "Magnified illustration, not to scale".
- The spectrum card is a schematic of a phosphor-white LED (a blue spike near 450 nm and a broad yellow hump), not a measurement of this bulb.
- The lifetime line uses the DOE range and says "can last", because life depends on heat and use.

## Script (yelled)

1. The light in your LED bulb starts out blue.
2. Not white. Not warm. Blue.
3. Inside, a ring of tiny chips is glowing pure blue.
4. Every chip sits in a little cup of yellow powder called phosphor.
5. The phosphor eats some of that blue and spits it back out as yellow.
6. Blue plus yellow hits your eyes, and your brain just calls it white.
7. That's why cheap LED light looks a little cold. There's barely any red in it.
8. And heat makes the phosphor dimmer and kills the chips.
9. So those fins on your bulb aren't decoration. They're a heat sink, pulling heat off the chips.
10. The base isn't empty either. There's a tiny power supply turning your wall's AC into the low DC the chips need.
11. Keep it cool and it can last thirty to fifty thousand hours. An old bulb? About a thousand.
12. All of that, just so the light in your LED bulb can start out blue.

Line 12 runs back into line 1, so the reel loops.

## Shots

| Line | Shot |
|---|---|
| 1 | Hanging bulb, lit warm white, push-in (the look-test shot) |
| 2 | Same bulb flashes blue, with a hard cut on each word |
| 3 | Cutaway from below: the LED ring glowing blue, no phosphor yet |
| 4 | Macro: the LED package sectioned, phosphor cup fills in |
| 5 to 6 | Macro: blue photons go in, yellow comes out, mixing to white; 2D blue + yellow = white card |
| 7 | Spectrum card (2D): blue spike, yellow hump, almost no red |
| 8 | Cutaway: the LED board glows hot orange, then dims |
| 9 | Fins macro: heat flowing out along the fins |
| 10 | Neck cutaway: the driver, with a small AC wave turning into a flat DC line (2D) |
| 11 | Poly Haven's incandescent bulb next to the LED bulb; hour counter; the old one burns out at 1,000 |
| 12 | Pull back to the hanging bulb, matching line 1 for the loop |

## Caption

Draft: "The white light in your room is blue light wearing a yellow coat. Send this to someone who still thinks LEDs make white. #howitworks #led #science"
