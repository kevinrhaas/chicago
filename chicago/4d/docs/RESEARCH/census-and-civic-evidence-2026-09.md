# The census-and-civic evidence sweep, September 2026 — one dossier over eight domains

**What this is.** Between 2026-09-01 and 2026-09-05 this project read, in parallel, eight
bodies of evidence beside the newspapers it already held: the town's own civic lists, the
1830 and 1840 federal censuses, the parish registers, the books and reminiscences, the
directories, the federal land tract sales and the Newberry genealogical index. Each was
read by its own tickets, into its own directory, under one fixed shape (T-0492). Nobody has
written down what the sweep as a whole supplied. This is that page: per domain, what it
gave, at what tier, what it declared it read, what its crosswalk against the town's people
concluded, and — the part that outranks all of it — **what it is allowed to assert**.

**What this is not.** It is not a research finding. Every number here is copied or counted
from a committed record, and every one carries the command that reproduces it. Run them from
`chicago/4d/`.

**The companion documents.** `docs/RESEARCH/resident-grading-policy.md` is the ladder;
`docs/RESEARCH/residents_1835.md` is the population layer's own dossier;
`chicago/reference/resident-research/README.md` indexes the cohort research packages and the
programme audit; `chicago/reference/census1840/README.md` indexes the 1840 deposit.

---

## The rule for what any of this may assert

The owner ratified the grading ladder on 2026-09-03 and it is the whole answer.
Read [`resident-grading-policy.md`](resident-grading-policy.md) before grading anybody; the
short form, and the parts of it this sweep bears on:

| what the sweep can produce | what the ladder does with it |
|---|---|
| the 1835 poll list **and** another independent source | **G1a → `attested`** |
| a contemporary record naming the person in Chicago (the 1833–35 press) | **G1b → `attested`** |
| two in-window records from **different class families** — civic · press · parish | **G1c → `attested`** (convergence, T-0699) |
| the 1835 poll list alone | **G2a → `inferred`** |
| an 1833/1834 list (poll, tax, the 1832 muster) **with another source** | **G2b → `inferred`** |
| the St Cyr register inside 1833–1835 | **G2c → `inferred`** |
| Fergus 1843 or Norris 1844 naming a person the town already carries, with a trade or address | **G2d → `inferred`** |
| a post-office letter list of 1833–35 **and something else** | **G2e → `inferred`** |
| a single appearance and nothing else | **G3 → `inferred` + `projected_resident`** |
| every appearance describes a date after 1835, and the town does not carry the person | **G0 → `not_1835_resident`** |

The owner's sentence, verbatim, is the one that governs the two latest domains here:
*"1839/1840 alone is never a 1835 resident (later evidence only)."* So the 1840 census, the
1839/1843/1844 directories, the old-settler receptions and the Newberry cards can
**corroborate** and can **never mint**.

Three further rules the sweep is bound by, and every domain section below is written against
them:

- **A surname is a clue, not a resolution.** Every domain's crosswalk states its *refusals*
  as carefully as its merges, and the refusal counts below are typically far larger than the
  match counts. That is the sweep working, not failing.
- **A coverage declaration is a promise about what was NOT read.** An item declared and never
  reached is meant to fail the gate rather than pass quietly
  (`python3 tools/research_domains.py --check`).
- **Nothing here is published.** See [§ None of it reaches the site](#none-of-it-reaches-the-site).

---

## The eight domains at a glance

| domain | holds | tier | coverage declaration | what it crosswalked to the town |
|---|---|---|---|---|
| [civic lists](#civic--the-towns-own-lists-of-its-own-people) | records | 1 | [`data/research/civic/coverage.json`](../../data/research/civic/coverage.json) — 2 declarations, 5 items | 345 voter entries → 99 matched, 82 candidate, 164 unmatched |
| [1830 census](#census_1830--the-named-schedule-five-years-early) | records | 1 | [`data/research/census_1830/coverage.json`](../../data/research/census_1830/coverage.json) — 1 declaration, 2 leaves | 67 lines → 7 matched, 1 variant candidate, 25 surname-only refused |
| [1840 census](#census_1840--later-evidence-and-the-largest-single-body-read) | records | 1 | [`data/research/census_1840/coverage.json`](../../data/research/census_1840/coverage.json) — 2 of 3 image groups declared | 498 named heads → 5 matched, 5 candidate, 488 refused |
| [church registers](#church--the-parish-registers) | records | 1 | [`data/research/church/coverage.json`](../../data/research/church/coverage.json) — 2 declarations, 13 items | baptisms 8 merges / 18 refusals; St Cyr 40 candidate, 98 refusal, 384 unmatched |
| [books](#books--prose-read-the-way-the-newspapers-are-read) | claims | 1 | [`data/research/books/coverage.json`](../../data/research/books/coverage.json) — 19 declarations | 23 merges, 35 refusals |
| [directories](#directories--the-largest-body-of-claims-and-the-strictest-rule) | claims | 1 | [`data/research/directories/coverage.json`](../../data/research/directories/coverage.json) — 11 declarations, 163 leaves/pages | Fergus 1843: 110 matched / 354 refused · Norris 1844: 90 matched / 340 refused |
| [land sales](#land_sales--a-transaction-is-not-a-residence) | records | 1 | [`data/research/land_sales/coverage.json`](../../data/research/land_sales/coverage.json) — 2 declarations, 95 sections | 431 purchasers → 35 matched, 396 refused |
| [Newberry index](#newberry_index--a-finding-aid-that-never-places-anybody) | records | 4 | [`data/research/newberry_index/coverage.json`](../../data/research/newberry_index/coverage.json) — 4 volumes | 788 leads ruled → 190 candidate, 598 refused, **0 matched** |

Reproduce the whole table's coverage half with:

```
python3 - <<'EOF'
import json, pathlib
for d in json.load(open('data/research/domains.json'))['domains']:
    c = json.load(open(pathlib.Path('data/research')/d['id']/'coverage.json'))
    decls = c.get('declarations')
    print(d['id'], d['holds'],
          '%d declarations / %d items' % (len(decls), sum(len(x.get('items', [])) for x in decls))
          if decls is not None else '%d image groups' % len(c.get('groups', [])))
EOF
```

`census_1840` is the one domain that answers in its own shape rather than the shared
`declarations[]` — it declares by image group, which the shared gate does not read. That
divergence is a known defect with its own open ticket (**T-0536**), and it is why the row
above reads differently from the other seven.

---

## `civic` — the town's own lists of its own people

**What it supplied.** The four Chicago voter and tax lists of 1833–1835 — the 1833 poll (30
entries), the 1833 tax list (115), the 1834 poll (115) and the 1835 poll (85), **345 entries
in all**, each carrying the line of `data/research/civic/text/voter_lists_1833_1835.txt` it
stands on. Beside them, the 1832 Black Hawk War Chicago enrolments (134 entries) and the 1835
town election return.

**Tier 1.** `chicago_voter_lists_1833_1835_irad` — Ingrid Latimer Schulz's IRAD transcription
as published by Genealogy Trails. The IRAD originals themselves nobody in this project has
seen, and the coverage declaration says so: what was read is the transcription, whole.

**Crosswalk.** 99 matched, 82 candidate, 164 unmatched, by list:

| list | entries | matched | candidate | unmatched |
|---|---:|---:|---:|---:|
| poll 1833 | 30 | 17 | 2 | 11 |
| tax 1833 | 115 | 31 | 6 | 78 |
| poll 1834 | 115 | 36 | 6 | 73 |
| poll 1835 | 85 | 15 | 68 | 2 |

```
python3 -c "import json;print(json.load(open('data/research/civic/voter_crosswalk.json'))['counts'])"
```

**What it may assert.** This is the *senior* domain of the sweep: it is the town's own record
of its own adult men, inside the scene window. The 1835 poll alone is rung **G2a**; with any
second independent source it is **G1a**. It is also the domain with the largest unmatched
tail — 164 entries the residents layer does not carry under any spelling — and that tail is
what the cohort research programme exists to work through.

**What it may not.** A poll list is a list of *voters*: adult men who turned out. It is not a
census, it carries no household, no age, no trade and no address, and its silence about a
person is not evidence of absence.

---

## `census_1830` — the named schedule, five years early

**What it supplied.** Chicago was enumerated in **Peoria County** in 1830, and this project
held only the county aggregates until T-0498 read the named schedule off leaves n580 and n582:
**67 committed lines**, plus four claims about the enumeration itself.

**Tier 1**, read `scan_verified` off the deposited images.

**Crosswalk.** 7 matched, 1 surname-variant candidate, 33 with no surname in the town at all,
25 refused as surname-only, 1 not a person.

```
python3 -c "import json;print(json.load(open('data/research/census_1830/resident_crosswalk.json'))['counts'])"
```

**What it may assert.** A name here is evidence that a person was in the enumerated district
in 1830 — not that they were in Chicago, and not that they were still anywhere near it in
1835. It corroborates an in-window record; it never stands alone.

**What is still unread.** The district runs on past leaf n584 and those leaves have not been
read — Peoria, Putnam and the territory attached (open ticket **T-0605**).

---

## `census_1840` — later evidence, and the largest single body read

**What it supplied.** 74 distinct FamilySearch page images, of which **39 now carry a
committed page reading** — 25 of the 25 in image group 1, 14 of the 25 in group 2, and none of
the 24 in group 3 (open ticket **T-0496**). From those pages: **498 named heads of household**,
the 26 free-white age bands wherever a page's columns close against the enumerator's own
printed footings, and the continuation sheets' industry, pensioner, disability and schooling
blocks.

Its own products are two: `serial_crosswalk.json`, the fingerprint attachment of read lines to
IPUMS household serials — **636 lines read on the 21 fingerprintable pages, 254 unique, 271
ambiguous, 111 none, 254 serials attached, 1 contested and withdrawn** — and
`composition_1840.json`, which carries counts and nothing else and is refused by its own
self-test if a name or a serial ever reaches it.

```
python3 -c "import json;print(json.load(open('data/research/census_1840/serial_crosswalk.json'))['counts'])"
python3 -c "import json;print(json.load(open('data/research/census_1840/resident_crosswalk.json'))['counts'])"
ls data/research/census_1840/pages/*.json | wc -l
```

**Tier 1**, `scan_verified`. The deposit and its workbooks are indexed in
[`chicago/reference/census1840/README.md`](../../../reference/census1840/README.md); the
reading rules are in
[`data/research/census_1840/README.md`](../../data/research/census_1840/README.md).

**Crosswalk to the town.** 498 named heads → **5 matched, 5 candidate, 488 refused.** That
ratio is the domain working correctly: 1840 is five years late, the hands are hard, and a
surname match across that gap is a clue.

**What it may assert.** Nothing on its own — rung **G0**. It corroborates an in-window record,
it calibrates what a Chicago household looked like, and the bridge from an 1840 line to an
1835 person is a separate adjudicated step (T-0505). The **ceiling** on the fingerprint method
is worth carrying here too: only 531 of the 964 IPUMS households have a globally distinct
age-band pattern, so 433 of them can never be separated by any reading of those columns, however
perfect. Naming those needs a second axis — the directories, the poll books, the registers.

---

## `church` — the parish registers

**What it supplied.** Two readings. **St Mary's baptismal register 1833–1835** (T-0503): all
eleven deposited page images read entry by entry — **57 entries, 267 named readings** — plus
eight claims about the place rather than about a family. And the **St Cyr registers** (T-0573)
by transcription: 513 marriage entries 1834–1839 and 13 deaths 1834–1837.

**Tier 1** (`st_cyr_register_ichr_v4`), the baptisms `scan_verified`, the St Cyr lists
`transcription_mediated`.

**Crosswalk.** Baptisms: 8 merges, 18 refusals. St Cyr: 40 candidate, 4 with no forename, 98
refusal, 384 unmatched, 5 ruled as making no change to the town.

```
python3 -c "import json;print(json.load(open('data/research/church/st_marys_baptisms_crosswalk.json'))['counts'])"
python3 -c "import json;print(json.load(open('data/research/church/st_cyr_crosswalk.json'))['counts'])"
```

**What it may assert.** A baptism, marriage or burial *inside 1833–1835* names people in the
town in the scene window and is rung **G2c** on its own; as a second class family beside a
civic list or the press it reaches **G1c**. Parent and godparent names in the window count the
same way. Entries after 1835 are later evidence like any other.

---

## `books` — prose, read the way the newspapers are read

**What it supplied.** 218 committed claims across six files, from nineteen declared reading
runs: Fergus' Historical Series Nos. 26–29 in full (T-0499, T-0500 — the 1843 directory, the
business directory, Wentworth's obituary lists, Beckwith on the Indians, Duncan's sketch),
Hubbard's 1911 autobiography in eight declared page ranges (T-0501), Hurlbut's *Chicago
Antiquities* pp. 28–36 (T-0575) and the ICHR *Vincennes* pages (T-0650).

**Tier 1** for the contemporary matter it quotes; a book's claim always carries a **verbatim
quote**, its locator, its `describes_date` and the entities it names, and the verbatim gate
rebuilds every quote out of the committed text and refuses one that differs by a character.

**Crosswalk.** 23 merges, 35 refusals.

```
python3 -c "import json;d=json.load(open('data/research/books/crosswalk.json'));print(len(d['merges']),'merges',len(d['refusals']),'refusals')"
```

**What it may assert.** A reminiscence written in 1881 or 1911 about 1835 is a *claim*, dated
by what it describes and not by when it was printed. Hubbard or Fergus naming a resident with a
trade or an address is rung **G2d**; recollection alone, sixty years on, is not an attestation.
What is still unopened is stated as plainly: H. H. Porter's *Short Autobiography* is a 66 MB
scan with a garbled text layer and nothing yet says whether it carries 1835 Chicago at all
(open ticket **T-0502**), and Moses and Kirkland's 1895 *History of Chicago* — the largest
Chicago work the Newberry index points at — is not held here at all (**T-0581**, **T-0582**).

---

## `directories` — the largest body of claims, and the strictest rule

**What it supplied.** **8,256 committed claims across eleven files** — by a wide margin the
largest body in the sweep — from eleven declared reading runs over 163 leaves and pages: the
1839 Chicago directory off the Internet Archive scan (T-0506, T-0664, T-0665, T-0666), Fergus's
1843 (T-0571, T-0589) and Norris's 1844 (T-0566, T-0567, T-0568, T-0576). A directory entry is
three facts at once — a name, a trade and an address — and is kept as one claim carrying the
printed line unedited.

**Tier 1**, `transcription_mediated` off committed page text.

**Crosswalk.** The refusals are the story:

| crosswalk | matched | refused |
|---|---:|---:|
| Fergus 1843 → 1835 | 110 | 354 |
| Norris 1844 → 1835 | 90 | 340 |
| Norris 1844 advertisers → 1835 | 16 | 140 |

and the 1839 directory's four passes, which report by population rather than by match/refuse:
147 residents matched to exactly one entry, 52 ambiguous, 65 contested, 285 refused as
surname-only; 123 voters matched to one entry; 334 letter-list names matched to one entry
against 653 refused.

```
python3 -c "import json;print(json.load(open('data/research/directories/fergus_1843_crosswalk_1835.json'))['counts'])"
python3 -c "import json;print(json.load(open('data/research/directories/fergus_1839_crosswalk_1835.json'))['counts'])"
```

**What it may assert.** Rung **G2d**, and only that: Fergus 1843 or Norris 1844 naming a person
**the town already carries**, with a trade or an address, is `inferred`. A directory of 1839,
1843 or 1844 never mints an 1835 resident — it is the owner's "later evidence only" sentence in
its purest form — and the address it prints is a *later* address, whose back-projection to 1835
is its own adjudicated question (`address_back_projection.json`, and the open ticket **T-0669**).

---

## `land_sales` — a transaction is not a residence

**What it supplied.** The Illinois State Archives' *Public Domain Land Tract Sales* register,
read over 95 declared sections in the two townships the town stands on and the five that ring
them, for every sale dated on or before 31 December 1836: **953 sales, 431 distinct purchasers
as the register spelled them** (T-0675, T-0676).

**Tier 1.**

**Crosswalk.** 431 purchasers → 35 matched, 396 refused.

```
python3 -c "import json;print(json.load(open('data/research/land_sales/resident_crosswalk.json'))['counts'])"
```

**What it may assert.** Very little, on purpose, and the domain says so in its own first
paragraph: **a sale is a transaction, never a residence.** Speculators bought Chicago ground
from Ohio and New York without ever seeing it. The register's own *Residence* column is the
only thing here that speaks to where a purchaser lived, and it is the only part of the domain
that touches the residents layer as anything more than a name to test.

---

## `newberry_index` — a finding aid that never places anybody

**What it supplied.** **7,005 committed card readings** across the four volumes of *The
Genealogical Index of the Newberry Library* (T-0570, T-0578, T-0579, T-0580), and from them 788
ruled leads.

**Tier 4** — and it is the only tier-4 body in the sweep, deliberately. A card never places a
person in Chicago in 1835; it says *where a book is* that might.

**Crosswalk.** 788 leads ruled over 1,294 cards: **190 candidate, 598 refused, 0 matched, 0
discriminators found.** By class of refusal: 292 OCR-variant-only, 242 locality absent, 64
surname-only Chicago. 190 are testable in a work this project could hold.

```
python3 -c "import json;print(json.load(open('data/research/newberry_index/lead_crosswalk.json'))['counts'])"
```

**What it may assert.** Nothing about a person, ever. Its whole product is an **acquisition
list** — which of the works it points at are worth getting — and that list is what the open
tickets **T-0581**, **T-0582** and **T-0583** are spending. The zero in the matched column is
the honest reading of a finding aid, not a failure of the pass.

---

## What the sweep has not read

Stated here because a dossier that lists only what was read is the wrong shape:

- **1840, image group 3** — images 51–74, undeclared and unread (**T-0496**); the nine
  continuation sheets of group 2 (**T-0657**, **T-0658**, **T-0659**); the two disputed
  readings of printed pages 229 and 231 (**T-0559**); the right sheet that continues printed
  230 and 232 and is in no image anyone has identified (**T-0543**).
- **1830** — everything past leaf n584 (**T-0605**).
- **books** — Porter's autobiography (**T-0502**); Moses and Kirkland 1895 and the four works
  beside it (**T-0581**, **T-0582**); the Second Presbyterian register (**T-0583**).
- **the shape defect** — `census_1840` declares coverage in its own `images[]` shape, which the
  shared research-domain gate does not read (**T-0536**).

---

## None of it reaches the site

Every artifact named on this page lives in the repository and nowhere else. Two gates hold it:

- `tools/check.sh` → step **“the newspaper corpus resolves, and nothing under `data/research/`
  is published”** (`python3 tools/newspaper_corpus.py --check`). That is the absolute
  assertion, and it is why a reader can be told these directories exist without being told to
  look for them on the live site.
- `tools/publish.sh` copies a named payload to `site/chicago/4d/`; neither `data/research/` nor
  `chicago/reference/` is in it, and `tools/check_published.mjs` re-derives the mirror from its
  source, so an extra file in the mirror is a red gate rather than a silent publication.

What a visitor *does* see of all this is the walkthrough's resident cards, which carry the
grades the ladder assigned and link to the dossiers in `docs/` on GitHub — a link
`tools/check_dossier_links.py` proves resolves, both halves, on every run.
