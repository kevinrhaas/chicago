#!/usr/bin/env python3
"""Validate the 1871 research dossier and derive its viewer/Markdown exports."""
import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'data/research_1871.json'


def validate(data):
    for key in ('title', 'updated', 'scope'):
        assert isinstance(data.get(key), str) and data[key].strip(), key
    assert data.get('cards') and data.get('year_audit') and data.get('readiness')
    ids = set()
    for card in data['cards']:
        assert card['id'] not in ids, f"duplicate {card['id']}"
        ids.add(card['id'])
        for key in ('id', 'category', 'title', 'statement', 'applies_to',
                    'render_implication', 'limits', 'next_step'):
            assert isinstance(card.get(key), str) and card[key].strip(), (card['id'], key)
        assert card['evidence_status'] in ('documented', 'inferred', 'open'), card['id']
        assert card.get('sources'), card['id']
        for source in card['sources']:
            for key in ('title', 'url', 'locator', 'source_date', 'source_kind'):
                assert isinstance(source.get(key), str) and source[key].strip(), (card['id'], key)
            assert urlparse(source['url']).scheme == 'https', source['url']
            assert source['access'] in ('read', 'catalog_only', 'lead'), source['access']
            if 'reference_image' in source:
                image = source['reference_image']
                assert isinstance(image, dict) and source['access'] == 'read', card['id']
                for key in ('local_image', 'alt', 'caption', 'credit', 'rights', 'sha256'):
                    assert isinstance(image.get(key), str) and image[key].strip(), (card['id'], key)
                assert not urlparse(image['local_image']).scheme, card['id']
                path = (ROOT / 'viewer' / image['local_image']).resolve()
                assert path.is_relative_to((ROOT / 'media/research').resolve()), path
                assert path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp'), path
                assert type(image.get('bytes')) is int and image['bytes'] > 0, card['id']
                assert all(type(image.get(k)) is int and image[k] > 0 for k in ('width', 'height')), card['id']
                assert re.fullmatch('[a-f0-9]{64}', image['sha256']), card['id']
                assert path.is_file() and path.stat().st_size == image['bytes'], path
                assert hashlib.sha256(path.read_bytes()).hexdigest() == image['sha256'], path
    for year in data['year_audit']:
        assert all(year.get(k) for k in ('year', 'status', 'summary', 'lessons', 'references'))
        assert 'date' in year and (year['date'] is None or isinstance(year['date'], str))
        assert all(urlparse(r['url']).scheme == 'https' for r in year['references'])
    for task in data['readiness']:
        assert all(task.get(k) for k in ('title', 'priority', 'deliverable', 'acceptance'))


def markdown(data):
    lines = [f"# {data['title']}", '', f"Research snapshot: {data['updated']}", '', data['scope'], '',
             'This document is generated from `data/research_1871.json` by `tools/build_research.py`.', '',
             '## Reading the evidence', '',
             'Documented means the cited source supports the stated claim; it does not certify measured geometry, primary-source status, or exact presence on the scene date. Inferred marks a reasoned reconstruction. Open marks an unresolved question. Source access is recorded separately: read, catalog only, or lead. Rendering implications are proposals unless independently attested. Linked reference scans document the evidence; they do not establish completed geometry, a solved camera or scene-time presence.', '',
             '## Other years: what the existing project teaches', '', data.get('audit_snapshot', ''), '']
    for item in data['year_audit']:
        lines += [f"### {item['year']} — {item['status']}", '', f"Date: {item['date'] or 'No single implemented scene date'}", '', item['summary'], '']
        lines += [f'- {s}' for s in item['lessons']]
        lines += ['', *[f"- [{r['title']}]({r['url']})" for r in item['references']], '']
    lines += ['## Evidence and rendering requirements', '']
    for card in data['cards']:
        lines += [f"### {card['title']}", '', f"`{card['id']}` · {card['category']} · **{card['evidence_status']}**", '',
                  card['statement'], '', f"**Applies to:** {card['applies_to']}", '',
                  f"**Rendering implication:** {card['render_implication']}", '',
                  f"**Limits:** {card['limits']}", '', f"**Next step:** {card['next_step']}", '', '**Sources:**', '']
        for s in card['sources']:
            lines += [f"- [{s['title']}]({s['url']}) — {s['source_date']}. {s['source_kind']}; access: {s['access']}. Locator: {s['locator']}."]
            if image := s.get('reference_image'):
                lines += ['', f"  [Open reference image]({image['local_image']}) — {image['caption']}",
                          f"  Credit: {image['credit']} Rights: {image['rights']}",
                          f"  SHA-256: `{image['sha256']}`.", '']
        lines += ['']
    lines += ['## Before rendering 1871', '']
    for item in data['readiness']:
        lines += [f"### {item['priority']} · {item['title']}", '', item['deliverable'], '', f"Acceptance: {item['acceptance']}", '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = json.loads(SOURCE.read_text())
    validate(data)
    # Audit every supported year using the existing viewer's inclusive year rule.
    # This is index coverage, never a historical census or an exact-day existence ruling.
    buildings = list(csv.DictReader((ROOT / 'data/buildings.csv').open()))
    media = list(csv.DictReader((ROOT / 'data/media_buildings.csv').open()))
    linked = {row['building_id'] for row in media}
    def year(value):
        match = re.search(r'\d{4}', value or '')
        return int(match[0]) if match else None
    coverage = io.StringIO()
    writer = csv.writer(coverage, lineterminator='\n')
    writer.writerow(['year', 'active_index_records', 'flagged_for_review', 'with_linked_media', 'with_point_coordinates', 'date_resolution'])
    for y in range(1674, 1872):
        active = [r for r in buildings if (year(r.get('year_completed')) or year(r.get('year_started')) or 9999) <= y
                  and (year(r.get('year_demolished')) or 9999) >= y]
        writer.writerow([y, len(active), sum(r['needs_review'] == 'true' for r in active),
                         sum(r['building_id'] in linked for r in active),
                         sum(bool(r.get('latitude') and r.get('longitude')) for r in active),
                         'inclusive year-level index; not exact-day occupancy'])
    outputs = {ROOT / 'viewer/research-1871.json': json.dumps(data, ensure_ascii=False, indent=2) + '\n',
               ROOT / 'viewer/year-coverage.csv': coverage.getvalue(),
               ROOT / 'docs/research_1871.md': markdown(data)}
    for path, content in outputs.items():
        if args.check:
            assert path.exists() and path.read_text() == content, f'Stale: {path}; run tools/build_research.py'
        else:
            path.write_text(content)
    print(f"Research {'current' if args.check else 'built'}: {len(data['cards'])} cards, "
          f"{len({s['url'] for c in data['cards'] for s in c['sources']})} source URLs, "
          f"{len(data['year_audit'])} year/period audits")


if __name__ == '__main__':
    main()
