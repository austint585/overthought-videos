# Your AI picture did not drink a bottle of water

- **id:** 2026-11-02-ai-water-bottle
- **Status:** Austin approved the script and the look test ("Yes, build it", Nov 2). Rendered 63 s, QA passed, queued under the standing approval.
- **Files:** `pipeline/render_water.py`, `pipeline/water_scene.py` (the pastel toy kit), `videos/2026-11-2_Your_AI_Picture_Did_Not_Drink_A_Bottle.mp4`.
- **Voice note:** line 2 is voiced as three takes (Chatterbox ran on into nonsense after the long sentence), with "2023" spelled out as "twenty twenty three". `cb_worker.py` skips wavs that already exist, so delete `out/water/voice` after any script change or old takes come back.
- **Source idea:** Austin in chat, Nov 2: AI uses less water than people think, images don't use 500 mL, and it's all a closed loop anyway.
- **Change from the idea:** the first two points hold up. "It's all a closed loop" does not (see below), so the script says what is true and uses it as the turn.
- **Why people care:** the bottle-of-water line is one of the most repeated arguments about AI, and both sides get something wrong, so both sides have a reason to comment or send it.
- **Format:** debunk with objects as the cast, yelled Chatterbox (straight educational, Austin's tone rule). Proposed look: pastel toy (@howyourhouseworks.au), numbers on in-scene signs. This would be the first test of that look, so a 5-second test comes before the full render.
- **Odd detail for comments:** a toilet flushes and a sign counts up 209 tiny framed AI pictures going down with it.

## Script (about 40 s yelled, last line loops into the first)

1. That AI picture you just scrolled past did not drink a whole *bottle* of water!
2. The bottle comes from a 2023 paper about text answers, and it says one bottle for *10 to 50* answers. It has no number for pictures!
3. Nobody has measured one picture directly. Do the math, power plant included, and you get about *12* milliliters!
4. The highest number we could find is *29*. That's two tablespoons!
5. One flush of your toilet is *6 liters*. That's 200 AI pictures, gone!
6. But if your friend says it's all a *closed loop*, your friend is wrong too!
7. Lots of data centers *evaporate* water on purpose. Google loses about 80 percent of the water it takes in!
8. Microsoft's no-water sites start coming online in *late 2027*, and they use more electricity!
9. And in one estimate, most of the water isn't at the data center. It's at the *power plant*!
10. Your one picture is nothing. The town next to a *giant* data center still has a real question!
11. But no, that picture did not drink a bottle of water!

## Shots

| Line | Shot |
|---|---|
| 1 | A framed picture on a table, a 500 mL bottle beside it, on frame 1 |
| 2 | Paper on the table, bottle pours into 10 to 50 small cups |
| 3 | Eyedropper fills a tiny glass, sign counts up to 12 mL |
| 4 | Two tablespoons, sign reads 29 mL |
| 5 | Bathroom cutaway, the flush, sign counts up to 209 pictures |
| 6 | Hard cut to a closed pipe loop, red X |
| 7 | Cooling tower with steam leaving the top, sign reads 80% |
| 8 | Sealed loop with a calendar at late 2027, power meter climbing |
| 9 | Pull back to a power plant with its own steam |
| 10 | Small town beside a huge building |
| 11 | Back to the picture and the bottle, matching frame 1 |

## Facts and sources

| Claim | Source |
|---|---|
| A 500 mL bottle for "roughly 10 to 50 medium-length responses", GPT-3, 2023 | https://arxiv.org/html/2304.03271v5 |
| That paper has no per-image figure | https://projetcelsius.com/en/blog/ai-image-carbon-footprint/ |
| No study measures water per image | https://projetcelsius.com/en/blog/ai-image-carbon-footprint/ |
| 2.9 Wh per image, measured on open generators | Luccioni, Jernite and Strubell 2024, via Projet Celsius above |
| Google on-site water 1.15 L/kWh; consumes 80% of what it withdraws; consumption means evaporated | https://arxiv.org/html/2508.15734v1 |
| Grid water 3.1 L/kWh | https://arxiv.org/abs/2304.03271, via Projet Celsius above |
| Federal toilet limit 1.6 gallons per flush | https://www.epa.gov/watersense/residential-toilets |
| Microsoft closed loop: new designs since Aug 2024, sites online from late 2027, more energy than evaporative | https://www.microsoft.com/en-us/microsoft-cloud/blog/2024/12/09/sustainable-by-design-next-generation-datacenters-consume-zero-water-for-cooling/ |
| 16.9 mL per GPT-3 response: 2.2 on site, 14.7 at the power plant (87%) | https://spectrum.ieee.org/ai-water-usage |
| Google's largest site consumes 2.8 million gallons a day (basis for line 10) | https://mostpolicyinitiative.org/science-note/data-center-water-use/ |
| About two tablespoons (29 mL) of electricity-associated water per image, UNU-INWEH, June 2026. The PDF was too large for our fetch tool, so its method is unread; the numbers imply about 10 L/kWh | https://unu.edu/inweh/news/environmental-cost-of-AIs-Enrgy-Use-carbon-water-and-land-footprints |

## Math, written out

- 12 mL per image: 2.9 Wh x 1.15 L/kWh = 3.3 mL on site, plus 2.9 Wh x 3.1 L/kWh = 9.0 mL at the power plant, 12.3 mL total. Our own calculation, close to Projet Celsius's "about 12 mL". Line 3 says "do the math" for that reason.
- 200 pictures per flush: 1.6 gallons = 6.06 L, and 6,057 mL / 29 mL = 209. At 12 mL it would be about 500. We use the less flattering number.
- Two tablespoons: 2 x 14.8 mL = 29.6 mL.

## Assumptions and known weak spots

- The 2.9 Wh is from open generators, not ChatGPT or Midjourney, and no company publishes a per-image water number. The real figure could differ either way.
- This is per picture only. It leaves out training and hardware manufacture. The Google 1.15 L/kWh is one company's fleet; LBNL's US average is lower, about 0.36 L/kWh, via https://andymasley.com/visuals/water
- The 87% power plant split is one estimate for GPT-3 in 2023. Line 9 says "in one estimate" for that reason.
- US data center direct water is growing: 17.4 billion gallons in 2023, projected 38 to 73 billion by 2028 (MOST Policy Initiative above). Line 10 keeps the video from implying the total is no issue.
- I found no source showing people say "500 mL per image" specifically. The hook denies the claim and doesn't say how common it is. Projet Celsius does document an unsourced "2 to 5 litres per image" going around.
- The Washington Post "519 mL for a 100-word email" figure is left out: the article blocked us and we couldn't read its wording.
- This account is made with AI, so it has a stake in the answer. The caption says so.

## Caption

"Your AI picture didn't drink a bottle of water. It's not all closed loop either. This account is made with AI, so go check us. #ai #datacenters #water"
