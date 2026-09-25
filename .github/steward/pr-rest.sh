#!/usr/bin/env bash
# pr-rest.sh — T-0234: every pull-request operation through the REST bucket.
#
#   pr-rest.sh create --title T --base B --head H --body P   # stdout: PR number (empty if refused-but-recoverable)
#   pr-rest.sh list  [--jq EXPR]                             # default '.[] | .number'
#   pr-rest.sh view N [--jq EXPR]                            # default '.mergeable_state'
#   pr-rest.sh comment N --body P
#   pr-rest.sh merge N [--method squash|merge|rebase]
#   pr-rest.sh resume N --why R [--waits-on T-NNNN|nothing]  # hand an unfinished PR to the next run
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

[ $# -ge 1 ] || { echo "usage: $0 create|list|view|comment|merge|resume|meter ..." >&2; exit 2; }
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

  # THE HANDOFF, AND WHY IT IS NOT `hold` (T-1573; owner, 2026-09-25, on finding
  # three PRs parked on `hold` whose reasons he had not seen: *"that seems like a
  # bad move because i am not aware of why they are held"*).
  #
  # `hold` is THE OWNER'S PARK SWITCH. Every automated pass in this repository
  # skips it on purpose — the lap, merge-ready, the stuck reporter — because a park
  # a robot can overrule is not a park. But the steward prompt told a run to apply
  # that same label whenever it merely COULD NOT FINISH: verification unrun, the
  # turn budget low, `dev` moving faster than it could rebase, or `dev`'s own gate
  # red. So a label meaning "a person is deciding" was mostly worn by work needing
  # no decision at all, only a later run — and because every pass skipped it,
  # nothing ever came. Measured on the three PRs open at 17:35Z on 2026-09-25:
  #
  #   #39 (T-1563)  "this run's clock ran out" — CI then passed all 620 steps, so
  #                 the stated reason was already stale, and it drifted into
  #                 conflict with `dev` while held.
  #   #41 (T-1521)  complete; held only because `dev`'s gate was red (T-1567).
  #   #42 (T-1565)  the same.
  #
  # Not one needed a ruling. Each needed a machine to lap it, re-gate it and merge
  # it, and each got a person instead.
  #
  # So an unfinished run says `resume` and says WHY, in a line a machine can read:
  #
  #   resume: <reason> · waits on: <T-NNNN | nothing>
  #
  # `waits on` is the difference between "come back to this" and "come back to this
  # AFTER that lands", and it is a ticket id or the word `nothing` — never prose,
  # because the reader is a script.
  resume)
    n=${1:?PR number}; shift
    why= waits=nothing
    while [ $# -gt 0 ]; do
      case "$1" in
        --why)      why=$2; shift 2 ;;
        --waits-on) waits=${2:-nothing}; shift 2 ;;
        *) echo "$0 resume: unknown argument $1" >&2; exit 2 ;;
      esac
    done
    # A HANDOFF WITH NO REASON IS THE FAULT THIS VERB EXISTS TO END, so it is a
    # usage error and not a default. The three PRs above each had a reason; it was
    # in the PR body, which is the one place nobody reads.
    [ -n "$why" ] || { echo "$0 resume: --why is required — a handoff whose reason is not written down is the fault this verb exists to end" >&2; exit 2; }
    # ONE LINE, ALWAYS. A newline in the reason would push the machine-readable
    # part off the first line and every reader below would see a handoff with no
    # reason — the same silence, wearing a new label.
    why=$(printf '%s' "$why" | tr '\n\r\t' '   ')
    [ -n "$waits" ] || waits=nothing
    case "$waits" in
      nothing|T-[0-9][0-9][0-9][0-9]) ;;
      *) echo "$0 resume: --waits-on takes a ticket id like T-1567, or the word 'nothing' — got '$waits'" >&2; exit 2 ;;
    esac
    # The label vocabulary, created once and idempotently. Adding a label that does
    # not exist is a 422 on the issues endpoint, so the first handoff in a fresh
    # clone would otherwise leave the comment and no label — visible to a person
    # and invisible to every script.
    gh api -X POST "repos/${repo}/labels" \
      -f name=resume -f color=0E8A16 \
      -f description="A run could not finish this; the next one picks it up — reason in the resume: comment" \
      >/dev/null 2>&1 || true
    # THE REASON GOES ON BEFORE THE LABEL, and the order is the point: a labelled
    # PR must never exist without its reason beside it. If the comment fails, the
    # label is never applied and the run is told — better an unlabelled PR with a
    # loud failure than a labelled one nobody can interpret.
    {
      printf 'resume: %s · waits on: %s\n\n' "$why" "$waits"
      printf 'This pull request is the loop'"'"'s own unfinished work, and it is NOT parked.\n'
      printf 'The run that opened it could not finish inside its own budget; the branch\n'
      printf 'carries the work. A later run picks it up before it takes new queue work:\n'
      printf 'merge `%s` in, re-derive, fix what is red, gate, merge.\n\n' "${PR_BASE:-dev}"
      if [ "$waits" != "nothing" ]; then
        printf 'It waits on **%s**. Until that ticket closes this PR cannot go green, so a\n' "$waits"
        printf 'run that finds it says so and takes the next row rather than re-gating it.\n\n'
      fi
      printf '`hold` is the owner'"'"'s park switch and no run applies it — see\n'
      printf '`chicago/4d/AGENTS.md` § the two labels.\n\n'
      printf -- '---\n_Generated by [Claude Code](https://claude.ai/code)_\n'
    } | jq -Rs '{body: .}' \
      | gh api -X POST "repos/${repo}/issues/${n}/comments" --input - >/dev/null
    gh api -X POST "repos/${repo}/issues/${n}/labels" -f 'labels[]=resume' >/dev/null
    # AND `hold` COMES OFF. A run that reaches for this verb is declaring the work
    # unfinished, not parked; leaving both on would leave every pass skipping it,
    # which is exactly the state being fixed. A PR that never had `hold` answers
    # 404 here and that is not a failure.
    if gh api -X DELETE "repos/${repo}/issues/${n}/labels/hold" >/dev/null 2>&1; then
      echo "  hold removed — hold is the owner's switch and no run applies it"
    fi
    echo "resume: #${n} handed off · waits on: ${waits}"
    ;;

  *)
    echo "$0: unknown command $cmd" >&2
    echo "usage: $0 create|list|view|comment|merge|resume|meter ..." >&2
    exit 2
    ;;
esac
