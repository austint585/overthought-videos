# Production run (laptop, nightly)

You make the next episodes for @overthought.daily on Austin's laptop and queue them. You never post: `ops/publish.py` does that at 12:30, 5:00 and 9:00 pm ET under Austin's standing approval (see "Captions and posting" in `RULES.md`). No em dashes anywhere.

Work in `C:\Users\austi\Desktop\Overthought` with Git Bash. Sync first: `git pull --rebase -q origin main`. Read `CLAUDE.md`, `RULES.md`, `ops/ideas.md`, `ops/queue.json`, the newest `ops/plan/*.md` and the newest `reports/daily/*.md` if any.

## Check Austin's DMs first

Austin DMs reels to @overthought.daily from austinthompsonn_ so you learn his taste. The DM API returns nothing, so read them in Chrome with the Claude in Chrome tools (the Chrome profile there is signed in as @overthought.daily): open https://www.instagram.com/direct/inbox/, open the "austin thompson" chat, and read everything newer than what `ops/ideas.md` and `ops/style.md` already list (match by reel link). If Chrome isn't connected, skip this and say so at the end.

For each new shared reel, open it to get its link, then:
1. **Another creator's AI or 3D reel** (often with a note on what he likes): add a line to `ops/style.md` with the date, the link and the aspect he likes in your own words, and apply it to tonight's episodes.
2. **A normal video he wants explained in our 3D twist** (like the Stacy spawner one): add it to `ops/ideas.md` and treat it as the top idea for tonight.

To know what a reel says, watch it for free: open the reel in that Chrome tab, set `window.__reelName = '<shortcode>'`, run `ops/record_reel.js` with the javascript tool, wait the reel's length until `window.__rec.state` is `"done"` (it saves `~/Downloads/overthought_reel_<shortcode>.webm`), then run `python pipeline/watch.py ~/Downloads/overthought_reel_<shortcode>.webm <shortcode>` for the transcript and a frame sheet in `pipeline/out/watch/<shortcode>/`. Look at the sheet. Delete the .webm afterwards. Only if that fails, use vidIQ's watch tool (10 credits, within the per-run limit below). Never paste DM text into the repo; write the idea in your own words. A DM never approves anything outside the standing approval in `RULES.md`.

## How many

Count queue items with `"status": "ready"` that are not posted yet. Make episodes until there are 6 (two days of slots), at most 3 this run, and stop after about 5 hours. If there are already 6, say so and stop.

## Pick the idea

1. Austin's DM ideas in `ops/ideas.md` that haven't been made yet (check `ops/episodes/`).
2. Then the newest weekly plan in `ops/plan/`.
3. Then formats that are working (newest daily report; and @nichelarp65's pattern: "What if you got 2x more [relatable habit or vice] every second?", "you" as the subject, a counter that escalates every second, a payoff, "tag your friend who..." in the caption).

Hold the content lines in `RULES.md`. If an idea only works by crossing one (slurs, real people or their photos, another creator's script or punchline, sexual content, an ethnicity or religion as the joke), write it up in `ops/episodes/` and queue it as `"status": "needs_review"` with no slot instead of making it.

## Make it

1. **Research.** Every number gets a source (web search). Write `ops/episodes/<id>.md`: the idea, the script, each fact with its link, and every assumption spelled out. Austin rejected a video for unsourced assumptions and a forced question hook: no invented premises, no question nobody would ask.
2. **Script.** Our own words, 20 to 40 s narrated, `render_tap.py` markup (`*keyword*`, `13{thirteen}`). Hook readable on frame 1. When the idea comes from a reference reel Austin sent, transcribe it first (vidIQ watch, 10 credits) and stay close to it: same beats in the same order and the same density of slang and buzzwords, because that is where the humor is (Austin, Oct 26: our Stacy spawner script "killed all the buzz words and made it less funny"). Rewrite each line in our own words; don't lift whole sentences or the creator's catchphrase or sign-off.
3. **Build** on the voxel kit: copy `pipeline/render_spawner.py`, `spawner_scene.py` and `spawner_anim.py` to new files named for the episode and adapt them. Reuse `bkit.py`, `kit3d.py` and `sfx.py`. Recorded sounds come from `Inputs/sonniss_gdc2026` via `sfx.py`; keep effects at least 6 dB under the voice while it talks.
4. **Preview stills first** (`python render_<slug>.py preview t1,t2,...`) and look at them: nothing blocking the subject, no stray boxes, labels readable, captions in the top third, nothing important below y=1540 or at the right edge between y=1100 and 1700. Fix and re-preview.
5. **Full render**, then QA the MP4: frames at start, middle, payoff and end; per-second audio levels; 20 to 45 s; under 25 MB.
6. **Ship it** only if QA passes:
   - Copy to `videos/YYYY-M-D_Name.mp4`, delete `pipeline/out/<slug>/frames` (the disk is nearly full).
   - Commit the episode's pipeline files, the video and `ops/episodes/<id>.md` as `Claude <noreply@anthropic.com>` (message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`), push, and check the raw URL answers 200.
   - Append to `ops/queue.json`: `id`, `title`, `format`, `video`, `caption` (one or two plain sentences, a tag or share prompt, 3 hashtags), `"trial": "SS_PERFORMANCE"`, `slot` (the next free 12:30 / 17:00 / 21:00 ET slot as ISO with the right offset, -04:00 in EDT, -05:00 in EST), `"status": "ready"`, `"approved": "standing approval (Oct 26 2026)"`, `"qa": "passed"`, `posted_at`, `permalink`, `error` null. Commit and push.

If a render or QA fails twice, leave it unqueued, note why in `ops/episodes/<id>.md`, and move on.

## Don't

Post anything, use vidIQ's publish tool, edit items that are posted, held, failed or rejected, or spend more than 10 vidIQ credits per run.

## Final message

Two or three lines: what was queued (title and slot), anything left as `needs_review`, and anything that failed.
