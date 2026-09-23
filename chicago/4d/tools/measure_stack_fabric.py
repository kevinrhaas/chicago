#!/usr/bin/env python3
"""What every stack in the town is painted, read off the committed masters.

**T-0137.** T-0008 took the town's chimneys off the roof material — R-W2a finding 1,
"a stack came out painted whatever weathering condition its own roof was dealt" — and
left one archetype behind. `fort_structure` went on building its stacks with `M_ROOF`,
so the garrison's ten stacks were the only ones in Chicago the colour of the roof they
pass through. Nothing measured that, which is why it survived a parcel that existed to
fix it, so this is the instrument, and `tools/check.sh` runs it as a gate.

It is deliberately **archetype-blind**: it asks the BYTES, not the generator that wrote
them, because the generator is the thing under test.

## How a stack is found without decoding a mesh

Every archetype here emits ONE primitive per material, and a glTF POSITION accessor is
REQUIRED to carry `min`/`max`. So the highest vertex belonging to each material is
readable from the JSON chunk alone, at no cost.

The test is then a fact about geometry rather than about names: **a stack has to clear
the roof to draw at all.** An interior stack rises inside the wall and breaks the roof
at the ridge; an exterior gable stack is built against the wall and carries its flue
past the eave. Either way, on a building whose record counts a chimney, something must
stand above the roof — and if the highest thing above the roof IS the roof material,
the stack is inside the roof's own primitive and is painted with it.

**What the name column is and is not.** `material` names the primitive that reaches
highest above the roof, and it is REPORTING, not the test. It is not sound as a test in
either direction: `brick` and `log` are wall materials on some records as well as stack
materials on others, and on `wolf_point_tavern` the highest thing over the roof is the
tavern's own signpost at 8.297 m, standing 1.8 m above its (correctly painted) stack.
The gate does not read it. What the gate reads is the clearance.

    python3 tools/measure_stack_fabric.py           # the whole town
    python3 tools/measure_stack_fabric.py --fort    # the garrison alone
    python3 tools/measure_stack_fabric.py --gate --quiet   # check.sh's line

Exit 1 if any building that counts a chimney has nothing above its roof.
"""
import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from measure_glbs import read_glb  # noqa: E402

#: The exporter runs `export_yup=True`, so glTF +Y is Blender +Z is up.
UP = 1


def chimney_count(phase):
    v = (phase.get("form") or {}).get("chimneys")
    if isinstance(v, dict):
        v = v.get("value")
    return v if isinstance(v, int) else 0


def material_tops(js):
    """{material name: the highest vertex any primitive of it holds}."""
    tops = {}
    for mesh in js.get("meshes", []):
        for prim in mesh.get("primitives", []):
            mi = prim.get("material")
            if mi is None:
                continue
            name = js["materials"][mi].get("name", f"#{mi}")
            top = js["accessors"][prim["attributes"]["POSITION"]]["max"][UP]
            tops[name] = max(tops.get(name, top), top)
    return tops


def readings(fort_only=False):
    manifest = json.loads((ROOT / "assets" / "manifest.json").read_text())["assets"]
    by_key = {(a["structure_id"], a.get("phase_id")): name
              for name, a in manifest.items() if "structure_id" in a}
    arch_of = {(a["structure_id"], a.get("phase_id")): a.get("archetype")
               for a in manifest.values() if "structure_id" in a}

    out = []
    for path in sorted((ROOT / "data" / "structures").glob("*.json")):
        rec = json.loads(path.read_text())
        if fort_only and not rec["id"].startswith("fort_dearborn"):
            continue
        for phase in rec.get("phases", []):
            n = chimney_count(phase)
            if n <= 0:
                continue
            key = (rec["id"], phase.get("id"))
            if key not in by_key:
                continue
            tops = material_tops(read_glb(ROOT / "assets" / "gltf" / by_key[key])[0])
            roof = tops.get("roof")
            if roof is None:
                continue
            above = {m: t for m, t in tops.items() if m != "roof" and t > roof}
            best = max(above.items(), key=lambda kv: kv[1], default=None)
            out.append({
                "id": rec["id"], "archetype": arch_of[key], "stacks": n,
                "roof_top": roof,
                "material": best[0] if best else "roof",
                "clear": (best[1] - roof) if best else 0.0,
            })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fort", action="store_true",
                    help="only the buildings inside Fort Dearborn")
    ap.add_argument("--gate", action="store_true", help="pass/fail only")
    ap.add_argument("--quiet", action="store_true", help="suppress the per-building table")
    args = ap.parse_args()

    rows = readings(fort_only=args.fort)
    bad = [r for r in rows if r["clear"] <= 0.0]

    if not (args.gate or args.quiet):
        width = max((len(r["id"]) for r in rows), default=10)
        print(f"{'structure':<{width}}  {'archetype':<18} {'stacks':>6}  "
              f"{'highest over the roof':<22} {'by':>9}")
        for r in rows:
            flag = "   <- NOTHING CLEARS THE ROOF" if r["clear"] <= 0 else ""
            print(f"{r['id']:<{width}}  {(r['archetype'] or '?'):<18} {r['stacks']:>6}  "
                  f"{r['material']:<22} {r['clear']:>7.3f} m{flag}")
        print()

    fams = {}
    for r in rows:
        fams.setdefault(r["archetype"], {}).setdefault(r["material"], 0)
        fams[r["archetype"]][r["material"]] += 1
    stacks = sum(r["stacks"] for r in rows)
    if not args.quiet:
        print(f"{len(rows)} buildings counting {stacks} stacks, "
              f"by archetype and by what stands over the roof:")
        for arch in sorted(fams, key=str):
            painted = ", ".join(f"{m} x{c}" for m, c in sorted(fams[arch].items()))
            print(f"  {(arch or '?'):<18} {painted}")

    if bad:
        n = sum(r["stacks"] for r in bad)
        print(f"FAIL: {len(bad)} building(s) carrying {n} stacks have NOTHING above the "
              f"roof material, so the stack is inside the roof's own primitive and is "
              f"painted the colour of the roof it passes through — R-W2a finding 1, "
              f"T-0137: {', '.join(r['id'] for r in bad)}")
        return 1
    print(f"OK: all {stacks} stacks in the town stand clear of their roof in a material "
          f"of their own.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
