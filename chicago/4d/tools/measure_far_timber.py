#!/usr/bin/env python3
"""measure_far_timber.py — does a body of timber stand in the river?

ROADMAP R-BUG5. The owner sent a screenshot from 31 ft up, bearing 044°, of
woody plants standing on the main stem: scattered individuals, and a straight
LINE of them running out across the channel. Two gates already claimed this
could not happen — `tools/smoke_renderer.mjs` asserts *"woody vegetation never
occupies the river mask"* and *"emergent flora stays within eight metres of a
riverbank"* — and both were GREEN on that build.

**They were green because they were both asking about the near field.** The
first walks `trees.group.userData.stations`, which is written by `noteStation()`
inside the woody planter's own lattice, a 632 m square centred on the datum. The
second walks the flora instance matrices, a lattice re-centred on the camera.
Neither one has ever seen `FAR_TIMBER`, which is a different population
altogether: five bodies of timber the sources put beyond the modelled town,
authored as polylines in `renderers/web/js/trees.js` and drawn as a horizon
silhouette rather than as stems. Nothing in this project had ever asked those
polylines where they stand.

Measured, one of them stands in the river along its whole length:

| body | samples | over water | worst depth below the water surface |
|---|---|---|---|
| `main_stem_belt_east` | 20 | **20** | **3.339 m** |
| `north_branch_belt` | 1257 | 4 | 1.380 m |
| `south_branch_belt` | 1156 | 0 | — |
| `north_division_timber` | 232 | 0 | — |
| `south_branch_grove` | 672 | 0 | — |

`main_stem_belt_east` is a three-point, near-straight polyline from (326, 46) to
(396, 68). South Water Street's committed centreline is at n ≈ +7 across that
reach and North Water Street's at n ≈ +66, so the belt was authored between the
two banks — in the channel — by a body whose own note says it follows South
Water Street. That is the LINE in the screenshot; the horizon solver's gap
modulation breaks the rest of the run into separate crowns, which is the
scatter. **One cause, both populations.**

WHAT THIS ASKS, and why the data half is a ratchet
--------------------------------------------------
Every FAR_TIMBER polyline, sampled every 2 m — finer than the renderer's own
adaptive emission step, which is never under 16 m, so this gate is strictly
harder to pass than the band is to draw. A sample inside the modelled
heightfield whose ground is below the shore threshold is a body of timber
standing in water.

Outside the modelled field the mask cannot answer — `terrain.js` returns its
fallback height there — so those samples are reported as `unmodelled` and
counted as neither. Four of the five bodies run kilometres past the box, and a
gate that called that ground dry would be inventing a survey it does not have.

The RENDERER half is absolute: `solveHorizon()` now refuses to emit a sample the
mask calls water, so nothing draws in the channel whatever the table says, and
this file asserts that clip is still there. The DATA half is a ratchet, banked by
name in `far_timber_baseline.json`: an offender may shrink and may not grow, a
new one fails, and a repair the baseline was not told about fails too.

THE SOUTH WATER BELT IS REPAIRED — T-0031, 2026-08-27, and the ratchet is what
made the repair provable. This file used to argue that `main_stem_belt_east`
could not be re-placed, because where the belt's near edge ran is a PLACEMENT
claim no source here settles. The owner ruled instead: derive it from the
committed `south_water` centreline, and record the side of the street as a
liberty. `tools/derive_timber_belt.py` does exactly that and `tools/check.sh`
re-derives it, so the belt cannot drift from the street it is cut from. The
census went **39 of 39 samples over water, 3.347 m deep → 0 of 136**, and the
body left the baseline by the ratchet's own third rule. `north_branch_belt` is
still banked at 8: it crosses the North Branch between two dry ends, which is a
belt doing what belts do, and the renderer clips the crossing.

It also scans `renderers/web/js/trees.js` for the runtime clip itself. The data
being clean and the solver consulting the mask are two different claims, and
R-BUG5 is the fourth time on this project that a green gate and the owner's
screen have disagreed — every previous time because the gate was pointed at
something other than what ships.

    tools/measure_far_timber.py            the census
    tools/measure_far_timber.py --gate     the census, and fail on any of it
    tools/measure_far_timber.py --self-test   break each assertion, in memory
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from heightfield import Heightfield  # noqa: E402
import measure_layer_reads as k42  # noqa: E402

TREES_JS = ROOT / "renderers" / "web" / "js" / "trees.js"
TERRAIN_JS = ROOT / "renderers" / "web" / "js" / "terrain.js"
SCENE_JSON = ROOT / "data" / "scenes" / "1835.json"
EPOCHS = ROOT / "data" / "terrain" / "epochs"

# Finer than the renderer can emit. `solveHorizon()` steps
# `max(16, distance * 0.030)` metres along a body, so a 2 m census cannot miss a
# reach the band can draw into.
SAMPLE_STEP_M = 2.0


class Fault(Exception):
    """An assertion this file makes about the town."""


# --- reading the renderer's own table ------------------------------------- #

def _ring_path(e: float, n: float, radius: float, steps: int) -> list[list[float]]:
    """`ringPath()` from trees.js, which authors the one closed-ring body.

    Replicated rather than approximated: a grove whose outline is its silhouette
    is exactly as capable of lying in water as a belt is, and sampling only its
    four authored arguments would ask nothing about the ring between them.
    """
    return [
        [e + math.cos(i / steps * math.pi * 2) * radius,
         n + math.sin(i / steps * math.pi * 2) * radius]
        for i in range(steps + 1)
    ]


def _bracketed(block: str, opener: str) -> str | None:
    """The text inside the `[ … ]` an `opener` pattern opens.

    A non-greedy regex is wrong here and quietly so: the first `],` inside a
    `path:` array closes its FIRST POINT, so `south_branch_belt` reads as one
    coordinate pair and a nine-point belt censuses as nothing. Brackets are
    counted instead.
    """
    m = re.search(opener, block)
    if not m:
        return None
    depth = 0
    for i in range(m.end() - 1, len(block)):
        if block[i] == "[":
            depth += 1
        elif block[i] == "]":
            depth -= 1
            if depth == 0:
                return block[m.end():i]
    return None


def _blocks(body_src: str) -> list[str]:
    """Split the array body into its top-level `{ ... }` object literals."""
    out = []
    depth = 0
    start = None
    for i, ch in enumerate(body_src):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                out.append(body_src[start:i + 1])
                start = None
    return out


def read_far_timber(src: str) -> list[dict]:
    """The FAR_TIMBER table, as `{id, path}` with every path resolved."""
    m = re.search(r"const FAR_TIMBER\s*=\s*\[(.*?)\n\];", src, re.S)
    if not m:
        raise Fault("trees.js no longer declares `const FAR_TIMBER = [ … ];` — this "
                    "gate reads the renderer's own table and cannot find it")
    bodies = []
    for block in _blocks(m.group(1)):
        idm = re.search(r"\bid:\s*'([^']+)'", block)
        if not idm:
            raise Fault(f"a FAR_TIMBER entry carries no id:\n{block[:200]}")
        ident = idm.group(1)
        ring = re.search(r"path:\s*ringPath\(([^)]*)\)", block)
        if ring:
            args = [float(a) for a in ring.group(1).split(",")]
            path = _ring_path(args[0], args[1], args[2], int(args[3]))
        else:
            lit = _bracketed(block, r"path:\s*\[")
            if lit is None:
                raise Fault(f"FAR_TIMBER.{ident} has no readable `path`")
            path = [[float(a), float(b)] for a, b in
                    re.findall(r"\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\]", lit)]
        if len(path) < 2:
            raise Fault(f"FAR_TIMBER.{ident} has fewer than two points")
        bodies.append({"id": ident, "path": path})
    if not bodies:
        raise Fault("FAR_TIMBER parsed as empty")
    return bodies


def read_shore_y(trees_src: str, terrain_src: str) -> float:
    """The waterline the mask actually uses, read from `terrain.js`.

    trees.js keeps its own copy of the constant. Both are read and they must
    agree: a renderer carrying two waterlines is how the drawn surface and the
    sampled one stop being the same surface, which is the R-BUG3c class of
    fault this project has already paid for once.
    """
    def one(src: str, where: str) -> float:
        m = re.search(r"const SHORE_Y\s*=\s*(-?[\d.]+);", src)
        if not m:
            raise Fault(f"{where} no longer declares SHORE_Y")
        return float(m.group(1))
    a = one(terrain_src, "terrain.js")
    b = one(trees_src, "trees.js")
    if abs(a - b) > 1e-9:
        raise Fault(f"terrain.js SHORE_Y {a} and trees.js SHORE_Y {b} disagree — "
                    "the mask and the planter are answering about two waterlines")
    return a


def renderer_consults_the_mask(src: str) -> None:
    """The solver's own clip, scanned rather than assumed.

    The data being clean does not mean the band refuses water; a future body
    authored a metre into the channel has to be refused by the renderer, not by
    the reviewer of the commit that adds it.
    """
    stripped = k42.strip_js_comments(src)
    solver = re.search(r"function solveHorizon\(.*?\n  \}", stripped, re.S)
    if not solver:
        raise Fault("trees.js no longer declares `function solveHorizon(` — the "
                    "horizon solver is where the water clip lives")
    if not re.search(r"terrain\.isWater\(\s*pe\s*,\s*pn\s*\)", solver.group(0)):
        raise Fault("solveHorizon() no longer asks `terrain.isWater(pe, pn)` — a "
                    "body of far timber may be emitted into the channel again "
                    "(ROADMAP R-BUG5)")


# --- the census ------------------------------------------------------------ #

def census(bodies: list[dict], hf: Heightfield, shore_y: float) -> list[dict]:
    rows = []
    for body in bodies:
        path = body["path"]
        samples = wet = unmodelled = 0
        worst = 0.0
        wet_length = 0.0
        total_length = 0.0
        # Each sample owns the sub-interval that STARTS at it, and the path's
        # final point owns nothing. Sampling both ends of every sub-interval
        # instead double-counts each shared vertex, which reported a wet run of
        # 77.3 m on a body 73.4 m long — a census that outruns its own subject
        # is not one anybody should quote.
        points: list[tuple[float, float, float]] = []
        for s in range(len(path) - 1):
            ax, ay = path[s]
            bx, by = path[s + 1]
            seg = math.hypot(bx - ax, by - ay)
            total_length += seg
            steps = max(1, int(math.ceil(seg / SAMPLE_STEP_M)))
            for k in range(steps):
                f = k / steps
                points.append((ax + (bx - ax) * f, ay + (by - ay) * f, seg / steps))
        points.append((path[-1][0], path[-1][1], 0.0))
        for e, n, owns in points:
            samples += 1
            if not hf.covers(e, n):
                unmodelled += 1
                continue
            y = hf.height(e, n)
            if y < shore_y:
                wet += 1
                wet_length += owns
                worst = min(worst, y)
        rows.append({
            "id": body["id"],
            "samples": samples,
            "wet": wet,
            "unmodelled": unmodelled,
            "worst_depth_m": round(-worst, 3) if wet else None,
            "length_m": round(total_length, 1),
            "wet_length_m": round(wet_length, 1),
        })
    return rows


def report(rows: list[dict]) -> None:
    print("  far timber, sampled every "
          f"{SAMPLE_STEP_M:g} m against the committed heightfield")
    print(f"  {'body':<24} {'samples':>8} {'in water':>9} {'unmodelled':>11} "
          f"{'worst depth':>12} {'wet run':>9}")
    for r in rows:
        depth = "—" if r["worst_depth_m"] is None else f"{r['worst_depth_m']:.3f} m"
        print(f"  {r['id']:<24} {r['samples']:>8} {r['wet']:>9} {r['unmodelled']:>11} "
              f"{depth:>12} {r['wet_length_m']:>7.1f} m")
    total = sum(r["wet"] for r in rows)
    print(f"  {'':<24} {'':>8} {total:>9}   "
          f"({sum(r['unmodelled'] for r in rows)} samples lie outside the modelled "
          "field, where the mask cannot answer)")


BASELINE = ROOT / "tools" / "far_timber_baseline.json"


def load_baseline() -> dict:
    if not BASELINE.exists():
        return {}
    return json.loads(BASELINE.read_text(encoding="utf-8")).get("bodies", {})


def gate(rows: list[dict]) -> int:
    banked = load_baseline()
    offenders = [r for r in rows if r["wet"]]
    faults = []
    for r in offenders:
        allowed = banked.get(r["id"], {}).get("wet")
        if allowed is None:
            faults.append(f"{r['id']} is NEW: {r['wet']} of {r['samples']} samples over "
                          f"water, {r['wet_length_m']:.1f} m of {r['length_m']:.1f} m, "
                          f"worst {r['worst_depth_m']:.3f} m below the water surface")
        elif r["wet"] > allowed:
            faults.append(f"{r['id']} got WORSE: {r['wet']} samples over water against "
                          f"{allowed} banked")
    seen = {r["id"] for r in offenders}
    for ident, entry in banked.items():
        if ident not in seen:
            faults.append(f"{ident} is banked at {entry['wet']} samples over water and "
                          "now has none — drop it from far_timber_baseline.json in the "
                          "commit that repaired it (--update)")
    if faults:
        print("  FAIL — the far-timber census disagrees with what is banked "
              "(ROADMAP R-BUG5)")
        for f in faults:
            print(f"    {f}")
        return 1
    if offenders:
        print(f"  PASS (ratchet) — {sum(r['wet'] for r in offenders)} samples over water "
              f"across {len(offenders)} banked bodies, none new and none worse; the "
              "renderer clip keeps every one of them off the screen")
    else:
        print("  PASS — no body of far timber stands in water inside the modelled field")
    return 0


def write_baseline(rows: list[dict], epoch: str) -> None:
    bodies = {
        r["id"]: {"wet": r["wet"], "samples": r["samples"],
                  "wet_length_m": r["wet_length_m"],
                  "worst_depth_m": r["worst_depth_m"]}
        for r in rows if r["wet"]
    }
    BASELINE.write_text(json.dumps({
        "_doc": "ROADMAP R-BUG5. Bodies of far timber whose authored polyline crosses "
                "water inside the modelled heightfield, banked by name so the fault may "
                "shrink and may not grow. Written by tools/measure_far_timber.py "
                "--update; the renderer refuses to draw any of it, so nothing banked "
                "here is on screen. main_stem_belt_east left this file in T-0031, "
                "re-placed on the committed South Water centreline: 39 of 39 samples "
                "over water became 0 of 136.",
        "epoch": epoch,
        "sample_step_m": SAMPLE_STEP_M,
        "bodies": bodies,
    }, indent=1) + "\n", encoding="utf-8")
    print(f"  wrote {BASELINE.relative_to(ROOT)} — {len(bodies)} banked bodies")


# --- self-test -------------------------------------------------------------- #

def self_test(hf: Heightfield, shore_y: float, trees_src: str) -> int:
    """Break each assertion in memory and require it to fire."""
    failures = []

    def expect_fault(label, fn):
        try:
            fn()
        except Fault:
            print(f"  fires: {label}")
            return
        failures.append(label)
        print(f"  SELF-TEST FAIL: {label} did not fire")

    # 1. a body laid across the main stem must be caught.
    planted = [{"id": "synthetic", "path": [[326.0, 46.0], [396.0, 68.0]]}]
    rows = census(planted, hf, shore_y)
    if rows[0]["wet"] == rows[0]["samples"] and rows[0]["samples"] > 1:
        print("  fires: a polyline laid down the channel counts every sample wet")
    else:
        failures.append("channel polyline")
        print(f"  SELF-TEST FAIL: a channel polyline censused {rows[0]}")

    # 2. ...and dry ground must NOT be caught, or the gate means nothing.
    dry = [{"id": "synthetic-dry", "path": [[-60.0, 352.0], [130.0, 358.0]]}]
    rows = census(dry, hf, shore_y)
    if rows[0]["wet"] == 0:
        print("  fires: the North Side timber's own ground censuses dry")
    else:
        failures.append("dry control")
        print(f"  SELF-TEST FAIL: dry ground censused {rows[0]}")

    # 3. the renderer clip, removed.
    expect_fault("solveHorizon without the water clip",
                 lambda: renderer_consults_the_mask(
                     trees_src.replace("terrain.isWater(pe, pn)", "false")))

    # 4. the table, renamed.
    expect_fault("FAR_TIMBER renamed out from under the gate",
                 lambda: read_far_timber(trees_src.replace("const FAR_TIMBER", "const X")))

    # 5. two disagreeing waterlines.
    expect_fault("trees.js and terrain.js carrying different waterlines",
                 lambda: read_shore_y(trees_src.replace("const SHORE_Y = -0.10;",
                                                        "const SHORE_Y = -0.40;"),
                                      TERRAIN_JS.read_text(encoding="utf-8")))

    # 6. the ratchet, in all three directions. A banked fault that grows, a body
    #    nobody banked, and a repair left unrecorded must each fail — the last
    #    one because a stale baseline is how a gate stops meaning anything.
    banked = load_baseline()
    if not banked:
        failures.append("empty baseline")
        print("  SELF-TEST FAIL: far_timber_baseline.json banks nothing to ratchet")
    else:
        ident = next(iter(banked))
        real = [{"id": i, "samples": e["samples"], "wet": e["wet"], "unmodelled": 0,
                 "worst_depth_m": e["worst_depth_m"], "length_m": 1.0,
                 "wet_length_m": e["wet_length_m"]} for i, e in banked.items()]
        if gate(real) != 0:
            failures.append("clean ratchet")
            print("  SELF-TEST FAIL: the banked census does not pass its own ratchet")
        worse = [dict(r, wet=r["wet"] + 1) if r["id"] == ident else r for r in real]
        if gate(worse) == 0:
            failures.append("growing fault")
            print("  SELF-TEST FAIL: a banked body that got worse passed")
        else:
            print("  fires: a banked body whose fault grew")
        novel = real + [{"id": "unbanked", "samples": 9, "wet": 9, "unmodelled": 0,
                         "worst_depth_m": 1.0, "length_m": 9.0, "wet_length_m": 9.0}]
        if gate(novel) == 0:
            failures.append("new offender")
            print("  SELF-TEST FAIL: an unbanked body standing in water passed")
        else:
            print("  fires: a body standing in water that nobody banked")
        repaired = [r for r in real if r["id"] != ident]
        if gate(repaired) == 0:
            failures.append("stale baseline")
            print("  SELF-TEST FAIL: a repaired body left in the baseline passed")
        else:
            print("  fires: a repair the baseline was not told about")

    if failures:
        print(f"  SELF-TEST FAILED: {len(failures)} assertion(s) did not fire")
        return 1
    print("  self-test: every assertion fires when broken")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gate", action="store_true", help="fail on any timber in water")
    ap.add_argument("--self-test", action="store_true", help="break each assertion")
    ap.add_argument("--json", action="store_true", help="machine-readable census")
    ap.add_argument("--update", action="store_true", help="re-bank the census")
    args = ap.parse_args()

    trees_src = TREES_JS.read_text(encoding="utf-8")
    terrain_src = TERRAIN_JS.read_text(encoding="utf-8")
    shore_y = read_shore_y(trees_src, terrain_src)

    epoch = json.loads(SCENE_JSON.read_text(encoding="utf-8"))["terrain_epoch"]
    hf = Heightfield.load(EPOCHS / epoch)
    if hf is None:
        print(f"  heightfield for {epoch} is not readable — nothing measured")
        return 1

    if args.self_test:
        return self_test(hf, shore_y, trees_src)

    renderer_consults_the_mask(trees_src)
    rows = census(read_far_timber(trees_src), hf, shore_y)
    if args.json:
        print(json.dumps({"epoch": epoch, "shore_y": shore_y, "bodies": rows}, indent=1))
        return 0
    report(rows)
    if args.update:
        write_baseline(rows, epoch)
        return 0
    return gate(rows) if args.gate else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Fault as exc:
        print(f"  FAIL — {exc}")
        sys.exit(1)
