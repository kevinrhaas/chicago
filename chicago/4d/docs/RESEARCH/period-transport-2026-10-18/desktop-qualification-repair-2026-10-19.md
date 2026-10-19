# Desktop transport qualification repair — 2026-10-19

The earlier f97 published desktop stage 13 run failed its 330 draw-call guard at 331 and its 10% HUD guard at 31.23%. The saved 512f checkpoint passed 1,015 fast checks but was not merge-qualified. This follow-up preserves both ceilings.

## Changes

The HUD instrument waits after the hint for the actual visible, in-viewport Navigator dock: correct semantic level/detent, no pending/running native root animations,58px desktop rail or136x64 phone pill. The same readiness is required for baseline and both planted controls. The original 10% union,2px grid, exclusions and positive-control predicates are unchanged. It does not repeatedly redock, hide UI or freeze CSS motion.

Only the explicit camera-facing grass card material now uses Three.js forceSinglePass. The three sharing sets are flora-mid, flora-far and flora-mid-carry. Blade/head/forb/shrub/GPU-near materials, trees, buildings, geometry, confidence colors/opacity and both rendered sides are unchanged. Three 0.185.1 documents this option for flat vegetation. These cards start as zero-depth sheets and turn toward the camera; wind can bend them, so the measurement below is deliberately scoped to its sampled camera.

## Actual local evidence

Published runtime512f, with the proposed material flag applied only in memory for a controlled false/true/false experiment. All three modes shared the same prepared camera and held animation. WebGL was restored before every actual frame. Immediate final-frame RGBA readback produced nonblank scene images; root viewed the tint and both row-ghost images. Candidate and restored full-frame pixels were exactly equal to baseline in every mode.

| Mode | Baseline calls | Candidate | Restored | Removed submitted triangles |
| --- | ---: | ---: | ---: | ---: |
| Tint |287|287|287|0|
| Reconstructed at 40% ghost |327|325|327|4602|
| X-RAY |316|313|316|5456|

Actual renderBufferDirect call/triangle deltas sum to the frame totals. Each optimized card changes BackSide+FrontSide into one DoubleSide submission with the same per-submission triangle count and instance coverage. All other submitted rows are unchanged; restored rows/totals/pixels match exactly. Warm-up recorded initial GPU geometry registration from 526 to 568, then two consecutive stable frames before comparison. Earlier incomplete probes and their failures remain preserved; no failed attempt is treated as a pass.

This does not reproduce the historical331 frame: its exact camera/residency was not logged. It also does not prove visible card-fragment contribution or equivalence at every other camera; submitted coverage and a nonblank whole-scene image are not that control. Source geometry and the documented engine use support the narrow material choice; production photographic acceptance remains open.

The generic 3,470,000 submitted-triangle ceiling is unchanged. Ghost samples already exceeded it before this change and still do: row ghost 3,486,563 to 3,481,961; X-RAY 3,654,889 to 3,649,433. Their stats.withinBudget remains false. The result above proves the strict330 draw-call assertion and reduced work, not overall triangle-budget acceptance. No triangle assertion or ceiling was raised or removed.

Actual HUD positives used 1280x800 and CSS-resized 390x780/390x844 in the existing desktop context. Baseline/Extra/old-row percentages were 6.75/6.96/8.32, 9.31/10.01/14.53 and 8.61/9.25/13.43. Every dock readiness, baseline 10% and original planted-control predicate passed. Root viewed all three screenshots. WebGL was held only during those diagnostic DOM screenshots and restored before numerical measurements. These are not genuine touch or phone-GPU qualification.

The first standalone HUD run reached its 400s bound after all positives, leaving refusal/restoration incomplete; its overall result remains false. A separate completed actual run then observed visible OPEN rejection(52.53% footprint), a restored dock, rejection of an infinite native opacity1 animation with unchanged visible dock geometry, cancellation and a ready dock. All five steps and final app/level/viewport/renderer/animation restoration passed. No page/network/console errors were recorded in the completed run.

Fourteen extracted-source readiness controls and nine aggregate controls passed, including reopened-during-hint, hidden/offscreen docks and inflated unready planted controls. Final installed-source preflight, exact-head canonical human export, all 18 published smoke legs and normal PR checks are still required before the conditional dev merge.

## Durable receipts

Central ticket evidence: evidence/period-transport-2026-10-18/hair-normal-precision-2026-10-19/fb6-c02-requalification/desktop-repair-completed-proof/ in kevinrhaas/chicago-tickets. The main actual run is run-512f-card-pixel-proof-refusals-v3.json; mode comparison.json/PNGs and hud-refusals.json retain raw rows and actual restoration. Standalone HUD positives and all earlier failed probes are kept separately. This document records working-tree validation before the final code commit; the frozen-tree and final-check receipts bind the committed candidate later.
