#!/usr/bin/env python3
"""restamp_stale.py — re-emit every mesh `validate.py --stale` calls stale, when only
its input hash moved.

    python3 tools/restamp_stale.py            re-stamp, then re-check (exit 1 if any stay stale)
    python3 tools/restamp_stale.py --check    list what is stale, write nothing (exit 1 if any)
    python3 tools/restamp_stale.py --self-test

WHY (2026-11-27, the batch merges). Two pull requests that each change shared archetype
code (archetypes/k01_*.py, a K12 recipe) merge with NO conflict in manifest.json and still
leave dozens of meshes stale: each side stamped its assets from its own tree, and the
merged tree hashes differently. `merge_asset_registry.py` re-emits only rows that
CONFLICTED, so these were re-stamped by hand, one `kNN_emit.py --only` per archetype,
on every lap and batch (memory: chicago-lap-k01-restamp, the #2399 batch). This is that
hand step: read the stale list, look each asset up in the manifest it is recorded in,
and run the pure-Python emitter its entry names with `--only` (one call per emitter).

THE SAFETY LINE is merge_asset_registry's: only a pure-Python emitter is run (its
PURE_EMITTERS list, plus the K01 versions emitter), and every GLB it rewrites must come
out BYTE-IDENTICAL. A re-stamp moves `inputs_sha256` and nothing else. If a mesh's bytes
move, the merged inputs really do build a different building; that wants its web
derivatives re-made and a look, so this restores the old GLB bytes and fails instead.
A stale asset no pure emitter owns (a Blender bake, the terrain) also fails: it cannot
be re-stamped here.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # chicago/4d
sys.path.insert(0, str(ROOT / "tools"))

VERSIONS_EMITTER = "generators/k01_versions_emit.py"

STALE_MESH = re.compile(r"FAIL\s+stale: (\S+\.glb) is STALE")
STALE_VERSION = re.compile(r"FAIL\s+version mesh (\S+\.glb): is STALE")


def pure_emitters() -> tuple[str, ...]:
    from merge_asset_registry import PURE_EMITTERS  # noqa: PLC0415 — one list, not two
    return tuple(PURE_EMITTERS) + (VERSIONS_EMITTER,)


def stale_names(log: str) -> tuple[list[str], list[str]]:
    """(canonical meshes, version meshes) a `validate.py --stale` log calls STALE."""
    return (sorted(set(STALE_MESH.findall(log))), sorted(set(STALE_VERSION.findall(log))))


def run_stale_check() -> str:
    r = subprocess.run([sys.executable, "tools/validate.py", "--stale"], cwd=ROOT,
                       capture_output=True, text=True)
    return r.stdout + r.stderr


def plan(meshes, versions, manifest, vmanifest, pure):
    """{emitter: sorted structure ids}, plus the stale names nothing here can re-stamp."""
    jobs, orphans = {}, []
    for names, table in ((meshes, manifest), (versions, vmanifest)):
        for name in names:
            e = table.get(name) or {}
            gen, sid = e.get("generator"), e.get("structure_id")
            if gen in pure and sid:
                jobs.setdefault(gen, set()).add(sid)
            else:
                orphans.append(f"{name} ({gen or 'no pure emitter recorded'})")
    return {g: sorted(ids) for g, ids in jobs.items()}, orphans


def load(path: Path) -> dict:
    return json.loads(path.read_text()).get("assets", {}) if path.exists() else {}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()

    meshes, versions = stale_names(run_stale_check())
    total = len(meshes) + len(versions)
    if not total:
        print("restamp_stale: no stale mesh")
        return 0
    manifest = load(ROOT / "assets" / "manifest.json")
    vmanifest = load(ROOT / "assets" / "manifest.versions.json")
    jobs, orphans = plan(meshes, versions, manifest, vmanifest, pure_emitters())
    print(f"restamp_stale: {total} stale mesh(es): "
          + ", ".join(f"{Path(g).name} x{len(ids)}" for g, ids in jobs.items())
          + (f"; {len(orphans)} with no pure emitter" if orphans else ""))
    for o in orphans:
        print(f"  cannot re-stamp here: {o}")
    if a.check:
        return 1

    gltf = ROOT / "assets" / "gltf"
    before = {p: p.read_bytes() for p in gltf.rglob("*.glb")}
    for gen, ids in jobs.items():
        r = subprocess.run([sys.executable, gen, "--only", ",".join(ids)], cwd=ROOT,
                           capture_output=True, text=True)
        if r.returncode:
            print(f"restamp_stale: {gen} --only … exited {r.returncode}:")
            print("  " + "\n  ".join((r.stdout + r.stderr).strip().splitlines()[-6:]))
            return 1
    moved = [p for p, b in before.items() if p.exists() and p.read_bytes() != b]
    if moved:
        for p in moved:
            p.write_bytes(before[p])
        print(f"restamp_stale: {len(moved)} GLB(s) changed BYTES, not just their input hash — "
              f"restored, and refusing: the merged inputs build a different mesh, which wants a "
              f"look and its web derivatives, not a re-stamp. First: {moved[0].relative_to(ROOT)}")
        return 1

    left = sum(map(len, stale_names(run_stale_check())))
    print(f"restamp_stale: re-stamped {total - left} of {total}; every GLB byte-identical"
          + (f"; {left} STILL stale" if left else ""))
    return 1 if (left or orphans) else 0


def self_test() -> int:
    log = ("  FAIL  stale: a__p.glb is STALE — its inputs now hash to 0123\n"
           "  FAIL  version mesh versions/b/x/b__p.glb: is STALE — the version record\n"
           "  FAIL  stale: Glessner v4 packaged outputs do not match\n"
           "  FAIL  stale: c__p.glb is STALE — x\n  FAIL  stale: a__p.glb is STALE — again\n")
    m, v = stale_names(log)
    assert m == ["a__p.glb", "c__p.glb"], m
    assert v == ["versions/b/x/b__p.glb"], v
    man = {"a__p.glb": {"generator": "generators/k01_emit.py", "structure_id": "a"},
           "c__p.glb": {"generator": None, "structure_id": "c"}}
    vman = {"versions/b/x/b__p.glb": {"generator": VERSIONS_EMITTER, "structure_id": "b"}}
    jobs, orphans = plan(m, v, man, vman, ("generators/k01_emit.py", VERSIONS_EMITTER))
    assert jobs == {"generators/k01_emit.py": ["a"], VERSIONS_EMITTER: ["b"]}, jobs
    assert orphans == ["c__p.glb (no pure emitter recorded)"], orphans
    assert "generators/k12_emit.py" in pure_emitters()
    print("restamp_stale self-test: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
