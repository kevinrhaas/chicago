# T-3171 (piece 1 of T-1895) — 1827 Prairie onto K01 from the Doane photograph

The envelope package for the John W. Doane house (1882; reported architect Theodore V. Wadskier), C10A
of the T-1837 programme. It refines the district draft (T-2330) in place under
`doane_house_1827_prairie`. T-3172 (piece 2 of T-1895) owns the corner block at the south-west corner
with its square tower, and the pavilion's pyramidal roof; T-1896 finishes the house and owns the image
gate's `matches`.

## The picture

One photograph, undated (after the house's completion in late 1882), reproduced on chicagology.com and,
smaller, on the Glessner House Museum's blog: source record `chicagology_1827_doane_exterior`, Prairie
library `cgn-1827-doane-exterior` (and `a18-gh-doane-exterior`). Committed as the image store's copy at
`data/sources/assets/doane_1827_photo_t3171/` (rights `check_required`: forms, counts and proportions are
read from it, nothing is derived from it as an asset). The Chicago Tribune's picture of the fire of
31 December 1926 (`a18-cgy-1827-fire-1927`) shows the two roofs and a stack in silhouette and is not
solved.

**It looks north-east, from the south-west.** The library records the camera north-west of the house,
facing south-east. That cannot be: the walk and the fence run along the left-hand face, so that face is
the Prairie front; the right-hand face has an open lawn beside it and the coach house beyond its far
end, which the 1911 sheet runs 5 m further south than the house; and 1823 stands 3 m north of 1827 on
the sheet, so no camera north-west of the house could see a flank. Read that way, the photograph and
the sheet agree: the porch at the front's north end (behind the street tree), the shallow pavilion,
the window bay, and the corner block at the south-west corner where the sheet draws a feature 1.1 m
out of the front and 1.5 m out of the south flank.

## The plan, from the 1911 sheet (trace s28fp-1827-b1, in the house's frame: u west toward Prairie, v south)

| part | u (m) | v (m) | built as |
|---|---|---|---|
| main block | 0 – 24.4 | 0 – 15.5 | K01's main body |
| pavilion | 24.4 – 24.97 | 5.33 – 10.79 | K08 projection, 5.46 m wide and 0.47 m out, three lights a storey |
| stone range at the north end (p1) | 24.4 – 27.2 | 0.05 – 5.05 | the photograph's porch: K01's door hood on columns with a railing, 5.0 x 2.7 m, over a landing as wide |
| brick rear range (p3) | -3.8 – 0 | 0.85 – 11.6 | K01 rear wing, two storeys, flat deck |
| corner feature at the south-west corner | to 25.64 | to 17.04 | not built (T-3172, with the tower over it) |
| rear part's steps out on the flanks | 0 – 14.6 | -1.2 – 0 and 15.5 – 17.1 | not built (open) |

## The camera

`data/reference_views/doane_house_1827_prairie/chicagology_doane_exterior.json`: level, f = 2376 px, the
eye across the avenue about 22 m south of the corner and 5.2 m up, fitted to six readings of the corner,
the pavilion, the porch and the flank's far end. Its `solve` says how and how far.

## After, from the photograph's camera

`../photo-match/doane_house_1827_prairie/chicagology_doane_exterior-side-by-side.jpg`. The match record
is `differs`: the massing, the pavilion, the porch and its balcony, the dormers, the cornice, the stacks
and the fence are fixed; the corner block and its tower, the pavilion's pyramidal roof, the south
flank's step out, the hoods, the alternating courses, the porch's arches and steps and the basement
lights' height are open.

One generator rule changed: K11 finds the stoop's foot within the stoop's own half-width of its centre
(never under 2 m), so a porch landing as wide as its hood, 5 m here, stands behind an iron fence. Every
other house's stoop is 4 m wide or less, so it reads the same vertices as before.
