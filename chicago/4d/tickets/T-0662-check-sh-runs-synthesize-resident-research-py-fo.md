---
id: T-0662
title: check.sh runs synthesize_resident_research.py for three mint steps whose labels name a different pass, so mint_documented and mint_letter_list drift ungated
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-17
pr: 1381
claimed_by: run 9/17/2026, 2:56:02 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T08:29:28.829Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35196250693
---
`tools/check.sh` has three steps whose labels name three different mint passes and
whose commands are all `python3 tools/synthesize_resident_research.py --check`:

- "the documented residents on reconstructed roofs re-derive from the register"
- "the minted documented residents re-derive from the register"  → should be
  `tools/mint_documented_residents.py --check`
- "the minted letter-list residents re-derive from the register"  → should be
  `tools/mint_letter_list_residents.py --check`

So two of the three passes that write `data/residents/households/` are not gated at
all, and both have drifted on `dev`. Measured on 2026-09-04 against a clean
`origin/dev` tree, where `check.sh` itself exits 0:

    mint_documented_residents.py --check    →   7 file(s) differ
    mint_letter_list_residents.py --check   → 743 file(s) differ

T-0418 absorbed the 6 households of the documented pass's drift because it had to run
that pass, and deliberately did NOT run the letter-list pass: 743 files is not a
by-product, it is its own unit of work that wants its own reading before it lands.

**Acceptance:** the three steps invoke the passes their labels name; whatever the
letter-list pass's 743 files turn out to be is read before it is written — the drift is
either a real re-derivation to commit (with what changed and why stated) or a fault in
the pass; `check.sh` is green afterwards with the corrected steps in place, so the two
passes cannot drift ungated again.

## What the reading found (2026-09-17)

**It was five steps, not three.** `tools/synthesize_resident_research.py --check` ran
five times in `tools/check.sh`, under five labels, and four of them named a pass it does
not run — the K1 inferred-household programme (line 676), the invented names (2092),
T-0264's roof deal (2145), the documented mint (2156) and the letter-list mint (2195).
It was the ONLY command in all 424 steps that appeared more than once. Each of the four
passes those labels named carries a `--check` of its own; all four are RED and all four
were already in `data/research/check_gate_baseline.json` as ungated. The baseline was
right, the build was green, and check.sh read as though five derivations were held when
one was. The command proves a single fact:
`OK: 1281 people; 404 attested, 877 inferred, 0 reconstructed; 730 projected`.

**The letter-list drift is a fault in the pass, and the fault is the contract.**
798 files differ (the ticket measured 743 on 2026-09-04). It must not be written.
`mint_letter_list_residents.py` is NOT the last writer of the files it derives:
`synthesize_resident_research.py` — the very command these steps were running — rewrites
the `letter_list_only` cohort's `grade`, `resident_subtype` and `note`, and retires
households outright. Re-running the mint over the committed tree therefore reverts that
work. Measured on a scratch run of the real tree: grades go back from `inferred` to
`attested` and the `PROJECTED RESIDENT. …not independently corroborated…` qualifier is
stripped from post-office-only names (hh_works_charles is one), which is a confidence
upgrade this project forbids; 81 households the research retired come back; and 54 are
re-minted under changed ids — `hh_adains_will_si` becomes `hh_adains_willisi`. Byte
identity is the wrong contract here; a gate for this pass has to compare what the pass
OWNS. The drift itself remains T-0691's, which is blocked on T-0660.

**The documented drift is not committable either.** 10 files differ, not the 42 the
baseline claimed. Some of it is real register growth (Aaron Russell's bound moves from
12 November to 29 October 1834 on a second printing). But it also renames
`hh_grant_james` to `hh_grant_j` and writes the name as “J. Jr. Grant”, which is the
resident name-splitting fault T-1155, T-1217 and T-1218 are open on, and it retires
`hh_montgomery_l_w` on a register reading that now gives only a surname and a trade.
Gating that mint waits on those tickets; T-1220 carries it.

**What shipped instead.** The five steps are one honest step. The four removed slots each
carry, in place, what their pass is, that it is not gated, its measured red and its owner
ticket. No coverage was lost — the same command still runs — and four redundant runs of
it were paid for on every commit. `audit_check_gates.py --gate` now refuses a check.sh in
which any command runs under more than one label, with the defect's own shape as its
self-test; and `survey()` reads the COMMANDS check.sh runs rather than its text, because
writing “`tools/mint_documented_residents.py --check` reports 10 file(s) differing” into
a comment otherwise counted as gating it — the same mistake of reading prose as a gate.
Proven equivalent against `origin/dev`: same 150 capable, same 10 ungated, same set.
