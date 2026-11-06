# People match: the paired-still acceptance rig (T-3417)

**The plan, "Photographic humans: the path", approved by the owner 2026-11-06:** *"A person is
done when a still of them sits beside a period photograph of someone like them and reads as the
same kind of picture. This is the buildings' image-match rule (AGENTS.md rule 11), applied to
people."* Each role's first figure goes to the owner as a side-by-side; once he approves one, the
rest of that role are held to it.

## Layout

```
data/people_match/reference_sets/<set>.json         period pictures of one role and decade
data/people_match/subjects/<id>.json                one person in the town and the rig's cameras
data/people_match/subjects/<id>.match.json          the match record (tools/people_match.mjs writes it)
kevinrhaas/chicago-evidence  evidence/people-references-<date>/<set>/   the pictures
kevinrhaas/chicago-evidence  evidence/people-match-<date>/<id>/         the stills and sheets
```

The pictures and stills live in the evidence repo (bulky evidence, owner 2026-10-23); this repo
holds what they are, by sha256, and the verdict.

**A reference set** (`<set>.json`): `id`, `role`, `label`, `years` `[first, last]`, the `scenes`
it judges, `evidence` `{repo, dir}`, and two or more `pictures`, at least one per band
(`near` pairs with the 3 m still, `far` with the 10 m one). Each picture has its `file` and
`sha256`, a `source_id` in `data/sources/` (rule 1: no picture without its record), `from` (which
copy and which crop of it, so it can be cut again), `caption` (the sheet's credit line) and
`shows` (what it shows). A set says what a person in that role and decade looked like, never who
the subject was: no likeness is asserted.

**A subject** (`<id>.json`): `person_id`, `scene`, `reference_set`, how the rig finds them
(`find`: `driven`, by their transport row, for now), what figure a verdict is bound to (`bound`:
the row's asset, clip and livery hashes), and the fixed rig: exactly two `stills`, `near` at 3 m
and `far` at 10 m, each at a `bearing_off_heading_deg` (clockwise from the way the subject faces),
a camera height `eye_m` over the ground (1.68 m: someone standing in the street, where the period
photographers stood) and an aim `aim_below_head_m` under the head bone; and a `clip` of about
5 seconds at one still.

**The match record** (`<id>.match.json`): when and against what build it was shot, the `bound`
values, every still's file and sha256 and camera, the sheets, a `verdict` (`unreviewed` |
`differs` | `matches`) and a `checklist` answering each of the plan's items: silhouette and fit of
the clothes, folds where cloth gathers, hat and hair, skin at 3 m, hands, how the figure stands or
sits, and how it moves. Each item is `{what, status, note}`; status is `open` (a visitor would see
the figure is not the pictures' kind of person in this respect), `reads`, `not shown` (no picture
in the set can say: colour in a monochrome print, hands the pictures hide), `within tolerance` or
`owner ruling`. Only `open` blocks `matches`.

## Shooting

```
node tools/people_match.mjs data/people_match/subjects/<id>.json [--published] [--evidence DIR]
```

It verifies the set's pictures by sha256 in a clone of kevinrhaas/chicago-evidence (default: a
sibling of this repo's clone, or `CHICAGO_EVIDENCE`), boots the app (the dev preview by default;
`--published` shoots a local `tools/publish.sh` mirror to judge a branch), finds the subject,
stops them as an approach does, and shoots in the town's own light with the HUD hidden. It writes
the stills, one side-by-side per band (the band's pictures | desktop | phone), a 5-frame motion
strip, and the match record. A reshoot of the same figure keeps the verdict; a reshoot of a
changed one keeps the notes and sets the verdict back to `unreviewed`.

`tools/test_people_match.mjs` (in `check.sh`) holds the records: sources resolve, the rig is the
fixed one, every checklist item is answered, and no verdict outlives the figure it was given on.
