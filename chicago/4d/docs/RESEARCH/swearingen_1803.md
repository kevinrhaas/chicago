# Swearingen's 1803 journal, fetched at last

**Date:** 2026-08-11 · **Subject:** the primary printing of Lt. James Strode Swearingen's
journal — Quaife 1913, Appendix I, pp. 373-377 · **Outcome:** a new tier-1 source record, the
first written eyewitness document in this dataset; the paraphrase this project had been
standing on loses one of its two bank figures; one Swearingen sentence that reaches the
modelled quadrant is recovered, and one that does not is shown to be about a river regime the
1835 scene has removed. No value moved and no mesh is stale.

## 1. The queue this discharges

`docs/RESEARCH/evidence_tiers_round_two.md` § 4 read `wikipedia_chicago_river` in full,
established that it reprints no document, and ended by naming what it does carry:

> THE FOOTNOTE IS THE THING WORTH HAVING … *Journal of Lieutenant James Strode Swearingen
> reproduced in Quaife 1913, pp. 373-377*. Fetch those five pages and the figures stop resting
> on an encyclopedia.

`docs/ROADMAP.md` § S5 priced it: *reading. Free of a bake unless it is then cited from
`terrain_spec.json`.* Both halves of that turned out to be true, and the second half turned out
to be cheaper than the price on it — see § 6.

## 2. What was fetched, and how it was checked

Milo Milton Quaife, *Chicago and the Old Northwest, 1673-1835* (University of Chicago Press,
1913). Appendix I prints the journal Swearingen kept while marching the detachment from Detroit
to build the first Fort Dearborn. Two Internet Archive scans of the first edition were
downloaded in full and the Chicago passage extracted from each:

| scan | item |
|---|---|
| 1 | `chicagooldnorthw00quaiuoft` |
| 2 | `chicagooldnorthw00quai` |

Normalised for whitespace, **the two agree character for character** across the whole passage.
That is the standard `old_settlers_bridges_1883` set when the Andreas footnote had to be read
through poor OCR, and it is applied here because this passage is the entire reason the record
exists.

Two internal checks came free. The journal heads its entries with weekday and date, and
**17 August 1803 was a Wednesday**, as printed. And the volume's own index points at the same
place independently: *"Swearingen's description, 377."*

## 3. The passage, as printed

Appendix I, pp. 376-377, entry for Wednesday 17 August 1803 — the day he arrived:

> Proceeded on our march at 6 o'clock a.m., 34 miles and encamped on the Chicago river, at
> 2 o'clock p.m. This river is about 30 yards wide where the garrison is intended, to be built,
> and from 18 feet and upwards, deep, dead water, owing to its being stopped up at the mouth,
> by the washing of sand, from the lakes. The water is not fit to use. The bank where the fort
> is to be built is about 8 feet high and a half mile above the mouth. The opposite bank is not
> so high, not being a difference, of more than two feet, by appearances. The banks above are
> quite low.

Quaife states his own chain of custody in a footnote on p. 373, and it is two hops rather than
one. The original manuscript was in private hands in Dallas and he could not get access to it;
his text is taken from **a typewritten copy made for the Chicago Historical Society in 1903** by
another descendant of Swearingen. So the rung is a judgement about a period document, and
nobody in this project — or in 1913 — has seen the manuscript. That belongs on the record and
is on it.

## 4. What the encyclopedia kept, and what it dropped

This is the finding. `wikipedia_chicago_river`, verbatim:

> Swearingen … described the river as being about 30 yd wide and upwards of 18 ft deep at the
> place where the fort was intended to be built; the riverbanks were 8 ft high on the south
> side and 6 ft on the north.

Held against the page:

| the paraphrase | the journal | verdict |
|---|---|---|
| about 30 yd wide at the fort site | *"about 30 yards wide where the garrison is intended, to be built"* | **faithful** |
| upwards of 18 ft deep | *"from 18 feet and upwards, deep"* | **faithful** |
| 8 ft high on the south side | *"The bank where the fort is to be built is about 8 feet high"* | **faithful in substance.** The fort stood on the south bank, so the assignment is right, but "south" is the encyclopedia's word, not the witness's |
| **6 ft on the north** | *"The opposite bank is not so high, not being a difference, of more than two feet, by appearances"* | **NOT what he wrote** |
| — | *"dead water, owing to its being stopped up at the mouth, by the washing of sand, from the lakes"* | **dropped** |
| — | *"The banks above are quite low"* | **dropped** |
| — | *"The water is not fit to use"* | dropped; nothing here rests on it |

**The 6 ft is arithmetic on a hedge.** Swearingen gives no north-bank height. He gives a
*difference*, bounds it — *not more than two feet* — and then flags the whole comparison as
made by eye: *by appearances*. Subtracting the maximum difference from 8 produces 6, and 6 is
then printed as a measurement beside a measurement. The honest reading of the sentence is that
the north bank stood somewhere between about 6 and 8 feet, estimated visually. A maximum is not
a value, and a figure derived by a later writer should not arrive looking like a sounding.

This is the fourth time this project has found a citation misdescribing what is actually on its
page (`prefire273`, `prefire278`, `prefire062` were the first three), and it is the first found
by opening the *document* rather than the page. The class is the same: nothing checks what is
inside a source, and a number that has been quoted often enough stops looking like a claim.

**The dropped sentence about the banks above is the expensive omission.** Every figure the
paraphrase kept is measured at the fort, 1.2 miles downstream of the forks, and
`wikipedia_chicago_river`'s own note has warned since it was written not to carry them upstream.
The one sentence in the passage that *is* about upstream — *the banks above are quite low* — is
the one that did not survive the paraphrase. So the encyclopedia kept the numbers that do not
reach the modelled quadrant and dropped the observation that does.

## 5. What it does and does not license

**It does not rescue the `documented` grade on ground `water`, and the reason is in the
witness's own sentence.** The queued regrade (`docs/ROADMAP.md` § S5, STATUS § 45) stands, and
this memo strengthens the argument for it rather than overturning it:

- Swearingen gives **no gradient**. He gives a width, a depth, two bank statements and a
  distance. A level surface is not among the things he measured.
- He *does* give the river standing still — **dead water** — which is the strongest period
  statement of stillness this project has. But he attributes it, in the same clause, to a
  specific cause: *owing to its being stopped up at the mouth, by the washing of sand, from the
  lakes.* That is the **closed-mouth regime**, which this dataset models as the epoch
  `e1830_natural`.
- The 1835 scene is `e1834_harbor_cut`. The bar is cut, the piers are in, the mouth is open —
  the epoch exists precisely because that condition was removed. So a 1803 observation of dead
  water behind a sand-stopped mouth cannot be carried forward as evidence for a level surface
  in 1835 without arguing that the cut did not change the thing Swearingen says caused it, and
  no source read here argues that either way.

Citing him on the water plane would therefore be the over-grading move dressed as a citation:
a tier-1 source attached to a claim it does not make, which is worse than the tier-4 one it
would replace, because nobody would look at it twice. **He is deliberately not cited there**,
and the water block's note now says so where a visitor reads it.

**It does corroborate two things, qualitatively, and both are recorded as corroboration:**

- *The banks above are quite low* sits beside the spec's `bank` block, whose crest comes from
  dossier zone 13 (+2 to +4 ft at the forks) and is graded `conjectural`. A period eyewitness
  saying the upstream banks were low is real corroboration of a low bank. It has no number in
  it, so it does not move the grade — but the block cited nothing at all before, and now the
  one period statement that bears on it is attached.
- *The bank where the fort is to be built … is about 8 feet high* is the figure
  `docs/RESEARCH/fort_dearborn.md` should be read against: Hubbard, correcting *Wau-Bun* in
  1881, says the ground at the fort was "not over eight feet above the River at its lowest
  stage". Two witnesses, seventy-eight years apart, on the same number. That is left as a
  pointer rather than taken here — the fort parcel is where it belongs.

## 6. A price the roadmap over-quoted, worth correcting

§ S5 said citing this source from `terrain_spec.json` would cost a bake, "whose source ids are
inside the terrain's staleness hash". **They are not.** `generators/terrain_inputs.py` (scheme
`resolved-spec-v2`) strips `sources` from the hash along with the prose, for the stated reason
that *a citation is an obligation the record answers to and it cannot move a vertex*. A
`confidence` is still an input, which is why the regrade is still queued behind a bake and the
citation is not. Attaching a source and correcting a note are free; that is exactly what that
module was written to make possible, and the roadmap line has been corrected.

## 7. The cross-check the half mile makes possible

Swearingen puts the fort site *"a half mile above the mouth"* — 805 m. Before the 1833-34 cut
the river was deflected south behind the baymouth bar and ran parallel to the shore before
reaching the lake, which is what `data/terrain/epochs.json` already says of `e1830_natural`:
*the bar deflects the river south … for nearly half a mile … the natural outlet lies near
present Madison Street.* That sentence was sourced to a compilation and an encyclopedia. **It
now has a period eyewitness behind it**, who walked the distance in 1803 and wrote it down the
same day, and the record has been updated to cite him.

Measured against the committed trace, for what it is worth and no more. Walking the south
shore of `e1834_harbor_cut/shoreline.geojson` from the vertex nearest the Wright 1834 fort
label (local E +1118, N +256, 49 m from the label) southward along the west bank of the old
channel gives **1 366 m** before the line leaves the traced window at N −589, and the feature's
own note says the channel continues south of there untraced. So the 1834-mapped channel is at
least 560 m longer than Swearingen's 1803 half mile.

**That is a consistency, not a measurement, and it is stated as one.** Thirty-one years
separate the two, a littoral spit grows downdrift, and the trace follows a shoreline round the
reservation rather than a boat's path down a channel. It is compatible with the bar having
extended southward between 1803 and the cut — which is the behaviour `e1830_natural` already
describes — and it is not evidence of it. Nothing in the dataset is changed on this paragraph.

## 8. What this leaves open

- **Ground `water`: `documented` → `inferred`** — still queued, still priced at one Blender
  bake, and now better argued (§ 5). It is the first of § 43's six warnings to be settled in
  the over-graded direction.
- **The manuscript itself.** Quaife read a 1903 typescript, not the original. The original was
  a private possession in Dallas in 1913 and this project has not looked for it since. Anyone
  who does should record what they find whether or not it changes a word.
- **Hubbard's eight feet against Swearingen's eight feet** — one line of arithmetic in the
  fort parcel, not taken here.
- **Six pages at tier 4 or weaker still declare nothing** (`chicago_temple_history`,
  `chicagology_first_post_office`, `chicagology_lastwardance`, `chicagology_prefire274`,
  `drloih_hotels`, `drloih_wolf_point`). Unchanged by this slice; the two `drloih` pages are
  not solvable this way.
