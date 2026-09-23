# The four readings the Chicago American contradicts itself on

**Ticket:** T-0305 · **Measured by:** `tools/measure_american_contradictions.py`, re-derived on
every `tools/check.sh` · **Corpus:** `data/research/newspapers/` — 86 issues, 73 *Chicago
Democrat* (1833-11-26 to 1835-08-26) and 13 *Chicago American* (1835-06-08 to 1835-08-29)

The American earns its place in this corpus by being a **second, independent witness** —
`data/sources/chicago_american_1835.json` puts it in those words: *"corroboration or
contradiction of a Democrat address, which is worth more than either paper alone"*. Four times
in thirteen issues it contradicts **itself**, or prints a street and loses the one that would
locate it.

This dossier states the four, quotes every printing of each verbatim with its page and column,
records what the rest of the corpus was tested against and could not settle, and says what one
page image would buy. It answers no question. That is the finding: **none of the four is
closeable from the material this repository holds**, and the four are held open by a gate rather
than by a memory.

---

## The rule this dossier is written under

Every reading below is a **transcription** read. The transcriptions are the owner's own work
product, made from scans he supplied; the scans themselves are held outside the repository
(`chicago_american_1835.json` § `rights_note`). So a disagreement here is not usually a
disagreement between two claims about 1835 — it is a disagreement between two bracketed
reconstructions of damaged type, and the page image is the instrument that settles it.

Nothing in this dossier upgrades a confidence, moves a building, or completes a bracket. Where a
printing does not resolve a street, it is recorded as not resolving it.

---

## 1. The tailor's street — Franklin or Lake

**Edward Burton's `NEW FASHIONABLE Tailoring Establishment`**, one standing advertisement under
one copy date — *Chicago, 27th June, 1835* — set **four times**, and the street changes.

| printing | page/col | claim | what it reads |
|---|---|---|---|
| 1835-06-27 | p3 c5 | `chicago_american_1835_06_27#c009` | *"Shop in Frank[uncertain: eter — the rest of the street name] street"* |
| 1835-07-25 | p3 c4 | `chicago_american_1835_07_25#c002` | *"[has] taken a Shop i[n] [F]r[an]kli[n street]"* |
| 1835-08-01 | p3 c6 | `chicago_american_1835_08_01#c005` | *"Shop in [uncertain: Laks runlie — a street name this printing does not resolve]"* |
| 1835-08-15 | p3 c6 | `chicago_american_1835_08_15#c002` | *"having ta[ken a shop in] lake - str[eet]"* |

Two Franklin, one Lake, one that resolves to neither. **The two-to-one count is not an
argument**, and this dossier does not make it one: 06-27 reads `Frank…eter`, which is a bracket
around a word the column did not give, and 08-15 reads `lake - str[eet]`, which is the cleanest
setting of the four. The 08-01 fragment `Laks runlie` is the interesting one — it is the shape a
scanner makes of a *pair* of words, and neither "Franklin" nor "Lake" accounts for the whole of
it.

The distance matters. Franklin Street and Lake Street are two blocks and one street-class apart
in this reconstruction, and the register carries the house as `street_only` with **no street at
all** rather than picking.

**What the rest of the corpus says:** nothing. `Burton` does not appear in the Democrat's
seventy-three issues.

---

## 2 and 3. Which Water street — Wm. Sabine and John Dave[s]

Two forwarding houses whose cards are set **one under the other in the same column**, and they
move together.

| printing | page/col | Sabine | John Dave[s] |
|---|---|---|---|
| 1835-06-13 | p3 c5 | `#c005` *"N[ORT]H WATER [S]TREET"* | `#c006` *"NORT[H] WATER STREET"* |
| 1835-06-20 | p3 c6 | line 346 *"NORTH WATER STRERT"* | line 360 *"NORTH WaTEM sTRERT"* |
| 1835-07-04 | p4 c4 | `#c002` *"[SO]UTH WATER STREET"* | `#c002` *"[S]OUTH WATER STREET"* |

The 1835-07-04 extraction's own note states the problem and refuses to decide it:

> *"So either the firms moved across the river between 20 June and 4 July, or one printing is a
> compositor's or the OCR's error. THIS FILE DOES NOT DECIDE IT."*

**Three things this dossier adds to that.**

**(a) It is one event, not two.** Both houses read North in both June settings and South in the
July one. Whatever happened, happened to the pair — which is what a standing-type column does
when a compositor resets a heading, and is *not* what two independent firms moving premises looks
like. That does not decide which reading is right; it does mean **one page image settles both**.

**(b) The 06-20 attribution to Sabine is positional, not by name.** That column is interleaved
badly enough that neither card was extracted as a claim of its own. The line above the street
reads only `Commission Merehatit`; the name `WM. SABINE` is not legible on that setting. The
project's identification rests on the card's place in the column, and the extraction for that
issue says so in its own words. It is the weaker of the two North readings and is recorded here
as such.

**(c) The contradicting printing is invisible to the register.** On 1835-07-04 the three
forwarding cards were extracted as **one claim**, filed under the third firm's name (Newberry &
Dole), so `business_wm_sabine_storage_forwarding_and_commission_merchant` carries the two June
mentions and reads **North Water Street** flat, with no contradiction recorded on it. The South
reading survives only on John Davis's *entity* and in the claim's note. A reader who opened
Sabine's register entry would not learn that the run disagrees with itself about him. That is a
finding about the register and it is filed as one — this dossier does not re-cut the claim,
because re-cutting a claim is a reading of the page, and the page is the thing that is missing.

The river is the whole of what is at stake: North Water Street and South Water Street are
**opposite banks**, and the two houses are warehouse trades whose whole business is a wharf.
Placing either on the wrong side would be the largest single placement error available in the
register.

**What the rest of the corpus says:** nothing usable. `Sabine` appears once in the Democrat, in
the post-office letter list of 1835-07-01 (*"Sabine, Williem"*), and `John Davis` three times in
letter lists of 1834-04-01, 1834-10-22 and 1835-05-20. A letter list gives a name and never a
street.

---

## 4. Which cross street is S. B. Cobb's saddlery on

The one of the four that **stands in the scene** — `goss_cobb_saddlery`, on the corner of Lake
Street, in the West Division.

| printing | page/col | claim | the cross street |
|---|---|---|---|
| 1833-11-26 (Democrat) | — | `chicago_democrat_1833_11_26#c019` | *"on the conner of Lake and Canal-streets"* |
| 1835-06-08 | p3 c5 | `chicago_american_1835_06_08#c007` | *"corner of Lake an[d] [uncertain: Amor.] streets"* |
| 1835-06-13 | p3 c6 | `chicago_american_1835_06_13#c016` | *"at his shop, corner [o]f [… ][st]re[et]s"* — no street names at all |
| 1835-07-11 | p3 c6 | `chicago_american_1835_07_11#c008` | *"corner of [L]ake [an]d the [uncertain: Balle]"* |

T-0383 read these three cards on 2026-08-28 and settled the firm's **survival** with them —
four printed dates, the last ten days after the scene date, which moved `documented_range` off
`reconstructed`. It could not settle the corner, and said so. **This is that half of the
sentence.**

Lake Street is legible in all three American printings and the cross street is lost in all three.
So the American **cannot corroborate and cannot refute** the Democrat's 1833 "Canal", which
remains the only reading of the corner anywhere in the corpus.

**And that reading is the strongest one in this dossier, which makes this the weakest of the four
questions.** The Democrat of 1833-11-26 is the one issue in the corpus whose page images were
read: `data/sources/chicago_democrat_1833_11_26.json` carries `verified: true` and states the
address in the clear — *"Goss & Cobb, saddle and harness makers, self-reported on the corner of
Lake and Canal streets"* — and the corpus README makes it senior to the transcription for that
issue, because a scan read outranks a transcription read. (The transcription of the same
advertisement is far weaker: it brackets the clause down to *"[on the corner of Lake and
Ca]n[a]l [s]tree[t]s"*, and prints *"conner"* for "corner".)

So the American's silence is not a doubt about where the shop was **in 1833**. What it leaves
open is the twenty months after it: whether the shop Cobb *"will continue the above business at"*
in June 1835 is the same corner, which is exactly the identification the record grades `inferred`
and argues in its own note. An image of either 1835 card would settle it in one word.

**`Amor.` and `Balle` are not read here, and deliberately.** Both are fragments a reader can make
several street names out of, and this project's own rule is that a bracket is not a licence: a
completion that reaches a conclusion the page did not print is an invention, whatever it is
graded. They are quoted and left. What is recorded instead is what the fragments **rule out** —
neither is a plausible setting of `Canal`, the word the building's position is derived from.

**The consequence, and why it is now on the visitor's card.** The saddlery's position claim is
`inferred` and its note argues the corner out honestly. Until this ticket it was argued only
inside the record's own prose. The building is now on the **watch list** in
`data/exclusions.json`, so the doubt reaches the Evidence panel's open questions and the
provenance card a visitor opens by walking up to the shop — which is where a live question about
a standing building belongs, and is the same treatment the New York House's "which side of
Wells?" already has.

---

## What one page image would buy, per question

The ask is four questions and **six columns**, all of them in the American:

| question | the columns that settle it | what it unblocks |
|---|---|---|
| the tailor's street | 1835-06-27 p3 c5 · 1835-08-15 p3 c6 | a `street_only` house takes a street, and reaches the street-face adoption pass |
| Sabine's Water street | 1835-06-13 p3 c5 · 1835-07-04 p4 c4 | which bank a forwarding house stands on |
| John Dave[s]'s Water street | the same two columns | the same, for the card set below it |
| Cobb's cross street | 1835-06-08 p3 c5 · 1835-07-11 p3 c6 | the saddlery's position leaves `inferred`, or moves |

Two of the six columns serve two questions each, so **six columns close four questions**. Nothing
smaller than an image will do it: every one of these readings is already the best the
transcription can give, and three of the four subjects appear nowhere else in eighty-six issues.

---

## The gate

`tools/measure_american_contradictions.py` declares every reading above as a substring the
committed extraction has to carry, at the page and column named, and re-derives the negative
half — that the Democrat supplies **no address** for the tailor, for Sabine or for Dave[s] — over
all seventy-three of its issues. It fails if a printing moves, if a reading changes, if a
disagreement collapses, or if the Democrat turns out to place one of them after all. Eight
assertions, each proved to fire under `--self-test`.

So the day one of these four is answered — by an image, or by an extraction pass reaching a card
nobody has read — the gate says so, instead of this page going quietly out of date.
