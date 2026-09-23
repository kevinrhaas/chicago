#!/usr/bin/env bash
# Register this repo's custom git merge drivers in the LOCAL clone.
#
# `.gitattributes` can say `merge=queue`, but it cannot say what `queue` runs —
# git deliberately keeps the command out of tracked content, because a merge
# driver is an executable a repository would otherwise be able to hand you. So
# every clone registers it once, and this is that step.
#
# Safe either way: with the driver unregistered git falls back to the ordinary
# text merge, which is the behaviour this repo had before the driver existed.
# `tools/check.sh` notices and advises; it does not fail, because a fresh clone
# that has not run this is not broken.
#
# Idempotent. Run it as often as you like.
set -euo pipefail
cd "$(dirname "$0")/../../.."          # repo root

git config merge.queue.name \
  'tickets/QUEUE.md — keep our order, take their closes and their new tickets'
git config merge.queue.driver \
  'node chicago/4d/tools/merge-queue.mjs %O %A %B %P'

git config merge.changelog.name \
  'changelog.js — our new entries, unstamped, on top of theirs'
git config merge.changelog.driver \
  'node chicago/4d/tools/merge-changelog.mjs %O %A %B %P'

# T-0831. The five BUILD PRODUCTS: keep ours, print how to rebuild, never conflict.
# They collided on all five merges of PR #906 in seventy minutes and on every lap
# #894 and #850 recorded, and they resolve the same way every time — by being
# regenerated. Safe because the gate already refuses each of them stale
# (ticket.mjs check, test_ticket_mirror.mjs, check_published.mjs), so the conflict
# was never the thing protecting them.
git config merge.generated.name \
  'build products — keep ours; regenerate before committing'
git config merge.generated.driver \
  'node chicago/4d/tools/merge-generated.mjs %O %A %B %P'

# …and the one file in that conflict set that is NOT a build product. The smoke
# ledger is append-only, its rows carry no id, and no step of check.sh reads it —
# so "keep ours" would silently drop the other side's readings with nothing to
# notice. It gets a union of whole readings instead, never of lines.
git config merge.smokestate.name \
  'dev-smoke-state.json — every reading from both sides, none dropped'
git config merge.smokestate.driver \
  'node chicago/4d/tools/merge-smoke-state.mjs %O %A %B %P'

echo "registered: merge.queue.driver      -> $(git config merge.queue.driver)"
echo "registered: merge.changelog.driver  -> $(git config merge.changelog.driver)"
echo "registered: merge.generated.driver  -> $(git config merge.generated.driver)"
echo "registered: merge.smokestate.driver -> $(git config merge.smokestate.driver)"
echo "  QUEUE.md:       $(git check-attr merge -- chicago/4d/tickets/QUEUE.md)"
echo "  changelog.js:   $(git check-attr merge -- chicago/4d/renderers/web/js/changelog.js)"
echo "  BOARD.md:       $(git check-attr merge -- chicago/4d/tickets/BOARD.md)"
echo "  smoke ledger:   $(git check-attr merge -- chicago/4d/tools/dev-smoke-state.json)"
echo
echo "NOTE: a changelog merge leaves our entries UNSTAMPED on purpose. After one, run:"
echo "  node chicago/4d/tools/stamp-changelog.mjs && node chicago/4d/tools/check-changelog.mjs"
echo "NOTE: a build-product merge keeps OURS and does not rebuild it. After one, run:"
echo "  node chicago/4d/tools/ticket.mjs board   &&   bash chicago/4d/tools/publish.sh"
