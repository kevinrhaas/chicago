---
id: T-1012
title: The trade sentinel two of the four directory crosswalks read as a trade, so Fergus 1843 and the advertising cards could carry nothing
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0867
opened: 2026-09-10
closed: 2026-09-10
pr: 1097
claimed_by: run 9/10/2026, 7:59:49 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T01:32:15.991Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34548035832
---

The trade sentinel two of the four directory crosswalks read as a trade, so Fergus 1843 and the advertising cards could carry nothing.

Piece 1 of 2 of **T-0867 — The Fergus 1843 crosswalk reads 'none_recorded' as a trade, so could_carry_occupation is 0 where Norris's fixed twin reports 63**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

THE BUG, measured on dev before the fix. The residents layer does not leave a trade
null where it holds none — it writes the sentinel `none_recorded`, and 738 of its 849
people carried that when T-0569 counted. Four crosswalks ask "whose trade could this
directory supply?" and each wrote the predicate itself:

| crosswalk | predicate | `could_carry` trade, before |
|---|---|---|
| `crosswalk_fergus_1839` | excluded `none_recorded` AND `unknown` | 99 |
| `crosswalk_norris_1844` | excluded `none_recorded` (fixed by T-0569) | 64 |
| `crosswalk_fergus_1843` | `if not r["occupation"]` — the truthiness test | **0** |
| `crosswalk_norris_1844_advertiser` | `if not r["occupation"]` | **0** |

The two zeroes are the finding this ticket's parent was filed on. They are not Fergus
failing to print trades — Fergus 1843 prints a trade against most of two thousand
entries — they are the question never being asked, because `none_recorded` is truthy
and every one of those 738 people read as already traded.

- The predicate is stated ONCE, in a module the four crosswalks import, carrying its
  own self-test and gated by `check.sh` — because writing it four times is what let
  two of the four be wrong for months. The sentinel list is the thing the self-test
  guards: widening it widens what every directory may carry to a card.
- The two correct crosswalks re-derive BYTE FOR BYTE across the refactor. That is the
  regression evidence: if `crosswalk_fergus_1839` or `crosswalk_norris_1844` moves by
  one line, the shared predicate is not the predicate they had.
- The two broken ones re-derive with a non-zero `could_carry`, and
  `spend_directories.py` carries exactly that list onto the cards under its own rule 1.
  No rule is re-parsed and no grade moves; the spend is mechanical.
- `crosswalk_norris_1844_advertiser` GETS A GATE. It was the only one of the four with
  a committed output and no `--check` step, so it stood at the residents layer of
  4 September 2026 while the layer moved under it. Regenerating it on this ticket moved
  eleven refusals, five ambiguities and one match that nothing had asked for — drift
  nobody could see, which is the same failure T-0714 gated the 1840 heads for.
- `bash tools/check.sh` green. No bake: nothing here moves geometry.
