---
id: T-1115
title: consolidate_resident_evidence strips a name's brackets before mint_civic_residents' uncertainty guard can see them, so a surname the page cut in half mints a household: H. G. Hub[…] becomes The Hub household
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-13
closed: 2026-09-16
pr: 1371
claimed_by: Codex 9/16/2026, 10:58:34 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-16T20:45:31.902Z
claimed_run: null
---

consolidate_resident_evidence strips a name's brackets before mint_civic_residents' uncertainty guard can see them, so a surname the page cut in half mints a household: H. G. Hub[…] becomes The Hub household.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0997, 2026-09-13**, reading the committee of seventy out of the *Chicago
Democrat* of 29 October 1834. The segmenter's crop cuts five surnames in half —
`A. N. Ful[…]`, `M. M'Cle[…]`, `H. G. Hub[…]`, `[?] Hau[…]`, `Hon. R. J. […]` — and
`[…]` is this corpus's mark of ABSENCE, so the reading is right to stop there.

`tools/mint_civic_residents.py` already has the guard for exactly this. Refusal 7 is
*"the transcription bracketed the name as uncertain"*, and its pattern is
`UNCERTAIN = re.compile(r"\[|uncertain", re.I)` — any `[` at all. **It cannot fire.**
`tools/consolidate_resident_evidence.py` clusters on a surname and a forename it has
already split with the brackets stripped, so `H. G. Hub[…]` reaches the mint as the
plain name `H G Hub`, and the town gains a card headed `The Hub household` with a
person called `H G Hub` on it. `E. K[in]zie` splits WORSE: the bracket falls inside the
surname, so the split is forename `e k`, surname `zie`, and the card is
`The Zie household`. Five such cards were minted and deleted by hand during T-0997; the
claims were then narrowed so none of them is asserted, which is the right record anyway
but is not a fix.

Two things are wrong and they are separable:

1. **The guard is applied to the wrong string.** It should read the appearance's
   `as_read` — which identity_master.json carries verbatim, brackets and all — rather
   than the name the clusterer rebuilt. Every bracketed newspaper name in the corpus has
   been invisible to it since it was written.
2. **The split itself breaks a name at a bracket.** `E. K[in]zie` is one surname and the
   splitter makes two tokens of it. That is a separate defect and it also affects the
   gazetteer's own ties, so it may want its own ticket.

**Acceptance:** the guard fires on a bracketed name; a fixture in
`mint_civic_residents.py --self-test` proves it fires on `H. G. Hub[…]` and on
`E. K[in]zie`; the tree is measured for cards already minted this way and each is either
deleted or ruled; and if (2) is left open, it is filed with what it costs.

**Tree audit completed 2026-09-16.** Eighteen civic-minted cards carried a bracketed
scene-year name reading. Thirteen rested on no separate clean in-window appearance and
the mint derivation removes them: `bailey_esth_r_m`, `han_m_s`, `hunter_osice`,
`intry_m`, `isaac_h`, `jesteorple_bernard`, `john_w`, `king_byra`, `man_hol`,
`nter_edward_f_h`, `owen_v`, `sweet_alon_on`, and `tmple_john_t`. Five identities
survive on independent clean evidence — `beaubien_b`, `chapman_george`,
`hogue_william`, `hubbard_henry_g`, and `hunt_charles_cotesworth_pinckney` — while the
bracketed appearance is removed from their card and from any arrival/presence conclusion
it previously carried. The gate now asks this of the committed tree as well as the
decision function. The separate splitter defect and the size of its rekey are preserved
in T-1155 under PARKED RESEARCH.

Every resident-dependent crosswalk and spend was then rebuilt against the smaller town.
Three old-settler readings had been counted as spent only because they were attached to
the withdrawn false identities; the historical ratchet now records their deliberate
return to the unspent pool (460 → 463) until a clean 1835 identity can carry them. They
were not discarded: the closed ledger still classifies all 23,699 registered research
units, with zero unclassified units, and its mutation tests still fire.
