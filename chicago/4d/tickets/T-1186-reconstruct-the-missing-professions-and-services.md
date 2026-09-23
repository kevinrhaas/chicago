---
id: T-1186
title: Reconstruct the missing professions and services: physicians and law offices to the State census's 14 and 22, land agents, surveyors, a dentist's stand, barbers, teachers, laundresses, seamstresses and domestics, as businesses or as no-premises employments
state: open
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-09-16
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

Third group of T-1184's tool. The State census of late 1835 counted 22 lawyers and 14
physicians; the register reaches 18 and 3. T-1182 first raises an office for every attorney and
physician the research names in window; this ticket reconstructs the remainder — and it is
allowed to, because the census is a COUNT OF MEN, dated months after the scene, so the gap is
filled at the low end of its bracket (the tool states the bracket: 1835-07-01 sits between the
August count and the December one) and labelled.

**This group's quota:** physicians and attorneys to the bracket's low end; land agents and
surveyors as the June 1835 land sales imply (the press is full of them — count the attested
first); a barber (the second the old programme argued); schoolteachers to the 7 schools
(attested first); the female service trades — laundresses, seamstresses/dressmakers/milliners,
domestics — as businesses only where a woman kept a shop (milliner, dressmaker) and otherwise as
`no_fixed_premises` employments on reconstructed women written by T-1174.

**Naming:** professionals by name and title as the papers print them (`Dr. E. S. Kimberly`,
`Wm. Stuart, Attorney at Law`); offices `locations[]` of kind `office`, `street_only` (Lake,
Dearborn, Clark, "at the Tremont House"), with lodging at a hotel where the lodging model seats
single professionals.

**Acceptance:**

- Records build to quota; `--check`; LIBERTIES scope; the census crosswalk re-run shows the
  lawyer and physician deltas closed to the stated low end and NOT above it; documented zeros
  (bank, lottery office, lyceum) untouched — the tool refuses a record of those classes.
- Visible: the Businesses view; the People view shows the reconstructed professionals with
  their office and lodging.

**Stop condition:** the professions/services buckets read filled within the bracket.

**Links:** T-1184 · T-1182 · T-1006 · T-1007 · T-1164 · T-1174.
