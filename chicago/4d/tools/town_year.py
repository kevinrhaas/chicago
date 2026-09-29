"""Which structure records belong to the 1835 town's own books.

TICKET T-1732. `data/structures/` held one town until the Glessner House (built
1886-1887, the 1904 scene's first building) was committed beside it. A dozen 1835
tools walk that directory whole — the 665-roof ledger, the anonymous-roof redeal,
the name pool's key census, the land-tract join, the order book — and each one
treats every record it finds as a roof of 1835, so the first record of another
year stops them all ("glessner_house belongs to no programme this ledger can
read"). The directory is shared on purpose (`docs/EPOCHS.md`: a structure is an
identity with dated phases, and one scene rule decides membership), so the fix is
to have those books ask the same question the scene rule asks, once, here.

**The test is "does any phase touch the year 1835"**, not "does a phase cover
1 July 1835". The narrower test would drop the first Cook County court-house,
which Andreas dates to the fall of 1835: it is excluded from the 1835 scene by
date and is nonetheless a roof of 1835 that the ledger counts and the order book
owes. A record of 1887 touches no day of 1835 under either reading, and that is
the only case this module exists to separate.
"""

from __future__ import annotations

import datetime as dt

TOWN_YEAR = 1835


def touches_year(record: dict, year: int = TOWN_YEAR) -> bool:
    """True when any phase's documented range overlaps the calendar year `year`.

    A phase with an unreadable range counts as touching it, so a malformed record
    is still read by the 1835 books (and refused there, loudly) rather than
    quietly dropped from them.
    """
    first, last = dt.date(year, 1, 1), dt.date(year, 12, 31)
    for ph in record.get("phases", []):
        rng = ph.get("documented_range") or {}
        try:
            frm = dt.date.fromisoformat(rng["from"])
            to = dt.date.fromisoformat(rng["to"])
        except (KeyError, TypeError, ValueError):
            return True
        if frm <= last and to >= first:
            return True
    return False
