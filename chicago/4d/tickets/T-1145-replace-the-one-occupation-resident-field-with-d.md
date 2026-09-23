---
id: T-1145
title: Replace the one-occupation resident field with dated plural roles and migrate every matched trade, profession and civic office without back-projecting later evidence
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
claimed_by: run 9/17/2026, 3:38:16 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T08:38:27.728Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35200021551
---

Replace the one-occupation resident field with dated plural roles and migrate every matched trade, profession and civic office without back-projecting later evidence.

**Measured by the owner-requested audit, 2026-09-15.** The newspaper gazetteer already stores
`persons[].occupations[]`, directory crosswalks carry later occupations, and the 1839 register
carries civic offices, but a resident exposes one `occupation` block and the people index reads
only that value. The audit found 1,126 structured role-evidence rows tied to current residents and
176 people with more than one distinct raw/later role string. Synonyms may describe one trade;
dates and source claim ids, not string count, decide the assertions.

Daniel Elston is the acceptance fixture. Research calls him candle manufacturer, soap
manufacturer, chandler, pork curer, provision dealer and soap boiler in 1833-34; brickmaker in
1839; school inspector in the 1839 civic register; and press-brick maker in 1843-44. The model
shows only `soap_and_candle_maker`, incorrectly graded as an attested 1835 occupation.

**Acceptance:**

1. Add a plural, dated resident role schema. Each assertion carries a controlled role, the source's
   wording, role kind (`trade`, `profession`, `office`, `employment` or `business_interest`),
   `from`/`to` or point date with precision, confidence, source id and claim/entry id. Unknown
   dates stay unknown; they are never widened to the scene date.
2. Make `roles[]` canonical. Keep a singular scene occupation only as a generated compatibility
   view of roles that actually cover 1 July 1835; two simultaneous roles remain two roles.
3. Migrate every matched role from the newspaper gazetteer, resident later-occupation blocks,
   1839 directory and civic-register crosswalks, and the 1843/1844 identity-master appearances.
   Produce a reconciliation table: offered, asserted, synonym-folded, refused and unresolved.
4. Resolve T-0991 by retaining its six 1833 trades as dated pre-scene roles and removing their
   claim to be attested 1835 occupations unless an in-window source is found. Jones and Kimball's
   later, different trades remain separate assertions rather than overwriting the earlier ones.
5. The people view shows all roles as a dated timeline, clearly marks which (if any) reach the scene
   date, and searches both controlled and printed wording. Daniel Elston visibly shows his
   manufacturing, provisions/packing, brickmaking and school-inspector evidence with dates.
6. Extend the schema, validators, compiler, resident audit and layer-read census. Gates fail when a
   role loses its source/claim id, an undated/later role enters the 1835 compatibility field, or a
   structured role is retained in research but absent from the migration disposition table.

**Owner review, 2026-09-17 — added acceptance:**

7. The Elston fixture is extended to LOCATION: each dated role names where it was exercised when
   a source says (the manufactory on the North Side for the candles and soap; the school
   inspectorship's seat), so T-1147 can carry a role's place as a `works_at[]`/`associated_with[]`
   entry with the role's dates. A role with no stated place says `place: not_stated`.
8. The role kinds `office` and `employment` carry an `employer_or_body` field (the town board, the
   county, a named firm) so the business band (T-1180 onward) can attach clerks and officers to
   the establishment they served without re-reading prose.
9. The migration table is published as `docs/RESEARCH/roles-migration-2026-09.md` with one row per
   person carrying 2+ roles (the audit found 176), because the population profile (T-1160) counts
   multi-role persons from it.

**Stop condition:** every matched trade/profession/office row has a dated role, a documented fold,
or a refusal; the singular field is no longer capable of erasing a second role.

**Links:** T-0632 · T-0693 · T-0837 · T-0872 · T-0991 · T-1025 · T-1143 · T-1144.
