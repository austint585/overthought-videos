# What accounts that steadily get ~200K a reel do, and what we change (Oct 29, 2026)

Austin, Oct 29: we were repeating the same idea (physics rule + dating) on the same clay bedroom with the same opening shot, four posts in one day. He asked to redo the trend research, but against accounts that are *consistently* around 200K a reel (not one-off 3M hits), like @speedy_devv, then pick a new voice and a new animation approach from what they do.

## Who is consistently near 200K

Play counts read from each account's Reels tab on Oct 29 (last ~12 reels, pinned ones skipped). Median, not best.

| Account | Followers | Median of recent reels | What it is |
|---|---|---|---|
| @speedy_devv | 183K | about 300K (13K to 1.9M) | How the thing in your hand works. Product-render 3D cutaways, 75 to 85 s. |
| @justinbig03 "Fruits Universe" | 58K | about 280K (29K to 3.4M) | AI-generated Pixar-style fruit people in short soap-opera stories with a twist. Labeled AI-generated. |
| @anatoverse.3d | 10.5K | about 160K (9K to 3.7M) | AI-generated macro nature and body shots, 20 to 25 s. Tiny account, big views: format beats followers. |
| @learningwithlyrics | 973K | about 120K | 3D everyday-tech explainers. |
| @hisytstory | 810K | about 100K | 3D storytime, several posts a day. |

Not consistent (hit or miss, median 20K to 30K with some 300K to 900K hits): @how_it_secretly_works, @seethroughworks, @larpforlarp. @petersindex (the clay look) is a 46-follower account: a style reference, not a performance one.

Us, Oct 27 to 29: Schrodinger 404K (18.9K shares), Halloween Loadout 63K, Curious George 18K, then 1K to 3.6K for everything else. The four clay posts on Oct 29 got 167 to 1.6K.

## What the three benchmarks do (watched Oct 29)

**@speedy_devv, trackpad reel (353K, 85 s).**
- Hook: a surprising claim about something you are touching right now, then a question. The answer is teased in the first 7 s.
- Script: "you" or "your" in almost every line, then the mechanism one step at a time, then two or three consequences you can check yourself. The last line runs into the first, so the reel loops.
- Voice: warm, conversational, fast: about 200 words a minute (ours: 158 to 163).
- Picture: 31 distinct shots in 85 s (a new angle every 2 to 3 s). Real-looking hardware on a dark warm desk, macro cross-sections, a recreated settings screen, a hand pressing the pad. Amber marks the part that matters. Small honesty notes ("movement exaggerated", "values illustrative").
- Captions: small, 2 to 4 words, top third, one keyword in a thin selection box.

**Fruits Universe, wedding reel (277K, 79 s).**
- Hook: something dramatic is already happening in frame one (a collapse at the altar).
- Story: a world with one absurd rule (a number on everyone's forehead), a secret, a public reveal, then a twist line from the least expected character.
- Voice: three acted character voices (panic, whisper, booming sermon), not one narrator. Sounds like ElevenLabs-class TTS.
- Picture: AI image-to-video, Pixar-like characters. Only about 8 shots, 10 s each, small push-ins. Choir music and crowd gasps.

**AnatoVerse, chicken dust bath (266K, 23 s).**
- Hook: an everyday animal habit reframed as life or death.
- Script: four sentences.
- Voice: deep documentary male, about 140 wpm.
- Picture: AI video, 7 shots about 3 s each, wide to microscopic push-ins, golden-hour light. Foley for every action (dirt, crawling, sand pouring, wing shake). Bold white captions with a black outline.

## Us next to them

| | Benchmarks | Overthought now |
|---|---|---|
| Picture quality | Product-real or Pixar-level characters | Code-built clay, sausage limbs, block heads |
| Shots | A new shot every 2 to 3 s (explainers), or every 10 s with real acting (stories) | A handful of angles in one room |
| Locations | A new place every episode, often several | One bedroom reused for 4 episodes in a row, same opening |
| Voice | Fast, warm, acted; multiple characters in stories | One Kokoro voice, 160 wpm, flat |
| Hook | Action or a surprising claim in frame one | A title card and a premise pun |
| Story | Mechanism with payoffs, or setup, secret, reveal, twist | One joke stretched over 30 to 40 s |
| Length | 23 s (nature), 75 to 85 s (explainer, story) | 30 to 40 s every time |
| Sound | Foley on every action, music matched to the setting | Sparse effects |
| Posting | About 1 a day | Hourly |

Our one hit (Schrodinger) won on the premise: relatable and shareable (18.9K shares). It did not win on the picture. Repeating its formula on a weaker set four times in one day got 167 to 1.6K plays each.

## What we change

1. **Animation.** Two of the three benchmarks use AI image-to-video. speedy_devv's picture is product-render quality (his bio says he edits everything in his own tool; how he makes the shots isn't public). Our Blender kit can't reach that bar at 2 hours a render. Options:
   - **A. AI video (paid).** Kling 3.0 or Seedance 2.0 through the Higgsfield connector: character-consistent 5 to 15 s clips, 9:16. Plus is $49 a month (or $39 a month billed yearly) for 1,000 credits, about 200 five-second Kling clips, roughly 15 reels of 12 shots. Ultra is $129 a month (or $99 a month yearly) for 3,000 credits, roughly 40 reels. There is a 3-day $0 trial (100 credits, card required, renews at $49 unless cancelled). Needs Austin's OK; the account is on the free plan with 0 credits.
   - **B. Blender, rebuilt (free).** Real CC0 assets (Poly Haven, Sketchfab CC0), a properly rigged human, a new location every episode, 20 to 30 short shots, foley on every action. Better than now, still below the benchmarks, and slower.
2. **Voice.**
   - Free: Chatterbox (MIT license) has an emotion dial that goes up to shouting. `pipeline/voice_test.py` reads the same two lines with our Kokoro voice and with Chatterbox. The references are Kokoro's own synthetic voices, so no real person is cloned. The output goes to `pipeline/out/voice_tests/`.
     - It installs into `pipeline/vendor/venv_chatterbox` but doesn't run on this laptop yet: Windows' commit limit (23.4 GB RAM plus a 7 GB page file) runs out loading the 3 GB model, on CPU and GPU alike.
     - The Oct 29 samples came from Resemble's free hosted demo, which stopped after three takes (anonymous quota). The male and screaming takes are still missing.
     - Running it locally needs a bigger page file or fewer background apps.
   - Paid: ElevenLabs, which is what these accounts sound like. It has acted delivery, multiple character voices, and tags for shouting and whispering. Prices (third-party summaries checked Oct 29; confirm on elevenlabs.io before buying): Starter is about $6 a month, or $5 a month billed yearly, for 30,000 credits (about 30 minutes of speech) with commercial use. Creator is $22 a month for about 100,000 or more. At 2 to 3 reels a day, Creator covers it.
   - Either way: about 190 to 200 wpm for explainers, and separate acted voices for character stories.
3. **Writing.** Stop the physics + dating series for now. Rotate between three formats, never the same one twice in a row:
   - **Everyday-object explainer**, speedy-style but our own objects: a surprising-claim hook, "you" in every line, payoffs, a loop ending, honesty notes. Per Austin's rule, the narrator screams.
   - **Character story with one absurd rule**: setup, secret, reveal, twist. Our satire voice.
   - **20 to 25 s nature or body macro short**: an everyday thing reframed as life or death.
4. **Process.** Never reuse an opening shot or a set two episodes in a row. Frame one is action, not a title card. Foley on every visible action.

## Decision (Oct 29, evening)

Austin: "whatever can look the best if blender can be efficient and look good then go for it". A 5 s test of a new Blender product-studio kit (real Poly Haven CC0 bulb, walnut desk, cutaway, magnified LED section) reached speedy-level product renders at 1.8 s a frame (30 fps), about an hour of rendering for a 60 s episode. So everyday-object explainers stay in Blender on that kit. Code-built people are still the weak spot, so character stories need a different answer (props and objects as the cast, or AI video later).
