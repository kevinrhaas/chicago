---
id: T-0740
title: The Newberry leads have drifted from the layers beneath them: a plain --parse rewrites leads.json by 6,039 lines and leaves five leads unruled
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: 878
claimed_by: run 9/5/2026, 6:48:31 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T12:27:15.443Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33963509540
---

The Newberry leads have drifted from the layers beneath them: a plain --parse rewrites leads.json by 6,039 lines and leaves five leads unruled.

**Found by T-0582**, which added a WORKS pattern for Wood 1881 and then could not commit
the re-parse that would carry it into the cards.

`tools/read_newberry_index.py --parse` is deterministic over the committed card text AND
the layers it looks leads up in — residents, voters, the 1840 heads, structures. Those
layers have grown since `leads.json` was last generated (cohorts 13 and 14, the census
reads), and `--parse` is the only thing that notices. Measured on dev at 85d650116, with
NO source change at all: running `--parse --volume 1..4` in a clean worktree of
`origin/dev` leaves the tree dirty —

| file | diff |
|---|---|
| `leads.json` | +6,039 lines |
| `follow_up.json` | 54 lines |
| `entries.json` | 24 lines |
| `records/entries_vol_01..04.json` | 6 lines each |

and `tools/check.sh` then reports three things it does not report on dev: `lead_crosswalk.json
does not re-derive from leads.json and the committed cards`, `5 lead(s) offered and not ruled
on` (`lead_v01_abbott_census_1840`, `alley`, `andrus`, `armatrong`, `arnold_residents`), and
`acquisition_list.json does not re-derive from the committed cards`.

So the committed generated data is a snapshot of layers that no longer exist, and the gate
cannot see it, because the gate re-derives the crosswalk from the COMMITTED leads rather than
from a fresh parse. Nothing is wrong in the files; they are just old, and any run that touches
the works table has to choose between shipping a stale parse and shipping 6,039 unrelated lines.
T-0582 chose neither and left the Wood 1881 clustering out of the cards (8 cards, 5 Chicago or
Cook, 1 on a lead surname; the unmatched residue falls 4,175 -> 4,167 and its Chicago half
375 -> 370). Those counts are in a comment on the WORKS entry until this lands.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)
- `--parse` over all four volumes is re-run and its output committed, with the five new leads
  ruled on through `tools/rule_newberry_leads.py` so `check.sh` is no redder than dev.
- Whatever makes a re-parse a no-op when nothing has changed — a check that fails when the
  committed leads do not re-derive from a fresh parse, run in `check.sh` — so the next drift
  is found by the gate and not by a run that tripped over it.
- The Wood 1881 clustering is in `follow_up.json` and the comment on its WORKS entry comes out.
