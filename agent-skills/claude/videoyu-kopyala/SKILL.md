---
name: videoyu-kopyala
description: Rebuild a supplied reference video as editable code with matching composition, motion, timing and sound. Use for copying or recreating a specific video, not for making a new video from a general content brief.
---

# Referans videoyu yeniden kur

The user wants to reproduce videos people make with Claude Code. Success is fidelity to the
actual supplied reference, not a generic social promo, an inspired redesign or a tools demo.
The earlier Social Studio demo was rejected and is not an approved visual reference.

If no reference video or usable link is supplied, ask for that input in one short message.
Do not generate a substitute example or claim the workflow has proved reference fidelity.
If the reference comes with a public source repository, inspect and reuse the relevant original
project/assets when available rather than guessing how it was built.

## Work from the video

Local tools: `C:/Users/birlik grup/Documents/Codex/tools/social-studio/social.cmd`.
Invoke its quoted full path in PowerShell. Its directory has Python, FFmpeg, HyperFrames,
Remotion/React, GSAP, transcription and image-comparison tools already installed.
Three.js r187 (npm `three@0.187.0`) is also installed there, including addons under
`three/examples/jsm/`. Use it for 3D references when appropriate; keep core and addons on the
same pinned release. For video exports, drive scene state from an explicit seek(time/frame),
not from wall-clock animation. Its real WebGL2 render and addon imports have been checked.

1. Run `analyze REFERENCE --out NEW_JOB/analysis`. Read the actual dimensions, rational fps,
   duration, scene list, transcript and frame sheet. Open the extracted frames. The sheet is
   only an overview: extract consecutive native-rate frames with local FFmpeg around text
   changes, entrances, exits and transitions. The actual video outranks detected cuts.
2. Record the reference's shot boundaries, text, fonts, sizes/positions, spacing, palette,
   assets, motion direction, easing, camera moves and audio accents. Label uncertain measurements.
   Keep reference dimensions, frame rate, duration and sound unless the user asks to change them.
3. Select the renderer from the reference/source: Remotion/React, HyperFrames/GSAP, canvas or
   Three.js as appropriate. Do not select a visual template merely because it is installed.
   Official format guidance is under `C:/Users/birlik grup/.agents/skills/hyperframes/` and
   `C:/Users/birlik grup/.agents/skills/remotion-best-practices/`.
4. Match the first representative scene before extending its treatment across the film.
   This is an internal comparison step, not a mandatory approval pause. Rebuild typography,
   shapes, layouts and motion as editable source. Photographic footage can remain media assets.
   Do not play the original full frame underneath and call that a reconstructed animation.
5. Preserve the reference audio for an exact remake. Do not invent narration, music, effects,
   headlines, brand styling or a CTA. Apply saved brand styles only when adaptation is requested.
   Missing source assets should be identified; disclose any necessary approximation.
6. Render a real MP4. Use `compare REFERENCE OUTPUT --out NEW_JOB/comparison`, inspect the
   source/output/difference images and the native-resolution moments that matter. Check text
   placement and glyphs, transitions frame by frame, and audio timing; MAE alone cannot certify
   similarity. Correct visible mismatches and render a new version before delivery.

Deliver the playable MP4, editable project and a short account of remaining differences.
If an asset or method prevents a close match, say exactly what is missing. A dependency check,
a generic demo or a successful export does not prove that the requested video was reproduced.

Detailed local CLI usage is in
`C:/Users/birlik grup/Documents/Codex/tools/social-studio/WORKFLOWS.md`.
For this request use only reference analysis/reconstruction sections. Postiz, publishing,
content calendars and account analytics are outside the current stage.
