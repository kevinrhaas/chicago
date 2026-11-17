# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3553: a name for everyone of 1812 whom no source names.

The owner, 2026-11-17: "for everyone in 1812 who does not have a name give them a name, they are
of course reconstructed people, unless its a known kid or something like that who is inferred, it
should show on their hover card".

The Potawatomi and Miami of the gathering already have names of our making (T-3507,
tools/native_cards_1812.py). This module does the same for the rest of the 1812 scene:

  TOWN CARDS. The people a source counts and nobody names, and who were carded as "name not
  recorded": the six unnamed men of the Chicago militia, the seven unnamed children of the post,
  Kinzie's boatman and second engagé, and his second servant. Each is given a name of the kind the
  sources say they were (Kinzie's engagés "Canadian voyageurs", Andreas p. 73; the militia men of
  the settlement, French and American, Quaife ch. X; the post's children of the soldier and settler
  families of British, Irish and German descent). No name is a name a source gives anyone at
  Chicago in 1812 (every surname on the 1812 cards is refused below), and a child is given a
  first name only, because which family a child belonged to is not known and a surname would claim
  one. Each card keeps what it was called before in `also_written`, says in `name_basis` (graded
  reconstructed) that the name is ours, and carries a Name fact saying so.

  KNOWN CHILDREN KEEP THEIR LABEL. A child a source places in a named family (the Burns children
  and baby, the Lee son, daughter and baby, the Holt and Needs children, Cicely's son, the Ouilmette
  children) is a real child whose name is lost; a name of ours on them would read as the record's,
  so they keep the honest label (the owner's exception: "unless its a known kid ... who is
  inferred"). The wives a source calls only "Mrs. Burns" and the like have the name the record
  gives them.

  STAGED FIGURES. The figures who play the unnamed in the two 1812 story jaunts (the men Heald
  took for Winnebagoes, the war party from the Wabash, the men who kept the Kinzies' porch, the
  young men who burned the fort, the gathering come to watch, the warriors of the 18+ telling) each
  take a name the same way the gathering's people did: in English, as the treaty clerks of 1815-16
  wrote these bands' names, a Potawatomi's speaking of a gens Morgan lists. The men whose nation is
  not certain (Heald "took" them for Winnebagoes; the war party is only "from the Wabash") are
  given a name that claims no gens. What the figure stands for stays on it as `about`.

Liberty L-1812-names-3553. Called by docs/RESEARCH/people-1812-3461/build.py and
docs/RESEARCH/people-1812-town/cards.py on their records before they write them, and by
docs/RESEARCH/jaunt-stage-1812-3553/build.py for each unnamed castmate.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIBERTY = 'L-1812-names-3553'
TICKET = 'T-3553'

# pid -> (name, sex, the basis sentence, its sources)
_KINZIE = ("Kinzie's engagés were Canadians (Andreas p. 73: \"the Canadian voyageurs in the service of Mr. Kinzie\"), "
           'so he is given a French-Canadian name')
_MILITIA_FR = ('The militia was enrolled from the men of the settlement, French-Canadian and American (Quaife ch. X); '
               'he wears an engagé\'s dress, so he is given a French-Canadian name')
_MILITIA_US = ('The militia was enrolled from the men of the settlement, French-Canadian and American (Quaife ch. X); '
               'he is given an American name of the time')
_CHILD = ("A first name only, of those common in the soldier and settler families of the day: which family the child "
          "belonged to is not known, and a surname would claim one")
TOWN = {
    'kinzie_boatman_1812': ('François Dumoulin', 'male', _KINZIE, ['andreas_1884_v1']),
    'kinzie_engage_1812': ('Michel Pelletier', 'male', _KINZIE, ['andreas_1884_v1']),
    'kinzie_servant_second': ('Louis Gagnon', 'male',
                              "The household's servants and helpers were French, Métis, Black and American; he is given a "
                              'French-Canadian name, the commonest in the house', ['kirkland_1893_chicago_massacre']),
    'chicago_militia_unnamed_1': ('Amos Whitcomb', 'male', _MILITIA_US, ['quaife_1913']),
    'chicago_militia_unnamed_2': ('Ezra Stoddard', 'male', _MILITIA_US, ['quaife_1913']),
    'chicago_militia_unnamed_3': ('Pierre Langlois', 'male', _MILITIA_FR, ['quaife_1913']),
    'chicago_militia_unnamed_4': ('Antoine Bellanger', 'male', _MILITIA_FR, ['quaife_1913']),
    'chicago_militia_unnamed_5': ('Joseph Desjardins', 'male', _MILITIA_FR, ['quaife_1913']),
    'chicago_militia_unnamed_6': ('Daniel McCurdy', 'male', _MILITIA_US, ['quaife_1913']),
    'garrison_child_unnamed_1': ('Reuben', 'male', _CHILD, ['quaife_1913']),
    'garrison_child_unnamed_2': ('Polly', 'female', _CHILD, ['quaife_1913']),
    'garrison_child_unnamed_3': ('Hannah', 'female', _CHILD, ['quaife_1913']),
    'garrison_child_unnamed_4': ('Eli', 'male', _CHILD, ['quaife_1913']),
    'garrison_child_unnamed_5': ('Betsey', 'female', _CHILD, ['quaife_1913']),
    'garrison_child_unnamed_6': ('Ephraim', 'male', _CHILD, ['quaife_1913']),
    'garrison_child_unnamed_7': ('Sally', 'female', _CHILD, ['quaife_1913']),
}
# Known children of named families keep their label (see above).
KEEP = {'burns_infant', 'burns_child_a', 'burns_child_b', 'lee_son', 'lee_daughter', 'lee_infant', 'holt_child',
        'needs_child', 'cicely_son', 'ouilmette_children'}


def apply_households(households: dict) -> int:
    """Name the unnamed town cards in `households` (id -> record), in place. Returns how many."""
    n = 0
    for rec in households.values():
        for p in rec.get('persons', []):
            if p['id'] not in TOWN:
                continue
            name, sex, why, srcs = TOWN[p['id']]
            old = p['name']
            if old == name:
                continue
            him = 'her' if sex == 'female' else 'him'
            p['name'] = name
            p['also_written'] = sorted(set(p.get('also_written') or []) | {old})
            p['name_basis'] = {'value': 'reconstructed', 'grade': 'reconstructed', 'sources': srcs,
                               'note': f'No source names {him}: the name is ours. {why}.'}
            p['card_facts'] = [f for f in p.get('card_facts') or [] if f.get('label') != 'Name'] + [
                {'label': 'Name', 'value': 'Reconstructed (no source names them)', 'grade': 'reconstructed'}]
            if p.get('note'):
                p['note'] = p['note'].replace('No name.', f'No source names {him}; the name on this card is ours.')
            p['sources'] = sorted(set(p.get('sources') or []) | set(srcs))
            rec_ = dict(p.get('reconstruction') or {})
            rec_.update({'name': 'reconstructed', 'name_ticket': TICKET, 'name_liberty': LIBERTY})
            p['reconstruction'] = rec_
            n += 1
    return n


# ── staged figures in the 1812 jaunts ───────────────────────────────────────────────────────
# The old label (what the figure stands for) -> (kind, the `about` line shown with the name).
_STAGED = [
    (r'took for Winnebagoes', 'uncertain', "One of the eleven men Heald took for Winnebagoes (Ho-Chunk)"),
    (r"two other Indians", 'potawatomi', "One of the 'two other Indians' who kept the Kinzies' porch with Black Partridge"),
    (r'war party from the Wabash, faces', 'uncertain', 'One of the war party from the Wabash, faces blackened'),
    (r'searchers, a war party', 'uncertain', 'One of the searchers, a war party from the Wabash'),
    (r'burned the fort', 'potawatomi', 'One of the young men of the gathering who burned the fort'),
    (r'women of the gathering', 'potawatomi_woman', 'One of the women of the gathering, come to watch'),
    (r'men of the gathering, come', 'potawatomi', 'One of the men of the gathering, come to watch'),
    (r'One of the warriors', 'potawatomi', 'One of the warriors'),
]
_names = None


def _taken():
    """Every name already on an 1812 card, so a staged figure's name repeats none of them."""
    out = set()
    for f in (ROOT / 'data/residents_1812/households').glob('hh_*.json'):
        for p in json.loads(f.read_text()).get('persons', []):
            out.add(p['name'])
            out.update(p.get('also_written') or [])
    return out


def stage_name(extra_id: str, label: str | None):
    """(name, about) for an unnamed castmate of an 1812 jaunt; (label, None) for one who has a name."""
    global _names
    if not label or not re.search(r'names? not recorded', label):
        return label, None
    for rx, kind, about in _STAGED:
        if re.search(rx, label):
            break
    else:
        raise SystemExit(f'names_1812: no kind for the staged label {label!r}; add it to _STAGED')
    import native_cards_1812 as nc
    if _names is None:
        _names = nc._Names(reserved=_taken())
    gentes = nc.GENTES['Potawatomi']
    if kind == 'uncertain':
        # A nation not certain: the name speaks of no gens (wolf, bear, elk, eagle and thunder are
        # words of every people of this country), and the line says so.
        gentes = [g for g in gentes if g[0] in ('Wolf', 'Bear', 'Elk', 'Eagle', 'Thunder')]
    role = 'woman' if kind == 'potawatomi_woman' else 'man'
    first = gentes.index(nc._pick(gentes, 'stage-gens', extra_id))
    # The gens's own pool first; a pool already spent on the gathering's cards moves to the next
    # gens rather than give a name again ("... the Second").
    for k in range(len(gentes)):
        name = _names.make(gentes[(first + k) % len(gentes)][0], role, 28, f'stage:{extra_id}')
        if re.search(r' the (Second|Third|Fourth|Fifth)$| \(\d+\)$', name):
            _names.used.discard(name)
            continue
        if len(re.findall(r'\b(White|Black|Red|Yellow|Gray)\b', name)) > 1:
            continue      # two colours ("Yellow White Head"): left unused, the next gens tried
        break
    else:
        raise SystemExit(f'names_1812: every pool spent for {extra_id}')
    return name, f'{about}; name reconstructed'
