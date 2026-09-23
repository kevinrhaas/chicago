---
id: T-1172
title: Re-admit the borderline roster as reconstructed residents under their own read names: fix the uncertain presences, mint the single-source and 1834-return names, back-project the biographied later names — every re-admission with its evidence limit and its reopen rule
state: done
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-18
pr: 1495
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T02:13:31.895Z
claimed_run: null
---

The owner: *"give them a real human name … research that … may have only been one source not a
few so you marked them out, but now is the time to dip back into that and fill out the
population."* Stage `readmit` of T-1167, reading T-1159 class by class.

**What each class gets:**

- **R1 (893 `uncertain` presences on existing cards):** `present_on_scene_date` re-ruled at tier
  `reconstructed` — `present` where the model's persistence rate for the person's cohort and
  last appearance says so (a letter waiting on 1 July 1835 → present; a last appearance in
  January 1834 → drawn against the persistence curve), `absent` otherwise; the inferred
  `uncertain` value is kept beside it as the evidence leg. Nobody's grade moves.
- **R2 (in-window single-source names, no card):** minted as households at `grade: reconstructed`
  under the read name, `source_pass: reconstructed_readmission`, the source and the ledger
  refusal quoted, trade from the source where printed.
- **R3 (the 1 April 1834 return and the 1832 muster):** minted likewise, presence drawn against
  persistence; the 28 T-1153 name disputes wait for T-1153 — those rows stay `unresolved`.
- **R5 (later-only names whose biography dates arrival ≤ 1835-07-01):** minted with the
  biography's arrival at `inferred` and the presence at `reconstructed`.
- **R0:** untouched; the tool proves it.
- Every re-admission carries `replaceable_by` = the ledger's `reopens_on` / the class rule, and a
  `withdrawn_if` clause: a later ruling that the name is a duplicate of an existing card retires
  it through `consolidate_town_cards.py`'s path, not by hand.

**Acceptance:**

- Counts per class: offered / re-admitted / withheld (with reason); the order book's
  `roster_offered` rows read consumed before any pool name is drawn for the same bucket
  (T-1171 and T-1173 check this).
- No R0 name is touched; no existing grade, rung or inferred/attested value moves; the ledger's
  dispositions are unchanged (a re-admission is a NEW row of kind `reconstructed_readmission`
  pointing at the refused unit, never a rewrite of the refusal).
- `mint_*` writers still re-derive drift-zero: re-admissions live in the programme's own files,
  not in the mints' outputs.
- Visible: the People view; each re-admitted card says in words that it stands on one reading
  and what would retire it.

**Stop condition:** every real name the corpus offers is in the town or has a stated reason not
to be.

**Links:** T-1159 · T-1167 · T-1153 · T-1027 · `conflict_rulings.json` (`reopens_on`) ·
`docs/RESEARCH/resident-grading-policy.md`.
