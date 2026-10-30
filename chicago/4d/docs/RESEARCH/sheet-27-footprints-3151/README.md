# Sheet 27's Indiana frontage, 18th to 20th Street, traced and drafted (T-3151)

**What:** every building on Indiana Avenue's east frontage from 18th to 20th Street and on the
row at 213-217 East Eighteenth Street, read off Sanborn 1911 vol. 3 sheet 27 (ingested and fit by
T-3150) into a census of its own,
[`data/components/prairie_1904/edges_census_s27w.json`](../../../data/components/prairie_1904/edges_census_s27w.json),
traced as sheet `27w` into
[`data/traces/prairie_1904_footprints_s27w.json`](../../../data/traces/prairie_1904_footprints_s27w.json)
(**24 grounds, 38 buildings, 95 parts**), and drafted by `tools/draft_prairie_1904.py`: **22 houses
and 13 alley buildings**. They replace T-3011's reconstructed background row
(`indiana_east_frontage_18th_20th_background_row`, 22 re-stood houses), which is retired.

**How:** the T-2327 tracer with one SHEETS entry. One thing on this scan needed a rule: its frame
(yellow) wash is printed darker than sheets 20's and 28's (r 156-169 against the rule's r > 170),
so the alley sheds behind 1901, 1909, 1913 and 1921 fell out as paper. The sheet's entry lowers the
floor on r to 150 for this scan alone (`frame_r_min`); the hue tests are unchanged, and every other
sheet's outlines re-derive byte for byte.

## The 1904 Blue Book's households, lot by lot

T-3011 read the 1904 Blue Book's Indiana Avenue list for this face. Each number falls on a lot whose
1911 front is a dwelling:

| Blue Book | lot (1904 grid) | the 1911 sheet draws |
|---|---|---|
| 1813 (three households) | `indiana_1813` | 3B brick dwelling |
| 1815 | `indiana_1815` | 3B brick dwelling, canted bay |
| 1819 | `indiana_1819` | 3B brick dwelling, canted bay |
| 1821 | `indiana_1821` | 2B brick dwelling, stone strip |
| 1825 | `indiana_1825` | 3B brick dwelling, stone front, round bay |
| 1829 | `indiana_1829` | 2B brick dwelling |
| 1833 (two households) | `indiana_1833` | 2½B brick dwelling |
| 1901 | `indiana_1901` | 2S.B. brick dwelling, pair with 1909 |
| 1921 | `indiana_1921` | 2B brick pair 1921-1923, stone fronts |
| 1933 | `indiana_1931` | 3S.B. brick pair 1931-1933, round bays |

## What is not drafted

- **1925-1929**, a one-storey P.O. sub-station, and **1935-1937**, a one-storey corner store with
  the 4B frame flats at 216-216a East 20th behind it: 1911 uses, traced and not drafted. T-3154
  then read their 1904 state (below).
- **The 1911 shops on house lots:** the one-storey stores built forward of 1801 and 1807 to the
  street line and the two stores at 205-207 East 18th behind 1801. They are kept out of those
  houses' drafts by depth from the street line (`keep_out`).
- **The two unnumbered lots between 1839 and 1901**, open on the sheet, stay open.

## Limits

- Robinson 1886 plate 10's page ends at 18th Street, so no earlier plan checks these outlines.
  Presence in 1904 is inferred from the 1911 sheet alone (study ruling 11), as on sheet 35w.
- The fit is the sheet's own tie to sheets 20 and 28, 0.67 m RMS on six components, with no
  independent check; relative accuracy inside a lot is the trace's, about 0.05 m.
- The pairs (1917-1919, 1921-1923, 1931-1933) and the 213-217 row stand as one record each until
  T-1946 parts them.

## Overlays

`overlay.jpg`, `overlay-west.jpg` and `overlay-east.jpg`: building outlines in red, parts by role.
Regenerate with
`python3 tools/trace_prairie_1904_footprints.py --sheet 27w --overlay docs/RESEARCH/sheet-27-footprints-3151`.

## The 1904 state of 1925-1929 and 1935-1937 (T-3154)

Read 2026-10-25 from the OCR text of the 1902 Lakeside directory, the 1911 Lakeside directory
(`lakeside_annual_directory_1911`, new) and the Chicago Blue Books of 1902 to 1911, searched for
every number from 1901 to 1937 Indiana and 214 to 218 East 20th. The face's numbers did not move
in the 1909 renumbering: the Blue Books seat Sprague at 1933 in 1902-1904 and Bourchier at 1933 in
1905-1911, both on the 1931-1933 pair.

| frontage | 1902 | 1910-1911 | ruling |
|---|---|---|---|
| 1925-1929 | two households at 1927 (Joseph Schnable, Anton Yensch), Sophia M. Schnable at 1927 | six homes at 1927 and Ira S. Weidner's furnished rooms (Lakeside 1911) | `replaced_after_1904` |
| 1935-1937 | nothing legible; the Health Food Co. at 1601 Wabash | the Health Food Co.'s western agency, J. G. Moore & Co. (Lakeside 1911) | `phase_unresolved` |
| 216-216a E. 20th | nothing legible; no Blue Book household 1902-1909 | Blue Book households from 1910; Judge Marcus Kavanagh there in 1911 | `phase_unresolved` |

- **1925-1929.** A house let in rooms stood at 1927 on both sides of the scene date, so the
  sub-station the 1911 sheet draws is a later building: it came after the 1911 directory's canvass,
  or the sheet carries a later correction. No plan, view or description of the house is in hand,
  so, as with 2001-2003 on sheet 35w, nothing is drafted; the lots are not open ground in 1904.
- **1935-1937 and 216-216a.** The flats' first Blue Book households in 1910, and Kavanagh's move
  there from the Congress hotel by 1911, point to flats of about 1909. But an absence from the Blue
  Book, or from an OCR that also drops 1933's Sprague household in 1902, is not a date, so the
  frontage stays `phase_unresolved`.
- **Not read:** the Tribune. Its archive is not reachable from here; a dated advertisement for
  1927's rooms, the corner store or the flats would be the next source to try.
