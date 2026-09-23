---
id: T-1147
title: Spend every defensible home, workplace and business-location finding, preserve the 123 location limits, and close research with zero unclassified attested or inferred fact
state: split
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-15
closed: 2026-09-17
pr: null
claimed_by: run 9/17/2026, 7:46:54 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T12:47:05.057Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35222324991
---

Spend every defensible home, workplace and business-location finding, preserve the 123 location limits, and close research with zero unclassified attested or inferred fact.

**Measured on `dev`, 2026-09-15.** Only 20 of 1,276 households name a `lives_at` structure and 50
name `works_at`. The newspaper register treats 179 businesses as present: 56 records reach an
individual structure (33 unique targets), 61 support only a street and 62 support no usable
location. Those 123 are not automatically missing buildings. A street or an unresolved anchor is
the evidence limit until another source narrows it.

This is the last closeout ticket. It follows the closed ledger (T-1143), resident convergence
(T-1144), dated roles (T-1145) and household/profile spend (T-1146). Existing source questions stay
owned by T-0251 (church/office ground conflict), T-0305 (four contradictory American addresses),
T-0386 (Montgomery/Carver stand) and T-1087 (Wabansia/Kinzie Addition vocabulary); do not guess
around them.

**Acceptance:**

1. Build a reconciliation row for every home, workplace and business-location claim: source and
   claim id, describes date, resident/household/business ids, printed place, resolved street/anchor/
   structure, confidence, and disposition. Include later directory addresses without treating them
   as 1835 placements unless the existing back-projection rule explicitly fires.
2. Write every defensible relationship: residents may hold multiple employments/business interests;
   businesses link to every adjudicated proprietor/partner; `works_at`/`lives_at` become plural,
   dated relationships rather than one overwriting another.
3. Keep exact placement proportional to evidence. Individual structures need a resolvable anchor;
   street-only businesses may occupy a labelled street face but claim no lot or roof; unplaceable
   businesses remain visible in the register with the printed reason. No completion metric rewards
   invented coordinates.
4. Resolve or explicitly retain the outcomes of T-0251, T-0305, T-0386 and T-1087. The 61/62
   location-limit counts may fall only when a new source/reading names the stronger anchor; every
   move is shown in the before/after report.
5. The people and business views expose the links, dates, confidence and location limits. A user can
   see a person's concurrent roles and workplaces and can find a street-only/unplaceable business
   without seeing a fabricated building.
6. Run the T-1143 ledger over the final resident, household, business and structure layers. Close
   only at zero unclassified research units, zero attested/inferred fact stranded solely in research
   prose, zero dead target, and zero resident-generator drift. Publish the final audit and exact
   counts; wire all checks and mutation self-tests into `check.sh`.

**Owner review, 2026-09-17 — added acceptance:**

7. "Other significant locations" are in scope, not only home and workplace: a civic office's seat,
   a church, an agency held, land purchased, a school taught, a tavern kept — written as
   `associated_with[]` on the person `{ kind, place_or_structure_id, from, to, tier, source_id }`
   (the shape T-1182 also writes for the business audit; one schema, defined here).
8. The address book the seating ticket T-1198 builds starts from this ticket's reconciliation rows:
   every row keeps `resolved_street`, `resolved_face`, `resolved_anchor` and the clause that limited
   it, so a later rung can be added without re-adjudicating the evidence.
9. The closing report states the three location-limit counts (structure / street-only /
   unplaceable) for businesses AND the four seating classes for households (structure / lot /
   face / division / none), which T-1157 reads as the sign-off's location axis.

**Stop condition:** the research phase has a reproducible closed ledger. Every usable fact is on a
structured model target; every unusable or unresolved unit says why; reconstruction can begin
without silently inheriting an unspent attested/inferred claim.

**Links:** T-0251 · T-0305 · T-0386 · T-1087 · T-1143 · T-1144 · T-1145 · T-1146.
