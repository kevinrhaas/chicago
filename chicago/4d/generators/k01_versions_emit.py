#!/usr/bin/env python3
"""Build the K01 assemblies' structure VERSIONS — pure Python, no Blender (T-3721).

    python3 generators/k01_versions_emit.py                 build every k01_frontage version
    python3 generators/k01_versions_emit.py --only ID[,ID]  the versions of these structures
    python3 generators/k01_versions_emit.py --check         rebuild in memory; refuse if a
                                                            committed version GLB is not those bytes

A structure version (T-1727, docs/STRUCTURE-VERSIONS.md) is a whole record at
`data/structures/versions/<id>/<label>.json` with its own mesh. `generators/build.py`
bakes the versions of Blender archetypes; a K01 record never reaches Blender, and
`generators/k01_emit.py` walks only `data/structures/`, so until this command a version
on the K01 kit had no builder at all. 2126 Prairie's completed house (T-3721) is the
first: the default record stands the July 1904 works shell, the version the finished
front the May 1905 plate shows.

This is a separate command on purpose. `k01_emit.py` is an input to every K01 mesh's
hash (generators/mesh_inputs.py PURE_PYTHON), so teaching it versions would stale all of
them for a change that cannot move a vertex. Here the GLB is `k01_emit.glb_for` — the
same function, the same bytes — written under the version's own paths
(`common.versions.asset_key`) and recorded in `assets/manifest.versions.json` with the
same inputs hash `tools/validate.py --stale` recomputes, so a version is held to its
record exactly as a canonical K01 house is. `tools/bake.sh` runs it beside k01_emit and
hands what it wrote to `tools/web_derivatives.sh`, which records the derivative
(`structure_versions.py record-web`).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))
sys.path.insert(0, str(ROOT / "tools"))

import k01_emit  # noqa: E402
import mesh_inputs  # noqa: E402
from common import versions as V  # noqa: E402

ARCHETYPE = k01_emit.ARCHETYPE


def records(only=None):
    """(version row, record, phase, scenes) for every K01 version phase some scene shows."""
    for v in V.load_versions(ROOT):
        st = v["record"]
        if st.get("archetype") != ARCHETYPE or st.get("id") != v["id"] or V.label_problem(v["label"]):
            continue   # tools/validate.py refuses a misplaced or mislabelled version
        if only and v["id"] not in only:
            continue
        for phase in st.get("phases", []):
            scenes = [sid for sid, day in k01_emit._scenes(st) if k01_emit._covers(phase, day)]
            if scenes:
                yield v, st, phase, scenes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", default="", help="comma list of structure ids")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--wrote", help="append each master written, one name a line (bake.sh)")
    args, _ = ap.parse_known_args(argv)   # bake.sh hands over the Blender bake's flags too
    only = {x for x in args.only.split(",") if x} or None

    manifest = V.read_manifest(ROOT)
    wrote, bad = [], []
    for v, st, phase, scenes in records(only):
        key = V.asset_key(v["id"], v["label"], phase["id"])
        path = ROOT / "assets" / "gltf" / key
        data = k01_emit.glb_for(st, phase, scenes)
        if args.check:
            have = path.read_bytes() if path.exists() else None
            if have != data:
                bad.append(f"{key}: the committed GLB is not what its version record builds "
                           f"({'missing' if have is None else f'{len(have)} vs {len(data)} bytes'}) — "
                           f"run python3 generators/k01_versions_emit.py --only {v['id']}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        old = manifest["assets"].get(key) or {}
        entry = {
            "kind": "generated", "generator": "generators/k01_versions_emit.py",
            "structure_id": v["id"], "phase_id": phase["id"], "archetype": ARCHETYPE,
            "version_label": v["label"],
            "inputs_sha256": mesh_inputs.structure_inputs_sha(st, phase, ARCHETYPE),
            "bytes": len(data), "baked_ao": False,
        }
        if old.get("web_master_sha256"):   # kept so an unmoved master stays derived
            entry["web_master_sha256"] = old["web_master_sha256"]
        manifest["assets"][key] = entry
        wrote.append(key)
        print(f"k01_versions_emit: wrote assets/gltf/{key} ({len(data)} bytes)")
    if args.check:
        for b in bad:
            print(f"  ✗ {b}", file=sys.stderr)
        print("k01_versions_emit --check: ok — every K01 version is the bytes its record builds"
              if not bad else f"k01_versions_emit --check: {len(bad)} problem(s)")
        return 1 if bad else 0
    if wrote:
        V.write_manifest(manifest, ROOT)
    if args.wrote:
        with open(args.wrote, "a") as fh:
            fh.writelines(f"{n}\n" for n in wrote)
    return 0


if __name__ == "__main__":
    sys.exit(main())
