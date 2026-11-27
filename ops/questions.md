# Questions before building and before handing back

From Austin, Nov 27: "add some protocol that asks questions that will catch stuff like that in the future". The questions come from three misses:

- Every chad episode was the same four guys at the same patio table.
- A rule meant for a reference reel became a limit on ours: the reel's style note said "one warm golden-hour set reused".
- The chad's look got one change per note, and then I stopped instead of comparing him with the reference.

Answer every question in the episode pack (`ops/episodes/<id>.md`), under `## Questions`, one or two lines each. A make run asks part A before the script and part B before the queue. A chat revision asks part B before sending anything to Austin. An answer like "same as last time" needs a reason Austin gave, not habit.

## A. Before the script and the build

1. **Where does each big choice come from: a rule Austin gave, or a habit?** For the set, cast, format, look, length and opening shot, name the source:
   - Austin's words, with a date: it holds.
   - A description of someone else's reel: it's a habit, and you're free to break it.
   - "How we did it last time": also a habit.
   - "One warm golden-hour set reused" in `ops/style_rules.md` described the reference reel, and it kept us at the same table for every episode.
2. **Did any of the last three posts use this set, this cast line-up or this opening shot?** Check `ops/queue.json` and their packs, and change whatever repeats. Background music and ambience may repeat (Austin, Nov 27). Scenery, the line-up and the first frame may not.
3. **Where would this actually happen?** Put the scene where the topic lives. Black Friday happens in a store, not on a patio, and the TV aisle set came from asking this.
4. **Who has to be on screen for the joke to work?** Bring only them. The four friends and their salary tags aren't the default for every chad episode.
5. **What does Austin want beyond his exact words?** Write his intent in one line. "Make him look like X" means people can tell it's X, not one change in X's direction.
6. **If he named a reference (a person, a reel, a look), where is the side-by-side?** Before calling it done, put our frame next to the reference and list every difference.

## B. Before handing anything back (episodes and every revision)

7. **What's still off compared with the reference or his note?** List it. Fix anything on the list that takes under an hour, then compare again. Hand it back only when what's left is something you chose on purpose, and name it. (Nov 27: "why did you stop iterating".)
8. **Could I predict his next correction?** If so, make that fix now.
9. **Does it still follow everything he said in this chat, not only his last note?** Earlier notes still stand.
10. **Would someone who saw yesterday's post think this is the same video?** If yes, go back to question 2.
11. **Will the rework land before the slot?** Check the clock against the item's slot in `ops/queue.json`; the poster runs at :40. If a queued episode is being reworked, set it to `held` or move its slot first, and only then start. On Nov 27 Black Friday's patio version posted at 10:40 while its store version was still rendering.
