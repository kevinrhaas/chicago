#!/usr/bin/env python3
"""Every reconstructed roof's RIDGE, against the family band its own record cites.

T-0145. `tools/measure_band_claims.py` tests the values a record STATES — its
footprint, its eave, its storeys, its pitch. This tests a value no record states and
every visitor sees: the height the ridge actually reaches, which is what the sampled
pitch and the sampled footprint make together. The crosswalk authors it — every family
but the two `custom` ones carries a `ridge_ft` band beside its eave band — and until
now nothing read that column at all.

WHY IT IS A SEPARATE INSTRUMENT. A ridge is not in the record, so it cannot be measured
off the JSON alone; it has to be either modelled from the archetype or read out of the
built GLB. This tool does BOTH, and reports two different faults:

  ridge outside the family band   the modelled ridge is not inside `ridge_ft`.
  model disagrees with the GLB    `tools/ridge_model.py`'s run is wrong for that
                                  archetype — the roof was set out some other way.

The second is what makes the first trustworthy. The model exists so the sampler in
`tools/family_bands.py` can CHOOSE a pitch whose ridge lands in the band, and a sampler
choosing against a wrong model would be worse than no sampler at all. So the GLB is
read on every run: the top of the `roof` material — the ridge itself, not the chimney
standing over it — and the two numbers must agree to within `TOL_M`.

THE BASELINE IS A RATCHET, NOT AN ALLOWANCE. `tools/ridge_band_baseline.json` records
the roofs that are outside their band TODAY, and this tool fails on any offender that is
not in it and on any listed offender whose ridge has MOVED. So a repair can shrink the
list and nothing can grow it. What is in the list is honest and stated: for several
families no pitch inside the authored pitch band can reach the authored ridge band at
the footprint the family authors, because the archetype points the ridge across the
short axis. That is a conflict between two committed bands and an archetype, and it is
filed as its own ticket rather than papered over by a pitch nobody claims.

    python3 tools/measure_ridge_band.py                  measure and gate
    python3 tools/measure_ridge_band.py --write-baseline record a repair
"""
from __future__ import annotations

import json
import math
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import family_bands  # noqa: E402
import ridge_model  # noqa: E402

FT = 0.3048
BASELINE = ROOT / "tools" / "ridge_band_baseline.json"
GLB_DIR = ROOT / "assets" / "gltf"

# How far the modelled ridge may sit from the ridge the GLB carries. The roof planes
# are slabs with boards laid over them, so the top of the `roof` material stands a
# board's thickness proud of the structural line the model computes; 0.15 m is that
# thickness with room to spare and is far below the resolution of a ridge band, which
# is four to nine feet wide.
TOL_M = 0.15

# A ridge is stated to the foot in the crosswalk, so a ridge is tested to the foot.
EPS_FT = 0.01


def read_glb(path: pathlib.Path):
    data = path.read_bytes()
    magic, _version, length = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67:
        raise ValueError(f"{path}: not a GLB")
    off, js = 12, None
    while off < length:
        clen, ctype = struct.unpack_from("<II", data, off)
        if ctype == 0x4E4F534A:
            js = json.loads(data[off + 8: off + 8 + clen])
        off += 8 + clen + ((4 - clen % 4) % 4 if clen % 4 else 0)
    return js


def roof_top_m(path: pathlib.Path) -> float | None:
    """The top of the `roof` material, in the GLB's own Y-up frame.

    Read off the POSITION accessor's `max`, which glTF requires — so no mesh is
    decoded and no browser is needed. The material name is the filter, because the
    chimney rises past the ridge and the tallest vertex in the file is often its cap.
    """
    js = read_glb(path)
    names = [m.get("name") for m in js.get("materials", [])]
    best = None
    for mesh in js.get("meshes", []):
        for prim in mesh.get("primitives", []):
            mat = prim.get("material")
            if mat is None or names[mat] != "roof":
                continue
            acc = js["accessors"][prim["attributes"]["POSITION"]]
            if not acc.get("max"):
                continue
            top = acc["max"][1]
            best = top if best is None else max(best, top)
    return best


def records() -> list[dict]:
    out = []
    for path in sorted((ROOT / "data" / "structures").glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("reconstruction", {}).get("family"):
            out.append(doc)
    return out


def measure() -> dict:
    fams = family_bands.families()
    findings: list[dict] = []
    drift: list[dict] = []
    tested = 0
    unmodelled: dict[str, int] = {}
    unbanded = 0

    for doc in records():
        fam = doc["reconstruction"]["family"]
        spec = fams.get(fam)
        if spec is None:
            continue
        band = family_bands.ridge_band_m(spec.get("ridge_ft"))
        if band is None:
            unbanded += 1
            continue
        for phase in doc.get("phases", []):
            poly = (phase.get("footprint") or {}).get("polygon")
            form = {k: v.get("value") for k, v in (phase.get("form") or {}).items()}
            if not poly or "roof_pitch_deg" not in form:
                continue
            width = max(p[0] for p in poly) - min(p[0] for p in poly)
            depth = max(p[1] for p in poly) - min(p[1] for p in poly)
            roof_type = str(form.get("roof_type") or "gable")
            # `open_sides` decides which way a shed falls and therefore how high it
            # stands (T-0179). No reconstructed record carries one today, so this reads
            # as the closed shell it always did; a record that gains one moves its
            # modelled ridge with it instead of being measured against the wrong span.
            run = ridge_model.ridge_run_m(doc.get("archetype", ""), roof_type, width, depth,
                                          form.get("gable_front"),
                                          tuple(form.get("open_sides") or ()))
            if run is None:
                unmodelled[doc.get("archetype", "?")] = unmodelled.get(doc.get("archetype", "?"), 0) + 1
                continue
            eave = float(form.get("wall_height_m") or 0.0)
            ridge = family_bands.ridge_m(eave, run, float(form["roof_pitch_deg"]))
            tested += 1

            glb = GLB_DIR / f"{doc['id']}__{phase['id']}.glb"
            if glb.exists():
                built = roof_top_m(glb)
                if built is not None and abs(built - ridge) > TOL_M:
                    drift.append({
                        "id": doc["id"], "family": fam,
                        "archetype": doc.get("archetype"), "roof": roof_type,
                        "modelled_m": round(ridge, 3), "built_m": round(built, 3),
                        "delta_m": round(built - ridge, 3),
                    })

            lo, hi = band
            ft = ridge / FT
            lo_ft, hi_ft = lo / FT, hi / FT
            if lo_ft - EPS_FT <= ft <= hi_ft + EPS_FT:
                continue
            findings.append({
                "id": doc["id"],
                "family": fam,
                "band": spec.get("ridge_ft"),
                "ridge_ft": round(ft, 2),
                "outside_ft": round(lo_ft - ft if ft < lo_ft else ft - hi_ft, 2),
                "direction": "low" if ft < lo_ft else "high",
            })
    return {
        "tested": tested,
        "unbanded": unbanded,
        "unmodelled": unmodelled,
        "findings": findings,
        "drift": drift,
    }


def key(f: dict) -> str:
    return f["id"]


def main() -> int:
    result = measure()
    write = "--write-baseline" in sys.argv
    findings = result["findings"]

    print(f"   {result['tested']} reconstructed roof(s) modelled against a family ridge band; "
          f"{len(findings)} outside it")
    if result["unbanded"]:
        print(f"   {result['unbanded']} record(s) on a family whose ridge_ft is 'custom' — not testable")
    for arch, n in sorted(result["unmodelled"].items()):
        print(f"   {n} record(s) on archetype '{arch}', which tools/ridge_model.py does not model")

    if result["drift"]:
        print("\n   THE MODEL DISAGREES WITH THE BUILT ROOF — tools/ridge_model.py is wrong "
              f"for these (tolerance {TOL_M} m):")
        for d in result["drift"][:20]:
            print(f"     {d['id']:38}{d['archetype']:17}{d['roof']:6} modelled {d['modelled_m']:7.3f} "
                  f"built {d['built_m']:7.3f}  delta {d['delta_m']:+.3f} m")

    for f in sorted(findings, key=key):
        print(f"     {f['id']:38}{f['family']:4} ridge {f['ridge_ft']:6.2f} ft vs {f['band']:8} "
              f"{f['direction']:4} by {f['outside_ft']:.2f} ft")

    if write:
        BASELINE.write_text(json.dumps({
            "$note": "T-0145. Every reconstructed roof whose MODELLED ridge sits outside the "
                     "ridge_ft band its family authors. A RATCHET, not an allowance: "
                     "tools/check.sh fails on any offender not here and on any listed offender "
                     "whose ridge has moved. Regenerate with tools/measure_ridge_band.py "
                     "--write-baseline, and only ever to record a repair.",
            "counts": {"tested": result["tested"], "outside": len(findings)},
            "offenders": {f["id"]: {k: f[k] for k in ("family", "band", "ridge_ft",
                                                      "outside_ft", "direction")}
                          for f in sorted(findings, key=key)},
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"\n   wrote {BASELINE.relative_to(ROOT)} with {len(findings)} offender(s)")
        return 0

    if result["drift"]:
        print("\n   FAIL: the ridge model does not match the geometry the generators build.")
        return 1

    base = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else {"offenders": {}}
    known = base.get("offenders", {})
    problems = []
    for f in findings:
        prior = known.get(f["id"])
        if prior is None:
            problems.append(f"{f['id']}: ridge {f['ridge_ft']} ft is outside {f['band']} ft "
                            f"and is not in the baseline")
        elif abs(float(prior.get("ridge_ft", 0)) - f["ridge_ft"]) > EPS_FT:
            problems.append(f"{f['id']}: ridge moved {prior.get('ridge_ft')} -> {f['ridge_ft']} ft "
                            f"while still outside {f['band']} ft")
    healed = sorted(set(known) - {f["id"] for f in findings})
    if healed:
        problems.append(f"{len(healed)} baselined roof(s) are inside their band now — "
                        f"rerun with --write-baseline to record the repair: "
                        f"{', '.join(healed[:6])}{' ...' if len(healed) > 6 else ''}")
    for p in problems:
        print(f"   FAIL {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
