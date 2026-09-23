# North Branch Bridge — research memo

**Record:** `data/structures/north_branch_bridge.json` · **Archetype:** `bridge_timber` ·
**Written:** 2026-08-10 · **Scene:** 1835 (target 1835-07-01)

Chicago's first bridge, and the first structure in this dataset that is not a building. It is
also the first record here whose dimensions come from evidence instead of from a placeholder,
which is worth stating plainly because every other footprint in `data/structures/` says in its
own note that its numbers are invented.

---

## 1. What the sources say

**Andreas, *History of Chicago* vol. I (1886), transcribed by chicagology on its Kinzie Street
Bridges page** (`chicagology_kinzie_bridge`):

> In the summer of 1832 Samuel Miller, the original possessor of the old ferry scow, built the
> first bridge over the North Branch. It was located near the southeast corner of Kinzie and
> Canal streets, in the vicinity of the present bridge of the Chicago & Northwestern Railroad
> Company. It was formed of stringers and only fitted for foot passengers. Even up to the summer
> of 1833 the structure was useless for teams.

The same page carries a tabulated chronology of the six Kinzie Street crossings whose first row
reads **Kinzie #1 · 1832 · 1839 · Wood, Fixed, Bent · Samuel Miller**. That table is the page's
own editorial apparatus, not Andreas, and it is treated as weaker than his prose.

**Charles Cleaver, recalled in the *Chicago Tribune* of 29 October 1893**
(`chicagology_prefire252`):

> Mr. Cleaver was authority for the statement that the first bridge across the North Branch of
> the river was built in the winter of 1831-32, and that the first bridge over the South Branch
> was built in the [winter] of 1832-33. The abutments were built of heavy logs in the shallow
> water near the banks. **These bridges were ten feet wide.** Mr. Cleaver remembered driving
> across the first bridge over the North Branch.

(The transcription's OCR is corrupt in two places — "heavy legs" for heavy logs, "in the beer of"
for in the winter of. Both are read through, and the fact that they had to be is itself a reason
not to build anything on a single word of this page.)

**The war-dance account of 18 August 1835** (`chicagology_lastwardance`) has a procession cross
"the North Branch bridge" and then move "south along West Water street (now Canal street), in
front of the 'Green Tree Tavern' and 'Wolf's Point Tavern' to the log raft bridge across the
south branch". Cited here for three narrow facts and nothing else: the bridge was standing six
and a half weeks after the scene date, it carried a crowd, and it landed on the west bank north
of the two taverns. **The subject of that page falls under the standing constraint in
`AGENTS.md`**, and nothing in this project depicts, stages or narrates it; the citation is about
timber.

---

## 2. Three disagreements, and how each was read

**The build date — Andreas's summer 1832 against Cleaver's winter 1831-32.** Adopted: 1832.
Cleaver did not reach Chicago until 23 October 1833, so his date is hearsay reported sixty years
after the fact, while Andreas is a compiler working over the town's records in the 1880s. It
makes no difference to a scene dated 1835-07-01 and is recorded because the next reader will
find both numbers.

**The capacity — "only fitted for foot passengers" against "remembered driving across".** Both
kept; neither discarded. Andreas's judgement is explicitly dated ("even up to the summer of
1833"), Cleaver's recollection is undated, and on 18 August 1835 the thing carried hundreds of
people at once. The reading adopted is that the bridge was rebuilt, widened or decked between
1833 and 1835 and **nothing reached says when or how**. The record's `stringer_count: 4` and its
full-width deck take the 1835 reading, and its note says that an 1833 scene would want the other
one. This is the single largest unknown about the structure and it is invisible in the model,
because a model shows one state.

**The pier type — Cleaver's heavy logs against the table's "Bent".** Adopted: `crib`, tagged
`inferred` — **and overturned on 2026-08-10 by §6: "bents" is the settlers' own word and Cleaver
signed it. The record is now `bent`, `documented`.** The reading below is left as written.
Adopted at the time: `crib`, tagged `inferred`. An eyewitness describing logs standing in shallow water is describing a crib; "Bent"
is a modern type-word applied down a column covering six bridges and a century. The inference
that matters is not the choice of word, though — it is the step from *abutments*, which Cleaver
describes, to *piers*, which nobody does. See §4.

---

## 3. Where it stands, and how the span was measured

The corner is documented and the coordinate is derived, so the position is tagged `inferred` —
the same rule the Green Tree's placement uses.

- Modern **Kinzie and Canal** intersection centre, from OpenStreetMap (three shared nodes, mean
  41.889068 N, -87.640156 W) = EPSG:26916 **E 446891.7, N 4637657.8**, local **N +262.0**. Kinzie
  Street is one of the streets that survives on its 1835 alignment, and it runs east-west, which
  is also this archetype's zero-rotation orientation.
- The deck centreline sits on that northing. Its ends sit where the **traced 1834 waterline**
  crosses it — west bank local **E −117.52**, east bank local **E −45.69** — read off
  `data/terrain/epochs/e1834_harbor_cut/river.geojson`, the same Wright 1834 segmentation the
  ground and the river are built from. **Span 71.83 m.** It agrees with the reach's drafted mean
  width of 72.9 m to about a metre, which is the check that the number is reading the map at this
  station rather than averaging it.
- The modern channel was deliberately not used. It is a dredged and walled successor; measuring
  against it would put an 1832 bridge's abutments on nineteenth-century engineering.

**The span overstates the clear span, and by an unknown amount.** Cleaver puts the abutments "in
the shallow water near the banks" — inside the drawn line — and nobody recorded how far inside.
Landing the deck exactly on the traced waterline was chosen because that line is the one thing
here that is evidence: the terrain surface crosses Z = 0 along it by construction, so the deck
ends where ground meets water. An inset would have been a second invention stacked on the first.
The carried uncertainty, ±20 m from the georeference, is larger than the difference being argued
about.

One thing the corner does **not** say: modern Canal Street at this northing lies **63 m west of
the traced 1834 west bank**. "The south-east corner of Kinzie and Canal" is where the approach
began, not where the bridge did. That is a fact about two streets, not an error bar.

---

## 4. What is invented

**SUPERSEDED 2026-08-10 BY §6 AND §6a, and kept because it is what the thinner evidence honestly
looked like.** The middle of this bridge is described after all: two bents, not fifteen cribs.
L29 is Resolved and the invention that remains — where along the span the two stand — is **L31**.
Read this section as the state of play before the footnote at Andreas pp. 631-632 was read; the
paragraphs below are unchanged.

`docs/LIBERTIES.md` **L29**. Fifteen cribs stand in the river at the archetype's default 4.5 m
spacing over a 71.83 m span, and **no source describes the middle of this bridge at all**.
Something had to hold up seventy metres of log stringer, so intermediate supports are not the
invention; their number, spacing and form are. The default was kept rather than replaced with a
fresh number, because a new number would look like a finding.

It is also the invention the confidence view cannot show: the tint on a crib grades what a crib
*is*, not how many there were. A visitor sees a regular colonnade marching across the water and
reads it as a fact about the bridge.

Beyond that: the stringer scantlings, the puncheon deck pitch and the abutment fill are the
archetype's, unstated on the record, and the railing is deliberately absent — an absence argued
in `generators/archetypes/bridge_timber.py` and stated as `inferred` on the record, because a
railed deck reads as considered infrastructure and an unrailed one reads as a plank over water.

---

## 5. A correction to this project's own dossier

`docs/research/03-structures-north.md` §5 gives both branch bridges as "about 10 ft wide,
clearing the water by about 6 ft" and tags the pair `[DOC]`. **Only the width survives.** Ten
feet is Cleaver's and now has a source record. The six-foot clearance has none: the pages that
carry the width, the abutments, the stringers, the 1832 date and the 1839 replacement say
nothing about a height above the water, and a direct search of the same host for the phrasing
returns nothing.

The figure is kept — it is plausible for a stringer bridge on cribbed abutments in shallow water,
and it is the dossier's — but the record tags `clearance_m` **inferred**, and
`bridge_timber_params.py`'s docstring is corrected in the same slice so that the constant's name
stops asserting what it cannot show. Promote it if the page behind it is found.

---

## 6. The middle of the bridge is described after all — 2026-08-10

Four of §7's threads were pulled the same week they were written down, and the second one paid
for all of them. **Andreas prints, as a footnote at the foot of pp. 631-632, a signed statement
by four men who used these bridges** — J. D. Caton, John Bates, Charles Cleaver and John Noble —
agreed at a meeting of old settlers late in the fall of 1883 and handed to the editors by Bates.
Source record: `old_settlers_bridges_1883`. It reads, in the part this project can defend:

> ...both bridges were built on abutments and two "bents." The abutments were built of logs in
> the shallow water near the banks. The bents were of four heavy logs, resting on the bottom, in
> deeper water. Stringers of heavy logs stretched from the abutments to the bents, and between
> the bents. On these stringers puncheons or split logs were laid for a floor. These bridges were
> about ten feet wide and without railings, for the first few years, after which guards, or
> railings, were added. These were both wagon bridges, and were about six feet above the water,
> so that teams passed under them on the ice freely.
>
> Cleaver remembers driving across the first bridge over the North Branch; it was a wagon bridge,
> ten or twelve feet wide.

**Why this was missed, and it is not an excuse.** It is a footnote in small type under the very
paragraph this project has been quoting for the structure — "It was formed of stringers and only
fitted for foot passengers" — and it is badly OCR'd in the archive.org index, so a phrase search
for *bridge* does not reach it. It was found by reading the printed pages either side of the
Wolf Point narrative rather than by searching for the answer. **Both scans were read against each
other** (`historyofchicago01andr` and `historyofchicago01inandr`) because neither OCR is
trustworthy alone; every sentence quoted above is one on which the two independently agree. The
South Branch dates in the same footnote are one on which they do **not** agree, and nothing in
this dataset cites them.

What it settles, in the order the record is wrong:

- **The middle of the bridge — `pier_spacing_m`, and it is the big one.** L29 says in as many
  words that "nothing anybody wrote describes the middle of this bridge at all", and puts fifteen
  cribs in the river on the archetype's 4.5 m default. The letter says **two bents**, each of
  **four heavy logs resting on the bottom**, in the deeper water between the log abutments. Two,
  not fifteen. The most conspicuous invention in this structure turns out to be answerable.
- **`pier_kind`, and this record's reasoning was inverted.** The record adopts `crib` and argues
  that the Kinzie Street page's "Wood, Fixed, Bent" is "a modern editorial classification applied
  uniformly down a column". It is nothing of the kind: **"bents" is the settlers' own word**, and
  Cleaver — the eyewitness this record set against the table — signed it. The table is very
  probably reading this footnote. A bent of four heavy logs standing on the bottom is not a crib.
- **`clearance_m` is documented, and the reason is better than the number.** "About six feet above
  the water, **so that teams passed under them on the ice freely**." The clearance is not a
  construction convenience; it is the winter road under the bridge. `docs/research/03-structures-north.md`
  §5 tagged the figure `[DOC]`, this record demoted it to `inferred` for want of a page, and the
  page exists. The dossier was right and the demotion was the correct thing to have done in the
  meantime.
- **The deck** is `puncheons or split logs`, stated rather than inherited from the archetype.
- **`railing`** — "without railings, for the first few years, after which guards, or railings,
  were added". The record's `false` survives for a scene three years after the build, but it is
  now an inference against a stated timeline instead of an argument from silence, and "the first
  few years" is exactly the kind of phrase that will not settle 1835 on its own.
- **The build date stays disputed and the dispute gets a third signature.** The letter's opening
  clause has the North Branch bridge built "in the winter of 1831 and 1832", which is Cleaver's
  1893 date again — but now over four names, one of them Caton's. Andreas's own prose says summer
  1832. Nothing here breaks the tie; the record keeps Andreas and now records that the other
  reading has four men behind it rather than one.

**And a fact for the 1833-1835 gap** (§7 thread 3), from Andreas's main text on the same subject:
a committee of G. W. Dole, Madore B. Beaubien and Edmund S. Kimberly was appointed in December
1833 "to see that they were properly repaired", and "in September the corporation paid $166.67 on
account of repairing". That does not say what was done to the North Branch crossing, but it dates
and funds work on it in the window where this record has always said *something* happened and
nothing said what.

**What it does not settle is the approach**, which is why the bridge still arrives nowhere. No
sentence anywhere describes how a wagon got from the bank up onto a deck standing six feet above
the water. The letter tightens the problem rather than solving it: these were **wagon** bridges,
so an approach at each end is now attested by implication and is still undrawn and undescribed.

### 6a. The repair, and what the archetype had to learn — 2026-08-10

All four corrections landed the same day as the finding, record and mesh in one commit (the four
values are mesh inputs, so neither half could travel alone). `clearance_m` is `documented`;
`pier_kind` is `bent`; `deck_kind: puncheon` states the floor the archetype had been supplying
silently; and `pier_spacing_m` is **gone**, replaced by `pier_count: 2`.

**The last of those is the one worth carrying to other archetypes.** `bridge_timber` asked for a
spacing and divided the span by it, so its output was a colonnade by construction — and a spacing
is a builder's convenience that no witness would ever record. The evidence class available for a
structure like this is a **count** and a **form**: how many stood in the water, and what they were
made of. Editing 4.5 m to 23.94 m would have fixed this bridge and left the next one to be caught
by the same accident, so the parameter changed rather than the number, and the spacing survives
only as the fallback a crossing whose middle nobody described still needs.

**Two things the repair could not do, both recorded in `docs/LIBERTIES.md` L31.** The letter
locates the bents by depth — "resting on the bottom, in deeper water" — which is unusable here:
no source gives the channel's bed profile at this station and nothing below the waterline is
modelled, so "deeper water" cannot be converted into a station. They are built at the third points
of the span, which is a builder's habit and not a finding. And three spans make each stringer run
23.9 m, longer than any timber that was being moved; the runs were spliced somewhere, nothing says
where, and the mesh shows one log per bay rather than inventing joints.

**A note on what the model can carry from a source.** The most specific phrase in the whole
paragraph — *resting on the bottom* — is precisely what distinguishes a bent from a driven pile
bent, and it is invisible in a reconstruction that models neither the riverbed nor anything much
below the waterline. Above water the two are the same picture. What the visitor gets is four heavy
logs per support instead of three light ones; the rest of the sentence lives in the record.

## 7. Open threads, in the order worth pulling

1. ~~**The 1834/1835 Wabansia and Kinzie's Addition plat**~~ — **pulled 2026-08-10, and it is a
   negative finding.** The plat is the sheet this project already holds as `hathaway_1834` (LoC
   `g4104c.ct007620` = "Chicago with the school section Wabansia and Kinzie's addition"), and it
   is already georeferenced here, so the crossing could be inspected at its own fitted pixel
   rather than hunted for by eye. **Neither 1834 sheet draws a bridge.** On Wright 1834
   (resource-space px ~1262-1365, 1447) the pink Kinzie Street band and its black boundary lines
   stop dead at each traced waterline and nothing spans the channel. On Hathaway (native px
   ~2000-2183, 2747) the street lines likewise stop at the bank, and the only mark inside the
   channel at the crossing station is the letter **H** of "BRANCH", lettered down the water — a
   hatched capital that reads convincingly as a plank-and-stringer symbol until it is enlarged,
   and is recorded here so the next reader does not rediscover it as a bridge. Both sheets draw
   the *street*; a platted street is a dedication, not a structure. Method is reproducible: fit
   each sheet's committed GCPs, invert the affine at the record's deck line, fetch that IIIF
   region.
2. ~~**Andreas vol. I at page-image level**~~ — **pulled 2026-08-10, and it paid**: see §6.
   Read the pages, not the index. The full-text index missed the single most informative
   paragraph in the volume about this structure.
3. **The Trustees' minutes, and they now answer two questions rather than one.** Besides what the
   1833-35 repair money bought (below), they are the likeliest home of anything describing where
   the two bents stood or how the approaches were made — the two things §6a could not settle. A
   voucher or a specification would be worth more here than another narrative.
4. **What happened between 1833 and 1835.** Narrowed, not closed — §6 gives a repair committee
   (December 1833) and a payment ($166.67, September 1834). The Trustees' own minutes are the
   likely home of what the money bought.
5. ~~**The six-foot clearance**~~ — **found**, §6, and **promoted to `documented` on the record
   2026-08-10** with the re-bake that had to travel with it. It is Andreas p. 632, and the
   dossier's tag was right.
6. **New, and it is the last thing standing between this bridge and the ground:** the approach.
   Nothing describes one. §6 makes it harder to leave out — a wagon bridge implies a way for a
   wagon to reach the deck — and no better candidate document than the Trustees' minutes has
   turned up.
