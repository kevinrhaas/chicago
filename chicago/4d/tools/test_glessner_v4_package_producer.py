#!/usr/bin/env python3
"""Exercise the real derivative shell/record/package lifecycle with a tiny tool stub.

Only gltf-transform is stubbed. The real version recorder and packer run against
isolated byte fixtures; no town assets or network/tool installation are touched.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from recover_glessner_v4 import ROOT, TARGETS, materialize, pack, sha256, verified_members, write_member

KEY = TARGETS[0].removeprefix("assets/gltf/")
OTHER = KEY.replace("/v4/", "/v3/")
STUB = '''#!/usr/bin/env python3
import hashlib,os,sys
from pathlib import Path
args=sys.argv[1:]; args=args[args.index("gltf-transform")+1:]
mode=os.environ.get("FIXTURE_TRANSFORM", "optimized")
if args[0]=="--version":
    print("" if mode=="unavailable" else "4.5.0"); raise SystemExit()
command,source,target=args[:3]
data=Path(source).read_bytes()
if command=="optimize": Path(target).write_bytes(data)
elif command=="meshopt":
    stamp=b"invalid-generator" if mode=="badstamp" else b"glTF-Transform v4.5.0"
    Path(target).write_bytes(stamp+b" "+hashlib.sha256(data).hexdigest().encode())
else: raise SystemExit(2)
'''


def fixture(directory):
    root = Path(directory)
    for name in ("tools/web_derivatives.sh", "tools/recover_glessner_v4.py",
                 "tools/structure_versions.py", "generators/common/versions.py",
                 "generators/common/phases.py"):
        target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    binary = root / "bin/npx"; binary.parent.mkdir()
    binary.write_text(STUB); binary.chmod(0o755)
    write_member(root, TARGETS[0], b"old master" * 200)
    write_member(root, TARGETS[1], b"old derivative")
    manifest = root / "assets/manifest.versions.json"
    manifest.write_text(json.dumps({"assets": {KEY: {}, OTHER: {}}}))
    recovery = root / "docs/RESEARCH/glessner-v4-recovery"
    pack(root, recovery)
    return root, recovery, manifest


def snapshot(path):
    return {p.name: p.read_bytes() for p in path.iterdir() if p.is_file()}


def run(root, *args, mode="optimized", success=True):
    environment = {**os.environ, "PATH": str(root / "bin") + os.pathsep + os.environ["PATH"],
                   "FIXTURE_TRANSFORM": mode}
    result = subprocess.run(["bash", "tools/web_derivatives.sh", *args], cwd=root,
                            env=environment, capture_output=True, text=True)
    assert (result.returncode == 0) == success, result.stdout + result.stderr
    return result.stdout


for mode in ("optimized", "unavailable"):
    with tempfile.TemporaryDirectory() as directory:
        root, recovery, manifest = fixture(directory)
        original = snapshot(recovery)
        new_master = ("new master " + mode).encode() * 200
        (root / TARGETS[0]).write_bytes(new_master)
        # The new master + missing derivative case must not try materialization.
        (root / TARGETS[1]).unlink()
        run(root, "--only", KEY, mode=mode)
        members = verified_members(recovery)
        assert members[TARGETS[0]] == new_master, "producer must preserve the new master"
        assert members[TARGETS[1]] == (root / TARGETS[1]).read_bytes()
        assert snapshot(recovery) != original, "canonical production must refresh archive"
        assert json.loads(manifest.read_text())["assets"][KEY]["web_master_sha256"] == sha256(new_master)
        assert materialize(root, recovery, check=True) == 0
        for name in TARGETS: (root / name).unlink()
        assert materialize(root, recovery) == 2
        for name in TARGETS: assert (root / name).read_bytes() == members[name]
        # A fresh exact-v4 request must restore its source, not silently skip it.
        for name in TARGETS: (root / name).unlink()
        output = run(root, "--only", KEY, mode=mode)
        assert "2 missing GLB(s) materialized" in output
        assert materialize(root, recovery, check=True) == 0

        # Existing stale web bytes also belong to the producer, not recovery.
        newer_master = b"second deliberate bake" * 200
        (root / TARGETS[0]).write_bytes(newer_master)
        run(root, "--only", KEY, mode=mode)
        assert verified_members(recovery)[TARGETS[0]] == newer_master
        assert materialize(root, recovery, check=True) == 0

        before = snapshot(recovery); recorded = manifest.read_bytes()
        (root / TARGETS[0]).write_bytes(b"unpacked measurement master" * 200)
        run(root, "--only", KEY, "--out", "measurement", mode=mode)
        assert (root / "measurement" / KEY).is_file()
        assert snapshot(recovery) == before and manifest.read_bytes() == recorded, "--out must not repack/record"
        for name in TARGETS: (root / name).unlink()
        write_member(root, "assets/gltf/" + OTHER, b"unrelated version" * 200)
        run(root, "--only", OTHER, mode=mode)
        assert snapshot(recovery) == before, "unrelated version must not repack"
        assert all(not (root / name).exists() for name in TARGETS), "unrelated request must not materialize"

with tempfile.TemporaryDirectory() as directory:
    root, recovery, manifest = fixture(directory)
    before = snapshot(recovery)
    run(root, "--only", KEY, mode="badstamp", success=False)
    assert snapshot(recovery) == before, "hard producer failure must not repack"
    manifest.write_text(json.dumps({"assets": {}}))
    run(root, "--only", KEY, success=False)
    assert snapshot(recovery) == before, "record-web failure must not repack"
print("PASS: optimized/no-tool producer refresh, fresh restoration, --out/id guards, failure ordering")
