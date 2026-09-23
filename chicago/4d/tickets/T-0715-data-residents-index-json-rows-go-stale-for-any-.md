---
id: T-0715
title: data/residents/index.json rows go stale for any household no minting pass owns, and only validate.py notices
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: 924
claimed_by: run 9/5/2026, 3:57:33 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T21:34:15.585Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33991495750
---

**Found landing #797, 2026-09-04.** The residents index disagreed with the records on 18
households — 12 of them people this project had regraded — and nothing that writes the index would
have fixed it.

## The mechanism

Two passes write `data/residents/index.json`, and each owns only part of it:

| pass | what it rebuilds | what it does with the rest |
|---|---|---|
| `mint_civic_residents.apply()` | rows for the civic-minted households | `keep = [r for r in index["households"] if r["id"] not in mine_ids]` — **verbatim** |
| `mint_civic_residents.apply_regrade()` | rows it touched this run | untouched rows left as they are |

So a household that **neither pass owns** — an `hh_inf_*` inferred household, a documented resident,
a letter-list mint — can have its grade changed by any other pass and keep an index row that says
something else, for ever. And `apply_regrade` touches nothing at all on a run where the proposal is
already spent, which is the normal steady state once the ladder has caught up.

The totals then inherit the error: `counts.by_grade` is summed from the ROWS, not from the records,
so a stale row makes the whole count wrong. In #797 the index read `attested: 505, inferred: 899`
against the records' `attested: 523, inferred: 881`.

## Why it matters more than 18 rows

`index.json` is what a visitor's browser loads first and what six gate steps compare against. When
it drifts, `validate.py` reports it as 19 separate errors and `synthesize_resident_research.py`
reports it as "index attested count disagrees with records" — the same one fault, wearing seven
different failure messages across `check.sh`, none of which names the cause. That is expensive to
diagnose and was diagnosed by hand this time.

## The ask

1. **One owner for the index.** A single derivation that rebuilds EVERY row's `grades` and
   `persons` from the household file on disk, and the counts from those rows — the same tally both
   passes already use, applied to the whole layer rather than a slice of it. Every pass that
   currently patches the index calls it instead of hand-patching.
2. **Gate it as a re-derivation**, the way the crosswalks are gated: the committed index must equal
   what the rebuild produces, so drift is a red build and not a hunt.
3. **Make the failure say the cause.** When the index disagrees with the records, one message
   naming the rebuild to run — not 19 per-household errors in one step and a different sentence in
   six others.
4. **Do not change any grade to close this.** The records are the truth here; the index is the
   summary that has to follow them.

**Done when** one command rebuilds the index from the cards, `check.sh` fails if the committed file
is not what it produces, and no pass patches index rows it does not own.
