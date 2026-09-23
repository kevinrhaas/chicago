---
id: T-0861
title: Eight newspaper claims print a street in their prose and their placement record carries none, so the reading ranks as an address that names no ground
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-11
pr: 1152
claimed_by: run 9/11/2026, 5:07:51 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T22:33:17.320Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34652380475
---

Eight newspaper claims print a street in their prose and their placement record carries none, so the reading ranks as an address that names no ground.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

FOUND BY T-0859, which asked whether a `street_only` placement carrying neither a
`street` nor an `anchor` is an address at all, and counted them: **twelve claims across
eleven houses.** The ruling there is about the PLACEMENT RECORD — it names no ground, so
it may not outrank a reading that does — and it is right whatever the notice printed. But
the count turned up something the ruling does not fix.

**Eight of the twelve notices DO print a street, in their own prose.** The reading pass
put it in the claim's business-level `street` field and left the placement empty:

| claim | prints |
|---|---|
| `chicago_democrat_1834_02_25#c003` David Carver | *"at his Store"* — no street. Correctly empty |
| `chicago_democrat_1834_03_04#c004` Hiram Pearsons | *"a lot and Store[hous]e on South Water Street"* |
| `chicago_democrat_1834_03_04#c010` Brewster, Hogan & Co. | *"at the old stand"* — no street. Correctly empty |
| `chicago_democrat_1834_03_04#c021` Newberry & Dole | no address. Correctly empty |
| `chicago_democrat_1834_03_25#c010` J. S. C. Hogan | no address (the cedar posts). Correctly empty |
| `chicago_democrat_1834_11_05#c008` Jno. S. Wilson & Co | *"Dearborn-stree[t]"* |
| `chicago_democrat_1834_11_12#c005` Briggs & Humphrey | *"a shop, on Randolph street"* |
| `chicago_democrat_1834_12_03#c016` Briggs & Humphrey | *"a shop, on Randolph street"* |
| `chicago_democrat_1834_12_17#c008` Pierce & French | *"at the corner of […] and Canal streets"* |
| `chicago_democrat_1835_08_05#c004` Samuel Lewis | *"at his room on south water street"* |
| `chicago_democrat_1835_08_05#c008` Jones, King & Co. | no address. Correctly empty |
| `chicago_democrat_1835_08_05#c016` W. Montgomery | *"Montgomery's Auction Room, South Water Street"* |

Seven of the twelve name a street the placement should carry, and one — Pierce & French —
prints a CORNER (*"the corner of […] and Canal streets"*, the first street name lost with
the type) that is read as `street_only` with nothing in it. Four are correctly empty and
are T-0859's population proper.

**Why it matters beyond tidiness.** `compile_register` adopts a street face off the
business-level `street`, so nothing is currently mis-placed by this. What is wrong is that
the READING does not say what the printing said, and every downstream instrument that asks
a reading what it names — `places_nothing`, `placement_rank`, the anchor rules, the
placement-silence report — gets an answer the page does not support.

**Acceptance:**

- Each of the eight claims either carries the street its own prose prints, in the
  placement, quoted; or a stated reason why the line will not support it.
- Pierce & French is read as the corner it prints, or its reading says why the lost street
  name means it cannot be.
- Nothing is invented: a claim whose prose names no street keeps an empty placement, and
  the business-level `street` is not read back into a placement it never had.
- `tools/measure_placement_silence.py` re-derives and the T-0859 count moves for the
  reason given.

**Links:** T-0859 · T-0440 · `docs/RESEARCH/outranked_printed_addresses.md` ·
`tools/compile_gazetteer.py` § `places_nothing`.
