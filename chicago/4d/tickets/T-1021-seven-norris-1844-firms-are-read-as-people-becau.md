---
id: T-1021
title: Seven Norris 1844 firms are read as people because the scanner set their ampersand as '<fc', '6c' or 'it', and the firm test never fired
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-11
closed: 2026-09-13
pr: 1276
claimed_by: run 9/13/2026, 8:58:49 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T02:40:37.077Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34797498709
---

Seven Norris 1844 firms are read as people because the scanner set their ampersand as '<fc', '6c' or 'it', and the firm test never fired.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-1018, which refused these rather than damage them.

`FIRM` decides firm-or-person on the leading name run, and it needs a real `&`.
archive.org sets this volume's ampersand as `<fc`, `6c` or `it` in seven entries, so
each reads as a man whose surname is the whole firm:

    n1844_e0063  Ballentine <fc Sherman, dry goods and groceries, 122 Lake street
    n1844_e0168  Bowen 6c Cole, dry goods and groceries, 66 Lake street
    n1844_e0180  Bracken it Tuller, dry goods and groceries, 161 Lake st
    n1844_e0439  Crauer <fc Sanser, builders, Clark st. b Randolph and Michigan sts
    n1844_e0719  Gould it Dodge, ball alley and grocery, South Water st. b State and Dearborn
    n1844_e0787  Hamilton <fc White, dry goods and grocery store, 139 Lake st
    n1844_e1629  Skinner 6c .Smith, Mansion House. 6G Lake street

They are `kind: person` in the reading and the crosswalk's firm filter — which exists
so a company is never matched to a resident of 1835 — never sees them. Seven Lake and
Water street TRADES, with printed addresses, are also filed under a man's name.

**THE TRAP.** `it` is an English word and `6c` is how this scanner sets `&c.`
(`Surdam. S. J. stoves, &c. 132 Lake st`). A loose rule would weld `stoves it` or
`&c.` into a partnership. T-1018 gates its refusal on the span being EXACTLY
`Name <conj> Name`, three tokens, which is narrow enough to name but is a REFUSAL,
not a reading — this ticket has to decide what the entries actually are.

**Acceptance:**

- Each of the seven is ruled firm or person on its own printed line, and the ruling
  cites the page. The second hand (`data/research/genealogytrails/text/`) reads the
  same seven and is quoted where it disagrees.
- Whatever mechanism lands, `&c.` and the word `it` are shown NOT to be swept up:
  enumerate every entry the new rule touches, before and after.
- `crosswalk_norris_1844.py` counts before and after; any 1835 resident who stops
  matching because a firm is now correctly a firm is NAMED, and that is a gain.
- T-1018's `OVERRUN_CLASSES` rows for these seven move off `firm_conj`, and
  `read_norris_1844.py --self-test` stays green.
- `bash tools/check.sh` green, and the derived layer re-run (`node tools/rederive.mjs
  --run`) in the same commit. No bake.
