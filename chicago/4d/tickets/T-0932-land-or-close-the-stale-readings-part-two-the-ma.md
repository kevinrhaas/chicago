---
id: T-0932
title: Land or close the stale readings, part two: the map and book PRs — #955, #953, #841
state: split
epic: PIPELINE
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0929
opened: 2026-09-06
closed: 2026-09-07
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-07T09:03:57.789Z
claimed_run: null
---

These PRs carry real reading and their base is far enough behind `dev` that a lap is not
mechanical — the tree they were measured against is gone, and their numbers have to be
re-established before either landing or closing is honest.

`#955` (Wright's numerals read block by block), `#953` (the 1830 recapitulation re-counted), `#841` (Moses and Kirkland vol. 1 — the oldest base in the list).

**Each one gets the same three questions, in order:**

1. **Has its ticket already closed under another PR?** If so it belongs in T-0927, not here.
2. **Do its measurements still hold on today's `dev`?** Re-run them. A PR body's table is a
   reading of a tree that has since moved; landing it unchecked lands a number that is no
   longer true. Where a figure has moved, the PR body is corrected before the merge — the
   figure the branch shipped and the figure on the merged tree must be the same figure.
3. **Does anything it asserts contradict what has landed since?** This is the one that
   matters. #968 placed a warehouse on a corner the committed centrelines say does not
   exist; the only way that was caught was checking the claim against
   `data/streets/1835.json` rather than against the PR body.

`#991` and `#998` are flagged: `#991` says it "puts the question to the owner", and `#998`
rules on R6, which `#925` is parked on. Neither should land without reading the other.

**Acceptance:**

1. Each is merged, closed with its salvage recorded, or moved to the `hold` label with a
   written question — and no PR is left in none of those three states.
2. Any merged PR's body states figures that are true of the tree that actually merged.
3. Where a branch's claim is refuted, the refutation is written down with the evidence, and
   the open question behind it is filed. A refuted branch usually still holds a real
   question — #968's did, and it is now T-0869.
