#!/usr/bin/env bash
#
# preflight.sh — ask, BEFORE the PR is opened, every question CI will ask after.
#
# WHY THIS EXISTS (measured 2026-09-10). `tools/check.sh` is the gate a run runs
# and it is not the whole gate. Two of CI's questions are asked only where a base
# ref exists — on the pull_request event — so a run cannot discover its own red
# by any means available to it, opens the PR, and ends its turn. Nothing comes
# back. PR #1049 sat red for two hours nineteen minutes on a one-line commit
# trailer; its own body said "No changelog entry: this is the research gate's own
# instrument", which is exactly the sentence the gate wanted — written in the PR
# body, where the gate does not look, instead of in a commit, where it does.
#
# That is not a careless run. It is a gate a run has no way to rehearse. So:
#
#   ./tools/preflight.sh          # before `gh pr create`
#
# It runs check.sh and then the questions check.sh deliberately does not ask:
#
#   - `check-changelog-entry.mjs` against the MERGE BASE, which is the same pair
#     of shas the workflow passes it. It is out of check.sh on purpose — the
#     nightly bake regenerates data/ and correctly ships no entry, so a gate
#     inside check.sh would fail every bake (T-0409). Out of check.sh is not the
#     same as out of reach.
#   - `resolve_id_collisions.mjs --check`, because a ticket id this branch minted
#     may have been taken by a sibling slice while this run was working, and the
#     first thing that notices is the lap.
#
# It writes NOTHING. Everything here is a question; the repairs it names are the
# run's to make, and each failure prints the command that makes it.
#
# BASE defaults to `origin/dev`, which is what this repo PRs into. Override for
# the hotfix path: `BASE=origin/main ./tools/preflight.sh`.
set -uo pipefail

cd "$(dirname "$0")/.." || exit 2
BASE="${BASE:-origin/dev}"
FAILED=0

hr() { printf '\n\033[1m%s\033[0m\n' "$*"; }
bad() { printf '\033[31m  FAIL\033[0m  %s\n' "$*"; FAILED=$((FAILED+1)); }
good() { printf '\033[32m  ok  \033[0m  %s\n' "$*"; }

# Fetch so the base is today's, not whatever this clone last saw. A run that
# rehearses against a stale dev rehearses the wrong gate.
git fetch origin "${BASE#origin/}" --quiet 2>/dev/null \
  || printf '  (could not fetch %s — rehearsing against the cached ref)\n' "$BASE"

MERGE_BASE=$(git merge-base "$BASE" HEAD 2>/dev/null)
if [ -z "$MERGE_BASE" ]; then
  printf 'preflight: no merge base with %s — is the ref fetched?\n' "$BASE" >&2
  exit 2
fi

hr "1/3  the gate a run already runs"
if ./tools/check.sh >/tmp/preflight-check.log 2>&1; then
  good "check.sh"
else
  bad "check.sh — the last lines:"
  tail -12 /tmp/preflight-check.log | sed 's/^/        /'
fi

hr "2/3  does this change carry a changelog entry? (PR-event only in CI)"
if node tools/check-changelog-entry.mjs "$MERGE_BASE" HEAD >/tmp/preflight-cl.log 2>&1; then
  good "$(head -1 /tmp/preflight-cl.log)"
else
  bad "changelog entry"
  sed 's/^/        /' /tmp/preflight-cl.log
fi

hr "3/3  did a sibling slice take a ticket id this branch minted?"
if node tools/resolve_id_collisions.mjs --base "$BASE" --check >/tmp/preflight-ids.log 2>&1; then
  good "$(head -1 /tmp/preflight-ids.log)"
else
  bad "ticket ids"
  sed 's/^/        /' /tmp/preflight-ids.log
fi

if [ "$FAILED" -eq 0 ]; then
  printf '\n\033[32mPREFLIGHT PASS\033[0m — CI has nothing left to ask. Open the PR.\n'
  exit 0
fi
printf '\n\033[31mPREFLIGHT FAIL\033[0m — %d question(s) CI would have asked after the PR was\n' "$FAILED"
printf 'open, and nobody comes back to a red PR. Fix them here.\n'
exit 1
