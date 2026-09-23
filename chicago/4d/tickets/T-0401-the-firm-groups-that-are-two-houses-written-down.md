---
id: T-0401
title: The firm groups that are two houses, written down so no later sweep merges them
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0338
opened: 2026-08-29
closed: 2026-08-29
pr: 557
claimed_by: run 8/29/2026, 3:20:12 PM CT
blocked_on: null
needs_bake: false
---

Piece 3 of 4 of **T-0338 — Thirty-one groups of firms share a partner surname and only one
of them has been judged**. The parent keeps the full ask; this ticket owns one slice of it.

The groups `firm_surnames()` puts together that are NOT one house. Nothing merges here; the
work is the written record, and it is worth a run because the next sweep that groups on the
surname will find these again and the file has to be able to answer it. T-0399 opens
`refused_firm_merges` for exactly this and leaves entries standing in it.

The candidates:

    the Kinzies — J. H., John S. and R. A., three men of one family
    P. F. Peck against P. F. W. Peck · F. G. Blanshard against G. Blanshard
    Dr. J. B. Barnard against Dr. J. H. Barnard · G. W. Keeney against W. Keeney
    M. H. Kennicott against Wm. H. Kennicott · J. H. Mulford against [J. I. Mulford]
    J. Curtiss, L. Curtiss and L. G. Curtiss · Charles Taylor against Wm. H. Taylor
    Brown the painter against W. H. Brown
    the 'store' group — New York Clothing Store, Peter Cohen's store, W. Kimball's New
      Store — which share no partner at all, only the word
    the 'hotel' group — the Eagle Hotel against the blacksmith shop opposite the Chicago
      Hotel — same shape, an anchor mistaken for a partner
    the two Chicago & St. Joseph packets, schooner Llewellyn against schooner Phillips

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- Every group above stands in `refused_firm_merges` with the reason it is two, in the shape
  T-0399 established (`into`, `from`, `witnesses`, `kind`, `refused_because`).
- The 'store' and 'hotel' groups additionally record that `firm_surnames()` grouped them on
  a common WORD and not a partner, so the failure is legible if the function changes.
- The gazetteer recompiles green; no business count changes, and the PR says so.

Links: T-0338 (the parent), T-0399 (which opened the file).

---

**WHAT WAS DONE.** All thirteen candidate groups read from the printings. **16 refusals
declared; 209 businesses before and 209 after**, and the gazetteer recompiles green with
`--self-test` at 97 cases.

    REFUSED (16)
      the Kinzies (5)  ·  J. H. Kinzie / John H. Kinzie / John S. Kinzie / R. A. Kinzie,
        three men of one family. `two_houses` where two of them are printed on one page —
        the Democrat of 1833-12-10 names R. A. Kinzie at c008 and 'JAS. KINZIE' at c009 —
        and `not_joined` for John S. against John H., because the John S. card's middle
        initial is set as the figure '8' on a page wrecked by the column rule and reading
        it as an H would be a repair to the page rather than a reading of it.
      J. H. Mulford (1)  ·  the jeweller one door west of the Printing Office against the
        carriage and sleigh maker; they share the issue of 1834-07-02 and nothing else.
      W. H. Brown (1)  ·  the Dearborn street grocer against 'Brown, painter', who has no
        forename on the page to be compared with anything.
      Wm. H. Taylor (1)  ·  the Dearborn street boot store against Charles Taylor the
        South Water tailor; both forenames are printed whole.
      the Curtisses (3)  ·  the attorney first door west of Jones, King & Co. against
        L. G. Curtiss, deputy surveyor of Cook County. The Democrat of 1835-08-05 prints
        both, at c017 and c011.
      the 'store' group (3) and the 'hotel' group (1) and the two packets (1)  ·  grouped
        on a WORD and not a partner, and each refusal says so in those terms.

The five word-grouped refusals carry the second acceptance clause explicitly: the group is
made by `firm_surnames()` taking the LAST word of a partnership segment, so 'store' holds
thirteen businesses, 'Hotel' reaches into an ANCHOR carried inside a style, and the two
Chicago & St. Joseph packets are grouped on the route's own name because the split on '&'
and 'and' turns 'Chicago' and 'packet' into partners.

**Six candidates were NOT refused, and that is a deviation from this ticket's own candidate
list.** The parent built that list from the names alone and said so; read against the
printings, six of the rows are one house — P. F. Peck / P. F. W. Peck on one La Salle
corner in abutting windows, F. G. / G. Blanshard opposite Dr. Temple's, G. W. / W. Keeney
below Newberry & Dole's, Dr. J. B. / Dr. J. H. Barnard at the New-York House nine days
apart, M. H. / Wm. H. Kennicott on one copy date, and J. / L. Curtiss on one copy date at
one anchor. A refusal asserted against the evidence is worth less than no refusal at all,
so none was written; a merge would have moved the business count this ticket holds fixed,
and is a different piece of work. **T-0413** carries all six with the evidence found here,
including the one delicate part — merging `L. Curtiss, attorney and counsellor at law`
into `J. Curtiss` will break one of the refusals declared today unless it is retargeted in
the same commit, which is exactly the guard T-0399 built and is working as intended.
