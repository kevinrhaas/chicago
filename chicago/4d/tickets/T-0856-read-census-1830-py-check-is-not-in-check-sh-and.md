---
id: T-0856
title: read_census_1830.py --check is not in check.sh, and dev was red on it: the 1830 crosswalk had drifted off the folded household tree unseen
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-17
pr: 1379
claimed_by: run 9/17/2026, 1:05:13 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T07:03:58.588Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35188132337
---

read_census_1830.py --check is not in check.sh, and dev was red on it: the 1830 crosswalk had drifted off the folded household tree unseen.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Measured 2026-09-06 on this run's own checkout of `dev`, before anything was touched.**
`python3 tools/read_census_1830.py --check` FAILS on dev:

    FAIL resident_crosswalk.json: hand-edited — it does not match what the committed reading rebuilds

Nothing was hand-edited. The 1830 crosswalk names, for every refused surname-only pair, the town
households the surname reaches — and T-0839 and its siblings have since FOLDED several of those
households onto the cards they duplicate. `hh_owen_t_j_v`, `hh_owen_th_j_v`, `hh_owen_thomas_j_v`
and `hh_owen_thomas` are gone into `hh_owen_thomas_jv`; `hh_allen_james`, `hh_allen_lieut` and
`hh_allen_lieut_j` into their survivors; three of the four Fullertons into
`hh_fullerton_alexander`. So the committed crosswalk went on printing refusals against cards that
no longer exist, and `data/research/residents/identity_master.json` — which copies those refusal
strings verbatim — printed them too.

**Why nothing caught it.** `tools/check.sh` does not run `read_census_1830.py --check` at all.
It runs `research_domains.py --check` (green, because that gate does not re-derive this file) and
`consolidate_resident_evidence.py`'s own re-derivation of `identity_master.json` — and that second
one only went red once the crosswalk beneath it was rebuilt. So the drift was invisible from
below AND from above: the file that had moved was not checked, and the file that checks was
consistent with the stale copy.

T-0757 rebuilt both in passing, because its own edit to `read_census_1830.py` made `--build`
unavoidable. That repairs today's instance and not the hole.

## The ask

1. Wire `python3 tools/read_census_1830.py --check` into `tools/check.sh`, beside the other
   re-derivations, so this domain cannot silently drift from its own build again.
2. Say what else in `data/research/` derives from `data/residents/households/` and is likewise
   unchecked — a household fold moves every refusal string in every domain that prints one, and
   this cannot be the only one.
3. No reading changes and no grade moves: this is a gate, not a research pass.

**Links:** T-0757 (which found it) · T-0814 · T-0715 · T-0691 — the same shape of fault, each in
its own writer: a generated artefact nobody re-derives.

