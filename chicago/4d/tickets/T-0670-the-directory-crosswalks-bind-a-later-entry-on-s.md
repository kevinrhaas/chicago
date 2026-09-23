---
id: T-0670
title: The directory crosswalks bind a later entry on surname plus a first initial, and 532 new anchors made that rule bind Thomas L. Abbott onto Titus H. Abbott
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-04
pr: 814
claimed_by: run 9/4/2026, 4:03:34 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T21:39:54.498Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33918567032
---

The directory crosswalks bind a later entry on surname plus a first initial, and 532 new anchors made that rule bind Thomas L. Abbott onto Titus H. Abbott.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**The finding, measured on dev at the T-0514 mint (2026-09-04).** `tools/crosswalk_fergus_1843.py`
and `tools/crosswalk_norris_1844.py` match a directory entry to a resident on the folded SURNAME
plus the FIRST INITIAL of the given name, and refuse a surname-only agreement. That rule was
written when the residents layer held 848 names. T-0514 minted 532 more, and the rule then declared
35 merges onto people it had never had an anchor for — of which about nine agree on the initial and
disagree on the name behind it:

    Abbott, Thomas L.   → abbott_titus_h        (thomas / titus)
    Hogan, Michael      → hogan_mary            (michael / mary)
    Fisher, Peter       → fisher_pitman         (peter / pitman)
    Bristol, Calvin     → bristol_charles_l     (calvin / charles)
    Brown, Henry        → brown_hanna_e         (henry / hanna)
    Burke, John         → burke_james           (john / james)

The rest of the 35 are an initial standing in for the same name (`f`/`francis`, `w`/`william`,
`h`/`henry`) or a spelling (`absalom`/`absolom`), and those are the merges the rule exists to make.
Nothing is hidden by the bad ones — every card shows the entry AS READ, so `Abbott, Thomas L.`
appears verbatim on Titus H. Abbott's card — but a declared merge feeds
`consolidate_resident_evidence.py` as a D1 ruling and carries a later address and trade with it,
which is what T-0633 will spend.

**The ask.** Tighten the crosswalk's match to refuse a first-initial agreement where BOTH readings
print a full forename that disagrees (an initial against a full name stays a match; two full names
that differ do not), re-derive both crosswalks, and report which of the 35 survive. Then look at
whether the same rule wants a second discriminator — a trade, an address or a year — where the town
now holds more than one candidate under a surname.

**Links:** T-0514 (the mint that surfaced it) · docs/LIBERTIES.md L220 · T-0633.

**And the same weakness in the other direction, found the same day.** `tools/read_land_sales.py`'s
resident crosswalk matches a purchaser only where the residents layer holds EXACTLY ONE person of
the surname and the forename agrees. A bigger town makes that rule fire LESS: seating 531 people
turned nine of its matches ambiguous (Carpenter, Dole, Fullerton, Haddock twice, Heacock, Sweet,
Burdick, Wooley) and made six possible for the first time (Bronson, Hale, Hartzell, Ludby, Price,
Wolcott) — a net loss of three rulings with nothing new read, which is why `land_sales`'s spend
ceiling was raised by two in that commit. So the two crosswalks fail in opposite directions off the
same assumption: the directories bind too readily on an initial, and the land sales stop binding at
all when a surname stops being unique. Both want a second discriminator rather than a count of
namesakes.
