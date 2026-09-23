---
id: T-0415
title: John Wright's two buildings to let are named (east) and (west) and stand the other way round
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-05
pr: 898
claimed_by: run 9/5/2026, 11:04:53 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T16:36:39.136Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33976336967
---

John Wright's two buildings to let are named (east) and (west) and stand the other way round.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Measured on `dev` while working T-0386, 2026-08-29.** The two records' committed
positions run the opposite way to their names:

| record | name | `utm_e` |
|---|---|---|
| `wright_building_to_let_a` | John Wright's Building to Let **(east)** | 447496.614 |
| `wright_building_to_let_b` | John Wright's Building to Let **(west)** | 447619.812 |

Higher easting is further east, so the one called *(east)* stands about 123 m **west**
of the one called *(west)*, in a different block: `_a` is on the Randolph frontage of
Lake/LaSalle/Randolph/Wells, `_b` on the Randolph frontage of Lake/Clark/Randolph/
LaSalle.

**This is not necessarily an error, and that is the problem.** Both positions declare
themselves invented in their own notes — *"The advertisement gives no address at all,
so this is a band assignment and not a reading"* — and both were moved off the public
square on 2026-08-15 under ROADMAP T-A16. So *(east)* and *(west)* may never have meant
anything about the ground at all; they may be nothing but the disambiguators this
project needed to hold two records apart. Either way a reader, or a later anchor pass,
will read them as a bearing, because that is what those words say.

**What it needs.** Decide which the two words are, and make the record say so: either
the names carry a claim about relative position and the two are the wrong way round, or
they carry none and should be disambiguators that cannot be misread as one — `(a)` and
`(b)`, or the block each stands on. Note that `tools/compile_register.py`'s `words()`
drops `east` and `west` as address stop words, so under any name-based matching these
two records are ONE name regardless (T-0386), and renaming them does not change that.

Found while working **T-0386**.
