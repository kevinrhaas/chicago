---
id: T-1282
title: The lap cannot re-derive a resident household card, so any PR that conflicts on hh_*.json is refused whole
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-17
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

`tools/derived_manifest.json` enumerates, deliberately rather than by glob, every generated
path whose merge conflict the lap may clear by re-running a build. Thirty-six steps are listed
today. **Not one of them resolves a resident household card.** Measured on `dev` at
d1ae03268: the steps that touch the residents layer resolve `directories.json`,
`identity_master.json`, `source_coverage.json`, `grading_proposal.json`, `pass_14_findings.json`,
`town_card_candidates.json`, `index.json`, `ladder_spend.json` and `person_facts.json` — and
nothing under `data/residents/households/`.

So `data/residents/households/hh_*.json` is a path the lap refuses, and by `_the_rule` it
refuses the ENTIRE pull request rather than that file. There are roughly a thousand of those
cards and they are written by tools, not by hand, which is the shape the manifest exists for.

**How it was found.** T-1155's branch was hand-merged on 2026-09-17 and the merge would not
converge; `hh_sweet_alanson.json` was the file it broke on. The same refusal is the reason the
lap left six PRs alone in run 35235341167 — a different unlisted path that time
(`T-0509_resident_research_working.xlsx`, fixed by adding it to
`complete_resident_research_pass_14.py`'s `resolves`), same mechanism, and this is the next
instance of it.

**What makes this more than a missing line.** `derive_resident_roles.py --write` is the writer
behind those cards. It is gated — `check.sh` runs `--check` and `--self-test` at the
"resident roles re-derive" step — so `_only_gated_tools` is satisfied. But `_must_reproduce` is
the rule that decides, and it has to be MEASURED, not assumed: on a clean tree, does `--write`
rewrite bytes that `--check` calls fine? `crosswalk_census_1840_heads.py` passed `--check` and
still rewrote 137 lines, and it is correctly not listed. Do the same measurement here before
listing anything.

Note also that the step's placement is already constrained: `qualify_later_trades.py` carries a
`why` saying it MUST run before any writer that re-derives roles from the same card, because
both write `hh_elston_daniel` and the other order leaves whichever ran first red. A roles step
goes after it.

**Acceptance:** determine, by running it on a clean `dev`, whether
`derive_resident_roles.py --write` reproduces the committed household cards byte for byte. If
it does, add it to `tools/derived_manifest.json` after `qualify_later_trades.py`, with
`resolves` naming the household paths it actually writes and a `why` recording this finding;
then `node tools/rederive.mjs --check` and `--prove` must pass, and `./tools/check.sh` must be
green. If it does NOT reproduce, add nothing — record the measurement in this ticket and in a
`why`-style note beside `_must_reproduce`, so the next run does not spend the afternoon
re-discovering that the entry is inadmissible. Either outcome closes this ticket; a listed
step that cannot reproduce is the one failure mode the manifest's backstop cannot catch
cheaply.
