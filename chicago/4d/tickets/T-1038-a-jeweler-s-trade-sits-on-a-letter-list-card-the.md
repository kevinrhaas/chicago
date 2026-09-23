---
id: T-1038
title: A jeweler's trade sits on a letter-list card: the identity layer folds Norris 1844's 'Sherwood, Smith J. jeweler, 144 Lake' onto hh_sherwood_s, minted from two uncalled-for letters for Stephen Sherwood
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-11
closed: 2026-09-11
pr: 1146
claimed_by: run 9/11/2026, 2:26:20 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T20:39:07.043Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34638552772
---

A jeweler's trade sits on a letter-list card: the identity layer folds Norris 1844's 'Sherwood, Smith J. jeweler, 144 Lake' onto hh_sherwood_s, minted from two uncalled-for letters for Stephen Sherwood.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- the fold is traced: say which pass joined `Sherwood, Smith J. jeweler, 144 Lake st` (Norris
  1844) to `sherwood_s`, a card `tools/mint_letter_list_residents.py` minted from the
  Democrat's returns of 28 January and 2 July 1834 for a Stephen Sherwood, and whether the
  same pass joined the 1839 reading too;
- the corpus's own separate identities for the jeweler — `id_sherwood_s_j`,
  `id_sherwood_smith_jones` — are weighed against the card, and the ruling either splits the
  card or states in its note why one man is right;
- nothing is spent onto a `letter_list_only` card that the letter list did not say. If the
  trade and the 144 Lake address belong to Smith Jones Sherwood they come off `sherwood_s`,
  and if a business record was placed from them, it moves with them;
- `bash tools/check.sh` green, and the derived resident files re-run in the same pass.

## WHERE THIS CAME FROM

T-1034 cohort B, refusing SHERWOOD S J against `sherwood_s`: the register's middle initial J
belongs to the jeweler the corpus holds under his own name, and the card that the proposal
pointed at is the letter-list Stephen. Refusing the land row does not fix the directory line
already sitting on that card — **a person minted to claim nothing now carries a trade and a
street address** — and the argument is in
`data/research/land_sales/README.md` § Cohort B.

