---
id: T-0408
title: Four spellings of one Lake Street trade take four separate roofs, and the identity layer has judged none of them
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-12
pr: 1173
claimed_by: run 9/12/2026, 12:30:45 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T05:59:08.830Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34674841397
---
Measured on 2026-08-29 by `tools/adopt_street_faces.py --report`, building T-0354's
street-face adoption. Four `street_only` businesses in the register advertise a Lake
Street trade inside five months, each under a different spelling of what reads as one
name, and the gazetteer's identity layer has judged none of them:

| register entry | proprietor as printed | first issue | mentions |
|---|---|---|---|
| `Wm. G. Branchaud` | Wm. G. Branchaud | 1834-06-11 | 1 |
| `W. G. Blanchard` | W. G. Blanchard | 1834-07-09 | 1 |
| `G. Blanshard` | G. Blanshard | 1834-10-08 | 1 |
| `F. G. Blanshard` | F. G. Blanshard | 1834-11-12 | 1 |

`identity.json` carries 177 person merges, 29 refused merges, 4 firm merges and 6
proprietor merges, and **not one of them names any of these four**. So this is an
unjudged group rather than a decided distinction.

**What it costs, and why it is not T-0338's.** T-0338 is thirty-one groups of FIRMS that
share a partner surname — a different question, answerable from the firm's own partners.
This is one surname under four TRANSCRIBED SPELLINGS, which no exact-string rule can
reach. T-0354's adoption pass refuses a second roof to a proprietor surname it has
already seated on a face (that is what caught 'F. G. Blanshard' behind 'G. Blanshard'),
and it deliberately does NOT match by resemblance, because deciding that Branchaud is
Blanshard is a reading of the printing and belongs to the gazetteer. The consequence is
that **three Lake Street roofs are adopted for what is probably one house**, and the
seeding tickets will stand three storefronts where the papers support one.

**What would settle it:** the page images for the four issues, read against each other —
the same remedy T-0331 and T-0305 name for their own contested readings. The Democrat set
this project holds is transcribed, and a compositor's spelling of a French-looking name is
exactly what a transcription loses. If they are one man, the merge carries a `merge_rule`
in `identity.json` and the adoption pass drops from 22 to 20 without being touched.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- The four entries are either merged in `identity.json`, each merge carrying its own
  `merge_rule` and the witnesses it rests on, or declared distinct in
  `refused_merges`/`proprietor_distinctions` with the reason.
- The decision cites the printing it was made from, not a resemblance.
- `python3 tools/adopt_street_faces.py --check` is green afterwards and its adopted count
  is restated in the PR.
