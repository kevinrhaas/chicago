---
id: T-0201
title: docs/LIBERTIES.md ships committed Git conflict markers on dev and check.sh is green across them
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: XS
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-08-27
pr: null
claimed_by: null
blocked_on: Fixed and shipped as T-0207 in PR #383: tools/test_no_conflict_markers.py is on dev and wired into check.sh, the three markers are gone from docs/LIBERTIES.md and data/liberties.json, and the repair reached production in release-v272. Filed independently before that landed.
needs_bake: false
---

`docs/LIBERTIES.md` ships committed Git conflict markers on `dev`, and `tools/check.sh`
is green across them.

## The evidence, off `origin/dev` (found 2026-08-24 while working T-0026)

    git show origin/dev:chicago/4d/docs/LIBERTIES.md | grep -n '^<<<<<<<\|^=======\|^>>>>>>>'
    7741:<<<<<<< HEAD
    7814:=======
    7815:>>>>>>> origin/dev

`### L181` — the poplar rows — sits **inside** that hunk, and the `origin/dev` side of it is
empty, so the resolution is trivial: keep L181, delete the three marker lines. It is not
filed here because it was hard. It is filed here because **nothing noticed.**

## Why it is worse than T-0186 and not the same ticket

T-0186 is about a merge that comes out *clean* and wrong — two branches each taking
`L177`, auto-merged, duplicate committed. This is a merge that came out **conflicted**, was
committed unresolved, and still passed every gate:

- `python3 tools/compile_liberties.py --check` → *"OK: 182 liberties, data/liberties.json
  matches its markdown"*. The compiler skips the marker lines because they match no entry
  pattern, so the markdown and the JSON agree — about a file with an unresolved conflict in it.
- `bash tools/check.sh` → **CHECK PASS** on 2026-08-24 with the markers present.

A conflict marker is the one failure mode a text gate should never miss, and this project's
own standard for the changelog is exactly that: `tools/check-changelog.mjs` *parses the
result* and fails on a malformed literal, because "`merge=union` runs during the merge, so
both parents can be green and the result broken" (AGENTS.md). The liberty ledger has no
equivalent.

## The fix, and it is small

A conflict-marker scan over the repository's committed text — at minimum
`docs/LIBERTIES.md`, `docs/ROADMAP.md`, `docs/STATUS.md`, `tickets/*.md` and
`renderers/web/js/changelog.js`, the five files ten parallel branches all append to — as a
step of `tools/check.sh`, plus the one-time resolution of the three lines above. It is
cheap, it is absolute (zero today once resolved), and it cannot cry wolf: no legitimate line
in this repository begins with seven `<`, `=` or `>`.

Deliberately NOT folded into T-0186: that ticket's acceptance is about duplicate NUMBERING
and the `## Resolved` exemption, and its check has to reason about lettered sub-entries. This
one is a two-line regex and should not wait behind that design question.

## Acceptance

- `tools/check.sh` fails on a committed conflict marker in any of the append-heavy text
  files, demonstrated failing by introducing one and removing it again.
- The three marker lines in `docs/LIBERTIES.md` are resolved — L181 kept whole, markers
  gone — and `compile_liberties.py --check` still re-derives `data/liberties.json` byte for
  byte.
- The reason the check exists is written next to it, the way the changelog contract's is.
