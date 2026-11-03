#!/usr/bin/env python3
"""Build the Potawatomi camp groups a structure record names — pure Python, no Blender (T-3342).

    python3 generators/lodge_camp_emit.py                 build every lodge_camp record
    python3 generators/lodge_camp_emit.py --only ID[,ID]  build these (others are ignored)
    python3 generators/lodge_camp_emit.py --check         rebuild in memory; refuse if a
                                                          committed GLB is not those bytes

The haystack route (generators/haystack_emit.py, T-2510) for the reason it gives: a
Blender archetype is registered in `generators/emit.py`, whose bytes are in every Blender
mesh's freshness record, so a new one would restale the town. `tools/bake.sh` runs this
beside the Blender bake and hands what it wrote to `tools/web_derivatives.sh`; the
manifest entry is the one `generators/build.py` writes, so `tools/validate.py --stale`
holds it to its record, and `--check` holds the committed bytes to a rebuild.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

import mesh_inputs  # noqa: E402
from archetypes import lodge_camp  # noqa: E402
from archetypes import lodge_camp_params  # noqa: E402

ARCHETYPE = "lodge_camp"
MANIFEST = ROOT / "assets" / "manifest.json"
GLTF = ROOT / "assets" / "gltf"


def _scenes() -> list[tuple[str, dt.date]]:
    out = []
    for p in sorted((ROOT / "data" / "scenes").glob("*.json")):
        s = json.loads(p.read_text())
        if s.get("target_date"):
            out.append((s["id"], dt.date.fromisoformat(s["target_date"])))
    return out


def _covers(phase: dict, day: dt.date) -> bool:
    rng = phase.get("documented_range") or {}
    lo, hi = rng.get("from"), rng.get("to")
    return bool(lo) and dt.date.fromisoformat(lo) <= day and (not hi or day <= dt.date.fromisoformat(hi))


def records(only=None):
    for p in sorted((ROOT / "data" / "structures").glob("*.json")):
        st = json.loads(p.read_text())
        if not isinstance(st, dict) or st.get("archetype") != ARCHETYPE:
            continue
        if only and st["id"] not in only:
            continue
        for phase in st.get("phases", []):
            scenes = [sid for sid, day in _scenes() if _covers(phase, day)]
            if scenes:
                yield st, phase, scenes


def glb_for(st: dict, phase: dict, scenes) -> bytes:
    return lodge_camp.glb(lodge_camp_params.from_phase(phase, st), st["id"], phase["id"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", default="", help="comma list of structure ids")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--wrote", help="append each master written, one name a line (bake.sh)")
    args, _ = ap.parse_known_args(argv)   # bake.sh hands over the Blender bake's flags too
    only = {x for x in args.only.split(",") if x} or None

    manifest = json.loads(MANIFEST.read_text())
    wrote, bad = [], []
    for st, phase, scenes in records(only):
        name = f"{st['id']}__{phase['id']}.glb"
        data = glb_for(st, phase, scenes)
        if args.check:
            have = (GLTF / name).read_bytes() if (GLTF / name).exists() else None
            if have != data:
                bad.append(f"{name}: the committed GLB is not what its record builds "
                           f"({'missing' if have is None else f'{len(have)} vs {len(data)} bytes'}) — "
                           f"run python3 generators/lodge_camp_emit.py --only {st['id']}")
            continue
        (GLTF / name).write_bytes(data)
        manifest["assets"][name] = {
            "kind": "generated", "generator": "generators/lodge_camp_emit.py",
            "structure_id": st["id"], "phase_id": phase["id"], "archetype": ARCHETYPE,
            "inputs_sha256": mesh_inputs.structure_inputs_sha(st, phase, ARCHETYPE),
            "bytes": len(data), "baked_ao": False,
        }
        wrote.append(name)
        print(f"lodge_camp_emit: wrote assets/gltf/{name} ({len(data)} bytes)")
    if args.check:
        for b in bad:
            print(f"  ✗ {b}", file=sys.stderr)
        print("lodge_camp_emit --check: ok — every camp group is the bytes its record builds"
              if not bad else f"lodge_camp_emit --check: {len(bad)} problem(s)")
        return 1 if bad else 0
    if wrote:
        MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    if args.wrote:
        with open(args.wrote, "a") as fh:
            fh.writelines(f"{n}\n" for n in wrote)
    return 0


if __name__ == "__main__":
    sys.exit(main())
