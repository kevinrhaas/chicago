---
id: T-0537
title: The web derivatives are stamped by an unpinned gltf-transform, so a release upstream restamps all 372 of them
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-16
pr: 1372
claimed_by: run 9/16/2026, 11:38:18 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T01:49:28.500Z
claimed_run: null
---

The web derivatives are stamped by an unpinned gltf-transform, so a release upstream restamps all 372 of them.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

`tools/web_derivatives.sh` shells out to `npx --yes @gltf-transform/cli` with no version
on it, twice per asset (`optimize`, then `meshopt`). npm resolves that to whatever is
latest at the moment the command runs, so the bytes the step produces are a function of
the calendar rather than of the tree.

**Measured on 2026-09-03, on the steward runner, during T-0430.** A bake ran the step over
the committed masters and rewrote ALL 372 derivatives. The diff per file was TWO BYTES:

    committed:  {"asset":{"generator":"glTF-Transform v4.4.2", ...
    regenerated:{"asset":{"generator":"glTF-Transform v4.5.0", ...

Nothing else moved — same triangles, same accessors, same sizes. `@gltf-transform/core`
shipped 4.5.0 since the committed set was produced, and `@gltf-transform/cli` depends on
it by caret, so pinning the CLI to 4.4.2 does NOT pin the stamp: run with
`npx @gltf-transform/cli@4.4.2` and the output still reads v4.5.0, which is how this was
confirmed rather than guessed.

**Why it matters, and it is not the two bytes.** The header of that same script states the
determinism claim this project relies on — "running this over the committed masters
reproduces all 334 committed derivatives exactly, md5 for md5, on gltf-transform 4.4.2" —
and `tools/measure_web_derivatives.py` is built on being able to re-derive a shipped
derivative from its master. An unpinned toolchain means any run that touches ONE building
can land a 372-file binary diff that reviews as noise and buries whatever it was carrying.
T-0430 worked around it by regenerating only the eight derivatives whose masters had
actually changed and reverting the rest, which is a workaround and not a fix: the next
bake nightly does the full pass and lands the churn anyway.

**What to decide (and it is a fork worth stating rather than assuming).**

1. PIN IT — an exact `@gltf-transform/cli@X.Y.Z` AND an exact `@gltf-transform/core`,
   the way `generators/blender.pin` pins Blender by version and sha256. That is the
   shape this repo already uses for its other stateful tool, and the reason is the same
   one written at the top of `bake.sh`: version pinning is what buys back determinism.
2. MOVE THE TOWN TO THE CURRENT RELEASE in one deliberate commit that does nothing else,
   then pin at that version. The churn is 372 files either way; the question is whether
   it is ever allowed to arrive as a side effect again.

Either way the pin belongs beside the claim it protects, and the claim in the script's
header should say which version it was measured on and where that version is fixed.

**Acceptance:** `tools/web_derivatives.sh` names an exact version for every tool it
shells out to; running it twice on an unchanged tree, on two different days, produces
byte-identical derivatives; and the header's md5-for-md5 sentence names the pin it
holds true under.

**Links:** T-0430 (where it was found) · `tools/web_derivatives.sh` ·
`tools/measure_web_derivatives.py` · `generators/blender.pin` (the pattern) · K36(b) · K39.

## The release landed — measured 2026-09-13 on T-0332's branch

This is no longer hypothetical. T-0332's town-wide rebake ran `tools/bake.sh`, whose
`web_derivatives.sh` leg resolved `npx --yes @gltf-transform/cli` to **4.5.0**; the committed
derivatives were written by **4.4.2** (the version the script's own comment at line 19 names).

| reading | |
|---|---|
| `assets/web/*.glb` rewritten | **196 of 384** |
| bytes differing in a sampled file | **2** — `"generator":"glTF-Transform v4.4.2"` → `v4.5.0` |
| masters (`assets/gltf/`) changed | 0 |

So the churn is the stamp and nothing else, and it is now unavoidable on this runner: any bake
that regenerates derivatives drags 196 unrelated files into the PR. T-0332 dropped them
(`git checkout -- assets/web`) because zero masters moved, so no derivative needed rebuilding —
that dodge works only while a bake changes no geometry, and the next one that does will not have
it. Pin the CLI.
