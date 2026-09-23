---
id: T-1050
title: One back-projected home stands on Clark Street off 'h Clark st. b Mad. & Mon', where the R4 qualifier clause cannot read Norris's abbreviation of a street the town does not have
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-11
closed: 2026-09-14
pr: 1316
claimed_by: run 9/14/2026, 2:28:10 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T07:58:52.216Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34817655906
---

One back-projected home stands on Clark Street off 'h Clark st. b Mad. & Mon', where the R4 qualifier clause cannot read Norris's abbreviation of a street the town does not have.

**Acceptance** (stated 2026-09-14, before working — the definition of done, never
weakened to pass):

1. `h Clark st. b Mad. & Mon` and `h Clark, b Madison and Monroe` — the same address, two
   spellings, three lines apart in Norris's own column — get **one verdict for one
   reason, word for word**. Both are refused under R4's second half. Asserted by
   `--self-test` comparing the two `reason` strings, not by the prose saying so.
2. The contractions the table gains are **attested and bounded**: each one quoted off a
   page, each expansion unique on the 1844 street list, and every occurrence of every
   token across all 4,235 addresses the four volumes print is that street. Three are
   `documented` by Norris's REMARKS page; the rest are `inferred` from its `&c.` with the
   uniqueness as the stated reasoning. A contraction that CANNOT be decided is declared
   and left unread rather than guessed (`Wat` — North or South Water).
3. The expansion lives in ONE place, ahead of both street tables, so the two passes cannot
   disagree about a contraction the way they could never disagree about `Michigan ave`.
4. Both ledgers re-derive and every outcome that moves is named — in the policy docs and
   in L223, with the count restated and the withdrawn face said out loud. A refusal that
   stops reasoning off the wrong street counts as a move even where its verdict does not
   change.
5. `./tools/check.sh` green, both `--self-test`s green, the mirror published in the same
   commit.

**Done, 2026-09-14.** All five hold. The measured effect is two entries of 57 and the
business pass's ledger is byte-identical: Rebecca Sherman comes off Clark Street, and John
Harris Kinzie's refusal stops making Cass the head street of a house that stood on
Michigan Street. Fourteen contractions are read where none was; the scanner's word-splits
(`Wash ington`, `Ran dolph`, `Dear-. born`) fall out of the same table, because the first
half of a broken name looks exactly like the contraction Norris declares; and `;ind`, this
OCR's rendering of `and`, does not become Indiana Street, because a contraction is read
only where the page sets it as a word of its own.
