# The 1904 street section: the curb's reveal, the walk's fall, carriage walks (T-2474)

The owner, 2026-10-13, with the postcard of Prairie Avenue looking south from 18th Street:
*"Look at the curb height and make sure we are correct on that, with correct carriage walk
ways"*; then, with a second photograph, *"it shows the curbs nicely"*.

## What was read

| source | what it shows | carried as |
|---|---|---|
| `chicago_revised_municipal_code_1905`, the 'Slope' sections | the sidewalk space's grade: "a uniform incline from the street line toward the curb line, with a fall of one inch in every three feet" | the fall, inferred for 1904 |
| `picturesque_chicago_1892_prairie_avenue` (the 1887-91 view south from 18th Street; the owner's postcard copy) | a pale dressed stone curb standing above a smooth roadway; a paved crossing of the parkway from the walk to the curb | the reveal's order of size; that crossings existed |
| the owner's second photograph (`data/sources/assets/prairie_streetscape_owner_2026_10/owner_prairie_avenue_curbs_photo.jpg`; publication not identified) | the curb's top about one stoop riser above the roadway, walk and parkway level with the curb's top | the reveal's order of size |
| `views_of_chicago_1905_prairie_michigan` | dressed stone carriage blocks along the parkway's edge | that blocks existed |

No source read states the reveal as a number. A stoop riser of the period is about 7 in, so the
reveal is **7 in, reconstructed** (`docs/LIBERTIES.md` L-prairie-curb-reveal-2474).

## What was built

- `tools/lay_prairie_1904_street_section.py` writes `data/street_section/1904.json`: the fall,
  the reveal, the roadway's level (0.30 m below the lot line on a 66-ft street), and **91
  carriage walks**, one at the middle of every lot at least 40 ft wide, each 5 ft wide from the
  walk to the curb with a 3 x 2 ft, 18-in carriage block beside it at the curb
  (L-prairie-carriage-walks-2474). `check.sh` re-lays and diffs it.
- `renderers/web/js/street-grid.js` draws every band at its fall and every roadway at its level,
  a dressed stone face down from each curb, and a stone edge wherever a roadway at the district's
  edge meets no drawn sidewalk. It cuts the field's own ground out under all of it
  (`terrain.setGroundCut`: a 0.5 m coverage mask, a discard in the ground's shader behind a uniform
  switch, so no other scene's program changes) and tells the walker how far down the street is.
- The parkway elms stand on the parkway's fall and keep clear of the carriage walks.
- L293 (the street section) gains a line saying the section is now drawn.

## Side by side

![the curb at street level, before and after](prairie_1904_street_section/curb-before-after.jpg)

## The carriage blocks withdrawn; posts only where pictured (T-3198, 2026-10-27)

The owner, 2026-10-27: *"i dont need to have those carriage steps at every house. i dont see that in
photos of prarie anywhere"*, then *"what you keep you should vary them in appearance so that they do
not look like clones"* and *"they mostly should go i think because i dont see them in photos, unless
you do"*.

Read again, `views_of_chicago_1905_prairie_michigan` and the Flinn view show the **lot-line coping**
along the walk's inside edge (rounded stone copers), not blocks at the curb; the Pullman views
(`a16-pullman-det-4a08065`, `a16-ghm-blog-pullman-completed`) show the parkway's edge clear. Two
pictures do show stones at the curb:

| picture | source | what stands | carried as |
|---|---|---|---|
| `a18-cgy-1815-sears-two-views` | `chicagology_1815_sears_two_views` | a square post with a domed top beside 1815's crossing | one square domed post, attested |
| `a20-glessner-2100-block-west-side-1890s` | `glessner_blog_2100_block_looking_nw_1890s` | round white domed posts: two before 2112, one before 2110, a row on the east curb at the right edge | 3 posts at 2112/2110, attested; 9 along the east curb before 2109-2115, inferred |

So the 91 rule-placed blocks are gone and 13 carriage posts stand (`carriage_posts` in
`data/street_section/1904.json`, laid by the same tool), 0.38 m in from the curb's face, stood clear
of any elm by 0.85 m. Each post is varied by a seed on its id: height 0.78-1.06 m, width, the cap
(plain dome, dome over a collar, flattened dome), a lean of 0.4-2 degrees, its turn and its stone's
tone. The paved carriage walks stay: 1815's, the 2100 block's and Glessner's (HABS no. 2) are pictured.
Amended liberty: L-prairie-carriage-walks-2474.

## The corner crossings and their ramps (T-3200, 2026-10-27)

The owner, 2026-10-27, with J. W. Taylor's photograph no. 2135: *"there are ramps down into the
street. they appear to be stone"*.

| picture | source | what it shows | carried as |
|---|---|---|---|
| `a18-rba-taylor-2135-glessner-ne` | `taylor_2135_glessner_exterior_1887_1889` | the Glessner corner (18th and Prairie, SW): the walk carried across the parkway to the curb, two broad slabs sloping from the curb's top to the roadway, one each way across, the lamp's footing between | that corner's two crossings, attested |
| `a16-pullman-det-4a08065` | `loc_det_4a08065_pullman_residence` | the Pullman corner (NE): the walks carried across the parkway either side of a curbed grass corner with the lamp, down to the roadway | that corner's two crossings, attested |

So at each of the 28 corners where two faces of a block meet (Calumet's curve at 18th is a bend and
has none), each face's walk runs straight on across the other street's parkway and over the curb at
its own width and level, and from the curb's face one dressed stone slab, 15 cm thick, runs 1.5 m out
into the roadway, its top falling from the curb's top to 5 cm over the paving at its foot:
`corner_crossings` in `data/street_section/1904.json`, 56 crossings, laid by the same tool.
`street-grid.js` cuts the parkway and the curb out under each crossing, lays the walk over them, lays
the slab's sloping top on the roadway with its two sides and its foot standing to its thickness, and
gives the walker the slab's slope. The curb's face runs on unbroken behind the slab. The corner
lamp's plot stands between each pair (T-3199). Liberty: L-prairie-corner-crossings-3200.

**T-3217 (2026-10-28).** The first build (T-3200) sloped the walk's last 1.35 m down inside the
parkway and broke the curb for it, so at the curb it read as a bevel that sank under the road. The
owner, 2026-10-27, with a screenshot of it: *"they dont go down into the street like the photos ...
make them a single piece or pieces ramped down into onto the street like the photos"*. Read again,
both pictures carry the walk level over the curb and set the slab beyond it, in the roadway: Taylor
2135's two slabs start at the curb's top and lie on the dirt road with a dark gap under their sides;
the Detroit view's south-west and south-east slabs show their thickness at their sides and foot.

![Taylor 2135's corner; the first build (the owner's screenshot); the slabs now, from Taylor's stand](prairie_1904_street_section/corner-ramps-before-after.jpg)

## The walk joins (T-3274, 2026-10-31)

The owner, 2026-10-31, with a phone screenshot from the 18th Street walk at Calumet Avenue (the
Pullman glasshouse ground): *"there is a gap there between sidewalk and walkway. I see that all over
the place ... make the walk connect correctly based on the photos"*. Measured on dev that day, every
yard builder laid its walks to the lot line (`front_yard_m` before the house's street front), and
the public walk starts a foot outside it (the `margin` band, sec. 2062: "All walks to be laid on a
line one foot from and parallel with the lot line"; T-3233 made that foot the lot's own grass). So
39 of the 48 worked houses' front walks, all 11 side service walks, 1729's two drives and the
glasshouse ground's walk and drive stopped 0.18-1.6 m short on grass; the widest were 1812 Prairie
(1.6 m: its traced front and recorded front yard leave more than the foot) and the glasshouse
ground (0.8-0.9 m). Nine front walks already met the public walk.

`tools/lay_prairie_1904_walk_joins.py` reads each walk's street end off what was built (the K14/K16
instances in the GLBs' node extras, as `tools/check_house_walks.py` reads them, and the K13 record's
`grounds` rows), carries it into the scene by the house's 1904 placement, and measures it to the
nearest public walk band. An end 0.02-2.5 m off gets a join the walk's width, from 4 cm under its
end square across to 4 cm into the public walk: 51 joins in `data/street_section/walk_joins_1904.json`,
which `street-grid.js` draws as pieces of the face's walk band, in its paving and at its level. The
houses' GLBs are untouched, so no house lane's work is restaled; a lane that moves a walk or a
placement fails `--check` in the gate and reruns the tool. Liberty: L-prairie-walk-joins-3274.
