---
id: T-1396
title: Dev is red at part 12 on both viewports: the garrison's 102 soldiers pushed 'labourer' off the Trade row, and T-1382's assertion names labourer by hand
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-19
closed: 2026-09-20
pr: 1603
claimed_by: run 9/20/2026, 8:21:22 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T01:43:55.760Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35550415793
---

Dev is red at part 12 on both viewports: the garrison's 102 soldiers pushed 'labourer' off the Trade row, and T-1382's assertion names labourer by hand.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-1393's run, which inherited it. `dev` is red on part 12 at BOTH viewports:

    the Trade row offers the documented trades AND the town's commonest
    13 pill(s): [attorney, tavern_keeper, merchant, schoolteacher, carpenter,
                 physician, blacksmith, hotel_keeper, soldier, domestic,
                 boarding_house_keeper, laundress, clerk]

T-1382 cut the Trade row from two rankings — the eight commonest trades among the
people the sources evidence, then the six commonest of the town as a whole — and
asserted the result by naming five trades that must be on it: tavern_keeper,
physician, attorney, domestic, **labourer**. Counted over the published sidecar today
the town's six commonest are soldier 102, domestic 76, boarding_house_keeper 44,
laundress 42, carpenter 26, clerk 26. `labourer` also has 26 and loses the
alphabetical tie-break to `clerk`, so it stands seventh and falls off.

Nothing is wrong with the row. The garrison stage minted 102 soldiers, which is a
real trade held by real people in this town, and it took a slot — exactly the
behaviour T-1382 designed for ("a reconstruction pass can ADD a pill"). What is wrong
is the assertion: it names one member of the reconstructed half by hand, so any pass
that mints a numerous trade turns it red.

**Acceptance:** the assertion tests the PROPERTY rather than a list. The evidenced half
must carry the trades a reader looks for and this project can name people in
(tavern_keeper, physician, attorney are the right probes and they are stable — they are
ranked over the evidenced layer, which a reconstruction cannot push off). The
reconstructed half must be asserted as "the town's commonest trades are on the row",
computed from the same sidecar the view reads rather than typed in. Row stays bounded,
10-16 pills. Both viewports green on part 12 afterwards — note that T-1373's count red
is the OTHER failure on that part and is not this ticket.
