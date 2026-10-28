# The 1904 front yards: what the photographs show, and what we plant (T-3203, T-3223)

The owner, 2026-10-27: *"plants in front of the houses they seem to be missing flora on the
property"* (T-3203). The owner, 2026-10-28, on what T-3203 drew: *"I find the bushes and plants
and flowers added to be very low quality ... make sure they don't block doorways, etc and are
positioned correctly to not block the doors"* (T-3223).

T-3203 laid a continuous foundation row (1,354 shrubs) along nearly every house and drew each as
a lump. Neither the row nor the lumps were what the pictures show. T-3223 read the pictures again,
lot by lot, and rebuilt both the planting and the plants.

## What the photographs show

| Lot | Picture | Front yard |
| --- | --- | --- |
| 1720 Prairie (Tyrrell) | `glessner_blog_1720_tyrrell_photo` | lawn behind the iron fence; no shrub |
| 1736 Prairie (McBirney) | `glessner_blog_1736_mcbirney_c1890_photo` | lawn behind the fence; no shrub |
| 1801 Prairie (Kimball) | `taylor_c1895_kimball_residence_1801` | lawn edged by a low coping; no shrub |
| 1811 Prairie (Ames) | `chicagology_1811_ames_photo` | lawn behind a rock-faced coping; no shrub |
| 1816 Prairie (Henderson) | `chicagology_1816_henderson_photo` | lawn; the trees are the parkway's |
| 1905 Prairie (Field) | `chicagology_1905_field_photo` | lawn behind the fence; no shrub |
| 2120 Prairie (Gorton) | `chicagology_2120_gorton_photo` | lawn; no shrub |
| 1729 Prairie (Pullman) | `loc_det_4a08065_pullman_residence`, `loc_det_4a08066_pullman_residence` | ivy over the west front and porch; a few low shrubs at the porch's foot; staked young trees in the lawn; a dense shrub border inside the 18th Street coping |
| 1912 Prairie | `chicagology_1912_prairie_exterior_photo` (after 1904) | ivy over the front |

The common picture is a kept, mown lawn running to the house, behind an iron fence or a stone
coping, with the stoop and its walk, and the parkway elms outside. The tall trees that frame the
houses in these views stand in the parkway, not the yard. Only Pullman's yard is planted in a way
a picture records.

## What is drawn

* **Pictured lots** are drawn as their pictures show them: the seven lots above with a bare lawn
  are bare (`BARE` in the tool), and Pullman and 1912 keep their ivy, Pullman its porch shrubs,
  its young lindens and its 18th Street border (attested; 1912 inferred).
* **Every other lot** is reconstructed (liberty `L-prairie-front-yards-3203`). About a third are
  left as open lawn. The rest get one of the few plantings the period's yards and garden books
  describe, chosen per lot from a seed of its parcel id: a matched pair of shrubs at the stoop's
  foot, a lilac or a sheared arborvitae at a front corner, a short group of two or three shrubs
  against the front, and on a deep lot now and then a young sugar maple or linden in the lawn and
  one round or oval bed of scarlet or pink geraniums or coleus.
* **The plants** are the nursery stock of the time: common lilac, Van Houtte's spiraea, smooth
  hydrangea in flower, a garden rose in flower, American arborvitae sheared to a cone or a ball,
  geraniums, coleus, young sugar maple and linden, and Boston ivy. Each is grown by
  `renderers/web/js/tree-model.js` from its own habit (branching, leaf, flower heads) on the
  parkway elms' leaf and bark atlases, and drawn by `tree-instances.js` at the same detail levels
  as the elms; evergreens keep their crown in every Season.

## Doors, stoops and walks

`tools/plant_prairie_1904_front_yards.py` lays every 1904 house's baked model on a 0.25 m plan
raster. A plant is placed only where its crown's EDGE keeps clear of: the house wall, a stoop and
its steps, a fence, pier or coping, a paved walk, a 2 m disk round every door leaf of the lot's
houses, a 1.6 m-wide way from each front door straight to the lot line, and the lot lines. The
renderer draws each plant at the height and crown width the tool measured, so what is checked is
what is seen. `--check` re-measures the committed file against the models in every gate run, so a
rebake that moves a stoop or a door under a plant fails and names the plant and what it blocks;
`--self-test` plants three faults on a real lot (a shrub on the way to a front door, one beside the
door, one inside the house) and confirms each is refused.

## Before and after

`front-yards-3223/before-after.jpg`: the same stands on dev before T-3223 and with it.
