---
id: T-0991
title: Eight cards assert an 1835 trade out of a PRE-scene printing, and T-0693's later_occupation pointer cannot hold one: blank the field, or regrade it reconstructed?
state: blocked-owner
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0872
opened: 2026-09-10
closed: null
pr: null
claimed_by: run 9/10/2026, 9:27:49 AM CT
blocked_on: Six cards carry an 1835 trade printed only in the Chicago Democrat of 26 November 1833. (a) blank the 1835 field and mint an earlier_occupation pointer, losing six trades from the town; or (b) keep the value at 'reconstructed' — which would be the first trade ever held at that grade (all 1,223 reconstructed occupations today are none_recorded), a new class of assertion in the layer a visitor reads. The two rows that were never a grading question are already repaired.
needs_bake: false
closed_at: null
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34488496242
---

T-0872's title reads "a later trade", and the population it names no longer is one. Five of
its eight — the Fergus 1839 cards — were repaired by other work between 2026-09-06 and
2026-09-10, and the audit T-0994 landed
(`python3 tools/audit_scene_window_trades.py --report`) shows what is actually left. Every
remaining row fails T-0837's rule from the OTHER side: the cited volume is about a year
BEFORE the scene, not after it.

| person | 1835 trade, at `attested` | cited | that source's `describes_date` | verdict |
|---|---|---|---|---|
| ~~`goss_o`~~ | ~~saddler~~ | Democrat, 26 Nov 1833 | 1833-11 | **REPAIRED** — dissolved_before_the_scene |
| ~~`hathaway_joshua`~~ | ~~forwarding_and_commission~~ | `hathaway_1834` (a MAP) | 1834 | **REPAIRED** — trade_read_from_a_map |
| `elston_daniel` | soap_and_candle_maker | Democrat, 26 Nov 1833 | 1833-11 | pre_scene_printing |
| `harmon_charles_l` | dry_goods_merchant | Democrat, 26 Nov 1833 | 1833-11 | firm_in_window_trade_not_printed |
| `harmon_isaac_d` | dry_goods_merchant | Democrat, 26 Nov 1833 | 1833-11 | firm_in_window_trade_not_printed |
| `jones_benjamin` | grocer | Democrat, 26 Nov 1833 | 1833-11 | pre_scene_printing |
| `kimball_walter` | dry_goods_merchant | Democrat, 26 Nov 1833 | 1833-11 | pre_scene_printing |
| `mason_matthias` | blacksmith | Democrat, 26 Nov 1833 | 1833-11 | pre_scene_printing |

The reasoning behind each verdict is written per row in
`data/research/residents/scene_window_trade_audit.json`, out of the newspaper register's own
compilation of the corpus — for each firm, the last issue that prints it.

**THE TWO ROWS THAT WERE NEVER A GRADING QUESTION ARE REPAIRED (PR below).** Neither needed
a rule about carry-forward, because neither had a trade to carry:

  * `goss_o` — the Chicago American of 8 June 1835 prints the DISSOLUTION of Goss & Cobb over
    copy dated 18 February 1835, and the 13 June issue reprints it with this man's own
    signature readable. The newspaper register already read `business_goss_cobb` as
    `present_at_scene_date: false`, exclusion `contradicted_before_scene_date`. The trade was
    not undated by the corpus, it was CONTRADICTED by it, four and a half months before the
    scene date. Now `none_recorded` at `reconstructed`; the 1833 saddlery keeps its place in
    the structures layer and the register, dated to the years that print it.
  * `hathaway_joshua` — the trade's only citation was `hathaway_1834`, which this repository's
    own inspection at native resolution records as a pure cadastral lot plat carrying no
    trades at all. `forwarding_and_commission` was read IN, not read off. No tier can hold a
    figure no source states, so this is a repair and not a grade. Now `none_recorded` at
    `reconstructed`. The cartouche's evidence that he SURVEYED is left deliberately unspent:
    reading `surveyor` off an authorship line, out of a sheet whose describes_date is 1834,
    is the same move in the other direction.

**WHY THE PARENT'S REMEDY CANNOT BE EXECUTED ON THE SIX THAT REMAIN.** T-0872 says an
unrepairable row is "moved to the `occupation.later_occupation` pointer T-0693 mints, leaving
the 1835 field as `none_recorded`". That pointer is derived, wholly and only, from the
record's own `directories` block — a directory of 1839, 1843 or 1844 — and it says in its own
note "a trade is recorded for {year}". There is nowhere in it to put a trade printed in
November 1833, and writing one there would assert the exact back-projection T-0693 exists to
refuse, in reverse. The parent's second arm has no mechanism behind it for this population.

**THE QUESTION, and it is one rule over one cohort of six.** All six are the same shape: a
firm printed in the Chicago Democrat of 26 November 1833, a man printed inside the 1835
window, and no printing that puts the two together in the scene year.

  a. **Blank and point.** 1835 field to `none_recorded`, and mint the symmetric
     `occupation.earlier_occupation` pointer carrying the pre-scene trade and its year.
     Faithful to the parent's letter and to T-0837's rule. It takes six trades out of the
     town's 1835 layer — a blacksmith, two dry-goods houses, a grocer, a soap and candle
     manufactory — and out of everything downstream that reads `occupation.value`. It also
     needs a new key declared to `tools/measure_layer_reads.py`, which refuses an unread
     figure.

  b. **Regrade and say so.** Keep the value, move `attested` to `reconstructed`, keep the
     pre-scene issue cited, and write the carry-forward and its last-printed date into the
     note. `reconstructed` is this dataset's word for a figure the reconstruction supplies
     rather than a source, and `synthesize_resident_research.py`'s own overwrite guard
     already treats a `reconstructed` trade as an empty field. The town keeps its blacksmith
     and the card stops claiming a printing it does not have.

**WHY THIS IS NARROW ENOUGH TO BE THE OWNER'S, and why a run stopped rather than choosing.**
`tickets/README.md` keeps `blocked-owner` for "a decision that changes what the project is",
and answer (b) is one, measurably: all 1,357 cards carry an occupation block — 1,223 at
`reconstructed`, 125 `attested`, 9 `inferred` — and **not one** of the 1,223 holds a trade.
Every single one has the value `none_recorded`. `reconstructed` has so far meant *the
reconstruction says there is nothing here*. Answer (b) would make it also mean *the
reconstruction supplies a trade the sources do not print for this year*, and that is a new
class of assertion in the layer a visitor reads, established on six cards and precedent for
the rest. AGENTS.md § RECONSTRUCTED IS A TIER argues for exactly that widening and the owner
has argued against hesitancy; that is why (b) is likely right and still not a run's to
declare. Answer (a) needs no precedent and costs the town six trades.

Two facts that ought to weigh on the answer, found while repairing the other two:
`jones_benjamin`'s later readings in the same corpus print `forwarding_and_commission` (21
January to 16 July 1834), not `grocer`; `kimball_walter`'s print `grocer` (to 3 December
1834), not `dry_goods_merchant`. For those two, (b) would carry forward a value the corpus's
own later readings already moved off — so a third answer is available for them alone: take
the LAST trade the corpus prints for the man rather than the first.

**Acceptance:** the owner's rule is recorded, and all six remaining rows leave
`tools/audit_scene_window_trades.py --report` under it. The gate T-0994 wired into
`check.sh` is what proves it: the ledger may only fall, and it has fallen from 8 to 6.

**Links:** [[T-0872]] (the parent) · [[T-0994]] (the audit and the one row the corpus
decided) · [[T-0837]] (the write gate) · [[T-0693]] (the later-trade pointer).
