---
id: T-0575
title: Hurlbut's Chicago Antiquities pages 28-36 on the American Fur Company at Chicago, read as claims about the trade the town actually carried
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0556
opened: 2026-09-03
closed: 2026-09-03
pr: 725
claimed_by: run 9/3/2026, 2:34:08 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T20:19:22.200Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33796887297
---

Hurlbut's Chicago Antiquities pages 28-36 on the American Fur Company at Chicago, read as claims about the trade the town actually carried.

Piece 5 of 6 of **T-0556 — genealogytrails.com Cook County: inventory every section of the site, grade what it holds for 1835 Chicago, and split the extraction of residents, households, businesses, structures and occupations into tickets**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**The source.** `text/americanfurco.txt` — Henry H. Hurlbut, *Chicago Antiquities* (Chicago, 1881),
pages 28-36, transcribed in full with its spelling kept. It names Hubbard, Beaubien, Crafts and the
Kinzies as the American Fur Company's Chicago men and describes what the trade did here.

**Why it is worth a run.** It is a size argument about the town, from a named book with a page
range, about people this project already models. Hurlbut's judgement — Mackinac the great
storehouse, "Chicago was the port and point of a very limited district of distribution" — bears
directly on how much fur-trade apparatus the scene should show, which is a question the
reconstruction currently answers by feel.

**What it is not.** Prose written in 1881 about the decades before the scene. It is a CLAIMS read
into the books domain, not a records read, and it is a judgement rather than an observation: no
building moves on the strength of it without the reasoning being written into
`docs/LIBERTIES.md`.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- The chapter read into `data/research/books/claims/`, every claim with a verbatim quote the
  domain's own gate rebuilds from the committed text, a locator naming Hurlbut's page, a
  `describes_date`, and `town_finding` set honestly.
- The four named men carried to `entities[]` with no merge asserted that the crosswalk has not
  stated a rule for.
- Anything that would change a structure or an asset is proposed in the ticket, not done in it.
- `gt_005` in `data/research/genealogytrails/claims/` is the one quote already filed; supersede it
  rather than duplicating it.

**Links:** parent T-0556 · `docs/RESEARCH/jb_beaubien_homestead.md` · T-0513 waits on this.


**Where it is.** Cached, in text, at `chicago/4d/data/research/genealogytrails/text/` — this
project's own committed copy, taken 2026-09-03. Do NOT re-fetch to read it; the cache is what a
later run has to be able to trust, and `tools/read_genealogytrails.py --fetch` is how it is
refreshed if it ever must be. `data/research/genealogytrails/inventory.json` is the grade and the
count this ticket was sized from, and `README.md` beside it says what the site is and is not.

**The shape.** T-0492 fixed it: a records file for a list, a claims file for prose, a closed kind
vocabulary, `reading: transcription_mediated` (nothing here is a scan read), a `coverage.json`
declaration for what was read, and a `crosswalk.json` whose refusals are written as carefully as
its merges — surname-only is always a refusal.

**The ladder.** The owner ratified it on 2026-09-03 and it binds this ticket: a source later than
1835 alone never makes an 1835 resident. It corroborates, it enriches, and above all it DATES.
Everything read here carries `describes_date`.

---

## PROPOSALS OUT OF THE READING (T-0575, 2026-09-03)

The acceptance says *anything that would change a structure or an asset is proposed in
the ticket, not done in it.* Nothing under `data/structures/`, `data/assets/`,
`data/residents/` or `data/scene/` was touched by this ticket. Four things the chapter
argues for, each with its own ticket:

1. **Hubbard's arrival is datable now — T-0594.** `hh_hubbard_gurdon.json` grades
   `arrival: 1818` as `reconstructed` and says the year "could not be traced to a sentence
   here". `bk_afc_004` is the sentence, with the day: Montreal 13 May 1818, Mackinaw 4
   July, Chicago "the last day of October or first day of November of that year". The
   two-day ambiguity must survive the fix.
2. **`jb_beaubien_homestead` has an origin — T-0595.** `bk_afc_009`: the United States
   Factory House, just south of Fort Dearborn, bought from the government by the American
   Fur Company in 1822, Beaubien's family moved into it. A note and a research page, not a
   regrade: it is a claim of 1822 about a building standing in 1835, and `bk_afc_008`'s
   1819 trading houses at the old river mouth are a *different* building again.
3. **The trade goods need a ruling before they need a model — T-0596.** `bk_afc_018`
   itemises about 130 articles of the Chicago-country trade of about 1828. Read with
   `bk_afc_005` and `bk_afc_012` the honest answer may be that the scene should show
   *less* fur-trade apparatus, not more, and that belongs in `docs/LIBERTIES.md` before
   anything is lettered.
4. **The two Kinzie households are half brothers — T-0597.** `bk_afc_015`, Hurlbut's own
   note. Half brother, in that form.

**And one thing this reading deliberately did NOT propose.** The chapter is a size
argument — Hurlbut's "a very limited district of distribution" (`bk_afc_003`) and
Hubbard's own "this place never had been preeminent as a trading-post, as this was not
the Indian hunting-ground" (`bk_afc_012`), from two men who did not copy each other.
That is a reason to ask how much fur-trade apparatus the town shows, and it is *not* on
its own a warrant to delete any of it: an 1881 judgement about the 1820s cannot by
itself remove a building placed on other evidence. The question is T-0596's, with the
reasoning going into `docs/LIBERTIES.md`, and it is not answered here.

**What the chapter settles outright.** The words "American Fur Company" do not belong
anywhere in the 1835 scene. Hubbard bought the company's entire Illinois interest in
1828 (`bk_afc_005`) and Astor sold the company in 1834 (`bk_afc_013`); whatever fur
trade stands in this town in the scene year is a private business, and a signboard
saying otherwise would be wrong.
