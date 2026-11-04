// SPDX-License-Identifier: GPL-3.0-or-later
import fs from 'node:fs';
import assert from 'node:assert/strict';
const read = path => fs.readFileSync(new URL(path, import.meta.url), 'utf8');
const source = read('../renderers/web/js/businesses.js');
const tick = () => new Promise(resolve => setImmediate(resolve));
function deferred() { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; }
function harness(source, joinPromise, overlayPromise = Promise.resolve({})) {
  const start = source.indexOf('async function seatSlot(card, r');
  const end = source.indexOf('\n  function close()', start);
  assert(start >= 0 && end > start);
  const method = source.slice(start, end);
  const call = source.match(/state\.seatPending = seatSlot\(cardEl, r(?:, seq)?\)\.catch\(\(\) => \{\}\);/);
  assert(call, 'Use the actual open-to-seat call site, including captured sequence');
  let readerCalls = 0;
  const build = new Function('loadResidentJoins', 'loadReaderText', 'readerCopy', `
    let openSeq = 0, reader = null;
    const state = { open: null, seatPending: null };
    const dataBase = 'https://example.invalid/data/', sceneId = '1835', problems = [];
    const registry = new Set(), goTarget = () => null;
    const seatHtml = row => 'seat:' + row.id, buildingTitle = () => null, words = x => x;
    ${method}
    return { request(cardEl, r) {
      const seq = ++openSeq; state.open = r.id;
      ${call[0]}
      return state.seatPending;
    } };
  `);
  const api = build(() => joinPromise, () => { readerCalls++; return overlayPromise; }, x => x);
  const slot = { innerHTML: 'initial' };
  const card = { hidden: false, queries: 0, querySelector(selector) {
    this.queries++;
    if (selector === '.biz-seat-slot') return slot;
    if (selector === '.biz-locs .biz-go') return null;
    throw Error('Unexpected actual selector ' + selector);
  } };
  return { api, card, slot, readerCalls: () => readerCalls };
}
const A = { id: 'biz_A', register_id: 'register_A' }, B = { id: 'biz_B' };
const joins = () => ({ seatByBusiness: new Map([['register_A', { id: 'address_A', rung: 'street' }]]) });
async function coldJoinRace(source) {
  const wait = deferred(), h = harness(source, wait.promise);
  const a = h.api.request(h.card, A); await tick();
  await h.api.request(h.card, B); h.slot.innerHTML = 'B:no seat'; h.card.queries = 0;
  wait.resolve(joins()); await a;
  return { content: h.slot.innerHTML, staleQueries: h.card.queries };
}
async function overlayRace(source) {
  const wait = deferred(), h = harness(source, Promise.resolve(joins()), wait.promise);
  const a = h.api.request(h.card, A); await tick();
  assert.equal(h.readerCalls(), 1, 'A is genuinely suspended in its second await');
  await h.api.request(h.card, B); h.slot.innerHTML = 'B:no seat'; h.card.queries = 0;
  wait.resolve({}); await a;
  return { content: h.slot.innerHTML, staleQueries: h.card.queries };
}
async function currentA(source) {
  const wait = deferred(), h = harness(source, wait.promise);
  const a = h.api.request(h.card, A); wait.resolve(joins()); await a;
  return h.slot.innerHTML;
}
assert.deepEqual(await coldJoinRace(source), { content: 'B:no seat', staleQueries: 0 });
assert.deepEqual(await overlayRace(source), { content: 'B:no seat', staleQueries: 0 });
assert.equal(await currentA(source), 'seat:address_A', 'Current A still receives the real join');
const early = source.replace('    if (seq !== openSeq || state.open !== r.id) return;\n', '')
  .replace('    if (!r.register_id) return;', '    if (!r.register_id) return;\n    if (seq !== openSeq || state.open !== r.id) return;');
assert.notEqual(early, source);
assert.equal((await coldJoinRace(early)).content, 'seat:address_A', 'Planted guard-before-await fault is caught');
const lostSeq = source.replace('seatSlot(cardEl, r, seq)', 'seatSlot(cardEl, r)');
assert.notEqual(lostSeq, source);
assert.equal(await currentA(lostSeq), 'initial', 'Planted missing sequence forwarding loses current seat and is caught');
console.log(JSON.stringify({ scope: 'Actual shipped business seatSlot and open call site under asynchronous join/reader resolution; no browser claim', latestBusinessCardPreserved: true, noStaleSharedCardQueries: true, currentAStillShowsJoin: true, negativeControls: ['guard before awaits', 'lost captured-sequence forwarding'] }, null, 2));
