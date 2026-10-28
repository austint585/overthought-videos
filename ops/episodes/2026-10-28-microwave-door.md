# The dots on your microwave door

- **id:** 2026-10-28-microwave-door
- **Source idea:** Austin's DM, Oct 27 (https://www.instagram.com/p/De_42nKxoyZ/, @how_it_secretly_works): more 3D "how the stuff people use daily works" episodes, opened with a hook that makes a familiar thing feel like it quietly matters to you. The microwave door mesh was first on our explainer backlog (CLAUDE.md, next steps 5) and is not one of @speedy_devv's topics.
- **Format:** 3D voxel explainer, a kitchen and a microwave whose lid lifts off, about 37 s. Hook on frame 1: "The dots on your microwave door".

## Script (render_tap markup)

1. Those *dots* on your microwave door have *one job.*
2. Inside, a *magnetron* makes microwaves at *2,450 megahertz.*
3. That makes each wave about *12 centimeters* long.
4. They make the *water* in your food *shake,* and that's the *heat.*
5. The metal walls bounce them *back in.* But you want a *window.*
6. So the glass has a *metal sheet* with holes a *millimeter* or two wide.
7. A *12-centimeter* wave can't get through. It *bounces back.*
8. *Light* waves are *thousands* of times smaller than the holes, so they go *right through.*
9. And by law, *two* separate *switches* cut the power the second you open the door.
10. So you get to *watch* your food cook, without *cooking* with it.

## Facts and sources

| Claim | Source |
|---|---|
| Home microwave ovens use a magnetron at 2,450 MHz | Health Physics Society, https://hps.org/hpspublications/articles/microwaveoven/ |
| Wavelength about 12 cm | Calculation: speed of light / 2.45 GHz = 3.0e8 / 2.45e9 m = 0.122 m. Also https://www.straightdope.com/21343269/what-keeps-microwave-radiation-from-leaking-out-the-oven-door |
| Microwaves make water molecules in food vibrate, producing the heat | FDA, https://www.fda.gov/radiation-emitting-products/resources-you-radiation-emitting-products/microwave-ovens |
| Microwaves are reflected by metal | FDA page above |
| The door window has a metal grid with small holes that light passes through but the microwaves don't | Health Physics Society article above |
| The holes are about 1 to 2 mm across | Straight Dope article above |
| Visible light is about 400 to 700 nm (0.0004 to 0.0007 mm), so a 1 to 2 mm hole is thousands of times wider | standard physics; 1 mm / 0.0007 mm is about 1,400, 2 mm / 0.0004 mm is 5,000 |
| Federal law (21 CFR 1030.10) requires two independent interlock systems that stop the microwaves the moment the latch is released | FDA page above |

## Assumptions, written out

- "Can't get through" is the simple version: a hole much smaller than the wavelength acts as a waveguide below cutoff, so the field dies off within the hole instead of passing. The mesh is not perfect, which is why the FDA also sets a leakage limit (5 mW per square cm about 2 inches from the surface). The script makes no claim of zero leakage.
- The holes in the animation are enlarged so the camera can see them, and the label says so ("holes enlarged"). The waves are drawn at true length (12.2 cm) inside a cavity of roughly real size (60 x 42 x 35 cm outside).
- The water molecules over the soup are an illustration, not to scale.
- The guy, the kitchen and the soup are made up.

## Caption

"The dots on your microwave door are a metal sheet full of holes too small for a 12 cm microwave, but huge for light. Send this to the friend who stands right in front of it. #howitworks #science #physics"
