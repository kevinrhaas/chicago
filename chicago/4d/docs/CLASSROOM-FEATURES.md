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
Jump is open. The combined PR #2197 merged to DEV after its source and renderer gates
passed. Keyboard ownership
also keeps arrows and Space with focused controls and releases held world movement
when focus enters a reader. The earlier draft PR #2199 is superseded by #2197.
The hunt reuses five photographs of four places, with a daily order and shared date,
and reveals their recorded dates rather than treating them as photographs taken in 1904.

## Next separate delivery: one source investigation

T-3663 uses the existing *Gossip or Printed Notice?* route and its five tellings.
**Make your case** stays collapsed until requested and preserves the general reflection.
It displays our readings of two newspaper transcriptions, with dates, locators,
citations and uncertainty. The lost sale figure remains lost; the Springfield building
is an inference. Save keeps the student's chosen support and answer with both readings
in the existing notebook. No new account, service, route or source image is involved.
This separate implementation follows the merged first delivery and still requires
its own complete release gates in PR #2205.

## Teacher routes (item 11)

T-3672 adds a teacher's own route without a server, account or upload. In Guide ›
For teachers, *Make a route for your class* starts from a jaunt (its buildings and
viewpoints, in order; the jaunt itself stays startable) or from places and people found
by name in the year the teacher is in. Each stop may carry a note and a question of up to
280 characters; the title is up to 80; a route holds up to 20 stops. The route is one
object (`renderers/web/js/teacher-route.js`): a `?route=` link carries it as base64url of
compact UTF-8 JSON, bounded to 6,000 characters, and a downloaded route file carries the
same object in readable JSON for the teacher to open again and change.

A student who opens the link lands in that year with the Route panel pinned above the
Jaunts list: stops in order, Go there for each (a person found in town, else at the house
they live or work in, else their card), and the teacher's note and question labelled as
the teacher's words, drawn as text only. Answers save to the field notebook under the
route's and stop's names; its existing download or print is how they are handed in. A
malformed or over-long link lands in the town with a message; a link for another year
names that year and offers its link; ids this town does not hold are dropped and counted.
Nothing about the route is recorded or sent anywhere.

## Disposition of all twenty items

| # | Feature | Delivery / next step |
|---|---|---|
| 1 | Same spot, another year | T-3669 (owner, 19 November: "finish the rest of the top 5"): Jump carries the ground you stand on, your facing, season and hour to the far year by the moment link's bounded fields plus `via=jump&from=`. The far page validates against its own coverage and obstruction map: open ground keeps the spot, built-over or flooded ground moves to the nearest open ground within 24 m and says how far, and ground outside its town leaves that year's own Welcome and says so. Still one document replaced per Jump; nothing preloaded. |
| 2 | Photo and share a moment | First delivery: bounded capture of the existing frame; stamped PNG and validated public view link. No notes, credentials or private identifiers in links. |
| 3 | Field notebook | First delivery: browser-local notes, chosen photos, people and citations; explicit deletion and portable/print export. No teacher upload service. |
| 4 | Understanding checks | T-3670: each of the three questions now has one answer the jaunt's own data settles, asked in the guide's voice at each band: where on the walk we heard the claim, who on the walk told us (the stop's one host), and how sure we can be (its grade). A "which source" question was tried and dropped on the owner's reading: a citation is not something a student can recall, and the record behind a line can differ from the book the telling echoes. Each question quotes the line the walk actually said, and the record behind it waits under "Where does this come from?" with where we read it. A sweep of all 240 tellings found 1,846 of 4,528 stop records were never said aloud at their stop; those are never quizzed now (`heardLine`, enforced in `test_jaunt_understanding.mjs`), and two loosely retold 3-5 tellings get no check rather than a wrong one. Every option is a real stop, person or grade from the jaunt, so a wrong option is never an invented fact; retry is unlimited and "Show me the answer" follows two tries. Nothing is scored or stored; the own-words reflection remains under each question. |
| 5 | Lesson guides | First delivery: current catalog groups, document tasks, discussion and suggested standards connections; preserve source type and provenance. |
| 6 | Class codes and teacher view | Defer shared class storage, authentication and cross-device submissions. Local exports are useful now but are not a dashboard. |
| 7 | Where and when? | T-3657 merged to DEV in #2197: five licensed 1904-scene photographs, deterministic daily/shareable order, ground-distance scores, source/date reveals and bounded local progress. One image at a time; no leaderboard service. |
| 8 | Mysteries with sources | T-3663: first bounded case in progress, attached to eligible Gossip completion. Compare two cited newspaper readings, choose support, write a claim/uncertainty, review an ungraded guide and explicitly save to Notebook. No invented witnesses or new engine; browser and release validation pending. |
| 9 | Play a part | T-3679 first delivery: three role jaunts on the existing engine, each with two route-changing choices and four endings. *Errands Before the March* (1812, Errands): a runner of the settlement carries the evacuation order of August 1812 and ends on the eve of the march, with no fighting told. *Apprentice at the Democrat* (1835, Work): the paper's new apprentice carries the 1 July number round the town. *Ice for Prairie Avenue* (1904, Work): an iceman's helper finds the right door at 1800 Prairie. Every grade band and 18+ telling built; the roles, choices and endings are reconstructed (L-play-a-part-3679). More roles are content work. |
| 10 | Accessibility | T-3658 first slice (Navigator zoom, keyboard picture viewers, rail Tab stop), then T-3671 the full pass toward WCAG 2.1 AA: keyboard and screen-reader paths through every menu, Settings tab, jaunt and card; Text size to 200 %; contrast and focus ring in every appearance; grades told by shape as well as colour; narration transcripts and Pause; Settings › Look › Motion and Letter keys. Criterion by criterion with its tests and the known gaps (the canvas itself; no physical screen-reader run yet): docs/ACCESSIBILITY.md. No third-party audit or legal conformance claim. |
| 11 | Assign/build a jaunt | T-3672 implemented the browser-only subset: Guide › For teachers builds a route from a jaunt or from one year's buildings, viewpoints and people (up to 20 stops, a note and a question each), as one bounded `?route=` link and a reopenable route file; the student's Route panel in Jaunts gives Go there per stop, shows the teacher's words as theirs, and saves answers to the local field notebook. Shared authoring libraries and submission tracking still need storage. |
| 12 | Classroom/Clever/Canvas | Ordinary links/files can be assigned manually now. Defer provider setup, SSO, add-ons and grade sync. |
| 13 | Follow the teacher | Defer live cross-device coordination. Projection works now. |
| 14 | People met, places found | T-3673 implemented: a bounded browser-local list per year (`chicago4d.metfound.v1`, an id and its first day only, never evicted). **Met** = a Greet, Tell me a story or Ask a question finished in town, on foot (not flying) within 8 m of someone standing outside; a card opened from People, search, Inspect, a jaunt or a link never counts. **Found** = on foot (not flying, riding, aboard, at a helm, in Inspect or on the arrival screen) inside a named place's footprint or within 3 m of its walls, checked once a second; unnamed buildings, privies and sheds are not places. People (1812, 1835, 1904) shows a Met badge and a "Met N of M" filter; the Map outlines found places with "Found N of M places" and a toggle; both have Clear <year> with an inline confirm. Damaged or unavailable storage is said on screen. No streaks, scores, leaderboards or network. Notebook still saves chosen person cards. |
| 15 | Spanish | Later browser-only localization infrastructure and reviewed UI/narrative translations. Existing string registries are a foundation, not a complete locale system. |
| 16 | On-site mode | T-3674 implemented in 1904: Window mode offers a seven-stop on-site tour of Prairie Avenue ending at the Glessner House. Each stop has today's position (derived from its 1904 parcel and checked against the City's landmark lot) and a cited card; live distance and direction from the fix; arrival inside a radius scaled to the reported accuracy, never on a fix rougher than 35 m; a fix off the tour's ground is said and never walked to; Window mode now opens without motion access too (a sideways drag turns the view); `?window-at=` drives it. Desk checks and 390×780 / 1280×800 captures only: the walk on the real street with a phone or tablet is the owner's field test. Other neighbourhoods and years remain. |
| 17 | Chromebook class set | T-3675: ChromeOS is recognised (user agent `CrOS` or userAgentData) and profiled as a computer, touch screen or not: `weak`, so Balanced, Sharpness Low, light textures and the memory diet, with people, horses, carriages and wagons drawn, never Light; keyboard/trackpad controls unless in tablet mode. PowerVR joins the shared-memory GPUs. The loading screen names the Chromebook. The year's offline copy reads "Prepare for class" with its size on a Chromebook's welcome and sits in Settings › Graphics on every device, with progress, a ready state and how to check it offline; the copy says each device keeps its own copy. An emulated Chromebook (ChromeOS UA, 4 GB, 4 threads, Intel UHD 600) has a memory ceiling in every year, held in CI with its routing. Remains: a real Chromebook (Intel and Arm) and a school network, a teacher-side view of which devices are ready, and any room-wide cache, which needs a local server. |
| 18 | Ask your own question | Existing authored questions remain. A local cited-record search is possible later; generated free-form answers require separate cost/grounding decisions. |
| 19 | Classmates in town | Defer shared presence/signaling service. |
| 20 | Watch a block grow | Later bounded single-block timeline, one state at a time, subject to historical coverage. No three-world preload. |

## People met, places found (T-3673)

Item **14** keeps its two words literal. You *met* someone when you talked with them here:
the Interact engine finished a Greet, Tell me a story or Ask a question with a person standing
in the town, and you were on foot within 8 m of them (their 2.5 m reach plus the few metres the
Interact key holds them while they turn to you). You *found* a place when you stood there:
inside its footprint or within 3 m of its walls, on foot. Cards opened from the directory,
search, Inspect, jaunt cards and shared links never add anyone or anywhere, and a Map preview
or Go to card is not a visit. The check is a box test over the Map's footprints once a second,
with no new GPU work. The list is per year, bounded and kept in this browser only.

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
