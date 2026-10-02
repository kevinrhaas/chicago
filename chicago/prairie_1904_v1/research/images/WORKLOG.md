# Image & document collection — work log

Started 2026-10-01 on the owner's request (claude/lucid-gates-1w48ds → PR into dev).
Ticket: T-1821 (filed --anyway on the owner's instruction; claimed). PR #237.

## Streams

| stream file | scope | status |
|---|---|---|
| stream-1600-1700.json | 1600 + 1700 blocks of Prairie (1609–1736) | done (68 records; see worklog-1600-1700.md) |
| stream-1800.json | 1800 block (1800 Glessner – 1834) | done (204 records; see worklog-1800.md) |
| stream-1900.json | 1900 block + Michigan/Cullerton/Indiana adjacent | done (98 records; see worklog-1900.md) |
| stream-2000-2100.json | 2000 + 2100 blocks + Calumet adjacent | done (76 records; see worklog-2000-2100.md) |
| stream-streetscape.json | street views, district, aerials, maps, atlases, panoramas | done (51 records; see worklog-streetscape.md) |
| stream-drawings.json | architects' drawings, plans, permits, filings, publications | done (109 records; see worklog-drawings.md) |

## First pass — result (2026-10-01)

605 records after cross-stream merging, covering all 62 buildings: 349 made by 1911, 41 in 1912–1930, and 215 later. 126 have local derivatives (about 36 MB, public domain or no known restrictions only). Each stream's worklog lists what was searched per source and per building, with hit counts. Read it before re-searching a source.

**Thinnest coverage (records):**

| building | records | what was found |
|---|---|---|
| 1709 Williams (pre-1904) | 1 | |
| 1726–1728 predecessor | 1 | |
| 1630 | 2 | maps only |
| 1635 | 2 | maps only |
| 2027 | 2 | no image anywhere |
| 1609 | 3 | only the post-1910 loft that replaced the house |
| 1611 | 3 | only the post-1910 loft that replaced the house |
| 1709 Kellogg | 3 | Rand McNally 1893 strip only |
| 2109 Roloson | 3 | |
| 1923 Kellogg | 4 | shared street views only |

**Resolved here:**
- **Sanborn between 1886 and 1911 for 16th–22nd Prairie (LoC):** none. LoC's 1894–97 Chicago volumes are vols 9–16 and A–F (outlying districts). Its 1906 Vol. 1 South Division is the "congested district" north of 12th Street. The central South Division volumes of the 1890s/1905 are not at LoC; try the Chicago History Museum, the Newberry, or UIC Special Collections.
- **Dedup:** different plates, crops or pages of one catalogue record are kept as separate records. `build_images.py` merges only identical items found by two streams (page, image, local copy and kind all equal).

## Second pass — chicagology, all 82 Prairie Avenue house pages (2026-10-01)

`stream-chicagology-north.json` and `stream-chicagology-south.json` add the per-house pages the
first pass had not opened (37 of 82), and every uncollected image on the rest. They also add the
Robinson 1886 address crops, Tribune and Inter Ocean notices, and page-text facts. Every item is
link-only; the viewer shows them as remote thumbnails. Records for addresses with no building
record in the library are placed on the site plan by lot.

**The best of it:**
- **Chicago Tribune, 9 Jan 1898:** a strip of entrance drawings for 1905, 1906, 1923, 2035 and
  2108. It holds the first images of 1923 and of 2108, and shows 2035 as a detached house with a
  wide veranda.
- **2027:** the only image is the Robinson crop, showing a brick house on a 60-ft lot.
- **1919:** a third near-period photograph of the enlarged house.

**Chicagology's address arrows are not always right.** Read the printed numbers on the plate
instead:
- **2108 "Empty lot":** the arrow is on the future 2110; 2108 stood.
- **2125 "Empty lot":** a frame building is shown on that lot.
- **2109:** the arrow lands on the printed 2107.
- **2021:** the arrow is on 2017.
- **Shared crops:** 1919/1923, 2001/2003, 2009/2011 and 2031/2035 share crops or arrows.

**Other conflicts and notes:**
- **1906 vs 1900:** the 1898 drawing of 1906 has a side bay and porch, so the mansard photo
  labelled 1906 (`a19-cgy-1906-keith-photo`) likely shows 1900.
- **1905:** the "Hallway" image is a mirrored copy of the Artistic Houses plate.
- **2018 S. Prairie:** the Herrick house, not 2018 S. Calumet.

## Third pass — newspapers for the north half's thin buildings (2026-10-02)

`stream-newspapers-north.json`: 43 records, all link-only. The per-building log is
`worklog-newspapers-north.md`.

**Where the material came from.** Internet Archive's full-text search over the Chicago Tribune
microfilm (`per_chicago-daily-tribune_*`, 1860s–1920s) was by far the richest source. It also
covers the Abendpost, Blue Books and trade weeklies. Chronicling America has no Inter Ocean and
gave 4 records.

**Findings for the 1904 model.** None of these has been applied to library.json or
building-research.json yet.

- **1609 and 1611:** two-storey, nine-room frame houses. 1609 was to rent in Oct 1904.
- **1612:** remodelled for C. E. Brown by Frost & Granger in 1901.
- **1620:** 16 rooms, with a two-storey double brick stable (1908).
- **1700 and 1706:** 1901 permit for two three-storey brick houses, 36 × 66 ft each. American
  Artisan gives 36 × 60.
- **1702:** brownstone, three storeys, footprint 55 × 90 (1899).
- **1708:** A. A. Carpenter Jr. was the 1904 occupant.
- **1709 Kellogg:** completed 15 Oct 1883, not "c.1882". Jesse Spalding's household in 1904;
  three-storey brick or brownstone, 18 rooms.
- **1630:** the Brust family, 1876 to at least 1917. This resolves "owner unresolved".
- **1635:** the Springer family, occupied through 1903–04.
- **1824:** Connecticut brownstone; a two-storey brick barn with rooms over it.
- **1811:** 16 rooms plus billiard and ball rooms, and a two-storey stable.
- **1736:** 1875 permit for a two-storey-and-basement brick house.
- **1726:** a brick house and brick stable, occupied 1875–1915.

**Conflicts with what the library or collection holds:**

- **1635 "likely absent":** it was occupied in 1903–04 and is gone by 1911. Its material also
  conflicts: brick in 1886 and 1893, frame in 1895.
- **1726–1728 (id 51, "frame, demolished 1880s"):** the newspapers show a brick house occupied
  1875–1915.
- **`dw-aabn-1889-mcbirney-1736-permit`:** belongs to 1625 (Hugh J. McBirney, the son). The
  father stayed at 1736.
- **1620:** the 1922 "large brick residence" ad is 1616, because the 1911 Sanborn has no house
  at 1620.
- **Lot and footprint figures that disagree:**
  - 1811: 40 ft vs 46½ ft
  - 1824: 67 × 171 vs 67 × 115
  - 1700/1706: 36 × 66 vs 36 × 60
- **1702:** two storeys (1879) vs three (1899). The 1878 addition explains it.
- **1625–1635 (the AABN 1896 flats item):** not built, and on the east side, not the west.
- **1834:** no newspaper item on its form. The lead is Wilbur F. Storey's 1884 funeral "in his
  residence, No. 1834 Prairie Avenue", which bears on the construction date.

## Findings that bear on the 1904 model

Each needs a building-research.json update or a ruling. None has been applied to library.json yet.

- **2126 Robbins:** the Inland Architect plate of May 1905 shows the house finished, with bare trees. Complete by winter 1904–05; the earlier Hamill house on the lot was razed in 1904.
- **2013 Reid:** the coach house dates from 1910, so it was absent in 1904.
- **2108–2110:** one shared Kimball/Rees barn stood at the rear in 1904.
- **2110 Rees:** permit 1988 (18 June 1888) gives the dwelling as 20 × 80 × 44 ft. The National Register nomination (2007) gives a lot of 24.08 × 178.5 ft.
- **No 17th Street through Prairie:** the 1600 and 1700 blocks were continuous.
- **1700/1706 townhouses:** razed in 1954.
- **Measurements from period notices:**

  | house | dimensions | other details | date and source |
  |---|---|---|---|
  | 1808 O. R. Keith | 38 × 80 ft | granite front, 3 storeys | 1886 notice |
  | 1901 O. R. Keith | 52 × 82 ft | | 1881 |
  | 1912 Moulton | 45 × 80 ft | | 1882 |
  | 1919 Murray | 32 × 58 ft | (or 32 × 63) | 1884/1885 |
  | 1815 Sears | 35 × 75 ft | | 1879 |
  | 1823 Dent | 44 × 60 ft | | 1881 |
  | 1827 Doane | 64 × 94 ft | | Tribune 2 Nov 1882 |
  | 1936 Thompson/Allerton | 66'6" × 94' | tower 73 ft, barn 39 × 80, lot 193 × 175 | Tribune 30 Oct 1869 |

- **1905 Field, from Hunt's principal-floor plan (LoC ppmsca-58353, read from the master TIFF):**
  - depth about 75'6"
  - entrance front about 56 ft
  - Drawing Room 18'6" × 29'6"
  - conservatory chord 37'4"
- **Second Presbyterian, HABS IL-328 (the 1900 rebuild, i.e. its 1904 state):**
  - tower 122'-8½"
  - gable 87'-8¼" (sheet 9 says 67'-8¼" — a discrepancy within the set)
- **Roadway:** 32 ft curb to curb (Tribune 1891, via the Glessner House blog).
- **2140 Tucker/Smith tower roofs:** an iron-crested form and a conical-spire form are both photographed. The conical-spire photo must be dated before the 1904 roof is chosen.
- **1905 Field fence:** a scroll pattern in 1893, tall vertical bars by c.1905 (DN-0003324).
- **2018 Calumet Wheeler–Kohn:** still had its bracketed cornice in 1904.

## Conflicts to adjudicate

- **1827 Doane loss:** burned 1 Jan 1927 (Tribune, chicagology) vs razed 1936 (library).
- **Second Presbyterian spire:** blew down 1929 (1976 landmark report) vs hipped roof removed after 1959 (1974 NRHP form). It stood in 1904 either way.
- **McBirney plate (Art Institute "1736"):** the evidence points to about 1625 Prairie. The record is kept with no building id.
- **The image labelled 1900 vs 1906 Prairie:** the 1900 stream identifies the Glessner blog's "1900 PA" photo as 1900; chicagology labels the same image 1906.
- **2031 Dewey vs Tolman occupancy:** check before changing 2031's front.
- **Murdoch house:** an older Art Institute catalogue says 2130 S. Calumet; every other source says Prairie.
- **Index conflicts:**
  - Shortall at 1600, 1608 or 1638
  - Hibbard at 1616 or 1701
  - the 1712 Lowden addition
  - Ryerson mqc 4609: 1811 or 1808?
- **New architect lead:** Charles A. Alexander for work on the Dexter (1721) and Harvey (1702) houses (Inland Architect obituary, June 1888).

## Best leads for the next pass

0. **Owner-name full-text searches.** The third pass searched by address only. Owner-name searches over IA's Tribune run, plus the Chicago Economist and Real Estate and Building Journal runs, are untried (`worklog-newspapers-north.md`).

These are mostly blocked from a sandbox, so they need a browser or a reference request:

1. **Chicago History Museum images:** the ICHi originals behind the Chicagology and Tyre images, and the Charles R. Clark negatives (ICHi-071912, i71913, i70232, i71911, Box 4). Cloudflare blocked every automated request.
2. **Library of Congress Hunt collection, unprocessed lot 2010:100:** the rest of the Marshall Field house drawing set; the plan held is "No. 2".
3. **Newberry Robinson 1886 atlas (G4104.C6 1886 .R6a, "No Copyright – United States"):** full plates for 16th–22nd Streets.
4. **UIC building-permit ledgers:** the method works (IIIF manifests), but the street-index cards are needed. Missing permits:
   - Keith 1808 (1886)
   - Kimball 1890
   - Murray 1884
   - Doane and Dent 1881
   - Robbins 1903–04
   - Reid 1894
5. **Tyre, *Chicago's Historic Prairie Avenue* (Arcadia 2008):** trace its photo credits to their holders. Pages:
   - pp. 13, 17, 18, 26, 27, 30, 31, 32, 35, 36, 39, 44–45 (Rand McNally 1898 elevations), 48, 61, 110
6. **Chicago Daily News rotogravure "This Is Prairie Avenue", 25 Aug 1951,** plus Chicago Daily News 19 Jan 1940 (2021 High).
7. **City paving tables:** Chicago Department of Public Works annual reports 1880/1898/1901, to settle the 1904 roadway material.
8. **HathiTrust (403 to the sandbox all session):** Building Budget, Western Architect 1902–04 (the 1815 Heun remodel), Andreas vol. 3 full text.
9. **Second Presbyterian:** Shaw's 1900 drawings. **1700/1706 townhouses:** Shepley, Rutan & Coolidge drawings.
