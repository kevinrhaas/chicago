#!/usr/bin/env bash
#
# MERGE-READY. Merge every open PR into `dev` that GitHub itself calls `clean`.
#
# WHY THIS EXISTS. Nothing merged a finished pull request in this repository, and
# three separate pieces each assumed one of the others did.
#
#   .github/steward/pr-lap.sh header  "It does NOT merge the PR; auto-merge does
#                                      that once `gate` goes green on the new head."
#   polecat-platform steward-janitor  "`custom` merges through the lap plus GitHub
#                                      auto-merge" — and `custom` is deliberately
#                                      NOT in the janitor's roster, because its
#                                      gate could not fit in a 55-minute job
#                                      (run 1047: 53m37s inside one gate).
#   chicago-4d-bake.yml:580           `gh pr merge --auto` — the ONLY thing in the
#                                      repo that arms auto-merge, and only on bakes.
#
# So auto-merge was armed by hand, PR by PR, or not at all. Checked on 2026-09-14
# against every PR that had landed that day: #1327 and #1312 merged with
# `auto_merge: off`, and the ones that carried it had been armed by a session. A
# pull request that the lap made clean and CI made green simply sat there, which
# is what the pile looks like from outside — every PR mergeable, every PR green,
# nothing moving.
#
# THE CONDITION IS GITHUB'S OWN, NOT ONE COMPUTED HERE. `mergeable_state` is
# `clean` only when the branch merges AND every required check has passed AND no
# review blocks it; `blocked` is what a PR reads while its gate runs. Verified on
# this repo the same day: #1329 sat `blocked` through its gate and turned `clean`
# the moment that gate went green, and #1315/#1316/#1319 read `blocked` while
# their re-gates ran after a lap. Nothing here re-derives that judgement — it
# asks, and merges only on `clean`.
#
# REST ONLY, and that is not a style choice. Enabling auto-merge is a GraphQL
# mutation with no REST equivalent, and the steward PAT's GraphQL budget is
# exactly what ran out twice on 2026-09-14 — blinding the lap into reporting
# `pushed=0 ... red=0` while it swept nothing (see pr-lap.sh, and that repo's
# test_pr_lap_list.mjs). The merge itself is a plain REST PUT. Putting the merge
# on the budget that fails would rebuild the fault this repo just spent a day
# removing.
#
# WHAT IT WILL NOT TOUCH. Drafts, and anything labelled `hold` — `hold` is the
# owner's park mechanism and a park that a robot can overrule is not a park.
set -uo pipefail

REPO="${GITHUB_REPOSITORY:-kevinrhaas/custom}"
BASE="${MERGE_BASE:-dev}"
ONLY="${MERGE_ONLY:-}"
DRY="${MERGE_DRY_RUN:-}"

say() { printf '%s\n' "$*"; }

# THE LIST, AND ITS EXIT STATUS. `PRS=$(gh api …)` carries gh's status and this
# script runs without `-e`, so a failed call leaves PRS empty, the loop runs zero
# times, and the summary is character for character what a healthy empty queue
# prints. That is the exact shape that made the blind lap look green while it
# swept nothing, and it is checked here rather than re-learned.
PRS=$(gh api --paginate \
        "repos/$REPO/pulls?state=open&base=$BASE&per_page=100" \
        --jq '.[] | select(.draft==false)
                  | select([.labels[].name] | index("hold") | not)
                  | "\(.number)"')
LIST_RC=$?
if [ "$LIST_RC" -ne 0 ]; then
  echo "::error::cannot see the pull requests into $BASE — the list call failed (exit $LIST_RC)."
  echo "::error::Refusing to report an empty queue, which is what a blind run looks like."
  exit 1
fi

if [ -n "$ONLY" ]; then
  MATCHED=$(printf '%s\n' "$PRS" | awk -v n="$ONLY" '$1==n')
  if [ -z "$MATCHED" ]; then
    echo "::error::MERGE_ONLY=$ONLY matched no mergeable-candidate pull request into $BASE."
    echo "::error::Drafts and \`hold\` are filtered out before this point — check both."
    exit 1
  fi
  PRS="$MATCHED"
fi

MERGED=0; WAITING=0; CONFLICTED=0; REFUSED=0

for N in $PRS; do
  [ -n "$N" ] || continue

  # `mergeable_state` is computed LAZILY. Straight after a push — which is
  # precisely when this workflow runs — GitHub answers `unknown` and starts the
  # computation as a side effect of being asked. Asking once and believing the
  # first answer would skip every PR the lap had just touched, i.e. all of them.
  STATE=unknown
  for _ in 1 2 3 4 5; do
    STATE=$(gh api "repos/$REPO/pulls/$N" --jq '.mergeable_state' 2>/dev/null || echo error)
    [ "$STATE" = "unknown" ] || break
    sleep 3
  done

  TITLE=$(gh api "repos/$REPO/pulls/$N" --jq '.title' 2>/dev/null | cut -c1-72)
  case "$STATE" in
    clean)
      if [ -n "$DRY" ]; then
        say "#$N  WOULD MERGE — $TITLE"; MERGED=$((MERGED+1)); continue
      fi
      # The head sha is pinned so a push landing between the read and the merge
      # loses the race instead of being merged unseen. GitHub answers 409 and the
      # next run picks it up with a fresh gate.
      SHA=$(gh api "repos/$REPO/pulls/$N" --jq '.head.sha' 2>/dev/null)
      if gh api -X PUT "repos/$REPO/pulls/$N/merge" \
           -f merge_method=squash -f sha="$SHA" >/tmp/mr.json 2>/tmp/mr.err; then
        say "#$N  MERGED — $TITLE"
        MERGED=$((MERGED+1))
      else
        say "#$N  merge REFUSED by GitHub after reading \`clean\` — $(tail -1 /tmp/mr.err | cut -c1-120)"
        say "     the head moved under the read, or a rule this cannot see; next run re-reads it"
        REFUSED=$((REFUSED+1))
      fi
      ;;
    blocked|unstable|has_hooks)
      say "#$N  $STATE — its checks are not green yet, leaving it"; WAITING=$((WAITING+1)) ;;
    dirty|behind)
      say "#$N  $STATE — the PR lap's job, not this one"; CONFLICTED=$((CONFLICTED+1)) ;;
    *)
      say "#$N  $STATE — not a state this merges on"; REFUSED=$((REFUSED+1)) ;;
  esac
done

say ""
say "merge-ready: merged=$MERGED waiting-on-checks=$WAITING needs-a-lap=$CONFLICTED refused=$REFUSED"
say "  (\`clean\` is GitHub's own verdict: the branch merges AND every required check passed.)"
