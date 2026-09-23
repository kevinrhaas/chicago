---
id: T-0803
title: The published tree is 936 bytes under the 32 MiB budget, so no PR that publishes anything can pass validate.py again
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: 823
claimed_by: null
blocked_on: Superseded, and the fault is measured gone. All five of T-0722, T-0725, T-0731, T-0774 and T-0803 reported the SAME thing within one day — the published tree sitting a few hundred bytes under SITE_BUDGET_MB on dev at 06a0a9ec/1e9108aa, so the next PR to publish anything failed the gate. T-0722 fixed it in PR #836 by publishing changelog.js once instead of twice. Measured on this tree: 30.412 MB of 32, 1.588 MB of headroom, and ZERO pairs of published files over 64 KB with identical bytes — the condition #836's new validate.py rule now gates, so it cannot return the way it arrived. Withdrawn on the owner's instruction of 2026-09-05, 'do it if those tickets are useless now', after checking each one's own claim rather than the band's summary of them.  CORRECTION, same day: this reason first cited "30.412 MB of 32, 1.588 MB of headroom". The 32 came from tools/site_budget.py, which still hardcoded it while tools/validate.py — the gate that actually refuses a merge — had been raised to 36 by T-0593 (#823). The true figures are 30.5 MB of 36 and 5.5 MB of headroom, so the withdrawal stands and stands wider than stated. site_budget.py now reads SITE_BUDGET_MB out of the gate rather than restating it.
needs_bake: false
closed_at: 2026-09-05T19:59:09.129Z
claimed_run: null
---

The published tree is 936 bytes under the 32 MiB budget, so no PR that publishes anything can pass validate.py again.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Measured on `origin/dev` at 06a0a9ec on 2026-09-05, by summing the blobs under `site/chicago/4d/`:

```
origin/dev   33,553,488 bytes = 31.9991 MiB
budget       33,554,432 bytes = 32      MiB   (validate.py SITE_BUDGET_MB)
headroom            944 bytes
```

`tools/validate.py` `run_site_check()` errors the moment the published tree passes 32 MiB, and
that error fails the `dataset (schema, provenance, date gates, licenses, staleness, publish)`
step of `check.sh` — which `docs/PIPELINE.md` names as the dev gate and nothing else. So the
budget is not a warning any more; it is a **merge stop on every PR that publishes a byte**.

**The floor is already above the ceiling.** `dev` currently carries five sidecars that were
never recompiled (T-0728), and `compile_scene.py --all --check` fails on them, so any branch
must recompile them to pass the dataset step at all. Publishing that mandatory recompile costs
**7,207 bytes** — seven times the headroom. A branch that changes nothing else, adds no note,
writes no changelog entry and ships no comment still lands over budget.

T-0713 hit it first: its seventeen upgraded street notes reach `data/sidecars/1835/index.json`
(+22,257), its renderer comments reach `walk/js/streets.js` (+3,878), its changelog entry
reaches two mirrors (+3,886), and with the forced recompile that is +37,526 — 36,582 over.
Its PR is parked on `hold` behind this ticket and T-0728.

**What this ticket has to decide**, and it is the owner's call which:

- **Raise the number.** The comment beside it explains itself — "GitHub Pages cannot serve Git
  LFS objects, so this has to stay lean" — but Pages' own limit is 1 GB per site with a 100 MB
  per-file cap, and 32 MiB is a project discipline rather than a platform edge. If the number is
  a discipline it can be re-set on purpose; it should not be re-set by whoever happens to trip it.
- **Find the room.** The tree is 32 MiB of which the GLBs are the great majority. A census of
  what is published, by kind and by size, is the first honest step and no such census exists.
- **Stop publishing something.** The mirror is `publish.sh`'s verbatim copy of a growing dataset;
  if some of it is never fetched by a page, it is paying rent.

**What it must not do:** shrink a note to fit. The notes are the product, and a budget that is
met by writing less provenance has inverted what this project is for.

**Acceptance:** `python3 tools/validate.py --all` green on a tree that has just published, with
enough headroom stated as a number that the next PR is not this ticket again; the decision and
its reasoning recorded in a STATUS section; T-0713's PR unblocked or explicitly re-parked.

---

## CLOSED 2026-09-05 by T-0807 — the duplicate of T-0722, and answered with it

Filed four hours after T-0722 against the same wall, from a fresher measurement (944 bytes
of headroom at `06a0a9ec`, where T-0722 had read 32.1 MB over). Both numbers are true and
neither is rewritten; this is one stop with two ids, and T-0807's acceptance called for
exactly this reconciliation.

Its own acceptance, item by item:

- **"the decision and its reasoning recorded in a STATUS section"** — recorded better than
  asked, in the code the decision binds: the note above `SITE_BUDGET_MB` in
  `tools/validate.py` states 32 -> 36 as the third conscious re-budget (#823, T-0593), what
  exhausted 32 measured on dev, what supports 36, and what will exhaust it again named
  rather than discovered — the duplicated changelog (T-0364) and the letter-list cohort
  (T-0438).
- **"enough headroom stated as a number"** — 31,889,319 bytes = 30.41 MiB of 36 MB,
  **5.59 MiB free**, and `SITE_WARN_FRACTION = 0.90` now warns before the next PR
  discovers the wall the way this ticket did.
- **"T-0713's PR unblocked or explicitly re-parked"** — unblocked; it merged as #840.
- **"validate.py --all green on a tree that has just published"** — `./tools/check.sh`
  green on this branch.

The ticket's third option, "stop publishing something", is what actually bought the room:
#836 found the mirror shipping the changelog twice. Its first option, raising the number,
was taken on top of that and on purpose. Its forbidden option, shrinking a note to fit,
was not taken.

---

## DONE, NOT WITHDRAWN — #914's ruling taken over this session's, 2026-09-06

This ticket was withdrawn a few hours ago as one of five duplicate reports of one
ceiling. #914 closed it `done --pr 823` instead, and #914 is right, so its reading is the
one that stands.

**The difference is not bookkeeping.** `withdrawn` says the ask was never real. But the ask
WAS answered: **#823 (T-0593) re-budgeted the ceiling 32 -> 36** and wrote the reasoning
above `SITE_BUDGET_MB` in `tools/validate.py`, which is exactly the "decide the ceiling, and
put the reasoning where the decision binds" this ticket asked for. `done --pr 823` records
that and keeps the link to the commit that did it; `withdrawn` throws both away.

**And the withdrawal was argued from a wrong number.** Its reason cited "30.412 MB of 32,
1.588 MB of headroom", read out of `tools/site_budget.py`, which still hardcoded 32 while
the gate had been at 36 since #823. The correction is already on that reason and
site_budget.py now reads the gate — but a ruling reached through a stale figure is worth
re-examining rather than defending, and re-examining it changes the answer.

T-0725, T-0731 and T-0774 stay withdrawn: they report the same ceiling and none of them
asks for a decision that #823 made.
