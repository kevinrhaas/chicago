# Did a deep-plan gable-front cottage stand in Chicago on 1 July 1835?

**Record:** none — this memo settles a FORM, not a building ·
**Data:** `data/reconstruction/1835_family_archetype_crosswalk.json` (family D5) ·
**Sources:** `andreas_1884_v1`, `chicagology_prefire127`, `drloih_hotels`,
`drloih_wolf_point`, `thompson_plat_1830`, and the 2026-08-11 reference plates (T-0083) ·
**Gate:** `tools/measure_band_claims.py` (the band ratchet), `tools/check.sh` ·
**Ticket:** T-1497

---

## 1. The question, and why it had to be asked before anything was built

The crosswalk authors family **D5 — "Deep-plan frame cottage", 58 roofs** — with
`roof: "front gable, 7:12-10:12"` and `variants: "narrow urban plan; side entry"`. It
names a canonical archetype, `dwelling_frame`, and a required variant,
`deep_plan_gable_front`. Neither exists. No file in `generators/archetypes/` is called
`dwelling_frame` and, before T-1497, no ticket had ever named it.

The archetype that does exist — `frame_dwelling` — refuses exactly this shape, in terms:

> The eaves-front house is the 1835 form; the gable-front house, turned end-on to the
> street, is the Greek Revival habit that arrives with the Clarke House in 1836 and
> dominates the 1840s.

So two committed documents contradict each other, and both are sourced. **Building the
archetype first would have answered the question by assuming it**, which is why T-1497's
acceptance put the reading ahead of the modelling and said in as many words that a
negative answer is a legitimate close.

## 2. The form existed here before 1835 — and it existed on a tavern

This is the finding that stops the question being easy, and it is the project's own.

The **Green Tree Tavern**, built by James Kinzie in 1833 (`chicagology_prefire127`,
`drloih_hotels`, `drloih_wolf_point`; attested from 1833-01-01), is carried at
7.62 × 12.19 m — **25 × 40 ft, a depth-to-width ratio of 1.6** — and it is dressed
`elevation_scheme: "gable_front"`, read off plate "11" of the 2026-08-11 reference set
(T-0083). `frame_tavern_params` describes what that means: the building fronts on a gable
end, the even bays run along the two eaves elevations, and the gable faces carry the doors
and the attic lights. Its own validator *requires* `depth_m > width_m`, so the ridge runs
along the deep axis.

A deep-plan, gable-front, ridge-front-to-back frame building therefore **stood in Chicago
on 1 July 1835**, and this project already models one. The Greek-Revival-arrives-in-1836
line cannot mean the mass was unbuildable here; it is a statement about a *fashion in
dwellings*, not about carpentry.

## 3. But every gable-front building the project holds is a business, a public house or a church

Twenty-four committed structure records mention a gable front. Sorted by what the building
*was*, they fall into one pattern and admit no exception:

| building | kind | archetype | elevation |
|---|---|---|---|
| Green Tree Tavern | tavern | `frame_tavern` | `gable_front`, from a depiction |
| physician's office | shop/office | `frame_storefront` | `gable_front` |
| inferred bakery, barber, tailor, butcher's market | shops | `frame_storefront` | gable-front |
| St Mary's, First Presbyterian | churches | — | gable-front is the form the memo says was wanted |
| the anonymous C2/C3 store rows | shops | `frame_storefront` | gable-front |

**Not one of them is a dwelling.** And the gable front on a shop is not a fashion at all —
it is the shopfront's own logic, the show face and the door put on the street end of a deep
lot-filling range. That logic does not transfer to a cottage, which has nothing to show.

## 4. Where a source states a dwelling's elevation, it states eaves-front

Two records in this dataset turn on the question and both answer it the same way.

- **New York House** (1834). The record's note is explicit: *"'With eaves to the street'
  is the one elevation fact any source states about this building"* (`andreas_1884_v1`).
  It is dressed on the `frontage` scheme, taken with a footprint wider than it is deep.
- **The LaSalle-and-Lake house** (1834, $250). The record reasons from plan and form to a
  30 ft front on a 16 ft depth, and cites the eaves-front rule to do it: *"the long
  dimension is the front by the same argument that shapes every other dwelling in the
  town."*

The only record that pushes the other way is **St Mary's church**, whose memo concedes the
archetype forced an eaves-front range onto a building that *"would ordinarily have turned
its 25 ft gable end to the street"* — and files the orientation in `docs/LIBERTIES.md`
rather than dressing it up as a finding. That is a church, and the memo already says the
liberty is the archetype's.

## 5. The driver for a gable-front cottage did not exist in this town

The gable-front cottage is a **narrow-lot** building. Turning the short side to the street
is what you do when frontage is the scarce thing, and it is why the form spreads through
American towns as their blocks subdivide in the 1840s and 50s. The crosswalk knows this:
D5's own `variants` line reads **"narrow urban plan"**.

Chicago in July 1835 had no narrow lots. Measured on the committed lot layer,
`data/traces/vectors/thompson_lots.json`:

    298 lot records carrying a frontage
    median frontage   80.9 ft
    minimum           24.3 ft
    under 40 ft        4 lots  (1.3 %)
    under 30 ft        2 lots  (0.7 %)

Eighty feet is the module, and the plat prints it: `docs/RESEARCH/thompson_plat_grid.md`
reads the platted **80** written in each street on Wright's 1834 sheet, and
`docs/RESEARCH/west_division_lot_figures.md` reads a lot frontage of **75 ⅗ ft** off the
west margin of blocks 47 and 26 of the Thompson plat itself.

A D5 cottage is **18–24 ft wide**. On a 75-to-80 ft lot it uses under a third of its
frontage. **There is nothing for the gable front to economise.** The crosswalk's stated
reason for the form names a condition the town did not have.

## 6. The ruling

**NEGATIVE, for a dwelling family, as a default.** The deep-plan gable-front *cottage* is
not an attested or inferable form of Chicago on 1 July 1835. D5's mandatory front gable is
withdrawn and the D5 crosswalk row is repaired instead of an archetype being built for it.

The argument is not the 1836 date on its own — § 2 shows the mass was standing in 1833. It
is the three readings together: **no source records a gable-front dwelling here; every
gable front the corpus does hold belongs to a building with a shopfront's or a church's
reason for one; and the narrow frontage that produces the form on a house was not a
condition of this town.** An invention needs a reason, and D5's stated reason is the one
thing § 5 measures as false.

### What the ruling does NOT say

1. **It does not refuse a gable front on a shop, a tavern or a church.** The Green Tree
   keeps its elevation and its depiction; `frame_tavern` and `frame_storefront` keep their
   schemes unchanged. This is a ruling about D-family dwellings only.
2. **It does not relax `frame_dwelling`'s 1.5 ceiling**, and does not touch it. T-1497's
   acceptance § 5 required that and it is met by not editing the file's gate at all.
3. **It does not widen D5's footprint band.** `measure_band_claims.py` says why in terms —
   *"a band widened to admit the value it was supposed to bound stops being evidence"* —
   and the band `18x28-24x34 ft` is committed here unchanged. What changes is the *roof
   claim over* that rectangle, not the rectangle.
4. **It does not re-grade a single instantiated record.** Every D5 value stays at the
   bottom tier where it was; nothing is upgraded because a plan document was repaired.
5. **It does not close the door.** A depiction, an insurance survey or a description of a
   named Chicago house turned end-on before 1836 reopens this at once. § 7 states the test.

## 7. What it costs the town: one building

The repair is nearly free, and that is itself evidence the crosswalk row was the thing out
of step rather than the model. **All 32 instantiated D5 roofs already stand eaves-front**,
on `frame_dwelling`, because the placeholder was the only thing that could build them.
Thirty-one of them sit inside D5's band as drawn and do not move.

The thirty-second is `recon_1835_west_033`, and it is the one the ratchet has been
carrying. Its recipe slot asks for **20 × 32 ft** — a ratio of 1.6, past the archetype's
1.5 refusal — so `tools/generate_west_infill.py` swapped width for depth and turned the
bearing a quarter circle to get an eaves-front house through at all. The result stood as
`32.00 × 20.00 ft` and read **out of the 18x28-24x34 band it cites**, which is the row
banked in `tools/band_claims_baseline.json` with `waiting_on: T-1497`.

With the front gable withdrawn, the swap has nothing to be a workaround for, and the fault
is visible for what it always was: **the west parcel is the one generator that takes its
rectangle straight from the recipe instead of through `tools/family_bands.py`**, so the
rule the other parcels already carry —

    if family.startswith(("D", "H")) and family not in ("D1", "D2") and depth > width * 1.46:
        width = min(hi_w * .3048, depth / 1.46)

— never reached it. T-1497 routes the west parcel's refusals through that same rule rather
than through a quarter-circle turn. `west_rec_033` is re-derived at **21.92 × 32.00 ft**:
the recipe's own 32 ft depth kept, the width held to the eaves-front proportion the project
already uses, both figures inside D5's authored band, no swap and no rotation. The baseline
row leaves the file.

**The residual, stated rather than left silent.** Nineteen other west slots sit between
1.46 and 1.5 — six of them D-family — and they keep their recipe rectangles, because their
archetype builds them and the clamp here fires only where it refuses. Re-sampling the whole
west parcel through `family_bands.dimensions_m` would move seven roofs and rebake them for
a proportion nothing is complaining about; it is not this ticket's work. Filed as a
finding on T-1497.
