---
id: T-0012
title: Ship the 16-bit ground the script already computes
state: split
epic: RENDERING
requested_by: loop
seen: true
effort: M
legacy_id: R-W6(b)
parent: null
opened: 2026-08-17
closed: 2026-08-22
pr: null
claimed_by: run 8/22/2026, 10:17:39 PM CT
blocked_on: null
needs_bake: true
---

The 16-bit ground exists in the bake script and not in the file a visitor loads — the
committed derivative still quantises POSITION to 14 bits (306 mm lattice, held down only by
the load-time conform). Deep history: § R-W6(b) (~5403). Needs one bake, or the owner's word
to hand-run it.

**Acceptance:** shipped terrain GLB carries 16-bit POSITION; check_published's derivative
report shows it; worst error ≤ 13 mm.

---

**SPLIT 2026-08-23, and the reason is a correction to this ticket's own premise.** Its first
sentence was no longer true when it was picked up: the committed derivative already carries
**16-bit** POSITION — regenerating it from the master at 16 bits reproduces the committed
file md5 for md5, at 14 bits it does not — so the 16-bit ground reached the site in a
nightly bake and nothing in the repository could say it had. Its third clause (worst error
≤ 13 mm) is red at **77.1 mm**, but not for the reason written here: the bit depth is
unchanged and the GROUND changed, extended east into slopes far steeper than the ones R-W6
measured 12.9 mm against.

Two findings, two demonstrations, two tickets: **T-0151** asserts the bit depth so neither
silence can recur, and **T-0152** owns the drawn-surface error and R-W6's own stated reopen
condition for the skirt split.

