---
id: T-0399
title: The restyled firm duplicates: one style is the other plus a trade tail or a leading article
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0338
opened: 2026-08-29
closed: 2026-08-29
pr: 549
claimed_by: run 8/29/2026, 12:21:52 PM CT
blocked_on: null
needs_bake: false
---

Piece 1 of 4 of **T-0338 — Thirty-one groups of firms share a partner surname and only one
of them has been judged**, split because the parent needed more than one run's
demonstration. The parent keeps the full ask; this ticket owns one slice of it.

**The slice, defined mechanically so it is complete and checkable.** Take the firm styles
that are IDENTICAL once a trailing trade description, a bracketed disambiguator and a
leading article are cut away — `slug(firm_style(name))` with a leading `the` and a
possessive `'s` normalised away. That is 23 clusters holding 48 of the gazetteer's 242
businesses. `Russell & Clift` is one of them and is NOT taken: T-0340 owns it and may
change the partner-surname guard itself. So 22 clusters, 46 entries.

These are the cheapest honest judgements in the parent, because the difference between the
two styles is usually the compositor's, not the firm's: `firm_style()` already knows that a
comma followed by a lower-case word begins a trade and not a partner. But cheap is not
automatic — the parent names traps that live in this slice, and a sweep that merged on the
style alone would have merged them.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- All 22 clusters are judged. Every one is either declared in `firm_merges` with a rule
  that cites the printings it rests on — issues, copy dates, streets, anchors — or written
  down in `refused_firm_merges` with the reason it is two.
- No cluster is merged on the name alone.
- The gazetteer recompiles green and `check.sh` is no worse than the dev it was cut from.
- The PR states the business count before and after.
- Clusters outside this slice stay on the queue as T-0400 / T-0401 / T-0402.

Links: T-0338 (the parent), T-0304 (the firm-merge machinery), T-0340 (Russell & Clift).

---

**WHAT WAS DONE.** All 22 clusters judged; `Russell & Clift` left to T-0340 as stated.
19 clusters merged in 21 rules, 3 refused. The register goes 242 businesses → 221.

`refused_firm_merges` is new machinery and is the half of T-0304 that was missing: before
it, the only record of having judged a group and found it two houses was the ABSENCE of a
merge rule, which reads exactly like a group nobody has looked at. It is held to the merge
rules' own disciplines — both spellings verbatim, named witnesses, and it cannot outlive
its pair — plus a `kind` from three values, because *"not shown to be one"* is not the same
finding as *"shown to be two"*.

    MERGED (21 rules, 19 clusters)
      Chicago Bakery · The Chicago Democrat (×2) · Chicago Democrat printing office
      Chicago Soap and Candle Manufactory · Collins & Caton · David Carver
      Dr. W. G. Austin · G. Spring · Henry Moore · Hubbard & Co.
      J. H. Collins & J. D. Caton · John Holbrook · L. W. Montgomery
      Matthias Mason & Co. · P. Pruyne & Co. · Philo Carpenter
      Pierce & Abbott (×2) · Sarah D. Howe · the Traveller's Home

    REFUSED (3)
      A. Garrett  ·  different_ground — the South Water stand passes to W. Montgomery in
        July 1835 and Garrett signs from Dearborn street in August; a removal is a claim
      B. Jones  ·  not_joined — a grocery and a forwarding business, set as two
        advertisements in two columns of one issue, and no printing puts them under one roof
      W. Montgomery  ·  two_houses — the auctioneer at David Carver's old stand against
        L. W. Montgomery the bootmaker next door to P. Cohen's, with the L lost in the setting

Two directions were chosen against the default and the rules say why: `L. W. Montgomery`
merged INTO the styled record, because that one holds the Cohen anchor three printings
support against a single damaged line read `P. Ca[rpenter's]`; and the Democrat's printing
office keeps the 1834 corner through the merge, because `placement_rank` prefers a corner to
a relative offset regardless of date — **T-0403** was filed for that, and it is a machinery
question, not this house's.
