# Weekly plan (cloud routine, Saturday mornings)

Austin's call on Oct 26: **3D only from now on, no more 2D videos.** This cloud has no GPU, so it cannot render 3D. Your job here is the report and the plan; Austin's laptop renders the episodes (in a desktop session or its scheduled render task) and puts them up for approval.

Sync first, because the checkout can start out of date: `git fetch -q origin && git checkout -q -B main origin/main`. Then read `CLAUDE.md`, `RULES.md`, `ops/queue.json`, the newest files in `reports/daily/`, the newest plan in `ops/plan/`, and `ops/ideas.md`. Ideas Austin sent by DM come first when they fit a kit. No em dashes anywhere.

## Steps

1. **Weekly report.** Call `vidiq_instagram_owner_insights` (`platformAccountId` `29135912216032186`, `recentMediaLimit` 12) and write `reports/weekly/<ET date>.md`: per Reel and per format (the queue's `format` field), plays, watched %, skip rate, shares, saves. Then a few plain sentences: what to make more of, what to drop, what to change. Trial Reels go to non-followers, so compare formats with each other, not with follower counts.
2. **Plan next week's 3D episodes** in `ops/plan/<ET date>.md`: up to 7, one per day for the 12:30 pm ET slot. For each one:
   - The kit it uses (see "3D kits" in `CLAUDE.md`). Prefer kits that already exist: a new episode of an existing kit is mostly new numbers and a new script, while a new object or scene needs a lot more laptop time. Mark any episode that needs a new kit.
   - The topic and the hook, readable on frame 1.
   - The narration script in the `render_tap.py` format (`*keyword*` marks, `{spoken form}`), 20 to 40 s. Loop the ending back into the opening where the format allows.
   - Every number with a source link, checked.
   - The caption (per `RULES.md`, ending with a tag or share prompt).
   - Use the weekly report: more of what is holding viewers, less of what is losing them. Everyday objects and escalating what-ifs have done best so far.
3. Commit only the report and the plan to `main` as `Claude <noreply@anthropic.com>` and push. Do not touch `ops/queue.json`, do not render, and do not open pull requests.
4. **Final message**, two lines at most: the week's best and worst post, and the plan's episode titles.
