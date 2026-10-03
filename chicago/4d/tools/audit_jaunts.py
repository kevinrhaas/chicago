#!/usr/bin/env python3
"""The jaunt library's shape, gated (T-2039, the first piece of T-1271).

compile_jaunts.py proves each jaunt on its own: schema, sources, locators, dates, 25-60
words a stop, a finite reachable graph. This proves the LIBRARY the owner asked for:

  * the 25 premises named in docs/JAUNTS-INITIAL-LIBRARY.md are exactly the 1835 jaunts,
    each `available` in the compiled catalog, with no title or premise twice;
  * the six priority jaunts of docs/ARRIVAL-JAUNTS-EXECUTION.md § 5H are all featured;
  * every jaunt has 4-8 stops, and the reducer walk (tools/play_jaunt.mjs --all) reaches
    every declared ending with no failure and awards the keepsake on some path;
  * at least five quiet outings declare no resource at all;
  * every daybook family holds at least three keepsakes, and every rank is reachable by
    distinct completions — the top one in 15 or fewer — since an award is idempotent per
    jaunt and a replay can never count;
  * every subject on the owner's list is the menu category of at least one jaunt.

    python3 tools/audit_jaunts.py              # the tables and the verdict
    python3 tools/audit_jaunts.py --self-test  # each assertion must fire when broken
"""
import copy
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENE = '1835'
STOPS = (4, 8)
QUIET_MIN = 5
FAMILY_MIN = 3
TOP_RANK_MAX_COMPLETIONS = 15
# The owner's list (T-1271 Do 4), each read against the category the menu filters by.
SUBJECTS = {
    'commerce': r'commerce|shopping', 'travel': r'routes|orientation', 'taverns': r'tavern',
    'lodging': r'lodging', 'employment': r'employment', 'land': r'\bland\b', 'newspapers': r'news',
    'mail': r'\bmail\b', 'river transportation': r'\briver\b', 'Fort Dearborn': r'fort dearborn',
    'household provisioning': r'household', 'trades': r'trades', 'repairs': r'repairs',
    'migration': r'migration', 'social life': r'social life|leisure',
}


def load():
    walk = subprocess.run(['node', 'tools/play_jaunt.mjs', '--all', '--json', '--scene', SCENE],
                          cwd=ROOT, capture_output=True, text=True)
    if walk.returncode:
        sys.exit(f'JAUNT AUDIT FAIL — the library walk did not run: {walk.stderr.strip()[-400:]}')
    rows = json.loads(walk.stdout)['jaunts']
    catalog = json.loads((ROOT / f'data/sidecars/{SCENE}/jaunts/catalog.json').read_text())['jaunts']
    book = json.loads((ROOT / 'data/jaunts/daybook.json').read_text())
    library = (ROOT / 'docs/JAUNTS-INITIAL-LIBRARY.md').read_text()
    roster = re.findall(r'^\*\*ID:\*\* `([a-z0-9-]+)`', library, re.M)
    plan = (ROOT / 'docs/ARRIVAL-JAUNTS-EXECUTION.md').read_text()
    section = plan.split('## 5H.', 1)[1].split('\n## ', 1)[0]
    priority = [re.sub(r'\s*\(.*\)$', '', m).strip()
                for m in re.findall(r'^\| \[T-\d+\]\([^)]*\) \| ([^|]+?) \|', section, re.M)]
    return {'rows': rows, 'catalog': catalog, 'book': book, 'roster': roster, 'priority': priority}


def completions_for(threshold, rows, families):
    """Fewest distinct completions found that bring every family to `threshold` (greedy)."""
    counts, chosen = {f: 0 for f in families}, []
    pool = [r for r in rows if r['keepsake']['awarded']]
    while any(n < threshold for n in counts.values()):
        def gain(r):
            fams = {r['keepsake']['family'], r['keepsake']['secondary_family']} - {None}
            return sum(1 for f in fams if f in counts and counts[f] < threshold)
        best = max((r for r in pool if r not in chosen), key=gain, default=None)
        if best is None or gain(best) == 0:
            return None
        chosen.append(best)
        for f in {best['keepsake']['family'], best['keepsake']['secondary_family']} - {None}:
            if f in counts:
                counts[f] += 1
    return len(chosen)


def audit(lib):
    rows, findings = lib['rows'], []
    by_id = {r['id']: r for r in rows}
    shown = {c['id']: c for c in lib['catalog']}
    if len(lib['roster']) != 25 or set(lib['roster']) != set(by_id):
        findings.append(f'roster: the brief names {len(lib["roster"])} jaunts and the scene has {len(by_id)}; '
                        f'missing {sorted(set(lib["roster"]) - set(by_id))}, unnamed {sorted(set(by_id) - set(lib["roster"]))}')
    for jid in sorted(by_id):
        if shown.get(jid, {}).get('availability') != 'available':
            findings.append(f'{jid}: not available in the compiled catalog ({shown.get(jid, {}).get("reason") or "absent"})')
    for key in ('title', 'premise'):
        seen = {}
        for c in lib['catalog']:
            seen.setdefault(c[key].strip().lower(), []).append(c['id'])
        findings += [f'duplicate {key}: {", ".join(ids)}' for ids in seen.values() if len(ids) > 1]
    titles = {r['title']: r for r in rows}
    if len(lib['priority']) != 6:
        findings.append(f'priority: § 5H names {len(lib["priority"])} jaunts, not six')
    for title in lib['priority']:
        if title not in titles:
            findings.append(f'priority: "{title}" is not a jaunt in the scene')
        elif not titles[title]['featured']:
            findings.append(f'priority: {titles[title]["id"]} is a § 5H priority jaunt and is not featured')
    for r in rows:
        if not STOPS[0] <= r['stops'] <= STOPS[1]:
            findings.append(f'{r["id"]}: {r["stops"]} stops, outside {STOPS[0]}-{STOPS[1]}')
        if r['failures']:
            findings.append(f'{r["id"]}: walk failed — {r["failures"][0]}')
        if set(r['endings_reached']) != set(r['endings_declared']):
            findings.append(f'{r["id"]}: endings never reached {sorted(set(r["endings_declared"]) - set(r["endings_reached"]))}')
        if not r['keepsake']['awarded']:
            findings.append(f'{r["id"]}: no path awards its keepsake')
    quiet = [r['id'] for r in rows if r['quiet'] and not r['resources']['hidden']]
    if len(quiet) < QUIET_MIN:
        findings.append(f'quiet: {len(quiet)} outing(s) declare no resource, fewer than {QUIET_MIN}')
    families = [f['name'] for f in lib['book']['families']]
    held = {f: [r['id'] for r in rows if r['keepsake']['awarded']
                and f in (r['keepsake']['family'], r['keepsake']['secondary_family'])] for f in families}
    findings += [f'family {f}: {len(ids)} keepsake(s), fewer than {FAMILY_MIN}' for f, ids in held.items() if len(ids) < FAMILY_MIN]
    ranks = [(rank['title'], completions_for(rank['threshold'], rows, families)) for rank in lib['book']['ranks']]
    for title, n in ranks:
        if n is None:
            findings.append(f'rank {title}: not reachable by distinct completions')
    if ranks and (ranks[-1][1] or 0) > TOP_RANK_MAX_COMPLETIONS:
        findings.append(f'rank {ranks[-1][0]}: needs {ranks[-1][1]} completions, more than {TOP_RANK_MAX_COMPLETIONS}')
    subjects = {s: [r['id'] for r in rows if re.search(p, r['category'], re.I)] for s, p in SUBJECTS.items()}
    findings += [f'subject {s}: no jaunt carries it' for s, ids in subjects.items() if not ids]
    return findings, {'quiet': quiet, 'held': held, 'ranks': ranks, 'subjects': subjects}


def report(lib, findings, facts):
    rows = lib['rows']
    print(f'JAUNT LIBRARY {SCENE} — {len(rows)} jaunts; {sum(r["paths"] for r in rows)} paths walked; '
          f'{sum(r["featured"] for r in rows)} featured')
    print(f'  quiet, no resource declared ({len(facts["quiet"])}): {", ".join(facts["quiet"])}')
    print(f'  no resource shown ({sum(r["quiet"] for r in rows)}), hidden preferences allowed')
    for f, ids in facts['held'].items():
        print(f'  {f:<17} {len(ids)}  {", ".join(ids)}')
    print('  ranks by distinct completions: ' + ', '.join(f'{t} {n}' for t, n in facts['ranks']))
    for s, ids in facts['subjects'].items():
        print(f'  {s:<23} {", ".join(ids) or "—"}')
    for f in findings:
        print(f'JAUNT AUDIT FAIL — {f}')
    if not findings:
        print('JAUNT AUDIT PASS — the 25 named premises, six featured, every shape bound met')


def self_test(lib):
    """Break the library one way at a time; each must produce exactly the finding it guards."""
    def broken(change, expect):
        bad = copy.deepcopy(lib)
        change(bad)
        found, _ = audit(bad)
        ok = any(expect in f for f in found)
        print(f'self-test | {"fires" if ok else "SILENT"}: {expect}')
        return ok

    def first(bad):
        return bad['rows'][0]
    first_quiet = next(r['id'] for r in lib['rows'] if r['quiet'] and not r['resources']['hidden'])
    cases = [
        (lambda b: b['roster'].pop(), 'roster:'),
        (lambda b: b['catalog'][0].update(availability='unavailable'), 'not available'),
        (lambda b: b['catalog'][1].update(title=b['catalog'][0]['title']), 'duplicate title'),
        (lambda b: next(r for r in b['rows'] if r['title'] == b['priority'][0]).update(featured=False), 'is not featured'),
        (lambda b: first(b).update(stops=9), 'outside 4-8'),
        (lambda b: first(b).update(failures=['x: state limit']), 'walk failed'),
        (lambda b: first(b)['endings_declared'].append('never'), 'endings never reached'),
        (lambda b: first(b)['keepsake'].update(awarded=False), 'no path awards'),
        (lambda b: [r['resources']['hidden'].append('x') for r in b['rows'] if r['id'] == first_quiet], 'quiet:'),
        (lambda b: [r['keepsake'].update(family='Provisions') for r in b['rows'] if r['keepsake']['family'] == 'Neighbors'], 'family Neighbors'),
        (lambda b: [r.update(category='Commerce') for r in b['rows'] if 'mail' in r['category'].lower()], 'subject mail'),
    ]
    clean, _ = audit(lib)
    ok = all([broken(change, expect) for change, expect in cases])
    if clean:
        print(f'self-test | the committed library itself has {len(clean)} finding(s); fix those first')
    print('JAUNT AUDIT SELF-TEST ' + ('PASS' if ok else 'FAIL'))
    return ok


def main():
    lib = load()
    if '--self-test' in sys.argv:
        sys.exit(0 if self_test(lib) else 1)
    findings, facts = audit(lib)
    report(lib, findings, facts)
    sys.exit(1 if findings else 0)


if __name__ == '__main__':
    main()
