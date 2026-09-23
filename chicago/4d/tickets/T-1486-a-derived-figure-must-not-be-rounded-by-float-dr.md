---
id: T-1486
title: A derived figure must not be rounded by float drift: sweep the 31 remaining round(sum(...)) sites
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-20
closed: 2026-09-20
pr: 1593
claimed_by: run 9/20/2026, 4:30:26 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T22:19:53.025Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35538771732
---

Two gated writers flapped their committed output between machines this week, and both for
the same reason. `sum()` accumulates left to right and drifts a few parts in 10^15. That
is nothing on a height or an easting — until the true value sits exactly on the rounding
boundary, at which point the drift, and not the measurement, decides the last digit
printed.

**Where it bit.** Found working PR #1585 (T-1477), whose gate was red on two steps that
had nothing to do with its diff:

* `generate_plat_lots.ground_reading` — the School Section's blocks 95, 118 and 119 are
  each perfectly flat at 0.885 m. `min` and `max` rounded that up to 0.89; the mean of
  418 identical samples accumulated to 0.8849999999999949 and rounded DOWN to 0.88. The
  committed record printed **a mean outside its own min and max**, which rounding being
  monotonic says is impossible, and no assertion caught it.
* `derive_hay_limits.programme_blocks` — Kinzie's Addition is platted in feet, so a
  quarter of four corners lands on an exact half-centimetre; **twenty** of these
  centroids sit precisely on the 2 dp boundary. Four of them read one value on the
  loop's machine and the other on CI's, so the committed file was re-derived back and
  forth between two "correct" versions, each red on the other machine. One branch
  committed a re-derivation of it believing it was clearing a stale fossil from dev; it
  was not stale, it was flapping.

Both were fixed in that PR with `math.fsum`, which is correctly rounded and
order-independent, plus a refusal in `ground_reading` for a mean outside its own
min-max. Neither fix moved a committed byte — the arithmetic was wrong, not the data.

**What is left.** 31 further `round(sum(...))` sites in `tools/*.py` carry the same
pattern (`grep -rn "round(sum(" tools/*.py`). Most will never land on a boundary. The
point is not to guess which: the two that bit were both found by a red gate rather than
by reading, and a figure whose last digit is decided by accumulation order is not a
measurement.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. Every `round(sum(...))` site in `tools/*.py` that divides by a count is either
   converted to `math.fsum` or carries a one-line note saying why the boundary cannot be
   reached there. The count in this ticket's title is checked at the start, not assumed.
2. A gate step that measures how close each converted figure runs to its rounding
   boundary, so the next one is found by measurement and not by a red CI run on someone
   else's branch. A figure landing within one part in 10^12 of a boundary is reported.
3. Any site that also publishes a min and a max alongside the mean asserts the three
   against each other, as `ground_reading` now does — and the assertion is
   mutation-tested by restoring `sum()` and watching it fire.
4. No committed derived file changes value. If one does, that is a finding to be
   explained on the PR, not a re-derivation to be waved through: the last digit moving
   means the old one was decided by drift.
5. `./tools/check.sh` green, and `tools/writer_inventory.json` untouched by this work —
   this is an arithmetic fix, not a placement pass.

**Not this ticket.** The tie-breaking *rule* itself. A true half like 888.695 has no exact
binary form, so which way `round()` breaks the tie is decided by which double is nearest.
`fsum` makes that decision reproducible everywhere, which is what a gate needs; whether
the project would rather round half away from zero on the exact decimal is a separate
question and nothing currently turns on it.

---

## MEASURED, 2026-09-20 — the cause was the INTERPRETER, not only the order

The ticket says the drift is accumulation order, and the fix it asked for is right. But
the drift would not reproduce here at all, on any sample set: `sum()` and `math.fsum`
agreed to the last bit over 418 identical samples, over 4,096 samples tuned onto the
boundary, and over 20,000 randomised clusters. The reason is that **CPython 3.12 gave
`sum()` Neumaier compensation for float inputs**. This runner is 3.12.3.
`.github/workflows/chicago-4d-check.yml` pins **3.11**, which still accumulates left to
right, uncompensated.

Replaying the pre-3.12 accumulation — `functools.reduce(operator.add, values, 0.0)` —
over 418 samples of a flat 0.885 m reproduces the ticket's own figure exactly:

    naive mean : 0.8849999999999949 -> 0.88
    fsum  mean : 0.885              -> 0.89
    min / max  : 0.89   0.89

So the two writers did not flap because one machine added in a different ORDER. They
flapped because one machine's `sum()` was compensated and the other's was not, and a
re-derivation therefore looked correct where it ran and stale where it did not. That is
also why the committed files were red on somebody else's branch: CI is the 3.11 side.

Three things follow, and all three are in this PR:

* `math.fsum` is still the right fix and is now the WHOLE fix — it is correctly rounded
  on every version, so the pin stops mattering for these figures.
* The mutation test in acceptance 3 cannot use a bare `sum()` on this runner, because a
  bare `sum()` no longer drifts here. It restores the *uncompensated* accumulation the
  fix replaced, which is what CI runs, and the refusal fires.
* The gate prints which summation the running interpreter has, because a gate that is
  green only because its interpreter hides the fault is not a green gate.

### Acceptance, answered

1. **33 sites, not 31** — and the count was the least of it. An AST census found **five
   more** that `grep -rn "round(sum("` cannot see, because they put `round(` and `sum(`
   on different lines. 38 sites converted, 2 annotated (`# exact-sum-ok:`): a share of
   an integer row count, and the all-zero fallback described below.
2. `tools/check_exact_sums.py` is the gate step. It re-adds the committed aggregates
   whose components are committed beside them, checks each still equals the figure its
   generator wrote, and reports any figure within one part in 10^12 of its boundary.
   Five today; the closest runs at 0.18 of a rounding step, none is near.
3. The min-max-mean refusal moved into `tools/exact_sums.py` and is now shared by four
   sites that publish the three together (the ground reading, the corridor cut width,
   the shoreline band spread, the Wabansia corridor). It is mutation-tested as above.
4. **No committed derived file changed value, and no committed byte moved.** Every
   writer touched was re-run and `git status` is clean. One site needed care to keep it
   that way: `math.fsum` always returns a FLOAT, so an acreage column with nothing in it
   would have newly serialised as `0.0` where the committed file carries `0`. An
   all-zero column has no boundary to drift across, so it keeps its exact arithmetic —
   `_acres()` in `sort_land_sales_onto_tracts.py`, documented there.
5. `./tools/check.sh` green; `tools/writer_inventory.json` untouched.

### Left standing, deliberately

130 further sites take a mean as `sum(xs) / len(xs)` into a VARIABLE and round it
somewhere else. Two of them sat in the same dict as a converted site and were fixed with
it; the rest are mostly centroids that never reach a committed figure, and converting
them blind would move geometry, which acceptance 4 forbids. The census only sees
`round(...)` over `sum(...)`, so it does not catch that shape — a finding for whoever
takes the next arithmetic pass, recorded here rather than as a new ticket.
