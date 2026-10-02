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
 */

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
const KIND_LABEL = { feature: 'Added', fix: 'Fixed', polish: 'Polish' };

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

/**
 * Paint the feed into `host`. Marks entries newer than the visitor's last visit
 * so "what changed since I was last here" is answerable at a glance — which is
 * the only question this panel is really for.
 */
export async function renderWhatsNew(host) {
  if (!host) return;
  const { CHANGELOG } = await loadChangelog();
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
export async function markSeen() {
  const { latest } = await releaseSummary(readSeen());
  if (latest) writeSeen(latest);
}
