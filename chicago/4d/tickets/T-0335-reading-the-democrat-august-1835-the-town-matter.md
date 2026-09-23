---
id: T-0335
title: Reading the Democrat, August 1835: the town matter of the four issues
state: done
epic: PAPERS
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: T-0297
opened: 2026-08-28
closed: 2026-08-28
pr: 500
claimed_by: run 8/28/2026, 8:09:16 PM CT
blocked_on: null
needs_bake: false
---

The four Democrats after the scene date: **1835-08-05** (Vol. II No. 16), **08-12**
(No. 17), **08-19** (No. 18) and **08-26** (No. 18 again, the printed number repeated) —
the paper's last month in the corpus. Piece 1 of 2 of **T-0297**, which is piece 3 of 4
of **T-0260**.

All four are `.docx`-only primaries whose derived text is committed under `text/`, so
every quote here is machine-verified by the gate with no deposit at all. `corpus.json`
records the August Democrat tail as single-pass OCR — weight a reading by the batch it
came from.

## What this piece owns

Everything the parent asks for EXCEPT the name-level extraction of the post-office
letter list, which is [[T-0336]]: persons, businesses, buildings, street and
infrastructure details, events, shipping and prices, into
`data/research/newspapers/extracted/<issue_id>.json`.

The three owner rulings of 2026-08-28 govern it unchanged and each lives in a field
rather than in prose — `letter_list_only` on a person, a required `reading` flag on
every claim, and a computed `built_at_scene_date` / `survival_liberty_required` on a
business. `tools/compile_gazetteer.py`'s header carries them in full.

## Why the parent was split, measured on 2026-08-29

The parent's letter list is not four lists. It is **ONE** list — letters remaining in
the Post Office at Chicago on **31 July 1835**, over J. S. C. Hogan's signature — set
once and printed unchanged in all four issues, some six hundred names across two
segmenter columns per printing. The parent T-0260 was itself split on exactly this
ground: "Reading that list is a run on its own ... so it does not belong in a batch
where it would be hurried." The same sentence applies here, and the four issues' own
town matter — the town ordinances of 5 August, a fire ordinance and a hay-stacking
boundary walked street by street, three schools opening, two doctors, a dressmaker, a
grocery near the draw bridge, a marriage, a death, the vessel arrivals and the prices
current — is a run's work beside it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- All four issues have an extraction file, and coverage of 1835-08-01 to 1835-08-31 is
  asserted BY THE GATE against `corpus.json`.
- Because all four texts resolve on `dev`, every quote is reassembled by the gate — no
  claim in this piece may be left unresolved.
- The post office is carried: the letter list's heading and the postmaster's signature
  are claimed in every issue that prints them, and the coverage note says in plain words
  that the names themselves are [[T-0336]]'s and are not minted here.
- An August advertisement that announces a NEW opening carries `announces_opening: true`,
  so T-0262 can keep it out of the July 1 town.
- The gazetteer recompiles green; new merges, if any, carry `merge_rule`.
- The PR states counts: claims, persons, businesses, placements by class.
