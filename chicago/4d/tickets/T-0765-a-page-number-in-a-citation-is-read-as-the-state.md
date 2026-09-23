---
id: T-0765
title: A page number in a citation is read as the state: ', 111,' after a digit run, 65 kept cards across the four volumes
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-06
pr: 999
claimed_by: run 9/6/2026, 1:38:23 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T18:43:58.797Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34049602990
---

A page number in a citation is read as the state: `, 111,` after a digit run, 65 kept
cards across the four volumes.

**Where it was measured.** T-0600, which struck the two classes T-0578's draw found and
measured this third one on the way past without acting on it. The `illinois_abbreviated`
pattern anchors on a comma or a semicolon, and a page list ends in one: `1897: 130,111,
183,186,371` gives it `,111,`. So does an illustration note — `(Delano, J. A.) 1899: 203,
ill.` is page 203, illustrated. Counting only cards whose ONLY bucket is the abbreviation,
and only where what precedes the matched comma ends in a digit: 17 in volume 1, 18 in
volume 2, 18 in volume 3 and 12 in volume 4.

**Why T-0600 did not do it.** The obvious rule — refuse when a digit precedes — over-fires
on this OCR, which reads a trailing `o` as `0`: `'««g0, III.'` and `'> — Chiear.0, 111.,'`
are both *Chicago, Ill.* and both would be struck by it. Two in the forty-odd looked at,
which is a 5 per cent error rate on a rule that removes 65 cards, and T-0600's own
demonstration did not need it. A digit RUN of two or more, not preceded by a letter, was
the tightening that looked promising and was not measured.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- The rule is stated with the shape it tests, written beside `REGNAL` and
  `names_only_the_place` with its reason, and the count it strikes per volume is named.
- The Chicago-or-Cook cards it strikes are counted separately and a sample of them is
  looked at against the page image — this is the stratum `follow_up.json` ranks on, and a
  recall loss there costs more than a precision gain.
- All four volumes re-extracted and re-parsed in the same commit, the precision samples
  maintained the way T-0600 maintained them (the struck rows replaced from the same
  stratum and adjudicated against the page image), and the README's figures moved with them.

**Links:** T-0600 (the two rules that landed, and the measurement) · T-0578 · T-0766 ·
`tools/read_newberry_index.py` `LOCALITY_BUCKETS`.
