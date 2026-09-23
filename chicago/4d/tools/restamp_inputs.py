#!/usr/bin/env python3
"""Re-stamp `assets/manifest.json` when the input-hash RECIPE changed, not the data.

    tools/restamp_inputs.py --reason "..."            # dry run: what would move
    tools/restamp_inputs.py --reason "..." --write    # move it

WHY THIS EXISTS (T-0164). `tools/validate.py`'s staleness gate already tells you
to do this, in its own words:

    manifest inputs_scheme is 'X' but the generators compute 'Y' — the two sides
    are hashing different things ... Re-stamp the manifest (and say in the commit
    why the definition changed)

and until now nothing could. `inputs_sha256` is written in exactly two places,
`generators/build.py` and `generators/terrain_gen.py`, and both of them are
bakes. So the only way to change the DEFINITION of an input hash was to rebake
349 GLBs whose geometry nobody had touched — twenty minutes of Cycles, a diff of
every mesh in the town (Cycles AO is not bit-reproducible, so they all move),
and no way for a reader to tell that from a real content change.

That cost is why the recipe was never fixed. T-0164 is the case in point: while
`generators/common/phases.py` was globbed into both recipes, one comment line in
it staled **349 of 349** assets, and taking it back out — which changes no
vertex — would itself have staled 349 of 349.

## The one guard that makes this safe, and why it is the right one

A tool that rewrites the freshness record can obviously be used to bless a mesh
that really is out of date. This one cannot, and not by asking nicely:

**It refuses unless a SCHEME constant has moved.** `mesh_inputs.SCHEME` and
`terrain_inputs.SCHEME` are the recipes' own version numbers, bumped by hand in
the commit that changes what the recipe hashes. If the manifest already records
the schemes the generators compute, then the two sides agree about what they are
hashing, and any hash that has moved has moved because the DATA moved. That is
staleness, it means the committed mesh is the old building, and the answer is
`tools/bake.sh` — never this. So the legal window for a re-stamp is exactly the
commit that bumps a scheme, which is also the commit a reviewer is reading.

Two more, because the first only bounds *when*:

  * **Every asset's bytes must still match the manifest.** If a GLB on disk is
    not the length the manifest recorded, geometry moved after the bake and this
    is not a recipe-only change. Refuse.
  * **Nothing but the hash fields may change.** The written manifest is diffed
    against the loaded one and any other moved key is a bug in this tool. Refuse.

`--reason` is required and is echoed into the run's output, because the gate's
message asks for a sentence and a sentence nobody typed is not one.

NO BLENDER, NO NETWORK. It recomputes with the generators' own recipe — the same
two calls `validate.py` makes — and writes numbers, never meshes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ROOT = ROOT.parent
DATA = ROOT / "data"
MANIFEST = ROOT / "assets" / "manifest.json"
GLTF = ROOT / "assets" / "gltf"


class RestampRefused(SystemExit):
    """The preconditions for a recipe-only re-stamp are not met."""

    def __init__(self, msg: str) -> None:
        super().__init__(f"REFUSED — {msg}")


def _load_structures() -> dict:
    out = {}
    for p in sorted((DATA / "structures").glob("*.json")):
        if p.name == "index.json":
            continue
        try:
            out[p.stem] = json.loads(p.read_text())
        except json.JSONDecodeError as e:
            raise RestampRefused(f"{p.relative_to(ROOT)} is not loadable: {e}") from e
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--reason", required=True,
                    help="why the recipe changed — the sentence the gate asks for")
    ap.add_argument("--write", action="store_true",
                    help="apply; without it nothing is written")
    args = ap.parse_args(argv)

    if not MANIFEST.exists():
        raise RestampRefused("assets/manifest.json does not exist, so there is "
                             "nothing to re-stamp")
    before = json.loads(MANIFEST.read_text())
    manifest = json.loads(MANIFEST.read_text())
    assets = manifest.get("assets", {})

    sys.path.insert(0, str(ROOT / "generators"))
    import mesh_inputs  # noqa: PLC0415
    import terrain_gen  # noqa: PLC0415
    import terrain_inputs  # noqa: PLC0415

    # GUARD 1 — a scheme must have moved. Without this the tool is a way to bless
    # a stale mesh; with it, the only hashes it can rewrite are ones whose
    # DEFINITION changed in the same commit.
    schemes = {"inputs_scheme": (before.get("inputs_scheme"), mesh_inputs.SCHEME),
               "terrain_inputs_scheme": (before.get("terrain_inputs_scheme"),
                                         terrain_inputs.SCHEME)}
    moved = {k: v for k, v in schemes.items() if v[0] != v[1]}
    if not moved:
        raise RestampRefused(
            "no scheme has moved — the manifest and the generators already agree "
            "about what they are hashing, so any hash that differs differs "
            "because the DATA moved. That is staleness and the answer is "
            "tools/bake.sh, not a re-stamp.")
    for key, (was, now) in sorted(moved.items()):
        print(f"  scheme {key}: {was!r} -> {now!r}")

    # GUARD 2 — geometry is demonstrably untouched since the bake that wrote this.
    for name, entry in sorted(assets.items()):
        path = GLTF / name
        if not path.exists():
            raise RestampRefused(f"manifest lists {name} but assets/gltf/{name} is "
                                 f"missing — the record of a bake outlived its output")
        recorded_bytes = entry.get("bytes")
        if recorded_bytes is None:
            raise RestampRefused(f"{name} records no byte length, so nothing here can "
                                 f"say its geometry is untouched")
        actual = path.stat().st_size
        if actual != recorded_bytes:
            raise RestampRefused(
                f"{name} is {actual} bytes on disk and {recorded_bytes} in the "
                f"manifest — geometry moved after the bake, so this is not a "
                f"recipe-only change. Re-bake it.")

    structures = _load_structures()
    by_id = {st.get("id"): st for st in structures.values() if isinstance(st, dict)}

    changed, same, unchecked = 0, 0, 0
    for name, entry in sorted(assets.items()):
        if entry.get("structure_id"):
            st = by_id.get(entry["structure_id"])
            if st is None:
                raise RestampRefused(f"{name} was built from structure "
                                     f"'{entry['structure_id']}', which no longer exists")
            phase = next((p for p in st.get("phases", [])
                          if p.get("id") == entry.get("phase_id")), None)
            if phase is None:
                raise RestampRefused(f"{name} was built from phase "
                                     f"'{entry.get('phase_id')}' of "
                                     f"{entry['structure_id']}, which the record no longer has")
            got = mesh_inputs.structure_inputs_sha(st, phase, entry.get("archetype"))
        elif entry.get("terrain_epoch"):
            got = terrain_gen.terrain_inputs_sha(
                DATA / "terrain" / "epochs" / entry["terrain_epoch"])
        else:
            unchecked += 1
            continue
        if got == entry.get("inputs_sha256"):
            same += 1
        else:
            changed += 1
            entry["inputs_sha256"] = got

    manifest["inputs_scheme"] = mesh_inputs.SCHEME
    manifest["terrain_inputs_scheme"] = terrain_inputs.SCHEME

    # GUARD 3 — nothing but the hash fields moved.
    allowed = {"inputs_sha256"}
    for name, entry in sorted(assets.items()):
        old = before["assets"][name]
        for key in set(old) | set(entry):
            if key in allowed:
                continue
            if old.get(key) != entry.get(key):
                raise RestampRefused(f"{name}.{key} changed, and this tool may only "
                                     f"move input hashes — that is a bug in it")
    for key in set(before) | set(manifest):
        if key in {"assets", "inputs_scheme", "terrain_inputs_scheme"}:
            continue
        if before.get(key) != manifest.get(key):
            raise RestampRefused(f"manifest.{key} changed, and this tool may only "
                                 f"move input hashes — that is a bug in it")

    print(f"  {changed} hash(es) move, {same} already match"
          + (f", {unchecked} not input-tracked" if unchecked else ""))
    print(f"  reason: {args.reason}")
    if not args.write:
        print("  dry run — nothing written. Re-run with --write to apply.")
        return 0
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"  written: {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
