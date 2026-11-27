#!/usr/bin/env node
// T-3576: the sign-in gate's policy, without a browser. When it asks, that it never
// locks anyone out, and that what it writes is exactly what docs/SIGN-IN.md's
// Firestore rules allow.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { configured, gateMode, validEmail, signInGate, offered, manualLabel, methodOf, AUTH_ERRORS, showAccount } from '../renderers/web/js/sign-in.js';
import { entryWrites, fromFields, deviceClass, autoId, MESSAGE_FIELDS } from '../renderers/web/js/visitor-store.js';
import { SIGN_IN } from '../renderers/web/js/sign-in-config.js';
import { ACCOUNT_DOCS, ACCOUNT_ROWS, ACCOUNT_TREES, ACCOUNT_CLASSES, ACCOUNT_BY_EMAIL, cloudFeaturesOn, deleteMyData, rowsQuery, showSavedData } from '../renderers/web/js/student-data.js';
import { rulesFromDoc, collectionsOf, ownerEmailOf } from './publish_firestore_rules.mjs';

const FULL = { apiKey: 'k', authDomain: 'p.firebaseapp.com', projectId: 'p', appId: 'a' };
const on = { enabled: true, hosts: ['chicago.polecat.live'], firebase: FULL };

// When it asks.
assert.equal(configured({}), false);
assert.equal(configured({ ...FULL, appId: ' ' }), false, 'a blank value is not configured');
assert.equal(configured(FULL), true);
assert.equal(gateMode({ config: on, hostname: 'chicago.polecat.live' }), 'on');
assert.equal(gateMode({ config: { ...on, enabled: false }, hostname: 'chicago.polecat.live' }), 'off', 'the flag off is off');
assert.equal(gateMode({ config: { ...on, firebase: { ...FULL, apiKey: '' } }, hostname: 'chicago.polecat.live' }), 'off', 'no keys is off');
assert.equal(gateMode({ config: on, hostname: 'localhost' }), 'off', 'a local serve is never gated');
assert.equal(gateMode({ config: on, hostname: 'chicago.polecat.live', webdriver: true }), 'robot', 'automation passes');
assert.equal(gateMode({ config: { ...on, enabled: false }, hostname: 'localhost', search: '?signin=preview' }), 'preview');
assert.equal(gateMode({ config: on, hostname: 'chicago.polecat.live', search: '?signin=preview' }), 'on', 'preview never weakens a live gate');

// The shipped config may be on or off, but on means complete.
if (SIGN_IN.enabled) assert.ok(configured(SIGN_IN.firebase), 'sign-in-config.js is enabled without all four Firebase values');
assert.ok(Array.isArray(SIGN_IN.hosts) && SIGN_IN.hosts.length, 'sign-in-config.js names its hosts');
if (SIGN_IN.enabled) assert.ok(SIGN_IN.hosts.includes('dev.chicago.polecat.live'), 'the dev preview is gated too, so the gate can be tried there before a promote');

// T-3580: the ways in, Google always first, and the grey link names the big buttons.
assert.deepEqual(offered({ providers: ['email', 'password', 'microsoft', 'google'] }), ['google', 'microsoft', 'password', 'email']);
assert.deepEqual(offered({ providers: ['google', 'facebook'] }), ['google'], 'an unknown provider is never drawn');
assert.deepEqual(offered({}), ['google', 'email'], 'no list is the first build: Google and the email alone');
assert.deepEqual(offered({ providers: [] }), ['google', 'email']);
assert.deepEqual(offered(SIGN_IN), ['google', 'microsoft', 'password', 'email'], 'the shipped list is the owner\'s four (2026-11-13)');
assert.equal(manualLabel(['google', 'microsoft', 'password']), 'No Google or Microsoft account? Sign in with email');
assert.equal(manualLabel(['google', 'email']), 'No Google account? Sign in with email');
assert.equal(methodOf({ isAnonymous: true }), 'email');
assert.equal(methodOf({ providerData: [{ providerId: 'google.com' }] }), 'google');
assert.equal(methodOf({ providerData: [{ providerId: 'microsoft.com' }] }), 'microsoft');
assert.equal(methodOf({ providerData: [{ providerId: 'password' }] }), 'password');
for (const code of ['auth/invalid-credential', 'auth/email-already-in-use', 'auth/account-exists-with-different-credential', 'auth/popup-closed-by-user'])
  assert.ok(AUTH_ERRORS[code] && AUTH_ERRORS[code].split(' ').length <= 20, `${code} has a short visitor sentence`);

// Emails.
for (const good of ['a@b.co', 'kid.name+4d@school.k12.il.us', '  spaced@example.com ']) assert.ok(validEmail(good), good);
for (const bad of ['', 'nope', 'a@b', 'a b@c.com', '@example.com', `${'x'.repeat(250)}@example.com`]) assert.ok(!validEmail(bad), bad);

// Off, and on but unable to start Firebase: both go straight in.
{
  const t0 = Date.now();
  const r = await signInGate({ year: '1904', gate: {}, config: { ...on, enabled: false }, loc: { hostname: 'chicago.polecat.live', search: '' }, nav: {} });
  assert.equal(r.how, 'off');
  assert.ok(Date.now() - t0 < 200, 'off returns at once');
  const robot = await signInGate({ year: '1904', gate: {}, config: on, loc: { hostname: 'chicago.polecat.live', search: '' }, nav: { webdriver: true } });
  assert.equal(robot.how, 'robot');
  // Node cannot import an https: module, which stands in for a blocked or failed SDK.
  const warn = console.warn; console.warn = () => {};
  const open = await signInGate({ year: '1904', gate: {}, config: on, loc: { hostname: 'chicago.polecat.live', search: '' }, nav: {}, storage: null });
  console.warn = warn;
  assert.equal(open.how, 'fail-open', 'a Firebase that cannot start lets the visitor in');
}

// T-3603: the About tab's account line and its Sign out.
{
  const els = {};
  const node = () => ({ hidden: true, textContent: '', disabled: false, onclick: null });
  for (const id of ['s-account', 's-account-who', 's-account-how', 's-sign-out']) els[id] = node();
  const doc = { getElementById: id => els[id] || null };
  assert.equal(showAccount(doc, null), false);
  assert.equal(els['s-account'].hidden, true, 'nobody signed in: no account line');
  assert.equal(showAccount({ getElementById: () => null }, { email: 'a@b.co' }), false, 'a page without the row is left alone');
  let out = 0, reloaded = 0;
  assert.equal(showAccount(doc, { email: 'a@b.co', method: 'microsoft', signOut: async () => { out++; } }, { reload: () => { reloaded++; } }), true);
  assert.equal(els['s-account'].hidden, false);
  assert.equal(els['s-account-who'].textContent, 'a@b.co');
  assert.equal(els['s-account-how'].textContent, 'with Microsoft');
  await els['s-sign-out'].onclick();
  assert.equal(out, 1, 'Sign out ends the session');
  assert.equal(reloaded, 1, 'and reloads, so the gate asks again');
  assert.equal(els['s-sign-out'].disabled, true, 'one press');
}

// What it writes matches the rules' field lists.
const doc = readFileSync(new URL('../docs/SIGN-IN.md', import.meta.url), 'utf8');
const lists = [...doc.matchAll(/hasOnly\(\[([^\]]*)\]\)/g)].map(m => m[1].match(/'([^']+)'/g).map(s => s.slice(1, -1)).sort());
// T-3645 added readers/<uid> (the reading age), whose list tools/test_reading_level.mjs holds;
// T-3644 people/<uid>'s, the visitor's own person (tools/test_visitor_person.mjs holds its write).
// T-3741 messages/<id>, the public contact page's (site/js/contact.js), checked below.
// T-3743 bugs/<id>, crash and bug reports (tools/test_bug_report.mjs holds its fields).
// T-3777 users/<uid>/<part>/<id>, cloud save (tools/test_cloud_save.mjs holds its writes).
// T-3778 classes, their members and hand-ins, and join codes (tools/test_classes.mjs holds them).
// T-3797 access/<email> (its fields and the two rights), waitlist/<email> and launch/cloud (tools/test_launch_rights.mjs).
assert.equal(lists.length, 16, 'docs/SIGN-IN.md holds the visitors, readers, visits, messages, bugs, people, users, classes, members (and what a member may change), handins, codes, access (and its rights), waitlist and launch hasOnly lists');
const visitorRule = lists.find((l) => l.includes('firstSeen'));
const visitRule = lists.find((l) => l.includes('uid') && !l.includes('kind'));
assert.deepEqual(lists.find((l) => l.includes('deleted')), ['at', 'deleted', 'v'], 'users/<uid>/<part>/<id> holds v, deleted and when');
assert.deepEqual(lists.find((l) => l.includes('ages')), ['ages', 'at'], 'readers/<uid> holds its ages and when');
const w = entryWrites({ projectId: 'p', uid: 'u1', email: 'a@b.co', name: 'A', method: 'google', year: '1835', device: 'phone', visitId: 'v1' });
const fieldsOf = write => [...Object.keys(write.update.fields), ...(write.updateTransforms || []).map(t => t.fieldPath)];
const visitorWritten = [...new Set([...fieldsOf(w.first[0]), ...fieldsOf(w.every[0])])].sort();
assert.deepEqual(visitorWritten, visitorRule, 'visitors/<uid> writes exactly the fields its rule allows');
assert.deepEqual(fieldsOf(w.every[1]).sort(), visitRule, 'visits/<id> writes exactly the fields its rule allows');
assert.match(w.first[0].update.name, /\/documents\/visitors\/u1$/);
assert.match(w.every[1].update.name, /\/documents\/visits\/v1$/);
assert.deepEqual(w.first[0].currentDocument, { exists: false }, 'first-seen lands only once');
assert.deepEqual(w.every[0].updateMask.fieldPaths.sort(), Object.keys(w.every[0].update.fields).sort(), 'the update touches only what it sends');
assert.equal(w.every[1].update.fields.uid.stringValue, 'u1', 'a visit names its own visitor (the rule checks it)');

// T-3741: the contact page writes exactly the messages rule's fields, to the same project.
const messageRule = lists.find((l) => l.includes('message'));
assert.deepEqual(messageRule, [...MESSAGE_FIELDS].sort(), 'messages/<id> rule lists the fields the visitors page reads');
const contact = readFileSync(new URL('../../../site/js/contact.js', import.meta.url), 'utf8');
const sent = contact.match(/fields: \{([\s\S]*?)\} \}\)/)[1].match(/\b([a-z]+): /g).map(s => s.slice(0, -2)).filter(k => !['stringValue', 'timestampValue'].includes(k)).sort();
assert.deepEqual(sent, messageRule, 'site/js/contact.js writes exactly the fields the messages rule allows');
assert.ok(contact.includes(`var PROJECT = '${SIGN_IN.firebase.projectId}'`), 'the contact page writes to the sign-in project');
assert.ok(contact.includes(`KEY = '${SIGN_IN.firebase.apiKey}'`), 'with its public web key');

// Reading back.
assert.deepEqual(fromFields({ a: { stringValue: 'x' }, n: { integerValue: '3' }, y: { arrayValue: { values: [{ stringValue: '1904' }] } }, t: { timestampValue: '2026-11-13T00:00:00Z' } }),
  { a: 'x', n: 3, y: ['1904'], t: '2026-11-13T00:00:00Z' });
assert.equal(autoId(() => 0).length, 20);
assert.equal(deviceClass({ matchMedia: () => ({ matches: true }), navigator: {}, screen: { width: 390, height: 844 } }), 'phone');
assert.equal(deviceClass({ matchMedia: () => ({ matches: true }), navigator: {}, screen: { width: 820, height: 1180 } }), 'tablet');
assert.equal(deviceClass({ matchMedia: () => ({ matches: false }), navigator: { maxTouchPoints: 0 }, screen: { width: 1920, height: 1080 } }), 'computer');

// The vendored SDK is reached through the import map, never fetched from gstatic.
const page = readFileSync(new URL('../renderers/web/index.html', import.meta.url), 'utf8');
assert.ok(page.includes('"https://www.gstatic.com/firebasejs/13.3.0/": "./vendor/firebase-13.3.0/"'), 'index.html maps the Firebase SDK to the vendored copy');
const visitorsPage = readFileSync(new URL('../renderers/web/visitors.html', import.meta.url), 'utf8');
assert.ok(visitorsPage.includes('"https://www.gstatic.com/firebasejs/13.3.0/": "./vendor/firebase-13.3.0/"'), 'visitors.html maps it too');

// T-3776: what an account keeps, and Delete my saved data.
{
  // One switch, off until the owner turns it on; a gate that is off turns it off too.
  assert.equal(SIGN_IN.cloudFeatures, true, 'the Stage 1 cloud features are on: the owner, 2026-11-27, "Turn on the cloud features" (docs/STUDENT-DATA.md)');
  assert.equal(cloudFeaturesOn({ enabled: true, cloudFeatures: true }), true);
  assert.equal(cloudFeaturesOn({ enabled: false, cloudFeatures: true }), false, 'no sign-in, no cloud feature');
  assert.equal(cloudFeaturesOn({ enabled: true }), false, 'absent is off');
  assert.equal(cloudFeaturesOn(null), false);

  // Every collection the rules let a visitor write is one Delete my saved data removes, and
  // the rules let the visitor read and delete each of them.
  const kept = [...ACCOUNT_DOCS, ...ACCOUNT_ROWS].sort();
  // T-3777: the tree under users/<uid>/ is the account's alone, in exactly the parts deleted.
  const tree = /match \/users\/\{uid\}\/\{part\}\/\{id\} \{\n\s+allow read, delete: if isSelf\(uid\) && part in \[([^\]]*)\];/.exec(doc);
  assert.ok(tree, 'users/<uid>/<part>/<id>: the account reads and deletes its own, nobody else');
  assert.deepEqual(tree[1].match(/'([^']+)'/g).map((x) => x.slice(1, -1)), [...ACCOUNT_TREES.users], 'in the parts Delete my saved data removes');
  assert.deepEqual(Object.keys(ACCOUNT_TREES), ['users']);
  const written = [...doc.matchAll(/match \/([a-z]+)\/\{[a-z]+\} \{\n\s+allow read, delete: ([^;]+);/g)].map((m) => [m[1], m[2]]);
  const selfDeletes = written.filter(([, rule]) => /isSelf|request\.auth\.uid == uid/.test(rule)).map(([c]) => c).sort();
  assert.deepEqual(selfDeletes, kept, 'the rules let a visitor delete exactly the collections js/student-data.js deletes');
  assert.deepEqual(written.filter(([, rule]) => !/isSelf|request\.auth\.uid == uid/.test(rule)).map(([c]) => c), ['messages'],
    'only the contact page\'s messages (no uid) are the owner\'s alone');
  const policy = readFileSync(new URL('../docs/STUDENT-DATA.md', import.meta.url), 'utf8');
  for (const c of [...kept, 'users', ...ACCOUNT_CLASSES]) assert.ok(policy.includes(`| \`${c}/`), `docs/STUDENT-DATA.md lists ${c}`);
  const privacy = readFileSync(new URL('../renderers/web/privacy.html', import.meta.url), 'utf8');
  assert.deepEqual([...privacy.matchAll(/data-collection="([a-z]+)"/g)].map((m) => m[1]).sort(), [...kept, 'users', 'classes', ...ACCOUNT_BY_EMAIL].sort(), 'privacy.html names every collection kept');
  assert.ok(page.includes('href="./privacy.html"'), 'Settings › About links What we keep');
  assert.ok(readFileSync(new URL('../renderers/web/js/sign-in.js', import.meta.url), 'utf8').includes('href="./privacy.html"'), 'the sign-in panel links it before anything is kept');

  // The query asks only for this uid's rows.
  const q = rowsQuery('visits', 'u1');
  assert.equal(q.where.fieldFilter.field.fieldPath, 'uid');
  assert.equal(q.where.fieldFilter.value.stringValue, 'u1');

  // A fake Firestore: three documents, two visits and one bug for u1, one visit for someone else.
  const calls = [];
  // T-3778: classes come back empty here (tools/test_classes.mjs and the emulator run hold them).
  const rows = { visits: ['v1', 'v2'], bugs: ['b1'], notebook: ['n1'], metfound: ['1835-met', '1835-found'], settings: [], classes: [] };
  const fakeFetch = async (url, init = {}) => {
    calls.push([init.method ?? 'GET', url, init.body ? JSON.parse(init.body) : null]);
    const ok = (body) => ({ ok: true, status: 200, json: async () => body });
    if (url.endsWith(':runQuery')) {
      const col = JSON.parse(init.body).structuredQuery.from[0].collectionId;
      const left = rows[col].splice(0);
      const parent = url.includes('/users/') ? 'users/u1/' : '';
      return ok(left.length ? left.map((id) => ({ document: { name: `projects/p/databases/(default)/documents/${parent}${col}/${id}` } })) : [{ readTime: 'x' }]);
    }
    return ok({});
  };
  const account = { uid: 'u1', idToken: async () => 'tok' };
  const r = await deleteMyData({ projectId: 'p', account, fetchFn: fakeFetch });
  assert.deepEqual(r, { deleted: 9, failed: [] }, 'three documents, three rows and three saved items');
  assert.deepEqual(calls.filter(([m]) => m === 'DELETE').map(([, u]) => u.split('/documents/')[1]), ['readers/u1', 'people/u1', 'visitors/u1']);
  const commits = calls.filter(([, u]) => u.endsWith(':commit')).map(([, , b]) => b.writes.map((w) => w.delete.split('/documents/')[1]));
  assert.deepEqual(commits, [['visits/v1', 'visits/v2'], ['bugs/b1'], ['users/u1/notebook/n1'], ['users/u1/metfound/1835-met', 'users/u1/metfound/1835-found']]);
  assert.ok(calls.filter(([, u]) => u.endsWith('/users/u1:runQuery')).length === 7, "the account's classes, then each saved part, queried under the account until empty");
  assert.deepEqual(calls[0].slice(0, 2), ['POST', 'https://firestore.googleapis.com/v1/projects/p/databases/(default)/documents/users/u1:runQuery'],
    "the student's classes are read before the tree that names them goes");
  assert.equal(calls.length, 19, 'the classes, three deletes, then each collection and part queried until it comes back empty');

  // A refusal is reported, never thrown, and the rest still goes.
  const refuse = async (url, init = {}) => (init.method === 'DELETE' && url.includes('/people/') ? { ok: false, status: 403 } : fakeFetch(url, init));
  rows.visits = ['v3']; rows.bugs = [];
  const partly = await deleteMyData({ projectId: 'p', account, fetchFn: refuse });
  assert.deepEqual(partly.failed, ['people']);
  assert.equal(partly.deleted, 3);
  assert.deepEqual(await deleteMyData({ projectId: 'p', account: null, fetchFn: fakeFetch }), { deleted: 0, failed: ['not signed in'] });

  // Settings › About: hidden signed out; the button asks once more, then deletes and says so.
  const els = Object.fromEntries(['s-saved-data', 's-delete-data', 's-delete-data-confirm', 's-delete-data-yes', 's-delete-data-no', 's-delete-data-status']
    .map((id) => [id, { id, hidden: true, disabled: false, textContent: '', focus() {} }]));
  els['s-delete-data'].hidden = false;
  const dom = { getElementById: (id) => els[id] ?? null };
  assert.equal(showSavedData(dom, null), false);
  assert.equal(els['s-saved-data'].hidden, true, 'nobody signed in: no saved-data section');
  let asked = 0, afterRan = 0;
  assert.equal(showSavedData(dom, account, { projectId: 'p', deleteFn: async () => { asked++; return { deleted: 4, failed: [] }; }, after: () => { afterRan++; } }), true);
  assert.equal(els['s-saved-data'].hidden, false);
  els['s-delete-data'].onclick();
  assert.equal(els['s-delete-data-confirm'].hidden, false, 'one press asks first');
  assert.equal(asked, 0, 'and deletes nothing yet');
  els['s-delete-data-no'].onclick();
  assert.equal(els['s-delete-data-confirm'].hidden, true, 'Cancel puts it back');
  els['s-delete-data'].onclick();
  await els['s-delete-data-yes'].onclick();
  assert.equal(asked, 1);
  assert.equal(afterRan, 1, 'then signs out');
  assert.match(els['s-delete-data-status'].textContent, /^Deleted/);
}

// T-3776: the rules publisher (chicago-4d-firestore-rules.yml) publishes exactly the doc's one
// rules block, with every collection the app writes, and carries the live owner address
// across rather than reading it from the repo.
{
  const rules = rulesFromDoc(doc);
  // T-3797: access/<email> and waitlist/<email> (deleted by address), and launch/cloud (the owner's switch, no one's data).
  assert.deepEqual(collectionsOf(rules), [...ACCOUNT_DOCS, ...ACCOUNT_ROWS, ...Object.keys(ACCOUNT_TREES), ...ACCOUNT_CLASSES, ...ACCOUNT_BY_EMAIL, 'handins', 'members', 'messages', 'launch'].sort(),
    'the published rules match every account collection (classes with their members and hand-ins), messages and launch access, and nothing else');
  assert.equal(ownerEmailOf(rules), null, 'the doc holds the placeholder, never an address');
  assert.equal(ownerEmailOf(rules.replaceAll("'OWNER_EMAIL'", "'owner@example.com'")), 'owner@example.com');
  assert.equal(ownerEmailOf("request.auth.token.email == 'a@x.org' || request.auth.token.email == 'b@x.org'"), null,
    'two addresses are refused, not guessed between');
  assert.throws(() => rulesFromDoc('no rules here'), /0 rules blocks/);
}

console.log('sign-in gate: OK');
