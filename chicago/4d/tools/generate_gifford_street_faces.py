#!/usr/bin/env python3
"""Build the two street faces Gifford draws beside the first Tremont House (T-3605).

The owner, 2026-11-15, looking at the Tremont's photo match: the rest of the street in
that drawing "looks different" from the town, so read the drawing as a view of 1835 and
build its street faces to it. `data/reconstruction/1835_gifford_street_faces.json` is the
reading — one row per drawn building, in order along its face, with the family, the
frontage and depth, and the form the drawing shows (storeys, gable to the street or eaves,
a false front, a hipped roof, the board's lettering where it can be read). This command
turns each row into an ordinary structure record standing on the face's line, packed
between the face's two ends the way the drawing packs it.

WHAT IS A READING AND WHAT IS INVENTED. The order, the count, the storeys, the roof form
and the fronts are read off the drawing, so they carry the drawing as their source at the
`inferred` tier. The frontages are proportioned from the drawn bays and fitted to the
platted face (the drawing has no scale), and the building's presence on 1 July 1835 is the
owner's reading of a retrospective drawing, so presence, position and footprint stay
`reconstructed` (docs/LIBERTIES.md L-gifford-street-faces-3605).

    python3 tools/generate_gifford_street_faces.py           write the records
    python3 tools/generate_gifford_street_faces.py --check   fail on drift
    python3 tools/generate_gifford_street_faces.py --self-test
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "generators")]
from family_bands import families  # noqa: E402
from generate_block_infill import form_for, invented, no_build_rings, FUNCTIONS  # noqa: E402
import fabric_rule_1835  # noqa: E402
from generate_west_infill import footprint_origin  # noqa: E402
from plat_corridors import corridors, intrusion  # noqa: E402
from plat_occupancy import world_polygon, footprints, overlap_area  # noqa: E402
from inferred_occupancy import occupancy  # noqa: E402
from normalise_structure_function import canonical  # noqa: E402

CORRIDOR_LINE = "drawn"
CORRIDOR_LINE_WHY = ("The rows stand on platted block faces, so the block grid's own drawn "
                     "line is the one asked whether a store stands in the roadway.")
RECIPE = DATA / "reconstruction" / "1835_gifford_street_faces.json"
LOTS = DATA / "traces" / "vectors" / "thompson_lots.json"
INVENTORY = DATA / "reconstruction" / "1835_building_inventory.json"
PREFIX = "recon_1835_gifford_"
SOURCE = "owner_chicago_1835_reconstruction_spec_2026"
DRAWING = "gifford_tremont_house_no_1"
STREET_NAME = {"lake": "Lake Street", "dearborn": "Dearborn Street"}
#: a party row may stand this close to its own neighbours, and no closer to anything else
ROW_GAP_MIN_M = 0.10
OTHER_GAP_MIN_M = 0.50


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _unit(a, b):
    de, dn = b[0] - a[0], b[1] - a[1]
    length = math.hypot(de, dn)
    return (de / length, dn / length), length


def face_frame(face: dict, block: dict):
    """The face line's origin, its unit direction, and its inward (into-the-block) normal."""
    a, b = face["line"]["from"], face["line"]["to"]
    t, _ = _unit(a, b)
    ring = block["boundary_local_enu_m"]
    ce = sum(p[0] for p in ring) / len(ring)
    cn = sum(p[1] for p in ring) / len(ring)
    nrm = (-t[1], t[0])
    if (ce - a[0]) * nrm[0] + (cn - a[1]) * nrm[1] < 0:
        nrm = (-nrm[0], -nrm[1])
    return a, t, nrm


def station_span(poly, a, t):
    s = [(p[0] - a[0]) * t[0] + (p[1] - a[1]) * t[1] for p in poly]
    return min(s), max(s)


def bearing_of(vec) -> float:
    return (math.degrees(math.atan2(vec[0], vec[1])) + 360.0) % 360.0


def lay_face(face: dict, block: dict, datum: dict, standing: dict) -> list[dict]:
    """Stations and centres for every building of one face, in recipe order."""
    a, t, nrm = face_frame(face, block)
    outward = (-nrm[0], -nrm[1])
    bearing = round(bearing_of(outward), 6)
    inset = float(face["line"]["inset_m"])
    alley = [tuple(p) for p in block["alley_local_enu_m"]]
    al0, al1 = station_span(alley, a, t)
    if "start_after" in face:
        s0 = station_span(standing[face["start_after"]], a, t)[1] + float(face["start_clear_m"])
    else:
        s0 = float(face["start_m"])
    s1 = None
    if "end_before" in face:
        s1 = station_span(standing[face["end_before"]], a, t)[0] - float(face["end_clear_m"])
    rows = face["buildings"]
    # The block alley splits a face that runs along its side: the rows before it are
    # packed to its near edge, the rows marked `after_alley` start past its far edge.
    split = next((i for i, r in enumerate(rows) if r.get("after_alley")), None)
    runs = []
    if split is None:
        runs.append((rows, s0, s1))
    else:
        if not al0 > s0:
            raise ValueError(f"{face['id']}: the alley does not lie ahead of the row")
        runs.append((rows[:split], s0, al0 - 0.6))
        runs.append((rows[split:], al1 + 0.6, None))
    out = []
    for run, lo, hi in runs:
        widths = [float(r["width_m"]) for r in run]
        if hi is None:
            gap = 0.3
        else:
            gap = (hi - lo - sum(widths)) / max(1, len(run) - 1)
            if gap < ROW_GAP_MIN_M:
                raise ValueError(f"{face['id']}: {len(run)} drawn stores need "
                                 f"{sum(widths):.2f} m and the face holds {hi - lo:.2f} m")
        s = lo
        for row, w in zip(run, widths):
            mid = s + w / 2.0
            depth = float(row["depth_m"])
            off = inset + depth / 2.0
            ce = a[0] + t[0] * mid + nrm[0] * off
            cn = a[1] + t[1] * mid + nrm[1] * off
            out.append({"row": row, "centre": (ce, cn), "bearing": bearing,
                        "station": (round(s, 3), round(s + w, 3)), "gap": round(gap, 3)})
            s += w + gap
    return out


def _drawn(value, why: str) -> dict:
    return {"value": value, "confidence": "reconstructed", "sources": [DRAWING],
            "note": ("READ OFF GIFFORD'S DRAWING of the first Tremont House and its street "
                     f"({DRAWING}): {why}. Graded reconstructed, not inferred: the value is "
                     "the drawing's, but which building of 1835 the drawn front was is ours "
                     "(the roof is an invented count-unit), the drawing is retrospective, and "
                     "taking it as the street on 1 July 1835 is the owner's reading of "
                     "2026-11-15 (T-3605, docs/LIBERTIES.md L-gifford-street-faces-3605). "
                     "The drawn value stands over the family's typology band where the two "
                     "differ.")}


def make_record(seq: int, face: dict, laid: dict, table: dict, datum: dict,
                people: dict) -> dict:
    row = laid["row"]
    family = row["family"]
    spec = table[family]
    sid = f"{PREFIX}{family.lower()}_{seq:03d}"
    width, depth = float(row["width_m"]), float(row["depth_m"])
    ce, cn = laid["centre"]
    east, north = footprint_origin(ce, cn, width, depth, laid["bearing"])
    fabric = fabric_rule_1835.deal(sid, family, spec["archetype"])
    form = fabric_rule_1835.apply_form(
        form_for(family, spec, sid, width, depth, fabric["paint"]), fabric)
    for attr, value in row.get("form", {}).items():
        form[attr] = _drawn(value, row["read"])
    if spec["archetype"] == "frame_tavern" and form.get("rear_ell", {}).get("value"):
        # A three-storey block on a party row has neighbours at both ends and the drawn
        # rear is not seen; the programme's rear service wing is left off rather than
        # pushed into the yard behind a store.
        form.pop("rear_ell", None)
        form.pop("rear_ell_door", None)
    if spec["archetype"] == "frame_tavern" and form.get("roof_type", {}).get("value") == "hip":
        # the programme's stovepipes stand on a gable's two slopes; a drawn hip carries
        # its stacks as chimneys instead
        form.pop("stovepipes", None)
        # and the drawn hip is a low one, lower than the family's gable pitches
        form["roof_pitch_deg"] = _drawn(form["roof_pitch_deg"]["value"],
                                        "a low hipped roof, as drawn")
    if spec["archetype"] == "frame_tavern" and form.get("stories", {}).get("value") == 3:
        form["wall_height_m"] = _drawn(round(3.0 * 3, 3), "three full storeys, about 3 m a storey")
    if spec["archetype"] == "frame_storefront" and form.get("stories", {}).get("value") == 2.0:
        form["wall_height_m"] = _drawn(form["wall_height_m"]["value"],
                                       "two full storeys under the eaves")
    if row.get("sign_as_drawn"):
        form["sign"] = _drawn(row["sign_as_drawn"],
                              f"the board is lettered {row['sign_as_drawn']!r} in the drawing")
    street = STREET_NAME[face["street"]]
    function_term = FUNCTIONS.get(family) or canonical(spec["label"])
    record = {
        "id": sid,
        "name": f"Reconstructed {spec['label'].lower()} on {street}, as Gifford draws it",
        "archetype": spec["archetype"],
        "phases": [{
            "id": "inferred_1835",
            "documented_range": {
                "from": "1835-01-01", "to": "1835-12-31", "confidence": "reconstructed",
                "sources": [DRAWING],
                "note": ("Drawn standing beside the first Tremont House (1833-1839) in "
                         "Gifford's retrospective view of its street; taken as standing on "
                         "1 July 1835 on the owner's reading of the drawing (T-3605). No "
                         "dated record of this building is known.")},
            "position": {
                "utm_e": round(datum["origin_utm_e"] + east, 3),
                "utm_n": round(datum["origin_utm_n"] + north, 3),
                "rotation_deg": laid["bearing"],
                "symbolic_location": (f"{street}, {face['id'].replace('_', ' ')}: drawn "
                                      f"store {row['key'].upper()} of Gifford's row"),
                "confidence": "reconstructed",
                "sources": [DRAWING],
                "note": (f"Placed in the drawn order along the face, at stations "
                         f"{laid['station'][0]:.2f}-{laid['station'][1]:.2f} m of the "
                         f"face line ({face['line']['why']}), with {laid['gap']:.2f} m "
                         f"between neighbours. Drawn at x {row['drawn_px'][0]}-"
                         f"{row['drawn_px'][1]} px of the 1637 px plate. The face is the "
                         f"drawing's (read through the Tremont's solved camera, "
                         f"data/reconstruction/1835_gifford_street_faces.json camera); "
                         f"the station is fitted, not measured."),
                "derivation": {"method": "not_derivable",
                               "reason": "The drawing has no scale; the rows are fitted to the platted face."}},
            "footprint": {
                "polygon": [[0, 0], [width, 0], [width, depth], [0, depth]],
                "confidence": "reconstructed",
                "note": (f"{width:.2f} m of frontage proportioned from the drawn bays "
                         f"({DRAWING}; the drawing's frontage stands over the {family} "
                         f"typology's own where the two differ), and {depth:.2f} m deep, "
                         f"a depth the {family} typology allows. Neither is a "
                         f"measurement.")},
            "form": form,
            "change_note": "T-3605 builds this store as Gifford draws it."}],
        "function": invented(function_term,
                             f"The {family} type, as the drawn front reads; no proprietor "
                             f"is recovered from the drawing."),
        "reconstruction": {
            "status": "inferred_anonymous", "family": family, "district": face["district"],
            "inventory_class": "principal_functional",
            "programme_phase": "gifford_street_faces_1835", "source_id": SOURCE,
            "sequence": seq, "finish_key": fabric["finish_key"],
            "roof_condition": fabric["roof_condition"], "age_state": fabric["age_state"],
            "fabric_basis": fabric["fabric_basis"],
            "drawn": {"source_id": DRAWING, "face": face["id"], "key": row["key"],
                      "drawn_px": row["drawn_px"], "read": row["read"]}},
        **({"occupants": people[sid]} if sid in people else {}),
        "research_note": ("RECONSTRUCTED FROM A PICTURE. Gifford draws this store in the row "
                          "beside the first Tremont House; the owner ruled on 2026-11-15 that "
                          "the drawing is a reasonable view of 1835 and the street is to be "
                          "built to it. The drawn form is read off the drawing and graded reconstructed; the "
                          "building's presence in July 1835, its exact frontage and its "
                          "station are reconstructed. Its occupants, if any, are dealt by "
                          "the town's housing tools and graded by their own records."),
        "review_required": False,
    }
    return record


def records_from_inputs():
    recipe, datum = load(RECIPE), load(DATA / "datum.json")
    blocks = {b["id"]: b for b in load(LOTS)["blocks"]}
    table, people = families(), occupancy()
    standing = dict(footprints(datum, set()))
    records, seq = [], 0
    for face in recipe["faces"]:
        for laid in lay_face(face, blocks[face["block_id"]], datum, standing):
            seq += 1
            records.append(make_record(seq, face, laid, table, datum, people))
    return records, validate(records, recipe, datum)


def _gap(a, b) -> float:
    if overlap_area(b, a) > 1e-4:  # a, the new rectangle, is the convex clip
        return 0.0
    def seg(p, q, r):
        de, dn = r[0] - q[0], r[1] - q[1]
        span = de * de + dn * dn
        u = 0.0 if span == 0 else max(0.0, min(1.0, ((p[0]-q[0])*de + (p[1]-q[1])*dn) / span))
        return math.hypot(p[0] - (q[0] + u * de), p[1] - (q[1] + u * dn))
    return min(seg(p, q, r) for x, y in ((a, b), (b, a)) for p in x
               for q, r in zip(y, y[1:] + y[:1]))


def validate(records, recipe, datum) -> list[str]:
    import importlib
    want = Counter(r["family"] for f in recipe["faces"] for r in f["buildings"])
    if Counter(r["reconstruction"]["family"] for r in records) != want:
        raise ValueError("the records do not hold one roof per drawn store")
    if len({r["id"] for r in records}) != len(records):
        raise ValueError("two drawn stores share an id")
    # The inventory's `pictured_roofs` block keeps these roofs off the household model's
    # weights (tools/model_town_1835.py household_matrix); it must say what is written here.
    group = {"C": "stores_mixed_use", "H": "larger_boarding_houses"}
    held = {}
    for r in records:
        rec = r["reconstruction"]
        cell = held.setdefault(group[rec["family"][0]], {})
        cell[rec["district"]] = cell.get(rec["district"], 0) + 1
    pictured = load(INVENTORY).get("pictured_roofs") or {}
    if pictured.get("structure_prefix") != PREFIX or pictured.get("by_group") != held:
        raise ValueError(f"the inventory's pictured_roofs block says {pictured.get('by_group')} "
                         f"and the records hold {held}")
    lanes = corridors()
    refused = no_build_rings()
    ids = {r["id"] for r in records}
    in_1835 = {s["id"] for s in load(DATA / "sidecars" / "1835" / "index.json")["structures"]}
    others = [(sid, poly) for sid, poly in footprints(datum, ids) if sid in in_1835]
    own = [(r["id"], world_polygon(r["phases"][0], datum)) for r in records]
    report = []
    for record, (sid, poly) in zip(records, own):
        importlib.import_module("archetypes." + record["archetype"] + "_params").from_phase(
            record["phases"][0], record)
        street, depth = intrusion(poly, lanes)
        if street:
            raise ValueError(f"{sid} intrudes {depth:.2f} m into {street}")
        for name, ring in refused.items():
            if overlap_area(ring, poly) > 1e-3:
                raise ValueError(f"{sid} stands on refused ground {name}")
        near_row = min(_gap(poly, q) for o, q in own if o != sid)
        if near_row < ROW_GAP_MIN_M - 1e-6:
            raise ValueError(f"{sid} stands {near_row:.2f} m from a neighbour in its own row")
        near = min(((_gap(poly, q), o) for o, q in others), default=(99.0, None))
        if near[0] < OTHER_GAP_MIN_M:
            raise ValueError(f"{sid} stands {near[0]:.2f} m from {near[1]}")
        report.append(f"{sid}: {record['reconstruction']['drawn']['face']} "
                      f"{record['reconstruction']['drawn']['key']}, nearest other "
                      f"{near[0]:.2f} m ({near[1]})")
    return report


def self_test() -> int:
    records, _ = records_from_inputs()
    recipe, datum = load(RECIPE), load(DATA / "datum.json")
    cases = []
    short = copy.deepcopy(records[:-1])
    cases.append(("a drawn store left out", short))
    dup = copy.deepcopy(records)
    dup[1]["id"] = dup[0]["id"]
    cases.append(("two stores under one id", dup))
    road = copy.deepcopy(records)
    road[0]["phases"][0]["position"]["utm_n"] -= 12.0
    cases.append(("a store moved into Lake Street", road))
    onto = copy.deepcopy(records)
    onto[0]["phases"][0]["position"] = copy.deepcopy(onto[1]["phases"][0]["position"])
    cases.append(("two stores on one spot", onto))
    lost = copy.deepcopy(records)
    lost[0]["reconstruction"]["district"] = "west"
    cases.append(("a store the inventory's pictured_roofs does not hold", lost))
    for label, mutated in cases:
        try:
            validate(mutated, recipe, datum)
        except (ValueError, SystemExit):
            print("   self-test | PASS: refuses " + label)
        else:
            print("   self-test | FAIL: did not refuse " + label)
            return 1
    try:
        tight = copy.deepcopy(recipe["faces"][0])
        tight["buildings"][0]["width_m"] = 40.0
        blocks = {b["id"]: b for b in load(LOTS)["blocks"]}
        lay_face(tight, blocks[tight["block_id"]], datum, dict(footprints(datum, set())))
    except ValueError:
        print("   self-test | PASS: refuses a row wider than its face")
    else:
        print("   self-test | FAIL: laid a row wider than its face")
        return 1
    print("PASS: generate_gifford_street_faces self-test")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    records, report = records_from_inputs()
    drift, expected = [], set()
    for record in records:
        path = DATA / "structures" / (record["id"] + ".json")
        expected.add(path)
        content = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                drift.append(str(path.relative_to(ROOT)))
        else:
            path.write_text(content, encoding="utf-8")
    stale = [p for p in (DATA / "structures").glob(PREFIX + "*.json") if p not in expected]
    if args.check:
        drift += [str(p.relative_to(ROOT)) for p in stale]
    else:
        for p in stale:
            p.unlink()
    print("\n".join(report))
    if drift:
        print("FAIL: Gifford street-face records drift: " + ", ".join(drift))
        return 1
    print(f"PASS: {len(records)} Gifford street-face roofs"
          + (" rederive exactly" if args.check else " generated"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
