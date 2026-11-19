# Browser-only classroom work

Owner request, 18 November 2026; delivery tracked by T-3656, T-3657 and T-3658
in PR #2197.
The source is the owner's “4D Chicago: features that would make it compelling”
list dated 17 November. This records the whole list without treating every item
as delivered in the first implementation.

## First delivery

Parallel work on **2–5**: an on-demand photo and public moment link, a local
field notebook, optional evidence-based reflection at a jaunt's ending, and
printable lesson guides. These use existing static hosting, with no new server
or service activation. Print-to-PDF uses the browser; downloadable notebooks
are files the student chooses to hand in, not automatic submissions.

The owner's priority correction is explicit: **1 is lower priority**. Keep
Jump in the Navigator and keep replacing the current document as the default.
If an additional session is offered later, explain the choice between releasing
the current world and opening another tab. A browser controls whether that is a
tab or window. A hidden or paused tab still holds GPU resources; it is not a
released session. Same-ground transfer also requires destination bounds and
ground validation. Do not preload multiple years to implement it.

## Photo hunt and accessibility in the same delivery

T-3657 and T-3658 add **7** and a bounded first slice of **10** to the same
classroom PR: a five-photo hunt in 1904, native browser magnification/panning in the
Navigator, keyboard-safe picture dialogs, and a visible rail Tab stop while Move or
Jump is open. Pure, browser-fixture and native-town integration checks pass;
complete release validation remains before the combined PR merges. Keyboard ownership
also keeps arrows and Space with focused controls and releases held world movement
when focus enters a reader. The earlier draft PR #2199 is superseded by #2197.
The hunt reuses five photographs of four places, with a daily order and shared date,
and reveals their recorded dates rather than treating them as photographs taken in 1904.

## Disposition of all twenty items

| # | Feature | Delivery / next step |
|---|---|---|
| 1 | Same spot, another year | T-3669 (owner, 19 November: "finish the rest of the top 5"): Jump carries the ground you stand on, your facing, season and hour to the far year by the moment link's bounded fields plus `via=jump&from=`. The far page validates against its own coverage and obstruction map: open ground keeps the spot, built-over or flooded ground moves to the nearest open ground within 24 m and says how far, and ground outside its town leaves that year's own Welcome and says so. Still one document replaced per Jump; nothing preloaded. |
| 2 | Photo and share a moment | First delivery: bounded capture of the existing frame; stamped PNG and validated public view link. No notes, credentials or private identifiers in links. |
| 3 | Field notebook | First delivery: browser-local notes, chosen photos, people and citations; explicit deletion and portable/print export. No teacher upload service. |
| 4 | Understanding checks | T-3670: each of the three questions now has one answer the jaunt's own data settles, asked in the guide's voice at each band: where on the walk we heard the claim, how sure we can be (its grade), and which source we cited. Every option is a real stop, grade or citation from the jaunt, so a wrong option is never an invented fact; retry is unlimited and "Show me the answer" follows two tries. Nothing is scored or stored; the own-words reflection remains under each question. |
| 5 | Lesson guides | First delivery: current catalog groups, document tasks, discussion and suggested standards connections; preserve source type and provenance. |
| 6 | Class codes and teacher view | Defer shared class storage, authentication and cross-device submissions. Local exports are useful now but are not a dashboard. |
| 7 | Where and when? | T-3657 implemented in the combined delivery: five licensed 1904-scene photographs, deterministic daily/shareable order, ground-distance scores, source/date reveals and bounded local progress. One image at a time; no leaderboard service. Native-town integration passes; complete release gates pending. |
| 8 | Mysteries with sources | Later content work using evidence/confidence and existing jaunt branching. Needs authored, reviewed investigations. |
| 9 | Play a part | Existing engine already supports choices and alternate endings. Later authored historical-role stories, with reconstruction labelled. |
| 10 | Accessibility | T-3658 follow-up implemented: native Navigator zoom/pan with stable canvas sizing and usable movement controls; keyboard-contained picture dialogs with Escape, background isolation and focus return; a visible rail Tab stop while Move or Jump is open. Browser fixtures and native-town integration pass; complete release gates pending. Broader menu/card and assistive-technology audit remains; no full WCAG 2.1 AA claim. |
| 11 | Assign/build a jaunt | Later browser-only subset: assignment links and portable route/question files. Shared authoring libraries and submission tracking need storage. |
| 12 | Classroom/Clever/Canvas | Ordinary links/files can be assigned manually now. Defer provider setup, SSO, add-ons and grade sync. |
| 13 | Follow the teacher | Defer live cross-device coordination. Projection works now. |
| 14 | People met, places found | Notebook saves selected person cards now. Automatic visited/met collections in Map and People are later work; opening a card must not be reported as entering a building or physically meeting someone. |
| 15 | Spanish | Later browser-only localization infrastructure and reviewed UI/narrative translations. Existing string registries are a foundation, not a complete locale system. |
| 16 | On-site mode | Later extension of GPS Window mode, with real location/accuracy and mobile field testing. |
| 17 | Chromebook class set | Preserve low-detail/device governor and offline-copy behavior. Bound new capture/storage work. Actual Chromebook and school-network testing remains; a device cache is not a room-wide download-once cache. |
| 18 | Ask your own question | Existing authored questions remain. A local cited-record search is possible later; generated free-form answers require separate cost/grounding decisions. |
| 19 | Classmates in town | Defer shared presence/signaling service. |
| 20 | Watch a block grow | Later bounded single-block timeline, one state at a time, subject to historical coverage. No three-world preload. |

## Resource and privacy boundaries

- Educational panels load on demand; capture allocates only when requested.
- Capture dimensions and notebook storage are bounded; failed saves are visible.
- Notebook entries stay in this browser until explicitly exported. Shared devices
  share browser storage; students can delete entries and should export before clearing it.
- Reflection is ungraded. Source quotations retain confidence and citation context.
- New controls must work by keyboard and at phone width. Hardware performance and
  complete assistive-technology conformance need their own measurements.

STATUS.md records the checks actually run and any remaining limitations. Production
promotion remains the owner's existing dispatch workflow.
