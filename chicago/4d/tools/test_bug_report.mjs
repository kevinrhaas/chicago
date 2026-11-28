#!/usr/bin/env node
// T-3743: crash reports and the Report a bug key (renderers/web/js/bug-report.js). The fields
// written are the ones docs/SIGN-IN.md's `bugFields` rule allows, at its lengths; nothing goes
// out from a host the sign-in gate does not run on or under automation; a crash is filed once
// (a display reset filed by its own page is not filed again by the next); automatic reports
// and their emails are capped; "Script error." and other origins' errors are not ours; and the
// key sits in the compass row with its Settings switch.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  BUG_FIELDS, BUG_LIMITS, BUG_KINDS, AUTO_PER_PAGE, MAIL_PER_DAY, SENT_KEY,
  siteOf, sendsFrom, reportFields, mailBody, browserOf, createErrorRing, createBugReports,
} from '../renderers/web/js/bug-report.js';
import { BUG_LIST_FIELDS } from '../renderers/web/js/visitor-store.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');

// ---- the rule and the writer agree ---------------------------------------------------------------
const doc = read('docs/SIGN-IN.md');
const rule = /function bugFields\(d\) \{([\s\S]*?)\n    \}/.exec(doc)?.[1];
assert(rule, 'docs/SIGN-IN.md has the bugFields rule');
const ruled = JSON.parse(`[${/hasOnly\(\[([^\]]*)\]\)/.exec(rule)[1].replace(/'/g, '"')}]`);
assert.deepEqual(ruled, BUG_FIELDS, 'the rule allows exactly the fields the writer sends');
const fields = reportFields({ kind: 'bug', uid: 'u1', email: 'a@example.com', env: { x: 1 } }, { now: () => 0 });
assert.deepEqual(Object.keys(fields), BUG_FIELDS, 'and the writer sends each of them');
for (const [k, n] of Object.entries(BUG_LIMITS)) {
  assert(new RegExp(`d\\.${k} is string && d\\.${k}\\.size\\(\\) <= ${n}\\b`).test(rule), `the rule holds ${k} to ${n}`);
}
assert(/d\.at is timestamp/.test(rule) && 'timestampValue' in fields.at, 'at is a timestamp');
assert.deepEqual(JSON.parse(`[${/d\.kind in \[([^\]]*)\]/.exec(rule)[1].replace(/'/g, '"')}]`), BUG_KINDS);
assert(/request\.auth == null && d\.uid == ''/.test(rule) && /d\.uid == request\.auth\.uid/.test(rule), 'a uid is the writer’s own, or none');
// T-3776: the owner reads every report; a signed-in visitor reads and deletes only their own
// (Delete my saved data), and a report sent signed out (uid '') stays the owner's alone.
assert(/match \/bugs\/\{id\} \{\s*allow read, delete: if isOwner\(\) \|\| \(resource\.data\.uid != '' && isSelf\(resource\.data\.uid\)\);/.test(doc),
  'the owner reads; a visitor only their own signed-in reports');
assert(BUG_LIST_FIELDS.every((f) => BUG_FIELDS.includes(f)) && !BUG_LIST_FIELDS.includes('shot'), 'the list reads short fields, never the picture');

// Every field fits; an over-long JSON field keeps its newest tail; an over-long picture is dropped.
const big = reportFields({ kind: 'nonsense', comment: 'x'.repeat(9000), steps: 'a'.repeat(19990) + 'TAIL'.repeat(10), shot: 'd'.repeat(BUG_LIMITS.shot + 1) });
assert.equal(big.kind.stringValue, 'bug', 'an unknown kind is filed as a bug');
assert.equal(big.comment.stringValue.length, BUG_LIMITS.comment);
assert(big.steps.stringValue.endsWith('TAIL') && big.steps.stringValue.length === BUG_LIMITS.steps);
assert.equal(big.shot.stringValue, '');

// ---- where it sends ------------------------------------------------------------------------------
assert.equal(siteOf('chicago.polecat.live'), 'live');
assert.equal(siteOf('dev.chicago.polecat.live'), 'dev');
assert.equal(siteOf('127.0.0.1'), 'local');
const config = { enabled: true, hosts: ['chicago.polecat.live', 'dev.chicago.polecat.live'], firebase: { apiKey: 'k', projectId: 'p' } };
assert.equal(sendsFrom({ config, hostname: 'chicago.polecat.live' }), true);
assert.equal(sendsFrom({ config, hostname: 'chicago.polecat.live', webdriver: true }), false, 'never under automation');
assert.equal(sendsFrom({ config, hostname: 'localhost' }), false, 'never from a local serve');
assert.equal(sendsFrom({ config: { ...config, enabled: false }, hostname: 'chicago.polecat.live' }), false);
assert.equal(browserOf('Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 Chrome/131.0 Safari/537.36'), 'Chrome 131');
assert.equal(browserOf('Mozilla/5.0 (iPhone) AppleWebKit/605 Version/18.1 Mobile/15E148 Safari/604.1'), 'Safari 18');
assert.equal(mailBody({ kind: 'crash', site: 'dev', year: '1835', email: '' })._subject, '4D Chicago [dev] — Crash — 1835 — not signed in');
assert.equal(mailBody({ kind: 'bug', site: 'live', year: '1904', email: 'v@example.com' })._replyto, 'v@example.com');

// ---- the reporter ---------------------------------------------------------------------------------
function fakeWin({ hostname = 'chicago.polecat.live', webdriver = false } = {}) {
  const on = {};
  const store = new Map();
  return {
    on, store,
    location: { hostname, origin: `https://${hostname}`, pathname: '/4d/1904/', search: '?year=1904' },
    navigator: { userAgent: 'Mozilla/5.0 Chrome/131.0', webdriver, hardwareConcurrency: 8, maxTouchPoints: 0, platform: 'Win32' },
    screen: { width: 1920, height: 1080 }, innerWidth: 1280, innerHeight: 800, devicePixelRatio: 1,
    matchMedia: () => ({ matches: false }), performance: {},
    console: { error() {} },
    addEventListener(type, fn) { on[type] = fn; },
    localStorage: { getItem: (k) => store.get(k) ?? null, setItem: (k, v) => store.set(k, String(v)) },
  };
}
const flush = () => new Promise((r) => setTimeout(r, 0));
function reporter(opts = {}) {
  const win = fakeWin(opts);
  let clock = 1_000_000;
  const r = createBugReports({ config, year: '1904', build: 'b1', win, store: win.localStorage, now: () => clock });
  const sent = []; const mailed = [];
  r.net.send = async (id, f, token) => { sent.push({ id, f, token }); return true; };
  r.net.mail = async (body) => { mailed.push(body); return true; };
  return { r, win, sent, mailed, tick: (ms) => { clock += ms; } };
}

{
  // Queued until sign-in answers; then sent with the visitor's token and uid.
  const { r, win, sent, mailed } = reporter();
  assert.equal(r.live, true);
  r.setExtra(() => ({ gpu: 'Intel UHD 630', place: 'Prairie Avenue', link: 'https://chicago.polecat.live/4d/1904/?moment=1', settings: { bugKey: true } }));
  win.on.error({ message: 'boom', filename: 'https://chicago.polecat.live/4d/walk/js/main.js', error: new Error('boom') });
  await flush();
  assert.equal(sent.length, 0, 'nothing leaves before sign-in has answered');
  r.signedIn({ uid: 'U1', email: 'v@example.com', idToken: async () => 'TOKEN' });
  await flush(); await flush();
  assert.equal(sent.length, 1);
  assert.equal(sent[0].token, 'TOKEN');
  assert.equal(sent[0].f.uid.stringValue, 'U1');
  assert.equal(sent[0].f.kind.stringValue, 'error');
  assert.equal(sent[0].f.site.stringValue, 'live');
  assert.equal(sent[0].f.gpu.stringValue, 'Intel UHD 630');
  assert.match(sent[0].f.errors.stringValue, /boom/, 'the error is among the recent errors');
  assert.equal(JSON.parse(sent[0].f.env.stringValue).device.cores, 8, 'the device’s facts ride in env');
  assert.equal(mailed.length, 0, 'an error is recorded, not emailed');

  // The same message again is not filed again; another origin's, and "Script error.", never.
  win.on.error({ message: 'boom', filename: 'https://chicago.polecat.live/4d/walk/js/main.js', error: new Error('boom') });
  win.on.error({ message: 'Script error.', filename: '' });
  win.on.error({ message: 'ext', filename: 'chrome-extension://abc/x.js' });
  await flush(); await flush();
  assert.equal(sent.length, 1, JSON.stringify(sent.map(s => s.f.comment.stringValue)));
  assert(r.errors.lines.some((l) => l.msg === 'Script error.'), 'but kept among the recent errors');

  // The visitor's own report: always emailed, with the picture.
  const entry = await r.bug({ comment: 'the door went black', shot: 'data:image/jpeg;base64,AAAA', steps: { page: 'p1', entries: [] } });
  assert(entry.stored && entry.mailed);
  assert.equal(sent.at(-1).f.kind.stringValue, 'bug');
  assert.equal(sent.at(-1).f.shot.stringValue, 'data:image/jpeg;base64,AAAA');
  assert.equal(mailed.at(-1).comment, 'the door went black');
  assert.match(mailed.at(-1).report, /visitors\.html\?bug=/, 'the email links to the report');
}
{
  // A display reset filed by its page is not filed again from the next load; a crash is filed once.
  const a = reporter();
  a.r.signedIn(null);
  assert.equal(a.r.contextLost({ page: 'PAGE1', entries: [{ k: 'lost' }] }), true);
  await flush(); await flush();
  assert.equal(a.sent.at(-1).f.kind.stringValue, 'context');
  assert.equal(a.sent.at(-1).f.uid.stringValue, '', 'nobody signed in: no uid');
  assert.equal(a.sent.at(-1).token, '');
  assert.equal(a.mailed.length, 1, 'a display reset is emailed');
  const b = createBugReports({ config, year: '1835', win: a.win, store: a.win.localStorage, now: () => 1_000_500 });
  b.net.send = a.r.net.send; b.net.mail = a.r.net.mail;
  b.signedIn(null);
  assert.equal(b.crash({ page: 'PAGE1', year: '1904', entries: [] }, 'Display reset'), false, 'already filed by the page it hit');
  assert.equal(b.crash({ page: 'PAGE2', year: '1904', entries: [] }, 'Page stopped 45 s into the visit.'), true);
  assert.equal(b.crash({ page: 'PAGE2', year: '1904', entries: [] }, 'again'), false, 'and once only');
  await flush(); await flush();
  assert.equal(a.sent.at(-1).f.kind.stringValue, 'crash');
  assert.equal(a.sent.at(-1).f.year.stringValue, '1904', 'filed under the year that crashed');
  assert.match(a.sent.at(-1).f.steps.stringValue, /PAGE2/, 'with that page’s black box');
}
{
  // Caps: AUTO_PER_PAGE automatic reports a page; MAIL_PER_DAY automatic emails a device a day.
  const { r, win, sent, mailed, tick } = reporter();
  r.signedIn(null);
  for (let i = 0; i < 6; i++) win.on.error({ message: `e${i}`, filename: '', error: new Error(`e${i}`) });
  await flush(); await flush();
  assert.equal(sent.length, AUTO_PER_PAGE, 'three automatic reports a page');
  const days = [];
  for (let i = 0; i < 5; i++) {
    const next = createBugReports({ config, year: '1904', win, store: win.localStorage, now: () => 2_000_000 + i });
    next.net.send = r.net.send; next.net.mail = r.net.mail; next.signedIn(null);
    days.push(next.crash({ page: `P${i}`, entries: [] }, 'cut'));
  }
  await flush(); await flush();
  assert.equal(mailed.length, MAIL_PER_DAY, 'three automatic emails a device a day');
  const ledger = JSON.parse(win.store.get(SENT_KEY));
  assert.equal(ledger.mail.length, MAIL_PER_DAY);
  tick(0);
}
{
  // Off the live hosts, and under automation, nothing is sent.
  for (const opts of [{ hostname: '127.0.0.1' }, { webdriver: true }]) {
    const { r, sent, mailed } = reporter(opts);
    r.signedIn(null);
    const e = await r.bug({ comment: 'x' });
    assert.equal(e.live, false);
    r.crash({ page: 'Z', entries: [] });
    await flush(); await flush();
    assert.equal(sent.length + mailed.length, 0, JSON.stringify(opts));
    assert.match(r.preview({ comment: 'hello' }), /"comment": "hello"/, 'Copy has the report');
  }
}
{
  const ring = createErrorRing({ max: 3, now: () => 0 });
  for (let i = 0; i < 5; i++) ring.push('console', `line ${i}`);
  assert.deepEqual(ring.lines.map((l) => l.msg), ['line 2', 'line 3', 'line 4'], 'the newest few, newest last');
}

// ---- the page ------------------------------------------------------------------------------------
const main = read('renderers/web/js/main.js');
assert(/bugs\.signedIn\(api\.signIn\.account \?\? null\)/.test(main), 'reports go out once sign-in answers');
assert(/bugs\.crash\(blackbox\.previous, line\)/.test(main), 'a cut-off page is filed by the next load');
assert(/webglcontextlost', \(\) => \{ blackbox\.log\('lost'\); bugs\.contextLost\(blackbox\.box\); \}/.test(main), 'a display reset is filed at once');
assert(/pendingBugShot \|\| gateFrame\.due\(\)/.test(main), 'a picture asked for forces a frame');
assert(/v\?\.target === '#bug-key' && backends\.name === 'touch'[^\n]*navigatorUi\.dock\(\)/.test(main), 'on a phone the tour docks the Navigator, which hides the key, at the bug step');
assert(/key === 'bugKey'[\s\S]{0,80}api\.bugKey\?\.setShown\(value\)/.test(main), 'the Settings switch shows and hides the key');
const hud = read('renderers/web/js/hud.js');
assert(/bugKey: true,/.test(hud), 'the key is on by default');
assert(/wireToggle\('s-bug-key', 'bugKey'\)/.test(hud), 'and Settings › Show switches it');
const html = read('renderers/web/index.html');
assert(/class="instrument-keys"/.test(html), 'the key hangs in the compass row’s keys');
assert(!/bug-key/.test(html), 'built by script, so the year doors stay under the copy floor');
const css = read('renderers/web/css/walk.css');
assert(/\.bug-key \{[^}]*width: 24px; height: 24px/.test(css), 'the smallest key on the row');

console.log(`test_bug_report: ${BUG_FIELDS.length} fields as the rule allows, live hosts only, crash filed once, ${AUTO_PER_PAGE} automatic a page, ${MAIL_PER_DAY} emails a day, key on by default`);
