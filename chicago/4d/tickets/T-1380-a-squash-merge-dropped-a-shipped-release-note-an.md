---
id: T-1380
title: A squash merge dropped a shipped release note and re-used its version: v971 named 'Six dates that would not stick' on dev at 06:06 and names 'How many people each tavern and boarding house could sleep' at 06:31, and the first entry is gone from the file the launcher and Manager parse
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-19
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

A squash merge dropped a shipped release note and re-used its version: v971 named 'Six dates that would not stick' on dev at 06:06 and names 'How many people each tavern and boarding house could sleep' at 06:31, and the first entry is gone from the file the launcher and Manager parse.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-1367**, resolving its own changelog conflict against a moved `dev`.

`git log -S "Six dates that would not stick"` names two commits: `5fc0e7507` (T-1366,
PR #1502) added the entry as **v971**, ts `2026-09-19T06:06:11.774Z`; `a1fecdb70`
(T-1370, PR #1504) removed it. #1504 branched before #1502 merged, and its changelog
resolution took its own side of the file whole — so the entry that shipped an hour
earlier is gone from `origin/dev`, and **v971 now names T-1370's release instead**.

`grep -c "Six dates that would not stick"` on `origin/dev`: 0.

This is the failure the version contract is built to prevent, arriving from the other
direction. The house rule (author `v: null`, let the repo's stamp tool assign after the
merge) stops two branches CLAIMING the same number; it does nothing about a merge that
DELETES a stamped entry and frees its number to be re-assigned. `check-changelog.mjs`
reads the file it is given and cannot see an entry that is no longer in it.

`.gitattributes` does not carry `merge=union` for this path — the merge conflicted rather
than unioning, which is what left the resolution to a branch that could not see the entry.

**What is at stake:** Manager and the launcher parse the published `changelog.js` live, so
a version number that changes meaning after it has been ingested is a fact about a release
that is now wrong in two places.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. The lost entry is back and every version number names exactly one release, forever —
   the ordering question is the real one: the entry's `ts` (06:06) puts it BELOW v971
   (06:31), so it cannot simply take the next number off the top. State the rule chosen.
2. A merge that DROPS a stamped entry is loud. `check-changelog.mjs` (or a gate beside it)
   fails when a version present in the merge base is absent from the result — with a
   firing self-test.
3. Consider `merge=union` in `.gitattributes` for `renderers/web/js/changelog.js`, which is
   what the fleet contract assumes is already there.
