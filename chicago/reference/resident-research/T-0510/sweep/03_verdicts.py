import json, os, re, collections
xw = json.load(open('/tmp/xw.json'))
cohort = json.load(open('data/research/residents/pass_15_76_cohort.json'))
people = cohort['people']

def dom(f): 
    parts = f.split('/'); return parts[2] if parts[1]=='research' else 'sources'

REFUSAL_TEXT = re.compile(r'is a refusal|is refused|\bis NOT\b|Refused\b', re.I)
AGREE_TEXT = re.compile(r'folds to the same string|initial for initial|both agree|forename[s]? agree', re.I)

def kind(rec):
    o = (rec.get('outcome') or '').lower()
    if o in ('refused',): return 'neg'
    if o in ('matched', 'merged'): return 'pos'
    if o in ('earlier_evidence',): return 'pos'
    if o in ('candidate',): return 'cand'
    if (rec.get('match') or '').lower() in ('forename_agrees','exact'): return 'pos'
    if 'into' in rec and 'from' in rec: return 'pos'
    b = json.dumps(rec, ensure_ascii=False)
    if 'CONTESTED' in b: return 'cand'
    if REFUSAL_TEXT.search(b): return 'neg'
    if AGREE_TEXT.search(b): return 'pos'
    return 'other'

def srcs_of(rec):
    s = set()
    if rec.get('source_id'): s.add(rec['source_id'])
    for x in rec.get('source_ids') or []: s.add(x)
    for e in rec.get('entries') or []:
        if isinstance(e, dict) and e.get('source_id'): s.add(e['source_id'])
    for e in rec.get('evidence') or []:
        if isinstance(e, dict) and e.get('source_id'): s.add(e['source_id'])
    return s

CONTEMP = {'civic', 'land_sales', 'census_1830', 'church', 'books'}
out = {}
for p in people:
    pid = p['person_id']
    recs = xw.get(pid, [])
    b = collections.defaultdict(list); srcs = set(); pdoms = set(); cdoms = set(); ndoms = set()
    for f, rec in recs:
        k = kind(rec); d = dom(f)
        b[k].append((d, rec))
        if k == 'pos': srcs |= srcs_of(rec); pdoms.add(d)
        if k == 'cand': cdoms.add(d)
        if k == 'neg': ndoms.add(d)
    out[pid] = {'name': p['name'], 'stratum': p['stratum'],
                'pos': len(b['pos']), 'cand': len(b['cand']), 'neg': len(b['neg']), 'other': len(b['other']),
                'pos_domains': sorted(pdoms), 'cand_domains': sorted(cdoms), 'neg_domains': sorted(ndoms),
                'sources': sorted(srcs)}
json.dump(out, open('/tmp/verdict2.json','w'), indent=1)
c = collections.Counter()
for pid, d in out.items():
    if d['pos'] and (set(d['pos_domains']) & CONTEMP): o = 'corroborated'
    elif d['pos']: o = 'corroborated_enrichment'
    elif d['cand']: o = 'candidate_identity'
    else: o = 'no_corroboration'
    d['outcome'] = o; c[o] += 1
    print(f"{pid:24s} {o:24s} pos={d['pos']:2d}/{','.join(d['pos_domains'])[:34]:34s} cand={d['cand']:2d} neg={d['neg']:2d}")
print(c)
json.dump(out, open('/tmp/verdict2.json','w'), indent=1)
