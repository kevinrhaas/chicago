---
id: T-0808
title: The owner's three rulings — the site budget, kinship, and the planform of record at the forks — carried into the tickets that asked
state: withdrawn
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: stale: #836 and #839 merged, T-0685 done, the plat corrected — the three rulings reached their tickets
needs_bake: false
closed_at: 2026-09-10T04:20:10.919Z
claimed_run: null
---

Three PRs were parked on questions only the owner could answer — the only three in a
21-PR backlog genuinely blocked on a decision. **All three were answered on 2026-09-05,
in session, and the answers are quoted below.** This ticket is no longer a question; it
is the work of carrying each ruling into the ticket that asked it, so no run re-asks.

**With these three answered, nothing in the backlog is blocked on the owner.** The
drain ends at zero open PRs, not two.

---

## 1. The published tree at its 32 MB ceiling — T-0730 / T-0722

**RULED: keep the 32 MB budget, land [#836](https://github.com/kevinrhaas/custom/pull/836),
and rank T-0727 next.**

The question offered three shapes — raise `SITE_BUDGET_MB`, stop publishing
`changelog.js` twice, or ship only the newest N entries to the site. **#836 had already
built the second**, and it is the one taken: `js/changelog.js` and `walk/js/changelog.js`
were the same **1.31 MB** under two published URLs, both paths contracts, neither wrong.
One now holds the file and the other re-exports it. **31.999 MB → 30.69 MB**, and the
changelog's growth against the payload is halved.

The budget is NOT raised, and the reason is on the record in #836's own
`docs/SITE-BUDGET.md`: 32 is this project's own number — **GitHub's documented Pages
limit is 1 GB**, and the gate's stated defence (Pages cannot serve LFS objects) is not a
size argument at all. It stays because it works: it is what turned up a 1.31 MB verbatim
duplicate that had been growing at twice the rate of the record. A budget nobody can hit
finds nothing.

**Consequences to carry:**
- #836's 90 %-of-budget warning is the part that matters operationally — the next PR gets
  warned instead of refused. Keep it.
- **T-0727 is ranked immediately after this band** — *budget the walkthrough's boot
  payload, which is what a visitor actually downloads*. That is the number worth
  defending; 30.69 MB of repository is not, and 25.3 MB of it is the town's own record
  with every directory read by something the visitor uses. The run that lands #836 places
  T-0727's queue line under this instruction; it cannot be placed sooner because the
  ticket does not exist on `dev` until #836 merges.
- T-0728 (minify the mirror's JSON, a measured further 1.99 MB) is NOT ranked here. It
  carries a question about what the mirror is for, so it waits behind T-0727.
- T-0730 is answered by the same ruling and closes with it; #841 unblocks once #836 lands.

---

## 2. Kinship between households — T-0787 (the kin ticket, restamped)

**RULED: yes — model it, as the household-level `kin[]` block
[#839](https://github.com/kevinrhaas/custom/pull/839) demonstrates.**

The measurement that decided it is T-0734's: **14 of 1,404 people carry any stated
relationship to anybody at all**, while the corpus already prints many more — the St Cyr
marriage entries, the Fergus death notices that name a surviving widow, the 1840 census
households the bridge has matched. Every one of those lands as free prose that no
question can follow, and T-0734's spend cannot be done well until there is somewhere for
them to go.

**The shape is #839's, and its two rules are the reason it is acceptable rather than an
invention:** a `kin[]` row is an ordinary graded claim block (so `walk_attested` checks
it like any other reading), a relation is legal **only against its declared inverses**,
and **every row must be reciprocal** — asymmetric relations deliberately not declared.
Enforced in `validate.py` with its own self-test cases, not trusted.

**Consequences to carry:**
- #839 is now reviewed on its merits, not held. It lands in drain lap 1 (T-0805)
  **immediately after #822**, which writes the Hurlbut note onto the same two Kinzie
  records — they touch the same household files and the note is what the `kin[]` row
  cites. #822 first, #839 second, adjacent, never split across laps.
- The kin ticket's id collides with dev's own T-0787 (the Wright 1834 sheet registration,
  landed in #895) and is restamped by lap 1 regardless of this ruling.
- T-0734 is unblocked and should be re-read for what it can now spend.

---

## 3. The planform of record at Wolf Point — T-0685

**RULED: Wright 1834 stays the planform of record. Nothing moves.**

The measurement is not in doubt and is not what was ruled against. The Thompson plat
DID carry a fit — 22 street-corridor crossings, **RMS 4.9 m, max 7.8 m**, four control
points shared with Wright's own — which is four times tighter than Wright 1834's declared
17.5 m. And the disagreement is structural rather than noise: the North Branch's east
bank **27–43 m west**, its west bank **35–60 m west**, the channel **88–93 m** against
Wright's 66–83, both banks displaced together over 240 m of reach, with the georeference
able to account for about **3 m** of it.

The ruling takes the argument `docs/RESEARCH/thompson_forks_georeference.md` § 6 makes
for the status quo: **Wright is a survey OF the river, four years nearer the scene, and
the river is its subject.** Thompson's river is a boundary on a plat of lots, drawn
freehand — the stroke visibly wavers where a surveyed line would not — surviving as a
Canal Commissioners' working copy dated to at least 1836, so the line may be a copyist's.
`thompson_plat_1830.json` already says to read that sheet for its figures and never to
trace it for geometry, and this ruling leaves that instruction standing.

**Consequences to carry — and the second one is not optional:**
- **#886 is mergeable as it stands.** Its acceptance 5 was *nothing moves*, and nothing
  did: it commits `thompson_1830_gcps.json` and `thompson_1830_forks_banks.json`
  **beside** the Wright planform, each with its source, and overwrites no waterline. The
  ruling is what it was blocked on, so it lands in drain lap 3 (T-0807).
- **`thompson_plat_1830.json`'s declared ±20 m is falsified by this measurement and must
  be corrected.** That is bookkeeping the ruling implies, not a re-opening of it: the
  file states an agreement figure of ±20 m for two sheets now measured to disagree by
  27–60 m on the North Branch. Wright being of record does not make the other sheet agree
  with it. The file should say what was measured, and cite the memo. The run that lands
  #886 makes that correction in the same PR.
- The heightfield, the water surface, the seven river landings, every waterline test and
  the frontage rules that stand on them are all UNTOUCHED. There is no cascade to file.
- [#894](https://github.com/kevinrhaas/custom/pull/894) is unaffected and stays in lap 1:
  it seats the North Division's six streets as the committed South Division streets
  continued north, unbent — deliberately not fitted to Thompson's sheet — with all 182
  soundings on modelled dry ground under the Wright bank this ruling keeps.

---

**Acceptance:** each ruling above is written into the ticket that asked it — T-0730,
the restamped kin ticket, T-0685 — quoted as given, with the reasoning that follows.
`thompson_plat_1830.json` carries the measured disagreement in place of its ±20 m claim.
T-0727 carries a queue line under the band this ticket sits in. None of #836, #841, #822,
#839 or #886 is left parked: each is merged by its lap. No question in this ticket is
re-asked of the owner.
