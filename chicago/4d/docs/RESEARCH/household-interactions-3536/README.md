# Household interactions (T-3536)

Engineering verification, not an archival reading. The activities and timings remain
reconstructions under [L-t3533-household-routines](../../LIBERTIES.md#l-t3533-household-routines--1904-seasonal-household-days).

Multiple actions open under **Interact**. R toggles the list, Escape closes it,
and number keys select actions while it is open. Selecting an action or changing
target closes the list. Buttons retain their action IDs, use short labels and
decorative icons, and keep the full seasonal activity in their tooltip. The list
scrolls within the viewport. Single-action objects keep their direct control.

A discussion reserves two available people with the same home in their seasonal
day. It prefers an outdoor companion, otherwise bringing someone out through an
existing door. People who are away, on a jaunt, answering a caller, using a passage,
or following another visitor request are unavailable as companions. Both must
arrive within 2.2 metres before taking alternating speaking turns. After a minute
of company they resume their current duties; a completed scheduled discussion
returns indoors until the next period. Failed arrivals time out after 150 seconds.
Go inside, greetings, date/hour changes, removal and jaunt takeover release the pair.

The seven household members doing chores use working poses and short movements
on clear ground. The coachman retains his stationary watch.

## Extending to other houses

Give each person a complete seasonal day with an indoor `where` home and authored
outdoor work, walk or talk spans. The partner selection uses the home reference,
not Glessner identity IDs. Add short controls for unfamiliar tasks in
`activityOffer`; keep the complete description in the schedule. Existing door
passages, clear-ground checks, jaunt ownership and timed requests remain the
shared movement and interruption mechanisms.

## Checks

All four local `tools/check.sh` partitions pass: 323, 323, 323 and 322 checks.
Parts 3 and 4 ran in isolated checkouts with byte-identical application changes
and separate published mirrors.

- `tools/test_human_days.mjs`: outdoor and indoor companions, real arrival before
  speech, alternating turns, return to duties, unavailable partners, timeout,
  Go inside, jaunt takeover, date changes and scheduled conversations.
- `tools/test_house_errands.mjs`: 76 checks, including the collapsed list, R,
  Escape, hidden shortcuts, selection, and existing real-actor door/stroll behavior.
- `tools/test_human_rounds.mjs`: the 1812, 1835 and 1904 routine simulations pass;
  the tally observes paired conversations and actual returns indoors.

The published browser probe in [probe.mjs](probe.mjs) uses the real 1904 scene,
actors, doors and Interact controls at 23:00. It checks 390×780 and 1280×800 menu
bounds, short labels, disclosure behavior, an actual requested pair, both returns
indoors, and Go inside. Movement clocks are stepped directly after loading, so
this is a behavior/layout check, not a frame-time measurement. Screenshots are
written to `/tmp/t3536-menu-390.png` and `/tmp/t3536-menu-1280.png`.

Run from `chicago/4d` after `bash tools/publish.sh`:

```sh
node docs/RESEARCH/household-interactions-3536/probe.mjs
```

`NODE_PATH` may supply Playwright and `PW_EXECUTABLE` may select its Chromium.
The first phone attempt timed out at the normal 240-second ready limit while a
local gate pool was also running; it reached no interaction assertions. Final
published browser and full smoke results are pending. No release pass is claimed
for that attempt.
