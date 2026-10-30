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
  are bare (`BARE` in the tool), and Pullman and 1912 keep their ivy (off the porch front), Pullman
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
houses, a 5.2 m-wide way from each front door straight to the lot line (T-3227: at 3.2 m wide,
Pullman's porch pair and the ivy on its porch posts still stood in front of its door), widened to
the whole front of the stoop or porch the door opens onto, up to 4.5 m either side, and the lot
lines. Pullman's porch-foot shrubs, which the Detroit views show, are therefore left out. A patch of ivy keeps its whole width, not just its middle, off a door's way. The
renderer draws each plant at the height and crown width the tool measured, so what is checked is
what is seen. `--check` re-measures the committed file against the models in every gate run, so a
rebake that moves a stoop or a door under a plant fails and names the plant and what it blocks;
`--self-test` plants three faults on a real lot (a shrub on the way to a front door, one beside the
door, one inside the house) and confirms each is refused.

## Before and after

`front-yards-3223/before-after.jpg`: the same stands on dev before T-3223 and with it.

## Pullman's tub plants (T-1934)

The 1894 Inland Architect plate of the palm house and stable is a summer picture, and the terrace
in it is set out with clipped evergreens: a ball sitting on its tub east of the flight, a ball on a
clear stem in a tub before the stable's west arcade, a slim clipped column inside the 18th Street
wall by its east pier, and more by the plate's second flight (a cone in a tub, a potted conifer,
a tall evergreen mass). Taylor's 16555, a summer or two earlier, shows the column by the pier and
sets the rest differently (an urn on the flight's east pier, slim cones, potted palms). Tub plants
were carried under glass for the winter and set out again each summer, so the two arrangements are
two summers, not a disagreement about a building. The three the build can stand without the plate's
second flight are planted from the plate (`PICTURED["prairie_1729"]["tubs"]` in the planter), each
read through the plate's solved camera on a stated plane, and graded `inferred` for 1904; a tub on
the terrace stands on the terrace floor read off the baked model, which `--check` re-measures. The
renderer draws the tubs and their plants in every Season but winter (L-pullman-terrace-tubs-1934).

The second reading (T-1934, 2026-10-30) stands three more where both pictures place them. Each is
fixed in plan by crossing the plate's pixel column with 16555's (the two cameras stand 16 degrees
apart, so the depth is good to about a metre) and its top read off the plate where it shows: the
slim column on the terrace against the drum's west side, the cone in its tub before the wing's
arched door east of the drum (the plate's "cone at the flight's head": it stands on the terrace
behind the flight, not on it), and the palm in its tub before the drum, which only the print shows
(the plate's elm trunk stands across that place). The palm grows on its own habit,
`phoenix_tub` in `tree-model.js`: a short stem and arching pinnate fronds, no clipped shell.

The planter's ivy band now reaches the house's main face as well as its nearest part. T-1881
brought Pullman's entry porch 3.5 m before the front wall, and measured from the porch the band
(`front + 6 m`) stopped short of the wall the Detroit photograph shows the ivy on, so a re-run left
the lot with none; the band now also takes the wall along the median of the face's metre-by-metre
front line. 1912 Prairie's ivy is unchanged by it.
