---
id: T-1502
title: The register deal reads the raw text of every household card as a name pool, so any pass writing a proper name onto one can silently retire a documented man from it
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-21
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

The register deal reads the raw text of every household card as a name pool, so any pass writing a proper name onto one can silently retire a documented man from it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-1489, 2026-09-21, as a red gate rather than as a reading.**
`tools/replace_invented_residents.py` decides which documented men of the register may
head an anonymous roof. One of its refusals is `town_surnames()`: every
`\b[A-Z][a-z]{2,}\b` word in the RAW TEXT of every structure record and every
non-`hh_inf_` household card — prose, notes and all — is read as a name the town has
already said something about, and a candidate whose surname is in that set is refused.

The guard already knows it can poison itself: its own docstring says the `hh_inf_`
households are excluded precisely because reading back a name this pass wrote would
refuse that man on the next run. The hole is that the exclusion is by DIRECTORY
PREFIX, and nothing stops a different pass writing a proper name into one of the cards
that IS read.

T-1489 did exactly that by accident. Its `persons[].employment` block carried the house's
`business_name` beside its id, so 33 cards in `households/` gained the word `Eels` —
and the deal stopped seating the documented tailor **Thomas S. Eels** on
`hh_inf_tailor_north_02`, reporting "already named in the town (eels)". One gate step
caught it; nothing else would have. T-1489 answered for itself by dropping the name
(the id resolves to it in one lookup) and asserting in its own `--self-test` that no
value in that block may carry a capitalised word.

**What is still owed.** That assertion guards ONE writer. Any future pass that puts a
proper name into a household card — a landlord, an employer, a witness, a vessel's
master — retires a documented man from this deal silently, and the failure surfaces as
one unexplained DRIFT line in a step about something else. The answer is probably one
of: read the harvest from declared NAME FIELDS rather than from raw text; or keep a
declared list of the keys the harvest may read and gate it; or have the harvest state,
per refused candidate, WHICH file and which key the word came out of, so a collision
names its own cause. That is a decision about the guard, not a bug fix, which is why
this is a ticket and not a patch.
