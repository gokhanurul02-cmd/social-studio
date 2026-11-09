# Agent production workflows

Tool root: `.`.
PowerShell reliable entrypoint (also works before PATH refresh):

```powershell
& './social.cmd' --help
```

`social` is a local tool CLI. Codex or Claude supplies editorial reasoning and writes editable
video source. There is no hidden background LLM, no promise that a CLI template alone reconstructs
arbitrary video, and no automatic paid API calls. Local skills work in local Codex / Claude Code
sessions, not automatically in the claude.ai website or remote Cowork.

## Analyze a video

`social analyze 'ABSOLUTE_VIDEO_OR_URL' --out 'NEW_JOB/analysis'`
Defaults: Turkish, Whisper large-v3-turbo, CPU int8. Both large-v3-turbo and small are pre-cached.
Use `--model small` for a faster draft with lower Turkish accuracy. For another language add `--language auto` or language code.
Read `analysis.json`, `scenes.json`, `transcript.json`, `frames.json`; open `contact-sheet.jpg` and the
individual cut-adjacent frames. Scene detection is a candidate list, not ground truth. Verify jump
cuts, speed ramps, dissolves and text changes visually. Inspect the start/end of every word group.
The installed detector uses `min_content_val=3` rather than the stock 15, so cuts between motion
layouts sharing a white/dark background are not silently lost. CLI `--scene-threshold N` raises
or lowers that floor; `--min-scene SECONDS` controls the minimum shot length (default 0.3s).
For silent footage add `--no-speech` to avoid a model call. Model cache is shared in the user's
Hugging Face cache; do not modify another tool's Python environment.

Produce a concrete analysis: hook, target audience, narrative beats, shot timing, text density,
readable safe areas, colour/font measurements, visual hierarchy, motion direction/easing, sound
events and reuse opportunities. Separate observed facts, inferred style and proposed changes.

## Rebuild a reference

Current priority: reproduce a specific reference video made with Claude Code. The generic
Social Studio demo was rejected by the user and is not an approved style or quality benchmark.
Without the reference, ask for the video/link; do not create a substitute demo. If the public
original source project is available, inspect/reuse it before reconstructing from pixels alone.

Analyze first. Keep the exact reference dimensions, rational fps, duration, text and audio when
the user asks for the same video. If the user asks to adapt it, retain the useful style/timing but
change the requested content. Write `SPEC.md` with measured shot boundaries and layer/source table.
For an exact remake, the supplied reference outranks saved brand templates. Use existing brand
skills only when the user requests a brand adaptation. Those reference sources live in
`agent-skills/codex/`.

Choose the engine from the actual reference/source (Remotion, HyperFrames, canvas, Three.js),
not from an installed template. Match a representative scene before extending it to the film.
Three.js r187 (`three@0.187.0`) is installed in this tool root's node_modules. Core, GLTFLoader,
OrbitControls and other bundled addons share that release. New jobs under `jobs/` can import
`three` through Node/bundler resolution; browser-only modules need an import map/local server.
For 3D exports derive all scene/camera state from seek(time/frame) so frame captures are repeatable.
`node check_three.cjs` verifies a real WebGL2 render, addon imports and seek-dependent frames.
When choosing HyperFrames, use `social hf init 'NEW_JOB/project' --skip-skills --non-interactive` then edit the root size/fps
and duration. Read the official HyperFrames format/runtimes docs before writing composition HTML.
Use one editable sub-composition per shot, local assets and a paused deterministic timeline.
Use local GSAP from `node_modules/gsap/dist/gsap.min.js`, copied into project assets; ship local
fonts as files. Do not depend on CDN responses at render time. Search `social hf catalog --help`
and the registry before hand-building named components. Package paths are pinned by package-lock.

Rebuild typography, cards, shapes, camera moves and timing as editable layers. Photographic footage
and people require the original assets or newly created replacements; document replacements.
Do not use the original full video as a background and claim the layers were reconstructed.
The built-in `reverse-any-video` is a separate Pro workflow; this local workflow does not invoke it.

When keeping original sound, use one timed audio element with an id and mute visual footage.
Do not regenerate approved voices for a visual-only edit. Add needed effects with Earshot.
After structural edits run `social hf check 'PROJECT' --json`. Fix errors; inspect warnings.
Capture representative frames and entrances/exits: `social hf snapshot 'PROJECT' --at 0.5,2,4`.
Open the actual PNG files. Before the delivery render, start the editable preview:
`social hf preview 'PROJECT' --background`; verify its printed URL responds. There is no need
to wait for another approval because this user asked to finish autonomously.

`social render 'PROJECT' --out 'NEW_JOB/final-v1.mp4'`
`social compare 'SOURCE.mp4' 'NEW_JOB/final-v1.mp4' --out 'NEW_JOB/comparison-v1'`

If the output mix is outside the requested target, use
`social master 'NEW_JOB/final-v1.mp4' --out 'NEW_JOB/final-master.mp4'`.
It performs two-pass loudness mastering to -16 LUFS / -1.5dBTP and copies the video stream.

Review the comparison's worst moments and frames around cuts. `compare` scores every decodable
overlapping frame at 320px analysis width; dimensions, fps and duration are checked separately.
Different dimensions are rescaled for diagnostics, never treated as a perfect match. MAE/PSNR
are image metrics, not a percentage guarantee of perceived similarity. Audio offset and timbre
must be checked separately with the waveform/listening tools and Earshot. Fix visible defects,
render a new version and save `REVIEW.md`: what was rebuilt, what is approximate, actual metrics,
remaining gaps and full absolute output paths. Deliver the playable MP4 and editable project.

## Create a new video

Turn the brief into a precise hook, voice script, shot map and CTA. Reasonable defaults for a
new Reel: 1080×1920, 30fps, 15–30s; reference/brand/user instructions override these. Use concrete
visual metaphors, distinct shot layouts, large readable type and a strong opening. Use real logos,
not invented replacements. Existing brand skills supply approved fonts/layouts.
Create a job; write script and SPEC; record voice once if requested; derive actual speech timing
with `social transcribe`; compose to the voice. Follow the same check/snapshot/render workflow.
Use Remotion instead when React/source compatibility calls for it. Read
`agent-skills/codex/remotion-best-practices/SKILL.md`; `social remotion` wraps its CLI.

## Voice and sound

```powershell
social voice --file 'JOB/script.txt' --voice tr-TR-EmelNeural --out 'JOB/voice.mp3'
social voice --text 'Merhaba.' --voice tr-TR-AhmetNeural --out 'JOB/male.mp3'
social transcribe 'JOB/voice.mp3' --out 'JOB/speech'
social sfx sfx list --kind whoosh
social sfx sfx render swipe/glide -o 'JOB/glide.wav' --dur 0.5 --apex 0.16 --peak -16
social sfx sfx check 'JOB/glide.wav'
social sfx measure 'JOB/final.mp4' --json
```

Edge TTS is online and sends the supplied text to Microsoft's service; no API key is needed.
Emel/Ahmet are standard Turkish voices, not voice clones. Word timestamps from Whisper are
estimated and need spot checks. The Edge draft SRT is sentence-level, not word-level.
Premium ElevenLabs adapter: `social voice --provider elevenlabs --voice VOICE_ID ...` uses the
user's `ELEVENLABS_API_KEY` environment variable. It is optional and has not been billed/tested.
Never print secrets. Inspect account availability before making provider-specific promises.

Earshot is already installed under `../earshot-main`; preserve its environment and model cache.
Align the effect's measured peak (not its file start) to the visual accent: start = accent - peak_s.
Use `kit init --help` / `kit render --help` for whole kits. Explicitly place each effect as audio
in the project; creating files does not mix them into video. Start subtle under speech, vary
the sound vocabulary and avoid a whoosh on every element. Target roughly -16 LUFS and ≤-1.5dBTP
for social narration as a starting point; check the encoded final file. Loudness is not aesthetics.

## Plan and performance

`social plan --brand 'BRAND' --days 30 --start 2026-11-06 --out 'JOB/plan'`
This creates a DRAFT scaffold. The agent must fill every hook/script/caption/CTA from the user's
brand, services and actual audience; do not deliver blank generated rows as a completed AI plan.
No universal best posting hour: 19:00 is explicitly a placeholder until account data is available.
Track content pillars, offer frequency, audience intent, production assets and measurable tests.

For account exports use a CSV/JSON list with `id,platform,date,format,topic,views,reach,likes,comments,shares,saves`
(optional columns may be absent). Normalize Turkish/platform-specific headers and decimal formats
into a new file before `social analytics 'NORMALIZED.csv' --out 'JOB/performance.json'`.
Do not mix reach-based and view-based engagement rates; missing metrics are marked.
Read the actual source data and sample size before recommending content. Live account access
can use Postiz once the user's account is connected; no invented trend or competitor metrics.

## Postiz publishing

The user says Ömer at the office owns/develops the existing Postiz system. Preserve that
installation; do not default to a separate cloud login, duplicate server or new deployment.
Until its URL/auth/API compatibility is supplied, create a provider-neutral draft package:
`social handoff 'FINAL.mp4' --caption-file 'caption.txt' --brand 'BRAND' --platform instagram --out 'JOB/postiz-handoff'`.
This produces a ZIP with video, auto-selected cover, caption, SHA-256 records and publication.json.
The schema is `social-studio.handoff.v1`, not a native Postiz request body; Ömer's integration
maps it to the existing server's actual API. No upload or posting happens in this command.
See `POSTIZ-OMER-NOTU.md` for the minimal integration details to obtain.

The bundled CLI's `auth:login` uses its own auth server (default cli-auth.postiz.com); setting
POSTIZ_API_URL alone does not turn that login into the existing self-hosted server's OAuth.
For a compatible existing API, resolve its base URL and credentials with the owner first.

`social postiz auth:status`, `social postiz auth:login`, `social postiz integrations:list`.
API keys are optional if OAuth is connected; `POSTIZ_API_KEY` also works. The CLI is installed;
the Postiz server/account and platform OAuth approvals are separate prerequisites. Docker is
not installed; no self-hosted server was started. Postiz's exact Node 22.23.4 requirement
is satisfied by `runtimes/node22/node.exe`; only this CLI uses that isolated runtime.
The user's system Node 24.19 remains the runtime for HyperFrames and Remotion.

Prepare the exact media, caption, platform settings and Europe/Istanbul timestamp first.
Inspect current `social postiz posts:create --help` and integration settings, then upload the
actual file with `social postiz upload`. Use returned media paths/IDs. Save the exact proposed
payload and receipt in the job. A request merely to create a video does not ask to publish it.
When the user explicitly asks to publish/schedule with sufficient details, do so without
redundant approval; otherwise deliver the draft for review. Verify returned post status/date.

## Inbox

`social inbox 'FOLDER'` analyzes existing stable files once.
`social inbox 'FOLDER' --watch` stays in the foreground, checks every five seconds, and skips
files modified in the previous five seconds. Stop with Ctrl+C. Its local journal records analyzed
file identities. It prepares analysis, not autonomous video recreation. To rebuild the newest
analysis, invoke social-rebuild in a local Codex or Claude session. Do not imply a watcher is
running unless its process has actually been started and remains alive.
