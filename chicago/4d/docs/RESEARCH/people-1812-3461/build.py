# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3461: write the 1812 household cards from the research sweep beside this file.

The sweep (2026-11-07) is four readings, each fact carrying its source id, a locator and a
quote of 25 words or fewer checked against the text it names:

  garrison.json   Heald's company (muster-roll to 31 May 1812, Quaife 1913 App. VIII; fates
                  App. IX), the officers, the militia, the women and the children
  civilians.json  the Kinzie, Ouilmette, Burns and Lee households and those excluded
  native.json     the Potawatomi people the sources name, Wells and the Miami escort
  dress.json      dress references, read by the placement tickets (T-3462..T-3467)

This script only arranges what they read into the household shape compile_scene.py reads
(data/residents_1812/households/). It composes no fact: every sentence of a card's note is a
field of the reading (its role, its presence basis, its fate, its notes), and every source a
card cites is a source a fact of that person cites. The few things it decides are said here:

  * HOUSEHOLDS. Who lives with whom is the reading's (wife_of, child_of, the Kinzie and Burns
    households); which roof a soldier's family had is NOT in any source (garrison.json says so
    in every residence_basis), so those homes are `reconstructed` and the card says so.
  * GRADE is the grade of the PERSON, not of the story: `attested` when a source names or
    counts the person by their place in a family or a roll; `inferred` where the identity is
    the researcher's or Quaife's deduction (marked in INFERRED below with the reason);
    `reconstructed` only for the rows minted for people a source counts and nobody names.
  * PRESENCE on the afternoon of 14 August is carried as `present_on_scene_date` on the
    person, from the reading's own status.
  * Anyone the readings put dead or gone before 14 August (Lalime, Liberty White, Cardin,
    the Mirandeaus, Irwin, Jouett, Caldwell, Shabbona, the Healds' stillborn son) is not
    carded; the household notes and the README name them.

Run from chicago/4d:  python3 docs/RESEARCH/people-1812-3461/build.py [--check]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'data/residents_1812/households'
SOURCES = ROOT / 'data/sources'

G = {p['id']: p for p in json.loads((HERE / 'garrison.json').read_text())['persons']}
C = {p['id']: p for p in json.loads((HERE / 'civilians.json').read_text())['persons']}
N = {p['id']: p for p in json.loads((HERE / 'native.json').read_text())['persons']}

COMPANY = "Captain Nathan Heald's company of the First Regiment of Infantry"
ROLL = 'the muster-roll of the company to 31 May 1812 (Quaife 1913, Appendix VIII)'

# Identities that are a deduction rather than a naming, with why.
INFERRED = {
    'holt_child': 'Quaife counts a child returned with Mrs. Holt; the reading takes it as hers, which no source states outright.',
    'fettle_louis': "Quaife's conjecture only: in Kinzie's books down to 1812, then gone; he guesses Fettle died among the militia.",
    'lee_son': "Wau-Bun has Lee's son killed with him; that he served in the militia is Quaife's inference.",
}

# Presence wording.
PRESENCE = {
    'present': 'present', 'probably_present': 'probably present', 'unknown': 'not documented',
    'uncertain': 'not documented', 'conflicting': 'not documented',
}


def fact_list(p):
    out = []
    for f in p.get('facts') or []:
        sid = f.get('source_id') or f.get('source')
        if not sid:
            continue
        e = {'source_id': sid, 'locator': f.get('locator'), 'quote': f.get('quote')}
        if f.get('claim'):
            e['claim'] = f['claim']
        if f.get('tier'):
            e['tier'] = f['tier']
        out.append(e)
    return out


# Sentences of a reading that speak to the reading itself (who else covered a person, a line
# in a local text file) are the researcher's, not the person's; they stay in the JSON beside
# this file and out of the card.
META = re.compile(r'researcher|pg\d+\.txt|\blines? \d|Do not render|handle with care|see facts', re.I)
PLACEHOLDER = {
    'Named by a source as in the battle or among its survivors/captives (see facts).':
        'An account of the battle or of its captives names him, so he was with the garrison when it marched.',
}


def clean(text):
    text = PLACEHOLDER.get(str(text or '').strip(), text)
    keep = [s for s in re.split(r'(?<=[.;])\s+(?=[A-Z])', re.sub(r'\s+', ' ', str(text or '')).strip()) if s and not META.search(s)]
    return ' '.join(keep)


def sentence(s):
    s = clean(s)
    if not s:
        return ''
    s = s[0].upper() + s[1:]
    return s if s[-1] in '.!?' or s[-2:] in ('."', ".'") else s + '.'


def year_of(v):
    m = re.search(r'\b(1[6-8]\d\d)\b', str(v or ''))
    return m.group(1) if m else None


class Card:
    def __init__(self, pid, name, relationship, refs, *, grade=None, note_lead='', home_note=None,
                 occupation=None, born=None, presence=None, extra_sources=(), review=None, minted=None):
        self.pid, self.name, self.relationship = pid, name, relationship
        self.refs = refs                       # [(dict, record), ...]
        self.grade, self.note_lead, self.home_note = grade, note_lead, home_note
        self.occupation, self.born, self.presence = occupation, born, presence
        self.extra_sources = list(extra_sources)
        self.review, self.minted = review, minted

    def evidence(self):
        seen, out = set(), []
        for _, r in self.refs:
            for e in fact_list(r):
                k = (e['source_id'], e['locator'], e['quote'])
                if k not in seen:
                    seen.add(k)
                    out.append(e)
        return out

    def sources(self):
        ids = [e['source_id'] for e in self.evidence()] + self.extra_sources
        return sorted(dict.fromkeys(ids))

    def record(self):
        first = self.refs[0][1] if self.refs else {}
        parts = [self.note_lead]
        status = self.presence
        for i, (kind, r) in enumerate(self.refs):
            if i and kind == 'n':
                parts.append(r.get('part_15_16_aug') and ('15 and 16 August: ' + re.sub(r'^15th: ', '', r['part_15_16_aug'])))
                continue
            if i:
                continue          # a second reading of the same person adds its evidence, not its prose
            if kind == 'g':
                if (r.get('enlistment') or {}).get('date'):
                    en = r['enlistment']
                    parts.append(f"On {ROLL}, enlisted {en['date']} for five years, to {en['term_to']}"
                                 + (f"; the roll remarks: {en['roll_remark']}" if en.get('roll_remark') else '') + '.')
                parts.append(r.get('presence_basis'))
                parts.append(r.get('notes'))
                if r.get('fate'):
                    parts.append('After 14 August: ' + r['fate'])
                status = status or r.get('presence_14aug1812')
            elif kind == 'c':
                pr = r.get('present_14aug') or {}
                parts.append(r.get('occupation') and f"{sentence(r['occupation'])}")
                anc = (r.get('ancestry') or {}).get('value') if isinstance(r.get('ancestry'), dict) else None
                if anc:
                    parts.append(f'Ancestry as the sources put it: {anc}.')
                parts.append(pr.get('summary'))
                if r.get('fate'):
                    parts.append('After 14 August: ' + r['fate'])
                status = status or pr.get('status')
            elif kind == 'n':
                parts.append(sentence(r.get('role')))
                parts.append(sentence(r.get('nation_band')))
                parts.append(r.get('presence_evidence'))
                parts.append(r.get('part_15_16_aug') and ('15 and 16 August: ' + re.sub(r'^15th: ', '', r['part_15_16_aug'])))
                if r.get('fate'):
                    parts.append('Afterwards: ' + r['fate'])
                status = status or r.get('present_14_aug')
        if self.home_note:
            parts.append(self.home_note)
        if self.grade == 'inferred' and self.pid in INFERRED:
            parts.append(INFERRED[self.pid])
        note = ' '.join(sentence(p) for p in parts if p and str(p).strip())
        rec = {
            'id': self.pid,
            'name': self.name,
            'relationship': self.relationship,
            'grade': self.grade or ('inferred' if self.pid in INFERRED else 'attested'),
            'sources': self.sources(),
        }
        if self.born:
            rec['born'] = self.born
        if self.occupation:
            rec['occupation'] = self.occupation
        rec['present_on_scene_date'] = {
            'value': PRESENCE.get(status, 'not documented'),
            'confidence': 'inferred',
            'note': 'Presence on the afternoon of 14 August 1812, read from the evidence below; no source takes a roll call that afternoon.',
        }
        aka = []
        for kind, r in self.refs:
            aka += r.get('other_spellings') or []
            if kind == 'n':
                aka += [n for n in r.get('names', [])[1:]]
        if aka:
            rec['also_written'] = list(dict.fromkeys(a for a in aka if a and a != self.name))
        rec['note'] = note
        if self.review:
            rec['review_required'] = True
            rec['touches_removal'] = self.review.get('touches_removal', False)
            rec['review_note'] = self.review['note']
        if self.minted:
            rec['reconstruction'] = self.minted
        rec['evidence'] = self.evidence()
        return rec


def born_g(r):
    a = r.get('age_or_birth') or {}
    y = a.get('birth_year') or a.get('birth') or a.get('birth_year_approx')
    if not y:
        return None
    srcs = sorted({f['source_id'] for f in r['facts'] if str(y) in (f.get('quote') or '') or 'orn' in (f.get('claim') or '')}) or ['quaife_1913']
    return {'value': str(y), 'confidence': 'inferred', 'sources': srcs,
            'note': f"{a.get('basis') or 'As the source gives it'}{'; born in ' + a['place'] if a.get('place') else ''}. A year from a later family account, not a register."}


def born_c(r):
    b = r.get('birth') or {}
    y = year_of(b.get('value'))
    if not y:
        return None
    srcs = sorted({f['source'] for f in r.get('facts') or [] if 'born' in (f.get('claim') or '').lower() or y in (f.get('quote') or '')})
    return {'value': str(b['value']), 'confidence': 'attested' if str(b.get('grade', '')).startswith('attested') and srcs else 'inferred',
            'sources': srcs or sorted({f['source'] for f in r.get('facts') or []})[:1],
            'note': b.get('note') or 'As the source gives it.'}


def occ(value, sources, note, confidence='attested'):
    return {'value': value, 'confidence': confidence, 'sources': sources, 'note': note}


def rank_occ(r):
    rank = re.sub(r'\s*\(.*?\)', '', (r.get('rank_role') or 'Private').split(';')[0]).replace(', commanding', ' commanding the post')
    return occ(f"{rank.lower()}, {COMPANY}", ['quaife_1913'],
               f"His rank as {ROLL} prints it.")


def soldier(gid, relationship='soldier', **kw):
    r = G[gid + '_1812']
    name = kw.pop('name', None) or r['name_as_printed']
    return Card(gid, name, relationship, [('g', r)], occupation=rank_occ(r), born=born_g(r), **kw)


FORT_HOME_NOTE = ("No source says which room of the fort any soldier or soldier's family lived in; the "
                  "barracks named here is the reconstructed choice (liberty L-1812-people-3461).")

REVIEW_NATIVE = ("review_required: a Potawatomi person of the gathering at Chicago in August 1812, the eve of "
                 "the battle in which the garrison and its families were attacked. The card states only what the "
                 "named sources say, says where a story is Kinzie family tradition rather than a contemporary "
                 "account, and stages no speech or ceremony.")
REVIEW_OUILMETTE = ("review_required: a Potawatomi woman (Currey) married to a French trader, whose household "
                    "stayed through the battle. The card states only what the named sources say.")


def households():
    H = []

    def hh(hid, name, head, division, persons, homes, note_out, present_note, review=None):
        H.append({'hid': hid, 'name': name, 'head': head, 'division': division, 'persons': persons,
                  'homes': homes, 'not_in': note_out, 'present_note': present_note, 'review': review})

    # --- the commanding officer
    hh('hh_heald_nathan_1812', "Captain Nathan Heald's household in the commanding officer's quarters", 'heald_nathan', 'fort',
       [soldier('heald_nathan', 'head', name='Nathan Heald'),
        Card('heald_rebekah', 'Rebekah Wells Heald', 'wife', [('g', G['heald_rebekah_1812'])], born=born_g(G['heald_rebekah_1812'])),
        Card('cicely', 'Cicely', 'enslaved', [('g', G['cicely_1812'])],
             note_lead="Enslaved by the Healds; the sources call her Mrs. Heald's servant or slave and give her no other name.",
             review={'note': 'review_required: ' + G['cicely_1812']['review_reason']}),
        Card('cicely_son', "Cicely's son", 'son', [('g', G['cicely_son_1812'])],
             note_lead="Cicely's infant son; no source names him.",
             review={'note': 'review_required: an enslaved child, named by no source; see his mother\'s card.'})],
       [('first_fort_dearborn_commanding_officers_barracks', 'inferred', ['whistler_1808_fort_dearborn_draught', 'quaife_1913'],
         "Whistler's index names the commanding officer's barracks; that the Healds lived in it in 1812 is inferred from his command, and Wau-Bun's Black Partridge enters 'the quarters of the commanding officer'.")],
       "The Healds' son, stillborn on 4 May 1812 (Heald's journal), died before the scene date and has no card.",
       "Heald commanded the post until the evacuation on 15 August (his own report, Quaife App. IV).")

    hh('hh_helm_linai_1812', "Lieutenant Linai T. Helm and Margaret Helm in the officers' barracks", 'helm_linai', 'fort',
       [soldier('helm_linai', 'head', name='Linai T. Helm'),
        Card('helm_margaret', 'Margaret Helm', 'wife', [('g', G['helm_margaret_1812']), ('c', C['helm_margaret'])],
             born=born_c(C['helm_margaret']),
             note_lead="Eleanor Kinzie's daughter by her first marriage (to McKillip), married to Lieutenant Helm.")],
       [('first_fort_dearborn_officers_barracks', 'reconstructed', ['whistler_1808_fort_dearborn_draught'],
         "Whistler's index names an officers' barracks; which officer had which room is not recorded.")],
       '', "Helm wrote his own account of the evacuation in 1814 (Quaife App. VI).")

    for gid, nm, title in [('ronan_george', 'George Ronan', 'Ensign George Ronan'),
                           ('vanvoorhis_isaac', 'Isaac Van Voorhis', "Surgeon's mate Isaac Van Voorhis")]:
        pid = 'van_voorhis_isaac' if gid.startswith('vanvoorhis') else gid
        c = soldier(gid, 'head', name=nm)
        c.pid = pid
        hh(f'hh_{pid}_1812', f"{title} in the officers' barracks", pid, 'fort', [c],
           [('first_fort_dearborn_officers_barracks', 'reconstructed', ['whistler_1808_fort_dearborn_draught'],
             "An officer of the post; which room he had is not recorded.")],
           '', 'On the 31 May 1812 roll of the post\'s officers.')

    # --- married soldiers
    fam = [
        ('hh_holt_isaac_1812', 'The Holt family', 'holt_isaac', [('holt_mrs', 'Mrs. Holt', 'wife'), ('holt_child', 'The Holt child', 'child')], 'first_fort_dearborn_small_house_sw'),
        ('hh_simmons_john_1812', 'The Simmons family', 'simmons_john', [('simmons_susan_millhouse', 'Susan Millhouse Simmons', 'wife'), ('simmons_david', 'David Simmons', 'son'), ('simmons_susan', 'Susan Simmons', 'daughter')], 'first_fort_dearborn_small_house_ne'),
        ('hh_corbin_fielding_1812', 'The Corbin family', 'corbin_fielding', [('corbin_mrs', 'Mrs. Corbin', 'wife')], 'first_fort_dearborn_soldiers_barracks_sw'),
        ('hh_needs_john_1812', 'The Needs family', 'needs_john', [('needs_mrs', 'Mrs. Needs', 'wife'), ('needs_child', 'The Needs child', 'child')], 'first_fort_dearborn_soldiers_barracks_se'),
    ]
    for hid, nm, head, members, home in fam:
        people = [soldier(head, 'head')]
        for pid, pname, rel in members:
            r = G[pid + '_1812']
            people.append(Card(pid, pname, rel, [('g', r)], born=born_g(r)))
        hh(hid, f'{nm} of Heald\'s company, in the fort', head, 'fort', people,
           [(home, 'reconstructed', ['whistler_1808_fort_dearborn_draught'], FORT_HOME_NOTE)],
           'A child the counts of 18 do not name may have been of this family; those children have their own reconstructed cards (hh_garrison_children_unnamed_1812).',
           "The family's men, women and children are on Helm's and Heald's lists of 1812-1814 (Quaife App. IV, VI).")

    # --- the company's other men
    family_heads = {'heald_nathan', 'helm_linai', 'ronan_george', 'vanvoorhis_isaac', 'holt_isaac', 'simmons_john', 'corbin_fielding', 'needs_john'}
    company = []
    for gid, r in G.items():
        b = gid[:-5]
        if r.get('group') == 'garrison_regular' and b not in family_heads:
            company.append(soldier(b))
    hh('hh_heald_company_1812', "The men of Heald's company in the soldiers' barracks", 'holt_isaac' if False else company[0].pid, 'fort', company,
       [('first_fort_dearborn_soldiers_barracks_sw', 'reconstructed', ['whistler_1808_fort_dearborn_draught'], FORT_HOME_NOTE),
        ('first_fort_dearborn_soldiers_barracks_se', 'reconstructed', ['whistler_1808_fort_dearborn_draught'], FORT_HOME_NOTE),
        ('first_fort_dearborn_north_range', 'reconstructed', ['whistler_1808_fort_dearborn_draught'], FORT_HOME_NOTE)],
       'The officers and the four married men have their own family cards. Thomas Forth\'s enlistment ran out on 6 July 1812; no discharge is recorded, so he is carded with the presence he was read with.',
       "All 51 enlisted men of the roll are taken as at the post on 14 August: no discharge, desertion or detachment is recorded after 31 May, and Quaife sees 'no reason to suppose that there was any alteration in this number' (App. IX).")

    # --- militia households
    hh('hh_burns_thomas_1812', 'Thomas Burns and his family at the Burns house', 'burns_thomas', 'north',
       [Card('burns_thomas', 'Thomas Burns', 'head', [('g', G['burns_thomas_1812']), ('c', C['burns_thomas'])],
             occupation=occ('sergeant of the Chicago militia', ['quaife_1913'], 'The militia Heald enrolled after the April murders (Quaife ch. X, App. IX).')),
        Card('burns_mrs', 'Mrs. Burns', 'wife', [('g', G['burns_mrs_1812']), ('c', C['burns_mrs'])]),
        Card('cooper_joseph', 'Joseph (or James) Cooper', 'stepson', [('g', G['cooper_joseph_or_james_1812']), ('c', C['cooper_joseph'])]),
        Card('cooper_isabella', 'Isabella Cooper', 'stepdaughter', [('g', G['cooper_isabella_1812']), ('c', C['cooper_isabella'])], born=born_c(C['cooper_isabella'])),
        Card('burns_infant', 'The Burns baby', 'daughter', [('g', G['burns_infant_1812']), ('c', C['burns_infant'])], born=born_c(C['burns_infant'])),
        Card('burns_child_a', 'A child of Mrs. Burns, name not recorded', 'child', [('g', G['burns_child_killed_a_1812'])]),
        Card('burns_child_b', 'A second child of Mrs. Burns, name not recorded', 'child', [('g', G['burns_child_killed_b_1812'])])],
       [('burns_house_1812', 'inferred', ['quaife_1913'], 'The Burns house on the north bank, as the 1812 structure record places it.')],
       '', 'In the fort from the April alarm, with the other civilian families (Quaife ch. X).')

    hh('hh_lee_charles_1812', 'Charles Lee and his family at the Lee house by the river mouth', 'lee_charles', 'south',
       [Card('lee_charles', 'Charles Lee', 'head', [('c', C['lee_charles']), ('g', G['lee_mr_1812'])],
             occupation=occ('farmer of Lee\'s Place (Hardscrabble)', ['quaife_1913'], 'His farm on the South Branch, where Liberty White and Jean Baptiste Cardin were killed on 6 April 1812.', 'inferred')),
        Card('lee_mrs', 'Mrs. Lee', 'wife', [('c', C['lee_mrs']), ('g', G['lee_mrs_1812'])]),
        Card('lee_son', "Lee's son", 'son', [('c', C['lee_son']), ('g', G['lee_son_1812'])], grade='inferred'),
        Card('lee_daughter', "Lee's daughter", 'daughter', [('c', C['lee_daughter']), ('g', G['lee_daughter_1812'])], born=born_c(C['lee_daughter'])),
        Card('lee_infant', 'The Lee baby', 'child', [('c', C['lee_infant']), ('g', G['lee_infant_1812'])])],
       [('lee_house_1812', 'inferred', ['kinzie_waubun_1856', 'currey_1912_story_of_old_fort_dearborn'], 'The family\'s town house on the lake shore near the fort (Wau-Bun ch. XIX).')],
       'Liberty White and Jean Baptiste Cardin, killed at Lee\'s Place on 6 April 1812, died before the scene date. Russell, said to be Lee\'s partner, is not placed at Chicago in August by any source read.',
       'In the fort from the April alarm (Quaife ch. X).')

    # --- the Kinzie household (the elder's card is kept as written; the family joins it)
    K = [('kinzie_eleanor', 'Eleanor Kinzie', 'wife'), ('kinzie_john_h', 'John Harris Kinzie', 'son'),
         ('kinzie_ellen_marion', 'Ellen Marion Kinzie', 'daughter'), ('kinzie_maria_indiana', 'Maria Indiana Kinzie', 'daughter'),
         ('kinzie_robert_allen', 'Robert Allen Kinzie', 'son'), ('laframboise_josette', 'Josette LaFramboise', 'servant'),
         ('chandonnai_jean_baptiste', 'Jean Baptiste Chandonnai', 'clerk'), ('black_jim', 'Black Jim', 'servant'),
         ('leclerc_pierre', 'Pierre Le Clerc', 'employee')]
    kin = []
    for cid, nm, rel in K:
        refs = [('c', C[cid])]
        if cid == 'chandonnai_jean_baptiste':
            refs.append(('n', N['jean_baptiste_chandonnai_1812']))
        if cid == 'leclerc_pierre':
            refs += [('n', N['pierre_leclerc_1812']), ('g', G['leclaire_pierre_1812'])]
        pid = {'kinzie_john_h': 'kinzie_john_h_1812', 'laframboise_josette': 'laframboise_josette_1812'}.get(cid, cid)
        kin.append(Card(pid, nm, rel, refs, born=born_c(C[cid]),
                        grade='inferred' if cid == 'leclerc_pierre' else None))
    kin.append(Card('kinzie_servant_second', 'A second Kinzie servant, name not recorded', 'servant', [('c', C['kinzie_servant_second'])]))
    H.append({'hid': 'hh_kinzie_john_elder', 'extend': kin})

    hh('hh_ouilmette_antoine_1812', "Antoine Ouilmette's household at his house west of the Kinzies", 'ouilmette_antoine', 'north',
       [Card('ouilmette_antoine', 'Antoine Ouilmette', 'head', [('c', C['ouilmette_antoine'])]),
        Card('ouilmette_archange', 'Archange Ouilmette', 'wife', [('c', C['ouilmette_archange'])],
             review={'note': REVIEW_OUILMETTE}),
        Card('bisson_mrs', 'Mrs. Bisson', 'household_member', [('c', C['bisson_mrs'])],
             note_lead="Archange Ouilmette's sister."),
        Card('ouilmette_children', 'The Ouilmette children', 'children', [('c', C['ouilmette_children_1812'])],
             note_lead='One row for the children of the house, who are counted and not named for 1812.')],
       [('ouilmette_house_1812', 'inferred', ['kinzie_waubun_1856'], "The house the 1812 structure record calls Ouilmette's; the sources differ on whether it stood north, behind or west of the Kinzie house (civilians.json notes).")],
       '', 'The household stayed through the battle (Wau-Bun; Quaife).',
       review=REVIEW_OUILMETTE)

    # --- people of other places at the post
    hh('hh_wells_william_1812', 'Captain William Wells, come from Fort Wayne with a Miami escort', 'wells_william', 'fort',
       [Card('wells_william', 'William Wells', 'head', [('n', N['william_wells_1812'])],
             note_lead="Rebekah Heald's uncle, Indian agent and interpreter at Fort Wayne.")],
       [], "His Miami escort of about thirty men is named by no source; T-3467 gives them reconstructed cards when it places them.",
       'He reached the post on 12, 13 or 14 August depending on the source (native.json); every account has him there for the evacuation.')

    # --- Potawatomi people the sources name
    named = ['black_partridge', 'winnemeg', 'waubansee', 'topenebe', 'blackbird', 'nuscotnemeg', 'keepotah',
             'peesotum', 'naunongee']
    for nid in named:
        r = N[nid + '_1812']
        hh(f'hh_{nid}_1812', f"{r['names'][0]}, at the gathering of August 1812", nid, 'camp',
           [Card(nid, r['names'][0], 'head', [('n', r)], review={'note': REVIEW_NATIVE, 'touches_removal': True})],
           [], 'No source names his family or places his lodge in the camp.', '', review=REVIEW_NATIVE)
    r, w = N['waubeeneemah_1812'], N['wife_of_waubeeneemah_1812']
    hh('hh_waubeeneemah_1812', "Wau-bee-nee-mah's lodge by the creek", 'waubeeneemah', 'camp',
       [Card('waubeeneemah', 'Wau-bee-nee-mah', 'head', [('n', r)], review={'note': REVIEW_NATIVE, 'touches_removal': True}),
        Card('waubeeneemah_wife', 'The wife of Wau-bee-nee-mah', 'wife', [('n', w)],
             note_lead='Wau-Bun gives her no name of her own.', review={'note': REVIEW_NATIVE, 'touches_removal': True})],
       [('potawatomi_camp_1812_mouth', 'inferred', ['kinzie_waubun_1856'],
         "Wau-Bun puts his wigwam beside the stream 'along the present State Street', the creek the camp records follow; which lodge is not said.")],
       '', '', review=REVIEW_NATIVE)
    hh('hh_main_poc_runner_1812', "A runner from Main Poc", 'main_poc_runner', 'camp',
       [Card('main_poc_runner', 'A runner from Main Poc, name not recorded', 'head', [('n', N['main_poc_runner_1812'])],
             review={'note': REVIEW_NATIVE, 'touches_removal': True})],
       [], '', '', review=REVIEW_NATIVE)

    # --- people a source counts and nobody names: reconstructed rows
    mil = []
    for i in range(1, 7):
        mil.append(Card(f'chicago_militia_unnamed_{i}', f'A man of the Chicago militia, name not recorded ({i} of 6)', 'militiaman', [],
                        grade='reconstructed', extra_sources=['quaife_1913'],
                        note_lead=("Heald enrolled fifteen men of the settlement as militia after the April murders and three deserted; "
                                   "twelve marched on 15 August (Quaife, App. IX). Burns, Cooper, Lee and Lee's son are named, and Fettle and "
                                   "Le Clerc only by Quaife's guess, so at least six of the twelve have no name in any source. This card stands "
                                   "for one of them: that he lived, served and was at the post is the count's; everything else about him is reconstructed."),
                        minted={'stage': 'counted_unnamed', 'counted_by': 'quaife_1913', 'ticket': 'T-3461', 'liberty': 'L-1812-people-3461'},
                        presence='present'))
    hh('hh_chicago_militia_unnamed_1812', 'The unnamed men of the Chicago militia', mil[0].pid, 'fort', mil, [],
       'A name found for any of these men retires one card.', 'Counted in the twelve militia of 15 August (Quaife App. IX).')

    kids = []
    for i in range(1, 8):
        kids.append(Card(f'garrison_child_unnamed_{i}', f'A child of the post, name not recorded ({i} of 7)', 'child', [],
                         grade='reconstructed', extra_sources=['quaife_1913'],
                         note_lead=("Woodward and Quaife count eighteen children with the evacuation (Helm's list reads 15 in Quaife's "
                                    "transcription and 18 in Gordon's); eleven can be put to a family by name, so seven are counted and unnamed, "
                                    "most likely more Lee, Burns, Holt or Needs children. This card stands for one of them; the family, age and "
                                    "name are not known."),
                         minted={'stage': 'counted_unnamed', 'counted_by': 'quaife_1913', 'ticket': 'T-3461', 'liberty': 'L-1812-people-3461'},
                         presence='present'))
    hh('hh_garrison_children_unnamed_1812', "The children of the post whom no source names", kids[0].pid, 'fort', kids, [],
       'A name or family found for any child retires one card.', 'Counted with the eighteen children of 15 August (Quaife App. IX).')
    return H


def write(check=False):
    known = {p.stem for p in SOURCES.glob('*.json')}
    out = {}
    for h in households():
        if 'extend' in h:
            path = OUT / f"{h['hid']}.json"
            rec = json.loads(path.read_text())
            keep = [p for p in rec['persons'] if p['id'] == rec['head']]
            rec['persons'] = keep + [c.record() for c in h['extend']]
            rec['not_in_this_household'] = {
                'note': ("The Kinzie household on the afternoon of 14 August 1812, from the T-3461 sweep (docs/RESEARCH/people-1812-3461/). "
                         "The family had been in the fort since the April alarm (Andreas p. 74). Kinzie's boatmen and engagés, and the 'Frenchmen' of "
                         "the lodging house, are counted by no source and named by none, so they have no card; Henry and Pero, sometimes named as "
                         "servants, are in none of the six works read. Margaret Helm, Eleanor's daughter, is on her husband's card."),
                'sources': ['kinzie_waubun_1856', 'andreas_1884_v1', 'quaife_1913']}
            out[path.name] = rec
            continue
        persons = [c.record() for c in h['persons']]
        cited = sorted({s for p in persons for s in p['sources']})
        rec = {'id': h['hid'], 'scene': '1812', 'name': h['name'], 'head': h['head'], 'division': h['division']}
        if h.get('review'):
            rec['review_required'] = True
            rec['touches_removal'] = h['hid'] != 'hh_ouilmette_antoine_1812'
            rec['review_note'] = h['review']
        rec['present_on_scene_date'] = {'value': 'present', 'confidence': 'inferred', 'sources': cited[:4],
                                        'note': h['present_note'] or 'Each person\'s own card says how their presence on 14 August is known.'}
        rec['associated_with'] = [{'kind': 'home', 'place_or_structure_id': sid, 'resolves_to': 'structure', 'from': None, 'to': None,
                                   'tier': tier, 'source_id': srcs[0], 'also_sources': srcs[1:], 'note': note}
                                  for sid, tier, srcs, note in h['homes']]
        rec['not_in_this_household'] = {'note': h['not_in'] or 'Everyone the T-3461 sweep found in this household on 14 August is on the card.',
                                        'sources': cited[:3]}
        rec['persons'] = persons
        out[f"{h['hid']}.json"] = rec
    faults = []
    for name, rec in out.items():
        for p in rec['persons']:
            for s in p.get('sources', []) + [x for b in ('born', 'occupation') for x in (p.get(b) or {}).get('sources', [])]:
                if s not in known:
                    faults.append(f'{name}: {p["id"]} cites {s}, which has no record')
    if faults:
        raise SystemExit('\n'.join(sorted(set(faults))))
    stale = []
    for name, rec in out.items():
        text = json.dumps(rec, indent=2, ensure_ascii=False) + '\n'
        path = OUT / name
        if check:
            if not path.exists() or path.read_text() != text:
                stale.append(name)
        else:
            path.write_text(text)
    if check and stale:
        raise SystemExit('stale 1812 household cards (rerun build.py): ' + ', '.join(stale))
    n = sum(len(r['persons']) for r in out.values())
    print(f'{len(out)} households, {n} people' + (' — current' if check else ' written'))


if __name__ == '__main__':
    write(check='--check' in sys.argv)
