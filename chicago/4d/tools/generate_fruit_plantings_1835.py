#!/usr/bin/env python3
"""Generate the 1835 fruit plantings: the fort's company gardens and Dr. Harmon's orchard (T-2809).

WHAT IS STATED, verbatim, by one witness who rode past both in the spring of 1831.
Juliette Kinzie, *Wau-Bun* (1856), source record `kinzie_waubun_1856`:

    "Beyond the parade-ground which extended south of the pickets, were the company
     gardens, well filled with currant-bushes and young fruit-trees."

    "When we chose the path across the prairie towards the south, we generally passed
     Dr. Harmon, superintending the construction of a sod fence, at a spot he had
     chosen, near the shore of the lake. In this inclosure he occupied himself, as the
     season advanced, in planting fruit stones of all descriptions, to make ready a
     garden and orchard for future enjoyment."

Andreas (1884, vol. 1, the medical chapter) gives Harmon a pre-emption of 140 acres
"the northern boundary of which was in the vicinity of Sixteenth Street".

THE COMPANY GARDENS are a committed structure, fort_dearborn_garrison_garden: the
1830 Harrison plan's "Garden for the Garrison", a 77 m square worm-fenced plot whose
record says its planting is attested and "NOTHING OF THE PLANTING IS BUILT". This file
builds it, inside that footprint and in the garden's own frame:

  * YOUNG FRUIT TREES in a border row ROW_INSET_M inside each fence, TREE_STEP_M
    apart: apple, with one in three a sour cherry. Neither fruit is named; apple is
    the frontier's orchard tree and cherry the hardiest stone fruit.
  * CURRANT BUSHES in BUSH_ROWS long rows running the length of the plot between its
    vegetable beds, BUSH_STEP_M apart in the row, a bush now and then missing. A
    working garden of long parallel beds, not a laid-out four-square: nothing records
    the plot's plan, and the owner read the first cut's cross walk as a monument
    (2026-10-19). The beds are not drawn.
  * The rest of the plot is the vegetable ground, which no layer draws.

DR. HARMON'S ORCHARD has no record of a place beyond "near the shore of the lake" on
the prairie south of the fort, and his claim's north line near Sixteenth Street. So
it is set inside that claim just south of the Sixteenth Street line, west of Robert
Clarke's shore cottonwood grove (shore_cottonwood_grove_1835) with GROVE_CLEAR_M
between them: a ORCHARD_E x ORCHARD_N plot of seedlings four seasons from the stone,
peach with two in five a sour cherry, in rows. The sod fence round it is not drawn:
the enclosure layer has no turf bank (left open on T-2767).

Every stem is asked the planting loop's own refusals (generate_fort_trees.refusal) so
none is stated that trees.js would decline, the garden's own footprint excepted for
its own stems (`in_structure`). Heights fall inside the z10 species' recorded bands.

    python3 tools/generate_fruit_plantings_1835.py            write both records
    python3 tools/generate_fruit_plantings_1835.py --check    re-derive and diff
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_fort_trees as gft  # noqa: E402  (its refusals and the committed world)

ROOT = Path(__file__).resolve().parent.parent
PLANTINGS = ROOT / "data/flora/plantings"
ZONE = ROOT / "data/flora/zones/z10_settled_town.json"
GARDEN_ID = "fort_dearborn_garrison_garden"
GARDEN_OUT = PLANTINGS / "fort_company_garden_1835.json"
HARMON_OUT = PLANTINGS / "harmon_orchard_1835.json"
GROVE = PLANTINGS / "shore_cottonwood_grove_1835.json"

# The company gardens, in the garden's own (u, v) frame, metres from its corner.
ROW_INSET_M = 4.0
TREE_STEP_M = 7.0
BUSH_STEP_M = 1.8
BUSH_ROWS = 4
BUSH_END_M = 10.0
BUSH_JITTER_M = 0.3
BUSH_GAP = 0.06
APPLE_H = (3.5, 5.5)
CHERRY_H = (3.0, 5.0)
BUSH_H = (0.9, 1.4)

# Dr. Harmon's orchard, in local ENU.
N_SIXTEENTH = -2949.59
SOUTH_OF_LINE_M = 12.0
ORCHARD_E = 48.0
ORCHARD_N = 44.0
GROVE_CLEAR_M = 20.0
SOD_M = 1.5
ORCH_INSET_M = 3.0
ORCH_STEP_E = 5.25
ORCH_STEP_N = 5.4
PEACH_H = (2.2, 3.8)
SEEDLING_CHERRY_H = (2.0, 3.4)

SEED = 2809


def height(rnd: random.Random, band: tuple[float, float]) -> float:
    return round(band[0] + rnd.random() * (band[1] - band[0]), 1)


def check_bands(stems: list[dict], zone: dict) -> None:
    bands = {sp["id"]: sp["height_m"] for sp in zone["species"]}
    for s in stems:
        lo, hi = bands[s["species"]]
        if not lo <= s["height_m"] <= hi:
            raise SystemExit(f"{s['id']}: {s['height_m']} m is outside {s['species']}'s "
                             f"recorded {lo}-{hi} m")


def refuse_all(stems, world, skip_fp=None):
    obstructions, streets, fences, aprons, hulls, hf, taken = world
    obs = [o for o in obstructions if o is not skip_fp and o != skip_fp]
    for s in stems:
        why = gft.refusal(tuple(s["at_local_enu_m"]), obs, streets, fences, aprons, hulls, hf, [])
        if why:
            raise SystemExit(f"generate_fruit_plantings_1835: {s['id']} is {why}")


def garden_stems(rnd: random.Random) -> list[dict]:
    sc = gft.load(gft.SIDECARS / f"{GARDEN_ID}.json")
    poly = sc["footprint"]["polygon"]
    side = max(u for u, _ in poly)
    pl = sc["placement"]
    th = math.radians(pl["rotation_deg"])
    c, s = math.cos(th), math.sin(th)

    def at(u: float, v: float) -> list[float]:
        return [round(pl["local_e"] + u * c + v * s, 1), round(pl["local_n"] - u * s + v * c, 1)]

    stems: list[dict] = []
    # The border row: along v = inset and v = side - inset the full run; along the
    # two u sides the run is shortened by one step so the corner trees are not doubled.
    count = int((side - 2 * ROW_INSET_M) // TREE_STEP_M) + 1
    first = (side - (count - 1) * TREE_STEP_M) / 2
    run = [first + k * TREE_STEP_M for k in range(count)]
    places = ([(x, ROW_INSET_M) for x in run] + [(x, side - ROW_INSET_M) for x in run]
              + [(ROW_INSET_M, y) for y in run[1:-1]] + [(side - ROW_INSET_M, y) for y in run[1:-1]])
    for k, (u, v) in enumerate(places, 1):
        cherry = rnd.random() < 1 / 3
        sp = "prunus_cerasus" if cherry else "malus_domestica"
        stems.append({
            "id": f"garden_fruit_{k}", "species": sp, "at_local_enu_m": at(u, v),
            "height_m": height(rnd, CHERRY_H if cherry else APPLE_H),
            "confidence": "reconstructed",
            "note": (f"YOUNG FRUIT TREE {k} of the border row, {ROW_INSET_M:.0f} m inside the "
                     f"garden's fence at {TREE_STEP_M:.0f} m spacing (garden frame u {u:.1f}, "
                     f"v {v:.1f}). Kinzie's 'young fruit-trees' are attested; the row, the "
                     f"spacing and the species ({'sour cherry' if cherry else 'apple'}) are "
                     "this record's."),
        })
    # The currants: long rows between the beds, evenly across the plot inside the
    # border row, running the plot's length (along u).
    lo, hi = ROW_INSET_M + 6.0, side - ROW_INSET_M - 6.0
    rows_v = [lo + r * (hi - lo) / (BUSH_ROWS - 1) for r in range(BUSH_ROWS)]
    k = 0
    for r, v0 in enumerate(rows_v, 1):
        t = BUSH_END_M
        while t <= side - BUSH_END_M + 1e-9:
            u = t + (rnd.random() - 0.5) * BUSH_JITTER_M
            v = v0 + (rnd.random() - 0.5) * BUSH_JITTER_M
            gone = rnd.random() < BUSH_GAP
            h = height(rnd, BUSH_H)
            t += BUSH_STEP_M
            if gone:
                continue
            k += 1
            stems.append({
                "id": f"garden_currant_{k}", "species": "ribes_spp", "at_local_enu_m": at(u, v),
                "height_m": h,
                "confidence": "reconstructed",
                "note": (f"CURRANT BUSH in row {r} of {BUSH_ROWS}, the rows running the plot's "
                         f"length between its vegetable beds, {BUSH_STEP_M} m apart. Kinzie's "
                         "'currant-bushes' are attested; the rows and their places are this "
                         "record's."),
            })
    return stems


def harmon_stems(rnd: random.Random) -> tuple[list[dict], dict]:
    grove = json.loads(GROVE.read_text())
    north = N_SIXTEENTH - SOUTH_OF_LINE_M
    south = north - ORCHARD_N
    near = [s["at_local_enu_m"] for s in grove["stems"]
            if south - GROVE_CLEAR_M <= s["at_local_enu_m"][1] <= north + GROVE_CLEAR_M]
    east = round(min(e for e, _ in near) - GROVE_CLEAR_M, 1)
    west = round(east - ORCHARD_E, 1)
    plot = {"west_e": west, "east_e": east, "north_n": round(north, 2), "south_n": round(south, 2)}
    cols = int((ORCHARD_E - 2 * ORCH_INSET_M) // ORCH_STEP_E) + 1
    rows = int((ORCHARD_N - 2 * ORCH_INSET_M) // ORCH_STEP_N) + 1
    stems: list[dict] = []
    k = 0
    for r in range(rows):
        for q in range(cols):
            k += 1
            e = west + ORCH_INSET_M + q * ORCH_STEP_E + (rnd.random() - 0.5) * 0.6
            n = north - ORCH_INSET_M - r * ORCH_STEP_N + (rnd.random() - 0.5) * 0.6
            cherry = rnd.random() < 0.4
            sp = "prunus_cerasus" if cherry else "prunus_persica"
            stems.append({
                "id": f"harmon_seedling_{k}", "species": sp,
                "at_local_enu_m": [round(e, 1), round(n, 1)],
                "height_m": height(rnd, SEEDLING_CHERRY_H if cherry else PEACH_H),
                "confidence": "reconstructed",
                "note": (f"SEEDLING {k}, row {r + 1} of {rows}, of a {'sour cherry' if cherry else 'peach'} "
                         "four seasons from the stone Harmon planted in 1831. The orchard and its "
                         "fruit stones are Kinzie's; the plot's place, its rows and the species "
                         "are this record's."),
            })
    return stems, plot


def garden_record(stems: list[dict]) -> dict:
    return {
        "_doc": ("A PLANTING RECORD for the 1835 scene (T-2809), read by renderers/web/js/trees.js "
                 "through data/flora/index.json. GENERATED by tools/generate_fruit_plantings_1835.py, "
                 "which re-derives it byte for byte in tools/check.sh. Do not hand-edit."),
        "id": "fort_company_garden_1835",
        "name": "The fort's company gardens: young fruit trees and currant bushes",
        "kind": "planting",
        "scene": "1835",
        "target_date": "1835-07-01",
        "generated_by": "tools/generate_fruit_plantings_1835.py",
        "belongs_to": [GARDEN_ID],
        "in_structure": GARDEN_ID,
        "zone": "z10_settled_town",
        "existence": {
            "value": True,
            "confidence": "attested",
            "sources": ["kinzie_waubun_1856"],
            "note": ("Juliette Kinzie, of the fort she lived beside in 1831: 'Beyond the parade-ground "
                     "which extended south of the pickets, were the company gardens, well filled with "
                     "currant-bushes and young fruit-trees.' The planting is attested as the garden "
                     "record's own `planting` field says; the garden stands to the end of 1836. Every "
                     "position, the species of the trees and the number of each are reconstructed."),
        },
        "rule": {
            "row_inset_m": ROW_INSET_M, "tree_step_m": TREE_STEP_M, "bush_step_m": BUSH_STEP_M,
            "bush_rows": BUSH_ROWS, "bush_end_m": BUSH_END_M, "bush_gap": BUSH_GAP,
            "apple_h_m": list(APPLE_H), "cherry_h_m": list(CHERRY_H), "bush_h_m": list(BUSH_H),
            "seed": SEED,
        },
        "stems": stems,
        "research_note": ("WHY in_structure: the garden is a committed footprint (its fence's), and the "
                          "planting loop keeps every stem out of every footprint; this record's stems are "
                          "let past that one polygon only. docs/LIBERTIES.md L-fruit-trees-1835-2809."),
    }


def harmon_record(stems: list[dict], plot: dict) -> dict:
    return {
        "_doc": ("A PLANTING RECORD for the 1835 scene (T-2809), read by renderers/web/js/trees.js "
                 "through data/flora/index.json. GENERATED by tools/generate_fruit_plantings_1835.py, "
                 "which re-derives it byte for byte in tools/check.sh. Do not hand-edit."),
        "id": "harmon_orchard_1835",
        "name": "Dr. Harmon's young orchard by the lake",
        "kind": "planting",
        "scene": "1835",
        "target_date": "1835-07-01",
        "generated_by": "tools/generate_fruit_plantings_1835.py",
        "zone": "z10_settled_town",
        "existence": {
            "value": True,
            "confidence": "inferred",
            "sources": ["kinzie_waubun_1856"],
            "note": ("Kinzie, spring 1831: Dr. Harmon 'superintending the construction of a sod fence, "
                     "at a spot he had chosen, near the shore of the lake. In this inclosure he occupied "
                     "himself ... in planting fruit stones of all descriptions, to make ready a garden and "
                     "orchard'. That it still stands in 1835, four seasons on, is inferred. Andreas (1884, vol. 1) gives his 140-acre claim a "
                     "north line near Sixteenth Street, which is why the plot is just south of that line. "
                     "The sod fence is not drawn."),
        },
        "clears_local_enu_m": {"west_e": round(plot["west_e"] - SOD_M, 1),
                               "east_e": round(plot["east_e"] + SOD_M, 1),
                               "north_n": round(plot["north_n"] + SOD_M, 2),
                               "south_n": round(plot["south_n"] - SOD_M, 2),
                               "note": ("The plot and its sod fence, kept clear of the sand hills' "
                                        "dealt cedar, pine and shrubs: a fenced orchard is ground "
                                        "somebody cleared (trees.js inClearedPlot).")},
        "rule": {
            "plot_local_enu_m": plot, "inset_m": ORCH_INSET_M,
            "step_e_m": ORCH_STEP_E, "step_n_m": ORCH_STEP_N, "grove_clear_m": GROVE_CLEAR_M,
            "peach_h_m": list(PEACH_H), "cherry_h_m": list(SEEDLING_CHERRY_H), "seed": SEED,
        },
        "stems": stems,
        "research_note": ("The plot's place is reconstructed: inside Harmon's claim, south of the "
                          "Sixteenth Street line, west of Clarke's shore grove (docs/LIBERTIES.md "
                          "L-fruit-trees-1835-2809). WHAT WOULD MOVE IT: the 1830s pre-emption entry or "
                          "a plat of the claim, or any later account that sites Harmon's garden."),
    }


def build() -> tuple[dict, dict]:
    zone = json.loads(ZONE.read_text())
    world = gft.world()
    sc = gft.load(gft.SIDECARS / f"{GARDEN_ID}.json")
    garden_fp = gft.footprint_world(sc)
    g = garden_stems(random.Random(SEED))
    h, plot = harmon_stems(random.Random(SEED + 1))
    check_bands(g + h, zone)
    refuse_all(g, world, skip_fp=garden_fp)
    refuse_all(h, world)
    return garden_record(g), harmon_record(h, plot)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="re-derive both records and fail if a committed file differs")
    args = ap.parse_args()
    bad = 0
    for path, rec in zip((GARDEN_OUT, HARMON_OUT), build()):
        text = json.dumps(rec, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            have = path.read_text() if path.exists() else ""
            if have != text:
                print(f"generate_fruit_plantings_1835: {path.relative_to(ROOT)} does not re-derive; "
                      "run tools/generate_fruit_plantings_1835.py and commit the result")
                bad = 1
            else:
                print(f"generate_fruit_plantings_1835: {len(rec['stems'])} stems in "
                      f"{path.name} re-derive")
        else:
            path.write_text(text)
            print(f"generate_fruit_plantings_1835: wrote {len(rec['stems'])} stems to "
                  f"{path.relative_to(ROOT)}")
    return bad


if __name__ == "__main__":
    sys.exit(main())
