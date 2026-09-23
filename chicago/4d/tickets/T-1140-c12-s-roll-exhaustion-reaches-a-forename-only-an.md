---
id: T-1140
title: C12's roll exhaustion reaches a forename only, and five one-letter SURNAME pairs are the shape it would decide
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-15
closed: 2026-09-17
pr: null
claimed_by: null
blocked_on: folded into T-1291
needs_bake: false
closed_at: 2026-09-17T19:18:45.407Z
claimed_run: null
---

C12's roll exhaustion reaches a forename only, and five one-letter SURNAME pairs are the shape it would decide.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-1134**, which refused six one-letter surname pairs under the new rule D6 — C9's
shape with no page — and found five of the six standing in exactly one other shape, which C12
already knows how to decide and cannot reach.

C12 is *TWO SPELLINGS ON ONE CLOSED ROLL, RESOLVED BY EXHAUSTION OVER THE ROLL*: a closed roll
inside the window does NOT print the survivor's spelling while an independent non-name fact puts
him on it, and every other bearer of the surname on that roll is accounted for by a card of its
own that the survivor is not — so the folded spelling is the only entry left for him. It never
weighs how alike two strings look, which is why it may be applied at three letters where C9 and
C10 are held to one. **Its first condition says `the surname agrees letter for letter`, so it
reaches a FORENAME only.** T-1132 hit this from the other side and said so in the Pruyne ruling:
"C12 as written reaches a FORENAME only, so firing it here is itself a rule to write."

## The five, and the roll each waits on

| pair | the closed roll | what the roll does not print | the non-name fact that puts him on it |
|---|---|---|---|
| Bread / Breed (A O T) | poll list of 1835 | `Breed` | A. O. T. Breed sues and is sued in the Cook Circuit Court, May Term 1834 |
| Kingston / Kingstone (Paul) | tax list of 1833 | `Kingston` | the ISA land register enters KINGSTON PAUL; two other Kingstons on it |
| Trall / Thrall (E. L.) | poll list of 1835 | `Thrall` | a documented clothier's stand on South Water Street, Democrat 4 June 1834 |
| Wesencraft / Wessencraft (Charles) | tax list of 1833 | `Wesencraft` | Fergus 1843's carpenter and wagonmaker, cor S. Clinton and W. Monroe |
| Forsyth / Forsythe (William) | poll of 1834 | `Forsyth` | the tax roll of 1833 and the Democrat of 29 October 1834 |
| *(and)* Pruyne / Pryne (Peter) | tax list of 1833 | `Pruyne` | school-section lots bought inside the platted town, October 1833 |

The last row is **T-1135**, which owns that one pair and its reading. This ticket owns the RULE:
whether C12's exhaustion may be moved from the forename to the surname, and under what extra
condition if so. They are not the same job and should not be done in the same run — T-1135 reads
one roll, this one decides whether the shape generalises and, if it does, says which of the five
above it then reaches. Do T-1135 first; it is the demonstration this reasons from.

## What has to be argued, not assumed

1. **A surname is not a forename.** C12's forename version is safe partly because the surname
   agreeing letter for letter already restricts the field to a handful of people. Moved to the
   surname, the restriction is the forename doing the same work — weaker where the forename is
   John or William, stronger where it is `A. O. T.` The rule must say which, and
   `tools/measure_surname_fold.py` is the measurement to reason from, not around.
2. **The exhaustion must be WORKED AND PRINTED**, over the whole roll, per pair. That is a
   reading each time and it is why this is a rule ticket and not a batch merge.
3. **D5 is watching.** The same rolls that could exhaust could instead turn up both spellings as
   separate entries, which refuses the pair outright. The 1833 tax list already did that to
   David/Davis.

## Acceptance

(state it before working — one demonstration, never weakened to pass)

