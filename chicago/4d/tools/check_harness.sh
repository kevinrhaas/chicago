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

# T-1289. WHERE THE GATE'S TIME GOES, recorded rather than guessed. Set
# CHECK_TIMINGS to a path and every step appends "<seconds>\t<kind>\t<label>" to it.
# Off by default: no file, no cost beyond two clock reads a step. The gate's duration
# is the window in which `dev` can move under an open pull request, so it is the
# number that decides how much a merge round costs — and nothing here measured it.
CHECK_TIMINGS="${CHECK_TIMINGS:-}"

_check_now() { date +%s.%N; }

_check_time() {
  [ -n "$CHECK_TIMINGS" ] || return 0
  awk -v s="$1" -v e="$2" -v k="$3" -v l="$4" \
      -v c="$5" 'BEGIN { printf "%.3f\t%s\t%s\t%s\n", e - s, k, c, l }' >> "$CHECK_TIMINGS"
}

# ---------------------------------------------------------------------------
# T-1289. THE GATE RUNS ITS STEPS IN PARALLEL, AND PRINTS THEM IN ORDER.
#
# WHY THIS IS THE FIX AND NOT A MERGE-ORDERING ONE. Every merge into `dev` makes
# every other open pull request `dirty`, and the window in which that can happen to
# a PR is exactly how long its gate takes. T-1289 proposed three ways to reorder
# MERGES; none of them shortens the gate, and on 2026-09-18 three pull requests cost
# nine dev merges between them, four of those on one PR that was overtaken three
# times while its gate ran. Shortening the window attacks the cause.
#
# MEASURED, because the ticket says an unmeasured change here is not this ticket.
# 499 steps, 773 s serial. 380 of them (76 %) finish in under a second and together
# account for under a tenth of the time; the slowest twenty are half of it, and one
# self-test alone is 79 s. That shape decided the design:
#
#     4 jobs, ordered batches (each batch costs its slowest member):  559 s, 1.4x
#     4 jobs, work-stealing  (a free worker takes the next step):     240 s, 3.2x
#
# Batching was the simpler code and it is worth 1.4x, because the heavy tail lands
# one long step in a batch and the other three wait on it. So this is a real pool.
#
# ORDER IS PRESERVED IN THE OUTPUT, WHICH IS THE PART THAT MATTERS. The transcript
# is read by people and by agents, and T-0763 is the record of what happens when it
# reads wrong — three tickets filed against self-test lines that were never failures.
# So a step's output is captured whole and replayed at its declared position, never
# interleaved. A parallel run's log is byte-comparable with a serial one.
#
# CHECK_JOBS=1 keeps the old path exactly: run, print, move on. Nothing is queued and
# no temporary file is made. That is the escape hatch for any step that turns out to
# share state with another, and the control in the before/after measurement.
CHECK_JOBS="${CHECK_JOBS:-1}"

_CHECK_Q_KIND=()
_CHECK_Q_LABEL=()
_CHECK_Q_CMD=()

# A queued step is stored as a %q-quoted string and re-run with `eval`. The quoting is
# produced here rather than parsed from anywhere, so it round-trips whatever a caller
# passed — including the labels with em-dashes and quotes that this gate is full of.
_check_enqueue() {
  local kind="$1" label="$2"; shift 2
  _CHECK_Q_KIND+=("$kind")
  _CHECK_Q_LABEL+=("$label")
  _CHECK_Q_CMD+=("$(printf '%q ' "$@")")
}

# One queued step, in its own process: everything it prints goes to its own file, and
# its status to another. A self-test's transcript is tagged here, exactly as the
# serial path tags it, so the two produce the same bytes.
_check_worker() {
  local i="$1" dir="$2"
  local kind="${_CHECK_Q_KIND[$i]}" cmd="${_CHECK_Q_CMD[$i]}"
  local t0; t0=$(_check_now)
  if [ "$kind" = selftest ]; then
    eval "$cmd" > "$dir/$i.raw" 2>&1
    local rc=$?
    sed "s@^@${CHECK_SELFTEST_TAG}@" < "$dir/$i.raw" > "$dir/$i.out"
    rm -f "$dir/$i.raw"
  else
    eval "$cmd" > "$dir/$i.out" 2>&1
    local rc=$?
  fi
  printf '%s' "$rc" > "$dir/$i.rc"
  _check_time "$t0" "$(_check_now)" "$kind" "${_CHECK_Q_LABEL[$i]}" "$cmd"
}

# Run everything queued, then print it in declaration order. Called at a barrier and
# by check_summary; queueing nothing makes it a no-op, so the serial path never
# reaches the pool at all.
check_flush() {
  local n="${#_CHECK_Q_LABEL[@]}"
  [ "$n" -eq 0 ] && return 0
  local dir; dir="$(mktemp -d)"
  local i running=0
  for ((i = 0; i < n; i++)); do
    _check_worker "$i" "$dir" &
    running=$((running + 1))
    if [ "$running" -ge "$CHECK_JOBS" ]; then wait -n 2>/dev/null || wait; running=$((running - 1)); fi
  done
  wait
  for ((i = 0; i < n; i++)); do
    local label="${_CHECK_Q_LABEL[$i]}" kind="${_CHECK_Q_KIND[$i]}"
    CHECK_STEPS=$((CHECK_STEPS + 1))
    if [ "$kind" = selftest ]; then
      CHECK_SELFTESTS=$((CHECK_SELFTESTS + 1))
      printf '\n\033[1m== %s\033[0m \033[2m(self-test: the assertions below are meant to fire)\033[0m\n' "$label"
    else
      printf '\n\033[1m== %s\033[0m\n' "$label"
    fi
    if [ "$(cat "$dir/$i.rc" 2>/dev/null || echo 1)" -ne 0 ]; then
      # A POOLED FAILURE IS NOT YET A FAILURE. T-1336: some steps mutate the working
      # tree and put it back — a self-test that breaks a live file to prove a check
      # fires is the whole pattern, and read_census_1830.py's is the one that caught
      # us — so a step that ran BESIDE one of those may have read a tree that was
      # briefly wrong. The pool is drained by now, so re-running it alone answers the
      # only question that matters: is it red on a quiet tree?
      #
      # This does NOT make a red gate green. A real failure fails both times and is
      # recorded exactly as before. What it removes is the false red, which on this
      # queue costs a push, a CI run and a reviewer's trust.
      #
      # AND IT DOES NOT HIDE THE RACE EITHER, which is the part worth insisting on.
      # A step that fails in the pool and passes alone is NAMED, counted, and printed
      # again in the summary under its own heading. A quiet retry would turn a race
      # into folklore about a flaky gate; this makes it a line of output with the
      # step's name in it, so the offender can be found and marked.
      local _rr_out _rr_rc
      _rr_out="$dir/$i.retry"
      if [ "$kind" = selftest ]; then
        eval "${_CHECK_Q_CMD[$i]}" > "$_rr_out.raw" 2>&1
        _rr_rc=$?
        sed "s@^@${CHECK_SELFTEST_TAG}@" < "$_rr_out.raw" > "$_rr_out"
        rm -f "$_rr_out.raw"
      else
        eval "${_CHECK_Q_CMD[$i]}" > "$_rr_out" 2>&1
        _rr_rc=$?
      fi
      if [ "$_rr_rc" -eq 0 ]; then
        CHECK_RACED_LABELS+=("$label")
        [ -s "$_rr_out" ] && cat "$_rr_out"
        printf '\033[33m   ~ %s failed in the pool and PASSED ALONE — T-1336, a step beside it moved the tree\033[0m\n' "$label"
      else
        [ -s "$_rr_out" ] && cat "$_rr_out"
        _check_record_failure "$label"
      fi
      rm -f "$_rr_out"
    else
      [ -s "$dir/$i.out" ] && cat "$dir/$i.out"
    fi
  done
  rm -rf "$dir"
  _CHECK_Q_KIND=(); _CHECK_Q_LABEL=(); _CHECK_Q_CMD=()
  return 0
}

CHECK_FAILED=0
CHECK_STEPS=0
CHECK_SELFTESTS=0
CHECK_FAILED_LABELS=()
# Steps that went red in the pool and green alone (T-1336). Not failures, and not
# nothing: each one is a step that shares state with a neighbour.
CHECK_RACED_LABELS=()

step() {
  local label="$1"; shift
  if [ "$CHECK_JOBS" -gt 1 ]; then _check_enqueue step "$label" "$@"; return 0; fi
  CHECK_STEPS=$((CHECK_STEPS + 1))
  printf '\n\033[1m== %s\033[0m\n' "$label"
  local _t0 _cmd; _t0=$(_check_now); _cmd="$*"
  if "$@"; then
    _check_time "$_t0" "$(_check_now)" step "$label" "$_cmd"
    return 0
  else
    _check_time "$_t0" "$(_check_now)" step "$label" "$_cmd"
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
  if [ "$CHECK_JOBS" -gt 1 ]; then _check_enqueue selftest "$label" "$@"; return 0; fi
  CHECK_STEPS=$((CHECK_STEPS + 1))
  CHECK_SELFTESTS=$((CHECK_SELFTESTS + 1))
  printf '\n\033[1m== %s\033[0m \033[2m(self-test: the assertions below are meant to fire)\033[0m\n' "$label"
  # stderr is folded in because that is where most of these assertions print, and an
  # untagged stderr line is the one line that would still read as a failure. The
  # status is read from PIPESTATUS rather than relied on from `pipefail`, so sourcing
  # this file cannot be made wrong by the caller's shell options.
  local _t0 _cmd; _t0=$(_check_now); _cmd="$*"
  "$@" 2>&1 | sed "s@^@${CHECK_SELFTEST_TAG}@"
  local rc=${PIPESTATUS[0]}
  _check_time "$_t0" "$(_check_now)" selftest "$label" "$_cmd"
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

# T-1336. Printed on a PASS as loudly as on a failure, because this is the only
# place the race is visible. A step that failed in the pool and passed alone shares
# state with something running beside it — almost always a self-test that breaks a
# live file to prove a check fires and restores it in a `finally`. The gate's verdict
# is correct either way; this is the list of steps that should not be in the pool.
_check_report_races() {
  [ "${#CHECK_RACED_LABELS[@]}" -eq 0 ] && return 0
  printf '\n\033[33m%d step(s) failed in the pool and passed alone (T-1336):\033[0m\n' \
    "${#CHECK_RACED_LABELS[@]}"
  local label
  for label in "${CHECK_RACED_LABELS[@]}"; do
    printf '  \033[33m~\033[0m %s\n' "$label"
  done
  printf '  Each one read a working tree a neighbour was briefly holding wrong. The\n'
  printf '  verdict above is from the quiet re-run and is correct; these steps still\n'
  printf '  need to be taken out of the pool. CHECK_JOBS=1 reproduces without the race.\n'
}

# The last thing the gate prints. On a pass it says, in words, why FAIL lines are
# still above it; on a failure it lists the steps that failed and nothing else, so
# the answer to "what is red?" is at the bottom of the log where the reader already is.
check_summary() {
  check_flush
  printf '\n'
  _check_report_races
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
