#!/usr/bin/env node
// T-3576: the sign-in gate's policy, without a browser. When it asks, that it never
// locks anyone out, and that what it writes is exactly what docs/SIGN-IN.md's
// Firestore rules allow.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { configured, gateMode, validEmail, signInGate, offered, manualLabel, methodOf, AUTH_ERRORS } from '../renderers/web/js/sign-in.js';
import { entryWrites, fromFields, deviceClass, autoId } from '../renderers/web/js/visitor-store.js';
import { SIGN_IN } from '../renderers/web/js/sign-in-config.js';

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

// What it writes matches the rules' field lists.
const doc = readFileSync(new URL('../docs/SIGN-IN.md', import.meta.url), 'utf8');
const lists = [...doc.matchAll(/hasOnly\(\[([^\]]*)\]\)/g)].map(m => m[1].match(/'([^']+)'/g).map(s => s.slice(1, -1)).sort());
assert.equal(lists.length, 2, 'docs/SIGN-IN.md holds the visitors and visits hasOnly lists');
const [visitorRule, visitRule] = lists;
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

console.log('sign-in gate: OK');
