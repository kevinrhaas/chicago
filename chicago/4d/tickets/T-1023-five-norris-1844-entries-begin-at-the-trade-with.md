---
id: T-1023
title: Five Norris 1844 entries begin at the trade with no name at all — turned lines the entry-boundary rule mis-cut, and margin droppings, needing a ruling each
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-11
closed: 2026-09-13
pr: 1282
claimed_by: run 9/13/2026, 4:47:27 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T22:56:15.144Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34784722475
---

Five Norris 1844 entries begin at the trade with no name at all — turned lines the entry-boundary rule mis-cut, and margin droppings, needing a ruling each.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-1018, which refused these five: capping their name to the empty prefix
would set `surname` to `''`, and `crosswalk_norris_1844.py` skips a claim with no
surname WITHOUT SAYING SO, so five men would leave the town's reach in silence.

Each begins at the trade or mid-word, because the scanner lost the opening letters or
the entry-boundary rule cut a turned line:

    n1844_e0009  . -house Clark street (See card)
    n1844_e0276  <'ady, Dennis S. Lake Street House, 135 Lake st (Sec card)
    n1844_e0278  * '.ilhoun, John, printer, house State st. b Wash and Madison
    n1844_e0771  llageman, Christopher, grocer, N. Water st. b Clark & Dearborn
    n1844_e1637  v; Smith, Abial, printer. Dem. Olnce, res Lake Street House

Four of the five name a man and a trade plainly — a Dennis S. C-ady, John Calhoun
the printer, Christopher Hageman the grocer, Abial Smith of the Democrat's office —
and the surname is all that is damaged. e0009 is different: it has no name at all and
is probably the turned tail of the entry above it, which is a question about the
boundary rule, not about a name.

`clean_head()` already strips the left margin's specks; it cannot restore a letter
the scan never had. The second hand at `data/research/genealogytrails/text/` read the
same page from a different copy and is the evidence, exactly as `REPAIRS` uses it.

**Acceptance:**

- Each of the five is read against the second hand, or against the page image on
  T-0903's terms (word box + leaf size + two readings), and is either repaired with a
  citation or left refused with the reason stated on the claim.
- e0009 is ruled separately: whose entry is it, and does the entry-boundary rule need
  to change? If it does, that is its own ticket and this one names it.
- A repaired entry reaches `crosswalk_norris_1844.py`; the count moves and the men it
  reaches (or refuses) are named.
- T-1018's `OVERRUN_CLASSES` rows move off `empty_prefix` for whatever is repaired,
  and the self-test's empty-surname assertion still fires.
- `bash tools/check.sh` green, derived layer re-run in the same commit. No bake.
