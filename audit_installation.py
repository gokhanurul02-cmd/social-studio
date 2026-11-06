"""Produce an evidence inventory; distinguish local readiness from account connection."""
from datetime import datetime
from pathlib import Path
import hashlib
import json
import subprocess
import studio

root = studio.ROOT


def file_evidence(relative):
    file = root/relative
    return {'path': str(file), 'exists': file.is_file(),
            'size': file.stat().st_size if file.is_file() else None,
            'sha256': hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() else None}


doctor = studio.load(root/'doctor.json')
quality = studio.load(root/'jobs/demo/social-studio-final.quality.json')
analysis = studio.load(root/'jobs/demo-analysis-final/analysis.json')
transcript = studio.load(root/'jobs/demo-analysis-final/transcript.json')
comparison = studio.load(root/'jobs/demo/master-comparison/comparison.json')
auth = studio.load(root/'agent-auth-status.json')
guide = studio.load(root/'guide-verification.json')
tests = {**studio.load(root/'test-results.json'),'log':str(root/'verification-tests.log')}
with (root/'postiz-auth-status.txt').open('w',encoding='utf-8') as f:
    p = subprocess.run([str(studio.PYTHON),str(root/'studio.py'),'postiz','auth:status'],
                       stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    postiz_status = p.stdout.decode('utf-8',errors='replace')
    f.write('\n'.join(line for line in postiz_status.splitlines() if 'Token:' not in line and 'Key:' not in line))
postiz_authenticated = ('Credentials are valid.' in postiz_status and p.returncode == 0)
packages = studio.load(root/'package-lock.json')['packages']
versions = {name:packages['node_modules/'+name]['version'] for name in
            ['hyperframes','remotion','@remotion/cli','@remotion/renderer','gsap','postiz','react','playwright']}
skills = {}
for target in ['.agents','.claude']:
    base = Path.home()/target/'skills'
    skills[target] = [{'name':p.name, 'exists':(p/'SKILL.md').is_file()}
                      for p in [base/'social',*sorted(base.glob('social-*'))]]
files = [file_evidence(p) for p in [
    'KULLANIM-KILAVUZU.html','KULLANIM-KILAVUZU.md','REPOSITORIES.md',
    'WORKFLOWS.md','jobs/demo/social-studio-final.mp4','jobs/demo/index.html',
    'jobs/remotion-smoke/proof.mp4','verification-tests.log','installed-requirements.txt',
    'bin/source.json','runtimes/node22/node.source.json','POSTIZ-OMER-NOTU.md',
    'jobs/omer-handoff-demo.zip','jobs/omer-handoff-demo/publication.json']]
result = {
    'checked_at':datetime.now(studio.IST).isoformat(),
    'local_tools_ready':doctor['core_ready'], 'versions':versions,
    'tests':tests,
    'accounts':{**auth,'postiz':{'authenticated':postiz_authenticated}},
    'skills':skills, 'guide':guide,
    'hyperframes_demo':{'video':studio.video_info(root/'jobs/demo/social-studio-final.mp4'),
                       'decode_ok':quality['decode_ok'], 'loudness':quality['loudness']},
    'analysis':{'manifest':analysis,'transcript_model':transcript['model'],
                'transcript_text':' '.join(s['text'] for s in transcript['segments']),
                'low_confidence_words':transcript.get('low_confidence_words',[])},
    'master_preserves_video':{'compared_frames':comparison['compared_frames'],
                             'mae_255':comparison['mean_mae_255'],
                             'dimensions_match':comparison['dimensions_match'],
                             'fps_match':comparison['fps_match'],
                             'duration_delta':comparison['duration_delta']},
    'remotion_smoke':studio.video_info(root/'jobs/remotion-smoke/proof.mp4'),
    'files':files,
    'scope_notes':[
        f'{tests["count"]} integration tests cover real-media transforms, portable handoff and local orchestration, not arbitrary reference fidelity.',
        'A real editable HyperFrames project was rendered; an independent React/Remotion fixture was also rendered.',
        'The full demo was analyzed using the default large-v3-turbo model.',
        'The image identity comparison proves mastering did not change video frames, not that every reference can be cloned.',
        'Claude subscription OAuth login is verified. No validator model-inference call was made.',
        'External posting is not claimed as tested; the existing Postiz server/API details are pending from its owner Ömer.',
        'ComfyUI and stable-audio-tools were researched but are not part of the installed core stack.',
        'The folder watcher is installed but not running as a background service.',
    ]}
result['local_verification_passed'] = bool(
    doctor['core_ready'] and tests['passed'] and tests['count'] >= 12
    and all(v['exists'] for v in files)
    and quality['decode_ok'] and float(quality['loudness']['input_tp']) <= -1.5
    and abs(float(quality['loudness']['input_i'])+16) <= 0.5
    and analysis['scene_count'] == 4 and transcript['model'] == 'large-v3-turbo'
    and comparison['compared_frames'] == 330 and comparison['mean_mae_255'] == 0
    and len(skills['.agents']) == 11 and len(skills['.claude']) == 11
    and all(x['exists'] for group in skills.values() for x in group)
    and not guide['errors'] and guide['copy_test']
    and versions['remotion'] == versions['@remotion/cli'] == versions['@remotion/renderer'])
studio.save(root/'verification.json',result)
print(json.dumps({'local_tools_ready':result['local_tools_ready'], 'accounts':result['accounts'],
                  'demo':result['hyperframes_demo'], 'preserved':result['master_preserves_video']},
                  ensure_ascii=False,indent=2))
