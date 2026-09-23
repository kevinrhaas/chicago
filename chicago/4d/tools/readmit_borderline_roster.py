#!/usr/bin/env python3
"""T-1172 — stage `readmissions`: the borderline roster re-admitted under its own read names.

    python3 tools/readmit_borderline_roster.py --build      write the re-admissions
    python3 tools/readmit_borderline_roster.py --check      re-derive them byte-for-byte
    python3 tools/readmit_borderline_roster.py --self-test  the mutations the rules refuse

THE OWNER, 2026-09-16: *"give them a real human name … research that … may have only been
one source not a few so you marked them out, but now is the time to dip back into that and
fill out the population."*

T-1159 built the borderline roster — every name the corpus PRINTED and the research
WITHHELD, each with its evidence limit and the class of re-admission it allows. This tool
spends four of those classes. It overturns no refusal: a refusal was a ruling about
EVIDENCE and it stands. What it adds is a SECOND row of kind `reconstructed_readmission`
that says, at the reconstructed tier, what the town looks like if the name is admitted, and
what would retire it again.

WHERE THE WRITES GO, AND WHY NOT INTO THE CARDS. `data/residents/households/` is derived:
`mint_letter_list_residents.py`, `mint_civic_residents.py` and their siblings re-derive it
drift-zero, and `data/residents/index.json` is derived from THAT directory in turn. A
re-admission is not a mint output and must not pretend to be one, so:

  * the ruling itself lives in `data/reconstruction/1835_readmissions.json`;
  * a re-admitted household that has no card gets one under `data/residents/readmitted/`,
    a directory no mint writer and no index rebuild globs;
  * `tools/compile_scene.py` overlays both onto `sidecars/<scene>/people.json`, which is
    where the People view reads the town.

So a mint re-run is still byte-identical, and nothing here can be mistaken for research.

THE PERSISTENCE MODEL, MEASURED RATHER THAN CHOSEN. Three of this project's crosswalks
count how many of the SAME 1,280-person layer a later Chicago source still names: Fergus
1839 (164), Fergus 1843 (136) and Norris 1844 (112). Their LEVEL is dominated by how much
of the town each volume covers at all, which nobody knows. Their SLOPE is not: a coverage
constant that is roughly the same in all three volumes cancels out of the ratio between
them, and what is left is the rate at which a person the layer names stops being found in
Chicago. A least-squares line through ln(matched) against the years from the scene date
gives that rate directly, and `persistence(L) = exp(-lambda * L)` is what a card whose
evidence stops L years before 1 July 1835 is worth.

It is a reconstruction and it is written down as one (docs/LIBERTIES.md). What bounds it:
the three measured points, the assumption that directory coverage is stable across them,
and the exponential form. What would retire it: a measured Chicago out-migration rate for
the 1830s, or a fourth horizon that bends the line.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate_attribute_tiers import check_tier_block  # noqa: E402
from reconstruct_residents_1835 import (  # noqa: E402
    READMISSION_PASS, RECONSTRUCTED, check_reconstructed_person, draw, load_programme,
    seed_for, stages)

ROOT = Path(__file__).resolve().parents[1]
ROSTER = ROOT / "data" / "reconstruction" / "1835_borderline_roster.json"
OUT = ROOT / "data" / "reconstruction" / "1835_readmissions.json"
CARDS = ROOT / "data" / "residents" / "readmitted"
INDEX = ROOT / "data" / "residents" / "index.json"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"
OLD_SETTLERS = ROOT / "data" / "research" / "old_settlers" / "people.json"
DIRECTORIES = ROOT / "data" / "research" / "directories"
SOURCES = ROOT / "data" / "sources"

STAGE = "readmissions"
TICKET = "T-1172"
SCENE_DATE = dt.date(1835, 7, 1)
SCHEMA = 1

# The classes this stage spends. R4 is T-1170's (a family for a head the town already
# holds), R6 is T-1177's (the under-documented cohorts, which carry their own review), and
# R0 is never anybody's. Each value is the id of the rule that admits the class.
SPENDS = {
    "R1_in_window_uncertain": "readmission_r1_presence_against_persistence",
    "R2_in_window_single_source": "readmission_r2_single_source_read_name",
    "R3_1834_return_or_muster": "readmission_r3_muster_or_return",
    "R5_later_only_backprojectable": "readmission_r5_own_biography_back_projects",
}
NOT_OURS = {"R4_surname_only_census": "T-1170", "R6_native_metis_black": "T-1177",
            "R0_ineligible": "never"}

# The later Chicago volumes that measure persistence, and how many of the layer each names.
# `matched` is read from the committed crosswalk rather than typed here, so a re-run of a
# crosswalk moves the model instead of silently disagreeing with it.
HORIZONS = (
    ("fergus_1839_crosswalk_1835.json", ("counts", "residents_matched_one_entry"),
     dt.date(1839, 7, 1), "Fergus 1839, the first ward-by-ward list after the scene"),
    ("fergus_1843_crosswalk_1835.json", ("counts", "matched_one_1843_entry"),
     dt.date(1843, 7, 1), "Fergus 1843"),
    ("norris_1844_crosswalk_1835.json", ("counts", "matched_one_1844_entry"),
     dt.date(1844, 7, 1), "Norris 1844"),
)

# A draw is a 64-bit integer; this is what turns it into a share of one.
DRAW_SPAN = float(1 << 64)


# --------------------------------------------------------------------------
# small shared readings
# --------------------------------------------------------------------------

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fold(s) -> str:
    s = unicodedata.normalize("NFD", str(s or ""))
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn").lower()


def slug(s) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", fold(s))).strip("_")


def title_case(normalised: str) -> str:
    """The roster's normalised, given-first reading, printed for a reader.

    The roster already did the reading; this only chooses the capitals, because a land
    index prints `CHIPMAN ANSEL` and a card is read by a person. `name_as_read` keeps the
    printed form verbatim on every record, so nothing is lost by the choice.
    """
    out = []
    for word in str(normalised or "").split():
        if len(word) == 1:
            out.append(word.upper() + ".")
        elif word[:2] in ("mc",) and len(word) > 2:
            out.append("Mc" + word[2:].capitalize())
        else:
            out.append(word.capitalize())
    return " ".join(out)


def earliest_meaning(date_text: str):
    """The EARLIEST day a partial date can mean. `1835` -> 1835-01-01, `1835-04` -> the 1st.

    A partial date is read at its earliest, which puts the card's evidence as far from the
    scene as the text allows and therefore gives the persistence model its LONGEST lag. It
    is the reading that re-admits the fewest people, and that is the direction an invention
    should err in.
    """
    text = str(date_text or "").strip()
    # A SPAN (`1833-11/1835-08`) is two dates and therefore not one; it is read by
    # dated_evidence() through T-1144's own fields, not guessed at here.
    try:
        if re.fullmatch(r"\d{4}", text):
            return dt.date(int(text), 1, 1)
        if re.fullmatch(r"\d{4}-\d{2}", text):
            return dt.date(int(text[:4]), int(text[5:7]), 1)
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            return dt.date.fromisoformat(text)
    except ValueError:
        return None
    return None


def dated_evidence(row: dict):
    """(the day the evidence reaches, the text it was read from) or (None, why not).

    T-1144 gave every roster row the far end of its evidence — `dated_evidence_reaches`
    — and a flag saying whether that evidence's window BRACKETS the scene date. Both
    matter here. A reading that pins a day before 1 July 1835 is a lag the persistence
    model can price; a source SPAN that runs through the scene date pins no day before it
    (the row's own `dated_evidence_leg` says exactly that), and a persistence rate is
    meaningless over a lag nothing measures. So the second kind is withheld and says so,
    rather than being priced off the start of a span the person was never sighted at.
    """
    when = earliest_meaning(row.get("describes_date"))
    if when is not None:
        return when, None
    if row.get("dated_evidence_includes_scene_date") is True:
        return None, ("the_evidence_pins_no_day_before_the_scene")
    reaches = earliest_meaning(row.get("dated_evidence_reaches"))
    if reaches is not None and reaches <= SCENE_DATE:
        return reaches, None
    return None, "undated_reading"


def lag_years(when: dt.date) -> float:
    """Years from a dated appearance to the scene date, never negative."""
    return max(0.0, (SCENE_DATE - when).days / 365.2425)


# --------------------------------------------------------------------------
# the persistence model
# --------------------------------------------------------------------------

def persistence_model() -> dict:
    """lambda, its three measured points, and the sentence that says what it rests on."""
    points = []
    for filename, path, when, label in HORIZONS:
        doc = load(DIRECTORIES / filename)
        node = doc
        for key in path:
            node = node[key]
        points.append({
            "volume": label,
            "crosswalk": f"data/research/directories/{filename}",
            "counts_key": ".".join(path),
            "dated": when.isoformat(),
            "years_after_the_scene": round((when - SCENE_DATE).days / 365.2425, 4),
            "of_the_layer_still_named": int(node),
        })

    ts = [p["years_after_the_scene"] for p in points]
    ys = [math.log(p["of_the_layer_still_named"]) for p in points]
    tbar = sum(ts) / len(ts)
    ybar = sum(ys) / len(ys)
    num = sum((t - tbar) * (y - ybar) for t, y in zip(ts, ys))
    den = sum((t - tbar) ** 2 for t in ts)
    lam = round(-num / den, 6)

    return {
        "id": "persistence_1835",
        "form": "persistence(L) = exp(-lambda * L), L in years before 1835-07-01",
        "lambda_per_year": lam,
        "one_year_persistence": round(math.exp(-lam), 4),
        "measured_on": points,
        "why_the_slope_and_not_the_level": (
            "Each volume names only a part of the town, and what part is unknown. That "
            "unknown coverage multiplies all three counts alike, so it cancels out of the "
            "SLOPE of ln(matched) against time and does not cancel out of any one level. "
            "The slope is therefore the rate at which the layer's people stop being found "
            "in Chicago; the level is mostly a fact about directories."),
        "what_bounds_it": (
            "Three points, an assumption that directory coverage is roughly steady across "
            "1839-1844, and an exponential form. Nothing here is measured at the short lags "
            "the roster actually needs (0-3.5 years), so the rate is carried back to them."),
        "which_way_it_is_wrong_if_it_is_wrong": (
            "The steady-coverage assumption is the load-bearing one and it is the one most "
            "likely to fail: Fergus 1839 is a list first set up from memory in 1839 and "
            "completed in 1876, and the 1843 and 1844 volumes are ordinary printed "
            "directories. If coverage GREW across the three, the observed fall is shallower "
            "than the real one, this lambda is too small, and the stage re-admits too many "
            "people rather than too few. Published persistence studies of frontier towns "
            "read nearer 0.15-0.25 a year than 0.068. That is stated here rather than "
            "corrected for, because correcting it would mean choosing a number instead of "
            "measuring one; the ruling it would change is which side of the draw a card "
            "whose evidence stops early falls on, and the seed makes that re-runnable the "
            "day a measured rate lands."),
        "what_would_retire_it": (
            "A measured out-migration or persistence rate for Chicago in the 1830s, or a "
            "fourth horizon that bends this line."),
        "tier": RECONSTRUCTED,
    }


def ruled_present(model: dict, household_id: str, when: dt.date):
    """(value, share, lag, seed) — the persistence draw for one dated appearance."""
    lag = lag_years(when)
    share = math.exp(-model["lambda_per_year"] * lag)
    seed = seed_for(household_id, "persistence")
    u = draw(seed) / DRAW_SPAN
    return ("present" if u < share else "absent"), share, lag, seed


# --------------------------------------------------------------------------
# what the town already holds
# --------------------------------------------------------------------------

def layer_names() -> tuple[set, set, set]:
    """(person ids, household ids, surname + first-initial keys) already in the layer.

    The third is the discriminator this project's own directory crosswalks use — a surname
    and a first given initial — and it is what stops a re-admission minting a second card
    for somebody the town already carries under a slightly different reading.
    """
    person_ids, household_ids, keys = set(), set(), set()
    index = load(INDEX)
    for entry in index.get("households", []):
        household_ids.add(entry.get("id"))
        path = ROOT / "data" / "residents" / entry.get("file", "")
        if not path.exists():
            continue
        record = load(path)
        for person in record.get("persons") or []:
            person_ids.add(person.get("id"))
            keys.add(name_key(person.get("name")))
    keys.discard("")
    return person_ids, household_ids, keys


def name_key(name) -> str:
    """`surname|first initial`, the crosswalks' own discriminator, from a display name."""
    words = [w for w in re.split(r"[^A-Za-z]+", fold(name)) if w]
    if len(words) < 2:
        return ""
    return f"{words[-1]}|{words[0][0]}"


# --------------------------------------------------------------------------
# the four classes
# --------------------------------------------------------------------------

def ruling_r1(row: dict, model: dict, when: dt.date) -> dict:
    """A card the town already holds, whose presence on 1 July 1835 stands `uncertain`."""
    hid = row["existing_household_id"]
    value, share, lag, seed = ruled_present(model, hid, when)
    return {
        "row_id": row["row_id"],
        "class": row["class"],
        "household_id": hid,
        "name_as_read": row["name_as_read"],
        "dated_evidence": row.get("describes_date") or row.get("dated_evidence_reaches"),
        "dated_evidence_read_as": when.isoformat(),
        "years_before_the_scene": round(lag, 4),
        "persistence": round(share, 4),
        "seed": seed,
        "present_on_scene_date": {
            "value": value,
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "model", "id": model["id"],
                "note": (f"The corpus last names this person on "
                         f"{row.get('describes_date') or row.get('dated_evidence_reaches')}, "
                         f"{lag:.2f} years before the scene date, and says nothing after it. "
                         f"The persistence model gives {share:.3f} for that lag; the draw "
                         f"seeded on this household reads {value}."),
            },
            "seed": seed,
            "replaceable_by": {
                "kind": "person",
                "match": ("any source that follows this person past 1 July 1835, or any "
                          "source that places them elsewhere on it"),
            },
        },
        "the_inferred_value_this_stands_beside": "uncertain",
        "withdrawn_if": ("a later ruling finds this card a duplicate of another, in which "
                         "case the retirement runs through tools/consolidate_town_cards.py "
                         "and not by hand here"),
    }


def person_note(row: dict, class_sentence: str) -> str:
    return (f"RE-ADMITTED FROM THE BORDERLINE ROSTER ({TICKET}). {class_sentence} "
            f"The research READ this name and WITHHELD it, and that refusal is not "
            f"overturned: this record is a reconstruction of what the town looks like if "
            f"the name is admitted at the limit of its own evidence, and it says so on its "
            f"face. The reading, the source and the refusal stand at "
            f"`{row['row_id']}` in data/reconstruction/1835_borderline_roster.json. "
            f"No figure is drawn (L1).")


def minted_card(row: dict, model: dict, hid: str, pid: str, sources: list,
                arrival: dict | None, class_sentence: str, rule_id: str,
                presence: dict) -> dict:
    display = title_case(row.get("normalised") or row.get("name_as_read"))
    return {
        "id": hid,
        "name": f"The {display.split()[-1]} household — a name the roster offered back",
        "division": "unplaced",
        "head": pid,
        "source_pass": READMISSION_PASS,
        "readmission": {
            "ticket": TICKET,
            "stage": STAGE,
            "class": row["class"],
            "rule": rule_id,
            "row_id": row["row_id"],
            "name_as_read": row["name_as_read"],
            "stands_on": class_sentence,
            "withdrawn_if": ("a ruling that this name is a duplicate of a card the town "
                             "already holds; the retirement runs through "
                             "tools/consolidate_town_cards.py, never by hand"),
        },
        "arrival": arrival or {
            "value": None, "confidence": RECONSTRUCTED, "tier": "unknown",
            "note": "Not attested. The reading dates an appearance and not an arrival.",
        },
        "lives_at": {"value": None, "confidence": RECONSTRUCTED, "tier": "unknown",
                     "note": "Not attested: the reading gives a name and no address."},
        "works_at": {"value": None, "confidence": RECONSTRUCTED, "tier": "unknown",
                     "note": "Not attested."},
        "present_on_scene_date": presence,
        "persons": [{
            "id": pid,
            "name": display,
            "name_as_read": row["name_as_read"],
            "relationship": "head",
            "grade": RECONSTRUCTED,
            "basis": {"kind": "rule", "id": rule_id,
                      "note": class_sentence},
            "replaceable_by": {
                "kind": "person",
                "match": ("a second independent source naming this person at Chicago inside "
                          "the window, which would carry the card back to the research "
                          "layer at `inferred`"),
            },
            "reconstruction": {"stage": STAGE, "programme": "chicago_1835_resident_reconstruction",
                               "community": None},
            "occupation": {"value": "none_recorded", "confidence": RECONSTRUCTED,
                           "tier": "unknown",
                           "note": "No source records an occupation for this person."},
            "sources": sources,
            "note": person_note(row, class_sentence),
            "resident_subtype": "readmitted_resident",
        }],
        "touches_removal": False,
        "review_required": False,
        "research_note": (
            f"WRITTEN BY tools/readmit_borderline_roster.py ({TICKET}), the `{STAGE}` stage of "
            f"the 1835 resident reconstruction programme. This file is NOT research and is not "
            f"a mint output: data/residents/households/ is re-derived by the mint writers and "
            f"data/residents/index.json is derived from that directory, so a re-admission lives "
            f"here instead and is overlaid onto the scene by tools/compile_scene.py. "
            f"docs/LIBERTIES.md carries the invention."),
    }


def presence_block(model: dict, hid: str, when: dt.date, row: dict) -> tuple[dict, dict]:
    value, share, lag, seed = ruled_present(model, hid, when)
    block = {
        "value": value, "confidence": RECONSTRUCTED, "tier": RECONSTRUCTED,
        "basis": {"kind": "model", "id": model["id"],
                  "note": (f"The reading dates this name at {row.get('describes_date')}, "
                           f"{lag:.2f} years before the scene date. The persistence model "
                           f"gives {share:.3f} for that lag and the seeded draw reads "
                           f"{value}.")},
        "seed": seed,
        "replaceable_by": {"kind": "person",
                           "match": "any source naming this person at Chicago on or after "
                                    "1 July 1835"},
    }
    return block, {"value": value, "persistence": round(share, 4),
                   "years_before_the_scene": round(lag, 4), "seed": seed}


# --------------------------------------------------------------------------
# the build
# --------------------------------------------------------------------------

def old_settler_rows() -> dict:
    """record id -> the roll entry, for the source and the arrival an R5 row stands on."""
    if not OLD_SETTLERS.exists():
        return {}
    return {p["id"]: p for p in load(OLD_SETTLERS).get("people", [])}


def derive() -> tuple[dict, dict]:
    """(the readmissions record, {household_id: card}) — the whole stage, in memory."""
    roster = load(ROSTER)
    model = persistence_model()
    settlers = old_settler_rows()
    person_ids, household_ids, keys = layer_names()
    source_ids = {p.stem for p in SOURCES.glob("*.json")}

    r1: list[dict] = []
    minted: list[dict] = []
    withheld: list[dict] = []
    cards: dict[str, dict] = {}
    taken_keys = set(keys)
    taken_ids = set(household_ids)

    def withhold(row, reason, why):
        withheld.append({"row_id": row["row_id"], "class": row["class"],
                         "name_as_read": row["name_as_read"], "reason": reason, "why": why})

    for row in sorted(roster["rows"], key=lambda r: r["row_id"]):
        cls = row["class"]
        if cls not in SPENDS:
            continue
        rule_id = SPENDS[cls]

        if cls == "R1_in_window_uncertain":
            when, refusal = dated_evidence(row)
            if when is None:
                withhold(row, refusal,
                         (row.get("dated_evidence_leg")
                          or "The row carries no date this tool can read.")
                         + " So the persistence model has no lag to price, and the card "
                           "keeps the research's `uncertain` with nothing beside it.")
                continue
            if row.get("existing_household_id") not in household_ids:
                withhold(row, "the_card_is_no_longer_in_the_layer",
                         "The roster names a household the index no longer carries; a "
                         "presence cannot be ruled onto a card that is not there.")
                continue
            r1.append(ruling_r1(row, model, when))
            continue

        # R2, R3 and R5 all MINT. A read name, no card, and one reading behind it.
        when, refusal = dated_evidence(row)
        if when is None:
            withhold(row, refusal,
                     "A mint needs a dated appearance to price its presence against the "
                     "persistence model, and this reading gives none: "
                     + (row.get("dated_evidence_leg") or "it carries no readable date."))
            continue
        key = name_key(title_case(row.get("normalised")))
        if not key:
            withhold(row, "not_a_whole_name",
                     "The reading gives no surname and forename together, so there is no "
                     "person to mint under a read name.")
            continue
        if key in taken_keys:
            withhold(row, "a_card_of_that_name_already_stands",
                     "A person already in the layer shares this surname and first given "
                     "initial — the same discriminator this project's directory crosswalks "
                     "match on — so minting a second card would risk carrying one person "
                     "into the town twice.")
            continue

        pid = slug(row.get("normalised"))
        hid = f"hh_{pid}"
        if not pid or hid in taken_ids:
            withhold(row, "the_id_a_read_name_derives_is_already_taken",
                     "The household id this reading derives is already borne by a card in "
                     "the layer; the id scheme forbids renaming a real person to make room.")
            continue

        sources = [s for s in (row.get("source_id") or []) if s in source_ids]
        arrival = None
        if cls == "R5_later_only_backprojectable":
            entry = settlers.get(row.get("claim_or_record_id")) or {}
            sid = entry.get("source")
            if sid in source_ids and sid not in sources:
                sources.append(sid)
            year = row.get("arrival_year")
            if not isinstance(year, int) or year > SCENE_DATE.year:
                withhold(row, "the_biography_does_not_reach_before_the_scene",
                         "R5 stands on the row's own biography dating an arrival at or "
                         "before 1 July 1835, and this one does not.")
                continue
            arrival = {
                "value": f"{year}-01-01", "confidence": "inferred", "tier": "inferred",
                "sources": list(sources),
                "note": (f"THE BIOGRAPHY'S OWN DATE, NOT THIS PROJECT'S. The roll records "
                         f"this person's arrival at Chicago in {year}, and a later source "
                         f"may date what it remembers of an earlier year. Read at 1 January "
                         f"because the roll gives a year and no day."),
                "precision": "year",
            }
        if not sources:
            withhold(row, "no_source_resolves",
                     "Every record here must cite a source that resolves in data/sources/, "
                     "and this reading's does not.")
            continue

        if cls == "R5_later_only_backprojectable":
            class_sentence = (
                "A later Chicago source names this person and their own biography dates "
                "their arrival before 1 July 1835, so the later naming back-projects on its "
                "own evidence — and, by naming them after the scene, shows they had not "
                "left it.")
            presence = {
                "value": "present", "confidence": RECONSTRUCTED, "tier": RECONSTRUCTED,
                "basis": {"kind": "rule", "id": rule_id,
                          "note": ("Argued, not drawn: the roll dates the arrival before the "
                                   "scene date and names the person in Chicago after it, so "
                                   "nothing is left for a persistence draw to price.")},
                "replaceable_by": {"kind": "person",
                                   "match": "a source placing this person away from Chicago "
                                            "on 1 July 1835"},
            }
            drawn = {"value": "present", "persistence": None,
                     "years_before_the_scene": None, "seed": None}
        else:
            if cls == "R2_in_window_single_source":
                class_sentence = (
                    "One dated appearance inside the window under a read name, withheld from "
                    "the town for want of corroboration or of identity, and carried on no "
                    "card.")
            else:
                class_sentence = (
                    "Enrolled at Chicago in the 1832 Black Hawk muster, with no 1835 "
                    "corroboration and no card; an earlier source dates and corroborates and "
                    "never promotes, so presence is priced against the persistence model.")
            presence, drawn = presence_block(model, hid, when, row)

        card = minted_card(row, model, hid, pid, sources, arrival, class_sentence,
                           rule_id, presence)
        cards[hid] = card
        taken_keys.add(key)
        taken_ids.add(hid)
        minted.append({
            "row_id": row["row_id"], "class": cls, "rule": rule_id,
            "household_id": hid, "person_id": pid,
            "name_as_read": row["name_as_read"], "name": card["persons"][0]["name"],
            "file": f"readmitted/{hid}.json", "sources": sources,
            "dated_evidence": row.get("describes_date"),
            "dated_evidence_read_as": when.isoformat(),
            "present_on_scene_date": drawn,
        })

    offered = {c: 0 for c in SPENDS}
    for row in roster["rows"]:
        if row["class"] in offered:
            offered[row["class"]] += 1
    readmitted = {c: 0 for c in SPENDS}
    for entry in r1:
        readmitted[entry["class"]] += 1
    for entry in minted:
        readmitted[entry["class"]] += 1
    withheld_by_class = {c: 0 for c in SPENDS}
    for entry in withheld:
        withheld_by_class[entry["class"]] += 1

    record = {
        "$schema_note": ("DERIVED — regenerate with tools/readmit_borderline_roster.py "
                         "--build; tools/check.sh re-derives it. Do not hand-edit."),
        "schema": SCHEMA,
        "id": "chicago_july_1835_readmissions",
        "ticket": TICKET,
        "stage": STAGE,
        "target_date": SCENE_DATE.isoformat(),
        "generated_by": "tools/readmit_borderline_roster.py --build",
        "reads": {
            "roster": "data/reconstruction/1835_borderline_roster.json",
            "layer": "data/residents/index.json",
            "persistence": [h[0] for h in HORIZONS],
        },
        "writes": {
            "cards": "data/residents/readmitted/",
            "not_into": ("data/residents/households/ and data/residents/index.json, which "
                         "the mint writers and tools/rebuild_resident_index.py re-derive"),
            "overlaid_by": "tools/compile_scene.py",
        },
        "overturns_nothing": (
            "Every ledger disposition, grade, rung and inferred or attested value in the "
            "research layer is untouched. An R1 ruling is a SECOND, reconstructed value "
            "standing beside the inferred `uncertain`, which is kept on the card; R2, R3 "
            "and R5 are new records of kind `reconstructed_readmission` pointing at the "
            "refused unit, never a rewrite of the refusal."),
        "classes_this_stage_spends": SPENDS,
        "classes_owned_elsewhere": NOT_OURS,
        "persistence_model": model,
        "counts": {
            "offered": offered,
            "readmitted": readmitted,
            "withheld": withheld_by_class,
            "presence_ruled_present": sum(
                1 for e in r1 if e["present_on_scene_date"]["value"] == "present"),
            "presence_ruled_absent": sum(
                1 for e in r1 if e["present_on_scene_date"]["value"] == "absent"),
            "cards_minted": len(cards),
            "minted_present": sum(1 for e in minted
                                  if e["present_on_scene_date"]["value"] == "present"),
        },
        "the_tension_this_leaves": {
            "what": ("The order book (T-1166) models 643 households in the town on 1 July "
                     "1835 and the layer carries 436 present today. Ruling 787 more cards "
                     "present takes that to 1,223, which is nearly twice the model."),
            "why_it_is_not_this_stage_overfilling_a_quota": (
                "The order book says of the roster that it 'is a licence on WHICH name a "
                "filler uses and never a quota', and counts it against its ticket rather "
                "than into a cell. The mismatch is older than this stage: 736 of the "
                "layer's households are letter-list CONTAINERS holding one person and "
                "arguing for a person rather than for a dwelling, which the mint says in "
                "its own words. A container is not a household in the model's sense, and "
                "the two counts are not yet in the same unit."),
            "whose_it_is": ("T-1171 draws families into these heads and T-1179 converges "
                            "the layer against the model. Neither can do it before the "
                            "presences are ruled, which is what this stage is for."),
        },
        "presence_rulings": r1,
        "minted": minted,
        "withheld": sorted(withheld, key=lambda w: w["row_id"]),
    }
    return record, cards


def emit(record: dict, cards: dict, write: bool) -> list[str]:
    """Write or compare. Returns the paths that differ from what is committed."""
    drift: list[str] = []
    wanted = {f"{hid}.json" for hid in cards}

    def settle(path: Path, payload: dict):
        text = json.dumps(payload, indent=1, ensure_ascii=False) + "\n"
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        elif not path.exists() or path.read_text(encoding="utf-8") != text:
            drift.append(str(path.relative_to(ROOT)))

    settle(OUT, record)
    for hid, card in sorted(cards.items()):
        settle(CARDS / f"{hid}.json", card)

    existing = {p.name for p in CARDS.glob("*.json")} if CARDS.exists() else set()
    for stale in sorted(existing - wanted):
        if write:
            (CARDS / stale).unlink()
        else:
            drift.append(f"data/residents/readmitted/{stale} (committed, no longer derived)")
    return drift


def build() -> int:
    prog = load_programme()
    if STAGE not in stages(prog):
        print(f"FAIL the programme has no '{STAGE}' stage", file=sys.stderr)
        return 2
    record, cards = derive()
    emit(record, cards, write=True)
    c = record["counts"]
    print(f"  built {sum(c['readmitted'].values())} re-admission(s) from "
          f"{sum(c['offered'].values())} offered; {c['cards_minted']} card(s) written to "
          f"data/residents/readmitted/, {sum(c['withheld'].values())} withheld")
    print(f"  persistence lambda {record['persistence_model']['lambda_per_year']}/yr "
          f"({record['persistence_model']['one_year_persistence']} over one year); "
          f"{c['presence_ruled_present']} present / {c['presence_ruled_absent']} absent")
    return 0


# --------------------------------------------------------------------------
# the gate
# --------------------------------------------------------------------------

def check() -> int:
    problems: list[str] = []

    def error(where, msg):
        problems.append(f"{where}: {msg}")

    if not OUT.exists():
        print(f"  FAIL {OUT.relative_to(ROOT)} is missing; run --build")
        return 1

    record, cards = derive()
    for path in emit(record, cards, write=False):
        error(path, "does not re-derive — a hand edit, or a reading that moved under it")

    committed = load(OUT)
    # THE REFUSALS STAY REFUSED. A re-admission may never touch the research layer, so
    # the gate re-reads it and asserts that every card the stage speaks about is still
    # exactly as the research left it.
    index = load(INDEX)
    by_id = {e["id"]: e for e in index.get("households", [])}
    for ruling in committed.get("presence_rulings", []):
        entry = by_id.get(ruling["household_id"])
        if entry is None:
            error(ruling["household_id"], "the card this ruling stands on is not in the index")
        elif entry.get("present_on_scene_date") != "uncertain":
            error(ruling["household_id"],
                  f"the research card now reads presence "
                  f"{entry.get('present_on_scene_date')!r}; a re-admission stands BESIDE an "
                  f"`uncertain` and may not survive the research settling it")

    # No re-admitted card may live in the mints' directory, and no mint card here.
    for path in sorted(CARDS.glob("*.json")) if CARDS.exists() else []:
        if (HOUSEHOLDS / path.name).exists():
            error(path.name, "a card of this id stands in data/residents/households/ too — "
                             "the town would carry the person twice")

    # The record contract, held over every minted person, by the programme's own copy.
    prog = load_programme()
    keys = set(stages(prog))
    real = {" ".join(str(p.get("name") or "").split()).lower()
            for hid in cards for p in cards[hid]["persons"]}
    for hid, card in sorted(cards.items()):
        for person in card["persons"]:
            check_reconstructed_person(f"{hid}:{person['id']}", person, keys, error)
        for key in ("arrival", "lives_at", "works_at", "present_on_scene_date"):
            check_tier_block(hid, key, card.get(key) or {}, error)
        for person in card["persons"]:
            check_tier_block(f"{hid}:{person['id']}", "occupation",
                             person.get("occupation") or {}, error)
    if len(real) != len(cards):
        error("readmitted", "two minted cards print the same name")

    if problems:
        for p in problems[:20]:
            print(f"  FAIL {p}")
        if len(problems) > 20:
            print(f"  FAIL ... and {len(problems) - 20} more")
        return 1

    c = committed["counts"]
    print(f"  ok    {sum(c['readmitted'].values())} re-admission(s) re-derive from the "
          f"roster, the layer and the three persistence crosswalks")
    print(f"  ok    {c['cards_minted']} minted card(s) hold the record contract; "
          f"{sum(c['withheld'].values())} row(s) withheld, each with its reason")
    print(f"  ok    every card an R1 ruling stands on still reads `uncertain` in the "
          f"research layer — no refusal was overturned")
    return 0


# --------------------------------------------------------------------------
# the mutations the rules refuse
# --------------------------------------------------------------------------

def self_test() -> int:
    failures = 0

    def case(name, ok):
        nonlocal failures
        if ok:
            print(f"  ok    {name}")
        else:
            failures += 1
            print(f"  FAIL {name}")

    model = {"id": "persistence_1835", "lambda_per_year": 0.07}

    # A partial date is read at its EARLIEST, which is the longest lag and the fewest
    # re-admissions. A reading that took `1834` as the end of 1834 would re-admit more
    # people on less evidence, which is the direction this rule exists to refuse.
    case("a bare year is read at 1 January",
         earliest_meaning("1834") == dt.date(1834, 1, 1))
    case("a year and month are read at the 1st",
         earliest_meaning("1835-04") == dt.date(1835, 4, 1))
    case("a full date is read as itself",
         earliest_meaning("1834-10-22") == dt.date(1834, 10, 22))
    case("an unreadable date is refused rather than guessed",
         earliest_meaning("about 1834") is None and earliest_meaning("") is None)

    # T-1144's two fields, read the way this stage is allowed to read them.
    case("a row whose evidence brackets the scene date pins no day before it",
         dated_evidence({"describes_date": "1833-11/1835-08",
                         "dated_evidence_reaches": "1835-08-31",
                         "dated_evidence_includes_scene_date": True})
         == (None, "the_evidence_pins_no_day_before_the_scene"))
    case("a row whose evidence stops before the scene is priced off where it stops",
         dated_evidence({"describes_date": None,
                         "dated_evidence_reaches": "1834-10-22"})
         == (dt.date(1834, 10, 22), None))
    case("a plain readable date still outranks the derived reach",
         dated_evidence({"describes_date": "1834-04-01",
                         "dated_evidence_reaches": "1835-06-30"})
         == (dt.date(1834, 4, 1), None))

    # The draw is a function of the household id and nothing else, so two runs, two
    # machines and two orderings of the roster agree.
    a = ruled_present(model, "hh_x", dt.date(1834, 1, 1))
    b = ruled_present(model, "hh_x", dt.date(1834, 1, 1))
    case("the same household and lag redraw the same presence", a == b)
    case("two households of the same lag draw independently",
         ruled_present(model, "hh_x", dt.date(1834, 1, 1))[3]
         != ruled_present(model, "hh_y", dt.date(1834, 1, 1))[3])

    # Persistence falls with the lag, and a card whose evidence reaches the scene date is
    # worth 1: a model that rose with distance from the evidence would be the wrong sign.
    near = ruled_present(model, "hh_x", SCENE_DATE)[1]
    far = ruled_present(model, "hh_x", dt.date(1832, 1, 1))[1]
    case("persistence is 1 at the scene date and falls with the lag",
         abs(near - 1.0) < 1e-9 and 0.0 < far < near)

    # The discriminator that stops one person being carried into the town twice is the
    # crosswalks' own: a surname and a first given initial.
    case("the name key is surname and first initial",
         name_key("Ansel Chipman") == "chipman|a"
         and name_key("A. Chipman") == "chipman|a")
    case("a name with no surname yields no key", name_key("Ansel") == "")

    # A read name is printed for a reader without being re-read.
    case("a normalised reading is capitalised, not re-read",
         title_case("ansel chipman") == "Ansel Chipman"
         and title_case("a w taylor") == "A. W. Taylor")

    # The persistence model must be measured on committed crosswalks, not typed here.
    try:
        live = persistence_model()
        case("the model reads its three horizons off the committed crosswalks",
             len(live["measured_on"]) == 3
             and all(p["of_the_layer_still_named"] > 0 for p in live["measured_on"]))
        case("the fitted rate is a decay and not a growth", live["lambda_per_year"] > 0)
    except (OSError, KeyError, ValueError) as exc:
        case(f"the model reads its three horizons off the committed crosswalks ({exc})", False)

    # The stage this tool writes must be the one the programme names, or a person could be
    # written under a stage the programme cannot re-derive.
    prog = load_programme()
    stage = stages(prog).get(STAGE)
    case("the programme carries this stage and gives it to this ticket",
         bool(stage) and stage.get("ticket") == TICKET)
    case("the programme's readmission pass is the one these cards wear",
         prog["id_scheme"]["readmission_source_pass"] == READMISSION_PASS)

    # The classes this stage spends are exactly the four the roster gives it, and the
    # other three belong to somebody else by name.
    roster_classes = set(load(ROSTER)["classes"])
    case("every class is either spent here or owned by a named ticket",
         set(SPENDS) | set(NOT_OURS) == roster_classes)
    case("R4 and R6 are not this stage's to spend",
         "R4_surname_only_census" not in SPENDS and "R6_native_metis_black" not in SPENDS)

    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true", help="write the re-admissions")
    ap.add_argument("--check", action="store_true", help="re-derive them byte-for-byte")
    ap.add_argument("--self-test", action="store_true", help="the mutations the rules refuse")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.build:
        return build()
    if args.check:
        return check()
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
