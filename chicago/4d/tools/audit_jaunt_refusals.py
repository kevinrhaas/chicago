#!/usr/bin/env python3
"""The content refusals, read across every jaunt (T-2040, piece 2 of T-1271).

`compile_jaunts.py` proves a jaunt is WELL-FORMED: its claims resolve, its graph is
finite, its destinations stand on the scene date. It does not read what a jaunt SAYS.
Four things a jaunt must never say are standing rules of this project, and until now
each was held by the author's care alone:

  I  NO RECONSTRUCTED INDIGENOUS ENCOUNTER (AGENTS.md § Standing constraint). A jaunt
     never sends the visitor to call at a Native or Métis home or business; never
     names an Indigenous subject in its invented voice (premise, opening, choices,
     endings, keepsake, narrative lines); and never names one in a told passage
     (stop text, leg) unless an attested or inferred claim of that passage names it
     too, no reconstructed claim of that passage touches the subject, and the
     sentence does not put the visitor in it ("you", "your").
  F  NO HUMAN-FIGURE DEPICTION (L1). A jaunt is text and a route; it carries no asset
     of any kind, and its schema stays closed so that no field can be added to carry
     one without this gate seeing the schema change. Its destinations are places —
     a person destination resolves to the house, never to a drawn figure.
  Q  NO QUOTATION PUT IN A NAMED PERSON'S MOUTH. Every quoted span must stand
     verbatim in an ATTESTED claim the passage cites (the invented voices may use
     any attested claim of the jaunt), so a quotation is always a source's words
     with a locator and never the story's. And no named person "tells you", "asks
     you", "greets you" — reported speech to the visitor is dialogue without the
     quotation marks.
  R  ASSET RIGHTS RESPECTED (AGENTS.md hard rule 6). A jaunt publishes to every
     visitor, so it may not cite a `restricted` source (redistribution forbidden);
     a `check_required` source may be cited in text, which is all a jaunt does,
     and the F rule is what keeps it to text.

    python3 tools/audit_jaunt_refusals.py              the table, exit 1 on a finding
    python3 tools/audit_jaunt_refusals.py --self-test  break each rule in memory

WHAT THIS DOES NOT READ, AND SAYS SO. A sentence that describes an unnamed
person's appearance in invented prose is not detected: there is no lexicon for it
that would not also refuse "a sale room and a wet street". The shape of the library
(stop counts, quiet outings, keepsake families, ranks) is T-2039's; the timing is
T-2041's. Name exemptions are listed in NAME_EXEMPT, each with the record whose
proper name the term is, and an exemption only applies to a jaunt that references
that record.
"""
import argparse
import copy
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compile_jaunts import Compiler, NOT_JAUNTS, ROOT, read  # noqa: E402

INDIGENOUS = [r'potawatomi\w*', r'pottawat+omi\w*', r'ojibw\w*', r'chippewa\w*', r'odawa\w*',
              r'ottawas?', r'menomin\w*', r'ho-chunk', r'winnebago\w*', r'sauks?', r'kickapoo\w*',
              r'miamis?', r'm[ée]tis', r'half-?breeds?', r'indians?', r'indigenous',
              r'natives?(?! of\b)', r'tribes?', r'tribal', r'wigwams?', r'treaty', r'treaties',
              r'annuit(?:y|ies)', r'the removal', r'pow-?wows?', r'war dance', r'squaws?']
# A term that is the proper name of a record, and so names a place rather than a people.
# Applied only to a jaunt that references the record (destination or link).
NAME_EXEMPT = {
    'sauganash': ('sauganash_hotel', "the Sauganash is Mark Beaubien's tavern, named for "
                  "Billy Caldwell; the word in a jaunt names the house"),
}
SPEECH = re.compile(r"\b(?:tells|told|asks|asked|says|said|greets|greeted|welcomes|welcomed|warns|"
                    r"warned|answers|answered|assures|assured|bids|bade|calls|called|whispers|"
                    r"shouts|invites|invited|offers|offered)\s+(?:to\s+)?(?:you|your)\b", re.I)
SECOND = re.compile(r"\b(?:you|your|yours|yourself)\b", re.I)
QUOTE = re.compile(r"(?:(?<=\s)|^|(?<=[(\[—]))(['‘\"“])(.+?)(['’\"”])(?=[\s.,;:!?)—]|$)")
ASSET = re.compile(r"\.(?:glb|gltf|png|jpe?g|webp|svg|gif|mp3|ogg|wav|mp4)\b|\bassets/|https?://", re.I)
TITLES = r"(?:Mr|Mrs|Miss|Dr|Col|Rev|Capt|Major|Judge|Squire|Gen|Lt)\.?\s+[A-Z][\w'-]+"
DEST_KINDS = {'structure', 'anchor', 'intersection', 'person', 'business'}
LINK_KINDS = DEST_KINDS - {'anchor', 'intersection'} | {'source', 'topic'}


def val(v):
    return v.get('value') if isinstance(v, dict) else v


def norm(text):
    text = text.lower().replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    return re.sub(r'\s+', ' ', text)


def sentences(text):
    return [s for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]


def passages(doc):
    """(where, voice, text, evidence ids). `told` passages stand on their own claims;
    `invented` ones are the story's voice and may stand on any claim of the jaunt."""
    every = [e['id'] for e in doc['evidence']]
    yield 'title', 'invented', doc['title'], every
    yield 'premise', 'invented', doc['premise'], every
    yield 'opening', 'invented', doc['opening']['text'], every
    yield 'keepsake', 'invented', doc['keepsake']['title'] + '. ' + doc['keepsake']['text'], every
    for s in doc['stops']:
        yield f"{s['id']}", 'told', s['text'], s['evidence']
        if s.get('narrative'):
            yield f"{s['id']}.narrative", 'invented', s['narrative'], s['evidence']
        for c in s.get('choices', []):
            yield f"{s['id']}.{c['id']}", 'invented', c['label'] + '. ' + c.get('consequence', ''), s['evidence']
        for link in s.get('links', []):
            yield f"{s['id']}.link:{link['id']}", 'invented', link['label'], s['evidence']
    for i, leg in enumerate(doc.get('legs', [])):
        ev = leg['evidence'] + leg.get('story_evidence', [])
        for k in ('note', 'story'):
            if leg.get(k):
                yield f"leg{i}.{k}", 'told', leg[k], ev
    for e in doc['endings']:
        yield f"ending:{e['id']}", 'invented', e['text'], every


class Audit:
    def __init__(self, compiler):
        self.c = compiler
        people = list(compiler.refs['person'].values())
        native = [p for p in people if p.get('community') in ('native', 'metis') or p.get('touches_removal')]
        self.native_people = {p['id'] for p in native}
        self.native_places = {val(p.get(k)) for p in native for k in ('lives_at', 'works_at')} - {None}
        self.native_business = {b['id'] for b in compiler.refs['business'].values()
                                if b.get('proprietor_community') in ('native', 'metis')}
        names = set()
        for p in native:
            for part in re.split(r'\s*[()]\s*', p.get('name') or ''):
                if len(part) >= 4: names.add(re.escape(part.lower()))
        self.indigenous = re.compile(r'\b(?:' + '|'.join(INDIGENOUS + sorted(names, key=len, reverse=True)) + r')\b', re.I)
        full = {p['name'] for p in people if p.get('name') and len(p['name'].split()) >= 2}
        self.person_names = [re.compile(r'\b' + re.escape(n) + r'\b') for n in sorted(full, key=len, reverse=True)]

    def named(self, sentence, doc):
        labels = [l['label'] for s in doc['stops'] for l in s.get('links', []) if l['kind'] == 'person']
        return (re.search(TITLES, sentence) or any(l in sentence for l in labels)
                or any(rx.search(sentence) for rx in self.person_names))

    def subjects(self, text, refs):
        """The Indigenous terms in a text that are not a referenced record's own name."""
        return [m.group(0) for m in self.indigenous.finditer(text)
                if not (NAME_EXEMPT.get(m.group(0).lower()) and NAME_EXEMPT[m.group(0).lower()][0] in refs)]

    def jaunt(self, doc):
        findings, notes = [], {'terms': 0, 'exempt': 0, 'quotes': 0, 'sources': {}}
        claims = {e['id']: e for e in doc['evidence']}
        refs = {s['destination']['id'] for s in doc['stops']} | {
            l['id'] for s in doc['stops'] for l in s.get('links', [])}
        def say(rule, where, text):
            findings.append((rule, where, text))
        # I — destinations: no call at a Native or Métis home or business.
        for s in doc['stops']:
            d = s['destination']
            if (d['kind'] == 'person' and d['id'] in self.native_people) or \
               (d['kind'] == 'business' and d['id'] in self.native_business) or \
               (d['kind'] == 'structure' and d['id'] in self.native_places):
                say('I-destination', s['id'], f"sends the visitor to {d['kind']} {d['id']}, a Native or Métis home or business")
        # I, Q — every passage the visitor reads.
        for where, voice, text, ev in passages(doc):
            cited = [claims[e] for e in ev if e in claims]
            for sentence in sentences(text):
                for m in self.indigenous.finditer(sentence):
                    term = m.group(0).lower()
                    notes['terms'] += 1
                    exempt = NAME_EXEMPT.get(term)
                    if exempt and exempt[0] in refs:
                        notes['exempt'] += 1
                        continue
                    if voice == 'invented':
                        say('I-invented-voice', where, f"'{m.group(0)}' in the story's invented voice")
                    elif not any(c['confidence'] in ('attested', 'inferred') and term in norm(c['text']) for c in cited):
                        say('I-unbacked', where, f"'{m.group(0)}' named with no attested or inferred claim of the passage naming it")
                    elif any(c['confidence'] == 'reconstructed' and self.subjects(c['text'], refs) for c in cited):
                        say('I-reconstructed', where, f"'{m.group(0)}' told beside a reconstructed claim touching the subject")
                    elif SECOND.search(sentence):
                        say('I-encounter', where, f"'{m.group(0)}' in a sentence that puts the visitor in it")
                if SPEECH.search(sentence) and self.named(sentence, doc):
                    say('Q-speech', where, f"a named person speaks to the visitor: {sentence[:90]!r}")
            pool = [c for c in (doc['evidence'] if voice == 'invented' else cited) if c['confidence'] == 'attested']
            for m in QUOTE.finditer(text):
                notes['quotes'] += 1
                frags = [f for f in re.split(r'\s*(?:\[[^\]]*\]|…|\.\.\.)\s*', norm(m.group(2))) if f.strip()]
                if not any(all(f in norm(c['text']) for f in frags) for c in pool):
                    say('Q-quotation', where, f"{m.group(0)} stands verbatim in no attested claim it cites")
        # F — no asset anywhere outside the claims; R — no restricted source.
        def strings(o, path):
            if isinstance(o, dict):
                for k, v in o.items():
                    if path == '' and k == 'evidence': continue
                    yield from strings(v, f'{path}.{k}')
            elif isinstance(o, list):
                for i, v in enumerate(o): yield from strings(v, f'{path}[{i}]')
            elif isinstance(o, str):
                yield path, o
        for path, text in strings(doc, ''):
            if ASSET.search(text):
                say('F-asset', path, f"carries an asset or URL: {text[:80]!r}")
        cites = {sid for c in doc['evidence'] for sid in c['sources']} | {
            l['id'] for s in doc['stops'] for l in s.get('links', []) if l['kind'] == 'source'}
        for sid in sorted(cites):
            rights = (self.c.refs['source'].get(sid) or {}).get('rights_status', 'missing')
            notes['sources'][rights] = notes['sources'].get(rights, 0) + 1
            if rights in ('restricted', 'missing'):
                say('R-rights', 'sources', f"cites {sid}, whose rights_status is {rights}")
        return findings, notes


def schema_findings(schema):
    """F — the schema is closed at every object, and its kinds are places and records."""
    out = []
    def walk(node, path):
        if isinstance(node, dict):
            if 'properties' in node and node.get('additionalProperties') is not False:
                out.append(('F-schema', path or '/', 'object is open: a field could carry an asset unseen'))
            for k, v in node.items(): walk(v, f'{path}/{k}')
        elif isinstance(node, list):
            for i, v in enumerate(node): walk(v, f'{path}/{i}')
    walk(schema, '')
    defs = schema.get('$defs', {})
    for name, allowed, enum in (('destination', DEST_KINDS, defs.get('destination', {}).get('properties', {}).get('kind', {}).get('enum', [])),
                                ('link', LINK_KINDS, defs.get('stop', {}).get('properties', {}).get('links', {}).get('items', {}).get('properties', {}).get('kind', {}).get('enum', []))):
        if not enum or set(enum) - allowed:
            out.append(('F-schema', name, f'{name} kinds {sorted(set(enum) - allowed) or "missing"} are not places or records'))
    return out


def load():
    scenes = sorted(p.stem for p in (ROOT / 'data/scenes').glob('*.json')
                    if (ROOT / f'data/sidecars/{p.stem}/index.json').exists())
    docs = [read(p) for p in sorted((ROOT / 'data/jaunts').glob('*.json')) if p.name not in NOT_JAUNTS]
    audits = {s: Audit(Compiler(scene_id=s)) for s in scenes if any(d.get('scene') == s for d in docs)}
    return docs, audits, read(ROOT / 'data/jaunts/schema.json')


def run(docs, audits, schema, quiet=False):
    total = schema_findings(schema)
    rows = []
    for doc in docs:
        found, notes = audits[doc['scene']].jaunt(doc)
        total += [(r, f"{doc['id']}:{w}", t) for r, w, t in found]
        rows.append((doc['id'], doc['scene'], notes, len(found)))
    if not quiet:
        print(f"{'jaunt':30} {'scene':5} {'terms':>5} {'exempt':>6} {'quotes':>6}  sources by rights_status  findings")
        for jid, scene, n, f in rows:
            rights = ', '.join(f'{k} {v}' for k, v in sorted(n['sources'].items()))
            print(f"{jid:30} {scene:5} {n['terms']:5} {n['exempt']:6} {n['quotes']:6}  {rights:24} {f}")
        for rule, where, text in total:
            print(f'REFUSED {rule} — {where}: {text}')
        a = next(iter(audits.values()))
        print(f"Native/Métis records a jaunt may not visit: {len(a.native_people)} people, "
              f"{len(a.native_places)} places, {len(a.native_business)} business(es)")
        verdict = 'PASS' if not total else 'FAIL'
        print(f'JAUNT REFUSALS {verdict} — {len(docs)} jaunts, {len(total)} finding(s)')
    return total


def self_test(docs, audits, schema):
    """Break each rule once, in memory, on a real jaunt, and require exactly that rule to fire."""
    base = next(d for d in docs if d['id'] == 'calling-on-neighbors')
    a = audits[base['scene']]
    place = sorted(a.native_places)[0]
    def broken(fn):
        doc = copy.deepcopy(base); fn(doc); return doc
    cases = {
        'I-destination': broken(lambda d: d['stops'][1]['destination'].update(kind='structure', id=place)),
        'I-invented-voice': broken(lambda d: d['endings'][0].update(text=d['endings'][0]['text'] + ' A Potawatomi trader waves.')),
        'I-unbacked': broken(lambda d: d['stops'][1].update(text=d['stops'][1]['text'] + ' Potawatomi traders came here.')),
        'I-encounter': broken(lambda d: (d['evidence'].append({'id': 'x', 'text': 'Potawatomi traders came to the store.', 'confidence': 'attested', 'sources': ['andreas_1884_v1'], 'locator': 'p. 1'}),
                                         d['stops'][1]['evidence'].append('x'), d['stops'][1].update(text=d['stops'][1]['text'] + ' You buy from Potawatomi traders.'))),
        'I-reconstructed': broken(lambda d: (d['evidence'].append({'id': 'x', 'text': 'Potawatomi traders came to the store.', 'confidence': 'attested', 'sources': ['andreas_1884_v1'], 'locator': 'p. 1'}),
                                             d['evidence'].append({'id': 'y', 'text': 'The Potawatomi visit is invented.', 'confidence': 'reconstructed', 'sources': [], 'liberty': d['liberties'][0]}),
                                             d['stops'][1]['evidence'].extend(['x', 'y']), d['stops'][1].update(text=d['stops'][1]['text'] + ' Potawatomi traders came.'))),
        'Q-quotation': broken(lambda d: d['stops'][1].update(text=d['stops'][1]['text'] + " Peck said 'welcome to the town'.")),
        'Q-speech': broken(lambda d: d['stops'][0].update(text=d['stops'][0]['text'] + ' Mrs Rufus Brown tells you the room is ready.')),
        'F-asset': broken(lambda d: d['keepsake'].update(text=d['keepsake']['text'] + ' See assets/figures/brown.glb')),
        'R-rights': broken(lambda d: d['evidence'][0]['sources'].append('ipums_1840_chicago_households')),
    }
    ok = True
    for rule, doc in cases.items():
        fired = {r for r, _, _ in run([doc], audits, schema, quiet=True)}
        good = fired == {rule}
        ok &= good
        print(f"self-test {'PASS' if good else 'FAIL'} — {rule}: fired {sorted(fired) or 'nothing'}")
    def unreferenced(d):
        for s in d['stops']:
            s['links'].clear()
            s['destination'].update(kind='structure', id='peck_store')
    exempt = broken(unreferenced)
    fired = {r for r, _, _ in run([exempt], audits, schema, quiet=True)}
    good = 'I-invented-voice' in fired
    ok &= good
    print(f"self-test {'PASS' if good else 'FAIL'} — a name exemption lapses when the jaunt drops its record: fired {sorted(fired)}")
    open_schema = copy.deepcopy(schema); open_schema['$defs']['stop'].pop('additionalProperties', None)
    good = {r for r, _, _ in schema_findings(open_schema)} == {'F-schema'}
    ok &= good
    print(f"self-test {'PASS' if good else 'FAIL'} — F-schema: an opened stop object is refused")
    clean = not run(docs, audits, schema, quiet=True)
    print(f"self-test {'PASS' if clean else 'FAIL'} — the committed library is clean")
    return ok and clean


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--self-test', action='store_true')
    args = ap.parse_args()
    docs, audits, schema = load()
    if args.self_test:
        sys.exit(0 if self_test(docs, audits, schema) else 1)
    sys.exit(1 if run(docs, audits, schema) else 0)


if __name__ == '__main__':
    main()
