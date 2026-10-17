// T-2624 — the string table's own mechanics (js/strings/index.js): sections register
// and extend, t() fills placeholders and never returns a key, applyStrings fills the page.
//
//   node tools/test_strings.mjs
import assert from 'node:assert/strict';
import { register, t, has, entries, applyStrings } from '../renderers/web/js/strings/index.js';
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

console.log('STRING TABLE PASS — sections register and extend, placeholders fill, no key ever shown, the page fills from the table');
