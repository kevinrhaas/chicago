---
id: T-0718
title: Is jb_beaubien_homestead the Factory House or the house Beaubien moved to: John Dean is the hinge, and the SW-versus-NE corner turns on it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-06
pr: 990
claimed_by: run 9/6/2026, 9:16:55 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T15:50:06.728Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34038473898
---

Is jb_beaubien_homestead the Factory House or the house Beaubien moved to: John Dean is the hinge, and the SW-versus-NE corner turns on it.

**Found by T-0595**, which wrote the Factory House origin into the record and dossier and
deliberately did NOT act on what follows.

**The hinge.** `bk_hub_063` (Hubbard, 1911) names **John Dean** as the United States factor who
succeeded Jouett at the "Factor House" at the second construction of the fort. `bk_afc_009`
(Hubbard through Hurlbut, 1881) says the American Fur Company bought that Factory House from the
U.S. in 1822 and Beaubien moved his family into it. And Wentworth's 1881 address, as reprinted by
`chicagology_prefire052`, directs a reader to "the traditional residence of Gen. Jean Baptiste
Beaubien, **after he moved from what was before known as the John-Dean house**".

If those two John Deans are one man, then Beaubien **left** the Factory House, and
`jb_beaubien_homestead` — whose phase is literally named `factory_1817` — models the house he
moved TO, not the one Hubbard describes. Nothing reached says the two John Deans are one man.

**Why it is the corner question too.** The record adopts the **south-west** corner of South Water
and Michigan from Andreas p. 185, on the argument that p. 185 is about the homestead while
p. 339's **north-east** is a waypoint in a boundary walk. But Wentworth's north-east sentence is
not a boundary walk: it is expressly an instruction for finding Beaubien's residence. Whether
Andreas p. 339 and Wentworth are the same sentence at second hand has not been checked, and
checking it is half this ticket.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)
- Andreas scan p. 339 is read directly and compared with the Wentworth sentence
  `chicagology_prefire052` reprints: one sentence at second hand, or two independent ones.
- A stated finding on whether Hubbard's factor John Dean and Wentworth's "John-Dean house" are
  the same, with its confidence and its reasoning, or "not established" in as many words.
- The SW-versus-NE adoption in `position.note` is either re-argued with the Wentworth reading in
  it, or moved — and if it moves, the bake and the publish move with it.
- `form.stories` is settled or explicitly left at 1 with the reason, against `bk_hub_063`'s two.
- `tools/check.sh` green; `docs/RESEARCH/jb_beaubien_homestead.md` § 6 updated to match.

**Links:** T-0595 · T-0575 · `bk_afc_009` · `bk_hub_063` · `chicagology_prefire052` ·
`chicagology_prefire276` · `data/structures/jb_beaubien_homestead.json`
