/**
 * T-3576: the visitors page (visitors.html). The owner signs in with Google; the page
 * reads the visitor list and the last 30 days of entries over Firestore REST
 * (visitor-store.js) and draws who has come in, how many, into which year, on what.
 * The security rules decide who may read: anyone else gets a plain refusal.
 *
 * `?demo` draws invented sample rows (example.com addresses) without Firebase, so the
 * page can be looked at, and smoked, before the project exists.
 */
import { SIGN_IN } from './sign-in-config.js';
import { configured, signedInUser } from './sign-in.js';
import { listVisitors, listVisits } from './visitor-store.js';

const $ = id => document.getElementById(id);
const status = (text, bad = false) => { $('status').textContent = text; $('status').classList.toggle('bad', bad); };
const DAY = 86400000;

const central = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/Chicago', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
});
const centralDay = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Chicago', year: 'numeric', month: '2-digit', day: '2-digit' });
const when = iso => (iso ? central.format(new Date(iso)) + ' CT' : '—');

function tally(rows, key) {
  const out = new Map();
  for (const row of rows) { const k = row[key] || '—'; out.set(k, (out.get(k) || 0) + 1); }
  return [...out.entries()].sort((a, b) => b[1] - a[1]);
}

function bars(el, pairs) {
  el.replaceChildren();
  const max = Math.max(1, ...pairs.map(p => p[1]));
  if (!pairs.length) { const li = document.createElement('li'); li.textContent = 'Nothing yet.'; el.append(li); return; }
  for (const [label, n] of pairs) {
    const li = document.createElement('li');
    const name = document.createElement('span'); name.textContent = label;
    const bar = document.createElement('i'); bar.style.width = `${(100 * n / max).toFixed(1)}%`;
    const count = document.createElement('b'); count.textContent = String(n);
    li.append(name, document.createElement('span'), count);
    li.children[1].append(bar);
    el.append(li);
  }
}

function tiles(visitors, visits, now) {
  const since = ms => visits.filter(v => now - Date.parse(v.at) < ms);
  const people = ms => new Set(since(ms).map(v => v.uid)).size;
  const newPeople = ms => visitors.filter(v => v.firstSeen && now - Date.parse(v.firstSeen) < ms).length;
  const data = [
    ['People', visitors.length, `${visitors.filter(v => v.method === 'google').length} Google · ${visitors.filter(v => v.method === 'email').length} email`],
    ['Today', people(DAY), `${since(DAY).length} entries`],
    ['Last 7 days', people(7 * DAY), `${since(7 * DAY).length} entries · ${newPeople(7 * DAY)} new`],
    ['Last 30 days', people(30 * DAY), `${visits.length} entries · ${newPeople(30 * DAY)} new`],
  ];
  $('tiles').replaceChildren(...data.map(([label, n, note]) => {
    const div = document.createElement('div'); div.className = 'tile';
    const dt = document.createElement('dt'); dt.textContent = label;
    const dd = document.createElement('dd'); dd.textContent = String(n);
    const small = document.createElement('small'); small.textContent = note;
    div.append(dt, dd, small);
    return div;
  }));
}

let shown = [];
function table(visitors) {
  const q = $('filter').value.trim().toLowerCase();
  shown = q ? visitors.filter(v => `${v.email} ${v.name}`.toLowerCase().includes(q)) : visitors;
  $('rows').replaceChildren(...shown.map(v => {
    const tr = document.createElement('tr');
    const cells = [
      [v.email || '—', 'email'], [v.name || '—'], [v.method === 'google' ? 'Google' : v.method === 'email' ? 'Email' : (v.method || '—')],
      [when(v.firstSeen)], [when(v.lastSeen)], [String(v.visits ?? '—'), 'num'], [(v.years || []).slice().sort().join(', ') || '—'],
    ];
    for (const [text, cls] of cells) { const td = document.createElement('td'); td.textContent = text; if (cls) td.className = cls; tr.append(td); }
    return tr;
  }));
}

function csv(visitors) {
  const esc = s => `"${String(s ?? '').replace(/"/g, '""')}"`;
  const head = ['email', 'name', 'method', 'first_seen_utc', 'last_seen_utc', 'entries', 'years'];
  const lines = [head.join(',')].concat(visitors.map(v =>
    [v.email, v.name, v.method, v.firstSeen, v.lastSeen, v.visits, (v.years || []).join(' ')].map(esc).join(',')));
  const blob = new Blob([lines.join('\n') + '\n'], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `4d-chicago-visitors-${centralDay.format(new Date())}.csv`;
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

export function draw(visitors, visits, now = Date.now()) {
  tiles(visitors, visits, now);
  bars($('by-year'), tally(visits, 'year'));
  bars($('by-device'), tally(visits, 'device'));
  const days = [];
  for (let i = 13; i >= 0; i--) {
    const day = centralDay.format(new Date(now - i * DAY));
    days.push([day.slice(5), visits.filter(v => centralDay.format(new Date(v.at)) === day).length]);
  }
  bars($('by-day'), days);
  table(visitors);
  $('filter').oninput = () => table(visitors);
  $('csv').onclick = () => csv(shown);
  for (const id of ['report', 'usage', 'people']) $(id).hidden = false;
  status(visitors.length ? `${visitors.length} ${visitors.length === 1 ? 'person has' : 'people have'} signed in.` : 'Nobody has signed in yet.');
}

/** Invented rows for ?demo: example.com addresses, nothing real. */
export function demoRows(now = Date.now()) {
  const years = ['1812', '1835', '1904'];
  const devices = ['phone', 'computer', 'tablet'];
  const visitors = [];
  const visits = [];
  for (let i = 0; i < 9; i++) {
    const uid = `demo${i}`;
    const method = i % 3 === 2 ? 'email' : 'google';
    const first = new Date(now - (i * 3 + 1) * DAY).toISOString();
    const entered = years.filter((_, k) => (i + k) % 2 === 0 || k === i % 3);
    for (let k = 0; k <= i % 4; k++) {
      visits.push({ uid, email: `visitor${i + 1}@example.com`, year: entered[k % entered.length], device: devices[i % 3],
        method, at: new Date(now - (i * 2 + k) * DAY / 3).toISOString() });
    }
    visitors.push({ id: uid, email: `visitor${i + 1}@example.com`, name: method === 'google' ? `Sample Visitor ${i + 1}` : '',
      method, firstSeen: first, lastSeen: new Date(now - i * DAY / 2).toISOString(), visits: (i % 4) + 1 + i, years: entered });
  }
  visits.sort((a, b) => b.at.localeCompare(a.at));
  return { visitors, visits };
}

async function main() {
  if (new URLSearchParams(location.search).has('demo')) {
    const { visitors, visits } = demoRows();
    $('who').textContent = 'Sample data';
    draw(visitors, visits);
    return;
  }
  if (!configured(SIGN_IN.firebase)) {
    status('Sign-in is not set up yet: the Firebase project goes in js/sign-in-config.js.');
    return;
  }
  let fb;
  try { fb = await signedInUser(SIGN_IN); } catch (err) { status(`Firebase did not start: ${err.message}`, true); return; }
  const { auth, authMod } = fb;
  $('sign-in').onclick = async () => {
    try {
      await authMod.signInWithPopup(auth, new authMod.GoogleAuthProvider());
      location.reload();
    } catch (err) { status(`Google sign-in did not work: ${err.code || err.message}`, true); }
  };
  $('sign-out').onclick = async () => { await authMod.signOut(auth); location.reload(); };
  const user = auth.currentUser;
  if (!user || user.isAnonymous) {
    $('sign-in').hidden = false;
    status('Sign in with the owner’s Google account to see the list.');
    return;
  }
  $('who').textContent = user.email || '';
  $('sign-out').hidden = false;
  try {
    const idToken = await user.getIdToken();
    const projectId = SIGN_IN.firebase.projectId;
    const [visitors, visits] = await Promise.all([
      listVisitors({ projectId, idToken }),
      listVisits({ projectId, idToken, since: new Date(Date.now() - 30 * DAY) }),
    ]);
    draw(visitors, visits);
  } catch (err) {
    status(err.code === 'denied' ? 'This account cannot read the visitor list.' : err.message, true);
  }
}

main();
