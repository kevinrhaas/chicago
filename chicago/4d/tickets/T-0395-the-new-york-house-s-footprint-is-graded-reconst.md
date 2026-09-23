---
id: T-0395
title: The New York House's footprint is graded reconstructed but its note cites a source, and the gate warns
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: stale: the New York House note now reads INVENTED and the audit is silent
needs_bake: false
closed_at: 2026-09-10T04:20:12.093Z
claimed_run: null
---

`tools/check.sh` prints, and has printed since PR #536 (T-0380) landed:

```
warn: new_york_house footprint: reconstructed, but the note says a source states it
      — this may be graded too low.
```

It is a WARN, not a fail, so the gate is green with it standing — found while
repairing T-0389, which was the hard failure on the same record.

**What the grader is objecting to.** The footprint is graded `reconstructed`, the
bottom rung, and its note quotes a source. The provenance gate's rule is that a note
saying a source states something and a grade saying nothing does are in tension: one
of the two is wrong.

**Which one is wrong is the judgement, and it is not obvious.** Andreas gives this
building no dimension at all — the 40 × 25 ft plan is the stock rectangle, and
`reconstructed` is honest about that. But Andreas DOES state the eaves-to-the-street
elevation, which is why the footprint is wider than it is deep rather than square, so
the note is not merely decorative either. The likely repair is to the NOTE — separate
what Andreas states about the building's ORIENTATION from what the plan invents about
its SIZE — rather than to the grade, which should stay at the bottom rung.

Do NOT upgrade the confidence to silence the warn. `docs/LIBERTIES.md` already carries
the invented footprint; if the note is split, the liberty should say the same thing.

**Acceptance:**

- The warn is gone from `tools/check.sh`, and gone because the record and its note
  agree, not because the grader was loosened.
- If the grade stays `reconstructed`, the note says plainly which half of the
  footprint is Andreas's and which half is the stock rectangle.
- `docs/LIBERTIES.md`'s entry for this footprint reads the same way.

**Links:** T-0380 / PR #536 (authored the record) · T-0389 (the hard failure on the
same record, repaired first)
