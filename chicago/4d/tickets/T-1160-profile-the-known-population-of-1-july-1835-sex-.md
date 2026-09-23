---
id: T-1160
title: Profile the known population of 1 July 1835: sex, age, origin, arrival date and reason, roles, household composition, lodging, division and presence for every attested and inferred person, per attribute and per tier, as a generated report and an in-app card
state: split
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-17
pr: null
claimed_by: run 9/17/2026, 8:44:31 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T02:32:41.854Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35296201573
---

The owner, 2026-09-17: *"do a population analysis of the known population … analyze
demographics, gender, age, occupations, arrival date and reason, all the attributes for all
members of all households and descriptions of the population composition and types so we can make
a best profile of the town."*

`docs/RESEARCH/residents-households-summary-2026-09.md` (T-0517, `tools/summarize_residents.py`)
is the last profile and it predates the spend: 1,404 persons, 7% with a sex, 9.6% with a trade,
1.4% in a multi-person household, 5.4% with any address. This ticket re-profiles the layer AFTER
T-1157 on the per-attribute tiers of T-1158, adds the axes the owner named that the old
profile lacks, and publishes it where a visitor can open it.

**Axes (each a section, each printed by one named command, each broken down by tier):**

1. **Headcount** — persons, households, by grade and rung; by division; presence.
2. **Sex** — recorded / implied-by-forename (inferred, rule stated) / unknown.
3. **Age** — birth year where a biography or register gives one; age BAND otherwise
   (adult-by-office, adult-by-poll, child-by-baptism); unknown. Age pyramid of the known.
4. **Origin and arrival** — origin (state/country) and arrival year/precision from the earliest
   dated appearance (a `not_later_than` bound) and from biographies; **reason for coming** where a
   source states it (army posting, Indian agency, trade/forwarding, canal and harbour works, land
   purchase, mission/church, following kin) — with a controlled vocabulary added to the index.
5. **Roles** — persons by number of roles, by role kind, roles reaching the scene date; the top
   trades; who holds a civic office; who keeps a tavern/hotel/boarding house.
6. **Household composition** — household size, relationships present (wife/child/servant/
   boarder/clerk/apprentice/partner), heads without any family, heads with attested family,
   female-headed households, group entries.
7. **Lodging** — persons whose `lives_at` is a hotel, tavern or boarding house; the fort; vessels.
8. **Where they meet the buildings** — housed / roofed-workplace / unplaced, by division.
9. **Composition and types** — a prose section, every sentence quoting a table above: what
   KINDS of people the sources show (merchant-forwarders, army, agency, mechanics, professionals,
   labourers, women and children as the sources show them, free Black residents, French-Canadian, Native and Métis households as
   the sources show them — quoted here; T-1177 reconstructs the rest) with a `community`
   axis counted like the others and what kinds the sources are silent about.

**Acceptance:**

- `tools/profile_population_1835.py` (extending, not forking, `summarize_residents.py`) prints
  every section; `--build` writes `docs/RESEARCH/1835_population_profile.md` and
  `data/reconstruction/1835_population_profile.json`; `--check` re-derives both and is in
  `check.sh`.
- The reason-for-coming vocabulary and the age-band vocabulary are added to
  `data/residents/index.json` `vocabulary` with the rule that assigns each band.
- Every table carries a **tier column** (attested / inferred / reconstructed / unknown) so the
  reconstruction bands can see exactly what they are filling.
- **Visible:** a "The town's people, 1 July 1835" card in the Evidence hub (the People view's
  summary tab or the evidence panel index) renders the headline tables from the JSON — headcount,
  sex, age bands, origins, top roles, household sizes, lodging — with the tier legend.
- The profile's closing section, "What the town should have held", lists the buckets the
  MODEL tickets below must supply, without numbers (numbers are T-1161's).

**Stop condition:** a reader can answer, for any attribute and any tier, how many known people
carry it — and the same command answers it again after every reconstruction ticket.

**Links:** T-1157 · T-1158 · T-0517 · `tools/summarize_residents.py` ·
`docs/RESEARCH/census-and-civic-evidence-2026-09.md`.
