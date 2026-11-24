#!/usr/bin/env python3
"""run_plan.py PLAN.json CTL — feed a site_films.mjs server one job after another (T-3744).

A plan is a list of jobs as site_films.mjs takes them. A job may name its page code in a file
beside the plan ("js_file" for eval, "track_file" for track.js, "each_file" for each) so the
code stays readable. Each answer is printed; the plan stops on the first error.
"""
import json, os, sys, time
plan_path, ctl = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(plan_path))
read = lambda f: open(os.path.join(here, f)).read()
for i, job in enumerate(json.load(open(plan_path))):
    if 'js_file' in job: job['js'] = read(job.pop('js_file'))
    if 'each_file' in job: job['each'] = read(job.pop('each_file'))
    if 'track_file' in job: job.setdefault('track', {})['js'] = read(job.pop('track_file'))
    for k, v in job.pop('replace', {}).items():
        for key in ('js', 'each'):
            if key in job: job[key] = job[key].replace(k, v)
    name = f"t3744-{i:02d}-{job.get('id', job['type'])}"
    tmp = os.path.join(ctl, 'queue', name + '.json.tmp')
    json.dump(job, open(tmp, 'w')); os.rename(tmp, tmp[:-4])
    done = os.path.join(ctl, 'done', name + '.json')
    while not os.path.exists(done): time.sleep(0.5)
    ans = json.load(open(done)); os.remove(done)
    print(name, json.dumps(ans)[:600], flush=True)
    if ans.get('error'): sys.exit(1)
