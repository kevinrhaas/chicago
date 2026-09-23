---
id: T-0186
title: LIBERTIES.md has no merge driver and no duplicate check, so two branches that each append L-NNN merge clean
state: done
epic: META
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-08-27
pr: 405
claimed_by: run 8/27/2026, 10:23:21 AM CT
blocked_on: null
needs_bake: false
---

LIBERTIES.md has no merge driver and no duplicate check, so two branches that each append
L-NNN merge clean.

## What happened

2026-08-24, merging `steward/t-0094-fort-pickets` onto dev. Both that branch and dev's
T-0104 had taken **L177**:

    ### L177 — The point on a Fort Dearborn picket is ours, and the plate ... rules a flat top
    ### L177 — The Lake face's street line is 0.80 m, and the plat module's lot margin gives way

`docs/LIBERTIES.md` **auto-merged**. Git reported no conflict, because the two additions
landed in different parts of a long file and neither touched the other's lines. The result
was a committed ledger with two entries carrying the same number, and nothing said so.

It was caught by reading the merged file, not by any gate. `tools/check.sh` was green
across it: `compile_liberties.py` compiled 179 liberties happily, and the liberties gate
checks that `data/liberties.json` matches its markdown — which it did, duplicates and all.

## Why this is the changelog's problem, already solved once

`js/changelog.js` is the same shape of artifact — a numbered ledger every branch prepends
to — and this project already learned this lesson there. It has THREE defences:

1. `.gitattributes` keeps the merge itself from silently interleaving,
2. entries are authored with `v: null` and numbered by `tools/stamp-changelog.mjs` at merge
   time, precisely "because two branches that each guess top + 1 both get it wrong", and
3. `tools/check-changelog.mjs` parses the result and fails on a malformed literal.

`docs/LIBERTIES.md` has none of the three. It is hand-numbered, has no merge driver, and
its gate compares the markdown to its own compiled output rather than checking the
numbering. The changelog's own contract note says why that is not enough, and the liberty
ledger was never given the same protection.

A conflict is SAFE, because it stops you. A clean merge of two appends to a numbered
ledger is silent, and only a human reading the file catches it.

## Corrected: there are no standing duplicates, and the reason matters

An earlier draft of this ticket claimed L4, L31 and L36 were already duplicated on dev.
**That was wrong, and the mistake is instructive enough to keep.** It came from counting
with `grep -oE "^### L[0-9]+"`, which truncates the ledger's LETTERED SUB-ENTRIES — L4a,
L31a through L31g, L36a — down to their parent number and reports them as repeats. Nine
such sub-entries exist. Counted correctly, with `^### L[0-9]+[a-z]*`, **dev has no
duplicate liberty numbers at all** once today's two were resolved.

So a duplicate checker has to know that `L31` and `L31a` are different entries, and that
a sub-entry is deliberate rather than a collision. A naive numeric check will cry wolf
nine times on the current file — which is worse than no check, because a gate that is
always red gets switched off.

## The instances that ARE real, all from one afternoon

- **L177** — the fort's picket head and T-0104's Lake-face street line, both appended, file
  auto-merged clean, duplicate committed.
- **L179** — the fort's picket head (after renumbering) and T-0107's west-bank landing, the
  same way, hours later.
- **L178** — not a duplicate but the same class of silence: Dearborn's worn track, appended
  at end of file, landed under the trailing `## Resolved` heading, which the liberties gate
  EXEMPTS from its still-an-invention check. A live invention filed as discharged.

All three were found by a human reading the file. `tools/check.sh` was green across every
one of them.

## The fix, roughly

Pick from what the changelog already proves works, rather than inventing something new:

- a duplicate check in `tools/check.sh` — the cheapest half, and it would have caught this
  one and the three standing duplicates;
- `.gitattributes` treatment so the merge itself stops being silent;
- optionally, author with a placeholder and number at merge, as the changelog does — the
  most robust and the most disruptive, since liberty numbers are cited from records,
  tickets, STATUS.md and research docs, so a renumber has to carry its references (this
  run had to move four of them by hand).

Whichever is chosen, the three standing duplicates are the acceptance test.

## Acceptance

- `tools/check.sh` fails on a duplicate liberty number, and is demonstrated failing by
  introducing one deliberately and removing it again.
- The check distinguishes a lettered sub-entry (L31a) from a duplicate of its parent
  (a second L31), and is demonstrated staying green on the nine sub-entries the file
  already carries.
- The `## Resolved` exemption is closed, so an entry appended at end of file cannot land
  in it silently — L178 got there that way and was moved by hand.
- If a merge driver or a stamp step is adopted, the reason is written next to it the way
  the changelog contract's is.
