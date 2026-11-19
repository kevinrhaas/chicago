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
| 1 | Same spot, another year | Deprioritized by owner. Navigator session design above; current Jump replacement remains. |
| 2 | Photo and share a moment | First delivery: bounded capture of the existing frame; stamped PNG and validated public view link. No notes, credentials or private identifiers in links. |
| 3 | Field notebook | First delivery: browser-local notes, chosen photos, people and citations; explicit deletion and portable/print export. No teacher upload service. |
| 4 | Understanding checks | First delivery: three optional cited reflection prompts, grade-aware wording and evidence self-review. No scoring or automatic assertion that a student's answer is correct. Authored guide-voice quizzes remain a content refinement. |
| 5 | Lesson guides | First delivery: current catalog groups, document tasks, discussion and suggested standards connections; preserve source type and provenance. |
| 6 | Class codes and teacher view | Defer shared class storage, authentication and cross-device submissions. Local exports are useful now but are not a dashboard. |
| 7 | Where and when? | T-3657 implemented in the combined delivery: five licensed 1904-scene photographs, deterministic daily/shareable order, ground-distance scores, source/date reveals and bounded local progress. One image at a time; no leaderboard service. Native-town integration passes; complete release gates pending. |
| 8 | Mysteries with sources | Later content work using evidence/confidence and existing jaunt branching. Needs authored, reviewed investigations. |
| 9 | Play a part | Existing engine already supports choices and alternate endings. Later authored historical-role stories, with reconstruction labelled. |
| 10 | Accessibility | T-3658 first slice (Navigator zoom, keyboard picture viewers, rail Tab stop), then T-3671 the full pass toward WCAG 2.1 AA: keyboard and screen-reader paths through every menu, Settings tab, jaunt and card; Text size to 200 %; contrast and focus ring in every appearance; grades told by shape as well as colour; narration transcripts and Pause; Settings › Look › Motion and Letter keys. Criterion by criterion with its tests and the known gaps (the canvas itself; no physical screen-reader run yet): docs/ACCESSIBILITY.md. No third-party audit or legal conformance claim. |
| 11 | Assign/build a jaunt | Later browser-only subset: assignment links and portable route/question files. Shared authoring libraries and submission tracking need storage. |
| 12 | Classroom/Clever/Canvas | Ordinary links/files can be assigned manually now. Defer provider setup, SSO, add-ons and grade sync. |
| 13 | Follow the teacher | Defer live cross-device coordination. Projection works now. |
| 14 | People met, places found | Notebook saves selected person cards now. Automatic visited/met collections in Map and People are later work; opening a card must not be reported as entering a building or physically meeting someone. |
| 15 | Spanish | Later browser-only localization infrastructure and reviewed UI/narrative translations. Existing string registries are a foundation, not a complete locale system. |
| 16 | On-site mode | Later extension of GPS Window mode, with real location/accuracy and mobile field testing. |
| 17 | Chromebook class set | T-3675: ChromeOS is recognised (user agent `CrOS` or userAgentData) and profiled as a computer, touch screen or not: `weak`, so Balanced, Sharpness Low, light textures and the memory diet, with people, horses, carriages and wagons drawn, never Light; keyboard/trackpad controls unless in tablet mode. PowerVR joins the shared-memory GPUs. The loading screen names the Chromebook. The year's offline copy reads "Prepare for class" with its size on a Chromebook's welcome and sits in Settings › Graphics on every device, with progress, a ready state and how to check it offline; the copy says each device keeps its own copy. An emulated Chromebook (ChromeOS UA, 4 GB, 4 threads, Intel UHD 600) has a memory ceiling in every year, held in CI with its routing. Remains: a real Chromebook (Intel and Arm) and a school network, a teacher-side view of which devices are ready, and any room-wide cache, which needs a local server. |
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
