// T-2624 — the string table's own mechanics (js/strings/index.js): sections register
// and extend, t() fills placeholders and never returns a key, applyStrings fills the page.
//
//   node tools/test_strings.mjs
import assert from 'node:assert/strict';
import { register, t, has, entries, applyStrings, isResearcherKey, RESEARCHER } from '../renderers/web/js/strings/index.js';
import '../renderers/web/js/strings/arrival.js';
import '../renderers/web/js/strings/hud.js';
import '../renderers/web/js/strings/navigator.js';
import { LOCKED_TERMS, gradeTerm } from '../renderers/web/js/strings/terms.js';

assert.equal(t('hud.tab.sources'), 'Sources');
assert.equal(t('hud.tab.move'), 'Move');
assert.equal(t('hud.tab.guide'), 'Guide');
assert.equal(t('hud.tab.shops'), 'Shops & work');
assert.equal(t('arrival.stalled', { year: 1950 }), 'The jump stalled somewhere around 1950.');
assert.equal(t('nav.front.away', { distance: '40 ft' }), '40 ft away');
assert.equal(t('nav.no-such-key'), '', 'a missing key is empty, never the key');
assert.equal(t('nowhere.at.all', null, 'fallback'), 'fallback');
assert.equal(t('arrival.stalled', {}), 'The jump stalled somewhere around {year}.', 'a missing placeholder stays visible to the gate, not to undefined');
assert.ok(has('terms.confidence-view'));
assert.equal(t('terms.confidence-view'), 'Confidence view');

// A later lane adds its own section, and may extend one, without touching another's file.
register('jaunts-test', { title: 'Jaunts' });
register('jaunts-test', { 'stop.next': 'Next stop' });
assert.equal(t('jaunts-test.title'), 'Jaunts');
assert.equal(t('jaunts-test.stop.next'), 'Next stop');
assert.throws(() => register('Bad_Name', {}), /namespace/);
assert.throws(() => register('ok', { n: 3 }), /not a string/);
assert.ok(entries().some(([k]) => k === 'jaunts-test.stop.next'));

assert.deepEqual(LOCKED_TERMS.map(([term]) => term),
  ['Attested', 'Inferred', 'Reconstructed', 'Confidence view', 'Liberties', 'Sources', 'Jaunts']);
assert.deepEqual(gradeTerm('attested').label, 'Attested');
assert.equal(gradeTerm('reconstructed').meaning, LOCKED_TERMS[2][1]);
assert.deepEqual(gradeTerm('documented'), { label: '', meaning: '' }, 'a retired grade has no label');

// applyStrings: text, title and aria-label from the table; an unknown key is left alone.
const el = (data, attrs = {}) => ({ dataset: data, textContent: 'old', attrs: { ...attrs },
  getAttribute(n) { return this.attrs[n] ?? null; }, setAttribute(n, v) { this.attrs[n] = v; } });
const a = el({ str: 'hud.tab.sources' });
const b = el({ strTitle: 'hud.tab.guide', strLabel: 'nav.open' }, { title: 'Controls' });
const c = el({ str: 'hud.no-such' });
const n = applyStrings({ querySelectorAll: () => [a, b, c] });
assert.equal(a.textContent, 'Sources');
assert.equal(b.attrs.title, 'Guide');
assert.equal(b.attrs['aria-label'], 'Open the Navigator');
assert.equal(c.textContent, 'old', 'an unknown key never blanks the markup');
assert.equal(n, 3);
assert.equal(applyStrings(null), 0);

// T-2668: the Researcher-mode exemption is a key segment, the same rule the lint applies.
assert.equal(RESEARCHER, 'researcher');
assert.ok(isResearcherKey('researcher.order-book'));
assert.ok(isResearcherKey('guide.researcher.why-full'));
assert.ok(!isResearcherKey('researchers.note'), 'a namespace merely starting with the word is not exempt');
assert.ok(!isResearcherKey('hud.tab.sources'));
assert.ok(!isResearcherKey(null));

// Gap analysis item 15: Spanish. Every Spanish section key is one the English table has, with
// the same placeholders; every text pattern keeps its own; the page translator swaps whole
// strings only; a jaunt's overlay lands on the passages it names and nowhere else.
{
  const { readdirSync } = await import('node:fs');
  const dir = new URL('../renderers/web/js/strings/', import.meta.url);
  for (const f of readdirSync(dir).filter((f) => f.endsWith('.js')).sort()) await import(new URL(f, dir));
  const { LANG, LANGUAGES, localeText, localePatterns } = await import('../renderers/web/js/strings/index.js');
  assert.equal(LANG, 'en', 'with no choice and no browser, the table reads English');
  assert.deepEqual(LANGUAGES.map(([c]) => c), ['en', 'es']);
  const es = (await import('../renderers/web/js/strings/es/index.js')).default;
  const english = new Map(entries());
  const holes = (s) => [...String(s).matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort().join(',');
  const bad = [];
  for (const [ns, table] of Object.entries(es.sections)) {
    for (const [k, v] of Object.entries(table)) {
      const key = `${ns}.${k}`;
      if (!english.has(key)) bad.push(`${key}: no such English string`);
      else if (typeof v !== 'string' || !v.trim()) bad.push(`${key}: empty`);
      else if (holes(v) !== holes(english.get(key))) bad.push(`${key}: placeholders {${holes(v)}} but English has {${holes(english.get(key))}}`);
    }
  }
  for (const [en, tr] of Object.entries(es.text)) {
    if (typeof tr !== 'string' || !tr.trim()) bad.push(`text "${en}": empty`);
    if (en !== en.trim()) bad.push(`text "${en}": an entry is the trimmed string`);
  }
  for (const pair of es.patterns) {
    if (!Array.isArray(pair) || pair.length !== 2) { bad.push(`pattern ${JSON.stringify(pair)}: not [English, Spanish]`); continue; }
    const [en, tr] = pair;
    if (holes(en) !== holes(tr)) bad.push(`pattern "${en}": placeholders differ`);
    if (!/[A-Za-z]{3}/.test(en.replace(/\{\w+\}/g, ''))) bad.push(`pattern "${en}": too little fixed text to match safely`);
  }
  assert.deepEqual(bad, [], `Spanish strings:\n  ${bad.join('\n  ')}`);

  // The page translator (js/i18n-dom.js), fed a small locale by hand.
  localeText.set('Free roam', 'Recorrido libre');
  localeText.set('Walk', 'Caminar');
  localePatterns.push(['{n} stops', '{n} paradas'], ['Going to {place}', 'Rumbo a {place}']);
  const { translate } = await import('../renderers/web/js/i18n-dom.js');
  assert.equal(translate('Free roam'), 'Recorrido libre');
  assert.equal(translate('  Free roam '), '  Recorrido libre ', 'the node keeps its own spacing');
  assert.equal(translate('Free roaming'), null, 'only a whole string is swapped');
  assert.equal(translate('12 stops'), '12 paradas');
  assert.equal(translate('Going to Walk'), 'Rumbo a Caminar', 'a matched value is itself translated when the locale holds it');
  assert.equal(translate('Recorrido libre'), null, 'a translation is never translated again');
  assert.equal(translate('— MB'), null);
  localeText.set('The Lake House was built of brick.', 'La Lake House se construía de ladrillo.');
  assert.equal(translate('The Lake House was built of brick. — 1883/1902 Recollections'), 'La Lake House se construía de ladrillo. — 1883/1902 Recollections',
    'a line put together from parts reads part by part');
  assert.equal(translate('Nothing held · nor this'), null);
  localeText.clear(); localePatterns.length = 0;

  // A jaunt's Spanish overlay (js/jaunt-language.js).
  const { applyPassages, current, markOf } = await import('../renderers/web/js/jaunt-language.js');
  const doc = { title: 'T', premise: 'P', opening: { text: 'O' }, stops: [{ id: 'a', text: 'A', narrative: 'N', choices: [{ id: 'x', label: 'L', consequence: 'C' }] }],
    legs: [{ story: 'S', note: 'R' }], endings: [{ id: 'e', text: 'E' }], keepsake: { title: 'K', text: 'KT', family: 'F' } };
  const n = applyPassages(doc, { title: 't', premise: 'p', opening: 'o', 'stop a': 'a', 'narrative a': 'n', 'label a x': 'l', 'consequence a x': 'c',
    'leg 0': 's', 'note 0': 'r', 'ending e': 'e', 'keepsake title': 'k', 'keepsake text': 'kt', 'stop zz': 'nowhere', 'ending zz': 'nowhere' });
  assert.equal(n, 12, 'a passage for a stop or ending the jaunt lacks lands nowhere');
  assert.deepEqual([doc.title, doc.premise, doc.opening.text, doc.stops[0].text, doc.stops[0].narrative, doc.stops[0].choices[0].label,
    doc.stops[0].choices[0].consequence, doc.legs[0].story, doc.legs[0].note, doc.endings[0].text, doc.keepsake.title, doc.keepsake.text, doc.keepsake.family],
  ['t', 'p', 'o', 'a', 'n', 'l', 'c', 's', 'r', 'e', 'k', 'kt', 'F']);
  // A passage lands only while the English it was translated from (its mark, tools/jaunts_es.py)
  // is the English shown; a corrected English reads as corrected.
  assert.equal(await markOf('Lake Street'), '31cf42c7', 'the mark is what tools/jaunts_es.py writes (sha1, first eight hex)');
  const shown = { title: 'Old title', premise: 'Changed premise', stops: [] };
  const live = await current(shown, { title: [await markOf('Old title'), 'Título'], premise: [await markOf('The premise as it was'), 'Premisa'] });
  assert.deepEqual(live, { title: 'Título' }, 'a passage whose English changed since translation stays English');
  console.log(`SPANISH PASS — ${Object.values(es.sections).reduce((n, t) => n + Object.keys(t).length, 0)} of ${english.size} table strings, `
    + `${Object.keys(es.text).length} page strings, ${es.patterns.length} patterns`);
}

console.log('STRING TABLE PASS — sections register and extend, placeholders fill, no key ever shown, the page fills from the table');
