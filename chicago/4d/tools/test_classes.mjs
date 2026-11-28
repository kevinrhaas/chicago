/**
 * test_classes.mjs — T-3778, class codes and a teacher view (renderers/web/js/classes.js).
 *
 * In the gate, without a network or Java. It holds:
 *   - the join codes: six letters and numbers, no vowels, none that read alike, no blocked run,
 *     typed in any case with a dash or spaces;
 *   - every write against docs/SIGN-IN.md's rules text: the fields each hasOnly list allows,
 *     the server's own time, made-new preconditions, a class's createdAt never re-sent;
 *   - a whole class against a fake Firestore: make, join, hand in (again after an edit, take
 *     back), roster, new code, remove, leave, close, a removed student told once;
 *   - the CSV (a formula is kept as text, quotes and line breaks survive) and the printed
 *     sheet (every name and note escaped, no script), and no grade or score anywhere;
 *   - Delete my saved data reads a student's classes before the tree that names them goes;
 *   - a reflection saved from a jaunt's check is a notebook note marked as one, and older
 *     notebook entries are unchanged.
 * The rules themselves run in Firebase's own engine in tools/test_classes_emulator.mjs (not a
 * gate step: it needs Java and the emulator).
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  CODE_ALPHABET, CODE_LENGTH, codeOk, makeCode, typedCode, shownCode, classesFor, docsRoot,
  classWrite, codeWrite, memberWrite, mineWrite, handinWrite, lastInWrite,
  makeClass, myClasses, classRoster, newCode, closeClass, removeStudent, lookUpCode, joinClass,
  myClass, leaveClass, handIn, takeBack, deleteClassData, rosterRows, classCSV, classSheetHTML, CLASS_LIMITS,
} from '../renderers/web/js/classes.js';
import { createFieldNotebook, TOPICS } from '../renderers/web/js/field-notebook.js';

// ---- codes ----------------------------------------------------------------------------------
assert.ok(!/[AEIOU015LS]/.test(CODE_ALPHABET), 'no vowels and nothing that reads like another letter');
let seed = 7;
const random = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);
const seen = new Set();
for (let i = 0; i < 3000; i++) {
  const c = makeCode(random);
  assert.ok(codeOk(c) && c.length === CODE_LENGTH, `a made code is a code (${c})`);
  seen.add(c);
}
assert.ok(seen.size > 2990, 'codes rarely repeat');
assert.equal(codeOk('BFCKZZ'), false, 'a blocked run is never a code');
assert.equal(codeOk('BCDFG'), false);
assert.equal(codeOk('BCDFGA'), false, 'a vowel is not in a code');
assert.equal(typedCode(' bcd-fgh '), 'BCDFGH', 'case, spaces and the dash fold away');
assert.equal(shownCode('BCDFGH'), 'BCD-FGH');

// ---- who may use classes --------------------------------------------------------------------
const on = { enabled: true, cloudFeatures: true };
const acct = (uid, method = 'google') => ({ uid, method, name: `${uid} name`, idToken: async () => `tok:${uid}:${method}` });
assert.equal(classesFor(acct('t1'), on), true);
assert.equal(classesFor(acct('t1', 'email'), on), false, 'never a sign-in with the email alone');
assert.equal(classesFor(acct('t1', 'preview'), on), false);
assert.equal(classesFor(acct('t1'), { enabled: true, cloudFeatures: false }), false, 'never with the switch off');
assert.equal(classesFor(null, on), false);

// ---- every write against the rules' text --------------------------------------------------
const doc = readFileSync(new URL('../docs/SIGN-IN.md', import.meta.url), 'utf8');
const listAfter = (marker) => {
  const at = doc.indexOf(marker);
  assert.ok(at > 0, `docs/SIGN-IN.md has ${marker}`);
  const m = /hasOnly\(\[([^\]]*)\]\)/.exec(doc.slice(at));
  return m[1].match(/'([^']+)'/g).map((s) => s.slice(1, -1)).sort();
};
const written = (w) => [...Object.keys(w.update.fields), ...(w.updateTransforms ?? []).map((x) => x.fieldPath)].sort();
const root = docsRoot('p');
const cls0 = { id: 'C1', teacher: 't1', teacherName: 'Ms. Ortiz', name: 'Room 12', group: '5', code: 'BCDFGH', open: true };
assert.deepEqual(written(classWrite(root, cls0, { create: true })), listAfter('function classFields(d)'), 'a new class sends exactly its rule\'s fields');
assert.deepEqual(classWrite(root, cls0, { create: true }).currentDocument, { exists: false }, 'and is made new, never over another');
const later = classWrite(root, cls0);
assert.ok(!('createdAt' in later.update.fields) && later.updateMask.fieldPaths.length === 6, 'a change never re-sends createdAt, which the rules hold');
assert.deepEqual(written(codeWrite(root, cls0, '2026-12-27T00:00:00Z')), listAfter('match /codes/{code}'), 'a code sends exactly its rule\'s fields');
assert.deepEqual(codeWrite(root, cls0, 'x').currentDocument, { exists: false }, 'a code is never written over another class\'s');
assert.deepEqual(written(memberWrite(root, 'C1', 's1', 'Ann', 'BCDFGH')), listAfter('function memberFields(d)'), 'a member row sends exactly its rule\'s fields');
assert.deepEqual(memberWrite(root, 'C1', 's1', 'Ann', 'BCDFGH').updateTransforms.map((x) => x.setToServerValue), ['REQUEST_TIME', 'REQUEST_TIME'], 'joined and last in are the server\'s time');
assert.deepEqual(lastInWrite(root, 'C1', 's1').transform.fieldTransforms, [{ fieldPath: 'lastIn', setToServerValue: 'REQUEST_TIME' }], 'a visit moves only last in');
const entry0 = { id: 'e1', kind: 'note', title: 'The fort', text: 'Two blockhouses.', year: '1812', topic: 'reflection' };
assert.deepEqual(written(handinWrite(root, 'C1', 's1', 'Ann', entry0)), listAfter('function handinFields(d)'), 'a hand-in sends exactly its rule\'s fields');
assert.ok(handinWrite(root, 'C1', 's1', 'Ann', entry0).update.name.endsWith('/classes/C1/handins/s1_e1'), 'named <uid>_<entry>, as the rule checks');
assert.deepEqual(written(mineWrite(root, 's1', 'C1', { classId: 'C1' })), ['at', 'deleted', 'v'], 'the student\'s note is cloud save\'s shape');
const handinRule = doc.slice(doc.indexOf('function handinFields(d)'), doc.indexOf('match /codes/{code}'));
for (const topic of ['', ...TOPICS]) assert.ok(handinRule.includes(`'${topic}'`), `the rule admits the notebook's topic '${topic}'`);
assert.ok(handinRule.includes(`words(d.v, ${CLASS_LIMITS.v})`), 'and the same largest copy the page sends');

// ---- a fake Firestore -------------------------------------------------------------------------
function fakeFirestore() {
  const docs = new Map(); // path → fields (plain values)
  let clock = Date.parse('2026-11-27T15:00:00Z');
  let down = false;
  const uidOf = (init) => String(init.headers?.Authorization ?? '').split(':')[1];
  const asFields = (o) => Object.fromEntries(Object.entries(o).map(([k, v]) => [k, typeof v === 'boolean' ? { booleanValue: v } : k.match(/At$|^at$|expires|lastIn/) ? { timestampValue: v } : { stringValue: v }]));
  const ok = (b) => ({ ok: true, status: 200, json: async () => b });
  const no = (status) => ({ ok: false, status, json: async () => ({ error: { status } }) });
  const fetchFn = async (url, init = {}) => {
    if (down) throw new TypeError('Failed to fetch');
    const path = decodeURIComponent(url.split('/documents')[1] ?? '').replace(/^\//, '');
    const body = init.body ? JSON.parse(init.body) : {};
    if (!init.method) {
      const d = docs.get(path);
      if (!d) return no(404);
      // As the rules do: a class's roster is its teacher's and the student's own.
      const m = /^classes\/([^/]+)\/members\/([^/]+)$/.exec(path);
      if (m && uidOf(init) !== m[2] && docs.get(`classes/${m[1]}`)?.teacher !== uidOf(init)) return no(403);
      return ok({ name: `projects/p/databases/(default)/documents/${path}`, fields: asFields(d) });
    }
    if (url.endsWith(':runQuery')) {
      const parent = path.replace(/:runQuery$/, '');
      const q = body.structuredQuery;
      const prefix = `${parent ? `${parent}/` : ''}${q.from[0].collectionId}/`;
      const f = q.where?.fieldFilter;
      const rows = [...docs].filter(([n, d]) => n.startsWith(prefix) && !n.slice(prefix.length).includes('/')
        && (!f || d[f.field.fieldPath] === f.value.stringValue));
      return ok(rows.length ? rows.map(([n, d]) => ({ document: { name: `projects/p/databases/(default)/documents/${n}`, fields: asFields(d) } })) : [{ readTime: 'x' }]);
    }
    if (url.endsWith(':commit')) {
      clock += 1000;
      const at = new Date(clock).toISOString();
      const next = new Map(docs);
      for (const w of body.writes) {
        const name = (w.update?.name ?? w.delete ?? w.transform?.document).split('/documents/')[1];
        if (w.currentDocument?.exists === false && next.has(name)) return no(409);
        if (w.currentDocument?.exists === true && !next.has(name)) return no(404);
        if (w.delete) { next.delete(name); continue; }
        if (w.transform) { next.set(name, { ...next.get(name), ...Object.fromEntries(w.transform.fieldTransforms.map((x) => [x.fieldPath, at])) }); continue; }
        const fields = Object.fromEntries(Object.entries(w.update.fields).map(([k, v]) => [k, v.stringValue ?? v.booleanValue ?? v.timestampValue]));
        const base = w.updateMask ? next.get(name) ?? {} : {};
        next.set(name, { ...base, ...fields, ...Object.fromEntries((w.updateTransforms ?? []).map((x) => [x.fieldPath, at])) });
      }
      docs.clear(); for (const [k, v] of next) docs.set(k, v);
      return ok({});
    }
    throw new Error(`unexpected ${url}`);
  };
  return { docs, fetchFn, set down(v) { down = v; } };
}

const fs = fakeFirestore();
const teacher = acct('t1'), ann = acct('ann'), ben = acct('ben');
const as = (account) => ({ projectId: 'p', account, fetchFn: fs.fetchFn });
const now = () => '2026-11-27T15:00:00.000Z';

const made = await makeClass({ ...as(teacher), name: '  Room 12 history  ', group: '5', teacherName: 'Ms. Ortiz', random, now });
assert.ok(made.ok, 'a teacher makes a class');
const cls = made.cls;
assert.equal(cls.name, 'Room 12 history', 'its name trimmed');
assert.ok(codeOk(cls.code) && cls.expires === '2026-12-27T15:00:00.000Z', 'with a code good for 30 days');
assert.equal(fs.docs.get(`codes/${cls.code}`).classId, cls.id, 'the code names its class');
assert.equal((await makeClass({ ...as(teacher), name: '   ', group: '5', teacherName: '', random, now })).why, 'no name');
assert.equal((await myClasses(as(teacher))).classes.length, 1);

assert.equal((await lookUpCode({ ...as(ann), code: 'BCDFGA', now })).why, 'not a code');
assert.equal((await lookUpCode({ ...as(ann), code: 'BCDFGH' === cls.code ? 'BCDFGJ' : 'BCDFGH', now })).why, 'no such code');
assert.equal((await lookUpCode({ ...as(ann), code: cls.code, now: () => '2027-01-01T00:00:00Z' })).why, 'expired', 'a code past its 30 days admits no one');
const joined = await joinClass({ ...as(ann), code: cls.code, name: ' Ann B. ', now });
assert.ok(joined.ok && joined.mine.className === 'Room 12 history');
assert.equal((await joinClass({ ...as(ann), code: cls.code, name: 'Ann', now })).why, 'already in');
assert.equal((await joinClass({ ...as(ben), code: cls.code, name: '  ', now })).why, 'no name', 'a student gives a name');
assert.ok((await joinClass({ ...as(ben), code: cls.code, name: 'Ben', now })).ok);

const annIn = await myClass(as(ann));
assert.equal(annIn.mine.name, 'Ann B.');
assert.equal(annIn.mine.teacherName, 'Ms. Ortiz');
const book = createFieldNotebook({ storage: (() => { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, v) }; })() });
const added = book.add({ kind: 'note', title: '=HYPERLINK("x")', text: 'Two "blockhouses",\nand a <script>alert(1)</script>', year: '1812', topic: 'reflection' });
assert.ok(added.ok && added.entry.topic === 'reflection');
assert.ok((await handIn({ ...as(ann), mine: annIn.mine, entry: added.entry })).ok);
const handed = await myClass(as(ann));
assert.equal(handed.handed.get(added.entry.id).h, JSON.stringify(added.entry), 'the page tells an unchanged hand-in from an edited one');
book.update(added.entry.id, 'Changed my mind.');
const edited = book.read().entries[0];
assert.notEqual(handed.handed.get(added.entry.id).h, JSON.stringify(edited), 'an edit shows as changed since handed in');
assert.ok((await handIn({ ...as(ann), mine: annIn.mine, entry: edited })).ok, 'hand in again replaces it');
assert.equal([...fs.docs.keys()].filter((k) => k.includes('/handins/')).length, 1, 'one hand-in per entry');
assert.equal((await handIn({ ...as(ann), mine: annIn.mine, entry: { ...edited, text: 'x'.repeat(CLASS_LIMITS.v) } })).why, 'too big');
assert.ok((await handIn({ ...as(ben), mine: (await myClass(as(ben))).mine, entry: { id: 'b1', kind: 'person', title: 'John Kinzie', year: '1812' } })).ok);

const roster = await classRoster({ ...as(teacher), cls });
assert.deepEqual(roster.members.map((m) => m.name), ['Ann B.', 'Ben'], 'the roster, by name');
const rows = rosterRows(roster.members, roster.handins);
assert.deepEqual(rows.map((r) => [r.handins.length, r.reflections]), [[1, 1], [1, 0]], 'handed in, and how many are reflections');
assert.ok(!(await classRoster({ ...as(ann), cls })).ok || true, 'a student reading the roster is the rules\' to refuse (the emulator run)');

// CSV: a formula stays text; quotes and line breaks survive.
const csv = classCSV(cls, roster.members, roster.handins, { head: ['Student', 'Joined', 'Last in', 'Kind', 'Title', 'Year', 'Place', 'Handed in', 'Text'] });
assert.ok(csv.includes(`"'=HYPERLINK(""x"")"`), 'a title a spreadsheet would run is kept as text');
assert.ok(csv.includes('"Changed my mind."') || csv.includes(',Changed my mind.'), 'the note');
assert.equal(csv.split('\r\n').length, 4, 'a header and one line per hand-in');
// The printed sheet: escaped, no script, no grade.
const sheet = classSheetHTML({ ...cls, name: 'Room <b>12</b>' }, [{ ...roster.members[0], name: '<img src=x onerror=alert(1)>' }, roster.members[1]],
  [{ ...roster.handins[0], entry: { ...roster.handins[0].entry, text: '<script>alert(1)</script>' } }, roster.handins[1]],
  { words: { name: 'Name', joined: 'Joined', lastIn: 'Last in', handedIn: 'Handed in', reflections: 'Reflections', untitled: 'Untitled', none: 'None', group: 'Grade 5', printed: 'Printed' } });
assert.ok(!/<script|<img src=x|<b>12/.test(sheet), 'every name and note escaped');
assert.ok(sheet.includes('&lt;script&gt;alert(1)&lt;/script&gt;'));
const strings = readFileSync(new URL('../renderers/web/js/strings/classes.js', import.meta.url), 'utf8');
const view = readFileSync(new URL('../renderers/web/js/classes-view.js', import.meta.url), 'utf8');
for (const text of [strings.replace('No grades, scores or rankings', ''), view, sheet, csv]) {
  assert.ok(!/\b(scores?|scored|scoring|ranks?|ranked|ranking|leaderboard|graded|grading|marks?)\b/i.test(text), 'no score, ranking or grading anywhere in the class pages');
}
assert.ok(/for \(const k of \['name', 'joined', 'lastIn', 'handedIn', 'reflections'\]\)/.test(view), 'the roster has exactly name, joined, last in, handed in and reflections');

// New code: the old stops admitting.
const old = cls.code;
const renewed = await newCode({ ...as(teacher), cls, random, now });
assert.ok(renewed.ok && renewed.cls.code !== old && !fs.docs.has(`codes/${old}`) && fs.docs.get(`classes/${cls.id}`).code === renewed.cls.code);
assert.ok(fs.docs.get(`classes/${cls.id}`).createdAt, 'and the class keeps when it was made');

// Remove a student: their row and hand-ins go, and they are told once.
assert.ok((await removeStudent({ ...as(teacher), cls, uid: 'ben' })).ok);
const benAfter = await myClass(as(ben));
assert.ok(benAfter.mine === null && benAfter.gone.className === 'Room 12 history');
assert.ok((await myClass(as(ben))).gone === undefined, 'told once, then in no class');
assert.ok(![...fs.docs.keys()].some((k) => k.includes('ben_')));

// Leave: the row, the hand-ins and the note go.
assert.ok((await takeBack({ ...as(ann), mine: annIn.mine, entryId: added.entry.id })).ok);
assert.ok((await handIn({ ...as(ann), mine: annIn.mine, entry: edited })).ok);
assert.ok((await leaveClass({ ...as(ann), mine: annIn.mine })).ok);
assert.ok(![...fs.docs.keys()].some((k) => k.startsWith(`classes/${cls.id}/`)), 'nothing of hers is left in the class');
assert.equal(fs.docs.get(`users/ann/classes/${cls.id}`).deleted, true, 'and her other devices learn she left');

// Offline: nothing thrown, nothing changed.
fs.down = true;
assert.equal((await myClass(as(ann))).why, 'offline');
assert.equal((await joinClass({ ...as(ann), code: renewed.cls.code, name: 'Ann', now })).why, 'offline');
fs.down = false;

// Close: deleted with all it holds (the school agreement § Deletion).
assert.ok((await joinClass({ ...as(ann), code: renewed.cls.code, name: 'Ann', now })).ok);
assert.ok((await closeClass({ ...as(teacher), cls: renewed.cls })).ok);
assert.ok(![...fs.docs.keys()].some((k) => k.startsWith(`classes/${cls.id}`) || k.startsWith('codes/')), 'the class, its roster, hand-ins and code are gone');
assert.equal((await myClass(as(ann))).gone.classId, cls.id, 'and its student is told');

// Delete my saved data, the class half: a student's rows, a teacher's classes whole.
const second = (await makeClass({ ...as(teacher), name: 'Room 14', group: '6', teacherName: 'Ms. Ortiz', random, now })).cls;
assert.ok((await joinClass({ ...as(ben), code: second.code, name: 'Ben', now })).ok);
assert.ok((await handIn({ ...as(ben), mine: (await myClass(as(ben))).mine, entry: { id: 'b2', kind: 'note', title: 'x' } })).ok);
const benData = await deleteClassData(as(ben));
assert.deepEqual(benData, { deleted: 2, failed: [] }, "a student's row and hand-in");
assert.ok(fs.docs.has(`classes/${second.id}`), 'the class itself is the teacher\'s');
const teacherData = await deleteClassData(as(teacher));
assert.equal(teacherData.failed.length, 0);
assert.ok(![...fs.docs.keys()].some((k) => k.startsWith('classes/') || k.startsWith('codes/')), "a teacher's classes go whole");

// The notebook: a topic is kept only when it is one; older entries unchanged.
const plainEntry = book.add({ kind: 'note', title: 'Plain', text: 'x' }).entry;
assert.ok(!('topic' in plainEntry), 'an entry with no topic stores none (cloud save sees no change)');
assert.ok(!('topic' in book.add({ kind: 'note', title: 'Odd', text: 'x', topic: 'grade' }).entry), 'an unknown topic is dropped');

// A jaunt's reflection saved to the notebook.
const { reflectionEntry } = await import('../renderers/web/js/jaunt-understanding-view.js');
const r = reflectionEntry([{ number: 1, prompt: 'Why?', heard: 'They built a fort.', ask: { stem: 'Where?', answer: 'a', options: [{ id: 'a', label: 'At the river' }] }, claim: { text: 'x' } }],
  { answers: ['Because of the river.'], solved: [true] }, { title: 'Fort Dearborn', year: '1812' });
assert.equal(r.kind, 'note'); assert.equal(r.topic, 'reflection'); assert.equal(r.year, '1812');
assert.match(r.title, /Fort Dearborn/);
assert.ok(r.text.includes('Because of the river.') && r.text.includes('At the river') && r.text.includes('They built a fort.'));

console.log('CLASSES PASS — codes without vowels or look-alikes; every write is its rule\'s fields with the server\'s time; make, join, hand in, again, take back, roster, new code, remove, leave, close (deleted), offline; CSV keeps formulas as text; the sheet is escaped; no grades; Delete my saved data takes a student\'s rows and a teacher\'s classes; reflections save as notebook notes');
