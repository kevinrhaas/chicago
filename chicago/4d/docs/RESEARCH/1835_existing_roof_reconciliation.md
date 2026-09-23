# July 1835 existing-roof reconciliation

**Status:** production accounting audit, 2026-08-12  
**Covers:** all 76 committed `data/structures/*.json` records whose IDs do not begin `recon_`  
**Machine-readable ledger:** `data/reconstruction/1835_existing_roof_reconciliation.json`

## Decision

The 76 historical records are not 76 roofs. They include bridges, piers, a stockade,
open grounds, an open livestock pen, two July-incomplete construction sites, grouped
cabins, and buildings with attached roof ranges. The audit therefore keeps three
different ideas separate:

1. **Physical roof masses** describe what a close model may eventually need to draw.
2. **Inventory roofs** are the roofed-building units deducted from the 665-roof July
   programme.
3. **Records** preserve evidence and are never treated as a count by themselves.

An attached range does not become another anonymous town building merely because it
has its own ridge. Thus the Sauganash's log wing, the Mansion House addition, the Miller
House frame front, the Wolf Point Tavern addition, the Western Hotel's intersecting
ranges, and the compound Agency House each consume one inventory slot. Separate cabins
consume separate slots.

## Result

| District | Covered records | Eligible records | Eligible inventory roofs |
|---|---:|---:|---:|
| South | 35 | 30 | 30 |
| West | 12 | 11 | 12–13 |
| North | 16 | 13 | 14 |
| Fort | 13 | 10 | 10 |
| **Total** | **76** | **64** | **66–67** |

The physical modelling obligation is **73–78 roof masses**, because several eligible
buildings are compound. The programme-accounting deduction is **66–67 roofs**. The
one-roof uncertainty is Wau-Bun's explicitly loose count of “two or three” Robinson and
Caldwell cabins. Keeping the range is more honest than resolving a number the witness
did not resolve.

The Fort reconciles exactly to the specification's ten principal roofs: artillery
house, barracks, blockhouse, commandant's quarters, guard house, magazine, officers'
quarters, root house, store house, and sutler's store. The palisade, parade, and garden
consume no roof slots.

## Zero-roof records

Twelve records consume no inventory roof:

- four open crossings: Dearborn drawbridge, North Branch bridge, South Branch bridge,
  and the Water Street slough logs;
- two open harbour works: North Pier and South Pier;
- three open Fort elements: stockade, parade, and garrison garden;
- the estray pen, an open pound whose current rendered roof is explicitly a generator
  limitation rather than evidence;
- the first courthouse, whose construction belongs after July under the adopted
  chronology; and
- the Lake House construction site, which may show works but not a completed roof.

These records stay in the research dataset and may stay visible where chronologically
appropriate. “Zero” means only that they do not consume one of the 665 roof slots.

## Compound and grouped records

| Record | Physical roofs | Inventory roofs | Reason |
|---|---:|---:|---|
| Clybourn cabins | 2 | 2 | Two separately stated cabins; current geometry shows only one. |
| Robinson/Caldwell cabins | 2–3 | 2–3 | The source itself says “two or three.” |
| Cobweb Castle / Agency House | 3–5 | 1 | Centre, two wings, and two tails form one compound house. |
| Green Tree Tavern | 1–3 | 1 | Core certain; two low wings are documented only later. |
| Mansion House | 2 | 1 | Log core plus documented frame front. |
| Miller House | 2 | 1 | Log cabin plus documented two-story frame range. |
| Sauganash Hotel | 2 | 1 | Frame block plus likely surviving attached log wing. |
| Western Hotel | 2 | 1 | One L-plan hotel under intersecting gable ranges. |
| Wolf Point Tavern | 2 | 1 | One partly-log, partly-frame public house. |

## Substitution rule

Every eligible `inventory_roof_count` in the ledger is an explicit substitution for an
anonymous slot of the named district and likely family. It is not an addition above the
665 target. The family labels are production mappings, not claims that a historical
source used the reconstruction specification's modern taxonomy. Where a committed
record's existence or July survival is weak, the ledger says so rather than deleting it.

This produces the next programme baseline:

- named/existing roofs to reserve: **66–67**;
- anonymous roofs still required: **598–599**;
- Fort anonymous roofs still required: **0**;
- district subtraction must use the ledger, not the count of JSON records.

## Validation

The ledger was compared to the structure directory by ID: **76 records, 76 unique IDs,
no omissions and no extras**. District totals sum to 76 records and eligible inventory
totals sum to 66–67. Any added non-`recon_` structure should make this audit fail until it
is classified explicitly.
