# Directing an episode

Austin, Nov 10: "direct the animations instead of describing them", from two @science_in_8bit reels he sent (https://www.instagram.com/p/DfeDGl0HJZs/ and https://www.instagram.com/p/Dfgr-20D5Hw/). Both show the same idea made twice with the same tool. The second one labels the flat version "Claude" and "described". That is how our scenes have been built: a script, a set, a three-point light that never changes, a 35 mm camera drifting from one spot to the next. The content carried the hits. Direction is the part we skipped.

Their two lists, merged: the look and the palette; where the light goes; four layers of depth; where the eye goes and the empty space; the one big moment and when it hits; a breath before the hit; anticipation, release, settle; smear frames and animating on twos; a perfect loop; and what to avoid (an orb, anything muddy). Their 119-page guide is behind a paywall, so the rest of this page fills it in from standard film and animation craft (Disney's principles of animation, Bruce Block's *The Visual Story* on contrast and affinity, Walter Murch on cutting) and turns it into code (`pipeline/direct.py`) and a check (`pipeline/qa_direction.py`).

## The rule

**Decide, then build.** Before any scene code, write the shot sheet below in the episode file. Every line in it is a decision a viewer can see. "A couple sits on a couch" is a description. "Couple at the lower middle of the frame, lit only by the TV in front of them, everything behind them falls to black, 50 mm, locked off, the cat's tail flicks once in the foreground blur" is direction.

## Decisions for the whole reel

1. **The look.** Four colors at most:
   - a dark field: near-black blue, teal or purple (never brown-gray);
   - the subject's color;
   - a neutral;
   - **one accent kept back for the big moment.** Plan the values too: the subject is the brightest thing in the frame and the background is the darkest. Write the four colors down, as hex.
2. **The one big moment.** Pick the single shot the reel builds to, usually the punchline. Tie it to a word in the narration (an event in `timing.json`). It gets:
   - the biggest change in light;
   - the reel's only fast move;
   - the accent color's first appearance;
   - the loudest sound.

   Everything before it stays quieter so it reads. Plot the intensity of each shot from 1 to 5 (contrast, color, motion, sound). It should climb to the big moment and drop after it (Block's contrast and affinity curve). A flat line means no moment.
3. **The loop.** The last frame should cut cleanly back into the first, with the same framing and the same light, so a rewatch doesn't feel like a restart.
4. **The first frame is a directed still.** No establishing shot. Open in the middle of the situation, on the subject, lit, with the one strange thing already visible. It has to work as a thumbnail with the sound off.

## Decisions for every shot

5. **Where the eye goes.** Each shot has one focal point, and you say where it sits on screen.
   - Keep it in the clear band of the 9:16 frame, between the captions and the app's buttons: y from 0.30 to 0.72 of the height.
   - Leave empty space on the side the subject faces or moves toward.
   - The focal point gets the highest contrast and the most saturated color in the frame.
   - Across a cut, keep the eye near the same spot on screen (Murch's eye trace) so the viewer never has to hunt.
6. **Where the light goes.** One motivated key light per shot: a lamp, a phone screen, a TV, a window, a flashlight, a fire. Light the focal point and let it fall off into shadow around it.
   - Fill at 10 to 20% of the key.
   - A rim light behind the subject so it separates from the dark field.
   - Relight per shot: film crews re-place the key for every camera setup, and so do we (the `key=` argument).
   - Light changes are events (a phone lights up, a door opens). It never drifts.
7. **Four layers of depth:**
   - foreground: something near the lens, out of focus and dark (a couch arm, a shelf edge, a plant, falling snow or dust);
   - the subject, in focus;
   - the midground;
   - the background: darker, cooler, hazier (`bkit.add_haze`).

   Open the aperture on close shots (f/1.8 to 2.8) so the layers separate.
8. **Camera with a reason.**
   - **Lens:** 24 to 28 mm for space, comedy and scale; 35 mm neutral; 50 to 85 mm for faces, tension and isolation.
   - **Height:** low makes something important or absurdly heroic; high makes it small and pathetic.
   - **Moves:** at most one per shot, and it means something. A push-in is a realization, a pull-out is a reveal of scale, still is deadpan.
   - Our narrator is deadpan, so most shots are **locked off and symmetrical**. A calm frame makes the absurd thing funnier. Save the reel's one push or punch-in for the big moment.
9. **Timing: a breath, then the hit.**
   - Before every beat that matters: 0.2 to 0.4 s where everything holds still (idle motion, drift, flicker) and the sound dips (`hold()`).
   - Then anticipation, release, settle (`ars()`): a small move the wrong way, a fast move (3 to 6 frames) into the hit, an overshoot that settles over about half a second.
   - Fast moves get motion blur. Their "smear frames" are the 2D version of the same thing.
10. **Figures on twos.** Blocky figures look like stop-motion when their poses step every second frame (`on_twos()`). Keep the camera and light smooth so the frame stays clean.
11. **Cuts.**
    - Use hard cuts on the stressed word, with no 0.4 s camera slides between shots.
    - After a punchline, hold the reaction for half a second before the next line.
    - Let shot lengths vary with the narration: a long establishing hold, quick cuts while things escalate, a long hold on the big moment.
12. **Staging.**
    - Figures in three-quarter view or profile, overlapping in depth (one nearer, one farther). Never a row facing the camera.
    - Silhouettes must read: if the shot rendered black on white, could you tell what is happening?
    - Group what matters and leave the rest of the frame empty.

## What to avoid

- Even light from everywhere: the frame looks like a product render.
- Brown on brown, gray on gray, every value in the middle (muddy).
- A camera that floats without a reason.
- Several things moving at once: one thing moves, everything else holds.
- The payoff in a wide shot, or halfway through a sentence.
- Labels or panels over the subject.
- Glowing orbs, lens flares and particle sparkles as decoration.
- A crossfade where a cut belongs.
- The same lens and the same distance for every shot.

## What their two biggest reels do (watched Nov 10)

"Don't swallow" (4.4M, https://www.instagram.com/reel/DfEeekmgjHs/, 34 s) and "your knuckle crack" (4.2M, https://www.instagram.com/reel/DfIqOKUCneZ/, 32 s) are built the same way:

- **One subject, centered, for the whole reel.** A body part with a simple face: a tongue in an open mouth, a knuckle joint. The frame barely changes; the subject is the shot.
- **Warm subject, cool field.** An orange or pink glow sits right on the subject against deep blue or maroon. It reads as a halo even as a thumbnail. One yellow accent marks the keyword in each caption and the payoff number.
- **A counter drives it.** The swallow reel counts down 20 to 1 while the saliva visibly rises, so the tension rises with the count. The knuckle reel runs a 20-minute "reload" timer. The viewer always knows how far along they are.
- **One camera move, and it means "go inside".** It tilts down the throat to show the two pipes, then comes back out. Everything else is held.
- **One big moment:** "GULP!" at zero, with the drop falling, the flap shutting and a beat of silence. The knuckle reel's version is the bubble popping.
- **One true number for the payoff** ("585 tiny breath-holds a day"; the doctor who cracked one hand for 60 years and not the other).
- **A share line aimed at a person:** "send this to your knuckle cracker". This is the share we measure.
- **A perfect loop:** the last line is the first line ("Did you make it? Now try not to think about it" cuts back to "DON'T SWALLOW").
- Short caption lines at the top, one keyword in yellow, a big number at the top center.

Their account also shows the limit. In the weeks after those two, most of their reels got 3K to 14K views (Nov 10), so direction alone doesn't carry an account. The topic still has to be one people send to each other. The direction is what makes the reels that do get sent look worth sending.

## The shot sheet (goes in `ops/episodes/<id>.md` before any scene code)

Start with the look (four hex colors and what each is for) and the big moment (the word, the event name, what changes). Then fill in one row per shot:

| # | Cuts in on | Job | Eye: what, and where on screen (x, y) | Light: source, side, what falls dark | Depth: fg / subject / mid / bg | Lens, height, move | Beat: breath, hit, settle | Intensity 1-5 |
|---|---|---|---|---|---|---|---|---|

Read each row aloud. If a row could describe any reel, it isn't directed yet.

## In code

`pipeline/direct.py` turns the rows into the camera and the light levels on every frame:

```python
import direct as D
rig = D.Rig(cam, {"key": key, "fill": fill, "rim": rim, "tv": tv_light})
SHOTS = D.ShotList([
    D.Shot("hook", 0.0, eye=(0, 0.4, 1.3), lens=50, dist=4.5, yaw=0, pitch=-4, screen=(0.5, 0.55),
           light={"tv": 1, "key": 0, "fill": 0.15, "rim": 1}, note="lit by the TV only"),
    D.Shot("punch", E["collapses"] - 0.05, eye=(0, 0.4, 1.5), lens=50, dist=3.0, screen=(0.5, 0.5),
           hit=E["collapses"], move=("punch", 1.4), kick=0.03, light={"tv": 0.2, "flash": 1, "rim": 1.5}),
], end=DUR)
SHOTS.check()                                   # warnings go to the render log
SHOTS.dump(os.path.join(OUT, "shots.json"), big=E["collapses"])
def apply_state(t):
    SHOTS.apply(rig, t)                         # camera, lens shift, depth of field, light levels, key placement
```

- `screen=` is where the eye lands, as (x from left, y from top) fractions. It is framed with lens shift, so verticals stay straight.
- Moves: `still`, `push`, `pull`, `orbit`, `crane`, `punch` (a cut-in on the hit), `push_on_hit` (waits, winds back, lands on the hit).
- Timing helpers for anything that moves: `ars`, `hold`, `flash`, `kick` and `on_twos`.

## The check

`python pipeline/qa_direction.py <video.mp4> <out_dir>/shots.json <sheet.png>` measures, per shot:

- whether the eye's spot pulls hardest (eye rank, aim for 0.8 or more);
- whether the light is on the subject (light focus: near the eye vs far from it, aim for 1.4 or more; our Schrodinger frames measure 1.0 to 1.3, the lighthouse reel 1.4 to 1.85);
- muddiness and value range.

For the whole reel it reports whether the biggest change inside a shot lands on the big moment, the shot rhythm, and the loop. It also saves a sheet with a cyan ring where the shot puts the eye and a magenta square on what actually pulls. A shot may break a rule on purpose (a silhouette is meant to be dark); write why in the shot's `note`.
