# Initial library — 25 short jaunts

Content design for [the arrival/jaunts architecture](ARRIVAL-JAUNTS-ARCHITECTURE.md).
These are authoring briefs, not shipped scripts or newly attested events. The owner
wants a varied collection of approximately five-minute experiences. The recommended
modes and stop counts below are **design targets**, not measured durations; every
content ticket measures its final route and the displayed estimate comes from travel.
Deep reading is always optional. Ordinary outings may finish in 3–4 minutes naturally.

## Verified on 2026-09-17 (second pass) — every proposed stop, with what its record can carry

All 42 ids below resolve in `data/structures/` and `data/sidecars/1835/index.json`; none is
`review_required`. **No stop's position is attested** — each is `inferred` (placed from a
corner, address or later directory) or `reconstructed` (invented within bounds). A stop's
text therefore never claims a placed front door; an exterior stand-off framed by the engine
is the whole of what a stop asserts about location. Authors read the sidecar and the dossier
(where one exists) before writing; the authoring rules and field reference live in
`docs/JAUNTS-AUTHORING.md` (T-1253).

| Stop id | Position | Dossier | Note |
|---|---|---|---|
| `sauganash_hotel`, `green_tree_tavern`, `wolf_point_tavern`, `western_hotel`, `western_hotel_stable`, `mansion_house`, `exchange_coffee_house` | inferred | yes (stable: no) | tavern_inn / hotel_stable |
| `peck_store`, `hogan_store`, `carpenter_south_water_store`, `harmon_loomis_store`, `john_holbrook_store`, `h_jones_store` | inferred (Jones: reconstructed) | yes (Holbrook: no) | store / drug_store / grocery_and_provision_store |
| `thomas_church_store`, `brown_boarding_house`, `newberry_dole_warehouse`, `elston_soap_candle_manufactory`, `lasalle_slough_crossing`, `lake_house_construction`, `walker_meeting_house`, `chappel_infant_school`, `watkins_school_house` | **reconstructed** | mixed | say so on the stop; the two school records read "use on the scene date unattested" |
| `chicago_democrat_office`, `chicago_american_office`, `bates_auction_room`, `dole_warehouse_south`, `goss_cobb_saddlery`, `pierce_blacksmith_shop`, `miller_tannery`, `brickyard_north_side`, `north_side_school_1833`, `first_presbyterian_church`, `st_marys_church` | inferred | mixed | printing_office / auction_room / warehouse_and_slaughter_yard / trades / school / church |
| `fort_dearborn_palisade`, `fort_dearborn_guard_house`, `fort_dearborn_sutlers_store`, `fort_dearborn_store_house`, `fort_dearborn_shop` | inferred | yes (shop: no) | Harrison 1830 plan, continuity to 1835 inferred; "shop" = workshop |
| `south_branch_raft_bridge`, `dearborn_street_drawbridge`, `north_pier`, `chicago_lighthouse_1832` | inferred | yes | river_crossing / harbour_works / harbour light |
| `anchor:lake_shore_south` | camera anchor | — | a viewpoint in `data/scenes/1835.json`, not an establishment |

## Shared historical authoring rule

Proposed destinations below resolve in `data/sidecars/1835/index.json` or the scene's
anchors as inspected on 17 September 2026. Their precise function, operation date,
location and form can have different confidence grades. Read each structure's
`data/structures/<id>.json`, compiled card and cited source record before authoring.
Follow its dossier and newspaper `data/research/newspapers/register_1835.json` evidence
to the actual locator; source membership is not permission to assert any claim.

Keep facts, supported inference and invented connective material separate. Invented
errands, transactions, small talk, prices and keepsakes are reconstructed narrative,
with their bounds recorded in LIBERTIES. Real residents' details belong to their
existing cards; do not invent quotations or encounters and pass them off as events.
Keep the July 1 scene eligibility while welcoming the visitor to summer 1835.
No improvised Indigenous presence/dialogue or new human figures. No playable interior
is implied by a building stop; a safe exterior framing is sufficient.

The plan intentionally avoids the court-house that the current compiled scene excludes
for its October 1835 start. Do not use the 1836 Lake House as an open hotel, Hogan's
former post-office site as a current mail counter, or an unlocated business as a
precise storefront. Supported street/anchor substitutes are allowed with a note.

## Menu-level library

| # | Title / premise | Category | Stops | Recommended mode | Main keepsake family |
|---|---|---|---:|---|---|
| 1 | **Outfit for the West** — Leave town with a practical kit, sound equipment and enough money for the road. | Migration | 5 | Wagon | Provisions |
| 2 | **Taverns of Chicago** — Visit three taverns, collect local talk and decide where to finish the evening. | Taverns | 4 | Horse | Neighbors |
| 3 | **New in Chicago** — Find your bearings, a bed and a practical next step on your first day in town. | Orientation | 5 | Walk | Wayfinding |
| 4 | **Shopping South Water Street** — Fill a small household list along the working riverfront without buying everything you see. | Commerce | 4 | Walk | Provisions |
| 5 | **Across Wolf Point** — Make a short crossing between the settlement’s divisions and learn why the forks mattered. | River and routes | 4 | Walk | Wayfinding |
| 6 | **Fort Dearborn Errand** — Carry a small fictional supply request through the fort’s everyday service places. | Fort Dearborn | 5 | Walk | Livelihood |
| 7 | **News Before Breakfast** — Compare two papers and carry one useful item of news back to the lodging house. | Newspapers | 4 | Walk | News & Knowledge |
| 8 | **A Letter Home** — Find out how to send a letter and decide what to tell the people you left behind. | Mail | 4 | Walk | News & Knowledge |
| 9 | **A Bed for the Night** — Compare a few lodging options and choose a place that fits your modest purse. | Lodging | 4 | Walk | Neighbors |
| 10 | **Work on the Waterfront** — Follow a small job lead from the papers to the warehouses. | Employment | 4 | Horse | Livelihood |
| 11 | **Look Before You Buy a Lot** — Compare a land-sale notice with the ground before making an expensive commitment. | Land | 4 | Walk | News & Knowledge |
| 12 | **Freight for the Store** — Move an imagined small consignment from warehouse to shop with its tally intact. | River commerce | 4 | Wagon | Livelihood |
| 13 | **Stock the Household** — Gather the ordinary supplies needed to settle into a room in Chicago. | Household | 4 | Walk | Provisions |
| 14 | **A Decent Coat** — Find something practical to wear for work and a social call. | Shopping | 4 | Walk | Provisions |
| 15 | **Mend the Harness** — Resolve a small equipment problem before a longer journey. | Trades and repairs | 4 | Wagon | Livelihood |
| 16 | **Soap and Candles** — Take a short provisioning outing to understand two useful household trades. | Household and trades | 4 | Horse | Provisions |
| 17 | **Materials for a Roof** — Inspect how a growing town obtains the materials for another building. | Building trades | 4 | Horse | Livelihood |
| 18 | **Boots, Leather and the Road** — Learn how hides and leatherwork support everyday travel. | Trades | 4 | Horse | Livelihood |
| 19 | **A Schoolday Errand** — Plan a simple schooling inquiry while learning where early classes met. | Education | 4 | Horse | News & Knowledge |
| 20 | **A Sunday Circuit** — Take a quiet outing past a few community gathering places. | Social life | 4 | Walk | Neighbors |
| 21 | **Calling on Neighbors** — Make a few imagined introductions without pretending to know who answered the door. | Social life | 4 | Walk | Neighbors |
| 22 | **Gossip or Printed Notice?** — Follow a rumor back to its evidence before passing it along. | News and social life | 4 | Walk | News & Knowledge |
| 23 | **Along the Working Harbor** — Take a short outing from a warehouse toward the river mouth. | River transportation | 4 | Horse | Wayfinding |
| 24 | **From Prairie to Town** — Arrive from the open ground south of town and choose a useful first stop. | Migration and routes | 4 | Horse | Wayfinding |
| 25 | **An Evening Stroll** — Take a calm circuit of the familiar streets and choose a place to end your outing. | Leisure | 4 | Walk | Neighbors |

## 01. Outfit for the West

**ID:** `outfit-for-the-west` · **Owner ticket:** [T-1260](../tickets/T-1260-publish-outfit-for-the-west-as-a-five-minute-jau.md)

**Setup/goal:** Leave town with a practical kit, sound equipment and enough money for the road.

**Proposed stops, in story order:**

- [`green_tree_tavern`](../data/structures/green_tree_tavern.json) — Green Tree Tavern.
- [`goss_cobb_saddlery`](../data/structures/goss_cobb_saddlery.json) — S. B. Cobb's Saddle, Harness and Trunk Manufactory.
- [`peck_store`](../data/structures/peck_store.json) — P. F. W. Peck's Store.
- [`h_jones_store`](../data/structures/h_jones_store.json) — Jones's Grocery and Provision Store.
- [`pierce_blacksmith_shop`](../data/structures/pierce_blacksmith_shop.json) — Asahel Pierce's Blacksmith Shop.

**Primary interactions:** Set a short supply list; choose pack or harness; buy essential tools; select provisions; decide whether to repair before departure. A light-versus-prepared ending follows money/readiness, not a survival battle.

**Keepsake/outcome:** Ready for the Road (Provisions); fictional narrative memento.

**Evidence and route cautions:** Prices, quantities and the errand are reconstructed; cite which trades actually sold the chosen goods.

## 02. Taverns of Chicago

**ID:** `taverns-of-chicago` · **Owner ticket:** [T-1261](../tickets/T-1261-publish-taverns-of-chicago-as-a-five-minute-jaun.md)

**Setup/goal:** Visit three taverns, collect local talk and decide where to finish the evening.

**Proposed stops, in story order:**

- [`sauganash_hotel`](../data/structures/sauganash_hotel.json) — Sauganash Hotel.
- [`wolf_point_tavern`](../data/structures/wolf_point_tavern.json) — Wolf Point Tavern.
- [`green_tree_tavern`](../data/structures/green_tree_tavern.json) — Green Tree Tavern.
- [`western_hotel`](../data/structures/western_hotel.json) — Western Hotel.

**Primary interactions:** Choose a modest purse; hear a short piece of clearly fictional gossip bounded by the papers; compare welcome and lodging; pick a final house. Money and optional sobriety alter a restrained ending; abstaining is equally playable.

**Keepsake/outcome:** A Sensible Evening (Neighbors); fictional narrative memento.

**Evidence and route cautions:** Do not put reconstructed dialogue in a named historical person’s mouth as quotation; site presence and business tenure retain their own grades.

## 03. New in Chicago

**ID:** `new-in-chicago` · **Owner ticket:** [T-1262](../tickets/T-1262-publish-new-in-chicago-as-a-five-minute-jaunt.md)

**Setup/goal:** Find your bearings, a bed and a practical next step on your first day in town.

**Proposed stops, in story order:**

- [`sauganash_hotel`](../data/structures/sauganash_hotel.json) — Sauganash Hotel.
- [`hogan_store`](../data/structures/hogan_store.json) — Hogan's Store.
- [`peck_store`](../data/structures/peck_store.json) — P. F. W. Peck's Store.
- [`chicago_democrat_office`](../data/structures/chicago_democrat_office.json) — The Chicago Democrat Office.
- [`brown_boarding_house`](../data/structures/brown_boarding_house.json) — Rufus Brown's Boarding House.

**Primary interactions:** Arrive at the Sauganash; learn how the old mail corner oriented the settlement; note a supply shop; inspect a useful notice; choose a boarding arrangement. A low-pressure outing with one optional preference and a route-note keepsake.

**Keepsake/outcome:** Finding Your Feet (Wayfinding); fictional narrative memento.

**Evidence and route cautions:** Hogan’s held the post office earlier; the record says it moved about July 1834. This is not the current 1835 mail counter. Engine pilot becomes this final authored jaunt, not a duplicate.

## 04. Shopping South Water Street

**ID:** `shopping-south-water` · **Owner ticket:** [T-1263](../tickets/T-1263-publish-shopping-south-water-street-as-a-five-mi.md)

**Setup/goal:** Fill a small household list along the working riverfront without buying everything you see.

**Proposed stops, in story order:**

- [`peck_store`](../data/structures/peck_store.json) — P. F. W. Peck's Store.
- [`carpenter_south_water_store`](../data/structures/carpenter_south_water_store.json) — Philo Carpenter's South Water Street Store.
- [`harmon_loomis_store`](../data/structures/harmon_loomis_store.json) — Harmon & Loomis's Store.
- [`thomas_church_store`](../data/structures/thomas_church_store.json) — Thomas Church's Store.

**Primary interactions:** Choose essentials at Peck’s; consider household supplies at Carpenter’s; compare the next two merchants; finish with a usable basket and a receipt. A modest purse supports useful substitutions, not min-max scoring.

**Keepsake/outcome:** The Household List (Provisions); fictional narrative memento.

**Evidence and route cautions:** Verify each item against trade/advertisement evidence; fictional prices remain labeled. The optional broader business layer must not supply later-only goods.

## 05. Across Wolf Point

**ID:** `across-wolf-point` · **Owner ticket:** [T-1264](../tickets/T-1264-publish-across-wolf-point-as-a-five-minute-jaunt.md)

**Setup/goal:** Make a short crossing between the settlement’s divisions and learn why the forks mattered.

**Proposed stops, in story order:**

- [`green_tree_tavern`](../data/structures/green_tree_tavern.json) — Green Tree Tavern.
- [`wolf_point_tavern`](../data/structures/wolf_point_tavern.json) — Wolf Point Tavern.
- [`south_branch_raft_bridge`](../data/structures/south_branch_raft_bridge.json) — South Branch Bridge.
- [`sauganash_hotel`](../data/structures/sauganash_hotel.json) — Sauganash Hotel.

**Primary interactions:** Orient from the west side; read the fork from the tavern; choose the supported crossing; arrive on the south side with a simple route note. Focus on place and everyday movement, with no forced money or drama.

**Keepsake/outcome:** Knows the Crossing (Wayfinding); fictional narrative memento.

**Evidence and route cautions:** Route over the current bridge graph, never straight across water. Describe disputed bridge/tavern details at their recorded tier.

## 06. Fort Dearborn Errand

**ID:** `fort-dearborn-errand` · **Owner ticket:** [T-1265](../tickets/T-1265-publish-fort-dearborn-errand-as-a-five-minute-ja.md)

**Setup/goal:** Carry a small fictional supply request through the fort’s everyday service places.

**Proposed stops, in story order:**

- [`fort_dearborn_palisade`](../data/structures/fort_dearborn_palisade.json) — Fort Dearborn — the stockade.
- [`fort_dearborn_guard_house`](../data/structures/fort_dearborn_guard_house.json) — Fort Dearborn — guard house.
- [`fort_dearborn_sutlers_store`](../data/structures/fort_dearborn_sutlers_store.json) — Fort Dearborn — sutler's store.
- [`fort_dearborn_store_house`](../data/structures/fort_dearborn_store_house.json) — Fort Dearborn — store house.
- [`fort_dearborn_shop`](../data/structures/fort_dearborn_shop.json) — Fort Dearborn — the shop.

**Primary interactions:** Approach the supported entrance stand-off; check the errand at the guard-house vicinity; choose a supply at the sutler’s; account for the package at the storehouse; finish at the service shop. A concise cargo/readiness ending makes the fort a working neighbor.

**Keepsake/outcome:** Accounted for at the Fort (Livelihood); fictional narrative memento.

**Evidence and route cautions:** Harrison plan and record dates support locations with stated limits; shop is not automatically a documented blacksmith. Do not invent access to closed interiors or military procedures, figures or Indigenous dialogue; use exterior stops when the route requires.

## 07. News Before Breakfast

**ID:** `news-before-breakfast` · **Owner ticket:** [T-1266](../tickets/T-1266-publish-news-mail-lodging-and-work-jaunts.md)

**Setup/goal:** Compare two papers and carry one useful item of news back to the lodging house.

**Proposed stops, in story order:**

- [`sauganash_hotel`](../data/structures/sauganash_hotel.json) — Sauganash Hotel.
- [`chicago_democrat_office`](../data/structures/chicago_democrat_office.json) — The Chicago Democrat Office.
- [`chicago_american_office`](../data/structures/chicago_american_office.json) — The Chicago American Office.
- [`exchange_coffee_house`](../data/structures/exchange_coffee_house.json) — Exchange Coffee House.

**Primary interactions:** Choose a question, read one short item from each paper, distinguish reporting from an advertisement, and keep a clipping.

**Keepsake/outcome:** A Useful Clipping (News & Knowledge); fictional narrative memento.

**Evidence and route cautions:** Only issue-dated, page-and-column-located material eligible on the scene date; do not treat later news as current.

## 08. A Letter Home

**ID:** `letter-home` · **Owner ticket:** [T-1266](../tickets/T-1266-publish-news-mail-lodging-and-work-jaunts.md)

**Setup/goal:** Find out how to send a letter and decide what to tell the people you left behind.

**Proposed stops, in story order:**

- [`brown_boarding_house`](../data/structures/brown_boarding_house.json) — Rufus Brown's Boarding House.
- [`hogan_store`](../data/structures/hogan_store.json) — Hogan's Store.
- [`chicago_democrat_office`](../data/structures/chicago_democrat_office.json) — The Chicago Democrat Office.
- [`peck_store`](../data/structures/peck_store.json) — P. F. W. Peck's Store.

**Primary interactions:** Choose the fictional letter’s purpose; visit the former mail corner; consult an eligible postal notice; obtain writing supplies only where supported, then finish with a draft and a plan for posting.

**Keepsake/outcome:** A Letter Ready to Send (News & Knowledge); fictional narrative memento.

**Evidence and route cautions:** No invented current post-office address. If dated evidence resolves a current counter during authoring, substitute that typed location; otherwise end with the posting inquiry honestly unresolved, not a false mailed receipt.

## 09. A Bed for the Night

**ID:** `bed-for-the-night` · **Owner ticket:** [T-1266](../tickets/T-1266-publish-news-mail-lodging-and-work-jaunts.md)

**Setup/goal:** Compare a few lodging options and choose a place that fits your modest purse.

**Proposed stops, in story order:**

- [`sauganash_hotel`](../data/structures/sauganash_hotel.json) — Sauganash Hotel.
- [`brown_boarding_house`](../data/structures/brown_boarding_house.json) — Rufus Brown's Boarding House.
- [`western_hotel`](../data/structures/western_hotel.json) — Western Hotel.
- [`mansion_house`](../data/structures/mansion_house.json) — Mansion House.

**Primary interactions:** State a preference for cost or convenience; compare short supported descriptions; choose a lodging outcome.

**Keepsake/outcome:** A Place to Lay Your Head (Neighbors); fictional narrative memento.

**Evidence and route cautions:** Room prices/availability are narrative bounds, not documented bookings; a four-stop path can finish early without padding.

## 10. Work on the Waterfront

**ID:** `work-on-waterfront` · **Owner ticket:** [T-1266](../tickets/T-1266-publish-news-mail-lodging-and-work-jaunts.md)

**Setup/goal:** Follow a small job lead from the papers to the warehouses.

**Proposed stops, in story order:**

- [`chicago_democrat_office`](../data/structures/chicago_democrat_office.json) — The Chicago Democrat Office.
- [`newberry_dole_warehouse`](../data/structures/newberry_dole_warehouse.json) — Newberry & Dole's Forwarding and Commission Warehouse.
- [`dole_warehouse_south`](../data/structures/dole_warehouse_south.json) — George W. Dole's Warehouse.
- [`exchange_coffee_house`](../data/structures/exchange_coffee_house.json) — Exchange Coffee House.

**Primary interactions:** Choose a skill, consider a bounded fictional work inquiry at two documented firms, and leave with a work chit or a sensible next lead.

**Keepsake/outcome:** A Day’s Work in Prospect (Livelihood); fictional narrative memento.

**Evidence and route cautions:** Do not claim an actual named vacancy, wage or employer offer without a dated source.

## 11. Look Before You Buy a Lot

**ID:** `inspect-a-lot` · **Owner ticket:** [T-1267](../tickets/T-1267-publish-land-freight-household-supplies-and-clot.md)

**Setup/goal:** Compare a land-sale notice with the ground before making an expensive commitment.

**Proposed stops, in story order:**

- [`chicago_democrat_office`](../data/structures/chicago_democrat_office.json) — The Chicago Democrat Office.
- [`bates_auction_room`](../data/structures/bates_auction_room.json) — John Bates Jr.'s Auction Room.
- [`peck_store`](../data/structures/peck_store.json) — P. F. W. Peck's Store.
- [`lasalle_slough_crossing`](../data/structures/lasalle_slough_crossing.json) — The La Salle Slough Crossing, South Water Street.

**Primary interactions:** Read an eligible notice; distinguish auction context from a particular sale; orient at a known corner; inspect the wet ground and decide to inquire further or hold your money.

**Keepsake/outcome:** Read the Ground (News & Knowledge); fictional narrative memento.

**Evidence and route cautions:** Use only a matched in-window lot for a precise offer; do not invent parcel ownership, price or a functioning 1835 bank. Caution can be a successful ending.

## 12. Freight for the Store

**ID:** `freight-for-the-store` · **Owner ticket:** [T-1267](../tickets/T-1267-publish-land-freight-household-supplies-and-clot.md)

**Setup/goal:** Move an imagined small consignment from warehouse to shop with its tally intact.

**Proposed stops, in story order:**

- [`newberry_dole_warehouse`](../data/structures/newberry_dole_warehouse.json) — Newberry & Dole's Forwarding and Commission Warehouse.
- [`dole_warehouse_south`](../data/structures/dole_warehouse_south.json) — George W. Dole's Warehouse.
- [`peck_store`](../data/structures/peck_store.json) — P. F. W. Peck's Store.
- [`thomas_church_store`](../data/structures/thomas_church_store.json) — Thomas Church's Store.

**Primary interactions:** Count packages, choose a manageable load, check the store list and deliver a tally. Optional cargo and story-time decisions fit the errand.

**Keepsake/outcome:** Cargo Accounted For (Livelihood); fictional narrative memento.

**Evidence and route cautions:** Warehouse roles may be sourced; this shipment and its bill are fictional. Use safe street paths and no imaginary unloading simulation.

## 13. Stock the Household

**ID:** `household-provisions` · **Owner ticket:** [T-1267](../tickets/T-1267-publish-land-freight-household-supplies-and-clot.md)

**Setup/goal:** Gather the ordinary supplies needed to settle into a room in Chicago.

**Proposed stops, in story order:**

- [`brown_boarding_house`](../data/structures/brown_boarding_house.json) — Rufus Brown's Boarding House.
- [`h_jones_store`](../data/structures/h_jones_store.json) — Jones's Grocery and Provision Store.
- [`carpenter_south_water_store`](../data/structures/carpenter_south_water_store.json) — Philo Carpenter's South Water Street Store.
- [`peck_store`](../data/structures/peck_store.json) — P. F. W. Peck's Store.

**Primary interactions:** Pick a short list; select provisions; consider useful household goods; finish with a practical basket.

**Keepsake/outcome:** A Cupboard Begun (Provisions); fictional narrative memento.

**Evidence and route cautions:** Keep items tied to supported trades and bound reconstructed quantities/prices; no compulsory health score.

## 14. A Decent Coat

**ID:** `a-decent-coat` · **Owner ticket:** [T-1267](../tickets/T-1267-publish-land-freight-household-supplies-and-clot.md)

**Setup/goal:** Find something practical to wear for work and a social call.

**Proposed stops, in story order:**

- [`brown_boarding_house`](../data/structures/brown_boarding_house.json) — Rufus Brown's Boarding House.
- [`john_holbrook_store`](../data/structures/john_holbrook_store.json) — John Holbrook's Clothing Store.
- [`harmon_loomis_store`](../data/structures/harmon_loomis_store.json) — Harmon & Loomis's Store.
- [`sauganash_hotel`](../data/structures/sauganash_hotel.json) — Sauganash Hotel.

**Primary interactions:** Choose an occasion, inspect supported clothing stock, compare practical needs, and finish prepared for the visit.

**Keepsake/outcome:** Fit for the Occasion (Provisions); fictional narrative memento.

**Evidence and route cautions:** Do not invent a fitting service or named tailor at a shop whose record only supports retail.

## 15. Mend the Harness

**ID:** `mend-the-harness` · **Owner ticket:** [T-1268](../tickets/T-1268-publish-harness-candles-building-materials-and-l.md)

**Setup/goal:** Resolve a small equipment problem before a longer journey.

**Proposed stops, in story order:**

- [`western_hotel_stable`](../data/structures/western_hotel_stable.json) — The Western Hotel's Stable.
- [`goss_cobb_saddlery`](../data/structures/goss_cobb_saddlery.json) — S. B. Cobb's Saddle, Harness and Trunk Manufactory.
- [`pierce_blacksmith_shop`](../data/structures/pierce_blacksmith_shop.json) — Asahel Pierce's Blacksmith Shop.
- [`green_tree_tavern`](../data/structures/green_tree_tavern.json) — Green Tree Tavern.

**Primary interactions:** Notice a reconstructed wear problem; choose a harness repair; check related hardware; decide the outfit is ready or keep the trip short.

**Keepsake/outcome:** Sound Tack (Livelihood); fictional narrative memento.

**Evidence and route cautions:** The repair story is invented; distinguish leather work from iron work using the actual firm records.

## 16. Soap and Candles

**ID:** `soap-and-candles` · **Owner ticket:** [T-1268](../tickets/T-1268-publish-harness-candles-building-materials-and-l.md)

**Setup/goal:** Take a short provisioning outing to understand two useful household trades.

**Proposed stops, in story order:**

- [`h_jones_store`](../data/structures/h_jones_store.json) — Jones's Grocery and Provision Store.
- [`elston_soap_candle_manufactory`](../data/structures/elston_soap_candle_manufactory.json) — Daniel Elston & Co.'s Soap and Candle Manufactory.
- [`thomas_church_store`](../data/structures/thomas_church_store.json) — Thomas Church's Store.
- [`brown_boarding_house`](../data/structures/brown_boarding_house.json) — Rufus Brown's Boarding House.

**Primary interactions:** Make a small list, learn what the manufactory produced, choose what to carry and bring the supplies back.

**Keepsake/outcome:** Light for the Evening (Provisions); fictional narrative memento.

**Evidence and route cautions:** Do not promise a documented retail counter at the works; an exterior observation can carry the stop.

## 17. Materials for a Roof

**ID:** `materials-for-a-roof` · **Owner ticket:** [T-1268](../tickets/T-1268-publish-harness-candles-building-materials-and-l.md)

**Setup/goal:** Inspect how a growing town obtains the materials for another building.

**Proposed stops, in story order:**

- [`newberry_dole_warehouse`](../data/structures/newberry_dole_warehouse.json) — Newberry & Dole's Forwarding and Commission Warehouse.
- [`brickyard_north_side`](../data/structures/brickyard_north_side.json) — Blodgett's Brickyard.
- [`lake_house_construction`](../data/structures/lake_house_construction.json) — Lake House (under construction).
- [`peck_store`](../data/structures/peck_store.json) — P. F. W. Peck's Store.

**Primary interactions:** Consider freight, inspect the brickmaking site, see a hotel under construction, and choose a bounded material order.

**Keepsake/outcome:** A Builder’s List (Livelihood); fictional narrative memento.

**Evidence and route cautions:** Lake House is under construction, not open lodging; material costs and the customer’s order are reconstructed.

## 18. Boots, Leather and the Road

**ID:** `boots-and-leather` · **Owner ticket:** [T-1268](../tickets/T-1268-publish-harness-candles-building-materials-and-l.md)

**Setup/goal:** Learn how hides and leatherwork support everyday travel.

**Proposed stops, in story order:**

- [`miller_tannery`](../data/structures/miller_tannery.json) — John Miller's Tannery.
- [`goss_cobb_saddlery`](../data/structures/goss_cobb_saddlery.json) — S. B. Cobb's Saddle, Harness and Trunk Manufactory.
- [`john_holbrook_store`](../data/structures/john_holbrook_store.json) — John Holbrook's Clothing Store.
- [`green_tree_tavern`](../data/structures/green_tree_tavern.json) — Green Tree Tavern.

**Primary interactions:** Observe the tannery from outside; distinguish harness from clothing trades; choose practical travel kit; finish at the approach to the road.

**Keepsake/outcome:** Equipped to Travel (Livelihood); fictional narrative memento.

**Evidence and route cautions:** Do not turn the saddler into a bootmaker; substitute a verified shoemaker business only if its dated location resolves.

## 19. A Schoolday Errand

**ID:** `schoolday-errand` · **Owner ticket:** [T-1269](../tickets/T-1269-publish-schooling-social-visits-and-careful-news.md)

**Setup/goal:** Plan a simple schooling inquiry while learning where early classes met.

**Proposed stops, in story order:**

- [`chappel_infant_school`](../data/structures/chappel_infant_school.json) — Eliza Chappel's infant school.
- [`watkins_school_house`](../data/structures/watkins_school_house.json) — Watkins school house.
- [`north_side_school_1833`](../data/structures/north_side_school_1833.json) — North Side School House.
- [`chicago_democrat_office`](../data/structures/chicago_democrat_office.json) — The Chicago Democrat Office.

**Primary interactions:** Ask a bounded fictional household question, compare the documented school histories, cross between neighborhoods and retain a useful notice.

**Keepsake/outcome:** A Schooling Note (News & Knowledge); fictional narrative memento.

**Evidence and route cautions:** Check operation dates, teachers and relocated classes before present-tense narration; exterior historical context is safer than invented active lessons.

## 20. A Sunday Circuit

**ID:** `sunday-circuit` · **Owner ticket:** [T-1269](../tickets/T-1269-publish-schooling-social-visits-and-careful-news.md)

**Setup/goal:** Take a quiet outing past a few community gathering places.

**Proposed stops, in story order:**

- [`first_presbyterian_church`](../data/structures/first_presbyterian_church.json) — First Presbyterian Church.
- [`st_marys_church`](../data/structures/st_marys_church.json) — St. Mary's Catholic Church.
- [`walker_meeting_house`](../data/structures/walker_meeting_house.json) — Walker Meeting House.
- [`sauganash_hotel`](../data/structures/sauganash_hotel.json) — Sauganash Hotel.

**Primary interactions:** Notice the buildings, read short supported histories and finish with a social visit premise. No score, sermon or compulsory choice is needed.

**Keepsake/outcome:** A Morning Among Neighbors (Neighbors); fictional narrative memento.

**Evidence and route cautions:** Do not assert an actual service schedule/day for July 1; this is an era-themed outing, not a dated recreation of a particular Sunday.

## 21. Calling on Neighbors

**ID:** `calling-on-neighbors` · **Owner ticket:** [T-1269](../tickets/T-1269-publish-schooling-social-visits-and-careful-news.md)

**Setup/goal:** Make a few imagined introductions without pretending to know who answered the door.

**Proposed stops, in story order:**

- [`brown_boarding_house`](../data/structures/brown_boarding_house.json) — Rufus Brown's Boarding House.
- [`peck_store`](../data/structures/peck_store.json) — P. F. W. Peck's Store.
- [`exchange_coffee_house`](../data/structures/exchange_coffee_house.json) — Exchange Coffee House.
- [`sauganash_hotel`](../data/structures/sauganash_hotel.json) — Sauganash Hotel.

**Primary interactions:** Choose an introduction note, learn about a merchant household, find a public meeting place and leave a fictional calling card.

**Keepsake/outcome:** An Introduction Made (Neighbors); fictional narrative memento.

**Evidence and route cautions:** Named resident information stays on sourced cards. No invented real-person quotations or encounter claims.

## 22. Gossip or Printed Notice?

**ID:** `gossip-or-notice` · **Owner ticket:** [T-1269](../tickets/T-1269-publish-schooling-social-visits-and-careful-news.md)

**Setup/goal:** Follow a rumor back to its evidence before passing it along.

**Proposed stops, in story order:**

- [`wolf_point_tavern`](../data/structures/wolf_point_tavern.json) — Wolf Point Tavern.
- [`chicago_democrat_office`](../data/structures/chicago_democrat_office.json) — The Chicago Democrat Office.
- [`chicago_american_office`](../data/structures/chicago_american_office.json) — The Chicago American Office.
- [`exchange_coffee_house`](../data/structures/exchange_coffee_house.json) — Exchange Coffee House.

**Primary interactions:** Hear explicitly invented connective gossip; inspect two eligible items; decide what is actually supported; keep a careful note.

**Keepsake/outcome:** A Careful Reader (News & Knowledge); fictional narrative memento.

**Evidence and route cautions:** Avoid defamatory invented claims about real people; uncertainty is a valid outcome and no fabricated source settles it.

## 23. Along the Working Harbor

**ID:** `along-the-harbor` · **Owner ticket:** [T-1270](../tickets/T-1270-publish-harbor-prairie-arrival-and-a-quiet-strol.md)

**Setup/goal:** Take a short outing from a warehouse toward the river mouth.

**Proposed stops, in story order:**

- [`newberry_dole_warehouse`](../data/structures/newberry_dole_warehouse.json) — Newberry & Dole's Forwarding and Commission Warehouse.
- [`dearborn_street_drawbridge`](../data/structures/dearborn_street_drawbridge.json) — Dearborn Street Drawbridge.
- [`north_pier`](../data/structures/north_pier.json) — North Pier.
- [`chicago_lighthouse_1832`](../data/structures/chicago_lighthouse_1832.json) — Chicago Lighthouse (1832 tower).

**Primary interactions:** Follow freight, inspect a crossing, view the pier and learn the lighthouse’s role; leave with a harbor route note.

**Keepsake/outcome:** Knows the Harbor (Wayfinding); fictional narrative memento.

**Evidence and route cautions:** No boarding inaccessible ships or entering the tower; use safe stand-offs and cite construction-stage limits.

## 24. From Prairie to Town

**ID:** `from-prairie-to-town` · **Owner ticket:** [T-1270](../tickets/T-1270-publish-harbor-prairie-arrival-and-a-quiet-strol.md)

**Setup/goal:** Arrive from the open ground south of town and choose a useful first stop.

**Proposed stops, in story order:**

- `anchor:lake_shore_south` — The lake shore, three-quarters of a mile south of the fort; typed viewpoint, not an invented establishment.
- [`fort_dearborn_palisade`](../data/structures/fort_dearborn_palisade.json) — Fort Dearborn — the stockade.
- [`peck_store`](../data/structures/peck_store.json) — P. F. W. Peck's Store.
- [`sauganash_hotel`](../data/structures/sauganash_hotel.json) — Sauganash Hotel.

**Primary interactions:** Orient at the open shore, approach the fort, find a supply shop and finish at a lodging place. Recommend Horse, with Fly or Instantly available throughout.

**Keepsake/outcome:** Into Town (Wayfinding); fictional narrative memento.

**Evidence and route cautions:** Do not stage the August removal, an 1812 encounter or invented Indigenous presence. Route and terrain limitations remain visible; measure the long leg.

## 25. An Evening Stroll

**ID:** `an-evening-stroll` · **Owner ticket:** [T-1270](../tickets/T-1270-publish-harbor-prairie-arrival-and-a-quiet-strol.md)

**Setup/goal:** Take a calm circuit of the familiar streets and choose a place to end your outing.

**Proposed stops, in story order:**

- [`sauganash_hotel`](../data/structures/sauganash_hotel.json) — Sauganash Hotel.
- [`peck_store`](../data/structures/peck_store.json) — P. F. W. Peck's Store.
- [`chicago_democrat_office`](../data/structures/chicago_democrat_office.json) — The Chicago Democrat Office.
- [`exchange_coffee_house`](../data/structures/exchange_coffee_house.json) — Exchange Coffee House.

**Primary interactions:** Notice a shopfront, a newspaper office and a social meeting place; end with a short keepsake note. No resource management or dramatic plot.

**Keepsake/outcome:** A Pleasant Circuit (Neighbors); fictional narrative memento.

**Evidence and route cautions:** An evening premise does not require changing the lighting engine or claiming an actual dated event; do not invent advertised entertainment.

## Initial research anchors

Use the source records already attached to the chosen claims, rather than treating
this list as a blanket citation. The following were inspected during planning:

- `chicago_democrat_1833_1835`: contemporary trade/address/notices evidence; the
  source contract requires issue date, page, column and transcription locator.
- `chicago_american_1835`: same date-and-locator discipline; later issues do not
  automatically make their news current in this scene.
- `andreas_1884_v1`: retrospective local histories; retain its limits and contradictions.
- `harrison_1830_river_mouth`: named fort service buildings on a plan, with continuity
  to 1835 inferred in the current structure records. It does not establish dialogue
  or an invented transaction, and “shop” is not automatically “blacksmith”.
- `wright_1834`, `hathaway_1834`: spatial/platted context, not unqualified floor plans
  or proof that every plotted business was active at the scene date.

Five collection families each have at least three proposed jaunts, making the planned
three-keepsake-per-family top rank possible without replay farming. The final audit
rechecks this after any route or premise substitution. At least five outings should
remain quiet, straightforward experiences with no required inventory/branching puzzle.
