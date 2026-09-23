import json, os, re, collections
cohort = json.load(open('data/research/residents/pass_15_76_cohort.json'))
people = cohort['people']
names = {p['person_id']: p['name'] for p in people}
pids = set(names)

FILES = []
for base in ['data/research']:
    for dp, dns, fns in os.walk(base):
        if dp.startswith('data/research/residents'): continue
        for fn in fns:
            if fn.endswith('.json') and ('crosswalk' in fn or 'spend' in fn or fn in ('claims.json',)):
                FILES.append(os.path.join(dp, fn))
print(len(FILES), 'crosswalk files')

hits = collections.defaultdict(list)
def walk(node, path, f):
    if isinstance(node, dict):
        blob = json.dumps(node, ensure_ascii=False)
        # only leaf-ish records
        if len(blob) < 4000:
            for pid, nm in names.items():
                if f'"{pid}"' in blob or f'"{nm}"' in blob or f': "{nm}"' in blob:
                    hits[pid].append((f, node))
                    return
        for k, v in node.items(): walk(v, path + '/' + str(k), f)
    elif isinstance(node, list):
        for i, v in enumerate(node): walk(v, path, f)

for f in FILES:
    try: doc = json.load(open(f))
    except Exception: continue
    walk(doc, '', f)

json.dump({k: [(f, v) for f, v in vs] for k, vs in hits.items()}, open('/tmp/xw.json','w'), indent=1, default=str)
for pid in names:
    vs = hits.get(pid, [])
    doms = collections.Counter(f.split('/')[2] for f, _ in vs)
    print(f"{pid:24s} {len(vs):3d}  " + ','.join(f'{k}:{v}' for k,v in doms.most_common()))
