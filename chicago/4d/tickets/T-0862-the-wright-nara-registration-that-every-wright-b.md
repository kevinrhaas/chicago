---
id: T-0862
title: The Wright NARA registration that every Wright-band ticket is built on has no gate: nothing verifies its raster, its checksum or its fit
state: done
epic: PAPERS
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-12
pr: 1215
claimed_by: run 9/12/2026, 5:36:52 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T22:53:33.418Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34723073050
---

The Wright NARA registration that every Wright-band ticket is built on has no gate: nothing verifies its raster, its checksum or its fit.

**Acceptance:** `tools/check.sh` carries a step that re-verifies the NARA
registration against the working copy and refuses a hand edit, with a self-test
proving it fires.

## Where this came from

PR **#957** and **#956** were rival runs at T-0787. #956 landed. #957 was parked
and its title claimed *"a measured registration and a gate the merged one lacks"*.
**Checked before closing it, and the claim is true.**

`dev` carries both data files —

- `data/sources/wright_1834_nara_hup.json`
- `data/traces/gcp/wright_1834_nara_hup_gcps.json`

— and **`tools/check.sh` contains no step referencing either.** `grep -i "nara"`
over the committed gate returns nothing but unrelated Playwright comments. The
registration is ungated: a hand edit to a coefficient, a residual or the checksum
would pass every gate this project has.

**That matters more than one file.** T-0787 is the enabler the whole Wright band
(T-0788 … T-0795) is waiting on — at 600 dpi the block numerals are legible where
the BPL scan's are not — so every ticket in that band will rest on numbers nothing
currently re-derives.

## It is cheap, and this was measured rather than assumed

The offline half needs no numpy, no scipy and no network. Verified on the
committed tree while writing this ticket:

| the record claims | checked |
|---|---|
| working copy `chicago/pre_fire_v1/maps/images/1834-wright-map.jpg` | **present** |
| `sha256: dbb92c01…73266` | **matches, exactly** |
| `1834-wright-map-lg.jpg` is byte-identical to it | **true — same sha256** |

So a `--check-properties`-style step can assert: the raster is where the record
says, its checksum still matches, its declared 5050 × 6628 / 600 dpi agrees with
the file, the duplicate claim still holds, and the affine's stated
`scale_m_per_px` re-derives from its own coefficients. All of that is arithmetic
and file reads.

The expensive half — re-fitting the correspondences off the raster — is the
deliberate second tier, exactly as `trace_river.py` splits `--check-properties`
from a full re-trace.

## Note on the two registrations

#956 and #957 registered the same sheet by different methods — #956 with 8 GCPs
(`rms_m: 16.19`), #957 with 20 patch correspondences located by normalised
cross-correlation (`rms_px: 6.9`). **This ticket is not a proposal to replace
what landed.** It is a gate over what landed. If the two fits are ever to be
compared that is its own reading, and #957's branch is where the alternative
lives.

## Acceptance

- A step in `tools/check.sh` re-verifies the committed registration and **fails on
  a mutated residual, coefficient or checksum** — proved by a self-test, the way
  #957 proved its own ("a mutated `residual_px` is refused by name").
- It **skips rather than fails** when the working copy is absent, since the raster
  lives outside this app's subtree in `chicago/pre_fire_v1/`.
- The `-lg` duplicate finding stays asserted rather than recorded in prose only.
