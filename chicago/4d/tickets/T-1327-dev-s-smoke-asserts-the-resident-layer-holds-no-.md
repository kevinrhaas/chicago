---
id: T-1327
title: Dev's smoke asserts the resident layer holds no reconstructed person, and since T-1314 it holds three: the retargeted K18 check is stale again
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-18
closed: 2026-09-18
pr: 1466
claimed_by: run 9/18/2026, 1:47:33 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T19:04:55.522Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35381768605
---

Dev's smoke asserts the resident layer holds no reconstructed person, and since T-1314 it holds three: the retargeted K18 check is stale again.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Measured on a steward runner, 2026-09-18, on `steward/t-1311-…` whose diff touches no
resident file at all (`git diff origin/dev...HEAD -- data/residents` is empty):

    FAIL  desktop 1280x800: the invented-name programme left nothing behind on this layer
          — 3 reconstructed people in the manifest, 0 on hh_inf_cooper_north_04,
            name_basis present: false

`data/residents/index.json` on `origin/dev` reads
`counts.by_grade.reconstructed: 3`, written by T-1314 (#1453) when stage
`named_families` seated the three people the 1840 census counts in a bridged head's
house. So the assertion is inherited red, not caused by the branch that found it.

The assertion is T-0524's retarget of the retired K18 check: T-0489 removed the
invented-name population, `reconstructed` went to 0, and rather than delete a
passing-shaped check T-0524 turned it round to assert the OPPOSITE promise — that the
programme left nothing behind. T-1167 then made `reconstructed` a GRADE THE PROJECT
WRITES ON PURPOSE, with a stage, a basis and a seed on every person, and twelve more
stages queued behind it. The promise the check states is no longer the project's.

What must NOT happen is the thing T-0524 itself forbids: deleting the check because it
is in the way. What the layer promises now is narrower and still worth a gate — no
reconstructed person without a stage, a basis and a seed, and no `name_basis` block
coming back — which is what `reconstruct_residents_1835.py --check` already refuses
record by record. The smoke's job is to prove the CARD says it.

**Acceptance:** the assertion states the promise the reconstruction programme actually
makes, reads the count from the manifest rather than hardcoding one (it will move on
every stage from T-1171 to T-1178), and the PR says which promise replaced which.
Desktop part 3 runs green on `--published`. No check deleted without the sentence
T-0524 requires.

**Links:** T-0524 · T-0489 · T-1167 · T-1314 · `tools/smoke_renderer.mjs` ·
`tools/dev-smoke-state.mjs`.

---

**Measured independently on T-1326's branch, 2026-09-18, desktop part 2-3, `--published`:**

```
FAIL  desktop 1280x800: the invented-name programme left nothing behind on this layer
      — 3 reconstructed people in the manifest, 0 on hh_inf_cooper_north_04,
        name_basis present: false
```

`index.counts.by_grade` reads `{attested: 410, inferred: 875, reconstructed: 3}` identically on
`origin/dev` and on a branch whose diff does not touch that file, so the red is dev's.

**What the check should assert instead, and why the wire is worth keeping.** Not
`reconstructed === 0` — that ruling is superseded. The comment at `smoke_renderer.mjs:6180`
argues for a check that trips when an *undeclared* invented name comes back, and T-1158 states
the live promise: every reconstructed value carries tier, basis, seed and `replaceable_by`. So
`name_basis` may exist; where it does it must carry its basis and its seed, and no person may be
graded `reconstructed` without the reconstruction contract on the record. `tools/check.sh`
already holds that half — "3 reconstructed person(s) in data/residents/, each holding the record
contract" — which is why the gate is green while the smoke is red. (T-1328 was filed for this
before dev's copy was visible on the branch, and is withdrawn to here.)

**A SECOND DEAD ASSERTION IN THE SAME PART, FOUND 2026-09-18 BY T-1320's SMOKE LEG.**
`desktop 1280x800: the placeholder label agrees with the asset it describes` cannot pass
and never has. `tools/smoke_renderer.mjs:7218` reads `placeholder.whereholderFlag`; the
object the page evaluates carries `placeholderFlag`, so the left side is always
`undefined` and the comparison is always false. It is the "both directions" half added
beside the three placeholder checks that DO pass, and it has been red on every desktop
part 2-3 run since. Filed here rather than as a new queue line because this ticket
already owns "a smoke assertion in this part has rotted and says nothing"; the
`dev-smoke-state` record for desktop parts 2 and 3 names only the K18 failure, so
whoever takes this should expect two.
---

**Done, 2026-09-18.** The wire was turned round a second time, not cut. One check
became three, and the count is read off `index.counts.by_grade.reconstructed`
rather than written into the gate:

- `nothing was drawn into an evidence-only household` — T-0489's ruling, kept on
  the population it was made about (`hh_inf_*`: a head the papers name, no
  `name_basis`, nothing drawn in).
- `the manifest's reconstructed count is the layer the records hold` — manifest
  count, the index's own household rows summed, and the records themselves, all
  three agreeing. It fetches the two households the index says carry a
  reconstructed person, not the other 1,256.
- `every reconstructed person carries its stage, basis, seed and replacement` —
  T-1158's promise: a programme stage, a `basis` with kind/id/note, the `seed`
  that redraws a `model` draw, `replaceable_by` naming the evidence that retires
  them. And the live half of K18: a `name_basis` on a person **not** graded
  `reconstructed` is an undeclared invented name coming back, and it trips.

Measured on a steward runner, both `--published`:

    desktop 1280x800, stage 2-3: 168 passed, 1 failed (3 m 46 s)
    mobile  390x780,  stage 1-3: 240 passed, 1 failed (3 m 29 s)

      pass  nothing was drawn into an evidence-only household
      pass  the manifest's reconstructed count is the layer the records hold
      pass  every reconstructed person carries its stage, basis, seed and replacement

The one red left on both legs is **T-1331**, and it is dev's: `smoke_renderer.mjs`
reads `placeholder.whereholderFlag` — a field nothing writes — so
`the placeholder label agrees with the asset it describes` is permanently red.
The typo is on `origin/dev` at line 7218 and is not in this diff.

`./tools/check.sh` — CHECK PASS, 495 steps, none red. No reader missing: the
gate's first step reports PIL, numpy and scipy all installed.
