# Resident-research cohort inventory

Updated 2026-09-02 after PR #625 (fifth cohort) landed.

## Covered or reserved

| Cohort | Ticket / PR | Count | State |
|---|---:|---:|---|
| Pilot | T-0442 / prior merged pass | 75 | covered |
| Pass 2 | T-0462 / PR #622 | 75 | covered |
| Pass 3 | T-0463 / PR #624 | 75 | covered |
| Pass 4 | T-0478 / steward/resident-research-pass-4-reconciled | 75 | reserved/in flight |
| Pass 5 | T-0479 / PR #625 | 75 | landed; research ledger remains in progress |

The reservation ledger therefore contains 375 unique person IDs. Pass 4 is retained in the collision lock even while its reconciled branch is being finalized; no later cohort may reuse it.

## Remaining queue

The eligible remainder is 461 unique named, non-reconstructed residents whose household records are marked letter-list-only. The deterministic selector sorts person IDs within the scene-date-present and earlier/uncertain strata, interleaves the strata, and chunks that sequence in order:

| Next cohort | Ticket | Draft PR | Count | Present / uncertain |
|---:|---|---:|---:|---:|
| 6 | T-0480 | #627 | 75 | 38 / 37 |
| 7 | T-0481 | #628 | 75 | 37 / 38 |
| 8 | T-0482 | #629 | 75 | 38 / 37 |
| 9 | T-0483 | #630 | 75 | 37 / 38 |
| 10 | T-0484 | #631 | 75 | 31 / 44 |
| 11 | T-0485 | #632 | 75 | 0 / 75 |
| 12 | T-0486 | #633 | 11 | 0 / 11 |

Each ticket is open in the file-backed queue and each draft PR contains a frozen manifest, a pending-outcomes ledger and a research note. Draft PRs are scaffolds, not completed research; the next worker should claim the matching queue ticket and replace pending entries with dated corroboration, candidate/duplicate or documented no-corroboration outcomes.

## Deliberate exclusions

Reconstructed and hypothesised `inf_*` entries are outside the identity-research denominator. Seven remaining technical entries are unnamed/count or inferred household placeholders (including the Beaubien, Heacock, Owen, Robinson and Temple placeholder records); they are not silently converted into named people. No named non-letter-list residents remain after pass 5.

Surname similarity is a search clue only. Heritage, lineage, immigration origin, marriage, occupation, address and household membership require resolving evidence and must retain conflicts and candidate duplicates.

## What a manifest freezes, and what it does not (T-0764, 2026-09-06)

Each manifest carries two different kinds of thing, and only one of them is frozen.

**The reservation** — the person ids, in a fixed order — is the collision lock: it says
which people a pass owns, so two passes cannot claim the same person. It is re-derived
from the selector's frame on every `--gate` and must match exactly. So must every
document field outside the snapshot, and every id must still name a real, named person
in `data/residents/households/`; a member who leaves the town or turns into an unnamed
placeholder is staleness, and fails.

**The snapshot** — per person `starting_evidence`, `starting_grade`, `starting_presence`,
`starting_occupation`, `sources`, `letter_list_returns` and `stratum`, and the document's
`population_frame` — records the tree as it stood when the cohort was fixed. That is what
makes a finished pass legible: *this person came into the cohort at `inferred`, on one
source, and left it at `attested` on three.*

Until 2026-09-06 the snapshot was gated as if it were the reservation, by re-deriving the
whole document from today's tree and demanding equality. Two things followed, and both
were reported as defects in the manifest when neither was:

- researching a cohort writes a `resident_research` row onto its own members, so a
  completed pass failed its own gate — cohorts 13, 14 and 15 were red on all 76 of 76 of
  their people on 2026-09-05;
- a source landing on any member made the manifest read `stale`, and the documented
  remedy — regenerate without `--gate` — **overwrote the snapshot with today's values.**
  The freeze then dated to the last regeneration rather than to the day the cohort was
  fixed, silently, with no diff anybody read.

`tools/resident_cohort_freeze.py` now holds both halves: the gate asserts the reservation
and reports how many snapshot cells have moved since the freeze without failing on them,
and the write path carries the committed snapshot forward, so a regeneration cannot
rewrite it. A person the manifest does not yet hold is frozen at today's values, because
that is when their membership begins. Seventeen assertions run in `tools/check.sh`.

**What is not recoverable, counted.** The snapshots on disk are not the day each cohort
was fixed. Measured over `dev`'s history on 2026-09-06: of the **79 commits** that have
touched the eight gated manifests, **46 rewrote the freeze**, and **384 snapshot cells**
were overwritten that way. The gate called a moved snapshot `stale`, the documented remedy
was to regenerate, and the regeneration rebuilt every row from today's tree — so no diff
was ever read.

| manifest | commits | rewrote the freeze | cells overwritten |
|---|---:|---:|---:|
| `pilot_75_cohort.json` | 13 | 7 | 79 |
| `pass_02_75_cohort.json` | 16 | 10 | 92 |
| `pass_03_75_cohort.json` | 13 | 8 | 95 |
| `pass_04_75_cohort.json` | 6 | 0 | 0 |
| `pass_05_75_cohort.json` | 2 | 0 | 0 |
| `pass_13_76_cohort.json` | 9 | 7 | 50 |
| `pass_14_76_cohort.json` | 10 | 7 | 36 |
| `pass_15_76_cohort.json` | 10 | 7 | 32 |

Passes 4 and 5 are clean because they were fixed late and have barely been regenerated
since — not because anything protected them.

Lifting old values out of those commits and re-committing them today would assert a
provenance this project cannot show, so it is not done. The guarantee is forward only:
from the first write, a snapshot cell is written once.

*Provenance of this table: measured by PR #951, an independent implementation of T-0764
that #952 beat to the merge, and re-counted against `origin/dev` before landing here. The
46 rewrites and the 384 cells reproduced exactly; that branch's commit total read 82
because it counted its own commits as well as dev's.*
