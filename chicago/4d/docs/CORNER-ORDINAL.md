# The ordinal off a corner — what a business does when the paper counts doors

**Status: policy, in force.** Recorded 2026-08-30 for T-0384, on the owner's ruling of the
same day. A later run applies this without re-deciding it; a run that wants to change it
opens a ticket and asks. The implementation is the `corner_ordinal` anchor kind in
`tools/compile_register.py`, the transparency clause is `no_lot_claim_ids` in
`tools/plat_occupancy.py`, the liberty is **L215**, and `tools/check.sh` re-derives the
register and runs `tools/measure_corner_ordinals.py` on every commit.

## The question, and it was one line

> **Does *"one door from Dearborn street"* place a store, or is it a street and nothing
> narrower?**

It mattered because the two answers put John Holbrook's clothing store in two different
places, and one of them was nowhere. Read as a street, the address is a `street_only`
business and falls to `docs/STREET-FACE-ADOPTION.md`: it adopts a reconstructed roof
already standing on that face, nothing is built, and **South Water Street has no free roof
to adopt** — nineteen front it, five are a named household's dwelling, five are yard
buildings and nine are already adopted by better-evidenced businesses. Holbrook would have
waited on T-0375 indefinitely. Read as an ordinal, the phrase counts doors from a crossing
the plat fixes, which is a position along the face, and the store can be stood at it.

## The ruling

> **Read it as an ordinal off the corner.**

So *"one door from Dearborn"* is a NARROWER claim than *"on South Water Street"*. It counts
doors from a named corner, which is a position along a face and not merely the face.

**The blast radius was measured before the ruling, not after.** Nothing else in the corpus
turns on it: zero register businesses anchor on any of the five documented buildings holding
a business-front lot. The ruling corrects one anchor and does not cascade.

## The one limit, and it is the whole of the care

**AN ORDINAL IS NOT A LOT.** "One door from the corner" fixes a position in a sequence
along a face; it does not name a platted lot and may not claim one. This is the same limit
the street-face ruling carries, arrived at from the other direction — there the paper gives
a face and no position, here it gives a position and no lot — and it is enforced the same
way, in fields rather than in prose:

- the structure record carries a `lot_claim` block: `claims_lot: false`, `lot: null`,
  `placement_rule: "corner_ordinal"`, and a note saying why. The schema permits no other
  value for either of the first two.
- `tools/plat_occupancy.no_lot_claim_ids` reads that block, and such a record is **not a
  holder of the lot** for the business-front clause of 2026-08-27. It neither entitles the
  lot it physically stands on nor exhausts it; the roof schedule and the block generator
  see the lot exactly as they would if the record named a different street.
- `occupied_lots` still counts it. The building stands where it stands, is a roof of its
  block, and is subtracted from that block's headroom like any other. Only the entitlement
  question reads the declaration.
- **nothing physical is relaxed.** The footprint still may not overlap another, still
  clears every neighbour by the separation gate's three metres, still stands inside the
  block's own lot lines by `LOT_MARGIN_M`, and still may not lap a platted corridor.

The transparency runs ONE WAY on purpose. A lot held only by no-lot-claim records has no
documented store entitling it, so it reads as taken and the run is not dealt it — the
cautious answer, costing nothing today because no such lot exists. Freeing it would be a
second ruling, about ground rather than about evidence, and this policy does not make it.

## THE COUNT IS EVIDENCE AND THE METRES ARE NOT

The owner's ruling says it in terms, and it is the sentence a later run is most likely to
forget. How far one door is from the corner is a **reconstruction**. The rule that produced
the number is **L215's door-gap rule**: a front placed one door along from a named
neighbour is set **3.048 m (10 ft) clear of that neighbour's wall**, measured along the
face — because "one door from" describes a neighbouring front and not a party wall, so the
gap may not be zero, and because ten feet is the smallest gap that still reads as two
buildings rather than one at walking distance. It is a convention with two reasons and no
source, it is declared at L215, and a second ordinal placement anywhere in the corpus turns
it from a convention used once into a rule that has to be argued.

The DIRECTION is the same kind of thing where the paper omits it. Holbrook's card gives a
count and no side of Dearborn; east is read from three of this face's own printed addresses
agreeing when read eastward and closing on nothing when read westward. That is a reading of
sources against each other, which is why the position is graded `inferred`; the fork is
recorded on the record and at L215 rather than resolved silently.

## How a reading pass gets this for free

**The vocabulary is derived, not hand-tagged, and that is the point.** A reading pass writes
what it always wrote — `class: relative`, an `anchor` naming the cross street, and an
`offset_normalized` carrying the phrase — and `tools/compile_register.resolve_anchor` reads
the ordinal out of it. Nobody decides anything twice, and a claim written before this policy
existed is read under it the moment the register recompiles.

`ordinal_off_a_corner` runs **after** the landmark resolutions and **before** the `street`
fallback, which is the whole of its precedence, and three things must hold:

1. the offset counts DOORS, in a word this project translates to a number. *"a few doors
   below Messrs. Newberry & Dole"* names no count and is refused — `few` is not a number,
   and a placement that cannot say how many doors is a reach of the street.
2. its reference resolves to exactly ONE platted street, suffix required — the same test
   the `street` kind uses, so a phrase that could not have been read as a street cannot be
   read as an ordinal off one either.
3. the business's OWN street is platted and is a different street. *"two doors north of Lake
   street"* said by a house on Lake Street names no crossing.

An ordinal off a BUILDING — *"first door west of Messrs. Jones, King & Co."* — is untouched:
it resolves earlier, as a landmark hop, and was always placed by the building it names.

The anchor that comes back names the crossing in `streets`, as `corner` does, and the reading
itself in `ordinal` — `{count, direction, along, from_street, phrase}` — so a gate reads the
count without parsing prose. The action is `new_building`, the same action a corner gets.

## What it reaches today — swept by the gate, not estimated

`tools/measure_corner_ordinals.py` sweeps every extraction file for the `n doors` forms
this corpus prints and reports what the reading does with each, so the numbers below move
when a reading pass adds one rather than going stale. As of 2026-08-30, over 86 extraction
files:

| | |
|---|---|
| claims carrying an *n doors* phrase | **28** |
| — whose phrase also names a corner of two streets, which resolves first | **5** |
| — a landmark hop, or naming no platted street | **20** |
| — readable as an ordinal off a corner | **3** |
| — the crossing split between the anchor and the placement's `street` | **4** |
| — refused: the two streets named never meet | **2** |
| phrases a bracketed supply hides from the reader | **10** |
| register businesses reading `corner_ordinal` at the scene date | **1** |

*(Read as an ordinal was 3 until 2026-09-06, when T-0771 added the fourth test below and
Clark, Filer & Co.'s two printings were refused for a stated reason.)*

One readable claim, one business, and it reaches the register:

- **John Holbrook**, Democrat 1835-06-10 c010, *"one door from Dearborn street"* — the
  store this ruling was made for. Its other printing, American 1835-06-13 c012, is NOT
  readable: the transcription cuts the cross street to *"De[arborn]"* and a bracketed
  supply is not a street name, so the phrase resolves to no platted street. The Democrat's
  printing is what carries the placement, and it also corroborates the street word the
  American's column cut away.
- **Clark, Filer & Co.**, Democrat 1834-06-18 c009 and 1834-07-02 c014, *"their ware house
  on South water St. five doors east of the corner of Randolph st."* — **refused, and the
  refusal is the point.** Randolph Street and South Water Street are both east-west lines
  of the Original Town and never meet, so the phrase counts doors from a corner the plat
  does not hold. It stays `street_only` on South Water Street and adopts a face there under
  `docs/STREET-FACE-ADOPTION.md`, exactly as before. **T-0771** below is how that was
  found; what the ad's Randolph actually names is not a question this policy can answer.

So the ruling reaches **one store**, which is what the measurement taken before the ruling
said it would.

## T-0771 — the two streets, and the printing the reading quotes

Two questions were asked of Clark, Filer & Co. on 2026-09-04. Neither was the fault, and
answering them found a third thing that was.

### The crossing may be split between the anchor and `street`, and always could be

**The question.** An ordinal counts doors from a CROSSING, so the reader needs two streets.
Clark, Filer's claim names only one of them in its `anchor` — *"the corner of Randolph
st."* — and carries the other, South Water Street, in the placement's own `street` field.
May an anchor naming one street of a crossing take the second from there?

**The answer is yes, and it is not new.** It is the THIRD of the three tests
`ordinal_off_a_corner` has applied since the ruling: *the business's OWN street is platted
and is a different street.* The pairing is what that test does. The doubt was about the
code, not about the corpus, and reading the code settles it.

**The limit is the test itself, and it is why the pairing is safe.** `street` is a DECLARED
field and not free prose, so the second street is not being fished out of a sentence — it
is the street the reading pass wrote down for this house. And the test refuses the
degenerate case in terms: *"two doors north of Lake street"* said by a house on Lake Street
names no crossing, because a crossing is a crossing of two DIFFERENT streets. An ordinal
still fixes a position and never a lot; nothing above this line moves.

**Swept rather than assumed** (`measure_corner_ordinals.py`, the row added for this
ticket): **4** of the 28 `n doors` claims carry their crossing split that way, and they
include **every** claim that has ever read as an ordinal. The split is the corpus's normal
shape, not its exception. The fourth is Kinzie & Hall, *"one door east from the corner of
Lake and Canal streets"*, which names its crossing whole in the anchor and reads as a
`corner` first.

### The fault was a supply, and the fix is which printing a reading keeps

**What actually held the warehouse off the ground.** The house prints one sentence three
times. The Democrat sets it whole on 1834-06-18 and 1834-07-02 and damaged on 1834-06-11 —
*"five [doors east] of the corner [of Randolph st.]"* — and `absorb_reading` kept the
EARLIEST printing of a reading, so the gazetteer's live placement was the damaged one. The
reader met a supply where the count should be, refused it exactly as it refuses the
American's *"De[arborn]"*, and the register put a documented warehouse on the whole of
South Water Street.

**Nothing here spends a supply.** `absorb_reading` now prefers a printing that sets the
very same sentence without the brackets — equality after opening the supplies, up to case
and run of whitespace, so the candidate says NEITHER more nor less than the printing it
displaces. That is `docs/CORNER-ORDINAL.md`'s own standing rule, *an anchor printed four
ways is resolved on its BEST reading*, applied to the rest of the same sentence. It chooses
between printings of ONE reading and never between readings; a damaged printing that is the
only printing of its reading keeps that reading, still bracketed, still refused. No word
enters the tree that some printing did not set.

**Two records move and no reading does.** Clark, Filer & Co. and D. Graves each gain a
clean quotation — D. Graves' is *"a few doors north of Messrs. Newbury & Dole's store"*,
which stays unreadable because *few* is not a number — and the register is byte-identical
either way. That is the right size for a transcription fix. A first attempt ranked printings
by bracket COUNT instead and moved five houses onto worse transcriptions, G. Spring's office
off Dearborn Street and onto South Water among them. That is why the rule is equality and
not a score.

**What it bought is a true reason.** Before it, Clark, Filer & Co. was refused because a
bracket fell where the count should be — an accident of one column's ink. After it, the
phrase is legible, the reader gets to the streets, and the refusal below is a fact about
Chicago instead. Refusing for the wrong reason and refusing for the right one look identical
in the register and are not the same thing.

**The refusals are now counted.** **10** claims across the corpus print an `n doors` phrase
the reader cannot reach because a supply falls inside it, and the sweep names all ten. That
is a measurement and not a queue. **Four** sit in a reading whose kept printing does set the
sentence whole — Clark, Filer's by this fix, G. Spring's two and Collins & Caton's because
the earliest printing of their reading was already the clean one — and the other **six**
have no whole printing to fall back on at all. Those six stay refused, which is the right
answer: the New York Clothing Store's cross street is *[the T]remont House* in every one of
its three printings, and no run may supply it. A refusal nobody can see is a refusal nobody
fixes; these are now countable.

### THE FOURTH TEST: different is not crossing

**And this is what the whole ticket found.** With the sentence legible, Clark, Filer & Co.
passed all three tests — an `n doors` count, one platted street in the reference, another
platted street in `street` — and the register stood a documented warehouse **five doors east
of a corner that has never existed**. Randolph Street and South Water Street are both
east-west lines of the Original Town. They run parallel for their whole length. There is no
corner of Randolph and South Water and there never was.

Three tests asked whether two streets were NAMED. None asked whether they MEET.

> **4. the two streets must meet on the committed plat.**

`compile_register.streets_cross` asks `data/streets/1835.json`'s own `path_local_enu_m` —
the same committed centrelines every other placement is measured against — by segment
intersection, counting a T-junction as a corner. Nothing is inferred: if the plat's lines
meet there is a corner, and if they do not there is not one. A street the town holds no path
for cannot be shown to cross anything and is refused, which is the cautious direction.

**It costs nothing true and refuses two things false.** Holbrook's South Water × Dearborn
crosses and is untouched; Kinzie & Hall's Lake × Canal crosses. The two Clark, Filer
printings are refused, the sweep names them and says why, and the store keeps the
`street_only` reading and the street-face adoption it already had. The register, the
adoptions and every count are byte-identical to the tree before this ticket — **the town
does not move, only the reasoning does.**

**What the ad's Randolph means is not settled here.** The Democrat sets it three times and
the OCR reads *"of Rando!ph st.)"* on one of them, so a mis-set cross street is possible and
so is a firm advertising a corner it did not stand on. Both are readings of a source and
neither is this policy's to make. What is settled is that the corner named is not one the
plat holds, and a run that later reads the phrase differently will find this test in its
way — which is the point of writing it in code rather than in prose.

**Related:** `docs/STREET-FACE-ADOPTION.md` (the policy for the other half of the problem) ·
**L215** (the metres, the side of Dearborn, and the invented building) · T-0384 (the ruling) ·
T-0306 (the American's six storefronts) · T-0375 (the South Water roofs an adoption wanted).
