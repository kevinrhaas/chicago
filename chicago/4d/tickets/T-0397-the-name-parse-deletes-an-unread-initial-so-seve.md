---
id: T-0397
title: The name parse deletes an unread [?] initial, so seventeen refusals are stated on a letter no printing read
state: done
epic: PAPERS
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0348
opened: 2026-08-29
closed: 2026-08-29
pr: 544
claimed_by: run 8/29/2026, 9:46:32 AM CT
blocked_on: null
needs_bake: false
---

`initials()` in `tools/compile_gazetteer.py` runs the name through `unmarked()`, which
DELETES the `[?]` marker. That is right for a surname and wrong for a forename, because
deleting the marker hands the initial to whatever letter stood behind it. Measured on the
1 July 1834 letter list, **all seventeen `[?]` refusals in `identity.json` parsed wrongly**,
in three shapes:

- **seven invented a letter from the rest of the forename** — `[?]rah Fowler` read as `R.`,
  `[?]nn M. Gooding` as `N. M.`, `[?]saac Scarrett` as `S.`, `[?]bey Blankinship` as `B.`,
  `[?]amnee Ball` as `A.`, `[?]kiler Brown` as `K.`, `[?]oon Bowrassa` as `O.`;
- **six collapsed a position** — `[?]. M. Fish` read as `M.` in FIRST position against
  `E. M. Fish`'s `E. M.`, so a middle initial was compared with a forename one; likewise
  `[?]. D. Doty`, `[?]. C. Chamberlain`, `[?]. [H]. Scott`, `[?]. W. Easling`, `[?]. Smith`;
- **four read no initial at all** — `[?]. Beegle`, `[?] Adkins`, `[?]. Blair`, `[?]. Fisher` —
  which is the shape T-0348's own diagnosis assumed all seventeen had.

Those readings then went into `data/research/newspapers/identity.json` as the STATED ground
of each refusal — *"same surname … A. against R."* — so a committed record asserts letters
no printing ever carried. **That is a provenance defect, and it is what this ticket is.**

It is also why T-0392 cannot be implemented either way it is ruled: whichever answer the
owner gives, the code has to be able to SAY which side is unread, and today it cannot —
`[?]rah` is indistinguishable from a read `R.`

**This ticket does not touch the policy.** 177 declared merges and 29 refusals before and
after; every one of the eleven `read_initials_disagree` refusals still refuses; `Cohen, P.`
and `Cohen, J.` still never merge. The open question is T-0392's and stays open.

**Acceptance:** (one demonstration, never weakened to pass)

- `initials()` records an unread `[?]` as an UNREAD value occupying the position it was
  printed in, equal to no read letter; the marker stays welded to the word it opens, so
  `[?]rah` is one forename with an unread initial and not two.
- The gazetteer self-test asserts the VALUE for all three shapes above — the existing
  cases only assert that a pair DIFFERS, which is what let `[?]nn M. Gooding` pass while
  reading `N. M.` — and the eleven genuine disagreements plus `Cohen, P.`/`Cohen, J.`
  still refuse.
- All 29 `refused_because` texts in `identity.json` state the reading the page carries,
  and each refusal carries its parsed `initials_read`.
- Person and merge counts are stated before and after, and are unchanged.
