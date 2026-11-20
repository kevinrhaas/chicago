#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3621: a telling of every jaunt for every school grade band the Jaunts menu offers.

The owner, 2026-11-16: "take a sweep of all the jaunts and make sure you have all grade levels
for all of them across all years"; "add jaunts to fill it all in so there is a version of every
jaunt for every level". T-3590 tagged each jaunt with the band its words measure at and made the
first `version_of` (the Glessner Household tour for grades 3-5); this fills in the rest.

A version is the same walk in other words: the base jaunt's stops, stage, people, light, choices,
effects and evidence are copied as they are, and only the words the visitor reads are replaced,
from a words file here (words/<version id>.txt). No fact enters a retelling that its base jaunt or
the base's own evidence does not already state: a younger telling leaves detail out, an older one
draws more of the base's evidence into the prose. Each words file must replace every passage the
reading-level tool counts (opening, each stop's text and narrative, each choice and consequence,
each leg's story, each ending), so no telling mixes two bands, and each version must MEASURE
inside its own band (tools/jaunt_reading_level.py), stricter than the one-band slack the gate
allows. A stop's `read_s` is the base's, scaled by the words. The 18+ tellings are not
retold for students (the owner, 2026-11-14: students see the build-up and the aftermath only), and
the build log (prairie-built-so-far) is the project's own progress walk, not a story to retell.

T-3623 (the owner, 2026-11-16: "Do 18+ jaunts for all jaunts, fill them in"): a words file named
<base id>-adults.txt makes the 18+ telling of a jaunt (`audience: adults`, listed only behind
Settings' 18+ jaunts, never in a teacher handout). It is the same walk told for grown readers:
fuller and franker, drawing the hard parts of the base's own evidence into the prose (drink, debt,
disease, death, money, class), with no warning and no word of its audience in the telling. No fact
enters it that the base and its evidence do not state, and the fighting is staged only where the
1812 adults jaunts (docs/RESEARCH/jaunt-stage-1812-3553/adults.py) already stage it, so a version
here copies its base's stage as it stands. Its band is whatever its words measure. It must replace
the opening, every stop's text and every ending; a choice, a leg or a narrative line it leaves out
keeps the base's words. Two keys are its own:

    warning                         the 18+ tag's tooltip (default below)
    cite <stop id>                  base evidence ids, space-separated, the stop's text also cites

T-3696 (the owner, 2026-11-19: transitions between topics and pauses between subjects; "that
smother narration rule applies for all the jaunts"): every telling is written to be heard. A stop
groups its facts into a few subjects joined by short lines that carry no fact ("Now, about this
house."), never more than about five bare facts in a row, and ends on the hand-on. A joining line
must still keep the telling inside its band; the reading-level tool counts it like any other
words. docs/AUDIO.md § Narration style; docs/JAUNTS-AUTHORING.md § Spoken words.

Words file format: a line `== <key>` starts a passage, and the passage runs to the next such
line (blank lines inside are kept, ends trimmed). Keys:

    premise                         the card's line
    opening                         the opening text
    stop <stop id>                  a stop's text
    narrative <stop id>             a stop's narrative line
    caption <stop id>               a staged stop's caption (optional)
    label <stop id> <choice id>     a choice's label
    consequence <stop id> <choice id>
    leg <n>                         leg n's story (from 0)
    note <n>                        leg n's road note (optional)
    ending <ending id>              an ending's text
    keepsake title / keepsake text  the keepsake card (optional)

    python3 docs/RESEARCH/jaunt-grade-versions-3621/versions.py              # write every version
    python3 docs/RESEARCH/jaunt-grade-versions-3621/versions.py --check      # versions are as built
    python3 docs/RESEARCH/jaunt-grade-versions-3621/versions.py --template B # a base's passages, keyed
    python3 docs/RESEARCH/jaunt-grade-versions-3621/versions.py --report     # each version's measure
"""
import argparse
import copy
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import jaunt_reading_level as rl  # noqa: E402
import check_jaunt_demolitions as demolitions  # noqa: E402

JAUNTS = ROOT / 'data/jaunts'
WORDS = HERE / 'words'
KEY = re.compile(r'^== (.+?)\s*$', re.M)


def suffix(band):
    return '-grades-' + band.lower()


def parse(path):
    text = path.read_text()
    parts = KEY.split(text)
    head, out = parts[0].strip(), {}
    if head:
        raise ValueError(f'{path.name}: text before the first == key')
    for key, body in zip(parts[1::2], parts[2::2]):
        key = ' '.join(key.split())
        if key in out:
            raise ValueError(f'{path.name}: {key} given twice')
        body = body.strip()
        if not body:
            raise ValueError(f'{path.name}: {key} is empty')
        out[key] = body
    return out


def passages(doc):
    """Every passage of a jaunt, keyed as a words file keys it: (key, required)."""
    yield 'premise', True
    yield 'opening', True
    for s in doc['stops']:
        if s.get('text'): yield f"stop {s['id']}", True
        if s.get('narrative'): yield f"narrative {s['id']}", True
        if (s.get('stage') or {}).get('caption'): yield f"caption {s['id']}", False
        for c in s.get('choices', []):
            if c.get('label'): yield f"label {s['id']} {c['id']}", True
            if c.get('consequence'): yield f"consequence {s['id']} {c['id']}", True
    for i, leg in enumerate(doc.get('legs', [])):
        if leg.get('story'): yield f'leg {i}', True
        if leg.get('note'): yield f'note {i}', False
    for e in doc['endings']:
        if e.get('text'): yield f"ending {e['id']}", True
    yield 'keepsake title', False
    yield 'keepsake text', False


def get(doc, key):
    kind, *rest = key.split()
    stops = {s['id']: s for s in doc['stops']}
    if kind == 'premise': return doc['premise']
    if kind == 'opening': return doc['opening']['text']
    if kind == 'stop': return stops[rest[0]]['text']
    if kind == 'narrative': return stops[rest[0]]['narrative']
    if kind == 'caption': return stops[rest[0]]['stage']['caption']
    if kind in ('label', 'consequence'):
        return {c['id']: c for c in stops[rest[0]]['choices']}[rest[1]][kind]
    if kind == 'leg': return doc['legs'][int(rest[0])]['story']
    if kind == 'note': return doc['legs'][int(rest[0])]['note']
    if kind == 'ending': return {e['id']: e for e in doc['endings']}[rest[0]]['text']
    if kind == 'keepsake': return doc['keepsake'][rest[0]]
    raise KeyError(key)


def words(text):
    return max(1, len(rl.WORD.findall(text)))


def scaled(read_s, old, new):
    return max(1, min(600, round(read_s * words(new) / words(old)))) if read_s else read_s


# The 18+ tag's tooltip on a telling that is franker, not bloodier (the owner, 2026-11-16: no
# warning text on the card or in the telling; the compiler still wants a few words for the tag).
WARNING = 'Told in full, for adults.'
# What an 18+ telling must replace; the rest may keep the base's words.
ADULT_REQUIRED = ('opening', 'stop', 'ending')


def build(path, strict=True):
    """The version a words file makes, from its base jaunt as it stands now."""
    adults = re.fullmatch(r'(.+)-adults', path.stem)
    m = adults or re.fullmatch(r'(.+)-grades-(3-5|6-8|9-10|11-12|k-2)', path.stem)
    if not m:
        raise ValueError(f'{path.name}: a words file is named <base id>-grades-<band>.txt or <base id>-adults.txt')
    base_id, band = m[1], (None if adults else m[2].upper())
    base = json.loads((JAUNTS / f'{base_id}.json').read_text())
    if base.get('version_of') or base.get('audience') == 'adults':
        raise ValueError(f'{path.name}: {base_id} is itself a version')
    if band and base['grade_band'] == band:
        raise ValueError(f'{path.name}: {base_id} is already written for grades {band}')
    w = parse(path)
    keys = dict(passages(base))
    if adults:
        keys = {k: k.split()[0] in ADULT_REQUIRED for k in keys}
        keys['warning'] = False
        keys.update({f"cite {s['id']}": False for s in base['stops']})
    missing = [k for k, required in keys.items() if required and k not in w]
    unknown = [k for k in w if k not in keys]
    if missing or unknown:
        raise ValueError(f'{path.name}: ' + '; '.join(
            ([f"missing {', '.join(missing)}"] if missing else []) + ([f"no such passage {', '.join(unknown)}"] if unknown else [])))
    doc = copy.deepcopy(base)
    doc['id'] = path.stem
    doc['grade_band'] = band or base['grade_band']
    doc['version_of'] = base_id
    if adults:
        doc['audience'] = 'adults'
        doc['content_warning'] = w.pop('warning', WARNING)
        doc['featured'] = False
    doc['content_version'] = 1
    doc.pop('menu_rank', None)
    doc['keepsake']['id'] = base['keepsake']['id'] + ('-adults' if adults else suffix(band))
    stops = {s['id']: s for s in doc['stops']}
    known = {e['id'] for e in base['evidence']}
    for key, text in w.items():
        kind, *rest = key.split()
        if kind == 'cite':
            ids = text.split()
            stray = [i for i in ids if i not in known]
            if stray:
                raise ValueError(f"{path.name}: cite {rest[0]}: {', '.join(stray)} is not the base's evidence")
            have = stops[rest[0]].setdefault('evidence', [])
            have.extend(i for i in ids if i not in have)
            continue
        old = get(base, key)
        if kind == 'premise': doc['premise'] = text
        elif kind == 'opening':
            doc['opening']['text'] = text
            doc['opening']['read_s'] = scaled(base['opening']['read_s'], old, text)
        elif kind == 'caption': stops[rest[0]]['stage']['caption'] = text
        elif kind in ('stop', 'narrative'): stops[rest[0]]['text' if kind == 'stop' else 'narrative'] = text
        elif kind in ('label', 'consequence'):
            {c['id']: c for c in stops[rest[0]]['choices']}[rest[1]][kind] = text
        elif kind == 'leg': doc['legs'][int(rest[0])]['story'] = text
        elif kind == 'note': doc['legs'][int(rest[0])]['note'] = text
        elif kind == 'ending':
            e = {e['id']: e for e in doc['endings']}[rest[0]]
            e['text'] = text
            e['read_s'] = scaled(e['read_s'], old, text)
        elif kind == 'keepsake': doc['keepsake'][rest[0]] = text
    # A stop reads for as long as its text and narrative take, scaled from the base's pace.
    for s, b in zip(doc['stops'], base['stops']):
        old = ' '.join(x for x in (b.get('text', ''), b.get('narrative', '')) if x)
        new = ' '.join(x for x in (s.get('text', ''), s.get('narrative', '')) if x)
        if old: s['read_s'] = scaled(b['read_s'], old, new)
    # compile_jaunts: a stop tells 25-60 words, or up to 150 in a long-form jaunt (T-3355).
    most = 150 if doc.get('long_form') else 60
    for s in doc['stops']:
        n = len((s['text'] + ' ' + s.get('narrative', '')).split())
        if not 25 <= n <= most:
            raise ValueError(f"{path.name}: stop {s['id']} tells {n} words; a stop needs 25-{most}")
    # check_jaunt_demolitions: a 1904 stop at a house later torn down gives the year it went.
    torn = demolitions.problems([(path.name, doc)], json.loads(demolitions.TABLE.read_text())['houses'])
    if torn:
        raise ValueError('; '.join(torn))
    got = rl.band_of(rl.measure(doc)['grade'])
    if adults:
        # An 18+ telling is for grown readers at whatever level its words read.
        doc['grade_band'] = got
    elif strict and got != band:
        raise ValueError(f'{path.name}: written for grades {band} but reads at grade {rl.measure(doc)["grade"]} ({got})')
    return doc


def dump(doc):
    return json.dumps(doc, ensure_ascii=False, indent=2) + '\n'


def template(base_id):
    base = json.loads((JAUNTS / f'{base_id}.json').read_text())
    for key, required in passages(base):
        try:
            text = get(base, key)
        except KeyError:
            continue
        print(f'== {key}' + ('' if required else '    (optional)'))
        print(text)
        print()
    if EVIDENCE:
        print('---- evidence (the facts a retelling may draw on) ----')
        for e in base['evidence']:
            print(f"[{e['id']}] {e['text']}")


EVIDENCE = False


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--report', action='store_true')
    ap.add_argument('--template')
    ap.add_argument('--evidence', action='store_true', help='with --template, list the base evidence too')
    ap.add_argument('only', nargs='*', help='words files to build (default every one)')
    args = ap.parse_args()
    global EVIDENCE
    EVIDENCE = args.evidence
    if args.template:
        return template(args.template)
    paths = sorted(WORDS.glob('*.txt'))
    if args.only:
        paths = [p for p in paths if p.stem in args.only or p.name in args.only]
    bad, stale = [], []
    for path in paths:
        try:
            doc = build(path, strict=not args.report)
        except (ValueError, KeyError) as e:
            bad.append(str(e))
            continue
        out = JAUNTS / f'{path.stem}.json'
        body = dump(doc)
        if args.report:
            m = rl.measure(doc)
            ok = rl.band_of(m['grade']) == doc['grade_band']
            print(f"{doc['scene']}  {m['grade']:>5}  {doc['grade_band']:>5}  {m['words']:>5}w  {path.stem}" + ('' if ok else '   <- OUT OF BAND'))
        if args.check:
            if not out.exists() or out.read_text() != body:
                stale.append(path.stem)
        elif not args.report:
            out.write_text(body)
    if bad:
        sys.exit('VERSIONS FAIL\n' + '\n'.join(bad))
    if stale:
        sys.exit('VERSIONS STALE (run versions.py): ' + ', '.join(stale))
    print(f'versions: {len(paths)} ' + ('as built' if args.check else 'checked' if args.report else 'written'))


if __name__ == '__main__':
    main()
