#!/usr/bin/env python3
"""T-1304: the sex and age no evidence can settle, drawn from the model and said so.

    python3 tools/reconstruct_sex_age.py --build       write the model, the cards, the ledger
    python3 tools/reconstruct_sex_age.py --check       everything re-derives; nothing drifted
    python3 tools/reconstruct_sex_age.py --report      bucket by bucket, what was drawn
    python3 tools/reconstruct_sex_age.py --self-test   the rules below, held over what it draws

This is stage `attribute_fill_sex_age` of the resident reconstruction programme
(data/reconstruction/1835_resident_reconstruction_programme.json, T-1167). It writes NO
person: it fills two RECONSTRUCTED attribute blocks on people the sources already name.
`tools/reconstruct_residents_1835.py --stage attribute_fill_sex_age --build` is the
programme's front door to it, and the programme's record contract is held here in full.

WHAT T-1303 LEFT. That pass read sex and age off the evidence and stopped where the
evidence stopped: 593 of 1,282 people carried no sex and 1,218 no birth year. Its
refusals were right and none of them is reversed here. What changes is that a refusal is
no longer an empty field — it is a DRAW from a measured distribution, marked
`reconstructed`, carrying the seed that reproduces it and the evidence that would retire
it. The three tiers of T-1168 are complete when this runs: recorded, read, drawn.

THE BUCKET IS THE ROLL, AND THE RATE IS MEASURED ON IT. The ticket asks that the 205
people known only as an initial off a letter list be sexed "at the measured adult-male
rate of a letter list, and the measurement stated rather than assumed". The measurement
is this layer's own: of the letter-list people whose forename IS spelled and whose sex
T-1303 settled, 351 of 372 are men — 94.4%. The same measurement is taken for every roll
the layer was minted from (civic, documented, placed, and the people no pass claims), and
a roll that settles fewer than MIN_SAMPLE names is not measured separately; it draws at
the pooled rate of all rolls, and the ledger says which rolls did that.

AND THE MEASUREMENT'S OWN BIAS IS STATED, because it runs one way. The forename table
T-1303 derived was built mostly on this layer's men, so a woman's forename is likelier
than a man's to be missing from it and to fall into the unsettled group that is being
drawn for. 94.4% is therefore a CEILING on the letter lists' male share rather than a
point reading of it, and every draw made from it leans male by an amount this pass cannot
bound. It is written into the ledger and into docs/LIBERTIES.md rather than smoothed.

THE ROLLS ARE NOT THE TOWN, and that gap is the whole reconstruction's brief. The town
model reads 120.9-150 males per 100 females (a 55-60% male town); these rolls read 94%
male. The difference is not a disagreement — a roll of correspondents, voters and
subscribers names adult men, and the town's women and children are named nowhere in it.
Nothing here is drawn at the town's ratio, because none of these people is a draw from
the town: they are people a roll already named. T-1174 writes the women and children the
pyramid lacks, and it is a different stage with a different quota.

AGE: A BAND, NEVER A YEAR. The only committed sex x age band distribution this project
holds is the 1840 Chicago schedule, read into data/research/census_1840/composition_1840
.json, whose `what_this_may_calibrate` admits exactly this use and whose
`what_this_may_not_do` forbids the other one: it may not name anybody or supply a person
to a household, and this pass does neither. A draw yields the band the schedule prints -
`20 under 30` - and the card carries that band. NO BIRTH YEAR IS WRITTEN. An exact year
drawn from a decadal band would read as a record of a birth, which is the precise
misrepresentation T-1303 refused six thin death-notice matches to avoid.

THE CONDITIONING IS THE MODEL'S, NOT A SOURCE'S, and T-1303 handed that finding here:
no age may be derived from an adult status until the rule is in a source record. It is
not, so the rule is not derived - it is DECLARED, as a liberty, and the card says so in
those words. Three conditionings, each naming what it assumes:

  * `civic_list_20_and_over` - the person stands on a poll, tax or muster list. Drawn
    from the bands 20 and over, the 1840 schedule's own adult line.
  * `named_on_a_roll_15_and_over` - the person is named in their own right on a roll of
    correspondents, litigants, subscribers or tradesmen. Drawn from 15 and over: the
    schedule counts a child as a tally inside a household and never as a correspondent,
    and 15 rather than 20 because an apprentice or a journeyman is on a trade roll.
  * `dependent_child_under_15` - the register calls the person an infant or a baptised
    child, or the household calls them a son, a daughter or a child AND the card names
    them nowhere in their own right. A kinship word is not an age (T-1179): a grown man
    in his father's house is still that household's son, so evidence of a roll, a press
    appearance or a trade of the person's own is read before the word is.

A COLLECTIVE DESCRIPTION IS STILL REFUSED. "The four Temple children" is a row about
four people and has no sex and no band of its own. Six such rows get an explicit
`unknown` block that says why, rather than a draw that would make a group into a person.
A group is a group WORD — rest, household, children, unnamed, four — and since T-1395 it
is not a leading article: "The Harmon daughter later known as Mrs A. G. Burley" is one
woman and was reading as a seventh group.

AND ONE ROW NAMES ONE PERSON AND STILL EARNS NO BAND (T-1395). Where a household seats
somebody as its child and the same record prints them in a married style — Mrs, Madam,
Widow — the kinship word and the style cannot both be read as an age, and neither is
dated to the scene: the style is a later source's, and `dependent_child_under_15` would
make a married woman a child under fifteen. No conditioning fits, so the band is refused
with that said, and the sex is left to whatever rule would have settled it anyway.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from profile_population_1835 import age_band_of  # noqa: E402
from spend_person_sex_age import ours_birth, read_name, tokens  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HOUSEHOLDS = ROOT / "data" / "residents" / "households"
COMPOSITION = ROOT / "data" / "research" / "census_1840" / "composition_1840.json"
TOWN_MODEL = ROOT / "data" / "reconstruction" / "1835_town_model.json"
MODEL = ROOT / "data" / "reconstruction" / "1835_sex_age_model.json"

SCENE_YEAR = 1835
RECONSTRUCTED = "reconstructed"

# A roll that settles fewer names than this is not measured on its own. 50 is the point
# below which one more woman moves the rate by more than two points, and a rate that
# moves that far on one card is a reading of that card rather than of the roll.
MIN_SAMPLE = 50

# The two seeds, in the programme's own form. The programme's `seed_rule` writes
# `<household_id>:<bucket>`; an ATTRIBUTE fill seeds by the PERSON, because two people
# share a household id and would otherwise draw the same sex and the same band.
SEED_SEX = "sex_ratio"
SEED_AGE = "age_bands_1840"

CHILD_RELATIONSHIPS = ("child", "son", "daughter")

# The styles a married life puts on a name. Read only against a kinship word, and only to
# REFUSE a band — never to draw one. See `married_style_over_a_kinship_word` below.
MARRIED_STYLES = ("mrs", "madam", "madame", "widow")

CONDITIONINGS = {
    "civic_list_20_and_over": {
        "low_edge": 20,
        "high_edge": None,
        "when": "the person stands on a poll, a tax list or a muster roll",
        "assumes": "that a poll, tax or muster list names a person 20 or over - the 1840 "
                   "schedule's own adult line. THE FRANCHISE'S AGE RULE IS NOT IN ANY "
                   "SOURCE RECORD THIS PROJECT HOLDS; this is the model's conditioning "
                   "and not a reading (T-1303's finding, handed to T-1304).",
        "liberty": "L-rc-age-conditioning",
    },
    "named_on_a_roll_15_and_over": {
        "low_edge": 15,
        "high_edge": None,
        "when": "the person is named in their own right on any other roll this layer was "
                "minted from - a letter list, a subscription, a court docket, a trade "
                "notice - or carries a role, a trade, a marriage or a parenthood",
        "assumes": "that a roll naming a person in their own right names somebody 15 or "
                   "over. The 1840 schedule counts a child as a tally inside a household "
                   "and never as a correspondent; 15 rather than 20 because an apprentice "
                   "or a journeyman stands on a trade roll. No source states this rule.",
        "liberty": "L-rc-age-conditioning",
    },
    "dependent_child_under_15": {
        "low_edge": 0,
        "high_edge": 15,
        "when": "the church register calls the person an infant or a baptised child, or "
                "the household record calls them a son, a daughter or a child",
        "assumes": "nothing beyond what the record already says: the band is drawn from "
                   "the schedule's child bands because the record calls them a child.",
        "liberty": "L-rc-age-conditioning",
    },
}


# --------------------------------------------------------------------------
# the draw
# --------------------------------------------------------------------------

def seed_for(person_id: str, bucket: str) -> str:
    """The seed a reader can retype. The programme's `seed_rule`, seeded by person."""
    return f"{person_id}:{bucket}"


def draw(seed: str) -> int:
    """The integer a seed draws. Deterministic across runs, machines and Pythons."""
    import hashlib
    return int.from_bytes(hashlib.blake2s(seed.encode("utf-8"), digest_size=8).digest(),
                          "big")


def unit(seed: str) -> float:
    """The draw as a number in [0, 1), to six places a reader can check by hand."""
    return (draw(seed) % 1_000_000) / 1_000_000


def pick(seed: str, weighted: list) -> dict:
    """The row a seed lands on. `weighted` is [(row, weight), ...]; weights need no sum."""
    total = sum(w for _, w in weighted)
    if total <= 0:
        raise SystemExit("a draw over an empty distribution is not a draw")
    at = unit(seed) * total
    running = 0.0
    for row, weight in weighted:
        running += weight
        if at < running:
            return row
    return weighted[-1][0]


# --------------------------------------------------------------------------
# the model, measured
# --------------------------------------------------------------------------

def band_label(band: str) -> tuple:
    """(printed label, low, high) for one 1840 band name."""
    tail = band.split("females", 1)[-1] if "females" in band else band.split("males", 1)[-1]
    tail = tail.strip()
    if tail.lower().startswith("under "):
        high = int(tail.split()[-1])
        return f"0-{high - 1}", 0, high - 1
    if "and upwards" in tail.lower():
        low = int(tail.split()[0])
        return f"{low}+", low, None
    low, high = int(tail.split()[0]), int(tail.split()[-1])
    return f"{low}-{high - 1}", low, high - 1


def age_bands() -> list:
    """The 1840 free-white bands, each with its printed label, edges, sex and persons."""
    rows = json.loads(COMPOSITION.read_text(encoding="utf-8"))["age_bands"]["free_white"]
    out = []
    for row in rows:
        label, low, high = band_label(row["band"])
        out.append({"band": label, "low": low, "high": high, "sex": row["sex"],
                    "census_band": row["band"], "persons": row["persons"]})
    return out


def cards() -> dict:
    return {path.stem: json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(HOUSEHOLDS.glob("hh_*.json"))}


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def ours_sex(block) -> bool:
    """A `sex_basis` this pass wrote. T-1303's are graded `inferred`; ours never are."""
    return isinstance(block, dict) and block.get("confidence") == RECONSTRUCTED


def ours_age(block) -> bool:
    """An `age_band` block. Nothing but this pass writes one, at any tier."""
    return isinstance(block, dict)


def counted_band_block(person: dict) -> dict:
    """The `age_band` of somebody a census column already counted, not drawn (T-1314)."""
    age = (person.get("reconstruction") or {}).get("age_on_scene_date") or {}
    low, high = age.get("low"), age.get("high")
    span = f"{low} or older" if high is None else f"{low}-{high}"
    stage = (person.get("reconstruction") or {}).get("stage")
    band = (person.get("reconstruction") or {}).get("band_1840")
    return {
        "value": span,
        "confidence": RECONSTRUCTED,
        "tier": RECONSTRUCTED,
        "note": (f"READ OFF A COUNT, NOT DRAWN. The `{stage}` stage wrote this person from a "
                 f"census column - \u201c{band}\u201d - and the band back-projects to {span} "
                 f"on the scene date. This pass draws an age only where nothing dates one, and "
                 f"a tally in an age column dates one."),
        "basis": {
            "kind": "rule",
            "id": "counted_by_a_census_column",
            "note": (f"ARGUED, NOT DRAWN. The `{stage}` stage wrote this person BECAUSE the "
                     f"1840 schedule tallies them in \u201c{band}\u201d; that column is the "
                     f"only thing said about their age, and five years off it is the whole "
                     f"derivation. No model row is consulted and nothing is drawn, so this "
                     f"block carries no seed."),
        },
        "replaceable_by": {
            "kind": "person",
            "match": ("a source that states this person's age, their birth year, or an "
                      "interval either can be read out of"),
        },
    }


# A STAGE THAT BRINGS ITS OWN SEX AND AGE IS NOT ONE THIS PASS FILLS (T-1171).
#
# This pass draws for a person the sources named and left undescribed. Stage
# `modelled_families` writes people no source names at all, and it writes them WITH a
# sex and an age band of its own - the wife drawn from the 1840 female adult columns and
# never above her husband's band, the child capped by the marriage his band allows. Both
# blocks carry `basis.id: age_bands_1840`, so without this exemption the ownership test
# below reads them as this pass's own and redraws them from the roll model, which throws
# the spacing rule away and replaces a documented draw with an undocumented one. The two
# stages are not disagreeing about a person: they are writing about different people.
SELF_DESCRIBING_STAGES = ("modelled_families", "women_and_children", "garrison")
# `women_and_children` (T-1174) is here for the same reason: it writes the whole card, and
# the sex and age of everybody on it are the draw the age pyramid was short of. Redrawing
# them from the roll model would throw away the bucket they were drawn against and replace
# a measured shortfall with an unmeasured one.
# `garrison` (T-1349) likewise, and it is the sharpest case of the three: a company of
# infantry is male by the statute that constitutes it, so leaving it in the rate would move
# the measured male share of the town's ROLLS by a hundred men nobody read off a roll at
# all, and the age of every one of them is drawn inside the recruiting window the Army's own
# regulations print rather than off the 1840 schedule.


def drawn_by_another_stage(person: dict) -> bool:
    """A reconstructed person whose own stage already settled their sex and age."""
    stage = (person.get("reconstruction") or {}).get("stage")
    return stage in SELF_DESCRIBING_STAGES


def without_this_pass(card: dict) -> dict:
    """The card as it stood before this pass ever ran. The basis of `--check`."""
    out = json.loads(json.dumps(card))
    for person in out.get("persons") or []:
        if drawn_by_another_stage(person):
            continue
        if ours_sex(person.get("sex_basis")):
            person.pop("sex_basis", None)
            person.pop("sex", None)
        person.pop("age_band", None)
    return out


def roll_of(card: dict) -> str:
    """The roll a person was minted off. `unclaimed` where no pass says."""
    return str(card.get("source_pass") or "unclaimed")


def collective(person: dict) -> bool:
    """A row that describes a group rather than a person."""
    _, _, why = read_name(person.get("name") or "")
    return why == "a_group_not_a_person"


def married_style_over_a_kinship_word(person: dict) -> bool:
    """A row a household seats as its child whose own name is printed in a married style.

    `dependent_child_under_15` assumes "nothing beyond what the record already says": the
    record calls them a child, so the child bands are drawn. Where the SAME record also
    prints a married style — Mrs, Madam, Widow — it does not say child. It says a married
    woman whom a household seats as its daughter, and the two readings cannot both be an
    age. T-1179 is this finding from the other side (a kinship word is not an age, and a
    grown man in his father's house is still that household's son); this is the case where
    the contradiction stands on the face of the name.

    Nor does the married style bound an age at the scene in the other direction. It is a
    style the card carries because a LATER source used it — a husband's initials, a
    widowhood, a recollection written down decades on — and no marriage on these cards is
    dated to 1 July 1835. `named_on_a_roll_15_and_over` therefore cannot claim the row
    either. So none of the three conditionings fits and no band is drawn.

    A register that calls the person an infant or a baptised child is a RECORD of
    childhood rather than a household's word for somebody, and it is read first: a row
    with one keeps its conditioning and its draw.
    """
    church = person.get("church_evidence") or []
    if any((e.get("locator") or "") in ("infant", "baptised", "child") for e in church):
        return False
    if str(person.get("relationship") or "").lower() not in CHILD_RELATIONSHIPS:
        return False
    if named_in_their_own_right(person):
        return False
    return any(tok in MARRIED_STYLES for tok in tokens(person.get("name") or ""))


def named_in_their_own_right(person: dict) -> bool:
    """The card names this person on a roll, in the press, or at a trade of their own.

    Exactly what `named_on_a_roll_15_and_over` is about, read off the card rather than
    off the word a household happens to use for somebody.
    """
    if person.get("roles"):
        return True
    for entry in person.get("civic_evidence") or []:
        if str(entry.get("list") or "").startswith(("poll_", "tax_", "muster_")):
            return True
    return any(person.get(key) for key in
               ("press_evidence", "book_evidence", "letter_list_returns"))


def conditioning_of(person: dict) -> str:
    church = person.get("church_evidence") or []
    if any((e.get("locator") or "") in ("infant", "baptised", "child") for e in church):
        return "dependent_child_under_15"
    # A KINSHIP WORD IS NOT AN AGE (T-1179). `relationship: son` says whose son a person
    # is and nothing about how old he is - a grown man living in his father's house is
    # still the household's son, and this project has one. John S. Wright kept a store on
    # South Water Street, stands in the press over the scene date and carries an attested
    # role of clerk; because his father's card calls him a son he was drawn out of the
    # schedule's 10-14 column, and the town's best-known young booster was eleven years
    # old. The conditioning's own words are the argument against the order it was tested
    # in - it assumes "nothing beyond what the record already says", and the record also
    # says he holds a trade. So evidence the person was named in their own right is read
    # FIRST, and the kinship word answers only for the children it is the only word for.
    if named_in_their_own_right(person):
        return ("civic_list_20_and_over" if age_band_of(person) == "adult_by_civic_list"
                else "named_on_a_roll_15_and_over")
    if str(person.get("relationship") or "").lower() in CHILD_RELATIONSHIPS:
        return "dependent_child_under_15"
    if age_band_of(person) == "adult_by_civic_list":
        return "civic_list_20_and_over"
    return "named_on_a_roll_15_and_over"


def measure(base: dict) -> dict:
    """The male rate of every roll, measured on the people whose sex is already settled.

    `base` is the layer WITHOUT this pass's fills, so the measurement never reads a
    draw of its own back in as evidence.
    """
    settled, men, unsettled = Counter(), Counter(), Counter()
    for hid, card in sorted(base.items()):
        roll = roll_of(card)
        for person in card.get("persons") or []:
            if collective(person):
                continue
            # A DRAW IS NEVER EVIDENCE, WHOEVER DREW IT. The sex another reconstruction
            # stage drew is as much a draw as one of this pass's, so it is kept out of the
            # rate for the same reason `base` strips this pass's own fills.
            if drawn_by_another_stage(person):
                continue
            if person.get("sex"):
                settled[roll] += 1
                if person["sex"] == "male":
                    men[roll] += 1
            else:
                unsettled[roll] += 1
    pooled_settled = sum(settled.values())
    pooled_men = sum(men.values())
    rolls = []
    for roll in sorted(set(settled) | set(unsettled)):
        own = settled[roll]
        measured = own >= MIN_SAMPLE
        rate = (men[roll] / own) if own else None
        rolls.append({
            "roll": roll,
            "settled_by_the_evidence": own,
            "of_those_male": men[roll],
            "own_male_rate": round(rate, 4) if rate is not None else None,
            "measured_on_its_own": measured,
            "drawn_at": round(rate, 4) if measured else round(pooled_men / pooled_settled, 4),
            "drawn_for": unsettled[roll],
            "why": ("its own %d settled names are enough to measure it" % own) if measured
                   else ("only %d of its names are settled - below the floor of %d, so it "
                         "draws at the pooled rate of every roll" % (own, MIN_SAMPLE)),
        })
    return {
        "floor": MIN_SAMPLE,
        "pooled": {"settled_by_the_evidence": pooled_settled, "of_those_male": pooled_men,
                   "male_rate": round(pooled_men / pooled_settled, 4)},
        "rolls": rolls,
    }


def rate_for(measurement: dict) -> dict:
    return {r["roll"]: r["drawn_at"] for r in measurement["rolls"]}


def town_row(town: dict, key: str) -> str:
    """One `Figure | Reading | Method` row of the town model, by its figure name."""
    for section in town["sections"]:
        for row in section.get("figures") or []:
            if row.get("figure") == key:
                point = row.get("point")
                return ("%s-%s (point reading %s)" % (row["low"], row["high"], point)
                        if point is not None else "%s-%s" % (row["low"], row["high"]))
    raise SystemExit("the town model has no figure %r" % key)


def model(base: dict) -> dict:
    town = json.loads(TOWN_MODEL.read_text(encoding="utf-8"))
    comp = json.loads(COMPOSITION.read_text(encoding="utf-8"))
    measurement = measure(base)
    letters = next((r for r in measurement["rolls"] if r["roll"] == "letter_list"), None)
    return {
        "$schema_note": "DERIVED. Rebuild with tools/reconstruct_sex_age.py --build; "
                        "tools/check.sh re-derives it. Never hand-edit.",
        "id": "chicago_july_1835_sex_age_draw_model",
        "ticket": "T-1304",
        "stage": "attribute_fill_sex_age",
        "target_date": "1835-07-01",
        "generated_by": "tools/reconstruct_sex_age.py",
        "_doc": "The distribution stage `attribute_fill_sex_age` draws a sex and an age "
                "band from, and the measurement that sets its rates. Nothing here names "
                "anybody. The sex rates are measured on THIS layer's own settled people, "
                "roll by roll; the age bands are the 1840 Chicago schedule's, which is "
                "the only committed sex x age band distribution this project holds.",
        "the_measurement_and_its_bias": {
            "what_was_measured": "the male share of every roll this layer was minted "
                                 "from, counted over the people whose sex T-1303 settled "
                                 "off a source, a gendered title or a forename",
            "the_letter_lists": (
                "%d of %d settled letter-list names are men - %s. This is the measured "
                "adult-male rate of a letter list the ticket asks for, and it is a "
                "measurement of these lists rather than a figure borrowed from the period."
                % (letters["of_those_male"], letters["settled_by_the_evidence"],
                   f"{letters['own_male_rate']:.1%}") if letters else "no letter list roll"),
            "the_bias_runs_one_way": (
                "The forename table T-1303 derived was built mostly on this layer's men, "
                "so a woman's forename is likelier than a man's to be missing from it and "
                "to fall into the unsettled group being drawn for. Every rate here is "
                "therefore a CEILING on its roll's male share rather than a point reading, "
                "and every draw made from it leans male by an amount this pass cannot "
                "bound. Stated, not smoothed; docs/LIBERTIES.md L-rc-sex-rate."),
            **measurement,
        },
        "the_rolls_are_not_the_town": {
            "the_rolls": "%s male, measured above" % f"{measurement['pooled']['male_rate']:.1%}",
            "the_town": "%s males per 100 females - a 55-60%% male town"
                        % town_row(town, "males_per_100_females"),
            "why_they_differ": "A roll of correspondents, voters and subscribers names "
                               "adult men; the town's women and children are named nowhere "
                               "in it. Nothing here is drawn at the town's ratio, because "
                               "none of these people is a draw from the town - they are "
                               "people a roll already named. The gap IS the reconstruction's "
                               "brief: T-1174 writes the women and children the pyramid "
                               "lacks, to its own quota.",
            "under_ten_in_the_town": "the town model's `share_under_ten`, 0.2-0.2702, "
                                     "which this stage draws for nobody: a person named on "
                                     "a roll is not a child under ten.",
        },
        "age_bands": {
            "source": "data/research/census_1840/composition_1840.json#age_bands.free_white",
            "what_it_licenses": comp["what_this_may_calibrate"],
            "what_it_forbids": comp["what_this_may_not_do"],
            "no_birth_year_is_written": "A draw yields the band the schedule prints. An "
                                        "exact year drawn from a decadal band would read as "
                                        "a record of a birth; T-1303 refused six thin "
                                        "death-notice matches for less.",
            "bands": age_bands(),
        },
        "conditionings": CONDITIONINGS,
        "seeds": {
            "sex": "<person_id>:%s" % SEED_SEX,
            "age": "<person_id>:%s" % SEED_AGE,
            "algorithm": "blake2s(seed.encode('utf-8'), digest_size=8) read as a "
                         "big-endian integer, taken modulo 1,000,000 over 1,000,000",
            "why_the_person_and_not_the_household": "The programme's seed_rule writes "
                                                    "<household_id>:<bucket>. Two people "
                                                    "share a household id and would draw "
                                                    "the same sex and the same band, so an "
                                                    "ATTRIBUTE fill seeds by the person.",
        },
    }


# --------------------------------------------------------------------------
# the blocks a drawn value owes
# --------------------------------------------------------------------------

def sex_block(person: dict, roll: str, rate: float, sex: str, seed: str,
              measured: bool) -> dict:
    return {
        "value": sex,
        "confidence": RECONSTRUCTED,
        "tier": RECONSTRUCTED,
        "basis": {
            "kind": "model",
            "id": "sex_share_of_the_roll",
            "note": "Drawn at %.1f%% male, the rate measured on the %s roll's own people "
                    "whose sex the evidence settles%s. "
                    "data/reconstruction/1835_sex_age_model.json holds the measurement."
                    % (rate * 100, roll,
                       "" if measured else " (pooled across every roll: this one settles "
                                           "too few names to measure on its own)"),
        },
        "seed": seed,
        "replaceable_by": {
            "kind": "person",
            "match": "a source that records this person's sex, a gendered title on their "
                     "name, or a forename the project's evidence lets fire",
        },
        "note": "A DRAW, NOT A READING. Nothing about this person says which sex they "
                "were: T-1303 refused the name and was right to. This value is drawn from "
                "the measured male share of the roll the person was named on, seeded by "
                "their own id so the draw reproduces - retype %r and the same face comes "
                "up. It carries no weight as evidence about this person and it is never "
                "promoted. The rate is a ceiling rather than a point reading, because the "
                "forename table that settled the rest was built mostly on men's names."
                % seed,
    }


def age_block_drawn(row: dict, conditioning: str, seed: str, sex: str) -> dict:
    cond = CONDITIONINGS[conditioning]
    return {
        "value": row["band"],
        "low": row["low"],
        "high": row["high"],
        "confidence": RECONSTRUCTED,
        "tier": RECONSTRUCTED,
        "basis": {
            "kind": "model",
            "id": "age_bands_1840",
            # The column is named IN the note rather than carried as a field of its own:
            # `tools/measure_layer_reads.py` is right that a figure shipped to a browser
            # that nothing reads is dead weight, and a reader wants the schedule's own
            # words here, not a second machine-readable copy of the band edges above.
            "note": "Drawn from the 1840 Chicago schedule's column '%s', one of its %s "
                    "bands, conditioned on `%s` because %s."
                    % (row["census_band"], sex, conditioning, cond["when"]),
        },
        "seed": seed,
        "replaceable_by": {
            "kind": "person",
            "match": "a source that states this person's age, their birth year, or an "
                     "interval either can be read out of",
        },
        "note": "AN AGE BAND, NEVER A YEAR. No source this project holds bears on when "
                "this person was born, so the band is drawn from the only committed sex "
                "by age distribution the project has - the 1840 Chicago schedule, five "
                "years after the scene and a town twice the size - seeded by this "
                "person's own id (%r). AND THE CONDITIONING IS THE MODEL'S, NOT A "
                "SOURCE'S: %s No exact year is written, because a year drawn from a "
                "decadal band would read as a record of a birth."
                % (seed, cond["assumes"]),
    }


def age_block_read(low: int, high, band: str, tier: str, from_what: str,
                   sources: list) -> dict:
    """The band a value already on the card puts the person in, at that value's own tier.

    IT CARRIES THAT VALUE'S SOURCES, and must: `validate.py` refuses an `attested` claim
    with no `source_id`, and it is right to — a view of an attested figure that cited
    nothing would be the one row on the card asking to be taken on trust.
    """
    out = {
        "value": band,
        "low": low,
        "high": high,
        "confidence": tier,
        "tier": tier,
    }
    if sources:
        out["sources"] = list(sources)
    out["note"] = ("THE BAND THIS PERSON'S OWN %s PUTS THEM IN on 1 July 1835. It is a view "
                "of a value already on this card and adds nothing to it; it exists so the "
                   "age axis can be read across the whole layer at once, beside the bands "
                   "the model draws for everybody else." % from_what)
    return out


def refusal_block(what: str) -> dict:
    return {
        "value": None,
        "confidence": RECONSTRUCTED,
        "tier": "unknown",
        "note": "A COLLECTIVE DESCRIPTION NAMES NOBODY, so there is no %s to draw. This "
                "row stands for more than one person and a single band or a single sex "
                "would make a group into a person. The refusal is T-1303's and it is kept "
                "here word for word rather than overridden by a model that could not tell."
                % what,
    }


def kinship_refusal_block() -> dict:
    """T-1395's refusal: the row names one person and still earns no band."""
    return {
        "value": None,
        "confidence": RECONSTRUCTED,
        "tier": "unknown",
        "note": "NO BAND IS DRAWN, AND THE REASON IS THIS CARD'S OWN. A household seats "
                "this person as its child and the same record names them in a married "
                "style, printed by a source later than the scene. A KINSHIP WORD IS NOT "
                "AN AGE (T-1179) and a married style is not one either: neither is dated "
                "to 1 July 1835, and they cannot both be read as a band. None of this "
                "pass's three conditionings fits, and a band drawn from the schedule's "
                "child columns would make a married woman a child under fifteen. This "
                "row names ONE person, which is why it does not carry the collective "
                "refusal it used to: the refusal is T-1395's and the reason is the "
                "card's.",
    }


def band_for_age(age: int, sex: str, bands: list) -> dict:
    """The 1840 band an age falls in, for the sex given (male where none is known)."""
    want = sex if sex in ("male", "female") else "male"
    for row in bands:
        if row["sex"] != want:
            continue
        if row["high"] is None:
            if age >= row["low"]:
                return row
        elif row["low"] <= age <= row["high"]:
            return row
    return None


def value_of(block):
    return block.get("value") if isinstance(block, dict) else block


def tier_of_block(block) -> str:
    conf = block.get("confidence") if isinstance(block, dict) else None
    return conf if conf in ("attested", "inferred") else "inferred"


# --------------------------------------------------------------------------
# the build
# --------------------------------------------------------------------------

def settle_order(person: dict) -> None:
    """`age_band` first, then the blocks T-1303 re-derives, in the order IT writes them.

    THIS IS A GATE'S REQUIREMENT, NOT A STYLE. `tools/spend_person_sex_age.py --check`
    proves the layer by stripping ITS OWN sex fills and deriving them again, and a
    re-derived fill lands at the END of the person. If this pass appended `age_band`
    after one of those blocks, the derived card would put `age_band` before them and the
    committed card after, and 597 cards would read as drift on a difference of ordering
    alone. Writing the same order both passes produce costs three lines and keeps the two
    gates honest about each other.
    """
    if "age_band" in person:
        person["age_band"] = person.pop("age_band")
    # `tools/spend_person_sex_age.apply_to` writes sex, then its reason, then the birth
    # year, in that order. A block of THIS pass's — a sex it drew, graded reconstructed —
    # is not one of those and is left where it lies.
    if (person.get("sex_basis") or {}).get("confidence") == "inferred":
        for key in ("sex", "sex_basis"):
            if key in person:
                person[key] = person.pop(key)
    if ours_birth(person.get("birth_year")):
        person["birth_year"] = person.pop("birth_year")


def fill(base: dict) -> tuple:
    """(cards with this pass's blocks, the ledger counts). Pure over `base`."""
    out = json.loads(json.dumps(base))
    mdl = model(base)
    rates = rate_for(mdl["the_measurement_and_its_bias"])
    measured = {r["roll"]: r["measured_on_its_own"] for r in
                mdl["the_measurement_and_its_bias"]["rolls"]}
    bands = mdl["age_bands"]["bands"]
    by_sex = defaultdict(list)
    for row in bands:
        by_sex[row["sex"]].append(row)

    counts = {"sex_drawn": Counter(), "sex_refused": Counter(), "sex_already": Counter(),
              "age_drawn": Counter(), "age_read": Counter(), "age_refused": Counter(),
              "drawn_sex_is": Counter(), "drawn_band_is": Counter()}

    for hid in sorted(out):
        card = out[hid]
        roll = roll_of(card)
        for person in card.get("persons") or []:
            pid = str(person.get("id") or "")
            # A PERSON A CENSUS BAND ALREADY DATES IS NOT ONE TO DRAW AN AGE FOR (T-1314).
            # The `named_families` stage writes people the 1840 schedule COUNTS in an age
            # column, and carries the band it back-projects to on the record. Drawing an
            # age band for them out of the population model would put a draw beside a
            # reading of the same person and let the weaker one win a coin toss.
            if drawn_by_another_stage(person):
                counts["age_read"]["another_stage_drew_them"] += 1
                continue
            if (person.get("reconstruction") or {}).get("age_on_scene_date"):
                person["age_band"] = counted_band_block(person)
                counts["age_read"][roll] += 1
                settle_order(person)
                continue
            if collective(person):
                if not person.get("sex"):
                    person["sex_basis"] = refusal_block("sex")
                    counts["sex_refused"]["a_group_not_a_person"] += 1
                person["age_band"] = refusal_block("age band")
                counts["age_refused"]["a_group_not_a_person"] += 1
                settle_order(person)
                continue

            # --- sex
            if person.get("sex"):
                counts["sex_already"][roll] += 1
            else:
                seed = seed_for(pid, SEED_SEX)
                rate = rates[roll]
                sex = "male" if unit(seed) < rate else "female"
                person["sex"] = sex
                person["sex_basis"] = sex_block(person, roll, rate, sex, seed,
                                                measured.get(roll, False))
                counts["sex_drawn"][roll] += 1
                counts["drawn_sex_is"][sex] += 1

            # --- age
            sex = person.get("sex") or "male"
            born = value_of(person.get("birth_year"))
            aged = value_of(person.get("age_on_scene_date"))
            if born:
                row = band_for_age(SCENE_YEAR - int(born), sex, bands)
                person["age_band"] = age_block_read(
                    row["low"], row["high"], row["band"],
                    tier_of_block(person.get("birth_year")), "BIRTH YEAR",
                    (person.get("birth_year") or {}).get("sources") or [])
                counts["age_read"]["birth_year"] += 1
            elif aged is not None:
                row = band_for_age(int(aged), sex, bands)
                person["age_band"] = age_block_read(
                    row["low"], row["high"], row["band"],
                    tier_of_block(person.get("age_on_scene_date")), "STATED AGE",
                    (person.get("age_on_scene_date") or {}).get("sources") or [])
                counts["age_read"]["age_on_scene_date"] += 1
            elif married_style_over_a_kinship_word(person):
                person["age_band"] = kinship_refusal_block()
                counts["age_refused"]["a_married_style_over_a_kinship_word"] += 1
            else:
                conditioning = conditioning_of(person)
                cond = CONDITIONINGS[conditioning]
                seed = seed_for(pid, SEED_AGE)
                allowed = [(r, r["persons"]) for r in by_sex[sex]
                           if r["low"] >= cond["low_edge"]
                           and (cond["high_edge"] is None or r["low"] < cond["high_edge"])]
                row = pick(seed, allowed)
                person["age_band"] = age_block_drawn(row, conditioning, seed, sex)
                counts["age_drawn"][conditioning] += 1
                counts["drawn_band_is"][row["band"]] += 1
            settle_order(person)
    return out, {k: dict(v) for k, v in counts.items()}


def build() -> int:
    base = {hid: without_this_pass(card) for hid, card in cards().items()}
    filled, counts = fill(base)
    written = 0
    for hid, card in filled.items():
        path = HOUSEHOLDS / f"{hid}.json"
        text = dumps(card)
        if path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
            written += 1
    ledger = dict(model(base))
    ledger["counts"] = counts
    MODEL.write_text(dumps(ledger), encoding="utf-8")
    print("  wrote %s" % MODEL.relative_to(ROOT))
    print("  %d card(s) rewritten; %d sex drawn, %d age band(s) drawn, %d read"
          % (written, sum(counts["sex_drawn"].values()),
             sum(counts["age_drawn"].values()), sum(counts["age_read"].values())))
    return 0


def check() -> int:
    live = cards()
    base = {hid: without_this_pass(card) for hid, card in live.items()}
    filled, counts = fill(base)
    bad = [hid for hid in sorted(live) if dumps(live[hid]) != dumps(filled[hid])]
    if bad:
        print("  FAIL %d card(s) are not what this pass derives: %s"
              % (len(bad), ", ".join(bad[:6])))
        return 1
    want = dict(model(base))
    want["counts"] = counts
    if not MODEL.exists() or MODEL.read_text(encoding="utf-8") != dumps(want):
        print("  FAIL %s is not what --build writes" % MODEL.relative_to(ROOT))
        return 1
    people = sum(len(c.get("persons") or []) for c in live.values())
    placed = sum(1 for c in live.values() for p in (c.get("persons") or [])
                 if p.get("birth_year") or value_of(p.get("age_band")))
    sexed = sum(1 for c in live.values() for p in (c.get("persons") or []) if p.get("sex"))
    refused = sum(counts["age_refused"].values())
    if placed + refused != people:
        print("  FAIL %d of %d people carry neither a birth year nor an age band"
              % (people - placed - refused, people))
        return 1
    print("  ok    %d of %d people carry a sex; %d a birth year or an age band; %d "
          "row(s) refused a band, and say why" % (sexed, people, placed, refused))
    print("  ok    the model, the rates and every drawn block re-derive")
    return 0


def report() -> int:
    base = {hid: without_this_pass(card) for hid, card in cards().items()}
    mdl = model(base)
    _, counts = fill(base)
    print("THE MEASURED MALE RATE, ROLL BY ROLL")
    for row in mdl["the_measurement_and_its_bias"]["rolls"]:
        print("   %-12s settled %4d  male %4d  rate %s  draws for %4d  -> %.4f"
              % (row["roll"], row["settled_by_the_evidence"], row["of_those_male"],
                 ("%.4f" % row["own_male_rate"]) if row["own_male_rate"] is not None
                 else "  n/a ", row["drawn_for"], row["drawn_at"]))
    for key in ("sex_drawn", "sex_refused", "drawn_sex_is", "age_drawn", "age_read",
                "age_refused", "drawn_band_is"):
        print(key.upper().replace("_", " "))
        for name, n in sorted(counts[key].items(), key=lambda kv: (-kv[1], kv[0])):
            print("   %-28s %5d" % (name, n))
    return 0


# --------------------------------------------------------------------------
# the self-test — the rules above, held over what this pass derives
# --------------------------------------------------------------------------

def self_test() -> int:
    fails = []

    def ok(name, cond):
        print(("  ok    " if cond else "  FAIL  ") + name)
        if not cond:
            fails.append(name)

    ok("a seed reproduces its draw", unit("wilson_john:sex_ratio")
       == unit("wilson_john:sex_ratio"))
    ok("two people do not share a draw",
       unit("wilson_john:sex_ratio") != unit("wilson_jane:sex_ratio"))
    ok("the sex seed and the age seed differ for one person",
       unit("wilson_john:sex_ratio") != unit("wilson_john:age_bands_1840"))

    bands = age_bands()
    ok("the schedule's 26 bands are read", len(bands) == 26)
    ok("a band label reads back as its edges",
       band_label("free white males 20 under 30") == ("20-29", 20, 29))
    ok("the youngest band starts at nought",
       band_label("free white females Under 5") == ("0-4", 0, 4))
    ok("the open band has no top", band_label("free white males 100 and upwards")[2] is None)

    child = [r for r in bands if r["sex"] == "male" and r["low"] < 15]
    ok("a child conditioning can never draw an adult band",
       all(r["high"] is not None and r["high"] < 15 for r in child))
    adult = [r for r in bands if r["sex"] == "male" and r["low"] >= 20]
    ok("a civic conditioning can never draw a child band", all(r["low"] >= 20 for r in adult))

    ok("a group is refused a sex", collective({"name": "The four Temple children"}))
    ok("a person is not", not collective({"name": "John Wilson"}))
    # T-1395: a leading article made one named woman into a group.
    ok("a leading article is not a group on its own",
       not collective({"name": "The Harmon daughter later known as Mrs A. G. Burley"}))
    ok("a married style over a kinship word refuses a band",
       married_style_over_a_kinship_word(
           {"name": "The Harmon daughter later known as Mrs A. G. Burley",
            "relationship": "daughter"}))
    ok("a plain daughter keeps her conditioning",
       not married_style_over_a_kinship_word({"name": "Eliza Harmon",
                                              "relationship": "daughter"})
       and conditioning_of({"name": "Eliza Harmon", "relationship": "daughter"})
       == "dependent_child_under_15")
    ok("a married style outside a household's child word refuses nothing",
       not married_style_over_a_kinship_word({"name": "Mrs Rufus Brown",
                                              "relationship": "wife"}))
    ok("a register calling the person an infant is read before the style is",
       not married_style_over_a_kinship_word(
           {"name": "Mrs A. B.", "relationship": "daughter",
            "church_evidence": [{"locator": "infant"}]}))
    ok("a roll of her own is read before the style is",
       not married_style_over_a_kinship_word(
           {"name": "Mrs A. B.", "relationship": "daughter", "roles": [{"role": "milliner"}]}))
    ok("the refusal says it names one person and names its reason",
       "ONE person" in kinship_refusal_block()["note"]
       and kinship_refusal_block()["value"] is None
       and kinship_refusal_block()["tier"] == "unknown")

    ok("a drawn sex block is graded reconstructed and this pass owns it",
       ours_sex(sex_block({}, "letter_list", 0.94, "male", "s", True)))
    ok("a read sex block from T-1303 is not ours",
       not ours_sex({"value": "male", "confidence": "inferred", "note": "forename"}))

    drawn = age_block_drawn({"band": "20-29", "census_band": "free white males 20 under 30",
                             "low": 20, "high": 29}, "civic_list_20_and_over", "s", "male")
    ok("a drawn age band names the schedule's own column",
       "free white males 20 under 30" in drawn["basis"]["note"])
    ok("a drawn age band writes no birth year", "birth_year" not in drawn)
    ok("a drawn age band carries its seed and its replacement rule",
       drawn.get("seed") == "s" and drawn["replaceable_by"]["kind"] == "person")
    ok("a drawn age band says the conditioning is the model's",
       "NOT A SOURCE'S" in drawn["note"])

    read = age_block_read(20, 29, "20-29", "inferred", "BIRTH YEAR", ["a_source"])
    ok("a read age band carries no basis, seed or replacement rule",
       not any(k in read for k in ("basis", "seed", "replaceable_by")))
    ok("a read age band cites what it is a view of", read["sources"] == ["a_source"])
    ok("...and cites nothing where the value it reads cites nothing",
       "sources" not in age_block_read(20, 29, "20-29", "inferred", "BIRTH YEAR", []))

    want = ["id", "name", "age_band", "sex", "sex_basis", "birth_year"]
    scrambled = {"id": "p", "sex": "male",
                 "sex_basis": {"value": "male", "confidence": "inferred"},
                 "birth_year": {"value": 1799,
                                "sources": ["calumet_club_early_chicago_1879"]},
                 "name": "n", "age_band": {"value": "20-29"}}
    settle_order(scrambled)
    ok("a read sex and a spent birth year settle in the order T-1303 writes them",
       list(scrambled) == want)
    settle_order(scrambled)
    ok("...and settling twice moves nothing", list(scrambled) == want)
    drawn_person = {"id": "p", "sex": "male",
                    "sex_basis": {"value": "male", "confidence": RECONSTRUCTED},
                    "age_band": {"value": "20-29"}}
    settle_order(drawn_person)
    ok("a DRAWN sex is left where it lies; T-1303 never re-derives it",
       list(drawn_person) == ["id", "sex", "sex_basis", "age_band"])

    recorded = {"id": "p", "sex": "male", "name": "n"}
    settle_order(recorded)
    ok("a recorded sex with no reason keeps the mint's own order",
       list(recorded) == ["id", "sex", "name"])

    rf = refusal_block("sex")
    ok("a refusal asserts nothing and carries no draw",
       rf["value"] is None and rf["tier"] == "unknown" and "seed" not in rf)

    # the whole distribution, over a nominal roll: a rate of 1 draws every man
    ok("a rate of 1.0 draws a man every time",
       all(("male" if unit(f"p{i}:sex_ratio") < 1.0 else "female") == "male"
           for i in range(200)))
    ok("a rate of 0.0 draws a woman every time",
       all(("male" if unit(f"p{i}:sex_ratio") < 0.0 else "female") == "female"
           for i in range(200)))
    # ... and the measured rate lands near itself over the layer's own scale
    men = sum(1 for i in range(2000) if unit(f"p{i}:sex_ratio") < 0.9435)
    ok("a rate of 0.9435 draws within a point of itself over 2,000 seeds",
       abs(men / 2000 - 0.9435) < 0.01)

    print("  %d case(s) failed" % len(fails) if fails else "  all cases pass")
    return 1 if fails else 0


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", dest="self_test", action="store_true")
    args = ap.parse_args(argv)
    if args.build:
        return build()
    if args.check:
        return check()
    if args.report:
        return report()
    if args.self_test:
        return self_test()
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
