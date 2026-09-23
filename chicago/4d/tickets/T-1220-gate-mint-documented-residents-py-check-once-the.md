---
id: T-1220
title: Gate mint_documented_residents.py --check once the resident name-splitting tickets land
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-17
closed: 2026-09-17
pr: 1383
claimed_by: run 9/17/2026, 3:44:27 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T08:53:26.810Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35193523780
---

Gate mint_documented_residents.py --check once the resident name-splitting tickets land.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

`tools/mint_documented_residents.py --check` reports 10 file(s) differing on `dev`
(measured 2026-09-17; `data/research/check_gate_baseline.json` had said 42 since before
T-0662 re-measured it). The pass is ungated because the drift cannot be committed as it
stands, and T-0662 read it rather than writing it:

- **Real register growth, and welcome.** Aaron Russell's arrival bound moves from
  1834-11-12 to 1834-10-29 because the corpus now holds a second printing
  (`Aapon Ruseell,` — Democrat, 29 October 1834, column 6). Seven files are of this kind.
- **A name the splitter mangles — and it is not the splitter.** The pass re-mints
  `hh_grant_james` as `hh_grant_j` with the person's name written “J. Jr. Grant”. Read
  on 2026-09-17: the register ADJUDICATES, and `person_grant_j_jr` and `person_james_grant`
  both carry `action_target: grant_james` — the register's own ruling that they are one
  man. The mint iterated the printings rather than the people, so the two arrived as
  RIVALS for the one Grant household refusal 8 allows and the loser was refused as a
  duplicate of himself; whichever printing sorted first took the card. That is a fault
  in this pass, not in the splitter, and it is fixed here rather than waited on.
- **A retirement that wants a reading.** `hh_montgomery_l_w` — a documented shoemaker —
  is refused now, and the reason is refusal 6, not the surname test: the papers put his
  work at `P. Cohen's store` on South Water Street, no roof is committed under that
  name, and `in_town_places()` could not resolve the string — so a Chicago store read as
  evidence the man was somewhere else. `place_vocabulary.json` states the rule the
  refusal is meant to be (T-1048, B2): "a reading that names only such places is not a
  Chicago appearance." It is a test on a READING now, and a person is refused only when
  every one of his readings fails it — which is also what keeps the postmaster Levi F.
  Arnold, the sheriff Stephen Forbes and the justice Stephen M. Salisbury, each printed
  once beside Plainfield, Cook County and the Dupage.

**Not in this ticket.** Consulting `place_vocabulary.json` directly, rather than taking
its B2 rule, admits `A. Clybourn` — and `measure_card_fuzzy_candidates.py --self-test`
refuses that as a one-letter duplicate of the committed `clybourne_archibald`. That pair
is T-1002's open question and refusal 7's surname-proxy blind spot, not this one's.

**Acceptance:** `--check` is measured against a tree the name-splitting tickets have
moved (T-1218 landed first); each remaining difference is read and either committed with what
changed and why stated (the retirement named explicitly, in the changelog) or refused as
a fault; `tools/mint_documented_residents.py --check` is then a step in `tools/check.sh`
and the tool leaves `check_gate_baseline.json`'s ungated list in the same commit
(`audit_check_gates.py --write`).
