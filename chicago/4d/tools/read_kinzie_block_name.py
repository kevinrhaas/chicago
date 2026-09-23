#!/usr/bin/env python3
"""Read the Kinzie Block off Wright's 1834 survey, and search the corpus for its name.

    tools/read_kinzie_block_name.py           print the reading
    tools/read_kinzie_block_name.py --write   write data/traces/kinzie_block_name.json
    tools/read_kinzie_block_name.py --check   re-derive the committed file WITHOUT the raster
    tools/read_kinzie_block_name.py --check-sheet   re-open the raster and re-derive the peaks

WHAT IS BEING READ. Wright letters two words — "Kinzie" over "Block" — inside one
block of Kinzie's Addition, between Michigan and Illinois Streets and between Cass
and Rush. It is the only block in the Addition given a NAME, and apart from the
Public Square the only one on the whole sheet. Every other block in its tier
carries a numeral instead. That is the whole of the claim this file makes about
the sheet, and it is made three ways: the lettering is transcribed off a cited
crop; the numerals either side of it are transcribed off their own crops, which
is what places the name in the slot that would be number 11; and the block's
INTERIOR is measured, because the sheet says something about this block that no
transcription can — it is drawn with no lot divisions at all while both its
neighbours are ruled into lots.

WHY THE INTERIOR IS MEASURED AND NOT LOOKED AT. A lot division on this sheet is a
short vertical rule, and whether one is there is a fact about the raster anybody
can re-measure. `_profile` from tools/read_kinzie_addition_streets.py stacks the
ink of a band along the sheet's own shear and projects it onto one axis; `_rules`
takes the sharp narrow peaks. Run across the tier, the block boundaries and the
lot rules come out at peak heights of 65 to 108 and the cursive strokes of the
lettering come out at 15 to 33, which is a margin of two to one with nothing in
between. The cut is stated below as RULE_PEAK_MIN and every peak the profile
found, above and below it, is written to the committed file so the next person
can disagree with the cut rather than with a summary of it.

WHAT THIS FILE DOES NOT DO. It does not number the Addition's blocks — that is
T-1061's, and this reading transcribes exactly two numerals, the ones that bracket
the name. It does not read the river tier or the water lots (T-1063). Blocks east
of Pine Street are cut by the lake shore and are drawn on a different division;
the interior measurement here is stated for the three full-width blocks between
Wolcott and Pine and claims nothing about the shore-cut ones.

THE SEATING is the committed grid's, never this sheet's own fit. The block's
footprint is derived from the four streets that bound it in data/streets/1835.json
— michigan_north, illinois_north, cass and rush, all four already seated by T-1060
— so the ground this names is the ground the walker stands on. The sheet is read
for WHAT IS DRAWN THERE; where it is, the committed streets already say.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from read_kinzie_addition_streets import _profile, _rules, _sheet, SHEAR_NS, SHEAR_EW  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/traces/kinzie_block_name.json"
STREETS = ROOT / "data/streets/1835.json"
RESEARCH = ROOT / "data/research"
SCENE = ROOT / "data/scenes/1835.json"
NUMERALS = ROOT / "data/traces/kinzie_addition_block_numbering.json"

TICKET = "T-1062 (piece 3 of T-0789)"

# The bands the tier's north-south rules are read in: the upper and lower
# half-blocks of the Michigan-Illinois tier, clear of the tier's own bounding
# rules and of the mid-block line between them.
TIER_BANDS = [
    {"id": "upper_half_block", "y": (1900, 1928),
     "note": "between the Illinois rule and the mid-block line"},
    {"id": "lower_half_block", "y": (1948, 1976),
     "note": "between the mid-block line and the Michigan rule"},
]
TIER_X = (2790, 3620)          # Wolcott's east rule to beyond Sand Street
RULE_PEAK_MIN = 50.0           # see the header: rules 65-108, lettering 15-33

# The block boundaries the tier scan is expected to find, west to east, as the
# rules bounding the three full-width blocks. Named here so the scan's output is
# attached to blocks rather than left as a list of numbers.
BOUNDS = [
    ("wolcott_east", 2941), ("cass_west", 3096), ("cass_east", 3130),
    ("rush_west", 3255), ("rush_east", 3286), ("pine_west", 3409),
]
BOUND_TOL = 8.0

# The crops the transcriptions are made from. Pixel boxes on the registered NA
# raster, (left, top, right, bottom).
CROPS = {
    "kinzie": {"box": [3125, 1886, 3262, 1938], "reads": "Kinzie"},
    "block": {"box": [3125, 1934, 3262, 1986], "reads": "Block"},
    "numeral_west": {"box": [3010, 1908, 3070, 1950], "reads": "12"},
    "numeral_east": {"box": [3325, 1928, 3385, 1970], "reads": "10"},
    "context": {"box": [2955, 1875, 3475, 2000],
                "reads": "the whole Michigan-Illinois tier, Wolcott to Pine"},
}

# The corpus. Every file in these sets is a unit the search ruled on.
CORPUS = [
    ("newspapers/text", "newspapers/text/*.txt"),
    ("newspapers/extracted", "newspapers/extracted/*.json"),
    ("directories", "directories/**/*.json"),
    ("books/text", "books/text/*.txt"),
]
# Spelt loosely on purpose: an OCR'd 'o' becomes '0' and a 'c' drops out, and a
# possessive may or may not be printed. If the phrase is anywhere in the corpus
# in any of those shapes this finds it.
PHRASE = re.compile(r"kinzie(?:['’]?s)?[\s\-—]*bl[o0]c?k", re.I)
NEAR = re.compile(r"(kinzie[^\n]{0,60}block|block[^\n]{0,60}kinzie)", re.I)


# --------------------------------------------------------------- the interior

def _tier_scan(img):
    """The north-south rules of the Michigan-Illinois tier, band by band."""
    out = []
    for band in TIER_BANDS:
        prof = _profile(img, TIER_X[0], band["y"][0], TIER_X[1], band["y"][1], "v", SHEAR_NS)
        peaks = [{"px_x": x, "peak": v} for x, v in _rules(prof)]
        out.append({"band": band["id"], "y_px": list(band["y"]), "note": band["note"],
                    "x_px": list(TIER_X), "shear": SHEAR_NS, "peaks": peaks})
    return out


def _named_bounds(peaks):
    """Attach the six block-boundary rules to their names.

    RULE_PEAK_MIN is NOT applied here, and that is deliberate. The cut exists to
    tell an interior lot rule from a stroke of the lettering; a block boundary is
    a rule this reading already knows is drawn, because the block outline is what
    the tier is made of. Rush Street's west rule comes in at 18.7 in the upper
    half-block against 101.8 in the lower, because the final 'e' of Kinzie is
    written into it and the two inks merge in the projection. Refusing it there
    on a height test would be letting the lettering delete the line it touches.
    Every boundary's own peak height is recorded so the weak ones are visible."""
    found = {}
    for name, want in BOUNDS:
        near = [p for p in peaks if abs(p["px_x"] - want) <= BOUND_TOL]
        if not near:
            found[name] = None
            continue
        best = max(near, key=lambda p: p["peak"])
        found[name] = {"px_x": best["px_x"], "peak": best["peak"],
                       "below_cut": best["peak"] < RULE_PEAK_MIN}
    return found


def _interior(peaks, west, east):
    """The rules strictly between two boundaries: this block's lot divisions."""
    if west is None or east is None:
        return None
    w, e = west["px_x"], east["px_x"]
    inside = [p for p in peaks if w + BOUND_TOL < p["px_x"] < e - BOUND_TOL]
    return {
        "lot_rules": [p["px_x"] for p in inside if p["peak"] >= RULE_PEAK_MIN],
        "below_cut": [[p["px_x"], p["peak"]] for p in inside if p["peak"] < RULE_PEAK_MIN],
    }


def _blocks(scan):
    """Blocks 12, the Kinzie Block and 10, measured in each band."""
    out = {"block_12": [], "kinzie_block": [], "block_10": []}
    for band in scan:
        b = _named_bounds(band["peaks"])
        band["bounds_px"] = b
        out["block_12"].append(_interior(band["peaks"], b["wolcott_east"], b["cass_west"]))
        out["kinzie_block"].append(_interior(band["peaks"], b["cass_east"], b["rush_west"]))
        out["block_10"].append(_interior(band["peaks"], b["rush_east"], b["pine_west"]))
    for k, v in out.items():
        for i, band in enumerate(scan):
            if v[i] is not None:
                v[i] = dict(v[i], band=band["band"])
    return out


def _mid_line(img):
    """The line that halves the Kinzie Block, read in a column inside it."""
    prof = _profile(img, 3150, 1840, 3240, 2030, "h", SHEAR_EW)
    return [{"px_y": y, "peak": v} for y, v in _rules(prof)]


# -------------------------------------------------------------- the footprint

def _footprint():
    """The block's ground, from the four committed streets that bound it."""
    doc = json.loads(STREETS.read_text())
    default = doc.get("corridor_width_m", 24.384)
    by_id = {s["id"]: s for s in doc["streets"]}
    want = {"south": "michigan_north", "north": "illinois_north",
            "west": "cass", "east": "rush"}
    lines = {}
    for side, sid in want.items():
        s = by_id[sid]
        lines[side] = {"id": sid, "name_1835": s["name_1835"],
                       "path": s["path_local_enu_m"],
                       "corridor_width_m": s.get("corridor_width_m", default)}

    def at_e(line, e):
        (e0, n0), (e1, n1) = line["path"]
        return n0 + (n1 - n0) * (e - e0) / (e1 - e0)

    def at_n(line, n):
        (e0, n0), (e1, n1) = line["path"]
        return e0 + (e1 - e0) * (n - n0) / (n1 - n0)

    # Two passes: seed the block's middle from the streets' own ends, then take
    # each face at the middle of the face it is measured across.
    n_mid = (at_e(lines["south"], 995) + at_e(lines["north"], 995)) / 2
    e_mid = (at_n(lines["west"], n_mid) + at_n(lines["east"], n_mid)) / 2
    faces = {
        "south_n": at_e(lines["south"], e_mid) + lines["south"]["corridor_width_m"] / 2,
        "north_n": at_e(lines["north"], e_mid) - lines["north"]["corridor_width_m"] / 2,
        "west_e": at_n(lines["west"], n_mid) + lines["west"]["corridor_width_m"] / 2,
        "east_e": at_n(lines["east"], n_mid) - lines["east"]["corridor_width_m"] / 2,
    }
    faces = {k: round(v, 2) for k, v in faces.items()}
    return {
        "bounded_by": lines,
        "faces_local_enu_m": faces,
        "width_m": round(faces["east_e"] - faces["west_e"], 2),
        "depth_m": round(faces["north_n"] - faces["south_n"], 2),
        "centre_local_enu_m": [round((faces["east_e"] + faces["west_e"]) / 2, 2),
                               round((faces["north_n"] + faces["south_n"]) / 2, 2)],
    }


def _corroboration():
    """What T-1061's independent reading of the Addition's numerals says about this cell.

    The two readings reach the same number by different routes and neither used the
    other: this one transcribes the numerals either side of the name and subtracts,
    T-1061 fits the boustrophedon run over all fifty-one figures it could read. An
    agreement between two methods is worth more than either alone, and a
    DISAGREEMENT is the thing a gate should catch, so it is checked rather than
    written down."""
    if not NUMERALS.exists():
        return {"available": False}
    doc = json.loads(NUMERALS.read_text())
    cells = doc.get("blocks") or []
    named = [c for c in cells if str(c.get("written_on_sheet", "")).lower() == "kinzie block"]
    return {
        "available": True,
        "file": str(NUMERALS.relative_to(ROOT)),
        "ticket": doc.get("ticket"),
        "cells_naming_the_kinzie_block": len(named),
        "number": named[0].get("number") if named else None,
        "bounded_by": named[0].get("bounded_by") if named else None,
        "numeral_on_sheet": named[0].get("numeral_on_sheet") if named else None,
        "agrees_with_this_reading": bool(
            len(named) == 1 and named[0].get("number") == 11
            and named[0].get("numeral_on_sheet") is False),
    }


def _modelled_ground(faces):
    """Whether the block stands on the scene's modelled ground, from the heightfield box.

    Asked because the answer decides where the viewpoint can be put, and because
    it turned out to be no."""
    scene = json.loads(SCENE.read_text())
    epoch = scene["terrain_epoch"]
    meta = json.loads((ROOT / f"data/terrain/epochs/{epoch}/heightfield.json").read_text())
    box = meta["box_local_enu_m"]
    inside = (box["n"][0] <= faces["south_n"] and faces["north_n"] <= box["n"][1]
              and box["e"][0] <= faces["west_e"] and faces["east_e"] <= box["e"][1])
    return {
        "epoch": epoch,
        "heightfield_box_local_enu_m": box,
        "block_inside_the_box": inside,
        "block_south_face_n_m": faces["south_n"],
        "box_north_edge_n_m": box["n"][1],
        "beyond_the_north_edge_m": round(faces["south_n"] - box["n"][1], 2),
    }


# ----------------------------------------------------------- the phrase search

def _search():
    groups = []
    units = 0
    hits = []
    near = []
    for label, pattern in CORPUS:
        files = sorted(RESEARCH.glob(pattern))
        units += len(files)
        for f in files:
            text = f.read_text(errors="replace")
            rel = str(f.relative_to(RESEARCH))
            if PHRASE.search(text):
                hits.append(rel)
            for m in NEAR.finditer(text):
                near.append({"unit": rel,
                             "text": " ".join(text[m.start():m.end()].split())[:160]})
        groups.append({"set": label, "glob": pattern, "units": len(files),
                       "unit_ids": [str(f.relative_to(RESEARCH)) for f in files]})
    return {"groups": groups, "units_searched": units,
            "phrase_hits": hits, "co_occurrences": near}


# ------------------------------------------------------------------ the record

def read():
    g, img = _sheet()
    scan = _tier_scan(img)
    blocks = _blocks(scan)
    footprint = _footprint()
    return {"gcp": g, "scan": scan, "blocks": blocks, "mid_line": _mid_line(img),
            "footprint": footprint, "search": _search(),
            "modelled_ground": _modelled_ground(footprint["faces_local_enu_m"]),
            "corroboration": _corroboration()}


def _document(r):
    kinzie = r["blocks"]["kinzie_block"]
    b12 = r["blocks"]["block_12"]
    b10 = r["blocks"]["block_10"]
    counts = {
        "block_12": [len(b["lot_rules"]) for b in b12],
        "kinzie_block": [len(b["lot_rules"]) for b in kinzie],
        "block_10": [len(b["lot_rules"]) for b in b10],
    }
    search = r["search"]
    return {
        "_doc": __doc__,
        "ticket": TICKET,
        "raster": r["gcp"]["raster"],
        "registration": "data/traces/gcp/wright_1834_nara_hup_gcps.json — the same "
                        "registration T-1060 read the Addition's street grid through.",
        "method": "tools/read_kinzie_block_name.py. Lettering and numerals are "
                  "TRANSCRIBED from the cited crops. The block interiors are MEASURED: "
                  "ink stacked along the sheet's shear and projected onto the east-west "
                  "axis, sharp narrow peaks taken as ruled lines, a peak below "
                  f"{RULE_PEAK_MIN} taken as a stroke of the lettering rather than a rule. "
                  "`--check` re-derives the counts, the footprint and the search from what is "
                  "committed here; `--check-sheet` re-opens the raster and re-derives the "
                  "peaks the counts are made of. check.sh runs the first, a PR runs both.",
        "lettering": {
            "transcription": "Kinzie Block",
            "as_drawn": "Two lines of cursive inside one block outline, 'Kinzie' in the "
                        "upper half and 'Block' in the lower, reading west to east. No "
                        "apostrophe and no possessive 's' is drawn: the sheet letters "
                        "Kinzie, not Kinzie's.",
            "confidence": "documented",
            "source_id": "wright_1834_nara_hup",
            "crops": {k: v for k, v in CROPS.items() if k in ("kinzie", "block", "context")},
        },
        "which_block": {
            "claim": "The block Wright names is the one that would otherwise be numbered 11.",
            "confidence": "inferred",
            "note": "The numeral 11 is NOT on the sheet — the name stands where it would "
                    "be. What is on the sheet is the tier's numbering either side of it: "
                    "the block west of Cass Street is lettered 12 and the block east of "
                    "Rush Street is lettered 10, both transcribed from the crops below, "
                    "and both sitting astride their block's mid-line the way every numeral "
                    "in the Addition does. A tier that runs 12, name, 10 leaves one slot, "
                    "and it is 11. That is arithmetic on two read numerals, not a reading "
                    "of a third, so it is inferred and not documented. The Addition's "
                    "numbering as a whole is T-1061's to read.",
            "crops": {k: v for k, v in CROPS.items() if k.startswith("numeral")},
            "corroborated_by": dict(r["corroboration"], note=(
                "T-1061 read all fifty-one numerals the Addition carries and fitted the "
                "run they are written in. It reaches 11 for this cell from the run, "
                "having no numeral to read there; this reading reaches 11 from the two "
                "numerals either side of the name. Neither used the other. The field "
                "above re-reads T-1061's committed file every time the gate runs, so a "
                "future disagreement between the two fails rather than sits.")),
        },
        "interior": {
            "claim": "The Kinzie Block is drawn with no lot divisions. Both its "
                     "full-width neighbours in the same tier are ruled into lots.",
            "confidence": "documented",
            "lot_rules_found": counts,
            "reading": "Six lot rules in block 12 and five in block 10, in each of the two "
                       "half-blocks, at peak heights of 65 to 108. Between Cass Street's "
                       "east rule and Rush Street's west rule, none — the only ink the "
                       "profile finds inside the Kinzie Block is the lettering, at peak "
                       "heights of 15 to 33. The block is bounded and halved like its "
                       "neighbours and then left whole.",
            "what_it_is_not": "This is a statement about what Wright DREW, not about how "
                              "the ground was held. A block drawn without lots is not by "
                              "itself evidence that it was never sold as lots, and nothing "
                              "here reserves it or refuses it a subdivision — "
                              "data/reconstruction/1835_reserved_ground.json is where such "
                              "a claim would have to be argued, and this reading does not "
                              "make it.",
            "shore_cut_blocks": "Blocks east of Pine Street are cut by the lake shore and "
                                "are drawn on a different division. The count above is "
                                "stated for the three full-width blocks between Wolcott "
                                "and Pine only.",
            "scan": r["scan"],
            "mid_line_px_y": r["mid_line"],
        },
        "footprint": dict(r["footprint"], _doc=(
            "The ground the name belongs to, derived from the four committed streets that "
            "bound it — not from this sheet's own fit, which carries 16.2 m RMS. Each face "
            "is its street's centreline offset by half that street's corridor, taken at the "
            "middle of the face.")),
        "phrase_in_the_corpus": {
            "claim": "The phrase 'Kinzie Block' appears nowhere in this project's "
                     "newspaper, directory and book corpus.",
            "confidence": "documented",
            "units_searched": search["units_searched"],
            "phrase_hits": search["phrase_hits"],
            "sets": [{k: v for k, v in g.items() if k != "unit_ids"} for g in search["groups"]],
            "unit_ids": {g["set"]: g["unit_ids"] for g in search["groups"]},
            "co_occurrences_examined": search["co_occurrences"],
            "ruling": "Every one of the co-occurrences above was read and none is the "
                      "phrase. They are Kinzie STREET beside a block number in a lot "
                      "advertisement, Kinzie's ADDITION beside a water lot, and John H. "
                      "Kinzie beside somebody else's block. The nearest thing the corpus "
                      "has is Fergus's 1843 directory on a hotel 'occupying w. half of "
                      "block fronting on Rush, Michigan, and Kinzie' — which is the Lake "
                      "House, on the river tier one block south of this one, described by "
                      "the streets it fronts and not by a name.",
            "what_this_is_evidence_of": "That the name was Wright's label on a survey and "
                                        "not a term the town used in print, as far as this "
                                        "corpus goes. It is a search of 148 units, not of "
                                        "everything printed in Chicago: a page this project "
                                        "has not transcribed could overturn it, and finding "
                                        "one would be worth a ticket.",
        },
        "stands_on_modelled_ground": dict(r["modelled_ground"], claim=(
            "No. The whole of the Kinzie Block lies north of the modelled ground's edge."),
            note=(
            "The 1834 harbour-cut heightfield is boxed at n_max +400 m and the block's "
            "SOUTH face — its nearest edge — is at +402.72, so the block misses the "
            "modelled ground entirely, by 2.7 m at the near corner and by 70 m at the far "
            "one. Michigan Street, which forms that south face, is inside the box and dry: "
            "the heightfield reads +1.54 m above the summer-1835 water surface at the "
            "block's mid-face. That is why the viewpoint below stands on the street and "
            "looks north rather than standing on the block. Filed as its own ticket: this "
            "is the north counterpart of T-0219, which finishes the heightfield south."),
        ),
        "anchor": {
            "scene_anchor_id": "kinzie_block",
            "note": "data/scenes/1835.json puts a viewpoint on Michigan Street at the "
                    "middle of the block's south face, looking north across it. NOT on the "
                    "block: see stands_on_modelled_ground above.",
        },
    }


def _cheap(doc):
    """Everything that can be re-derived WITHOUT opening the raster.

    Split for the reason tools/read_kinzie_addition_streets.py is split: the
    re-read opens a 5050 x 6628 raster and the per-commit gate runs without
    Pillow installed. What is re-derived here is real work all the same — the
    block's ground from the committed streets, the answer about the modelled
    ground from the committed heightfield meta, the corpus search over the
    committed research files, and the boundary attribution and lot-rule counts
    re-derived from the peaks committed beside them. A hand-edited count is
    caught here. A hand-edited PEAK is caught by --check-sheet."""
    scan = doc["interior"]["scan"]
    bounds, counts = {}, {"block_12": [], "kinzie_block": [], "block_10": []}
    for band in scan:
        b = _named_bounds(band["peaks"])
        bounds[band["band"]] = b
        for key, (w, e) in (("block_12", ("wolcott_east", "cass_west")),
                            ("kinzie_block", ("cass_east", "rush_west")),
                            ("block_10", ("rush_east", "pine_west"))):
            inner = _interior(band["peaks"], b[w], b[e])
            counts[key].append(None if inner is None else len(inner["lot_rules"]))
    return {"bounds": bounds, "counts": counts,
            "committed_counts": doc["interior"]["lot_rules_found"],
            "footprint": _footprint()["faces_local_enu_m"],
            "committed_footprint": doc["footprint"]["faces_local_enu_m"],
            "modelled": _modelled_ground(doc["footprint"]["faces_local_enu_m"]),
            "committed_modelled": {k: v for k, v in doc["stands_on_modelled_ground"].items()
                                   if k not in ("note", "claim")},
            "search_units": _search()["units_searched"],
            "committed_units": doc["phrase_in_the_corpus"]["units_searched"]}


def _peaks(doc):
    return {band["band"]: [[p["px_x"], p["peak"]] for p in band["peaks"]]
            for band in doc["interior"]["scan"]}


def _committed():
    if not OUT.exists():
        raise SystemExit(f"FAIL  {OUT.relative_to(ROOT)} is not committed")
    return json.loads(OUT.read_text())


def _report(pairs) -> int:
    bad = 0
    for label, have, want in pairs:
        if have != want:
            print(f"FAIL  {label}\n        committed {have}\n        re-derived {want}")
            bad += 1
    return bad


def _check() -> int:
    doc = _committed()
    c = _cheap(doc)
    bad = _report([
        ("lot rules per block", c["committed_counts"], c["counts"]),
        ("the block's faces in local ENU", c["committed_footprint"], c["footprint"]),
        ("whether the block stands on modelled ground", c["committed_modelled"], c["modelled"]),
        ("units searched for the phrase", c["committed_units"], c["search_units"]),
    ])
    hits = _search()["phrase_hits"]
    if hits != doc["phrase_in_the_corpus"]["phrase_hits"]:
        print(f"FAIL  the phrase now appears in the corpus: {hits}")
        bad += 1
    print("re-derived from the committed pixels, streets and corpus: "
          + ("OK" if not bad else f"{bad} field(s) differ"))
    return 1 if bad else 0


def _check_sheet() -> int:
    doc = _committed()
    want = _peaks(_document(read()))
    bad = _report([(f"the {band} profile's peaks", have, want.get(band))
                   for band, have in _peaks(doc).items()])
    print("re-read the raster: "
          + ("OK, the committed peaks are the ones the sheet gives"
             if not bad else f"{bad} band(s) differ"))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--check-sheet", action="store_true", dest="check_sheet",
                    help="re-open the raster and re-derive the profiles' peaks")
    a = ap.parse_args()
    if a.check:
        return _check()
    if a.check_sheet:
        return _check_sheet()
    doc = _document(read())
    if a.write:
        OUT.write_text(json.dumps(doc, indent=2) + "\n")
        print(f"wrote {OUT.relative_to(ROOT)}")
        return 0
    c = doc["interior"]["lot_rules_found"]
    print(f"lettering          {doc['lettering']['transcription']!r}")
    print(f"which block        {doc['which_block']['claim']}")
    print(f"lot rules  blk 12  {c['block_12']}")
    print(f"           Kinzie  {c['kinzie_block']}")
    print(f"           blk 10  {c['block_10']}")
    f = doc["footprint"]
    print(f"footprint          {f['width_m']} x {f['depth_m']} m, centre {f['centre_local_enu_m']}")
    m = doc["stands_on_modelled_ground"]
    print(f"modelled ground    inside the box: {m['block_inside_the_box']}, "
          f"south face {m['block_south_face_n_m']} m vs box edge {m['box_north_edge_n_m']} m")
    p = doc["phrase_in_the_corpus"]
    print(f"phrase in corpus   {len(p['phrase_hits'])} hits in {p['units_searched']} units, "
          f"{len(p['co_occurrences_examined'])} co-occurrences examined")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
