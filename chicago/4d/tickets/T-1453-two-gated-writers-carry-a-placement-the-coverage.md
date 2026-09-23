---
id: T-1453
title: Two gated writers carry a placement the coverage audit does not count, so it says 208 measured and accounts for 206 — and the one whose ordering is unrecorded cost three gate cycles today
state: done
epic: META
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-20
closed: 2026-09-20
pr: 1606
claimed_by: run 9/20/2026, 8:47:51 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T02:49:28.954Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35551917772
---

Two gated writers carry a placement the coverage audit does not count, so it says 208 measured and accounts for 206 — and the one whose ordering is unrecorded cost three gate cycles today.

`tools/audit_manifest_coverage.mjs` prints, and it is green today:

```
manifest coverage: OK — 208 gated tool(s), every one measured.
  152 in the manifest · 17 measured to reproduce and not yet placed
  15 cannot rebuild, each with its number · 22 write nothing
```

**152 + 17 + 15 + 22 = 206.** It claims 208. Two rows in
`tools/writer_inventory.json` carry `placement: "reproduces"`, which is not one of
the four the audit buckets, so they are counted by no line of the summary and
flagged by nothing:

| tool | placement | has a `placed` reason |
|---|---|---|
| `complete_inwindow_trades.py` | `reproduces` | no |
| `build_trade_table_1839.py` | `reproduces` | no |

**It is a conflation of the outcome with the placement, and the audit's own error text
is where it comes from.** When a tool has no row, the audit tells you how to measure it
and what each result means:

```
  wrote its own outputs and changed no committed byte  -> reproduces
  changed a committed byte                             -> not_derivable, WITH THE NUMBER
```

Two of those four outcomes are also placement values and two are not. *Reproduces* is
an outcome; the placement that follows from it is **`pending`** — "measured to reproduce
and not yet placed" — and every one of the 17 real `pending` rows carries a `placed`
field saying why it is not in the manifest yet. These two carry none, because whoever
wrote them wrote the outcome word into the placement field and the audit had no reason
to argue.

**WHAT IT COSTS, measured on this repository today.** `complete_inwindow_trades.py` is
gated with `--check`, writes `trade_census_1835_crosswalk.json` and
`inwindow_trade_workplaces.json`, and manifest steps read both. Nothing sequences it and
nothing records where it goes. Driving PR #1560 to green I burned **three gate cycles**
rediscovering that by hand:

1. Rebuilt the town model first, reading T-1179's "rebuild the town model before the
   stages that draw from it" as a rule about the model. The model draws too —
   `trade_census_1835.py` writes the crosswalk it reads — so it went stale against its
   own input.
2. Ran `rederive.mjs --run`, then this tool. Running it *after* the manifest staled every
   step that reads what it writes: the roof programme went red.
3. Ran this tool, then the manifest, then `reprogramme_roofs_1835.py`. Green.

That order is not written down anywhere. `reprogramme_roofs_1835.py` at least says why it
is unplaced — *"this tool reads the order book and the lodging model, both of which later
reconstruction stages write, so its place in the manifest's order is that pass's to
settle"* — which is exactly the sentence a run needs and exactly what the two `reproduces`
rows are missing.

**This is T-1302's residue, not a new hole.** That ticket built this gate and closed the
big gap; the manifest's own preamble records why (`_a_writer_belongs_here`: four hand-fixes
in one night). The mechanism is right. Two rows drifted past its vocabulary, and because an
unknown placement is silently uncounted rather than refused, the gate reports OK while
under-reporting itself by two.

**Acceptance:**

- **The audit refuses a placement it does not know.** An unrecognised value is a failure
  naming the tool, the value and the four that are legal — not a row that vanishes from
  every count. This is the fix; the two rows below are the instances it would have caught.
- **The summary's arithmetic is asserted, not assembled.** The buckets must sum to the
  total the same line prints, and a disagreement is red. "208 measured" and four numbers
  adding to 206 is the whole bug, and it is the kind of thing a reader is entitled to
  trust at a glance.
- `complete_inwindow_trades.py` and `build_trade_table_1839.py` are re-placed as `pending`
  — their measurements stand and are not re-taken — and each gains a `placed` field in the
  form the other seventeen use.
- **`complete_inwindow_trades.py`'s `placed` field records the ordering that three red
  gates paid for**: it writes the trade-census crosswalk and the in-window trade
  workplaces, manifest steps read both, so it runs BEFORE `rederive.mjs --run` and never
  after. A future run reads that instead of rediscovering it.
- The audit's guidance text stops handing back a word that is not a placement: the outcome
  *reproduces* maps to the placement `pending`, and the message says so.

**Stop condition:** every gated writer is counted by exactly one bucket, the buckets sum
to the total printed beside them, and no tool sits outside the manifest without a written
reason a run can act on.

**Links:** T-1302 (built this gate; PR #1470) · T-1179 (the ordering finding) · T-1447 (a
figure nobody measured) · PR #1560 · `tools/derived_manifest.json` `_a_writer_belongs_here`.

**Re-measured 2026-09-20, and the gap has GROWN.** `audit_manifest_coverage.mjs` now reports
**218 gated tools** and accounts for 215 of them: 152 in the manifest, 25 measured and not
yet placed, 15 that cannot rebuild, 23 that write nothing. Three are unaccounted, up from
the two in this ticket's title. The audit still says `OK`, which is the fault — it prints a
total and a breakdown that do not reconcile and passes anyway. The sum is the assertion.

**The placement gap is the expensive half.** Three gated writers outside the manifest bit in
one evening: `complete_inwindow_trades.py` must run BEFORE `rederive.mjs --run` and
`reprogramme_roofs_1835.py` after it, with nothing sequencing either; and
`employment_coverage_1835.py` was left stale by T-1463's re-cut, so the gate read fifteen
people carrying no employment answer and the red was found by CI rather than by the
manifest. A fourth ordering fault sits in the manifest itself — step 154,
`rebuild_closing_set.py --build`, refuses unless the published mirror exists, and
`rederive.mjs --run` does not publish, so a bare manifest run cannot complete.
