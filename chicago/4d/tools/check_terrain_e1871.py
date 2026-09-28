#!/usr/bin/env python3
"""Re-derive the e1871_postfire terrain spec from its readings, and hold its zone table (T-1251).

    python3 tools/check_terrain_e1871.py --check    # check (also the default)
    python3 tools/check_terrain_e1871.py --write    # write the spec's DERIVED fields back
    python3 tools/check_terrain_e1871.py --self-test

`data/terrain/epochs/e1871_postfire/terrain_spec.json` is authored, but three kinds of
figure in it are not the author's to type, and this derives all three:

* every street crown is a reading in `data/terrain/e1871_grade_readings.json` put through
  the spec's own datum conversion -- a crown that stops matching its reading fails;
* the fill at each crown is the crown minus the committed 1835 heightfield at the same
  point, and it FAILS IF IT IS CONSTANT -- the ticket's second clause is that the two
  epochs are not offsets of one another, and that is only a claim while a check can
  catch it becoming false;
* the evidence limit is derived from the readings and the traced shoreline, not carried
  over from 1835 (whose N -2149.4 is about 1835 ground).

It also holds the zone table's discipline the way the 1835 spec is held: every block that
states an elevation cites a research zone that exists as a heading in the research doc,
no land elevation is attested, a reconstructed block says why, every source resolves, and
every block says which date it describes. Standard library only; reads the 1835
heightfield's int16 file with `array`, so it needs no numpy.
"""
from __future__ import annotations

import argparse
import array
import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TERRAIN = ROOT / "data" / "terrain"
SPEC_PATH = TERRAIN / "epochs" / "e1871_postfire" / "terrain_spec.json"
READINGS_PATH = TERRAIN / "e1871_grade_readings.json"
SHORE_PATH = TERRAIN / "epochs" / "e1871_postfire" / "shoreline.geojson"
HF1835 = TERRAIN / "epochs" / "e1834_harbor_cut"
SOURCES = ROOT / "data" / "sources"
FT = 0.3048
HALF_BLOCK_M = 50.0          # the evidence limit sits this far past the last used crown
CONFIRM_WITHIN_FT = 0.4      # a standing house's walk must read this close to its street's crown
PRAIRIE_BAND_M = 40.0        # a walk is "on Prairie" within this of the avenue's crowns
MIN_FILL_RANGE_FT = 1.0      # below this the fill would be an offset in all but name
ZONED = ("vertical", "lake_surface", "street_crowns", "graded_ground", "fill", "earthworks",
         "made_ground", "lake_shelf", "original_surface", "surface_texture", "relationship_to_1835")
GRADED = ("lake_surface", "street_crowns", "graded_ground", "fill", "earthworks", "made_ground",
          "lake_shelf", "original_surface", "surface_texture")


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def hf1835_ft(e: float, n: float) -> float:
    meta = load(HF1835 / "heightfield.json")
    raw = array.array("h")
    raw.frombytes((HF1835 / "heightfield.bin").read_bytes())
    if sys.byteorder != "little":
        raw.byteswap()
    cols, cell = meta["cols"], meta["cell_m"]
    c = (e - meta["origin_e"]) / cell
    r = (n - meta["origin_n"]) / cell
    c0, r0 = int(c), int(r)
    fc, fr = c - c0, r - r0

    def at(rr, cc):
        return raw[rr * cols + cc] * meta["scale"] + meta["offset"]

    v = (at(r0, c0) * (1 - fc) * (1 - fr) + at(r0, c0 + 1) * fc * (1 - fr)
         + at(r0 + 1, c0) * (1 - fc) * fr + at(r0 + 1, c0 + 1) * fc * fr)
    return v / FT


def derived(spec: dict, readings: dict, shore: dict) -> dict:
    conv = spec["vertical"]["navd88_to_internal_ft"]
    rd = {r["id"]: r for r in readings["readings"]}
    used = [r for r in readings["readings"] if r["role"] == "street_crown" and r["use"] == "used"]
    prairie = [r for r in used if r["id"].startswith("prairie_")]
    walks = [r for r in readings["readings"] if r["role"] == "house_frontage" and r["use"] == "confirms"]

    def crown_near(n: float) -> float:
        ps = sorted(prairie, key=lambda r: r["local_n"], reverse=True)
        for a, b in zip(ps, ps[1:]):
            if b["local_n"] <= n <= a["local_n"]:
                t = (n - a["local_n"]) / (b["local_n"] - a["local_n"])
                return a["navd88_ft"] + t * (b["navd88_ft"] - a["navd88_ft"])
        return min(ps, key=lambda r: abs(r["local_n"] - n))["navd88_ft"]

    on_prairie = [w for w in walks
                  if min(abs(w["local_e"] - p["local_e"]) for p in prairie) <= PRAIRIE_BAND_M]
    diffs = {w["id"]: round(w["navd88_ft"] - crown_near(w["local_n"]), 2) for w in on_prairie}
    good = [w for w in on_prairie if abs(diffs[w["id"]]) <= CONFIRM_WITHIN_FT]
    reach = ([round(max(w["local_n"] for w in good) + 25.0, 1), round(min(w["local_n"] for w in good) - 25.0, 1)]
             if good else [None, None])

    crowns = []
    for r in used:
        confirmed = bool(good) and r in prairie and reach[1] <= r["local_n"] <= reach[0]
        crowns.append({"reading": r["id"], "e_m": r["local_e"], "n_m": r["local_n"],
                       "crown_ft": round(r["navd88_ft"] + conv, 2),
                       "research_zone": 3 if confirmed else 4,
                       "confidence": "inferred" if confirmed else "reconstructed"})
    fill = {c["reading"]: round(c["crown_ft"] - hf1835_ft(c["e_m"], c["n_m"]), 2) for c in crowns}
    segF = next(s for s in next(f for f in shore["features"] if f["id"] == "shore_1904_ic_edge")
                ["properties"]["segments"] if s["id"] == "F")
    return {
        "crowns": crowns,
        "fill_ft": fill,
        "walk_minus_crown_ft": diffs,
        "confirmed_reach": reach,
        "evidence_south_of_n_m": round(min(r["local_n"] for r in used) - HALF_BLOCK_M, 1),
        "shore_south_of_n_m": segF["n_from"],
        "crown_range_ft": [min(c["crown_ft"] for c in crowns), max(c["crown_ft"] for c in crowns)],
    }


def write_derived(spec: dict, d: dict) -> dict:
    s = copy.deepcopy(spec)
    byr = {c["reading"]: c for c in d["crowns"]}
    for c in s["street_crowns"]:
        dc = byr[c["reading"]]
        for k in ("e_m", "n_m", "crown_ft", "research_zone", "confidence"):
            c[k] = dc[k]
    s["fill"]["depth_ft_at_crowns"] = d["fill_ft"]
    s["fill"].pop("depth_ft_at_controls", None)
    lim = s["evidence_limit"]
    lim["south_of_n_m"] = d["evidence_south_of_n_m"]
    lim["shore_south_of_n_m"] = d["shore_south_of_n_m"]
    lim["confirmed_reach"] = {"n_from_m": d["confirmed_reach"][0], "n_to_m": d["confirmed_reach"][1],
                              "walk_minus_crown_ft": d["walk_minus_crown_ft"]}
    s["graded_ground"]["range_ft"] = d["crown_range_ft"]
    return s


def zones_in_doc(spec: dict) -> set[int]:
    text = (ROOT / spec["research_doc"]).read_text(encoding="utf-8")
    return {int(m) for m in re.findall(r"^## Zone (\d+)\b", text, re.M)}


def blocks(spec: dict):
    for key in ZONED:
        v = spec.get(key)
        if isinstance(v, dict):
            yield key, key, v
        elif isinstance(v, list):
            for item in v:
                yield key, f"{key}.{item.get('id') or item.get('reading')}", item


def validate(spec: dict, readings: dict, shore: dict) -> list[str]:
    bad: list[str] = []
    d = derived(spec, readings, shore)
    if write_derived(spec, d) != spec:
        bad.append("the spec's derived fields (crowns, fill, evidence limit, range) are not what its readings "
                   "derive -- re-run tools/check_terrain_e1871.py --write, or revert a hand edit")
    fills = list(d["fill_ft"].values())
    if max(fills) - min(fills) < MIN_FILL_RANGE_FT:
        bad.append(f"the post-fire fill is constant to within {max(fills) - min(fills):.2f} ft: the two epochs "
                   "would be an offset of one another, which the spec says they are not")
    if not any(c["research_zone"] == 3 for c in d["crowns"]):
        bad.append("no crown is confirmed by a standing house, so zone 3's inference has nothing under it")
    zones = zones_in_doc(spec)
    sources = {p.stem for p in SOURCES.glob("*.json")}
    for group, cid, b in blocks(spec):
        z = b.get("research_zone")
        if z is None:
            bad.append(f"{cid} cites no research zone")
        elif z not in zones:
            bad.append(f"{cid} cites research zone {z}, which {spec['research_doc']} does not have")
        if group in GRADED:
            conf = b.get("confidence")
            if conf not in ("attested", "inferred", "reconstructed"):
                bad.append(f"{cid} has confidence {conf!r}")
            if conf == "attested":
                bad.append(f"{cid} is attested: no land elevation in this spec is, and the caveat says so")
            if conf in ("inferred", "reconstructed") and not str(b.get("note", "")).strip():
                bad.append(f"{cid} is {conf} and says nothing about why")
            if not b.get("describes"):
                bad.append(f"{cid} does not say which date it describes")
            for sid in b.get("sources", []) or []:
                if sid not in sources:
                    bad.append(f"{cid} cites unresolved source {sid!r}")
    ev = spec["evidence_limit"]
    if ev.get("south_of_n_m") == -2149.4:
        bad.append("the evidence limit is the 1835 one, inherited rather than derived")
    return bad


def self_test(spec, readings, shore) -> int:
    cases = []
    s = copy.deepcopy(spec)
    s["street_crowns"][0]["crown_ft"] += 0.5
    cases.append(("a hand-edited crown fails", bool(validate(s, readings, shore))))
    r = copy.deepcopy(readings)
    for x in r["readings"]:
        if x["role"] == "street_crown" and x["use"] == "used":
            x["navd88_ft"] = 592.0
    cases.append(("a flat reading set is caught as an offset or as drift", bool(validate(spec, r, shore))))
    s = copy.deepcopy(spec)
    s["lake_shelf"]["research_zone"] = 99
    cases.append(("citing a research zone the doc does not have fails", bool(validate(s, readings, shore))))
    s = copy.deepcopy(spec)
    s["graded_ground"]["confidence"] = "attested"
    cases.append(("an attested land elevation fails", bool(validate(s, readings, shore))))
    s = copy.deepcopy(spec)
    s["evidence_limit"]["south_of_n_m"] = -2149.4
    cases.append(("inheriting the 1835 evidence limit fails", bool(validate(s, readings, shore))))
    r = copy.deepcopy(readings)
    for x in r["readings"]:
        if x["role"] == "house_frontage":
            x["navd88_ft"] += 3.0
    cases.append(("houses that no longer stand at their street's grade leave zone 3 unconfirmed",
                  bool(validate(spec, r, shore))))
    for label, ok in cases:
        print(("   ok   " if ok else "   FAIL ") + label)
    return 0 if all(ok for _, ok in cases) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true", help="re-derive and compare (the default; named so the gate says what it asks)")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    spec, readings, shore = load(SPEC_PATH), load(READINGS_PATH), load(SHORE_PATH)
    if a.self_test:
        return self_test(spec, readings, shore)
    if a.write:
        spec = write_derived(spec, derived(spec, readings, shore))
        SPEC_PATH.write_text(json.dumps(spec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    bad = validate(spec, readings, shore)
    for b in bad:
        print("FAIL", b)
    if not bad:
        d = derived(spec, readings, shore)
        z3 = sum(c["research_zone"] == 3 for c in d["crowns"])
        print(f"OK e1871_postfire re-derives: {len(d['crowns'])} crowns ({z3} confirmed by standing houses), "
              f"Z {d['crown_range_ft'][0]}-{d['crown_range_ft'][1]} ft; fill {min(d['fill_ft'].values())}-"
              f"{max(d['fill_ft'].values())} ft over 1835, not an offset; evidence limit N "
              f"{d['evidence_south_of_n_m']} (grade), N {d['shore_south_of_n_m']} (shore)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
