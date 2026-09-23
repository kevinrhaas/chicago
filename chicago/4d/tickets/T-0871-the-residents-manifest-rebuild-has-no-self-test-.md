---
id: T-0871
title: The residents-manifest rebuild has no self-test and silently accepts any flag: nothing proves its assertions fire, and --write typo'd is a green check
state: done
epic: PIPELINE
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-13
pr: 1267
claimed_by: run 9/13/2026, 2:05:49 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T19:24:12.148Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34776448081
---

`tools/rebuild_resident_index.py` is the single owner of `data/residents/index.json`
(T-0715, landed by PR #924) and `tools/check.sh` runs its `--check`. **Nothing proves its
own assertions fire**, and it is the only re-derivation gate in this repository without a
self-test — `resident_cohort_freeze`, `compile_gazetteer`, `compile_register`,
`consolidate_resident_evidence`, `measure_corner_ordinals` and `synthesize_resident_research`
all carry one, and `check.sh` runs each.

Two faults, both measured on `dev` at 3500c2f6c:

**1. No self-test.** `main()` reads `"--write" in argv` and does nothing else with the
argument list. A rule that has never been shown to fail is a rule nobody has tested.

**2. Any flag is silently a `--check`.** Because the only test is `"--write" in argv`,
an unrecognised argument is not refused — it falls through to the check path and exits 0:

    $ python3 tools/rebuild_resident_index.py --nonsense-flag
    data/residents/index.json re-derives from its 1339 household cards      # exit 0
    $ python3 tools/rebuild_resident_index.py --selftest
    data/residents/index.json re-derives from its 1339 household cards      # exit 0

So **`--wrtie` typed for `--write` reports success and writes nothing.** The person who
ran it believes the manifest was rebuilt. That is the same class of quiet failure T-0715
was opened about, one level up: the manifest goes stale and the tool says it is fine.

**Acceptance:**

1. `rebuild_resident_index.py` grows a `--selftest`, wired into `tools/check.sh` beside
   the existing `--check` step, that **proves each assertion fires when broken** — at
   minimum: a row whose grade disagrees with its card is caught; a card with no row is
   caught; a row with no card is caught; each derived count in `DERIVED_COUNTS` is caught
   when moved; a flag written when false is caught; and **a rebuild of a rebuild is a
   no-op**.
2. The argument list is parsed rather than sniffed, so an unrecognised flag exits non-zero
   and says so. A typo must never read as a passing check.
3. Neither change touches `data/residents/index.json` — the manifest re-derives before and
   after, byte for byte.

**Found by:** PR #926, an independent implementation of T-0715 that #924 beat to the merge.
Its version carried a `selftest()` with twelve named cases — *a flag is written only when
true*, *civic_mint comes off source_pass*, *grades tally the persons*, *key order is
canonical*, *an unstated confidence block reads as None*, *a rebuild of a rebuild is a
no-op* — and a refusal naming a row key no derivation emits. Those cases do not transplant
directly, because that branch's `rebuild(index, docs)` takes the household documents and
dev's `rebuild(index)` loads them itself, but **they are the list of what to write** and
the branch is the place to read them from. Everything else #926 held is already on `dev`:
the derivation, the `check.sh` gating, the `projected_resident: false` cleanup (0 rows
carry it) and the `generate_inferred_households.py` T-0715 note.
