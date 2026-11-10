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
Roster refreshes preserve existing resident state: an unrelated actor arriving or
leaving cannot cancel a conversation, call, or temporary chore. Removing an actual
participant releases the remaining partner.

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

All four final local `tools/check.sh` partitions pass: 323, 323, 323 and 322
checks. Partitions use isolated checkouts with byte-identical runtime/tests and
separate published mirrors. Final preflight passes, including partition 2/4,
changelog and ticket-ID checks. The datum check initially skipped locally because
`pyproj` was absent; after installing it, the explicit rerun passes (0.01 m origin
drift, 17.5 m fit RMS). All required raster readers are installed.

- `tools/test_human_days.mjs`: outdoor and indoor companions, real arrival before
  speech, alternating turns, return to duties, unavailable partners, timeout,
  Go inside, jaunt takeover, date changes and scheduled conversations. A regression
  that adds/removes an unrelated driver fails before the roster fix and passes
  after it; removing a participant still releases the pair.
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
`PROBE_VIEWPORT` selects one width. `PROBE_FAST=1` skips the extra scene draw and
screenshot, and `PROBE_QUALITY` sets the visitor's pixel-quality preference; neither
changes the actor, day, passage, or interaction logic. The probe advances the full
human update (including gait), day, door, interaction, and spacing layers.
The final behavior/layout run passes at both viewports, at 23:00, with quality
0.5 and `PROBE_FAST=1`. John met August on the phone and Mary on desktop, 1.4 m
apart; both pairs returned indoors and the subsequent Go inside request completed.
Both pages reported zero errors. Default-quality menu screenshots were also
inspected at both widths and fit within the screen.

The desktop run exercised an actual roster change (8 actors at setup, 9 at the
request). That exposed the resident-state reset described above; preserving the
existing residents fixed the meeting. Initial attempts are not release passes:
one timed out at the 240-second ready limit during concurrent local checks, one
missed the arrival-card transition, and the earlier desktop conversation attempts
failed before the roster fix. A later default-quality diagnostic exceeded the
ready deadline and its diagnostic read stalled; that browser was stopped. Using
the complete human update loop corrected a harness omission but did not, by
itself, fix the desktop failure.

After the roster correction, focused day, household (76 checks), passage (109
checks), jaunt-host, duties, spacing and multi-era routine tests all pass.
Final PR validation and the final-runtime published smoke are pending.

## Smoke contract repair found during validation

The published full smoke on application commit `3438c7c74fd1` found ten building
material groups in 1835 where the old check required eight. T-3341, already on dev,
added the brick and clay reliefs. The repaired contract in `f7d095735c49` names
`masonry:brick` and `masonry:clay`, requires their maps and valid opaque materials,
and retains every original group and the single lighthouse-glass predicate.
Mutation checks reject missing, duplicate, mislabelled, or untextured groups.
No rendering budget or material was changed for this repair.

The full smoke is [run 42851675727](https://github.com/kevinrhaas/chicago/actions/runs/42851675727);
the corrected 7–8 checks are [run 42855177518](https://github.com/kevinrhaas/chicago/actions/runs/42855177518).
Each validation job checks that its application tree matches the named candidate.
These temporary validation workflows are not part of the feature branch.

The corrected 7–8 smoke passes on both viewports (48 assertions each). Original
failures remain in the smoke ledger under their original application tree hash.

All other original smoke legs passed, including desktop 13 (158 assertions).
Together with the corrected 7–8 runs, every stage passed on both viewports.
Those readings precede the final roster fix and retain their candidate hashes;
the final runtime will receive its own full published smoke run.
