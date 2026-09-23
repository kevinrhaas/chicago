---
id: T-0516
title: 31 inf_ roofs still stand as inferred_household for 101 households that no longer exist, and about 140 records name them in prose
state: done
epic: TOWN
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-04
pr: 843
claimed_by: run 9/4/2026, 10:27:42 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T04:26:18.353Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33941752969
---

**The owner's ask, 2026-09-03, verbatim:** "later we will add reconstructed people, but i would like to
remove any pre-existing reconstructed people from the resident list and household like now that we have
more complete information, when you remove a reconstructed resident, make sure that if there is a
structure you already made for them, you can abandon that structure or remove it because we will want
to do a sweep later and assign these residents a place to live and work once we complete the full
3600ish resident list best we can." Asked which of the two to do, the owner ruled (2026-09-03):
**"Keep as anonymous stock"** — "Re-enrol them honestly in the 665-roof ledger as anonymous count-units,
strip the dead household references, keep the geometry for the later placement sweep."

**The finding.** PR #668 retired the 108 reconstructed people and 96 household containers and marked
the building stock `resident_assignment: unassigned` — the people half of the ask is done. The
buildings half is not: **31 `inf_*` structure records** still carry `reconstruction.status:
"inferred_household"`, a status the schema defines as "a roof the inferred-household layer raised
BECAUSE an argued household needed somewhere to be, and it carries an occupants block naming that
household" — and those households no longer exist. `data/reconstruction/1835_inferred_household_programme.json`
still lists 101 households and 38 buildings (only `resident_population_active: false` was added);
`tools/reconcile_665.py` still classifies a roof as `inferred_household_programme` by `rid in
households` from that file, so the 665-roof ledger credits 31 roofs to a programme that no longer has
people; and about **140 structure files and 183 sidecars** name a dead `hh_inf_*` id in their
`occupants.note` prose. A visitor clicking one of these roofs is told about a household that was
retired on 2 September.

**The ask.**

1. The 31 `inf_*` records: `reconstruction.status` → `inferred_anonymous` (the schema's other value —
   "a count-unit of the 665-roof programme, placed by aggregate mix and carrying no occupant"), the
   `occupants` block rewritten to say what is true ("anonymous stock; the household this roof was raised
   for was retired 2026-09-02 under the owner's ruling; unassigned until the placement sweep"),
   `resident_assignment` kept `unassigned`. No geometry edit — the roof is the same roof.
2. `1835_inferred_household_programme.json` becomes a RETIRED programme record: the 101 households
   listed as `retired` with the date and the ruling, the 38 buildings as anonymous stock, the occupation
   census kept as history with a note pointing at **T-0507**'s calibration as its successor; or, if that
   is dishonest to the file's own `_doc`, a new `1835_anonymous_stock.json` and the old file kept as
   history — decide, and say why in the PR.
3. `tools/reconcile_665.py`: classify by the record's own status; the 31 roofs enrol as anonymous
   stock; the ledger's totals before/after stated and the target argued if it moves (T-0032 records
   that the target has been wrong before).
4. Every `hh_inf_*` mention under `data/` (structures, sidecars via `tools/compile_scene.py`, the
   programme file excepted) rewritten to the truth; `data/residents/index.json`'s `structure_policy`
   sentence unchanged.
5. `tools/smoke_renderer.mjs` at both viewports — the cards changed; `needs_bake: false` because no
   geometry changed, and the PR says so.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- `grep -r hh_inf_ data/` returns only the retired programme record; 31 of 31 records restatused;
  the 665 ledger's group rows add up and the reconciliation's self-test still fires.
- `check.sh` green; smoke green at 390×780 and desktop; mirror published; a changelog entry.
- No structure removed, no geometry changed, no new occupant invented.

**Links:** PR #668 and `docs/RESEARCH/resident-household-synthesis-2026-09-02.md` · T-0389 (the
programme-membership rule) · T-0032 · `data/structures.schema.json` (`reconstruction.status`,
`resident_assignment`) · T-0507 · the future placement sweep.
