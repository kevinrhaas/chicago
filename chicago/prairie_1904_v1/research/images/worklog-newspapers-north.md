# Newspaper pass, north half thin buildings (16th–18th St): work log

Started 2026-10-02 (re-run of the pass lost to the 2026-10-01 restart). Stream:
`stream-newspapers-north.json`, id prefix `np-`. Link-only records (no downloads).

## Method

- **Chronicling America via the loc.gov API** (`/collections/chronicling-america/?q=…&fo=json`),
  OCR read from each hit page's `word-coordinates-service … &full_text=1` text and grepped
  for the address. Chicago titles indexed there (facet `location_city:chicago`): Chicago Daily
  Tribune 1872–1963 (partial), Chicago Tribune 1864–72, Chicago Daily Tribune 1860–64, Press
  and Tribune, Abendblatt der Illinois Staats-Zeitung, The Broad Ax, The Appeal, The
  Conservator. The Inter Ocean did not appear in the Chicago facet. Coverage of the Tribune
  is far from complete: "prairie avenue" hits per decade are 5,839 (1870s), 1,815 (1880s),
  1,839 (1890s), 605 (1900s).
- **Internet Archive full text** (`archive.org/services/search/beta/page_production/?service_backend=fts&user_query=…`)
  turned out to index the complete **Chicago Tribune 1860–1920s on microfilm** (`per_chicago-daily-tribune_*`,
  c. 1,800 issues per 5 years), plus AABN, Engineering Record, school directories and Blue Books. This was
  the productive source. Hits were located with BookReader search-inside (`/fulltext/inside.php`), and every
  recorded ad or notice was read on the page image (IIIF crop of the page jp2); the OCR is often garbled.
  `catalog_url` = `/details/<id>/page/n<index>/mode/1up` (index checked against the page image).
- Phrase queries `"<house number> prairie"` (new numbers, and the pre-1881 old numbers known
  from the chicagology page texts: 846 = 1630, 854 = 1702, 874 = 1726, 882 = 1736,
  894/896 = 1816), then owner-name queries.

## Per building

### 1609 and 1611 (pa-1609-1904-correction, pa-1611-1904-correction)

- **Queries:** LoC `"1609 prairie"` (5 hits, none Chicago-relevant: Milwaukee and South Bend Prairie Streets) and `"1611 prairie"` (9;
  one Chicago hit: Abendblatt 20 Jul 1898, Margareth Murphy 'wohnende' at 1611 — occupancy only, not recorded).
  IA full text `"1609 prairie"` (36 hits, 7 Tribune) and `"1611 prairie"` (110, 58 Tribune).
- **Recorded (5):** Tribune 30 Oct 1904 (1609: 2-storey, 9-room FRAME residence to rent, $20); Tribune 31 Oct
  1897 (1609: 9-room dwelling, $16); Tribune 12 Feb 1888 (1609 + 1611: 50 ft with frame dwellings, a site for
  flats); Tribune 3 May 1896 (1609 + 1611: 2-storey frame houses, new plumbing, $30 each); Tribune 14 Apr 1895
  (1611: 2-storey and basement frame house, 9 rooms and bath, $27.50).
- **Seen, not recorded:** Tribune 26 Feb 1888 (repeat of the Newbury sale offer); Tribune 31 Dec 1893 (1611,
  '2-story and bas[ement]: 9 rooms', OCR only); room-to-rent ads at 1609 (1881-06-12, 1882-05-07, 1882-11-19)
  and 1611 (1881-06-19, 1882-05-28/06-09/06-25, 1884-09-21, 1893-03-26, 1898-02-06, 1900-09-16) — show the
  houses as rooming/boarding houses through 1900; Engineering Record 12 Aug 1905 (Strauss warehouse 'to be
  built at 1609 Prairie' — duplicates the AABN record already in the collection); 1611 used-car and truck
  dealer ads 1916–18 (the loft era); 'Mr. and Mrs. Joseph Fish, 1611 Prairie avenue' society notes
  1912 and 1914 (unexplained — the loft is said to cover 1609–1611 by 1910; check whether 1611 survived).
- **Bearing:** both houses stood in 1904-era use; 1609 is fixed as a 2-storey, 9-room frame house in October
  1904; 1611 was its twin (2 storeys + basement, frame, 9 rooms). Lots c. 25 ft each (50 ft for the pair).

Correction to the above: the 'Joseph Fish, 1611 Prairie' society notes are a misprint or OCR slip for 1811 —
the Day Book (10 Jun 1914) and Dziennik Chicagoski (24 Jul 1913) put Joseph Fish at **1811** Prairie.

### 1612 Goodman/Studebaker (pa-1612-1)

- **Queries:** LoC `"1612 prairie"` (74 hits nationwide; Chicago-relevant: Washington Times 27 Apr 1904 wire
  story; Dziennik Chicagoski 8 Feb 1900, Edward A. Flanders of 1612 suing Dowie; syndicated Peruna ads
  1900–03 for 'Captain John H. Lyons, 1612 Prairie Ave.'; Wisconsin Vorwärts 1896 is Milwaukee's Prairie
  St. — rejected). IA full text `"1612 prairie"` (316 hits, 52 Tribune).
- **Recorded (5):** Washington Times 27 Apr 1904 (Brown household holding the house 'in a state of siege' —
  the 1904 occupants); Tribune 10 Nov 1901 'Prairie Avenue Improvement' (Brown's alterations through
  **Frost & Granger**; also 1709, 1702→1700/1706, 1721 etc.); Tribune 17 Mar 1895 ('large double modern,
  15 rooms … also large barn'); Tribune 6 Jun 1897 ('18-room modern dwelling … newly decorated'); Tribune
  26 Nov 1922 (lot 50 × 177).
- **Seen, not recorded:** Tribune Brown-divorce reports 26 and 29 Apr, 5–6 May, 11 and 20 Sep, 5 Oct,
  4 Nov 1904 (occupancy and litigation only; 20 Sep: she 'stripped her home … of valuables'); Tribune
  14 Mar 1905 (Bishop Anderson bought the Brown residence, deed filed, possession 1 Apr 1905); Studebaker
  society notices 1881–1892 (Mr and Mrs P. E. Studebaker, 1612); servant-wanted ads; Anderson-era notices
  1908–1921; 1931 rooming-house notices (18 football-player roomers, Evening Star 15 Aug 1931).
- **Bearing:** the 1904 house is the Studebaker house as altered for Charles E. Brown by Frost & Granger
  (1901): broad 'double' house of 15–18 rooms with a large barn, on a 50 × 177 lot.

### 1620 (pa-1620-1904-correction)

- **Queries:** LoC `"1620 prairie"` (8; Abendblatt 1895 robbery of Robert H. Law near his home, 1898 Law
  obituary — occupancy only). IA `"1620 prairie"` (91, 28 Tribune).
- **Recorded (4):** Tribune 26 Apr 1908 (16 rooms, 3 baths, 'all outside light', 100 ft ground, 2-storey
  double brick stable with living rooms); Tribune 6 Apr 1909 (Hibbard sells, lot 73 × 177, east front);
  Tribune 11 Jun 1899 (residence taken at $50,000 in a Law property deal); Tribune 22 Oct 1922 (1616–1620,
  109 × 177, 'large brick residence, double garage').
- **Rejected:** Tribune 28 Apr 1883 'For Rent—1620 Prairie' is **1626** on the page image (OCR error) —
  'three-story and basement, 14 rooms; 2-story barn' belongs to 1626 (no building id; lead for that lot).
  1878 '1620 Prairie-av., near Thirty-fourth-st.' ads are pre-renumbering addresses far south.
- **Bearing:** 1620 in 1904 = a large detached brick house (Frank Hibbard), lot 73 ft, brick double stable.
  Note the frontage conflict: 73 ft (1909 deed) vs '100 feet ground' (1908 ad).

### 1630 (pa-1630-50)

- **Queries:** LoC `"1630 prairie"` (3: Brust death notice 1893; Broad Ax 1924 'late home at 1630 Prairie'
  of a Black civic leader — 1920s rooming era, not recorded). IA `"1630 prairie"` (59: school directories,
  Blue Books, 4 Tribune servant ads/letters, AABN 1905 Newhouse).
- **Recorded (2):** Abendblatt 11 Sep 1893 (Peter Brust's death at 1630); Chicago school directory 1905/06
  (Louisa Brust at 1630; series 1881–1917).
- **Nothing found on the building's form.** 'Mr. and Mrs. Arthur Meeker, 1630 Prairie' (Tribune 21 Jun 1908
  society) is presumably an error for 1815.

Correction to 1620: the 1911 Sanborn (map_frontages.csv) shows **no front dwelling at 1620**, only its rear stable,
and a 2½-storey brick house at 1616 — so the 1922 '1616–1620 … large brick residence' is the 1616 house; the
1620 house went between the 1909 sale and 1911. The 1922 record's notes say so.

### 1635 Forsyth (pa-1635-48)

- **Queries:** LoC `"1635 prairie"` (15; Chicago: Illinois Staats-Zeitung 23 Jul 1894, Mrs Warren Springer of
  1635). LoC `"warren springer"` Chicago (223; nothing further at 1635). IA `"1635 prairie"` (93, 48 Tribune;
  plus Blue Books, the women's-clubs directory, AABN 1896, W. T. Stead's *If Christ Came to Chicago* 1894
  list of property owners). IA `"Warren Springer" prairie` (1,300; first 100 scanned).
- **Recorded (4):** Staats-Zeitung 23 Jul 1894; Tribune 19 Mar 1893 (15-room brick house, plate glass, large
  barn); Tribune 28 Jul 1895 (99-year lease, 70 × 200 ft, 'two-story frame building', 8-storey apartment
  intended); Women's Clubs directory 1903–04 (Mrs W. Springer at 1635). The AABN 26 Sep 1896 Turnock
  flat-building item was found too but is already in the collection (dw-aabn-1896-springer-flats-1625-1635);
  my duplicate was removed. That record's 'if built…' is answered: not built; and 1625–1635 is the EAST side.
- **Seen, not recorded:** Tribune 20 Apr 1886 (1635, 10 rooms, brick — cited in notes); 99-year-lease ads
  Apr–Oct 1892 (70 × 160 ft, 'suitable for nice apartment house'); Tribune 1888 notices (a missing man of
  1635), 1895-11-22 (Springer's Canal St fire; he had gone home to 1635), 1898-07-20 (Mrs Springer 'at her
  home, 1635'); Blue Books 1895–1902; Engineering News 2 Jun 1883 (Hart L. Stewart died at 1635 — i.e. the
  Stewart family before the Herricks? the chicagology page has Herrick 1874–85; unresolved); 1870s
  directories with '1635 Prairie' are pre-1881 numbering (a different, far-south address).
- **Bearing:** REVERSES 'uncertain; likely absent': the house stood and was the Springer home in 1903–04;
  gone by the 1911 Sanborn. Lot 70 ft (depth 160 or 200). Material in conflict (brick ×2 vs frame ×1).

### 1700, 1706 Glessner townhouses; 1702 Staples/Harvey; 1708 Thorne (pa-1700-52, pa-1706-53, pa-1702-43, pa-1708-54)

- **Queries:** LoC `"1700 prairie"` (19 Chicago; none on this house), `"1702 prairie"` (2 Chicago: Abendblatt
  1896 Harvey family; 1897 Moritz Stein 'at 1702' — unexplained, not recorded), `"854 prairie"` (Tribune 1879
  barn permit and 1880 Harvey reception — already on chicagology), `"1706 prairie"`, `"1708 prairie"` (0).
  IA `"1700 prairie"` (497; almost all Science Research Associates 1940s), `"1702 prairie"` (89, 25 Tribune),
  `"1706 prairie"` (80), `"1708 prairie"` (176, 33 Tribune). Glessner House blog feed: '1706', '1700 Prairie',
  'townhouses', 'Thorne', 'Carpenter' — posts already in the collection or with nothing on the buildings
  ('Frances Glessner Lee moves to the north side' only calls 1700 'an elegant Georgian Revival townhouse').
- **Recorded (8):** Engineering News 25 Apr 1901 (permit: two 3-storey brick residences 36 × 66 ft, $30,000,
  Shepley, Rutan & Coolidge, builder J. Rodatz); American Artisan 27 Apr 1901 (each 36 × 60, three storeys,
  one Robinson No. 60 furnace each); Blue Book 1904 (Blewett Lee at 1700; J. G. M. Glessner at 1706;
  A. A. Carpenter Jr. at 1708); Abendpost 16 Jul 1907 (Thorne buys the three-storey 1708, 28 × 177, from Mrs
  Mary W. Keith — 'always rented since completion'); Tribune 10 Feb 1899 (1702: brownstone, 3 storeys,
  20 rooms, 55 × 90 ft, lot 102½ × 177; Glessner to tear it down); Tribune 26 Dec 1898 (1702: 'large brown
  stone front house, brick stable').
- **Seen, not recorded:** Tribune 8 May 1898 (Harvey house transferred by master in chancery), 12 Feb 1899
  (repeat), Blue Books 1890–97 (Harvey family at 1702), 1903–1915 (Glessner at 1706; 1907 'Lee Blewett,
  1706' — check), Tribune 1903–1911 society notes (Carpenter at 1708 1903–06; Thornes from 1907), Abendpost
  9 Feb 1900 (1708 empty, pipe thieves), 8 Oct 1910 ('unbewohnten Gebäude Nr. 1708' — unoccupied in 1910?
  contradicts the Thornes' 1908–11 society listings; not checked on the image), Tribune 5 Dec 1926 (1708 sold
  for $160,000 — store and flat building era), Tribune 1888 (Henry K. Elkins at 1706 — the pre-1899 house
  numbering on the Harvey frontage; unresolved).
- **Bearing:** 1700/1706 = two 3-storey brick colonial houses, each 36 ft wide × 60–66 ft deep, on the
  102½-ft Harvey lot, occupied in 1904 by the Lees and George Glessners. 1708 = a 3-storey rental house on
  a 28-ft lot, Carpenter tenancy in 1904.

### 1709 Williams / Kellogg (pa-1709-46, pa-1709-…-47)

- **Queries:** LoC `"1709 prairie"` (1: Abendblatt 28 Oct 1893, Charles Schwartz died at 1709 — occupancy
  only). IA `"1709 prairie"` (175; the FTS backend returned 502 at first, retried with 50 per page).
  Nothing found for the Williams house (pre-1883) beyond the replacement date.
- **Recorded (5):** Tribune 19 Oct 1883 (Kellogg house 'but just completed', occupied from 15 Oct 1883);
  Tribune 18 Mar 1904 (Jesse Spalding died at 1709 — the 1904 household); Abendpost 24 Jul 1908
  (brownstone house, ground 101 × 220, sold to Philo Otis); Abendpost 18 Aug 1908 (three-storey brick,
  18 rooms, lot 99 × 213–243, south 14 ft to stay open); Tribune 11 Oct 1936 (to be torn down).
  Also the 1901 'Prairie Avenue Improvement' article (Spalding 'greatly improved' it), recorded under 1612.
- **Seen, not recorded:** Abendpost 27 Jan 1899 (1637↔1709 exchange: Spaldings acquire 1709); Kellogg
  widow and Schwartz society/funeral notices 1889–1894; Tribune 16 Sep 1894 (1709 to rent, OCR garbled);
  Blue Book 1899 (Mrs Jessie D. Crane and Mrs Edgar M. Doolittle at 1709 — tenants between Schwartz and
  Spalding); Otis notices 1909–1930.
- **Bearing:** the Kellogg house = completed Oct 1883; in 1904 the Spalding home, 3 storeys, brick with
  brownstone (front), 18–20 rooms, 99–101 ft lot with a 14-ft open strip on the south.

### 1726–1728 (pa-1726–1728-…-51)

- **Queries:** LoC `"1726 prairie"` (16 Chicago: 1893 Walker robbery attempt, Staats-Zeitung/Abendblatt;
  The Citizen 1894–95 AOH lists 'John Clarke, Pres, 1726 Prairie av' — a puzzle, perhaps a rear tenant),
  `"1728 prairie"` (0), `"874 prairie"` (0). IA `"1726 prairie"` (155, 60 Tribune), `"1728 prairie"` (21;
  '1728' Pullman furnishings 1921 is 1729).
- **Recorded (1):** Tribune 27 Feb 1893 (fire in James R. Walker's two-storey brick stable at 1726).
- **Seen, not recorded:** Tribune rent ads Apr 1886 and Mar 1887 ('1726 Prairie-av.—10 rooms'); Walker
  society notices 1890–1915; Blue Books 1890–1915 (James R. Walker at 1726, Mrs James M. Walker at 1720);
  Tribune 22 May 1904 'Mrs. Hugh McBirney, 1726 Prairie' (presumably 1736 misprinted); 1922–33 commercial use;
  Tribune 1924/1927 '1708 to 1726 Prairie-av., 220 feet frontage' (later redevelopment).
- **Conflict:** the evidence shows a BRICK house (10 rooms in 1886, 14 rooms in 1875) with a brick stable at
  1726, occupied 1875–1915 — not a frame double house demolished in the 1880s. Re-examine id 51.

### 1736 Ingraham/McBirney (pa-1736-49)

- **Queries:** LoC `"1736 prairie"` (3: Day Book 1913 fire 'in home of Mrs. Emma Marr, 1736 Prairie',
  1914 Dr John Harris — post-McBirney, not recorded), `"882 prairie"` (1: the 1875 permit). IA
  `"1736 prairie"` (89).
- **Recorded (1):** Tribune 8 Aug 1875 permit (Gen. [Henry] Strong, two-storey and basement brick, 23 × 32
  [or 52] ft, at old 882 = 1736).
- **Seen, not recorded:** Blue Books 1890–1911 (Hugh McBirney at 1736 incl. 1904; Hugh J. McBirney at
  **1625** from 1891); Tribune 12 Apr 1904 ('the residence of his father, Hugh McBirney, 1736'); Tribune
  16 Nov 1910 and Abendpost (McBirney died at 1736, Nov 1910); Tribune 31 Dec 1905 (George Day McBirney
  divorce); Tribune 1883-09-23 cook wanted at 1736.
- **Conflict:** the collection's AABN 1889 permit 'H. J. McBirney, three-st'y dwell.' (dw-aabn-1889-
  mcbirney-1736-permit) belongs to **1625** (Hugh J. McBirney's house from 1891), not 1736.

### 1811 Coleman/Ames (pa-1811-24)

- **Queries:** LoC `"1811 prairie"` (6 Chicago: Citizen 18 Jan 1890 Ames death; Dziennik 1891 theft; Abendblatt
  1894 W. B. Keep of 1811; Day Book 1914 and Dziennik 1913 Joseph Fish). IA `"1811 prairie"` (300; most are
  1920s publishers' addresses).
- **Recorded (3):** Tribune 1 Sep 1905 (16 rooms with billiard and ball rooms, 2-storey stable); Abendpost
  16 Jan 1907 (Baltimore estate sells to Joseph Fish, 40 × 150 ft); Abendpost 19 Jan 1921 (built 'over thirty
  years ago by the architect Kopp' [= Cobb?]; sold to the Midland Press for business use).
- **Conflict:** lot 40 × 150 (1907) vs 46½ ft (1894 ad already in the collection).

### 1816 Henderson (pa-1816-33)

- **Queries:** LoC `"1816 prairie"` (2: Henderson death notices Jan 1896), `"894 prairie"`, `"896 prairie"`
  (1880 'Mrs. T. W. Harvey, 894 Prairie' — a misprint for 854). IA `"1816 prairie"` (275, 92 Tribune).
- **Recorded (2):** Tribune 8 Dec 1895 (house partly burned, $10,000, mostly contents; second-floor bedroom);
  Tribune 11 Sep 1896 (barn at the rear burned).
- **Seen, not recorded:** Tribune 8 Feb 1896 (Henderson's will: widow gets the homestead); tax list 4 Jul
  1903 (Mrs C. M. Henderson, 1816); society notes 1886–1921; dog/bicycle ads 'in barn, 1816' 1888–93.
  '1816' Meeker notices (1907, 1913) are misprints for 1815.
- **Bearing:** stood and was occupied by Mrs Henderson in 1904 (to c.1921); close 'unresolved'.

### 1823 Dent (pa-1823-13)

- **Queries:** LoC `"1823 prairie"` (0). IA `"1823 prairie"` (229, 54 Tribune).
- **Recorded (1):** Tribune 2 Dec 1922 (lot 56 × 140 [depth OCR uncertain]).
- **Seen, not recorded:** Dent notices 1893–1911 (club meetings at the residence); Tribune 1911 Dent
  estate sale; 1919–22 school use; 1922 offices to let; Abendpost 20 Nov 1909 'Wohnhaus von J. W. Doane,
  1823 Prairie' (Doane was 1827 — misprint); Tribune 12 Apr 1894 '1823 Prairie-av., 10 rooms' rent ad (OCR
  garbled, conflicts with Dent occupancy; not checked).

### 1824 Pomeroy/Marsh (pa-1824-8)

- **Queries:** LoC `"1824 prairie"` (6 Chicago: Staats-Zeitung 1883 Mrs G. B. Marsh; Dziennik 12 and 16 Dec
  1908 garage explosion; Day Book 1915 'Hotel Rish, 1824 Prairie'). IA `"1824 prairie"` (214).
- **Recorded (2):** Tribune 14 Feb 1897 (Cunningham buys; Connecticut brownstone; Marsh spent $50,000;
  lot 67 × 171); Tribune 12 Dec 1908 (fatal fire in the two-storey brick barn/garage with living rooms above).
- **Seen, not recorded:** rent ads Jun 1896–Jan 1897 ('brown stone house with 67 ft. and barn'); Tribune
  1 Jan 1898 annual review (lot 67 × 115 — conflict); Tribune 2 Sep 1881 (permit '…at 1824 Prairie avenue,
  to cost $3,500' — presumably the Marsh barn, already in the collection from AABN); Schwartz family at 1824
  1891–93 (tenants); Cunningham society notes 1904–1912; 1915 rooming house.

### 1834 Fernando Jones (pa-1834-9)

- **Queries:** LoC `"1834 prairie"` (5 Chicago: Jones as oldest settler 1893; Staats-Zeitung 3 Nov 1884
  'Wilbur F. Storey's funeral at No. 1834 Prairie Avenue' — Storey's home?; Dziennik 1911 death; Tribune 1873
  is pre-1881 numbering). IA `"1834 prairie"` (283).
- **Nothing recorded.** All hits are occupancy/society (Jones family 1885–1911, Mrs Jones died there Dec
  1905, 90th birthday 1910), tax assessments (Tribune 12 Jun 1897, 11 Aug 1903) and 1920s–30s business
  use; nothing on the house's form beyond what the collection has. **Lead:** the 1884 Staats-Zeitung puts
  Wilbur F. Storey's funeral 'in der Wohnung des Verstorbenen, No. 1834 Prairie Avenue' — check whether Storey
  rented 1834 before Jones, which bears on the disputed construction date.

## Summary

43 records (after removing one duplicate). Sources: IA Chicago Tribune microfilm (27), Abendpost (5),
LoC Chronicling America (4: Washington Times, Staats-Zeitung, Abendblatt, Tribune 1875), Blue Book 1904 (3),
school / women's-club directories (2), Engineering News and American Artisan (2). Rights: all pre-1929 public
domain except the 1936 Tribune item (link only). No downloads (site at size budget).

Best leads not finished:
- IA full text for owner names (not just addresses) — e.g. `"Spalding" "Prairie"`, `"Henderson residence"`,
  `"Glessner" townhouses 1901–02`, `"Studebaker residence"` — and the Inter Ocean, which is not in
  Chronicling America and was not found on IA as a run.
- The Real Estate and Building Journal on IA (`realestatebuildi*` items) — only one volume surfaced.
- Economist (Chicago) and Inland Architect news columns 1900–05 were not re-searched here (the 1600–1700
  stream grepped Inland Architect already).
