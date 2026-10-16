#!/usr/bin/env node
// T-2609: the building card's two review bugs, held in the gate.
//
//   1. An object-valued attribute printed "[object Object]" — the 1904 Glessner card's
//      `bay_dining`. claim-value.js gives a structured value no text (the claim row then
//      draws no value cell and keeps its chip, sources and why); every attribute in
//      data/structures/ is run through it.
//   2. The 1835 hay-stacking limit rode every scene's cards, so a 1904 house quoted an
//      1835 by-law. ordinances.js now serves a law only to its own scene's year, and
//      another year does not fetch it at all.
//
// The self-test lines run the first assertion against the formatter the card had before
// (`String(v)`), and it is MEANT to fire: that is the proof the assertion can catch the bug.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const load = (rel) => import(pathToFileURL(path.join(ROOT, rel)).href);
const { claimValueText } = await load('renderers/web/js/claim-value.js');
const { lawServesScene, loadOrdinanceLimits, HAY_LIMITS } = await load('renderers/web/js/ordinances.js');
const readJson = (rel) => JSON.parse(fs.readFileSync(path.join(ROOT, rel), 'utf8'));

let failures = 0;
function check(label, ok, detail) {
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${label}${ok || detail === undefined ? '' : ` — ${detail}`}`);
  if (!ok) failures++;
}

// --- 1. values -------------------------------------------------------------------
const glessner = readJson('data/structures/glessner_house.json');
const bay = glessner.phases.map((p) => p.form?.bay_dining).find(Boolean);
check('glessner_house still carries an object-valued bay_dining to test against',
  bay && typeof bay.value === 'object' && !Array.isArray(bay.value));

/** The visible text the card's row would print for a value, through `format`. */
const printed = (format, v) => {
  const t = format(v);
  return t === null ? '' : String(t);
};
const leaks = (format, values) => values.filter((v) => /\[object Object\]/.test(printed(format, v)));

let selfFailures = 0;
const oldFormat = (v) => String(v);
const firedOnOld = leaks(oldFormat, [bay.value]).length > 0;
console.log(`   self-test | ${firedOnOld ? 'ok  ' : 'FAIL'} the old String() formatter prints '[object Object]' for bay_dining`);
if (!firedOnOld) selfFailures++;
console.log(`   self-test | ${selfFailures} failure(s)`);
if (selfFailures) failures++;

check("bay_dining prints no '[object Object]'", leaks(claimValueText, [bay.value]).length === 0,
  printed(claimValueText, bay.value));
check('a structured value prints no value at all (null: the row keeps its chip, sources and why)',
  claimValueText(bay.value) === null);

const values = [];
for (const file of fs.readdirSync(path.join(ROOT, 'data/structures'))) {
  if (!file.endsWith('.json')) continue;
  const rec = readJson(`data/structures/${file}`);
  for (const phase of rec.phases ?? []) {
    for (const attr of Object.values(phase.form ?? {})) {
      if (attr && typeof attr === 'object' && 'value' in attr) values.push(attr.value);
    }
  }
}
const bad = leaks(claimValueText, values);
check(`no attribute of ${values.length} across data/structures/ prints '[object Object]'`,
  bad.length === 0, `${bad.length}, e.g. ${JSON.stringify(bad[0])?.slice(0, 80)}`);
check('a list of objects prints no value', claimValueText([{ id: 'r1' }, { id: 'r2' }]) === null);

for (const [v, want] of [[true, 'yes'], [false, 'no'], [null, '—'], [3, '3'], ['gable_roof', 'gable roof'],
  [[3.9, 3.6, 3.4], '3.9, 3.6, 3.4'], [['s'], 's'], [[], 'none']]) {
  check(`${JSON.stringify(v)} prints ${JSON.stringify(want)}`, claimValueText(v) === want,
    JSON.stringify(claimValueText(v)));
}

// --- 2. the era -------------------------------------------------------------------
const hay = readJson(`data/${HAY_LIMITS.path}`);
const scene = (id) => readJson(`data/scenes/${id}.json`).target_date;
check(`HAY_LIMITS.year (${HAY_LIMITS.year}) is the year the file was derived for`,
  lawServesScene(hay.target_date, HAY_LIMITS.year), hay.target_date);
check('the 1835 limit serves the 1835 scene', lawServesScene(hay.target_date, scene('1835')));
check('…and not the 1904 scene', !lawServesScene(hay.target_date, scene('1904')));
check('…nor the 1812 scene', !lawServesScene(hay.target_date, scene('1812')));
check('…nor an undated one', !lawServesScene(hay.target_date, undefined));

const realFetch = globalThis.fetch;
let fetches = 0;
const stub = (doc) => {
  globalThis.fetch = async () => {
    fetches++;
    return { ok: true, json: async () => doc };
  };
};
const dataBase = new URL('https://example.invalid/data/');
try {
  stub(hay);
  let problems = [];
  const on1904 = await loadOrdinanceLimits({ dataBase, sceneDate: scene('1904'), problems });
  check('on 1904 the loader returns null', on1904 === null);
  check('…without fetching the file', fetches === 0, `${fetches} fetch(es)`);
  check('…and without reporting a problem', problems.length === 0, problems.join('; '));

  const on1835 = await loadOrdinanceLimits({ dataBase, sceneDate: scene('1835'), problems });
  check('on 1835 the loader returns the limits', on1835 !== null && typeof on1835.coversPlacement === 'function',
    problems.join('; '));

  stub({ ...hay, target_date: '1904-07-01' });
  problems = [];
  const misdated = await loadOrdinanceLimits({ dataBase, sceneDate: scene('1835'), problems });
  check("a file re-derived for another date does not reach 1835 through the path's name",
    misdated === null && problems.length === 0);
} finally {
  globalThis.fetch = realFetch;
}

console.log(`${failures} failure(s)`);
process.exit(failures ? 1 : 0);
