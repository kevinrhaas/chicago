// T-2643 — Inspect's Story tab (js/inspect-story.js): BUILT, YOU ARE HERE and TODAY on one
// timeline from design to today, from the dated facts the data already carries, with another
// scene's era filtered out and what came after the visit labelled as after it.
//
//   node tools/test_nav_story.mjs
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { storyTimeline, renderStory, visitWords, _test } from '../renderers/web/js/inspect-story.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const data = path.join(here, '../data');
const read = (p) => JSON.parse(readFileSync(path.join(data, p), 'utf8'));
const S1904 = { id: '1904', target_date: '1904-07-01' };
const S1835 = { id: '1835', target_date: '1835-07-01' };

// --- helpers -------------------------------------------------------------------------
assert.equal(_test.earliest('1885'), '1885-01-01');
assert.equal(_test.earliest('1885-05'), '1885-05-01');
assert.equal(_test.weaker('inferred', 'attested'), 'inferred');
assert.equal(_test.weaker('inferred', 'reconstructed'), 'reconstructed');
assert.equal(_test.weaker('inferred', undefined), null, 'no position grade, no grade');
assert.equal(_test.span({ from: '1887-12-01', to: '1946-08-31', from_is: 'began', to_is: 'ended' }), '1887\u00a0–\u00a01946');
// T-3037: an end the record does not date is a bound, and is never printed as a date.
assert.equal(_test.span({ from: '1904-07-01', to: '1911-12-31' }), '');
assert.equal(_test.span({ from: '1904-07-01', to: '1911-12-31', to_is: 'seen' }), 'still in 1911');
assert.equal(visitWords('1904-07-01'), '1 July 1904');
assert.equal(visitWords('1904'), null, 'a year alone is not dressed up as a day');

// --- Glessner, from its own summary record and sidecar ---------------------------------
const sum = read('summaries/glessner_house.json');
const sidecar = read('sidecars/1904/glessner_house.json');
const g = storyTimeline({ sum, sidecar, scene: S1904 });
const marks = g.rows.map((r) => r.mark);
assert.equal(g.lead, 'From design to today. Your visit is 1 July 1904.');
assert.equal(g.rows[0].mark, 'event', 'the timeline runs from design: the record\'s first dated fact leads');
assert.equal(g.rows[0].when, '1885');
const iBuilt = marks.indexOf('built');
const iHere = marks.indexOf('here');
assert.ok(iBuilt > 0 && iBuilt < iHere, 'BUILT sits among the years before the visit');
assert.equal(g.rows[iBuilt].when, String(sum.built.year));
assert.equal(g.rows[iBuilt].grade, sum.built.grade, 'BUILT carries the record\'s own grade');
assert.equal(g.rows[iHere].when, '1904');
assert.equal(g.rows[iHere].text, '1 July 1904');
assert.equal(marks.at(-1), 'today', 'TODAY closes the timeline');
assert.equal(g.rows.at(-1).text, 'Still standing · A house museum');
assert.equal(g.rows.at(-1).grade, 'attested');
assert.equal(g.rows.at(-1).after, true, 'Today is after your visit');
assert.equal(marks.filter((m) => m === 'here').length, 1);
// Every story entry renders (all are tagged 1904), in date order, each with its grade.
const events = g.rows.filter((r) => r.mark === 'event');
assert.equal(events.length, sum.story.length);
assert.ok(events.every((r) => r.grade === 'attested'));
// After your visit: exactly the entries whose earliest day is past 1 July 1904. The entry dated
// "1904" may be before the visit, so it is not marked after it, and sits before YOU ARE HERE.
for (const r of g.rows.slice(0, iHere)) assert.equal(r.after, false, `${r.when} ${r.text} is before the visit`);
for (const r of g.rows.slice(iHere + 1)) assert.equal(r.after, true, `${r.when} ${r.text} is after the visit`);
assert.deepEqual(g.rows.slice(iHere + 1, -1).map((r) => r.when), ['1924', '1936', '1946', '1966']);
// The modelled phase moves here as "Stood here", with its claim's grade.
const stood = g.rows.find((r) => r.mark === 'stood');
assert.equal(stood.text, 'On record standing 1887\u00a0–\u00a01946.');
assert.equal(stood.grade, sidecar.documented_range.confidence);

// --- the era filter: another scene's content never renders -----------------------------
const mixed = { ...sum, story: [...sum.story, { date: '1835-08-05', text: 'A rule from another scene.', era: '1835', grade: 'attested' }] };
const m = storyTimeline({ sum: mixed, sidecar, scene: S1904, fireLimit: { inside: true, passed: '1835-08-05' } });
assert.ok(!m.rows.some((r) => /another scene|fire limit|hay/i.test(r.text)), 'no 1835 entry or civic rule on a 1904 building');
assert.equal(m.rows.length, g.rows.length);
// And with no scene at all, no tagged entry can claim to belong.
assert.equal(storyTimeline({ sum, sidecar, scene: null }).rows.filter((r) => r.mark === 'event').length, 0);

// --- an 1835 building without a record: honest gaps, the fire limit after the visit ------
const hogan = read('sidecars/1835/hogan_store.json');
const h = storyTimeline({ sidecar: hogan, scene: S1835, fireLimit: { inside: true, passed: '1835-08-05' } });
assert.deepEqual(h.rows.map((r) => r.mark), ['built', 'stood', 'here', 'fire', 'today']);
assert.equal(h.rows[0].missing, true);
assert.equal(h.rows[0].date, null, 'no build date is composed from where the evidence begins');
assert.equal(h.rows[0].text, 'Our records give no date for when it was built.');
const fire = h.rows.find((r) => r.mark === 'fire');
assert.equal(fire.after, true, 'the 5 August 1835 by-law is after a 1 July 1835 visit');
assert.equal(fire.when, '1835');
assert.equal(fire.grade, _test.weaker('inferred', hogan.placement.position_confidence), 'never stronger than where the building stands');
assert.match(fire.text, /inside it/);
assert.match(storyTimeline({ sidecar: hogan, scene: S1835, fireLimit: { inside: false, passed: '1835-08-05' } }).rows.find((r) => r.mark === 'fire').text, /outside it/);
assert.equal(h.rows.at(-1).missing, true);
assert.equal(h.rows.at(-1).text, 'Our records do not say what stands here now.');
assert.equal(storyTimeline({ sidecar: hogan, scene: S1835, fireLimit: null }).rows.some((r) => r.mark === 'fire'), false, 'not loaded is not a side');

// --- the sidecar's own present status, where there is no record --------------------------
const t = storyTimeline({ sidecar, scene: S1904 });
assert.equal(t.rows.at(-1).text, String(sidecar.attributes.present_status.value));
const tBuilt = t.rows.find((r) => r.mark === 'built');
assert.equal(tBuilt.when, '1887', 'T-3037: the sidecar\'s own built attribute dates it');
assert.equal(tBuilt.grade, sidecar.attributes.built.confidence);

// --- 1736 Prairie (T-3037): the sources disagree, and the card says so ------------------
const mcb = read('sidecars/1904/house_1736_prairie.json');
const k = storyTimeline({ sidecar: mcb, scene: S1904 });
const kBuilt = k.rows.find((r) => r.mark === 'built');
assert.equal(kBuilt.text, 'Built in 1864 or 1875.');
assert.equal(kBuilt.when, '1864');
assert.equal(kBuilt.grade, 'inferred');
assert.equal(k.rows.find((r) => r.mark === 'stood').text, 'On record standing still in 1911.');
assert.ok(!k.rows.some((r) => r.mark !== 'here' && /1904/.test(r.text)), 'no row dates it by the scene\'s own year');

// --- a record whose range is all bounds: no Stood here row, and no composed date ---------
const bare = storyTimeline({ sidecar: { documented_range: { from: '1835-01-01', to: '1835-12-31', confidence: 'reconstructed' } }, scene: S1835 });
assert.deepEqual(bare.rows.map((r) => r.mark), ['built', 'here', 'today']);

// --- coarse dates and a scene with only a year ----------------------------------------
const coarse = storyTimeline({ sum: { story: [
  { date: '1904-08', text: 'In August.', era: '1904', grade: 'inferred' },
  { date: '1904', text: 'Some time that year.', era: '1904', grade: 'inferred' },
  { date: '1904-06-30', text: 'The day before.', era: '1904', grade: 'inferred' }] }, scene: S1904 });
assert.deepEqual(coarse.rows.map((r) => `${r.mark}:${r.after}`), ['built:false', 'event:false', 'event:false', 'here:false', 'event:true', 'today:true']);
const yearOnly = storyTimeline({ sum: { story: [{ date: '1904-08', text: 'In August.', era: '1904', grade: 'inferred' }] }, scene: { id: '1904' } });
assert.equal(yearOnly.lead, 'From design to today. Your visit is in 1904.');
assert.equal(yearOnly.rows.find((r) => r.mark === 'event').after, false, 'without a scene day, the same year is not after');

// --- the drawing -------------------------------------------------------------------------
function fakeDoc() {
  const make = (tag) => {
    const el = {
      tagName: tag.toUpperCase(), className: '', _text: '', dataset: {}, attrs: {}, children: [],
      setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; },
      append(...cs) { for (const c of cs) { c.parent = el; el.children.push(c); } },
      get lastChild() { return el.children.at(-1) ?? null; },
      set textContent(v) { el._text = String(v); el.children = []; },
      get textContent() { return el._text + el.children.map((c) => c.textContent).join(''); },
    };
    return el;
  };
  return { createElement: make, createTextNode: (s) => ({ textContent: s, children: [] }) };
}
const all = (n, f, out = []) => { if (f(n)) out.push(n); for (const c of n.children ?? []) all(c, f, out); return out; };
const doc = fakeDoc();
const dots = [];
const dot = (d, grade) => { const i = d.createElement('i'); i.className = `fact-dot fact-${grade}`; dots.push(grade); return i; };
const block = renderStory(doc, g, dot);
const items = all(block, (n) => n.tagName === 'LI');
assert.equal(items.length, g.rows.length);
const kick = all(block, (n) => n.className === 'insp-kicker').map((n) => n.textContent);
assert.deepEqual(kick.filter((k) => ['Built', 'You are here', 'Today'].includes(k)), ['Built', 'You are here', 'Today'],
  'the three marks, in order (drawn in capitals by the stylesheet)');
const hereLi = items.find((n) => n.dataset.mark === 'here');
assert.equal(hereLi.getAttribute('aria-current'), 'date');
const afterTags = all(block, (n) => n.className === 'insp-after');
assert.equal(afterTags.length, g.rows.filter((r) => r.after).length);
assert.ok(afterTags.every((n) => n.textContent === 'After your visit'));
assert.equal(dots.length, g.rows.filter((r) => r.grade).length, 'every graded fact line carries its dot');
const text = block.textContent;
assert.ok(!/[a-z0-9]+_[a-z0-9]+/i.test(text), 'no snake_case reaches a visitor');
assert.ok(!/\b(attested|inferred|reconstructed)\b/.test(text), 'grade words appear only as dots, named for a screen reader');

// --- T-3042: a summary record's build date as its sources give it --------------------------
const pull = read('summaries/pullman_house_1729_prairie.json');
const pr = storyTimeline({ sum: pull, sidecar: read('sidecars/1904/pullman_house_1729_prairie.json'), scene: S1904 });
const pBuilt = pr.rows.find((r) => r.mark === 'built');
assert.equal(pBuilt.when, '1870', 'a phrase is placed at its earliest year');
assert.equal(pBuilt.text, 'Built between 1870 and 1876.');

console.log('test_nav_story: OK');
