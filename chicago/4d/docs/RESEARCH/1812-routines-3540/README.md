# Daily routines and interactions throughout 1812

T-3540, T-3541 and T-3543 extend the 1904 household interaction model to the entire active
1812 population, including every Native resident and visitor already drawn or
listed at a lodge door. All 284 drawn people and 520 callable residents have
complete daily schedules. Reference-only identities with absent/uncertain presence
and carried infants retain their existing treatment; they are not newly placed.

The existing 233 dated/seasonal schedules remain. The 51 enlisted men gain explicit
days that delegate their original stations to human-duties only after arrival.
Meals, sleep, cold-weather tasks, visitor requests and jaunts release that owner.
Guard beats and ranks remain their existing duties. Requested patrols use the same
beat endpoints, and ordinary gardening is offered in the appropriate season.

The 520 lodge/household residents use lightweight logical days. At most three
additional nearby residents take autonomous outings, starting at most one figure
every five seconds; they return through their own door after a short activity.
Door calls remain independent of that limit. Returning residents dispose their
figures and unregister their Interact controls. All activities, exact hours and
this rendering compression are declared under L-1812-everyday-routines-3541.

Generic 1812 person controls register with the day engine, including newly built
figures. Interact offers short icon labels and retains full activity descriptions
as tooltips. Opening it lowers the Navigator panel so the card cannot obscure the
choices on a phone. Go inside selects the nearest available known entrance; Go home returns to the
person's residence. Both walk through their doors. A visiting family can wait at the Kinzie house and Winnemeg at the
agency when their current day has no town home; these temporary guest shelters
are also declared reconstructions. Greet opens the existing historical card. The seasonal day's outdoor
activities are offered at other hours, while absent and away people stay absent.

Requested chats reserve a real companion, prefer an available nearby person
outside within 18 metres, otherwise bring one outside, and speak only after both meet.
A shared household never recruits an outdoor person across town; indoor candidates
are located by their actual entrance. Requested chats meet beside the person
being asked. After about
a minute they return to their current duties; a lazy lodge resident goes back
inside. Ordinary soldiers can take this break with comrades, while sentries and
guards on watch remain at their posts. Failure to arrive, a date/hour change, a jaunt or another request releases
the pair. Existing scheduled 1812 gatherings still alternate work, play, short
conversations and indoor breaks.

## Persistent selection and destinations

The shared control gives a walking person a four-second grace period. Opening the
menu retains its person, and an explicit figure selection persists until dismissed,
hidden, retired or unavailable. The menu names its target and has a close control;
Escape dismisses it. Fixed objects keep their normal reach requirement.

The day engine temporarily pauses an available person's walk while choices are
open, restores the unfinished path on dismissal, and yields to a new time period
or jaunt. A selected action releases attention before taking ownership. Line icons
use the app's existing visual language with subtle social, task, movement and
indoor colors; the two indoor destinations are grouped at the bottom.

A person sheltered in a different building answers at that building's door. Lodge
residents are retired only after returning to their own residence. Moving from one
interior to another exits the first doorway, then walks to the destination; the
actor's one-frame hidden state while exiting cannot authorize a teleport.
One-time paths keep advancing outside drawing range, without mesh animation.
Their arrival callbacks run once and cannot redisplay an actor who just entered
a building or retired. This fixes a remotely selected person stopping on the
way inside when the visitor moves away.

## Verification

`tools/test_human_days.mjs` covers all 804 schedules, garrison duty ownership,
requested patrols, cold-season field work, Native door calls and paired
conversations, dynamic roster changes, mesh/control retirement, bounded rotation,
jaunt holds, winter presence and battle-day absence. Existing human-duties,
human-rounds, house-errand and jaunt-host tests remain part of the check gate.

`probe.mjs` exercises the published 1812 scene at 390×780 and 1280×800 using real
actors, interactions, paths, spacing and doors. It calls a Native woman out at
night, opens the actual menu, requests a companion chat, verifies both meet and
return, calls her again for an outdoor task and sends her inside. Its accelerated
clock is a functional check, not a performance measurement. Without PROBE_FAST it
also records a screenshot at each viewport. Run after `tools/publish.sh`:

```
NODE_PATH=<playwright module root> PW_EXECUTABLE=<chromium> \
  node docs/RESEARCH/1812-routines-3540/probe.mjs
```

The first phone probe exposed the Navigator card covering the expanded menu. The
onExpand hook now docks the card panel. A new retirement regression also exposed
the old inside-only path marking a figure disposed before HumanActor could free
its body and detach its root. Cleanup now
runs before that flag is set; the probe checks the real root and body are gone.

The published probes also exposed one-time walks stopping outside drawing range
and a distant outdoor camp-mate being preferred to a nearby indoor companion.
Both have regressions that fail before the correction and pass afterward.

## Completed validation

All four final local check partitions pass (324, 324, 324, 325 steps),
as does preflight. Focused tests cover all 804 schedules, seasonal and dated
presence, military duties, paired conversations, retirement, moving selection,
menu pause/resume, offscreen arrivals, doors and jaunt ownership.

Both published browser probes pass at 390×780 and 1280×800 with no page errors.
The 1812 sequence calls a Native resident at night, brings a companion out to
meet 1.4 metres away, completes the conversation and return, then requests
ordinary outdoor work and verifies both indoor destinations and resource cleanup.
The 1904 sequence catches a real walker, keeps the menu open, resumes the walk
on dismissal, pins a deliberate selection beyond reach and completes Go inside
and Go home. Default-quality screenshots were inspected. Accelerated simulation
clocks make these functional checks, not frame-time measurements.

The full published smoke passes all 15 stages on both viewports: 1,653 assertions
on source `147a770384a1`, runtime `sha256:27b7282625ca4d07`. The repository,
human-model, moving-frame performance and build checks also pass.
[PR #1929 checks](https://github.com/kevinrhaas/chicago/pull/1929/checks) track the
final head. Verification-only documentation and ledger changes retain this
runtime hash; smoke receipts keep their original source commit and job URLs.

The first desktop stage 13 attempt passed its behavior assertions but failed
the zero-page-error check when an external historical-image thumbnail returned
`net::ERR_BLOCKED_BY_ORB`. A direct request and a fresh browser decode then
loaded that JPEG successfully. The complete stage was rerun without changing
the application or its assertions; both attempts remain in the smoke ledger.

| Stages | Desktop | Phone |
| --- | --- | --- |
| 1-2 | [Pass](https://github.com/kevinrhaas/chicago/actions/runs/42944708489/job/130274606452) | [Pass](https://github.com/kevinrhaas/chicago/actions/runs/42944716815/job/130274633711) |
| 3-4 | [Pass](https://github.com/kevinrhaas/chicago/actions/runs/42944729705/job/130274675008) | [Pass](https://github.com/kevinrhaas/chicago/actions/runs/42944746422/job/130274727110) |
| 5-6 | [Pass](https://github.com/kevinrhaas/chicago/actions/runs/42944754878/job/130274755728) | [Pass](https://github.com/kevinrhaas/chicago/actions/runs/42944768664/job/130274800237) |
| 7-8 | [Pass](https://github.com/kevinrhaas/chicago/actions/runs/42944782110/job/130274845636) | [Pass](https://github.com/kevinrhaas/chicago/actions/runs/42944794555/job/130274885894) |
| 9-10 | [Pass](https://github.com/kevinrhaas/chicago/actions/runs/42944806618/job/130274926295) | [Pass](https://github.com/kevinrhaas/chicago/actions/runs/42944819744/job/130274967644) |
| 11-12 | [Pass](https://github.com/kevinrhaas/chicago/actions/runs/42944841682/job/130275039396) | [Pass](https://github.com/kevinrhaas/chicago/actions/runs/42944854311/job/130275080244) |
| 13 | [Pass](https://github.com/kevinrhaas/chicago/actions/runs/42944661493/job/130294832383) | [Pass](https://github.com/kevinrhaas/chicago/actions/runs/42944675858/job/130274501718) |
| 14-15 | [Pass](https://github.com/kevinrhaas/chicago/actions/runs/42944685838/job/130274535148) | [Pass](https://github.com/kevinrhaas/chicago/actions/runs/42944696351/job/130274570078) |
