/**
 * test_cloud_save.mjs — T-3777, cloud save (renderers/web/js/cloud-save.js).
 *
 * Two browsers of one student against a fake Firestore that answers runQuery and commit the
 * way the REST API does (REQUEST_TIME stamped by the server). It holds:
 *   - the three-way merge: one side changed wins, an edit beats a delete, two edits keep the
 *     newer, met/found joins and keeps the earlier day, a new browser takes the account's
 *     Settings, and the device's own graphics never travel;
 *   - offline and refused: the browser's copy is untouched, and the next sync catches up;
 *   - a damaged browser copy is neither overwritten nor pushed;
 *   - the writes match docs/SIGN-IN.md's users rule (fields, size, server time);
 *   - debouncing: twenty quick changes make one commit;
 *   - a 30-student, 45-minute lesson's writes and reads, printed, far inside the free tier.
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  mergeMap, mergeDoc, hashOf, syncOnce, readLocal, writeOf, cloudSaveFor, startCloudSave, cloudSaveLine,
  CLOUD_PARTS, MAX_V, DEVICE_FIELDS, STATE_KEY, TIMING,
} from '../renderers/web/js/cloud-save.js';
import { createFieldNotebook, NOTEBOOK_KEY } from '../renderers/web/js/field-notebook.js';
import { createMetFound, METFOUND_KEY } from '../renderers/web/js/met-found.js';
import { ACCOUNT_TREES } from '../renderers/web/js/student-data.js';

// ---- a browser's storage, and a fake Firestore ------------------------------------------
const storageOf = (init = {}) => {
  const m = new Map(Object.entries(init));
  return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k), map: m };
};
function fakeFirestore() {
  const docs = new Map(); // full name → { v, deleted, at }
  let clock = Date.parse('2026-11-27T15:00:00Z');
  const stats = { writes: 0, reads: 0, commits: 0, queries: 0 };
  let down = false, refuse = false;
  const fetchFn = async (url, init = {}) => {
    if (down) throw new TypeError('Failed to fetch');
    if (refuse) return { ok: false, status: 403, json: async () => ({}) };
    const body = init.body ? JSON.parse(init.body) : {};
    const ok = (b) => ({ ok: true, status: 200, json: async () => b });
    if (url.endsWith(':runQuery')) {
      stats.queries++;
      const parent = url.slice(url.indexOf('/documents/') + '/documents/'.length, -':runQuery'.length);
      const q = body.structuredQuery;
      const prefix = `${parent}/${q.from[0].collectionId}/`;
      const since = q.where?.fieldFilter?.value?.timestampValue;
      const rows = [...docs].filter(([n, d]) => n.startsWith(prefix) && !n.slice(prefix.length).includes('/') && (!since || d.at > since))
        .slice(q.offset ?? 0, (q.offset ?? 0) + (q.limit ?? 300));
      stats.reads += Math.max(1, rows.length);
      return ok(rows.length ? rows.map(([n, d]) => ({ document: { name: `projects/p/databases/(default)/documents/${n}`,
        fields: { v: { stringValue: d.v }, deleted: { booleanValue: d.deleted }, at: { timestampValue: d.at } } } })) : [{ readTime: 'x' }]);
    }
    if (url.endsWith(':commit')) {
      stats.commits++;
      clock += 1000;
      const at = new Date(clock).toISOString();
      for (const w of body.writes) {
        stats.writes++;
        const name = (w.update?.name ?? w.delete).split('/documents/')[1];
        if (w.delete) { docs.delete(name); continue; }
        assert.deepEqual(Object.keys(w.update.fields).sort(), ['deleted', 'v'], 'a write sends v and deleted');
        assert.deepEqual(w.updateTransforms, [{ fieldPath: 'at', setToServerValue: 'REQUEST_TIME' }], 'and the server stamps at');
        assert.ok(w.update.fields.v.stringValue.length <= MAX_V, 'v within the rule');
        docs.set(name, { v: w.update.fields.v.stringValue, deleted: w.update.fields.deleted.booleanValue, at });
      }
      return ok({ writeResults: body.writes.map(() => ({ updateTime: at })) });
    }
    throw new Error(`unexpected ${url}`);
  };
  return { docs, fetchFn, stats, set down(v) { down = v; }, set refuse(v) { refuse = v; }, tick(ms) { clock += ms; } };
}
const account = { uid: 'stu1', method: 'google', idToken: async () => 'tok' };
let t = Date.parse('2026-11-27T15:00:00Z');
const now = () => new Date(t += 1000).toISOString();
const sync = (fs, storage, extra = {}) => syncOnce({ projectId: 'p', account, storage, fetchFn: fs.fetchFn, now, ...extra });
const notebookOf = (storage) => JSON.parse(storage.getItem(NOTEBOOK_KEY) ?? '{"entries":[]}').entries;

// ---- the pure merge -----------------------------------------------------------------------
assert.deepEqual(mergeMap({ a: 1, b: 2 }, { a: 1, b: 3 }, { a: 4, b: 2 }, () => 'clash'), { a: 4, b: 3 }, 'each side keeps its own change');
assert.deepEqual(mergeMap({ a: 1 }, { a: 2 }, { a: 3 }, (l, r) => `${l}|${r}`), { a: '2|3' }, 'a key changed on both is settled by both()');
assert.deepEqual(mergeMap({ a: 1, b: 2 }, { b: 2 }, { a: 1, b: 2, c: 5 }, () => 'x'), { b: 2, c: 5 }, 'deleted here, kept there unchanged: gone; added there: kept');
assert.deepEqual(mergeMap({ x: true }, {}, { x: '2026-11-01', y: '2026-11-02' }, () => 'x'), { y: '2026-11-02' }, 'a list base keeps keys only');
{
  const base = { h: hashOf({ id: 'e', text: 'a' }) };
  const id = 'notebook/e';
  assert.deepEqual(mergeDoc(id, base, undefined, { value: { id: 'e', text: 'b' }, at: '2026-11-27T15:00:00Z' }, '2026-11-27T16:00:00Z'),
    { value: { id: 'e', text: 'b' }, push: false }, 'deleted here, edited there: the edit stays');
  assert.deepEqual(mergeDoc(id, base, { id: 'e', text: 'c' }, { value: undefined, at: '2026-11-27T17:00:00Z' }, '2026-11-27T16:00:00Z'),
    { value: { id: 'e', text: 'c' }, push: true }, 'edited here, deleted there: the edit stays and goes up');
  assert.equal(mergeDoc(id, base, { id: 'e', text: 'c' }, { value: { id: 'e', text: 'd' }, at: '2026-11-27T17:00:00Z' }, '2026-11-27T16:00:00Z').value.text, 'd', 'two edits: the newer (the account\'s)');
  assert.equal(mergeDoc(id, base, { id: 'e', text: 'c' }, { value: { id: 'e', text: 'd' }, at: '2026-11-27T15:00:00Z' }, '2026-11-27T16:00:00Z').value.text, 'c', 'two edits: the newer (this browser\'s)');
  assert.deepEqual(mergeDoc('metfound/1835-found', { h: 'x', keys: ['a'] }, { a: '2026-11-02', b: '2026-11-03' }, { value: { a: '2026-11-01', c: '2026-11-04' }, at: 'z' }, 'a').value,
    { a: '2026-11-01', b: '2026-11-03', c: '2026-11-04' }, 'met/found joins, keeping the earlier first day');
}

// ---- two browsers, one student -------------------------------------------------------------
const fs = fakeFirestore();
const a = storageOf();
const nbA = createFieldNotebook({ storage: a, now, id: (() => { let n = 0; return () => `a${++n}`; })() });
const mfA = createMetFound({ storage: a, today: () => '2026-11-27' });
nbA.add({ kind: 'note', title: 'Kinzie house', text: 'Porch faces the river.', year: '1835' });
nbA.add({ kind: 'note', title: 'Fort', text: 'Blockhouse.', year: '1812' });
mfA.record('1835', 'found', 'kinzie_house');
mfA.record('1835', 'met', 'john_kinzie');
a.setItem('chicago4d.settings', JSON.stringify({ speed: 3, nameCards: false, quality: 'high', detailKept: 2 }));
a.setItem('chicago4d.skin', 'brass');
let r = await sync(fs, a);
assert.equal(r.ok, true);
assert.equal(r.pushed, 5, 'two entries, two lists and the Settings go up');
assert.equal([...fs.docs.keys()].every((n) => n.startsWith('users/stu1/') && CLOUD_PARTS.includes(n.split('/')[2])), true, 'all under the student\'s own uid');
const prefsUp = JSON.parse(fs.docs.get('users/stu1/settings/prefs').v);
assert.ok(DEVICE_FIELDS.every((f) => !(f in prefsUp)), 'the device\'s own graphics stay on the device');
assert.equal(prefsUp['@chicago4d.skin'], 'brass');
r = await sync(fs, a);
assert.equal(r.pushed, 0, 'nothing changed, nothing written');

// A new browser: default Settings of its own, and a found place of its own.
const b = storageOf({ 'chicago4d.settings': JSON.stringify({ speed: 4.47, nameCards: true, quality: 'low' }) });
const nbB = createFieldNotebook({ storage: b, now, id: (() => { let n = 0; return () => `b${++n}`; })() });
const mfB = createMetFound({ storage: b, today: () => '2026-11-26' });
mfB.record('1835', 'found', 'kinzie_house');
mfB.record('1904', 'found', 'glessner_house');
r = await sync(fs, b);
assert.equal(r.ok, true);
assert.deepEqual(notebookOf(b).map((e) => e.title), ['Kinzie house', 'Fort'], 'the notebook arrives on the new browser');
const settingsB = JSON.parse(b.getItem('chicago4d.settings'));
assert.equal(settingsB.speed, 3, 'the account\'s Settings win on a new browser');
assert.equal(settingsB.nameCards, false);
assert.equal(settingsB.quality, 'low', 'and this device keeps its own graphics');
assert.equal(b.getItem('chicago4d.skin'), 'brass');
assert.equal(mfB.has('1835', 'met', 'john_kinzie'), true, 'people met arrive');
assert.equal(mfB.year('1835').found.kinzie_house, '2026-11-26', 'the earlier first day is kept');
assert.equal(mfB.has('1904', 'found', 'glessner_house'), true, 'and this browser\'s own finds are kept');
await sync(fs, a);
assert.equal(createMetFound({ storage: a }).has('1904', 'found', 'glessner_house'), true, 'and reach the first browser');

// An edit on one browser, a delete of the same entry on the other: the edit is kept on both.
const [kinzie] = notebookOf(a);
nbA.remove(kinzie.id);
nbB.update(kinzie.id, 'Porch faces the river; a fence in front.');
await sync(fs, a);
await sync(fs, b);
await sync(fs, a);
assert.equal(notebookOf(a).find((e) => e.id === kinzie.id)?.text, 'Porch faces the river; a fence in front.', 'an edit beats a delete, on both browsers');
// A delete with no edit elsewhere reaches the other browser.
const fort = notebookOf(a).find((e) => e.title === 'Fort');
nbB.remove(fort.id);
await sync(fs, b);
await sync(fs, a);
assert.equal(notebookOf(a).some((e) => e.id === fort.id), false, 'a delete travels');
assert.equal(JSON.parse(JSON.stringify([...fs.docs].find(([n]) => n.endsWith(fort.id))[1])).deleted, true, 'as a tombstone');
// Clearing a year on one browser while the other finds a new place there: the new one stays.
createMetFound({ storage: a }).clearYear('1904');
createMetFound({ storage: b, today: () => '2026-11-27' }).record('1904', 'found', 'kimball_house');
await sync(fs, a);
await sync(fs, b);
await sync(fs, a);
assert.deepEqual(Object.keys(createMetFound({ storage: a }).year('1904').found), ['kimball_house'], 'cleared, except what was found since');

// Offline and refused: nothing changes in the browser, and the next sync catches up.
nbA.add({ kind: 'note', title: 'Offline note', text: 'On the train.', year: '1904' });
const before = a.getItem(NOTEBOOK_KEY);
fs.down = true;
r = await sync(fs, a);
assert.deepEqual([r.ok, r.why], [false, 'offline']);
assert.equal(a.getItem(NOTEBOOK_KEY), before, 'offline: the browser\'s copy untouched');
fs.down = false; fs.refuse = true;
r = await sync(fs, a);
assert.deepEqual([r.ok, r.why], [false, 'refused (403)']);
fs.refuse = false;
r = await sync(fs, a);
assert.equal(r.ok, true);
await sync(fs, b);
assert.ok(notebookOf(b).some((e) => e.title === 'Offline note'), 'the note written offline arrives once back');

// A damaged copy is neither overwritten nor pushed.
const c = storageOf({ [NOTEBOOK_KEY]: '{"version":1,"entries":[{"kind":"bogus"}]}' });
r = await sync(fs, c);
assert.equal(r.ok, true);
assert.equal(c.getItem(NOTEBOOK_KEY), '{"version":1,"entries":[{"kind":"bogus"}]}', 'a damaged notebook is left as it was');
assert.ok(readLocal(c).unreadable.includes('notebook'));

// Who may: a real sign-in, with the switch on.
assert.equal(cloudSaveFor(account, { enabled: true, cloudFeatures: true }), true);
assert.equal(cloudSaveFor({ ...account, method: 'email' }, { enabled: true, cloudFeatures: true }), false, 'never the email alone');
assert.equal(cloudSaveFor(account, { enabled: true, cloudFeatures: false }), false, 'never while the switch is off');
assert.equal(cloudSaveFor(null, { enabled: true, cloudFeatures: true }), false);
assert.match(cloudSaveLine({ state: 'saved', at: '2026-11-27T15:00:00Z' }, { clock: () => '9:00 AM' }), /^Saved to your account at 9:00 AM\.$/);

// The writes are what the users rule allows, and Delete my saved data covers every part.
const rules = readFileSync(new URL('../docs/SIGN-IN.md', import.meta.url), 'utf8');
assert.ok(rules.includes(`request.resource.data.v.size() <= ${MAX_V}`), 'the rule\'s size is MAX_V');
assert.ok(rules.includes("request.resource.data.at == request.time"), 'and at is the server\'s time');
assert.ok(rules.includes(`part in [${CLOUD_PARTS.map((p) => `'${p}'`).join(', ')}]`), 'in exactly the parts written');
assert.deepEqual([...ACCOUNT_TREES.users], [...CLOUD_PARTS], 'Delete my saved data removes every part');
assert.equal(writeOf('p', 'u', 'notebook/x', undefined).update.fields.deleted.booleanValue, true);

// ---- debouncing: twenty quick changes, one commit ------------------------------------------
{
  const f = fakeFirestore();
  const s = storageOf();
  const nb = createFieldNotebook({ storage: s, now });
  const timers = (() => {
    let clock = 0, seq = 0; const q = new Map();
    return {
      setTimeout: (fn, ms) => { q.set(++seq, { fn, at: clock + ms }); return seq; }, clearTimeout: (id) => q.delete(id),
      setInterval: () => 0, clearInterval: () => {},
      async advance(ms) { clock += ms; for (const [id, x] of [...q]) if (x.at <= clock) { q.delete(id); await x.fn(); } },
    };
  })();
  const ctl = startCloudSave({ account, projectId: 'p', storage: s, fetchFn: f.fetchFn, sources: [nb], timers, doc: null, now });
  await ctl.ready;
  const commitsBefore = f.stats.commits;
  for (let i = 0; i < 20; i++) { nb.add({ kind: 'note', title: `n${i}`, text: 'x' }); await timers.advance(1000); }
  assert.equal(f.stats.commits, commitsBefore, 'no write per change');
  await timers.advance(TIMING.debounceMs);
  await ctl.flush();
  assert.equal(f.stats.commits - commitsBefore, 1, 'twenty changes in one commit');
  assert.equal(ctl.status.state, 'saved');
  ctl.stop();
}

// ---- a lesson: 30 students, 45 minutes ----------------------------------------------------
{
  const f = fakeFirestore();
  let seed = 7;
  const rand = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
  for (let s = 0; s < 30; s++) {
    const who = { uid: `s${s}`, method: 'google', idToken: async () => 'tok' };
    const st = storageOf();
    const nb = createFieldNotebook({ storage: st, now });
    const mf = createMetFound({ storage: st, today: () => '2026-11-27' });
    await syncOnce({ projectId: 'p', account: who, storage: st, fetchFn: f.fetchFn, now });     // sign-in
    for (let minute = 0; minute < 45; minute++) {
      // A busy student: a find most minutes, a met person every few, a note every four, a
      // Settings change now and then; at most one flush a minute (the debounce's ceiling).
      let changed = false;
      if (rand() < 0.7) { mf.record('1904', 'found', `place_${s}_${minute}`); changed = true; }
      if (rand() < 0.3) { mf.record('1904', 'met', `person_${s}_${minute}`); changed = true; }
      if (minute % 4 === 0) { nb.add({ kind: 'note', title: `Note ${minute}`, text: 'What I saw.', year: '1904' }); changed = true; }
      if (rand() < 0.05) { st.setItem('chicago4d.settings', JSON.stringify({ speed: 3 + rand() })); changed = true; }
      f.tick(60000);
      if (changed) await syncOnce({ projectId: 'p', account: who, storage: st, fetchFn: f.fetchFn, now });
    }
  }
  console.log(`test_cloud_save: a 30-student, 45-minute lesson writes ${f.stats.writes} documents in ${f.stats.commits} commits `
    + `and reads ${f.stats.reads} (free tier: 20,000 writes and 50,000 reads a day)`);
  assert.ok(f.stats.writes < 4000, `a lesson's writes stay far inside the free tier (${f.stats.writes})`);
  assert.ok(f.stats.reads < 20000, `and its reads (${f.stats.reads})`);
}

console.log('test_cloud_save: three-way merge, edits beat deletes, new browser takes the account\'s Settings, offline and refusal safe, damaged copy untouched, debounced');
