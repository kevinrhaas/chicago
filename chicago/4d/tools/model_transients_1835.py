#!/usr/bin/env python3
"""THE TRANSIENT COHORT OF 1 JULY 1835: who was in the town that day and not of it.

T-1352, piece 1 of T-1178. The town model (T-1293) bounds the town's RESIDENTS and
says so in terms; the land-sale crowd, the immigrants waiting on lots, the harbour
gang and the crews ashore are a separate population that the order book (T-1166)
carries as one unapportioned row. This bounds that row and says where it slept.

    tools/model_transients_1835.py --build       write the model and its report
    tools/model_transients_1835.py --check       re-derive both and refuse any drift
    tools/model_transients_1835.py --self-test   the guards, fired on fixtures

WHAT THIS TOOL IS. An ADJUDICATION over committed claim records and committed derived
files. It opens no scan and no network, and it names, ages and houses nobody: what it
returns is a bracket, a composition and a list of sleeping places. It WRITES NO PERSON
— that is T-1353, and the standing constraint's own rule applies there and not here.

WHY THE COHORT IS NOT IN THE TOWN MODEL. Because a transient is not a resident and the
census that a resident model is built from does not count one. Chicago's own enumerator
drew that line himself: the census of 1 August 1843 prints `Transient persons` as a row
of its own, 533 against a permanent 7,047, and Norris's remarks on the same census say
he excluded every person not permanently residing in the city. Folding the two together
is exactly the error he says the 1835 figure of 5,500 made.

THE SCENE DATE CATCHES A FALLING TIDE, AND THAT IS THE FINDING. The federal land sale
at Chicago closed on 27 June 1835 — 232 of the register's 274 June entries fall on the
26th and the 27th — and the Democrat of 1 July, printed on the scene date itself, says
the sale 'has passed'. The crowd of 1 July is a draining sale crowd on top of a
navigation-season immigrant stream that was still landing: the Marine Journal has
vessels in with passengers on 28 and 29 June and again on 2 and 3 July. The two move in
opposite directions across the day and no committed source measures either, which is
why this model declines a point reading and says so rather than splitting the
difference and calling it an answer.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "data" / "reconstruction" / "1835_transient_cohort.json"
REPORT = ROOT / "docs" / "RESEARCH" / "1835_transient_cohort.md"
CAMPS = ROOT / "data" / "reconstruction" / "1835_camp_grounds.json"
VESSELS = ROOT / "data" / "reconstruction" / "1835_vessels_in_port.json"

TOWN_MODEL = ROOT / "data" / "reconstruction" / "1835_town_model.json"
ENTRIES = ROOT / "data" / "research" / "land_sales" / "entries.json"
CROSSWALK = ROOT / "data" / "research" / "land_sales" / "resident_crosswalk.json"
FERGUS_1843 = ROOT / "data" / "research" / "directories" / "claims" / "fergus_1843_civic.json"
NORRIS_1844 = ROOT / "data" / "research" / "directories" / "claims" / "norris_1844_town_findings.json"
PAPERS = ROOT / "data" / "research" / "newspapers" / "extracted"
BROWN = ROOT / "data" / "residents" / "households" / "hh_brown_rufus.json"
BUSINESS_INDEX = ROOT / "data" / "businesses" / "index.json"

SCENE_DATE = "1835-07-01"
SALE_DAYS = ("1835-06-26", "1835-06-27")
SALE_MONTH = "1835-06"

# "Strangers, to the a[mo]unt of some hundreds more" — the American of 13 June 1835.
# A PHRASE IS NOT A NUMBER, and turning this one into a band is the largest liberty in
# this file (docs/LIBERTIES.md L245). Two hundred is the least a plural of hundreds can
# carry; nine hundred is the most, because an editor with a thousand strangers in his
# streets writes "a thousand" and this one did not.
SOME_HUNDREDS = (200, 900)

# Norris's own remarks on the census of 1 August 1843: the town "might have been made
# much larger than it appears to be ... undoubtedly 8,500, by including a class of
# transitory persons". Held to that wording by the guard in `build_size`.
NORRIS_1843_WITH_TRANSIENTS = 8500

# The Marine Journal of the Chicago American, 4 July 1835 (claim c008). The reading used
# to be a pair of lists typed into this file, under a comment promising a `guard_port_
# reading` that was never written: the hulls' names, masters, cargoes and last ports had
# nowhere to live, and nothing held the constants to the extraction. T-1372 moved the
# reading to `data/reconstruction/1835_vessels_in_port.json`, where each hull is a record
# with its own provenance, and `check_vessels` below is the guard the comment promised —
# every entry is held to the column's own words, so a re-extraction that drops them fails
# the gate instead of leaving the table quietly stale.

CAMP_CONFIDENCE = ("documented", "inferred", "conjectural")
VESSEL_CONFIDENCE = CAMP_CONFIDENCE
VESSEL_EVENTS = ("arrived", "cleared")
NO_COORDINATE = ("coordinates", "polygon", "vertices", "local_enu_m")


class Fault(Exception):
    """A defect in the inputs, phrased for the person who must fix it."""


# ---------------------------------------------------------------------------
# a figure — the same contract the town model keeps, and deliberately so


def figure(name: str, low, high, method: str, comparanda: list[str],
           derived_from: list[str], point=None) -> dict:
    """One bounded answer. A range whose ends are equal is a COUNT, not an estimate."""
    if low > high:
        raise Fault(f"figure '{name}' is inverted: {low} > {high}")
    if not method.strip():
        raise Fault(f"figure '{name}' states no method")
    if not derived_from:
        raise Fault(f"figure '{name}' names no file it was derived from")
    if point is not None and not (low <= point <= high):
        raise Fault(f"figure '{name}' puts its point reading {point} outside [{low}, {high}]")
    return {"figure": name, "low": low, "high": high, "point": point,
            "is_a_count": low == high, "method": method,
            "comparanda": comparanda, "derived_from": derived_from}


def section(key: str, title: str, figures: list[dict], not_claiming: str,
            open_questions: list[str], tables: dict | None = None) -> dict:
    """A page, not a paper. Every section says what it is NOT claiming, in one sentence."""
    if not figures:
        raise Fault(f"section '{key}' carries no figure")
    if not not_claiming.strip():
        raise Fault(f"section '{key}' does not say what it is not claiming")
    if not_claiming.count(".") > 1:
        raise Fault(f"section '{key}' takes more than one sentence to say what it is not claiming")
    return {"key": key, "title": title, "figures": figures,
            "not_claiming": not_claiming, "open_questions": open_questions,
            "tables": tables or {}}


# ---------------------------------------------------------------------------
# reading the committed record


def read_json(path: Path) -> dict:
    if not path.exists():
        raise Fault(f"the model cannot read {path.relative_to(ROOT)} — it is not in the tree")
    return json.loads(path.read_text(encoding="utf-8"))


def claim(doc: dict, claim_id: str, where: str) -> dict:
    for c in doc.get("claims", []):
        if c.get("id") == claim_id:
            return c
    raise Fault(f"{where} no longer carries claim '{claim_id}', which this model rests on")


def plain(text: str) -> str:
    """OCR restorations are printed in brackets. A guard must not depend on them."""
    return re.sub(r"\s+", " ", (text or "").replace("[", "").replace("]", ""))


def says(text: str, needle: str, where: str) -> None:
    if needle.lower() not in plain(text).lower():
        raise Fault(f"{where} no longer says '{needle}' — this model quotes it and the "
                    f"reading must be re-taken before the figure that rests on it stands")


def town_figure(model: dict, section_key: str, name: str) -> dict:
    for s in model.get("sections", []):
        if s.get("key") == section_key:
            for f in s.get("figures", []):
                if f.get("figure") == name:
                    return f
    raise Fault(f"the town model no longer carries {section_key}/{name}")


def load(root: Path = ROOT):
    global ROOT
    if root != ROOT:  # the self-test points the loader at a tree that does not exist
        raise Fault(f"the model cannot read its inputs under {root}")
    return (read_json(TOWN_MODEL), read_json(ENTRIES), read_json(CROSSWALK),
            read_json(FERGUS_1843), read_json(NORRIS_1844),
            read_json(PAPERS / "chicago_american_1835_06_13.json"),
            read_json(PAPERS / "chicago_democrat_1835_06_17.json"),
            read_json(PAPERS / "chicago_democrat_1835_07_01.json"),
            read_json(PAPERS / "chicago_american_1835_07_04.json"),
            read_json(PAPERS / "chicago_american_1835_06_20.json"),
            read_json(CAMPS), BROWN.read_text(encoding="utf-8") if BROWN.exists() else "",
            read_json(VESSELS))


# ---------------------------------------------------------------------------
# the land sale, counted rather than remembered


def sale_crowd(entries: dict, crosswalk: dict) -> dict:
    rows = entries.get("entries") or []
    if not rows:
        raise Fault("the land-sale register carries no entry, so the sale crowd has "
                    "nothing to stand on")
    matched = {m.get("purchaser_as_read") for m in crosswalk.get("matches", [])}
    if not matched:
        raise Fault("the land-sale resident crosswalk matches nobody, so every purchaser "
                    "would read as a stranger and the floor would be fiction")
    june = {r["purchaser_as_read"] for r in rows
            if (r.get("date_purchased") or "").startswith(SALE_MONTH)}
    sale = {r["purchaser_as_read"] for r in rows
            if (r.get("date_purchased") or "") in SALE_DAYS}
    june_rows = sum(1 for r in rows if (r.get("date_purchased") or "").startswith(SALE_MONTH))
    sale_rows = sum(1 for r in rows if (r.get("date_purchased") or "") in SALE_DAYS)
    return {
        "june_rows": june_rows, "sale_day_rows": sale_rows,
        "june_purchasers": len(june), "sale_day_purchasers": len(sale),
        "june_in_the_layer": len(june & matched),
        "june_not_in_the_layer": len(june - matched),
        "sale_day_in_the_layer": len(sale & matched),
        "sale_day_not_in_the_layer": len(sale - matched),
    }


def port_on_the_scene_date(vessels: dict) -> dict:
    """In on or before the scene date, not cleared before it — one row per HULL.

    A hull entered inbound twice is one hull, which is what makes six arrivals out of
    the column's seven inbound lines. Nothing is hard-coded here: the window and the
    dedup rule are the authored file's own, stated in `the_counting_window` and
    `the_dedup_rule`, and `check_vessels` holds every entry to the extraction.
    """
    in_port, at_nightfall, cleared_on = [], [], []
    for v in vessels.get("vessels") or []:
        arrivals = sorted(e["date"] for e in v["entries"] if e["event"] == "arrived"
                          and e["date"] <= SCENE_DATE)
        clearances = [e["date"] for e in v["entries"] if e["event"] == "cleared"]
        if not arrivals or any(d < SCENE_DATE for d in clearances):
            continue
        first = next(e for e in v["entries"]
                     if e["event"] == "arrived" and e["date"] == arrivals[0])
        row = (arrivals[0], v["display_name"], v["rig"],
               (v.get("master") or {}).get("surname"), first.get("port"),
               first.get("cargo"),
               (v.get("register_business") or {}).get("business_id"))
        in_port.append(row)
        if SCENE_DATE in clearances:
            cleared_on.append(v["display_name"])
        else:
            at_nightfall.append(row)
    if not in_port:
        raise Fault("the port reading puts no hull at Chicago on the scene date, so the "
                    "composition has nothing to count")
    return {"in_port": in_port, "still_at_nightfall": at_nightfall,
            "cleared_on_the_day": sorted(cleared_on)}


# ---------------------------------------------------------------------------
# the vessels file, validated rather than generated — the guard the old constants'
# comment promised and never had


def check_vessels(vessels: dict, journal: str, corroborant: str) -> dict:
    """Hold every hull to the shipping column's own words, and to the refusals."""
    rows = vessels.get("vessels") or []
    if not rows:
        raise Fault("the vessels file enters no hull, so the port reading counts nothing")
    reach = vessels.get("the_reach_they_lay_in") or {}
    if reach.get("confidence") not in VESSEL_CONFIDENCE:
        raise Fault(f"the reach the hulls lay in is graded '{reach.get('confidence')}', "
                    f"which is not one of {list(VESSEL_CONFIDENCE)}")
    refs = reach.get("resolves_from") or []
    if not refs:
        raise Fault("the reach names no committed geometry to resolve from, so a hull "
                    "would have to be moored by hand")
    for ref in refs:
        if not (ROOT / ref).exists():
            raise Fault(f"the reach resolves from '{ref}', which is not in the tree")
    if (vessels.get("the_crew_this_file_refuses") or {}).get("complement") is not None:
        raise Fault("the vessels file has acquired a crew complement — no committed source "
                    "in this corpus gives one, and a hull multiplied by a guess is an "
                    "invention. Cite the source in the file before the refusal is lifted")

    seen = set()
    for v in rows + (vessels.get("entered_but_outside_the_window") or []):
        vid = v.get("id")
        if not vid or vid in seen:
            raise Fault(f"vessel '{vid}' has no id or repeats one")
        seen.add(vid)
        for lat in NO_COORDINATE:
            if lat in v:
                raise Fault(f"vessel '{vid}' authors '{lat}' — this file authors no "
                            f"coordinate and every hull seats to the reach")
        if v.get("berth") is not None:
            raise Fault(f"vessel '{vid}' claims a berth. No committed source gives one of "
                        f"these hulls a landing; a berth read off a cargo is a mooring "
                        f"invented whole")
        if v.get("crew") is not None:
            raise Fault(f"vessel '{vid}' carries a crew. T-1352 priced this row 'hulls "
                        f"only' and no source has changed that")

    documented = 0
    for v in rows:
        vid = v["id"]
        if v.get("confidence") not in VESSEL_CONFIDENCE:
            raise Fault(f"vessel '{vid}' is graded '{v.get('confidence')}', which is not "
                        f"one of {list(VESSEL_CONFIDENCE)}")
        if v["confidence"] == "documented":
            documented += 1
            if not v.get("claim_ids"):
                raise Fault(f"vessel '{vid}' is graded documented and cites no claim — "
                            f"only a shipping column that enters her may carry that grade")
        entries = v.get("entries") or []
        if not entries:
            raise Fault(f"vessel '{vid}' is entered on no line of any column")
        for e in entries:
            if e.get("event") not in VESSEL_EVENTS:
                raise Fault(f"vessel '{vid}' carries an event '{e.get('event')}', which is "
                            f"not one of {list(VESSEL_EVENTS)}")
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", e.get("date") or ""):
                raise Fault(f"vessel '{vid}' carries an undated line")
            says(journal, e["verbatim"], f"the Marine Journal of 4 July 1835, for '{vid}'")
        master = (v.get("master") or {}).get("surname")
        if master and v.get("corroborated_by"):
            says(corroborant, master,
                 f"the Marine Journal of 20 June 1835, which '{vid}' cites as corroboration")

    for v in vessels.get("entered_but_outside_the_window") or []:
        if not (v.get("why_outside") or "").strip():
            raise Fault(f"vessel '{v['id']}' is held outside the window and does not say why")
        says(journal, v["verbatim"],
             f"the Marine Journal of 4 July 1835, for '{v['id']}'")

    joined = check_register_join(vessels)

    return {"hulls": len(rows), "documented": documented,
            "outside_the_window": len(vessels.get("entered_but_outside_the_window") or []),
            "in_the_register": joined}


def check_register_join(vessels: dict) -> list[str]:
    """T-1425: every hull says whether the business layer holds a house for it.

    THE JOIN IS AN IDENTITY RULING AND THE GUARD TREATS IT AS ONE. A `business_id` must
    name a record `data/businesses/index.json` actually carries, so a compile that
    renames or retires a house takes this file red instead of leaving a dangling id; it
    may never be graded `documented`, because no source says in words that the
    register's packet and the column's hull are one vessel; and where the two runs spell
    the name differently the divergence must be WRITTEN, not normalised away — that is
    data/sources/chicago_american_1835.json's own rule that a disagreement between two
    witnesses is the finding. A hull with no house must still say so and why: the whole
    point of the field is that no hull is passed over in silence.
    """
    if not BUSINESS_INDEX.exists():
        raise Fault("the business index is not in the tree, so no hull can be joined to a "
                    "house; run tools/compile_businesses.py --build")
    known = {b["id"]: b for b in read_json(BUSINESS_INDEX).get("businesses") or []}
    joined = []
    for v in (vessels.get("vessels") or []) + (
            vessels.get("entered_but_outside_the_window") or []):
        vid = v["id"]
        join = v.get("register_business")
        if not isinstance(join, dict):
            raise Fault(f"vessel '{vid}' does not say whether the register holds a house "
                        f"for her. Every hull carries `register_business`, with a null "
                        f"`business_id` and a reason where it does not")
        if not (join.get("basis") or "").strip():
            raise Fault(f"vessel '{vid}' joins to the register with no basis printed")
        bid = join.get("business_id")
        if bid is None:
            for key in ("name_in_the_register", "confidence", "spelling_divergence",
                        "what_the_column_adds"):
                if join.get(key) is not None:
                    raise Fault(f"vessel '{vid}' holds no register house and still carries "
                                f"'{key}' — a refused join says nothing but why")
            continue
        if bid not in known:
            raise Fault(f"vessel '{vid}' joins to business '{bid}', which "
                        f"data/businesses/index.json does not carry")
        if join.get("confidence") == "documented":
            raise Fault(f"vessel '{vid}' grades its register join documented. No source "
                        f"says the register's house and this hull are one vessel; the "
                        f"join is reasoned and `inferred` is its ceiling")
        if join.get("confidence") not in VESSEL_CONFIDENCE:
            raise Fault(f"vessel '{vid}' grades its register join "
                        f"'{join.get('confidence')}', which is not one of "
                        f"{list(VESSEL_CONFIDENCE)}")
        printed = join.get("name_in_the_register")
        if not printed:
            raise Fault(f"vessel '{vid}' joins to a register house and does not carry the "
                        f"name that house is printed under")
        if v["display_name"].lower() not in printed.lower() and not (
                join.get("spelling_divergence") or "").strip():
            raise Fault(f"vessel '{vid}' is printed '{printed}' in the register and "
                        f"'{v['display_name']}' in the column, and the divergence is not "
                        f"written down. Two witnesses that disagree are a finding, not a "
                        f"spelling to be picked")
        joined.append(bid)
    if len(set(joined)) != len(joined):
        raise Fault("two hulls claim the same register house; one house is one vessel")
    return sorted(joined)


# ---------------------------------------------------------------------------
# the camp grounds file, validated rather than generated


def check_camps(camps: dict) -> dict:
    cands = camps.get("candidates") or []
    if not cands:
        raise Fault("the camp-grounds file offers no candidate, so the cohort has "
                    "nowhere to sleep and T-1214 has nothing to place")
    seen = set()
    for c in cands:
        cid = c.get("id")
        if not cid or cid in seen:
            raise Fault(f"camp ground '{cid}' has no id or repeats one")
        seen.add(cid)
        if c.get("confidence") not in CAMP_CONFIDENCE:
            raise Fault(f"camp ground '{cid}' is graded '{c.get('confidence')}', which is "
                        f"not one of {list(CAMP_CONFIDENCE)}")
        if not (c.get("why") or "").strip():
            raise Fault(f"camp ground '{cid}' gives no sentence that suggested it")
        if c.get("confidence") == "documented" and not c.get("claim_ids"):
            raise Fault(f"camp ground '{cid}' is graded documented and cites no claim — "
                        f"only a source that says people slept there may carry that grade")
        if c.get("confidence") != "documented" and c.get("claim_ids"):
            raise Fault(f"camp ground '{cid}' cites a claim and is not graded documented")
        refs = c.get("resolves_from") or []
        if not refs:
            raise Fault(f"camp ground '{cid}' names no committed geometry to resolve from, "
                        f"so its extent would have to be typed by hand")
        for ref in refs:
            if not (ROOT / ref).exists():
                raise Fault(f"camp ground '{cid}' resolves from '{ref}', which is not in "
                            f"the tree")
        for lat in ("coordinates", "polygon", "vertices", "local_enu_m"):
            if lat in c:
                raise Fault(f"camp ground '{cid}' authors '{lat}' — this file authors no "
                            f"coordinate and T-1214 resolves every extent")
    documented = [c["id"] for c in cands if c["confidence"] == "documented"]
    return {"candidates": len(cands), "documented": documented,
            "conjectural": [c["id"] for c in cands if c["confidence"] == "conjectural"]}


# ---------------------------------------------------------------------------
# the three sections


def build_size(town, entries, crosswalk, fergus, norris, amer_0613, dem_0701) -> dict:
    residents = town_figure(town, "population", "population_on_1_july_1835")
    r_low, r_high, r_point = residents["low"], residents["high"], residents["point"]

    transient_1843 = claim(fergus, "f1843c0314", "the 1843 census table")
    pop_1843 = claim(fergus, "f1843c0315", "the 1843 census table")
    t43 = int(transient_1843["normalized"]["total"])
    p43 = int(pop_1843["normalized"]["total"])
    if transient_1843["normalized"]["row"] != "Transient persons":
        raise Fault("claim f1843c0314 is no longer the census's `Transient persons` row")
    if t43 >= p43:
        raise Fault(f"the 1843 census returns {t43:,} transient persons out of {p43:,}, "
                    f"which cannot be")
    permanent_1843 = p43 - t43
    ratio_1843 = t43 / permanent_1843
    if NORRIS_1843_WITH_TRANSIENTS <= p43:
        raise Fault(f"Norris's larger 1843 reading of {NORRIS_1843_WITH_TRANSIENTS:,} is "
                    f"not larger than the printed total of {p43:,}")
    also_excluded = NORRIS_1843_WITH_TRANSIENTS - p43
    ratio_1843_high = (t43 + also_excluded) / permanent_1843

    says(claim(norris, "n1844_tf_029", "Norris 1844")["quote"], "5,500", "Norris 1844 leaf 23")
    norris_1843 = claim(norris, "n1844_tf_061", "Norris 1844")["quote"]
    says(norris_1843, "transitory", "Norris 1844 leaf 85")
    says(norris_1843, "8,500", "Norris 1844 leaf 85")
    says(amer_0613_text := claim(amer_0613, "c001", "the American of 13 June 1835")["normalized"],
         "between 2500 and 3000", "the American of 13 June 1835")
    says(amer_0613_text, "some hundreds more", "the American of 13 June 1835")
    says(claim(dem_0701, "c020", "the Democrat of 1 July 1835")["normalized"],
         "this sale has passed", "the Democrat of 1 July 1835")

    sale = sale_crowd(entries, crosswalk)
    floor = int(round(r_point * ratio_1843))
    ceiling = SOME_HUNDREDS[1]
    if floor > ceiling:
        raise Fault(f"the 1843 ratio puts {floor:,} transients in the town and the "
                    f"American's own phrase will not carry more than {ceiling:,}")

    doubled = int(round(r_point * ratio_1843 * 2))
    midpoint = (SOME_HUNDREDS[0] + SOME_HUNDREDS[1]) // 2

    figures = [
        figure("residents_on_1_july_1835", r_low, r_high,
               "CARRIED, not derived. The town model's own reading, repeated here because "
               "the transient bracket is stated against it and a reader must not have to "
               "hold two files open to see what it is a fraction of.",
               ["andreas_1884_v1"], ["data/reconstruction/1835_town_model.json"],
               point=r_point),
        figure("the_papers_own_estimate_13_june_1835", 2500, 3000,
               "The Chicago American of 13 June 1835, eighteen days before the scene: the "
               "actual population 'we cannot estimate with any degree of accuracy, but it "
               "is now supposed to be between 2500 and 3000'. An estimate that says it is "
               f"one. The town model's point reading of {r_point:,} — built five years "
               "later out of a November census and an arrival distribution, and knowing "
               "nothing of this sentence — falls inside it.",
               ["chicago_american_1835_06_13"],
               ["data/research/newspapers/extracted/chicago_american_1835_06_13.json"]),
        figure("strangers_the_american_counts_separately", SOME_HUNDREDS[0], SOME_HUNDREDS[1],
               "The same sentence goes on: 'Strangers, to the amount of some hundreds more, "
               "fill our public houses and streets'. MORE — the paper puts the strangers "
               "OUTSIDE its own population estimate, which is the whole distinction this "
               f"model is built on. The band is the phrase's own arithmetic: {SOME_HUNDREDS[0]} "
               "is the least a plural of hundreds can carry and "
               f"{SOME_HUNDREDS[1]} the most, because an editor with a thousand strangers "
               "in his streets writes 'a thousand'. Turning the phrase into a band is a "
               "liberty and is recorded as docs/LIBERTIES.md L245.",
               ["chicago_american_1835_06_13"],
               ["data/research/newspapers/extracted/chicago_american_1835_06_13.json"]),
        figure("transient_persons_counted_at_chicago_1843", t43, t43,
               "The census of 1 August 1843, taken by Jas. W. Norris under the authority of "
               f"the Common Council, prints `Transient persons` as a row of its own: {t43:,} "
               f"across six wards, in a printed total of {p43:,}. The only time Chicago's "
               "own enumerator counted the two populations apart, and the reason this model "
               "exists as a separate file.",
               ["fergus_chicago_directory_1843"],
               ["data/research/directories/claims/fergus_1843_civic.json"]),
        figure("transient_rate_of_a_chicago_summer_1843", round(ratio_1843, 5),
               round(ratio_1843_high, 5),
               f"TWO READINGS OF ONE CENSUS. The printed table puts {t43:,} transient "
               f"persons against {permanent_1843:,} permanent ones, which is "
               f"{ratio_1843:.2%}; Norris's own remarks on the same census say every person "
               "not permanently residing was excluded and that counting them would have "
               f"made the town 'undoubtedly {NORRIS_1843_WITH_TRANSIENTS:,}', which is "
               f"{also_excluded:,} more again and {ratio_1843_high:.2%}. Whether those are "
               "the same people counted twice is not settled here. It is a rate and not a "
               "population, and it is taken on 1 August 1843 — a boom year, mid-season, and "
               "no land sale.",
               ["fergus_chicago_directory_1843", "norris_directory_1844"],
               ["data/research/directories/claims/fergus_1843_civic.json",
                "data/research/directories/claims/norris_1844_town_findings.json"]),
        figure("named_purchasers_at_the_sale_the_layer_cannot_place",
               sale["sale_day_not_in_the_layer"], sale["june_not_in_the_layer"],
               "MEASURED, and a floor three times over. The Public Domain Land Tract Sales "
               f"register enters {sale['sale_day_rows']:,} purchases at Chicago on 26 and 27 "
               f"June 1835 — four days before the scene — from {sale['sale_day_purchasers']:,} "
               f"distinct purchasers, of whom the resident crosswalk can place only "
               f"{sale['sale_day_in_the_layer']:,} in this town's own layer. Over June as a "
               f"whole the figures are {sale['june_purchasers']:,} and "
               f"{sale['june_in_the_layer']:,}. It is a floor because a purchaser the "
               "crosswalk refuses is one the layer cannot NAME rather than one proved "
               "absent, because a man at a land sale travelled with agents and family, and "
               "because most of a land-sale crowd buys nothing at all.",
               ["illinois_state_archives_land_tract_sales"],
               ["data/research/land_sales/entries.json",
                "data/research/land_sales/resident_crosswalk.json"]),
        figure("transients_on_1_july_1835", floor, ceiling,
               f"FLOOR: {ratio_1843:.2%} — the LOWER of the two 1843 rates above, the one "
               "Chicago's own enumerator printed — applied to this model's resident point "
               f"of {r_point:,}, which gives "
               f"{floor:,}. The higher reading of the same census would give "
               f"{int(round(r_point * ratio_1843_high)):,}. It is a floor and not an "
               "estimate because 1 July 1835 is not an "
               "ordinary day: the federal land sale closed four days earlier, the navigation "
               "season was at its height, and the same enumerator says the crowd of 1835 "
               "inflated the town's own reckoning of itself by thousands. CEILING: "
               f"{ceiling:,}, the most the American's 'some hundreds more' will carry, "
               "written in the town in the month itself. NO POINT READING: see the section's "
               "open questions — a draining sale crowd and a landing immigrant stream cross "
               "on this day in opposite directions, no committed source measures either, and "
               "a midpoint would be a number nobody could defend dressed as an answer.",
               ["chicago_american_1835_06_13", "fergus_chicago_directory_1843"],
               ["data/research/newspapers/extracted/chicago_american_1835_06_13.json",
                "data/research/directories/claims/fergus_1843_civic.json",
                "data/reconstruction/1835_town_model.json"]),
    ]

    tables = {
        "the_two_candidate_points": {
            "unit": "persons, on 1 July 1835 — NEITHER is adopted here",
            "note": "T-1353 must spend a number and this model will not pick one for it. "
                    "These are the two that can be argued from committed evidence; whichever "
                    "it takes, it cites this table and says which.",
            "rows": [
                {"reading": "twice the 1843 rate", "persons": doubled,
                 "argument": "1 July 1835 is a land-sale week and 1 August 1843 was not, so "
                             "the measured rate is doubled. The multiplier is invented and "
                             "nothing in the record sets it."},
                {"reading": "the midpoint of the American's phrase", "persons": midpoint,
                 "argument": "'Some hundreds more' read at the middle of its own band. An "
                             "editor's impression, printed eighteen days before the scene "
                             "and before the sale crowd arrived."},
            ],
        },
        "the_land_sale_as_the_register_prints_it": {
            "unit": "entries and distinct purchasers, Chicago land office",
            "rows": [
                {"window": "June 1835, whole month", "entries": sale["june_rows"],
                 "purchasers": sale["june_purchasers"],
                 "in the resident layer": sale["june_in_the_layer"],
                 "not in it": sale["june_not_in_the_layer"]},
                {"window": "26-27 June 1835, the sale days",
                 "entries": sale["sale_day_rows"],
                 "purchasers": sale["sale_day_purchasers"],
                 "in the resident layer": sale["sale_day_in_the_layer"],
                 "not in it": sale["sale_day_not_in_the_layer"]},
            ],
        },
        "the_ceiling_this_model_refuses": {
            "line": "n1844_tf_029",
            "what_it_says": "Norris, writing in 1844: in 1835 'the population of the place "
                            "was said to amount to 5,500, a computation which probably "
                            "included transitory persons, a great many of whom were here at "
                            "the time. The actual population, however, that year, could not "
                            "have been much less than 3000.'",
            "the_arithmetic_it_offers": "5,500 less 3,000 is 2,500 transients, which would "
                                        "be a ceiling four times the one adopted here.",
            "why_it_is_refused": "Norris does not stand behind the 5,500 — it is what the "
                                 "population 'was said to amount to', nine years before he "
                                 "wrote — and the Chicago American, printing in the town in "
                                 "the month itself, put the WHOLE population at 2,500 to "
                                 "3,000 with the strangers counted on top of it. A "
                                 "recollected rumour does not outrank a contemporary "
                                 "estimate, and the figure is recorded here rather than "
                                 "dropped so that a reader can disagree.",
        },
    }

    questions = [
        "This model declines a point reading, and that is a refusal rather than an "
        "omission. The sale closed on 27 June and the Democrat of 1 July says it 'has "
        "passed', so the sale crowd is leaving; the Marine Journal has vessels in with "
        "passengers on 28 and 29 June and again on 2 and 3 July, so the immigrant stream "
        "is still landing. Nothing committed measures the rate of either, and the answer "
        "is a band.",
        f"The two readings of the same 1843 census disagree. The printed table carries "
        f"{t43:,} transient persons INSIDE a total of {p43:,}; Norris's own remarks on that "
        "census say every person not permanently residing was excluded and that including "
        "them would have made the town 'undoubtedly 8,500'. Whether the 533 and the ~920 "
        "are the same people counted twice or two different exclusions is not settled here, "
        f"and the second reading would put the floor at "
        f"{int(round(r_point * ratio_1843_high)):,} instead of {floor:,}.",
        "The floor derived from the 1843 rate sits just below the least value the "
        f"American's phrase can carry ({floor:,} against {SOME_HUNDREDS[0]}). Two arguments "
        "that share no evidence landing that close together is the best corroboration this "
        "model has, and it is not a confirmation: both could be low.",
        "The register's residence column reads UNKNOWN on every June 1835 row, so a "
        "purchaser the crosswalk cannot place is a purchaser this project cannot name at "
        "Chicago — never a purchaser shown to have come from elsewhere.",
    ]
    return section("size", "How many", figures, "This section does not say that any named "
                   "person was a transient, and the land-sale purchasers it counts are a "
                   "measurement of the register rather than a roll of the crowd.",
                   questions, tables)


def build_composition(sale: dict, port: dict, vessel_stats: dict) -> dict:
    in_port = port["in_port"]
    at_nightfall = port["still_at_nightfall"]
    figures = [
        figure("vessels_lying_at_chicago_on_1_july_1835", len(at_nightfall), len(in_port),
               "The Marine Journal of the Chicago American, 4 July 1835, three days after "
               f"the scene. {len(in_port)} vessels had arrived on 27, 28 and 29 June and "
               "were not entered as cleared before 1 July; two of them, the Philips and the "
               "Jesse Smith, cleared on the day itself, so "
               f"{len(at_nightfall)} lay at Chicago at nightfall. The hulls are SEATED — "
               f"{vessel_stats['hulls']} records in "
               "data/reconstruction/1835_vessels_in_port.json, each with the master, last "
               "port and cargo the column prints and a mooring that resolves to the reach "
               "and never to a deck — and this figure is re-derived from them. THE MODEL "
               "COUNTS VESSELS AND NOT MEN: no committed source gives the crew of a Great "
               "Lakes schooner of 1835, and multiplying a hull by a guessed complement "
               "would turn a reading into an invention.",
               ["chicago_american_1835_07_04"],
               ["data/reconstruction/1835_vessels_in_port.json",
                "data/research/newspapers/extracted/chicago_american_1835_07_04.json"]),
        figure("named_land_sale_purchasers_still_owed_a_bed",
               sale["sale_day_not_in_the_layer"], sale["june_not_in_the_layer"],
               "The same measurement as the size section's floor, carried here as the one "
               "row of the composition that has a number at all. Every other row below is "
               "bounded by nothing committed and says so.",
               ["illinois_state_archives_land_tract_sales"],
               ["data/research/land_sales/entries.json",
                "data/research/land_sales/resident_crosswalk.json"]),
    ]
    tables = {
        "who_the_cohort_was": {
            "unit": "rows of the cohort — `bounded` says whether anything committed sets a size",
            "rows": [
                {"row": "land-sale visitors and their agents",
                 "bounded": "floor only",
                 "evidence": "the register's own purchasers, 26-27 June 1835",
                 "at the scene date": "draining — the Democrat of 1 July says the sale has passed"},
                {"row": "immigrant families awaiting lots",
                 "bounded": "no",
                 "evidence": "the American, 13 June 1835: 'men, women and children just "
                             "landed from the vessels', 'the unsheltered emigrants'",
                 "at the scene date": "still landing — vessels in with passengers 28, 29 June, 2, 3 July"},
                {"row": "the harbour-works gang",
                 "bounded": "no",
                 "evidence": "the federal harbour improvement was at work through 1835; no "
                             "committed source gives its strength in any month",
                 "at the scene date": "at work"},
                {"row": "crews ashore",
                 "bounded": "hulls only",
                 "evidence": "the Marine Journal of 4 July 1835, seated hull by hull in "
                             "data/reconstruction/1835_vessels_in_port.json, and joined to "
                             "the two packets the newspaper register already carried as "
                             "houses of trade (T-1425)",
                 "at the scene date": f"{len(at_nightfall)} to {len(in_port)} vessels in "
                                      f"port, named and mastered; nobody aboard"},
                {"row": "travellers of business and of state",
                 "bounded": "no",
                 "evidence": "the Democrat of 1 July 1835 names Lewis Cass, Secretary of "
                             "War, arrived on the 29th in the steamer Michigan, 'among the "
                             "numerous visitors to Chicago'",
                 "at the scene date": "present"},
            ],
        },
        "the_port_on_the_scene_date": {
            "unit": "vessels, from the Marine Journal of 4 July 1835, re-derived from the "
                    "seated hulls in data/reconstruction/1835_vessels_in_port.json",
            "rows": [{"arrived": r[0], "vessel": r[1], "rig": r[2],
                      "master": r[3] or "not read", "from": r[4] or "cut from the column",
                      "cargo": r[5] or "not stated",
                      "cleared 1 July": "no" if r in at_nightfall else "yes",
                      # T-1425. Two of these hulls trade under a name the register prints,
                      # and the business layer could see neither of them until the join was
                      # made; the other four are silences in the register and not gaps here.
                      # The identity ruling itself is `inferred` and lives on the hull,
                      # where the reading is.
                      "house in the register": r[6] or "none"}
                     for r in in_port],
        },
    }
    questions = [
        "Four of the five rows have no size and this model does not give them one. The "
        "harbour works were the largest employer in the town and their 1835 strength is not "
        "in any file this project holds; the Chief Engineer's annual report for 1835 would "
        "settle it and is named in docs/research/01-terrain-hydrology as the thing to find.",
        "A crew complement for an 1830s lake schooner would turn the port reading into a "
        "number of men. This model refuses to supply one from general knowledge; T-1353 "
        "seated no crews, and T-1372 seated the hulls and left them empty. Everything but "
        "the number is now in place — the vessels file names the hulls and the transient "
        "cards carry a `lodged_at` rung of kind `vessel` — so an enrolment return, a "
        "shipping article or a marine list that prints hands as well as hulls would finish "
        "it without anything being unpicked.",
        "The steamboat that arrived on 29 June is unnamed in the extraction; the Democrat "
        "of 1 July has Lewis Cass arriving that day in the steamer Michigan, and the "
        "American has the Michigan clearing on the 26th. The likeliest reading is that the "
        "two entries are the same vessel returned, and the model neither merges them nor "
        "claims they are distinct.",
    ]
    return section("composition", "Who they were", figures,
                   "This section apportions nobody between its rows and no row here is a "
                   "quota.", questions, tables)


def build_sleeping(camps: dict, camp_stats: dict, brown_text: str) -> dict:
    documented = len(camp_stats["documented"])
    figures = [
        figure("sleeping_place_classes_the_sources_name", 6, 6,
               "Six, and each is a sentence in a committed source rather than a class this "
               "model invented: a room in a public house; the floor of that room; the floor "
               "of a private house; a store house thrown open; the open sky upon the "
               "wharves; a tent pitched at the landing. The vessels in port are a seventh "
               "place and are counted in the composition section instead, because a hull is "
               "a hull whether or not anybody slept in it.",
               ["chicago_american_1835_06_13", "chicago_democrat_1835_06_17"],
               ["data/research/newspapers/extracted/chicago_american_1835_06_13.json",
                "data/research/newspapers/extracted/chicago_democrat_1835_06_17.json"]),
        figure("camp_ground_candidates", camp_stats["candidates"], camp_stats["candidates"],
               f"The authored candidates file offers {camp_stats['candidates']} grounds, of "
               f"which {documented} is graded documented — the landing place, where the "
               "American says the tents were pitched — and the rest conjectural. The file "
               "authors no coordinate: each candidate names the committed geometry its "
               "extent resolves from, and T-1214 places the camps.",
               [], ["data/reconstruction/1835_camp_grounds.json"]),
    ]
    tables = {
        "where_they_slept": {
            "unit": "one row per class, with the sentence that establishes it",
            "rows": [
                {"place": "a room in a public house", "source": "the Democrat, 17 June 1835",
                 "says": "'the immense congregation of strangers crowding every room of our "
                         "public houses, and every room in which they can obtain "
                         "accommodations'"},
                {"place": "the floor of that room", "source": "the Democrat, 17 June 1835",
                 "says": "'even to the extent of sleeping on the floor'"},
                {"place": "the floor of a private house",
                 "source": "hh_brown_rufus, on Mrs Rufus Brown's boarding house",
                 "says": "'full meant three in a bed sometimes, with the floor covered "
                         "besides'"},
                {"place": "a store house thrown open", "source": "the American, 13 June 1835",
                 "says": "'even some store houses have been thrown open to receive the "
                         "unsheltered emigrants'"},
                {"place": "the open sky upon the wharves",
                 "source": "the American, 13 June 1835",
                 "says": "'who had else remained under the open sky upon the wharves'"},
                {"place": "a tent at the landing place",
                 "source": "the American, 13 June 1835",
                 "says": "'Some build tents upon the spot they were landed from the boats'"},
            ],
        },
        "camp_ground_candidates": {
            "unit": "grounds offered to T-1214 — a candidate is not a placement",
            "rows": [{"id": c["id"], "name": c["name"], "confidence": c["confidence"],
                      "refused to a builder":
                          ", ".join(c.get("refused_to_a_builder") or []) or "—"}
                     for c in camps["candidates"]],
        },
    }
    questions = [
        "A refusal in 1835_no_build_ground.json is a refusal to a BUILDER and this model "
        "does not read it as a refusal to a camp: the United States Reservation carried no "
        "lot line and no street, and a crowd sleeping rough on it for a fortnight asked "
        "nobody's leave. Whether that reading is right is T-1214's to settle on the ground.",
        "Four of the five candidate grounds are conjectural and would stay conjectural even "
        "if T-1214 placed a camp on every one of them — placing a thing does not raise the "
        "evidence for it.",
        "Two of the candidates stand on ground the terrain and lot layers have not reached "
        "(T-1193, T-1194). Until they do, those candidates are a direction rather than an "
        "extent, and T-1214 may find it has nowhere to put them.",
    ]
    if brown_text and "floor covered besides" not in brown_text:
        raise Fault("hh_brown_rufus no longer carries 'floor covered besides', which this "
                    "model quotes as the evidence for a private floor")
    return section("where_they_slept", "Where they slept", figures,
                   "This section places no camp and gives no ground a capacity.",
                   questions, tables)


def build(town, entries, crosswalk, fergus, norris, amer_0613, dem_0617, dem_0701,
          amer_0704, amer_0620, camps, brown_text, vessels) -> dict:
    says(claim(dem_0617, "c001", "the Democrat of 17 June 1835")["normalized"],
         "immense congregation of strangers", "the Democrat of 17 June 1835")
    says(claim(dem_0701, "c009", "the Democrat of 1 July 1835")["normalized"],
         "Secretary of War", "the Democrat of 1 July 1835")
    journal = claim(amer_0704, "c008", "the American of 4 July 1835")["normalized"]
    for needle in ("June 27", "June 28", "CLEARED", "Jesse Smith", "Llewelling", "Whig"):
        says(journal, needle, "the Marine Journal of 4 July 1835")

    corroborant = claim(amer_0620, "c012", "the American of 20 June 1835")["normalized"]
    camp_stats = check_camps(camps)
    vessel_stats = check_vessels(vessels, journal, corroborant)
    sale = sale_crowd(entries, crosswalk)
    sections = [
        build_size(town, entries, crosswalk, fergus, norris, amer_0613, dem_0701),
        build_composition(sale, port_on_the_scene_date(vessels), vessel_stats),
        build_sleeping(camps, camp_stats, brown_text),
    ]
    return {
        "$schema_note": "DERIVED — regenerate with tools/model_transients_1835.py --build; "
                        "tools/check.sh re-derives it. Do not hand-edit: every figure is a "
                        "function of a committed file named in its own `derived_from`.",
        "id": "chicago_july_1835_transient_cohort",
        "ticket": "T-1352",
        "parent": "T-1178",
        "target_date": SCENE_DATE,
        "generated_by": "tools/model_transients_1835.py --build",
        "not_a_reading": "an adjudication over committed claim records and committed derived "
                         "files — no scan is opened here, and nobody is named, aged or housed",
        "writes_no_person": "T-1353 mints the cohort; this file bounds it. Nothing here is "
                            "evidence about any person, household or building, and no card "
                            "may cite it.",
        "spent_by": "T-1353, which mints the cohort, and T-1214, which places the camps",
        "tolerance": "Every figure is a range with a stated method and a named comparandum, "
                     "and where the record bounds nothing the row says so instead of "
                     "carrying an invented number. The headline figure has NO point reading "
                     "on purpose: the evidence supports a band and not a number, and a band "
                     "is the answer.",
        "inputs": [
            "data/reconstruction/1835_camp_grounds.json",
            "data/reconstruction/1835_vessels_in_port.json",
            "data/reconstruction/1835_town_model.json",
            "data/research/directories/claims/fergus_1843_civic.json",
            "data/research/directories/claims/norris_1844_town_findings.json",
            "data/research/land_sales/entries.json",
            "data/research/land_sales/resident_crosswalk.json",
            "data/research/newspapers/extracted/chicago_american_1835_06_13.json",
            "data/research/newspapers/extracted/chicago_american_1835_06_20.json",
            "data/research/newspapers/extracted/chicago_american_1835_07_04.json",
            "data/research/newspapers/extracted/chicago_democrat_1835_06_17.json",
            "data/research/newspapers/extracted/chicago_democrat_1835_07_01.json",
            "data/residents/households/hh_brown_rufus.json",
        ],
        "sections": sections,
    }


# ---------------------------------------------------------------------------
# the report


def _range(f: dict) -> str:
    fmt = (lambda v: f"{v:,}" if isinstance(v, int) else f"{v:g}")
    if f["is_a_count"]:
        return f"**{fmt(f['low'])}**"
    point = f" (point reading **{fmt(f['point'])}**)" if f["point"] is not None else ""
    return f"**{fmt(f['low'])} – {fmt(f['high'])}**{point}"


def report_text(doc: dict) -> str:
    out = ["# The transient cohort of 1 July 1835", "",
           "**T-1352**, piece 1 of **T-1178**. Who was in the town on the scene date and "
           "not of it: how many, who they were, and where they slept — each figure a range "
           "with its method and its comparanda, and no person written.", "",
           "Derived file: `data/reconstruction/1835_transient_cohort.json`  ",
           "Candidate grounds: `data/reconstruction/1835_camp_grounds.json` (authored)  ",
           "Hulls in port: `data/reconstruction/1835_vessels_in_port.json` (authored) — "
           "seated to the reach, carrying nobody  ",
           f"Built and gated by: `{doc['generated_by'].replace(' --build', '')} "
           "--build | --check | --self-test`  ",
           f"Spent by: {doc['spent_by']}", "", "---", "",
           "## The tolerance, stated first", "", doc["tolerance"], "",
           "It is " + doc["not_a_reading"] + ". " + doc["writes_no_person"], ""]

    for n, s in enumerate(doc["sections"], 1):
        out += [f"## {n}. {s['title']}", ""]
        out += ["| Figure | Reading | Method |", "| --- | ---: | --- |"]
        for f in s["figures"]:
            out.append(f"| `{f['figure']}` | {_range(f)} | {f['method']} |")
        out += ["", f"**Not claiming.** {s['not_claiming']}", ""]
        for name, table in s["tables"].items():
            out += [f"### {name.replace('_', ' ')}", ""]
            rows = table.get("rows")
            if isinstance(rows, list) and rows:
                cols = list(rows[0].keys())
                out += ["| " + " | ".join(c.replace("_", " ") for c in cols) + " |",
                        "| " + " | ".join("---" for _ in cols) + " |"]
                for r in rows:
                    out.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
            for k, v in table.items():
                if k in ("rows", "unit"):
                    continue
                out.append(f"- **{k.replace('_', ' ')}** — {v}")
            if table.get("unit"):
                out.append(f"- **unit** — {table['unit']}")
            out.append("")
        if s["open_questions"]:
            out += ["**Open questions.** These are recorded here and do not become tickets.", ""]
            for q in s["open_questions"]:
                out.append(f"- {q}")
            out.append("")

    out += ["---", "", "## What this model may not do", "",
            "- **write a person.** T-1353 mints the cohort; this file bounds it, and "
            "`--self-test` refuses a build that names a record;",
            "- **inflate the residents.** A transient is in the town and not of it, and the "
            "town census must go on reporting the two apart;",
            "- **place a camp.** The candidate grounds are offered to T-1214, which may "
            "refuse every one of them;",
            "- **man a hull.** The vessels file seats the hulls and `--self-test` refuses "
            "one that acquires a crew or a berth;",
            "- **pick the point reading for T-1353.** Two candidates are printed with their "
            "arguments and neither is adopted here.",
            "", "## Inputs", ""]
    for path in doc["inputs"]:
        out.append(f"- `{path}`")
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# commands


def cmd_build() -> int:
    doc = build(*load())
    MODEL.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report_text(doc), encoding="utf-8")
    head = _fig(doc["sections"][0], "transients_on_1_july_1835")
    print(f"OK: 1835 transient cohort — {head['low']:,}–{head['high']:,} persons, "
          f"{len(doc['sections'])} sections, "
          f"{sum(len(s['figures']) for s in doc['sections'])} figures")
    return 0


def _fig(sec: dict, name: str) -> dict:
    for f in sec["figures"]:
        if f["figure"] == name:
            return f
    raise Fault(f"section '{sec['key']}' no longer carries '{name}'")


def cmd_check() -> int:
    expected = build(*load())
    faults = []
    if not MODEL.exists():
        faults.append("the 1835 transient cohort model is missing — run --build")
    elif json.loads(MODEL.read_text(encoding="utf-8")) != expected:
        faults.append("the 1835 transient cohort model is stale — run --build")
    if not REPORT.exists():
        faults.append("the 1835 transient cohort report is missing — run --build")
    elif REPORT.read_text(encoding="utf-8") != report_text(expected):
        faults.append("the 1835 transient cohort report is stale — run --build")
    if faults:
        for f in faults:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1
    head = _fig(expected["sections"][0], "transients_on_1_july_1835")
    camps = _fig(expected["sections"][2], "camp_ground_candidates")
    print(f"OK: 1835 transient cohort — {head['low']:,}–{head['high']:,} persons on "
          f"{SCENE_DATE}, no point reading, {camps['low']} candidate grounds")
    return 0


def cmd_self_test() -> int:
    args = load()
    fired = 0

    def _fires(mutated, why):
        nonlocal fired
        try:
            build(*mutated)
        except Fault:
            fired += 1
            print(f"   fires: {why}")
            return
        raise AssertionError(f"did not fire: {why}")

    # THE QUOTED SENTENCE IS THE FIGURE. Every reading this model rests on is held to
    # the words it quotes, so a re-extraction that drops them fails the gate instead of
    # leaving a figure standing on a sentence the corpus no longer carries.
    a = list(copy.deepcopy(args))
    for c in a[5]["claims"]:
        if c["id"] == "c001":
            c["normalized"] = "The actual population is unknown."
    _fires(a, "the American of 13 June no longer saying 'some hundreds more'")

    a = list(copy.deepcopy(args))
    for c in a[3]["claims"]:
        if c["id"] == "f1843c0314":
            c["normalized"]["row"] = "Something else"
    _fires(a, "the 1843 census row that counts transients separately being renamed")

    # THE FLOOR IS A FRACTION OF A POPULATION, and a 1843 return with more transients
    # than people is a corrupt input rather than a very transient town.
    a = list(copy.deepcopy(args))
    for c in a[3]["claims"]:
        if c["id"] == "f1843c0314":
            c["normalized"]["total"] = "99999"
    _fires(a, "an 1843 return with more transient persons than people")

    # THE MEASURED FLOOR MUST BE MEASURED. An empty crosswalk would make every
    # purchaser in the register read as a stranger, which is a fiction and not a floor.
    a = list(copy.deepcopy(args)); a[2]["matches"] = []
    _fires(a, "a land-sale crosswalk that can place nobody")
    a = list(copy.deepcopy(args)); a[1]["entries"] = []
    _fires(a, "a land-sale register with no entry")

    # THE CAMP GROUNDS FILE AUTHORS NO COORDINATE, and a candidate graded `documented`
    # must cite the source that says people slept there.
    a = list(copy.deepcopy(args)); a[10]["candidates"][0]["claim_ids"] = []
    _fires(a, "a camp ground graded documented that cites no claim")
    a = list(copy.deepcopy(args)); a[10]["candidates"][1]["confidence"] = "certain"
    _fires(a, "a camp ground graded outside the vocabulary")
    a = list(copy.deepcopy(args)); a[10]["candidates"][1]["polygon"] = [[0, 0]]
    _fires(a, "a camp ground that authors its own polygon")
    a = list(copy.deepcopy(args))
    a[10]["candidates"][2]["resolves_from"] = ["data/nothing/at/all.json"]
    _fires(a, "a camp ground resolving from a file that is not in the tree")
    a = list(copy.deepcopy(args)); a[10]["candidates"] = []
    _fires(a, "a camp grounds file that offers no candidate")

    # THE HULLS ARE SEATED AND EMPTY. The port reading is a count of vessels, and the two
    # ways it could quietly become a count of men — a complement on the file, a crew on a
    # hull — are the first two guards here. The rest hold the reading to the column.
    a = list(copy.deepcopy(args))
    a[12]["the_crew_this_file_refuses"]["complement"] = 7
    _fires(a, "a vessels file that has acquired a crew complement")
    a = list(copy.deepcopy(args)); a[12]["vessels"][0]["crew"] = 7
    _fires(a, "a hull that carries a crew")
    a = list(copy.deepcopy(args)); a[12]["vessels"][0]["berth"] = "newberry_dole_landing"
    _fires(a, "a hull moored to a landing no source gives it")
    a = list(copy.deepcopy(args))
    a[12]["vessels"][0]["local_enu_m"] = [0, 0]
    _fires(a, "a hull that authors its own coordinate")
    a = list(copy.deepcopy(args))
    a[12]["vessels"][0]["entries"][0]["verbatim"] = "Schr Jesse Smith, Drurian, from Buffalo"
    _fires(a, "a hull entered on words the shipping column does not carry")
    a = list(copy.deepcopy(args))
    a[12]["vessels"][2]["master"]["surname"] = "Clarkson"
    _fires(a, "a master the corroborating column of 20 June does not name")
    a = list(copy.deepcopy(args)); a[12]["vessels"][0]["claim_ids"] = []
    _fires(a, "a hull graded documented that cites no claim")
    a = list(copy.deepcopy(args)); a[12]["vessels"][0]["entries"][0]["date"] = "27 June"
    _fires(a, "a hull entered on an undated line")
    a = list(copy.deepcopy(args)); a[12]["vessels"] = []
    _fires(a, "a vessels file that enters no hull")
    a = list(copy.deepcopy(args))
    a[12]["the_reach_they_lay_in"]["resolves_from"] = ["data/nothing/at/all.json"]
    _fires(a, "a reach resolving from a file that is not in the tree")
    a = list(copy.deepcopy(args))
    for v in a[12]["vessels"]:
        v["entries"] = [e for e in v["entries"] if e["event"] != "arrived"]
    _fires(a, "a port reading that puts no hull at Chicago on the scene date")

    # THE TOWN MODEL IS THE DENOMINATOR. Lose its July figure and the bracket has
    # nothing to be a fraction of.
    a = list(copy.deepcopy(args)); a[0]["sections"] = []
    _fires(a, "a town model that no longer carries the July population")

    # THE FIGURE CONTRACT, the same one the town model keeps.
    for bad, why in ((dict(method="  "), "a figure that states no method"),
                     (dict(derived_from=[]), "a figure derived from no file"),
                     (dict(low=9, high=1), "an inverted range")):
        kwargs = dict(name="x", low=1, high=2, method="m", comparanda=[], derived_from=["p"])
        kwargs.update(bad)
        try:
            figure(**kwargs)
            raise AssertionError(f"did not fire: {why}")
        except Fault:
            fired += 1
            print(f"   fires: {why}")
    try:
        figure("x", 1, 3, "m", [], ["p"], point=9)
        raise AssertionError("did not fire: a point reading outside its range")
    except Fault:
        fired += 1
        print("   fires: a point reading outside its range")
    try:
        section("k", "T", [figure("x", 1, 2, "m", [], ["p"])], "One. Two.", [])
        raise AssertionError("did not fire: a two-sentence refusal")
    except Fault:
        fired += 1
        print("   fires: a refusal that takes more than one sentence")
    try:
        load(Path("/nonexistent-root-for-the-self-test"))
        raise AssertionError("did not fire: a missing input tree")
    except Fault:
        fired += 1
        print("   fires: an input tree the model cannot read")

    doc = build(*args)
    assert len(doc["sections"]) == 3, doc["sections"]

    # THE PORT FIGURE IS RE-DERIVED FROM THE SEATED HULLS. Retire one and the figure must
    # move with it, which is what says the reading is read and not remembered.
    port = _fig(doc["sections"][1], "vessels_lying_at_chicago_on_1_july_1835")
    a = list(copy.deepcopy(args)); a[12]["vessels"] = a[12]["vessels"][:-1]
    moved = _fig(build(*a)["sections"][1], "vessels_lying_at_chicago_on_1_july_1835")
    assert moved["high"] == port["high"] - 1, (moved, port)
    fired += 1
    print("   fires: the port figure follows the hulls rather than a typed constant")

    # THE HEADLINE HAS NO POINT READING, and that is a decision this gate protects:
    # a later hand adding one would be adopting a number this model refused to pick.
    head = _fig(doc["sections"][0], "transients_on_1_july_1835")
    assert head["point"] is None, "the headline figure has acquired a point reading"
    assert head["low"] < head["high"], head

    # NOBODY IS WRITTEN. The cohort becomes persons in T-1353 and is cohorts here, so a
    # person or business id anywhere in the sections would be a record minted by the
    # wrong stage. A HOUSEHOLD CARD MAY BE CITED and is not covered: `hh_brown_rufus` is
    # where the sentence about the floor being covered was read, and a citation writes
    # nobody — which is why the scan runs over the sections and not over `inputs`.
    text = json.dumps(doc["sections"])
    for forbidden in ("person_", "rc_", "business_"):
        assert forbidden not in text, f"the model names a {forbidden} record"

    print(f"model_transients_1835 self-tests pass ({fired} guards fired, 3 sections, "
          "no point reading adopted, no record named)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    try:
        if args.build:
            return cmd_build()
        if args.check:
            return cmd_check()
        if args.self_test:
            return cmd_self_test()
    except Fault as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
