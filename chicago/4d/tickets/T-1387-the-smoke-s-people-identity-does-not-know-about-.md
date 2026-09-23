---
id: T-1387
title: The smoke's people identity does not know about the 87 Native and Métis cards, so part 12 is red at both viewports on dev
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-19
closed: 2026-09-19
pr: null
claimed_by: null
blocked_on: duplicate of T-1373, which is the same red with the same arithmetic and was filed first
needs_bake: false
closed_at: 2026-09-19T13:13:58.575Z
claimed_run: null
---

The smoke's people identity does not know about the 87 Native and Métis cards, so part 12 is red at both viewports on dev.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**MEASURED ON `origin/dev` ALONE, 2026-09-19, from T-1325's run.** A clean worktree
at `origin/dev` (3c1a0dfe), published and run at `SMOKE_VIEWPORT=mobile
SMOKE_STAGE=12`, fails exactly two checks, and the payloads are byte-identical to
the ones a branch on top of it sees:

    the People directory lists the town, and its count is the file's and the manifest's
      {"stated":3028,"manifest":2144,"readmitted":182,"trades":308,"transients":307}
    the tavern-keeper pill narrows the list to tavern keepers
      {"all":3028,"matched":8,"pressed":"","rows":8}

**The first is this ticket.** The check asserts an identity its own comment states:
the directory lists the manifest's people PLUS every cohort the reconstruction
minted outside `data/residents/households/`, *"and nothing else has a path into
it"*. 2,144 + 182 + 308 + 307 = **2,941** against a stated 3,028 — a gap of **87**,
which is exactly the men T-1376 (#1511, merged 2026-09-19 11:28 UTC) carded from
the 1832 Chicago roll. T-1347 and T-1353 each extended the sum when they added a
cohort; T-1376 added one and did not, so the check is measuring an identity that no
longer names every term. The fix is a term for the Native and Métis cards, read off
the file the way the other four are — not a loosened assertion.

**The second is T-1382**, already open and in flight: `pressed: ""` is the Trade
row failing to offer `tavern_keeper` at all, because T-1347's 308 reconstructed
trade heads pushed the town's tavern keepers off the ten commonest trades. Filed
here only so the two reds a run meets at part 12 are both accounted for.

Neither is attributable to a branch: the record (`tools/dev-smoke-state.mjs ask
--viewport mobile --stage 12`) has part 12 last passing at 2026-09-19T02:04Z, and
eleven commits have landed on dev since.
