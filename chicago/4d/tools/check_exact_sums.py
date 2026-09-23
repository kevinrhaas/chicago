#!/usr/bin/env python3
"""T-1486. A derived figure must not have its last digit decided by accumulation order.

`sum()` adds left to right in binary floating point and drifts a few parts in 10^15.
That is nothing on a height or an easting — until the true value sits exactly on the
rounding boundary, at which point the DRIFT, and not the measurement, decides the last
digit that gets committed. Two gated writers flapped their committed output between
this loop's machine and CI's for exactly that reason (T-1477):

  * `generate_plat_lots.ground_reading` printed a mean OUTSIDE its own min and max —
    418 identical 0.885 m samples, min and max rounding up to 0.89, the drifted mean
    accumulating to 0.8849999999999949 and rounding down to 0.88. Rounding is
    monotonic, so that reading is arithmetically impossible, and nothing caught it.
  * `derive_hay_limits.programme_blocks` re-derived four block centroids one way on one
    machine and the other way on another. Kinzie's Addition is platted in feet, so a
    quarter of four corners lands on an exact half-centimetre: twenty of those centroids
    sit precisely on the 2 dp boundary.

`math.fsum` is correctly rounded and order-independent, so the same inputs give the same
last digit on every machine. This gate keeps the sweep swept, and it MEASURES rather
than assumes — the two sites above were found by a red CI run on someone else's branch,
which is the expensive way to find the third.

Three parts, all fast enough for the per-commit gate:

  1. CENSUS. An AST walk of tools/*.py for every `round(...)` whose argument tree
     contains a bare `sum(...)`. Each must be `math.fsum` or carry a one-line
     `# exact-sum-ok: <why>` on or just above the `round(`. A regex cannot do this: four
     of the sites this file found put `round(` and `sum(` on DIFFERENT LINES, and
     `grep -rn "round(sum("` — the search the ticket was written from — misses every one.

  2. MARGINS. For the converted figures whose components are themselves committed, the
     summands are re-added and the result is measured against its rounding boundary. A
     figure landing within one part in 10^12 of the boundary is REPORTED, because that
     is a figure whose last digit `sum()` would have been free to decide either way.

  3. MUTATION. The min/max/mean assertions are only worth having if they fire, so each
     is run once with `math.fsum` restored to `sum()` over the sample set that bit, and
     the gate fails if the assertion stays silent.

  tools/check_exact_sums.py            the gate
  tools/check_exact_sums.py --list     print every site the census found
  tools/check_exact_sums.py --self-test
"""
from __future__ import annotations

import argparse
import ast
import functools
import json
import math
import operator
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
DATA = ROOT / "data"

# tools/cut_school_section_tier.py ACRE_M2 — the international acre, exactly.
ACRE_M2 = 4046.8564224

# One part in 10^12 of the rounding step. A figure this close to the boundary is one
# whose last committed digit sum()'s drift (a few parts in 10^15 of the MAGNITUDE, which
# for these figures is the same order) would have been free to decide either way.
NEAR_BOUNDARY = 1e-12

ALLOW = "# exact-sum-ok:"


# --------------------------------------------------------------------------- census

class _Census(ast.NodeVisitor):
    """Every `round(...)` whose argument tree still adds with a bare `sum(...)`."""

    def __init__(self, src: str):
        self.lines = src.splitlines()
        self.sites: list[dict] = []

    @staticmethod
    def _name(node) -> str | None:
        f = node.func
        if isinstance(f, ast.Name):
            return f.id
        if isinstance(f, ast.Attribute):
            base = f.value.id if isinstance(f.value, ast.Name) else ""
            return f"{base}.{f.attr}"
        return None

    def visit_Call(self, node: ast.Call):
        if self._name(node) == "round" and node.args:
            for inner in ast.walk(node.args[0]):
                if isinstance(inner, ast.Call) and self._name(inner) == "sum":
                    self.sites.append({"line": node.lineno, "sum_line": inner.lineno})
                    break
        self.generic_visit(node)


def _annotated(lines: list[str], lineno: int) -> str | None:
    """The `# exact-sum-ok:` note for a site, on its own line or the one above it."""
    for i in (lineno - 1, lineno - 2):
        if 0 <= i < len(lines) and ALLOW in lines[i]:
            return lines[i].split(ALLOW, 1)[1].strip()
    return None


def census() -> tuple[list[dict], list[dict]]:
    """(unconverted sites still adding with sum(), annotated sites and their reasons)."""
    bad, noted = [], []
    for path in sorted(TOOLS.glob("*.py")):
        src = path.read_text()
        if "round(" not in src:
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError as exc:                     # a broken tool is not ours to judge
            bad.append({"file": path.name, "line": exc.lineno or 0,
                        "why": f"does not parse: {exc.msg}"})
            continue
        walk = _Census(src)
        walk.visit(tree)
        for site in walk.sites:
            why = _annotated(walk.lines, site["sum_line"])
            row = {"file": path.name, "line": site["sum_line"],
                   "code": walk.lines[site["sum_line"] - 1].strip()}
            (noted if why else bad).append({**row, "why": why} if why else row)
    return bad, noted


def converted() -> list[dict]:
    """Every `math.fsum` CALL, for the roll-up — this is what the sweep bought.

    Read off the syntax tree rather than the text, so that this file's own prose about
    `math.fsum` does not count itself as four more conversions.
    """
    out = []
    for path in sorted(TOOLS.glob("*.py")):
        src = path.read_text()
        if "math.fsum" not in src:
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        lines = src.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _Census._name(node) == "math.fsum":
                out.append({"file": path.name, "line": node.lineno,
                            "code": lines[node.lineno - 1].strip()})
    return sorted(out, key=lambda r: (r["file"], r["line"]))


# -------------------------------------------------------------------------- margins

def margin(total: float, nd: int) -> float:
    """How far a figure sits from the rounding boundary, in parts of the rounding step.

    0.0 means the value is exactly on the boundary and the last committed digit is
    decided by whatever the summation drifted to; 0.5 means it is as far from a boundary
    as a figure can be.
    """
    step = 10.0 ** -nd
    scaled = abs(total) / step
    return abs(scaled - math.floor(scaled) - 0.5)


def _load(rel: str):
    return json.loads((DATA / rel).read_text())


def measured_figures() -> list[dict]:
    """Converted figures whose summands are committed beside them, re-added exactly.

    Only an aggregate whose components are themselves in the committed tree can be
    measured without re-running its generator, so this is the subset the per-commit gate
    can afford — and it is the place the next one goes. Each row answers two questions
    at once: does the exact sum still agree with the figure the generator committed, and
    how far does that figure sit from the rounding boundary where the drift gets to
    decide the last digit.
    """
    rows = []

    def take(label: str, values, nd: int, committed):
        values = list(values)
        if not values:
            return
        total = math.fsum(values)
        rows.append({"figure": label, "n": len(values), "nd": nd,
                     "value": round(total, nd), "committed": committed,
                     "margin": margin(total, nd)})

    north = _load("traces/vectors/north_division_tier_lots.json")
    take("cut_north_division_tier.tier_ground_m2",
         (b["area_m2"] for b in north["blocks"]), 1,
         north["counts"]["tier_ground_m2"])

    school = _load("traces/vectors/school_section_tier_lots.json")
    counts = school["counts"]
    blocks = school["blocks"]
    take("cut_school_section_tier.tier_ground_m2",
         (b["area_m2"] for b in blocks), 1, counts["tier_ground_m2"])
    take("cut_school_section_tier.tier_ground_acres",
         (b["area_m2"] / ACRE_M2 for b in blocks), 1, counts["tier_ground_acres"])
    take("cut_school_section_tier.lot_ground_acres",
         (lot["area_acres"] for b in blocks for lot in b.get("lots", [])), 1,
         counts["lot_ground_acres"])

    wedge = _load("traces/wabansia_seating.json")["water_lot_wedge_local_enu_m"]
    take("seat_wabansia_streets.tiled_wedge_area_m2",
         (r["area_m2"] for r in wedge["ranks"]), 1, None)

    return rows


# ------------------------------------------------------------------------- mutation

def naive_sum(values) -> float:
    """`sum()` as CPython computed it before 3.12: left to right, uncompensated.

    THIS IS WHY THE TWO WRITERS FLAPPED, and it is the measurement this ticket was
    missing. CPython 3.12 gave `sum()` Neumaier compensation for float inputs, so on a
    3.12 interpreter `sum()` and `math.fsum` agree on every sample set below and the
    drift is INVISIBLE. `.github/workflows/chicago-4d-check.yml` pins python 3.11, which
    has the uncompensated loop — so the same code, on the same data, printed a different
    last digit in CI than it did on the machine that committed it, and each re-derivation
    looked correct where it ran and stale where it did not.

    Reproduced exactly: 418 samples of a perfectly flat 0.885 m mean to
    0.8849999999999949 here, which is the figure the T-1477 gate reported off CI.
    """
    return functools.reduce(operator.add, values, 0.0)


def mutation() -> list[str]:
    """Restore the uncompensated sum under the min-max-mean refusal and watch it fire.

    An assertion nobody has seen fail is a comment. The case is the one that bit: the
    School Section's blocks 95, 118 and 119, each perfectly flat at 0.885 m over 418
    samples, where min and max round UP to 0.89 and the drifted mean rounds DOWN to 0.88.
    """
    from exact_sums import consistent_reading          # noqa: E402  (same directory)

    out = []
    flat = [0.885] * 418
    try:
        lo, mean, hi = consistent_reading(flat, 2, label="flat block")
        if (lo, mean, hi) != (0.89, 0.89, 0.89):
            out.append(f"the flat block should read 0.89 throughout, read {lo}/{mean}/{hi}")
    except AssertionError as exc:
        out.append(f"fsum should not have fired on the flat block: {exc}")
    try:
        consistent_reading(flat, 2, summer=naive_sum, label="flat block")
        out.append("the min-max-mean refusal did NOT fire with the uncompensated sum "
                   "restored over the 418 flat samples that bit — the assertion is a "
                   "comment rather than a check")
    except AssertionError:
        pass
    drifted = naive_sum(flat) / len(flat)
    if round(drifted, 2) != 0.88:
        out.append(f"the mutation case has stopped drifting: it means {drifted!r}, which "
                   "no longer rounds away from its own min and max, so it is testing "
                   "nothing")
    return out


def summation_note() -> str:
    """What the running interpreter's `sum()` would have done, said out loud.

    A gate that is green because its interpreter hides the fault is not a green gate, and
    this line is the difference between the two machines that flapped.
    """
    flat = [0.885] * 418
    compensated = sum(flat) == math.fsum(flat)
    return (f"python {sys.version_info.major}.{sys.version_info.minor}: bare sum() is "
            + ("COMPENSATED here, so it hides the drift this gate is about — CI runs "
               "3.11, where it does not" if compensated else
               "UNCOMPENSATED here, the drift is live"))


# ----------------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="print every converted site")
    ap.add_argument("--self-test", action="store_true", dest="self_test")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    bad, noted = census()
    fsums = converted()
    print(summation_note())
    print(f"{len(fsums)} figure(s) summed exactly with math.fsum; "
          f"{len(noted)} site(s) annotated; {len(bad)} unconverted")
    if args.list:
        for row in fsums:
            print(f"  fsum      {row['file']}:{row['line']}  {row['code'][:90]}")
        for row in noted:
            print(f"  annotated {row['file']}:{row['line']}  {row['why']}")

    fail = []
    for row in bad:
        fail.append(f"{row['file']}:{row['line']} rounds a bare sum() — "
                    f"use math.fsum, or say why the boundary cannot be reached with "
                    f"`{ALLOW} <why>`\n      {row.get('code', row.get('why', ''))}")

    figures = measured_figures()
    near = []
    for row in figures:
        if args.list:
            print(f"  margin    {row['figure']} = {row['value']} "
                  f"({row['margin']:.3e} of a rounding step from the boundary, "
                  f"{row['n']} summand(s))")
        if row["margin"] <= NEAR_BOUNDARY:
            near.append(f"{row['figure']} = {row['value']} sits {row['margin']:.2e} of "
                        f"a rounding step from the {row['nd']} dp boundary over "
                        f"{row['n']} summand(s) — its last digit is inside the drift a "
                        f"bare sum() would have, so it must stay summed exactly")
        if row["committed"] is not None and row["committed"] != row["value"]:
            fail.append(f"{row['figure']} re-adds to {row['value']} but the committed "
                        f"file carries {row['committed']}")
    print(f"{len(figures)} committed aggregate(s) re-added exactly; "
          f"{len(near)} within {NEAR_BOUNDARY:g} of a rounding boundary")
    for line in near:
        print(f"  NEAR BOUNDARY  {line}")

    fail += mutation()

    for line in fail:
        print(f"  FAIL  {line}")
    return 1 if fail else 0


def self_test() -> int:
    """The gate's own arithmetic, on cases whose answers are known independently."""
    bad = []
    if margin(0.885, 2) > 1e-15:
        bad.append("0.885 is exactly on the 2 dp boundary and should measure ~0")
    if not 0.49 < margin(0.880, 2) <= 0.5:
        bad.append("0.880 is as far from a 2 dp boundary as a figure gets")
    if margin(888.695, 2) > 1e-12:
        bad.append("888.695 — the centroid that flapped — is on the 2 dp boundary")

    src = ("import math\n"
           "a = round(sum(xs) / len(xs), 2)\n"
           "b = round(math.fsum(xs) / len(xs), 2)\n"
           "c = round(  # exact-sum-ok: counts, not measurements\n"
           "    sum(1 for x in xs), 2)\n")
    walk = _Census(src)
    walk.visit(ast.parse(src))
    if len(walk.sites) != 2:
        bad.append(f"the census should see the two bare sum() sites, saw {walk.sites}")
    if _annotated(src.splitlines(), 5) != "counts, not measurements":
        bad.append("the annotation is not read from the line above the sum()")
    if _annotated(src.splitlines(), 2) is not None:
        bad.append("an unannotated site is reading somebody else's note")

    for line in bad:
        print(f"  FAIL  {line}")
    print(f"exact-sum gate self-test: {len(bad)} failure(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
