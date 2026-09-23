---
id: T-1182
title: Audit every attested and inferred business against the research: proprietors, partners, dates, primary and secondary premises, the Dec 1835 State census classes and the August 1835 American count — and raise an inferred business for every in-window trade that has none
state: split
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-19
pr: null
claimed_by: run 9/19/2026, 11:07:27 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T16:07:49.273Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35453633099
---

The owner, 2026-09-17: *"make sure all of the businesses are complete that we have audited against
the attested and inferred businesses data."* After T-1180 the 179 present-at-scene-date firms
are records; this ticket makes them COMPLETE and finds the businesses the research implies but the
register never printed.

**Denominators the audit is held against** (both already committed, both dated OUT of the scene
and used as brackets, never as instructions to invent):

- The State census of Sept–Dec 1835 (`data/research/books/claims/moses_kirkland_history_of_chicago_v1.json`
  claim `bk_mose1_006`; crosswalk `trade_census_1835_crosswalk.json`, T-1006/T-1007): 44 stores,
  2 book stores, 4 druggists, 2 silversmiths, 2 tin-and-copper shops, 2 printing offices, 2
  breweries, 1 steam saw-mill, 1 iron foundry, 4 forwarding houses, 8 taverns, 1 lottery office,
  1 bank, 5 churches, 7 schools, 22 lawyers, 14 physicians, 1 lyceum. The town today: 59 stores,
  2 druggists (−2), 1 silversmith (−1), 1 brewery (−1), 18 lawyers (−4), 3 physicians (−11), and
  three DOCUMENTED ZEROS (bank, lottery office, lyceum — "not an invitation to invent").
- The *Chicago American* of 15 August 1835 (via Andreas; quoted in `tremont_house_1.json`):
  upward of fifty business houses, four forwarding houses, eight taverns, two printing offices,
  two book-stores, one steam saw-mill, one brewery, one furnace, twenty-five mechanics' shops.

**Acceptance:**

1. For every present business record: proprietors and partners adjudicated against
   `identity.json` (47 firm merges, 12 proprietor merges), dates from first/last printing with
   `opening_announced`/`dissolved` honoured, `type` = its census class, `goods`, and every
   location the research names — the premises AND the secondary places (a warehouse on the
   river, a yard, an office at a hotel, an auction stand) — as `locations[]` with the limit class.
   A reconciliation table: field × (filled attested / filled inferred / empty with reason).
2. **Persons' other significant locations** (the owner's "any other locations they were
   significantly involved in"): for every person, the civic offices held and where they sat
   (the council house, post office, land office, court — `civic_public_buildings_1835.md`), church
   membership/office, agency holdings (`1835_agencies.json`), land purchased
   (`1835_land_sales_by_tract.json`), schools taught — written as `associated_with[]` on the
   person with kind, place/structure id, dates, tier and source. Counts before/after printed.
3. **A business for every in-window trade.** Every person whose `roles[]` reaches 1835-07-01
   with a trade that implies premises (the `works_trades` + `public_trades` of the signage rule,
   plus lawyer/physician offices) and who holds no business role gets one: `inferred` where a
   source says they practised in Chicago (the shop is the person's own — "J. Mason, blacksmith" →
   `biz_mason_blacksmith`, location street-only or unplaceable per the evidence), never
   `attested`. Trades that carry no premises (labourer, teamster, clerk, boatman) get
   `no_fixed_premises` on the role instead. `scene_window_trade_audit.json` (T-0872) must read
   zero.
4. The physicians' gap (3 vs 14) and lawyers' gap (18 vs 22) are worked FROM THE RESEARCH first:
   every physician/attorney the layer names in window gets an office record here; what remains
   short is written to the order book for T-1186, not invented here.
5. **Black-owned and Native/Métis-run businesses identified.** Every business whose proprietor
   the sources place in either community (the Indian traders' houses, the interpreters, the
   barber, any firm a register or biography so describes) carries `proprietor_community` at the
   tier the evidence supports, so the Businesses view can list them on one filter; the attested
   set is the floor T-1177 reconstructs above.
6. The Sept–Dec 1835 crosswalk is re-run and its deltas re-printed; documented zeros stay zero.
7. Report `docs/RESEARCH/business-audit-2026-09.md`; `--check` re-derives; gates in `check.sh`.

**Stop condition:** no attested or inferred business fact in the research is absent from a
business record, and no in-window tradesman is without a workplace or a stated reason.

**Links:** T-1180 · T-1145 · T-1147 · T-1006 · T-1007 · T-0872 · T-1041 (agencies) ·
`docs/RESEARCH/civic_public_buildings_1835.md`.

---

**FINDING from T-1325, 2026-09-19 — the anchored houses name their landmark in
prose only, so nothing can crosswalk them, and the register prints twelve people
twice.**

T-1325 put the business layer on the two cards a visitor is already standing at: a
person's card lists every firm the register puts them in, and a building card's Use
row lists every firm the register puts in that roof. Both are folded off
`data/businesses/index.json`. Two limits came out of doing it, and both belong to
this audit rather than to the renderer.

1. **`anchored` carries no structure.** All 26 anchored locations in the layer —
   record and index alike — have `structure_id: null`; the landmark is stated only
   inside `limit_reason`'s sentence (*"The register places this house against
   `tremont_house_1`…"*, *"…against `business_eagle_tavern`…"*). So the Tremont
   House's card cannot say which houses the register stands against it, and
   `businesses.js::locationHtml`'s `kind === 'anchored' && title` branch is dead
   code today — it renders a landmark title that no record supplies. The crosswalk
   deliberately refuses to parse the sentence for an id. Resolving the anchor onto
   the location (a structure id where the anchor IS a committed structure, a
   business id where it is another firm) would make 26 more houses reachable from
   the roof they stand beside, and would give that branch something to render.

2. **Twelve person-firm pairs are named twice on one record**, because the register
   prints the same person under two styles — `biz_collins_caton` carries "J. D.
   Caton" and "J. Dean Caton" as separate entries with the same `person_id`, the
   same role and the same dates, and so do `biz_g_spring` (three times),
   `biz_j_s_c_hogan`, `biz_jones_king_co` (both partners), `biz_p_pruyne_co` and
   seven others. T-1325's crosswalk folds them, so a person's card lists four firms
   for Caton rather than five. The firm's OWN card does not fold them: "Who kept
   it" still prints both styles as two partners, which is the register's typography
   read as the town's partnership.
