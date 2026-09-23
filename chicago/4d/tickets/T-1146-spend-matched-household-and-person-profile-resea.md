---
id: T-1146
title: Spend matched household and person-profile research into structured relationships, names, sex, dates and life events, with every withheld fact legible
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
claimed_by: run 9/17/2026, 5:12:27 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T10:16:00.765Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35208861486
---

Spend matched household and person-profile research into structured relationships, names, sex, dates and life events, with every withheld fact legible.

**Measured on `dev`, 2026-09-15.** The town has 1,300 people in 1,276 households, but 1,201 people
have no recorded sex and only 20 households contain more than one named person. The 1835 census
counts 3,265 people in 398 dwellings; that gap proves the cards are a named-evidence layer, not
permission to manufacture spouses and children. At the same time, resident cards retain matched
research in prose and nested `resident_research`, old-settler and merge blocks that the renderer
census classifies among 83 unread resident field paths.

This ticket spends facts already attached to a canonical person or household. It does not resolve
the 68 fuzzy one-letter pairs (T-1027), the unread-initial policy (T-0392), or create unnamed people
from aggregate census counts. Those stay explicit dispositions in T-1143's ledger.

**Acceptance:**

1. Derive a candidate-fact table from every matched resident research block and crosswalk. Cover
   printed names/aliases, sex, household relationship, spouse/parent/child/boarder membership,
   birth and death bounds, arrival/origin, life events and other person-profile facts. Every row
   names the person/household id, source id, claim/record id, date, proposed value and confidence.
2. Adjudicate every candidate as `asserted`, `duplicate`, `contradicted`, `insufficient_identity`,
   `later_only`, `outside_chicago` or `unresolved:<ticket>`. No candidate disappears into prose.
3. Write asserted attested/inferred values into structured person or household assertions with
   per-value provenance. Preserve multiple names and dated life events; do not overwrite one date
   with a later source or promote a later appearance into 1835 household membership.
4. Household membership requires an explicitly named relationship or co-residence. Aggregate age/
   sex buckets may constrain reconstruction later but mint no spouse, child, boarder or servant.
5. Make the evidence panel render the asserted facts and the reason for every withheld candidate in
   readable text. Review all 83 unread resident paths: wire visitor-relevant findings, retain
   machine-only rulings with an explicit refusal, and remove only genuine duplicate machinery.
6. Add a deterministic `--check` plus mutation tests. Re-run the resident audit and report exact
   before/after counts for populated profile fields, multi-person households and unresolved facts;
   no grade or presence value moves unless the assertion that moved it is named.

**Owner review, 2026-09-17 — added acceptance and one clarification:**

7. Acceptance ¶4 ("aggregate age/sex buckets … mint no spouse, child, boarder or servant") binds
   the ATTESTED and INFERRED spend and is unchanged. The owner's 2026-09-17 direction to
   reconstruct families, women, children, boarders and staff applies to the `reconstructed` tier
   only, under the programme ticket T-1167 and the household model T-1163, where every such
   person carries a basis and a seed. This ticket does not do that work and does not forbid it.
8. The candidate-fact table's `insufficient_identity`, `later_only` and `outside_chicago` rows
   are written with the fields T-1159 (the borderline roster) reads — `name_as_read`, `source_id`,
   `claim_or_record_id`, `describes_date`, `reason` — so the roster is a filter over this table,
   not a second reading.
9. Where a source names a family member (a baptism parent, a marriage party, an 1840 row bridged
   to a head the layer carries), the structured relationship carries the member's `sex` and the
   birth/marriage bound the source gives, because T-1170 fills families from exactly those fields.

**Stop condition:** every already-matched person/household fact is structured or has a durable
disposition, and no inferred/attested value exists only inside a note or research summary.

**Links:** T-0392 · T-0507 · T-0513 · T-0634/T-0636 · T-1027 · T-1129 · T-1143 · T-1144.
