#!/usr/bin/env python3
"""Who owns the ground a fence stands on — the enclosure layer's join to the town.

WHAT THIS IS. T-0637, on the owner's instruction of 2026-09-04 naming *enclosures* among
the things the core dataset has to hold. Until this module the town held 289 lot-line runs
and 13 dooryard runs that could not answer **whose?**. The two hand-authored yards could —
the Sauganash's and the Western's were written against a building by hand — and the
generated ones could not, for the good reason that they are generated FROM THE LOT GRID and
the grid does not know who lives on it.

THE JOIN IS DERIVED, NOT AUTHORED, and that is the whole point of putting it here rather
than typing 302 owners into three records:

  1. a run knows its LOT, because the rule that drew it keyed it to one (a rear line and a
     dooryard to a single lot, a side line to the one or two lots that claim it);
  2. a lot knows its BUILDINGS, by exactly the occupancy test that decided the lot was
     improved and therefore fenced at all — a committed sidecar whose placement centre
     falls inside the committed lot polygon;
  3. a building knows its HOUSEHOLDS, because `data/residents/index.json` is the committed
     household index and its `lives_at` and `works_at` are the two links T-0632 and T-0633
     spent onto the people. A household whose `lives_at` names a building on this lot holds
     that ground as a HOME; one whose `works_at` names it holds it as a WORKPLACE, which is
     this dataset's business join — the project has no separate business record, a business
     here IS a structure with a trade on its `function`.

Nothing in that chain is a new claim about 1835. It is a restatement of joins the repository
already committed, which is why every entry it writes is graded `derived` and why no liberty
is taken: re-run the generators and the same owners come back.

WHAT IT REFUSES, and refusing out loud is half the value. **Most lots in this town have no
household on them.** 20 of 1,380 households carry a real `lives_at` and 50 a real
`works_at`, all of them at named landmarks, so the great majority of runs bound ground whose
buildings no household record names. Those runs are NOT left blank and are NOT given a
household the evidence does not support: they name the structures whose ground they bound
and carry a `refused` line saying why the household is missing. When the placement sweep the
household layer still owes (T-0514) lands, the same derivation picks the new owners up on
the next re-generation without a line of this module changing.

WHICH SIDE. Where one line divides two lots the run belongs to BOTH, and the record says
which owner stands on which side — as the compass bearing from the run's own midpoint to
that lot's centroid, so it is a measurement off the committed plat rather than a word.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESIDENT_INDEX = ROOT / "data" / "residents" / "index.json"
STRUCTURES = ROOT / "data" / "structures"
HH_ID = re.compile(r"hh_[a-z0-9_]+")

COMPASS = ["east", "north-east", "north", "north-west",
           "west", "south-west", "south", "south-east"]


def household_links() -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """`lives_at` and `works_at`, inverted: structure id -> the households that name it."""
    index = json.loads(RESIDENT_INDEX.read_text(encoding="utf-8"))
    homes: dict[str, list[str]] = {}
    works: dict[str, list[str]] = {}
    for hh in index.get("households", []):
        if hh.get("lives_at"):
            homes.setdefault(hh["lives_at"], []).append(hh["id"])
        if hh.get("works_at"):
            works.setdefault(hh["works_at"], []).append(hh["id"])
    return ({k: sorted(v) for k, v in homes.items()},
            {k: sorted(v) for k, v in works.items()})


def centroid(poly) -> tuple[float, float]:
    return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))


def bearing(frm, to) -> str:
    """The compass point from one place to another, in the local ENU frame (x east, y north)."""
    ang = math.atan2(to[1] - frm[1], to[0] - frm[0])
    return COMPASS[int(round(ang / (math.pi / 4))) % 8]


def owners_for(lots: list[tuple[str, list, list[str]]], path,
               links: tuple[dict, dict] | None = None) -> list[dict]:
    """The `belongs_to` of one run.

    `lots` is [(lot id, lot polygon, [structure ids on it])] — one entry for a rear or
    dooryard line, two where a side line is a party fence. `path` is the run's own
    coordinates, used only to say which side each owner is on.
    """
    homes, works = links if links is not None else household_links()
    mid = centroid(path)
    out = []
    for lot_id, poly, buildings in sorted(lots, key=lambda e: e[0]):
        households = []
        for sid in sorted(buildings):
            for hh in homes.get(sid, []):
                households.append({"id": hh, "held_as": "home", "at": sid})
            for hh in works.get(sid, []):
                households.append({"id": hh, "held_as": "workplace", "at": sid})
        entry = {
            "lot": lot_id,
            "structures": sorted(buildings),
            "households": households,
        }
        if len(lots) > 1:
            entry["side"] = bearing(mid, centroid(poly))
        if not households:
            # THE REFUSAL IS A TOKEN AND THE REASON IS STATED ONCE, in this record's
            # `belongs_to_rule.refusals`. It is the same reason for every refused run in
            # the town, and 239 copies of a paragraph is 145 kB the renderer fetches to
            # read the same sentence over and over.
            entry["refused"] = "no_household_names_this_ground"
        out.append(entry)
    return out


def prose_report(structure_ids) -> dict:
    """WHY SO MANY RUNS REFUSE, counted rather than asserted.

    A structure record's `occupants` block is PROSE, and a great deal of it names a household
    id in passing — which is the link the dooryard rule's own clause 4 reads for. This module
    deliberately does NOT join on it, for two reasons, and both are countable here rather
    than argued. The first is that the prose is stale: most of the ids it names belong to
    households the 2026-09-02 synthesis removed and the index no longer holds (T-0516). The
    second is that a mention is not an occupancy — `philo_carpenter_log_shop` names
    `hh_chappel_eliza_mir` in a sentence whose own `value` says no occupant is attested at
    the scene date — so a regex over the note would hand ground to the wrong household while
    looking like evidence.

    So the count is the finding and the join stays on `lives_at`/`works_at`.
    """
    index = json.loads(RESIDENT_INDEX.read_text(encoding="utf-8"))
    live = {hh["id"] for hh in index.get("households", [])}
    naming = 0
    named: set[str] = set()
    for sid in sorted(set(structure_ids)):
        path = STRUCTURES / f"{sid}.json"
        if not path.exists():
            continue
        occ = json.loads(path.read_text(encoding="utf-8")).get("occupants")
        if not occ:
            continue
        hits = set(HH_ID.findall(json.dumps(occ, ensure_ascii=False)))
        if hits:
            naming += 1
            named |= hits
    return {
        "structures_naming_a_household_in_prose": naming,
        "household_ids_so_named": len(named),
        "of_those_the_index_still_holds": len(named & live),
        "of_those_naming_a_household_that_no_longer_exists": len(named - live),
    }


def tally(records: list[dict]) -> dict:
    """Runs joined, runs refused, and the households that gained a fence — over any set of
    generated enclosure records, so every one of them states the same three counts."""
    joined = refused = 0
    households: set[str] = set()
    lots: set[str] = set()
    for rec in records:
        for run in rec.get("runs", []):
            entries = run.get("belongs_to") or []
            hh = {h["id"] for e in entries for h in e.get("households", [])}
            lots.update(e["lot"] for e in entries)
            if hh:
                joined += 1
                households |= hh
            else:
                refused += 1
    return {
        "runs_joined_to_a_household": joined,
        "runs_bounding_structures_only": refused,
        "households_that_gained_a_fence": len(households),
        "lots_named": len(lots),
        "households": sorted(households),
    }


def rule_block(counts: dict, prose: dict | None = None) -> dict:
    """The record-level statement of the join: what it is, how it is derived, what it refuses."""
    return {
        "_doc": (
            "WHOSE FENCE THIS IS. Every run below carries a `belongs_to` naming the lot it "
            "bounds, the committed buildings standing on that lot, and the households the "
            "committed household index puts in those buildings — a home by `lives_at`, a "
            "workplace by `works_at`, which is this dataset's business join because a "
            "business here IS a structure with a trade on its `function`. Where a single "
            "line divides two lots it belongs to both and each entry says which side of the "
            "run that owner's ground lies on, as a bearing off the committed plat."
        ),
        "derived_by": "tools/enclosure_owners.py",
        "derived_from": [
            "data/traces/vectors/thompson_lots.json",
            "data/sidecars/1835/*.json",
            "data/residents/index.json",
        ],
        "confidence": "derived",
        "counts": counts,
        "not_joined_on_the_occupants_prose": {
            "_doc": (
                "THE JOIN DOES NOT READ `occupants`, and this is the count of what it "
                "passed over. A structure record's occupants block is prose that often "
                "names a household id; most of those ids belong to households the "
                "2026-09-02 synthesis removed and the index no longer holds (T-0516), and a "
                "mention is not an occupancy — philo_carpenter_log_shop names "
                "hh_chappel_eliza_mir in a sentence whose own value says no occupant is "
                "attested there. Joining on it would hand ground to the wrong household "
                "while looking like evidence, so the refusals above stand and this is what "
                "they cost."
            ),
            **(prose or {}),
        },
        "refusals": (
            "`refused: no_household_names_this_ground` IS THE REFUSAL, and here is the "
            "reason it stands for, stated once because it is the same reason every time. "
            "A run with no household is not blank and is not guessed at: it names the "
            "structures whose ground it bounds and carries a `refused` line giving the "
            "reason, which is the same reason for every one of them — the household layer "
            "holds a real `lives_at` for 20 of its 1,380 households and a real `works_at` "
            "for 50, all of them at named landmarks, so most improved lots in this town have "
            "buildings no household record names. That is a gap in the address work "
            "(T-0514), not in this join, and the join picks up whatever the sweep lands "
            "without a line of the rule changing."
        ),
        "record_belongs_to": (
            "The record-level `belongs_to` above stays empty ON PURPOSE. It is the field the "
            "hand-authored yards use to say which ONE building a whole enclosure record is "
            "the yard of — the Sauganash's, the Western's — and these records are town-wide: "
            "they hold the fences of scores of lots and belong to no single structure. The "
            "ownership this ticket asked for is on the runs, where it can be right."
        ),
    }
