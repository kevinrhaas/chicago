---
id: T-0892
title: The synthesizer drift ratchet turns red the moment anybody publishes: its T-0838 baseline names the data/ paths and not their site/ mirrors
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: superseded: fixed by T-0933 (#1024) and T-0938 (#1023) — the mirror is untracked, publish.sh is its one writer, DRIFT_ROOTS no longer includes site/, and --drift-self-test holds it; --drift is green on dev
needs_bake: false
closed_at: 2026-09-10T04:20:07.653Z
claimed_run: null
---

The synthesizer drift ratchet turns red the moment anybody publishes: its T-0838 baseline names the data/ paths and not their site/ mirrors.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0828 (#989), 2026-09-06, and it cost that run a gate.**

`tools/synthesize_resident_research.py --drift` walks the tree, so it reads the published
mirror as well as the source. Four resident cards stand off what the writer would produce
today and are declared on the T-0838 baseline — but the baseline names them by their
`data/…` path only:

```
data/residents/households/hh_adams_william_h.json
data/residents/households/hh_miller_john.json
data/residents/households/hh_murphy_john.json
data/residents/index.json
```

On `dev` the ratchet is green, because `site/chicago/4d/data/residents/` is STALE — it
still holds the pre-drift copies. The moment any PR runs `./tools/publish.sh`, which
every publishing PR must, the mirror is refreshed with the drifted content and four new
`FAIL`s appear under `site/chicago/4d/…`, on files whose `data/` originals are declared:

```
FAIL site/chicago/4d/data/residents/households/hh_adams_william_h.json has drifted
     from the writer and is not on the T-0838 baseline
```

So the gate is red for a change that touched no resident card, and the only way past it is
to check out the four mirror files again — i.e. to publish everything EXCEPT them, and
leave the mirror stale for the next run to trip over. #989 did exactly that, deliberately
and scoped to those four paths, because reverting them restores `dev`'s own state; but
that is a workaround and it does not survive contact with the next publishing run.

**Two things to decide, and they are different questions:**

1. **Whether the ratchet should read the mirror at all.** The mirror is generated: a
   drift there is never news, it is the same drift already declared one path up. Skipping
   `site/**` would fix this outright, and it is the answer that matches how every other
   generated-mirror rule in this project works.
2. **Whether the baseline should carry mirror paths.** Cheaper, but it doubles every
   future declaration and quietly makes the mirror a thing an author has to remember.

**Acceptance:** `./tools/publish.sh` followed by `bash tools/check.sh` is green on a tree
whose only change is a publish — asserted by a self-test that fires when it is broken, not
by a run happening to try it; the four cards above stay declared exactly as they are; and
the mirror is left FRESH afterwards rather than deliberately stale.
