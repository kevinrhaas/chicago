#!/usr/bin/env python3
"""Second reading of Norris's 1844 Chicago directory: T-0566's reading of the
Internet Archive scan checked, entry by entry, against Kim Torp's independent
transcription on genealogytrails.com.

Two hands, two copies, one printed book. This tool does not merge them and it
does not prefer one: it MATCHES them and writes down every place they differ,
both readings verbatim. Nothing in data/research/directories/claims/ is touched.

  --build   write data/research/directories/second_readings/norris_1844_genealogytrails.json
  --check   rebuild in memory and fail if the committed file differs

The match is deterministic: normalise, block on the first three letters of the
surname, take the best difflib ratio inside the block, then sweep what is left
against everything unmatched. No randomness, no threshold tuned per entry.
"""
import argparse, json, re, sys
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A_CLAIMS = ROOT / 'data/research/directories/claims/norris_1844_directory_entries.json'
OUT = ROOT / 'data/research/directories/second_readings/norris_1844_genealogytrails.json'

# The two cached Genealogy Trails pages, and the line ranges that are NOT entries.
# Stated here rather than sniffed, so a later reader can check them against the file.
GT_PAGES = [
    {
        'file': 'data/research/genealogytrails/text/1844directory.txt',
        'url': 'https://genealogytrails.com/ill/cook/1844directory.html',
        'entries': [(26, 1188)],
        'skipped': {
            '1-24': "the page title, Kim Torp's transcriber's note, and Norris's own Remarks",
            '1189-1194': 'the site navigation and the copyright line',
        },
    },
    {
        'file': 'data/research/genealogytrails/text/1844dir2.txt',
        'url': 'https://genealogytrails.com/ill/cook/1844dir2.html',
        'entries': [(12, 846), (854, 973)],
        'skipped': {
            '1-11': "the page title, the transcriber's note, and Norris's Remarks repeated",
            '847-853': "the word 'Addenda' and Norris's prose introducing it",
            '974-976': 'the site navigation and the copyright line',
        },
    },
]
ADDENDA_RANGE = (854, 973)  # in 1844dir2.txt

# An all-caps surname-band heading Kim Torp set between the entries, e.g. "MOODY-NICHOLS".
BAND_RE = re.compile(r"^[A-Z][A-Za-z'’\.]*\s*-{1,2}\s*[A-Z][A-Za-z'’\.]*$")

# Ratios. Above IDENTICAL the two readings are the same string once punctuation and
# case are set aside; above AGREES they are the same entry read slightly differently;
# above MATCH they are the same entry with something really different in it; below,
# nothing is claimed and the entry stands as present in one reading only.
AGREES = 0.90
MATCH = 0.62


def norm(s):
    s = s.lower().replace('&', ' and ')
    s = re.sub(r"[^a-z0-9 ]+", ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def block_key(n):
    first = n.split(' ')[0] if n else ''
    return first[:3]


def read_gt():
    """Every entry line of the two cached pages, verbatim, with its locator.

    A line that does not begin with a capital letter is the tail of the entry above,
    wrapped by the web page: in this cache there are exactly five of them and every
    one is the bare word 'sts'. They are joined back on, and the entry keeps both
    line numbers.
    """
    out = []
    for page in GT_PAGES:
        lines = (ROOT / page['file']).read_text(encoding='utf-8').split('\n')
        for lo, hi in page['entries']:
            for no in range(lo, hi + 1):
                text = lines[no - 1].rstrip()
                if not text.strip():
                    continue
                if BAND_RE.match(text):
                    continue
                if not text[0].isupper() and out and out[-1]['file'] == Path(page['file']).name:
                    out[-1]['quote'] += ' ' + text.strip()
                    out[-1]['wrapped_lines'].append(no)
                    out[-1]['norm'] = norm(out[-1]['quote'])
                    continue
                section = 'directory'
                if page['file'].endswith('1844dir2.txt') and ADDENDA_RANGE[0] <= no <= ADDENDA_RANGE[1]:
                    section = 'addenda'
                out.append({
                    'quote': text,
                    'file': Path(page['file']).name,
                    'line': no,
                    'wrapped_lines': [],
                    'section': section,
                    'norm': norm(text),
                })
    return out


def read_a():
    doc = json.loads(A_CLAIMS.read_text(encoding='utf-8'))
    out = []
    for c in doc['claims']:
        out.append({
            'id': c['id'],
            'quote': c['quote'],
            'kind': c['kind'],
            'section': c['normalized'].get('section'),
            'page': c['locator']['page'],
            'printed_page': c['locator']['printed_page'],
            'norm': norm(c['quote']),
        })
    return out, doc['counts']


def best_pairs(a_items, b_items, candidates_for):
    """Greedy one-to-one matching: score every candidate pair, take the best first."""
    scored = []
    for ai, a in enumerate(a_items):
        for bi in candidates_for(ai):
            b = b_items[bi]
            sm = SequenceMatcher(None, a['norm'], b['norm'])
            if sm.real_quick_ratio() < MATCH or sm.quick_ratio() < MATCH:
                continue
            r = sm.ratio()
            if r >= MATCH:
                scored.append((r, ai, bi))
    scored.sort(key=lambda t: (-t[0], t[1], t[2]))
    pa, pb, pairs = set(), set(), []
    for r, ai, bi in scored:
        if ai in pa or bi in pb:
            continue
        pa.add(ai)
        pb.add(bi)
        pairs.append((ai, bi, r))
    return pairs


def compare():
    a_items, a_counts = read_a()
    b_items = read_gt()

    # Pass 1 — block on the first three letters of the surname, which is where two
    # readings of the same line almost always agree.
    b_by_block = {}
    for bi, b in enumerate(b_items):
        b_by_block.setdefault(block_key(b['norm']), []).append(bi)
    pairs = best_pairs(a_items, b_items,
                       lambda ai: b_by_block.get(block_key(a_items[ai]['norm']), []))

    matched_a = {ai for ai, _, _ in pairs}
    matched_b = {bi for _, bi, _ in pairs}

    # Pass 2 — the residue, swept against every unmatched line. This is what catches
    # a surname whose first letter the OCR lost ("ISickalls" for "Nickalls").
    ra = [ai for ai in range(len(a_items)) if ai not in matched_a]
    rb = [bi for bi in range(len(b_items)) if bi not in matched_b]
    sub_a = [a_items[i] for i in ra]
    sub_b = [b_items[i] for i in rb]
    for x, y, r in best_pairs(sub_a, sub_b, lambda ai: range(len(sub_b))):
        pairs.append((ra[x], rb[y], r))
    matched_a = {ai for ai, _, _ in pairs}
    matched_b = {bi for _, bi, _ in pairs}

    # Pass 3 — an UNAMBIGUOUS name agreement, whatever the rest of the line says.
    # Where exactly one entry is left unmatched on each side whose first three
    # normalised tokens are the same string, they are the same entry: the archive
    # OCR has swallowed the address into a ditto mark and the ratio can never reach
    # the threshold. Requiring uniqueness on BOTH sides is what keeps two different
    # men of one name apart.
    def prefix(n):
        return ' '.join(n.split(' ')[:3])
    ua, ub = {}, {}
    for ai in range(len(a_items)):
        if ai not in matched_a:
            ua.setdefault(prefix(a_items[ai]['norm']), []).append(ai)
    for bi in range(len(b_items)):
        if bi not in matched_b:
            ub.setdefault(prefix(b_items[bi]['norm']), []).append(bi)
    for key, alist in sorted(ua.items()):
        blist = ub.get(key, [])
        if len(alist) == 1 and len(blist) == 1 and key:
            ai, bi = alist[0], blist[0]
            r = SequenceMatcher(None, a_items[ai]['norm'], b_items[bi]['norm']).ratio()
            pairs.append((ai, bi, r))
    matched_a = {ai for ai, _, _ in pairs}
    matched_b = {bi for _, bi, _ in pairs}

    identical, agree, differ = [], [], []
    for ai, bi, r in sorted(pairs, key=lambda t: t[0]):
        a, b = a_items[ai], b_items[bi]
        rec = {
            'archive_id': a['id'],
            'archive_quote': a['quote'],
            'archive_page': a['page'],
            'archive_printed_page': a['printed_page'],
            'genealogytrails_quote': b['quote'],
            'genealogytrails_file': b['file'],
            'genealogytrails_line': b['line'],
            'genealogytrails_wrapped_lines': b['wrapped_lines'] or None,
            'ratio': round(r, 4),
            'section_agrees': a['section'] == b['section'],
        }
        if a['norm'] == b['norm']:
            identical.append(rec)
        elif r >= AGREES:
            agree.append(rec)
        else:
            differ.append(rec)

    only_a = [{
        'archive_id': a_items[ai]['id'],
        'archive_quote': a_items[ai]['quote'],
        'archive_page': a_items[ai]['page'],
        'archive_printed_page': a_items[ai]['printed_page'],
        'section': a_items[ai]['section'],
    } for ai in sorted(set(range(len(a_items))) - matched_a)]
    only_b = [{
        'genealogytrails_quote': b_items[bi]['quote'],
        'genealogytrails_file': b_items[bi]['file'],
        'genealogytrails_line': b_items[bi]['line'],
        'genealogytrails_wrapped_lines': b_items[bi]['wrapped_lines'] or None,
        'section': b_items[bi]['section'],
    } for bi in sorted(set(range(len(b_items))) - matched_b)]

    section_moved = [r for r in identical + agree + differ if not r['section_agrees']]

    # Near-duplicates INSIDE one reading. A transcriber who re-reads a band can set the
    # same entries down twice, and the two copies need not agree with each other; an OCR
    # pass can double a line the same way. Reported, not removed.
    def internal_dupes(items, render):
        by = {}
        for i, it in enumerate(items):
            by.setdefault(' '.join(it['norm'].split(' ')[:3]), []).append(i)
        out = []
        for key, idx in sorted(by.items()):
            if len(idx) < 2 or not key:
                continue
            for x in range(len(idx)):
                for y in range(x + 1, len(idx)):
                    a, b = items[idx[x]], items[idx[y]]
                    r = SequenceMatcher(None, a['norm'], b['norm']).ratio()
                    if r >= MATCH:
                        out.append({'ratio': round(r, 4),
                                    'first': render(a), 'second': render(b),
                                    'the_two_agree': a['norm'] == b['norm']})
        return out

    dupes_a = internal_dupes(a_items, lambda a: {'id': a['id'], 'quote': a['quote'], 'page': a['page']})
    dupes_b = internal_dupes(b_items, lambda b: {'quote': b['quote'], 'file': b['file'], 'line': b['line']})

    gt_sections = {'directory': 0, 'addenda': 0}
    for b in b_items:
        gt_sections[b['section']] += 1

    return {
        'a_items': a_items, 'b_items': b_items, 'a_counts': a_counts,
        'identical': identical, 'agree': agree, 'differ': differ,
        'only_a': only_a, 'only_b': only_b,
        'section_moved': section_moved, 'gt_sections': gt_sections,
        'dupes_a': dupes_a, 'dupes_b': dupes_b,
    }


def build(c):
    n_a, n_b = len(c['a_items']), len(c['b_items'])
    matched = len(c['identical']) + len(c['agree']) + len(c['differ'])
    return {
        'schema': 1,
        '_doc': 'GENERATED by tools/compare_norris_1844_readings.py --build. A COMPARISON, not a reading and not an import: it holds both transcriptions of every entry the two readings disagree about, and prefers neither. Hand-edit and --check says so.',
        'generated_by': 'tools/compare_norris_1844_readings.py --build',
        'ticket': 'T-0576',
        'source_id': 'norris_directory_1844',
        'what': "Norris's General Directory of Chicago for 1844, read twice: once by T-0566 (PR #704) off the Internet Archive scan generaldirectory19norr, and once by Kim Torp for genealogytrails.com, published 2002, from a different copy. Two hands, one printed book. Every disagreement below is a line one of them read differently, and those are the lines hardest to read.",
        'readings': {
            'archive': {
                'label': 'archive',
                'claims_file': 'data/research/directories/claims/norris_1844_directory_entries.json',
                'ticket': 'T-0566',
                'pr': 704,
                'reading': 'transcription_mediated',
                'how': "archive.org's OCR of the University of Illinois scan of the 1903 Bohan republication, committed untidied — 'Win.' for 'Wm.', 'VV.' for 'W.'",
                'entries': n_a,
            },
            'genealogytrails': {
                'label': 'genealogytrails',
                'text_files': [p['file'] for p in GT_PAGES],
                'urls': [p['url'] for p in GT_PAGES],
                'transcriber': 'Kim Torp, © 2002',
                'cached': '2026-09-03, by tools/read_genealogytrails.py --fetch',
                'reading': 'transcription_mediated',
                'how': "a human transcription typed from the printed page; the transcriber states she kept spellings 'as is', added the occasional comma for readability, and marked what she could not read with (sic) or (?)",
                'entries': n_b,
                'lines_not_entries': {p['file']: p['skipped'] for p in GT_PAGES},
                'band_headings_skipped': "all-caps surname-band headings Kim Torp set between the entries, e.g. 'MOODY-NICHOLS'",
            },
        },
        'method': {
            'normalisation': 'lowercase; & written out as and; every character outside a-z 0-9 and space dropped; runs of space collapsed. Nothing is corrected — the comparison is on the two strings as they stand.',
            'matching': 'greedy one-to-one on the difflib SequenceMatcher ratio of the normalised strings. Pass 1 blocks on the first three letters of the leading token; pass 2 sweeps what is left against everything still unmatched, which is what recovers an entry whose first letter the OCR lost.',
            'wrapped_lines': "a genealogytrails line that does not begin with a capital letter is the wrapped tail of the entry above and is joined back on; five lines in this cache, all of them the bare word 'sts'",
            'unambiguous_name_agreement': 'pass 3: where exactly one entry is left unmatched on each side sharing its first three normalised tokens, they are paired whatever the ratio — the archive OCR has swallowed the rest of the line into a ditto mark. Uniqueness on both sides is required, so two men of one name are never joined.',
            'bands': {'identical': 'normalised strings equal', 'agrees': f'ratio >= {AGREES}', 'differs': f'{MATCH} <= ratio < {AGREES}', 'unmatched': f'ratio < {MATCH} against every candidate — stated as present in one reading only, never as an error in the other'},
            'internal_near_duplicates': 'CANDIDATES, reported and never removed: two entries of one reading sharing their first three normalised tokens at a ratio at or above the match threshold. A doubled band in a transcription shows up here, and the two copies of it need not agree. Two different firms of one name show up here too — Johnson, J. & A. the grocers and Johnson, J. & Co. the barbers are in both readings and are not a duplicate of anything.',
            'preference': 'NONE. Where the two differ, both stand. This file is the record of the disagreement; it corrects nothing and deletes nothing.',
        },
        'counts': {
            'archive_entries': n_a,
            'genealogytrails_entries': n_b,
            'matched': matched,
            'identical': len(c['identical']),
            'agrees': len(c['agree']),
            'differs': len(c['differ']),
            'only_in_archive': len(c['only_a']),
            'only_in_genealogytrails': len(c['only_b']),
            'match_rate_of_archive_entries': round(matched / n_a, 4),
            'match_rate_of_genealogytrails_entries': round(matched / n_b, 4),
            'identical_rate_of_matched': round(len(c['identical']) / matched, 4) if matched else 0,
            'archive_sections': {'directory': sum(1 for a in c['a_items'] if a['section'] == 'directory'),
                                 'addenda': sum(1 for a in c['a_items'] if a['section'] == 'addenda')},
            'genealogytrails_sections': c['gt_sections'],
            'matched_across_sections': len(c['section_moved']),
            'near_duplicate_pairs_within_archive': len(c['dupes_a']),
            'near_duplicate_pairs_within_genealogytrails': len(c['dupes_b']),
        },
        'identical': c['identical'],
        'agrees': c['agree'],
        'differs': c['differ'],
        'only_in_archive': c['only_a'],
        'only_in_genealogytrails': c['only_b'],
        'near_duplicates_within_archive': c['dupes_a'],
        'near_duplicates_within_genealogytrails': c['dupes_b'],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', action='store_true')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--report', action='store_true')
    args = ap.parse_args()
    c = compare()
    doc = build(c)
    if args.report:
        k = doc['counts']
        for key in ('archive_entries', 'genealogytrails_entries', 'matched', 'identical',
                    'agrees', 'differs', 'only_in_archive', 'only_in_genealogytrails',
                    'match_rate_of_archive_entries', 'match_rate_of_genealogytrails_entries',
                    'matched_across_sections', 'near_duplicate_pairs_within_archive',
                    'near_duplicate_pairs_within_genealogytrails'):
            print(f'{key:42} {k[key]}')
        return 0
    text = json.dumps(doc, indent=1, ensure_ascii=False) + '\n'
    if args.build:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text, encoding='utf-8')
        print(f'wrote {OUT.relative_to(ROOT)} — {doc["counts"]["matched"]} of {doc["counts"]["archive_entries"]} matched')
        return 0
    if args.check:
        if not OUT.exists():
            print(f'MISSING {OUT}', file=sys.stderr)
            return 1
        if OUT.read_text(encoding='utf-8') != text:
            print(f'STALE {OUT.relative_to(ROOT)} — rebuild with --build', file=sys.stderr)
            return 1
        print(f'{OUT.relative_to(ROOT)} matches its inputs')
        return 0
    ap.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
