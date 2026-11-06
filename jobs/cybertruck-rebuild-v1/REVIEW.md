# REVIEW — Cybertruck reference reconstruction (v3)

**Deliverable:** `renders/cybertruck-rebuild-v3.mp4`, H.264 2160×3840, 30000/1001 fps,
664 frames, 22.155467 s, AAC 256 kb/s (the reference audio).
**Editable source:** `project/` (Three.js r187; see `project/README.md`, `SPEC.md`, `ASSETS.md`).
**Comparisons:** `comparison-v3/` (social compare), `preview/final_cmp.jpg` (reference top, render bottom).

## What matches

- **Format and sound:** dimensions, frame rate, frame count and duration match exactly (compare tool:
  `dimensions_match`, `fps_match`, duration delta 0.0). The audio is the reference track,
  sample-aligned (cross-correlation lag 0). The residual is about 29 dB below the signal, which is
  AAC re-encoding only.
- **Structure and timing:** every sequence is rebuilt in 3D, in order, with timings measured from
  native-rate frames:
  - baby close-up with the harness and ropes appearing
  - pull-back to the wide shot, rush to ground level, low straining crawl
  - pull-back over **5,000** instanced babies with ropes
  - card-flip transition (edge-on at 7.905 s)
  - anaconda ambush, with snakes swallowing babies and a huge body passing the lens
  - second card flip (edge-on at 10.41 s)
  - one snake, then a pull-back over **160** instanced snakes on ropes
  - zoom-blur whoosh into the strongman: he points at the camera, steps back, stands with snake tow-ropes, bends to pick them up and pulls the trucks
  - three-quarter orbit with a second, lower-half figure and a blood-drip trail
- **Subtitles:** all 27 caption groups switch on the exact reference frames (detected from the
  subtitle band). Verdana Bold, white with black outline and drop shadow, at the measured size and
  baseline. At 4K the line width is within about 1% of the reference.
- **Environment:** turquoise ground, white grid, bold centre line, blue sky with clouds and a pale
  horizon, sun shadows. Colours were measured against the reference; the opening and the
  herd shots are within a few sRGB levels at the sampled points. The strongman section uses its paler
  ground and finer grid.
- **Camera language:** real per-frame motion blur, depth of field in the opening, accelerating and
  decelerating pull-backs, and the orbit at the end.
- Mean frame MAE is 50.7/255 (it was 65.5 in the first draft). The worst frames are now 93.7 (crowd pull-back, 4.20 s), 83.4 (whoosh, 15.65 s) and 78.3
  (second flip, 10.44 s). These are diagnostics only, not a similarity percentage.

## What is approximate or different (honest limits)

- **No original assets exist.** The user confirmed only the MP4 is available. All characters are
  substitutes:
  - **Baby:** the three.js Xbot mannequin rig, re-proportioned by bone scaling, with a procedural
    cartoon head and a shader-painted diaper and red harness. The reference has a realistic, fully
    modelled toddler with a detailed face, a 3D harness with buckles, and a grimace. Ours reads as a
    stylised mannequin baby, with visible segment seams at the joints and a pale, simple face.
  - **Strongman:** the Xbot rig bulked up, with the CC-BY "Lee Perry-Smith" bald head scan, black
    trunks, knee pads, boots, arm bands and a procedural shoulder "tattoo". **This is not a likeness of
    Dwayne Johnson**, and the body has neither his musculature nor the reference's skin detail. It is a
    smooth mannequin torso with segment seams. The trunks carry abstract white marks, not the
    reference's "ROCK" logo.
  - **Lower-half figure:** the same rig cut at the waist with a stylised flesh/bone cap and a red
    splat trail. It is cruder and less gory than the reference.
- **Trucks:** a procedural faceted Cybertruck-style loft, with glass, black cladding, light bar and tyres. The
  silhouette and the front with exposed tyres are close. The panels are simpler than the reference
  model, and the chrome shows less of the reference's pink/lilac reflection.
- **Snakes:** procedural tubes with a black/yellow-spot skin and an olive spotted head. They are smoother
  and more regular than the reference anacondas, and the swallowing is a placement trick (the baby is
  parented at the jaw), not a deformation.
- **Crowd:** low-poly baked crawl poses (4 phases). Ground darkening under the crowd stands in for the
  reference's dense shadowing, and the field still reads redder/pinker than the reference's
  blue-purple. Several cameras are hand-matched by eye, so framing differs by roughly 5–15% in places,
  especially in the ambush and strongman shots.
- **Poses** are procedural (aim-based) on top of the Mixamo-derived idle/walk/run clips. The bend, the pull
  and the pointing are less expressive than the reference animation.

## Re-render / edit

`cd project && node render/video.cjs ../renders/out.mp4 2160 3840 8` (about 2 minutes). Shot timing and
cameras are in `project/src/shots.js`.

Earlier versions are kept for traceability:
- `renders/cybertruck-rebuild-v1.mp4`, `-v2.mp4`: v1 had the second flip one frame early and a distant strongman lunge.
- `renders/draft*-540.mp4`: quick low-resolution drafts.

---

# v4: character fidelity pass (`renders/cybertruck-rebuild-v4.mp4`)

v3 is preserved unchanged (`renders/cybertruck-rebuild-v3.mp4`, `project-v3-baseline/`). v4 has the same
timing, captions and reference audio: 2160×3840, 30000/1001 fps, 664 frames, 22.155467 s.
The audio residual against the source is −28.8 dB, which is AAC encoding loss only.

**What changed**
- **Bodies:** the segmented Xbot mannequin surface is replaced by continuous CC0 MakeHuman meshes
  (baby and young-male targets), skinned onto the same Xbot skeleton, so every existing pose,
  clip and camera still applies. The baby now has natural toddler proportions and a real modelled
  face, and the 5,000-baby crowd uses the same body. The strongman is a muscular continuous body
  with extra arm, shoulder and chest mass.
- **Strongman face:** a crop of the reference face is projected onto the front of the 3D head, giving
  the angry brow and nose/mouth character of the reference. This is a projected texture on generic
  geometry, not a modelled likeness. From the side the head shape is MakeHuman's, and the crop's
  eyes are flat paint, not eyeballs. It is still not a faithful Dwayne Johnson likeness.
- **Evidence:** before/after stills at 0.5, 3.0, 16.7, 18.3 and 20.5 s are in
  `preview/v4hero/compare.jpg` (rows: reference / v3 / v4). There is also a full-film sheet at
  `preview/sheet_v4.jpg`.

**Still different (honest)**
- **Baby face:** MakeHuman's generic baby face, with no reference texture. The only usable reference
  crop is blurred, looks down and is edged by the red harness. The harness and diaper are still
  painted bands on the skin, not 3D straps with buckles.
- **Strongman body:** the tattoo is still procedural rings, not the reference tribal design. The
  trunks logo is abstract. The skin lacks the reference's detail and specular quality. The boots are
  painted on bare-foot geometry.
- **Bend pose:** at about 17.0–17.6 s the reference bends down to pick up the snakes. In v4 the bend
  reads as nearly upright. This is a regression from v3, because the bend deltas were tuned on the
  Xbot joint layout.
- **Not changed in v4:** the trucks (still the faceted procedural loft), the snakes and the crowd
  colour. The crowd field still reads redder than the reference.

---

# v5: strongman likeness and anaconda swallowing (`renders/cybertruck-rebuild-v5.mp4`)

Earlier versions are preserved (`renders/cybertruck-rebuild-v1..v4.mp4`, `project-v3-baseline/`, `project-v4-baseline/`).
Review copy: `renders/cybertruck-preview-v5.mp4` (720×1280, faststart).

**Verified:** the 4K file is 2160×3840, 30000/1001 fps, 664 frames, 22.155467 s, and decodes fully with no
errors. It carries the reference audio: cross-correlation lag 0 samples, residual −28.8 dB (AAC encoding only).
Timing, subtitles and the other shots are unchanged.
**Comparison sheets** (rows: reference / v4 / v5):
- `preview/v5-focused/final_ref_v4_v5.jpg`
- `swallow_ref_v4_v5.jpg`, `swallow3_ref_v4_v5.jpg`
- `dwayne_ref_v4_v5.jpg` (consecutive bend frames 16.98–17.58 s)

**Swallowing (8.1–10.3 s), now an actual action**
- **Snake heads:** rebuilt as an open upper skull with a pink palate, a hinged lower jaw (gape up to about 50°)
  with a tongue floor, two rows of teeth and a dark throat. On the strike the head lifts and pitches.
- **Capture:** each hunting snake slows on contact and slides over its baby head-first. Everything
  behind the moving mouth plane is clipped, including the baby's shadow, so the baby disappears
  progressively into the mouth: head, then torso, then legs. There is no teleport and no scaling to zero.
- **After:** the jaw closes and a bulge travels down the body. The rope now trails out of the mouth.
- **Staging:** the two hero captures happen at about 8.4–9.3 s and 9.5–10.4 s, framed like the reference.
  The giant foreground body sweeps the lower frame from about 9.8 s.
- **Content:** no blood or wounds were added involving babies.

**Strongman**
- **Head and build:** the head is reshaped in the continuous mesh: broader square jaw, chin forward,
  heavier brow, wider nose, slightly larger head. Neck, trap and foot mass are added, with more deltoid,
  biceps and quadriceps bulk. The body is continuous; the projected face still shows visible texture/geometry mismatches.
- **Tattoo:** the procedural rings are replaced by the reference tattoo, extracted as an ink mask from
  the 18.3 s frame and projected onto the left pec and shoulder. It shows the sun-face disc, the rays and
  the upper tribal crescent.
- **Trunks logo:** a projected "THE ROCK" mask from the same crop.
- **Bend/pickup (16.86–17.55 s) rebuilt:** hip hinge, bent knees, rounded back, and arms hanging to the
  ground where the two snake heads now lie. The hands visibly reach and lift them. He also stands
  nearer the trucks, matching the reference staging.

**Still approximate (honest)**
- **Likeness:** the face is still a crop projected onto generic MakeHuman geometry. It has the
  reference's frown, nose and mouth from the front, but in profile and three-quarter views the cheek
  and ear areas show the generic head, and the eyes are painted. This is not a scanned or modelled
  Dwayne Johnson asset.
- **Tattoo:** its upper part, over the shoulder and down the arm, is incomplete (the mask was weak
  in the shaded crescent). It does not continue onto the deltoid or biceps as in the reference.
- **Material and gear:** skin is a single smooth material with no pores or specular breakup. The boots
  are paint over bare-foot geometry.
- **Swallow geometry:** snakes are still smooth tubes. The jaw is a rigid hemisphere hinge, not
  stretching mouth tissue. The prey bulge is subtle. In the reference the closest snake's head is
  larger and more detailed.
- **Half figure (≈19.3 s onward):** unchanged from v4.


**Full-timeline v5 comparison:** all 664 frames were compared at 320 px analysis width. Mean absolute pixel error is 50.221/255; this is not a similarity percentage. Dimensions and rational fps match, and duration difference is 0 s. See `comparison-v5/index.html`.

**Additional face QA:** temporary surface-eye and curved portrait-relief experiments were inspected under `preview/v5-face-qa/` and `preview/v5-face-relief/`. They were rejected because of eye/texture misalignment and poor side-view/neck joins. They are NOT used in the delivered project or video.
