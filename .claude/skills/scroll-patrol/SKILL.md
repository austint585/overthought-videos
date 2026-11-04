---
name: scroll-patrol
description: Run a short-form video (Reel, TikTok, Short) past ten Claude viewers who each try to scroll past it from a different seat (the half-second thumb, the sound-off commuter, the caption skimmer, your target viewer, a total stranger, a rival creator, the skeptic, the pace police, the friend you'd send it to, the saver), mark the exact second each one leaves, then rewrite the opening and re-test it. Use when the user types /scroll-patrol, says "will people watch this", "rate my hook", "why do people skip my reels", "fix my first line", or pastes a video script, caption or transcript.
---

# /scroll-patrol: ten viewers try to scroll past your video

Made by @thepapercrab. Free to use and share.

Your analytics tell you *when* people leave, never *why*. Here, ten viewers watch your video, each from
a different seat. Each one says the exact second they'd scroll away and the reason. Then you get a new
opening, re-tested by the same ten.

⛔ This is a simulation by characters, not real analytics or a promise of views. Say so in the verdict.
Never invent facts, numbers, results or claims for the user's video. Judge the video, never the
creator's looks, voice or accent.

## The ten viewers

Each viewer has one job. They never step on each other's job.

| Viewer | Their one question | What keeps them |
|---|---|---|
| **The Thumb** (half a second) | "Does frame one make me stop?" | Something moving, a result or a clear face on screen at 0:00. No logo, no title card, no "hey guys" |
| **The Sound-Off Commuter** | "Do I get it with the sound off?" | On-screen text that carries the hook by itself in the first 2 seconds |
| **The Caption Skimmer** | "Does the first line of the caption pay off what I just saw?" | A first caption line that adds a reason to keep watching, not a repeat |
| **Your Target Viewer** | "What's in it for me, specifically?" | A benefit to *them* by second 3, in their words |
| **The Total Stranger** | "Do I understand every word?" | No jargon, no insider names, no unexplained acronyms |
| **The Rival Creator** | "Have I seen this exact video before?" | A twist, a premise or a result nobody else has |
| **The Skeptic** | "Do I believe it?" | Proof on screen; no claim bigger than what's shown |
| **The Pace Police** | "Is anything slow?" | No dead air, no beat longer than about 4 seconds without something new, roughly 4 spoken words a second |
| **The Friend You'd Send It To** | "Who would I send this to, and why?" | A clear "this is so you" moment |
| **The Saver** | "Will I need this later?" | Something reusable: a step, a list, a link, a tool |

## Run it in four rounds

### Round 1: Collect

You need:

1. **The video** in any of these forms:
   - the script or voiceover
   - a transcript with timestamps
   - the video file itself, if you can extract frames from it
2. **What's on screen in the first 3 seconds**, one line per second if there are no frames ("0:00 my face, text: 3 AI tools", "0:01 screen recording").
3. **On-screen text** and the **first line of the caption**.
4. **Who it's for**, in one line. If they skip it, judge for a general audience and say so.

Ask for anything missing in **one** message, then wait. Don't ask for anything else.
If there are no timestamps, estimate them at 4 spoken words a second and say that you did.

### Round 2: The viewers

Go viewer by viewer, in the table order. For each one, write:

- **GONE AT 0:0X** or **WATCHED IT ALL**
- The one reason, in a single sentence, tied to a specific second, line or frame of this video
- **What they'd point at:** the exact words quoted or the timestamp
- **What would have kept them:** the specific fix

Rules:
- Judge only what's in the video. Don't invent weaknesses or strengths.
- Be funny about the video, never cruel about the person.
- It's fine for all ten to leave. It's fine for all ten to stay. Don't balance it.
- The Rival Creator must name one thing they'd steal, then the thing they've seen before.

### Round 3: The verdict

Write:

- The score, e.g. "3 of 10 watched to the end"
- **The exit map:** a one-line timeline of when each viewer left, e.g. `0:00 ▮▮ 0:02 ▮▮▮ 0:05 ▮ ... end ▮▮▮`
- **The deadliest second:** the moment that lost the most viewers, and why, in one sentence
- **The three fixes that keep the most viewers**, most important first

### Round 4: The rewrite and re-test

Write two files in the current folder (change nothing else):

- `PATROL.md`: every viewer's verdict, the score, the exit map and the fix list
- `HOOK-FIXED.md`:
  - **Five new first lines** (spoken), each under 3 seconds at 4 words a second, each in a different style:
    1. result first
    2. "I built / I tested"
    3. a belief and its contradiction
    4. a number
    5. a question
  - **Frame one:** what should be on screen at 0:00 for the best line, using only things the user has
  - **On-screen text** for the first 2 seconds
  - **A new first caption line**
  - **Re-test:** run all ten viewers again on the best new opening plus the rest of the original video. Give the new score and say which viewers changed their minds and why. If someone still leaves, say so. Never fake a perfect score.

Rewrite rules:
- Use only facts from the original. Where a number, result or detail would help but the user never gave one, write `[ADD: how many? / what result? / how long did it take?]` instead of inventing it.
- No clickbait the video doesn't pay off. Every promise in the hook must be shown later in the video.

Then tell the user in chat:
- the old and new score
- the deadliest second
- every `[ADD: ...]` they need to fill in

## Patrol again

If `PATROL.md` already exists, read it first. After the user changes the video, say which fixes
landed, let the viewers who left react to the change, and add a new dated section instead of
overwriting it, so the user can watch the exit map move later.

## Privacy

Everything stays in the user's own Claude session and folder. Don't send the video, script or stats
anywhere.

## Overthought house rules (added Nov 3 2026, not part of the original)

This copy runs in the @overthought.daily project. Where these rules and the rounds above disagree, these win.

- **Inputs come from the episode pack** `ops/episodes/<id>.md`: the script (drop the `render_tap.py` markup: `*word*` is the boxed keyword, `13{thirteen}` is how it's spoken), the shot list for the first 3 seconds, the sign and caption text on screen, and the caption. The viewer is a non-follower on Instagram (every reel starts as a Trial Reel), narrowed by the pack's "why people care" line. Never ask for anything: judge with what the pack has and say what was missing.
- **Our frame one is a 3D scene, not a person.** "A clear face" means a clear subject. Nobody speaks as themselves on this faceless account, so drop the "I built / I tested" line style; use "the payoff shown first" in its place.
- **Hooks follow RULES.md.** No invented premise and no question nobody would ask (Austin rejected the rice video for both). A question line is fine only when people really ask it. Every number in a new line must already be in the pack's sources table; otherwise write `[ADD: ...]`.
- **One file, in the pack folder.** Write everything (Rounds 2 to 4) to `ops/episodes/<id>-patrol.md` instead of `PATROL.md` and `HOOK-FIXED.md`. Start it with a line `Patrol score: N of 10` (the original opening) and, if there is a re-test, `Re-test score: N of 10`. The daily report compares that first number with the real skip rate later.
- **Keep it short.** One or two lines per viewer. Usage is limited, and a make run can patrol four episodes.
- **It is a guess.** Real insights in `reports/daily/` outrank it, and it never approves or blocks an episode on its own.
