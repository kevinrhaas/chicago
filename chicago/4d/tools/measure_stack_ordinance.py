#!/usr/bin/env python3
"""Eighteen inches of stack above every roof — the town's own by-law, measured.

**T-0333.** The Trustees of the Town of Chicago passed their by-laws on 5 August 1835,
and `chicago_democrat_1835_08_19#c005` prints section 18 line by line:

> *"every stove pipe or chimney passing through the roof of any building shall extend
> and be carried at least eighteen inches above the roof, and no stove pipe shall be
> passed through the side or end of any building"* — under a penalty of five dollars for
> each and every offence, with a fire warden walking every house, store and shop in his
> district once a month from September to May (section 21).

**This is the first documented DIMENSIONAL constraint this project holds on anything
above a roof line**, and it points the other way from the sentence the flagstaff work
quotes — Andreas describing a town with *"not a single steeple nor a chimney four feet
above any roof."* Four feet is a maximum a memoirist noticed; eighteen inches is a
minimum the town enforced, and together they bracket every stack in the scene.

## What it measures, and why on the bytes

`tools/measure_stack_fabric.py` (T-0137) asks what a stack is PAINTED and reads the
committed masters' accessor bounds to do it. This asks the neighbouring question — how
far a stack stands above the roof it passes through — off the same bounds and on the
same principle: **the generator is the thing under test, so ask the geometry, not the
generator.** A glTF POSITION accessor is required to carry `min`/`max`, so the highest
vertex of each material is readable from the JSON chunk with no mesh decoded.

The clearance is measured against the top of the `roof` material, which is the RIDGE.
That is the conservative reading in the two ways it can be wrong:

- A stack standing off the ridge — `frame_storefront` on a shed roof, `frame_tavern`
  across the frontage — breaks a roof plane LOWER than the ridge, so its true projection
  above its own roof is larger than the figure here.
- A building carrying stacks on two roofs (a `frame_dwelling` ell, a `log_dwelling`
  frame addition) reports its TALLEST stack. That the lower one clears its own ridge by
  the same margin is the archetype's guarantee, not this measurement's: every archetype
  builds each stack with one helper, relative to the ridge it is handed. Said plainly
  here rather than left for a reader to assume.

## What the ordinance's second clause binds, which is nothing today

*"No stove pipe shall be passed through the side or end of any building."* **This model
draws no stove pipe anywhere.** Every one of the stacks below is masonry — brick on the
argument `docs/RESEARCH/chimneys.md` makes from Blodgett's yard, the brick Lake House and
the Petford watercolour — and the archetypes carry no pipe object at all. `log_dwelling`'s
stack stands OUTSIDE the gable rather than inside it, which is the frontier pattern and
not a pipe through an end wall: it is a chimney, and it is carried above the roof like
every other. So the clause is recorded and binds nothing that is drawn.

## The corporation limits, and why this gate is a ratchet rather than an enforcement

Section 18 binds *"within the limits of the Corporation"*, and until T-0436 this file
said that section 22 of the same sitting walks those limits. **IT DOES NOT.** Section 22
draws the hay-stacking boundary, which is a DIFFERENT and narrower line and is T-0334's
— committed since that ticket landed, at `data/reconstruction/1835_hay_limits.json`, and
199 acres against this boundary's 532. Reading section 22 as the corporate limits is a
mistake this docstring made and this paragraph retracts. The corporation's limits are the ones the Trustees walked on 7 November 1833
and printed three weeks later in the first number of the Chicago Democrat
(`chicago_democrat_1833_11_26#c024`, tier 1) — and since T-0436 they are committed, at
`data/reconstruction/1835_corporation_limits.json`, resolved by
`tools/measure_corporation_limits.py` from the committed streets and the committed
shoreline.

So this gate now knows which buildings the by-law reached, and says so: **twenty-four
drawn structures stand outside the limits, eight of them carrying twelve chimneys between
them, and section 18 never bound one of them.** All twenty-four are on the United States Reservation or the
harbour beyond it — ground the 1833 boundary walks around and the extension of February
1835 withheld again.

It still gates every stack in the town, and that is deliberate. Every stack already
clears eighteen inches on both sides of the line, so the ratchet costs nothing and keeps
one from dropping back under; and the twelve stacks beyond the line are held to the figure
by their archetypes rather than by the by-law. What has changed is that the reach is now REPORTED instead of
assumed, so nothing can be quietly conformed to a rule that never bound it. The day a
record legitimately stands a shorter stack outside the limits, that is the boundary to
scope on, and the failure message says which side of it the building is on.

    python3 tools/measure_stack_ordinance.py            the census
    python3 tools/measure_stack_ordinance.py --gate --quiet    check.sh's line
    python3 tools/measure_stack_ordinance.py --self-test       the assertions, fired

Exit 1 if any drawn stack stands less than eighteen inches above its roof.
"""
import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from measure_glbs import read_glb                       # noqa: E402
from measure_stack_fabric import chimney_count, material_tops   # noqa: E402
from measure_corporation_limits import split as corporation_split   # noqa: E402

#: Eighteen inches, stated converted per data/datum.json's units rule.
MINIMUM_M = 18 * 0.0254

#: The materials an archetype builds a stack with. `roof` is excluded by construction —
#: a stack painted the colour of its own roof is T-0137's fault and its own gate.
STACK_MATERIALS = ("chimney", "brick")

#: A ridge is modelled to the centimetre, so a clearance is tested to the millimetre.
EPS_M = 0.0005


def readings():
    """One row per phase whose record counts a chimney and whose master is committed."""
    manifest = json.loads((ROOT / "assets" / "manifest.json").read_text())["assets"]
    by_key = {(a["structure_id"], a.get("phase_id")): name
              for name, a in manifest.items() if "structure_id" in a}
    arch_of = {(a["structure_id"], a.get("phase_id")): a.get("archetype")
               for a in manifest.values() if "structure_id" in a}

    out = []
    for path in sorted((ROOT / "data" / "structures").glob("*.json")):
        rec = json.loads(path.read_text())
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
            stack = {m: t for m, t in tops.items() if m in STACK_MATERIALS}
            if not stack:
                continue
            material, top = max(stack.items(), key=lambda kv: kv[1])
            out.append({"id": rec["id"], "archetype": arch_of[key], "stacks": n,
                        "material": material, "roof_top": roof, "above": top - roof})
    return out


def offenders(rows):
    return [r for r in rows if r["above"] < MINIMUM_M - EPS_M]


def report(rows, quiet=False):
    bad = offenders(rows)
    _inside, outside = corporation_split()
    beyond = [r for r in rows if r["id"] in set(outside)]
    if not quiet:
        width = max((len(r["id"]) for r in rows), default=10)
        print(f"{'structure':<{width}}  {'archetype':<18} {'stacks':>6} "
              f"{'material':<9} {'above its roof':>16}")
        for r in rows:
            flag = "   <- UNDER EIGHTEEN INCHES" if r in bad else ""
            print(f"{r['id']:<{width}}  {(r['archetype'] or '?'):<18} {r['stacks']:>6} "
                  f"{r['material']:<9} {r['above']:>10.3f} m "
                  f"({r['above'] / 0.0254:>4.1f} in){flag}")
        print()

        by_arch = {}
        for r in rows:
            by_arch.setdefault(r["archetype"], []).append(r["above"])
        print("by archetype — the ordinance's floor is 0.457 m (18.0 in):")
        for arch in sorted(by_arch, key=str):
            v = by_arch[arch]
            print(f"  {(arch or '?'):<18} {len(v):>4} building(s)  "
                  f"least {min(v):.3f} m ({min(v) / 0.0254:.1f} in)  "
                  f"most {max(v):.3f} m ({max(v) / 0.0254:.1f} in)")

        print(f"\nwhich of them the by-law actually reached — the limits of the "
              f"Corporation as the Trustees\nwalked them on 7 November 1833 "
              f"(chicago_democrat_1833_11_26#c024, resolved by\n"
              f"tools/measure_corporation_limits.py):")
        print(f"  inside the limits  {len(rows) - len(beyond):>4} building(s), "
              f"{sum(r['stacks'] for r in rows if r not in beyond):>4} stack(s) — "
              f"section 18 bound these")
        print(f"  outside them       {len(beyond):>4} building(s), "
              f"{sum(r['stacks'] for r in beyond):>4} stack(s) — it bound none of "
              f"these, and they are gated anyway")
        for r in beyond:
            print(f"      {r['id']:<34} {r['above']:.3f} m "
                  f"({r['above'] / 0.0254:.1f} in)")

    stacks = sum(r["stacks"] for r in rows)
    if bad:
        n = sum(r["stacks"] for r in bad)
        print(f"FAIL: {len(bad)} building(s) carrying {n} stack(s) stand less than "
              f"eighteen inches above their own roof, which the Town of Chicago's "
              f"by-law of 5 August 1835 section 18 forbids under a five-dollar penalty "
              f"(chicago_democrat_1835_08_19#c005): "
              f"{', '.join('%s %.3f m' % (r['id'], r['above']) for r in bad)}. "
              f"Raise the stack, or — if the building stands OUTSIDE the limits of the "
              f"Corporation — scope this gate on the boundary of 7 November 1833 "
              f"(data/reconstruction/1835_corporation_limits.json; "
              f"tools/measure_corporation_limits.py names the "
              f"{len(outside)} structure(s) that are outside it today) and say in the "
              f"record which side of it the building is on. Do not weaken the eighteen "
              f"inches: it is a documented figure.")
        return 1
    if not quiet:
        least = min(rows, key=lambda r: r["above"])
        print(f"\nOK: all {stacks} stack(s) on {len(rows)} building(s) are carried at "
              f"least eighteen inches above their own roof. The tightest is "
              f"{least['id']} at {least['above']:.3f} m "
              f"({least['above'] / 0.0254:.1f} in).")
    else:
        print(f"OK: all {stacks} stack(s) on {len(rows)} building(s) clear eighteen "
              f"inches above their own roof, per the by-law of 5 August 1835 § 18.")
    return 0


def self_test():
    """The four ways this could pass something it should refuse, fired."""
    cases = [
        ("a stack exactly on the ordinance's floor passes",
         [{"id": "a", "archetype": "x", "stacks": 1, "material": "chimney",
           "roof_top": 4.0, "above": MINIMUM_M}], 0),
        ("a stack a millimetre under it fails",
         [{"id": "a", "archetype": "x", "stacks": 1, "material": "chimney",
           "roof_top": 4.0, "above": MINIMUM_M - 0.001}], 1),
        ("a stack level with its own roof fails",
         [{"id": "a", "archetype": "x", "stacks": 1, "material": "chimney",
           "roof_top": 4.0, "above": 0.0}], 1),
        ("one short stack among compliant ones still fails",
         [{"id": "a", "archetype": "x", "stacks": 1, "material": "chimney",
           "roof_top": 4.0, "above": 0.78},
          {"id": "b", "archetype": "x", "stacks": 2, "material": "brick",
           "roof_top": 4.0, "above": 0.30}], 1),
    ]
    failures = []
    for label, rows, want in cases:
        got = 1 if offenders(rows) else 0
        print(f"  {'fires' if want else 'ok   '}: {label}")
        if got != want:
            failures.append(label)

    # The floor is the ordinance's figure and not a rounded one.
    if abs(MINIMUM_M - 0.4572) > 1e-9:
        failures.append("MINIMUM_M is not eighteen inches")
    print(f"  ok   : the floor is eighteen inches exactly ({MINIMUM_M:.4f} m)")

    if failures:
        print("SELF-TEST FAIL: " + "; ".join(failures))
        return 1
    print(f"SELF-TEST PASS — the ordinance gate fires when broken ({len(cases)} cases)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true", help="pass/fail only")
    ap.add_argument("--quiet", action="store_true", help="suppress the per-building table")
    ap.add_argument("--self-test", action="store_true",
                    help="prove the gate refuses a short stack")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    return report(readings(), quiet=args.gate or args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
