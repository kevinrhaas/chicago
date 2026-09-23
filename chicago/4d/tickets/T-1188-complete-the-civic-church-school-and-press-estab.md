---
id: T-1188
title: Complete the civic, church, school and press establishments as businesses with staff: the post office, the land office opened in 1835, the county offices, the schools, the churches and the two printing offices — attested where the sources name the officer, reconstructed for the rest
state: split
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-19
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T23:30:56.880Z
claimed_run: null
---

Fifth group of T-1184's tool, and mostly an ATTESTED one: the civic establishments are
the best-documented workplaces in town and the least staffed in the layer. `docs/RESEARCH/
civic_public_buildings_1835.md` fixes the three civic roofs of 1 July 1835; the register carries
7 schools, 3 printing offices, the churches are "not compared". The owner's Elston fixture —
school inspector — is a civic role that needs a place to sit.

**Establishments and what each needs:**

- **Post office** (postmaster attested; where it sat on 1 July — `civic_public_buildings_1835.md`;
  a clerk reconstructed).
- **The U.S. Land Office at Chicago** (opened for the June 1835 sales — register and receiver
  attested in the vocabulary; clerks reconstructed; its building per the civic dossier).
- **County and town offices**: clerk, sheriff, justices, the town board, the school inspectors —
  roles on persons (T-1145 already carries the 1839 register's offices; the 1835 ones are in the
  civic lists) seated at the council house/court room the civic dossier names.
- **Schools** (7): teacher attested where named (the 1833 north-side school, the Presbyterian
  school…), the rest reconstructed; each a `school` business with its teacher and a pupil COUNT
  (not pupils) from the model.
- **Churches** (5 in the census; First Presbyterian, St Mary's, the Baptist and Methodist
  congregations, the Episcopal): minister/priest attested; sexton reconstructed; congregation as
  `associated_with[]` on attested members only.
- **The press**: the *Chicago Democrat* and the *Chicago American* (first issue 8 June 1835 —
  inside the window) with editors, printers, apprentices per the staffing model; the third
  printing office of the register adjudicated.
- **Fort Dearborn**: not a business — its establishment is T-1176's.

**Acceptance:**

- Every establishment above is a business record with `type` civic/church/school/printing_office,
  its officers at `attested`/`inferred` with sources, its reconstructed staff at `reconstructed`,
  and a `locations[]` entry that resolves to the civic roof the dossier names or states the limit.
- Nothing is invented that the dossier refuses (no fourth civic roof); documented zeros stand.
- Visible: the civic building cards name their establishment and officers; the Businesses view
  filters civic.

**Stop condition:** every civic role in the layer has a seat and every civic seat has its people.

**Links:** T-1184 · T-1145 · `docs/RESEARCH/civic_public_buildings_1835.md` ·
`docs/RESEARCH/council_house.md` · `docs/RESEARCH/chicago_american_office.md` ·
`docs/RESEARCH/chicago_democrat_office.md` · `docs/RESEARCH/north_side_school_1833.md`.
