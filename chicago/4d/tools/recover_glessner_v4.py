#!/usr/bin/env python3
"""Verify or restore the exact Glessner v4 checkpoint assets.

The available GitHub connector limits request bodies to 16 MiB. This recovery
archive preserves the larger generated files until authenticated git can push
them normally. It is not an alternate asset format or a publishing step.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RECOVERY = ROOT / "docs/RESEARCH/glessner-v4-recovery"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore", action="store_true",
                        help="restore the verified generated files into this checkout")
    args = parser.parse_args()
    manifest = json.loads((RECOVERY / "manifest.json").read_text())
    chunks = []
    for part in manifest["parts"]:
        path = RECOVERY / part["name"]
        assert path.parent == RECOVERY, "invalid part path"
        data = path.read_bytes()
        assert len(data) == part["bytes"] and sha256(data) == part["sha256"], path
        chunks.append(data)
    archive = b"".join(chunks)
    assert sha256(archive) == manifest["archive_sha256"], "archive checksum mismatch"
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        assert set(zipped.namelist()) == set(manifest["files"]), "unexpected archive member"
        # Verify every member before writing any file.
        members = {}
        for name, expected in manifest["files"].items():
            target = (ROOT / name).resolve()
            assert target.is_relative_to(ROOT), "path escapes checkout"
            assert name.startswith(("assets/", "data/sidecars/")), "not a generated asset"
            data = zipped.read(name)
            assert len(data) == expected["bytes"] and sha256(data) == expected["sha256"], name
            members[name] = data
        if args.restore:
            for name, data in members.items():
                target = ROOT / name
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_name(target.name + ".recovery-tmp")
                temporary.write_bytes(data)
                temporary.replace(target)
            print(f"Restored {len(members)} exact generated files. Run the normal preflight before a PR.")
        else:
            mismatches = [name for name, data in members.items()
                          if not (ROOT / name).is_file() or (ROOT / name).read_bytes() != data]
            print(f"Verified archive: {len(members)} files; {len(mismatches)} differ or are absent locally.")
            if mismatches:
                print("Use --restore to recover the recorded generated files.")


if __name__ == "__main__":
    main()
