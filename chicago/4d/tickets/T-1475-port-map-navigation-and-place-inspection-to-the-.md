---
id: T-1475
title: Port map navigation and place inspection to the Unreal preview
state: blocked-tech
epic: PIPELINE
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: T-1356
opened: 2026-09-20
closed: null
pr: null
claimed_by: null
blocked_on: Qualified Unreal executor and approved runtime provenance contract; use T-1473 placement and T-1360 street receipts for navigation routes
needs_bake: false
closed_at: null
claimed_run: null
---

Owner request, 2026-09-20: bring navigation and the web application's interaction features into Unreal. Parent: T-1356. First bounded slice: map/search/place selection and source-aware inspection; remaining time/epoch and interaction features stay visible in the parity matrix.

**Executor: LOCAL / QUALIFIED UNREAL ONLY.** A remote worker may inventory web controls and prepare runtime-safe data, but completion requires packaged UI/input tests on an engine-capable runner. Hold for a reviewed runtime provenance contract and current engine access. Route acceptance uses T-1473 placement and the applicable T-1360 road corridor; do not imply an AI NavMesh is required merely to reproduce first-person navigation.

## Acceptance — find and inspect a place in the native app

1. Inventory the current web navigation and interaction flows at a pinned revision: movement/camera, compass/street labels/unit settings, inset/full map orientation/player marker, route-guided travel and pace controls, search/filter, place selection, information/source/confidence cards, reset/bookmarks or travel controls where present, settings/help, and time/epoch navigation. Mark what exists natively, what this slice implements, and what remains. Match user-visible behavior rather than invent unrelated game menus.
2. Implement map/player location, search for a named place, select it, and open a readable place card with source citations and confidence/review status from approved runtime sidecars. Do not expose private research files. Preserve missing/conjectural status. Show unavailable features honestly; do not provide decorative controls that do nothing.
3. Verify mouse capture/release, keyboard focus and input conflicts: typing in search must not walk the character; closing menus returns control predictably; pause/back/restart/quit behavior is documented. Check readable UI at two window sizes and keyboard operation. Any optional jump-to-place action is distinct from normal walking tests, with safe spawn and no persistent ghost/fly mode.
4. In a packaged build, locate a known building, navigate a verified route, inspect its card/citations, return to play and reset. Test missing search results, missing provenance and selected-place changes without stale UI. Record visual/input receipts and remaining web differences.
5. Hand off one bounded successor for remaining compass/map/travel/pace controls, time/epoch switching and confidence/interaction parity in this same band. A single-date app with search is not complete web parity; keep T-1356 open until each inventory row has evidence or an explicit owner-accepted deferral.

**Budget exception:** Owner explicitly requested navigation in addition to builds, placement and flora; this is a separately testable first UI slice.
