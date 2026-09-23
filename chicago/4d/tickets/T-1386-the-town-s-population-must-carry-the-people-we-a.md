---
id: T-1386
title: The town's population must carry the people we already know: 276 of 410 attested residents sit outside it on an unruled 'uncertain', not on evidence of absence, and the owner's rule is that an attested person is the ideal case
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-19
closed: 2026-09-19
pr: 1523
claimed_by: run 9/19/2026, 9:39:50 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T15:44:22.904Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35449200132
---

The town's population must carry the people we already know: 276 of 410 attested residents sit outside it on an unruled 'uncertain', not on evidence of absence, and the owner's rule is that an attested person is the ideal case.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**The owner's direction, 2026-09-19, in his words:** *"You should not be so dogmatic about the
scene date, put more of those attested people back into the population, I want a full population
of the city to work from."* And earlier the same morning, the rule behind it: *"if they are
attested that's ideal if we know them already."*

**The measurement that makes this a defect rather than a preference.** Of the 410 people the
layer grades `attested`:

| grade | `present` | `uncertain` | `absent` |
|---|---|---|---|
| attested | 133 | **276** | 1 |
| inferred | 324 | **550** | 1 |
| reconstructed | **983** | 1 | 0 |
| **total** | 1,440 | **827** | **2** |

**827 people the project has evidence for sit outside the town on an unruled `uncertain`. TWO
are out on evidence of absence.** The owner extended this to the inferred in the same breath as
the attested — *"Same with inferred people"* — and the counts say why: the inferred are the
larger half of the loss, 550 against 276.

**And the asymmetry is the finding.** The RECONSTRUCTED — the people this project invented — are
ruled `present` 983 times out of 984, because the reconstruction stages rule presence as they
mint. The attested and inferred, the people the sources actually name, are left unruled. The
layer currently believes in the people it made up and is undecided about the people it read. No
standard of evidentiary caution produces that ordering; it is an artefact of which code path
happens to write a presence.

The two absences are `hh_porthier_joseph` — Joseph Porthier, one of the six documented
departures T-1354 owns — and one inferred person. So of the 829 people the town census leaves
out of its population, **827 are out because nobody has ruled them, and two are out on
evidence.**
Every one of those 827 has attested or inferred evidence that they lived in this town. None of them has
evidence they were elsewhere on 1 July 1835. They are missing from the population because a
field says `uncertain`, and `uncertain` here means unadjudicated, not disputed.

That is the wrong side of the project's own standard. T-1144's rule is "no false Chicago
resident, and no 1835 claim above its dated evidence" — which refuses INVENTING a resident. It
does not ask the layer to forget one it has attested evidence for. Holding 827 known people out
of the town's population to protect a single day's precision reads the rule backwards, and it
is worse the better the research gets: every attested person the corpus gains arrives
`uncertain` and lands outside the town.

Note also that all of them carry `tier: None` on the presence — they have no tier at all, so this
is not a case of a weak tier being honestly recorded. Nothing has been decided about them.

1. The town's population carries the attested. An attested person is in the population unless
   there is EVIDENCE they were not — a documented departure, a dated appearance elsewhere, a
   source that places them outside. `uncertain` with no tier and no contrary reading is not that
   evidence and does not exclude anybody.
2. **Rule all 827 — attested AND inferred — one at a time, and record the tier.** Each gets a presence and a tier that
   says how it was reached: attested where a source dates them at Chicago across 1 July;
   `inferred` where attested evidence places them in the town in a window that spans the scene
   date; `reconstructed` only where the persistence model is genuinely what carries it. A blanket
   flip to `present` is refused by this ticket — it would put an undeclared claim on 276 cards
   and is the fault this acceptance exists to prevent.
3. **An attested or inferred person never takes a presence tier below what their own evidence
   already supports.**
   T-1172's R1 leg re-rules `uncertain` presences at tier `reconstructed`; for a person whose
   residence is attested that is a downgrade dressed as progress. The owner's rule governs:
   attested is the ideal case and the tier must not fall below what the evidence already
   supports.
4. **The splash reads the population, and says what it is counting.** After T-1365 the gate
   screen shows the scene-established count, which is honest but is not "the population of the
   city". Whatever this unit lands, the front screen states plainly which question its number
   answers, and the scene-date figure stays available rather than being overwritten — they are
   two real measures and the project needs both.
5. The two evidenced absences stay out, and the files say why — Joseph Porthier's is a documented
   departure owned by T-1354. Two evidenced absences are the shape of a correct exclusion; 827
   unruled ones are not.
6. The order book, the town census, the population profile and the front screen all move together
   and re-derive — this changes `persons_present`, which the model's own targets are measured
   against, so the convergence set of T-1179 runs over it (model first; the whole sequence).

**NOT IN SCOPE:** inventing anybody, or relaxing T-1144's refusal of a false resident. This
ticket moves people the project has ALREADY attested or inferred from outside the town to inside
it, with a
ruling and a tier on each. It adds no new names.

**WHERE THIS IS WORKED.** The owner put it on T-1179: *"Ok so 1179 should fix them and we have
more people."* T-1179 is the resident band's closeout and already owns the convergence this
changes — `persons_present` is what the model's targets are measured against, so moving 827
people into the town moves the order book, the town census, the population profile and the front
screen together. Whoever takes T-1179 takes this with it, or T-1179 closes on a population that
leaves 827 known residents outside the town it is converging.
