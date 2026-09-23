---
id: T-0835
title: The Newberry leads re-parse to 8 fewer cards from unchanged card text, so the parser moved under leads.json and the fingerprint gate could not see it
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-17
pr: null
claimed_by: null
blocked_on: folded into T-1291
needs_bake: false
closed_at: 2026-09-17T19:18:46.845Z
claimed_run: null
---

The Newberry leads re-parse to 8 fewer cards from unchanged card text, so the parser moved under leads.json and the fingerprint gate could not see it.

Found by T-0431, which added two structure records and was forced to re-derive `leads.json`
by the T-0740 fingerprint gate.

**What happened.** `parse_fingerprint()` hashes three things: the committed card text, the
WORKS table, and `layer_names()` — and the layers include the named structures. Adding ANY
structure record therefore invalidates the fingerprint and forces
`read_newberry_index.py --parse --volume 1..4` plus `rule_newberry_leads.py --write`. That is
the gate working as designed.

**What the re-parse revealed, which is not.** With the card TEXT byte-identical, a fresh parse
of all four volumes produces **6,720 cards where the committed leads claim 6,728**, and
**4,598 distinct surname keys where they claim 4,603** — so 980 leads instead of 981, and
`lead_crosswalk.json` loses 106 lines. One named casualty: `lead_v01_broone_census_1840`
(card `nbi_v01_0920`, OCR variant of Boone at 0.91 similarity) is gone, and `nbi_v01_1517`
drops out of another lead's entries.

Card text did not move, so the LAYERS cannot explain a card-count change: **the parser moved
under the committed file, and the fingerprint cannot see its own code.** It hashes the WORKS
table (T-0582's case) but nothing else about `read_committed_cards()` / `parse()`.
`leads.json` was last written by T-0415 (#898), after T-0740 built the fingerprint, so the
drift is somewhere after that.

T-0431 shipped the re-parse because the gate refuses without it, and named the delta in its
PR rather than absorbing it silently. Nobody has decided whether the eight cards SHOULD have
gone.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The eight cards and five surname keys are identified, and it is stated whether losing them
  is a repair or a regression — with the parser change that caused it named.
- The fingerprint covers the parser it is a fingerprint OF, so a code change to
  `read_committed_cards()` / `parse()` fails the gate the way a WORKS edit already does.
- The self-test gains a case that fires when the parser moves and the card text does not.

**Links:** T-0431 (found it) · T-0740 (the fingerprint) · T-0415 · T-0601 · T-0582 ·
`tools/read_newberry_index.py`.
