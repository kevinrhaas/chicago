---
id: T-1013
title: Norris prints a firm as 'Jones, B. & Co.' and the firm test only looks before the comma, so 33 firm entries are read as people
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0867
opened: 2026-09-10
closed: 2026-09-10
pr: 1103
claimed_by: run 9/10/2026, 10:12:09 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T03:43:46.048Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34557219374
---

Norris prints a firm as 'Jones, B. & Co.' and the firm test only looks before the comma, so 33 firm entries are read as people.

Piece 2 of 2 of **T-0867 — The Fergus 1843 crosswalk reads 'none_recorded' as a trade, so could_carry_occupation is 0 where Norris's fixed twin reports 63**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

MEASURED ON DEV BY T-1012'S RUN, so this ticket is the fix and not the survey.

`tools/read_norris_1844.py` decides firm-or-person with

    firm = bool(FIRM.search(head.split(",")[0] + ","))

— it looks ONLY at the text before the first comma. That catches the firm style with
no comma in it, `Sicar & Co. groceries and boarding house`, and misses the INVERTED
style this volume uses constantly, where the surname is set first for the alphabet:

    Jones, B. & Co. dry goods and groceries, S. Water, b Clark and Dearborn

Before the comma stands `Jones`, so the entry is normalised as a PERSON — surname
Jones, given "B", trade "& Co. dry goods and groceries" — and the firm filter at
`crosswalk_norris_1844.py:100`, which skips firms so a company is never matched to a
resident, never sees it. Norris's volume reports 65 firms; the count is short.

**THE CLASS IS 33 ENTRIES, and the rule that finds them is not "the line contains
`& Co.`".** 124 entries contain that string and 91 of them are people —
`Bradley, Joseph, clerk, at W. H. Adams & Co.'s` is a clerk, not a company, and
`Burley, A. G. of A. G. B. & Co.` is a partner giving his residence. The rule that
separates them: walk the entry's leading tokens and STOP at the first plain
lower-case word (the trade) or at `of` (the partnership preposition); a firm marker
inside that prefix is a firm. Under it, 33 entries flip and none of the 65 existing
firms flips back. Thirty are unambiguous —

    Adams W. H. · Allen J. P. · Barrows D. A. · Burley A. G. · Carter T. B. ·
    Chapin J. P. · Collins S. B. · Dow J. I. · Frink, Walker · Gale Stephen F. ·
    Gilbert, Ashley · Goss S. W. · Holden C. N. · Irvin J. B. · Johnson J. ·
    Johonnott, Wells · Jones B. · Lessey John F. · Lock Wm. · Lloyd, Blakesly ·
    Magie H. H. · Norton Horace · Rattle F. · Raymond B. W. · Ryer G. ·
    Sanger L. P. · Smith George · Walker C. · Wheeler Wm. · Whitmore(?), Magill

— and THREE are false positives the prefix rule must also refuse, all three the same
shape: the scanner welded `of` onto its neighbour, so the stop word is not a token.

    n1844_e0556  Eddy, Ira B.-of Eddy & Co. res Michigan avenue
    n1844_e1469  Raymond, B. W. ofJ5. W. R. & Co. h Wash, b Clark and Lasalle
    n1844_e1646  Smith, George, of'G. S. & Co. res City Hotel

A boundary-insensitive stop — `of` followed by anything that is not a lower-case
letter — catches the first and third. The second (`ofJ5`) is OCR damage and belongs in
the T-0695 repair table, not in the firm rule.

- The 33 flip, the 65 do not, and `read_norris_1844.py --check` re-derives.
- **The flip is a DELETION from the person crosswalk** — each of these entries may be
  matched to a resident today, and a match that vanishes takes a `could_carry` with it.
  Count what the person crosswalk loses BEFORE and AFTER and say so; a firm that was
  matched to a person of 1835 was a wrong match, but the arithmetic has to be shown,
  not asserted.
- Whether the 30 reach `norris_1844_businesses_1835.json` through
  `date_norris_1844_businesses.py` is the second half of the yield: a firm Norris
  prints is not an 1835 business until a date reaches it, and that pass already holds
  the rule.
- `bash tools/check.sh` green. No bake.
