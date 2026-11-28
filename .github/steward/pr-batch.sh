#!/usr/bin/env bash
# THE BATCH. Merge several open pull requests into ONE branch off `dev`, regenerate
# what the tools own once on the combined tree, and open that branch as one pull
# request, so the lot lands on one gate instead of one lap and one gate each.
#
#   BATCH_PRS="2401 2402 2404"  bash .github/steward/pr-batch.sh [--repo owner/name]
#
# Environment: BATCH_PRS (required: the members, in the order to merge them),
# BATCH_MIN (default 2: fewer members left after the drops means no batch),
# BATCH_DRY_RUN (build and report, push nothing, take no lock), BATCH_OUT (a
# key=value summary for the caller: pr=, branch=, members=, dropped=).
# Exit 0: a batch PR is open (or, dry, would be). 3: too few members merged.
# 1: the build failed; nothing was pushed and every lock it took is released.
#
# WHO RUNS IT: polecat-platform's steward janitor (`batch` job), which picks the
# members, holds the chicago lane while the batch is open, merges the batch PR
# with a MERGE commit once its gate is green, and restarts the lane. This file is
# only the git and the regeneration, and it lives here because every tool it
# calls does.
#
# WHY (Kevin, 2026-11-27: "Can you improve the steward janitor loop to do this
# automatically periodically?"). With five slices running, dev moves every few
# minutes and each landing re-dirties the other open PRs, so every one of them is
# lapped, re-gated (~80 min on the shared runner pool) and dirtied again before
# its gate ends. Twice that day a thread paused the lane and did this by hand:
# #2399 landed six loop PRs on one gate (merge commit c895b7776) and GitHub
# marked all six merged, because each member's head is reachable from `dev`.
# That is also why the janitor merges the batch with a MERGE commit and never a
# squash: a squash leaves every member open with its work already on `dev`.
#
# HOW A CONFLICT BETWEEN MEMBERS IS CLEARED — the PR lap's rules (pr-lap.sh), plus one:
#   * a file a tool owns (GENERATED below): take either side; the tail rewrites it
#   * an asset registry: entry by entry (merge_asset_registry.py --resolve)
#   * the derived research layer (rederive.mjs --resolvable): either side, rebuilt
#   * prose or a shell step list where BOTH sides only ADDED lines (two new check.sh
#     steps at one spot, two STATUS.md sections on top): both, one after the other
#     (tools/merge_additions.py; the #2399-evening batch needed exactly this)
#   * anything else is a real disagreement: that member is DROPPED from the batch
#     (merge aborted, its lock released) and stays open for its own lap and owner.
# Then, on the combined tree: the meshes `validate.py --stale` lists are re-emitted
# with their pure emitter's --only (tools/restamp_stale.py, byte-identical or it
# refuses), the derived layer is re-run, and the lap's own regeneration tail.
#
# THE LOCKS. Each member's `lap/pr-<N>` lock is taken before it is merged and kept
# while the batch is open, so the PR lap does not push a dev merge onto a member
# (its head would move past what the batch holds, and GitHub would not mark it
# merged) and merge-ready does not squash it on its own. A member whose lock a
# live run holds is left out. Locks age out after 3 h (ticket.mjs RUN_HOURS), so a
# batch that never lands strands nothing; the janitor deletes them once it lands.
set -uo pipefail

repo=""
while [ $# -gt 0 ]; do
  case "$1" in
    --repo)   repo=${2:-}; shift 2 ;;
    --repo=*) repo=${1#--repo=}; shift ;;
    *) echo "usage: BATCH_PRS='N N …' $0 [--repo owner/name]" >&2; exit 2 ;;
  esac
done

TOP=$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null) || {
  echo "::error::$0 must run from inside a chicago checkout"; exit 2; }
cd "$TOP"
if [ -z "$repo" ]; then  # the checkout's origin, never $GITHUB_REPOSITORY (T-1655/T-1656)
  repo=$(git remote get-url origin 2>/dev/null | sed -E 's#\.git$##; s#^(https?://([^@/]+@)?[^/]+/|ssh://([^@/]+@)?[^/]+/|[^/@]+@[^:/]+:)##')
fi
if ! [[ "$repo" =~ ^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$ ]]; then
  echo "::error::$0: cannot tell which repository to act on — pass --repo owner/name (got '$repo')"; exit 2
fi
REPO="$repo"
BASE="${BATCH_BASE:-dev}"
MIN="${BATCH_MIN:-2}"
DRY="${BATCH_DRY_RUN:-}"
OUT="${BATCH_OUT:-/tmp/batch-out.txt}"
MEMBERS=$(printf '%s' "${BATCH_PRS:-}" | tr ',' ' ' | tr -s ' ' '\n' | sed 's/^#//' | grep -E '^[0-9]+$' || true)
[ -n "$MEMBERS" ] || { echo "::error::BATCH_PRS names no pull request"; exit 2; }
DRIVERS="$(mktemp -d)"
STAMP=$(date -u +%Y%m%d-%H%M)
BRANCH="steward/batch-$STAMP"
: > "$OUT"
say() { printf '%s\n' "$*"; }

git config user.name  "polecat-steward"
git config user.email "steward@polecat.live"

# The same lists as pr-lap.sh, which explains each (T-0857, T-0937).
GENERATED='
chicago/4d/tickets/BOARD.md
chicago/4d/tickets/tickets.json
chicago/4d/tickets/QUEUE.md
chicago/4d/tools/dev-smoke-state.json
chicago/4d/renderers/web/js/changelog.js
site/4d/build.json
site/4d/tickets.json
site/4d/js/changelog.js
site/4d/walk/index.html
site/4d/walk/js/changelog.js
'
UNTRACKED_GENERATED='
chicago/4d/tickets/BOARD.md
chicago/4d/tickets/tickets.json
site/4d/tickets.json
'

# THE 1904 TABLES A TOOL LAYS FROM THE MODELS, which the research layer's manifest
# (rederive.mjs) does not list: each has a `--check` in check.sh saying the committed
# file is what the tool writes, so a conflict in one is cleared like a tool-owned
# file (either side) and the tool lays it again on the combined tree. Every house
# PR re-lays them, so nearly every pair of house PRs conflicts here (the dry run of
# tonight's six: doors_1904.json in five, back_yards/1904.json in one). They run in
# the order the #2399 batch ran them: doors, people, back yards, walk joins, numbers.
LAID_PATHS='^chicago/4d/data/(humans/doors_(1835|1904)\.json|back_yards/1904\.json|street_section/walk_joins_1904\.json|house_numbers/1904\.json)$'
LAID_TOOLS='tools/derive_doors_scene.py
tools/prairie_people.py
tools/lay_prairie_1904_back_yards.py
tools/lay_prairie_1904_walk_joins.py
tools/place_prairie_1904_house_numbers.py'

# --- merge drivers and the lock tool, from the BASE (as pr-lap.sh does) ----------
git fetch origin "$BASE" -q || { echo "::error::cannot fetch $BASE"; exit 1; }
for f in merge-queue.mjs merge-changelog.mjs merge-generated.mjs merge-smoke-state.mjs; do
  git show "origin/$BASE:chicago/4d/tools/$f" > "$DRIVERS/$f" 2>/dev/null || true
done
reg() { [ -s "$DRIVERS/$2" ] && git config "merge.$1.driver" "node $DRIVERS/$2 %O %A %B %P"; }
reg queue merge-queue.mjs; reg changelog merge-changelog.mjs
reg generated merge-generated.mjs; reg smokestate merge-smoke-state.mjs
git show "origin/$BASE:.gitattributes" | grep -E 'merge=(queue|changelog|generated|smokestate)' \
  > "$(git rev-parse --git-dir)/info/attributes"
LOCK_TOOL="$DRIVERS/lock/tools/ticket.mjs"
mkdir -p "$(dirname "$LOCK_TOOL")"
git show "origin/$BASE:chicago/4d/tools/ticket.mjs" > "$LOCK_TOOL" 2>/dev/null || : > "$LOCK_TOOL"
GITDIR=$(git rev-parse --absolute-git-dir)
lock()    { [ -n "$DRY" ] && return 0; GIT_DIR="$GITDIR" node "$LOCK_TOOL" lap "$1" --by "steward batch" >/tmp/batch-lock.log 2>&1; }
release() { [ -n "$DRY" ] && return 0; GIT_DIR="$GITDIR" node "$LOCK_TOOL" lap "$1" --release >/dev/null 2>&1 || true; }

LOCKED=""
fail() {  # nothing was pushed; give back every lock this run took
  say "BATCH FAILED: $*"
  for n in $LOCKED; do release "$n"; done
  printf 'failed=%s\n' "$*" >> "$OUT"
  exit 1
}

# --- one conflict pass, after a member's merge stopped ---------------------------
# Echoes nothing; returns 0 when every unmerged path is cleared, else 1 with
# $LEFT naming what was not.
LEFT=""
resolve_conflicts() {
  local U REAL REG DROP KEEP
  U=$(git diff --name-only --diff-filter=U)
  LEFT=
  [ -n "$U" ] || return 0
  DROP=$(comm -12 <(echo "$U" | sort -u) <(echo "$UNTRACKED_GENERATED" | sed '/^$/d' | sort -u))
  [ -n "$DROP" ] && git rm -q -f --ignore-unmatch $DROP >/dev/null 2>&1
  KEEP=$(comm -12 <(echo "$U" | sort -u) <(echo "$GENERATED" | sed '/^$/d' | sort -u) \
         | comm -23 - <(echo "$UNTRACKED_GENERATED" | sed '/^$/d' | sort -u))
  [ -n "$KEEP" ] && { git checkout --ours $KEEP >/dev/null 2>&1; git add $KEEP; }
  REAL=$(comm -23 <(echo "$U" | sort -u) <(echo "$GENERATED" | sed '/^$/d' | sort -u))
  if [ -n "$REAL" ] && [ -f chicago/4d/tools/merge_asset_registry.py ]; then
    REG=$(comm -12 <(echo "$REAL" | sort -u) <(python3 chicago/4d/tools/merge_asset_registry.py --list | sort -u))
    if [ -n "$REG" ] && python3 chicago/4d/tools/merge_asset_registry.py --resolve $REG >/tmp/batch-registry.log 2>&1; then
      say "    registries merged entry by entry: $(echo $REG)"
      git add $REG
      REAL=$(comm -23 <(echo "$REAL" | sort -u) <(echo "$REG" | sort -u))
    elif [ -n "$REG" ]; then
      sed 's/^/      /' /tmp/batch-registry.log | tail -4
    fi
  fi
  if [ -n "$REAL" ]; then
    local L
    L=$(echo "$REAL" | grep -E "$LAID_PATHS" || true)
    if [ -n "$L" ]; then
      say "    1904 tables a tool lays, taken either side and laid again below: $(echo $L)"
      git checkout --ours $L >/dev/null 2>&1; git add $L
      REAL=$(comm -23 <(echo "$REAL" | sort -u) <(echo "$L" | sort -u))
    fi
  fi
  if [ -n "$REAL" ] && [ -f chicago/4d/tools/rederive.mjs ]; then
    local D=""
    for p in $REAL; do
      node chicago/4d/tools/rederive.mjs --resolvable "$p" >/dev/null 2>&1 && D="$D $p"
    done
    if [ -n "$D" ]; then
      say "    derived files, taken either side and rebuilt below:$D"
      git checkout --ours $D >/dev/null 2>&1; git add $D
      REAL=$(comm -23 <(echo "$REAL" | sort -u) <(echo $D | tr ' ' '\n' | sort -u))
    fi
  fi
  if [ -n "$REAL" ]; then
    local A=""
    for p in $REAL; do
      python3 chicago/4d/tools/merge_additions.py --resolve "$p" 2>&1 | sed 's/^/    /'
      [ "${PIPESTATUS[0]}" -eq 0 ] || A="$A $p"
    done
    REAL=$(echo $A | tr ' ' '\n' | sed '/^$/d')
  fi
  LEFT="$REAL"
  [ -z "$REAL" ]
}

# Back to the last member's commit. `merge --abort` can refuse once a resolver has
# rewritten files (the dry run of 2026-11-28 left one merge half-done that way), and
# this is a scratch clone, so a hard reset to HEAD is the fallback, never a guess.
abort_merge() {
  git merge --abort >/dev/null 2>&1
  [ -z "$(git status --porcelain --untracked-files=no)" ] || git reset -q --hard HEAD
}

# --- build ------------------------------------------------------------------------
git checkout -q -B "$BRANCH" "origin/$BASE" || fail "cannot check out origin/$BASE"
DEV_SHA=$(git rev-parse HEAD)
say "batch $BRANCH on $BASE ${DEV_SHA:0:12}"
IN=""; DROPPED=""
for N in $MEMBERS; do
  BR=$(gh api "repos/$REPO/pulls/$N" --jq 'select(.state=="open" and .base.ref=="'"$BASE"'") | .head.ref' 2>/dev/null)
  if [ -z "$BR" ]; then say "#$N  not an open PR into $BASE — left out"; DROPPED="$DROPPED $N(not-open)"; continue; fi
  if ! lock "$N"; then
    say "#$N  its lap lock is held by a live run — left out: $(tail -2 /tmp/batch-lock.log | head -1)"
    DROPPED="$DROPPED $N(locked)"; continue
  fi
  LOCKED="$LOCKED $N"
  if ! git fetch -q origin "+refs/heads/$BR:refs/remotes/origin/$BR"; then
    say "#$N  cannot fetch $BR — left out"; release "$N"; LOCKED=$(echo $LOCKED | tr ' ' '\n' | grep -vx "$N" | tr '\n' ' ')
    DROPPED="$DROPPED $N(fetch)"; continue
  fi
  say "#$N  merging $BR ($(git rev-parse --short "origin/$BR"))"
  if git merge --no-ff --no-edit -m "Batch: merge #$N ($BR)" "origin/$BR" >/tmp/batch-merge.log 2>&1; then
    IN="$IN $N"; continue
  fi
  if [ -z "$(git diff --name-only --diff-filter=U)" ]; then
    say "    the merge failed with no conflict to resolve — left out:"; tail -3 /tmp/batch-merge.log | sed 's/^/      /'
    abort_merge
  elif resolve_conflicts && git -c core.editor=true commit -q --no-edit; then
    IN="$IN $N"; continue
  else
    say "    REAL CONFLICT with the batch so far — left out:"; echo "$LEFT" | sed 's/^/      /'
    abort_merge
  fi
  release "$N"; LOCKED=$(echo $LOCKED | tr ' ' '\n' | grep -vx "$N" | tr '\n' ' ')
  DROPPED="$DROPPED $N(conflict)"
done
IN=$(echo $IN); DROPPED=$(echo $DROPPED)
COUNT=$(echo "$IN" | wc -w)
printf 'members=%s\ndropped=%s\n' "$(echo $IN | tr ' ' ',')" "$(echo $DROPPED | tr ' ' ',')" >> "$OUT"
if [ "$COUNT" -lt "$MIN" ]; then
  say "only $COUNT member(s) merged (needs $MIN) — no batch"
  for n in $LOCKED; do release "$n"; done
  exit 3
fi

if [ "${BATCH_STOP:-}" = merged ]; then   # a test knob: the merges alone, nothing regenerated
  say "BATCH_STOP=merged — stopping after the merges ($COUNT in: $IN)"; exit 0
fi

# --- regenerate once, on the combined tree -----------------------------------------
say "regenerating on the $COUNT-member tree"
publish() {
  [ -f chicago/4d/tools/recover_glessner_v4.py ] && ( cd chicago/4d && python3 -c '
import sys; sys.path.insert(0, "tools")
import recover_glessner_v4 as r
print("\n".join(r.targets()))' 2>/dev/null ) | while IFS= read -r rel; do
    [ -n "$rel" ] && [ -e "chicago/4d/$rel" ] && git check-ignore -q "chicago/4d/$rel" && rm -f "chicago/4d/$rel"
  done
  ( cd chicago/4d && bash tools/publish.sh ) >>/tmp/batch-regen.log 2>&1
}
: > /tmp/batch-regen.log
step() { say "  $1"; shift; "$@" >>/tmp/batch-regen.log 2>&1 || { tail -12 /tmp/batch-regen.log | sed 's/^/    /'; fail "regeneration step failed: $*"; }; }
if [ -f chicago/4d/tools/resolve_id_collisions.mjs ]; then
  step "ticket ids" bash -c 'cd chicago/4d && node tools/resolve_id_collisions.mjs --base "origin/'"$BASE"'"'
fi
step "publish the mirror the rebuild reads" publish
step "re-stamp stale meshes (pure emitters, byte-identical)" bash -c 'cd chicago/4d && python3 tools/restamp_stale.py'
for t in $LAID_TOOLS; do
  [ -f "chicago/4d/$t" ] && step "lay again: $t" bash -c "cd chicago/4d && python3 $t"
done
step "rebuild the derived layer" bash -c 'cd chicago/4d && node tools/rederive.mjs --run'
step "the lap's regeneration tail" bash -c 'cd chicago/4d \
  && node tools/stamp-changelog.mjs \
  && bash tools/tickets.sh \
  && node tools/ticket.mjs reconcile --base "origin/'"$BASE"'" \
  && node tools/ticket.mjs prune \
  && node tools/ticket.mjs board \
  && node tools/rederive.mjs --tail tools/compile_scene.py \
  && ./tools/publish.sh'
step "nothing left stale" bash -c 'cd chicago/4d && python3 tools/restamp_stale.py --list'
git add -A
git commit -q -m "Batch: re-derive the shared files on the $COUNT-member tree

Members, merged one after another above: $(for n in $IN; do printf '#%s ' "$n"; done)
The files a tool owns were taken from either side and rewritten from source;
meshes whose input hash moved on the combined tree were re-emitted with their
pure emitter (byte-identical); the derived layer was re-run." 2>/dev/null \
  || say "  (the regeneration moved nothing)"

if [ -n "$DRY" ]; then
  say "DRY RUN — built $BRANCH with $COUNT member(s); nothing pushed"
  printf 'branch=%s\n' "$BRANCH" >> "$OUT"
  exit 0
fi

# --- push and open ----------------------------------------------------------------
git push -q origin "HEAD:refs/heads/$BRANCH" || fail "push of $BRANCH refused"
LIST=$(for n in $IN; do printf -- '- #%s\n' "$n"; done)
TITLE="Batch: $COUNT loop PRs on one gate ($(for n in $IN; do printf '#%s ' "$n"; done | sed 's/ $//'))"
BODY=$(cat <<EOF
<!-- batch-members: $(echo $IN | tr ' ' ',') -->
The steward janitor merged these open pull requests into one branch off \`$BASE\` (${DEV_SHA:0:12}) so they land on one gate:

$LIST

Derived files were taken from either side and regenerated once on the combined tree; meshes whose input hash moved were re-stamped with their pure emitter (byte-identical); the derived layer was re-run (\`.github/steward/pr-batch.sh\`).${DROPPED:+

Left out, and still open for their own lap: $DROPPED}

The janitor merges this with a **merge commit** (never a squash) once \`gate\` is green, so GitHub marks every member merged, and then restarts the chicago lane. Close it to give the members back; their lap locks age out within 3 h.
EOF
)
PR=$(jq -n --arg t "$TITLE" --arg h "$BRANCH" --arg b "$BASE" --arg body "$BODY" \
       '{title:$t, head:$h, base:$b, body:$body, draft:false}' \
     | gh api -X POST "repos/$REPO/pulls" --input - --jq '.number' 2>/tmp/batch-pr.err)
if [ -z "$PR" ]; then
  git push -q origin --delete "$BRANCH" 2>/dev/null
  fail "opening the PR failed: $(tail -1 /tmp/batch-pr.err | cut -c1-160)"
fi
printf 'pr=%s\nbranch=%s\n' "$PR" "$BRANCH" >> "$OUT"
say "opened #$PR ($BRANCH) with $COUNT member(s)${DROPPED:+; left out: $DROPPED}"
