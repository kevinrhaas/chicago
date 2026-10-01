# The licensed houses' horse-keeping, read against their beds (T-1776)

The second piece of T-1209. Its acceptance asks for "a stable, a yard or a stated absence for
each licensed house the lodging model sizes". The licensed houses are the `inn_tavern` class of
`data/reconstruction/1835_lodging_model.json`: nine named places. The twelve built boarding houses
of the other class are T-1779's, which raises each "with its stable and privy".

## The one fact everything here rests on

On 13 April 1831 the Cook County Court of County Commissioners, sitting at Chicago, granted the
county's first two tavern licences and "Ordered that the following rates be allowed to tavern
keepers", among them "For each horse fed 25" and "Keeping horse one night 50" (Andreas vol. 1,
scan p. 249, `andreas_1884_v1`). Keeping a traveller's horse overnight was a priced service of a
licensed Chicago house. That establishes the service. It does not establish a building. A horse
can be kept at a picket line, in a fenced lot or at a livery. No source reached mentions a stable
at any of these houses except the Western Hotel.

## The rule (reconstructed, L313)

- **Stalls:** one single standing stall per two ordinary-night guests, rounded up, never fewer
  than four. Half a horse per guest because the summer crowd of 1835 came mostly by lake.
- **Exceptions:** the Western Hotel keeps its own attested ratio ("the teams were as numerous as
  were the guests", `chicagology_prefire278`, T-1775). The Tremont gets one stall per guest
  because it was a stage stop (`chicagology_prefire021`).
- **Size:** 5 ft a stall. A single range is 20 ft deep; two ranges either side of an 8 ft
  passage are 28 ft deep, the Western stable's own section. Add a 6 ft harness and feed bay.
- **Place:** the placement policy's `ancillary_behind_its_own_roof` clause, at the alley end of
  the house's own lot, 1.5 m inside the alley line. Off the plat, behind the house on the side
  away from its front. Every site is checked against every committed footprint with 1 m
  clearance and against the modelled water.

## The ledger

| house | ordinary beds | stalls wanted | what stands | reading |
|---|---|---|---|---|
| Western Hotel | 15 | 16 (teams) | `western_hotel_stable` 22.0 x 8.5 m, wagon yard | **stable**, attested, re-sized by T-1775 |
| Wolf Point Tavern | 4 | 4 (floor) | `wolf_point_tavern_stable` 9.0 x 6.0 m, yard | **stable**, standing; holds 4-5, enough, unchanged |
| Tremont House (first) | 12 | 12 (stage stop) | `tremont_house_1_stable` 10.97 x 8.53 m | **stable**, new, alley end of blk_south_water_clark #07 |
| Exchange Coffee House | 11 | 6 | `exchange_coffee_house_stable` 10.97 x 6.10 m | **stable**, new, east half of the alley end of blk_south_water_franklin #07 |
| Steamboat Hotel | 11 | 6 | `steamboat_hotel_stable` 10.97 x 6.10 m | **stable**, new, behind the house off the plat, door to the house |
| New York House | 8 | 4 | `new_york_house_stable` 7.92 x 6.10 m | **stable**, new, west half of the alley end of blk_south_water_franklin #07 |
| Sauganash Hotel | 7 | 4 | `sauganash_hotel_stable` 7.92 x 6.10 m; `sauganash_yard` | **stable**, new, alley end of blk_lake_market #00, behind the yard the views show |
| Mansion House | 5 | 4 (floor) | `mansion_house_stable` 7.92 x 6.10 m | **stable**, new, alley end of blk_south_water_dearborn #01 |
| Green Tree Tavern | 8 | 4 | nothing | **stated absence** (below) |

**The Green Tree's absence is a fact about the model's ground, not about 1835.** The house stands
at the Canal and Lake corner with its back about 12 m from the modelled South Branch bank. A
four-stall range was placed behind it, between the back wall and the bank. The placement policy
read it 2.64 m inside Lake Street's corridor, and there is no room to move it north before the
water. Nothing says the Green Tree had no stable. It is not drawn because no honest site exists
on this ground at this size. Either of these would retire the absence: a reading that moves the
house or the bank, or a source that puts its stabling somewhere, such as the Western Hotel's
yard 190 m south-west.

## Also checked

- **Two houses share one lot.** The Exchange Coffee House and the New York House stand on the
  same Lake Street lot (blk_south_water_franklin #07). Each stable takes the half of the alley
  end nearer its own house, 1.5 m apart.
- **Two stables are outliers, each with a stated reason.** Every point of the Sauganash's corner
  lot is nearest a principal street (Market), so its stable carries an `OUTLIER_REASONS` entry
  in `tools/placement_policy_1835.py`. The Wolf Point stable already carried one.
- **The roof count.** Each stable is an A1 roof in
  `data/reconstruction/1835_existing_roof_reconciliation.json`. Like the Wolf Point and Western
  stables, it substitutes for one anonymous A1 slot in its district. It is never added above 665.
