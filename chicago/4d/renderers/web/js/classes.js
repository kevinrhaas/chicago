/**
 * T-3778: class codes and a teacher view (classroom feature 6).
 *
 * Stage 1 of the owner's server plan (2026-11-26), behind T-3776's `cloudFeatures` switch
 * (js/student-data.js). A signed-in teacher makes a class and gets a short join code; a
 * student types the code once and is in the class on every device they sign in on; the
 * teacher's page lists who joined, when each was last in, and what each chose to hand in
 * from the field notebook. No grades, scores or leaderboards: nothing here ranks anyone.
 *
 * Firestore (docs/SIGN-IN.md holds the rules, docs/STUDENT-DATA.md every field):
 *
 *   classes/<classId>                     the class: its teacher, name, year group, code, open
 *   classes/<classId>/members/<uid>       one student: the name they gave, joined, last in
 *   classes/<classId>/handins/<uid>_<id>  one notebook entry that student handed in
 *   codes/<code>                          the join code: which class, until when (read by
 *                                         name only, never listed)
 *   users/<uid>/classes/<classId>         the student's own note of the class they are in,
 *                                         so another device finds it (cloud save's shape)
 *
 * The rules check every one of those: only the class's teacher reads its roster and
 * hand-ins, a student reads only their own, a member row is written only with a live code
 * for that class, and never from a sign-in with the email alone (anyone could type one).
 *
 * The pure half (codes, the writes, CSV and the printed sheet) is exported for
 * tools/test_classes.mjs; the network half takes `fetchFn` so the test can stand a fake
 * Firestore in front of it. Every call returns { ok, … } or { ok: false, why } and never
 * throws: a refused or offline call leaves the page as it was and says so.
 */

import { cloudFeaturesOn } from './student-data.js';

/** Join-code letters: no vowels (so no words), and none that read alike (0 O 1 I L S 5 U). */
export const CODE_ALPHABET = 'BCDFGHJKMNPQRTVWXYZ2346789';
export const CODE_LENGTH = 6;
/** How long a code admits new students. The teacher can make a new one at any time. */
export const CODE_DAYS = 30;
/** Letter runs a code may not hold even without vowels. */
const BLOCKED = ['FCK', 'FKN', 'KKK', 'CNT', 'NGR', 'NGG', 'PHK', 'FGT', 'WTF', 'DCK', 'KKN'];
export const CLASS_LIMITS = Object.freeze({ name: 80, group: 40, teacherName: 80, studentName: 60, title: 200, v: 400000, classes: 20, students: 60 });
/** Year groups a class can name (the reading ages the app writes for). */
export const YEAR_GROUPS = Object.freeze(['3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'adult']);
/** What a hand-in is: a notebook entry, and whether it is a reflection (topic). */
export const REFLECTION_TOPICS = Object.freeze(['reflection', 'case']);

// ---------------------------------------------------------------------------------------
// Codes (pure)
// ---------------------------------------------------------------------------------------

const unbiased = (random, n) => {
  // random() in [0, 1); a whole index below n.
  const i = Math.floor(random() * n);
  return i >= 0 && i < n ? i : 0;
};
const cryptoRandom = () => {
  const c = globalThis.crypto;
  if (c?.getRandomValues) { const a = new Uint32Array(1); c.getRandomValues(a); return a[0] / 4294967296; }
  return Math.random();
};

/** Is this a code the app could have made? (Shape only: the account says whether it is live.) */
export function codeOk(code) {
  if (typeof code !== 'string' || code.length !== CODE_LENGTH) return false;
  if ([...code].some((ch) => !CODE_ALPHABET.includes(ch))) return false;
  return !BLOCKED.some((run) => code.includes(run));
}
/** A new code. */
export function makeCode(random = cryptoRandom) {
  for (let tries = 0; tries < 50; tries++) {
    let code = '';
    for (let i = 0; i < CODE_LENGTH; i++) code += CODE_ALPHABET[unbiased(random, CODE_ALPHABET.length)];
    if (codeOk(code)) return code;
  }
  return 'BCDFGH';
}
/** What a student typed, as a code: case, spaces and the dash folded away. */
export const typedCode = (text) => String(text ?? '').toUpperCase().replace(/[\s-]+/g, '').slice(0, 12);
/** A code as it is shown and read aloud: BCD-FGH. */
export const shownCode = (code) => (code ? `${code.slice(0, 3)}-${code.slice(3)}` : '');
/** A document id: 20 letters and digits. */
export function makeId(random = cryptoRandom) {
  const abc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let id = '';
  for (let i = 0; i < 20; i++) id += abc[unbiased(random, abc.length)];
  return id;
}

const clip = (v, max) => (typeof v === 'string' ? v.trim().slice(0, max) : '');

// ---------------------------------------------------------------------------------------
// Firestore over REST
// ---------------------------------------------------------------------------------------

const API = 'https://firestore.googleapis.com/v1';
export const docsRoot = (projectId) => `projects/${projectId}/databases/(default)/documents`;
const S = (v) => ({ stringValue: String(v ?? '') });
const B = (v) => ({ booleanValue: Boolean(v) });
const T = (iso) => ({ timestampValue: iso });

/** A Firestore document's fields as plain values. */
export function plain(fields = {}) {
  const out = {};
  for (const [k, v] of Object.entries(fields)) {
    if ('stringValue' in v) out[k] = v.stringValue;
    else if ('booleanValue' in v) out[k] = v.booleanValue;
    else if ('timestampValue' in v) out[k] = v.timestampValue;
    else if ('integerValue' in v) out[k] = Number(v.integerValue);
    else if ('nullValue' in v) out[k] = null;
  }
  return out;
}
const lastPart = (name) => String(name).slice(String(name).lastIndexOf('/') + 1);

/** May this account use classes? A real sign-in, with the cloud features on. */
export function classesFor(account, config) {
  return Boolean(cloudFeaturesOn(config) && account?.uid && typeof account.idToken === 'function'
    && account.method && account.method !== 'email' && account.method !== 'preview');
}

function client({ projectId, account, fetchFn = globalThis.fetch?.bind(globalThis) }) {
  const root = docsRoot(projectId);
  const call = async (url, init = {}) => {
    let token;
    try { token = await account.idToken(); } catch { return { ok: false, why: 'not signed in' }; }
    let res;
    try {
      res = await fetchFn(url, { ...init, headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...(init.headers ?? {}) } });
    } catch { return { ok: false, why: 'offline' }; }
    let body = null;
    try { body = await res.json(); } catch { body = null; }
    if (!res.ok) return { ok: false, why: res.status === 404 ? 'missing' : res.status === 403 ? 'refused' : `failed (${res.status})`, status: res.status, body };
    return { ok: true, body };
  };
  return {
    root,
    name: (path) => `${root}/${path}`,
    get: (path) => call(`${API}/${root}/${path}`),
    commit: (writes) => call(`${API}/${root}:commit`, { method: 'POST', body: JSON.stringify({ writes }) }),
    query: async (parent, structuredQuery) => {
      const r = await call(`${API}/${root}${parent ? `/${parent}` : ''}:runQuery`, { method: 'POST', body: JSON.stringify({ structuredQuery }) });
      if (!r.ok) return r;
      return { ok: true, docs: (Array.isArray(r.body) ? r.body : []).map((row) => row.document).filter(Boolean)
        .map((d) => ({ ...plain(d.fields), id: lastPart(d.name), path: d.name })) };
    },
  };
}

const where = (field, value) => ({ fieldFilter: { field: { fieldPath: field }, op: 'EQUAL', value: S(value) } });

// ---- the writes (pure, so the test can hold them to the rules) ---------------------------

/** The class document. */
export function classWrite(root, cls, { create = false } = {}) {
  const w = {
    update: {
      name: `${root}/classes/${cls.id}`,
      fields: {
        teacher: S(cls.teacher), teacherName: S(clip(cls.teacherName, CLASS_LIMITS.teacherName)),
        name: S(clip(cls.name, CLASS_LIMITS.name)), group: S(clip(cls.group, CLASS_LIMITS.group)),
        code: S(cls.code), open: B(cls.open),
      },
    },
  };
  // Made new: the server stamps createdAt. Changed later: only these fields are sent, so
  // createdAt stays as the server first wrote it (the rules hold it unchanged).
  if (create) { w.currentDocument = { exists: false }; w.updateTransforms = [{ fieldPath: 'createdAt', setToServerValue: 'REQUEST_TIME' }]; }
  else { w.currentDocument = { exists: true }; w.updateMask = { fieldPaths: Object.keys(w.update.fields) }; }
  return w;
}
/** The join code's document: made new, never overwritten (a clash tries another code). */
export function codeWrite(root, cls, expires) {
  return {
    update: {
      name: `${root}/codes/${cls.code}`,
      fields: {
        classId: S(cls.id), teacher: S(cls.teacher), className: S(clip(cls.name, CLASS_LIMITS.name)),
        teacherName: S(clip(cls.teacherName, CLASS_LIMITS.teacherName)), expires: T(expires),
      },
    },
    currentDocument: { exists: false },
    updateTransforms: [{ fieldPath: 'at', setToServerValue: 'REQUEST_TIME' }],
  };
}
/** A student's member row, written when they join. */
export function memberWrite(root, classId, uid, name, code) {
  return {
    update: { name: `${root}/classes/${classId}/members/${uid}`, fields: { uid: S(uid), name: S(clip(name, CLASS_LIMITS.studentName)), code: S(code) } },
    currentDocument: { exists: false },
    updateTransforms: [
      { fieldPath: 'joinedAt', setToServerValue: 'REQUEST_TIME' },
      { fieldPath: 'lastIn', setToServerValue: 'REQUEST_TIME' },
    ],
  };
}
/** "Last in", moved on a visit (only that field changes). */
export function lastInWrite(root, classId, uid) {
  return {
    transform: { document: `${root}/classes/${classId}/members/${uid}`, fieldTransforms: [{ fieldPath: 'lastIn', setToServerValue: 'REQUEST_TIME' }] },
    currentDocument: { exists: true },
  };
}
/** The student's own note of their class (users/<uid>/classes/<classId>, cloud save's shape). */
export function mineWrite(root, uid, cls, value) {
  return {
    update: {
      name: `${root}/users/${uid}/classes/${cls.id ?? cls}`,
      fields: value === undefined ? { v: S(''), deleted: B(true) } : { v: S(JSON.stringify(value)), deleted: B(false) },
    },
    updateTransforms: [{ fieldPath: 'at', setToServerValue: 'REQUEST_TIME' }],
  };
}
/** One notebook entry handed in. */
export function handinWrite(root, classId, uid, studentName, entry) {
  const v = JSON.stringify(entry);
  return {
    update: {
      name: `${root}/classes/${classId}/handins/${uid}_${entry.id}`,
      fields: {
        uid: S(uid), name: S(clip(studentName, CLASS_LIMITS.studentName)), entryId: S(entry.id), kind: S(entry.kind),
        topic: S(entry.topic ?? ''), title: S(clip(entry.title, CLASS_LIMITS.title)), v: S(v),
      },
    },
    updateTransforms: [{ fieldPath: 'at', setToServerValue: 'REQUEST_TIME' }],
  };
}

// ---- the teacher -----------------------------------------------------------------------

const daysOn = (now, days) => new Date(Date.parse(now) + days * 86400000).toISOString();

/** Make a class and its code. Returns { ok, cls } (cls.code, cls.expires). */
export async function makeClass({ projectId, account, fetchFn, name, group, teacherName, random = cryptoRandom, now = () => new Date().toISOString() }) {
  const c = client({ projectId, account, fetchFn });
  const cls = { id: makeId(random), teacher: account.uid, teacherName: clip(teacherName, CLASS_LIMITS.teacherName),
    name: clip(name, CLASS_LIMITS.name), group: clip(group, CLASS_LIMITS.group), open: true };
  if (!cls.name) return { ok: false, why: 'no name' };
  for (let tries = 0; tries < 5; tries++) {
    cls.code = makeCode(random);
    const expires = daysOn(now(), CODE_DAYS);
    const r = await c.commit([classWrite(c.root, cls, { create: true }), codeWrite(c.root, cls, expires)]);
    if (r.ok) return { ok: true, cls: { ...cls, expires, createdAt: now(), members: [], handins: [] } };
    // 409/400 FAILED_PRECONDITION: that code (or id) is taken; try another.
    if (r.status !== 409 && r.status !== 400) return r;
    cls.id = makeId(random);
  }
  return { ok: false, why: 'no free code' };
}

/** The classes this account teaches, newest first, each with its code's expiry. */
export async function myClasses({ projectId, account, fetchFn }) {
  const c = client({ projectId, account, fetchFn });
  const r = await c.query('', { from: [{ collectionId: 'classes' }], where: where('teacher', account.uid), limit: CLASS_LIMITS.classes * 2 });
  if (!r.ok) return r;
  const classes = r.docs.sort((a, b) => String(b.createdAt).localeCompare(String(a.createdAt)));
  for (const cls of classes) {
    if (!cls.open || !cls.code) continue;
    const code = await c.get(`codes/${cls.code}`);
    cls.expires = code.ok ? plain(code.body?.fields).expires ?? '' : '';
  }
  return { ok: true, classes };
}

/** One class's roster and hand-ins (the teacher's page). */
export async function classRoster({ projectId, account, fetchFn, cls }) {
  const c = client({ projectId, account, fetchFn });
  const members = await c.query(`classes/${cls.id}`, { from: [{ collectionId: 'members' }], limit: 300 });
  if (!members.ok) return members;
  const handins = await c.query(`classes/${cls.id}`, { from: [{ collectionId: 'handins' }], limit: 1000 });
  if (!handins.ok) return handins;
  const entries = handins.docs.map((h) => { let entry = null; try { entry = JSON.parse(h.v); } catch { entry = null; } return { ...h, entry }; });
  return { ok: true, members: members.docs.sort((a, b) => String(a.name).localeCompare(String(b.name))), handins: entries };
}

/** A new code for an open class; the old one stops admitting at once. */
export async function newCode({ projectId, account, fetchFn, cls, random = cryptoRandom, now = () => new Date().toISOString() }) {
  const c = client({ projectId, account, fetchFn });
  for (let tries = 0; tries < 5; tries++) {
    const next = { ...cls, code: makeCode(random) };
    const expires = daysOn(now(), CODE_DAYS);
    const r = await c.commit([
      ...(cls.code ? [{ delete: c.name(`codes/${cls.code}`) }] : []),
      classWrite(c.root, next), codeWrite(c.root, next, expires),
    ]);
    if (r.ok) return { ok: true, cls: { ...next, expires } };
    if (r.status !== 409 && r.status !== 400) return r;
  }
  return { ok: false, why: 'no free code' };
}

/** Close a class: it and everything in it go (members, hand-ins, its code), as the school
 * agreement says (docs/STUDENT-DATA-AGREEMENT.md § Deletion). The teacher's page offers the
 * CSV and the printed sheet first. */
export async function closeClass({ projectId, account, fetchFn, cls }) {
  const c = client({ projectId, account, fetchFn });
  const roster = await classRoster({ projectId, account, fetchFn, cls });
  if (!roster.ok) return roster;
  const names = [
    ...roster.handins.map((h) => h.path), ...roster.members.map((m) => m.path),
    ...(cls.code ? [c.name(`codes/${cls.code}`)] : []), c.name(`classes/${cls.id}`),
  ];
  const deleted = await deleteNames(c, names);
  return deleted.ok ? { ok: true, deleted: names.length } : deleted;
}

/** Remove one student and what they handed in. */
export async function removeStudent({ projectId, account, fetchFn, cls, uid }) {
  const c = client({ projectId, account, fetchFn });
  const roster = await classRoster({ projectId, account, fetchFn, cls });
  if (!roster.ok) return roster;
  const names = [...roster.handins.filter((h) => h.uid === uid).map((h) => h.path), c.name(`classes/${cls.id}/members/${uid}`)];
  return deleteNames(c, names);
}

async function deleteNames(c, names) {
  for (let i = 0; i < names.length; i += 400) {
    const r = await c.commit(names.slice(i, i + 400).map((name) => ({ delete: name })));
    if (!r.ok) return r;
  }
  return { ok: true };
}

// ---- the student -------------------------------------------------------------------------

/** What a code admits to, before joining: { ok, code: { classId, className, teacherName, expires } }. */
export async function lookUpCode({ projectId, account, fetchFn, code, now = () => new Date().toISOString() }) {
  if (!codeOk(code)) return { ok: false, why: 'not a code' };
  const c = client({ projectId, account, fetchFn });
  const r = await c.get(`codes/${code}`);
  if (!r.ok) return r.why === 'missing' ? { ok: false, why: 'no such code' } : r;
  const found = { code, ...plain(r.body?.fields) };
  if (!(found.expires > now())) return { ok: false, why: 'expired' };
  return { ok: true, code: found };
}

/** Join with a code, under the name the student gives their teacher. One class at a time. */
export async function joinClass({ projectId, account, fetchFn, code, name, now = () => new Date().toISOString() }) {
  const student = clip(name, CLASS_LIMITS.studentName);
  if (!student) return { ok: false, why: 'no name' };
  const look = await lookUpCode({ projectId, account, fetchFn, code, now });
  if (!look.ok) return look;
  const c = client({ projectId, account, fetchFn });
  const found = look.code;
  const mine = { classId: found.classId, className: found.className, teacherName: found.teacherName, name: student, joinedAt: now() };
  const r = await c.commit([memberWrite(c.root, found.classId, account.uid, student, code), mineWrite(c.root, account.uid, found.classId, mine)]);
  if (!r.ok) return r.status === 409 || r.status === 400 ? { ok: false, why: 'already in' } : r;
  return { ok: true, mine };
}

/**
 * The class this student is in, read on every visit: { ok, mine | null, handed, why? }.
 * `handed` maps an entry id to the hand-in's { at, h }. A class the student was removed
 * from, or that the teacher closed (which deletes it), is forgotten here and the reason
 * given once. (`closed` marks a class whose `open` is false, which the page never writes.)
 */
export async function myClass({ projectId, account, fetchFn, touch = true }) {
  const c = client({ projectId, account, fetchFn });
  const notes = await c.query(`users/${account.uid}`, { from: [{ collectionId: 'classes' }], limit: 20 });
  if (!notes.ok) return notes;
  const live = notes.docs.filter((d) => !d.deleted).map((d) => { try { return JSON.parse(d.v); } catch { return null; } }).filter((m) => m?.classId);
  if (!live.length) return { ok: true, mine: null, handed: new Map() };
  const mine = live.sort((a, b) => String(b.joinedAt).localeCompare(String(a.joinedAt)))[0];
  const member = await c.get(`classes/${mine.classId}/members/${account.uid}`);
  if (!member.ok) {
    if (member.why !== 'missing' && member.why !== 'refused') return member;
    // Removed by the teacher, or the class deleted: the note goes, and the student is told.
    await c.commit([mineWrite(c.root, account.uid, mine.classId, undefined)]);
    return { ok: true, mine: null, gone: mine, handed: new Map() };
  }
  const cls = await c.get(`classes/${mine.classId}`);
  const clsData = cls.ok ? plain(cls.body?.fields) : {};
  const handins = await c.query(`classes/${mine.classId}`, { from: [{ collectionId: 'handins' }], where: where('uid', account.uid), limit: 200 });
  const handed = new Map((handins.ok ? handins.docs : []).map((h) => [h.entryId, { at: h.at, h: h.v }]));
  const out = { ...mine, name: plain(member.body?.fields).name ?? mine.name, closed: clsData.open === false,
    className: clsData.name || mine.className, teacherName: clsData.teacherName || mine.teacherName };
  if (touch && !out.closed) {
    const last = plain(member.body?.fields).lastIn ?? '';
    if (!last || Date.now() - Date.parse(last) > 30 * 60000) await c.commit([lastInWrite(c.root, mine.classId, account.uid)]);
  }
  return { ok: true, mine: out, handed };
}

/** Leave the class: the member row, what was handed in, and the note on the account go. */
export async function leaveClass({ projectId, account, fetchFn, mine }) {
  const c = client({ projectId, account, fetchFn });
  const handins = await c.query(`classes/${mine.classId}`, { from: [{ collectionId: 'handins' }], where: where('uid', account.uid), limit: 300 });
  const names = [...(handins.ok ? handins.docs.map((h) => h.path) : []), c.name(`classes/${mine.classId}/members/${account.uid}`)];
  const r = await c.commit([...names.map((name) => ({ delete: name })), mineWrite(c.root, account.uid, mine.classId, undefined)]);
  return r.ok ? { ok: true } : r;
}

/** Hand one notebook entry in (again, after an edit, replaces it). */
export async function handIn({ projectId, account, fetchFn, mine, entry }) {
  const c = client({ projectId, account, fetchFn });
  const w = handinWrite(c.root, mine.classId, account.uid, mine.name, entry);
  if (w.update.fields.v.stringValue.length > CLASS_LIMITS.v) return { ok: false, why: 'too big' };
  const r = await c.commit([w]);
  return r.ok ? { ok: true, h: w.update.fields.v.stringValue } : r;
}
/** Take a hand-in back. */
export async function takeBack({ projectId, account, fetchFn, mine, entryId }) {
  const c = client({ projectId, account, fetchFn });
  const r = await c.commit([{ delete: c.name(`classes/${mine.classId}/handins/${account.uid}_${entryId}`) }]);
  return r.ok ? { ok: true } : r;
}

/**
 * Delete my saved data, the class half: a student's member rows and hand-ins, and every
 * class this account teaches with all it holds. Called by js/student-data.js before the
 * account's own tree goes (that tree is how a student's classes are found).
 */
export async function deleteClassData({ projectId, account, fetchFn }) {
  const c = client({ projectId, account, fetchFn });
  let deleted = 0;
  const failed = [];
  const notes = await c.query(`users/${account.uid}`, { from: [{ collectionId: 'classes' }], limit: 50 });
  if (!notes.ok) failed.push('classes/members');
  else {
    for (const note of notes.docs) {
      const classId = note.id;
      const handins = await c.query(`classes/${classId}`, { from: [{ collectionId: 'handins' }], where: where('uid', account.uid), limit: 300 });
      const names = [...(handins.ok ? handins.docs.map((h) => h.path) : [])];
      const member = await c.get(`classes/${classId}/members/${account.uid}`);
      if (member.ok) names.push(member.body.name);
      if (!names.length) continue;
      const r = await deleteNames(c, names);
      if (r.ok) deleted += names.length; else failed.push('classes/members');
    }
  }
  const taught = await myClasses({ projectId, account, fetchFn });
  if (!taught.ok) failed.push('classes');
  else {
    for (const cls of taught.classes) {
      const r = await closeClass({ projectId, account, fetchFn, cls });
      if (r.ok) deleted += r.deleted; else failed.push('classes');
    }
  }
  return { deleted, failed: [...new Set(failed)] };
}

// ---------------------------------------------------------------------------------------
// The teacher's sheet: CSV and print (pure)
// ---------------------------------------------------------------------------------------

const isReflection = (h) => REFLECTION_TOPICS.includes(h.topic ?? h.entry?.topic ?? '');

/** Per student: { member, handins, reflections } in roster order. */
export function rosterRows(members, handins) {
  return members.map((member) => {
    const theirs = handins.filter((h) => h.uid === member.uid).sort((a, b) => String(a.at).localeCompare(String(b.at)));
    return { member, handins: theirs, reflections: theirs.filter(isReflection).length };
  });
}

const csvCell = (v) => {
  let s = String(v ?? '');
  // A cell a spreadsheet would run as a formula is kept as text.
  if (/^[=+\-@\t\r]/.test(s)) s = `'${s}`;
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};
/** The class as CSV: one row per hand-in, and one for each student with none. */
export function classCSV(cls, members, handins, { head, clock = (iso) => iso, kindName = (k) => k }) {
  const lines = [head.map(csvCell).join(',')];
  for (const row of rosterRows(members, handins)) {
    const m = row.member;
    const base = [m.name, clock(m.joinedAt), clock(m.lastIn)];
    if (!row.handins.length) { lines.push([...base, '', '', '', '', '', ''].map(csvCell).join(',')); continue; }
    for (const h of row.handins) {
      const e = h.entry ?? {};
      lines.push([...base, kindName(h), e.title || h.title, e.year ?? '', e.place ?? '', clock(h.at), e.text ?? ''].map(csvCell).join(','));
    }
  }
  return `${lines.join('\r\n')}\r\n`;
}

const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
const photoOk = (p) => typeof p === 'string' && /^data:image\/(jpeg|png);base64,[A-Za-z0-9+/=]+$/.test(p);

/** A complete printable page for the class: all text escaped, no script, photos embedded. */
export function classSheetHTML(cls, members, handins, { words, clock = (iso) => iso, kindName = (h) => h.kind }) {
  const rows = rosterRows(members, handins);
  const table = `<table><thead><tr>${[words.name, words.joined, words.lastIn, words.handedIn, words.reflections].map((w) => `<th>${esc(w)}</th>`).join('')}</tr></thead><tbody>${
    rows.map((r) => `<tr><td>${esc(r.member.name)}</td><td>${esc(clock(r.member.joinedAt))}</td><td>${esc(clock(r.member.lastIn))}</td><td>${r.handins.length}</td><td>${r.reflections}</td></tr>`).join('')
  }</tbody></table>`;
  const work = rows.filter((r) => r.handins.length).map((r) => `<section><h2>${esc(r.member.name)}</h2>${
    r.handins.map((h) => {
      const e = h.entry ?? {};
      const meta = [kindName(h), e.year, e.place, clock(h.at)].filter(Boolean).join(' · ');
      return `<article><h3>${esc(e.title || h.title || words.untitled)}</h3><p class="meta">${esc(meta)}</p>${
        photoOk(e.photo) ? `<img src="${e.photo}" alt="${esc(e.title)}">` : ''}${
        e.excerpt ? `<p class="note">${esc(e.excerpt)}</p>` : ''}${e.text ? `<p class="note">${esc(e.text)}</p>` : ''}</article>`;
    }).join('')}</section>`).join('');
  return `<!doctype html><html lang="${esc(words.lang || 'en')}"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>${esc(cls.name)}</title><style>body{max-width:52rem;margin:2rem auto;padding:0 1rem;color:#172127;font:15px/1.45 system-ui,sans-serif}table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid #87959c;padding:.35rem .5rem;text-align:left;vertical-align:top}section{border-top:2px solid #172127;margin-top:1.5rem}article{border-top:1px solid #c3ccd0;padding:.6rem 0;break-inside:avoid}.meta{color:#4a5a62;margin:.1rem 0}.note{white-space:pre-wrap}img{max-width:100%;height:auto;max-height:90mm}@media print{body{margin:0;font-size:10.5pt}}</style><body><h1>4D Chicago · ${esc(cls.name)}</h1><p>${esc([cls.group ? words.group : '', words.printed].filter(Boolean).join(' · '))}</p>${table}${work || `<p>${esc(words.none)}</p>`}</body></html>`;
}
