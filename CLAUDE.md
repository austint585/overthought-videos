# Overthought: passdown for Claude Code

Last updated 2026-10-25 evening by Claude Code on Austin's laptop (first 3D video, Blender pipeline). Read this and RULES.md before doing anything.

## What this is

An AI-run, faceless Instagram account, **@overthought.daily** (display name "Overthought"), posting short animated videos drawn entirely in code. Austin Thompson owns it and approves every post. The plan: test a few formats for about two weeks, read the numbers, then commit to the winner and post daily.

- The account is Austin's from 2019. Its ~776 followers came from follow-for-follow, so they are random and won't engage. That's why new formats go out as **Trial Reels** (non-followers only).
- Bio (Austin sets it by hand): "Questions nobody asked, answered anyway."
- Profile picture: `pipeline/pfp.py` (orange circle, stick figure with a tangled thought).

## Status (2026-10-25)

| Video | State |
|---|---|
| Last Flag Standing (elimination sim, 43 s) | Posted as Trial Reel, Oct 25 ~1:00 pm ET: https://www.instagram.com/reel/De7L-22ChQ0/ |
| Folding Paper 103 Times (what-if counter, 48 s) | Posted as Trial Reel, Oct 25 7:00 pm ET: https://www.instagram.com/reel/De71w3qERvN/ |
| How Tap-To-Pay Works (narrated explainer, 48 s) | Approved Oct 25 (exact video, caption below, Trial Reel SS_PERFORMANCE). In `ops/queue.json` for Mon Oct 26 12:30 pm ET. The desktop session posts it at 12:30 if the app is open; otherwise the posting routine picks it up at 1:45 pm. |
| Why Only Your Key Opens Your Door (3D cutaway, 41 s) | First 3D video (Blender). Approved Oct 25 (exact video, caption below, Trial Reel SS_PERFORMANCE) In `ops/queue.json` for Mon Oct 26 7:00 pm ET. The desktop session posts it at 7:00 if the app is open; otherwise the posting routine picks it up at 8:45 pm. |

Early numbers, Last Flag Standing at ~6 h (trial audience only): 116 plays, avg watch 13.1 s of 43 s (30%), skip rate 34%, no likes, comments, shares, or saves yet. Read: a third of viewers swipe in the first seconds, and most leave long before the winner reveal. Ideas to test: a louder first second, a shorter sim (25-30 s), and teasing the final duel on screen.

Approved captions:
- Last Flag Standing: "48 countries, 1 ring, 1 survivor. Comment your country and it's in the next round. #simulation #flags #countries"
- Folding Paper: "Every fold doubles it. By fold 42 it reaches the Moon. The real-life record is 12. #math #space #science"
- Tap-To-Pay: "Your phone never sends your card number when you tap to pay. It sends a stand-in and a one-time code. #howitworks #tech #nfc"
- Why Only Your Key Opens Your Door: "Five tiny pins decide whether your door opens. Comment what we should cut open next. #howitworks #engineering #locks"

## Connections

- **vidIQ MCP** (claude.ai connector, logged in as austinthompson585@gmail.com). Run `/mcp` to confirm it's available in Claude Code; if not, connect vidIQ there.
  - Instagram account: `platformAccountId = 29135912216032186` (@overthought.daily), scopes: basic, content_publish, manage_insights.
  - Credits: 150/month plan, renews Nov 6. About 80 left on Oct 25. Free: upload, publish, owner insights, job polling. Paid: watch a reel 10, outlier search 5, profile reels 5, vidIQ voiceover 14 per 1,000 chars (we don't use it; see voice below).
- **GitHub**: `austint585/overthought-videos` (public). Finished videos go in `videos/` and are served from
  `https://raw.githubusercontent.com/austint585/overthought-videos/main/videos/<file>.mp4`
  (application/octet-stream with Content-Length, which vidIQ accepts). The cloud session couldn't create Releases (403). With local `gh auth`, moving videos to Releases would keep the repo small.

## How posting runs now (hands-off, from Oct 26)

- `ops/queue.json` is the source of truth: every post with its video, exact caption, trial setting, slot (ET) and status (`approved`, `posted`, `failed`). Only items on `main` with `"status": "approved"` ever get posted.
- **Posting routine** (Claude Code cloud routine, `45 0,17 * * *` UTC, so 1:45 and 8:45 pm EDT, 12:45 and 7:45 pm EST): follows `ops/post.md`. Checks Instagram first so nothing posts twice, posts the earliest due approved item (one per run), writes `reports/daily/` on the evening run, commits the queue.
- **Weekly routine** (Saturdays `0 14 * * 6` UTC, 10 am EDT / 9 am EST): follows `ops/weekly.md`. Weekly report, renders next week's 2D videos (the cloud has no GPU), opens a pull request `Week of ...`. **Austin merging that pull request is his approval** of every video and caption in it.
- 3D videos are rendered on Austin's laptop in a desktop session and added to the queue once he approves them in chat.
- Both routines need the vidIQ connector attached on their routine page at claude.ai/code/routines, and the Claude GitHub app with access to this repo.
- Change what the routines do by editing `ops/post.md` and `ops/weekly.md`; the routine prompts just point at them.

## Publishing a Reel by hand

1. Render to `videos/YYYY-M-D_Name.mp4`, commit, push.
2. `vidiq_video_upload(url=<raw URL>)` returns `videoUrl` and `uploadId` (pass the uploadId later to refresh an expired signed URL).
3. Get Austin's OK on the exact video, caption, trial setting, and time. vidIQ requires this, and so do we.
4. `vidiq_instagram_publish_reel(platformAccountId, videoUrl, caption, trialParams={"graduationStrategy": "SS_PERFORMANCE"})`. It returns a `containerId`; call again with the containerId (about 5 s apart) until `PUBLISHED`. Never re-submit a failed one automatically.
5. Read results with `vidiq_instagram_owner_insights(platformAccountId)`: views, watch time, watched %, skip rate, shares, saves. Metrics can lag a day.

## What no connection can do

Bio, profile picture, username (Instagram's API has no profile editing). Stories and carousels (vidIQ posts Reels only). Instagram comments and DMs (vidIQ's comment tools are YouTube-only). Following or unfollowing (no API, and automated following gets accounts banned). Never handle Austin's passwords. If a browser is ever used for profile edits, Austin signs in himself and approves each change.

## Pipeline (`pipeline/`)

Setup on a new machine (Git Bash on Windows): `bash pipeline/setup.sh`. Needs Python 3.10+, Node/npm, ffmpeg, git. On Austin's Windows laptop: `winget install Git.Git OpenJS.NodeJS.LTS Gyan.FFmpeg` (Anaconda Python is already installed). setup.sh installs the Python libs, downloads the Kokoro voice model from GitHub (Hugging Face's CDN was blocked in the cloud), and pulls fonts and flags from npm into `pipeline/vendor/` (gitignored).

| File | What it does |
|---|---|
| `common.py` | Brand colors, fonts, text helpers, audio synthesis (tones, sweeps, noise, kick, hats, beat bed), `save_wav` with soft limiter, ffmpeg encoder (1080x1920, 60 fps, H.264 veryfast CRF 18, AAC 192k). |
| `sim_elim.py`, `render_elim.py` | Last Flag Standing: pymunk balls inside a rotating ring with a gap; escape = out; last one wins. Tuned: seed 6, gap0 0.28, growth 0.18, ball radius 31 (38.9 s sim, Poland wins). Re-sweep seeds for new rounds; aim for 35-55 s with a 3+ s final duel. |
| `render_fold.py` | Folding Paper 103 Times: true-scale zoom-out with landmark lines, shrinking Earth, Moon and Sun dots. |
| `render_tap.py` | Narrated explainer template. `SCRIPT` = (scene, sentence) with `*keyword*` and `13.56{thirteen point five six}` for spoken forms. Voice `am_adam`, speed 1.05. Word timing from phoneme weights snapped to energy dips. Captions top third, keywords boxed orange. |
| `pfp.py` | Profile picture. |
| `render_lock.py`, `lock_scene.py`, `lock_anim.py` | 3D cutaway explainer (pin tumbler lock). `render_lock.py` reuses the tap-to-pay narration and captions, writes `out/lock/timing.json`, runs Blender headless on `lock_scene.py` (every mesh, material, light and camera move built in Python, Eevee, 60 fps), then draws captions, labels and the end card over the frames and mixes synthesized sound. `lock_anim.py` holds the shared geometry and motion (pin heights from the key profile, plug turn, glows) so the picture and the pin clicks stay in sync. Blender frames cache in `out/lock/frames`; delete them after changing the scene. About 1.4 s per frame on Austin's laptop (RTX 3060), so a 41 s video is about an hour. |

Every script: `python <script>.py out.mp4 out.wav` to render, `python <script>.py preview <times>` to dump PNG frames into `preview/` for checking.

setup.sh also fetches portable Blender 5.2.3 into `pipeline/vendor/blender_dl/` from the Berkeley mirror (blender.org and winget's source return 403 to scripts) and checks its SHA-256. Override with `BLENDER=/path/to/blender`.

## What the research found (Oct 2026)

- Instagram ranks Reels mainly on watch time and sends per reach (DM shares); originality matters. The AI label requirement applies to profiles built around AI-generated *people*, not to code-drawn animation.
- Breakout faceless formats we can build in code: physics elimination sims (huge views, weak follower conversion), what-if with an escalating counter, how-it-works explainers, stick-figure justice stories (4.6M, 3.6M), choose-your-path stories where the top comment decides the next part (2.9M), animated-graph comedy ("rules of staring", 2.9M at 634x), comment-to-play races ("your birth month = your stickman", 2.9M).
- **@speedy_devv** (Claude-built explainers) is the model to beat: "How does [thing in your hand] really work under the hood?", narrated, word-by-word captions with a boxed keyword, labeled cutaways with honesty notes ("magnified illustration"), 80-90 s, near-daily. Everyday objects win (touchscreen 13.2M, phone keyboard 9.8M); niche topics flop (Cloudflare Workers, 225 plays). "Comment FOLDER" got 12K comments because a DM automation sent a reward. Don't copy his topics: touchscreen, phone keyboard, laptop battery, noise cancelling, trackpad, Find My, wireless charging, H-bomb, AI chips, closing apps.

## Next steps

1. Get Austin's approval for Tap-To-Pay and post it.
2. About 48 h after each post, pull insights and compare the three formats on watched %, skip rate, shares, saves.
3. Daily routine: done (see "How posting runs now"). After Nov 1 the cron's UTC times land an hour earlier in ET; still after both slots.
4. Test the untried formats above (justice story, choose-your-path, graph comedy, birth-month race).
5. Explainer backlog (everyday, not his topics): microwave door mesh, car key fob, fridge, Face ID in the dark, why phones die in the cold, how noise travels through walls. Lock and key is done (3D). Austin is a mechanical engineering student and can sanity-check mechanisms.
6. Austin wants the realistic 3D look, not flat 2D (Oct 25: "looks a whole lot less ai"). References he picked: @alloyrobotics lidar-in-snow reel (https://www.instagram.com/p/Dec8Nx2kU2_/, 26 s, cinematic scene, moving camera, short centered captions) and @wemakebuild "How a Wooden Plank Becomes a Bridge" (https://www.instagram.com/p/Deiz8tguWYI/, 98 s, 1.8M likes, cross-section diorama that upgrades step by step, one big word at a time, a running joke character). New explainers should be Blender cutaways built on the lock pipeline.
7. Later: a comment-keyword giveaway with DM automation, and a way for the account to make money.

## Austin's preferences

- Never use em dashes, in anything (captions, docs, chat).
- File names: `YYYY-M-D_Descriptive_Name`.
- Plain, direct wording. Captions and bios should not sound AI-written.
