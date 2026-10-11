#!/usr/bin/env python3
"""Build the K12 coach houses a structure record names — pure Python, no Blender (T-2321).

    python3 generators/k12_emit.py                 build every k12_coach_house record
    python3 generators/k12_emit.py --only ID[,ID]  build these (others are ignored)
    python3 generators/k12_emit.py --check         rebuild in memory; refuse if a
                                                   committed GLB is not those bytes

`tools/bake.sh` runs this beside the Blender bake and hands what it wrote to
`tools/web_derivatives.sh`, so a bake reaches these assets the way it reaches every
other. The manifest entry is the one `generators/build.py` writes — `kind`,
`structure_id`, `phase_id`, `archetype`, `inputs_sha256` from `mesh_inputs` — so
`tools/validate.py --stale` holds it to its record like any other mesh. `--check`
adds what Blender cannot offer: the same inputs give the same bytes, so a committed
asset that differs from a rebuild is a hand edit or an unrecorded change.
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
from archetypes import k12_coach_house  # noqa: E402
from archetypes import k12_coach_house_params  # noqa: E402

ARCHETYPE = "k12_coach_house"
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
    k12_coach_house_params.from_phase(phase, st)      # refuse a record the builder cannot read
    data = k12_coach_house.load()
    var = k12_coach_house.structure_variant(st, phase, data)
    return k12_coach_house.structure_glb(var, data, st["id"], phase["id"], scenes)


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
                           f"run python3 generators/k12_emit.py --only {st['id']}")
            continue
        (GLTF / name).write_bytes(data)
        manifest["assets"][name] = {
            "kind": "generated", "generator": "generators/k12_emit.py",
            "structure_id": st["id"], "phase_id": phase["id"], "archetype": ARCHETYPE,
            "inputs_sha256": mesh_inputs.structure_inputs_sha(st, phase, ARCHETYPE),
            "bytes": len(data), "baked_ao": False,
        }
        wrote.append(name)
        print(f"k12_emit: wrote assets/gltf/{name} ({len(data)} bytes)")
    if args.check:
        for b in bad:
            print(f"  ✗ {b}", file=sys.stderr)
        print(f"k12_emit --check: {'FAIL' if bad else 'ok'} — every K12 coach house is the bytes its record builds"
              if not bad else f"k12_emit --check: {len(bad)} problem(s)")
        return 1 if bad else 0
    if wrote:
        MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    if args.wrote:
        with open(args.wrote, "a") as fh:
            fh.writelines(f"{n}\n" for n in wrote)
    return 0


if __name__ == "__main__":
    sys.exit(main())
