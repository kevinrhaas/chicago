---
id: T-0717
title: The first Catholic church still stood at State and Lake in June 1837, and st_marys_church.json ends its phase on 1836-12-31
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-06
pr: 988
claimed_by: run 9/6/2026, 9:16:22 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T14:58:57.659Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34038457857
---

The first Catholic church still stood at State and Lake in June 1837, and st_marys_church.json ends its phase on 1836-12-31.

**Found by T-0650**, which read Joseph J. Thompson's *The Illinois Part of the Diocese of
Vincennes* in Illinois Catholic Historical Review vol. 4 (1921-22) under the books discipline.
The reading is at `data/research/books/claims/ichr_v4_thompson_vincennes.json`, claims
`bk_ichr4_001` and `bk_ichr4_004`, and the source record is
`data/sources/ichr_v4_thompson_illinois_vincennes.json`.

**The disagreement, in two sentences off one article.** Page 258: "When he came he found the
little church that Father St. Cyr had built standing near the southwest corner of what is now
State and Lake Streets". Page 256: Father Schaefer was the sole priest at Chicago "until the
early or middle part of June, 1837, when Rev. Timothy O'Meara sent by Bishop Bruté arrived".
So the church had not been moved by about mid-June 1837.

`data/structures/st_marys_church.json` ends its phase on **1836-12-31**. Its own note says why,
and says it honestly: the chicagology page dates the removal two ways, its building summary
saying 1836 and its Andreas transcription attributing the removal to O'Meara, who did not
arrive until after St. Cyr left in April 1837 — and the record took the EARLIER reading as the
conservative one for a scene dated 1835-07-01.

**THE SCENE IS NOT WRONG AND THIS IS NOT URGENT.** Either reading puts the church at Lake and
State on the scene date, by fourteen months on the record's own arithmetic and by 23 on this
one. What is at stake is the end bound and the reasoning behind it, not a building's presence.

**What this ticket is for.** The conservative choice was made against a page that contradicted
itself. A third source now agrees with the LATER of that page's two readings and dates it, so
"take the earlier because the sources disagree" no longer describes the evidence. Decide
whether the phase end moves, and write down which reading it rests on either way.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The date the canal lot auction actually happened is either found in a source this project
  holds or declared not held. The ICHR names the auction and dates neither it nor the
  valuation; without that date the removal has a floor (mid-June 1837) and no ceiling, and a
  phase end picked without it is a guess wearing a citation.
- `st_marys_church.json`'s phase end either moves or does not, and its note says which of the
  three readings it now rests on and why the other two were refused.
- The confidence grade is not touched to make the answer look better. A date that rests on a
  1921 retrospective is not `documented` because a second retrospective agrees with it.
- No geometry moves. The building does not change position, footprint or bearing on this
  ticket; only its phase and the prose that argues for it.

**Links:** T-0650 · `st_marys_church.json` · `chicagology_prefire216` ·
`ichr_v4_thompson_illinois_vincennes` · `bk_ichr4_001` · `bk_ichr4_004`
