# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3500: a card for everyone of the August 1812 gathering and of Wells's escort, and Louis Fettle.

The owner, 2026-11-08, after the spike that counted the people at Chicago on 14 August 1812:
he chose *"Card all, draw a sample"* (every missing person carded with a lodge home, about one
in five drawn), then *"The remainder would be in buildings and I can ask them to come out and
meet them"*. Helm counts the gathering on the 12th as *"500 warriors 179 women & children"*
and Wells's escort as *"27 Miamis"* (Quaife 1913, App. VI). The T-3461 and T-3463..T-3467
sweeps carded 42 Potawatomi (24 men, 10 women, 8 children) and 8 Miamis; this script cards
the rest, none of whom any source names:

    476 men, 50 women and 111 children of the gathering, and 19 men of the escort,

and Louis Fettle (Pettell), whom Quaife thinks one of the twelve militia (App. IX: "Probably").

What it decides, said here (liberty L-1812-gathering-people-3500):

  * SEX AND AGE. Helm's split is followed exactly. Ages are seeded per person: men 16-60
    (most 20-40), women 16-62, children 0-15; a child under 3 is carried, and is carded but
    neither drawn nor asked for at a door (there is no carried pose, and nobody calls a baby
    out of a lodge).
  * LODGES. A camp ground sleeps what T-3499's occupancy rule says (mat or bark-roofed lodge 8,
    long lodge 20, bark house 14; 710 for the thirteen grounds, 36 for the Miamis'). The four
    men's grounds of T-3499 take men only, about 57 each; the women and children go to the
    family grounds in proportion to the room left there, and the rest of the men fill them.
    Within a ground people are dealt to its lodge doors (data/humans/doors_1812.json) a
    family at a time: a woman, her children and a man share a lodge. Which family had which
    lodge is not recorded anywhere.
  * WHO IS DRAWN. One in five, seeded per person (never a carried child). The drawn spend the
    day at their own ground: asleep in the lodge at night, at its door at their work, eating
    with whoever of their lodge is drawn; on the 15th the men are away from the camp from
    7:30 to 13:00, as the T-3467 representatives are, and nothing of the day is staged. Every
    point is a clear spot in front of the person's own lodge door, out of every lodge, rack and
    woodpile of the ground's model.
  * EVERYONE ELSE is listed in data/humans/inside_1812.json at their lodge's door, so Ask for
    calls them out (renderers/web/js/human-days.js).
  * LOOKS. Heritage, not a description: black hair (grey from 55), dark eyes, a brown
    complexion drawn copper, a few lighter (tan) or darker (deep brown); stature seeded about
    the period's means; children's height by age. No feature is exaggerated.
  * LOUIS FETTLE gets his own household in Le Mai's house: data/exclusions.json
    pettell_cabin_1812 reads his hut of 1803 as Le Mai's or La Lime's house of 1808, and La
    Lime's was La Lime's until 17 June 1812. He is asked for at its door; whether he was in
    the town on the 14th is uncertain, as his card says.
  * WELLS'S ESCORT moves to its camp (miami_escort_camp_1812, T-3499): `--move-miami` rewrote
    the bivouac points of docs/RESEARCH/people-1812-3467/day.json once (MIAMI_MOVE below);
    docs/RESEARCH/people-1812-town/cards.py now names the camp as their home.

Run from chicago/4d:  python3 docs/RESEARCH/gathering-people-1812-3500/build.py [--check]
Then: python3 tools/human_variation_kit.py (persons), tools/compile_scene.py --scene 1812.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'generators'))
sys.path.insert(0, str(ROOT / 'docs/RESEARCH/people-1812-town'))

HH = ROOT / 'data/residents_1812/households'
INST = ROOT / 'data/humans/instances/1812'
INSIDE = ROOT / 'data/humans/inside_1812.json'
LOOKS = ROOT / 'data/humans/variation/looks'
DOORS = ROOT / 'data/humans/doors_1812.json'
TICKET = 'T-3500'
LIBERTY = 'L-1812-gathering-people-3500'
GEN = 'docs/RESEARCH/gathering-people-1812-3500/build.py'
PREFIX = 'hi_camp_'
SEED = 'T-3500:20261108'

OCCUPANCY = {'mat_lodges': 8, 'bark_roofed_lodges': 8, 'long_lodges': 20, 'bark_houses': 14}
MEN_GROUNDS = ('north_flat', 'head_west', 'prairie_west', 'far_west')
FAMILY_GROUNDS = ('mouth', 'middle', 'west_bank', 'south_reach', 'upper', 'south_bend', 'south_prairie', 'south_west')
LABEL = {'mouth': "the creek's mouth", 'middle': "the creek's middle reach", 'west_bank': 'the west bank',
         'south_reach': 'the south reach', 'upper': 'the upper creek', 'south_bend': 'the bend',
         'south_prairie': 'the south prairie', 'south_west': 'the south-west ground', 'north_flat': 'the north flat',
         'head_west': "the creek's head", 'prairie_west': 'the west prairie', 'far_west': 'the far west ground'}
NEW = {'men': 476, 'women': 50, 'children': 111, 'miami': 19}
MEN_PER_MEN_GROUND = 57
CARRIED_UNDER = 3
DRAW = 0.2

HELM = {'source_id': 'quaife_1913', 'locator': "App. VI, Helm's narrative (1814), Gutenberg #69274 lines 16635-16636",
        'quote': 'the tribes there assembled to amount of 500 warriors 179 women & children',
        'claim': "Helm's count of the gathering at Wells's council; this card is one of it."}
CREEK = {'source_id': 'currey_1912_old_fort_dearborn', 'locator': 'ch. III, Gutenberg #52346 lines 2246-2247',
         'quote': 'beyond which were the groups of Indian wigwams clustered along the creek',
         'claim': 'The lodges along the creek, seen from the fort.'}
HELM_MIAMI = {'source_id': 'quaife_1913', 'locator': "App. VI, Helm's narrative, Gutenberg #69274 lines 16634-16635",
              'quote': 'Capt. William Wells arrived from Fort Wayne on the 12th August with 27 Miamis',
              'claim': "Helm's count of the escort; this card is one of it."}
HEALD_MIAMI = {'source_id': 'quaife_1913', 'locator': "App. IV, Heald's report, Gutenberg #69274 lines 16229-16230",
               'quote': 'On the 13th, Captain Wells, of Fort Wayne, arrived with about 30 Miamies, for the purpose of escorting us in',
               'claim': "Heald's date and count of the escort."}

INSIDE_PROVENANCE = {'grade': 'reconstructed', 'ticket': TICKET, 'sources': ['quaife_1913'], 'liberty': 'L418',
                     'basis': f'Carded by {TICKET} and not drawn: asked for at the door of the lodge or house they are put in, and built then in their dress; that home, the look and the dress are ours (liberty {LIBERTY}).'}

REVIEW = ("review_required: a person of the Potawatomi gathering at Chicago in August 1812, carded so that Helm's count "
          "of it is whole; no roll names them or counts them lodge by lodge. touches_removal: these are the people removed "
          "from Chicago in 1835. The card invents no name, band or story; its sex, age, lodge and day are reconstructed "
          f"({LIBERTY}) and it stages no speech, ceremony or act of war.")
REVIEW_MIAMI = ("review_required: a Miami man of the escort William Wells brought from Fort Wayne, carded so that Helm's "
                "count of 27 is whole; no source names him. The card invents no name or story and stages no speech, "
                "ceremony or act of war.")


def rng_for(*parts):
    return random.Random(int(hashlib.sha256('|'.join(map(str, (SEED,) + parts)).encode()).hexdigest()[:16], 16))


def seeded(*parts):
    return rng_for(*parts).random()


# ── the grounds: room, doors and the clear spots before each door ─────────────────────
def grounds():
    from archetypes import lodge_camp_params
    doors = {s['structure']: s['doors'] for s in json.loads(DOORS.read_text())['structures']}
    out = {}
    for g in MEN_GROUNDS + FAMILY_GROUNDS:
        sid = f'potawatomi_camp_1812_{g}'
        st = json.loads((ROOT / f'data/structures/{sid}.json').read_text())
        p = lodge_camp_params.from_phase(st['phases'][0], st)
        out[g] = {'id': sid, 'room': sum(getattr(p, k, 0) * v for k, v in OCCUPANCY.items()), 'doors': doors[sid]}
    st = json.loads((ROOT / 'data/structures/miami_escort_camp_1812.json').read_text())
    p = lodge_camp_params.from_phase(st['phases'][0], st)
    out['miami'] = {'id': 'miami_escort_camp_1812', 'room': sum(getattr(p, k, 0) * v for k, v in OCCUPANCY.items()),
                    'doors': doors['miami_escort_camp_1812']}
    return out


class Obstacles:
    """Where a ground's model stands above the ground (lodges, racks, woodpiles, hearth kit), on
    a 0.25 m grid in the town's frame, and the town's own footprints (place_town.clear)."""
    CELL = 0.25

    def __init__(self):
        import numpy as np
        from export_print_3mf import load_triangles
        import place_town
        self.place_town = place_town
        self.cells = set()
        # where the town's other people stand at some hour (their spans' points): no one of
        # the gathering is put on top of them
        self.taken = []
        for f in sorted((ROOT / 'data/humans/instances/1812').glob('hi_*.json')):
            if f.name.startswith(PREFIX):
                continue
            b = json.loads(f.read_text()).get('behaviour') or {}
            for v in b.get('day') or [] if isinstance(b.get('day'), list) else []:
                for sp in v.get('spans') or []:
                    if sp.get('at') and not sp.get('indoors'):
                        self.taken.append((sp['at']['local_e'], sp['at']['local_n']))
        for sc in sorted((ROOT / 'data/sidecars/1812').glob('*camp_1812*.json')):
            rec = json.loads(sc.read_text())
            if not isinstance(rec, dict) or 'placement' not in rec:
                continue
            glb = ROOT / f"assets/gltf/{rec['id']}__camp_1812.glb"
            if not glb.exists():
                continue
            pl = rec['placement']
            th = math.radians(float(pl.get('rotation_deg') or 0.0))
            c, s = math.cos(th), math.sin(th)
            T = np.concatenate([t for _, t in load_triangles(glb)])
            T = T[T[:, :, 1].max(axis=1) > 0.06]
            uv = np.stack([T[:, :, 0], -T[:, :, 2]], axis=2)          # (n, 3, 2)
            edge = np.max(np.linalg.norm(uv - np.roll(uv, 1, axis=1), axis=2), axis=1)
            k = np.clip(np.ceil(edge / (self.CELL * 0.7)), 1, 60).astype(int)
            pts = []
            for n in np.unique(k):
                sel = uv[k == n]
                ij = np.array([(i, j) for i in range(n + 1) for j in range(n + 1 - i)], float) / n
                w = np.stack([ij[:, 0], ij[:, 1], 1 - ij[:, 0] - ij[:, 1]], 1)   # (m, 3)
                pts.append(np.einsum('mk,nkd->nmd', w, sel).reshape(-1, 2))
            P = np.concatenate(pts)
            E = float(pl['local_e']) + P[:, 0] * c + P[:, 1] * s
            N = float(pl['local_n']) - P[:, 0] * s + P[:, 1] * c
            for i, j in np.unique(np.stack([np.floor(E / self.CELL), np.floor(N / self.CELL)], 1).astype(int), axis=0):
                self.cells.add((int(i), int(j)))

    def _mark(self, e, n):
        self.cells.add((math.floor(e / self.CELL), math.floor(n / self.CELL)))

    def clear(self, e, n, r=0.6):
        k = int(math.ceil(r / self.CELL))
        ci, cj = math.floor(e / self.CELL), math.floor(n / self.CELL)
        for i in range(ci - k, ci + k + 1):
            for j in range(cj - k, cj + k + 1):
                if (i, j) in self.cells:
                    return False
        return self.place_town.clear((e, n), 0.6)

    def near(self, e, n, r=0.6, reach=4.0, sep=0.0, take=False):
        """The clear spot nearest (e, n), within `reach`, `sep` from every spot taken; None if
        there is none. `take` keeps it for the next asker."""
        def ok(q):
            return self.clear(*q, r) and all(math.hypot(q[0] - t[0], q[1] - t[1]) >= sep for t in self.taken)
        found = (e, n) if ok((e, n)) else None
        for ring in range(1, int(reach / 0.25) + 1) if found is None else ():
            d = ring * 0.25
            for k in range(max(8, ring * 6)):
                a = 2 * math.pi * k / max(8, ring * 6)
                q = (e + d * math.sin(a), n + d * math.cos(a))
                if ok(q):
                    found = q
                    break
            if found:
                break
        if found is None:
            return None
        found = (round(found[0], 2), round(found[1], 2))
        if take:
            self.taken.append(found)
        return found


def before(door, out_m, side_m=0.0):
    h = math.radians(door['outward_deg'])
    e = door['step']['local_e'] + out_m * math.sin(h) + side_m * math.cos(h)
    n = door['step']['local_n'] + out_m * math.cos(h) - side_m * math.sin(h)
    return e, n


# ── who: Helm's split, dealt to grounds and lodges ────────────────────────────────────
def tri(r, lo, hi, mode):
    return int(round(r.triangular(lo, hi, mode)))


def people(G):
    men = [{'sex': 'male', 'age': tri(rng_for('man', i), 16, 60, 28), 'kind': 'man'} for i in range(NEW['men'])]
    women = [{'sex': 'female', 'age': tri(rng_for('woman', i), 16, 62, 30), 'kind': 'woman'} for i in range(NEW['women'])]
    kids = []
    for i in range(NEW['children']):
        r = rng_for('child', i)
        kids.append({'sex': 'female' if r.random() < 0.5 else 'male', 'age': r.randint(0, 15), 'kind': 'child'})
    # families: each woman with her children (two or three, dealt in turn) and a man
    fams = [[w] for w in women]
    for i, k in enumerate(kids):
        fams[i % len(fams)].append(k)
    # the men's grounds first
    out = {g: [] for g in G}
    mi = 0
    for g in MEN_GROUNDS:
        for _ in range(MEN_PER_MEN_GROUND):
            out[g].append([men[mi]])
            mi += 1
    # the family grounds: room left after the people already carded there
    carded = {'mouth': 11, 'middle': 10, 'west_bank': 9, 'south_reach': 6, 'upper': 6}
    room = {g: G[g]['room'] - carded.get(g, 0) for g in FAMILY_GROUNDS}
    total = len(women) + len(kids) + (len(men) - mi)
    share = {g: room[g] * total / sum(room.values()) for g in FAMILY_GROUNDS}
    want = {g: int(share[g]) for g in FAMILY_GROUNDS}
    for g in sorted(FAMILY_GROUNDS, key=lambda g: share[g] - want[g], reverse=True)[:total - sum(want.values())]:
        want[g] += 1
    # families go round the family grounds in turn, each with a man while men last
    order = list(FAMILY_GROUNDS)
    fi = 0
    have = {g: 0 for g in FAMILY_GROUNDS}
    for fam in fams:
        while have[order[fi % len(order)]] + len(fam) + 1 > want[order[fi % len(order)]]:
            fi += 1
        g = order[fi % len(order)]
        fi += 1
        fam = [men[mi]] + fam
        mi += 1
        out[g].append(fam)
        have[g] += len(fam)
    for g in FAMILY_GROUNDS:
        while have[g] < want[g] and mi < len(men):
            out[g].append([men[mi]])
            mi += 1
            have[g] += 1
    assert mi == len(men), (mi, len(men))
    for g in FAMILY_GROUNDS:
        assert have[g] <= room[g], (g, have[g], room[g])
    miami = [[{'sex': 'male', 'age': tri(rng_for('miami', i), 22, 42, 30), 'kind': 'miami'}] for i in range(NEW['miami'])]
    out['miami'] = miami
    return out


def deal_lodges(groups, doors, start=0):
    """Families to lodge doors in turn, a family whole; returns [(person, door)]."""
    out, d = [], start
    for fam in groups:
        door = doors[d % len(doors)]
        d += 1
        for p in fam:
            out.append((p, door))
    return out


# ── cards ─────────────────────────────────────────────────────────────────────────────
def noun(p):
    a = p['age']
    if p['kind'] == 'child':
        if a < CARRIED_UNDER:
            return 'A baby'
        return ('A girl' if p['sex'] == 'female' else 'A boy') if a < 13 else ('A young woman' if p['sex'] == 'female' else 'A youth')
    if p['kind'] == 'woman':
        return 'An old woman' if a >= 55 else 'A woman'
    return 'An old man' if a >= 55 else ('A young man' if a < 20 else 'A man')


def card(pid, p, g, k, n, door):
    miami = g == 'miami'
    where = "the Miami escort's camp" if miami else f"the camp at {LABEL[g]}"
    name = f"{noun(p)} of {where} (name not recorded), {k} of {n}"
    lodge = door['id'].split(':')[1].replace('lodge', 'lodge no. ')
    note = (f"One of the {'27 Miamis of Wells\'s escort (Helm)' if miami else 'gathering Helm counts on 12 August 1812, 500 warriors and 179 women and children'}, "
            f"whom no source names; carded so the count is whole. Sleeps in {lodge} of the ground"
            + (", with " + ('her' if p['sex'] == 'female' else 'his') + " family" if len(p.get('fam', [])) > 1 else '')
            + f". Sex and age follow Helm's split; the age, the lodge and the day are reconstructed ({LIBERTY}).")
    if p['kind'] == 'child' and p['age'] < CARRIED_UNDER:
        note += ' Carried by the family; not drawn and not called out at the door.'
    rec = {'id': pid, 'name': name, 'relationship': 'child' if p['kind'] == 'child' else 'household_member',
           'grade': 'reconstructed', 'sources': sorted({'quaife_1913'} | ({'currey_1912_old_fort_dearborn'} if not miami else set())),
           'sex': p['sex'],
           'age_band': {'value': f"{p['age']}-{p['age']}", 'low': p['age'], 'high': p['age'], 'tier': 'reconstructed',
                        'note': 'Seeded to give the camp a believable spread of ages; not recorded.'},
           'present_on_scene_date': {'value': 'present', 'confidence': 'inferred',
                                     'note': ('Wells came in with the escort on the 13th (Heald) and they marched out with the column on the 15th.'
                                              if miami else 'The gathering stood at the camp from the council of the 12th; no source takes a roll call on the 14th.')},
           'note': note, 'review_required': True, 'touches_removal': not miami,
           'review_note': REVIEW_MIAMI if miami else REVIEW,
           'reconstruction': {'stage': 'counted_unnamed', 'counted_by': 'quaife_1913', 'ticket': TICKET, 'liberty': LIBERTY},
           'evidence': [HELM_MIAMI, HEALD_MIAMI] if miami else [HELM, CREEK]}
    return rec


def household(hid, name, g, persons, home, tier, home_note, review, touches):
    return {'id': hid, 'scene': '1812', 'name': name, 'head': persons[0]['id'], 'division': 'camp',
            'review_required': True, 'touches_removal': touches, 'review_note': review,
            'present_on_scene_date': {'value': 'present', 'confidence': 'inferred', 'sources': ['quaife_1913'],
                                      'note': "Each person's own card says how their presence on 14 August is known."},
            'associated_with': [{'kind': 'home', 'place_or_structure_id': home, 'resolves_to': 'structure', 'from': None,
                                 'to': None, 'tier': tier, 'source_id': 'quaife_1913',
                                 'also_sources': [] if g == 'miami' else ['currey_1912_old_fort_dearborn'], 'note': home_note}],
            'not_in_this_household': {'note': f"The people already carded at this ground have their own cards; everyone dealt here by {GEN} is on this one (liberty {LIBERTY}).",
                                      'sources': ['quaife_1913']},
            'persons': persons}


FETTLE = {
    'id': 'fettle_louis', 'name': 'Louis Fettle (Pettell)', 'relationship': 'head', 'grade': 'inferred',
    'sources': ['currey_1912_story_of_old_fort_dearborn', 'quaife_1913'], 'sex': 'male',
    'age_band': {'value': '45-45', 'low': 45, 'high': 45, 'tier': 'reconstructed',
                 'note': 'Not recorded; settled here by 1803 with a wife, drawn at forty-five.'},
    'present_on_scene_date': {'value': 'uncertain', 'confidence': 'inferred',
                              'note': "In Kinzie's books down to 1812; only Quaife's guess (\"Probably\") puts him among the twelve militia of 15 August."},
    'note': ("A French-Canadian who was living at Chicago with an Indian wife when the garrison came in 1803, and whose name "
             "is in John Kinzie's books down to 1812; then he disappears. Quaife thinks him probably one of the twelve militia "
             "killed on 15 August. His home here is Le Mai's house: the hut Currey puts 'near the Kinzie house' is read as one "
             "of the four houses of 1808 under a later name (data/exclusions.json pettell_cabin_1812), La Lime's or Le Mai's, "
             f"and La Lime lived in his until 17 June 1812 ({LIBERTY}). His wife is not named or carded."),
    'reconstruction': {'stage': 'home_inferred', 'ticket': TICKET, 'liberty': LIBERTY},
    'evidence': [
        {'source_id': 'quaife_1913', 'locator': 'ch. VI, PG 69274 lines 5706-5707',
         'quote': 'he was a French-Canadian living here with an Indian wife when the garrison came in 1803',
         'claim': 'French Canadian with an Indian wife, here in 1803'},
        {'source_id': 'quaife_1913', 'locator': 'ch. VI, PG 69274 lines 5709-5710',
         'quote': 'His name occurs at intervals down to 1812, showing that he was a resident of Chicago during the entire period.',
         'claim': "in Kinzie's books down to 1812"},
        {'source_id': 'currey_1912_story_of_old_fort_dearborn', 'locator': 'pt. II, PG 52346 line 707',
         'quote': 'A man named Pettell also had a small cabin near the Kinzie house.', 'claim': 'his cabin'},
        {'source_id': 'quaife_1913', 'locator': 'app. IX, PG 69274 lines 17158-17159',
         'quote': 'Probably Louis Fettle, who lived at Chicago from 1803 to 1812 and then disappeared from recorded history, was still another.',
         'claim': "Quaife's guess: one of the twelve militia"}],
}


# ── looks ─────────────────────────────────────────────────────────────────────────────
CHILD_CM = {3: 94, 4: 101, 5: 107, 6: 113, 7: 119, 8: 124, 9: 129, 10: 134, 11: 139, 12: 144, 13: 150, 14: 156, 15: 160}
BODY_M = {'adult_male': 1.75, 'adult_female': 1.65, 'child_8': 1.205}


def asset_of(p):
    if p['kind'] == 'child' and p['age'] < 12:
        return 'potawatomi_girl_1812' if p['sex'] == 'female' else 'potawatomi_boy_1812'
    return 'potawatomi_woman_1812' if p['sex'] == 'female' else 'potawatomi_man_1812'


def looks(pid, p, origin):
    r = rng_for('looks', pid)
    x = r.random()
    comp = ('copper', 'brown, a warm medium-to-deep tone') if x < 0.7 else (
        ('tan', 'light brown') if x < 0.85 else ('deep_brown', 'dark brown'))
    asset = asset_of(p)
    if asset.startswith('potawatomi_boy') or asset.startswith('potawatomi_girl'):
        cm = CHILD_CM.get(max(3, p['age']), 94) * r.uniform(0.96, 1.04)
        scale = round(max(0.8, min(1.25, cm / 100 / BODY_M['child_8'])), 4)
    elif p['sex'] == 'female':
        cm = r.gauss(158, 5) if p['kind'] != 'child' else CHILD_CM.get(p['age'], 156)
        scale = round(max(0.85, min(1.15, cm / 100 / BODY_M['adult_female'])), 4)
    else:
        cm = r.gauss(172, 6) if p['kind'] != 'child' else CHILD_CM.get(p['age'], 160)
        scale = round(max(0.85, min(1.15, cm / 100 / BODY_M['adult_male'])), 4)
    female = p['sex'] == 'female'
    grey = p['age'] >= 55
    return {
        'format': 'chicago4d_human_looks_v1', 'ticket': TICKET, 'person_id': pid, 'scene': '1812', 'generated_by': GEN,
        'heritage': {'origin': origin, 'family': 'reading'},
        'complexion': {'value': comp[1], 'drawn': comp[0], 'grade': 'reconstructed'},
        'hair': {'value': 'grey, straight' if grey else 'black, straight', 'drawn': 'grey_brown' if grey else 'black',
                 'cut': 'centre_part_clubbed_1812' if female else 'clubbed_behind_1812',
                 'facial': ['brows_fine', 'lashes_upper'] if female else [], 'grade': 'reconstructed'},
        'eyes': {'value': 'dark brown', 'drawn': 'dark_brown', 'grade': 'reconstructed'},
        'height_scale': scale,
        'basis': f'Heritage, not a description: no one of the gathering is described. Seeded colouring and stature, no exaggerated feature ({LIBERTY}).',
        'grade': 'reconstructed', 'liberty': LIBERTY,
    }


# ── days of the drawn ─────────────────────────────────────────────────────────────────
WORK = {
    'man': ['mending a moccasin by the lodge', 'shaving a new bow stave', 'seeing to his pony and its gear',
            'splitting firewood for the lodge', 'repairing a fish spear', 'smoking by the lodge door'],
    'woman': ['scraping a deerskin at the frame', 'tending the kettle', 'pounding corn in the mortar',
              'sewing and mending by the lodge', 'tying back a loose mat on the lodge', 'cutting meat to dry'],
    'child': ['carrying water and wood for the kettle', 'playing between the lodges', 'minding a younger child by the lodge'],
    'miami': ['rubbing down his pony', 'mending a bridle', 'cleaning his gun by the fire'],
}


def day_for(p, at, meal, work, kind, men_talk):
    w = WORK['child' if p['kind'] == 'child' else kind]
    doing = w[int(seeded('work', p['pid']) * len(w))]
    def out(a, b, act, pt, text, extra=None):
        s = {'from': a, 'to': b, 'indoors': False, 'at': {'local_e': pt[0], 'local_n': pt[1], 'heading_deg': pt[2]},
             'activity': act, 'doing': text}
        if extra:
            s.update(extra)
        return s
    home = p['home']
    eat = ('talk', {'knot': meal[1]}) if meal[1] else ('stand', None)
    spans = [{'from': 0, 'to': 5.5, 'indoors': True, 'where': home, 'doing': 'asleep in the lodge'},
             out(5.5, 6.5, 'stand', at, 'up at the lodge door, the fire made up'),
             out(6.5, 7.5, eat[0], meal[0], 'eating with the lodge', eat[1]),
             out(7.5, 12, 'work', at, doing, {'spots': work}),
             {'from': 12, 'to': 13.5, 'indoors': True, 'where': home, 'doing': 'out of the midday sun in the lodge'}]
    if men_talk and men_talk[1]:
        spans.append(out(13.5, 17.5, 'talk', men_talk[0], 'talking with the men of the ground', {'knot': men_talk[1]}))
    else:
        spans.append(out(13.5, 17.5, 'work', at, doing, {'spots': work}))
    spans += [out(17.5, 18.75, eat[0], meal[0], 'the evening meal with the lodge', eat[1]),
              out(18.75, 21.5, 'stand', at, 'evening at the lodge door'),
              {'from': 21.5, 'to': 24, 'indoors': True, 'where': home, 'doing': 'asleep in the lodge'}]
    for s in spans:
        if s.get('activity') == 'talk' and not s.get('knot'):
            s['activity'] = 'stand'
    return spans


def away(spans, a, b, text):
    out = []
    for s in spans:
        if s['to'] <= a or s['from'] >= b:
            out.append(s)
            continue
        if s['from'] < a:
            out.append({**s, 'to': a})
        if s['to'] > b:
            out.append({**s, 'from': b})
    out.append({'from': a, 'to': b, 'indoors': True, 'away': True, 'doing': text})
    return sorted(out, key=lambda s: s['from'])


def instance(pid, p, spans_default, variants, asset):
    first = next(s for s in spans_default if not s['indoors'])
    day = [{'dates': d, 'spans': s} for d, s in variants] + [{'spans': spans_default}]
    pres = {'from': '1812-08-13', 'to': '1812-08-15'} if p['kind'] == 'miami' else {'from': '1812-08-12', 'to': '1812-08-16'}
    iid = f'{PREFIX}{pid}'
    return iid, {
        'id': iid, 'contract_version': 1, 'scene': '1812', 'person_id': pid, 'appearance': {'asset_id': asset},
        'placement': {'local_e': first['at']['local_e'], 'local_n': first['at']['local_n'],
                      'heading_deg': first['at']['heading_deg'], 'anchor': 'terrain'},
        'animation': {'clip': 'idle', 'loop': True, 'phase': round(seeded(pid, 'phase'), 3)},
        'behaviour': {'state': 'standing', 'day': day, 'presence': pres},
        'interaction': {'selectable': True, 'radius_m': 3, 'opens': 'resident_card'},
        'lod': {'policy': 'auto'}, 'display': 'shown', 'review_required': True,
        'provenance': {'grade': 'reconstructed',
                       'basis': (f'One of the {"escort" if p["kind"] == "miami" else "gathering"} carded by {TICKET} and drawn (about one in '
                                 f'five), at the door of their own lodge by day and asleep in it by night; the hours, places and work '
                                 f'are ours (liberty {LIBERTY}); nothing of the 15th is staged.'),
                       'sources': ['quaife_1913'], 'liberty': 'L418', 'seed': f'{pid}:{SEED}',
                       'replaceable_by': 'An account of the camp that says who lodged where and what they did.'},
    }


# ── the whole build ───────────────────────────────────────────────────────────────────
def build():
    G = grounds()
    groups = people(G)
    obst = Obstacles()
    files_hh, files_inst, inside, looks_files, problems = {}, {}, [], {}, []
    drawn_by_lodge = {}
    rows = []   # (pid, person, ground, door)
    for g in MEN_GROUNDS + FAMILY_GROUNDS + ('miami',):
        dealt = deal_lodges(groups[g], G[g]['doors'], start=0)
        persons = []
        n = len(dealt)
        for k, (p, door) in enumerate(dealt, 1):
            pid = f'miami_escort_1812_{k + 8:02d}' if g == 'miami' else f'gathering_1812_{g}_{k:03d}'
            p['pid'], p['home'], p['door'] = pid, G[g]['id'], door['id']
            p['fam'] = next(f for f in groups[g] if p in f)
            persons.append(card(pid, p, g, k + 8 if g == 'miami' else k, 27 if g == 'miami' else n, door))
            rows.append((pid, p, g, door))
        if g == 'miami':
            hid, name = 'hh_miami_escort_camp_1812', "The rest of the Miami escort, at its camp (names not recorded)"
            files_hh[hid] = household(hid, name, g, persons, G[g]['id'], 'reconstructed',
                                      "The escort's camp ground south-west of the fort (T-3499); where they camped is not recorded.",
                                      REVIEW_MIAMI, False)
        else:
            hid = f'hh_gathering_{g}_1812'
            name = f"The people of the gathering at {LABEL[g]} (names not recorded)"
            files_hh[hid] = household(hid, name, g, persons, G[g]['id'], 'reconstructed',
                                      "A ground of the camp of the gathering (T-3342, T-3499); which lodge each family had is not recorded.",
                                      REVIEW, True)
    files_hh['hh_fettle_louis_1812'] = {
        'id': 'hh_fettle_louis_1812', 'scene': '1812', 'name': 'Louis Fettle, in Le Mai\'s house', 'head': 'fettle_louis',
        'division': 'north',
        'present_on_scene_date': {'value': 'uncertain', 'confidence': 'inferred', 'sources': ['quaife_1913'],
                                  'note': "His card says what is known of him in 1812."},
        'associated_with': [{'kind': 'home', 'place_or_structure_id': 'lemai_house_1812', 'resolves_to': 'structure', 'from': None,
                             'to': None, 'tier': 'reconstructed', 'source_id': 'currey_1912_story_of_old_fort_dearborn',
                             'also_sources': ['quaife_1913'],
                             'note': "Currey's 'small cabin near the Kinzie house', read as one of the four houses of 1808 (pettell_cabin_1812); Le Mai's, since La Lime's was his own until June 1812."}],
        'not_in_this_household': {'note': 'His wife, an Indian woman (Quaife), is not named and not carded.', 'sources': ['quaife_1913']},
        'persons': [FETTLE]}

    # who is drawn: one in five, never a carried child
    for pid, p, g, door in rows:
        p['drawn'] = p['age'] >= CARRIED_UNDER and seeded('draw', pid) < DRAW
        if p['drawn']:
            drawn_by_lodge.setdefault(door['id'], []).append((pid, p, g, door))
    # points: each drawn person's spot before their own door; the lodge's meal, a ring about
    # a spot before its door; the ground's afternoon talk, the men in knots of up to five, each
    # a ring about its own spot. No two people stand within SEP of each other.
    SEP = 0.8

    def ring(centre, k, n, radius):
        a = 2 * math.pi * k / max(1, n) + seeded('ring', centre) * math.pi
        q = obst.near(centre[0] + radius * math.sin(a), centre[1] + radius * math.cos(a), reach=1.5, sep=SEP, take=True)
        if q is None:
            return None
        return (q[0], q[1], round(math.degrees(math.atan2(centre[0] - q[0], centre[1] - q[1])) % 360, 1))

    door_at = {}
    for lodge, ds in sorted(drawn_by_lodge.items()):
        for i, (pid, p, g, door) in enumerate(ds):
            side = (-1.3 if i % 2 else 1.3) * (1 + i // 2)
            door_at[pid] = next((q for out_m, sd in ((1.6, side), (2.2, side), (1.6, -side), (2.8, side / 2), (3.4, 0.0))
                                 for q in [obst.near(*before(door, out_m, sd), reach=3.0, sep=SEP)] if q), None)
            if door_at[pid]:
                obst.taken.append(door_at[pid])
    meal_spot, knots = {}, {}
    for lodge, ds in sorted(drawn_by_lodge.items()):
        # a lodge whose drawn people find no spot together eats each at their own door
        meal_spot[lodge] = obst.near(*before(ds[0][3], 3.4), reach=3.0, sep=1.2) or obst.near(*before(ds[0][3], 4.5), reach=5.0, sep=1.0)
    centres = []
    for g in MEN_GROUNDS + FAMILY_GROUNDS + ('miami',):
        men = [r for _, ds in sorted(drawn_by_lodge.items()) for r in ds if r[2] == g and r[1]['kind'] in ('man', 'miami')]
        chunks = [men[i:i + 5] for i in range(0, len(men), 5)]
        if len(chunks) > 1 and len(chunks[-1]) == 1:
            last = chunks.pop()
            chunks[-1] += last
        for c, chunk in enumerate(chunks):
            if len(chunk) < 2:
                continue
            q = None
            for member in chunk:
                for out_m in (5.5, 7.0, 8.5, 10.0):
                    cand = obst.near(*before(member[3], out_m, 1.5 * c), reach=4.0, sep=1.4)
                    if cand and all(math.hypot(cand[0] - x[0], cand[1] - x[1]) >= 4.5 for x in centres):
                        q = cand
                        break
                if q:
                    break
            if q is None:   # they keep at their work through the afternoon
                continue
            centres.append(q)
            for k, (pid, *_rest) in enumerate(chunk):
                knots[pid] = (q, k, len(chunk), f'men_{g}_{c + 1}')
    meal_seat = {}
    for lodge, ds in sorted(drawn_by_lodge.items()):
        mq = meal_spot[lodge]
        for i, (pid, *_rest) in enumerate(ds):
            meal_seat[pid] = ring(mq, i, len(ds), 0.75 + 0.12 * len(ds)) if mq and len(ds) >= 2 else None
    for lodge, ds in sorted(drawn_by_lodge.items()):
        for i, (pid, p, g, door) in enumerate(ds):
            at = door_at[pid]
            if at is None:
                problems.append(f'{pid}: no clear spot before {lodge}')
                p['drawn'] = False
                continue
            hd = round((door['outward_deg']) % 360, 1)
            side = (-1.3 if i % 2 else 1.3) * (1 + i // 2)
            w1 = obst.near(*before(door, 1.6, side + 0.9), reach=1.2, sep=SEP) or at
            w2 = obst.near(*before(door, 2.4, side), reach=1.2, sep=SEP) or at
            work = [{'local_e': w1[0], 'local_n': w1[1]}, {'local_e': w2[0], 'local_n': w2[1]}]
            meal = (meal_seat[pid], f'meal_{lodge.replace(":", "_")}') if meal_seat[pid] else ((at[0], at[1], hd), None)
            men_talk = None
            if pid in knots:
                kq, k, n, kid = knots[pid]
                seat = ring(kq, k, n, 0.9 + 0.15 * n)
                if seat:
                    men_talk = (seat, kid)
            spans = day_for(p, (at[0], at[1], hd), meal, work, 'miami' if p['kind'] == 'miami' else p['kind'], men_talk)
            variants = []
            if p['kind'] == 'man':
                variants.append(({'from': '1812-08-15', 'to': '1812-08-15'}, away(spans, 7.5, 13.0, 'away from the camp')))
            if p['kind'] == 'miami':
                variants.append(({'from': '1812-08-13', 'to': '1812-08-13'}, away(spans, 0, 16.0, 'on the road from Fort Wayne (not drawn)')))
                variants.append(({'from': '1812-08-15', 'to': '1812-08-15'}, away(spans, 9.0, 24.0, 'gone south with the column (not drawn)')))
            iid, rec = instance(pid, p, spans, variants, asset_of(p))
            files_inst[f'{iid}.json'] = rec
    for pid, p, g, door in rows:
        if p['age'] < CARRIED_UNDER and p['kind'] == 'child':
            continue
        looks_files[f'{pid}.json'] = looks(pid, p, 'Miami' if g == 'miami' else 'Potawatomi')
        if not p['drawn']:
            inside.append({'person': pid, 'name': next(x['name'] for x in files_hh[('hh_miami_escort_camp_1812' if g == 'miami' else f'hh_gathering_{g}_1812')]['persons'] if x['id'] == pid),
                           'home': p['home'], 'door': door['id'], 'asset_id': asset_of(p),
                           'presence': {'from': '1812-08-13', 'to': '1812-08-15'} if g == 'miami' else {'from': '1812-08-12', 'to': '1812-08-16'},
                           'provenance': INSIDE_PROVENANCE})
    # Louis Fettle, asked for at Le Mai's door; his looks are the T-3466 reading's words
    inside.append({'person': 'fettle_louis', 'name': 'Louis Fettle', 'home': 'lemai_house_1812', 'asset_id': 'engage_1812',
                   'presence': {'from': '1803-08-17', 'to': '1812-08-15'},
                   'provenance': INSIDE_PROVENANCE})
    looks_files['fettle_louis.json'] = {
        'format': 'chicago4d_human_looks_v1', 'ticket': TICKET, 'person_id': 'fettle_louis', 'scene': '1812', 'generated_by': GEN,
        'heritage': {'origin': 'French-Canadian', 'family': 'reading'},
        'complexion': {'value': 'fair, weathered', 'drawn': 'ruddy', 'grade': 'reconstructed'},
        'hair': {'value': 'dark brown greying, tied behind', 'drawn': 'grey_brown', 'cut': 'clubbed_behind_1812', 'facial': [], 'grade': 'reconstructed'},
        'eyes': {'value': 'brown', 'drawn': 'brown', 'grade': 'reconstructed'},
        'height_scale': round(66 * 0.0254 / BODY_M['adult_male'], 4),
        'basis': 'Heritage only: "a French-Canadian" (Quaife). No likeness. The T-3466 day reading\'s words, drawn.',
        'grade': 'reconstructed', 'liberty': LIBERTY}
    return files_hh, files_inst, inside, looks_files, problems


def write(path, rec, indent, check, stale):
    text = json.dumps(rec, indent=indent, ensure_ascii=False) + '\n'
    if check:
        if not path.exists() or path.read_text() != text:
            stale.append(str(path.relative_to(ROOT)))
    else:
        path.write_text(text)


def main(check=False):
    files_hh, files_inst, inside, looks_files, problems = build()
    stale = []
    for hid, rec in files_hh.items():
        write(HH / f'{hid}.json', rec, 2, check, stale)
    for name, rec in files_inst.items():
        write(INST / name, rec, 2, check, stale)
    for old in INST.glob(f'{PREFIX}*.json'):
        if old.name not in files_inst:
            stale.append(old.name) if check else old.unlink()
    index = json.loads((INST / 'index.json').read_text())
    keep = [i for i in index['instances'] if not i.startswith(PREFIX)]
    write(INST / 'index.json', {**index, 'instances': sorted(set(keep) | {f[:-5] for f in files_inst})}, 2, check, stale)
    doc = json.loads(INSIDE.read_text())
    others = [x for x in doc['people'] if (x.get('provenance') or {}).get('ticket') != TICKET]
    write(INSIDE, {**doc, 'people': others + inside}, 1, check, stale)
    for name, rec in looks_files.items():
        write(LOOKS / name, rec, 1, check, stale)
    for old in LOOKS.glob('*.json'):
        try:
            gen = json.loads(old.read_text()).get('generated_by')
        except ValueError:
            continue
        if gen == GEN and old.name not in looks_files:
            stale.append(old.name) if check else old.unlink()
    for p in problems:
        print('  PROBLEM:', p, file=sys.stderr)
    n = sum(len(h['persons']) for h in files_hh.values())
    if stale:
        raise SystemExit(f'stale T-3500 files (rerun {GEN}): ' + ', '.join(stale[:12]))
    print(f'{n} people carded in {len(files_hh)} households; {len(files_inst)} drawn, {len(inside)} asked for at a door'
          + (' — current' if check else ' written'))
    return 1 if problems else 0


# ── the eight drawn Miamis of T-3467 move from their bivouac to the escort's camp ─────
MIAMI_MOVE = {'from': (1100.0, 162.0), 'reach_m': 22.0, 'delta': (-28.0, -99.0), 'gate': (1076.0, 83.0),
              'day': 'docs/RESEARCH/people-1812-3467/day.json'}


def day_json(doc):
    """The reading's own layout: indent 1, with `at`, `route` and two-month `months` on one line."""
    import re
    s = json.dumps(doc, indent=1, ensure_ascii=False)
    one = lambda m: m.group(1) + json.dumps(json.loads(m.group(2)), ensure_ascii=False)
    s = re.sub(r'("months": )(\[\s*\d+,\s*\d+\s*\])', one, s)
    s = re.sub(r'("(?:at|route)": )(\{[^{}]*\}|\[(?:[^\[\]]|\[[^\[\]]*\])*\])', one, s)
    return s + '\n'


def move_miami():
    """Once (a moved point is far from the bivouac, so a rerun changes nothing): every point of
    the T-3467 Miamis within reach of the bivouac by the stables moves by `delta` to the escort's
    camp, onto clear ground; a night asleep by the fire becomes a night in the lodges; a route
    that began or ended at the bivouac runs on to the camp's north edge by way of it."""
    path = ROOT / MIAMI_MOVE['day']
    doc = json.loads(path.read_text())
    obst = Obstacles()
    fe, fn = MIAMI_MOVE['from']
    de, dn = MIAMI_MOVE['delta']
    gate = obst.near(*MIAMI_MOVE['gate'], reach=4)
    moved = 0

    def near(q):
        return math.hypot(q[0] - fe, q[1] - fn) <= MIAMI_MOVE['reach_m']

    def spans(day):
        nonlocal moved
        for i, v in enumerate(day):
            if v.get('activity') == 'sleep' and v.get('at') and near((v['at']['local_e'], v['at']['local_n'])):
                day[i] = {'from': v['from'], 'to': v['to'], 'indoors': True, 'where': 'miami_escort_camp_1812',
                          'doing': 'asleep in the lodge', **{k: v[k] for k in ('grade', 'basis') if k in v}}
                moved += 1
                continue
            if v.get('at') and near((v['at']['local_e'], v['at']['local_n'])):
                q = obst.near(v['at']['local_e'] + de, v['at']['local_n'] + dn, reach=5)
                v['at'] = {**v['at'], 'local_e': q[0], 'local_n': q[1]}
                moved += 1
            if isinstance(v.get('where'), str):
                v['where'] = v['where'].replace('the Miami bivouac south-west of the fort', "the Miami escort's camp south-west of the fort")
                v['where'] = v['where'].replace('south of the bivouac', "by the escort's camp")
                v['where'] = v['where'].replace('path to the bivouac', "path to the escort's camp")
            if isinstance(v.get('doing'), str):
                v['doing'] = v['doing'].replace('walking back to the bivouac', "walking back to the escort's camp")
            r = v.get('route')
            if r and len(r) >= 2:
                if near(r[0]) and list(r[0]) != list(gate):
                    r.insert(0, list(gate))
                    moved += 1
                if near(r[-1]) and list(r[-1]) != list(gate):
                    r.append(list(gate))
                    moved += 1

    for p in doc['people']:
        if not p['person_id'].startswith('new:miami_escort'):
            continue
        spans(p['day'])
        for k in p.get('days', []) + p.get('alt_days', []):
            spans(k['day'])
        card = p.get('card') or {}
        if (card.get('home') or {}).get('place_or_structure_id') is None and 'home' in card:
            card['home'] = {'place_or_structure_id': 'miami_escort_camp_1812',
                            'note': "The escort's camp ground south-west of the fort (T-3499); where they camped is not recorded. "
                                    "Moved there from the bivouac by the stables by T-3500.",
                            'tier': 'reconstructed'}
            card['stands_for'] = 'himself: one of the 27 (Helm); T-3500 cards the other 19'
    path.write_text(day_json(doc))
    print(f'{moved} Miami points moved to the escort camp')


if __name__ == '__main__':
    if '--move-miami' in sys.argv:
        move_miami()
        sys.exit(0)
    sys.exit(main('--check' in sys.argv))
