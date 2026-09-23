---
id: T-0263
title: The documented storefronts take their places on South Water and Lake
state: done
epic: PAPERS
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-29
pr: 554
claimed_by: run 8/29/2026, 12:21:53 PM CT
blocked_on: T-0262
needs_bake: false
---
**VISIBLE.** The register (T-0262) names documented businesses placeable
against committed anchors. This ticket puts the first batch into the town —
on South Water and Lake Streets, where the anchors (Newberry & Dole, the post
office, the named stores of T-0198/T-0199) already stand.

## The owner's three rulings, 2026-08-28 — every ticket in this epic works under them

1. **A letter-list name is enough to mint a resident.** The post-office letter
   lists name people by the hundred; the owner ruled a listed name alone makes a
   resident candidate, not merely a gazetteer entry. Record `letter_list_only:
   true` so the two evidence strengths stay distinguishable forever.
2. **Transcription-mediated readings grade `documented`, carrying a flag.** The
   corpus is read through OCR-assisted transcriptions, not the page scans. Every
   claim taken this way carries `reading: transcription_mediated` and preserves
   the transcription's own uncertainty brackets. This EXTENDS, and does not
   overturn, `data/sources/chicago_democrat_1833_11_26.json`'s standard — where
   a scan exists and is read, the scan remains the authority (it caught 'C. & I.
   HARMON' where the transcription had 'C. & L. Harmon'), and a
   transcription-mediated claim upgrades when a scan read confirms it.
3. **A documented business is BUILT at the scene date unless contradicted.** A
   dissolution, removal or replacement notice is the only thing that keeps a
   documented business out of the 1835 town. A business whose last evidence is
   1833-1834 is built WITH a survival liberty stated on the record (existence
   documented, survival to 1835-07-01 assumed) — docs/LIBERTIES.md carries it.


## The work

Work from `register_1835.json` actions, batch of at least five:

- **`enrich_existing`**: the committed record gains the documented trade,
  proprietor names and citation; trade grade moves to `documented` with
  `reading: transcription_mediated`. A documented trade makes the building
  eligible for its SIGNBOARD and HITCHING POST under the existing rules
  (`generate_business_signboards.py` PUBLIC_TRADES; T-0194's post rule) — that
  is the visible change, and it is the existing generators doing it, not new
  ones.
- **`new_building`**: a structure record through the existing pipeline. The
  position derives from the ad's own words — "a few doors below X" places the
  building on X's block face at a stated door-width offset (use the committed
  party-line unit width as the door module and SAY SO in position.note, with
  the ad quoted verbatim); grade `inferred`, `derivation` naming anchor +
  offset judgment. Massing per the existing archetype rules for its trade;
  existence documented, massing reconstructed — exactly the K20b split. A
  LIBERTIES entry per invention class, and the survival liberty where the
  register flags it. The lot question goes through `plat_occupancy` and the
  owner's business-front clause like every other roof.
- Changelog entry — this one is FOR THE VISITOR: named, documented storefronts
  with citations on their cards, where the record was invented before.

## Bounds

- Placement inference NEVER displaces a committed documented building; a
  collision is a finding for the register, not a nudge (the T-0196 pattern —
  refuse in writing with the numbers).
- Triangle ceilings and draw-call budgets hold at T-0135's five stands — the
  street-edge tickets' own measurements are the precedent for what a refusal
  looks like (T-0193).

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- ≥5 register businesses placed or enriched, each card carrying the citation
  (publication, issue, page/column) and the quote its placement rests on.
- Signboards/hitching posts appear where the rules now qualify the building —
  screenshot-different at a named stand.
- Every gate green: check.sh, ceilings, smoke per dev's standing record; the
  mirror republished.
