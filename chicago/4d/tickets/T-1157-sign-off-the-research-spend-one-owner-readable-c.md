---
id: T-1157
title: Sign off the research spend: one owner-readable coverage report over residents, households, plural roles, business staff and every home, work and other significant location, and the gate that lets reconstruction begin
state: done
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-18
pr: 1440
claimed_by: run 9/18/2026, 12:27:06 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T06:08:33.402Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35310590693
---

Sign off the research spend. This is the owner's "confirm Completed Research" step (2026-09-17):
*"confirm that all of the research has been spent successfully on building residents households
trades occupations (… in some cases they can have more than 1, like … Dan Elston sold soap and
candles and was also school inspector) and also the business structures and where everyone works
and lives, their primary and any other locations they were significantly involved in."*

It follows the standing spend tickets — T-1155, T-1121, T-1136, T-1129, T-0856, T-0662, T-1145,
T-1146, T-1108, T-1147 and the convergence pass T-1144 — and does not re-decide any of them. It is
the receipt that they did what they say, read from the tree, and it is the ENTRY CONDITION for
the 1835 TOWN ANALYSIS band (T-1158 onward): no reconstruction ticket may be claimed while this
one is open, because a reconstruction that inherits an unspent attested fact will invent what a
source already says.

**What "spent" means here, checked per axis** (every figure re-derived by a tool, never typed):

1. **Residents and households.** Every research unit dispositioned `asserted` in the T-1143
   ledger (`data/research/ledger/` — `measure_research_spend.py --ledger-build`) resolves to a
   structured field on a person or household card; zero `unresolved` rows remain whose owning
   ticket is closed; the resident derivations (synthesis, documented mint, letter-list mint) are
   drift-zero (T-1144 acceptance 1).
2. **Trades, professions and offices — plural and dated.** `roles[]` (T-1145) is canonical.
   Print the reconciliation table: how many persons carry 2+ roles, how many roles reach
   1835-07-01, how many are dated pre-scene or later-only. Daniel Elston is the fixture and the
   report shows him: soap and candle manufacture (1833-34, in window), provisions/packing, and
   school inspector / brickmaker as dated later roles, none of the later ones claiming 1 July 1835.
3. **Business structures and who works where.** Every business in the newspaper register and
   the business layer names its proprietors/partners (T-1147.2); every person with an in-window
   trade either links to a business/workplace or carries the printed reason none is resolvable.
   Print the three location-limit counts (structure / street-only / unplaceable) before and after
   the spend, from the tool, and name every business whose limit moved and on what source.
4. **Primary and other significant locations.** For each person: `lives_at` (plural, dated),
   `works_at` (plural, dated), and OTHER places the research ties them to — a civic office held
   (the council house, the post office, the land office, the court), a church membership, an
   agency (`data/reconstruction/1835_agencies.json`), a land purchase (`1835_land_sales_by_tract`),
   a tavern kept, a school taught. Report how many persons carry each kind and how many attested
   location facts in research prose have NO structured target — that number must be zero or every
   remainder named with its reason.
5. **Withheld is legible.** Every refused / later_only / outside_chicago / aggregate_only unit
   keeps its stated reason on the ledger and, where it touches a card, on the card (T-1146.5).

**Acceptance:**

- `tools/report_research_signoff.py --build` writes `docs/RESEARCH/research-signoff-2026-09.md`
  with the five axes above as tables, each row naming the command that reproduces it; `--check`
  re-derives byte-for-byte and is wired into `tools/check.sh` with a mutation self-test.
- The report ends with an explicit **GO / NO-GO for reconstruction** line and, on NO-GO, the
  ticket ids that must close first. On GO, `tickets/QUEUE.md`'s band 2 header comment is updated
  to say the entry condition is met (the only queue edit this ticket makes).
- The people view / evidence panel shows a person's plural roles, plural locations and "other
  significant locations" as one dated timeline (T-1145.5 + T-1147.5 verified here, not rebuilt).
- Zero attested or inferred fact stranded solely in prose, re-measured; zero dead target.

**Stop condition:** the sign-off report is committed, green, and says GO — or says NO-GO with
the exact blockers, in which case this ticket stays open and the band below it waits.

**Links:** T-1143 · T-1144 · T-1145 · T-1146 · T-1147 · T-1155 · T-1121 · T-1136 · T-1129 ·
T-0856 · T-0662 · T-1108 · `docs/RESEARCH/research-spend-ledger-2026-09-15.md` ·
`docs/RESEARCH/residents-households-summary-2026-09.md`.


## T-1144 AND T-1241 COULD NOT BE FOLDED — THEY RUN IN THIS PASS (owner's tightening, 2026-09-17)

Three tickets were standing at the end of the research spend and all three are the same act —
prove the layer converged, then say so:

* **T-1144** — converge the resident layer: zero synthesis and mint drift, no false Chicago.
  **Could NOT be folded**: unresolved research units name it BY ID as the work they wait on,
  and `research_spend_ledger.py` refuses a unit deferred to a closed ticket.
* **T-1241** — run the T-1143 ledger over the final resident, household, business and
  structure layers and publish the closing figures. **This one could NOT be folded and stays
  a ticket of its own**: 748 unresolved research units defer to T-1147, a split parent counts
  as live only while a child is open, and T-1241 is now the last open child. Folding it made
  all 748 defer to finished work and `measure_research_spend.py --check` failed on every one.
  It is not a separate expedition — run it in THIS pass, as this report's evidence section.
* **T-1157** (this one) — one owner-readable coverage report, and the GO that opens bands 3-5.

A convergence nobody reports is not finished, and a report on an unconverged layer is not
true, so they cannot happen apart. Running them as three tickets means three runs each
re-establishing the same tree and re-reading the same ledgers.

**One run, and it ends in a signature.** The drift checks and the ledger pass are the EVIDENCE
SECTION of the report, not their own deliverables.

**Good, not great — and this is the ticket that most needs it, because it is the gate the city
is waiting behind.** The report answers, per layer: what is attested, what is inferred, what
is still unclassified, and what is knowingly left as a gap. **A stated gap is a finished
answer.** Zero unclassified is NOT the bar and never was — the queue's own header says so:
"zero unclassified research does not mean forcing uncertain people or locations into 1835."
If a class cannot be closed, name it, say what it would take, and sign anyway. The GO is a
judgement about whether reconstruction can start on what is known, not a certificate that
nothing is unknown.
