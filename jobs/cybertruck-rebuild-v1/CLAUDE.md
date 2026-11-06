# Cybertruck reference reconstruction

The user explicitly wants this work done in the visible Claude Code terminal. Recreate the
supplied reference; do not make a generic social promo. Work here and keep source and outputs.
The reference is `reference-source.mp4` (copied unchanged from the user's supplied video).
`reference-original.json` records its original path and exact video metadata.

Analysis is already available in `analysis/`: open contact-sheet.jpg AND individual frames.
The original source is 2160×3840. Latest user preference overrides output resolution:
final target is 1080×1920, 30000/1001 fps, 664 frames, 22.155467 seconds. Preserve the reference audio.
Use 540p/720p short previews of changed scenes, reuse existing analysis and keep context/logs
concise. Do not render 4K or start additional agent sessions unless explicitly requested.
Whisper transcript and word timings are in `analysis/transcript.json`.
The scene detector returned a single scene, but visual inspection shows the distinct sequences
below; use the actual video rather than blindly trusting automatic cuts.

## Observed sequence

- 0–~1.5s: a stylized 3D baby, red towing harness appearing, two silver Cybertrucks behind.
- ~1.5–3.8s: camera pulls back / lowers to show the pair of trucks and a baby pulling ropes.
- ~3.8–7.6s: camera rapidly retreats over a huge field of babies/ropes, illustrating 5,000.
- ~7.6–10.4s: rotating-panel transition introduces giant yellow/black-green anacondas.
- ~10.4–15.5s: one then many snakes on the cyan grid, ropes leading toward the truck pair;
  camera pulls far back, illustrating 160. Another rotating-panel transition follows.
- ~15.5–19s: muscular bald human/Dwayne Johnson-like character in dark shorts and a harness;
  first near the camera, then shown pulling the pair of Cybertrucks.
- ~19–22.155s: camera moves to a three-quarter side view; one whole and a partial second
  figure illustrate "one and a half". Match the reference's actual body treatment on frames.

Persistent design: bright turquoise ground with thin white perspective grid and bold centre
line, blue sky with clouds, reflective silver angular trucks, red ropes/harnesses, white
compact subtitles near the lower-middle with a dark shadow. This is full 3D animation with
assets and lighting; typography alone does not reproduce it. Timings above are approximate:
inspect consecutive original frames around changes and refine them.

## Installed tools

Tool root: `C:/Users/birlik grup/Documents/Codex/tools/social-studio`.
Three.js 0.187.0 is installed under its node_modules, with GLTFLoader/OrbitControls addons.
Real WebGL2 rendering on the RTX 2080 Ti has been verified. Browser executable:
`C:/Users/birlik grup/.cache/hyperframes/chrome/chrome-headless-shell/win64-152.0.7977.30/chrome-headless-shell-win64/chrome-headless-shell.exe`.
On Windows use `--use-angle=d3d11`, `--enable-gpu`, `--ignore-gpu-blocklist` for headless GPU.
FFmpeg/FFprobe: tool-root `bin/`. Node, Playwright, GSAP and Remotion are installed there.
Python: tool-root `.venv/Scripts/python.exe`. Do not call the broken Windows `python` alias.
`social.cmd compare SOURCE OUTPUT --out DIRECTORY` writes frame comparisons. It computes
320px diagnostics; also inspect full-resolution frames for shape, text and character likeness.

## Work contract

Use `/videoyu-kopyala` and the relevant official framework skill. Find appropriate original
or usable public source models if available; keep asset source/license records. Source assets
cropped from the reference can be used as component textures, but do not play the original
full frames as the final animation and claim a reconstruction.
Match the truck geometry, camera, blue grid/sky and a representative character shot before
repeating the treatment through the full film. Missing original character meshes/rigs are a
real fidelity limitation; disclose substitutions instead of claiming perfect replication.
All animation must be driven by seek(time/frame), not wall-clock animation. Use instancing
for large populations. Preserve exact duration/fps and the original audio unless requested.
Render the actual complete MP4, inspect and compare it with the source, then correct obvious
differences. Deliver editable source + video + a short truthful REVIEW.md. A smoke test or a
placeholder cube is not completion. Do not publish, set up Postiz, or create new accounts.

## Latest user clarification

The user confirmed that ONLY the supplied MP4 is available; there is no original 3D project
or model pack to obtain from them. Continue the closest reconstruction possible from the
video and available assets. Do not wait for original files, invent a new visual treatment,
or call placeholder characters an exact match. Show remaining likeness/asset differences.
