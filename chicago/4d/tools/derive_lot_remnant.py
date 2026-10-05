#!/usr/bin/env python3
"""derive_lot_remnant.py — the vacant platted lots as grazed prairie remnant (T-2101).

WHY THIS EXISTS. The owner, 2026-10-04, asking for a tidier town (T-2086): the town should be
*"less 'weedy' in the town area, in front of stores and houses, and in the house back yards and
properties"* — and *"I don't want you to go crazy and cut all the beautiful plants and grass and
flowers"*. T-2086 kept the yards of the improved lots (`tools/generate_kept_ground.py`) and said in
writing that a lot with no building is not a yard. Its second point is this one: **a platted lot
with no building stays grazed prairie remnant — shorter and patchier than the open prairie, with
its flowers** — so the flowers are still in town, between the houses. Until this record every
vacant lot grew `z10_settled_town`'s ruderal mix: lamb's-quarters, pigweed, ragweed, cocklebur
and dock over a trodden sward, the "weedy" ground the owner asked to see less of.

WHAT THE EVIDENCE IS, and what it is not. The flora dossier (`docs/research/02-flora.md` § 5) has
the grid "drawn but mostly not built" in summer 1835 (documented), and livestock at large — the
town's code of 7 Nov 1833 forbids letting pigs wander, cattle grazed the unfenced commons —
producing a cropped halo round the built blocks that grades into ungrazed prairie (ordinance
documented, halo inferred). Nothing describes a particular vacant lot. So this community is
RECONSTRUCTED (docs/LIBERTIES.md, the vacant-lot liberty), bounded three ways:

  * its SPECIES are the committed records' own, copied from `z02_mesic_prairie` (the higher
    prairie the plat was laid across) and, for the trodden grass and clover that follow stock
    onto grazed ground, from `z10_settled_town`. No species is new. Each copy keeps its parent's
    July state, colour, flower and width, and is never graded above its parent;
  * WHICH prairie forbs stand is the plain ecology of grazed prairie: stock take the palatable
    plants first (compass plant, purple prairie clover, lead plant — the "decreasers") and leave
    the bitter, aromatic, spiny and milky ones (bergamot, rattlesnake master, butterfly weed,
    black-eyed Susan — the "increasers"). The ones left out are named in the record with why;
  * HOW SHORT AND HOW PATCHY is CROP below — every height inside or under its parent's July
    range, every density at or under it except the two increasers grazing favours, and the bare
    share between the prairie's 0.02 and the trodden town's 0.45.

THE EXTENT is derived, never drawn: every lot of the committed plat
(`data/traces/vectors/thompson_lots.json`) that the lot survey `generate_lot_line_fences.survey`
finds no building placed in, that no standing structure's footprint overlaps and that no yard
outbuilding is dealt to — and that lies wholly inside the settled town's own derived extent, so the
beach band and the public square's slough keep their communities. Neighbouring vacant lots in one
tier share their side lines exactly, so their union is taken edge for edge, not rasterised. The
zone's priority sits just over the town's, so on those lots it wins and nowhere else does it reach.

Its matrix stands over the turf line (`turf-tile.js` TURF_MAX_M, 0.25 m), so the renderer draws it
as sward and not as painted turf — the remnant keeps its grass as well as its flowers.

    python3 tools/derive_lot_remnant.py --write   # write the zone record and its manifest entry
    python3 tools/derive_lot_remnant.py --check   # fail if either drifted (check.sh)
    python3 tools/derive_lot_remnant.py           # report only
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_lot_line_fences as fences  # noqa: E402
from generate_dooryard_pickets import convex_overlap, footprint_world  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FLORA = DATA / "flora"
INDEX = FLORA / "index.json"
TOWN = FLORA / "zones" / "z10_settled_town.json"
PRAIRIE = FLORA / "zones" / "z02_mesic_prairie.json"
OUTBUILDINGS = DATA / "yard" / "town_yard_outbuildings.json"
ZONE_ID = "z11_lot_remnant"
OUT = FLORA / "zones" / f"{ZONE_ID}.json"
LIBERTY = "docs/LIBERTIES.md L386"
PRIORITY = 62          # over z10_settled_town's 60, under z04_marsh's 70
COLLINEAR_M = 0.02     # a union vertex this close to its neighbours' chord is a lot corner on a straight line

# THE CROP, per species: (parent zone, height_m, abundance). Heights are the July plant under
# grazing; abundances are the remnant's, against the parent's stated range.
CROP = [
    # The matrix: the prairie's bunchgrasses cropped, and the trodden bluegrass that follows
    # stock onto grazed ground. Big bluestem is the grass cattle take first, so it is the
    # shortest and the thinnest of the three bluestems relative to its parent.
    ("z02_mesic_prairie", "schizachyrium_scoparium", [0.25, 0.45], {"cover_fraction": [0.15, 0.25]}),
    ("z02_mesic_prairie", "andropogon_gerardii", [0.3, 0.55], {"cover_fraction": [0.1, 0.18]}),
    ("z02_mesic_prairie", "sporobolus_heterolepis", [0.3, 0.4], {"cover_fraction": [0.03, 0.06]}),
    ("z10_settled_town", "poa_pratensis", [0.05, 0.2], {"cover_fraction": [0.1, 0.2]}),
    ("z10_settled_town", "trifolium_repens", [0.05, 0.15], {"cover_fraction": [0.02, 0.06]}),
    # The flowers stock leave: bergamot (aromatic), rattlesnake master (spiny), butterfly weed
    # (milky, bitter) and black-eyed Susan (bristly, and a coloniser of broken ground) stand at
    # or above their prairie density; the palatable coneflowers stand, thinned.
    ("z02_mesic_prairie", "monarda_fistulosa", [0.6, 0.9], {"density_per_ha": [400, 1000]}),
    ("z02_mesic_prairie", "rudbeckia_hirta", [0.35, 0.65], {"density_per_ha": [150, 400]}),
    ("z02_mesic_prairie", "eryngium_yuccifolium", [0.8, 1.2], {"density_per_ha": [150, 400]}),
    ("z02_mesic_prairie", "asclepias_tuberosa", [0.3, 0.5], {"density_per_ha": [20, 100]}),
    ("z02_mesic_prairie", "ratibida_pinnata", [0.6, 1.0], {"density_per_ha": [150, 400]}),
    ("z02_mesic_prairie", "echinacea_pallida", [0.5, 0.8], {"density_per_ha": [30, 120]}),
]

# The parent's species this community does NOT carry, each with its reason — a remnant is
# stated by what it lost as much as by what it kept.
LEFT_OUT = {
    "sorghastrum_nutans": "Indian grass is a palatable decreaser and the first tall grass to go "
                          "under steady grazing; its 0.8-1.1 m is the open prairie's height",
    "silphium_laciniatum": "compass plant is the classic grazing casualty — stock seek out its "
                           "leaves — and its 2.0-2.8 m stalk is exactly the tall prairie a grazed "
                           "lot is not",
    "dalea_purpurea": "purple prairie clover is a legume stock prefer, a textbook decreaser",
    "amorpha_canescens": "lead plant is browsed hard and recovers slowly, a textbook decreaser",
    "heliopsis_helianthoides": "ox-eye is a woodland-edge forb of the prairie record and palatable; "
                               "it is left to the open prairie rather than guessed onto a lot",
    "parthenium_integrifolium": "wild quinine is a forb of undisturbed prairie; nothing bounds it "
                                "onto grazed ground",
}

COVER = {"matrix_fraction": 0.75, "bare_soil_fraction": 0.12, "standing_water_fraction": 0.02}

EXISTENCE_NOTE = (
    "RECONSTRUCTED (T-2101, " + LIBERTY + "). DERIVED, NOT DRAWN: tools/derive_lot_remnant.py "
    "takes every lot of the committed plat that holds no building, no standing structure's "
    "footprint and no dealt outbuilding, and lies wholly inside z10_settled_town's derived extent, "
    "and check.sh refuses a hand edit. The dossier has the grid 'drawn but mostly not built' in "
    "summer 1835 and stock at large on it (the 7 Nov 1833 code against wandering pigs; cattle on "
    "the unfenced commons); no source describes a particular vacant lot, so what the ground is "
    "there is reconstructed: the prairie the plat was laid across, cropped by the town's stock, "
    "with the flowers stock leave standing in it. Neighbouring vacant lots in one tier share their "
    "side lines, so their union is exact.")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def pip(ring, e, n) -> bool:
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > n) != (yj > n) and e < (xj - xi) * (n - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def area2(ring) -> float:
    return sum(ring[i - 1][0] * ring[i][1] - ring[i][0] * ring[i - 1][1] for i in range(len(ring)))


def in_town(ext, e, n) -> bool:
    """The settled town's own extent rule, as flora.js `matches` reads a polygon extent."""
    ok = pip(ext["polygon"], e, n) or any(pip(r, e, n) for r in ext.get("include_polygons") or [])
    return ok and not any(pip(r, e, n) for r in ext.get("exclude_polygons") or [])


def vacant_lots():
    """Every vacant platted lot inside the town, and a count of every other lot by why."""
    lots = load(fences.LOTS_PATH)
    entries, sidecars = fences.survey()
    improved = {(e["block"]["id"], e["index"]) for e in entries}
    fps = [[tuple(p) for p in footprint_world(sc)] for _, sc in sorted(sidecars.items())]
    fps = [fp for fp in fps if len(fp) >= 3]
    dealt = {ob["lot"] for ob in load(OUTBUILDINGS)["outbuildings"]}
    town = load(TOWN)["extent"]
    out, why = [], {"improved": 0, "a footprint overlaps it": 0, "an outbuilding is dealt to it": 0,
                    "not wholly on the settled town's ground": 0}
    for block in lots["blocks"]:
        for i, lot in enumerate(block["lots"]):
            poly = [tuple(p) for p in lot["polygon"]]
            if (block["id"], i) in improved:
                why["improved"] += 1
            elif any(convex_overlap(fp, poly) for fp in fps):
                why["a footprint overlaps it"] += 1
            elif f"{block['id']}_lot{i}" in dealt:
                why["an outbuilding is dealt to it"] += 1
            elif not all(in_town(town, e, n) for e, n in poly):
                why["not wholly on the settled town's ground"] += 1
            else:
                out.append((block["id"], i, lot.get("tier"), poly))
    return out, why


def drop_collinear(ring):
    """Remove the lot corners a union leaves standing on a straight line."""
    pts = list(ring)
    changed = True
    while changed and len(pts) > 3:
        changed = False
        for i in range(len(pts)):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
            L = math.hypot(c[0] - a[0], c[1] - a[1]) or 1e-9
            d = abs((c[0] - a[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (c[1] - a[1])) / L
            if d < COLLINEAR_M:
                del pts[i]
                changed = True
                break
    return pts


def union(polys):
    """The exact union of lots that share whole side lines: every directed edge two
    counter-clockwise lots share runs once each way and cancels, and what is left chains into
    rings. Returns None where the edges will not chain into simple rings — the caller then keeps
    the lots apart rather than guess."""
    edges = {}
    for poly in polys:
        ring = poly if area2(poly) > 0 else list(reversed(poly))
        for i in range(len(ring)):
            a, b = ring[i], ring[(i + 1) % len(ring)]
            if (b, a) in edges:
                del edges[(b, a)]
            else:
                edges[(a, b)] = True
    nxt = {}
    for a, b in edges:
        if a in nxt:
            return None
        nxt[a] = b
    rings = []
    while nxt:
        start = min(nxt)
        ring, cur = [start], nxt.pop(start)
        while cur != start:
            if cur not in nxt:
                return None
            ring.append(cur)
            cur = nxt.pop(cur)
        rings.append(ring)
    return rings


def derive():
    lots, why = vacant_lots()
    groups = {}
    for bid, i, tier, poly in lots:
        groups.setdefault((bid, tier), []).append(poly)
    rings = []
    for key in sorted(groups, key=lambda k: (k[0], str(k[1]))):
        polys = groups[key]
        merged = union(polys)
        for ring in (merged if merged is not None else polys):
            ring = drop_collinear(ring if area2(ring) > 0 else list(reversed(ring)))
            rings.append([[round(e, 2), round(n, 2)] for e, n in ring])
    rings.sort(key=lambda r: (-abs(area2(r)), r[0]))
    pts = [p for r in rings for p in r]
    extent = {
        "kind": "polygon",
        "polygon": rings[0],
        "include_polygons": rings[1:],
        "priority": PRIORITY,
        "confidence": "reconstructed",
        "sources": [],
        "note": EXISTENCE_NOTE,
        "box": {"e": [math.floor(min(p[0] for p in pts)), math.ceil(max(p[0] for p in pts))],
                "n": [math.floor(min(p[1] for p in pts)), math.ceil(max(p[1] for p in pts))]},
    }
    report = {"lots": len(lots), "why": why, "rings": len(rings),
              "area_ha": round(sum(abs(area2(r)) / 2 for r in rings) / 1e4, 2)}
    return extent, report


def species():
    parents = {z["id"]: {s["id"]: s for s in z["species"]} for z in (load(PRAIRIE), load(TOWN))}
    out = []
    for zid, sid, height, abundance in CROP:
        sp = copy.deepcopy(parents[zid][sid])
        ph = sp["height_m"]
        if height[0] > ph[0] or height[1] > ph[1]:
            raise SystemExit(f"CROP {sid}: {height} is not at or under its parent's {ph} — a grazed "
                             "plant is never taller than the prairie's")
        was = dict(sp["abundance"])
        sp["height_m"] = height
        sp["abundance"] = abundance
        sp["confidence"] = "reconstructed"
        sp.pop("abundance_provenance", None)
        wp = sp.get("width_provenance")
        if isinstance(wp, dict) and wp.get("confidence") in ("attested", "inferred"):
            wp["confidence"] = "reconstructed"
        sp["note"] = (f"Copied from {zid} ({ph[0]}-{ph[1]} m, {json.dumps(was)}) with its July "
                      f"state, colour and flower unchanged; height and abundance are this "
                      f"community's grazing crop, reconstructed ({LIBERTY}). Parent's note: "
                      + (parents[zid][sid].get("note") or "none"))
        out.append(sp)
    return out


def record(extent):
    prairie = load(PRAIRIE)
    return {
        "id": ZONE_ID,
        "zone": 11,
        "name": "Vacant lots: grazed prairie remnant",
        "dossier": "docs/research/02-flora.md § 5 (livestock at large) and § ZONE 2",
        "scene_date": "1835-07-01",
        "palette": prairie["palette"],
        "reads_as": "a cropped, patchy prairie sward between the houses, knee-high at most, "
                    "with the flowers the stock leave standing in it — lavender bergamot, "
                    "black-eyed Susan, rattlesnake master's pale globes, butterfly weed's orange",
        "plantable_in_scene": True,
        "scenes": ["1835"],
        "generated_by": "tools/derive_lot_remnant.py",
        "cover": COVER,
        "ground": {"rgb": [89, 86, 59], "wet_rgb": [66, 63, 45]},
        "extent": extent,
        "species": species(),
        "left_out": [{"id": k, "from": "z02_mesic_prairie", "why": v} for k, v in LEFT_OUT.items()],
        "confidence": "reconstructed",
        "sources": [],
        "note": "Every value is reconstructed; " + LIBERTY + " records the liberty. The ground "
                "colour is the mean of the mesic prairie's and the settled town's, and the bare "
                "share sits between them: grazed ground shows more earth than the prairie and far "
                "less than the trodden town.",
        "review_required": False,
    }


def manifest_entry(rec):
    return {
        "id": rec["id"], "zone": rec["zone"], "file": f"zones/{rec['id']}.json",
        "palette": rec["palette"], "priority": rec["extent"]["priority"],
        "plantable_in_scene": rec["plantable_in_scene"], "scenes": rec["scenes"],
        "extent": rec["extent"], "ground_rgb": rec["ground"]["rgb"],
        "ground_wet_rgb": rec["ground"]["wet_rgb"],
        "bare_soil_fraction": rec["cover"]["bare_soil_fraction"],
    }


def entry_text(entry) -> str:
    pad = "    "
    lines = []
    for k, v in entry.items():
        if k == "extent":
            body = ",\n".join(f"{pad}    {json.dumps(ek)}: "
                              f"{json.dumps(ev, ensure_ascii=False, separators=(',', ':'))}"
                              for ek, ev in v.items())
            lines.append(f'{pad}  "extent": {{\n{body}\n{pad}  }}')
        else:
            lines.append(f"{pad}  {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}")
    return pad + "{\n" + ",\n".join(lines) + "\n" + pad + "}"


def write_manifest(entry) -> None:
    """Replace this zone's manifest entry in place, or add it after the last zone; every other
    byte of the hand-formatted manifest stays as its author wrote it."""
    text = INDEX.read_text(encoding="utf-8")
    dec = json.JSONDecoder()
    zones_at = text.index("[", text.index('"zones":'))
    _, used = dec.raw_decode(text[zones_at:])
    end = zones_at + used - 1                     # the zones list's closing bracket
    tag = f'"id": "{entry["id"]}"'
    if tag in text[zones_at:end]:
        start = text.rfind("{", 0, text.index(tag, zones_at))
        _, n = dec.raw_decode(text[start:])
        text = text[:start] + entry_text(entry).lstrip() + text[start + n:]
    else:
        last = text.rfind("}", zones_at, end) + 1
        text = text[:last] + ",\n" + entry_text(entry) + text[last:]
    INDEX.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    extent, rep = derive()
    rec = record(extent)
    entry = manifest_entry(rec)
    print(f"lot remnant: {rep['lots']} vacant platted lot(s) in {rep['rings']} ring(s), "
          f"{rep['area_ha']} ha; " + ", ".join(f"{v} {k}" for k, v in rep["why"].items()))
    text = json.dumps(rec, indent=1, ensure_ascii=False) + "\n"
    if args.write:
        OUT.write_text(text, encoding="utf-8")
        write_manifest(entry)
        print(f"  wrote {OUT.relative_to(ROOT)} and {INDEX.relative_to(ROOT)}")
    elif args.check:
        on_disk = next((z for z in load(INDEX)["zones"] if z["id"] == ZONE_ID), None)
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text or on_disk != entry:
            print(f"FAIL: {ZONE_ID} (record or manifest entry) is not what the plat, the lot "
                  "survey and the crop derive — never hand-edit it; run "
                  "python3 tools/derive_lot_remnant.py --write")
            return 1
        print("  the record and the manifest hold the derived remnant")
    return 0


if __name__ == "__main__":
    sys.exit(main())
