---
id: T-0491
title: dev's gate is red on an unmodified dev: the register drifted, two mirrors are stale, an index count disagrees, and #670 left scaffolding and two off-schema source records
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-03
pr: 682
claimed_by: run 9/3/2026, 1:27:47 AM CT
blocked_on: null
needs_bake: false
---

**`tools/check.sh` is RED on an unmodified `dev`**, and has been on every push since 2026-09-02 17:09Z
(gate runs 3133 through 3446 all `failure`). Run 3446 — the owner's merge of PR #670 at `6e72679b` —
fails on three distinct things, and every branch cut from `dev` inherits all three before it changes a
line:

```
the scene-date register re-derives, and every action names its target          FAILED
  chicago/4d/data/research/newspapers/register_1835.json is not what a rebuild produces —
  run tools/compile_register.py --build and commit the result
published mirror matches its source                                              FAILED
  data/residents/households/hh_miller_john.json DIFFERS from its source
  data/residents/households/hh_murphy_john.json DIFFERS from its source
the reconstructed residents' invented names re-derive  (and three more steps)    FAILED
  RESIDENT SYNTHESIS FAIL — index attested count disagrees with records
```

A local run of the gate on a clean checkout of `6e72679b` (2026-09-03, the ticket-filing branch, which
touches nothing outside `tickets/`) finds a FOURTH, same-origin failure the CI tail did not show:

```
every flora and fauna figure is declared read or banked unread                   FAILED
  residents/household:persons[].later_census.source_id is banked as reaching nothing and the
  renderer accesses it …
  residents/household:persons[].later_census.{bridge_basis, bridge_status, census_page, census_row,
  head_name_*, household.*, source_image, year, …} is a figure on 3 record(s) that no renderer reads,
  and it is not in layer_reads_baseline.json. Wire it up, or bank it with --update in this commit …
```

— `tools/measure_layer_reads.py --gate` against `tools/layer_reads_baseline.json`: PR #670 added the
`later_census` block to three persons without declaring which of its figures the renderer reads
(`renderers/web/js/residents.js`) and which are banked unread. The honest fix is to DECIDE — show the
1840 link on the card (year, serial, page/row, the "later evidence" note) and bank the rest with
`--update` and the reason in the commit message — not to bank everything so the step passes.

The first of the three CI faults dates from PR #668 (the resident synthesis regenerated residents without rebuilding the
register); the second and third from PR #670 (`hh_adams_william_h` was added as `attested` and the
Miller/Murphy records gained `later_census` blocks, but `data/residents/index.json` counts and the
published mirror were not regenerated). Read T-0389 first: it is the same fault class, and the rule it
set stands — **the fix is one honest regeneration per fault, never a loosened assertion.**

**PR #670 also left its own scaffolding on `dev`**, which its body said would be removed before merge:
`data/research/residents/README_669.tmp`; `census_bridge_recovery_status.json` still reading
`"status": "in_progress"`; `census_1840_identity_bridges_pending.csv` still listing William Hanford Adams
as `canonical_person_id_not_yet_resolved` although `hh_adams_william_h.json` now exists; two source
records outside `data/source.schema.json`'s enums — `resident_research_v4_1835_census_bridge.json`
(`type: research_synthesis`, `rights_status: research_notes`) and `census_1840_chicago_v4_research.json`
(check its `type` too) — the schema allows `type` ∈ map/book/newspaper/manuscript/illustration/photograph/
website/dataset/article/legal and `rights_status` ∈ public_domain/no_known_restrictions/check_required/
cleared/restricted, with `additionalProperties: false`; no changelog entry although the PR body said
one was required; and `tools/apply_census_1840_bridges.py --check` runs only in its own workflow
(`.github/workflows/census-bridge-generate.yml`), not in `check.sh`, so the bridge contract is ungated
on the gate that matters.

**Also note for the fix, not for this ticket's scope:** `check.sh` now calls
`tools/synthesize_resident_research.py --check` under FIVE different historical step labels (the old
generate/mint/replace steps were pointed at it in commit 1d3ddade). Leave that as is here — one
repair per ticket — but say in the PR that a later cleanup could collapse them.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- `bash tools/check.sh` exits 0 on a clean checkout of `dev` after this merges, and the PR body links the
  green gate run on `dev` — not on the branch.
- `register_1835.json` is rebuilt by `tools/compile_register.py --build`, and the PR states what changed
  in it and why (which residents moved which actions).
- `data/residents/index.json` counts are regenerated by the tool that owns them (the synthesis/bridge
  build paths), not edited by hand; the published mirror is refreshed by `tools/publish.sh`.
- The two source records validate against `data/source.schema.json` with values that are TRUE (`type:
  dataset`; a rights status the record can defend, with `rights_note` saying it is project research
  derived from public-domain census pages), not merely values that pass.
- `README_669.tmp` is gone; the recovery status file says complete with the date; the pending CSV either
  resolves Adams to `adams_william_h` or is deleted with the reason in the PR.
- `apply_census_1840_bridges.py --check` is a `check.sh` step beside the synthesis step, with the prose
  comment every step carries.
- A changelog entry for the #670 recovery is prepended with `v: null`, `ts: ''`, `date: ''` and stamped
  with `node tools/stamp-changelog.mjs`; `node tools/check-changelog.mjs` passes.
- `tools/measure_layer_reads.py --gate` is green because the `later_census` figures are declared
  read or banked with a stated reason — not because the baseline was regenerated wholesale.
- The gate is not weakened anywhere; `node tools/ticket.mjs check` is green.

**Links:** gate runs 3422 (#668 merge) and 3446 (#670 merge) · T-0389 and T-0215 (the cost every branch
pays while dev is red) · PR #668, PR #670 · commit 1d3ddade ("restore clean dev gate") · this band's
rationale in QUEUE.md.
