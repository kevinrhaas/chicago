---
id: T-1073
title: dev's check.sh is red: moving the lighthouse onto Wright's glyph moved sauganash_range_m 1066.3 to 1001.2 and the Chappel baseline was never re-banked
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-12
closed: 2026-09-13
pr: null
claimed_by: null
blocked_on: Resolved by T-1083 (#1216) on 2026-09-13, which re-banked chappel_shore_lighthouse_baseline.json sauganash_range_m from 1066.3 to 1001.2 — the exact re-bank this ticket asked for. Verified rather than inferred from a green log: the town geometry is derived LIVE from the committed records and is gated whether or not an image library is present, and measure_chappel_shore_lighthouse.py --gate exits 0 on dev today.
needs_bake: false
closed_at: 2026-09-13T19:17:51.810Z
claimed_run: null
---

dev's check.sh is red: moving the lighthouse onto Wright's glyph moved sauganash_range_m 1066.3 to 1001.2 and the Chappel baseline was never re-banked.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

FOUND BY T-1071's gate, 2026-09-12, on a branch that had just merged dev.

`tools/check.sh` step **"the Chappel shore drawing still refuses to place its own station"**
(`tools/measure_chappel_shore_lighthouse.py --gate --quiet`) exits 1:

```
FAIL sauganash_range_m moved from 1066.3 to 1001.2 (tolerance 1.0)
```

**It is dev's, not a branch's.** Reproduced on a clean worktree of `origin/dev` at
`2ef6d60bb` — the same FAIL, the same exit 1, with nothing of T-1071 in the tree. So every
branch cut from dev now inherits one red step, and the next run that reads `CHECK FAIL` will
spend its budget on it before discovering that.

**What moved it.** T-1065 / PR #1189 put the lighthouse where Wright's own glyph draws it. The
Sauganash corner's range to the light is measured FROM that position, so it moved with it:
1066.3 m → 1001.2 m, 65.1 m against a 1.0 m tolerance. The reading in
`tools/chappel_shore_lighthouse_baseline.json` was banked against the old coordinate and was
not re-banked in that PR.

**What this ticket is NOT.** It is not an argument that the gate is wrong. The gate is doing
exactly its job — it caught a banked reading going stale under a coordinate change, which is
what it was built for. The work is to re-derive the reading against the new light position and
re-bank it, and to say in `docs/RESEARCH/chappel_shore_lighthouse.md` whether the verdict (the
drawing still refuses to place its own station) survives the move. It should: the refusal rests
on the adults not sharing a ground plane and on no fort standing beside the tower, neither of
which depends on the range. But it has to be re-read and said, not assumed.

**Links:** T-1065 · PR #1189 · `tools/measure_chappel_shore_lighthouse.py` ·
`tools/chappel_shore_lighthouse_baseline.json` · `docs/RESEARCH/chappel_shore_lighthouse.md`
