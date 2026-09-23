#!/usr/bin/env bash
# pr-rest.sh — T-0234: every pull-request operation through the REST bucket.
#
#   pr-rest.sh create --title T --base B --head H --body P   # stdout: PR number (empty if refused-but-recoverable)
#   pr-rest.sh list  [--jq EXPR]                             # default '.[] | .number'
#   pr-rest.sh view N [--jq EXPR]                            # default '.mergeable_state'
#   pr-rest.sh comment N --body P
#   pr-rest.sh merge N [--method squash|merge|rebase]
#   pr-rest.sh meter                                         # both buckets, one line
#
# WHY, measured 2026-08-27 (steward run 1140): GitHub meters GraphQL and REST as
# TWO SEPARATE hourly buckets, and the fleet emptied one while the other sat
# untouched — graphql remaining 0 of 5000, core remaining 4969 of 5000. A slice
# that had finished, gated and pushed its work lost its PR when `gh pr create`
# drew on the empty bucket. `gh pr create/list/view/merge/comment`, and
# `gh issue`/`gh search`, speak GraphQL; the same operations below speak REST,
# which the steward workload barely touches. This script is the REST half, kept
# beside the workflows so the next call is one line away.
#
# THE ONE NAMED EXCEPTION — arming auto-merge (`gh pr merge --auto`) has NO REST
# equivalent: enablePullRequestAutoMerge is GraphQL-only. Its cost, stated: one
# mutation (plus gh's repo query) per PR armed — a few points against the 5,000
# an hour that this rule leaves nearly full. It is allowed exactly once, in
# chicago-4d-bake.yml, and tools/check_gh_rest.mjs refuses any other GraphQL draw
# re-entering the steward surfaces.
#
# FAILURE SHAPE: create NEVER loses finished work. A refusal (permissions,
# policy) exits 0 with an empty stdout and a ::notice:: carrying the manual
# compare URL — the branch is PUSHED, the work is recoverable, and the summary
# says so. A transport failure exits 1 after printing the same recovery line to
# stderr, because "pushed, gated, no PR" must never be silent.
set -euo pipefail

[ $# -ge 1 ] || { echo "usage: $0 create|list|view|comment|merge|meter ..." >&2; exit 2; }
cmd=$1; shift

repo="${GITHUB_REPOSITORY:?GITHUB_REPOSITORY is not set}"

meter_line() {
  gh api rate_limit --jq '"graphql \(.resources.graphql.remaining)/\(.resources.graphql.limit) core \(.resources.core.remaining)/\(.resources.core.limit)"' 2>/dev/null || echo "meter unread"
}

compare_url() { # base head
  echo "https://github.com/${repo}/compare/$1...$2?expand=1"
}

case "$cmd" in
  create)
    title= base= head= body=
    while [ $# -gt 0 ]; do
      case "$1" in
        --title) title=$2; shift 2 ;;
        --base)  base=$2;  shift 2 ;;
        --head)  head=$2;  shift 2 ;;
        --body)  body=$2;  shift 2 ;;
        *) echo "$0 create: unknown argument $1" >&2; exit 2 ;;
      esac
    done
    [ -n "$title$base$head" ] || { echo "$0 create: --title --base --head are required" >&2; exit 2; }
    out="$(gh api -X POST "repos/${repo}/pulls" \
             -f title="$title" -f base="$base" -f head="$head" -f body="$body" \
             --jq .number 2>&1)" || {
      if printf '%s\n' "$out" | grep -Eiq "not permitted|resource not accessible|creation is disabled"; then
        # Permission/policy refusal: recoverable, and the recovery is named.
        echo "::warning::PR creation refused: $(printf '%s\n' "$out" | head -1)" >&2
        echo "::notice::the branch is PUSHED — open the PR by hand: $(compare_url "$base" "$head") (rate: $(meter_line))" >&2
        exit 0
      fi
      echo "::error::PR creation failed: $out" >&2
      echo "::notice::recoverable — the branch is pushed; open the PR by hand: $(compare_url "$base" "$head") (rate: $(meter_line))" >&2
      exit 1
    }
    printf '%s\n' "$out"
    ;;

  list)
    expr='.[] | .number'
    [ $# -eq 0 ] || { expr=$1; shift; }
    gh api --paginate "repos/${repo}/pulls?per_page=100" --jq "$expr"
    ;;

  view)
    n=${1:?PR number}; shift
    expr='.mergeable_state'
    [ $# -eq 0 ] || { expr=$1; shift; }
    gh api "repos/${repo}/pulls/${n}" --jq "$expr"
    ;;

  comment)
    n=${1:?PR number}; shift
    body=
    while [ $# -gt 0 ]; do
      case "$1" in
        --body) body=$2; shift 2 ;;
        *) echo "$0 comment: unknown argument $1" >&2; exit 2 ;;
      esac
    done
    [ -n "$body" ] || { echo "$0 comment: --body is required" >&2; exit 2; }
    printf '%s' "$body" | gh api -X POST "repos/${repo}/issues/${n}/comments" --input - >/dev/null
    ;;

  merge)
    n=${1:?PR number}; shift
    method=squash
    while [ $# -gt 0 ]; do
      case "$1" in
        --method) method=$2; shift 2 ;;
        *) echo "$0 merge: unknown argument $1" >&2; exit 2 ;;
      esac
    done
    gh api -X PUT "repos/${repo}/pulls/${n}/merge" -f merge_method="$method" >/dev/null
    ;;

  meter)
    meter_line
    ;;

  *)
    echo "$0: unknown command $cmd" >&2
    exit 2
    ;;
esac
