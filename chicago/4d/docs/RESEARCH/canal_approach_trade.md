# Canal approach stores and workshops — T-1766

This parcel completes the current West Division trade-roof remainder: two stores
and three workshops. It does not identify five historical buildings or recover
five addresses. The owner reconstruction specification bounds the building
families and town totals; the West Division memo bounds the district character.
All five presences, exact uses, placements and forms are reconstructed.

## Why this family mix

The current programme has four West stores against six and five workshops against
eight. Its town-wide C1 and C2 budgets are already exceeded by one each; repeating
the old memo's initial C1/C2 allocation would add to that excess. This parcel uses
one C3 narrow two-storey store, one C4 wider two-storey store, and W1/W2/W3 shop
families. The memo's first-parcel table is an earlier allocation, not a second
master inventory. The four original West workshop slots that were refamilied
because they stood off the street retain that ruling.

## Placement and evidence limits

The new parcel takes free frontage on the east side of the drawn Canal Street
corridor between Lake and Randolph. Its street line is the drawn line, consistent with the
project's block-placement ruling; it does not silently substitute survey control.
Individual sites and gaps are inventions. They must clear existing footprints,
road corridors, the river setback, the unrevised swale corridors and no-build
polygons, and remain on dry terrain across their complete footprints.

The Wright and Hathaway maps bound streets and lots; they are not evidence for
these five roofs or their occupants. The owner specification
(`owner_chicago_1835_reconstruction_spec_2026`) supports reconstruction within
family bands. The existing West memo, `west_division_infill_1835.md`, supplies
context. A dated plan, address, advertisement or archaeological finding specific
to one of these sites would replace the relevant reconstruction.

This work does not complete the deferred West street ticket T-1414. Its proposed
sites are on existing modelled Canal frontage, and its former terrain-limit
statement is not treated as evidence that the entire street programme is complete.
T-1764 retains the forks close-out; T-1208 retains the outer West clusters.

## Validation record

The pre-deal frame-budget reading, final geometry clearances, occupancy assignments,
bake and published viewport results are recorded with the implementation and PR.
The five structures must be baked and occupied before this parcel is complete.

### Pre-deal budget

`data/render/canal_approach_before.json` records the published `dev` desktop
sweep before the new roofs: Full 1,417,245/1,460,000, Balanced
1,220,005/1,280,000, and Light 802,855/825,000. The largest standing C3/C4/W1/W3
meshes cost 828/850/1,504/1,626 triangles. No standing W2 mesh is attributable,
so the instrument correctly refuses to price that family. For planning only,
allowing W2 twice the largest W3 gives 8,060 triangles before the measured
shadow multipliers: about 9,508 at Full/Balanced and 10,663 at Light. The
remaining margins would be 33,247, 50,487 and 11,482. This surrogate is an
explicit estimate, not a measured W2 mesh or a guarantee; the final baked scene
must pass its own budget sweep. No ceiling is raised.

The selected frontage is east of Canal between Lake and Randolph. Earlier
north-of-Lake candidate sites were rejected because they entered an active
conjectural swale. The final records omit `resident_assignment`: a household's
keeper working here does not establish a dwelling here, and the platted dealer
would otherwise mistake that field for a residential reservation.

Both archetypes define the front at local +Y. The generated bearing is
266.704005 degrees, so the front doors face west toward Canal. A regression
case reverses that bearing while preserving the footprint and requires the
frontage check to reject it.

The street-face allocator reads the authored workplace allocation as a reservation,
so a second firm cannot adopt the same roof. Its five rejection cases pass; it
does not reserve or invent a home. Public IDs end in unique ordinals as required
by the existing allocation system. Separate, explicit geometry seed keys preserve
the original measured dimensions, form, finish and siding through this naming fix.
