# The named military men of 1835 — who was of the post, and who was not

Research memo for T-1348, the first half of T-1176. Written 2026-09-19.

`docs/RESEARCH/fort_dearborn.md` settles that Fort Dearborn was **held** on 1835-07-01 and
names two men at it: Maj. John Greene in command and Assistant Surgeon Philip Maxwell. Both
have household cards in `division: fort`. Meanwhile `data/structures/fort_dearborn_officers_quarters.json`
told a visitor its occupants were **"subordinate officers of the garrison"** — anonymous —
while the resident layer held a dozen men whose cards print a rank, a service or a soldier's
trade and who stood at `division: unplaced` with no roof at all.

This memo rules on every one of them. It adds **one name** to the post and states, for each
of the other eleven, the clause that kept it off.

---

## 1. The test, and why each clause is in it

A clause is only in this test if it can be said from committed evidence. Nothing here is a
judgement about how military a name sounds.

**Clause 1 — the United States Army, not the county militia.** The residents vocabulary
carries `army_officer` and `militia_officer` as different roles, and the difference is the
whole question: the Cook county regiment mustered its neighbours and quartered none of them.
A `militia_officer` is not of the post.

**Clause 2 — at the post, and not somewhere else in the town.** An officer of the United
States Army printed at Chicago in the scene window is at the only United States military post
in the place *unless the record itself puts him somewhere else*. The strongest such record
this project holds is the **town poll list of 1835**, and it is this project's own reading:
the T-1291 merge ruling on `greene_john` refused a fold partly because "the fold would put a
serving army major onto a town poll roll." That argument cannot be worth using in one
direction and not the other. A man on the poll roll is a man of the town.

**Clause 3 — across the day, not near it.** The household's own `present_on_scene_date` must
read `present`. An officer is the most transferable resident there is — the 5th Infantry moved
companies between posts on orders — so a single notice months before the scene date says where
a man was that week and nothing about 1 July 1835. `uncertain` is a finding, and this memo
does not spend a finding as a presence.

---

## 2. The ruling, name by name

Fourteen cards carry a rank in the name, a military role, or both. Every one is ruled.

| id | as the record prints it | military reading | dated by | presence | verdict |
|---|---|---|---|---|---|
| `greene_john` | Major John Greene | `army_officer`, attested, commanding | Andreas v1 p. 84; drloih chronology | present | **of the post** — already in the commandant's quarters |
| `maxwell_philip` | Dr Philip Maxwell | `army_surgeon`, attested | Andreas v1 | present | **of the post** — already in the officers' quarters |
| `allen_lieut_james` | "Lieut. Allen", "Lieut. J, Al", "…cient superintendent, Lieu…" | `army_officer`, **attested**, and engineer and harbour agent beside it | Democrat 25 Mar 1834 c. 2; Democrat 13 Aug 1834 c. 2; American 18 Jul 1835 c. 1 | **present** — the corpus prints him seventeen days after the scene date and fifteen months before it | **of the post** — named on the officers' quarters, `inferred` (§ 3) |
| `baxley_j_m` | "Capt. J. M. ley, U. S. A." | `army_officer`, attested | Democrat 19 Nov 1834 c. 3 | **uncertain** — one notice, 224 days before the day, nothing after it | refused, clause 3 |
| `jamison_l_t` | "Lieutenant, U.S. Army" | `army_officer`, inferred, span reaches the day | Democrat 4 Jun 1834 → 1835; **1835 poll list** | **uncertain** | refused, clauses 2 and 3 |
| `green_j` | "Major, 5th Infantry, commanding the post" | `army_officer`, inferred | American 27 May – 13 Jun 1835; **1835 poll list** | **uncertain** | refused, clause 2 — and see § 4, which does not act on it |
| `smith_e_kirby` | E Kirby Smith | `army_officer`, inferred, one day, `covers_scene_date: false` | Democrat 25 Mar 1834 | present, but bracketed by the 1843 and 1844 directories | refused — the military reading is of one day in March 1834 and does not reach the scene date |
| `thompson_lieut_j_l` | Lieut J L Thompson | `soldier`, inferred, one day | Democrat 4 Feb 1834; **caulker** in Fergus 1843 and Norris 1844 | present, by the directories | refused — the only trade the record follows him with is a caulker's |
| `wilcox_d` | D Wilcox | `soldier`, inferred, one day | Democrat 4 Feb 1834 | uncertain — 512 days before the day | refused, clause 3 — and see § 4 |
| `carpenter_nathaniel` | Nathaniel Carpenter | `soldier`, inferred, one day | Democrat 14 Jan 1834 | uncertain — 533 days | refused, clause 3 |
| `morin_william_w` | William W Morin | `soldier`, inferred — **and `cabinet maker` and `carriage maker` off the same span** | Democrat 25 Mar – 1 Apr 1834 | uncertain — 463 days | refused — one printing read three trades, so "soldier" is the extractor's third reading of it and not a service |
| `kirne_e` | "E. Capt. Kirne" | **none** — the card carries no military role at all | a letter waiting, Democrat 1 Jul 1835 c. 5 | present | refused, clause 1 — a letter list gives a name and a garble; the rank sits inside the read name and no role was ever derived from it |
| `beaubien_jean_baptiste` | Col. Jean Baptiste Beaubien | `militia_officer` — colonel of the Cook county regiment | — | present, at `jb_beaubien_homestead` | refused, clause 1 |
| `jackson_samuel` | Samuel Jackson | "Government works, near Garrison" | Fergus **1839** directory | uncertain | refused, clause 1 — a civilian on the harbour works, read off a volume four years after the scene |

**Eleven refusals and one addition.** That ratio is the finding, not a disappointment: the
town's papers print ranks freely and the post's roll is not among this project's sources.

---

## 3. Lieut. James Allen, and exactly what is claimed for him

The corpus prints him three times: 25 March 1834, 13 August 1834 and 18 July 1835 — and the
last of those is **seventeen days after the scene date**, which is why his household reads
`present` and Capt. Baxley's does not. The gazetteer reads his trade as *army officer,
engineer*, and one of the three printings survives as "…cient superintendent, Lieu…", the tail
of a line about the superintendent of a public work. His own card's `reason_for_coming`
already says "A posting to Fort Dearborn or the Indian Agency."

**What is claimed:** that a commissioned officer of the United States Army, printed at Chicago
on both sides of 1 July 1835, was quartered at the United States post at Chicago, in the
building this dataset holds for the post's subordinate officers. That is the identical
argument `hh_maxwell_philip` already carries on its own `lives_at`: *"A commissioned officer of
the garrison lodged in the officers' quarters. The building is in the dataset and the practice
is universal for a post of this kind; no source puts this man in this building, hence
inferred."*

**What is not claimed:** that any source says where Allen slept. The grade does not move. The
occupants block on the building was already `inferred`; it stays `inferred`, and all that
changes is that it stops being anonymous.

**The counter-argument, stated rather than buried.** Allen's other two readings are *engineer*
and *harbour agent* — the harbour improvement was a public work with its own establishment and
its own paid hands, and Samuel Jackson's 1839 entry ("Government works, near Garrison") shows
that work had civilians attached to it who lived *near* the garrison rather than in it. An
officer detached to a civil work could have lodged in the town. Nothing reached says he did,
and nothing reached says he did not; the officers' quarters is where the Army put a lieutenant
at a held post, and that is the reason the grade stays where it is.

---

## 4. Two findings this memo records and does not act on

**(a) The press prints a Major of the 5th Infantry commanding the post against the name
"J. Green".** The role on `green_j` reads, as printed, *"Major, 5th Infantry, commanding the
post"*, dated to the American of 27 May – 13 June 1835. The T-1291 merge ruling held `green_j`
and `greene_john` **distinct**, and one of its stated reasons was that "Major John Greene is
Andreas and the fort literature, with **no letter-list or poll reading at all**" — that the
anchor was on the wrong side of the fold. This printing is on the *other* side: it is a press
reading, in the scene year, that carries the command itself. It does not overturn the ruling —
the poll roll is still on the Green side and D7 still stands — but it is a fact the ruling did
not weigh, and an identity ticket should weigh it. Recorded for T-1027; not acted on here,
because a merge ruling is not this ticket's to reopen.

**(b) "D Wilcox", 4 February 1834, falls inside DeLafayette Wilcox's gap.** The commandant
chronology in `fort_dearborn.md` has DeLafayette Wilcox in command to 18 December 1833 and
again from 16 September 1835, with Greene between. A "D Wilcox" printed at Chicago on 4
February 1834 sits inside that interval, which is exactly where an officer of the post who was
not *commanding* it would be. The card is a single 1834 notice with an `inferred` soldier's
trade and an `uncertain` presence, so clause 3 refuses it whatever the identity is. Recorded
for T-1027.

---

## 5. Why Allen gains a building line and not a dwelling

He does not get `lives_at` in this ticket, and the reason is architectural rather than
evidential. `hh_allen_lieut_james` is **mint output** — `source_pass: "documented"`,
written by `tools/mint_documented_residents.py`, which derives `division` and `lives_at`
itself and whose `--check` re-derives them. `tools/resident_mint_carry.py` carries only the
keys a mint does *not* write, so a `lives_at` hand-written onto a minted card is reverted by
the next gate run. The refusal is deliberate and the sibling pass says so in its own words:

> `lives_at`: gained a `lives_at`; **the placement sweep does that, once the resident list is
> complete** — `tools/mint_civic_residents.py`

The placement sweep is **T-1198**, and this ruling is written for it: when it seats the layer,
Lieut. James Allen goes to `fort_dearborn_officers_quarters` at `inferred` on § 3's argument,
and the eleven refused names do not go to the fort at all. A bullet on T-1198 carries it.

**Links:** T-1348 · T-1349 (the companies to their strength) · T-1198 (the placement sweep) ·
T-1027 (identity) · T-1291 (the Green/Greene ruling) · `docs/RESEARCH/fort_dearborn.md`.
