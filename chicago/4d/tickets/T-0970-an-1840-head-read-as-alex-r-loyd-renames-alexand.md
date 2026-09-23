---
id: T-0970
title: An 1840 head read as 'Alex[r]. Loyd' renames Alexander Loyd's card to hh_loyd_a and strips his directory evidence
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-07
closed: 2026-09-07
pr: 1040
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-08T04:25:36.073Z
claimed_run: null
---

An 1840 head read as 'Alex[r]. Loyd' renames Alexander Loyd's card to hh_loyd_a and strips his directory evidence.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found while landing T-0964's reading of printed 220. It is why that PR ships the reading and
leaves the derived chain unrebuilt.

**What happens.** Line 12 of `33SQ-GYYJ-P5` is read `Alex[r]. Loyd` — the enumerator's raised-r
contraction, with the r bracketed because the stroke is not settled. `crosswalk_census_1840_heads.py`
rules it **matched** to `loyd_alexander` (correctly: the 1843 directory writes the forename out in
full at a stated address, which is a discriminator independent of the name). The ruling then
travels, and by the time `mint_civic_residents.py --check` sees it the derivation wants a
DIFFERENT card:

    hh_loyd_alexander / loyd_alexander   ->   hh_loyd_a / loyd_a
    "Alexander Loyd"                     ->   "A Loyd"
    present_on_scene_date: present       ->   uncertain
    directories block                    ->   dropped
    arrival sources: democrat + 1843     ->   democrat alone

That is a man losing his forename, his directory and his place on the scene date because a new
source spelled his name with a contraction. `spend_fergus_1839_later_lists.py --check` then
fails from both ends at once — `hh_loyd_a/loyd_a — the record the ruling names does not exist`
and `hh_loyd_alexander/loyd_alexander — carries this pass's paragraph and no crosswalk match
names them`.

**The reading is not the fault and must not be bent to fit.** `Alex[r].` is what the sheet says.
The temptation is to write `Alexander Loyd` into `as_read` or `normalized` so the pipeline
resolves it, and that is transcription written to please a tool. What wants deciding is which
layer may let a NEW source rename an EXISTING card at all: a match is an assertion that two
records are one man, and the senior name should be the one the town already holds, not the one
the newest source happens to print.

**Two questions, and the second may be the owner's.**
1. Should `Alexr.`, `Jno.`, `Wm.`, `Thos.`, `Chs.` and `Jas.` — every contraction this corpus is
   full of — expand for identity purposes, and where?
2. When a matched head's name form differs from the card's, may the card be renamed at all? The
   safe answer is no: a match adds evidence to a person, it does not re-christen them.

Scope: `mint_civic_residents.py`'s card-naming derivation and `consolidate_resident_evidence.py`,
plus a re-run of the whole derived chain. Until it is ruled on, T-0964's two page files sit on
dev with the chain unrebuilt and `crosswalk_census_1840_heads.py --check` red at
`849 head(s) on disk, 910 read from the pages`.


Resolved in T-0976 / PR #1040. The original reading above is preserved. See `docs/RESEARCH/open-pr-reconciliation-2026-09-08.md` for the repair, its limits and regression tests.
