---
id: T-0759
title: Chicago drank from the lake by cart in 1835 and the town has no waterman: the hogshead cart, the watering place at the foot of Randolph and the barrel at the door
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-06
pr: 982
claimed_by: run 9/6/2026, 6:59:23 AM CT
blocked_on: null
needs_bake: true
closed_at: 2026-09-06T12:45:58.579Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34031638142
---

Andreas's Water Works section says how this town got its drinking water, and T-0592 read it:
*"the settlers early cast longing eyes towards the lake … For some years private enterprise
reaped a comfortable little financial harvest in the operation of water carts, which ran to
and from the lake. These carts were two wheeled vehicles, upon which hogsheads were mounted.
Having driven into the lake, generally at the foot of Randolph Street, the watermen loaded up
their reservoirs by means of pails, and then commenced their journeys 'around town.' Backing
their carts up to the doors of their customers' houses, with a short leathern hose they filled
the barrels or other receptacles placed there for the purpose. The price per barrel varied,
according to competition, from five to ten cents."*
(`town_findings_andreas_v1#c013`.)

The era is bracketed at both ends by the same page: the town's one public well, dug in
Kinzie's Addition for $95.50 on 10 November 1834 (`#c012`), and the Chicago Hydraulic
Company, not chartered until 18 January 1836 and not working until 1842 (`#c014`). July 1835
sits inside it. So a cart, a hogshead, a pail, a leathern hose, a barrel standing at a door,
and a watering place at the foot of Randolph Street are all documented pieces of this town,
and the model has none of them.

**THE WEIGHT IS THE HARD PART AND IT IS WHY THIS IS ITS OWN TICKET.** This is one
retrospective sentence written in 1884 about a trade nobody minuted. It dates nothing itself;
'for some years' is what brackets it. Anything drawn from it is `inferred` at best, its
liberty has to say how many carts and on what argument, and the number is exactly the trap
T-0592 refused for wells — one cart on the one street the sentence names is as unsupported a
distribution as one well on the one lot whose address resolves.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The count and the rule that places them are argued from something, or the ticket refuses
  and says so in `docs/RESEARCH/wells.md` beside the reading that opened it.
- The barrel at a door is the cheaper half and can stand without the cart; if only that is
  supportable, ship that and say why the cart is not.
- Any new archetype is a bake: `./tools/bake.sh --only` and `tools/publish.sh` in the same
  commit; its liberty is recorded in `docs/LIBERTIES.md`.

**Links:** T-0592 · `docs/RESEARCH/wells.md` ·
`data/research/civic/claims/town_findings_andreas_v1.json#c012,c013,c014` · T-0702
