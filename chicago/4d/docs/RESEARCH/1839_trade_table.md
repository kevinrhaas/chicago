# The 1839 directory's trade table

*T-1346, piece 1 of T-1173. Built by `tools/build_trade_table_1839.py --build`; the
table itself is `data/research/directories/fergus_1839_trade_table.json` and
`tools/check.sh` re-derives it on every run.*

## Why it exists

The resident reconstruction programme (T-1167) has to draw a reconstructed head's
TRADE, and the file it meant to draw from was never built. T-1162 — "the 1835
occupation model" — was **withdrawn**: its five figures were folded into
`data/reconstruction/1835_town_model.json`, and what the fold kept was the
establishment comparison (how many stores, taverns, printing offices the December
1835 State census counted against the register) and the seven industry columns of
the 1840 schedule. What it lost is the thing T-1162 § 2 asked for first: *the 1839
share per trade, count over all 1839 entries with a trade.*

The consequence is visible in the order book. `1835_reconstruction_order_book.json`
buckets a person as `trade` or `none` — 307 adults in family households at a trade —
and says nothing whatever about WHICH trade. T-1347 cannot draw one without
inventing the distribution it draws from, and inventing a distribution is the move
this project exists not to make. This table is that distribution, out of committed
text and nothing else.

## What it is not

1839 is four years after the scene. Worse, this volume is Fergus's **1876
completion** of a list that, in the compiler's own words on printed page 3, "was
never written" — the names of the business men of the City, recalled decades later
by the Old Settlers he names on page 4. `tools/read_fergus_1839.py` carries both of
the compiler's warnings in its header and every claim it writes is stamped
`describes_date: "1839"`.

So a share here is the shape of a LATER town recalled later still. It is a **prior
for a draw**. It is not a count of 1835, it is not evidence about any person, and
nothing in it may be written onto a card.

## What it reads, and how

The input is `claims/fergus_1839_directory_entries.json` — 1,655 entries the
segmenter takes off the committed page text, 1,583 of them
carrying something in the printed trade slot. No page is opened here; this is an
aggregate over a reading that already exists and that the gate already re-derives.

The slot is cut at the first comma. This volume routinely prints the employer
there too — *"Boyer, Charles, clerk, on the canal"*, *"Breese, Robert, clerk, James
Hervey"* — and the trade is what stands before it; the rest names somebody else's
house.

The normalisation is an ordered list of committed rules, and **the first rule that
matches decides**:

1. **OCR repairs**, by name. This scan turns `r` into `i'` inside a word often
   enough that five common trades arrive broken — `laboi'er`, `cai'penter`,
   `clei'k`, `bakei'`, `tailoi`. A general rule for that would also rewrite words
   that are correctly set, so each repair is written out and a sixth broken word
   arrives as a refusal rather than as a silent miscount.
2. **What cannot be a trade at all**: an illegible fragment, a firm's trading style
   (`Briggs & Humphrey`), and a **proper-named house**. That last one earns its
   length. *"Smith, John, American Hotel"* says where the man was, not what he did
   there, and reading it as tavern-keeping would promote every porter and boarder
   in the volume to a landlord. But a BARE house-word — `boarding-house`, `saloon`,
   `grocery` — is the trade itself. The rule therefore fires only on a house
   carrying a proper name, and steps aside wherever the phrase also carries a trade
   or a post, which is why `private boarding house` and `pastor first presbyterian
   church` are read and `Lake House` is not.
3. **The trade patterns**, most specific first, so `ship chandler` is never a
   chandler-of-nothing and the barber's *shaving saloon* is never a tavern.
4. **Then, and only then**, the classes that would otherwise swallow a real trade:
   an employer or a name the segmenter kept, and an address.

A compound — *carpenter and builder*, *grocer and liquor dealer* — is counted once,
under whichever of its trades the ordered rules reach first. The volume prints no
second slot and this table invents none.

**Nothing is dropped.** `mapped + refused == entries carrying a printed trade`, and
the self-test asserts it. Every refusal carries its class, its reason and every form
it caught, because the honest measure of a reading like this one is how much of the
volume it could NOT read.

## The table

1,377 of 1,583 entries (87.0%) map onto
88 trades.

| trade | entries | share of mapped | 1840 column |
|---|---:|---:|---|
| clerk | 152 | 0.110 | Commerce |
| carpenter | 133 | 0.097 | Manufactures and trades |
| labourer | 73 | 0.053 | Manufactures and trades |
| grocer | 65 | 0.047 | Commerce |
| builder | 54 | 0.039 | Manufactures and trades |
| blacksmith | 48 | 0.035 | Manufactures and trades |
| attorney | 45 | 0.033 | Learned professions and engineers |
| dry goods merchant | 45 | 0.033 | Commerce |
| tailor | 42 | 0.030 | Manufactures and trades |
| merchant | 41 | 0.030 | Commerce |
| teamster | 41 | 0.030 | Navigation of canals, lakes and rivers |
| drayman † | 30 | 0.022 | Navigation of canals, lakes and rivers |
| shoemaker | 27 | 0.020 | Manufactures and trades |
| farmer | 26 | 0.019 | Agriculture |
| gardener † | 26 | 0.019 | Agriculture |
| boarding house keeper | 25 | 0.018 | Commerce |
| land agent | 25 | 0.018 | Commerce |
| tavern keeper | 23 | 0.017 | Commerce |
| boatman | 19 | 0.014 | Navigation of canals, lakes and rivers |
| cabinet maker † | 18 | 0.013 | Manufactures and trades |
| butcher | 16 | 0.012 | Manufactures and trades |
| carriage maker | 15 | 0.011 | Manufactures and trades |
| forwarding and commission | 15 | 0.011 | Commerce |
| printer | 15 | 0.011 | Manufactures and trades |
| sheriff | 15 | 0.011 | Learned professions and engineers |
| painter | 14 | 0.010 | Manufactures and trades |
| druggist | 13 | 0.009 | Commerce |
| schoolteacher | 13 | 0.009 | Learned professions and engineers |
| surveyor | 13 | 0.009 | Learned professions and engineers |
| banker † | 12 | 0.009 | Commerce |
| founder | 12 | 0.009 | Manufactures and trades |
| mason | 12 | 0.009 | Manufactures and trades |
| town officer † | 12 | 0.009 | Learned professions and engineers |
| baker | 11 | 0.008 | Manufactures and trades |
| livery stable keeper | 11 | 0.008 | Commerce |
| lumber merchant | 11 | 0.008 | Commerce |
| music teacher | 11 | 0.008 | Manufactures and trades |
| student † | 11 | 0.008 | Learned professions and engineers |
| cooper | 10 | 0.007 | Manufactures and trades |
| auctioneer | 9 | 0.007 | Commerce |
| master mariner | 8 | 0.006 | Navigation of the ocean |
| soap and candle maker | 8 | 0.006 | Manufactures and trades |
| tinsmith | 8 | 0.006 | Manufactures and trades |
| miller | 7 | 0.005 | Manufactures and trades |
| watchmaker | 7 | 0.005 | Manufactures and trades |
| barber surgeon | 6 | 0.004 | Manufactures and trades |
| harness maker | 6 | 0.004 | Manufactures and trades |
| milliner | 6 | 0.004 | Manufactures and trades |
| plasterer | 6 | 0.004 | Manufactures and trades |
| sawyer | 6 | 0.004 | Manufactures and trades |
| seaman | 6 | 0.004 | Navigation of the ocean |
| confectioner | 5 | 0.004 | Manufactures and trades |
| domestic | 5 | 0.004 | Manufactures and trades |
| hardware merchant | 5 | 0.004 | Commerce |
| hatter | 5 | 0.004 | Manufactures and trades |
| physician | 5 | 0.004 | Learned professions and engineers |
| speculator | 5 | 0.004 | Commerce |
| brickmaker | 4 | 0.003 | Manufactures and trades |
| bookseller | 3 | 0.002 | Commerce |
| brewer | 3 | 0.002 | Manufactures and trades |
| foreman † | 3 | 0.002 | Manufactures and trades |
| justice of the peace | 3 | 0.002 | Learned professions and engineers |
| liquor dealer | 3 | 0.002 | Manufactures and trades |
| mail contractor | 3 | 0.002 | Navigation of canals, lakes and rivers |
| soldier | 3 | 0.002 | Learned professions and engineers |
| tanner | 3 | 0.002 | Manufactures and trades |
| bar keeper † | 2 | 0.001 | Commerce |
| county clerk | 2 | 0.001 | Learned professions and engineers |
| dentist | 2 | 0.001 | Learned professions and engineers |
| drover | 2 | 0.001 | Agriculture |
| editor | 2 | 0.001 | Learned professions and engineers |
| engraver † | 2 | 0.001 | Manufactures and trades |
| fire warden | 2 | 0.001 | Learned professions and engineers |
| harbour agent | 2 | 0.001 | Navigation of canals, lakes and rivers |
| minister | 2 | 0.001 | Learned professions and engineers |
| postmaster | 2 | 0.001 | Learned professions and engineers |
| refectory keeper | 2 | 0.001 | Commerce |
| ship chandler | 2 | 0.001 | Commerce |
| steward † | 2 | 0.001 | Manufactures and trades |
| warehouseman † | 2 | 0.001 | Commerce |
| ferryman | 1 | 0.001 | Navigation of canals, lakes and rivers |
| gunsmith | 1 | 0.001 | Manufactures and trades |
| laundress | 1 | 0.001 | Manufactures and trades |
| lighthouse keeper | 1 | 0.001 | Navigation of canals, lakes and rivers |
| millwright † | 1 | 0.001 | Manufactures and trades |
| packer | 1 | 0.001 | Manufactures and trades |
| sexton † | 1 | 0.001 | Manufactures and trades |
| town clerk | 1 | 0.001 | Learned professions and engineers |

† — a trade the 1839 volume prints and `data/residents/index.json`'s
`vocabulary.occupations` has no word for: `banker`, `bar_keeper`, `cabinet_maker`, `drayman`, `engraver`, `foreman`, `gardener`, `millwright`, `sexton`, `steward`, `student`, `town_officer`, `warehouseman`.
They are counted here because a share that quietly drops a town's draymen is wrong
about its carpenters too. **T-1347 must extend the vocabulary before it may write
one of these people**, and that extension is the first thing it owes.

## Against the 1840 industry columns

The 1840 federal schedule returns persons in families by industry; this table
returns directory entries by trade. **The two are not the same unit**, and the
deltas below are read as shape and not as error.

| column | 1839 entries | 1839 share | 1840 persons | 1840 share | delta |
|---|---:|---:|---:|---:|---:|
| Agriculture | 54 | 0.039 | 136 | 0.1563 | -0.117 |
| Commerce | 468 | 0.340 | 185 | 0.2126 | +0.127 |
| Manufactures and trades | 611 | 0.444 | 405 | 0.4655 | -0.022 |
| Navigation of the ocean | 14 | 0.010 | 9 | 0.0103 | -0.000 |
| Navigation of canals, lakes and rivers | 97 | 0.070 | 62 | 0.0713 | -0.001 |
| Learned professions and engineers | 133 | 0.097 | 71 | 0.0816 | +0.015 |
| Mining | 0 | 0.000 | 2 | 0.0023 | -0.002 |

Three of the seven agree closely enough to be worth saying out loud. Manufactures
and trades — the mechanics, the largest block in both — reads 0.444 here against
0.466 there. Navigation of canals, lakes and rivers reads 0.070 against 0.071.
Navigation of the ocean reads 0.010 against 0.010. Two independent documents, one a
recalled directory of a city and the other a federal schedule of a county, put the
same shares of working people in the same three columns.

The two that disagree disagree for reasons that are about the documents and not
about the town. **Agriculture** is 0.039 here against 0.156 there: the 1840 schedule
covers a county of farms and this directory covers a city of streets, and the
farmers are outside it. **Commerce** is 0.340 against 0.213: a subscription
directory is a list of the men who wanted to be found by customers, so clerks,
merchants and agents are over-listed in it by construction — which is the single
most important caveat on any use of the table above, and the reason T-1347 must
renormalise within the trades it is actually drawing for rather than take these
shares whole.

## The refusals

| class | entries | why |
|---|---:|---|
| `a_firm_style` | 64 | a firm's trading style, not one person's trade — the entry names a house |
| `no_rule_reaches_it` | 61 | the trade slot carries words no committed rule places — a forename the segmenter kept, a works, a vessel or a trade this volume prints once. Counted, printed, and left for a reader rather than guessed at |
| `not_legible` | 28 | fewer than three letters survive the scan — a speck, a rule or a broken line |
| `an_employer_or_a_name` | 25 | the segmenter carried a name, an initial or an employer into the trade slot; the volume gives this person no trade of their own |
| `a_house_not_a_trade` | 21 | a named house, church or place of business standing where a trade would be set — it says where the person was, not what they did there |
| `an_address` | 7 | an address or a ward printed where a trade would be, the entry giving no trade at all |

`no_rule_reaches_it` is the class worth reading. It holds forenames the segmenter
kept whole (`smead`, `davis`, `ira`), a works and a vessel or two, and a short tail
of trades this volume prints exactly once — a phrenologist, a chess player, a
gamboleer, a match maker, a block and pump maker. Two entries read `indian chief`,
which is an office set where a place belongs and is left refused deliberately.
Guessing at any of them would buy a tenth of a percent of coverage at the price of
the only thing that makes the other 87% usable.
