# The log cabins at Wolf Point — research dossier

**Record:** `data/structures/robinson_caldwell_cabins.json` · **Scene status:** standing on
1835-07-01 on the thinnest continuity argument in the dataset · **west bank, in the row near
Wentworth's tavern** · `review_required: true`

The hardest record in this parcel to get right, and the one most likely to be wrong.

---

## 1. The whole of the evidence

*Wau-Bun*, ch. XVII, describing 1831:

> "Facing down the river from the west was, first **a small tavern kept by Mr. Wentworth**,
> familiarly known as 'Old Geese' … **Near him were two or three log cabins occupied by
> Robinson, the Pottowattamie chief, and some of his wife's connexions.** Billy Caldwell, the
> Sau-ga-nash, too, resided here occasionally, with his wife, who was a daughter of
> Nee-scot-nee-meg, one of the most famous chiefs of the nation. **A little remote from these
> residences** was a small square log building, originally designed for a school-house…"

One sentence, in a book written twenty-five years after the year it describes. Nothing reached
follows these cabins to 1832 or to any year after.

## 2. Position — an order, not a place

*Wau-Bun* gives a **row order** along the west bank and no distances. Reading it against this
project's existing records:

| | local N | record |
|---|---|---|
| Wolf Point Tavern (Wentworth's), north face | −45 | `wolf_point_tavern` |
| **the cabins** | **−24** (this record) | — |
| Walker's log meeting house, south face, "a little remote" | −10 | `walker_meeting_house` |

The coordinate splits that gap. Both neighbours are themselves placed from bank geometry rather
than from any surviving intersection, and the Walker meeting house's own position is tagged
`conjectural` and **may be on the wrong bank entirely**. So this record inherits two soft
positions and adds a free choice between them: `position` is `conjectural`, good to about ±40 m
along the bank and no better. Facade bearing 90, east onto the river, follows *Wau-Bun*'s "facing
down the river from the west" and the bearing this project gives the rest of the row.

## 3. Two or three cabins, and one built

`form.cabin_count` keeps the source's words — "two or three" — because the looseness *is* the
evidence, and declares `geometry: simplified`: **one cabin is built.** The archetype models a
building, not a group, and choosing two or three would mean inventing the count *Wau-Bun*
declined to give, plus their spacing and arrangement. The model therefore understates the place,
and the record says so rather than letting the visitor count.

## 4. The date, and why this is the weakest survival claim in the dataset

The four years this range crosses are the years of the removal:

- **1833** — the Treaty of Chicago cedes the land.
- **1833–35** — the Potawatomi are assembled around the town awaiting removal west.
- **1835** — Billy Caldwell, who *Wau-Bun* says resided here occasionally, leads his people west.
- Alexander Robinson (Che-che-pin-qua) held a reserve of his own on the Des Plaines from the 1829
  treaty and lived out his life there.

A house left by the people who built it comes down or is taken over, and **no source records
either happening to these**. The record closes the range at the end of 1835 on the ordinary
continuity argument and states plainly that this is a likelier candidate for
`data/exclusions.json` than anything else in the parcel.

## 5. What this record claims, and what it refuses to

It claims that **buildings stood**. It carries **no `occupants` block at all**: who was in them
on 1835-07-01 is unattested, and `AGENTS.md` is explicit that Native presence is not a research
gap to be filled by inference and that depiction requires consultation. So the record models the
built environment — a log cabin on a bank — asserts nothing about people, and carries
`review_required: true`, which holds the scene short of `released` until someone qualified has
read it.

**What would upgrade it:** any source that follows these cabins past 1831 — the 1833 treaty's
schedules of improvements and claims, the agency's correspondence, or the *Chicago Democrat*.
