---
id: T-0896
title: Drain the 18 --check-capable tools tools/check.sh never runs: gate each or record why it cannot be gated
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-13
pr: 1271
claimed_by: run 9/13/2026, 2:30:47 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T19:59:58.695Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34777624082
---

Drain the 18 --check-capable tools tools/check.sh never runs: gate each or record why it cannot be gated.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0714, 2026-09-06.** `tools/audit_check_gates.py` reports 18 of this repo's 100
`--check`-capable tools that `tools/check.sh` never runs a `--check` on; 17 of them it does not
invoke under any mode at all. The list is committed at `data/research/check_gate_baseline.json`
and the gate T-0714 added is a RATCHET only — the set may not grow, and nothing shrinks it.

Each of the 18 needs one of two answers, and they are not the same answer:

- **gate it** — the tool re-derives a committed file from committed inputs, so `check.sh` runs
  its `--check` beside its siblings, in the same commit that makes it green; or
- **record why it cannot be** — a one-shot pass whose inputs are gone, a tool that reaches the
  network, a derivation that is red for a ruling somebody else owns. That reason belongs in the
  baseline file, next to the tool, where the next reader finds it.

Known before starting: `mint_letter_list_residents.py --check` is red today and is **T-0691's**,
which is itself blocked on T-0660's ruling — do not fold it in here. `verify_fergus_1839_first_ward.py`
runs `--offline` in the gate, which proves something different from `--check`.

**Acceptance:** every one of the 18 is either gated in `check.sh` with a green `--check`, or
carries a stated reason in `check_gate_baseline.json` that a reader can act on; `bash tools/check.sh`
green; and `audit_check_gates.py --gate` still passes. Splittable by group if 18 is more than one
run — it very likely is.

## The answer, measured 2026-09-13 — and it was 16, not 18

The baseline said eighteen; the tree said **sixteen**. `crosswalk_norris_1844_advertiser.py`
(T-0867) and `generate_school_section_grid.py` had been gated in the week since T-0714 wrote
the file, and nothing had asked it to notice — `--gate` could only fail on GROWTH, measured
against a number it allowed to stay too high. That is the first thing this ticket fixed, and
it is why the second column below is now a gate and not a convention.

**Every one of the sixteen was run.** Two were green and offline and are gated now; two are
green but reach the network to re-read a raster; two cannot be gated at all; and **ten were
RED** — ten committed derivations that had stopped following from their inputs, none of them
watched by anything.

| | tool | answer |
|---|---|---|
| gated now | `read_norris_1844_advertiser.py` | green, 0 s — the cards its crosswalk stands on |
| gated now | `compare_norris_1844_readings.py` | green, 2 s — where our Norris disagrees with Torp's |
| network | `measure_street_widths.py` | green with the readers (5 s), but re-reads the sheet over IIIF |
| network | `trace_shoreline.py` | green with the readers (24 s), re-traces a Digital Commonwealth scan |
| network | `verify_fergus_1839_first_ward.py` | fetches leaves; check.sh runs `--offline`, which is the gateable half |
| spent | `rename_household_ids.py` | refuses (exit 2): the legacy prefixes are gone, the migration is done |
| RED | `generate_inferred_households.py`, `generate_inferred_names.py`, `replace_invented_residents.py` | one refusal, three tools — **T-1108** |
| RED | `complete_resident_research_pass_14.py` | **T-1109** |
| RED | `read_st_marys_baptisms.py` | **T-1110** |
| RED | `read_voter_lists.py` | **T-1111** |
| RED | `generators/placeholder.py` | **T-1112** |
| RED | `mint_documented_residents.py` (42 files) | T-0662's |
| RED | `mint_letter_list_residents.py` (798 files) | T-0691's, blocked on T-0660 |
| RED | `read_census_1830.py` | T-0856's — and `--check` **writes**, which is why it cannot be gated even once it is green |

Sixteen ungated becomes fourteen, each carrying a reason a reader can act on, and five of the
reds become tickets placed under this one. The two answers this ticket was filed with turned
out to be three: a red `--check` is a FINDING, not an exemption, and the reason column says so
rather than filing it under "cannot be gated".

**Acceptance met.** Two gated with a green `--check`; fourteen carrying a stated reason;
`audit_check_gates.py --gate` green and now failing three ways instead of one;
`bash tools/check.sh` green.
