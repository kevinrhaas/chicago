# T-3660 — 2031 Prairie on K01: the Tolman house, a bounded design off the 1911 sheet

Piece 2 of T-1918 (the S09 package of the T-1837 programme: the 2031-2035 limestone row). The district draft
(T-2352) is refined in place, under its own id (`tolman_house_2031_prairie`), onto the K01 frontage assembly
(`generators/k01_emit.py`); liberty `L-k01-2031-tolman-3660`. The alley building
(`tolman_house_2031_prairie_coach_house`) is T-1938's and is untouched.

## Does the 1887 Dewey drawing belong to 2031? No.

The Prairie library held one picture against 2031: William W. Clay's 1887 Inland Architect drawing,
*Residence for A. B. Dewey* (`a20-aic-ia-dewey-residence-drawing-1887`), placed here on an Inter Ocean notice
of 1 October 1887 quoted by Chicagology ("Bedford stone, 72x32 feet, three stories", at No. 2031). It is
ruled out for this structure in `data/structure_grades.json`, so 2031's grade is now `inferred` (map only):

- the Art Institute catalogues the drawing at "2631 S. Prairie Ave. [?]";
- directories (quoted on the same Chicagology page) have Samuel A. Tolman at 2031 from 1873 to his death
  there in 1919, and the 1904 Blue Book lists "Mr. & Mrs. Samuel A. Tolman" at 2031;
- the 1911 sheet draws 2031 as the north house of a party-walled row of three on 25-foot lots (census
  ruling r35-2031-2035-row): a 7.8 m stone front with a canted bay. The drawing is a free-standing,
  rock-faced Romanesque house with a corner tower and a 32-foot front, which that lot cannot hold.

So T-1918's image gate has no picture to ask of 2031. A photograph or plate of 2031's real front, if one
turns up, is what would reopen it.

## What was read

Sheet 35 of the 1911 Sanborn (`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_35.jpg`),
read at full size with dark-line profiles, carried into the lot frame through the committed trace's affine fit
(`data/traces/prairie_1904_footprints_s35.json`, 0.186 m a pixel) and `draft_prairie_1904.lot_frame`; the T-1842
census rows s35-2031-front ("3B brick dwelling with a stone front and a full-height bay (D), the north house of
a row of three") and s35-2031-wing ("Rear two-storey range ("rear2B") with a small frame porch").

| reading | raster (column / row) | lot frame (u toward the street, v south) |
|---|---|---|
| north wall (2027's south wall on the lot line) | row 763 | v -3.93 |
| party wall with 2033 | row 805 | v 3.87 |
| stone front (flat part) | column 915 | u 47.6 (6.85 m behind the 1904 street line, u 54.45) |
| main rear wall | column 991 | u 33.45 |
| canted bay, foot | rows 765-788 at column 915 | v -3.56..0.71 (4.2 m) |
| canted bay, face | double line at columns 909-911 | 0.93-1.1 m out, built 1.0 m |
| canted bay, south cant | rows 784-788 | about 0.75 m along the front (the north cant is overlaid by a symbol) |
| stoop (dashed outline) | column 913, rows 788-805 | the front's south part: the door is at the south end |
| rear range '2B' | columns 991-1014, row 779.5 to the party wall | u 29.18..33.45, v -0.8..3.87 |
| frame porch (yellow), not built | columns 1014-1019, rows 784-800 | about 0.9 x 3.0 m |

The draft's rectangle had the body 11.75 x 6.75 m; the sheet's is 14.15 x 7.8 m.

**A note for 2033 (T-3659, PR #2203).** 2033's front is drawn on the same column (915) and its rear wall on
the same column (991), so the two bodies are the same depth and their fronts are flush. #2203 builds 2033's
front at lot u 46.5 (12.9 m deep); this reading puts the row's front at u 47.6. Whichever lands second should
bring the row's front onto one line.

## The design (no picture)

The north house of the row mirrors 2033 across their party wall, as the sheet draws it: bay north, door south.
Heights, cornice and frieze are 2033's (T-3659), so the row's floors and its one bracketed cornice line run
through. What keeps it from being a copy: the lights over the door are segmental under K09 cornice hoods (the
brief's "hooded windows"; 2033 wears key blocks), and the bay is wider (4.2 m at the wall) with flat-headed
lights in all three faces. K07 panelled door at the head of a 1.7 m stoop; an iron picket fence on a curb with
a walk gate; flat tin roof; two stacks on the south party wall; the rear range under a flat tin deck.

## Views

`after-desktop-front.jpg`, `after-desktop-oblique-north.jpg`, `after-desktop-oblique-south.jpg`: the published
/1904/ app at 1280x800 (`node tools/qa_k01_t3660.mjs`, `QA_PART=a`), zero page errors, with
`browser-validation-after-desktop-a.json` holding load, heap and frame time.
