# The 1904 Prairie Avenue parkway elms (T-2473)

The owner, 2026-10-13, with the postcard of Prairie Avenue looking south from 18th Street:
*"we want to emulate this … add street foliage trees correctly, would be nice to in options to
be able to hide trees or make them spring trees barely blooming so you can see the house with
the trees shown but you can still see the house, default should have the correct trees, you
should be able to use the models from 1835 for flora as a base."* And: *"I want the default to be
nice trees with summer leaves like the photo but an option to make them spring trees, winter bare
trees or make them all disappear."*

## What was read

| source | what it shows | tier carried |
|---|---|---|
| `picturesque_chicago_1892_prairie_avenue`: the west-walk view south from 18th Street beside Glessner, negative Dec. 1887 to 1891 (Flinn 1891, Picturesque Chicago 1892, Flinn 1892/93, the Holzman postcard postmarked 1908; the owner's copy is `data/sources/assets/prairie_streetscape_owner_2026_10/`) | one file of tall elms per parkway, standing nearer the curb than the walk; boles clear to about a third of their height; crowns meeting high over the walk; spacing very roughly 25-35 ft; a file on the far side too | the file, its side of the parkway, the habit: inferred for 1904 |
| `views_of_chicago_1905_prairie_michigan`: L. H. Nelson, 1905 | "a single row of closely spaced elms" in the parkway, around the scene date | the single file in 1904: inferred |

Neither names the species. Elm is the reading of crown and bark in the prints, and it is the
1835 scene's own American elm model that draws them, as asked.

## What was built

- `tools/plant_prairie_1904_street_trees.py` plants **418 trees on 31 block faces** into
  `data/street_trees/1904.json` from the parkway bands of the street grid (T-0474): one file per
  face, 62 % of the way from walk to curb, about 30 ft apart, 10.5 m clear of each face's end,
  3.5 m clear of an alley mouth, about one young tree in twelve and one gap in twenty-five.
  `check.sh` re-plants and diffs it.
- `renderers/web/js/street-trees.js` draws them with `trees.js`'s own builder (the 1835 elm in
  a high-crowned, clear-boled "gallery" form): 12 mature and 3 young crowns, instanced in one
  batched draw call that casts and takes shadows and sways with the 1835 wind.
- **Settings › Street trees**: *Summer — full leaf* (the default), *Spring — first leaf, see
  the houses* (sparse pale leaf on bare limbs), *Winter — bare limbs* (the summer crown's sprays
  drawn from a twig-only copy of the 1835 leaf atlas, painted the first time winter is picked),
  *Hidden*. It shows only in a scene with street
  trees (1904 today). Clicking a trunk opens the tree's card with this reading and the liberty.
- Every position is reconstructed: `docs/LIBERTIES.md` **L-prairie-parkway-elms-2473**.

## Side by side

The owner's postcard, the street before, and after (desktop, same stand: the west walk at
18th Street looking south):

![postcard, before, after](prairie_1904_street_trees/postcard-before-after.jpg)

The four settings at the same stand (summer, spring; winter, hidden):

![summer, spring, winter, hidden](prairie_1904_street_trees/modes-summer-spring-winter-hidden.jpg)

From 30 m up before and after, and the phone (390 x 780) at the postcard stand:

![aerial before, after, phone](prairie_1904_street_trees/aerial-and-phone.jpg)

**Matches:** one file per parkway on both sides; tall clear boles; crowns meeting over the walk;
the rhythm of the trunks down the block; dappled shade on walk and roadway.
**Differs, and where it goes:** the postcard's trunks are slimmer and more irregular than these
fluted dark columns, and its trees stand a little nearer the curb; the paved crossing of the
parkway, the curb's step above the roadway and the carriage blocks are T-2474; the hard
seams between street surfaces and lawn are T-2475. Bushes and planting at the house fronts are
left to each house's own pass.

## Cost

Measured on SwiftShader at the postcard stand, full detail: the frame goes from 3.63 M to
3.92 M triangles and from 205 to 207 draw calls; the JS heap after a forced collection is
unchanged (678 MB both ways, 678 MB on the phone viewport). Hidden returns the frame to 3.63 M.
Winter draws the same triangles as summer; picking it the first time paints the twig atlas, about
23 MB of heap, which the summer and spring settings never pay.
At `balanced`/`light` each crown has fewer leaf sprays and the phone build drops the leaf
atlas's top mip.
