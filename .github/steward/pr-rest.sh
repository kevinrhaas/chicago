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
# EVERY VERB EXCEPT `meter` TAKES `--repo owner/name`, and defaults it to the
# ORIGIN REMOTE OF THE CHECKOUT THIS SCRIPT LIVES IN. See T-1655 below.
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

# WHICH REPOSITORY (T-1655, measured 2026-09-27 by the run that hit it — T-1652,
# chicago#104). This script read its repository out of the AMBIENT ENVIRONMENT,
# and the environment belongs to whoever started the process, not to the checkout
# the script is in. A steward improve run executes inside a **polecat-platform**
# Actions job and clones this repo into the workspace, so the ambient repo name is
# `kevinrhaas/polecat-platform` for every call made from `chicago-repo/` — while
# `.github/steward/improve.md` tells a run to use *"that repo's own
# pr-rest.sh resume <N>"* for a chicago PR. Both instructions were followed and
# they cannot both be obeyed:
#
#   create  FAILED LOUDLY — 422, `base` and `head` invalid, because `dev` and
#           `steward/t1652-bake-only-list` are not branches of polecat-platform.
#           Its recovery notice printed a `polecat-platform/compare/…` URL, the tell.
#   resume  SUCCEEDED SILENTLY AGAINST A STRANGER — it commented the handoff reason
#           on, and applied `resume` to, polecat-platform#104, an unrelated PR
#           ("fix: mobile drawer has no way to close except tapping the backdrop").
#           A number collision across two repos is not rare: both had a #104 open
#           that same day. Undone by hand afterwards.
#
# The silent case is the whole ticket, and labelling a stranger's PR is the one
# thing T-1577 exists to stop happening without the owner knowing why. So:
#
#   1. `--repo owner/name` NAMES it, and wins.
#   2. Otherwise it is the origin remote of THE CHECKOUT THIS FILE IS IN — resolved
#      from ${BASH_SOURCE[0]}, not from $PWD, because a run drives this script by
#      absolute path from wherever it happens to be standing.
#   3. Otherwise it REFUSES, in one line, naming `--repo`. It never falls back to
#      the environment. The platform's own gh-rest.sh takes the repo as its first
#      argument and is why that one cannot make this mistake.
#
# …and naming a repository is not the same as being in the right one, so every verb
# that WRITES first asks whether its target is there: `create` that the head branch
# exists, `comment`/`merge`/`resume` that the pull request does. One GET, and it is
# the difference between a 404 and a comment on a stranger.
repo=""

# The pre-verb position (`pr-rest.sh --repo o/n list`). Each verb's own option loop
# accepts `--repo` too, so a free-form `--why`/`--body`/`--title` value can never be
# mistaken for it — the reason this is not one global strip over all of "$@".
while [ $# -gt 0 ]; do
  case "$1" in
    --repo)   repo=${2:-}; shift 2 ;;
    --repo=*) repo=${1#--repo=}; shift ;;
    *) break ;;
  esac
done
[ $# -ge 1 ] || { echo "usage: $0 [--repo owner/name] create|list|view|comment|merge|resume|meter ..." >&2; exit 2; }
cmd=$1; shift

# …and immediately after the verb, so `--repo o/n resume N` and `resume --repo o/n N`
# read the same. The verbs that take a PR number take it POSITIONALLY, so without
# this the option would be read as the number.
while [ $# -gt 0 ]; do
  case "$1" in
    --repo)   repo=${2:-}; shift 2 ;;
    --repo=*) repo=${1#--repo=}; shift ;;
    *) break ;;
  esac
done

checkout_repo() { # the origin remote of the checkout THIS FILE is in, as owner/name
  local root url
  root=$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null) || return 1
  url=$(git -C "$root" remote get-url origin 2>/dev/null) || return 1
  url=${url%.git}
  # https://host/owner/name · https://user@host/owner/name · git@host:owner/name · ssh://host/owner/name
  url=$(printf '%s' "$url" | sed -E 's#^(https?://([^@/]+@)?[^/]+/|ssh://([^@/]+@)?[^/]+/|[^/@]+@[^:/]+:)##')
  printf '%s\n' "$url"
}

require_repo() {
  if [ -z "$repo" ]; then repo=$(checkout_repo) || repo=""; fi
  if ! [[ "$repo" =~ ^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$ ]]; then
    echo "$0 $cmd: cannot tell which repository to act on — pass --repo owner/name; the default is this checkout's origin remote and NEVER \$GITHUB_REPOSITORY (T-1655), and it resolved to '${repo}'" >&2
    exit 2
  fi
}

require_head() { # head — create acts on a branch, so the branch has to be there
  gh api "repos/${repo}/branches/$1" --jq .name >/dev/null 2>&1 && return 0
  echo "$0 create: ${repo} has no branch '$1' — refusing to open a pull request in a repository this branch is not in; name the right one with --repo owner/name (T-1655)" >&2
  return 1
}

require_pr() { # N — the three writing verbs act on a pull request, so refuse a stranger
  local got
  got=$(gh api "repos/${repo}/pulls/$1" --jq '.number' 2>/dev/null) || got=""
  [ "$got" = "$1" ] && return 0
  echo "$0 $cmd: ${repo} has no pull request #$1 — refusing to write to a repository this PR is not in; name the right one with --repo owner/name (T-1655)" >&2
  return 1
}


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
        --repo) repo=$2; shift 2 ;;
        --repo=*) repo=${1#--repo=}; shift ;;
        *) echo "$0 create: unknown argument $1" >&2; exit 2 ;;
      esac
    done
    [ -n "$title$base$head" ] || { echo "$0 create: --title --base --head are required" >&2; exit 2; }
    require_repo
    # THE ONE GET THAT TELLS A WRONG REPOSITORY FROM A WRONG ARGUMENT (T-1655). Without
    # it the 422 below says only "head invalid", which reads as a bad branch name and
    # sent the run that hit it looking at its own branch rather than at the repository.
    # Loud, and exit 1: create must never lose finished work silently, and a compare URL
    # into a repository the branch is not in is not a recovery.
    require_head "$head" || { echo "::error::$0 create: refused — see above (rate: $(meter_line))" >&2; exit 1; }
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
    require_repo
    expr='.[] | .number'
    [ $# -eq 0 ] || { expr=$1; shift; }
    gh api --paginate "repos/${repo}/pulls?per_page=100" --jq "$expr"
    ;;

  view)
    require_repo
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
        --repo) repo=$2; shift 2 ;;
        --repo=*) repo=${1#--repo=}; shift ;;
        *) echo "$0 comment: unknown argument $1" >&2; exit 2 ;;
      esac
    done
    [ -n "$body" ] || { echo "$0 comment: --body is required" >&2; exit 2; }
    require_repo
    require_pr "$n" || exit 2
    printf '%s' "$body" | gh api -X POST "repos/${repo}/issues/${n}/comments" --input - >/dev/null
    ;;

  merge)
    n=${1:?PR number}; shift
    method=squash
    while [ $# -gt 0 ]; do
      case "$1" in
        --method) method=$2; shift 2 ;;
        --repo) repo=$2; shift 2 ;;
        --repo=*) repo=${1#--repo=}; shift ;;
        *) echo "$0 merge: unknown argument $1" >&2; exit 2 ;;
      esac
    done
    require_repo
    require_pr "$n" || exit 2
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
        --repo) repo=$2; shift 2 ;;
        --repo=*) repo=${1#--repo=}; shift ;;
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
    # AND THE TARGET IS THERE, BEFORE ANYTHING IS WRITTEN (T-1655). This verb's
    # writes all land on an ISSUE number, and every repository has one of those —
    # which is why the wrong-repository handoff succeeded instead of 404ing. Asking
    # for the PULL REQUEST is the question that distinguishes them, and it is asked
    # before the label vocabulary, so a refusal leaves the stranger untouched.
    require_repo
    require_pr "$n" || exit 2
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
    echo "usage: $0 [--repo owner/name] create|list|view|comment|merge|resume|meter ..." >&2
    exit 2
    ;;
esac
