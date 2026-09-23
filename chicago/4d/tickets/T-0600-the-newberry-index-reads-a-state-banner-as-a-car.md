---
id: T-0600
title: The Newberry index reads a state banner as a card body, and a wrecked call number as ', Ill.' — four and one of forty sampled cards
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-05
pr: 873
claimed_by: run 9/5/2026, 4:25:18 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T11:05:40.860Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33957706556
---

The Newberry index reads a state banner as a card body, and a wrecked call number as ', Ill.' — four and
one of forty sampled cards.

**Where it was measured.** T-0578's forty-card hand draw on volume 2 (`precision_sample.json`, block `2`).
Five of the forty are bad keeps and both classes are new — volume 1's draw surfaced neither.

**Class one, the state banner (four of the five).** The printed index divides one family's run of cards by
state with a rule: `ILLINOIS.` on its own line. `tools/read_newberry_index.py` assembles a card from a
heading line and the lines under it, so when that rule falls directly beneath a heading it becomes that
card's whole body, and `LOCALITY_BUCKETS` keeps the stanza on `illinois_named`. The stanza carries no
citation at all. `nbi_v02_1675` is the proof it does not belong to the heading above it: the heading is
'Kinge or King family.', whose one card is an English parish register, and the surname run that begins
under the banner is KINGERY. The others are `nbi_v02_0561`, `nbi_v02_1027` and `nbi_v02_0539`.

**Class two, the call number (one of the five).** `nbi_v02_1106` is 'Holden family. — Hapgood fam.
(Hapgood, W.) 1898. See index. E. 7. H 21' — a family genealogy naming no locality. The
`illinois_abbreviated` pattern matched on ', III,' out of the wrecked Newberry call number. It is the
sharper of the two: the banner at least names a true state, this names nothing.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- A rule in `tools/read_newberry_index.py` that refuses a stanza whose whole body is a bare state name
  or a bare state banner, on the same footing as `REGNAL` — written where REGNAL is, with its reason.
- A rule that refuses `, III,` when what precedes it is a call-number shape (a Newberry class letter,
  a number, a letter). State on the ticket which of the two classes each refusal covers.
- Volumes 1 AND 2 re-extracted and re-parsed against the new rules, in the same commit, with the count
  of cards that left each volume named in the PR — the PDFs are not committed, so the run fetches them
  from the Internet Archive item in `text/MANIFEST.json` and the MANIFEST sha256s must still match.
- Both volumes' precision samples RE-DRAWN and re-adjudicated. `--check` already fails when a sampled
  card leaves the records, which is the gate that forces this; a number carried forward is not a
  measurement of the new reading.
- The five cards named above are gone from the records, and the README's figures move with them.

**Effort.** S — the rules are small and the tool already has the shape for them (`REGNAL`). The bulk is
the two re-extractions (about a minute each) and the two re-draws.

**Links:** T-0578 (which measured it) · T-0570 (volume 1) · T-0562 (the parent read) ·
`data/research/newberry_index/precision_sample.json` block `2`, `found`.
