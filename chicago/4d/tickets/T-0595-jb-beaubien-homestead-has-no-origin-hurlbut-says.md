---
id: T-0595
title: jb_beaubien_homestead has no origin: Hurlbut says it was the United States Factory House, bought from the government in 1822 and moved into by Beaubien
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-04
pr: 818
claimed_by: run 9/4/2026, 5:38:15 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T23:02:11.902Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33926198826
---

jb_beaubien_homestead has no origin: Hurlbut says it was the United States Factory House, bought from the government in 1822 and moved into by Beaubien.

**What is missing.** `data/structures/jb_beaubien_homestead.json` is one of this
project's better-evidenced buildings and it says nothing about where the building came
from. Hurlbut's chapter does: "In 1822, Crafts succumbed, and engaged himself to the
American Fur Company bought from the U.S. the Factory House, located just south of Fort
Dearborn, to which Beaubien removed his family." The United States factory — the
government trading house — sold to the American Fur Company in 1822, with Beaubien's
family moved into it. That is an origin, a date, a former owner and a bearing from the
fort, for the house this project already models.

**The identity is settled.** `data/research/books/crosswalk.json` merges "Jean Baptiste
Beaubien" into this project's "Col. Jean Baptiste Beaubien" on the full name, the title,
the Milwaukee trade and the company, from a source Andreas did not copy.

**What it is not, and this is the whole risk.** It is a claim of 1822 about a building
standing in 1835 — thirteen years, and `hh_beaubien_jean_baptiste.json` already records
that Andreas says Beaubien built a NEW residence which is a different building and is not
modelled. Hurlbut's sentence is also ungrammatical as transcribed and the reading supplies
a missing "which". NOTHING MAY MOVE, RESIZE OR REGRADE THE STRUCTURE ON THIS EVIDENCE.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- `docs/RESEARCH/jb_beaubien_homestead.md` carries the Factory House origin with the
  quote, the citation and the thirteen-year gap stated as a limit and not as a footnote.
- The structure record gains the origin as a sourced NOTE. Its geometry, position and
  confidence are untouched — so no bake, and `validate.py --stale` stays green.
- Whether the building standing in 1835 is the same building is answered honestly, which
  most likely means "not established here", written where a visitor can read it.
- `tools/check.sh` green.

**Links:** T-0575 · `american_fur_company_hurlbut.json` bk_afc_009 (the Factory House) and
bk_afc_008 (the earlier 1819 trading houses at the old river mouth, a DIFFERENT building
that must not be conflated with this one) · `docs/GLB-CONTRACT.md` is not touched.
