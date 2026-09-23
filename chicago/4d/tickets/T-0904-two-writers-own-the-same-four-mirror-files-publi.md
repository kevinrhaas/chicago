---
id: T-0904
title: Two writers own the same four mirror files: publish.sh compacts what synthesize_resident_research.py pretty-prints, and whichever runs last decides whether the drift gate is green
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-07
pr: null
claimed_by: null
blocked_on: Superseded: the same fault was already filed as T-0874, T-0880 and T-0905, and T-0933 CLOSED it — T-0938 took the published mirror off the PR surface entirely, so publish.sh and synthesize_resident_research.py no longer contend over four committed mirror files. Filed on this branch on 2026-09-06, before that landed.
needs_bake: false
closed_at: 2026-09-07T07:33:22.681Z
claimed_run: null
---

Two writers own the same four mirror files: publish.sh compacts what synthesize_resident_research.py pretty-prints, and whichever runs last decides whether the drift gate is green.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0723, 2026-09-06.** Four files under `site/chicago/4d/data/residents/` are
written by two tools that disagree about their formatting:

- `tools/publish.sh` mirrors `data/residents/` into the site payload **compact**;
- `tools/synthesize_resident_research.py` writes the same four files **pretty-printed**,
  and `--drift` (the T-0838 gate, in `check.sh`) fails on any file whose bytes are not
  what that writer produces.

The four: `index.json`, `households/hh_adams_william_h.json`, `households/hh_miller_john.json`,
`households/hh_murphy_john.json`. Their CONTENT is identical either way — `json.load` on the
two versions compares equal — so nothing on the site changes; only the bytes and the gate do.

**How it shows up.** A run that touches the residents layer must do its rebuilds in one exact
order — publish, then synthesize — or the gate goes red on files its change never mentioned.
T-0723 hit it twice and had to establish the order by experiment. Committed dev satisfies the
drift gate, which means dev's mirror is what the SYNTHESIZER wrote and dev's publish of those
four files is stale; run `./tools/publish.sh` alone on a pristine dev checkout and the gate
turns red on a tree nobody edited.

**Acceptance:** one writer owns each of the four files. Either publish.sh stops writing them
(the synthesizer already does, and the site reads the same JSON), or the synthesizer writes
them the way publish.sh does and the baseline follows — decided by which tool the site
payload's own freshness check regards as the author, not by whichever is easier to change.
`./tools/publish.sh` on an untouched checkout of dev must leave `--drift` green afterwards,
and the order in which a run does its rebuilds must stop mattering.

**Links:** T-0723 · T-0838 · `tools/publish.sh` · `tools/synthesize_resident_research.py`
