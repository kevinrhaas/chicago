---
id: T-0865
title: PR #948 proposed deleting the Taylor brotherhood as unsourced and a committed source states it: land the tie instead
state: done
epic: TOWN
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-06
pr: 965
claimed_by: run 9/5/2026, 11:55:23 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T05:03:38.002Z
claimed_run: null
---

PR #948 proposed deleting the Taylor brotherhood as unsourced and a committed source states it: land the tie instead.

**Acceptance:** the tie stands on both cards under a written ruling, and the ruling
records that the sentence was nearly deleted as unsourced.

## What #948 proposed, and why it was wrong

PR #948 — the rival to #947 on T-0734, parked on `hold` and recommending its own
closure — listed among its contributions:

> **One sentence removed rather than added.** `hh_taylor_augustine` called him "one
> of two Taylor brothers in this parcel". **No source says it**, nine Taylors live
> here, and Anson's documented brother is Charles — a family invented out of a
> shared surname is what the acceptance forbids.

The restraint is exactly right and the fact is wrong. **A source does say it:**

- `data/research/residents/pass_02_findings.json` carries this project's reading of
  the Chicago History Museum's encyclopedia entry, which distinguishes Augustine
  Deodat Taylor from *"brother Anson who hauled lumber"*;
- `data/sources/encyclopedia_chicago_church_architecture.json` is a committed
  source record, `verified: true`.

So the sentence was not a family invented out of a shared surname. It was a
**cited kinship nobody had ever written as a link** — and deleting it would have
lost a family the corpus actually states.

## What shipped instead

The tie is landed both ways, `taylor_augustine` ⇄ `taylor_anson_h`, through the
authored-readings seam (T-0860): the entry quotes the encyclopedia summary and
names the file it stands in, so `survey_stated_kin.py --check` verifies the quote
is really there before the statement is allowed to exist.

**Graded `inferred`, not `attested`** — what the corpus holds is this project's
SUMMARY of the encyclopedia rather than a quoted page. That is the same restraint
the Beaubien brotherhood got, and the confidence is not raised to make the row look
better.

**The identification is not a surname match.** Five Taylor households stand in this
parcel; the source names Anson outright, so the tie reaches exactly one of them.

## What is NOT settled here

#948 also asserts "Anson's documented brother is Charles". Nothing found in this
pass states that, and it is not ruled either way — if it is true, Charles H. Taylor
and Anson H. Taylor are a second tie the corpus is sitting on, and it wants its own
reading rather than an inference from this one.
