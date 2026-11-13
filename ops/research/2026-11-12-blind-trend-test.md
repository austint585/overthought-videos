# Blind trend test (Nov 12, 2026)

Austin's ask (DM, Nov 12): run trend research blind until the agent comes up with something like the raw liver Reel by itself, then use what it learned for better ideas.

**The benchmark** is the raw liver Reel (posted Nov 12). It took a hype-speech edit from the past week (@cluberich "Or we could go up..", Nov 6, 5.3M: its delivery, look and instrumental) and poured in an older meme line everyone knows (the raw liver guy's "you never wanted chocolate"). The joke is the gap between a dead-serious delivery and an unhinged line.

**Blind** means each researcher (a Sonnet agent) was told only what the account is and what it can make. None of them saw the account, its posts, this repo or the raw liver Reel. Each round's prompt added lessons about method, never the answer.

## Rounds

| Round | Method given | vidIQ credits | Closest pitch to the benchmark | Verdict |
|---|---|---|---|---|
| 1A | trending sounds and formats | 10 | "Think you're tough like a gorilla?" audio rebuilt in 3D (a known audio in a new form) | partial: no quoted line, no earnest-form clash |
| 1B | outlier data in faceless animation | 25 | none (explainers, sketches, sims) | miss: it threw out live-action and meme clips as unmakeable |
| 2 | + use any format's form; look for quoted lines; ideas people already know half of | 20 | "8th Avenue smoothie": a deadpan motivational monologue form plus a quoted line | the shape matches but the line was unverified |
| 3 | + an earnest form plus an absurd line is the joke; forms fresh, lines can be old; lines verified word for word | 10 | "Sir, this is a Wendy's" as a corner-coach motivational speech, in the form of a 1.5M Nov 10 reel of cats boxing to an earnest speech | **pass: the same machine as the raw liver Reel** |

None of the rounds found the @cluberich edit or the raw liver clip themselves. Round 3 did find their siblings: an earnest motivational speech over cats (1.5M, Nov 10) and a deadpan narrator over mundane action (2.7M, Nov 1).

## What the researcher learned (the method)

1. **Forms come from any format.** Live-action edits, talking clips and audio memes are the best source. We rebuild the form: its delivery and cadence, music, on-screen text style, edit structure and payoff shot.
2. **Look for the lines people quote**, not only sounds: catchphrases, soundboard clips, an unhinged line from an interview. Our voice can carry a sentence.
3. **Earnest form plus an absurd line.** The more seriously the form plays it (hype speech, nature documentary, trailer, breaking news, luxury ad), the harder a tiny or unhinged line lands.
4. **Forms must be fresh, lines can be old.** A form is a 1M+ video from the last two weeks that people are copying. A line can be years old if people still quote it, but it has to be found word for word in a source.
5. Ideas the audience already knows half of spread fastest.

The prompt that passed is saved as `ops/research/form-x-line-prompt.md`, for a make run that has no new DM to work from.

## Ideas from the test, ranked (each is one fresh form plus one known line)

1. **Have you ever heard of a bicep heart?**
   - Pairing: a hushed nature-documentary narrator plus this week's trend line.
   - The trend: kavithageorge, Oct 31, 5.3M (https://www.tiktok.com/@kavithageorge/video/7703044626931895583). Versions reached 8M by Nov 4, and a "waist heart" spin-off followed on Nov 9 (https://knowyourmeme.com/memes/bicep-heart-trend).
   - The form: a calm narrator over nature B-roll, 2.5M, Nov 7 (https://www.instagram.com/reel/DfchdnwzPXi).
   - Ours: the gym bro's bicep heart told as an ancient courtship ritual. It is timely, so make it first.
2. **Sir, this is a Wendy's (corner speech).**
   - The form: an earnest motivational speech over cats boxing, 1.5M, Nov 10 (https://www.instagram.com/reel/DfjX_KStX9j).
   - The line: the 2012 tweet everyone still quotes (https://knowyourmeme.com/memes/sir-this-is-a-wendys).
   - Ours: a full locker-room hype speech to a trembling cashier, whose only content is the line.
3. **Nothing beats a Jet2 holiday (disaster edition).**
   - The form: a calm ad voice over scenic B-roll.
   - The line: the Jet2 ad's tagline (https://trending.knowyourmeme.com/editorials/guides/whats-the-nothing-beats-a-jet2-holiday-meme-about-the-viral-jet2-holiday-tiktok-sound-explained).
   - Ours: the tagline read deadpan while a pastel-toy volcano erases the resort.
   - The line is older, so check that it's still quoted before making it.
4. **Why would I deceive you?**
   - The line: Elizabeth Holmes's teaser line, 32M+ on one repost (https://knowyourmeme.com/memes/elizabeth-holmes-and-nathan-fielder-why-would-i-deceive-you).
   - Ours: a lie-detector gag where the claims escalate ("I'm five minutes away").
   - We'd quote the line only and never show her.
5. **Remember November 2026.**
   - The meme: a polar bear "meme from the future" (https://knowyourmeme.com/memes/remember-november-2026-is-coming) whose date is now.
   - Ours: a suspense storyteller form that resolves it this month. Timely for days only.
   - The original caption is a translation, so put it on screen as text, not as a quote.
6. **Think you're tough like a gorilla?**
   - The audio: 8.1M, Nov 6 (https://www.tiktok.com/@71cent/video/7704845522510548238).
   - Ours: rebuilt in toon 3D with a deadpan animal-fact reply.

The cat "go up" episode (`ops/episodes/2026-11-13-cat-go-up.md`) was written before round 3. Round 3's 1.5M reel of cats under an earnest motivational speech backs the choice of a cat.
