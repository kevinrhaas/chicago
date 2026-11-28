/**
 * whatsnew.js — render the changelog inside the walkthrough.
 *
 * The project already keeps a fleet-format changelog that Manager and the
 * polecat.live launcher parse. Until now the one audience who could not read it
 * was the person standing in the town it describes. This puts it in the panel.
 *
 * It imports `./changelog.js` directly rather than fetching a URL: the file is
 * authored here, in the app, and `tools/publish.sh` mirrors it out to
 * <site>/js/changelog.js for the fleet. A relative import is the one form that
 * resolves identically in the dev tree and in the published build — a fetch
 * would need a different base in each, which is exactly the class of bug that
 * ships green and 404s live.
 *
 * The import is DYNAMIC, and made only when the tab is opened (T-1973). The
 * changelog is a megabyte on the wire and every first visit paid it at boot to
 * answer one question — how many releases are newer than the last one read —
 * for the unread dot. The published page now carries the answer's inputs:
 * tools/publish.sh writes the release numbers into
 * `<meta name="c4d-releases" content="1-1303">`, read from the same file this
 * module imports. Where the meta is empty (the dev tree, unpublished) the count
 * falls back to importing the changelog, so both trees show the same dot.
 *
 * T-3813 (Kevin, 2026-11-27: "consolidate it some and save the old version and keep
 * the what's new items more concise"). The tab painted every release with every note
 * open, 3,300 releases and 690,000 words. It now opens on the latest few release days,
 * one line a release under its day, a tap away from its notes; the full history, as
 * first written, sits behind one button and paints a page at a time. changelog.js is
 * untouched: Manager and the launcher read it as before.
 */

import { t as str } from './strings/index.js';
import './strings/whatsnew.js';

let changelogPromise = null;
/** The changelog module, imported once, on first need. */
function loadChangelog() {
  if (!changelogPromise) {
    changelogPromise = import('./changelog.js').catch((err) => {
      changelogPromise = null;
      throw err;
    });
  }
  return changelogPromise;
}

/**
 * The release numbers publish.sh wrote into the page, as [from, to] runs, or
 * null where there are none to read (the dev tree, or a meta that fails to parse).
 */
function publishedReleases() {
  const raw = document.querySelector('meta[name="c4d-releases"]')?.content?.trim();
  if (!raw) return null;
  const runs = [];
  for (const part of raw.split(',')) {
    const m = /^(\d+)(?:-(\d+))?$/.exec(part.trim());
    if (!m) return null;
    const a = Number(m[1]);
    const b = m[2] ? Number(m[2]) : a;
    if (!(b >= a)) return null;
    runs.push([a, b]);
  }
  return runs.length ? runs : null;
}

/** What the dot needs: the newest release and how many are newer than `seen`. */
async function releaseSummary(seen) {
  const runs = publishedReleases();
  if (runs) {
    let unseen = 0;
    let latest = 0;
    for (const [a, b] of runs) {
      latest = Math.max(latest, b);
      unseen += Math.max(0, b - Math.max(a, seen + 1) + 1);
    }
    return { latest, unseen };
  }
  const { CHANGELOG, LATEST_VERSION } = await loadChangelog();
  return { latest: LATEST_VERSION, unseen: CHANGELOG.filter((e) => e.v > seen).length };
}

const SEEN_KEY = 'chicago4d.whatsnew.seen';

// Not "New" for `feature`: that is also what the unread flag says, and an entry
// reading "NEW … New · Aug 9" makes the two mean nothing. `kind` describes what
// the release WAS; the flag describes whether you have read it.
// T-3813: every kind the history carries has a word, so no line reads "improvement".
const KIND_LABEL = {
  feature: 'Added', add: 'Added', feat: 'Added', fix: 'Fixed', polish: 'Polish',
  change: 'Changed', improvement: 'Improved', improve: 'Improved', chore: 'Upkeep',
};

function readSeen() {
  try { return Number(window.localStorage.getItem(SEEN_KEY)) || 0; } catch { return 0; }
}

function writeSeen(v) {
  try { window.localStorage.setItem(SEEN_KEY, String(v)); } catch { /* private mode */ }
}

/** How many releases the visitor has not been shown yet (a promise). */
export async function unseenCount(seen = readSeen()) {
  return (await releaseSummary(seen)).unseen;
}

/** How many release days the tab opens on (T-3813). Some twenty releases land on a
 * busy day, so three days is a screenful of titles, not a scroll through a season. */
export const LATEST_DAYS = 3;
/** …and never on fewer releases than this: a quiet week still opens on a screenful. */
export const LATEST_MIN = 8;
/** The full history paints this many releases at a time, so a phone opening it is not
 * handed the whole record (3,300 releases, 690,000 words in November 2026) at once. */
export const HISTORY_PAGE = 100;

/** `date` is "Nov 27, 2026, 1:19 PM CT": the day is its first two parts, the time the rest. */
function dayOf(entry) {
  const parts = String(entry.date || '').split(', ');
  return { day: parts.slice(0, 2).join(', '), time: parts.slice(2).join(', ') };
}

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined) n.textContent = text;
  return n;
}

function itemsList(entry) {
  const items = el('ul', 'wn-items');
  for (const it of entry.items || []) items.appendChild(el('li', '', it));
  return items;
}

function flag() { return el('span', 'wn-flag', 'new'); }

/** One release as one line: its title, tapped open for its notes (T-3813). */
function latestEntry(entry, isNew) {
  const li = el('li', 'wn-entry');
  li.dataset.v = String(entry.v);
  if (isNew) li.classList.add('is-new');
  const box = el('details', 'wn-fold');
  const head = el('summary', 'wn-head');
  head.appendChild(el('b', 'wn-title', entry.title));
  if (isNew) head.appendChild(flag());
  // The kind and the hour: the day is the group's heading above. Shown as stored (a
  // Central-Time alias the stamper derives from `ts`), so it matches every fleet surface.
  head.appendChild(el('span', 'wn-meta',
    [KIND_LABEL[entry.kind] || entry.kind, dayOf(entry).time].filter(Boolean).join(' · ')));
  box.append(head, itemsList(entry));
  li.appendChild(box);
  return li;
}

/** One release as the feed first wrote it, notes open: the full history keeps that look. */
function historyEntry(entry, isNew) {
  const li = el('li', 'wn-entry');
  li.dataset.v = String(entry.v);
  if (isNew) li.classList.add('is-new');
  const head = el('div', 'wn-head');
  head.appendChild(el('b', 'wn-title', entry.title));
  if (isNew) head.appendChild(flag());
  const meta = el('div', 'wn-meta',
    [KIND_LABEL[entry.kind] || entry.kind, entry.date].filter(Boolean).join(' · '));
  li.append(head, meta, itemsList(entry));
  return li;
}

/**
 * Paint the feed into `host` (T-3813): the latest LATEST_DAYS release days (LATEST_MIN
 * releases at least), one line a release grouped under its day, then the full history
 * behind one button, painted a page at a time. Entries newer than the visitor's last visit are marked in both, so
 * "what changed since I was last here" is answerable at a glance — the only question
 * this panel is really for.
 */
export async function renderWhatsNew(host) {
  if (!host) return;
  const { CHANGELOG } = await loadChangelog();
  const seen = readSeen();
  // A first-time visitor has no "last time", so flagging every entry as new
  // marks the whole list and distinguishes nothing. The chip dot still points
  // them here; the per-entry flag is reserved for what it can actually answer.
  const markNew = seen > 0;
  const isNew = (e) => markNew && e.v > seen;
  host.textContent = '';

  let cut = 0;
  const days = [];
  for (; cut < CHANGELOG.length; cut++) {
    const { day } = dayOf(CHANGELOG[cut]);
    if (!days.length || days.at(-1).day !== day) {
      if (days.length >= LATEST_DAYS && cut >= LATEST_MIN) break;
      days.push({ day, entries: [] });
    }
    days.at(-1).entries.push(CHANGELOG[cut]);
  }
  const older = CHANGELOG.slice(cut);

  host.appendChild(el('p', 'wn-lead', str('whatsnew.lead')));
  const latest = el('div', 'wn-latest');
  for (const { day, entries } of days) {
    const group = el('section', 'wn-day');
    group.appendChild(el('h3', 'wn-day-head', day.replace(/, \d{4}$/, '')));
    const list = el('ol', 'wn-list');
    for (const e of entries) list.appendChild(latestEntry(e, isNew(e)));
    group.appendChild(list);
    latest.appendChild(group);
  }
  host.appendChild(latest);

  if (!older.length) return;
  const unreadOlder = older.filter(isNew).length;
  if (unreadOlder) {
    host.appendChild(el('p', 'wn-unread', str('whatsnew.unread', { n: unreadOlder.toLocaleString() })));
  }

  const history = el('section', 'wn-history');
  const toggle = el('button', 'setting-button wn-history-toggle', str('whatsnew.history'));
  toggle.type = 'button';
  toggle.setAttribute('aria-expanded', 'false');
  const body = el('div', 'wn-history-body');
  body.hidden = true;
  toggle.id = 'wn-history-toggle';
  body.id = 'wn-history';
  toggle.setAttribute('aria-controls', body.id);
  history.append(toggle, body);
  host.appendChild(history);

  let painted = 0;
  let list = null;
  let more = null;
  const paintPage = () => {
    const page = older.slice(painted, painted + HISTORY_PAGE);
    for (const e of page) list.appendChild(historyEntry(e, isNew(e)));
    painted += page.length;
    const left = older.length - painted;
    more.hidden = left <= 0;
    more.textContent = str('whatsnew.history.more', { n: Math.min(left, HISTORY_PAGE).toLocaleString() });
  };
  toggle.addEventListener('click', () => {
    const open = body.hidden;
    body.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
    toggle.textContent = str(open ? 'whatsnew.history.hide' : 'whatsnew.history');
    if (open && !list) {
      const first = older.at(-1);
      body.appendChild(el('p', 'wn-history-note', str('whatsnew.history.note', {
        date: dayOf(first).day || '', n: older.length.toLocaleString(),
      })));
      list = el('ol', 'wn-list');
      more = el('button', 'setting-button wn-history-more');
      more.type = 'button';
      more.addEventListener('click', paintPage);
      body.append(list, more);
      paintPage();
    }
  });
}

/** Called when the tab has actually been looked at, never merely rendered. */
export async function markSeen() {
  const { latest } = await releaseSummary(readSeen());
  if (latest) writeSeen(latest);
}
