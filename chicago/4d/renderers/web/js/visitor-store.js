/**
 * T-3576: the visitor list, written and read over Firestore's REST API.
 *
 * Two collections, both in the project's default database:
 *   visitors/<uid>  one document per person: email, name, how they signed in, first and
 *                   last time seen, the years they have entered, and a count of entries.
 *   visits/<id>     one document per year entered: who, which year, when, which device.
 *
 * Every call carries the signed-in visitor's Firebase ID token, and the security rules in
 * docs/SIGN-IN.md let a visitor write only their own rows and let only the owner read.
 * REST rather than the Firestore SDK because the SDK is about a megabyte and this is two
 * writes on entry and two reads on the visitors page.
 */

const docsBase = projectId =>
  `https://firestore.googleapis.com/v1/projects/${encodeURIComponent(projectId)}/databases/(default)/documents`;
const docName = (projectId, path) =>
  `projects/${projectId}/databases/(default)/documents/${path}`;

const str = value => ({ stringValue: String(value ?? '') });

/** A random document id, the same shape Firestore's own auto ids take. */
export function autoId(random = Math.random) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let id = '';
  for (let i = 0; i < 20; i++) id += chars[Math.floor(random() * chars.length)];
  return id;
}

/** What kind of device this is, in the three words the visitors page counts by. */
export function deviceClass(win = globalThis) {
  try {
    const coarse = win.matchMedia?.('(pointer: coarse)').matches || (win.navigator?.maxTouchPoints > 0);
    const short = Math.min(win.screen?.width || 0, win.screen?.height || 0);
    if (coarse && short && short < 600) return 'phone';
    if (coarse) return 'tablet';
  } catch { /* an old browser: call it a computer */ }
  return 'computer';
}

async function commit(projectId, idToken, writes, fetchFn = fetch) {
  const res = await fetchFn(`${docsBase(projectId)}:commit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${idToken}` },
    body: JSON.stringify({ writes }),
  });
  return res;
}

/**
 * The commits that record one entry into a year. Exported for the self-test, which
 * holds their shape to the field list the security rules allow.
 */
export function entryWrites({ projectId, uid, email, name, method, year, device, visitId }) {
  const visitor = docName(projectId, `visitors/${uid}`);
  const person = { email: str(email), name: str(name), method: str(method) };
  return {
    // Only lands the first time (the document must not exist yet).
    first: [{
      update: { name: visitor, fields: { ...person, firstYear: str(year) } },
      updateTransforms: [{ fieldPath: 'firstSeen', setToServerValue: 'REQUEST_TIME' }],
      currentDocument: { exists: false },
    }],
    every: [{
      update: { name: visitor, fields: { ...person, lastYear: str(year), lastDevice: str(device) } },
      updateMask: { fieldPaths: ['email', 'name', 'method', 'lastYear', 'lastDevice'] },
      updateTransforms: [
        { fieldPath: 'lastSeen', setToServerValue: 'REQUEST_TIME' },
        { fieldPath: 'visits', increment: { integerValue: '1' } },
        { fieldPath: 'years', appendMissingElements: { values: [str(year)] } },
      ],
    }, {
      update: {
        name: docName(projectId, `visits/${visitId}`),
        fields: { uid: str(uid), email: str(email), method: str(method), year: str(year), device: str(device) },
      },
      updateTransforms: [{ fieldPath: 'at', setToServerValue: 'REQUEST_TIME' }],
      currentDocument: { exists: false },
    }],
  };
}

/** Record one entry into a year. Never throws: the list is for the owner, not the door. */
export async function recordEntry({ projectId, idToken, fetchFn = fetch, ...entry }) {
  try {
    const writes = entryWrites({ projectId, visitId: autoId(), ...entry });
    // The first write is refused (FAILED_PRECONDITION) on every visit after the first,
    // which is the point; it only ever lands once.
    await commit(projectId, idToken, writes.first, fetchFn).catch(() => null);
    const res = await commit(projectId, idToken, writes.every, fetchFn);
    if (!res.ok) console.warn('[4D Chicago] sign-in: visit not recorded', res.status);
    return res.ok;
  } catch (err) {
    console.warn('[4D Chicago] sign-in: visit not recorded', err);
    return false;
  }
}

/** A Firestore REST value, as plain JavaScript. */
export function fromValue(value) {
  if (!value || typeof value !== 'object') return null;
  if ('stringValue' in value) return value.stringValue;
  if ('integerValue' in value) return Number(value.integerValue);
  if ('doubleValue' in value) return value.doubleValue;
  if ('booleanValue' in value) return value.booleanValue;
  if ('timestampValue' in value) return value.timestampValue;
  if ('nullValue' in value) return null;
  if ('arrayValue' in value) return (value.arrayValue.values || []).map(fromValue);
  if ('mapValue' in value) return fromFields(value.mapValue.fields);
  return null;
}
export function fromFields(fields = {}) {
  const out = {};
  for (const [key, value] of Object.entries(fields || {})) out[key] = fromValue(value);
  return out;
}

async function runQuery(projectId, idToken, structuredQuery, fetchFn = fetch) {
  const res = await fetchFn(`${docsBase(projectId)}:runQuery`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${idToken}` },
    body: JSON.stringify({ structuredQuery }),
  });
  if (res.status === 403 || res.status === 401) {
    const err = new Error('This account cannot read the visitor list.');
    err.code = 'denied';
    throw err;
  }
  if (!res.ok) throw new Error(`The visitor list did not load (${res.status}).`);
  const rows = await res.json();
  return rows.filter(row => row.document).map(row => ({
    id: row.document.name.split('/').pop(),
    ...fromFields(row.document.fields),
  }));
}

/** Everyone who has come in, most recent first. Owner only (the rules say so). */
export async function listVisitors({ projectId, idToken, fetchFn = fetch }) {
  const rows = await runQuery(projectId, idToken, { from: [{ collectionId: 'visitors' }], limit: 10000 }, fetchFn);
  return rows.sort((a, b) => String(b.lastSeen || b.firstSeen || '').localeCompare(String(a.lastSeen || a.firstSeen || '')));
}

/** Every year entered since a date, most recent first. Owner only. */
export async function listVisits({ projectId, idToken, since, fetchFn = fetch }) {
  return runQuery(projectId, idToken, {
    from: [{ collectionId: 'visits' }],
    where: { fieldFilter: { field: { fieldPath: 'at' }, op: 'GREATER_THAN_OR_EQUAL', value: { timestampValue: since.toISOString() } } },
    orderBy: [{ field: { fieldPath: 'at' }, direction: 'DESCENDING' }],
    limit: 10000,
  }, fetchFn);
}
