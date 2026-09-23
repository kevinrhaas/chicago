---
id: T-0391
title: Are 'Eagle Hotel' and 'the Eagle Hotel (Steele's)' one house, and no issue prints both
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-11
pr: 1170
claimed_by: run 9/11/2026, 10:53:50 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T04:28:33.375Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34671336778
---

Two names in the gazetteer's `places` table look like one hotel and are held apart because
nothing in the corpus decides it. `place_eagle_hotel` ("Eagle Hotel") is minted from a display
heading over its own advertisement, chicago_democrat_1834_05_14 c008. `place_the_eagle_hotel_steele_s`
("the Eagle Hotel (Steele's)") is minted from chicago_democrat_1834_02_04 c003, where something is
located at "the Eagle Hotel, (Steele's)" — the building named with its keeper in a parenthesis.

T-0359 declared both places, which is what made a merge between them POSSIBLE: `place_merges` is
not held to the families rule that reads "Hotel" as a surname. It deliberately did not make the
merge. The only thing joining the two readings is the shared word Eagle, and resemblance is exactly
the argument `identity.json` exists to refuse. The Haddock's/Maddock's pair was closed because one
advertisement stands over five settings and four of them read one way; there is no such witness here
— two claims, three months apart, in different kinds of notice.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Either an issue is found that prints both settings in a way that decides it, and the merge lands in
  `place_merges` with that reading quoted; or the pair is written into `identity.json` as a refusal
  with the reason, the way `refused_places` records the two letter-list names — and this ticket is
  withdrawn rather than left open as a suspicion.
- Nothing is merged on the shared word alone. A keeper's name in a parenthesis is not evidence that
  two settings are one house; Chicago could hold two signs with an eagle on them.
- Whatever lands is gated: `compile_gazetteer.py --check` and its self-tests stay green.

**Links:** T-0359 (declared them places) · `data/research/newspapers/identity.json` ·
`tools/compile_gazetteer.py`
