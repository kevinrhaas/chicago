---
id: T-0357
title: 129 documented businesses will stand on a survival liberty and LIBERTIES.md carries none of them
state: done
epic: PAPERS
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-08-29
pr: 548
claimed_by: run 8/29/2026, 12:24:26 PM CT
blocked_on: null
needs_bake: false
---

The register counts 129 businesses standing at the scene date whose last newspaper
evidence is earlier than 1835 — `survival_liberty_required: true`. Owner ruling 3,
2026-08-28: such a business is BUILT, with a survival liberty stated on the record
(existence documented, survival to 1835-07-01 assumed).

`docs/LIBERTIES.md` carries none of them today, and it must before any of those
businesses stands in the town, because the liberties gate reads the compiled
`data/liberties.json` and the Evidence panel reads it back to the visitor. Writing 129
near-identical liberty entries by hand is the wrong shape: this wants ONE liberty
stating the survival assumption, with the register as its enumerated scope, or a
generated family the compiler expands — a decision to make before T-0263 builds the
first one.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The survival assumption is stated in docs/LIBERTIES.md in a form that covers every
  business the register flags, and names how the scope is enumerated.
- `tools/compile_liberties.py` and the liberties gate accept it; check.sh green.
- The count in the liberty and the count in the register agree, and a gate says so —
  a liberty whose scope has drifted from the register is worse than none.
