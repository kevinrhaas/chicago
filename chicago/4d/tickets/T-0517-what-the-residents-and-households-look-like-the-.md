---
id: T-0517
title: What the residents and households look like: the summary the owner asked for, and residents_1835.md still documents the pre-rename model
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-02
closed: 2026-09-05
pr: 847
claimed_by: run 9/5/2026, 6:36:26 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T11:54:27.786Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33963518050
---

**The owner's ask, 2026-09-03, verbatim:** "then i would like a summary of what the residents and
households look like, since you have good census data now on many you should be able to improve that."

**The finding.** The population layer has changed three times in two days (#668, #670, and the sweep
above) and no document describes it. `docs/RESEARCH/residents_1835.md` — the layer's dossier — still
prints the pre-rename vocabulary (`documented` / `derived` / `inferred`), reports "72 households, 96
person entries", and does not mention `hh_ll_*`, `projected_resident`, `resident_research`,
`later_census` or any ticket after T-0378. `docs/RESEARCH/resident-household-synthesis-2026-09-02.md`
is a receipt for one day. The owner wants to know what the town's people look like now.

**The ask.**

1. `docs/RESEARCH/residents-households-summary-2026-09.md`: households and persons; by grade and
   subtype; by division and scene-date presence; by sex where recorded; occupation coverage (how many
   carry a trade, from which source); household size distribution; evidence coverage per domain
   (newspaper / civic / 1830 / 1840 / church / book / directory) and the overlap; letter-list-only and
   1840-linked counts; what the sweep added and regraded against the #668 baseline (117 attested / 731
   inferred / 706 projected / 848 persons / 824 households); and what remains unresearched or
   unresolved. **Every number is reproduced by a stated command** over `data/residents/index.json`,
   `data/town_census.json` and `data/research/residents/identity_master.json` — a summary a later run
   can re-derive, not a snapshot.
2. Rewrite `docs/RESEARCH/residents_1835.md` for the current model: the three grades and the subtype,
   the household families (`hh_`, `hh_doc_`, `hh_placed_`, `hh_ll_`, and the civic mint), the mint
   precedence, the evidence blocks, the 1840 bridge rule, the liberties (L205–L214 and the new one),
   the gates. It no longer names `reconstructed` as a live grade nor `documented` at all.
3. Re-run **T-0512**'s audit export so the two audits bracket the programme.
4. Write the owner's report section: five paragraphs, the numbers, the gaps, the recommendation for the
   placement sweep — this is what the session hands the owner.

**Dependency:** T-0515 must be `done`.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Every figure in the summary carries the command that reproduces it, and running them reproduces
  them; `residents_1835.md` no longer contains `documented` or names `reconstructed` as live.
- The audit export is regenerated and matches; `check.sh` green (the dossier-link gate included).

**Links:** T-0512 · T-0513 · T-0514 · T-0515 · `docs/RESEARCH/residents_1835_inferred.md` (stale in the
same way — note it, do not rewrite it here).
