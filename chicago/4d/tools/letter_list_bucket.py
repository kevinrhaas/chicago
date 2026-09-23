#!/usr/bin/env python3
"""An initial on a letter-list card stands for a BUCKET, not a person (T-1038).

`tools/mint_letter_list_residents.py` seats ONE household per surname — its
refusal 8, `surname already minted` — so where the post office's returns printed
two names under one surname, the town holds one card and the other name is
refused. A refused name is not a person the corpus decided against; it is a
second reading of that surname the pass had no room for.

That collapse defeats T-0670. The forename rule refuses a directory entry when
BOTH readings print a full forename and the two disagree, and it leaves an
initial standing against a full name alone. A letter-list card that prints only
an initial therefore takes the entry — and the reading it was seated over, which
prints a full forename, would have refused the same entry. Whether the entry is
carried or refused is then decided by which reading the mint pass RANKED FIRST,
and the ranking is not evidence about anybody.

The case this was written for. `hh_sherwood_s` is `S. Sherwood`, minted from the
return of 1 July 1834. The same returns print `Stephen Sherwood` (1 January
1834), refused as `surname already minted`. Fergus 1839 and Norris 1844 both
print `Sherwood, Smith J., watchmaker and jeweller, 144 Lake st`, and the
corpus holds that jeweler under his own identities — `id_sherwood_s_j`,
`id_sherwood_smith_jones` (`Sherwood, Smith Jones` in Fergus 1843). Against the
card's `S.` the entry is a match and a trade and a street reached a person the
letter list gave a name and nothing else. Against `Stephen` it is Stephen
against Smith: two full forenames that disagree, and T-0670 refuses it.
`fergus_1839_crosswalk_1835.json` already showed the contest in its own
letter-list pool, where the single entry `f1839_e1338` matches BOTH `S.
Sherwood` and `Stephen Sherwood`; only the residents pool could not see it,
because only one of the two was ever minted.

  THE RULE. A person of the 1835 layer is a CONTESTED LETTER-LIST BUCKET when
  all three hold:
    1. their card carries `letter_list_only` — the post office's returns are the
       whole of the evidence that seated them;
    2. their card's own forename is an INITIAL, not a full name;
    3. the letter-list pool holds at least one OTHER name that folds to the same
       surname, begins with the same initial, and prints a FULL forename.
  A later directory entry is not matched to such a card. The refusal is FILED,
  never dropped: the crosswalks report the card, the entry as printed, and the
  rival readings, so the reading can be argued with.

  IT REFUSES THE WHOLE CARD, not the entry it can weigh. The alternative — refuse
  only where the rival's full forename disagrees with the printed one — lets the
  same man back in through a volume that prints him by initial: Norris's
  alphabetical `Sherwood, Smith J. … (See card)` would be refused and his own
  advertising card `S. J. Sherwood`, the same jeweler at the same 144 Lake
  street, would carry the trade and the address anyway. A card that cannot be
  identified with any one of the readings that made it has not been met by any
  later directory.

  IT IS NOT A RULING THAT THEY ARE TWO PEOPLE. The corpus does not say `S.
  Sherwood` and `Stephen Sherwood` are two men, and does not say they are one;
  `identity_master.json` folds them on the same surname-plus-initial rule this
  module distrusts. What is refused is the SPEND, because it rests on a
  ranking. A source that names the letter-list person in full retires this
  refusal at once.

This module is the rule; the crosswalks import it rather than restate it.
Run it directly for its self-test: `python3 tools/letter_list_bucket.py --self-test`.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import name_agreement as na

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAZETTEER = os.path.join(ROOT, "data/research/newspapers/gazetteer.json")

RULE = (
    "The card is a CONTESTED LETTER-LIST BUCKET (T-1038): it prints an INITIAL, the "
    "post office's returns print another name under the same surname and the same "
    "initial IN FULL, and mint_letter_list_residents.py seats one household per "
    "surname — so the card stands for readings the corpus cannot separate, and at "
    "least one of them would refuse this entry under T-0670's forename rule. What is "
    "refused is the SPEND, not the identity: nothing here says the readings are two "
    "people. A source naming the letter-list person in full retires the refusal."
)


def split_name(name):
    """A pool name as (surname, given). 'W. H. Adams' and 'Adams, W. H.' both work."""
    name = (name or "").strip()
    if "," in name:
        surname, given = name.split(",", 1)
        return surname.strip(" ."), given.strip(" .")
    parts = [p for p in name.replace(".", ". ").split() if p]
    parts = [p for p in parts if p.strip(".,").lower() not in na.TITLES]
    if len(parts) < 2:
        return "", ""
    return parts[-1].strip(" ."), " ".join(parts[:-1])


def _key(name):
    surname, given = split_name(name)
    if not surname:
        return None
    return (na.fold(surname), na.initial(given))


def pool(path=GAZETTEER):
    """The letter-list names as the gazetteer prints them."""
    doc = json.load(open(path, encoding="utf-8"))
    return [p.get("name") for p in doc.get("persons") or []
            if p.get("letter_list_only") and p.get("name")]


def buckets(names):
    """surname+initial -> the FULL forenames the letter list prints under it."""
    out = {}
    for name in names:
        key = _key(name)
        if not key or not key[1]:
            continue
        _surname, given = split_name(name)
        if na.is_full_forename(given):
            out.setdefault(key, [])
            if name not in out[key]:
                out[key].append(name)
    return out


def rivals(card_name, letter_list_only, index):
    """The full-forename letter-list readings this card was seated over.

    Empty for any card the rule does not reach — not letter-list-only, no
    surname, or a card that prints a full forename of its own."""
    if not letter_list_only:
        return []
    key = _key(card_name)
    if not key or not key[1]:
        return []
    _surname, given = split_name(card_name)
    if na.is_full_forename(given):
        return []
    return [n for n in index.get(key, []) if n != card_name]


def refusal(card_name, letter_list_only, index):
    """The filed refusal for this card, or None where the rule does not reach."""
    seen = rivals(card_name, letter_list_only, index)
    if not seen:
        return None
    return {
        "outcome": "refused_letter_list_bucket",
        "card": card_name,
        "seated_over": seen,
        "rule": RULE,
    }


def _self_test():
    ll = ["S. Sherwood", "Stephen Sherwood", "Jeremiah Sherwood",
          "A. Lamb", "Adam Lamb", "Caleb Lamb", "P. Hall", "Wm. Ogden"]
    idx = buckets(ll)
    ok = True

    def check(label, got, want):
        nonlocal ok
        if got != want:
            ok = False
            print("FAIL %s: %r != %r" % (label, got, want))

    # The case the rule exists for: an initial seated over a full forename.
    check("sherwood is a bucket", rivals("S. Sherwood", True, idx), ["Stephen Sherwood"])
    check("lamb is a bucket", rivals("A. Lamb", True, idx), ["Adam Lamb"])
    check("the refusal is filed",
          (refusal("S. Sherwood", True, idx) or {}).get("outcome"),
          "refused_letter_list_bucket")

    # The three ways a card is NOT a bucket, each of which the rule must leave alone.
    check("a full forename is not a bucket", rivals("Stephen Sherwood", True, idx), [])
    check("a card the letter list did not seat is untouched",
          rivals("S. Sherwood", False, idx), [])
    check("an initial with no full-forename rival is untouched",
          rivals("P. Hall", True, idx), [])
    check("no refusal where the rule does not reach", refusal("P. Hall", True, idx), None)

    # A rival must agree on the INITIAL, not merely the surname: Jeremiah and Caleb
    # stand under the same surnames and must not make their cards buckets.
    check("a rival on the surname alone is not a rival",
          rivals("C. Sherwood", True, idx), [])

    # The comma form is a pool name too, and its surname is the FIRST token —
    # 'Baxter, Daniel' is a Baxter, and reading it as a Daniel invents a rival.
    idx2 = buckets(["Baxter, Daniel", "B. Clevinger [?] Daniel"])
    check("the comma form's surname is read first",
          rivals("B. Clevinger [?] Daniel", True, idx2), [])

    # A garbled card name still has to be answerable rather than crash.
    check("a name with no surname is untouched", rivals("Stephen", True, idx), [])
    check("an empty name is untouched", rivals("", True, idx), [])

    print("letter_list_bucket self-test: %s" % ("ok" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    idx = buckets(pool())
    print("%d surname+initial bucket(s) the letter list prints a full forename under"
          % len(idx))
