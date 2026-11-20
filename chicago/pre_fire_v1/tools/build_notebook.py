#!/usr/bin/env python3
"""Validate primary-source observations and build deterministic web/CSV exports."""
import argparse
import csv
import hashlib
import html
import io
import json
import math
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'data/field_notebook_1871.json'
BASIS = {'listed', 'scheduled', 'reported-built', 'reported-condition', 'reported-event', 'proposal', 'measured'}


def require_strings(obj, keys):
    for key in keys:
        assert isinstance(obj.get(key), str) and obj[key].strip(), (obj.get('id'), key)


def index(items):
    ids = [x['id'] for x in items]
    assert len(ids) == len(set(ids)), 'Duplicate IDs'
    assert all(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', x) for x in ids), 'Invalid ID'
    return {x['id']: x for x in items}


def validate(data):
    require_strings(data, ('title', 'scope', 'updated', 'method'))
    books, pages, records, packets = [index(data[k]) for k in ('books', 'pages', 'records', 'scene_packets')]
    assert all((books, pages, records, packets, data['corrections'])), 'Empty notebook section'
    for book in books.values():
        require_strings(book, ('title', 'author', 'archive_id', 'url', 'date_scope', 'rights', 'bias'))
        assert urlparse(book['url']).scheme == 'https'
        assert isinstance(book['publication_year'], int) and book['publication_year'] <= 1871
    for page in pages.values():
        require_strings(page, ('title', 'printed_page', 'verification', 'inspected_on', 'sha256'))
        for key in ('scan_label', 'image_note'):
            if key in page:
                require_strings(page, (key,))
        assert page['book_id'] in books, page['id']
        assert isinstance(page['scan_index'], int) and page['scan_index'] >= 0
        for key in ('url', 'image_url'):
            assert urlparse(page[key]).scheme == 'https', page['id']
        assert re.fullmatch('[a-f0-9]{64}', page['sha256']), page['id']
        assert isinstance(page['bytes'], int) and page['bytes'] > 0
        if page['local_image']:
            path = (ROOT / 'viewer' / page['local_image']).resolve()
            assert path.is_relative_to((ROOT / 'media/research').resolve()), path
            assert path.exists(), path
            assert path.stat().st_size == page['bytes'], path
            assert hashlib.sha256(path.read_bytes()).hexdigest() == page['sha256'], path
    for record in records.values():
        require_strings(record, ('topic', 'title', 'historical_location', 'date_scope', 'finding', 'locator', 'excerpt', 'render_use', 'limitations'))
        assert record['evidence_type'] in BASIS, record['id']
        assert record['source_ids'] and all(s in pages for s in record['source_ids']), record['id']
        for quantity in record['quantities']:
            require_strings(quantity, ('name', 'unit', 'qualifier'))
            assert type(quantity['value']) in (int, float) and math.isfinite(quantity['value']), record['id']
    for packet in packets.values():
        require_strings(packet, ('title', 'historical_location', 'purpose', 'status'))
        assert packet['record_ids'] and all(r in records for r in packet['record_ids']), packet['id']
        for key in ('proposed_actions', 'unresolved', 'exclude'):
            assert packet[key] and all(isinstance(s, str) and s.strip() for s in packet[key]), packet['id']
    for correction in data['corrections']:
        require_strings(correction, ('title', 'before', 'after'))
        assert correction['record_ids'] and all(r in records for r in correction['record_ids'])
    dossier = json.loads((ROOT / 'data/research_1871.json').read_text())
    for card in dossier['cards']:
        assert all(r in records for r in card.get('notebook_ids', [])), card['id']


def exports(data):
    pages = index(data['pages'])
    books = index(data['books'])
    records = index(data['records'])
    stream = io.StringIO()
    fields = ['id', 'topic', 'title', 'historical_location', 'date_scope', 'evidence_type', 'finding', 'locator', 'excerpt', 'render_use', 'limitations', 'quantities_json', 'source_ids', 'source_urls', 'source_pages', 'verification']
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    for record in data['records']:
        row = {key: record[key] for key in fields if key in record}
        row['quantities_json'] = json.dumps(record['quantities'], ensure_ascii=False)
        row['source_ids'] = ' | '.join(record['source_ids'])
        row['source_urls'] = ' | '.join(pages[s]['url'] for s in record['source_ids'])
        row['source_pages'] = ' | '.join(books[pages[s]['book_id']]['title'] + ', p. ' + pages[s]['printed_page'] for s in record['source_ids'])
        row['verification'] = ' | '.join(pages[s]['verification'] for s in record['source_ids'])
        # Neutralize spreadsheet formulas if future transcriptions begin with a formula marker.
        writer.writerow({k: "'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@')) else v for k, v in row.items()})
    e = lambda value: html.escape(str(value), quote=True)
    def para(label, value):
        return f'<p><strong>{e(label)}</strong> {e(value)}</p>'
    def items(values):
        return '<ul>' + ''.join('<li>' + e(v) + '</li>' for v in values) + '</ul>'
    def refs(ids):
        return '<ul>' + ''.join(f'<li><a href="#record-{e(r)}">{e(records[r]["title"])}</a></li>' for r in ids) + '</ul>'
    out = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>1871 field notebook — reading edition</title><link rel="stylesheet" href="research.css"><link rel="stylesheet" href="notebook.css"></head><body>',
           '<header class="masthead"><a href="notebook.html">← Searchable field notebook</a><h1>Reading <em>edition</em></h1>', f'<p>{e(data["scope"])}</p><p>{e(data["method"])}</p><p>Updated {e(data["updated"])} · Complete edition; works without JavaScript.</p><nav class="page-nav"><a href="#scenes">Scene studies</a><a href="#observations">Observations</a><a href="#sources">Sources</a><a href="#revisions">Revisions</a></nav></header><main>']
    out.append('<section id="scenes"><h2>Proposed scene studies</h2>')
    for packet in data['scene_packets']:
        out += [f'<article class="audit-card" id="scene-{e(packet["id"])}"><h3>{e(packet["title"])}</h3>', para('Status:', packet['status']), para('Where:', packet['historical_location']), '<p>' + e(packet['purpose']) + '</p>', '<h4>Evidence</h4>', refs(packet['record_ids']), '<h4>Proposed actions</h4>', items(packet['proposed_actions']), '<h4>Still unresolved</h4>', items(packet['unresolved']), '<h4>Keep out of this reconstruction</h4>', items(packet['exclude']), '</article>']
    out.append('</section><section id="observations"><h2>Field observations</h2>')
    for record in data['records']:
        out += [f'<article class="audit-card" id="record-{e(record["id"])}"><p class="eyebrow">{e(record["topic"])} · {e(record["evidence_type"])}</p><h3>{e(record["title"])}</h3>', '<p>' + e(record['finding']) + '</p>']
        for label, key in [('Historical location:', 'historical_location'), ('Date scope:', 'date_scope'), ('Transcription / locating text:', 'excerpt'), ('Proposed rendering use:', 'render_use'), ('Limits:', 'limitations'), ('Locator:', 'locator')]:
            out.append(para(label, record[key]))
        if record['quantities']:
            out += ['<h4>Quantities</h4>', items(f'{q["name"]}: {q["value"]} {q["unit"]} ({q["qualifier"]})' for q in record['quantities'])]
        out.append('<ul>' + ''.join(f'<li><a href="#source-{e(s)}">{e(books[pages[s]["book_id"]]["title"])} · p. {e(pages[s]["printed_page"])}</a></li>' for s in record['source_ids']) + '</ul></article>')
    out.append('</section><section id="sources"><h2>Source register</h2>')
    for book in data['books']:
        out += [f'<article class="audit-card"><h3>{e(book["title"])}</h3>', para('Reporting period:', book['date_scope']), para('Reading limits:', book['bias']), para('Rights:', book['rights'])]
        for page in data['pages']:
            if page['book_id'] != book['id']:
                continue
            out += [f'<p id="source-{e(page["id"])}"><a href="{e(page["url"])}">p. {e(page["printed_page"])} · {e(page["title"])}</a> · {e(page["verification"])} · <a href="{e(page["local_image"] or page["image_url"])}">Open original scan</a></p>']
            if page.get('scan_label'):
                out.append(para('Scan locator:', page['scan_label']))
            if page.get('image_note'):
                out.append(para('Local image:', page['image_note']))
        out.append('</article>')
    out.append('</section><section id="revisions"><h2>What this pass changes</h2>')
    for correction in data['corrections']:
        out += [f'<article class="audit-card"><h3>{e(correction["title"])}</h3>', para('Earlier:', correction['before']), para('Now:', correction['after']), refs(correction['record_ids']), '</article>']
    out.append('</section></main><footer><a href="notebook.html">Return to searchable notebook</a></footer></body></html>\n')
    return {'field-notebook-1871.json': json.dumps(data, ensure_ascii=False, indent=2) + '\n', 'field-observations-1871.csv': stream.getvalue(), 'notebook-reading.html': '\n'.join(out)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = json.loads(SOURCE.read_text())
    validate(data)
    for name, content in exports(data).items():
        path = ROOT / 'viewer' / name
        if args.check:
            assert path.exists() and path.read_text() == content, f'Stale {path}; run tools/build_notebook.py'
        else:
            path.write_text(content)
    print(f"Notebook {'current' if args.check else 'built'}: {len(data['records'])} observations, {len(data['pages'])} source pages, {len(data['scene_packets'])} proposed scene studies")


if __name__ == '__main__':
    main()
