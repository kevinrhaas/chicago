---
id: T-0820
title: A duplicate in a keyed list takes dev red instead of failing the branch that wrote it: assert unique ids on streets, tickets and coverage declarations at the branch's own gate
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: 906
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T18:21:54.344Z
claimed_run: null
---

A duplicate in a keyed list takes dev red instead of failing the branch that wrote it: assert unique ids on streets, tickets and coverage declarations at the branch's own gate.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

## Why now

`dev`'s gate went red TWICE on 2026-09-05, and both times the cause was a
duplicate in a keyed list:

- **04:00Z** — two branches each minted ticket id **T-0739**. Fixed in #863.
- **~16:00Z** — #882 committed a second, **byte-identical** `west_water` entry
  to `data/streets/1835.json`, because its branch was cut before #875 landed the
  first one. Fixed in #889.

Neither was caught on the branch that wrote it. Both were caught by `check.sh`
running against `dev` AFTER the merge — which is the expensive place to find it,
because the dev gate is the base every open PR inherits. On the morning failure
that meant nineteen PRs sat on `hold` saying "dev is red before this branch".

**This gets worse, not better, once `dev` carries a required status check.**
Today a red `dev` blocks work by discouraging merges; with a ruleset it blocks
them outright.

## What to assert

A branch's own gate should refuse a duplicate id in any keyed list it touches.
Known lists, from the two failures and the near-misses beside them:

| file | key |
|---|---|
| `data/streets/1835.json` | `streets[].id` |
| `tickets/*.md` + `tickets.json` | `id` (already caught by `ticket.mjs check`) |
| `data/research/*/coverage.json` | `declarations[].items[]` |
| `data/research/newberry_index/records/entries_vol_*.json` | `records[].id` |
| `tools/research_spend_baseline.json` | `raised[]` — see the note below |

## What NOT to assert

`raised[]` in `research_spend_baseline.json` legitimately holds several entries
for one domain — each is a separate dated decision with its own reasoning. The
rule there is not "one entry per domain" but "no two entries identical". The
same care applies anywhere an append-only ledger is keyed by something other
than identity; the assertion must be about DUPLICATES, not about uniqueness of a
grouping field, or it will refuse honest history.

## Acceptance

- A fixture with a duplicated street id fails the gate, and the failure names
  the file and the id.
- The assertion runs on a BRANCH, not only against `dev`.
- `raised[]` with two entries for one domain still passes.
- `tools/check.sh` carries it, and a self-test proves it fires when broken.
