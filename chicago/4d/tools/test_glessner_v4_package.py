#!/usr/bin/env python3
"""Exercise package integrity, a fresh checkout, and refusal of stale/new bakes."""
import argparse
import io
import json
from pathlib import Path
import tempfile
import zipfile

from recover_glessner_v4 import TARGETS, drift, materialize, pack, reuse_derivatives, sha256, verified_members, write_member

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

# T-3004: a clone holding outputs materialized before the archive was repacked must read
# as that clone's drift, by hash alone, never as a stale committed derivative.
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory) / "checkout"; recovery = Path(directory) / "package"
    write_member(root, "data/structures/glessner_house.json", b"{}")
    canonical = tuple(name.replace("versions/glessner_house/v4/", "") for name in TARGETS)
    for name in canonical:
        write_member(root, name, b"old " + name.encode())
    pack(root, recovery)
    old = {name: (root / name).read_bytes() for name in canonical}
    assert drift(root, recovery) == {}, "a tree that matches its archive has no drift"
    for name in canonical:
        write_member(root, name, b"repacked " + name.encode())
    pack(root, recovery)                       # the archive moves on (a merged rebake)...
    for name, content in old.items():
        write_member(root, name, content)      # ...and this clone still holds the old bytes
    assert drift(root, recovery) == {name: "divergent" for name in canonical}, drift(root, recovery)
    (root / canonical[2]).unlink()
    assert drift(root, recovery)[canonical[2]] == "missing", "an absent output is named missing"
    for name in canonical:
        (root / name).unlink(missing_ok=True)
    assert materialize(root, recovery) == 3 and drift(root, recovery) == {}, "--materialize heals it"
    assert drift(root, Path(directory) / "no-package") == {}, "an unreadable manifest is --check's to report"
print("PASS: drift names a stale or missing materialized output by hash, and --materialize clears it")

# T-3503: a whole-town bake builds the master and finds no derivative (they are
# untracked). Restore the packaged pair only when the built master IS the packaged one,
# only into absent files, and say "derive it" for everything else without writing.
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory) / "checkout"; recovery = Path(directory) / "package"
    write_member(root, "data/structures/glessner_house.json", b"{}")
    master, web, light = (name.replace("versions/glessner_house/v4/", "") for name in TARGETS)
    for name in (master, web, light):
        write_member(root, name, b"packed " + name.encode())
    pack(root, recovery)
    packed = {name: (root / name).read_bytes() for name in (master, web, light)}

    (root / web).unlink(); (root / light).unlink()
    count, why = reuse_derivatives(root, recovery)
    assert count == 2, why
    assert all((root / n).read_bytes() == packed[n] for n in (web, light)), "restore the packed bytes"
    assert drift(root, recovery) == {}, "a reused tree matches its package"

    (root / web).unlink(); (root / light).unlink()
    (root / master).write_bytes(b"a moved master")
    assert reuse_derivatives(root, recovery)[0] == 0, "a moved master is derived, not reused"
    assert not (root / web).exists() and not (root / light).exists(), "nothing written for a moved master"
    assert (root / master).read_bytes() == b"a moved master", "never roll back a bake"

    (root / master).unlink()
    assert reuse_derivatives(root, recovery)[0] == 0 and not (root / web).exists(), \
        "an absent master is the bake's to build, not this to restore"

    write_member(root, master, packed[master])
    write_member(root, web, b"a stale local derivative")
    assert reuse_derivatives(root, recovery)[0] == 0, "a present derivative is left alone"
    assert (root / web).read_bytes() == b"a stale local derivative" and not (root / light).exists(), \
        "never write over a present derivative, nor beside one"

    (root / web).unlink()
    assert reuse_derivatives(root, Path(directory) / "no-package")[0] == 0, "no package: derive it"
    (recovery / "assets.zip.part00").write_bytes(b"corrupt")
    refuses(lambda: reuse_derivatives(root, recovery))
    assert not (root / web).exists(), "a corrupt package restores nothing"
print("PASS: a whole-town bake reuses the packaged derivatives only for the packaged master, only into absent files")
