---
id: T-0413
title: Six of T-0401's surname traps are one house on the printings, and the merge is unwritten
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-11
pr: 1163
claimed_by: run 9/11/2026, 7:54:00 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T01:43:31.524Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34663007218
---

T-0401 took the parent's candidate list — the groups `firm_surnames()` puts together that
are supposedly NOT one house — and read the printings behind every row of it. Six rows do
not survive the reading. They are not namesakes; each is one house whose two styles differ
by an initial, and each one has a printing that says so. T-0401 refused none of them,
because a refusal asserted against the evidence is worse than no refusal at all, and it
merged none of them either, because its own acceptance holds the business count fixed and
a merge is a different piece of work. So they stand unjudged, which is exactly the state
T-0399 opened `refused_firm_merges` to abolish — and this ticket exists so the reading is
not done a third time.

The six, with the evidence T-0401 found, so nothing here has to be re-read from scratch:

    P. F. Peck  ←  P. F. W. Peck
      One corner: 'corner of La Salle and South Water streets' in both, and the windows
      abut — P. F. Peck runs 1833-12-03 c010 to 1834-06-18 c007, and P. F. W. Peck is
      copy-dated 1834-06-18, the very issue the shorter style last appears in. Both are
      general stores. The extra W is a fuller signature of one merchant.

    G. Blanshard  ←  F. G. Blanshard
      One anchor, printed twice: 'opposite Dr. Temple's, Lake-st.' at 1834-10-08 c004 and
      the same words damaged at 1834-11-12 c012. One trade: houses and lots for sale or
      to let. Five weeks apart in one paper.

    W. Keeney  ←  G. W. Keeney
      One anchor again: 'A few doors below Messrs. Newberry & Dole's', at 1834-05-07 c003
      and 1834-06-04 c022, and one trade — tin, sheet iron and copper ware, stoves and
      castings. Four weeks apart in the Democrat.

    Dr. J. H. Barnard  ←  Dr. J. B. Barnard
      One lodging: 'AT THE NEW-YORK HOUSE, LAKE-STREET' in the Democrat of 1835-06-04
      c006, copy-dated 1835-06-03, and 'a[t] t[h]e New Yor[k] Ho[u]se, La[k]e [s]t[r]eet'
      in the American of 1835-06-13 c009, nine days later. One trade: physician. The B and
      the H are the second initial of one man read out of two settings.

    Wm. H. Kennicott, Surgeon Dentist  ←  M. H. Kennicott
      The Democrat of 1835-06-24 carries M. H. Kennicott, dentist, Lake Street (c007) —
      and 1835-06-24 is a COPY DATE of the Wm. H. Kennicott signboard record, which is
      also a dentist's and also in Lake Street (1835-08-05 c021, 1835-08-19 c014). One
      notice, two settings of the same forename.

    J. Curtiss  ←  L. Curtiss, attorney and counsellor at law
      Copy-dated 1835-05-18 on both sides, and both stand 'first door west of Messrs.
      Jones, King & Co.' in South Water street (1835-05-20 c009 and 1835-07-01 c013). One
      standing advertisement of one attorney, read twice. NOTE this one is delicate: the
      register also holds L. G. Curtiss the deputy surveyor, a different man, and T-0401
      refuses BOTH L styles against him. A merge here must not disturb those refusals —
      and it cannot, because `L. Curtiss, attorney and counsellor at law` is the `from`
      side of one of them, so the compile will fail the moment the merge lands unless the
      refusal is retargeted onto the surviving style in the same commit. That is the
      interesting part of this ticket and the reason it is not an XS.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Each of the six is either declared in `firm_merges` with a rule naming both spellings and
  citing the printings above, or written into `refused_firm_merges` with a reason that
  says why the evidence here does not hold.
- The Curtiss merge lands together with the retargeting of T-0401's two L refusals, so the
  compile never sees a refusal that has outlived its pair.
- The gazetteer recompiles green, `--self-test` passes, and the PR states the business
  count before and after.

Links: T-0401 (which read the printings and did not act on them), T-0399 (which opened
`refused_firm_merges`), T-0400 (the forename-form slice), T-0338 (the parent sweep).
