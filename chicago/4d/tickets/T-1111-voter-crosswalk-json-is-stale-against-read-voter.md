---
id: T-1111
title: voter_crosswalk.json is stale against read_voter_lists.py, and 35 of 345 voters stand unmatched behind it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-13
closed: 2026-09-14
pr: 1332
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T16:23:42.455Z
claimed_run: null
---

voter_crosswalk.json is stale against read_voter_lists.py, and 35 of 345 voters stand unmatched behind it.

**Found by T-0896, 2026-09-13**, which measured `--check` on every tool `tools/check.sh` never runs one on. The reason is recorded beside the tool in `data/research/check_gate_baseline.json`, and the gate there now refuses a row that states none — so this ticket is what makes that row go away.

    $ python3 tools/read_voter_lists.py --check
    FAIL  voter_crosswalk.json is stale or hand-edited; regenerate with
          tools/read_voter_lists.py --build
    voter lists: 345 entries, 297 matched, 13 candidate, 35 unmatched

345 entries is a large reading, and the crosswalk is where it reaches the town's residents.
Stale, it is 35 unmatched and 13 candidates standing on a layer that has moved underneath
them — the same shape of fault T-0867 found in the advertising directory's crosswalk, and
for the same reason: a committed output nobody re-derives.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The cause named before the rebuild — stale against a moved residents layer, or edited.
- The rebuild's effect on the town stated in numbers: which of the 297 matches, 13
  candidates and 35 refusals move, and what that does to the cards they reach.
- `--check` green, gated in `tools/check.sh`, and `audit_check_gates.py --write` re-run in
  the same commit.

**CLOSED BY T-1029, PR #1332.** The two tickets asked the same question of the same file —
this one found it via T-0896's `--check` sweep, T-1029 via T-1026's re-derivation — so the
one diff closes both rather than the second run rebuilding it. Against the acceptance stated
above: the cause is **stale against a moved residents layer**, not an edit (849 resident cards
when the crosswalk was last built on 2026-09-03, 1,308 now). The effect in numbers: matched
99 → 300, candidate 82 → 11, unmatched 164 → 34, with 128 `unmatched → matched` and 73
`candidate → matched` and nothing moving backwards; the identity file's T-0493 refusals fall
82 → 26. What it does to the cards is that `spend_civic_voter_lists.py` now writes 300 rulings
onto 239 of them, up from 99. `--check` is green, `tools/check.sh` runs it, and
`audit_check_gates.py --write` was re-run in the same commit — the row naming this ticket is
out of `check_gate_baseline.json` and the ratchet stands at 13 ungated.
