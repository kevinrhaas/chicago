---
id: T-0130
title: The signs should read as the trade wrote them, not as we label the building
state: done
epic: TOWN
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-08-21
closed: 2026-08-22
pr: 305
claimed_by: run 8/22/2026, 12:10:48 AM CT
blocked_on: null
needs_bake: false
---

The signs should read as the trade wrote them, not as we label the building.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

The signs should read as the trade wrote them, not as we label the building.

**The owner, 2026-08-21, on the Philo Carpenter board shipped by T-0066 (PR #291):**
*"philo would not have referred to his own place as log drug store, it would be philo
carpenter, drugs and medicines, or druggist or whatever he would have referred to himself
as on the sign, that may be different than the name of the building for us, the sign may
read differently historically."* And, of the next one: *"same with hogan's store."*

He is right, and he has supplied the evidence that settles it.

## The defect

`tools/generate_business_signboards.py` `_sign_text()` paints **the record's own `name`**,
dropping only a trailing parenthetical, and its docstring defends that as the point: *"the
card a visitor opens by tapping the board has to say what the board says."* Those are two
different objects and the generator collapsed them:

- **The record's `name` is OUR label for a STRUCTURE** — descriptive, disambiguating, written
  so a modern reader knows which building is meant: *"Philo Carpenter's Log Drug Store"*,
  *"Hogan's Store"*, *"Tremont House (the first)"*. The word "log" is in there because the
  walls are log; no druggist ever painted the construction of his own shop on his own board.
- **A signboard carries the wording the TRADE used** — the proprietor or firm, and the trade
  he practised, in the register a signwriter actually lettered.

So every one of the 33 boards is currently painted with a museum caption.

## The evidence the owner supplied — the businesses in their own words

Two Chicago newspaper advertisements, both from the paper's first weeks, both self-written:

**1. Philo Carpenter** (ad dated Nov 22 1833; the page carries "Chicago, Dec. 31, 1833"):

> PHILO CARPENTER, CHICAGO—ILL. Will keep constantly on hand, a general assortment of
> **DRUGS AND MEDICINES**, Oils, Paints, Dye-Stuffs, &c. &c. —ALSO— Dry Groceries, Glass,
> Nails, &c.

So his own order is **name first, trade second** — "PHILO CARPENTER" over "DRUGS AND
MEDICINES" — and the trade word he chose is *drugs and medicines*, not "drug store".

**2. Brewster, Hogan & Co.** (page carries "Chicago, Dec. 4, 1833"):

> BREWSTER, HOGAN & CO. *Forwarding & Commission* **MERCHANTS**, Chicago—Illinois.

Which corrects more than the wording: our label says *"Hogan's Store"*, but the firm was
**Brewster, Hogan & Co.** and its trade was **forwarding and commission merchants** — not a
store at all in the retail sense. The board should carry the firm, not a shorthand for one
partner.

Note what these two also show about LAYOUT, since T-0066 already varies it: both put the
proprietor on the top line in the largest letter, the trade beneath in a second face, and
the place ("CHICAGO—ILL.", "Chicago—Illinois") last and smallest. That is the period's own
hierarchy, taken from the sources rather than from a modern eye.

## What to do

1. **Separate the two fields on the record.** The structure keeps its `name` for the card
   and the search box; the sign gets its own wording, sourced independently. They are allowed
   to differ, and the smoke check that currently asserts *the painted name equals the card's
   name* is enforcing the wrong invariant — it must become "the board and the card agree
   about WHO this is" (the proprietor or firm appears in both), not string equality. That is
   a correction of the assertion, not a relaxation: say so where it is changed.
2. **Where a period advertisement survives, use the firm's own words and GRADE IT UP.** These
   two are attested wordings from period documents — the strongest evidence class this
   project holds for what a sign said — so their sign text stops being `reconstructed`. Record
   the advertisements as sources properly (the owner's images are in the conversation of
   2026-08-21; the citations are the Chicago paper of Dec 4 and Dec 31 1833, the Carpenter ad
   itself dated Nov 22 1833). **A research sweep of the surviving 1833–35 Chicago newspaper
   advertisements is the highest-value follow-up here** — every firm that advertised wrote its
   own sign copy for us. If that sweep is more than this run can hold, split it.
3. **For businesses with no surviving advertisement, reconstruct in the same register** —
   proprietor or firm, then trade, in period trade words (druggist, forwarding merchant,
   grocer, tailor, cabinet maker), never our descriptive building label and never the word
   "log". Keep those `reconstructed` and carded as such.
4. **Do not lose what T-0066 got right**: the variation scheme, the five mountings, the atlas
   that costs no triangles, and the rule that no two boards within 40 m are alike.

**Acceptance:** no board carries our descriptive building label; Carpenter's board reads in
his own advertised words and Hogan's carries the firm **Brewster, Hogan & Co.** with its
forwarding-and-commission trade, both graded on the advertisements and cited to them; every
other board reads as a proprietor and a trade; the card-and-board check asserts agreement of
identity rather than string equality; gates green.

**Links:** T-0066 (PR #291, the boards this corrects) · T-0039 (the layer) · L159 (the sign
scheme's liberty) · `tools/generate_business_signboards.py` `_sign_text()` ·
`data/sources/` (the advertisements need source records).

---

## Widened, 2026-08-21: do the whole set

**The owner:** *"i guess do a pass on all those signs and make sure they feel right for the
era."* So this is not two corrections — it is a pass over all 33 boards, and he has supplied
the material to do it from: **two full pages of Chicago newspaper advertising, 1833 and
1834**, in which the town's businesses write their own copy. Nearly every firm the model
names is on those pages, in its own words.

**These pages are the source, and they must be committed as one.** The owner supplied the
images in conversation on 2026-08-21; they are the Chicago paper of late 1833 (one page
carries "Chicago, Dec. 31, 1833" and a "CHICAGO PRICES CURRENT ... Reported for the Democrat
by P. F. Peck", which identifies the *Chicago Democrat*) and a page of 1834. **Ask the owner
to drop the two image files into `data/sources/assets/` before grading anything to them** —
a sign wording graded `attested` needs a citable source record, not a transcription in a
ticket. Until they land, the transcriptions below are the working text.

### What the pages give, transcribed (the businesses this town already models)

The register is consistent and it is the answer to "feel right for the era": **proprietor or
firm first and largest, the trade beneath, the place last and smallest** ("CHICAGO—ILL.",
"Chicago—Illinois"). Trades are named in the period's own words.

| firm, as it wrote itself | trade line, as it wrote it |
|---|---|
| PHILO CARPENTER | Drugs and Medicines; Oils, Paints, Dye-Stuffs; also Dry Groceries, Glass, Nails |
| BREWSTER, HOGAN & CO. | Forwarding & Commission Merchants — also Dry Goods, Groceries |
| JOHN H. KINZIE | Storage, Forwarding & Commission Merchant · Agent for the Troy & Erie Line |
| NEWBERRY & DOLE | Forwarding & Commission Merchants |
| HUBBARD & CO. | Commission & Forwarding Merchants (Gurdon S., Elijah K. and Henry G. Hubbard) |
| J. S. C. HOGAN | Dry Goods, Groceries, Hardware, Crockery and Glass Ware — "at his store in South Water Street, one door east of Dearborn" |
| P. F. PECK | corner of LaSalle and South Water — staple articles, salt, flour, butter, feathers |
| JOHN WRIGHT | Dry Goods (a long list), also Hardware, Crockery, Groceries, Boots and Shoes, Stationary, Tin Ware |
| C. & I. HARMON | Dry Goods, Crockery, Hardware, Wet and Dry Groceries |
| HARMON, LOOMIS & CO. | Dry Goods, Groceries, Crockery, Glass and Hardware |
| B. JONES | Grocery & Provision Store |
| J. L. WILSON & CO. | Dry Goods, Groceries, Hardware, Crockery, Glassware, Ready made clothing |
| DANIEL ELSTON & CO. | Chicago Soap and Candle Manufactory |
| PIERCE & ABBOTT | New Blacksmith Shop |
| MATTHIAS MASON & CO. | Blacksmithing Business |
| A. K. BOTSFORD | Tin, Sheet Iron and Stove Manufactory |
| BRIGGS & HUMPHREY | Carriage & Sleigh Making |
| RUSSELL & CLIFT | Chicago Wholesale and Retail Book & Stationary Store |
| W. MONTGOMERY | Boot & Shoe Making |
| J. D. CATON | Attorney & Counsellor at Law, & Solicitor in Chancery |
| G. SPRING | Attorney and Counsellor at Law |
| D. GRAVES | Chicago Ashery |
| J. BATES, JR. | Auctioneer |
| JONES & KING | (iron ploughs) |
| E. WENTWORTH | Public House |
| RICHARD J. HAMILTON | Clerk, Commissioners' Court, Cook County |

Note the spellings are theirs — **"Stationary" for stationery, "Sattinetts", "Merselles"** —
and period spelling on a board is part of feeling right for the era. Note also that several
of these firms are the SAME people the model already places, which means a board can now
carry the firm's own line instead of our shorthand.

### The pass, concretely

1. **Every board re-worded in that register** — firm, trade, and place only where the board has
   room; never our descriptive label, never the word "log", never a modern nickname.
2. **Where the pages give the firm's own words, grade the wording up and cite the page.**
   Where they do not, reconstruct in the same register and keep it `reconstructed`.
3. **Correct the identities the pages correct**, not just the wording — "Hogan's Store" is
   Brewster, Hogan & Co. (forwarding and commission) and/or J. S. C. Hogan's South Water
   store; the pages distinguish them and the model should.
4. **Let the trade lines drive the variation** that T-0066 already built: a druggist, a
   forwarding merchant, an attorney and a blacksmith should not letter alike, and the trade
   word is what makes them differ.

**Acceptance (widened):** all 33 boards read as the trade wrote itself, in the period's own
words and spelling; the firms the newspaper pages name carry their own advertised line, cited
to a committed source record; the rest are reconstructed in the same register; no board
carries a descriptive building label; the card-and-board check asserts agreement of identity
rather than string equality; gates green.

---

## More pages, 2026-08-21 — and now 1835, the scene year itself

The owner supplied five further newspaper pages, several of them from **1835** (they carry
"CHICAGO PRICES CURRENT" corrected to 1835, an "ARRIVALS OF VESSELS AT CHICAGO, 1835" table,
and a Post Office list of letters remaining "on the 31st day of March, 1835"). These are
**contemporaneous with the scene date of 1 July 1835** — the strongest possible evidence for
what a board said on the day this model depicts.

**The owner's prediction is confirmed by Carpenter's own 1835 advertisement**, which heads
itself:

> **PHILO CARPENTER**, *Wholesale & Retail Druggist*, **South Water Street**, Chicago
> — "has just received and now offers for sale, one of the largest and best selected
> assortments of **DRUGS AND MEDICINES**, Paints, Oils, & Dye-Stuffs, ever offered in the
> State of Illinois … Dry Groceries, Crockery, and Glass-Ware"

So the word is **druggist**, exactly as he guessed, and the board should read in that order:
the man, his trade, his street. Not "log drug store".

### 1835 wordings, transcribed (use these first — they are the scene year)

| firm, as it wrote itself | its own trade line | where it says it is |
|---|---|---|
| PHILO CARPENTER | Wholesale & Retail Druggist — Drugs and Medicines, Paints, Oils & Dye-Stuffs | South Water Street |
| J. S. C. HOGAN | Dry Goods, Groceries, Hardware, Crockery and Glass Ware | South Water Street, one door below Dearborn |
| NEWBERRY & DOLE | Storage, Forwarding and Commission Merchants · Agents for the Merchants Line | Chicago—Illinois |
| HUBBARD & CO. | Commission & Forwarding Merchants | Chicago—Illinois |
| JOHN H. KINZIE | Forwarding & Commission Merchant · Agent for the Troy & Erie Line | Chicago |
| WM. H. TAYLOR | Boot, Shoe & Leather Store | Dearborn street, a few rods north of Newberry & Dole's |
| JOHN HOLBROOK | New Store — Hats, Clothing, Boots & Shoes, Wholesale and Retail; Dry Goods, Groceries, Hardware, Crockery | — |
| P. PRYNE & CO. | Groceries (spring supplies), Scythes, Cradles &c | — |
| J. H. MULFORD | Watches and Jewelry · Watch Repairing | — |
| WILLIAM JONES · B. B. CLARKE | Hardware, Stoves &c — Cutlery, Nails, Iron, Steel; Stove Furniture, Iron Ware and Saw Mill Gearing | — |
| HARMON, LOOMIS & CO. | New Goods! — Dry Goods, Groceries and Hard Ware | — |
| JONES, KING & CO. | Dry Groceries; Leather; on consignment, whiskey | — |
| PETER COHEN | New Goods — Dry Goods, Groceries, & Clothing | — |
| MAGIE & WILKINSON | Boots, Shoes and Hats | — |
| DAVID CARVER | Lumber Dealer & Commission Merchant | Water street |
| L. W. MONTGOMERY | Boot & Shoe Making | — |
| RUSSELL E. HEACOCK | Counsellor and Attorney at Law | Chicago, Illinois |
| J. CURTISS | Attorney and Counsellor at Law, and Solicitor in Chancery | South Water street, first door west of Jones, King & Co. |
| JAMES GRANT · HENRY MOORE · EDWARD W. CASEY | Attorney & Counsellor at Law (Casey: office adjoining the Clerk of the Circuit Court) | — |
| COLLINS & CATON | Attorneys & Counsellors at Law, and Solicitors in Chancery | — |
| DR. J. H. BARNARD | (physician) at the New York House | Lake Street |
| JOHN DAVIS | Steam-Boat Hotel | North Water Street |
| J. T. TEMPLE | (two stores to let) | South Water street |
| F. J. CONANT | New York Cheap Wholesale Clothing Warehouse | — |
| PHILIP LAIRD · RICHD. J. HAMILTON | Administrator / Clerk of the Commissioners' Court | — |

Out-of-town houses also advertise here (Patterson, Gardner & Mather of Detroit "at the sign
of the Large Pitcher"; Cromelien, Brothers & Co. of New York) — **useful as register, not as
Chicago signs.** "At the sign of the Large Pitcher" is itself a period signboard convention
worth knowing about, but it belongs to Detroit and must not be hung here.

### What this changes about the pass

1. **Prefer the 1835 wording over the 1833 wording** where a firm advertises in both — the
   scene is 1 July 1835 and firms changed their line (Carpenter reads "Drugs and Medicines"
   in 1833 and calls himself "Wholesale & Retail Druggist" by 1835).
2. **Several boards can now name their street the way the trade did** ("South Water Street"),
   which is both period-correct and a quiet piece of wayfinding.
3. **The trade vocabulary is now evidenced, not guessed**: druggist, forwarding and commission
   merchant, attorney and counsellor at law, boot and shoe maker, watches and jewelry,
   hardware and stoves, lumber dealer. Reconstructed boards for unadvertised businesses should
   be built from THIS vocabulary.
4. **Some of these firms may not yet be in the model at all.** Where a page names a business
   the town should plausibly have and the model lacks, that is a research/placement question —
   note it, do not silently invent a building for it.

---

## The find, 2026-08-21: a Chicago sign named in its owner's own words

The last batch of pages carries Carpenter's fuller 1835 advertisement, and it names **his
actual signboard**:

> **PHILO CARPENTER**, *Wholesale & Retail Druggist*, **AT THE SIGN OF THE GOLDEN MORTAR**,
> South Water Street, Chicago — DRUGS AND MEDICINES, Paints, Oils, & Dye-Stuffs

**This is the thing L25 said we did not have.** L25 withholds the Wolf Point wolf because the
sign's IMAGE was never described; here a Chicago tradesman describes his own board, in print,
in the scene year. A golden mortar — the druggist's universal device — is therefore
**attested** for Carpenter's shop, not reconstructed, and it should be *painted on the board*
rather than merely named in text. The Detroit house advertising "at the sign of the Large
Pitcher" on the same pages confirms the convention was live and ordinary.

**Do not generalise the device to other trades without evidence.** A golden mortar is
Carpenter's because he wrote it down. Other shops get lettering unless their own advertisement
names a device.

### Further 1835 trades from these pages (extend the vocabulary)

Attorneys are thick on the ground and each writes the same formula: **JOHN DEAN CATON**,
**JAMES H. COLLINS**, **S. ABELL**, **ALBERT G. LEARY**, **LORENZO LELAND** (Ottawa),
**HENRY MOORE**, **JAMES GRANT**, **J. CURTISS**, **EDWARD W. CASEY**, **G. SPRING**,
**GEO. W. FORSYTH** (Ottawa) — *"Attorney and Counsellor at Law, and Solicitor in Chancery"*,
several giving an office by landmark ("first door west of Jones, King & Co.", "opposite the
Tremont House", "adjoining the Clerk of the Circuit Court").

Also new: **Doct. WM. H. KENNICOTT**, *Practical Medicine and Dentistry / Surgeon Dentist*,
office opposite the Tremont, Lake Street · **DR. W. G. AUSTIN**, *Botanic Medicines* ·
**GEORGE HOLSMAN**, agent for *Morison's Hygeian Medicine* · **SAMUEL LEWIS**, *Teaching of
Music* · **CHARLES HUNT**, *High School for Young Ladies* · **A. GARRETT**, *Auction and
Commission House* · a *Wholesale Grocery House* at the corner of South Water near the
drawbridge · *Tailoring "in the most Fashionable Style"* at the **Eagle Coffee House** ·
**JOHN DAVIS**, *Steam-Boat Hotel*, North Water Street · **P. PRYNE & CO.**, *New Store —
Dry Goods, Groceries, Hardware, Crockery, Boots, Shoes, Hats* · **MAGIE & WILKINSON**, *New
and Cheap Goods; Boots, Shoes and Hats* · **WILLIAM JONES · BYRAM KING · H. B. CLARKE**,
*Hardware, Stoves, Iron Ware and Saw Mill Gearing*.

**Two of these name their location by a neighbour**, which is a wayfinding gift: Taylor's boot
store is "a few rods north of Newberry & Dole's", Curtiss's office is "first door west of
Jones, King & Co.", Kennicott is "opposite the Tremont". Those relationships can be checked
against the model's own placements — and where they disagree, that is a placement finding
worth raising rather than burying.

**Ask the owner for the seven page images to be committed** to `data/sources/assets/` so the
gradings above can cite a source record. Until then they are transcriptions in a ticket, and a
transcription is not a citation.

---

## Done, 2026-08-22 — the boards re-worded, and the upgrade path written down

**THE OWNER'S RULING THAT LET THIS PROCEED, verbatim, 2026-08-21:**

> *"I will give you all those data sources later in a more comprehensive form proceed where
> you can and label reconstruction or inferred with a note as you like"*

That is the authority for the tiering below and it is recorded here rather than in a run's
transcript, because the transcript does not survive and the upgrade path has to.

### What shipped

The structure record's `name` and the board's wording are now **separate fields** and are allowed
to differ. All **33 boards** are re-lettered from `SIGN_WORDING` in
`tools/generate_business_signboards.py`, in the advertisements' own register — proprietor or firm
first and largest, the trade beneath, the place last and smallest — carried per line with a role
(`sign_lines`) and lettered in that hierarchy by `renderers/web/js/signage.js`.

* **14 `inferred`** — the firm's own advertised line: Bates, Carpenter (both shops), the *Chicago
  Democrat*, Elston, Goss & Cobb, Jones, Harmon Loomis & Co., Brewster Hogan & Co., J. H. Kinzie,
  Mason, Newberry & Dole's warehouse, Peck, John Davis's Steam-Boat Hotel.
* **19 `reconstructed`** — no surviving advertisement; built from the trade vocabulary the same
  pages evidence (druggist, forwarding & commission merchant, public house, blacksmithing,
  slaughtering & packing, brick maker, tannery, boarding house, dry goods & groceries).
* **0 `attested`, deliberately.** The seven pages are images supplied in conversation and are not
  in `data/sources/assets/`; a transcription is not a citation. Every `inferred` note quotes its
  advertisement, names its date, says the transcription came from owner-supplied images on
  2026-08-21, and says the value is to be **upgraded to `attested`** when the pages are committed.

### The upgrade path, for whoever has the pages

1. Commit the seven page images to `data/sources/assets/<source_id>/` with a source record, in the
   shape of `data/sources/chicago_democrat_1833_11_26.json`.
2. Add that id to the `sources` list of each `SIGN_WORDING` entry it covers and change that
   entry's `grade` from `"inferred"` to `"attested"` — and add `"attested"` to `WORDING_GRADES`,
   which currently refuses it on purpose.
3. Trim the `PENDING` sentence from those entries' `why`.
4. Re-run the generator; `tools/check.sh` re-derives the record byte for byte.

**Goss & Cobb's is already citable** — its page is committed at
`data/sources/assets/chicago_democrat_1833_11_26/` — and what still keeps it `inferred` is that an
advertisement heading is not a description of a signboard. That is a judgement, not a gap, and it
is the one to revisit first.

### Identities corrected, and findings raised rather than buried

`hogan_store` now reads **BREWSTER, HOGAN & CO. / Forwarding & Commission**, which its own record
already knew (its `aka` carries "Brewster, Hogan & Co.'s store"). The record's `findings` array
carries six things the pages say and the model does not yet answer — J. S. C. Hogan's separate
South Water store, Pierce & Abbott, P. Pryne & Co. against Pruyne & Kimball, three advertisements
that locate themselves by a neighbour, a list of firms the town should plausibly have and the
model lacks, and the out-of-town houses that must never be hung here.

### The golden mortar

Carpenter's 1835 advertisement heads itself *"AT THE SIGN OF THE GOLDEN MORTAR"*, so the device is
**painted on his South Water board** — canvas, zero triangles — graded `inferred` with the
wordings and upgradeable with them. It is on that frontage and not on his older Lake Street shop
because the advertisement that names it also names South Water Street. **L25 is untouched**: it
withholds an image nobody described, which is the opposite case. The smoke pins the device count
at exactly one so it cannot spread to a trade whose advertisement names none.

### The check

T-0066's string-equality assertion is **corrected, not relaxed**. The board and the card must now
agree about **who** — `sign_identity`, which has to appear in both — asserted at the Tremont's own
board, over every sign in the town, and beside two new absolute assertions: no board carries the
word "log", and every board letters a trade as well as a proprietor. The generator refuses to
build if any of them fails.

**Liberty:** L166. **PR:** see the front matter.
