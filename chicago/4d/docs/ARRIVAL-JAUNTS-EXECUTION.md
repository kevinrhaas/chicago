# Arrival and jaunts — execution plan

Owner-directed ticket plan, 17 September 2026, **reviewed and re-cut the same day on the
owner's second instruction** ("review the queue and the overall project … make these tickets
very detailed and clear for execution so it all comes together in the end"). Planning is
complete; implementation is queued. The owner approved **summer 1835** wording; the scene
date stays 1835-07-01.

[Architecture and shared contracts §A–§H](ARRIVAL-JAUNTS-ARCHITECTURE.md) ·
[25 content briefs](JAUNTS-INITIAL-LIBRARY.md) · [Queue](../tickets/QUEUE.md) ·
authoring guide `docs/JAUNTS-AUTHORING.md` (written by T-1253)

## Where this work sits, and how to take a ticket

The five subsections sit after reconstruction convergence (T-1215) and immediately before
South Through Time. Inside each subsection the queue is **dependency order**: every ticket
names its predecessors under **Depends on**; take the topmost ticket whose predecessors are
all `done`, and skip one whose predecessor is still `open`/`claimed` (state the skip in the
PR). Tickets marked *(opener)* have no predecessor and may be taken by different agents at
once. Shared engine and compiler contracts land before the content batches; a content batch
owns only its own JSON files and never changes engine behaviour to fit a story.

Every ticket is one run (`M`, or `S` for T-1292). Each states what exists today with real
symbols, what to build, a numbered acceptance clause with the command or measurement that
demonstrates it, the harness ids and budgets it must keep (§F), and what is out of scope.
Finish each subsection; if a genuine remaining piece cannot fit, insert one focused
successor `--after` its dependency inside the band, update this matrix, and keep the
subsection below 15 tickets. Never send unfinished work to the queue tail and never close
an incomplete ticket. Claims, sizing, provenance, preflight and the dev-only merge workflow
remain in force.

## Lanes — what can run at the same time

```
5F  T-1246 boot phases ──► T-1247 arrival ──► T-1275 statuses
    T-1292 city topic ─────────────┐              ▲
    T-1248 source index ──► T-1276 sources ───────┘ (T-1275 needs T-1247 + T-1248)
    T-1277 destinations ──┐
                          ├──► T-1278 welcome  (needs T-1247, T-1292, T-1277)
5G  T-1253 jaunt contract (opener; parallel with 5F)
    T-1279 engine + navigation (needs T-1253, T-1277, T-1278)
      ├─► T-1280 travel modes ─┐
      └─► T-1256 mechanics ────┼─► T-1257 context (needs T-1279, T-1280, T-1276)
                               └─► T-1258 daybook (needs T-1256, T-1257)
    T-1259 menu (needs T-1279, T-1280, T-1258, T-1278)
5H  six priority jaunts — parallel, content only (need T-1259, T-1256, T-1257, T-1258)
5I  five batches of everyday jaunts — parallel, content only (same predecessors)
5J  T-1271 library convergence (needs all of 5H + 5I) ──► T-1272 published acceptance
```

Five agents can start today: T-1246, T-1292, T-1248, T-1277 and T-1253.

## 5F. Arrival and sources — measured loading, time rollback, source library, city summary, free start (8 tickets)

| Ticket | Bounded delivery | Depends on |
|---|---|---|
| [T-1246](../tickets/T-1246-expose-real-boot-phases-and-yield-long-scene-bui.md) *(opener)* | `api.boot` phase events, measured `boot-weights.js`, time-sliced flora phase, essential/optional readiness | — |
| [T-1292](../tickets/T-1292-move-the-town-census-off-the-loader-into-an-evid.md) *(opener, S)* | The gate census moves to Evidence → City; part-1 smoke checks relocated | — |
| [T-1248](../tickets/T-1248-compile-the-sources-used-and-their-reconstructio.md) *(opener)* | `compile_source_use.py` → `sidecars/1835/sources/` index + per-source edges, coverage report, tests | — |
| [T-1277](../tickets/T-1277-share-one-destination-search-for-go-to-and-explo.md) *(opener)* | `destinations.js` shared by Go to and the start picker; derived business rows; spawn-at-destination | — |
| [T-1247](../tickets/T-1247-roll-the-year-back-into-a-restrained-time-machin.md) | `arrival.js`: split-flap year paced by §A, restrained instrument style, error/retry, a11y | T-1246 |
| [T-1276](../tickets/T-1276-move-city-statistics-into-a-browsable-sources-an.md) | Evidence → Sources: searchable, filtered, windowed list; counts; used-for link library | T-1248, T-1292 |
| [T-1275](../tickets/T-1275-give-the-loading-journey-160-varied-source-and-r.md) | `data/loading/statuses.json` (≥160), `loading-content.js` bags, content validator | T-1247, T-1248 |
| [T-1278](../tickets/T-1278-land-on-a-warm-mobile-welcome-with-jaunts-and-ex.md) | The welcome: Jaunts · Explore Myself · Enter Chicago; no pointer lock on menus; Start route back | T-1247, T-1292, T-1277 |

## 5G. Jaunts engine — content contract, navigation, travel, mechanics, history, daybook, menu (7 tickets)

| Ticket | Bounded delivery | Depends on |
|---|---|---|
| [T-1253](../tickets/T-1253-define-validated-jaunt-json-and-render-a-real-pi.md) *(opener)* | `schema.json`, `compile_jaunts.py`, catalog, the `new-in-chicago` pilot file, fixtures, `docs/JAUNTS-AUTHORING.md` | — (T-1248 if landed) |
| [T-1279](../tickets/T-1279-make-the-pilot-jaunt-playable-with-persistent-st.md) | `jaunts.js` reducer + `jaunt-panel.js`; Previous / Next / End / Menu; pilot played end to end | T-1253, T-1277, T-1278 |
| [T-1280](../tickets/T-1280-offer-live-jaunt-travel-modes-and-honest-quick-p.md) | `travel-estimate.js`; per-jaunt mode, mid-leg switch that re-plans; Go straight to next stop | T-1279 |
| [T-1256](../tickets/T-1256-support-bounded-choices-inventory-and-alternate-.md) | Declared, bounded, once-only mechanics; Revise choice; endings; session resume | T-1279 |
| [T-1257](../tickets/T-1257-connect-jaunt-stops-and-travel-to-optional-histo.md) | Typed card links with exact return; route-aware leg notes ("passing …"); provenance chips | T-1279, T-1280, T-1276 |
| [T-1258](../tickets/T-1258-collect-era-themed-keepsakes-in-a-five-family-ch.md) | `daybook.json` five families + ranks; `jaunt-journal.js`; outcome card; reset | T-1256, T-1257 |
| [T-1259](../tickets/T-1259-finish-the-scalable-jaunts-menu-and-integrated-s.md) | `jaunt-menu.js`: six-field cards, featured row, search/pills, windowing, resume strip | T-1279, T-1280, T-1258, T-1278 |

## 5H. Priority jaunts — six short stories, fully authored and playable (6 tickets, parallel)

All need T-1259, T-1256, T-1257, T-1258. Each ticket carries its stops, mechanics, cautions and
the per-stop authoring checklist; content only.

| Ticket | Jaunt | Mode · keepsake |
|---|---|---|
| [T-1260](../tickets/T-1260-publish-outfit-for-the-west-as-a-five-minute-jau.md) | Outfit for the West | Wagon · Ready for the Road (Provisions) |
| [T-1261](../tickets/T-1261-publish-taverns-of-chicago-as-a-five-minute-jaun.md) | Taverns of Chicago | Horse · A Sensible Evening (Neighbors) |
| [T-1262](../tickets/T-1262-publish-new-in-chicago-as-a-five-minute-jaunt.md) | New in Chicago (finishes the T-1253 pilot in place) | Walk · Finding Your Feet (Wayfinding) |
| [T-1263](../tickets/T-1263-publish-shopping-south-water-street-as-a-five-mi.md) | Shopping South Water Street | Walk · The Household List (Provisions) |
| [T-1264](../tickets/T-1264-publish-across-wolf-point-as-a-five-minute-jaunt.md) | Across Wolf Point | Walk · Knows the Crossing (Wayfinding) |
| [T-1265](../tickets/T-1265-publish-fort-dearborn-errand-as-a-five-minute-ja.md) | Fort Dearborn Errand | Walk · Accounted for at the Fort (Livelihood) |

## 5I. Everyday jaunts — nineteen additional outings in five bounded content batches (5 tickets, parallel)

Same predecessors as 5H. Each batch names its quiet outing (no declared resource).

| Ticket | Jaunts |
|---|---|
| [T-1266](../tickets/T-1266-publish-news-mail-lodging-and-work-jaunts.md) | news-before-breakfast · letter-home · bed-for-the-night (quiet) · work-on-waterfront |
| [T-1267](../tickets/T-1267-publish-land-freight-household-supplies-and-clot.md) | inspect-a-lot · freight-for-the-store · household-provisions · a-decent-coat (quiet) |
| [T-1268](../tickets/T-1268-publish-harness-candles-building-materials-and-l.md) | mend-the-harness · soap-and-candles (quiet) · materials-for-a-roof · boots-and-leather |
| [T-1269](../tickets/T-1269-publish-schooling-social-visits-and-careful-news.md) | schoolday-errand · sunday-circuit (quiet) · calling-on-neighbors · gossip-or-notice |
| [T-1270](../tickets/T-1270-publish-harbor-prairie-arrival-and-a-quiet-strol.md) | along-the-harbor · from-prairie-to-town · an-evening-stroll (quiet) |

## 5J. Arrival and jaunts complete — content convergence and published mobile acceptance (2 tickets)

| Ticket | Bounded delivery | Depends on |
|---|---|---|
| [T-1271](../tickets/T-1271-reconcile-and-time-the-complete-25-jaunt-library.md) | `play_jaunt.mjs --all`, `audit_jaunts.py` in the gate, all 25 measured and corrected, 26th-by-JSON proof, report | all of 5H and 5I |
| [T-1272](../tickets/T-1272-verify-arrival-jaunts-and-source-browsing-on-the.md) | A priced smoke part for the whole path at both viewports; boot variants; layouts; budgets; report | T-1271, T-1275, T-1276, T-1278, T-1259 |

## Requirements accounted for

| Owner requirement | Tickets / proof |
|---|---|
| Loader knows how long each section takes and should take; year rolls back smoothly and lands on 1835 exactly at readiness | T-1246 (`boot-weights.js`, phase events), T-1247 (§A pacing, ≤300 ms settle) |
| Welcome explains a digital reconstruction of 1835; statuses show sources ("Assessing newspapers… Chicago Democrat"), flip cards, facts, assess→collect→prepare→resolve→land arc, 100–few-hundred entries, rare humour incl. "reticulating splines" | T-1247 (card slot, copy), T-1275 (≥160 entries, phase arc, 1 % humour), T-1248 (facts trace to real sources) |
| Gently steampunk, retro-60s time-machine feel, not cutesy | T-1247 (restrained instrument style, `--brass` token, no gears/sound) |
| Fast load shows only a couple of statuses; long prairie phase keeps repainting | T-1246 (time-slicing), T-1275 (dwell scaled to expected phase length) |
| Land on the Jaunts / Explore Myself page; "Tap to enter", not "Tap to walk"; mobile fits | T-1278, T-1259, T-1272 |
| Counts and percentages off the opening screen, into a city summary tab | T-1292 (Evidence → City) |
| All sources used, easy to consume, with attested/inferred/reconstructed counts and a used-for link library | T-1248 (index), T-1276 (browser) |
| Explore Myself: search structure / business / resident place / street & intersection, then free exploration; not a duplicate of Go to | T-1277 (one `destinations.js`, derived business rows), T-1278 |
| Recommended travel mode per jaunt, changeable on the card and mid-jaunt; duration follows the mode | T-1280, T-1259 |
| Sites along the way and the story between stops; deeper cards without slowing the jaunt | T-1257 (route-aware leg notes, typed links with exact return) |
| Persistent Previous / Next / End / Jaunts Menu; End returns to the menu immediately | T-1279 |
| Menu shows title, premise, stops, duration, category, travel mode; 25 → 50+ by data | T-1253 (catalog), T-1259 (windowing, 55-item fixture), T-1271 (26th by JSON) |
| Optional mechanics, alternate endings, matched to the subject | T-1256, the quiet outing per batch |
| 3–5 collection systems, level up across categories, modern low-pressure gameplay | T-1258 (five families, four ranks, no streaks/leaderboards) |
| Six priority jaunts; ~25 varied everyday outings; provenance model preserved | 5H, 5I, T-1271 (audit in the gate) |
| About five minutes, 4–8 stops, measured | T-1280 (estimate), T-1271 (measured paths) |
| Published mobile and desktop, slow/fast/failed boots, reduced motion, budgets | T-1272 |

## Planning validation and implementation handoff

All 42 proposed stop ids were re-verified against `data/structures/` and
`data/sidecars/1835/index.json` on 2026-09-17 (second pass); every one resolves, none is
`review_required`, and positions are `inferred` or `reconstructed` throughout — the
library's per-stop table records which, so a stop's text never claims a placed front door.
The anchor `lake_shore_south` resolves in `data/scenes/1835.json`. These remain **content
briefs**: each content ticket verifies the claim and locator it uses when it authors the stop.
Known traps stay called out: the future court-house is excluded, the Lake House is under
construction, Hogan's mail role is historical, and fort service functions and access must
not be silently strengthened.

No new geometry and no human figures are required by this plan. A missing number is handled
at the reconstructed tier with a liberty, never a new epic. Code checks on this planning
change do not validate a future runtime; T-1272 owns that evidence after implementation.
