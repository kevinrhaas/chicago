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

T-3678 generalizes it: a small case table names each case's jaunt, year, readings and
evidence, and four more completed outings offer one (1812 twice, 1835, 1904). Each case is
refused unless every named claim is still cited, visited and graded as recorded.
`docs/RESEARCH/investigations-3678.md` records each case's evidence and why it conflicts.

## Disposition of all twenty items

| # | Feature | Delivery / next step |
|---|---|---|
| 1 | Same spot, another year | Deprioritized by owner. Navigator session design above; current Jump replacement remains. |
| 2 | Photo and share a moment | First delivery: bounded capture of the existing frame; stamped PNG and validated public view link. No notes, credentials or private identifiers in links. |
| 3 | Field notebook | First delivery: browser-local notes, chosen photos, people and citations; explicit deletion and portable/print export. No teacher upload service. |
| 4 | Understanding checks | First delivery: three optional cited reflection prompts, grade-aware wording and evidence self-review. No scoring or automatic assertion that a student's answer is correct. Authored guide-voice quizzes remain a content refinement. |
| 5 | Lesson guides | First delivery: current catalog groups, document tasks, discussion and suggested standards connections; preserve source type and provenance. |
| 6 | Class codes and teacher view | Defer shared class storage, authentication and cross-device submissions. Local exports are useful now but are not a dashboard. |
| 7 | Where and when? | T-3657 merged to DEV in #2197: five licensed 1904-scene photographs, deterministic daily/shareable order, ground-distance scores, source/date reveals and bounded local progress. One image at a time; no leaderboard service. |
| 8 | Mysteries with sources | T-3663: the Gossip case (two cited newspaper readings). T-3678: a case table drives it, with four more cases built only from each jaunt's own cited claims: where the 1812 attack began, who bought Du Sable's trading post (1812), where Eliza Chappel's school met (1835) and whether the 1893 bronze shows what happened (1904). Student bands; the 18+ tellings are left out of the later cases. Claim, chosen support, uncertainty and ungraded review, saved to Notebook only on request. No invented witnesses, engine or service. |
| 9 | Play a part | Existing engine already supports choices and alternate endings. Later authored historical-role stories, with reconstruction labelled. |
| 10 | Accessibility | T-3658 first slice (Navigator zoom, keyboard picture viewers, rail Tab stop), then T-3671 the full pass toward WCAG 2.1 AA: keyboard and screen-reader paths through every menu, Settings tab, jaunt and card; Text size to 200 %; contrast and focus ring in every appearance; grades told by shape as well as colour; narration transcripts and Pause; Settings › Look › Motion and Letter keys. Criterion by criterion with its tests and the known gaps (the canvas itself; no physical screen-reader run yet): docs/ACCESSIBILITY.md. No third-party audit or legal conformance claim. |
| 11 | Assign/build a jaunt | Later browser-only subset: assignment links and portable route/question files. Shared authoring libraries and submission tracking need storage. |
| 12 | Classroom/Clever/Canvas | Ordinary links/files can be assigned manually now. Defer provider setup, SSO, add-ons and grade sync. |
| 13 | Follow the teacher | Defer live cross-device coordination. Projection works now. |
| 14 | People met, places found | T-3673 implemented: a bounded browser-local list per year (`chicago4d.metfound.v1`, an id and its first day only, never evicted). **Met** = a Greet, Tell me a story or Ask a question finished in town, on foot (not flying) within 8 m of someone standing outside; a card opened from People, search, Inspect, a jaunt or a link never counts. **Found** = on foot (not flying, riding, aboard, at a helm, in Inspect or on the arrival screen) inside a named place's footprint or within 3 m of its walls, checked once a second; unnamed buildings, privies and sheds are not places. People (1812, 1835, 1904) shows a Met badge and a "Met N of M" filter; the Map outlines found places with "Found N of M places" and a toggle; both have Clear <year> with an inline confirm. Damaged or unavailable storage is said on screen. No streaks, scores, leaderboards or network. Notebook still saves chosen person cards. |
| 15 | Spanish | Later browser-only localization infrastructure and reviewed UI/narrative translations. Existing string registries are a foundation, not a complete locale system. |
| 16 | On-site mode | Later extension of GPS Window mode, with real location/accuracy and mobile field testing. |
| 17 | Chromebook class set | Preserve low-detail/device governor and offline-copy behavior. Bound new capture/storage work. Actual Chromebook and school-network testing remains; a device cache is not a room-wide download-once cache. |
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
