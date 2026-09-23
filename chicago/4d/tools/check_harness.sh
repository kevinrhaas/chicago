# The gate's step harness — sourced by tools/check.sh.
#
# It is a file of its own for one reason: tools/test_check_harness.sh can source it
# and exercise it, which nothing could do while it lived inline in a 2,500-line gate.
#
# T-0763. A SELF-TEST IS NOT A FAILURE, AND THE OUTPUT USED TO SAY OTHERWISE.
# Around a hundred steps here deliberately break a derivation and REQUIRE its
# assertions to fire. A fired assertion prints the same `FAIL <sentence>` a real one
# does — one of them prints `2 check(s) FAILED` — so on a GREEN tree (`check.sh` exit
# 0) the output carried fourteen lines that read exactly like a broken gate. That cost
# three tickets: T-0745 wrote three of its four acceptance clauses on six such lines
# and sent the next run at terrain and street geometry that were fine, and T-0522,
# T-0612 and T-0683 each reported a red dev that was not one.
#
# Two changes, and neither silences anything:
#
#   1. `selftest` replaces `step` for those steps. It marks the heading and prefixes
#      EVERY line of the transcript with CHECK_SELFTEST_TAG, so a fired assertion is
#      legible as one at the line level — which is the level `grep -i fail` reads at,
#      and the level a run's log gets skimmed at.
#   2. `check_summary` names the failing steps ONCE at the end. The roll-up existed
#      only inline, next to the step that failed, a thousand lines up.
#
# tools/test_check_harness.sh holds both to that, and scans check.sh for a self-test
# that went back through `step`.

# Every line of a self-test's transcript starts with this. Deliberately plain ASCII
# and no colour: its whole job is to survive a grep and a log file.
CHECK_SELFTEST_MARK='self-test |'
CHECK_SELFTEST_TAG="   ${CHECK_SELFTEST_MARK} "

CHECK_FAILED=0
CHECK_STEPS=0
CHECK_SELFTESTS=0
CHECK_FAILED_LABELS=()

step() {
  local label="$1"; shift
  CHECK_STEPS=$((CHECK_STEPS + 1))
  printf '\n\033[1m== %s\033[0m\n' "$label"
  if "$@"; then
    return 0
  else
    _check_record_failure "$label"
    return 1
  fi
}

# Same contract as `step`, for a step that PROVES a gate by breaking it. The exit
# status still decides — a self-test that stops firing fails the gate exactly as
# before — but the transcript is tagged, because the transcript is the part a human
# reads wrong.
selftest() {
  local label="$1"; shift
  CHECK_STEPS=$((CHECK_STEPS + 1))
  CHECK_SELFTESTS=$((CHECK_SELFTESTS + 1))
  printf '\n\033[1m== %s\033[0m \033[2m(self-test: the assertions below are meant to fire)\033[0m\n' "$label"
  # stderr is folded in because that is where most of these assertions print, and an
  # untagged stderr line is the one line that would still read as a failure. The
  # status is read from PIPESTATUS rather than relied on from `pipefail`, so sourcing
  # this file cannot be made wrong by the caller's shell options.
  "$@" 2>&1 | sed "s@^@${CHECK_SELFTEST_TAG}@"
  local rc=${PIPESTATUS[0]}
  if [ "$rc" -eq 0 ]; then
    return 0
  else
    _check_record_failure "$label"
    return 1
  fi
}

_check_record_failure() {
  CHECK_FAILED=1
  CHECK_FAILED_LABELS+=("$1")
  printf '\033[31m   ^ %s failed\033[0m\n' "$1"
}

# The last thing the gate prints. On a pass it says, in words, why FAIL lines are
# still above it; on a failure it lists the steps that failed and nothing else, so
# the answer to "what is red?" is at the bottom of the log where the reader already is.
check_summary() {
  printf '\n'
  if [ "$CHECK_FAILED" -eq 0 ]; then
    printf '\033[32mCHECK PASS\033[0m — %d steps, none red.\n' "$CHECK_STEPS"
    printf '  %d of them are self-tests that prove a gate by breaking it; their\n' "$CHECK_SELFTESTS"
    printf "  assertions fire on purpose and every line of it is prefixed '%s'.\n" "$CHECK_SELFTEST_MARK"
  else
    printf '\033[31mCHECK FAIL\033[0m — %d of %d steps failed:\n' \
      "${#CHECK_FAILED_LABELS[@]}" "$CHECK_STEPS"
    local label
    for label in "${CHECK_FAILED_LABELS[@]}"; do
      printf '  \033[31m*\033[0m %s\n' "$label"
    done
    printf '\nFix those before committing. Anything else above that looks red is a\n'
    printf "self-test firing — those lines are prefixed '%s'.\n" "$CHECK_SELFTEST_MARK"
  fi
  return "$CHECK_FAILED"
}
