---
id: T-0113
title: The nightly bake refuses its own publish: 30 masters now compress smaller than their banked passthrough
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-20
closed: 2026-08-23
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

The nightly bake refuses its own publish: 30 masters now compress smaller than their banked passthrough.

The last three `chicago-4d-bake.yml` runs (32322062363, 32334547119, 32339944530, all
2026-08-20) end at the K38 web-derivative gate: ~30 `recon_1835_blk_south_water_*` masters
are "banked in web_derivative_baseline.json as a decided master passthrough and it is
compressed now", and the bake REFUSES TO PUBLISH — correctly. Nothing lands from any
nightly until this is settled. The committed tree itself still passes the gate
(`measure_web_derivatives.py --gate` is green on dev), so this is the bake's FRESH
regeneration disagreeing with the banked passthrough set: either a recent commit changed
those masters so they now compress smaller, or the toolchain moved under the pin. The
gate's own message names the remedy — re-run `python3 tools/measure_web_derivatives.py
--write-baseline` in the commit that moved the set — but do not run it blind: first say
WHY the set moved (which commit, which tool), because a baseline rewrite that cannot name
its cause is how a real regression gets banked as a decision.

**Acceptance:** the cause of the passthrough-set movement is named in the PR (commit or
toolchain, with the numbers); the baseline is regenerated in that light; the nightly bake
runs green end to end — bake, gate, publish, smoke — on its next scheduled run.

---

**2026-08-23 — SUPERSEDED BY T-0160, and this ticket should probably be withdrawn.**
This is the K38 web-derivative passthrough failure, and T-0160 (#331) settled it. The cause was
not a stale baseline and not a toolchain move: the bake was **discarding a real upgrade every
night**. 132 of 226 placeholders were already archetypes; the last 94 (median 6.5 KB, all
`extras.placeholder: True`) were rebuilt at 16.4× triangles, which flipped them out of K38's
banked passthrough set. The upgrade and the re-bank landed together — 93 passthroughs down to 3 —
and the nightly publishes again.

Left in the queue rather than withdrawn, because withdrawing another run's ticket on one reading
is a bigger step than re-ranking it. Withdraw if you agree.
