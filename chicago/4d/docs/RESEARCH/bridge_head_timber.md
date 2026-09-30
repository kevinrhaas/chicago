# Bridge-head repair stock and the unlocated forks ferries

Ticket: T-1765 (split from T-1763 under T-1207). Scene date: 1835-07-01.
Record: `data/yard/bridge_head_timber.json`. Gate: `tools/measure_bridge_head_timber.py`.

## Evidence and reconstruction

The two branch bridges were timber crossings. Their committed research memos and
structure phases cite `old_settlers_bridges_1883`, `chicagology_kinzie_bridge`,
`chicago_democrat_1833_1835` and `chicago_democrat_1833_11_26`.
The 7 November 1833 ordinance protects bridge plank and timber against removal;
it does not say whether these were installed members or loose spare stock.
The Board's 4 December 1833 instruction appoints a committee to arrange repairs
to both branch bridges. It establishes repair planning, not an executed contract.
The bridge records also cite the 4 February 1834 repair specifications for oak
planks, pins, braces and railing. These support maintenance material as a subject,
not the existence, location or amount of a stockpile on the scene date.
The ordinance of 19 August 1835 is later context and does not establish July fabric.

Four small piles are reconstructed: one at each end of each branch bridge.
Nothing establishes that four piles stood there, their quantity, ownership or
stacking. The existing yard renderer draws squared timber, a simplified stock
form rather than an attested puncheon profile. Each stick is 3.048 m long, reusing
the documented ten-foot deck width as a plausible repair length, and 0.2 m square.
Three courses of four, four and three sticks give eleven per pile and forty-four
total. All of this stock remains reconstructed; L306 records the liberty.

## Placement

The 6 m back-off and 6 m lateral offset are chosen reconstruction rules. They are
not measured stockpile locations and are not forced by the evidence. Deck ends
are computed from the committed footprint bounds, including the midpoint across
the deck width: structure.position is a footprint corner, not a centerline.
At each end the rule selects whichever candidate side has higher committed ground.
The resulting pile edge clears the deck corridor by 4.08 m, accounting for the
pile's 0.4 m half-width. All sixteen pile corners must be on dry modelled ground.
A terrain or bridge edit must be reconciled against this gate; positions are not
silently accepted as unchanged.

| Bridge | End | Pile ENU, metres | Side | Ground, metres |
|---|---|---|---|---|
| north_branch_bridge | west | [-123.5, 256.02] | south | 1.18 |
| north_branch_bridge | east | [-39.67, 256.02] | south | 1.22 |
| south_branch_raft_bridge | west | [0.82, -170.58] | north | 1.14 |
| south_branch_raft_bridge | east | [68.84, -182.23] | south | 0.97 |

## Why no forks ferry landing is drawn

The Miller-Clybourn ferry licence of 2 June 1829 establishes earlier service.
Andreas describes Miller as the original possessor of the old ferry scow and
credits him with the North Branch bridge of 1832. This is consistent with
replacement but does not date cessation or exclude parallel ferry service.
The Sauganash memo says Beaubien's South Branch canoe ferry was probably
superseded, explicitly an inference.

The current source set does not establish an operating forks ferry or landing
form on 1835-07-01. The scene therefore omits a landing pending dated evidence;
it does not declare either ferry closed. Cook County licences and bonds after
1832 and contemporary newspaper notices could replace this omission.
The Harrison 1830 river-mouth ferry and later Lake House ferry are separate
questions; this record does not settle them.

No timber pile is added to the Dearborn drawbridge, outside the branch-bridge
scope. Shelters, toll houses and signs are omitted from this bounded parcel;
town-wide posts and walks remain with T-1211. These omissions do not assert
that such furniture was absent historically.
