# Newspaper pass, south half (18th–22nd St) and adjacent: work log

Started 2026-10-02. Stream: `stream-newspapers-south.json`, id prefix `nps-`. Link-only records
(no downloads; page images read as IIIF crops in a scratch directory only).

## Method

Same as `worklog-newspapers-north.md`, with two refinements:

- **IA full text** (`archive.org/services/search/beta/page_production/?service_backend=fts&user_query=…`)
  for `"<number> prairie"` and owner-name phrases; hits located inside each item with BookReader
  search-inside (`https://<server>/fulltext/inside.php?item_id=…&doc=…&path=…&q=…`), which returns the
  LEAF number and word boxes; the passage read on a IIIF crop of the leaf's jp2
  (`iiif.archive.org/image/iiif/3/<id>%2f<id>_jp2.zip%2f<id>_jp2%2f<id>_<leaf4>.jp2/<x,y,w,h>/1400,/0/default.jpg`).
- **Leaf ≠ page index.** The `/page/n<index>` of `catalog_url` is the BookReader index, taken from
  `https://<server>/BookReader/BookReaderJSIA.php?id=…&itemPath=…&server=…&format=json&subPrefix=…`
  (leaf → index). Tribune microfilm items: index = leaf. The 1904 Blue Book: index = leaf − 1
  (the street page 'Prairie Avenue' p. 187 is leaf 189 = n188).
- **Chicago Blue Book street directory.** The Blue Book (IA `chicagobluebooko<year>chic`) has a section
  listing society households street by street, house by house. For 1904 this is printed pp. 186–187
  (n187–n188) for Prairie Avenue. It answers most 'occupants unresolved' questions in one place.

## Per building

### Blue Book 1904, Prairie Avenue street pages (all south-half buildings)

- **Recorded (2):** p. 186 (n187: east side 1901–2009) and p. 187 (n188: 2009–2140 both sides).
- **Absences checked in the alphabetical section of the same volume:** Thomas Murdoch at the
  **Lexington hotel** (leaf 609/n608); Mrs. Mark Kimball at the **Lakota hotel** (leaf 577/n576);
  John B. Sherman (d. 1902) not listed. So no society household at 2100, 2108 or 2130 in 1904.
- A. B. Dewey is at **2631** Prairie in 1904 (p. 188) — the AIC catalogue's '2631' is right and the
  Inter Ocean's '2031' (1887 drawing) is wrong; 2031 is Samuel A. Tolman.

### 2115 Kelley / Armour (pa-2115-19)

- **Queries:** IA `"2115 prairie"` (265 hits; c. 120 Tribune, 15 Blue Books 1890–1915, Abendpost,
  St Luke's reports, Ames phone books = noise). Owner phrases `"Armour residence" "Prairie avenue"`,
  `"P. D. Armour" "Prairie" "stable"`, `"David Kelley" Prairie` (noise: FTS does not AND terms).
- **Recorded (3):** Tribune 7 Jan 1901 (obituary: 'large square house with stone front and mansard roof',
  tall elms in the lawn); Tribune 8 Jul 1928 'Famous Homes' PHOTOGRAPH of the front (19-room stone
  residence, elaborate rear stables; rooming house by 1928); Tribune 24 Mar 1928 (sale; lot 58 × 178).
  Plus the Blue Book 1904 (Mrs. Philip D. Armour).
- **Seen, not recorded:** Tribune 23 Aug 1897 ('the stone curb and the steps of the Armour mansion …
  polished so white'); Tribune 12 Feb 1902 (Mrs. P. D. Armour Jr. to occupy the family residence while
  Mrs. Armour travels); 1904 society notes (13 Feb, 19 and 24 Apr: Mrs. Armour in residence); Tribune
  25 Dec 1937 (to be razed for a parking lot — already held via chicagology); Tribune 18 Jan 1942
  (retrospective: torn down); Abendpost 7 Jan 1901 ('palastartigen Wohnhause'); St Louis Post-Dispatch
  22 Jul 1888 '2115 Prairie' brick dwelling 20 × 114 = St Louis, rejected.
- **Bearing:** 1904 = Mrs. Armour's house: square stone-fronted block, 2 storeys + iron-crested
  mansard, 19 rooms, rear stable, lot 58 × 178, elms in the front lawn.

### 2130 Murdoch (pa-2130-42)

- **Queries:** IA `"2130 prairie"` (129 hits: Blue Books 1890–1915, AJA member lists 1895–1900, Abendpost
  1899 tax list, Tribune 18 items, 1925 ENR World Book Co. printing plant); `"Thomas Murdoch" "Prairie
  avenue"` (220), `"Thomas Murdoch" residence Prairie`, `"Thos. Murdoch" residence`, `"Murdoch" "Cobb"
  residence 1889`, `"2130 Prairie" Cobb` (no permit or description of the 1890 Cobb house found).
- **Recorded (2 + the street pages):** Blue Book 1904 alphabetical (Thomas Murdoch at the Lexington hotel);
  Tribune 31 Dec 1909 (will: household effects 'at the Murdoch residence at 2130 Prairie avenue and at the
  Metropole hotel, where he died').
- **Seen, not recorded:** Blue Books 1890–1902 (Murdoch at 2130; 1892 also prints '2130 Calumet' for
  Thos. Murdoch — the source of the AIC 'Calumet' conflict: a Blue Book misprint, the same volume also
  has him at 2130 Prairie); Blue Books 1911–15 (Julius B. Cone, Miss Jane Murdoch; 1915 Forsyth family);
  Tribune 8 Jul 1909 (assessment; snippet only); Tribune 27 Apr 1910 (the Cones to occupy 2130);
  ENR 25 Jun 1925 (World Book Co., 2130 Prairie, sketches for a 10-storey printing plant — the house's end).
- **Bearing:** stood in 1904, furnished, the Murdoch family's town house while Murdoch lived in hotels;
  no society household listed there 1903–05.

### 2108 Mark Kimball (pa-2108-40)

- From the street pages: 1903 tenants Alex. H. Seelye and the Miner T. Ames family; 1904 no entry; 1905
  Dr. & Mrs. Frank Allport. Mrs. Mark Kimball at the Lakota hotel (Blue Book 1904, n576). 2108 stood and
  was a let house; it was unoccupied by a society household during the 1904 edition's compilation.

### 2031, 2033, 2035 (pa-2031-nrhp, pa-2033-nrhp, pa-2035-nrhp) — the 1904 occupants

- **Answer (Blue Books 1903, 1904, 1905 street pages):** 2031 = Mr. & Mrs. **Samuel A. Tolman**
  (there 1873–1919; Tolman died at 2031 on 4 Jun 1919); 2033 = the **Frederick R. Otis** family —
  F. R. Otis died there 17 Dec 1903, and the 1904 will gave the 'homestead at 2033' to his widow
  **Mrs. Emeline Otis** (sons Charles T. and Lucius J. Otis also at 2033); 2035 = **Mrs. Horatio O.
  Stone** (there 1891–c.1912; son Robert E. Stone's family kept the house Jan–Mar 1904).
- **Queries:** IA `"2031 prairie"` (80), `"2033 prairie"` (c. 60), `"2035 prairie"` (c. 150).
- **Recorded (4):** Tribune 27 Feb 1904 (Otis will: homestead at 2033 to the widow); National Police
  Gazette 22 Jan 1887 (2035 'Mrs. Stone's mansion … the "steamboat" house, so called from the numerous
  pretty galleries of fancy woodwork'); Tribune 8 Feb 1934 (2035: corner building, 30 rooms, 9 baths);
  Tribune 4 Feb 1904 (R. E. Stones occupying Mrs. H. O. Stone's home).
- **Rejected:** Tribune '2033 Prairie' rent ads of 9 Nov 1881, 9 Sep 1902 and 4 Sep 1904 — all read
  **2933** on the page image (OCR error; the 1904 one even says 'cor. house'). Abendpost 16 Jun 1900
  '2031 Prairie' piano for sale (occupancy noise).
- **Seen, not recorded:** Tribune 18 Dec 1903 (F. R. Otis death notice, 2033); Tolman wedding notices
  1885 (2031); Tolman death 5–6 Jun 1919; Charles Raymond Otis death at 2033, Feb 1920; Tribune 1882
  (a horse 'in barn rear 2035' — a stable at 2035); Abendpost 16 May 1894 (2035, health department);
  Tribune 14 Feb 1943 (retrospective: the H. O. Stones 'lived at 2035 Prairie avenue for many years').
- **Bearing / conflict:** 2035 was the corner (21st St) END of the row, described as a 'mansion' with
  wooden galleries (1887) and a broad columned veranda (1898 vignette); 30 rooms by 1934. The library's
  'trio of equal 25-ft limestone townhouses' fits 2031 and 2033 better than 2035.
- **Dewey:** the A. B. Dewey house (W. W. Clay, 1887) was at **2631** Prairie (Blue Books 1903–05) —
  the AIC '2631' is right, the Inter Ocean '2031' wrong; a20-aic-ia-dewey-residence-drawing-1887 does
  not show 2031.

### 2027 Cobb-associated (pa-2027-37)

- **Households:** William B. Walker (Silas B. Cobb's son-in-law) c. 1884–1901, Cobb living with them
  1890–1900 (Tribune 28 Jan 1900, 8 Apr 1900); **1903–05: Mrs. John Jay Borland, Chauncey Blair Borland,
  Bruce Borland** (Blue Books; Tribune 1902–04 society notes, the Borland reception 'at the Borland home,
  2027' 15 Nov 1904); Kuppenheimer family by 1907–11; to rent 1911; Nystrom 1923.
- **Queries:** IA `"2027 prairie"` (215).
- **Recorded (3):** Tribune 16 Apr 1911 (15-room residence to rent, $300/month); Tribune 3 May 1912
  (large 2-storey brick garage with 4 living rooms above — the rear building); Tribune 8 Mar 1923 (old
  residence sold; lot 50 × 178).
- **Seen, not recorded:** Tribune 28 Jan 1900 (Cobb at 'the front window of his house, 2027'), 15 Apr 1900
  (the residence not in Cobb's will — not opened, timed out); Abendpost 4–5 Apr 1900 (Cobb dying/died at
  his son-in-law Walker's, 2027); 1904 Borland society notes (14 Jan, 22–24 Apr, 13 and 22 May, 17 Jul).
- **Conflict:** lot 50 ft (1923) vs '60' printed on the Robinson 1886 crop.

### 2021 Adams / High (pa-2021-36)

- **Queries:** IA `"2021 prairie"` (c. 70); `"High residence" Prairie`, `"Benjamin Adams" Prairie` (noise).
- **Recorded (1):** Tribune 30 Aug 1942 'Wrecking 2021 Prairie-av.' (Italian marble and tile fireplaces,
  oak trim and floors … — the house was demolished in 1942; the library has no demolition date).
- **Rejected:** Tribune 10 and 13 Aug 1893 permit 'Dr. Frank Johnson will erect a … and basement brick
  dwelling and [barn at] 2021 Prairie avenue … $20,000' — printed '2021' on the page, but Dr. Frank S.
  Johnson lived at **2521** Prairie (Blue Books 1903–05): a misprint for 2521.
- **Seen, not recorded:** James L. High's death at 2021 (4–5 Oct 1898); Mrs. High's death 1911;
  1904-05-15 home wedding notice; Shirley T. High residence 1932 (taxes).

### 2109 Roloson (pa-2109-41)

- **Queries:** IA `"2109 prairie"` (c. 60).
- **Recorded (1):** Tribune 11 Feb 1883 (the house bought for the Rolosons by J. H. Dunham; Roloson spent
  c. $4,000 on it and bought it for $21,000).
- **Rejected:** '2109 Prairie' rent ads 5 Nov 1893 (= 2409 on the image) and 17 Apr 1905 (= 4949).
- **Seen, not recorded:** Tribune 7 Jun 1899 (already held as cgs headline); 16 Jun 1921 ('Robert Roloson of
  2109 Prairie … whose house is noted for its open latchstring'); 14 Jun 1933 'Parking lot, 2109 Prairie'
  (gone by 1933, as the library says).

### 2108 Mark Kimball (pa-2108-40)

- **Queries:** IA `"2108 prairie"` (c. 80).
- **Recorded (1):** Tribune 28 Feb 1904 (= 21 Feb 1904): '11 r. stone front house … new plumbing; 2
  bathrooms; hardwood floors; hot water heat … good brick barn' (Trotter & Kimball).
- **Seen, not recorded:** the same house as '10 room stone front' in eight 1903 ads (May–Dec); Tribune and
  Abendpost 25 Jul 1902 (Mrs. M. Ames of 2108, tax review); 1891 Kimball funeral notices at 2108;
  Allport notices 1906–1911; 'barn rear 2108' 1909; Tribune 17 Dec 1922 (sale 'from Mark Kimball').
- **Bearing:** the house stood empty and to let in early 1904 — explains the missing 1904 Blue Book entry.

### 2112 Rothschild (pa-2112-39)

- **Queries:** IA `"2112 prairie"` (c. 70).
- **Recorded (2):** Tribune 1 Jan 1913 (beautiful DETACHED house, 20 large light rooms, 5 bathrooms, steam
  plant); Tribune 31 May 1910 (brick barn to rent, $40).
- **Seen, not recorded:** Tribune 6 and 8 Sep 1893 (Rothschild funeral 'at the gilt-trimmed residence' —
  headline already held); 1911–12 rooms/suites to rent at 2112 (rooming era); 1895 'Mrs. Levy P. Mayer,
  No. 2112' (unexplained, not opened).

**Method note (from here on):** the FTS endpoint accepts Lucene filters: `"<n> prairie" AND
collection:pub_chicago-daily-tribune` restricts to the Tribune run (2126: 5,193 hits overall, 37 in the
Tribune), and `AND year:1904` narrows by year. Plain owner-name queries without such a filter return
noise because the backend ORs unquoted terms.

### 2036 Buckingham (pa-2036-38)

- **Queries:** IA `"2036 prairie"` (c. 60).
- **Nothing recorded.** The '2036 Prairie' stable and brougham ads of 1903–04 read **2936** on the
  page images (24 Mar and 6 Apr 1904); the 1934 '2036' rooming-house ad is the 2035 ad (OCR); the
  Abendpost 7 Jul 1904 tax list gives 'Silas B. Cobb, 2036' (a misprint). Society notes 1912–1923 and the
  1937 Kate Buckingham article (headline already held) only confirm occupancy ('the old mansion her
  father had built at 2036'). Blue Books 1903–05: E. Buckingham & drs., Clarence Buckingham.

### 1923 Kellogg (pa-1923-35)

- **Queries:** IA `"1923 prairie"` (noise from '1923. Prairie Oil'); Tribune hits are society and the 1912
  burglary (paintings worth $25,000 stolen from Mrs. C. P. Kellogg) — nothing on the building.
- **Resolved by the Blue Books:** Mrs. C. P. Kellogg and Mrs. Lois Kellogg at 1923 in 1904 and 1905;
  Tribune 27 Aug 1902 (Mrs. Kellogg 'removed yesterday to her residence at 1923'). The house stood and
  was occupied in 1904. 1905 electric brougham for sale at 1923 (Tribune 12 and 30 Oct 1905).

### 2126 Robbins (pa-2126-20)

- **Queries:** IA `"2126 prairie"` (5,193 — World Book Co. noise), restricted to the Tribune (37);
  `"Edward F. Robbins"` (127); `"E. F. Robbins" AND collection:pub_chicago-daily-tribune` (31);
  `Robbins AND "Prairie av" AND … year:1903/1904` (113/96, noise); `"Mann, MacNeille"`, `"Mann &
  MacNeille"`, `"MacNeille & Lindeberg"` (only the 1905–06 Inland Architect plates and other works);
  `"E. F. Robbins" AND year:1904` → the City Council proceedings.
- **Recorded (3):** Tribune 3 Nov 1901 (Robbins buys the Hamill residence: 'three-story brick, built some
  years ago', lot 50 × 180, $25,000); Tribune 22 Apr 1909 (Armour buys from W. H. Johnson: 'three story
  brick structure containing fourteen rooms', lot 58 × 178; with 17 Jan 1909, the Bingham sale);
  City Council proceedings, Jan–Mar 1904 (water-tax rebate to E. F. Robbins, 2126 Prairie).
- **Seen, not recorded:** Hamill society notices at 2126, 1890–1898 (Charles D. Hamill; his mother died
  there Feb 1895); DAR directory 1904 'Hamill, Susan W. (Mrs Chas. D.) 2126 Prairie' (a stale address);
  A. Watson Armour notices 1910–13; Tribune 8–9 Jan 1916 (2126 sold — not opened); 1920s–50s World Book Co.
- **Not found:** any 1903–04 building permit, razing notice or completion notice for 2126 in the
  Tribune run (the permit columns were not found under 'Robbins' or '2126'); the Real Estate and Building
  Journal on IA stops in the 1890s; no Chicago Economist run surfaced on IA. The completion date
  therefore still rests on the May 1905 Inland Architect plate.
- **Open question:** 1901 'three-story brick' (Hamill) vs 1909 'three story brick … fourteen rooms'
  (Robbins). Both fit; whether the Mann, MacNeille & Lindeberg house of 1904 replaced or remodelled the
  Hamill house needs the permit ledger (UIC) or the Inland Architect text.

### 2140 Tucker / Byron L. Smith (pa-2140-21) — the tower roofs

- **Queries:** `"2140 prairie" AND collection:pub_chicago-daily-tribune` (85: almost all society notes of the
  Byron L. Smiths 1890–1922, Hamlines 1919–21).
- **Recorded (1, with local image):** Tribune 15 Jul 1928 'Famous Homes' PHOTOGRAPH: the house with three
  tall CONICAL SPIRES, high iron fence, 'To lease'.
- **Bearing on the roof question:** cresting-crowned towers are dated pre-1881 and 1898 (collection);
  conical spires are dated by July 1928 (this record). The change falls between 1898 and 1928; no
  newspaper item dating it was found (searched the Smith notices for 'remodel', 'roof', 'improvement';
  nothing). The 1904 roof therefore remains open; the Smiths were in residence 1904 (Blue Book).
- **Seen, not recorded:** Tribune 17 Feb 1940 ('Byron L. Smith residence, 2140 Prairie avenue, which was
  built in the 1880's' — conflicts with 1876 Van Osdel/Tucker; dining-room salvage story, already
  represented); 1906/1908/1909 '2140 Prairie' flat ads (other buildings: OCR of 2140 S. Prairie flats?
  not checked).

### 'Famous Homes' (Chicago Sunday Tribune photo series, May–Aug 1928)

Found by `"Famous Homes" AND collection:pub_chicago-daily-tribune` (40 items; the series ran 27 May –
19 Aug 1928). Prairie Avenue subjects: **1905 Field (3 Jun)**, **2115 Armour (8 Jul)**, **2140 Smith
(15 Jul)**, 2919 Logan (22 Jul, out of scope), **1945 Corwith (29 Jul)**, **1701 Hibbard (5 Aug)**,
**1800 Glessner (12 Aug)**, and 19 Aug (Spalding homestead, '1700' — not opened). The south-half ones are
recorded with local images (public domain, pre-1929); **1701, 1800 and the 19 Aug item are leads for the
north stream** and were not recorded here.

### 2009 Meyer (pa-2009-17), 2013 Reid (pa-2013-29)

- **Queries:** `"2009 prairie"` / `"2013 prairie"` AND Tribune collection (29 / 20 hits).
- **Nothing recorded** beyond the Blue Book street pages (2009: Mrs. M. A. Meyer & dr., E. F., Albert,
  Carl and Abraham Meyer; 2013: Mr. & Mrs. William H. Reid). 2009: Allen family 1886, Hodges 1882 (an
  earlier house), Meyer wedding 1897; furnished rooms 1910–11; Tribune 5 Feb 1933 '15 rm … fine interior
  brick res. 2009 Prairie' (OCR, not opened). 2013: Reid notices 1895–1909, Reynolds 1921–35.
