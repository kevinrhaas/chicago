# A count of namesakes is not evidence — the land sales' second discriminator (T-0697)

**The question the ticket asked.** The land-sales resident crosswalk matched a purchaser
in the Illinois tract-sales register to a person of 1835 only where the residents layer
held **exactly one** person of the surname and the forename agreed. T-0670 found the
opposite failure on the directory side — a rule that bound too readily on an initial —
and split this one out: *"Decide what the land sales' discriminator is — a purchase date
inside the person's own bounds, a trade, a lot the person is otherwise placed on — and
hold it to the same standard T-0696 sets for the directories."*

**The measurement that made it a ticket.** The middle clause is a count of namesakes, and
a count of namesakes is a fact about the rest of the town rather than about the reading in
hand. So the rule fired LESS as the town grew truer: seating 531 people (T-0514) turned
nine matches ambiguous — Carpenter, Dole, Fullerton, Haddock twice, Heacock, Sweet,
Burdick, Wooley — and made six possible for the first time. A net loss of three rulings
with nothing new read.

## The ruling, and it is two answers

**1. The forename decides, across the rivals.** The surname GATHERS the people it might
be; the forename says which. A reading is put to every person of the surname and named
onto the one it agrees with, on the merge rules this project already ratified in
`data/research/residents/identity_master.json` and restated nowhere else:

| | |
|---|---|
| M1 | the same name, through `tools/name_agreement.py` — the tightening T-0670 made for the directories, contractions and one-letter spellings and all |
| M2 | an initial attaches to the one full forename carrying it |
| M3 | a middle initial on one side and absent on the other, **with no rival carrying a different one** |
| R3 | an initial with two or more rivals: refused with the rivals named, never guessed at |
| R4 | two full forenames that differ, and its reading at one letter's remove — two middle initials that differ |

Two survivors or none is still a refusal, which is what the old rule did to all of them
and is right when it is the forename saying so. What changed is that the refusal now
names the rivals: *"there are 5"* never said which five people refused the reading.

Three refusals are new, and each is a case the namesake count reached by accident:

* **A middle initial that disagrees.** `KING JOHN R` is not John Lyle King.
* **M3's guard, which is the whole of M3.** `WRIGHT JOHN F` is not John Wright while John
  S. Wright stands beside him.
* **A suffix says which man of the name is meant.** `CHURCH THOS JR` is the son of a
  Thomas Church, and the town's one Thomas Church is not said to be either man.

And the same rule reads from the other end (`namesake.collide`): two readings named onto
ONE person are put back to each other, and refused whole where they are not the same man.
`BOND HARVEY` and `BOND HEMAN` both meet an `H Bond` and the initial cannot say which;
`WENTWORTH ELIJAH SEN` is the Wolf Point father against a town holding one card. Keeping
the first reading and dropping the rest would be the count of namesakes again, wearing a
hat.

**2. No second discriminator may break what is left.** T-0697 named three, and all three
are refused. The reasons live in `tools/namesake.py`'s `REFUSED_DISCRIMINATORS` rather
than in this page, so a later run reviving one argues with a record:

* **A purchase date** tested against the person's arrival refuses nobody. A man may enter
  ground in a county he has not yet moved to, and in this register most of them did — 318
  of the 387 ring sales fall in 1835, a year behind the town's own lots.
* **A trade** has nothing to compare. The register's only column near one is Social
  Status, blank on 874 of 953 rows and elsewhere a single letter. This is where the
  directories' answer (T-0696: a trade may NARROW a tie and never make a match) has no
  counterpart — they had a trade printed against the name and this register does not.
* **A lot the person is otherwise placed on.** Preferring the rival the town has already
  put on the ground is how a reconstruction invents a fact. T-0696 refused a premises for
  this reason and it holds harder here: the register names a purchaser and never an
  occupant.
* **The register's own Residence column**, added to the list while measuring: it reads
  COOK, a state, or UNKNOWN, and every rival of a surname in the residents layer is a
  person of Cook County already.

## What it moved

| | before | after |
|---|---|---|
| purchaser spellings matched | 38 | 139 |
| people of the town they reach | 35 | 124 |
| refusals | 393 | 292 |
| entries carried onto cards (consolidation pass 3) | 180 | 421 |
| records of the register carrying a ruling | 953 of 953 | 953 of 953 |

One match was LOST: `NEWBERRY WALTER S` against Walter **Loomis** Newberry, refused on the
middle initial. The register's other spelling of him, `NEWBERRY WALTER L`, still names
him, so the man keeps his citation and the reading that disagrees is filed rather than
folded in.

**The gate.** `tools/namesake.py --self-test` runs in `check.sh` beside the directories'
two rule modules, for the reason T-0696 gave when it added those: the crosswalk is
re-derived by the gate and the rule it is re-derived BY was not, so a loosened rule would
re-derive the crosswalk quietly and pass everything after it.

**What this did not do.** No grade moved, in either direction: a land entry is a second
source about a TRANSACTION rather than about who was living at Chicago on 1 July 1835.
The crosswalk is still proposals, and `tools/spend_land_sales.py` still writes two fields
and no others. The 292 refusals are rivals still standing.
