#!/usr/bin/env python3
"""Generate the 1835 shore cottonwood grove at Sixteenth to Eighteenth Street (T-2766).

WHAT IS STATED, verbatim, by a man who grew up under it. Robert G. Clarke, letter
of 15 March 1890, printed in Kirkland, *The Chicago Massacre of 1812* (1893),
Appendix K, pp. 209-210 (source record `kirkland_1893_chicago_massacre_appendix_k`):

    "This was one of a grove, consisting of perhaps fifty to seventy-five large
     cottonwoods, extending from a little north of Sixteenth to a little south of
     Eighteenth Street. Almost in the center of this grove -- I think the exact
     location would be two hundred and fifty to three hundred feet north of
     Eighteenth Street, on the east end of Wirt Dexter's lot -- stood a "clump" of
     eight or nine trees."

Mary Clark Williams, through Galloway in the same appendix, played under the 18th
Street tree "nearly fifty years" before 1884, when it was "a large and thrifty
tree"; Isaac Arnold, arriving in 1836, saw "some cottonwood trees" there. So the
1835 scene has a grove of large cottonwoods on the shore south of the town, and
until this file it had none: the dune poplars stop about 400 m either side of the
river.

WHAT THIS FILE INVENTS, and it is every position but one rule's worth.

  * THE COUNT: 60, inside Clarke's "perhaps fifty to seventy-five".
  * THE NORTH-SOUTH EXTENT: Sixteenth Street's line (N -2949.59) and Eighteenth's
    (N -3206.93) are the OpenStreetMap junctions the 1835 scene's anchors already
    use (data/traces/south_anchor_control.json). "A little" beyond each is taken
    as 20 m, so the grove runs N -2929.6 to N -3226.9.
  * THE CLUMP: nine stems (the upper of "eight or nine") round a centre 275 ft
    (83.8 m, the middle of Clarke's 250-300 ft) north of the Eighteenth Street
    line, at the east end of Wirt Dexter's lot. 1721 Prairie Avenue's traced lot
    (data/traces/prairie_1904_footprints_s20.json, parcel prairie_1721) is
    78.78 m deep from a street line at E 1411.3, so its east end is E 1490.1.
    The lot is a survey of the 1850s, not of 1835, and that easting is the one
    place in this file a source gives an east-west position. It lands 22 m
    inside the 1835 bank the committed heightfield draws at that northing.
  * THE 18TH STREET TREE AND ITS FELLOW: at the two positions the 1812 scene's
    massacre_cottonwoods_1812 record already gives them, so the same two trees
    stand in the same place in both years.
  * HOW FAR BACK FROM THE WATER: no source says. The grove is held to a strip
    BAND_M deep behind the bank, measured from the easternmost point at each
    northing where the committed e1834_harbor_cut ground stands BANK_Y above the
    water. Cottonwood on this shore is a tree of the wet sand behind the beach
    (Cowles 1899, in the research dossier), so the strip hugs the bank rather
    than reaching inland onto the prairie the sources keep open.
  * EVERY OTHER STEM: dealt in that strip by a seeded dart throw at no less than
    MIN_GAP_M apart, the spacing of grown trees whose crowns meet in a grove.

THE ZONE IS z05_riverbank_timber, and that is a choice to justify. The planting
loop draws a stem from the zone its record names, and the shore's own record,
z08_lakeshore, describes the cottonwood only in its dune form, 5-15 m, leaning
and wind-cut on the beach ridge. Clarke's trees are "large" and the 18th Street
tree "large and thrifty" in 1835; z05's populus_deltoides is the full-grown
tree, 22-30 m and 60-100 cm through the trunk, and it is the only record that
describes one. Heights are dealt 22-26 m, the lower half of that band, because a
grove of trees of one generation on a sand shore is not the river's tallest
timber.

    python3 tools/generate_shore_grove_1835.py            write the record
    python3 tools/generate_shore_grove_1835.py --check    re-derive and diff
"""
from __future__ import annotations

import argparse
import array
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HF_DIR = ROOT / "data/terrain/epochs/e1834_harbor_cut"
OUT = ROOT / "data/flora/plantings/shore_cottonwood_grove_1835.json"

N_SIXTEENTH = -2949.59
N_EIGHTEENTH = -3206.93
BEYOND_M = 20.0
N_NORTH = round(N_SIXTEENTH + BEYOND_M, 2)
N_SOUTH = round(N_EIGHTEENTH - BEYOND_M, 2)

COUNT = 60
CLUMP_N = 9
FT = 0.3048
CLUMP_CENTRE = (1490.1, round(N_EIGHTEENTH + 275 * FT, 1))
CLUMP_RADIUS_M = 4.5
MASSACRE = [("eighteenth_street_tree", (1534.0, -3203.0)),
            ("eighteenth_street_fellow", (1535.0, -3211.0))]

BANK_Y = 2.0      # m above the water: the edge of the flat terrace behind the beach
BAND_M = 48.0     # how far back from that edge the grove reaches
MIN_GAP_M = 11.0
CLEAR_OF_CLUMP_M = 12.0
H_BAND = (22, 26)
SEED = 2766


class Field:
    def __init__(self) -> None:
        meta = json.loads((HF_DIR / "heightfield.json").read_text())
        raw = array.array("h")
        raw.frombytes((HF_DIR / "heightfield.bin").read_bytes())
        if sys.byteorder != "little":
            raw.byteswap()
        self.m = meta
        self.raw = raw

    def h(self, e: float, n: float) -> float:
        m = self.m
        c = (e - m["origin_e"]) / m["cell_m"]
        r = (n - m["origin_n"]) / m["cell_m"]
        c0, r0 = int(math.floor(c)), int(math.floor(r))
        fc, fr = c - c0, r - r0
        cols = m["cols"]

        def g(i: int, j: int) -> float:
            return self.raw[j * cols + i] * m["scale"] + m.get("offset", 0.0)

        top = g(c0, r0) * (1 - fc) + g(c0 + 1, r0) * fc
        bot = g(c0, r0 + 1) * (1 - fc) + g(c0 + 1, r0 + 1) * fc
        return top * (1 - fr) + bot * fr

    def bank_e(self, n: float) -> float:
        """The easternmost easting at this northing where the ground is BANK_Y up."""
        e = 1700.0 - self.m["cell_m"]
        while e > 1300.0 and self.h(e, n) < BANK_Y:
            e -= 0.5
        return e


def deal(field: Field) -> list[dict]:
    rnd = random.Random(SEED)
    stems: list[dict] = []
    taken: list[tuple[float, float]] = []

    ce, cn = CLUMP_CENTRE
    clump = [(ce, cn)] + [
        (ce + CLUMP_RADIUS_M * math.cos(2 * math.pi * k / (CLUMP_N - 1)),
         cn + CLUMP_RADIUS_M * math.sin(2 * math.pi * k / (CLUMP_N - 1)))
        for k in range(CLUMP_N - 1)]
    for k, (e, n) in enumerate(clump, 1):
        h = 24 if k == 1 else rnd.randint(22, 24)
        stems.append(stem(f"grove_clump_{k}", e, n, h,
                          f"STEM {k} OF THE {CLUMP_N} IN CLARKE'S CLUMP, \"two hundred and fifty to "
                          "three hundred feet north of Eighteenth Street, on the east end of Wirt "
                          "Dexter's lot\". The centre is 275 ft north of the Eighteenth Street line at "
                          "1721 Prairie Avenue's traced lot end, E 1490.1; the ring of eight round it "
                          f"at {CLUMP_RADIUS_M} m is this record's. Height inside z05's 22-30 m band."))
        taken.append((e, n))
    for name, (e, n) in MASSACRE:
        stems.append(stem(f"grove_{name}", e, n, 24,
                          "THE 18TH STREET TREE" if name.endswith("tree") else "ITS FELLOW",
                          ))
        taken.append((e, n))
    stems[-2]["note"] = (
        "THE 18TH STREET 'MASSACRE TREE', at the position massacre_cottonwoods_1812 gives it in "
        "the 1812 scene, so one tree stands in one place in both years. In 1835 Mary Clark "
        "Williams played under it when it was 'a large and thrifty tree' (Galloway, 1884, in "
        "Kirkland 1893 App. K); 24 m is inside z05's 22-30 m band. Position reconstructed, as in 1812.")
    stems[-1]["note"] = (
        "THE 18TH STREET TREE'S FELLOW (Mrs. King's 'with its fellow'), at the 1812 record's "
        "second position. Height 24 m, inside z05's band. Position reconstructed, as in 1812.")

    tries = 0
    while len(stems) < COUNT:
        tries += 1
        if tries > 200000:
            raise SystemExit(f"generate_shore_grove_1835: placed only {len(stems)} of {COUNT}")
        n = N_SOUTH + rnd.random() * (N_NORTH - N_SOUTH)
        edge = field.bank_e(n)
        e = edge - rnd.random() * BAND_M
        if any(math.hypot(e - a, n - b) < MIN_GAP_M for a, b in taken):
            continue
        if math.hypot(e - ce, n - cn) < CLEAR_OF_CLUMP_M:
            continue
        h = rnd.randint(*H_BAND)
        k = len(stems) - CLUMP_N - len(MASSACRE) + 1
        stems.append(stem(f"grove_{k}", e, n, h,
                          f"GROVE STEM {k}, dealt by tools/generate_shore_grove_1835.py: "
                          f"{edge - e:.1f} m back from the bank edge the committed heightfield draws "
                          f"at this northing, at least {MIN_GAP_M:.0f} m from every other stem. "
                          "The grove and its extent are Clarke's; this position is invented. "
                          "Height inside z05's 22-30 m band."))
        taken.append((e, n))
    return stems


def stem(sid: str, e: float, n: float, h: int, note: str) -> dict:
    return {"id": sid, "species": "populus_deltoides",
            "at_local_enu_m": [round(e, 1), round(n, 1)], "height_m": h,
            "confidence": "reconstructed", "note": note}


def record(stems: list[dict]) -> dict:
    return {
        "_doc": ("A PLANTING RECORD for the 1835 scene (T-2766): woody stems whose position is "
                 "stated rather than dealt from the land, read by renderers/web/js/trees.js through "
                 "data/flora/index.json and scoped there to scene 1835. GENERATED by "
                 "tools/generate_shore_grove_1835.py, which holds the rule and re-derives this file "
                 "byte for byte in tools/check.sh. Do not hand-edit."),
        "id": "shore_cottonwood_grove_1835",
        "name": "The shore cottonwood grove at Sixteenth to Eighteenth Street",
        "kind": "planting",
        "scene": "1835",
        "target_date": "1835-07-01",
        "generated_by": "tools/generate_shore_grove_1835.py",
        "zone": "z05_riverbank_timber",
        "existence": {
            "value": True,
            "confidence": "inferred",
            "sources": ["kirkland_1893_chicago_massacre_appendix_k"],
            "note": ("A RECOLLECTION, GRADED AS ONE. Robert G. Clarke, 1890, of his childhood on the "
                     "Clark farm: 'This was one of a grove, consisting of perhaps fifty to seventy-five "
                     "large cottonwoods, extending from a little north of Sixteenth to a little south of "
                     "Eighteenth Street. Almost in the center of this grove ... stood a \"clump\" of "
                     "eight or nine trees.' What he describes is the late 1830s and 1840s; Mary Clark "
                     "Williams's 'large and thrifty tree' about 1835 and Arnold's 'some cottonwood trees' "
                     "of 1836 carry it back to this scene. No picture of the grove is in this corpus, so "
                     "its existence is inferred, not attested."),
        },
        "rule": {
            "count": COUNT,
            "north_south_m": [N_NORTH, N_SOUTH],
            "clump_centre_local_enu_m": list(CLUMP_CENTRE),
            "clump_stems": CLUMP_N,
            "bank_y_m": BANK_Y,
            "band_m": BAND_M,
            "min_gap_m": MIN_GAP_M,
            "height_m": list(H_BAND),
            "seed": SEED,
        },
        "stems": stems,
        "research_note": ("WHY z05 AND NOT z08: z08_lakeshore's cottonwood is the 5-15 m dune form; "
                          "Clarke's are 'large', and z05_riverbank_timber's 22-30 m populus_deltoides is "
                          "the only record of the full-grown tree. WHAT IS INVENTED is every position "
                          "except the clump's centre, and the strip's depth (docs/LIBERTIES.md "
                          "L-shore-grove-1835-2766). WHAT WOULD MOVE THESE: Andreas's engraving of the "
                          "18th Street tree (vol. 1, p. 31), an early plat of the Clark farm or of "
                          "Eighteenth Street that draws trees, or a photograph of the shore before the "
                          "Illinois Central's fill."),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="re-derive the record and fail if the committed file differs")
    args = ap.parse_args()
    stems = deal(Field())
    text = json.dumps(record(stems), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        have = OUT.read_text() if OUT.exists() else ""
        if have != text:
            print(f"generate_shore_grove_1835: {OUT.relative_to(ROOT)} does not re-derive; "
                  "run tools/generate_shore_grove_1835.py and commit the result")
            return 1
        print(f"generate_shore_grove_1835: {len(stems)} stems re-derive")
        return 0
    OUT.write_text(text)
    print(f"generate_shore_grove_1835: wrote {len(stems)} stems to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
