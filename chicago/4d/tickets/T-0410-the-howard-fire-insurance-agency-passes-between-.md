---
id: T-0410
title: The Howard fire-insurance agency passes between three houses, and the gazetteer has no relation that can hold it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-11
pr: 1161
claimed_by: run 9/11/2026, 7:38:37 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T01:26:54.555Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34662068638
---

**Found by T-0402**, which judged the Hubbard group and could go no further than a refusal.

The Howard Fire Insurance Company of the city of New-York sold fire insurance in Chicago
through a LOCAL AGENT, and the corpus shows the agency in three different hands inside
thirteen months. The advertisement is one standing setting; only the signature changes.

    HUBBARD & CO.        plural — 'THE subscribers having been appointed AGENTS for the
                         Howard Fire Insurance Company … HUBBARD & CO.', copy-dated
                         July 1, standing 1834-07-02 c048 → 1834-10-15 c005 →
                         1835-05-20 c023
    E. K. HUBBARD        singular — the same copy word for word, 'THE subscriber having
                         been appointed agent … E. K. HUBBARD.', copy-dated June 20,
                         1835: 1835-06-20 c015 (American), reprinted by the Democrat at
                         1835-07-01 c017, 1835-07-08 c005, 1835-07-29 c011
    JONES, KING & CO.    'having been appointed Agent for the Howard Fire Insurance
                         Company', over a dateline of 1 July 1835 — 1835-08-05 c008,
                         where the segmenter ran the agency notice and the hardware
                         firm's copy together on one fragment

**What the gazetteer cannot say.** A business record holds a trade, goods, proprietors, a
street and placement readings. An AGENCY is none of those: it is a relation between a
named principal that is not in this town at all and a local house that holds it for a
season. So the corpus expresses it the only way it can — by minting the agency as its own
business, which then collides with the house holding it under `firm_surnames()` and has to
be refused by hand. T-0402 wrote two of those refusals and neither of them says the true
thing, which is that these houses are joined rather than confused.

It matters to the model as well as to the register. If the agency is a business it wants a
roof; if it is a relation it wants none, and the house that holds it wants a line on its
card instead. On the scene date of 1 July 1835 the corpus reads the agency as held by
E. K. Hubbard (copy of 20 June) AND announced by Jones, King & Co. (dateline of 1 July),
which is either a handover inside that week or two readings of one — and nothing here can
even pose the question.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The gazetteer can record that a house HOLDS an agency for a named principal, over a
  window read from the printings, without minting the agency as a business.
- The three holdings above are expressed in it, each citing the printings above, and none
  of them upgraded past what the copy states — in particular nothing decides whether
  E. K. Hubbard was a partner in Hubbard & Co., because no printing says so.
- The refusals T-0402 left in `refused_firm_merges` are revisited: whichever of them the
  new relation makes unnecessary is removed with the reason, and whichever it does not is
  left standing.
- A house holding an agency does not thereby gain or lose a roof, and the register's
  business count moves only by the agency records the relation retires.
- `check.sh` green, and the PR states the business count before and after.

Links: T-0402 (the refusal that could not say this), T-0338 (the parent sweep),
T-0304 (the firm-merge machinery), T-0411 (the same shape, for a paper and its office).
