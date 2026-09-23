---
id: T-0601
title: A column sliver is kept as a second, truncated copy of a card the neighbouring pass read in full, and nothing counts how many
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-05
pr: 876
claimed_by: run 9/5/2026, 6:35:51 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T12:25:20.002Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33963535650
---

A column sliver is kept as a second, truncated copy of a card the neighbouring pass read in full, and
nothing counts how many.

**What the passes do.** `tools/read_newberry_index.py --extract` reads each page four times, cropping a
200-point window on a 173-point pitch, because the page widths drift by up to 44 points across a volume
and a narrower window would clip a column. The overlap is deliberate and the file says so: 'the slivers
are deduplicated on (page, heading, body) after the passes'.

**Why that dedup cannot fire.** A sliver is not a copy — it is the left edge of a card. Its heading and
its body are both TRUNCATED, so the tuple never equals the full reading's, and the sliver survives as a
short second card with the same locality.

**The one that was caught.** T-0578's draw hit `nbi_v02_1775`, whose whole reading is `Krlog | Cook Co..`
— the left edge of 'Kristenson family. — Cook Co., Ill. See index.', which column 3 read in full and
committed as `nbi_v02_1779`. It was graded `locality_correct`, because Cook County is genuinely on the
card; what it corrupts is the COUNT, not the locality.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- A measurement first: how many of volume 1's 2,579 and volume 2's 1,987 kept cards are slivers of a card
  a neighbouring column read in full. Match on the page, the column adjacency and the fact that one
  reading is a prefix of the other under `collapse()`; state the figure before proposing a rule.
- Then the rule, if the figure earns it: prefer the LONGER reading of the same card and drop the sliver,
  or keep it and mark it, but do not silently leave two. Say which, and why.
- The counts in `entries.json`, `coverage.json` and the README move with it, and the precision samples
  are re-drawn if any sampled card leaves the records (`--check` enforces this).
- Volumes 3 and 4 are unread; if the rule lands first, they never carry the double count.

**Effort.** S. The measurement is a script over two committed text files and can be run before anything
is changed.

**Links:** T-0578 (which caught it) · T-0600 (the other two false-positive classes from the same draw) ·
T-0562 (the parent read) · `precision_sample.json` block `2`, record `nbi_v02_1775`.
