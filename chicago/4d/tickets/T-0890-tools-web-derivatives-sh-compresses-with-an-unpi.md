---
id: T-0890
title: tools/web_derivatives.sh compresses with an unpinned `npx --yes @gltf-transform/cli`, so a runner with a newer CLI rewrites the generator string in all 380 web assets
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: duplicate of T-0537, which explains why pinning the CLI alone fails; its bake.sh --only note is carried in T-0537
needs_bake: false
closed_at: 2026-09-10T04:20:09.911Z
claimed_run: null
---

tools/web_derivatives.sh compresses with an unpinned `npx --yes @gltf-transform/cli`, so a runner with a newer CLI rewrites the generator string in all 380 web assets.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0881 (this run held T-0887, the split that lost the race to #984), 2026-09-06, on the steward runner.** `tools/web_derivatives.sh` compresses
every master with `npx --yes @gltf-transform/cli`, unpinned. The committed derivatives were
written by **4.4.2**; the runner resolved **4.5.0**, and a full pass therefore rewrote the
`asset.generator` string in every file it touched — same byte length, same geometry, 145 files
dirty in the working tree before the run noticed. They were reverted and only the two new
assets kept, so nothing shipped, but the next run that calls `bake.sh` without watching will
put a 380-file no-op diff in its PR.

Two things follow from it, and only the first is this ticket:

1. **Pin the CLI**, `@gltf-transform/cli@<version>`, in `web_derivatives.sh`, from the version
   the committed assets were actually written with. Determinism here is already declared on
   INPUTS (`assets/manifest.json`); the compressor is an input and is not pinned, while Blender
   is pinned by version AND sha256 two files away.
2. `bake.sh --only <id>` bakes ONE mesh and then runs the web-derivative pass over **all 380**,
   `compile_scene --all`, `publish.sh`, `check.sh` and — unless `SKIP_SMOKE=1` — the full
   ~25-minute smoke. On a run with a tool-call budget that is a trap: the one-structure path is
   `generators/build.py -- --only <id>` plus `web_derivatives.sh --only <name>.glb`, and the
   `.glb` on the end is required (the loop compares full basenames, so `--only <name>` silently
   matches nothing and prints only its banner). Worth a line in AGENTS.md § the bake.

**Acceptance:** the pin is in the script with the version stated and reasoned; a re-run of the
full pass on a clean tree leaves `assets/web/` untouched.
