# The south bank at the Dearborn reach: is there ground for the plate's warehouses?

**T-0134. Settled 2026-08-28, against the committed plat, the traced 1834 waterline and
the committed heightfield. The answer is no, and the reason is not the one the refusal
was originally written on.**

## The question

Image 3 of the owner's brief of 2026-08-18
(`data/sources/assets/owner_brief_2026_08_18/README.md`) is an engraving of the reach
below the Dearborn Street drawbridge. It draws **low warehouses on BOTH banks**. T-0133
built the north side — `north_bank_shed_dearborn_{w,e1,e2,e3}`, four freight sheds
standing back from North Water Street — and left the south side empty, with one sentence
repeated in all four records:

> the platted South Water Street corridor reaches to within about 1.7 m of the traced
> 1834 waterline at the Dearborn reach, so there is no ground there for a building that
> is not standing in the platted street.

That was a spot reading, taken by hand at one station (local E 697), and the whole south
bank of the reach was refused on it. T-0134 was opened to settle it properly. The
acceptance clause offered two ways out: build the warehouses clear of whatever the
corridor turns out to be, or hold a written finding that the corridor reaches the water
and the plate's buildings cannot be sited without settling it first.

## The measurement

`tools/measure_south_bank_ground.py` walks the south bank from the Dearborn crossing —
`dearborn_street_drawbridge`'s own committed position, local E 699.2 — east to the United
States Reservation's west line at E 842.0, the line `tools/measure_no_build_ground.py`
already resolves from the State & Madison section corner. Both ends are resolved from
committed records rather than typed, for the reason `data/datum.json` is re-derived
rather than stored.

At every station it asks whether the **smallest footprint family F1 allows** — 18 × 32 ft
(5.486 × 9.754 m), the freight shed of the plate, read out of
`data/reconstruction/1835_building_inventory.json` — can be put down on ground that is
above the water surface in the committed heightfield, outside every platted street
corridor (`tools/plat_corridors.py`, the module the placement gate itself asks), and off
the refused ground of the Reservation and the sand bar.

**Every bound is the permissive one.** The rectangle may stand at any bearing rather than
square to the street. It is the smallest the family allows rather than the median. "Dry"
means one millimetre above the water surface rather than any freeboard. And the relief
clause is reported four ways: at the 0.30 m walker step tolerance three infill generators
hold themselves to (`generate_block_infill.MAX_RELIEF_M`), at the 0.35 m the north bank
sheds' own notes quote, at a full metre, and with the clause switched off entirely.

## The reading

    the south bank from dearborn_street_drawbridge (E 699.2) east to the
    Reservation's west line (E 842.0)
    124 of 143 stations carry ANY dry ground outside a platted corridor
    the widest such strip is 26.50 m, at E 813.2 (N 0.0 to 26.0, 1.30 m of relief)
    positions the smallest F1 footprint would stand at, at any bearing:
       relief <= 0.30 m       0
       relief <= 0.35 m       0
       relief <= 1.00 m       6
       no relief clause      26
    BESIDE THE PLATTED STREET — west of South Water's own east end (E 805.0),
    which is the frontage the plate draws:
       the widest free strip is 8.00 m, at E 804.2
       relief <= 0.30 m       0
       relief <= 0.35 m       0
       relief <= 1.00 m       3
       no relief clause       3

## What it says, and what it corrects

**1. The refusal holds, and it holds far more strongly than the 1.7 m reading did.** Not
one position on the whole reach, at any bearing, takes the smallest footprint the family
allows on ground flat enough for the walker — 0 at 0.30 m of relief, 0 at 0.35 m. The
plate's south-bank warehouses cannot be sited outside the platted corridor at this reach.

**2. But "there is no ground" was wrong, and the correction matters.** 124 of 143 stations
DO carry dry ground outside a corridor. The reading at E 697 was the narrowest station on
the reach, not a typical one: the free strip beside the platted street widens eastward to
8.00 m by E 804. What defeats a building there is not width, it is **slope**. That strip
is the river bank itself, falling from about +0.6 m to the water inside its own width, and
the three positions on it that accept a footprint at all span 0.96–0.98 m of relief —
better than three times the walker's step tolerance. A building put there would not share
one walker surface without a cut or a fill, which is the same clause the north bank sheds
were held to and passed at 0.30 m.

**3. The widest free ground on the reach is not on the plate's frontage at all.** The
26.50 m strip at E 813.2 lies EAST of South Water Street's committed platted line, which
ends at E 805 — it is the east bank of the town slough, under `slough_log_bridge`, between
the slough and State Street's corridor. Ground there answers a different question from the
one the plate asks, which is why the tool reports the two apart rather than in one count
that would read as frontage the warehouses could have used.

## What is still open, and it is a decision rather than a number

The plate is not refuted by any of this. It draws warehouses on this bank, and the reason
they cannot be built is that **the platted 80 ft corridor of South Water Street occupies
the whole bank down to the water at this reach** — the roadway's legal reservation, not
its travelled way. `docs/LIBERTIES.md` L79 records that the visible tracks run 5.8–10.5 m
inside that 80 ft corridor, and `tools/plat_corridors.py` says in its own docstring that a
building inside a corridor is not necessarily a building in anybody's way. South Water
Street's travelled track is committed at 10.5 m, so about 7 m of legal corridor stands
between the wheel line and the corridor's north edge at this reach, on ground the
heightfield holds flat to within 0.05 m.

So the honest question this hands on is **not "where is the ground" but "may an invented
building stand on the river margin of a platted street corridor, where this town's own
warehouses and landings stood?"** That is a decision about what the dataset asserts, not a
missing measurement:

* it would be the first record in this project placed knowingly inside a corridor —
  the 29 that lap one today are documented records the plat was fitted around, and T-0009
  owns getting them out;
* `tools/measure_corridor_intrusion.py --gate` refuses a new lap by construction, and its
  written-refusal mechanism (T-0195) exists for documented records whose escape is
  blocked, not for admitting invented ones;
* and the five South Water landings (T-0062) and the two attested docks already stand on
  the wharfing-out practice of this bank, so the alternative reading — that what the plate
  draws on the south bank is wharfed out over the water rather than standing on it — is
  live and belongs to the wharf layer (T-0059), not to the ground.

That question is filed as its own ticket rather than answered here.

## What would replace this finding

A drawn width for South Water Street at the Dearborn reach on the 1834 sheets themselves,
measured against the traced bank; or a lot record on the river side of the street. Either
would move the corridor rather than the buildings, and the gate below is what would notice.

## The gate

`tools/measure_south_bank_ground.py --gate` runs in `tools/check.sh` against
`tools/south_bank_ground_baseline.json`. It fails if a fit appears — on the reach or,
separately, beside the platted street — because a fit appearing is this question
re-opening and not a number to bank. It is the assertion that fires the day the terrain is
extended, the plat is re-derived or the waterline is re-traced.

**Links:** T-0134 · T-0133 · T-0071 · T-0009 · T-0059 · T-0195 · `docs/LIBERTIES.md` L79,
L164 · `data/exclusions.json` → `south_bank_warehouses_dearborn_reach`.
