---
id: T-0805
title: The residents schema has no field for a kinship BETWEEN two households, so every cross-household relationship the sources print lands as prose
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: null
claimed_by: null
blocked_on: Should this reconstruction model kinship across households at all, and if so in what shape — a kin[] block on the person (PR #839 is a worked, validated demonstration), a separate edge file, or nothing and the prose stands by design? Nothing gets invented before the answer.
needs_bake: false
closed_at: 2026-09-05T16:23:17.424Z
claimed_run: null
---

The residents schema has no field for a kinship BETWEEN two households, so every
cross-household relationship the sources print lands as prose.

**How it was found.** T-0597 wrote Hurlbut's 1881 bracketed note — "[The late James Kinzie,
formerly of Chicago, and half brother of the late John H. Kinzie.]" (`bk_afc_015`) — onto
`kinzie_james` and `kinzie_john_h`. That ticket's second acceptance bullet said: if the schema
has no field for a relationship between households, say so, add nothing invented, and file the
schema question. It has none, so this is the filing.

**What exists and what does not.** `data/residents/index.json`'s `vocabulary.relationships`
(head, wife, son, boarder, clerk…) describes a person's place *within* one household record.
`RESIDENT_HOUSEHOLD_KEYS` in `tools/validate.py` has no key for an edge between records. The
other cross-household kinships already in the dataset are the same free prose —
`hh_clybourne_archibald`'s "Julia K. Clark, half-brother of A. Clybourne", `hh_miller_john`.
So the Kinzie half-brotherhood sits on both cards as a cited `book_evidence` reading with the
relationship in the note, and no question can follow it.

**Why it matters beyond one pair.** T-0734 measured it: 14 of 1,404 people carry any stated
relationship to anybody at all, and the corpus already prints more — the St Cyr marriage
entries, the death notices Fergus prints with a surviving widow, the 1840 census households
the bridge has matched. Every one of those lands as prose until this is answered, and T-0734
cannot be spent well without it.

**This is a ruling, not a build.** A run does not invent a residents-schema field on its own
initiative. PR #839 (open, from a sibling run on this same ticket's earlier pass) is a worked
`kin[]` demonstration — validated, tested, rendered, migrated onto the two Kinzie records —
held for exactly this ruling rather than merged. It is the thing to rule ON, not the ruling.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- The owner's answer to: should this layer model kinship across households at all, and if so
  in what shape — a `kin[]` block on the person, a separate edge file, or nothing.
- Nothing invented before that answer. If the answer is `kin[]`, #839 is the candidate and is
  reviewed on its merits; if it is "nothing", say so here and the prose stands by design.
- Grading and reciprocity are part of the question, not afterthoughts: a kinship carries a
  source and a rung like any other reading, and it points both ways.

**Links:** T-0597 (found it) · T-0734 (the 14-of-1,404 measurement this blocks) · PR #839 (the
worked proposal) · `data/residents/index.json` `vocabulary.relationships` ·
`RESIDENT_HOUSEHOLD_KEYS` in `tools/validate.py`.
