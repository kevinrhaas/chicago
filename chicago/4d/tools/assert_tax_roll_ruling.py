#!/usr/bin/env python3
"""T-1117 — the 1833 tax list is a property roll, and the gate holds what that rests on.

The ruling: the Tax List of the Town of Chicago, 1833 names the owners of ground inside
the town, resident or not, and it is therefore not a check on where a PERSON was. It is
spent in `tools/mint_civic_residents.py`, where `NOT_A_PRESENCE_CLASS` keeps it out of
both legs of the presence bracket, and it withdrew thirteen households from `present` to
`uncertain` on the day it was made.

A ruling that lives in a derivation can be quietly undone, so this asserts the two
readings the ruling stands on rather than trusting the prose that cites them. If either
moves the gate goes red and the ruling is reopened, not re-argued from memory:

  1. Entry 110 of the 1833 tax list reads "Wolcott, Alexander" — the man the list admits
     who cannot have been in the town, which is the whole refutation.
  2. The old-settler death notices give that man's death as 25 October 1830 and already
     record `places_in_1835: false` for their own class.

THE COHORT IS COUNTED AND NOT FROZEN. How many cards rest on this list alone is a
property of a residents layer that grows every week, so it is printed here and asserted
nowhere: the ruling does not rest on the count. What IS asserted, on every card and not
on a number, is `mint_civic_residents.py --gate`'s own invariant — no household may read
`present` on a tax roll's at-or-before leg.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAX_LIST = "tax_1833"
WOLCOTT_RECORD = "tax_1833_110"
WOLCOTT_AS_READ = "Wolcott, Alexander"
DEATH_RECORD = "fdn0742"
DEATH_DATE = "1830-10-25"


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def main() -> int:
    bad: list[str] = []

    voters = load("data/research/civic/records/voter_lists_1833_1835.json")
    rows = {r.get("id"): r for r in voters.get("records") or []}
    row = rows.get(WOLCOTT_RECORD)
    if row is None:
        bad.append(f"{WOLCOTT_RECORD} is no longer a record of the 1833 tax list, and it is "
                   f"the entry the ruling turns on")
    else:
        if row.get("as_read") != WOLCOTT_AS_READ:
            bad.append(f"{WOLCOTT_RECORD} now reads {row.get('as_read')!r}, not "
                       f"{WOLCOTT_AS_READ!r}")
        if (row.get("locator") or {}).get("list") != TAX_LIST:
            bad.append(f"{WOLCOTT_RECORD} has left the {TAX_LIST} list")

    deaths = load("data/research/old_settlers/death_notices.json")
    notice = next((r for r in deaths.get("records") or [] if r.get("id") == DEATH_RECORD), None)
    if notice is None:
        bad.append(f"{DEATH_RECORD} is gone from the old-settler death notices, and it is "
                   f"what dates the man on that tax list to three years before it")
    else:
        got = (notice.get("normalized") or {}).get("death_date")
        if got != DEATH_DATE:
            bad.append(f"{DEATH_RECORD} now dates the death {got!r}, not {DEATH_DATE!r}")
        if notice.get("places_in_1835") is not False:
            bad.append(f"{DEATH_RECORD} no longer records places_in_1835: false")

    # The count, printed and not asserted — see the module docstring.
    resting = 0
    households = 0
    for d in sorted((ROOT / "data/residents").glob("*/*.json")):
        if d.parent.name not in ("households", "merged"):
            continue
        doc = json.loads(d.read_text(encoding="utf-8"))
        for person in doc.get("persons") or []:
            classes = {e.get("list") for e in person.get("civic_evidence") or []}
            if classes == {TAX_LIST}:
                resting += 1
                households += 1
                break

    if bad:
        for line in bad:
            print(f"  T-1117: {line}")
        print("T-1117: the 1833 tax-roll ruling rests on a reading that has moved. "
              "Reopen the ticket and re-read the page; do not re-argue it from this note.")
        return 1

    print(f"the 1833 tax list is a property roll (T-1117): its entry 110 is "
          f"{WOLCOTT_AS_READ!r}, dead {DEATH_DATE} on {DEATH_RECORD}, so the list admits a "
          f"man who was not in the town — {households} household(s) rest on it alone today "
          f"and none of them may read `present` on it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
