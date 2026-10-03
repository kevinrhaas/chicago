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
| 26 | **Over the Draw to the North Side** — Cross the town's first drawbridge and see a brickyard, a school-house and a hotel going up on the far bank. | Town growth | 4 | Horse | Wayfinding |

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

**Route note (published, T-1260):** The shipped story order is Green Tree → Peck → Jones → Cobb → Pierce. The stops straddle the South Branch: the tavern, the saddlery and the smithy stand on the west bank, and the two stores stand on South Water Street. The order proposed above crosses the river three times, about 1,285 m in straight lines. The shipped order crosses it twice, about 1,045 m, and it still sets the list first and leaves the repair for last. It also lets the visitor choose pack or harness after the load is bought. The catalog card on the published mirror gives these routed figures at 390×780: Wagon about 9 min, Horse 6, Fly 4, Instantly 2.5. No order of these five stops comes under about 7 min at the default light-wagon pace of 3.6 m/s, because the river crossing alone is about 500 m. The overrun is the price of the owner's five trades, and it is not a reason to substitute a stop.

**Route note (T-2054, re-cut):** measured on the published mirror at 390×780 (T-2051), Wagon was 8.98 min, and as the note above says no order of the five trades fits six minutes at a wagon's pace. The five trades are kept, so two levers move together. **Horse is now the recommended mode**, which the prose allows: the visitor has no wagon until the harness choice hires one. And the stops run in the order that crosses the South Branch once, Green Tree → Cobb → Pierce → Jones → Peck (about 721 m in straight lines, against 1,045): the load's carriage is settled at Cobb's, the ironwork at Pierce's on the same corner, and the goods are bought over the river. On horseback the shipped order still read about 6.1 min. The stop texts change only where they named the old crossings; no `read_s` or `action_s` was lowered.

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

**Route note (published, T-1262):** The proposed order is kept. The stops lie about 613 m apart in straight lines (Sauganash → Hogan 43 m, → Peck 318 m, → Democrat 123 m, → Brown 129 m). Every other order that ends at the bed is longer, so Walk reads about 10.5 min on the catalog card. That is over the 4–6 min target, and Horse reads about 4. The "useful notice" is Kinzie and Forsyth's town-map notice, dated 18 June 1834 and still running in June 1835. The boarding arrangement is a cost-or-convenience preference with no rate given (L-jaunt-new-in-chicago).

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

**Route note (published, T-1263):** The shipped story order is Carpenter → Peck → Harmon & Loomis → Church. Carpenter's store stands west of Peck's corner on the same block face, so the proposed order walks west and then doubles back east past Peck's to Clark; starting at the druggist cuts that backtrack, about 40 m, and the list still ends with tea. Every good traces to a dated advertisement for its own firm: flour and calico to Peck's 1833–34 cards, liquorice ball to Carpenter's notice of 27 June 1835, tea, loaf sugar and crockery to Harmon, Loomis & Co.'s notices of 1834 and 20 June 1835. **Nothing is sold at Thomas Church's store**: the only source for it is one undated sentence naming the builder and no stock, so the stop is the tally, not a purchase, and the receipt is the keepsake. The whole walk is about 350 m along South Water, Clark and Lake.

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

**Route note (published, T-1264):** The shipped story order is Wolf Point Tavern → Green Tree → South Branch bridge → Sauganash. The order proposed above starts at the Green Tree, walks north to the forks and then doubles back past the Green Tree to the bridge; on the published mirror that read about 6.5 min at Walk. Starting at the forks and walking down the west bank removes the backtrack and still reads the fork before the crossing. The catalog card on the published mirror gives these routed figures at 390×780: Walk about 5.5 min, Wagon 3.5, Horse 3, Fly 2.5, Instantly 2. Walk sits half a minute over the 3–5 min target because about two minutes of it is reading four stops; the walking itself is about 3.5 min.

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

**Route note (published, T-1265):** The shipped story order is the brief's: stockade → guard-house → sutler's store → store-house → shop. **Stop 1 is substituted:** `fort_dearborn_palisade`'s stand-off resolves to the north bank of the river, which routed the first walk 1.2 km round by a bridge (card: Walk about 19.5 min). The stop now uses the scene anchor `fort_dearborn` ("Fort Dearborn, from the south-west"), 48 m from the guard-house, and keeps the stockade's card link. It crosses the parade twice, south gate to north-east range and back, because the errand reads in that order (state it, choose, account, deliver) and the whole fort is about 55 m across. The guard-house/store-house sides are the structure records' inference from Hubbard's magazine sentence, and the stops say the model chose them. **The sutler's supplies are invented**: no stock list for this store was found, so candles and thread are commonplace goods labelled as the story's. The store-house stop is the one with a dated document behind its use: the Army's fresh-beef proposals of 28 May and 4 June 1834. The shop is a workshop only; the plate names no trade. No soldier, sentry or garrison routine is staged.

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

**Route note (T-2004, as built):** the four stops are kept as briefed. The printed items are the Democrat of 24 June 1835 (p. 2 col. 5, the cholera paragraph; p. 3 col. 3, an auction house whose first sale is 1 July) and the American of 27 June 1835 (p. 3 col. 5, Frederick Thomas's Cholera Elixir), all transcription-mediated. The Democrat's corner is visited as its FORMER office (over Jones & King's hardware by 20 May 1835). **Timing is an outlier at Walk and is stated, not hidden:** the stops lie about 1.2 km apart on the routed streets (Sauganash → Clark 525 m, → Dearborn 166 m, → Lake and Wells 530 m), so the card reads about 17.5 min on foot, 9 at Wagon, 6.5 on Horse and 4.5 at Fly. Walk stays the recommendation because the brief names it; whether to re-cut the route or change the recommended mode belongs to T-1271's library-wide timing pass.

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

**Route note (published, T-2005):** The shipped story order is Brown → Peck → the Democrat's corner → Hogan's. The proposed order walks west from Brown's to Hogan's and then back east past Peck's to Clark, about 870 m in straight lines; the shipped order runs the block once, east and then west along South Water, about 585 m, and ends at the former mail corner, where the posting question is asked. At the brief's Walk pace (1.45 m/s) either order reads about 11 min on the card, so the default is **Horse** (about 5 min) and Walk stays offered. **The paper comes from the druggist, not Peck**: Peck's cards name no stationery, and the only advertisement read that lists letter paper is Frederick Thomas's (Chicago American, 20 June 1835, p. 1 col. 2), so the stop links his card and sells nothing. **The eligible postal notice** is the Democrat's List of Letters remaining on 31 March, printed 27 May 1835 (p. 4 col. 4). **No current counter is substituted**: Hogan's card (30 July 1834, still printed 27 May 1835) puts the post office "one door below" his South Water Street store, and Andreas puts it at Franklin and South Water from about July 1834 — a street and a neighbour, not a lot — so the outing ends with a posting plan, not a mailed receipt.

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

**Route note (published, T-2006):** The shipped story order is Western Hotel → Sauganash → Brown's boarding house → Mansion House. The order proposed above runs east from the Sauganash to Brown's, back west over the South Branch to the Western and then east again to Dearborn, crossing the river twice; starting at the Western on the west side and riding east once over the bridge and along Lake Street visits the same four houses without the backtrack. The four houses still span the town from Canal Street to Dearborn, about 0.9 km, so even the re-cut order reads **about 15.5 min at Walk** on the published mirror; the recommended pace is therefore **Horse**, as for New in Chicago and Taverns of Chicago, with Walk still offered. The catalog card on the published mirror gives these routed figures at 390×780 and 1280×800 alike: Horse about 5.5 min, Wagon 8, Walk 15.5, Fly 4, Instantly 2.5. This is the batch's quiet outing: a hidden cost-or-convenience preference and the choice of where to ask first decide among three endings, and no purse, basket or resource strip is shown.

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

**Route note (T-2007, as built):** the two warehouses are visited in the reverse of the briefed order — Democrat corner → Dole's 1832 warehouse at Lake and Dearborn → Newberry & Dole's forwarding house → Exchange — because the briefed order doubled back across town (west 351 m, east 525 m, west 397 m) and read about 7 min at Horse; the re-cut reads about 6. The only vacancies named are the two printed before the scene date: the Democrat's apprentice notice (20 May 1835, p. 3 col. 2) and Jones, King & Co.'s coppersmith and tinner (17 June 1835, p. 3 col. 3), both transcription-mediated. Newberry & Dole's role comes from the firm's own 1833 card and the American's 20 June 1835 steamboat Michigan notice; the chit and the packing promise are labelled invented where they are received. Newberry & Dole's house stands at a reconstructed position on a disputed bank and the stop says so. Card estimates on the published mirror: Walk about 16 min (15.5 at 1280×800), Wagon 8.5 (8), Horse 6, Fly 4.5, Instantly 3.5. Horse stays the recommendation as briefed; Walk is an outlier left to T-1271's library-wide timing pass.

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

**Route note (published, T-2008):** The shipped story order is Bates's auction room → the former Democrat corner → Peck's store → the La Salle slough crossing. The order proposed above starts at the Democrat corner, walks a block east to Dearborn and then doubles back west past Clark to LaSalle; on the published mirror that read about 9.5 min at Walk. Starting at the sale room removes the backtrack and still tells auction context before the particular notice. The catalog card on the published mirror gives these routed figures at 390×780: Walk about 7 min, Wagon 4, Horse 3.5, Fly 3, Instantly 2.5 (Walk 6.5 and Horse 3 at 1280×800). Walk stays a minute over the 4–6 min target because the auction room stands mid-block on Dearborn, a block east of the other three stops, and two and a half minutes of it is reading; Wagon is the faster mode. The two notices it reads are E. K. Hubbard's town lots (Democrat, 27 May 1835) and J. W. Fell's canal-route land (17 June 1835); neither names a lot price, so the errand ends at an inquiry or at holding your money.

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

**Route note (T-2009, as built):** the tally comes last — Newberry & Dole's forwarding house → Peck's store → Thomas Church's store → George W. Dole's 1832 warehouse — because the briefed order ran east 529 m to Dole's, west 310 m to Peck's and east again 122 m (961 m straight-line) and read past 7 min at Wagon; delivering first and carrying the tally a block east from Church's to Dole's is 546 m straight-line. That the tally is handed in at Dole's warehouse is invented, and the stop says Dole was the firm's partner rather than that the firm kept its books there. The wagon holds the whole three-package consignment (a `count` variable shown as *Packages*, max 3); the visitor may count it, take only Peck's two and leave Church's for a second trip, or load it on the bill's word, and the four endings follow those choices. Peck's stock is his own 1833–34 cards; Church's store has no stock on record, so his package is never said to hold anything. Card estimates on the published mirror at 390×780: Walk 10.5 min, Wagon 6, Horse 4.5, Fly 4, Instantly 3. Wagon stays the recommendation as briefed.

**Route note (T-2054, re-cut):** measured at 6.12 min by wagon on the published mirror at 390×780 (T-2051), seven seconds over the band. The route is kept, since every position on it is either attested or the structure record's own reconstruction, and the wagon is the errand. The opening and the four stop texts are shortened (about 45 words in all) and their reading seconds lowered with them at no faster a reading rate.

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

**Route note (T-2010, as built):** the briefed order stands and the whole outing keeps to one block face of South Water Street between Wells and LaSalle: Brown's, behind Peck's, west to Jones's at the Wells end, back east to Carpenter's mid-block, and on to Peck's corner beside where it began (about 210 m). It reads about 5 min at Walk (4.5 at 1280×800), 3–3.5 at Wagon and 3 at Horse. Each good is offered only where that store's own advertisement lists it: coffee, sugar and tea at Jones's (26 Nov 1833), cream of tartar and tooth powder at Carpenter's (27 June 1835), crockery and flannel at Peck's. Carpenter's June 1835 window-glass consignment is left out because its signature is cut and not proved to be his. Prices and the purse are `L-jaunt-household-provisions`.

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

**Route note (published, T-2011):** The shipped story order is Holbrook's store → Harmon & Loomis's store → Brown's boarding house → the Sauganash, one way west along South Water Street. The order proposed above starts at Brown's on LaSalle, walks two blocks east to Dearborn and doubles back west past Clark and LaSalle to Market; computed on the published mirror's own router it reads 13.5 min at Walk, 6.7 at Wagon and 4.7 at Horse. Starting at the clothing store removes the backtrack and keeps the story's sense: made goods, then cloth, then the lodging where the two occasions are weighed, then the call. The catalog card on the published mirror gives these routed figures at both 390×780 and 1280×800: Walk about 10.5 min, Wagon 5.5, Horse 4, Fly 3, Instantly 2. The recommended mode is Horse, as for A Letter Home on the same street: the Sauganash stands at the street's far west end by the South Branch, so on foot the outing is mostly walking and runs well past the quiet outing's 3–4 min, while on horseback it is 4. Fly is the faster mode. This is the batch's quiet outing: it declares no variable or inventory and shows no strip. Holbrook's June 1835 card offers made goods as agent for the manufacturers and names no tailoring; Harmon, Loomis & Co.'s cloth list is their November 1834 notice, carried by their June 1835 card. No maker, fitting or price is claimed.

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

**Route note (published, T-2024):** The briefed order is kept: the Western Hotel's stable → S. B. Cobb's saddlery → Asahel Pierce's smithy → the Green Tree, a block north up Canal Street from Randolph to Lake and then east along Lake to West Water, with no backtrack. The repair is an invented cracked trace and, if the visitor looks the harness over in the yard, a worn whiffletree hook. Leather goes to the saddler and iron to the smith, and that division is read from the two firms' own records: Goss & Cobb's 1833 advertisement lists harness, bridles and trunks and promises repairs 'immediately attended to when brought to their shop', Cobb's June 1835 card continues the business, and Andreas's Pierce paragraph is ironing a stage line and making ploughs. The saddler is never made a smith, and neither shop is said to have done this repair. At the Green Tree the visitor calls the outfit ready (only if the trace was restitched) or keeps tomorrow's trip short, and the four endings follow those choices. The Wagon recommendation stands as briefed: the route is short and the brief's subject is a wagon outfit. Card estimates on the published mirror: Walk 7.5 min, Wagon 5, Horse 4, Fly 3.5, Instantly 3 at 390×780 (Walk 7, Wagon 4.5 at 1280×800). The primary path measured 281 s at Wagon and 207 s at Fly against estimates of 290 s and 215 s. Flags only, no shown variable or inventory: there is nothing to count. Receipt: `docs/performance/jaunt-mend-the-harness/`.

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

**Route note (published, T-2025):** The shipped story order is Elston & Co.'s works → Jones's grocery → Church's store → Brown's boarding house. The order proposed above goes out from South Water Street to the works and back again, so it crosses the river twice: about 1,125 m in straight lines, and on the published mirror the card read Walk 31.5 min and Horse 9. Starting at the works crosses once (works → Jones 411 m, → Church 191 m, → Brown 112 m, about 714 m) and still reads the trade before the list: the works stop settles whether soap or light matters most, the list and what to carry are settled at Jones's, and nothing is bought at Church's store, whose one undated source names no stock. **No counter at the works is claimed**: the stop is an exterior observation of a site no source gives (the scene's placement on the North Branch is conjectural), and where the story's bundle came from is left unrecorded. Elston & Co.'s goods — hard and soft soap, wax and other candles, cash paid for tallow and house ashes — are their own notice in the Democrat's first number (26 November 1833, p. 3, col. 6), still printed on 2 July 1834. **Timing is an outlier at Horse and is stated, not hidden:** the card reads Horse about 7 min, Walk 22 (21.5 at 1280×800), Wagon 10.5, Fly 3.5 and Instantly 3 at 390×780, and about three of the seven minutes are the one ride from the works' placement to the first bridge and back to South Water Street. Every order of these four stops pays that ride at least once, and the works is the brief's subject, so the recommendation stays Horse with Fly as the quick version. The primary path measured 428 s at Horse and 217 s at Fly against estimates of 425 s and 224 s. This is the batch's quiet outing: two hidden preferences (what matters most, what is carried) choose among four endings, and no purse, basket or resource strip is shown. Receipt: `docs/performance/jaunt-soap-and-candles/`.

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

**Route note (published, T-2026):** The shipped story order is Newberry & Dole's warehouse → Peck's store → Blodgett's brickyard → the Lake House. The order proposed above goes north to the brickyard and the Lake House and then back over the river to Peck's, so it crosses twice: about 1,660 m in straight lines (435 + 498 + 726). Taking Peck's second crosses once (228 + 228 + 498, about 954 m) and lets the jaunt end at its biggest sight, the brick shell going up at Rush Street. The bounded order is two choices and no prices: **nails or nail rods** at Peck's (both are lines of his own notice, 10 September 1834, p. 3 col. 1) and **brick for a chimney or none** at the yard; three endings. **No order, price or sale is claimed anywhere**, and the Lake House stop does not say its brick came from Blodgett's yard, because no source says so; the structure record's research note leans that way and the jaunt does not follow it. The Lake House is a building site, not lodging: Andreas describes the finished hotel (brick, three storeys and a basement, opened autumn 1836), the 1835 groundbreaking is an uncredited modern paragraph and the stop says so, and the one-storey roofless shell is called our reconstruction. Newberry & Dole's card is the Democrat of the scene date itself (1 July 1835, p. 4 col. 4: storage, forwarding and commission, agents for the Merchants' Line). **Timing sits inside the band:** the card reads Horse about 6 min, Walk 17.5, Wagon 8.5, Fly 4 and Instantly 3 at both 390×780 and 1280×800. The primary path (cut nails, brick chimney) measured 364 s at Horse and 226 s at Fly against estimates of 361 s and 232 s at 390×780 (365 s and 225 s against 364 s and 232 s at 1280×800). Receipt: `docs/performance/jaunt-materials-for-a-roof/`.

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

**Route note (published, T-2027):** The shipped story order is Holbrook's store → Miller's tannery → Cobb's saddlery → the Green Tree. The order proposed above starts at the forks, goes west to Lake and Canal, east across the South Branch to South Water Street and back west again: about 1,871 m in straight lines, crossing the South Branch twice. Starting at Holbrook's goes one way, east to west (Holbrook → tannery 718 m, → Cobb 250 m, → Green Tree 122 m, about 1,090 m), and the story still reads: made goods shipped in, then where the town's own leather began, then the leather trade that is not the clothier's. **No shoemaker was substituted** — the boots come from Holbrook's card, which names boots and shoes; the saddler's card names none, and a choice at his stop says so. The tannery stop claims no work on the scene date: its source trail ends in 1832.

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

**Route note (published, T-2028):** The shipped story order is Hamilton's house on Michigan Street (`watkins_school_house`) → the North Side school-house → Chappel's log house by State Street → the Democrat's corner. The order proposed above starts south of the river, goes north for the two Watkins houses and comes back for the Democrat, so it crosses the river twice: routed on the published mirror it is 808 + 607 + 330 m and the primary path measured about 449 s at Horse (7.5 min). Starting north of the river crosses once and reads the schools in date order: Watkins's house of 1833, the north-bank school-house of 1833 that was the North Side's public school in 1835, then Chappel's infant school of 1833–34, which had moved into the Presbyterian church in 1834. The household's question is asked at the first stop instead of at Chappel's. **Only one school is narrated in the present year, and only by its year**: the north-bank school-house, which Andreas has in use as a public school in 1835 with Watkins's retirement undated. The Michigan Street house and Chappel's log house are narrated as history, because their structure records mark the school use on the scene date unattested; Chappel's site is also an open conflict (Andreas's 'just outside the military reservation' against two other readings) and the stop says other accounts differ. **The useful notice is the scene date's own**: the Democrat dated 1 July 1835 (p. 3 col. 5, `chicago_democrat_1835_07_01#c012`, first printed 17 June) calls a meeting of School District No. 4 in the Presbyterian Church on 7 July to consider building a school house. The Democrat's corner is visited as its former office (by 20 May 1835 it printed over Jones & King's hardware).

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

**Route note (published, T-2029):** The shipped story order is St. Mary's → Presbyterian → Walker meeting house → Sauganash. The order proposed above goes east from Clark to State and then all the way back west across the South Branch, about 1,420 m in straight lines (Presbyterian → St. Mary's 255 m, → Walker 922 m, → Sauganash 243 m). Starting at St. Mary's walks one way along Lake Street, about 1,169 m (→ Presbyterian 255 m, → Walker 671 m, → Sauganash 243 m), and still ends at the call. On the published mirror the card reads Horse 6.5 min and Walk 22.5, so the default mode is Horse, not the Walk this brief names. **Horse is half a minute over the 4–6 min band.** The cost is the Walker meeting house: it stands across the South Branch from the other three, so every order that keeps it and ends at the Sauganash crosses the river twice. Its bank is disputed and the stop calls its marker a placeholder. The Presbyterian church carries the scene-year notice calling School District No. 4 to meet there on 7 July 1835; the meeting is after the scene date and is not narrated as held. No service, day or minister is asserted (L-jaunt-sunday-circuit).

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

**Route note (published, T-2030):** The shipped story order is the briefed one: Brown's boarding house → Peck's store → the Exchange Coffee House → the Sauganash. The two choices are the letter of introduction presented (a merchant's or a minister's) at Brown's and where the calling card is left (the Exchange, where J. A. Marshall's November 1834 notice asked addresses to be left, or the Sauganash) at the Exchange; Peck's stop sends the visitor to the household's card rather than to a door. The Exchange is the public meeting place on the Democrat's own reports of Democratic meetings held there in April and June 1835. **Recommended mode is Horse, not the brief's Walk:** the primary path measures about 8.7 min at Walk on the published mirror, past the 4–6 min band, and 4.1 min at Horse; Walk stays allowed.

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

**Route note (published, T-2031):** The shipped story order is the Wolf Point Tavern → the Exchange Coffee House → the Democrat's corner → the American's office, and the default mode is Horse. The order proposed above doubles back from the American at Dearborn to the Exchange at Wells, and the forks lie across the river from both papers: routed on the published mirror it measured Walk 1,233 s (20.5 min) and Horse 402 s on the primary path at 390×780. Taking the Exchange second never doubles back: Horse 340 s against the card's 333 s (5.5 min), Fly 227 s, Walk 821 s; no order of these four stops makes a 4–6 min walk. **The rumors are invented and the papers are not.** The land-sale item is the Democrat of 1 July 1835, p. 3 col. 2 (`chicago_democrat_1835_07_01#c020`), in the editor's own hedge ("we have not been able to ascertain … led to believe"); the second figure of "between Fi[v]e and […]red Thousand Dollars" does not survive in the transcription, so the stop says it is lost instead of repeating the extraction's supply. The bank item is the American of 27 June 1835, p. 1 col. 5 (`chicago_american_1835_06_27#c001`), reprinted from the Sangamon Journal: a Chicago branch decided, its officers not made known, and a brick building on the square near the court house that is read as Springfield's (the stop does not quote the phrase: "re, near" is the extraction's supply for a damaged line, T-2040). Neither rumor is put in a real person's mouth, and the endings let uncertainty stand.

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

**Route note (published, T-2032):** The shipped story order is Newberry & Dole's warehouse → the Dearborn Street drawbridge → the 1832 lighthouse → **the south pier** (`south_pier`), which stands in for the north pier as the destination. The north pier is still the stop's subject: the walker looks at it across the cut, and the choice is whether to mark it or the light. **The reason is the route, measured.** The north pier's stand-off is on the north bank at the mouth, so the router reaches it only over the Dearborn draw, 949 m from the bridge. Every order of the four briefed stops routes at 2.6 km or more (warehouse → light → draw → north pier: 1,096 + 598 + 949 m). That card read **Horse about 9.5 min, Walk 33 min**, well outside the 4–6 min band. The south pier's stand-off is 147 m from the light and about 93 m from the north pier's, across the channel, so the walk stays on the south bank: 502 + 598 + 147 m, about 1,250 m. The drawbridge is inspected from its south end and not crossed. **Construction-stage limits are cited on the stop.** Both piers grew all season, and no source gives either length on 1 July 1835. The north pier ran from about 700 ft at the end of 1834 to 1,260 ft by the end of 1835. Andreas has the south pier extended 500 ft in 1835, to 700 ft in all. The scene's 900 and 400 ft are interpolations, and the stop calls them our estimate. The light is seen from outside, and its keeper on the scene date is not named because no source reached names one. No vessel is boarded, no cargo is named, and no walk along either pier is claimed. **Timing sits inside the band:** the card reads Horse about 6 min, Walk 17, Wagon 8.5, Fly 4 and Instantly 2.5 at both 390×780 and 1280×800. The primary path (mark the end of the north pier) measured 355 s at Horse and 221 s at Fly against estimates of 350 s and 227 s at 390×780 (320 s and 221 s against 354 s and 228 s at 1280×800). Receipt: `docs/performance/jaunt-along-the-harbor/`.

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

**Route note (published, T-2033):** The shipped order is the brief's: shore viewpoint → stockade → Peck's → Sauganash, about 2.28 km in straight lines (→ stockade 1,218 m, → Peck's 726 m, → Sauganash 333 m). The first stop is the scene anchor and says it is a viewpoint, not a place; what it says of the ground is cited (Wright 1834's Fractional Section 15, no land-office entry before 31 May 1836, platted 13 June 1836). **The long leg, measured as the brief asks:** on the published mirror the shore → stockade leg takes 300 s at Horse and 58 s at Fly at both 390×780 and 1280×800. The whole primary path measures 560 s at Horse against the card's "about 10 min", and 231 s at Fly against "about 4 min". **Horse is three and a half minutes over the 4–6 min band, and that is kept on purpose:** the length is the subject — the town begins three-quarters of a mile from where the outing starts — and Fly and Instantly stay offered at every stop. The tents passed on the reservation are the model's conjecture and the leg note says so (L355, L358). Nothing of 1812 is staged (L-jaunt-from-prairie-to-town).

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

**Route note (published, T-2034):** The shipped order is the brief's: Sauganash → Peck's → the Democrat's first corner → the Exchange, about 0.71 km in straight lines (→ Peck's 347 m, → the Democrat 123 m, → the Exchange 245 m). The last stop asks where the evening ends — at the Exchange, or back west along Lake Street to the Sauganash — and each choice leads to its own ending with the same keepsake, so the circuit the brief names is the walker's to close. On the published mirror the card reads Horse 4.5 min at both 390×780 and 1280×800, and the primary path measures 268 s at 390 (257 s at 1280); Fly reads 3 min and measures 173 s. **The default is Horse, not the Walk this brief names:** Walk reads 12.5 min (765 s measured), well past the 4–6 min band, and Walk stays offered. The evening is a premise only: the scene's light is not changed, and no entertainment, meeting or dated event is claimed. The one new claim — that the Democrat came out weekly, on Wednesdays — is inferred from the dated issue numbers already cited, not from a masthead (L-jaunt-an-evening-stroll).

## 26. Over the Draw to the North Side — the growth path (beyond the initial 25)

**ID:** `over-the-draw` · **Owner ticket:** [T-2042](../tickets/T-2000-2249/T-2042-prove-the-growth-path-with-a-26th-jaunt-added-by.md) (piece 4 of T-1271)

**Setup/goal:** Cross the Dearborn Street draw into the North Side and look at what stood on the far bank. The 25 above are the owner's initial library; this one is the first jaunt added after it, and it was added the way every later one should be: one JSON file in `data/jaunts/`, compiled by `tools/compile_jaunts.py`, and no change to the renderer's code or styles. It is kept as a real jaunt, not a fixture removed after the demonstration.

**Stops, in story order:**

- [`dearborn_street_drawbridge`](../data/structures/dearborn_street_drawbridge.json) — Dearborn Street Drawbridge.
- [`brickyard_north_side`](../data/structures/brickyard_north_side.json) — Blodgett's Brickyard.
- [`north_side_school_1833`](../data/structures/north_side_school_1833.json) — North Side School House.
- [`lake_house_construction`](../data/structures/lake_house_construction.json) — Lake House (under construction).

**Primary interactions:** Look from the street; at the last stop choose whether to end on the North Side or go back over the draw. No resource, no strip: a quiet outing.

**Keepsake/outcome:** North of the River (Wayfinding); fictional narrative memento. Wayfinding had the fewest jaunts of the five families (4), so this one goes to it.

**Evidence and route cautions:** Every building claim is reused word for word from a published jaunt (Along the Working Harbor, Materials for a Roof, A Schoolday Errand); no claim is new. No passage over the draw on a given day is claimed, and the Lake House shell is the scene's reconstruction of a site Andreas only describes finished in 1836 (L-jaunt-over-the-draw).

**Route note (published, T-2042):** The draw's south end to the brickyard is about 0.12 km over the river, the school-house is about 20 m on, and the Lake House site about 0.5 km east along the bank: about 0.65 km in straight lines. The measured card estimates are in [the acceptance report](measurements/jaunts_acceptance_2026-10.md).

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
