---
id: T-0438
title: The letter-list cohort is 2.54 MiB of the published tree, and it is now the largest single item in it
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-30
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

The letter-list cohort is 2.54 MiB of the published tree, and it is now the largest single item in it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

The owner's ruling of 2026-08-30 (T-0379) put 727 letter-list households into the
published tree. After a trim that took each record from 5,503 bytes to 3,661 — moving
the reasoning identical on all 727 out of 727 files and into docs/LIBERTIES.md L214,
the pass's docstring and the Evidence panel's group heading — the cohort publishes at
**2.54 MiB, the largest single item in a 28.48 MiB tree**, ahead of T-0364's 2.07 MiB
of duplicated changelog. `SITE_BUDGET_MB` was raised 28 -> 32 in that PR to ship it,
which buys headroom and does not answer this.

**What makes it worth a ticket rather than a shrug:** the cohort grows with the corpus.
Every newspaper reading ticket in the queue adds letter-list names, the mint holds all
the refusals admit, and each one costs another ~3.6 KB of published tree. The growth is
not bounded by anything the project has decided.

**The shape of an answer, and T-0379 already priced it.** The owner was offered
"Option C — hold them in a lighter form than a household" and chose Option A instead,
so the RECORDS stay as they are; what this ticket asks is whether the PUBLISHED form
has to be one file per person. The panel fetches a household record only when its row
is opened, and every row in this cohort is opened out of one closed group. A single
bundled roster for the group — derived at publish time, the individual records staying
canonical in the repo — would cost one fetch instead of one per row and would drop the
per-record JSON scaffolding that is most of what remains. Not proposed as decided: the
mirror contract says publish copies rather than derives, and changing that is the
question.

**Acceptance:** (state it before working — never weakened to pass)

- The published cost of the cohort measured before and after, and the panel's behaviour
  at both viewports unchanged for a visitor.
- Whatever is done, `data/residents/households/*.json` stays the canonical per-person
  record and `--gate` still passes over it.

Related: **T-0379** (the ruling), **T-0364** (the duplicated changelog), `validate.py`
§ SITE_BUDGET_MB (both re-budgets and their reasoning).
