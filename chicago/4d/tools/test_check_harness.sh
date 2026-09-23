#!/usr/bin/env bash
# T-0763. The gate's own output, held to being readable.
#
#   tools/test_check_harness.sh              the gate
#   tools/test_check_harness.sh --self-test  prove it by breaking it
#
# Two things are asserted, and the second is the one that rots:
#
#   A. tools/check_harness.sh behaves — `selftest` tags every line of a transcript
#      including stderr, still fails when its command does, and `check_summary`
#      names the failing steps once at the end and prints nothing failure-shaped on
#      a pass.
#   B. tools/check.sh USES it — no step that runs a self-test goes through `step`,
#      where its fired assertions would print untagged. That is the rule three
#      tickets were misfiled for want of, and it is one `step` away from returning.
set -uo pipefail
cd "$(dirname "$0")/.."

PASS=0
FAILN=0
ok()   { PASS=$((PASS + 1)); printf '  ok    %s\n' "$1"; }
bad()  { FAILN=$((FAILN + 1)); printf '  FAIL  %s\n' "$1"; }
want() { if [ "$1" = "$2" ]; then ok "$3"; else bad "$3 — wanted [$2], got [$1]"; fi; }

# ---------------------------------------------------------------- A. the harness

# Sourced into a subshell per case, because the harness keeps counters in globals.
harness_run() { # <body> -> transcript on stdout, exit status preserved
  bash -c '
    set -uo pipefail
    source tools/check_harness.sh
    '"$1"'
  ' 2>&1
}

transcript="$(harness_run '
  selftest "a self-test that fires" bash -c "echo FAIL the roofs are wrong; echo ok >&2"
  check_summary
')"

untagged="$(printf '%s\n' "$transcript" | grep -c '^FAIL' || true)"
want "$untagged" "0" "a fired assertion never starts a line"
tagged="$(printf '%s\n' "$transcript" | grep -c '^   self-test | ' || true)"
want "$tagged" "2" "every transcript line is tagged, stderr included"
case "$transcript" in
  *"self-test | FAIL the roofs are wrong"*) ok "the assertion's own words are kept, not silenced" ;;
  *) bad "the assertion's own words are kept, not silenced" ;;
esac
case "$transcript" in
  *CHECK\ PASS*) ok "a self-test that fires leaves the gate green" ;;
  *) bad "a self-test that fires leaves the gate green" ;;
esac

# A green run must give a reader nothing that reads as a failure once the self-test
# transcripts are set aside. That is the ticket's acceptance, stated as a test.
residue="$(printf '%s\n' "$transcript" | grep -v '^   self-test | ' | grep -ci 'fail' || true)"
want "$residue" "0" "a green run prints no failure-shaped line of its own"

# The status still decides: a self-test whose assertions stop firing is a red gate.
harness_run 'selftest "a self-test gone quiet" false; check_summary' >/dev/null
want "$?" "1" "a self-test that stops firing still fails the gate"

rollup="$(harness_run '
  step "the first gate" true
  step "the second gate" false
  selftest "a self-test gone quiet" false
  check_summary
')"
named="$(printf '%s\n' "$rollup" | grep -c '^  .\[31m\*.\[0m ' || true)"
want "$named" "2" "the roll-up names every failing step, once each"
case "$rollup" in
  *"CHECK FAIL"*"2 of 3 steps failed"*) ok "the roll-up counts steps, not lines" ;;
  *) bad "the roll-up counts steps, not lines — got: $(printf '%s' "$rollup" | tr -d '\n' | tail -c 120)" ;;
esac
plain_rollup="$(printf '%s\n' "$rollup" | sed 's/\x1b\[[0-9;]*m//g')"
case "$plain_rollup" in
  *"  * the second gate"*) ok "a failing step is named at the end, not only inline" ;;
  *) bad "a failing step is named at the end, not only inline" ;;
esac

# ------------------------------------------------------- B. the gate uses it

# A step is written either on one line (`step "label" check_js`) or on two, with the
# command on the continuation. Both shapes exist in check.sh, so the scan reads the
# command out of whichever one it is looking at.
scan_check() { # <file> -> offending "line: reason" rows on stdout
  awk '
    /^step "/ || /^selftest "/ {
      n = NR; kind = ($0 ~ /^selftest "/) ? "selftest" : "step"
      if ($0 ~ /\\$/) { getline cmd } else { cmd = $0 }
      looks = (cmd ~ /self-?test/)
      if (kind == "step" && looks)
        printf "%d: a self-test runs through step(), so its fired assertions print untagged:%s\n", n, cmd
      if (kind == "selftest" && !looks)
        printf "%d: selftest() wraps something that is not a self-test:%s\n", n, cmd
    }
  ' "$1"
}

if [ "${1:-}" = "--self-test" ]; then
  printf '\n-- self-test: the scan is shown a gate that breaks the rule --\n'
  tmp="$(mktemp)"; trap 'rm -f "$tmp"' EXIT
  cat > "$tmp" <<'BROKEN'
step "a real gate" \
  python3 tools/validate.py --all

step "…and its own assertions still fire when broken" \
  python3 tools/validate.py --self-test
BROKEN
  caught="$(scan_check "$tmp" | wc -l | tr -d ' ')"
  want "$caught" "1" "a self-test left on step() is refused"
  cat > "$tmp" <<'BROKEN'
selftest "a gate that is not a self-test" \
  python3 tools/validate.py --all
BROKEN
  caught="$(scan_check "$tmp" | wc -l | tr -d ' ')"
  want "$caught" "1" "a plain gate dressed as a self-test is refused"
fi

offenders="$(scan_check tools/check.sh)"
if [ -z "$offenders" ]; then
  ok "every self-test in check.sh runs through selftest(), and nothing else does"
else
  bad "check.sh mislabels $(printf '%s\n' "$offenders" | wc -l | tr -d ' ') step(s):"
  printf '%s\n' "$offenders" | sed 's/^/        /'
fi

selftests="$(grep -c '^selftest "' tools/check.sh || true)"
if [ "$selftests" -ge 100 ]; then
  ok "$selftests self-test steps are tagged"
else
  bad "only $selftests self-test steps are tagged — check.sh had 114 when T-0763 landed"
fi

# T-1289. THE POOL MUST REACH THE SAME VERDICT AS THE SERIAL PATH, and print the same
# thing in the same order. A gate that is faster and differently right is not faster.
#
# Each run is its own shell so the harness's counters start clean; the run prints its
# transcript and then one VERDICT line, which is what the comparison reads.
_pool_run() {
  CHECK_JOBS="$1" bash -c '
    source tools/check_harness.sh
    step     "first"  sh -c "echo one"
    selftest "second" sh -c "echo two; exit 0"
    step     "third"  sh -c "echo three; exit 1"
    step     "fourth" sh -c "echo four"
    check_flush
    printf "VERDICT failed=%s steps=%s selftests=%s\n" \
      "$CHECK_FAILED" "$CHECK_STEPS" "$CHECK_SELFTESTS"
  ' 2>&1
}

serial_run="$(_pool_run 1)"
parallel_run="$(_pool_run 4)"

if [ "$serial_run" = "$parallel_run" ]; then
  ok "a four-job run prints byte-for-byte what a serial run prints, and agrees on the verdict"
else
  bad "the pool differs from the serial path:"
  diff <(printf '%s\n' "$serial_run") <(printf '%s\n' "$parallel_run") | sed 's/^/        /'
fi
want "$(printf '%s\n' "$parallel_run" | grep -o 'failed=[01]')" "failed=1" \
     "a step that exits non-zero still fails the gate under the pool"
want "$(printf '%s\n' "$parallel_run" | grep -o 'steps=[0-9]*')" "steps=4" \
     "the pool counts every step it ran"

# The order is the DECLARED order, not the order they finished in.
ordered="$(CHECK_JOBS=4 bash -c '
  source tools/check_harness.sh
  step "slow" sh -c "sleep 0.5; echo SLOW"
  step "fast" sh -c "echo FAST"
  check_flush' 2>&1)"
slow_at="$(printf '%s\n' "$ordered" | grep -n SLOW | head -1 | cut -d: -f1)"
fast_at="$(printf '%s\n' "$ordered" | grep -n FAST | head -1 | cut -d: -f1)"
if [ -n "$slow_at" ] && [ -n "$fast_at" ] && [ "$slow_at" -lt "$fast_at" ]; then
  ok "a slow step prints before the fast one declared after it, though it finished last"
else
  bad "the pool printed in completion order, not declaration order"
fi

# T-1336: A STEP THAT FAILS BESIDE A NEIGHBOUR AND PASSES ALONE.
#
# The race this answers is real and it is in this repo's own gate:
# read_census_1830.py's self-test writes a drift into the live
# data/research/.../resident_crosswalk.json to prove `--check` catches it, and puts
# it back in a `finally`. The step declared immediately BEFORE it reads that same
# file. Serially that is fine. In the pool they run together, and the check reads
# the drift the self-test is holding — a red gate on a tree that is green.
#
# The fixture below is that shape with the timing made certain instead of likely:
# a step that fails while a marker exists, beside a step that holds the marker for
# a moment and removes it.
race_dir="$(mktemp -d)"
trap 'rm -rf "$race_dir"' EXIT

raced="$(CHECK_JOBS=4 bash -c '
  source tools/check_harness.sh
  step "the neighbour that holds the tree wrong" sh -c "touch '"$race_dir"'/drift; sleep 0.4; rm -f '"$race_dir"'/drift"
  step "the step that reads it"                  sh -c "sleep 0.1; if [ -e '"$race_dir"'/drift ]; then echo DRIFT SEEN; exit 1; fi; echo quiet"
  check_flush
  printf "VERDICT failed=%s raced=%s\n" "$CHECK_FAILED" "${#CHECK_RACED_LABELS[@]}"' 2>&1)"

want "$(printf '%s\n' "$raced" | grep -o 'failed=[01]')" "failed=0" \
     "a step that fails in the pool and passes alone does NOT fail the gate"
want "$(printf '%s\n' "$raced" | grep -o 'raced=[0-9]*')" "raced=1" \
     "and it is counted as a race rather than forgotten"
if printf '%s\n' "$raced" | grep -q 'PASSED ALONE'; then
  ok "the race is named inline, with the step's own label"
else
  bad "a retried step passed silently — a race must never be quiet:"
  printf '%s\n' "$raced" | sed 's/^/        /'
fi

# THE OTHER HALF, WHICH MATTERS MORE: the retry must not turn a real failure green.
real="$(CHECK_JOBS=4 bash -c '
  source tools/check_harness.sh
  step "genuinely broken" sh -c "echo BROKEN; exit 1"
  step "fine"             sh -c "echo ok"
  check_flush
  printf "VERDICT failed=%s raced=%s\n" "$CHECK_FAILED" "${#CHECK_RACED_LABELS[@]}"' 2>&1)"
want "$(printf '%s\n' "$real" | grep -o 'failed=[01]')" "failed=1" \
     "a step that is red on a quiet tree too still fails the gate"
want "$(printf '%s\n' "$real" | grep -o 'raced=[0-9]*')" "raced=0" \
     "and it is not miscounted as a race"
want "$(printf '%s\n' "$real" | grep -c 'BROKEN')" "1" \
     "the failure's own output is printed once, not twice by the retry"

# The serial path has no pool, so it has no race to report and must not grow a field.
serial_race="$(CHECK_JOBS=1 bash -c '
  source tools/check_harness.sh
  step "fine" sh -c "echo ok"
  check_flush
  printf "raced=%s\n" "${#CHECK_RACED_LABELS[@]}"' 2>&1)"
want "$(printf '%s\n' "$serial_race" | grep -o 'raced=[0-9]*')" "raced=0" \
     "CHECK_JOBS=1 reports no races, because it cannot have one"

printf '\n%d passed, %d failed\n' "$PASS" "$FAILN"
[ "$FAILN" -eq 0 ]
