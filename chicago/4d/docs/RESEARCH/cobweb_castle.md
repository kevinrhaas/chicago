# Cobweb Castle — the Indian Agency House — research dossier

**Record:** `data/structures/cobweb_castle.json` · **Scene status:** standing on 1835-07-01 on a
continuity argument only — this building is on the project's `watch_list` · **north bank, foot
of State Street** · `review_required: true`

The United States Indian Agency house on the north bank: begun under Charles Jouett's agency
(1816–18), finished and lived in by Dr. Alexander Wolcott from about 1820, nicknamed **Cobweb
Castle** during his bachelor years, and described exactly once, in *Wau-Bun*, of 1831.

---

## 1. Sequence

| date | event | source |
|---|---|---|
| 1803–4 | the **first** agency house is built beside old Fort Dearborn, **south side**, "a two-story log building, covered with split oak siding" — a different building, and not this one | Andreas |
| 1816–18 | Charles Jouett agent. His residence and the agency house of that period is "**a log building of two large rooms, about twenty steps from the river bank, on the north side**" | Andreas, quoting Mrs. Susan M. Callis (Jouett's daughter), who came here in 1816 |
| **c. 1820** | Wolcott appointed agent; "**finished and resided in a building commenced during Judge Jouett's incumbency**"; Andreas's chronology enters "'Cobweb Castle,' completed by Dr. Wolcott" against 1820 | Andreas |
| 6 Sept 1825 | Peoria County Court orders "**that the elections be held at the agency-house or Cobweb's Hall**" | Andreas |
| by 1823 | "All these houses were of logs — **the agency-house being afterward clapboarded part way up**" | Andreas, quoting David McKee |
| late 1830 | Wolcott dies; the house is "left unoccupied by the death of Dr. Wolcott" | Andreas |
| spring 1831 | Mrs. Wolcott leaves; *Wau-Bun*'s description belongs to this year | Andreas, Wau-Bun |
| autumn 1832 | Watkins's first school is kept "near **the old Indian agency-house in which Colonel Hamilton then resided**" | Andreas |
| **1835-07-01** | **scene date** — nothing attests the building either way | — |

## 2. The load-bearing passage

*Wau-Bun*, ch. XVII, describing 1831 — the whole of the physical evidence:

> "Proceeding from this point along the northern bank of the river, we came first to the Agency
> House, 'Cobweb Castle,' as it had been denominated while long the residence of a bachelor, and
> the sobriquet adhered to it ever after. **It stood at what is now the southwest corner of
> Wolcott and N. Water Streets.** Many will still remember it, **a substantial, compact little
> building of logs hewed and squared, with a centre, two wings, and, strictly speaking, two
> tails**, since, when there was found no more room for additions at the sides, they were placed
> in the rear, whereon a vacant spot could be found. **These appendages did not mar the symmetry
> of the whole, as viewed from the front**, but when, in the process of the town's improvement,
> **a street was maliciously opened directly in the rear of the building**, the whole
> establishment, with its comical little adjuncts, was a constant source of amusement to the
> passers-by. No matter. There were pleasant, happy hours passed under **its odd-shaped roof**
> … Around the Agency House were grouped **a collection of log buildings, the residences of the
> different persons in the employ of Government** … blacksmith, striker, and laborers."

Andreas corroborates the site independently — "the agency-house on the north side of the river,
**near where now is the foot of North State Street**, and which was facetiously called 'Cobweb
Castle'" — and his footnote cites *Wau-Bun* for the same corner.

## 3. What that passage decided in the record

- **The corner** (`position`, `inferred`): documented twice, coordinate derived, so the tag
  follows the weaker half.
- **The facade bearing**, 180: the street was opened at the **rear**, so the front faced the
  river. Corroborated by *Wau-Bun*'s account of the fort's people reaching the agency house by
  canoe.
- **The distance from the water**, 15 m: Mrs. Callis's "**about twenty steps from the river
  bank**". Two inferences ride on it — the length of a step, and the identification of the
  Jouett-era house with the one Wolcott finished.
- **The plan** (`form.plan_composition`, `documented`, `geometry: absent`): centre, two wings,
  two tails. The footprint polygon draws it; the archetype masses the polygon's bounding box,
  so the model shows a rectangle.
- **The roof** (`form.roof_type`, `conjectural`): the source says *odd-shaped*, and the model
  builds one gable. The value is a substitution, not a reading, and is tagged accordingly.
- **The cladding** (`documented`, `geometry: simplified`): "clapboarded part way up", after
  1823. The mesh shows bare hewn log.

## 4. Where the quadrant goes strange, and why the record still uses it

On the Wright 1834 sheet — read through this project's fitted affine — the north-bank block row
west of Wolcott Street has its south line at about local **N +130**, and the drawn north bank of
the main stem runs at about **N +98**. North Water Street occupies that strip. **There is no
block in the south-west quadrant**: south of the street is the river.

That is not a contradiction of *Wau-Bun*, it is the same fact from the other side. The house was
built about 1820, a decade before Thompson platted the town and thirteen years before Kinzie's
Addition; the street was laid out **behind** it, which is exactly what the "maliciously opened"
sentence complains about. So the record places the building on the bank between the platted
street line and the water.

## 5. What is invented

| attribute | state | what would upgrade it |
|---|---|---|
| `footprint` | `conjectural` — the SHAPE is *Wau-Bun*'s, every dimension is invented | any plan or measurement; agency accounts |
| `form.roof_type` | `conjectural` — "odd-shaped" cannot be built by this archetype | an archetype that masses a polygon rather than its bbox |
| `form.stories` | `inferred` — 1, from "compact little building" and from a house that grew sideways | any description |
| `form.wall_height_m` | `inferred` — 2.6 m, one storey of hewn log | — |
| `form.chimneys` | `inferred` — 2, from the room count implied by centre + wings | — |
| `documented_range.to` | `inferred` — the honest minimum; **no source gives this building a fate** | the *Chicago Democrat*; any 1836–40 recollection |
| `ground_contact` | `outside_modelled_ground` — 494 m east of the terrain box | ROADMAP § S2e |

## 6. Why the record is flagged for review

This is the administrative seat of the United States Indian Agency at Chicago — the office that
ran the 1833 Treaty of Chicago and the removal of August 1835, six weeks after the scene date.
`AGENTS.md` places that subject under a standing constraint. The record describes a building and
nothing else; the flag holds the scene short of `released` until someone qualified has read it.




## Future log picture-controls increment

Compound parts build the already reconstructed centre/wings/tails polygon rather
than its bounding box. Wau-Bun supports composition, not the exact plan/roof.
Dimensions, openings, intersections and stack positions remain reconstructed;
partial siding, 1835 survival and the tiny panorama subject remain unresolved.
The original T-2374 image match remains open.


## T-2374 picture-card increment — prepared 2026-11-03

The original ticket names `chicago_fort_dearborn_1831_1.jpg`. The actual full
1920×1042 reproduction was visually read for this increment: its heading credits
*Wau-Bun*, Juliette A. Kinzie, Chicago, 1857; its lower key names “Agency-House.”
Existing public-domain illustration record `kinzie_1857_chicago_1831_panorama`
identifies the independently inspected Wentworth 1881 reproduction, printed p. 86,
and preserves Hubbard’s criticism on pp. 86–87. Naming that existing source in
the structure’s research note makes the original ticket’s picture reachable in
the visitor’s Images tab, with the source’s existing creator, holder and rights
credits. No copy is uploaded or represented as a held thumbnail.

This is the same retrospective panorama already used for the Beaubien-group
question, not a new independent witness. The existing source’s Beaubien
identification qualification stays intact. The small Agency-House subject is
context for an unfinished comparison; it does not settle the five-part plan,
partial clapboarding, roof intersections or July 1835 survival. No camera,
image-match verdict, pictured-grade ruling, position, dimension, form attribute
or asset changes in this increment. The structure remains inferred by the
existing grade rule because no camera or affirmative pictured ruling is added.
T-2374 remains open; final picture matching is not claimed.

## T-2374 final form and canonical illustration view — 2026-11-10

This supersedes the old bounding-box, bare-log and unsolved-view limitations
above. The sole identified held picture is the keyed panorama
`chicago_fort_dearborn_1831_1.jpg` / `kinzie_1857_chicago_1831_panorama`.
The full 1920×1042 reproduction and its Agency-House subject were visually read.
The source register's Wisconsin Kinzie Agency House entry is a different,
text-only property record, not another picture of Cobweb Castle.

The composition follows Wau-Bun's centre/two wings/two tails and the engraving's
dominant front gable, receding ridge, subordinate side gable, three front marks
and small roof stack. The previous 13×9 m trial and transverse wing roofs made
an overly broad cabin with conspicuous exterior wing stacks. The bounded
replacement is 9×4.5 m: a 5×3.5 m centre, two 2×2 m wings recessed 1 m, and
two 1.5×1 m rear adjuncts. The wings' 2.0 m eaves sit below the retained 2.6 m
centre; all pitches remain 35°. One reconstructed 0.80 m square main-ridge
stack replaces the unsupported pair. The retained head is 5.05 m. The former
count was inferred, not textual evidence against the change. Exact metric
choices and unseen rear forms remain reconstructed. The 1.30 m partial board
band and central apertures' count, depth and relative set-out remain. Position
and bearing values do not change; no survey or terrain is fitted.

`data/reference_views/cobweb_castle/kinzie_1831.json` records a bounded
illustrative pose fitted to five hand-read front points at 1.009 px coordinate
RMS. Point uncertainty is about 2 px. Fixed 800 px focal length and 1.60 m eye
choose a drawing pose family; they do not recover a historical viewpoint.
`diagnostic_only` keeps that invented spot out of visitor navigation. Hidden
tail geometry, monochrome colour, exact finish date and scene-date survival are
outside what the picture establishes. Its canonical match record and actual
side-by-side carry final acceptance after native export; CPU projection is not
an image-gate verdict. Under T-3153, pixel offsets and disagreements between
plausible drawing fits are within tolerance; missing or wrongly shaped visible
elements still require a fix. See `L-cobweb-completion-2374`.
