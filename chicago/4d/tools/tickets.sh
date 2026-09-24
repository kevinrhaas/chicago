#!/usr/bin/env bash
# tickets.sh — the tickets live in their own repository, kevinrhaas/chicago-tickets.
#
#   bash tools/tickets.sh          clone it into tickets/, or pull it if it is there
#   bash tools/tickets.sh --push   push commits the clone is holding (a push that
#                                  failed inside ticket.mjs, say)
#
# WHY A SEPARATE REPOSITORY (2026-09-23). Every ticket or queue edit used to ride the
# code PR it belonged to, so every PR carried QUEUE.md and ticket files, and every one
# of them conflicted whenever `dev` moved — GitHub's server-side merge runs none of
# this repo's merge drivers (T-0857, and .gitattributes has the measurements). Out of
# the code repo those files are not on the PR surface at all: `ticket.mjs` commits and
# pushes them straight to the tickets repo's `main`, one small commit per change, and
# retries on a moved main instead of merging. See the tickets repo's README.md.
#
# tickets/ is .gitignored here. The clone is read-only-safe without credentials (the
# repo is public); pushing needs the same git credentials as any other push.
set -euo pipefail
cd "$(dirname "$0")/.."
REMOTE="${CHICAGO_TICKETS_REMOTE:-https://github.com/kevinrhaas/chicago-tickets.git}"
DIR=tickets

if [ -d "$DIR/.git" ]; then
  if [ "${1:-}" = "--push" ]; then
    git -C "$DIR" pull --rebase --quiet origin main
    git -C "$DIR" push --quiet origin HEAD:main
    echo "tickets: pushed $(git -C "$DIR" rev-parse --short HEAD) to $REMOTE"
    exit 0
  fi
  # Never throw away local work: a clone holding unpushed commits is rebased, not reset.
  if git -C "$DIR" pull --rebase --quiet origin main 2>/dev/null; then
    echo "tickets: up to date at $(git -C "$DIR" rev-parse --short HEAD) ($(find "$DIR" -name 'T-[0-9]*.md' | wc -l | tr -d ' ') tickets)"
  else
    echo "tickets: could not pull $REMOTE — using the local clone at $(git -C "$DIR" rev-parse --short HEAD)" >&2
  fi
  exit 0
fi

if [ -e "$DIR" ] && [ -n "$(ls -A "$DIR" 2>/dev/null)" ]; then
  # A tickets/ folder that is not a clone: the layout from before the move (a checkout
  # of an old branch), or files dropped here by hand. Leave it alone and say so.
  echo "tickets: $DIR/ exists and is not a clone of $REMOTE — leaving it as it is" >&2
  exit 0
fi

rm -rf "$DIR"
for attempt in 1 2 3 4; do
  if git clone --quiet "$REMOTE" "$DIR"; then
    echo "tickets: cloned $REMOTE → $DIR/ ($(find "$DIR" -name 'T-[0-9]*.md' | wc -l | tr -d ' ') tickets)"
    exit 0
  fi
  sleep $((2 ** attempt))
done
echo "tickets: could not clone $REMOTE" >&2
exit 1
