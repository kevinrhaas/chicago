import json, os, re, collections

cohort = json.load(open('data/research/residents/pass_15_76_cohort.json'))
people = cohort['people']

corpus = []
for base in ['data/research', 'data/sources']:
    for dp, dns, fns in os.walk(base):
        if dp.startswith('data/research/residents'): continue
        for fn in fns:
            if fn.endswith(('.json', '.txt', '.md', '.csv')):
                p = os.path.join(dp, fn)
                if os.path.getsize(p) > 40_000_000: continue
                corpus.append(p)

blobs = []
for p in corpus:
    try:
        t = open(p, encoding='utf-8', errors='replace').read()
        blobs.append((p, t, t.lower()))
    except Exception: pass

STOP = {'mrs','mr','miss','dr','rev','the','four','children','jr','sr','ii','capt','col','maj'}
def parse(name, pid):
    toks = [t.strip('.,!') for t in name.replace('(',' ').replace(')',' ').split()]
    toks = [t for t in toks if t and t.lower().strip('.') not in STOP and len(t) > 1]
    seg = pid.split('_')[0]
    sur = None
    for t in toks:
        if t.lower()[:4] == seg[:4]: sur = t
    if sur is None: sur = toks[-1] if toks else name
    firsts = [t for t in toks if t != sur]
    return sur, firsts

MID = r'(?:\s+[A-Za-z]{1,12}\.?){0,2}'
out = {}
for p in people:
    pid, name = p['person_id'], p['name']
    sur, firsts = parse(name, pid)
    surl = sur.lower()
    pats = []
    if firsts:
        f0 = firsts[0]
        pats.append(re.compile(r'(?i)\b' + re.escape(f0) + r'\.?' + MID + r'\s+' + re.escape(sur) + r'\b'))
        pats.append(re.compile(r'(?i)\b' + re.escape(f0[0]) + r'\.\s?(?:[A-Za-z]\.\s?){0,2}' + re.escape(sur) + r'\b'))
        pats.append(re.compile(r'(?i)\b' + re.escape(sur) + r',\s*' + re.escape(f0)))
    else:
        pats.append(re.compile(r'(?i)\b' + re.escape(sur) + r'\b'))
    hits = {}
    for path, txt, low in blobs:
        if surl not in low: continue
        snips = []
        for pat in pats:
            for m in pat.finditer(txt):
                s = max(0, m.start()-100); e = min(len(txt), m.end()+100)
                snips.append(re.sub(r'\s+', ' ', txt[s:e]))
                if len(snips) >= 3: break
            if len(snips) >= 3: break
        if snips: hits[path] = snips
    out[pid] = {'name': name, 'surname': sur, 'firsts': firsts, 'hits': hits}

json.dump(out, open('/tmp/strict.json','w'), indent=1)
for pid, d in out.items():
    doms = collections.Counter()
    for f in d['hits']:
        parts = f.split('/')
        doms[parts[2] if parts[1]=='research' else 'sources'] += 1
    print(f"{pid:24s} {d['surname']:16s} f={len(d['hits']):4d}  " + ','.join(f'{k}:{v}' for k,v in doms.most_common(8)))
