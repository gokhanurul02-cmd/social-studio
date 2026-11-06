"""Install scoped local agent skills; do not change unrelated account/configuration settings."""
from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parent
USER = Path.home()
WORKFLOW = ROOT/'WORKFLOWS.md'
SKILLS = {
    'social': ('Route local social media production, reference analysis, planning, voice and video requests.',
               'Read the supplied request. Select the applicable workflow section and complete the requested deliverable with the installed tools. If no task is supplied, show a compact command menu from the guide.'),
    'social-analyze': ('Analyze a supplied reference video or URL: shots, timing, speech, visual style and audio.',
                       'Complete Analyze a video. Open the frame sheets and individual frames. Deliver an observed shot/style breakdown plus concrete remake instructions, not only technical metadata.'),
    'social-rebuild': ('Recreate a reference video as editable code and a finished MP4, with measured comparison.',
                       'Complete Rebuild a reference from analysis through editable source, actual render, comparison and fixes. Finish autonomously with a playable MP4. If the source is an analyzed inbox job, reuse its analysis.'),
    'social-create': ('Create a finished social video from a brief, brand or script using local code tools.',
                      'Complete Create a new video. Use the appropriate approved brand skill where applicable. Render and verify the finished MP4 and keep editable sources.'),
    'social-plan': ('Create a filled social content strategy and calendar with hooks, scripts, captions and CTAs.',
                    'Complete Plan and performance. Use the CLI only for the scaffold, then fill the actual calendar. Deliver specific publishable copy and production instructions for every requested day.'),
    'social-voice': ('Generate Turkish narration with timing and reusable audio files.',
                     'Complete Voice and sound for narration. Preserve supplied/approved audio when only visuals need edits. Check generated file and provide sentence or word timing as requested.'),
    'social-sfx': ('Generate and place sound effects matched to motion, then inspect the final mix.',
                   'Complete Voice and sound for effects. Measure peak timing, place sounds in the project and inspect the encoded mix; do not just generate an unconnected effects folder.'),
    'social-check': ('Review a finished video for technical, visual and audio defects or reference differences.',
                     'Run check, inspect representative decoded frames, inspect audio measurements and compare if a reference exists. Report real defects with timestamps and fix them if requested. Do not equate a decode pass with artistic quality.'),
    'social-analytics': ('Analyze real social post performance exports or connected Postiz account metrics.',
                         'Complete Plan and performance using real records. Normalize fields, compute metrics with the CLI, compare within platform/format/payda cohorts and produce evidence-based next tests. State absent data.'),
    'social-publish': ('Prepare, schedule or publish approved media through the installed Postiz CLI.',
                       'Complete Postiz publishing. First check authentication and integrations. Use the user request to determine whether to prepare a draft or actually publish/schedule; verify the resulting status.'),
    'social-inbox': ('Process videos dropped into a local folder, or rebuild the newest analyzed reference.',
                     'Complete Inbox. A foreground watcher analyzes only; if the user asks for a finished rebuild, invoke the Rebuild a reference workflow for the selected/newest source and finish it.'),
}
paths = []
for name, (description, instruction) in SKILLS.items():
    for base in [USER/'.agents/skills', USER/'.claude/skills']:
        folder = base/name
        target = folder/'SKILL.md'
        if target.exists() and 'social-studio' not in target.read_text(encoding='utf-8'):
            raise RuntimeError(f'Existing unrelated skill would be overwritten: {target}')
        folder.mkdir(parents=True, exist_ok=True)
        text = (f'---\nname: {name}\ndescription: {json.dumps(description, ensure_ascii=False)}\n---\n\n'
                f'# {name}\n\nThis is the local social-studio integration.\n\n'
                f'Read `{WORKFLOW.as_posix()}` and only its relevant workflow sections.\n'
                f'Tool entrypoint: `{(ROOT/"social.cmd").as_posix()}`. Quote its full path in PowerShell.\n\n'
                f'{instruction}\n\nUse the actual user request and attached files as inputs. '
                'Preserve approved brand assets and create versioned job outputs. '
                'Do not claim account connection, a successful render, or reference fidelity without evidence.\n')
        target.write_text(text, encoding='utf-8')
        paths.append(str(target))

# Official skills are canonical under .agents/skills (legacy installer fallback: .codex/skills).
# Their references use relative sibling paths; preserve the entire directories.
for name in ['hyperframes','hyperframes-cli','hyperframes-registry','media-use','remotion-best-practices']:
    source, dest = USER/'.agents/skills'/name, USER/'.claude/skills'/name
    if not source.exists():
        source = USER/'.codex/skills'/name
    if not dest.exists():
        shutil.copytree(source, dest)
        paths.append(str(dest/'SKILL.md'))

local_bin = USER/'.local/bin'
local_bin.mkdir(parents=True, exist_ok=True)
shim = local_bin/'social.cmd'
if shim.exists() and 'social-studio' not in shim.read_text(encoding='utf-8'):
    raise RuntimeError(f'Existing command would be overwritten: {shim}')
shim.write_text(f'@echo off\ncall "{ROOT / "social.cmd"}" %*\nexit /b %errorlevel%\n', encoding='utf-8')
(ROOT/'integrations.json').write_text(json.dumps({'skills': paths, 'terminal_shim': str(shim)}, indent=2), encoding='utf-8')
print(f'{len(SKILLS)} workflows installed for Codex and Claude; official skills copied for Claude.')
