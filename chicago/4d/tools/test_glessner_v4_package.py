#!/usr/bin/env python3
"""Exercise package integrity, a fresh checkout, and refusal of stale/new bakes."""
import argparse
import io
import json
from pathlib import Path
import tempfile
import zipfile

from recover_glessner_v4 import TARGETS, materialize, pack, sha256, verified_members, write_member

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--self-test', action='store_true', help='run the fixture assertions (also the default)')
parser.parse_args()


def refuses(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError("expected a refusal")


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory) / "checkout"; recovery = Path(directory) / "package"
    data = {TARGETS[0]: b"master-glb", TARGETS[1]: b"web-glb", TARGETS[2]: b"light-glb"}
    for name, content in data.items():
        write_member(root, name, content)
    pack(root, recovery)
    first = {p.name: p.read_bytes() for p in recovery.iterdir()}
    pack(root, recovery)
    assert first == {p.name: p.read_bytes() for p in recovery.iterdir()}, "pack must be deterministic"
    assert set(verified_members(recovery)) == set(TARGETS), "pack must include exactly three GLBs"

    # Model the original recovery archive containing older snapshots as well.
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zipped:
        for name, content in {**data, "assets/manifest.json": b"obsolete snapshot"}.items():
            zipped.writestr(name, content)
    archive = buffer.getvalue()
    manifest = {"files": {name: {"bytes": len(content), "sha256": sha256(content)}
                            for name, content in {**data, "assets/manifest.json": b"obsolete snapshot"}.items()},
                "archive_sha256": sha256(archive), "archive_bytes": len(archive),
                "parts": [{"name": "assets.zip.part00", "bytes": len(archive), "sha256": sha256(archive)}]}
    (recovery / "assets.zip.part00").write_bytes(archive)
    (recovery / "manifest.json").write_text(json.dumps(manifest))
    write_member(root, "assets/manifest.json", b"current manifest")
    for name in TARGETS:
        (root / name).unlink()
    refuses(lambda: materialize(root, recovery, check=True))
    assert materialize(root, recovery) == 3
    assert (root / "assets/manifest.json").read_bytes() == b"current manifest", "never restore snapshot manifests"
    assert materialize(root, recovery, check=True) == 0

    (root / TARGETS[0]).write_bytes(b"new bake")
    (root / TARGETS[1]).unlink()
    refuses(lambda: materialize(root, recovery))
    assert not (root / TARGETS[1]).exists(), "refuse before writing any output"
    assert (root / TARGETS[0]).read_bytes() == b"new bake", "never roll back a bake"
    (recovery / "assets.zip.part00").write_bytes(archive[:-1] + b"X")
    refuses(lambda: materialize(root, recovery))
print("PASS: deterministic three-file packing, selective restoration, and stale/corrupt refusal")

# The owner's chosen default uses canonical paths, with the same integrity rules.
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory) / "checkout"; recovery = Path(directory) / "package"
    write_member(root, "data/structures/glessner_house.json", b"{}")
    canonical = tuple(name.replace("versions/glessner_house/v4/", "") for name in TARGETS)
    for name in canonical:
        write_member(root, name, name.encode())
    pack(root, recovery)
    assert set(verified_members(recovery)) == set(canonical)
    for name in canonical:
        (root / name).unlink()
    assert materialize(root, recovery) == 3
    assert materialize(root, recovery, check=True) == 0
    (root / canonical[0]).write_bytes(b"new canonical bake")
    refuses(lambda: materialize(root, recovery))
print("PASS: promoted canonical paths restore exactly and still refuse a divergent bake")
