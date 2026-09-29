#!/usr/bin/env python3
"""Lossless packaging for the two Glessner v4 GLBs larger than the upload limit.

Publish/check materialize only the two explicit outputs below. All existing bytes
must match the verified archive: the canonical v4 derivative producer repacks its
new pair, never rolls back a bake. --pack also supports deliberate manual recovery.
Other checkpoint members are available only to manual --restore.
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
TARGETS = tuple(f"assets/{kind}/versions/glessner_house/v4/glessner_house__as_built_1887.glb"
                for kind in ("gltf", "web"))
PART_BYTES = 6 * 1024 * 1024


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verified_members(recovery=RECOVERY):
    manifest = json.loads((recovery / "manifest.json").read_text())
    chunks = []
    for part in manifest["parts"]:
        path = recovery / part["name"]
        require(path.parent == recovery and path.name.startswith("assets.zip.part"), "invalid part path")
        data = path.read_bytes()
        require(len(data) == part["bytes"] and sha256(data) == part["sha256"], f"corrupt part: {path}")
        chunks.append(data)
    archive = b"".join(chunks)
    require(len(archive) == manifest["archive_bytes"] and sha256(archive) == manifest["archive_sha256"],
            "archive checksum mismatch")
    members = {}
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        names = zipped.namelist()
        require(len(names) == len(set(names)) and set(names) == set(manifest["files"]), "unexpected archive member")
        for name, expected in manifest["files"].items():
            require(not Path(name).is_absolute() and ".." not in Path(name).parts and
                    name.startswith(("assets/", "data/sidecars/")), "not a generated asset")
            data = zipped.read(name)
            require(len(data) == expected["bytes"] and sha256(data) == expected["sha256"], f"corrupt member: {name}")
            members[name] = data
    return members


def write_member(root, name, data):
    target = root / name
    require(target.resolve().is_relative_to(root.resolve()), "path escapes checkout")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".recovery-tmp")
    temporary.write_bytes(data)
    temporary.replace(target)


def materialize(root=ROOT, recovery=RECOVERY, check=False):
    members = verified_members(recovery)
    missing = []
    # Check BOTH existing files before writing either missing file. Never mask a
    # new bake by restoring the older packed result over it.
    for name in TARGETS:
        require(name in members, f"archive lacks {name}")
        target = root / name
        require(target.resolve().is_relative_to(root.resolve()), "path escapes checkout")
        if not target.exists():
            missing.append(name)
        else:
            require(target.is_file() and target.read_bytes() == members[name],
                    f"{name} differs from the packed asset. After the normal bake/derivative gates, "
                    "run python3 tools/recover_glessner_v4.py --pack and commit the archive parts and manifest.")
    require(not check or not missing, "packaged GLBs absent; run python3 tools/recover_glessner_v4.py --materialize")
    for name in missing:
        write_member(root, name, members[name])
    return len(missing)


def pack(root=ROOT, recovery=RECOVERY):
    members = {name: (root / name).read_bytes() for name in TARGETS}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipped:
        for name, data in members.items():
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zipped.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    archive = buffer.getvalue()
    manifest = {"purpose": "Exact two-file Glessner v4 GLB package; materialized before ordinary validation/publish.",
                "files": {name: {"bytes": len(data), "sha256": sha256(data)} for name, data in members.items()},
                "parts": [], "archive_sha256": sha256(archive), "archive_bytes": len(archive)}
    recovery.mkdir(parents=True, exist_ok=True)
    for i, offset in enumerate(range(0, len(archive), PART_BYTES)):
        name = f"assets.zip.part{i:02d}"; data = archive[offset:offset + PART_BYTES]
        write_member(recovery, name, data)
        manifest["parts"].append({"name": name, "bytes": len(data), "sha256": sha256(data)})
    write_member(recovery, "manifest.json", (json.dumps(manifest, indent=2) + "\n").encode())
    names = {p["name"] for p in manifest["parts"]}
    for old in recovery.glob("assets.zip.part[0-9][0-9]"):
        if old.name not in names:
            old.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--materialize", action="store_true", help="verify both outputs and restore only missing v4 GLBs")
    mode.add_argument("--check", action="store_true", help="refuse missing/divergent v4 GLBs or a corrupt archive")
    mode.add_argument("--pack", action="store_true", help="repack exactly the two current v4 GLBs after a bake")
    mode.add_argument("--restore", action="store_true", help="manual snapshot recovery: overwrite ALL archived generated files")
    args = parser.parse_args()
    try:
        if args.pack:
            pack(); print("Packed two exact v4 GLBs; commit archive parts and manifest with the bake.")
        elif args.materialize or args.check:
            count = materialize(check=args.check)
            print(f"Glessner v4 package verified; {count} missing GLB(s) materialized.")
        else:
            members = verified_members()
            if args.restore:
                for name, data in members.items():
                    write_member(ROOT, name, data)
            print(f"{'Restored' if args.restore else 'Verified archive:'} {len(members)} exact generated files.")
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        parser.exit(1, f"Glessner v4 package: {error}\n")


if __name__ == "__main__":
    main()
