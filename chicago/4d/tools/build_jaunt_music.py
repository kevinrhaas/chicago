#!/usr/bin/env python3
"""T-3710: which score cue plays under which jaunt. Writes data/music/jaunts.json.

The owner, 2026-11-20: "Ok can you go ahead and add the music to the jaunts correctly".
The narrated jaunts come first (his order of 2026-11-20). Each plan names the cue for the
flight to the first stop (opening), the bed looped at the stops, any stop that wants its
own cue (the battle's four movements), and the cue under the closing scene. Every grade
band's and audience's version of a jaunt (version_of) gets its jaunt's plan, listed by its
own id, so the Jaunts menu's Music filter (T-3711) can read the file as it stands.

The cue files are the owner-selected score set v1 (generated through fal; the main theme is
his fixed recording, never regenerated). tools/prepare_audio.py --score-only encodes them
and copies the plans into the audio catalogue. Run from any directory:

    python3 tools/build_jaunt_music.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/music/jaunts.json'
JAUNTS = ROOT / 'data/jaunts'
ORIGINALS = 'assets/audio/originals/score-v1/'

# id: (file, era, title, role, target LUFS[, seconds kept from the end])
# Beds sit under a speaking voice: sparse, no lead line in the voice's register, quieter.
CUES = {
    'jaunt-opening-1812': ('30-jaunt-opening-1812.mp3', '1812', 'Jaunt Opening, 1812', 'opening', -21),
    'jaunt-closing-1812': ('31-jaunt-closing-1812.mp3', '1812', 'Jaunt Closing, 1812', 'closing', -21, 32),
    'bed-1812-fort': ('40-bed-1812-fort.mp3', '1812', 'The Fort', 'bed', -23),
    'bed-1812-mystery': ('41-bed-1812-mystery.mp3', '1812', 'Mystery at the River', 'bed', -23),
    'battle-1-buildup': ('42-battle-1-buildup.mp3', '1812', 'Battle I: Before the March', 'bed', -23),
    'battle-2-march': ('43-battle-2-march.mp3', '1812', 'Battle II: The March', 'bed', -23),
    'battle-3-fight': ('44-battle-3-fight.mp3', '1812', 'Battle III: The Fight', 'bed', -23),
    'battle-4-aftermath': ('45-battle-4-aftermath.mp3', '1812', 'Battle IV: Aftermath', 'bed', -23),
    'theme-remembrance': ('23-theme-remembrance.mp3', '1812', 'Remembrance', 'closing', -21),
    'jaunt-opening-1904': ('30-jaunt-opening-1904.mp3', '1904', 'Jaunt Opening, 1904', 'opening', -21),
    'jaunt-closing-1904': ('31-jaunt-closing-1904.mp3', '1904', 'Jaunt Closing, 1904', 'closing', -21, 32),
    'bed-1904-places': ('46-bed-1904-places.mp3', '1904', 'The Avenue', 'bed', -23),
    'bed-1904-household': ('47-bed-1904-household.mp3', '1904', 'The Household', 'bed', -23),
    'bed-1904-people': ('48-bed-1904-people.mp3', '1904', 'Famous Names', 'bed', -23),
    'bed-1904-stories': ('49-bed-1904-stories.mp3', '1904', 'Prairie Avenue Stories', 'bed', -23),
    'bed-1904-architecture': ('50-bed-1904-architecture.mp3', '1904', 'Architecture', 'bed', -23),
    'bed-1904-ghosts': ('51-bed-1904-ghosts.mp3', '1904', 'Night on the Avenue', 'bed', -23),
    'bed-1904-bronze': ('52-bed-1904-bronze.mp3', '1904', 'The Bronze', 'bed', -23),
}

# The battle: April to the eve of the march builds; the march out of the gate; the fight at
# the sand bank and the cottonwoods; the aftermath at Kinzie's and the burning fort.
BATTLE_STOPS = {'river-mouth': 'battle-2-march', 'the-bank': 'battle-3-fight', 'cottonwoods': 'battle-3-fight',
    'kinzie-house': 'battle-4-aftermath', 'the-burning': 'battle-4-aftermath', 'war-party': 'battle-4-aftermath',
    'ouilmette': 'battle-4-aftermath'}

O12, C12, O04, C04 = 'jaunt-opening-1812', 'jaunt-closing-1812', 'jaunt-opening-1904', 'jaunt-closing-1904'
PLANS = {
    # A tragedy: no fanfare. It opens on its own build and closes on Remembrance.
    'battle-of-fort-dearborn': {'opening': 'battle-1-buildup', 'bed': 'battle-1-buildup', 'stops': BATTLE_STOPS,
        'closing': 'theme-remembrance'},
    'first-fort-dearborn-tour': {'opening': O12, 'bed': 'bed-1812-fort', 'closing': C12},
    'killing-of-jean-lalime': {'opening': O12, 'bed': 'bed-1812-mystery', 'closing': C12},
    'prairie-avenue-orientation': {'opening': O04, 'bed': 'bed-1904-places', 'closing': C04},
    'glessner-household-tour': {'opening': O04, 'bed': 'bed-1904-household', 'closing': C04},
    'prairie-famous-names': {'opening': O04, 'bed': 'bed-1904-people', 'closing': C04},
    'prairie-notable-women': {'opening': O04, 'bed': 'bed-1904-people', 'closing': C04},
    **{j: {'opening': O04, 'bed': 'bed-1904-stories', 'closing': C04} for j in (
        'field-and-mrs-caton', 'frances-glessner-lee', 'monday-reading-class', 'one-year-and-a-day',
        'pullmans-other-son', 'the-pullman-twins', 'the-walk-to-the-lake',
        # Their own bed (bed-1904-scandal in data/music/score.json) is not made yet: fal's
        # balance ran out on 2026-11-20. The stories bed stands in until it is.
        'scandal-at-1612', 'sisters-of-the-levee')},
    **{j: {'opening': O04, 'bed': 'bed-1904-architecture', 'closing': C04} for j in (
        'prairie-architects', 'prairie-style-italianate', 'prairie-style-romanesque', 'prairie-style-second-empire')},
    'prairie-ghosts-at-night': {'opening': O04, 'bed': 'bed-1904-ghosts', 'closing': C04},
    'bronze-at-eighteenth': {'opening': O04, 'bed': 'bed-1904-bronze', 'closing': C04},
}


def build():
    docs = {}
    for f in sorted(JAUNTS.glob('*.json')):
        d = json.loads(f.read_text())
        if isinstance(d, dict) and 'id' in d: docs[d['id']] = d
    cues = {}
    for cid, row in CUES.items():
        file, era, title, role, lufs, *tail = row
        cues[cid] = {'file': ORIGINALS + file, 'era': era, 'title': title, 'role': role, 'lufs': lufs,
            'loop': role == 'bed', **({'keep_last_s': tail[0]} if tail else {})}
    rows = []
    for jid, plan in PLANS.items():
        doc = docs.get(jid)
        if not doc: raise SystemExit(f'{jid}: no such jaunt')
        if doc.get('version_of'): raise SystemExit(f'{jid}: name the jaunt, not a version of it')
        stops = {s['id'] for s in doc['stops']}
        for cid in [plan['opening'], plan['bed'], plan['closing'], *plan.get('stops', {}).values()]:
            if cid not in cues: raise SystemExit(f'{jid}: no cue {cid}')
            if cues[cid]['era'] != str(doc['scene']): raise SystemExit(f'{jid}: {cid} is not {doc["scene"]} music')
        for sid in plan.get('stops', {}):
            if sid not in stops: raise SystemExit(f'{jid}: no stop {sid}')
        rows.append({'id': jid, **plan})
        for vid, v in sorted(docs.items()):
            if v.get('version_of') != jid: continue
            missing = set(plan.get('stops', {})) - {s['id'] for s in v['stops']}
            if missing: raise SystemExit(f'{vid}: lacks stops {sorted(missing)} its plan names')
            rows.append({'id': vid, 'version_of': jid, **plan})
    return {'version': 1,
        'about': 'T-3710: the score under the jaunts, written by tools/build_jaunt_music.py. Each jaunt (and each '
                 "version of it) names its opening cue, its bed, any stop's own cue and its closing cue; "
                 'tools/prepare_audio.py --score-only encodes the cues and copies the plans into the audio catalogue. '
                 'A jaunt listed here has music (T-3711).',
        'cues': cues, 'jaunts': rows}


if __name__ == '__main__':
    data = build()
    OUT.write_text(json.dumps(data, indent=2) + '\n')
    print(f'jaunt music: {len(data["cues"])} cues under {len(data["jaunts"])} jaunts')
