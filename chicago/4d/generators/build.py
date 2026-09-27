"""Generate meshes from data/. Run inside Blender:

    blender -b -noaudio --factory-startup --python generators/build.py -- [args]

    --all           build every structure phase resolvable for the scene
    --only <id>     build one structure id
    --scene <id>    scene to resolve phases against (default 1835)
    --no-bake       skip UV + AO baking (fast iteration)
    --ao            bake ambient occlusion (opt-in; nothing in the nightly passes it —
                    see emit.bake_ao() for why, and generators/ao_export.py for the guard
                    that refuses a GLB whose occlusion did not survive the export)
    --out <dir>     output directory (default assets/gltf)

Refuses to run while data/datum.json is unverified — fixing the origin after
geometry exists means regenerating everything, so the build makes that impossible
rather than merely discouraged.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))
sys.path.insert(0, str(ROOT / "generators"))

import bpy  # noqa: E402

import ao_export  # noqa: E402
import emit  # noqa: E402
import mesh_inputs  # noqa: E402

from common.phases import drawn_by_another_layer  # noqa: E402


def argv_after_ddash() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def load(p: Path):
    return json.loads(p.read_text())


def resolve_phase(structure: dict, target: dt.date):
    """The scene rule, identical to tools/validate.py: exactly one phase must
    cover the date, or the structure is not in the scene."""
    hits = []
    for ph in structure.get("phases", []):
        r = ph.get("documented_range", {})
        try:
            frm = dt.date.fromisoformat(r["from"])
            to = dt.date.fromisoformat(r["to"])
        except (KeyError, ValueError):
            continue
        if frm <= target <= to:
            hits.append(ph)
    if len(hits) > 1:
        raise SystemExit(f"{structure['id']}: {len(hits)} phases cover {target}; exactly one must")
    return hits[0] if hits else None


def inputs_hash(structure: dict, phase: dict, archetype: str) -> str:
    """Hash of everything that determines this mesh, written into
    `assets/manifest.json` so `tools/check.sh` can tell a stale committed GLB from
    a fresh one. Determinism is defined on inputs, because Cycles AO is not
    bit-reproducible across hardware.

    The recipe lives in `generators/mesh_inputs.py` rather than here, because the
    gate that compares the hash has to recompute it in a sandbox with no Blender,
    and this module cannot be imported without bpy."""
    return mesh_inputs.structure_inputs_sha(structure, phase, archetype)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--scene", default="1835")
    ap.add_argument("--no-bake", action="store_true",
                    help="skip UV unwrap as well as AO")
    ap.add_argument("--ao", action="store_true",
                    help="bake ambient occlusion. OFF by default: see emit.bake_ao().")
    ap.add_argument("--out", default=str(ROOT / "assets" / "gltf"))
    args = ap.parse_args(argv_after_ddash())

    datum = load(ROOT / "data" / "datum.json")
    if not datum.get("verified"):
        print("REFUSING TO BUILD: data/datum.json is not verified.\n"
              "Fixing the origin after geometry exists means regenerating everything.\n"
              "See docs/EPOCHS.md and docs/RESEARCH/datum_derivation.md.")
        return 2

    scene = load(ROOT / "data" / "scenes" / f"{args.scene}.json")
    target = dt.date.fromisoformat(scene["target_date"])
    outdir = Path(args.out)

    manifest_path = ROOT / "assets" / "manifest.json"
    manifest = load(manifest_path) if manifest_path.exists() else {}
    manifest.setdefault("assets", {})
    manifest["blender"] = bpy.app.version_string.split()[0]
    # What the hashes below mean. tools/validate.py refuses to compare against a
    # scheme it does not compute, so redefining freshness is a visible event.
    manifest["inputs_scheme"] = mesh_inputs.SCHEME

    built = 0
    for path in sorted((ROOT / "data" / "structures").glob("*.json")):
        st = load(path)
        if args.only and st["id"] != args.only:
            continue
        phase = resolve_phase(st, target)
        if phase is None:
            print(f"skip {st['id']}: no phase covers {target}")
            continue
        # T-0161. The phase says its geometry is built at load by another layer,
        # so baking one here puts a mesh in the tree that `tools/validate.py`
        # then refuses — which is what made every full bake need a hand-deletion
        # to pass its own gate. The test is imported rather than restated: see
        # generators/common/phases.py for why a fourth copy was the problem.
        if drawn_by_another_layer(phase):
            layer = (phase.get("drawn_by") or {}).get("layer", "another layer")
            print(f"skip {st['id']}: phase '{phase.get('id', '?')}' is drawn by {layer}")
            continue
        arch = st["archetype"]
        if arch not in emit.ARCHETYPES:
            print(f"skip {st['id']}: archetype '{arch}' has no generator yet")
            continue

        # T-1654. Every line that can move a vertex lives in generators/emit.py, and
        # that module's bytes — not this file's — are what mesh_inputs.py hashes into
        # each asset's freshness record. What is left here chooses the structures and
        # keeps the books, so editing it cannot stale a committed mesh.
        name = f"{st['id']}__{phase['id']}"
        made = emit.emit_structure(st, phase, arch, outdir / f"{name}.glb",
                                   bake=not args.no_bake, ao=args.ao)
        out, baked_mean = made.path, made.baked_mean

        entry = {
            "kind": "generated",
            "structure_id": st["id"],
            "phase_id": phase["id"],
            "archetype": arch,
            "inputs_sha256": inputs_hash(st, phase, arch),
            "bytes": out.stat().st_size,
            "baked_ao": bool(args.ao and not args.no_bake),
        }
        # Read the exported BYTES back and refuse a file whose occlusion texture is
        # not the occlusion that was baked. On the bytes rather than on the in-memory
        # image, because memory is not where this breaks: T-0158 shipped a bake that
        # read min 0.000 / max 1.000 in Blender and min 0 / max 0 in the GLB, with the
        # run exiting 0 and the manifest recording baked_ao: true. The manifest entry
        # is written only if the file passes, so `baked_ao: true` cannot outlive the
        # occlusion again.
        if baked_mean is not None:
            try:
                stats = ao_export.assert_ao_survived_export(out, baked_mean)
            except ao_export.AoExportError as e:
                raise SystemExit(f"REFUSING TO RECORD THIS BAKE: {e}") from e
            entry["ao_occlusion_mean"] = round(stats["mean"], 6)
            print(f"       AO baked mean {baked_mean:.4f} -> exported mean "
                  f"{stats['mean']:.4f} (min {stats['min']:.4f} max {stats['max']:.4f}) over "
                  f"{stats['texels']:,} texels, "
                  f"{abs(stats['mean'] - baked_mean) / max(baked_mean, 1e-9) * 100:.1f} % drift")
        manifest["assets"][out.name] = entry
        print(f"built {out.name}  {out.stat().st_size:,} bytes  ~{made.tris} tris")
        built += 1

    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"\n{built} asset(s) built; manifest updated")
    return 0 if built else 1


if __name__ == "__main__":
    sys.exit(main())