---
id: T-1302
title: The manifest coverage gate only sees a --build declared one way, so 55 gated writers still slip past it
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-17
closed: 2026-09-18
pr: 1470
claimed_by: run 9/18/2026, 12:28:30 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T20:33:58.296Z
claimed_run: null
---

`tools/audit_manifest_coverage.mjs` refuses a gated writer the derived manifest has never
heard of. It works, and it found four on the day it shipped. **It also has a false negative,
and a gate with one is worse than no gate, because it is believed.**

Its write-mode pattern was anchored to the start of a line:

    /(?:^|\n)\s*(?:if\s+)?["']--(?:build|write)["']/

That matches a tool which reads argv directly — `if "--build" in argv:` — and MISSES one
that declares the same mode through argparse — `parser.add_argument("--build", ...)`. Both
styles are used in this repository.

**It cost two red runs on #1422.** `export_borderline_roster.py` declares `--build` through
argparse, landed on dev after the audit was written, and the audit reported OK while the lap
could not rebuild the roster. That one is now listed (measured first: a rebuild on clean dev
changed no committed byte). This ticket is the rest.

**Widening the pattern to `/["'`]--(?:build|write)["'`]/` reports 55 tools.** That number is
the finding, and it is why this is a ticket rather than a same-night fix: fifty-five is far
too many to list unmeasured, and `_must_reproduce` is not a formality — a tool can pass
`--check` and still not rebuild to itself, which is what `crosswalk_census_1840_heads.py`
already demonstrates at 137 rewritten lines.

**Acceptance:** widen the pattern, then triage all 55 BY MEASUREMENT, in batches, and state
the split. For each: run its build on a clean `dev` and record whether it changed a committed
byte. It reproduces, so it goes in the manifest with what it writes. It does not, so it goes
in `NOT_DERIVABLE` with the measurement that says why. **No tool is listed on the strength of
its `--check` passing**, and none is exempted without a number beside it. The gate must be
green at the end with the widened pattern in place, and the count of listed versus exempted
is the deliverable.

**Do not weaken the gate to make this pass.** If the triage cannot be finished in one run,
split it by batch and leave the pattern widened behind a smaller exemption list — a gate that
fails honestly beats one that reports OK while a writer it cannot see goes stale.


---

## Done — and the answer is not a wider pattern

**The ticket asked to widen the pattern and triage 55 tools. Measuring first showed the
premise was wrong twice over:** widening cannot be made correct, and the population is 175
rather than 55.

### No pattern over SOURCE can classify these tools

Three candidate patterns, each measured against the real tree on 2026-09-18:

| pattern | unlisted writers found | why it is wrong |
| --- | --- | --- |
| anchored to a line start (as shipped) | **0** | misses an argparse declaration — the ticket's own complaint |
| widened bluntly | **59** | **8 false positives**: they declare no write mode and matched `--build` in their own PROSE. `carry_stage_blocks.py` has only `--check` and `--self-test` |
| a DECLARED flag only | **52** | misses `read_fergus_1839.py`, which has **no `--build` at all** and WRITES BY DEFAULT when the argument is neither `--check` nor `--self-test` |

That last one settles it. A tool's write mode is sometimes its **default branch**, so no
reading of the source can answer the question — and the blunt widening the ticket proposed
would have traded a false negative for eight false positives.

### So the gate holds the tree to a measurement instead

`tools/writer_inventory.json` carries one row per gated tool: its measured verdict, the
mode that was run, and a date. `audit_manifest_coverage.mjs` refuses any gated tool with no
row — which is what stops a new writer arriving unmeasured, the hole this ticket was filed
for. Behaviour is too slow for a per-commit gate and does not belong in one: the answer
only changes when a tool changes.

### The measurement

Every gated tool was run on a clean tree — its declared write mode, or **bare** where it
declares none — and git was asked what moved. **175 measured**, none on the strength of its
`--check`:

| | count |
| --- | --- |
| in the manifest (re-derived on every gate) | **52** |
| reproduce, not yet placed | **89** |
| cannot rebuild, each with its number | **15** |
| write nothing at all | **19** |

Four wrote nothing on a clean tree *while declaring a write flag*, which a content diff
cannot tell from a perfect rebuild — the `_must_actually_write` trap. Each was **perturbed**
before being classified: break its output, confirm `--check` catches it, confirm the write
mode restores it. All four are real write-if-changed writers, and all four would have gone
silently into the manifest as no-op steps under a content-only test.

### What cannot rebuild, with the numbers

* `adjudicate_wright_na_fit.py` — Does NOT reproduce: `--write` rewrote 1 committed file(s) on a tree the gate called clean.
* `build_book_page_index.py` — Cannot rebuild: --build raises on a clean tree (traceback, exit 1).
* `carry_stage_blocks.py` — Cannot rebuild: declares only --check and --self-test; the blunt pattern matched `--build` in a MESSAGE about what a later build would do.
* `census_1840_fingerprint.py` — Does NOT reproduce: `--build` rewrote 1 committed file(s) on a tree the gate called clean.
* `check_household_derivations.py` — Cannot rebuild: run bare it exits 2 (usage) — it is a checker, not a writer.
* `check_wright_nara_registration.py` — Cannot rebuild: run bare it exits 2 (usage) — a checker.
* `crosswalk_census_1840_heads.py` — Does NOT reproduce: `--build` rewrote 2 committed file(s) on a tree the gate called clean.
* `derive_timber_belt.py` — Does NOT reproduce: `--write` rewrote 1 committed file(s) on a tree the gate called clean.
* `generate_inferred_households.py` — Cannot rebuild: run bare it exits 2 (usage); its build needs arguments this audit did not supply.
* `generate_inferred_names.py` — Does NOT reproduce: `(bare)` rewrote 2 committed file(s) on a tree the gate called clean.
* `read_blackhawk_war.py` — Does NOT reproduce: `--build` rewrote 1 committed file(s) on a tree the gate called clean.
* `read_newberry_index.py` — Needs OCR shards from outside the repository. Invoked bare it prints its usage and exits 0, writing nothing.
* `replace_invented_residents.py` — Does NOT reproduce: `(bare)` rewrote 5 committed file(s) on a tree the gate called clean.
* `trace_lake_shore_rees_1849.py` — Cannot rebuild: run bare it exits 1 — needs inputs or arguments not supplied.
* `trace_south_branch_rees_1849.py` — Cannot rebuild: run bare it exits 1 — needs inputs or arguments not supplied.

### An inherited bug found on the way

The audit tested `manifest.includes('tools/x.py')` — a substring match over the whole JSON —
so a tool merely NAMED in a step's prose read as listed. That is how
`read_newberry_index.py`, the one tool the exemption list existed to keep OUT, registered as
present. A step now counts only when it RUNS the tool.

### Batch 2, which this deliberately does not do

The 89 that reproduce are recorded as `pending`, not hidden: the gate counts them out loud
on every run. **Placing them is its own measured pass** — on #1452 three reconstruction
stages oscillated between red states until they sat in the right slot, so 89 writers cannot
be appended to the manifest blind. The ticket permits exactly this split, and the honest
position is that the gate now SEES every one of them, which it did not before.
