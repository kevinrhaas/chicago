#!/usr/bin/env python3
"""Validate T-1765's reconstructed bridge-head timber placement.

The 6 m offsets and distribution are chosen reconstruction rules, not historical
measurements. Deck endpoints and centerlines come from committed footprints;
terrain chooses between the two candidate sides. All stock remains reconstructed.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "tools"))
from heightfield import Heightfield  # noqa: E402

EPOCH_DIR = DATA / "terrain" / "epochs" / "e1834_harbor_cut"
RECORD_PATH = DATA / "yard" / "bridge_head_timber.json"
DATUM_PATH = DATA / "datum.json"

BRIDGES = ("north_branch_bridge", "south_branch_raft_bridge")

# The set-out, in metres. Both numbers are this project's; the clearance they have to
# buy is the attested ten feet of roadway.
BACK_M = 6.0
OFF_M = 6.0
# The deck width the clearance is measured against, and the length the stock is drawn
# at. Asserted against both records rather than written here twice.
DECK_WIDTH_M = 3.048
# How close the record may sit to the derivation before this is a different claim.
TOL_M = 0.01


def load(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def derive(field: Heightfield) -> list[dict]:
    """The four heads, their stack points and the ground under them."""
    datum = load(DATUM_PATH)
    origin_e = datum["origin_utm_e"]
    origin_n = datum["origin_utm_n"]
    out = []
    for bridge in BRIDGES:
        record = load(DATA / "structures" / f"{bridge}.json")
        phase = record["phases"][0]
        pos = phase["position"]
        poly = phase["footprint"]["polygon"]
        xmin, xmax = min(x for x, _ in poly), max(x for x, _ in poly)
        ymin, ymax = min(y for _, y in poly), max(y for _, y in poly)
        length = xmax - xmin
        width = ymax - ymin
        mid_y = (ymin + ymax) / 2
        e0 = pos["utm_e"] - origin_e
        n0 = pos["utm_n"] - origin_n
        theta = math.radians(pos["rotation_deg"])
        # Along the deck, and across it. The same two lines the footprint is written on.
        ue, un = math.cos(theta), math.sin(theta)
        ve, vn = -un, ue
        for end, along, sign in (("west", xmin, -1.0), ("east", xmax, 1.0)):
            head_e = e0 + along * ue + mid_y * ve
            head_n = n0 + along * un + mid_y * vn
            back_e = head_e + sign * BACK_M * ue
            back_n = head_n + sign * BACK_M * un
            sides = {}
            for side, offset in (("south", -OFF_M), ("north", OFF_M)):
                pe = back_e + offset * ve
                pn = back_n + offset * vn
                sides[side] = (pe, pn, field.height(pe, pn) if field.covers(pe, pn) else None)
            higher = max(sides, key=lambda s: (sides[s][2] if sides[s][2] is not None else -99))
            pe, pn, ground = sides[higher]
            # The pile lies along the crossing's own axis, and this layer's bearing is
            # the facing, measured clockwise from local north: a stick laid along
            # (cos b, -sin b) in east-north is the wall line of a facing of b.
            bearing = round(-math.degrees(theta), 2) % 360.0
            out.append({
                "bridge": bridge,
                "end": end,
                "deck_width_m": width,
                "deck_length_m": length,
                "head_local_enu_m": [round(head_e, 2), round(head_n, 2)],
                "head_ground_m": round(field.height(head_e, head_n), 2),
                "side": higher,
                "at_local_enu_m": [round(pe, 2), round(pn, 2)],
                "bearing_deg": 0.0 if abs(bearing) < 1e-9 else round(bearing, 2),
                "ground_m": None if ground is None else round(ground, 2),
                "other_side_ground_m": None if sides["south" if higher == "north" else "north"][2] is None
                else round(sides["south" if higher == "north" else "north"][2], 2),
                "clear_of_deck_m": round(OFF_M - width / 2 - 0.4, 2),
                "corner_ground_m": [field.height(pe + a * ue + b * ve, pn + a * un + b * vn)
                    if field.covers(pe + a * ue + b * ve, pn + a * un + b * vn) else None
                    for a in (-DECK_WIDTH_M / 2, DECK_WIDTH_M / 2) for b in (-0.4, 0.4)],
            })
    return out


def failures(derived: list[dict], record: dict) -> list[str]:
    """Everything this gate asserts, as a list of complaints."""
    bad: list[str] = []
    lots = record.get("lots", [])
    items = [(lot, item) for lot in lots for item in lot.get("items", [])]
    if len(items) != len(derived):
        bad.append(f"the record stands {len(items)} pile(s) and the derivation gives "
                   f"{len(derived)}")
        return bad
    for want, (lot, item) in zip(derived, items):
        who = f"{want['bridge']} {want['end']}"
        if lot.get("structure_id") != want["bridge"]:
            bad.append(f"{who}: the pile hangs off {lot.get('structure_id')!r}")
        if item.get("kind") != "timber":
            bad.append(f"{who}: the pile is {item.get('kind')!r} and not timber")
        if item.get("end") != want["end"]:
            bad.append(f"{who}: wrong deck end")
        if item.get("ground_m") != want["ground_m"]:
            bad.append(f"{who}: stored ground height is stale")
        if item.get("courses") != 3:
            bad.append(f"{who}: expected three reconstructed courses")
        if any(h is None or h <= 0 for h in want["corner_ground_m"]):
            bad.append(f"{who}: pile corner is outside dry modelled ground")
        at = item.get("at_local_enu_m")
        if not isinstance(at, list) or len(at) != 2 or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in at):
            bad.append(f"{who}: expected two finite coordinates")
            at = [None, None]
        for axis, got, expect in zip("en", at, want["at_local_enu_m"]):
            if got is None or abs(got - expect) > TOL_M:
                bad.append(f"{who}: {axis} is {got} and the set-out gives {expect}")
        if abs((item.get("bearing_deg") or 0.0) - want["bearing_deg"]) > 0.01:
            bad.append(f"{who}: bearing is {item.get('bearing_deg')} and the crossing's "
                       f"own axis gives {want['bearing_deg']}")
        if item.get("stands_on") != want["side"]:
            bad.append(f"{who}: the record stands it on the {item.get('stands_on')} side "
                       f"and the higher committed ground is {want['side']}")
        if want["ground_m"] is None or want["ground_m"] <= 0.0:
            bad.append(f"{who}: the committed ground under the pile is "
                       f"{want['ground_m']} — it is not dry land")
        if want["clear_of_deck_m"] < 4.0:
            bad.append(f"{who}: the set-out leaves only {want['clear_of_deck_m']} m "
                       f"clear of the deck")
        if abs(want["deck_width_m"] - DECK_WIDTH_M) > 1e-6:
            bad.append(f"{who}: the deck is {want['deck_width_m']} m wide and the "
                       f"clearance was measured against {DECK_WIDTH_M}")
    stick = (record.get("form", {}).get("timber_stick_m", {}).get("value") or [None])[0]
    if stick is None or abs(stick - DECK_WIDTH_M) > 1e-6:
        bad.append(f"the stock is drawn {stick} m long and the attested deck width — "
                   f"which is what a puncheon is cut to — is {DECK_WIDTH_M}")
    if record.get("form", {}).get("timber_stick_m", {}).get("value") != [3.048, 0.2, 0.2]:
        bad.append("stock cross-section differs from the placement envelope")
    if record.get("form", {}).get("timber_pile", {}).get("value") != [4, [4, 4], 1]:
        bad.append("pile form differs from the placement envelope")
    if record.get("counts", {}).get("sticks") != 44:
        bad.append("expected forty-four reconstructed sticks")
    stated = record.get("counts", {}).get("piles")
    if stated != len(derived):
        bad.append(f"`counts.piles` says {stated} and there are {len(derived)}")
    return bad


def report(derived: list[dict]) -> None:
    print("  bridge                      end   head ENU            ground   side    "
          "pile ENU             ground")
    for row in derived:
        print("  %-26s %-5s (%8.2f,%8.2f) %6.2f   %-6s (%8.2f,%8.2f) %6.2f" % (
            row["bridge"], row["end"], row["head_local_enu_m"][0],
            row["head_local_enu_m"][1], row["head_ground_m"], row["side"],
            row["at_local_enu_m"][0], row["at_local_enu_m"][1], row["ground_m"]))


def self_test(derived: list[dict], record: dict) -> int:
    """Break each assertion and prove it fires. Tagged for check.sh's roll-up."""
    import copy
    cases = []

    def moved(rec):
        rec["lots"][0]["items"][0]["at_local_enu_m"][0] += 1.0
        return rec
    cases.append(("a pile moved a metre", moved))

    def rekinded(rec):
        rec["lots"][0]["items"][0]["kind"] = "stone"
        return rec
    cases.append(("the stock turned to stone", rekinded))

    def turned(rec):
        rec["lots"][0]["items"][0]["bearing_deg"] = 45.0
        return rec
    cases.append(("a pile turned off the crossing's axis", turned))

    def flipped(rec):
        rec["lots"][0]["items"][0]["stands_on"] = "south" if \
            rec["lots"][0]["items"][0].get("stands_on") == "north" else "north"
        return rec
    cases.append(("a pile put on the lower side", flipped))

    def shortened(rec):
        rec["form"]["timber_stick_m"]["value"][0] = 4.0
        return rec
    cases.append(("the stock cut to a length no source gives", shortened))

    def dropped(rec):
        rec["lots"][0]["items"].pop()
        return rec
    cases.append(("a pile dropped", dropped))

    def miscounted(rec):
        rec["counts"]["piles"] = 99
        return rec
    cases.append(("the count disagreeing with the piles", miscounted))

    for label, key, value in (("wrong deck end", "end", "wrong"), ("stale ground", "ground_m", -20), ("missing coordinate", "at_local_enu_m", [0]), ("wrong courses", "courses", 9)):
        def mutate(rec, key=key, value=value):
            rec["lots"][0]["items"][0][key] = value
            return rec
        cases.append((label, mutate))
    failed = 0
    for label, break_it in cases:
        broken = break_it(copy.deepcopy(record))
        bad = failures(derived, broken)
        if bad:
            print(f"   self-test | FAIL as designed — {label}: {bad[0]}")
        else:
            print(f"   self-test | NOT CAUGHT — {label}")
            failed += 1
    if failures(derived, copy.deepcopy(record)):
        print("   self-test | NOT CAUGHT — the committed record itself does not pass")
        failed += 1
    else:
        print("   self-test | the committed record passes unbroken")
    return failed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gate", action="store_true",
                    help="fail if the record disagrees with the derivation")
    ap.add_argument("--self-test", action="store_true",
                    help="break each assertion and prove it fires")
    ap.add_argument("--json", action="store_true", help="the derivation as JSON")
    ap.add_argument("--quiet", action="store_true", help="say nothing when green")
    args = ap.parse_args()

    field = Heightfield.load(EPOCH_DIR)
    if field is None:
        print("no committed heightfield for e1834_harbor_cut", file=sys.stderr)
        return 1
    derived = derive(field)

    if args.json:
        print(json.dumps(derived, indent=1))
        return 0

    if not RECORD_PATH.exists():
        print(f"FAIL {RECORD_PATH} is not committed", file=sys.stderr)
        return 1
    record = load(RECORD_PATH)

    if args.self_test:
        return 1 if self_test(derived, record) else 0

    bad = failures(derived, record)
    if bad:
        for line in bad:
            print(f"FAIL {line}")
        return 1
    if not args.quiet:
        report(derived)
        print("  the four piles follow the reconstructed offsets on committed "
              "ground.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
