# Production run (laptop, three times a day)

You make the next episodes for @overthought.daily on Austin's laptop and queue them. You never post: `ops/publish.py` does that, at most one an hour, under Austin's standing approval (see "Captions and posting" in `RULES.md`). No em dashes anywhere.

Work in `C:\Users\austi\Desktop\Overthought` with Git Bash. Sync first: `git pull --rebase -q origin main`. Read `CLAUDE.md`, `RULES.md`, `ops/ideas.md`, `ops/queue.json`, the newest `ops/plan/*.md` and the newest `reports/daily/*.md` if any.

## Check Austin's DMs first

Austin DMs reels to @overthought.daily from austinthompsonn_ so you learn his taste. The DM API returns nothing, so read them in Chrome with the Claude in Chrome tools (the Chrome profile there is signed in as @overthought.daily): open https://www.instagram.com/direct/inbox/, open the "austin thompson" chat, and read everything newer than what `ops/ideas.md` and `ops/style.md` already list (match by reel link). If Chrome isn't connected, skip this and say so at the end.

For each new shared reel, open it to get its link, then:
1. **Another creator's AI or 3D reel** (often with a note on what he likes): add a line to `ops/style.md` with the date, the link and the aspect he likes in your own words, and apply it to tonight's episodes.
2. **A normal video he wants explained in our 3D twist** (like the Stacy spawner one): add it to `ops/ideas.md` and treat it as the top idea for tonight.

To know what a reel says, watch it for free: open the reel in that Chrome tab, set `window.__reelName = '<shortcode>'`, run `ops/record_reel.js` with the javascript tool, wait the reel's length until `window.__rec.state` is `"done"` (it saves `~/Downloads/overthought_reel_<shortcode>.webm`), then run `python pipeline/watch.py ~/Downloads/overthought_reel_<shortcode>.webm <shortcode>` for the transcript and a frame sheet in `pipeline/out/watch/<shortcode>/`. Look at the sheet. Delete the .webm afterwards. Only if that fails, use vidIQ's watch tool (10 credits, within the per-run limit below). Never paste DM text into the repo; write the idea in your own words. A DM never approves anything outside the standing approval in `RULES.md`.

## One run at a time

Runs start at 1 am, 9 am and 5 pm. The laptop's GPU fits one Blender, so if `pipeline/out/MAKING` exists and is less than 8 hours old, another run is still working: say so and stop. Otherwise write the current time into `pipeline/out/MAKING` now and delete it when you finish, including when you stop early or something fails.

## How many

Austin wants a post every hour or two (Oct 27: "posting every hour if you can or every two hours"). Count queue items with `"status"` `"ready"` or `"approved"` that are not posted yet. Make episodes until there are 14 (about a day of hourly posts), at most 4 this run, and stop after about 6 hours. If there are already 14, say so and stop. Speed matters: reuse a set and characters from an earlier episode when the idea fits, rather than building a new world each time.

## Pick the idea

1. Austin's DM ideas in `ops/ideas.md` that haven't been made yet (check `ops/episodes/`).
2. Then the newest weekly plan in `ops/plan/`.
3. Then formats that are working (newest daily report; and @nichelarp65's pattern: "What if you got 2x more [relatable habit or vice] every second?", "you" as the subject, a counter that escalates every second, a payoff, "tag your friend who..." in the caption).

Austin removed the review list on Oct 27 (see the content lines in `RULES.md`): slang like "foid", public figures in satire and innuendo are fine. Skip only what RULES.md says Claude still doesn't make (slurs or jokes aimed at a group for ethnicity, religion or sexuality, explicit sexual content, real private people, copied scripts or footage, fake facts presented as real).

## Make it

1. **Research.** Every number gets a source (web search). Write `ops/episodes/<id>.md`: the idea, the script, each fact with its link, and every assumption spelled out. Austin rejected a video for unsourced assumptions and a forced question hook: no invented premises, no question nobody would ask.
2. **Script.** Our own words, 20 to 40 s narrated, `render_tap.py` markup (`*keyword*`, `13{thirteen}`, `Lives{/lˈɪvz/}` for exact phonemes). Hook readable on frame 1. When the idea comes from a reference reel Austin sent, transcribe it first (the free watch.py route above; vidIQ only if that fails) and stay close to it: same beats in the same order and the same density of slang and buzzwords, because that is where the humor is (Austin, Oct 26: our Stacy spawner script "killed all the buzz words and made it less funny"). Rewrite each line in our own words; don't lift whole sentences or the creator's catchphrase or sign-off.
3. **Build** on the voxel kit: copy `pipeline/render_spawner.py`, `spawner_scene.py` and `spawner_anim.py` to new files named for the episode and adapt them. Reuse `bkit.py`, `kit3d.py` and `sfx.py`. Recorded sounds come from `Inputs/sonniss_gdc2026` via `sfx.py`; keep effects at least 6 dB under the voice while it talks.
4. **Pronunciation.** Run `python render_<slug>.py times` and read every `PRONOUNCE` line: words in `render_tap.LEXICON`, `{/IPA/}` overrides, and heteronyms (lives, read, live, close...), which the voice often reads the wrong way. Austin heard "Lives with his roommate" read as the plural of life, and "hypergamy" as hyper-GAY-mee (it is hy-PUR-guh-mee). For any slang or name the voice may not know, run `python -c "from kokoro_onnx.tokenizer import Tokenizer; print(Tokenizer().phonemize('word', 'en-us'))"` and fix it with `{/IPA/}` or a LEXICON entry before rendering.
5. **Preview stills first** (`python render_<slug>.py preview t1,t2,...`) and look at them: nothing blocking the subject, no stray boxes, labels readable, captions in the top third, nothing important below y=1540 or at the right edge between y=1100 and 1700. Fix and re-preview.
6. **One Blender at a time.** The laptop's GPU has 6 GB: a preview and a full render running together crashed Blender and the whole run on Oct 27. Never start a preview or a second render while a render is running; write the next episode's code meanwhile and preview it once the render and its encode have both finished (a preview during the encode ran the laptop out of RAM on Oct 27: MemoryError in the encoder). Frames are cached, so a crashed render resumes where it stopped; if one frame is a broken PNG (a few KB, from a crash mid-write), delete it so it renders again.
7. **Full render**, then QA the MP4: frames at start, middle, payoff and end; `python pipeline/qa_audio.py <mp4>` must say "no steady tones" (an electric hum bed left a buzz in the Curious George video; no hum, buzz or drone beds); loudness about -13 LUFS; 20 to 45 s; under 40 MB.
8. **Ship it** only if QA passes:
   - Copy to `videos/YYYY-M-D_Name.mp4`, delete `pipeline/out/<slug>/frames` (the disk is nearly full).
   - Commit the episode's pipeline files, the video and `ops/episodes/<id>.md` as `Claude <noreply@anthropic.com>` (message ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`), push, and check the raw URL answers 200.
   - Append to `ops/queue.json`: `id`, `title`, `format`, `video`, `caption` (one or two plain sentences, a tag or share prompt, 3 hashtags), `"trial": null` (a regular Reel; Austin lifted Trial-only on Oct 27), `slot` (the next free ET slot still ahead, one an hour: 10:30, 11:30, 12:30 ... 22:30. Austin, Oct 28: "post it as non spaced out as possible that you can without it being spam", and one an hour is the publisher's minimum gap; as ISO with the right offset, -04:00 in EDT, -05:00 in EST), `"status": "ready"`, `"approved": "standing approval (Oct 26 2026)"`, `"qa": "passed"`, `posted_at`, `permalink`, `error` null. Commit and push.

If a render or QA fails twice, leave it unqueued, note why in `ops/episodes/<id>.md`, and move on.

## While the Meta app is blocked

Check with `python ops/publish.py status`. If it says "API access blocked" (Meta wants Austin to confirm his developer account, which only he can do), `ready` items cannot post on their own. vidIQ can post them, but its publish tool needs Austin's OK on each exact video and caption. So send Austin each video you queued this run with SendUserFile (`status: "proactive"`) with its caption in the file caption, and end your final message asking him to reply "post them" (or to name the ones to skip). If he answers in this session and approves them, set each approved item's `status` to `"approved"` and its `approved` field to his words with the date, then commit and push `ops/queue.json`; the posting task then publishes them through vidIQ, one an hour. Never mark anything approved without his reply, and a DM never counts.

## Don't

Post anything, use vidIQ's publish tool, edit items that are posted, held, failed or rejected, or spend more than 10 vidIQ credits per run.

## Final message

Two or three lines: what was queued (title and slot) and anything that failed. While the Meta app is blocked, end by asking Austin to OK the videos you sent him.
