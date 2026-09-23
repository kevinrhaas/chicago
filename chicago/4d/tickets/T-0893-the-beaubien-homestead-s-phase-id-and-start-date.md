---
id: T-0893
title: The Beaubien homestead's phase id and start date still say 1817, and Andreas's own pages say the factory building reached Beaubien in 1822
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-11
pr: 1142
claimed_by: run 9/11/2026, 1:13:22 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T18:44:17.260Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34631049207
---

The Beaubien homestead's phase id and start date still say 1817, and Andreas's own pages say the factory building reached Beaubien in 1822.

**Found by T-0718, 2026-09-06**, which read four Andreas pages directly off the
archive.org scan of `historyofchicago01andr` and did not act on this one because acting on it is
a rename, not a sentence.

`data/structures/jb_beaubien_homestead.json` carries a phase `factory_1817` whose
`documented_range.from` is `1817-01-01`, on the reading that Beaubien bought the American Fur
Company's factory building in 1817. **The 1817 belongs to a different building.** Andreas scan
p. 183: an army contractor named Dean built a house at the lake shore near the foot of Randolph
Street in 1815, and *"In 1817, Mr. Beaubien purchased this house, which was a low, gloomy building
of five rooms, for $1,000"*. Andreas scan p. 205 dates this record's building instead: *"In 1822,
after the abandonment of the United States Factory at Chicago, by Government, the factory building
was bought by the American Fur Company, and soon after sold to John B. Beaubien, who made it his
dwelling house."* That is the year and the chain `bk_afc_009` gives, so the two sources agree and
the "disagreement" the dossier used to report between them was the conflation talking.

**Why T-0718 left it.** Moving the bound makes the phase id a lie, and renaming the id renames
`assets/gltf/jb_beaubien_homestead__factory_1817.glb`, its two manifest entries, the 1835 sidecar
and a `docs/LIBERTIES.md` coverage line — a mechanical change across five kinds of file that is
its own demonstration. The correction is written on `documented_range.note` and in the dossier in
the meantime, so nothing is silently wrong.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The phase's `from` rests on Andreas p. 205 and `bk_afc_009` together, or the ticket says in
  writing why it should not.
- If the id moves with it, every reference moves in the same commit — record, both manifests,
  the sidecar, `docs/LIBERTIES.md` L17's Covers line, the published mirror — and `check.sh` is
  green including `--stale`.
- No confidence is upgraded. Two retrospectives agreeing on 1822 is still `inferred`.

**Links:** T-0718 · T-0595 · `data/structures/jb_beaubien_homestead.json` ·
`docs/RESEARCH/jb_beaubien_homestead.md` § 6 · `bk_afc_009`
