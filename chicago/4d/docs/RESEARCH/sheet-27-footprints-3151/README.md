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
  the 4B frame flats at 216-216a East 20th behind it: 1911 uses whose 1904 state nothing in hand
  attests. Ruled `phase_unresolved`, traced and not drafted. T-3154 reads them.
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
