# The Chicago lighthouse of 1832

Research memo for `data/structures/chicago_lighthouse_1832.json`. Written 2026-08-11.

---

## 1. There are two towers and only one of them is in this scene

| | first tower | **second tower** |
|---|---|---|
| authorised | Act of Congress 3 March 1831, $5,000 | same appropriation |
| contractor | Samuel Jackson | Samuel Jackson |
| height | **fifty feet**, reached before it fell | **forty feet** |
| walls | **three feet thick** | *not stated* |
| shape | *not stated* | *not stated* |
| fate | **collapsed 30 October 1831, unfinished** | standing on 1835-07-01 |

Andreas, vol. 1, is the primary text for both:

> Before it was fairly completed, however, on October 30, of that year, the structure
> fell. … The walls were three feet thick, and the tower had been raised to a height of
> fifty feet. Samuel Jackson was the contractor. … **Another tower, forty feet high, was
> begun and completed by Mr. Jackson in 1832. It boasted of a fourteen-inch reflector.**

`lighthousefriends_chicago` paraphrases the same passage and adds, from its own
bibliography, that the second tower "employed four, fourteen-inch reflectors in its
bird-cage lantern room" and that it was the first light established on Lake Michigan.

**The first tower is already excluded** — see `data/exclusions.json`.

## 2. The correction this memo exists to make

`docs/research/04-structures-south.md` § 2 reads the 1832 tower as
"**forty feet high; conical stone/masonry**" and tags it `[DOC]` on Andreas,
drloihjournal and lighthousefriends jointly. `data/exclusions.json` called it "the 1832
conical masonry tower" on Andreas's authority.

**Neither "conical" nor "masonry" is in Andreas's sentence or on the lighthousefriends
page.** The only fabric detail either source carries — three-foot walls, fifty feet — is
the description of the tower **that fell down**. Whatever supports "conical", it is not
either of the two sources those entries cite.

The exclusions entry has been amended. The record grades:

- **height 12.19 m (40 ft)** — `documented`, Andreas and lighthousefriends;
- **lantern** — `documented`, lighthousefriends (a lantern; the four reflectors are *not*
  modelled, because a bird-cage lantern is a glazed drum at this level of detail);
- **construction `stone`** — `inferred`, on a real argument and not a guess: the same
  contractor built both towers under the same appropriation on the same site, and the
  first had three-foot walls, which is masonry. That the second was masonry too is
  likely; that it was any particular stone is not claimed;
- **shape, taper, cap, finish, diameter, footprint** — `conjectural`. **L44** owns them.
- **position** — `inferred` since 2026-09-12, on Wright 1834. It left L44 that day; see § 3.

## 3. Position

**Read off Wright's sheet, 2026-09-12 (T-1065).** Wright's 1834 map draws a ring with
*L. House* lettered round it, on the south bank west of the fort at the inside of the bend.
Its centre reads at resource pixel **(2941, 1604)** on the BPL master scan, which through this
project's fitted affine is **local E +1055.6, N +172.5** — 107.9 m from the fort's centre on a
bearing of 243°. That is the first independent witness this placement has ever had. The
reading, its two independent picks, its uncertainty budget and its crops are committed at
`data/traces/wright_1834_lighthouse_glyph.json`, and `tools/measure_wright_lighthouse.py`
recomputes the record's coordinate from that pixel on every gate.

**It moved the tower 75.3 m south-west.** The reading's combined uncertainty is 22.4 m — 1.4 m
picking, 10 m for the half-width of a ring drawn twenty metres across for a forty-foot tower,
20 m for the affine here — so the disagreement is 3.4σ. The point it replaced was invented; the
grade goes `reconstructed` → `inferred` and the quadrant goes west-north-west → west-south-west.
Two things corroborate rather than argue: the new point stands on dry modelled ground at +2.48 m
(the old one had to be nudged onto the bank top in August 2026 after the heightfield finally
reached this far east and found the first pick standing in the channel), and it sits 40.9 m
inside the derived reservation tract where the old point sat 20.8 m inside it.

Before that reading, adjacency was documented three ways and the offset was invented.

- Andreas: "Fort Dearborn and the light-house are placed at the angle thus formed" — the
  bend where the river turned south.
- Wentworth, disposing of the reservation in 1839: the land left over "upon which the old
  light-house was located" was lots "near the Rush-Street bridge", which is at the river
  north of the fort.
- Fergus, of the 1850 view: River Street runs between the block-house and the
  light-keeper's.

All of that says *close*, and *north or west*, and *near the water*, and the record turned it
into a bearing and a distance of our own.

**How the three fare against Wright.** Andreas agrees, and better than he did: the ring is at
the inside of the very bend he names. Fergus's 1850 note is about a keeper's dwelling that is
not modelled and a street of 1850, so it neither confirms nor refuses. **Wentworth disagrees** —
lots near the Rush Street bridge are north of the river and the ring is south of it. A sheet
surveyed a year before the scene is preferred to a recollection written five years after it
about which lots a disposal covered, but nothing here shows Wentworth wrong. If his lots are
ever plotted, this reading is the thing they test.

## 4. Keepers

Samuel Lasby (Andreas; "Samuel C. Lasby" in the Chicago Magazine of March 1857) was the
first keeper, at $350 a year with quarters. **Who kept it on 1835-07-01 was not
established**: Wentworth names William M. Stevens as keeper when he arrived in October
1836 and no source reached covers the gap. Mark Beaubien was the last. No keeper's
dwelling is modelled — a small house beside the tower is plausible and unattested.

## 5. What would settle it

The Light-House Board's annual reports; a keeper's return; or a measured reading of the
1850 von Schneidau daguerreotype or the 1855 Hesler photograph, in both of which the tower
stands. Any of those settles the **shape** at once and would move the rest of L44 to Resolved —
the position left it on 2026-09-12. For the position, what is left to want is a second
contemporary sheet, or Wentworth's 1839 lots plotted against this point.
