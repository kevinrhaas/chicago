# The district's background closed: Indiana 18th-20th as a reconstructed row, the IC sliver ruled open, and 1904 measured before and after (T-3011)

Piece 4 of 4 of T-2983. The visibility census (`data/components/prairie_1904/background_census.json`) left two
unparcelled targets after the three drafted pieces (T-3008, T-3009, T-3018/T-3019):

- **`unparcelled:blk_indiana_prairie_18_20`, the Indiana half of the 18th-20th block.** Seen from 48 Prairie
  stands, the census's most-seen target. Sanborn 1911 vol. 3 **sheet 27**, which draws this face, is not among the
  committed scans, so the 1904 grid carries Indiana's east line straight between sheets 20 and 35 and has no lots
  here. The **1904 Blue Book** (`chicago_blue_book_1904`, its Indiana Avenue street list, item OCR lines
  24563-24597, read through archive.org's stream view) lists households at **1813, 1815, 1819, 1821, 1825, 1829,
  1833, 1901, 1921 and 1933**. The face is drafted as **one record,
  `indiana_east_frontage_18th_20th_background_row`: 22 houses** re-stood from the neighbouring Indiana faces' own
  drafts. The 1800s half (15 houses) uses the 20th-21st face's 3B row (2007-2027), because the Blue Book lists a
  run of consecutive numbers there. The 1900s half (7 houses) uses the 16th-18th face's freestanding houses
  (1601-1703), because it lists three households in 122 m. The rule, the numbering calibration and what is
  invented are in `L-draft-district-background-3011`. Each house's own row of the plan (`from`) names its model,
  its lot and the Blue Book numbers that fall on it. T-3145 ingests sheet 27 and replaces the row house by house.
- **`unparcelled:blk_prairie_ic_16_18`, the strip between Prairie's east lots and the Illinois Central.** It is
  about 150 m² of slivers where E. 18th Street's north line curves into Calumet beside 1729's lot and meets the
  railway's line. Sheet 20's lots run back to the right-of-way themselves, and the sheet draws nothing on the
  slivers. **Ruled open** in the rules' `open_ground` (`data/components/prairie_1904/draft_prairie_1904.json`).

## 1904 before and after the whole background (published /1904/, `node tools/qa_draft_t3011.mjs`)

**Before** is the same published build booted with every record of the background passes filtered out of the
1904 sidecar index and its boot packs: 84 records (T-3008, T-3009, T-3011, T-3018 and T-3019, plus the Indiana
lots T-3068 and T-3130 drafted on them). **After** is the build as it ships. Desktop runs at full detail and
mobile at light. Frame times are medians of 3 renders on this runner's software GL, so they are relative
readings, not device claims.

| viewport | | load to ready | JS heap (after GC) | GLBs fetched | page errors / failed requests |
|---|---|---|---|---|---|
| 390x780, light | before | 35.3 s | 88.1 MB | 126 | 0 / 0 |
| 390x780, light | after | 36.7 s | 109.6 MB | 210 | 0 / 0 |
| 1280x800, full | before | 59.1 s | 61.9 MB | 126 | 0 / 0 |
| 1280x800, full | after | 60.9 s | 65.5 MB | 210 | 0 / 0 |

| stand | viewport | triangles before → after | draw calls before → after | frame ms before → after |
|---|---|---|---|---|
| west-between-prairie-houses-at-1900 | desktop | 0.93 M → 1.05 M (of 4.60 M) | 3684 → 3801 | 7852 → 8219 |
| west-down-18th | desktop | 3.33 M → 3.44 M (of 4.60 M) | 3659 → 3705 | 14628 → 14845 |
| west-down-20th | desktop | 0.90 M → 1.06 M (of 4.60 M) | 3793 → 4063 | 10069 → 10447 |
| east-down-18th | desktop | 1.25 M → 1.25 M (of 4.60 M) | 1259 → 1263 | 9186 → 8994 |
| indiana-west-walk-at-1900 | desktop | 1.50 M → 1.73 M (of 4.60 M) | 4140 → 4678 | 11602 → 12018 |
| air-over-indiana-18th-20th | desktop | 4.25 M → 4.44 M (of 4.60 M) | 2669 → 3042 | 12356 → 12834 |
| west-between-prairie-houses-at-1900 | mobile | 0.21 M → 0.24 M (of 1.27 M) | 820 → 998 | 1561 → 1592 |
| west-down-18th | mobile | 0.50 M → 0.53 M (of 1.27 M) | 1275 → 1455 | 2901 → 2954 |
| west-down-20th | mobile | 0.22 M → 0.24 M (of 1.27 M) | 738 → 1013 | 2423 → 2460 |
| east-down-18th | mobile | 0.46 M → 0.46 M (of 1.27 M) | 786 → 786 | 2576 → 2594 |
| indiana-west-walk-at-1900 | mobile | 0.69 M → 0.55 M (of 1.27 M) | 2460 → 2056 | 3254 → 2974 |
| air-over-indiana-18th-20th | mobile | 0.60 M → 0.69 M (of 1.27 M) | 1679 → 1861 | 2648 → 2843 |

Every stand is within its tier's budget in both states, with no page error or failed request. The whole
background costs about 1.4-1.8 s of load, 3.6 MB of heap on desktop and 21.5 MB on mobile, and 84 more GLBs.
At the stands that see it, it adds up to 0.23 M triangles and up to about 540 draw calls. On mobile at
Indiana's west walk the count *falls*, because the row hides ground and trees behind it. The tightest reading
is the desktop air view over Indiana, at 4.44 M of 4.6 M. The stand already over budget (Calumet's east walk at
20th looking north, 4.63 M) is T-3012's and is not re-read here.

Screenshots: `before-*` and `after-*`, one per stand and viewport. `browser-validation-*.json` holds the
raw readings.
