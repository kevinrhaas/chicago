#!/usr/bin/env python3
"""The written ruling on the 1,094 remaining unasserted units (T-1298).

    python3 tools/spend_remainder_rulings.py             write the five ruling registers
    python3 tools/spend_remainder_rulings.py --check     they re-derive; nothing drifted
    python3 tools/spend_remainder_rulings.py --self-test the rules below, held over the
                                                         corpus they derive

WHY THIS EXISTS. T-1234 gave the research-spend ledger a place to write a ruling down:
`data/research/spend_rulings.json`, consulted only where a reading's own dispositions run
out, a named rule with a stated reason and a note on every single unit it closes. That
file is HAND-AUTHORED and holds 87 rulings; T-1296 wrote the first DERIVED register, for
1,572 land-sale rows, because typing 1,572 notes by hand would make a worse register --
the notes drift and nobody can prove a note matched the row it claims to rule.

T-1298 is the remainder of T-1236, and it is five corpora at once:

    residents        382  the reserved people of the pilot and passes 02-15 whose pass
                          finding names no exact structured resident field
    newspapers       378  the person, notice, event, shipping and price units of the
                          thirteen held issues that no card names
    church           272  the register entries outside the later-only and outside-Chicago
                          rulings already carried by the readings themselves
    books             61  the non-person readings -- ground, harbour, weather, price,
                          shipping, institution and household
    genealogytrails    1  one landscape reading

Each gets its own derived register beside its corpus, on the terms
`research_spend_ledger.ruling_registers` sets: the same statement floor, the same note
floor, the same coverage faults. Every note is built out of the unit's OWN committed
fields -- its file's preamble, its pass finding's summary, its issue date, its register
role, its `normalized` line -- so a reader can put the note beside the row and see that
it says what the row says.

WHAT THIS DOES NOT DO. Nothing here edits a resident, mints a person, moves a confidence,
invents a citation or re-adjudicates an identity. A hand-off is not a spend: it names the
OPEN ticket whose field genuinely owns the finding, and that ticket closing turns this
file red, which is the point. In particular this file does NOT decide the letter-list
question: T-0660 -> T-0691 is blocked on the owner and its outcome is not invented here.
A letter-list name is handed to T-1159, whose field is the roster of names the research
READ AND WITHHELD, with `letter-list-only` as a declared re-admission class -- recording
that a name was read and withheld is not ruling on whether its bearer lived here.

AND A SECOND CORPUS SINCE T-1509: the 100 `business` readings the ledger routes to
T-1468. T-1508 taught `research_spend_ledger` to reach the BUSINESS layer as a target
surface and 485 units landed there; these 100 did not, and they stood `unresolved` behind
a routing pointer with nothing said about any one of them. They fall in the newspapers
(77) and books (23) corpora -- the two registers this file already writes -- and
`ruling_registers` allows exactly one register per domain directory, so the tool that
owns the file is the tool that has to rule them. They get four answers, and the layer
decides which:

    49  the layer holds a record compiled from the reading, and names the claim ONLY at
        the record root where no tier stands -- handed to T-1514, which owns putting the
        tier on in tools/compile_businesses.py
    25  the layer compiled no record from the reading and it is in the window -- spent in
        aggregate, the way a price or a shipping reading is
    20  the reading's own describes_date is earlier than the scene -- refused
     6  the issue is printed after the scene date and no record was compiled -- later_only

The record OUTRANKS the date here, which is the order T-1508 set on this corpus: a record
carries its own tier and basis for what it read out of a post-scene printing, and that
judgement is the record's rather than this register's.

THE CORPUS IS DERIVED FROM THE CORPUS, not from the committed ledger: this tool asks
`research_spend_ledger.natural_disposition` -- the derivation that reads no ruling
register at all -- which units end unresolved and owned by T-1298, and which of T-1468's are
`business` readings, and rules exactly those. So writing the registers cannot change what the registers are asked to cover, and
`--check` re-derives the same answer from the same readings.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import research_spend_ledger as L  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TICKET = "T-1298"
# T-1509. THE BUSINESS REMAINDER IS THE SECOND CORPUS THIS TOOL OWNS. T-1508 taught the
# ledger to reach the business layer, and 485 units landed there; 100 did not, and they
# stood `unresolved` behind the routing pointer T-1468 with nothing said about any one
# of them. They live in the newspapers and books corpora -- the two registers this file
# already writes -- and `ruling_registers` allows exactly one register per domain
# directory, so the tool that owns the file is the tool that must rule them.
BUSINESS_TICKET = "T-1468"
BUSINESS_TIER_OWNER = "T-1514"
SCENE_DATE = "1835-07-01"
HAND_AUTHORED = ROOT / "data" / "research" / "spend_rulings.json"
DOMAINS = ("residents", "newspapers", "church", "books", "genealogytrails")

# The register roles that carry KIN -- the entry's own `cells.role`. A child, a parent, a
# groom, a bride or a decedent named beside a spouse is a family the source names, which
# is T-1170's field verbatim. A sponsor or a witness is NOT kin: standing at the font or
# signing the page names a person on a dated Chicago day and nothing about a household.
KIN_ROLES = {"child", "father", "mother", "groom", "bride", "spouse", "parent",
             "decedent", "subject"}
ATTENDANCE_ROLES = {"sponsor", "godfather", "godmother", "witness"}

# The column headings a Chicago paper prints over its family news.
FAMILY_COLUMN = re.compile(r"^\W{0,4}(MARRIED|Married|DIED|Died)\b")

# T-1172 closed on 2026-09-18 having re-admitted the roster, so by this file's own
# rule -- a hand-off names the OPEN ticket whose field owns the finding -- every
# hand-off that pointed at it moves on rather than pointing at finished work.
# T-1423, 2026-09-20: AND THE RENAMING ENDS HERE. The tail below used to grow a paragraph
# every time the named ticket closed. What it records now is that the renaming was never
# the answer, and the unit waits on a document.
HANDED_ON = (
    " T-1172 SPENT THE RE-ADMISSION (2026-09-18): the name is on the town at the "
    "reconstructed tier, under its own read name, in "
    "data/reconstruction/1835_readmissions.json, with its own `withdrawn_if` clause -- and "
    "that settles nothing about the evidence, which is why this unit stays `unresolved`. "
    "The pointer was then renamed to T-1179 and to T-1394 as each closed, and T-1394's "
    "three children DID their work -- the rebuild order a fixed point, a liberty entry per "
    "stage, the minting stage on the People view's filter -- while leaving this unit "
    "exactly where it was: what they reconciled is the LAYER, and what is open is the "
    "EVIDENCE. No ticket can close that, so this unit names none. What would reopen it is "
    "stated in this rule's `awaiting_evidence`.")

TWO_HAND_OFF_SHAPES = (
    "A hand-off is not a spend, and it has two honest shapes (T-1423): a unit waiting on WORK names the open ticket whose field owns the finding, and that ticket closing turns this file red, which is the point; a unit waiting on EVIDENCE names no ticket at all and states `awaiting_evidence` -- the document that would reopen it -- because no ticket can produce a source nobody holds, and a pointer renamed at every closure records nothing but the closures.")

RULES = {
    # ---- residents ---------------------------------------------------------------
    "the_manifest_is_a_reservation_and_not_a_reading": {
        "disposition": "refused",
        "statement": (
            "The unit is a row of a research COHORT MANIFEST, and the manifest says so "
            "itself in its own preamble: it is a sampling frame that reserves a person "
            "for a pass and an identity lock that fixes which person was reserved. It "
            "carries the person_id, the starting grade and the letter-list returns the "
            "residents layer ALREADY holds, and it states no new fact about anybody. The "
            "pilot committed no findings ledger, so no reading is attached to this row to "
            "spend. What is refused here is the claim that the ROW carries an 1835 fact; "
            "nothing is refused about the person, whose card is untouched and whose "
            "evidence is exactly what it was."),
    },
    "the_pass_named_a_candidate_and_did_not_assert_it": {
        "disposition": "refused",
        "statement": (
            "The completed pass reviewed this reserved person and returned a CANDIDATE "
            "IDENTITY it explicitly did not assert -- the finding's own candidate rows "
            "carry `asserted: false` and name the conflict that stopped them. The "
            "research already refused the join; the ledger now carries that refusal "
            "instead of leaving the row open. Closing it by eye would be manufacturing "
            "the identity the pass declined to make, and this ruling does not touch the "
            "candidate, the card, or the grade either of them carries."),
    },
    "corroboration_confirms_and_moves_nothing": {
        "disposition": "refused",
        "statement": (
            "The completed pass returned `corroborated`: an independent source agrees "
            "with what the card already says, and the finding's own words are that the "
            "person was confirmed, NOT MOVED. Under the evidence ladder ratified "
            "2026-09-03 corroboration corroborates; it does not promote and it names no "
            "new structured field, so there is nothing here to write. The agreement is a "
            "closed decision and the sources stand in the finding where the pass put "
            "them."),
    },
    "the_enrichment_names_a_birth_or_age_no_field_carries": {
        "disposition": "unresolved",
        "ticket": "T-1315",
        "statement": (
            "The completed pass returned `corroborated_enrichment`: a real, sourced fact about a "
            "person this town holds -- a trade, an address, an origin, a kinship, a date -- that "
            "extends the card and that no exact source-bearing structured field on that card "
            "carries today. It is not refused, because it is true research; it is not written here, "
            "because writing one attribute at a time, out of one pass and without the other sources "
            "beside it, is how a layer acquires facts it cannot defend. T-1301 read all 98 of them "
            "one at a time and handed each to the OPEN ticket whose acceptance owns the kind of "
            "fact it names; this unit's own note says which field that is. This one names a BIRTH "
            "DATE, a birth year or an age. It was routed to T-1168, the pass that fills sex and "
            "age for every attested and inferred person with its tier and its reason; that "
            "ticket was split into T-1303 (the tiers the evidence pays for) and T-1304 (the "
            "tier the model draws), and both are done, so `birth_year` and `age_band` both "
            "exist on the card and there is at last a field for these three to go in. "
            "T-1315 owns spending them, and a hand-off must name LIVE work rather than a "
            "spent parent."),
    },
    "the_enrichment_is_written_onto_the_card_it_names": {
        "disposition": "asserted",
        "statement": (
            "The completed pass returned `corroborated_enrichment` naming an arrival year or "
            "an origin, and T-1330 WROTE IT ONTO THE CARD -- over a value the arrival stage "
            "had drawn from a distribution, or over a year this project's own note called a "
            "guess. tools/spend_enrichment_arrivals.py holds the adjudication, writes the "
            "block and re-derives it under --check; the block is `inferred`, cites the volume "
            "the finding names, says which person it is about, and carries no "
            "`written_by_stage` mark, which is how reconstruct_residents_1835.py's "
            "`writable()` yields the field to it. This ruling exists because the ledger's own "
            "assertion test cannot see a spend of this kind: it closes a unit only where the "
            "card cites a source the READING already carried, and the whole value of these "
            "nine is that they bring a volume it did not. The `wrote` list on each row names "
            "the file and the field, and tools/research_spend_ledger.py re-reads every one of "
            "them -- an assertion a register cannot show is a fault, not an assertion."),
    },
    "the_enrichment_dates_an_appearance_the_card_already_carries": {
        "disposition": "refused",
        "statement": (
            "The completed pass returned `corroborated_enrichment` naming an arrival, an "
            "origin or a dated appearance, and T-1330 read it against the card it names: the "
            "card ALREADY carries that date or that place, from a source of its own, at equal "
            "or better precision. Under the evidence ladder ratified 2026-09-03 corroboration "
            "corroborates; it does not promote, and a second volume agreeing that a man "
            "Andreas puts at Chicago in 1833 was at Chicago in 1833 names no field to fill. "
            "This is a finished answer rather than a deferral, and the finer detail some of "
            "these carry -- a month inside a year the card states, a roster naming inside a "
            "residence the card states -- is recorded in this unit's own note rather than "
            "written over a reading that owns the field. The nine of the thirty that DID "
            "retire a drawn or guessed value are not here: they are asserted on their cards "
            "by tools/spend_enrichment_arrivals.py and the ledger closes them by reading the "
            "card, which is why a ruling on one of them would be a fault."),
    },
    "the_enrichment_names_a_departure_from_chicago_no_field_carries": {
        "disposition": "refused",
        # T-1144 SPLIT ON 2026-09-18 AND THIS LINE WAS LEFT POINTING AT THE PARENT.
        # The split (#1471) found the one deferral it was looking for — the
        # `identity_open_one_letter_apart` ruling in data/research/spend_rulings.json —
        # and repointed it to T-1334. It did not find this one, which had been added
        # hours earlier by T-1330's arrival-and-origin pass, so `dev` went red on the
        # ledger ratchet and every branch that merged dev inherited the strand.
        #
        # #1489 MOVED IT TO T-1333 AND THAT WAS ONLY HALF RIGHT. T-1333 was live, so
        # the ledger cleared; but T-1333's acceptances are a rebuild and measured deltas,
        # and none of them owns spending a departure onto a presence date. T-1334 is the
        # identity rule, so it does not either. T-1172 is not the owner: its R1 leg is
        # scoped to the 893 UNCERTAIN presences, and these six are not all uncertain —
        # caldwell_billy is attested and present. The departure question is an UNBANKED
        # REMAINDER of T-1144's split, and pointing it at whichever child happened to be
        # open would have failed again the moment that child closed, which is precisely
        # what T-1333's own closing run hit.
        #
        # T-1354 WAS FILED FOR IT AND HAS NOW SPENT IT, which is why this line is no
        # longer a hand-off. Six rulings, each reading the removal BESIDE the other
        # sources on the card rather than out of the one volume it came in, stand in
        # data/research/residents/departure_rulings.json and re-derive under
        # tools/spend_departure_rulings.py --check. This register says `refused`
        # because none of the six asks anything further of the layer — not because a
        # departure is worthless evidence. It is the disposition the sibling rule
        # `the_enrichment_dates_an_appearance_the_card_already_carries` already uses
        # for a finished answer, and the one spend among the six is stated here rather
        # than left for a reader to find.
        "statement": (
            "The completed pass returned `corroborated_enrichment` naming a DEPARTURE from "
            "Chicago -- a removal, a migration to another town, a prospecting journey that "
            "ended somewhere else -- for a person this town holds a card for. T-1330 read all "
            "thirty arrival-and-origin enrichments one at a time and these six name a going "
            "rather than a coming. No field on a resident card carries a departure: the only "
            "thing a removal bears on is `present_on_scene_date`. T-1354 SPENT ALL SIX, one "
            "at a time, each read beside the other sources on its card -- because a removal "
            "read alone, out of the single late compiler that carries it, is how a layer "
            "loses a resident it had evidence for. FIVE DO NOT REACH THE SCENE DATE, and "
            "they miss in three different ways: Caldwell's removal and Jones's Manitowoc "
            "settlement are dated AFTER 1 July 1835, Sweet's removal to Milwaukee is dated "
            "only to the year the scene falls in and stands on both sides of the day, and "
            "Pugsley's return to Paw Paw and Cleland's move to Niles carry no departure date "
            "at all -- Pugsley's volume in fact dates a journey TO Chicago in the month of "
            "the card's own bound. THE SIXTH REACHES IT AND WAS ALREADY WRITTEN: Porthier "
            "left with Horace Chase on 27 February 1835 and reached Milwaukee on 23 March, "
            "and T-0478 had already moved his presence to `absent` at `attested` citing this "
            "volume. So no presence moves under this rule, no grade moves and no card is "
            "retired, which is the answer and not a deferral. The six rulings, what each was "
            "read beside, and the presence each stands on are in "
            "data/research/residents/departure_rulings.json, re-derived by "
            "tools/spend_departure_rulings.py -- whose --check re-reads every one of the six "
            "cards, so a presence that moves out from under one of these rulings turns the "
            "gate red."),
    },
    "the_enrichment_names_kin_no_field_carries": {
        "disposition": "unresolved",
        # WAS T-1170 UNTIL T-1313 CLOSED ON 2026-09-18. That ticket was SPLIT into
        # T-1312 (read and rule the named relatives), T-1313 (seat them) and T-1314
        # (reconstruct the ones only counted), and with the last of the three done the
        # parent is spent work — a unit deferred to it is stranded exactly as it would
        # be behind a closed ticket (T-1237). The three children do not cover these
        # units: they answered the relatives who are NOBODY in this dataset, and each
        # of these names a relative who is HERSELF A HELD RESIDENT — Josette as Jean
        # Baptiste Beaubien's wife, Catherine Chevalier as Robinson's. That is a tie
        # between two cards rather than a person to seat, which was T-1320.
        #
        # AND IT MOVED AGAIN TO T-1335 ON 2026-09-18, for the same reason one step out.
        # T-1320 is scoped to the BOOK corpus by its own title — the ties whose relative
        # is ALSO a held resident, and the book-corpus relatives who are nobody here —
        # and the retarget above pointed ALL FOUR domains at it, which it never covered.
        # Its pass (tools/spend_book_kin.py, PR #1464) did the book job and the ticket
        # closed, stranding 168 units: 147 church, 12 newspapers, 7 residents, and 2 book
        # units its own pass left unruled. T-1335 is the family pass proper and owns all
        # of them. This is the T-1237 rule reached from the other side — not a split
        # parent going quiet, but a handoff aimed at a ticket narrower than the line
        # pointing at it.
        "ticket": "T-1335",
        "statement": (
            "The completed pass returned `corroborated_enrichment`: a real, sourced fact about a "
            "person this town holds -- a trade, an address, an origin, a kinship, a date -- that "
            "extends the card and that no exact source-bearing structured field on that card "
            "carries today. It is not refused, because it is true research; it is not written here, "
            "because writing one attribute at a time, out of one pass and without the other sources "
            "beside it, is how a layer acquires facts it cannot defend. T-1301 read all 98 of them "
            "one at a time and handed each to the OPEN ticket whose acceptance owns the kind of "
            "fact it names; this unit's own note says which field that is. This one names KIN -- a "
            "spouse, a marriage, a child, a parent or a household the source distinguishes -- and "
            "T-1170 is the pass that gives the attested and inferred heads the families the sources "
            "name."
            " THE HANDOFF WAS T-1170, THEN T-1320, AND IS T-1335 SINCE 2026-09-18: T-1170's split is spent, and T-1320 is scoped to the BOOK corpus by its own title, so it never covered this domain. T-1335 is the family pass proper."),
    },
    "the_enrichment_names_a_civic_church_or_school_post_no_field_carries": {
        "disposition": "unresolved",
        "ticket": "T-1189",
        "statement": (
            "The completed pass returned `corroborated_enrichment`: a real, sourced fact about a "
            "person this town holds -- a trade, an address, an origin, a kinship, a date -- that "
            "extends the card and that no exact source-bearing structured field on that card "
            "carries today. It is not refused, because it is true research; it is not written here, "
            "because writing one attribute at a time, out of one pass and without the other sources "
            "beside it, is how a layer acquires facts it cannot defend. T-1301 read all 98 of them "
            "one at a time and handed each to the OPEN ticket whose acceptance owns the kind of "
            "fact it names; this unit's own note says which field that is. This one names a CIVIC, "
            "CHURCH, SCHOOL or GARRISON POST -- a county office, a town trusteeship, a coronership, "
            "a ministry, a church membership, a school kept or an officer's clerkship."
            " IT WAS ROUTED TO T-1188, which completes those establishments with their staff. That "
            "ticket split into T-1410 (the post office, the land office and the county rooms) and "
            "T-1411, which split again into T-1421 (the churches) and T-1422 (the schools and the "
            "press), and all four are now done -- so the establishments EXIST and a unit cannot "
            "defer to spent work. The hand-off is T-1189 since 2026-09-20: what these twelve "
            "findings name is a POST, a person at one of those establishments, and T-1189 is the "
            "open ticket that puts real persons into them -- every working person a workplace and "
            "every workplace its people. The three closed children raised the houses and named the "
            "officers their own sources printed; they did not walk the resident layer's enrichments "
            "against them, and that walk is what a post found in a volume still needs."),
    },
    "the_enrichment_names_a_landholding_no_field_carries": {
        "disposition": "unresolved",
        "ticket": "T-1198",
        "statement": (
            "The completed pass returned `corroborated_enrichment`: a real, sourced fact about a "
            "person this town holds -- a trade, an address, an origin, a kinship, a date -- that "
            "extends the card and that no exact source-bearing structured field on that card "
            "carries today. It is not refused, because it is true research; it is not written here, "
            "because writing one attribute at a time, out of one pass and without the other sources "
            "beside it, is how a layer acquires facts it cannot defend. T-1301 read all 98 of them "
            "one at a time and handed each to the OPEN ticket whose acceptance owns the kind of "
            "fact it names; this unit's own note says which field that is. This one names LAND "
            "rather than a trade or a roof -- a purchase, an original-town lot, a holding -- and "
            "T-1198 is the pass that seats every attested and inferred household and business on "
            "the ground its evidence allows, plural and dated, with no fabricated coordinates."),
    },
    "the_later_volume_enriches_a_biography_and_names_no_1835_field": {
        "disposition": "later_only",
        "statement": (
            "The completed pass returned `corroborated_enrichment` and the source it read is a "
            "volume or a return PRINTED AFTER 1 July 1835 -- a later directory, an old-settler "
            "roll, a death notice, an 1837 election return -- which confirms and dates a person the "
            "town already holds and, in the pass's own words, backfills no in-window value: no "
            "occupation, no roof, no 1835 attestation. Under the ladder ratified 2026-09-03 such a "
            "source may corroborate, enrich and date, and may never assert an 1835 fact. That is "
            "`later_only`, which is an answer and not a deferral: handing it to an attribute-fill "
            "ticket whose acceptance is about 1835 values would name a field the reading cannot "
            "fill. The reading stands as committed biography where the pass put it; no card is "
            "edited and no confidence moves."),
    },
    # ---- the ladder --------------------------------------------------------------
    "the_issue_is_printed_after_the_scene_date": {
        "disposition": "later_only",
        "statement": (
            "The issue this unit was read from was PRINTED after 1 July 1835, so under "
            "T-0513's ladder it may corroborate, enrich and date, and it may not assert "
            "an 1835 fact. The unit itself carries no `describes_date`, which is why the "
            "ledger's year test never reached it: the date that bounds it is the issue's "
            "own masthead date, and that is what is applied here."),
    },
    "the_roll_is_beyond_the_reading_window": {
        "disposition": "later_only",
        "statement": (
            "The entry's own `beyond_ticket_window` field is true: it is a row of a "
            "congregation roll that begins after the scene date -- the Second "
            "Presbyterian Church of Chicago was formed in 1842, seven years on -- and the "
            "row prints no date within the window at all. Under the ladder it may "
            "corroborate and date a person the town already holds, and it may never "
            "assert that person into 1835."),
    },
    "the_reading_is_earlier_than_the_scene_and_does_not_reach_it": {
        "disposition": "refused",
        "statement": (
            "The reading's own `describes_date` is earlier than 1835 and its content does "
            "not reach the scene date: an event, a notice, an appearance, a civic act or "
            "a household described in 1812, 1818, 1821, 1827, 1830 or 1833 is a fact "
            "about that year. Under the ladder ratified 2026-09-03 a source LATER than "
            "the scene date corroborates and never promotes, and an EARLIER source does "
            "not promote either -- a man, a society or a house at Chicago in 1827 is not "
            "thereby at Chicago in 1835. The reading stands as committed chronology; no "
            "card is edited, nothing is minted, and the ground, harbour and structure "
            "layers keep it exactly as they have it."),
    },
    # ---- readings about the town rather than about a record ----------------------
    "a_ground_reading_describes_the_site_not_a_record": {
        "disposition": "aggregate_only",
        "statement": (
            "The unit is a LANDSCAPE reading: it describes the site -- its timber, its "
            "prairie, its streams, its shore, the naming of a river -- and names no "
            "person, household, business or structure record for the person ledger to "
            "write. That is the answer, not a deferral: a ground reading is committed "
            "chronology for the terrain and shore work, which cites it where it bears, "
            "and the spend ledger's honest disposition for it is that it is good in "
            "AGGREGATE and attaches to no record. This ruling neither cites it for the "
            "ground tickets nor invents a terrain fact from it."),
    },
    "the_market_and_the_port_in_aggregate": {
        "disposition": "aggregate_only",
        "statement": (
            "The unit is a PRICE or a SHIPPING reading -- a marine journal's arrivals and "
            "clearances, a wholesale list by the cask, a freight or a rate. This is the "
            "question T-1298 was asked to answer: what a reading of the harbour or the "
            "price of flour does for the 1835 scene when no person unit owns it. It sizes "
            "the town's trade -- what came in, in what bottoms, and what it cost -- and "
            "it names no person, household, business or structure record, so the person "
            "ledger has nothing to write from it. It is true, it is spent in aggregate, "
            "and it is closed: the scene reads it as texture and the vessels and stocks "
            "it counts are not thereby minted as records."),
    },
    "a_town_reading_with_no_record_to_write": {
        "disposition": "aggregate_only",
        "statement": (
            "The unit is an in-window reading ABOUT THE TOWN rather than about a person: "
            "a society, a public event, a civic act, a weather or an institution note, "
            "dated 1835 or undated, naming no record this layer holds. It is not refused "
            "-- it is true and it is in the window -- and it is not handed on, because "
            "there is no structured record for it to land on. It is spent in aggregate as "
            "scene chronology, which is a finished answer."),
    },
    "a_trade_reading_the_business_layer_holds_no_record_for": {
        "disposition": "aggregate_only",
        "statement": (
            "The unit is a BUSINESS reading -- a trade, a stock, a firm's own "
            "advertisement, a historian's paragraph about the trade of the place -- "
            "whose claim NO record of data/businesses/ names in its `claim_ids`. The "
            "layer is the compiled answer to this corpus (T-1310 built it out of these "
            "very readings) and it did not compile a record from this one, so there is no "
            "business record for the ledger to land it on and inventing one off the "
            "reading is the move this project refuses everywhere else. It is in the "
            "window and it is true, so it is not refused: it sizes the town's trade the "
            "way the price and shipping readings do, and it is spent in aggregate. "
            "Nothing here mints a firm, edits a business record or moves a tier."),
    },
    "the_column_names_nobody": {
        "disposition": "aggregate_only",
        "statement": (
            "The unit is a notice or an editorial paragraph whose own `entities` array is "
            "EMPTY -- the reading looked for the people in it and recorded that it names "
            "none. A paragraph that names nobody cannot assert a person fact and cannot "
            "be handed to a person pass. Its content is the town's public print in "
            "aggregate -- what the paper carried, and when -- and that is what it is "
            "spent as."),
    },
    # ---- hand-offs ---------------------------------------------------------------
    "the_compiled_record_names_this_claim_and_tiers_no_field_to_it": {
        "disposition": "unresolved",
        "ticket": "T-1514",
        "statement": (
            "A compiled business record DOES name this claim -- and only at its root, in "
            "`claim_ids`, beside a root `sources` list that carries no tier. The ledger "
            "reaches the business layer on a block that carries a tier AND cites a source "
            "(T-1508), and on these records there is no such block: `proprietors` and "
            "`partners` are empty because the advertisement is anonymous, and `locations` "
            "and `dates` are `inferred` from the placement policy and cite nothing. So the "
            "reading compiled a whole record and no field of that record is attested from "
            "it. This is a fault in the LAYER and not in the reading, and it is not closed "
            "by calling the root a tier: that would be minting a confidence the generator "
            "never derived. T-1514 owns putting the tier on in "
            "tools/compile_businesses.py, where the layer re-derives; the day it does, the "
            "ledger asserts these units with no ruling at all and these rows go red, which "
            "is what a hand-off closing is supposed to look like."),
    },
    "the_letter_list_name_belongs_to_the_borderline_roster": {
        "disposition": "unresolved",
        # T-1159 CLOSES WITH THE ROSTER IT BUILDS, so a hand-off cannot name it: this
        # register's own doc asks a hand-off to name the OPEN ticket whose field owns the
        # finding, and a unit deferred to finished work fails the ledger's invariant
        # outright. T-1159 moved its 40 land-sale purchaser hand-offs to T-1172 for exactly
        # this reason and missed this one; it is moved here on the same rule.
        #
        # AND A SPLIT CLOSES A TICKET TOO (2026-09-19). T-1179 was split into T-1392,
        # T-1393 and T-1394, which leaves `state: split` -- not an open state -- so
        # research_spend_ledger.py's invariant fired on five units at once:
        #
        #   FAIL: ... unresolved ticket 'T-1179' is missing or not open
        #
        # That is not cosmetic. The failure is inside `rederive.mjs --run`, which
        # .github/steward/pr-lap.sh runs on every lap, so the lap stopped pushing
        # ("the derived-layer rebuild failed -- left alone", pushed=0 left-alone=2) and
        # three PRs sat dirty with no gate able to run on them. A hand-off pointing at a
        # split ticket blocks the whole queue, not just this file.
        #
        # AND THE HEIR HAD AN HEIR, WHICH IS WHEN TO STOP (T-1423, 2026-09-20). T-1394's
        # children T-1398, T-1399 and T-1400 all closed, having done real work: the rebuild
        # order is a fixed point, one liberty entry per stage is written, the minting stage
        # is on the People view's filter. These 69 units were not one document nearer
        # settled for any of it, because what those tickets reconciled is the LAYER and what
        # is open is the EVIDENCE. Renaming the pointer a fifth time would buy the same
        # nothing at the same cost -- a red gate inside `rederive.mjs --run` the next time
        # the named ticket closes. So this rule names NO ticket. It states
        # `awaiting_evidence`: the document that would reopen the unit, gated by
        # research_spend_ledger.py, which takes exactly one owner and refuses a wait that
        # says nothing. The unit is still `unresolved` -- it just no longer claims a ticket
        # is on it.
        "awaiting_evidence": (
            "A source beyond the post-office list that places this name at Chicago inside "
            "the scene window -- a poll or tax roll, a deed, a church register line, a "
            "directory entry, an old-settler recollection naming the person in the town."),
        "statement": (
            "The unit's own `letter_list_only` field is true: the name's whole evidence is "
            "that a letter waited for it at the Chicago post office. Whether a letter-list "
            "name is a resident is the question of T-0660, and the owner RULED IT on "
            "2026-09-18, option (c): refusals 7 and 8 are mint-time rules that do not "
            "un-mint a standing record, nothing is retired, and the pass SAYS a collision "
            "rather than acting on one. That ruling settles what the letter list may DO; it "
            "decides no individual residency, and this unit is an individual. What is ruled "
            "here is the only "
            "thing that can be ruled without it: the name was read and it is withheld from "
            "1835, and the borderline roster is exactly that -- every name the research "
            "read and withheld, with its source, its reason and its re-admission class, of "
            "which `letter-list-only` is one the ticket names. Handing the name to the "
            "roster records the withholding; it does not decide the residency. The hand-off "
            "named T-1172, the ticket that re-admits the roster's single-source names, "
            "because T-1159 closes with the roster it builds." + HANDED_ON),
    },
    "the_family_column_names_kin": {
        "disposition": "unresolved",
        # WAS T-1170 UNTIL T-1313 CLOSED ON 2026-09-18. That ticket was SPLIT into
        # T-1312 (read and rule the named relatives), T-1313 (seat them) and T-1314
        # (reconstruct the ones only counted), and with the last of the three done the
        # parent is spent work — a unit deferred to it is stranded exactly as it would
        # be behind a closed ticket (T-1237). The three children do not cover these
        # units: they answered the relatives who are NOBODY in this dataset, and each
        # of these names a relative who is HERSELF A HELD RESIDENT — Josette as Jean
        # Baptiste Beaubien's wife, Catherine Chevalier as Robinson's. That is a tie
        # between two cards rather than a person to seat, which was T-1320.
        #
        # AND IT MOVED AGAIN TO T-1335 ON 2026-09-18, for the same reason one step out.
        # T-1320 is scoped to the BOOK corpus by its own title — the ties whose relative
        # is ALSO a held resident, and the book-corpus relatives who are nobody here —
        # and the retarget above pointed ALL FOUR domains at it, which it never covered.
        # Its pass (tools/spend_book_kin.py, PR #1464) did the book job and the ticket
        # closed, stranding 168 units: 147 church, 12 newspapers, 7 residents, and 2 book
        # units its own pass left unruled. T-1335 is the family pass proper and owns all
        # of them. This is the T-1237 rule reached from the other side — not a split
        # parent going quiet, but a handoff aimed at a ticket narrower than the line
        # pointing at it.
        "ticket": "T-1335",
        "statement": (
            "The unit is the paper's own MARRIED or DIED column, printed under that "
            "heading: it names a bride and a groom, or a decedent and the survivor they "
            "are named by, and the magistrate or minister who officiated. A marriage names "
            "a spouse and creates nobody; T-1170 gives the attested and inferred heads the "
            "families the sources name, from exactly these ruled kin ties. No household "
            "member is minted here and no kin tie is written here."
            " THE HANDOFF WAS T-1170, THEN T-1320, AND IS T-1335 SINCE 2026-09-18: T-1170's split is spent, and T-1320 is scoped to the BOOK corpus by its own title, so it never covered this domain. T-1335 is the family pass proper."),
    },
    "the_register_entry_names_kin": {
        "disposition": "unresolved",
        # WAS T-1170 UNTIL T-1313 CLOSED ON 2026-09-18. That ticket was SPLIT into
        # T-1312 (read and rule the named relatives), T-1313 (seat them) and T-1314
        # (reconstruct the ones only counted), and with the last of the three done the
        # parent is spent work — a unit deferred to it is stranded exactly as it would
        # be behind a closed ticket (T-1237). The three children do not cover these
        # units: they answered the relatives who are NOBODY in this dataset, and each
        # of these names a relative who is HERSELF A HELD RESIDENT — Josette as Jean
        # Baptiste Beaubien's wife, Catherine Chevalier as Robinson's. That is a tie
        # between two cards rather than a person to seat, which was T-1320.
        #
        # AND IT MOVED AGAIN TO T-1335 ON 2026-09-18, for the same reason one step out.
        # T-1320 is scoped to the BOOK corpus by its own title — the ties whose relative
        # is ALSO a held resident, and the book-corpus relatives who are nobody here —
        # and the retarget above pointed ALL FOUR domains at it, which it never covered.
        # Its pass (tools/spend_book_kin.py, PR #1464) did the book job and the ticket
        # closed, stranding 168 units: 147 church, 12 newspapers, 7 residents, and 2 book
        # units its own pass left unruled. T-1335 is the family pass proper and owns all
        # of them. This is the T-1237 rule reached from the other side — not a split
        # parent going quiet, but a handoff aimed at a ticket narrower than the line
        # pointing at it.
        "ticket": "T-1335",
        "statement": (
            "The entry's own `cells.role` puts this person in the KIN of a dated "
            "sacrament at Chicago -- the child, the father, the mother, the groom, the "
            "bride, the spouse or the decedent of a baptism, a marriage or a death. "
            "T-1170's field is the spouses, children, kin and dependants the baptism and "
            "marriage registers name. The tie is handed on whole; nobody is minted, no "
            "household is edited, and the entry's `confidence` is untouched."
            " THE HANDOFF WAS T-1170, THEN T-1320, AND IS T-1335 SINCE 2026-09-18: T-1170's split is spent, and T-1320 is scoped to the BOOK corpus by its own title, so it never covered this domain. T-1335 is the family pass proper."),
    },
    # ---- T-1343: THE PRESS APPEARANCES THE REGISTER COULD NOT IDENTIFY ---------------
    #
    # `a_dated_appearance_bounds_a_presence` STOOD HERE AND HANDED 147 PRESS UNITS ON, for
    # the fourth time, through T-1169, T-1318, T-1329, T-1338 and T-1343. It is gone,
    # because the hand-off has been answered rather than moved: T-1342 made a press claim
    # NAMEABLE -- the ledger key is the issue file's stem and the claim id joined by `#` --
    # and T-1343 spent every unit of this corpus that reaches a card.
    # tools/spend_press_bounds.py writes them as `persons[].dated_bounds[]`, 225 bounds on
    # 148 cards off 111 of the 147 units, so those units close `asserted` and never reach a
    # register again (`mine()` drops them, and `research_spend_ledger.ruling_coverage_faults`
    # would fail a ruling on one).
    #
    # The other 36 are the point of these two rules, and their ground is one committed
    # adjudication read and never re-made: `data/research/newspapers/register_1835.json`
    # says, of every person the press names, whether the residents layer HOLDS that person.
    # Where it does not, the refusal is about the spend and not about the person -- there is
    # no card to write on -- and each rule says what would reopen it. A unit whose register
    # row says `enrich` does not fall here at all: `press_appearance_rule` raises rather
    # than ruling it, because a unit with a card waiting for it is a unit that pass owes a
    # bound, and mapping it onto the nearest refusal is how a statement stops being true of
    # the units under it.
    "the_press_name_is_a_person_the_town_does_not_hold": {
        "disposition": "refused",
        "statement": (
            "The claim puts a named person in the town's print on a dated day, and the "
            "committed newspapers-to-residents register -- "
            "data/research/newspapers/register_1835.json, derived from the gazetteer and "
            "the committed town by tools/compile_register.py -- says of every person it "
            "names here that THIS LAYER HOLDS NO CARD FOR THEM: the register's action is "
            "`new_resident`, which is a person to be minted and not a person to be written "
            "on. There is nothing to spend because there is nothing to spend it onto. The "
            "refusal is about the SPEND and not about the name: the register's row stands, "
            "the reading is not withdrawn, and nothing here decides whether the person "
            "lived in the town. WHAT REOPENS IT is the mint: the day this layer holds a "
            "card for that name the register re-derives to `enrich`, this unit leaves the "
            "register, and tools/spend_press_bounds.py writes the bound. Nothing here "
            "mints, regrades or reopens."),
    },
    "the_press_name_replaces_an_invented_card": {
        "disposition": "refused",
        "statement": (
            "The claim puts a named person in the town's print on a dated day, and the "
            "committed newspapers-to-residents register says the printed name REPLACES AN "
            "INVENTED PERSON: its action is `replace_invented`, which names a card this "
            "project composed rather than read, and the substitution has not been made. A "
            "bound written onto that card would rest a dated reading on a person no source "
            "names, and writing it onto the printed name instead would BE the substitution "
            "-- a change to the residents layer, which is not a spend and is not this "
            "pass's to make. WHAT REOPENS IT is the substitution: once it lands the "
            "register re-derives to `enrich` and the bound is written. Nothing here mints, "
            "regrades, substitutes or reopens."),
    },
    # ---- T-1337: THE REGISTER APPEARANCES THE CROSSWALKS DID NOT IDENTIFY ------------
    #
    # 95 register units reached the rule above as one undifferentiated hand-off, and 13 of
    # them had an identification standing in
    # `data/research/church/st_marys_baptisms_crosswalk.json` the whole time. T-1337 wrote
    # those 13 onto their cards, so they close `asserted` and never reach a register again
    # (`mine()` drops them, and `research_spend_ledger.ruling_coverage_faults` would fail a
    # ruling on one).
    #
    # The other 82 are the point of these four rules. The ticket's own instruction was
    # that where an identification CANNOT be made the answer is a refusal in writing and
    # not a fourth deferral -- and in every one of the 82 cases the refusal has already
    # been made, by name, in the crosswalk that looked. So each rule below states one
    # crosswalk outcome and the per-unit note carries that crosswalk's own words. Four
    # rules and not one, because the four grounds are genuinely different and a single
    # statement would have to be vague enough to be true of all of them -- the same
    # argument T-1301 made when it turned one enrichment rule into seven.
    #
    # NOTHING HERE MINTS, REGRADES OR REOPENS. A refusal is a complete answer, and each
    # rule says what would reopen it.
    "the_register_appearance_names_nobody_this_town_holds": {
        "disposition": "refused",
        "statement": (
            "The crosswalk looked for this adult in the residents layer and found no "
            "candidate at all -- not a surname, not a variant. 85 of the 111 distinct "
            "adults St Mary's names in its Chicago entries reach no surname in the town's "
            "households, and this is one of them. The three readings that stay open are "
            "the ones the crosswalk itself states: the person had gone by 1835, or was "
            "never of the town, or is somebody the reconstruction has not found. On all "
            "three the appearance asserts no 1835 fact, mints nobody and edits no card, "
            "and what it spends into the town is NOTHING. That is a complete answer and "
            "not a deferral; the reading stays where it is for any later evidence to "
            "reach, and a surname arriving in the residents layer is what would reopen "
            "it."),
    },
    "the_register_appearance_identity_was_refused_in_the_crosswalk": {
        "disposition": "refused",
        "statement": (
            "The crosswalk has already refused this row by name: the register shares only "
            "a surname with the town person or persons it was set beside, or the page "
            "prints no forename at all to separate them. A surname alone separates nobody "
            "in a town of families -- this project's standing rule is that a surname-only "
            "join is always a refusal -- and a refusal written down is not made weaker by "
            "the ledger carrying it. The refusal was recorded so the next sweep would not "
            "make the same match again, and it is that record the ledger now reads instead "
            "of reading the row as work nobody has looked at. A second attribute agreeing "
            "is what would reopen it."),
    },
    "the_register_appearance_identity_is_a_candidate_and_not_a_merge": {
        "disposition": "refused",
        "statement": (
            "The crosswalk declares this row a CANDIDATE and not a match: a surname folds "
            "equal and the forenames agree initial for initial, which its own rule says is "
            "a candidate because a merge needs a second attribute to agree as well. A "
            "candidate is a rival still standing, and a bound written off one would print "
            "an undecided identity as a decided one -- which is why T-1337 wrote nothing "
            "off St Cyr's pages, where the crosswalk proposes one merge in 531 entries and "
            "makes none. The row is refused as a person unit; the candidate stands where it "
            "is, and a second agreeing attribute is what would reopen it."),
    },
    "the_register_reading_is_about_the_town_and_not_a_person": {
        "disposition": "refused",
        "statement": (
            "The crosswalk rules that there is nobody in this reading to crosswalk: it is "
            "a town finding, or a prose note that BOUNDS the register rather than "
            "populating it -- who the priest was, how a witness's name was spelled twice. "
            "It is not refused for being false and it is not out of the window; it is "
            "refused because there is no person unit in it for a card to receive. The "
            "content is the register's own chronology, which is where it is already spent. "
            "A reading naming a person the town holds would not fall here in the first "
            "place."),
    },
}


# T-1469 SPENT THE 37 TRADE AND PREMISES ENRICHMENTS, AND THIS FILE STOPPED ROUTING THEM.
# The single rule that used to stand here -- `the_enrichment_names_a_trade_or_premises_no_
# field_carries` -- said the finding named a fact "that no exact source-bearing structured
# field on that card carries today", and handed all 37 to a business ticket: T-1182, then
# its five children, then T-1190, then its three, then T-1468. Every one of those hand-offs
# was forced by the last named ticket closing, and not one of them read a card.
#
# It is no longer true that no field carries them. The business layer is built and converged
# (T-1310, T-1440..T-1442), the one-occupation field became dated plural roles with a
# `covers_scene_date` flag and a written withdrawal (T-0837, T-0991), and the candidate-fact
# table is committed (T-1232). tools/spend_trade_premises.py reads all 37 against those
# fields and gives each one of SIX outcomes, 36 of them terminal. Its rules are folded in
# here rather than restated, for the same reason `wrote_by_spend` imports the arrival pass's
# table: the pass that read the card is the pass that says what the card answered with, and
# a rule renamed there cannot drift out of the register that vouches for it.
from spend_trade_premises import (BOUNDED as TRADE_BOUNDED,  # noqa: E402
                                  CARRIED as TRADE_CARRIED,
                                  HANDED as TRADE_HANDED,
                                  LATER as TRADE_LATER,
                                  PROFILE as TRADE_PROFILE,
                                  RULES as TRADE_RULES,
                                  UNREACHED as TRADE_UNREACHED)

RULES.update(TRADE_RULES)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def clip(value, limit: int = 220) -> str:
    """One line of a committed field, whitespace-flattened, cut on a word."""
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + " …"


def issue_date(doc: dict) -> str | None:
    """The masthead date of a held issue, off its own `issue_id`."""
    match = re.search(r"(\d{4})_(\d{2})_(\d{2})$", str(doc.get("issue_id") or ""))
    return "-".join(match.groups()) if match else None


# ---------------------------------------------------------------------------------
# T-1301: WHERE EACH ENRICHMENT GOES, ONE AT A TIME.
#
# T-1298 ruled all 98 `corroborated_enrichment` units under ONE rule whose `ticket` was
# T-1160, and T-1160 then closed. `research_spend_ledger` holds that a unit may only
# defer to work that is still going to happen, so the gate went red on all 98 at once --
# not on the work, on the pointer. T-1301 is the piece that owes them an answer.
#
# A blanket repoint of all 98 to one id is the thing to avoid: a rule takes a SINGLE
# ticket, and these enrichments name six different fields, so one id would hand five of
# them to a ticket whose acceptance does not mention them -- which is how a unit ends up
# deferring to work that is not going to happen a second time. So the one rule becomes
# SEVEN, each naming the open ticket whose acceptance owns the kind of fact it carries,
# and the table below records the adjudication for every unit BY HAND: the field the
# pass's own summary names, in a phrase a reader can put beside the summary. The note is
# still derived -- it prints the finding verbatim -- and only the routing is authored.
#
# T-1254 was the sixth destination the ticket named and it is `done`; nothing routes to
# it. Seven units are not handed on at all: their own summaries say the source is a
# volume or a return PRINTED AFTER 1 July 1835 which confirms and dates a person the town
# already holds and backfills no in-window value. Under the ladder ratified 2026-09-03
# that is `later_only` -- a terminal disposition the registers already use -- and calling
# it a deferral to an 1835 attribute-fill ticket would be the false half of the pair.
#
# NOTHING HERE WRITES A CARD. A hand-off is not a spend; it names the field and the open
# ticket that owns it, and that ticket closing turns this file red, which is the point.
AGE = "the_enrichment_names_a_birth_or_age_no_field_carries"
WRITTEN = "the_enrichment_is_written_onto_the_card_it_names"
CARRIED = "the_enrichment_dates_an_appearance_the_card_already_carries"
DEPARTURE = "the_enrichment_names_a_departure_from_chicago_no_field_carries"
KIN = "the_enrichment_names_kin_no_field_carries"
# TRADE IS A ROUTING MARKER AND NO LONGER A RULE. The rule a trade enrichment falls
# under is decided by tools/spend_trade_premises.py, which reads the card; this
# constant only says which of the 96 enrichments go to it (T-1469).
TRADE = "routed_to_the_trade_and_premises_spend"
CIVIC = "the_enrichment_names_a_civic_church_or_school_post_no_field_carries"
LAND = "the_enrichment_names_a_landholding_no_field_carries"
LATER = "the_later_volume_enriches_a_biography_and_names_no_1835_field"

ENRICHMENT_ROUTE: dict[tuple[str, str], tuple[str, str]] = {
    ("02", "peck_philip"): (WRITTEN, "a Providence origin and a dated July 1831 arrival"),
    ("02", "temple_john_t"): (WRITTEN, "a July 1833 arrival with a family"),
    ("02", "tuller_elam"): (WRITTEN, "a July 1833 family arrival and a Connecticut origin"),
    ("03", "church_thomas"): (WRITTEN, "an 1834 arrival"),
    ("07", "jackson_samuel"): (WRITTEN, "an arrival from Buffalo dated 27 June 1833"),
    ("11", "andrus_thomas"): (WRITTEN, "an arrival dated 1 December 1833 and a June 1835 return"),
    ("11", "evans_sciota"): (WRITTEN, "a dated October 1834 list and a later Milwaukee office"),
    ("02", "bates_john_jr"): (TRADE, "an auctioneer's trade and a directory address"),
    ("02", "beaubien_josette"): (KIN, "a daughter and a wife the source names"),
    ("02", "caldwell_billy"): (DEPARTURE, "a dated removal that conflicts with the record's own migration year"),
    ("02", "calhoun_john"): (TRADE, "the founding and operation of a printing office"),
    ("02", "clybourne_archibald"): (TRADE, "a slaughterhouse and a meat trade with their premises"),
    ("02", "couch_ira"): (TRADE, "the keeping of the Tremont House"),
    ("02", "hamilton_richard_j"): (CIVIC, "county clerk and recorder, and the later county offices"),
    ("02", "hogan_john_s_c"): (CIVIC, "a corporate trustee named in the 1835 incorporation act"),
    ("02", "kinzie_juliette"): (CARRIED, "a dated pre-Chicago residence at the Fort Winnebago agency house"),
    ("02", "owen_thomas_jv"): (KIN, "a wife and four sons the sources name"),
    ("02", "pearsons_hiram"): (TRADE, "a house painter's trade the household carried as speculator"),
    ("02", "porter_eliza_chappel"): (KIN, "an 1835 marriage"),
    ("02", "porter_jeremiah"): (KIN, "a marriage dated 15 June 1835"),
    ("02", "robinson_alexander"): (AGE, "a birth year current scholarship disputes"),
    ("02", "robinson_catherine"): (KIN, "a husband, a marriage year, parents and a grandfather"),
    ("02", "sen_elijah_wentworth"): (TRADE, "a tavern kept at Wolf Point and later at Sand Ridge"),
    ("02", "snow_george_w"): (CIVIC, "election as assessor and surveyor in December 1833"),
    ("02", "spring_giles"): (CARRIED, "a relocation to Chicago dated June 1833"),
    ("02", "taylor_augustine"): (TRADE, "a builder's trade and the building of St Mary's"),
    ("02", "wright_john"): (CARRIED, "a joint arrival dated 29 October 1832"),
    ("03", "blodgett_tyler_k"): (TRADE, "an 1833 north-bank brickyard and a brick house"),
    ("03", "brown_rufus"): (TRADE, "a log boarding house kept full"),
    ("03", "carver_david"): (CARRIED, "a dated 1833 voter-roster appearance, which is an arrival bound"),
    ("03", "casey_edward_w"): (CARRIED, "an 1833 arrival remembered by a near participant"),
    ("03", "cobb_silas_b"): (TRADE, "saddlery and harness work and a later Lake Street address"),
    ("03", "cohen_peter"): (TRADE, "incorporation of the Chicago Hydraulic Company"),
    ("03", "davis_t_o"): (TRADE, "the establishing of the Whig newspaper in 1835"),
    ("03", "elston_daniel"): (TRADE, "soap and candle manufacture and a later distillery and brewery"),
    ("03", "fullerton_alexander"): (CIVIC, "the 1835 town-clerk chronology"),
    ("03", "gale_stephen_f"): (CARRIED, "a dated 1833 voter-roster appearance"),
    ("03", "heacock_russel_e"): (KIN, "a household the 1843 directory distinguishes"),
    ("03", "ingersoll_chester"): (TRADE, "the Green Tree house held as landlord 1834-37"),
    ("03", "jones_benjamin"): (DEPARTURE, "a dated 1835 purchase and an 1836 removal"),
    ("04", "handy_major"): (TRADE, "a named role in the 1833 river-improvement works"),
    ("04", "kimberly_edmund_s"): (AGE, "an exact birth date of 7 April 1803"),
    ("04", "kinzie_robert_a"): (TRADE, "a frame store and membership of Kinzie, Davis & Hyde"),
    ("04", "mason_matthias"): (TRADE, "a blacksmith shop opened in the fall of 1833"),
    ("04", "maxwell_philip"): (AGE, "full birth data"),
    ("04", "mckee_david"): (TRADE, "the agency blacksmith's shop at the foot of State Street"),
    ("04", "meeker_joseph"): (CIVIC, "church membership, a Sunday-school office and the first meeting house"),
    ("04", "murphy_john"): (TRADE, "the keeping of the Exchange Coffee House from August 1834"),
    ("04", "norton_nelson_r"): (CARRIED, "an arrival dated 16 November 1833"),
    ("04", "pierce_asahel"): (CARRIED, "an October 1833 arrival"),
    ("04", "porthier_joseph"): (DEPARTURE, "a departure dated 27 February 1835 and a return"),
    ("04", "pruyne_peter"): (TRADE, "a drug store kept in partnership from early 1833"),
    ("04", "sproat_grenville"): (CIVIC, "an English and Classical School opened in the fall of 1833"),
    ("04", "st_cyr_john_mary"): (CIVIC, "an 1833 appointment, the first Mass and the first church"),
    ("04", "steele_ashbel"): (CIVIC, "the county coroner's office in the 1835 period"),
    ("04", "sweet_alanson"): (DEPARTURE, "a removal to Milwaukee in 1835"),
    ("04", "thomas_frederick"): (TRADE, "a barber-surgeon's and retail druggist's trade"),
    ("04", "walters_william"): (TRADE, "the Wolf Point Tavern kept 1833-36"),
    ("04", "watkins_john"): (CIVIC, "a school taught in Chicago in 1835"),
    ("05", "kercheval_gholson"): (CARRIED, "a dated 1833 treaty payment naming him of Chicago"),
    ("05", "kimball_walter"): (TRADE, "a New Store at the South Water and Clark junction"),
    ("05", "lampman_henry_s"): (TRADE, "a brickmaker's trade and the yard that engaged him"),
    ("05", "wright_john_s"): (LAND, "Chicago land purchases and original-town lots"),
    ("06", "andrews_davi"): (CARRIED, "a dated Cook County presence from 1834"),
    ("06", "blakesley_harvey_a"): (LATER, "later Chicago directories, backfilling no occupation and no roof"),
    ("06", "mitchell_henry"): (TRADE, "wagon-factory work in 1834"),
    ("08", "hobson_jesse"): (KIN, "a marriage at Naperville dated 6 April 1835"),
    ("08", "orsemus_morrison"): (CARRIED, "an 1833 arrival"),
    ("09", "chandler_joseph"): (TRADE, "executive charge of the harbour work begun 1 July 1833"),
    ("09", "hathaway_joshua"): (TRADE, "the making of the 1834 cadastral map"),
    ("09", "myers_frederick"): (CIVIC, "a quartermaster's clerkship at Fort Dearborn, 1831-33"),
    ("09", "pugsley_john_k"): (DEPARTURE, "a June 1835 journey from near Utica, and a return"),
    ("10", "barrows_mary"): (CIVIC, "an assistant's post in Miss Chappel's school"),
    ("10", "boilvin_nicholas"): (CARRIED, "dated 1834 post-office returns and an 1833 treaty schedule"),
    ("10", "christy_nathan"): (CARRIED, "a dated 1834 letter-list appearance"),
    ("10", "cleland_martin"): (DEPARTURE, "an 1834 prospecting journey from Chautauqua, New York"),
    ("10", "vasseur_noel"): (CARRIED, "an 1835 postal list and an 1833 treaty schedule"),
    ("11", "kingston_paul"): (LAND, "a Chicago landholding and a dated January 1835 departure"),
    ("11", "lathrop_samuel_s"): (CIVIC, "First Baptist membership from October 1833"),
    ("12", "woodworth_james_h"): (CARRIED, "a move to Chicago in 1833"),
    ("14", "bailey_bennet"): (TRADE, "a carpenter and builder's trade printed in 1839"),
    ("14", "chapman_chas_h"): (TRADE, "a real-estate dealer's trade and a Randolph Street address"),
    ("14", "clarke_h_b"): (TRADE, "a hardware merchant's trade the 1835 papers carry"),
    ("14", "collins_j_h"): (TRADE, "an attorney's practice carried across 1834-35"),
    ("14", "elston_daniel"): (TRADE, "soap and candle manufacture read in pass 3 and never written"),
    ("14", "marshall_j_a"): (TRADE, "an auction and commission trade on South Water Street"),
    ("14", "moore_henry"): (TRADE, "an attorney's practice and a Clark Street office"),
    ("14", "sabine_wm"): (TRADE, "a boarding house at 161 Lake Street"),
    ("14", "sen_elijah_wentworth"): (TRADE, "the Wolf Point tavern, carried forward from pass 2"),
    ("14", "stewart_r"): (TRADE, "an attorney's practice on Lake Street"),
    ("14", "thrall_e_l"): (LATER, "an 1837 election return, carrying a 1837 ward and no 1835 value"),
    ("15", "doolittle_ehjah"): (LATER, "a volume printed after the scene date, adding no 1835 attestation"),
    ("15", "kinzie_juliette"): (LATER, "a volume printed after the scene date, adding no 1835 attestation"),
    ("15", "porter_jeremiah"): (LATER, "a volume printed after the scene date, adding no 1835 attestation"),
    ("15", "vanderbogart_h"): (LATER, "a volume printed after the scene date, adding no 1835 attestation"),
    ("15", "wright_john"): (LATER, "a volume printed after the scene date, adding no 1835 attestation"),
}


def enrichment_key(unit: dict) -> tuple[str, str]:
    """The pass number and the person, which is what makes a resident unit unique.

    Five people were read in two different passes -- Daniel Elston, Elijah Wentworth sen.,
    Juliette Kinzie, Jeremiah Porter and John Wright -- and the two readings say different
    things, so the person alone is not a key and the routing is per READING.
    """
    name = Path(unit["source_file"]).name
    match = re.match(r"pass_(\d\d)_", name)
    return ((match.group(1) if match else name), str(unit["source_record_id"]))


def entity_names(row: dict) -> list[str]:
    names = []
    for entity in row.get("entities") or []:
        if isinstance(entity, dict):
            names.append(str(entity.get("normalized") or entity.get("as_printed") or ""))
        else:
            names.append(str(entity))
    return [name for name in names if name]


def rule_residents(unit: dict, finding: dict | None, preamble: str) -> tuple[str, str]:
    if not finding:
        return ("the_manifest_is_a_reservation_and_not_a_reading",
                f"{unit['source_record_id']} is a row of the pilot manifest, whose own preamble "
                f"reads: “{clip(preamble, 160)}” No findings ledger was ever committed for the "
                f"pilot, so this reservation has no reading attached to it to spend.")
    outcome = str(finding.get("outcome") or "")
    summary = clip(finding.get("summary") or finding.get("default_summary"))
    sources = ", ".join(str(s) for s in (finding.get("sources") or [])) or "none named"
    if outcome == "candidate_identity":
        candidates = finding.get("candidates") or []
        assessed = "; ".join(
            f"{clip(c.get('name'), 60)} ({clip(c.get('assessment'), 24)}, asserted="
            f"{bool(c.get('asserted'))})" for c in candidates if isinstance(c, dict))
        return ("the_pass_named_a_candidate_and_did_not_assert_it",
                f"The pass on {unit['source_record_id']} returned: “{summary}” "
                f"Candidate(s) as recorded: {assessed or 'none carried on the finding'}.")
    if outcome == "corroborated":
        return ("corroboration_confirms_and_moves_nothing",
                f"The pass on {unit['source_record_id']} returned: “{summary}” "
                f"Corroborating sources as recorded: {clip(sources, 200)}.")
    key = enrichment_key(unit)
    route = ENRICHMENT_ROUTE.get(key)
    if route is None:
        raise SystemExit(
            f"{unit['source_record_id']} (pass {key[0]}) is an enrichment T-1301 never "
            "adjudicated. An enrichment may not be routed by default: add it to "
            "ENRICHMENT_ROUTE with the field its own summary names.")
    rule, field = route
    if rule == TRADE:
        # THE OUTCOME AND THE NOTE ARE THE READING PASS'S TO GIVE, not this one's. T-1469
        # read each of these 37 against the card it names; this register carries what it
        # found, and its note prints the finding beside the field that answers it.
        from spend_trade_premises import carrier_sentence, rule_for
        return (rule_for(key), carrier_sentence(key))
    return (rule,
            f"The pass on {unit['source_record_id']} returned: “{summary}” "
            f"Sources as recorded: {clip(sources, 180)}. T-1301 reads that as {field}.")


# T-1343: A DATED PRESS APPEARANCE IS A CLASSIFICATION, AND ITS RULE IS THE REGISTER'S
# ANSWER. Two tools have to agree about which press units are in play -- this register and
# `tools/spend_press_bounds.py`, which spends the ones that reach a card -- and the way
# they cannot drift apart is for one of them to own the test. `rule_newspapers` is that
# owner: asked with a probe cache it says only whether the claim IS a dated appearance of a
# named person, and asked normally it goes on to read the committed register and rule it.
PRESS_APPEARANCE = "a dated press appearance"
PRESS_REGISTER = ROOT / "data" / "research" / "newspapers" / "register_1835.json"
PRESS_GAZETTEER = ROOT / "data" / "research" / "newspapers" / "gazetteer.json"
PRESS_ACTION_RULES = {
    "new_resident": "the_press_name_is_a_person_the_town_does_not_hold",
    "replace_invented": "the_press_name_replaces_an_invented_card",
}


def press_register_index(root: Path = ROOT) -> dict:
    """Claim key -> the register row of every person the gazetteer says that claim names."""
    rel = lambda path: root / path.relative_to(ROOT)  # noqa: E731
    register = {row["id"]: row for row in read_json(rel(PRESS_REGISTER))["persons"]}
    index: dict = {}
    for person in read_json(rel(PRESS_GAZETTEER))["persons"]:
        row = register.get(person["id"])
        if row is None:
            continue
        for claim in person.get("mentions") or []:
            index.setdefault(claim, []).append(
                {"person": person["id"], "name": person.get("name"),
                 "action": row.get("action")})
    return index


def press_appearance_rule(unit: dict, cache: dict | None, note: str) -> tuple[str, str]:
    """The refusal a dated press appearance falls under, off the committed register."""
    cache = {} if cache is None else cache
    if cache.get("press_probe"):
        return (PRESS_APPEARANCE, note)
    index = cache.get("press_register_index")
    if index is None:
        index = cache["press_register_index"] = press_register_index()
    key = str(unit.get("record_key") or "")
    rows = index.get(key) or []
    actions = sorted({str(row.get("action")) for row in rows})
    if not rows:
        raise SystemExit(
            f"{key}: a dated press appearance the committed register carries no person for. "
            "Rebuild data/research/newspapers/register_1835.json with "
            "tools/compile_register.py --build rather than ruling it blind.")
    if "enrich" in actions:
        raise SystemExit(
            f"{key}: the register enriches a card with this claim, so it is T-1343's to "
            "SPEND and not this register's to rule. Run tools/spend_press_bounds.py.")
    unseen = [action for action in actions if action not in PRESS_ACTION_RULES]
    if unseen:
        raise SystemExit(
            f"{key}: the register carries action(s) {unseen} that this file has no rule "
            "for. Rule them rather than mapping them onto the nearest statement.")
    rule = (PRESS_ACTION_RULES["replace_invented"] if "replace_invented" in actions
            else PRESS_ACTION_RULES["new_resident"])
    said = "; ".join("%s → %s" % (row["name"], row["action"]) for row in rows)
    return (rule, f"{note} The register carries: {clip(said, 200)}")


def is_dated_press_appearance(unit: dict, printed: str | None) -> bool:
    """Whether this claim's only spendable content is a named person on a dated day."""
    return rule_newspapers(unit, printed, {"press_probe": True})[0] == PRESS_APPEARANCE


def rule_newspapers(unit: dict, printed: str | None,
                    cache: dict | None = None) -> tuple[str, str]:
    row = unit["record"]
    where = f"{unit['source_file'].rsplit('/', 1)[-1].removesuffix('.json')} {row.get('id')}"
    kind = row.get("kind")
    line = clip(row.get("normalized"), 180)
    if printed and printed > SCENE_DATE:
        return ("the_issue_is_printed_after_the_scene_date",
                f"{where}: the issue is dated {printed}, after the scene date. The {kind} "
                f"reads: “{line}”")
    if row.get("letter_list_only"):
        return ("the_letter_list_name_belongs_to_the_borderline_roster",
                f"{where}: a post-office letter list printed {printed}. Names as read: "
                f"{clip(', '.join(entity_names(row)) or line, 200)}")
    business = row.get("business") or {}
    if business:
        # T-1508. This register ruled these until the ledger learned to reach the
        # AUTHORED BUSINESS LAYER as a target surface, matching a block on its own
        # `claim_ids`. Every business unit over the committed corpora is spent there
        # now, so the rule here fired zero times and was removed rather than left
        # standing as judgement it never makes. It refuses instead of falling through:
        # the branches below read a notice as a person or a family column, and a firm
        # answered by one of those is a wrong ruling arriving quietly.
        # A PROBE ASKS A QUESTION AND HAS TO GET AN ANSWER. `is_dated_press_appearance`
        # runs every unit in the corpus past this function to ask one thing — is this a
        # named person on a dated day? — and tools/spend_press_bounds.py asks it of the
        # WHOLE newspaper corpus, firm notices included. The answer for a firm is no.
        # Raising at a caller that is only asking stops a build that was right to ask,
        # which is what happened on the first cut of this change: the gate went red on
        # `chicago_american_1835_06_08 c006` — a real Goss & Cobb notice — from a probe,
        # not from a ruling. The refusal below is for the RULING path alone, and the
        # early return above in press_appearance_rule is the same distinction already
        # drawn once in this file.
        if (cache or {}).get("press_probe"):
            return (None, f"{where}: a notice carrying a firm is not a dated press "
                          "appearance; it is the ledger's to spend on the business layer")
        raise SystemExit(
            f"{where}: the notice of {printed} carries the firm "
            f"“{clip(business.get('name'), 80) or 'unnamed in the block'}”, and since "
            "T-1508 a business unit is the ledger's to SPEND on the business layer, not "
            "this register's to rule. Run tools/research_spend_ledger.py --build; if it "
            "still arrives here, no business record claims it, which is T-1468's.")
    if kind == "person":
        if FAMILY_COLUMN.match(str(row.get("normalized") or "")):
            return ("the_family_column_names_kin",
                    f"{where}: the family column of {printed} reads: “{line}”")
        return press_appearance_rule(
            unit, cache,
            f"{where}: a person notice of {printed} naming "
            f"{clip(', '.join(entity_names(row)) or 'no entity row', 120)}. It reads: “{line}”")
    if kind in {"price", "shipping"}:
        return ("the_market_and_the_port_in_aggregate",
                f"{where}: a {kind} reading of {printed}. It reads: “{line}”")
    names = entity_names(row)
    if names:
        return press_appearance_rule(
            unit, cache,
            f"{where}: a {kind} of {printed} naming {clip(', '.join(names), 150)}. "
            f"It reads: “{line}”")
    return ("the_column_names_nobody",
            f"{where}: a {kind} of {printed} whose entities array is empty. It reads: “{line}”")


# The two committed crosswalks that decide whether a register appearance HAS an
# identification, and the rule each of their outcomes falls under. A new outcome is a
# SystemExit and not a guess: `church_identification` raises, the gate goes red, and
# somebody rules it. Mapping an unseen outcome onto the nearest rule is how a statement
# stops being true of the units under it.
CHURCH_CROSSWALKS = (
    "data/research/church/st_marys_baptisms_crosswalk.json",
    "data/research/church/st_cyr_crosswalk.json",
)
CHURCH_OUTCOME_RULES = {
    "merged": None,                       # spent on a card by T-1337; see below
    "no_candidate": "the_register_appearance_names_nobody_this_town_holds",
    "unmatched": "the_register_appearance_names_nobody_this_town_holds",
    "refused": "the_register_appearance_identity_was_refused_in_the_crosswalk",
    "refused_surname_only": "the_register_appearance_identity_was_refused_in_the_crosswalk",
    "no_forename": "the_register_appearance_identity_was_refused_in_the_crosswalk",
    "candidate": "the_register_appearance_identity_is_a_candidate_and_not_a_merge",
    "not_a_person": "the_register_reading_is_about_the_town_and_not_a_person",
    "ruled_no_town_change": "the_register_reading_is_about_the_town_and_not_a_person",
}


def church_identification(record_id: str, cache: dict) -> dict | None:
    index = cache.get("church_crosswalk_index")
    if index is None:
        index = {}
        for rel in CHURCH_CROSSWALKS:
            doc = read_json(ROOT / rel)
            for entry in (doc.get("rulings") or []) + (doc.get("entries") or []):
                key = entry.get("record_id") or entry.get("claim_id")
                if key:
                    index[key] = dict(entry, crosswalk=rel)
        cache["church_crosswalk_index"] = index
    entry = index.get(record_id)
    if entry is None:
        return None
    outcome = str(entry.get("outcome") or "")
    if outcome not in CHURCH_OUTCOME_RULES:
        raise SystemExit(
            f"{record_id}: {entry['crosswalk']} rules it {outcome!r} and this register has "
            f"no rule for that outcome -- rule it rather than mapping it onto the nearest "
            f"statement")
    return entry


def church_appearance_rule(row: dict, where: str, seen: str,
                           entry: dict) -> tuple[str, str]:
    """What an appearance's own crosswalk already decided about the identity."""
    rule = CHURCH_OUTCOME_RULES[str(entry.get("outcome"))]
    told = f"{entry['crosswalk'].rsplit('/', 1)[-1]} rules it {entry.get('outcome')!r}"
    if rule is None:
        # SPENT, NOT RULED (T-1337). tools/spend_appearance_bounds.py has written this
        # appearance onto the card the crosswalk merges it into, so it closes `asserted`
        # and this register states nothing about it: a ruling on a unit something else
        # closed reads as work done and is not, and
        # `research_spend_ledger.ruling_coverage_faults` fails it.
        return None, (
            f"{where}: {seen}. {told} into {entry.get('name')!r}, and "
            f"tools/spend_appearance_bounds.py has written that bound onto the card.")
    return rule, (f"{where}: {seen}. {told}: {clip(entry.get('rule'), 320)}")


def rule_church(unit: dict, cache: dict | None = None) -> tuple[str, str]:
    row = unit["record"]
    cache = {} if cache is None else cache
    where = f"{unit['source_file'].rsplit('/', 1)[-1].removesuffix('.json')} {row.get('id')}"
    dated = row.get("describes_date")
    if row.get("beyond_ticket_window") is True:
        return ("the_roll_is_beyond_the_reading_window",
                f"{where}: {clip(row.get('normalized'), 80)}, read from the roll of the Second "
                f"Presbyterian Church. The entry as printed: "
                f"“{clip((row.get('cells') or {}).get('entry_as_printed') or row.get('as_read'), 140)}”")
    role = str((row.get("cells") or {}).get("role") or "")
    if role in KIN_ROLES:
        return ("the_register_entry_names_kin",
                f"{where}: {clip(row.get('normalized'), 80)} is the {role} of a register entry "
                f"dated {dated} at Chicago. {clip(row.get('notes'), 160)}")
    ruled = church_identification(str(row.get("id") or ""), cache)
    if role in ATTENDANCE_ROLES:
        seen = (f"{clip(row.get('normalized'), 80)} stands as {role} at a register entry "
                f"dated {dated} at Chicago")
        if ruled is None:
            raise SystemExit(
                f"{row.get('id')}: an attendance appearance no committed church crosswalk "
                f"has ruled on -- crosswalk it rather than handing it on")
        return church_appearance_rule(row, where, seen, ruled)
    if row.get("kind") == "person":
        seen = (f"a person reading of the register prose, dated {dated}, which reads: "
                f"“{clip(row.get('normalized'), 180)}”")
        if ruled is None:
            raise SystemExit(
                f"{row.get('id')}: a person reading of the register prose no committed "
                f"church crosswalk has ruled on -- crosswalk it rather than handing it on")
        return church_appearance_rule(row, where, seen, ruled)
    return ("a_town_reading_with_no_record_to_write",
            f"{where}: a {row.get('kind')} reading of the register, dated {dated}. "
            f"It reads: “{clip(row.get('normalized'), 180)}”")


def rule_books(unit: dict) -> tuple[str, str]:
    row = unit["record"]
    where = f"{unit['source_file'].rsplit('/', 1)[-1].removesuffix('.json')} {row.get('id')}"
    kind = row.get("kind")
    dated = row.get("describes_date")
    line = clip(row.get("normalized"), 200)
    if kind == "landscape":
        return ("a_ground_reading_describes_the_site_not_a_record",
                f"{where}: a landscape reading dated {dated}. It reads: “{line}”")
    if kind in {"price", "shipping"}:
        return ("the_market_and_the_port_in_aggregate",
                f"{where}: a {kind} reading dated {dated}. It reads: “{line}”")
    year = L.year_in(row)
    if year is not None and year < 1835:
        return ("the_reading_is_earlier_than_the_scene_and_does_not_reach_it",
                f"{where}: a {kind} reading whose own describes_date is “{clip(dated, 60)}”, "
                f"earlier than the scene date. It reads: “{line}”")
    return ("a_town_reading_with_no_record_to_write",
            f"{where}: a {kind} reading dated {clip(dated, 60) or 'undated'}, in the window and "
            f"naming no record this layer holds. It reads: “{line}”")


_BUSINESS_REACH: dict[str, list[str]] = {}


def business_claim_reach(root: Path = ROOT) -> dict[str, list[str]]:
    """Claim id -> the compiled business records that name it, at ANY depth (T-1509).

    Deliberately LOOSER than `research_spend_ledger.business_target_index`, which is the
    point of the pair. That index answers "is this reading asserted?" and so demands a
    block carrying a tier and citing a source. This one answers the different question a
    ruling has to answer first: "does the layer hold a record for this reading at all?"
    Between the two answers sit the units T-1514 owns -- reached by a record, asserted by
    no block of it -- and outside both sit the readings the layer compiled nothing from.
    Nothing is read out of prose here either: a record reaches a claim only where it
    names that claim in a `claim_ids` list.
    """
    key = str(root)
    if key in _BUSINESS_REACH:
        return _BUSINESS_REACH[key]
    found: dict[str, list[str]] = {}

    def walk(node, record_id):
        if isinstance(node, dict):
            claims = node.get("claim_ids")
            if isinstance(claims, list):
                for claim in claims:
                    if isinstance(claim, str) and claim:
                        seen = found.setdefault(claim, [])
                        if record_id not in seen:
                            seen.append(record_id)
            for value in node.values():
                walk(value, record_id)
        elif isinstance(node, list):
            for value in node:
                walk(value, record_id)

    base = root.joinpath(*L.BUSINESS_LAYER)
    for path in sorted(base.rglob("*.json")) if base.is_dir() else []:
        if path.name in L.BUSINESS_INDEX_FILES:
            continue
        doc = read_json(path)
        if isinstance(doc, dict) and doc.get("id"):
            walk(doc, str(doc["id"]))
    _BUSINESS_REACH[key] = found
    return found


def rule_business(unit: dict, reach: dict[str, list[str]],
                  printed: str | None) -> tuple[str, str]:
    """The written answer for a business reading the ledger could not assert (T-1509).

    THE RECORD OUTRANKS THE DATE, which is the order T-1508 already set on this corpus:
    where the layer holds a record compiled from the reading, that record carries its own
    `tier` and `basis` for what it read out of a printing, and the scene-date question is
    the record's rather than this register's.
    """
    row = unit["record"]
    where = f"{unit['source_file'].rsplit('/', 1)[-1].removesuffix('.json')} {row.get('id')}"
    block = row.get("business") or {}
    named = clip(block.get("name") or block.get("trade"), 80) or "unnamed in the block"
    line = clip(row.get("normalized"), 180)

    records = reach.get(unit["record_key"]) or []
    if records:
        return ("the_compiled_record_names_this_claim_and_tiers_no_field_to_it",
                f"{where}: the layer holds {', '.join(records)}, compiled from this very "
                f"reading of “{named}” — and it names this claim only at the record root, "
                f"where no tier stands. It reads: “{line}”")
    if printed and printed > SCENE_DATE:
        return ("the_issue_is_printed_after_the_scene_date",
                f"{where}: the issue is dated {printed}, after the scene date, and the "
                f"layer compiled no record from it. The notice of “{named}” reads: “{line}”")
    year = L.year_in(row)
    if year is not None and year < 1835:
        dated = clip(row.get("describes_date"), 60)
        return ("the_reading_is_earlier_than_the_scene_and_does_not_reach_it",
                f"{where}: a business reading whose own describes_date is “{dated}”, "
                f"earlier than the scene date. It reads: “{line}”")
    return ("a_trade_reading_the_business_layer_holds_no_record_for",
            f"{where}: a business reading of “{named}”, dated "
            f"{clip(row.get('describes_date'), 60) or (printed or 'undated')}, that no "
            f"record of data/businesses/ names in its claim_ids. It reads: “{line}”")


def mine(root: Path = ROOT) -> list[dict]:
    """Every unit the derivation leaves unresolved and owned by T-1298.

    `natural_disposition` reads no ruling register, so this corpus is fixed by the
    readings and the residents layer alone -- writing the registers cannot change what
    they are asked to cover. The hand-authored register's own units are excluded: they
    were ruled by T-1234 and a second ruling on one unit is a fault, correctly.
    """
    registry = read_json(root / "data" / "research" / "domains.json")
    units, faults = L.extract_units(root, registry)
    if faults:
        raise SystemExit("the reading registry is faulted: " + "; ".join(faults[:5]))
    # T-1342: the index is keyed on the unit's `record_key`, not its raw id, or a
    # file-local claim number reaches every issue that prints it and this register
    # rules a unit a resident card had already closed.
    targets = L.target_index(root, {unit["record_key"] for unit in units})
    already = {row["unit"] for row in read_json(HAND_AUTHORED).get("rulings") or []}
    out = []
    for unit in units:
        if unit["unit_id"] in already:
            continue
        natural = L.natural_disposition(root, unit, targets)
        if natural.get("disposition") != "unresolved":
            continue
        if natural.get("ticket") == TICKET:
            out.append(unit)
        elif (natural.get("ticket") == BUSINESS_TICKET
                and unit["record"].get("kind") == "business"):
            # T-1509. The `business` half of T-1468's routing, and only that half: the
            # same pointer also carries the civic corpus, which is another tool's file
            # and another ticket's question. `kind` is the readings' own word, and it is
            # what `research_spend_ledger.PLACE_AND_ENTERPRISE` routes on.
            out.append(unit)
    return out


def classify(root: Path, unit: dict, cache: dict) -> tuple[str, str]:
    domain = unit["domain"]
    if unit["record"].get("kind") == "business":
        # T-1509, and BEFORE the domain rules: a business unit is the same question in
        # both corpora -- does the compiled layer hold a record for it? -- and answering
        # it twice, once in `rule_newspapers` and once in `rule_books`, is how the two
        # would drift. `rule_newspapers` refuses a business block outright (T-1508) for
        # exactly this reason.
        doc = cache.setdefault(unit["source_file"], read_json(root / unit["source_file"]))
        printed = issue_date(doc) if domain == "newspapers" else None
        return rule_business(unit, business_claim_reach(root), printed)
    if domain == "residents":
        preamble = cache.setdefault(
            unit["source_file"], read_json(root / unit["source_file"])).get("_doc") or ""
        return rule_residents(unit, L.resident_finding(root, unit), preamble)
    if domain == "newspapers":
        doc = cache.setdefault(unit["source_file"], read_json(root / unit["source_file"]))
        return rule_newspapers(unit, issue_date(doc), cache)
    if domain == "church":
        return rule_church(unit, cache)
    return rule_books(unit)


def wrote_by_spend(person_id: str) -> list[dict]:
    """Where tools/spend_enrichment_arrivals.py put this finding, from its own table."""
    from spend_enrichment_arrivals import ADJUDICATION, household_of
    row = ADJUDICATION[person_id]
    path = household_of(person_id)
    return [{"file": path.relative_to(ROOT).as_posix(), "field": field}
            for field in sorted(row["writes"])]


def corpus_ticket(unit: dict) -> str:
    """Which ticket's remainder this unit is (T-1509). The readings' own `kind` decides."""
    return BUSINESS_TICKET if unit["record"].get("kind") == "business" else TICKET


def build_documents(root: Path = ROOT) -> dict[str, dict]:
    cache: dict = {}
    per_domain: dict[str, list[dict]] = {domain: [] for domain in DOMAINS}
    per_domain_tickets: dict[str, set[str]] = {domain: set() for domain in DOMAINS}
    for unit in mine(root):
        if unit["domain"] not in per_domain:
            raise SystemExit(f"{unit['unit_id']}: this tool rules a domain it does not write")
        rule, note = classify(root, unit, cache)
        if rule is None:                   # spent on a card; see church_appearance_rule
            continue
        row = {"unit": unit["unit_id"], "rule": rule, "note": note}
        if rule == WRITTEN:
            # THE FIELDS ARE THE WRITING PASS'S TO NAME, not this one's. Importing the
            # adjudication keeps one table in charge of both halves: the pass that put the
            # block on the card is the pass that says where it went, and a field renamed
            # there cannot drift out of the register that vouches for it.
            row["wrote"] = wrote_by_spend(unit["source_record_id"])
        per_domain[unit["domain"]].append(row)
        per_domain_tickets[unit["domain"]].add(corpus_ticket(unit))
    documents = {}
    for domain, rulings in per_domain.items():
        rulings.sort(key=lambda row: row["unit"])
        tally = Counter(row["rule"] for row in rulings)
        # T-1509: WHOSE UNITS ARE IN THIS FILE, derived from the rows rather than declared.
        # The register carried one ticket's remainder until the business half of T-1468's
        # routing arrived in the two corpora this tool already writes, and a reader who
        # cannot tell which ticket a row answers cannot tell what closing that ticket
        # should do to the file.
        tickets = sorted(per_domain_tickets[domain])
        documents[domain] = {
            "schema": "research-spend-rulings-v1",
            "_doc": (
                f"DERIVED, T-1298, by tools/spend_remainder_rulings.py from the {domain} "
                "corpus beside it and the residents layer it names -- run --check to "
                "re-derive it. The written ruling on the remainder of T-1236: every unit "
                "the ledger's own derivation leaves unresolved and owns to T-1298. "
                "tools/research_spend_ledger.py reads this file beside the hand-authored "
                "spend_rulings.json, at the point where it would otherwise leave a unit "
                "open, so a ruling here can only close a unit nothing else has closed and "
                "can never overturn an assertion, a later_only or a refusal the readings "
                "themselves carry. NOTHING HERE EDITS A RESIDENT, MINTS A PERSON, MOVES A "
                "CONFIDENCE OR INVENTS A CITATION, and nothing here decides the blocked "
                "letter-list question of T-0660 -> T-0691. "
                "T-1509 ADDED A SECOND CORPUS to the newspapers and books registers: the "
                "100 `business` readings the ledger's own derivation routes to T-1468 and "
                "that T-1508 could not spend on the business layer. `tickets` above says "
                "which tickets the rows in THIS file answer. "
                + TWO_HAND_OFF_SHAPES),
            "ticket": TICKET,
            "tickets": tickets,
            "generated_by": "tools/spend_remainder_rulings.py",
            "counts": {rule: tally[rule] for rule in sorted(tally)},
            "rules": {name: RULES[name] for name in sorted(tally)},
            "rulings": rulings,
        }
    return documents


def out_path(domain: str, root: Path = ROOT) -> Path:
    return root / "data" / "research" / domain / "spend_rulings.json"


def write(documents: dict[str, dict]) -> None:
    for domain, doc in documents.items():
        path = out_path(domain)
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def self_test() -> int:
    failures = []
    for name, rule in sorted(RULES.items()):
        if len(str(rule.get("statement") or "").strip()) < 40:
            failures.append(f"rule {name}: states no rule")
        if rule["disposition"] not in L.RULING_DISPOSITIONS:
            failures.append(f"rule {name}: {rule['disposition']!r} is not a disposition a ruling may reach")
        if rule["disposition"] == "unresolved":
            failures.extend(L.unresolved_owner_faults(f"rule {name}", rule))

    # A hand-off may only name a ticket that is still live work, which is the invariant
    # that makes "owned" mean something. The ledger tests this too; testing it here says
    # WHICH rule broke rather than which 90 units did. A rule that names no ticket at all
    # is waiting on EVIDENCE and not on work (T-1423) -- there is no liveness to test, and
    # `unresolved_owner_faults` above has already required it to say what it waits for.
    states = L.ticket_states(ROOT)
    for name, rule in sorted(RULES.items()):
        if rule["disposition"] != "unresolved" or not rule.get("ticket"):
            continue
        if states.get(rule["ticket"]) not in L.OPEN_TICKET_STATES:
            failures.append(f"rule {name}: hands on to {rule['ticket']}, which is "
                            f"{states.get(rule['ticket'])!r} and not live work")

    # The rules held over the corpus they derive.
    def held(label, unit, want, **kw):
        got = classify(ROOT, unit, {}) if not kw else kw["fn"](unit)
        if want is None:
            # SPENT, NOT RULED (T-1337): the note has to say where the unit went instead,
            # or the register is silent about a unit for no stated reason.
            if got[0] is not None:
                failures.append(f"{label}: is ruled here and it is spent on a card "
                                f"(fell under {got[0]!r})")
            elif "spend_appearance_bounds" not in got[1]:
                failures.append(f"{label}: is unruled and does not say where it went")
            return
        if got[0] != want:
            failures.append(f"{label}: ruled {got[0]!r}, wanted {want!r}")

    paper = {"source_file": "x/chicago_democrat_1835_01_21.json",
             "record": {"id": "c001", "kind": "notice", "normalized": "A notice.", "entities": []}}
    held("an issue after the scene date", paper,
         "the_issue_is_printed_after_the_scene_date",
         fn=lambda u: rule_newspapers(u, "1835-08-05"))
    held("a letter list", {**paper, "record": {**paper["record"], "letter_list_only": True}},
         "the_letter_list_name_belongs_to_the_borderline_roster",
         fn=lambda u: rule_newspapers(u, "1835-06-10"))
    held("a letter list printed later still reads by the ladder",
         {**paper, "record": {**paper["record"], "letter_list_only": True}},
         "the_issue_is_printed_after_the_scene_date",
         fn=lambda u: rule_newspapers(u, "1835-08-05"))
    firm_unit = {**paper, "record": {**paper["record"],
                                     "business": {"name": "Goss & Cobb"}}}
    try:
        rule_newspapers(firm_unit, "1835-06-10")
        failures.append("a notice carrying a firm: was ruled rather than refused")
        print("  FAIL: a notice carrying a firm")
    except SystemExit:
        print("  ok:   a notice carrying a firm stops the build (T-1508)")
    # AND THE PROBE GETS AN ANSWER RATHER THAN THE REFUSAL. tools/spend_press_bounds.py
    # runs the WHOLE newspaper corpus past is_dated_press_appearance, firm notices
    # included, to ask one question; raising at a caller that is only asking took the
    # gate red on the real Goss & Cobb notice (chicago_american_1835_06_08 c006) on the
    # first cut of T-1508. Both halves are held here because either alone is a bug.
    try:
        if is_dated_press_appearance(firm_unit, "1835-06-10"):
            failures.append("a firm notice probes as a dated press appearance")
            print("  FAIL: a firm notice probes as a dated press appearance")
        else:
            print("  ok:   a firm notice answers the probe with no, and does not raise at it")
    except SystemExit:
        failures.append("the probe on a firm notice raised instead of answering — "
                        "spend_press_bounds asks this of every unit and cannot be refused")
        print("  FAIL: the probe on a firm notice raised instead of answering")
    held("the married column",
         {**paper, "record": {**paper["record"], "kind": "person",
                              "normalized": "MARRIED, In this town, on the 12th inst."}},
         "the_family_column_names_kin", fn=lambda u: rule_newspapers(u, "1834-01-07"))
    # T-1343: A PRESS APPEARANCE'S RULE IS THE REGISTER'S ANSWER, so these fixtures carry a
    # pre-seeded register index rather than reading the committed one — the point of each
    # case is the MAPPING, and a fixture standing on a real claim would move the day the
    # register was rebuilt.
    press = {"press_register_index": {
        "c_new": [{"person": "person_j_doe", "name": "J. Doe", "action": "new_resident"}],
        "c_replace": [{"person": "person_j_roe", "name": "J. Roe",
                       "action": "replace_invented"}],
        "c_enrich": [{"person": "person_j_coe", "name": "J. Coe", "action": "enrich"}],
        "c_unseen": [{"person": "person_j_poe", "name": "J. Poe", "action": "withdrawn"}]}}
    held("a person notice whose name the town does not hold",
         {**paper, "record_key": "c_new",
          "record": {**paper["record"], "kind": "person",
                     "normalized": "Be it ordained by the Board of Trustees"}},
         "the_press_name_is_a_person_the_town_does_not_hold",
         fn=lambda u: rule_newspapers(u, "1834-01-07", press))
    held("the marine journal", {**paper, "record": {**paper["record"], "kind": "shipping"}},
         "the_market_and_the_port_in_aggregate", fn=lambda u: rule_newspapers(u, "1835-06-20"))
    held("a notice naming nobody", paper, "the_column_names_nobody",
         fn=lambda u: rule_newspapers(u, "1835-06-10"))
    held("a notice naming somebody the register would replace",
         {**paper, "record_key": "c_replace",
          "record": {**paper["record"], "entities": [{"normalized": "George W. Snow"}]}},
         "the_press_name_replaces_an_invented_card",
         fn=lambda u: rule_newspapers(u, "1834-01-07", press))
    for label, key in (("a unit the register enriches is spent, not ruled", "c_enrich"),
                       ("a register action with no rule", "c_unseen"),
                       ("a claim the register carries nobody for", "c_absent")):
        try:
            rule_newspapers({**paper, "record_key": key,
                             "record": {**paper["record"],
                                        "entities": [{"normalized": "George W. Snow"}]}},
                            "1834-01-07", press)
            failures.append(f"{label}: was ruled rather than refused")
            print(f"  FAIL: {label}")
        except SystemExit:
            print(f"  ok:   {label} stops the build")
    ok_probe = is_dated_press_appearance(
        {**paper, "record": {**paper["record"],
                             "entities": [{"normalized": "George W. Snow"}]}}, "1834-01-07")
    if not ok_probe:
        failures.append("the probe does not agree that a named press claim is an appearance")
    print("  %s the probe and the rule agree on what a press appearance is"
          % ("ok:  " if ok_probe else "FAIL:"))

    church = {"source_file": "x/st_marys_baptisms_1833_1835.json",
              "record": {"id": "e1", "normalized": "George Beaubien", "describes_date": "1833-05-22",
                         "cells": {"role": "child"}, "notes": "Child of entry 1."}}
    # T-1337: AN APPEARANCE'S RULE IS ITS CROSSWALK'S OUTCOME, so these fixtures carry a
    # pre-seeded crosswalk index rather than reading the committed one. The point of each
    # case is the MAPPING, and a fixture standing on a real record would move the day that
    # record was re-adjudicated.
    ruled: dict = {}
    church_cache = {"church_crosswalk_index": ruled}

    def churched(label, outcome, want, **record):
        row = dict(church["record"], **record)
        ruled[row["id"]] = {"outcome": outcome, "crosswalk": "x/st_marys_crosswalk.json",
                            "name": "George Beaubien",
                            "rule": "stated verbatim by the crosswalk that looked"}
        held(label, {**church, "record": row}, want,
             fn=lambda u: rule_church(u, church_cache))

    held("a register child", church, "the_register_entry_names_kin",
         fn=lambda u: rule_church(u, church_cache))
    churched("a sponsor the crosswalk merged", "merged", None,
             cells={"role": "godmother"})
    churched("a sponsor the town does not hold", "no_candidate",
             "the_register_appearance_names_nobody_this_town_holds",
             id="e2", cells={"role": "godmother"})
    churched("a sponsor refused on the surname alone", "refused_surname_only",
             "the_register_appearance_identity_was_refused_in_the_crosswalk",
             id="e3", cells={"role": "godmother"})
    churched("a witness printed with no forename", "no_forename",
             "the_register_appearance_identity_was_refused_in_the_crosswalk",
             id="e4", cells={"role": "witness"})
    churched("a witness still standing as a candidate", "candidate",
             "the_register_appearance_identity_is_a_candidate_and_not_a_merge",
             id="e5", cells={"role": "witness"})
    churched("register prose that bounds the register", "ruled_no_town_change",
             "the_register_reading_is_about_the_town_and_not_a_person",
             id="p2", kind="person", cells={})
    churched("a town finding with nobody in it to crosswalk", "not_a_person",
             "the_register_reading_is_about_the_town_and_not_a_person",
             id="p3", kind="person", cells={})
    held("the roll beyond the window",
         {**church, "record": {**church["record"], "beyond_ticket_window": True,
                               "cells": {"role": "member"}}},
         "the_roll_is_beyond_the_reading_window",
         fn=lambda u: rule_church(u, church_cache))
    held("register prose about the town",
         {**church, "record": {"id": "p1", "kind": "civic", "normalized": "A civic note.",
                               "describes_date": "1834"}},
         "a_town_reading_with_no_record_to_write",
         fn=lambda u: rule_church(u, church_cache))
    # And an outcome nobody has written a rule for is a stop, not a nearest match.
    ruled["e9"] = {"outcome": "invented_outcome", "crosswalk": "x/st_marys_crosswalk.json"}
    try:
        rule_church({**church, "record": {**church["record"], "id": "e9",
                                          "cells": {"role": "godmother"}}}, church_cache)
        failures.append("an unmapped crosswalk outcome: was ruled anyway")
    except SystemExit:
        pass
    # An appearance no crosswalk has looked at is a stop too, for the same reason.
    try:
        rule_church({**church, "record": {**church["record"], "id": "e8",
                                          "cells": {"role": "godmother"}}}, church_cache)
        failures.append("an uncrosswalked appearance: was handed on anyway")
    except SystemExit:
        pass

    # T-1509: the four answers a business reading can get, each held over a fixture, and
    # the reach index held over the layer as it stands. The reach fixture is synthetic on
    # purpose -- the real claim ids move as the corpora are read, and a self-test pinned
    # to one of them goes red on work that is nothing to do with it.
    trade = {"source_file": "x/chicago_democrat_1835_01_21.json", "record_key": "c900",
             "record": {"id": "c900", "kind": "business", "normalized": "Iron and hardware.",
                        "business": {"name": "an iron and hardware stock"}}}
    held("a business the layer compiled a record from", trade,
         "the_compiled_record_names_this_claim_and_tiers_no_field_to_it",
         fn=lambda u: rule_business(u, {"c900": ["biz_fixture"]}, "1835-06-13"))
    held("a business notice printed after the scene date", trade,
         "the_issue_is_printed_after_the_scene_date",
         fn=lambda u: rule_business(u, {}, "1835-08-05"))
    held("a business reading of an earlier year",
         {**trade, "record": {**trade["record"], "describes_date": "1828"}},
         "the_reading_is_earlier_than_the_scene_and_does_not_reach_it",
         fn=lambda u: rule_business(u, {}, None))
    held("a business reading the layer holds no record for", trade,
         "a_trade_reading_the_business_layer_holds_no_record_for",
         fn=lambda u: rule_business(u, {}, "1835-06-13"))
    # THE RECORD OUTRANKS THE DATE, and that order is the ruling, not an accident of the
    # branch order: a post-scene printing the layer compiled a record from is the
    # record's question and not this register's (T-1508).
    if rule_business(trade, {"c900": ["biz_fixture"]}, "1835-08-05")[0] != \
            "the_compiled_record_names_this_claim_and_tiers_no_field_to_it":
        failures.append("a compiled record lost to the scene-date fallback")

    # ...and the reach index reads the layer that is committed, not one in a fixture.
    reach = business_claim_reach(ROOT)
    if not reach:
        failures.append("the business layer reaches no claim at all")
    else:
        unreached = [unit for unit in mine(ROOT)
                     if unit["record"].get("kind") == "business"
                     and not reach.get(unit["record_key"])]
        ruled = {rule_business(unit, reach, None)[0] for unit in unreached}
        if "the_compiled_record_names_this_claim_and_tiers_no_field_to_it" in ruled:
            failures.append("a unit no record reaches was handed to T-1514 anyway")

    book = {"source_file": "x/hubbard_autobiography_1911.json",
            "record": {"id": "b1", "kind": "landscape", "normalized": "The prairie.",
                       "describes_date": "1818"}}
    held("a ground reading, whatever its year", book,
         "a_ground_reading_describes_the_site_not_a_record", fn=rule_books)
    held("a price reading", {**book, "record": {**book["record"], "kind": "price"}},
         "the_market_and_the_port_in_aggregate", fn=rule_books)
    held("an earlier event", {**book, "record": {**book["record"], "kind": "event"}},
         "the_reading_is_earlier_than_the_scene_and_does_not_reach_it", fn=rule_books)
    held("an in-window civic reading",
         {**book, "record": {**book["record"], "kind": "civic", "describes_date": "1835-03"}},
         "a_town_reading_with_no_record_to_write", fn=rule_books)

    manifest = {"source_record_id": "carpenter_philo"}
    held("the pilot reservation", manifest, "the_manifest_is_a_reservation_and_not_a_reading",
         fn=lambda u: rule_residents(u, None, "a sampling manifest, not new evidence"))
    held("a declined candidate", manifest, "the_pass_named_a_candidate_and_did_not_assert_it",
         fn=lambda u: rule_residents(u, {"outcome": "candidate_identity", "summary": "s" * 50,
                                         "candidates": [{"name": "X", "assessment": "strong",
                                                         "asserted": False}]}, ""))
    held("a corroboration", manifest, "corroboration_confirms_and_moves_nothing",
         fn=lambda u: rule_residents(u, {"outcome": "corroborated", "summary": "s" * 50}, ""))
    # T-1301: one fixture per enrichment destination, each on a REAL adjudicated reading,
    # so the seven rules are held over the units they actually rule rather than over a
    # synthetic id that would route by default -- which this tool no longer allows.
    def enrichment(pass_no, person):
        return {"source_file": f"data/research/residents/pass_{pass_no}_x_cohort.json",
                "source_record_id": person}

    for label, pass_no, person, want in (
            ("a birth date", "04", "kimberly_edmund_s", "the_enrichment_names_a_birth_or_age_no_field_carries"),
            ("an arrival the card already carries", "04", "norton_nelson_r", "the_enrichment_dates_an_appearance_the_card_already_carries"),
            ("an arrival written onto the card", "02", "peck_philip", "the_enrichment_is_written_onto_the_card_it_names"),
            ("a departure", "04", "sweet_alanson", "the_enrichment_names_a_departure_from_chicago_no_field_carries"),
            ("a marriage", "08", "hobson_jesse", "the_enrichment_names_kin_no_field_carries"),
            # T-1469: one probe per outcome the trade pass can reach, because the rule a
            # trade enrichment falls under is now a reading of the card rather than a
            # constant, and a router that collapsed them all to one would look fine here.
            ("a trade the card carries", "02", "couch_ira", TRADE_CARRIED),
            ("a trade bounded outside the window", "04", "mason_matthias", TRADE_BOUNDED),
            ("a trade carried as a profile fact", "06", "mitchell_henry", TRADE_PROFILE),
            ("a trade printed for a later year", "14", "sabine_wm", TRADE_LATER),
            ("a pre-scene engagement", "04", "handy_major", TRADE_UNREACHED),
            ("a reading the card contradicts", "02", "pearsons_hiram", TRADE_HANDED),
            ("a county office", "04", "steele_ashbel", "the_enrichment_names_a_civic_church_or_school_post_no_field_carries"),
            ("a landholding", "05", "wright_john_s", "the_enrichment_names_a_landholding_no_field_carries"),
            ("a later volume", "15", "doolittle_ehjah", "the_later_volume_enriches_a_biography_and_names_no_1835_field")):
        held(f"an enrichment naming {label}", enrichment(pass_no, person), want,
             fn=lambda u: rule_residents(u, {"outcome": "corroborated_enrichment",
                                             "summary": "s" * 50}, ""))

    # An enrichment this tool never adjudicated must FAIL, not fall to a default. The whole
    # reason T-1301 exists is that one default pointer went stale and took 98 units with it.
    try:
        rule_residents(enrichment("02", "nobody_at_all"),
                       {"outcome": "corroborated_enrichment", "summary": "s" * 50}, "")
        failures.append("an unadjudicated enrichment: routed by default instead of failing")
    except SystemExit:
        pass

    # ...and the table must be exactly the corpus: no stale row, no unrouted reading.
    enrichment_units = {
        enrichment_key(unit) for unit in mine(ROOT)
        if unit["domain"] == "residents"
        and str((L.resident_finding(ROOT, unit) or {}).get("outcome") or "") not in
        ("candidate_identity", "corroborated")
        and L.resident_finding(ROOT, unit) is not None}
    for stale in sorted(set(ENRICHMENT_ROUTE) - enrichment_units):
        failures.append(f"ENRICHMENT_ROUTE holds {stale}, which is not an enrichment unit")
    for missing in sorted(enrichment_units - set(ENRICHMENT_ROUTE)):
        failures.append(f"{missing} is an enrichment with no adjudicated field")

    documents = build_documents()
    total = 0
    seen: set[str] = set()
    for domain, doc in documents.items():
        for row in doc["rulings"]:
            total += 1
            if row["unit"] in seen:
                failures.append(f"two rulings on one unit: {row['unit']}")
            seen.add(row["unit"])
            if len(row["note"].strip()) < 20:
                failures.append(f"{row['unit']}: carries no note")
            if not row["unit"].startswith(domain + ":"):
                failures.append(f"{row['unit']}: ruled in the {domain} register")
    unfired = sorted(set(RULES) - {rule for doc in documents.values() for rule in doc["counts"]})
    if unfired:
        failures.append("rules that never fire over the committed corpora: " + ", ".join(unfired))

    for line in failures:
        print(f"FAIL {line}")
    print(f"REMAINDER RULING SELF-TEST {'FAIL' if failures else 'PASS'} — "
          f"{len(failures)} failure(s), {len(RULES)} rule(s), {total} unit(s)")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="re-derive and prove nothing drifted")
    parser.add_argument("--self-test", action="store_true", help="hold the rules over the rows")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    documents = build_documents()
    if args.check:
        for domain, doc in documents.items():
            path = out_path(domain)
            if not path.exists():
                print(f"FAIL {path.relative_to(ROOT)} is missing — run tools/spend_remainder_rulings.py")
                return 1
            if read_json(path) != doc:
                print(f"FAIL {path.relative_to(ROOT)} is stale — run tools/spend_remainder_rulings.py")
                return 1
        if not args.quiet:
            total = sum(len(doc["rulings"]) for doc in documents.values())
            print(f"OK remainder rulings re-derive: {total} units across "
                  + ", ".join(f"{d} {len(doc['rulings'])}" for d, doc in documents.items()))
        return 0
    write(documents)
    for domain, doc in documents.items():
        print(f"wrote {out_path(domain).relative_to(ROOT)}: {len(doc['rulings'])} rulings")
        for rule, n in doc["counts"].items():
            print(f"  {n:5d}  {rule}  ({RULES[rule]['disposition']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
