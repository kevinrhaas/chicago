---
id: T-0838
title: Gate the synthesizer's drift: the committed cards must re-derive from the writer that owns them
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0814
opened: 2026-09-05
closed: 2026-09-05
pr: 917
claimed_by: run 9/5/2026, 3:25:53 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T20:38:58.596Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33989596649
---

Gate the synthesizer's drift: the committed cards must re-derive from the writer that owns them.

Piece 1 of 2 of **T-0814 — The synthesizer's write has drifted hundreds of household cards away from the repository and --check cannot see it, so T-0509's eight corroborations never reach a card**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

`tools/check.sh` fails when `synthesize_resident_research.py` would change a committed
file it is not already known to disagree with, and that failure is demonstrated against
a real card rather than asserted.

## What was measured, and what shipped

**The drift, twice, on this run's own checkout of `dev` at 4ab5b39cf.** A fresh run of
the writer changes **271 files** — 132 authored household cards, 135 in the published
mirror, plus the index, the ledger, the summary and the census crosswalk. (The parent
measured 108 authored cards on 2026-09-05; `dev` has moved since, and the two figures are
the same fact at two commits.) `--check` was green on that tree the whole time: it
re-derives the population in memory and validates its invariants, and never asks whether
that derivation matches the cards on disk.

**`--drift`, the ratchet.** It copies the three trees the writer writes into a throwaway
root, symlinks the reference library it only reads, runs the REAL writer against the copy
in a subprocess, and compares every file byte for byte. 3.3 s, and it cannot touch the
working tree — verified: `git status` is unchanged across a run.

*Why a scratch tree and not a `write=False` derivation.* The committed state is this
writer FOLLOWED BY `apply_census_1840_bridges.apply()`, which the tail of `main()` runs so
that a run of either tool converges on the same bytes (T-0491). A synthesis-only
derivation would report drift wherever the bridges own the answer. Running the real pair
against a copy is what the parent's own measurement did, and it cannot drift from the
thing it checks.

*Why a ratchet and not a hard fail.* The 271 files standing are unspent promotion that
wants reading before it lands — T-0837 owns that. A hard fail would have turned check.sh
red for every run in the repo until that reading was done. So the standing drift is
written down file by file in `data/research/residents/synthesis_drift_baseline.json`: a
file that drifts and is not listed fails, and a listed file that stops drifting fails too,
so the list can only shrink and a spend has to shrink it in its own commit. **New
invisible drift is what this makes impossible.**

**Demonstrated, not asserted.** `hh_abbot_8_g.json` — a card NOT on the baseline — had one
`resident_research.outcome` altered; `--drift` failed on it by name, and passed again when
it was restored. A ghost path added to the baseline made the healed direction fail. Both
directions are also held by `--drift-self-test`, wired into check.sh beside the gate.
