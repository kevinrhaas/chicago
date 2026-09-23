---
id: T-0338
title: Thirty-one groups of firms share a partner surname and only one of them has been judged
state: split
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-29
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

T-0304 gave firms the merge machinery persons already had — `identity.json`'s `firm_merges`,
a `merge_rule` naming both spellings, a partner-surname guard and a street guard — and used it
on ONE group, the Wilson house of Dearborn street, which was standing in the register as five
businesses. It left the rest of the register unjudged.

Grouping the 197 compiled businesses by `firm_surnames()` — the same function the guard uses —
finds **31 groups holding 76 firms**. That is the candidate list and it is emphatically NOT a
list of merges: the function groups on the surname alone, so it cannot tell a firm from its
namesake, and several of these groups are certainly two houses.

The ones that look like one house under two styles, from the names alone:

    Collins & Caton (4)      Hubbard & Co. + the Howard Fire agency (4)
    Matthias Mason & Co (4)  Chicago Democrat (3)      David Carver (3)
    Giles Spring (3)         Philo Carpenter (2)       J. S. C. Hogan (2)
    John Wellmaker & Co (2)  Pierce & Abbott (2)       Jones & King (2)
    A. Garrett (2)           Chicago Bakery (2)        the Soap and Candle Manufactory (2)
    E. Wentworth's Flag Creek house (2)                and the two Taylor boot-store readings

And the ones that are a TRAP, so nobody merges them in a sweep:

    the Kinzies — J. H., John S. and R. A. are three men in one family
    L. W. Montgomery the boot maker against W. Montgomery the auctioneer
    P. F. Peck against P. F. W. Peck
    F. G. Blanshard against G. Blanshard
    the 'store' group — New York Clothing Store, Peter Cohen's store, W. Kimball's New Store
      share no partner at all, only the word

**This is more than one run and should be split before it is claimed** — the judgement per
group is the work, and each one needs the printings read, not the names compared.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Every group taken is either declared in `firm_merges` with a rule that cites the printings
  it rests on, or written down as two houses with the reason it is two.
- No group is merged on the name alone. A merge cites issues and dates.
- The gazetteer recompiles green, and the PR states the business count before and after.
- Groups not taken stay on the queue rather than being silently dropped.
