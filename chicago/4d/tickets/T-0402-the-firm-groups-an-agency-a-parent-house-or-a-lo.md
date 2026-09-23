---
id: T-0402
title: The firm groups an agency, a parent house or a lost signature makes ambiguous
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0338
opened: 2026-08-29
closed: 2026-08-29
pr: 556
claimed_by: run 8/29/2026, 2:27:08 PM CT
blocked_on: null
needs_bake: false
---

Piece 4 of 4 of **T-0338 — Thirty-one groups of firms share a partner surname and only one
of them has been judged**. The parent keeps the full ask; this ticket owns one slice of it.

What is left after T-0399, T-0400 and T-0401: the groups where the honest answer is not
"one house" or "two houses" but something the merge machinery cannot say at all.

    Hubbard & Co. against the Howard Fire Insurance Company, E. K. Hubbard agent
      — an AGENCY is not the house that holds it, and the gazetteer has no relation
        that says so
    the Chicago Democrat against the Chicago Democrat printing office
      — T-0399 merges each of these into itself and leaves them two, because the partner
        surnames are {democrat} against {office}: the guard cannot see that an office is
        its paper's. Same shape as T-0340's headline-only firm, and it should be decided
        with it rather than against it
    Jones & King against Jones, King & Co.
    Abell against S. Abell, attorney and counsellor — a bare surname against a styled one

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- Each group is either merged with a declared rule, refused with a written reason, or —
  where the answer needs machinery the gazetteer does not have (an agency relation, a
  paper-and-its-office relation) — a ticket is filed for that machinery and this one
  records the decision to file it.
- Nothing is merged that changes the partner surnames, unless T-0340 has already changed
  that guard and this cites the change.
- The gazetteer recompiles green and the PR states the business count before and after.

Links: T-0338 (the parent), T-0340 (the same guard question), T-0304.

---

**WHAT WAS DONE.** All four groups judged. Two merged, one refused, one declined and
ticketed — and the fourth group turned out to be two refusals rather than one, because the
Hubbard group holds three records and not two. The register goes **219 businesses → 217**.

    MERGED (2)
      E. K. Hubbard, agent for the Howard Fire Insurance Company
        ← Howard Fire Insurance Company — E. K. Hubbard, agent at Chicago
        One standing advertisement, four printings — the American of 1835-06-20 c015 over
        the copy date 'June 20, 1835' and the Democrat's reprints at 1835-07-01 c017,
        1835-07-08 c005 and 1835-07-29 c011 — the same setting word for word over one
        signature. The em-dashed style is a transcriber's construction; no printing sets it.
      S. Abell, attorney and counsellor  ←  Abell
        One law card in the two papers. The Democrat of 1835-06-24 c006 survives as every
        OTHER line of itself and loses the forename off the head; the American of
        1835-08-01 c003 sets the same six clauses in the same order with 'S. ABELL' clean.
        Conveyancing advertised as a line of business is what makes it unmistakable — the
        American's own claim note records it as the FIRST law card in this run to name it.
        Merged INTO the styled record so the initial survives; the Dearborn Street reading
        the Democrat holds comes through under `placement_rank`, so the merged house is
        strictly better placed than either record was, and the missing preposition in that
        damaged line stays missing.

    REFUSED (2)
      Hubbard & Co.  ·  two_houses — a commission and forwarding house whose named partners
        are Gurdon S. and Henry G. Hubbard, against a one-man fire-insurance agency signed
        E. K. Hubbard. They are live at once in two trades. What puts them together is not
        a spelling: **Hubbard & Co. held the Howard agency first**, in the plural, from
        1834-07-02 c048 to 1835-05-20 c023, and the identical copy runs in the singular
        over E. K. Hubbard from 1835-06-20. That is a succession of the AGENCY and nothing
        in the corpus makes E. K. a partner in the firm.
      Jones & King  ·  two_houses — and this is the sharpest trap the surname grouping has
        set yet. The '& Co.' IS the difference: it is a third partner, and the guard strips
        'Co.' as a style suffix before it compares, so the partner it hides is invisible to
        the machinery meant to catch exactly this. Jones & King is two men selling stoves
        from Water-street near the bridge (1834-09-10 c008, 1834-12-03 c007); Jones, King &
        Co. is a firm announcing its own formation over THREE names — WILLIAM JONES, BYRAM
        KING, H. B. CLARKE — copy-dated May 26, 1835 (1835-05-27 c005, standing again at
        1835-07-08 c009 and 1835-07-29 c012). A copartnership notice is the strongest
        statement the papers can make that the partners changed, and this project's own
        rule is that a changed partnership is a different house.

    DECLINED AND TICKETED (1)
      the Chicago Democrat against the Chicago Democrat printing office — NOT merged, and
      NOT refused either. Not merged because the partner surnames are {democrat} against
      {office} and that guard has no escape; T-0340 had not changed it when this ran, and
      this ticket's own second acceptance clause forbids merging without such a change. Not
      refused because none of the three refusal kinds is TRUE here: they are not two
      houses, a printing does join them (the colophon is the paper naming its own shop),
      and in 1834 they stand on the same corner. Filing a false refusal to make the group
      look closed is worse than leaving it open. **T-0411** is filed for the machinery.

**T-0410** is filed for the agency relation the Hubbard refusal could not express — and it
turned out to be a three-house question, not a two: Jones, King & Co. announce the SAME
Howard agency over a dateline of 1 July 1835 (1835-08-05 c008), the scene date itself.

**On the second acceptance clause.** Nothing merged here changes the partner surnames.
Both merges are within {hubbard} and {abell} respectively, and both pass the guard
untouched.

**Business count: 219 before, 217 after.** `check.sh` green — and green on the unmodified
dev this branch was cut from, so the RED the queue's top band records has been repaired by
a merge since it was measured.
