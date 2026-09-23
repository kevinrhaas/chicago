---
id: T-1222
title: Read the letter-list mint's 798-file drift and give the pass a check the gate can run at its own place in the pipeline
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-17
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

Read the letter-list mint's 798-file drift and give the pass a check the gate can run at its own place in the pipeline.

**The parent's premise does not survive contact, and that is the finding.** T-0662 asked
for `tools/mint_letter_list_residents.py --check` as a step beside the other mints. It
cannot be one there. `tools/synthesize_resident_research.py` runs AFTER the mint and
rewrites `grade`, `resident_subtype`, `note`, `sources` and `resident_research` on every
letter-list person it projects — that rewrite IS the PROJECTED RESIDENT downgrade, and the
mint knows nothing about it. So a re-derive-and-diff at that point in the pipeline is red
against a CORRECT tree, and green only against one the projection has not run on.

Measured on `origin/dev`, 2026-09-17, over the 798 files the mint re-derives differently:

| what | files |
| --- | --- |
| differ in nothing but the five keys the projection owns | 648 |
| households the mint no longer derives at all | 81 |
| ids the name splitter now mints differently | 54 |
| mint-owned changes (`name`, `occupation`, `arrival`, `letter_list_returns`) | 14 |

`hh_abbott_constant` is one of the 81: `--report` names neither a mint nor a refusal for
Constant Abbott, so the candidate has left the corpus — the returns were re-read. The 54
are ids like `hh_adains_will_si` → `hh_adains_willisi`, which is the splitter's territory
and moves again under T-1155 and T-1217.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- A check the gate can run at the mint's own place in the pipeline: it compares what the
  mint OWNS, and states in the file which keys a later pass owns and why.
- The 81 withdrawals are read before they are written — a household the town loses is a
  reading, not a by-product — and the 54 re-mints are taken after the splitter tickets
  land, not across them.
- `check.sh` runs that check, green, so the pass cannot drift ungated again.
