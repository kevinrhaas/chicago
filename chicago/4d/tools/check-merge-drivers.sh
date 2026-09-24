#!/usr/bin/env bash
# ARE THE MERGE DRIVERS REGISTERED IN THIS CLONE? (T-1548)
#
# /.gitattributes routes changelog.js and dev-smoke-state.json through custom
# drivers, and it already says what happens when they are not registered: "git
# falls back to the ordinary text merge and you get conflict markers — the old
# behaviour, never something worse."
#
# Never something worse is true and it is not free. MEASURED 2026-09-24: in a
# container where no driver was registered, four branches in one session each hit
# the changelog conflict and each was resolved BY HAND — the identical edit every
# time, and exactly the edit tools/merge-changelog.mjs performs. One of the four
# was resolved wrongly on the first attempt (the shared closing `] },` was left
# with the wrong entry) and had to be redone. That is the cost the note calls the
# old behaviour, and it is paid per branch, silently, by whoever merges.
#
# Registration is a one-line command and cannot be committed — it lives in
# .git/config, so a fresh clone or a container rebuild starts without it and
# nothing says so. This step is what says so.
#
# It is a WARNING and not a failure by default, because an unregistered driver
# cannot corrupt anything: it degrades to conflict markers, which stop you. Set
# CHECK_DRIVERS_STRICT=1 to make it fail instead.
set -u

missing=()
for d in queue changelog generated smokestate; do
  if [ -z "$(git config --get "merge.$d.driver" || true)" ]; then
    missing+=("merge.$d.driver")
  fi
done

if [ ${#missing[@]} -eq 0 ]; then
  echo "merge drivers OK — all four registered in this clone"
  exit 0
fi

echo "MERGE DRIVERS NOT REGISTERED in this clone: ${missing[*]}"
echo
echo "  /.gitattributes routes changelog.js through merge=changelog. Unregistered,"
echo "  every branch that ships a changelog entry conflicts and is resolved by hand"
echo "  — the same edit merge-changelog.mjs makes for free. Four such resolutions"
echo "  were paid in one session on 2026-09-24."
echo
echo "  Register them once per clone (it writes .git/config, nothing to commit):"
echo "      bash chicago/4d/tools/setup-merge-drivers.sh"
echo
if [ "${CHECK_DRIVERS_STRICT:-0}" = "1" ]; then
  echo "CHECK_DRIVERS_STRICT=1 — failing."
  exit 1
fi
echo "(warning only; set CHECK_DRIVERS_STRICT=1 to make this a failure)"
exit 0
