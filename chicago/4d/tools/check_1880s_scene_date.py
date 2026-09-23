#!/usr/bin/env python3
"""Re-derive the 1880s scene date from its readings, and hold every copy of it.

T-1249, piece 1 of T-0473.  A representative scene date is a claim about when
this reconstruction stands, and it was the one claim in the terrain layer that
nothing derived and nothing checked: ``tools/check_shoreline_states.py`` carried
a bare ``date(1885, 7, 1)`` that T-1152 wrote in as scaffolding for a different
assertion.  It looked exactly like a settled figure and it was not one — it is
three and a half years before the Glessner House was finished, so the Prairie
Avenue this epoch exists to carry could not have stood on it.

This proves four things:

* the adopted date is the arithmetic of the committed readings and nothing else
  — the latest documented lower bound, carried to the scene day-of-year, held
  inside the window the parent ticket set;
* every reading resolves to a committed source, and a reading that supplies no
  constraint does not quietly acquire one;
* the epoch, the shoreline state and the shoreline gate all address the SAME
  day, because the two data files and the gate now read one file; and
* the epoch that day resolves to is unique, and is still ``planned`` with no
  borrowed geometry — a settled date is not permission to draw ground.
"""
from __future__ import annotations

import argparse
import copy
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TERRAIN = ROOT / "data" / "terrain"
CONSTRAINTS_PATH = TERRAIN / "1880s_scene_date_constraints.json"
EPOCHS_PATH = TERRAIN / "epochs.json"
STATES_PATH = TERRAIN / "shoreline_states.json"
SOURCES_DIR = ROOT / "data" / "sources"

EPOCH_ID = "e1871_postfire"
STATE_ID = "shore_1880s_ic_edge"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_iso(value: str) -> date:
    return date.fromisoformat(value)


def derive(constraints: dict) -> tuple[date | None, list[str]]:
    """The adopted date, recomputed from the readings. None if it cannot be."""
    bad: list[str] = []
    window = constraints.get("window", {})
    readings = constraints.get("readings", [])

    bounds: list[date] = []
    for r in readings:
        rid = r.get("id", "?")
        kind = r.get("kind")
        if kind == "lower_bound":
            if not r.get("not_before"):
                bad.append(f"reading {rid} is a lower_bound with no not_before")
                continue
            bounds.append(parse_iso(r["not_before"]))
        elif kind == "no_constraint":
            if r.get("not_before") is not None:
                bad.append(f"reading {rid} says it constrains nothing and carries a bound")
            if r.get("why_it_binds") is not None:
                bad.append(f"reading {rid} says it constrains nothing and says why it binds")
        else:
            bad.append(f"reading {rid} has unknown kind {kind!r}")

    if not bounds:
        bad.append("no lower bound survives: the date would rest on the window alone")
        return None, bad

    day = constraints.get("derivation", {}).get("day_of_year", "")
    try:
        month, dom = (int(part) for part in day.split("-"))
    except (ValueError, AttributeError):
        bad.append(f"derivation day_of_year {day!r} is not MM-DD")
        return None, bad

    floor = max(bounds)
    candidate = date(floor.year, month, dom)
    if candidate < floor:
        candidate = date(floor.year + 1, month, dom)

    frm, to = window.get("from"), window.get("to")
    if not frm or not to:
        bad.append("the window has no bounds, so nothing holds the derivation inside the decade")
    elif not parse_iso(frm) <= candidate <= parse_iso(to):
        bad.append(f"the derived date {candidate.isoformat()} falls outside the window {frm}..{to}")
    return candidate, bad


def validate(constraints: dict, epochs_doc: dict, states_doc: dict,
             source_ids: set[str], gate_date: date) -> list[str]:
    bad: list[str] = []
    derived, bad_derivation = derive(constraints)
    bad += bad_derivation

    adopted_raw = constraints.get("adopted", {}).get("date")
    adopted = parse_iso(adopted_raw) if adopted_raw else None
    if adopted is None:
        bad.append("no adopted date")
    elif derived is not None and adopted != derived:
        bad.append(f"the adopted date {adopted.isoformat()} is not what its own readings "
                   f"derive ({derived.isoformat()}) — a scene date may not be hand-edited "
                   f"into agreement")

    for r in constraints.get("readings", []):
        sid = r.get("source_id")
        if sid not in source_ids:
            bad.append(f"reading {r.get('id')!r} cites unresolved source {sid!r}")
        if not r.get("quoted"):
            bad.append(f"reading {r.get('id')!r} quotes nothing of the source it rests on")

    superseded = constraints.get("adopted", {}).get("supersedes", {}).get("date")
    if not superseded:
        bad.append("the date this one replaced is not recorded, so nothing stops it coming back")
    elif adopted is not None and superseded == adopted.isoformat():
        bad.append("the superseded date and the adopted date are the same day")

    if adopted is None:
        return bad

    epochs = {e.get("id"): e for e in epochs_doc.get("epochs", [])}
    covering = [e for e in epochs.values()
                if e.get("from") and e.get("to")
                and parse_iso(e["from"]) <= adopted <= parse_iso(e["to"])]
    if len(covering) != 1:
        bad.append(f"{adopted.isoformat()} falls inside {len(covering)} terrain epochs, not 1")
    elif covering[0].get("id") != EPOCH_ID:
        bad.append(f"{adopted.isoformat()} resolves to {covering[0].get('id')!r}, "
                   f"expected {EPOCH_ID!r}")

    epoch = epochs.get(EPOCH_ID, {})
    if epoch.get("representative_date") != adopted.isoformat():
        bad.append(f"{EPOCH_ID} carries representative_date "
                   f"{epoch.get('representative_date')!r}, not {adopted.isoformat()!r}")
    if epoch.get("representative_date_derivation") != CONSTRAINTS_PATH.name:
        bad.append(f"{EPOCH_ID} does not name the file its date is derived in")
    if epoch.get("status") != "planned":
        bad.append(f"{EPOCH_ID} left `planned` before any of its ground layers exist")
    if epoch.get("sources"):
        bad.append(f"{EPOCH_ID} cites ground sources while its ground layers are unwritten")
    for layer in ("shoreline", "terrain_spec", "heightfield"):
        if not (epoch.get("layer_status", {}) or {}).get(layer):
            bad.append(f"{EPOCH_ID} does not say who owes its {layer}")

    states = {s.get("id"): s for s in states_doc.get("states", [])}
    state = states.get(STATE_ID, {})
    if state.get("address_date") != adopted.isoformat():
        bad.append(f"{STATE_ID} addresses {state.get('address_date')!r}, "
                   f"not the adopted {adopted.isoformat()!r}")
    if state.get("geometry") is not None or state.get("status") != "planned":
        bad.append(f"{STATE_ID} acquired a line from a ticket that only settled a date")
    rng = state.get("address_range", {})
    if not (rng.get("from") and rng.get("to")
            and parse_iso(rng["from"]) <= adopted <= parse_iso(rng["to"])):
        bad.append(f"{STATE_ID}'s address_date falls outside its own address_range")

    if gate_date != adopted:
        bad.append(f"tools/check_shoreline_states.py addresses {gate_date.isoformat()}, "
                   f"not the adopted {adopted.isoformat()} — the two have drifted apart")
    return bad


def documents() -> tuple[dict, dict, dict, set[str]]:
    return (load(CONSTRAINTS_PATH), load(EPOCHS_PATH), load(STATES_PATH),
            {p.stem for p in SOURCES_DIR.glob("*.json")})


def gate_address_date() -> date:
    """What tools/check_shoreline_states.py itself resolves for the 1880s."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_c4d_shoreline_states", Path(__file__).with_name("check_shoreline_states.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ADDRESS_DATES["1880s"]


def self_test(docs: tuple[dict, dict, dict, set[str]], gate_date: date) -> int:
    cases = []

    d = copy.deepcopy(docs[:3])
    d[0]["adopted"]["date"] = "1885-07-01"
    cases.append(("a hand-edited adopted date fails",
                  bool(validate(*d, docs[3], gate_date))))

    d = copy.deepcopy(docs[:3])
    d[0]["readings"][0]["not_before"] = "1881-01-01"
    cases.append(("weakening the Glessner bound stops deriving the adopted date",
                  bool(validate(*d, docs[3], gate_date))))

    d = copy.deepcopy(docs[:3])
    d[0]["readings"][1]["not_before"] = "1892-01-01"
    cases.append(("giving the undated Kimball record a bound fails",
                  bool(validate(*d, docs[3], gate_date))))

    d = copy.deepcopy(docs[:3])
    d[0]["readings"][0]["source_id"] = "no_such_source"
    cases.append(("a reading citing an uncommitted source fails",
                  bool(validate(*d, docs[3], gate_date))))

    d = copy.deepcopy(docs[:3])
    for e in d[1]["epochs"]:
        if e.get("id") == EPOCH_ID:
            e["representative_date"] = "1889-07-01"
    cases.append(("the epoch drifting off the derived date fails",
                  bool(validate(*d, docs[3], gate_date))))

    d = copy.deepcopy(docs[:3])
    for s in d[2]["states"]:
        if s.get("id") == STATE_ID:
            s["geometry"] = {"dated_lines": []}
            s["status"] = "active"
    cases.append(("the 1880s state taking a line on a date ticket fails",
                  bool(validate(*d, docs[3], gate_date))))

    d = copy.deepcopy(docs[:3])
    cases.append(("the shoreline gate drifting off the derived date fails",
                  bool(validate(*d, docs[3], date(1885, 7, 1)))))

    d = copy.deepcopy(docs[:3])
    d[0]["window"]["to"] = "1887-12-31"
    cases.append(("a window the derived date falls outside fails",
                  bool(validate(*d, docs[3], gate_date))))

    for label, passed in cases:
        print(("OK " if passed else "FAIL ") + label)
    return 0 if all(passed for _, passed in cases) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    docs = documents()
    gate_date = gate_address_date()
    if args.self_test:
        return self_test(docs, gate_date)
    bad = validate(docs[0], docs[1], docs[2], docs[3], gate_date)
    for problem in bad:
        print("FAIL", problem)
    if not bad:
        adopted = docs[0]["adopted"]["date"]
        print(f"OK the 1880s scene stands at {adopted}, re-derived from the Glessner House "
              f"bound; {EPOCH_ID} and {STATE_ID} address the same day and neither has ground yet")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
