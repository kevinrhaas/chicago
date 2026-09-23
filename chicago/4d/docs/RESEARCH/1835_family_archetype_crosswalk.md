# July 1835 family-to-archetype production crosswalk

## Status and limits

**THE TOTAL MOVED 665 → 662 on 2026-08-27 (ticket T-0032).** Three of family I3's six civic
slots were shown to count nothing — the town's public buildings with a roof on 1835-07-01 are
three named records — so I3 goes 6 → 3 and the total with it. No other family target changed.
See `docs/RESEARCH/civic_public_buildings_1835.md` § 6a.

This crosswalk turns the 35-family, 662-roof production schedule into an implementable
geometry backlog. Its source is the owner-supplied *Chicago · July 1835: Building Inventory
and Architectural Reconstruction Specification*, recorded as
`owner_chicago_1835_reconstruction_spec_2026`. That modern synthesis supports aggregate family
counts, dimensional bands and type-level variation. It does **not** document any anonymous
building, parcel, occupant, finish or detail.

“Current” below means the least-wrong generator available today, not a claim that it is a
finished representation. “Canonical” is the required production family and variant. Existing
named records remain protected: a named or better-documented roof substitutes for an anonymous
slot instead of increasing the authored total.

## Count and priority control

The family targets independently sum to the programme total. Phase 1 has instantiated 48
anonymous South Division roofs, leaving 614. Reviewed but unrendered phase-2 recipes are not
subtracted. The backlog is ordered by remaining roof count:

- **P0:** 50 or more remaining
- **P1:** 25–49
- **P2:** 10–24
- **P3:** 5–9
- **P4:** 1–4

| Family | Target | Phase 1 | Remaining | Rank | Priority |
|---|---:|---:|---:|---:|---|
| D1 | 52 | 2 | 50 | 4 | P0 |
| D2 | 38 | 2 | 36 | 7 | P1 |
| D3 | 65 | 6 | 59 | 2 | P0 |
| D4 | 75 | 7 | 68 | 1 | P0 |
| D5 | 58 | 5 | 53 | 3 | P0 |
| D6 | 29 | 3 | 26 | 10 | P1 |
| D7 | 18 | 1 | 17 | 12 | P2 |
| H1 | 18 | 0 | 18 | 11 | P2 |
| H2 | 14 | 0 | 14 | 15 | P2 |
| H3 | 10 | 0 | 10 | 18 | P2 |
| C1 | 18 | 3 | 15 | 13 | P2 |
| C2 | 12 | 2 | 10 | 17 | P2 |
| C3 | 17 | 3 | 14 | 14 | P2 |
| C4 | 5 | 0 | 5 | 25 | P3 |
| T1 | 6 | 0 | 6 | 24 | P3 |
| T2 | 3 | 0 | 3 | 32 | P4 |
| T3 | 1 | 0 | 1 | 35 | P4 |
| W1 | 6 | 1 | 5 | 26 | P3 |
| W2 | 8 | 1 | 7 | 21 | P3 |
| W3 | 6 | 1 | 5 | 27 | P3 |
| W4 | 6 | 1 | 5 | 28 | P3 |
| W5 | 4 | 0 | 4 | 30 | P4 |
| F1 | 8 | 1 | 7 | 20 | P3 |
| F2 | 7 | 1 | 6 | 22 | P3 |
| F3 | 3 | 0 | 3 | 31 | P4 |
| F4 | 2 | 0 | 2 | 33 | P4 |
| I1 | 4 | 0 | 4 | 29 | P4 |
| I2 | 2 | 0 | 2 | 34 | P4 |
| I3 | 3 | 0 | 3 | 23 | P4 |
| M1 | 10 | 0 | 10 | 19 | P2 |
| A1 | 42 | 1 | 41 | 5 | P1 |
| A2 | 30 | 1 | 29 | 8 | P1 |
| A3 | 40 | 3 | 37 | 6 | P1 |
| A4 | 28 | 2 | 26 | 9 | P1 |
| A5 | 14 | 1 | 13 | 16 | P2 |
| **Total** | **662** | **48** | **614** |  |  |

## Production crosswalk

The compact table identifies the implementation gap. Exact dimensional bands and parameter
notes are machine-readable in `data/reconstruction/1835_family_archetype_crosswalk.json`.

| Family | Current placeholder | Required canonical variant | Key production gap | Evidence / assumption guardrail |
|---|---|---|---|---|
| D1 | `log_dwelling` | `dwelling_log:cabin_older` | 1 + loft; side/front gable; external chimney; optional shed addition | Current log vocabulary is close. Orientation, chimney and addition remain per-slot conjecture. |
| D2 | `outbuilding` | `dwelling_plank:shanty_rough` | Add habitable windows, hearth/entry and repaired-board variants to rough shed/gable shell | Dwelling versus temporary shanty is interpretive; never invent an occupant. |
| D3 | `frame_dwelling` | `dwelling_frame:single_room_cottage` | Lock one-storey single-pen, 2/3-bay, side-chimney and stoop variants | Type is well covered; framing, gable direction, bays and finish remain controlled variation. |
| D4 | `frame_dwelling` | `dwelling_frame:two_room_cottage` | Side-gable hall/parlour, 3/5 bays, center/side door and rear lean-to | Room plan and lean-to are family options, not recovered parcel facts. |
| D5 | `frame_dwelling` | `dwelling_frame:deep_plan_gable_front` | Current eaves-front compression must become a defining deep-plan front-gable silhouette | Shop-room use cannot be inferred from depth alone. |
| D6 | `frame_dwelling` | `dwelling_frame:cottage_one_and_half` | True knee-wall/steep-roof profile, explicit orientation, sparse tiny dormers and rear ell | Dormers and ell are optional, not defaults. |
| D7 | `frame_dwelling` | `dwelling_frame:house_two_story_restrained` | Two-storey 3/5-bay set with restrained Federal/Greek doorway and trim | Style remains a restrained family-level treatment, never an anonymous attribution. |
| H1 | `frame_dwelling` | `house_frame_large:center_hall_one_and_half` | Larger scale, 5-bay center hall, kitchen ell and small porch | Paint/prosperity and service additions are aggregate signals only. |
| H2 | `frame_dwelling` | `house_frame_large:merchant_two_story` | Hip-roof option, Greek doorway, corner boards and 1/2 chimneys | “Merchant/professional” is a type label, not an identified resident. |
| H3 | `frame_tavern` | `boarding_house_frame:service_wing_two_story` | Remove tavern cues; add 6–10 upper-window rhythms, service wing and varied stovepipes | Window/stovepipe counts indicate capacity without asserting an interior plan. |
| C1 | `frame_storefront` | `storefront_frame:small_shop_one_story` | One-storey front-gable/shed shop, split door, modest panes and sign socket | Never invent business, sign text or goods for an anonymous slot. |
| C2 | `frame_storefront` | `storefront_frame:store_residence_one_and_half` | Replace current one-storey-plus-loft compression with a true attic-room silhouette | Residence, lean-to and signboard remain selectable family options. |
| C3 | `frame_storefront` | `storefront_frame:narrow_store_two_story` | Explicit gable direction, 2/3 shop bays, optional hoist beam/upper freight door | Hoist and lodging are variants, not consequences of height. |
| C4 | `frame_storefront` | `storefront_frame:wide_mixed_block_two_story` | Hip option, 4–6-bay shared composition and plain cornice | Timber is default; rare brick requires separate direct evidence. |
| T1 | `frame_tavern` | `tavern_frontier:neighborhood_public_house` | Lower 1.5/2-storey scale, bar-room entry and limited stable-yard/sign sockets | Sign, yard and log/frame mix are per-slot conjectures. |
| T2 | `frame_tavern` | `tavern_frontier:inn_two_story` | 5–8 bays, hip option, rear kitchen and limited porch | A substantial detached stable consumes an A-family slot; do not add it silently. |
| T3 | `frame_tavern` | `landmark_sauganash_inn:documentary_composite` | Custom documentary log-core/frame-addition composite | Reconcile the one slot to the protected named record; never generate an anonymous T3. |
| W1 | `outbuilding` | `workshop_frontier:blacksmith_forge` | Forge chimney, wide heat-safe opening, soot zones and detached-shop set | Tools, forge position and soot remain conjectural; no invented smith. |
| W2 | `outbuilding` | `workshop_frontier:carpenter_joiner` | Workshop daylight/openings, wide doors, optional loft and prop sockets | Lumber racks and sawdust are use cues rather than a specific job. |
| W3 | `outbuilding` | `workshop_frontier:cooper_wagon_wheelwright` | Double doors, facade work opening and audited hoops/wheels/barrel sockets | Shared visual family must not assert one individual trade. |
| W4 | `outbuilding` | `workshop_frontier:artisan_shop_house` | Add two-storey shop-house and dwelling/storefront opening variants | Trade differences should remain subtle without named evidence. |
| W5 | `outbuilding` | `workshop_riverside:heavy_open_work_bay` | Heavy frame, open river-facing work apron and rare lifting-gear socket | Crane is never default; bank access requires validated dry terrain. |
| F1 | `outbuilding` | `warehouse_frontier:freight_shed_low` | Long-frame bays, cargo openings and terrain-following skids/apron | Cargo and dock relationship remain unknown per anonymous slot. |
| F2 | `frame_storefront` | `warehouse_frontier:warehouse_narrow_two_story` | Remove retail facade; add sparse glazing, upper freight doors and optional hoist | Hoist and cargo type are not automatic. |
| F3 | `frame_storefront` | `warehouse_frontier:warehouse_river_large` | New heavy-frame broad-span shell with multiple cargo doors and landing apron | Apron must follow access and may not intrude into water or duplicate a pier. |
| F4 | `outbuilding` | `warehouse_frontier:lumber_shed_open` | Long-bay open posts, large-roof LOD and nonstructural lumber stacks | Stack quantity and open-side pattern are visual variation only. |
| I1 | `frame_dwelling` | `institution_landmark:worship_meeting_custom_set` | Four separate named custom assets, not a generic church family | Each slot requires named-institution reconciliation and its own dossier. |
| I2 | `log_dwelling` | `institution_vernacular:school_community_reused` | Alternate log/frame fabric and meeting-room window rhythm | Reuse and sign require named-record reconciliation for both slots. |
| I3 | `fort_structure` | `institution_civic:adapted_public_service_set` | Separate blockhouse/jail, service and adapted-office variants | Unlike functions cannot share an invented construction; rare brick needs support. |
| M1 | `fort_structure` | `fort_dearborn_compound:ten_principal_roofs_1835` | Reconcile a controlled ten-roof compound; keep stockade/flagstaff separate | Bind slots to physical roofs in protected fort records; props consume no roof slots. |
| A1 | `outbuilding` | `outbuilding_agricultural:stable_lofted` | Stable doors, hay opening, ventilation and wear-mask variation | Require `yard_group`; never infer animals or manure location. |
| A2 | `outbuilding` | `outbuilding_agricultural:barn_carriage_lofted` | Heavy-frame scale, drive-through pairing, loft door and optional lean-to | Barn/carriage use and door axis remain yard-specific conjectures. |
| A3 | `outbuilding` | `outbuilding_utility:privy_small` | Small-scale tolerances and controlled lean without breaking ground contact | Placement and lean are production rules; household ownership is unknown. |
| A4 | `outbuilding` | `outbuilding_utility:woodshed_storage` | Audited open/closed-side, stacked-wood and patch-roof variants | Open side and contents should follow yard access, not random display. |
| A5 | `outbuilding` | `outbuilding_utility:small_utility_mixed` | Mutually exclusive smokehouse/chicken/utility detail sets | Rare brick, vent, soot and fenced run must be conservative and never all combined. |

## Recommended build order

1. Build the four P0 dwelling families D4, D3, D5 and D1. Together they cover 230 of the
   remaining roofs and determine most of the town's visual fabric.
2. Complete P1 with a shared agricultural/utility outbuilding system (A1–A4) plus D2 and D6.
   These families cover another 221 remaining roofs and remove the most visible placeholder
   repetition.
3. Add P2 domestic, commercial and fort variants. Reconcile T3, I1–I3 and M1 to protected
   named/compound roofs before generation.
4. Finish P3/P4 work, freight and landmark variants. Low count does not mean low research
   importance: T3 and the institutional families are custom evidence work, not generic infill.

Every family implementation must sample the same visible terrain surface used for walking and
vegetation, expose explicit roof orientation, carry finish/age/condition variation, and retain
the existing provenance and anonymous-reconstruction labels.
