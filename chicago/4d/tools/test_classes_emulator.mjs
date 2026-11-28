/**
 * test_classes_emulator.mjs — T-3778's rules, run for real against the Firestore emulator.
 *
 * NOT a gate step: the gate has no Java and installs nothing. tools/test_classes.mjs holds
 * the same writes to the rules' text in the gate; this drives renderers/web/js/classes.js,
 * cloud save's users tree and Delete my saved data through Firebase's own rules engine, as
 * a teacher, two students, a stranger and an email-only sign-in. Run it when the rules in
 * docs/SIGN-IN.md change:
 *
 *   npm i --prefix /tmp/fb firebase-tools                       # once (needs Java 11+)
 *   node tools/publish_firestore_rules.mjs --dry-run | sed '$d' \
 *     | sed "s/'OWNER_EMAIL'/'owner@example.com'/" > /tmp/fb/firestore.rules
 *   echo '{"firestore":{"rules":"firestore.rules"},"emulators":{"firestore":{"port":8080},"ui":{"enabled":false}}}' > /tmp/fb/firebase.json
 *   (cd /tmp/fb && npx firebase emulators:exec --only firestore --project demo-test \
 *     "node $PWD/tools/test_classes_emulator.mjs")
 */
import assert from 'node:assert/strict';
import {
  makeClass, myClasses, classRoster, newCode, closeClass, removeStudent,
  lookUpCode, joinClass, myClass, leaveClass, handIn, takeBack, deleteClassData,
} from '../renderers/web/js/classes.js';
import { deleteMyData } from '../renderers/web/js/student-data.js';
import { syncOnce } from '../renderers/web/js/cloud-save.js';
import { NOTEBOOK_KEY } from '../renderers/web/js/field-notebook.js';

const HOST = process.env.FIRESTORE_EMULATOR_HOST || '127.0.0.1:8080';
const PROJECT = 'demo-test';
const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
const tokenFor = (uid, provider = 'google.com') => `${b64({ alg: 'none', typ: 'JWT' })}.${b64({
  iss: `https://securetoken.google.com/${PROJECT}`, aud: PROJECT, sub: uid, user_id: uid,
  iat: Math.floor(Date.now() / 1000), exp: Math.floor(Date.now() / 1000) + 3600, auth_time: Math.floor(Date.now() / 1000),
  firebase: { sign_in_provider: provider, identities: {} },
})}.`;
const fetchFn = (url, init) => fetch(String(url).replace('https://firestore.googleapis.com', `http://${HOST}`), init);
const who = (uid, provider) => ({ uid, method: provider === 'anonymous' ? 'email' : 'google', idToken: async () => tokenFor(uid, provider) });
const as = (account) => ({ projectId: PROJECT, account, fetchFn });

const teacher = who('teach1'), ann = who('ann1'), ben = who('ben1'), stranger = who('str1'), anon = who('anon1', 'anonymous');
await fetch(`http://${HOST}/emulator/v1/projects/${PROJECT}/databases/(default)/documents`, { method: 'DELETE' });

let passed = 0;
const ok = (cond, what) => { assert.ok(cond, what); passed++; };

// A teacher makes a class; the email-only sign-in cannot.
const made = await makeClass({ ...as(teacher), name: 'Room 12 history', group: '5', teacherName: 'Ms. Ortiz' });
ok(made.ok, `a teacher makes a class (${made.why ?? ''})`);
const cls = made.cls;
ok((await makeClass({ ...as(anon), name: 'x', group: '5', teacherName: 'x' })).ok === false, 'an email-only sign-in cannot make a class');
const mine = await myClasses(as(teacher));
ok(mine.ok && mine.classes.length === 1 && mine.classes[0].code === cls.code && mine.classes[0].expires, 'the teacher lists their class, with its code and expiry');
ok((await myClasses(as(stranger))).classes?.length === 0, 'another account lists none of it');

// The code: a stranger can look it up by name; the email-only sign-in cannot.
ok((await lookUpCode({ ...as(ann), code: cls.code })).ok, 'a student looks the code up');
ok(!(await lookUpCode({ ...as(anon), code: cls.code })).ok, 'an email-only sign-in cannot');
ok((await lookUpCode({ ...as(ann), code: 'BCDFGH' })).why === 'no such code', 'a wrong code is no such code');
const listCodes = await fetchFn(`https://firestore.googleapis.com/v1/projects/${PROJECT}/databases/(default)/documents:runQuery`, {
  method: 'POST', headers: { Authorization: `Bearer ${tokenFor('ann1')}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ structuredQuery: { from: [{ collectionId: 'codes' }] } }),
});
ok(listCodes.status === 403, 'no one can list the codes');

// Students join.
ok((await joinClass({ ...as(ann), code: cls.code, name: 'Ann B.' })).ok, 'a student joins with the code');
ok((await joinClass({ ...as(ben), code: cls.code, name: 'Ben C.' })).ok, 'a second student joins');
ok(!(await joinClass({ ...as(anon), code: cls.code, name: 'Anon' })).ok, 'an email-only sign-in cannot join');
const annIn = await myClass(as(ann));
ok(annIn.ok && annIn.mine?.classId === cls.id && annIn.mine.className === 'Room 12 history' && !annIn.mine.closed, 'the student finds their class on another visit');

// A forged member row: a code for another class, or no code, is refused.
const other = (await makeClass({ ...as(stranger), name: 'Other', group: '7', teacherName: 'Mr. X' })).cls;
const forge = await fetchFn(`https://firestore.googleapis.com/v1/projects/${PROJECT}/databases/(default)/documents:commit`, {
  method: 'POST', headers: { Authorization: `Bearer ${tokenFor('ben1')}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ writes: [{ update: { name: `projects/${PROJECT}/databases/(default)/documents/classes/${other.id}/members/ben1`,
    fields: { uid: { stringValue: 'ben1' }, name: { stringValue: 'Ben' }, code: { stringValue: cls.code } } },
    updateTransforms: [{ fieldPath: 'joinedAt', setToServerValue: 'REQUEST_TIME' }, { fieldPath: 'lastIn', setToServerValue: 'REQUEST_TIME' }] }] }),
});
ok(forge.status === 403, 'a code for one class does not admit to another');

// Hand-ins: the student's choice, read by the teacher and that student only.
const entry = { id: 'e1', kind: 'note', title: 'The fort', text: 'Two blockhouses.', year: '1812', place: 'Fort Dearborn', topic: 'reflection' };
ok((await handIn({ ...as(ann), mine: annIn.mine, entry })).ok, 'a student hands an entry in');
ok((await handIn({ ...as(ben), mine: { ...annIn.mine, name: 'Ben C.' }, entry: { ...entry, id: 'b1' } })).ok, 'so does the second');
const roster = await classRoster({ ...as(teacher), cls });
ok(roster.ok && roster.members.length === 2 && roster.handins.length === 2 && roster.handins.some((h) => h.entry?.text === 'Two blockhouses.'),
  'the teacher reads the roster and both hand-ins');
ok(!(await classRoster({ ...as(ann), cls })).ok, 'a student cannot read the roster');
ok(!(await classRoster({ ...as(stranger), cls })).ok, 'nor can a stranger');
const annHanded = await myClass(as(ann));
ok(annHanded.handed.size === 1 && annHanded.handed.has('e1'), 'a student sees only their own hand-ins');
const allHandins = await fetchFn(`https://firestore.googleapis.com/v1/projects/${PROJECT}/databases/(default)/documents/classes/${cls.id}:runQuery`, {
  method: 'POST', headers: { Authorization: `Bearer ${tokenFor('ann1')}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ structuredQuery: { from: [{ collectionId: 'handins' }] } }),
});
ok(allHandins.status === 403, "a student cannot list the class's hand-ins");
const benRow = await fetchFn(`https://firestore.googleapis.com/v1/projects/${PROJECT}/databases/(default)/documents/classes/${cls.id}/members/ben1`, {
  headers: { Authorization: `Bearer ${tokenFor('ann1')}` },
});
ok(benRow.status === 403, "nor read a classmate's row");
const forgedHandin = await fetchFn(`https://firestore.googleapis.com/v1/projects/${PROJECT}/databases/(default)/documents:commit`, {
  method: 'POST', headers: { Authorization: `Bearer ${tokenFor('str1')}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ writes: [{ update: { name: `projects/${PROJECT}/databases/(default)/documents/classes/${cls.id}/handins/str1_x`,
    fields: { uid: { stringValue: 'str1' }, name: { stringValue: 'S' }, entryId: { stringValue: 'x' }, kind: { stringValue: 'note' },
      topic: { stringValue: '' }, title: { stringValue: 't' }, v: { stringValue: '{}' } } },
    updateTransforms: [{ fieldPath: 'at', setToServerValue: 'REQUEST_TIME' }] }] }),
});
ok(forgedHandin.status === 403, 'someone not in the class cannot hand in to it');
ok((await takeBack({ ...as(ann), mine: annIn.mine, entryId: 'e1' })).ok, 'a student takes a hand-in back');
ok((await handIn({ ...as(ann), mine: annIn.mine, entry })).ok, 'and hands it in again');

// A new code: the old one stops admitting.
const renewed = await newCode({ ...as(teacher), cls });
ok(renewed.ok && renewed.cls.code !== cls.code, 'the teacher makes a new code');
ok((await lookUpCode({ ...as(stranger), code: cls.code })).why === 'no such code', 'the old code no longer admits');
ok(!(await newCode({ ...as(ann), cls: renewed.cls })).ok, 'a student cannot change the code');

// Remove a student: their row and hand-ins go; on their next visit they are told.
const removed = await removeStudent({ ...as(teacher), cls: renewed.cls, uid: 'ben1' });
ok(removed.ok, `the teacher removes a student (${removed.why ?? ''} ${JSON.stringify(removed.body ?? '').slice(0, 300)})`);
const benAfter = await myClass(as(ben));
ok(benAfter.ok && benAfter.mine === null && benAfter.gone?.classId === cls.id, 'the removed student is told on their next visit');
ok((await classRoster({ ...as(teacher), cls })).handins.every((h) => h.uid !== 'ben1'), 'and their hand-ins are gone');

// A student leaves.
const third = who('cara1');
ok((await joinClass({ ...as(third), code: renewed.cls.code, name: 'Cara' })).ok, 'a third student joins with the new code');
const caraIn = await myClass(as(third));
ok((await handIn({ ...as(third), mine: caraIn.mine, entry: { ...entry, id: 'c1' } })).ok, 'and hands in');
ok((await leaveClass({ ...as(third), mine: caraIn.mine })).ok, 'a student leaves the class');
ok((await myClass(as(third))).mine === null, 'and is in no class');
ok((await classRoster({ ...as(teacher), cls })).members.every((m) => m.uid !== 'cara1'), 'the roster no longer lists them');

// T-3777's users tree, through the same engine: cloud save writes and reads it back.
const storageOf = (init = {}) => { const m = new Map(Object.entries(init)); return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) }; };
const book = JSON.stringify({ version: 1, entries: [{ id: 'n1', kind: 'note', title: 'Kinzie house', year: '1835', place: '', person: '', grade: '', text: 'Across the river.', excerpt: '', sources: [], photo: '', link: '', createdAt: '2026-11-27T15:00:00Z' }] });
const first = await syncOnce({ ...as(ann), storage: storageOf({ [NOTEBOOK_KEY]: book }) });
ok(first.ok && first.pushed >= 1, `cloud save writes a student's notebook (${first.why ?? ''})`);
const second = storageOf();
const back = await syncOnce({ ...as(ann), storage: second });
ok(back.ok && JSON.parse(second.getItem(NOTEBOOK_KEY)).entries[0]?.text === 'Across the river.', 'and another browser of theirs reads it back');
ok((await syncOnce({ ...as(anon), storage: storageOf({ [NOTEBOOK_KEY]: book }) })).ok === false, 'an email-only sign-in cannot write it');

// Delete my saved data: a student's row and hand-ins leave the class.
const annGone = await deleteMyData(as(ann));
ok(annGone.failed.length === 0, `a student's Delete my saved data refuses nothing (${annGone.failed})`);
ok((await classRoster({ ...as(teacher), cls })).members.length === 0, "the student's row and hand-ins left the class");

// Close: the class and all it holds are deleted (the school agreement); its students are told.
const dan = who('dan1');
ok((await joinClass({ ...as(dan), code: renewed.cls.code, name: 'Dan' })).ok, 'a student joins before the class closes');
ok((await closeClass({ ...as(teacher), cls: renewed.cls })).ok, 'the teacher closes the class');
ok((await myClasses(as(teacher))).classes.length === 0, 'it is gone from their classes');
ok((await lookUpCode({ ...as(stranger), code: renewed.cls.code })).why === 'no such code', 'its code admits no one');
const danAfter = await myClass(as(dan));
ok(danAfter.mine === null && danAfter.gone?.classId === cls.id, 'its student is told on their next visit');
ok(!(await closeClass({ ...as(ann), cls: other })).ok, 'a student cannot close a class');

// A teacher's Delete my saved data takes their classes with it.
const teachGone = await deleteMyData(as(stranger));
ok(teachGone.failed.length === 0, `a teacher's Delete my saved data refuses nothing (${teachGone.failed})`);
ok((await myClasses(as(stranger))).classes.length === 0, 'and their classes are gone');

console.log(`test_classes_emulator: ${passed} checks passed against the Firestore emulator`);
