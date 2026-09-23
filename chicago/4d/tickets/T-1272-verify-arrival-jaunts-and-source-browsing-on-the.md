---
id: T-1272
title: Verify arrival, jaunts and source browsing on the published mobile app
state: open
epic: RENDERING
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-17
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

**The published, integrated experience, end to end** — cold boot → arrival → welcome → a jaunt → a detail card and a source → a mode change → End → a second jaunt → Explore Myself — on the published mirror at both gate viewports, with concrete integration failures fixed inside this slice. This closes the section.

**Depends on:** T-1271, T-1275, T-1276, T-1278, T-1259.

**Do:**
1. Add a smoke section (its own `SMOKE_STAGE` part, priced with `smoke_budget.mjs --legs` so no nightly leg exceeds its 30-minute cap) that runs the full path above at 390×780 and 1280×800 on `--published`, asserting: year never reads 1835 before `api.ready`; the welcome shows no count/percentage; picker spawn takes no pointer lock; a jaunt starts at stop 1; Previous/Next/End/Menu work; mode switch changes motion and ETA; detail card returns to the same stop; End returns to the menu in < 200 ms; Explore Myself clears a paused jaunt; Sources counts still match `index.json` after the 25 jaunts' claims were registered; zero page errors.
2. Boot variants: warm (service of cached assets), throttled slow (CPU 4×, Fast 3G), essential failure (Retry offered, no arrival), optional failure (people.json 404 → still arrives), `prefers-reduced-motion`, background/resume, stale local timing history, and a failed `statuses.json`/catalog fetch (basic entry still works).
3. Layout: 320 px width, 780×390 landscape, on-screen keyboard open in the picker, safe-area insets, focus order and restoration, ≥ 44 px targets, no overlap among popup / drawer / jaunt panel / sticky control / touch stick.
4. Budgets: `measure_boot_payload.mjs --check` (12 MB), `measure_boot_phases.mjs` before/after this section (arrival.js + loading-early.js added to boot), frame cost at the reference stands unchanged (`measure_stand_budget.mjs`); catalog, jaunt files, source index and statuses stay lazy. T-1156 owns CI wiring of the payload check — do not duplicate it; do not raise a budget silently.
5. Legacy surfaces still work: every Evidence topic, Go to, Travel settings, People, framing, the popup — the existing smoke parts pass unchanged.
6. Record all evidence in `docs/measurements/arrival_jaunts_acceptance_2026-xx.md` and a STATUS.md section; fix what fails here if it is an integration defect; a defect that belongs to one component's contract goes back as a successor placed beside that ticket, named in the report.

**Acceptance:**
1. The new smoke part passes on the published mirror at both viewports with zero page errors, and is priced in `smoke_budget.mjs`'s map.
2. All boot variants and layouts in 2–3 pass, with stills in the report.
3. Budgets: boot payload under 12 MB; `boot-weights.js` re-measured and updated if the boot changed by > 10 %; reference-stand frame cost within the existing ceilings.
4. No requirement of this section is relabelled as done; anything left is a named successor inside 5F–5J, not a tail line.

**Harness and gates:** `./tools/check.sh`; the full `smoke_renderer.mjs --published` at both viewports (staged per `docs/SMOKE-BUDGET.md`); `preflight.sh`; merge green into `dev`; do not promote `main`.

Changelog: one visible entry. Contract: [architecture](../docs/ARRIVAL-JAUNTS-ARCHITECTURE.md) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
