---
id: T-0305
title: Four readings the American contradicts itself on need the page images: the tailor's street, which Water street two forwarding houses stood in, and the corner of Cobb's saddlery
state: blocked-owner
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: null
pr: null
claimed_by: run 8/29/2026, 9:19:33 PM CT
blocked_on: Six columns of Chicago American page images, which are held outside this repository: 1835-06-13 p3 c5 and 1835-07-04 p4 c4 (Sabine and John Dave[s], North in June and South in July — opposite banks of the river for two wharf trades); 1835-06-27 p3 c5 and 1835-08-15 p3 c6 (Edward Burton's tailoring shop, Franklin in two settings and Lake in a third); 1835-06-08 p3 c5 and 1835-07-11 p3 c6 (the cross street of S. B. Cobb's saddlery, lost in all three 1835 printings). Every reading is already the best the transcription can give, and three of the four subjects appear nowhere else in 86 issues except a post-office letter list, so nothing smaller than an image will do it.
needs_bake: false
---

Four readings the American contradicts itself on need the page images: the tailor's street, which Water street two forwarding houses stood in, and the corner of Cobb's saddlery.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

This ticket was filed with a title and an EMPTY acceptance clause, and its title asserts
the answer — *"need the page images"*. So the acceptance is written here first, and it is
written to be capable of refuting that assertion:

1. **The four are named**, each with every printing of it quoted verbatim from the
   committed extraction, at its issue page and column. A question nobody can point at is
   not a question.
2. **Each of the four is tested against the whole corpus, not against the American
   alone** — 86 issues, 73 of them the Democrat. If the corpus settles one, it is settled
   here and the title's assertion is wrong about it.
3. **What survives that test is put to the owner as a specific ask** — which columns of
   which issues, and what each would buy — because the page images are held outside this
   repository and only he can supply them.
4. **Nothing is completed to reach a result.** No bracket is filled, no confidence moves,
   no building moves. A fragment that could be read two ways is quoted and left.
5. **The finding is held by a gate rather than by this file**, so the day one of the four
   is answered — by an image, or by an extraction pass reaching a card nobody has read —
   the build says so instead of the dossier going quietly out of date.

---

## What the run of 2026-08-30 found

**All four are real, none is closeable from the corpus, and one of them belongs on the
visitor's card.** `tools/measure_american_contradictions.py` and
`docs/RESEARCH/american_self_contradictions.md` carry the whole of it; in short:

| # | the question | the printings | what the corpus adds |
|---|---|---|---|
| 1 | Edward Burton's tailoring shop: **Franklin or Lake street** | 4 settings of one card under one copy date: Franklin (06-27), Franklin (07-25), unresolved (08-01), **Lake** (08-15) | nothing — `Burton` is not in the Democrat at all |
| 2 | **Wm. Sabine**: North or South Water Street | North (06-13, 06-20), **South** (07-04) | nothing — one letter-list line, 1835-07-01 |
| 3 | **John Dave[s]**: the card set below Sabine's | North (06-13, 06-20), **South** (07-04) | nothing — three letter-list lines |
| 4 | **S. B. Cobb's saddlery**: which cross street | Lake legible in all three 1835 cards, the cross street lost in all three | the Democrat's 1833 *"corner of Lake and Canal streets"*, and that reading is **image-verified** |

Three things the run added that the ticket did not know:

- **2 and 3 are one event, not two.** Both houses read North in both June settings and
  South in the July one. One page image settles both.
- **The contradicting printing is invisible to the register.** On 1835-07-04 the three
  forwarding cards were extracted as ONE claim under the third firm's name, so Sabine's
  register entry reads "North Water Street" flat with no disagreement recorded on it.
- **Question 4 is the weakest of the four**, because the 1833 corner is one of the few
  addresses read off the page images themselves. What the American leaves open there is
  the twenty months after it, not the corner in 1833.

**Shipped with this ticket:** the saddlery is now on the watch list in
`data/exclusions.json`, so its doubt reaches the Evidence panel's open questions (4 → 5)
and the provenance card of a building a visitor can walk up to — the same treatment the
New York House's *"which side of Wells?"* already has.

**What is left is the owner's**, and it is small: **six columns**, all in the American.

    1835-06-13 p3 c5   Sabine and Dave, both reading North
    1835-07-04 p4 c4   the same two, both reading South
    1835-06-27 p3 c5   the tailor, reading Franklin
    1835-08-15 p3 c6   the tailor, reading Lake
    1835-06-08 p3 c5   Cobb, "Lake and [Amor.] streets"
    1835-07-11 p3 c6   Cobb, "Lake and the [Balle]"

Two of those columns serve two questions each, so six columns close four questions.
