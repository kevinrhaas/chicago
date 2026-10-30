# 1904 Prairie Avenue households (T-3253)

The owner, 2026-10-30: *"you don't have very many of the people on the people cards in 1904 for
prairie I think you should research all of those and make sure you put the families there in the
houses with all of the people in the house, including staff and servants where possible"*.

Before this, `data/residents_1904/households/` held one card, the Glessners at 1800 (two people).
It now holds 71 cards and 183 people, every one at a structure that stands in the 1904 scene.

## What was read

| Source | What it gave | How it was read |
|---|---|---|
| Chicago Blue Book for 1904 (`chicago_blue_book_1904`), Prairie Avenue street list, printed pp. 186-187 | the base of every card: the households the register listed at each number from 1600 to 2140 | the Internet Archive's OCR, through its page text and full-text search; agrees entry for entry with the Prairie library's independent reading (`chicago/prairie_1904_v1/data/occupancy_candidates.csv`) |
| Chicago Blue Book for 1905 (`chicago_blue_book_1905`), pp. 185-187 | the later bracket: canvassed from September 1904, so a household in both editions is taken to be in its house on 1 July 1904 | the same OCR route; its first leaf's reading stops at 2101, so the younger Pikes and 2120 were not checked against it |
| Glessner House, family page (`glessner_house_family_page`) | the children of the two Glessner children's houses, with birth years: John (1898) and Frances (1903) Lee at 1700; Elizabeth (1899), Frances (1900), John (1902) and Emily (1904) Glessner at 1706 | already cited by the Glessner card; read again |
| Glessner House blog on Mattie Williamson (`glessner_house_blog_mattie_williamson_2020`) | the Glessners' cook, February 1892 to December 1912 apart from 1897-98, and the size of their live-in staff, eight | read whole |
| Wikipedia on W. W. Kimball, Arthur Meeker (Jr.), Norman B. Ream, Frank O. Lowden, Marshall Field III, Frances Glessner Lee | wives' own names, a few occupations, and children with birth dates where the article gives them (Arthur Meeker jr., 1902; Marshall Field III, 1893, and Henry Field, 1895) | read for those facts only; tier 4 |

The Blue Book is a society register. It prints married couples as "Mr. & Mrs.", unmarried
daughters only as "& dr." or "& drs.", grown sons and other adults by name, and **no young
children and no servants**. So:

- a wife is named as the book names her ("Mrs. Howard E. Perry") unless another source gives her
  own name;
- an unnamed daughter is one line, "Miss Longini", whose note says the name is the book's form of
  address and not a record; "& drs." is one line for two or more;
- a grown son, or another adult of the surname, is read as a son only where he is listed under a
  widow or a couple of the same name, and his note says the book does not state it;
- a person of another surname in the house is a `household_member` whose relation is not printed;
- a child is added only where a source names them and dates their birth before the scene, and is
  `inferred` (in the parents' house is read from the parents' listing);
- a person the Blue Book names at the address is `attested` (the owner, 2026-10-30, on directory
  listings: *"Those sound attested to Me, it's a well defined document that says they lived at a
  certain address, it's very specific"*), including a person first listed in the 1905 edition,
  whose note says their presence on 1 July 1904 itself is not documented; a 1904 person the 1905
  edition drops says so in their note.

## The bracket

A household in both editions is `present`, attested (the owner's ruling above). A household the 1905 edition replaces is
`uncertain` (inferred): 1604 (Rev. Wm. Otis Waters in 1905), 1620 (Rev. John Balcom Shaw), 2005 (Mrs. O. R.
Keith). Three are simply missing from the 1905 reading: 1712, 2001 and 2120.

## What has no card, and why

- **Numbers with no Blue Book listing** (1601, 1609, 1611, 1613, 1615, 1623, 1630, 1635, 1811,
  1827, 2100, 2108, 2125, 2127, 2130, and the 16th Street station): the register is selective,
  so silence is not vacancy; these stay empty until another source names someone. 1635's empty
  house is the subject of `docs/RESEARCH/forsyth-1635-2443/`.
- **Listed numbers with no standing structure**: 1904 (Mr. & Mrs. Walter W. Keith) and 1936
  (Mr. & Mrs. S. W. Allerton, Robert H. Allerton). Neither house is in the 1904 model, and the
  people directory refuses a home that does not stand.
- **New in 1905 only**: 2108, Dr. & Mrs. Frank Allport. Not carried: nothing puts them there by
  July 1904.
- **Servants, apart from the Glessners' cook.** The 1900 and 1910 US censuses name every live-in
  servant, coachman and nurse on the street, with ages and birthplaces. They are the next source
  for these cards; this session could not reach the census page images (the container's network
  policy refuses archive.org), and a summary of a handwritten page is not a reading of it.

## The cards

| No. | Household | People | Inferred | 1 July 1904 |
|---|---|---|---|---|
| 1600 | Shortall | 1 | 0 | present |
| 1604 | Shortall | 2 | 0 | uncertain |
| 1608 | Frank | 2 | 0 | present |
| 1612 | Brown | 3 | 0 | present |
| 1616 | Stirling | 2 | 0 | present |
| 1619 | Perry | 2 | 0 | present |
| 1620 | Hibbard | 2 | 0 | uncertain |
| 1621 | Hamline | 3 | 0 | present |
| 1625 | McBirney | 2 | 0 | present |
| 1626 | Longini | 3 | 0 | present |
| 1628 | Einstein | 3 | 0 | present |
| 1634 | Bellas | 4 | 0 | present |
| 1636 | Johnston | 3 | 0 | present |
| 1637 | Hibbard | 2 | 0 | present |
| 1638 | Gregory | 4 | 0 | present |
| 1700 | Lee | 4 | 2 | present |
| 1701 | Hibbard | 3 | 1 | present |
| 1706 | Glessner | 7 | 5 | present |
| 1708 | Carpenter | 2 | 0 | present |
| 1709 | Spalding | 2 | 0 | present |
| 1712 | McKinlock | 2 | 0 | uncertain |
| 1720 | Walker | 1 | 0 | present |
| 1721 | Walker | 2 | 0 | present |
| 1726 | Walker | 2 | 0 | present |
| 1729 | Pullman | 2 | 1 | present |
| 1730 | Otis | 3 | 2 | present |
| 1736 | McBirney | 3 | 1 | present |
| 1800 | Glessner | 3 | 0 | present |
| 1801 | Kimball | 2 | 0 | present |
| 1808 | Field | 2 | 0 | present |
| 1812 | Young | 2 | 0 | present |
| 1815 | Meeker | 3 | 1 | present |
| 1816 | Henderson | 1 | 0 | present |
| 1823 | Dent | 2 | 0 | present |
| 1824 | Cunningham | 2 | 0 | present |
| 1828 | Shipman | 1 | 0 | present |
| 1834 | Jones | 2 | 0 | present |
| 1900 | Keith | 5 | 2 | present |
| 1901 | Ream | 3 | 0 | present |
| 1905 | Field | 1 | 0 | present |
| 1906 | Keith | 1 | 0 | present |
| 1912 | Lowden | 2 | 0 | present |
| 1919 | Field | 4 | 2 | present |
| 1923 | Kellogg | 2 | 0 | present |
| 1945 | Corwith | 2 | 0 | present |
| 2000 | Clark | 2 | 0 | present |
| 2001 | Free | 2 | 0 | uncertain |
| 2003 | Hoyt | 2 | 0 | present |
| 2005 | Wood | 2 | 0 | uncertain |
| 2009 | Meyer | 6 | 0 | present |
| 2010 | Grey | 3 | 0 | present |
| 2011 | Lamb | 2 | 0 | present |
| 2013 | Reid | 2 | 0 | present |
| 2017 | McBean | 5 | 0 | present |
| 2018 | Herrick | 5 | 0 | present |
| 2021 | High | 2 | 0 | present |
| 2026 | Stettauer | 3 | 0 | present |
| 2027 | Borland | 3 | 0 | present |
| 2031 | Tolman | 2 | 0 | present |
| 2033 | Otis | 5 | 0 | present |
| 2035 | Stone | 1 | 0 | present |
| 2036 | Buckingham | 3 | 0 | present |
| 2101 | Pike | 5 | 0 | present |
| 2109 | Roloson | 1 | 0 | present |
| 2110 | Keith | 2 | 0 | present |
| 2112 | Rothschild | 3 | 0 | present |
| 2115 | Armour | 1 | 0 | present |
| 2120 | Gorton | 2 | 0 | uncertain |
| 2123 | Hulbert | 1 | 0 | present |
| 2126 | Robbins | 2 | 0 | present |
| 2140 | Smith | 5 | 0 | present |

`data/jaunts/_names/place-names.json` is unchanged: its rule is that a name restates the family
the structure record already names, so a household on these cards does not rename a house.
