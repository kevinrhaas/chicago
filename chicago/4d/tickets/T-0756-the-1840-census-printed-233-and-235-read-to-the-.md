---
id: T-0756
title: The 1840 census printed 233 and 235 read to the name: PR #670's last two calibration pages, off the sheets
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: 860
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T07:49:19.267Z
claimed_run: null
---

The 1840 census printed 233 and 235 read to the name: PR #670's last two calibration pages, off the sheets.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

A piece of **T-0496** that its split did not carve out. T-0741 inventoried images 51-74 and
read nothing from them; T-0746 holds the reading of the group's sheets and will split by
printed page. This ticket is the two leaves that could not wait for that, because they are
**PR #670's last two calibration pages** and the other five were already read.

**What was done** (see PR #860):

- `pages/33SQ-GYYJ-RJ.json` — printed 233, 31 lines, names only, `[?]` kept as a POSITION.
- `pages/33SQ-GYYJ-ZQ.json` — printed 235, 24 lines, same discipline; the blank remainder of
  the leaf was looked at rather than assumed.
- `crosswalk_670.json` gains both pages with the row-offset test. **233's rows are aligned
  and its readings differ** (17 hits at offset 0 against 2 and 4 either side); **235 is the
  cleanest page in the domain** — 24 against 24, 16 hits at offset 0 and none at any other.
- All seven of #670's pages are now read off the sheets. None reproduces.
- T-0741's inventory counted 31 and 24 written lines on these two leaves; the line-by-line
  reading returns the same two numbers.

**Not done here, on purpose:** no cell, no IPUMS serial, no resident. The cells are T-0746's
and the bridge is T-0505's. 1840 is later evidence and never an 1835 resident on its own.
