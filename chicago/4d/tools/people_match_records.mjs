// T-3417: the records of the people match — reference sets, subjects and match records —
// and the rules they are held to. Read by tools/people_match.mjs (the rig, which shoots) and
// tools/test_people_match.mjs (the gate, which needs no browser and no evidence clone).
// data/people_match/README.md is the page.
import fs from 'node:fs';
import path from 'node:path';

export const DIR = 'data/people_match';
export const SETS = `${DIR}/reference_sets`;
export const SUBJECTS = `${DIR}/subjects`;

/** The fixed rig: two distances, two viewports (the plan's "How we judge photographic"). */
export const DISTANCES_M = [3, 10];
export const VIEWPORTS = { desktop: [1280, 800], phone: [390, 780] };

/** What a person is judged on, in the plan's order. Every match record answers each one. */
export const CHECKLIST = {
  silhouette: 'Silhouette and fit of the clothes',
  folds: 'Folds where cloth gathers',
  hat_hair: 'Hat and hair',
  skin: 'Skin at 3 m',
  hands: 'Hands',
  stance: 'How the figure stands or sits',
  motion: 'How it moves (the 5-second strip)',
};
/** open: a visitor would see the figure is not the picture's kind of person here.
 *  reads: it reads as the same kind of picture. not shown: no picture in the set can say
 *  (colour in a monochrome print, hands the pictures hide). within tolerance: a gap two
 *  pictures disagree about, or smaller than the pictures can show. owner ruling: the owner
 *  asked for it otherwise. Only open blocks matches. */
export const STATUSES = ['open', 'reads', 'not shown', 'within tolerance', 'owner ruling'];
export const VERDICTS = ['unreviewed', 'differs', 'matches'];
export const BANDS = ['near', 'far'];

const HEX64 = /^[0-9a-f]{64}$/;
const ID = /^[a-z0-9_]+$/;

export const readJSON = (root, rel) => JSON.parse(fs.readFileSync(path.join(root, rel), 'utf8'));

export function listRecords(root) {
  const list = (rel, keep) => fs.existsSync(path.join(root, rel))
    ? fs.readdirSync(path.join(root, rel)).filter(keep).sort().map(f => `${rel}/${f}`) : [];
  return {
    sets: list(SETS, f => f.endsWith('.json')),
    subjects: list(SUBJECTS, f => f.endsWith('.json') && !f.endsWith('.match.json')),
    matches: list(SUBJECTS, f => f.endsWith('.match.json')),
  };
}

/** The values a subject's match record is bound to: when one changes, the figure the record
 *  judged is not the figure in the town any more. */
export function boundValues(root, subject, doc = null) {
  const b = subject.bound;
  doc ??= readJSON(root, b.file);
  const rows = Array.isArray(doc.rows) ? doc.rows : [];
  const row = rows.find(r => r.id === b.row);
  if (!row) throw Error(`${subject.id}: bound row ${b.row} is not in ${b.file}`);
  return Object.fromEntries(b.keys.map(k => [k, row[k] ?? null]));
}

export function checkSet(root, set, rel = 'reference set') {
  const errs = [], e = m => errs.push(`${rel}: ${m}`);
  if (!ID.test(set.id ?? '')) e('id must be lower_snake');
  if (rel !== 'reference set' && path.basename(rel, '.json') !== set.id) e('file name must be its id');
  for (const k of ['role', 'label']) if (typeof set[k] !== 'string' || !set[k].trim()) e(`${k} is required`);
  if (!Array.isArray(set.years) || set.years.length !== 2 || !set.years.every(Number.isInteger) || set.years[0] > set.years[1]) e('years must be [first, last]');
  if (!Array.isArray(set.scenes) || !set.scenes.length) e('scenes must name the scenes it judges');
  if (set.evidence?.repo !== 'kevinrhaas/chicago-evidence' || typeof set.evidence?.dir !== 'string' || !set.evidence.dir.startsWith('evidence/')) e('evidence must name a folder in kevinrhaas/chicago-evidence');
  const pics = Array.isArray(set.pictures) ? set.pictures : [];
  if (pics.length < 2) e('a set needs at least two pictures (the plan asks two or three per role)');
  const names = new Set();
  for (const p of pics) {
    const at = `picture ${p.name ?? '?'}`;
    if (!ID.test(p.name ?? '')) e(`${at}: name must be lower_snake`);
    if (names.has(p.name)) e(`${at}: name repeats`); names.add(p.name);
    if (typeof p.file !== 'string' || !/^[a-z0-9_]+\.(jpg|png)$/.test(p.file)) e(`${at}: file must be a .jpg or .png in the set's evidence folder`);
    if (!HEX64.test(p.sha256 ?? '')) e(`${at}: sha256 is required`);
    if (!BANDS.includes(p.band)) e(`${at}: band must be one of ${BANDS.join(', ')}`);
    if (typeof p.source_id !== 'string' || !fs.existsSync(path.join(root, 'data/sources', `${p.source_id}.json`))) e(`${at}: source_id ${p.source_id} does not resolve in data/sources/ (AGENTS.md rule 1)`);
    else {
      const src = readJSON(root, `data/sources/${p.source_id}.json`);
      if (['check_required', 'restricted'].includes(src.rights_status) && !p.rights_note) e(`${at}: ${p.source_id} is ${src.rights_status}; say why it may be shown beside a still`);
    }
    if (typeof p.from !== 'string' || !p.from.trim()) e(`${at}: from must say which copy and crop it is`);
    if (typeof p.shows !== 'string' || !p.shows.trim()) e(`${at}: shows must say what it shows`);
    if (typeof p.caption !== 'string' || !p.caption.trim() || p.caption.length > 160) e(`${at}: caption (the sheet's credit line, at most 160 characters) is required`);
  }
  for (const band of BANDS) if (pics.length && !pics.some(p => p.band === band)) e(`no ${band} picture: every still is paired with a picture of its own band`);
  return errs;
}

export function checkSubject(root, subject, sets, rel = 'subject') {
  const errs = [], e = m => errs.push(`${rel}: ${m}`);
  if (!ID.test(subject.id ?? '')) e('id must be lower_snake');
  if (rel !== 'subject' && path.basename(rel, '.json') !== subject.id) e('file name must be its id');
  const set = sets.get(subject.reference_set);
  if (!set) e(`reference_set ${subject.reference_set} is not in ${SETS}/`);
  else if (!set.scenes?.includes(subject.scene)) e(`reference set ${set.id} does not judge scene ${subject.scene}`);
  if (typeof subject.person_id !== 'string' || !subject.person_id) e('person_id is required');
  if (subject.find?.kind !== 'driven') e('find.kind must be "driven" (the only kind the rig can find yet)');
  const b = subject.bound;
  if (!b || typeof b.file !== 'string' || typeof b.row !== 'string' || !Array.isArray(b.keys) || !b.keys.length) e('bound must name {file, row, keys}');
  else {
    try {
      const doc = readJSON(root, b.file);
      const row = doc.rows?.find(r => r.id === b.row);
      if (!row) e(`bound row ${b.row} is not in ${b.file}`);
      else {
        if (row.person_id !== subject.person_id) e(`bound row ${b.row} drives ${row.person_id}, not ${subject.person_id}`);
        if (row.scene !== subject.scene) e(`bound row ${b.row} is in scene ${row.scene}, not ${subject.scene}`);
        if (subject.find?.kind === 'driven' && subject.find.row !== b.row) e('find.row and bound.row must be the same row');
        for (const k of b.keys) if (!(k in row)) e(`bound key ${k} is not on row ${b.row}`);
      }
    } catch (x) { e(`bound file ${b.file}: ${x.message}`); }
  }
  const stills = Array.isArray(subject.stills) ? subject.stills : [];
  const dist = stills.map(s => s.distance_m).sort((x, y) => x - y);
  if (JSON.stringify(dist) !== JSON.stringify(DISTANCES_M)) e(`stills must be exactly one at each of ${DISTANCES_M.join(' m and ')} m (the fixed rig)`);
  for (const s of stills) {
    const at = `still ${s.name ?? '?'}`;
    if (!BANDS.includes(s.name)) e(`${at}: name must be ${BANDS.join(' or ')} (the band it pairs with)`);
    if (!Number.isFinite(s.bearing_off_heading_deg) || Math.abs(s.bearing_off_heading_deg) > 180) e(`${at}: bearing_off_heading_deg must be within ±180`);
    if (!Number.isFinite(s.aim_below_head_m) || s.aim_below_head_m < -0.5 || s.aim_below_head_m > 3) e(`${at}: aim_below_head_m must be between -0.5 and 3`);
    if (!Number.isFinite(s.eye_m) || s.eye_m < 0.5 || s.eye_m > 4) e(`${at}: eye_m (camera height over the ground) must be between 0.5 and 4`);
  }
  if (stills.find(s => s.name === 'near')?.distance_m !== 3 || stills.find(s => s.name === 'far')?.distance_m !== 10) e('near is the 3 m still and far the 10 m one');
  if (subject.figure_below_head_m !== undefined && !(subject.figure_below_head_m > 0.5 && subject.figure_below_head_m < 2.2)) e('figure_below_head_m (head bone to feet, for the crop) must be between 0.5 and 2.2');
  for (const [vp, level] of Object.entries(subject.detail ?? {})) {
    if (!(vp in VIEWPORTS)) e(`detail.${vp} is not a viewport`);
    if (!['full', 'balanced'].includes(level)) e(`detail.${vp} must be full or balanced (light draws no people)`);
  }
  const clip = subject.clip;
  if (!clip || !BANDS.includes(clip.still) || !(clip.viewport in VIEWPORTS) || !Number.isInteger(clip.frames) || clip.frames < 3 || !(clip.interval_s > 0)) e('clip must name {still, viewport, frames >= 3, interval_s}');
  else if (Math.abs((clip.frames - 1) * clip.interval_s - 5) > 1.01) e('the clip spans about 5 seconds');
  return errs;
}

export function checkMatch(root, match, subject, rel = 'match record') {
  const errs = [], e = m => errs.push(`${rel}: ${m}`);
  if (!subject) return [`${rel}: no subject ${match.subject}`];
  if (match.subject !== subject.id) e(`subject must be ${subject.id}`);
  if (match.reference_set !== subject.reference_set) e(`reference_set must be ${subject.reference_set}`);
  if (!VERDICTS.includes(match.verdict)) e(`verdict must be one of ${VERDICTS.join(', ')}`);
  const items = match.checklist ?? {};
  for (const k of Object.keys(CHECKLIST)) {
    const it = items[k];
    if (!it) { e(`checklist.${k} is missing: every item is answered (${CHECKLIST[k]})`); continue; }
    if (!STATUSES.includes(it.status)) e(`checklist.${k}.status must be one of ${STATUSES.join(', ')}`);
    if (typeof it.note !== 'string' || !it.note.trim()) e(`checklist.${k}.note must say what was read`);
  }
  for (const k of Object.keys(items)) if (!(k in CHECKLIST)) e(`checklist.${k} is not a checklist item`);
  const open = Object.entries(items).filter(([, it]) => it?.status === 'open').map(([k]) => k);
  if (match.verdict === 'matches' && open.length) e(`verdict matches with open items: ${open.join(', ')}`);
  if (match.verdict === 'differs' && !open.length) e('verdict differs names no open item');
  for (const s of subject.stills ?? []) for (const vp of Object.keys(VIEWPORTS)) {
    const st = match.stills?.[`${s.name}-${vp}`];
    if (!st || typeof st.file !== 'string' || !HEX64.test(st.sha256 ?? '')) e(`stills.${s.name}-${vp} must record its file and sha256`);
  }
  if (!match.shot?.date || !match.shot?.target) e('shot must say when and against what build it was taken');
  // A verdict is about the figure it was shot on. A changed livery, clip or asset is a
  // different figure: the rig sets it back to unreviewed when it reshoots, and an approval
  // that outlived its figure is refused here.
  try {
    const now = boundValues(root, subject);
    const was = match.bound ?? {};
    const changed = Object.keys(now).filter(k => JSON.stringify(now[k]) !== JSON.stringify(was[k]));
    if (changed.length && match.verdict !== 'unreviewed') e(`verdict ${match.verdict} was given on a different figure (${changed.join(', ')} changed since it was shot): reshoot with tools/people_match.mjs`);
  } catch (x) { e(x.message); }
  return errs;
}

/** Every record in the tree, checked. */
export function checkAll(root) {
  const { sets: setFiles, subjects: subjectFiles, matches } = listRecords(root);
  const errs = [], sets = new Map(), subjects = new Map();
  for (const f of setFiles) { const s = readJSON(root, f); errs.push(...checkSet(root, s, f)); sets.set(s.id, s); }
  for (const f of subjectFiles) { const s = readJSON(root, f); errs.push(...checkSubject(root, s, sets, f)); subjects.set(s.id, s); }
  for (const f of matches) {
    const m = readJSON(root, f);
    const id = path.basename(f, '.match.json');
    errs.push(...checkMatch(root, m, subjects.get(id), f));
  }
  return { errs, sets, subjects, counts: { sets: setFiles.length, subjects: subjectFiles.length, matches: matches.length } };
}
