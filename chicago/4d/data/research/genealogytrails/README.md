# Genealogy Trails, Cook County — what it is good for, and what it is not

`genealogytrails.com/ill/cook/` is a volunteer transcription site. It holds no
originals. Every page here is a copy of something else — a printed directory, a
church register printed in a historical review, a state archives database, a county
history, a newspaper column — and **a transcription is a pointer to its original**.
So the rule for citing anything out of this site is the one the repo already applies
to the voter lists: cite the ORIGINAL where the page names it, cite the page where it
does not, and say in the source record that this project has seen the republication
and not the original.

This directory is **the assessment, not the reading** (T-0556 phase 1). Nothing in it
is payload. No resident, household, business or structure record was written from it.

## What is here

| file | hand-authored? | what |
|---|---|---|
| `inventory.json` | yes | One row per section the county index links — 22 of them — with what it transcribes, the original it derives from, its era, a measured count of 1830s items, a grade and a state. Twelve of the rows carry `items[]` for the leaf pages a grade had to be earned on. |
| `claims/town_findings_genealogytrails.json` | yes | The five findings the assessment read in passing and would otherwise have lost. Verbatim quote, locator, `describes_date`, and — where a merge was tempting — the reason it was refused. |
| `text/*.txt` | generated | The 40 pages this pass read, cached as text. `tools/read_genealogytrails.py --fetch` writes them. |
| `html/index.htm` | generated | The county index page kept RAW, because the gate re-reads its links. |

`tools/read_genealogytrails.py --check` is the gate and `--self-test` proves its ten
assertions still fire when broken. The one worth naming: **the gate re-extracts every
link from the cached county index and fails if a section has no row in
`inventory.json`.** That is the ticket's acceptance — "covers every section the index
links, none skipped silently" — turned into something a machine refuses rather than
something a reader hopes.

## What it is good for

Four things, and they are worth a great deal:

1. **The town's own lists of 1833-1835** — the poll lists of the three town elections
   and the 1833 tax list, 345 names. **Already read**, under T-0493, into
   `data/research/civic/`. Do not spend a run on it again.
2. **Three complete Chicago directories** — 1839, 1843 and Norris's 1844 — free, in
   text, with trade and street for nearly every name. When this walk began,
   `data/research/directories/` was empty and no directory entry had ever been read
   into the project; while it was running, T-0566 (PR #704) read Norris's 1844 in full
   off the Internet Archive. So the 1844 here is now a **second reading** of a book the
   repo has — an independent transcription by a different hand from a different copy,
   which is the same thing `data/research/census_1840/second_readings/` exists for, and
   every place the two disagree is a name somebody read twice. The **1839 and the 1843
   are still unread by anyone.**
3. **The first Catholic register**, marriages 1834-1839 and deaths 1834-1836, printed
   in the *Illinois Catholic Historical Review* vol. 4 — 87 marriages with their
   witnesses named, six of them in the scene year, and nine deaths.
4. **Two rolls of men who stood in this town before the scene** — 134 Black Hawk War
   veterans enrolled at Chicago in 1832, and Fergus's 743 old-settler death notices,
   whose ages at death are birth years.

## What it is not good for

Most of the site. Fourteen of the 22 sections graded C or D: the naturalizations are
1922-1931, the news gleanings start in the 1850s, the biographies come from an 1897
album and are mostly untranscribed anyway, the townships are suburbs that did not
exist, the maps are twentieth-century. **The site's own narrative history of Chicago
begins at incorporation in 1837**, which is the single most useful negative finding
here: the town of 1835 is reachable through this site only through its lists, never
through its prose.

Recorded so that the next run does not re-walk twenty-two sections to learn it. The
site's `updates.html` is cached for exactly that reason — it is how a later pass sees
whether anything has been added since 2026-09-03 without walking the site again.

## The ladder

Everything here except the four 1830s items is **later evidence**, and carries
`describes_date` to say so. Under the grading ladder ratified by the owner on
2026-09-03, a later source alone never makes an 1835 resident: it corroborates, it
enriches, and above all it DATES. An 1844 directory entry is not a person in the 1835
town; an 1844 directory entry for a man who signed the 1834 poll list is that man's
trade.
