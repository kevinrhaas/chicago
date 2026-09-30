#!/usr/bin/env python3
"""Exercise the real derivative shell/record/package lifecycle with a tiny tool stub.

Only gltf-transform and the geometry-building subcommand are stubbed. The real version recorder and packer run against
isolated byte fixtures; no town assets or network/tool installation are touched.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from recover_glessner_v4 import ROOT, TARGETS, materialize, pack, sha256, verified_members, write_member

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--self-test', action='store_true', help='run the producer fixtures (also the default)')
parser.parse_args()

KEY = TARGETS[0].removeprefix("assets/gltf/")
OTHER = KEY.replace("/v4/", "/v3/")
STUB = '''#!/usr/bin/env python3
import hashlib,json,os,sys,struct
from pathlib import Path
args=sys.argv[1:]; args=args[args.index("gltf-transform")+1:]
mode=os.environ.get("FIXTURE_TRANSFORM", "optimized")
if args[0]=="--version":
    print("" if mode=="unavailable" else "4.5.0"); raise SystemExit()
command,source,target=args[:3]
data=Path(source).read_bytes()
if command=="optimize": Path(target).write_bytes(data)
elif command=="meshopt":
    with Path("precision-calls.jsonl").open("a") as log:
        log.write(json.dumps({"target":target,"position_bits":int(args[args.index("--quantize-position")+1])})+"\\n")
    stamp=b"invalid-generator" if mode=="badstamp" else b"glTF-Transform v4.5.0"
    if data.startswith(b"glTF"):
        doc=json.loads(data[20:20+struct.unpack_from("<I",data,12)[0]])
        doc["asset"]["generator"]=stamp.decode()
        payload=json.dumps(doc).encode();payload+=b" "*((-len(payload))%4)
        Path(target).write_bytes(struct.pack("<5I",0x46546c67,2,20+len(payload),len(payload),0x4e4f534a)+payload)
    else: Path(target).write_bytes(stamp+b" "+hashlib.sha256(data).hexdigest().encode())
else: raise SystemExit(2)
'''


def fixture(directory):
    root = Path(directory)
    for name in ("tools/web_derivatives.sh", "tools/recover_glessner_v4.py",
                 "tools/structure_versions.py", "generators/common/versions.py",
                 "generators/common/phases.py"):
        target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    (root / "tools/_glessner_lod.py").write_text("# isolated geometry recipe fixture\n")
    binary = root / "bin/npx"; binary.parent.mkdir()
    binary.write_text(STUB); binary.chmod(0o755)
    write_member(root, TARGETS[0], b"old master" * 200)
    write_member(root, TARGETS[1], b"old derivative")
    write_member(root, TARGETS[2], b"old light derivative")
    # Keep the real recorder/packer. The costly geometry subcommand alone is a
    # deterministic fixture, so lifecycle failures do not need a full house bake.
    wrapper = root / "bin/python3"
    wrapper.write_text("#!" + sys.executable + "\n" + '''
import os,sys,json,struct
from pathlib import Path
args=sys.argv[1:]
if len(args)>1 and args[0]=="tools/structure_versions.py" and args[1]=="build-light":
    mode=os.environ.get("FIXTURE_TRANSFORM")
    if mode=="lightfail": raise SystemExit(1)
    sys.path.insert(0,str(Path("generators").resolve()))
    from common import versions as V
    receipt={"master_sha256":V.sha256_file(Path("assets/gltf")/args[2]),
             "recipe_sha256":V.lod_recipe_sha(Path.cwd())}
    if mode=="stalereceipt": receipt["master_sha256"]="0"*64
    doc={"asset":{"version":"2.0"},"extras":{"glessner_light":receipt},
         "accessors":[{"count":600003 if mode=="overbudget" else 300}],
         "meshes":[{"primitives":[{"indices":0}]}]}
    payload=json.dumps(doc).encode();payload+=b" "*((-len(payload))%4)
    Path(args[3]).write_bytes(struct.pack("<5I",0x46546c67,2,20+len(payload),len(payload),0x4e4f534a)+payload)
    raise SystemExit()
os.execv(sys.executable,[sys.executable,*args])
''')
    wrapper.chmod(0o755)
    manifest = root / "assets/manifest.versions.json"
    manifest.write_text(json.dumps({"assets": {KEY: {}, OTHER: {}}}))
    recovery = root / "docs/RESEARCH/glessner-v4-recovery"
    pack(root, recovery)
    return root, recovery, manifest


def snapshot(path):
    return {p.name: p.read_bytes() for p in path.iterdir() if p.is_file()}


def run(root, *args, mode="optimized", success=True, asset_bits=14):
    environment = {**os.environ, "PATH": str(root / "bin") + os.pathsep + os.environ["PATH"],
                   "FIXTURE_TRANSFORM": mode, "ASSET_QUANT_BITS": str(asset_bits), "EPOCH_QUANT_BITS": "16"}
    result = subprocess.run(["bash", "tools/web_derivatives.sh", *args], cwd=root,
                            env=environment, capture_output=True, text=True)
    assert (result.returncode == 0) == success, result.stdout + result.stderr
    return result.stdout


for mode in ("optimized",):
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
        assert members[TARGETS[2]] == (root / TARGETS[2]).read_bytes()
        assert snapshot(recovery) != original, "canonical production must refresh archive"
        entry = json.loads(manifest.read_text())["assets"][KEY]
        assert entry["web_master_sha256"] == sha256(new_master)
        light = entry["web_lods"]["light"]
        assert light["master_sha256"] == sha256(new_master)
        assert light["output_sha256"] == sha256((root / TARGETS[2]).read_bytes())
        assert len(light["recipe_sha256"]) == 64
        assert materialize(root, recovery, check=True) == 0
        for name in TARGETS: (root / name).unlink()
        assert materialize(root, recovery) == 3
        for name in TARGETS: assert (root / name).read_bytes() == members[name]
        # A fresh exact-v4 request must restore its source, not silently skip it.
        for name in TARGETS: (root / name).unlink()
        output = run(root, "--only", KEY, mode=mode)
        assert "3 missing GLB(s) materialized" in output
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
        assert (root / "measurement" / KEY.replace(".glb", ".light.glb")).is_file()
        assert snapshot(recovery) == before and manifest.read_bytes() == recorded, "--out must not repack/record"
        for name in TARGETS: (root / name).unlink()
        write_member(root, "assets/gltf/" + OTHER, b"unrelated version" * 200)
        run(root, "--only", OTHER, mode=mode)
        assert snapshot(recovery) == before, "unrelated version must not repack"
        assert all(not (root / name).exists() for name in TARGETS), "unrelated request must not materialize"

with tempfile.TemporaryDirectory() as directory:
    root, recovery, manifest = fixture(directory)
    before = snapshot(recovery)
    recorded = manifest.read_bytes()
    for mode in ("badstamp", "lightfail", "unavailable", "stalereceipt", "overbudget"):
        run(root, "--only", KEY, mode=mode, success=False)
        assert snapshot(recovery) == before, "hard producer failure must not repack"
        assert manifest.read_bytes() == recorded, "failed light/full production must not stamp freshness"
    manifest.write_text(json.dumps({"assets": {}}))
    run(root, "--only", KEY, success=False)
    assert snapshot(recovery) == before, "record-web failure must not repack"

# A precision fix for the new opt-in mesh must never change the town's transform
# or nearby version names. Exercise the actual dispatch, not a duplicated selector.
with tempfile.TemporaryDirectory() as directory:
    root, recovery, manifest = fixture(directory)
    controls = [(KEY,16), (OTHER,14), (KEY.replace('/v4/','/v40/'),14),
                ('ordinary_house.glb',14), ('terrain__fixture.glb',16), ('water__fixture.glb',16)]
    for rel, expected in controls:
        write_member(root, 'assets/gltf/'+rel, b'precision fixture'*200)
        run(root, '--only', rel, '--out', 'measurement')
        calls = [json.loads(line) for line in (root/'precision-calls.jsonl').read_text().splitlines()]
        assert calls[-1]['position_bits'] == expected, (rel, calls[-1])
    # The existing diagnostic override still applies elsewhere; v4 retains its
    # required precision even when a lower global setting is being measured.
    for rel, expected in [(KEY,16), (OTHER,12)]:
        run(root, '--only', rel, '--out', 'measurement', asset_bits=12)
        calls = [json.loads(line) for line in (root/'precision-calls.jsonl').read_text().splitlines()]
        assert calls[-1]['position_bits'] == expected, (rel, calls[-1])
print("PASS: full/light producer/package lifecycle and exact-v4 precision; other paths retain prior bit depths")

# Promotion changes ownership and paths, not the producer's safety obligations.
with tempfile.TemporaryDirectory() as directory:
    root, recovery, _ = fixture(directory)
    canonical = tuple(name.replace("versions/glessner_house/v4/", "") for name in TARGETS)
    for old, new in zip(TARGETS, canonical):
        (root / old).replace(root / new)
    write_member(root, "data/structures/glessner_house.json", b"{}")
    key = KEY.replace("versions/glessner_house/v4/", "")
    manifest = root / "assets/manifest.json"
    manifest.write_text(json.dumps({"assets": {key: {}}}))
    pack(root, recovery)
    run(root, "--only", key)
    assert set(verified_members(recovery)) == set(canonical)
    entry = json.loads(manifest.read_text())["assets"][key]
    assert entry["web_lods"]["light"]["asset"] == key.replace(".glb", ".light.glb")
    calls = [json.loads(line) for line in (root / "precision-calls.jsonl").read_text().splitlines()]
    assert calls[-1]["position_bits"] == 16
    assert materialize(root, recovery, check=True) == 0
    before, recorded = snapshot(recovery), manifest.read_bytes()
    run(root, "--only", key, mode="lightfail", success=False)
    assert snapshot(recovery) == before and manifest.read_bytes() == recorded
    for name in canonical:
        (root / name).unlink()
    run(root, "--only", key)
    assert materialize(root, recovery, check=True) == 0
print("PASS: canonical producer preserves precision, receipts, recovery and failure atomicity")
