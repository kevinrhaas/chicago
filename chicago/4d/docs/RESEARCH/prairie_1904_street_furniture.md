# The 1904 district's street furniture: what the pictures show

The owner, 2026-10-27, thread "Improve 1904 Prairie streetscape": *"I do see evidence of
streetlamps at the corners of major streets, and also from the photo"*. The brief is the tickets
repo's `evidence/streetscape-1904-2026-10-27/BRIEF.md` § 2. This page is the reading behind
`data/street_furniture/1904.json` (written by `tools/lay_prairie_1904_street_furniture.py`, drawn by
`renderers/web/js/street-furniture.js`); the inventions are `docs/LIBERTIES.md`
L-prairie-street-lamps-3199 (the lamps), L-prairie-hydrants-3201 (the hydrants) and
L-prairie-utility-poles-3202 (the poles and wires). Every picture below was read from the image store's copy
(`kevinrhaas/chicago-images`, `prairie-1904/files/<id>.jpg`).

## 1. Gas lamps (T-3199)

**The post.** Three pictures show one whole and near: Taylor no. 2135 (Glessner's corner, c. 1887-89),
the 1811 photograph (Coleman / Ames) and the second 2140 photograph (Tucker). All three are the same
post: a moulded base about a third of a metre across and half a metre high, a fluted cast-iron
column tapering up to a knop, a ladder bar across it just under the lantern, a four-sided glass
lantern wider at its top than its foot, a pyramidal cap with a short chimney and a finial. Against
Glessner's rustication courses and the 1811 stair the lantern's foot stands about 2.4 m up and the
finial about 3.1 m. The Detroit Publishing view, George Glessner's 1721 photograph, the Kimball,
1816, 1905 and 2120 photographs show the same post. The 2140 photograph looking north-west from 22nd
Street's south-east corner has a different, hooded lamp in its foreground, on a corner outside the
drawn district; it is not modelled. Electric standards appear only in pictures dated after 1904
(1912 Moulton-Lowden, the 1919 programme, the 1915 view at 2001), so every 1904 lamp is gas.

**At the corners.** Taylor 2135: the post stands on a small square stone footing at the curb corner,
between the two crossing ramps. The Detroit view and the museum's halftone of the finished Pullman
house: the Pullman corner (north-east of 18th and Prairie) has its post in a curbed grass plot at the
curb corner. The Greene stereograph shows the Tucker corner (north-west of 22nd and Prairie) the same
way, c. 1876-81. The Ward engraving of 1887 draws one at the east parkway's corner at 20th Street.
So four corners are pictured, and the owner's reading and these four put one at every corner. The
early Kimball photograph's lamp, at its right edge, stands in front of the brick house south of
1801: it is the 1811 photograph's lamp, at the 1801/1811 lot line, not the corner's.

**Mid-block.** 1801/1811 (the 1811 photograph: on the parkway beside the walk at the north lot
line); 1708 (the Glessner townhouses photograph: before 1708); opposite 1721 (George Glessner's
winter photograph from the west walk, the lamp in the right foreground); 1816/1824 (the 1816
photograph: beyond the house's south flank); 1905 (the Field photograph: before the house's north
part); 2120 (just south of the stoop); 2140 (at the Prairie Avenue porch). Each of those stands on
the parkway close to the walk, which is where the rule places the others. The pictured runs (the 1905
*Views of Chicago* plate, Taylor 9974 south from 18th) read as about one lamp per 150-200 ft of side.

**Lit?** The scene is 10:30 on a July morning and world.js has no night or evening setting, so no
lamp is lit and no light is added.

## 2. Fire hydrants (T-3201)

**The hydrant.** The Detroit Publishing view of the Pullman house (`loc_det_4a08065_pullman_residence`,
the owner's crop) shows it clearly on the Prairie Avenue parkway beside the walk, a few metres north of
the corner lamp at 18th Street: a post hydrant, a barrel on a flared foot, a band under a domed bonnet
with an operating nut on top, and a nozzle cap on each side, read as about 0.85 m tall. The museum's halftone of the finished house (`ghm_blog_pullman_completed`)
has the same hydrant at the same place. The second 2140 photograph (`chicagology_2140_photo_b`) has
one of the same type in its left foreground, on the Prairie Avenue parkway toward 22nd Street, near
the curb. The prints are monochrome. The Detroit view prints the hydrant lighter than the lamp posts, so it is drawn a mid grey.

**Where the rest stand.** No other picture places one, so the rest are a reconstructed spacing: one
at each intersection, at a corner taken in turn, on the avenue's parkway a few metres from the corner near the curb, and one
mid-block on the long blocks (the faces of 150 m or more), on one side of the street. Every hydrant is
in the grass, never in a walk, a corner crossing or a carriage walk, and is kept clear of the lamps and
the elms. The inventions are `docs/LIBERTIES.md` L-prairie-hydrants-3201.

**Stills.** `street-furniture-3201/`: Pullman's hydrant against a crop of the Detroit view, on the desktop
(full) and on a phone (light), the Detroit view's whole stand, and Tucker's hydrant from the south-east;
`readings.json` holds each stand's frame triangles and draw calls with the layer hidden and shown. The
lamps' stills are in `street-furniture-3199/` (Glessner's corner against Taylor 2135, Pullman's against
the Detroit view).

## 3. Utility poles and wires (T-3202)

**Glessner's pole.** The c. 1887 photograph of the stable from the north-west
(`cornell_adw_glessner_stable_1887`, the museum's "Cornell rear") has a wooden pole on the 18th Street
parkway at the stable's north-west corner, by the alley. It carries one crossarm of about six pins.
It is the only pole any picture of the district shows. Taylor no. 2135, looking along Glessner's 18th
Street front east of the stable, shows none; neither does the Detroit Publishing view of 18th Street
east of Prairie. So the drawn line runs west from Glessner's pole, not east, and turns into the alley
behind it.

**The alleys.** No picture of an alley in the district has been found. Lines down the alleys are the
reconstruction: one on each alley's east side, about every 34 m, joined across the cross streets where
alleys meet. No pole stands on a Prairie Avenue parkway, where the pictures show the lamps and elms and
no pole.

**22nd Street's trolley.** The photograph from the south-east corner of 22nd and Prairie
(`chicagology_2140_photo_a`) shows street-railway rails and overhead trolley wires across 22nd Street.
It is undated, but taken after 1890. The two maps that would date the line,
`st-uchicago-1902-surface-street-railroads` and `st-uchicago-blanchard-1897-street-car-lines-se`, are
catalogued in the Prairie library, but their images could not be reached from the build containers.
So the overhead is inferred from the photograph, and its form is reconstructed: paired plain poles, a
span wire between them and two contact wires over the tracks. The poles are not in the photograph.
The inventions are `docs/LIBERTIES.md` L-prairie-utility-poles-3202.

**Stills.** `street-furniture-3202/`: Glessner's stable from 18th Street, the alley behind Glessner's,
and 22nd Street's overhead, each on the desktop and on a phone, and `readings.json`.
