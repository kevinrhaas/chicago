---
id: T-0386
title: W. Montgomery's new auction and commission room takes David Carver's old stand on South Water Street
state: blocked-tech
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: T-0306
opened: 2026-08-29
closed: null
pr: null
claimed_by: run 8/29/2026, 2:33:12 PM CT
blocked_on: T-0414 first (the street-face adoption refuses W. Montgomery for being L. W. Montgomery, against identity.json's own two_houses ruling), which in turn wants T-0009's roofs because South Water Street is out of supply. Both of the paper's own anchors are exhausted: the town holds no Carver building and can hold none, and J. Wright's two buildings stand at invented positions on Randolph Street. The ticket's stated prerequisite - an anchor that refuses ambiguity instead of taking the first - shipped in this PR.
needs_bake: true
---

W. Montgomery's new auction and commission room takes David Carver's old stand on South Water Street.

Piece 4 of 5 of **T-0306 — The American names six Chicago storefronts with usable placements and none of them is standing in the model yet**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance, stated before working (2026-08-29):** the register never resolves an
anchor onto one of several records that answer to the same name. Where two or more
committed structures — or two or more documented businesses — carry the anchor's exact
identity-word set, the anchor resolves to a new kind, `ambiguous`, naming every rival,
instead of `structure`/`business` on the alphabetically first. Demonstrated on this
ticket's own blocker, `J. Wright's`. **Delivered in PR #563.** That was this
ticket's stated prerequisite and it is the part of it that could be finished; the
placement itself cannot be, and the rest of this note says why rather than leaving it
to the next run to rediscover.

**WHY THE PLACEMENT CANNOT BE MADE — both anchors are exhausted, measured on `dev`.**

*"David Carver's old stand."* The town holds no Carver building and cannot be made to.
The corpus's two Carver records — `business_d_carver_co` and `business_david_carver` —
are both `unplaceable`, and the register's note on each is *"The paper gives no
anchor."* His lumber yard has no address in these papers. Nothing but a new source
changes this, and no ruling can.

*"west of J. Wright's."* Resolved as far as it goes, and it does not go far enough.
`J. Wright's` names `wright_building_to_let_a` and `_b` — one advertisement's two
buildings under one man's name — which `words()` reduces to a single name-set,
`{building, john, let, wright}`, because the *(east)* / *(west)* that separate them are
address stop words. That is now `ambiguous` rather than a silent pick. **And even
resolving it would buy nothing:** both Wright positions declare themselves invented in
their own notes — *"The advertisement gives no address at all, so this is a band
assignment and not a reading"* — and stand on Randolph Street, in two different blocks,
not on South Water Street at all. An offset measured west of an invented point on the
wrong street is an invented point. See also **T-0415**: the two are named the opposite
way round to the way they stand.

**THE ONE ROUTE LEFT, AND IT IS THE OWNER'S.** This business is `street_only` on
`south_water`, so the standing policy that would seat it is T-0354's street-face
adoption — and that pass refuses it, on a rule `docs/STREET-FACE-ADOPTION.md` says
itself must not answer identity questions, against an identity ruling the corpus has
already made and written down. That is **T-0414**, filed with the measurement. It needs
**T-0009**'s roofs first, because South Water Street is out of supply (19 fronting, 14
free, 14 adopted).

So this ticket waits on T-0414 (which waits on T-0009). Blocked rather than done: no
storefront is standing.

**What it needs first.** *"David Carver's old stand, South Water Street, doors west of
J. Wright's."* Neither anchor resolves: the town holds no Carver record at all, and
`J. Wright's` would have to be read onto `wright_building_to_let_a` / `_b`, which are two
records sharing one name — `match_landmark` would have to refuse the ambiguity rather
than take the first. Register action today: `street_only` on `south_water`.
