# The school-section sale of October 1833 — what it can check, and what it cannot

**Ruled:** 2026-09-14 · **Ticket:** T-1017 · **Domain:** `land_sales` ·
**Tool:** `tools/school_section_sale.py` · **Measurement:**
`data/research/land_sales/school_section_sale_1833.json` · **Ruling:**
`data/research/land_sales/resident_rulings.json` → `questions_ruled` → `T-1017`

Re-derivable end to end:

```
python3 tools/school_section_sale.py --build       # re-measure and write
python3 tools/school_section_sale.py --check       # re-measure, diff, assert the invariants
python3 tools/school_section_sale.py --self-test   # the assertions, broken on purpose
```

---

## 1. The question, and who asked it

`resident_rulings.json` upholds a proposal only where the town's own record of the person
carries something the register's row can be **checked against** beyond a bare name: a middle
initial the register repeats, a trade the purchase is consistent with, a second document that
says something, or the register's own Residence column. Four arms, and no fifth.

On 11 September 2026, adjudicating cohort C3, T-0990 refused two proposals and wrote the same
sentence into both. RUSSELL SAMUEL took three whole blocks for $1,205 against a card that is one
line of the 1833 tax roll; SKINNER JOSEPH took lots 1 and 8 of block 117 against a card that is
that tax roll and one return of uncalled-for letters. Both refusals record an argument that
would have gone the other way and is none of the four arms:

> the rows are lots 1 and 8 of block 117 at the town's OWN school-section sale of 22 October
> 1833, and a man on the town's tax list of that same year is the kind of man who bought there.
> That argument is not one of the rule's four arms and it would, if admitted, reopen rulings
> already made — so it is FILED as a question rather than used here.

That filing is T-1017. It was right to file it: fifty rulings across four tickets name this sale,
and deciding it in the middle of a cohort would have decided them by momentum.

## 2. What the sale actually is

The register names it itself. `type_of_sale` carries three codes across the 1,572 committed
entries — `FD` federal, `CN` canal, `SC` school — and `SC` and section 16 of T39N R14E are the
**same 337 rows**, which is the first thing `--self-test` proves. No date range and no section had
to be guessed at.

| | |
|---|---|
| rows | **337** |
| days | **four** — 22, 23, 24 and 25 October 1833 |
| purchaser spellings | **105** |
| total | **$39,844.85** |
| sold as town lots, no acreage stated | 252 rows |
| sold as whole blocks, acreage stated | 85 rows — 302.18 acres for $15,559.10 |
| volumes and pages | 817/027–029, 818/008–010 |

**Nothing here is new about the sale itself.** T-0798 already read it as four days and 105
purchasers when it spent the 337 rows onto Wright's block polygons, and § *The school section,
spent* of this domain's README says so. What is new is that the reading is now derived by a tool
the gate runs, from the register's own code rather than from a date range, so the figures a ruling
quotes cannot drift from the register that carries them. One phrase is worth noting in passing:
RUSSELL SAMUEL's ruling calls it "the school-section sale of 23 and 24 October 1833", which is
true of *his three rows* and not of the sale — SKINNER JOSEPH's ruling, on the same day, dates his
own two lots to the 22nd.

## 3. What argues for admitting it, measured rather than asserted

It is real, and it is the reason the question was worth asking. Set the sale's 105 buyers beside
the 542 purchaser spellings that appear only elsewhere in the register:

| | at the school section | everywhere else |
|---|---|---|
| purchaser spellings | 105 | 542 |
| carrying an **upheld** match to a town card | **50 — 47.6%** | 85 — **15.7%** |
| carrying a surname the residents layer holds **nobody** of | **13 — 12.4%** | 210 — **38.7%** |

Three times the density of town-side names, and a third of the density of strangers. The second
row uses **no adjudication at all** — it asks only whether the layer holds the surname — so it
cannot be an echo of rulings already made. The town's own men did buy at the town's own sale.

## 4. Why it is still not a check

### One — it is not exclusive

Thirteen of the 105 buyers carry a surname this layer holds nobody of: BROSON ARTHUR,
HUQUEUIN HIRAM, BARCKENBILE CHRISTIA, JAMIESON STLOUIS T, VANDERBURG WILLIAM H, BARNES HAMILTON,
BIAS GARRET, BIAS GARRETT, CAMPEAU DANIEL J, STOSE CLEMENTS, SWIGLEY JOHN, WEED EDMUND and
WORTHINGHAM WILLIAM.

And the ground went at auction prices. The 85 rows that state an acreage fetched **$51.49 an
acre**; the 592 federal rows in the same register fetched **$1.45**. A sale at thirty-six times
the government minimum is one capital could reach from anywhere — not a roll of the men who lived
here.

### Two — it cannot carry a name on its own

Fifty of the 105 buyer spellings hold an upheld match. **Fifty-five do not.** A criterion that is
wrong more often than it is right cannot be the thing a row is checked against. 47.6 per cent is a
prior over a population; the rule is applied to one proposal at a time.

### Three — it cannot separate two bearers of a name, and that is the whole work a check does

This is the arm that decides it. Attendance at the sale is a property of the **row**, and it is
identical for every buyer at it. A middle initial, a trade, a street, the Residence column — each
is a property of the **name**, and that is precisely why each can tell one claimant from another.

The sale's own pages prove it has no such power. **Twenty surnames are printed at this sale under
more than one spelling:**

| | |
|---|---|
| HALE | EBENEZER and JOHN — entering the *same* twenty-six parcels, the duplicate pair T-0885 filed and left open |
| HARMON | CHARLES L, ISAAC, ISAAC D |
| JONES | BENJAMIN, WILLARD, WILLIAM |
| PRUYNE | P, P AND CO, PETER |
| BLANCHARD | F G, F G AS, GURTREY |
| WRIGHT | JOHN, T G |
| KIMBERLEY / KIMBERLY | EDMUND S, IRA, J E, S A |
| and thirteen more | BIAS, BOND, COOK, DOLE, FOOT, GOODRICH, HADDOCK, MORRISON, NEWBERRY, NOBLE, VANDERBOGERT, WILLIAMS |

This is T-0990's WENTWORTH reasoning turned on the sale rather than on the register as a whole:
*a source that sells to two men of a surname has told you there are two.* Admitting the sale as a
check would lift SKINNER JOSEPH and RUSSELL SAMUEL — and it would lift, by exactly the same
amount, the 41 buyers refused against a rival and the 13 whose surname the town has never held. A
criterion that cannot tell those apart is not a check.

## 5. What the ruling changes

**Nothing retracts.** That is the answer T-0990 feared and the one it got.

Fifty rulings across T-0850, T-0990, T-0993 and T-1034 name the sale — **39 upholds, 10 refusals
and one `named`** — and not one of them rests on it. In the upholds it stands beside a middle
initial, an office or a trade: Thomas J V Owen, the town's first president, and George W Snow, its
Assessor and Surveyor, are upheld on what they were, with the sale saying only that the purchase
fits the man. In the refusals it is the argument being declined — HALE JOHN, KINGSTON PAUL,
GOODRICH CHAUNCEY, CHANDLER JOSEPH, MORRISON THOS M, STANLEY JOSEPH, VANDERBOGERT HENRY,
WESSENCRAFT CHARLES, and the two that asked the question. All ten stand.

What is added is a **measured prior, expressly not a fifth arm.** The enrichment in § 3 may be
quoted in a ruling as context — it already is — and it may never decide one.

## 6. The ruling is gated, so it can be wrong out loud

The three figures § 4 turns on are **asserted** in `check.sh`, not merely printed:

1. some buyer at the sale carries a surname the layer holds nobody of — it is not a townsmen-only
   roll;
2. upheld matches are a minority of its buyers — the criterion is wrong more often than right;
3. the sale prints some surname more than once — it cannot separate two bearers of a name.

The residents layer grows every week and the crosswalk is re-derived from it, so all three of
these can move. If any one of them flips, the build goes **red** and names which arm failed, and
T-1017 reopens — rather than a ruling quietly standing on a measurement that has moved underneath
it. `--self-test` breaks each of the three on purpose and requires the failure.

## 7. What was not done

- **No card moved, no grade moved, no row moved.** This is a ruling about a kind of argument, and
  the four rulings it was asked about keep the verdicts they already had.
- **The sale's buyers were not identified.** Whether HALE EBENEZER and HALE JOHN are one hand or
  two is T-0885's question and is still open; nothing here decides it.
- **The prior was not turned into a tiebreak.** It would be easy to write "admissible where the
  other four arms already nearly hold", and that is a fifth arm wearing a hedge. If a later ticket
  wants one, it is the owner's to rank.
