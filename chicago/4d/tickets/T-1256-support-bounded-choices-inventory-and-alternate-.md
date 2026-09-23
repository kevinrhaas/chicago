---
id: T-1256
title: Support bounded choices, inventory and alternate jaunt endings
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

**Optional mechanics, declared in data, never forced.** The owner: *"Optional inventory, money, time, reputation, information, health, sobriety, cargo or readiness mechanics when they improve that particular jaunt … Alternate outcomes or endings where appropriate … The amount of branching, scoring and decision-making should match the subject rather than being forced into every jaunt."* The schema (T-1253) already carries the shapes; this ticket makes the reducer honour them exactly once, safely, and shows them in the panel only when a jaunt declares them.

**Depends on:** T-1279. T-1258 depends on this.

**What exists today:** `jaunts.js` reducer with `vars`, `inventory`, `events[]`; schema `effects` (`add|remove|set|inc`), `when` (`all/any/not`, comparisons, `has`), `endings[]`; the three fixtures from T-1253 (plain walk, money branch, malformed).

**Build:**
1. Reducer: declared variables with `min/max` bounds (money in integer cents, `readiness`, `information`, `sobriety`, `health`, `reputation`, `cargo` with capacity, story `time` in minutes); effects clamp to bounds and are **committed once per event id** — Previous then Next never re-spends or re-awards; **Revise choice** at a visited stop truncates `events[]` after that stop and replays the rest deterministically.
2. Ending selection: the first `endings[]` entry whose `when` holds, else the declared `default`; the compiler (T-1253) already proves every branch reaches one — add the runtime assertion and a visible fallback if content is somehow inconsistent.
3. Panel: a compact resource strip (only the variables the jaunt declares; hidden otherwise) with plain-language consequence lines on choices ("costs 75 ¢ · you have $1.20"); insufficient money or full cargo disables the choice with its reason and always leaves a viable alternative or "move on".
4. Story time advances only through explicit effects; wall-clock time, reading cards, and pauses never change any variable.
5. Persistence (session resume only): `localStorage['c4d.jaunt.session.v1']` = `{ content_version, jaunt, events[] }`; on load, a mismatched `content_version` or a parse failure discards it with a one-line note; storage unavailable → memory only. No scores leave the device.
6. Fixtures: extend to one shopping jaunt (purse, basket, receipt ending), one branching tavern (sobriety, two endings, abstaining viable), one plain outing (no variables, no strip) — all three play through the same engine.
7. `tools/play_jaunt.mjs <id> --all-paths` (node, ≤ 150 lines, no browser): drives the reducer over a compiled jaunt through every choice combination, reports endings reached, effects committed, keepsakes awarded and any state with no viable move; exit 1 on a dead end or a double award. This is the walker every content ticket (5H, 5I) and T-1271 runs; it lives here because it tests the reducer's contract.

**Acceptance:**
1. `tools/test_jaunt_mechanics.mjs`: bounds clamp; `play_jaunt.mjs --all-paths` walks all three fixtures and refuses a fixture with a dead end; purchase committed once across Previous/Next; Revise replays to a different ending; insufficient money and full cargo leave a viable path; the plain fixture renders no strip; corrupt and version-mismatched saves recover.
2. Play the three fixtures on the published mirror at 390×780: strip fits on one line (or wraps to two at 320 px) without covering the sticky control; consequences read in plain language.
3. Rapid double-tap on a purchase button commits one purchase (event id dedupe).
4. No `eval`, `Function`, or `innerHTML` with content text anywhere in jaunt code (grep in the PR).

**Harness and gates:** `./tools/check.sh` (+ test); `smoke_budget.mjs --for-diff` → chrome parts `--published`, both viewports.

**Out of scope:** the daybook and ranks (T-1258), narrative content (5H/5I).

Changelog: one visible entry (resources appear on the jaunts that declare them). Contract: [architecture §C state/branches](../docs/ARRIVAL-JAUNTS-ARCHITECTURE.md#c-jaunt-json-contract) · [plan](../docs/ARRIVAL-JAUNTS-EXECUTION.md). One PR into `dev`; claim with `ticket.mjs`.
