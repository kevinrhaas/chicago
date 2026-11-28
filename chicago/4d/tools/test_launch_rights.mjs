/**
 * test_launch_rights.mjs — T-3797, launch access by sign-in address (renderers/web/js/launch-rights.js).
 *
 * In the gate, without a network or Java. It holds:
 *   - addresses folded to lower case, rights kept to cloud and admin, in that order;
 *   - the grant write against docs/SIGN-IN.md's accessFields list, its time the server's;
 *   - the rules' text: only the owner grants or takes away admin, a player reads only their
 *     own row, no access keys anywhere (the owner chose rights by email only, 2026-11-27);
 *   - a whole run against a fake Firestore: an admin adds and changes people, a player reads
 *     their own rights, an email-only sign-in has none, cloud play waits until launch/cloud opens;
 *   - the waitlist: a player without cloud play joins (twice is once), only admins list it,
 *     letting someone in grants cloud play and removes their row in one commit;
 *   - the launch page's panel module names only what the data module exports.
 * The rules run in Firebase's own engine in tools/test_launch_rights_emulator.mjs (not a gate
 * step: it needs Java and the emulator).
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import * as rightsMod from '../renderers/web/js/launch-rights.js';

const { RIGHTS, emailId, emailOk, cleanRights, grantWrite, waitlistWrite, myRights, cloudState, listPeople, grant, revoke, joinWaitlist, listWaitlist, letIn, leaveWaitlist } = rightsMod;

assert.deepEqual(RIGHTS, ['cloud', 'admin']);
assert.equal(emailId('  Kid.Name@School.ORG '), 'kid.name@school.org');
assert.ok(emailOk('a@b.co') && !emailOk('a@b') && !emailOk('a/b@c.d') && !emailOk(''));
assert.deepEqual(cleanRights(['admin', 'x', 'cloud', 'cloud']), ['cloud', 'admin'], 'only known rights, once each, in order');

// ---- the rules' text ----------------------------------------------------------------------
const doc = readFileSync(new URL('../docs/SIGN-IN.md', import.meta.url), 'utf8');
const rules = doc.slice(doc.indexOf('// T-3797: launch access'), doc.indexOf('match /launch/{doc}') + 600);
const listAfter = (text, marker) => {
  const m = /hasOnly\(\[([^\]]*)\]\)/.exec(text.slice(text.indexOf(marker)));
  return m[1].match(/'([^']+)'/g).map((s) => s.slice(1, -1)).sort();
};
const w = grantWrite('projects/p/databases/(default)/documents', { email: 'Ann@X.org', rights: ['admin', 'cloud'], note: 'tester', by: 'o@x.org' });
const sent = [...Object.keys(w.update.fields), ...w.updateTransforms.map((t) => t.fieldPath)].sort();
assert.deepEqual(sent, listAfter(rules, 'function accessFields(d, email)'), 'a grant sends exactly its rule\'s fields');
assert.ok(w.update.name.endsWith('/access/ann@x.org'), 'named by the address in lower case, as the rule checks');
assert.deepEqual(w.update.fields.rights, { arrayValue: { values: [{ stringValue: 'cloud' }, { stringValue: 'admin' }] } });
assert.deepEqual(w.updateTransforms, [{ fieldPath: 'at', setToServerValue: 'REQUEST_TIME' }], 'the time is the server\'s');
const ww = waitlistWrite('r', { email: 'Ann@X.org', name: 'Ann', year: '1904', check: 'Playable at Light detail' });
assert.deepEqual([...Object.keys(ww.update.fields), 'at'].sort(), listAfter(rules, 'match /waitlist/{email}'), 'a waitlist row sends exactly its rule\'s fields');
assert.deepEqual(ww.currentDocument, { exists: false }, 'and is made new, never over another');
assert.ok(/d\.rights\.hasOnly\(\['cloud', 'admin'\]\)/.test(rules), 'the rules admit cloud and admin only');
assert.ok(/allow list: if isAdmin\(\);/.test(rules), 'only an admin lists people');
assert.ok(/allow get: if \(verified\(\) && myEmail\(\) == email\) \|\| isAdmin\(\);/.test(rules), 'a player reads their own row only');
assert.equal((rules.match(/isOwner\(\) \|\| /g) || []).length, 3, 'admin is given, changed and taken away by the owner only');
assert.ok(/email_verified == true/.test(rules), 'a typed address is never enough');
assert.ok(!/match \/keys\//.test(doc) && !/redeem/i.test(rules), 'no access keys (rights by email only)');
assert.ok(!/@/.test(rules.replace(/OWNER_EMAIL/g, '')), 'no address in the rules but the owner placeholder');

// ---- a fake Firestore -------------------------------------------------------------------------
const OWNER = 'owner@example.org';
function fakeFirestore() {
  const docs = new Map();
  const who = (init) => JSON.parse(String(init.headers?.Authorization ?? '').slice(7));
  const isAdmin = (u) => u.verified && u.provider !== 'anonymous' && (u.email === OWNER || docs.get(`access/${u.email}`)?.rights?.includes('admin'));
  const fields = (d) => Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? { arrayValue: { values: v.map((s) => ({ stringValue: s })) } }
    : typeof v === 'boolean' ? { booleanValue: v } : k === 'at' ? { timestampValue: v } : { stringValue: v }]));
  const res = (status, body = {}) => ({ ok: status < 300, status, json: async () => body });
  const fetchFn = async (url, init = {}) => {
    const u = who(init);
    const path = decodeURIComponent(url.split('/documents')[1] ?? '').replace(/^\//, '');
    if (!init.method) {
      if (/^(access|waitlist)\//.test(path) && path.split('/')[1] !== u.email && !isAdmin(u)) return res(403);
      const d = docs.get(path);
      return d ? res(200, { name: `x/documents/${path}`, fields: fields(d) }) : res(404);
    }
    const body = JSON.parse(init.body);
    if (url.endsWith(':runQuery')) {
      if (!isAdmin(u)) return res(403);
      const col = body.structuredQuery.from[0].collectionId;
      const rows = [...docs].filter(([n]) => n.startsWith(`${col}/`)).slice(0, body.structuredQuery.limit);
      return res(200, rows.length ? rows.map(([n, d]) => ({ document: { name: `x/documents/${n}`, fields: fields(d) } })) : [{ readTime: 'x' }]);
    }
    for (const wr of body.writes) {
      const name = (wr.update?.name ?? wr.delete).split('/documents/')[1];
      const own = name === `waitlist/${u.email}` && u.verified && u.provider !== 'anonymous';
      if (!isAdmin(u) && !own) return res(403);
      if (wr.currentDocument?.exists === false && docs.has(name)) return res(409);
      const before = docs.get(name);
      const after = wr.update ? Object.fromEntries(Object.entries(wr.update.fields).map(([k, v]) => [k, v.arrayValue ? v.arrayValue.values.map((x) => x.stringValue) : v.stringValue ?? v.booleanValue])) : null;
      if (u.email !== OWNER && (before?.rights?.includes('admin') || after?.rights?.includes('admin'))) return res(403);
      if (after) docs.set(name, { ...after, at: '2026-11-27T17:00:00Z' }); else docs.delete(name);
    }
    return res(200, {});
  };
  return { docs, fetchFn };
}
const fs = fakeFirestore();
const acct = (email, { method = 'google', verified = true } = {}) => ({ uid: email, email, method, name: '',
  idToken: async () => JSON.stringify({ email: emailId(email), verified, provider: method === 'email' ? 'anonymous' : 'google.com' }) });
const as = (a) => ({ projectId: 'p', account: a, fetchFn: fs.fetchFn });
const owner = acct('Owner@Example.org'), ann = acct('ann@school.org'), ben = acct('ben@school.org'), typed = acct('carl@school.org', { method: 'email' });

let r = await myRights(as(owner));
assert.deepEqual([r.rights, r.admin], [['cloud', 'admin'], true], 'the owner is an admin by his sign-in, and may start the cloud');
r = await myRights(as(ann));
assert.deepEqual([r.rights, r.admin], [[], false], 'a stranger has no rights');
assert.ok((await grant({ ...as(owner), email: 'Ann@School.org ', rights: ['cloud'], note: 'tester' })).ok, 'the owner pre-assigns cloud play by email');
assert.deepEqual((await myRights(as(ann))).rights, ['cloud'], 'and it is waiting for her first sign-in');
assert.equal((await grant({ ...as(owner), email: 'not an email', rights: ['cloud'] })).why, 'not an email');
assert.ok((await grant({ ...as(owner), email: 'ben@school.org', rights: ['cloud', 'admin'] })).ok, 'the owner makes an admin');
assert.deepEqual((await myRights(as(ben))).admin, true);
assert.ok((await grant({ ...as(ben), email: 'dee@school.org', rights: ['cloud'] })).ok, 'an admin adds people');
assert.equal((await grant({ ...as(ben), email: 'eve@school.org', rights: ['admin'] })).why, 'refused', 'but cannot make an admin');
assert.equal((await revoke({ ...as(ann), email: 'dee@school.org' })).why, 'refused', 'a player cannot change anyone');
const people = await listPeople(as(owner));
assert.deepEqual(people.people.map((p) => `${p.email}:${p.rights.join('+')}`), ['ann@school.org:cloud', 'ben@school.org:cloud+admin', 'dee@school.org:cloud']);
assert.equal(people.people[0].note, 'tester');
assert.equal((await listPeople(as(ann))).why, 'refused', 'a player cannot list people');
assert.ok((await revoke({ ...as(owner), email: 'ann@school.org' })).ok);
assert.deepEqual((await myRights(as(ann))).rights, [], 'a revoked player has none');
assert.ok(!fs.docs.has('access/ann@school.org'), 'revoking removes the row');
assert.deepEqual((await myRights(as(typed))).rights, [], 'an email-only sign-in never has rights, even if granted');
assert.equal((await cloudState(as(ann))).ready, false, 'cloud play waits until launch/cloud opens');
fs.docs.set('launch/cloud', { ready: true, note: '', by: OWNER });
assert.equal((await cloudState(as(ann))).ready, true);

// ---- the waitlist ---------------------------------------------------------------------------
const eve = acct('eve@school.org');
assert.equal((await myRights(as(eve))).waiting, false);
assert.ok((await joinWaitlist({ ...as(eve), year: '1904', check: 'Playable at Light detail' })).ok, 'a player joins the waitlist');
assert.ok((await joinWaitlist({ ...as(eve), year: '1835' })).already, 'joining twice is once');
assert.equal((await myRights(as(eve))).waiting, true, 'and the page knows she is waiting');
assert.equal((await joinWaitlist(as(typed))).why, 'sign in', 'an email-only sign-in cannot join');
assert.equal((await listWaitlist(as(eve))).why, 'refused', 'a player cannot list the waitlist');
const wl = await listWaitlist(as(owner));
assert.deepEqual(wl.waiting.map((x) => `${x.email}:${x.year}:${x.check}`), ['eve@school.org:1904:Playable at Light detail']);
assert.ok((await letIn({ ...as(owner), email: 'eve@school.org' })).ok, 'the owner lets her in');
assert.deepEqual((await myRights(as(eve))).rights, ['cloud'], 'she has cloud play');
assert.equal((await myRights(as(eve))).waiting, false);
assert.equal((await listWaitlist(as(owner))).waiting.length, 0, 'and is off the waitlist, in the same commit');
assert.equal(fs.docs.get('access/eve@school.org').note, 'from the waitlist');
const fay = acct('fay@school.org');
await joinWaitlist(as(fay));
assert.ok((await leaveWaitlist({ ...as(owner), email: 'fay@school.org' })).ok && !fs.docs.has('waitlist/fay@school.org'), 'an admin removes someone from it');

// ---- the panel module ------------------------------------------------------------------------
const panel = readFileSync(new URL('../renderers/web/portal/launch-access.js', import.meta.url), 'utf8');
const named = /import \{([^}]*)\} from '\.\.\/js\/launch-rights\.js'/.exec(panel)[1].split(',').map((s) => s.trim().split(' as ')[0]);
for (const n of named) assert.ok(n in rightsMod, `launch-access.js imports ${n}, which launch-rights.js exports`);
for (const n of ['myRights', 'joinWaitlist', 'startCloud', 'mountAdmin', 'refreshAdmin']) assert.ok(new RegExp(`export (async )?function ${n}\\(`).test(panel), `the panel exports ${n}, which launch.js calls`);
assert.ok(!/innerHTML/.test(panel), 'the panel writes text, never markup, so an address cannot inject any');
console.log('PASS launch rights: addresses, the grant against its rule, owner-only admin, no keys, a whole run on a fake Firestore, the waitlist, the panel\'s imports');
