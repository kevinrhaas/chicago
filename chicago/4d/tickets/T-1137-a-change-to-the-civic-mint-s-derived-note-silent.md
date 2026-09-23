---
id: T-1137
title: A change to the civic mint's derived note silently deletes every other pass's findings appended to the same card
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-14
closed: 2026-09-15
pr: 1364
claimed_by: Codex 9/15/2026, 2:49:01 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-15T20:25:51.900Z
claimed_run: null
---

A change to the civic mint's derived note silently deletes every other pass's findings appended to the same card.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-1131, which hit it: the ticket changed one sentence of `arrival_block`'s note
and `--build` deleted about 6,000 characters of other passes' prose off
`hh_wolcott_alexander` — the Calumet Club receptions of 1879 and 1882, the federal land
tract sales, the town's own rolls. The change was reverted for that reason alone, so the
defect is still there and the next run that touches this pass's prose will hit it again.

**THE DEFECT.** `mint_civic_residents.carry_over()` preserves another pass's additions to
a person's note by prefix match:

    was = (old.get("note") or "")
    if was.startswith(person["note"]) and len(was) > len(person["note"]):
        person["note"] = person["note"] + was[len(person["note"]):]

The contract is "the derived note is a PREFIX of the committed one, and everything past it
belongs to somebody else". Change one character of the derived prefix and the match fails,
the branch does not fire, and every appended finding is dropped — silently, in a
`--build` that reports `wrote 415 file(s)` and nothing else. `--check` then passes on the
next run, because the truncated note is what re-derives.

**HOW IT SURFACED AT ALL, and it was luck.** `old_settlers.py --check` has its own gate
and went red with `wolcott_alexander ... does not say what the old-settlers roll is worth
— run --apply-citations`. The land-sales and civic-rolls appenders have no such gate, so
their prose would have gone and nothing would have said so.

- The boundary between this pass's prose and another pass's is held by something better
  than a prefix match — a marker, a structured field, or the appending passes writing
  where they cannot be truncated. Say which and why.
- A change to this pass's derived note does not delete another pass's findings, proved by
  a `--self-test` case that changes the derived prose and asserts the appended text
  survives.
- The same question is asked of the sibling mints that share `carry_over`'s contract.
- No card hand-edited; `--check` re-derives byte for byte. `bash tools/check.sh` green.

**THE SIBLING MINT IS THE SAME, AND IT IS WORSE. Measured by T-1141, 2026-09-15**, under
the fourth acceptance clause above ("the same question is asked of the sibling mints").

T-1141 needed two names lifted into the letter-list pool, which is a two-entity change to
one extraction, and ran the pass that owns that pool to find out what the refusals would
do with them:

    python3 tools/mint_letter_list_residents.py     # the writer, not --check
    744 files changed, 3356 insertions(+), 25932 deletions(-)

That is on the COMMITTED TREE WITH NO EDIT OF ANY KIND — the run above was repeated after
`git checkout -- .` and produced the same 744 files. So this is not the two-entity change
propagating; the committed town is simply not what its own writer writes, and the writer
is the one that loses the difference. Whole households are DELETED (`hh_abbott_constant`,
`hh_allen_william`, `hh_young_gideon` among them) and `data/residents/index.json` is
rewritten across 4,943 lines.

What makes it worse than the civic case rather than merely equal: `--check` is green on
that same tree, and `check.sh` runs `--gate` and `--self-test` and neither notices. So the
pass has a `--check` that passes on a tree its own `--build` would not produce, which is
the failure this ticket names, one layer further out. A run that touches the letter-list
pool for any reason at all — a lift, a re-read, one corrected name — cannot run the writer
without taking those 25,932 deletions with it, and has no way to tell which of them are
this pass's own output and which are another pass's findings standing on the same cards.

T-1141 stopped there rather than ship it, and its own two tails wait on this ticket: the
lift of `P. Cook` and `Jeter Foster` into the pool, and the movement of the 28 readings the
page overturns. Both are one small edit and one run of a writer that cannot currently be
run.
