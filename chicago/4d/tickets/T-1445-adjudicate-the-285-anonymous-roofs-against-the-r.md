---
id: T-1445
title: Adjudicate the 285 anonymous roofs against the re-derived programme and the placement policy: one verdict per roof — keep, refamily to a named family, or retire — each with the order-book bucket it serves and the reason it is a substitution, published as a re-derivable redeal ledger and gated; no roof moves ground
state: done
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1197
opened: 2026-09-20
closed: 2026-09-20
pr: 1566
claimed_by: run 9/20/2026, 6:46:16 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T12:50:47.524Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35508393032
---

Adjudicate the 285 anonymous roofs against the re-derived programme and the placement policy: one verdict per roof — keep, refamily to a named family, or retire — each with the order-book bucket it serves and the reason it is a substitution, published as a re-derivable redeal ledger and gated; no roof moves ground.

Piece 1 of 2 of **T-1197 — Re-audit the 285 anonymous roofs against the re-derived programme: keep the ones the order book can occupy, re-family the ones of the wrong kind, retire the ones that no longer fit — 214 stand empty today — and record every change as a substitution, not a demolition**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:**

- `tools/redeal_anonymous_roofs.py --build|--check|--self-test`: every anonymous roof
  gets one verdict, and the verdict is reached from committed files only —
  `keep` where the inventory's district/group matrix still has head for the roof's
  group in its division AND some clause of the placement policy accepts its family
  where it stands; `refamily` where the slot is wanted and the kind is not, naming
  the family it becomes; `retire` where neither the kind nor anything it could
  become is wanted there.
- The verdicts are a SUBSTITUTION LEDGER, not a demolition list: each row carries the
  order-book bucket it leaves and the bucket it joins, and the record asserts that no
  refamily moved the roof count by one. `data/reconstruction/1835_roof_redeal.json`
  and `docs/RESEARCH/1835_anonymous_roof_redeal.md` both re-derive, byte for byte,
  or `--check` refuses.
- A SEATED ROOF IS NEVER RE-DEALT. A roof carrying an `occupants` block is kept
  whatever the policy says about its family, and the breach is recorded against the
  seating tickets (`kept_occupied`) rather than acted on here. Head is counted as the
  tool walks, so two roofs cannot take the same last slot in a cell, and no roof is
  dealt into a group its division is not short in.
- Wired into `tools/check.sh` beside the programme re-derivation it reads, with the
  self-test firing on a bent order book; the tool measured into
  `tools/writer_inventory.json` and `tools/step_isolation.json`.
- No roof moves ground and no confidence moves. Every record audited is
  `inferred_anonymous` before and after; nothing is built, renamed, seated or baked.

**Not this ticket:** carrying the verdicts out — the recipe-file edits that make the
three infill generators re-derive the new families byte for byte, the retired records'
move into `data/exclusions.json`, the bake and the screenshot. That is T-1446, and it
is why `needs_bake` is false here. The parent's clause about dealing the 31 stock
roofs to the trades they were raised for is a SEATING question rather than a question
about what a roof IS; this ledger carries each roof's `raised_for` occupation through
untouched so T-1446 and the seating tickets can ask it without re-reading 285 records.

**Demonstration (2026-09-20):** 285 audited — **253 keep, 32 refamily, 0 retire**, with
3 seated breaches owed out and 0 unplaceable ones. 28 of the 32 refamily into a band
that already fits the committed footprint, so the substitution costs no new geometry.
`retire` is empty because the programme wants 668 roofs and 371 stand: the town is 297
roofs short, and there is almost nowhere a standing roof is surplus to what the order
book can occupy. The 32 are the two shapes the policy names — trade roofs stranded 6 to
48 m back inside a block (a C2 store-residence becomes a D6 cottage), and yard buildings
fronting a principal street (an A1 barn on Randolph becomes a D4) — plus the one roof in
the only oversubscribed cell in town, `structures/institutional_public/north`, which
stood 4 against a target of 3.
