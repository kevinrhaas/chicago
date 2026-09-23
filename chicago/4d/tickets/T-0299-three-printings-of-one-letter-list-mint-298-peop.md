---
id: T-0299
title: Three printings of one letter list mint 298 people three times, and identity.json is empty
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-28
pr: 509
claimed_by: run 8/28/2026, 11:52:03 PM CT
blocked_on: null
needs_bake: false
---

The gazetteer compiled from July 1834 holds **638 persons** and the town had nothing like
that many. The post office's list of letters for 1 July 1834 was printed in three
consecutive issues, the segmenter cut each printing differently, and the identity policy —
correctly — keys on the whole normalized name, so `Ara Brundaze`, `Asa Brundage` and
`[…]andage` are three people. Multiply by 298 names and three printings.

That is the policy working, not failing: nothing coalesced by accident. But the file that
exists to fix it, `data/research/newspapers/identity.json`, is still empty, and until it
is filled the gazetteer cannot be counted, sorted or shown to anyone.

## What the merge pass has to respect

- A merge is declared in `identity.json` with a `merge_rule` naming BOTH spellings
  verbatim. The compiler refuses one without.
- Same surname, different initials NEVER merges, rule or no rule. `Cohen, P.` and
  `Cohen, J.` stay two people; so do `M. Jones` and `Wm. Jones`, who are the same
  advertisement signed twice (T-0289 claims c020 of 1834-07-09 and c007 of 1834-07-23).
- The three printings are three witnesses to ONE list, so a merge here is usually a
  recognition-class OCR difference in one letter of one name — the easiest kind to justify
  and the easiest kind to get wrong at scale.
- The claims themselves must not be edited to agree. Each stands on the lines it cites;
  the merge is where the judgement goes.

## Why it is not free

Roughly 300 merge rules, each naming two spellings and saying why. The compiler validates
every one, so a wrong rule fails loudly rather than quietly — but a rule that merges two
real people passes. Sampling against a fourth witness (the page images, or the 1834
issues of the American once they are read) is what would make it safe.

**Acceptance:** (state it before working — never weakened to pass)

- Every merge in `identity.json` carries a `merge_rule` naming both spellings; the gate is
  green and `--self-test` still fires.
- The PR states the person count before and after, and names the merges it REFUSED to make
  and why — the refusals are the evidence the pass was not just a de-duplication.
- No claim's `normalized` reading is changed to make a merge easier.
