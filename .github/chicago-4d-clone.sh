#!/usr/bin/env bash
# chicago-4d-clone.sh — T-0232: the bounded, retried partial clone the
# chicago-4d workflows share.
#
#   GITHUB_TOKEN=… GITHUB_REPOSITORY=owner/repo chicago-4d-clone.sh <branch> [branch…]
#   chicago-4d-clone.sh --self-test
#
# Why this exists, measured: actions/checkout@v4 + fetch-depth:0 on this
# repository is a lottery. The pack is 1.31 GiB — overwhelmingly superseded GLB
# masters the chicago-4d jobs never open — and checkout across the eight jobs of
# ONE bake run measured 37s, 47s, 54s, 2m20s, 3m32s, 3m40s, 4m45s and 7m11s, with
# a ninth still cloning at 30 minutes when it was cancelled. On the owner's
# promotion switch it was worse because the switch is dispatch-only: run #12
# burned its whole 15-minute cap inside checkout and never reached a promotion
# step, and post-hotfix run #15 spent >=18m28s there before an operator cancelled
# it — while run #16, same repo, same ref, twenty minutes later, checked out in
# 35 seconds. actions/checkout has no retry of its own and a step timeout fails
# the job rather than re-rolling, so this is plain git under timeout(1): a bad
# draw costs ONE bound (default 4 minutes) and the next attempt re-rolls. On
# run #16's numbers a 4-minute bound costs a bad draw four minutes and touches
# the good draws not at all.
#
# The jobs keep the full commit history (rev-list main..dev, merge-base, real
# merges), so every attempt fetches commits and trees for the named branches
# with --filter=blob:none and pulls blobs on demand — the same partial-clone
# shape as the checkout this replaces, minus the coin toss. An attempt is
# bounded end to end: the fetch AND the checkout, because checkout pulls the
# working tree's blobs on demand and can draw the bad ticket by itself. An
# attempt that overruns is abandoned wholesale; the objects already fetched
# stay fetched, so a retry resumes rather than restarts.
#
# Every attempt's elapsed is written to $GITHUB_STEP_SUMMARY, so the
# distribution stops being reconstructed from timestamps after the fact — run
# #15's ">=18m28s" was a lower bound read off created_at/updated_at, which is
# how a cancelled run's duration got misread once already.
#
# Deliberate limits, stated where the next editor will look:
#   * The on-demand blob fetches inside LATER git commands (merge, worktree add)
#     are NOT bounded here — killing a merge mid-write is damage, not retry.
#   * The 1.31 GiB pack itself is the root cause; every item above is
#     mitigation and the pack is the only cure. Its scoping — history rewrite,
#     LFS, or a different home for the masters — lives in T-0232 item 4.
#   * CLONE_URL_OVERRIDE exists for --self-test (a file:// upstream in /tmp).
#     It is not a back door: the production callers pass only the branch list.
set -euo pipefail

if [ "${1:-}" = "--self-test" ]; then
  # The acceptance demonstration, committed: stand up a tiny upstream in /tmp,
  # shim PATH with a git whose FIRST fetch hangs past the bound (the injected
  # bad draw), and require this script to abandon attempt 1 at the bound and
  # succeed on a later attempt. A green run on a fast draw proves nothing; this
  # proves the mechanism that only exists for the slow one.
  self="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
  tmp="$(mktemp -t t0232-selftest.XXXXXX)"; rm -f "$tmp"; mkdir -p "$tmp/bin" "$tmp/src" "$tmp/work"
  cleanup() { rm -rf "$tmp"; }
  trap cleanup EXIT
  git init -q "$tmp/src"
  ( cd "$tmp/src" && git config user.email t@t && git config user.name t \
      && echo hello > f.txt && git add . && git commit -qm one \
      && echo world >> f.txt && git commit -qam two )
  git init -q --bare "$tmp/upstream.git"
  git -C "$tmp/src" push -q "$tmp/upstream.git" master:main 2>/dev/null \
    || git -C "$tmp/src" push -q "$tmp/upstream.git" master
  cat > "$tmp/bin/git" <<EOF
#!/bin/bash
if [ "\$1" = "fetch" ] && [ ! -e "$tmp/spent" ]; then
  touch "$tmp/spent"
  echo "SELF-TEST: injected bad draw — this fetch hangs 6s against a 2s bound" >&2
  sleep 6
fi
exec $(command -v git) "\$@"
EOF
  chmod +x "$tmp/bin/git"
  # cd into the scratch work tree: the clone under test does `git init .` in
  # the CWD, and inheriting the caller's directory would init the caller.
  if ( cd "$tmp/work" \
       && PATH="$tmp/bin:$PATH" \
          CLONE_URL_OVERRIDE="file://$tmp/upstream.git" \
          CLONE_BOUND_SECS=2 CLONE_ATTEMPTS=3 \
          GITHUB_REPOSITORY=self/test GITHUB_TOKEN=demo \
          bash "$self" main ) > "$tmp/out.txt" 2>&1; then
    :
  else
    cat "$tmp/out.txt"; echo "SELF-TEST FAIL: the clone did not succeed after the injected bad draw"; exit 1
  fi
  if ! grep -q 'overran' "$tmp/out"*.txt 2>/dev/null && ! grep -q 'overran' "$tmp/out.txt"; then
    cat "$tmp/out.txt"; echo "SELF-TEST FAIL: attempt 1 did not hit the bound — the bad draw was not exercised"; exit 1
  fi
  [ -f "$tmp/work/f.txt" ] || { echo "SELF-TEST FAIL: working tree missing after clone"; exit 1; }
  echo "SELF-TEST PASS: attempt 1 drew the injected bad draw and was abandoned at the 2s bound; a later attempt completed."
  grep -E 'attempt|overran' "$tmp/out.txt" | head -6
  exit 0
fi

bound="${CLONE_BOUND_SECS:-240}"
attempts="${CLONE_ATTEMPTS:-4}"
repo="${GITHUB_REPOSITORY:?GITHUB_REPOSITORY is not set}"
token="${GITHUB_TOKEN:?GITHUB_TOKEN is not set}"

if [ "$#" -lt 1 ]; then
  echo "usage: $0 <branch> [branch...]" >&2
  exit 2
fi

# bounded CMD…: run CMD under a seconds-bound, implementation by availability.
# coreutils timeout(1) on the ubuntu runners; gtimeout if a steward Mac has
# GNU coreutils; perl alarm+exec otherwise (perl ships with macOS) — the bound
# is load-bearing on every flavor, not only where timeout(1) happens to live.
if command -v timeout >/dev/null 2>&1; then
  bounded() { timeout "$@"; }
elif command -v gtimeout >/dev/null 2>&1; then
  bounded() { gtimeout "$@"; }
elif command -v perl >/dev/null 2>&1; then
  bounded() { perl -e 'alarm shift; exec @ARGV' "$@"; }
else
  echo "$0: no timeout mechanism (timeout, gtimeout, or perl) on PATH" >&2
  exit 2
fi

origin_url="${CLONE_URL_OVERRIDE:-https://x-access-token:${token}@github.com/${repo}.git}"

git init -q .
git remote add origin "$origin_url"

refs=()
for b in "$@"; do
  refs+=("+refs/heads/$b:refs/remotes/origin/$b")
done

if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  {
    echo "## Checkout — bounded clone (T-0232)"
    echo
    echo "bound ${bound}s per attempt, ${attempts} attempt(s), blob:none partial clone."
    echo
    echo "| attempt | outcome | elapsed (s) |"
    echo "|---|---|---|"
  } >> "$GITHUB_STEP_SUMMARY"
fi

attempt=1
while [ "$attempt" -le "$attempts" ]; do
  start=$SECONDS
  if bounded "$bound" git fetch --filter=blob:none --no-tags origin "${refs[@]}" \
    && bounded "$bound" git checkout -f -B "$1" "origin/$1"; then
    elapsed=$(( SECONDS - start ))
    echo "checkout attempt ${attempt}: ok in ${elapsed}s (bound ${bound}s)"
    if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
      echo "| ${attempt} | ok | ${elapsed} |" >> "$GITHUB_STEP_SUMMARY"
    fi
    exit 0
  fi
  elapsed=$(( SECONDS - start ))
  echo "::warning::checkout attempt ${attempt} overran the ${bound}s bound at ${elapsed}s — re-rolling ($(( attempts - attempt )) attempt(s) left)"
  if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
    echo "| ${attempt} | overran bound | ${elapsed} |" >> "$GITHUB_STEP_SUMMARY"
  fi
  attempt=$(( attempt + 1 ))
done

echo "::error::checkout failed ${attempts} attempt(s) under a ${bound}s bound — nothing downstream of it ran. Re-dispatch the switch."
if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  echo "| — | FAILED after ${attempts} attempts | — |" >> "$GITHUB_STEP_SUMMARY"
fi
exit 1
