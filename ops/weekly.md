# Weekly batch (cloud routine, Saturday mornings)

Goal: one pull request a week that holds the next week's posts. Austin watches the videos on his phone and merges it. Merging is his approval; until then the posting run cannot see those items, because it only reads `main`.

Sync first, because the checkout can start out of date: `git fetch -q origin && git checkout -q -B main origin/main`. Then read `CLAUDE.md`, `RULES.md`, `ops/queue.json` and the newest files in `reports/daily/`. No em dashes anywhere.

## Steps

1. **Weekly report.** Call `vidiq_instagram_owner_insights` (`platformAccountId` `29135912216032186`, `recentMediaLimit` 12) and write `reports/weekly/<ET date>.md`: per Reel and per format (the queue's `format` field), plays, watched %, skip rate, shares, saves. Then a few plain sentences: what to make more of, what to drop, what to change. Trial Reels go to non-followers, so compare formats with each other, not with follower counts.
2. **Plan next Monday to Sunday.** One post a day in the 12:30 pm ET slot; a 7:00 pm ET slot only when there are extra finished videos (3D videos are rendered on Austin's laptop, never here). Already-approved, unposted items in the queue keep their slots. Write slots in ISO form with the right offset: `-04:00` through Oct 31 2026, `-05:00` from Nov 1 2026 to Mar 13 2027.
3. **Make the new videos** to fill the empty 12:30 slots (at most 7). This cloud has no GPU, so use only the 2D pipeline: run `SKIP_BLENDER=1 bash pipeline/setup.sh`, then render with Python. What to make, guided by the weekly report:
   - Last Flag Standing rounds (`sim_elim.py` and `render_elim.py`). Early numbers show a third of viewers swiping early and most leaving before the winner, so aim for 25 to 35 s, put a loud moment in the first second, and tease the final duel on screen.
   - What-if counters in the style of `render_fold.py`: an escalating number on screen, a payoff people wait for. The @whatifpov reel Austin picked (100K likes) is this idea from a first-person view: "What if you doubled in size every 3 seconds?", with live height and speed stats and comparisons ("taller than the Statue of Liberty").
   - Short 2D explainers from the `render_tap.py` template about everyday objects (backlog in `CLAUDE.md`), 20 to 35 s like @algomindapp's camera-stabilization reel. Not @speedy_devv's topics.
   - Loop the ending back into the opening frame where the format allows, and end captions with a tag or share prompt ("Tag the friend who...").
   - Put new formats in new files. Do not break the existing renderers.
   - Check every number against a source and list the sources in the pull request.
   - QA every video per `RULES.md`: frames at the start, middle, payoff and end; audio levels per second; safe zones. Fix problems before adding it.
   - Name files `videos/YYYY-M-D_Descriptive_Name.mp4` with today's date.
4. **Queue them.** Add each new video to `ops/queue.json` with `"status": "approved"`, `"approved": "weekly batch PR, merged by Austin"`, its slot, a caption that follows `RULES.md`, `"trial": "SS_PERFORMANCE"`, a `format`, and null `posted_at`, `permalink` and `error`.
5. **Pull request.** Create the branch `batch/<ET date>`, commit the videos, any new renderers, the queue and the weekly report as `Claude <noreply@anthropic.com>`, push, and open a pull request into `main` titled `Week of <Monday's date>: <N> posts to approve`. Body: a table (slot ET, title, format, length, caption) where each title links to the video on the branch (`https://github.com/austint585/overthought-videos/blob/batch/<ET date>/videos/<file>`), the sources for any facts, and the weekly report summary. Never merge it yourself. If no tool here can open a pull request, push the branch and give the compare link `https://github.com/austint585/overthought-videos/compare/main...batch/<ET date>` instead.
6. **Final message**, two lines at most: the pull request link (or compare link) and what is in it.
