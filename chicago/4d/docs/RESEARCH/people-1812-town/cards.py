# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3463..T-3467: cards for the people of the 1812 town whom the T-3461 sweep left uncarded.

T-3461 carded the people of 14 August 1812 (docs/RESEARCH/people-1812-3461/build.py) and left
out anyone dead or gone before that day. The owner, 2026-11-08: *"if we set to winter lalime
would exist and we will need him for the murder jaunt"*; the town now runs on its other dates
too (Settings > Season, the jaunts), so the day readings beside this file
(docs/RESEARCH/people-1812-34NN/day.json) add the people who were there on them, and the
representative people of the August gathering whom no roll names. Each such person is a
`new:` row of a reading, with a `card` block (household, relationship, grade, note) and facts
that carry a source id, a locator and a quote.

This script only arranges those rows into the household shape compile_scene.py reads, in NEW
household files (data/residents_1812/households/hh_*_1812.json, the ones listed in HOUSEHOLDS);
it never edits a file build.py writes. It composes no fact: a card's note is the reading's own
card note, presence basis and role. What it decides, said here:

  * HOUSEHOLDS. A reading that suggests joining a T-3461 household (the Kinzie engagés, Lee's
    farm hands, the Mirandeau girls at Ouilmette's) gets a household of its own instead, so the
    two scripts never write one file; the home is where the reading puts them indoors most.
  * PRESENCE on the afternoon of 14 August is the reading's own status (absent for Lalime,
    Irwin, the Mirandeaus, White and Cardin, who were dead or gone by then); their presence
    window is in their instance's behaviour.presence and their card's note.
  * EVIDENCE cites only sources with a record under data/sources; a fact citing anything else
    is left in the reading and named on the run.
  * Louis Fettle is not carded: Quaife's guess is all there is, and his cabin is not drawn.

Liberty L-1812-town-days-3463 (who is put in which household, and its home, where a source does
not say).

Run from chicago/4d:  python3 docs/RESEARCH/people-1812-town/cards.py [--check]
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
READINGS = [ROOT / f'docs/RESEARCH/people-1812-{t}/day.json' for t in (3463, 3464, 3465, 3466, 3467)]
LIBERTY = 'L-1812-town-days-3463'
SKIP = {'fettle_louis'}

REVIEW_REP = ("review_required: a person drawn to stand for the families of the Potawatomi gathering at Chicago in "
              "August 1812, whom no roll names or counts lodge by lodge. touches_removal: these are the people removed "
              "from Chicago in 1835. The card invents no name, band or story and stages no speech, ceremony or act of war.")
REVIEW_MIAMI = ("review_required: a Miami man drawn to stand for the escort William Wells brought from Fort Wayne, whom no "
                "source names. The card invents no name or story and stages no speech, ceremony or act of war.")

# household id -> (name, head, division, home structure or None, home tier, home note, review note or None)
HOUSEHOLDS = {
    'hh_lalime_john_1812': ("Jean Lalime at his house by the fort", 'lalime_john', 'north', 'lalime_house_1812', 'inferred',
                            "The house the 1812 structure record calls Lalime's.", None),
    'hh_irwin_matthew_1812': ("Matthew Irwin, factor, at the government factory", 'irwin_matthew', 'south', 'first_fort_outer_factory', 'inferred',
                              "The United States factory outside the fort, which he kept until he left on 5 July 1812.", None),
    'hh_mirandeau_1812': ("Jean Baptiste Mirandeau and his daughters, lodging at the Ouilmette house", 'mirandeau_jean_baptiste', 'north',
                          'ouilmette_house_1812', 'attested',
                          "Victoire Mirandeau (Andreas p. 105): 'some of us lived in the Ouilmette house, across the river from the fort'.",
                          "review_required: a Métis family of an Ottawa mother, depicted through the French household they lodged in; dress and looks are reconstructed and say so."),
    'hh_lees_place_1812': ("The men at Lee's Place on the South Branch", 'white_liberty', 'south', 'lees_place_cabin_1812', 'inferred',
                           "Lee's farm, where Liberty White had charge and he and Cardin were killed on 6 April 1812 (Quaife ch. X).", None),
    'hh_kinzie_engages_1812': ("John Kinzie's engagés, at the lodging house by his", 'kinzie_boatman_1812', 'north', 'kinzie_lodging_house_1812',
                               'reconstructed', "Wau-Bun's lodging house 'for the Frenchmen' beside the Kinzie house; which men slept there is not said.", None),
    'hh_miami_escort_1812': ("The Miami escort William Wells brought from Fort Wayne", 'miami_escort_1812_01', 'fort', 'first_fort_outer_stable_south',
                             'reconstructed',
                             "A bivouac in the open outside the fort, by the stables where their ponies (Currey: 'mounted on ponies') could be "
                             "kept; where they camped is not recorded. Put at the south stable until the escort's own camp ground is drawn.",
                             REVIEW_MIAMI),
}
for ground, nm in (('mouth', 'the creek mouth'), ('middle', 'the middle of the creek'), ('west_bank', 'the west bank'),
                   ('south_reach', 'the south reach'), ('upper', 'the upper creek')):
    HOUSEHOLDS[f'hh_potawatomi_camp_{ground}_1812'] = (
        f"The families at the camp's ground by {nm} (names not recorded)", None, 'camp', f'potawatomi_camp_1812_{ground}',
        'reconstructed', "The camp ground of the 1812 camp records; which lodge each family had is not recorded.", REVIEW_REP)

PLACE = {'kinzie_boatman_1812': 'hh_kinzie_engages_1812', 'kinzie_engage_1812': 'hh_kinzie_engages_1812',
         'white_liberty': 'hh_lees_place_1812', 'cardin_john_b': 'hh_lees_place_1812',
         'mirandeau_victoire_1812': 'hh_mirandeau_1812', 'mirandeau_madeline_1812': 'hh_mirandeau_1812',
         'mirandeau_jean_baptiste': 'hh_mirandeau_1812', 'lalime_john': 'hh_lalime_john_1812',
         'irwin_matthew': 'hh_irwin_matthew_1812'}
STATUS = {'present': 'present', 'absent': 'absent', 'uncertain': 'uncertain', 'probably_present': 'probably present'}
REL = re.compile(r'[^a-z_]')


def relationship(card, pid):
    r = str(card.get('relationship') or 'member').lower()
    for k, v in (('daughter', 'daughter'), ('son', 'son'), ('wife', 'wife'), ('clerk', 'clerk'), ('servant', 'servant'),
                 ('engag', 'employee'), ('hand', 'employee'), ('member', 'household_member')):
        if k in r:
            return v
    return 'head' if pid in {h[1] for h in HOUSEHOLDS.values()} else 'household_member'


# Sentences that speak of the readings or the build (a ticket, a jaunt's needs, who carded whom)
# are the researcher's, not the person's: they stay in the reading and out of the card.
META = re.compile(r'\bT-\d{4}\b|uncarded|carded|not_placed|\breading\b|researcher|scene now runs|jaunt|placeable|'
                  r'pg\d+\.txt|\blines? \d|Do not render|\(L-[\w-]+\)', re.I)


FACT_REF = re.compile(r'\bfacts? [a-z][a-z0-9_]*(?: and [a-z][a-z0-9_]*)?|;?\s*see (?:alt_)?days\b')
TIDY = [(re.compile(r'\(\s*[;,]\s*'), '('), (re.compile(r'\s*[;,]\s*\)'), ')'), (re.compile(r'\s*\(\s*\)'), ''),
        (re.compile(r'\s+([:;,.])'), r'\1'), (re.compile(r':\.'), '.'), (re.compile(r',,'), ',')]


def clean(text):
    text = FACT_REF.sub('', re.sub(r'\s+', ' ', str(text or '')).strip())
    for rx, to in TIDY:
        text = rx.sub(to, text)
    parts = re.split(r"(?<=[a-z0-9)\]\"'][.;])\s+(?=[A-Z\"(])", text)
    return ' '.join(x for x in parts if x and not META.search(x)).replace(' ;', ';').replace(' .', '.')


# Who they were, in a line, from their own facts (each quote is on the card below), for the
# civilians whose reading's card note speaks only of the reading.
LEAD = {
    'lalime_john': "The government's interpreter at Fort Dearborn, a Frenchman with a house on the north side of the river. "
                   "He was killed just outside the fort's entrance on the evening of 17 June 1812, in a fight with John Kinzie.",
    'irwin_matthew': "The United States factor at Chicago, who came in 1809 to keep the government factory and left on 5 July 1812. "
                     "He watched the killing of Lalime.",
    'mirandeau_jean_baptiste': "A Frenchman who did blacksmith work at the fort in 1811 and lodged his family at Ouilmette's. "
                               "On the night of 17 June 1812 he took John Kinzie to Milwaukee; the family were gone before the fort burned.",
    'cardin_john_b': "A Canadian newly come to Chicago (Currey calls him Debou), killed with Liberty White at Lee's Place on 6 April 1812.",
    'white_liberty': "An American who had charge of Lee's farm on the South Branch, killed there on 6 April 1812.",
    'mirandeau_victoire_1812': "A daughter of Jean Baptiste Mirandeau and his Ottawa wife; she and her sister Madeline saw the fight "
                               "between John Kinzie and Lalime (Andreas p. 105).",
    'mirandeau_madeline_1812': "A daughter of Jean Baptiste Mirandeau and his Ottawa wife, afterwards the wife of John K. Clark; she "
                               "and her sister Victoire saw the fight between John Kinzie and Lalime (Andreas p. 105).",
}


def sentence(s):
    s = clean(s)
    if not s:
        return ''
    s = s[0].upper() + s[1:]
    return s if s[-1] in '.!?"\'' else s + '.'


def build():
    known = {p.stem for p in SOURCES.glob('*.json')}
    rows, unknown = {}, set()
    for path in READINGS:
        d = json.loads(path.read_text())
        for p in d['people']:
            if not p['person_id'].startswith('new:'):
                continue
            pid = p['person_id'][4:]
            if pid in SKIP:
                continue
            card = p.get('card') or {}
            hid = PLACE.get(pid) or str(card.get('household') or '').split()[0]
            if hid not in HOUSEHOLDS:
                raise SystemExit(f'{pid}: no household for {hid!r}')
            ev, seen = [], set()
            for f in p.get('facts') or []:
                sid = f.get('source') or f.get('source_id')
                if not sid:
                    continue
                if sid not in known:
                    unknown.add(sid)
                    continue
                k = (sid, f.get('locator'), f.get('quote'))
                if k in seen:
                    continue
                seen.add(k)
                e = {'source_id': sid, 'locator': f.get('locator'), 'quote': f.get('quote')}
                if f.get('claim'):
                    e['claim'] = f['claim']
                if f.get('tier'):
                    e['tier'] = f['tier']
                ev.append(e)
            sources = sorted({e['source_id'] for e in ev} | {s for s in card.get('sources') or [] if s in known})
            grade = str(card.get('grade') or 'reconstructed').split()[0]
            grade = grade if grade in ('attested', 'inferred', 'reconstructed') else 'reconstructed'
            pres = p.get('presence') or {}
            st = (p.get('present') or {}).get('status', 'uncertain')
            window = f"In the town from {pres.get('from')} to {pres.get('to')}" if pres.get('from') or pres.get('to') else ''
            note = ' '.join(x for x in (LEAD.get(pid, ''), sentence(card.get('note')),
                                        sentence(window and window + ': ' + str(pres.get('basis') or ''))) if x)
            rec = {'id': pid, 'name': card.get('name') or p.get('name') or pid, 'relationship': relationship(card, pid),
                   'grade': grade, 'sources': sources or ['quaife_1913']}
            sex = card.get('sex') or p.get('sex')
            if sex in ('m', 'f', 'male', 'female'):
                rec['sex'] = {'m': 'male', 'f': 'female'}.get(sex, sex)
            age = (p.get('age_1812') or {})
            if isinstance(age, dict) and isinstance(age.get('value'), (int, float)):
                a = int(age['value'])
                rec['age_band'] = {'value': f'{a}-{a}', 'low': a, 'high': a, 'tier': age.get('grade', 'reconstructed'),
                                   'note': sentence(age.get('basis')) or 'Not recorded; reconstructed for the figure.'}
            rec['present_on_scene_date'] = {
                'value': STATUS.get(st, 'uncertain'), 'confidence': 'inferred',
                'note': sentence((p.get('present') or {}).get('basis') or pres.get('basis')) +
                        ' No source takes a roll call on the afternoon of 14 August 1812; this is read from the evidence below.'}
            rec['note'] = note
            review = card.get('review_note') or (card.get('review_reason') and 'review_required: ' + card['review_reason']) \
                or HOUSEHOLDS[hid][6]
            if review or p.get('review_required') or card.get('touches_native_history'):
                rec['review_required'] = True
                rec['touches_removal'] = bool(card.get('touches_removal') or p.get('touches_removal'))
                rec['review_note'] = review or REVIEW_REP
            if card.get('reconstruction') or grade == 'reconstructed':
                rec['reconstruction'] = {**(card.get('reconstruction') or {'stage': 'counted_unnamed', 'counted_by': 'quaife_1913'}),
                                         'liberty': LIBERTY}
                rec['reconstruction'].setdefault('ticket', d['meta']['ticket'])
            rec['evidence'] = ev
            rows.setdefault(hid, []).append(rec)
    out = {}
    for hid, persons in rows.items():
        name, head, division, home, tier, home_note, review = HOUSEHOLDS[hid]
        head = head if head and any(p['id'] == head for p in persons) else persons[0]['id']
        persons.sort(key=lambda p: (p['id'] != head,))
        cited = sorted({s for p in persons for s in p['sources']})
        rec = {'id': hid, 'scene': '1812', 'name': name, 'head': head, 'division': division}
        if review:
            rec['review_required'] = True
            rec['touches_removal'] = hid.startswith('hh_potawatomi_camp_')
            rec['review_note'] = review
        here = [p for p in persons if p['present_on_scene_date']['value'] in ('present', 'probably present')]
        rec['present_on_scene_date'] = {
            'value': 'present' if here else 'absent', 'confidence': 'inferred', 'sources': cited[:4],
            'note': ("Each person's own card says how their presence on 14 August is known." if here else
                     'Dead or gone before 14 August 1812; in the town on the earlier dates their cards give.')}
        rec['associated_with'] = ([{'kind': 'home', 'place_or_structure_id': home, 'resolves_to': 'structure', 'from': None,
                                    'to': None, 'tier': tier, 'source_id': cited[0], 'also_sources': cited[1:3], 'note': home_note}]
                                  if home else [])
        rec['not_in_this_household'] = {'note': f'Everyone the T-3463..T-3467 day readings put in this household is on the card (liberty {LIBERTY}).',
                                        'sources': cited[:3]}
        rec['persons'] = persons
        out[f'{hid}.json'] = rec
    return out, unknown


def main(check=False):
    out, unknown = build()
    stale = []
    for name, rec in out.items():
        text = json.dumps(rec, indent=2, ensure_ascii=False) + '\n'
        path = OUT / name
        if check:
            if not path.exists() or path.read_text() != text:
                stale.append(name)
        else:
            path.write_text(text)
    for s in sorted(unknown):
        print(f'  a fact cites {s}, which has no source record; left in the reading')
    if stale:
        raise SystemExit('stale 1812 town cards (rerun cards.py): ' + ', '.join(stale))
    print(f"{len(out)} households, {sum(len(r['persons']) for r in out.values())} people" + (' — current' if check else ' written'))


if __name__ == '__main__':
    main('--check' in sys.argv)
