# Former residents of the 1904 Prairie Avenue houses (T-3266)

The owner, 2026-10-30, on the 1904 People cards: *"is this card right, the fields are in the
osborn keith house on 1808? And you dont have anyone in the joseph coleman house? and the
meekers are in the sears house at 1815? no one in the doane house either?"*, then *"even
houses like the 1808 you should have in there as former residents the name of the people
whose house it was"*.

## The cards were right

Every 1904 card (T-3253) was checked against the PAGE IMAGES of the 1904 Blue Book's Prairie
Avenue list (scan leaves n187-n189) and the 1905 edition's (n186-n187), not only the OCR.
All 71 match the printed page. 1808 prints "Mr. & Mrs. Stanley Field" in the 1903, 1904 and
1905 editions; 1815 prints "Mr. & Mrs. Arthur Meeker" from the 1903 edition on. The model
names those houses for the families they were built for (the district markers: Osborn R.
Keith, Joseph Sears), and the cards had no place to say so.

1811 and 1827 really are empty in the 1904 and 1905 editions. David Mayer is at 1811 through
the 1903 edition and at 4706 Woodlawn av. in the 1904 edition's alphabetical list; Joseph Fish
is there by 1908. The Doanes are at 1827 through the 1899 edition, nobody is listed there
1901-1910, and the 1900 census taker walked from 1823 to 1905 without enumerating 1827 (ED 40,
sheet 4A, leaf n800).

## What was read

`read_blue_books.py` reads 16 editions (1890-1895, 1897-1899, 1901-1905, 1907-1910; 1896
and 1900 are not on the Internet Archive and the 1906 item's text returned a server error)
from each item's OCR text, twice: the street-and-number list on the PRAIRIE AVENUE pages, and
every line of the alphabetical list that gives a Prairie Avenue number from 1600 to 2140.
`blue_book_prairie_readings.tsv` is every candidate it found (4,039 rows).

`tools/build_former_residents_1904.py` then keeps a household only where the two lists agree:
its surname is in the alphabetical list at that number, and the street list prints it too, or
the alphabetical list does in a second edition. A family in two editions or fewer whose
surname fills a house within twenty numbers for five editions or more is read as that house's
family under a misread number and left out (Mrs. H. O. Stone at 2033 for 2035). Kept households
are `attested` (owner ruling 2026-10-30 on directory listings). It adds the 1900 census heads
the cards do not seat (T-3258's reading) and the district markers' name lines, which put the
family a house is named for first.

The result is `data/residents_1904/former_residents.json`: 57 houses, 116 earlier households,
and a why-empty note for the 15 houses nobody is listed in for 1904 (1601, 1609, 1611, 1613,
1615, 1623, 1630, 1635, 1811, 1827, 2100, 2108, 2125, 2127, 2130), with who came after where
an edition up to 1910 names them. `compile_scene.py` carries it into
`data/sidecars/1904/people.json` as `former_residents`; Inspect's People tab draws it
(`renderers/web/js/apps/former-residents.js`).

## Limits

- The readings are OCR. The two-list rule removes column run-ons and misread fragments, but a
  name can still be misspelt the same way twice; names are printed as the alphabetical list
  most often reads them.
- The Blue Book is a society register: servants, children and households outside society are
  not in it, and silence at a number is not vacancy.
- Before 1890 the only source used is the markers, so a house's earlier owners between its
  builder and 1890 are not listed.
