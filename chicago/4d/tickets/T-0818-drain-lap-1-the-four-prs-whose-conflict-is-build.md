---
id: T-0818
title: Drain lap 1: the four PRs whose conflict is build products and nothing else
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: 905
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T19:35:25.594Z
claimed_run: null
---

**Re-cut 2026-09-05 17:10Z against the live backlog, because the first cut was overtaken
inside an hour.** The lap this ticket originally named (#892, #894, #822, #839, #868,
#858) is half merged: #892, #839, #876, #899 and #836 landed on `dev` on their own once
#836 took the published tree off the 32 MB wall. What follows is measured against `dev`
at `d6ffce99`, not against the plan.

**Three PRs whose ENTIRE conflict is build products, plus one that is nearly so.** Nothing
here needs a ruling; the whole lap is `ticket.mjs board` + `publish.sh` + a merge.

| order | PR | ticket | behind | conflicts | non-build conflicts |
|---|---|---|---|---|---|
| 1 | [#894](https://github.com/kevinrhaas/custom/pull/894) | T-0451, owner | 6 | 7 | **none** |
| 2 | [#886](https://github.com/kevinrhaas/custom/pull/886) | T-0685, owner | 19 | 7 | **none** |


**Two of this lap's four merged on their own while it was being written** —
[#898](https://github.com/kevinrhaas/custom/pull/898) at 17:20Z and
[#901](https://github.com/kevinrhaas/custom/pull/901) at 17:35Z, the latter taking
[#865](https://github.com/kevinrhaas/custom/pull/865) with it as the superseded duplicate
on T-0509. #898 while this ticket was being written — it stood zero commits behind with
no conflict at all, which is what a PR looks like when nothing is wedging the lane.

**#886 was parked on the planform question and the owner ruled it (T-0808 § 3): Wright
1834 stays, nothing moves.** That is what it was waiting for, and its own acceptance 5 was
*nothing moves* — it commits the Thompson GCPs and bank trace BESIDE the Wright planform,
overwriting no waterline. **One correction rides with it and is not optional:**
`thompson_plat_1830.json` declares the two sheets agree to ±20 m against **27–60 m
measured** on the North Branch. Wright being of record does not make the other sheet agree
with it; the file states the measured figure, citing
`docs/RESEARCH/thompson_forks_georeference.md`.

**#901 supersedes [#865](https://github.com/kevinrhaas/custom/pull/865)** — same ticket
T-0509, opened 17:02Z against #865's 09:58Z, and its own title says it is *"the reading the
32 MB wall held back"*. **Verify that before closing #865**, don't assume it: #865 carries
43 conflicts and ~36 non-build files against #901's 6 and one. If #901 really carries the
same reading, #865 closes with a comment naming it; if it does not, #865 is the one to land
and #901 is the duplicate. Closing the loser is part of this lap, not a follow-up.

---

## HOW THIS LAP PICKS ITS PRs — the rule, because the list goes stale in under an hour

**Do not trust the table below. Re-derive it.** This ticket was written at 16:00Z against
21 open PRs; by 17:30Z the lane had merged eight of them unaided and replaced two more with
fresh PRs on the same tickets (#865 → #901, #835 → #902). A hard-coded list is a snapshot,
and a snapshot of this backlog is wrong within the hour.

The lap's membership is a MEASUREMENT, and it takes about a minute:

```
# 1. what is open, and against what
#    (the open PR list, base dev, minus drafts and minus `hold` you have not cleared)
# 2. for each one, how far behind and what actually conflicts:
git fetch origin dev <branch>
MB=$(git merge-base origin/dev origin/<branch>)
git rev-list --count $MB..origin/dev                      # behind
git merge-tree --write-tree --name-only origin/dev origin/<branch> \
  | grep -vE 'BOARD\.md|tickets\.json|build\.json|walk/index\.html|dev-smoke-state\.json|QUEUE\.md|changelog\.js'
```

**That last grep is the whole classifier.** What it strips is build products — regenerate
them, never merge them. What survives is the real work, and the lap is sorted by how much
of it there is:

| band | survives the grep | lap |
|---|---|---|
| nothing | pure build products | **this one, T-0818** |
| a short named tail | a coverage note, a README, a built index | T-0806 |
| a hundred-odd records | mostly the published mirror | T-0807 |

**A PR that has been superseded by a fresher PR on the same ticket is closed, not merged**
— check the ticket id in the title before adding anything to a lap.

**Acceptance:** #898, #894, #886 and #901 merged into `dev` in that order (squash);
`thompson_plat_1830.json` corrected in #886's own PR; #865 or #901 closed as the duplicate
with the comparison written into the comment. Every build product REGENERATED from its
source, never hand-reconciled. `./tools/check.sh` exit 0 with `Queue OK`,
`check-changelog.mjs` green, no conflict marker under `chicago/4d/` or `site/`. Open PRs
against `dev`: **8**.
