# Cybertruck pull — editable Three.js reconstruction

Three.js r187 scene rendered in headless GPU Chrome. Every frame is produced by
`window.renderFrame(frame)` (seek-driven, no wall clock): 8 sub-frame samples per frame give
motion blur, thin-lens depth of field and anti-aliasing (24 samples in the shallow-DOF opening).

```
src/main.js        renderer, sample accumulation, card-flip + zoom-whoosh compositing, grade, subtitles
src/shots.js       timeline, camera keys, staging of every shot, subtitle table   <- main edit point
src/env.js         sky/clouds shader, turquoise grid ground, sun + image-based lighting
src/truck.js       procedural faceted Cybertruck-style pickup
src/characters.js  Xbot-rig babies / strongman (bone re-proportioning, aim poses, shader-painted clothing), heads
src/props.js       instanced slithering snakes, snake tow-ropes, instanced red ropes, blood splats
render/video.cjs   full render -> MP4 with the reference audio
render/stills.cjs  render chosen frames:  node render/stills.cjs OUTDIR 540 960 8 t1.9,t12.5,600
render/debug.cjs   stage a single rig/pose for inspection
```

Render the film at the default 1080×1920 resolution from this directory:

```
node render/video.cjs ../renders/out.mp4
```

The repository root supplies `node_modules` (Three.js and Playwright) and `bin/ffmpeg.exe`.
The harness serves Three.js and the Windows Verdana Bold font locally. See the [root setup](../README.md) for restoring the reference audio and rig files.
See `SPEC.md` for measured shot/subtitle timings and `ASSETS.md` for asset licences.
