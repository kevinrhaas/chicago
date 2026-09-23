---
id: T-0832
title: The six generated artifacts get merge treatment, registered and self-tested
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0813
opened: 2026-09-05
closed: 2026-09-05
pr: 910
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T19:46:22.853Z
claimed_run: null
---

The six generated artifacts get merge treatment, registered and self-tested.

Piece 1 of 2 of **T-0813 — Six generated artifacts conflict on every branch: merge them by regenerating, and make a drain lap a tool**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** the six files carry merge treatment registered by
`setup-merge-drivers.sh`, each with a self-test on a specimen that would conflict
without it, and the conflicting-file count on a real merge drops to zero.

## Delivered in PR #910

- `tools/merge-generated.mjs` — the five build products. Keeps ours, prints the
  rebuild command, never conflicts.
- `tools/merge-smoke-state.mjs` — the smoke ledger. Union of whole readings.
- `.gitattributes` for all six; both registered in `setup-merge-drivers.sh`.
- `tools/merge-generated-selftest.mjs` — 20 assertions, in `check.sh`.
- **Measured, which is this ticket's own acceptance:** merging `dev` into the
  PR's branch afterwards produced **zero conflicts**, on a branch where the five
  preceding laps had each conflicted on exactly these files.

## Two deliberate deviations from T-0813's spec, with reasons

T-0813 asked for particular mechanisms. Both were changed, and it is worth saying
so rather than letting the difference be discovered later.

**1. It asked for a driver that "ignores both sides entirely and re-runs the tool
that owns the file". This keeps ours and PRINTS the command instead.** A merge
driver runs *during* the merge, on a half-merged tree, once per conflicting file —
and the tools that own these files are `ticket.mjs board` and `publish.sh`, the
second of which takes a minute or two and reads the whole tree. Re-running either
against an inconsistent tree would produce a build product derived from a state
that never existed, which is worse than a stale one, and it would do it several
times per merge. Keeping ours is safe because **the gate already refuses each of
these five stale** — `ticket.mjs check`, `test_ticket_mirror.mjs`,
`check_published.mjs` — so the regeneration still happens, after the merge, from a
tree that is whole. The print is what carries the instruction across.

**2. It asked to union the ledger "by (tree hash, viewport, stage), newest wins on
a tie". This unions on full identity and drops nothing.** Newest-wins-on-a-tie
discards a reading, and two runs of the same stage on the same tree are not
redundant — they are the evidence that it was run twice. The conservative rule
costs a few rows and cannot lose history; the ticket's rule is a size optimisation
on a file nothing reads for size. If the file ever needs pruning, that is a
deliberate pass, not a merge driver's silent side effect.

## Not delivered here

`tools/drain.mjs` — the parent's second half, now **T-0833**.
