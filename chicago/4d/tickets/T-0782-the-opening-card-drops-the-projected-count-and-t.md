---
id: T-0782
title: The opening card drops the projected count and the 371-structures line and reads as two parallel completeness ladders — buildings and people
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: 893
claimed_by: run 9/5/2026, 10:25:46 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T15:25:47.068Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33973340162
---

The owner, 2026-09-05, on the opening card (the gate screen, `renderers/web/js/census.js` + the ready line in `main.js`): "for the named residents dont include the projected number there", "that 29 people housed of 3265 is a portion of what will eventually be the 1404 named residents 425 attested and 881 inferred and more and the balance will be reconstructed to get to the 3265, can you improve the way that is presented", and "at the top it says 371 structures, just remove that".

**What the card says today, and why it misleads.** Three stacked figures: `359 buildings standing · of the 662 the town held`, `29 people housed · of roughly 3,265`, `1,404 named residents · 526 attested · 878 inferred (719 projected) · 0 reconstructed`. Read top-down, the second row says the town is 0.9% peopled and the third row looks like a separate tally with nothing to do with 3,265. They are one ladder: 1,404 named is the numerator against the town's 3,265; attested and inferred are what has been earned so far; reconstructed is how the balance gets filled; and the 29 housed is a **placement** figure — residents standing inside a building that stands in the scene — not population coverage. Above all that, the ready line under the title reads `371 structures · sun 62.3° up, …` — 371 is `records_in_scene` (bridges, the pier, the palisade, the parade ground are records that are not buildings), so it contradicts the 359 on the card three lines below it.

**The change.**
1. **Strike `(719 projected)`** from the named-residents row. `projected_residents` stays in `data/residents/index.json` (T-0490 still reads it); it just no longer reaches the card.
2. **Strike `371 structures`** from the ready line in `main.js` (~line 2284). The line keeps `world.describe()` (sun elevation, local mean time, the target date); nothing else on the card counts structure records.
3. **Rebuild the census block as two parallel completeness rows of the same shape**, each a headline count over its denominator with a filled bar:
   - buildings — `359` standing of the `662` the town held;
   - people — `1,404` named of roughly `3,265` who lived here, the bar segmented **attested → inferred → reconstructed** in that order so the three grades read as portions of the named count filling toward the census total, not as a separate list. The grade legend carries the three numbers; reconstructed shows even at 0 so the third segment is visibly the one still to fill.
4. **Demote the 29 housed to a placement note under the people row** — wording in the spirit of "29 of them are placed in a building that stands" — with the existing `people.basis` + `town_total_note` titles kept for hover/aria. It is never again set directly against 3,265.
5. Every number still comes from `data/town_census.json` and `data/residents/index.json` at load (T-0036 / T-0490 rule); fail-soft stays — a missing source drops its row, never errors the first screen.

**Check before shipping.** The owner quotes 425 attested; `residents/index.json` on dev at 4f405bf6 carries 526 attested + 878 inferred = 1,404. The card must show what the data says; if 425 is the number the owner expects, that is a data question for the residents ledger, not a card edit — say which in the PR.

**Acceptance:** on the gate at 390×780 and desktop, both themes: no `projected` string and no `structures` string anywhere on the card; two bar rows with the numbers above, the people bar segmented by grade with a legend; the 29 housed appears only as a note under the people row; `gate-census` aria text reads the same story; `tools/check.sh` (which re-derives `town_census.json`) and the smoke gate green with zero pageerrors.
