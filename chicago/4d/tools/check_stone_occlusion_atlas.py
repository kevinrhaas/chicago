#!/usr/bin/env python3
"""Every Glessner tier's stone occlusion was baked from a committed atlas (T-2431).

The granite's stone-scale occlusion (T-2400 master, T-2401 light) is a Cycles AO bake,
and Cycles AO is not bit-reproducible across CPUs: a bake in a cloud container and one
on an Actions runner differed in 2,471 texels and moved the master's bytes, which reds
the bake check's K01 hashes (T-2427). So the baker
(generators/archetypes/masonry_house_v4_occlusion.py) keeps its quantised atlas in
assets/bakes/stone-occlusion/, keyed by a hash of everything the bake reads, and a bake
whose key matches takes that atlas instead of running Cycles. That holds only while the
atlas the models were baked with is the atlas committed beside them. This checks it,
with no Blender and no numpy: each tier named by the K01 baseline carries its baker's
record in node extras (`stone_occlusion.atlas_key`), and the committed atlas for that
image and size must hold the same key. A model rebaked without its atlas, or an atlas
no model was baked from, is refused.

    python3 tools/check_stone_occlusion_atlas.py [--check]
    python3 tools/check_stone_occlusion_atlas.py --self-test
"""
from __future__ import annotations

import ast
import json
import struct
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "data" / "components" / "prairie_1904" / "glessner_baseline.json"
ATLAS_DIR = ROOT / "assets" / "bakes" / "stone-occlusion"


def glb_records(path):
    """Every `stone_occlusion` record in a GLB's node and asset extras."""
    with open(path, "rb") as fh:
        magic, _version, _length = struct.unpack("<4sII", fh.read(12))
        if magic != b"glTF":
            raise ValueError(f"{path} is not a GLB")
        size, kind = struct.unpack("<I4s", fh.read(8))
        if kind != b"JSON":
            raise ValueError(f"{path}: first chunk is not JSON")
        doc = json.loads(fh.read(size))
    holders = [*doc.get("nodes", []), *doc.get("meshes", []), doc.get("asset", {}), doc]
    return [h["extras"]["stone_occlusion"] for h in holders
            if isinstance(h.get("extras"), dict) and "stone_occlusion" in h["extras"]]


def atlas_key(path):
    """The `key` string an atlas .npz holds, read from its .npy member by hand."""
    with zipfile.ZipFile(path) as zf:
        raw = zf.read("key.npy")
    if raw[:6] != b"\x93NUMPY":
        raise ValueError(f"{path}: key.npy is not an npy array")
    if raw[6] == 1:
        hlen, start = struct.unpack("<H", raw[8:10])[0], 10
    else:
        hlen, start = struct.unpack("<I", raw[8:12])[0], 12
    header = ast.literal_eval(raw[start:start + hlen].decode("latin1"))
    if header.get("shape") != () or not str(header.get("descr", "")).startswith(("<U", "|U")):
        raise ValueError(f"{path}: key.npy is not one string")
    return raw[start + hlen:].decode("utf-32-le").rstrip("\x00")


def check(baseline=BASELINE, atlas_dir=ATLAS_DIR, root=ROOT):
    errors, used, lines = [], set(), []
    tiers = json.loads(Path(baseline).read_text())["tiers"]
    for tier, spec in sorted(tiers.items()):
        glb = Path(root) / spec["path"]
        if not glb.is_file():
            errors.append(f"{tier}: {spec['path']} is not on disk (materialize the v4 package)")
            continue
        records = glb_records(glb)
        if not records:
            errors.append(f"{tier}: {spec['path']} carries no stone_occlusion record")
            continue
        for rec in records:
            name = f"{rec.get('image')}_{rec.get('size')}.npz"
            if not rec.get("atlas_key"):
                errors.append(f"{tier}: baked before T-2431 — its record names no atlas_key, "
                              f"so a bake elsewhere would run Cycles afresh")
                continue
            atlas = Path(atlas_dir) / name
            if not atlas.is_file():
                errors.append(f"{tier}: baked from atlas {rec['atlas_key']} but {name} is not "
                              f"committed — commit the atlas the bake wrote")
                continue
            used.add(name)
            held = atlas_key(atlas)
            if held[:len(rec["atlas_key"])] != rec["atlas_key"]:
                errors.append(f"{tier}: baked from atlas {rec['atlas_key']} but {name} holds "
                              f"{held[:16]} — commit the atlas the bake wrote with the model")
                continue
            lines.append(f"{tier} {rec['atlas_key']} = {name}")
    for orphan in sorted(p.name for p in Path(atlas_dir).glob("*.npz") if p.name not in used):
        errors.append(f"{orphan}: no tier was baked from it — a stale atlas; remove it or rebake")
    return errors, lines


def self_test():
    failures = []

    def expect(label, ok):
        print(f"  {'ok  ' if ok else 'FAIL'} {label}")
        if not ok:
            failures.append(label)

    def npy_str(s):
        width = max(len(s), 1)
        header = "{'descr': '<U%d', 'fortran_order': False, 'shape': (), }" % width
        header += " " * (63 - (10 + len(header)) % 64) + "\n"
        return (b"\x93NUMPY\x01\x00" + struct.pack("<H", len(header)) + header.encode("latin1")
                + s.ljust(width, "\x00").encode("utf-32-le"))

    def glb(path, extras):
        doc = json.dumps({"asset": {"version": "2.0"},
                          "nodes": [{"name": "n", "extras": extras}]}).encode()
        doc += b" " * (-len(doc) % 4)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(struct.pack("<4sII", b"glTF", 2, 20 + len(doc))
                         + struct.pack("<I4s", len(doc), b"JSON") + doc)

    def atlas(directory, name, key):
        directory.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(directory / name, "w") as zf:
            zf.writestr("key.npy", npy_str(key))

    key = "ab" * 32
    rec = {"image": "granite_stone_occlusion", "size": 64, "atlas_key": key[:16]}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        base = root / "baseline.json"
        base.write_text(json.dumps({"tiers": {"full": {"path": "m.glb"}}}))
        bakes = root / "bakes"

        def run():
            return check(base, bakes, root)[0]

        glb(root / "m.glb", {"stone_occlusion": rec})
        atlas(bakes, "granite_stone_occlusion_64.npz", key)
        expect("a model and the atlas it was baked from pass", run() == [])
        atlas(bakes, "granite_stone_occlusion_64.npz", "cd" * 32)
        expect("an atlas holding another key is refused", any("holds cdcd" in e for e in run()))
        (bakes / "granite_stone_occlusion_64.npz").unlink()
        expect("a model whose atlas is not committed is refused",
               any("not committed" in e for e in run()))
        atlas(bakes, "granite_stone_occlusion_64.npz", key)
        atlas(bakes, "granite_stone_occlusion_32.npz", key)
        expect("an atlas no tier was baked from is refused", any("stale atlas" in e for e in run()))
        (bakes / "granite_stone_occlusion_32.npz").unlink()
        glb(root / "m.glb", {"stone_occlusion": {k: v for k, v in rec.items() if k != "atlas_key"}})
        expect("a model baked before the atlas was kept is refused",
               any("no atlas_key" in e for e in run()))
        glb(root / "m.glb", {})
        expect("a tier with no occlusion record is refused", any("no stone_occlusion" in e for e in run()))
    if failures:
        print(f"check_stone_occlusion_atlas self-test: {len(failures)} assertion(s) failed")
        return 1
    print("check_stone_occlusion_atlas self-test: every assertion fires")
    return 0


def main(argv):
    if "--self-test" in argv:
        return self_test()
    errors, lines = check()
    for e in errors:
        print(f"  ✗ {e}")
    if errors:
        print(f"stone occlusion atlas: {len(errors)} problem(s) (T-2431)")
        return 1
    print("stone occlusion atlas: every tier was baked from its committed atlas — "
          + "; ".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
