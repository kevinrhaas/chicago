---
id: T-0284
title: Two slices of one batch claimed T-0256 and both built it — a claim is written where the next slice cannot see it
state: withdrawn
epic: PIPELINE
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-28
pr: null
claimed_by: null
blocked_on: Duplicate of T-0238, which owned this defect a day earlier with the mechanism established rather than hypothesized. Filed without searching the ledger — the identical fault T-0236 records. Its measurement (the 14% collision rate) is preserved on T-0238.
needs_bake: false
---

**T-0256 — the ticket that made the newspaper corpus citable — was claimed twice
and built twice, by two slices of the same batch, four minutes apart.** Both
finished. Both opened a pull request. One merged.

## Measured, from the two branches' own copies of the ticket file

| | `claimed_by` | PR | outcome |
|---|---|---|---|
| slice A | `run 8/28/2026, 4:31:14 AM CT` | **#448** | merged to `dev` as `eae02528` |
| slice B | `run 8/28/2026, 4:35:22 AM CT` | **#454** | open, now labelled `hold` |

Both descend from the eight-slice batch dispatched at **09:15:36–09:16:07 UTC**
(polecat-platform runs 1183–1190). The claims land 15 and 19 minutes after
dispatch, which is a slice's normal checkout-then-claim delay.

Read the two `claimed_by` values against each other: this is not a re-run of one
slice, and it is not one slice claiming twice. They are different runs.

## Why the loop's own design did not prevent it

A slice is told `SLICE: k of N` and takes **the k-th topmost workable ticket**.
That rule cannot produce a collision on a fixed list — two different `k` select
two different rows. So the list was not fixed. **A claim is recorded by writing
`claimed_by` into the ticket file on the claiming run's own branch**, and `dev`
does not learn about it until that branch merges — typically thirty to ninety
minutes later. For essentially the whole of a run's life, its claim is invisible
to every sibling.

## What is NOT yet known, and must be measured before anything is changed

Naming a mechanism is not the same as showing it, and the obvious diagnosis is a
guess. Do not skip to the fix.

- **The ranking-shift hypothesis.** If a ticket ABOVE T-0256 stopped being
  workable between 09:31 and 09:35 — closed, blocked, or claimed-and-merged —
  every row below it shifts up one, and slice `k+1` lands on the row slice `k`
  already took. This is testable: the two runs' logs both record the list they
  ranked, and `dev`'s history over that four-minute window is readable.
  **Plausible, and not established.**
- **How often it happens.** One observed collision says nothing about the rate.
  Every merged PR carries the `claimed_by` of the run that made it, so the whole
  ledger can be swept for two PRs bearing the same ticket id — that is the
  measurement, and it wants doing before the cost is argued about.
- **Whether wider batches make it worse.** The batch width went 3 → 5 → 8 today.
  If the cause is ranking shift, the exposure grows with both N and run length.
  **Untested.** Do not assume it, and do not narrow the batch to "fix" this
  before the rate is known — that trades known throughput for an unmeasured gain.

## Candidate answers, in the order they should be considered

1. **Measure first** — the sweep above, and the two runs' ranked lists.
2. **Put the claim where a sibling can see it.** The claim is a fact about the
   fleet, and it is currently written only into a branch. Somewhere shared — the
   steward journal already carries a per-run marker, and `claim-notice.sh`
   (polecat-platform#145) already writes the claimed ticket there at claim time —
   would let a slice check what its siblings took. That existing work was built
   for *visibility*; this asks whether it can also serve as the *interlock*.
3. **Make the k-th selection stable against a shifting list** — rank once per
   batch rather than once per slice, so all eight select from one snapshot.
4. **Detect it after the fact and fail loudly.** A second PR for a ticket already
   `done` should be refused by the gate, not merged by a janitor. Today nothing
   noticed; a human reading the PR list found it.

## The cost, so the priority is arguable on evidence

Not merely a wasted run. The two slices **split the work differently**, so the
duplicate is not the same code twice:

- merged (#448): `tools/newspaper_corpus.py` — one tool, `--build` / `--check` /
  `--self-test`
- open (#454): `tools/build_newspaper_corpus.py` + `tools/check_newspaper_corpus.py`
  + `tools/docx_text.py`

Both generate `data/research/newspapers/corpus.json`. Merging the second would
have left two programs claiming to be the source of truth for one generated file,
in a subtree the whole PAPERS epic now resolves citations through — and T-0276
had already edited what the merged builder writes. **The janitor would have
merged it**: the branch is `steward/`-prefixed, not draft, and carried no label.
It was caught by a person reading the open-PR list, which is not a mechanism.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The collision rate is **measured across the merged ledger**, not inferred from
  this one case, and stated as a number with the window it covers.
- The ranking-shift hypothesis is **established or refuted against the two runs'
  own logs** — not adopted because it is the tidiest story available.
- A second PR against a ticket already `done` **fails a check** rather than
  depending on someone reading the PR list.
- If the batch width is changed, the change comes **after** the rate is known and
  cites it. A narrower batch is a throughput loss and must be paid for with a
  measurement, not a worry.

**Links:** #454 (parked with `hold`, and the salvage question is on that PR) ·
#448 (the merged twin) · T-0276 (edits what the merged builder writes) ·
T-0236 (the heartbeat's own gap — the other loop defect found by reading a run
list by hand, and the same lesson about visibility) ·
polecat-platform#145 (`claim-notice.sh`, candidate 2's raw material).
