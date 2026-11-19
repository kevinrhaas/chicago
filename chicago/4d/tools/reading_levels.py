#!/usr/bin/env python3
"""T-3645: every card's words at the reader's other ages, written and measured.

The owner, 2026-11-17: "a person can set a grade level age level in their settings and then
the cards they read about people etc are targeted at their age level ... there would be a tab
to read the different levels of all of the cards, the default level is the highest level".

A card's words are written once, for a visitor. This tool holds their retellings at the other
ages (8-10, 11-13, 14-15, 16-17, as the Jaunts menu offers them since T-3640) and writes the
table the app reads, `data/reading/<scene>.json`. The retellings are authored by hand in
`docs/RESEARCH/reading-levels-3645/words/<scene>-<family>.json`, keyed by the record's id, each
age a list of paragraphs, one for each paragraph of the record's own. Nothing is generated.

Every age is MEASURED, never typed (tools/jaunt_reading_level.py, the mean of five US
grade-level formulas over a card's words, each number read as one short word: see `plain`):
  - the record's own words read at the age they measure (`own`), and so at every older age:
    a retelling is for a reader younger than its words, never a harder telling for an older
    one, so only the ages below `own` are written;
  - each retelling reads inside its age's band or below it, and easier than the record itself.
No fact enters a retelling that the record does not hold: a retelling says the same thing in
other words, for a reader of another age.

A "why", Design or evidence note is keyed by its own words, so a house PR that rewrites one
leaves its retelling unmatched. That is not an error in the house PR: `--check` lists the
retelling as waiting for a re-key and passes, and the card shows the note as written at every
age until someone keys the retelling to the note's new words (adding a sentence for what the
note added) and runs this tool.

    python3 tools/reading_levels.py            # write data/reading/<scene>.json, print each card's measures
    python3 tools/reading_levels.py --check    # fail on a stale table or an age out of its band; list retellings to re-key
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from jaunt_reading_level import measure, band_of, BANDS  # noqa: E402

WORDS = ROOT / 'docs/RESEARCH/reading-levels-3645/words'
OUT = ROOT / 'data/reading'
# The ages a card is told at, youngest first, and the school band each stands for (T-3640).
AGES = {'8-10': '3-5', '11-13': '6-8', '14-15': '9-10', '16-17': '11-12'}
AGE_OF_BAND = {'K-2': '8-10', **{band: age for age, band in AGES.items()}}
ORDER = list(AGES)
DOC = ("T-3645: the cards' words at the reader's other ages, written by tools/reading_levels.py from "
       "docs/RESEARCH/reading-levels-3645/words. Each entry is one paragraph as a card shows it (`text`), "
       "the age it measures at (`own`), and its words at other ages (`levels`); js/reading-level.js "
       "lays them under a card's age tabs. Do not edit: edit the words files and run the tool.")


def stories(scene):
    path = ROOT / f'data/residents_{scene}/stories.json'
    doc = json.loads(path.read_text()) if path.exists() else {}
    return {k: [str(p).strip() for p in v] for k, v in (doc.get('stories') or {}).items()}


def tales(scene):
    path = ROOT / f'data/tales/{scene}.json'
    doc = json.loads(path.read_text()) if path.exists() else {}
    out = {}
    for t in doc.get('tales') or []:
        out[t['id']] = [str(p).strip() for p in t.get('text') or []]
    for teller in (doc.get('personal') or {}).values():
        for t in teller:
            out[t['id']] = [str(p).strip() for p in t.get('text') or []]
    return out


def asks(scene):
    """'Ask a question' answers (js/ask-card.js): an answer by its question's id, and each
    follow-up's answer by that id and its place among the follow-ups (`a04-md-day.1`)."""
    path = ROOT / f'data/tales/{scene}.json'
    doc = json.loads(path.read_text()) if path.exists() else {}
    out = {}

    def walk(ask, rid):
        if ask.get('a'):
            out[rid] = [str(p).strip() for p in ask['a']]
        for i, more in enumerate(ask.get('more') or []):
            walk(more, f'{rid}.{i + 1}')
    for ask in doc.get('asks') or []:
        walk(ask, ask['id'])
    for teller in (doc.get('personal_asks') or {}).values():
        for ask in teller:
            walk(ask, ask['id'])
    return out


def places(scene):
    """A building's authored Inspect record (data/inspect/<scene>.json `summaries`, compiled from
    data/summaries/): its summary by the building's id, and each line under it by the id, the
    part and its place (`glessner_house.notable.2`, `.story.1`, `.look.1`, `.status`)."""
    path = ROOT / f'data/inspect/{scene}.json'
    doc = json.loads(path.read_text()) if path.exists() else {}
    out = {}
    for bid, rec in (doc.get('summaries') or {}).items():
        if rec.get('summary'):
            out[bid] = [str(rec['summary']).strip()]
        note = (rec.get('status') or {}).get('note')
        if note:
            out[f'{bid}.status'] = [str(note).strip()]
        for part, key in (('notable', 'notable'), ('story', 'story'), ('look', 'lookFor')):
            for i, item in enumerate(rec.get(key) or []):
                text = item.get('text') if isinstance(item, dict) else item
                if text:
                    out[f'{bid}.{part}.{i + 1}'] = [str(text).strip()]
    return out


def leads(scene):
    """Every building card's opening line as the card shows it (tools/reading_leads.mjs: the
    phase's own account or the line composed from its sidecar, said through the reader
    overlay). Many buildings share a composed line, so a lead is keyed by its own words."""
    import subprocess
    run = subprocess.run(['node', str(ROOT / 'tools/reading_leads.mjs'), scene],
                         capture_output=True, text=True, check=True)
    return {t: [t] for t in json.loads(run.stdout)['leads']}


# A family is where a card's words live: its records, by id, each a list of paragraphs.
def notes(scene):
    """Every evidence note a building's Details tab shows, its "Why" (tools/reading_notes.mjs:
    the claim notes `buildingFacts` gives the tab, where they pass `clean`). Many claims share a
    note, so a note is keyed by its own words."""
    import subprocess
    run = subprocess.run(['node', str(ROOT / 'tools/reading_notes.mjs'), scene],
                         capture_output=True, text=True, check=True)
    return {t: [t] for t in json.loads(run.stdout)['notes']}


def design(scene):
    """Every line a building's Inspect Design tab shows (tools/reading_design.mjs: the written
    guide's lead, look-for, parts and basis, the style module's card and the record's own "On
    this house" items, as `designModel` gives the tab), keyed by its own text."""
    import subprocess
    run = subprocess.run(['node', str(ROOT / 'tools/reading_design.mjs'), scene],
                         capture_output=True, text=True, check=True, cwd=ROOT)
    return {t: [t] for t in json.loads(run.stdout)['lines']}


def why(scene):
    """Every "why" the floating card folds away behind its button (tools/reading_why.mjs: each
    claim's note in its Design, Story, People and research panes, as popup.js `sections` draws
    them), keyed by its own text. A note the Details tab shows too is told once, in `notes`."""
    import subprocess
    run = subprocess.run(['node', str(ROOT / 'tools/reading_why.mjs'), scene],
                         capture_output=True, text=True, check=True, cwd=ROOT)
    return {t: [t] for t in json.loads(run.stdout)['notes']}


FAMILIES = {'stories': stories, 'tales': tales, 'asks': asks, 'places': places, 'leads': leads, 'notes': notes,
            'design': design, 'why': why}


# A card is full of dates and house numbers: "lived at 2027 Prairie Avenue in 1904" is not hard
# to read, but the formulas count each digit of 2027 as a syllable, so a four-digit number is a
# long word. Before a card is measured each number reads as one short word. Names are left as
# they are: a long name is still hard for a young reader.
NUMBER = re.compile(r"\d+(?:[,.]\d+)*(?:st|nd|rd|th)?")


def plain(text):
    out = []
    for para in re.split(r'\n\s*\n', text):
        out.append(NUMBER.sub('ten', para.strip()))
    return '\n\n'.join(out)


def grade(paragraphs):
    return measure({'opening': {'text': plain('\n\n'.join(paragraphs))}})['grade']


def compile_scene(scene, files):
    """The table for one scene, and every problem found on the way."""
    entries, problems, report, stale = [], [], [], []
    for path in files:
        family = path.stem.split('-', 1)[1]
        source = FAMILIES.get(family)
        if not source:
            problems.append(f'{path.name}: no family "{family}" (one of {", ".join(FAMILIES)})')
            continue
        records = source(scene)
        words = json.loads(path.read_text())
        for rid, ages in words.items():
            if rid.startswith('_'):
                continue
            where = f'{path.name} {rid}'
            original = records.get(rid)
            if not original:
                # The note was edited, renamed or removed since it was told (a house PR that
                # rewrites a "why" changes its key). That is not an error in the edit: the card
                # shows the note's own words at every age until the telling is re-keyed.
                stale.append(f'{where[:140]}')
                continue
            g0 = grade(original)
            own = AGE_OF_BAND[band_of(g0)]
            # A "why" or Design line is keyed by its own words, so its card names only their start:
            # the whole note already rides in `text`, and spelling it twice doubled 1835's file.
            name = rid if len(rid) <= 80 else rid[:60].rstrip() + '…'
            row = {'card': f'{family}:{name}', 'own': own, 'grade': g0, 'ages': {}}
            for age, paras in ages.items():
                if age not in AGES:
                    problems.append(f'{where}: "{age}" is not an age ({", ".join(ORDER)})')
                    continue
                if age == own:
                    problems.append(f'{where}: the record itself reads at {age} (grade {g0}); that age is its own words')
                    continue
                if not isinstance(paras, list) or len(paras) != len(original):
                    problems.append(f'{where} {age}: {len(paras) if isinstance(paras, list) else "?"} paragraphs for the record\'s {len(original)}')
                    continue
                g = grade(paras)
                got, want = band_of(g), AGES[age]
                row['ages'][age] = g
                if ORDER.index(age) > ORDER.index(own):
                    problems.append(f'{where} {age}: the record reads at {own} (grade {g0}); an older reader reads it as written')
                    continue
                if BANDS.index(got) > BANDS.index(want):
                    problems.append(f'{where} {age}: written for grades {want} but reads at grade {g} ({got})')
                if g >= g0:
                    problems.append(f'{where} {age}: reads at grade {g}, no easier than the record itself ({g0}, {own})')
            report.append(row)
            for i, text in enumerate(original):
                levels = {age: ages[age][i] for age in ORDER if age in row['ages']}
                if levels:
                    entries.append({'card': row['card'], 'text': text, 'own': own, 'levels': levels})
    return {'_doc': DOC, 'scene': scene, 'entries': entries}, problems, report, stale


def current_texts(scene, files):
    """Every paragraph the scene's cards show now, for the families its words files tell."""
    texts = set()
    for path in files:
        source = FAMILIES.get(path.stem.split('-', 1)[1])
        for paras in (source(scene).values() if source else []):
            texts.update(paras)
    return texts


def scenes():
    by = {}
    for path in sorted(WORDS.glob('*.json')):
        scene = path.stem.split('-', 1)[0]
        by.setdefault(scene, []).append(path)
    return by


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true', help='fail on a stale table or an age out of its band')
    ap.add_argument('--quiet', action='store_true')
    ap.add_argument('--prepare', action='store_true',
                    help='only build the ignored records the card readers read (tools/test_reading_level.mjs)')
    args = ap.parse_args()
    # The buildings' Inspect records (data/inspect/<scene>.json, which `places` reads) are derived
    # and ignored, not committed: build them from data/summaries/ first, as publish.sh does, so a
    # fresh clone (CI) reads the same records as a working tree.
    import subprocess
    subprocess.run([sys.executable, str(ROOT / 'tools/compile_summaries.py'), '--build'],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    # And the reader's overlay (data/reader/, ignored too): a building card's "why" is read through
    # it (tools/reading_why.mjs), so without it a fresh clone reads the builders' raw notes.
    subprocess.run([sys.executable, str(ROOT / 'tools/compile_reader_text.py')]
                   + [a for s in ('1812', '1835', '1904') for a in ('--family', f'structures_{s}')],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    if args.prepare:
        return 0
    failures, waiting = [], []
    wanted = set()
    for scene, files in scenes().items():
        table, problems, report, stale = compile_scene(scene, files)
        failures += [f'{scene}: {p}' for p in problems]
        waiting += [f'{scene}: {w}' for w in stale]
        out = OUT / f'{scene}.json'
        wanted.add(out.name)
        text = json.dumps(table, ensure_ascii=False, indent=1) + '\n'
        if args.check:
            fresh = not out.exists() or out.read_text() == text
            if out.exists() and not fresh and stale:
                # A table written before a note changed still holds the old note's row, which no
                # card can match: it is fresh if, past those rows, it is the table written now.
                shown = current_texts(scene, files)
                held = json.loads(out.read_text())
                held['entries'] = [e for e in held['entries'] if e['text'] in shown]
                fresh = json.dumps(held, ensure_ascii=False, indent=1) + '\n' == text
            if not out.exists() or not fresh:
                failures.append(f'{scene}: data/reading/{scene}.json is stale; run python3 tools/reading_levels.py')
        elif not problems:
            OUT.mkdir(parents=True, exist_ok=True)
            out.write_text(text)
        if not args.quiet:
            for r in report:
                ages = ' · '.join(f'{a} {g}' for a, g in sorted(r['ages'].items(), key=lambda x: ORDER.index(x[0])))
                print(f'{scene} {r["card"]}: own {r["own"]} (grade {r["grade"]}) · {ages}')
    for path in sorted(OUT.glob('*.json')) if OUT.exists() else []:
        if path.name not in wanted:
            failures.append(f'data/reading/{path.name} has no words files behind it')
    entries = sum(len(json.loads((OUT / n).read_text())['entries']) for n in wanted if (OUT / n).exists())
    if waiting:
        print(f'reading_levels: {len(waiting)} telling(s) wait for a re-key: their note changed since it was told, '
              'so its card shows the note as written at every age. Key each to the note\'s words now:')
        for w in waiting:
            print(f'  {w}')
    if failures:
        print('reading_levels: FAIL')
        for f in failures:
            print(f'  {f}')
        return 1
    print(f'reading_levels: {"OK" if args.check else "written"} — {entries} paragraphs at other ages across {len(wanted)} scene(s)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
