---
id: T-0558
title: smoke_budget.mjs prices the publish stamp site/chicago/4d/walk/index.html at all 13 parts, so every publishing PR is told to run the whole gate
state: done
epic: META
requested_by: owner
seen: false
effort: XS
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-03
pr: 701
claimed_by: null
blocked_on: null
needs_bake: false
---

smoke_budget.mjs prices the publish stamp site/chicago/4d/walk/index.html at all 13 parts, so every publishing PR is told to run the whole gate.

**Filed on the owner's instruction of 2026-09-03** ("A couple fails, can you correct for future") after steward
run #1464 was read: it changed two census page files, `smoke_budget.mjs --for-diff` correctly named parts 11-13
for them — and then also said "parts to run: 1-13", because `publish.sh` rewrites the build sha and Central date
into `site/chicago/4d/walk/index.html` on every run, and the only row matching that path was the mirror
catch-all (`site/chicago/4d/` → ALL). The run obeyed, ran seven legs, overran the 600 s cap on the fifth, and
died on an API 500 before it could open a PR. `site/chicago/4d/build.json` already had a NONE row for exactly
this reason; the stamp in the HTML did not.

**Acceptance:** (one demonstration, never weakened to pass)
- A `NONE` row for `site/chicago/4d/walk/index.html` with its reason, beside the `build.json` row.
- `--self-test` asserts the stamp maps to no part AND that a real mirrored module (`walk/js/main.js`) still maps
  to the whole gate — the map may only ever ADD parts, and this row must not become a hole.
- `--for site/chicago/4d/walk/index.html` prints NO PART; `--for-diff` on a data-only PR names the data parts
  and nothing else; `check.sh` (which runs the self-test) green.

**Not changed:** the mirror catch-all, which is right for every real file under `site/chicago/4d/`.
