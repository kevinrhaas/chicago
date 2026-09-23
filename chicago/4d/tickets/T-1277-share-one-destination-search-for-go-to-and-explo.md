---
id: T-1277
title: Share one destination search for Go to and Explore Myself
state: open
epic: RENDERING
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-17
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

One destination model for both entry points. The owner: *"I'll Explore Myself — Starting At… should let the user search or browse for a historical location, structure, business, resident-associated place, street/intersection … after selection, take them there and return them to normal free-exploration mode. This is like the way Go to works now so integrate all that together so it's not duplicate."* Extract what `goto.js` builds today into a shared `destinations.js`, and let the welcome's start picker and the in-world Go to tab both use it.

**Depends on:** nothing. **Runs in parallel with:** T-1246, T-1292, T-1248. T-1278 and T-1279 depend on this.

**What exists today:**
- `renderers/web/js/goto.js` `createGoTo({ … })` builds `targets[]` inline (~L66–140): anchors (`scene.anchors`, 17 in 1835), intersections (`index.intersections`, 5), structures from the registry (label from `display-name.js`, `placeKind` group, `presenceGrade`, `position_confidence`, `search` terms), and people **only when `lives_at`/`works_at` resolves to a registry id** — unlocated people are deliberately not rows. It owns diacritic-folded search, kind pills, keyboard selection, distance readouts and the "include reconstructed" preference.
- `main.js` `goToTarget(target)` (~L2069) resolves a person to a structure and calls `travel.go(target)`; `framing(id)` (~L1942) frames a whole building on arrival; `api.goTo(anchorId)` jumps to an anchor.
- Businesses: there is no authored business layer on dev yet (T-1180/T-1181 in band 4). Structure names and `function` words already carry the business ("Jones's Grocery and Provision Store", `grocery_and_provision_store`), so business search works through structures today.

**Build:**
1. `renderers/web/js/destinations.js` (~250 lines): `createDestinations({ scene, index, registry, people, positionOf, businesses = null })` → `{ targets, kinds, search(q, { kind, includeReconstructed }), byId(kind, id), resolve(target) → { kind, id, label, e, n, standOff, limit } }`. Move the row-building and the search normaliser out of `goto.js`; `goto.js` keeps only the DOM (search box, pills, list, keyboard) and calls `destinations.search`.
2. Add a `business` kind that reads `businesses` when the authored layer is present (its ids, proprietors, dated primary location) and otherwise **derives** rows from structures whose `function` is a trade (`store`, `tavern_inn`, `*_shop`, `warehouse*`, `*_manufactory`, `tannery`, `brickyard`, `auction_room`, `printing_office`, `drug_store`, `boarding_house`, `hotel_stable`) — one row per structure, labelled by the structure's name, with `derived_from: 'structure'`. Do not author a competing register.
3. Unlocated people and businesses (no resolvable coordinates) are searchable and open their card with the stated location limit; they never acquire coordinates. Ambiguous labels show the kind and the street/building in `sub`.
4. `resolve()` returns a safe stand-off for structures (the existing framing/stand-off contract from `route.js standOff` and `framing()`), the point itself for intersections and anchors, and `null` for anything without a position.
5. `main.js`: `goToTarget` and the future spawn selection both call `destinations.resolve`; free-exploration spawn = `walker` placed at the stand-off, camera framed as arrival framing does today, no travel ride, no jaunt state.
6. Harness: `api.destinations = { count, kinds, search }` for the smoke; existing Go to assertions (junction count is data — T-0245; person rows) keep passing.

**Acceptance:**
1. Go to behaves exactly as before: same rows, order, pills, distances, keyboard, reconstructed toggle (smoke parts covering Go to pass unchanged, plus one new assertion that `api.destinations.count === visible rows`).
2. `search('peck')` returns Peck's store as structure AND as business (derived); `search('kinzie & canal')` returns the intersection; `search('sauganash')` returns the structure and the anchor; a person with no address returns a row that opens the card and states "no known address".
3. `resolve()` for a structure, an intersection, an anchor and a person all yield a stand-off on ground, inside no footprint (assert with `router.blockedAt` and `terrain.surfaceHeight`), demonstrated in `tools/test_destinations.mjs` (node, fixture scene).
4. Spawn-at-destination places the visitor there with arrival framing and no ride, before any jaunt code exists; repeated selection and dismissal without selection move nothing.
5. Both entry points share one inventory: no second target list anywhere (grep proves `targets.push` lives only in destinations.js).

**Harness and gates:** `./tools/check.sh`; `node tools/smoke_budget.mjs --for-diff` (goto.js/main.js → the Go to parts); run them `--published` at both viewports.

**Out of scope:** the welcome UI that hosts the picker (T-1278); travel-mode estimates (T-1280).

Contract: [architecture §E](../docs/ARRIVAL-JAUNTS-ARCHITECTURE.md#e-destination-model) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`; changelog entry (business rows in Go to are the visible change).
