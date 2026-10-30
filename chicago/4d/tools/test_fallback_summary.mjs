#!/usr/bin/env node
/**
 * test_fallback_summary.mjs — the card's opening, over every structure in every scene (T-2636).
 *
 *   node tools/test_fallback_summary.mjs
 *
 * A building with no written summary opens on what renderers/web/js/fallback-summary.js
 * templates from its sidecar. This runs the card's own composition (popup.js
 * `cardOpening`, the strings its head and lead print) over every structure record in
 * data/sidecars/<scene>/ and refuses:
 *
 *   - an id, snake_case word, file path, link or ticket number in the title, the address
 *     line, the other names, the kind line or the lead;
 *   - the address given more than once: an other name that restates it, or a composed
 *     lead that repeats it;
 *   - a composed lead over three sentences or sixty words (the summary record's limits);
 *   - the Glessner card of the owner's screenshot (IMG_6942) opening any other way than
 *     its street address once and a templated lead;
 *   - a year in a composed lead that the record does not date (T-3037): every year the
 *     lead prints is its `built` value's or a range end the record marks (`from_is`,
 *     `to_is`), never a bound — the owner found 1736 Prairie's "It had stood like this
 *     since 1904" under the 1893 drawing of the house; and that card must say what its
 *     sources say, "1864 or 1875".
 *
 * And it holds the JavaScript lint to the Python one in tools/compile_summaries.py on
 * the same strings, so the card and the summary gate cannot disagree about what a
 * visitor may read.
 */
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import path from 'node:path';

const APP = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const JS = path.join(APP, 'renderers/web/js');
const { cardOpening } = await import(path.join(JS, 'popup.js'));
const { displayName } = await import(path.join(JS, 'display-name.js'));
const { visitorTextProblems, fallbackSummary, fallbackAddress, cardTitle } = await import(path.join(JS, 'fallback-summary.js'));

const fails = [];
const fail = (m) => fails.push(m);
const words = (t) => String(t).split(/\s+/).filter((w) => /[A-Za-z0-9]/.test(w)).length;
const leads = [];

const counts = {};
for (const scene of readdirSync(path.join(APP, 'data/scenes')).filter((f) => f.endsWith('.json')).map((f) => f.slice(0, -5))) {
  const dir = path.join(APP, 'data/sidecars', scene);
  if (!existsSync(dir)) continue;
  let n = 0; let composed = 0; let addressed = 0;
  for (const f of readdirSync(dir).sort()) {
    if (!f.endsWith('.json')) continue;
    const s = JSON.parse(readFileSync(path.join(dir, f), 'utf8'));
    if (!s || typeof s !== 'object' || !s.placement || !s.id) continue; // directories, indexes
    n += 1;
    const called = displayName(s, s.id);
    const o = cardOpening(s, called);
    if (o.composed) composed += 1;
    if (o.address) addressed += 1;
    const shown = [['title', o.title], ['address', o.address], ...o.aka.map((a) => ['other name', a]),
      ...o.kind.map((k) => ['kind', k]), ['lead', o.lead]];
    for (const [where, text] of shown) {
      for (const p of visitorTextProblems(text)) fail(`${scene}/${s.id}: ${where} carries ${p}`);
    }
    if (o.address) {
      const key = o.address.toLowerCase();
      if (o.aka.some((a) => a.toLowerCase() === key)) fail(`${scene}/${s.id}: an other name restates the address`);
      if (o.composed && o.lead.toLowerCase().includes(key)) fail(`${scene}/${s.id}: the composed lead repeats the address`);
      if (o.title.toLowerCase().includes(key)) fail(`${scene}/${s.id}: the title repeats the address line`);
    }
    if (o.composed) {
      if (!o.lead) fail(`${scene}/${s.id}: no lead at all`);
      leads.push([`${scene}/${s.id}`, o.lead]);
      if (words(o.lead) > 60) fail(`${scene}/${s.id}: composed lead runs to ${words(o.lead)} words`);
      if (/undefined|null|\[object/.test(o.lead)) fail(`${scene}/${s.id}: composed lead prints a missing value: "${o.lead}"`);
    }
    if (o.composed) {
      // T-3037: a year the lead prints is one the record dates, never a bound.
      const dated = new Set([...String(s.attributes?.built?.value ?? '').matchAll(/\d{4}/g)].map((m) => m[0]));
      const r = s.documented_range ?? {};
      if (r.from_is) dated.add(String(r.from).slice(0, 4));
      if (r.to_is) dated.add(String(r.to).slice(0, 4));
      const datedSentence = fallbackSummary(s, { kind: o.kind[0] ?? '' }).sentences.find((x) => /^(Built|It had stood|Recorded here)/.test(x)) ?? '';
      for (const m of datedSentence.matchAll(/\b1\d{3}\b/g)) {
        if (!dated.has(m[0])) fail(`${scene}/${s.id}: the lead dates it ${m[0]}, which the record does not date: "${datedSentence}"`);
      }
    }
    if (scene === '1904' && s.id === 'house_1736_prairie') {
      if (/1904/.test(o.lead) || !/1864 or 1875/.test(o.lead)) fail(`1904/house_1736_prairie: lead is "${o.lead}"`);
      console.log(`  house_1736_prairie: "${o.lead}"`);
    }
    if (scene === '1904' && s.id === 'glessner_house') {
      if (o.address !== '1800 S. Prairie Avenue') fail(`1904/glessner_house: address line is "${o.address}"`);
      if (o.aka.length) fail(`1904/glessner_house: other names restate the address: ${o.aka.join(' · ')}`);
      if (!o.composed || /parcel|street_grid|1800 S/.test(o.lead)) fail(`1904/glessner_house: lead is "${o.lead}"`);
      console.log(`  glessner_house: "${o.title}" · "${o.address}" · "${o.lead}"`);
    }
  }
  counts[scene] = { structures: n, composed, addressed };
}
for (const [scene, c] of Object.entries(counts)) {
  console.log(`  ${scene}: ${c.structures} structures, ${c.addressed} with an address line, ${c.composed} with a templated lead`);
}
for (const scene of ['1835', '1904']) {
  if (!counts[scene]?.structures) fail(`no structures read for ${scene}`);
}

// The template refuses what it is handed rather than printing it.
const planted = fallbackSummary({ attributes: { construction: { value: 'log' } }, documented_range: { from: '1830-01-01', from_is: 'began' }, target_date: '1835-07-01' },
  { kind: 'see data/x.json', today: 'parcel_7' });
if (planted.text !== 'It was a log building. It had stood like this since 1830.') {
  fail(`a dirty kind and status are dropped, not printed: "${planted.text}"`);
}
// T-3037: a range end is printed only as what the record says it is.
const when = (range, built) => fallbackSummary({ attributes: { construction: { value: 'brick' }, ...(built === undefined ? {} : { built: { value: built } }) },
  documented_range: range, target_date: '1904-07-01' }).text;
for (const [range, built, want] of [
  [{ from: '1904-07-01', to: '1911-12-31' }, undefined, 'It was a brick building.'],
  [{ from: '1890-01-01', to: '1911-12-31' }, undefined, 'It was a brick building.'],
  [{ from: '1890-01-01', to: '1911-12-31', from_is: 'seen' }, undefined, 'It was a brick building. Recorded here by 1890.'],
  [{ from: '1904-07-01', to: '1911-12-31' }, '1864 or 1875', 'It was a brick building. Built in 1864 or 1875.'],
  [{ from: '1904-07-01', to: '1911-12-31' }, 'about 1834', 'It was a brick building. Built about 1834.'],
  [{ from: '1904-07-01', to: '1911-12-31' }, 'between 1870 and 1876', 'It was a brick building. Built between 1870 and 1876.'],
  [{ from: '1833-01-01', to: '1850-12-31', from_is: 'began' }, 1831, 'It was a brick building. Built in 1831, and like this since 1833.'],
  [{ from: '1904-07-01', to: '1911-12-31' }, 'sometime in the 1860s', 'It was a brick building.'],
  [{ from: '1904-07-01', to: '1911-12-31' }, 1905, 'It was a brick building.'],
]) {
  const got = when(range, built);
  if (got !== want) fail(`range ${JSON.stringify(range)} built ${JSON.stringify(built)}: "${got}", want "${want}"`);
}
const { rangeWords } = await import(path.join(JS, 'range-words.js'));
for (const [range, want] of [
  [{ from: '1887-12-01', to: '1946-08-31', from_is: 'began', to_is: 'ended' }, '1887 – 1946'],
  [{ from: '1904-07-01', to: '1911-12-31', to_is: 'seen' }, 'still in 1911'],
  [{ from: '1890-01-01', to: '1911-12-31', from_is: 'seen', to_is: 'seen' }, 'by 1890, still in 1911'],
  [{ from: '1816-07-01', to: '1856-08-31', to_is: 'ended' }, 'until 1856'],
  [{ from: '1835-01-01', to: '1835-12-31' }, ''],
]) {
  if (rangeWords(range) !== want) fail(`rangeWords(${JSON.stringify(range)}) is "${rangeWords(range)}", want "${want}"`);
}
const t1 = cardTitle('1823 Prairie Avenue — Dent masonry mansion (district draft; refined by T-1894)', '1823 S. Prairie Avenue');
if (t1.title !== 'Dent masonry mansion' || t1.addressInTitle) fail(`a title loses its ticket aside and its address prefix (got "${t1.title}")`);
if (!cardTitle('1823 S. Prairie Avenue', '1823 Prairie Avenue').addressInTitle) fail('a title that is the address takes the address line\'s place');
if (fallbackAddress({ placement: { symbolic_location: 'Anonymous reconstructed roof in cluster a_b; between the north bank and Michigan Street' } })
  !== 'Between the north bank and Michigan Street') fail('the address skips a dirty clause and takes the next clean one');
if (fallbackAddress({ placement: { symbolic_location: 'parcel prairie_1800 (data/street_grid/1904.json)' } }) !== '') {
  fail('a location with no clean phrase gives no address line');
}

// Sentences are counted by the summary gate's own counter, which knows "H. H." and "Ave.".
const sc = spawnSync('python3', ['-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(path.join(APP, 'tools'))})
from compile_summaries import sentences
print(json.dumps([sentences(t) for t in json.loads(sys.stdin.read())]))`], { input: JSON.stringify(leads.map((l) => l[1])), encoding: 'utf8' });
if (sc.status !== 0) fail(`python sentence count did not run: ${sc.stderr}`);
else JSON.parse(sc.stdout).forEach((n, i) => {
  if (n > 3) fail(`${leads[i][0]}: composed lead runs to ${n} sentences: "${leads[i][1]}"`);
});

// The JavaScript lint and the Python gate agree, string for string.
const cases = ['A granite fortress on the street.', 'on parcel prairie_1800', 'see data/street_grid/1904.json',
  'Fixed under T-2635.', 'https://example.test/x', 'H. H. Richardson, 1800 S. Prairie Ave.', 'the 1880s', 'map.png',
  'NAV-501 layout', 'Still standing — Glessner House museum', 'and/or 1/4 mile'];
const py = spawnSync('python3', ['-c', `
import json, sys
sys.path.insert(0, ${JSON.stringify(path.join(APP, 'tools'))})
from compile_summaries import lint_string
print(json.dumps([bool(lint_string(s)) for s in json.loads(sys.stdin.read())]))`], { input: JSON.stringify(cases), encoding: 'utf8' });
if (py.status !== 0) fail(`python lint did not run: ${py.stderr}`);
else {
  const pyv = JSON.parse(py.stdout);
  cases.forEach((c, i) => {
    const js = visitorTextProblems(c).length > 0;
    if (js !== pyv[i]) fail(`lint disagreement on "${c}": js ${js}, python ${pyv[i]}`);
  });
}

for (const f of fails.slice(0, 60)) console.log(`FAIL: ${f}`);
if (fails.length > 60) console.log(`FAIL: … and ${fails.length - 60} more`);
if (fails.length) {
  console.log(`FAIL: ${fails.length} problem(s) in the card's opening`);
  process.exit(1);
}
console.log('OK: every structure opens with its address once and no id, path or snake_case');
