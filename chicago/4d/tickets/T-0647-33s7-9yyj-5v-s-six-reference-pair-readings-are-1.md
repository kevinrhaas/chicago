---
id: T-0647
title: 33S7-9YYJ-5V's six 'reference pair' readings are 11 and the digit key from a sheet that closes says they are 4
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: 868
claimed_by: run 9/5/2026, 4:23:17 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T10:20:36.055Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33957730780
---

33S7-9YYJ-5V's six 'reference pair' readings are 11 and the digit key from a sheet that closes says they are 4.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**The finding, from T-0648.** `33S7-9YYJ-5V` reads a matched pair of parallel slashes as **11** on its
lines 2, 3, 4, 6, 9 and 24, and calls line 2 "the sheet's reference pair". Its TOTAL column does not
close, and nothing checked it: 5V's printed footing is illegible.

**33S7-9YYJ-24 is the check nobody had used.** It is the same enumerator — S. W. Sherman — and its
TOTAL column CLOSES against its own printed 201 over 31 lines, so every glyph on it is labelled by
arithmetic rather than by opinion. Its line 6 is a matched pair of parallel slashes and its committed
value is **4**. Its line 8 is three slashes — a 1 then that same pair — and its committed value is
**14**. Its line 10 is two of the small 2-curls and its committed value is 22. That is a digit key, and
it is now written into `pages/33S7-9YYJ-6Q.json` under `total_column.digit_key`.

**What this ticket does.** Re-read 5V's lines 2, 3, 4, 6, 9 and 24 against that key and either correct
them to 4 or state, from the ink, why 5V's pairs are a different construction from 24's. If they
correct, 5V's committed sum moves from 126 to 84 and its `records[]`, `total_column` and the
changelog's account of it all have to move with it. T-0648 deliberately did not touch 5V: it is
another sheet and another demonstration.

**Check the division before extending this.** The key is measured on S. W. Sherman's hand. `33S7-9YYJ-8D`
(changelog v486) reads six two-stroke figures as 11 on a spacing argument and records no division in its
page file; whether 24's key binds that sheet is a question this ticket should answer rather than assume.
