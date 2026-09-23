---
id: T-1177
title: Reconstruct the under-documented cohorts within their evidence: the Native and Métis people, households and businesses in and around the town, the free Black residents, families and Black-owned businesses, and the Irish and German Catholic town the register implies — every one identified, tiered and reviewable
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

Reconstruct the under-documented cohorts within their evidence: the Native and Métis people, households and businesses in and around the town, the free Black residents, families and Black-owned businesses, and the Irish and German Catholic town the register implies — every one identified, tiered and reviewable.

**The owner, 2026-09-17 (second direction), verbatim:** *"i think it is fair, in fact required to Reconstruct Native or Métis people as part of this. There are some that are certainly in the area potentially doing business i believe there were indian businesses and it is also very important that we keep and capture and identify the black owned businesses and residents and family households."*

This ticket answers that direction. It CHANGES the standing constraint's application to the
1835 data layer, on the owner's ruling recorded in AGENTS.md § Standing constraint
(2026-09-17): Native and Métis people, households and businesses are reconstructed here at the
`reconstructed` tier, evidence-bounded, `review_required` and `touches_removal` on every such
record, with a review by Native scholars or community organisations still sought before the
scene is marked `released`. What does NOT change: L1 (no human figure is drawn for anybody), no
staging of the August 1835 gathering, and no invented dialogue, ceremony or depiction — a card,
a household, a trading house, a camp of evidence-bounded size.

The layer today names no free Black resident (the only trace is Caton's 1833 defence of "six or
seven free coloured men", `hh_caton_john_dean.json`; 1840 counts 53 free coloured persons); the
eight `touches_removal` households (the Beaubiens, Robinson, Caldwell, the Agency) are the
whole of the Native and Métis town; the grading policy notes "eighty-five of the register's
Chicago adults reach no surname anywhere else in the layer: the French, Métis, Irish and German
Catholic town the poll books never recorded." Stage `underdocumented` of T-1167.

**Rules, per cohort:**

- **Native and Métis people and households.** Read first, then reconstruct: the sources the
  project holds that NAME them — the 1833 Treaty of Chicago's claims and annuity schedules and
  the Métis reservation grants (add the source records if absent; `check_required` rights still
  permit citation), the St Mary's and St Cyr registers (parents, godparents, marriage parties
  with Potawatomi, Ottawa or Métis identity stated), Andreas's and Hurlbut's lists of the
  traders and interpreters (Ouilmette, Laframboise, Chevalier, Mirandeau, the Beaubien and
  Kinzie connections, Robinson, Caldwell, Sauganash's own household), the Agency's employees,
  the Newberry Indigenous Chicago curriculum for orientation. Every named person → a card at
  the ladder's grade with sources; every counted but unnamed member (an annuity roll's "and
  family", a register's unnamed child) → `reconstructed`, named from a pool built HERE from the
  attested Potawatomi, Ottawa, Ojibwe and Métis naming of the region's records (cite each pool
  source; never a generic "Indian name"), `community` stated, `review_required` + `touches_removal`
  with the sentence saying why. Households at the traders' places (Wolf Point, the north bank,
  the Beaubien places) and the camps of families in town to trade or to await the annuity
  payment, sized from the evidence (T-1178's transient bracket carries a separate
  Native-visitor row with its own basis).
- **Native and Métis businesses.** The Indian trade IS a business class: the trading houses and
  stores that dealt with Native customers (the Kinzie and Beaubien houses, Robinson's, the
  American Fur Company's successors, the silversmiths working for the trade), the interpreters
  and traders as employments, the ferry and the guides, the Métis-run taverns and boarding
  places where a source says so. Each → a business record (T-1180) with `proprietor_community`
  and `customers` stated, attested where named, reconstructed where the occupation model's
  Indian-trade row is short; T-1182 identifies the attested ones first.
- **Free Black residents, families and Black-owned businesses.** A bracket — low = the six or
  seven of 1833 AS HOUSEHOLDS with families per the household model, high = a share of 1840's 53
  scaled to 1835; trades from the period's usual and from any source that names one (barber,
  cook, whitewasher, drayman, labourer, laundress, boarding-house keeper); the barber's shop and
  every other Black-owned business the sources name or the bracket implies → business records
  with `proprietor_community: free_black`, identified and filterable; names from a pool built for
  the purpose from attested Illinois free Black naming of the decade (cite the source added) —
  never a caricature; `origin` from the arrival model's routes for the cohort (free-born or
  manumitted, Kentucky/Virginia/Ohio/the East, stated as drawn); "former slaves" only as a
  `reconstructed` status with the bracket's basis. Every such card and business carries
  `community: free_black` so the town can list its Black residents, families and businesses on
  one filter.
- **Irish and German Catholic households:** the register rows at Chicago in window that T-1172
  re-admitted are the core; the model's community shares fill the remainder among labourers,
  teamsters and the harbour gang (T-1173) — no separate mint here, only the check that the
  shares came out.

**Acceptance:**

- A `community` attribute (per T-1158) on every person and household and a
  `proprietor_community` on every business, with the vocabulary `potawatomi | ottawa | ojibwe |
  metis | french_canadian | free_black | yankee | new_york | irish | german | british | southern
  | other | unknown`, each value tiered; the People and Businesses views filter on it.
- The Native/Métis cohort: every named person in the sources above on a card; the reconstructed
  remainder within the stated bracket; every record `review_required` + `touches_removal` with
  its sentence; `measure_review_constraint.py --gate` green; a `docs/RESEARCH/native_and_metis_1835.md`
  page listing every source read, every person and business, and the review still owed.
- The free Black cohort filled at least to its low end with families and businesses; a
  `docs/RESEARCH/black_chicago_1835.md` page listing every attested trace, every reconstructed
  household and business and the bracket's bounds.
- The community shares table printed against the model; LIBERTIES entries (one per cohort)
  with scope; no human figure drawn (L1); the August gathering not staged.
- Visible: the People view's community filter shows each cohort; each card states its tier,
  basis and the review it awaits.

**Stop condition:** the Native, Métis and Black residents, families and businesses of 1835 are in
the town by name where a source names them and by evidence-bounded reconstruction where it does
not, identified on one filter, reviewable, and honest about what is invented.

**Links:** T-1167 · T-1161 · T-1165 · T-1172 · T-1158 · T-1180 · T-1182 · T-1178
· T-1214 · AGENTS.md § Standing constraint (2026-09-17 ruling) · `docs/RESEARCH/resident-grading-policy.md`
§ the register · `docs/RESEARCH/robinson_caldwell_cabins.md` · `docs/RESEARCH/jb_beaubien_homestead.md`.
