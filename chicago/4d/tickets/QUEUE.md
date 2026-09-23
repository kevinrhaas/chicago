# QUEUE — top is next. The parser reads only T-NNNN lines; ticket files hold evidence and acceptance.
# The owner sets the order. Work top-down, skipping a blocked or already-claimed ticket.
# Add findings to an existing ticket first. Put new one-run work beside its dependency;
# add new research readings to RESEARCH COMPLETION so the spend band can drain.
# Split multi-run epics into bounded tickets when reached; do not create a refill at the top.
# Research spend: fix identity/date/mint gates before deriving cards. THE LETTER-LIST
# RULING IS MADE (owner, 2026-09-18: option (c) on T-0660) — refusals 7 and 8 are
# mint-time rules and do not un-mint a standing record; nothing is retired, rank() is
# unchanged, and the pass SAYS a collision instead of acting on it. T-1144 is no longer
# waiting on anything and is the queue's second row; the line that told runs to skip it
# is gone with this. T-0691 shrinks to wiring its --check into check.sh.
# South Through Time: 1812 depiction follows AGENTS.md Indigenous-history review;
# ship no human figures. T-0469/T-0470/T-0471 depend on T-0468; T-0472 on T-0470.
# Prairie Avenue: T-0474 follows T-0473; T-0475/T-0477 follow T-0474;
# T-0476 follows T-0475. Respect needs_bake and other ticket-level blockers.
# Completion: preserve explicit refusals and later/out-of-town evidence; zero
# unclassified research does not mean forcing uncertain people or locations into 1835.
# T-1027 is the one-letter identity epic; Newberry and 1840 deposit work follow
# their lower resident yield. Read each ticket before splitting or claiming.
# Reconstruction (owner, 2026-09-17): BAND 2 IS OPEN NOW — it reads the layer and writes
# reports, models and an order book, and it needs no sign-off to do that. Bands 3-5 WRITE
# reconstructed people, businesses and roofs, and those wait for T-1157 to say GO.
#   The first cut gated 2-5 together, and it starved the top: band 1's rows were all in
#   flight or self-blocked, so runs fell past 59 gated tickets into SOUTH THROUGH TIME and
#   LOOP IMPROVEMENTS (T-0467, T-1154, 2026-09-17). A gate that empties the top of the
#   queue sends the loop to the bottom of it.
# Every reconstructed value carries tier, basis, seed and replaceable_by (T-1158); the order
# book (T-1166) is the quota; docs/RESEARCH/1835_reconstruction_plan.md is the map.
# Sub-bands (3A/3B/3C, 5A-5E) may be taken by different agents; within a sub-band, top first.
# Build tickets in 5C are needs_bake and hand on a successor. Native, Métis and Black residents,
# families and businesses ARE reconstructed (owner, 2026-09-17; T-1177), review_required, no figures.
# Owner, 2026-09-17: THE CITY COMES FIRST. Bands 6 (arrival and jaunts) and 7 (south
# through time) are PARKED BEHIND IT — jaunts first, then south through time. They were
# numbered 5F-5J, which read as part of the 5A-5E structures programme and is why they
# looked like city work; they are band 6 now so the ordering says what it means.
#   AND A RUN MAY NOT FALL INTO THEM. While any row in bands 1-5 is workable, that row is
# the work. If the top is gated or every row is in flight, the run SAYS SO and stops — it
# does not walk down to band 6, 7 or 8. That fall-through is how T-0467 and T-1154 were
# picked up out of the bottom of a 148-line queue on 2026-09-17 while the city waited.
# TICKET BUDGET (T-1295, owner 2026-09-17: "I don't want too many tickets and not making
# any progress"). `ticket.mjs new` REFUSES at 140 queue lines, and refuses a branch its
# fourth new ticket. Override is `--anyway --why "<reason>"` and the reason is written into
# the file. Filing is free and working is not — add a finding to the ticket it was found in
# first, which is what the line above already asks for. `split` is exempt: it replaces a
# ticket rather than adding one. An EPIC states its own cap in children (T-1236: three).
# --- 1. RESEARCH SPEND — truth, safe derivation, roles, profiles, and locations
T-1254 — Migrate the external structured role evidence — newspaper gazetteer, 1839 directory and civic register, 1843/1844 identity master — with each role's stated place and employer, and publish the migration table
T-0660 — The letter-list pass minted the same man twice when the paper printed his name in both orders, and the corrected reading now shows it
T-1144 — Converge the resident layer after the standing truth tickets: zero synthesis and mint drift, no false Chicago resident, and no 1835 claim above its dated evidence
T-1241 — Run the T-1143 ledger over the final resident, household, business and structure layers and publish the closing research audit at zero unclassified units
T-1157 — Sign off the research spend: one owner-readable coverage report over residents, households, plural roles, business staff and every home, work and other significant location, and the gate that lets reconstruction begin
# --- 2. 1835 TOWN ANALYSIS — the known population profiled, the town modelled, the order book (OPEN NOW)
T-1159 — Export the borderline roster: every name the research read and withheld from 1835 — single-source, refused, surname-only, uncertain presence, letter-list-only — with its source, reason and re-admission class, so reconstruction can name real people before it invents any
T-1301 — Spend the 98 corroborated_enrichment research units the remainder ruling hands to T-1160: each sourced fact about a person this town already holds written into the structured field that carries it, or repointed to the attribute-fill ticket whose acceptance owns it
T-1166 — The reconstruction order book: known minus model, per bucket and per division — exactly how many persons, households, businesses and structures of each kind to reconstruct, in the order the bands below will build them, published as a card
# --- 3A. RECONSTRUCT RESIDENTS — programme, then complete the known people (attributes, arrival, families, re-admissions)
T-1167 — The 1835 resident reconstruction programme: one recipe file, one generator, the `reconstructed` grade turned on — superseding the retired programme without restoring it, and stating the owner's 2026-09-17 override of the no-estimation rule
T-1168 — Fill sex and age for every attested and inferred person: recorded where a source says, inferred from forename, office or register role where the evidence about that person allows, reconstructed from the population model otherwise — each value with its tier and reason
T-1169 — Fill arrival date, origin and reason for coming for every attested and inferred person: the earliest dated appearance as the bound, the biographies where they speak, the arrival model otherwise — dated, tiered and explained
T-1170 — Give the attested and inferred heads the families the sources name: spouses, children, kin and dependants from the baptism and marriage registers, the 1840 census rows of heads the layer carries, Andreas and old-settler biographies and the ruled kin ties — inferred where named, reconstructed where only counted
T-1171 — Give the remaining attested and inferred heads reconstructed families from the household model: wives, children, servants and apprentices drawn by the head's age, trade and household type, seeded, named from the pools, every member marked reconstructed
T-1172 — Re-admit the borderline roster as reconstructed residents under their own read names: fix the uncertain presences, mint the single-source and 1834-return names, back-project the biographied later names — every re-admission with its evidence limit and its reopen rule
# --- 3B. RECONSTRUCT RESIDENTS — fill the model: trades, women and children, lodgers, garrison, cohorts, transients
T-1173 — Reconstruct the trade households the occupation model still wants after the known and re-admitted people are counted: labourers, carpenters, teamsters, sawyers, masons, boatmen, clerks and the rest, by division, each head named from the pools with a family per the household model
T-1174 — Reconstruct the women and children the age pyramid still lacks after families are drawn: widow-headed households, laundresses, seamstresses, domestics and schoolmistresses, the boarding-house keepers' families and the children of the 1833–35 arrivals, to the population model's sex and age bands
T-1175 — Fill the beds: boarders, lodgers, hotel guests, boarding-house keepers' households, the crews of the vessels in port and the hands at the works, seated in the named and reconstructed lodging places to the lodging model's capacities
T-1176 — Reconstruct the Fort Dearborn garrison of 1 July 1835: the officers the sources name, the companies of the 5th Infantry to their strength, the surgeon, the sutler, the laundresses and soldiers' families, the Indian Agency establishment as attested — seated in the fort's roofs
T-1177 — Reconstruct the under-documented cohorts within their evidence: the Native and Métis people, households and businesses in and around the town, the free Black residents, families and Black-owned businesses, and the Irish and German Catholic town the register implies — every one identified, tiered and reviewable
T-1178 — Reconstruct the transient population of 1 July 1835 as a bounded cohort: the land-sale visitors, the immigrants awaiting lots, the harbour-works gang and the crews ashore — who they were, how many, and where they slept (tents, wagons, floors, vessels) — for the camps the structure band will build
# --- 3C. RECONSTRUCT RESIDENTS — converge
T-1179 — Converge the reconstructed resident layer: index, sidecars, town census, People view and gates agree; every reconstructed person carries basis, seed, liberty and substitution rule; the population profile is re-run and the town reads complete against the model
# --- 4. BUSINESSES — the authored layer and view, the audit, staffing model, five reconstruction groups, staff, converge
T-1180 — An authored business layer: one record per business with tiered proprietors, partners, staff, dated primary and secondary locations and sources — compiled into the register beside the newspaper-derived firms, with the structure function vocabulary normalised
T-1181 — A Businesses view in the app: every firm by trade, street and tier, with its proprietors, staff, dated locations and location limit on one card — the visible surface for the audit and reconstruction bands
T-1182 — Audit every attested and inferred business against the research: proprietors, partners, dates, primary and secondary premises, the Dec 1835 State census classes and the August 1835 American count — and raise an inferred business for every in-window trade that has none
T-1183 — The 1835 business staffing model: how many clerks, journeymen, apprentices, printers, bar-keepers, hostlers, cooks and teachers each kind of business employed, from the sources the project holds — the rule every business is staffed by
T-1184 — Reconstruct the missing stores and provision trades: dry goods, groceries, hardware, drug, book and provision houses, packers and the market, to the order book's quota, each with a period firm style, a reconstructed proprietor household and a location class
T-1185 — Reconstruct the missing mechanics' shops: smiths, carpenters and joiners, coopers, wheelwrights and wagon makers, tailors, shoemakers, tanners, saddlers, tinners, masons, painters, bakers and butchers, to the twenty-five mechanics' shops and the occupation model's quota
T-1186 — Reconstruct the missing professions and services: physicians and law offices to the State census's 14 and 22, land agents, surveyors, a dentist's stand, barbers, teachers, laundresses, seamstresses and domestics, as businesses or as no-premises employments
T-1187 — Reconstruct the missing lodging, river and transport businesses: boarding houses to the 42-roof programme, the inns the lodging model wants, forwarding and warehouse hands, the ferries, drays and livery, the lumber yards, the pier-works gang and the vessels in port
T-1188 — Complete the civic, church, school and press establishments as businesses with staff: the post office, the land office opened in 1835, the county offices, the schools, the churches and the two printing offices — attested where the sources name the officer, reconstructed for the rest
T-1189 — Staff every business — attested, inferred and reconstructed — with real persons: attested partners and clerks first, then the reconstructed residents, then new reconstructed staff to the staffing model, so every working person has a workplace and every workplace its people
T-1190 — Converge the business layer: register, businesses, persons and structures agree by id; every reconstructed firm carries its substitution rule and liberty; the trade-census crosswalk, the order book and the Businesses view print the finished count
# --- 5A. STRUCTURES — ground: north and west streets and alleys, terrain extent, the lot grid beyond the river
T-1191 — Seat the North Division's streets and alleys as platted corridors: Kinzie's Addition and the Kinzie–Michigan tier off Wright and Hathaway, with block faces, mid-block alleys and corridor control, so a north-side roof can be dealt to a lot
T-1192 — Seat the West Division's and Wabansia's streets and alleys as platted corridors off Wright and Hathaway — Canal, Clinton, West Water, Carroll, Fulton, the School Section tier and the Wabansia grid north-west of the forks — with the small lots the sheets draw
T-1193 — Extend the modelled ground to N +760 and E −700: heightfield, collision, water mask, North and South Branch banks, flora and minimap together, so the North Division's second parcel and the West Division's held slots have ground to stand on
T-1194 — Generate the lot grid north and west of the river: Thompson's North Division blocks, Kinzie's Addition, Wabansia, the West Division blocks and the School Section tier — numbered lots from each sheet's own module, the small lots kept small, buildable ground tested
# --- 5B. STRUCTURES — seating: placement policy, roof programme re-derived, anonymous roofs redealt, everyone seated
T-1195 — The placement policy of 1835, written as testable rules with their evidence: who lived and worked where — merchants and forwarders on the river and Lake Street, professionals by the square and the hotels, mechanics on the side streets, labourers on the small lots and the fringes, farms and country seats outside — and how many buildings a main-street lot held
T-1196 — Re-derive the roof programme from the order book: the 668-roof schedule re-cut by what the population, occupation and lodging models say the town needed — families, districts and blocks re-targeted, every delta from the spec stated, the census's 398 dwellings reconciled
T-1197 — Re-audit the 285 anonymous roofs against the re-derived programme: keep the ones the order book can occupy, re-family the ones of the wrong kind, retire the ones that no longer fit — 214 stand empty today — and record every change as a substitution, not a demolition
T-1198 — Seat every attested and inferred household and business on the ground its evidence allows: a structure where one is named, a lot on the right face where an address, corner or later directory narrows it, a division band where only that is known — plural, dated, no fabricated coordinates
T-1199 — Seat every reconstructed household, business, lodging house and camp by the placement policy into the extended lot grid: multiple buildings per main-street lot, single roofs on the back streets, labourers on the small lots and fringes, the noxious trades on the branches — deterministic, order-book-counted
# --- 5C. STRUCTURES — build, one district per run, baked, successor handed on (frame budget measured before every push)
T-1200 — Build the South Water Street river front to its seats: the forwarding houses, warehouses, stores and store-residences on the party lines from Market to State, the freight sheds and landings behind, every roof with its firm and its keeper
T-1201 — Build the Lake Street and Dearborn–Clark–LaSalle core to its seats: the store fronts and store-residences, the hotels' neighbours, the professional offices over shops, the mechanics' shops on State and Dearborn, the cottages behind them
T-1202 — Build the Randolph–Washington tier and the public square's neighbours to their seats: the professional and merchant houses (H1/H2), the churches and schools the civic band established, the log jail and the estray pen as they stand, the dwellings falling southward
T-1203 — Build the South Division's outer ground to its seats: the Fort Dearborn Addition and Michigan Street tract dwellings, the Clark–State cottages south of Washington where the ground allows, the packing and slaughter yards on the South Branch, the country places outside the plat
T-1204 — Build the fort reach and the lakefront to their seats: the sutler's, the garrison's outbuildings and the Agency establishment as the dossiers allow, the lighthouse keeper's, the pier-works yard at the river mouth, the Lake House's neighbours on the north bank east end
T-1205 — Build the North Division's Kinzie band to its seats: the Kinzie properties' neighbours, the North Water bank's forwarding and heavy trades, the Wolcott–Kinzie core's stores and taverns, the brickyard and the school, the dwellings between Kinzie and Michigan
T-1206 — Build Kinzie's Addition and the north tier to their seats: the labourers' and mechanics' cabins, shanties and small cottages on the addition's small lots, the scattered better houses on the Rush–Pine fringe, the open ground left honestly open
T-1207 — Build the West Division's Wolf Point and Canal Street approach to their seats: the taverns' yards and stables, the grocery and blacksmith on the approach, the ferry and the bridge heads, the cabins and boarding houses of the forks
T-1208 — Build the West Division's outer clusters and Wabansia to their seats: the three looser clusters toward the Des Plaines edge, the Wabansia cabins on the North Branch, the farms and barns on the prairie edge, the held 35 slots released on the extended ground
T-1209 — Build the boarding houses to their beds: the H1–H3 houses the lodging model sized, each with the window rhythm, service wing and stovepipes its capacity implies, its stable and privies, on the seats near the landings and approaches — and re-size the named hotels' outbuildings to their guests
# --- 5D. STRUCTURES — finish: fabric by household, plank walks, yards, signs, camps
T-1210 — Deal building fabric, finish and weathering by who lived and worked there: a physician's or forwarder's house painted and glazed, a tradesman's cottage weathered clapboard, a labourer's cabin unpainted and patched — the rule set on the material sheet, applied to every dwelling and business, no attested finish moved
T-1211 — Plank sidewalks, stoops, hitching posts and street crossings for every business face, varied by the business — a forwarding house's wide decked walk, a store's board walk and stoop, a smithy's bare ground and rail, a tavern's posts and mounting block — extended to the new fronts town-wide
T-1212 — Yards for every household: lot-line and dooryard fences, gardens, woodpiles, wells, privies and stables assigned by household type, wagons and barrels and trade goods at the shops by trade — the enclosure, yard and outbuilding layers extended to the reconstructed town
T-1213 — Signboards for every business that would have hung one: the reconstructed firms' names and trades in period lettering and forms, the attested signs untouched, the signless trades left signless by rule
T-1214 — Build the camps of the summer of 1835: a tent and wagon-camp archetype, the encampments on the grounds the transient ticket evidenced — the land-sale crowd south of the fort, the immigrants' wagons at the west approach, the pier gang at the river mouth — bounded, labelled, and empty of figures
# --- 5E. STRUCTURES — converge: every person housed, every business roofed, the town complete
T-1215 — Converge the reconstructed town: every person housed, every business roofed, every roof occupied or its use stated, the census's dwellings ratio met, the programme reconciled, the budgets re-measured and set — the completion report a visitor can open
# Arrival/jaunts: read docs/ARRIVAL-JAUNTS-EXECUTION.md; honor ticket dependencies.
# Finish each subsection; unavoidable successors stay beside their dependency, not at the tail.
# --- 6A. ARRIVAL AND SOURCES — measured loading, time rollback, source library, free start
T-1246 — Expose real boot phases and yield long scene-building tasks
T-1292 — Move the town census off the loader into an Evidence → City summary topic
T-1247 — Roll the year back into a restrained time-machine arrival
T-1248 — Compile the sources used and their reconstruction backlinks
T-1275 — Give the loading journey 160 varied source and reconstruction statuses
T-1276 — Browse every source the reconstruction used, with its counts and used-for links
T-1277 — Share one destination search for Go to and Explore Myself
T-1278 — Land on a warm mobile welcome with Jaunts and Explore Myself
# --- 6B. JAUNTS ENGINE — content contract, navigation, travel, choices, history and menu
T-1253 — Define validated jaunt JSON and render a real pilot preview
T-1279 — Make the pilot jaunt playable with persistent stop navigation
T-1280 — Offer live jaunt travel modes and honest quick-play estimates
T-1256 — Support bounded choices, inventory and alternate jaunt endings
T-1257 — Connect jaunt stops and travel to optional historical context
T-1258 — Collect era-themed keepsakes in a five-family Chicago daybook
T-1259 — Finish the scalable Jaunts Menu and integrated start experience
# --- 6C. PRIORITY JAUNTS — six short stories, fully authored and playable
T-1260 — Publish Outfit for the West as a five-minute jaunt
T-1261 — Publish Taverns of Chicago as a five-minute jaunt
T-1262 — Publish New in Chicago as a five-minute jaunt
T-1263 — Publish Shopping South Water Street as a five-minute jaunt
T-1264 — Publish Across Wolf Point as a five-minute jaunt
T-1265 — Publish Fort Dearborn Errand as a five-minute jaunt
# --- 6D. EVERYDAY JAUNTS — nineteen additional outings in five bounded content batches
T-1266 — Publish news, mail, lodging and work jaunts
T-1267 — Publish land, freight, household supplies and clothing jaunts
T-1268 — Publish harness, candles, building materials and leather jaunts
T-1269 — Publish schooling, social visits and careful news reading jaunts
T-1270 — Publish harbor, prairie arrival and a quiet stroll jaunts
# --- 6E. ARRIVAL AND JAUNTS COMPLETE — content convergence and published mobile acceptance
T-1271 — Reconcile and time the complete 25-jaunt library
T-1272 — Verify arrival, jaunts and source browsing on the published mobile app
# --- 7. SOUTH THROUGH TIME — dated terrain, Fort Dearborn, and Prairie Avenue
T-1286 — Cross-check the derived 1812 pre-cut shore against the Harrison 1830 trace, and record what the two readings disagree about
T-1243 — Author the e1830_natural terrain spec and generate the 1812 heightfield and the ground and water meshes across the Fort-to-Eighteenth-Street corridor
T-0469 — Reconstruct the first Fort Dearborn complex as it stood in August 1812
T-0470 — Map the 15 August 1812 evacuation route and battle-location confidence zone
T-0471 — Build the 1812 lakeshore prairie, vegetation and landscape features
T-0472 — Build the 1812 interpretive scene with Indigenous-history review gates
T-1250 — Trace the 1880s Illinois Central lake edge and fill shore_1880s_ic_edge from a sourced period sheet
T-1251 — The e1871_postfire terrain spec: the graded, filled and raised South Side ground as an authored zone table
T-1252 — Generate and bake the e1871_postfire heightfield over the Prairie Avenue reach
T-0474 — Reconstruct the 1880s Prairie Avenue street, parcel and service grid
T-0475 — Build the Prairie Avenue landmark mansion core
T-0476 — Fill the 1880s Prairie Avenue corridor with documented residences and outbuildings
T-0477 — Build the 1880s Prairie Avenue streetscape, vegetation and urban furniture
# --- 8. LOOP IMPROVEMENTS — scene budgets, gates, build cost, and rendering
T-1289 — Each merge into dev makes every other open PR dirty, so N pull requests cost N-squared lap-and-gate rounds
T-1287 — A split mints its children's ids from the local maximum, so two runs splitting one parent mint the SAME ids for DIFFERENT tickets and the parent's claim lock covers neither
T-1282 — The lap cannot re-derive a resident household card, so any PR that conflicts on hh_*.json is refused whole
T-1118 — A bake whose ref merged mid-run still spends the whole bake before the PR is withheld
T-0231 — T-0229's expiry was blocked on a flora ticket, so the raised ceilings would never have come down
T-0673 — The triangle-budget fork was never filed as a ticket, so the owner's answer had nothing to land against: record the ruling and spend it only where a breach is measured
T-0672 — The three ceilings were raised for one parcel on 2026-09-03 and light's floor was spent: re-measure once #432 lands and take every tier back down
T-0237 — The full ceiling has 1,145 triangles clear on the published mirror, twelve hours after T-0229 raised it
T-0438 — The letter-list cohort is 2.54 MiB of the published tree, and it is now the largest single item in it
T-0777 — assets/manifest.web.json's $note is rewritten with escaped em-dashes, so its own generator does not reproduce what dev committed
T-0776 — A full tools/web_derivatives.sh rewrites 348 derivatives with identical byte counts: the derivative step is not reproducible
T-0829 — A repeated string in a provenance or coverage list is the same merge artefact as a repeated id, and nothing asserts it
T-0239 — Nothing tests the party-line note's prose against the placement it describes
T-0253 — May an invented building stand on the river margin of a platted street corridor
T-0190 — A second street tier for the street edge, and the ceiling that refuses it
T-0252 — Decide once whether a baked town carries the nine renderer-drawn layers, or none of them
T-0285 — An asset carrying its own AO map cannot batch with the town: +2 draw calls for one building
T-0286 — The AO unwrap leaves 68.9 per cent of every atlas empty, and the map is priced as if it were full
T-0364 — Two byte-identical copies of changelog.js are 7.2 per cent of the published payload, and they grow on every release
T-0053 — A patched lit material silently inherits another layer's shader program
T-0371 — The lattice path's block rotation is dead code that measure_rank_bias.mjs's drift guard pins in place
T-0433 — T-0346's measured costs for the new desktop parts 4, 5 and 6 were never filed, and the two places they are written down disagree
T-0030 — A queue card in Manager reading tickets.json
# --- 9. RESEARCH COMPLETION — remaining readings, identity epics, and deposit closeout
T-1219 — The three re-spelled cards still say in prose that the papers print the reading T-1139 overturned: hh_fraser_wm_h reads 'Wm. H. Frazer' and its own note says the papers print 'Wm. H. Fraser'

# --- MERGED IN, NOT YET PLACED. These arrived on the branch being merged and were
# --- appended here rather than guessed into a band. Rank them or leave them.
T-1222 — Read the letter-list mint's 798-file drift and give the pass a check the gate can run at its own place in the pipeline
T-1281 — Is the Democrat's 'A. Sweet' of 4 June 1834 Alanson Sweet or the Alon[s]on Sweet of the same column
T-1294 — hh_inf_joiner_north_02 stands in the tree and no pass derives it: the register deal seats four roofs where its own docstring says five, and J. W. Reed's household is owned by nobody
T-1273 — Write every committed home and workplace reconciliation row as an associated_with row on the record it belongs to, changing no value, confidence or source
T-1274 — Move the renderers and tools off the singular lives_at/works_at once the plural rows carry every claim, and retire the pair
