---
id: T-1313
title: Seat the ruled family members: open the seat on stated_family_rulings.json and re-derive the forty committed artifacts that count the town
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1170
opened: 2026-09-18
closed: 2026-09-18
pr: 1452
claimed_by: run 9/18/2026, 6:14:29 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T12:42:07.037Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35338406931
---

Seat the ruled family members: open the seat on stated_family_rulings.json and re-derive the forty committed artifacts that count the town.

Piece 2 of 3 of **T-1170 — Give the attested and inferred heads the families the sources name: spouses, children, kin and dependants from the baptism and marriage registers, the 1840 census rows of heads the layer carries, Andreas and old-settler biographies and the ruled kin ties — inferred where named, reconstructed where only counted**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- `data/residents/stated_family_rulings.json` `seating.state` flips to `open`, naming this
  ticket, and `python3 tools/spend_stated_families.py --build` seats the people its rulings
  say `write`: today Welthyan Loomis Harmon, the Harmon daughter later known as Mrs A. G.
  Burley, and Ellen Hamilton.
- AND THE FORTY ARE RE-DERIVED IN THE SAME PR. Measured on T-1312's branch: seating three
  people took `tools/check.sh` from 2 failing steps to 42. Every mint, the directory and
  census crosswalks, the ladder passes, the population profile, the reconstruction order
  book, the tier tables, the closing audit and the sign-off hold their own copy of the
  town's counts to a `--check`, and adding a person moves all of them at once. That sweep
  is the work of this ticket; the reading was T-1312's.
- `tools/check.sh` green, `--check` green with `seating.state: open`, and the published
  mirror moved with the layer.

**What it must NOT do:** weaken a ruling to avoid a rebuild, or seat somebody a mint's own
ruling refuses. `hh_hobson_jesse` is why the sixth verdict exists: the letter-list mint's
ruling of 2026-08-30 permits exactly one person on a letter-list card, so Catherine
Daugherty Hobson — named, and married three months before the scene date — is `no_seat`
until a run rules on how a letter-list head may acquire a family.
