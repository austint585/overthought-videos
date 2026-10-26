# Overthought video rules

Every video follows these. They exist so each new format starts from what already works instead of from scratch.

## Look
- Canvas 1080x1920, 60 fps, H.264 CRF 18, AAC 192k.
- Background near-black (12,13,17) with a soft radial lift behind the subject. One accent: orange (255,106,43). Text off-white (243,239,230), secondary text muted (150,148,142).
- Fonts: Bricolage Grotesque 700/800 for words, JetBrains Mono 500-800 for numbers and labels.
- No stock footage, no AI-generated people. Everything is drawn in code.

## Safe zones (Instagram UI covers these)
- Top 160 px: Reels header. Keep text below y=170.
- Bottom 380 px (y > 1540): caption, username, audio. Nothing important there.
- Right edge x > 960 between y=1100 and y=1700: like/comment/share buttons.

## First second
- Motion on frame 1. No fade-in from black, no title card.
- The premise is readable on frame 1 as on-screen text (a question or a challenge).
- A number on screen that will change (counter, timer, countdown) whenever the format allows.

## Holding attention
- Something escalates on a schedule: a counter, a shrinking field, a doubling.
- A visible payoff that viewers wait for (winner, final number, last fold). Tease it early.
- Series hooks when a format repeats: "Part N", "next round", "comment your country".
- Length: 40-60 s for music-only formats; up to 90 s when narrated.

## Sound
- Every visual event gets a sound (bounce, fold, elimination, reveal). Original synthesized audio only, no copyrighted music.
- Loudness around -14 to -20 dB RMS per second after the soft limiter in common.save_wav.

## Narrated formats (when a voice is used)
- Word-by-word captions, top third, with the key word boxed in the accent color.
- Labeled cutaway diagrams with thin leader lines and caps labels.
- Honesty notes in small text where needed ("magnified", "not to scale").

## 3D formats (Blender)
- Real lighting, metal materials, depth of field and camera moves are what make it read as real. Keep the camera moving a little in every shot.
- Dark studio floor and backdrop in the brand near-black. Orange shows up as glows on the part being talked about, red for whatever blocks or fails.
- Labels sit on dark pills so they stay readable over busy geometry.
- Open on the real object in its real place (the door, the phone in a hand) before cutting to the cutaway.

## Facts
- Every number shown is checked against a source before render. Prefer phrasing that stays true at the margin ("almost as tall as you" when 1.64 m vs 1.75 m).

## Captions and posting
- Caption: one or two plain sentences that restate the hook or ask for a comment, then 3 hashtags. No emoji walls, no "you won't believe".
- New formats go out as Trial Reels first (non-followers only), auto-sharing to followers if they perform.
- Every post needs Austin's approval of the exact video and caption before it goes out.
- File names: YYYY-M-D_Descriptive_Name.

## QA before sending
- Pull frames from the encoded MP4 (start, middle, payoff, end) and look at them.
- Check audio levels per second and that sound starts in the first second.
- Confirm nothing sits in the safe zones above.
