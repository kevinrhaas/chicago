---
id: T-1117
title: Arthur Bronson's card says present on the scene date, inferred from the 1833 tax list, and the town's own historians print him a visitor from New York who went home
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-13
closed: 2026-09-14
pr: 1346
claimed_by: run 9/14/2026, 7:41:58 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-15T01:32:35.417Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34913852701
---

Arthur Bronson's card says present on the scene date, inferred from the 1833 tax list, and the town's own historians print him a visitor from New York who went home.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-1017, which decided the rule and left this one alone because it is a question
about a CARD and not about the register.

`data/residents/households/hh_bronson_arthur.json` carries `present_on_scene_date: present`,
`confidence: inferred`, on the note that the record BRACKETS 1 July 1835: the tax list of
1833 names him at Chicago at or before it and the old-settler death notices name him at or
after. `arrival` is an `inferred` bound of 1833-12-31 on the same tax list.

T-1017 read the town's own historians on the same man:

    "Two visitors to the settlement from New York — Charles Butler and Arthur Bronson —
    were so moved with commiseration at the sight of this apology for a library, that on
    their return home they sent on a donation of two hundred volumes."
    — Moses & Kirkland, History of Chicago vol. 2, printed page 367, claim bk_mose2_021

**THE QUESTION.** A town taxes a NON-RESIDENT on the ground he holds in it, and Arthur
Bronson held a great deal — thirteen blocks of the school section plus eight more rows under
the register's `BROSON`, and in 1834 the half of Kinzie's Addition and the whole of
Wolcott's, bought of General David Hunter for $20,000 with his associates. So the tax list
may be evidence of PROPERTY rather than of presence, and if it is, the bracket that puts
this man in the town on the scene date does not hold.

**THE TRAP.** Do not swing it the other way either. The passage does not date the visit, it
does not say he was absent on 1 July 1835, and a New York capitalist with this much Chicago
ground may well have been in the town that summer. The honest outcomes are a re-graded
inference with the ambiguity stated, or a `documented` absence if a source actually places
him elsewhere — not a silent retraction and not a silent keep.

**Acceptance:**

- The 1833 tax list is read for what it is: does it distinguish resident from non-resident
  payers, on its own face or in what the project already knows of it? Whatever the answer,
  it is stated with its source, because the same question governs every card whose whole
  evidence is that list.
- `hh_bronson_arthur`'s `present_on_scene_date` and `arrival` are re-stated under the
  answer — upheld, re-graded or retracted — and the note says which and why.
- If the tax list turns out NOT to be a residence check, every other card resting on it
  alone is COUNTED, and the count decides whether this is one ticket or a cohort.
- Nothing in `data/research/land_sales/resident_rulings.json` moves: T-1017 already settled
  that the BRONSON ARTHUR ruling is an IDENTITY ruling and stands either way.
- `bash tools/check.sh` green; any derived layer re-run in the same commit.
