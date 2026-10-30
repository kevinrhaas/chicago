# 1904 Prairie Avenue households: the 1900 census read for staff and children (T-3258)

T-3253 put 71 Blue Book households on the 1904 Prairie Avenue cards and left every card
saying the same thing: the Blue Book names no servants and no young children, and the 1900
census, which would, had not been read. This ticket reads it.

## The source

Twelfth Census, 1900, population schedules, NARA T623 roll 245, Internet Archive item
`12thcensusofpopu245unit` (record: `data/sources/census_1900_chicago_t623_roll245.json`).
The roll is handwritten and has no usable OCR, so the page images were read directly.

The enumeration districts were found from the street names written down each sheet's
margin, not from a finding aid (the Steve Morse ED tool returns nothing for Prairie Avenue):

| ED | Leaves | Sheets | What it walks |
|----|--------|--------|---------------|
| 36 | n665-n669 | 1A-3A | Prairie Avenue 1600-1638, both sides, with rear houses |
| 40 | n794-n822 | 1A-15A | Prairie Avenue 1700-2115, interleaved with Calumet and Indiana Avenues |

`census_1900_prairie_reading.tsv` is the line-by-line reading: leaf, ED, sheet, line, house
number as written (`Rear NNNN` for the coach house), name, relation, sex, birth month and
year, age, marital state, birthplace, occupation, and a note. A `?` marks the hand at its
hardest. Only the Prairie Avenue lines that bear on a 1904 card were transcribed.

## How it went onto the cards

`spec.py` says, house by house, which census line is which card person and which lines are
left off and why; `apply.py` (run once, against the T-3253 cards) does the rest:

- **Live-in staff** in the house (cooks, maids, laundresses, nurses, governess, butler,
  steward, valet, housekeeper, companion) go on as `servant`, graded **inferred**, with the
  occupation as written, birth, birthplace and year of immigration, and a `census_1900`
  block giving the line. The census is four years before the scene and servants moved
  often, so a servant is evidence of who kept the house in 1900, not of 1 July 1904.
- **Stable staff** in the rear building (coachmen, grooms, horsemen, a footman, a helper) go
  on the same way. The coachman's wife and children are named in his note rather than
  carded: they lived in the coach house, not the house.
- **Children** the Blue Book never prints go on as `son` / `daughter`, graded **inferred**.
- **People already on a card** (head, wife, grown sons and daughters the Blue Book names)
  keep their grade and gain the census as a second source, a `census_1900` block and a note
  with their birth and birthplace.
- **Daughters the Blue Book prints only as "& dr."** are not carded twice: the census names
  are added to that line's note, with a plain statement that the book does not say which
  daughter it means.
- **Left off, with the reason in the card's "who is not on this card" note:** grown children
  and in-laws the 1904 Blue Book does not list at the house; boarders; family members who
  died before 1904 (Philip D. Armour, January 1901; William Gold Hibbard, 1903); rear-house
  families with no stable trade written.

Each card's "who is not on this card" note now says what the census found at the house.

## What was found

| House | Family (1904) | Staff added | Children added | Card people given the census | 1900 |
|-------|---------------|-------------|----------------|------------------------------|------|
| 1600 | Shortall | 1 | 0 | 1 | same family |
| 1604 | Shortall | 2 | 4 | 2 | same family |
| 1608 | Frank | 2 | 0 | 2 | same family |
| 1612 | Brown | 0 | 0 | 0 | another household |
| 1616 | Stirling | 0 | 3 | 2 | same family |
| 1619 | Perry | 3 | 0 | 2 | same family |
| 1620 | Hibbard | 0 | 0 | 0 | not found |
| 1621 | Hamline | 5 | 2 | 3 | same family |
| 1625 | McBirney | 4 | 2 | 2 | same family |
| 1626 | Longini | 1 | 2 | 2 | same family |
| 1628 | Einstein | 1 | 0 | 2 | same family |
| 1634 | Bellas | 3 | 0 | 3 | same family |
| 1636 | Johnston | 2 | 0 | 3 | same family |
| 1637 | Hibbard | 0 | 0 | 0 | not found |
| 1638 | Gregory | 0 | 2 | 4 | same family |
| 1700 | Lee | 0 | 0 | 0 | the Lees were at 1623 |
| 1701 | Hibbard | 2 | 0 | 0 | same family |
| 1706 | Glessner | 0 | 0 | 0 | not found |
| 1708 | Carpenter | 0 | 0 | 0 | not found |
| 1709 | Spalding | 5 | 0 | 2 | same family |
| 1712 | McKinlock | 2 | 0 | 0 | same family |
| 1720 | Walker | 1 | 0 | 1 | same family |
| 1721 | Walker | 0 | 0 | 0 | another household |
| 1726 | Walker | 6 | 3 | 2 | same family |
| 1729 | Pullman | 3 | 0 | 1 | same family |
| 1730 | Otis | 3 | 0 | 1 | same family |
| 1736 | McBirney | 3 | 0 | 2 | same family |
| 1800 | Glessner | 5 | 0 | 0 | same family |
| 1801 | Kimball | 7 | 0 | 2 | same family |
| 1808 | Field | 0 | 0 | 0 | another household |
| 1812 | Young | 7 | 2 | 2 | same family |
| 1815 | Meeker | 0 | 0 | 0 | another household |
| 1816 | Henderson | 1 | 0 | 0 | same family |
| 1823 | Dent | 1 | 0 | 2 | same family |
| 1824 | Cunningham | 2 | 0 | 0 | same family |
| 1828 | Shipman | 4 | 0 | 1 | same family |
| 1834 | Jones | 3 | 0 | 0 | same family |
| 1900 | Keith | 4 | 0 | 4 | same family |
| 1901 | Ream | 5 | 2 | 2 | same family |
| 1905 | Field | 5 | 0 | 1 | same family |
| 1906 | Keith | 3 | 0 | 1 | same family |
| 1912 | Lowden | 12 | 2 | 2 | same family |
| 1919 | Field | 0 | 0 | 0 | another household |
| 1923 | Kellogg | 1 | 0 | 0 | same family |
| 1945 | Corwith | 6 | 0 | 2 | same family |
| 2000 | Clark | 4 | 0 | 2 | same family |
| 2001 | Free | 0 | 0 | 0 | not found |
| 2003 | Hoyt | 0 | 0 | 0 | not found |
| 2005 | Wood | 0 | 0 | 0 | not found |
| 2009 | Meyer | 5 | 0 | 6 | same family |
| 2010 | Grey | 4 | 0 | 2 | same family |
| 2011 | Lamb | 3 | 0 | 2 | same family |
| 2013 | Reid | 2 | 1 | 2 | same family |
| 2017 | McBean | 4 | 0 | 5 | same family |
| 2018 | Herrick | 0 | 0 | 0 | another household |
| 2021 | High | 0 | 0 | 0 | family away; no staff listed |
| 2026 | Stettauer | 1 | 0 | 1 | same family |
| 2027 | Borland | 0 | 0 | 0 | another household |
| 2031 | Tolman | 2 | 0 | 2 | same family |
| 2033 | Otis | 4 | 0 | 5 | same family |
| 2035 | Stone | 4 | 0 | 1 | same family |
| 2036 | Buckingham | 5 | 0 | 2 | same family |
| 2101 | Pike | 7 | 0 | 3 | same family |
| 2109 | Roloson | 3 | 1 | 1 | same family |
| 2110 | Keith | 4 | 2 | 2 | same family |
| 2112 | Rothschild | 5 | 2 | 2 | same family |
| 2115 | Armour | 7 | 0 | 1 | same family |
| 2120 | Gorton | 0 | 0 | 0 | another household |
| 2123 | Hulbert | 0 | 0 | 0 | another household |
| 2126 | Robbins | 0 | 0 | 0 | another household |
| 2140 | Smith | 0 | 0 | 0 | another household |
| | **total** | **179** | **30** | | |

Several families were away on the census day and the enumerator wrote their names with the
other columns blank, listing only the servants in the house: the Glessners at 1800 (at The
Rocks, New Hampshire), the McKinlocks at 1712, Mrs. Henderson at 1816 and the Cunninghams at
1824 (Highland Park), the Joneses at 1834, Mrs. Kellogg at 1923 ("abroad"), the Stettauers
at 2026 ("in Europe"), and J. L. High at 2021 ("at Lakeside", nobody else listed).

At 1800 the census lists a cook, Kate Ryan, while the museum's account has Mattie Williamson
as the Glessners' cook from 1892 to 1912. With the family in New Hampshire on the census day,
the likeliest reading is that Kate Ryan cooked for the house while Mattie was away with them;
both are on the card, and Kate Ryan's note says so.

## Not found, and why

- **1700 (Lee):** in 1900 Blewett and Frances Lee were at **1623** Prairie (ED 36, sheet 1A,
  lines 14-19) with their son John and three servants. Those servants kept a different house
  and are not carried to 1700; the Lee card's note names them.
- **1620, 1637, 1706, 1708, 2001, 2003, 2005:** not found in the sheets read. ED 40 does not
  open at 1700; the 1700 block's east side before 1702 and the 2001-2005 numbers may sit on
  sheets not read, or in another district. A William G. Hibbard household with six servants
  is enumerated in ED 36 as an unnumbered dwelling between 1616 and 1612; it is not attached
  to 1620 or 1701, because the sheet does not give its number.
- **Another household in 1900:** 1612 (a nine-family house), 1721, 1808, 1815, 1919, 2018,
  2027, 2123 and 2126. The 1904 family had not yet come; the census says nothing about their
  staff.

## Left for later

- The 1910 census (T624), which would bracket 1904 from the other side.
- The away families' own entries (the Glessners in Grafton County, New Hampshire, and the
  Highland Park and Lake Forest households).
- A second reading of the lines marked `?`.
