# The 668-roof programme, re-derived against the order book

DERIVED. Written by `tools/reprogramme_roofs_1835.py --build`; re-derived by `--check` in `tools/check.sh`. Do not hand-edit.

Ticket T-1196. An adjudication over committed derived files — no page of any source was opened, nobody is named, nothing is built, and no roof moves ground.

## What moved

The specification schedules **668 roofs**; this re-derivation adopts **668** — no group moves.

The inventory's own defensible range is 565–765 roofs; the adopted total is inside it.

| Group | Spec | Model | Compared in | Adopted | Δ |
|---|---:|---:|---|---:|---:|
| `barns_stables` | 73 | — | not modelled | 73 | +0 |
| `fort_principal` | 10 | 10 | roofs against roofs | 10 | +0 |
| `inns_taverns` | 10 | 11 | roofs against printed notices | 10 | +0 |
| `institutional_public` | 9 | 9 | roofs outside the fort against roofs outside the fort | 9 | +0 |
| `larger_boarding_houses` | 42 | 42 | roofs against roofs | 42 | +0 |
| `ordinary_dwellings` | 335 | 335 | roofs against roofs | 335 | +0 |
| `small_outbuildings` | 85 | — | not modelled | 85 | +0 |
| `stores_mixed_use` | 53 | — | roofs against establishments | 53 | +0 |
| `warehouses_freight` | 20 | — | roofs against establishments | 20 | +0 |
| `workshops` | 31 | — | roofs against establishments | 31 | +0 |

## Why each group stands where it does

**`barns_stables`** — Ancillary. The town model carries no figure for yards and outbuildings and the order book orders none; the ratio to principal roofs is T-1212's to deal. The spec stands untouched.

**`fort_principal`** — The fort component of the model's institutional high end, and the same number. The compound is read from its dossiers, not apportioned.

**`inns_taverns`** — THE FOLD RAN AND THE GROUP MEETS THE TOWN EXACTLY (T-1471). The model's 11 is the business register's count of HOUSES at the scene date: 15 records folded to 11 by 4 one-house rulings in trade_class_rulings.json, which is where an identity ruling belongs and this tool still makes none of its own. One of those 11 is E. Wentworth's house on Flag Creek, eighteen miles south of Chicago on the Ottawa road — all five of its printings say so — and a house outside the plat is no roof inside it. That leaves 10 public houses in the town against the 10 this programme schedules: the two figures MEET, and the group is left exactly as it is. The layer stands at 9 of those 10, which is the schedule's own remaining build and not a disagreement about how many there should be.

**`institutional_public`** — The model's low end is the 9 roofs OUTSIDE the fort and its high end adds the 10 principal roofs INSIDE it. The programme schedules both — 9 institutional_public plus 10 fort_principal — so the two agree at 19. The order book's delta of ten is that high end read against one of the two groups.

**`larger_boarding_houses`** — The model reads this figure off district_group_matrix, so its agreement with the programme is the programme agreeing with itself. Recorded as circular rather than banked as corroboration; the group stands because nothing independent moves it.

**`ordinary_dwellings`** — The model's own low end IS this schedule. The order book's competing figure is 643 HOUSEHOLDS, which is a different unit: satisfying it with roofs would seat one family per roof, the error the town model exists to refuse. It is met by occupancy instead — see the dwellings reconciliation, where the rate the order book needs falls inside the band the November census brackets.

**`small_outbuildings`** — Ancillary. The town model carries no figure for yards and outbuildings and the order book orders none; the ratio to principal roofs is T-1212's to deal. The spec stands untouched.

**`stores_mixed_use`** — No model figure schedules this group on its own. The nearest comparandum is the 118–130 establishments the occupation model counts in the compared classes, against the 104 commercial, workshop and freight roofs the programme schedules together — more trades than roofs, which is the store-over-office and shop-house town these families already build. Nothing moves a single group off that.

**`warehouses_freight`** — No model figure schedules this group on its own. The nearest comparandum is the 118–130 establishments the occupation model counts in the compared classes, against the 104 commercial, workshop and freight roofs the programme schedules together — more trades than roofs, which is the store-over-office and shop-house town these families already build. Nothing moves a single group off that.

**`workshops`** — No model figure schedules this group on its own. The nearest comparandum is the 118–130 establishments the occupation model counts in the compared classes, against the 104 commercial, workshop and freight roofs the programme schedules together — more trades than roofs, which is the store-over-office and shop-house town these families already build. Nothing moves a single group off that.

## The census's 398 dwellings, reconciled

The order book orders more households than the programme schedules dwellings. How many households to a roof?

- Dwelling roofs on the scene date: **377** (335 ordinary dwellings, 42 larger houses and boarding houses).
- Households the order book orders: **643**.
- Households to a dwelling, adopted: **1.706**.
- The band the census brackets: **1.636–2.051** — 8.204 people per dwelling in the town census of November 1835, over the 1840 city's household size of 4.0–5.015 (median to mean).
- Inside the bracket: **yes**.

The census counted 398 dwellings in November 1835, four months after the scene, in the fastest-growing months the town had. A July programme of 377 dwelling roofs stands 5.3% below it, which is growth across that gap and not a hole in the schedule. The same date caution governs every class the trade-census crosswalk compares.

Source for the November figures: `andreas_1884_v1`.

## The crosswalk's count fields

Re-derived from `1835_building_inventory.json`'s `family_targets` and the crosswalk's own `priority_rule`. Authored content — archetypes, geometry bands, evidence and assumption notes — is untouched.

Target 668 roofs · 48 instantiated in phase 1 · 620 remaining.

| Rank | Family | Target | Phase 1 | Remaining | Band |
|---:|---|---:|---:|---:|---|
| 1 | `D4` | 75 | 7 | 68 | P0 |
| 2 | `D3` | 65 | 6 | 59 | P0 |
| 3 | `D5` | 58 | 5 | 53 | P0 |
| 4 | `D1` | 52 | 2 | 50 | P0 |
| 5 | `A1` | 42 | 1 | 41 | P1 |
| 6 | `A3` | 40 | 3 | 37 | P1 |
| 7 | `D2` | 38 | 2 | 36 | P1 |
| 8 | `A2` | 31 | 1 | 30 | P1 |
| 9 | `A4` | 28 | 2 | 26 | P1 |
| 10 | `D6` | 29 | 3 | 26 | P1 |
| 11 | `H1` | 18 | 0 | 18 | P2 |
| 12 | `D7` | 18 | 1 | 17 | P2 |
| 13 | `A5` | 17 | 1 | 16 | P2 |
| 14 | `C1` | 18 | 3 | 15 | P2 |
| 15 | `C3` | 17 | 3 | 14 | P2 |
| 16 | `H2` | 14 | 0 | 14 | P2 |
| 17 | `C2` | 13 | 2 | 11 | P2 |
| 18 | `H3` | 10 | 0 | 10 | P2 |
| 19 | `M1` | 10 | 0 | 10 | P2 |
| 20 | `F1` | 8 | 1 | 7 | P3 |
| 21 | `W2` | 8 | 1 | 7 | P3 |
| 22 | `F2` | 7 | 1 | 6 | P3 |
| 23 | `T1` | 6 | 0 | 6 | P3 |
| 24 | `W4` | 7 | 1 | 6 | P3 |
| 25 | `C4` | 5 | 0 | 5 | P3 |
| 26 | `W1` | 6 | 1 | 5 | P3 |
| 27 | `W3` | 6 | 1 | 5 | P3 |
| 28 | `I1` | 4 | 0 | 4 | P4 |
| 29 | `W5` | 4 | 0 | 4 | P4 |
| 30 | `F3` | 3 | 0 | 3 | P4 |
| 31 | `I3` | 3 | 0 | 3 | P4 |
| 32 | `T2` | 3 | 0 | 3 | P4 |
| 33 | `F4` | 2 | 0 | 2 | P4 |
| 34 | `I2` | 2 | 0 | 2 | P4 |
| 35 | `T3` | 1 | 0 | 1 | P4 |

## Deltas this re-derivation does not act on

**`inns_and_taverns`** → SETTLED by T-1471. THE IDENTITY QUESTION IS ANSWERED AND THE GROUP IS LEFT ALONE. It was asked as: the register holds 15 tavern records at the scene date and folds none of them — are they that many HOUSES? They are not. 4 of them are re-settings of two standing advertisements, ruled one house apiece in trade_class_rulings.json with the printed copy beside each ruling. Five settings of E. Wentworth's Flag Creek notice — the same four sentences every time, signing themselves 'Dec. 17, 1833' a year after that date — had raised four businesses; three settings of the Eagle Tavern's chair-and-harness notice — signing themselves 'June 11, 1834' and differing only in the keeper's middle initial — had raised two. So 15 records are 11 houses, and the delta against 10 scheduled roofs falls from 5 to 1. AND THE LAST ONE IS NOT IN THE TOWN. E. Wentworth's house stood eighteen miles south of Chicago on the Ottawa road, which all five of its printings state and which no roof inside the plat can be. The town's own figure is therefore 10 public houses against the 10 this programme schedules: they MEET, and there is nothing left to re-cut. THE REMAINDER RECONCILES TOO, which is the check on that. Six of the town's ten records already sit on a standing public house (Couch on the Tremont, Davis on the Steamboat, Murphy on the Exchange, Stow on the Western, Walters on Wolf Point, Ingersoll on the Green Tree). Three standing houses carry no register record at all — the Sauganash, the Mansion House and the New York House — and the schedule has one roof still to raise (10 scheduled against the layer's nine standing). Three unlinked houses plus one unbuilt roof is four, and four is exactly the number of town records with no house yet: Beaubien, Sweet, the Eagle Tavern and the Traveller's Home. Linking a keeper to the house he kept is a person-to-house ruling and is not made here. WHAT IS STILL OPEN, and named rather than ruled: the register's 'Eagle Hotel' (Cable and Shrigley) and 'Eagle Tavern' (Carli) trade in the same months under the same bird. That pair sits in trade_class_rulings.json's `register_cautions` and cannot move this count either way — the Eagle Hotel is already excluded from the scene date as contradicted before it.

**`institutional_and_public`** → T-1196. The false delta of ten is GONE (T-1439, 2026-09-21): build_order_book_1835.programme_deltas now sums institutional_public and fort_principal on its programme side, which is where the model's high end already had them, and the two files read 19 against 19. What is still owed is a COUNT: both ends of the model's figure are read off district_group_matrix, so the corrected zero is a restatement and the book prints it as one. Nothing outside the roof programme has said how many institutional and public roofs the town had.

**`boarding_houses`** → T-1196. model_town_1835.build_lodging takes larger_boarding_houses straight off district_group_matrix, so that figure can never disagree with the programme and the order book's delta of zero is a tautology. A figure that cannot fail is not a check on 42 roofs. The book stopped printing it as a pass with T-1439 and marks the row NOT A CHECK; an independent count of the town's boarding houses is still owed to the re-cut.
