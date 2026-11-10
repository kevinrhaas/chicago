"""Append-only, explicitly reconstructed completion of T-2023's frozen person room.

This is a bounded programme extension, never a source about a historical family.
The old keeper-child and ordinary-bed draws remain byte-for-byte reproducible.
"""
import copy
import hashlib
import json
import re
from collections import Counter

TICKET = "T-2023"
NORTH = "recon_1835_blk_indiana_north_cass_h3_09"
SOUTH = "tremont_house_1"
WEST = "recon_1835_blk_washington_clinton_h3_02"


def fingerprint(person):
    # Current-capacity explanatory text is allowed to report a later weight;
    # identity, kinship, ages, occupations, provenance and seeds stay frozen.
    text = json.dumps(person, sort_keys=True, ensure_ascii=False)
    text = re.sub(r"the current model reports [0-9]+", "the current model reports <current>", text)
    return hashlib.sha256(text.encode()).hexdigest()


def apply(s, houses, cards, seated_by_house, drawn, live_room, arrivals,
          pool, taken_names, taken_ids):
    """Return exact supplementary fills and their carried allocation contract."""
    old = s.load(s.LEDGER) if s.LEDGER.exists() else {}
    carried = old.get("quota_basis", {}).get("remainder_completion")
    rows = copy.deepcopy(carried["buckets"]) if carried else [
        {"bucket": key, "division": div, "sex": sex, "age_band": band,
         "to_complete": max(0, int(n) - int(arrivals.get(key, 0)) - int(drawn[key]))}
        for (div, sex, band, axis), (key, n) in sorted(live_room.items())
        if axis == "none" and band in ("under_10", "10_19")
        and max(0, int(n) - int(arrivals.get(key, 0)) - int(drawn[key]))]
    left = {r["bucket"]: r["to_complete"] for r in rows}
    expected = {("north", "female", "under_10"): 1,
                ("south", "female", "under_10"): 4,
                ("west", "female", "under_10"): 4,
                ("south", "male", "10_19"): 3,
                ("west", "male", "10_19"): 1}
    if {(r["division"], r["sex"], r["age_band"]): r["to_complete"]
            for r in rows} != expected:
        raise SystemExit("FAIL T-2023 completion room changed; deliberate review required")
    by_id = {h["id"]: h for h in houses}
    fills, child_counts = Counter(), Counter()
    additions, family_draws = [], []

    # These are frozen pre-extension whole-roof occupancy figures, including the
    # independent housing overlay. New housing admissions are checked separately.
    occupancy_basis = {NORTH: 12, SOUTH: 12, WEST: 11}
    if carried and carried.get("whole_roof_occupancy_before") != occupancy_basis:
        raise SystemExit("FAIL T-2023 shared occupancy contract changed")
    actual = dict(occupancy_basis)

    def append(sid, person, kind):
        card = cards[f"hh_lodging_{sid}"]
        card["persons"].append(person)
        card["lodging_household"]["minted_here"] = len(card["persons"])
        additions.append({"person": person["id"], "place": sid, "kind": kind})
        fills[person["remainder_bucket"]] += 1
        left[person["remainder_bucket"]] -= 1
        actual[sid] += 1
        if kind == "child":
            child_counts[sid] += 1
        else:
            by_id[sid]["minted_lodgers"] += 1
            by_id[sid]["occupancy"] += 1

    # Three ordinary South beds really are vacant. The single West youth is an
    # explicit exceptional night, ordinary11 ->12, inside the unchanged full26.
    for sid, div, n in ((SOUTH, "south", 3), (WEST, "west", 1)):
        key = f"persons/male/10_19/{div}/lodging/none"
        for i in range(1, n + 1):
            slot = f"lodgers:remainder_completion:{sid}:male:10_19:{i:03d}"
            person = s.person_card(slot, "male", "10_19", key, by_id[sid],
                                   s.RELATION[by_id[sid]["class"]], pool,
                                   taken_names, taken_ids)
            person["dealt_by"] = {"ticket": TICKET,
                "note": "Appended from quota_basis.remainder_completion; all earlier draws are carried."}
            person["remainder_bucket"] = key
            append(sid, person, "youth")

    mf = s.household_model()
    ages, sizes = mf.age_rows(), mf.size_rows()
    child_rows = [(r, r[2]) for r in ages if r[1] < 20]
    boy_rate = sum(r[2] for r in ages if r[0] == "male" and r[1] < 20) / float(
        sum(r[2] for r in ages if r[1] < 20))
    communities = {c["id"]: c for c in pool["communities"]}
    north_card = s.load(s.ROOT / "data/residents/reconstructed_trades/hh_rc_chevalier_pierre.json")
    north_parent = north_card["persons"][0]
    candidates = [(NORTH, north_parent, north_card["id"], 8)]
    for sid in (SOUTH, WEST):
        # Only pre-existing anonymous adult lodgers; the four appended youths
        # cannot acquire children in the same completion draw.
        candidates += [(sid, p, cards[f"hh_lodging_{sid}"]["id"], None)
                       for p in cards[f"hh_lodging_{sid}"]["persons"]
                       if p["grade"] == s.RECONSTRUCTED and not p.get("kin_of")
                       and p["age_band"]["low"] >= 20]
    for sid, parent, parent_household, original_size in candidates:
        div = by_id[sid]["division"]
        key = f"persons/female/under_10/{div}/lodging/none"
        if left.get(key, 0) <= 0:
            continue
        seed = f"T-2023:lodging_family:{parent['id']}"
        size = original_size or s.pick(seed + ":household_size", sizes)
        cap = min(19, max(0, parent["age_band"]["low"] - 20))
        community = communities[parent["reconstruction"]["community"]]
        surname = mf.surname_of(parent["name"])
        family_names = {surname.lower(), parent["name"].split(" ", 1)[0].lower()}
        family = {"parent": parent["id"], "parent_household": parent_household,
                  "place": sid, "size_drawn": size,
                  "size_basis": "carried original trade-household draw" if original_size
                                else "supplementary 1840 size-histogram draw",
                  "seed": seed, "draws": []}
        for i in range(1, size):
            slot = seed + f":child:{i:03d}"
            row = s.pick(slot + ":age_bands_1840", [(r, w) for r, w in child_rows if r[1] <= cap])
            sex = "male" if s.unit(slot + ":sex_ratio") < boy_rate else "female"
            draw = {"index": i, "sex": sex, "age_band": "under_10" if row[1] < 10 else "10_19"}
            family["draws"].append(draw)
            if sex != "female" or row[1] >= 10 or left[key] <= 0:
                draw["outcome"] = "not this remaining order; never re-banded"
                continue
            child = s.child_card(slot, sex, key, by_id[sid], parent, surname, community,
                                 size, i, size - 1, cap, taken_names, taken_ids, family_names)
            if child is None:
                draw["outcome"] = "name pool exhausted; no invented replacement"
                continue
            def clarify(value):
                if isinstance(value, str):
                    return value.replace("keeper", "anonymous adult lodger")
                if isinstance(value, list):
                    return [clarify(v) for v in value]
                if isinstance(value, dict):
                    return {k: clarify(v) for k, v in value.items()}
                return value
            child = clarify(child)
            child["kin_of"].update(household=parent_household,
                relation="reconstructed child of an anonymous adult lodger",
                note="An explicit R supplementary family relation. No historical source identifies this parent or child.")
            child["reconstruction"]["ticket"] = TICKET
            child["resident_subtype"] = "reconstructed_lodger_child"
            child["dealt_by"] = {"ticket": TICKET,
                "note": "Supplementary family completion; carried old family draws and identities unchanged."}
            child["remainder_bucket"] = key
            child["basis"]["note"] = (
                f"Supplementary anonymous lodging-family draw of {size}, child {i}; "
                "size and child sex/age seeds are recorded in quota_basis.remainder_completion. "
                "Only the live lodging order is paid; no family/none counter is spent.")
            child["note"] = (
                f"RECONSTRUCTED, NOT FOUND. A supplementary child of {parent['name']}, "
                "an anonymous reconstructed adult lodger, under the unchanged crowded "
                "capacity of their shared sleeping roof. Parentage is explicitly modeled. "
                "The name is drawn from the existing pool; no source names this family.")
            append(sid, child, "child")
            block = cards[f"hh_lodging_{sid}"]["lodging_household"]
            block["note"] = (
                "A storage container for unrelated lodgers and expressly modeled kin groups. "
                "Sharing this card implies no kinship: every child names their own modeled "
                "parent, who may hold a separate source household card at this same roof.")
            block.setdefault("supplementary_parent_links", []).append({
                "child": child["id"], "parent": parent["id"], "parent_name": parent["name"],
                "parent_household": parent_household, "grade": "reconstructed"})
            draw.update(outcome="seated", person=child["id"])
        family_draws.append(family)
    if any(left.values()):
        raise SystemExit("FAIL T-2023 family/name draw leaves orders: " + str(left))
    if sum(fills.values()) != 13:
        raise SystemExit("FAIL T-2023 may append exactly its13 carried ordered people")
    for sid, n in actual.items():
        if n > by_id[sid]["beds_crowded"]:
            raise SystemExit("FAIL T-2023 shared roof exceeds unchanged crowded capacity")
    for sid, n in child_counts.items():
        by_id[sid]["supplementary_children"] = n
    block = {"ticket": TICKET, "buckets": rows,
             "statement": "Bounded R completion, after every frozen draw. No historical family is asserted.",
             "whole_roof_occupancy_before": occupancy_basis,
             "whole_roof_occupancy_after": actual,
             "ordinary_exception": {"place": WEST, "division": "west", "persons": 1,
                "ordinary_beds_unchanged": 11, "crowded_beds_unchanged": 26,
                "meaning": "One exceptional night within the existing full capacity; not an empty ordinary bed."},
             "supplementary_children": dict(child_counts), "family_draws": family_draws,
             "additions": additions, "unspent": left}
    if carried:
        for key, value in carried.items():
            if key == "preserved_person_fingerprints":
                continue  # checked after employment and current-capacity metadata carry
            if block.get(key) != value:
                raise SystemExit("FAIL T-2023 carried identity/kinship/roof allocation changed: " + key)
    return dict(sorted(fills.items())), block


def verify(s, cards, ledger):
    """Refuse unpriced people, unsupported kinship, or a broadened night exception."""
    block = ledger["quota_basis"]["remainder_completion"]
    rows = block["additions"]
    originals = {p["id"]: fingerprint(p)
                 for card in cards.values() for p in card["persons"]
                 if (p.get("dealt_by") or {}).get("ticket") != TICKET}
    if len(originals) != 157 or originals != block["preserved_person_fingerprints"]:
        raise SystemExit("FAIL T-2023 changed an original frozen person record")
    if len(rows) != 13 or len({r["person"] for r in rows}) != 13:
        raise SystemExit("FAIL T-2023 completion must contain its13 distinct ordered people")
    if sum(ledger["remainder_fills"].values()) != 13 or any(block["unspent"].values()):
        raise SystemExit("FAIL T-2023 completion overdrawn or incomplete")
    expected_exception = {"place": WEST, "division": "west", "persons": 1,
        "ordinary_beds_unchanged": 11, "crowded_beds_unchanged": 26,
        "meaning": "One exceptional night within the existing full capacity; not an empty ordinary bed."}
    if block["ordinary_exception"] != expected_exception:
        raise SystemExit("FAIL T-2023 ordinary-night exception exceeds its reviewed single West youth")
    capacity_basis = ledger["capacity_allocation_basis"]
    authorization = capacity_basis["initial_allocation_authorized_empty_beds"]
    initial_slept = sum(h["beds_ordinary"] for h in capacity_basis["houses"]) - authorization
    acquired = max(0, sum(h["occupancy_after"] for h in ledger["houses"]) - initial_slept)
    if acquired > authorization:
        raise SystemExit("FAIL T-2023 overdraws the unchanged allocation authorization")
    by_id = {p["id"]: p for c in cards.values() for p in c["persons"]}
    external = s.load(s.ROOT / "data/residents/reconstructed_trades/hh_rc_chevalier_pierre.json")
    by_id.update({p["id"]: p for p in external["persons"]})
    house_of = {p["id"]: c["lodging_household"]["place"] for c in cards.values() for p in c["persons"]}
    house_of[external["persons"][0]["id"]] = NORTH
    houses = {h["id"]: h for h in ledger["houses"]}
    if houses[WEST]["beds_ordinary"] != 11 or houses[WEST]["beds_crowded"] != 26:
        raise SystemExit("FAIL T-2023 changed West ordinary/crowded capacity")
    if houses[WEST]["occupancy_after"] != 12:
        raise SystemExit("FAIL T-2023 West ordinary occupancy is not the one reviewed extra youth")
    if sum(h["beds_ordinary"] for h in houses.values()) != 252:
        raise SystemExit("FAIL T-2023 changed the ordinary bed programme")
    if ledger["capacity_allocation_basis"]["initial_allocation_authorized_empty_beds"] != 32:
        raise SystemExit("FAIL T-2023 changed the carried mint authorization")
    expected_parents = {d["person"]: fam["parent"] for fam in block["family_draws"]
                        for d in fam["draws"] if d.get("outcome") == "seated"}
    counted = Counter()
    for row in rows:
        p = by_id.get(row["person"])
        if not p or house_of.get(p["id"]) != row["place"] or p["grade"] != s.RECONSTRUCTED:
            raise SystemExit("FAIL T-2023 identity, grade or sleeping roof changed")
        if p["remainder_bucket"] not in ledger["remainder_fills"]:
            raise SystemExit("FAIL T-2023 person has no ordered bucket")
        counted[p["remainder_bucket"]] += 1
        if row["kind"] == "child":
            kin = p.get("kin_of") or {}
            if kin.get("person") != expected_parents.get(p["id"]):
                raise SystemExit("FAIL T-2023 child kinship differs from its carried draw")
            parent = by_id.get(kin.get("person"))
            if (not parent or parent["grade"] != s.RECONSTRUCTED
                    or parent["age_band"]["low"] < 20 or kin.get("name") != parent["name"]):
                raise SystemExit("FAIL T-2023 child lacks an anonymous reconstructed adult parent")
            if house_of[parent["id"]] != row["place"] or p["age_band"]["high"] >= 10:
                raise SystemExit("FAIL T-2023 child moved away from parent or was re-banded")
        elif p["sex"] != "male" or p["age_band"]["value"] != "10-19":
            raise SystemExit("FAIL T-2023 youth changed sex or age band")
    if dict(counted) != ledger["remainder_fills"]:
        raise SystemExit("FAIL T-2023 person and bucket receipts disagree")
    live_joint = {r["place"]: r for r in ledger["shared_occupancy"]["houses"]}
    for sid, n in block["whole_roof_occupancy_after"].items():
        if live_joint[sid]["people"] > houses[sid]["beds_crowded"]:
            raise SystemExit("FAIL T-2023 live joint occupancy exceeds unchanged crowded cap")
        if n != block["whole_roof_occupancy_before"][sid] + sum(r["place"] == sid for r in rows):
            raise SystemExit("FAIL T-2023 shared-roof occupancy is not conserved")
        if n > houses[sid]["beds_crowded"]:
            raise SystemExit("FAIL T-2023 exceeds existing shared-roof full capacity")


def shared_occupancy(s, cards):
    """Dedupe person IDs across every sleeping overlay, including housing seats."""
    import house_the_present_1835 as housing
    inputs = housing.read_inputs()
    all_cards = {hid: r["card"] for hid, r in inputs["cards"].items()}
    all_cards.update(cards)
    occupants = {}
    for sid, rows in housing.compile_residents(housing=False).items():
        here = occupants.setdefault(sid, set())
        for row in rows:
            if row.get("relation") == housing.WORKED_HERE:
                continue
            here.update(p["id"] for p in all_cards[row["household"]].get("persons", []))
    for row in housing.load(housing.OUT)["seats"]:
        occupants.setdefault(row["place"], set()).update(
            p["id"] for p in all_cards[row["household"]].get("persons", []))
    # All derived cards are sleeping cards, including a card newly created by
    # this append stage before it exists on disk or in compiled residents.
    for card in cards.values():
        occupants.setdefault(card["lodging_household"]["place"], set()).update(
            p["id"] for p in card["persons"])
    return occupants


def seat_north_party(s, houses, seats):
    """Two existing unplaced adults, one R non-kin boarding party, no new person."""
    house = next(h for h in houses if h["id"] == "steamboat_hotel")
    current = next(p for p in s.lodging_model()["places"] if p["id"] == "steamboat_hotel")
    if house["occupancy"] != 8 or current["beds_ordinary"] != 10:
        raise SystemExit("FAIL T-2023 North party's two ordinary Steamboat beds changed")
    housing = s.load(s.ROOT / "data/reconstruction/1835_housing_seats.json")
    basis = housing.get("allocation_basis") or housing
    protected = {r["household"] for r in basis["seats"]}
    for hid, pid in (("hh_judar_barbery", "judar_barbery"), ("hh_welsh_t", "welsh_t")):
        if hid in protected or any(r["person"] == pid for r in seats):
            raise SystemExit("FAIL T-2023 North party would move an accepted resident")
        card = s.load(s.ROOT / f"data/residents/households/{hid}.json")
        if len(card["persons"]) != 1 or card["persons"][0]["id"] != pid:
            raise SystemExit("FAIL T-2023 North party's original cards changed")
        person = card["persons"][0]
        seats.append({"person": pid, "name": person["name"], "household": hid,
            "file": f"households/{hid}.json", "drawn_solitary_by": TICKET,
            "drawn_solitary_in_stage": "existing_unplaced_north_boarding_party",
            "trade": (person.get("occupation") or {}).get("value", "none_recorded"),
            "group": "labour", "place": "steamboat_hotel", "place_name": house["name"],
            "relationship": "lodger", "basis": {"kind": "rule", "id": "T-2023",
                "note": "R placement of an existing present North adult in one of two real ordinary beds. The shared party implies no marriage, kinship or travel association; source identity and grade unchanged."},
            "replaceable_by": {"kind": "person", "match": "dated evidence naming this person's actual July1835 home"}})
    house["occupancy"] += 2


def self_test(s):
    cards, ledger = s.fill()
    verify(s, cards, ledger)
    def expect(label, mutate):
        cc, ll = copy.deepcopy(cards), copy.deepcopy(ledger)
        mutate(cc, ll)
        try:
            verify(s, cc, ll)
        except SystemExit:
            return
        raise AssertionError("T-2023 guard failed: " + label)
    for field, value in (("persons", 2), ("division", "south"), ("place", SOUTH),
                         ("ordinary_beds_unchanged", 12), ("crowded_beds_unchanged", 27)):
        expect("exception " + field, lambda c, l, f=field, v=value:
               l["quota_basis"]["remainder_completion"]["ordinary_exception"].update({f: v}))
    expect("authorization raised", lambda c, l: l["capacity_allocation_basis"].update(
        initial_allocation_authorized_empty_beds=33))
    expect("authorization overdrawn", lambda c, l: l["houses"][0].update(
        occupancy_after=l["houses"][0]["occupancy_after"] + 33))
    expect("new person beyond order", lambda c, l: l["remainder_fills"].update(
        {next(iter(l["remainder_fills"])): 2}))
    child_id = next(r["person"] for r in ledger["quota_basis"]["remainder_completion"]["additions"]
                    if r["kind"] == "child")
    def wrong_parent(c, l):
        next(p for card in c.values() for p in card["persons"] if p["id"] == child_id)["kin_of"] = {}
    expect("child without modeled parent", wrong_parent)
    expect("actual joint crowding", lambda c, l: next(
        r for r in l["shared_occupancy"]["houses"] if r["place"] == WEST).update(people=27))
    def move_original(c, l):
        next(p for card in c.values() for p in card["persons"]
             if (p.get("dealt_by") or {}).get("ticket") != TICKET)["name"] = "changed"
    expect("old identity changed", move_original)
    programme_path = s.RECON / "1835_lodging_household_programme.json"
    original_programme = s.load(programme_path)
    import types
    def bad_units(label, mutate):
        programme = copy.deepcopy(original_programme)
        mutate(programme)
        mock = types.SimpleNamespace(**vars(s))
        mock.load = lambda path: programme if path == programme_path else s.load(path)
        try:
            household_units(mock, {"storage": 22})
        except SystemExit:
            return
        raise AssertionError("T-2023 unit guard failed: " + label)
    bad_units("duplicate unit member", lambda p: p["reconstructed_units"][1]["member_ids"].append(
        p["reconstructed_units"][0]["member_ids"][0]))
    bad_units("nonexistent sleeping member", lambda p: p["reconstructed_units"][0]["member_ids"].append("no_such_person"))
    bad_units("wrong roof division", lambda p: p["reconstructed_units"][0].update(roof_division="south"))
    bad_units("missing secondary boarding amendment", lambda p: p.update(secondary_boarding_uses=[]))
    bad_units("new individual as a family", lambda p: p["reconstructed_units"][0].update(
        member_ids=[p["reconstructed_units"][0]["member_ids"][0]], kind="shared_boarding_tenancy"))
    bad_units("known household loses a member", lambda p: p["known_receipts"][0]["member_ids"].pop())
    print("  ok    T-2023 ordered-room, frozen identities, modeled kin, joint capacity, single-night exception and real disjoint household-unit guards")
    return 0


def household_units(s, container_counts):
    """Verify actual disjoint household economies; no person/card-count shortcut."""
    programme = s.load(s.RECON / "1835_lodging_household_programme.json")
    import house_the_present_1835 as housing
    inputs = housing.read_inputs()
    cards = {hid: r["card"] for hid, r in inputs["cards"].items()}
    persons = {p["id"]: p for c in cards.values() for p in c.get("persons", [])}
    member_household = {p["id"]: hid for hid, c in cards.items() for p in c.get("persons", [])}
    held = s.load(s.RECON / "1835_held_head_dwellings.json")
    excluded_households = {r["household"] for r in held["counted"]}
    excluded_households.update(hid for hid, c in cards.items()
                               if c.get("source_pass") == "reconstructed_women_children")
    excluded = {p["id"] for hid in excluded_households for p in cards[hid]["persons"]}
    family_seats = {r["household"] for r in housing.load(housing.OUT)["seats"]
                    if r["rung"] in ("family", "dealt")}
    excluded_r = excluded | {p["id"] for hid in family_seats for p in cards[hid]["persons"]}
    joint = shared_occupancy(s, {})
    seen, counts, known_counts = set(), Counter(), Counter()
    units = programme["reconstructed_units"]
    known = programme["known_receipts"]
    if len(units) != 56 or len(known) != 20:
        raise SystemExit("FAIL T-2023 requires56 real R units and20 known-house receipts")
    secondary = {r["roof_id"] for r in programme["secondary_boarding_uses"]}
    for unit in units + known:
        ids, sid = set(unit["member_ids"]), unit["roof_id"]
        if not ids or len(ids) != len(unit["member_ids"]) or seen & ids:
            raise SystemExit("FAIL T-2023 household units empty or duplicate a member")
        if not ids <= joint.get(sid, set()):
            raise SystemExit("FAIL T-2023 household unit includes somebody not sleeping under its roof: " + unit["id"])
        if ids & (excluded_r if unit in units else excluded):
            raise SystemExit("FAIL T-2023 double-credits another stage's entire household")
        roof = inputs["roofs"][sid]
        div = roof["district"]
        if not div:
            div = next((r["district"] for r in s.load(s.RECON / "1835_existing_roof_reconciliation.json")["records"]
                        if r["structure_id"] == sid), None)
        if not div:
            # Brown's named roof is absent from the programme reconciliation;
            # retain the lodging writer's reviewed keeper/premises division.
            div = next(h["division"] for h in s.load(s.LEDGER)["houses"] if h["id"] == sid)
        if unit["roof_division"] != div or not unit["quota_cell"].endswith("/" + div):
            raise SystemExit("FAIL T-2023 uses a person civil division as its roof division")
        if unit in units:
            limit = 21 if "/boarding_house/" in unit["quota_cell"] else 35
            if len(ids) > limit:
                raise SystemExit("FAIL T-2023 shared economy exceeds original census lodging tail")
            if unit.get("kin_size_drawn") and len(unit.get("kin_member_ids", [])) > unit["kin_size_drawn"]:
                raise SystemExit("FAIL T-2023 enlarges a frozen kin-family draw")
            if len(ids) == 1:
                if (unit["kind"] != "existing_explicitly_drawn_solitary_reconstructed_household"
                        or ids != {"rc_dufresne_hyacinthe"}
                        or cards["hh_rc_dufresne_hyacinthe"]["household_owed"]["size_drawn"] != 1):
                    raise SystemExit("FAIL T-2023 a solitary source individual is not a modeled shared household")
            for pid in ids:
                parent = (persons[pid].get("kin_of") or {}).get("person")
                if parent and parent not in ids:
                    raise SystemExit("FAIL T-2023 splits an existing family between units")
            counts[unit["quota_cell"]] += 1
        else:
            if unit.get("needs_secondary_boarding_use_amendment") and sid not in secondary:
                raise SystemExit("FAIL T-2023 missing explicit secondary boarding classification")
            if not unit.get("dwelling_evidence"):
                raise SystemExit("FAIL T-2023 known receipt lacks official dwelling evidence")
            core = {p["id"] for p in cards[unit["household_id"]]["persons"]}
            if not core <= ids or ids - core != set(unit.get("unrelated_boarder_ids", [])):
                raise SystemExit("FAIL T-2023 known receipt loses its household or silently invents kin")
            known_counts[unit["quota_cell"]] += 1
        seen.update(ids)
    for row in programme["quota_arithmetic"]:
        key = row["quota_cell"]
        if counts[key] != row["reconstructed_units"] or known_counts[key] != row["known_candidates"]:
            raise SystemExit("FAIL T-2023 exact household receipts disagree with quota arithmetic")
        if counts[key] + known_counts[key] != row["target"]:
            raise SystemExit("FAIL T-2023 changes a lodging-household target")
    global_known = verify_known_receipts(s, programme, cards, excluded,
                                        {pid for u in units for pid in u["member_ids"]})
    return {"ticket": TICKET, "global_exclusive_known_receipts": global_known,
            "statement": "Actual disjoint reconstructed household economies/tenancies under existing roofs. An inn holds several. No new kinship is inferred among unrelated boarders.",
            "unit": "household economies, not container cards, individual source records or roofs",
            "programme": "data/reconstruction/1835_lodging_household_programme.json",
            "containers_written": sum(container_counts.values()),
            "houses_filled": len(units), "known_house_receipts": len(known),
            "distinct_members": len(seen), "double_credited_members": 0,
            "by_cell": dict(sorted(counts.items())),
            "known_by_cell": dict(sorted(known_counts.items()))}


def verify_known_receipts(s, programme, cards, excluded, reconstructed_members):
    crosswalk = s.load(s.RECON / "1835_known_household_receipts.json")
    index = s.load(s.ROOT / "data/residents/index.json")
    rulings = s.load(s.RECON / "1835_presence_rulings.json")
    ruled = {r["household_id"] for r in rulings["rulings"]
             if r.get("present_on_scene_date", {}).get("value") == "present"}
    eligible = {r["id"] for r in index["households"] if r.get("dwelling_evidence")
                and (r.get("present_on_scene_date") == "present" or r["id"] in ruled)
                and sum(r.get("grades", {}).get(g, 0) for g in ("attested", "inferred")) > 0}
    receipts = crosswalk["receipts"]
    if not {r["household_id"] for r in programme["known_receipts"]} <= eligible:
        raise SystemExit("FAIL T-2023 local known receipt is not an official known house")
    if len(receipts) != 165 or {r["household_id"] for r in receipts} != eligible:
        raise SystemExit("FAIL T-2023 global known-house crosswalk differs from official eligible pool")
    seen, counts, local = set(), Counter(), {r["household_id"]: r for r in programme["known_receipts"]}
    for row in receipts:
        ids = set(row["member_ids"])
        actual = {p["id"] for p in cards[row["household_id"]]["persons"]}
        extra = set(local.get(row["household_id"], {}).get("unrelated_boarder_ids", []))
        if ids != actual | extra or ids & (seen | excluded | reconstructed_members):
            raise SystemExit("FAIL T-2023 global known-house receipt duplicates a person or household-stage credit")
        if row["source_division"] in ("north", "south", "west", "fort") and row["source_division"] != row["assigned_quota_division"]:
            raise SystemExit("FAIL T-2023 moves a resolved known-house quota division")
        if row["household_id"] in local and row["quota_cell"] != local[row["household_id"]]["quota_cell"]:
            raise SystemExit("FAIL T-2023 global and local known-house receipts disagree")
        seen.update(ids)
        counts[row["quota_cell"]] += 1
    if any(counts[r["quota_cell"]] != r["after"] for r in crosswalk["known_cells"]):
        raise SystemExit("FAIL T-2023 global known receipts do not conserve every known cell")
    return len(receipts)
