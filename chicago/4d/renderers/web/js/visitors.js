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
import { configured, signedInUser, METHOD_LABEL } from './sign-in.js';
import { listVisitors, listVisits, listMessages, listBugs, getBug } from './visitor-store.js';

const $ = id => document.getElementById(id);
const status = (text, bad = false) => { $('status').textContent = text; $('status').classList.toggle('bad', bad); };
const DAY = 86400000;

const central = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/Chicago', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
});
const centralDay = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Chicago', year: 'numeric', month: '2-digit', day: '2-digit' });
// T-3580: how each person signed in, in the words the table and the tiles use (sign-in.js).
export { METHOD_LABEL };
const methodLabel = m => METHOD_LABEL[m] || m || '—';
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
    ['People', visitors.length, tally(visitors, 'method').map(([m, n]) => `${n} ${methodLabel(m)}`).join(' · ')],
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
      [v.email || '—', 'email'], [v.name || '—'], [methodLabel(v.method)],
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
  bars($('by-method'), tally(visitors, 'method').map(([m, n]) => [methodLabel(m), n]));
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

/** T-3741: the contact page's messages, newest first; `null` when they could not be read. */
export function drawMessages(messages) {
  $('messages').hidden = false;
  if (messages === null) {
    $('messages-head').textContent = 'Messages from the contact page: not readable yet (paste the messages rule from docs/SIGN-IN.md)';
    $('message-rows').replaceChildren();
    return;
  }
  $('messages-head').textContent = `Messages from the contact page · ${messages.length}`;
  $('message-rows').replaceChildren(...messages.map(m => {
    const li = document.createElement('li');
    const meta = document.createElement('div'); meta.className = 'meta';
    const who = document.createElement('b'); who.textContent = m.name || '—';
    const mail = document.createElement('a'); mail.textContent = m.email || '—';
    if (m.email) mail.href = `mailto:${m.email}?subject=${encodeURIComponent('Re: 4D Chicago — ' + (m.topic || 'your message'))}`;
    const topic = document.createElement('span'); topic.textContent = m.topic || '';
    const at = document.createElement('span'); at.textContent = when(m.at);
    meta.append(who, mail, topic, at);
    const body = document.createElement('p'); body.textContent = m.message || '';
    li.append(meta, body);
    return li;
  }));
}

/**
 * T-3743: crash reports and bug reports, newest first; `null` when they could not be read.
 * `open(id)` reads one whole report (picture, environment, errors, steps) when asked.
 */
const KIND_WORDS = { bug: 'Bug report', crash: 'Crash', context: 'Display reset', error: 'Error' };
export function drawBugs(bugs, { open = async () => null, focus = '' } = {}) {
  $('bugs').hidden = false;
  if (bugs === null) {
    $('bugs-head').textContent = 'Bug reports and crashes: not readable yet (paste the bugs rule from docs/SIGN-IN.md)';
    $('bug-rows').replaceChildren();
    return;
  }
  const paint = () => {
    const site = $('bug-site').value;
    const shown = bugs.filter(b => !site || b.site === site);
    $('bugs-head').textContent = `Bug reports and crashes · ${shown.length}`;
    $('bug-rows').replaceChildren(...shown.map(b => {
      const li = document.createElement('li');
      li.id = `bug-${b.id}`;
      li.className = `bug bug-${b.kind || 'bug'}`;
      const meta = document.createElement('div'); meta.className = 'meta';
      const kind = document.createElement('b'); kind.textContent = KIND_WORDS[b.kind] || 'Report';
      const who = document.createElement(b.email ? 'a' : 'span'); who.textContent = b.email || 'not signed in';
      if (b.email) who.href = `mailto:${b.email}?subject=${encodeURIComponent('Re: your 4D Chicago report')}`;
      const where = document.createElement('span'); where.textContent = [b.year, b.site, b.place].filter(Boolean).join(' · ');
      const at = document.createElement('span'); at.textContent = when(b.at);
      meta.append(kind, who, where, at);
      const body = document.createElement('p'); body.textContent = b.comment || '—';
      const kit = document.createElement('div'); kit.className = 'meta';
      const dev = document.createElement('span'); dev.textContent = [b.device, b.gpu].filter(Boolean).join(' · ');
      kit.append(dev);
      // Anyone can file a report, so its link and picture are opened only as what they claim to be.
      if (/^https:\/\/(dev\.)?chicago\.polecat\.live\//.test(b.link || '')) { const go = document.createElement('a'); go.href = b.link; go.textContent = 'Open this spot'; go.target = '_blank'; go.rel = 'noopener'; kit.append(go); }
      const more = document.createElement('button'); more.type = 'button'; more.textContent = 'Details';
      const detail = document.createElement('div'); detail.className = 'bug-detail'; detail.hidden = true;
      more.onclick = async () => {
        if (!detail.hidden) { detail.hidden = true; more.textContent = 'Details'; return; }
        more.disabled = true; more.textContent = 'Loading…';
        try {
          const full = await open(b.id);
          detail.replaceChildren();
          if (/^data:image\/jpeg;base64,/.test(full?.shot || '')) { const img = document.createElement('img'); img.src = full.shot; img.alt = 'What the visitor saw'; detail.append(img); }
          for (const [key, label] of [['env', 'Device, scene and settings'], ['errors', 'Recent errors'], ['steps', 'Last steps (black box)']]) {
            if (!full?.[key]) continue;
            const d = document.createElement('details'); const sm = document.createElement('summary'); sm.textContent = label;
            const pre = document.createElement('pre');
            try { pre.textContent = JSON.stringify(JSON.parse(full[key]), null, 1); } catch { pre.textContent = full[key]; }
            d.append(sm, pre); detail.append(d);
          }
          const line = document.createElement('p'); line.className = 'meta'; line.textContent = `Build ${full?.build || '?'} · ${full?.page || ''}`;
          detail.append(line);
          detail.hidden = false; more.textContent = 'Hide';
        } catch (err) { more.textContent = 'Details'; status(err.message, true); }
        finally { more.disabled = false; }
      };
      kit.append(more);
      li.append(meta, body, kit, detail);
      return li;
    }));
  };
  $('bug-site').onchange = paint;
  paint();
  if (focus) {
    const row = $(`bug-${focus}`);
    row?.scrollIntoView({ block: 'start' });
    row?.querySelector('button')?.click();
  }
}

/** Invented rows for ?demo: example.com addresses, nothing real. */
export function demoRows(now = Date.now()) {
  const years = ['1812', '1835', '1904'];
  const devices = ['phone', 'computer', 'tablet'];
  const visitors = [];
  const visits = [];
  for (let i = 0; i < 9; i++) {
    const uid = `demo${i}`;
    const method = ['google', 'google', 'email', 'microsoft', 'google', 'password'][i % 6];
    const first = new Date(now - (i * 3 + 1) * DAY).toISOString();
    const entered = years.filter((_, k) => (i + k) % 2 === 0 || k === i % 3);
    for (let k = 0; k <= i % 4; k++) {
      visits.push({ uid, email: `visitor${i + 1}@example.com`, year: entered[k % entered.length], device: devices[i % 3],
        method, at: new Date(now - (i * 2 + k) * DAY / 3).toISOString() });
    }
    visitors.push({ id: uid, email: `visitor${i + 1}@example.com`, name: method === 'google' || method === 'microsoft' ? `Sample Visitor ${i + 1}` : '',
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
    drawMessages([
      { name: 'Sample Sender', email: 'sender@example.com', topic: 'A building, photo or source', message: 'A sample message, invented for the demo.', at: new Date().toISOString() },
    ]);
    const demoBugs = [
      { id: 'demo1', kind: 'bug', email: 'visitor1@example.com', year: '1904', site: 'live', place: 'Prairie Avenue at 18th Street', device: 'computer · Windows · Chrome 131', gpu: 'Google Inc. (Intel) · ANGLE (Intel, Intel(R) UHD Graphics 630)', comment: 'A sample report, invented for the demo: the door went black after I walked away.', link: '', at: new Date().toISOString() },
      { id: 'demo2', kind: 'crash', email: 'visitor2@example.com', year: '1835', site: 'dev', place: '', device: 'phone · iPhone · Safari 18', gpu: 'Apple Inc. · Apple GPU', comment: 'Page stopped 45.0 s into the visit.', link: '', at: new Date(Date.now() - DAY).toISOString() },
    ];
    drawBugs(demoBugs, { open: async (id) => ({ ...demoBugs.find(b => b.id === id), env: '{"device":{"class":"computer"}}', errors: '[]', steps: '' }) });
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
    drawMessages(await listMessages({ projectId, idToken }).catch(() => null));
    drawBugs(await listBugs({ projectId, idToken }).catch(() => null), {
      open: (id) => getBug({ projectId, idToken, id }),
      focus: new URLSearchParams(location.search).get('bug') || '',
    });
  } catch (err) {
    status(err.code === 'denied' ? 'This account cannot read the visitor list.' : err.message, true);
  }
}

main();
