# A death notice is not a presence — which evidence class may stand on which leg

**T-1131.** `hh_wolcott_alexander` read `present_on_scene_date: present` for 1 July 1835.
The bracket that put it there had two legs: a Fergus 1843 directory entry on the far side
of the day, and on the near side the man's own death notice —

> Wolcott, Dr. Alexander, Indian agent, died Oct. 25, 1830, aged 40; his will was the
> first probated in Cook County.
> — `fdn0742`, `fergus_1843_old_settler_death_notices`

Andreas has the house on the north bank *"left unoccupied by the death of Dr. Wolcott"*
(`docs/RESEARCH/cobweb_castle.md`). A death at a place is not a presence at it, and this
death is five years before the day the scene models.

T-1117 found this card and could not reach it: that ruling was about the 1833 tax list,
and this card's at-or-before leg is not the tax list. It named the second defect and left
it open. This is that ticket, and the ruling is deliberately not about the card.

## It is a class question, and the class already answered it

`data/research/old_settlers/death_notices.json` has carried `places_in_1835: false` on
every one of its 757 records since the obituary was read, with the reason beside it —
the OBITUARY's own header:

> Names, places, dates, and ages at death of some of Chicago's Old Settlers, prior to
> 1843, and other well-known citizens who **arrived after 1843**, together with others
> prominently connected with Illinois history

Presence in that list is therefore evidence of neither residence in 1835 nor arrival
before 1843. The field was already true, already committed and already quoted in the
repository's own prose. **Nothing read it.** The refusal existed in the corpus and in no
derivation, which is why a dead man could bracket the day.

So the rule is reached from the field and not from the card: a class whose domain declares
`places_in_1835: false`, on every record it publishes, may not be an at-or-before leg of
the presence bracket. `tools/mint_civic_residents.py`'s `not_in_1835_classes()` reads the
domain every run. Unanimity is the bar — a file that stops saying it, or says it of some
rows and not others, drops the class out of the refusal and `--self-test` goes red on the
class it expects to find, so the ticket reopens rather than the rule being re-argued.

## Which leg, and why the refusal is asymmetric

Three answers, not two, because the two refusals this pass now carries are different
shapes:

| class | at-or-before leg | after leg | why |
|---|---|---|---|
| `tax_1833` | no | no | **T-1117.** A property roll names the owner of ground inside the town — resident, absent or three years dead. It places no person anywhere, at any date. |
| `death_notice` | **no** | **yes** | **T-1131.** The list declares it does not place its people in 1835, which is exactly what an at-or-before leg claims. The after leg claims something else — that the person was at Chicago on a **later** day — and the record does say that on its own face. |
| everything else | yes | yes | |

The asymmetry is the field's own wording and not a convenience. A man who died at Chicago
in 1885 **was** at Chicago in 1885; refusing that closes a bracket nobody asked to close.
It was measured before it was written: **7 cards** in the committed tree carry a death
notice as their ONLY at-or-after leg, and a blanket refusal would have withdrawn all
seven along with the one card that deserved it.

## What it moved, counted before it was written

Measured on `dev` at `8bd9bbc47`, over all 1,342 committed households:

| | |
|---|---|
| cards carrying a death-notice row at all | 26 |
| death-notice rows landing on the **at-or-before** leg | **1** |
| death-notice rows landing on the **at-or-after** leg | 22 (21 cards) |
| cards the refusal moves | **1** — `hh_wolcott_alexander` |
| cards a *symmetric* refusal would also have moved, wrongly | 7 |

`mint_civic_residents.py --gate` names the one card before the derivation is changed, and
`--check` re-derives all 414 civic cards byte for byte after it. No card was hand-edited.

## `absent`, and not `uncertain` — the one card where that is honest

Everywhere else this pass withdraws to `uncertain`, and T-1117 was explicit about why: a
man taxed for ground in the town may perfectly well have been standing on it, and a
silence is somewhere the sources have not looked. **A death is not a silence.** The record
says the man stopped and it dates the stopping before the day. `uncertain` would be the
flattering reading; `absent` is the true one, and it has a precedent in the tree —
`hh_porthier_joseph`, `attested`, withdrawn by a dated departure for Milwaukee (T-0478).

The reading is narrow and says no three ways, in `death_before_the_day()`:

- it reads **only** the death class. Another class may join the `places_in_1835` refusal
  without its date being a death, and the answer stays `uncertain` for it;
- it wants **one** death. Two notices that disagree on the year are an identity question,
  not a death;
- it defers to any record that places the person at Chicago **after** the death and at or
  before the scene date. A tax roll is not one of those records, which is the whole of
  T-1117 — and it is why this card reaches `absent` at all.

## What was NOT done

- **The arrival bound is untouched, and deliberately.** `arrival` stays `not_later_than
  1830-12-31`: a man who died at Chicago in 1830 was at Chicago by 1830 to die there, and
  that is all the bound ever asserted. The claim this ticket refuses is about the day, and
  it lives in `present_on_scene_date` alone.
- **The card's 1843 directory leg is probably a second Alexander Wolcott** — it reads
  *"Wolcott, Alex., surveyor, bds H. Wolcott [died Aug. 11, 1884, a. 69]"*, which is a man
  born about 1815. The card already carries that contradiction in its own note and files
  it for the identity master under `os_q_registered_after_a_documented_death`. Splitting a
  person is the consolidation's ruling to make, not a mint's, and nothing here presumes it.
- **`bound_of` still reads a bare year at the year's END on both legs**, which is right
  for a bound and wrong for the far leg of a bracket. One card is affected today —
  `hh_vanderbogart_henry`, whose after leg is a death on 8 April 1835, three months BEFORE
  the scene date, read as 31 December 1835. Filed as its own ticket; it is a date-reading
  defect and not a class one, and fixing it inside this ruling would have hidden it.

## How this stays true

`mint_civic_residents.py --self-test` fires the whole rule at fixtures: that the domain
still declares the refusal, that a death before the day reads `absent`, that the after leg
is **not** swallowed, that a contradicting record leaves `uncertain`, that two disagreeing
deaths are not read as one, that the arrival bound does not move, and that `--gate` refuses
a card forced back to `present`. `--gate` asks the committed tree the same question on
every card. `tools/assert_tax_roll_ruling.py`, already in `check.sh`, holds the reading
underneath both rulings: `fdn0742` dates the death 1830-10-25 and records
`places_in_1835: false`.
