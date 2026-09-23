---
id: T-0859
title: J. S. C. Hogan's live placement is a street_only that names no street: the cedar-post notice gives no address and T-0440's repair cannot see it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-06
pr: 960
claimed_by: run 9/5/2026, 11:51:14 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T05:16:04.635Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34009841423
---

J. S. C. Hogan's live placement is a street_only that names no street: the cedar-post notice gives no address and T-0440's repair cannot see it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

FOUND WHILE RULING ON T-0773's list of houses whose printed address is outranked by a
later printed address. Hogan is the one row on that list where the disagreement is not a
judgement at all, and the reason is in the minting claim.

`business_j_s_c_hogan` is live at `{"class": "street_only", "anchor": null}` off ONE
printing, `chicago_democrat_1834_03_25#c010`. That claim is a two-line notice of three
hundred cedar posts under a scrap of song about fencing a garden — *"300 CEDAR POSTS, for
sale che[ap] by J. S. C. HOGAN. March [24]."* — and **it names no address whatever**. The
`street_only` class and the `South Water Street` beside it come from the extraction's
business-level `street` field, supplied by a reader who knew where Hogan's store was, not
from anything the advertisement printed.

Eight printings from 1834-08-13 to the scene date itself, 1835-07-01, place him *"in South
Water Street, one [door … of] the Post Office"* — the post office he kept. That reading is
outranked by the cedar posts today.

## Why T-0440 cannot see it

`compile_gazetteer.py`'s repair fires only where the live placement rank is ZERO. This one
ranks 1, so a printing that gave no address outranks eight that did, and
`measure_placement_silence.py` reports it on the line for houses waiting on an
`anchor_changes` judgement. No such rule may be written for it either, and the mechanism is
right to refuse: guard 3 admits only anchors some printing carries, and this printing
carries none. See `docs/RESEARCH/outranked_printed_addresses.md` § 4.

T-0773 could not do this, because that ticket forbids teaching the compiler to prefer one
printed address to another and this is a compiler change. It is a narrow one: a
`street_only` that names neither a street nor a landmark is the same silence T-0440 already
rules on, not a competing address.

**Acceptance:**

1. A ruling, written down, on whether a `street_only` placement carrying no `street` and no
   `anchor` is an address at all — with the count of how many claims in the corpus carry
   one, not Hogan alone.
2. If it is not: the T-0440 repair extended to reach it, in `compile_gazetteer.py`, by the
   same rule and the same scene-date bound — never a second implementation of it — and the
   business-level `street` left where it is, since it is not the claim's placement.
3. `python3 tools/measure_placement_silence.py` re-derives, and the waiting count moves for
   the reason given.
4. No house is re-placed except by that rule; no anchor is invented; `bash tools/check.sh`
   green.

**Links:** T-0773 · T-0440 · T-0345 · `docs/RESEARCH/outranked_printed_addresses.md` ·
`tools/compile_gazetteer.py` § T-0440.
