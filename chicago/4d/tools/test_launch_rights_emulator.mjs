/**
 * test_launch_rights_emulator.mjs — T-3797's rules, run for real against the Firestore emulator.
 *
 * NOT a gate step: the gate has no Java and installs nothing. tools/test_launch_rights.mjs holds
 * the writes to the rules' text in the gate; this drives renderers/web/js/launch-rights.js
 * through Firebase's own rules engine as the owner, an admin he made, two players, an
 * unverified address and an email-only sign-in. Run it when the rules in docs/SIGN-IN.md change
 * (set up as tools/test_classes_emulator.mjs says, with the owner placeholder replaced by
 * owner@example.com):
 *
 *   (cd /tmp/fb && npx firebase emulators:exec --only firestore --project demo-test \
 *     "node $PWD/tools/test_launch_rights_emulator.mjs")
 */
import assert from 'node:assert/strict';
import { deleteMyData } from '../renderers/web/js/student-data.js';
import { myRights, cloudState, setCloudState, listPeople, grant, revoke, joinWaitlist, listWaitlist, letIn, leaveWaitlist } from '../renderers/web/js/launch-rights.js';

const HOST = process.env.FIRESTORE_EMULATOR_HOST || '127.0.0.1:8080';
const PROJECT = 'demo-test';
const OWNER = 'owner@example.com';
const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
const tokenFor = (uid, email, { provider = 'google.com', verified = true } = {}) => `${b64({ alg: 'none', typ: 'JWT' })}.${b64({
  iss: `https://securetoken.google.com/${PROJECT}`, aud: PROJECT, sub: uid, user_id: uid,
  iat: Math.floor(Date.now() / 1000), exp: Math.floor(Date.now() / 1000) + 3600, auth_time: Math.floor(Date.now() / 1000),
  ...(email ? { email, email_verified: verified } : {}),
  firebase: { sign_in_provider: provider, identities: {} },
})}.`;
const fetchFn = (url, init) => fetch(String(url).replace('https://firestore.googleapis.com', `http://${HOST}`), init);
const who = (uid, email, opts = {}) => ({ uid, email, method: opts.provider === 'anonymous' ? 'email' : 'google', idToken: async () => tokenFor(uid, email, opts) });
const as = (account) => ({ projectId: PROJECT, account, fetchFn });
// The raw commit, for what the module itself never sends (an email-only sign-in, a forged field).
const commitAs = (account, writes) => account.idToken().then((t) => fetchFn(`https://firestore.googleapis.com/v1/projects/${PROJECT}/databases/(default)/documents:commit`, {
  method: 'POST', headers: { Authorization: `Bearer ${t}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ writes }) }));
const root = `projects/${PROJECT}/databases/(default)/documents`;

await fetch(`http://${HOST}/emulator/v1/projects/${PROJECT}/databases/(default)/documents`, { method: 'DELETE' });
const owner = who('own1', 'owner@example.com'), ann = who('ann1', 'ann@school.org'), ben = who('ben1', 'ben@school.org');
const unverified = who('unv1', 'cat@school.org', { verified: false });
const anon = who('anon1', '', { provider: 'anonymous' });

let passed = 0;
const ok = (cond, what) => { assert.ok(cond, what); passed++; };

let r = await myRights(as(owner));
ok(r.admin && r.rights.includes('cloud'), `the owner is an admin by his sign-in (${JSON.stringify(r)})`);
ok(!(await myRights(as(ann))).admin, 'a stranger is not');
ok((await grant({ ...as(owner), email: 'Ann@School.org', rights: ['cloud'], note: 'tester' })).ok, 'the owner pre-assigns cloud play by email');
r = await myRights(as(ann));
ok(r.rights.join() === 'cloud' && !r.admin, `the player reads her own rights (${r.rights})`);
ok((await listPeople(as(ann))).why === 'refused', 'a player cannot list people');
ok((await grant({ ...as(ann), email: 'ann@school.org', rights: ['cloud', 'admin'] })).why === 'refused', 'nor raise her own rights');
ok((await grant({ ...as(owner), email: 'ben@school.org', rights: ['cloud', 'admin'] })).ok, 'the owner makes an admin');
ok((await myRights(as(ben))).admin, 'who is an admin by that grant');
ok((await grant({ ...as(ben), email: 'dee@school.org', rights: ['cloud'] })).ok, 'an admin adds a player');
ok((await grant({ ...as(ben), email: 'eve@school.org', rights: ['admin'] })).why === 'refused', 'an admin cannot make an admin');
ok((await grant({ ...as(ben), email: 'ben@school.org', rights: ['cloud'] })).why === 'refused', 'nor take admin away, even his own');
ok((await grant({ ...as(ben), email: 'ann@school.org', rights: ['cloud'], note: 'room 12' })).ok, 'an admin changes a player');
const people = await listPeople(as(ben));
ok(people.ok && people.people.map((p) => p.email).join() === 'ann@school.org,ben@school.org,dee@school.org', `an admin lists people (${people.people?.map((p) => p.email)})`);
ok(people.people[0].note === 'room 12' && people.people[0].by === 'ben@school.org' && people.people[0].at, 'with the note, who and when');
ok((await myRights(as(unverified))).rights.length === 0, 'an unverified address reads nothing');
ok((await grant({ ...as(unverified), email: 'cat@school.org', rights: ['cloud'] })).why === 'refused', 'and writes nothing');
let raw = await commitAs(anon, [{ update: { name: `${root}/access/x@y.org`, fields: { email: { stringValue: 'x@y.org' }, rights: { arrayValue: { values: [{ stringValue: 'cloud' }] } }, note: { stringValue: '' }, by: { stringValue: '' } } }, updateTransforms: [{ fieldPath: 'at', setToServerValue: 'REQUEST_TIME' }] }]);
ok(raw.status === 403, 'an email-only sign-in writes nothing');
raw = await commitAs(owner, [{ update: { name: `${root}/access/x@y.org`, fields: { email: { stringValue: 'x@y.org' }, rights: { arrayValue: { values: [{ stringValue: 'root' }] } }, note: { stringValue: '' }, by: { stringValue: '' } } }, updateTransforms: [{ fieldPath: 'at', setToServerValue: 'REQUEST_TIME' }] }]);
ok(raw.status === 403, 'not even the owner writes a right that does not exist');
raw = await commitAs(owner, [{ update: { name: `${root}/access/x@y.org`, fields: { email: { stringValue: 'someone@else.org' }, rights: { arrayValue: { values: [] } }, note: { stringValue: '' }, by: { stringValue: '' } } }, updateTransforms: [{ fieldPath: 'at', setToServerValue: 'REQUEST_TIME' }] }]);
ok(raw.status === 403, 'nor a row whose address is not its name');
ok((await revoke({ ...as(ann), email: 'ann@school.org' })).ok, 'a player may remove her own row');
ok((await revoke({ ...as(owner), email: 'ben@school.org' })).ok, 'the owner takes admin away');
ok(!(await myRights(as(ben))).admin, 'and it is gone');

ok((await grant({ ...as(owner), email: 'ann@school.org', rights: ['cloud'] })).ok, 'the owner gives it back');
const gone = await deleteMyData(as(ann));
ok(!gone.failed.includes('access') && (await myRights(as(ann))).rights.length === 0, `Delete my saved data takes her rights row too (${gone.failed})`);
// The waitlist.
const eve = who('eve1', 'eve@school.org');
ok((await joinWaitlist({ ...as(eve), year: '1904', check: 'Playable at Light detail' })).ok, 'a player joins the waitlist');
ok((await joinWaitlist({ ...as(eve), year: '1835' })).already, 'joining twice is once');
ok((await myRights(as(eve))).waiting === true, 'she reads her own row');
ok((await listWaitlist(as(eve))).why === 'refused', 'a player cannot list the waitlist');
ok((await joinWaitlist({ ...as(unverified) })).ok === false, 'an unverified address cannot join');
raw = await commitAs(ann, [{ update: { name: `${root}/waitlist/eve@school.org`, fields: { email: { stringValue: 'eve@school.org' }, name: { stringValue: '' }, year: { stringValue: '' }, check: { stringValue: '' } } }, updateTransforms: [{ fieldPath: 'at', setToServerValue: 'REQUEST_TIME' }] }]);
ok(raw.status === 403, 'nobody writes another person\'s row');
const wl = await listWaitlist(as(owner));
ok(wl.ok && wl.waiting.length === 1 && wl.waiting[0].year === '1904' && wl.waiting[0].at, 'the owner lists it, with the year and when');
ok((await letIn({ ...as(owner), email: 'eve@school.org' })).ok, 'and lets her in');
ok((await myRights(as(eve))).rights.join() === 'cloud' && !(await myRights(as(eve))).waiting, 'she has cloud play and is off the list, in one commit');
await joinWaitlist(as(who('fay1', 'fay@school.org')));
ok((await leaveWaitlist({ ...as(owner), email: 'fay@school.org' })).ok && (await listWaitlist(as(owner))).waiting.length === 0, 'an admin removes someone from it');
await joinWaitlist(as(ann));
const gone2 = await deleteMyData(as(ann));
ok(!gone2.failed.includes('waitlist') && !(await myRights(as(ann))).waiting, `Delete my saved data takes her waitlist row (${gone2.failed})`);

ok((await cloudState(as(ann))).ready === false, 'cloud play is closed until the owner opens it');
ok((await setCloudState({ ...as(ann), ready: true })).why === 'refused', 'a player cannot open it');
ok((await setCloudState({ ...as(owner), ready: true, note: 'trial' })).ok, 'the owner opens it');
ok((await cloudState(as(ann))).ready === true, 'and every signed-in player sees it open');
console.log(`PASS launch rights in the Firestore emulator: ${passed} checks (owner ${OWNER})`);
