#!/usr/bin/env bash
#
# THE STUCK-PR REPORTER (T-1368). It merges nothing, pushes nothing and resolves
# nothing. Its whole job is that a pull request no automation in this repository
# can move is never SILENT about it.
#
# IT REPORTS TWO SHAPES. The first is the deadlock below. The second (T-1510) is a
# PR whose `gate` has COMPLETED with a failing conclusion while the steward run that
# owns the branch has finished — the one state with no owner at all in this repo, as
# the lap does not gate, `merge-ready` merges only `clean`, and the run is over.
# Measured 2026-09-21 on #1616 and #1618: both runs completed SUCCESS around the
# minute their own gate went red, and both PRs sat until a person read the logs. It
# names the failing steps, because having to open the logs is most of the cost.
#
# THE DEADLOCK IT REPORTS, stated as the cycle it is:
#
#   1. The PR is `dirty`, so GitHub cannot compute a merge ref for it.
#   2. chicago-4d-check.yml gates on `pull_request`, and a `pull_request` run needs
#      that merge ref — so the gate never starts and the PR carries ZERO check runs.
#   3. `gate` is a REQUIRED check on `dev`, so GitHub never calls the PR `clean`.
#   4. .github/steward/merge-ready.sh merges only on `clean`, deliberately, so it
#      passes over the PR every time.
#   5. .github/steward/pr-lap.sh prints `REAL CONFLICT — left alone` and stops,
#      which is CORRECT: it will not hand-merge a file no tool owns.
#
# Nothing in that loop advances. Measured twice on 2026-09-19 (#1495, #1497) and
# four more times on 2026-09-20 (#1587, #1585, #1584, #1590) — every one needed a
# person, and #1590 was a GREEN pull request that no automation could merge,
# purely because `dev` moved four times under it. Both 2026-09-19 PRs merged
# themselves within minutes of a human pushing the merge, which is the proof that
# the rest of the automation is sound: the only thing missing was a person being
# TOLD.
#
# WHY LOUD AND NOT GATED — the ticket offers both and asks for the reading to be
# written down, so here it is. The other option was to dispatch the gate for the
# branch (`workflow_dispatch` is already on chicago-4d-check.yml). It was rejected
# on merit, not on cost: a dispatched run gates the BRANCH, not the merge result,
# and it attaches a `gate` check run to the PR's head sha. That check would
# satisfy a REQUIRED check with a verdict about a tree that is not the one that
# would land — the branch as it stands, without `dev`'s last several merges in it.
# And it still would not merge: `dirty` is not `clean`, whatever the checks say.
# So gating a conflicted PR buys a green tick that means less than the empty space
# it replaces. A reported PR is worth more than a falsely-gated one.
#
# WHAT IT REFUSES TO TOUCH, and each refusal is a fault this ticket names:
#
#   * `hold`. The owner's park switch. A held PR is `dirty` with zero check runs
#     and looks EXACTLY like the deadlock from outside — #1533 and #1576 were both
#     mistaken for it on 2026-09-20. Labels are read before anything is declared.
#   * Drafts. The steward's salvage step opens one for a run that died before its
#     PR; it is not a queue member.
#   * A PR WHOSE OWNING RUN IS STILL ALIVE. #1499 was `dirty` with zero check runs
#     and looked identical to the real thing; its run was still going, and it
#     rebased onto `dev` twice, re-derived, pushed and cleared ITSELF. A fix that
#     labels or comments on a mid-run PR is a fault of T-1368 in its own words,
#     because such a PR commonly resolves itself and colliding with a live run
#     costs more than waiting. The branch's `claim/t-nnnn` marker names the run;
#     this asks GitHub whether that run is still going.
#   * A PR whose head is younger than STUCK_MIN_AGE_MIN. Every PR is `dirty` for a
#     while after a merge into `dev` — that is T-0857 and it is the normal state of
#     this queue, not a fault. The lap is what clears it. Shouting at a PR the lap
#     has not reached yet would make this reporter noise, and noise is how the
#     previous signals were lost.
#
# REST, NEVER GraphQL, for the reason pr-lap.sh and merge-ready.sh both give at
# length: `gh pr` and `gh issue` are GraphQL, the steward PAT's GraphQL budget is
# the one that runs out, and on 2026-09-14 it ran out while REST sat untouched.
# Every call below is a REST path.
set -uo pipefail

REPO="${GITHUB_REPOSITORY:-kevinrhaas/custom}"
BASE="${STUCK_BASE:-dev}"
ONLY="${STUCK_ONLY:-}"
DRY="${STUCK_DRY_RUN:-}"
LABEL="${STUCK_LABEL:-stuck}"
MIN_AGE_MIN="${STUCK_MIN_AGE_MIN:-45}"
# The same three hours ticket.mjs calls a dead run. A claim marker older than this
# is already stolen by the next claimer, so it cannot be evidence of a live run.
RUN_HOURS="${STUCK_RUN_HOURS:-3}"
# How long to wait between re-asks while GitHub is still computing mergeability.
# A variable only so the harness can drive the retry without sleeping 15 seconds
# a PR; nothing in the workflow sets it.
RETRY_SLEEP="${STUCK_RETRY_SLEEP:-3}"
# MAY A BLIND SWEEP FAIL THIS JOB? On `dev` and on a dispatch, yes, loudly. On a
# push to a steward branch, NO — and that is not squeamishness, it is that the
# failure would land on somebody else's pull request.
#
# A workflow run started by a push creates a check run on the pushed head sha,
# and for a steward branch that sha is an open PR's head. A non-required check
# that FAILS makes the PR `unstable`, and merge-ready.sh merges only on `clean`,
# so it would leave that PR "waiting on checks" for ever — until the branch is
# pushed again, which for a finished unit never happens. A reporter built to stop
# pull requests rotting must not be the thing that rots one, and a rate limit on
# the list call is exactly the transient that would do it.
#
# Nothing is lost by softening it THERE, because the two triggers cover each
# other: the same sweep runs on every push to `dev`, where it fails hard and where
# a failure poisons nothing. A rate limit outlasts one steward push and does not
# outlast the day.
SOFT_FAIL="${STUCK_SOFT_FAIL:-}"

say() { printf '%s\n' "$*"; }

now_epoch=$(date -u +%s)
# Portable ISO-8601 → epoch, answering 0 for anything it will not vouch for.
# GNU date takes `-d`, BSD does not; the runner is GNU and the tests run on
# whatever the developer has, so both are tried.
#
# THE SHAPE IS CHECKED BEFORE `date` IS TRUSTED WITH IT, and that is not
# belt-and-braces. GNU `date -u -d "" +%s` does not fail: it answers MIDNIGHT
# TODAY, exit 0. So an API call that returned nothing — a 404, a rate limit —
# would read as a timestamp a few hours old, and after 00:45 UTC that is old
# enough for this script to declare a pull request stuck on no evidence at all.
# Caught by test_pr_stuck.mjs case 7b, which passed for the wrong reason at
# 00:20 UTC and would have failed an hour later.
to_epoch() {
  case "${1:-}" in
    [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]*) ;;
    *) echo 0; return 0 ;;
  esac
  date -u -d "$1" +%s 2>/dev/null || date -u -j -f '%Y-%m-%dT%H:%M:%SZ' "$1" +%s 2>/dev/null || echo 0
}

# THE LIST, AND ITS EXIT STATUS. `PRS=$(gh api …)` carries gh's status and this
# script runs without `-e`, so a failed call would leave PRS empty, the loop would
# run zero times, and the summary would be character for character what a healthy
# empty queue prints. That is the shape that made the blind lap look green while
# it swept nothing (pr-lap.sh, 2026-09-14) and it is checked here rather than
# re-learned. A reporter that cannot see the queue has not reported on it.
#
# `hold` is NOT filtered out here, unlike the lap and the merger. This has to SEE
# a held PR to say it left one alone, and to take its own label back off one the
# owner has since parked.
PRS=$(gh api --paginate \
        "repos/$REPO/pulls?state=open&base=$BASE&per_page=100" \
        --jq '.[] | select(.draft==false)
                  | "\(.number)\t\(.head.ref)\t\(.head.sha)\t\([.labels[].name]|join(","))"')
LIST_RC=$?
if [ "$LIST_RC" -ne 0 ]; then
  echo "::error::the PR-list call failed (exit $LIST_RC) — the stuck reporter cannot see the queue."
  echo "::error::A rate limit or an auth failure here is indistinguishable from an empty queue:"
  echo "::error::both leave the list empty and this would print 'stuck=0' and exit 0."
  if [ -n "$SOFT_FAIL" ]; then
    echo "::error::Not failing the job: this sweep was started by a push to a steward branch,"
    echo "::error::so the failure would attach to an open PR's head sha, make it \`unstable\`"
    echo "::error::and stall merge-ready.sh on it. The next push to \`dev\` fails hard instead."
    exit 0
  fi
  exit 1
fi

if [ -n "$ONLY" ]; then
  MATCHED=$(printf '%s\n' "$PRS" | awk -v n="$ONLY" -F'\t' '$1==n')
  if [ -z "$MATCHED" ]; then
    echo "::error::STUCK_ONLY=$ONLY matched no open pull request into $BASE."
    echo "::error::Drafts are filtered out before this point; \`hold\` is not."
    exit 1
  fi
  PRS="$MATCHED"
fi

# The label, created once and idempotently. Adding a label that does not exist is
# a 422 on this endpoint, so a first run in a fresh repository would report
# nothing and say it had — the same silence this script exists to end.
if [ -z "$DRY" ]; then
  gh api -X POST "repos/$REPO/labels" \
    -f name="$LABEL" -f color=B60205 \
    -f description="No automation in this repo can move this PR — see the comment" \
    >/dev/null 2>&1 || true
fi

# Is the run that owns this branch's ticket still going? Returns 0 for ALIVE.
# CONSERVATIVE BY CONSTRUCTION: anything it cannot read, it calls alive. Acting on
# a live run is a fault this ticket names by number (#1499); waiting one more
# sweep on a dead one costs nothing, because the next push sweeps again.
owning_run_alive() {
  local br="$1" tid marker run_url api_path status marker_date marker_epoch marker_age
  tid=$(printf '%s' "$br" | grep -oiE 't-[0-9]{3,5}' | head -1 | tr 'A-Z' 'a-z')
  [ -n "$tid" ] || { LIVE_WHY="the branch names no ticket, so no claim can be read"; return 1; }

  marker=$(gh api "repos/$REPO/commits/heads/claim/$tid" --jq '.commit.message' 2>/dev/null)
  if [ -z "$marker" ]; then
    LIVE_WHY="no claim/$tid marker — nothing holds the ticket"
    return 1
  fi

  run_url=$(printf '%s\n' "$marker" | sed -n 's|^run: *\(https://github.com/[^ ]*\)|\1|p' | head -1)
  api_path=$(printf '%s' "$run_url" | sed -n 's|^https://github.com/\([^/]*\)/\([^/]*\)/actions/runs/\([0-9]*\).*|repos/\1/\2/actions/runs/\3|p')
  if [ -n "$api_path" ]; then
    status=$(gh api "$api_path" --jq '.status' 2>/dev/null)
    case "$status" in
      queued|in_progress|waiting|requested|pending)
        LIVE_WHY="claim/$tid names a run that is still $status"; return 0 ;;
      completed)
        LIVE_WHY="claim/$tid names a run that has completed"; return 1 ;;
    esac
  fi

  # The marker is there and the run cannot be read. Fall back on the marker's own
  # age, which is the rule ticket.mjs already applies: older than RUN_HOURS is a
  # run that died and the claim is stolen from it.
  marker_date=$(gh api "repos/$REPO/commits/heads/claim/$tid" --jq '.commit.committer.date' 2>/dev/null)
  marker_epoch=$(to_epoch "${marker_date:-}")
  marker_age=$(( (now_epoch - ${marker_epoch:-0}) / 3600 ))
  if [ "${marker_epoch:-0}" -ne 0 ] && [ "$marker_age" -gt "$RUN_HOURS" ]; then
    LIVE_WHY="claim/$tid names no readable run and is ${marker_age}h old — past the ${RUN_HOURS}h a run lives"
    return 1
  fi
  LIVE_WHY="claim/$tid stands and its run could not be read — assuming it is alive"
  return 0
}

# The newest `gate` check run on a head, as `status:conclusion\tdetails_url`, or
# nothing at all when the head carries none. NEWEST BY `started_at` AND NOT BY
# ARRAY ORDER: a head that was re-gated carries several, and the first one the API
# hands back is not reliably the one that decided the PR.
gate_verdict() {
  gh api "repos/$REPO/commits/$1/check-runs?per_page=100" \
    --jq '[.check_runs[]? | select(.name=="gate")]
          | sort_by(.started_at // "") | last
          | if . == null then empty
            else "\(.status):\(.conclusion // "none")\t\(.details_url // "")" end' \
    2>/dev/null
}

# The steps that actually failed, read from the job the check run points at. WHY
# THIS AND NOT "the gate is red": the whole cost of this state is that somebody
# has to open the logs to find out what broke, and the reporter has just been
# there. Measured 2026-09-21 on the two PRs that prompted T-1510 — #1616 failed
# one step (`Does this change carry a changelog entry?`) and #1618 failed another
# (`Run the gate`), and those two words are the difference between a five-minute
# fix and a re-derivation. It answers nothing when the job cannot be read; a
# comment with no step list is still worth more than no comment.
failing_steps() {
  local jid
  jid=$(printf '%s' "${1:-}" | sed -n 's|.*/job/\([0-9][0-9]*\).*|\1|p')
  [ -n "$jid" ] || return 1
  gh api "repos/$REPO/actions/jobs/$jid" \
    --jq '.steps[]? | select(.conclusion=="failure" or .conclusion=="timed_out")
          | "  * \(.name)"' 2>/dev/null
}

STUCK=0; RED=0; HELD=0; MIDRUN=0; YOUNG=0; FINE=0; CLEARED=0

while IFS=$'\t' read -r N BR SHA LABELS; do
  [ -n "${N:-}" ] || continue

  # LABELS FIRST, BEFORE ANY STATE IS READ. A held PR is not a stuck PR however
  # identical the two look, and reading the state first invites reporting it and
  # only then noticing.
  if printf '%s' ",$LABELS," | grep -q ',hold,'; then
    say "#$N  held — the owner parked this on purpose; not a deadlock however much it looks like one"
    HELD=$((HELD+1)); continue
  fi
  HAS_LABEL=
  printf '%s' ",$LABELS," | grep -q ",$LABEL," && HAS_LABEL=1

  # `mergeable_state` is computed LAZILY: straight after a push GitHub answers
  # `unknown` and starts the computation as a side effect of being asked. The same
  # retry merge-ready.sh uses, for the same reason.
  STATE=unknown
  for _ in 1 2 3 4 5; do
    STATE=$(gh api "repos/$REPO/pulls/$N" --jq '.mergeable_state' 2>/dev/null || echo error)
    [ "$STATE" = "unknown" ] || break
    sleep "$RETRY_SLEEP"
  done

  # TWO SHAPES OF STUCK, and the second was added by T-1510 after a queue grew
  # 1 -> 5 open PRs in two hours with `dev` still for 95 minutes of it.
  #
  #   A. `dirty` — the T-1368 deadlock the header sets out at length.
  #   B. A RED GATE under a run that has finished. The lap merges the base in and
  #      pushes; it does not gate, deliberately (that cost ~7 min a PR and was why
  #      the queue never converged). `merge-ready` merges only `clean` and a red PR
  #      never is. So nothing in this repository is coming for it — which is this
  #      reporter's whole subject, arriving in a state it used to wave through.
  #      Measured 2026-09-21: #1616's steward run completed SUCCESS 28 seconds
  #      after its gate went red, #1618's four minutes BEFORE its own did, and
  #      both sat until a person read the logs.
  #
  # `unknown` is still NOT a diagnosis — #1518 read `unknown` indefinitely and
  # merged fine when asked directly. `behind` is the lap's. `blocked` is the one
  # that needed splitting: blocked-while-gating has the gate moving it, and
  # blocked-because-the-gate-failed has nothing.
  SHAPE=
  if [ "$STATE" = "dirty" ]; then
    SHAPE=deadlock
  else
    VERDICT=$(gate_verdict "$SHA")
    GATE_STATUS=${VERDICT%%:*}
    GATE_REST=${VERDICT#*:}
    GATE_CONC=${GATE_REST%%$'\t'*}
    GATE_URL=${GATE_REST#*$'\t'}
    # A GATE STILL RUNNING IS NOT A RED ONE, and neither is a head with no gate
    # on it at all — that one belongs to shape A or to a PR the gate has not
    # reached. Only a COMPLETED, failing verdict counts.
    if [ "$GATE_STATUS" = "completed" ]; then
      case "$GATE_CONC" in
        failure|timed_out|cancelled|action_required) SHAPE=redgate ;;
      esac
    fi
  fi

  if [ -z "$SHAPE" ]; then
    if [ -n "$HAS_LABEL" ]; then
      # A LABEL THAT OUTLIVES ITS REASON IS WORSE THAN NO LABEL. Something moved
      # this PR after all, so the reporter takes its own word back — and that now
      # covers a gate that has gone green as well as a merge that has come clean.
      say "#$N  $STATE — no longer stuck; taking the \`$LABEL\` label back off"
      [ -z "$DRY" ] && gh api -X DELETE "repos/$REPO/issues/$N/labels/$LABEL" >/dev/null 2>&1
      CLEARED=$((CLEARED+1))
    else
      say "#$N  $STATE — something can move this"
      FINE=$((FINE+1))
    fi
    continue
  fi

  HEAD_DATE=$(gh api "repos/$REPO/commits/$SHA" --jq '.commit.committer.date' 2>/dev/null)
  HEAD_EPOCH=$(to_epoch "${HEAD_DATE:-}")
  # AN UNREADABLE DATE IS NOT AN OLD ONE. `to_epoch` answers 0 when it cannot
  # parse, and 0 would make every such PR read as decades old and get reported.
  # A reporter that shouts when it cannot see is the fault this script is built
  # around, so it holds its tongue instead and the next sweep asks again.
  # THE THREE REFUSALS BELOW GUARD BOTH SHAPES, and that is the reason the shape
  # is decided above rather than acted on there: an unreadable date, a head the
  # lap has not reached, and a run still working are wrong to report whether the
  # PR is conflicted or red, and each was learned the expensive way once already.
  SAW="$SHAPE"
  [ "$SHAPE" = "redgate" ] && SAW="$STATE with a red gate"
  if [ "${HEAD_EPOCH:-0}" -eq 0 ]; then
    say "#$N  $SAW, but its head commit date could not be read — not reporting on a PR whose age is unknown"
    YOUNG=$((YOUNG+1)); continue
  fi
  AGE_MIN=$(( (now_epoch - HEAD_EPOCH) / 60 ))
  if [ "$AGE_MIN" -lt "$MIN_AGE_MIN" ]; then
    say "#$N  $SAW, and its head is ${AGE_MIN}m old — every PR is dirty for a while after a merge into $BASE (T-0857) and a fresh red gate is often re-pushed within the minute; neither the lap nor the run has had its turn"
    YOUNG=$((YOUNG+1)); continue
  fi

  LIVE_WHY=
  if owning_run_alive "$BR"; then
    say "#$N  $SAW, but $LIVE_WHY — left alone (#1499 cleared itself exactly like this)"
    MIDRUN=$((MIDRUN+1)); continue
  fi

  CHECKS=$(gh api "repos/$REPO/commits/$SHA/check-runs" --jq '.total_count' 2>/dev/null || echo 0)
  [ -n "$CHECKS" ] || CHECKS=0

  if [ "$SHAPE" = "redgate" ]; then
    say "#$N  STUCK — $STATE, gate $GATE_CONC, ${AGE_MIN}m old, and $LIVE_WHY"
    RED=$((RED+1))
  else
    say "#$N  STUCK — dirty, $CHECKS check run(s), ${AGE_MIN}m old, and $LIVE_WHY"
    STUCK=$((STUCK+1))
  fi
  [ -n "$DRY" ] && continue

  if [ -z "$HAS_LABEL" ]; then
    gh api -X POST "repos/$REPO/issues/$N/labels" -f "labels[]=$LABEL" >/dev/null 2>&1 \
      && say "     labelled \`$LABEL\`" \
      || say "     could not label #$N"
  fi

  # ONE COMMENT PER STUCK HEAD. Once-ever would go quiet if a PR came unstuck and
  # then stuck again on a later head; once-per-sweep would bury the PR. The head
  # sha is in the marker, so each distinct stuck head is said exactly once.
  if [ "$SHAPE" = "redgate" ]; then
    MARK="PR stuck: the gate is red and the run that owned it has finished (\`${SHA:0:8}\`)"
  else
    MARK="PR stuck: no automation in this repository can move this pull request (\`${SHA:0:8}\`)"
  fi
  if gh api --paginate "repos/$REPO/issues/$N/comments" --jq '.[].body' 2>/dev/null | grep -qF "$MARK"; then
    say "     already said so on this head"
    continue
  fi

  if [ "$SHAPE" = "redgate" ]; then
    { printf '%s.\n\n' "$MARK"
      printf 'The `gate` check run on this head completed **%s**, and the steward run that\n' "$GATE_CONC"
      printf 'owns this branch has finished. Nothing in this repository is coming back for it:\n\n'
      printf '* `.github/steward/pr-lap.sh` merges `%s` in and pushes. It does NOT gate — that\n' "$BASE"
      printf '  cost ~7 minutes a PR and was why the queue never converged — so a red gate is\n'
      printf '  not something it can notice, let alone fix.\n'
      printf '* `.github/steward/merge-ready.sh` merges only what GitHub calls `clean`, and a PR\n'
      printf '  with a failing required check is never `clean`.\n'
      printf '* The run that would have pushed a fix is over. On 2026-09-21 two runs finished\n'
      printf '  SUCCESS while leaving a red PR behind (#1616, #1618), which is what this\n'
      printf '  report exists to stop being silent about.\n\n'
      STEPS=$(failing_steps "$GATE_URL")
      if [ -n "$STEPS" ]; then
        printf 'The step(s) that failed:\n\n%s\n\n' "$STEPS"
        # A STEP `preflight.sh` ALREADY ASKS is worth naming, because the run that
        # opened this PR could have found it in seconds and did not. The changelog-
        # entry question is asked ONLY on the `pull_request` event, where a base ref
        # exists, and is deliberately out of tools/check.sh — the nightly bake
        # regenerates data/ and correctly ships no entry, so a gate inside check.sh
        # would fail every bake (T-0409). Out of check.sh is not out of reach:
        # tools/preflight.sh asks it against the merge base, which is the same pair
        # of shas the workflow passes. AGENTS.md has required it before opening a PR
        # since 2026-09-10 and PR #1049 sat red for 2h19m on the one-line trailer it
        # would have caught. Six more did on 2026-09-21. A rule with no enforcement
        # is the fault check-changelog-entry.mjs was written to end, arriving one
        # level up.
        if printf '%s' "$STEPS" | grep -q 'carry a changelog entry'; then
          printf '`./tools/preflight.sh` asks that question BEFORE the PR is opened, against the\n'
          printf 'merge base and with the same shas the workflow uses. It is out of `check.sh` on\n'
          printf 'purpose — the bake regenerates `data/` and correctly ships no entry — which is\n'
          printf 'why running the gate alone cannot find it. AGENTS.md has required preflight\n'
          printf 'before a PR is opened since 2026-09-10.\n\n'
        fi
      else
        printf 'The failing step could not be read from the job; open the gate run from the\n'
        printf 'Checks tab.\n\n'
      fi
      printf 'This reporter does not re-run, revert or repair anything, and that is deliberate:\n'
      printf 'both of the PRs above needed real judgement (a rule that had stopped firing and\n'
      printf 'had to be retired; a report whose prose contradicted its own table), and a robot\n'
      printf 'that had guessed at either would have been worse than the silence.\n\n'
      printf 'What clears it:\n\n'
      printf '1. Reproduce the failing step in a clone of this branch with `%s` merged in,\n' "$BASE"
      printf '   fix it, and push. The gate re-runs on the push and `merge-ready` takes it.\n'
      printf '2. If the failure is not this PR'"'"'s — red on `%s` too — say so on the PR and\n' "$BASE"
      printf '   port the fix rather than widening this branch.\n'
      printf '3. Or close it and re-cut the work on a current `%s`.\n\n' "$BASE"
      printf 'Park it with the `hold` label if it is waiting on the owner on purpose — this\n'
      printf 'reporter reads labels first and will leave a held PR alone.\n\n'
      printf -- '---\n_Generated by [Claude Code](https://claude.ai/code)_\n'
    } > /tmp/pr-stuck-comment.md
  else
  { printf '%s.\n\n' "$MARK"
    printf 'GitHub reports this PR `dirty`'
    if [ "$CHECKS" -eq 0 ]; then
      printf ' with **zero check runs**. That pair is the deadlock T-1368 names:\n\n'
      printf 'A `dirty` PR has no merge ref; the gate runs on `pull_request`, which needs one,\n'
      printf 'so no gate ever starts; `gate` is a required check, so GitHub never calls the PR\n'
      printf '`clean`; and `merge-ready.sh` merges only on `clean`. The lap is the one thing that\n'
      printf 'can break the cycle, and it has not — either it refused a conflict it does not own,\n'
      printf 'or it has not run since this head was pushed.\n\n'
    else
      printf ' with %s check run(s). The gate may well be green; `dirty` is not `clean`,\n' "$CHECKS"
      printf 'so `merge-ready.sh` will pass over it for as long as it stays this way. #1590 was\n'
      printf 'exactly this on 2026-09-20: a GREEN pull request that no automation could merge,\n'
      printf 'because `dev` moved four times under it.\n\n'
    fi
    printf 'The branch may well merge `dev` with no conflict at all. **GitHub never runs this\n'
    printf "repo's merge drivers** (T-0857), so a branch that merges cleanly in a clone is still\n"
    printf 'reported conflicting by the platform.\n\n'
    printf 'What clears it, in the order to try:\n\n'
    printf '1. Dispatch **Chicago 4D — PR lap** with `only: %s`. If it pushes, the gate runs\n' "$N"
    printf '   on the merge and `merge-ready` takes it from there.\n'
    printf '2. If the lap prints `REAL CONFLICT — left alone`, the conflict is in content no\n'
    printf '   tool owns and it wants hands:\n\n'
    printf '```\n'
    printf 'git fetch origin %s %s\n' "$BASE" "$BR"
    printf 'git checkout -B %s origin/%s\n' "$BR" "$BR"
    printf 'chicago/4d/tools/setup-merge-drivers.sh   # or the merge will not resolve\n'
    printf 'git merge origin/%s\n' "$BASE"
    printf '# resolve, then:\n'
    printf '( cd chicago/4d && node tools/rederive.mjs --run && node tools/ticket.mjs reconcile --base origin/%s && ./tools/publish.sh )\n' "$BASE"
    printf 'git add -A && git commit && git push origin HEAD:%s\n' "$BR"
    printf '```\n\n'
    printf '3. Or close it and re-cut the work on a current `%s`.\n\n' "$BASE"
    printf 'Park it with the `hold` label if it is waiting on the owner on purpose — this\n'
    printf 'reporter reads labels first and will leave a held PR alone.\n\n'
    printf -- '---\n_Generated by [Claude Code](https://claude.ai/code)_\n'
  } > /tmp/pr-stuck-comment.md
  fi

  # `jq -Rs` wraps the file as a JSON string: the body carries backticks, a fenced
  # block and paths, and none of that survives interpolation into a shell argument.
  if jq -Rs '{body: .}' < /tmp/pr-stuck-comment.md \
       | gh api -X POST "repos/$REPO/issues/$N/comments" --input - >/dev/null 2>/tmp/pr-stuck.err; then
    say "     said so on the PR"
  else
    say "     could not comment on #$N — $(tail -1 /tmp/pr-stuck.err 2>/dev/null | cut -c1-120)"
    say "     the reading above stands; it is in this log and not on the PR"
  fi
done <<< "$PRS"

say ""
say "PR stuck: deadlocked=$STUCK red-gate=$RED held=$HELD mid-run=$MIDRUN too-young=$YOUNG moving=$FINE unlabelled=$CLEARED"
say "  (it reports; it never merges, pushes or resolves. The lap and merge-ready do those.)"
