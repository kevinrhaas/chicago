---
id: T-0769
title: A card body can OPEN with the TAIL of the card in the column to its left, so a locality is matched on text that is not on the card
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-06
pr: 1003
claimed_by: run 9/6/2026, 2:32:38 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T20:37:59.012Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34055014009
---

A card body can OPEN with the TAIL of the card in the column to its left, so a locality is matched on text that is not on the card.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found while measuring T-0601**, which is the mirror of this and does not cover it.

T-0601's column sliver is a **prefix** artefact: the crop window is 200 points wide on a
173-point pitch, so it reaches 27 points into the NEXT column and catches the left edge of
a card that column reads in full. T-0601 measured nine of those, marked them, and stopped
there because they duplicate a card and that is a COUNT defect.

This is the other end of the same overlap. Page widths in a volume run from 689 to 733
points, so on a wide page the PREVIOUS column's text is pushed past the boundary and a
window catches its right edge. The fragment does not arrive as a card of its own — it
arrives glued to the FRONT of a real card's body, and the locality patterns then match on
text that is not on that card.

**The one that is already adjudicated.** `nbi_v02_0610` — `Hallam | , 111.19 Hallam
faaily.` — opens with `, 111.19`, which closes the body of `Hall` in the column to its
left (`-±~2.' la letk» te,'», 111.19`). It is volume 2's one remaining bad keep in
`precision_sample.json`, and `coverage.json` recorded it as "a column sliver of the shape
T-0601 carries", which T-0601 measured and disproved. That claim is corrected in the same
PR.

**The figure so far is an UPPER BOUND and is not yet a measurement.** Asking, over all
four volumes, whether a body OPENS with a run of six or more characters that CLOSES a body
on the same page: 117 candidates at column delta −1 against 4 at every other delta. The
delta −1 concentration is the artefact's signature and is real; the 117 is not, because
most of those runs are a common word (`Illinoi`, `Chicago,`) that two unrelated cards both
carry. A length-6 run is far too weak a test for a body whose median length is 47.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- A test that separates the artefact from a shared word, argued on the same ground T-0601
  used: the fragment is the SAME INK read twice by the same engine, so the match has to be
  byte-exact and long enough that two independent cards cannot reach it by coincidence.
  State the figure it gives, and state the delta profile beside it — a rule whose hits do
  not concentrate at delta −1 has not found this artefact.
- Then the rule, if the figure earns it. Note that unlike T-0601 this one cannot be
  answered by striking a record: the card is real and only its BODY is contaminated, so
  the choice is between trimming the body (which edits a reading, and
  `MANIFEST.text_sha256` plus `check()` will both refuse it) and marking the card so its
  localities are not trusted. Say which, and why.
- If a card's localities come only from the bled-in fragment, it should not be kept at
  all, and the counts in `entries.json`, `coverage.json` and the README move with it.
- `precision_sample.json`'s rows are re-adjudicated only if a sampled card leaves the
  records; `--check` enforces that either way.
- `--self-test` gains the case.

**Effort.** S — the measurement runs over committed text files, exactly as T-0601's did.

**Links:** T-0601 (the prefix half, which is done and is where the geometry is written
down) · T-0600 (the other false-positive classes from the same draw) · T-0578 (the draw
that caught the first one) · `data/research/newberry_index/README.md` § The column sliver.
