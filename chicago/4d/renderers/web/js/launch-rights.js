/**
 * T-3797: launch access. Who may start a cloud machine and who may manage people, by
 * sign-in address, on the Firebase project the sign-in already uses.
 *
 * Firestore (docs/SIGN-IN.md holds the rules, docs/STUDENT-DATA.md every field):
 *
 *   access/<email>   one person's rights, by their sign-in address in lower case, so the
 *                    owner can pre-assign rights before that person ever signs in:
 *                    { email, rights: ['cloud' | 'admin'], note, by, at }
 *   waitlist/<email> a player without cloud play who asked for it: { email, name, year,
 *                    check, at } (the year they had chosen and the system check's verdict,
 *                    so the owner can let in first the people whose computers need it most).
 *                    Letting someone in grants cloud and removes the row in one commit.
 *   launch/cloud     { ready, note, by, at }: whether the cloud machines take players yet.
 *
 * The owner chose rights by email only (2026-11-27): there are no access keys or shared
 * passwords. The rules hold all of it: the owner (the address the published rules carry for
 * OWNER_EMAIL, never in the repository) is an admin by his sign-in; an admin reads and writes
 * grants; only the owner grants or takes away `admin`; a player reads only their own rights.
 * An admin may always start a cloud machine.
 *
 * Every call returns { ok, … } or { ok: false, why } and never throws.
 */

export const RIGHTS = Object.freeze(['cloud', 'admin']);
export const RIGHT_WORD = Object.freeze({ cloud: 'cloud play', admin: 'admin' });
export const NOTE_MAX = 200;

const API = 'https://firestore.googleapis.com/v1';
const root = (projectId) => `projects/${projectId}/databases/(default)/documents`;

// ---- pure ------------------------------------------------------------------------------

export const emailId = (email) => String(email ?? '').trim().toLowerCase();
export const emailOk = (email) => /^[^\s@/]+@[^\s@/]+\.[^\s@/]+$/.test(emailId(email)) && emailId(email).length <= 254;
const clip = (v, max) => (typeof v === 'string' ? v.trim().slice(0, max) : '');
export const cleanRights = (rights) => RIGHTS.filter((r) => (rights ?? []).includes(r));

// Firestore values.
const S = (v) => ({ stringValue: String(v ?? '') });
const B = (v) => ({ booleanValue: !!v });
const L = (list) => ({ arrayValue: { values: list.map(S) } });
function value(v) {
  if ('stringValue' in v) return v.stringValue;
  if ('booleanValue' in v) return v.booleanValue;
  if ('timestampValue' in v) return v.timestampValue;
  if ('integerValue' in v) return Number(v.integerValue);
  if ('arrayValue' in v) return (v.arrayValue.values ?? []).map(value);
  return null;
}
export const plain = (fields = {}) => Object.fromEntries(Object.entries(fields).map(([k, v]) => [k, value(v)]));
const lastPart = (name) => decodeURIComponent(String(name).slice(String(name).lastIndexOf('/') + 1));
const serverTime = (field) => ({ fieldPath: field, setToServerValue: 'REQUEST_TIME' });

/** An admin's grant: rights by email, the time the server's own. */
export function grantWrite(r, { email, rights, note = '', by = '' }) {
  return {
    update: { name: `${r}/access/${emailId(email)}`, fields: { email: S(emailId(email)), rights: L(cleanRights(rights)), note: S(clip(note, NOTE_MAX)), by: S(clip(by, 254)) } },
    updateTransforms: [serverTime('at')],
  };
}
/** A player's own waitlist row. */
export function waitlistWrite(r, { email, name = '', year = '', check = '' }) {
  return {
    update: { name: `${r}/waitlist/${emailId(email)}`, fields: { email: S(emailId(email)), name: S(clip(name, 80)), year: S(clip(year, 4)), check: S(clip(check, 80)) } },
    updateTransforms: [serverTime('at')],
    currentDocument: { exists: false },
  };
}
// ---- the network -----------------------------------------------------------------------

function client({ projectId, account, fetchFn = globalThis.fetch?.bind(globalThis) }) {
  const r = root(projectId);
  const call = async (url, init = {}) => {
    let token;
    try { token = await account.idToken(); } catch { return { ok: false, why: 'not signed in' }; }
    let res;
    try { res = await fetchFn(url, { ...init, headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` } }); }
    catch { return { ok: false, why: 'offline' }; }
    let body = null;
    try { body = await res.json(); } catch { body = null; }
    if (!res.ok) return { ok: false, why: res.status === 404 ? 'missing' : res.status === 403 ? 'refused' : `failed (${res.status})`, status: res.status };
    return { ok: true, body };
  };
  return {
    root: r,
    get: (path) => call(`${API}/${r}/${path.split('/').map(encodeURIComponent).join('/')}`),
    commit: (writes) => call(`${API}/${r}:commit`, { method: 'POST', body: JSON.stringify({ writes }) }),
    list: async (collectionId, limit = 300) => {
      const q = await call(`${API}/${r}:runQuery`, { method: 'POST', body: JSON.stringify({ structuredQuery: { from: [{ collectionId }], limit } }) });
      if (!q.ok) return q;
      return { ok: true, docs: (Array.isArray(q.body) ? q.body : []).map((row) => row.document).filter(Boolean).map((d) => ({ ...plain(d.fields), id: lastPart(d.name) })) };
    },
  };
}
const usable = (account) => Boolean(account?.uid && typeof account.idToken === 'function' && account.method && account.method !== 'email' && account.method !== 'preview');

/** This player's rights. An admin (the owner, or a grant naming admin) may also start the cloud. */
export async function myRights({ projectId, account, fetchFn }) {
  if (!usable(account) || !emailOk(account.email)) return { ok: true, rights: [], admin: false };
  const c = client({ projectId, account, fetchFn });
  const [mine, probe] = await Promise.all([c.get(`access/${emailId(account.email)}`), c.list('access', 1)]);
  if (!mine.ok && mine.why !== 'missing' && mine.why !== 'refused') return mine;
  const had = mine.ok ? cleanRights(plain(mine.body?.fields).rights) : [];
  const admin = probe.ok; // only an admin may list access at all
  const rights = cleanRights([...had, ...(admin ? ['admin', 'cloud'] : [])]);
  let waiting = false;
  if (!rights.includes('cloud')) waiting = (await c.get(`waitlist/${emailId(account.email)}`)).ok;
  return { ok: true, rights, admin, waiting, grant: mine.ok ? plain(mine.body?.fields) : null };
}

/** A signed-in player without cloud play asks for it. Asking twice is the same as once. */
export async function joinWaitlist({ projectId, account, fetchFn, year = '', check = '' }) {
  if (!usable(account) || !emailOk(account.email)) return { ok: false, why: 'sign in' };
  const c = client({ projectId, account, fetchFn });
  const r = await c.commit([waitlistWrite(c.root, { email: account.email, name: account.name, year, check })]);
  if (r.ok) return r;
  // Already on it: the made-new precondition fails (or the rules refuse an update); either way
  // the player's own row says so.
  if ((await c.get(`waitlist/${emailId(account.email)}`)).ok) return { ok: true, already: true };
  return r;
}
/** Off the waitlist: the player themself, or an admin naming `email`. */
export async function leaveWaitlist({ projectId, account, fetchFn, email = account?.email }) {
  const c = client({ projectId, account, fetchFn });
  return c.commit([{ delete: `${c.root}/waitlist/${emailId(email)}` }]);
}
/** Admin: who is waiting, oldest first. */
export async function listWaitlist({ projectId, account, fetchFn }) {
  const r = await client({ projectId, account, fetchFn }).list('waitlist');
  if (!r.ok) return r;
  return { ok: true, waiting: r.docs.map((d) => ({ email: d.id, name: d.name ?? '', year: d.year ?? '', check: d.check ?? '', at: d.at ?? '' }))
    .sort((a, b) => String(a.at).localeCompare(String(b.at))) };
}
/** Admin: let someone in from the waitlist (cloud play, and the row goes, in one commit). */
export async function letIn({ projectId, account, fetchFn, email, note = '' }) {
  if (!emailOk(email)) return { ok: false, why: 'not an email' };
  const c = client({ projectId, account, fetchFn });
  const had = await c.get(`access/${emailId(email)}`);
  const rights = cleanRights([...(had.ok ? plain(had.body?.fields).rights : []), 'cloud']);
  return c.commit([grantWrite(c.root, { email, rights, note: note || (had.ok ? plain(had.body?.fields).note : '') || 'from the waitlist', by: emailId(account.email) }),
    { delete: `${c.root}/waitlist/${emailId(email)}` }]);
}

/** Whether the cloud machines take players yet (launch/cloud; off until the owner says). */
export async function cloudState({ projectId, account, fetchFn }) {
  const c = client({ projectId, account, fetchFn });
  const r = await c.get('launch/cloud');
  if (!r.ok) return { ok: r.why === 'missing', ready: false, note: '' };
  const d = plain(r.body?.fields);
  return { ok: true, ready: d.ready === true, note: d.note ?? '' };
}
export async function setCloudState({ projectId, account, fetchFn, ready, note = '' }) {
  const c = client({ projectId, account, fetchFn });
  return c.commit([{ update: { name: `${c.root}/launch/cloud`, fields: { ready: B(ready), note: S(clip(note, NOTE_MAX)), by: S(emailId(account.email)) } }, updateTransforms: [serverTime('at')] }]);
}

/** Admin: everyone with rights, by email. */
export async function listPeople({ projectId, account, fetchFn }) {
  const r = await client({ projectId, account, fetchFn }).list('access');
  if (!r.ok) return r;
  return { ok: true, people: r.docs.map((d) => ({ email: d.id, rights: cleanRights(d.rights), note: d.note ?? '', by: d.by ?? '', at: d.at ?? '' }))
    .sort((a, b) => a.email.localeCompare(b.email)) };
}
export async function grant({ projectId, account, fetchFn, email, rights, note = '' }) {
  if (!emailOk(email)) return { ok: false, why: 'not an email' };
  const c = client({ projectId, account, fetchFn });
  const list = cleanRights(rights);
  if (!list.length) return c.commit([{ delete: `${c.root}/access/${emailId(email)}` }]);
  return c.commit([grantWrite(c.root, { email, rights: list, note, by: emailId(account.email) })]);
}
export const revoke = (o) => grant({ ...o, rights: [] });
