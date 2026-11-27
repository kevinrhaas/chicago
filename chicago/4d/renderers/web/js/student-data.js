/**
 * T-3776: what the app keeps on a signed-in visitor's account, and the way to delete it.
 *
 * Stage 1 of the owner's server plan (2026-11-26) puts student work on Firebase, so the
 * policy comes first: docs/STUDENT-DATA.md says field by field what is kept and why, the
 * visitor's page (privacy.html) says it in plain words, and Settings › About gains
 * **Delete my saved data**, which removes every record this account owns.
 *
 * Three shapes of record, all in Firestore's default database (nam5):
 *   ACCOUNT_DOCS  one document per account, keyed by its uid
 *   ACCOUNT_ROWS  many rows per account, each carrying `uid`
 *   ACCOUNT_TREES documents under users/<uid>/<part>/ (T-3777 cloud save)
 * The rules in docs/SIGN-IN.md let the account read and delete exactly these (and the
 * owner, his visitor list). A new collection that holds a visitor's data is added HERE and
 * to the rules in the same change; tools/test_sign_in.mjs holds the two lists together.
 *
 * `cloudFeatures` (js/sign-in-config.js) is the one switch every later Stage 1 feature
 * (cloud save, classes, shared routes, follow the teacher) checks before it writes a byte.
 * It stays off until this policy has been read by the owner and a school has the
 * agreement (docs/STUDENT-DATA-AGREEMENT.md).
 */

/** Documents keyed by the account's uid: readers (reading age), people (your own person),
 * visitors (the owner's visitor list: your email, how you signed in, when, which years). */
export const ACCOUNT_DOCS = Object.freeze(['readers', 'people', 'visitors']);
/** Rows that carry the account's uid: visits (one per year entered), bugs (your reports). */
export const ACCOUNT_ROWS = Object.freeze(['visits', 'bugs']);

/** Trees under users/<uid>/: T-3777's cloud save (js/cloud-save.js CLOUD_PARTS). */
export const ACCOUNT_TREES = Object.freeze({ users: Object.freeze(['notebook', 'metfound', 'settings']) });

/** Is any Stage 1 cloud feature allowed to write? Off unless the config says so. */
export function cloudFeaturesOn(config) {
  return Boolean(config?.enabled && config?.cloudFeatures === true);
}

const docsBase = (projectId) =>
  `https://firestore.googleapis.com/v1/projects/${encodeURIComponent(projectId)}/databases/(default)/documents`;
const docName = (projectId, path) => `projects/${projectId}/databases/(default)/documents/${path}`;

/** The query for one collection's rows that belong to this uid, a page at a time. */
export function rowsQuery(collectionId, uid, limit = 300) {
  return {
    from: [{ collectionId }],
    where: { fieldFilter: { field: { fieldPath: 'uid' }, op: 'EQUAL', value: { stringValue: String(uid) } } },
    select: { fields: [{ fieldPath: 'uid' }] },
    limit,
  };
}

/**
 * Delete everything this account has saved. Returns { deleted, failed }: how many
 * records went, and the collections that refused (a rule not yet published, offline).
 * Never throws; a refused part is reported, the rest still goes.
 */
export async function deleteMyData({ projectId, account, fetchFn = globalThis.fetch?.bind(globalThis) } = {}) {
  if (!projectId || !account?.uid || typeof account.idToken !== 'function' || !fetchFn) {
    return { deleted: 0, failed: ['not signed in'] };
  }
  const base = docsBase(projectId);
  const uid = account.uid;
  let deleted = 0;
  const failed = [];
  let token;
  try { token = await account.idToken(); } catch { return { deleted: 0, failed: ['not signed in'] }; }
  const auth = { Authorization: `Bearer ${token}` };

  for (const collection of ACCOUNT_DOCS) {
    try {
      const res = await fetchFn(`${base}/${collection}/${encodeURIComponent(uid)}`, { method: 'DELETE', headers: auth });
      // Firestore answers a delete of a missing document with 200 as well.
      if (res.ok) deleted += 1; else failed.push(collection);
    } catch { failed.push(collection); }
  }
  for (const collection of ACCOUNT_ROWS) {
    try {
      // A page at a time, until a page comes back empty (bounded, so a fault cannot spin).
      for (let page = 0; page < 50; page++) {
        const res = await fetchFn(`${base}:runQuery`, {
          method: 'POST', headers: { ...auth, 'Content-Type': 'application/json' },
          body: JSON.stringify({ structuredQuery: rowsQuery(collection, uid) }),
        });
        if (!res.ok) { failed.push(collection); break; }
        const names = (await res.json()).map((row) => row.document?.name).filter(Boolean);
        if (!names.length) break;
        const commit = await fetchFn(`${base}:commit`, {
          method: 'POST', headers: { ...auth, 'Content-Type': 'application/json' },
          body: JSON.stringify({ writes: names.map((name) => ({ delete: name })) }),
        });
        if (!commit.ok) { failed.push(collection); break; }
        deleted += names.length;
      }
    } catch { failed.push(collection); }
  }
  for (const [tree, parts] of Object.entries(ACCOUNT_TREES)) {
    for (const part of parts) {
      try {
        for (let page = 0; page < 50; page++) {
          const res = await fetchFn(`${base}/${tree}/${encodeURIComponent(uid)}:runQuery`, {
            method: 'POST', headers: { ...auth, 'Content-Type': 'application/json' },
            body: JSON.stringify({ structuredQuery: { from: [{ collectionId: part }], select: { fields: [{ fieldPath: '__name__' }] }, limit: 300 } }),
          });
          if (!res.ok) { failed.push(`${tree}/${part}`); break; }
          const names = (await res.json()).map((row) => row.document?.name).filter(Boolean);
          if (!names.length) break;
          const commit = await fetchFn(`${base}:commit`, {
            method: 'POST', headers: { ...auth, 'Content-Type': 'application/json' },
            body: JSON.stringify({ writes: names.map((name) => ({ delete: name })) }),
          });
          if (!commit.ok) { failed.push(`${tree}/${part}`); break; }
          deleted += names.length;
        }
      } catch { failed.push(`${tree}/${part}`); }
    }
  }
  return { deleted, failed };
}

/** The name a row's document has, for the tests. */
export const accountDocName = (projectId, collection, uid) => docName(projectId, `${collection}/${uid}`);

const DONE = 'Deleted, and signed out. Signing in again starts a new record.';
const PARTLY = 'Some of it could not be deleted just now. Try again in a minute.';

/**
 * Settings › About: "Your saved data", with the delete button and its inline confirm.
 * Hidden unless someone is signed in. Exported for tools/test_sign_in.mjs.
 */
export function showSavedData(doc, account, { projectId, deleteFn = deleteMyData, after = () => {} } = {}) {
  const box = doc?.getElementById?.('s-saved-data');
  if (!box) return false;
  if (!account?.uid) { box.hidden = true; return false; }
  const button = doc.getElementById('s-delete-data');
  const confirm = doc.getElementById('s-delete-data-confirm');
  const yes = doc.getElementById('s-delete-data-yes');
  const no = doc.getElementById('s-delete-data-no');
  const status = doc.getElementById('s-delete-data-status');
  const say = (text) => { if (status) status.textContent = text; };
  if (button) {
    button.onclick = () => {
      if (confirm) confirm.hidden = false;
      button.hidden = true;
      say('');
      yes?.focus?.();
    };
  }
  if (no) {
    no.onclick = () => {
      if (confirm) confirm.hidden = true;
      if (button) { button.hidden = false; button.focus?.(); }
    };
  }
  if (yes) {
    yes.onclick = async () => {
      yes.disabled = true;
      if (no) no.disabled = true;
      say('Deleting…');
      const result = await deleteFn({ projectId, account });
      yes.disabled = false;
      if (no) no.disabled = false;
      if (confirm) confirm.hidden = true;
      if (button) button.hidden = false;
      say(result.failed.length ? PARTLY : DONE);
      if (!result.failed.length) after(result);
    };
  }
  box.hidden = false;
  return true;
}
