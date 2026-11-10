#!/usr/bin/env python3
"""A day for each drawn person of 1835 and 1904 (T-3516), as people-1812-town/place_town.py
writes 1812's.

    python3 docs/RESEARCH/people-days-1835-1904/days.py           write `behaviour.day` into each record
    python3 docs/RESEARCH/people-days-1835-1904/days.py --check   the gate: each record's day is this one

The owner, 2026-11-08: *"give everyone a purpose and role for every part of the day. This is
for all years starting with 1812"*, and *"the people should look natural that they are doing
ordinary things on a loop ... They can take breaks and go in and out of houses and buildings"*.
renderers/web/js/human-days.js plays a day: indoors (a building, asked for at its door) or out
at a place, at a job about it (a stand, played as one) or with others (a talk, which gathers
now and then and parts, each at their job between), and between spans in and out of their
door. Most jobs use the existing placement; the owners also use the court and evening
sidewalk, and Christine uses her recorded errand route. The hours and buildings are:

  1835 (1 July)
    Philip F. W. Peck   merchant; kept his store and lived in it (Andreas 1884; the record
                        peck_store): in it at night and at dinner, out at its front by day.
    Mary Flynn          a domestic keeping her own house (T-1347's model record): in her log
                        house (the record she stands at the door of) at night and at dinner.
    Patrick Mahoney     a labourer with no fixed premises (the seating ruling), at work on the
                        river bank by day; where he lodged no record says, so off the scene
                        (`away`) at night.
    Otis Bardwell       a teamster (the seating ruling), at his wagon in the Wolf Point Tavern
                        yard by day; off the scene at night, as Mahoney.
  1904 (1 July; the household of 1800 Prairie Avenue)
    The cooks (Mattie Williamson, Kate Ryan) and the stable helper (August Billings) in the
    court, one talk among them (`glessner_court`); the maid (Mary Reynolds) at the north entry
    and the coachman (Charles Nelson) at the stable doors on Eighteenth Street, another
    (`glessner_18th`). Each in the house by its servants' doors (tools/derive_doors_scene.py)
    at night and for the hours of the house's own meals.
  All eight drawn household members now have seasonal days, including the owners and
  Christine. Office hours are off-scene, not a claim to an office location. Activities
  and times are reconstructed, not diary entries (L-t3533-household-routines).

The hours are reconstructed (a working day of the trade and the season), recorded as liberty
L-t3516-days; the people, their trades and their buildings are their records'.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIB = "L-t3516-days"


def IN(f, t, where, doing):
    return {"from": f, "to": t, "indoors": True, "where": where, "doing": doing}


def AWAY(f, t, doing):
    return {"from": f, "to": t, "indoors": True, "away": True, "doing": doing}


def OUT(f, t, doing, knot=None):
    s = {"from": f, "to": t, "indoors": False, "at": None, "activity": "talk" if knot else "stand", "doing": doing}
    if knot:
        s["knot"] = knot
    return s


DAYS = {
    "1835": {
        "hi_peck_philip_1835": ("peck_store", [
            IN(0, 6, "peck_store", "asleep at the store"),
            IN(6, 7, "peck_store", "breakfast"),
            OUT(7, 11.75, "at the store front: goods in and out, the stock looked over"),
            IN(11.75, 12.25, "peck_store", "dinner"),
            OUT(12.25, 18.5, "at the store front: goods in and out, the stock looked over"),
            IN(18.5, 24, "peck_store", "supper, the books, asleep"),
        ]),
        "hi_rc_flynn_mary_1835": ("recon_1835_blk_south_water_lasalle_d1_04", [
            IN(0, 5.5, "recon_1835_blk_south_water_lasalle_d1_04", "asleep"),
            OUT(5.5, 11, "at her dooryard: water and wood, the washing, the garden"),
            IN(11, 12, "recon_1835_blk_south_water_lasalle_d1_04", "dinner"),
            OUT(12, 17.5, "at her dooryard: the washing, mending, the garden"),
            IN(17.5, 24, "recon_1835_blk_south_water_lasalle_d1_04", "supper, asleep"),
        ]),
        "hi_rc_mahoney_patrick_1835": (None, [
            AWAY(0, 5.5, "at his lodging, which no record names"),
            OUT(5.5, 18.5, "labouring on the river bank"),
            AWAY(18.5, 24, "at his lodging, which no record names"),
        ]),
        "hi_rc_bardwell_otis_1835": (None, [
            AWAY(0, 5.5, "at his lodging, which no record names"),
            OUT(5.5, 19, "at his wagon in the tavern yard: the team, the harness, the loads"),
            AWAY(19, 24, "at his lodging, which no record names"),
        ]),
    },
    "1904": {
        "hi_glessner_williamson_martha_l_1904": ("glessner_house", [
            IN(0, 6, "glessner_house", "asleep"),
            IN(6, 9, "glessner_house", "the kitchen: breakfast for the house"),
            OUT(9, 12, "in the court: kitchen work out of doors, the deliveries taken in", "glessner_court"),
            IN(12, 14.5, "glessner_house", "the kitchen: luncheon"),
            OUT(14.5, 17, "in the court: kitchen work out of doors", "glessner_court"),
            IN(17, 24, "glessner_house", "the kitchen: dinner; asleep"),
        ]),
        "hi_pa1904_glessner_john_j_c1900_kate_ryan_1904": ("glessner_house", [
            IN(0, 6, "glessner_house", "asleep"),
            IN(6, 9.5, "glessner_house", "the kitchen: breakfast for the house"),
            OUT(9.5, 12, "by the service stair in the court: the kitchen's work out of doors", "glessner_court"),
            IN(12, 15, "glessner_house", "the kitchen: luncheon"),
            OUT(15, 17, "by the service stair in the court", "glessner_court"),
            IN(17, 24, "glessner_house", "the kitchen: dinner; asleep"),
        ]),
        "hi_pa1904_glessner_john_j_c1900_august_billings_1904": ("glessner_house", [
            IN(0, 5.5, "glessner_house", "asleep in the rear building"),
            OUT(5.5, 12, "in the court by the stable: the harness, the carriage washed", "glessner_court"),
            IN(12, 13, "glessner_house", "dinner"),
            OUT(13, 19, "in the court by the stable: the harness, the carriage washed", "glessner_court"),
            IN(19, 24, "glessner_house", "supper; asleep in the rear building"),
        ]),
        "hi_pa1904_glessner_john_j_c1900_mary_reynolds_1904": ("glessner_house", [
            IN(0, 6, "glessner_house", "asleep"),
            IN(6, 10, "glessner_house", "the rooms done, breakfast served"),
            OUT(10, 12, "at the servants' entry on Eighteenth Street: the steps swept, errands", "glessner_18th"),
            IN(12, 15, "glessner_house", "luncheon served, the rooms"),
            OUT(15, 16.5, "at the servants' entry on Eighteenth Street", "glessner_18th"),
            IN(16.5, 24, "glessner_house", "dinner served; asleep"),
        ]),
        "hi_pa1904_glessner_john_j_c1900_charles_nelson_1904": ("glessner_house", [
            IN(0, 6, "glessner_house", "asleep"),
            OUT(6, 12.5, "at the stable doors: the horses, the carriage made ready", "glessner_18th"),
            IN(12.5, 13.5, "glessner_house", "dinner"),
            OUT(13.5, 19, "at the stable doors: the horses, the carriage made ready", "glessner_18th"),
            IN(19, 24, "glessner_house", "supper; asleep"),
        ]),
    },
}


HOUSE = "glessner_house"
DAYS["1904"].update({
    "hi_glessner_john_j_1904": (HOUSE, [
        IN(0, 7, HOUSE, "sleeping and dressing"),
        OUT(7, 8, "inspect the courtyard garden"),
        IN(8, 9, HOUSE, "breakfast and correspondence"),
        AWAY(9, 16, "at the office; its location is not staged"),
        OUT(16, 17.5, "inspect the house and grounds"),
        IN(17.5, 19, HOUSE, "dinner"),
        OUT(19, 20, "talk with the household on the evening walk", "glessner_evening"),
        IN(20, 24, HOUSE, "reading, family time and sleep"),
    ]),
    "hi_glessner_frances_m_1904": (HOUSE, [
        IN(0, 8, HOUSE, "sleeping, dressing and breakfast"),
        OUT(8, 9.5, "look over the garden with the household"),
        IN(9.5, 11, HOUSE, "household accounts and correspondence"),
        OUT(11, 12, "discuss household provisions in the court", "glessner_court"),
        IN(12, 15.5, HOUSE, "luncheon, reading and calls"),
        OUT(15.5, 17, "tend the courtyard flowers"),
        IN(17, 19, HOUSE, "prepare for dinner and dine"),
        OUT(19, 20, "talk with the household on the evening walk", "glessner_evening"),
        IN(20, 24, HOUSE, "music, reading and sleep"),
    ]),
    "hi_pa1904_glessner_john_j_c1900_christine_nelson_1904": (HOUSE, [
        IN(0, 6, HOUSE, "sleeping and dressing"),
        IN(6, 10, HOUSE, "breakfast service and the parlour"),
        OUT(10, 11.5, "walk the block on a household errand"),
        IN(11.5, 14.5, HOUSE, "luncheon service and polishing"),
        OUT(14.5, 15.5, "air and brush household things in the court"),
        IN(15.5, 18.5, HOUSE, "the parlour and dinner service"),
        OUT(18.5, 19.5, "take an evening walk"),
        IN(19.5, 24, HOUSE, "supper and sleep"),
    ]),
})


def day_of(rec: dict, spans: list) -> list:
    pl = rec["placement"]
    at = {"local_e": pl["local_e"], "local_n": pl["local_n"], "heading_deg": pl.get("heading_deg", 0.0)}
    out = []
    for s in spans:
        s = dict(s)
        if s.get("at", 0) is None:
            s["at"] = dict(at)
        out.append(s)
    if rec["scene"] != "1904":
        return [{"note": f"Reconstructed day ({LIB}, T-3516): docs/RESEARCH/people-days-1835-1904/days.py.", "spans": out}]
    from copy import deepcopy
    variants = []
    for season, months in [("winter", [12, 1, 2]), ("spring", [3, 4, 5]), ("autumn", [9, 10, 11]), ("summer", [6, 7, 8])]:
        seasonal = deepcopy(out)
        for span in seasonal:
            if span["indoors"]:
                continue
            # Individual jobs dominate; shared knots remain brief gatherings in the day engine.
            if span.get("knot") and span["to"] - span["from"] > 1:
                span.pop("knot")
                span["activity"] = "stand"
            if rec["person_id"] == "glessner_john_j":
                span["at"] = {"local_e": 1361.5, "local_n": -3232.5, "heading_deg": 230}
            if span.get("knot") == "glessner_evening":
                span["at"] = {"local_e": 1393.5, "local_n": -3226.5, "heading_deg": 270}
            if "christine_nelson" in rec["id"]:
                if "walk" in span["doing"]:
                    route = rec["behaviour"]["route"]
                    span.update(activity="walk", via=deepcopy(route[:-1]), to_point=deepcopy(route[-1]))
                else:
                    span["at"] = {"local_e": 1364, "local_n": -3234, "heading_deg": 210}
            if "garden" in span["doing"] or "flowers" in span["doing"]:
                span["doing"] = {"winter": "check the sheltered court and dormant plants", "spring": "tend the spring garden", "summer": "tend and inspect the courtyard flowers", "autumn": "inspect the garden and clear fallen leaves"}[season]
        # A short shared break, surrounded by each worker's own duties.
        shared = []
        for span in seasonal:
            if not span["indoors"] and span["from"] < 11 and span["to"] >= 11.5 and "christine" not in rec["id"]:
                before, meeting, after = deepcopy(span), deepcopy(span), deepcopy(span)
                before["to"] = 11
                meeting.update({"from": 11, "to": 11.5, "activity": "talk", "knot": "glessner_court" if span["at"]["local_n"] < -3220 else "glessner_18th", "doing": "take a short break and discuss the household work"})
                after["from"] = 11.5
                shared.extend([before, meeting] + ([after] if after["from"] < after["to"] else []))
            else:
                shared.append(span)
        seasonal = shared
        if season == "winter":
            shorter = []
            for span in seasonal:
                if not span["indoors"] and span["to"] - span["from"] > 0.5:
                    end = span["to"]
                    span["to"] = span["from"] + 0.5
                    shorter.extend([span, IN(span["to"], end, HOUSE, "indoor household duties and shelter from the cold")])
                else:
                    shorter.append(span)
            seasonal = shorter
        variants.append({"dates": {"months": months}, "note": "Reconstructed seasonal routine (L-t3533-household-routines); times and activities are not diary evidence.", "spans": seasonal})
    return variants


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    bad = 0
    n = 0
    for scene, people in DAYS.items():
        for rid, (_, spans) in people.items():
            f = ROOT / f"data/humans/instances/{scene}/{rid}.json"
            rec = json.loads(f.read_text())
            # Cover the day, end to end.
            assert spans[0]["from"] == 0 and spans[-1]["to"] == 24 and all(a["to"] == b["from"] for a, b in zip(spans, spans[1:])), rid
            want = day_of(rec, spans)
            if args.check:
                if (rec.get("behaviour") or {}).get("day") != want:
                    print(f"FAIL days: {f.relative_to(ROOT)}'s day is not what days.py writes; run python3 docs/RESEARCH/people-days-1835-1904/days.py", file=sys.stderr)
                    bad = 1
            else:
                rec.setdefault("behaviour", {})["day"] = want
                f.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
            n += 1
    if not bad:
        print(f"days 1835/1904: {n} people have a day ({LIB})")
    return bad


if __name__ == "__main__":
    sys.exit(main())
