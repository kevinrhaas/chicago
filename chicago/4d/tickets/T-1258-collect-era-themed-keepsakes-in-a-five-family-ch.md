---
id: T-1258
title: Collect era-themed keepsakes in a five-family Chicago daybook
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

**The Chicago daybook**: era-themed keepsakes in five families, and ranks that ask for a little of each. The owner: *"Era-appropriate achievements/rewards rather than generic game XP … different kinds of jaunts could collect different things … 3–5 scoring systems and when you collect enough from all categories that is a level up or something to that effect, use popular and modern gameplay examples for this."* Low pressure — the reference points are everyday-collection games and place-linked waypoint stories, not leaderboards.

**Depends on:** T-1256 (once-only commits), T-1257 (outcome/detail phases). T-1259 depends on this.

**What exists today:** the reducer's `outcome` phase and `keepsake` field in the schema (`{ family, id, title, text }`); the outcome card returned into the menu (T-1279); `localStorage` helpers in `hud.js` (`store`/`readStored`).

**Build:**
1. `data/jaunts/daybook.json`: the five families — **Provisions** (receipts, supply lists), **Livelihood** (work chits), **Wayfinding** (route notes), **News & Knowledge** (clippings, notices), **Neighbors** (calling cards, introductions) — each with a one-line description and an icon id; the ranks **New Arrival → Finding Your Feet → Knows the Town → Seasoned Chicagoan** with thresholds `[0, 1, 2, 3]` distinct keepsakes in *every* family; keepsake rendering templates per family (a receipt looks like a receipt, a chit like a chit) — all data, no code per family.
2. `renderers/web/js/jaunt-journal.js` (~200 lines): `award(keepsake)` on completion only (a jaunt's primary and at most one secondary family), idempotent per `jaunt id + keepsake id` so replays, Previous/Revise and duplicate completion events cannot inflate; `rank()` from distinct keepsakes per family; persistence at `localStorage['c4d.daybook.v1']` = `{ schema_version, content_version, keepsakes[] }` with corrupt/incompatible recovery (explained, not silent), memory-only when storage fails, and a **Reset daybook** control.
3. UI: a **Daybook** section reachable from the Jaunts menu (and the outcome card) — the five families as a row of small counters, the rank line, and the keepsake list as cards with "narrative keepsake, not evidence" printed once at the top; mobile: one screen tall, scrolls inside the sheet.
4. Outcome card: shows the keepsake earned, the family counter moving, and the rank when it changes — no streaks, no timers, no comparison to others. Every jaunt stays playable at every rank.
5. Fixtures: five tiny fixture jaunts, one per family, so the balanced-progression test can reach Seasoned Chicagoan.

**Acceptance:**
1. `tools/test_daybook.mjs`: award once across replay/Previous/Revise/duplicate events; rank thresholds exactly as data; three distinct keepsakes in four families and two in the fifth is *not* Seasoned; corrupt and old saves recover; storage-off works; reset clears.
2. Complete the pilot on the published mirror at 390×780: outcome shows the keepsake and counter; Daybook opens from the menu and lists it; reload keeps it.
3. Changing `daybook.json` thresholds changes the ranks with no JS change (show the diff).
4. No invented source attribution appears on any keepsake (grep + a render assertion).

**Harness and gates:** `./tools/check.sh` (+ test); `smoke_budget.mjs --for-diff` → chrome parts `--published`, both viewports.

**Out of scope:** authoring the 25 keepsakes (content tickets), menu filters (T-1259).

Changelog: one visible entry. Contract: [architecture §G and "Collections"](../docs/ARRIVAL-JAUNTS-ARCHITECTURE.md#collections-without-turning-every-outing-into-a-competition) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
