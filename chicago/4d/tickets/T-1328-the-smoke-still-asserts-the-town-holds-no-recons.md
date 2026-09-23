---
id: T-1328
title: The smoke still asserts the town holds no reconstructed people, and the owner's ruling put three there
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-18
closed: 2026-09-18
pr: null
claimed_by: null
blocked_on: Duplicate of T-1327, which dev filed for the same finding: the smoke's retargeted K18 check asserts the resident layer holds no reconstructed person and the reconstruction programme seated three. T-1326 measured it independently (desktop part 2-3, 2026-09-18) and the reading is in that PR; the analysis this file held — that the live promise is T-1158's 'a reconstructed person declares itself' rather than 'there are none' — belongs on T-1327.
needs_bake: false
closed_at: 2026-09-18T17:19:52.666Z
claimed_run: null
---

The smoke still asserts the town holds no reconstructed people, and the owner's ruling put three there.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Measured, on a steward run, 2026-09-18 16:5x UTC, desktop part 2-3, `--published`:**

```
FAIL  desktop 1280x800: the invented-name programme left nothing behind on this layer
      — 3 reconstructed people in the manifest, 0 on hh_inf_cooper_north_04,
        name_basis present: false
```

`tools/smoke_renderer.mjs:6230` asserts `index.counts.by_grade.reconstructed === 0`. It was
written that way for a reason that was true when it was written: T-0489 retired the invented-name
population, `data/residents/index.json` read `reconstructed: 0`, and the check was deliberately
turned round from "the invented names declare themselves" to "the invented-name programme left
nothing behind", so that a future run minting one would trip it.

A future run has, and it was not a mistake. The reconstruction programme (v946 and v948 in the
walkthrough's release notes, merged into dev on 2026-09-18) seats three reconstructed people, each
named from the period pools, each carrying `basis`, `seed`, `replaceable_by` and the stage that
wrote it — which is exactly the contract T-1158 asks of a reconstructed value. `tools/check.sh`
passes them: "3 reconstructed person(s) in data/residents/, each holding the record contract".

So the smoke and the gate now disagree about the same three people, and the smoke is the one that
is out of date. The check is red on `dev` itself: measured identical on `origin/dev`'s
`index.json` (`{attested: 410, inferred: 875, reconstructed: 3}`), on a branch whose diff does not
touch that file.

**What the check should assert instead.** Not `reconstructed === 0` — that ruling is superseded.
The live promise is the one T-1158 states: every reconstructed person declares itself. So:
`name_basis` may exist, and where it does it must carry its basis and its seed; and no person may
be graded `reconstructed` without the reconstruction contract on the record. That keeps the wire
the comment at `smoke_renderer.mjs:6180` argues for — a check that trips when an *undeclared*
invented name comes back — while letting the declared ones through.

**Found by:** T-1326, whose own diff adds no person and cannot cause it. Its PR records the
reading rather than bending the check.
