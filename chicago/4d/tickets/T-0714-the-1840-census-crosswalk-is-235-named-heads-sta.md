---
id: T-0714
title: The 1840 census crosswalk is 235 named heads stale on dev and no gate says so: 498 on disk against 733 read from the pages
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-06
pr: 993
claimed_by: run 9/6/2026, 11:00:46 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T16:54:03.465Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34043907719
---

**Found while bringing #817 forward, 2026-09-04.** On a clean `dev`:

```
$ python3 tools/crosswalk_census_1840_heads.py --check
BAD: counts on disk {'named_heads': 498, 'matched': 5, 'candidate': 5, 'refused': 488}
     do not follow from the inputs {'named_heads': 733, 'matched': 9, 'candidate': 16, 'refused': 708}
BAD: 498 head(s) on disk, 733 read from the pages
```

## This is the owner's original complaint, in its purest form

T-0584 — *"the 1840 census left sheets printed 210 and 215, read to the name and closed against
their footings"* — opened the question of research that produces no output. This is the same fault
one layer down, and worse, because here the reading DID happen: **235 more named heads have been
read off the page images than the crosswalk on disk adjudicates.** The pages were read. The
adjudication was never re-run. Nothing says so.

## Why nothing said so

`tools/check.sh` does not run `crosswalk_census_1840_heads.py --check`. Every sibling crosswalk IS
gated — `crosswalk_norris_1844`, `crosswalk_fergus_1843`, the three Fergus 1839 crosswalks, the
death notices — and each of them fails the gate the moment its committed file stops re-deriving.
This one alone is ungated, so it has drifted 235 heads without a single red build.

Re-running it is not free and must not be done blind: the tool's own output moves
`matched` 5 → 9 and `candidate` 5 → 16, and a candidate is a claim about a person. It also
rewrites `resident_crosswalk.json` wholesale (~11,000 lines), which is why it was deliberately kept
out of #817 rather than swept in.

## The ask

1. **Gate it.** Add `python3 tools/crosswalk_census_1840_heads.py --check` to `tools/check.sh`
   beside its siblings. Do this in the SAME commit as the re-derivation, so the gate never lands
   red.
2. **Re-derive it, and read the delta.** The 4 new merges and 11 new candidates are findings, not
   noise: each one is a claim that an 1840 head is a person the town already carries. They get the
   same standard as the rest — the reading as printed, the locator, the rule that fired.
3. **Say what the 235 are.** A `--report` naming which sheets the new heads came from, so the
   answer to "did reading those pages produce anything?" is a number and not a shrug.
4. **Audit for siblings.** This one was ungated; find out whether any other `--check`-capable tool
   is missing from `check.sh`. An ungated derivation is a research output that can silently stop
   existing, which is the whole class of fault the owner asked about.

**Done when** the crosswalk re-derives clean, `check.sh` runs its `--check`, the report names the
sheets the 235 heads came off, and no other tool with a `--check` mode is missing from the gate.
