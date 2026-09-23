---
id: T-0180
title: The bake opens a content PR on every run, because the build stamp it writes is always dirty
state: done
epic: META
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-08-29
pr: 579
claimed_by: run 8/29/2026, 9:32:49 PM CT
blocked_on: null
needs_bake: false
---

The bake opens a content PR on every run, because the build stamp it writes is always dirty.

## What was seen

Four bake PRs open at once on 2026-08-24 — #349 (run 32688616908), #351 (32690517288),
#353 (32696112597), #354 (32696836806) — spanning 04:41 to 06:56 UTC. Every one of them
changes exactly TWO files and no geometry, no assets, no data:

    site/chicago/4d/build.json      | 6 +++---
    site/chicago/4d/walk/index.html | 2 +-

and the whole of that diff is the stamp:

    -  "version": "762fa99c",
    -  "built_utc": "2026-08-24T06:04:28Z",
    +  "version": "55fca619",
    +  "built_utc": "2026-08-24T06:32:39Z",

## Why it happens

`chicago-4d-bake.yml`'s "Push a bake branch" step decides whether the bake produced
anything with

    if [ -z "$(git status --porcelain)" ]; then ... changed=0

`build.json` carries `built_utc`, a wall-clock timestamp, and `version`, the head sha.
Both move on every run by construction, so the tree is ALWAYS dirty and `changed` is
always 1. The `changed=0` branch is unreachable in practice.

## Why it matters

The PR is the signal that a bake produced new content. That signal is dead — it fires
identically whether 300 structures were rebuilt or nothing at all was. A reviewer cannot
tell the two apart without diffing each branch by hand, which is what this ticket did.

It also queues: one PR per run, none self-closing, four in six hours once the nightly
started succeeding (T-0114/T-0165/T-0171). The pileup is a symptom; the dead signal is
the defect.

Note the determinism story is INTACT and this is evidence for it, not against it — the
geometry re-baked byte for byte across all four runs, which is exactly what
`assets/manifest.json`'s inputs-based determinism promises. Only the stamp moved.

## The fix, roughly

Decide `changed` on the content rather than on the whole tree: exclude the stamp files
from the dirtiness test, and if nothing else moved, skip the branch and the PR (and say
so in the log). The stamp still gets written and still ships with the next PR that
carries real content — it just stops being the thing that manufactures one.

Two traps worth stating before someone implements it:

- Do NOT stop writing the stamp. The gate screen reads it ("build 55fca619 · Aug 24,
  2026, 1:32 AM CT") and it is how a visitor and a bake report agree on what is live.
- The stamp can never be self-consistent with the commit that carries it: merging it
  changes the head sha it names. That is inherent, not a bug to chase.

## Acceptance

- A bake run over unchanged inputs pushes no branch, opens no PR, and logs why.
- A bake run that changes any geometry, sidecar, derivative or data file still opens one.
- Demonstrated by two consecutive runs on `dev` with no content change between them:
  the first may carry a stamp, the second opens nothing.

---

## DONE 2026-08-30 — THE VERDICT IS ASKED OF THE CONTENT, AND IT IS A SCRIPT WITH A SELF-TEST

**Still true when this was taken.** Five `steward/bake-*` branches had been pushed to this
repository in the hour before this run started, and the newest four were 01:17, 01:28,
01:41 and 02:07 UTC — the same pileup the ticket recorded on 2026-08-24, six days on.

**What changed.** `chicago-4d-bake.yml`'s dirtiness test is gone. In its place the bake
runs `tools/bake_content_changed.py --github`, which writes `changed=0` or `changed=1`
into `$GITHUB_OUTPUT`, and the push step reads that instead of `git status --porcelain`.
Everything downstream — the branch, the artifact, the smoke, the PR — is unchanged.

**The test is narrower than the ticket's own sketch, on purpose.** "Exclude the stamp
files from the dirtiness test" would also mean a real change to `build.json` or to the
gate page never opens a PR again, which is the same dead signal pointing the other way. So
a dirty path is stamp-only when it is one of the two paths `publish.sh` stamps AND the
only thing that moved inside it is the stamp:

- `site/chicago/4d/build.json` — parsed as JSON both sides; stamp-only when the keys that
  differ are within `{version, built_utc, built_ct}` and the key SET has not changed.
- `site/chicago/4d/walk/index.html` — both sides normalised by putting the rendered
  `gate-build` paragraph back to the `<!--BUILD_STAMP-->` placeholder `publish.sh` found
  there; stamp-only when they are then identical.

Anything else — a new file, a deletion, a rename, a byte of data — is content.

**Both traps the ticket named are held.** The stamp is still written by `publish.sh` on
every run, still read by the gate screen, and still ships with the next PR that carries
content; what stops is the stamp MANUFACTURING that PR. And nothing here tries to make the
stamp self-consistent with the commit that carries it, which it cannot be.

**What was demonstrated in this run.**

- *The real case, on this checkout.* `tools/publish.sh` on an otherwise-clean tree leaves
  exactly `site/chicago/4d/build.json` and `site/chicago/4d/walk/index.html` dirty — the
  two files, and the whole diff, this ticket was filed about — and the verdict is
  `bake produced no CONTENT`.
- *The positive control.* One byte appended to a file under `chicago/4d/` and the same
  command reports `bake produced content — 1 path(s) beyond the build stamp`, naming it.
- *Seven sandbox cases,* in `--self-test`: a clean tree, a stamp-only bake, a data byte, a
  new published file, the gate page changed away from its stamp, `build.json` growing a
  real field, and a deleted data file.
- *Two drift guards,* in the same self-test, read out of `publish.sh` itself: that it still
  writes the stamp into `build.json`, and that it still stamps the gate page's placeholder.
  If a third stamped path is ever added, this is what says so.
- The self-test runs in `tools/check.sh`, so the bake's decision is gated on every commit
  rather than only when the nightly next fires.

**NOT claimed, and it is the third acceptance line.** *"Demonstrated by two consecutive
runs on dev with no content change between them"* cannot be run from a branch — the
nightly bakes `dev`, and this is not on `dev` until it merges. The demonstration lands on
the first two nightlies after this merges: the first may carry a stamp, and the second
should push nothing and log why. Anyone reading this afterwards can check it in one
place — a night with no `steward/bake-*` branch is the ticket closed for real.

**Links:** `.github/workflows/chicago-4d-bake.yml` · `chicago/4d/tools/bake_content_changed.py`
· `tools/publish.sh` · `tools/check.sh` · T-0114 · T-0165 · T-0171.
