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
 */

import { CHANGELOG, LATEST_VERSION } from './changelog.js';

const SEEN_KEY = 'chicago4d.whatsnew.seen';

// Not "New" for `feature`: that is also what the unread flag says, and an entry
// reading "NEW … New · Aug 9" makes the two mean nothing. `kind` describes what
// the release WAS; the flag describes whether you have read it.
const KIND_LABEL = { feature: 'Added', fix: 'Fixed', polish: 'Polish' };

function readSeen() {
  try { return Number(window.localStorage.getItem(SEEN_KEY)) || 0; } catch { return 0; }
}

function writeSeen(v) {
  try { window.localStorage.setItem(SEEN_KEY, String(v)); } catch { /* private mode */ }
}

/** Entries the visitor has not been shown yet. */
export function unseenCount(seen = readSeen()) {
  return CHANGELOG.filter((e) => e.v > seen).length;
}

export { LATEST_VERSION };

/**
 * Paint the feed into `host`. Marks entries newer than the visitor's last visit
 * so "what changed since I was last here" is answerable at a glance — which is
 * the only question this panel is really for.
 */
export function renderWhatsNew(host) {
  if (!host) return;
  const seen = readSeen();
  // A first-time visitor has no "last time", so flagging every entry as new
  // marks the whole list and distinguishes nothing. The chip dot still points
  // them here; the per-entry flag is reserved for what it can actually answer.
  const markNew = seen > 0;
  host.textContent = '';

  const list = document.createElement('ol');
  list.className = 'wn-list';

  for (const entry of CHANGELOG) {
    const li = document.createElement('li');
    li.className = 'wn-entry';
    const isNew = markNew && entry.v > seen;
    if (isNew) li.classList.add('is-new');

    const head = document.createElement('div');
    head.className = 'wn-head';

    const title = document.createElement('b');
    title.className = 'wn-title';
    title.textContent = entry.title;
    head.appendChild(title);

    if (isNew) {
      const flag = document.createElement('span');
      flag.className = 'wn-flag';
      flag.textContent = 'new';
      head.appendChild(flag);
    }

    const meta = document.createElement('div');
    meta.className = 'wn-meta';
    // `date` is a Central-Time alias the stamper derives from `ts`; show it as
    // stored rather than re-deriving in the visitor's zone, so what they read
    // matches what every other fleet surface shows for the same release.
    meta.textContent = [KIND_LABEL[entry.kind] || entry.kind, entry.date]
      .filter(Boolean).join(' · ');

    const items = document.createElement('ul');
    items.className = 'wn-items';
    for (const it of entry.items || []) {
      const d = document.createElement('li');
      d.textContent = it;
      items.appendChild(d);
    }

    li.append(head, meta, items);
    list.appendChild(li);
  }

  host.appendChild(list);
}

/** Called when the tab has actually been looked at, never merely rendered. */
export function markSeen() {
  writeSeen(LATEST_VERSION);
}
