---
id: T-0354
title: The register can only place 24 of 190 documented businesses; 49 more reach a street face and 78 reach nothing
state: done
epic: PAPERS
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-08-29
pr: 551
claimed_by: run 8/29/2026, 12:20:06 PM CT
blocked_on: null
needs_bake: false
---

The register (T-0262) places 24 of the 190 businesses standing on the scene date.
The other 166 divide into two piles the seeding tickets do not cover, and both need
a POLICY rather than a case-by-case decision:

- **49 `street_only`.** The paper names a platted street and nothing narrower —
  Peter Cohen at "the east end of South Water-street", J. S. C. Hogan on South Water.
  A street face is a real constraint and it is not a lot. What does the town do:
  adopt an anonymous reconstructed roof already standing on that face and attach the
  business to it, raise a new frontage record with a conjectural along-street
  position, or nothing at all until a corner turns up?
- **78 `unplaceable`.** No street the model holds. Some are outside the plat
  altogether (E. Wentworth's public house on Flag Creek, on the road to Ottawa);
  some are advertisements that simply never printed an address.

T-0263 takes the placeable ones onto South Water and Lake. This ticket is what
happens to the rest, and it is the difference between the papers yielding two dozen
buildings and yielding most of a town.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- A written policy for `street_only` and for `unplaceable`, in docs/, that a later
  run can apply without re-deciding.
- The policy states what confidence an adopted or raised record carries and what it
  cites; a business placed to a street face may not claim a lot.
- Counted against the register: how many of the 49 and the 78 the policy moves, and
  where the rest wait.

---

## THE OWNER'S RULING ON THE 49 `street_only`, 2026-08-29

Asked what a business does when the paper names a platted street and nothing narrower,
the owner chose, of the three options this ticket itself set out:

> **Adopt a reconstructed roof already standing on that street face and attach the
> business to it.**

Not a new frontage record with a conjectural along-street position, and not waiting for a
corner. So the 49 join the town on the streets their advertisements name, using roofs the
reconstruction programme has already raised there.

**What the adopted record may and may not claim — this is the whole of the care.**

- It claims a **STREET FACE, never a lot.** The paper's constraint is the face; the lot is
  the reconstruction's. A record that says which lot a street-only business stood on has
  asserted something no source carries, and the acceptance clause below refuses it.
- The **roof stays `reconstructed`**. Adopting it does not promote the building: the
  business is documented, the building under it is not, and the card must be able to say
  both in one breath — the pattern T-0264/#518 already set for a documented head on a
  reconstructed dwelling, and the convention to follow rather than reinvent.
- The **along-street position is the reconstruction's, not evidence.** Which roof on the
  face a business is given is an allocation, not a reading, and the note says so.
- **Order within a face is not a claim.** If two street-only businesses land on one face,
  neither is nearer the corner than the other on any authority.

**A liberty is owed** — a documented business seated on a roof no source attaches it to —
and `docs/LIBERTIES.md` carries it, in the shape L205 already uses for the documented
heads.

**The 78 `unplaceable` are NOT covered by this ruling** and stay open. Some are outside
the plat entirely (E. Wentworth's public house on Flag Creek, on the road to Ottawa) and
adopting a roof for them would put a business in a town it never stood in. That half of
the ticket still needs its own answer.

**Acceptance, restated with the ruling in it:**

- A written policy in `docs/` a later run can apply without re-deciding, stating the four
  limits above.
- The adoption is DERIVED and gated, not hand-authored: a tool re-derives which face each
  business's advertisement names and which standing roof it took, and `check.sh` re-runs it.
- Counted against the register: how many of the 49 the policy actually moves, which faces
  had no standing roof to adopt, and where those wait.
- No adopted record claims a lot, and a gate proves it.
- The 78 `unplaceable` remain open with their own count.
