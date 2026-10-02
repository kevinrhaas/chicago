# Owner-name newspaper pass, north half (16th–18th St): work log

Started 2026-10-02. The follow-up to `worklog-newspapers-north.md`, which searched by address only.
Stream: `stream-newspapers-north-owners.json`, id prefix `npo-`. All records are text items,
link-only (`local: null`).

## Method

- **IA full text:** `archive.org/services/search/beta/page_production/?service_backend=fts&user_query=…`.
  The query accepts `AND year:[1884 TO 1888]` to restrict dates. Hits were located on the page with
  BookReader search-inside (`/fulltext/inside.php`; its `page` value is the `/page/nN` index) and read
  on IIIF crops of the page jp2. OCR alone was never trusted for a recorded figure.
- **Real Estate and Building Journal (Chicago), IA:** only 7 volumes are online:
  - v.25:35–26 (1883–84)
  - v.28 (1886)
  - v.33:2 (1891)
  - v.34 (1892)
  - v.37 (1895)
  - v.38 (1896)
  - v.39 (1897)

  Each volume's whole `_djvu.txt` was grepped for every target house number before "Prairie", and for
  every owner name within 160 characters of "Prairie". Issue dates come from the nearest preceding
  masthead ("CHICAGO, SATURDAY, …"), found by search-inside.
- **The Chicago Economist:** not on IA. The IA "Economist" run (`sim_economist_*`) is the London
  weekly. HathiTrust full-text search and page views return 403 to the sandbox; only its catalog API
  answers. **Untried — needs a browser or HathiTrust login.**
- **Chicago Blue Book 1904 (`chicagobluebooko1904chic`):** searched inside for every address and
  occupant. Its street-and-number section, pp. 186–187 (`n188`, `n189`), lists every Blue Book
  household on Prairie Avenue in 1904. The previous pass recorded only the alphabetical entries for
  1700, 1706 and 1708.

## Per building

### 1834 Fernando Jones (pa-1834-9)

- **Queries:**
  - IA `"Storey" "1834 Prairie"` (101 hits)
  - `"Fernando Jones" "Storey" Prairie` (439; Tribune filter)
  - `"Storey residence" Prairie` (no Chicago hits)
  - `"Fernando Jones" mansard` (245; none on the house)
  - `"1834 Prairie" AND year:[1884 TO 1888]` (11)
  - `"F. Jones" "1834 Prairie"` (58)
  - RE&BJ 1886 grep (nothing at 1834)
- **Recorded (3):**
  - Tribune 22 Jan 1883: a two-storey brick barn at the rear burned; "owned and occupied by W. F. Storey"
  - Tribune 20 Jan 1886, Storey will case: "The Prairie avenue house he lived in belonged to Jones"
    (letter of Nov. 1881)
  - Blue Book 1904 p. 187: Fernando Jones at 1834
- **Seen, not recorded:**
  - Decatur papers 28 and 30 Oct 1884 (Storey died at, and was buried from, 1834)
  - Tribune 31 Oct 1884 (funeral notice)
  - Tribune 17 Dec 1885 (Storey estate accounts, "telephone at No. 1834")
  - Tribune 7 Feb 1886 (George R. Grant, Mrs Jones's brother, at 1834)
  - Tribune 10 Dec 1892 ("Stable rear 1834 Prairie" ad)
  - 1885 Elite Directory (Jones back at 1834)
  - *Historical Review* (1908): "his handsome residence at No. 1834"
- **Answer to the lead:** Storey was Jones's TENANT, from about 1881 until his death on
  27 Oct 1884. His occupancy says nothing about a later construction date. The house is Jones's
  1866–67 Van Osdel building, which pre-dates 1883. The Joneses returned in 1885. The library's 1886
  mansard addition falls after their return; no permit for it was found (RE&BJ 1886 grep and Tribune
  1886 permit columns, OCR only).

### 1709 Kellogg (pa-1709-…-47)

- **Recorded (2):**
  - RE&BJ 5 Jan 1884, review of 1883 building: the Palmer V. Kellogg house was 50 × 90 ft, two
    storeys, basement and attic, red brick with stone trimmings, with a large barn at the rear
  - RE&BJ 23 Jan 1897: the Kellogg "homestead" passed to George W. Cass. It was a brick residence
    with a rear barn, [1]02 ft front at $600 a foot, adjoining Dexter and diagonally opposite
    Harvey (1702).
- Also on the Blue Book 1904 street list (Jesse Spalding).

### 1823 Dent (pa-1823-13)

- **Recorded:** the same RE&BJ 5 Jan 1884 passage: 40 × 80 ft, two storeys, basement and attic,
  red brick and terra cotta. Also on the Blue Book 1904 list.
- **Conflict:** the AABN 1881 permit gives 44 × 60 ft and "three-st'y and basement".

### 1812 Wheeler (pa-1812-7)

- **Queries:** RE&BJ grep ("Wheeler" near "Prairie"; "1812 Prairie").
- **Recorded (2):**
  - RE&BJ 7 June 1884 dwelling permit: three storeys, 30 × 80 ft, $25,000, entered as "No 1810"
  - RE&BJ 27 Sept 1884 barn permit: two storeys, 30 × 47 ft, $4,000. AABN printed the same
    permit with the cost only.
- The 1904 Blue Book has Lawrence A. Young (Wheeler's son-in-law) at 1812.

### 1808 Keith (pa-1808-6, predecessors pa-1804–1808-44)

- **Recorded (2):**
  - RE&BJ 27 Mar 1886: deed of 14 Jan 1886, H. M. Wells to M. W. Keith, "the premises No 1808",
    $24,000
  - RE&BJ 28 Aug 1886 permit: three storeys, 38 × 80 ft, $30,000
- The predecessor house went in 1886.

### 1726 (pa-1726–1728-…-51)

- **Recorded:** RE&BJ 6 Feb 1886. On 19 Jan 1886 Charles L. Allen sold James R. Walker a lot
  47 × 172 ft, east front, beginning 84 ft north of 18th Street, for $35,000.
- The 1904 Blue Book has James R. Walker at 1726.
- **Answer to the lead:** the brick house of the 1870s (14 rooms in 1875) was bought by Walker in
  1886 and occupied by him in 1904. Building id 51 ("frame, demolished 1880s") is wrong for this
  lot.

### 1729 Pullman (pa-1729-5)

- **Recorded:** RE&BJ 8 Aug 1891 permit: "2 and 1 story and basement brick barn and dwelling",
  $20,000, at 1729–1731.
- **Conflict:** the 1911 Sanborn reading of a stone rear garage.

### 1824 Pomeroy/Marsh (pa-1824-8)

- **Recorded:** RE&BJ 1 May 1897, Fuller to A. I. Cunningham, $50,000.
  - lot 67 × 177 ft, east front, 215 ft south of 18th Street
  - three-storey brownstone-front house, between Mrs C. M. Henderson and D. B. Shipman
  - the RE&BJ transfer list of 1 June 1895 (Marsh to Watkins) gives 67 × 176 6/10; cited in the
    notes, not recorded separately
- **Answer to the lead:** the lot depth is about 177 ft. The 171 is a misprint and the 115 is wrong.

### 1620 and 1616 (pa-1620-1904-correction)

- **Queries:**
  - IA `"1616 Prairie" Hibbard` (112)
  - `"Frank Hibbard" "1620 Prairie"` (10)
  - `"1616 Prairie" AND year:[1880 TO 1911]` (77)
  - RE&BJ grep
- **Recorded (1):** RE&BJ 8 May 1886: W. G. Hibbard took a permit for a two-storey barn,
  33 × 32 ft, at 1616.
- **Answer to the lead:** the two houses are distinct.
  - **1616:** William R. Stirling (married Alice Hibbard), 1885–1912.
  - **1620:** Robert H. Law until about 1899, then Frank Van S. Hibbard, 1901–1909.
    - 1904 Blue Book: Frank Van S. Hibbard at 1620.
    - Blue Books 1905–07: Rev. John Balcom Shaw (alphabetical list only, not checked on the image).
    - Sold to Hankins in 1909.
  - The 1922 "1616–1620 large brick residence" is the Stirling house at 1616.

### 1637 Grosvenor/Spalding (pa-1637-45) — 1904 occupant

- The 1904 Blue Book (street list p. 186 and alphabetical p. n559) has **William Gold Hibbard Jr.**
  at 1637. The Spaldings had moved to 1709 by the 1899 exchange.
- The library's "target phase unresolved" stands as to form, but the 1904 household is now known.

### 1721 Dexter (pa-1721-4) — 1904 occupant

- The 1904 Blue Book has **Henry H. Walker** at 1721 (alphabetical p. n670: "Walker Henry H. 1721
  Prairie av."). The 1911 DAR directory has Mrs Henry H. (Jessie Spalding) Walker at 1721.

### 1638 Shortall/Gregory (pa-1638-2) — index conflict

- **Queries:**
  - IA `Shortall "1638 Prairie"` (60)
  - `Shortall Hibbard Prairie AND year:[1879 TO 1881]` (44)
  - `Shortall "Prairie" residence AND year:[1883 TO 1885]` (117)
  - RE&BJ grep
- **Not recorded:** none of these concerns the 1638 building directly. They resolve the conflict:
  - The landmark-report text on IA says Shortall built a "prim Gothic frame" at 1638 in 1870.
  - Hibbard bought it in 1880 for the Gregorys. His 1881 permit at 1638 is 40 × 33 ft, an addition.
  - Shortall then bought the SW corner of 16th Street (RE&BJ 1883–84 transfers: Bartlett to
    Shortall, ½ of 92½ ft).
  - Shortall built 1600 (Inland Architect Aug. 1884: "Architect L. B. Dixon is building a residence
    for John G. Shortall… near Sixteenth street").
  - Shortall built 1608 (RE&BJ 1884 permits, 26 July, 2 Aug, 9 Aug 1884: two-storey dwelling,
    23 × 61 ft, $12,000, Burnham & Root). Henry L. Frank lived at 1608 by 1885–1904.
- **Ruling:** "Shortall" at 1638 is correct only for 1870–1880. In 1904, 1638 is the Gregory house.

### 1815 Sears/Meeker (pa-1815-12)

- **Seen, not recorded:** RE&BJ 1891–92 transfers, "Prairie av, 131 ft s of 18th st, w f 76x140":
  - Aug 30, H. S. B. and Joseph Sears to A. A. Bliss, $90,000
  - Oct 4, Bliss to Annie A. Cooper, $90,000
  - Bliss and Cooper recur in the Journal as conveyancers, so this is a financing transfer, not a
    sale. Sears still sold to Meeker in 1902.
  - Useful site-plan figure: the 1815 lot's north line is 131 ft south of 18th Street.
- 1904 Blue Book: Arthur Meeker at 1815.

### 1635 Springer flats (pa-1635-48)

- **Seen, not recorded:** RE&BJ 1896, E. Hill Turnock's plans for an eight-storey fireproof
  apartment building at 1625–1635 for Springer. It is the same project as the collection's AABN item
  (dw-aabn-1896-springer-flats-1625-1635), and it was not built.

### 1811 Coleman/Ames (pa-1811-24)

- **Queries:** IA `"1811 Prairie" AND year:[1885 TO 1907]` (65), `Coleman "Prairie" Cobb AND year:[1885 TO 1887]` (noise), `"Ames residence" Prairie` (117), RE&BJ grep (nothing).
- **Recorded (3):** Tribune 16 Apr 1904 TO RENT (16 rooms, light on all sides, 3 bathrooms, billiard and ball rooms, 2-storey stable — the house was EMPTY in spring 1904); Tribune 2 Nov 1905 (brownstone DETACHED residence and barn, reduced to $37,500; repeated 13 Nov); Tribune 16 Jan 1907 (Cowen estate of Baltimore to Joseph Fish, three-storey stone front, lot 4[6]×150, $25,000).
- **Seen, not recorded:** Tribune 1 Apr, 8 Apr, 15 Apr 1894 'For Sale 1811 Prairie-av. The Late Miner T. Ames' Residence… lot 46½…' (same campaign as the collection's May 27, 1894 ad); tenants between the Ameses and 1904: W. B. Keep (1894), Judge Lorin C. Collins (1896), Mrs David Mayer (1897–1901).
- **Answer to the lead:** 40 vs 46½ ft — the Tribune's report of the 1907 sale prints 4[6] (blotted, but not 0), agreeing with 1894's 46½; the Abendpost's 40 is the error. Use 46½ × 150 ft.

### 1635 (pa-1635-48) — the 1904 question

- **Queries:** IA `"1635 Prairie" AND year:[1904 TO 1912]` (0), `"1635 Prairie-av"` (52; all 1874–1895), `"Springer" "Prairie" AND year:[1904 TO 1911]` (Tribune/Abendpost), Blue Books 1895–1910 searched inside for 'Springer Warren' and '1635 Prairie'.
- **Recorded (1):** Blue Book 1904 — 'Springer Warren, 85 Rush'. Springer is at 1635 in every Blue Book 1895–1902, at 85 Rush from the 1903 edition (Tribune 31 Dec 1908 also has Mrs Margaret Warren Springer at 85 Rush).
- **Answer to the lead (demolition 1904–1911):** not found. The owners left 1635 in 1902; the 1904 street list has no one at 1635; the women's-club directory of 1903–04 (recorded by the third pass) is a stale entry. The house's existence in 1904 is unproven either way — the demolition window is late 1902 – 1911. No wrecking or permit item turned up.

### 1721 Dexter (pa-1721-4)

- **Queries:** IA `"Dexter residence" Prairie` (24), `"1721 Prairie" AND year:[1901 TO 1906]` (18), `"H. H. Walker" Prairie AND (alterations OR remodel OR permit) AND year:[1901 TO 1903]`, `Spalding "Prairie av" AND (alterations OR remodel OR permit) AND year:[1901 TO 1903]`.
- **Recorded (3):** Tribune 1 Jan 1898 (Pullman bought it July 1897; 105 × 275 ft to the IC; BRICK, COLONIAL style, $50,000); Tribune 28 Nov 1901 'Wirt Dexter Residence Bought by Jesse Spalding' (three storeys, 65 ft frontage; Dexter's front addition had carried the building to the STREET LINE; the sale required the buyer to build anew or MOVE BACK the brick building to the 20-ft building line); Tribune 20 Mar 1903 (H. H. Walker family; thieves 'scaled the pillars in front of the house' into an upstairs bedroom).
- **Seen, not recorded:** Tribune 1 Dec 1901 Sunday round-up (repeat); Abendpost 20 Mar 1903 (same theft); City Council proceedings 1902 (water-tax claim, 1721); Tribune 1905–06 society notes (Mrs Henry H. Walker at 1721).
- **Bearing / open:** the 1889 front addition stood on the street line in Nov. 1901 and had to be removed or set back to the 20-ft line before the Walkers moved in (by March 1903). No 1902 permit found — that is the next search (Engineering News supplements / American Contractor 1902 for 'Spalding' or 'Walker', 1721).

### 1612 (pa-1612-1) — the Frost & Granger remodel

- **Queries:** IA `"Frost & Granger" "1612 Prairie"` (19 — only the 1901 round-up and Who's Who entries for Bishop Anderson), `"Frost & Granger" "C. E. Brown"` (8, none relevant), `"Frost & Granger" "Prairie" AND year:[1900 TO 1902]` (47; AABN/Engineering News permit lists name other Frost & Granger Prairie Ave jobs, not 1612), `"1612 Prairie" AND year:[1900 TO 1902]` (16), `"Studebaker residence"` (17).
- **Nothing recorded:** no description, permit or plan of the 1901 remodel found beyond the collection's 10 Nov 1901 round-up. Side finding (not recorded): c.1899–1900 the house was used by J. A. Dowie's followers — Edward A. Flanders 'of 1612' (1900), 'free room and meals, 1612 Prairie' (Tribune 13 Jul 1900) and a church history ('a large, beautiful home at 1612 Prairie Avenue was opened' for prayer) — i.e. an institutional interlude between the Studebakers and C. E. Brown.

## Running summary

21 records so far: RE&BJ 10, Tribune 8, Blue Book 1904 3.
