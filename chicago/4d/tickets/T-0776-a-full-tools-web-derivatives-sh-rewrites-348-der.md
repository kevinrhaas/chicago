---
id: T-0776
title: A full tools/web_derivatives.sh rewrites 348 derivatives with identical byte counts: the derivative step is not reproducible
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

A full tools/web_derivatives.sh rewrites 348 derivatives with identical byte counts: the derivative step is not reproducible.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found while shipping T-0686 (PR #882). A full `tools/web_derivatives.sh` on an otherwise
unchanged tree rewrote **348** files under `assets/web/`, every one of them with an
**identical byte count** to the version it replaced. Only two masters had actually changed.
Content-identical-but-not-byte-identical output means the derivative step carries state — a
temp path, an ordering, or a generator string — into its bytes.

It is not blocking, because `--only <name>` sidesteps it and that is what T-0686 used. It is
expensive: without `--only`, any run that rebakes one asset lands 348 unrelated binaries in
its PR, which is the shape of diff nobody reads.

**Acceptance:** running the full step twice on an unchanged tree produces byte-identical
output, demonstrated by two consecutive runs and a `git status` that is empty after the
second. If some part genuinely cannot be made deterministic, say which and why, and make the
step skip an asset whose master has not moved.
