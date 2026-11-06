# Measured reference spec (from `reference-source.mp4`)

2160×3840, 30000/1001 fps, 664 frames, 22.155467 s, Opus stereo 48 kHz. Single continuous 3D
render with internal transitions (the scene detector found no hard cuts).

Current delivery override (user, 5 November 2026): 1080×1920 final output; 540p/720p
short previews. Keep original fps, timing and audio. Existing v1–v5 4K files are historical.

## Shots (refined from consecutive native-rate frames)

| Time (s) | Content | Camera | Rebuild (`src/shots.js`) |
|---|---|---|---|
| 0.00–1.37 | Baby standing between/ahead of two trucks; rubs eye; harness appears ≈0.30; arms out; ropes attach ≈0.90; head turns ≈1.0 | Chest height, long lens, strong DOF on trucks | `shot_baby`, cam `baby` keys 0–1.37 |
| 1.37–1.74 | Fast pull-back/up to wide; baby drops to crawl | ease-out | keys 1.37→1.74 |
| 1.74–2.30 | Wide: trucks + tiny baby on ropes | static drift | hold |
| 2.30–2.64 | Rush down to ground level | motion-blurred push | keys 2.30→2.64 |
| 2.64–4.05 | Low close: baby crawling and straining, giant tyres behind | creeping | keys 2.64→4.05 |
| 4.05–7.90 | Pull-back over a wedge of 5,000 babies with ropes to the trucks | accelerate, then decelerate high/far; slight yaw/roll | `shot_crowd`, instanced crowd (4 baked crawl phases) |
| 7.785–8.09 | Card flip about vertical centre axis (edge-on ≈7.905), black surround | ~90° virtual lens | `TIMELINE.flips[0]`, card shader in `main.js` |
| 8.09–10.27 | Low side view: crawling babies with ropes; anacondas catch babies (first ≈8.5); huge snake body passes the lens | tracking right | `shot_ambush` |
| 10.27–10.56 | Second card flip (edge-on ≈10.385) | | `TIMELINE.flips[1]` |
| 10.56–11.25 | Trucks facing camera, one snake slithering toward camera on a rope | high, static | `shot_snakes` |
| 11.25–15.40 | Pull-back revealing 160 snakes in a wedge with ropes | ease, rising | instanced `SnakeHerd(180)`, 160 lanes |
| 15.40–15.78 | Zoom/radial-blur whoosh into the strongman | | `TIMELINE.whoosh` |
| 15.58–16.45 | Strongman lunges at camera pointing, then steps back in front of trucks | close → medium | `shot_rock` |
| 16.45–17.60 | Stands with two snake "ropes" on the ground; bends to pick them up | static | |
| 17.60–19.05 | Pulls the trucks toward camera (walk clip + lean) | slow | trucks begin rolling ≈17.75 |
| 19.05–19.50 | Camera orbits to front-left three-quarter; a lower-half figure appears | eased orbit | |
| 19.50–22.155 | Both walk; blood drips trail behind the half figure | slow follow | |

## Subtitles (frame-accurate, detected from the subtitle band)

27 groups, start frames: 1 If you · 9 strapped a · 27 baby · 41 to a pair of · 57 Cybertrucks ·
85 to pull them · 109 you would need · 128 5000 of them · 174 just to · 189 make them move ·
224 Now if you did · 244 the same thing · 270 with anacondas · 306 it would take · 326 at least ·
337 160 · 375 of the giant snakes · 410 to pull the truck · 447 But if you got · 466 Dwayne the Rock ·
493 Johnson · 509 to tow the trucks · 546 you would need · 563 just one · 581 and a half of him ·
611 to get them · 631 rolling · 647 (none to end). Frame 0 has no caption.

Style: Verdana Bold look, white fill, ~0.06 em black outline, down-right black drop shadow
(offset ≈0.045 em, slight blur), centred, baseline y≈3052 px; size calibrated so
"of the giant snakes" spans ≈1432 px (measured on the reference).

## Palette (sRGB, sampled)

Sky zenith ≈#0fbaea, upper ≈#2cc9eb, horizon pale lavender-white; ground sunlit ≈#2fbee4 with
white grid and bold centre line; strongman section ground paler ≈#96d7e4–#a3dee7.
