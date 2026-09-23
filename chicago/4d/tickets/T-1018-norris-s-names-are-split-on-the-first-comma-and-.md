---
id: T-1018
title: Norris's names are split on the first comma and 69 entries have no comma there, so a man's printed name runs on into his trade and his street
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-10
closed: 2026-09-11
pr: 1107
claimed_by: run 9/11/2026, 12:05:39 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T05:47:19.866Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34564250517
---

Norris's names are split on the first comma and 69 entries have no comma there, so a man's printed name runs on into his trade and his street.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)


**MEASURED ON THIS BRANCH by T-1013's run**, which found it and did not fix it: the
fix is 69 entries wide and one of them is a trap, so it is its own demonstration.

`split_entry()` in `tools/read_norris_1844.py` takes a person's name as everything
before the FIRST comma. Norris sets `Crissman, John M. laborer`, so that works — but
archive.org's OCR loses that comma constantly, setting a full stop or nothing at all,
and then the name runs on into whatever follows:

    Crissman John M. laborer          -> surname 'Crissman John M. laborer'
    Bowen 6c Cole                     -> surname 'Bowen 6c Cole'
    Wells. Andrew S. of Johoimett W. & Co. h Rand st. b Lasalle and Wells
                                      -> surname is the WHOLE LINE

T-1013 added `name_prefix()`, which already knows where the name ends: it walks the
leading tokens and stops at the trade or at `of`. Capping the comma-derived name at
that prefix repairs all 69 — `Crissman John M.`, `Bowen`, `Wells. Andrew S.`

**THE TRAP, and why this is not a one-line change.** The prefix is EMPTY for entries
whose reading starts lower-case, because the first token is already the trade:

    n1844_e0009  house Clark street (See card)
    n1844_e0276  ady
    n1844_e0278  ilhoun

Capping naively would set those surnames to `''`, which drops them out of
`crosswalk_norris_1844.py` (it skips a claim with no surname) with nothing said. They
are turned lines the entry-boundary rule mis-cut, or margin droppings — they need a
ruling of their own, not a silent empty string.

**Acceptance:**

- Every one of the 69 is enumerated before and after, and each is either repaired or
  refused with a reason. An empty prefix is a REFUSAL, not an empty surname.
- `crosswalk_norris_1844.py` counts before and after: a name that stops running into
  its street can match a resident it could not reach, and any match LOST is named.
- Six of the 69 are the entries T-1013 re-read as people (they were filed as firms,
  so nobody had noticed their names); `n1844_e1868` is the worst, carrying its whole
  line as a surname.
- `read_norris_1844.py --self-test` asserts the empty-prefix class stays refused.
- `bash tools/check.sh` green. No bake.
