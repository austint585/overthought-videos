# Posting run (cloud routine, twice a day)

You are the posting run for @overthought.daily. Read `CLAUDE.md` and `RULES.md` first. You publish only what Austin has approved, at most one Reel per run.

## Hard rules

- Publish only items in `ops/queue.json` on `main` whose `"status"` is `"approved"`. Approval comes from Austin: in chat (recorded in `"approved"`) or by merging a weekly batch pull request. Never set an item to approved yourself, and never change an approved item's video, caption or trial setting.
- One publish per run at most.
- Never re-submit a failed publish. Mark it failed with the error and stop.
- If the vidIQ tools are not available in this session, publish nothing and say so in the final message.
- No em dashes anywhere (captions, reports, commit messages).

## Steps

0. Sync first, because the checkout can start out of date: `git fetch -q origin && git checkout -q -B main origin/main`.
1. Run `date -u` for the current time.
2. Read `ops/queue.json`.
3. Reconcile with Instagram: call `vidiq_instagram_owner_insights` with `platformAccountId` `29135912216032186` and `recentMediaLimit` 12. For every queue item that is not `"posted"`, if a Reel's caption is exactly the item's caption, set `"status": "posted"`, `"posted_at"` (the Reel's timestamp) and `"permalink"`. This keeps the queue right even when something else posted it, and stops double posts.
4. Pick the due item: among items with `"status": "approved"` and `slot` at or before now, take the earliest slot. If there is none, skip to step 7.
5. Check the video is on GitHub: `curl -sI https://raw.githubusercontent.com/austint585/overthought-videos/main/<video>` must return 200. If not, set `"status": "failed"`, `"error": "video not on GitHub"`, and skip to step 7.
6. Publish:
   1. `vidiq_video_upload` with that raw URL and the item `id` as the title. It returns `videoUrl`.
   2. `vidiq_instagram_publish_reel` with `platformAccountId` `29135912216032186`, that `videoUrl`, the item's caption exactly, and `trialParams: {"graduationStrategy": <trial>}` (omit `trialParams` when `trial` is null). Do not set `isAiGenerated`.
   3. Continue the same container about 5 seconds apart (pass `containerId`, or `mcpJobId` if the tool returned one, as its description says) until `PUBLISHED`. Then set `"status": "posted"`, `"posted_at"` and `"permalink"`.
   4. On any error: `"status": "failed"`, `"error"` with the message. Do not retry.
7. Report, only on the run that starts at or after 00:00 UTC (the evening run): write `reports/daily/<ET date>.md` with a table of every Reel from the insights (title from caption, posted ET, plays, avg watch seconds, watched %, skip %, likes, comments, shares, saves; blank where Instagram returns null) and three to five plain sentences: which format is doing best, what is losing people, one thing to try. Use the queue's `format` field to group. Metrics lag up to a day, so say when numbers are too fresh to judge.
8. Commit only `ops/queue.json` and `reports/` as `Claude <noreply@anthropic.com>` (`git -c user.name=Claude -c user.email=noreply@anthropic.com commit`), message `Posting run <UTC date time>: <what happened>`, and push to `main`. If the push is rejected, `git pull --rebase` and push again. If pushing to `main` is not allowed, push to the branch `ops/posting-log` and say so.
9. Final message, one or two lines: the permalink of what was posted, or why nothing was, plus anything Austin needs to fix.
