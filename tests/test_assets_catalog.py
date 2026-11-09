"""Validate assets/catalog.json: schema, mandatory licence fields, safe paths; hashes when files exist."""
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
CATALOG = ASSETS / 'catalog.json'

OPEN_LICENSES = {'CC0-1.0', 'CC-BY-3.0', 'CC-BY-4.0'}
KINDS = {'character', 'vehicle', 'hdri', 'prop', 'texture'}
ALLOWED_EXT = {'.glb', '.gltf', '.bin', '.png', '.jpg', '.jpeg', '.hdr', '.exr'}
REQUIRED = ('id', 'kind', 'title', 'file', 'url', 'source_page', 'author', 'license', 'attribution_required', 'sha256', 'bytes')


def load():
    return json.loads(CATALOG.read_text(encoding='utf-8'))


def validate(catalog):
    """Return a list of problems (empty = valid). Kept as a function so other tools can reuse it."""
    errs = []
    if catalog.get('schema') != 1:
        errs.append('schema must be 1')
    ids = set()
    for i, a in enumerate(catalog.get('assets', [])):
        tag = a.get('id', f'#{i}')
        for k in REQUIRED:
            if k not in a or a[k] in (None, ''):
                errs.append(f'{tag}: missing {k}')
        if tag in ids:
            errs.append(f'{tag}: duplicate id')
        ids.add(tag)
        if a.get('kind') not in KINDS:
            errs.append(f'{tag}: bad kind {a.get("kind")}')
        if a.get('license') not in OPEN_LICENSES:
            errs.append(f'{tag}: licence {a.get("license")} not in {sorted(OPEN_LICENSES)}')
        if str(a.get('license', '')).startswith('CC-BY'):
            if a.get('attribution_required') is not True or not a.get('attribution'):
                errs.append(f'{tag}: CC-BY needs attribution_required=true and an attribution line')
        f = str(a.get('file', ''))
        if not f.startswith('assets/') or '..' in Path(f).parts:
            errs.append(f'{tag}: file must be a repo-relative path under assets/: {f}')
        if Path(f).suffix.lower() not in ALLOWED_EXT:
            errs.append(f'{tag}: extension not allowed: {f}')
        if not str(a.get('url', '')).startswith('https://'):
            errs.append(f'{tag}: url must be https')
        if not re.fullmatch(r'[0-9a-f]{64}', str(a.get('sha256', ''))):
            errs.append(f'{tag}: sha256 must be 64 lowercase hex chars')
        if a.get('kind') in ('character', 'vehicle'):
            if a.get('forward') not in ('+z', '-z', '+x', '-x'):
                errs.append(f'{tag}: forward must be one of +z -z +x -x')
            t = a.get('target') or {}
            if not any(isinstance(t.get(k), (int, float)) and t[k] > 0 for k in ('height', 'length', 'width')):
                errs.append(f'{tag}: target needs a positive height/length/width (metres)')
            for k in ('tris', 'size_m', 'foot_height_m', 'crowd_lod'):
                if k not in a:
                    errs.append(f'{tag}: missing measured field {k} (run templates/three-crowd/probe)')
        if a.get('kind') == 'character' and 'animations' in a and not a['animations']:
            errs.append(f'{tag}: character without animation clips')
        if 'derived_from' in a and a['derived_from'] not in {x.get('id') for x in catalog['assets']}:
            errs.append(f'{tag}: derived_from points to unknown id')
    return errs


class AssetCatalogTests(unittest.TestCase):
    def test_catalog_is_valid(self):
        self.assertTrue(CATALOG.exists(), 'assets/catalog.json missing')
        self.assertEqual(validate(load()), [])

    def test_required_species_present(self):
        species = {a.get('species') for a in load()['assets']}
        for s in ('horse', 'human'):
            self.assertIn(s, species)
        self.assertTrue(species & {'cat', 'dog'}, 'need a cat or dog')
        self.assertTrue(species & {'bus', 'truck'}, 'need a bus or truck')

    def test_validator_rejects_bad_entries(self):
        good = load()['assets'][0]
        bad = dict(good, id='x', license='Proprietary')
        self.assertTrue(any('licence' in e for e in validate({'schema': 1, 'assets': [bad]})))
        nolic = {k: v for k, v in good.items() if k != 'license'}
        nolic['id'] = 'y'
        self.assertTrue(any('missing license' in e for e in validate({'schema': 1, 'assets': [nolic]})))
        ccby = dict(good, id='z', license='CC-BY-3.0', attribution_required=False)
        self.assertTrue(any('attribution' in e for e in validate({'schema': 1, 'assets': [ccby]})))
        esc = dict(good, id='w', file='assets/../secret.glb')
        self.assertTrue(any('under assets' in e for e in validate({'schema': 1, 'assets': [esc]})))

    def test_licenses_md_lists_every_downloaded_file(self):
        text = (ASSETS / 'LICENSES.md').read_text(encoding='utf-8')
        for a in load()['assets']:
            if 'derived_from' in a:
                continue
            self.assertIn(a['id'], text)
            self.assertIn(a['url'], text)

    def test_files_match_hash_when_present(self):
        checked = 0
        seen = set()
        for a in load()['assets']:
            p = ROOT / a['file']
            if not p.exists() or p in seen:
                continue  # binaries are optional (git-ignored); fetch_assets.py downloads them
            seen.add(p)
            with self.subTest(asset=a['id']):
                self.assertEqual(p.stat().st_size, a['bytes'])
                self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), a['sha256'])
                if p.suffix == '.glb':
                    self.assertEqual(p.read_bytes()[:4], b'glTF')
            checked += 1
        if not checked:
            self.skipTest('no asset binaries present (run assets/fetch_assets.py)')


if __name__ == '__main__':
    unittest.main()
