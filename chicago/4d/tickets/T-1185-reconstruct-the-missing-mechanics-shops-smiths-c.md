---
id: T-1185
title: Reconstruct the missing mechanics' shops: smiths, carpenters and joiners, coopers, wheelwrights and wagon makers, tailors, shoemakers, tanners, saddlers, tinners, masons, painters, bakers and butchers, to the twenty-five mechanics' shops and the occupation model's quota
state: done
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-19
pr: 1539
claimed_by: run 9/19/2026, 5:20:38 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T23:21:21.590Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35472821496
---

Second group of T-1184's tool. The *American* of August 1835 counted "twenty-five
mechanics' shops of all kinds"; the roof programme carries 30 workshop roofs (W1 6 forges, W2 8
joiners, W3 6 cooper/wheelwright, W4 6 artisan shop-houses, W5 4 riverside heavy); the retired
programme's occupation census argued coopers 4, shoemakers 3, tailors 2, wheelwright, harness
maker, gunsmith, painter 1 each from the packing volumes and the 1833 roster — arguments that are
carried forward here at tier `reconstructed`, re-derived against T-1162 instead of the five
old figures.

**This group's quota:** the occupation model's gap per mechanic trade, capped by the workshop
family roofs (a trade with a shop family may not exceed its family's roofs — the retired rule,
kept), and bounded by the American's twenty-five. Each firm: sole trader style (`W. Hayes,
Blacksmith`; `Thos. Reed, Cooper`; `Boot & Shoe Maker`), a proprietor household with the trade,
`street_only` on the faces the placement policy gives mechanics (State, Dearborn, Clark south of
Lake, the Canal Street approach, the North Water bank for the heavy riverside trades), and the
staff rows the staffing model implies (journeyman/apprentice), written by T-1189.

**Acceptance:**

- Records build to quota; `--check`; LIBERTIES scope; counts by trade against the 25 and the
  workshop family roofs printed side by side; where the three disagree the ticket says which
  bound wins and why.
- Every existing `inf_*` workshop structure (`inf_blacksmith_shop_west`, `inf_cooperage_south`,
  `inf_cooperage_south_branch`, `inf_gunsmith_shop`, `inf_harness_shop`, …) is either ADOPTED as
  the premises of one of these firms (its `reconstruction.occupation` matches) or listed for
  retirement in T-1197; none is left anonymous when a firm of its trade is written.
- Visible: the Businesses view; the adopted `inf_*` building cards now name a keeper.

**Stop condition:** the mechanics' buckets read filled; every workshop roof standing has, or is
scheduled to have, a named (reconstructed) trade behind it.

**Links:** T-1184 · T-1162 · `residents_1835_inferred.md` § 3 · T-1108.
