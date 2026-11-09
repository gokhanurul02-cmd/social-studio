"""Download / verify the binary assets listed in assets/catalog.json.

Binaries are not committed (see .gitignore); this script re-creates them from the
pinned URL + sha256 in the catalog. Only plain data files are accepted
(.glb .gltf .bin .png .jpg .hdr .exr); nothing is executed or unpacked.

usage:
  python assets/fetch_assets.py            # download missing / mismatching files
  python assets/fetch_assets.py --check    # verify only, exit 1 on problems
  python assets/fetch_assets.py --only horse_quaternius cat_quaternius
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import urllib.request
from pathlib import Path

ASSETS = Path(__file__).resolve().parent
REPO = ASSETS.parent
ALLOWED = {".glb", ".gltf", ".bin", ".png", ".jpg", ".jpeg", ".hdr", ".exr"}
UA = "social-studio-asset-fetch/1.0 (+local render pipeline)"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def target_path(entry: dict) -> Path:
    p = (REPO / entry["file"]).resolve()
    if ASSETS not in p.parents:
        raise ValueError(f"{entry['id']}: file must live under assets/: {entry['file']}")
    if p.suffix.lower() not in ALLOWED:
        raise ValueError(f"{entry['id']}: extension {p.suffix} not allowed")
    return p


def fetch(entry: dict) -> None:
    dest = target_path(entry)
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(entry["url"], headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r, tempfile.NamedTemporaryFile(dir=dest.parent, delete=False, suffix=".part") as tmp:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            tmp.write(chunk)
        tmp_path = Path(tmp.name)
    got = sha256(tmp_path)
    if got != entry["sha256"]:
        tmp_path.unlink(missing_ok=True)
        raise RuntimeError(f"{entry['id']}: sha256 mismatch (got {got}, want {entry['sha256']})")
    tmp_path.replace(dest)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="verify only, do not download")
    ap.add_argument("--only", nargs="*", help="asset ids to process")
    ap.add_argument("--catalog", default=str(ASSETS / "catalog.json"))
    args = ap.parse_args(argv)
    catalog = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    bad = 0
    for e in catalog["assets"]:
        if args.only and e["id"] not in args.only:
            continue
        dest = target_path(e)
        ok = dest.exists() and sha256(dest) == e["sha256"]
        if ok:
            print(f"ok       {e['id']:<24} {e['file']}")
            continue
        if args.check:
            print(f"MISSING  {e['id']:<24} {e['file']}" if not dest.exists() else f"BADHASH  {e['id']:<24} {e['file']}")
            bad += 1
            continue
        print(f"fetch    {e['id']:<24} {e['url']}")
        try:
            fetch(e)
            print(f"ok       {e['id']:<24} {dest.stat().st_size} bytes")
        except Exception as exc:  # report and continue with the rest
            print(f"FAILED   {e['id']}: {exc}", file=sys.stderr)
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
