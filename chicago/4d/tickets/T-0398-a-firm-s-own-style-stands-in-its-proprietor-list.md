---
id: T-0398
title: A firm's own style stands in its proprietor list, because a claim read the signature where a person was wanted
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-11
pr: 1165
claimed_by: run 9/11/2026, 9:06:25 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T02:41:31.573Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34666575823
---

A firm's own style stands in its proprietor list, because a claim read the signature where a person was wanted.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

`business_russell_clift` carries three proprietors and one of them is the house itself:
`Aaron Russell`, `Benj. H. Clift` and **`Russell & Clift`**. The last comes from the
Democrat of 1835-08-19 (c012), where the only name the type gives is the signature —
"for sale only by Russell & Cl[if]t (Agents for the State of I[ll]inois) at the Chicago
Book Store" — so the reading pass recorded the firm as the proprietor, which is exactly
what the paper printed and is not a misreading.

The compiler already KNOWS it is a firm style. `firm_styled()` (T-0337) recognises it and
the proprietor policy steps over it, which is right — there is no second man to adjudicate.
What nothing does is say so on the record: a visitor-facing proprietor list that reads
"Aaron Russell, Benj. H. Clift, Russell & Clift" states that the partnership is its own
third partner.

This is the last of the three name-kind confusions the papers hand the gazetteer. T-0359
gave `places` a home for a BUILDING named by its signboard; T-0337 gave one man read twice
a rule. A partnership STYLE read where a person was wanted has neither.

Found while shipping T-0340 (PR #547), which merged four keys of this bookshop into one and
carried the string across rather than dropping it — nothing should edit a claim to make it
go away, and the union is documented as never narrowing a record.

**Acceptance:** the proprietor list distinguishes a partner from the firm's own style,
without editing any claim's reading, and the distinction is derived rather than declared
where `firm_styled()` can already tell (a declaration is only needed where it cannot).
