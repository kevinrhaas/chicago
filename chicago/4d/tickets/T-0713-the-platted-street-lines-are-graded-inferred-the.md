---
id: T-0713
title: The platted street lines are graded inferred; the owner rules them attested from the Thompson plat
state: done
epic: GROUND
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: 840
claimed_by: run 9/4/2026, 10:26:22 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T13:05:44.888Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33941742113
---

The owner, 2026-09-04: make the street lines show as **attested** — they are on the Thompson plat. Today the sixteen platted streets in `data/streets/1835.json` are `geometry_confidence: inferred` and none cites `thompson_plat_1830`. Left in the queue for the loop; not built in the drawer PR.

**The change.** Set `geometry_confidence: "attested"` on these sixteen ids (verified against the file 2026-09-04): `south_water, lake, randolph, washington, market, franklin, wells, lasalle, clark, dearborn, state, canal, clinton, kinzie, wolcott, michigan_north`. Add `thompson_plat_1830` to each `sources`, keeping `wright_1834` / `hathaway_1834` / `chicago_dpw_1891_streets` / `osm_streets_2026` as they stand (Wolcott has no `wright_1834` — do not add one). `surface_confidence` and `wear_confidence` unchanged: the plat attests where a street *ran*, not its surface or wear.

**Not upgraded, and why.** `north_water`, `fort_road`, `fort_bank_track` stay `reconstructed` — a line derived from the committed bank and two invented fort tracks the plat does not draw. Dev's newer `carroll` stays `inferred`: its note says the tier does not survive inside the plat and its line is *interpolated* between Kinzie and Fulton with a 5.24 m bracket. `fulton` already cites the plat and is held by four surviving intersections at RMS 0.35 m, the tightest fit in the file — upgrade it with the sixteen, and say so in its note.

**Each upgraded note** must say the 17.5 m RMS georeference residual (`data/datum.json` `derivation.residual_m`) is *coordinate uncertainty* — how well the 1834 sheet warped onto modern ground — not a grade: the plat states the street stood on that line, which is what `attested` means here. Re-read each note for `tools/audit_confidence.py`'s SILENCE words ("no source", "assumed", "conjectur…"); an attested field hedged that way contradicts itself.

**What the picture will not do by itself — measured.** `streets.js` grades a ribbon by the WEAKEST of geometry/surface/wear (T-0100), and every street carries `wear_confidence: reconstructed`, so upgrading the line alone moves no pixel. The owner asked for a visible outcome, so the loop must also decide how the ribbon composes its grade — the honest shape is that the LINE's grade decides whether the ribbon stands (presence, dither) while surface and wear grade only the track texture on it. A `streets.js` decision with `test_street_confidence.mjs` restated, never weakened (an invented line still dithers out under an attested surface) — not a licence to touch `wear_confidence`.

**Acceptance:** `python3 tools/validate.py --all`, `python3 tools/audit_confidence.py`, `node tools/test_street_confidence.mjs`, `python3 tools/measure_street_line.py --gate` green; in the confidence view (`#btn-confidence`) the platted streets stand at full confidence and hiding `inferred` leaves them standing while `carroll` and the fort tracks drop — asserted in the smoke, both viewports, zero pageerrors; one changelog entry (`v: null, ts: '', date: ''`, stamped before merge); a STATUS section naming the composition decision; `tools/publish.sh`.

**2026-09-05 — built, and parked.** PR #840 into `dev` carries the whole ticket: the seventeen upgraded lines, the composition split in `streets.js`, `test_street_confidence.mjs` restated, two new smoke assertions passing at both viewports, the changelog entry, the STATUS section and the publish. It is on `hold` behind two blockers that are not this branch's — T-0727 (the published tree has 944 bytes of headroom under the 32 MiB budget, and the mandatory sidecar recompile alone costs 7,207) and T-0728 (dev's `check.sh` is red on nine steps before any branch touches it). Land those and #840 merges as it stands. **Do not rebuild this ticket** — read the branch.
