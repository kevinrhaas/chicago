---
id: T-0333
title: Every stove pipe in the town owes eighteen inches above its roof, and the ordinance of 5 August 1835 says so
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-29
pr: 587
claimed_by: run 8/29/2026, 11:20:50 PM CT
blocked_on: null
needs_bake: false
---

The Trustees of the Town of Chicago passed an ordinance on **5 August 1835**, printed in
three of the four August Democrats and read under [[T-0335]]
(`chicago_democrat_1835_08_19.json` c005, section 18). It regulates roof geometry directly:

> every stove pipe or chimney passing through the roof of any building shall extend and be
> carried at least eighteen inches above the roof, and no stove pipe shall be passed through
> the side or end of any building

— under a penalty of five dollars for each and every offence, and a fire warden walked into
every house, store and shop in his district once a month from September to May to check
(section 21). Sections 15-17 are the same fear from the other side: shavings swept out weekly,
no burning in a street or on a lot without leave from a trustee.

This is the FIRST documented dimensional constraint this project has on anything above a
roof line, and it points the other way from the sentence the fort's flagstaff ticket quotes —
Andreas describing a town with "not a single steeple nor a chimney four feet above any roof."
Four feet is a maximum a memoirist noticed; eighteen inches is a minimum the town enforced.
Both can be true and together they bracket the height of every stack in the scene.

## What has to be found out before anything moves

- **What does the model draw today?** Count the structures carrying a chimney or stove pipe,
  and measure each one's projection above its own roof plane. The answer may already be
  compliant, in which case this ticket closes as a GATE and a provenance note rather than as
  geometry.
- **Is a stove pipe the same object as a chimney here?** The ordinance names both and treats
  them alike; the archetypes may not distinguish them at all.
- The ordinance binds only "within the limits of the Corporation", which section 22 of the
  same sitting describes street by street ([[T-0334]]). A farmhouse outside that line is not
  covered by it and must not be silently conformed to it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- A measured census, stated in the PR, of every drawn chimney and stove pipe's projection
  above its roof, inside the corporation limits and outside them.
- Where a stack is short, it is raised to at least eighteen inches and the confidence and note
  on the affected record cite the ordinance claim, not this ticket.
- A gate that fails if a stack inside the limits drops back under eighteen inches, so the
  constraint cannot rot the way the timber-placement gates did (T-0243).
- `docs/LIBERTIES.md` is untouched: this is a documented constraint, not an invention.
